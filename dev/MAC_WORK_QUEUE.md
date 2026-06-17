# Mac work queue — auto-assigned by WIN lane_watcher after each Mac push

WIN polls `scripts/lane_watcher.py --loop 120 --assign-mac`. On each Mac push it
pulls, then assigns the first unchecked line below via `lane_handoff.py assign`.

## Active queue

- [x] Phase 3 LOW: mirror study-glossary nav patch into `toc.ncx` — **Mac turn 111** @ 9a03dad1
- [x] Spot eink build one edition `--target-reader eink` + run `dev/verify_kr2_build.py` on output kepub — **Mac turn 112** catholic-study kepub **ALL K-R2 GATES GREEN**
- [x] M4b Kindle findings-only sketch — **Mac turn 108** + K-R6-2 glossary prefix note @ turn 111
- [x] Tick Phase 3 checkboxes in `docs/superpowers/notes/2026-06-16-round8-split-audit-findings.md` — **Mac turn 111**
- [ ] Round-8b THOROUGH re-audit (18 dims, LANE=mac local, Workflow deep-audit.js) — **★ Mac next** (Phase 1–3 complete)
- [x] M3 attach: 45 kepubs from `m3-kobo-v0.1.0/` handoff → GitHub release + SHA256SUMS merge @ turn 107b
- [x] SHA256SUMS gap: merge 45 Kindle color-variant EPUBs — **WIN turn 112b** (186/186 on `v0.1.0`)
- [x] website/dist rebuild: `gen_release_catalog` + `node website/build.mjs` — **Mac turn 112** (187 assets)
- [x] Phase 4: 3 OOE notes in `content/notes/aes.py` ch10 v11-13 — **Mac turn 108**
- [x] Phase 4: 1ki EN back-translation ch7-10 — **Mac turn 107b**

## Completed (reference)

- [x] Samuel CAM IIIF acquire — 0 remaining @ turn 110b
- [x] Kings CAM 180 hires @ turn 108