"""Per-push gate for the translation/notes store structural integrity invariant.

Round-13 closed the data-validity completeness gap (the deep-audit dimension that
returned 0/0) with the on-demand auditor ``dev/audit_translation_integrity.py``.
A gap is not truly closed until it is *gated*: this runs the auditor over the live
corpus and fails on any FAIL-level finding (a duplicate coordinate in a canonical
store → silent text loss, a non-int chapter key, an impossible coordinate, a
malformed tuple). It also pins the known-legitimate Geʽez-Psalter occurrence-multi
WARNs so a wrong "de-dup" of that scripture data, or a broken auditor, is caught —
and proves the gate itself can fail.

The critical checks (dup-coord / non-int / arity — the silent-text-loss class) run
per-push via the fast ``check_extent=False`` path (~9 s). The full scan, which also
builds the KJV skeleton for the canonical-extent pass (~90 s), is slow-tagged and
runs on the schedule / on demand — matching the project's existing real-data-gate
discipline (cf. the byte-stability gate).
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "audit_translation_integrity", REPO / "dev" / "audit_translation_integrity.py"
)
ati = importlib.util.module_from_spec(_spec)
# Register before exec so the module's @dataclass can resolve cls.__module__ via
# sys.modules (Python 3.14's dataclasses machinery requires it for spec-loaded modules).
sys.modules[_spec.name] = ati
_spec.loader.exec_module(ati)

# The 9 source-authoritative LXX/Geʽez-Psalter coordinates that legitimately carry
# two distinct verse-lines under one number (verified round-13: real LXX numbering,
# NOT typos — e.g. 71:19 is the LXX Ps 71 colophon "Ended are the songs of David").
_GEEZ_PSALTER_DUP_COORDS = {
    (21, 14),
    (36, 24),
    (36, 25),
    (46, 9),
    (68, 2),
    (71, 19),
    (101, 3),
    (115, 9),
    (144, 18),
}


@pytest.fixture(scope="module")
def fast_findings():
    # check_extent=False → skip the slow KJV-skeleton build; keep the dup-coord /
    # non-int / arity checks (the silent-text-loss class) that gate every push.
    return ati.audit_repo(REPO, check_extent=False)


class TestCriticalGate:
    """The silent-text-loss class — runs per-push (~9 s)."""

    def test_no_fail_level_findings(self, fast_findings):
        fails = [f for f in fast_findings if f.level == ati.FAIL]
        assert fails == [], [f"{f.store} {f.coord} {f.code}: {f.detail}" for f in fails]

    def test_geez_psalter_occurrence_multi_warns_persist(self, fast_findings):
        for store in ("geez-tewahedo/psa.py", "geez-tewahedo-en/psa.py"):
            got = {ast.literal_eval(f.coord) for f in fast_findings if f.code == "dup-coord" and f.store == store}
            assert got == _GEEZ_PSALTER_DUP_COORDS, (store, got)

    def test_dup_coords_exist_only_in_the_two_geez_psalters(self, fast_findings):
        stores = {f.store for f in fast_findings if f.code == "dup-coord"}
        assert stores == {"geez-tewahedo/psa.py", "geez-tewahedo-en/psa.py"}, stores


class TestGateCanFail:
    """A gate that cannot fail in a test is not a gate (round-13 completeness gap 3)."""

    def test_canonical_store_duplicate_is_a_fail(self):
        f = ati.check_translation_store("t/x.py", "psa", "canonical", [(1, 1, "a"), (1, 1, "b")])
        assert any(x.level == ati.FAIL and x.code == "dup-coord" for x in f)

    def test_impossible_chapter_in_kjv_is_a_fail(self):
        f = ati.check_translation_store("kjv/gen.py", "gen", "canonical", [(87, 1, "x")], translation="kjv")
        assert any(x.level == ati.FAIL and x.code == "chapter-missing" for x in f)

    def test_notes_non_int_coord_is_a_fail(self):
        f = ati.check_notes_store("notes/x.py", [("1", 1, "", "", "k", "", "", "", "")])
        assert any(x.level == ati.FAIL and x.code == "notes-coord" for x in f)


class TestFullCorpusGate:
    @pytest.mark.slow
    def test_full_audit_including_extent_has_no_fail(self):
        # The complete scan: also builds the KJV skeleton for the canonical-extent
        # pass (chapter-missing / canonical-table-gap). Slow → scheduled / on demand.
        findings = ati.audit_repo(REPO)
        fails = [f for f in findings if f.level == ati.FAIL]
        assert fails == [], [f"{f.store} {f.coord} {f.code}: {f.detail}" for f in fails]
