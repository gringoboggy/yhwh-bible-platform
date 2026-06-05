"""Defect #1 of the auto-note re-ingest: dict-easton un-cap (FULL articles) + the
``_HEAD`` headword-glue fix. See ``docs/superpowers/notes/2026-06-06-auto-note-reingest-plan.md`` §1.

The first two tests pin the extractor fix (pass as soon as the extractor is fixed).
The last two are full-population store invariants (pass after ``_reingest_eastons.py
--write`` has rewritten the existing notes)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from scripts.extract_eastons_ccel import _HEAD, build_notes, parse_entries

REPO = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO / "content" / "notes"


def _strip(html: str) -> str:
    return re.sub("<[^>]+>", "", html)


def _store_dict_easton() -> list[tuple[str, int, int, str, str]]:
    out: list[tuple[str, int, int, str, str]] = []
    for p in sorted(NOTES_DIR.glob("*.py")):
        if p.name == "__init__.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "NOTES" for t in node.targets):
                for t in ast.literal_eval(node.value):
                    if len(t) >= 8 and t[4] == "dict-easton":
                        out.append((p.stem, t[0], t[1], t[2], t[7]))
    return out


# --- extractor-level (the fix) ---------------------------------------------------


def test_head_regex_does_not_grab_sentence_case_lead_capital():
    # the glue bug: a sentence-case word's lead capital must NOT join the headword
    assert _HEAD.match("FOREST Hebrews dwelt").group(1) == "FOREST"
    assert _HEAD.match("DANIEL God is my judge").group(1) == "DANIEL"


def test_head_regex_keeps_genuine_allcaps_multiword_heads():
    assert _HEAD.match("BURNT OFFERING the").group(1) == "BURNT OFFERING"
    assert _HEAD.match("SONG OF SOLOMON is").group(1) == "SONG OF SOLOMON"
    assert _HEAD.match("BAAL-ZEBUB the").group(1) == "BAAL-ZEBUB"  # hyphenated head intact


def test_build_notes_is_uncapped_no_ellipsis():
    # a long synthetic entry must come through complete — no 480-char truncation, no "…"
    long_tail = "word " * 400  # ~2000 chars, well over the old MAX_BODY=480
    entries = parse_entries(f"•LAMECH a descendant of Cain (Genesis 4:18). {long_tail}")
    notes = build_notes(entries)
    assert len(notes) == 1
    body = notes[0]["body"]
    assert "…" not in body
    assert len(_strip(body)) > 1500  # the full tail survived


def test_build_notes_escapes_xhtml_metacharacters():
    # a literal &/</> in an entry must be XHTML-escaped so the body stays well-formed
    # when baked verbatim into the EPUB (the cause of the RSC-016 epubcheck failure
    # before escaping). The two <strong> tags are added after escaping, so they survive.
    entries = parse_entries("•GODLINESS the mystery (1 Timothy 3:16): a < b & c > d.")
    notes = build_notes(entries)
    assert len(notes) == 1
    body = notes[0]["body"]
    assert "&lt;" in body and "&gt;" in body and "&amp;" in body
    assert "< b" not in body and "c >" not in body  # no raw angle brackets in the prose
    assert body.count("<strong>") == 2 and body.count("</strong>") == 2  # tags intact


def test_no_raw_xhtml_metacharacters_in_dict_easton_bodies():
    # full-population: no shipping dict-easton body carries a raw </> or bare & in its
    # prose (would break XHTML well-formedness when baked). Passes after --write.
    offenders = []
    for c, ch, v, s, body in _store_dict_easton():
        inner = body.replace("<strong>", "").replace("</strong>", "")
        if "<" in inner or ">" in inner or re.search(r"&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)", inner):
            offenders.append(f"{c} {ch}:{v}{s}")
    assert not offenders, f"{len(offenders)} dict-easton bodies have raw XHTML metachars, e.g. {offenders[:5]}"


# --- full-population store invariants (pass after _reingest_eastons.py --write) ---


def test_no_dict_easton_body_ends_with_ellipsis():
    offenders = [
        f"{c} {ch}:{v}{s}" for c, ch, v, s, body in _store_dict_easton() if _strip(body).rstrip().endswith("…")
    ]
    assert not offenders, f"{len(offenders)} dict-easton notes still truncated, e.g. {offenders[:5]}"


def test_known_formerly_truncated_entry_is_complete():
    # ACHAN (1 Chronicles 2:7) was a capped entry in the audit; after re-ingest its
    # full article is present and ends on terminal punctuation, not a "…".
    achan = [
        body for c, ch, v, s, body in _store_dict_easton() if c == "1ch" and ch == 2 and v == 7 and "ACHAN" in body
    ]
    assert achan, "ACHAN dict-easton note at 1ch 2:7 not found"
    text = _strip(achan[0]).rstrip()
    assert not text.endswith("…")
    assert text[-1] in ".!?\"'”)", f"unexpected final char: {text[-30:]!r}"
