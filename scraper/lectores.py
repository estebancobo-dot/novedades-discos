"""Lectores genéricos. Ninguno sabe nada de una web concreta: todo lo que
necesitan (direcciones, qué parte de la página leer, cómo reconocer artista,
título y fecha) viene de data/fuentes.yaml.

Tipos de lector:
  texto  – una página HTML convertida a texto + expresiones regulares.
  rss    – un feed RSS/Atom; las reglas se aplican al título de cada entrada.
  sonda  – solo comprueba si la web responde (p. ej. Bandcamp).
"""
from __future__ import annotations

import datetime as dt
import html
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from .html_texto import html_a_texto
from .http import Bloqueado, Navegador, Prohibido
from .util import limpiar, parse_fecha

CAMPOS = ("artista", "titulo", "sello", "fecha", "genero", "tipo", "nota", "url", "portada", "extra", "anio", "pistas")


@dataclass
class Item:
    fuente: str
    artista: str
    titulo: str
    fecha: dt.date | None = None
    fecha_tipo: str = "lanzamiento"
    sello: str | None = None
    genero: str | None = None
    tipo: str | None = None
    nota: str | None = None
    url: str | None = None
    portada: str | None = None
    extra: str | None = None
    anio: int | None = None
    pistas: int | None = None
    mencion: str | None = None     # titular sin artista/título claros: se empareja después
    resenas_extra: list = field(default_factory=list)   # reseñas citadas: [{"medio", "nota"}]
    fecha_publicacion: dt.date | None = None
    etiquetas: list[str] = field(default_factory=list)


@dataclass
class ResultadoFuente:
    id: str
    estado: str = "ok"            # ok | bloqueada | prohibida | error | vacia
    detalle: str = ""
    paginas: int = 0
    items: list[Item] = field(default_factory=list)


MACROS: dict[str, str] = {}


def expandir(patron: str) -> str:
    """Sustituye {{NOMBRE}} por la macro definida en fuentes.yaml (macros:)."""
    for _ in range(3):
        patron = re.sub(r"\{\{(\w+)\}\}", lambda m: MACROS.get(m.group(1), m.group(0)), patron)
    return patron


def _compilar(lista):
    return [re.compile(expandir(p), re.M) for p in (lista or [])]


def _rx(p):
    return re.compile(expandir(p), re.M) if p else None


def _grupos(m) -> dict:
    """Grupos con nombre; 'fecha_2', 'titulo_2'… cuentan como 'fecha', 'titulo'…"""
    g = {}
    for k, v in m.groupdict().items():
        if v:
            g.setdefault(re.sub(r"_\d+$", "", k), v)
    return g


def fecha_de_pagina(html: str) -> dt.date | None:
    """Fecha de publicación declarada por la página (meta article:published_time, <time>)."""
    for rx in (r'property="article:published_time"\s+content="(\d{4}-\d{2}-\d{2})',
               r'content="(\d{4}-\d{2}-\d{2})[^"]*"\s+property="article:published_time"',
               r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})',
               r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})'):
        m = re.search(rx, html)
        if m:
            return dt.date.fromisoformat(m.group(1))
    return None


def _items_de_texto(texto: str, cfg: dict, fuente: str, hoy: dt.date, fecha_defecto=None,
                    indice: bool = False) -> list[Item]:
    patrones = _compilar(cfg.get("patrones"))
    cab = _rx(cfg.get("cabecera_fecha"))
    excluir = _rx(cfg.get("excluir"))
    rx_resenas = _rx(cfg.get("resenas_en_texto"))
    dia_primero = bool(cfg.get("dia_primero", False))
    cabeceras = []
    if cab:
        for m in cab.finditer(texto):
            f = parse_fecha(m.groupdict().get("fecha") or m.group(0), hoy, dia_primero)
            if f:
                cabeceras.append((m.start(), f))
    vistos = set()
    items = []
    for pat in patrones:
        for m in pat.finditer(texto):
            if (m.start(), m.end()) in vistos:
                continue
            g = _grupos(m)
            if excluir and excluir.search(m.group(0)):
                continue
            artista, titulo = limpiar(g.get("artista")), limpiar(g.get("titulo"))
            mencion = limpiar(g.get("mencion"))
            if indice and g.get("url"):
                artista, titulo = artista or "", titulo or ""
            elif mencion and not (artista and titulo):
                artista, titulo = artista or "", titulo or ""
            elif not artista or not titulo:
                continue
            vistos.add((m.start(), m.end()))
            fecha = parse_fecha(g.get("fecha"), hoy, dia_primero) if g.get("fecha") else None
            if not fecha:
                previas = [f for pos, f in cabeceras if pos <= m.start()]
                fecha = previas[-1] if previas else fecha_defecto
            it = Item(fuente=fuente, artista=artista, titulo=titulo, fecha=fecha, mencion=mencion)
            for k in ("sello", "genero", "tipo", "nota", "url", "portada", "extra"):
                if g.get(k):
                    setattr(it, k, limpiar(g[k]) if k not in ("url", "portada") else g[k].strip())
            if g.get("anio", "").isdigit():
                it.anio = int(g["anio"])
            if rx_resenas:
                for mr in rx_resenas.finditer(m.group(0)):
                    gr = mr.groupdict()
                    if gr.get("medio"):
                        it.resenas_extra.append({"medio": limpiar(gr["medio"]), "nota": limpiar(gr.get("nota"))})
            items.append(it)
    return items


def _detalle(nav: Navegador, it: Item, cfg: dict, hoy: dt.date) -> list[Item]:
    """Abre la página de un item y completa campos (o saca varios items)."""
    r = nav.get(it.url)
    if r.estado != 200:
        return [it]
    t = html_a_texto(r.texto, r.url, **(cfg.get("texto") or {}))
    if cfg.get("patrones"):
        fpag = fecha_de_pagina(r.texto)
        hijos = _items_de_texto(t, cfg, it.fuente, fpag or hoy, fecha_defecto=it.fecha or fpag)
        for h in hijos:
            h.fecha_tipo = it.fecha_tipo
            h.fecha_publicacion = it.fecha_publicacion or fpag
            h.url = h.url or it.url
        return hijos
    for campo, rx in (cfg.get("campos") or {}).items():
        m = re.search(rx, t, re.M)
        if not m:
            continue
        v = limpiar(m.groupdict().get(campo) or (m.group(1) if m.groups() else m.group(0)))
        if campo == "fecha":
            it.fecha = parse_fecha(v, hoy) or it.fecha
        elif campo == "anio" and v and v[:4].isdigit():
            it.anio = int(v[:4])
        elif v:
            setattr(it, campo, v)
    for campo, rx in (cfg.get("contar") or {}).items():
        n = len(re.findall(rx, t, re.M))
        if n:
            setattr(it, campo, n)
    return [it]


def _urls(cfg: dict, hoy: dt.date | None = None, desde: dt.date | None = None) -> list[str]:
    """Direcciones de una fuente: fijas, paginadas por número o por fecha.

    paginacion: {plantilla: "...{n}...", desde: 2, hasta: 5}
    paginacion: {fechas: {plantilla: "...{fecha}...", formato: "%b-%-d-%Y", minusculas: true,
                          dia_semana: 4, semanas: 22}}     # 0=lunes … 4=viernes
    """
    urls = list(cfg.get("urls") or [])
    pag = cfg.get("paginacion") or {}
    if pag.get("plantilla"):
        for n in range(int(pag.get("desde", 2)), int(pag.get("hasta", 3)) + 1):
            urls.append(pag["plantilla"].format(n=n))
    fx = pag.get("fechas")
    if fx:
        hoy = hoy or dt.date.today()
        d = hoy - dt.timedelta(days=(hoy.weekday() - int(fx.get("dia_semana", 4))) % 7)
        if fx.get("excluir_actual", True):
            d -= dt.timedelta(days=7)
        for _ in range(int(fx.get("semanas", 4))):
            if desde and d < desde - dt.timedelta(days=7):
                break
            f = d.strftime(fx.get("formato", "%Y-%m-%d"))
            urls.append(fx["plantilla"].format(fecha=f.lower() if fx.get("minusculas") else f))
            d -= dt.timedelta(days=7)
    return urls


def recortar(texto: str, desde: str | None, hasta: str | None) -> str:
    if desde and desde in texto:
        texto = texto[texto.index(desde) + len(desde):]
    if hasta and hasta in texto:
        texto = texto[: texto.index(hasta)]
    return texto


def leer_texto(nav, cfg, hoy, desde=None) -> ResultadoFuente:
    res = ResultadoFuente(cfg["id"])
    tcfg = dict(cfg.get("texto") or {})
    desde_txt, hasta_txt = tcfg.pop("desde", None), tcfg.pop("hasta", None)
    por_fechas = bool((cfg.get("paginacion") or {}).get("fechas"))
    rx_fpag = _rx(cfg.get("fecha_pagina"))
    for url in _urls(cfg, hoy, desde):
        try:
            r = nav.get(url)
        except ConnectionError as e:
            res.detalle += f" {url} → {e};"
            continue
        res.paginas += 1
        if r.estado != 200:
            if not por_fechas:
                res.detalle += f" {url} → HTTP {r.estado};"
            if cfg.get("paginacion") and res.items and not por_fechas:
                break
            continue
        completo = html_a_texto(r.texto, r.url, **tcfg)
        t = recortar(completo, desde_txt, hasta_txt)
        ref = (fecha_de_pagina(r.texto) if cfg.get("anio_desde_publicacion") else None) or hoy
        if cfg.get("anio_desde_url"):
            ma = re.search(cfg["anio_desde_url"], url)
            if ma:   # fechas sin año: el año que dice la dirección (p. ej. "List_of_2026_albums")
                ref = dt.date(int(ma.group(1)), 7, 1)
        fdef = None
        if rx_fpag:
            mf = rx_fpag.search(completo)
            fdef = parse_fecha(mf.groupdict().get("fecha") or mf.group(0), hoy) if mf else None
        nuevos = _items_de_texto(t, cfg, cfg["id"], ref, fecha_defecto=fdef,
                                 indice=bool((cfg.get("detalle") or {}).get("patrones")))
        for it in nuevos:
            it.fecha_tipo = cfg.get("fecha_es", "lanzamiento")
            if it.fecha_tipo == "publicacion":
                it.fecha_publicacion = it.fecha
        res.items.extend(nuevos)
        if cfg.get("paginacion") and not por_fechas and (not nuevos or _todo_antiguo([i.fecha for i in nuevos], desde)):
            break
    _seguir_detalles(nav, cfg, res, hoy, desde)
    return res


def _todo_antiguo(fechas, desde) -> bool:
    fechas = [f for f in fechas if f]
    return bool(desde and fechas and max(fechas) < desde)


def leer_rss(nav, cfg, hoy, desde=None) -> ResultadoFuente:
    res = ResultadoFuente(cfg["id"])
    patrones = _compilar(cfg.get("patrones"))
    filtro, excluir, rx_nota = _rx(cfg.get("filtro")), _rx(cfg.get("excluir")), _rx(cfg.get("nota"))
    vistos = set()
    for url in _urls(cfg, hoy):
        r = nav.get(url, acepta="application/rss+xml, application/xml, text/xml")
        res.paginas += 1
        if r.estado != 200:
            break
        soup = BeautifulSoup(r.texto, "xml")
        entradas = soup.find_all(["item", "entry"])
        if not entradas:
            break
        fechas_pag = [parse_fecha(_txt(e, "pubDate") or _txt(e, "published") or _txt(e, "updated"), hoy)
                      for e in entradas]
        for e in entradas:
            titulo = re.sub(r"\s+", " ", html.unescape(_txt(e, "title") or "")).strip()
            enlace = _txt(e, "link") or (e.find("link").get("href") if e.find("link") else None)
            if enlace in vistos:
                continue
            vistos.add(enlace)
            if filtro and not filtro.search(titulo):
                continue
            if excluir and excluir.search(titulo):
                continue
            fecha = parse_fecha(_txt(e, "pubDate") or _txt(e, "published") or _txt(e, "updated"), hoy)
            cats = [limpiar(c.get_text()) for c in e.find_all("category")]
            contenido = _txt(e, "encoded") or _txt(e, "description") or _txt(e, "content") or ""
            texto_cont = BeautifulSoup(contenido, "lxml").get_text(" ") if "<" in contenido else contenido
            for pat in patrones:
                m = pat.search(titulo)
                if not m:
                    continue
                g = _grupos(m)
                artista, tit = limpiar(g.get("artista")), limpiar(g.get("titulo"))
                mencion = limpiar(g.get("mencion"))
                if not (artista and tit) and not mencion:
                    continue
                it = Item(fuente=cfg["id"], artista=artista or "", titulo=tit or "", fecha=fecha,
                          fecha_tipo="publicacion", fecha_publicacion=fecha, url=enlace,
                          mencion=mencion if not (artista and tit) else None,
                          etiquetas=[c for c in cats if c])
                for k in ("sello", "genero", "tipo", "extra"):
                    if g.get(k):
                        setattr(it, k, limpiar(g[k]))
                if rx_nota:
                    mn = rx_nota.search(texto_cont)
                    if mn:
                        it.nota = limpiar(mn.groupdict().get("nota") or mn.group(0))
                res.items.append(it)
                break
        if _todo_antiguo(fechas_pag, desde):
            break
    _seguir_detalles(nav, cfg, res, hoy, desde)
    return res


def _seguir_detalles(nav, cfg, res: ResultadoFuente, hoy, desde=None):
    det = cfg.get("detalle")
    if not det:
        return
    maximo = int(det.get("max", 100))
    solo_si = re.compile(det["solo_si"]) if det.get("solo_si") else None
    nuevos, abiertos, parar, abiertas = [], 0, False, set()
    for it in res.items:
        if det.get("patrones") and it.url in abiertas:
            continue
        quiere = it.url and not parar and abiertos < maximo
        if quiere and desde and it.fecha and it.fecha < desde:
            quiere = False          # fuera de la lectura de esta ejecución
        if quiere and solo_si:
            quiere = bool(solo_si.search(f"{it.artista} – {it.titulo} {it.extra or ''}"))
        if not quiere:
            if not det.get("patrones"):
                nuevos.append(it)
            continue
        abiertos += 1
        abiertas.add(it.url)
        try:
            nuevos.extend(_detalle(nav, it, det, hoy))
        except (Bloqueado, Prohibido, ConnectionError) as e:
            res.detalle += f" detalle: {e};"
            if not det.get("patrones"):
                nuevos.append(it)
            parar = isinstance(e, Bloqueado)
    res.items = nuevos


def _txt(e, nombre):
    x = e.find(nombre)
    return x.get_text() if x else None


def leer_sonda(nav, cfg, hoy, desde=None) -> ResultadoFuente:
    res = ResultadoFuente(cfg["id"])
    for url in _urls(cfg, hoy):
        r = nav.get(url, usar_cache=False)
        res.paginas += 1
        res.detalle = f"responde HTTP {r.estado}"
    return res


LECTORES = {"texto": leer_texto, "rss": leer_rss, "sonda": leer_sonda}


def leer_fuente(nav: Navegador, cfg: dict, hoy: dt.date, desde: dt.date | None = None) -> ResultadoFuente:
    try:
        if cfg["lector"] in ("radar_musicbrainz", "radar_deezer"):
            from .config import cargar_config
            from .radar import leer_radar, leer_radar_deezer
            fn = leer_radar if cfg["lector"] == "radar_musicbrainz" else leer_radar_deezer
            res = fn(nav, cfg, hoy, desde, cargar_config())
        else:
            res = LECTORES[cfg["lector"]](nav, cfg, hoy, desde)
        if not res.items and cfg["lector"] != "sonda":
            res.estado = "vacia"
    except Bloqueado as e:
        res = ResultadoFuente(cfg["id"], "bloqueada", str(e))
    except Prohibido as e:
        res = ResultadoFuente(cfg["id"], "prohibida", str(e))
    except ConnectionError as e:
        res = ResultadoFuente(cfg["id"], "error", str(e))
    return res
