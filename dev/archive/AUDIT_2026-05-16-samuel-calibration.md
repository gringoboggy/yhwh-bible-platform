# AUDIT 2026-05-16 — τ.6.x.4.a Samuel calibration arc (quick solo)

**Type:** lighter SOLO-Claude battery (per the audit-cadence convention — proactive after a major arc closure; NOT the parallel-subagent DEEP sweep). Read-only + doc-only.
**Trigger:** user "do a quick audit, fix, commit" at the close of the τ.6.x.4.a Samuel calibration gate, before a `/clear`.
**Scope:** the calibration arc only (commits `6882063` evidence+report, `5a2c073` decision) + the just-written handoff docs.

## Checks run (one consolidated verification pass)

1. **Evidence integrity (3 files):** `1sa1_witnessGG.json` (GG, 28v contiguous, 442 tok, 16 illegible == 16 sentinel, contract OK, bounds OK, 0 numeral-glued); `1sa1_witnessCAM.json` (CAM low-res, 28v, 400 tok, 6==6, OK); `1sa1_witnessCAM_hires.json` (CAM hi-res, 28v, 404 tok, **0 illegible == 0 sentinel**, OK). All assertions PASS.
2. **Collation integrity (2 files):** `1sa1_collation.json` (low-res baseline, 28v, base=GG, strict 24.79 == basis; retained as the documented confound baseline, unmodified). `1sa1_collation_hires.json` (authoritative, 28v, base=CAM, strict 32.55 == basis, skeleton 44.75 == basis over aligned 467, both-confident 73.05, `definitions` + `delta_vs_lowres.method` present). All assertions PASS.
3. **Lacuna reconciliation:** hi-res `lacuna-gg` rows == `metrics.lacuna_counts.gg` == GG-evidence `⟦illegible⟧` token count == **16**; no `⟦illegible⟧` row mis-classed; lacunae excluded from agreement denominators. PASS.
4. **Report ↔ JSON consistency:** all 7 mandated sections present + `Decision (user): GO` filled; headline numbers (73.05 / 44.75 / 32.55) and CC BY-NC Cambridge attribution present and traceable to the JSON. PASS.
5. **Git integrity:** `6882063` + `5a2c073` present on `main`; pre-commit hook had passed (`ruff format` 529 clean, `lint_rules.py [pre-commit] ok`); working tree contained only the *intended* handoff changes (IN_FLIGHT edit + new plan file at audit time). No scratch/junk (`.tmp/.png/.log/chk_/cam_recon`) tracked or committed; `.sonar/` correctly excluded from the calibration commit.
6. **Handoff coherence:** memory (`reference_gaps_folder`, new `reference_cudl_iiif`, `feedback_reverify_conservative_nogo` + MEMORY.md index), SESSION_STATE top banner, IN_FLIGHT current-task, and the saved widened-pilot plan are mutually consistent and point at the same next step + chapters.

## Result

**STATE CLEAN — NO FIXES REQUIRED.** Every artifact of the τ.6.x.4.a arc is internally consistent and consistent with the report and the user decision. This is expected: the arc was adversarially spec+honesty reviewed at every step and the authoritative collation passed two review rounds (the only two defects — a lacuna mis-class and a non-like-for-like delta — were already caught and fixed in-arc before this audit).

## Recorded non-issues (no action — by design)

- **Hi-res CAM images live in `GAPS/1_Samuel/Cambridge-Add-1570-hires/` (outside the git repo).** This mirrors how the original Cambridge crops + GG scans are also GAPS-side source data, not repo content — intentional, not a loss. Provenance is captured in the report §1, `SOURCES.md`, and auto-memory `cudl-iiif-access`. Formal `_source.yaml` attribution is a **Phase-3** deliverable (spec §6/§9), correctly deferred — not in calibration scope.
- **`1sa1_collation.json` (low-res) base=GG vs hi-res base=CAM** is an intended, documented flip (the low-res GG pick was a resolution artifact; recorded in both the hi-res `base_rationale` and report §4) — not an inconsistency.

## Conclusion

τ.6.x.4.a is cleanly closed and safe to `/clear` past: nothing lost, next step durably saved (plan file + triad + memory), audit + handoff committed. Resume by executing `docs/superpowers/plans/2026-05-16-samuel-widened-calibration.md`.
