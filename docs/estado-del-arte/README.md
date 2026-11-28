# Estudio del estado del arte (28-nov-2026)

Repetible: `node estudio/capturar.mjs docs/estado-del-arte` (lista de webs y páginas en
`estudio/referencias.yaml`). Guarda, por web, capturas en móvil y escritorio (`NN-movil.jpg`,
`NN-escritorio.jpg`) y la estructura de cada página (`NN.json`: títulos, menús, controles, texto).
Resumen de lo capturado en `capturas.json`. Los requisitos que salen de aquí están en
`docs/requisitos-web.md`.

## Qué se pudo ver y cómo

| Web | Vía | Páginas |
|---|---|---|
| Metacritic | **En directo** (navegador real) | Novedades, mejores del año, página de disco (U2 – *Carnaval de Luz*) |
| New Music Tracker | En directo | Portada, novedades con filtros, destacados, disco, artista (+ revisión manual de 10 tipos de página) |
| AnyDecentMusic? | En directo | Portada, página de disco |
| ListenBrainz (código abierto) | En directo | Novedades ("Fresh releases") |
| Pitchfork | En directo | Lista de reseñas y una reseña |
| Bandcamp Daily | En directo | Lo mejor de 2025 |
| Musicboard | En directo | Portada (lo demás es app con cuenta) |
| **AOTY, RYM, AllMusic** | **Bloquean** a navegadores automáticos (Cloudflare). La copia de la Wayback Machine existe (AOTY 27-nov, RYM sept., AllMusic oct.) pero la red de este entorno no llega a web.archive.org ni a Common Crawl. **No se salta el bloqueo** (regla del usuario) | Estudiadas por: el código público que las lee (abajo), su propio registro de cambios y documentación, y artículos |

## Lo que hace cada una (lo que nos sirve)

**Metacritic – página de disco** (captura `metacritic/04-movil.jpg`): portada grande; franja con año ·
sello; título y "By Artista"; fecha; **"Metascore 76 · Generally Favorable · Based on 17 Critic Reviews"**
en un cuadro verde; **barra positivas / mixtas / negativas** (76 % · 18 % · 6 %, con su número); nota de
usuarios aparte; resumen de 2 líneas; géneros como etiquetas; artista y sello; **reseñas como tarjetas**:
fecha, nota en cuadro de color, medio, extracto de 2–3 líneas y "Full review ↗"; pestañas para ver todas,
positivas, mixtas o negativas. Listas con orden por Metascore, por fecha y por nota de usuarios; filtro por
año. Mucha publicidad.

**AnyDecentMusic?** (`anydecentmusic/`): portada con "Highest recent ratings" (nota · artista · medio) y
"Albums to watch" (portada + cita de una reseña con su nota y medio). Página de disco: **nota ADM 7.0** en
un cuadro negro, sello y fechas UK/US, botón para escuchar y **todas las reseñas** con nota, medio, extracto
y "Read review".

**New Music Tracker** (`nmt/`): portada por semanas (viernes a jueves): Esta semana, Destacados (con una
frase escrita), Populares, Recientes. Tarjeta: portada, **título con letra con remate**, artista enlazado,
fecha · género, popularidad en puntos. Filtros: género y estilo, más nuevos / más escuchados, esta semana /
30 / 90 días, país, álbumes y EP. Disco: migas, portada, Escuchar luego / Escuchado / Favorito, tipo · fecha
· sello, género y estilo, popularidad, escuchar en Qobuz/TIDAL/Apple, comprar, canciones con duración, "Más
de este artista". Artista: origen, seguir, discografía por tipo. Sin anuncios. Datos: MusicBrainz, Discogs
(géneros), ListenBrainz (popularidad).

**AOTY** (por su registro de cambios y por el código que la lee, `edideaur/AOTY-api`): nota de la crítica
y nota de usuarios **con el número de reseñas**; **rankings ponderados por el número de reseñas** (para que
un disco con pocas no suba arriba); página de disco con canciones (con nota por canción), enlaces a
plataformas, créditos, histograma de notas, evolución de la nota, etiquetas, portadas alternativas,
**discos parecidos**, reseñas de crítica y usuarios, **listas de fin de año en las que aparece**.
Secciones: novedades, esta semana, por fecha, "imprescindibles" (must-hear), próximos, "tal día como hoy";
rankings de crítica, de usuarios, por medio y por género con mínimo de reseñas y periodo (año, todo,
reciente).

**RYM** (por Wikipedia, su página de desarrollo y los programas que la leen): novedades con géneros, nota
media y número de valoraciones; rankings filtrables por género, **descriptores** (ánimo, tema), país,
idioma, sello; vistas de galería y de lista compacta; opción "diverso" (un disco por artista).

**AllMusic** (por su propio buscador público y los programas que la leen): disco con nota de AllMusic y
de usuarios, género, estilos, **estados de ánimo y temas**, discos parecidos y la reseña; "Featured New
Releases" por fecha con una frase; **tabla de todos los lanzamientos del día ordenable** por artista,
disco, sello, género y nota.

**ListenBrainz** (código abierto): novedades agrupadas por día, con **línea de tiempo** para saltar de
fecha, tipo (álbum, single, directo) en la portada, orden por fecha y dirección, RSS.

**Pitchfork**: portada grande, género en mayúsculas, título con letra con remate, nota en círculo; "Best
New Albums" aparte.

## Proyectos abiertos y de aficionados (GitHub)

| Proyecto | Qué hace | Qué nos aporta |
|---|---|---|
| `edideaur/AOTY-api` | Lee AOTY (todas sus secciones) | El mapa completo de AOTY (arriba) |
| `JahsiasWhite/AlbumOfTheYearAPI` | Lee AOTY con cookies del navegador | Confirma que AOTY exige saltar Cloudflare: no lo usamos |
| `dbeley/rymscraper`, `LeMetadatarr/pyrateyourmusic` | Leen RYM; necesitan saltar Cloudflare | Campos de RYM (ranking, nota, nº de valoraciones, géneros, descriptores); no los usamos |
| `chrismichaelps/metacritic` | Lee Metacritic | Campos: nota, fecha, reseñas (texto, medio, autor, fecha, nota), próximos discos |
| `crypt0rr/ArtistTrackarr` | Vigila novedades (Spotify, MusicBrainz, Apple, ListenBrainz, Cover Art Archive) | **Cada disco con sus "pruebas" por fuente y su confianza**; distingue anuncio y día de salida; EP/single por nº de pistas (1 = single, 2–6 = EP); calendario .ics |
| `Muukuro/freshwax` | Seguir artistas y avisar (Deezer, MusicBrainz) | Feed reciente, vista de próximos, calendario .ics por usuario, app instalable |
| `soulprovidr/nudedisco`, `mpuzey/ripe-peaches` | Agregadores de reseñas por RSS | Confirman el enfoque (RSS de reseñas → nota agregada); poca documentación |
| `jasii/Simple-Music-Tracker`, `Jawsled/music-release-tracker`, `emlopezr/trackwatch` | Seguidores de novedades por artista | Calendarios y feeds; ninguno combina novedades con notas de la crítica |

**Conclusión:** ningún proyecto abierto junta lo que pide este (novedades de varios géneros + notas de la
crítica + clasificación por subgénero). El modelo a seguir para **la página del disco y las notas es
Metacritic / AnyDecentMusic**; para **la portada y el listado, New Music Tracker**; para **los rankings,
AOTY** (ponderados por nº de reseñas).

## Fuentes consultadas

- [AOTY – Changelog](https://www.albumoftheyear.org/changelog/) · [AOTY – foros](https://forums.albumoftheyear.org/t/how-aoty-works-at-tie-score/1944)
- [Rate Your Music – Wikipedia](https://en.wikipedia.org/wiki/Rate_Your_Music) · [RYM – estado del desarrollo](https://rateyourmusic.com/development/) · [Sonemic](https://sonemic.com/)
- [AllMusic – All New Album Releases](https://www.allmusic.com/newreleases/all) · [AllMusic – Featured New Releases](https://www.allmusic.com/newreleases)
- GitHub: [AOTY-api](https://github.com/edideaur/AOTY-api), [AlbumOfTheYearAPI](https://github.com/JahsiasWhite/AlbumOfTheYearAPI), [rymscraper](https://github.com/dbeley/rymscraper), [pyrateyourmusic](https://github.com/LeMetadatarr/pyrateyourmusic), [allmusic-python](https://github.com/jack-arms/allmusic-python), [metacritic](https://github.com/chrismichaelps/metacritic), [nudedisco](https://github.com/soulprovidr/nudedisco), [ripe-peaches](https://github.com/mpuzey/ripe-peaches), [ArtistTrackarr](https://github.com/crypt0rr/ArtistTrackarr), [freshwax](https://github.com/Muukuro/freshwax), [Simple-Music-Tracker](https://github.com/jasii/Simple-Music-Tracker), [music-release-tracker](https://github.com/Jawsled/music-release-tracker), [trackwatch](https://github.com/emlopezr/trackwatch)
