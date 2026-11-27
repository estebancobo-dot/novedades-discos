"""Prepara los datos de la web:  python -m scraper.web

Lee data/discos.json y data/taxonomia.yaml y escribe en site/:
  data/discos.json   lo que la web necesita (incluida la taxonomía: los filtros se
                     construyen solos al añadir familias o subgéneros)
  rss/*.xml          un RSS por familia y por subgénero (y uno con todo)
  cal/*.ics          calendario de "próximamente" por familia (para suscribirse)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import re
from email.utils import format_datetime
from xml.sax.saxutils import escape

from .config import cargar_config, cargar_yaml, ruta

URL_WEB = os.environ.get("URL_WEB", "")
# Campos que solo usa la ficha: van en site/data/fichas/AAAA-MM.json, no en el índice.
CAMPOS_FICHA = ("portada_grande", "pistas", "idioma", "deezer_id", "dicen", "resenas", "fuentes", "enlaces")     # p. ej. https://usuario.github.io/novedades-discos/


def _portadas(url: str | None, deezer: dict | None) -> tuple[str | None, str | None]:
    if not url and deezer and deezer.get("portada"):
        return deezer["portada"], deezer.get("portada_grande") or deezer["portada"]
    if not url:
        return None, None
    if "coverartarchive.org" in url:
        return url, url.replace("front-250", "front-500")
    m = re.match(r"(https://f\d\.bcbits\.com/img/[a-z]?\d+)_\d+\.(jpg|png)", url)
    if m:  # Bandcamp: _2 = 350 px, _16 = 700 px
        return f"{m.group(1)}_2.{m.group(2)}", f"{m.group(1)}_16.{m.group(2)}"
    return url, url


def nota_10(texto: str | None) -> float | None:
    """'7.5/10' → 7.5 · '4/5' → 8.0 · '85%' → 8.5 · '9' → None (sin escala)."""
    if not texto:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*/\s*(\d+)", texto)
    if m:
        v, escala = float(m.group(1).replace(",", ".")), float(m.group(2))
        return round(v * 10 / escala, 1) if escala in (5, 10, 100) and v <= escala else None
    m = re.search(r"(\d{1,3})\s*%", texto)
    return round(int(m.group(1)) / 10, 1) if m else None


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
    familias, nombres_sub, prestados = {}, {}, {}
    for fk, fd in tax["familias"].items():
        familias[fk] = {"nombre": fd["nombre"], "corto": fd.get("nombre_corto", fd["nombre"]), "grupos": [
            {"nombre": g, "subs": [{"id": sid, "nombre": sd.get("nombre", sid), "frontera": bool(sd.get("frontera")),
                                    "descripcion": sd.get("descripcion", ""), "familia": fk}
                                   for sid, sd in subs.items()]}
            for g, subs in fd["grupos"].items()]}
        for subs in fd["grupos"].values():
            for sid, sd in subs.items():
                nombres_sub[sid] = sd.get("nombre", sid)
                for otra in sd.get("tambien_en", []) or []:
                    prestados.setdefault(str(otra), []).append(
                        {"id": sid, "nombre": sd.get("nombre", sid), "frontera": False,
                         "descripcion": sd.get("descripcion", ""), "familia": fk})
    for fk, subs in prestados.items():     # subgéneros que también cuentan en otra familia
        if fk in familias:
            familias[fk]["grupos"].append({"nombre": "De otras familias", "subs": subs})
    p_listas = ruta(config["rutas"].get("listas_anuales", "data/listas_anuales.json"))
    listas = json.load(open(p_listas, encoding="utf-8")) if os.path.exists(p_listas) else {}
    reglas = (tax.get("reglas") or {})
    umbral_dest = float(reglas.get("destacado_nota", 8.0))
    salida = []
    for d in discos:
        peq, gra = _portadas(d.get("portada"), d.get("deezer"))
        notas = [n for n in (nota_10(r.get("nota")) for r in d.get("resenas", [])) if n is not None]
        media = round(sum(notas) / len(notas), 1) if notas else None
        destacado = bool((media is not None and media >= umbral_dest and len(notas) >= 1) or len(d.get("resenas", [])) >= 3)
        en_listas = d.get("listas_anuales", [])
        puntos = round((media or 0) + 1.5 * len(en_listas) + 0.3 * min(len(d.get("resenas", [])), 5)
                       + 0.2 * min(len({x["id"] for x in d.get("fuentes", [])}), 5) + (1 if destacado else 0), 2)
        salida.append({
            "id": d["id"], "artista": d["artista"], "titulo": d["titulo"],
            "fecha": d["fecha"], "fecha_exacta": d.get("fecha_exacta", True),
            "sello": d.get("sello"), "familias": d.get("familias", []), "subgeneros": d.get("subgeneros", []),
            "portada": peq, "portada_grande": gra,
            # si la portada principal no carga (p. ej. Cover Art Archive sin imagen), la de Deezer
            "portada_alt": dz_port if (dz_port := (d.get("deezer") or {}).get("portada")) and dz_port != peq else None,
            "pistas": d.get("pistas"), "tipo": d.get("tipo"),
            "idioma": d.get("idioma"), "nota": media, "n_notas": len(notas), "destacado": destacado,
            "puntos": puntos, "listas": en_listas,
            "deezer_id": (d.get("deezer") or {}).get("id"),
            "dicen": [t for t in d.get("descripciones", []) if len(t) > 30][:2],
            "resenas": [{"nombre": r["nombre"], "url": r.get("url"), "nota": r.get("nota"), "fecha": r.get("fecha")}
                        for r in d.get("resenas", [])],
            "fuentes": [{"nombre": x["nombre"], "url": x.get("url"), "fecha": x.get("fecha"), "rol": x.get("rol")}
                        for x in d.get("fuentes", [])],
            "enlaces": {k: v for k, v in (d.get("enlaces") or {}).items() if v},
        })
    base = ruta("site")
    os.makedirs(os.path.join(base, "data"), exist_ok=True)
    # "Lo mejor de cada año": con nuestros discos si el año tiene datos; si no, con las listas de fin de año
    mejores = {}
    anios_discos = {}
    for d in salida:
        anios_discos[d["fecha"][:4]] = anios_discos.get(d["fecha"][:4], 0) + 1
    for anio in sorted(set(anios_discos) | set(listas), reverse=True):
        if anios_discos.get(anio, 0) >= 20:
            mejores[anio] = {"tipo": "discos"}
        elif listas.get(anio):
            entradas = sorted(listas[anio].values(), key=lambda e: (-len(e["listas"]), e["artista"].lower()))
            mejores[anio] = {"tipo": "listas", "lista": entradas[:150]}
    # La web carga primero un índice ligero (lo que necesitan la cuadrícula, los filtros y el orden)
    # y los detalles de la ficha (enlaces, fuentes, reseñas…) por meses, solo al abrir un disco.
    indice, fichas = [], {}
    for d in salida:
        det = {k: d[k] for k in CAMPOS_FICHA if d.get(k) not in (None, [], {})}
        fichas.setdefault(d["fecha"][:7], {})[d["id"]] = det
        indice.append({**{k: v for k, v in d.items() if k not in CAMPOS_FICHA}, "n_resenas": len(d["resenas"])})
    dir_fichas = os.path.join(base, "data/fichas")
    if os.path.isdir(dir_fichas):
        shutil.rmtree(dir_fichas)
    os.makedirs(dir_fichas)
    for mes, dets in fichas.items():
        with open(os.path.join(dir_fichas, f"{mes}.json"), "w", encoding="utf-8") as f:
            json.dump(dets, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(base, "data/discos.json"), "w", encoding="utf-8") as f:
        json.dump({"actualizado": actualizado, "familias": familias, "mejores": mejores, "discos": indice}, f,
                  ensure_ascii=False, separators=(",", ":"))
    _rss(base, salida, familias, nombres_sub, actualizado)
    _ics(base, salida, familias, actualizado)
    print(f"site/data/discos.json: {len(salida)} discos · RSS y calendarios generados")


# ------------------------------------------------------------------ RSS
def _rss(base, discos, familias, nombres_sub, actualizado):
    os.makedirs(os.path.join(base, "rss"), exist_ok=True)
    grupos = {"todo": ("Todas las novedades", discos)}
    for fk, fd in familias.items():
        grupos[fk] = (fd["nombre"], [d for d in discos if fk in d["familias"]])
    for sid, nombre in nombres_sub.items():
        grupos[sid] = (nombre, [d for d in discos if sid in d["subgeneros"]])
    for clave, (titulo, lista) in grupos.items():
        items = []
        for d in sorted(lista, key=lambda x: x["fecha"], reverse=True)[:100]:
            enlace = f"{URL_WEB}#disco={d['id']}" if URL_WEB else d["enlaces"].get("musicbrainz", "")
            fecha = dt.datetime.fromisoformat(d["fecha"] + "T12:00:00+00:00")
            subs = ", ".join(nombres_sub.get(s, s) for s in d["subgeneros"])
            desc = f"{d['fecha']} · {d.get('sello') or ''} · {subs}"
            img = f'<img src="{escape(d["portada"])}" alt=""/><br/>' if d.get("portada") else ""
            items.append(f"<item><title>{escape(d['artista'])} – {escape(d['titulo'])}</title>"
                         f"<link>{escape(enlace)}</link><guid isPermaLink=\"false\">{escape(d['id'])}</guid>"
                         f"<pubDate>{format_datetime(fecha)}</pubDate>"
                         f"<description><![CDATA[{img}{escape(desc)}]]></description></item>")
        xml = ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
               f"<title>Novedades · {escape(titulo)}</title><link>{escape(URL_WEB)}</link>"
               f"<description>Álbumes nuevos: {escape(titulo)}</description><language>es</language>"
               f"<lastBuildDate>{format_datetime(dt.datetime.fromisoformat(actualizado + 'T06:00:00+00:00'))}</lastBuildDate>"
               + "".join(items) + "</channel></rss>")
        with open(os.path.join(base, "rss", f"{clave}.xml"), "w", encoding="utf-8") as f:
            f.write(xml)


# --------------------------------------------------------------- ICS
def _ics(base, discos, familias, actualizado):
    os.makedirs(os.path.join(base, "cal"), exist_ok=True)
    sello = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    grupos = {"todo": discos, **{fk: [d for d in discos if fk in d["familias"]] for fk in familias}}
    for clave, lista in grupos.items():
        lineas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//novedades-discos//ES", "CALSCALE:GREGORIAN",
                  f"X-WR-CALNAME:Próximos discos · {familias.get(clave, {}).get('nombre', 'todo')}"]
        for d in lista:
            if d["fecha"] < actualizado:
                continue
            dia = d["fecha"].replace("-", "")
            fin = (dt.date.fromisoformat(d["fecha"]) + dt.timedelta(days=1)).strftime("%Y%m%d")
            lineas += ["BEGIN:VEVENT", f"UID:{d['id']}@novedades-discos", f"DTSTAMP:{sello}",
                       f"DTSTART;VALUE=DATE:{dia}", f"DTEND;VALUE=DATE:{fin}",
                       "SUMMARY:" + _ics_txt(f"{d['artista']} – {d['titulo']}"),
                       "DESCRIPTION:" + _ics_txt(d.get("sello") or ""), "END:VEVENT"]
        lineas.append("END:VCALENDAR")
        with open(os.path.join(base, "cal", f"{clave}.ics"), "w", encoding="utf-8", newline="") as f:
            f.write("\r\n".join(lineas) + "\r\n")


def _ics_txt(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


if __name__ == "__main__":
    main()
