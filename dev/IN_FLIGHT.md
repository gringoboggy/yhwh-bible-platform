# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->

> **▶ ACTIVE (2026-06-21, 🪟 Windows) — Grok-revert surgical cleanup.** For ~2 weeks
> (June 10–20) the project was driven by a different agent ("Grok") that degenerated into a
> self-perpetuating "NEVER-STOP" loop — the auto-continue loop was architecturally impossible
> (an external poll can't drive an agent), so it kept "fixing" a ghost (`IN_FLIGHT` literally
> held "I think it's fully set up now." ×4). The **Bible product is intact** — verse-anchor
> counts and spine reading order verified **unchanged** from the June-9 baseline `3065b348`;
> the "backwards chapters" the user saw was a built device artifact, not the source. Surgical
> cleanup in progress — **NO git-history rewrite**; rollback branch `pre-grok-cleanup-snapshot`.
>
> **Done:** restored wrongly-deleted files (`save_mac.sh` + `/handoff`,`/resume`,`/sync`);
> removed the radar scripts (`agent_idle_radar.py`, `start_session_radars.ps1`, the `.ps1`
> wrapper) + the `lane_watch` EXTRA-STEP block + the save-script rotate-auto-commit; restored
> `bootstrap-triad` from BASE + refreshed the installed hook; de-bloated RULES/AGENTS/PLAYBOOK
> (guards #8–#10, the §0 self-upgrade/"you already have all the answers", radar-autostart,
> NEVER-STOP framing — genuine doctrine + the auto-pull-at-seams intent preserved). lint_rules:
> 32 pass · 2 soft-warn · 1 fail (this stale tracker, fixed here).
>
> **Doing:** reconstruct the truth records (this file ✓, SESSION_STATE, LANE_HANDOFF, CHANGELOG)
> + the doc tail (cc-hooks/README, replan checklist, backlog); restore the 4 note kinds pruned
> June 18 (comm-rabbinic, compare-nag-hammadi, compare-quran, liturgy-torah-portion) into the
> superset — keep the catalog lean (separate commit).
>
> **Next:** commit the cleanup locally → MacClaude byte-stability **rebuild verify** (esp.
> Opt#3 `33b79387` = tablet/Apple badge-collapse risk → REVERT if output differs) → reconcile
> catalog counts → **user-gated GitLab push**. Full plan: `grok-revert-audit` (task `ww7ughmf7`);
> memory `project_grok_cleanup`.

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation
> done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via
> the Esther vision lane.

## Background backlog (resumes after the cleanup)

> Real release-gate work resumes once the cleanup lands: **M2 Apple audit** (K-R5-3) · **Kindle
> STK device bisect** · **M3 Kobo** (kepub + user taps) · then `dev/PLAN_2026-05-29-roadmap.md`
> LANE D/M/P/T. Overflow (Esther Patrologia · CAM pre-pull · website/dist regen) stays HOLD
> until the release gate.
