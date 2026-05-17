"""Witness-record schema + honesty-contract validator (Phase-2 Unit C)."""

from __future__ import annotations

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

    # ── verse contiguity 1..N ─────────────────────────────────────────────────
    vs = [v["v"] for v in d.get("verses", []) if isinstance(v, dict) and "v" in v]
    if vs and vs != list(range(1, len(vs) + 1)):
        e.append("verses not contiguous 1..N")

    return (not e), e
