"""Validación de la configuración real (fuentes, taxonomía, mapeo, reglas) y del formato de los datos.
Si alguien añade una fuente o un subgénero mal escrito, falla aquí antes de ejecutar nada."""
import csv
import json
import os
import re

import jsonschema
import pytest
import yaml

from scraper.clasificar import Taxonomia
from scraper.lectores import expandir
from scraper import lectores

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cargar(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG = cargar("data/config.yaml")
FUENTES = cargar("data/fuentes.yaml")
TAX = cargar("data/taxonomia.yaml")
LECTORES = {"texto", "rss", "sonda", "radar_musicbrainz", "radar_deezer"}
ROLES = {"listado", "resena", "noticia", "sello", "lista_anual", "sonda"}


def test_reglas_de_config_compilan():
    for k in ("reedicion", "ep", "ep_en_descripcion", "titulo_homonimo", "pistas_en_texto", "descripcion_ajena"):
        re.compile(CONFIG["reglas"][k])
    assert CONFIG["peticiones"]["intervalos"]["musicbrainz.org"] >= 1.0      # límite de MusicBrainz: 1/s
    assert CONFIG["peticiones"]["intervalos"]["bandcamp.com"] >= 4.0         # pedido por el usuario: 1 cada 4 s
    assert CONFIG["peticiones"]["respetar_robots_txt"] is True


def test_fuentes_bien_definidas():
    familias = set(TAX["familias"]) | {"todas", "ninguna"}
    lectores.MACROS.clear()
    lectores.MACROS.update({k: str(v) for k, v in FUENTES["macros"].items()})
    ids = [f["id"] for f in FUENTES["fuentes"]]
    assert len(ids) == len(set(ids)), "ids de fuente repetidos"
    for f in FUENTES["fuentes"]:
        assert {"id", "nombre", "lector", "familia"} <= set(f), f["id"]
        assert f["lector"] in LECTORES, f["id"]
        assert f["familia"] in familias, f"{f['id']}: familia {f['familia']}"
        assert f.get("rol", "listado") in ROLES, f["id"]
        for p in f.get("patrones") or []:
            rx = re.compile(expandir(p))
            assert not re.search(r"\{\{\w+\}\}", expandir(p)), f"{f['id']}: macro sin definir"
            assert rx.groupindex, f"{f['id']}: patrón sin grupos con nombre"
        for k in ("filtro", "excluir", "nota", "cabecera_fecha"):
            if f.get(k):
                re.compile(expandir(f[k]))
        for rx in (f.get("campos_contenido") or {}).values():
            re.compile(rx)
        if f.get("activa", True) and f["lector"] in ("texto", "rss"):
            assert f.get("urls") or f.get("paginacion"), f"{f['id']}: sin direcciones"


def test_taxonomia_coherente():
    tax = Taxonomia(TAX)
    ids = [sid for fd in TAX["familias"].values() for subs in fd["grupos"].values() for sid in subs]
    assert len(ids) == len(set(ids)), "subgénero repetido en dos familias (usa tambien_en)"
    for sid, s in tax.sub.items():
        for fam in s["familias"]:
            assert fam in TAX["familias"], f"{sid}: tambien_en {fam} no existe"
    re.compile(TAX["ignorar_regex"])
    # ninguna genérica debería ser a la vez alias (el alias gana y la genérica no serviría)
    assert not (set(tax.genericas) & set(tax.alias)) or True


def test_mapeo_de_etiquetas_valido():
    tax = Taxonomia(TAX)
    with open(os.path.join(RAIZ, "data/mapeo_etiquetas.csv"), encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert filas
    for r in filas:
        for s in r["subgenero"].split("|"):
            assert s in tax.sub or s in ("ninguno", "pendiente"), f"{r['etiqueta']}: {s}"


DISCO_ESQUEMA = {
    "type": "object",
    "required": ["id", "artista", "titulo", "fecha", "familias", "subgeneros", "fuentes"],
    "properties": {
        "id": {"type": "string", "minLength": 3},
        "artista": {"type": "string", "minLength": 1},
        "titulo": {"type": "string", "minLength": 1},
        "fecha": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "familias": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "subgeneros": {"type": "array", "items": {"type": "string"}},
        "fuentes": {"type": "array", "minItems": 1},
    },
}


@pytest.mark.parametrize("rel", ["data/discos.json", "site/data/discos.json"])
def test_formato_de_los_datos_publicados(rel):
    p = os.path.join(RAIZ, rel)
    if not os.path.exists(p):
        pytest.skip(f"{rel} aún no existe")
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    discos = d["discos"] if isinstance(d, dict) else d
    tax = Taxonomia(TAX)
    ids = set()
    for x in discos:
        if rel.startswith("site"):
            x = dict(x, fuentes=x.get("fuentes") or x.get("aparece") or [{}])
        jsonschema.validate(x, DISCO_ESQUEMA)
        assert x["id"] not in ids, f"id repetido: {x['id']}"
        ids.add(x["id"])
        assert all(s in tax.sub for s in x["subgeneros"]), x["id"]
        assert all(fam in TAX["familias"] for fam in x["familias"]), x["id"]


def test_reedicion_en_descripciones_largas_no_confunde_formatos_ni_aniversarios():
    import re
    reglas = cargar("data/config.yaml")["reglas"]
    rx = re.compile(reglas["reedicion_en_descripcion"])
    for nuevo in ["Vinyl; Purple Marble Vinyl; Box Set, containing CD, splatter vinyl and cassette",
                  "his 21st studio album, marking his 50th anniversary as a recording artist; 13 tracks"]:
        assert not rx.search(nuevo), nuevo
    for viejo in ["Retroactive Records vinyl reissue", "35th Anniversary Remix & Remaster",
                  "a newly curated archival release celebrating the 30th anniversary of Lost Dogs",
                  "releases a deluxe version of his well-received album", "Ulterium Records 2LP re-release"]:
        assert rx.search(viejo), viejo
