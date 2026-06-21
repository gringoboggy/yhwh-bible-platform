# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

> **Last arc CLOSED (2026-06-21): the Grok-revert cleanup — DONE + pushed** (4 commits →
> GitLab + GitHub + E: + F:, HEAD `b45a9ff1`). Loop machinery removed, rules/docs de-bloated,
> truth records reconstructed, **115 notes + 4 kinds restored** (corpus 91,712), editions junk
> fixed. Bible verified intact. Rollback branch `pre-grok-cleanup-snapshot`. Details:
> `dev/CHANGELOG.md` (2026-06-21) + memory `project_grok_cleanup` (task `ww7ughmf7`).
>
> **Mac follow-up DONE (2026-06-21):** the Mac-local Grok footprint is also removed — `~/.grok`
> CLI (1.2 GB → Trash), `~/.config/kilo/`, the `~/.zshrc` PATH block, repo `.grok/` + orphaned
> loop logs, and the tracked `.vscode/extensions.json` + `TOOLCHAIN.md §Grok` (now a decommission
> note). Cover-art Grok-image feature preserved. Claude is the sole coding agent.

## ▶ Fresh session — continue "the rest" (priority order)

1. **MacClaude byte-stability verify — DONE (2026-06-21).** **Opt#3 (`33b79387`) changed build output**
   → **REVERTED.** It skipped `apply_badge_markers` for tablet / any `reader_file_split:false` edition,
   so raw per-note `note-ref` markers leaked and badges were dropped; the *existing*
   `TestBadgeBuildIntegration::test_badge_build_has_badges_no_per_note_markers` went **red** on the Opt#3
   tree (real build). Added an explicit `test_tablet_badge_build_applies_badges` pin. **Opt#2 / #4 / #5
   byte-neutral → kept** (in-mem preload equivalence · `_list_temp_files`=`sorted(glob)` · pure-fn
   `@lru_cache`). Full verdict + evidence: `dev/LANE_HANDOFF.md` "Mac verify (2026-06-21)". Green
   re-verify PASS (2/2: the formerly-red badge integration test + the new tablet pin; 62 unit tests green).
2. **Reconcile the catalog counts** once Mac's rebuild gives exact per-edition figures — the **+72
   restored `comm`/`word` notes** shift the shipped numbers. Sweep the full count cascade (page
   bodies · `<meta>`/og/twitter · social-card image · GitHub/GitLab descriptions · EPUB metadata ·
   in-app trackers) per memory `feedback_deploy_means_build_and_deploy`.
3. ✅ **DONE (2026-06-21) — refreshed `.claude/workflows/deep-audit.js`:** dropped the Grok "round 9
   ridiculously deep" 9-dim block + every `CROSS_LANE_RULES_PARITY_PLAN` ref (file deleted in cleanup)
   + the "always make Mac do prep" directive; reset the deferred-list to genuine product residuals;
   bumped ROUND 9→10 / NOW 2026-06-21; added a `SCOPE='product'` default that ENFORCES the user
   "round 8+ = product-only" directive in code (round-7 sweep dims gated behind `scope='all'`).
   24 product dims; lane-coverage + wrapped-parse verified. The next audit run can launch once the
   tree is stable (after tasks 1–2).
4. **Resume the v1.0.0 release gate** (`docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`):
   WIN = M2 Apple audit (K-R5-3) · Kindle STK device bisect; Mac verifies. See `dev/SESSION_STATE.md`.

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done
> for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) via the Esther vision lane.
