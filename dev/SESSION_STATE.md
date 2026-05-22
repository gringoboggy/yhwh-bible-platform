# Session state — current snapshot

> **➤➤➤ 2026-05-21 (LATEST) — read FIRST.** Corpus **67,715 notes / 71 kinds / 11 editions / 87 books**; demo build LIVE — `inject` places **99.76%** (66,173 + 1,381 base-baked / 67,715), `ebible verify` **errors=0 / 24,015 paired**, valid EPUB. Health: `trace_matrix` **0 unresolved refs**, `validate_taxonomy` 100% attributed, ruff-format + `lint_rules` clean. Shipped chronology + latest commits: `dev/CHANGELOG.md`.
>
> **The map layer (read for "where / how / what shipped"):** `dev/PLAN_2026-05-21.md` (forward roadmap; supersedes `PLAN_2026-05-09`) · `dev/IN_FLIGHT.md` (live task tracker) · `dev/MATRIX_MAP.md` (data-flow + base-HTML structure) · `dev/REPO_MAP.md` (file/folder index) · `dev/CHANGELOG.md` (shipped chronology). (This file was trimmed from ~896 KB on 2026-05-21; history in `dev/SESSION_STATE_archive_2026-05-21.md`.)

## What shipped (2026-05-21 arcs)

- **Matrix maximization (2026-05-22, uncommitted).** `editions.yaml`: `scholarly-academic` += `topic` category (now reaches full corpus, enabled 41,374→67,709 — `topic-nave`'s 26,335 were orphaned in 0 editions); `ethiopian-tewahedo` `max_phase mvp→phase2` (ships its declared `dist-typological`/`dist-mariological` + `dict-easton`, 37,495→41,285; no topical flood — flagship lacks `topic`). TDD `tests/test_enabled_kinds_unified.py::TestMatrixMaximization`. Also IN_FLIGHT→idle, ν.8 logged, scope-addenda index. 762 edition/matrix tests pass · trace_matrix 0 · build smoke valid.
- **Test suite GREEN** — triaged + fixed all 92 post-rebuild failures. Most were phase pins reading the trimmed `SESSION_STATE.md`/`IN_FLIGHT.md` + the moved `PLAN_2026-05-09.md` (→ `dev/archive/`); fixed at root cause via the new `tests.fixtures.assert_phase_recorded` chokepoint (reads CHANGELOG) + `lint_rules.check_no_ephemeral_doc_pins` guard. Plus `dict-easton` count refresh + 13 pre-existing code fixes. **6404 passed / 0 logic failures** (1 pre-existing flaky HTTP-socket test, `test_build_all_route_serves_json`, passes in isolation).
- **Base-HTML recovered + committed** (`5ee2ad1`) — the lost WEB scripture HTML; `ebible build` makes valid EPUBs again.
- **Inject-tail spill resolver** (`d3acc4f`) — `inject.find_verse_region_b_spill` resolves Strategy-B chapters whose verses spill across a split-file boundary (jer/psa/isa/1ch). `scripts/audit_base_html.py` classifies regular vs irregular layout. 99.21% → 99.48%.
- **Reference-corpus rebuild + Easton's** (`38b80d3`): Nave's Topical rebuilt clean from a CCEL PDF (`extract_naves_ccel.py` → 26,335 `topic-nave`, was 15,258 OCR-noisy); Easton's Bible Dictionary ingested (`extract_eastons_ccel.py` → 3,779 `dict-easton`, new kind under `hist`). `promote.batch_insert_notes` (one write/book). Corpus 52,859 → 67,715.
- **Coord guard + dead-dispatch repoint** (`a935701`): `canonical_verse_counts.coord_in_canonical_extent` rejects out-of-extent coordinates at the promote boundary (0 invalid-coordinate notes corpus-wide); `run.py`/`add_note.py` injector dispatch repointed from the lost `source_archive/`+`kings_session/` scripts to `scripts/inject.py`.

## Next (per dev/PLAN_2026-05-21.md, toward the 2026-06-07 deadline)

1. **DEMO (north star)** — build is solid; remaining is user-side visual QA (browser + e-reader) + optional epubcheck/Java. **Base-HTML coverage is COMPLETE** — all 87 books / 1,702 chapters present (verified `audit_base_html.py --coverage`; NO book truncated). The ~156-161-note inject residual is purely **verse-level versification** (the note's source numbers a verse the base chapter lacks: aes/1en/mq/sir/jub) — NOT mechanically addable. Map: `dev/MATRIX_MAP.md` → "Base-HTML structure & coverage".
2. **MANUSCRIPT MARATHON — PAUSED** (the other major track): 1ki5 R2 spec-review held; then 1ki6 / 1sa2 (Kings/Samuel Geʽez dual-witness collation). HEAVY → script-based, single-chapter, OOM-aware (memory `feedback_concurrent_agent_cap`), check-in cadence (`feedback_marathon_pacing`).
3. **CORPUS EXPANSION — opportunistic** (memory `corpus-reference-expansion`): more PD reference works via clean CCEL PDFs the user supplies (candidates: Matthew Henry / JFB commentary, Torrey's Topical, Vincent's Word Studies).
4. **CLEANUP / UPGRADES** — see PLAN_2026-05-21 §upgrades (editorial note-key review, matrix vestigial-layering refactor, etc.).

## Conventions (unchanged)

Local commit only via `save.cmd`/`save.ps1` (PowerShell; no remote — deleted 2026-05-12). Tests: full interpreter path + `$env:PYTHONUTF8="1"`, one file at a time. "continue" ≠ "save". Scope frozen 2026-05-20 (consolidation phase).

## Console inventory (web.py UI surface, 18)

`APIHELP_HTML` · `AUDIT_HTML` · `AUDIT_LOG_HTML` · `BUILD_TRACKER_HTML` · `COMPARE_HTML` · `COVERS_HTML` · `CUSTOMIZE_HTML` · `DIFF_HTML` · `EXEC_HTML` · `EXPORT_HTML` · `GREEK_HTML` · `HEBREW_HTML` · `MATRIX_HTML` · `OPS_HTML` · `PREFLIGHT_HTML` · `PUBLISHER_HTML` · `SOURCES_HTML` · `WIZARD_HTML` (note editor served at `/` is `INDEX_HTML`). Each cross-links to the others (lint_rules check 6.2).
