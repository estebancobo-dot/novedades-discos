"""Reseñas completas desde agregadores de crítica (hoy AnyDecentMusic): cada página de disco del agregador
lista todas sus reseñas con medio, nota, una frase y el enlace a la reseña original. Cómo leerla está en
data/config.yaml → enriquecimiento.resenas_agregadores (selectores), no en el código."""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .http import Bloqueado, Navegador, Prohibido
from .util import normalizar


def leer_agregador(nav: Navegador, url: str, cfg: dict) -> list[dict] | None:
    """→ [{medio, nota, frase, url}] o None si no se pudo leer (bloqueo, robots, error)."""
    try:
        r = nav.get(url)
    except (Bloqueado, Prohibido):
        return None
    if r.estado != 200:
        return None
    sopa = BeautifulSoup(r.texto, "lxml")
    out = []
    for li in sopa.select(cfg["item"]):
        medio = li.select_one(cfg["medio"])
        nota = li.select_one(cfg["nota"])
        parrafo = li.select_one(cfg["frase"])
        enlace = li.select_one(cfg["enlace"])
        href = enlace.get("href") if enlace else None          # antes de quitar los enlaces del párrafo
        if not medio:
            continue
        frase = ""
        if parrafo:
            for a in parrafo.select("a"):
                a.decompose()
            frase = re.sub(r"\s+", " ", parrafo.get_text(" ")).strip()
        try:
            valor = float(nota.get_text().strip()) if nota else None
        except ValueError:
            valor = None
        out.append({"medio": medio.get_text().strip(), "nota": f"{valor:g}/10" if valor is not None else None,
                    "frase": frase[: int(cfg.get("frase_max", 300))], "url": href})
    return out


def _medio(nombre: str) -> str:
    return normalizar(re.sub(r"\s*\(vía [^)]*\)\s*$", "", nombre or "").replace("the ", "", 1))


def fusionar_resenas(d: dict, resenas: list[dict], agregador: str) -> int:
    """Añade al disco las reseñas del agregador; si ya había una del mismo medio, la completa con la frase,
    la nota y el enlace original. → nº de reseñas nuevas."""
    actuales = d.setdefault("resenas", [])
    por_medio = {_medio(r.get("nombre")): r for r in actuales}
    nuevas = 0
    for x in resenas:
        r = por_medio.get(_medio(x["medio"]))
        if r:
            if x.get("frase") and not r.get("frase"):
                r["frase"] = x["frase"]
            if x.get("nota") and not r.get("nota"):
                r["nota"] = x["nota"]
            if x.get("url") and agregador in (r.get("url") or ""):
                r["url"] = x["url"]
            r["nombre"] = re.sub(r"\s*\(vía [^)]*\)\s*$", "", r["nombre"])
        else:
            actuales.append({"fuente": f"{agregador}:{normalizar(x['medio'])}", "nombre": x["medio"], "url": x.get("url"),
                             "nota": x.get("nota"), "frase": x.get("frase"), "fecha": None, "via": agregador})
            por_medio[_medio(x["medio"])] = actuales[-1]
            nuevas += 1
    return nuevas
