"""Mapeo de etiquetas con un LLM (Claude, API de Anthropic). Solo se usa si existe la clave
(variable de entorno indicada en config.yaml, por defecto ANTHROPIC_API_KEY); sin clave no hace
nada y el mapeo sigue con Wikidata.

Cada etiqueta se pregunta una sola vez: la respuesta queda en data/mapeo_etiquetas.csv.
El modelo solo puede contestar con ids de subgénero que existen en data/taxonomia.yaml o
"ninguno": la salida va con un esquema JSON y además se valida aquí; lo que no cuadre se descarta
y la etiqueta sigue pendiente. Nunca se crean subgéneros."""
from __future__ import annotations

import json
import os

from .clasificar import Taxonomia

ESQUEMA = {
    "type": "object",
    "properties": {
        "respuestas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "etiqueta": {"type": "string"},
                    "subgeneros": {"type": "array", "items": {"type": "string"}},
                    "propuesta": {"type": "string"},
                },
                "required": ["etiqueta", "subgeneros", "propuesta"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["respuestas"],
    "additionalProperties": False,
}

INSTRUCCIONES = """You map free-form music tags (from music press, Bandcamp, MusicBrainz, Discogs, Last.fm, Apple Music)
to the subgenre ids of a closed taxonomy. Answer for every tag you are given, in the same order.

Rules:
- "subgeneros": 0 to 3 ids, copied exactly from the taxonomy below. Use an id only when the tag clearly
  names that style or a close synonym/spelling variant of it. Prefer the most specific id.
- Return an empty list when the tag is not a music style covered by the taxonomy: places, people, bands,
  labels, moods, themes, instruments, decades, formats, generic words ("music", "new"), or a genre that
  the taxonomy does not contain (e.g. techno, jazz, hip hop).
- "propuesta": only when the tag is a real, reasonably established music genre that belongs to the
  rock/pop/folk/country/blues world but has no id in the taxonomy, write its usual English name
  (e.g. "cajun"); otherwise an empty string.
- Never invent ids. Do not explain.

Taxonomy (id: name — family — description):
"""


def _taxonomia_texto(tax: Taxonomia, datos: dict) -> str:
    lineas = []
    for fam, fd in datos["familias"].items():
        for subs in fd["grupos"].values():
            for sid, sd in subs.items():
                desc = (sd.get("descripcion") or "").strip()
                alias = ", ".join(str(a) for a in (sd.get("alias") or [])[:6])
                lineas.append(f"{sid}: {sd.get('nombre', sid)} — {fam}" + (f" — {desc}" if desc else "")
                              + (f" (also: {alias})" if alias else ""))
    return "\n".join(lineas)


def validar(respuestas: list[dict], pedidas: list[str], tax: Taxonomia) -> dict[str, tuple[str, str]]:
    """Solo acepta respuestas para etiquetas pedidas y con ids existentes. → {etiqueta: (sub, nota)}"""
    pedidas_set = set(pedidas)
    out = {}
    for r in respuestas:
        et = r.get("etiqueta")
        if et not in pedidas_set or et in out:
            continue
        subs = [s for s in r.get("subgeneros") or [] if isinstance(s, str)]
        if any(s not in tax.sub for s in subs):
            continue                      # id inventado: no se acepta, la etiqueta sigue pendiente
        prop = (r.get("propuesta") or "").strip()
        out[et] = ("|".join(dict.fromkeys(subs[:3])) or "ninguno", f"propuesta: {prop}" if prop and not subs else "")
    return out


class MapeadorLLM:
    def __init__(self, cfg: dict, tax: Taxonomia, datos_tax: dict, cliente=None):
        self.cfg = cfg or {}
        self.tax = tax
        self.modelo = self.cfg.get("modelo", "claude-opus-5-5")
        self.esfuerzo = self.cfg.get("esfuerzo", "low")
        self.lote = int(self.cfg.get("lote", 50))
        self.sistema = INSTRUCCIONES + _taxonomia_texto(tax, datos_tax)
        self.cliente = cliente
        self.error = None
        self.uso = {"peticiones": 0, "entrada": 0, "salida": 0, "cache": 0}

    @staticmethod
    def disponible(cfg: dict) -> bool:
        return bool((cfg or {}).get("activo")) and bool(os.environ.get((cfg or {}).get("variable_clave", "ANTHROPIC_API_KEY")))

    def _cliente(self):
        if self.cliente is None:
            import anthropic                  # solo hace falta si se usa el LLM
            self.cliente = anthropic.Anthropic(api_key=os.environ[self.cfg.get("variable_clave", "ANTHROPIC_API_KEY")],
                                               max_retries=4)
        return self.cliente

    def mapear(self, etiquetas: list[str]) -> dict[str, tuple[str, str]]:
        """Pregunta por lotes. Si una petición falla, se para y lo no preguntado sigue pendiente."""
        resultado = {}
        for i in range(0, len(etiquetas), self.lote):
            lote = etiquetas[i:i + self.lote]
            try:
                respuestas = self._preguntar(lote)
            except Exception as e:            # red, clave, límite, saturación: se deja para otra vez
                self.error = f"{type(e).__name__}: {str(e)[:200]}"
                break
            if respuestas is None:
                continue
            resultado.update(validar(respuestas, lote, self.tax))
        return resultado

    def _preguntar(self, lote: list[str]) -> list[dict] | None:
        r = self._cliente().beta.messages.create(
            model=self.modelo,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",                       # si el modelo declina, otro modelo responde
            system=[{"type": "text", "text": self.sistema, "cache_control": {"type": "ephemeral"}}],
            output_config={"effort": self.esfuerzo, "format": {"type": "json_schema", "schema": ESQUEMA}},
            messages=[{"role": "user", "content": "Tags:\n" + "\n".join(f"- {t}" for t in lote)}],
        )
        self.uso["peticiones"] += 1
        u = getattr(r, "usage", None)
        if u is not None:
            self.uso["entrada"] += getattr(u, "input_tokens", 0) or 0
            self.uso["salida"] += getattr(u, "output_tokens", 0) or 0
            self.uso["cache"] += getattr(u, "cache_read_input_tokens", 0) or 0
        if r.stop_reason in ("refusal", "max_tokens"):
            return None
        texto = next((b.text for b in r.content if getattr(b, "type", "") == "text"), "")
        try:
            return json.loads(texto).get("respuestas", [])
        except (ValueError, AttributeError):
            return None
