# Progreso (se actualiza en cada paso)

Si la sesión se corta, la siguiente empieza por aquí. Cada línea de "Hecho" está subida a GitHub.

## Objetivo actual

**Validación automática y en profundidad de todas las capas y procesos frente a todos los requisitos**
(bloque V de `docs/plan.md`), y después la web nueva (W1–W7). Pedido por el usuario el 28-nov-2026:
"revisar todo automático y al 100 % en profundidad, de todas las capas y procesos; todo reanudable".

## Pasos

| # | Paso | Estado |
|---|---|---|
| 1 | `CLAUDE.md` + este archivo (reanudar sin perder nada) | ✅ |
| 2 | `data/requisitos.yaml`: los 140 requisitos (datos R1–R40, revisión de mensajes M1–M11, web A–K, procesos P) con su capa y su comprobación automática | ✅ |
| 3 | `scraper/validar.py`: motor de comprobaciones → `data/validacion.json` + `docs/validacion.md` (semáforo por capa y por requisito) | ✅ 40 comprobaciones; pruebas en `tests/test_validar.py` |
| 4 | Comprobaciones con los datos que ya hay: duplicados (V2), cobertura de campos (V6), coherencia con fuentes (V4b), formato y fechas | ✅ primer resultado: 44 cumplen, 5 no cumplen (años escritos a mano, portadas 80 %, reseñas sin frase, sin canciones, cobertura), 79 sin datos (la web aún no informa) |
| 5 | Conjunto de referencia de la clasificación (`data/revision_clasificacion.csv` con subgéneros esperados) y su comprobación semanal (V4c) | ✅ 53 discos con respuesta esperada; hoy 79,2 % exactamente bien (mínimo 85 %): sobran subgéneros de etiquetas débiles de MusicBrainz → tarea de mejora medible |
| 6 | Acuerdo con el género de Wikipedia y de MusicBrainz/Discogs (V4a) | ✅ Wikipedia: 98,1 % (155/158) |
| 7 | Historial semana a semana y saltos por fuente, familia y motivo de descarte (V3) | 🟡 historial y avisos hechos (`data/historial_validacion.json`); falta el aviso de "descartado con ≥ 2 reseñas especializadas" |
| 8 | Descubrimiento frente a referencias externas: Metacritic, AnyDecentMusic (V1) | ✅ `scraper/referencias.py` (fase `referencias`): Metacritic "All New Music" 2026 → 97 en la web, **7 perdidos (6,7 %)**, 11 sin poder saber su género; lista de perdidos en `docs/validacion.md` |
| 9 | Reseñas frente a AnyDecentMusic (V5) | ✅ `scraper/resenas.py`: cada disco con página en AnyDecentMusic recibe **todas** sus reseñas (medio, nota, frase, enlace original): U2 pasa de 3 a 21. Comprobación `resenas_cobertura`: 52,5 % de los publicados con reseña. Falta: leer el archivo de ADM (solo hay páginas de los discos actuales: 15) |
| 10 | Web: pruebas de contenido + capturas automáticas de cada pantalla en cada publicación (V7) | ✅ resultados por requisito + capturas en `docs/capturas/` (portada, ficha y lo mejor; móvil y escritorio) en cada ejecución |
| 11 | Fase `validar` en el orquestador y semáforo en el resumen de la Action (V8) | ✅ fase `validar` en `scraper/pipeline.py`; en la Action: prueba en navegador → validar → guarda y pone el semáforo en el resumen |
| 12 | W1 portada y tarjeta (con capturas al usuario) | 🟡 hecha y con todas sus comprobaciones en verde; **encontrado y corregido el fallo de "sin carátulas"**: el marcador tapaba la portada aunque cargara (nueva comprobación automática: las portadas cargadas se ven). Falta: OK del usuario con capturas y publicar |
| 13 | W2 página del disco | ⬜ |
| 14 | W3–W7 | ⬜ |
| 16 | Listas de fin de año del año en curso también descubren discos | ✅ código y configuración (`descubrir_en_listas_anuales`); comprobándose con una recogida real |
| 17 | Fuentes que sustituyen a Heavy Harmonies | ✅ Ultimate Classic Rock y Burning Minds/Art of Melody (`docs/fuentes.md`) |
| 15 | Por qué faltan los discos perdidos | ✅ 2 eran fallos de comparación y 1 un duplicado (corregidos: mismo nombre con "&", "and", "the"); quedan 5 reales con su causa |

## Avisos abiertos (los detectó la validación automática)

- **Heavy Harmonies** (principal fuente de AOR) sirve a las máquinas de GitHub unas reglas (robots.txt) que no
  permiten leerla; desde otras redes sí. Se respeta (regla del usuario). Tarea: **buscar fuentes de AOR que la
  sustituyan** (E1).
- Metal Planet y Blues Rock Review salieron vacías en la primera ejecución en GitHub (vigilar la próxima).
- Punk, indie y cantautores no tienen fuentes especializadas propias (E1).
- "First Songs" de Michael Hurley (1964, Folkways) sale como novedad de esta semana: revisar por qué no se descartó como reedición.
- 5 discos perdidos frente a Metacritic (28-nov): The Mary Wallopers (solo sale en listas de fin de año: usarlas
  también para descubrir), Formal Sppeedwear, Faust, Dis Fig, "Miley" (ninguna fuente los tiene: buscar fuentes de
  krautrock/experimental, indie e industrial). Editors, Los Bitchos, Echo & the Bunnymen y Neil Young sí estaban:
  eran fallos de comparación ("&", "and", "the"), ya corregidos con `util.clave_nombre`.

## Publicado en `main`

- 28-nov-2026: petición #11 fusionada. Desde ahora **cada ejecución en GitHub valida todas las capas** (fases
  `referencias` y `validar`, prueba en navegador y semáforo en el resumen de la Action).

## Último paso hecho

Pasos 3, 4 y parte del 7 (28-nov-2026). Hallazgos reales: 12 direcciones con el año escrito a mano (impide cargar 2025 cambiando un número); portadas 80 %; punk, indie y cantautores sin fuentes especializadas propias.

## Siguiente paso

**W1** (portada y tarjeta nuevas): criterios de aceptación ya escritos en `tests/e2e/web.mjs` (A1, A2, A4, A5, A6,
A7, A9, B1–B4, I1, I4). Hacerlos pasar en `site/app.js`, `site/index.html`, `site/styles.css`; capturas de móvil al
usuario antes de publicar. En paralelo (máquina): comprobar en el log de la recogida que entra The Mary Wallopers.
Pendientes después: clasificación al 85 % en la muestra de referencia; MelodicRock.com y Pride & Joy; archivo de
AnyDecentMusic; fuentes de krautrock/experimental, indie e industrial.
