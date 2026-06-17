# Round-8 split audit — merged findings (2026-06-16)

**Status:** MERGED (Mac 8b thorough @ `b1b9dffd` + WIN partial fast-pass). User standing approval: proceed to fixes.
**WIN half:** partial thorough pass @ turn 113 — `github-gitlab` SHA256 gap closed; `tests-run` shard complete (254 files, 12 triaged); `claude-setup`/`opt-build` pending full Workflow; Phase 2/4 ticks reconciled vs Mac ships.

## Executive summary

Mac lane (18 dims, adversarial verify): **35 survivors** (0 critical · 5 high · 17 medium · 9 low · 4 info).
WIN lane (partial): **12 survivors** (1 critical · 2 high · 7 medium · 2 low).
**Combined unique headline:** silent data-loss in ingest/promote paths, API error HTTP semantics, stale release/website artifacts, popup hidden-target classes beyond K-R4, and **45 corrupt Kindle stubs on GitHub release**.

Overall: codebase is shippable but **not mint** — several paths can drop or mis-mark data without surfacing errors; public release surface has corrupt/stale assets.

---

## Phased fixes

### Phase 1 — Silent data-loss + API correctness (safest high-impact)

- [x] **HIGH** `prospect.py` write_queue clobbers promotion status — delegate to `at_scale_base.append_candidates` or merge preserving status (`scripts/prospect.py:153`) — **Mac turn 101**
- [x] **HIGH** `batch_promote_xrefs` marks promoted when zero inserted — only mark actually inserted / `note_already_exists` (`scripts/batch_promote_xrefs.py:110`) — **Mac turn 101**
- [x] **HIGH** `/api/build-my-bible` errors return HTTP 200 — honor `http` in `_dispatch_table_result` (`scripts/web.py:1070`); add HTTP-level test — **WIN @ 9b877205** (`TestBuildMyBibleHttpStatus`)
- [x] **MEDIUM** `batch_promote_xrefs --per-candidate` never updates queue JSON status (`scripts/batch_promote_xrefs.py:181`) — **Mac turn 102** (verified + regression test; path already called `update_queue_status`)
- [x] **MEDIUM** `promote._chapter_from_id` parses verse as chapter (`scripts/promote.py:527`) — **Mac turn 101** (`rsplit` + `is not None` fallback)
- [x] **MEDIUM** `inject.py` treats SyntaxError notes file as empty corpus (`scripts/inject.py:689`) — **Mac turn 101**
- [x] **STALE TEST** `test_badge_sits_at_verse_end` + `test_chapter_last_verse_badge_stays_in_its_chapter` — walk K-R15a `badge-trail` span — **WIN @ b8c7c950**

### Phase 2 — Release / website / packaging (no marathon core)

- [x] **CRITICAL** Delete 45 `default._*` corrupt Kindle stubs from v0.1.0 release (keep canonical `YHWH-*-kindle-*.epub`) — **Mac turn 102** (46 assets incl. `SHA256SUMS-merged.txt`; release now 142)
- [x] **HIGH** Attach M3 Kobo 45/45 from `m3-kobo-v0.1.0/` handoff + merge SHA256SUMS + regen catalog — **Mac turn 107b** (187 assets; kobo column live)
- [x] **HIGH** Rebuild `website/dist/` from src (stale v0.0.3) — `gen_release_catalog` + `node website/build.mjs` — **Mac turn 102** (dist gitignored; regen run locally → v0.1.0)
- [x] **HIGH** `installer.iss` read first line of VERSION only (`dev/installer.iss:27`) — **Mac turn 102** (`/DMyAppVersion=` + `#ifndef` fallback)
- [x] **MEDIUM** Remove duplicate `SHA256SUMS-merged.txt` from release — **Mac turn 102** (deleted with stub batch)
- [x] **MEDIUM** Align Windows artifact naming (installer vs sign script vs releases.html) — **Mac turn 107b** (`YHWH-{ver}-windows-x64.exe`)
- [x] **MEDIUM** `how-to-use.html` cites legacy EPUB filename vs catalog matrix names — **Mac turn 102**

### Phase 3 — Build / popup / cache guards (byte-stability obligation)

- [x] **MEDIUM** `edition_stats` cache signature missing `enable_ai_notes` / `max_phase` (`scripts/core/edition_stats.py:56`) — **WIN @ 9b877205**
- [x] **MEDIUM** Gate Kobo byte-cap splitter on `target_reader==eink` (`scripts/build_edition.py`) — **WIN @ a8e0e099**
- [x] **MEDIUM** `verse-refs-section` hidden noteref targets (extend beyond `notes-section`) (`scripts/generate_verse_popups.py`) — **WIN @ a8e0e099**
- [x] **MEDIUM** Study-glossary-cat hist monoliths >7,748 stripped — within-note chunking (`scripts/build_edition.py`) — **WIN @ a8e0e099**
- [x] **MEDIUM** `config.py` mtime-keyed cache for runtime-edited YAML (`scripts/core/config.py:297`) — **WIN @ a8e0e099**
- [x] **LOW** Extend `verify_kr2_build` gates for glossary-cat + verse-refs-section census — **WIN @ a8e0e099**
- [x] **LOW** Mirror glossary nav patch into `toc.ncx` — **Mac turn 111** (`_patch_study_glossary_nav` + `inject_eink_study_backmatter` ncx entry; K-R6-2 wrapper id `study-entry-*`)

### Phase 4 — Data validity + docs drift

- [x] **MEDIUM** 3 OOE notes in `content/notes/aes.py` ch10 v11-13 — **Mac turn 108** (`test_aes_notes_extent`)
- [x] **MEDIUM** 31 phantom `1ma/2ma` candidate files — **Mac turn 107b**
- [x] **MEDIUM** `translations.py` legacy `ex`/`exo` store alias — **Mac turn 107b** (`_BOOK_FILE_ALIASES`)
- [x] **MEDIUM** 1ki EN back-translation gap ch7-10 — **Mac turn 107b** (117 v)
- [x] **MEDIUM** Doc count drift (MATRIX_MAP 91,733 vs live 91,723; dist meta 91,733 vs 91,553) — **Mac turn 101** (MATRIX_MAP + matrix.py; `website/dist/` deferred Phase 2)
- [ ] **MEDIUM** Test coverage gaps (inject_book write path, coord-guard driver loops) — build-my-bible HTTP **done @ 9b877205**

### Phase 5 — Optimization decisions (defer unless cheap)

| Area | Verdict | Note |
|------|---------|------|
| Single-edition build ~133s | CONFIRM-OPTIMAL | Cold floor; cache hits sub-second |
| compresslevel 9→6 | DECLINED | Byte/hash drift |
| M2 Apple layout | CONFIRM-OPTIMAL | Mac 8b read-only |
| Unified meta-driver ingest | CHANGE (medium) | ~6× wall-clock when implemented |
| Marathon Workflow orchestration | CHANGE (medium) | Future vision lane |

---

## Constraints carried

- Never touch marathon core / GAPS / `content/manuscript/**`
- 9 KJV editions byte-stable; additive schema only
- Local commit per fix; 5-leg sync at milestones
- **Kobo device QA / M4b HOLD** until Phase 1–3 land (user directive)

## WIN audit remainder

Complete thorough Workflow pass: `tests-run` (full pytest), `opt-build`, `claude-setup`, re-verify `rx-surfaces` + `popup-integrity` with adversarial bar. `github-gitlab` partial @ turn 112 (see below). Delete `lane-transfer/audit` after merge consumed.

### WIN turn-112 append (`github-gitlab` dim)

- [x] **MEDIUM** `SHA256SUMS.txt` covers 141/186 release assets — **45 Kindle color-variant EPUBs** missing checksums — **WIN @ turn 112 overnight** (`scripts/merge_release_checksums.py` → 186/186; uploaded to `v0.1.0`)

**Overnight coordination (WIN turn 112):** `scripts/lane_watcher.py --loop 120 --assign-mac` polls Mac pushes; `dev/MAC_WORK_QUEUE.md` holds the auto-assign backlog. Plan: re-run round-8b thorough Mac audit when Phase 1–3 all ticked.

### WIN turn-113 append (`tests-run` dim)

- [x] **Shard gate @ `b4bef146`:** `scripts/pytest_gate_shard.py` — 254 test files, marker `not slow and not done_gate`, ~2.5h. **12 triaged:** 5 TIMEOUT (retry with 1200s), 5 false-FAIL (all-slow deselect — fixed in shard runner), 1 real FAIL (`test_omega4x_hygiene` B023 in `build_edition.py` — **fixed @ turn 113**), 1 expected WIN skip (`test_samkings_manifest_complete` — GAPS images Mac-only; Mac 6/6 incl. `done_gate`).
- [x] **Retry @ turn 113:** all 5 TIMEOUT files **GREEN** — `marker_style` 27m @ 2400s; `presentation_polish` 59m @ 4800s (multiple `build_one` integration tests). Shard gate **complete** except Mac-only `test_samkings_manifest_complete` (`done_gate`).
- [ ] **Remainder:** `claude-setup`, `opt-build`, `rx-surfaces`, `popup-integrity` Workflow dims.