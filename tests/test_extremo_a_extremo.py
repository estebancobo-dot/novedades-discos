"""De extremo a extremo: recoger → clasificar → informe → web sobre una copia mínima del proyecto,
con páginas de ejemplo servidas desde la caché (sin red, sin MusicBrainz ni Bandcamp).
Comprueba las reglas de negocio: duplicados unidos, EP, reediciones, fuera de ventana, otro género."""
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys

import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sembrar(cache_dir, url, texto):
    os.makedirs(cache_dir, exist_ok=True)
    with open(os.path.join(cache_dir, hashlib.sha1(url.encode()).hexdigest() + ".json"), "w", encoding="utf-8") as f:
        json.dump({"url": url, "estado": 200, "texto": texto}, f)


def _rss_fecha(d):
    return d.strftime("%a, %d %b %Y 10:00:00 +0000")


def _montar(tmp):
    hoy = dt.date.today()
    reciente = hoy - dt.timedelta(days=10)
    antiguo = dt.date(hoy.year - 2, 3, 1)
    for rel in ("data/config.yaml", "data/taxonomia.yaml", "data/mapeo_etiquetas.csv"):
        os.makedirs(os.path.join(tmp, os.path.dirname(rel)), exist_ok=True)
        shutil.copy(os.path.join(RAIZ, rel), os.path.join(tmp, rel))
    with open(os.path.join(RAIZ, "data/fuentes.yaml"), encoding="utf-8") as f:
        macros = yaml.safe_load(f)["macros"]
    fuentes = {"macros": macros, "fuentes": [
        {"id": "lista", "nombre": "Lista de prueba", "familia": "country", "rol": "listado", "lector": "texto",
         "fecha_es": "lanzamiento", "urls": ["https://e2e.example/lista"],
         "patrones": [r"^(?P<fecha>\d{4}-\d{2}-\d{2}) \| (?P<artista>[^|\n]+?) \| (?P<titulo>[^|\n]+?) \| (?P<tipo>[^|\n]+?)$"]},
        {"id": "resenas", "nombre": "Reseñas de prueba", "familia": "todas", "mixta": True, "rol": "resena",
         "lector": "rss", "urls": ["https://e2e.example/feed"], "nota": r"(?P<nota>\d+/10)",
         "patrones": [r"^(?P<artista>.+?)\s+–\s+(?P<titulo>.+?) review$"]},
    ]}
    with open(os.path.join(tmp, "data/fuentes.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(fuentes, f, allow_unicode=True)
    lineas = [
        f"{reciente} | Ruby Hollow | Long Gone Daddy | Album",          # normal (y reseñado en la otra fuente)
        f"{reciente} | Ruby Hollow | Pickup Lines | EP",                 # EP
        f"{reciente} | Old Band | Greatest Days (Remastered) | Album",   # reedición
        f"{antiguo} | Past Due | Yesterday | Album",                     # fuera de la ventana
    ]
    pagina = "<html><body>" + "".join(f"<p>{x}</p>" for x in lineas) + "</body></html>"
    feed = f"""<?xml version="1.0"?><rss><channel>
<item><title>Ruby Hollow – Long Gone Daddy review</title><link>https://e2e.example/r1</link>
 <pubDate>{_rss_fecha(reciente)}</pubDate><category>Americana</category><description>Great. 8/10</description></item>
<item><title>DJ Pulse – Night Drive review</title><link>https://e2e.example/r2</link>
 <pubDate>{_rss_fecha(reciente)}</pubDate><category>Techno</category><description>Big beats. 7/10</description></item>
</channel></rss>"""
    cache = os.path.join(tmp, "data/cache/http")
    _sembrar(cache, "https://e2e.example/lista", pagina)
    _sembrar(cache, "https://e2e.example/feed", feed)
    return tmp


def _ejecutar(tmp, modulo, *args):
    env = dict(os.environ, NOVEDADES_RAIZ=str(tmp), PYTHONPATH=RAIZ)
    r = subprocess.run([sys.executable, "-m", modulo, *args], cwd=RAIZ, env=env, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"{modulo} falló:\n{r.stdout[-2000:]}\n{r.stderr[-3000:]}"
    return r.stdout


def test_cadena_completa(tmp_path):
    tmp = _montar(str(tmp_path))
    _ejecutar(tmp, "scraper.recoger", "--sin-mb", "--sin-bandcamp")
    _ejecutar(tmp, "scraper.clasificar")
    _ejecutar(tmp, "scraper.informe")
    _ejecutar(tmp, "scraper.web")

    discos = json.load(open(os.path.join(tmp, "data/discos.json"), encoding="utf-8"))
    descartados = json.load(open(os.path.join(tmp, "data/descartados.json"), encoding="utf-8"))
    por_titulo = {d["titulo"]: d for d in discos}
    motivos = {d["titulo"]: d["motivo"] for d in descartados}

    # normal: entra una sola vez, con las dos fuentes, la reseña y su nota
    assert list(por_titulo) == ["Long Gone Daddy"]
    d = por_titulo["Long Gone Daddy"]
    assert {f["id"] for f in d["fuentes"]} == {"lista", "resenas"}
    assert "country" in d["familias"] and "americana" in d["subgeneros"]
    assert any(r.get("nota") == "8/10" for r in d["resenas"])
    # reglas de descarte
    assert "EP" in motivos["Pickup Lines"]
    assert "reedición" in motivos["Greatest Days (Remastered)"]
    assert "ventana" in motivos["Yesterday"]
    assert "Night Drive" in motivos                        # fuente mixta, género ajeno: fuera
    # salidas de la web y del informe
    web = json.load(open(os.path.join(tmp, "site/data/discos.json"), encoding="utf-8"))
    assert [x["titulo"] for x in web["discos"]] == ["Long Gone Daddy"] and web["discos"][0]["nota"] == 8.0
    assert "fuentes" not in web["discos"][0] and web["discos"][0]["n_resenas"] == 1     # índice ligero
    mes = web["discos"][0]["fecha"][:7]
    ficha = json.load(open(os.path.join(tmp, f"site/data/fichas/{mes}.json"), encoding="utf-8"))[web["discos"][0]["id"]]
    assert {f["nombre"] for f in ficha["fuentes"]} == {"Lista de prueba", "Reseñas de prueba"}    # detalle aparte
    assert os.path.exists(os.path.join(tmp, "site/rss/todo.xml"))
    assert os.path.exists(os.path.join(tmp, "docs/informe.md"))
    # estado de las fuentes y lecturas guardadas para reanudar
    estado = json.load(open(os.path.join(tmp, "data/estado_fuentes.json"), encoding="utf-8"))
    assert estado["fuentes"]["lista"]["estado"] == "ok"
    assert os.path.exists(os.path.join(tmp, "data/cache/lecturas/lista.json"))


def test_relanzar_reutiliza_lo_leido(tmp_path):
    tmp = _montar(str(tmp_path))
    _ejecutar(tmp, "scraper.recoger", "--sin-mb", "--sin-bandcamp")
    shutil.rmtree(os.path.join(tmp, "data/cache/http"))     # sin páginas: solo puede tirar de lo guardado
    salida = _ejecutar(tmp, "scraper.recoger", "--sin-mb", "--sin-bandcamp")
    assert "lectura guardada" in salida
    discos = json.load(open(os.path.join(tmp, "data/candidatos.json"), encoding="utf-8"))
    assert any(d["titulo"] == "Long Gone Daddy" for d in discos)
