"""mint-9 (deep-audit round 2) Phase-5 guards — at-scale driver dedup (#9).

The naves / torrey / xref / ethiopian at-scale drivers appended candidates to a
chapter file without same-run dedup, so re-running a driver before promote
appended byte-identical candidates that promote then materialised as distinct
notes. They now mirror run_kenyon_at_scale: dedup against existing + within-run
on (verse, kind, draft_body), returning None when nothing new.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class _FakeCand:
    """Minimal stand-in matching the attrs candidate_to_dict reads."""

    verse: int
    kind: str
    draft_body: str
    chapter: int = 1
    draft_title: str = "T"
    draft_label: str = "L"
    anchor: str = ""
    confidence: float = 0.9
    source: str = "test"
    rationale: str = ""

    # candidate_to_dict may read extra attrs across drivers; provide safe defaults.
    def __getattr__(self, _name):  # pragma: no cover - defensive
        return ""


DRIVERS = [
    "run_naves_at_scale",
    "run_torrey_at_scale",
    "run_xref_at_scale",
    "run_ethiopian_at_scale",
]


@pytest.mark.parametrize("driver_mod", DRIVERS)
def test_rerun_does_not_duplicate_candidates(driver_mod, tmp_path, monkeypatch):
    import importlib

    drv = importlib.import_module(f"scripts.{driver_mod}")
    monkeypatch.setattr(drv, "CANDIDATES_DIR", tmp_path)

    cands = [
        _FakeCand(verse=1, kind="topic-nave", draft_body="body one"),
        _FakeCand(verse=2, kind="topic-nave", draft_body="body two"),
    ]
    # First write — both land.
    p1 = drv.write_queue("gen", 1, cands)
    assert p1 is not None
    import json

    n_after_first = json.loads(Path(p1).read_text(encoding="utf-8"))["n_candidates"]
    assert n_after_first == 2, f"{driver_mod}: first write should land 2 candidates"

    # Re-run with the SAME candidates — dedup must add nothing.
    p2 = drv.write_queue("gen", 1, cands)
    assert p2 is None, f"{driver_mod}: re-run with identical candidates must return None (no growth)"
    n_after_rerun = json.loads(Path(p1).read_text(encoding="utf-8"))["n_candidates"]
    assert n_after_rerun == 2, f"{driver_mod}: re-run duplicated candidates ({n_after_rerun} != 2)"


@pytest.mark.parametrize("driver_mod", DRIVERS)
def test_new_candidate_still_appends(driver_mod, tmp_path, monkeypatch):
    import importlib
    import json

    drv = importlib.import_module(f"scripts.{driver_mod}")
    monkeypatch.setattr(drv, "CANDIDATES_DIR", tmp_path)

    drv.write_queue("gen", 1, [_FakeCand(verse=1, kind="topic-nave", draft_body="first")])
    # A genuinely new candidate (different body) must append.
    p = drv.write_queue("gen", 1, [_FakeCand(verse=1, kind="topic-nave", draft_body="second")])
    assert p is not None, f"{driver_mod}: a new candidate must append"
    n = json.loads(Path(p).read_text(encoding="utf-8"))["n_candidates"]
    assert n == 2, f"{driver_mod}: expected 2 distinct candidates, got {n}"


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-q"]))
