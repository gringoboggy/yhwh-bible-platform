# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->

> **▶ ACTIVE (turn 146 handoff @ `27bc6cdc`, 2026-06-20).** **ci triage DONE** (turn 144). **Deep round-9 audit EXECUTING** (post auto-pull/parity phase; Mac prep first via MAC_WORK_QUEUE + LANE_HANDOFF). Latest save landed (exit 0). State: clean + fully synced. WIN executed: doc drift fixes (editions→6, kinds→68, notes 91,597), D1 scanner improved (cross-file only), automation-safety fixes (lane_watch rebase abort, save-all drives non-fatal, save_mac rotation parity), Mac prep moved into ## Active queue for auto-assign, subagents for redund/contradict/automation-safety/optimizations-everywhere (5 safe plans logged). Major defect found: 64,930 K-R6-2 fails in v0.1.0.kepub (widespread bare ids, 851 rev). Findings + plans in _audit-split/round9-win-initial-findings.md. **WIN 2026-06-20:** M2 Apple audit inspection complete (fixes already in tree). Deep audit: Opt #1 (single filter data pass) wired + de-dupe; Opt #2: css single-pass + post-badge html repairs (eink/empty/vnote/tablet) now single load + in-mem transforms via preloaded dict support in the 4 apply fns + batch write (1 I/O cycle vs 4). Gated clean. Opt #3: early-out for per-verse split work in build_one when no split/eink (added guard before badge call). Gated clean (reformatted). Strengthened rule parity STANDING: system for Mac to mirror/confirm/ACK any rule change (delegated via queue). Mac verify instructions + rule mirror task in queue/LANE_HANDOFF. D1 now INFO for by-design. **For new session:** pull, read triad + updated findings/IN_FLIGHT/LANE_HANDOFF, continue Win (safe impl of remaining opts, automation-safety), Mac: run prep list + verify section + mirror/confirm rules. **HOLD:** full M2 QA + M4 · overflow.

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via the Esther vision lane.

## Background backlog (HOLD until release-gate #1–2)

> Overflow frozen per focus reset: Esther Patrologia · CAM pre-pull · website/dist regen · full `ci.py` re-run. Resume via `AGENT_WORK_BACKLOG.md` P4 only after M2 + Kindle bisect land.