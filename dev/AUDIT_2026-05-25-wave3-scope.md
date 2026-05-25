# Light post-Wave-3 audit — scope & checklist (run after the /clear)

**Created 2026-05-25**, at the close of **Wave 3 (EPUB Presentation Phase 2)**.
This is the **light solo-Claude audit** (memory `audit_cadence`: proactively
suggest after a major arc closes ≥10 units) — **NOT** the heavy parallel-subagent
sweep. Wave 3 shipped 3 infra prereqs + 7 features across 5 commits
(`25e22cf` → … → the prep commit), with ~60 new tests. Confirm the tree is
clean, the gates are green from scratch, and nothing drifted.

## 0. Bootstrap (as always)
Read `dev/CLAUDE_PROJECT_RULES.md` → `dev/SESSION_STATE.md` → `dev/PLAN_2026-05-24-end-scope.md` first.

## A. Clean state + verification gates (run from scratch)
- [ ] `git status` clean — everything committed; note HEAD.
- [ ] E:/F: backup current (a `--all` bundle at the audited HEAD exists on both `…/YHWH-v2.4-backups/`).
- [ ] `python -m scripts.lint_rules` → **16/0/0**.
- [ ] `python -m ruff format --check .` → clean.
- [ ] `ebible verify` → **errors=0**; `validate_taxonomy` → 100%; `trace_matrix` → 0 unresolved; `trace_repo` → 0.
- [ ] epubcheck **0/0** on a representative set: flagship `ethiopian-tewahedo`, a filtered `catholic-study`, and a small-canon edition (e.g. `jewish-study`, tanakh — exercises canon-filtered popups + topical index).
- [ ] Test sweep: `test_scripts.py` + `test_core.py` + the Wave-3 files (`test_resync_markers`, `test_marker_glyphs`, `test_marker_style`, `test_popup_witnesses`, `test_topical_index`, `test_presentation_polish`). Confirm count incl. the ~60 new tests; **re-confirm the `test_popup_witnesses::TestOptInWitnessesStillAvailable::test_jps_…` transient (it errored once in a full sweep, passed clean on re-run) is NOT a real isolation bug** — if it recurs, harden it.

## B. Wave-3 currency (the likely drift points)
- [ ] **`dev/MATRIX_MAP.md`** — prereq #1 added the popup-STYLE enum settings, but the LATER features may need entries: (a) #6 popup-witness default drop-kjv + `DEFAULT_POPUP_WITNESSES` + the **KJV-floor fallback** in `_apply_popup_languages_and_translation`; (b) #7 the topical-index back-matter page + the `naves_topical` source + `inject_back_matter`'s new `canon_books` param + the build-time **per-edition marker renumber** post-pass in `build_one`. Add any missing data-flows (self-upgrading-matrix rule).
- [ ] **`marker_style`** is a *declarative* field (only `numbers` valid; `badge` DEFERRED, injection point TBD). Confirm the deferral is tracked (spec §4.1 / plan) and the disabled `badge (coming soon)` `/customize` option is intended.
- [ ] **KJV-floor fallback** — keeping English where no original-language witness exists *deviates* from the strict spec §4.3 ("kjv removed from popups"). It's documented in CHANGELOG + SESSION_STATE; decide whether the design spec (`docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md` §4.3/§12.3) should note it too.
- [ ] **Dead code** (vulture): is `ALL_POPUP_LANGUAGES` still referenced now that the unset fallback returns `DEFAULT_POPUP_WITNESSES`? Any orphaned popup-witness machinery?
- [ ] **`dev/REPO_MAP.md`** — new files this wave: `scripts/categorize_diff.py` + `tests/{test_resync_markers,test_marker_style,test_popup_witnesses,test_topical_index}.py`. Confirm `repo_map_complete` still passes (it did at each commit; re-verify).

## C. Loose ends / [USER] items
- [ ] **[USER] device eyeball** (reader-only behaviors): inline footnote numbers · in-note category symbol + its legend tap-through · widened popups (Hebrew/Greek/Latin/Arabic, no English where originals exist) · the topical index — on Apple Books / e-ink.
- [ ] EPUB size sanity: the topical index added ~0.26 MB compressed (flagship ~23.9 MB). Confirm acceptable; the topical page is the heaviest single XHTML (~1.2 MB uncompressed, 4,604 topics).
- [ ] **`dev/PLAN_2026-05-24-end-scope.md`** — mark Wave 3 DONE; confirm Wave 4 (productionization → downloadable desktop app) is the next active wave.

## D. Output
Write a brief `dev/AUDIT_2026-05-25-wave3-FINDINGS.md` (light) — verdict + any
issues — and **fix safe issues in-session** (the self-upgrading-matrix + "defect
found ≠ defect prevented" rules). Then update SESSION_STATE to point at Wave 4
(or whatever the audit surfaces).
