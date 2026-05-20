"""Witness-record schema + honesty-contract validator (Phase-2 Unit C)."""

from __future__ import annotations

import json
import re

# Canonical honesty-contract sentinel shared by the collation engine.
# manuscript_collation imports this constant; never redefine it there.
ILLEGIBLE = "⟦illegible⟧"

_TOP = {
    "witness",
    "book",
    "chapter",
    "source_images",
    "folio_sigla",
    "verses",
    "transcription_notes",
}
_VK = {"v", "column", "line_start", "geez", "tokens", "uncertain"}

# Ethiopic numeral range U+1369 (፩) … U+137C (፼).
# In geez fields they are concatenated directly to adjacent words without spaces,
# but the tokens array lists them as standalone items.  We insert spaces around
# them before the whitespace-split so that the geez↔tokens invariant holds for
# both witnesses.
_NUMERAL_RE = re.compile(r"([፩-፼])")

# ── non-Ethiopic contamination screen ────────────────────────────────────────
# A literal Latin 'f' (U+0066) once slipped into a transcription; this screen
# is the corrected adversarial check folded inline (formerly run by hand each
# chapter) so it is enforced for every witness.
#
# ALLOWED in a geez field = Ethiopic block U+1200–U+137F ('ሀ'..'፿') ∪ ASCII
# space U+0020 ∪ the sanctioned rubric-cross ✣ U+2723. ✣ is a LEGITIMATE
# inline section divider that _geez_to_tokens already strips; it occurs 94×
# in the immutable Samuel calibration goldens' geez, so it MUST be whitelisted
# here or the screen would wrongly reject the ground-truth evidence.
#
# The ⟦illegible⟧ honesty sentinel is required by the bijection check, so the
# whole substring is removed from geez before the per-char test, and a token
# equal to the whole sentinel is exempt from the per-char token test.
_GEEZ_EXTRA_ALLOWED = {" ", "✣"}  # U+0020, U+2723


def _is_ethiopic(c: str) -> bool:
    """True iff c is in the Ethiopic block U+1200–U+137F."""
    return "ሀ" <= c <= "፿"


def _screen_non_ethiopic(v: dict) -> list[str]:
    """Flag Latin-letter / mojibake contamination in one verse.

    geez:  with every whole ⟦illegible⟧ sentinel removed, every remaining
           character must be Ethiopic, ASCII space, or rubric-cross ✣.
    tokens: every token that is not exactly the ⟦illegible⟧ sentinel must
           consist entirely of Ethiopic-block characters (tokens never
           legitimately carry space or ✣ — _geez_to_tokens strips them).
    """
    out: list[str] = []
    vid = v["v"]
    for c in v["geez"].replace(ILLEGIBLE, ""):
        if not (_is_ethiopic(c) or c in _GEEZ_EXTRA_ALLOWED):
            out.append(f"v{vid}: non-Ethiopic char {hex(ord(c))} {c!r} in geez")
    for t in v["tokens"]:
        if t == ILLEGIBLE:
            continue
        if not all(_is_ethiopic(c) for c in t):
            out.append(f"v{vid}: non-Ethiopic token {t!r}")
    return out


def _geez_to_tokens(geez: str) -> list[str]:
    """Normalise a geez string to a token list matching the tokens field.

    Steps:
    1. Replace Ethiopic wordspace U+1361 (፡), Ethiopic full-stop U+1362 (།),
       Ethiopic clause-comma U+1363 (፣), and rubric-cross U+2723 (✣) with an
       ASCII space.  GG uses plain ASCII spaces between words; CAM uses ፡/།
       as separators (sometimes with surrounding ASCII spaces, sometimes not).
       ✣ appears in some GG geez strings as an inline section divider that is
       not itself a word.
    2. Insert spaces around any Ethiopic numeral glyph (U+1369–U+137C) so that
       e.g. '፩ብእሲ' becomes ' ፩  ብእሲ ' and splits correctly.  Numerals appear
       concatenated to adjacent words in the geez field but as standalone tokens.
    3. Split on whitespace and discard empty strings.
    """
    g = geez
    for ch in ("፡", "።", "፣", "✣"):  # ፡ ። ፣ ✣
        g = g.replace(ch, " ")
    g = _NUMERAL_RE.sub(r" \1 ", g)
    return g.split()


def validate_witness(d: dict) -> tuple[bool, list[str]]:
    """Validate a single witness record dict.

    Returns (ok, errors) where ok is True iff errors is empty.
    """
    e: list[str] = []

    # ── top-level keys ────────────────────────────────────────────────────────
    if set(d) != _TOP:
        e.append(f"top keys {sorted(set(d))} != {sorted(_TOP)}")

    # ── witness identity ──────────────────────────────────────────────────────
    if d.get("witness") not in ("GG", "CAM"):
        e.append("witness not GG/CAM")

    # ── per-verse checks ──────────────────────────────────────────────────────
    for i, v in enumerate(d.get("verses", [])):
        if set(v) != _VK:
            e.append(f"v[{i}] keys {sorted(set(v))} != {sorted(_VK)}")
            continue

        # geez↔tokens invariant
        computed = _geez_to_tokens(v["geez"])
        if computed != v["tokens"]:
            e.append(f"v{v['v']}: geez<->tokens mismatch (computed={computed[:10]}, stored={v['tokens'][:10]})")

        # honesty bijection: every ⟦illegible⟧ token must have exactly one
        # corresponding uncertain entry with marker=="illegible"
        ill_tok = sum(1 for t in v["tokens"] if t == ILLEGIBLE)
        ill_mk = sum(1 for u in v["uncertain"] if u.get("marker") == "illegible")
        if ill_tok != ill_mk:
            e.append(f"v{v['v']}: illegible bijection {ill_tok}!={ill_mk}")

        # uncertain entry sanity
        for u in v["uncertain"]:
            ti = u.get("token_index", -1)
            if not (isinstance(ti, int) and 0 <= ti < len(v["tokens"])):
                e.append(f"v{v['v']}: token_index OOB ({ti})")
            if u.get("marker") not in ("uncertain", "damaged", "illegible"):
                e.append(f"v{v['v']}: bad marker {u.get('marker')!r}")

        # non-Ethiopic contamination screen (Latin letters / mojibake);
        # ✣ U+2723 and the ⟦illegible⟧ sentinel are sanctioned exceptions
        e.extend(_screen_non_ethiopic(v))

    # ── verse contiguity 1..N ─────────────────────────────────────────────────
    vs = [v["v"] for v in d.get("verses", []) if isinstance(v, dict) and "v" in v]
    if vs and vs != list(range(1, len(vs) + 1)):
        e.append("verses not contiguous 1..N")

    return (not e), e


def write_witness(
    *,
    witness: str,
    book: str,
    chapter: int,
    source_images: list,
    folio_sigla: list,
    verses: list,
    transcription_notes: str,
    output_path,
) -> dict:
    """Build a canonical witness record, validate it, and atomic-write to disk.

    Each ``verses`` entry needs ``{v, column, line_start, geez, uncertain}``.
    ``tokens`` is derived from ``geez`` via ``_geez_to_tokens`` (so no caller
    can drift the geez↔tokens bijection). Each ``uncertain`` entry is a dict
    with at least ``{marker, note}`` and optionally ``token_index``. When
    ``marker == "illegible"`` and no ``token_index`` is supplied, the writer
    auto-assigns the next un-claimed ⟦illegible⟧ position in tokens. Plain
    string entries are treated as verse-level notes with ``token_index = 0``
    and ``marker = "uncertain"``.

    Raises ``ValueError`` (carrying the validator's error list) if the
    resulting record fails ``validate_witness``. **No file is written when
    validation fails** — transactional, mirroring §9 "Add an uploadable binary
    asset".
    """
    out_verses: list[dict] = []
    for raw in verses:
        geez = raw["geez"]
        tokens = _geez_to_tokens(geez)
        uncertain_out: list[dict] = []
        ill_used: set[int] = set()
        for u in raw.get("uncertain", []):
            if not isinstance(u, dict):
                uncertain_out.append({"token_index": 0, "marker": "uncertain", "note": str(u)})
                continue
            marker = u.get("marker", "uncertain")
            note = u.get("note", "")
            ti = u.get("token_index")
            if marker == "illegible" and ti is None:
                for i, t in enumerate(tokens):
                    if t == ILLEGIBLE and i not in ill_used:
                        ti = i
                        ill_used.add(i)
                        break
            if ti is None:
                ti = 0
            uncertain_out.append({"token_index": ti, "marker": marker, "note": note})
        out_verses.append(
            {
                "v": raw["v"],
                "column": raw["column"],
                "line_start": raw["line_start"],
                "geez": geez,
                "tokens": tokens,
                "uncertain": uncertain_out,
            }
        )

    record = {
        "witness": witness,
        "book": book,
        "chapter": chapter,
        "source_images": list(source_images),
        "folio_sigla": list(folio_sigla),
        "verses": out_verses,
        "transcription_notes": transcription_notes,
    }

    ok, errs = validate_witness(record)
    if not ok:
        raise ValueError(f"witness validation failed: {errs}")

    from .notes_io import atomic_write

    atomic_write(
        str(output_path),
        json.dumps(record, ensure_ascii=False, indent=2),
    )
    return record
