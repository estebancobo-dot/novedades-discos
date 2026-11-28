"""Importa a data/taxonomia.yaml las familias "en foco" de agenda-conciertos.

    python -m scraper.importar_taxonomia RUTA/agenda-conciertos/data

Usa su jerarquía de Discogs (taxonomia.json: género → estilos y sinónimos) y su
reparto en categorías (estilos_map.json: discogs_a_categoria). No toca las
familias que ya existen (Country/Americana/Folk y Hard rock/AOR, más detalladas):
si un estilo ya está en ellas, se marca con `tambien_en` para que el disco cuente
también en la familia nueva. Es un paso puntual; después se edita el YAML a mano."""
from __future__ import annotations

import json
import os
import re
import sys

import yaml

from .config import ruta
from .util import normalizar

FAMILIAS = {   # categoría de la agenda → (id, nombre)
    "rock y metal": ("rockmetal", "Rock y metal"),
    "punk y garage": ("punkgarage", "Punk y garage"),
    "pop e indie": ("indiepop", "Indie y pop-rock"),
    "blues": ("blues", "Blues"),
    "synth y dark wave": ("synthdark", "Synthwave y dark wave"),
    "cantautor": ("cantautores", "Cantautores"),
}


def _id(nombre: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalizar(nombre).replace("&", "and")).strip("-")


def main():
    origen = sys.argv[1]
    tax_ag = json.load(open(os.path.join(origen, "taxonomia.json"), encoding="utf-8"))
    mapa = json.load(open(os.path.join(origen, "estilos_map.json"), encoding="utf-8"))
    p = ruta("data/taxonomia.yaml")
    texto = open(p, encoding="utf-8").read()
    datos = yaml.safe_load(texto)
    existentes = {}                       # alias normalizado → id de subgénero ya existente
    for fk, fd in datos["familias"].items():
        for subs in fd["grupos"].values():
            for sid, sd in subs.items():
                for a in [sid.replace("-", " ")] + [str(x) for x in sd.get("alias", [])]:
                    existentes.setdefault(normalizar(a), sid)
    sinonimos = {}                        # estilo Discogs → variantes
    for var, estilo in tax_ag.get("sinonimos", {}).items():
        sinonimos.setdefault(estilo, set()).add(var)
    reparto = {k: v for k, v in mapa["discogs_a_categoria"].items() if not k.startswith("_")}
    asignado = {e: cat for cat, estilos in reparto.items() for e in estilos}
    por_familia = {fid: [] for fid, _ in FAMILIAS.values()}
    tambien = {}                          # id existente → familias nuevas donde también cuenta
    def anadir(fid, estilo):
        n = normalizar(estilo)
        if n in existentes:
            tambien.setdefault(existentes[n], set()).add(fid)
        else:
            por_familia[fid].append(estilo)
    for estilo in tax_ag["generos"].get("Rock", []):
        cat = asignado.get(estilo, "rock y metal")
        if cat in FAMILIAS:
            anadir(FAMILIAS[cat][0], estilo)
    for estilo in tax_ag["generos"].get("Blues", []) + reparto.get("blues", []):
        anadir("blues", estilo)
    for estilo in reparto.get("synth y dark wave", []):
        anadir("synthdark", estilo)
    for estilo in reparto.get("pop e indie", []):
        anadir("indiepop", estilo)
    tambien.setdefault("singer-songwriter", set()).add("cantautores")
    por_familia["cantautores"] = ["Cantautor"]
    sinonimos.setdefault("Cantautor", set()).update({"cantautora", "cancion de autor", "canción de autor"})

    lineas = ["", "  # ---- Importado de agenda-conciertos (familias en foco) con scraper/importar_taxonomia.py ----"]
    for cat, (fid, nombre) in FAMILIAS.items():
        if fid in datos["familias"]:
            continue
        lineas += [f"  {fid}:", f"    nombre: {nombre}", f"    nombre_corto: {nombre}", "    grupos:", f"      {nombre}:"]
        vistos = set()
        for estilo in sorted(dict.fromkeys(por_familia[fid]), key=str.lower):
            sid = _id(estilo)
            if sid in vistos:
                continue
            vistos.add(sid)
            alias = sorted({estilo.lower()} | {v for v in sinonimos.get(estilo, set())})
            lineas += [f"        {sid}:", f"          nombre: \"{estilo}\"",
                       "          alias: [" + ", ".join(json.dumps(a, ensure_ascii=False) for a in alias) + "]"]
    texto = texto.rstrip("\n")
    i = texto.index("\n# Etiquetas que no dicen nada de género")
    nuevo = texto[:i] + "\n".join(lineas) + "\n" + texto[i:] + "\n"
    # marcar los subgéneros existentes que también cuentan en una familia nueva
    for sid, fams in tambien.items():
        patron = re.compile(rf"(\n        {re.escape(sid)}:\n          nombre: [^\n]+\n)")
        m = patron.search(nuevo)
        if m and "tambien_en" not in nuevo[m.end():m.end() + 200].split("\n        ")[0]:
            nuevo = nuevo[:m.end()] + f"          tambien_en: [{', '.join(sorted(fams))}]\n" + nuevo[m.end():]
    open(p, "w", encoding="utf-8").write(nuevo)
    yaml.safe_load(open(p, encoding="utf-8"))
    print({fid: len(v) for fid, v in por_familia.items()}, "también_en:", {k: sorted(v) for k, v in tambien.items()})


if __name__ == "__main__":
    main()
