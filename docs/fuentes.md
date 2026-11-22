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

## 7. Resumen

- **En uso: 30 fuentes activas en `data/fuentes.yaml`.** Son 13 de prensa y listados de country, 8 de hard rock, 2 generalistas (Pause & Play y Bandcamp Daily), 6 de sellos y la comprobación de Bandcamp. Hay otras 3 desactivadas: Americana Highways, pendiente de tu OK, y Sleaze Roxx y Rock & Blues Muse, por su `robots.txt`. A eso se suma el enriquecimiento con MusicBrainz, Cover Art Archive y Bandcamp. Las que fallen o se bloqueen en una ejecución quedan anotadas en `data/estado_fuentes.json` y en el informe.
- **Descartadas:**
  - Por verificación anti-bots: Album of the Year, Metacritic, AllMusic, The Rockpit, Prog Archives y My Global Mind.
  - Por `robots.txt`: Sleaze Roxx y Rock & Blues Muse.
  - Por otros motivos: Rounder (sin página de novedades), Yep Roc (web parada desde 2024), Free Dirt (error de conexión segura), Thirty Tigers (sin página de novedades) y HNE (no responde).
- **El mayor problema** para el objetivo sigue siendo que **Album of the Year no se puede leer**, así que no hay comparación directa con él.
