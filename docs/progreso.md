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
| 9 | Reseñas frente a AnyDecentMusic (V5) | ⬜ |
| 10 | Web: pruebas de contenido + capturas automáticas de cada pantalla en cada publicación (V7) | 🟡 la prueba en navegador escribe `data/validacion_web.json` por requisito, con criterios de aceptación de W1/W2/W3 (hoy fallan: es lo correcto); faltan las capturas automáticas |
| 11 | Fase `validar` en el orquestador y semáforo en el resumen de la Action (V8) | ✅ fase `validar` en `scraper/pipeline.py`; en la Action: prueba en navegador → validar → guarda y pone el semáforo en el resumen |
| 12 | W1 portada y tarjeta (con capturas al usuario) | ⬜ |
| 13 | W2 página del disco | ⬜ |
| 14 | W3–W7 | ⬜ |

## Último paso hecho

Pasos 3, 4 y parte del 7 (28-nov-2026). Hallazgos reales: 12 direcciones con el año escrito a mano (impide cargar 2025 cambiando un número); portadas 80 %; punk, indie y cantautores sin fuentes especializadas propias.

## Siguiente paso

Paso 9: reseñas frente a AnyDecentMusic (sus páginas de disco listan todas las reseñas: comparar el número con las
nuestras). Después: capturas automáticas de cada pantalla (resto del 10); arreglar los 7 discos perdidos (qué fuente
los debía traer); subir la clasificación del 79 % al 85 % en la muestra de referencia (etiquetas débiles de
MusicBrainz). Luego W1 con capturas al usuario.
