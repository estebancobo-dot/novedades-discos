# UX: cómo es la web y cómo se compara

Estudio del 22-nov-2026. Las capturas del nicho se hicieron en un iPhone 13 simulado.

**Cómo se analizaron Album of the Year, Rate Your Music, Metacritic y AllMusic:** no se pueden abrir
de forma automática, porque piden la verificación anti-bots de Cloudflare, y las copias del Internet
Archive se descartaron por la misma razón. Sus funciones salen de lo que publican sobre sí mismas:
el registro de cambios de AOTY (citado en búsquedas), los artículos de Wikipedia sobre RYM,
Metacritic y AllMusic, y reseñas o fichas en directorios. **Falta ver su interfaz real.** Para
completarlo, lo mejor son capturas hechas desde un móvil por una persona (ver el final).

## 1. Cómo es nuestra web hoy

| Pantalla | Qué hace | Por qué |
|---|---|---|
| Cabecera fija | Marca, buscador (artista, disco o sello), botón **Filtros** con contador y pestañas de familia | Lo que más se usa, siempre a mano con el pulgar |
| Portada | Bloque **Próximamente** arriba; debajo, una **semana por bloque**, la más reciente primero. Cuadrícula de 2 columnas en móvil y hasta 6 en pantalla grande | Es lo que pediste. La portada del disco es lo que se reconoce de un vistazo |
| Tarjeta | Portada (o un degradado con el nombre si no la hay), artista, título, subgéneros y "N reseñas" | Lo justo para decidir si abrir la ficha |
| Ficha | Hoja que sube desde abajo en móvil (ventana centrada en ordenador). Portada grande, fecha, sello, pistas, subgéneros, **Reseñado en** (con nota), **Aparece en** (las fuentes) y botones para escuchar | Toda la información sin salir de la lista |
| Filtros | Hoja inferior en móvil y panel lateral en ordenador: fechas (por defecto 5 meses), sello y subgéneros en "chips" agrupados, **con el número de discos de cada uno** y botón "Ver N discos" | Se ve el efecto antes de aplicar y nunca se llega a cero resultados sin saberlo |
| Enlaces | Filtros y ficha abierta quedan en la dirección (`?familia=country&sub=honky-tonk#disco=…`) | Se puede compartir o guardar una búsqueda |
| Otros | Modo oscuro automático, carga diferida de portadas y "Ver semanas anteriores" | Rápida en móvil |

## 2. Estado del arte

### a) Grandes agregadores (generalistas)

| Web | Lo mejor | Lo peor (para este uso) |
|---|---|---|
| **Album of the Year** (verificado solo por su registro de cambios) | Nota de crítica y de usuarios con número de reseñas; listas "para escuchar"; filtros de artistas seguidos, escuchado/no escuchado; navegación por década, año, mes y semana | Todos los géneros mezclados; nicho (AOR, red dirt) muy poco cubierto; requiere cuenta para lo personal; bloquea a robots |
| **Rate Your Music** (verificado solo por búsquedas) | Árbol de géneros enorme y "descriptores"; listas filtrables por género, año, país e idioma | Página de novedades históricamente limitada; muy densa, pensada para usuarios registrados |
| **Metacritic** (verificado solo por búsquedas) | Metascore claro; orden por fecha, nota de crítica o de usuarios | Solo discos con muchas reseñas: el nicho casi no aparece; sin subgéneros |
| **AllMusic New Releases** | Selección semanal editada con resumen de cada disco | 10-30 discos por semana; bloquea a robots |
| **Bandcamp Discover** | Combinar varias etiquetas, filtrar por formato y lugar, modo oscuro, reproductor integrado | Solo lo que está en Bandcamp; sin fechas de salida ni reseñas externas |
| **MusicButler / Muspy** | Avisos (correo o RSS) cuando sacan disco los artistas que sigues | Solo artistas que ya conoces; no descubre nada nuevo |

**Qué copiar de cada una:**
- **Metacritic:** junto a la nota, un **extracto de cada reseña** con enlace. Aquí se puede mostrar la primera frase que da el feed de cada reseña.
- **Rate Your Music:** una **taxonomía explicada**: cada género tiene descripción y fuentes. Aquí, una frase por subgénero (qué es westcoast frente a AOR, por ejemplo) al tocar el chip.
- **AllMusic:** el **"Editor's Choice"**. Aquí se marcarían como *Destacado* los discos que la prensa especializada pone entre sus favoritos (la selección principal del Release Radar, las notas de 8/10 o más).
- **Album of the Year:** la **lista para escuchar** (*Spin List*), el filtro de **artistas seguidos** y la navegación por **mes y semana**. Equivalen aquí a "Mi lista", al radar de mis artistas y al índice de meses.

### b) El nicho (las webs que usamos como fuente)

| Web | Lo mejor | Lo peor |
|---|---|---|
| **Saving Country Music, Release Radar** | Selección experta, con anticipación, y comentario de cada disco | Un artículo larguísimo de texto, sin portadas ni filtros, con anuncios emergentes |
| **Pause & Play** | Lista semanal muy completa, con sello y descripción | Tabla de texto de todos los géneros; el aviso de afiliados ocupa la primera pantalla |
| **Wikipedia, List of 2026 albums** | La lista más completa del año, con género y sello | Tablas de escritorio, ilegibles en móvil |
| **Heavy Harmonies** | Base de datos de AOR y hard rock imbatible | Diseño de 2002, sin adaptación a móvil, con anuncios |
| **Loudwire, calendario** | Calendario anual completo | Texto plano, mucho metal y un anuncio que tapa la primera pantalla |
| **Bandcamp Daily, Essential Releases** | Portadas, reproductor y texto editorial | Generalista; aviso de cookies sobre el contenido |

### c) Tu agenda de conciertos (referencia de estilo)
Tiene cosas que esta web todavía no tiene: **"Mis conciertos" guardados en el móvil**, **compartir**,
**calendario `.ics`** por concierto, **suscripción a un calendario por género**, **funciona como app**
(*service worker*) y avisos breves.

## 3. Comparación

### Lo que mejoramos
- **Un solo sitio para dos nichos** que hoy están repartidos entre más de 30 webs, con duplicados eliminados.
- **Subgéneros finos** (AOR, westcoast, red dirt, honky-tonk…) con filtro y recuento. Ningún agregador los tiene y ninguna web del nicho filtra.
- **Portadas y móvil primero**, frente a listas de texto pensadas para escritorio.
- **Sin anuncios ni ventanas emergentes.**
- **Transparencia:** cada disco dice en qué webs aparece y dónde se ha reseñado.
- **Antes:** sección "Próximamente" con lo ya anunciado.
- **Filtros compartibles** por enlace.

### Lo que está igual
- Agrupación por semana o fecha (AOTY, Pause & Play, Loudwire).
- Enlaces para escuchar (Bandcamp, Spotify, Apple…).
- Modo oscuro (Bandcamp).

### Lo que empeoramos (hoy)
- **No hay nota agregada fiable:** solo algunos discos tienen nota (Saving Country Music, Americana UK…), frente al Metascore o la nota de AOTY.
- **No hay votos de usuarios ni comunidad** (AOTY, Rate Your Music).
- **No se puede escuchar dentro de la web** (Bandcamp Daily sí).
- **No hay lista personal, avisos ni calendario** (MusicButler, AOTY y tu propia agenda sí).
- **Solo cuadrícula:** falta una vista de lista compacta para repasar muchos discos rápido (Rate Your Music, Wikipedia).
- **Solo se puede ordenar por fecha:** falta "mejor valorados" o "más reseñados".
- **No se puede instalar como app ni usar sin conexión** (tu agenda sí).

## 4. Mejoras propuestas

**Ahora (dentro de la fase 5, unas 3 horas):**
1. **Mi lista:** guardar discos en el móvil, sin cuentas, como "Mis conciertos".
2. **Escuchar en la ficha:** reproductor de Bandcamp o de Spotify incrustado cuando haya enlace. Spotify sin Premium reproduce fragmentos.
3. **Nota media** en la tarjeta cuando haya notas, y **orden**: recientes, mejor valorados, más reseñados.
4. **Vista de lista** compacta, con un interruptor cuadrícula/lista.
5. **Compartir** un disco o una búsqueda (menú nativo del móvil).
6. **Calendario** de "Próximamente": `.ics` por disco y suscripción por familia.
7. **RSS** por familia y subgénero, generado cada semana.
8. **Instalable como app** y con caché sin conexión (*service worker*), como tu agenda.
9. **Saltar a un mes** con un índice de meses.
10. **Destacados** (al estilo "Editor's Choice") y **descripción de cada subgénero** al tocar su chip.
11. **Extracto de la reseña** junto a la nota, cuando el feed lo dé.

**Más adelante:**
- Radar de **mis artistas**: avisar cuando un artista de "Mi lista" anuncie disco, con MusicBrainz.
- Vista **"Lo mejor del año"** (punto 2 del plan).
- Página por artista y por sello.

## 5. Para completar el estudio (opcional)

Capturas desde tu móvil, navegando con normalidad:
1. **Album of the Year:** la página de novedades (*New Releases*), la de próximos (*Upcoming*) y la ficha de un disco.
2. **Rate Your Music:** *New Music* y el panel de filtros de *Charts*.
3. **Metacritic:** la lista de discos nuevos y la ficha de un disco.
4. **AllMusic:** *New Releases*.
