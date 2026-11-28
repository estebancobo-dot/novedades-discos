"""Enriquecimiento con MusicBrainz (API pública, 1 petición/s) y Cover Art Archive.

Se guarda un resumen de cada consulta en data/cache/musicbrainz.json para no
repetirla en ejecuciones futuras (la Action semanal reutiliza esa caché)."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.parse
from collections import Counter

from .http import Bloqueado, Navegador, guardar_json
from .util import normalizar, similitud

API = "https://musicbrainz.org/ws/2/"


def _esc(s: str) -> str:
    return re.sub(r'([+\-&|!(){}\[\]^"~*?:\\/])', r"\\\1", s)


def _mismo_apellido_e_inicial(a: str, b: str) -> bool:
    """"Mike Hurley" y "Michael Hurley", "Bob Dylan" y "Robert Dylan" no (distinta inicial)."""
    x, y = normalizar(a).split(), normalizar(b).split()
    return len(x) >= 2 and len(y) >= 2 and x[-1] == y[-1] and x[0][0] == y[0][0]


class MusicBrainz:
    def __init__(self, nav: Navegador, ruta_cache: str, umbral: float = 0.86, dias_reintento: int = 10):
        self.dias_reintento = dias_reintento
        self.nav = nav
        self.ruta = ruta_cache
        self.umbral = umbral
        self.cache = {}
        self.consultas = 0
        self.bloqueado = None
        if os.path.exists(ruta_cache):
            with open(ruta_cache, encoding="utf-8") as f:
                self.cache = json.load(f)

    def guardar(self):
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        for _ in range(5):      # otro hilo puede estar completando una entrada justo ahora
            try:
                guardar_json(self.ruta, dict(self.cache), ensure_ascii=False, indent=0, sort_keys=True)
                return
            except RuntimeError:
                continue

    def _json(self, ruta: str) -> dict | None:
        if self.bloqueado:
            return None
        try:
            r = self.nav.get(API + ruta, usar_cache=True, acepta="application/json")
        except Bloqueado as e:
            self.bloqueado = str(e)
            return None
        except ConnectionError:
            return None
        self.consultas += 1
        if r.estado != 200:
            return None
        try:
            return json.loads(r.texto)
        except ValueError:
            return None

    # ------------------------------------------------------------ búsqueda
    def buscar(self, artista: str, titulo: str, intercambiable: bool = False, completar: bool = True) -> dict | None:
        """Busca el disco. Con completar=False no pide aún los detalles (sellos,
        pistas, idioma, enlaces): se piden luego con completar() si hacen falta."""
        k = f"rg:{normalizar(artista)}|{normalizar(titulo)}"
        res = self.cache.get(k)
        if res is not None and "no_encontrado" in res:
            dias = (dt.date.today() - dt.date.fromisoformat(res["no_encontrado"])).days
            if dias >= self.dias_reintento:
                res = None
        if res is None:
            res = self._buscar(artista, titulo)
            if res is None:          # error de red o bloqueo: no se guarda
                return None
            self.cache[k] = res or {"no_encontrado": dt.date.today().isoformat()}
        if "no_encontrado" in res:
            res = {}
        if not res and intercambiable:
            return self.buscar(titulo, artista, False, completar)
        if res and completar:
            self.completar(res)
        return res or None

    def completar(self, res: dict) -> dict:
        """Añade sellos, pistas, idioma, enlaces y portada (una consulta más)."""
        if res.get("rg") and "release" not in res:
            extra = self._releases(res["rg"])
            if extra is not None:
                res.update(extra)
        return res

    def _buscar(self, artista: str, titulo: str) -> dict | None:
        q = f'releasegroup:"{_esc(titulo)}" AND artist:"{_esc(artista)}"'
        d = self._json("release-group/?fmt=json&limit=8&query=" + urllib.parse.quote(q))
        if d is None:
            return None
        mejor, puntos = None, 0.0
        for rg in d.get("release-groups", []):
            nombre = "".join((a.get("name") or "") + (a.get("joinphrase") or "") for a in rg.get("artist-credit", []))
            st = similitud(rg.get("title"), titulo)
            sa = max(similitud(nombre, artista), *(similitud(a.get("name"), artista) for a in rg.get("artist-credit", [{}])))
            if normalizar(artista) and normalizar(artista) in normalizar(nombre):
                sa = max(sa, 0.95)
            # mismo título y mismo artista con el nombre de pila abreviado ("Mike"/"Michael Hurley")
            if st >= 0.97 and sa < self.umbral and _mismo_apellido_e_inicial(nombre, artista):
                sa = self.umbral
            p = st * 0.6 + sa * 0.4
            # Mismo nombre para el disco y su sencillo (la canción que da título): a igualdad, el disco.
            p += {"Album": 0.02, "EP": 0.01}.get(rg.get("primary-type") or "", 0.0)
            if st >= self.umbral and sa >= self.umbral and p > puntos:
                mejor, puntos = rg, p
        if not mejor:
            return {}
        res = {
            "rg": mejor["id"],
            "titulo": mejor.get("title"),
            "artista": "".join((a.get("name") or "") + (a.get("joinphrase") or "") for a in mejor.get("artist-credit", [])),
            "artistas_id": [a["artist"]["id"] for a in mejor.get("artist-credit", []) if a.get("artist")],
            "tipo": mejor.get("primary-type"),
            "tipos_secundarios": mejor.get("secondary-types", []),
            "primera_fecha": mejor.get("first-release-date"),
            "puntuacion": round(puntos, 3),
        }
        return res

    def _releases(self, rg: str) -> dict | None:
        d = self._json(f"release?release-group={rg}&inc=labels+media+url-rels&fmt=json&limit=50")
        if d is None:
            return None
        rels = d.get("releases", [])
        idiomas = Counter(r.get("text-representation", {}).get("language") for r in rels
                          if r.get("text-representation", {}).get("language"))
        oficiales = [r for r in rels if r.get("status") in (None, "Official")] or rels
        oficiales.sort(key=lambda r: (r.get("date") or "9999"))
        elegido = oficiales[0] if oficiales else {}
        sellos = [li["label"]["name"] for li in elegido.get("label-info", []) if li.get("label")]
        pistas = sum(m.get("track-count") or 0 for m in elegido.get("media", [])) or None
        enlaces = {}
        for r in rels:
            for u in r.get("relations", []):
                url = (u.get("url") or {}).get("resource")
                if url:
                    enlaces.setdefault(_servicio(url), url)
        portada = any((r.get("cover-art-archive") or {}).get("front") for r in rels)
        return {
            "release": elegido.get("id"),
            "fecha_release": elegido.get("date"),
            "pais": elegido.get("country"),
            "idioma": idiomas.most_common(1)[0][0] if idiomas else None,
            "sellos": sellos,
            "pistas": pistas,
            "enlaces": enlaces,
            "portada": f"https://coverartarchive.org/release-group/{rg}/front-250" if portada else None,
        }

    # -------------------------------------------------------------- artista
    def artista(self, mbid: str) -> dict:
        k = f"art:{mbid}"
        if k in self.cache:
            return self.cache[k]
        d = self._json(f"artist/{mbid}?inc=genres+tags+url-rels&fmt=json")
        if d is None:
            return {}
        res = {
            "nombre": d.get("name"),
            "pais": d.get("country"),
            "generos": [g["name"] for g in sorted(d.get("genres", []), key=lambda g: -g.get("count", 0))],
            "etiquetas": [t["name"] for t in sorted(d.get("tags", []), key=lambda t: -t.get("count", 0)) if t.get("count", 0) > 0][:15],
            "enlaces": {},
        }
        for u in d.get("relations", []):
            url = (u.get("url") or {}).get("resource")
            if url:
                res["enlaces"].setdefault(_servicio(url), url)
        self.cache[k] = res
        return res


def _servicio(url: str) -> str:
    h = urllib.parse.urlparse(url).hostname or ""
    for nombre in ("bandcamp", "spotify", "apple", "deezer", "tidal", "qobuz", "youtube", "discogs",
                   "allmusic", "wikidata", "wikipedia", "soundcloud", "amazon", "facebook", "instagram"):
        if nombre in h:
            return nombre
    return h.replace("www.", "")
