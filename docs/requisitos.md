# Requisitos: trazabilidad, validación y base del diseño

Cada cosa que se ha pedido en la conversación, dónde está hecha, cómo se ha comprobado y en qué
estado está. **Estado:** ✅ hecho y comprobado · 🟡 hecho, falta validarlo con todos los datos o en
producción · ⏳ en curso · ⛔ no se puede (motivo) · ⬜ pendiente.
Actualizado el 27-nov-2026.

## 1. Alcance y objetivo

| # | Requisito | Dónde | Cómo se ha comprobado | Estado |
|---|---|---|---|---|
| 1 | Web de novedades de country/americana/folk y hard rock/AOR | `site/`, `scraper/` | Revisión con 1.267 discos reales, prueba de navegador | ✅ |
| 2 | Solo discos en inglés | `config.yaml` → `idiomas_permitidos`; idioma de MusicBrainz | Descartes "idioma X" en el informe. Si MusicBrainz no sabe el idioma, se mantiene y la ficha dice "Idioma sin verificar" | 🟡 un % de discos queda sin idioma verificado |
| 3 | "Mejor que el mercado" frente a AOTY (más discos, antes, subgénero correcto) y decirlo si no se logra | `docs/informe.md` | AOTY bloquea a todo lector automático (Cloudflare); el informe lo dice y compara con cada fuente por separado, mide "antes" y el acuerdo de subgénero con la prensa | ⛔ frente a AOTY · ✅ frente a cada fuente |
| 4 | Descartar EP | reglas de `config.yaml`, Deezer, MusicBrainz, nº de pistas | Prueba de extremo a extremo + descartes reales en el informe | ✅ |
| 5 | Descartar reediciones / remasters | regla `reedicion` | Prueba de extremo a extremo | ✅ |
| 6 | Todo 2026 (enero–diciembre) además de los 5 últimos meses | `ventana.anios_completos` | Recogida completa | ⏳ |
| 7 | "Lo mejor de cada año" | `scraper/web.py`, vista en la web, listas anuales | Prueba de navegador; con 2025 por listas | 🟡 falta con todo 2026 |

## 2. Taxonomía y clasificación

| # | Requisito | Dónde | Cómo se ha comprobado | Estado |
|---|---|---|---|---|
| 8 | Taxonomía cerrada del usuario con alias | `data/taxonomia.yaml` | Prueba de coherencia (ids únicos, familias existentes) | ✅ |
| 9 | Familias "en foco" de agenda-conciertos (rock y metal, punk y garage, indie y pop-rock, blues, synthwave y dark wave, cantautores; americana = country; "sin clasificar" como filtro) | `taxonomia.yaml`, filtro "Sin subgénero" | Clasificación de los 5 meses y web | 🟡 falta con todo 2026 |
| 10 | Etiqueta nueva → LLM **una sola vez** → `mapeo_etiquetas.csv` | `scraper/mapear.py` (Wikidata), `scraper/etiquetas_llm.py` (Claude con plan Pro), sesión | Pruebas (ids inventados rechazados, solo pendientes, una vez) | ✅ |
| 11 | Nunca crear subgéneros; proponerlos en el informe | notas "propuesta:" → informe | Pruebas | ✅ |
| 12 | LLM solo con el plan Pro, sin pagar API | API de pago desactivada; Action con `CLAUDE_CODE_OAUTH_TOKEN` | Pruebas con cliente falso | 🟡 la Action con token no se ha ejecutado aún (requiere `main` y el token) |
| 13 | Clasificación correcta | reglas, alias, mapeo, pesos por origen | Acuerdo con el género que da la prensa, en el informe | 🟡 no hay un conjunto de referencia revisado a mano (ver §6) |

## 3. Fuentes

| # | Requisito | Dónde | Cómo se ha comprobado | Estado |
|---|---|---|---|---|
| 14 | Verificar cada fuente propuesta | `docs/fuentes.md` | Cada una probada con el robot real (`scraper.probar`) | ✅ |
| 15 | 5 fuentes extra por familia | `docs/fuentes.md` §5–6 | Probadas | ✅ |
| 16 | Usar **todas** las fuentes posibles | ≈70 en `fuentes.yaml` + radares + listas | Búsquedas sucesivas documentadas con lo usado y lo descartado | 🟡 nunca puede darse por cerrado: hay que seguir buscando |
| 17 | Bandcamp ≤ 1 petición / 4 s; MusicBrainz ≤ 1 / s | `config.yaml` | Prueba que falla si se bajan; prueba de ritmo con hilos | ✅ |
| 18 | Captcha o bloqueo: no saltarlo, avisar | `scraper/http.py` | Pruebas (Cloudflare, 403, 429 persistente); en el informe y en el resumen de la Action | ✅ |
| 19 | Respetar `robots.txt` | `scraper/http.py` | Prueba de lectura prohibida; fuentes descartadas por ello | ✅ |
| 20 | No inventar datos ni fuentes | todo dato lleva su fuente y enlace | Revisión; la ficha enseña "Aparece en" con enlaces | ✅ |
| 21 | Extensible sin código: nuevas fuentes solo con configuración | `fuentes.yaml`, macros, lectores genéricos | Prueba que valida toda la configuración | ✅ |
| 22 | Wikipedia "List of 2026 albums" | fuente `wikipedia` | Recogida real | ✅ |
| 23 | Usar los repositorios compartidos (agenda-conciertos, radar de MusicBrainz, Deezer, UI de roberto-cabal…) | taxonomía importada, `scraper/radar.py`, enlaces de escucha | Recogida y web | ✅ |
| 24 | Year End Lists; evaluar Musicboard, MusicTaste, Shfl, New Music Tracker | listas anuales; `docs/fuentes.md` | Probadas; descartes con motivo | ✅ |
| 25 | Spotify, Tidal | — | Spotify requiere Premium para la API útil; no se usa | ⛔ |

## 4. Datos por disco

| # | Requisito | Dónde | Cómo se ha comprobado | Estado |
|---|---|---|---|---|
| 26 | Artista, título, fecha, sello, subgéneros, etiquetas originales, portada, nº de pistas, tipo, fuentes, reseñas (web + nota), enlaces | `data/discos.json`, esquema validado | Prueba de formato de los datos | ✅ campos · 🟡 la **cobertura** de cada campo (cuántos discos tienen sello, pistas, portada) aún no se mide en el informe |

## 5. Web

| # | Requisito | Dónde | Cómo se ha comprobado | Estado |
|---|---|---|---|---|
| 27 | Cuadrícula de portadas por semanas, lo más reciente arriba | `site/app.js` | Prueba de navegador | ✅ |
| 28 | Ficha del disco | `site/app.js` | Prueba de navegador | ✅ |
| 29 | Filtros: familia, subgénero múltiple, fechas (5 meses por defecto), sello, búsqueda | `site/app.js` | Prueba de navegador: familia, búsqueda, fechas, sello, limpiar | ✅ |
| 30 | Pensada para móvil | CSS móvil primero | Prueba en móvil emulado: sin desbordes, botones con nombre | ✅ |
| 31 | Estática en GitHub Pages | `site/`, Action `publicar` | — | ⬜ falta pasar a `main` y activar Pages (usuario) |
| 32 | Mejoras de UX del estudio (Mi lista, nota, orden, lista, compartir, calendario .ics, RSS, app instalable, meses, destacados, Deezer, Qobuz, calendario de salidas…) | `docs/ux.md` | Prueba de navegador | ✅ |
| 33 | Estudio de las funciones de AOTY, RYM, Metacritic, AllMusic | `docs/ux.md` §5 | Bloquean a los robots | ⬜ necesita el navegador del usuario |

## 6. Proceso, robustez y automatización

| # | Requisito | Dónde | Cómo se ha comprobado | Estado |
|---|---|---|---|---|
| 34 | Plan corto y OK antes de programar; un commit por fase | historial de git | — | ✅ |
| 35 | Action semanal | `.github/workflows/semanal.yml` | YAML validado | 🟡 no se ha ejecutado: solo corre en `main` |
| 36 | Todo automático, sin sesión ni gasto | Action + Wikidata + Claude con plan Pro | — | 🟡 igual que 35 |
| 37 | Persistencia, tolerancia a fallos, reanudar | `scraper/pipeline.py`, lecturas guardadas, escrituras atómicas | Pruebas de reanudación y de extremo a extremo | ✅ |
| 38 | Escenarios nominales, de borde, esquina y error | `tests/` (110 de Python + 47 comprobaciones de navegador), cobertura 72 % con mínimo exigido del 70 % | Se ejecutan en GitHub en cada envío | ✅ |
| 39 | Rendimiento | índice ligero + fichas por mes, carga diferida | Medido: 115 KB comprimidos | 🟡 sin auditoría Lighthouse |
| 40 | Secretos fuera del chat y del código | secretos del repositorio | Revisión | ✅ |

## 7. En qué se basa el diseño, capa por capa (y qué falta contrastar)

| Capa | Decisión | Referencias en que se basa | Qué no está contrastado todavía |
|---|---|---|---|
| Arquitectura | *git scraping* + web estática + GitHub Actions | Patrón de Simon Willison (*git scraping*), JAMstack; proyectos revisados que hacen lo mismo (radar de novedades de Thrasher2020, new-albums de roberto-cabal) | Alternativa con base de datos (SQLite) solo justificada por volumen; no medida |
| Lectura de webs | RSS/HTML con patrones en configuración; APIs oficiales | `robots.txt` (RFC 9309), límites publicados de MusicBrainz, Deezer, iTunes, Discogs, Wikidata | No se usan navegadores automatizados para leer webs con JavaScript (decisión: no saltar protecciones) |
| Identificación de discos | Normalización + similitud + ids de MusicBrainz | Recomendaciones de MusicBrainz (release groups) | **No se ha medido la precisión** de la unión de duplicados (cuántos se unen mal o no se unen) |
| Clasificación | Reglas + alias + base de conocimiento (Wikidata) + LLM con salida estructurada y validada | Enfoque híbrido habitual: determinista primero, LLM restringido a una lista cerrada | **No hay conjunto de referencia** revisado a mano para medir aciertos; solo el acuerdo con la prensa |
| Datos | JSON versionado, esquema validado en las pruebas | JSON Schema | Cobertura por campo no medida en el informe |
| Orquestación | Fases como procesos, estado persistente, reanudación diaria | Patrones de *checkpointing* de los ETL | Sin alertas propias además del correo de GitHub |
| Web | JavaScript sin framework, PWA, carga diferida, URL como estado | Guías de Google (web.dev) de PWA y Core Web Vitals; WCAG 2.1 AA; patrones de AOTY/RYM vistos en el estudio | Accesibilidad: auditoría axe (WCAG 2.1 A/AA) en cada envío, 0 infracciones tras corregir el contraste de colores. Rendimiento: medido el peso (115 KB), **sin Lighthouse** |
| Pruebas | pytest + Playwright + axe en CI | Pirámide de pruebas: unitarias, integración, extremo a extremo | Cobertura 72 % (mínimo 70 % en CI); lo menos cubierto: radar de Deezer y etiquetas extra de Wikidata/Discogs/Last.fm |
| Seguridad | Secretos de GitHub, sin claves en código, LLM solo escribe un archivo validado, versiones fijas, Dependabot | Guía de seguridad de la Action de Claude Code | Sin cabeceras de seguridad propias (GitHub Pages no las permite) |
| IA | Claude con el plan Pro vía Claude Code; Wikidata como base gratuita | Documentación oficial de la Action de Claude Code | La Action con token no se ha ejecutado |

**Conclusión honesta:** no está "validado al 100%". Están hechos y probados los requisitos marcados
con ✅. Los 🟡 dependen de terminar la recogida de todo 2026 o de pasar a `main`. Los ⬜ necesitan
una acción tuya. Y la última columna de §7 es lo que falta para poder decir con datos que cada capa
está al nivel de lo mejor que existe: medir aciertos de clasificación y de unión de duplicados,
y auditar el rendimiento con Lighthouse. Accesibilidad, cobertura de pruebas y dependencias ya están cubiertas (27-nov).
