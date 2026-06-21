# Mac work queue — operating model + current Mac scope

> **Lane-coordination-v2: WIN builds · Mac verifies + scopes** (RULES §4 + `dev/LANE_HANDOFF.md`
> STANDING). WIN owns implementation (`scripts/` · `tests/` · `ci.py` · matrix builds · Kindle
> bisect). On each WIN milestone, Mac: pull → run the WIN-listed verify commands → post PASS/FAIL
> in `dev/LANE_HANDOFF.md` → keep ≤3 next-scope items here. Mac must **not** dual-implement a fix
> WIN is shipping; Mac **may** run targeted `pytest` + sim gates + STK poll (user uploads); Mac
> must **not** run a full `ci.py` on the HDD while WIN's `ci.py` is in flight.

## Current scope (Mac) — max 3

1. **On the Grok-revert cleanup commit:** byte-stability **rebuild-verify** the Opt# build slices —
   build the 4 catalog editions at BASE `3065b348` vs the cleanup HEAD across targets and byte-diff.
   Make-or-break = Opt#3 (`33b79387`) tablet/Apple badge-collapse early-out (**REVERT** if the
   tablet artifact differs). Also Opt#2 `nav.xhtml` bilingual leg + the repair batch. Report
   PASS/FAIL + `file:line` in `dev/LANE_HANDOFF.md`. (No full pytest on the 8 GB box.)
2. **Mirror the de-bloated rules** into Mac per-box memory + ACK (rule-change parity): the radar /
   NEVER-STOP / "you already have all the answers" machinery was removed 2026-06-20; auto-pull is
   now seam-based. Confirm Mac rules identical (diff only real OS reasons).
3. After the cleanup lands: resume **M2 Apple audit** verify + **Kindle STK** device checks per the
   release gate (`dev/SESSION_STATE.md`).
