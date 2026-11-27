"""Intercambio de etiquetas con un LLM por archivos: solo se aplican ids existentes y solo a pendientes."""
from scraper.clasificar import Taxonomia
from scraper.etiquetas_llm import aplicar, exportar

TAX = Taxonomia({"familias": {"country": {"grupos": {"g": {"americana": {}, "alt-country": {}}}}}})


def mapeo():
    return {"nordicana": {"etiqueta": "Nordicana", "subgenero": "pendiente", "veces": "3"},
            "london": {"etiqueta": "London", "subgenero": "pendiente", "veces": "9"},
            "x": {"etiqueta": "x", "subgenero": "pendiente", "veces": ""},
            "roots": {"etiqueta": "roots", "subgenero": "americana", "veces": "1"}}


def test_exportar_ordena_por_frecuencia_y_solo_pendientes():
    lista = exportar(mapeo())
    assert [e["etiqueta"] for e in lista] == ["London", "Nordicana", "x"]


def test_aplicar_valida_ids_y_no_toca_lo_decidido():
    m = mapeo()
    n, rech = aplicar(m, {"Nordicana": ["americana", ""], "London": "ninguno", "x": ["inventado", ""],
                          "roots": ["alt-country", ""], "no-existe": ["americana", ""], "raro": 5}, TAX)
    assert n == 2 and set(rech) == {"x", "raro"}
    assert m["nordicana"]["subgenero"] == "americana" and m["nordicana"]["origen"] == "llm"
    assert m["london"]["subgenero"] == "ninguno"
    assert m["x"]["subgenero"] == "pendiente"           # id inventado: sigue pendiente
    assert m["roots"]["subgenero"] == "americana"       # ya decidido: no se cambia


def test_aplicar_varios_ids_y_maximo_tres():
    m = mapeo()
    aplicar(m, {"Nordicana": ["americana|alt-country|americana", "mezcla"]}, TAX)
    assert m["nordicana"]["subgenero"] == "americana|alt-country" and m["nordicana"]["nota"] == "mezcla"
