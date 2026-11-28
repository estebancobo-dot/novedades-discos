"""Validación automática: cada requisito tiene comprobaciones que existen, y el motor corre sobre los datos."""
import yaml

from scraper import validar
from tests.conftest import RAIZ


def test_cada_comprobacion_nombrada_existe():
    reqs = yaml.safe_load(open(f"{RAIZ}/data/requisitos.yaml", encoding="utf-8"))["requisitos"]
    assert len(reqs) >= 140 and len({r["id"] for r in reqs}) == len(reqs)
    faltan = [(r["id"], n) for r in reqs for n in r["comprobaciones"]
              if not n.startswith("web:") and n not in validar.COMPROBACIONES]
    assert not faltan, faltan


def test_el_motor_da_estado_a_todos_los_requisitos():
    salida, _ = validar.ejecutar()
    assert set(salida["requisitos"]) and all(v["estado"] in validar.ORDEN for v in salida["requisitos"].values())
    assert sum(salida["totales"].values()) == len(salida["requisitos"])
    assert all("estado" in r for r in salida["comprobaciones"].values())


def test_una_comprobacion_rota_no_tumba_las_demas(monkeypatch):
    monkeypatch.setitem(validar.COMPROBACIONES, "rota", lambda c: 1 / 0)
    salida, _ = validar.ejecutar()
    assert salida["comprobaciones"]["rota"]["estado"] == "fallo" and "ZeroDivisionError" in salida["comprobaciones"]["rota"]["detalle"]
    assert salida["comprobaciones"]["taxonomia_valida"]["estado"] in validar.ORDEN


def test_clave_de_referencias_iguala_grafias():
    from scraper.referencias import clave
    assert clave("THE ROLLING STONES") == clave("the-rolling-stones")
    assert clave("o\\i") == clave("oi") and clave("Echo & the Bunnymen") == clave("echo-the-bunnymen")
    assert clave("Trentemøller") != ""


def test_descubrimiento_cuenta_perdidos_frente_a_la_referencia(monkeypatch, tmp_path):
    import json
    ref = {"referencias": {"m": {"nombre": "M", "estado": "ok", "items":
           [{"artista": "a", "titulo": "t", "resultado": "en_web"}] * 9 + [{"artista": "b", "titulo": "u", "resultado": "perdido", "generos": ["folk"]}]}}}
    real = validar._leer
    monkeypatch.setattr(validar, "_leer", lambda rel, d=None: ref if rel == "data/referencias.json" else real(rel, d))
    c = validar.Contexto()
    r = validar.descubrimiento_referencias(c)
    assert r["estado"] == "ok" and "perdidos 1 (10.0 %)" in r["detalle"] and r["ejemplos"][0].startswith("perdido: b")
    ref["referencias"]["m"]["items"] += [{"artista": "c", "titulo": "v", "resultado": "perdido"}]
    assert validar.descubrimiento_referencias(c)["estado"] == "fallo"
