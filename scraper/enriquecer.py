"""Etiquetas extra para clasificar:  python -m scraper.enriquecer

Solo para los discos que, con lo ya recogido, no tienen ningún subgénero
(o solo subgéneros frontera). Consulta, por este orden y según data/config.yaml:
  - Wikidata: géneros del artista (P136). API pública, sin clave.
  - Discogs: estilos del disco. API pública; sin clave solo por identificador
    (el enlace sale de MusicBrainz); con DISCOGS_TOKEN también busca.
  - Last.fm: etiquetas de los oyentes del disco o del artista (necesita LASTFM_KEY).
El resultado se guarda en cada candidato (etiquetas_extra) y en una caché."""
from __future__ import annotations

import json
import os
import re
import urllib.parse
from collections import Counter

from .clasificar import Taxonomia, cargar_mapeo, clasificar_disco
from .config import RAIZ, cargar_config, cargar_yaml, ruta
from .http import Bloqueado, Navegador, Prohibido, guardar_json
from .util import normalizar, similitud


class Extras:
    def __init__(self, nav: Navegador, cfg: dict, ruta_cache: str):
        self.nav, self.cfg, self.ruta = nav, cfg, ruta_cache
        self.cache = json.load(open(ruta_cache, encoding="utf-8")) if os.path.exists(ruta_cache) else {}
        self.bloqueos: dict[str, str] = {}
        self.consultas = Counter()

    def guardar(self):
        guardar_json(self.ruta, dict(self.cache), ensure_ascii=False, indent=0, sort_keys=True)

    def _json(self, servicio: str, url: str, cab: dict | None = None):
        if servicio in self.bloqueos:
            return None
        try:
            r = self.nav.get(url, acepta="application/json")
        except Bloqueado as e:
            self.bloqueos[servicio] = str(e)
            return None
        except (Prohibido, ConnectionError):
            return None
        self.consultas[servicio] += 1
        if r.estado != 200:
            return None
        try:
            return json.loads(r.texto)
        except ValueError:
            return None

    # ------------------------------------------------------------ Wikidata
    def wikidata(self, url_wd: str) -> list[str]:
        m = re.search(r"(Q\d+)", url_wd or "")
        if not m:
            return []
        k = f"wd:{m.group(1)}"
        if k in self.cache:
            return self.cache[k]
        d = self._json("wikidata", f"https://www.wikidata.org/wiki/Special:EntityData/{m.group(1)}.json")
        if d is None:
            return []
        ent = next(iter(d.get("entities", {}).values()), {})
        ids = [c["mainsnak"]["datavalue"]["value"]["id"] for c in ent.get("claims", {}).get("P136", [])
               if c.get("mainsnak", {}).get("datavalue")]
        nombres = [self._etiqueta_wd(q) for q in ids[:12]]
        self.cache[k] = [n for n in nombres if n]
        return self.cache[k]

    def _etiqueta_wd(self, q: str) -> str | None:
        k = f"wdl:{q}"
        if k not in self.cache:
            d = self._json("wikidata", "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
                                       f"&props=labels&languages=en&ids={q}")
            if d is None:
                return None
            self.cache[k] = (d.get("entities", {}).get(q, {}).get("labels", {}).get("en") or {}).get("value")
        return self.cache[k]

    # -------------------------------------------------------------- Discogs
    def discogs(self, url_disco: str | None, url_artista: str | None, titulo: str) -> list[str]:
        token = os.environ.get(self.cfg.get("discogs", {}).get("variable_token", "DISCOGS_TOKEN"), "")
        sufijo = f"&token={token}" if token else ""
        if url_disco:
            m = re.search(r"discogs\.com/(?:[^/]+/)?(release|master)/(\d+)", url_disco)
            if m:
                return self._discogs_estilos(m.group(1), m.group(2), sufijo)
        m = re.search(r"discogs\.com/(?:[^/]+/)?artist/(\d+)", url_artista or "")
        if not m:
            return []
        k = f"dga:{m.group(1)}|{normalizar(titulo)}"
        if k in self.cache:
            return self.cache[k]
        d = self._json("discogs", f"https://api.discogs.com/artists/{m.group(1)}/releases"
                                  f"?sort=year&sort_order=desc&per_page=40{sufijo}")
        if d is None:
            return []
        mejor = max(d.get("releases", []), key=lambda r: similitud(r.get("title"), titulo), default=None)
        res = []
        if mejor and similitud(mejor.get("title"), titulo) >= 0.86:
            tipo = "master" if mejor.get("type") == "master" else "release"
            res = self._discogs_estilos(tipo, str(mejor["id"]), sufijo)
        self.cache[k] = res
        return res

    def _discogs_estilos(self, tipo: str, ident: str, sufijo: str) -> list[str]:
        k = f"dg:{tipo}:{ident}"
        if k not in self.cache:
            d = self._json("discogs", f"https://api.discogs.com/{tipo}s/{ident}?{sufijo.lstrip('&')}")
            if d is None:
                return []
            self.cache[k] = list(dict.fromkeys((d.get("styles") or []) + (d.get("genres") or [])))
        return self.cache[k]

    # ---------------------------------------------------------------- Deezer
    def deezer(self, artista: str, titulo: str) -> dict:
        """Disco en Deezer (API pública, sin clave): enlace, tipo (album/ep/single),
        fecha, pistas y portada. Sirve también para el reproductor de 30 s."""
        k = f"dz:{normalizar(artista)}|{normalizar(titulo)}"
        if k in self.cache:
            return self.cache[k]
        q = urllib.parse.quote(f'artist:"{artista}" album:"{titulo}"')
        d = self._json("deezer", f"https://api.deezer.com/search/album?limit=10&q={q}")
        if d is None:
            return {}
        mejor, puntos = None, 0.0
        for a in d.get("data", []):
            st, sa = similitud(a.get("title"), titulo), similitud((a.get("artist") or {}).get("name"), artista)
            if st >= 0.86 and sa >= 0.86 and st + sa > puntos:
                mejor, puntos = a, st + sa
        res = {}
        if mejor:
            res = {"id": mejor["id"], "url": mejor.get("link"), "tipo": mejor.get("record_type"),
                   "pistas": mejor.get("nb_tracks"), "portada": mejor.get("cover_medium"),
                   "portada_grande": mejor.get("cover_xl") or mejor.get("cover_big")}
        self.cache[k] = res
        return res

    # ---------------------------------------------------------------- iTunes
    def itunes(self, artista: str, titulo: str) -> dict:
        """Disco en Apple (API de búsqueda de iTunes, sin clave): enlace, género, pistas."""
        k = f"it:{normalizar(artista)}|{normalizar(titulo)}"
        if k in self.cache:
            return self.cache[k]
        q = urllib.parse.quote(f"{artista} {titulo}")
        d = self._json("itunes", f"https://itunes.apple.com/search?entity=album&limit=10&term={q}")
        if d is None:
            return {}
        mejor, puntos = None, 0.0
        for a in d.get("results", []):
            st, sa = similitud(a.get("collectionName"), titulo), similitud(a.get("artistName"), artista)
            if st >= 0.86 and sa >= 0.86 and st + sa > puntos:
                mejor, puntos = a, st + sa
        res = {}
        if mejor:
            res = {"url": mejor.get("collectionViewUrl"), "genero": mejor.get("primaryGenreName"),
                   "pistas": mejor.get("trackCount"), "fecha": (mejor.get("releaseDate") or "")[:10]}
        self.cache[k] = res
        return res

    # --------------------------------------------------------------- Last.fm
    def lastfm(self, artista: str, titulo: str) -> list[str]:
        clave = os.environ.get(self.cfg.get("lastfm", {}).get("variable_clave", "LASTFM_KEY"), "")
        if not clave:
            return []
        k = f"lfm:{normalizar(artista)}|{normalizar(titulo)}"
        if k in self.cache:
            return self.cache[k]
        base = "https://ws.audioscrobbler.com/2.0/?format=json&autocorrect=1&api_key=" + clave
        q = "&artist=" + urllib.parse.quote(artista)
        d = self._json("lastfm", base + "&method=album.gettoptags" + q + "&album=" + urllib.parse.quote(titulo))
        tags = [t["name"] for t in ((d or {}).get("toptags") or {}).get("tag", []) if int(t.get("count", 0)) >= 10]
        if not tags:
            d = self._json("lastfm", base + "&method=artist.gettoptags" + q)
            tags = [t["name"] for t in ((d or {}).get("toptags") or {}).get("tag", []) if int(t.get("count", 0)) >= 10]
        self.cache[k] = tags[:12]
        return self.cache[k]


def main():
    config = cargar_config()
    R = config["rutas"]
    cfg = config["enriquecimiento"].get("etiquetas_extra") or {}
    tax = Taxonomia(cargar_yaml(R["taxonomia"]))
    mapeo = cargar_mapeo(ruta(R["mapeo_etiquetas"]))
    nav = Navegador(config, RAIZ)
    ex = Extras(nav, cfg, ruta(R["cache_etiquetas_extra"]))
    mb = json.load(open(ruta(R["cache_musicbrainz"]), encoding="utf-8"))
    p = ruta(R["candidatos"])
    with open(p, encoding="utf-8") as f:
        candidatos = json.load(f)
    artistas_de = {v["rg"]: v.get("artistas_id", []) for k, v in mb.items() if k.startswith("rg:") and v.get("rg")}
    pendientes, resueltos = 0, 0
    usar_deezer = cfg.get("deezer", {}).get("activo")
    usar_itunes = cfg.get("itunes", {}).get("activo")
    for n, d in enumerate(candidatos, 1):
        if usar_deezer:                          # a todos: enlace, tipo, reproductor y portada
            dz = ex.deezer(d["artista"], d["titulo"])
            if dz:
                d["deezer"] = dz
                d.setdefault("enlaces", {}).setdefault("deezer", dz.get("url"))
                if not d.get("portada") and dz.get("portada"):
                    d["portada"] = dz["portada"]
                if not d.get("pistas") and dz.get("pistas"):
                    d["pistas"] = dz["pistas"]
        r = clasificar_disco(d, tax, mapeo, Counter(), {})
        utiles = [s for s in r["subgeneros"] if not tax.sub[s]["frontera"]]
        if utiles and not cfg.get("todos"):
            continue
        pendientes += 1
        ids = d.get("mbid_artistas") or artistas_de.get(d.get("mbid"), [])
        art = mb.get(f"art:{ids[0]}") if ids else None
        enl_art = (art or {}).get("enlaces", {}) if art else {}
        extra = []
        if cfg.get("wikidata", {}).get("activo") and enl_art.get("wikidata"):
            extra += [{"etiqueta": e, "origen": "wikidata"} for e in ex.wikidata(enl_art["wikidata"])]
        if cfg.get("discogs", {}).get("activo"):
            extra += [{"etiqueta": e, "origen": "discogs"}
                      for e in ex.discogs(d.get("enlaces", {}).get("discogs"), enl_art.get("discogs"), d["titulo"])]
        if cfg.get("lastfm", {}).get("activo"):
            extra += [{"etiqueta": e, "origen": "lastfm"} for e in ex.lastfm(d["artista"], d["titulo"])]
        if usar_itunes:                          # solo a los que siguen sin subgénero (va a 20/min)
            it = ex.itunes(d["artista"], d["titulo"])
            if it:
                d.setdefault("enlaces", {}).setdefault("apple", it.get("url"))
                if it.get("genero"):
                    extra.append({"etiqueta": it["genero"], "origen": "itunes"})
        d["etiquetas_extra"] = extra
        if extra and clasificar_disco(d, tax, mapeo, Counter(), {})["subgeneros"]:
            resueltos += 1
        if n % 50 == 0:
            ex.guardar()
            print(f"  {n}/{len(candidatos)} · consultas {dict(ex.consultas)}", flush=True)
    ex.guardar()
    with open(p, "w", encoding="utf-8") as f:
        json.dump(candidatos, f, ensure_ascii=False, indent=1)
    estado_p = ruta(R["estado_fuentes"])
    estado = json.load(open(estado_p, encoding="utf-8")) if os.path.exists(estado_p) else {}
    estado["etiquetas_extra"] = {"discos_sin_subgenero": pendientes, "con_subgenero_tras_extra": resueltos,
                                 "consultas": dict(ex.consultas), "bloqueos": ex.bloqueos,
                                 "lastfm_sin_clave": not os.environ.get(cfg.get("lastfm", {}).get("variable_clave", "LASTFM_KEY"))}
    with open(estado_p, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=1)
    print(f"Sin subgénero: {pendientes} · resueltos con etiquetas extra: {resueltos} · consultas {dict(ex.consultas)}")


if __name__ == "__main__":
    main()
