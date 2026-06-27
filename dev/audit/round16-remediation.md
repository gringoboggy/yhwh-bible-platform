# Round-16 remediation tracker — Build-Program Bulletproofing

Plan USER-APPROVED in plan mode (2026-06-27). Program: `dev/audit/round-16-build-program-bulletproofing-2026-06-27.md` (READ FIRST).
Process: configure `deep-audit.js ROUND=16` (DONE) → run two-lane (both lanes all 11 dims; WIN harness + Mac cross-OS verify) → adversarially verify → **gather all findings (FINDINGS-ONLY)** → merge → phased fixes plan for user approval. NO fixes this round.
`truth_owner = windows`; file-disjoint parallel. Marathon core OFF-LIMITS. Round-14 build-source dims + round-15 D1–D9 are `DEFERRED_BY_DESIGN` (do NOT re-litigate).

## Status: ⏳ NOT YET RUN — engine configured + Mac instructions pushed; awaiting the two autonomous lane runs.

## Findings (filled as the run surfaces them)

| # | dim | sev | source | finding / defect class | file:line or artifact | status |
|---|-----|-----|--------|------------------------|-----------------------|--------|
| — | — | — | — | _(none yet — run pending)_ | — | — |

`source ∈ {engine-win, engine-mac, harness, xos-verify}`. Severity from the calibrated skeptic panel. UNVERIFIED survivors (empty panel after retry) get their own row flagged `⚠ UNVERIFIED — human triage`.

## The 3 pre-found scoping seeds (start the verification here)

1. **`computer` orphan option** — valid `TARGET_READERS` value + `/customize` reader option, NO `FORMAT_MATRIX` row → silent everywhere-alias, no catalog asset, no test. (`cross-product` + `options-completeness`.)
2. **kindle declared ≠ built** — `FORMAT_MATRIX` kindle row declares `target_reader:"kindle"`, ships everywhere base + `kindle_post`. (`cross-product`.)
3. **standalone target degeneracy** — `apply_target_override` raises on a standalone `--target-reader`; geez/amharic = one shape each. (`cross-product`.)
4. **headline NEW gap** — code/template leak + built-artifact HTML well-formedness has NO gate (`[Reviewer:]` lint is commit-time only; G1 nested-anchor is base-only). (`html-integrity` + `audit_output_hygiene.py`.)

## Lane / side-work division (truth_owner = windows)

| Lane | Engine | Side-work |
|------|--------|-----------|
| WIN | all 11 `ROUND16_DIMS` | full-catalog build-inspect harness + `audit_output_hygiene` + existing gates; owns `build_edition.py` |
| MAC | all 11 `ROUND16_DIMS` | cross-OS verify (9 KJV golden → G1 9/9; one catholic-study eink → gates) + build-free gate `_selftest` |

## Gate deliverables (authored during the run; permanent)

- `dev/audit_cross_product.py` (build-free, dim 4 — headline) + `dev/audit_customize_completeness.py` (build-free, dim 9) → `tests/test_round16_source_gates.py`.
- `dev/audit_output_hygiene.py` (merged artifact scanner, dims 5/6/7/8; reuses audit_spine_breaks + audit_badge_conservation[extended] + audit_idmap_frags) → `tests/test_round16_build_gates.py`.
- `lint_rules` checks (dim 3): subprocess `stdin=DEVNULL`; `epub_working/` writes via `notes_io.atomic_write`.

## Log

- **2026-06-27 setup (WIN)** — plan approved; `deep-audit.js` configured (ROUND=16, 8 new dims, ROUND16_DIMS, selector, DEFERRED folded, PRIOR_SURVIVORS updated, stale pointer fixed; node syntax OK; all 11 keys resolve); program doc + this tracker authored; `dev/LANE_HANDOFF.md` Mac block pushed. **Audit NOT started this session** (user directive). Next: the fresh WIN session + the Mac session run their lanes autonomously to completion.
