# Estado del arte y decisiones, capa por capa

Qué ofrecen las webs de referencia, qué alternativas técnicas hay en cada capa, con qué criterio
se ha elegido y qué se cambia por ello. Escrito el 27-nov-2026. Las afirmaciones sobre otras
webs llevan su fuente; lo que no se ha podido comprobar se dice.

## 1. Las webs de referencia: qué se ha podido comprobar y cómo

El robot del proyecto no las lee (verificación anti-bots). Para estudiar sus funciones —no para
sacar datos— se ha probado además un lector web distinto y fuentes que las describen:

| Web | Lector alternativo | Fuentes descriptivas usadas |
|---|---|---|
| Metacritic (música) | ✅ lista "All New Music by Release Date" legible; la ficha de un disco, 403 | — |
| Album of the Year | ❌ 403 en portada, novedades, próximos y rankings | Proyecto [AlbumOfTheYearAPI](https://github.com/JahsiasWhite/AlbumOfTheYearAPI) (su referencia de funciones refleja lo que muestran las páginas) |
| Rate Your Music | ❌ 403 | [Wikipedia: Rate Your Music](https://en.wikipedia.org/wiki/Rate_Your_Music) |
| AllMusic | ❌ 403 | [Wikipedia: AllMusic](https://en.wikipedia.org/wiki/AllMusic) (marcada como desactualizada) |

### Funciones comprobadas y comparación

| Función | Quién la tiene (fuente) | Nuestra web |
|---|---|---|
| Lista de novedades por fecha, de la más reciente | Metacritic: lista plana con fecha por disco y anuncios intercalados | ✅ agrupada por semanas, sin anuncios, con índice de meses |
| Ordenar por nota de la crítica / de usuarios | Metacritic: "Newest", "Metascore (High–Low)", "User Score (High–Low)"… | ✅ recientes, mejor valorados, más reseñados (no hay nota de usuarios: no hay cuentas) |
| Tamaño de página | Metacritic: 25 / 50 / 100 por página | ✅ carga por tandas ("ver más") |
| Filtro por año | Metacritic: año o rango de años | ✅ rango de fechas libre |
| Filtro por género | Metacritic: sección "Genres" | ✅ familia + subgéneros múltiples, con descripción de cada uno |
| Resumen breve de cada disco en la lista | Metacritic: una o dos frases por disco | 🟡 en la ficha ("Lo que dicen"), no en la lista |
| Nota de la crítica agregada y número de reseñas | AOTY: puntuación de la crítica y número de reseñas por disco en sus rankings | ✅ nota media de las reseñas encontradas y su número |
| Nota de usuarios, valoraciones, listas, foros | AOTY (perfiles con valoraciones, listas, seguidores), RYM (valoración de 0,5 a 5, 1,6 M de listas, foros) | ⛔ requiere cuentas y servidor; fuera del alcance de una web estática sin coste. Sustituto: "Mi lista" en el móvil |
| Rankings por género y año (y década, histórico) | AOTY: por género y año/década/todo; RYM: por año, género, subgénero, formato y país | ✅ "Lo mejor del año" filtrable por familia y subgénero (solo 2025–2026: no hay décadas que ordenar) |
| Próximos lanzamientos | AOTY: lista de próximos por fecha | ✅ "Próximamente" + calendario de salidas + .ics |
| Taxonomía de géneros jerárquica | RYM: géneros y subgéneros editados por la comunidad; AllMusic: ~1.400 subgéneros (dato antiguo) | ✅ taxonomía cerrada y propia, familia → grupo → subgénero, con alias y descripciones |
| Descriptores / estados de ánimo | RYM: descriptores votados; AllMusic: estilos, tono | 🟡 no se muestran; tenemos las etiquetas de las fuentes → **se añaden a la ficha** |
| Artistas o discos parecidos | AOTY: artistas similares | 🟡 solo "Del mismo artista" → **se añade "Parecidos"** (mismo subgénero, fechas cercanas) |

Lo que **no** se ha podido comprobar: la ficha de un disco en las cuatro webs, sus apps móviles y
sus filtros exactos de RYM y AllMusic. Con el navegador del usuario se completaría.

## 2. Capas técnicas: alternativas y decisión

| Capa | Alternativas consideradas | Criterio | Decisión | Cambio que se hace ahora |
|---|---|---|---|---|
| Almacenamiento | Base de datos gestionada; SQLite (+ Datasette); JSON versionado en git ([git scraping](https://simonwillison.net/2020/Oct/9/git-scraping/)) | Coste 0, sin servidor, historial auditable, miles de discos | JSON en git | — |
| Ejecución | Servidor propio; funciones en la nube; GitHub Actions | Coste 0, programable, reanudable | GitHub Actions + orquestador reanudable | — |
| Lectura de webs | Scrapy; navegador automatizado; requests + BeautifulSoup/lxml con configuración | Respetar `robots.txt` ([RFC 9309](https://www.rfc-editor.org/rfc/rfc9309)) y no saltar protecciones; poco volumen | requests + lxml, lectores genéricos configurables | — |
| Identificación | Solo nombre; MusicBrainz (MBID) | Precisión | Normalización + similitud + MBID | Medir aciertos (tarea pendiente) |
| Clasificación | Solo reglas; modelo propio entrenado; LLM libre; híbrido | Precisión, coste 0, lista cerrada | Reglas + Wikidata + LLM (plan Pro) con respuesta validada | Medir aciertos con muestra revisada (pendiente) |
| Web | Framework con compilación (React, Svelte, Astro); JavaScript sin framework | Carga rápida en móvil, nada que mantener, sin compilación | JavaScript sin framework + PWA | — |
| Búsqueda | Índice de texto completo (Pagefind, Lunr); búsqueda difusa (Fuse.js); subcadena | Pocos miles de discos: cabe en memoria | Subcadena normalizada | **Por palabras en cualquier orden** ("price margo" encuentra "Margo Price") |
| Imágenes | Una sola resolución; `srcset` según la densidad de pantalla | Nitidez en móviles (pantallas 2x–3x) sin pesar más en las normales | Una sola resolución | **`srcset`**: 250 px y 500 px; el navegador elige |
| Accesibilidad | Revisión manual; auditoría automática ([WCAG 2.1](https://www.w3.org/TR/WCAG21/), axe) | Comprobable en cada cambio | axe en la prueba de navegador | Hecho (27-nov): 0 infracciones |
| Rendimiento | Medir peso; [Core Web Vitals](https://web.dev/articles/vitals) con Lighthouse | Experiencia en móvil | Índice ligero (115 KB) + fichas por mes | Lighthouse pendiente |
| Pruebas | Solo manuales; unitarias; + extremo a extremo + navegador | Detectar fallos antes de publicar | pytest + Playwright + axe en CI, cobertura ≥ 70 % | Hecho |
| IA | API de pago; LLM local; Claude con el plan Pro (Claude Code) | Sin gasto | Plan Pro + Wikidata | Hecho |

## 3. Cambios que salen de este estudio

1. Ficha: **"Parecidos"** (discos con algún subgénero en común y fecha cercana) y **etiquetas de las fuentes** (descriptores).
2. Búsqueda por palabras en cualquier orden.
3. Portadas nítidas en pantallas de alta densidad (`srcset`).
4. Pendiente de datos completos: medir aciertos de clasificación y de unión de duplicados, cobertura por campo, Lighthouse.
