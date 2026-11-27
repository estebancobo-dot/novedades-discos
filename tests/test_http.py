"""Cliente HTTP educado: bloqueos, 429/503, ritmo con varios hilos, caché y escritura atómica."""
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from scraper.config import cargar_config
from scraper.http import Bloqueado, Navegador, guardar_json


class RespuestaFalsa:
    def __init__(self, estado, texto="", cabeceras=None, url="https://web.example/x"):
        self.status_code, self.text, self.headers, self.url = estado, texto, cabeceras or {}, url
        self.encoding, self.apparent_encoding = "utf-8", "utf-8"


class SesionFalsa:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = 0

    def get(self, url, headers=None, timeout=None):
        self.llamadas += 1
        return self.respuestas.pop(0)


@pytest.fixture
def nav(tmp_path, monkeypatch):
    cfg = cargar_config()
    cfg["rutas"] = dict(cfg["rutas"], cache_http=str(tmp_path / "http"))
    cfg["peticiones"] = dict(cfg["peticiones"], intervalo_por_defecto=0.0, intervalos={}, respetar_robots_txt=False)
    n = Navegador(cfg, str(tmp_path))
    monkeypatch.setattr(time, "sleep", lambda s: None)          # las esperas no hacen falta en la prueba
    return n


def test_detecta_verificacion_anti_bots(nav):
    assert nav.es_bloqueo(200, "<html><title>Just a moment...</title>", {})
    assert nav.es_bloqueo(200, "ok", {"cf-mitigated": "challenge"})
    assert nav.es_bloqueo(403, "prohibido", {})
    assert not nav.es_bloqueo(200, "<title>Reseñas</title>", {})


def test_bloqueo_marca_la_web_y_no_vuelve_a_pedir(nav):
    nav.sesion = SesionFalsa([RespuestaFalsa(200, "<title>Just a moment...</title>")])
    with pytest.raises(Bloqueado):
        nav.get("https://web.example/a")
    with pytest.raises(Bloqueado):
        nav.get("https://web.example/b")                    # ya no se pide: se deja la web
    assert nav.sesion.llamadas == 1


def test_429_espera_y_reintenta_antes_de_bloquear(nav):
    nav.sesion = SesionFalsa([RespuestaFalsa(429, cabeceras={"Retry-After": "3"}), RespuestaFalsa(200, "bien")])
    r = nav.get("https://web.example/api")
    assert r.estado == 200 and r.texto == "bien" and nav.sesion.llamadas == 2


def test_429_persistente_acaba_en_bloqueo(nav):
    nav.sesion = SesionFalsa([RespuestaFalsa(429)] * 3)
    with pytest.raises(Bloqueado):
        nav.get("https://web.example/api")
    assert nav.sesion.llamadas == 3                         # 1 + 2 reintentos


def test_503_de_musicbrainz_se_reintenta(nav):
    nav.sesion = SesionFalsa([RespuestaFalsa(503), RespuestaFalsa(503), RespuestaFalsa(200, "{}")])
    assert nav.get("https://musicbrainz.org/ws/2/x").estado == 200


def test_cache_evita_repetir_peticion(nav):
    nav.sesion = SesionFalsa([RespuestaFalsa(200, "uno")])
    assert nav.get("https://web.example/c").texto == "uno"
    assert nav.get("https://web.example/c").desde_cache
    assert nav.sesion.llamadas == 1


def test_404_no_se_guarda_ni_bloquea(nav):
    nav.sesion = SesionFalsa([RespuestaFalsa(404, "no"), RespuestaFalsa(200, "ya")])
    assert nav.get("https://web.example/d").estado == 404
    assert nav.get("https://web.example/d").estado == 200


def test_ritmo_con_hilos_nunca_baja_del_intervalo(tmp_path):
    cfg = cargar_config()
    cfg["rutas"] = dict(cfg["rutas"], cache_http=str(tmp_path / "http"))
    cfg["peticiones"] = dict(cfg["peticiones"], intervalos={"lento.example": 0.2})
    n = Navegador(cfg, str(tmp_path))
    inicios, candado = [], threading.Lock()

    def tarea(_):
        n._esperar("lento.example")
        with candado:
            inicios.append(time.time())
        time.sleep(0.5)                                     # respuesta lenta

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(tarea, range(8)))
    inicios.sort()
    assert min(b - a for a, b in zip(inicios, inicios[1:])) >= 0.19


def test_guardar_json_es_atomico(tmp_path):
    p = tmp_path / "datos.json"
    guardar_json(str(p), {"a": 1})
    assert json.loads(p.read_text()) == {"a": 1}
    with pytest.raises(TypeError):
        guardar_json(str(p), {"no serializable": object()})
    assert json.loads(p.read_text()) == {"a": 1}            # el archivo bueno sigue intacto
    assert not [f for f in os.listdir(tmp_path) if f.endswith(".tmp")]    # sin restos
