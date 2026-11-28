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
