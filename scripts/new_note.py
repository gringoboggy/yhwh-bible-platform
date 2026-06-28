#!/usr/bin/env python3
"""
new_note.py — Scaffold generator for new editorial notes.

Generates a draft NOTES tuple ready to paste into ``content/notes/<book>.py``.
Pre-fills the boring scaffolding (verse coords, kind, attribution shape,
HTML opener pattern) with kind-appropriate templates so the author only
has to fill in actual content.

Usage:
    python3 scripts/new_note.py gen 3 15 --kind lang-hebrew --anchor "bruise"
    python3 scripts/new_note.py rev 12 9 --kind parallel --anchor "dragon"
    python3 scripts/new_note.py 1en 1 1 --kind comm-ethiopian --suffix a

Pipe to clipboard / append to file:
    python3 scripts/new_note.py gen 3 15 --kind comm-patristic | pbcopy   (macOS)
    python3 scripts/new_note.py gen 3 15 --kind comm-patristic >> content/notes/gen.py

Per Rule P6 — this script complements rather than duplicates `add_note.py`
(which performs an interactive append). new_note.py is non-interactive,
copy-paste-friendly, and template-driven.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.ui import RED, DIM, RESET  # noqa: E402

# ----------------------------------------------------------------------
# Per-kind scaffold templates
# ----------------------------------------------------------------------
# Each template returns (label, body, attribution_dict_template).
# Author fills in the TODO_ placeholders.

LANG_TEMPLATE = (
    "Hebrew.",  # label (or Greek / Aramaic / Ge'ez per kind)
    "<strong>TODO_TRANSLITERATION (TODO_NATIVE_SCRIPT).</strong> "
    "TODO_GLOSS_DEFINITION. <em>[Reviewer: extend with morphology, root, "
    "and any cross-canon resonance before promoting.]</em>",
    {
        "sources": [
            {
                "author": "Strong, James",
                "title": "Strong's Exhaustive Concordance — Hebrew",
                "year": 1890,
                "section": "TODO_STRONGS_NUMBER",
            }
        ],
        "license": "PD",
        "voice": "lexical",
    },
)

PARALLEL_TEMPLATE = (
    "Parallel: TODO_REF.",
    '<strong>TODO_TOPIC.</strong> TODO_BRIEF_FRAMING. <a href="#vnote-TODO">'
    "TODO_REF</a> picks up TODO_THEMATIC_LINK. The connection illuminates "
    "TODO_INSIGHT.",
    {
        "sources": [
            {"editor": "TODO_COMPILER", "title": "Treasury of Scripture Knowledge", "year": 1834, "license": "PD"}
        ],
        "license": "PD",
        "voice": "cross-canon",
    },
)

SOURCE_TEMPLATE = (
    "Textual variant.",
    "<strong>TODO_VARIANT_NAME.</strong> The MT reads TODO_MT; the LXX "
    "(TODO_GREEK) and TODO_OTHER_WITNESS read TODO_VARIANT. "
    "TODO_INTERPRETIVE_WEIGHT.",
    {
        "sources": [
            {"author": "TODO_EDITOR", "title": "TODO_CRITICAL_EDITION", "year": 0, "license": "TODO_PD_OR_LICENSED"}
        ],
        "voice": "text-critical",
    },
)

COMM_TEMPLATES: dict[str, tuple[str, str, dict]] = {
    "comm-patristic": (
        "Patristic reading.",
        "<strong>TODO_TOPIC.</strong> TODO_FATHER (TODO_WORK, TODO_BOOK_CH) "
        "reads this passage TODO_HOW. TODO_THEOLOGICAL_MOVE. The pattern "
        "anticipates the later TODO_LATER_DEVELOPMENT.",
        {
            "sources": [
                {"author": "TODO_FATHER (e.g. Augustine of Hippo)", "title": "TODO_WORK", "year": 0, "license": "PD"},
            ],
            "voice": "patristic",
        },
    ),
    "comm-ethiopian": (
        "Andemta tradition.",
        "<strong>TODO_TOPIC.</strong> The Andemta commentary on this passage "
        "preserves TODO_ETHIOPIAN_READING. The Synaxarium (TODO_DATE) "
        "associates TODO_FIGURE_OR_THEME. TODO_GE'EZ_LINGUISTIC_NOTE.",
        {
            "sources": [
                {
                    "editor": "Andemta tradition",
                    "title": "Andemta — traditional commentary",
                    "year": 0,
                    "license": "PD-tradition",
                },
            ],
            "voice": "ethiopian",
        },
    ),
    "comm-reformation": (
        "Reformation reading.",
        "<strong>TODO_TOPIC.</strong> Calvin (Institutes TODO_BK.TODO_CH or "
        "Commentaries) reads TODO. Luther (TODO_WORK) emphasises TODO. "
        "The Westminster divines (Confession TODO_CH) systematise TODO.",
        {
            "sources": [
                {
                    "author": "Calvin, John",
                    "title": "Institutes of the Christian Religion",
                    "year": 1559,
                    "license": "PD",
                },
            ],
            "voice": "reformation",
        },
    ),
    "comm-modern-critical": (
        "Modern critical synthesis.",
        "<strong>TODO_TOPIC.</strong> The redactional layer here (J / E / P / D — "
        "TODO_SOURCE) suggests TODO. The form-critical reading (Gunkel, Mowinckel) "
        "identifies TODO_GENRE. Recent scholarship (TODO_SCHOLAR, TODO_YEAR) "
        "argues TODO.",
        {
            "sources": [
                {"author": "TODO_SCHOLAR", "title": "TODO_WORK", "year": 0, "license": "TODO_QUOTED_OR_PARAPHRASED"},
            ],
            "voice": "modern-critical",
        },
    ),
    "comm-contextual": (
        "Ancient Near Eastern context.",
        "<strong>TODO_TOPIC.</strong> The TODO_PARALLEL_TEXT (Enuma Elish / "
        "Atrahasis / Gilgamesh / Ugaritic / Hammurabi — TODO_REF) preserves "
        "TODO_PARALLEL_MOTIF. Where the surrounding cosmogony assumes TODO, "
        "Genesis reframes TODO_THEOLOGICAL_DELTA.",
        {
            "sources": [
                {"editor": "TODO_TRANSLATOR", "title": "TODO_ANE_TEXT", "year": 0, "license": "TODO"},
            ],
            "voice": "contextual",
        },
    ),
    "comm-catholic": (
        "Catholic teaching.",
        "<strong>TODO_TOPIC.</strong> The Catechism (CCC TODO) frames this "
        "passage as TODO. Aquinas (Summa TODO_PART.TODO_Q.TODO_A) reasons TODO. "
        "Magisterial documents (TODO_ENCYCLICAL) develop TODO.",
        {
            "sources": [
                {
                    "editor": "Catholic Church",
                    "title": "Catechism of the Catholic Church",
                    "year": 1992,
                    "license": "TODO_QUOTED_FAIR_USE",
                },
            ],
            "voice": "catholic",
        },
    ),
    "comm-orthodox": (
        "Orthodox reading.",
        "<strong>TODO_TOPIC.</strong> The Eastern fathers (TODO_FATHER) read "
        "this through the lens of TODO. Liturgical use (TODO_LITURGY) places "
        "it in TODO. The Philokalia tradition (TODO_VOLUME) develops TODO.",
        {
            "sources": [
                {"author": "TODO_FATHER (e.g. Gregory Palamas)", "title": "TODO_WORK", "year": 0, "license": "PD"},
            ],
            "voice": "orthodox",
        },
    ),
}

DEFAULT_COMM_TEMPLATE = (
    "Note.",
    "<strong>TODO_TOPIC.</strong> TODO_OPENING_FRAME. TODO_DEVELOPMENT. TODO_THEOLOGICAL_OR_CONTEXTUAL_PAYOFF.",
    {
        "sources": [
            {"author": "TODO_AUTHOR", "title": "TODO_WORK", "year": 0, "license": "PD"},
        ],
        "voice": "editorial",
    },
)


def template_for(kind: str) -> tuple[str, str, dict]:
    """Look up the per-kind template."""
    if kind == "word":
        return ("Word.", LANG_TEMPLATE[1], LANG_TEMPLATE[2])
    if kind.startswith("lang-"):
        # Customise label per language family
        lang_label = {
            "lang-hebrew": "Hebrew.",
            "lang-aramaic": "Aramaic.",
            "lang-greek": "Greek.",
            "lang-amharic": "Amharic.",
            "lang-geez": "Ge'ez.",
            "lang-latin": "Latin.",
            "lang-syriac": "Syriac.",
            "lang-arabic": "Arabic.",
        }.get(kind, "Word.")
        return (lang_label, LANG_TEMPLATE[1], LANG_TEMPLATE[2])
    if kind == "parallel" or kind.startswith("xref-") or kind.startswith("parallel-"):
        return PARALLEL_TEMPLATE
    if kind == "source" or kind.startswith("source-") or kind.startswith("text-"):
        return SOURCE_TEMPLATE
    if kind in COMM_TEMPLATES:
        return COMM_TEMPLATES[kind]
    if kind.startswith("comm"):
        return DEFAULT_COMM_TEMPLATE
    return DEFAULT_COMM_TEMPLATE


# ----------------------------------------------------------------------
# Tuple rendering
# ----------------------------------------------------------------------


def render_tuple(
    _book_code: str,
    ch: int,
    v: int,
    suffix: str,
    anchor: str,
    kind: str,
    label: str,
    title: str,
    body: str,
    attribution: dict,
) -> str:
    """Format a NOTES tuple as Python source ready to paste into the
    book's content/notes/<code>.py."""

    def py_repr(obj, indent: int = 0) -> str:
        """Format dicts/lists with stable ordering and 4-space indentation."""
        pad = " " * indent
        if isinstance(obj, dict):
            inner = []
            for k, val in obj.items():
                inner.append(f"{pad}    {k!r}: {py_repr(val, indent + 4)}")
            return "{\n" + ",\n".join(inner) + f"\n{pad}}}"
        if isinstance(obj, list):
            inner = []
            for item in obj:
                inner.append(f"{pad}    {py_repr(item, indent + 4)}")
            return "[\n" + ",\n".join(inner) + f"\n{pad}]"
        return repr(obj)

    # Wrap body to ~100 cols for readability
    body_quoted = repr(body)

    return f"""    (
        {ch}, {v}, {suffix!r},                  # ch, v, suffix
        {anchor!r},
        {kind!r},
        {title!r},
        {label!r},
        {body_quoted},
        {py_repr(attribution, 8)},
    ),"""


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Scaffold a new editorial note tuple, with per-kind template.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("book", help="book code (e.g. 'gen', 'rev', '1en')")
    p.add_argument("chapter", type=int)
    p.add_argument("verse", type=int)
    p.add_argument("--suffix", default="", help="single lowercase letter for multiple notes on same verse")
    p.add_argument("--kind", required=True, help="note kind (e.g. lang-hebrew, comm-patristic, parallel)")
    p.add_argument("--anchor", default="", help="anchor text within verse (where marker attaches)")
    p.add_argument("--title", default="", help="popover title (often the same as label or empty)")
    args = p.parse_args()

    # Validate book
    try:
        book = config.get_book(args.book)
    except KeyError as e:
        print(f"{RED}✗ {e}{RESET}", file=sys.stderr)
        sys.exit(2)
    # R16 Phase D (★BUGCLUSTER) — normalize a legacy alias to the canonical stem
    # so the rendered tuple + the "paste into content/notes/<code>.py" hint point
    # at the real file (e.g. `--book joh` → jhn), mirroring add_note.
    args.book = book["code"]

    # Look up template
    label, body, attribution = template_for(args.kind)
    title = args.title or label.rstrip(".")

    rendered = render_tuple(
        args.book,
        args.chapter,
        args.verse,
        args.suffix,
        args.anchor,
        args.kind,
        label,
        title,
        body,
        attribution,
    )

    print()
    print(f"{DIM}# Paste into content/notes/{args.book}.py inside the NOTES list.{RESET}")
    print(f"{DIM}# Replace TODO_ placeholders with actual content. Run note_quality.py to validate.{RESET}")
    print()
    print(rendered)
    print()
    print(f"{DIM}# Then: python3 scripts/inject.py --book {args.book}{RESET}")
    print(f"{DIM}# Then: python3 scripts/manifest.py --build{RESET}")


if __name__ == "__main__":
    main()
