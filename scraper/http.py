"""Peticiones web educadas: ritmo por web, caché en disco, robots.txt y
detección de verificaciones anti-bots (que nunca se intentan saltar)."""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import urlparse

import requests


def guardar_json(ruta: str, datos, **kw) -> None:
    """Escritura atómica: si el proceso se corta a medias, el archivo anterior queda intacto."""
    tmp = f"{ruta}.{os.getpid()}.{threading.get_ident()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, **kw)
    os.replace(tmp, ruta)


class Bloqueado(Exception):
    """La web ha respondido con una verificación anti-bots o un bloqueo."""


class Prohibido(Exception):
    """robots.txt no permite leer esa dirección."""


@dataclass
class Respuesta:
    url: str
    estado: int
    texto: str
    desde_cache: bool = False


class Navegador:
    def __init__(self, config: dict, raiz: str):
        p = config["peticiones"]
        self.ua = config["identificacion"]["user_agent"]
        self.ua_mb = config["identificacion"]["user_agent_musicbrainz"]
        self.intervalo_def = float(p["intervalo_por_defecto"])
        self.intervalos = {k: float(v) for k, v in (p.get("intervalos") or {}).items()}
        self.timeout = p.get("timeout", 30)
        self.robots = p.get("respetar_robots_txt", True)
        self.apis = list(p.get("apis_documentadas") or [])
        self.cache_seg = float(p.get("cache_horas", 20)) * 3600
        self.reintentos_503 = int(p.get("reintentos_503", 5))
        self.reintentos_429 = int(p.get("reintentos_429", 2))
        b = config["bloqueo"]
        self.bloq_estados = set(b.get("estados", []))
        self.bloq_textos = [t.lower() for t in b.get("textos", [])]
        self.bloq_cabeceras = {k.lower(): v.lower() for k, v in (b.get("cabeceras") or {}).items()}
        self.dir_cache = os.path.join(raiz, config["rutas"]["cache_http"])
        os.makedirs(self.dir_cache, exist_ok=True)
        self.ultimo: dict[str, float] = {}
        self._candados: dict[str, threading.Lock] = {}
        self._candado_global = threading.Lock()
        self.hosts_bloqueados: dict[str, str] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.sesion = requests.Session()
        self.peticiones = 0

    # ------------------------------------------------------------------ util
    def _host(self, url: str) -> str:
        h = urlparse(url).hostname or ""
        return h[4:] if h.startswith("www.") else h

    def _intervalo(self, host: str) -> float:
        for k, v in self.intervalos.items():
            if host == k or host.endswith("." + k):
                return v
        return self.intervalo_def

    def _esperar(self, host: str) -> None:
        """Respeta el intervalo entre el inicio de dos peticiones a la misma web,
        también si varias consultas van en paralelo (un candado por web)."""
        with self._candado_global:
            candado = self._candados.setdefault(host, threading.Lock())
        with candado:
            falta = self._intervalo(host) - (time.time() - self.ultimo.get(host, 0))
            if falta > 0:
                time.sleep(falta)
            self.ultimo[host] = time.time()

    @staticmethod
    def _segundos_retry_after(valor: str | None) -> float:
        try:
            return max(0.0, float(valor)) if valor else 0.0
        except ValueError:
            return 0.0          # fecha HTTP u otro formato: se usa la espera por defecto

    def _ruta_cache(self, url: str) -> str:
        return os.path.join(self.dir_cache, hashlib.sha1(url.encode()).hexdigest() + ".json")

    def _ua(self, url: str) -> str:
        return self.ua_mb if "musicbrainz.org" in url else self.ua

    # ---------------------------------------------------------------- robots
    def _permitido(self, url: str) -> bool:
        if not self.robots or any(url.startswith(a) for a in self.apis):
            return True
        u = urlparse(url)
        base = f"{u.scheme}://{u.netloc}"
        if base not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                self._esperar(self._host(url))
                r = self.sesion.get(base + "/robots.txt", headers={"User-Agent": self._ua(url)}, timeout=self.timeout)
                if r.status_code == 200 and "<html" not in r.text[:500].lower():
                    rp.parse(r.text.splitlines())
                    self._robots[base] = rp
                else:
                    self._robots[base] = None
            except requests.RequestException:
                self._robots[base] = None
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(self._ua(url), url)

    # ------------------------------------------------------------- principal
    def es_bloqueo(self, estado: int, texto: str, cabeceras: dict) -> str | None:
        cab = {k.lower(): str(v).lower() for k, v in cabeceras.items()}
        for k, v in self.bloq_cabeceras.items():
            if v in cab.get(k, ""):
                return f"cabecera {k}: {v}"
        inicio = texto[:6000].lower()
        for t in self.bloq_textos:
            if t in inicio:
                return f"página de verificación ({t.strip('<>').replace('title>', '')})"
        if estado in self.bloq_estados:
            return f"HTTP {estado}"
        return None

    def get(self, url: str, usar_cache: bool = True, acepta: str | None = None) -> Respuesta:
        host = self._host(url)
        if host in self.hosts_bloqueados:
            raise Bloqueado(self.hosts_bloqueados[host])
        ruta = self._ruta_cache(url)
        if usar_cache and os.path.exists(ruta) and time.time() - os.path.getmtime(ruta) < self.cache_seg:
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            return Respuesta(d["url"], d["estado"], d["texto"], True)
        if not self._permitido(url):
            raise Prohibido(f"robots.txt de {host} no permite {url}")
        cab = {"User-Agent": self._ua(url), "Accept-Language": "en-US,en;q=0.8"}
        if acepta:
            cab["Accept"] = acepta
        intento = 0
        while True:
            self._esperar(host)
            self.peticiones += 1
            try:
                r = self.sesion.get(url, headers=cab, timeout=self.timeout)
            except requests.RequestException as e:
                if intento < 2:
                    intento += 1
                    time.sleep(5 * intento)
                    continue
                raise ConnectionError(f"{host}: {type(e).__name__}") from e
            if r.status_code == 503 and "musicbrainz.org" in host and intento < self.reintentos_503:
                intento += 1
                time.sleep(3 * intento)
                continue
            # 429 = "vas demasiado rápido": se espera lo que pida la web y se reintenta (dos veces).
            # Si sigue, se trata como bloqueo y se deja la web.
            if r.status_code == 429 and intento < self.reintentos_429:
                intento += 1
                time.sleep(min(self._segundos_retry_after(r.headers.get("Retry-After")), 120) or 20 * intento)
                continue
            break
        r.encoding = r.encoding if r.encoding and r.encoding.lower() != "iso-8859-1" else (r.apparent_encoding or "utf-8")
        texto = r.text
        motivo = self.es_bloqueo(r.status_code, texto, r.headers)
        if motivo and r.status_code != 404:
            self.hosts_bloqueados[host] = f"{host}: {motivo}"
            raise Bloqueado(self.hosts_bloqueados[host])
        resp = Respuesta(r.url, r.status_code, texto)
        if r.status_code == 200:
            guardar_json(ruta, {"url": r.url, "estado": r.status_code, "texto": texto})
        return resp
