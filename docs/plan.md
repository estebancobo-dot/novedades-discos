# Plan de trabajo

Fuente de verdad del plan. Cada tarea tiene: **entradas** (de qué depende), **salida**, **cómo se
valida** (criterio comprobable), **quién** la hace y **estado**. Actualizado el 27-nov-2026.

Estados: ✅ hecha y validada · ⏳ en curso · ⬜ pendiente · 👤 necesita al usuario.

## Cómo encajan (qué va en paralelo y qué no)

```
            ┌────────────── en paralelo, sin esperar a nada ───────────────┐
            │ E1 fuentes nuevas · B3 rendimiento · documentación · pruebas  │
            └──────────────────────────────────────────────────────────────┘
A1 recoger ─► A2 etiquetas extra ─► A3 consolidar+clasificar ─► A4 mapear ─► A3' reclasificar ─► A5 informe ─► A6 web
   (fuentes en paralelo,              (servicios en paralelo)                                       │
    radar en paralelo,                                                                               ▼
    MusicBrainz en paralelo)                                   B1 muestra revisada ─► B2 ─► C1 petición a main ─► 👤 C2 Pages ─► C3 1.ª Action
```

- **Lo que no puede ser paralelo:** cada fase usa la salida de la anterior (no se puede clasificar
  un disco antes de recogerlo). Y cada web tiene un ritmo máximo: MusicBrainz 1 petición/1,1 s,
  Bandcamp 1/4 s (pedido por el usuario), iTunes 1/3,1 s.
- **Lo que sí va en paralelo:** dentro de cada fase, las webs distintas a la vez (6 fuentes, 4
  consultas a MusicBrainz, 6 discos en las etiquetas extra), y mi trabajo (pruebas, documentación,
  mejoras) mientras la máquina recoge.

## Corto plazo (esta semana): datos de 2026, calidad y publicación

### Bloque A · Datos de todo 2026

| ID | Tarea | Entradas | Salida | Cómo se valida | Quién | Estado |
|---|---|---|---|---|---|---|
| A1 | Recogida completa (fuentes, radares, listas anuales, MusicBrainz, Bandcamp) | `fuentes.yaml`, `config.yaml`, cachés | `data/candidatos.json`, `estado_fuentes.json`, `listas_anuales.json` | Todas las fuentes "ok" o con motivo; 0 bloqueos nuevos sin anotar; discos en cada mes de enero a diciembre | máquina (`scraper.pipeline`) | ⏳ |
| A2 | Etiquetas extra (Deezer, iTunes, Wikidata, Discogs, Last.fm) | A1 | candidatos enriquecidos | Consultas > 0 por servicio, sin bloqueos; baja el % sin subgénero | máquina | ⬜ |
| A3 | Consolidar (duplicados, no-novedades) y clasificar | A2, `taxonomia.yaml`, `mapeo_etiquetas.csv` | `data/discos.json`, `descartados.json` | ≥ 75 % con subgénero; coherencia con fuentes especializadas ≥ 90 %; duplicados dudosos revisados uno a uno | máquina + revisión mía | ⬜ |
| A4 | Mapear etiquetas nuevas | etiquetas pendientes de A3 | `mapeo_etiquetas.csv` | 0 pendientes o justificadas; ids validados contra la taxonomía (automático) | Wikidata + yo (plan Pro, en sesión) | ⬜ |
| A5 | Informe | A3–A4 | `docs/informe.md` | Todas las secciones con datos de enero a diciembre; cifras coherentes entre secciones | máquina | ⬜ |
| A6 | Web con los datos de 2026 | A5 | `site/data/*` | Pruebas de navegador en verde, 0 infracciones de accesibilidad, revisión visual en móvil | máquina + yo | ⬜ |
| A7 | "Lo mejor del año" con 2026 | A3 + listas anuales | vista en la web | Ranking 2026 coherente (discos con más reseñas/nota/listas arriba); 2025 por listas | yo | ⬜ |

### Bloque B · Calidad medida

| ID | Tarea | Entradas | Salida | Cómo se valida | Quién | Estado |
|---|---|---|---|---|---|---|
| B1 | Revisar una muestra de 60 discos (subgéneros correctos, parciales o no) | A3 | `data/revision_clasificacion.csv` + aciertos en el informe | Objetivo: ≥ 85 % correctos o parciales; cada error explicado y, si es de reglas, corregido | yo (plan Pro, en sesión) | ⬜ |
| B2 | Revisar descartes por regla (muestra de cada motivo) | A3 | notas en el informe | Ningún disco nuevo descartado por error en la muestra | yo | ⬜ |
| B3 | Rendimiento de la web (Lighthouse, móvil) | web actual | cifras en `docs/requisitos.md` | Rendimiento ≥ 90 y accesibilidad ≥ 95 en móvil | yo | ⬜ (en paralelo) |
| B4 | Cobertura por campo, coherencia, duplicados | A3 | informe § Calidad | Se publica cada semana | máquina | ✅ (con 5 meses) |

### Bloque C · Publicación

| ID | Tarea | Entradas | Salida | Cómo se valida | Quién | Estado |
|---|---|---|---|---|---|---|
| C1 | Petición para pasar los cambios a `main` | A6, B1 | petición en GitHub | Pruebas de GitHub en verde | yo | ⬜ |
| C2 | Aprobar la petición y activar GitHub Pages | C1 | web pública | Settings → Pages → Source: GitHub Actions | 👤 | ⬜ |
| C3 | Primera ejecución de la Action en `main` | C2 | web publicada + datos | Ejecución en verde; la web abre en el móvil; resumen sin fuentes nuevas con problemas | máquina (👤 la lanza o espera al sábado) | ⬜ |

## Medio plazo (próximas semanas): funcionamiento solo y mejora continua

| ID | Tarea | Entradas | Salida | Cómo se valida | Quién | Estado |
|---|---|---|---|---|---|---|
| D1 | Token de Claude Code (plan Pro) para mapear etiquetas en la Action | 👤 `claude setup-token` | secreto `CLAUDE_CODE_OAUTH_TOKEN` | La Action semanal aplica respuestas válidas (paso "Claude clasifica") | 👤 (opcional) | ⬜ |
| D2 | Vigilancia semanal | Action | resumen de cada ejecución | Si una fuente sale "vacía", "bloqueada" o "error" dos semanas seguidas, se revisa su patrón | máquina + yo | ⬜ |
| E1 | Búsqueda continua de fuentes (synth/dark, punk, blues, cantautores) | `docs/fuentes.md` | fuentes nuevas probadas | Cada fuente nueva probada con `scraper.probar` y documentada con su motivo | yo | ⏳ continuo |
| E2 | Listas de fin de año 2026 (salen en diciembre–enero) | Year End Lists, plantillas por año | "Lo mejor de 2026" con listas | La vista muestra las listas de 2026 | máquina (automático) | ⬜ |
| F1 | Revisar AOTY, RYM y AllMusic con el navegador del usuario | 👤 navegador | `docs/estado-del-arte.md` completo | Ficha de disco y filtros de las 4 webs descritos | 👤 + yo | ⬜ (sin PC: hecho lo posible por otras vías) |
| F2 | Mejoras de la web que salgan de F1 y del uso real | F1, opiniones del usuario | cambios en `site/` | Pruebas de navegador y accesibilidad en verde | yo | ⬜ |

## Largo plazo (opcional, a decidir por el usuario)

| ID | Idea | Qué haría falta | Coste |
|---|---|---|---|
| G1 | Años anteriores (2025, 2024…) completos | Más ventana en `config.yaml`; más horas de recogida | 0 € |
| G2 | Recomendaciones a partir de "Mi lista" | Solo en el navegador, con subgéneros y parecidos | 0 € |
| G3 | Avisos (correo o móvil) de discos de tus artistas | RSS ya existe; avisos al móvil requieren un servicio externo | 0 € con RSS |
| G4 | Notas y listas de usuarios | Cuentas y servidor: deja de ser una web estática gratuita | coste y mantenimiento |

## Hecho y validado

| ID | Tarea | Cómo se validó |
|---|---|---|
| H1 | Fuentes verificadas (≈70) y documentadas | Cada una probada con el robot real (`docs/fuentes.md`) |
| H2 | Taxonomía de 8 familias, alias y mapeo de etiquetas | Prueba de coherencia; clasificación de 5 meses (76 %) |
| H3 | Web: cuadrícula, ficha, filtros, Mi lista, orden, calendario, lo mejor, RSS, .ics, app instalable | 50 comprobaciones en navegador (móvil y escritorio) |
| H4 | Robustez: reanudar, lecturas guardadas, escrituras atómicas, 429, fuentes que fallan | Pruebas unitarias y de extremo a extremo |
| H5 | Pruebas en GitHub en cada envío (cobertura ≥ 70 %, accesibilidad WCAG 2.1 AA) | Ejecuciones en verde en GitHub |
| H6 | LLM solo con el plan Pro; API de pago desactivada | Pruebas con cliente falso |
| H7 | Velocidad: fuentes, radar y etiquetas en paralelo sin pasar del ritmo de cada web | Prueba de ritmo con hilos; recogida real |
| H8 | Calidad medida en el informe y consolidación (duplicados, no-novedades) | Revisión manual de cada unión y descarte |
