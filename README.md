# Novedades discográficas: country / americana / folk, hard rock / AOR y rock, pop y afines

Web estática con los álbumes nuevos en inglés de las dos familias principales (country ·
americana · folk y hard rock · AOR) y de las familias "en foco" de rock, pop y afines (rock y
metal, punk y garage, indie y pop-rock, blues, synthwave y dark wave, cantautores). Recoge todo
2026 y lo anunciado para los próximos meses, y tiene una vista "Lo mejor del año" a partir de
las reseñas y de las listas de fin de año. Se actualiza cada semana con una GitHub Action y se
publica en GitHub Pages.

- **Web:** `site/`, una cuadrícula de portadas por semana, con ficha y filtros. Pensada para móvil.
- **Informe:** [`docs/informe.md`](docs/informe.md), con cifras, comparación con el mercado y etiquetas pendientes.
- **Fuentes:** [`docs/fuentes.md`](docs/fuentes.md), con qué webs se leen, cómo y cuáles se descartaron.
- **Arquitectura:** [`docs/arquitectura.md`](docs/arquitectura.md): persistencia, tolerancia a fallos, pruebas y qué está validado.
- **Plan:** [`docs/plan.md`](docs/plan.md) (tareas con entradas, salida, validación y estado) · [`docs/requisitos.md`](docs/requisitos.md) (cada petición y su estado) · [`docs/estado-del-arte.md`](docs/estado-del-arte.md) (alternativas y decisiones por capa).

## Todo se configura sin tocar código

| Quiero… | Edito |
|---|---|
| Añadir o quitar una web | `data/fuentes.yaml`: una entrada con su dirección y sus reglas (o `activa: false`). |
| Añadir un subgénero, un alias o una familia nueva | `data/taxonomia.yaml`. La web y los filtros se adaptan solos. |
| Cambiar la ventana (5 meses), qué es un EP, el idioma o el ritmo de peticiones | `data/config.yaml` |
| Corregir a qué subgénero va una etiqueta | `data/mapeo_etiquetas.csv` |

Para probar una fuente nueva sin guardar nada: `python -m scraper.probar ID --texto`.

## Cómo funciona

```
python -m scraper.pipeline [--incremental] [--desde=FASE]   # todas las fases, reanudable si se corta
```

Fase a fase:

```
python -m scraper.recoger [--incremental]   # lee las fuentes, MusicBrainz y Bandcamp → data/candidatos.json
python -m scraper.recoger --solo=ID1,ID2 --fusionar   # relee solo esas fuentes y las suma a lo ya recogido
python -m scraper.enriquecer                # Deezer (todos), Wikidata, Discogs, iTunes y Last.fm (sin subgénero)
python -m scraper.clasificar                # taxonomía + mapeo de etiquetas → data/discos.json
python -m scraper.mapear                    # etiquetas nuevas → subgénero con Wikidata (sin LLM)
python -m scraper.informe                   # → docs/informe.md
python -m scraper.web                       # → site/data/discos.json
```

- **Educado con las webs:** se identifica como `music-release-tracker`, respeta `robots.txt`,
  hace como máximo 1 petición cada 2 s por web (Bandcamp, 1 cada 4 s; MusicBrainz, 1/s) y guarda
  una copia local de lo ya descargado. Si una web muestra una verificación anti-bots, se deja y
  se anota en el informe; nunca se intenta saltar.
- **Etiquetas nuevas:** las que no encajan en la taxonomía se resuelven **una sola vez** y quedan en
  `data/mapeo_etiquetas.csv`: automáticamente con la jerarquía de géneros de Wikidata (sin LLM ni
  coste) y, en una sesión de Claude Code, con el LLM para lo que quede.
- **Nunca se crean subgéneros nuevos automáticamente:** se proponen en el informe.

## Claves opcionales (secretos del repositorio)

En **Settings → Secrets and variables → Actions → New repository secret**:

| Secreto | Para qué | Sin él |
|---|---|---|
| `LASTFM_KEY` | Etiquetas de los oyentes de Last.fm para clasificar mejor | Se omite Last.fm |
| `DISCOGS_TOKEN` | Buscar en Discogs discos sin enlace directo | Solo se consultan los discos con enlace en MusicBrainz |
| `CLAUDE_CODE_OAUTH_TOKEN` | Que Claude, **con tu plan Pro (sin coste extra)**, clasifique cada semana las etiquetas que Wikidata no resuelva. Se genera una vez en tu ordenador con Claude Code: `claude setup-token` | Las etiquetas se resuelven solo con Wikidata |

## Publicación (una sola vez)

1. Fusiona la rama de trabajo en `main`. Las Actions programadas solo se ejecutan en la rama principal.
2. En GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. En **Actions → Actualización de datos y web → Run workflow**, lánzala la primera vez a mano.
   Después se ejecuta sola cada sábado.

## Pruebas

```
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest              # 85 pruebas: escenarios normales, de borde, de error y de extremo a extremo
node tests/e2e/web.mjs site   # la web en un navegador real (móvil y escritorio); requiere Playwright
```

Se ejecutan solas en GitHub en cada envío (`.github/workflows/pruebas.yml`).
