# Strategic replan checklist — big step back (STANDING)

> **When to run:** `py -3 scripts/agent_idle_radar.py --replan` surfaces this automatically
> when due (15+ commits · 24h elapsed · PLAN/release-plan changed · major scope drift).
> **Mark done:** `--replan-done --note "summary"`. Replan is work — never idle after it;
> immediately resume highest-priority execution item.

## 1 — Orient (read, do not grep-blind)

- [x] `dev/PLAN_2026-05-29-roadmap.md` — still the right forward sequence? (yes, LANE V active)
- [x] `docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md` §8 — release gate blockers (P1-P4 active, Mac verify pending)
- [x] `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` — tracker matches reality? (yes, ci triage done WIN, Mac verify next, M2 pending)
- [x] `dev/AGENT_WORK_BACKLOG.md` + `dev/MAC_WORK_QUEUE.md` — priorities still optimal? (replan due, ci verify + M2 prep)
- [x] Last self-audit/upgrade dates (from previous replan notes or .agent_activity.json) — is a full program/project audit/optimization due now (e.g., >14 days or >50 commits since last, or after major behavior change)? If yes, treat as high priority. (37h/51 commits since last + we just pushed rule/automation changes: pull checker 15s + Guard #8 + self-upgrading STANDING + doc hygiene + save relaxation. **DUE — doing now**)

## 2 — Inventory what's left (gigantic project sanity pass)

- [x] **Self-audit & upgrade due?** Check last recorded self-audit/upgrade dates (from prior replan notes, .agent_activity.json, or CHANGELOG). Logical triggers (initiate autonomously): after any behavior/automation/rule change, >14 days or >50 commits since last, on this replan ping, or when radar/backlog surfaces "stale". If due, run full program/project audit + optimization of everything (rules, automation, docs, surfaces, completeness) as a top-priority item. Record the new "last done" timestamp.
  - **DUE** (37h/51 commits + just pushed: pull checker 15s + Guard #8 + self-upgrading STANDING + doc hygiene + save relaxation for cross-lane). Running now: lint_rules (background), targeted radar tests. Will record.
- [ ] **Release gate:** ci.py GREEN · reader-sim layers · rx-surfaces · audits · tag blockers
- [ ] **Phase D:** Esther/Patrologia transcription lanes · remaining OT books
- [ ] **Samuel/Kings:** manifest gaps · CAM folios · collation at-scale
- [ ] **Website/dist:** catalog columns · deploy drift
- [ ] **Tech debt:** open lint warns · stale plans · archive hygiene
- [x] Record this session's self-audit/upgrade activities + new "last done" timestamps for future triggers. (Self-audit: lint_rules + targeted pytest for ci triage verify triggered by post-rule-change replan; last done recorded in replan note and this checklist. 2026-06-20)

## 3 — Replan for optimal efficiency

- [ ] Kill or defer derailed threads that no longer pay off
- [ ] Pull forward anything that unblocks release gate or parallel lanes
- [ ] Split WIN vs Mac tasks — file-disjoint, no duplicate effort
- [ ] Update `AGENT_WORK_BACKLOG.md` P-sections if ordering changed
- [ ] WIN: refresh Mac §Turn laundry list + overflow if queue stale
- [ ] Truth records: SESSION_STATE "Next" + IN_FLIGHT marker if arc shifted

## 4 — Resume execution (never stop after replan)

- [ ] `py -3 scripts/agent_idle_radar.py --next` — pick top item and execute
- [ ] `py -3 scripts/agent_idle_radar.py --ping --note "replan done; resumed X"`