"""Mapeo con LLM usando un cliente falso: sin clave ni coste. Comprueba que solo se aceptan ids
de la taxonomía, que una negativa o un corte no estropean nada y que un error deja todo pendiente."""
import json
from types import SimpleNamespace as NS

from scraper.clasificar import Taxonomia
from scraper.llm import MapeadorLLM, validar

DATOS = {"familias": {"country": {"grupos": {"g": {
    "americana": {"nombre": "Americana", "alias": ["roots"]},
    "alt-country": {"nombre": "Alt-country"}}}}}}
TAX = Taxonomia(DATOS)


def respuesta(obj, stop="end_turn"):
    return NS(stop_reason=stop, usage=NS(input_tokens=100, output_tokens=20, cache_read_input_tokens=80),
              content=[NS(type="thinking", thinking=""), NS(type="text", text=json.dumps(obj))])


class ClienteFalso:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.peticiones = []
        self.beta = NS(messages=NS(create=self._create))

    def _create(self, **kw):
        self.peticiones.append(kw)
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def mapeador(respuestas, lote=50):
    return MapeadorLLM({"activo": True, "lote": lote}, TAX, DATOS, cliente=ClienteFalso(respuestas))


def test_validar_descarta_ids_inventados_y_etiquetas_no_pedidas():
    r = validar([{"etiqueta": "nordicana", "subgeneros": ["americana"], "propuesta": ""},
                 {"etiqueta": "x", "subgeneros": ["inventado"], "propuesta": ""},
                 {"etiqueta": "no-pedida", "subgeneros": ["americana"], "propuesta": ""},
                 {"etiqueta": "cajun", "subgeneros": [], "propuesta": "cajun"},
                 {"etiqueta": "London", "subgeneros": [], "propuesta": ""}],
                ["nordicana", "x", "cajun", "London"], TAX)
    assert r == {"nordicana": ("americana", ""), "cajun": ("ninguno", "propuesta: cajun"), "London": ("ninguno", "")}


def test_lotes_peticion_y_salida_estructurada():
    m = mapeador([respuesta({"respuestas": [{"etiqueta": "a", "subgeneros": ["americana"], "propuesta": ""},
                                            {"etiqueta": "b", "subgeneros": ["alt-country"], "propuesta": ""}]}),
                  respuesta({"respuestas": [{"etiqueta": "c", "subgeneros": [], "propuesta": ""}]})], lote=2)
    r = m.mapear(["a", "b", "c"])
    assert r == {"a": ("americana", ""), "b": ("alt-country", ""), "c": ("ninguno", "")}
    pet = m.cliente.peticiones[0]
    assert pet["model"] == "claude-opus-5-5"
    assert pet["output_config"]["format"]["type"] == "json_schema"
    assert pet["system"][0]["cache_control"] == {"type": "ephemeral"}          # la taxonomía se cachea
    assert "americana: Americana" in pet["system"][0]["text"]
    assert m.uso["peticiones"] == 2


def test_negativa_o_corte_dejan_el_lote_pendiente_y_siguen():
    m = mapeador([respuesta({}, stop="refusal"), respuesta({"respuestas": [{"etiqueta": "c", "subgeneros": [], "propuesta": ""}]})], lote=1)
    assert m.mapear(["a", "c"]) == {"c": ("ninguno", "")}


def test_json_roto_no_rompe():
    m = mapeador([NS(stop_reason="end_turn", usage=None, content=[NS(type="text", text="{roto")])])
    assert m.mapear(["a"]) == {}


def test_error_de_red_para_y_deja_lo_demas_pendiente():
    m = mapeador([respuesta({"respuestas": [{"etiqueta": "a", "subgeneros": ["americana"], "propuesta": ""}]}),
                  ConnectionError("sin red")], lote=1)
    assert m.mapear(["a", "b", "c"]) == {"a": ("americana", "")}
    assert "ConnectionError" in m.error


def test_sin_clave_no_se_usa(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert not MapeadorLLM.disponible({"activo": True})
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-prueba")
    assert MapeadorLLM.disponible({"activo": True})
    assert not MapeadorLLM.disponible({"activo": False})
