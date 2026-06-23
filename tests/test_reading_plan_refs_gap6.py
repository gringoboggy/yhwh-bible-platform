"""round-11 gap-6 — reading-plan verse refs are normalized (alias→canonical),
validated (unknown book = error), and canon-filtered at render so out-of-canon /
unparseable refs never reach the shipped EPUB page.
"""

from __future__ import annotations

import re

from scripts import matter_pages
from scripts.core import reading_plans as rp
from scripts.core.reading_plans import ReadingPlan, ReadingPlanEntry


def _refs(html: str) -> str:
    return " ".join(re.findall(r'<span class="reading-plan-refs">(.*?)</span>', html))


def test_parse_verse_ref_normalizes_legacy_alias():
    assert rp.parse_verse_ref("ps 1")["book"] == "psa"
    assert rp.parse_verse_ref("joh 3:16")["book"] == "jhn"


def test_validate_plan_refs_flags_unknown_book_accepts_canonical():
    good = ReadingPlan("g", "G", "", (ReadingPlanEntry(1, ("gen 1", "ps 23")),))
    bad = ReadingPlan("b", "B", "", (ReadingPlanEntry(1, ("zzz 1", "gen 1")),))
    assert rp.validate_plan_refs(good)["errors"] == []
    assert rp.validate_plan_refs(bad)["errors"] == ["zzz 1"]


def test_validate_plan_refs_canon_drops_out_of_canon_not_error():
    plan = ReadingPlan("p", "P", "", (ReadingPlanEntry(1, ("gen 1", "psa 1")),))
    res = rp.validate_plan_refs(plan, canon_books={"psa"})
    assert res["errors"] == []  # gen is a real book → not an error
    assert "gen 1" in res["dropped"]  # but out of this edition's canon → dropped
    assert res["kept"] == 1  # psa 1 ships


def test_render_filters_out_of_canon_verse_refs():
    plan = ReadingPlan("p", "Plan", "", (ReadingPlanEntry(1, ("gen 1", "psa 23")),))
    refs = _refs(matter_pages.render_reading_plans_page({"title": "T"}, [plan], canon_books={"psa"}))
    assert "psa 23" in refs and "gen 1" not in refs


def test_render_keeps_all_refs_when_in_canon():
    # canon_books=None or a superset keeps every ref — the current-data path is
    # byte-identical to the pre-gap-6 render (no edition emits this page today).
    plan = ReadingPlan("p", "Plan", "", (ReadingPlanEntry(1, ("gen 1", "psa 23")),))
    refs = _refs(matter_pages.render_reading_plans_page({"title": "T"}, [plan]))
    assert "gen 1" in refs and "psa 23" in refs
