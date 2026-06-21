# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->

> **▶ ACTIVE (2026-06-21, 🪟 Windows) — Grok-revert surgical cleanup (finishing).** For ~2 weeks
> (June 10–20) a different agent ("Grok") degenerated into a self-perpetuating "NEVER-STOP" loop —
> the auto-continue loop was architecturally impossible (an external poll can't drive an agent), so
> it kept "fixing" a ghost. The **Bible product is intact** (verse counts + reading order verified
> unchanged from the June-9 baseline `3065b348`). Surgical revert — **NO git-history rewrite**;
> rollback branch `pre-grok-cleanup-snapshot`. **3 local commits, nothing pushed.**
>
> **Done (committed):** killed the loop machinery (radars, EXTRA-STEP, rotate-churn) + restored
> bootstrap + refreshed the installed hook; de-bloated RULES/AGENTS/PLAYBOOK/LANE_HANDOFF (guards
> #8–#10, the §0 self-upgrade/"you already have all the answers", NEVER-STOP, 36× AUDIT-PROTOCOL
> spam — genuine doctrine kept, auto-pull now seam-based); reconstructed IN_FLIGHT/SESSION_STATE/
> LANE_HANDOFF/CHANGELOG; restored the **115 notes + 4 kinds** the June-18 scrub pruned (corpus
> **91,712**, 72 kinds; baked into base HTML, `ebible verify` errors=0); fixed editions.yaml
> `DEDICATION_SENTINEL_42` junk + registered the real `dedication` field. lint_rules green; all 6
> configs strict-clean.
>
> **Doing:** final residue sweep — deleted the orphaned `STRATEGIC_REPLAN_CHECKLIST` + trimmed the
> backlog P3 (the removed `--replan` mechanism).
>
> **Next:** present the full diff for the **user-gated GitLab push**. On push, MacClaude pulls its
> tasks (LANE_HANDOFF + MAC_WORK_QUEUE): **byte-stability rebuild-verify** of Grok's Opt# build
> slices (esp. Opt#3 `33b79387` tablet/Apple badge → REVERT if output differs) + rebuild the
> catalog for the new shipped counts (the +72 comm/word notes shift them) → reconcile the count
> cascade. **Deferred:** refresh `.claude/workflows/deep-audit.js` Grok-era dims when next run;
> tidy the mislabeled notarization commit-split. Plan: task `ww7ughmf7`; memory `project_grok_cleanup`.

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation
> done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via
> the Esther vision lane.

## Background backlog (resumes after the cleanup)

> Real release-gate work resumes once the cleanup lands: **M2 Apple audit** (K-R5-3) · **Kindle
> STK device bisect** · **M3 Kobo** (kepub + user taps) · then `dev/PLAN_2026-05-29-roadmap.md`
> LANE D/M/P/T. Overflow (Esther Patrologia · CAM pre-pull · website/dist regen) stays HOLD
> until the release gate.
