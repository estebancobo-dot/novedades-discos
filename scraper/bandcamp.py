"""Enriquecimiento con páginas de disco de Bandcamp (1 petición cada 4 s).

La búsqueda de Bandcamp está prohibida a robots en su robots.txt, así que solo
se abren páginas cuyo enlace ya conocemos (MusicBrainz o la propia fuente):
  - enlace directo al disco (…bandcamp.com/album/…), o
  - página del artista: se abre /music y se busca el disco por título.
De la página se leen los datos estructurados (JSON-LD): pistas, etiquetas,
portada y fecha."""
from __future__ import annotations

import json
import os
import re
from urllib.parse import urljoin, urlparse

from .http import Bloqueado, Navegador, Prohibido
from .util import similitud


class Bandcamp:
    def __init__(self, nav: Navegador, ruta_cache: str, maximo: int = 500, umbral: float = 0.86):
        self.nav, self.ruta, self.maximo, self.umbral = nav, ruta_cache, maximo, umbral
        self.abiertas = 0
        self.bloqueado = None
        self.cache = {}
        if os.path.exists(ruta_cache):
            with open(ruta_cache, encoding="utf-8") as f:
                self.cache = json.load(f)

    def guardar(self):
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=0, sort_keys=True)

    def _get(self, url):
        if self.bloqueado or self.abiertas >= self.maximo:
            return None
        try:
            self.abiertas += 1
            r = self.nav.get(url)
            return r if r.estado == 200 else None
        except Bloqueado as e:
            self.bloqueado = str(e)
        except (Prohibido, ConnectionError):
            pass
        return None

    def disco(self, titulo: str, url_disco: str | None, url_artista: str | None) -> dict | None:
        k = url_disco or f"{url_artista}|{titulo}"
        if k in self.cache:
            return self.cache[k] or None
        if not url_disco and url_artista:
            url_disco = self._buscar_en_artista(url_artista, titulo)
            if url_disco is None and (self.bloqueado or self.abiertas >= self.maximo):
                return None
        res = self._leer_disco(url_disco) if url_disco else {}
        if res is None:
            return None
        self.cache[k] = res
        return res or None

    def _buscar_en_artista(self, url_artista: str, titulo: str) -> str | None:
        u = urlparse(url_artista)
        if "bandcamp.com" not in (u.hostname or ""):
            return None
        base = f"{u.scheme}://{u.hostname}"
        r = self._get(base + "/music")
        if not r:
            return None
        mejor, puntos = None, 0.0
        for href, texto in re.findall(r'<a href="(/album/[^"?#]+)"[^>]*>(.*?)</a>', r.texto, re.S):
            nombre = re.sub(r"<[^>]+>", " ", texto)
            nombre = re.sub(r"\s+", " ", nombre).strip()
            s = max(similitud(nombre, titulo), similitud(href.split("/")[-1].replace("-", " "), titulo))
            if s > puntos:
                mejor, puntos = urljoin(base, href), s
        if mejor and puntos >= self.umbral:
            return mejor
        self.cache[f"{url_artista}|{titulo}"] = {}
        return ""

    def _leer_disco(self, url: str) -> dict | None:
        r = self._get(url)
        if not r:
            return None if (self.bloqueado or self.abiertas >= self.maximo) else {}
        m = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', r.texto, re.S)
        if not m:
            return {}
        try:
            d = json.loads(m.group(1))
        except ValueError:
            return {}
        etiquetas = d.get("keywords") or []
        if isinstance(etiquetas, str):
            etiquetas = [e.strip() for e in etiquetas.split(",")]
        imagen = d.get("image")
        if isinstance(imagen, list):
            imagen = imagen[0] if imagen else None
        pistas = d.get("numTracks")
        if not pistas and isinstance(d.get("track"), dict):
            pistas = d["track"].get("numberOfItems")
        return {
            "url": r.url,
            "titulo": d.get("name"),
            "artista": (d.get("byArtist") or {}).get("name") if isinstance(d.get("byArtist"), dict) else None,
            "fecha": (d.get("datePublished") or "")[:30] or None,
            "pistas": pistas,
            "etiquetas": [e for e in etiquetas if e],
            "portada": imagen,
            "sello": (d.get("publisher") or {}).get("name") if isinstance(d.get("publisher"), dict) else None,
        }
