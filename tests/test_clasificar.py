"""Clasificación: alias, genéricas, mapeo, ignoradas, frontera, varias familias."""
from collections import Counter

from scraper.clasificar import Taxonomia, clasificar_disco

TAX = {
    "reglas": {"max_subgeneros": 3, "alias_en_texto_min_palabras": 2},
    "ignorar": ["vinyl"],
    "ignorar_regex": r"(?i)\b(album reviews?|news)\b",
    "familias": {
        "country": {"genericas": ["country"], "grupos": {"g": {
            "outlaw-country": {"nombre": "Outlaw", "alias": ["outlaw"]},
            "americana": {"nombre": "Americana", "alias": ["roots"]},
            "southern-rock": {"nombre": "Southern rock", "frontera": True, "tambien_en": ["hardrock"]},
        }}},
        "hardrock": {"genericas": ["hard rock"], "grupos": {"g": {
            "aor": {"nombre": "AOR", "alias": ["melodic rock"]},
        }}},
    },
}


def disco(**k):
    base = {"artista": "A", "titulo": "T", "etiquetas_originales": [], "etiquetas_musicbrainz_bandcamp": [],
            "etiquetas_extra": [], "descripciones": []}
    base.update(k)
    return base


def clasificar(d, mapeo=None):
    tax, desconocidas, ej = Taxonomia(TAX), Counter(), {}
    r = clasificar_disco(d, tax, mapeo or {}, desconocidas, ej)
    return r, desconocidas


def test_alias_y_peso_por_origen():
    r, _ = clasificar(disco(etiquetas_originales=["Outlaw"], etiquetas_musicbrainz_bandcamp=["americana", "roots"]))
    assert r["subgeneros"][:2] == ["americana", "outlaw-country"] or set(r["subgeneros"]) >= {"americana", "outlaw-country"}


def test_etiquetas_compuestas_se_trocean():
    r, _ = clasificar(disco(etiquetas_originales=["Outlaw / Americana"]))
    assert set(r["subgeneros"]) == {"outlaw-country", "americana"}


def test_generica_da_familia_sin_subgenero():
    r, _ = clasificar(disco(etiquetas_originales=["Country"]))
    assert r["subgeneros"] == [] and r["familias_genericas"] == ["country"]


def test_mapeo_del_llm_o_wikidata():
    mapeo = {"yacht rock": {"subgenero": "aor"}, "cosas": {"subgenero": "ninguno"}, "x": {"subgenero": "pendiente"}}
    r, desconocidas = clasificar(disco(etiquetas_originales=["Yacht Rock", "cosas", "x"]), mapeo)
    assert r["subgeneros"] == ["aor"]
    assert "x" in desconocidas and "cosas" not in desconocidas


def test_ignoradas_y_regex_no_cuentan_como_pendientes():
    r, desconocidas = clasificar(disco(etiquetas_originales=["Vinyl", "Album Reviews", "News 2026"]))
    assert r["subgeneros"] == [] and not desconocidas


def test_alias_en_descripcion_solo_si_tiene_varias_palabras():
    r, _ = clasificar(disco(descripciones=["A big slice of melodic rock with roots in the 80s"]))
    assert "aor" in r["subgeneros"]            # "melodic rock" (2 palabras) sí
    assert "americana" not in r["subgeneros"]   # "roots" (1 palabra) no, demasiado ambiguo en texto libre


def test_maximo_de_subgeneros():
    r, _ = clasificar(disco(etiquetas_originales=["outlaw", "americana", "melodic rock", "southern rock"]))
    assert len(r["subgeneros"]) == 3


def test_subgenero_en_varias_familias():
    tax = Taxonomia(TAX)
    assert tax.sub["southern-rock"]["familias"] == ["country", "hardrock"]
    assert tax.sub["southern-rock"]["frontera"]


def test_disco_sin_nada():
    r, desconocidas = clasificar(disco())
    assert r == {"subgeneros": [], "familias_genericas": [], "familias_suman": []} and not desconocidas


def test_categoria_amplia_de_discogs_no_se_trocea_y_genericas_que_suman():
    from collections import Counter
    from scraper.clasificar import Taxonomia, clasificar_disco
    from scraper.config import cargar_yaml
    from tests.conftest import RAIZ
    tax = Taxonomia(cargar_yaml(f"{RAIZ}/data/taxonomia.yaml"))
    d = {"artista": "Morgan Myles", "titulo": "Laced", "etiquetas_extra": [{"etiqueta": "Folk, World, & Country", "origen": "discogs"}]}
    r = clasificar_disco(d, tax, {}, Counter(), {})
    assert r["subgeneros"] == [] and r["familias_genericas"] == []       # ni "contemporary folk" ni country: no dice el género
    d = {"artista": "A", "titulo": "B", "etiquetas_originales": ["soul blues", "Blues"]}
    assert "blues" in clasificar_disco(d, tax, {}, Counter(), {})["familias_suman"]
    d = {"artista": "A", "titulo": "B", "etiquetas_musicbrainz_bandcamp": ["x", "y", "z", "blues"]}   # peso débil
    assert clasificar_disco(d, tax, {}, Counter(), {})["familias_suman"] == []


def test_familia_por_defecto_de_fuente_mixta_solo_sin_genero_ajeno():
    from scraper.clasificar import Taxonomia, _sin_genero_ajeno
    from scraper.config import cargar_yaml
    from tests.conftest import RAIZ
    tax = Taxonomia(cargar_yaml(f"{RAIZ}/data/taxonomia.yaml"))
    r = {"familias_genericas": []}
    assert _sin_genero_ajeno({"etiquetas_originales": ["Album Reviews", "Bobby Murray"]}, tax, r)      # solo músicos
    assert not _sin_genero_ajeno({"etiquetas_musicbrainz_bandcamp": ["soul", "funk"]}, tax, r)        # soul: no
    assert _sin_genero_ajeno({"etiquetas_musicbrainz_bandcamp": ["soul", "blues"]}, tax, {"familias_genericas": ["blues"]})
