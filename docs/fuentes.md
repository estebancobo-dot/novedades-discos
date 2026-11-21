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

### Bandcamp: ❌ BLOQUEADO

Todas las páginas de Bandcamp probadas (15 subdominios de sellos, a 1 petición cada 4 s)
devuelven **"Client Challenge – JavaScript is disabled"**, una verificación anti-bots.
**Se ha parado y no se intenta saltar.** Consecuencias:
- Las portadas, pistas y etiquetas se sacan de **MusicBrainz + Cover Art Archive** y de las propias fuentes.
- El "% en Bandcamp" del informe se calcula con los **enlaces a Bandcamp que guarda MusicBrainz**, no visitando Bandcamp.
- El robot semanal volverá a probar **una sola** página de Bandcamp. Si sigue bloqueada, no hará más peticiones y lo dirá en el informe.

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

## 6. Resumen

- **Funcionan bien:** 14. Prensa country: Saving Country Music, Americana UK y Twangville. Hard rock: Heavy Harmonies, Fireworks, Angelic Warlord y Get Ready to Rock. Sellos: New West, Oh Boy, Frontiers, ROAR y Silver Lining. Enriquecimiento: MusicBrainz y Cover Art Archive.
- **A medias:** 5 (Holler, Whiskey Riff, Country Universe, MelodicRock y Escape).
- **Descartadas:** 7 (Bandcamp, Album of the Year, Rounder, Yep Roc, Free Dirt, Thirty Tigers y HNE).
- El mayor problema para el objetivo es que **no se puede leer Album of the Year**, y por tanto no hay comparación directa con él, y que **Bandcamp está bloqueado**.
