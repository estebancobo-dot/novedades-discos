# Requisitos de la web y plan de rediseño

28-nov-2026. Este documento nace de la crítica del usuario a la web publicada ("sin carátulas, sin reseñas
integradas, puntuaciones poco claras, artistas poco claros, confusa, nada profesional, parece la web de
conciertos"). La crítica es correcta: la web pasaba las pruebas técnicas, pero **nunca se validó visualmente
ni se comparó con las webs de referencia**. Los requisitos de datos y fuentes siguen en `docs/requisitos.md`;
aquí van los de la web.

Estado: ✅ hecho · 🟡 a medias · ❌ falta. Prioridad: **P1** imprescindible para que la web sirva,
**P2** la hace buena, **P3** extra.

## Qué se ha revisado y cómo

Estudio completo, con capturas y fuentes: `docs/estado-del-arte/README.md` (repetible con `node estudio/capturar.mjs`).


| Web | Cómo | Qué se vio |
|---|---|---|
| **New Music Tracker** | Navegador real en móvil, 10 tipos de página | Portada (Esta semana, Destacados, Populares, Recientes), Novedades con filtros, Destacados, picks de usuarios, página de disco, página de artista, géneros, búsqueda, "About" entero |
| Pitchfork | Navegador real en móvil | Lista de reseñas: portada grande, género, título en letra con remate, nota |
| Musicboard | Navegador real | Solo la portada (lo demás es app con cuenta) |
| AOTY, Metacritic (música), RYM, AllMusic | **Bloquean** a cualquier navegador automático (Cloudflare) | Lo que se sabe por su documentación pública y por Wikipedia: nota media de la crítica con color, nº de reseñas, nota de usuarios, listas por año. Revisarlas a fondo necesita el navegador del usuario (tarea F1 del plan) |

Lo que tienen en común las buenas: **la portada manda, el título y el artista se leen al primer vistazo, la
nota se ve sin abrir nada y no hay ruido**.

## 1. Portada (lo primero que se ve)

| ID | Requisito | Referencia | Estado | Prio |
|---|---|---|---|---|
| A1 | Abrir en **"Esta semana"** (de viernes a jueves) con discos ya publicados | NMT | ❌ abre con "Próximamente" | P1 |
| A2 | Secciones: Esta semana · Destacados (mejor nota / más reseñas) · Recientes · Próximos | NMT | ❌ | P1 |
| A3 | Cada sección con "ver todo ›" | NMT | ❌ | P2 |
| A4 | Próximos lanzamientos aparte, en lista compacta por fecha (sin cuadros grandes) | NMT | ❌ | P1 |
| A5 | Sin cuadros de colores con el nombre: si no hay portada, un marcador neutro discreto | NMT, Pitchfork | ❌ | P1 |
| A6 | Cabecera limpia: nombre, buscar, menú; la fila de meses dentro de Filtros | NMT | 🟡 | P1 |
| A7 | "Semana del 27 de noviembre · 137 discos" visible | NMT | 🟡 | P2 |
| A8 | Identidad propia: nombre, logo y estilo que no recuerden a la web de conciertos | usuario | ❌ | P1 |
| A9 | "Mejores notas recientes": lista corta con nota, artista y medio | ADM | ❌ | P1 |
| A10 | "Discos a seguir": portada + una frase de una reseña con su nota y medio | ADM | ❌ | P2 |
| A11 | Sin publicidad ni rastreo | NMT (Metacritic y ADM llenan la página de anuncios) | ✅ | — |

## 2. Tarjeta de disco

| ID | Requisito | Referencia | Estado | Prio |
|---|---|---|---|---|
| B1 | Portada real, cuadrada, protagonista | NMT, Pitchfork | 🟡 79 % de los publicados la tienen; no se ve en la primera pantalla | P1 |
| B2 | **Título del disco** (letra con remate) y **artista** debajo, sin repetir el nombre | NMT, Pitchfork | ❌ hoy el artista sale dos veces | P1 |
| B3 | Fecha · estilo en una línea | NMT | 🟡 | P1 |
| B4 | **Nota visible** tipo Metacritic: cuadro de color (verde ≥ 8, amarillo 6–7,9, rojo < 6) + nº de reseñas | Metacritic, AOTY | ❌ | P1 |
| B5 | Indicador de interés (nº de reseñas/fuentes) en puntos, como la popularidad de NMT | NMT | ❌ | P2 |
| B6 | Marca de tipo cuando no es estudio (Directo, Recopilatorio) | NMT | 🟡 | P3 |
| B7 | Guardar con un toque | NMT | ✅ | — |

## 3. Página del disco

| ID | Requisito | Referencia | Estado | Prio |
|---|---|---|---|---|
| C1 | Página propia que se puede compartir (hoy es una ventana con `#id`) | NMT | 🟡 | P2 |
| C2 | Migas: Artista / Disco | NMT | ❌ | P2 |
| C3 | Cabecera: portada + **título grande** + "de **Artista**" enlazado + tipo · fecha · sello | NMT | ❌ hoy el título sale solo ("45") y el artista debajo pequeño | P1 |
| C4 | **Nota media grande** + "según N reseñas" | Metacritic, AOTY | ❌ | P1 |
| C5 | **"Qué dice la crítica"**: medio, nota, fecha, primera frase, "leer reseña" | Metacritic, AOTY | 🟡 hay medio, enlace y fecha (2.382 reseñas, 866 con nota); falta frase y diseño | P1 |
| C6 | Acciones: Escuchar luego · Escuchado · Favorito | NMT | 🟡 solo "Guardar" | P2 |
| C7 | Géneros y estilos como etiquetas que filtran | NMT | 🟡 | P2 |
| C8 | Escuchar en Qobuz, TIDAL, Apple Music, Spotify, Deezer, Bandcamp, YouTube | NMT | ✅ | — |
| C9 | Comprar en Bandcamp / Qobuz | NMT | 🟡 | P3 |
| C10 | Lista de canciones con duración | NMT | ❌ solo el nº de pistas | P2 |
| C11 | "Más de este artista" con portadas | NMT | ❌ | P2 |
| C12 | Parecidos | — | ✅ | — |
| C13 | En qué listas de fin de año aparece | AOTY | 🟡 | P2 |
| C14 | Dónde lo vimos (fuentes) y enlace a MusicBrainz | NMT | ✅ | — |
| C15 | Nota con palabra: "Muy favorable / Favorable / Dividida / Desfavorable" + "según N reseñas" | Metacritic | ❌ | P1 |
| C16 | Barra de reseñas positivas / mixtas / negativas con su número | Metacritic | ❌ | P1 |
| C17 | Filtrar las reseñas: todas, positivas, mixtas, negativas | Metacritic | ❌ | P2 |
| C18 | Cada reseña como tarjeta: fecha, nota en cuadro de color, medio, frase, "reseña completa ↗" | Metacritic, ADM | ❌ | P1 |
| C19 | Resumen del disco en 1–2 frases | Metacritic, AllMusic | 🟡 hay descripciones de las fuentes | P2 |
| C20 | Estados de ánimo y temas | AllMusic | ❌ (sin datos gratuitos fiables) | P3 |

## 4. Página de artista

| ID | Requisito | Referencia | Estado | Prio |
|---|---|---|---|---|
| D1 | Página del artista con sus discos | NMT | ❌ (hoy solo filtra) | P2 |
| D2 | Origen ("de Nashville, EE. UU.") | NMT | ❌ | P3 |
| D3 | Discografía: álbumes, EP, directos | NMT | ❌ | P3 |
| D4 | Seguir al artista → sus novedades arriba en la portada | NMT | 🟡 "De tus artistas" | P2 |

## 5. Descubrir (listado completo)

| ID | Requisito | Referencia | Estado | Prio |
|---|---|---|---|---|
| E1 | Periodo: esta semana · 30 días · 90 días · año | NMT | 🟡 fechas libres | P1 |
| E2 | Familia (chips) y subgénero dentro | NMT | ✅ | — |
| E3 | Orden: más nuevos · mejor nota · más reseñados | NMT, Metacritic | ✅ | — |
| E4 | País del artista | NMT | ❌ | P3 |
| E5 | "Solo mis artistas" | NMT | 🟡 | P2 |
| E6 | Contador de resultados y "cargar más" | NMT | ✅ | — |
| E7 | Búsqueda por artista, disco o sello | NMT | ✅ | — |
| E8 | Vista de galería y de lista compacta | RYM | ✅ | — |
| E9 | Tabla de todos los lanzamientos, ordenable por artista, disco, sello, género y nota | AllMusic | ❌ | P2 |
| E10 | Agrupar por día con una línea de tiempo para saltar de fecha | ListenBrainz | 🟡 por semanas y meses | P3 |

## 6. Lo mejor

| ID | Requisito | Referencia | Estado | Prio |
|---|---|---|---|---|
| F1 | Lo mejor del año: **lista numerada** con portada, nota, nº de reseñas | AOTY | 🟡 rejilla poco clara | P1 |
| F2 | Por familia | AOTY | ✅ | — |
| F3 | Lo mejor del mes y de la semana | NMT (picks de semana/mes) | ❌ | P2 |
| F4 | Listas de fin de año de la prensa (2019–2025) | — | ✅ | — |
| F5 | Orden ponderado por nº de reseñas (que un disco con 1 reseña no gane) | AOTY | ✅ media bayesiana | — |
| F6 | Opción "un disco por artista" en los rankings | RYM | ❌ | P3 |
| F7 | "Imprescindibles" del mes (los de mejor nota con un mínimo de reseñas) | AOTY (must-hear) | ❌ | P2 |
| F8 | "Tal día como hoy": discos que cumplen años | AOTY (on this day) | ❌ | P3 |

## 7. Lo personal (sin cuentas: se guarda en el móvil)

| ID | Requisito | Referencia | Estado | Prio |
|---|---|---|---|---|
| G1 | Escuchar luego | NMT | ✅ ("Mi lista") | — |
| G2 | Escuchados | NMT | ❌ | P2 |
| G3 | Favoritos | NMT | ❌ | P2 |
| G4 | Seguir artistas | NMT | 🟡 | P2 |
| G5 | RSS y calendario | NMT | ✅ | — |

## 8. Diseño

| ID | Requisito | Referencia | Estado | Prio |
|---|---|---|---|---|
| I1 | Títulos con letra con remate; datos con letra sin remate | NMT, Pitchfork | ❌ | P1 |
| I2 | Paleta sobria con un color de acento | NMT | 🟡 | P1 |
| I3 | Jerarquía y espacios: una cosa importante por bloque | NMT | ❌ | P1 |
| I4 | Iconos propios, sin emojis | NMT | ❌ (📅, ✦) | P2 |
| I5 | Escritorio: rejilla de 4–6 columnas; página del disco en dos columnas | NMT | 🟡 | P2 |
| I6 | Modo oscuro | — | ✅ | — |

## 9. Datos que necesita la web

| ID | Requisito | Fuente gratuita | Estado | Prio |
|---|---|---|---|---|
| J1 | Portadas en el 95 % de los publicados (hoy 79 %) | Deezer, Cover Art Archive, Bandcamp | 🟡 | P1 |
| J2 | Primera frase de cada reseña | el propio RSS de la reseña | ❌ | P1 |
| J3 | Lista de canciones | MusicBrainz | ❌ | P2 |
| J4 | Origen del artista | MusicBrainz | ❌ | P3 |
| J5 | Popularidad | ListenBrainz (la que usa NMT) | ❌ | P3 |
| J6 | Discografía del artista | MusicBrainz | ❌ | P3 |

## 10. Validación (lo que faltó)

| ID | Requisito | Estado |
|---|---|---|
| K1 | Capturas de cada pantalla en móvil y escritorio, **enviadas al usuario y aprobadas antes de publicar** | ❌ → obligatorio desde ahora |
| K2 | Pruebas automáticas de contenido: portada en la primera pantalla, título y artista visibles, nota visible si existe, sin cuadros de color | ❌ |
| K3 | Comparación lado a lado con NMT en las mismas pantallas | ❌ |
| K4 | Accesibilidad WCAG 2.1 AA | ✅ |
| K5 | Rendimiento móvil ≥ 90 | 🟡 83–87 |

## 11. Procesos (lo que no se ve pero decide si la web es fiable)

| ID | Requisito | Cómo está hoy | Estado | Prio |
|---|---|---|---|---|
| P1 | **Cargar un año entero** (p. ej. 2025) cambiando solo la configuración | `ventana.anios_completos: [2025, 2026]` + ejecutar la Action en modo "completa". Radar de MusicBrainz y Deezer por meses, listas de fin de año y archivos paginados de las fuentes ya funcionan por año; **las listas de Wikipedia están escritas a mano para 2026** (hay que pasarlas a plantilla por año). Las fuentes que solo publican RSS no llegan tan atrás: la cobertura de 2025 será menor y se medirá por mes | 🟡 | P1 |
| P2 | **Recogida semanal** automática | Cada sábado: las ≈70 fuentes (RSS, listas, archivos), radar de MusicBrainz y Deezer de las últimas 3 semanas, MusicBrainz y Bandcamp para completar datos; cada día reanuda si algo quedó a medias; guarda y publica sola | ✅ | — |
| P3 | **Auditoría "¿perdemos discos?"** cada semana | Hoy el informe compara la web con cada fuente por mes, pero **no hay una comprobación contra listas externas completas**. Falta: tomar las listas de referencia (Wikipedia del mes con su columna de género, novedades de Metacritic, radar de MusicBrainz), quedarse con los de nuestros géneros y listar **los que no están y por qué** (descartado con motivo, o nunca visto → fuente que falta) | ❌ | P1 |
| P4 | **Validación automática del procesamiento** | (a) Pruebas de código en cada cambio ✅ (≈175 pruebas y 67 en navegador). (b) Comprobaciones de los datos en cada ejecución (formato, duplicados, fechas en la ventana, cada disco con fuente) 🟡. (c) La muestra revisada a mano como **conjunto de referencia**: en cada ejecución se recalcula el acierto y si baja, aviso ❌. (d) Comparar con la semana anterior: si una fuente o una familia cae de golpe, aviso 🟡 | 🟡 | P1 |
| P5 | **Estudio del estado del arte repetible** | `estudio/referencias.yaml` + `node estudio/capturar.mjs`: capturas y estructura de cada web de referencia (en directo o copia de archivo) | ✅ nuevo | — |
| P7 | Cada disco con sus **pruebas por fuente** (quién lo anunció, cuándo, con qué fecha) y una confianza | ArtistTrackarr | 🟡 hay fuentes y fechas, falta la confianza | P2 |
| P6 | Webs que bloquean (AOTY, RYM, AllMusic) | Bloquean a navegadores automáticos; la copia de archivo tampoco llega desde este entorno. No se salta el bloqueo (regla del usuario). Se estudian por su documentación, artículos y el código público que las lee | 🟡 | — |

## Plan, en orden

Cada fase: se construye → **capturas al usuario** → OK → se publica (al subir a `main` se publica solo).

| Fase | Qué | Requisitos | Cómo se valida |
|---|---|---|---|
| **P-a** (a la vez que W1) | Auditoría "¿perdemos discos?" y validación automática con la muestra de referencia | P3, P4 | Sección nueva del informe con los que faltan y por qué; aviso en la Action |
| **W1** | Portada y tarjeta nuevas; identidad propia; tipografía | A1–A11, B1–B5, I1–I4 | Capturas móvil/escritorio; pruebas K2 |
| **W2** | Página del disco nueva, al estilo Metacritic: nota grande con palabra, barra positivas/mixtas/negativas, reseñas como tarjetas con frase | C1–C7, C13, C15–C19, J2 | Capturas de 3 discos (con nota, sin nota, sin portada) |
| **W3** | Lo mejor del año en lista numerada; lo mejor del mes y la semana | F1, F3 | Captura del top 2026 |
| **W4** | Portadas al 95 % (automático en la recogida semanal) | J1 | Cifra en el informe |
| **W5** | Página de artista; seguir artistas; escuchados y favoritos | D1, D4, G2–G4 | Capturas |
| **W6** | Canciones, más del artista, periodo semana/30/90 días | C10, C11, E1, J3 | Capturas |
| W7 | Extras: país, popularidad, discografía, comprar | D2, D3, E4, C9, J4–J6 | — |

W1–W3 son las que convierten la web en algo útil y profesional; W4 en adelante la completan.
