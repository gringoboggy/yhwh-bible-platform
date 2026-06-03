---
holder: windows
from: mac
turn: 2
updated: 2026-06-03
status: idle
---

## Done (turn 2, windows lane — this session)
- **P0 Sam/Kings — 1 Samuel 1–17 dual-witness folio map COMPLETE** (this was the documented "dense-section wall"). Unique-event anchoring + recension awareness (GG = LXX/Kingdoms-compressed; CAM = MT/printed-fuller) retired the wall; three HIGH-confidence cross-checked vision passes (CAM keystone 7–17 · GG companion 2–17 · CAM 1–6 re-verify), penned folio numbers confirmed the view↔folio arithmetic. Corrected the prior shifted 1sa 4–11 CAM (on-disk filename labels were ~+3 chapters off) + filled 2,12–16.
- New reusable **`content/manuscript/_reviewer_context/SAMKINGS_FOLIO_ANCHOR_INDEX.md`** (method + per-chapter unique-event anchor tables for all 4 books + §12/§13 confirmed maps + image-availability inventory). Rewrote `samuel/manifest.yaml` 1sa 1–17 (both witnesses, boundary-generous, status `pending`) via a deterministic generator.
- Gate `tests/test_samkings_manifest_complete.py`: image-existence GREEN; has-folios failures 43→37 samuel. Commits `8b6cb947` (P0) + `683bf66e` (monetization plan).
- **Monetization & sustainability plan** authored (`plans/2026-06-03-monetization-and-sustainability-plan.md`): donations / print-on-demand / hosted open-core builder / commissions+grants — **the Word + digital stay free.** Mac website lane is wiring the support links (Ko-fi `ko-fi.com/gringoboggy` live; PayPal handle pending; GitHub Sponsors after enrollment).
- Pulled Mac's commits (`746a0546` font self-host + homepage rebuild incl. the `#donations` support scaffold; `361462ca` README). **Took the baton → windows** (Mac idle).

## Next (fresh session — Windows P0 is the critical path)
- **Continue P0 folio-mapping: 1sa 18–31 → 2sa 1–24 → 1ki 7–22 → 2ki 1–25.** READ `_reviewer_context/SAMKINGS_FOLIO_ANCHOR_INDEX.md` FIRST (method + anchor tables). GG is 100% on disk; **CAM needs CUDL-IIIF acquire** for most remaining folios — use `scripts/acquire_cudl_master.py` (anchor f106r=view215, 2 views/leaf; VERIFY each view→folio by reading the penned recto number). MAX-1 heavy vision; sub-batch check-ins; run the manifest gate per batch.
- Then P1 pod bulk-transcription waits on the user's pricing-trigger — OR grind locally free (agent path = Max subscription, slow but $0).
- (Mac lane, file-disjoint, if it resumes:) wire the support links live + rebuild the website content + `build_site.py` + GitLab Pages.

## Watch-outs
- **Baton held by `windows`.** If the fresh session is Mac (website), `/resume --force` after confirming Windows is idle.
- P0 fill = boundary-generous folio lists (onset→next-onset); status stays `pending` (mapped, not transcribed) so the collation driver can't mis-trigger.
- ⚠ CAM on-disk filename `_1SamN_` suffixes are WRONG (~+3 shifted); the FOLIO number is authoritative + penned-verified. Map by folio, ignore the suffix.
- ⚠ (Mac OCR) tests via Claude Bash need `export TMPDIR=/Volumes/MacHD2/<dir>`.
