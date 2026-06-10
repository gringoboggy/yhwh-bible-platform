"""P0 done-gate: the Samuel + Kings folio manifests must be COMPLETE — every
canonical chapter carries non-empty CAM + GG folios and every referenced image
resolves on disk. Fast structural check (no vision). Drives the P0 folio-index
task (plans/2026-06-02-samkings-folio-index-p0-plan.md) to green.

RED until P0 fills the ~93 pending chapters' folios; GREEN is P0's done-criterion.
"""

from pathlib import Path

import pytest

from scripts.core import manuscript_manifest as mm

REPO = Path(__file__).resolve().parent.parent
CANON = {"samuel": {"1sa": 31, "2sa": 24}, "kings": {"1ki": 22, "2ki": 25}}


def _chapters(track):
    man = mm.load_manifest(track=track)
    for book, nch in CANON[track].items():
        for ch in range(1, nch + 1):
            yield book, ch, mm.chapter_entry(man, book, ch)


@pytest.mark.parametrize("track", ["samuel", "kings"])
def test_every_chapter_present(track):
    missing = [f"{b} {c}" for b, c, e in _chapters(track) if not e]
    assert not missing, f"{track}: {len(missing)} chapters absent from manifest: {missing[:10]}"


# done_gate: RED until P0 fills the pending chapters' folios (module docstring)
# — a milestone pin, deselected in CI (-m "not done_gate"), visible on dev boxes.
@pytest.mark.done_gate
@pytest.mark.parametrize("track", ["samuel", "kings"])
def test_every_chapter_has_both_witness_folios(track):
    bad = []
    for b, c, e in _chapters(track):
        cam = (e.get("CAM") or {}).get("folios") or []
        gg = (e.get("GG") or {}).get("folios") or []
        if not cam or not gg:
            bad.append(f"{b} {c} (CAM={len(cam)}, GG={len(gg)})")
    assert not bad, f"{track}: {len(bad)} chapters lack folios: {bad[:10]}"


@pytest.mark.parametrize("track", ["samuel", "kings"])
def test_every_referenced_image_exists(track):
    # The referenced images live in the gitignored GAPS/ tree — out-of-repo
    # box data that CI runners never carry. Skip only when the WHOLE tree is
    # absent; a present-but-incomplete tree (data drift between dev boxes)
    # must keep failing loudly.
    if not (REPO / "GAPS").is_dir():
        pytest.skip("GAPS/ manuscript-image tree not on this box (gitignored dev-box data)")
    absent = []
    for b, c, e in _chapters(track):
        rels = ((e.get("GG") or {}).get("source_images") or []) + ((e.get("CAM") or {}).get("views") or [])
        absent += [f"{b} {c}: {r}" for r in rels if not (REPO / r).exists()]
    assert not absent, f"{track}: {len(absent)} referenced images missing on disk: {absent[:10]}"
