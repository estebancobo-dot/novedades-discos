"""Carga de la configuración (YAML) desde la raíz del repositorio."""
from __future__ import annotations

import os

import yaml

# Raíz del proyecto. NOVEDADES_RAIZ permite ejecutar todo sobre otra carpeta (p. ej. las pruebas
# de extremo a extremo, que montan una copia mínima con datos de ejemplo).
RAIZ = os.environ.get("NOVEDADES_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ruta(rel: str) -> str:
    return os.path.join(RAIZ, rel)


def cargar_yaml(rel: str):
    with open(ruta(rel), encoding="utf-8") as f:
        return yaml.safe_load(f)


def cargar_config() -> dict:
    return cargar_yaml("data/config.yaml")


def cargar_fuentes(config: dict) -> list[dict]:
    datos = cargar_yaml(config["rutas"]["fuentes"])
    from . import lectores
    lectores.MACROS.clear()
    lectores.MACROS.update({k: str(v) for k, v in (datos.get("macros") or {}).items()})
    fuentes = []
    for f in datos.get("fuentes", []):
        if f.get("activa", True):
            fuentes.append(f)
    return fuentes
