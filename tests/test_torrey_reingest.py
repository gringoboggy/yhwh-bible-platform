"""Defects #3 + #5 of the auto-note re-ingest: topic-torrey ref-dump leak + the
mis-parsed sub-entry description (audit filed #5 under topic-nave, but it is entirely
topic-TORREY — see docs/superpowers/notes/2026-06-06-auto-note-reingest-plan.md §3/§5).

The extractor tests pin the discriminator fix; the store/index tests are
full-population invariants (pass after scripts/_reingest_torrey_topics.py --write)."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from scripts.extract_torrey_ccel import parse_text
from scripts.lint_rules import check_no_torrey_topic_leak

REPO = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO / "content" / "notes"
TORREY_JSON = REPO / "content" / "sources" / "torrey_topical.json"
_NN = re.compile(r"\d+:\d+")


def _store_topic_torrey() -> list[tuple[str, int, int, str, str]]:
    out: list[tuple[str, int, int, str, str]] = []
    for p in sorted(NOTES_DIR.glob("*.py")):
        if p.name == "__init__.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "NOTES" for t in node.targets):
                for t in ast.literal_eval(node.value):
                    if len(t) >= 8 and t[4] == "topic-torrey":
                        out.append((p.stem, t[0], t[1], t[2], t[7]))
    return out


def _topic_region(body: str) -> str:
    m = re.search(r"appears under: (.*)\.\s*$", body)
    return m.group(1) if m else ""


# --- extractor-level (the discriminator) -----------------------------------------


def test_parse_text_rejects_description_and_refdump_headings():
    # A sentence-case description ('… against.') and a wrapped citation dump
    # ('Zechariah 1:1  1:7 …') must NOT become topics; the refs that follow flow back
    # to the real topic (Tyre), so nothing is lost.
    txt = (
        "Tyre\n"
        "To be destroyed by the king of Babylon. — Isa 23:13.\n"
        "The king of Babylon to be rewarded with the spoil of Egypt for his service against.\n"
        "— Eze 29:18-20.\n"
        "Zechariah 1:1  1:7  1:8\n"
        "— Mr 10:23.\n"
    )
    fwd = parse_text(txt)
    assert "Tyre" in fwd
    assert not [k for k in fwd if k.rstrip().endswith(".")], "a period-ending description became a topic"
    assert not [k for k in fwd if _NN.search(k)], "a chapter:verse run became a topic"
    # Isa 23:13 + Eze 29:18,19,20 + Mr 10:23 all attributed to Tyre
    assert ["mrk", 10, 23] in fwd["Tyre"]
    assert ["eze", 29, 18] in fwd["Tyre"]


def test_parse_text_keeps_real_titlecase_topic():
    fwd = parse_text("Works, Good\nDo good to all. — Ga 6:10.\n")
    assert "Works, Good" in fwd
    assert ["gal", 6, 10] in fwd["Works, Good"]


# --- regenerated index invariants ------------------------------------------------


def test_index_has_no_junk_topics():
    topics = list(json.loads(TORREY_JSON.read_text(encoding="utf-8"))["topics"])
    assert not [t for t in topics if t.rstrip().endswith(".")]
    assert not [t for t in topics if _NN.search(t)]


def test_index_refs_preserved():
    meta = json.loads(TORREY_JSON.read_text(encoding="utf-8"))["_meta"]
    # the two junk keys were dropped (630 -> 628) but every ref was kept (reassigned).
    assert meta["n_topics"] == 628
    assert meta["n_refs"] == 55566


# --- full-population store invariants (pass after _reingest_torrey_topics.py --write) ---


def test_no_topic_torrey_refdump_or_description():
    offenders = []
    for c, ch, v, s, body in _store_topic_torrey():
        region = _topic_region(body)
        if "." in region or _NN.search(region):
            offenders.append(f"{c} {ch}:{v}{s}")
    assert not offenders, f"{len(offenders)} topic-torrey bodies still leak, e.g. {offenders[:5]}"


def test_known_corrupted_tyre_verse_is_clean():
    # zec 9:2 is a Tyre prophecy; it previously listed the junk description/dump and
    # now reads the real 'Tyre' topic with no leaked refs.
    hits = [b for c, ch, v, s, b in _store_topic_torrey() if c == "zec" and ch == 9 and v == 2]
    assert hits, "zec 9:2 topic-torrey note not found"
    for b in hits:
        assert "service against" not in b
        assert not _NN.search(_topic_region(b))
        assert "Tyre" in b


def test_lint_guard_passes():
    result = check_no_torrey_topic_leak()
    assert result["status"] == "pass", result["message"]
