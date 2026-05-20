"""Pre-screened C-2/C-5 self-check (audit U-belt 2026-05-20).

The transcriber subagent calls ``screen_witness_for_class_failures(witness,
chapter_class)`` on its own JSON output BEFORE returning to the controller.
The helper flags tokens that pattern-match the documented systematic-
failure classes (per ``content/manuscript/_reviewer_context/GG_topology.md``
§2). The transcriber does ONE self-fix pass against the flags before C-3/
C-6 review dispatch — catching the obvious patterns without burning an
adversarial reviewer round.

The screens are PATTERN-based, not parchment-based. They cannot replace
C-3/C-6 vision review; they only catch patterns that are obvious from the
JSON alone. Recall > precision: flag borderline cases (~30 sec self-check
each) rather than miss a real defect (~30 min C-3 round).

Class hierarchy mirrors ``manuscript_chapter_class.chapter_profile``:
- NARRATIVE: non-Ethiopic screen + body `❈` (rubric-cross used in body)
- LIST: NARRATIVE + `ይ`/`ደ` family (standard `ይ`-verbs written `ደ`,
  including `ይሁዳ`/`ደሁዳ`) + `እስ` where `እለ` (relative pronoun) is the
  standard form
- REGNAL_FRAME: inherits all LIST patterns

When a new failure class is added to ``GG_topology.md`` or
``CAM_topology.md``, the pattern (if pattern-detectable) is added here.
"""

from __future__ import annotations

from .manuscript_records import _screen_non_ethiopic


# Known standard Ge'ez verb stems that legitimately start with `ይ-`
# (yə-prefix) — when the JSON shows the `ደ-` form of one of these,
# flag for re-verification. Conservative: small curated list of
# unambiguous standard forms documented in the 1Ki4 retrospective.
_DE_PREFIX_KNOWN_DE_FOR_YE: dict[str, str] = {
    "ደሁዳ": "ይሁዳ",  # Judah — the proper noun, repeatedly mis-written
    "ደበልዑ": "ይበልዑ",  # they-eat
    "ደትገበር": "ይትገበር",  # it-is-made
    "ደሰርዑ": "ይሰርዑ",  # they-arrange
    "ደትቀንዩ": "ይትቀንዩ",  # they-serve
    "ደከውን": "ይከውን",  # he-becomes
    "ደስምዑ": "ይስምዑ",  # they-hear
    "ደነግሥ": "ይነግሥ",  # he-reigns
    "ደመጽእ": "ይመጽእ",  # he-comes
}


def _flag_non_ethiopic(witness: dict) -> list[str]:
    """Compose the existing validator screen (single source of truth)."""
    out: list[str] = []
    for v in witness.get("verses", []):
        if {"v", "geez", "tokens"} <= set(v):
            verse_view = {
                "v": v["v"],
                "geez": v["geez"],
                "tokens": v["tokens"],
            }
            out.extend(_screen_non_ethiopic(verse_view))
    return out


def _flag_body_knot_cross(witness: dict) -> list[str]:
    """`❈` U+2748 in body geez — should be `✣` U+2723. Body geez NEVER
    legitimately carries the large knot-cross (per GG_topology.md §1)."""
    out: list[str] = []
    for v in witness.get("verses", []):
        vid = v.get("v", "?")
        if "❈" in v.get("geez", ""):
            out.append(f"v{vid}: body knot-cross ❈ in geez — should be ✣ (✣ is body register; ❈ is rubric-only)")
        for t in v.get("tokens", []):
            if "❈" in t:
                out.append(f"v{vid}: body knot-cross ❈ in token {t!r} — should be ✣")
    return out


def _flag_ye_de_family(witness: dict) -> list[str]:
    """Tokens matching known `ይ`-prefix standard forms written with `ደ`.
    Conservative — only flags exact matches in the curated list."""
    out: list[str] = []
    for v in witness.get("verses", []):
        vid = v.get("v", "?")
        for t in v.get("tokens", []):
            if t in _DE_PREFIX_KNOWN_DE_FOR_YE:
                standard = _DE_PREFIX_KNOWN_DE_FOR_YE[t]
                out.append(
                    f"v{vid}: ይ/ደ family — token {t!r} matches the known "
                    f"`ደ`-written form of standard `{standard}`; re-verify "
                    f"the prefix at 20x+ (per GG_topology.md §2)"
                )
    return out


def _flag_es_relative(witness: dict) -> list[str]:
    """Stand-alone `እስ` token — likely should be `እለ` (relative pronoun
    "those who"). Flags every occurrence on LIST/REGNAL chapters; the
    transcriber re-verifies against parchment."""
    out: list[str] = []
    for v in witness.get("verses", []):
        vid = v.get("v", "?")
        for t in v.get("tokens", []):
            if t == "እስ":
                out.append(
                    f"v{vid}: token `እስ` — likely should be `እለ` (relative pronoun); re-verify (per GG_topology.md §2)"
                )
    return out


# Class → list of screen functions to apply. Each function takes the
# witness dict and returns a list of flag strings.
_NARRATIVE_SCREENS = [
    _flag_non_ethiopic,
    _flag_body_knot_cross,
]

_LIST_ADDITIONS = [
    _flag_ye_de_family,
    _flag_es_relative,
]

_REGNAL_ADDITIONS: list = []  # inherits all LIST; no extras YET


def screen_witness_for_class_failures(witness: dict, chapter_class: str) -> list[str]:
    """Return a list of likely-defect flags for the witness.

    Empty list = no class-detectable pattern found (does NOT mean the
    witness is clean — parchment-only defects still require C-3/C-6
    review). Each flag string is human-readable and includes the verse
    + token + the rule citing the GG/CAM topology reference.
    """
    screens = list(_NARRATIVE_SCREENS)
    if chapter_class in ("LIST", "REGNAL_FRAME"):
        screens.extend(_LIST_ADDITIONS)
    if chapter_class == "REGNAL_FRAME":
        screens.extend(_REGNAL_ADDITIONS)

    flags: list[str] = []
    for screen in screens:
        flags.extend(screen(witness))
    return flags
