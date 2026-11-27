"""Utilidades comunes de las pruebas: un navegador falso que sirve páginas de ejemplo."""
from __future__ import annotations

import datetime as dt
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from scraper.http import Bloqueado, Prohibido, Respuesta  # noqa: E402

HOY = dt.date(2026, 11, 22)


class NavegadorFalso:
    """Sustituye a scraper.http.Navegador: devuelve el contenido fijado para cada URL.
    Un valor puede ser texto (HTTP 200), (estado, texto) o una excepción que se lanza."""

    def __init__(self, paginas: dict):
        self.paginas = paginas
        self.pedidas: list[str] = []

    def get(self, url, usar_cache=True, acepta=None):
        self.pedidas.append(url)
        v = self.paginas.get(url)
        if v is None:
            return Respuesta(url, 404, "")
        if isinstance(v, Exception):
            raise v
        if isinstance(v, tuple):
            return Respuesta(url, v[0], v[1])
        return Respuesta(url, 200, v)


@pytest.fixture
def hoy():
    return HOY


@pytest.fixture
def nav_falso():
    return NavegadorFalso


@pytest.fixture
def excepciones():
    return {"bloqueado": Bloqueado("web.example: verificación anti-bots"),
            "prohibido": Prohibido("robots.txt no permite"),
            "conexion": ConnectionError("web.example: Timeout")}
