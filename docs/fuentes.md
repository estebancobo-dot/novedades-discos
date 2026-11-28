# Fuentes: verificación

Comprobado el **21-nov-2026** desde la nube (la misma red que usará el robot de recogida).
Cada fuente se ha pedido a mano, a ritmo lento, y se ha mirado qué devuelve de verdad.

Leyenda: ✅ funciona · ⚠️ funciona a medias · ❌ descartada

> **Reglas que aplica el robot:** como máximo 1 petición cada 2 s por web
> (MusicBrainz 1/s). Si una página devuelve una verificación anti-bots
> ("Just a moment…", "Client Challenge", "Verifying your connection…",
> "Attention Required"), el robot **deja esa fuente**, lo apunta en el informe
> y no intenta saltársela.

---

## 1. Country / americana / folk: prensa

| Fuente | Estado | Cómo se lee / por qué no |
|---|---|---|
| **Saving Country Music**: Release Radar | ✅ | Dos páginas HTML cubren la ventana: *"Most Anticipated New Albums for 2nd Half of 2026"* y *"…for Final Portion of 2026"*. Formato: fecha → `Artista – Título (género)`, con los EP marcados. También anuncia discos futuros. Las reseñas salen por RSS (`/feed/`) con nota X/10. |
| **Holler** (holler.country) | ⚠️ | No tiene RSS ni sitemap, y el índice de reseñas solo muestra 6 enlaces (el resto se carga con JavaScript). Se leen los *"First Listen: … albums you need to hear this week"* enlazados desde la portada. |
| **Whiskey Riff** | ⚠️ | El RSS funciona, pero casi todo es actualidad y estilo de vida: ninguna de las 10 últimas entradas trata de discos. Solo sirve para "reseñado en" cuando menciona un disco. |
| **Americana UK** | ✅ | Categoría *album-reviews*, paginada. El título va como `Artista "Título"` y la nota aparece como X/10. |
| **Twangville** | ✅ | RSS (`/feed/`) con reseñas `Artista – Título`. |
| **Country Universe** | ⚠️ | El RSS funciona, pero ahora mismo casi todo son series retrospectivas ("Every No. 1 Single…"). Tiene pocas reseñas de discos nuevos. |

## 2. Hard rock / AOR: prensa y listados

| Fuente | Estado | Cómo se lee / por qué no |
|---|---|---|
| **Heavy Harmonies**: newcds.cgi | ✅ | Lista HTML de unas 380 altas, del 27-jul al 15-nov-2026. ⚠️ La fecha es la de **alta en su base de datos**, no la de salida, e incluye discos antiguos. La ficha de cada disco da año, sello, nº de catálogo y pistas, y el género va en la ficha del grupo. |
| **MelodicRock.com** | ⚠️ | Se lee bien (`/rss.xml` y `/reviews`, con nota en %), pero **está casi parada**: la última reseña es del 23-jun-2026 y la última noticia del 19-ago-2026. Solo 2 reseñas caen en la ventana. |
| **Fireworks Magazine** | ✅ | `/albumreviewsnew` lista las reseñas del número actual (artista, título, género y si es *New Release* o *Reissue*). El blog (`/blog-feed.xml`) es sobre todo de conciertos y entrevistas. Solo cubre el número en curso. |
| **Angelic Warlord**: release dates | ✅ | Página HTML de fechas 2026-2027 (`Artista / Título / fecha`), con EP y reediciones marcados. Ojo: es una web de **rock y metal cristiano**, así que hay que filtrar mucho metal extremo. |
| **Get Ready to ROCK!** | ✅ | RSS (`/blog/feed/?paged=N`), entradas `Album review: ARTISTA – Título`. Mezcla reseñas de conciertos y de libros. |

## 3. Sellos

| Sello | Estado | Cómo se lee / por qué no |
|---|---|---|
| **New West** | ✅ | Tienda Shopify: la página HTML `/collections/recent-releases` se lee (21 productos, con merchandising mezclado). El acceso a sus datos en formato JSON (`products.json`) **pide verificación anti-bots**, así que no se usa. |
| **Thirty Tigers** | ❌ | No tiene página de novedades, solo la lista de artistas. Sus discos aparecen en Saving Country Music, Country Standard Time y MusicBrainz. |
| **Rounder** | ❌ | La web devuelve **"Verifying your connection…"**, una verificación anti-bots. |
| **Yep Roc** | ❌ | La web y su RSS no se actualizan desde marzo de 2024. |
| **Oh Boy Records** | ✅ | Shopify: la página HTML `/collections/new-releases-from-oh-boy-records` se lee (16 productos, preventas incluidas). |
| **Free Dirt Records** | ❌ | La web falla en la conexión segura (*SSL handshake failure*). |
| **Frontiers** | ✅ | frontiers.it redirige a su tienda (frontiers-us.shop). `/collections/new-releases` se lee en HTML (51 productos, CD y vinilo). |
| **Escape Music** | ⚠️ | `news.htm` se lee, pero es texto libre con fechas como "COMING 19th FEBRUARY" sin año. Se usa como señal y la fecha se confirma con MusicBrainz. |
| **ROAR / Reigning Phoenix** | ✅ | `/releases` en HTML: `ARTISTA / Título / (MM/DD/AAAA)`. Mezcla mucho metal, hay que filtrar. |
| **Silver Lining Music** | ✅ | La web buena es **silverliningmusic.co.uk**; silverliningmusic.com es de otra persona. RSS `/blogs/news-stories.rss` con 51 noticias (anuncios de discos, la última del 17-nov). Hay también una página `/latest-releases`, aunque muestra menús por años y no una lista con fechas. |
| **HNE Recordings** | ❌ | hnerecordings.com no responde. Su página en Cherry Red no muestra productos en el HTML. |

### Bandcamp: ✅ (con condiciones; ver la sección 6)

En la primera prueba, con identidad de navegador Chrome, todas las páginas devolvían
**"Client Challenge"**, una verificación anti-bots. Con la identidad real del robot
(`music-release-tracker/0.1`), Bandcamp sirve las páginas con normalidad. Su `robots.txt`:
- **prohíbe** la búsqueda (`/search`), así que no se usa;
- **permite** las páginas de disco y de artista.

Por eso solo se abren discos cuyo enlace ya conocemos: lo da MusicBrainz o la página
del artista. Ritmo: 1 petición cada 4 s. Si vuelve a aparecer la verificación, el robot
para y lo dice en el informe.

## 4. Enriquecimiento y comparación

| Fuente | Estado | Notas |
|---|---|---|
| **MusicBrainz** (API) | ✅ | Hay que identificarse con un nombre de aplicación (con un navegador genérico responde `ua-blocked`). A veces devuelve 503 "server busy": se reintenta con espera. Da tipo (Album/EP), fecha, **idioma**, sello, nº de pistas, enlaces (Spotify, Apple, Bandcamp…) e identificador para quitar duplicados. Como fuente para *descubrir* discos sirve poco: casi no tienen etiquetas de género (en la ventana, solo 5 discos con `americana`, 5 con `hard rock` y 0 con `aor`). |
| **Cover Art Archive** | ✅ | Portada en 250 px por identificador de MusicBrainz. |
| **Album of the Year** | ❌ | Toda la web (incluidas las páginas de género y el RSS) devuelve **"Just a moment…"**, la verificación anti-bots de Cloudflare. **La comparación con AOTY no se puede hacer.** El informe lo dirá y comparará con la prensa. |

---

## 5. Fuentes nuevas que propongo (verificadas, pendientes de tu OK)

### Country / americana / folk
1. **Country Standard Time**: `countrystandardtime.com/cdreleases.asp`. ✅ Lista *Upcoming* y *Recent* releases con fecha, sello y descripción (dice si es EP y cuántas canciones). Es de las que anuncian antes.
2. **No Depression**: RSS (`nodepression.org/rss/`). ✅ 9 de 15 entradas son reseñas (`ALBUM REVIEW: …`).
3. **Bluegrass Today**: RSS. ✅ Noticias de lanzamientos de bluegrass, el subgénero peor cubierto por las demás.
4. **KLOF Mag** (antes Folk Radio UK, ahora redirige ahí): RSS. ✅ Reseñas de folk y psych-folk.
5. **Glide Magazine**: RSS (`/feed.xml`). ✅ Reseñas de americana y roots, aunque mezcla mucho directo y jam.

Probadas y descartadas: *Americana Highways* (responde "429 Too Many Requests" a la primera petición), *The Bluegrass Situation* (verificación de Cloudflare), *Country Queer* (el RSS no publica discos desde mayo).

### Hard rock / AOR
1. **Loudwire**: *2026 Hard Rock + Metal Album Release Calendar*. ✅ Enorme lista por fecha `Artista – Título (Sello)`, con reediciones marcadas. Mucho metal que filtrar, pero es la que más hard rock encuentra y antes.
2. **Sleaze Roxx**: RSS. ✅ Noticias y reseñas de glam y sleaze, incluidos discos *upcoming*.
3. **Metal Planet Music**: RSS. ✅ Separa por categorías *Albums / EPs / Singles*, lo que ayuda a descartar EP.
4. **Rock & Blues Muse**: RSS. ✅ Blues-rock y southern.
5. **Louder** (Classic Rock / Prog): `/reviews`. ✅ Lista HTML de reseñas, pero el titular es editorial: hay que casar el artista.

Probadas y descartadas: *The Rockpit*, *Prog Archives* y *My Global Mind* (verificación de Cloudflare); *Blabbermouth* (las reseñas se cargan con JavaScript); *Rock Report* (la web solo funciona con JavaScript); *AOR Heaven* (cerrada, con mensaje de despedida); *Dangerdog* (sin reseñas desde septiembre de 2025); *Metal Express Radio* (RSS con 1 entrada); *All About The Rock* (no responde).

---

## 6. Segunda verificación (21-nov, ya con el robot real)

La fase 1 se probó con identidad de navegador. El robot se identifica honestamente
(`Mozilla/5.0 (compatible; music-release-tracker/0.1)`) y **respeta `robots.txt`**. Con esa
identidad, varias webs cambian:

| Fuente | Antes | Ahora | Motivo |
|---|---|---|---|
| Bandcamp | ❌ | ✅ | Sirve las páginas al robot identificado. La búsqueda está prohibida por `robots.txt`. |
| Rounder | ❌ | ❌ | La web ya responde, pero no tiene página de novedades y `robots.txt` prohíbe ordenar el catálogo por fecha. |
| Americana Highways | ❌ | ✅ | El RSS responde. Está en `fuentes.yaml` desactivada, a la espera de tu OK. |
| Sleaze Roxx | ✅ | ❌ | Su `robots.txt` prohíbe todo a cualquier robot salvo Google y similares. Se respeta. |
| Rock & Blues Muse | ✅ | ❌ | Su `robots.txt` no permite leer el feed. Se respeta. |
| Album of the Year, The Rockpit, Prog Archives, My Global Mind | ❌ | ❌ | Siguen con la verificación de Cloudflare. |

**MusicBrainz:** su `robots.txt` cierra `/ws` a los rastreadores. Pero `/ws/2` es su
[API pública documentada](https://musicbrainz.org/doc/MusicBrainz_API) para programas, y se cumplen
sus condiciones: identificarse y 1 petición/s. Está declarada como excepción explícita en
`data/config.yaml` (`apis_documentadas`).

### Fuentes recomendadas en r/Music

| Fuente | Estado | Uso |
|---|---|---|
| **Pause & Play**: On the CD Front | ✅ | Lista semanal `Artista \| "Título" (descripción) \| Sello`, con archivo por fechas (`/new-releases-nov-13-2026/`). Mezcla todos los géneros (`mixta`). Unos 580 lanzamientos en 24 semanas. **En uso.** |
| **Bandcamp Daily**: Essential Releases | ✅ | Selección semanal con enlace directo al disco en Bandcamp. Generalista. **En uso.** |
| Metacritic (música) | ❌ | Verificación de Cloudflare. |
| AllMusic (New Releases) | ❌ | Verificación de Cloudflare. |
| Album of the Year | ❌ | Verificación de Cloudflare (ver arriba). |
| Hello Weimar Republic (Substack) | — | Se lee, pero recomienda **canciones**, no discos. No se usa. |

### Repositorios revisados (22-nov)

| Repositorio | Qué ofrece | ¿Se usa? |
|---|---|---|
| jahsiaswhite/albumoftheyearapi | Librería para leer AOTY | ❌ Su propio código avisa de que AOTY la bloquea con Cloudflare. Su solución es reutilizar la cookie `cf_clearance` de un navegador e imitar a Chrome, es decir, saltarse la verificación. |
| rheera/album-of-the-year-analysis | Datos de AOTY y árbol de géneros | ❌ Los datos llegan hasta 2024, el árbol de géneros no tiene subgéneros de country, folk, rock ni metal, e incluye un script para saltarse Cloudflare. |
| Tema `allmusic` en GitHub | Lectores de AllMusic | ❌ AllMusic responde con la verificación de Cloudflare. |
| Radares de Spotify (spotify-new-albums-radar, Better-Release-Radar, spotify-albums, musicreleases) | Discos nuevos de artistas que sigues, con la API de Spotify | ⏸ La idea, un **radar de artistas**, es la mejor forma de encontrar más discos y antes. Necesita una app gratuita de Spotify (client id y secret). El 81 % de nuestros artistas tiene su Spotify enlazado en MusicBrainz, así que la identidad sería exacta. |
| estebancobo-dot/agenda-conciertos | Wikipedia, Wikidata, Discogs, MusicBrainz, Last.fm, ReccoBeats | ✅ Se reutiliza el enfoque: Wikidata, Discogs y Last.fm en `scraper/enriquecer.py`, APIs documentadas exentas de `robots.txt` e identidad por enlaces, no por nombre. ❌ **ReccoBeats** no sirve aquí: su catálogo se queda en 2024; Ian Noe, Willi Carlisle o Kaitlin Butts no tienen nada posterior. |

### Repositorios de GitHub sobre novedades (búsqueda del 22-nov)

| Repositorio | Qué hace | Qué se aprovecha |
|---|---|---|
| **Thrasher2020/home-assistant-upcoming-music-releases** | Calendario de lanzamientos de tus artistas con MusicBrainz y Apple Music | ✅ **Su técnica**: pedir a MusicBrainz *todos* los álbumes de un rango de fechas (troceado por meses y días, con exclusión de las fechas de solo año y el tope de 500) y cruzarlos con los artistas de interés. Base del **Radar de artistas** (`scraper/radar.py`). |
| canmils/catala-music-radar | Novedades y próximos de una lista de artistas con MusicBrainz, sin clave | ✅ Confirma el enfoque: lista de artistas, MusicBrainz, 1 petición/s |
| InstaZDLL/waveflow-plugin-release-radar | Radar de novedades de tu biblioteca con MusicBrainz y Cover Art Archive | ✅ Escaneo incremental que se para limpiamente ante un 503/429; lo hace igual nuestro navegador |
| benderham/riff-radar | Agente que busca discos de metal nuevos, los verifica con MusicBrainz y los ordena según tus gustos | 💡 Idea para más adelante: ordenar según "Mi lista" |
| danworkman1/album-tracker-cli | Próximos discos desde Wikipedia | ✅ Ya usamos Wikipedia |
| PaulMcInnis/Better-Release-Radar, robbyrussell/spotify-new-albums-radar, jessmartin/spotify-new-releases, MusicReleases/musicreleases.github.io, emlopezr/trackwatch, elenaecheva/album-drop-calendar | Radares con la API de Spotify | ❌ Necesitan una app de Spotify, que exige cuenta Premium |
| GurnB/Upcoming_Album_Release_Schedule, vir-malhotra/metacritic-scraper, joelzehring/new-music-scraper | Leen Metacritic o AllMusic | ❌ Esas webs bloquean a los robots (Cloudflare) |
| hmlON/mun, ChrisSmith/AlbumTracker | Avisos de discos nuevos de tus artistas | 💡 Idea para "Mi lista": avisar cuando un artista guardado anuncie disco |

### Repositorios de la búsqueda del usuario (capturas, 22-nov)

| Repositorio / web | Qué hace | Qué se aprovecha |
|---|---|---|
| **JamieAfterlife/new-music-releases (DropSignal)** | Lista de artistas vigilada con MusicBrainz → RSS, página web y resumen diario | ✅ **Revisar cada vez los últimos 45 días** (MusicBrainz recibe datos tarde) · ✅ **RSS** por disco · ✅ enlaces exactos desde MusicBrainz y, si no hay, **enlace de búsqueda** en cada servicio |
| **jamj1m88/music-release-scout** | Tres "carriles" (tus artistas, artistas parecidos, prensa) y resumen semanal | ✅ **API de búsqueda de iTunes** (sin clave): enlace a Apple Music, nº de pistas y **género** · 💡 puntuar más los discos que salen por varios carriles |
| **roberto-cabal/new-albums** | Página que junta listas curadas (Needle Drop, Pitchfork BNA, Stereogum, The Quietus) | ✅ Filtro **"en 2+ listas"** para "lo mejor" · ✅ **API pública de Deezer** y de iTunes para escuchar · ✅ enlaces directos sólidos frente a búsquedas punteadas · ✅ enlace de **búsqueda en AOTY** para que la persona vea la nota (sin leer AOTY) |
| **ydniM/Music-Releases-Feed** | Novedades de una lista de artistas con **Deezer** | ✅ **Deezer como radar sin clave**: discografía al día con fecha y tipo (álbum/EP/single). Comprobado: Kaitlin Butts → *Hello, Honky Tonk* (30-oct-2026). A diferencia de ReccoBeats, está actualizado |
| tomasdrobnik/new-albums | Lista semanal de una web checa → página y playlist de Spotify | 💡 Secciones plegables por género y aviso por correo con secretos SMTP. Confirma que Spotify exige Premium desde febrero de 2026 |
| dkozynko/music-album-releases | Wiki anual de r/postrock y Sputnikmusic | ❌ Otro género; Reddit no se puede leer |
| purarue/albums | Listas de discos aclamados (1001 discos, Rolling Stone 500…) | 💡 Para "lo mejor de cada año" (histórico) |
| MoonWalker440/Music-Megathread | Lista enorme de recursos | 💡 Nada nuevo para nuestros géneros salvo Metal Tracker (descargas) |
| Federico0284364/latest-album-releases, savannah-hayes/music-releases, jessicaraepetersen/happyfridays, Better-Release-Radar, musicreleases.github.io | Radares con Spotify | ❌ Spotify exige Premium |
| newalbumreleases.net, downtify, SoulSync | Descargas de música | ❌ No se usan webs ni herramientas de descarga |
| hitsculture.com | Novedades de R&B y hip-hop | ❌ Fuera de nuestras familias |
| Pitchfork: *New Music Releases and Upcoming Albums 2026–2027* | Lista de próximos discos | 💡 Candidata a fuente de "próximamente" (por verificar) |

### Decisiones del 22-nov (modo autónomo)

| Fuente | Decisión | Por qué |
|---|---|---|
| Americana Highways | ✅ Activada | Verificada; publica reseñas `REVIEW: Artista "Título"` |
| Country Universe | ⏸ Desactivada | 0 discos en 5 meses: ahora publica sobre todo series retrospectivas |
| Bluegrass Today | ⏸ Desactivada | 0 discos en 5 meses: sus titulares son de fichajes y conciertos |
| Glide | ✅ Se mantiene | Solo 1 petición por semana; a veces publica reseñas de discos |
| **Pitchfork: guía de próximos discos** | ✅ Nueva | Se lee bien: `Artista: «Título» [Sello]` por fecha; unos 60 próximos discos |
| **The Line of Best Fit: Album release schedule** | ✅ Nueva | Agenda de lanzamientos por fecha, con los EP marcados; unos 180 discos |
| **Radar de artistas (Deezer)** | ✅ Nuevo | Discografía al día de nuestros artistas (idea de ydniM/Music-Releases-Feed). Solo artistas con nombre único en Deezer y solo lanzamientos de tipo álbum |

### Fuentes para las familias "en foco" (tarea 17, 22-nov)

| Fuente | Estado | Uso |
|---|---|---|
| Stereogum: Album of the Week | ✅ | Reseña semanal (indie, a veces country): "reseñado en" |
| Blues Blast Magazine | ✅ | Reseñas de blues `Artista – Título \| Album Review` |
| Blues Rock Review | ✅ | Reseñas `Artista: Título Review` y anuncios |
| Dying Scene | ✅ | Reseñas de punk `Dying Scene Album Review: Artista – "Título"` |
| The Quietus | ✅ | Noticias de discos (patrones de noticias) |
| American Blues Scene | ⚠️ No se usa | Solo artículos e historia, sin discos nuevos |
| Metal Injection: The Weekly Injection | ❌ | El RSS solo trae un resumen y los artículos piden la verificación de Cloudflare |
| BrooklynVegan | ❌ | Su `robots.txt` no permite el feed de novedades |
| Punknews | ❌ | El RSS de reseñas existe (`static.punknews.org/feeds/punknews-reviews.rdf`) pero lleva parado desde el 17-sep-2026; el de noticias solo trae los 15 últimos titulares, casi nunca con el título del disco |

**Segunda búsqueda (22-nov, tarde): synthwave/dark wave, metal, punk y blues.** Todas probadas con el robot real (`python -m scraper.probar ID`), respetando `robots.txt` y sin saltar ninguna verificación.

| Fuente | Familia | Estado | Uso |
|---|---|---|---|
| **Side-Line** (side-line.com) | Synthwave y dark wave | ✅ | Noticias de discos del mundo dark electrónico, EBM, synth y goth. Titulares con ficha: `Artista – Título (Digital/CD Album – Sello)` y anuncios. Fuente mixta (también industrial y ambient): solo entra el disco con subgénero |
| **ReGen Magazine** (regenmag.com) | Synthwave y dark wave | ✅ | Reseñas con ficha en el cuerpo: género (`Category: Synthpop / Dark Electro`), sello y **fecha de salida** exacta |
| **Angry Metal Guy** | Rock y metal | ✅ | Reseñas `Artista – Título Review` con nota sobre 5 |
| **Distorted Sound** | Rock y metal | ✅ | Reseñas `ALBUM REVIEW: Título – Artista` con nota sobre 10 |
| **Blabbermouth** | Rock y metal / hard rock | ✅ | Anuncios de discos de metal y hard rock (`ARTIST To Release 'Title' Album…`). Su RSS solo trae los ~30 últimos titulares: sirve para la ejecución semanal, no para el pasado |
| **Louder Than War** | Punk, post-punk, indie | ✅ | Reseñas `Artista: Título – Album Review` y anuncios |
| **Psychedelic Baby Magazine** | Psicodelia, garage, prog | ✅ | Anuncios de discos |
| Punk Rock Theory | Punk | ⚠️ Desactivada | Leídos 40 titulares: todos sencillos o vídeos, ningún álbum |
| Post-Punk.com | Dark wave / post-punk | ⚠️ Solo su lista anual | Los titulares son frases ("La banda X explora… en “Título”") y no separan el artista; sí se usa su lista del año |
| Synthpop Fanatic | Synth-pop | ⚠️ Solo su lista anual | Poca actividad de discos (entrevistas y canciones del mes) |
| Electrozombies | Dark wave | ❌ | Solo canciones sueltas |
| NewRetroWave | Synthwave | ❌ | Su RSS lleva parado desde julio de 2026 |
| Making a Scene | Blues / roots | ❌ | Titulares `Artista TÍTULO` sin separador fiable |
| Elmore Magazine | Blues / roots | ❌ | RSS con 3 entradas, la última de agosto |
| No Clean Singing | Metal extremo | ❌ No se usa | Titulares en mayúsculas mezclando estrenos de canciones y discos |
| IDIOTEQ | Hardcore | ❌ No se usa | Titulares narrativos, casi siempre de canciones |
| Invisible Oranges | Metal | ❌ | Su `robots.txt` no permite el feed |
| Ghost Cult, Cvlt Nation | Metal / dark | ❌ | Verificación de Cloudflare |
| New Noise, Northern Transmissions, The Big Takeover, Kerrang! | — | ❌ | Sin RSS (o 404) |

### Listas de fin de año (para "Lo mejor de cada año")

| Lista | Familia | Años | Estado |
|---|---|---|---|
| Heavy Harmonies: Best CDs | Hard rock / AOR | 2019–2025 (2016–2018 tienen otro formato) | ✅ |
| Saving Country Music: Essential Albums | Country / Americana | 2020–2025 | ✅ |
| Saving Country Music: AOTY nominees | Country / Americana | 2025 | ✅ |
| Holler: Best Country Music Albums | Country | 2025 (plantilla por año) | ✅ |
| Country Universe: The Forty Best | Country | 2025 (dirección con fecha: se añade cada año) | ✅ |
| Rush On Rock: Best melodic rock albums | Hard rock / AOR | 2025 (dirección con fecha) | ✅ |
| Classic Rock (Louder): 50 best rock albums | Hard rock / rock | 2025 (plantilla) | ✅ |
| Get Ready to ROCK!: Reviewer selections | Hard rock / rock | 2025 (dirección con número) | ✅ |
| Paste: The 50 best albums | Todas (indie sobre todo) | 2025 (plantilla) | ✅ |
| Beats Per Minute: Top 50 | Todas (indie sobre todo) | 2025 (plantilla) | ✅ |
| **Year End Lists** (yearendlists.com): todas las listas de discos del año (Mojo, Uncut, Decibel, AllMusic, Clash, Rough Trade, críticos…) | Todas | 2025 (≈135 listas) y 2026 (las que se van publicando) | ✅ Sugerida por el usuario. `robots.txt` solo prohíbe `/search`. Incluye las de **AllMusic**, que no se puede leer directamente |
| **Roots Music Report**: gráficas anuales de álbumes (Country, Folk, Bluegrass, Blues, Blues Rock; 50 primeros) | Country / Blues | 2025 y siguientes, solo años cerrados (plantilla por año) | ✅ Basadas en las radios de raíces: popularidad, no crítica |
| Rush On Rock: Best blues albums | Blues | 2025 (dirección con fecha) | ✅ |
| Rush On Rock: Best melodic rock albums | Hard rock / AOR | 2025 | ⛔ **Desde el 27-nov muestra una verificación anti-bots** ("Please wait while your request is being verified") en esa página. No se intenta saltar: queda como "bloqueada" en el informe. La de blues del mismo sitio sigue leyéndose |
| Synthpop Fanatic: The 25 best synthpop albums | Synthwave y dark wave | 2025 (plantilla por año) | ✅ |
| Post-Punk.com: The best of the year | Synthwave y dark wave / post-punk | 2025 (plantilla por año) | ✅ |
| Punk, metal y emo | — | — | Ya entran por Year End Lists: Alternative Press, Kerrang!, Louder Than War (top 100), Decibel, Loudwire, Ian Cohen (emo), A.A. Dowd (metal) |
| Treble: 50 best | — | — | ❌ Verificación de Cloudflare |
| Whiskey Riff: 40 best, Loudwire: best rock & metal | — | — | ❌ La lista no está en la página (se carga aparte) |

### Webs sociales y de recomendación (22-nov)

| Web | Qué es | ¿Se usa? |
|---|---|---|
| **Shfl** (theshfl.com) | Selección de discos recomendados por músicos y críticos, con página por año | ✅ Como **lista anual** ("selección de 2025/2026") para "Lo mejor del año". `/year/` está permitido; `/best-of` no (se respeta) |
| Musicboard (musicboard.app) | Red social de valoraciones (estilo Letterboxd) | ❌ La página solo funciona con JavaScript y su `robots.txt` bloquea expresamente a los rastreadores de IA. Se respeta. Idea de UX: valoraciones y listas de usuarios (no aplicable sin comunidad) |
| MusicTaste (musictaste.xyz) | Red social de reseñas y listas | ❌ Solo funciona con JavaScript (sus datos van por una API interna, que no se usa) |

## 7. Resumen

- **En uso: 30 fuentes activas en `data/fuentes.yaml`.** Son 13 de prensa y listados de country, 8 de hard rock, 2 generalistas (Pause & Play y Bandcamp Daily), 6 de sellos y la comprobación de Bandcamp. Hay otras 3 desactivadas: Americana Highways, pendiente de tu OK, y Sleaze Roxx y Rock & Blues Muse, por su `robots.txt`. A eso se suma el enriquecimiento con MusicBrainz, Cover Art Archive y Bandcamp. Las que fallen o se bloqueen en una ejecución quedan anotadas en `data/estado_fuentes.json` y en el informe.
- **Descartadas:**
  - Por verificación anti-bots: Album of the Year, Metacritic, AllMusic, The Rockpit, Prog Archives y My Global Mind.
  - Por `robots.txt`: Sleaze Roxx y Rock & Blues Muse.
  - Por otros motivos: Rounder (sin página de novedades), Yep Roc (web parada desde 2024), Free Dirt (error de conexión segura), Thirty Tigers (sin página de novedades) y HNE (no responde).
- **El mayor problema** para el objetivo sigue siendo que **Album of the Year no se puede leer**, así que no hay comparación directa con él.

## Sustitutos de Heavy Harmonies (28-nov-2026)

Heavy Harmonies sirve a las máquinas de GitHub unas reglas (robots.txt) que no permiten leerla. Se respeta y se
añaden fuentes de AOR y rock clásico que sí lo permiten (comprobado su robots.txt y que no hay verificación anti-bots):

| Fuente | Qué da | Estado |
|---|---|---|
| Ultimate Classic Rock – New Music Releases | Calendario de rock del mes en curso, por día (`ucr_lanzamientos`, mixta: solo entran los de nuestros géneros; libros, DVD y reediciones fuera) | ✅ |
| Burning Minds / Art of Melody Music | Lanzamientos de AOR, melodic rock y westcoast con fecha (`burningminds_aor`; sencillos fuera) | ✅ |
| Frontiers Music (sello principal de AOR) | Su web es una tienda dinámica: no hay lista legible sin JavaScript | ⛔ pendiente de otra vía |
| MelodicRock.com, Pride & Joy | Permiten leer; falta escribir sus reglas | ⬜ |
| Fireworks Magazine | Muestra verificación anti-bots | ❌ descartada (regla del usuario) |
