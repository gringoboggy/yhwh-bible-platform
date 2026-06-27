# Round-16 remediation tracker — Build-Program Bulletproofing

Plan USER-APPROVED in plan mode (2026-06-27). Program: `dev/audit/round-16-build-program-bulletproofing-2026-06-27.md` (READ FIRST).
Process: configure `deep-audit.js ROUND=16` (DONE) → run two-lane (both lanes all 11 dims; WIN harness + Mac cross-OS verify) → adversarially verify → **gather all findings (FINDINGS-ONLY)** → merge → phased fixes plan for user approval. NO fixes this round.
`truth_owner = windows`; file-disjoint parallel. Marathon core OFF-LIMITS. Round-14 build-source dims + round-15 D1–D9 are `DEFERRED_BY_DESIGN` (do NOT re-litigate).

## Status: ▶ WIN LANE RUNNING (2026-06-27) — engine (wf_571060b9-289) in flight; build-free gates authored + producing findings; full-catalog build sweep staged for a fresh session (RAM-heavy seam, per user).

## Findings (filled as the run surfaces them)

| # | dim | sev | source | finding / defect class | file:line or artifact | status |
|---|-----|-----|--------|------------------------|-----------------------|--------|
| F1 | cross-product / options-completeness | high | harness (`audit_cross_product`) | **`computer` ORPHAN reader target** — `/customize` offers 💻 Computer (`customize.py:534`) and `apply_target_override` accepts `computer` (it's in `TARGET_READERS`, `build_edition.py:1977`), but there is **no `FORMAT_MATRIX` row** for it → it builds as a silent alias of `everywhere` with no catalog asset, no colour fan-out, no test. | `build_edition.py:1977` (TARGET_READERS) · `build_edition.py:2034` (FORMAT_MATRIX, 5 rows) · `scripts/templates/customize.py:534` | ✅ CONFIRMED (gate `dev/audit_cross_product.py` FAIL; deterministic, build-free) |
| F2 | options-completeness | low-med | harness (`audit_customize_completeness`) | **`verse_marker_glyph` ORPHAN /customize field** — a text input (`customize.py`, max 4 chars) that is schema'd (`validate_schemas.py:229`), validated (`api/editions.py` EDITABLE_TEXT_FIELDS), and echoed back to the UI (`web_editions.py:419`), but is **READ by nothing on the build/cover path** (build_edition / matter_pages / core / generate_edition_covers all have zero consumers) → the control does nothing. | `scripts/validate_schemas.py:229` · `scripts/web_editions.py:419` · (no consumer) | ✅ CONFIRMED (gate `dev/audit_customize_completeness.py` FAIL; re-verified across whole tree). Fix options: wire it to the verse-marker render, or retire the field. |

**Seed verifications (scoping seeds confirmed NON-defects — the code already handles them; logged so they are not re-raised):**
- Seed #2 *kindle declared≠built* — `FORMAT_MATRIX` kindle row carries `post_process: kindle_safe` and `base_build_target` correctly returns `everywhere`; `audit_cross_product` check 2 PASSES → **not a defect** (the declared/built divergence is explicit + handled).
- Seed #3 *standalone target degeneracy* — `apply_target_override` raises `ValueError` on both standalone editions; they are excluded from `standard_edition_ids()`; `audit_cross_product` check 4 PASSES → **not a defect** (correct by design).
- Grid integrity: 4 catalog editions × 5 format cells × 5 colours = **100** expected catalog assets (+2 standalones = the 102 the scoping pass enumerated); no dup cell ids; no dup asset names.

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
- **2026-06-27 WIN lane RUN (this session)** — bootstrap + env-health (CommitFree ~50 GB, no AppXSvc leak; tree clean; in sync both remotes) + `git pull --rebase` (up to date). Flipped local `LANE='win'` (NOT committed; revert before push). Launched the engine `Workflow` `wf_571060b9-289` (LANE=win, ROUND=16, 11 dims, feature-dev agents; confirmed running with the WIN repo path + DEFERRED fed). **Authored 3 gates (ruff-clean, selftests pass):**
  - `dev/audit_output_hygiene.py` — R16 headline merged artifact scanner (families A html-integrity/code-leak [NEW] · B whitespace/pagebreak [reuses `audit_spine_breaks`] · C display-redundancy · D orphan-aside marker-logic). `--selftest` PASS (9 leak hits on dirty / 0 on clean; nested-`<a>` detected).
  - `dev/audit_cross_product.py` — R16 build-free dim-4 gate → **surfaced F1 (`computer` orphan)**; checks 1/2/4/5 PASS (seeds #2/#3 = non-defects). `--selftest` PASS.
  - `dev/round16_build_inspect.py` — the full-catalog build-inspect harness driver (RAM-safe ladder; flagship eink LAST+SOLO w/ CommitFree pre-flight; incremental JSON; per-asset scan suite). Ruff+parse clean; smoke-test (catholic-study:everywhere) RUNNING.
  - In flight: Explore recon of `/customize` field-wiring (for `audit_customize_completeness.py`, dim 9). **Heavy full-catalog build sweep + final merge staged for a FRESH session** (user-directed RAM seam).
