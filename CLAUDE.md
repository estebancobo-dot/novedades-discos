# Novedades discográficas — instrucciones para cualquier sesión

Léelo entero antes de hacer nada. El trabajo debe poder **reanudarse sin perder nada** si una sesión se
corta (límite de tokens, de sesión o semanal).

## Dónde está todo

| Qué | Dónde |
|---|---|
| **Progreso: qué se está haciendo, último paso y el siguiente** | `docs/progreso.md` ← **empieza aquí** |
| Plan único (bloques V, W, A–G, con estado y validación) | `docs/plan.md` |
| Requisitos de la web y de los procesos (IDs A–K, P) | `docs/requisitos-web.md` |
| Requisitos de datos y fuentes (1–40) | `docs/requisitos.md` |
| Requisitos en formato que lee la validación automática | `data/requisitos.yaml` |
| Validación automática (resultado de la última ejecución) | `docs/validacion.md`, `data/validacion.json` |
| Estudio del estado del arte (repetible) | `docs/estado-del-arte/README.md`, `estudio/` |
| Arquitectura | `docs/arquitectura.md` |

## Cómo se trabaja

1. Lee `docs/progreso.md` y sigue con el "Siguiente paso".
2. Trabaja en pasos pequeños. **Después de cada paso**: pruebas (`python -m pytest -q`; si toca la web,
   `node tests/e2e/web.mjs site`), actualiza `docs/progreso.md` y sube (`git commit` + `git push`).
   Nada importante puede quedar solo en el chat.
3. Lo que se valide debe quedar **automático** (una comprobación en `scraper/validar.py`, una prueba o una
   regla), nunca "lo revisé a mano en el chat". Si hace falta una revisión humana, se guarda su resultado
   como dato de referencia (p. ej. `data/revision_clasificacion.csv`) y se comprueba solo cada semana.
4. Cambios de la web: capturas del móvil al usuario **antes** de publicar en `main`.
5. Explica las cosas al usuario en español sencillo, sin jerga técnica.

## Reglas del usuario (obligatorias)

- Si aparece un captcha o un bloqueo: **parar y avisar. No intentar saltárselo** (tampoco desde otras
  máquinas, redes o servicios intermedios).
- Bandcamp ≤ 1 petición / 4 s; MusicBrainz ≤ 1 / s; respetar `robots.txt`.
- No inventar datos ni fuentes. Si algo no funciona, decirlo y seguir con el resto.
- **No gastar dinero**: nada de API de pago. El LLM es solo el del plan Pro (en sesión o con
  `CLAUDE_CODE_OAUTH_TOKEN` en la Action).
- Todo configurable (`data/*.yaml`), sin datos escritos en el código.
- Solo discos en inglés; taxonomía cerrada (`data/taxonomia.yaml`): nunca crear subgéneros, proponerlos.
- Secretos solo como secretos del repositorio; nunca pedirlos en el chat.
- Ramas: trabajar en `claude/discografia-country-rock-web-a98s2b`; `main` es lo publicado.
