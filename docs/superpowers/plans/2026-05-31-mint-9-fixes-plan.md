# mint-9 (deep-audit round 2) — phased fixes plan

**Status:** EXECUTING 2026-05-31 — Phase 1 (data-loss/filter HIGH) + Phase 2 (stale-cache/guards) shipped; Phases 3–6 in progress. NOT converged (45 survivors round 2); fixing then re-auditing (round 3). H5 `ex.py`→`exo` + `aes` ch11–16 + M8 compresslevel remain deferred-by-design.

> Generated 2026-05-31 by `.claude/workflows/deep-audit.js` round 2. Counts: 66 deduped → 45 survived / 21 refuted (high 6 · med 8 · low 25 · info 6). Raw: `../notes/2026-05-31-mint-9-audit-raw.json`; survivor detail in `../notes/2026-05-31-mint-9-findings.md`. (The synthesizer's exec-summary "36 findings/5 high" line below is a synth mis-count of the round-1 set — the authoritative round-2 counts are this line's.)

## Executive summary

The mint-8 round-1 deep audit surfaced 36 verified findings (5 high, 9 medium, 14 low/info, plus optimization recommendations) across a codebase that is fundamentally healthy — no crashes, no marathon-core defects, all 9 KJV editions byte-stable. The most serious issues are **silent data-loss vectors**: a non-canonical `BOOK = "ex"` code that orphans all Ge'ez/Amharic Exodus verse data from canonical lookups (so every Exodus popup silently falls back to KJV), a tradition/time-filter gap that lets Strategy-B notes (e.g. `2ch`) survive filters they should be disabled by, and `batch_insert_notes` dropping an entire note batch on a post-splice SyntaxError with no log. A second cluster is **stale-cache correctness**: the build cache key omits `matter_pages.py`, `resync_marker_glyphs.py`, theme CSS, and `source_dates.yaml`, so edits to those serve stale EPUBs. The remaining findings are guard hardening (lint coverage of book-code maps), tautological tests violating RULES §8.1/§8.7, a thread-race on `_CACHED_CONN`, and doc drift in REPO_MAP/INDEX/plan-status. Every fix below is additive or guard-adding; none touch the marathon core, and the KJV byte-gate holds throughout.

## Phased fixes

### Phase 1 — Silent data-loss & filter-correctness (HIGH, ship first)

- [ ] **HIGH — Canonical book code `ex` → `exo` orphans all Ge'ez/Amharic Exodus data** — `content/translations/{geez-tewahedo,amharic-tewahedo,geez-tewahedo-en,amharic-tewahedo-en}/ex.py:24` (`BOOK = "ex"`) + loader `scripts/core/translations.py:54-55`.
  **Fix:** `git mv ex.py exo.py` in all four translation dirs; set `BOOK = "exo"` (line 24) in each; in `scripts/lint_rules.py:977,1006` change `"ex"`→`"exo"` in `expected_geez`/`expected_amharic`; remove the now-redundant `"ex": "exo"` from `scripts/render_coverage.py:51 _BOOK_ALIASES`; add `"ex": "exo"` to `scripts/core/sources_base.py:54 _BOOK_CODE_ALIASES` so future legacy-coded re-ingests normalize at the boundary. Update runtime-code assertions in `tests/test_parallel_bible_tau7xb.py:164` and the `f"{book}.py"` existence checks in `test_parallel_bible_tau6x2{j,m}.py` / `..._geez_arc.py` to `"exo"`. **Do NOT** change `ingested_book_codes: [ex]` in `_meta.yaml` or the `== ["ex"]` provenance assertions (line 356) — those are historical ingest records. `ruff format` the four renamed files after.
  **Guard:** the lint fix above + the canonical-map lint extension in Phase 2 close the regression door; add a pytest asserting `translations.has_book("geez-tewahedo","exo")` is True.
  **Build path:** No (popup-source data path, not KJV build). 9 KJV editions use `kjv/exo.py`, untouched → byte-stable.

- [ ] **HIGH — Tradition/time filters silently skip Strategy-B books without `id_prefix`** — `scripts/build_edition.py:130-132` (`_iter_note_ref_traditions`), `:326-328` (`_iter_note_ref_attribution_years`), `:2636-2638` (`disabled_note_ids` block). Confirmed live: only 14/87 books have `id_prefix`; `2ch` (b13) has real notes that survive every tradition/time filter.
  **Fix:** in all three guards, mirror `inject.py:674-677` — fall back to `book.get("bxx")` before `continue`:
  ```python
  prefix = book.get("id_prefix")
  if not prefix:
      prefix = book.get("bxx")
  if not prefix:
      continue
  ```
  **Guard:** pytest asserting a Strategy-B book's note ref-id (e.g. `ref-b130101`) appears in `disabled_html_ref_ids` for an edition with `traditions_default`/`time_filter_ceiling` set.
  **Build path:** Yes, but functions short-circuit to empty when both filters unset → **byte-identical for all 9 KJV editions** (additive). Prove via regen + `git diff` on the 9 KJV outputs.

- [ ] **HIGH — `batch_insert_notes` silently drops entire batch on post-splice SyntaxError** — `scripts/promote.py:388-392`.
  **Fix:** replace bare `except SyntaxError: return 0` with a logged variant (`logging.error("...dropping %d note(s): %s", book_path, len(inserts), exc)`) then `return 0`. Second pass (separate commit): add backslash-escape FIRST in `format_tuple_text` (`:167`): `s = s.replace("\\","\\\\").replace("\n","\\n").replace("\r","\\r")` to kill the root cause; verify byte-stability after.
  **Guard:** pytest feeding a note body with a raw backslash before a non-escape char and asserting the batch is NOT dropped (or, if dropped, logs an error).
  **Build path:** No (ingest/promote path). KJV byte-stable.

### Phase 2 — Stale-cache correctness & guard hardening (additive, no behavior change)

- [ ] **HIGH — Build cache key omits all pipeline scripts except `build_edition.py`** — `scripts/core/build_cache.py:230-236`. `build_one` calls `matter_pages`, `resync_marker_glyphs`, `epub_utils`, `build_epub` — none hashed → edits serve stale EPUBs.
  **Fix:** replace Item 9 with an explicit `_PIPELINE_SCRIPTS` list hashing `build_edition.py`, `matter_pages.py`, `epub_utils.py`, `resync_marker_glyphs.py`, `build_epub.py`, `apply_style.py`, `style_config.py`. **Do NOT** use a `scripts/**/*.py` glob (would spuriously bust on test/migration edits).
  **Guard:** pytest asserting `compute_cache_key` changes when each listed script's hash changes (parametrized).
  **Build path:** Yes (cache only — output bytes unchanged). Byte-stable; only invalidation behavior changes.

- [ ] **MED — Cache key omits `content/themes/*.css`** — `scripts/core/build_cache.py:171-178`. Theme CSS read live at `build_edition.py:2798-2803`, not in `epub_working/`, not hashed.
  **Fix:** extend the theme block to also `parts.append((f"theme_css:{theme_id}", _hash_file(_CONTENT/"themes"/f"{theme_id}.css")))`.
  **Guard:** cache-key pytest covering theme CSS change. **Build path:** Yes (cache only) — byte-stable.

- [ ] **LOW — Cache key omits `content/source_dates.yaml`** — `scripts/core/build_cache.py:120-271`. `compute_time_filtered_html_ref_ids` reads it; latent until first real `time_filter_ceiling`.
  **Fix:** after line 169, `parts.append(("source_dates.yaml", _hash_file(_CONTENT/"source_dates.yaml")))`. Add only this file (traditions/customization YAML covered transitively via the edition record).
  **Guard:** fold into the same cache-key pytest. **Build path:** Yes (cache only) — byte-stable.

- [ ] **LOW — `bookcode_canonical` lint omits versification/extraction maps** (★BUGCLUSTER class) — `scripts/lint_rules.py:1995-2006`. Missing `versification.SWETE_BOOK_TO_CODE`, `versification._NT_BOOK_TO_CODE`, `extract_wlc_morphhb.OSIS_BOOK_TO_CODE` — all produce translation-file names; a legacy alias would silently misname a popup-source file.
  **Fix:** add the three `(module, name)` tuples to `map_specs`; extend `tests/test_scripts.py::TestBookCodeMaps` (`BOOK_CODE_MAPS` line 8397 + `_maps()` line 8405) to cover them. All current values canonical → zero new failures.
  **Guard:** this IS the guard — a **commit-time lint_rules check**, preferred over pytest-only since this drift recurs every ingest. **Build path:** No.

### Phase 3 — Behavior-changing correctness fixes (regen + `git diff` proof)

- [ ] **MED — `find_aside_insertion_point` misorders cross-chapter asides in Strategy-B** — `scripts/inject.py:631`. Reachable on non-ascending re-injection.
  **Fix:** `precedes = existing_ch < ch or (existing_ch == ch and (existing_v, existing_s) < target)`. Strategy-A unaffected (`existing_ch == ch` always).
  **Guard:** pytest re-injecting a Strategy-B book where a later chapter's aside already exists; assert new lower-chapter aside lands before it.
  **Build path:** touches `epub_working` mutation → after fix run `test_nested_anchors` + `check_nested_anchors --fix`; prove KJV byte-stability via regen + `git diff`.

- [ ] **MED — Copyright/About annotation count ignores tradition/time filters** — `scripts/matter_pages.py:131-132,364-365`. `catholic-study` count inflated vs shipped notes.
  **Fix:** add `annotation_count_override: int|None = None` to `inject_copyright_page`/`inject_about_page` (+ thread through `_about_specs_for_edition`); in `build_edition.py:2995-2998` pass `total_for_edition(edition_id) - len(disabled_html_ref_ids)` when `disabled_html_ref_ids` else `None`.
  **Guard:** pytest asserting `catholic-study` printed count == matrix total − disabled count.
  **Build path:** Yes — **`override=None` keeps all 9 KJV editions on the unchanged code path (byte-stable)**; only filtered editions change. Prove via KJV regen + `git diff`.

- [ ] **MED — `api_save_edition` baseline ignores phase/AI gates → corrupts `disabled_kinds`** — `scripts/api/editions.py:250-253`. Confirmed fired on `evangelical-reformed` (phase3 `dist-allegorical`/`dist-mystical` wrongly in `disabled_kinds`).
  **Fix:** add `config.category_baseline_kinds(edition, all_kinds)` to `scripts/core/config.py` (phase + AI gated, NO explicit-override layer) and call it at `editions.py:250-251`. Additive new public fn; build path uses `enabled_kind_codes`, not this → KJV byte-stable.
  **Guard:** pytest asserting a `max_phase: phase2` edition does NOT list phase3 kinds in `disabled_kinds` after save round-trip.
  **Build path:** No (web API path).

### Phase 4 — Concurrency & low-severity correctness

- [ ] **LOW — `_CACHED_CONN` reset outside rebuild lock races concurrent `connection()`** — `scripts/core/corpus_index.py:602-610` (under `ThreadingHTTPServer`). Closes a connection another thread just obtained → `ProgrammingError`.
  **Fix:** move the `_CACHED_CONN` reset block INSIDE `with _acquire_rebuild_lock():` (after line 600); hoist its `global` to top of `rebuild()`. Do NOT add a separate `_conn_lock`. **Build path:** No.

- [ ] **MED — Note saves invalidate corpus_index but not `compute_matrix` singleton** — `scripts/core/notes_io.py:114-135`. Matrix view stale until restart.
  **Fix:** inside `_invalidate_corpus_index_if_notes_file`, lazy-import `matrix` and call `compute_matrix.cache_clear()` right after `corpus_index.invalidate()` (mirrors `api/editions.py`/`api/customize.py`). **Build path:** No.

- [ ] **LOW — `cross_refs_stripped` overcounts via `re.subn` semantics** — `scripts/build_edition.py:2180-2193`. `subn` counts all matches, not strippings.
  **Fix:** use `nonlocal` counters incremented only in the `return visible` branches of `_check_anchor`/`_check_file_only`; assign those to the stat. Cosmetic (stat not surfaced) — low urgency. **Build path:** stat only — byte-stable.

- [ ] **LOW — `label`/`cat_label` injected into EPUB HTML un-escaped** — `scripts/inject.py:216-220`. `build_aside` interpolates `label` raw (body is sanitized, label is not).
  **Fix:** `safe_label = html.escape(str(label or ""))`, `safe_cat_label = html.escape(str(cat_label or ""))`; use them at lines 219-220.
  **Guard:** pytest with `label="<script>"` asserting escaped output.
  **Build path:** Yes — KJV labels are plain ASCII → **byte-identical**; prove via regen + `git diff`.

- [ ] **LOW — `trusted_html` claim has no ingest-time enforcement** — `scripts/core/popup_versions.py:132-138` (`lxx-greek`, `greek-nt`).
  **Fix:** add a guard loop in `extract_lxx_swete.write_translation` (after line 173) and `extract_byzantine_nt.write_translation` (after line 98) raising `ValueError` if any verse contains `< > &`. Purely additive safety net. **Build path:** No.

- [ ] **LOW — `url_override` bypasses PD-sources allowlist at validation time** — `scripts/api/sources.py:163-186`. Relies solely on runtime `SSRFBlockedError`.
  **Fix:** add defense-in-depth `_check_allowlist(url_override, DEFAULT_PD_SOURCES_ALLOWLIST)` before constructing the one-off Source, returning `ssrf_blocked` on failure. (Local single-user app — defense-in-depth, not a hosting-hardening flag.) **Build path:** No.

### Phase 5 — At-scale driver dedup & test/doc hygiene

- [ ] **MED — Four at-scale drivers share append-only `write_queue` with no same-run dedup** — `run_naves_at_scale.py:40-69`, `run_torrey_at_scale.py:41-67`, `run_xref_at_scale.py:40-68`, `run_ethiopian_at_scale.py:49-78`. Re-run before promote → duplicate candidates promoted as distinct notes.
  **Fix:** in each, mirror `run_kenyon_at_scale.py:64-77` dedup on `(verse, kind, draft_body)` with a `seen` set + `return None` when nothing new. Do NOT centralize into `at_scale_base.py` (docstring documents driver-local-by-design). **Build path:** No.

- [ ] **HIGH(test) — Arc-close share-pin violates RULES §8.1** — `tests/test_ethiopian_gamma4.py:8534-8556`. `test_..._block_share_floor` uses `share >= 0.38` in the γ.4.8.F arc-close class.
  **Fix:** rename to `test_tewahedo_distinctive_canonical_block_count_milestone` and replace with an absolute-count assertion (`block >= 600` via `Counter(e.father ...)`), mirroring the 1En conversion at lines 1512-1531. Test-file only. **Build path:** No.

- [ ] **LOW(test) — `test_cyril_remains_plurality_leader_at_arc_close` doesn't guard Ephrem/1 Enoch** — `tests/test_ethiopian_gamma4.py:7014-7037` (ω.41 §1 invariant).
  **Fix:** replace hand-rolled loop with a `Counter` checking all four challengers (Jubilees, Athanasius, 1 Enoch, Ephrem), mirroring the γ.4.8.F pattern. **Build path:** No.

- [ ] **LOW(test) — Tautological `hits >= 0` lru_cache test** — `tests/test_canonical_verse_counts.py:137-146` (violates S7/S8).
  **Fix:** `cache_clear()`, call `canonical_book_shape("gen")` twice (miss + hit), assert `info.hits >= 1`. **Build path:** No.

- [ ] **LOW(test) — Redundant `chapters_collated >= 0`** — `tests/test_manuscript_kings.py:67`, superseded by `>= 1` on line 69.
  **Fix:** delete line 67 only. **Build path:** No.

- [ ] **LOW(debt) — `build_edition.py` redefines 6 ANSI constants from `core/ui.py`** — `scripts/build_edition.py:92-97`.
  **Fix:** replace with `from scripts.core.ui import GREEN, RED, YELLOW, DIM, BOLD, RESET  # noqa: E402`. **Build path:** No (console only).

- [ ] **LOW(debt) — 3 manuscript-at-scale drivers redefine ANSI constants** — `run_manuscript_collation_at_scale.py:100-103`, `run_manuscript_transcribe_at_scale.py:45-48`, `run_manuscript_review_at_scale.py:59-63` (review needs `YELLOW` too).
  **Fix:** import from `at_scale_base`. NOTE: these are *driver* scripts, not marathon-core (`manuscript_*.py`/`po_vision_store.py`/`content/manuscript/**` untouched). **Build path:** No.

### Phase 6 — Documentation truth-record (no code, no build)

- [ ] **MED — `mint-8-fixes-plan.md` Status says "Not yet started"** — `docs/superpowers/plans/2026-05-31-mint-8-fixes-plan.md:3`. Update to `COMPLETE — all batches 1–3 shipped (852ed8a4/cf05d8e3/8d44ff1f); byte-gate PASSED; lint 28✓; NEXT = convergence re-audit. H5+M8 deferred by design.`
- [ ] **MED — INDEX rows stale** — `docs/superpowers/INDEX.md:13-14`. Update BOTH plan Status headers (fixes-plan line 3 + `2026-05-31-mint-8-audit-plan.md:2`) AND the matching INDEX cells; run `check_superpowers_coherence` after to confirm green.
- [ ] **LOW — REPO_MAP plan/notes counts** — `dev/REPO_MAP.md:19`. `23`→`26` plans; add `notes/` subdir (holds `2026-05-28-d2-source-readiness.md`, `2026-05-31-mint-8-findings.md`, `...-audit-raw.json`).
- [ ] **LOW — `_replace_verse_popup_translation` MATRIX_MAP trace inaccurate** — `dev/MATRIX_MAP.md:107`. Active path is `_apply_popup_languages_and_translation`; note the standalone fn is superseded (kept for its 5 tests). Doc-only.
- [ ] **INFO — REPO_MAP test count** — `dev/REPO_MAP.md:17`. `169`→`178` (or durable `170+`).
- [ ] **INFO — REPO_MAP §dev omits SESSION_PLAYBOOK.md** — `dev/REPO_MAP.md:48`. Insert `SESSION_PLAYBOOK.md (session lifecycle + verification gate commands)`.
- [ ] **INFO — `render_coverage.py` docstring falsely says Patrologia books pending** — `scripts/render_coverage.py:12-15,156,250,267`. Ingest shipped τ.6.x.5.x; update docstring/comment/summary-key to "rendered". Doc-only (coverage script not in build pipeline).

## Optimization decisions

| Area | Verdict | Recommendation |
|---|---|---|
| Ge'ez/Amharic Exodus popups (`ex.py`→`exo.py`) | **Change (functional bug — see Phase 1)** | Mislabeled as "optimization"; it is silent data loss. Rename in all 4 dirs; add ingest-boundary alias. |
| `filter_html` ρ.1 per-ID regex loop (`build_edition.py:1034-1052`) | **Change** | Hoist a single combined alternation regex into `build_one()` before the file loop (2 compiles/edition vs 2N×61); cap alternation groups at ~500 IDs for N>2000. Byte-identical output. |
| `_resolve_popup_languages` re-decode per vnote (`build_edition.py:759-786`) | **Change** | Hoist `decode_per_book_languages` + a `_lang_cache` above the `_process` closure (mirrors `book_active_cache`). Byte-stable; keep public fn for tests. |
| `is_output_current` mtime guard omits notes corpus (`build_edition.py:1943-1965`) | **Change** | Add per-file `notes_dir.glob("*.py")` to watched sources so direct `build_edition.py` invocations rebuild after a notes edit. |
| `batch_insert_notes` dedup ignores `attribution` (`promote.py:355`) | **Change** | Store `(body, normalized_attribution)` pairs in `existing_bodies` so attribution-repair re-promotes; contract-match `note_already_exists`. |
| `cross_refs_stripped` overcount (`build_edition.py:2180-2193`) | **Change (cosmetic)** | `nonlocal` counter in stripping branch only. Stat not surfaced → low urgency; fold into Phase 4. |
| `lint_rules.check_render_coverage_no_regression` duplicates `_BOOK_ALIASES` logic | **Change** | Call `render_coverage._list_rendered(ed_dir)` instead of raw stems; expected sets use canonical `"exo"`. Removes 2-place drift. |
| `render_coverage.run_all()` omits `-en` back-translation dirs | **Change (lint side)** | Add `-en` expected sets to the lint check ONLY; do NOT add to `run_all()` (geez-specific track categories would emit spurious "missing"). |
| Shared AI detector mutates `last_usage` across threads (`run_ai_xrefs_at_scale.py:151-165`, `run_ai_notes_at_scale.py:149-165`) | **Change** | Move `detector = detector_factory()` inside `_work` (per-thread client); shared lru_cache'd `_anthropic_client()` pool stays. `workers=1` default → zero current regression. |
| Vision-transcription marathon method (Esther/Kings-Samuel) | **Confirmed-optimal** | MAX-1-heavy-agent, tight crops ≤1568px, per-step commits, AGENT path (no paid API budget). One evolutionary add: a single medium-weight synthesis agent over 4–6 completed pages' JSON to catch cross-page glyph drift. **Marathon-core — no edits.** |
| ~10 at-scale driver shape + `at_scale_base` | **Confirmed-optimal** | Per-driver `write_queue` semantics (append / kind-replace / hash-dedup) are load-bearing. Optional future `append_candidates(... dedup_key_fn=...)` helper to absorb kenyon's 3rd variant; defer until a natural edit touches these files. |

## Constraints carried

- **Marathon core is OFF-LIMITS** — no edits to `scripts/build_standalone.py`, `scripts/core/manuscript_*.py`, `scripts/core/po_vision_store.py`, `content/manuscript/**`, `content/translations/sources/patrologia/**`, `GAPS/`. (The 3 manuscript-at-scale *drivers* in Phase 5 are launchers, not core.)
- **9 KJV editions MUST stay byte-stable.** Every build-path fix above is additive and inert when its trigger (tradition/time filter, theme, override) is unset. Prove zero-output-change per build-path fix via regen + `git diff` on the 9 KJV outputs; run the byte-stability gate + `epubcheck` before each ship. After any `epub_working` mutation (Phase 3 inject fix) run `test_nested_anchors` + `check_nested_anchors --fix`.
- **Schema changes additive only** — new params default to back-compat (`annotation_count_override=None`); byte-identical when unset.
- **Atomic writes** — all corpus/edition writes go through `notes_io.atomic_write`/`ensure_backup`; cache-invalidation fixes only add `cache_clear()`, no write-path changes.
- **No paid API** — all AI work stays on the AGENT path; optimization recs introduce no SDK/script-path API calls.
- **5-leg save per phase** — local commit (save.ps1) + `git push origin` (GitLab) + `git push github` + `git bundle` to E: + copy to F:; `ruff format` regenerated files first; verify `git log`/`git status` before claiming saved. Prefer commit-time `lint_rules` guards (Phase 2 book-code maps) over pytest-only for ingest-recurring invariants.