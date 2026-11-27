"""Mapeo automático de etiquetas:  python -m scraper.mapear [--max=N] [--sin-llm]

Primero, si hay clave de la API de Anthropic, un LLM (scraper.llm) resuelve las pendientes.
Después, para cada etiqueta que siga "pendiente" en data/mapeo_etiquetas.csv (o todas, sin clave):
  1. busca en Wikidata un elemento que sea un género musical con ese nombre;
  2. sube por "subclase de" (P279) hasta 3 niveles;
  3. el primer antepasado cuyo nombre o alias sea un alias de data/taxonomia.yaml da el
     subgénero (p. ej. "nordicana" → americana; "blackgaze" → black metal / shoegaze).
Si es un género pero no llega a nada de la taxonomía queda "ninguno" (con la cadena en la
nota, para que se pueda proponer como subgénero). Si no es un género (ciudades, personas,
sellos…) queda "ninguno". Si Wikidata no responde, la etiqueta sigue "pendiente".
Nunca se crean subgéneros: solo se apunta a los que ya existen."""
from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.parse

from .clasificar import Taxonomia, cargar_mapeo, guardar_mapeo
from .config import RAIZ, cargar_config, cargar_yaml, ruta
from .http import Bloqueado, Navegador
from .llm import MapeadorLLM
from .util import normalizar

API = "https://www.wikidata.org/w/api.php?format=json&"
GENERO_MUSICAL = {"Q188451", "Q105540327"}     # "género musical" y "género de música popular"
PROFUNDIDAD = 3


class Wikidata:
    def __init__(self, nav):
        self.nav = nav
        self.entidades: dict[str, dict] = {}

    def _json(self, params: dict) -> dict | None:
        try:
            r = self.nav.get(API + urllib.parse.urlencode(params), acepta="application/json")
        except (Bloqueado, ConnectionError):
            return None
        if r.estado != 200:
            return None
        try:
            return json.loads(r.texto)
        except ValueError:
            return None

    def buscar(self, texto: str) -> list[dict] | None:
        d = self._json({"action": "wbsearchentities", "search": texto, "language": "en", "type": "item", "limit": 7})
        return None if d is None else d.get("search", [])

    def entidades_de(self, ids: list[str]) -> bool:
        faltan = [i for i in ids if i not in self.entidades]
        for k in range(0, len(faltan), 50):
            d = self._json({"action": "wbgetentities", "ids": "|".join(faltan[k:k + 50]),
                            "props": "labels|aliases|claims|descriptions", "languages": "en"})
            if d is None:
                return False
            self.entidades.update(d.get("entities", {}))
        return True


def _ids(entidad: dict, prop: str) -> list[str]:
    out = []
    for c in entidad.get("claims", {}).get(prop, []):
        v = (((c.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {})
        if isinstance(v, dict) and v.get("id"):
            out.append(v["id"])
    return out


def _nombres(entidad: dict) -> list[str]:
    nombres = [(entidad.get("labels", {}).get("en") or {}).get("value", "")]
    nombres += [a.get("value", "") for a in entidad.get("aliases", {}).get("en", [])]
    return [n for n in nombres if n]


def es_genero(entidad: dict) -> bool:
    if set(_ids(entidad, "P31")) & GENERO_MUSICAL:
        return True
    desc = (entidad.get("descriptions", {}).get("en") or {}).get("value", "").lower()
    return "genre" in desc and ("music" in desc or "rock" in desc or "metal" in desc or "folk" in desc)


def subgeneros_de(entidad: dict, tax: Taxonomia) -> set[str]:
    subs = set()
    for n in _nombres(entidad):
        subs |= tax.alias.get(normalizar(n), set())
    return subs


def resolver(etiqueta: str, wd: Wikidata, tax: Taxonomia) -> tuple[str, str] | None:
    """(subgéneros separados por '|' o 'ninguno', nota) — None si Wikidata no responde."""
    cand = wd.buscar(etiqueta)
    if cand is None:
        return None
    n_et = normalizar(etiqueta)
    # solo elementos cuyo nombre o alias coincide con la etiqueta (evita "Heart" el grupo, etc.)
    ids = [c["id"] for c in cand if normalizar(c.get("label", "")) == n_et
           or any(normalizar(a) == n_et for a in c.get("aliases", []) or [])
           or normalizar((c.get("match") or {}).get("text", "")) == n_et]
    if not ids:
        return "ninguno", "automático: Wikidata no tiene un elemento con ese nombre"
    if not wd.entidades_de(ids):
        return None
    generos = [wd.entidades[i] for i in ids if i in wd.entidades and es_genero(wd.entidades[i])]
    if not generos:
        return "ninguno", "automático: en Wikidata no es un género musical (lugar, persona, sello, tema…)"
    g = generos[0]
    nombre_g = _nombres(g)[0] if _nombres(g) else g.get("id", "")
    nivel, vistos, camino = [g], {g.get("id")}, {g.get("id"): nombre_g}
    for _ in range(PROFUNDIDAD + 1):
        encontrados: set[str] = set()
        via = []
        for e in nivel:
            s = subgeneros_de(e, tax)
            if s:
                encontrados |= s
                via.append(camino.get(e.get("id"), ""))
        if encontrados:
            return "|".join(sorted(encontrados)), f"automático (Wikidata {g.get('id')}): {nombre_g} → {', '.join(via)}"
        padres = [p for e in nivel for p in _ids(e, "P279") if p not in vistos]
        if not padres:
            break
        if not wd.entidades_de(padres):
            return None
        siguiente = []
        for p in padres:
            vistos.add(p)
            if p in wd.entidades:
                siguiente.append(wd.entidades[p])
                camino[p] = (_nombres(wd.entidades[p]) or [p])[0]
        nivel = siguiente
    cadena = " → ".join(list(camino.values())[:5])
    return "ninguno", f"automático: género fuera de la taxonomía (Wikidata {g.get('id')}: {cadena})"


def main(args: list[str] | None = None) -> int:
    args = sys.argv[1:] if args is None else args
    config = cargar_config()
    maximo = int(next((a.split("=", 1)[1] for a in args if a.startswith("--max=")), 400))
    tax = Taxonomia(cargar_yaml(config["rutas"]["taxonomia"]))
    p = ruta(config["rutas"]["mapeo_etiquetas"])
    mapeo = cargar_mapeo(p)
    pend = sorted((k for k, v in mapeo.items() if v["subgenero"] == "pendiente"),
                  key=lambda k: -int(mapeo[k].get("veces") or 0))[:maximo]
    hoy = dt.date.today().isoformat()
    # 1) LLM (Claude), solo si hay clave: entiende jerga y variantes que Wikidata no tiene
    cfg_llm = (config.get("enriquecimiento") or {}).get("llm") or {}
    if MapeadorLLM.disponible(cfg_llm) and "--sin-llm" not in args:
        llm = MapeadorLLM(cfg_llm, tax, cargar_yaml(config["rutas"]["taxonomia"]))
        maximo_llm = int(cfg_llm.get("max_etiquetas_por_ejecucion", 600))
        por_etiqueta = {mapeo[k]["etiqueta"]: k for k in pend[:maximo_llm]}
        respuestas = llm.mapear(list(por_etiqueta))
        for et, (sub, nota) in respuestas.items():
            mapeo[por_etiqueta[et]].update({"subgenero": sub, "origen": "llm", "fecha": hoy,
                                            "nota": (nota + " · " if nota else "") + f"automático ({llm.modelo})"})
        guardar_mapeo(p, mapeo)
        print(f"LLM ({llm.modelo}): {len(respuestas)} etiquetas · {llm.uso}" + (f" · error: {llm.error}" if llm.error else ""))
        pend = [k for k in pend if mapeo[k]["subgenero"] == "pendiente"]
    else:
        print("LLM: sin clave configurada; se usa solo Wikidata")
    # 2) Wikidata para lo que quede
    wd = Wikidata(Navegador(config, RAIZ))
    hechas = sin_respuesta = con_sub = 0
    for k in pend:
        r = resolver(mapeo[k]["etiqueta"], wd, tax)
        if r is None:
            sin_respuesta += 1
            if sin_respuesta >= 5 and hechas == 0:
                break                 # Wikidata no responde: se deja para la próxima vez
            continue
        sub, nota = r
        mapeo[k].update({"subgenero": sub, "origen": "wikidata", "fecha": hoy, "nota": nota})
        hechas += 1
        con_sub += sub != "ninguno"
        if hechas % 50 == 0:
            guardar_mapeo(p, mapeo)
            print(f"  {hechas}/{len(pend)} etiquetas", flush=True)
    guardar_mapeo(p, mapeo)
    quedan = sum(1 for v in mapeo.values() if v["subgenero"] == "pendiente")
    print(f"Etiquetas resueltas: {hechas} ({con_sub} a un subgénero) · sin respuesta: {sin_respuesta} · pendientes: {quedan}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
