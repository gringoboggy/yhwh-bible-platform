# dev/archive — superseded docs

Preserved for historical reference. Active docs are in `dev/`.

| File                         | Was                            | Superseded by                                       |
|------------------------------|--------------------------------|-----------------------------------------------------|
| HANDOFF_NEW_THREAD.md        | v28a-50.1 fresh-Claude doc     | `dev/SESSION_STATE.md` + `dev/CLAUDE_PROJECT_RULES.md` §0 |
| v28_PLANNING.md              | older planning doc             | `dev/PLAN_2026-05-07.md`                            |
| v28_ROADMAP.md               | older roadmap                  | `dev/SCOPE_2026-05-07-addendum-tooling-roadmap.md`  |
| PHASE_BETA_AUDIT.md          | early audit (post-v28a-6)      | superseded by ongoing audit-tool + ξ.4 console       |
| INJECTOR_DUPLICATION.md      | known-issue tracker            | acknowledged · low-priority                         |

If a doc here turns out to still be live, move it back to the
project root or `dev/`.

---

## 2026-05-30 — mint cleanup Phase 2–3 sweep

The mint-cleanup arc (`docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md`)
retired the superseded master plan plus ~58 dated finished docs into this directory.
The live forward sequence is now `dev/PLAN_2026-05-29-roadmap.md`; the history lives here.
Lint's archive-aware `doc_cross_references` resolves references to these by filename, so
citations elsewhere still resolve — move one back to `dev/` only if it becomes active again.

**Plans / scope (Phase 2):**
- `PLAN_2026-05-24-end-scope.md` — the prior master plan → superseded by `dev/PLAN_2026-05-29-roadmap.md`.
- `SCOPE_2026-05-14-parallel-bible.md` — the popup-era framing → superseded by `SCOPE_2026-05-16-parallel-bible-standalone-bibles.md`.

**Phase-3 sweep (dated finished docs, by family):**
- **Audits** — `AUDIT_2026-05-10` … `AUDIT_2026-05-26` (the daily LIGHT/DEEP/EOD audits + `-samuel-calibration` / `-samuel-widened` / `-inject-tail-residual` / `-smoother-running` / `-wave3-{scope,FINDINGS}` / `-23-DEEP` / `-26-FINDINGS`). Findings folded into the rules, `dev/CHANGELOG.md`, and the roadmap LANE-T backlog.
- **Calibration** — `CALIBRATION_2026-05-16/17/19-{samuel,kings}-*` (the manuscript-marathon calibration template; the method is ratified in the marathon plan + memory).
- **Scope addenda** — `SCOPE_2026-05-07` … `SCOPE_2026-05-16-*` (covers, ops/accelerators, popup-languages, tooling-roadmap, ai-xrefs, audio-epubs, cross-denom-compare, kenyon-textcrit, pd-translations, prettification, robustness, security, textcrit-deep-dive, ai-notes, edition-templates, gamma-4-expansion, xi-18-style-src, the base `SCOPE_2026-05-08.md`, and the parallel-bible standalone-Bibles end-state). Shipped features are logged in `dev/CHANGELOG.md`.
- **Session-end** — `SESSION_END_2026-05-12.md`.
