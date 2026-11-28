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
| 5 | Conjunto de referencia de la clasificación (`data/revision_clasificacion.csv` con subgéneros esperados) y su comprobación semanal (V4c) | ⬜ |
| 6 | Acuerdo con el género de Wikipedia y de MusicBrainz/Discogs (V4a) | ⬜ |
| 7 | Historial semana a semana y saltos por fuente, familia y motivo de descarte (V3) | 🟡 historial y avisos hechos (`data/historial_validacion.json`); falta el aviso de "descartado con ≥ 2 reseñas especializadas" |
| 8 | Descubrimiento frente a referencias externas: Metacritic, AnyDecentMusic (V1) | ⬜ |
| 9 | Reseñas frente a AnyDecentMusic (V5) | ⬜ |
| 10 | Web: pruebas de contenido + capturas automáticas de cada pantalla en cada publicación (V7) | ⬜ |
| 11 | Fase `validar` en el orquestador y semáforo en el resumen de la Action (V8) | ⬜ |
| 12 | W1 portada y tarjeta (con capturas al usuario) | ⬜ |
| 13 | W2 página del disco | ⬜ |
| 14 | W3–W7 | ⬜ |

## Último paso hecho

Pasos 3, 4 y parte del 7 (28-nov-2026). Hallazgos reales: 12 direcciones con el año escrito a mano (impide cargar 2025 cambiando un número); portadas 80 %; punk, indie y cantautores sin fuentes especializadas propias.

## Siguiente paso

Paso 10: que la prueba en navegador (`tests/e2e/web.mjs`) escriba `data/validacion_web.json` con el resultado de cada
comprobación `web:NOMBRE` de `data/requisitos.yaml` (hoy 79 requisitos salen "sin datos" por esto). Después, paso 11.
