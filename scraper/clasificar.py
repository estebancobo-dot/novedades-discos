"""Clasificación con la taxonomía:  python -m scraper.clasificar

Para cada disco reúne sus etiquetas (pistas de la fuente, géneros de
MusicBrainz, etiquetas de Bandcamp, descripciones) y las traduce a subgéneros
de data/taxonomia.yaml mediante:
  1. los alias de la taxonomía,
  2. data/mapeo_etiquetas.csv (respuestas del LLM, una sola vez por etiqueta).
Las etiquetas que no encajan se apuntan en el CSV como "pendiente" para que un
LLM las clasifique una única vez. Nunca se crean subgéneros nuevos."""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
from collections import Counter, defaultdict

from .config import cargar_config, cargar_yaml, ruta
from .consolidar import ampliaciones, motivo_no_nuevo, unir_duplicados
from .util import normalizar

PESOS = {"fuente": 3, "bandcamp": 2, "musicbrainz_top": 2, "musicbrainz": 1, "descripcion": 2, "categoria": 1,
         "discogs": 3, "wikidata": 2, "lastfm": 2, "itunes": 1}
CAMPOS_CSV = ["etiqueta", "subgenero", "origen", "fecha", "veces", "ejemplo", "nota"]


class Taxonomia:
    def __init__(self, datos: dict):
        self.reglas = datos.get("reglas", {})
        self.sub: dict[str, dict] = {}
        self.alias: dict[str, set[str]] = defaultdict(set)
        self.genericas: dict[str, str] = {}
        self.ignorar = {normalizar(str(x)) for x in datos.get("ignorar", [])}
        self.rx_ignorar = re.compile(datos["ignorar_regex"]) if datos.get("ignorar_regex") else None
        for fam, fd in datos["familias"].items():
            for g in fd.get("genericas", []):
                self.genericas[normalizar(str(g))] = fam
            for grupo, subs in fd["grupos"].items():
                for sid, sd in subs.items():
                    self.sub[sid] = {"id": sid, "nombre": sd.get("nombre", sid), "familia": fam, "grupo": grupo,
                                     "frontera": bool(sd.get("frontera")),
                                     "familias": [fam] + [str(x) for x in sd.get("tambien_en", [])]}
                    for a in [sid.replace("-", " ")] + list(sd.get("alias", [])):
                        self.alias[normalizar(str(a))].add(sid)
        minp = int(self.reglas.get("alias_en_texto_min_palabras", 2))
        largos = [a for a in self.alias if len(a.split()) >= minp or "-" in a]
        largos.sort(key=len, reverse=True)
        self.rx_texto = re.compile(r"\b(" + "|".join(re.escape(a) for a in largos) + r")\b") if largos else None


def _trocear(etiqueta: str) -> list[str]:
    partes = re.split(r"\s*(?:,|;|/| and | & |\+)\s*", etiqueta)
    return [etiqueta] + [p for p in partes if p and p != etiqueta]


def cargar_mapeo(p: str) -> dict[str, dict]:
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8", newline="") as f:
        return {normalizar(r["etiqueta"]): r for r in csv.DictReader(f)}


def guardar_mapeo(p: str, mapeo: dict[str, dict]):
    """Escritura atómica (archivo temporal + renombrado): quien lea la tabla a la vez nunca ve
    un archivo a medias."""
    tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS_CSV)
            w.writeheader()
            for k in sorted(mapeo, key=lambda k: (mapeo[k]["subgenero"] != "pendiente", k)):
                w.writerow({c: mapeo[k].get(c, "") for c in CAMPOS_CSV})
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def etiquetas_de(d: dict, tax: Taxonomia) -> list[tuple[str, str]]:
    """(etiqueta, origen) de un disco."""
    out = []
    for e in d.get("etiquetas_originales", []):
        out.append((e, "fuente"))
    mbbc = d.get("etiquetas_musicbrainz_bandcamp", [])
    nmb = int(tax.reglas.get("max_etiquetas_musicbrainz", 8))
    for i, e in enumerate(mbbc[:nmb]):
        out.append((e, "musicbrainz_top" if i < 3 else "musicbrainz"))
    for x in d.get("etiquetas_extra", []):
        out.append((x["etiqueta"], x["origen"]))
    return out


def _conocida_entera(n: str, tax: Taxonomia, mapeo: dict) -> bool:
    """La etiqueta entera ya dice algo: no se trocea ("Folk, World, & Country" de Discogs es una
    categoría amplia; sus trozos "Folk" y "Country" dirían más de lo que dice)."""
    return n in tax.ignorar or n in tax.alias or n in tax.genericas or (n in mapeo and mapeo[n]["subgenero"] not in ("pendiente", "", "ninguno"))


def _sin_genero_ajeno(d: dict, tax: Taxonomia, r: dict) -> bool:
    """El disco no trae etiquetas de género de los servicios (MusicBrainz, Discogs, Deezer...) o
    solo genéricas nuestras ("blues", "rock"). Las de la propia fuente en estas webs son nombres de
    músicos y secciones ("Album Reviews"). Si trae "soul" o "jazz" de un servicio, no se le pone familia."""
    return r["familias_genericas"] != [] or not any(o != "fuente" for _, o in etiquetas_de(d, tax))


def clasificar_disco(d: dict, tax: Taxonomia, mapeo: dict, desconocidas: Counter, ejemplo: dict) -> dict:
    puntos: Counter = Counter()
    familias_gen, familias_gen_fuertes = set(), set()
    for etiqueta, origen in etiquetas_de(d, tax):
        reconocida = False
        entera = normalizar(etiqueta)
        trozos = [etiqueta] if _conocida_entera(entera, tax, mapeo) else _trocear(etiqueta)
        for trozo in trozos:
            n = normalizar(trozo)
            if not n or n in tax.ignorar:
                reconocida = True
                continue
            if n in tax.alias:
                for s in tax.alias[n]:
                    puntos[s] += PESOS.get(origen, 1)
                reconocida = True
            elif n in tax.genericas:
                familias_gen.add(tax.genericas[n])
                if PESOS.get(origen, 1) >= 2:
                    familias_gen_fuertes.add(tax.genericas[n])
                reconocida = True
            elif n in mapeo and mapeo[n]["subgenero"] not in ("pendiente", ""):
                for s in mapeo[n]["subgenero"].split("|"):
                    if s in tax.sub:
                        puntos[s] += PESOS.get(origen, 1)
                reconocida = True
        if not reconocida:
            n = normalizar(etiqueta)
            if tax.rx_ignorar and tax.rx_ignorar.search(etiqueta):
                continue
            if n and len(n) <= 40:
                desconocidas[n] += 1
                ejemplo.setdefault(n, (etiqueta, f"{d['artista']} – {d['titulo']}"))
    if tax.rx_texto:
        for texto in d.get("descripciones", []):
            for m in set(tax.rx_texto.findall(normalizar(texto))):
                for s in tax.alias[m]:
                    puntos[s] += PESOS["descripcion"]
    maxs = int(tax.reglas.get("max_subgeneros", 4))
    subs = [s for s, _ in sorted(puntos.items(), key=lambda kv: (-kv[1], kv[0]))][:maxs]
    suman = set(tax.reglas.get("genericas_suman_familia") or [])
    return {"subgeneros": subs, "familias_genericas": sorted(familias_gen),
            "familias_suman": sorted(familias_gen_fuertes & suman)}


def main():
    config = cargar_config()
    rutas = config["rutas"]
    tax = Taxonomia(cargar_yaml(rutas["taxonomia"]))
    fuentes = {f["id"]: f for f in cargar_yaml(rutas["fuentes"])["fuentes"]}
    p_mapeo = ruta(rutas["mapeo_etiquetas"])
    mapeo = cargar_mapeo(p_mapeo)
    with open(ruta(rutas["candidatos"]), encoding="utf-8") as f:
        discos = json.load(f)
    with open(ruta(rutas["descartados"]), encoding="utf-8") as f:
        descartados = [x for x in json.load(f) if not x["motivo"].startswith("clasificación:")]

    # Consolidación: unir duplicados que la recogida dejó separados y apartar lo que no es un
    # disco nuevo de un artista (recopilatorios, bandas sonoras, deluxe...). Ver scraper/consolidar.py
    cons = config.get("consolidacion") or {}
    equivalentes = {normalizar(k): normalizar(v) for k, v in (cons.get("titulos_equivalentes") or {}).items()}
    discos, uniones = unir_duplicados(discos, float(cons.get("similitud_titulo", 0.95)), int(cons.get("dias_maximos", 45)),
                                      int(cons.get("dias_maximos_titulo_identico", 200)), equivalentes)
    ampliadas = ampliaciones(discos, int(cons.get("dias_minimos_ampliacion", 30)), equivalentes) \
        if cons.get("descartar_ampliaciones", True) else {}
    nuevos = []
    for i, d in enumerate(discos):
        motivo = ampliadas.get(i) or motivo_no_nuevo(d, cons)
        if motivo:
            descartados.append({"artista": d["artista"], "titulo": d["titulo"], "motivo": "clasificación: " + motivo,
                                "fuentes": [x["id"] for x in d["fuentes"]], "fecha": d["fecha"]})
        else:
            nuevos.append(d)
    discos = nuevos
    print(f"Consolidación: {uniones} duplicados unidos · {sum(1 for x in descartados if 'disco nuevo' in x['motivo'] or 'recopilatorio' in x['motivo'] or 'ampliada' in x['motivo'])} no son discos nuevos")

    # Corte exacto de la ventana (por si la recogida se hizo con otra configuración).
    estado_p = ruta(rutas["estado_fuentes"])
    ventana = (json.load(open(estado_p, encoding="utf-8")).get("ventana") if os.path.exists(estado_p) else None) or ["", "9999"]
    # nombres de artistas y sellos del propio conjunto: como etiqueta no dicen nada del género
    for d in discos:
        tax.ignorar.add(normalizar(d.get("artista")))
        if d.get("sello"):
            for sello in re.split(r"\s*[/,]\s*", d["sello"]):
                tax.ignorar.add(normalizar(sello))
    tax.ignorar.discard("")
    desconocidas, ejemplo = Counter(), {}
    quedan = []
    for d in discos:
        if not (ventana[0] <= d["fecha"] <= ventana[1]):
            descartados.append({"artista": d["artista"], "titulo": d["titulo"], "fuentes": [x["id"] for x in d["fuentes"]],
                                "motivo": f"clasificación: fuera de la ventana {ventana[0]} – {ventana[1]} ({d['fecha']})",
                                "fecha": d["fecha"]})
            continue
        r = clasificar_disco(d, tax, mapeo, desconocidas, ejemplo)
        subs = r["subgeneros"]
        fam_subs = {f for s in subs if not tax.sub[s]["frontera"] for f in tax.sub[s]["familias"]} \
            or {f for s in subs for f in tax.sub[s]["familias"]}
        fam_fuentes = {fuentes[x["id"]].get("familia") for x in d["fuentes"]
                       if x["id"] in fuentes and not fuentes[x["id"]].get("mixta")} - {None, "todas", "ninguna"}
        familias = fam_subs | fam_fuentes
        if familias:
            familias |= set(r["familias_suman"])
        if not familias and not d.get("requiere_subgenero"):
            familias = set(r["familias_genericas"])
        motivo = None
        tipo_dz = (d.get("deezer") or {}).get("tipo")
        if tipo_dz in ("ep", "single") and not d.get("tipo_verificado"):
            motivo = f"clasificación: {tipo_dz.upper()} según Deezer"
        elif d.get("requiere_subgenero"):
            por_defecto = {fuentes[x["id"]].get("familia_sin_subgenero") for x in d["fuentes"] if x["id"] in fuentes} - {None}
            if not subs and r["familias_suman"]:
                familias = set(r["familias_suman"])       # "country" o "blues" explícito y con peso: basta
            elif not subs and por_defecto and _sin_genero_ajeno(d, tax, r):
                familias = por_defecto                    # sin ninguna etiqueta de género: la de la fuente
            elif not subs:
                motivo = "clasificación: fuente mixta y ningún subgénero de la taxonomía"
            elif all(tax.sub[s]["frontera"] for s in subs):
                motivo = "clasificación: solo subgéneros frontera y fuente mixta"
        if not familias and not motivo:
            motivo = "clasificación: sin familia reconocible"
        if motivo:
            descartados.append({"artista": d["artista"], "titulo": d["titulo"], "motivo": motivo,
                                "fuentes": [x["id"] for x in d["fuentes"]], "fecha": d["fecha"],
                                "etiquetas": (d.get("etiquetas_originales", []) + d.get("etiquetas_musicbrainz_bandcamp", []))[:10]})
            continue
        d["subgeneros"] = subs
        d["familias"] = sorted(familias)
        d["subgeneros_frontera"] = [s for s in subs if tax.sub[s]["frontera"]]
        quedan.append(d)

    hoy = dt.date.today().isoformat()
    for n, veces in desconocidas.items():
        if n in mapeo:
            mapeo[n]["veces"] = veces
        else:
            et, ej = ejemplo[n]
            mapeo[n] = {"etiqueta": et, "subgenero": "pendiente", "origen": "", "fecha": hoy, "veces": veces, "ejemplo": ej}
    guardar_mapeo(p_mapeo, mapeo)
    with open(ruta(rutas["discos"]), "w", encoding="utf-8") as f:
        json.dump(quedan, f, ensure_ascii=False, indent=1)
    with open(ruta(rutas["descartados"]), "w", encoding="utf-8") as f:
        json.dump(sorted(descartados, key=lambda x: x["motivo"]), f, ensure_ascii=False, indent=1)
    pend = sum(1 for v in mapeo.values() if v["subgenero"] == "pendiente")
    con = sum(1 for d in quedan if d["subgeneros"])
    print(f"Discos: {len(quedan)} · con subgénero: {con} · etiquetas pendientes de mapear: {pend}")


if __name__ == "__main__":
    main()
