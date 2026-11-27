# Arquitectura, persistencia, fallos y pruebas

Este documento explica cómo está hecho el sistema, dónde se guarda cada cosa, qué pasa
cuando algo falla y qué está probado. Está escrito para quien lo mantenga, no para el
público de la web.

## 1. Visión general

```
           fuentes (prensa, sellos, listados, Wikipedia, radares MusicBrainz/Deezer, listas anuales)
                                         │  lectura educada: robots.txt, ritmo por web, caché
                                         ▼
 recoger ──► enriquecer ──► clasificar ──► mapear ──► clasificar ──► informe ──► web
 (unir,       (Deezer,       (taxonomía +   (etiquetas   (con lo      (docs/      (site/data,
  MusicBrainz, iTunes,        mapeo)         nuevas vía   mapeado)     informe.md)  RSS, .ics)
  Bandcamp,    Wikidata,                     Wikidata)
  reglas)      Discogs, Last.fm)
     │              │              │              │                        │             │
     ▼              ▼              ▼              ▼                        ▼             ▼
 data/candidatos  data/cache/   data/discos    data/mapeo_            docs/          GitHub Pages
 .json            etiquetas_    .json          etiquetas.csv          informe.md     (web estática)
                  extra.json
```

**Patrón:** *git scraping* (datos que un proceso programado recoge y guarda como archivos
versionados en el propio repositorio) + **web estática** (HTML, CSS y JavaScript sin
servidor) + **GitHub Actions** como ejecutor. Se eligió porque:

- no hay servidores ni base de datos que mantener ni pagar: el coste es cero;
- cada cambio de datos queda en el historial de git (se puede ver qué entró, cuándo y por qué);
- la web la sirve GitHub Pages desde su CDN: rápida y sin caídas propias;
- todo el proceso corre en GitHub, **sin depender de ninguna sesión de Claude ni gastar tokens**.

Para este volumen (unos miles de discos al año) una base de datos no aporta nada que no den
los archivos JSON. Si algún día hicieran falta búsquedas complejas en el servidor o cuentas de
usuario, el siguiente paso natural sería SQLite (archivo único, también versionable) o una
base gestionada, sin cambiar el resto.

**Tecnologías:** Python 3.12 (requests, BeautifulSoup/lxml, PyYAML, python-dateutil) en el
proceso de datos; JavaScript sin framework en la web (carga instantánea, sin paso de
compilación, nada que actualizar); service worker para uso sin conexión e instalación como
app; Playwright y pytest para las pruebas.

## 2. Todo se configura sin tocar código

| Qué | Dónde |
|---|---|
| Webs a leer y cómo (patrones, paginación, familia, si es mixta…) | `data/fuentes.yaml` |
| Familias, subgéneros, alias, descripciones, genéricas, ignoradas | `data/taxonomia.yaml` |
| Ventana de fechas, reglas (EP, reediciones, idioma), ritmos, rutas | `data/config.yaml` |
| Etiqueta → subgénero (respuestas de Wikidata, del LLM o a mano) | `data/mapeo_etiquetas.csv` |

## 3. Persistencia: dónde se guarda cada cosa

| Dato | Archivo | ¿En git? | Para qué |
|---|---|---|---|
| Discos recogidos, antes de clasificar | `data/candidatos.json` | Sí | Entrada de la clasificación; base de la recogida incremental |
| Discos publicados | `data/discos.json` | Sí | Lo que muestra la web |
| Descartes y su motivo | `data/descartados.json` | Sí | Auditoría ("¿por qué no sale X?") |
| Estado de cada fuente en la última recogida | `data/estado_fuentes.json` | Sí | Informe y resumen de la Action |
| Estado de las fases de la última ejecución | `data/estado_pipeline.json` | Sí | Reanudar por la fase pendiente |
| Listas de fin de año | `data/listas_anuales.json` | Sí | "Lo mejor del año" |
| Mapeo de etiquetas | `data/mapeo_etiquetas.csv` | Sí | Clasificación |
| Consultas a MusicBrainz, Bandcamp, Deezer, iTunes, Wikidata, Discogs, Last.fm | `data/cache/*.json` | Sí | No repetir consultas (semanas o meses de trabajo de red) |
| Lo leído de cada fuente | `data/cache/lecturas/` | No (caché de la Action) | Reanudar una recogida cortada sin releer las fuentes (30 h) |
| Páginas descargadas | `data/cache/http/` | No (caché de la Action) | No repetir la misma petición en 20 h |
| Web: índice ligero | `site/data/discos.json` | Sí | Cuadrícula, filtros y orden |
| Web: detalle de cada disco, por meses | `site/data/fichas/AAAA-MM.json` | Sí | Se descarga al abrir una ficha |
| "Mi lista" y preferencias de vista | `localStorage` del navegador | — | Sin cuentas ni datos personales en ningún servidor |

Todas las escrituras de archivos JSON son **atómicas** (se escribe un temporal y se renombra):
un corte a mitad de escritura deja el archivo anterior intacto.

## 4. Tolerancia a fallos

| Qué falla | Qué hace el sistema |
|---|---|
| Una web muestra una verificación anti-bots (Cloudflare…) o responde 401/403 | Se deja esa web en esa ejecución, se anota en `estado_fuentes.json` y en el informe. **Nunca se intenta saltar.** |
| `robots.txt` no permite una dirección | No se lee; queda como "prohibida" |
| 429 "demasiadas peticiones" | Se espera lo que pide la web (`Retry-After`) y se reintenta dos veces; si sigue, se trata como bloqueo |
| 503 de MusicBrainz (saturado) | Reintentos con espera creciente (5) |
| Error de red o tiempo agotado | Dos reintentos; si sigue, la fuente queda "error" y el resto continúa |
| Página vacía, RSS roto o 404 | La fuente queda "vacía"; no rompe nada |
| Una fuente cambia de formato | Sale "vacía" en el resumen de la Action y en el informe; se corrige su patrón en `fuentes.yaml` |
| El proceso se corta (reinicio, límite de 6 h de GitHub) | Lo leído de cada fuente y cada consulta ya están guardados; `scraper.pipeline` sigue por la fase pendiente. La Action diaria lo reanuda sola |
| Una fase falla | Se marca "fallida", el resto no se ejecuta con datos a medias y la siguiente ejecución empieza por ella. GitHub avisa por correo de la ejecución fallida |
| Wikidata no responde | Las etiquetas siguen "pendientes" y se intentan la próxima vez |
| Una portada no carga | Se prueba la de Deezer y, si tampoco, se muestra el nombre del artista sobre un color |
| El usuario está sin conexión | La web funciona con lo último que vio (service worker) |

**Ritmos que se respetan siempre:** MusicBrainz 1 petición cada 1,1 s (aunque haya consultas
en paralelo: un candado por web controla el inicio de cada petición), Bandcamp 1 cada 4 s,
iTunes 1 cada 3,1 s, Discogs 1 cada 2,5 s, el resto 1 cada 2 s o lo que diga su `robots.txt`.

## 5. Clasificación y uso de IA

1. **Reglas y alias** (`taxonomia.yaml`): la mayor parte. Deterministas, explicables.
2. **Mapeo de etiquetas** (`mapeo_etiquetas.csv`): cada etiqueta desconocida se resuelve **una sola vez**
   en la fase `mapear`, sin intervención:
   - **LLM (Claude, API de Anthropic)** si existe el secreto `ANTHROPIC_API_KEY` (`scraper/llm.py`):
     lotes de 50 etiquetas; la respuesta va con **esquema JSON** y se valida contra la taxonomía (un id
     inventado se descarta y la etiqueta sigue pendiente); la taxonomía va en un bloque cacheado; si el
     modelo declina, responde otro (fallback del servidor). Modelo y esfuerzo en `config.yaml`
     (`enriquecimiento.llm`). Coste estimado con `claude-opus-5-5` y esfuerzo bajo: unos 2 $ la primera
     vez (≈1.500 etiquetas) y céntimos por semana; con `claude-haiku-5-5`, unas 40 veces menos;
   - **Wikidata** para lo que quede, o para todo si no hay clave (`scraper/mapear.py`): gratis; se busca el
     género y se sube por "subclase de" hasta un subgénero (p. ej. *blackgaze* → atmospheric black metal);
   - el LLM de una sesión de Claude Code, si se está trabajando en el proyecto.
3. **Nunca se crean subgéneros automáticamente**: lo que el LLM o Wikidata identifican como género sin sitio
   en la taxonomía queda como "propuesta" en el informe.

La clave de la API **no viene con el plan Pro de Claude**: se crea en la consola de Anthropic y se paga
por uso. Sin ella todo sigue funcionando con Wikidata.

## 6. Rendimiento

- Web: el índice pesa **115 KB comprimido** con 1.267 discos (antes 243 KB); el detalle de cada
  disco se descarga por meses al abrir la ficha. Las portadas se cargan solo al verse (`loading=lazy`).
- Cuadrícula paginada por semanas ("ver semanas anteriores"), así que el navegador no pinta miles de tarjetas de golpe.
- Proceso de datos: todo lo consultado se guarda; la ejecución semanal solo relee las últimas
  semanas de cada fuente y solo consulta MusicBrainz por los discos nuevos. MusicBrainz responde
  en unos 3–4 s, así que sus consultas van en paralelo (4) sin pasar del límite de 1 por segundo.

## 7. Pruebas (se ejecutan en GitHub en cada envío: `.github/workflows/pruebas.yml`)

| Tipo de escenario | Ejemplos cubiertos | Archivo |
|---|---|---|
| Nominal | RSS y páginas con fecha, sello, nota, género y fecha de salida; disco reseñado en dos fuentes se une en uno | `test_lectores.py`, `test_extremo_a_extremo.py` |
| Reglas de negocio | EP, reedición/remaster, fuera de la ventana, fuente mixta con género ajeno, nota media, índice/fichas de la web | `test_extremo_a_extremo.py`, `test_web_y_fases.py` |
| Borde | Fechas sin año (año más cercano), "Sept.", 29 de febrero, fin de mes, fechas parciales de MusicBrainz, notas sobre 5/10/100, límite de subgéneros, ciclos en Wikidata | `test_util.py`, `test_web_y_fases.py`, `test_clasificar.py` |
| Error | Bloqueo anti-bots, robots.txt, red caída, 404, RSS vacío o roto, 429 persistente, 503, escritura fallida, lectura guardada dañada o caducada, Wikidata sin respuesta, fase que falla | `test_http.py`, `test_lectores.py`, `test_web_y_fases.py` |
| Reanudación | Relanzar la recogida sin red usa lo ya leído; el orquestador sigue por la fase fallida y no repite las hechas | `test_extremo_a_extremo.py`, `test_web_y_fases.py` |
| Concurrencia | Con 4 hilos, nunca dos peticiones a la misma web en menos del intervalo | `test_http.py` |
| Configuración y datos | Toda fuente bien definida y con patrones válidos, taxonomía coherente, mapeo apunta a subgéneros que existen, formato de los discos publicados | `test_config_y_datos.py` |
| Web (navegador real, móvil y escritorio) | Carga sin errores, familias, búsqueda vacía, ficha y su enlace, Qobuz, Mi lista y recarga, vista lista, órdenes, lo mejor del año, calendario, filtros, enlace profundo, botones con nombre accesible, imágenes con `alt`, sin desplazamiento horizontal en móvil | `tests/e2e/web.mjs` |

Las pruebas ya han encontrado y corregido dos fallos reales: el panel de filtros podía salirse
de la pantalla del móvil (la × quedaba fuera) y una escritura fallida dejaba un archivo temporal.

## 8. Qué está validado y qué no (27-nov-2026)

| | Estado |
|---|---|
| Fuentes probadas una a una con el robot real (≈70) | ✅ |
| Clasificación con los 5 últimos meses (1.267 discos, 76 % con subgénero) | ✅ |
| Web revisada con datos reales en móvil y escritorio + pruebas automáticas | ✅ |
| Pruebas automáticas en GitHub | ✅ (se ejecutan en cada envío) |
| Datos de todo 2026 | ⏳ recogida completa en curso |
| Action de datos en GitHub | ⏳ se activa al pasar a `main` |
| Web publicada | ⏳ falta pasar a `main` y activar GitHub Pages (Settings → Pages → Source: GitHub Actions) |
| Comparación de funciones con AOTY, RYM, Metacritic y AllMusic | ⏳ sus webs bloquean a los robots; pendiente de revisarlas con tu navegador |

## 9. Cómo se ejecuta

```
python -m scraper.pipeline                 # todo, reanudable (completa)
python -m scraper.pipeline --incremental   # la semanal
python -m scraper.pipeline --desde=enriquecer
python -m pytest                           # pruebas de Python
node tests/e2e/web.mjs site                # prueba de la web en navegador
```
