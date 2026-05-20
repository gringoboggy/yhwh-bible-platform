"""Per-chapter complexity classifier for the dual-manuscript marathon (audit U4).

Codifies which Kings chapters historically fire which failure classes so the
C-2/C-5 transcriber prompt can pre-screen for them.

Derivation:
- 1Ki1, 1Ki2, 1Ki3 — narrative prose; converged in 3–5 rounds against the
  "harmonization-toward-printed-Bible" CARDINAL RULE plus the column/folio-
  boundary scripture-omission make-or-break check (the two pre-1Ki4 method
  notes).
- 1Ki4 — Solomon's officer registry (vv.7–19) + the comparative-wisdom
  name-list with Heman the Ezrahite / Darda son of Mahol (vv.20–34). The C-3
  R1 review on the first transcription found 110+ defects across systematic
  classes that had not fired on prior chapters: `ለ`/`ስ` in toponyms and
  prepositions, `ይ`/`ደ` at verb prefixes and the word "Judah", `ያ`/`ደ` in
  name-final syllables of deputy names, body-vs-rubric cross-glyph mis-
  labels (`❈` U+2748 only for rubrics; `✣` U+2723 for body), and numeral-
  vs-letter (red `ሺ` thousand-suffix mis-read as the fidel `ቯ`). Took 7
  rounds to converge.
- 1Ki15/16 and 2Ki13–17 — divided-kingdom regnal frames carry the LIST
  failure classes plus regnal-year numerals (often 4–5-digit Ethiopic
  multi-glyph sequences) and patronymic chains.

This module is the SINGLE SOURCE for chapter-class facts; the plan template's
class-specific transcriber screens are derived from `chapter_profile()`.

Conservative default: any unknown chapter is NARRATIVE. The classifier's
role is risk-screening (give the transcriber MORE class-specific warnings on
known-hard chapters), not gating.
"""

from __future__ import annotations

# Known list / regnal-frame chapters in Kings + Samuel. Everything not in
# these sets defaults to NARRATIVE. Samuel coverage added at audit U-belt
# 2026-05-20; same scribal hands (GG-00106 + Cambridge Add. 1570) so the
# class-specific screens carry over directly when the Samuel marathon runs.
_LIST_CHAPTERS: dict[str, set[int]] = {
    "1ki": {4},  # officer registry + comparative wisdom names
    "2sa": {
        8,  # David's victories + officers list vv.16-18
        20,  # narrative tail + officers list vv.23-26
        23,  # mighty men list vv.8-39 (heaviest name-fidel density in Samuel)
    },
}

_REGNAL_FRAME_CHAPTERS: dict[str, set[int]] = {
    "1ki": {15, 16},  # Rehoboam/Abijam → Jeroboam/Nadab/Baasha/Elah/Zimri/Omri/Ahab
    "2ki": {13, 14, 15, 16, 17},  # divided-kingdom synchronistic frames + Samaria's fall
    "1sa": {
        13,  # Saul's first regnal frame + war with Philistines
        14,  # Jonathan's exploit + Saul's family list (14:49-52)
        15,  # Saul + Amalek war regnal frame
    },
}

_NARRATIVE_SCREENS = [
    "CARDINAL RULE — anti-harmonization to printed Bible: transcribe the "
    "parchment glyphs even when they differ from the expected Bible. "
    "Wherever a recognisable standard phrase appears in faded text, "
    "transcribe what is actually written and flag `uncertain`; NEVER "
    "substitute the printed form; genuinely unreadable → ⟦illegible⟧ + "
    "matching marker:'illegible', never the expected word.",
    "METHOD NOTE 2 — column/folio-boundary scripture omission: trace text "
    "continuity across EVERY column AND every folio/recto-verso turn; a word "
    "routinely splits across the turn so a verse boundary may NEVER fall "
    "mid-word; never 'resume' at the next column/folio without confirming "
    "the running text is physically continuous (no skipped line/column); "
    "read column-bottom→column-top contiguously.",
]

_LIST_SCREENS = [
    "NAME-FIDEL FAMILY `ለ`/`ስ`: re-verify every `ስ` token in proper nouns "
    "and prepositions — `ለ` (lā) often looks like `ስ` (sā) in this scribal "
    "hand. Tokens at highest risk: `ፈለግ`/`ፈስግ`, `እለ`/`እስ` (relative pronoun), "
    "`ላ`/`ሳ` in toponyms (e.g. `ጋላዓድ` for Gilead).",
    "NAME-FIDEL FAMILY `ይ`/`ደ`: re-verify every word-initial `ደ` and verb-"
    "prefix position. Standard Ge'ez `ይ`-prefixed verbs (`ይበል`, `ይትገበር`, "
    "`ይሰርዑ`, `ይትቀንዩ`, `ይከውን`, `ይስምዑ`) and the proper noun `ይሁዳ` (Judah, "
    "never `ደሁዳ`) must NOT be written with `ደ`.",
    "NAME-FIDEL FAMILY `ያ`/`ደ`: re-verify every word-final `ደ` near the end "
    "of a deputy/king name. Final-syllable `ያ` is systematically misread as "
    "`ደ`: `አኪያድ` / `አኪያል` / `አርንያ` / `ዋልደ` and similar.",
    "CROSS-GLYPH NORMALIZATION: body geez contains only the small four-armed "
    "cross `✣` (U+2723) at clause/phrase boundaries. The large knot/figure-8 "
    "cross `❈` (U+2748) appears ONLY immediately after rubric numerals "
    "(`ክፍል ፴ ❈`) — and rubrics are EXCLUDED from body geez. Body `❈` tokens "
    "must be normalized to `✣`.",
    "NUMERAL-VS-LETTER: red Ethiopic numerals in lists (verse counts, "
    "thousand-suffix `ሺ`, regnal years) are NUMERALS not the fidel letter "
    "`ቯ` (qwā). If a red glyph follows another numeral or appears at a "
    "count position, it is `ሺ` (thousand) / `፬` (4) / `፰` (8), never `ቯ`.",
]

_REGNAL_FRAME_SCREENS = [
    "REGNAL YEAR NUMERALS: synchronistic frames stack multi-glyph Ethiopic "
    "numerals (`በ፫፻ወ፴ወ፱ዓመት` for 'in the 339th year of'). Each digit-glyph "
    "is a stand-alone token; do NOT join numerals to surrounding words or "
    "into compound forms — the validator's `_geez_to_tokens` splits them on "
    "input so the transcribed tokens MUST already be split.",
    "PATRONYMIC CHAINS: long `ወልደ X ወልደ Y` sequences carry the LIST name-"
    "fidel failure classes on every link. Apply the `ለ`/`ስ`, `ይ`/`ደ`, "
    "`ያ`/`ደ` screens to EACH name in the chain, not just the first.",
    "MOTHER + CITY FORMULA: '[king] reigned … and his mother's name was Y "
    "of [city Z]'. Both Y (mother) and Z (city) are proper nouns subject to "
    "the LIST name-fidel screens.",
]

_EXPECTED_ROUNDS = {
    "NARRATIVE": (2, 4),  # 1Ki1 was 3; 1Ki2 was 4; range stays honest
    "LIST": (4, 7),  # 1Ki4 was 7; future LIST chapters with these screens
    "REGNAL_FRAME": (4, 8),  # incl. patronymic + numeral overhead
}


def classify(book: str, chapter: int) -> str:
    """Return 'NARRATIVE' | 'LIST' | 'REGNAL_FRAME' for (book, chapter).

    Conservative default: anything not explicitly tagged is NARRATIVE.
    """
    if chapter in _LIST_CHAPTERS.get(book, set()):
        return "LIST"
    if chapter in _REGNAL_FRAME_CHAPTERS.get(book, set()):
        return "REGNAL_FRAME"
    return "NARRATIVE"


def chapter_profile(book: str, chapter: int) -> dict:
    """Return a structured profile for the transcriber's C-2/C-5 prompt.

    Shape: {book, chapter, class, screens, expected_rounds_min,
    expected_rounds_max}.
    `screens` is the ordered list of anti-failure screens — NARRATIVE first
    (always applicable), then LIST-additions, then REGNAL-additions.
    """
    cls = classify(book, chapter)
    screens: list[str] = list(_NARRATIVE_SCREENS)
    if cls in ("LIST", "REGNAL_FRAME"):
        screens.extend(_LIST_SCREENS)
    if cls == "REGNAL_FRAME":
        screens.extend(_REGNAL_FRAME_SCREENS)
    lo, hi = _EXPECTED_ROUNDS[cls]
    return {
        "book": book,
        "chapter": chapter,
        "class": cls,
        "screens": screens,
        "expected_rounds_min": lo,
        "expected_rounds_max": hi,
    }
