"""Normalización, similitud y fechas: escenarios normales, de borde y erróneos."""
import datetime as dt

import pytest

from scraper.util import clave, limpiar, normalizar, parse_fecha, restar_meses, similitud

HOY = dt.date(2026, 11, 22)


@pytest.mark.parametrize("entrada,esperado", [
    ("The Beatles", "beatles"),
    ("Mötley Crüe", "motley crue"),
    ("Simon & Garfunkel", "simon and garfunkel"),
    ("Guns N’ Roses", "guns n roses"),
    ("  Varios   espacios ", "varios espacios"),
    (None, ""),
    ("", ""),
    ("!!!", ""),
])
def test_normalizar(entrada, esperado):
    assert normalizar(entrada) == esperado


def test_clave_ignora_mayusculas_articulos_y_acentos():
    assert clave("The Band", "Stage Fright") == clave("band", "STAGE FRIGHT")
    assert clave("Beyoncé", "Cowboy Carter") == clave("Beyonce", "Cowboy Carter")


def test_similitud_extremos():
    assert similitud("Abc", "abc") == 1.0
    assert similitud(None, "x") == 0.0
    assert similitud("", "") == 0.0
    assert 0.0 < similitud("Long Way Home", "Long Way Home (Deluxe)") <= 1.0


def test_limpiar_espacios_y_vacios():
    assert limpiar("  hola \n mundo ") == "hola mundo"
    assert limpiar(None) is None


@pytest.mark.parametrize("texto,esperado", [
    ("November 13, 2026", dt.date(2026, 11, 13)),
    ("Sept. 11th, 2026", dt.date(2026, 9, 11)),
    ("Fri, 20 Nov 2026 10:00:00 +0000", dt.date(2026, 11, 20)),
    ("2026-03-06", dt.date(2026, 3, 6)),
    ("07/24/2026", dt.date(2026, 7, 24)),
])
def test_parse_fecha_formatos(texto, esperado):
    assert parse_fecha(texto, HOY) == esperado


def test_parse_fecha_sin_anio_elige_el_mas_cercano():
    # En noviembre, "January 9" es el próximo enero, no el pasado
    assert parse_fecha("January 9", HOY) == dt.date(2027, 1, 9)
    assert parse_fecha("October 30", HOY) == dt.date(2026, 10, 30)
    assert parse_fecha("12-5", HOY) == dt.date(2026, 12, 5)


def test_parse_fecha_dia_primero():
    assert parse_fecha("5-12", HOY, dia_primero=True) == dt.date(2026, 12, 5)


@pytest.mark.parametrize("basura", [None, "", "   ", "(TBA)", "fecha por anunciar xyz"])
def test_parse_fecha_basura_no_rompe(basura):
    r = parse_fecha(basura, HOY)
    assert r is None or isinstance(r, dt.date)


def test_parse_fecha_29_febrero_sin_anio_no_rompe():
    r = parse_fecha("February 29", HOY)
    assert r is None or (r.month, r.day) == (2, 29)


@pytest.mark.parametrize("d,n,esperado", [
    (dt.date(2026, 11, 22), 5, dt.date(2026, 6, 22)),
    (dt.date(2026, 1, 31), 1, dt.date(2025, 12, 31)),
    (dt.date(2026, 3, 31), 1, dt.date(2026, 2, 28)),       # fin de mes más corto
    (dt.date(2026, 11, 22), -6, dt.date(2027, 5, 22)),     # hacia delante
])
def test_restar_meses(d, n, esperado):
    assert restar_meses(d, n) == esperado
