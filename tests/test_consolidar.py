"""Consolidación: duplicados que la recogida dejó separados y lo que no es un disco nuevo."""
import yaml

from scraper.consolidar import motivo_no_nuevo, unir_duplicados
from tests.conftest import RAIZ

REGLAS = yaml.safe_load(open(f"{RAIZ}/data/config.yaml", encoding="utf-8"))["consolidacion"]


def disco(id_, artista, titulo, fecha="2026-09-04", mbid=None, fuentes=1, **k):
    return {"id": id_, "artista": artista, "titulo": titulo, "fecha": fecha, "fecha_exacta": True, "mbid": mbid,
            "fuentes": [{"id": f"f{id_}{i}", "url": f"u{id_}{i}"} for i in range(fuentes)], "resenas": [],
            "etiquetas_originales": [], "enlaces": {}, **k}


def test_mismo_mbid_con_artista_escrito_distinto():
    r, n = unir_duplicados([disco("a", "Cosmic Country", "Ryman to Robert's", mbid="m1"),
                            disco("b", "Daniel Donato's Cosmic Country", "Ryman to Robert's", mbid="m1", fuentes=2)])
    assert n == 1 and len(r) == 1 and len(r[0]["fuentes"]) == 3 and r[0]["unidos"] == ["a"]


def test_erratas_y_espacios_mismo_artista_y_fechas_cercanas():
    r, n = unir_duplicados([disco("a", "Ricky Warwick", "Fire & Vengeance"), disco("b", "Ricky Warwick", "Fire & Vengence"),
                            disco("c", "Iron Savior", "Deathbringer", "2026-11-13"), disco("d", "Iron Savior", "Death Bringer", "2026-11-06")])
    assert n == 2 and len(r) == 2


def test_mismo_dia_titulo_contenido_o_muy_parecido():
    r, n = unir_duplicados([disco("a", "Pug Johnson", "A Beaumont Bar", "2026-10-23"), disco("b", "Pug Johnson", "From a Beaumont Bar", "2026-10-23"),
                            disco("c", "Kaz Murphy", "Songs of Rebellion & Redemption", "2026-09-17"),
                            disco("d", "Kaz Murphy", "Making Noise: Songs of Rebellion and Redemption", "2026-09-18")])
    assert n == 2 and len(r) == 2


def test_volumenes_distintos_el_mismo_dia_no_se_unen():
    r, n = unir_duplicados([disco("a", "Band", "Live Volume II", "2026-10-23"), disco("b", "Band", "Live Volume III", "2026-10-23"),
                            disco("c", "Band", "Part 1", "2026-10-23"), disco("d", "Band", "Part 2", "2026-10-23")])
    assert n == 0 and len(r) == 4


def test_serie_secuela_o_directo_no_se_unen():
    r, n = unir_duplicados([
        disco("a", "Jon Batiste", "Thelonious Monk: Monk Meditations (Batiste Piano Series, Vol. 3)", "2026-08-14"),
        disco("b", "Jon Batiste", "Thelonious Monk: Monk Movements (Batiste Piano Series, Vol. 4)", "2026-08-14"),
        disco("c", "Cafferty", "Eddie and the Cruisers", "2026-09-21"), disco("d", "Cafferty", "Eddie and the Cruisers II - Eddie Lives!", "2026-09-21"),
        disco("e", "Rwake", "Built From Stardust", "2026-11-13"), disco("f", "Rwake", "Built From Stardust Live in Little Rock", "2026-11-13")])
    assert n == 0 and len(r) == 6


def test_no_une_discos_distintos():
    r, n = unir_duplicados([disco("a", "Band", "Volume II"), disco("b", "Band", "Volume III"),               # títulos distintos
                            disco("c", "X", "Same", "2026-01-10"), disco("d", "X", "Same", "2026-09-10"),     # fechas lejanas
                            disco("e", "Y", "Live", mbid="m1"), disco("f", "Y", "Live", mbid="m2"),           # dos discos de MusicBrainz
                            disco("g", "Z", "Home"), disco("h", "W", "Home")])                                # otro artista
    assert n == 0 and len(r) == 8


def test_union_conserva_lo_mejor_de_cada_uno():
    a = disco("a", "A", "T", fecha="2026-09-01", sello=None, portada="p.jpg", primera_mencion="2026-08-01")
    a["fecha_exacta"] = False
    b = disco("b", "A", "T", fecha="2026-09-04", sello="Loma Vista", fuentes=2, primera_mencion="2026-07-15",
              enlaces={"deezer": "dz"})
    (r,), _ = unir_duplicados([a, b])
    assert r["sello"] == "Loma Vista" and r["portada"] == "p.jpg" and r["fecha"] == "2026-09-04"
    assert r["primera_mencion"] == "2026-07-15" and r["enlaces"] == {"deezer": "dz"}


def test_no_es_disco_nuevo():
    casos = {("Various Artists", "Felice County Fair"): True, ("Tributes", "Buffalo Rock City"): True,
             ("John Cafferty", "Eddie and the Cruisers (Original Motion Picture Soundtrack)"): True,
             ("Budgie", "Running From My Soul The MCA Years 1973-75"): True,
             ("Ian Munsick", "Untamed: The Mountain Goat Deluxe"): True,
             ("Margo Price", "Hard Headed Woman"): False, ("X", "Deluxe"): False, ("X", "The Lost Years"): False,
             ("X", "Live in 2026"): False,
             ("Eliza Carthy", "Mr Sits in the Dark (a Tribute to Martin Carthy)"): False}   # versiones nuevas de un artista
    for (art, tit), esperado in casos.items():
        assert bool(motivo_no_nuevo({"artista": art, "titulo": tit}, REGLAS)) == esperado, tit


def test_abreviaturas_y_grafias_especiales_se_unen():
    eq = {"ei8ht": "eight"}
    r, n = unir_duplicados([disco("a", "Green Carnation", "A Dark Poem, Part II: Sanguis"),
                            disco("b", "Green Carnation", "A Dark Poem, Pt. II: Sanguis"),
                            disco("c", "Jerry Joseph", "Panther Tracks Volume 2", "2026-08-24"),
                            disco("d", "Jerry Joseph", "Panther Tracks Vol. 2", "2026-07-29"),
                            disco("e", "Shinedown", "Ei8ht", "2026-05-29"), disco("f", "Shinedown", "Eight", "2026-05-29")],
                           equivalentes=eq)
    assert n == 3 and len(r) == 3


def test_titulo_identico_admite_fechas_mas_lejanas_pero_no_sin_limite():
    a = disco("a", "Albert Bouchard", "Imaginos IV: Rhyme of the Starclock", "2026-09-25")
    b = disco("b", "Albert Bouchard", "Imaginos IV - Rhyme of the Star Clock", "2026-08-06")      # 50 días
    assert unir_duplicados([a, b])[1] == 1
    c = disco("c", "Band", "Same Name", "2026-01-10")
    d = disco("d", "Band", "Same Name", "2026-11-20")                                           # 314 días: otro disco
    assert unir_duplicados([c, d])[1] == 0
    e = disco("e", "Band", "Almost the Same Name", "2026-01-10")
    f = disco("f", "Band", "Almost the Same Name!", "2026-04-10")                                # 90 días, igual
    assert unir_duplicados([e, f])[1] == 1
    g = disco("g", "Gnod", "Chronicles of Gnowt (Vol 2)", "2026-10-09")
    h = disco("h", "Gnod", "Chronicles of Gnowt (Vol 1)", "2026-04-10")
    assert unir_duplicados([g, h])[1] == 0                                                      # volúmenes distintos


def test_titulares_de_noticia_no_son_discos():
    assert motivo_no_nuevo({"artista": "Twisted Teens", "titulo": "Watch the Video for “Florida Water Blues"}, REGLAS)
    assert motivo_no_nuevo({"artista": "The Wild High", "titulo": "Listen to The Wild High"}, REGLAS)
    assert motivo_no_nuevo({"artista": "New Found Glory", "titulo": "Listen Up!"}, REGLAS) is None
    assert motivo_no_nuevo({"artista": "Mega Colossus", "titulo": "Watch Out!"}, REGLAS) is None


def test_ediciones_ampliadas_de_un_disco_anterior():
    from scraper.consolidar import ampliaciones
    l = [disco("a", "Jackson Dean", "Magnolia Sage", "2026-04-24"),
         disco("b", "Jackson Dean", "Magnolia Sage (In Full Bloom)", "2026-10-09"),
         disco("c", "Albert Bouchard", "Imaginos", "2026-01-10"),
         disco("d", "Albert Bouchard", "Imaginos IV", "2026-09-25"),               # otra parte: disco nuevo
         disco("e", "Band", "Night", "2026-03-01"), disco("f", "Band", "Night Live", "2026-09-01"),  # directo: otro disco
         disco("g", "Other", "Sun", "2026-05-01"), disco("h", "Other", "Sun Rising", "2026-05-10")]  # 9 días: no
    r = ampliaciones(l)
    assert list(r) == [1] and "Magnolia Sage" in r[1]


def test_la_fuente_lo_etiqueta_como_reedicion_o_caja():
    assert "Box sets" in motivo_no_nuevo({"artista": "Rainbow", "titulo": "Live In Koln",
                                           "etiquetas_originales": ["ALBUM REVIEWS", "Box sets"]}, REGLAS)
    assert motivo_no_nuevo({"artista": "X", "titulo": "Y", "etiquetas_originales": ["Reviews", "reissue culture"]}, REGLAS) is None


def test_mismo_artista_escrito_con_and_the_o_ampersand():
    from scraper.util import clave_nombre
    assert clave_nombre("Neil Young & The Chrome Hearts") == clave_nombre("Neil Young & Chrome Hearts") == clave_nombre("neil-young-and-the-chrome-hearts")
    assert clave_nombre("Echo and the Bunnymen") == clave_nombre("echo-the-bunnymen") and clave_nombre("The The") != ""
    r, n = unir_duplicados([disco("a", "Neil Young & The Chrome Hearts", "Second Song", "2026-09-18"),
                            disco("b", "Neil Young & Chrome Hearts", "Second Song", "2026-09-18")])
    assert n == 1 and len(r) == 1
