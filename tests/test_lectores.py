"""Lectores de fuentes (RSS y páginas) con páginas de ejemplo, sin red."""
import datetime as dt

from scraper import lectores
from scraper.lectores import _urls, leer_fuente

RSS = """<?xml version="1.0"?><rss><channel>
<item><title>Margo Price – Hard Headed Woman | Album Review</title><link>https://x.example/1</link>
 <pubDate>Fri, 20 Nov 2026 10:00:00 +0000</pubDate><category>Americana</category>
 <description>Rating: 8/10. Category: Country / Americana Label: Loma Vista Release Date: 2026-11-13</description></item>
<item><title>Some Band – Old Record (Reissue) | Album Review</title><link>https://x.example/2</link>
 <pubDate>Thu, 19 Nov 2026 10:00:00 +0000</pubDate></item>
<item><title>Interview with a producer</title><link>https://x.example/3</link>
 <pubDate>Wed, 18 Nov 2026 10:00:00 +0000</pubDate></item>
<item><title>Margo Price – Hard Headed Woman | Album Review</title><link>https://x.example/1</link>
 <pubDate>Fri, 20 Nov 2026 10:00:00 +0000</pubDate></item>
</channel></rss>"""

RSS_VIEJO = """<?xml version="1.0"?><rss><channel>
<item><title>Old Artist – Old Album | Album Review</title><link>https://x.example/9</link>
 <pubDate>Mon, 05 Jan 2026 10:00:00 +0000</pubDate></item></channel></rss>"""


def cfg_rss(**extra):
    c = {"id": "prueba", "nombre": "Prueba", "lector": "rss", "rol": "resena", "familia": "country",
         "urls": ["https://x.example/feed"],
         "patrones": [r"^(?P<artista>.+?)\s+[–-]\s+(?P<titulo>.+?)\s*\|\s*Album Review\s*$"]}
    c.update(extra)
    return c


def test_rss_nominal_campos_nota_y_duplicados(nav_falso, hoy):
    nav = nav_falso({"https://x.example/feed": RSS})
    cfg = cfg_rss(excluir=r"(?i)reissue", nota=r"(?P<nota>\d+/10)",
                  campos_contenido={"genero": r"Category:\s*(?P<genero>.+?)\s+Label:",
                                    "sello": r"Label:\s*(?P<sello>.+?)\s+Release Date:",
                                    "fecha": r"Release Date:\s*(?P<fecha>\d{4}-\d{2}-\d{2})"})
    res = leer_fuente(nav, cfg, hoy)
    assert res.estado == "ok"
    assert len(res.items) == 1                       # reedición excluida, entrevista sin patrón, duplicado una vez
    it = res.items[0]
    assert (it.artista, it.titulo) == ("Margo Price", "Hard Headed Woman")
    assert it.nota == "8/10"
    assert it.sello == "Loma Vista"
    assert it.genero == "Country / Americana"
    assert it.fecha == dt.date(2026, 11, 13) and it.fecha_tipo == "lanzamiento"   # fecha de salida, no de publicación
    assert it.fecha_publicacion == dt.date(2026, 11, 20)
    assert "Americana" in it.etiquetas


def test_rss_paginado_para_al_llegar_a_lo_antiguo(nav_falso, hoy):
    nav = nav_falso({"https://x.example/feed": RSS, "https://x.example/feed?p=2": RSS_VIEJO,
                     "https://x.example/feed?p=3": RSS})
    cfg = cfg_rss(paginacion={"plantilla": "https://x.example/feed?p={n}", "desde": 2, "hasta": 3})
    res = leer_fuente(nav, cfg, hoy, desde=dt.date(2026, 6, 1))
    assert "https://x.example/feed?p=3" not in nav.pedidas     # la página 2 ya era toda antigua


def test_rss_vacio_o_roto_queda_vacia(nav_falso, hoy):
    for contenido in ["<rss><channel></channel></rss>", "esto no es xml <<<", ""]:
        res = leer_fuente(nav_falso({"https://x.example/feed": contenido}), cfg_rss(), hoy)
        assert res.estado == "vacia" and res.items == []


def test_rss_404_queda_vacia(nav_falso, hoy):
    res = leer_fuente(nav_falso({}), cfg_rss(), hoy)
    assert res.estado == "vacia"


def test_errores_de_red_bloqueo_y_robots(nav_falso, hoy, excepciones):
    for clave_exc, estado in [("bloqueado", "bloqueada"), ("prohibido", "prohibida"), ("conexion", "error")]:
        nav = nav_falso({"https://x.example/feed": excepciones[clave_exc]})
        res = leer_fuente(nav, cfg_rss(), hoy)
        assert res.estado == estado, clave_exc
        assert res.items == []


PAGINA = """<html><body><h2>Friday, November 13</h2>
<p>Margo Price – <em>Hard Headed Woman</em> (Loma Vista)</p>
<p>Colter Wall – <em>Memories and Empties</em></p>
<h2>Friday, November 20</h2>
<p>Ian Noe – <em>Pieces</em></p></body></html>"""


def test_texto_con_cabeceras_de_fecha_y_macros(nav_falso, hoy):
    lectores.MACROS.update({"ART": r"(?P<artista>[^–«\n]+?)"})
    cfg = {"id": "listado", "nombre": "L", "lector": "texto", "rol": "listado", "familia": "country",
           "urls": ["https://x.example/lista"], "fecha_es": "lanzamiento",
           "texto": {"marcas": {"em": "«»"}},
           "cabecera_fecha": r"^##\s*(?P<fecha>\w+, \w+ \d+)$",
           "patrones": [r"^{{ART}}\s+–\s+«(?P<titulo>[^»]+)»(?:\s+\((?P<sello>[^)]+)\))?"]}
    cfg["texto"]["marcas"]["h2"] = ["## ", ""]
    res = leer_fuente(nav_falso({"https://x.example/lista": PAGINA}), cfg, hoy)
    por = {(i.artista, i.titulo): i for i in res.items}
    assert por[("Margo Price", "Hard Headed Woman")].fecha == dt.date(2026, 11, 13)
    assert por[("Margo Price", "Hard Headed Woman")].sello == "Loma Vista"
    assert por[("Ian Noe", "Pieces")].fecha == dt.date(2026, 11, 20)
    assert len(res.items) == 3


def test_urls_por_anios_hasta_actual_y_anterior(hoy):
    base = {"paginacion": {"anios": {"plantilla": "https://x.example/{anio}", "desde": 2024}}}
    assert _urls(base, hoy) == ["https://x.example/2024", "https://x.example/2025", "https://x.example/2026"]
    base["paginacion"]["anios"]["hasta"] = "anterior"        # solo años cerrados
    assert _urls(base, hoy) == ["https://x.example/2024", "https://x.example/2025"]
    base["paginacion"]["anios"].update({"hasta": 2024, "paginas": 2, "plantilla_pagina": "https://x.example/{anio}/p{n}"})
    assert _urls(base, hoy) == ["https://x.example/2024", "https://x.example/2024/p2"]
