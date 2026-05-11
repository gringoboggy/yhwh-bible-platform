"""γ.2 — Greek interlinear API handler.

Direct mirror of `scripts.api.hebrew` — see that module for the
full rationale. Diffs vs Hebrew:
    - Strong's Greek numbers use the G prefix (5,523 entries:
      G1 through G5523).
    - The upstream JSON uses `translit` where Hebrew uses `xlit`;
      `StrongsGreekEntry.xlit` normalizes both onto one field.
    - Greek lexicon entries don't have a `pron` (pronunciation)
      field — the dict-class still exposes one for shape parity
      but it'll typically be empty for Greek entries. The API
      surfaces it consistently so γ.1 and γ.2 callers can share
      rendering code.

Future γ.2.x can wire results into the build_edition.py popup
pipeline so the buyer-facing EPUB renders Greek interlinear data
inline with NT verses (parallel to γ.1.x for OT/Hebrew).
"""

from __future__ import annotations

import re

_VALID_INPUT = re.compile(r"^[Gg]?\d+$")


def _normalize(num: str) -> str | None:
    """Normalize input to canonical 'G<digits>' form.

    Accepts: 'G1', 'g1', '1', '0001' (zero-padded).
    Strips leading zeros after the G.
    Returns None for any other shape.
    """
    if not isinstance(num, str):
        return None
    s = num.strip()
    if not _VALID_INPUT.match(s):
        return None
    digits = s.lstrip("GgH").lstrip("0")
    if not digits:
        return None  # input was 'G0' or '0' — Strong's numbers start at 1
    return f"G{digits}"


def api_greek_lookup(num: str) -> dict:
    """Look up a Strong's Greek entry by number. Returns the entry
    as a JSON-ready dict, or an error envelope with HTTP status.

    Lazy import of `scripts.core.sources` so the api module stays
    cheap to import in environments without the lexicon cache
    populated yet (the SourceMissingError gets surfaced as a 503).
    """
    canonical = _normalize(num)
    if canonical is None:
        return {
            "status": "error",
            "code": "invalid_format",
            "http": 400,
            "message": f"expected G<digits> (e.g. 'G1' or '1'); got: {num!r}",
        }

    from scripts.core import sources

    try:
        lex = sources.strongs_greek()
    except sources.SourceMissingError as e:
        return {
            "status": "error",
            "code": "lexicon_missing",
            "http": 503,
            "message": str(e),
        }

    entry = lex.get(canonical)
    if entry is None:
        return {
            "status": "error",
            "code": "unknown_number",
            "http": 404,
            "message": f"unknown Strong's Greek: {canonical}",
        }

    return {
        "status": "ok",
        "number": entry.number,
        "lemma": entry.lemma,
        "xlit": entry.xlit,
        "pron": entry.pron,
        "derivation": entry.derivation,
        "definition": entry.definition,
        "kjv_def": entry.kjv_def,
        "attribution": entry.attribution,
    }
