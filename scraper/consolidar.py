"""Consolidación de candidatos, antes de clasificar:
  1. Une duplicados que la recogida dejó separados:
     - mismo disco de MusicBrainz (MBID), p. ej. "Cosmic Country" y "Daniel Donato's Cosmic Country";
     - mismo artista, título casi igual (errata o espacios: "Vengeance"/"Vengence",
       "Deathbringer"/"Death Bringer") y fechas cercanas.
  2. Separa lo que no es un disco nuevo de un artista: recopilatorios de varios artistas, homenajes,
     bandas sonoras, "lo mejor de", antologías con rango de años, ediciones deluxe o redux.
Las reglas (expresiones y umbrales) están en data/config.yaml → consolidacion."""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict

from .util import normalizar, similitud

LISTAS = ("fuentes", "resenas", "etiquetas_originales", "etiquetas_musicbrainz_bandcamp", "descripciones")


def _fecha(s: str | None) -> dt.date | None:
    try:
        return dt.date.fromisoformat(s) if s else None
    except ValueError:
        return None


def _unir_lista(a: list, b: list) -> list:
    vistos, out = set(), []
    for x in a + b:
        k = repr(sorted(x.items())) if isinstance(x, dict) else normalizar(str(x))
        if k not in vistos:
            vistos.add(k)
            out.append(x)
    return out


def fusionar(base: dict, otro: dict) -> dict:
    """Une 'otro' en 'base'. La base es la que más fuentes tiene; sus datos mandan si los tiene."""
    if len(otro.get("fuentes", [])) > len(base.get("fuentes", [])) or (otro.get("mbid") and not base.get("mbid")):
        base, otro = otro, base
    res = dict(base)
    for k in LISTAS:
        res[k] = _unir_lista(base.get(k) or [], otro.get(k) or [])
    res["enlaces"] = {**(otro.get("enlaces") or {}), **(base.get("enlaces") or {})}
    for k, v in otro.items():
        if res.get(k) in (None, "", [], {}) and v not in (None, "", [], {}):
            res[k] = v
    if not base.get("fecha_exacta") and otro.get("fecha_exacta"):
        res["fecha"], res["fecha_exacta"] = otro["fecha"], True
    pm = [x for x in (base.get("primera_mencion"), otro.get("primera_mencion")) if x]
    if pm:
        res["primera_mencion"] = min(pm)
    res["unidos"] = sorted({base.get("id"), otro.get("id"), *base.get("unidos", []), *otro.get("unidos", [])} - {None, res.get("id")})
    return res


ABREVIATURAS = {"pt": "part", "pts": "parts", "vol": "volume", "vols": "volumes"}


def canon(t: str | None, equivalentes: dict | None = None) -> str:
    """Título normalizado y sin abreviaturas ("Pt. III" = "Part III", "Vol. 2" = "Volume 2").
    'equivalentes' (config) iguala grafías especiales: "ei8ht" = "eight"."""
    n = " ".join(ABREVIATURAS.get(x, x) for x in normalizar(t).split())
    return (equivalentes or {}).get(n, n)


NUMERALES = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "vol", "volume", "part", "pt", "chapter"}


DISTINTIVAS = {"live", "demo", "demos", "acoustic", "remix", "remixes", "instrumental", "instrumentals", "unplugged", "sessions",
               "redux", "deluxe", "edition", "remastered", "remaster", "expanded", "anniversary", "reissue"}


def _solo_cambia_el_numero(t1: str, t2: str) -> bool:
    """Discos distintos aunque se parezcan: cambia un número, volumen o parte ('Vol. 3' / 'Vol. 4',
    'Eddie and the Cruisers' / '... II'), o uno es directo, maqueta, acústico o remezclas y el otro no.
    Ante la duda, mejor dos fichas que unir dos discos distintos."""
    a, b = set(normalizar(t1).split()), set(normalizar(t2).split())
    dif = a ^ b
    return any(x.isdigit() or x in NUMERALES or x in DISTINTIVAS for x in dif)


def _mismo_titulo(d: dict, q: dict, umbral: float, dias_entre: int | None, equivalentes: dict | None = None) -> bool:
    t1, t2 = canon(d.get("titulo"), equivalentes), canon(q.get("titulo"), equivalentes)
    if not t1 or not t2 or _solo_cambia_el_numero(t1, t2):
        return False
    if similitud(t1, t2) >= umbral or t1.replace(" ", "") == t2.replace(" ", ""):
        return True
    # mismo día (o casi): basta con un título muy parecido o contenido en el otro
    # ("A Beaumont Bar" / "From a Beaumont Bar", "Songs of Rebellion & Redemption" / "Making Noise: Songs of ...")
    if dias_entre is not None and dias_entre <= 3 and min(len(t1), len(t2)) >= 8:
        return similitud(t1, t2) >= 0.75 or t1 in t2 or t2 in t1
    return False


def unir_duplicados(discos: list[dict], umbral: float = 0.95, dias: int = 45,
                    dias_identico: int = 200, equivalentes: dict | None = None) -> tuple[list[dict], int]:
    """→ (discos sin duplicados, nº de uniones). Con el título idéntico (tras quitar abreviaturas,
    espacios y signos) se admite más distancia entre fechas: una fuente da la fecha del anuncio y
    otra la de salida ("Imaginos IV: Rhyme of the Starclock" / "... Star Clock", 50 días)."""
    uniones = 0
    # 1) mismo MBID
    por_mbid, sin_mbid = {}, []
    for d in discos:
        m = d.get("mbid")
        if m and m in por_mbid:
            por_mbid[m] = fusionar(por_mbid[m], d)
            uniones += 1
        elif m:
            por_mbid[m] = d
        else:
            sin_mbid.append(d)
    lista = list(por_mbid.values()) + sin_mbid
    # 2) mismo artista + título casi igual + fechas cercanas (y que no sean dos MBID distintos)
    por_artista = defaultdict(list)
    for d in lista:
        por_artista[normalizar(d.get("artista"))].append(d)
    salida = []
    for grupo in por_artista.values():
        quedan = []
        for d in grupo:
            for i, q in enumerate(quedan):
                fa, fb = _fecha(d.get("fecha")), _fecha(q.get("fecha"))
                entre = abs((fa - fb).days) if fa and fb else None
                identico = canon(d.get("titulo"), equivalentes).replace(" ", "") == canon(q.get("titulo"), equivalentes).replace(" ", "")
                cerca = entre is None or entre <= (dias_identico if identico else dias)
                parecido = _mismo_titulo(d, q, umbral, entre, equivalentes)
                mbids_distintos = d.get("mbid") and q.get("mbid") and d["mbid"] != q["mbid"]
                if parecido and cerca and not mbids_distintos:
                    quedan[i] = fusionar(q, d)
                    uniones += 1
                    break
            else:
                quedan.append(d)
        salida.extend(quedan)
    return salida, uniones


def ampliaciones(discos: list[dict], dias_minimos: int = 30, equivalentes: dict | None = None) -> dict[int, str]:
    """Ediciones ampliadas de un disco anterior del mismo artista: el título empieza por el del
    disco anterior y añade algo ("Magnolia Sage (In Full Bloom)", "Musick: Encore"), y sale al menos
    'dias_minimos' después. No cuenta si cambia un número o parte ("Imaginos" / "Imaginos IV")
    ni si es un directo o una maqueta (eso ya es otro disco). → {posición en la lista: motivo}."""
    por_artista = defaultdict(list)
    for i, d in enumerate(discos):
        por_artista[normalizar(d.get("artista"))].append(i)
    out = {}
    for idx in por_artista.values():
        for i in idx:
            ti, fi = canon(discos[i].get("titulo"), equivalentes), _fecha(discos[i].get("fecha"))
            for j in idx:
                tj, fj = canon(discos[j].get("titulo"), equivalentes), _fecha(discos[j].get("fecha"))
                if i == j or not fi or not fj or len(tj) < 4 or not ti.startswith(tj + " "):
                    continue
                if (fi - fj).days >= dias_minimos and not _solo_cambia_el_numero(ti, tj):
                    out[i] = f"edición ampliada de «{discos[j]['titulo']}» ({discos[j]['fecha']})"
                    break
    return out


def motivo_no_nuevo(d: dict, reglas: dict) -> str | None:
    """Por qué no es un disco nuevo de un artista (o None)."""
    rx_artista = reglas.get("artista_recopilatorio")
    rx_titulo = reglas.get("titulo_no_nuevo")
    if rx_artista and re.search(rx_artista, d.get("artista") or ""):
        return "recopilatorio de varios artistas u homenaje"
    if rx_titulo:
        m = re.search(rx_titulo, d.get("titulo") or "")
        if m:
            return f"no es un disco nuevo («{m.group(0).strip()}» en el título)"
    rx_etq = reglas.get("etiquetas_no_nuevo")
    if rx_etq:
        for e in d.get("etiquetas_originales") or []:
            if re.search(rx_etq, e):
                return f"no es un disco nuevo (la fuente lo etiqueta «{e}»)"
    return None
