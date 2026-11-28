"""Informe:  python -m scraper.informe  →  docs/informe.md

Todo sale de los datos (discos, descartados, estado de fuentes, mapeo de
etiquetas). Si una comparación no se puede hacer, el informe lo dice."""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
from collections import Counter, defaultdict

from .clasificar import Taxonomia
from .util import normalizar, similitud
from .config import cargar_config, cargar_yaml, ruta
from .util import normalizar

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
ESTADOS = {"ok": "✅ funciona", "vacia": "⚠️ sin discos", "bloqueada": "❌ bloqueo / verificación anti-bots",
           "prohibida": "❌ robots.txt no lo permite", "error": "❌ error de conexión"}


def pct(a, b):
    return f"{(100 * a / b):.0f} %" if b else "—"


def _leer(p, defecto):
    if not os.path.exists(p):
        return defecto
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    config = cargar_config()
    R = config["rutas"]
    tax = Taxonomia(cargar_yaml(R["taxonomia"]))
    fuentes = {f["id"]: f for f in cargar_yaml(R["fuentes"])["fuentes"]}
    discos = _leer(ruta(R["discos"]), [])
    descartados = _leer(ruta(R["descartados"]), [])
    estado = _leer(ruta(R["estado_fuentes"]), {})
    mapeo = []
    if os.path.exists(ruta(R["mapeo_etiquetas"])):
        with open(ruta(R["mapeo_etiquetas"]), encoding="utf-8", newline="") as f:
            mapeo = list(csv.DictReader(f))
    hoy = estado.get("fecha") or dt.date.today().isoformat()
    ventana = estado.get("ventana", ["?", "?"])
    L = []
    w = L.append
    publicados = [d for d in discos if d["fecha"] <= hoy]
    prox = [d for d in discos if d["fecha"] > hoy]
    n = len(discos)
    fam_cuenta = Counter(f for d in discos for f in d["familias"])
    con_sub = sum(1 for d in discos if d["subgeneros"])
    en_bc = sum(1 for d in discos if d.get("en_bandcamp"))
    una = [d for d in discos if len({x["id"] for x in d["fuentes"]}) == 1]
    con_res = [d for d in discos if d["resenas"]]

    w(f"# Informe de novedades · {hoy}\n")
    w(f"Ventana: del **{ventana[0]}** (5 meses atrás) al **{ventana[1]}** (anunciados). "
      f"Generado automáticamente por `scraper/informe.py`.\n")
    w("## Resumen\n")
    w(f"| | |\n|---|---|")
    w(f"| Discos en la web | **{n}** ({len(publicados)} publicados · {len(prox)} próximamente) |")
    for fk, fd in cargar_yaml(R["taxonomia"])["familias"].items():
        w(f"| {fd['nombre']} | {fam_cuenta.get(fk, 0)} |")
    w(f"| Con subgénero | {con_sub} ({pct(con_sub, n)}) |")
    w(f"| En Bandcamp | {en_bc} ({pct(en_bc, n)}) |")
    w(f"| Aparecen en una sola fuente | {len(una)} ({pct(len(una), n)}) |")
    w(f"| Con al menos una reseña | {len(con_res)} ({pct(len(con_res), n)}) |")
    w(f"| Descartados | {len(descartados)} (EP, reediciones, otro idioma, fuera de fecha, otros géneros…) |\n")
    w("> «En Bandcamp» = MusicBrainz enlaza el disco o el artista a Bandcamp, o se ha encontrado la "
      "página del disco. La búsqueda de Bandcamp está prohibida a robots y no se usa.\n")

    # ------------------------------------------------ comparación con el mercado
    w("## ¿Mejor que el mercado?\n")
    w("### Frente a Album of the Year\n")
    aoty = estado.get("hosts_bloqueados", {}).get("albumoftheyear.org")
    w("**No se puede hacer.** Album of the Year responde a cualquier lector automático con la verificación "
      "anti-bots de Cloudflare (\"Just a moment…\") en todas sus páginas, también en las de género y el RSS. "
      "No se ha intentado saltar. Por tanto **no puedo afirmar que esta web sea mejor que AOTY**." +
      (f" (Último intento: {aoty}.)" if aoty else "") + "\n")
    w("### Frente a cada fuente de prensa por separado\n")
    w("Cuántos discos de la web aparecen en cada fuente, por mes de salida. «Web» es la unión de todas "
      "tras filtrar EP, reediciones, idioma y género, así que **siempre es ≥ que cualquier fuente sola**: "
      "lo relevante es cuánto añade sobre la mejor.\n")
    meses = sorted({d["fecha"][:7] for d in publicados})[-6:]
    for fk, fd in cargar_yaml(R["taxonomia"])["familias"].items():
        ds = [d for d in publicados if fk in d["familias"]]
        por_fuente = defaultdict(Counter)
        for d in ds:
            for x in {x["id"] for x in d["fuentes"]}:
                por_fuente[x][d["fecha"][:7]] += 1
        top = sorted(por_fuente, key=lambda k: -sum(por_fuente[k].values()))[:4]
        w(f"**{fd['nombre']}**\n")
        w("| Mes | Web | " + " | ".join(fuentes.get(t, {}).get("nombre", t).split(" –")[0] for t in top) + " | Mejor fuente sola |")
        w("|---|---:|" + "---:|" * len(top) + "---:|")
        for m in meses:
            total = sum(1 for d in ds if d["fecha"][:7] == m)
            vals = [por_fuente[t][m] for t in top]
            mejor = max([por_fuente[t][m] for t in por_fuente] or [0])
            w(f"| {MESES[int(m[5:]) - 1]} {m[:4]} | **{total}** | " + " | ".join(str(v) for v in vals) +
              f" | {mejor} ({pct(mejor, total)}) |")
        w("")
    w("### ¿Los encuentra antes?\n")
    resenados = [d for d in discos if d["resenas"]]
    previos = [d for d in resenados if any(fuentes.get(x["id"], {}).get("rol") in ("listado", "sello", "noticia")
                                          for x in d["fuentes"])]
    sin_resena = [d for d in publicados if not d["resenas"]]
    w(f"- **{len(prox)} discos anunciados** que todavía no han salido ya están en la web; "
      f"{sum(1 for d in prox if d['resenas'])} de ellos tienen ya alguna reseña.")
    w(f"- De los {len(resenados)} discos reseñados por la prensa, **{len(previos)} ({pct(len(previos), len(resenados))})** "
      f"también estaban en listados, anuncios o sellos, es decir, se encuentran sin esperar a la reseña.")
    w(f"- {len(sin_resena)} discos publicados ({pct(len(sin_resena), len(publicados))}) no tienen ninguna reseña "
      f"en las fuentes leídas: son los que un lector de prensa no vería.")
    w("- **Limitación honesta:** en esta primera carga no sé *cuándo* anunció cada web cada disco, solo que lo "
      "anunció. Cada disco guarda la fecha en que el robot lo vio por primera vez (`detectado`); a partir de las "
      "ejecuciones semanales el informe podrá medir los días de antelación reales.\n")
    w("### ¿Asigna bien el subgénero?\n")
    acuerdo, total_h, desacuerdos = 0, 0, []
    for d in discos:
        pistas = set()
        for e in d.get("etiquetas_originales", []):
            for s in tax.alias.get(normalizar(e), set()):
                pistas.add(s)
        if not pistas:
            continue
        total_h += 1
        if pistas & set(d["subgeneros"]):
            acuerdo += 1
        else:
            desacuerdos.append(d)
    w(f"No hay una referencia independiente fiable (AOTY no es legible). Como control, en los {total_h} discos en "
      f"los que la prensa da un género reconocible, el subgénero asignado lo incluye en **{pct(acuerdo, total_h)}** "
      f"de los casos. Discos sin subgénero: **{n - con_sub}** ({pct(n - con_sub, n)}).\n")
    if desacuerdos:
        w("Ejemplos de desacuerdo para revisar:\n")
        for d in desacuerdos[:10]:
            w(f"- {d['artista']} – *{d['titulo']}*: prensa «{', '.join(d['etiquetas_originales'][:3])}» → "
              f"asignado {', '.join(d['subgeneros']) or 'ninguno'}")
        w("")

    # ------------------------------------------------ por familia y subgénero
    # ------------------------------------------------ calidad de los datos
    w("## Calidad de los datos\n")
    w("### Cobertura de cada campo\n")
    campos = [("Portada", lambda d: d.get("portada") or (d.get("deezer") or {}).get("portada")),
              ("Sello", lambda d: d.get("sello")), ("Número de pistas", lambda d: d.get("pistas")),
              ("Fecha exacta (día)", lambda d: d.get("fecha_exacta")), ("Idioma verificado", lambda d: d.get("idioma")),
              ("Identificado en MusicBrainz", lambda d: d.get("mbid")),
              ("Enlace para escuchar (Deezer, Bandcamp, Apple…)", lambda d: (d.get("deezer") or {}).get("url") or d.get("en_bandcamp")
               or any(k in (d.get("enlaces") or {}) for k in ("bandcamp", "spotify", "apple", "deezer", "tidal", "qobuz", "youtube"))),
              ("Subgénero", lambda d: d.get("subgeneros")), ("Al menos una reseña", lambda d: d.get("resenas"))]
    w("| Campo | Discos | % |\n|---|---:|---:|")
    for nombre, f in campos:
        k = sum(1 for d in discos if f(d))
        w(f"| {nombre} | {k} | {pct(k, n)} |")
    w("")
    # coherencia: un disco de una fuente especializada (no mixta) debería tener algún subgénero de esa familia
    w("### Coherencia de la clasificación con fuentes especializadas\n")
    coh, tot_coh, malos = 0, 0, []
    for d in discos:
        fams_fuente = {fuentes[x["id"]].get("familia") for x in d["fuentes"] if x["id"] in fuentes
                       and not fuentes[x["id"]].get("mixta")} - {None, "todas", "ninguna"}
        if not fams_fuente or not d["subgeneros"]:
            continue
        fams_subs = {f for s_ in d["subgeneros"] if s_ in tax.sub for f in tax.sub[s_]["familias"]}
        tot_coh += 1
        if fams_fuente & fams_subs:
            coh += 1
        else:
            malos.append((d, fams_fuente))
    w(f"De los **{tot_coh}** discos con subgénero que vienen de una fuente especializada en una familia, "
      f"**{pct(coh, tot_coh)}** tienen al menos un subgénero de esa familia. Los demás pueden ser discos "
      f"fuera de su género habitual o errores de clasificación:\n")
    for d, ff in malos[:12]:
        w(f"- {d['artista']} – *{d['titulo']}*: fuente de {', '.join(sorted(ff))}, subgéneros {', '.join(d['subgeneros'])}")
    w("")
    # posibles duplicados no unidos
    w("### Posibles duplicados para revisar\n")
    por_artista = defaultdict(list)
    for d in discos:
        por_artista[normalizar(d["artista"])].append(d)
    dudosos = []
    for lista in por_artista.values():
        for i, a in enumerate(lista):
            for b in lista[i + 1:]:
                sim = similitud(a["titulo"], b["titulo"])
                if 0.75 <= sim < 1.0 or normalizar(a["titulo"]) in normalizar(b["titulo"]) or normalizar(b["titulo"]) in normalizar(a["titulo"]):
                    dudosos.append((sim, a, b))
    dudosos.sort(key=lambda x: -x[0])
    w(f"Parejas del mismo artista con títulos muy parecidos que **no** se han unido: **{len(dudosos)}** "
      f"(sobre {n} discos). Pueden ser el mismo disco escrito de dos formas o discos distintos (p. ej. un "
      f"directo y el de estudio):\n")
    for sim, a, b in dudosos[:15]:
        w(f"- {a['artista']}: *{a['titulo']}* ({a['fecha']}) · *{b['titulo']}* ({b['fecha']}) — similitud {sim:.2f}")
    w("")
    # revisión de una muestra (si existe data/revision_clasificacion.csv)
    p_rev = ruta("data/revision_clasificacion.csv")
    if os.path.exists(p_rev):
        with open(p_rev, encoding="utf-8", newline="") as f:
            rev = list(csv.DictReader(f))
        c = Counter(r.get("resultado") for r in rev)
        juzgados = c["correcto"] + c["parcial"] + c["incorrecto"]
        w("### Aciertos medidos en una muestra revisada\n")
        w(f"Muestra al azar de **{len(rev)}** discos revisados uno a uno (`data/revision_clasificacion.csv`), "
          "según lo que se sabe de cada artista y el género que da la propia reseña.\n")
        w(f"- De los **{juzgados}** con subgénero que se pueden juzgar: correctos **{pct(c['correcto'], juzgados)}**, "
          f"parcialmente correctos (algún subgénero de más) {pct(c['parcial'], juzgados)}, incorrectos {pct(c['incorrecto'], juzgados)}.")
        w(f"- Sin subgénero (pero en su familia): {c['sin_subgenero']} · sin datos suficientes para juzgar: {c['no_verificable']}.")
        if c["fuera_bien"] or c["fuera_mal"]:
            w(f"- Apartados al revisar las reglas: {c['fuera_bien'] + c['fuera_mal']} "
              f"({c['fuera_bien']} con razón, {c['fuera_mal']} probablemente por error).")
        errores = [r for r in rev if r.get("resultado") in ("incorrecto", "fuera_mal", "parcial") and r.get("nota")]
        if errores:
            w("\nErrores y su causa:\n")
            for r in errores:
                w(f"- {r['artista']} – *{r['titulo']}* ({r['resultado'].replace('_', ' ')}): {r['nota']}")
        w("")

    w("## Discos por familia y subgénero\n")
    datos_tax = cargar_yaml(R["taxonomia"])
    cuenta = Counter(s for d in discos for s in d["subgeneros"])
    for fk, fd in datos_tax["familias"].items():
        w(f"### {fd['nombre']} · {fam_cuenta.get(fk, 0)} discos\n")
        w("| Grupo | Subgénero | Discos |\n|---|---|---:|")
        for g, subs in fd["grupos"].items():
            for sid, sd in subs.items():
                w(f"| {g} | {sd.get('nombre', sid)}{' *(frontera)*' if sd.get('frontera') else ''} | {cuenta.get(sid, 0)} |")
        sin = sum(1 for d in discos if fk in d["familias"] and not d["subgeneros"])
        w(f"| — | *sin subgénero* | {sin} |\n")

    # ------------------------------------------------ fuentes
    w("## Fuentes\n")
    aporta = Counter(x["id"] for d in discos for x in {x["id"]: x for x in d["fuentes"]}.values())
    exclusivos = Counter(next(iter({x["id"] for x in d["fuentes"]})) for d in una)
    w("| Fuente | Estado | Discos en la web | Solo en esta fuente |\n|---|---|---:|---:|")
    for fid, info in estado.get("fuentes", {}).items():
        est = ESTADOS.get(info["estado"], info["estado"])
        if info["estado"] == "ok" and fuentes.get(fid, {}).get("rol") == "sonda":
            est = "✅ responde"
        w(f"| {info['nombre']} | {est} | {aporta.get(fid, 0)} | {exclusivos.get(fid, 0)} |")
    mb = estado.get("musicbrainz", {})
    bc = estado.get("bandcamp", {})
    w(f"\nMusicBrainz: {mb.get('consultas', 0)} consultas"
      f"{' · BLOQUEADO: ' + mb['bloqueado'] if mb.get('bloqueado') else ''}. "
      f"Bandcamp: {bc.get('paginas', 0)} páginas{' · BLOQUEADO: ' + bc['bloqueado'] if bc.get('bloqueado') else ''}. "
      f"Peticiones totales: {estado.get('peticiones', 0)}.\n")
    if estado.get("hosts_bloqueados"):
        w("Webs que respondieron con bloqueo o verificación anti-bots en esta ejecución:\n")
        for h, m in estado["hosts_bloqueados"].items():
            w(f"- {m}")
        w("")

    # ------------------------------------------------ descartes
    w("## Descartes\n")
    motivos = Counter(d["motivo"].split(":")[0].split(" (")[0] for d in descartados)
    w("| Motivo | Discos |\n|---|---:|")
    for m, c in motivos.most_common():
        w(f"| {m} | {c} |")
    w("\nLista completa en `data/descartados.json`.\n")

    # ------------------------------------------------ etiquetas y propuestas
    w("## Etiquetas sin encajar y subgéneros propuestos\n")
    pend = [r for r in mapeo if r["subgenero"] == "pendiente"]
    w(f"- Etiquetas en `data/mapeo_etiquetas.csv`: {len(mapeo)} · resueltas por el LLM: "
      f"{sum(1 for r in mapeo if r.get('origen') == 'llm')} · **pendientes: {len(pend)}**.")
    if pend:
        w("- Las pendientes no tienen todavía respuesta del LLM (la Action semanal no tiene clave de API); "
          "se resuelven una sola vez en una sesión de Claude Code. Las más frecuentes:")
        for r in sorted(pend, key=lambda r: -int(r.get("veces") or 0))[:15]:
            w(f"  - «{r['etiqueta']}» ({r.get('veces')} veces; p. ej. {r.get('ejemplo')})")
    props = [r for r in mapeo if (r.get("nota") or "").lower().startswith("propuesta")]
    if props:
        w("\n**Subgéneros nuevos propuestos** (no se han creado; decide tú si se añaden a la taxonomía):\n")
        agrup = defaultdict(list)
        for r in props:
            agrup[r["nota"].split(":", 1)[-1].strip()].append(r)
        for nombre, rs in sorted(agrup.items(), key=lambda kv: -sum(int(r.get("veces") or 0) for r in kv[1])):
            veces = sum(int(r.get("veces") or 0) for r in rs)
            w(f"- **{nombre}**: {veces} apariciones (etiquetas: {', '.join(r['etiqueta'] for r in rs[:6])})")
    w("")
    os.makedirs(ruta("docs"), exist_ok=True)
    with open(ruta("docs/informe.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("docs/informe.md escrito")


if __name__ == "__main__":
    main()
