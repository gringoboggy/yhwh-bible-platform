# Agent work backlog — always-on queue (never idle)

> **STANDING (2026-06-18):** The agent must NEVER wait for user input. If blocked on
> one task, pick the next item here or run `py -3 scripts/agent_idle_radar.py --next`.
> User will ask when they have something for you. Ping heartbeat after each slice:
> `py -3 scripts/agent_idle_radar.py --ping --note "what you just did"`.
>
> **Strategic replan (STANDING):** Periodically step back and re-read PLAN + release
> gate + queues — reorder for optimal efficiency when derailed or scope shifts.
> Radar auto-pings when due (15+ commits · 24h · PLAN changed). Checklist:
> `dev/STRATEGIC_REPLAN_CHECKLIST.md` · `py -3 scripts/agent_idle_radar.py --replan`.

## P3 — strategic replan (when radar pings — then resume execution)

- [ ] BOTH: Run `agent_idle_radar.py --replan` — read PLAN + release-plan §8 + SESSION_STATE + both queues
- [ ] BOTH: Reorder P5–P20 items if priorities shifted; refresh Mac laundry list if stale
- [ ] BOTH: `--replan-done --note "…"` then immediately `--next` and execute top item

## P4 — release gate slice (turn 142, user-directed FOCUS RESET)

> **One vertical slice.** Finish `#1` before touching overflow. Mac: **no Kindle code / STK / catalog** until WIN bisect lands.

- [ ] WIN: `ci.py` GREEN — **RUNNING** (started 2026-06-19 ~14:07); do not start second full run; triage reds when done
- [ ] WIN: Kindle STK glossary bisect vs `143407Z` (390 spine / 0 glossary) — one candidate m4b
- [ ] MAC: Mirror turn 141 scrub (lint · Desktop QA purge · website deploy if skew)
- [ ] MAC: Apple + Play sim depth only (M2/M5 matrix rows in platform notes)
- [ ] **HOLD until ci green + STK bisect:** rx-surfaces · Kobo `--sim` · sim-pipeline audit · `ci.py --reader-sim-gates`
- [ ] **HOLD Mac:** STK uploads · Kindle code · M4 catalog · Esther/CAM/1ki overflow

## P5 — release gate (WIN primary)

- [ ] WIN: pytest `--lf` → fix reds → `py -3 scripts/ci.py` GREEN
- [ ] WIN: Update `dev/reader_sim/STAGING_MANIFEST.md` SIM_LAYERS after sim passes
- [ ] BOTH: dishonest-code-audit + stub-audit before v1 tag (when RAM free)

## P8 — reader sim depth (folded into P4 day plan)

- [ ] WIN: Build fresh ethiopian-tewahedo eink kepub if staged artifact stale
- [ ] MAC: Thorium CDP tap calibration on catholic-study tablet build
- [ ] MAC: Play Books emulator spot-check one edition

## P10 — transcription side lanes (parallel, file-disjoint)

- [ ] MAC: Esther Patrologia OCR resume — `extract_patrologia_pdf --book est` (~p35+)
- [ ] WIN: Esther vision lane page tiles when GAPS PDF pages available on WIN
- [ ] MAC: CAM hi-res folio pre-pull for pending samkings chapters (manifest gaps)
- [ ] BOTH: 1ki EN back-translation ch11+ continuation (disjoint from pytest)

## P12 — website + release surfaces

- [ ] BOTH: `gen_release_catalog` + `node website/build.mjs` if catalog stale
- [ ] MAC: Deploy `yhwh-website` if dist column changed
- [ ] WIN: Release bundle SHA256SUMS audit vs GitHub assets

## P15 — audit cadence

- [ ] BOTH: LIGHT audit after every 10 shipped slices or 150 test-count drift
- [ ] BOTH: DEEP audit after 25+ commits or major pipeline touch (build_edition, inject, editions.yaml)
- [ ] BOTH: `dishonest-code-audit` before v1.0.0 tag

## P20 — overflow (when primary queue clears)

- [ ] MAC: M4b 6-variant re-gate after kindle_post.py touch
- [ ] MAC: evangelical-reformed tablet spot-build (category-color popups)
- [ ] WIN: Phase 4 disjoint notes in `content/notes/aes.py`
- [ ] BOTH: Archive sweep `scripts/_*.py` one-shots → `dev/archive/`
- [ ] MAC: Platform matrix close remaining M5/M3 rows in implementation matrix doc