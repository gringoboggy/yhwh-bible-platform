# Samuel/Kings Folio Index (P0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** ready — P0 of `specs/2026-06-02-samkings-cloud-draft-at-scale-design.md`. Vision-data task on the N95, supervised, before any pod spend.

**Goal:** Complete the two existing folio manifests (`content/manuscript/{samuel,kings}/manifest.yaml`) so every canonical chapter of 1sa/2sa/1ki/2ki maps to its CAM (base) + GG (2nd-witness) folio image(s) — the reusable input contract the at-scale collation drivers run against.

**Architecture:** This is a **vision-data-completion task, NOT a code-build** — the entire manuscript pipeline already exists (`scripts/core/manuscript_*.py` + `run_manuscript_*_at_scale.py`). We add exactly ONE code artifact: a fast structural **completeness test** that acts as the done-gate (red now → green when P0 finishes). The bulk is supervised vision: walk each witness's folios in order, identify the chapter:verse range each carries, and fill the manifest. The brittle part — locating chapters by vision, not arithmetic (CAM packs ~1.5–2 ch/folio; GG ~1–3 ch/folio across 3 columns; words split across column/page turns) — is exactly why P0 is supervised and done once.

**Tech Stack:** Python 3 (full interpreter path; `$env:PYTHONUTF8="1"`), PyYAML, the existing `scripts/core/manuscript_manifest.py` (`load_manifest`, `chapter_entry`) + `manuscript_vision.py` (safe crop/encode, cap 1568 px), `scripts/acquire_cudl_master.py` (`fetch_master(view_id, out)` — CUDL IIIF, anchor 1Sam1 = view 215 = f106r), pytest with `--basetemp` per memory `reference_pytest_basetemp`.

**Scope facts (verified 2026-06-02):**
- Manifest schema per chapter: `{CAM: {folios:[…], views:[…]}, GG: {folios:[…], source_images:[…]}, status: calibrated|pending}`.
- Witnesses: **CAM** = Cambridge Add. 1570 (base; `base_witness_recommended` per-chapter, defaults CAM) · **GG** = Gunda Gundē (2nd witness).
- Already filled (calibration): Samuel 1sa 1,3,17 + 2sa 11; Kings 1ki 1–6. **Pending (P0 fills): Samuel 1sa 2,4–16,18–31 + 2sa 1–10,12–24 (51 ch); Kings 1ki 7–22 + 2ki 1–25 (41 ch).**
- GG images on disk: `GAPS/1_Samuel/GG-00106/1-Samuel/1-Samuel_f###[rv].jpg` + `GAPS/2_Kings/GG-00106/…/1-Kings_f###[rv].jpg` (clean folios present; some crop-variants alongside).
- CAM hi-res on disk: **only the calibration chapters** (1_Samuel 9 files, 2_Kings 24) → pending CAM folios must be **IIIF-acquired** into `GAPS/<book>/Cambridge-Add-1570-hires/MS-ADD-01570_f###[rv]_<label>_hires.jpg`.
- P0 fills `folios`+`source_images`/`views`; **`status` stays `pending`** (folios-mapped-but-not-yet-transcribed — the collation driver only collates `status: calibrated` chapters, so P0 cannot mis-trigger collation).

---

### Task 1: The completeness done-gate (the one code artifact)

**Files:**
- Test: `tests/test_samkings_manifest_complete.py` (create)

- [ ] **Step 1: Confirm the manifest import pattern an existing test uses**

Run: `rg -n "manuscript_manifest" tests/ scripts/` (or Grep). Match the import style already in the repo (e.g. a `conftest.py` that puts `scripts/` on `sys.path`, so `from core import manuscript_manifest`). Use that exact pattern in Step 2 instead of guessing.

- [ ] **Step 2: Write the failing completeness test**

```python
# tests/test_samkings_manifest_complete.py
"""P0 done-gate: the Samuel + Kings folio manifests must be COMPLETE — every
canonical chapter carries non-empty CAM + GG folios and every referenced image
resolves on disk. Fast structural check (no vision). Drives P0 to green."""
from pathlib import Path

import pytest

from core import manuscript_manifest as mm  # adjust to the repo's import pattern (Task 1 Step 1)

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
    absent = []
    for b, c, e in _chapters(track):
        rels = ((e.get("GG") or {}).get("source_images") or []) + ((e.get("CAM") or {}).get("views") or [])
        absent += [f"{b} {c}: {r}" for r in rels if not (REPO / r).exists()]
    assert not absent, f"{track}: {len(absent)} referenced images missing on disk: {absent[:10]}"
```

- [ ] **Step 3: Run it — confirm it FAILS (the red gate)**

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_samkings_manifest_complete.py -v --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: `test_every_chapter_has_both_witness_folios` FAILS for both tracks (~51 samuel + ~41 kings chapters lack folios). `test_every_chapter_present` should PASS (all chapters are in the YAML as `pending`). This red state is P0's target to flip green.

- [ ] **Step 4: Commit the gate**

```bash
git add tests/test_samkings_manifest_complete.py
git commit -m "test(p0): Sam/Kings folio-manifest completeness gate (red until P0 fills folios)"
```
(Then the full 5-leg save via `save-all.ps1` per memory `reference_save` — same for every commit below.)

---

### Task 2: Pilot batch — 1 Samuel 4–6 (prove the folio-walk + CAM IIIF acquisition end-to-end)

**Why a pilot first:** the spec mandates a supervised proof before bulk. 1sa 4–6 is a contiguous narrative run adjacent to the calibrated 1sa 3, so the GG/CAM folio sequence is anchored. Proving this batch validates the whole procedure (GG-on-disk walk + CAM IIIF acquire-and-scan + manifest fill + gate) before committing to 88 more chapters.

**Files:**
- Modify: `content/manuscript/samuel/manifest.yaml` (1sa 4, 5, 6 entries)
- Acquire into: `GAPS/1_Samuel/Cambridge-Add-1570-hires/`

- [ ] **Step 1: Map the GG folios for 1sa 4–6 (vision; GG is on disk).**

List the GG folios after the calibrated 1sa 3 (f004r): `Get-ChildItem GAPS/1_Samuel/GG-00106/1-Samuel/ -Filter '1-Samuel_f00[4-9]*.jpg'`. Render each candidate folio (use `manuscript_vision`'s crop/encode at ≤1568 px) and read its column→line→verse to find where 1sa 4, 5, 6 each begin and end. Record the folio siglum(s) per chapter. **Locate by vision, not arithmetic** — a folio may carry 1–3 chapters and a verse may straddle a column turn; confirm each chapter's first word against the KJV skeleton (`content/translations/kjv/1sa.py`).

- [ ] **Step 2: Acquire + map the CAM folios for 1sa 4–6 (IIIF).**

CAM hi-res for these chapters is not on disk. Walk views forward from the 1sa 3 anchor (f107r ≈ view 217) with `python scripts/acquire_cudl_master.py` (or `from acquire_cudl_master import fetch_master`): for each next view, `fetch_master(view_id, GAPS/1_Samuel/Cambridge-Add-1570-hires/MS-ADD-01570_f###_1Sam#_hires.jpg)`, read the printed folio number + opening verse to confirm the view→folio→chapter mapping, and stop once 1sa 6 is covered. Name the files to match the existing convention (`MS-ADD-01570_f###[rv]_1Sam#_hires.jpg`).

- [ ] **Step 3: Fill the manifest entries for 1sa 4, 5, 6.**

Edit `content/manuscript/samuel/manifest.yaml` — for each of 1sa 4/5/6, set `GG.folios` + `GG.source_images` (the on-disk paths) and `CAM.folios` + `CAM.views` (the acquired hi-res paths); leave `status: pending`. Match the exact YAML shape of the 1sa 1/3 entries (2-space indent, relative `GAPS/...` paths).

- [ ] **Step 4: Verify the pilot chapters pass the gate.**

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_samkings_manifest_complete.py::test_every_referenced_image_exists -v --basetemp="…\bt"`
Expected: the image-existence test no longer reports 1sa 4/5/6 paths (they now resolve). Also run `python scripts/run_manuscript_collation_at_scale.py --track samuel` (dry) and confirm 1sa 4–6 now appear with non-empty folios in the pending report (they stay "pending" — no witness JSONs yet — which is correct).

- [ ] **Step 5: Commit the pilot + report metrics.**

Record wall-time + token burn for the 3-chapter pilot (this calibrates the per-chapter cost for the rest of P0 and informs whether to finish on the N95 or fold into the pod). Commit:
```bash
git add content/manuscript/samuel/manifest.yaml "GAPS/1_Samuel/Cambridge-Add-1570-hires/MS-ADD-01570_f*_1Sam*.jpg"
git commit -m "p0(samuel): folio-map 1sa 4-6 (pilot) — GG on-disk walk + CAM IIIF acquire"
```
⚠ GAPS is gitignored — the acquired CAM images will NOT be force-added by default (intended; the ~1 GB image tree stays out of git). Only the manifest YAML is committed; the acquired images live in GAPS and are uploaded to the pod separately in P1. (Do NOT `git add -f` the images.)

**CHECKPOINT — pause for user review of the pilot before the bulk batches.**

---

### Task 3: 1 Samuel bulk — chapters 2, 7–16, 18–31

**Files:** Modify `content/manuscript/samuel/manifest.yaml`; acquire into `GAPS/1_Samuel/Cambridge-Add-1570-hires/`.

- [ ] **Step 1:** Repeat the Task-2 procedure (GG-walk + CAM-IIIF-acquire + manifest-fill) for 1sa **2** (isolated, between calibrated 1 and 3), then the contiguous runs **7–16** and **18–31** (1sa 17 is already calibrated). Work in sub-batches of ~5 chapters; locate by vision; confirm chapter onsets against `content/translations/kjv/1sa.py`.
- [ ] **Step 2:** After each sub-batch, run the gate's `test_every_referenced_image_exists` + a `run_manuscript_collation_at_scale.py --track samuel` dry-report; confirm the new chapters carry folios.
- [ ] **Step 3:** Commit each sub-batch (`p0(samuel): folio-map 1sa <range>`), 5-leg save.

### Task 4: 2 Samuel — chapters 1–10, 12–24

- [ ] **Step 1:** Same procedure for 2sa **1–10** and **12–24** (2sa 11 is calibrated). The GG source is the same `GAPS/1_Samuel/GG-00106/` tree (Gunda Gundē packs Samuel together); CAM continues the IIIF view sequence past 1 Samuel. Sub-batches of ~5; vision-located; onsets confirmed against `content/translations/kjv/2sa.py`.
- [ ] **Step 2:** Gate + dry-report per sub-batch.
- [ ] **Step 3:** Commit each sub-batch, 5-leg save.

- [ ] **Step 4: Samuel track green.** Run `pytest tests/test_samkings_manifest_complete.py -v -k samuel` → all three tests PASS for `samuel`. Commit `p0(samuel): folio index COMPLETE (1sa+2sa)`.

### Task 5: 1 Kings — chapters 7–22

**Files:** Modify `content/manuscript/kings/manifest.yaml`; GG from `GAPS/2_Kings/GG-00106/` (`1-Kings_f###.jpg`); acquire CAM into `GAPS/2_Kings/Cambridge-Add-1570-hires/`.

- [ ] **Step 1:** Same procedure for 1ki **7–22** (1ki 1–6 calibrated). CAM IIIF views continue past Samuel; the 1ki 1 anchor is f126r (already on disk) — walk forward. Onsets vs `content/translations/kjv/1ki.py`. Sub-batches of ~5.
- [ ] **Step 2:** Gate + `run_manuscript_collation_at_scale.py --track kings` dry-report per sub-batch.
- [ ] **Step 3:** Commit each sub-batch, 5-leg save.

### Task 6: 2 Kings — chapters 1–25 (none started)

- [ ] **Step 1:** Same procedure for 2ki **1–25**. GG from `GAPS/2_Kings/GG-00106/` (`2-Kings_f###.jpg` if present; verify the filename prefix in Step 0 — it may be `1-Kings_…`/`2-Kings_…`). CAM IIIF continues. Onsets vs `content/translations/kjv/2ki.py`. Sub-batches of ~5.
- [ ] **Step 2:** Gate + dry-report per sub-batch.
- [ ] **Step 3:** Commit each sub-batch, 5-leg save.

- [ ] **Step 4: Kings track green.** Run `pytest tests/test_samkings_manifest_complete.py -v -k kings` → PASS. Commit `p0(kings): folio index COMPLETE (1ki+2ki)`.

---

### Task 7: P0 complete — full gate green + hand-off

- [ ] **Step 1: Full gate green.**

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_samkings_manifest_complete.py -v --basetemp="…\bt"`
Expected: all 6 parametrized tests PASS — every 1sa/2sa/1ki/2ki chapter carries CAM+GG folios that resolve on disk.

- [ ] **Step 2: Update the truth-record + memory.**

Update `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` (P0 done; folio index complete) and the memory `reference_runpod_cloud_budget` (P0 → done; next = P1 pod bring-up). Note the measured per-chapter folio-mapping cost from the pilot + batches.

- [ ] **Step 3: Final commit + 5-leg save.**

```bash
git add content/manuscript/samuel/manifest.yaml content/manuscript/kings/manifest.yaml dev/SESSION_STATE.md dev/IN_FLIGHT.md
git commit -m "p0: Sam/Kings folio index COMPLETE — all 102 chapters mapped (CAM+GG); input contract for P1/P2 ready"
```

- [ ] **Step 4: Hand-off note.** P1 (pod bring-up) is now unblocked: the completed manifests + the now-on-disk CAM hi-res are part of the ~1 GB GAPS upload; the existing `run_manuscript_{transcribe,review,collation}_at_scale.py` drivers will run against this folio map on the pod (P2).

---

## Self-Review

**Spec coverage:** P0 in the spec = "complete the folio index for ~92 pending chapters, on the N95, before pod spend." Covered by Tasks 2–6 (the fill) + Task 1 (the gate) + Task 7 (done-criterion + hand-off). The spec's IIIF-acquisition dependency (CAM hi-res off-disk) is covered in Task 2 Step 2 + each bulk task. ✔

**Placeholder scan:** The vision steps (GG-walk, CAM-acquire) are intentionally procedural, not code — folio assignments are *discovered* by vision and cannot be pre-written; the gate test (real code, full) is the verification each batch drives green. No "TBD"/"handle edge cases"/uncoded code-steps remain. ✔

**Type consistency:** The manifest shape (`CAM.{folios,views}`, `GG.{folios,source_images}`, `status`) and the loader calls (`mm.load_manifest(track=…)`, `mm.chapter_entry(man, book, ch)`) match the verified schema + `manuscript_manifest.py` API throughout. The gate's `CANON` counts (1sa 31 / 2sa 24 / 1ki 22 / 2ki 25) are the canonical chapter totals. ✔

**Open item to confirm at execution (not a blocker):** Task 1 Step 1 pins the exact `manuscript_manifest` import path from an existing test; Task 6 Step 0 confirms the 2 Kings GG filename prefix. Both are quick on-the-spot checks, not design gaps.
