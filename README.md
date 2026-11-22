# Novedades discográficas: country / americana / folk y hard rock / AOR

Web estática con los álbumes nuevos en inglés de dos familias de géneros. Se actualiza
cada semana con una GitHub Action y se publica en GitHub Pages.

- **Web:** `site/`, una cuadrícula de portadas por semana, con ficha y filtros. Pensada para móvil.
- **Informe:** [`docs/informe.md`](docs/informe.md), con cifras, comparación con el mercado y etiquetas pendientes.
- **Fuentes:** [`docs/fuentes.md`](docs/fuentes.md), con qué webs se leen, cómo y cuáles se descartaron.

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
python -m scraper.recoger [--incremental]   # lee las fuentes, MusicBrainz y Bandcamp → data/candidatos.json
python -m scraper.clasificar                # taxonomía + mapeo de etiquetas → data/discos.json
python -m scraper.informe                   # → docs/informe.md
python -m scraper.web                       # → site/data/discos.json
```

- **Educado con las webs:** se identifica como `music-release-tracker`, respeta `robots.txt`,
  hace como máximo 1 petición cada 2 s por web (Bandcamp, 1 cada 4 s; MusicBrainz, 1/s) y guarda
  una copia local de lo ya descargado. Si una web muestra una verificación anti-bots, se deja y
  se anota en el informe; nunca se intenta saltar.
- **Etiquetas nuevas:** las que no encajan en la taxonomía se consultan **una sola vez** a un LLM
  y la respuesta queda en `data/mapeo_etiquetas.csv`. La Action semanal no tiene clave de API, así
  que las nuevas quedan como `pendiente` y se resuelven en una sesión de Claude Code.
- **Nunca se crean subgéneros nuevos automáticamente:** se proponen en el informe.

## Publicación (una sola vez)

1. Fusiona la rama de trabajo en `main`. Las Actions programadas solo se ejecutan en la rama principal.
2. En GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. En **Actions → Actualización semanal → Run workflow**, lánzala la primera vez a mano.
   Después se ejecuta sola cada sábado.
