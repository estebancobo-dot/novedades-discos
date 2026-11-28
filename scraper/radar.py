"""Radar de artistas con MusicBrainz (sin Spotify ni claves).

Técnica tomada de la integración de Home Assistant "Upcoming Music Releases"
(Thrasher2020/home-assistant-upcoming-music-releases): en vez de preguntar
artista por artista, se piden TODOS los álbumes con fecha de salida en un rango
(firstreleasedate) y se cruzan con los artistas que nos interesan.
  - Se trocea por meses y, si un trozo supera el tope de 500 resultados de
    MusicBrainz, se parte por la mitad hasta llegar a días sueltos.
  - Se excluyen las fechas que empiezan antes del trozo, porque un disco con
    solo el año ("2026") coincide con cualquier día de ese año.
Los artistas que interesan son los que MusicBrainz etiqueta con géneros de
nuestras familias (data/taxonomia.yaml) y los de los discos ya publicados."""
from __future__ import annotations

import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
import os
import urllib.parse

from .clasificar import Taxonomia
from .config import cargar_yaml, ruta
from .lectores import Item, ResultadoFuente
from .util import normalizar

API = "https://musicbrainz.org/ws/2/release-group"
TOPE = 500           # MusicBrainz no devuelve más allá de offset+limit = 500
POR_PAGINA = 100


def _trozos_mensuales(lo: dt.date, hi: dt.date):
    inicio = lo
    while inicio <= hi:
        sig = dt.date(inicio.year, inicio.month, 1) + dt.timedelta(days=32)
        fin = min(dt.date(sig.year, sig.month, 1) - dt.timedelta(days=1), hi)
        yield inicio, fin
        inicio = fin + dt.timedelta(days=1)


def _consulta(lo: dt.date, hi: dt.date, offset: int, tipos: str) -> str:
    antes = (lo - dt.timedelta(days=1)).isoformat()
    q = (f"firstreleasedate:[{lo.isoformat()} TO {hi.isoformat()}] AND ({tipos}) "
         f"AND NOT firstreleasedate:[1000-01-01 TO {antes}]")
    return f"{API}?fmt=json&limit={POR_PAGINA}&offset={offset}&query=" + urllib.parse.quote(q)


def _paginas(nav, lo, hi, tipos, prof=0):
    r = nav.get(_consulta(lo, hi, 0, tipos), acepta="application/json")
    if r.estado != 200:
        return []
    d = json.loads(r.texto)
    n = int(d.get("count") or 0)
    if n > TOPE and lo < hi and prof < 12:
        mitad = lo + (hi - lo) // 2
        return _paginas(nav, lo, mitad, tipos, prof + 1) + _paginas(nav, mitad + dt.timedelta(days=1), hi, tipos, prof + 1)
    filas = list(d.get("release-groups", []))
    off = POR_PAGINA
    while off < min(n, TOPE):
        r = nav.get(_consulta(lo, hi, off, tipos), acepta="application/json")
        if r.estado != 200:
            break
        filas += json.loads(r.texto).get("release-groups", [])
        off += POR_PAGINA
    return filas


def artistas_de_interes(config: dict) -> tuple[set[str], set[str]]:
    """(ids de MusicBrainz, nombres normalizados) de los artistas de nuestras familias."""
    tax = Taxonomia(cargar_yaml(config["rutas"]["taxonomia"]))
    ids, nombres = set(), set()
    p = ruta(config["rutas"]["cache_musicbrainz"])
    cache = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    for k, v in cache.items():
        if not k.startswith("art:"):
            continue
        etiquetas = [normalizar(e) for e in (v.get("generos") or []) + (v.get("etiquetas") or [])]
        if any(e in tax.alias for e in etiquetas):        # un subgénero concreto, no solo "rock"
            ids.add(k[4:])
            nombres.add(normalizar(v.get("nombre")))
    pd = ruta(config["rutas"]["discos"])
    if os.path.exists(pd):
        for d in json.load(open(pd, encoding="utf-8")):
            if d.get("subgeneros"):
                nombres.add(normalizar(d["artista"]))
                ids.update(d.get("mbid_artistas") or [])
    nombres.discard("")
    return ids, nombres


def leer_radar(nav, cfg, hoy, desde=None, config=None) -> ResultadoFuente:
    res = ResultadoFuente(cfg["id"])
    ids, nombres = artistas_de_interes(config)
    if not ids and not nombres:
        res.detalle = "sin artistas de interés todavía"
        return res
    lo = desde or hoy - dt.timedelta(days=30)
    hi = hoy + dt.timedelta(days=int(cfg.get("dias_adelante", 180)))
    tipos = cfg.get("tipos", "primarytype:album")
    vistos = set()
    tramos = list(_trozos_mensuales(lo, hi))
    # MusicBrainz tarda segundos en responder: varios tramos a la vez, sin pasar de su ritmo (candado por web)
    with ThreadPoolExecutor(max_workers=max(1, int(cfg.get("hilos", 4)))) as ex:
        resultados = list(ex.map(lambda t: _paginas(nav, t[0], t[1], tipos), tramos))
    for filas in resultados:
        res.paginas += 1
        for rg in filas:
            if rg["id"] in vistos or rg.get("secondary-types"):
                continue
            credito = rg.get("artist-credit", [])
            aids = {c["artist"]["id"] for c in credito if c.get("artist")}
            nombre = "".join((c.get("name") or "") + (c.get("joinphrase") or "") for c in credito)
            if not (aids & ids or normalizar(nombre) in nombres):
                continue
            vistos.add(rg["id"])
            fecha = rg.get("first-release-date") or ""
            try:
                f = dt.date.fromisoformat(fecha) if len(fecha) == 10 else None
            except ValueError:
                f = None
            res.items.append(Item(fuente=cfg["id"], artista=nombre, titulo=rg.get("title") or "", fecha=f,
                                  fecha_tipo="lanzamiento", tipo=rg.get("primary-type"),
                                  url=f"https://musicbrainz.org/release-group/{rg['id']}"))
    res.detalle = f"{len(ids)} artistas por id y {len(nombres)} por nombre"
    return res


# ---------------------------------------------------------------- radar Deezer
def leer_radar_deezer(nav, cfg, hoy, desde=None, config=None) -> ResultadoFuente:
    """Discografía al día de cada artista de interés en Deezer (API pública, sin clave).
    Idea de ydniM/Music-Releases-Feed. El artista se identifica por nombre exacto
    (normalizado) y solo se aceptan lanzamientos de tipo álbum."""
    res = ResultadoFuente(cfg["id"])
    _ids, nombres_norm = artistas_de_interes(config)
    p = ruta(config["rutas"]["cache_musicbrainz"])
    cache = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    nombres = sorted({v.get("nombre") for k, v in cache.items() if k.startswith("art:") and v.get("nombre")
                      and normalizar(v.get("nombre")) in nombres_norm})
    lo = desde or hoy - dt.timedelta(days=45)
    hi = hoy + dt.timedelta(days=int(cfg.get("dias_adelante", 180)))
    maximo = int(cfg.get("max_artistas", 1000))
    for nombre in nombres[:maximo]:
        q = urllib.parse.quote(nombre)
        r = nav.get(f"https://api.deezer.com/search/artist?limit=5&q={q}", acepta="application/json")
        res.paginas += 1
        if r.estado != 200:
            continue
        cands = [a for a in json.loads(r.texto).get("data", []) if normalizar(a.get("name")) == normalizar(nombre)]
        if len(cands) != 1:          # homónimos: no se adivina
            continue
        r = nav.get(f"https://api.deezer.com/artist/{cands[0]['id']}/albums?limit=50", acepta="application/json")
        if r.estado != 200:
            continue
        for a in json.loads(r.texto).get("data", []):
            if a.get("record_type") != "album" or not a.get("release_date"):
                continue
            try:
                f = dt.date.fromisoformat(a["release_date"])
            except ValueError:
                continue
            if lo <= f <= hi:
                res.items.append(Item(fuente=cfg["id"], artista=nombre, titulo=a.get("title") or "", fecha=f,
                                      fecha_tipo="lanzamiento", url=a.get("link"), portada=a.get("cover_medium")))
    res.detalle = f"{len(nombres)} artistas consultados"
    return res
