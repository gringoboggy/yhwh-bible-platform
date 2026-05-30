# AUDIT 2026-05-17 — τ.6.x.4.a-W Samuel widened-calibration arc (quick solo)

**Type:** lighter SOLO-Claude battery (per the audit-cadence convention — proactive at major arc closure; NOT the parallel-subagent DEEP sweep). Read-only + doc-only.
**Trigger:** arc-close of the τ.6.x.4.a-W widened calibration (Tasks 7–11 of `docs/superpowers/plans/2026-05-16-samuel-widened-calibration.md`), before the single local commit + user gate.
**Scope:** the 3 new 2 Sam 11 artifacts + the aggregate report + cross-chapter reconcile (the 1 Sam 3 / 1 Sam 17 artifacts were shipped + audited at the prior Ch1+Ch2 checkpoint; this audit re-reconciles them against the aggregate, not re-litigated).

## Checks run (one consolidated programmatic verification pass)

1. **2 Sam 11 honesty bijection:** `2sa11_witnessGG.json` (GG, 27 v contiguous, 508 tok, **0 `⟦illegible⟧` == 0 illegible-marker**, all 48 `uncertain[].token_index` in range) and `2sa11_witnessCAM_hires.json` (CAM, 26 v-obj, 424 tok, **0 == 0**, all 44 indices in range). PASS.
2. **2 Sam 11 collation metric recompute (from raw `alignment[]`):** strict 187/551 = **33.94** == stored+basis; skeleton 317/551 = **57.53** == stored+basis; semantic 27/27 = **100.0** == basis; `lacuna_counts == {gg:0,cam:0,both:0}`. PASS.
3. **Token-conservation:** GG alignment-cell multiset **exactly** equals GG evidence tokens (total 508); CAM exactly equals CAM evidence (total 424); lacuna rows none. PASS. (The collation builder's inline token-conservation gate caught + fixed 3 real token-drops mid-build — a dropped GG `አኮኑ` v10, a dropped one-sided CAM `ኬጥያዊ` v6, a missing 8-token CAM v21-object at spine v22 — before the adversarial review, which then independently re-verified the multiset.)
4. **Schema verbatim-reuse:** `2sa11_collation.json` `metrics.definitions` block **byte-identical** to `1sa17_collation.json`; top-level key order identical (`book, chapter, base_witness_recommended, base_rationale, verses, metrics`). PASS.
5. **Aggregate report ↔ JSON consistency (hand-written-table verification):** every figure in the per-chapter table of `dev/CALIBRATION_2026-05-16-samuel-widened.md` was checked **against the actual collation `metrics`** for all four chapters — 1 Sam 1 (73.05/44.75/32.55, 28/28), 1 Sam 3 (89.35/60.11/36.34, 21/21), 1 Sam 17 (68.97/16.64/9.71, 58/58), 2 Sam 11 (86.39/57.53/33.94, 27/27) — both that the report figure equals the file metric AND that it appears verbatim in the report. No transcription error. PASS.
6. **Deliverable-convention hygiene:** the collation builder's `_build_2sa11_collation.py` + `__pycache__` were dropped — the established calibration-deliverable convention is **pure JSON** (siblings `1sa1`/`1sa3`/`1sa17` carry no `_build_*` script; the adversarial reviewer confirmed `_build_1sa3_collation.py` never existed, correcting an inaccurate IN_FLIGHT helper-note). Calibration dir now holds only the 14 immutable evidence/collation JSONs. CUDL hi-res CAM stitches (f120r/f120v ~80 MP) live GAPS-side (outside the repo) like all prior MS source data — intentional, provenance in report §1 + auto-memory `cudl-iiif-access`; CC BY-NC, Cambridge University Library.
7. **Adversarial-review provenance:** every artifact passed an independent adversarial spec+honesty review (GG: FAIL→fixed `፡`-tokenization + 48-marker re-index, the reviewer's own remap table corrected by note-target re-derivation, then PASS; CAM: PASS clean first pass; collation: PASS clean, every metric independently recomputed + builder reproduced byte-for-byte). Blind protocol confirmed uncontaminated by each reviewer (transcribers saw only their own witness).

## Result

**STATE CLEAN — NO FIXES REQUIRED.** All 2 Sam 11 artifacts and the aggregate are internally consistent, consistent with each other, and consistent with the four collation `metrics` blocks. Expected: every step was adversarially reviewed with fix-loops to ✅ before this audit.

## Recorded non-issues (no action — by design)

- **CRLF line endings** on the calibration/aggregate files match every sibling (the known `editions_crlf_gitnoise` artifact); LF-normalizing 2 Sam 11 alone would make it the outlier — left as-is (directory-wide, if ever).
- **2 Sam 11 base = CAM with both witnesses full-length & GG-undamaged (0 illegible)** is the *strengthening* observation, not an inconsistency: it shows the CAM-base choice is not a GG-damage artifact.
- **`## Decision (user): _pending_`** in the aggregate is correct — this is a user GO/adjust/NO-GO gate (mirrors the 1 Sam 1 report), not unfinished Claude work; τ.6.x.4.a-W execution is complete.

## Conclusion

τ.6.x.4.a-W is cleanly closed: 3 new immutable evidence/collation JSONs + the aggregate report + this audit, all reconciled. The bi-directional decision rule resolved to **CONFIRM** (distinct-recension + CAM-base generalize across all 3 widened chapters + pilot; no contradiction). Next step is the **user gate** in the aggregate report; Phase-2 is not started until ratified.
