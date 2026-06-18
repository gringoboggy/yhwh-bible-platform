# Mac work queue — auto-assigned by WIN lane_watch after each Mac push

**Lane watch (both boxes):** `scripts/lane_watch.py` — one engine for push radar +
remote handoff board + `lane_handoff incoming`. Handoffs only travel after **git push**.

**★ USER DIRECTIVE (2026-06-17): lane_watch ON for the entire pre-human remediation +
Round 9 audit arc on BOTH boxes.** Mac: start `--bg` at session open; do not stop until
the arc completes (unless user says so). WIN runs the matching watcher + optional `-AssignMac`.

**★ USER DIRECTIVE (2026-06-17): commit + save often — no asking, no waiting on input.**
After each coherent slice: local-commit micro-edits, then `bash dev/save_mac.sh -m "…"`
(radar-gated full save). Never pause for confirmation. Never end a session with unpushed
commits; handoff edits MUST be saved immediately.

**★ USER DIRECTIVE (2026-06-18, STANDING — both lanes, Mac MUST mirror to memory):**
Full standing authority on this project — commit, push, pull, build, deploy, install tools,
change any repo/website surface. **Never ask the user** whether to continue, save, install,
or finish logical next steps. **Never idle** — if blocked, `python3 scripts/agent_idle_radar.py --next`.
If the lane is on, keep working. **WIN assigns Mac a fresh laundry list whenever Mac queue clears**
(primary + overflow). **Bootstrap auto-starts BOTH radars every session:**
`bash dev/start_session_radars_mac.sh` (lane_watch 60s + agent_idle_radar 120s).

| Box | Start (foreground) | Background |
|-----|-------------------|------------|
| **Mac** | `bash dev/lane_watch_mac.sh` | `bash dev/lane_watch_mac.sh --bg` |
| **WIN** | `pwsh -File dev/lane_watch_win.ps1 -LoopSec 60 -AssignMac` | `... -Background` |
| **WIN + queue** | `-AssignMac` auto-assigns from this file after each Mac push |

WIN polls with `--assign-mac`. On each Mac push it pulls, surfaces incoming, then
assigns the first unchecked line below via `lane_handoff.py assign`.

## Active queue

- [x] **★ Lane watch v3 (REQUIRED whole arc):** `git pull` turn 117+ → `bash dev/lane_watch_mac.sh --once` → `bash dev/lane_watch_mac.sh --bg` — **keep running** through remediation + Round 9 — **Mac turn 118** (`--once` CLEAR post-rebase; `--bg` started)
- [x] **test_samkings_manifest_complete** — 6/6 `done_gate` — **Mac turn 118**
- [x] **ci.py parity** — **Mac turn 119** (fast gate green) + **WIN turn 119** (full gate)
- [x] **website/dist regen** — `gen_release_catalog` + `node website/build.mjs` — **Mac turn 119** (188 assets; kobo column live; dist rebuilt locally)
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

## Post-Round-9 queue (WIN assign @ turn 121)

- [x] **Kobo tap-prep (USER round 9):** build `ethiopian-tewahedo` eink kepub → `dev/kobo_tap_calibration.py` → stage gen-35:18 + bracket probes; update `EREADERS.md` §Kobo with tap list path — **Mac turn 121**
- [x] **M4b design doc:** write `docs/superpowers/notes/2026-06-18-m4b-kindle-fork-design.md` from `platform-kindle.md` (marker suppress + chapter-tail notes HTML plan) — **Mac turn 121**
- [x] **Archive hygiene:** move closed-arc `scripts/_*.py` one-shots → `dev/archive/` (Round-9 LOW survivor; grep + lint_rules green) — **Mac turn 121**
- [x] **ACK WIN ships:** standalone K-R4-1 sep (`77417fd4`) + v0.1.0 tag sync (`6a4838c8`) + platform matrix (`6e2ff13d`) — **Mac turn 122** (verified on `main`)

## Turn 122 queue (WIN assign) — **DEFERRED to Reader Sim Lab**

> **User directive (2026-06-18):** M4b + Apple builds happen **after** audit gate closes — not during `ci.py` / rx-surfaces fix arc. Device QA + STK pack → **Reader Sim Lab** §Phase 4.

- [x] **ACK WIN ships:** verified on `main` incl. `376daea2` K-R4-1 — **Mac turn 123**
- [x] **M4b code prep:** `apply_kindle_m4b` + `verify_kindle_m4b` + `tests/test_kindle_m4b.py` (7/7) + `build_kindle.py --m4b` — **Mac turn 122** (phone gate deferred)
- [x] **M4b STK pack:** 6/6 on `~/Desktop/YHWH-kindle-m4b-qa/` (`ethiopian-tewahedo` m4b-2 + RSC-012 vn-back fix — **Mac turn 124**)
- [x] **lane_watch:** keep `--bg` running — **standing**

## Turn 125 queue (WIN assign @ post-Mac turn 124)

> **Full runbook:** `dev/LANE_HANDOFF.md` §"Mac turn 125 — full runbook" (10 sections, copy-paste commands).

> Mac turn 124 **DONE** (`f3b12433`). **NO matrix builds** until WIN `ci.py` GREEN.

- [x] **0 Bootstrap:** `git pull` · `lane_watch --once` + `--bg` · `export PYTHONUTF8=1` — **Mac turn 125**
- [x] **1 ACK turn 124:** tests 20/20 · `--list` all wired · verify_kindle_m4b OK · stk gate-only PASS
- [x] **2 Stage `build/reader-sim/`:** kindle×6 · kobo kepub · play everywhere navy · apple GAP — `STAGING_MANIFEST.md`
- [x] **3 STK live poll:** gate-only documented (no Kindle-for-Mac); `stk-last-arrival.txt` hook shipped
- [x] **4 Thorium live:** `thorium_cdp.py --live` + `YHWH_THORIUM_LIVE=1` in `reader_sim.py`
- [x] **5 M4b pack gate sweep:** 6/6 PASS — m4b design doc §7 footer
- [x] **6 `--sim` dry-run:** kindle PASS · play re-staged · kobo slow epubcheck · apple SKIP — manifest
- [ ] **7 Play emulator (optional):** deferred
- [x] **8 Save + push:** `b154f8eb` — **Mac turn 125**
- [x] **lane_watch:** keep `--bg` running — **standing**

## ★ Turn 131 — STK re-tap + M4b 6-variant re-gate (START HERE)

> **Pull `c6e8c2de`+** then latest save. **M4b KFX fix shipped** @ `c6e8c2de` + epubcheck follow-up.

### 1 — STK device re-tap (user upload · agent poll)

> **2026-06-18 wrap:** STK poll **PAUSED** — user restarting Mac (8 GB RAM). Resume after reboot.

- [ ] User uploads `Ethiopian_Bible_ethiopian-tewahedo_0.1.0_2026-06-18T232708Z-kindle-m4b.epub` via Chrome (**165347Z/221232Z STK load FAIL — do not use**)
- [ ] `bash dev/reader_sim/kindle/stk_poll_watch.sh --epub ~/Desktop/YHWH-reader-sim/kindle/…232708Z-kindle-m4b.epub` (start poll only after user says upload done)
- [ ] User Kindle QA: Gen 1:1 vn-link · study coord/back-link · title page · ToC spacing
- [ ] Log result in `docs/superpowers/notes/2026-06-18-kindle-stk-m4b-device-qa.md`

### 2 — M4b 6-variant re-gate (overflow @ turn 128)

- [ ] Rebuild + gate 6 variants → `~/Desktop/YHWH-kindle-m4b-qa/` (4/6 gated @ turn 131: ethiopian + catholic + evangelical + eastern; standalones deferred — build wiring τ.G.x.*)

### 3 — Standing

- [ ] WIN: hold M4 kindle catalog regen until Mac STK re-PASS
- [ ] `save_mac.sh` each slice

## Turn 130 — **COMPLETE** (M4b KFX fix)

## ★ Turn 130 — M4b Kindle KFX fix arc (COMPLETE)

> **STK 2026-06-18:** delivery PASS · device QA **FAIL** (both m4b builds, Mac + phone). Findings: `docs/superpowers/notes/2026-06-18-kindle-stk-m4b-device-qa.md`. **WIN:** hold M4 kindle catalog regen; continue `ci.py` + M3 kobo.

### 1 — M4b KFX fixes (Mac owns `kindle_post.py`)

- [x] TDD: `vn-link` must surface translation on KFX, not teleport to `notes-section` — inline `vnote-*` after verse (`vnotes_inlined` stat) — **Mac turn 130**
- [x] Study notes between chapters: add chapter:verse label + back-link to source verse — per-chapter `kindle-chapter-study` + `#v-` vn-back — **Mac turn 130**
- [x] Title page split (Genesis BOOK I → 3 pages) — `apply_kindle_m4b_css` page-break pass — **Mac turn 130**
- [x] In-EPUB TOC chapter-link spacing — `toc-chapter-row a` margin rule — **Mac turn 130**
- [x] Rebuild ethiopian-tewahedo m4b → user STK spot → phone/Mac re-tap — staged `build/kindle-m4b-fix/` + `~/Desktop/YHWH-reader-sim/kindle/` — **Mac turn 130** (await user upload)

### 2 — WIN coordinate (disjoint)

- [ ] **Do not** `build_format_matrix --phase M4` kindle column until Mac STK re-PASS
- [ ] Continue pytest → `ci.py` GREEN + M3 35-kepub matrix

### 3 — Standing

- [ ] User STK upload · agent poll only (8 GB / no browser MCP)
- [ ] `save_mac.sh` each slice

## Turn 129 — **COMPLETE** (scrub ACK + STK live arrival)

## ★ Turn 129 — Mac fresh-session laundry list (COMPLETE)

> **Pull `ec6520e3`+** (Christian-scope scrub pushed @ `cbf939b8`). **7 tradition SKUs · 68 kinds · M3/M4 35 assets.** WIN owns `ci.py` GREEN + M3 matrix rebuild. **SKIP Kobo** on Mac HDD. Release-count sweep (README/profile/website hero) **deferred to v0.1.1/v1.0.0 tag** — do not hand-edit counts until then.

### 0 — Bootstrap

- [ ] `git pull --rebase origin main` — expect `ec6520e3`+
- [ ] Dual radars ON (`bash dev/start_session_radars_mac.sh`)
- [ ] `bash dev/lane_watch_mac.sh --once` · `export PYTHONUTF8=1`
- [ ] Read `dev/SESSION_STATE.md` · `dev/LANE_HANDOFF.md` §Turn 131

### 1 — ACK scrub milestone

- [ ] `pytest tests/test_prune_orphan_base_notes.py tests/test_validate_schemas.py tests/test_covers.py -q`
- [ ] `ebible verify` — errors=0 (paired markers/asides)
- [ ] Grep guard: no `note-comm-rabbinic` in `epub_working/`

### 2 — Help WIN close ci.py (disjoint files only)

- [ ] Fix any scrub-related pytest reds WIN surfaces (edition counts · catalog · matrix)
- [ ] **Do not** run full `ci.py` on Mac HDD unless WIN blocked

### 3 — Reader sim / STK (if STK poll timed out)

- [ ] Check `build/reader-sim/kindle/stk-poll-watch.log` · re-stage fresh ethiopian-tewahedo m4b if needed
- [ ] **STK:** user uploads in Chrome (8 GB box) · agent `stk_poll_watch.sh` + end-task Chrome/Kindle on request (RULES guard #6)

### 4 — Scrub tail (optional, same arc)

- [ ] Scan `word`/`comm` bodies for stray rabbinic/Islamic framing (keep `lang-hebrew` + `comm-ethiopian`)
- [ ] `build_format_matrix --phase M4` spot-check one edition after WIN matrix green

### 5 — Coordinate

- [ ] **SKIP kobo** — WIN owns
- [ ] `save_mac.sh` each slice — never end unpushed

- [ ] **lane_watch:** keep `--bg` running — **standing**

## Turn 128 — **SUPERSEDED** (pull scrub milestone instead)

> **Pull `f73cda6f`+** (STK Lassen container fix shipped). WIN owns `ci.py` GREEN + kobo `--sim`. **SKIP Kobo** on Mac HDD. When this queue clears, WIN will assign Turn 129 overflow — keep `lane_watch --bg` running.

## Turn 128 queue (WIN assign @ post-turn-127) — **help WIN close ci.py**

### 0 — Bootstrap

- [ ] `git pull --rebase origin main` — expect `f73cda6f`+ (kindle_library Lassen)
- [ ] **Dual radars ON** — bootstrap hook runs `bash dev/start_session_radars_mac.sh` (lane_watch 60s + agent_idle_radar 120s); verify both in `dev/.lane_watch.log` + `dev/.agent_idle_radar.log`
- [ ] `bash dev/lane_watch_mac.sh --once` (one-shot pull/handoff check)
- [ ] `export PYTHONUTF8=1`
- [ ] Read `dev/SESSION_STATE.md` · `dev/AGENT_WORK_BACKLOG.md` · `dev/LANE_HANDOFF.md` §Turn 128

### 1 — ACK WIN + Mac ships

- [ ] `pytest tests/test_kindle_library.py tests/test_kindle_m4b.py tests/test_reader_sim.py -q`
- [ ] ACK `f73cda6f`: `kindle_library.py` · `com.amazon.Lassen` container · STK gate no longer forced gate-only
- [ ] ACK WIN `440736f1`+ pytest fixes (schema hierarchical fields · RX P4a test baselines)

### 2 — STK live poll (**priority — unblocks kindle SIM_LAYERS**)

- [ ] `dev/reader_sim/kindle_library.py` → confirm container detected on Mac box
- [ ] Send-to-Kindle one m4b from `~/Desktop/YHWH-kindle-m4b-qa/` → `stk_channel.sh "$EPUB" --wait 3600`
- [ ] Log `build/reader-sim/kindle/stk-last-arrival.txt` · update `kindle/qa-checklist.md` + `EREADERS.md` §Kindle
- [ ] `scripts/reader_sim.py --sim kindle` without gate-only fallback → target PASS
- [ ] Update `STAGING_MANIFEST.md` · flip `SIM_LAYERS_READY["kindle"]` if live GREEN

### 3 — Help WIN reader-sim 4/4

- [ ] Re-run `YHWH_THORIUM_LIVE=1 scripts/reader_sim.py --sim all --artifact-dir build/reader-sim` (kobo SKIP)
- [ ] Stage any refreshed artifacts · keep `STAGING_MANIFEST.md` current for WIN kobo lane

### 4 — Play Android emulator (Phase 3)

- [ ] Android Studio AVD · sideload `build/reader-sim/play/` everywhere navy
- [ ] M5 taps from `dev/EREADERS.md` §Play · record in `play/qa-checklist.md`

### 5 — Thorium CDP depth (overflow from 127)

- [ ] Extend `thorium_cdp.py --live`: automated popup tap assertions beyond structural floor
- [ ] Add tests in `tests/test_reader_sim.py` for new probes

### 6 — Release + website (Mac owns E:/F:)

- [ ] `gen_release_catalog` + `node website/build.mjs` if assets changed
- [ ] rsync bundle → `/Volumes/NO NAME/YHWH-v2.4-releases/` when drive mounted
- [ ] `dev/build_dmg.sh` smoke — notarize only if arc requires

### 7 — Transcription side lane (**parallel with WIN — never idle**)

- [ ] Esther Patrologia OCR resume: `extract_patrologia_pdf --book est --output content/translations/geez-tewahedo/est_patrologia.py` (PO-9 fasc-1; ~p35+; DO NOT overwrite `est.py`)
- [ ] OCR-probe page range first per `MULTI_TRACK_RUNBOOK_2026-05-20.md` §Track B
- [ ] When Esther slice ships: `save_mac.sh` + note in CHANGELOG (τ.6.x.5.b)
- [ ] Overflow: CAM hi-res folio pre-pull for pending samkings manifest chapters

### 8 — Phase 4 disjoint (while WIN pytest runs)

- [ ] 1ki EN back-translation ch11+ (`content/translations/geez-tewahedo-en/`)
- [ ] Kings CAM remaining folios in `GAPS/` (Mac owns full tree — WIN env skips incomplete)
- [ ] Draft `ci.py --reader-sim-gates` hook (structural only; WIN wires)

### 9 — Coordinate

- [ ] **SKIP kobo** — WIN owns build · gates · epubcheck · `--sim kobo`
- [ ] **NO** full `ci.py`/pytest tree on Mac HDD
- [ ] `save_mac.sh` each slice — push **both** remotes · **never ask user**

- [ ] **lane_watch:** keep `--bg` running — **standing**

## Turn 128 overflow (if primary queue clears before WIN pulls again)

- [ ] M4b 6-variant re-gate after any `kindle_post.py` touch
- [ ] `evangelical-reformed` tablet spot-build (one edition · epubcheck strict)
- [ ] `docs/superpowers/notes/2026-06-18-platform-implementation-matrix.md` — close remaining M5/M3 rows
- [ ] Archive sweep: `scripts/_*.py` one-shots · stale `dev/archive/` index
- [ ] Esther vision lane resume (Phase D) — disjoint from WIN pytest files
- [ ] Website deploy `yhwh-website` if catalog column changes
- [ ] ACK + merge any WIN pytest/ci ships without waiting on user

## Turn 127 — **COMPLETE** @ `fbe94add` + `f73cda6f`

## ★ Turn 127 — Mac fresh-session laundry list (COMPLETE)

> **Pull `04b4b518`+** (turn 126 shipped). WIN owns pytest triage + kobo `--sim`. **SKIP Kobo** on Mac HDD. Your lane: live reader sim depth + tablet matrix + release prep + disjoint Phase 4.

## Turn 127 queue (WIN assign @ post-turn-126) — **Mac parallel arc**

> **Turn 126 DONE** (`04b4b518`): apple tablet · `--sim all` 3/3 · toc probe fix. WIN still RED on `ci.py` — **no full pytest/`ci.py` on Mac HDD**. Mac pushes reader-sim from gate-only → live where apps exist.

### 0 — Bootstrap (first 5 min)

- [x] `git pull --rebase origin main` — @ `97c7992a` — **Mac turn 127**
- [x] `bash dev/lane_watch_mac.sh --once` then `bash dev/lane_watch_mac.sh --bg`
- [x] `export PYTHONUTF8=1`
- [x] Read: `dev/SESSION_STATE.md` · `dev/reader_sim/STAGING_MANIFEST.md` · `dev/LANE_HANDOFF.md` §Turn 127

### 1 — ACK turn 126 ships

- [x] `pytest tests/test_kindle_m4b.py tests/test_reader_sim.py -q` — **21/21**
- [x] `scripts/reader_sim.py --list` — four readers `[ready]`
- [x] Confirm `build/reader-sim/apple/` tablet epub present · `STAGING_MANIFEST.md` updated
- [x] `test_samkings_manifest_complete` 6/6 — **Mac turn 127**

### 2 — Thorium live CDP (**priority — unlock Phase 5**)

- [x] **Install Thorium.app** — `brew install --cask thorium` 3.4.0 — **Mac turn 127**
- [x] `YHWH_THORIUM_LIVE=1 --sim apple` on catholic-study tablet — PASS
- [x] `--sim all` play+kindle+apple 3/3 PASS (`YHWH_SKIP_KOBO_SIM=1`)
- [ ] Extend `thorium_cdp.py --live`: automated CDP popup tap (MCP/manual ceiling documented)
- [ ] Add regression tests for new live probes (deferred — structural floor green)
- [x] Document ceiling in `STAGING_MANIFEST.md` + `EREADERS.md` §Apple

### 3 — STK live poll (Kindle-for-Mac real channel)

- [x] Diagnose: **`com.amazon.Lassen`** container (turn 128) — signed-in, 2 library files
- [ ] Send-to-Kindle one m4b epub → `stk_channel.sh "$EPUB" --wait 3600` — needs UI send step
- [x] Baseline logged in `build/reader-sim/kindle/stk-last-arrival.txt`
- [x] `stk_channel.sh` + `reader_sim.py` live inventory — **Mac turn 128** (`f73cda6f`)

### 4 — Tablet artifact matrix (apple sim depth)

- [x] Build **catholic-study** `tablet` — 23.00 MB · epubcheck **0/0/0/0** — **Mac turn 127**
- [x] Staged `build/reader-sim/apple/` · `STAGING_MANIFEST.md` updated
- [x] `YHWH_THORIUM_LIVE=1 --sim apple` catholic-study PASS
- [x] **HOLD** full 11-edition matrix until WIN `ci.py` GREEN

### 5 — Play Android emulator (Phase 3 spike)

- [ ] Android Studio AVD (Pixel · Play Books sideload path)
- [ ] Sideload `build/reader-sim/play/` everywhere navy artifact
- [ ] M5 minimum taps from `dev/EREADERS.md` §Play — honest pass/fail
- [ ] Record in `dev/reader_sim/play/qa-checklist.md` (emulator ≠ phone)

### 6 — M4b pack + Kindle sim maintenance

- [x] Re-run 6-variant gate sweep on `~/Desktop/YHWH-kindle-m4b-qa/` — **6/6 PASS**
- [x] Update `m4b-kindle-fork-design.md` §7 footer
- [x] `--sim kindle` uses live Lassen inventory (no forced gate-only) — turn 128

### 7 — EREADERS + platform truth records

- [x] Update `dev/EREADERS.md` §Apple — Thorium sim proxy + turn 127 evidence
- [x] Update §Kindle STK — gate-only blocker documented (m4b doc §7)
- [x] Update §Play — Thorium sim PASS; emulator deferred (`play/qa-checklist.md`)
- [x] Cross-check `platform-implementation-matrix.md` — M4b + Thorium sim rows

### 8 — Release prep (external drive — Mac owns E:/F:)

- [ ] `gen_release_catalog` + `node website/build.mjs` if catalog/assets changed
- [ ] rsync release bundle → `/Volumes/NO NAME/YHWH-v2.4-releases/` (or E:/F: when mounted)
- [ ] `dev/build_dmg.sh` smoke rebuild — notarize check only if user directed

### 9 — Phase 4 disjoint backlog (while WIN pytest runs)

- [ ] 1ki EN back-translation ch11+ gap (`content/translations/geez-tewahedo-en/`)
- [ ] Samuel/Kings CAM hi-res — any remaining folios in `GAPS/` tree
- [x] Archive hygiene: no `scripts/_*.py` one-shots at repo root (turn 127 grep)

### 10 — Reader Sim Lab Phase 4–6 closeout

- [ ] Flip `SIM_LAYERS_READY["kindle"]` if STK live GREEN
- [ ] Flip `SIM_LAYERS_READY["apple"]` + `["play"]` if Thorium live GREEN
- [x] Draft `ci.py --reader-sim-gates` hook (non-blocking; WIN integrates) — turn 128
- [x] `dev/TOOLCHAIN.md` §Reader Simulation Lab section — **Mac turn 127**

### 11 — Coordinate with WIN

- [ ] **SKIP kobo** entirely — WIN owns build · gates · epubcheck · `--sim kobo`
- [ ] **NO** full `ci.py`/pytest tree on Mac HDD
- [ ] `save_mac.sh` each slice — push **both** remotes

### 12 — Done when

- [x] Thorium live — installed + `--sim` PASS (CDP taps MCP/manual)
- [x] STK live — Lassen library inventory (`f73cda6f`); arrival poll awaits send
- [x] catholic-study tablet staged
- [x] EREADERS.md + STAGING_MANIFEST.md current
- [ ] Play emulator spike recorded — deferred (no AVD)
- [x] M4b 6/6 re-gate PASS

- [ ] **lane_watch:** keep `--bg` running — **standing**

## Turn 126 queue — **COMPLETE** @ `04b4b518`

> **Pull `ebbc2597`+** then work this section only. WIN `ci.py` RED (15 pytest reds). **SKIP Kobo** (WIN lane). **Apple tablet** blocks `--sim all`.

## Turn 126 queue (WIN assign @ post-ci.py triage) — **Mac fresh session**

> **Laundry list for Mac.** WIN `ci.py` still RED (15 pytest reds); do **not** run full pytest/`ci.py` on Mac HDD. **Apple tablet artifact** is the main blocker for agent `--sim all`.

### 0 — Bootstrap (first 5 min)

- [x] `git pull` @ `ebbc2597`+ — **Mac turn 126**
- [x] `lane_watch --once` + `--bg` · `PYTHONUTF8=1`

### 1 — ACK baseline (quick, no new work on red)

- [x] `pytest` kindle_m4b+reader_sim — **21/21**

### 2 — Apple tablet artifact (**BLOCKING** `--sim all`)

- [x] `build_edition` tablet ethiopian · epubcheck **0/0/0/0** · staged `build/reader-sim/apple/`
- [x] `thorium_cdp` toc probe — RX P4a chapter nav pass

### 3 — STK live poll (Kindle-for-Mac channel)

- [x] Kindle.app present; no library container — gate-only in qa-checklist

### 4 — Thorium live CDP (beyond gate-only)

- [x] Thorium not installed — gate-only floor

### 5 — Agent sim suite

- [x] `--sim all` **3/3 PASS** (`YHWH_SKIP_KOBO_SIM=1`) · kobo SKIP → WIN
- [x] `STAGING_MANIFEST.md` updated

### 6–9 — deferred to Turn 127 (M4b · Play emulator · coordination)

- [x] All turn 126 done-when criteria met @ `04b4b518`

## Turn 124 queue — **COMPLETE**

## Turn 124 queue (WIN assign @ parallel prep) — **Mac prep while WIN ci.py runs**

> **No heavy EPUB matrix builds** on either box while WIN `ci.py` runs. Gate/sim on cached artifacts only.

- [x] **Kindle `stk_channel.sh`:** gate-only + poll scaffold wired; auto-fallback when Kindle-for-Mac absent — **Mac turn 124**
- [x] **Thorium sim layers:** `thorium_cdp.py` + `SIM_LAYERS_READY` flipped (`apple`/`play`/`kindle`) — **Mac turn 124**
- [x] **M4b m4b-2:** comment-delimited study blocks + vn-back strip (epubcheck 0/0/0/0 on ethiopian m4b) — **Mac turn 124**
- [x] **ACK WIN ships:** pull turn 124+ sim pack shells + handoff — **Mac turn 124**
- [x] **lane_watch:** keep `--bg` running — **standing**

## Reader Simulation Lab (POST-AUDIT)

**WIN owns:** Kobo + Play sim layers. **Mac owns:** Kindle STK + Apple/Play Thorium.

- [x] **Phase 1 scaffold:** tree + `reader_sim.py` + per-reader `build|gate|sim.sh` shells — **WIN turn 124**
- [x] **Kobo sim layer wired** (`kobo_tap_calibration` in `--sim kobo`)
- [x] **Play Thorium sim** (`thorium_cdp.py` structural proxy; CDP when Thorium installed)
- [x] **Kindle STK channel** (`stk_channel.sh` gate-only GREEN; full poll when Kindle app present)
- [x] **Apple Thorium sim** (`thorium_cdp.py` via `reader_sim.py --sim apple`)
- [ ] **Agent sim suite:** `--sim all` GREEN (needs cached artifacts per reader on disk)
- [ ] **CI:** optional `ci.py --reader-sim-gates`

Specs: `m4b-kindle-fork-design.md` · `platform-apple.md` · `EREADERS.md`

## Round 9 queue (COMPLETE)

- [x] **Gate:** round-8 findings 0 open HIGH/MEDIUM @ turn 119
- [x] **Local engine:** ROUND=9 LANE=mac (local flip; reverted before commit)
- [x] **Workflow:** 22 dims — 8 survivors; fixes shipped for actionable items
- [x] **Research briefs:** `notes/2026-06-18-platform-apple.md` + `platform-kindle.md`
- [x] **Push:** `_audit-split/findings-mac.json` → `lane-transfer/audit` — **Mac turn 119** (`94e1010b`)

Plan: `docs/superpowers/plans/2026-06-17-round9-parallel-audit-and-platform-research.md`

## Completed (reference)

- [x] Samuel CAM IIIF acquire — 0 remaining @ turn 110b
- [x] Kings CAM 180 hires @ turn 108