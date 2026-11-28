# Validación automática · 2026-11-28

Generado por `python -m scraper.validar` (cada semana en la Action). Cada requisito de `data/requisitos.yaml` se comprueba solo, con los datos; nada se revisa a mano.

🟢 cumple · 🟡 aviso · 🔴 no cumple · ⚪ sin datos todavía · ⚫ sin comprobación automática

## Por capa

| Capa | 🟢 | 🟡 | 🔴 | ⚪ | ⚫ |
|---|---:|---:|---:|---:|---:|
| alcance | 1 | 0 | 0 | 0 | 0 |
| clasificacion | 6 | 1 | 0 | 0 | 0 |
| datos | 1 | 0 | 4 | 0 | 3 |
| descubrimiento | 1 | 0 | 0 | 1 | 0 |
| estudio | 2 | 0 | 0 | 0 | 0 |
| fuentes | 12 | 1 | 0 | 0 | 4 |
| informe | 1 | 0 | 0 | 0 | 0 |
| procesos | 10 | 1 | 1 | 1 | 2 |
| publicacion | 1 | 0 | 0 | 0 | 0 |
| reglas | 3 | 0 | 0 | 0 | 0 |
| validacion | 1 | 0 | 0 | 4 | 0 |
| web | 5 | 0 | 0 | 73 | 0 |

**Total: 140 requisitos** · cumplen 44 · aviso 3 · no cumplen 5 · sin datos 79 · sin comprobación 9

## Comprobaciones que fallan o avisan

- 🔴 **anios_por_plantilla**: direcciones con el año escrito a mano — 12
    - scm_radar: https://savingcountrymusic.com/release-radar-most-anticipated-new-country-albums-for-2026/
    - scm_radar: https://savingcountrymusic.com/release-radar-most-anticipated-new-albums-for-2nd-half-of-2026/
    - scm_radar: https://savingcountrymusic.com/release-radar-most-anticipated-new-albums-for-final-portion-of-2026/
    - loudwire: https://loudwire.com/2026-hard-rock-metal-album-release-calendar/
    - loudwire: https://loudwire.com/2027-hard-rock-metal-album-release-calendar/
- 🔴 **cobertura_campos**: 3787 discos ya publicados — portada 80.0, fecha_exacta 83.2, sello 73.3, pistas 82.2, subgenero 80.6, enlace_escucha 78.4
    - portada: 80.0 % (mínimo 95 %)
    - fecha_exacta: 83.2 % (mínimo 85 %)
    - enlace_escucha: 78.4 % (mínimo 80 %)
- 🔴 **cobertura_portadas**: mínimo 95 % — 80.0
- 🔴 **reseñas_con_frase**: 0 de 2382 reseñas con frase — 0.0
- 🔴 **canciones**: 0 de 3896 fichas con lista de canciones — 0.0
- 🟡 **mapeo_sin_pendientes**: etiquetas pendientes que dejan discos sin subgénero; ids que no existen — pendientes 353, en_discos_sin_subgenero 2, ids_invalidos 0
    - Franklin
    - slide
- 🟡 **fuentes_por_familia**: fuentes especializadas por familia (mínimo 5; además cuentan las generales y los radares) — country 21, hardrock 16, rockmetal 4, blues 5, synthdark 4
    - rockmetal: 4
    - punkgarage: 0
    - indiepop: 0
    - synthdark: 4
    - cantautores: 0
- 🟡 **pruebas_por_fuente**: cada disco con fuente y fecha; falta la confianza por fuente (P7) — 59.7

## Todos los requisitos

| ID | Requisito | Capa | Estado |
|---|---|---|---|
| R1 | Web de novedades de country/americana/folk y hard rock/AOR | alcance | 🟢 cumple |
| R2 | Solo discos en inglés | reglas | 🟢 cumple |
| R3 | "Mejor que el mercado" frente a AOTY (más discos, antes, subgénero correcto) y decirlo si  | descubrimiento | ⚪ sin datos todavía |
| R4 | Descartar EP | reglas | 🟢 cumple |
| R5 | Descartar reediciones / remasters | reglas | 🟢 cumple |
| R6 | Todo 2026 (enero–diciembre) además de los 5 últimos meses | descubrimiento | 🟢 cumple |
| R7 | "Lo mejor de cada año" | web | 🟢 cumple |
| R8 | Taxonomía cerrada del usuario con alias | clasificacion | 🟢 cumple |
| R9 | Familias "en foco" de agenda-conciertos (rock y metal, punk y garage, indie y pop-rock, bl | clasificacion | 🟢 cumple |
| R10 | Etiqueta nueva → LLM una sola vez → mapeo_etiquetas.csv | clasificacion | 🟡 aviso |
| R11 | Nunca crear subgéneros; proponerlos en el informe | clasificacion | 🟢 cumple |
| R12 | LLM solo con el plan Pro, sin pagar API | procesos | 🟢 cumple |
| R13 | Clasificación correcta | clasificacion | 🟢 cumple |
| R14 | Verificar cada fuente propuesta | fuentes | 🟢 cumple |
| R15 | 5 fuentes extra por familia | fuentes | 🟡 aviso |
| R16 | Usar todas las fuentes posibles | fuentes | 🟢 cumple |
| R17 | Bandcamp ≤ 1 petición / 4 s; MusicBrainz ≤ 1 / s | fuentes | 🟢 cumple |
| R18 | Captcha o bloqueo: no saltarlo, avisar | fuentes | 🟢 cumple |
| R19 | Respetar robots.txt | fuentes | 🟢 cumple |
| R20 | No inventar datos ni fuentes | datos | 🟢 cumple |
| R21 | Extensible sin código: nuevas fuentes solo con configuración | fuentes | 🟢 cumple |
| R22 | Wikipedia "List of 2026 albums" | fuentes | 🟢 cumple |
| R23 | Usar los repositorios compartidos (agenda-conciertos, radar de MusicBrainz, Deezer, UI de  | fuentes | 🟢 cumple |
| R24 | Year End Lists; evaluar Musicboard, MusicTaste, Shfl, New Music Tracker | fuentes | 🟢 cumple |
| R25 | Spotify, Tidal | fuentes | ⚫ sin comprobación automática |
| R26 | Artista, título, fecha, sello, subgéneros, etiquetas originales, portada, nº de pistas, ti | datos | 🔴 no cumple |
| R27 | Cuadrícula de portadas por semanas, lo más reciente arriba | web | ⚪ sin datos todavía |
| R28 | Ficha del disco | web | ⚪ sin datos todavía |
| R29 | Filtros: familia, subgénero múltiple, fechas (5 meses por defecto), sello, búsqueda | web | ⚪ sin datos todavía |
| R30 | Pensada para móvil | web | ⚪ sin datos todavía |
| R31 | Estática en GitHub Pages | publicacion | 🟢 cumple |
| R32 | Mejoras de UX del estudio (Mi lista, nota, orden, lista, compartir, calendario .ics, RSS,  | web | ⚪ sin datos todavía |
| R33 | Estudio de las funciones de AOTY, RYM, Metacritic, AllMusic | estudio | 🟢 cumple |
| R34 | Plan corto y OK antes de programar; un commit por fase | procesos | ⚫ sin comprobación automática |
| R35 | Action semanal | procesos | 🟢 cumple |
| R36 | Todo automático, sin sesión ni gasto | procesos | 🟢 cumple |
| R37 | Persistencia, tolerancia a fallos, reanudar | procesos | 🟢 cumple |
| R38 | Escenarios nominales, de borde, esquina y error | procesos | 🟢 cumple |
| R39 | Rendimiento | web | ⚪ sin datos todavía |
| R40 | Secretos fuera del chat y del código | procesos | 🟢 cumple |
| M1 | El informe debe dar: discos por familia y subgénero, % con subgénero, % en Bandcamp, disco | informe | 🟢 cumple |
| M2 | Subgéneros "frontera" (country-blues, southern-gospel, heartland-rock; melodic-metal, powe | clasificacion | 🟢 cumple |
| M3 | Un disco puede tener varios subgéneros | clasificacion | 🟢 cumple |
| M4 | Fuentes concretas de prensa, listados y sellos | fuentes | 🟢 cumple |
| M5 | Preguntas y explicaciones no técnicas | procesos | ⚫ sin comprobación automática |
| M6 | Fuentes de r/Music: Pause & Play, Hello Weimar Republic, Bandcamp Daily, Metacritic, AllMu | fuentes | 🟢 cumple |
| M7 | Repos: albumoftheyearapi, album-of-the-year-analysis, topic "allmusic", radares de Spotify | fuentes | ⚫ sin comprobación automática |
| M8 | Fuentes de agenda-conciertos: Wikipedia, Wikidata, Discogs, MusicBrainz, Last.fm, ReccoBea | fuentes | ⚫ sin comprobación automática |
| M9 | Pruebas de concepto saltándose Cloudflare | fuentes | 🟢 cumple |
| M10 | ¿Tidal tiene API gratis? | fuentes | ⚫ sin comprobación automática |
| M11 | New Music Tracker | estudio | 🟢 cumple |
| A1 | Abrir en "Esta semana" (de viernes a jueves) con discos ya publicados | web | ⚪ sin datos todavía |
| A2 | Secciones: Esta semana · Destacados (mejor nota / más reseñas) · Recientes · Próximos | web | ⚪ sin datos todavía |
| A3 | Cada sección con "ver todo ›" | web | ⚪ sin datos todavía |
| A4 | Próximos lanzamientos aparte, en lista compacta por fecha (sin cuadros grandes) | web | ⚪ sin datos todavía |
| A5 | Sin cuadros de colores con el nombre: si no hay portada, un marcador neutro discreto | web | ⚪ sin datos todavía |
| A6 | Cabecera limpia: nombre, buscar, menú; la fila de meses dentro de Filtros | web | ⚪ sin datos todavía |
| A7 | "Semana del 27 de noviembre · 137 discos" visible | web | ⚪ sin datos todavía |
| A8 | Identidad propia: nombre, logo y estilo que no recuerden a la web de conciertos | web | ⚪ sin datos todavía |
| A9 | "Mejores notas recientes": lista corta con nota, artista y medio | web | ⚪ sin datos todavía |
| A10 | "Discos a seguir": portada + una frase de una reseña con su nota y medio | web | ⚪ sin datos todavía |
| A11 | Sin publicidad ni rastreo | web | 🟢 cumple |
| B1 | Portada real, cuadrada, protagonista | web | ⚪ sin datos todavía |
| B2 | Título del disco (letra con remate) y artista debajo, sin repetir el nombre | web | ⚪ sin datos todavía |
| B3 | Fecha · estilo en una línea | web | ⚪ sin datos todavía |
| B4 | Nota visible tipo Metacritic: cuadro de color (verde ≥ 8, amarillo 6–7,9, rojo < 6) + nº d | web | ⚪ sin datos todavía |
| B5 | Indicador de interés (nº de reseñas/fuentes) en puntos, como la popularidad de NMT | web | ⚪ sin datos todavía |
| B6 | Marca de tipo cuando no es estudio (Directo, Recopilatorio) | web | ⚪ sin datos todavía |
| B7 | Guardar con un toque | web | ⚪ sin datos todavía |
| C1 | Página propia que se puede compartir (hoy es una ventana con #id) | web | ⚪ sin datos todavía |
| C2 | Migas: Artista / Disco | web | ⚪ sin datos todavía |
| C3 | Cabecera: portada + título grande + "de Artista" enlazado + tipo · fecha · sello | web | ⚪ sin datos todavía |
| C4 | Nota media grande + "según N reseñas" | web | ⚪ sin datos todavía |
| C5 | "Qué dice la crítica": medio, nota, fecha, primera frase, "leer reseña" | web | ⚪ sin datos todavía |
| C6 | Acciones: Escuchar luego · Escuchado · Favorito | web | ⚪ sin datos todavía |
| C7 | Géneros y estilos como etiquetas que filtran | web | ⚪ sin datos todavía |
| C8 | Escuchar en Qobuz, TIDAL, Apple Music, Spotify, Deezer, Bandcamp, YouTube | web | ⚪ sin datos todavía |
| C9 | Comprar en Bandcamp / Qobuz | web | ⚪ sin datos todavía |
| C10 | Lista de canciones con duración | web | ⚪ sin datos todavía |
| C11 | "Más de este artista" con portadas | web | ⚪ sin datos todavía |
| C12 | Parecidos | web | ⚪ sin datos todavía |
| C13 | En qué listas de fin de año aparece | web | ⚪ sin datos todavía |
| C14 | Dónde lo vimos (fuentes) y enlace a MusicBrainz | web | ⚪ sin datos todavía |
| C15 | Nota con palabra: "Muy favorable / Favorable / Dividida / Desfavorable" + "según N reseñas | web | ⚪ sin datos todavía |
| C16 | Barra de reseñas positivas / mixtas / negativas con su número | web | ⚪ sin datos todavía |
| C17 | Filtrar las reseñas: todas, positivas, mixtas, negativas | web | ⚪ sin datos todavía |
| C18 | Cada reseña como tarjeta: fecha, nota en cuadro de color, medio, frase, "reseña completa ↗ | web | ⚪ sin datos todavía |
| C19 | Resumen del disco en 1–2 frases | web | ⚪ sin datos todavía |
| C20 | Estados de ánimo y temas | web | ⚪ sin datos todavía |
| D1 | Página del artista con sus discos | web | ⚪ sin datos todavía |
| D2 | Origen ("de Nashville, EE. UU.") | web | ⚪ sin datos todavía |
| D3 | Discografía: álbumes, EP, directos | web | ⚪ sin datos todavía |
| D4 | Seguir al artista → sus novedades arriba en la portada | web | ⚪ sin datos todavía |
| E1 | Periodo: esta semana · 30 días · 90 días · año | web | ⚪ sin datos todavía |
| E2 | Familia (chips) y subgénero dentro | web | ⚪ sin datos todavía |
| E3 | Orden: más nuevos · mejor nota · más reseñados | web | ⚪ sin datos todavía |
| E4 | País del artista | web | ⚪ sin datos todavía |
| E5 | "Solo mis artistas" | web | ⚪ sin datos todavía |
| E6 | Contador de resultados y "cargar más" | web | ⚪ sin datos todavía |
| E7 | Búsqueda por artista, disco o sello | web | ⚪ sin datos todavía |
| E8 | Vista de galería y de lista compacta | web | ⚪ sin datos todavía |
| E9 | Tabla de todos los lanzamientos, ordenable por artista, disco, sello, género y nota | web | ⚪ sin datos todavía |
| E10 | Agrupar por día con una línea de tiempo para saltar de fecha | web | ⚪ sin datos todavía |
| F1 | Lo mejor del año: lista numerada con portada, nota, nº de reseñas | web | ⚪ sin datos todavía |
| F2 | Por familia | web | ⚪ sin datos todavía |
| F3 | Lo mejor del mes y de la semana | web | ⚪ sin datos todavía |
| F4 | Listas de fin de año de la prensa (2019–2025) | web | 🟢 cumple |
| F5 | Orden ponderado por nº de reseñas (que un disco con 1 reseña no gane) | web | 🟢 cumple |
| F6 | Opción "un disco por artista" en los rankings | web | ⚪ sin datos todavía |
| F7 | "Imprescindibles" del mes (los de mejor nota con un mínimo de reseñas) | web | ⚪ sin datos todavía |
| F8 | "Tal día como hoy": discos que cumplen años | web | ⚪ sin datos todavía |
| G1 | Escuchar luego | web | ⚪ sin datos todavía |
| G2 | Escuchados | web | ⚪ sin datos todavía |
| G3 | Favoritos | web | ⚪ sin datos todavía |
| G4 | Seguir artistas | web | ⚪ sin datos todavía |
| G5 | RSS y calendario | web | 🟢 cumple |
| I1 | Títulos con letra con remate; datos con letra sin remate | web | ⚪ sin datos todavía |
| I2 | Paleta sobria con un color de acento | web | ⚪ sin datos todavía |
| I3 | Jerarquía y espacios: una cosa importante por bloque | web | ⚪ sin datos todavía |
| I4 | Iconos propios, sin emojis | web | ⚪ sin datos todavía |
| I5 | Escritorio: rejilla de 4–6 columnas; página del disco en dos columnas | web | ⚪ sin datos todavía |
| I6 | Modo oscuro | web | ⚪ sin datos todavía |
| J1 | Portadas en el 95 % de los publicados (hoy 79 %) | datos | 🔴 no cumple |
| J2 | Primera frase de cada reseña | datos | 🔴 no cumple |
| J3 | Lista de canciones | datos | 🔴 no cumple |
| J4 | Origen del artista | datos | ⚫ sin comprobación automática |
| J5 | Popularidad | datos | ⚫ sin comprobación automática |
| J6 | Discografía del artista | datos | ⚫ sin comprobación automática |
| K1 | Capturas de cada pantalla en móvil y escritorio, enviadas al usuario y aprobadas antes de  | validacion | ⚪ sin datos todavía |
| K2 | Pruebas automáticas de contenido: portada en la primera pantalla, título y artista visible | validacion | ⚪ sin datos todavía |
| K3 | Comparación lado a lado con NMT en las mismas pantallas | validacion | 🟢 cumple |
| K4 | Accesibilidad WCAG 2.1 AA | validacion | ⚪ sin datos todavía |
| K5 | Rendimiento móvil ≥ 90 | validacion | ⚪ sin datos todavía |
| P1 | Cargar un año entero (p. ej. 2025) cambiando solo la configuración | procesos | 🔴 no cumple |
| P2 | Recogida semanal automática | procesos | 🟢 cumple |
| P3 | Auditoría "¿perdemos discos?" cada semana | procesos | ⚪ sin datos todavía |
| P4 | Validación automática del procesamiento | procesos | 🟢 cumple |
| P5 | Estudio del estado del arte repetible | procesos | 🟢 cumple |
| P7 | Cada disco con sus pruebas por fuente (quién lo anunció, cuándo, con qué fecha) y una conf | procesos | 🟡 aviso |
| P6 | Webs que bloquean (AOTY, RYM, AllMusic) | procesos | 🟢 cumple |
