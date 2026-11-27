"""Servicios externos sin red: MusicBrainz, Bandcamp, Deezer, iTunes y el radar, con respuestas
de ejemplo. Escenarios: coincidencia, homónimos, sin resultado, caché, red caída, bloqueo, límites."""
import datetime as dt
import json

import pytest

from scraper.bandcamp import Bandcamp
from scraper.enriquecer import Extras
from scraper.http import Bloqueado, Respuesta
from scraper.musicbrainz import MusicBrainz
from scraper.radar import TOPE, _paginas, _trozos_mensuales


class Nav:
    """Responde según una función url → valor (texto, (estado, texto), dict→JSON o excepción)."""

    def __init__(self, fn):
        self.fn, self.pedidas = fn, []

    def get(self, url, usar_cache=True, acepta=None):
        self.pedidas.append(url)
        v = self.fn(url)
        if isinstance(v, Exception):
            raise v
        if v is None:
            return Respuesta(url, 404, "")
        if isinstance(v, tuple):
            return Respuesta(url, v[0], v[1])
        return Respuesta(url, 200, v if isinstance(v, str) else json.dumps(v))


def rg(id_, titulo, artista, fecha="2026-10-03", tipo="Album", sec=()):
    return {"id": id_, "title": titulo, "primary-type": tipo, "secondary-types": list(sec), "first-release-date": fecha,
            "artist-credit": [{"name": artista, "artist": {"id": "a-" + artista.lower()}}]}


# ------------------------------------------------------------------ MusicBrainz
def mb(tmp_path, fn):
    return MusicBrainz(Nav(fn), str(tmp_path / "mb.json"), 0.86, dias_reintento=10)


def test_mb_elige_la_coincidencia_y_descarta_parecidos(tmp_path):
    m = mb(tmp_path, lambda u: {"release-groups": [rg("x", "Hard Headed", "Margo Price"),
                                                   rg("ok", "Hard Headed Woman", "Margo Price"),
                                                   rg("y", "Hard Headed Woman", "Margot Prize Tribute Band")]}
           if "release-group" in u else {"releases": []})
    r = m.buscar("Margo Price", "Hard Headed Woman", completar=False)
    assert r["rg"] == "ok" and r["primera_fecha"] == "2026-10-03"


def test_mb_sin_resultado_se_recuerda_y_se_reintenta_pasados_n_dias(tmp_path):
    m = mb(tmp_path, lambda u: {"release-groups": []})
    assert m.buscar("Nadie", "Nada") is None
    n = len(m.nav.pedidas)
    assert m.buscar("Nadie", "Nada") is None and len(m.nav.pedidas) == n          # no repite
    clave = next(iter(m.cache))
    m.cache[clave]["no_encontrado"] = (dt.date.today() - dt.timedelta(days=11)).isoformat()
    m.buscar("Nadie", "Nada")
    assert len(m.nav.pedidas) > n                                                  # pasados 10 días, sí


def test_mb_red_caida_no_se_guarda_como_no_encontrado(tmp_path):
    m = mb(tmp_path, lambda u: ConnectionError("timeout"))
    assert m.buscar("A", "B") is None and not m.cache


def test_mb_bloqueo_para_las_consultas(tmp_path):
    m = mb(tmp_path, lambda u: Bloqueado("musicbrainz.org: 403"))
    assert m.buscar("A", "B") is None and m.bloqueado
    n = len(m.nav.pedidas)
    m.buscar("C", "D")
    assert len(m.nav.pedidas) == n


def test_mb_intercambiable_prueba_artista_y_titulo_al_reves(tmp_path):
    m = mb(tmp_path, lambda u: {"release-groups": [rg("ok", "Pieces", "Ian Noe")]} if "Pieces" in u and "Ian" in u
           and u.index("Pieces") < u.index("Ian") else {"release-groups": []})
    assert m.buscar("Pieces", "Ian Noe", intercambiable=True, completar=False)["rg"] == "ok"


def test_mb_detalles_idioma_sello_pistas_enlaces_portada(tmp_path):
    rels = {"releases": [
        {"id": "r2", "status": "Official", "date": "2026-10-10", "text-representation": {"language": "eng"},
         "label-info": [{"label": {"name": "Tardío"}}], "media": [{"track-count": 3}]},
        {"id": "r1", "status": "Official", "date": "2026-10-03", "country": "US", "text-representation": {"language": "eng"},
         "label-info": [{"label": {"name": "Loma Vista"}}], "media": [{"track-count": 10}, {"track-count": 2}],
         "relations": [{"url": {"resource": "https://margoprice.bandcamp.com/album/hhw"}}],
         "cover-art-archive": {"front": True}},
        {"id": "r3", "status": "Bootleg", "date": "2026-01-01", "text-representation": {"language": "deu"}}]}
    m = mb(tmp_path, lambda u: {"release-groups": [rg("ok", "Hard Headed Woman", "Margo Price")]} if "release-group/" in u else rels)
    r = m.buscar("Margo Price", "Hard Headed Woman")
    assert (r["release"], r["idioma"], r["sellos"], r["pistas"]) == ("r1", "eng", ["Loma Vista"], 12)
    assert r["enlaces"]["bandcamp"].endswith("/album/hhw") and r["portada"].endswith("ok/front-250")


def test_mb_artista_generos_ordenados_y_cacheados(tmp_path):
    m = mb(tmp_path, lambda u: {"name": "Margo Price", "genres": [{"name": "americana", "count": 2}, {"name": "country", "count": 9}],
                                "tags": [{"name": "outlaw", "count": 3}, {"name": "spam", "count": 0}]})
    a = m.artista("abc")
    assert a["generos"] == ["country", "americana"] and a["etiquetas"] == ["outlaw"]
    m.artista("abc")
    assert len(m.nav.pedidas) == 1


# ------------------------------------------------------------------ Bandcamp
LD = '<script type="application/ld+json">{"name": "Hard Headed Woman", "byArtist": {"name": "Margo Price"}, ' \
     '"datePublished": "03 Oct 2026", "numTracks": 12, "keywords": "americana, country, Nashville", ' \
     '"image": ["https://f4.bcbits.com/img/a1_10.jpg"], "publisher": {"name": "Loma Vista"}}</script>'


def test_bandcamp_disco_directo(tmp_path):
    bc = Bandcamp(Nav(lambda u: LD), str(tmp_path / "bc.json"))
    d = bc.disco("Hard Headed Woman", "https://margo.bandcamp.com/album/hhw", None)
    assert d["pistas"] == 12 and d["etiquetas"] == ["americana", "country", "Nashville"] and d["sello"] == "Loma Vista"
    bc.disco("Hard Headed Woman", "https://margo.bandcamp.com/album/hhw", None)
    assert bc.abiertas == 1                                                  # caché


def test_bandcamp_por_pagina_de_artista(tmp_path):
    musica = '<a href="/album/otra-cosa">Otra cosa</a><a href="/album/hard-headed-woman"><p>Hard Headed Woman</p></a>'
    bc = Bandcamp(Nav(lambda u: musica if u.endswith("/music") else LD), str(tmp_path / "bc.json"))
    d = bc.disco("Hard Headed Woman", None, "https://margo.bandcamp.com")
    assert d["titulo"] == "Hard Headed Woman"
    assert bc.nav.pedidas == ["https://margo.bandcamp.com/music", "https://margo.bandcamp.com/album/hard-headed-woman"]


def test_bandcamp_sin_coincidencia_no_abre_nada_mas(tmp_path):
    bc = Bandcamp(Nav(lambda u: '<a href="/album/x">Algo distinto</a>'), str(tmp_path / "bc.json"))
    assert bc.disco("Hard Headed Woman", None, "https://margo.bandcamp.com") is None
    assert bc.nav.pedidas == ["https://margo.bandcamp.com/music"]


def test_bandcamp_bloqueo_y_limite(tmp_path):
    bc = Bandcamp(Nav(lambda u: Bloqueado("bandcamp.com: Client Challenge")), str(tmp_path / "bc.json"))
    assert bc.disco("T", "https://a.bandcamp.com/album/t", None) is None and bc.bloqueado
    bc2 = Bandcamp(Nav(lambda u: LD), str(tmp_path / "bc2.json"), maximo=1)
    bc2.disco("T", "https://a.bandcamp.com/album/t", None)
    assert bc2.disco("U", "https://a.bandcamp.com/album/u", None) is None and bc2.abiertas == 1


def test_bandcamp_pagina_sin_datos_estructurados(tmp_path):
    bc = Bandcamp(Nav(lambda u: "<html>sin json-ld</html>"), str(tmp_path / "bc.json"))
    assert bc.disco("T", "https://a.bandcamp.com/album/t", None) is None


# ------------------------------------------------------------------ Deezer e iTunes
def test_deezer_tipo_y_umbral(tmp_path):
    ex = Extras(Nav(lambda u: {"data": [
        {"id": 1, "title": "Hard Headed Woman (Single)", "artist": {"name": "Margo Price"}, "record_type": "single"},
        {"id": 2, "title": "Hard Headed Woman", "artist": {"name": "Margo Price"}, "record_type": "album", "nb_tracks": 12,
         "link": "https://www.deezer.com/album/2", "cover_medium": "c250", "cover_xl": "c1000"}]}), {}, str(tmp_path / "x.json"))
    d = ex.deezer("Margo Price", "Hard Headed Woman")
    assert (d["id"], d["tipo"], d["pistas"], d["portada_grande"]) == (2, "album", 12, "c1000")


def test_itunes_genero_y_servicio_bloqueado(tmp_path):
    ex = Extras(Nav(lambda u: {"results": [{"collectionName": "Pieces", "artistName": "Ian Noe", "primaryGenreName": "Country",
                                            "trackCount": 11, "releaseDate": "2026-09-05T07:00:00Z"}]}), {}, str(tmp_path / "x.json"))
    assert ex.itunes("Ian Noe", "Pieces") == {"url": None, "genero": "Country", "pistas": 11, "fecha": "2026-09-05"}
    ex2 = Extras(Nav(lambda u: Bloqueado("itunes: 403")), {}, str(tmp_path / "y.json"))
    assert ex2.itunes("A", "B") == {} and "itunes" in ex2.bloqueos
    ex2.itunes("C", "D")
    assert len(ex2.nav.pedidas) == 1                                         # no insiste en un servicio bloqueado


# ------------------------------------------------------------------ radar de MusicBrainz
def test_trozos_mensuales_cubren_todo_sin_huecos():
    t = list(_trozos_mensuales(dt.date(2026, 1, 15), dt.date(2026, 4, 3)))
    assert t[0][0] == dt.date(2026, 1, 15) and t[-1][1] == dt.date(2026, 4, 3)
    assert all(b + dt.timedelta(days=1) == c for (_, b), (c, _) in zip(t, t[1:]))
    assert t[1] == (dt.date(2026, 2, 1), dt.date(2026, 2, 28))


def test_radar_divide_el_tramo_si_pasa_del_tope():
    def fn(u):
        n = 700 if "2026-03-01%20TO%202026-03-31" in u else 150
        return {"count": n, "release-groups": [{"id": u[-12:]}]}
    nav = Nav(fn)
    filas = _paginas(nav, dt.date(2026, 3, 1), dt.date(2026, 3, 31), "primarytype:album")
    assert len(nav.pedidas) == 1 + 2 * 2          # tramo entero (700 > 500) → dos mitades de 150 (2 páginas cada una)
    assert len(filas) == 4 and TOPE == 500
