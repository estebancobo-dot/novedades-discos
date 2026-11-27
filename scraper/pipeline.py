"""Orquestador de fases, reanudable:  python -m scraper.pipeline [--incremental] [--nueva] [--git]

Ejecuta en orden recoger → enriquecer → clasificar → mapear → clasificar → informe → web.
Cada fase es un proceso aparte y su resultado queda en archivos (data/, docs/, site/), así
que si la ejecución se corta (reinicio de la máquina, límite de tiempo de la Action, error
de red), al relanzar este mismo comando se sigue por la primera fase que no terminó.

  --incremental  recogida semanal (solo relee las últimas semanas de cada fuente)
  --nueva        empieza de cero aunque haya una ejecución a medias
  --git          tras cada fase, guarda los cambios en git y los sube (para la Action)

El estado está en data/estado_pipeline.json."""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time

from .config import RAIZ, cargar_config, ruta
from .http import guardar_json

# (nombre, módulo, argumentos). "mapear" resuelve etiquetas nuevas sin LLM; después se
# vuelve a clasificar para aprovecharlas.
FASES = [
    ("recoger", "scraper.recoger", []),
    ("enriquecer", "scraper.enriquecer", []),
    ("clasificar", "scraper.clasificar", []),
    ("mapear", "scraper.mapear", []),
    ("clasificar_2", "scraper.clasificar", []),
    ("informe", "scraper.informe", []),
    ("web", "scraper.web", []),
]
CADUCIDAD_DIAS = 3          # una ejecución a medias más antigua no se reanuda: se empieza otra
GIT_RUTAS = ["data", "docs", "site/data", "site/rss", "site/cal"]


def ahora() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def cargar_estado(p: str) -> dict | None:
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError):
        return None


def ejecucion_vigente(estado: dict | None, modo: str, hoy: dt.datetime) -> bool:
    """¿Hay una ejecución a medias del mismo modo y reciente que se pueda continuar?"""
    if not estado or estado.get("modo") != modo or estado.get("terminada"):
        return False
    try:
        inicio = dt.datetime.fromisoformat(estado["inicio"])
    except (KeyError, ValueError):
        return False
    return hoy - inicio < dt.timedelta(days=CADUCIDAD_DIAS)


def nueva_ejecucion(modo: str) -> dict:
    return {"modo": modo, "inicio": ahora(), "terminada": False, "fases": {}}


def pendientes(estado: dict) -> list[tuple[str, str, list[str]]]:
    return [f for f in FASES if estado["fases"].get(f[0], {}).get("estado") != "hecha"]


def git_guardar(mensaje: str) -> None:
    """Guarda y sube los datos. Si el remoto tiene commits nuevos, los integra y reintenta."""
    subprocess.run(["git", "add", "-A", *GIT_RUTAS], cwd=RAIZ, check=False)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=RAIZ).returncode == 0:
        return
    subprocess.run(["git", "commit", "-q", "-m", mensaje], cwd=RAIZ, check=True)
    for intento in range(4):
        if subprocess.run(["git", "push", "-q"], cwd=RAIZ).returncode == 0:
            return
        subprocess.run(["git", "pull", "-q", "--no-rebase", "--no-edit"], cwd=RAIZ, check=False)
        time.sleep(2 ** (intento + 1))
    raise RuntimeError("no se pudo subir a git tras 4 intentos")


def main(args: list[str] | None = None) -> int:
    args = sys.argv[1:] if args is None else args
    modo = "incremental" if "--incremental" in args else "completa"
    config = cargar_config()
    p_estado = ruta(config["rutas"].get("estado_pipeline", "data/estado_pipeline.json"))
    estado = cargar_estado(p_estado)
    if "--nueva" in args or not ejecucion_vigente(estado, modo, dt.datetime.now(dt.timezone.utc)):
        estado = nueva_ejecucion(modo)
    else:
        hechas = [n for n, v in estado["fases"].items() if v.get("estado") == "hecha"]
        print(f"Se reanuda la ejecución del {estado['inicio']} (hechas: {', '.join(hechas) or 'ninguna'})", flush=True)
    guardar_json(p_estado, estado, ensure_ascii=False, indent=1)

    for nombre, modulo, extra in pendientes(estado):
        if not os.path.exists(os.path.join(RAIZ, *modulo.split(".")) + ".py"):
            estado["fases"][nombre] = {"estado": "hecha", "nota": "módulo no disponible", "fin": ahora()}
            continue
        argv = [sys.executable, "-u", "-m", modulo, *extra]
        if nombre == "recoger" and modo == "incremental":
            argv.append("--incremental")
        print(f"== {nombre} ({ahora()})", flush=True)
        estado["fases"][nombre] = {"estado": "en_curso", "inicio": ahora()}
        guardar_json(p_estado, estado, ensure_ascii=False, indent=1)
        t0 = time.time()
        r = subprocess.run(argv, cwd=RAIZ)
        fase = estado["fases"][nombre]
        fase.update({"fin": ahora(), "segundos": round(time.time() - t0)})
        if r.returncode != 0:
            fase["estado"] = "fallida"
            fase["codigo"] = r.returncode
            guardar_json(p_estado, estado, ensure_ascii=False, indent=1)
            print(f"!! La fase {nombre} ha fallado (código {r.returncode}). Al relanzar se seguirá desde aquí.", flush=True)
            return 1
        fase["estado"] = "hecha"
        guardar_json(p_estado, estado, ensure_ascii=False, indent=1)
        if "--git" in args:
            git_guardar(f"Datos ({modo}): fase {nombre}")
    estado["terminada"] = True
    estado["fin"] = ahora()
    guardar_json(p_estado, estado, ensure_ascii=False, indent=1)
    if "--git" in args:
        git_guardar(f"Datos ({modo}): ejecución terminada")
    print("== Terminado", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
