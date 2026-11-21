"""Convierte HTML en texto por líneas con marcas opcionales, para que las
reglas de data/fuentes.yaml puedan ser simples expresiones regulares.

Marcas:  «…» para lo que se configure (p. ej. cursivas = títulos),
         ⟦url⟧ antes del texto de un enlace, ⟪src⟫ en lugar de una imagen,
         " | " entre celdas de una tabla.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString

BLOQUES = ["p", "div", "li", "ul", "ol", "tr", "table", "tbody", "thead", "h1", "h2", "h3", "h4", "h5", "h6",
           "section", "article", "header", "footer", "blockquote", "figure", "figcaption", "dd", "dt", "hr"]


def html_a_texto(html: str, base_url: str = "", selector: str | None = None, marcas: dict | None = None,
                 enlaces: bool = False, imagenes: bool = False, desde: str | None = None,
                 hasta: str | None = None, quitar: str | None = None) -> str:
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "noscript", "svg", "template"]):
        t.decompose()
    raiz = None
    if selector:
        encontrados = soup.select(selector)
        if encontrados:
            raiz = encontrados[0] if len(encontrados) == 1 else _envolver(soup, encontrados)
    if raiz is None:
        raiz = soup.body or soup
    if quitar:
        for el in raiz.select(quitar):
            el.decompose()
    for sel, par in (marcas or {}).items():
        a, b = (par[0], par[1]) if len(par) == 2 else (par, par)
        for el in raiz.select(sel):
            el.insert(0, NavigableString(a))
            el.append(NavigableString(b))
    if enlaces:
        for el in raiz.select("a[href]"):
            el.insert(0, NavigableString(f"⟦{urljoin(base_url, el['href'])}⟧"))
    if imagenes:
        for el in raiz.select("img"):
            src = el.get("src") or el.get("data-src") or ""
            el.replace_with(NavigableString(f"⟪{urljoin(base_url, src)}⟫") if src else NavigableString(""))
    for el in raiz.find_all("br"):
        el.replace_with(NavigableString("\n"))
    for el in raiz.find_all(["td", "th"]):
        el.append(NavigableString(" | "))
    for el in raiz.find_all(BLOQUES):
        el.insert_before(NavigableString("\n"))
        el.insert_after(NavigableString("\n"))
    texto = raiz.get_text("")
    texto = texto.replace("\xa0", " ").replace("​", "").replace("&nbsp;", " ")
    texto = texto.replace("—", "–").replace("&ndash;", "–")
    lineas = []
    for ln in texto.split("\n"):
        ln = re.sub(r"[ \t\r\f\v]+", " ", ln).strip()
        ln = re.sub(r"(\s*\|\s*)+$", "", ln)
        if ln and ln not in ("|", "« »", "«»"):
            lineas.append(ln)
    texto = "\n".join(lineas)
    texto = re.sub(r"«\s*»", " ", texto)
    if desde and desde in texto:
        texto = texto[texto.index(desde) + len(desde):]
    if hasta and hasta in texto:
        texto = texto[: texto.index(hasta)]
    return texto


def _envolver(soup, elementos):
    cont = soup.new_tag("div")
    for e in elementos:
        cont.append(e.extract())
    return cont
