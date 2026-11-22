"""Prepara los datos de la web:  python -m scraper.web

Lee data/discos.json y data/taxonomia.yaml y escribe site/data/discos.json con
solo lo que la web necesita (incluida la taxonomía, para que los filtros se
construyan solos al añadir familias o subgéneros)."""
from __future__ import annotations

import datetime as dt
import json
import os
import re

from .config import cargar_config, cargar_yaml, ruta


def _portadas(url: str | None) -> tuple[str | None, str | None]:
    if not url:
        return None, None
    if "coverartarchive.org" in url:
        return url, url.replace("front-250", "front-500")
    m = re.match(r"(https://f\d\.bcbits\.com/img/[a-z]?\d+)_\d+\.(jpg|png)", url)
    if m:  # Bandcamp: _2 = 350 px, _16 = 700 px
        return f"{m.group(1)}_2.{m.group(2)}", f"{m.group(1)}_16.{m.group(2)}"
    return url, url


def main():
    config = cargar_config()
    tax = cargar_yaml(config["rutas"]["taxonomia"])
    with open(ruta(config["rutas"]["discos"]), encoding="utf-8") as f:
        discos = json.load(f)
    estado_p = ruta(config["rutas"]["estado_fuentes"])
    actualizado = dt.date.today().isoformat()
    if os.path.exists(estado_p):
        with open(estado_p, encoding="utf-8") as f:
            actualizado = json.load(f).get("fecha", actualizado)
    familias = {}
    for fk, fd in tax["familias"].items():
        familias[fk] = {"nombre": fd["nombre"], "corto": fd.get("nombre_corto", fd["nombre"]), "grupos": [
            {"nombre": g, "subs": [{"id": sid, "nombre": sd.get("nombre", sid), "frontera": bool(sd.get("frontera"))}
                                   for sid, sd in subs.items()]}
            for g, subs in fd["grupos"].items()]}
    salida = []
    for d in discos:
        peq, gra = _portadas(d.get("portada"))
        salida.append({
            "id": d["id"], "artista": d["artista"], "titulo": d["titulo"],
            "fecha": d["fecha"], "fecha_exacta": d.get("fecha_exacta", True),
            "sello": d.get("sello"), "familias": d.get("familias", []), "subgeneros": d.get("subgeneros", []),
            "portada": peq, "portada_grande": gra, "pistas": d.get("pistas"), "tipo": d.get("tipo"),
            "idioma": d.get("idioma"),
            "resenas": [{"nombre": r["nombre"], "url": r.get("url"), "nota": r.get("nota"), "fecha": r.get("fecha")}
                        for r in d.get("resenas", [])],
            "fuentes": [{"nombre": x["nombre"], "url": x.get("url"), "fecha": x.get("fecha"), "rol": x.get("rol")}
                        for x in d.get("fuentes", [])],
            "enlaces": d.get("enlaces", {}),
        })
    os.makedirs(ruta("site/data"), exist_ok=True)
    with open(ruta("site/data/discos.json"), "w", encoding="utf-8") as f:
        json.dump({"actualizado": actualizado, "familias": familias, "discos": salida}, f, ensure_ascii=False,
                  separators=(",", ":"))
    print(f"site/data/discos.json: {len(salida)} discos")


if __name__ == "__main__":
    main()
