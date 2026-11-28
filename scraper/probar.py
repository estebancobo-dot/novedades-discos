"""Prueba una fuente sin guardar nada:  python -m scraper.probar ID [--texto]

Sirve para ajustar las reglas de data/fuentes.yaml: muestra los discos
reconocidos y, con --texto, el texto que ven las reglas."""
from __future__ import annotations

import datetime as dt
import sys

from .config import RAIZ, cargar_config, cargar_fuentes
from .html_texto import html_a_texto
from .http import Navegador
from .lectores import _urls, leer_fuente


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ver_texto = "--texto" in sys.argv
    config = cargar_config()
    fuentes = {f["id"]: f for f in cargar_fuentes(config)}
    nav = Navegador(config, RAIZ)
    hoy = dt.date.today()
    for fid in args or list(fuentes):
        cfg = dict(fuentes[fid])
        if cfg.get("paginacion"):
            cfg["paginacion"] = dict(cfg["paginacion"], hasta=int(_opt("--paginas", 2)))
        if cfg.get("detalle"):
            cfg["detalle"] = dict(cfg["detalle"], max=int(_opt("--detalles", 3)))
        if ver_texto and cfg["lector"] == "texto":
            r = nav.get(_urls(cfg)[0])
            print(html_a_texto(r.texto, r.url, **(cfg.get("texto") or {}))[:6000])
        res = leer_fuente(nav, cfg, hoy)
        print(f"== {fid}: {res.estado} {res.detalle} | páginas {res.paginas} | items {len(res.items)}")
        for it in res.items[: int(_opt("--n", 15))]:
            print(f"   {it.fecha} | {it.artista} – {it.titulo} | sello={it.sello} gen={it.genero} "
                  f"tipo={it.tipo} nota={it.nota} anio={it.anio} pistas={it.pistas} extra={(it.extra or '')[:40]}")


def _opt(nombre, defecto):
    for a in sys.argv:
        if a.startswith(nombre + "="):
            return a.split("=", 1)[1]
    return defecto


if __name__ == "__main__":
    main()
