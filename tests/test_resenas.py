"""Reseñas completas desde el agregador: se leen con los selectores de la configuración y se fusionan por medio."""
from scraper.config import cargar_config
from scraper.resenas import fusionar_resenas, leer_agregador

HTML = """<ol id="album_reviews_list"><li class="review_item"><span class="data_rating">9.0</span>
<h4> 9.0 | &nbsp; <span>Rolling Stone</span></h4><p> The rock legends return. <br/><a href='https://rs.example/u2'>Read Review</a></p></li>
<li class="review_item"><span class="data_rating">4.0</span><h4>4.0 | <span>The Arts Desk</span></h4><p>It's just humdrum
<a href='https://ad.example/u2'>Read Review</a></p></li>
<li class="review_item"><span class="data_rating">8.0</span><h4>8.0 | <span>Mojo</span></h4><p>Shiny and heartfelt <a href='https://mojo.example/u2'>Read Review</a></p></li></ol>"""


class Nav:
    def __init__(self, estado=200):
        self.estado = estado

    def get(self, url):
        return type("R", (), {"estado": self.estado, "texto": HTML})()


def test_lee_y_fusiona_sin_duplicar_medios():
    cfg = cargar_config()["enriquecimiento"]["resenas_agregadores"][0]
    lista = leer_agregador(Nav(), "http://www.anydecentmusic.com/review/1/x.aspx", cfg)
    assert [x["medio"] for x in lista] == ["Rolling Stone", "The Arts Desk", "Mojo"]
    assert lista[0] == {"medio": "Rolling Stone", "nota": "9/10", "frase": "The rock legends return.", "url": "https://rs.example/u2"}
    d = {"resenas": [{"nombre": "Rolling Stone (vía Any Decent Music)", "url": "http://www.anydecentmusic.com/review/1/x.aspx", "nota": "9/10"},
                     {"nombre": "Arts Desk (vía Any Decent Music)", "url": "http://www.anydecentmusic.com/review/1/x.aspx", "nota": "4/10"}]}
    assert fusionar_resenas(d, lista, "anydecentmusic") == 1                 # solo Mojo es nueva
    rs = d["resenas"][0]
    assert rs["nombre"] == "Rolling Stone" and rs["url"] == "https://rs.example/u2" and rs["frase"] == "The rock legends return."
    assert d["resenas"][1]["frase"].startswith("It's just humdrum") and len(d["resenas"]) == 3


def test_pagina_que_no_responde_no_rompe_nada():
    cfg = cargar_config()["enriquecimiento"]["resenas_agregadores"][0]
    assert leer_agregador(Nav(estado=404), "u", cfg) is None
