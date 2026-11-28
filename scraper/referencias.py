"""¿Perdemos discos? python -m scraper.referencias

Lee las listas de novedades de referencias independientes (config → validacion.referencias; hoy
Metacritic), y para cada disco mira si está en la web, si lo vimos y lo descartamos (y por qué) o si no
lo vimos nunca. De los no vistos pregunta a MusicBrainz su género: si es de nuestras familias, es un disco
**perdido**; si no, está bien fuera. Escribe data/referencias.json, que lee scraper/validar.py."""
from __future__ import annotations

import datetime as dt
import json
import urllib.parse
import os
import re
from collections import Counter

from .clasificar import Taxonomia, cargar_mapeo
from .config import RAIZ, cargar_config, cargar_yaml, ruta
from .http import Bloqueado, Navegador, Prohibido, guardar_json
from .consolidar import motivo_no_nuevo
from .musicbrainz import MusicBrainz
from .util import normalizar, similitud


def buscar_artista(mb: MusicBrainz, nombre: str) -> str | None:
    """MBID del artista por su nombre (cuando el título del disco no basta para encontrarlo)."""
    k = f"artnom:{clave(nombre)}"
    if k in mb.cache:
        return mb.cache[k] or None
    d = mb._json("artist/?fmt=json&limit=5&query=" + urllib.parse.quote(f'artist:"{nombre}"'))
    if d is None:
        return None
    mejor = next((a["id"] for a in d.get("artists", []) if similitud(clave(a.get("name")), clave(nombre)) >= 0.9), "")
    mb.cache[k] = mejor
    return mejor or None


def clave(texto: str) -> str:
    """Igual para "THE ROLLING STONES" y "the-rolling-stones", "o\\i" y "oi"."""
    # "&" se quita antes de normalizar: Metacritic lo omite en sus direcciones ("echo-the-bunnymen")
    return re.sub(r"[^a-z0-9]", "", normalizar((texto or "").replace("-", " ").replace("&", " ")))


def leer_referencia(nav: Navegador, ref: dict) -> tuple[list[dict], str]:
    vistos, items = set(), []
    for n in range(1, int(ref.get("paginas", 1)) + 1):
        url = ref["url"] + (ref.get("pagina", "").format(n=n) if n > 1 else "")
        try:
            r = nav.get(url)
        except Bloqueado as e:
            return items, f"bloqueada: {e}"
        except Prohibido as e:
            return items, f"robots.txt no lo permite: {e}"
        if r.estado != 200:
            return items, f"HTTP {r.estado} en la página {n}"
        for m in re.finditer(ref["enlace"], r.texto):
            k = (clave(m.group("artista")), clave(m.group("titulo")))
            if k not in vistos:
                vistos.add(k)
                items.append({"artista": m.group("artista").replace("-", " "), "titulo": m.group("titulo").replace("-", " "),
                              "clave": list(k), "url": url})
    return items, "ok"


def main() -> int:
    config = cargar_config()
    refs = (config.get("validacion") or {}).get("referencias") or []
    nav = Navegador(config, RAIZ)
    tax = Taxonomia(cargar_yaml(config["rutas"]["taxonomia"]))
    mapeadas = {k for k, v in cargar_mapeo(ruta(config["rutas"]["mapeo_etiquetas"])).items() if v["subgenero"] not in ("pendiente", "", "ninguno")}
    mb = MusicBrainz(nav, ruta(config["rutas"]["cache_musicbrainz"]))

    def nuestra(e: str) -> bool:
        n = normalizar(e)
        return (n in tax.alias and not all(tax.sub[s]["frontera"] for s in tax.alias[n])) or n in tax.genericas or n in mapeadas

    def de_las_nuestras(generos: list[str]) -> bool:
        """Mira los géneros principales (los más votados), no cualquier etiqueta: el primero es nuestro,
        o lo son al menos la mitad de los cuatro primeros."""
        top = [g for g in dict.fromkeys(generos)][:4]
        return bool(top) and (nuestra(top[0]) or sum(map(nuestra, top)) * 2 >= len(top))

    discos = json.load(open(ruta(config["rutas"]["discos"]), encoding="utf-8"))
    descartados = json.load(open(ruta(config["rutas"]["descartados"]), encoding="utf-8"))
    en_web = {(clave(d["artista"]), clave(d["titulo"])): d["id"] for d in discos}
    descarte = {(clave(d["artista"]), clave(d["titulo"])): d["motivo"] for d in descartados}
    rx_reed = re.compile(config["reglas"]["reedicion"]) if config["reglas"].get("reedicion") else None
    cons = config.get("consolidacion") or {}
    rx_extra = re.compile(r"(?i)\b(box set|super deluxe|special edition|anniversary|live recordings|the encore)\b")
    salida = {"fecha": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "referencias": {}}
    for ref in refs:
        items, estado = leer_referencia(nav, ref)
        for it in items:
            k = tuple(it["clave"])
            if k in en_web:
                it["resultado"] = "en_web"
            elif (rx_reed and rx_reed.search(it["titulo"])) or rx_extra.search(it["titulo"]) \
                    or motivo_no_nuevo({"artista": it["artista"], "titulo": it["titulo"]}, cons):
                it["resultado"] = "no_es_nuevo"           # reedición, caja, edición especial: fuera por norma
            elif k in descarte:
                it["resultado"], it["motivo"] = "descartado", descarte[k]
            else:
                rg = mb.buscar(it["artista"], it["titulo"], completar=False)
                ids = (rg or {}).get("artistas_id", [])[:2] or [x for x in [buscar_artista(mb, it["artista"])] if x]
                etiquetas = [e for a in ids[:1] for e in (mb.artista(a).get("generos") or mb.artista(a).get("etiquetas") or [])]
                it["generos"] = etiquetas[:8]
                it["resultado"] = "perdido" if de_las_nuestras(etiquetas) else ("fuera_de_genero" if etiquetas else "sin_genero")
        mb.guardar()
        salida["referencias"][ref["id"]] = {"nombre": ref["nombre"], "estado": estado, "items": items,
                                            "resumen": dict(Counter(i["resultado"] for i in items))}
        print(f"{ref['nombre']}: {estado} · {len(items)} discos · {dict(Counter(i['resultado'] for i in items))}")
    guardar_json(ruta("data/referencias.json"), salida, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
