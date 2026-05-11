"""γ.1 — Hebrew interlinear API handlers.

Lookup endpoint over the Strong's Hebrew lexicon (cached at
`content/sources/strongs_hebrew.json`, ~2 MB, populated via
`fetch_sources.py`). Each entry has lemma, transliteration,
pronunciation, derivation, definition, KJV-usage summary, and
attribution.

Public route surface (registered in scripts/web.py route tables):
    GET /api/hebrew/<num>   — single entry by Strong's number.
                              Accepts "H1" / "h1" / "1" — all
                              normalize to canonical "H1".

Response shape (success):
    {
      "status": "ok",
      "number": "H1",
      "lemma": "אָב",
      "xlit": "ʼâb",
      "pron": "awb",
      "derivation": "a primitive word;",
      "definition": "father, in a literal and immediate, ...",
      "kjv_def": "chief, (fore-) father(-less), [idiom] ...",
      "attribution": "Strong's H1, A Concise Dictionary..."
    }

Response shape (404 unknown number):
    {"status": "error", "code": "unknown_number",
     "http": 404, "message": "unknown Strong's Hebrew: H99999"}

Response shape (400 invalid format):
    {"status": "error", "code": "invalid_format",
     "http": 400, "message": "expected H<digits>; got: ..."}

Future γ.* phases will build on this:
    γ.2 — Greek (parallel `/api/greek/<num>`)
    γ.1.x — wire results into the build_edition.py popup pipeline
            so the buyer-facing EPUB renders Hebrew interlinear
            data inline with OT verses.
"""

from __future__ import annotations

import re

_VALID_INPUT = re.compile(r"^[Hh]?\d+$")


def _normalize(num: str) -> str | None:
    """Normalize input to canonical 'H<digits>' form.

    Accepts: 'H1', 'h1', '1', '0001' (zero-padded).
    Strips leading zeros after the H.
    Returns None for any other shape.
    """
    if not isinstance(num, str):
        return None
    s = num.strip()
    if not _VALID_INPUT.match(s):
        return None
    digits = s.lstrip("HhH").lstrip("0")
    if not digits:
        return None  # input was 'H0' or '0' — Strong's numbers start at 1
    return f"H{digits}"


def api_hebrew_lookup(num: str) -> dict:
    """Look up a Strong's Hebrew entry by number. Returns the entry
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
            "message": f"expected H<digits> (e.g. 'H1' or '1'); got: {num!r}",
        }

    from scripts.core import sources

    try:
        lex = sources.strongs_hebrew()
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
            "message": f"unknown Strong's Hebrew: {canonical}",
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
