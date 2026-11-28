"""Validación automática de todas las capas: python -m scraper.validar

Para cada requisito de data/requisitos.yaml ejecuta sus comprobaciones (funciones de este módulo, o
resultados de la prueba en navegador "web:NOMBRE" leídos de data/validacion_web.json) y escribe:
  - data/validacion.json: estado de cada comprobación, requisito y capa;
  - docs/validacion.md: el mismo resultado para leer (semáforo por capa, fallos y por qué);
  - data/historial_validacion.json: cifras de cada ejecución, para ver saltos semana a semana.
Estados: ok · aviso · fallo · sin_datos (no se puede medir todavía) · sin_comprobar (no hay comprobación).
Umbrales en data/config.yaml → validacion. Nada se revisa a mano: todo sale de los datos."""
from __future__ import annotations

import csv
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

import yaml

from .clasificar import Taxonomia, cargar_mapeo, etiquetas_de
from .config import RAIZ, cargar_config, cargar_yaml, ruta
from .consolidar import canon
from .http import guardar_json
from .util import normalizar

ORDEN = {"fallo": 0, "aviso": 1, "sin_datos": 2, "sin_comprobar": 3, "ok": 4}
ICONO = {"ok": "🟢", "aviso": "🟡", "fallo": "🔴", "sin_datos": "⚪", "sin_comprobar": "⚫"}
NOMBRE_ESTADO = {"ok": "cumple", "aviso": "aviso", "fallo": "no cumple", "sin_datos": "sin datos todavía",
                 "sin_comprobar": "sin comprobación automática"}
COMPROBACIONES = {}


def comprobacion(f):
    COMPROBACIONES[f.__name__] = f
    return f


def R(estado: str, valor=None, detalle: str = "", ejemplos: list | None = None) -> dict:
    return {"estado": estado, "valor": valor, "detalle": detalle, "ejemplos": (ejemplos or [])[:10]}


def _leer(rel, defecto=None):
    p = ruta(rel)
    if not os.path.exists(p):
        return defecto
    with open(p, encoding="utf-8") as f:
        return json.load(f) if p.endswith(".json") else f.read()


class Contexto:
    """Todo lo que miran las comprobaciones, cargado una vez."""

    def __init__(self):
        self.config = cargar_config()
        self.umb = self.config.get("validacion") or {}
        self.rutas = self.config["rutas"]
        self.tax_datos = cargar_yaml(self.rutas["taxonomia"])
        self.tax = Taxonomia(self.tax_datos)
        self.fuentes = {f["id"]: f for f in cargar_yaml(self.rutas["fuentes"])["fuentes"]}
        self.discos = _leer(self.rutas["discos"], []) or []
        self.descartados = _leer(self.rutas["descartados"], []) or []
        self.estado_fuentes = _leer(self.rutas["estado_fuentes"], {}) or {}
        self.mapeo = cargar_mapeo(ruta(self.rutas["mapeo_etiquetas"]))
        self.web = _leer("site/data/discos.json", {}) or {}
        self.web_pruebas = _leer("data/validacion_web.json", {}) or {}
        self.hoy = dt.date.today()


# ---------------------------------------------------------------- alcance y reglas
@comprobacion
def familias_presentes(c):
    cuenta = Counter(f for d in c.discos for f in d.get("familias", []))
    minimo = int(c.umb.get("discos_min_por_familia", 20))
    pocas = {f: cuenta.get(f, 0) for f in c.tax_datos["familias"] if cuenta.get(f, 0) < minimo}
    return R("fallo" if pocas else "ok", dict(cuenta), f"mínimo {minimo} por familia",
             [f"{f}: {n}" for f, n in pocas.items()])


@comprobacion
def solo_ingles(c):
    permitidos = set(c.config["reglas"].get("idiomas_permitidos", ["eng"])) | {"zxx", "mul"}
    malos = [d for d in c.discos if d.get("idioma") and d["idioma"] not in permitidos]
    sin = sum(1 for d in c.discos if not d.get("idioma"))
    return R("fallo" if malos else ("aviso" if sin > len(c.discos) * 0.5 else "ok"), len(malos),
             f"{sin} discos sin idioma verificado", [f"{d['artista']} – {d['titulo']} ({d['idioma']})" for d in malos])


@comprobacion
def sin_ep(c):
    tope = int(c.config["reglas"].get("pistas_max_ep", 6))
    # la misma regla que la recogida: el tipo de MusicBrainz/Deezer manda; sin tipo, el nº de pistas
    malos = [d for d in c.discos if (d.get("tipo") or "").lower() in ("ep", "single")
             or (not d.get("tipo") and d.get("pistas") and d["pistas"] <= tope and not d.get("tipo_verificado"))]
    return R("fallo" if malos else "ok", len(malos), f"EP, sencillos o ≤ {tope} pistas entre los discos",
             [f"{d['artista']} – {d['titulo']} ({d.get('tipo') or ''} {d.get('pistas') or ''} pistas)" for d in malos])


@comprobacion
def sin_reediciones(c):
    rx = [re.compile(x) for x in (c.config["reglas"].get("reedicion"), (c.config.get("consolidacion") or {}).get("titulo_no_nuevo")) if x]
    malos = [d for d in c.discos if any(r.search(d["titulo"]) for r in rx)]
    return R("fallo" if malos else "ok", len(malos), "títulos de reedición o edición especial entre los discos",
             [f"{d['artista']} – {d['titulo']}" for d in malos])


@comprobacion
def ventana_y_meses(c):
    ventana = c.estado_fuentes.get("ventana") or []
    fuera = [d for d in c.discos if ventana and not (ventana[0] <= d["fecha"] <= ventana[1])]
    minimo = int(c.umb.get("discos_min_por_mes", 30))
    por_mes = Counter(d["fecha"][:7] for d in c.discos)
    pocos = []
    for anio in c.config["ventana"].get("anios_completos") or []:
        for m in range(1, 13):
            k = f"{anio}-{m:02d}"
            if k <= c.hoy.isoformat()[:7] and por_mes.get(k, 0) < minimo:
                pocos.append(f"{k}: {por_mes.get(k, 0)}")
    estado = "fallo" if fuera else ("aviso" if pocos else "ok")
    return R(estado, dict(sorted(por_mes.items())), f"ventana {ventana}; mínimo {minimo} por mes",
             [f"fuera: {d['artista']} – {d['titulo']} ({d['fecha']})" for d in fuera] + pocos)


# ---------------------------------------------------------------- clasificación
@comprobacion
def taxonomia_valida(c):
    malos = [d for d in c.discos if any(s not in c.tax.sub for s in d.get("subgeneros", []))
             or any(f not in c.tax_datos["familias"] for f in d.get("familias", []))]
    return R("fallo" if malos else "ok", len(malos), "subgéneros y familias que no existen en la taxonomía",
             [f"{d['artista']} – {d['titulo']}: {d.get('subgeneros')}" for d in malos])


@comprobacion
def varios_subgeneros(c):
    n = sum(1 for d in c.discos if len(d.get("subgeneros", [])) >= 2)
    return R("ok" if n else "fallo", n, "discos con dos o más subgéneros")


@comprobacion
def mapeo_sin_pendientes(c):
    pend_total = sum(1 for v in c.mapeo.values() if v["subgenero"] == "pendiente")
    pend_sin_sub = set()
    for d in c.discos:
        if d.get("subgeneros"):
            continue
        for e, _ in etiquetas_de(d, c.tax):
            v = c.mapeo.get(normalizar(e))
            if v and v["subgenero"] == "pendiente":
                pend_sin_sub.add(e)
    malos_ids = [k for k, v in c.mapeo.items() if v["subgenero"] not in ("pendiente", "ninguno", "")
                 and any(s not in c.tax.sub for s in v["subgenero"].split("|"))]
    estado = "fallo" if malos_ids else ("aviso" if pend_sin_sub else "ok")
    return R(estado, {"pendientes": pend_total, "en_discos_sin_subgenero": len(pend_sin_sub), "ids_invalidos": len(malos_ids)},
             "etiquetas pendientes que dejan discos sin subgénero; ids que no existen", sorted(pend_sin_sub)[:10] + malos_ids[:5])


@comprobacion
def coherencia_fuentes(c):
    total = bien = 0
    malos = []
    for d in c.discos:
        if not d.get("subgeneros"):
            continue
        fams = {c.fuentes[x["id"]].get("familia") for x in d.get("fuentes", [])
                if x["id"] in c.fuentes and not c.fuentes[x["id"]].get("mixta")} - {None, "todas", "ninguna"}
        for f in fams:
            total += 1
            if any(f in c.tax.sub[s]["familias"] for s in d["subgeneros"] if s in c.tax.sub):
                bien += 1
            else:
                malos.append(f"{d['artista']} – {d['titulo']}: fuente de {f}, subgéneros {d['subgeneros']}")
    pct = round(100 * bien / total, 1) if total else None
    minimo = float(c.umb.get("coherencia_fuentes_min_pct", 90))
    if pct is None:
        return R("sin_datos")
    return R("ok" if pct >= minimo else "fallo", pct, f"{bien} de {total}; mínimo {minimo} %", malos)


@comprobacion
def muestra_de_referencia(c):
    """Conjunto de referencia (data/revision_clasificacion.csv): para cada disco revisado, lo que debe
    tener y lo que no. Cada semana se compara, disco a disco, con la clasificación actual."""
    p = ruta("data/revision_clasificacion.csv")
    if not os.path.exists(p):
        return R("sin_datos", detalle="no hay muestra revisada")
    with open(p, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    por_id = {d["id"]: d for d in c.discos}
    sp = lambda x: set(filter(None, (x or "").split("|")))
    medidos = bien = 0
    errores = []
    for r in filas:
        if not any(r.get(k) for k in ("esperado", "no_esperado", "familia_esperada", "familia_no_esperada", "fuera")):
            continue                                   # sin respuesta esperada (no se pudo verificar)
        medidos += 1
        d = por_id.get(r["id"])
        subs, fams = set(d.get("subgeneros", [])) if d else set(), set(d.get("familias", [])) if d else set()
        fallos = []
        if r.get("fuera") == "si":
            if d:
                fallos.append("debía quedar fuera")
        elif not d:
            fallos.append("ha desaparecido de la web")
        else:
            if sp(r.get("esperado")) and not sp(r["esperado"]) & subs:
                fallos.append(f"le falta {r['esperado']}")
            if sp(r.get("no_esperado")) & subs:
                fallos.append(f"sobra {'|'.join(sp(r['no_esperado']) & subs)}")
            if sp(r.get("familia_esperada")) - fams:
                fallos.append(f"falta la familia {r['familia_esperada']}")
            if sp(r.get("familia_no_esperada")) & fams:
                fallos.append(f"sobra la familia {r['familia_no_esperada']}")
        if fallos:
            errores.append(f"{r['artista']} – {r['titulo']}: " + "; ".join(fallos))
        else:
            bien += 1
    if not medidos:
        return R("sin_datos")
    pct = round(100 * bien / medidos, 1)
    minimo = float(c.umb.get("muestra_acierto_min_pct", 85))
    return R("ok" if pct >= minimo else "fallo", pct, f"{bien} de {medidos} discos de referencia exactamente bien; mínimo {minimo} %", errores)


def _familias_de_texto(c, texto: str) -> set[str]:
    """Familias que nombra un texto de géneros ("Americana, alt-country, folk rock") según la taxonomía,
    sus genéricas y la tabla de etiquetas."""
    fams = set()
    for trozo in re.split(r"\s*[,;/]\s*", texto or ""):
        n = normalizar(trozo)
        subs = set(c.tax.alias.get(n, ()))
        v = c.mapeo.get(n)
        if v and v["subgenero"] not in ("pendiente", "ninguno", ""):
            subs |= set(v["subgenero"].split("|"))
        for s in subs:
            if s in c.tax.sub and not c.tax.sub[s]["frontera"]:
                fams |= set(c.tax.sub[s]["familias"])
        if n in c.tax.genericas:
            fams.add(c.tax.genericas[n])
    return fams


@comprobacion
def acuerdo_wikipedia(c):
    """¿Coincide la familia que damos con el género que pone Wikipedia para ese disco? (Wikipedia también
    es una de nuestras fuentes, así que no es del todo independiente: sirve para detectar desvíos.)"""
    p = ruta(os.path.join(c.rutas.get("cache_lecturas", "data/cache/lecturas"), "wikipedia.json"))
    if not os.path.exists(p):
        return R("sin_datos")
    items = json.load(open(p, encoding="utf-8")).get("items", [])
    por_clave = {(normalizar(d["artista"]), canon(d["titulo"]).replace(" ", "")): d for d in c.discos}
    total = bien = 0
    malos = []
    for it in items:
        d = por_clave.get((normalizar(it.get("artista")), canon(it.get("titulo")).replace(" ", "")))
        esperadas = _familias_de_texto(c, it.get("genero"))
        if not d or not esperadas:
            continue
        total += 1
        if esperadas & set(d.get("familias", [])):
            bien += 1
        else:
            malos.append(f"{d['artista']} – {d['titulo']}: Wikipedia «{it.get('genero')}», aquí {d.get('familias')}")
    if not total:
        return R("sin_datos")
    pct = round(100 * bien / total, 1)
    minimo = float(c.umb.get("acuerdo_wikipedia_min_pct", 85))
    return R("ok" if pct >= minimo else "fallo", pct, f"{bien} de {total} discos con la familia que indica Wikipedia; mínimo {minimo} %", malos)


# ---------------------------------------------------------------- fuentes
@comprobacion
def fuentes_estado(c):
    est = c.estado_fuentes.get("fuentes") or {}
    if not est:
        return R("sin_datos")
    malas = {k: v for k, v in est.items() if v.get("estado") != "ok"}
    pct = round(100 * (len(est) - len(malas)) / len(est), 1)
    minimo = float(c.umb.get("fuentes_ok_min_pct", 90))
    return R("ok" if pct >= minimo else "fallo", pct, f"{len(est) - len(malas)} de {len(est)} fuentes leídas bien",
             [f"{v.get('nombre', k)}: {v.get('estado')} {v.get('detalle', '')[:80]}" for k, v in malas.items()])


@comprobacion
def fuentes_por_familia(c):
    minimo = int(c.umb.get("fuentes_min_por_familia", 5))
    cuenta = Counter()
    for f in c.fuentes.values():
        if f.get("activa", True) is False:
            continue
        for fam in ([f.get("familia")] + [f.get("familia_sin_subgenero")]):
            if fam in c.tax_datos["familias"]:
                cuenta[fam] += 1
    pocas = [f"{fam}: {cuenta.get(fam, 0)}" for fam in c.tax_datos["familias"] if cuenta.get(fam, 0) < minimo]
    return R("aviso" if pocas else "ok", dict(cuenta), f"fuentes especializadas por familia (mínimo {minimo}; "
             "además cuentan las generales y los radares)", pocas)


@comprobacion
def ritmo_peticiones(c):
    iv = c.config["peticiones"].get("intervalos") or {}
    bc = max([v for k, v in iv.items() if "bandcamp" in k] or [0])
    mb = max([v for k, v in iv.items() if "musicbrainz" in k] or [0])
    ok = bc >= 4.0 and mb >= 1.0
    return R("ok" if ok else "fallo", {"bandcamp": bc, "musicbrainz": mb}, "Bandcamp ≥ 4 s, MusicBrainz ≥ 1 s")


@comprobacion
def robots_activo(c):
    return R("ok" if c.config["peticiones"].get("respetar_robots_txt", True) else "fallo")


@comprobacion
def bloqueos_respetados(c):
    est = c.estado_fuentes.get("fuentes") or {}
    bloq = [f"{v.get('nombre', k)}: {v.get('detalle', '')[:80]}" for k, v in est.items() if v.get("estado") in ("bloqueada", "prohibida")]
    textos = (c.config.get("bloqueo") or {}).get("textos") or []
    return R("ok" if textos else "fallo", len(bloq), "detección de bloqueos activa; fuentes bloqueadas que se dejan de leer", bloq)


@comprobacion
def configuracion_valida(c):
    malas = []
    for f in c.fuentes.values():
        falta = {"id", "nombre", "lector", "familia"} - set(f)
        if falta or f.get("familia") not in set(c.tax_datos["familias"]) | {"todas", "ninguna"}:
            malas.append(f"{f.get('id')}: falta {falta or ''} familia {f.get('familia')}")
    return R("fallo" if malas else "ok", len(c.fuentes), "fuentes configuradas", malas)


@comprobacion
def fuente_wikipedia(c):
    e = (c.estado_fuentes.get("fuentes") or {}).get("wikipedia", {})
    return R("ok" if e.get("estado") == "ok" else "fallo", e.get("items"), e.get("detalle", ""))


@comprobacion
def radares_activos(c):
    est = c.estado_fuentes.get("fuentes") or {}
    r = {k: est.get(k, {}).get("estado") for k in ("radar_musicbrainz", "radar_deezer")}
    return R("ok" if all(v == "ok" for v in r.values()) else "fallo", r)


@comprobacion
def listas_anuales(c):
    p = ruta(c.rutas.get("listas_anuales", "data/listas_anuales.json"))
    if not os.path.exists(p):
        return R("fallo", detalle="no hay listas anuales")
    listas = json.load(open(p, encoding="utf-8"))
    desde, minimo = int(c.umb.get("listas_anuales_desde", 2019)), int(c.umb.get("listas_anuales_min", 20))
    pocas = [f"{a}: {len(listas.get(str(a), {}))}" for a in range(desde, c.hoy.year) if len(listas.get(str(a), {})) < minimo]
    return R("fallo" if pocas else "ok", {a: len(v) for a, v in listas.items()}, f"discos en listas de fin de año por año (mínimo {minimo})", pocas)


@comprobacion
def anios_por_plantilla(c):
    """Cargar otro año debe ser cambiar un número: ninguna fuente con un año escrito a mano en sus direcciones."""
    malas = [f"{f['id']}: {u}" for f in c.fuentes.values() for u in f.get("urls", [])
             if re.search(r"(?<!\d)20\d\d(?!\d)", u) and "{anio}" not in u]
    return R("fallo" if malas else "ok", len(malas), "direcciones con el año escrito a mano", malas)


# ---------------------------------------------------------------- datos por disco
CAMPOS = {"portada": lambda d: d.get("portada") or (d.get("deezer") or {}).get("portada"),
          "fecha_exacta": lambda d: d.get("fecha_exacta"), "sello": lambda d: d.get("sello"),
          "pistas": lambda d: d.get("pistas"), "subgenero": lambda d: d.get("subgeneros"),
          "enlace_escucha": lambda d: any(k in (d.get("enlaces") or {}) for k in ("deezer", "bandcamp", "apple", "spotify", "qobuz"))
          or (d.get("deezer") or {}).get("url")}


def _publicados(c):
    return [d for d in c.discos if d["fecha"] <= c.hoy.isoformat()]


@comprobacion
def cobertura_campos(c):
    pub = _publicados(c)
    if not pub:
        return R("sin_datos")
    minimos = c.umb.get("cobertura_min_pct") or {}
    pct = {k: round(100 * sum(1 for d in pub if f(d)) / len(pub), 1) for k, f in CAMPOS.items()}
    bajos = [f"{k}: {v} % (mínimo {minimos[k]} %)" for k, v in pct.items() if k in minimos and v < minimos[k]]
    return R("fallo" if bajos else "ok", pct, f"{len(pub)} discos ya publicados", bajos)


@comprobacion
def cobertura_portadas(c):
    pub = _publicados(c)
    pct = round(100 * sum(1 for d in pub if CAMPOS["portada"](d)) / len(pub), 1) if pub else None
    minimo = (c.umb.get("cobertura_min_pct") or {}).get("portada", 95)
    return R("sin_datos") if pct is None else R("ok" if pct >= minimo else "fallo", pct, f"mínimo {minimo} %")


@comprobacion
def fuente_por_disco(c):
    malos = [d for d in c.discos if not d.get("fuentes") or not any(x.get("id") for x in d["fuentes"])]
    return R("fallo" if malos else "ok", len(malos), "discos sin fuente", [f"{d['artista']} – {d['titulo']}" for d in malos])


@comprobacion
def pruebas_por_fuente(c):
    con_fecha = sum(1 for d in c.discos if any(x.get("fecha") for x in d.get("fuentes", [])))
    pct = round(100 * con_fecha / len(c.discos), 1) if c.discos else None
    return R("aviso", pct, "cada disco con fuente y fecha; falta la confianza por fuente (P7)")


@comprobacion
def duplicados(c):
    vistos, dup = {}, []
    for d in c.discos:
        k = (normalizar(d["artista"]), canon(d["titulo"]).replace(" ", ""))
        if k in vistos:
            dup.append(f"{d['artista']} – {d['titulo']} ({d['fecha']} y {vistos[k]})")
        vistos[k] = d["fecha"]
    mb = Counter(d.get("mbid") for d in c.discos if d.get("mbid"))
    dup += [f"MusicBrainz {k} repetido {n} veces" for k, n in mb.items() if n > 1]
    return R("fallo" if dup else "ok", len(dup), "mismo artista y título, o mismo disco de MusicBrainz", dup)


@comprobacion
def reseñas_con_frase(c):
    total = con = 0
    for f in glob.glob(ruta("site/data/fichas/*.json")):
        for v in json.load(open(f, encoding="utf-8")).values():
            for r in v.get("resenas", []):
                total += 1
                con += bool(r.get("frase"))
    pct = round(100 * con / total, 1) if total else None
    return R("sin_datos") if pct is None else R("ok" if pct >= 50 else "fallo", pct, f"{con} de {total} reseñas con frase")


@comprobacion
def canciones(c):
    total = con = 0
    for f in glob.glob(ruta("site/data/fichas/*.json")):
        for v in json.load(open(f, encoding="utf-8")).values():
            total += 1
            con += bool(v.get("canciones"))
    pct = round(100 * con / total, 1) if total else None
    return R("sin_datos") if pct is None else R("ok" if pct >= 60 else "fallo", pct, f"{con} de {total} fichas con lista de canciones")


# ---------------------------------------------------------------- web y publicación
@comprobacion
def mejores_del_anio(c):
    m = (c.web.get("mejores") or {}).get(str(c.hoy.year))
    return R("ok" if m else "fallo", m.get("tipo") if m else None, f"'lo mejor de {c.hoy.year}' en la web")


@comprobacion
def ranking_ponderado(c):
    peso = float((c.tax_datos.get("reglas") or {}).get("peso_media_global", 0))
    return R("ok" if peso > 0 else "fallo", peso, "media bayesiana activada")


@comprobacion
def web_publicada(c):
    n_web = len(c.web.get("discos", []))
    ok = os.path.exists(ruta("site/index.html")) and n_web == len(c.discos)
    return R("ok" if ok else "fallo", n_web, f"la web tiene {n_web} discos y los datos {len(c.discos)}")


@comprobacion
def rss_y_calendarios(c):
    rss, ics = glob.glob(ruta("site/rss/*.xml")), glob.glob(ruta("site/cal/*.ics"))
    return R("ok" if rss and ics else "fallo", {"rss": len(rss), "calendarios": len(ics)})


@comprobacion
def sin_rastreo(c):
    html = _leer("site/index.html", "") or ""
    malos = re.findall(r"google-analytics|googletagmanager|gtag\(|facebook\.net|hotjar|doubleclick", html)
    return R("fallo" if malos else "ok", len(malos), "scripts de rastreo o publicidad en la web", malos)


@comprobacion
def aprobacion_usuario(c):
    ap = cargar_yaml("data/aprobaciones.yaml") if os.path.exists(ruta("data/aprobaciones.yaml")) else None
    return R("ok" if ap else "sin_datos", None, "diseño aprobado por el usuario con capturas (data/aprobaciones.yaml)")


# ---------------------------------------------------------------- procesos
@comprobacion
def llm_sin_pago(c):
    llm = (c.config.get("enriquecimiento") or {}).get("llm") or {}
    return R("fallo" if llm.get("activo") else "ok", bool(llm.get("activo")), "API de pago desactivada")


@comprobacion
def action_semanal(c):
    wf = _leer(".github/workflows/semanal.yml", "") or ""
    ok = "schedule" in wf and re.search(r"cron:\s*\"[^\"]*\* \* 6\"", wf)
    return R("ok" if ok else "fallo", None, "Action con ejecución cada sábado")


@comprobacion
def reanudacion(c):
    ok = bool(c.rutas.get("estado_pipeline")) and bool(c.rutas.get("cache_lecturas")) and os.path.exists(ruta("CLAUDE.md")) \
        and os.path.exists(ruta("docs/progreso.md"))
    return R("ok" if ok else "fallo", None, "estado de fases, lecturas guardadas, CLAUDE.md y docs/progreso.md")


@comprobacion
def pruebas_existentes(c):
    n = sum(len(re.findall(r"^def test_", open(f, encoding="utf-8").read(), re.M)) for f in glob.glob(ruta("tests/test_*.py")))
    return R("ok" if n >= 100 else "aviso", n, "pruebas unitarias y de extremo a extremo")


@comprobacion
def sin_secretos(c):
    try:
        archivos = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True).stdout.split()
    except OSError:
        return R("sin_datos")
    rx = re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|xox[bp]-[0-9A-Za-z-]{20,}")
    malos = []
    for a in archivos:
        p = os.path.join(RAIZ, a)
        if os.path.getsize(p) > 2_000_000 or a.endswith((".jpg", ".png")):
            continue
        try:
            if rx.search(open(p, encoding="utf-8", errors="ignore").read()):
                malos.append(a)
        except OSError:
            pass
    return R("fallo" if malos else "ok", len(malos), "claves o tokens escritos en el repositorio", malos)


@comprobacion
def informe_secciones(c):
    t = _leer("docs/informe.md", "") or ""
    necesarias = ["Calidad de los datos", "Discos por familia y subgénero"]
    faltan = [s for s in necesarias if s not in t]
    return R("fallo" if faltan else "ok", None, "secciones del informe", faltan)


@comprobacion
def estudio_repetible(c):
    cap = _leer("docs/estado-del-arte/capturas.json", {}) or {}
    ok = os.path.exists(ruta("estudio/capturar.mjs")) and os.path.exists(ruta("estudio/referencias.yaml")) and cap
    if not ok:
        return R("fallo", detalle="falta el estudio repetible o sus capturas")
    dias = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(cap["fecha"].replace("Z", "+00:00"))).days
    maximo = int(c.umb.get("estudio_max_dias", 120))
    return R("ok" if dias <= maximo else "aviso", dias, f"días desde el último estudio (máximo {maximo})")


@comprobacion
def validacion_automatica(c):
    return R("ok", len(COMPROBACIONES), "comprobaciones automáticas en scraper/validar.py")


@comprobacion
def descubrimiento_referencias(c):
    """¿Perdemos discos? Frente a referencias independientes (scraper/referencias.py): de los discos de
    nuestros géneros que tiene la referencia, cuántos no tenemos."""
    ref = _leer("data/referencias.json", {}) or {}
    if not ref.get("referencias"):
        return R("sin_datos", detalle="sin lectura de referencias (python -m scraper.referencias)")
    tope = float(c.umb.get("perdidos_max_pct", 10))
    peor, detalle, ejemplos = "ok", [], []
    for rid, r in ref["referencias"].items():
        cnt = Counter(i["resultado"] for i in r["items"])
        base = cnt["en_web"] + cnt["perdido"]
        pct = round(100 * cnt["perdido"] / base, 1) if base else None
        detalle.append(f"{r['nombre']}: {r['estado']}, {len(r['items'])} discos · en la web {cnt['en_web']} · perdidos {cnt['perdido']} "
                       f"({pct} %) · descartados con motivo {cnt['descartado']} · no son novedad {cnt['no_es_nuevo']} · "
                       f"de otros géneros {cnt['fuera_de_genero']} · sin poder saber su género {cnt['sin_genero']}")
        ejemplos += [f"perdido: {i['artista']} – {i['titulo']} ({', '.join(i.get('generos', [])[:3])})" for i in r["items"] if i["resultado"] == "perdido"]
        ejemplos += [f"sin género: {i['artista']} – {i['titulo']}" for i in r["items"] if i["resultado"] == "sin_genero"]
        if r["estado"] != "ok" or pct is None:
            peor = "aviso" if peor == "ok" else peor
        elif pct > tope:
            peor = "fallo"
    return R(peor, None, " | ".join(detalle) + f" (máximo {tope} % perdidos)", ejemplos)


# ---------------------------------------------------------------- motor
def ejecutar() -> dict:
    c = Contexto()
    reqs = yaml.safe_load(open(ruta("data/requisitos.yaml"), encoding="utf-8"))["requisitos"]
    res_comp = {}
    for nombre, f in COMPROBACIONES.items():
        try:
            res_comp[nombre] = f(c)
        except Exception as e:      # una comprobación rota no tumba las demás: se ve como fallo
            res_comp[nombre] = R("fallo", detalle=f"error al comprobar: {type(e).__name__}: {e}")
    res_req = {}
    for r in reqs:
        estados = []
        for nombre in r["comprobaciones"]:
            if nombre.startswith("web:"):
                v = c.web_pruebas.get(nombre[4:])
                # sin resultado: si la prueba en navegador ya se ejecutó, es que esa comprobación no existe aún
                estados.append(("sin_comprobar" if c.web_pruebas else "sin_datos") if v is None else ("ok" if v else "fallo"))
            else:
                estados.append(res_comp.get(nombre, {"estado": "sin_comprobar"})["estado"])
        estado = min(estados, key=lambda e: ORDEN[e]) if estados else "sin_comprobar"
        res_req[r["id"]] = {"estado": estado, "capa": r["capa"], "texto": r["texto"], "comprobaciones": r["comprobaciones"]}
    capas = defaultdict(Counter)
    for v in res_req.values():
        capas[v["capa"]][v["estado"]] += 1
    resumen = {k: dict(v) for k, v in sorted(capas.items())}
    salida = {"fecha": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "capas": resumen,
              "requisitos": res_req, "comprobaciones": res_comp,
              "totales": dict(Counter(v["estado"] for v in res_req.values()))}
    return salida, c


def historial(salida: dict, c: Contexto) -> list[str]:
    """Cifras de esta ejecución frente a la anterior: avisa de saltos grandes por fuente, familia y motivo."""
    p = ruta("data/historial_validacion.json")
    hist = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
    motivo = lambda m: re.sub(r"\(.*|«.*|\d{4}-\d\d(-\d\d)?|:.*", "", m).strip()[:50]
    foto = {"fecha": salida["fecha"][:10], "discos": len(c.discos), "descartados": len(c.descartados),
            "por_familia": dict(Counter(f for d in c.discos for f in d.get("familias", []))),
            "por_fuente": {k: v.get("items", 0) for k, v in (c.estado_fuentes.get("fuentes") or {}).items()},
            "por_motivo": dict(Counter(motivo(x["motivo"]) for x in c.descartados))}
    avisos = []
    if hist:
        ant, tope = hist[-1], float(c.umb.get("salto_max_pct", 30)) / 100
        for clave in ("por_familia", "por_fuente", "por_motivo"):
            for k, v in foto[clave].items():
                a = ant.get(clave, {}).get(k)
                if a and a >= 20 and abs(v - a) / a > tope:
                    avisos.append(f"{clave.replace('por_', '')} «{k}»: {a} → {v}")
        for k in ant.get("por_fuente", {}):
            if ant["por_fuente"][k] and not foto["por_fuente"].get(k):
                avisos.append(f"fuente «{k}» ha dejado de dar discos ({ant['por_fuente'][k]} → 0)")
    if not hist or hist[-1]["fecha"] != foto["fecha"]:
        hist.append(foto)
    else:
        hist[-1] = foto
    guardar_json(p, hist[-104:], ensure_ascii=False, indent=0)
    return avisos


def escribir_md(salida: dict, avisos: list[str]) -> str:
    L = [f"# Validación automática · {salida['fecha'][:10]}", "",
         "Generado por `python -m scraper.validar` (cada semana en la Action). Cada requisito de "
         "`data/requisitos.yaml` se comprueba solo, con los datos; nada se revisa a mano.", "",
         "🟢 cumple · 🟡 aviso · 🔴 no cumple · ⚪ sin datos todavía · ⚫ sin comprobación automática", "",
         "## Por capa", "", "| Capa | 🟢 | 🟡 | 🔴 | ⚪ | ⚫ |", "|---|---:|---:|---:|---:|---:|"]
    for capa, cnt in salida["capas"].items():
        L.append(f"| {capa} | {cnt.get('ok', 0)} | {cnt.get('aviso', 0)} | {cnt.get('fallo', 0)} | {cnt.get('sin_datos', 0)} | {cnt.get('sin_comprobar', 0)} |")
    t = salida["totales"]
    L += ["", f"**Total: {sum(t.values())} requisitos** · cumplen {t.get('ok', 0)} · aviso {t.get('aviso', 0)} · "
          f"no cumplen {t.get('fallo', 0)} · sin datos {t.get('sin_datos', 0)} · sin comprobación {t.get('sin_comprobar', 0)}", ""]
    if avisos:
        L += ["## Cambios bruscos frente a la ejecución anterior", ""] + [f"- {a}" for a in avisos] + [""]
    L += ["## Comprobaciones que fallan o avisan", ""]
    for n, r in sorted(salida["comprobaciones"].items(), key=lambda kv: ORDEN[kv[1]["estado"]]):
        if r["estado"] in ("fallo", "aviso"):
            val = r["valor"] if not isinstance(r["valor"], dict) else ", ".join(f"{k} {v}" for k, v in list(r["valor"].items())[:8])
            L.append(f"- {ICONO[r['estado']]} **{n}**: {r['detalle']} — {val}")
            L += [f"    - {e}" for e in r["ejemplos"][:5]]
    L += ["", "## Todos los requisitos", "", "| ID | Requisito | Capa | Estado |", "|---|---|---|---|"]
    for i, r in salida["requisitos"].items():
        L.append(f"| {i} | {r['texto'][:90]} | {r['capa']} | {ICONO[r['estado']]} {NOMBRE_ESTADO[r['estado']]} |")
    return "\n".join(L) + "\n"


def main(args: list[str] | None = None) -> int:
    args = sys.argv[1:] if args is None else args
    salida, c = ejecutar()
    avisos = historial(salida, c)
    salida["avisos_historial"] = avisos
    guardar_json(ruta("data/validacion.json"), salida, ensure_ascii=False, indent=1)
    with open(ruta("docs/validacion.md"), "w", encoding="utf-8") as f:
        f.write(escribir_md(salida, avisos))
    t = salida["totales"]
    print(f"Validación: {sum(t.values())} requisitos · 🟢 {t.get('ok', 0)} · 🟡 {t.get('aviso', 0)} · 🔴 {t.get('fallo', 0)} · "
          f"⚪ {t.get('sin_datos', 0)} · ⚫ {t.get('sin_comprobar', 0)}")
    for capa, cnt in salida["capas"].items():
        peor = min(cnt, key=lambda e: ORDEN[e])
        print(f"  {ICONO[peor]} {capa}: " + " · ".join(f"{NOMBRE_ESTADO[e]} {n}" for e, n in sorted(cnt.items(), key=lambda kv: ORDEN[kv[0]])))
    if avisos:
        print("Cambios bruscos: " + "; ".join(avisos[:5]))
    return 1 if "--estricto" in args and t.get("fallo") else 0


if __name__ == "__main__":
    raise SystemExit(main())
