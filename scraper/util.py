"""Utilidades genéricas: normalización de texto, fechas y similitud."""
from __future__ import annotations

import datetime as dt
import difflib
import html
import re
import unicodedata

from dateutil import parser as dparser

MARCAS = "«»⟦⟧⟪⟫"


def limpiar(valor: str | None) -> str | None:
    """Quita marcas internas, entidades y espacios sobrantes."""
    if valor is None:
        return None
    v = html.unescape(valor)
    v = re.sub(r"⟦[^⟧]*⟧|⟪[^⟫]*⟫", " ", v)
    v = v.replace("«", " ").replace("»", " ").replace("**", " ")
    v = v.replace("\xa0", " ").replace("​", "")
    v = re.sub(r"\s+", " ", v).strip()
    v = v.strip(" -–—|:,;\"'“”‘’")
    return v or None


def sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


CALIFICADORES = re.compile(
    r"\s*[\(\[][^\)\]]*(edition|version|deluxe|remaster|expanded|bonus|vinyl|cd|lp|digital|explicit|"
    r"signed|exclusive|pre-?order|colou?r)[^\)\]]*[\)\]]",
    re.I,
)


def normalizar(s: str | None) -> str:
    """Clave de comparación: minúsculas, sin acentos, sin artículos ni signos."""
    if not s:
        return ""
    s = limpiar(s) or ""
    s = CALIFICADORES.sub("", s)
    s = sin_acentos(s).lower()
    s = s.replace("&", " and ").replace("+", " and ")
    s = re.sub(r"['’`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"^(the|a|an) ", "", s.strip())
    return re.sub(r"\s+", " ", s).strip()


def clave(artista: str | None, titulo: str | None) -> str:
    return f"{normalizar(artista)}|{normalizar(titulo)}"


def similitud(a: str | None, b: str | None) -> float:
    na, nb = normalizar(a), normalizar(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


MESES = "january|february|march|april|may|june|july|august|september|october|november|december"


def parse_fecha(texto: str | None, hoy: dt.date, dia_primero: bool = False) -> dt.date | None:
    """Convierte textos como 'November 13, 2026', 'September 11th', '07/24/2026',
    '9-14' o fechas RSS en una fecha. Si falta el año, se elige el más cercano a hoy."""
    if not texto:
        return None
    t = limpiar(texto) or ""
    t = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", t, flags=re.I)
    t = re.sub(r"\bSept\b", "Sep", t, flags=re.I)
    t = re.sub(r"\(.*?\)", "", t).strip()
    if not t:
        return None
    m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})", t)
    if m:  # mes-día sin año
        a, b = int(m.group(1)), int(m.group(2))
        mes, dia = (b, a) if dia_primero else (a, b)
        return _anio_cercano(mes, dia, hoy)
    tiene_anio = bool(re.search(r"\b(19|20)\d{2}\b", t))
    try:
        base = dt.datetime(hoy.year, 1, 1)
        d = dparser.parse(t, default=base, dayfirst=dia_primero, fuzzy=True).date()
    except (ValueError, OverflowError):
        return None
    if not tiene_anio:
        return _anio_cercano(d.month, d.day, hoy)
    return d


def _anio_cercano(mes: int, dia: int, hoy: dt.date) -> dt.date | None:
    opciones = []
    for y in (hoy.year - 1, hoy.year, hoy.year + 1):
        try:
            opciones.append(dt.date(y, mes, dia))
        except ValueError:
            pass
    if not opciones:
        return None
    return min(opciones, key=lambda d: abs((d - hoy).days))


def restar_meses(d: dt.date, meses: int) -> dt.date:
    y, m = d.year, d.month - meses
    while m <= 0:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    dia = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return dt.date(y, m, dia)
