---
holder: windows
from: mac
turn: 4
updated: 2026-06-03
status: idle
---

## Done (turn 4, windows lane — this session)
- **P0 Sam/Kings: 1 SAMUEL COMPLETE (all 31 ch, both witnesses).** Added 1sa 18–31 via a GG companion pass + a CAM pass (incl. the session's **first CUDL-IIIF acquire** of CAM f114r–f117v — ★needs `PYTHONPATH=<repo>` or `scripts.core` import fails). Recension: GG (LXX) omits 18:1–5 (ch18 opens at the women's song); CAM (MT-fuller) ch18 = 18:1 covenant; 1 Samuel ends mid-folio (GG f017v / CAM f117r), 2 Samuel 1 immediately after. `samuel/manifest.yaml` 1sa 1–31 filled (boundary-generous folio lists, status `pending`); anchor index §14 added. Gate: image-existence GREEN; samuel has-folios now only 2sa pending (23). Commit `ab86dd87`.
- Documented Mac's new `brand/` dir in `REPO_MAP.md` (it was failing `repo_map_complete` + blocking commits).
- Pulled Mac's turn-3 (brand/identity kit; **GitHub Sponsors $1–$5 tiers PUBLISHED**, pending staff review; bootup env-health checks). **Took the baton → windows; full 5-leg save (PUSHED to GitLab+GitHub+E:+F:).**

## Next (fresh session — Windows P0 is the critical path)
- **P0 2 Samuel (1–10, 12–24).** READ `content/manuscript/_reviewer_context/SAMKINGS_FOLIO_ANCHOR_INDEX.md` FIRST (§9 = the 2sa unique-event table; method in §1). GG on disk: `GAPS/1_Samuel/GG-00106/2-Samuel/2-Samuel_f017v…f028v.jpg`. **CAM needs CUDL-IIIF acquire** — continue the view sequence past f117 (`scripts/acquire_cudl_master.py` with `$env:PYTHONPATH=<repo>`; anchor f106r=view215, 2 views/leaf; verify each by reading the penned recto number). 2sa 11 is calibrated (CAM f120r/v). Then 1ki 7–22 → 2ki 1–25. MAX-1 heavy vision; sub-batch check-ins; run the manifest gate per batch.
- **Mac (website lane), file-disjoint, if it resumes:** website repo (`gringoboggy.github.io`) + GitHub Pages + **Spaceship DNS** (needs the user's API key + secret); wire support links (Sponsors / PayPal / Ko-fi) + `.github/FUNDING.yml`; rebuild site content + `build_site.py` + Pages deploy.

## Watch-outs
- **Baton held by `windows` (status: idle).** If the fresh session is Mac (website), `/resume --force` after confirming Windows is idle.
- ⚠ CAM on-disk filename `_1SamN_` suffixes are ~+3 shifted — map by the penned FOLIO number, not the suffix. (Newly-acquired f114r+ are folio-named correctly.)
- ⚠ `acquire_cudl_master.py` needs `$env:PYTHONPATH=<repo>` (it imports `scripts.core`).
- ⚠ (Mac OCR) tests via Claude Bash need `export TMPDIR=/Volumes/MacHD2/<dir>`.
