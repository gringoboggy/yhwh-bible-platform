# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->

> **▶ ✅ 2026-06-14 (🖥️ Mac, turn 84 — ★★ K-KIN RESOLVED ON THE REAL CHANNEL: `june10recipe` DELIVERED via Send-to-Kindle, USER-CONFIRMED).** The reproduced **June-10 test-2 recipe** — `~/Desktop/Ethiopian Bible - Catholic Study (Kindle) june10recipe.epub` (standard everywhere build + `display:none` physically stripped + single `en-US`; 24.1 MB, 299 spine, epubcheck 0/0/0/0; **NONE of FIXED's shipshape/split/attr-strip extras**) — **WORKED on Send-to-Kindle** (fast upload, delivered; user-confirmed). ⇒ **the KP3-oracle-driven extras (shipshape compaction + 189-way file-split + attr-strip) were what BROKE Send-to-Kindle**; the minimal recipe (strip `display:none` + single lang, nothing else) is the proven-good shape. **PROVEN RECIPE (to productize):** `scripts/build_edition.py catholic-study` (standard) → post-process: strip `display:none`/`visibility:hidden` (CSS+inline) · collapse `dc:language`→single `en-US` · leave `hidden=""` · OCF re-zip (mimetype-first stored). **NEXT (fresh session):** (1) productize this as the clean kindle build mode (it's currently standard-build + a deterministic post-process script) → then WIN lights FORMAT_MATRIX **M4**; (2) v1.0.0 laundry list `notes/2026-06-14-mac-v1.0.0-laundry.md`. Detail: e999 note CORRECTION + WIN sections. Baton **windows** (truth_owner); mode=parallel.
>
> **▶ 🔄 2026-06-14 (🪟 Windows, turn 83 — CI health swept + Mac v1.0.0 laundry delivered + decommercialize-tail docs).** Bootstrapped; fixed BOTH CIs. (1) **GitLab** per-push pipelines were all `ci_quota_exceeded` (monthly CI minutes blown ~Jun 6 — NOT code; jobs never start) → `.gitlab-ci.yml` `workflow:rules` stops per-push pipeline creation (ends the failure-email spam; GitHub Actions stays the real per-push CI; manual/scheduled survive). (2) **GitHub** fast-gate green (Mac's KDP reword `7bec299b` pulled) + 2 stale `test_scripts.py` pins fixed (`bcp47` multi-lang/non-kindle + `enable_ai_notes` frozenset import) — verified pass; `popup_split` 52/52. (3) **Mac v1.0.0 laundry** = `notes/2026-06-14-mac-v1.0.0-laundry.md` (5-dim code-verified). (4) **Decommercialize-tail docs (2nd milestone):** free-public `RELEASE_NOTES_v1.0.0.md` rewrite + `HANDOFF_README_v7.md` pre-pivot banner. **K-KIN:** WIN's "restart the Kindle arc against the STK oracle (Mac)" directive is **DONE — see turn-84 (RESOLVED on Send-to-Kindle).** Next WIN session: confirm the GitHub `Tests` run greened, then pick the next v1.0.0 item. Baton **windows** (truth_owner); mode=parallel.
>

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via the Esther vision lane.

## Background backlog (never single-thread — RULES §2.5)

> When a lane frees, auto-pick the next: the mint-7 plan phases · CAM hi-res pre-pull · base-structured re-collation · geez→kjv xref anchoring · Phase-E Clementine (1es/2es) · doc-coherence currency · test-coverage growth · Phase-D source acquisition.
