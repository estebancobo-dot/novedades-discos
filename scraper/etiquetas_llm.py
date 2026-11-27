"""Etiquetas pendientes ↔ respuestas de un LLM que trabaja con archivos (Claude Code con el
plan Pro, en la Action o en una sesión). El LLM no toca el CSV: lee la lista y escribe un JSON
de respuestas; este módulo las valida contra la taxonomía y las aplica.

  python -m scraper.etiquetas_llm exportar [--max=N]     → data/etiquetas_pendientes.json
  python -m scraper.etiquetas_llm aplicar  [archivo]     ← data/respuestas_llm.json

Formato de respuestas: {"etiqueta": ["id-subgenero|otro-id" o "ninguno", "nota (opcional)"], ...}
Un id que no existe invalida esa respuesta (la etiqueta sigue pendiente). Nunca se crean subgéneros."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

from .clasificar import Taxonomia, cargar_mapeo, guardar_mapeo
from .config import cargar_config, cargar_yaml, ruta
from .http import guardar_json
from .util import normalizar

PENDIENTES = "data/etiquetas_pendientes.json"
RESPUESTAS = "data/respuestas_llm.json"


def exportar(mapeo: dict, maximo: int = 300) -> list[dict]:
    pend = sorted((v for v in mapeo.values() if v["subgenero"] == "pendiente"),
                  key=lambda v: (-int(v.get("veces") or 0), v["etiqueta"].lower()))
    return [{"etiqueta": v["etiqueta"], "veces": int(v.get("veces") or 0), "ejemplo": v.get("ejemplo", "")}
            for v in pend[:maximo]]


def aplicar(mapeo: dict, respuestas: dict, tax: Taxonomia, origen: str = "llm") -> tuple[int, list[str]]:
    """Aplica las respuestas válidas a etiquetas que siguen pendientes. → (aplicadas, rechazadas)"""
    hoy = dt.date.today().isoformat()
    aplicadas, rechazadas = 0, []
    for etiqueta, valor in respuestas.items():
        if isinstance(valor, str):
            valor = [valor, ""]
        if not isinstance(valor, (list, tuple)) or not valor:
            rechazadas.append(etiqueta)
            continue
        sub, nota = str(valor[0]).strip(), (str(valor[1]).strip() if len(valor) > 1 else "")
        ids = [s.strip() for s in sub.split("|") if s.strip()]
        if not ids or (ids != ["ninguno"] and any(s not in tax.sub for s in ids)):
            rechazadas.append(etiqueta)
            continue
        fila = mapeo.get(normalizar(etiqueta))
        if not fila or fila["subgenero"] != "pendiente":
            continue                                  # no estaba pendiente: no se toca lo ya decidido
        fila.update({"subgenero": "|".join(dict.fromkeys(ids[:3])), "origen": origen, "fecha": hoy, "nota": nota})
        aplicadas += 1
    return aplicadas, rechazadas


def main(args: list[str] | None = None) -> int:
    args = sys.argv[1:] if args is None else args
    config = cargar_config()
    p_mapeo = ruta(config["rutas"]["mapeo_etiquetas"])
    mapeo = cargar_mapeo(p_mapeo)
    if not args or args[0] not in ("exportar", "aplicar"):
        print(__doc__)
        return 2
    if args[0] == "exportar":
        maximo = int(next((a.split("=", 1)[1] for a in args if a.startswith("--max=")), 300))
        lista = exportar(mapeo, maximo)
        guardar_json(ruta(PENDIENTES), lista, ensure_ascii=False, indent=1)
        print(f"{len(lista)} etiquetas pendientes → {PENDIENTES}")
        return 0
    p = ruta(args[1] if len(args) > 1 and not args[1].startswith("--") else RESPUESTAS)
    if not os.path.exists(p):
        print(f"No hay respuestas en {p}: nada que aplicar.")
        return 0
    try:
        with open(p, encoding="utf-8") as f:
            respuestas = json.load(f)
    except ValueError as e:
        print(f"Respuestas con formato inválido ({e}): no se aplica nada.")
        return 1
    tax = Taxonomia(cargar_yaml(config["rutas"]["taxonomia"]))
    aplicadas, rechazadas = aplicar(mapeo, respuestas if isinstance(respuestas, dict) else {}, tax)
    guardar_mapeo(p_mapeo, mapeo)
    os.remove(p)
    if os.path.exists(ruta(PENDIENTES)):
        os.remove(ruta(PENDIENTES))
    print(f"Respuestas aplicadas: {aplicadas} · rechazadas (id inexistente o formato): {len(rechazadas)}"
          + (f" → {', '.join(rechazadas[:10])}" if rechazadas else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
