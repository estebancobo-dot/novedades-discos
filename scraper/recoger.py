"""Recogida completa:  python -m scraper.recoger [--sin-bandcamp] [--sin-mb] [--solo ID,ID]

1. Lee todas las fuentes activas de data/fuentes.yaml.
2. Junta los discos repetidos (artista + título normalizados).
3. Completa datos con MusicBrainz y, si hay enlace, con la página de Bandcamp.
4. Aplica las reglas de data/config.yaml (ventana de fechas, EP, idioma, reediciones).
5. Escribe data/discos.json, data/descartados.json y data/estado_fuentes.json.
La clasificación por subgénero se hace después (scraper.clasificar)."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict

from .bandcamp import Bandcamp
from .config import RAIZ, cargar_config, cargar_fuentes, ruta
from .http import Navegador
from .lectores import Item, leer_fuente
from .musicbrainz import MusicBrainz
from .util import clave, limpiar, normalizar, parse_fecha, restar_meses

NUMEROS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                       "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}


def log(*a):
    print(*a, flush=True)


def _iso(d):
    return d.isoformat() if isinstance(d, dt.date) else d


def _fecha_mb(s: str | None) -> tuple[dt.date | None, bool]:
    """'2026-09-25' → (fecha, exacta). '2026-09' o '2026' → (primer día, aproximada)."""
    if not s:
        return None, False
    p = s.split("-")
    try:
        if len(p) == 3:
            return dt.date(int(p[0]), int(p[1]), int(p[2])), True
        if len(p) == 2:
            return dt.date(int(p[0]), int(p[1]), 1), False
        return dt.date(int(p[0]), 1, 1), False
    except ValueError:
        return None, False


def _mayusculas(s: str) -> bool:
    letras = [c for c in s if c.isalpha()]
    return len(letras) > 3 and sum(c.isupper() for c in letras) / len(letras) > 0.8


def main():
    args = sys.argv[1:]
    config = cargar_config()
    reglas = config["reglas"]
    fuentes = cargar_fuentes(config)
    solo = next((a.split("=", 1)[1].split(",") for a in args if a.startswith("--solo=")), None)
    if solo:
        fuentes = [f for f in fuentes if f["id"] in solo]
    hoy = dt.date.today()
    desde = restar_meses(hoy, config["ventana"]["meses_atras"])
    hasta = restar_meses(hoy, -config["ventana"]["meses_adelante"])
    margen = dt.timedelta(days=int(reglas.get("margen_dias", 14)))
    nav = Navegador(config, RAIZ)
    por_id = {f["id"]: f for f in fuentes}

    rx_ep = re.compile(reglas["ep"])
    rx_reed = re.compile(reglas["reedicion"])
    rx_homo = re.compile(reglas["titulo_homonimo"])
    rx_pistas = re.compile(reglas["pistas_en_texto"])

    # ------------------------------------------------------------ 1. leer
    estado = {"fecha": hoy.isoformat(), "ventana": [desde.isoformat(), hasta.isoformat()], "fuentes": {}}
    items: list[Item] = []
    for f in fuentes:
        log(f"· {f['id']} …")
        res = leer_fuente(nav, f, hoy, desde - margen)
        estado["fuentes"][f["id"]] = {"nombre": f["nombre"], "web": f.get("web"), "familia": f.get("familia"),
                                     "rol": f.get("rol"), "estado": res.estado, "detalle": res.detalle.strip(),
                                     "paginas": res.paginas, "items": len(res.items)}
        log(f"  {res.estado} · {len(res.items)} items · {res.detalle.strip()[:120]}")
        items.extend(res.items)

    # ------------------------------------------------- 2. limpiar y agrupar
    descartados = []
    grupos: dict[str, list[Item]] = defaultdict(list)
    menciones: list[Item] = []
    for it in items:
        f = por_id[it.fuente]
        if it.mencion:
            menciones.append(it)
            continue
        if rx_homo.match(it.titulo or ""):
            it.titulo = it.artista
        texto_tipo = " ".join(x for x in (it.tipo, it.extra, it.genero) if x)
        it.extra = it.extra or ""
        m = rx_pistas.search(texto_tipo)
        if m and not it.pistas:
            n = m.group(1).lower()
            it.pistas = int(n) if n.isdigit() else NUMEROS.get(n)
        grupos[clave(it.artista, it.titulo)].append(it)

    discos = []
    for k, grupo in grupos.items():
        d = {"clave": k, "items": grupo}
        textos = " ".join(" ".join(x for x in (i.tipo, i.extra, i.genero, i.titulo) if x) for i in grupo)
        d["ep_fuente"] = any(rx_ep.search(" ".join(x for x in (i.tipo, i.extra, i.titulo) if x)) for i in grupo)
        d["reedicion_fuente"] = bool(rx_reed.search(textos)) or any((i.tipo or "").lower() == "reissue" for i in grupo)
        fechas_lanz = [i.fecha for i in grupo if i.fecha and i.fecha_tipo == "lanzamiento"]
        fechas_pub = [i.fecha_publicacion or i.fecha for i in grupo if (i.fecha_publicacion or i.fecha) and i.fecha_tipo != "lanzamiento"]
        d["fecha_fuente"] = min(fechas_lanz) if fechas_lanz else None
        d["fecha_pub"] = min(fechas_pub) if fechas_pub else None
        motivo = None
        if d["ep_fuente"]:
            motivo = "EP (según la fuente)"
        elif d["reedicion_fuente"]:
            motivo = "reedición o formato especial (según la fuente)"
        elif d["fecha_fuente"] and max(fechas_lanz) < desde - margen:
            motivo = f"fuera de la ventana (salió el {max(fechas_lanz)})"
        elif not fechas_lanz and d["fecha_pub"] and d["fecha_pub"] < desde - dt.timedelta(days=60):
            motivo = f"mencionado solo antes de la ventana ({d['fecha_pub']})"
        if motivo:
            descartados.append(_descartado(grupo, motivo, por_id))
        else:
            discos.append(d)
    log(f"Candidatos: {len(discos)} · descartados por la fuente: {len(descartados)} · menciones: {len(menciones)}")

    # ---------------------------------------------------- 3. enriquecer
    umbral = float(reglas.get("similitud_minima", 0.86))
    mb = MusicBrainz(nav, ruta(config["rutas"]["cache_musicbrainz"]), umbral) if config["enriquecimiento"].get("musicbrainz") and "--sin-mb" not in args else None
    bc_cfg = config["enriquecimiento"].get("bandcamp") or {}
    bc = Bandcamp(nav, ruta(config["rutas"]["cache_bandcamp"]), int(bc_cfg.get("max_paginas_por_ejecucion", 500)), umbral) \
        if bc_cfg.get("activo") and "--sin-bandcamp" not in args else None
    for n, d in enumerate(discos, 1):
        it0 = d["items"][0]
        inter = any(por_id[i.fuente].get("intercambiable") for i in d["items"])
        d["mb"] = mb.buscar(it0.artista, it0.titulo, inter) if mb else None
        d["mb_artistas"] = [mb.artista(a) for a in (d["mb"] or {}).get("artistas_id", [])[:2]] if mb and d["mb"] else []
        if n % 50 == 0:
            log(f"  MusicBrainz {n}/{len(discos)} · consultas {mb.consultas if mb else 0}")
            if mb:
                mb.guardar()
    if mb:
        mb.guardar()

    # ------------------------------------------- 4. reglas y salida final
    tipos_excl = set(reglas.get("tipos_secundarios_excluidos", []))
    idiomas = set(reglas.get("idiomas_permitidos", ["eng"]))
    previos = _cargar_previos(ruta(config["rutas"]["discos"]))
    salida = []
    for d in discos:
        grupo, m = d["items"], d.get("mb") or {}
        motivo = None
        fecha, exacta, origen = None, False, None
        fmb, exacta_mb = _fecha_mb(m.get("primera_fecha"))
        if fmb and exacta_mb:
            fecha, exacta, origen = fmb, True, "musicbrainz"
        elif d["fecha_fuente"]:
            fecha, exacta, origen = d["fecha_fuente"], True, "fuente"
        elif fmb:
            fecha, exacta, origen = fmb, False, "musicbrainz"
        elif d["fecha_pub"]:
            fecha, exacta, origen = d["fecha_pub"], False, "reseña"
        tipo = (m.get("tipo") or "").lower()
        sec = set(m.get("tipos_secundarios") or [])
        pistas = m.get("pistas") or next((i.pistas for i in grupo if i.pistas), None)
        if not fecha:
            motivo = "sin fecha conocida"
        elif fmb and fmb < desde - margen:
            motivo = f"no es nuevo: MusicBrainz lo fecha el {m.get('primera_fecha')}"
        elif fecha < desde - margen:
            motivo = f"fuera de la ventana ({fecha})"
        elif fecha > hasta:
            motivo = f"demasiado lejos en el futuro ({fecha})"
        elif tipo in ("ep", "single"):
            motivo = f"{tipo.upper()} según MusicBrainz"
        elif sec & tipos_excl:
            motivo = "tipo excluido: " + ", ".join(sorted(sec & tipos_excl))
        elif not tipo and pistas and pistas <= int(reglas.get("pistas_max_ep", 6)):
            motivo = f"probable EP ({pistas} pistas)"
        elif m.get("idioma") and m["idioma"] not in idiomas and m["idioma"] not in ("zxx", "mul"):
            motivo = f"idioma {m['idioma']}"
        elif not m.get("idioma") and reglas.get("idioma_desconocido") == "descartar":
            motivo = "idioma sin verificar"
        if motivo:
            descartados.append(_descartado(grupo, motivo, por_id))
            continue
        salida.append(_disco(d, fecha, exacta, origen, pistas, sec, por_id, hoy, previos, bc))
        if bc and len(salida) % 25 == 0:
            bc.guardar()
    if bc:
        bc.guardar()

    # ------------------------------------------- 5. menciones (titulares)
    indice = defaultdict(list)
    for s in salida:
        indice[normalizar(s["artista"]).split(" ")[0]].append(s)
    sin_pareja = 0
    for it in menciones:
        t = f" {normalizar(it.mencion)} "
        encontrado = None
        for s in (x for lista in indice.values() for x in lista):
            na, nt = normalizar(s["artista"]), normalizar(s["titulo"])
            if len(na) >= 3 and len(nt) >= 3 and f" {na} " in t and f" {nt} " in t:
                encontrado = s
                break
        if encontrado:
            _anadir_fuente(encontrado, it, por_id)
        else:
            sin_pareja += 1
    log(f"Menciones emparejadas: {len(menciones) - sin_pareja}/{len(menciones)}")

    salida.sort(key=lambda s: (s["fecha"], s["artista"].lower()), reverse=True)
    estado["musicbrainz"] = {"consultas": mb.consultas if mb else 0, "bloqueado": mb.bloqueado if mb else None}
    estado["bandcamp"] = {"paginas": bc.abiertas if bc else 0, "bloqueado": bc.bloqueado if bc else None}
    estado["peticiones"] = nav.peticiones
    estado["hosts_bloqueados"] = nav.hosts_bloqueados
    estado["menciones"] = {"total": len(menciones), "sin_pareja": sin_pareja}
    _escribir(ruta(config["rutas"]["discos"]), salida)
    _escribir(ruta(config["rutas"]["descartados"]), sorted(descartados, key=lambda x: x["motivo"]))
    _escribir(ruta(config["rutas"]["estado_fuentes"]), estado)
    log(f"Discos: {len(salida)} · descartados: {len(descartados)} · peticiones: {nav.peticiones}")


# ---------------------------------------------------------------- helpers
def _descartado(grupo, motivo, por_id):
    i = grupo[0]
    return {"artista": i.artista, "titulo": i.titulo, "motivo": motivo,
            "fuentes": sorted({g.fuente for g in grupo}),
            "fecha": _iso(i.fecha), "familia": sorted({por_id[g.fuente].get("familia") for g in grupo})}


def _cargar_previos(p):
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return {d["id"]: d for d in json.load(f)}


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", normalizar(s.replace("|", " – "))).strip("-")[:90]


def _anadir_fuente(disco, it: Item, por_id):
    f = por_id[it.fuente]
    if not any(x["id"] == f["id"] for x in disco["fuentes"]):
        disco["fuentes"].append({"id": f["id"], "nombre": f["nombre"], "rol": f.get("rol"), "url": it.url or f.get("web"),
                                 "fecha": _iso(it.fecha_publicacion or (it.fecha if it.fecha_tipo != "lanzamiento" else None))})
    if f.get("rol") == "resena" and not any(r["fuente"] == f["id"] for r in disco["resenas"]):
        disco["resenas"].append({"fuente": f["id"], "nombre": f["nombre"], "url": it.url, "nota": it.nota,
                                 "fecha": _iso(it.fecha_publicacion or it.fecha)})
    for e in it.etiquetas + ([it.genero] if it.genero else []):
        if e and e not in disco["etiquetas_originales"]:
            disco["etiquetas_originales"].append(e)
    fp = it.fecha_publicacion or (it.fecha if it.fecha_tipo == "publicacion" else None)
    if fp and (not disco.get("primera_mencion") or _iso(fp) < disco["primera_mencion"]):
        disco["primera_mencion"] = _iso(fp)


def _disco(d, fecha, exacta, origen, pistas, sec, por_id, hoy, previos, bc):
    grupo, m = d["items"], d.get("mb") or {}
    # nombre a mostrar: MusicBrainz, o la versión de la fuente que no esté en mayúsculas
    cand = sorted(grupo, key=lambda i: (_mayusculas(i.artista) or _mayusculas(i.titulo), por_id[i.fuente].get("rol") != "listado"))
    artista = m.get("artista") or cand[0].artista
    titulo = m.get("titulo") or cand[0].titulo
    sello = (m.get("sellos") or [None])[0] or next((i.sello for i in cand if i.sello), None) \
        or next((por_id[i.fuente].get("sello") for i in grupo if por_id[i.fuente].get("sello")), None)
    enlaces = dict(m.get("enlaces") or {})
    art_enl = {}
    etiquetas = []
    for a in d.get("mb_artistas") or []:
        for k, v in (a.get("enlaces") or {}).items():
            art_enl.setdefault(k, v)
        for e in (a.get("generos") or []) + (a.get("etiquetas") or []):
            if e not in etiquetas:
                etiquetas.append(e)
    if m.get("rg"):
        enlaces["musicbrainz"] = f"https://musicbrainz.org/release-group/{m['rg']}"
    portada = m.get("portada")
    # Bandcamp
    bcd = None
    if bc and (enlaces.get("bandcamp") or art_enl.get("bandcamp")):
        bcd = bc.disco(titulo, enlaces.get("bandcamp") if "/album/" in (enlaces.get("bandcamp") or "") else None,
                       art_enl.get("bandcamp"))
    if bcd:
        enlaces["bandcamp"] = bcd["url"]
        portada = portada or bcd.get("portada")
        pistas = pistas or bcd.get("pistas")
        for e in bcd.get("etiquetas") or []:
            if e not in etiquetas:
                etiquetas.append(e)
    portada = portada or next((i.portada for i in grupo if i.portada), None)
    ident = _slug(d["clave"])
    previo = previos.get(ident, {})
    disco = {
        "id": ident,
        "artista": limpiar(artista), "titulo": limpiar(titulo),
        "fecha": fecha.isoformat(), "fecha_exacta": exacta, "fecha_origen": origen,
        "estado": "proximamente" if fecha > hoy else "publicado",
        "sello": sello,
        "familias": sorted({por_id[i.fuente].get("familia") for i in grupo if por_id[i.fuente].get("familia")}),
        "subgeneros": previo.get("subgeneros", []),
        "etiquetas_originales": [],
        "etiquetas_musicbrainz_bandcamp": etiquetas,
        "portada": portada,
        "pistas": pistas,
        "tipo": "álbum (directo)" if "Live" in sec else "álbum",
        "tipo_verificado": bool(m.get("tipo")),
        "idioma": m.get("idioma"),
        "fuentes": [], "resenas": [],
        "enlaces": enlaces,
        "enlace_artista_bandcamp": art_enl.get("bandcamp"),
        "en_bandcamp": bool(enlaces.get("bandcamp") or art_enl.get("bandcamp")),
        "mbid": m.get("rg"),
        "requiere_subgenero": all(por_id[i.fuente].get("mixta") for i in grupo),
        "primera_mencion": None,
        "detectado": previo.get("detectado") or hoy.isoformat(),
    }
    for it in grupo:
        _anadir_fuente(disco, it, por_id)
    return disco


def _escribir(p, datos):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, default=_iso)


if __name__ == "__main__":
    main()
