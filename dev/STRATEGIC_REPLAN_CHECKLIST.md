# Strategic replan checklist — big step back (STANDING)

> **When to run:** `py -3 scripts/agent_idle_radar.py --replan` surfaces this automatically
> when due (15+ commits · 24h elapsed · PLAN/release-plan changed · major scope drift).
> **Mark done:** `--replan-done --note "summary"`. Replan is work — never idle after it;
> immediately resume highest-priority execution item.

## 1 — Orient (read, do not grep-blind)

- [ ] `dev/PLAN_2026-05-29-roadmap.md` — still the right forward sequence?
- [ ] `docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md` §8 — release gate blockers
- [ ] `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` — tracker matches reality?
- [ ] `dev/AGENT_WORK_BACKLOG.md` + `dev/MAC_WORK_QUEUE.md` — priorities still optimal?

## 2 — Inventory what's left (gigantic project sanity pass)

- [ ] **Release gate:** ci.py GREEN · reader-sim layers · rx-surfaces · audits · tag blockers
- [ ] **Phase D:** Esther/Patrologia transcription lanes · remaining OT books
- [ ] **Samuel/Kings:** manifest gaps · CAM folios · collation at-scale
- [ ] **Website/dist:** catalog columns · deploy drift
- [ ] **Tech debt:** open lint warns · stale plans · archive hygiene

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