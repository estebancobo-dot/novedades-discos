"""Notas, portadas, lecturas guardadas (reanudar), orquestador de fases y mapeo con Wikidata."""
import datetime as dt
import json
import os

import pytest

from scraper import pipeline
from scraper.clasificar import Taxonomia
from scraper.lectores import Item, ResultadoFuente
from scraper.mapear import resolver
from scraper.recoger import _fecha_mb, _fin_periodo, _huella, cargar_lectura, guardar_lectura
from scraper.web import _portadas, nota_10, version_2x


# ------------------------------------------------------------------ notas y portadas
@pytest.mark.parametrize("texto,esperado", [
    ("8/10", 8.0), ("7.5 / 10", 7.5), ("4/5", 8.0), ("3.5/5", 7.0), ("85%", 8.5), ("17/20", None),
    ("9", None), ("11/10", None), (None, None), ("", None), ("8,5/10", 8.5),
])
def test_nota_10(texto, esperado):
    assert nota_10(texto) == esperado


def test_portadas_tamanos_y_respaldo():
    assert _portadas("https://coverartarchive.org/release-group/x/front-250", None)[1].endswith("front-500")
    assert _portadas(None, {"portada": "dz250", "portada_grande": "dz1000"}) == ("dz250", "dz1000")
    assert _portadas("https://coverartarchive.org/release-group/x/front-250", {"portada": "dz250"})[0] == "dz250"   # Deezer primero
    assert _portadas(None, None) == (None, None)
    peq, gra = _portadas("https://f4.bcbits.com/img/a123_10.jpg", None)
    assert peq.endswith("_2.jpg") and gra.endswith("_16.jpg")


# ------------------------------------------------------------------ fechas de MusicBrainz
def test_fechas_mb_parciales():
    assert _fecha_mb("2026-09-25") == (dt.date(2026, 9, 25), True)
    assert _fecha_mb("2026-09") == (dt.date(2026, 9, 1), False)
    assert _fecha_mb("2026") == (dt.date(2026, 1, 1), False)
    assert _fecha_mb("raro") == (None, False) and _fecha_mb(None) == (None, False)
    assert _fin_periodo("2026") == dt.date(2026, 12, 31)
    assert _fin_periodo("2026-02") == dt.date(2026, 2, 28)
    assert _fin_periodo("2026-12") == dt.date(2026, 12, 31)


# ------------------------------------------------------------------ lecturas guardadas
def _res():
    it = Item(fuente="f", artista="A", titulo="T", fecha=dt.date(2026, 11, 1),
              fecha_publicacion=dt.date(2026, 11, 2), etiquetas=["x"], resenas_extra=[{"medio": "M", "nota": "8/10"}])
    return ResultadoFuente("f", "ok", "", 3, [it])


def test_lectura_guardada_ida_y_vuelta(tmp_path):
    h = _huella({"id": "f", "urls": ["u"]}, dt.date(2026, 1, 1))
    guardar_lectura(str(tmp_path), _res(), h)
    r = cargar_lectura(str(tmp_path), "f", h, 30)
    assert r is not None and r.items[0].fecha == dt.date(2026, 11, 1) and r.items[0].resenas_extra[0]["medio"] == "M"


def test_lectura_guardada_se_descarta_si_cambia_algo(tmp_path):
    h = _huella({"id": "f", "urls": ["u"]}, dt.date(2026, 1, 1))
    guardar_lectura(str(tmp_path), _res(), h)
    assert cargar_lectura(str(tmp_path), "f", _huella({"id": "f", "urls": ["otra"]}, dt.date(2026, 1, 1)), 30) is None
    assert cargar_lectura(str(tmp_path), "f", h, 0) is None                     # --refrescar
    p = tmp_path / "f.json"
    d = json.loads(p.read_text())
    d["leida"] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=31)).isoformat()
    p.write_text(json.dumps(d))
    assert cargar_lectura(str(tmp_path), "f", h, 30) is None                    # caducada
    p.write_text("{roto")
    assert cargar_lectura(str(tmp_path), "f", h, 30) is None                    # dañada: se relee


def test_lectura_con_error_vacia_o_bloqueada_no_se_reutiliza(tmp_path):
    h = "h"
    for estado in ("error", "vacia", "bloqueada", "prohibida"):
        guardar_lectura(str(tmp_path), ResultadoFuente("f", estado, "x"), h)
        assert cargar_lectura(str(tmp_path), "f", h, 30) is None, estado


# ------------------------------------------------------------------ orquestador
def test_pipeline_reanuda_tras_un_fallo(tmp_path, monkeypatch):
    p_estado = tmp_path / "estado.json"
    monkeypatch.setattr(pipeline, "cargar_config", lambda: {"rutas": {"estado_pipeline": str(p_estado)}})
    monkeypatch.setattr(pipeline, "ruta", lambda r: r)
    monkeypatch.setattr(pipeline.os.path, "exists", lambda p: True if p.endswith(".py") else os.path.isfile(p))
    llamadas = []

    class R:
        def __init__(self, c):
            self.returncode = c

    fallar = {"clasificar"}

    def run(argv, cwd=None, **k):
        llamadas.append(argv[3])
        return R(1 if argv[3] == "scraper.clasificar" and "clasificar" in fallar else 0)

    monkeypatch.setattr(pipeline.subprocess, "run", run)
    assert pipeline.main([]) == 1
    assert llamadas == ["scraper.recoger", "scraper.enriquecer", "scraper.clasificar"]
    estado = json.loads(p_estado.read_text())
    assert estado["fases"]["recoger"]["estado"] == "hecha" and estado["fases"]["clasificar"]["estado"] == "fallida"
    # se relanza: no repite recoger ni enriquecer
    fallar.clear()
    llamadas.clear()
    assert pipeline.main([]) == 0
    assert llamadas[0] == "scraper.clasificar" and "scraper.recoger" not in llamadas
    assert json.loads(p_estado.read_text())["terminada"]


def test_pipeline_no_reanuda_otro_modo_ni_lo_caducado():
    ahora = dt.datetime.now(dt.timezone.utc)
    viejo = {"modo": "completa", "inicio": (ahora - dt.timedelta(days=5)).isoformat(), "fases": {}}
    assert not pipeline.ejecucion_vigente(viejo, "completa", ahora)
    reciente = dict(viejo, inicio=ahora.isoformat())
    assert pipeline.ejecucion_vigente(reciente, "completa", ahora)
    assert not pipeline.ejecucion_vigente(reciente, "incremental", ahora)
    assert not pipeline.ejecucion_vigente(dict(reciente, terminada=True), "completa", ahora)
    assert not pipeline.ejecucion_vigente(None, "completa", ahora)


# ------------------------------------------------------------------ mapeo con Wikidata (sin red)
class WikidataFalso:
    def __init__(self, busquedas, entidades, falla=False):
        self.b, self.entidades_all, self.falla = busquedas, entidades, falla
        self.entidades = {}

    def buscar(self, t):
        return None if self.falla else self.b.get(t, [])

    def entidades_de(self, ids):
        for i in ids:
            if i in self.entidades_all:
                self.entidades[i] = self.entidades_all[i]
        return True


def _ent(qid, label, p31=(), p279=(), desc=""):
    claims = {"P31": [{"mainsnak": {"datavalue": {"value": {"id": x}}}} for x in p31],
              "P279": [{"mainsnak": {"datavalue": {"value": {"id": x}}}} for x in p279]}
    return {"id": qid, "labels": {"en": {"value": label}}, "aliases": {}, "claims": claims,
            "descriptions": {"en": {"value": desc}}}


TAXW = {"familias": {"country": {"grupos": {"g": {"americana": {"alias": ["americana"]}}}}}}


def test_mapear_sube_por_la_jerarquia():
    wd = WikidataFalso({"nordicana": [{"id": "Q1", "label": "Nordicana"}]},
                       {"Q1": _ent("Q1", "Nordicana", p31=["Q188451"], p279=["Q2"]),
                        "Q2": _ent("Q2", "Americana", p31=["Q188451"])})
    sub, nota = resolver("nordicana", wd, Taxonomia(TAXW))
    assert sub == "americana" and "Q1" in nota


def test_mapear_no_genero_homonimo_y_sin_respuesta():
    tax = Taxonomia(TAXW)
    wd = WikidataFalso({"London": [{"id": "Q84", "label": "London"}]}, {"Q84": _ent("Q84", "London", p31=["Q515"])})
    assert resolver("London", wd, tax)[0] == "ninguno"
    wd = WikidataFalso({"Heart": [{"id": "Q9", "label": "Heartbeat"}]}, {})
    assert resolver("Heart", wd, tax)[0] == "ninguno"                    # ningún elemento con ese nombre exacto
    assert resolver("x", WikidataFalso({}, {}, falla=True), tax) is None  # Wikidata no responde: sigue pendiente


def test_mapear_genero_fuera_de_taxonomia_deja_la_cadena():
    wd = WikidataFalso({"trip hop": [{"id": "Q3", "label": "trip hop"}]},
                       {"Q3": _ent("Q3", "trip hop", p31=["Q188451"], p279=["Q4"]),
                        "Q4": _ent("Q4", "electronic music", p31=["Q188451"])})
    sub, nota = resolver("trip hop", wd, Taxonomia(TAXW))
    assert sub == "ninguno" and "electronic music" in nota


def test_mapear_ciclos_en_la_jerarquia_no_cuelgan():
    wd = WikidataFalso({"a": [{"id": "Q1", "label": "a"}]},
                       {"Q1": _ent("Q1", "a", p31=["Q188451"], p279=["Q2"]),
                        "Q2": _ent("Q2", "b", p31=["Q188451"], p279=["Q1"])})
    assert resolver("a", wd, Taxonomia(TAXW))[0] == "ninguno"


def test_pipeline_solo_reanudar_sin_nada_pendiente(tmp_path, monkeypatch):
    p_estado = tmp_path / "estado.json"
    monkeypatch.setattr(pipeline, "cargar_config", lambda: {"rutas": {"estado_pipeline": str(p_estado)}})
    monkeypatch.setattr(pipeline, "ruta", lambda r: r)
    monkeypatch.setattr(pipeline.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no debía ejecutar")))
    assert pipeline.main(["--solo-reanudar"]) == 0
    p_estado.write_text(json.dumps({"modo": "completa", "inicio": "2020-01-01T00:00:00+00:00", "fases": {}}))
    assert pipeline.main(["--solo-reanudar"]) == 0        # caducada: tampoco


def test_pipeline_desde_una_fase(tmp_path, monkeypatch):
    p_estado = tmp_path / "estado.json"
    monkeypatch.setattr(pipeline, "cargar_config", lambda: {"rutas": {"estado_pipeline": str(p_estado)}})
    monkeypatch.setattr(pipeline, "ruta", lambda r: r)
    monkeypatch.setattr(pipeline.os.path, "exists", lambda p: True if p.endswith(".py") else os.path.isfile(p))
    llamadas = []

    class R:
        returncode = 0

    monkeypatch.setattr(pipeline.subprocess, "run", lambda argv, **k: llamadas.append(argv[3]) or R())
    assert pipeline.main(["--desde=enriquecer"]) == 0
    assert llamadas[0] == "scraper.enriquecer" and "scraper.recoger" not in llamadas
    assert pipeline.main(["--desde=no-existe"]) == 2


def test_version_2x_coincide_con_la_web():
    assert version_2x("https://coverartarchive.org/release-group/x/front-250").endswith("front-500")
    assert version_2x("https://cdn-images.dzcdn.net/images/cover/a/250x250-000000-80-0-0.jpg").endswith("/500x500-000000-80-0-0.jpg")
    assert version_2x("https://f4.bcbits.com/img/a123_2.jpg") == "https://f4.bcbits.com/img/a123_16.jpg"
    assert version_2x("https://otra.web/x.jpg") is None and version_2x(None) is None
