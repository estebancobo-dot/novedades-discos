# Plan de trabajo

Fuente de verdad del plan. Cada tarea tiene: **entradas** (de qué depende), **salida**, **cómo se
valida** (criterio comprobable), **quién** la hace y **estado**. Actualizado el 28-nov-2026.

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
| A1 | Recogida completa (fuentes, radares, listas anuales, MusicBrainz, Bandcamp) | `fuentes.yaml`, `config.yaml`, cachés | `data/candidatos.json`, `estado_fuentes.json`, `listas_anuales.json` | Todas las fuentes "ok" o con motivo; 0 bloqueos nuevos sin anotar; discos en cada mes de enero a diciembre | máquina (`scraper.pipeline`) | ✅ 66/67 fuentes ok (Rush On Rock: verificación anti-bots, anotada); todos los meses de 2026 y anuncios de 2027 |
| A2 | Etiquetas extra (Deezer, iTunes, Wikidata, Discogs, Last.fm) | A1 | candidatos enriquecidos | Consultas > 0 por servicio, sin bloqueos; baja el % sin subgénero | máquina | ✅ Deezer 3480, Discogs 561, Wikidata 147; 397 discos resueltos. iTunes (403) y Wikidata (429) pararon: respetado; iTunes se vuelve a probar la semana que viene a 1/4 s |
| A3 | Consolidar (duplicados, no-novedades) y clasificar | A2, `taxonomia.yaml`, `mapeo_etiquetas.csv` | `data/discos.json`, `descartados.json` | ≥ 75 % con subgénero; coherencia con fuentes especializadas ≥ 90 %; duplicados dudosos revisados uno a uno | máquina + revisión mía | ✅ 85 % con subgénero, coherencia 94 %; 15 parejas dudosas revisadas → 3 reglas nuevas (abreviaturas, título idéntico, ediciones ampliadas); quedan 9 que son discos distintos |
| A4 | Mapear etiquetas nuevas | etiquetas pendientes de A3 | `mapeo_etiquetas.csv` | 0 pendientes o justificadas; ids validados contra la taxonomía (automático) | Wikidata + yo (plan Pro, en sesión) | ✅ **0 pendientes**: 1517 revisadas en sesión (306 a subgénero), 3202 por la regla "sin palabra de género" (muestra revisada); 0 ids rechazados |
| A5 | Informe | A3–A4 | `docs/informe.md` | Todas las secciones con datos de enero a diciembre; cifras coherentes entre secciones | máquina | ⬜ |
| A6 | Web con los datos de 2026 | A5 | `site/data/*` | Pruebas de navegador en verde, 0 infracciones de accesibilidad, revisión visual en móvil | máquina + yo | ⬜ |
| A7 | "Lo mejor del año" con 2026 | A3 + listas anuales | vista en la web | Ranking 2026 coherente (discos con más reseñas/nota/listas arriba); 2025 por listas | yo | ⬜ |

### Bloque B · Calidad medida

| ID | Tarea | Entradas | Salida | Cómo se valida | Quién | Estado |
|---|---|---|---|---|---|---|
| B1 | Revisar una muestra de 60 discos (subgéneros correctos, parciales o no) | A3 | `data/revision_clasificacion.csv` + aciertos en el informe | Objetivo: ≥ 85 % correctos o parciales; cada error explicado y, si es de reglas, corregido | yo (plan Pro, en sesión) | ✅ 98 % correctos o parciales (79 % correctos); 4 causas corregidas en las reglas (ver abajo) |
| B2 | Revisar descartes por regla (muestra de cada motivo) | A3 | notas en el informe | Ningún disco nuevo descartado por error en la muestra | yo | ⏳ revisados los 30 motivos; 4 fallos encontrados y corregidos (ver abajo); falta comprobar el resultado de la nueva recogida |
| B3 | Rendimiento de la web (Lighthouse, móvil) | web actual | cifras en `docs/requisitos.md` | Rendimiento ≥ 90 y accesibilidad ≥ 95 en móvil | yo | 🟡 hecho: 83–87 (antes 56) y accesibilidad 100; repetir con la web publicada |
| B4 | Cobertura por campo, coherencia, duplicados | A3 | informe § Calidad | Se publica cada semana | máquina | ✅ (con 5 meses) |

### Bloque C · Publicación

| ID | Tarea | Entradas | Salida | Cómo se valida | Quién | Estado |
|---|---|---|---|---|---|---|
| C1 | Petición para pasar los cambios a `main` | A6, B1 | petición en GitHub | Pruebas de GitHub en verde | yo | ⬜ |
| C2 | Aprobar la petición y activar GitHub Pages | C1 | web pública | Settings → Pages → Source: GitHub Actions | 👤 | ⬜ |
| C3 | Primera ejecución de la Action en `main` | C2 | web publicada + datos | Ejecución en verde; la web abre en el móvil; resumen sin fuentes nuevas con problemas | máquina (👤 la lanza o espera al sábado) | ⬜ |

### Lo que encontraron B1 y B2 (28-nov) y cómo se corrigió

| Problema | Ejemplo | Corrección | Prueba |
|---|---|---|---|
| Disco y sencillo con el mismo nombre en MusicBrainz: a veces se cogía el sencillo y el disco se descartaba | Willie Nelson – *Dream Chaser* | A igualdad, gana el disco (`musicbrainz.py`); se repiten las 338 búsquedas que dieron sencillo/EP | `test_mb_disco_y_sencillo_con_el_mismo_nombre_elige_el_disco` |
| "¿Es de nuestros géneros?" no miraba la tabla de etiquetas: screamo, bedroom pop… contaban como "otro género" | Roman Candle (screamo) | La comprobación usa también `mapeo_etiquetas.csv`; "electropop" pasa a "ninguno" (traía Pitbull y K-pop) | prueba de extremo a extremo |
| Webs especializadas marcadas como mixtas: sus discos sin etiquetas se perdían | Blues Blast (90), Loudwire (108), Blues Rock Review (15) | `familia_sin_subgenero` en `fuentes.yaml`: sin etiquetas de género, la familia de la web | `test_familia_por_defecto_de_fuente_mixta_solo_sin_genero_ajeno` |
| "Box set" en la descripción de un disco nuevo (formatos de venta) se leía como reedición | Darkthrone – *Pre-Historic Metal* | Regla estricta para descripciones largas (`reedicion_en_descripcion`) | `test_reedicion_en_descripciones_largas_...` |
| La categoría amplia de Discogs "Folk, World, & Country" daba "contemporary folk" | Morgan Myles (country) | Se ignora entera; "country"/"blues" explícitos suman su familia | `test_categoria_amplia_de_discogs_...` |
| "Experimental" o "avant-garde" a secas metían en metal discos de electrónica, clásica o hip hop | Hildur Guðnadóttir, Skrillex | Subgéneros frontera: solos no bastan en fuentes mixtas | revisados los 59 que cambian |
| Reediciones que la fuente etiqueta "Reissues"/"Box sets" | Rainbow – *In Concert 1976* | `etiquetas_no_nuevo` en `config.yaml` | `test_la_fuente_lo_etiqueta_como_reedicion_o_caja` |

Decisiones que no se tomaron (y por qué): **no** recortar subgéneros con poco peso (quitaba tantos buenos
como malos: The Jayhawks perdía "americana"); **no** poner subgénero por defecto a Heavy Harmonies (sería
inventar: mezcla hard rock, AOR, metal y glam). Errores conocidos que quedan: Blackhaine (rap) entra en
Blues por una etiqueta de MusicBrainz; Kontrast – *Imperium – Proteus* se trató como edición ampliada (dudoso).

## Medio plazo (próximas semanas): funcionamiento solo y mejora continua

| ID | Tarea | Entradas | Salida | Cómo se valida | Quién | Estado |
|---|---|---|---|---|---|---|
| D1 | Token de Claude Code (plan Pro) para mapear etiquetas en la Action | 👤 `claude setup-token` | secreto `CLAUDE_CODE_OAUTH_TOKEN` | La Action semanal aplica respuestas válidas (paso "Claude clasifica") | 👤 (opcional) | ⬜ menos necesario: desde el 28-nov la regla "sin palabra de género" resuelve sola los nombres (85 % de las etiquetas nuevas); las pocas con palabra de género esperan a la Action con token o a una sesión, sin bloquear nada (salen en "Sin subgénero") |
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
