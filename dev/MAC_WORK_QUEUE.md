# Mac work queue — auto-assigned by WIN lane_watch after each Mac push

**Lane watch (both boxes):** `scripts/lane_watch.py` — one engine for push radar +
remote handoff board + `lane_handoff incoming`. Handoffs only travel after **git push**.

**★ USER DIRECTIVE (2026-06-17): lane_watch ON for the entire pre-human remediation +
Round 9 audit arc on BOTH boxes.** Mac: start `--bg` at session open; do not stop until
the arc completes (unless user says so). WIN runs the matching watcher + optional `-AssignMac`.

| Box | Start (foreground) | Background |
|-----|-------------------|------------|
| **Mac** | `bash dev/lane_watch_mac.sh` | `bash dev/lane_watch_mac.sh --bg` |
| **WIN** | `pwsh -File dev/lane_watch_win.ps1 -LoopSec 120` | `... -Background` |
| **WIN + queue** | add `-AssignMac` to auto-assign from this file after Mac pushes |

WIN polls with `--assign-mac`. On each Mac push it pulls, surfaces incoming, then
assigns the first unchecked line below via `lane_handoff.py assign`.

## Active queue

- [x] **★ Lane watch v3 (REQUIRED whole arc):** `git pull` turn 117+ → `bash dev/lane_watch_mac.sh --once` → `bash dev/lane_watch_mac.sh --bg` — **keep running** through remediation + Round 9 — **Mac turn 118** (`--once` CLEAR post-rebase; `--bg` started)
- [x] **test_samkings_manifest_complete** — 6/6 `done_gate` — **Mac turn 118**
- [ ] **ci.py parity** — full gate after Mac fixes land
- [ ] **website/dist regen** — `gen_release_catalog` + `node website/build.mjs` (pre-human milestone)
- [x] **refactor.py cache invalidation** — **Mac turn 114** (`_invalidate_caches_after_refactor`)
- [x] **inject_book write test** — **Mac turn 114** (`test_inject_write_path.py`)
- [x] **Doc count 91,720 sweep** — **Mac turn 114** + PLAYBOOK @ WIN turn 115
- [x] **Lane watch v3 (initial):** Mac turn 114 (`--once` CLEAR @ df04bab) — re-verify whole-arc @ turn 117+
- [x] Phase 3 LOW: mirror study-glossary nav patch into `toc.ncx` — **Mac turn 111** @ 9a03dad1
- [x] Spot eink build one edition `--target-reader eink` + run `dev/verify_kr2_build.py` on output kepub — **Mac turn 112** catholic-study kepub **ALL K-R2 GATES GREEN**
- [x] M4b Kindle findings-only sketch — **Mac turn 108** + K-R6-2 glossary prefix note @ turn 111
- [x] Tick Phase 3 checkboxes in `docs/superpowers/notes/2026-06-16-round8-split-audit-findings.md` — **Mac turn 111**
- [x] Round-8b THOROUGH re-audit (18 dims, LANE=mac local, Workflow deep-audit.js) — **Mac turn 113** @ lane-transfer/audit (30 survivors, 21 prior refuted)
- [x] M3 attach: 45 kepubs from `m3-kobo-v0.1.0/` handoff → GitHub release + SHA256SUMS merge @ turn 107b
- [x] SHA256SUMS gap: merge 45 Kindle color-variant EPUBs — **WIN turn 112b** (186/186 on `v0.1.0`)
- [x] website/dist rebuild: `gen_release_catalog` + `node website/build.mjs` — **Mac turn 112** (187 assets)
- [x] Phase 4: 3 OOE notes in `content/notes/aes.py` ch10 v11-13 — **Mac turn 108**
- [x] Phase 4: 1ki EN back-translation ch7-10 — **Mac turn 107b**
- [x] Playbook/RULES §4 save-cadence alignment — **Mac turn 114** @ 30d1064f
- [x] Book-code unified resolver (`book_codes.py` + `config.resolve_book_code`) — **Mac turn 114/118** (merged WIN turn 115)
- [x] Round-8 rx-surfaces + popup-integrity tail (deferred LOW/S2 documented) — **Mac turn 114**
- [x] `load_notes_checked` API/pipeline sweep — **Mac turn 114**

## Round 9 queue (after round-8 remediation gate — do NOT start early)

- [ ] **Gate:** pull turn 117+; findings doc 0 open HIGH/MEDIUM; `ci.py` green
- [ ] **Local engine:** `ROUND=9`, `LANE=mac` in `.claude/workflows/deep-audit.js` (never commit)
- [ ] **Workflow:** 22 dims (18 replay + `platform-apple` + `platform-kindle`); Fable 5 thorough
- [ ] **Research briefs:** `notes/2026-06-18-platform-apple.md` + `platform-kindle.md`
- [ ] **Push:** `_audit-split/findings-mac.json` → `lane-transfer/audit`

Plan: `docs/superpowers/plans/2026-06-17-round9-parallel-audit-and-platform-research.md`

## Completed (reference)

- [x] Samuel CAM IIIF acquire — 0 remaining @ turn 110b
- [x] Kings CAM 180 hires @ turn 108