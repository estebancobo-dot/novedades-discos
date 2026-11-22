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
from .util import normalizar

PESOS = {"fuente": 3, "bandcamp": 2, "musicbrainz_top": 2, "musicbrainz": 1, "descripcion": 2, "categoria": 1,
         "discogs": 3, "wikidata": 2, "lastfm": 2}
CAMPOS_CSV = ["etiqueta", "subgenero", "origen", "fecha", "veces", "ejemplo", "nota"]


class Taxonomia:
    def __init__(self, datos: dict):
        self.reglas = datos.get("reglas", {})
        self.sub: dict[str, dict] = {}
        self.alias: dict[str, set[str]] = defaultdict(set)
        self.genericas: dict[str, str] = {}
        self.ignorar = {normalizar(str(x)) for x in datos.get("ignorar", [])}
        for fam, fd in datos["familias"].items():
            for g in fd.get("genericas", []):
                self.genericas[normalizar(str(g))] = fam
            for grupo, subs in fd["grupos"].items():
                for sid, sd in subs.items():
                    self.sub[sid] = {"id": sid, "nombre": sd.get("nombre", sid), "familia": fam, "grupo": grupo,
                                     "frontera": bool(sd.get("frontera"))}
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
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_CSV)
        w.writeheader()
        for k in sorted(mapeo, key=lambda k: (mapeo[k]["subgenero"] != "pendiente", k)):
            w.writerow({c: mapeo[k].get(c, "") for c in CAMPOS_CSV})


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


def clasificar_disco(d: dict, tax: Taxonomia, mapeo: dict, desconocidas: Counter, ejemplo: dict) -> dict:
    puntos: Counter = Counter()
    familias_gen = set()
    for etiqueta, origen in etiquetas_de(d, tax):
        reconocida = False
        for trozo in _trocear(etiqueta):
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
                reconocida = True
            elif n in mapeo and mapeo[n]["subgenero"] not in ("pendiente", ""):
                for s in mapeo[n]["subgenero"].split("|"):
                    if s in tax.sub:
                        puntos[s] += PESOS.get(origen, 1)
                reconocida = True
        if not reconocida:
            n = normalizar(etiqueta)
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
    return {"subgeneros": subs, "familias_genericas": sorted(familias_gen)}


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

    desconocidas, ejemplo = Counter(), {}
    quedan = []
    for d in discos:
        r = clasificar_disco(d, tax, mapeo, desconocidas, ejemplo)
        subs = r["subgeneros"]
        fam_subs = {tax.sub[s]["familia"] for s in subs if not tax.sub[s]["frontera"]} or {tax.sub[s]["familia"] for s in subs}
        fam_fuentes = {fuentes[x["id"]].get("familia") for x in d["fuentes"]
                       if x["id"] in fuentes and not fuentes[x["id"]].get("mixta")} - {None, "todas", "ninguna"}
        familias = fam_subs | fam_fuentes
        if not familias and not d.get("requiere_subgenero"):
            familias = set(r["familias_genericas"])
        motivo = None
        if d.get("requiere_subgenero"):
            if not subs:
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
