# Agent work backlog — pending-work queue

> A plain list of non-blocked next-work items (pick the next when a lane frees). The
> anti-idle / auto-replan **radar was removed 2026-06-20** (runaway-loop cleanup) — this is
> now a manual backlog, not an "always-on / never-idle" engine. **Periodically step back**
> and re-read PLAN + release gate + queues and reorder when priorities shift; that judgment
> is the agent's, not a radar's.

## P4 — release gate slice (turn 145, WIN builds · Mac verifies)

> **Operating model:** `MAC_WORK_QUEUE.md` §WIN builds · Mac scopes + verifies. Handoff @ `091a3f14`.

- [x] WIN: ci pytest triage — turn 144 (`pytest --lf` 9/9 · edition_stats cross-check PASS)
- [ ] MAC: Verify turn 144 ci triage on pull (pytest + `lint_rules` per CHANGELOG) → `LANE_HANDOFF` verify block
- [x] WIN: M2 Apple audit — K-R5-3 · justify · Easton dedup (`LANE_HANDOFF` §user-fail) — gate scoped to real bleed + pure singletons; fixes (left-align, dict-* strip, boundary clamp) landed+confirmed; sim scope satisfied; device nav/justify separate from this gate. Mac loop root noted in LANE.
- [ ] WIN: Kindle STK glossary bisect vs `143407Z` — one candidate m4b
- [ ] MAC: Verify M2 tablet artifact + Kindle m4b after WIN pushes (no dual code fixes)
- [ ] **HOLD:** rx-surfaces · Kobo `--sim` · sim audit · catalog · overflow

## Recurring CHECKS (agent-run at seams, not daemonized)
- [ ] Relaxed audit (more often): run `audit.py --category D`, `dev/verify_kr2_build.py` on current/clean artifacts; small verifs after slices / rule / Mac updates / 5+ commits. Run post-work at a seam.
- [ ] Deep audit (less often): the deep-audit dims (redundancy / contradiction / optimization / automation-safety), after 15+ commits / 24h / milestones. Use findings in `_audit-split/`.
- [ ] Check in on Mac (WIN, on Mac-handoff): after a significant WIN slice (build/core/rule), append a `## Mac verify` block in LANE_HANDOFF with exact cmds for Mac (build, pytest, D/kr2, re-cut progress), update IN_FLIGHT, save-all push; Mac does prep/audit/verify + reports.
- [ ] Rotate cadence (every so often): `py -3 scripts/rotate_truth_records.py --apply --keep 2` (tied to audits/saves). Never batch without.
- [ ] After a Mac rule/parity update lands: advance to the next §3-sequenced item, or stop clean if the session's real work is done (no auto-continue). After a rule-change: send the Mac block FIRST with the full rules, then continue.

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