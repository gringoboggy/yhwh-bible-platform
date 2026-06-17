# Round-8 split audit — merged findings (2026-06-16)

**Status:** MERGED (Mac 8b re-audit @ turn 113 + WIN thorough @ turn 113b). User standing approval: proceed to fixes.
**WIN half:** thorough pass **COMPLETE** @ turn 113 — all 7 WIN dims run (`tests-run`, `github-gitlab`, `claude-setup`, `opt-build`, `rx-surfaces`, `popup-integrity`, `byte-stability` via kr2 gates). **5 new survivors** (claude-setup/lane); artifact dims GREEN with known WARNs only.

## Executive summary

Mac lane (18 dims, Round-8b re-audit @ turn 113): **30 survivors** (0 critical · 2 high · 10 medium · 13 low · 5 info); 21 prior refuted.
WIN lane (7 dims, thorough @ turn 113b): **17 survivors** (prior 12 + 5 claude-setup/lane); artifact dims GREEN.
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
- [x] **MEDIUM** Test coverage gaps (inject_book write path, coord-guard driver loops) — **Mac turn 114** (`test_inject_write_path.py`) + **mint-11** (`test_mint11_phase3.py` coord guard class sweep) + build-my-bible HTTP **@ 9b877205**

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

**COMPLETE @ turn 113b.** All 7 WIN dims run (see appends below). Delete `lane-transfer/audit` after merge consumed.

### WIN turn-112 append (`github-gitlab` dim)

- [x] **MEDIUM** `SHA256SUMS.txt` covers 141/186 release assets — **45 Kindle color-variant EPUBs** missing checksums — **WIN @ turn 112 overnight** (`scripts/merge_release_checksums.py` → 186/186; uploaded to `v0.1.0`)

**Overnight coordination (WIN turn 112):** `scripts/lane_watcher.py --loop 120 --assign-mac` polls Mac pushes; `dev/MAC_WORK_QUEUE.md` holds the auto-assign backlog. Plan: re-run round-8b thorough Mac audit when Phase 1–3 all ticked.

### WIN turn-113 append (`tests-run` dim)

- [x] **Shard gate @ `b4bef146`:** `scripts/pytest_gate_shard.py` — 254 test files, marker `not slow and not done_gate`, ~2.5h. **12 triaged:** 5 TIMEOUT (retry with 1200s), 5 false-FAIL (all-slow deselect — fixed in shard runner), 1 real FAIL (`test_omega4x_hygiene` B023 in `build_edition.py` — **fixed @ turn 113**), 1 expected WIN skip (`test_samkings_manifest_complete` — GAPS images Mac-only; Mac 6/6 incl. `done_gate`).
- [x] **Retry @ turn 113:** all 5 TIMEOUT files **GREEN** — `marker_style` 27m @ 2400s; `presentation_polish` 59m @ 4800s (multiple `build_one` integration tests). Shard gate **complete** except Mac-only `test_samkings_manifest_complete` (`done_gate`).

### Mac turn-113 append (Round-8b THOROUGH re-audit, post Phase 1–3)

**Pass:** 18 dims adversarial re-verify @ `lane-transfer/audit`. **30 survivors** (2 high · 10 medium · 13 low · 5 info). **21 prior survivors refuted** (Phase 1–3 fixes held).

**Phase 4 candidates (new):**
- [x] **HIGH** `web_notes.py` `load_notes() or []` — corrupt notes file wipe on editor save (`api_save`/`api_delete`) — **Mac turn 113b** (`load_notes_checked` + refuse writes)
- [x] **MEDIUM** `load_notes_checked` class sweep — preview/sources/editions/export/matrix/inject/api_books — **Mac turn 114** (23 parse-guard tests green)
- [x] **HIGH** `at_scale_base.append_candidates` — corrupt JSON queue reset to `[]` on parse failure — **Mac turn 113b** (`CandidateQueueCorruptError`)
- [x] **MEDIUM** `api_save` no `sanitize_html()` — stored XSS in note editor — **Mac turn 113b**
- [x] **MEDIUM** `build_edition.py` unparseable book silently omitted — **Mac turn 113b** (`assert_notes_corpus_parseable` at `build_one` entry)
- [x] **MEDIUM** `load_kinds()` / `load_categories()` still `maxsize=1` — mirror editions mtime cache — **Mac turn 113b**
- [x] **MEDIUM** `refactor.py --apply` — no config/matrix cache invalidation — **Mac turn 114** (`_invalidate_caches_after_refactor`)
- [x] **MEDIUM** `prospect.py` — no `coord_in_canonical_extent` guard on candidate emit — **Mac turn 113c** (`_emit_extent_ok` + mint11 driver sweep)
- [x] **MEDIUM** Kindle `catalog.json` — 45/45 cells `sha256: ""` (regen after turn-112b) — **Mac turn 113b** (188 assets; kindle empty_sha256=0)
- [x] **MEDIUM** Doc drift — source corpus **91,720** (post-aes purge) vs docs citing 91,723 — **Mac turn 114** + **WIN turn 115** (`SESSION_PLAYBOOK.md` §0/§3/§5)
- [x] **MEDIUM** `inject_book` write path (`dry_run=False`) — no behavioral test — **Mac turn 114** (`test_inject_write_path.py`)
- [x] **MEDIUM** Book-code canonicalization — 3 parallel alias maps, web/API uses none — **WIN turn 115 + Mac turn 114** (`scripts/core/book_codes.py` + `config.resolve_book_code`; API/CLI/preview/inject wired; `tests/test_api_book_code_normalize.py` + `test_book_codes.py`)

### WIN turn-113b append (`claude-setup` dim)

- [x] **HIGH** `SESSION_PLAYBOOK.md` §0/§6.6 says commit only on user `"save"`; `CLAUDE_PROJECT_RULES.md` §4 requires autonomous **local commits during work** + milestone `save-all.ps1` — agents following PLAYBOOK will under-commit overnight work — **WIN turn 115** (§0 + §6.6 aligned to RULES §4 two-cadence model; Mac turn 114 merged)
- [x] **HIGH** `SESSION_PLAYBOOK.md` §6.6 documents `save.ps1` + manual dual push; omits `save-all.ps1` (5-leg + `lane_ping --before-push` + rotation) — incomplete save path in the every-session playbook — **WIN turn 115** (+ `dev/save_mac.sh` on Mac)
- [x] **HIGH** `lane_watcher.py` handoff-blind — **WIN turn 114** unified `scripts/lane_watch.py`: fetch + remote `origin/main:LANE_HANDOFF` turn compare + auto-pull on BEHIND **or** remote board ahead + `incoming` both lanes + `UNPUSHED HANDOFF` nag when local board ahead of remote with unpushed commits. `lane_watcher.py` → shim; `dev/lane_watch_{mac,win}.*` wrappers.
- [x] **MEDIUM** Repo `.claude/settings.json` is `{}` — SessionStart hooks live in parent `YHWH-v2.4-full/.claude/` after `install_cc_hooks.ps1`; RULES §0 cites in-repo `.claude/hooks/bootstrap-triad.ps1` path that does not exist in the tracked repo — **WIN turn 115** (RULES §0 + PLAYBOOK §1 document `dev/cc-hooks/` install path)
- [x] **MEDIUM** `LANE_HANDOFF.md` STANDING still assigns turn-24 hook wiring already shipped in `dev/cc-hooks/bootstrap-triad.ps1`; turn 113 assign still says `lane_watcher running` after user stopped it — **WIN turn 115** (STANDING: lane_watch v3 + hooks ACK shipped)

### WIN turn-113 append (`opt-build` dim)

- [x] **INFO** Single-edition cold build ~133s + `--all` ThreadPool(5) + ω.20 cache + mtime guard — **CONFIRM-OPTIMAL** (round-7 adversarial review holds; compresslevel 9 + pinned ZipInfo required for byte-stability).

### WIN turn-113 append (`rx-surfaces` dim)

Built `ethiopian-tewahedo` + `catholic-study` @ `dev/.audit-build/` (r8audit, 2026-06-17). Gates:

- [x] `audit_epub_structure` — **0 critical** both (DUP_NOTE_ROWS / DUP_IDS / BROKEN_NOTEREF / UNBALANCED_TAGS all OK).
- [x] `verify_kr2_build` — **ALL K-R2 GATES GREEN** both (66,694 / 43,016 noterefs resolve; 0 promoted cross-file; 0 dup-ids; 0 ch-spilled badges).
- [x] **LOW (known-deferred)** WARN 4g: `vnote-1ki-12-24` strips 6,937 chars (> pop floor) — K-R4-2 class, fix arc in flight per deferred list. — **Mac turn 114** (confirmed @ r8audit; no new FAIL class)
- [x] **LOW (known)** WARN 4m: one ADJACENT `vnote-1en-100-1` < `vnote-1en-100-11` prefix pair on eth — documented corpus-wide translation-surface WARN (not FAIL). — **Mac turn 114** (confirmed; corpus-wide, not edition-specific)

### WIN turn-113 append (`popup-integrity` dim)

Artifact zip-scan on same r8audit builds (S1/S2/S3):

- [x] **S3 hidden-target noterefs:** **0** on both artifacts (no new teleport class beyond known `notes-section` / `verse-refs-section` fixes @ Phase 3).
- [x] **S1 separator coverage:** **0** study footnotes missing `vn-sep` on non-glossary emitters (vnote translation popups remain the known K-R4-1 gap — deferred).
- [x] **MEDIUM** **S2 size census:** eth 218 / catholic 184 asides >3,300 stripped chars; top offenders are `vnotes-*-s1` study chunks ~4,300 B (under 7,748 decline ceiling post Phase 3 chunking) + outlier `vnote-1ki-12-24` @ 6,937 (K-R4-2). No new emitter class beyond prior art — **CONFIRMED-KNOWN @ WIN turn 115 + Mac turn 114** (K-R4-2 deferred)
