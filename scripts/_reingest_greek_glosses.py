#!/usr/bin/env python3
"""One-shot re-ingest of the two malformed ``lang-greek`` glosses — θεός (G2316)
and φῶς (G5457) — byte-minimal **lockstep** in the SOURCE store
(``content/notes/*.py``) and the baked BASE (``epub_working/index_split_*.html``).

Defects #2 + #4 of the auto-note re-ingest
(``docs/superpowers/notes/2026-06-06-auto-note-reingest-plan.md`` §2/§4). The
PERMANENT fix is the curated ``_GREEK_DEF_OVERRIDES`` map in
``scripts/core/sources_lexicon.py``; this script rewrites the already-baked note
bodies to match it.

Provably-correct pairing (no heuristic)
---------------------------------------
Every affected note shares ONE identical body per word (verified: θεός 1,196 /
φῶς 76 distinct-body occurrences in source). The OLD body is
``GreekWordDetector._format_body`` of the **raw** ``strongs_def`` (exactly what
built the store); the NEW body is the same formatter applied to the corrected
(override) definition (exactly what the fixed loader now produces). So old→new is
a single deterministic string replacement applied to every occurrence.

Edge case (handled, not guessed): 2 θεός notes were never baked into the base
(source 1,196 vs base 1,194), so a body absent from the base is source-only — the
source is still fixed; the base simply has no occurrence to replace.

Usage
-----
    python3 scripts/_reingest_greek_glosses.py            # dry-run (no writes)
    python3 scripts/_reingest_greek_glosses.py --write    # apply the lockstep
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.core.detectors import GreekWordDetector  # noqa: E402
from scripts.core.sources_lexicon import (  # noqa: E402
    _GREEK_DEF_OVERRIDES,
    StrongsGreekEntry,
)

NOTES_DIR = REPO / "content" / "notes"
BASE_DIR = REPO / "epub_working"
GREEK_JSON = REPO / "content" / "sources" / "strongs_greek.json"


def _entry(num: str, raw: dict, definition: str) -> StrongsGreekEntry:
    """A StrongsGreekEntry mirroring ``StrongsGreek.get`` but with an explicit
    ``definition`` (so we can render both the raw-store body and the fixed body)."""
    return StrongsGreekEntry(
        number=num,
        lemma=raw.get("lemma", ""),
        xlit=raw.get("xlit") or raw.get("translit") or "",
        pron=raw.get("pron", ""),
        derivation=raw.get("derivation", ""),
        definition=definition,
        kjv_def=raw.get("kjv_def", ""),
    )


def build_map() -> dict[str, tuple[str, str]]:
    """num -> (old_body, new_body) for each overridden Strong's number."""
    data = json.loads(GREEK_JSON.read_text(encoding="utf-8"))
    fmt = GreekWordDetector._format_body
    out: dict[str, tuple[str, str]] = {}
    for num, new_def in _GREEK_DEF_OVERRIDES.items():
        raw = data[num]
        old_body = fmt("", _entry(num, raw, raw.get("strongs_def", "")), "")
        new_body = fmt("", _entry(num, raw, new_def), "")
        out[num] = (old_body, new_body)
    return out


def _xhtml_bad(b: str) -> bool:
    """Keep the .py literal valid (no double-quote/backslash/newline) AND the baked
    XHTML well-formed (no raw </>/& in the visible prose outside the markup tags)."""
    inner = b.replace("<strong>", "").replace("</strong>", "").replace("<em>", "").replace("</em>", "")
    return (
        '"' in b
        or "\\" in b
        or "\n" in b
        or "<" in inner
        or ">" in inner
        or bool(re.search(r"&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)", inner))
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="apply the lockstep (default: dry-run)")
    args = ap.parse_args(argv)

    mapping = build_map()
    repls: dict[str, str] = {}
    for num, (ob, nb) in mapping.items():
        print(f"{num}: old={ob!r}")
        print(f"{num}: new={nb!r}")
        if ob == nb:
            print(f"⚠ {num} old == new (override is a no-op) — ABORT")
            return 2
        if _xhtml_bad(nb):
            print(f"⚠ {num} new body is XHTML-unsafe — ABORT")
            return 2
        repls[ob] = nb

    src_texts = {p: p.read_text(encoding="utf-8") for p in sorted(NOTES_DIR.glob("*.py")) if p.name != "__init__.py"}
    base_texts = {p: p.read_text(encoding="utf-8") for p in sorted(BASE_DIR.glob("index_split_*.html"))}

    src_count = {ob: sum(t.count(ob) for t in src_texts.values()) for ob in repls}
    base_count = {ob: sum(t.count(ob) for t in base_texts.values()) for ob in repls}
    for num, (ob, nb) in mapping.items():
        print(f"{num}: source occ={src_count[ob]}  base occ={base_count[ob]}")
        if src_count[ob] == 0:
            print(f"⚠ {num} old body NOT found in source (.py) — ABORT")
            return 2
        if base_count[ob] == 0:
            print(f"  note: {num} has no base occurrence (notes unbaked) — source-only fix")

    if not args.write:
        print("\nDRY-RUN — no files written. Re-run with --write to apply.")
        return 0

    src_written = base_written = base_repl = 0
    for p, text in src_texts.items():
        new_text = text
        for ob, nb in repls.items():
            if ob in new_text:
                new_text = new_text.replace(ob, nb)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            src_written += 1
    for p, text in base_texts.items():
        new_text = text
        for ob, nb in repls.items():
            cnt = new_text.count(ob)
            if cnt:
                new_text = new_text.replace(ob, nb)
                base_repl += cnt
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            base_written += 1
    print(f"\nWROTE: src={src_written} base={base_written} ({base_repl} occ).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
