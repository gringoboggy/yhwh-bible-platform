# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

> **Last arc CLOSED (2026-06-21): the Grok-revert cleanup — DONE + pushed** (4 commits →
> GitLab + GitHub + E: + F:, HEAD `b45a9ff1`). Loop machinery removed, rules/docs de-bloated,
> truth records reconstructed, **115 notes + 4 kinds restored** (corpus 91,712), editions junk
> fixed. Bible verified intact. Rollback branch `pre-grok-cleanup-snapshot`. Details:
> `dev/CHANGELOG.md` (2026-06-21) + memory `project_grok_cleanup` (task `ww7ughmf7`).

## ▶ Fresh session — continue "the rest" (priority order)

1. **Integrate MacClaude's byte-stability verify.** Read `dev/LANE_HANDOFF.md` for Mac's PASS/FAIL
   report on Grok's `Opt#` build slices. If Mac flags **`Opt#3` (`33b79387`, tablet/Apple
   badge-collapse early-out)** as changing build output → `git revert 33b79387` (or surgical) +
   add a regression test pinning tablet badge-collapse; if byte-identical → keep. Same call for
   `Opt#2` nav.xhtml bilingual leg + the repair batch. (Mac gets this task from its `MAC_WORK_QUEUE`
   on pull.)
2. **Reconcile the catalog counts** once Mac's rebuild gives exact per-edition figures — the **+72
   restored `comm`/`word` notes** shift the shipped numbers. Sweep the full count cascade (page
   bodies · `<meta>`/og/twitter · social-card image · GitHub/GitLab descriptions · EPUB metadata ·
   in-app trackers) per memory `feedback_deploy_means_build_and_deploy`.
3. **Refresh `.claude/workflows/deep-audit.js`** Grok-era dims (the `CROSS_LANE_RULES_PARITY_PLAN` /
   round-9 / "always make Mac do prep" references are stale) — before the next deep-audit run.
4. **Resume the v1.0.0 release gate** (`docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`):
   WIN = M2 Apple audit (K-R5-3) · Kindle STK device bisect; Mac verifies. See `dev/SESSION_STATE.md`.

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done
> for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) via the Esther vision lane.
