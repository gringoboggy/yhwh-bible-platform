# mint-9 deep-audit — Round 2 (convergence re-audit) findings

**Status:** Round-2 audit COMPLETE (record/reference). Convergence loop: NOT converged — 45 survivors. Phased plan → `../plans/2026-05-31-mint-9-fixes-plan.md`. Raw: `2026-05-31-mint-9-audit-raw.json`.

> Generated 2026-05-31 by `.claude/workflows/deep-audit.js` round 2 (depth=deep, 14 dimensions). Run: **99 agents · ~4.67M subagent tokens · ~3.2 h** (`wf_e5e7a0d6-24a`).

> **66 deduped → 45 survivors / 21 refuted.** Severity (calibrated): high 6 · medium 8 · low 25 · info 6.

> Round-1 (mint-8) findings + the batch-1–3 fixes that shipped against them: `2026-05-31-mint-8-findings.md`. Compare against that to separate genuinely-new findings from deferred-by-design re-surfacers.


## Survivor index

| # | Sev | Dimension | Title | Location |
|---|-----|-----------|-------|----------|
| 1 | HIGH | byte-stability | Build cache key omits all pipeline script dependencies except build_edition.py itself | `YHWH v2.4/scripts/core/build_cache.py:230-236` |
| 2 | HIGH | correctness | _iter_note_ref_traditions and _iter_note_ref_attribution_years silently skip notes in Strategy-B books without id_prefix, causing tradition/time filters to never disable those notes | `YHWH v2.4/scripts/build_edition.py:130-132` |
| 3 | HIGH | correctness | batch_insert_notes silently drops entire batch on post-splice SyntaxError | `YHWH v2.4/scripts/promote.py:388-392` |
| 4 | HIGH | data-validity | Non-canonical book code 'ex' in geez-tewahedo/ex.py and amharic-tewahedo/ex.py silently orphans all Exodus verse data from canonical lookups | `YHWH v2.4/content/translations/geez-tewahedo/ex.py:24` |
| 5 | HIGH | opt-render | Ge'ez/Amharic Exodus popup content is silently inaccessible — ex.py vs exo.py filename mismatch | `YHWH v2.4/scripts/core/translations.py:54-55` |
| 6 | HIGH | tests | Arc-close class uses a share-based pin violating RULES §8.1 anti-pattern | `YHWH v2.4/tests/test_ethiopian_gamma4.py:8534-8556` |
| 7 | MEDIUM | byte-stability | Build cache key omits content/themes/*.css — theme CSS changes produce stale EPUBs | `YHWH v2.4/scripts/core/build_cache.py:171-178` |
| 8 | MEDIUM | byte-stability | Copyright page and About page embed matrix annotation count that ignores tradition/time filters — displayed count diverges from actual shipped notes | `YHWH v2.4/scripts/matter_pages.py:131-132, 364-365` |
| 9 | MEDIUM | code-debt | Four at-scale drivers share byte-identical append-only write_queue with no same-run dedup, causing silent candidate duplication on re-run | `YHWH v2.4/scripts/run_naves_at_scale.py:40-69` |
| 10 | MEDIUM | concurrency-caching | Note saves invalidate corpus_index but not compute_matrix singleton — matrix view stays stale | `YHWH v2.4/scripts/core/notes_io.py:114-135` |
| 11 | MEDIUM | correctness | find_aside_insertion_point: wrong 'precedes' logic places new asides after later-chapter asides in Strategy-B shared sections | `YHWH v2.4/scripts/inject.py:631` |
| 12 | MEDIUM | cross-module | api_save_edition baseline ignores phase/AI gates, corrupting disabled_kinds for max_phase-limited editions | `YHWH v2.4/scripts/api/editions.py:250-253` |
| 13 | MEDIUM | docs | INDEX.md two stale rows show mint-8 fixes 'NOT yet started' and audit 'NEXT = implement fixes' | `YHWH v2.4/docs/superpowers/INDEX.md:13-14` |
| 14 | MEDIUM | docs | mint-8-fixes-plan.md Status header says 'Not yet started' — all three batches shipped | `YHWH v2.4/docs/superpowers/plans/2026-05-31-mint-8-fixes-plan.md:3` |
| 15 | LOW | byte-stability | `filter_books_for_canon` Pass 1.5 TOC-block removal loop uses unsorted `tmp.glob()` — deterministic only because each file's output is independent, but the pattern is fragile | `YHWH v2.4/scripts/build_edition.py:2129, 2156, 2165, 2210` |
| 16 | LOW | byte-stability | `_replace_verse_popup_translation` is documented as 'NOT YET WIRED INTO THE BUILD' but MATRIX_MAP traces `popup_translation` → that function | `YHWH v2.4/scripts/build_edition.py:607-609` |
| 17 | LOW | byte-stability | `build_cache.compute_cache_key` does not hash `content/source_dates.yaml` — cache serves stale EPUBs if that file changes while an edition has `time_filter_ceiling` set | `YHWH v2.4/scripts/core/build_cache.py:120-271` |
| 18 | LOW | code-debt | build_edition.py locally redefines 6 ANSI color constants already present in scripts/core/ui.py | `YHWH v2.4/scripts/build_edition.py:92-97` |
| 19 | LOW | code-debt | run_manuscript_collation_at_scale.py locally redefines ANSI color constants instead of importing from at_scale_base | `YHWH v2.4/scripts/run_manuscript_collation_at_scale.py:100-103` |
| 20 | LOW | concurrency-caching | _CACHED_CONN reset in rebuild() is outside the rebuild lock — race with concurrent connection() calls in ThreadingHTTPServer | `YHWH v2.4/scripts/core/corpus_index.py:602-610` |
| 21 | LOW | correctness | filter_books_for_canon: cross_refs_stripped counter overcounts by including kept (non-stripped) link matches | `YHWH v2.4/scripts/build_edition.py:2180-2193` |
| 22 | LOW | correctness | filter_books_for_canon: cross_refs_stripped stat grossly overcounted via re.subn semantics | `YHWH v2.4/scripts/build_edition.py:2180-2193` |
| 23 | LOW | cross-module | bookcode_canonical lint rule does not screen versification.SWETE_BOOK_TO_CODE or _NT_BOOK_TO_CODE | `YHWH v2.4/scripts/lint_rules.py:1995-2006` |
| 24 | LOW | cross-module | bookcode_canonical lint guard does not screen translation-extraction book-code maps (SWETE_BOOK_TO_CODE, _NT_BOOK_TO_CODE, OSIS_BOOK_TO_CODE) | `YHWH v2.4/scripts/lint_rules.py:1995-2006` |
| 25 | LOW | cross-module | test_cyril_remains_plurality_leader_at_arc_close (γ.4.9.D) does not guard against Ephrem or 1 Enoch exceeding Cyril | `YHWH v2.4/tests/test_ethiopian_gamma4.py:7014-7037` |
| 26 | LOW | docs | REPO_MAP docs/superpowers plan count stale: claims 23, actual is 26 | `YHWH v2.4/dev/REPO_MAP.md:19` |
| 27 | LOW | docs | REPO_MAP docs/superpowers/ entry omits the notes/ subdirectory | `YHWH v2.4/dev/REPO_MAP.md:19` |
| 28 | LOW | opt-build | is_output_current mtime guard omits notes corpus — stale EPUB served when build_edition.py run directly after notes edit | `YHWH v2.4/scripts/build_edition.py:1943-1965` |
| 29 | LOW | opt-build | filter_html ρ.1 per-note-ID regex loop is O(\|disabled_ids\| × \|text\|) — degrades when tradition-filter produces large disabled sets | `YHWH v2.4/scripts/build_edition.py:1034-1052` |
| 30 | LOW | opt-build | _resolve_popup_languages decodes per_book_languages on every vnote aside — redundant parse inside tight regex callback | `YHWH v2.4/scripts/build_edition.py:759-786` |
| 31 | LOW | opt-ingest | `batch_insert_notes` dedup checks only `body`, not `attribution` — prevents attribution repair on previously-promoted notes | `YHWH v2.4/scripts/promote.py:355` |
| 32 | LOW | opt-render | render_coverage.run_all() omits the -en back-translation directories from coverage monitoring | `YHWH v2.4/scripts/render_coverage.py:235` |
| 33 | LOW | opt-render | render_coverage.py module docstring falsely states Patrologia books are patrologia_pending | `YHWH v2.4/scripts/render_coverage.py:12-15` |
| 34 | LOW | opt-vision | render_coverage._list_rendered normalises stems via _BOOK_ALIASES but lint_rules.check_render_coverage_no_regression duplicates its own expected-set logic without normalisation — coherence debt | `YHWH v2.4/scripts/lint_rules.py:948–1070` |
| 35 | LOW | security | url_override bypasses the PD-sources domain allowlist at validation time, relying solely on http.get's runtime SSRFBlockedError to block non-allowlisted hosts | `YHWH v2.4/scripts/api/sources.py:163-186` |
| 36 | LOW | security | trusted_html claim for lxx-greek and greek-nt has no ingest-time enforcement — HTML-special chars would be emitted raw | `YHWH v2.4/scripts/core/popup_versions.py:132-138` |
| 37 | LOW | security | Note label field injected into EPUB HTML without HTML-escaping in build_aside() | `YHWH v2.4/scripts/inject.py:216-220` |
| 38 | LOW | tests | Tautological lru_cache test: `hits >= 0` can never fail | `YHWH v2.4/tests/test_canonical_verse_counts.py:137-146` |
| 39 | LOW | tests | Redundant tautological assertion `chapters_collated >= 0` immediately superseded by `>= 1` | `YHWH v2.4/tests/test_manuscript_kings.py:67` |
| 40 | INFO | docs | REPO_MAP test-file count stale: claims 169, actual is 178 | `YHWH v2.4/dev/REPO_MAP.md:17` |
| 41 | INFO | docs | REPO_MAP §dev omits dev/SESSION_PLAYBOOK.md | `YHWH v2.4/dev/REPO_MAP.md:48` |
| 42 | INFO | opt-build | cross_refs_stripped build stat overcounts — subn returns total matches, not just strippings | `YHWH v2.4/scripts/build_edition.py:2180-2193` |
| 43 | INFO | opt-ingest | Ingest pipeline orchestration: CONFIRM-OPTIMAL — the ~10 driver shape is the right architecture | `YHWH v2.4/scripts/core/at_scale_base.py:1-143` |
| 44 | INFO | opt-ingest | Shared AI detector instance across parallel threads mutates `last_usage` non-atomically | `YHWH v2.4/scripts/run_ai_xrefs_at_scale.py:151-165` |
| 45 | INFO | opt-vision | CONFIRMED OPTIMAL: Vision-transcription marathon method (Patrologia Esther / Kings-Samuel) — MAX-1-heavy, tight crops, per-step commits, AGENT path | `YHWH v2.4/docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md:` |

## Detailed survivors

### 1. [HIGH] Build cache key omits all pipeline script dependencies except build_edition.py itself

- **Dimension:** byte-stability  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/core/build_cache.py:230-236`
- **Evidence:** Item 9 of compute_cache_key hashes only `scripts/build_edition.py`: `parts.append(("build_edition.py", _hash_file(_REPO / "scripts" / "build_edition.py")))`. Yet build_one imports and calls: `from scripts.matter_pages import inject_copyright_page, inject_back_matter, render_topical_index_page, ...` (build_edition.py lines 66-88), `from scripts.resync_marker_glyphs import renumber_markers` (line 2844), `from scripts.epub_utils import _resolve_publishing, load_canons` (lines 61-65), and `from scripts import build_epub` (line 3015). None of these modules are hashed. A change to matter_pages.py (which generates the copyright page, sources page, symbol legend, topical index, reading-plans page) or resync_marker_glyphs.py (which renumbers every inline marker) leaves the cache key unchanged, so cache_lookup returns the stale cached EPUB and the next build call returns it without rebuilding.
- **Fix:** In `YHWH v2.4/scripts/core/build_cache.py`, replace Item 9 (lines 230-236) with an explicit list covering all pipeline scripts that contribute to EPUB output:

```python
# 9. The build pipeline source itself — code changes invalidate.
#    Hash every script whose output directly affects the EPUB bytes.
_PIPELINE_SCRIPTS = [
    "scripts/build_edition.py",
    "scripts/matter_pages.py",
    "scripts/epub_utils.py",
    "scripts/resync_marker_glyphs.py",
    "scripts/build_epub.py",
    "scripts/apply_style.py",
    "scripts/style_config.py",
]
for _ps in _PIPELINE_SCRIPTS:
    parts.append((_ps, _hash_file(_REPO / _ps)))
```

Do NOT use `scripts/**/*.py` glob — that would include test files, migration tools, and manuscript scripts that have no effect on EPUB output, causing spurious cache misses on every unrelated script edit. The targeted list above covers exactly the import chain that `build_one()` calls before the cache-store point (lines 66-88 + 2844 + 3015). If new pipeline modules are added in future, they must be added to this list at the same time.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — Independently verified by reading the code:  1. `compute_cache_key` in `C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\core\build_cache.py` lines 230-236 hashes ONLY `scripts/build_edition.py` as the pipeline-code input (Item 9). Grep confirmed: no mention of `matter_pages`, `resync_marker_glyphs`, `epub_utils`, `apply_style`, or `style_config` anywhere in build_cache.py.  2. `build_edition.py` confirmed to import at module-level (lines 61-88): `scripts.epub_utils` (`_resolve_publishing`, `load_canons`) and `scripts.matter_pages` (copyright page, dedication page, symbol legend, abou

### 2. [HIGH] _iter_note_ref_traditions and _iter_note_ref_attribution_years silently skip notes in Strategy-B books without id_prefix, causing tradition/time filters to never disable those notes

- **Dimension:** correctness  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/build_edition.py:130-132`
- **Evidence:** In `_iter_note_ref_traditions` (and `_iter_note_ref_attribution_years` at line 326-328): `prefix = book.get('id_prefix'); if not prefix: continue`. Only 14 of 87 books have `id_prefix`. `2ch` (Strategy-B, bxx=b13) has no `id_prefix` but does have real notes (e.g., `content/notes/2ch.py` ch.1 v.1 `lang-hebrew`). When an edition declares `traditions_default` or `time_filter_ceiling`, these notes are never added to `disabled_html_ref_ids` — they survive the filter silently regardless of their tradition/attribution. The inject pipeline uses `bxx` as the fallback prefix for Strategy-B books, so the HTML ref-id is `ref-b130101`; the iteration needs to emit the same id to match it, but cannot without knowing the prefix.
- **Fix:** Apply the bxx fallback in both iterator functions, mirroring inject.py lines 674-677 exactly.

In `_iter_note_ref_traditions` (build_edition.py line 130-132), replace:
```python
prefix = book.get("id_prefix")
if not prefix:
    continue
```
with:
```python
prefix = book.get("id_prefix")
if not prefix:
    prefix = book.get("bxx")
if not prefix:
    continue
```

Apply the identical change in `_iter_note_ref_attribution_years` (lines 326-328).

Also apply the same fix at lines 2636-2638 (the `disabled_note_ids` block), which has the identical guard and the same gap.

No schema changes required; no KJV edition impact (the tradition/time filter functions short-circuit to empty set when `traditions_default` and `time_filter_ceiling` are both unset, so the iterator is never reached for standard editions). The fix is purely additive.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — All claims independently verified by reading the actual code:  1. `_iter_note_ref_traditions` (build_edition.py line 130-132) and `_iter_note_ref_attribution_years` (line 326-328) both do `prefix = book.get("id_prefix"); if not prefix: continue`, skipping any book without an `id_prefix` entry.  2. books.yaml confirms exactly 14 `id_prefix` entries, all on Strategy-A books EXCEPT 1ki (b10 "1k"), 2ki (b11 "2k"), and 1ch (b12 "1c") which are Strategy-B books that happen to have `id_prefix`. The remaining 73 Strategy-B books (e.g., 2ch/b13, man/b14, and the bulk of the canon) have no `id_prefix`. 

### 3. [HIGH] batch_insert_notes silently drops entire batch on post-splice SyntaxError

- **Dimension:** correctness  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/promote.py:388-392`
- **Evidence:** ```python
new_text = "".join(lines)
try:
    ast.parse(new_text)
except SyntaxError:
    return 0
```
When splicing new note tuples produces a SyntaxError (e.g. a body string containing an unescaped backslash that `format_tuple_text` emits verbatim), the function silently returns 0 — the entire batch of notes for that book is discarded with no log message and no exception raised. Callers in `batch_promote_xrefs.py` (line 85) and `extract_eastons_ccel.py` (line 186) test only `if n:` and print nothing on a 0 return, so the loss is invisible.
- **Fix:** Replace the bare `except SyntaxError: return 0` at lines 391-392 of `YHWH v2.4/scripts/promote.py` with:

```python
except SyntaxError as exc:
    logging.error(
        "batch_insert_notes: post-splice SyntaxError in %s — dropping %d note(s): %s",
        book_path,
        len(inserts),
        exc,
    )
    return 0
```

This is the minimal safe fix: purely additive, no control-flow change, no marathon core touch, KJV byte-stability preserved.

Optionally (as a second pass), add a `py_str` backslash-escape step in `format_tuple_text` at line 167 to prevent the root cause:

```python
s = s.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")
```

This must come FIRST (before newline replacement) to avoid double-escaping. This closes the underlying gap where a body containing a raw backslash before an unrecognised Python escape character can produce a SyntaxError on parse. Verify this doesn't corrupt existing notes by running the byte-stability test suite after the change.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — I read the code directly. The post-splice `SyntaxError` guard at lines 388-392 of `YHWH v2.4/scripts/promote.py` is confirmed exactly as the finder states: `except SyntaxError: return 0` with no logging and no exception raised. This is the path that fires when the *output* of `format_tuple_text` produces invalid Python after splicing — as opposed to the pre-parse guard at lines 299-309 which *does* log correctly.  Both callers treat `n == 0` as a silent no-op: `batch_promote_xrefs.py` line 86 gates on `if n:` (prints nothing on 0), and `extract_eastons_ccel.py` line 187 simply accumulates `add

### 4. [HIGH] Non-canonical book code 'ex' in geez-tewahedo/ex.py and amharic-tewahedo/ex.py silently orphans all Exodus verse data from canonical lookups

- **Dimension:** data-validity  ·  **kind:** find
- **Location:** `YHWH v2.4/content/translations/geez-tewahedo/ex.py:24`
- **Evidence:** Line 24: `BOOK = "ex"` (also in amharic-tewahedo/ex.py line 24). The canonical code throughout the project is `"exo"` (books.yaml, CANONICAL_BOOKS, kjv/exo.py, notes/exo.py). The translation loader in scripts/core/translations.py resolves `_book_path(translation, book_code)` as `f"{book_code}.py"`, so every call `tx.has_book("geez-tewahedo", "exo")` → looks for `exo.py` → False; `tx.get_verse("geez-tewahedo", "exo", ch, v)` → None. The 643 Ge'ez Exodus verses and ~947 Amharic Exodus verses on disk are invisible to all canonical-code lookups. The lint rule `check_render_coverage_no_regression` in lint_rules.py hardcodes `"ex"` in its expected sets so the pre-commit hook does not catch this. render_coverage.py has `_BOOK_ALIASES = {"ex": "exo", ...}` that remaps for coverage display only — the store loader has no such alias.
- **Fix:** 1. `git mv content/translations/geez-tewahedo/ex.py content/translations/geez-tewahedo/exo.py`
   `git mv content/translations/amharic-tewahedo/ex.py content/translations/amharic-tewahedo/exo.py`
   `git mv content/translations/geez-tewahedo-en/ex.py content/translations/geez-tewahedo-en/exo.py`
   `git mv content/translations/amharic-tewahedo-en/ex.py content/translations/amharic-tewahedo-en/exo.py`

2. In each renamed file, change `BOOK = "ex"` to `BOOK = "exo"` (line 24 in all four files).

3. In `scripts/lint_rules.py` lines 977 and 1006: replace `"ex"` with `"exo"` in `expected_geez` and `expected_amharic` sets.

4. In `scripts/render_coverage.py` line 51: remove the `"ex": "exo"` entry from `_BOOK_ALIASES` (it becomes redundant once the file is named `exo.py`).

5. In test files: update any assertion checking `BOOK == "ex"` (e.g. `tests/test_parallel_bible_tau7xb.py` line 164) to `BOOK == "exo"`. Do NOT update `ingested_book_codes: [ex]` in the `_meta.yaml` files and do NOT update tests that assert `ingested_book_codes == ["ex"]` (e.g. line 356 in test_parallel_bible_tau7xb.py) — these are historical provenance records of the ingest event, not runtime codes, and should remain accurate to what was originally ingested.

6. In `tests/test_parallel_bible_tau6x2j.py`, `test_parallel_bible_tau6x2m.py`, and `test_parallel_bible_tau6x2_geez_arc.py`: update string literals referencing `"ex"` as a book code (where used to probe `translations.has_book` or construct file paths) to `"exo"`. String literals used only to index the REGRESSION_FLOORS / EXPECTED_PHASES dicts that reference the historical record are fine to leave, but any assertion constructing `f"{book}.py"` file-existence checks with `"ex"` must become `"exo"`.

7. After all renames, run `ruff format` on the four renamed .py files and verify the test suite passes (excluding slow-tagged tests).
- **Verdict (2 skeptic[s]):** refuted=False conf=high — Independently verified all cited claims by reading the actual source files:  1. `BOOK = "ex"` at line 24 in both `content/translations/geez-tewahedo/ex.py` and `content/translations/amharic-tewahedo/ex.py` — confirmed. The same mismatch exists in `geez-tewahedo-en/ex.py` and `amharic-tewahedo-en/ex.py` (finder missed these two).  2. `books.yaml` declares `code: exo` for Exodus (line 21) — confirmed canonical code is `exo`.  3. `scripts/core/translations.py::_book_path()` at line 54-55 constructs the file path as `f"{book_code}.py"` with no aliasing. `has_book("geez-tewahedo", "exo")` → looks f

### 5. [HIGH] Ge'ez/Amharic Exodus popup content is silently inaccessible — ex.py vs exo.py filename mismatch

- **Dimension:** opt-render  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/core/translations.py:54-55`
- **Evidence:** `def _book_path(translation: str, book_code: str) -> Path:
    return TRANSLATIONS_DIR / translation / f"{book_code}.py"` — constructs the path verbatim from `book_code` without applying any alias. The EPUB uses code `exo` in every vnote aside (confirmed in `epub_working/index_split_005.html`: `id="vnote-exo-40-1"`). `translations.get_verse('geez-tewahedo', 'exo', ch, vs)` therefore looks for `content/translations/geez-tewahedo/exo.py` which does not exist. The actual file is `ex.py` (confirmed by glob). `render_coverage._BOOK_ALIASES` maps `ex→exo` for the inventory report, but that alias is never applied in `_book_path`. All four Tewahedo translation directories (`geez-tewahedo`, `amharic-tewahedo`, `geez-tewahedo-en`, `amharic-tewahedo-en`) have `ex.py`; none have `exo.py`. Result: every Ge'ez and Amharic Exodus verse popup silently returns `None` and falls back to English/KJV.
- **Fix:** The finder's proposed fix is correct but mislabeled as "optimization" — this is a functional bug. Execute:

1. Rename ex.py to exo.py in all four directories:
   - C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\content\translations\geez-tewahedo\ex.py → exo.py
   - C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\content\translations\amharic-tewahedo\ex.py → exo.py
   - C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\content\translations\geez-tewahedo-en\ex.py → exo.py
   - C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\content\translations\amharic-tewahedo-en\ex.py → exo.py

2. Update the module docstring header in each renamed file from "Book: ex" to "Book: exo" (cosmetic, non-functional but consistent with KJV convention).

3. Add "ex": "exo" to _BOOK_CODE_ALIASES in scripts/core/sources_base.py:54 so future re-ingests of legacy-coded source data normalize correctly at the ingest boundary.

4. Optionally remove the now-redundant "ex": "exo" from render_coverage._BOOK_ALIASES at scripts/render_coverage.py:51 — once exo.py exists, _list_rendered will find it directly. Keeping it is harmless defense-in-depth.

No KJV byte-stability risk: the 9 KJV editions use content/translations/kjv/exo.py which is already correctly named and untouched by this change.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Independently confirmed by reading every cited file. The chain of evidence:  1. EPUB HTML uses canonical code `exo` in vnote IDs: `id="vnote-exo-40-1"` etc. — confirmed in epub_working/index_split_005.html.  2. `_VNOTE_ASIDE_RE` in build_edition.py:585 captures group 2 as `([a-z0-9]+)`, so `book = "exo"` at lines 643/938.  3. `get_verse(translation_id, book, ch, vs)` at lines 648 and 953 passes `"exo"` directly — no aliasing before the call.  4. `_book_path` at translations.py:54-55 constructs `TRANSLATIONS_DIR / translation / f"{book_code}.py"` verbatim — no alias table.  5. All four affected

### 6. [HIGH] Arc-close class uses a share-based pin violating RULES §8.1 anti-pattern

- **Dimension:** tests  ·  **kind:** find
- **Location:** `YHWH v2.4/tests/test_ethiopian_gamma4.py:8534-8556`
- **Evidence:** ```python
def test_tewahedo_distinctive_canonical_block_share_floor(self):
    # ...
    share = block / total if total else 0.0
    assert share >= 0.38, ...
```
This is in `TestGamma48FArcClose`, which is the arc-close class for γ.4.8.F. RULES §8.1 says explicitly: "Anti-pattern: a share-pin in the arc-close class — the convention exists in part to replace the failure-prone share-pin with the durable count-milestone pattern." The current block count at arc-close is 192+200+212=604 entries. Any future voice-broadening wave that adds ~100 entries to another father voice would push `total` past 1590 and drop `share` below 38%, failing this test even though the absolute achievement (604 Tewahedo-distinctive entries) is perfectly preserved. The same pattern was already fixed for 1 Enoch at line 1512-1527 of the same file with an explicit note explaining the conversion.
- **Fix:** Replace the body of the existing method `test_tewahedo_distinctive_canonical_block_share_floor` in `TestGamma48FTier2AuditIntegration` (lines 8534-8556) in place — rename it and swap the share assertion for an absolute-count assertion:

```python
def test_tewahedo_distinctive_canonical_block_count_milestone(self):
    # §8.1 absolute-count milestone — NEVER a share pin (RULES §8.1;
    # feedback_share_pin_pattern). Share-pins break mechanically on every
    # voice-broadening wave even though the historical achievement is intact.
    # Cf. the 1En share→count conversion at line 1511-1531.
    # γ.4.8.F corpus state: Meqabyan 212 + Jubilees 200 + 1Enoch 192 = 604.
    all_entries = [e for verse_entries in self.ec._by_verse.values() for e in verse_entries]
    from collections import Counter
    counts = Counter(e.father for e in all_entries)
    meq = counts.get("Meqabyan (Ethiopian tradition)", 0)
    jub = counts.get("Jubilees (Ethiopian tradition)", 0)
    enoch = counts.get("1 Enoch (Ethiopian tradition)", 0)
    block = meq + jub + enoch
    assert block >= 600, (
        f"γ.4.8.F: Tewahedo-distinctive-canonical block must reach ≥600 entries "
        f"(Meqabyan {meq} + Jubilees {jub} + 1Enoch {enoch} = {block}); "
        f"supports v1.1 publisher-led uniqueness-angle anchor"
    )
```

This is a test-file-only change. No scripts, marathon core, or EPUB output is affected.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — Independently confirmed by reading the code and rules:  1. The offending code exists exactly as described. Lines 8534-8556 of `YHWH v2.4/tests/test_ethiopian_gamma4.py` contain `test_tewahedo_distinctive_canonical_block_share_floor` inside class `TestGamma48FTier2AuditIntegration`. It computes `share = block / total if total else 0.0` and asserts `share >= 0.38`.  2. RULES §8.1 (`dev/CLAUDE_PROJECT_RULES.md` lines 506-509) states: "Use a count milestone, NEVER a share threshold — share-pins break mechanically when later waves dilute the share even though the historical achievement is preserved

### 7. [MEDIUM] Build cache key omits content/themes/*.css — theme CSS changes produce stale EPUBs

- **Dimension:** byte-stability  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/core/build_cache.py:171-178`
- **Evidence:** Item 4 hashes `content/themes.yaml` (metadata only) when an edition uses a theme: `parts.append(("themes.yaml", _hash_file(_CONTENT / "themes.yaml")))`. But in build_one the actual theme CSS is read from disk and appended to the edition stylesheet: `theme_css = REPO_ROOT / 'content' / 'themes' / f'{theme_id}.css'` ... `theme_handle.write(theme_css.read_text(...))` (build_edition.py lines 2798-2803). The five files content/themes/{classic,scholarly,devotional,modern,school}.css are NOT inside epub_working/ (confirmed: no epub_working/themes* path exists) and are not hashed anywhere in compute_cache_key. A change to e.g. content/themes/classic.css leaves the cache key unchanged for all editions using theme=classic.
- **Fix:** In build_cache.py, extend the existing theme block (lines 171-178) to also hash the CSS file:

```python
# 4. themes.yaml when the edition uses one, plus the actual CSS.
theme_id = (edition.get("theme") or "").strip()
if theme_id:
    parts.append(("themes.yaml", _hash_file(_CONTENT / "themes.yaml")))
    parts.append((f"theme_css:{theme_id}", _hash_file(_CONTENT / "themes" / f"{theme_id}.css")))
```

Replace the existing `if (edition.get("theme") or "").strip():` block with the above. This refactors the theme_id extraction once (avoiding the double get()), hashes both the registry and the CSS file, and is fully additive — the `_hash_file` guard already returns `"<missing>"` for nonexistent files, so no extra guard is needed.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Independently verified by reading both files. In build_cache.py lines 171-178, when an edition declares a theme, only `themes.yaml` (the metadata registry) is hashed — the actual CSS file at `content/themes/{theme_id}.css` is never hashed. In build_edition.py lines 2797-2803, the build reads that CSS file from disk and appends it directly into the EPUB stylesheet (`stylesheet.css`). The five CSS files (`content/themes/{classic,scholarly,devotional,modern,school}.css`) do not exist under `epub_working/` (Glob confirmed zero matches for `epub_working/themes*`), so they are also not picked up by 

### 8. [MEDIUM] Copyright page and About page embed matrix annotation count that ignores tradition/time filters — displayed count diverges from actual shipped notes

- **Dimension:** byte-stability  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/matter_pages.py:131-132, 364-365`
- **Evidence:** inject_copyright_page (line 131): `annotation_count = _matrix.total_for_edition(edition_id)` and inject_about_page/_about_specs_for_edition (line 364): `annotation_count = _matrix.total_for_edition(edition_id)`. The matrix count applies only the kind+canon filter; it never applies the `traditions_default` filter (ψ.8.2-A) or the `time_filter_ceiling` filter (ψ.37-B). For `catholic-study`, which declares `traditions_default: [catholic]`, the matrix count includes cross-tradition and protestant-tradition notes that `compute_tradition_disabled_html_ref_ids` will strip from the EPUB. The printed count on the copyright page and About page is therefore inflated relative to what the reader actually receives.
- **Fix:** The finder's fix approach is correct. Implement it as follows:

1. In `scripts/matter_pages.py`, add an `annotation_count_override: int | None = None` parameter to both `inject_copyright_page` (line 123) and `inject_about_page` (line 480). When the override is not None, use it instead of the matrix total. Inside `_about_specs_for_edition`, accept and thread through an optional override similarly (or restructure so the caller passes it in directly to avoid re-calling the function).

2. In `scripts/build_edition.py` at line 2995–2998, compute the effective count before calling the inject functions:

```python
effective_annotation_count = (
    _matrix.total_for_edition(edition_id) - len(disabled_html_ref_ids)
    if disabled_html_ref_ids
    else None  # no override needed → inject functions use matrix (back-compat for 9 KJV editions)
)
inject_copyright_page(tmp, edition, version, annotation_count_override=effective_annotation_count)
inject_about_page(tmp, edition, version, annotation_count_override=effective_annotation_count)
```

This keeps all 9 KJV editions at `override=None` (code path unchanged, byte-stable) and corrects the displayed count for `catholic-study` and any future edition that uses tradition or time filtering. No marathon-core files are touched.
- **Verdict (2 skeptic[s]):** refuted=True conf=high — I read the actual code and data. The finding's structural claim is correct — `inject_copyright_page` (line 131) and `inject_about_page` (line 364) both call `_matrix.total_for_edition(edition_id)`, which counts enabled-kind notes without subtracting tradition-filtered or time-filtered IDs. However, the finding is a false alarm given the current corpus and edition config:  1. TIME FILTER: The only edition that sets `time_filter_ceiling` is `catholic-study`, and it is set to `null` (C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\content\editions.yaml line 138). `compute_time_filtered_html_ref

### 9. [MEDIUM] Four at-scale drivers share byte-identical append-only write_queue with no same-run dedup, causing silent candidate duplication on re-run

- **Dimension:** code-debt  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/run_naves_at_scale.py:40-69`
- **Evidence:** run_naves (L40-69), run_torrey (L41-67), run_xref (L40-68), and run_ethiopian (L49-78) each define a local write_queue that blindly appends all new candidates to the existing JSON without filtering by kind or deduplicating by (verse, kind, body). The at_scale_base.py docstring (L8-9) claims write_queue was 'deliberately NOT here — each driver has its own append/dedup/overwrite semantics,' but these four are functionally identical. By contrast run_kenyon deduplicates on (verse, kind, body) hash (run_kenyon L64-77) and run_hebrew/run_greek replace existing same-kind candidates. Re-running any of these four before promoting fills the candidate file with duplicate pending entries, each with a unique ID. promote.py's note_already_exists guard only catches notes already in the notes file, not duplicates within the candidate queue — so every duplicate candidate gets promoted as a distinct note.
- **Fix:** In each of the four drivers (run_naves_at_scale.py, run_torrey_at_scale.py, run_xref_at_scale.py, run_ethiopian_at_scale.py), update write_queue to mirror the dedup logic already in run_kenyon_at_scale.py lines 64-77. After loading existing candidates, build a seen set:

  seen = {(c.get('verse'), c.get('kind'), c.get('draft_body')) for c in existing}

Then filter new candidates before appending:

  new_dicts = []
  next_idx = len(existing) + 1
  for c in candidates:
      d = candidate_to_dict(c, next_idx)
      key = (d['verse'], d['kind'], d['draft_body'])
      if key in seen:
          continue
      seen.add(key)
      new_dicts.append(d)
      next_idx += 1
  if not new_dicts:
      return None  # idempotent

Do NOT modify at_scale_base.py or centralize write_queue there — the module docstring explicitly documents that write_queue is driver-local by design, and changing that contract would require updating all 10 drivers and the docstring. The per-driver fix is self-contained, safe, and mirrors the already-proven kenyon pattern.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — Independently verified by reading all cited files:  1. run_naves_at_scale.py L40-68, run_torrey_at_scale.py L41-67, run_xref_at_scale.py L40-68, and run_ethiopian_at_scale.py L49-78 all have byte-identical append logic: read existing candidates list, concatenate new candidates from current run, write back — no seen-set, no body-hash guard. Confirmed verbatim.  2. run_kenyon_at_scale.py L64-77 does implement a seen = {(verse, kind, draft_body)} guard, exactly as the finder states. The contrast is real.  3. promote.py's note_already_exists (L79-135) guards against duplicates already in the notes

### 10. [MEDIUM] Note saves invalidate corpus_index but not compute_matrix singleton — matrix view stays stale

- **Dimension:** concurrency-caching  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/core/notes_io.py:114-135`
- **Evidence:** `_invalidate_corpus_index_if_notes_file` calls `corpus_index.invalidate()` and `clear_load_notes_cache()` but never `matrix.compute_matrix.cache_clear()`. Because `compute_matrix` is `@lru_cache(maxsize=1)` (scripts/core/matrix.py line 328), the cached Matrix object is returned on every subsequent `/matrix` or `/api/search` request without re-executing its body, even though the underlying corpus_index has been fully invalidated. The note-save path (web_notes.api_save → write_book → notes_io.atomic_write → _invalidate_corpus_index_if_notes_file) therefore leaves the matrix stale until server restart. The edition-write paths in api/editions.py and api/customize.py do call compute_matrix.cache_clear(), but the note-save path does not.
- **Fix:** Inside `_invalidate_corpus_index_if_notes_file` in `YHWH v2.4/scripts/core/notes_io.py`, add a lazy import of `matrix` and call `cache_clear()` immediately after `corpus_index.invalidate()`:

```python
def _invalidate_corpus_index_if_notes_file(path: Path) -> None:
    try:
        if path.suffix == ".py" and path.parent.name == "notes":
            from scripts.core import corpus_index
            from scripts.core import matrix as matrix_mod  # add this

            corpus_index.invalidate()
            matrix_mod.compute_matrix.cache_clear()       # add this
            clear_load_notes_cache()
    except Exception:  # noqa: BLE001
        pass
```

This exactly mirrors the pattern already used in `scripts/api/editions.py` and `scripts/api/customize.py`. The lazy import is safe because `notes_io` has no top-level `matrix` import, avoiding any circular-import risk.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — Independently verified by reading the actual code. In `YHWH v2.4/scripts/core/notes_io.py` lines 114-135, `_invalidate_corpus_index_if_notes_file` calls `corpus_index.invalidate()` and `clear_load_notes_cache()` but has no `compute_matrix.cache_clear()` call. In `YHWH v2.4/scripts/core/matrix.py` lines 328-350, `compute_matrix()` is decorated `@lru_cache(maxsize=1)` and its body is a single call to `corpus_index.compute_matrix_indexed()`. Because `lru_cache` memoizes the return value, the body never re-executes after the first call — meaning that after a note save via `api_save → write_book → 

### 11. [MEDIUM] find_aside_insertion_point: wrong 'precedes' logic places new asides after later-chapter asides in Strategy-B shared sections

- **Dimension:** correctness  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/inject.py:631`
- **Evidence:** `precedes = existing_ch != ch or (existing_v, existing_s) < target` — when a new aside for chapter 3 is inserted and the shared notes-section already contains an aside for chapter 10 (existing_ch=10, ch=3), `existing_ch != ch` is True so `precedes=True`. The code then advances `insertion` past the chapter 10 aside, placing the chapter 3 aside AFTER it. Strategy-B uses a single per-file notes-section shared across all chapters, so this cross-chapter misordering is reachable whenever injection is not strictly chapter-ascending (e.g., re-injecting a book where some later chapters' notes already exist).
- **Fix:** The proposed fix is correct and safe. Change line 631 in C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\inject.py from:

  precedes = existing_ch != ch or (existing_v, existing_s) < target

to:

  precedes = existing_ch < ch or (existing_ch == ch and (existing_v, existing_s) < target)

This correctly treats only lower-chapter asides (or same-chapter lower-(verse,suffix) asides) as preceding the insertion point. Higher-chapter asides are no longer treated as preceding, so the new aside is placed before them (at m.start()). Strategy-A is unaffected because in Strategy-A existing_ch always equals ch (per-chapter sections), so the first disjunct is always False and the behavior is identical to before.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — I independently confirmed the bug by reading C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\inject.py lines 609–645.  The condition at line 631 is:   precedes = existing_ch != ch or (existing_v, existing_s) < target  For Strategy-B, `ensure_notes_section_b` (lines 374–409) creates a single shared `<aside class="notes-section">` per HTML file, not one per chapter. A Strategy-B file can contain multiple chapters (e.g. 1 Kings spans index_split_012/013/014.html, confirmed in books.yaml). So the shared section accumulates asides from all chapters in that file.  `find_aside_insertion_poi

### 12. [MEDIUM] api_save_edition baseline ignores phase/AI gates, corrupting disabled_kinds for max_phase-limited editions

- **Dimension:** cross-module  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/api/editions.py:250-253`
- **Evidence:** ```python
enabled_cats = set(edition.get("enabled_categories") or [])
baseline = {k["code"] for k in config.load_kinds() if k.get("category") in enabled_cats}
new_enabled_kinds = sorted(new_enabled_set - baseline)
new_disabled_kinds = sorted(baseline - new_enabled_set)
```
`baseline` includes ALL kinds whose category is in `enabled_categories`, with no phase gate. `new_enabled_set` (the payload from `api_apply_kind_to_all_editions` or the matrix UI) is already phase-filtered by `_enabled_kinds_for_edition`/`config.enabled_kind_codes`. Therefore `baseline - new_enabled_set` will include phase3 kinds (e.g. `comm-contextual`, `dist-allegorical`, `dist-mystical`) that the canonical resolver correctly excluded via the phase gate — writing them into `disabled_kinds` spuriously. Confirmed: `evangelical-reformed` has `max_phase: phase2` and enabled `dist` category; `dist-allegorical` and `dist-mystical` are both `phase: phase3` and appear in its `disabled_kinds`, consistent with this defect having already fired. When `max_phase` is later raised, the spurious `disabled_kinds` overrides the phase-gate rollback permanently.
- **Fix:** The fix must add phase and AI gates to `baseline` without incorporating `explicit_disabled`/`explicit_enabled` from the edition (which would break roundtrip fidelity for user overrides). The cleanest approach is to add a narrow public helper to `scripts/core/config.py`:

```python
def category_baseline_kinds(edition: dict, all_kinds) -> set[str]:
    """Phase- and AI-gated category default set, without explicit_enabled/disabled applied.

    Used by api_save_edition to compute the 'what category gives you by default'
    baseline so that only genuine user overrides land in enabled_kinds/disabled_kinds.
    Mirrors the gate order of enabled_kind_codes but skips the explicit-override layer.
    """
    enabled_cats = set(edition.get("enabled_categories") or [])
    max_phase = edition.get("max_phase")
    max_idx = _PHASE_ORDER[max_phase] if max_phase and max_phase in _PHASE_ORDER else max(_PHASE_ORDER.values())
    allow_ai = bool(edition.get("enable_ai_notes"))
    return {
        k["code"] for k in all_kinds
        if k.get("category") in enabled_cats
        and _PHASE_ORDER.get(k.get("phase", "legacy"), 99) <= max_idx
        and (k.get("code") not in AI_DRAFTED_KINDS or allow_ai)
    }
```

Then in `scripts/api/editions.py` lines 250-253, replace:
```python
enabled_cats = set(edition.get("enabled_categories") or [])
baseline = {k["code"] for k in config.load_kinds() if k.get("category") in enabled_cats}
```
with:
```python
baseline = config.category_baseline_kinds(edition, config.load_kinds())
```

This is additive (new public function in config.py), does not touch the marathon core, and keeps the 9 KJV editions byte-stable (the build path uses `enabled_kind_codes`, not `api_save_edition`).
- **Verdict (2 skeptic[s]):** refuted=False conf=high — The finding is confirmed by reading the actual code.  **What the code does (lines 250-253 of scripts/api/editions.py):** ```python enabled_cats = set(edition.get("enabled_categories") or []) baseline = {k["code"] for k in config.load_kinds() if k.get("category") in enabled_cats} new_enabled_kinds = sorted(new_enabled_set - baseline) new_disabled_kinds = sorted(baseline - new_enabled_set) ``` The `baseline` is built from category membership alone — no phase gate, no AI-gate.  **The divergence path is real and live:** In `api_apply_kind_to_all_editions` (lines 308-337), `current` is computed via

### 13. [MEDIUM] INDEX.md two stale rows show mint-8 fixes 'NOT yet started' and audit 'NEXT = implement fixes'

- **Dimension:** docs  ·  **kind:** find
- **Location:** `YHWH v2.4/docs/superpowers/INDEX.md:13-14`
- **Evidence:** Line 14: 'synthesized 2026-05-31, ready to execute; NOT yet started — the actionable backlog from the round-1 audit (39 grouped fixes + optimization decisions)'
Line 13: 'fixes-plan generated; NEXT = implement fixes → re-audit'

Both rows contradict the SESSION_STATE which confirms all three fix batches shipped. The INDEX is the first document a fresh session reads to understand project state. These two rows will cause a future session to skip directly to re-implementing already-shipped fixes.
- **Fix:** Update BOTH the plan file Status headers AND the INDEX rows (the INDEX is generated from those headers; fixing only the INDEX without the sources leaves a lint coherence violation or stale plan files):

1. `docs/superpowers/plans/2026-05-31-mint-8-fixes-plan.md` line 3 — replace the Status line with:
`**Status:** COMPLETE — all 3 batches shipped 2026-05-31 (commits 852ed8a4 / cf05d8e3 / 8d44ff1f); byte-stability gate PASSED; lint 28✓/0/0; NEXT = convergence re-audit (deep-audit round 2).`

2. `docs/superpowers/plans/2026-05-31-mint-8-audit-plan.md` line 2 — replace or append to the Status line so it reads:
`**Status:** ROUND 1 EXECUTED + FIXES COMPLETE 2026-05-31 — deep-audit.js built + run (106 agents, 57 verified findings); all fixes shipped in 3 batches; NEXT = convergence re-audit (deep-audit round 2).`

3. `docs/superpowers/INDEX.md` line 13 — update the Status cell to match the audit-plan's revised header (e.g. "ROUND 1 EXECUTED + FIXES COMPLETE 2026-05-31 ... NEXT = convergence re-audit").

4. `docs/superpowers/INDEX.md` line 14 — update the Status cell to match the fixes-plan's revised header (e.g. "COMPLETE — all 3 batches shipped 2026-05-31; NEXT = convergence re-audit").

After editing, run the `check_superpowers_coherence` lint to confirm INDEX rows and plan file headers are coherent and the guard stays green.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — Independently confirmed by reading three files:  1. `docs/superpowers/INDEX.md` lines 13-14: Line 13 reads "fixes-plan generated; NEXT = implement fixes → re-audit". Line 14 reads "synthesized 2026-05-31, ready to execute; NOT yet started". Both are stale.  2. `docs/superpowers/plans/2026-05-31-mint-8-fixes-plan.md` line 3: `**Status:** synthesized 2026-05-31 from the verified survivors... ready to execute. Not yet started.` — stale source header.  3. `docs/superpowers/plans/2026-05-31-mint-8-audit-plan.md` line 2: `**Status:** ROUND 1 EXECUTED 2026-05-31 — ... NEXT SESSION: implement the fixe

### 14. [MEDIUM] mint-8-fixes-plan.md Status header says 'Not yet started' — all three batches shipped

- **Dimension:** docs  ·  **kind:** find
- **Location:** `YHWH v2.4/docs/superpowers/plans/2026-05-31-mint-8-fixes-plan.md:3`
- **Evidence:** > **Status:** synthesized 2026-05-31 from the verified survivors of the mint-8 deep-audit round 1; ready to execute. Not yet started.

SESSION_STATE confirms batch-1 (852ed8a4), batch-2 (cf05d8e3), and batch-3 (8d44ff1f) all shipped and were verified. The superpowers_coherence lint only checks that a **Status:** header EXISTS — it does not verify that the text reflects reality. A future session reading the INDEX or this plan will believe the fixes haven't been implemented and will re-implement them.
- **Fix:** Change line 3 of YHWH v2.4/docs/superpowers/plans/2026-05-31-mint-8-fixes-plan.md from the current stale text to: `**Status:** COMPLETE — all fixes implemented across batches 1–3 (2026-05-31: 852ed8a4 / cf05d8e3 / 8d44ff1f); byte-stability gate PASSED; lint 28✓/0/0; epubcheck CLEAN; NEXT = convergence re-audit (deep-audit round 2). H5 + M8 deferred by design.` This is a docs-only edit; no code, no build path, no EPUB output is touched.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — Independently verified by reading both artifacts. The plan file at YHWH v2.4/docs/superpowers/plans/2026-05-31-mint-8-fixes-plan.md line 3 literally contains: `**Status:** synthesized 2026-05-31 from the verified survivors of the mint-8 deep-audit round 1; ready to execute. Not yet started.` SESSION_STATE.md line 3 unambiguously confirms all three batches shipped: "✅ MINT-8 FIXES BATCH-1 + BATCH-2 + BATCH-3 ALL SHIPPED & VERIFIED · convergence re-audit = next." with commits 852ed8a4 / cf05d8e3 / 8d44ff1f.  The lint guard at lint_rules.py:1376-1377 only checks `_SUPERPOWERS_STATUS_RX.search(hea

### 15. [LOW] `filter_books_for_canon` Pass 1.5 TOC-block removal loop uses unsorted `tmp.glob()` — deterministic only because each file's output is independent, but the pattern is fragile

- **Dimension:** byte-stability  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/build_edition.py:2129, 2156, 2165, 2210`
- **Evidence:** Four separate glob loops in `filter_books_for_canon` use `for f in tmp.glob("*.html"):` (without `sorted()`): Pass 1.5 TOC removal (line 2129), Pass 2 id_inventory build (line 2156), Pass 2 file processing (line 2165), Pass 3 orphan-aside removal (line 2210). The main filter loop in `build_one` at line 2846 and `apply_title_pages` at line 2543 are similarly unsorted. Python's `glob()` returns results in OS filesystem-enumeration order, which is undefined and can differ across filesystems (ext4 vs NTFS vs tmpfs). While each file is processed independently (no cross-file state mutations that feed back into the same pass), this is a known class of non-determinism that has bitten other passes in this codebase. The stats counters accumulated across the unsorted loop produce different per-file orderings in printed output, and any future change that introduces cross-file dependency (e.g., a shared accumulator whose value changes behaviour) would silently break byte-stability.
- **Fix:** The fix is correct and safe as stated: replace `for f in tmp.glob("*.html"):` with `for f in sorted(tmp.glob("*.html")):` at lines 2129, 2156, 2165, and 2210 in `filter_books_for_canon`, and at line 2846 in `build_one` and line 2543 in `apply_title_pages`. No other change is needed. This is a pure defensive hygiene change — zero output impact today, eliminates the latent risk if any future change introduces cross-file state, and matches the existing project pattern at lines 1574 and 1719.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — I read all six cited locations directly.  Pass 1.5 (line 2129): `for f in tmp.glob("*.html")` — confirmed unsorted. The closure `_maybe_drop_toc_block` reads from `dropped_files_for_toc` and `dropped_bp_anchors_for_toc`, both computed before the loop as frozen sets. No cross-file write feeds back into the same pass. Output is order-independent today.  Pass 2 id_inventory build (line 2156): `for f in tmp.glob("*.html")` — confirmed unsorted. This pass only *reads* files to build `id_inventory`. Since all reads complete before any writes begin (writes are in the separate line-2165 loop), order i

### 16. [LOW] `_replace_verse_popup_translation` is documented as 'NOT YET WIRED INTO THE BUILD' but MATRIX_MAP traces `popup_translation` → that function

- **Dimension:** byte-stability  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/build_edition.py:607-609`
- **Evidence:** Lines 607-609: `"""Swap the English text ... ⚠ NOT YET WIRED INTO THE BUILD (flagged mint-7 D3, 2026-05-31): a complete, tested feature (5 tests in test_scripts.py) with no production caller yet."""`. MATRIX_MAP line 107 traces `popup_translation` → `build _replace_verse_popup_translation` → `OK (kjv, *-en, "")`. The active production path is `_apply_popup_languages_and_translation` (which performs the translation swap inline at lines 952-970), not `_replace_verse_popup_translation`. The MATRIX_MAP trace is therefore inaccurate and will mislead future reviewers into believing the standalone function is live.
- **Fix:** Update MATRIX_MAP line 107 to reflect the actual active code path: `popup_translation` → `build _apply_popup_languages_and_translation` (unified pass). Add a note that `_replace_verse_popup_translation` is the superseded standalone implementation kept for the 5 tests. No code change required — the active path works correctly; this is a documentation divergence only.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Independently confirmed by reading the code directly. Three facts established:  1. `_replace_verse_popup_translation` at line 600 of `YHWH v2.4/scripts/build_edition.py` carries an explicit docstring warning: "NOT YET WIRED INTO THE BUILD (flagged mint-7 D3, 2026-05-31)". No call sites exist — Grep confirms zero callers of this function.  2. MATRIX_MAP line 107 states: `popup_translation` → `build _replace_verse_popup_translation` → OK (`kjv`, `*-en`, `""`). This trace is factually wrong.  3. The actual production path for `popup_translation` is: line 2698 reads `popup_translation_id = (editio

### 17. [LOW] `build_cache.compute_cache_key` does not hash `content/source_dates.yaml` — cache serves stale EPUBs if that file changes while an edition has `time_filter_ceiling` set

- **Dimension:** byte-stability  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/core/build_cache.py:120-271`
- **Evidence:** The cache key (line 264-271) hashes `kinds.yaml`, `categories.yaml`, `books.yaml`, the edition record JSON, notes files, translations, and `build_edition.py` — but NOT `content/source_dates.yaml`. Yet `compute_time_filtered_html_ref_ids` (build_edition.py line 369) calls `source_dates.lookup_year(attribution)` which reads `source_dates.yaml` via `@functools.lru_cache`. If `source_dates.yaml` gains or loses an entry (changing which notes survive a `time_filter_ceiling`), the cache key is unchanged and the stale (pre-edit) EPUB is served. Currently only one edition has `time_filter_ceiling: null` (a no-op), so the bug is latent, but the first edition to use a real ceiling would be silently broken after a source-dates update.
- **Fix:** In `YHWH v2.4/scripts/core/build_cache.py`, inside `compute_cache_key`, after the loop at line 169 that appends kinds.yaml/categories.yaml/books.yaml, add:

    parts.append(("source_dates.yaml", _hash_file(_CONTENT / "source_dates.yaml")))

This is the minimal correct fix. The finder's suggestion to also add `traditions.yaml` and `customization.yaml` is reasonable but separate: `traditions.yaml` is already covered transitively (the edition record includes `traditions_default` which is what actually drives the tradition filter — the YAML itself is the master list, not a per-build input), and `customization.yaml` similarly. `source_dates.yaml` is the only one that is a direct, untracked per-build file input to a filtering pass. Add only `source_dates.yaml` to keep the change minimal and focused on the confirmed gap.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Verified by reading the actual code:  1. `compute_cache_key` (build_cache.py lines 120-271) hashes kinds.yaml, categories.yaml, books.yaml, the edition record JSON, notes files, translations, reading plans, cover images, build_edition.py, and the full epub_working/ tree — but NOT content/source_dates.yaml. The omission is confirmed.  2. The feature is real and wired: `compute_time_filtered_html_ref_ids` (build_edition.py line 2655) is called in `build_one()`. It calls `source_dates.lookup_year` (source_dates.py line 64), which calls `load_source_dates()` (decorated with @functools.lru_cache), 

### 18. [LOW] build_edition.py locally redefines 6 ANSI color constants already present in scripts/core/ui.py

- **Dimension:** code-debt  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/build_edition.py:92-97`
- **Evidence:** Lines 92-97 of build_edition.py: `GREEN = "\033[92m"` / `RED = "\033[91m"` / `YELLOW = "\033[93m"` / `DIM = "\033[2m"` / `BOLD = "\033[1m"` / `RESET = "\033[0m"`. These are identical to the constants in scripts/core/ui.py (lines 33-41) which already acts as the shared color module (imported by ebible.py, matrix.py, cleanup.py, customize.py, new_note.py, ship-check.py). build_edition.py already imports from scripts.core extensively. The at_scale_base.py was created specifically to centralize these for at-scale drivers, leaving build_edition.py as one of ~20 scripts still carrying its own copy.
- **Fix:** Replace the 6 inline definitions at build_edition.py lines 92-97 with `from scripts.core.ui import GREEN, RED, YELLOW, DIM, BOLD, RESET  # noqa: E402`. No functional change; eliminates duplication.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Independently verified by reading the actual code. Lines 92-97 of YHWH v2.4/scripts/build_edition.py define exactly `GREEN = "\033[92m"`, `RED = "\033[91m"`, `YELLOW = "\033[93m"`, `DIM = "\033[2m"`, `BOLD = "\033[1m"`, `RESET = "\033[0m"` - matching the finder's evidence verbatim. YHWH v2.4/scripts/core/ui.py lines 33-41 define the identical 6 constants (plus BLUE, CYAN, MAGENTA which build_edition.py does not use). build_edition.py already has `sys.path.insert(0, str(REPO_ROOT))` at line 54 and uses `from scripts.core import config` at line 56, so `scripts.core.ui` is already importable by t

### 19. [LOW] run_manuscript_collation_at_scale.py locally redefines ANSI color constants instead of importing from at_scale_base

- **Dimension:** code-debt  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/run_manuscript_collation_at_scale.py:100-103`
- **Evidence:** Lines 100-103: `GREEN = "\033[92m"` / `RED = "\033[91m"` / `DIM = "\033[2m"` / `RESET = "\033[0m"`. The file's docstring (L12-14) says 'Mirrors the established at-scale driver pattern (rules §9 — run_ethiopian_at_scale.py / run_naves_at_scale.py / run_ai_notes_at_scale.py)' and all three cited examples import these constants from at_scale_base. The collation driver does not import from at_scale_base at all (confirmed: no such import in the file's import block).
- **Fix:** For all three files, replace the inline ANSI constant block with an import from at_scale_base:

run_manuscript_collation_at_scale.py — remove lines 100-103 and add after the existing `from scripts.core.notes_io import atomic_write` import:
  from scripts.core.at_scale_base import DIM, GREEN, RED, RESET  # noqa: E402

run_manuscript_transcribe_at_scale.py — remove lines 45-48 and add to its import block:
  from scripts.core.at_scale_base import DIM, GREEN, RED, RESET  # noqa: E402

run_manuscript_review_at_scale.py — remove lines 59-63 and add to its import block (note: YELLOW must be included, which the finder's fix omitted):
  from scripts.core.at_scale_base import DIM, GREEN, RED, RESET, YELLOW  # noqa: E402

No other changes needed. Marathon core files (manuscript_*.py, po_vision_store.py, content/manuscript/) are not touched.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — The finding is confirmed by direct code inspection. Lines 100-103 of run_manuscript_collation_at_scale.py define GREEN/RED/DIM/RESET inline. The same pattern appears at lines 45-48 of run_manuscript_transcribe_at_scale.py and lines 59-63 of run_manuscript_review_at_scale.py (plus YELLOW at line 59). All four constants — including YELLOW — are exported by scripts/core/at_scale_base.py (lines 23-28). Every other at-scale driver in the scripts/ directory (run_ethiopian, run_naves, run_ai_notes, run_greek, run_kenyon, run_torrey, run_xref, run_hebrew, run_ai_xrefs) imports them from at_scale_base.

### 20. [LOW] _CACHED_CONN reset in rebuild() is outside the rebuild lock — race with concurrent connection() calls in ThreadingHTTPServer

- **Dimension:** concurrency-caching  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/core/corpus_index.py:602-610`
- **Evidence:** After the `with _acquire_rebuild_lock():` block exits (line 601), the code resets `_CACHED_CONN` at lines 602-610. The web server is a `ThreadingHTTPServer` (web.py line 2100). Thread A (rebuild) exits the lock; thread B (a concurrent request) calls `connection()`, passes the `if _CACHED_CONN is None` check (line 664), and stores a new connection. Thread A then executes lines 604-606: `_CACHED_CONN.close()`, closing the connection thread B just obtained and is about to return. Thread B's caller receives a closed connection and the next SQL query raises `sqlite3.ProgrammingError: Cannot operate on a closed database`. The `_CACHED_CONN` global has no threading.Lock protecting the check-then-set compound operation.
- **Fix:** Move the `_CACHED_CONN` reset block (lines 602-610) inside the `with _acquire_rebuild_lock():` block, immediately after line 600. This is the minimal safe fix — the filesystem lock already serializes all callers of `rebuild()` (every `connection()` call invokes `rebuild()` first), so moving the reset inside the lock closes the race without introducing a new threading primitive:

```python
# In rebuild(), inside `with _acquire_rebuild_lock():`, after line 600:
        _FINGERPRINT_CACHE = (time.monotonic(), fp, str(_notes_dir()))
        # Reset cached connection INSIDE the lock — prevents a race
        # where a concurrent connection() call sets _CACHED_CONN after
        # we exit the lock but before we close the old connection.
        global _CACHED_CONN, _CACHED_CONN_PATH
        if _CACHED_CONN is not None:
            try:
                _CACHED_CONN.close()
            except sqlite3.Error:
                pass
            _CACHED_CONN = None
            _CACHED_CONN_PATH = None
    # (lock released here — no bare reset block below)
```

Remove lines 602-610 from their current position outside the lock. No other changes needed. The `global` declaration should also be moved to the top of `rebuild()` alongside the existing `global _FINGERPRINT_CACHE` at line 546. Do NOT add a separate `_conn_lock` — it would require protecting `connection()` and `invalidate()` symmetrically and is unnecessary given the lock already serializes `rebuild()` callers. The `invalidate()` function's unprotected pattern is acceptable because it is called from `notes_io` write paths (not concurrent rebuild paths) and its blast radius is the same single-request 500.
- **Verdict (1 skeptic[s]):** refuted=False conf=medium — I read the cited region directly. Lines 602-610 of `YHWH v2.4/scripts/core/corpus_index.py` are definitively OUTSIDE the `with _acquire_rebuild_lock():` block (which closes at line 601 by indentation). The lock is a filesystem advisory lock (msvcrt.locking on Windows / fcntl.flock on POSIX), not a threading.Lock, so it provides zero protection against in-process thread races on `_CACHED_CONN`.  The race the finder describes is real in principle: Thread A exits the filesystem lock, is about to execute lines 604-606 (`_CACHED_CONN.close()`), while Thread B has already returned from its own (fast

### 21. [LOW] filter_books_for_canon: cross_refs_stripped counter overcounts by including kept (non-stripped) link matches

- **Dimension:** correctness  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/build_edition.py:2180-2193`
- **Evidence:** `new_text, n1 = link_re.subn(_check_anchor, text); stats['cross_refs_stripped'] += n1` — Python's `str.subn()` returns the number of substitution CALLS (i.e., all matches), not the number that were actually changed. `_check_anchor` returns `m.group(0)` (unchanged) for valid links and `visible` (stripped) for dangling ones. `n1` therefore counts ALL matched links in the file, not just the stripped ones. The same error is repeated for `n2` at line 2193. As a result `canon_xrefs_stripped` in the build stats can be many times higher than the actual number of stripped links.
- **Fix:** The simplest safe fix is to count the actual delta after both subn passes, since the HTML structure is consistent:

```python
new_text, _n1 = link_re.subn(_check_anchor, text)
new_text2, _n2 = file_only_re.subn(_check_file_only, new_text)

# Count actual <a> tags removed (overcounting via subn is wrong — it counts all matches)
stripped_count = text.count('<a ') - new_text2.count('<a ')
stats['cross_refs_stripped'] += stripped_count

if new_text2 != text:
    f.write_text(new_text2, encoding='utf-8')
```

This eliminates both n1/n2 intermediate accumulations and measures the real change. It is additive (the stat key already exists), does not touch the marathon core, and is byte-stable for the 9 KJV editions (the filtering logic itself is unchanged). Alternatively, a nonlocal counter inside each closure works but requires more restructuring.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — The code at lines 2180-2193 of YHWH v2.4/scripts/build_edition.py is exactly as described. `link_re.subn(_check_anchor, text)` returns `n1` = the total number of regex matches (all `<a href="...#...">` links in the file), regardless of whether `_check_anchor` returned `m.group(0)` (unchanged) or `visible` (stripped). The same overcounting occurs at line 2193 with `file_only_re.subn(_check_file_only, new_text)` for `n2` — and `_check_file_only` has an additional path that also returns `m.group(0)` unchanged for non-html refs and for kept files. Both `n1` and `n2` are added unconditionally to `s

### 22. [LOW] filter_books_for_canon: cross_refs_stripped stat grossly overcounted via re.subn semantics

- **Dimension:** correctness  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/build_edition.py:2180-2193`
- **Evidence:** ```python
new_text, n1 = link_re.subn(_check_anchor, text)
stats["cross_refs_stripped"] += n1
...
new_text2, n2 = file_only_re.subn(_check_file_only, new_text)
stats["cross_refs_stripped"] += n2
```
`re.subn` returns the count of every pattern *match* processed, not the count of matches where the replacement function returned different text. `_check_anchor` returns `m.group(0)` (original text) for valid kept links, but those still increment `n1`. The result is that `cross_refs_stripped` ≈ total `<a href>` count across all HTML files in the build, not the number actually stripped. This number surfaces in the stats sidecar (`.stats.json`) and in the console build summary, making the canon-filter diagnostic misleading for any edition that drops books.
- **Fix:** The finder's proposed fix (use `nonlocal` counters inside the closures, switch to `re.sub`) is correct and safe — it does not touch marathon core, does not affect EPUB bytes, and is additive. However, given the stat is never surfaced anywhere (not in the sidecar, not in the console, not consumed by any other code or test), this is a cosmetic fix with no functional impact. If fixed, prefer the closure-counter pattern the finder shows, which is clean and self-contained. No urgency.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Confirmed by reading lines 2168-2193 of YHWH v2.4/scripts/build_edition.py. Both `link_re.subn(_check_anchor, text)` and `file_only_re.subn(_check_file_only, new_text)` accumulate their return counts directly into `stats["cross_refs_stripped"]`. Since `re.subn` counts every match processed — not just those where the replacement function returned different text — `_check_anchor` returning `m.group(0)` for valid kept links still increments `n1`. The finder's logic is correct.  However, the blast radius is zero. Traced the full consumer chain: `cross_refs_stripped` is aggregated into `canon_stats

### 23. [LOW] bookcode_canonical lint rule does not screen versification.SWETE_BOOK_TO_CODE or _NT_BOOK_TO_CODE

- **Dimension:** cross-module  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/lint_rules.py:1995-2006`
- **Evidence:** The `map_specs` list in `check_book_codes_canonical()` (lines 1995-2006) covers 8 maps but omits `scripts.core.versification.SWETE_BOOK_TO_CODE` and `scripts.core.versification._NT_BOOK_TO_CODE`. Both maps emit values used as the canonical book codes for translation files written to `content/translations/lxx-swete-greek/*.py` and `content/translations/byzantine-greek/*.py` by `extract_lxx_swete.py` / `extract_byzantine_nt.py`. If either map acquired a legacy alias value (e.g. `"eze"` → `"ezk"` for Ezekiel), the ingested file would be named `ezk.py` — a code with no corresponding `content/notes/ezk.py` — and that book's popups would silently disappear. Neither map is covered by any test in `tests/test_scripts.py::TestBookCodeMaps._maps()` either (that test only covers 5 maps). The maps are currently clean but carry no guard against future ★BUGCLUSTER-class drift.
- **Fix:** The proposed fix is correct and safe. Add both entries to `map_specs` in `YHWH v2.4/scripts/lint_rules.py` after line 2005:

```python
# Versification remappers — values become the book codes of translation files.
("scripts.core.versification", "SWETE_BOOK_TO_CODE"),
("scripts.core.versification", "_NT_BOOK_TO_CODE"),
```

And extend `TestBookCodeMaps` in `YHWH v2.4/tests/test_scripts.py` to include them. In `BOOK_CODE_MAPS` (line 8397), add `"SWETE_BOOK_TO_CODE"` and `"_NT_BOOK_TO_CODE"`. In `_maps()` (line 8405), add:

```python
from scripts.core.versification import SWETE_BOOK_TO_CODE, _NT_BOOK_TO_CODE
```

and include both in the returned dict. Note: `test_every_map_value_is_canonical_with_notes_file` will pass cleanly because all current values are canonical codes with corresponding `content/notes/<code>.py` files. No changes to the marathon core; no KJV byte-stability impact.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — I independently verified all claims by reading the actual code.  (a) Does the code do what the evidence claims? Yes. `check_book_codes_canonical()` in `YHWH v2.4/scripts/lint_rules.py` lines 1995-2006 lists exactly 8 `map_specs` entries; `scripts.core.versification.SWETE_BOOK_TO_CODE` and `scripts.core.versification._NT_BOOK_TO_CODE` are absent from that list. The test `TestBookCodeMaps._maps()` in `tests/test_scripts.py` lines 8405-8417 covers only 5 maps (KENYON, TSK, NAVES, _BOOK_CODE_ALIASES, _LEGACY_TO_CANON) — the two versification maps are absent there too.  (b) Is it a genuine defect? 

### 24. [LOW] bookcode_canonical lint guard does not screen translation-extraction book-code maps (SWETE_BOOK_TO_CODE, _NT_BOOK_TO_CODE, OSIS_BOOK_TO_CODE)

- **Dimension:** cross-module  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/lint_rules.py:1995-2006`
- **Evidence:** The `map_specs` list in `check_book_codes_canonical` (line 1995-2006) covers notes-routing maps (TSK_BOOK_REMAP, NAVES_BOOK_REMAP, KENYON_BOOK_NAME_TO_CODE, _BOOK_CODE_ALIASES, _LEGACY_TO_CANON, ABBREV, CCEL_ABBREV, EASTON_BOOK) but omits three translation-extraction maps: `scripts.core.versification.SWETE_BOOK_TO_CODE`, `scripts.core.versification._NT_BOOK_TO_CODE`, and `scripts.extract_wlc_morphhb.OSIS_BOOK_TO_CODE`. All three produce book codes used to write `translations/<id>/<book>.py` filenames for the verse-popup pipeline. A legacy code value there (e.g. `"JOH": "joh"` instead of `"JOH": "jhn"`) would silently produce a wrongly-named translation file, causing the popup to return empty for that entire book. Current values are all canonical, so this is a maintenance risk, not an active defect — but the ★BUGCLUSTER memory note explicitly flags that this class of error recurs at ingest.
- **Fix:** The proposed fix is correct and safe. Add the three entries to `map_specs` in `check_book_codes_canonical` (`YHWH v2.4/scripts/lint_rules.py` after line 2005):

```python
("scripts.core.versification", "SWETE_BOOK_TO_CODE"),
("scripts.core.versification", "_NT_BOOK_TO_CODE"),
("scripts.extract_wlc_morphhb", "OSIS_BOOK_TO_CODE"),
```

No other changes needed. All three maps currently pass (all values are canonical), so adding them to the guard will produce zero new failures today while blocking future legacy-alias drift — the same guardrail rationale used for the `CCEL_ABBREV`/`EASTON_BOOK` additions in the M16a comment at line 2002.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Verified by direct code reading:  (a) The `map_specs` list at lines 1995-2006 of `YHWH v2.4/scripts/lint_rules.py` covers 8 maps but does NOT include `scripts.core.versification.SWETE_BOOK_TO_CODE`, `scripts.core.versification._NT_BOOK_TO_CODE`, or `scripts.extract_wlc_morphhb.OSIS_BOOK_TO_CODE`. The omission is real.  (b) All three maps were checked directly: - `_NT_BOOK_TO_CODE` (versification.py lines 663-691): all 27 values are canonical (jhn, mrk, phi, jam, etc. — none match the legacy keys joh/mar/php/jas/jol/ezk/nam/ps). - `SWETE_BOOK_TO_CODE` (versification.py lines 99-152): ~45 values

### 25. [LOW] test_cyril_remains_plurality_leader_at_arc_close (γ.4.9.D) does not guard against Ephrem or 1 Enoch exceeding Cyril

- **Dimension:** cross-module  ·  **kind:** find
- **Location:** `YHWH v2.4/tests/test_ethiopian_gamma4.py:7014-7037`
- **Evidence:** ```python
assert cyril_count > jubilees_count  # checks only Jubilees
assert cyril_count > ath_count       # checks only Athanasius
```
The ω.41 §1 invariant states Cyril must be the single-father plurality-leader. The test iterates `_by_verse.values()` but counts only Jubilees and Athanasius as challengers. At arc-close the corpus has 1 Enoch at 192 entries and Ephrem at 157 entries — both larger than Jubilees (200 is Meqabyan, which is caught at γ.4.8.E's class). The γ.4.9.D test class does not accumulate a `_all_meq()` method (Meqabyan is in a different class) and does not check 1 Enoch or Ephrem. The γ.4.8.F class (`test_cyril_plurality_preserved_post_tier2`) correctly checks all five challengers, but that is a separate class covering a different corpus snapshot. Any future wave adding Ephrem or 1 Enoch entries without proportional Cyril entries could violate the γ.4.9.D invariant undetected.
- **Fix:** The proposed fix is safe and correct. A slightly cleaner version that mirrors the γ.4.8.F pattern exactly:

In `TestGamma49DAthanasiusArcClose.test_cyril_remains_plurality_leader_at_arc_close` (C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\tests\test_ethiopian_gamma4.py, lines 7014–7037), replace the hand-rolled loop with a Counter and check all five challengers:

```python
def test_cyril_remains_plurality_leader_at_arc_close(self):
    from collections import Counter
    all_entries = [e for ve in self.ec._by_verse.values() for e in ve]
    counts = Counter(e.father for e in all_entries)
    cyril = counts.get("Cyril of Alexandria", 0)
    for challenger, label in [
        ("Jubilees (Ethiopian tradition)", "Jubilees"),
        ("Athanasius of Alexandria",       "Athanasius"),
        ("1 Enoch (Ethiopian tradition)",  "1 Enoch"),
        ("Ephrem the Syrian",              "Ephrem"),
    ]:
        n = counts.get(challenger, 0)
        assert cyril > n, (
            f"ω.41 §1: Cyril must remain single-father plurality-leader at γ.4.9.D arc-close; "
            f"Cyril={cyril} vs {label}={n}"
        )
```

This is purely additive to the test suite, touches no production code, and does not affect byte stability of any edition.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Read lines 7014–7037 of test_ethiopian_gamma4.py directly. The test `test_cyril_remains_plurality_leader_at_arc_close` in `TestGamma49DAthanasiusArcClose` iterates `_by_verse` and accumulates only `cyril_count` and `jubilees_count` inline; it then adds `ath_count = len(self._all_athanasius())`. The class docstring at line 6751–6758 explicitly records that 1 Enoch has 192 entries and Ephrem the Syrian has 157 entries at this arc-close snapshot — both are larger challengers than Athanasius (150) and Jubilees (200, but Jubilees IS checked). 1 Enoch and Ephrem are not accumulated or asserted again

### 26. [LOW] REPO_MAP docs/superpowers plan count stale: claims 23, actual is 26

- **Dimension:** docs  ·  **kind:** find
- **Location:** `YHWH v2.4/dev/REPO_MAP.md:19`
- **Evidence:** '`plans/` (23 implementation plans) + `specs/` (16 design specs)'

Actual file count: 26 .md files in docs/superpowers/plans/ (mint-7-quality-pass, mint-8-audit-plan, mint-8-fixes-plan were added after this line was last updated). The INDEX.md correctly says '26 plans · 16 specs = 42 documents'. The check_repo_map_complete lint skips prose counts; the superpowers_coherence lint verifies the 26 files all have Status headers and are in INDEX, confirming 26 is correct.
- **Fix:** Update line 19 to '`plans/` (26 implementation plans) + `specs/` (16 design specs)'.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Independently verified by reading YHWH v2.4/dev/REPO_MAP.md line 19 (says "23 implementation plans") and globbing C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\docs\superpowers\plans\ — exactly 26 .md files returned. INDEX.md line 7 confirms "26 plans · 16 specs = 42 documents." The discrepancy is real: REPO_MAP.md's prose count is 3 behind the actual file count. Blast radius is zero for any runtime, build, or lint behavior: the check_repo_map_complete lint explicitly documents (line 1291-1292 of lint_rules.py) that "Brittle prose-COUNT parsing is deliberately NOT attempted" — it checks on

### 27. [LOW] REPO_MAP docs/superpowers/ entry omits the notes/ subdirectory

- **Dimension:** docs  ·  **kind:** find
- **Location:** `YHWH v2.4/dev/REPO_MAP.md:19`
- **Evidence:** '`plans/` (23 implementation plans) + `specs/` (16 design specs) for the manuscript/ingest workstreams.'

The docs/superpowers/notes/ subdirectory exists and holds: 2026-05-28-d2-source-readiness.md, 2026-05-31-mint-8-findings.md, and 2026-05-31-mint-8-audit-raw.json. The mint-8-findings.md is the primary audit-findings record referenced by SESSION_STATE and the fixes-plan. Omitting it from REPO_MAP means a future session looking for audit findings won't find the directory via the map.
- **Fix:** In YHWH v2.4/dev/REPO_MAP.md line 19, replace the current entry with: '`docs/superpowers/` | ✅ | `plans/` (23 implementation plans) + `specs/` (16 design specs) + `notes/` (audit findings and research notes) for the manuscript/ingest workstreams. Root-level: `2026-05-31-mint-7-audit-findings.md` (sits outside the three subdirs) + `INDEX.md`.' The `notes/` entry should clarify it currently holds: `2026-05-28-d2-source-readiness.md`, `2026-05-31-mint-8-findings.md` (primary mint-8 audit record referenced by SESSION_STATE), and `2026-05-31-mint-8-audit-raw.json`. This is a pure documentation edit — no code, no build output, no schema change.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Verified by reading YHWH v2.4/dev/REPO_MAP.md line 19 and listing YHWH v2.4/docs/superpowers/ directly. Line 19 states only `plans/` and `specs/` exist under docs/superpowers/. The Glob confirms a `notes/` subdirectory is present with three files (2026-05-28-d2-source-readiness.md, 2026-05-31-mint-8-findings.md, 2026-05-31-mint-8-audit-raw.json), and a root-level file 2026-05-31-mint-7-audit-findings.md sits outside all three subdirectories. REPO_MAP is declared "The file/folder index of record" in its own header, so omitting an existing subdirectory that holds the primary audit-findings recor

### 28. [LOW] is_output_current mtime guard omits notes corpus — stale EPUB served when build_edition.py run directly after notes edit

- **Dimension:** opt-build  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/build_edition.py:1943-1965`
- **Evidence:** ```python
sources = list(EPUB_DIR.glob("*.html"))
sources.append(EPUB_DIR / "content.opf")
sources.append(EPUB_DIR / "nav.xhtml")
sources.append(EPUB_DIR / "stylesheet.css")
sources.append(REPO_ROOT / "content" / "editions.yaml")
sources.append(REPO_ROOT / "scripts" / "build_edition.py")
```
`content/notes/<book>.py` files (the corpus) are not in the mtime-watched list. If a user edits notes then calls `python scripts/build_edition.py <ed>` directly — without running inject first — the content-addressable cache (ω.20-B) will miss (the cache key includes note hashes and will not match), but then the mtime fallback at line 2757 finds the prior EPUB, sees its mtime > all watched sources (notes were not watched), and returns the prior stale artifact without rebuilding. The `ebible build` command is safe because it always runs inject first, but direct invocations of `build_edition.py` are not.
- **Fix:** In `is_output_current` (build_edition.py ~line 1961), after the existing `sources.append(REPO_ROOT / "scripts" / "build_edition.py")` line, add:

```python
notes_dir = REPO_ROOT / "content" / "notes"
if notes_dir.is_dir():
    sources.append(notes_dir)          # directory mtime catches add/delete
    sources.extend(notes_dir.glob("*.py"))  # file mtimes catch edits
```

The existing loop at line 1962 already handles `Path` objects for both files and directories via `s.is_file()` — note that a directory will fail `is_file()` and be silently skipped, so the directory-mtime check also needs `s.is_dir()` in the loop predicate. Either change the loop to:

```python
for s in sources:
    try:
        if s.stat().st_mtime > out_mtime:
            return None
    except OSError:
        pass
```

Or keep the current `is_file()` guard and omit `sources.append(notes_dir)` (the per-file globs alone are sufficient for edit detection; add/delete of a book file is caught when the new/removed file's mtime is checked). The simplest correct fix is just the per-file glob without the directory entry.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — I read the code directly.  `is_output_current` at build_edition.py:1956-1964 confirms the watched-sources list is exactly: `EPUB_DIR/*.html`, `content.opf`, `nav.xhtml`, `stylesheet.css`, `editions.yaml`, `build_edition.py`. No notes files.  `compute_cache_key` in scripts/core/build_cache.py:181-187 confirms the CA cache key DOES hash every in-canon `content/notes/<book>.py` (step 5 of 10). So after a notes edit the CA cache produces a new key H2, `cache_lookup(H2)` finds no `exports/.cache/H2.epub`, and returns None.  The code then falls to the mtime guard at build_edition.py:2757-2764. That 

### 29. [LOW] filter_html ρ.1 per-note-ID regex loop is O(|disabled_ids| × |text|) — degrades when tradition-filter produces large disabled sets

- **Dimension:** opt-build  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/build_edition.py:1034-1052`
- **Evidence:** ```python
for ref_id in disabled_html_ref_ids:
    m_re = re.compile(
        rf'<a class="note-ref [^"]*" id="{re.escape(ref_id)}"[^>]*>.*?</a>',
        re.DOTALL,
    )
    new_text, n = m_re.subn("", new_text)
    counts["id_markers"] += n
    note_id = ref_id.replace("ref-", "note-", 1)
    a_re = re.compile(
        rf'<aside class="note [^"]*" id="{re.escape(note_id)}"[^>]*>.*?</aside>',
        re.DOTALL,
    )
    new_text, n = a_re.subn("", new_text)
    counts["id_asides"] += n
```
Two regex compilations per disabled ID per `filter_html` call. With 61 HTML files per edition, N disabled IDs → 2 × N × 61 regex compiles. Python's internal regex cache holds 256 entries; any tradition-filtered edition with N > 128 IDs will flood the cache and force full recompilation on every call. The `catholic-study` edition currently declares `traditions_default: ["catholic", "cross"]`, which would fire this path for every note tagged with other traditions. As the corpus grows with explicit tradition-tagged notes, this path worsens quadratically.
- **Fix:** Move the two combined regex compiles to `build_one()` before the file loop, and pass them as pre-compiled objects into `filter_html` (or as a second path within the existing signature). The fix shown in the finding is architecturally correct but needs the compile to happen in `build_one()` rather than inside `filter_html` itself (since `filter_html` doesn't know whether it's being called in a loop). Concretely:

In `build_one()` (around line 2843), before the `for html_path in tmp.glob("*.html"):` loop, add:

```python
batch_marker_re = batch_aside_re = None
if disabled_html_ref_ids:
    ref_pat = "|".join(re.escape(r) for r in disabled_html_ref_ids)
    note_pat = "|".join(re.escape(r.replace("ref-", "note-", 1)) for r in disabled_html_ref_ids)
    batch_marker_re = re.compile(
        rf'<a class="note-ref [^"]*" id="(?:{ref_pat})"[^>]*>.*?</a>', re.DOTALL
    )
    batch_aside_re = re.compile(
        rf'<aside class="note [^"]*" id="(?:{note_pat})"[^>]*>.*?</aside>', re.DOTALL
    )
```

Then replace the ρ.1 loop in `filter_html` with a single-pass using those pre-compiled objects passed in. This reduces from 2N compiles × 61 files to 2 compiles total per edition build, regardless of N. Apply the same change to the dry-run loop at line 2768. For future-proofing when N exceeds ~2000, add a batch-size cap (500 IDs per alternation group, union the counts).
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Code confirmed at build_edition.py:1034–1052: the per-ID loop is exactly as described — two `re.compile()` calls per disabled ref-id inside `filter_html`, and `filter_html` is called once per HTML file (~61 files per edition build, lines 2768 and 2846).  Key facts from reading the actual code:  1. The double-compile pattern is real. Each call to `filter_html` with N disabled IDs performs 2N `re.compile()` calls. The regex cache (Python 3.x, ~512 entries) means that for a single edition build, patterns compiled during file 1 are cache-hits for files 2–61, so the cache-flood concern is only rele

### 30. [LOW] _resolve_popup_languages decodes per_book_languages on every vnote aside — redundant parse inside tight regex callback

- **Dimension:** opt-build  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/build_edition.py:759-786`
- **Evidence:** ```python
def _resolve_popup_languages(edition: dict, book_code: str) -> set[str]:
    per_book = decode_per_book_languages(edition.get("popup_languages_per_book"))
    ...
```
`_resolve_popup_languages` is called inside the `_process` callback of `_apply_popup_languages_and_translation`, which is itself called by `_VNOTE_ASIDE_RE.sub(_process, html_text)`. The corpus has 36,556 vnote asides. Each call re-parses the raw `popup_languages_per_book` list from the edition dict (splitting on `=` and `,` for each entry). For an edition with, say, 87 per-book overrides, this is 87 string splits × 36,556 calls per file × 61 files = ~194M string ops per edition. For the 9 editions that have `popup_languages_default` or `popup_languages_per_book` configured, this adds meaningful overhead.
- **Fix:** In `_apply_popup_languages_and_translation` (build_edition.py line 907), hoist both the decode and the per-book resolution cache above the `_process` closure:

```python
def _apply_popup_languages_and_translation(
    html_text: str,
    edition: dict,
    translation_id: str,
    translation_short: str,
) -> tuple[str, dict]:
    from scripts.core import translations as _tx

    # Hoist once — decode_per_book_languages is O(N_overrides) and its
    # result is edition-constant; _resolve_popup_languages is also
    # book-constant so cache per book_code (mirrors traditions pattern
    # at lines 276-281 / 395-401).
    _per_book_decoded = decode_per_book_languages(edition.get("popup_languages_per_book"))
    _default_langs = edition.get("popup_languages_default")
    _lang_cache: dict[str, set[str]] = {}

    def _resolve_langs_fast(book_code: str) -> set[str]:
        cached = _lang_cache.get(book_code)
        if cached is not None:
            return cached
        if book_code in _per_book_decoded:
            raw = _per_book_decoded[book_code]
        elif _default_langs is not None:
            raw = _default_langs
        else:
            result = {m for m in _pv.DEFAULT_POPUP_WITNESSES if m in POPUP_LANGUAGES}
            _lang_cache[book_code] = result
            return result
        mapped = ((_pv.resolve_version_id(lang) or lang) for lang in (raw or []))
        result = {m for m in mapped if m in POPUP_LANGUAGES}
        _lang_cache[book_code] = result
        return result

    # ... rest of stats setup unchanged ...

    def _process(m: re.Match) -> str:
        # replace: active_langs = _resolve_popup_languages(edition, book)
        # with:
        active_langs = _resolve_langs_fast(m.group(2))
        # ... rest unchanged ...
```

This is byte-stable (identical output), zero-risk, and consistent with the existing `book_active_cache` pattern used in `filter_html` and `_build_disabled_ref_ids`. The original `_resolve_popup_languages` can stay as the public API used by tests; `_resolve_langs_fast` is a private closure. No marathon core touched.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Independently confirmed by reading the code:  1. `_resolve_popup_languages` at line 771 does call `decode_per_book_languages(edition.get("popup_languages_per_book"))` on every invocation, and `_process` (line 936) calls `_resolve_popup_languages` on every regex match inside `_VNOTE_ASIDE_RE.sub(_process, html_text)` at line 997. So the structural redundancy the finder describes is real.  2. HOWEVER the finder's severity arithmetic is wrong. In the actual editions.yaml, exactly one edition has the `popup_languages_per_book` key, and it is set to null (no entries follow the YAML key at line 167)

### 31. [LOW] `batch_insert_notes` dedup checks only `body`, not `attribution` — prevents attribution repair on previously-promoted notes

- **Dimension:** opt-ingest  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/promote.py:355`
- **Evidence:** `if skip_existing and body in existing_bodies.get((ch, v, kind), set()): continue` — `existing_bodies` is keyed by `(ch, v, kind)` and stores only `vals[7]` (the body). `note_already_exists()` at line 121-134 in the same file correctly matches on `(ch, v, kind, body, attribution)`. When a note was originally promoted without attribution (`attribution=None`) and the same candidate is re-generated with correct attribution, `batch_insert_notes` will skip it because body matches — no fix applied. The `note_already_exists` contract is intentionally body+attribution so `topic-nave` can write multiple bodies per verse. `batch_insert_notes` silently diverges from that contract.
- **Fix:** In `batch_insert_notes` (promote.py line 334), change the `existing_bodies` value type from `set[str]` to `set[tuple[str, str|None]]` storing `(body, normalized_attribution)` pairs:

```python
norm_existing_attr = ((vals[8] if len(vals) > 8 else None) or "").strip() or None
existing_bodies.setdefault((ch, v, kind), set()).add(
    (vals[7] if len(vals) > 7 else "", norm_existing_attr)
)
```

Then update the skip guard at line 355:

```python
norm_attr = (attribution or "").strip() or None
if skip_existing and (body, norm_attr) in existing_bodies.get((ch, v, kind), set()):
    continue
```

This exactly mirrors `note_already_exists`'s normalization (`tattr.strip() != norm_attr` at line 132) and makes the two dedup paths contract-identical. No other changes required; no build path touched; byte-stable output unaffected.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — I read promote.py directly. The divergence is exactly as described: line 334 populates `existing_bodies` with bare body strings (`vals[7]`), and line 355's skip guard does a body-only membership test. Meanwhile `note_already_exists` at lines 121-134 checks body AND attribution together (lines 129-133), explicitly so that multiple distinct-body or distinct-attribution notes per (ch,v,kind) are not collapsed. The two dedup contracts are genuinely inconsistent.  The practical consequence: if `batch_insert_notes` is called with a note whose body already exists on disk but with a different (or newl

### 32. [LOW] render_coverage.run_all() omits the -en back-translation directories from coverage monitoring

- **Dimension:** opt-render  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/render_coverage.py:235`
- **Evidence:** `for ed_name in ("kjv", "geez-tewahedo", "amharic-tewahedo"):` — only three editions are scanned. `content/translations/geez-tewahedo-en/` and `content/translations/amharic-tewahedo-en/` (the EN back-translation directories used as popup sources for the standalone Bibles) are completely absent from the coverage report. These directories already have `gen.py`, `ex.py`, `lev.py`, `1ki.py`, `1sa.py`, `2sa.py`, `psa.py` on disk. A regression in either directory (deletion, rename, content corruption) would go undetected by preflight.
- **Fix:** In `scripts/lint_rules.py`, extend `check_render_coverage_no_regression()` (line 1028) to add the `-en` directories to its edition loop with their own expected-books sets. After the existing `expected_geez` / `expected_amharic` definitions, add:

```python
expected_geez_en = {"gen", "ex", "lev", "1ki", "1sa", "2sa", "psa"}
expected_amharic_en = {"gen", "ex", "lev"}
```

Then extend the loop at line 1028:

```python
for edition, expected in (
    ("geez-tewahedo", expected_geez),
    ("amharic-tewahedo", expected_amharic),
    ("geez-tewahedo-en", expected_geez_en),
    ("amharic-tewahedo-en", expected_amharic_en),
):
```

Update the pass-message at line 1058 to include the two new counts. Do NOT add the `-en` directories to `render_coverage.run_all()` — the `_per_edition_report()` helper uses geez-specific track categories (marathon_pending, patrologia_pending) that are meaningless for the partial EN back-translation stores and would produce ~80 spurious "missing" entries in the summary output.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — The finding is confirmed: `render_coverage.run_all()` at line 235 of `scripts/render_coverage.py` iterates only over `("kjv", "geez-tewahedo", "amharic-tewahedo")`. The `-en` directories (`content/translations/geez-tewahedo-en/` with 7 files: gen, ex, lev, 1ki, 1sa, 2sa, psa; and `content/translations/amharic-tewahedo-en/` with 3 files: gen, ex, lev) are absent from both `run_all()` and `lint_rules.check_render_coverage_no_regression()` (lines 1028-1031 loop only over `geez-tewahedo` and `amharic-tewahedo`). The `-en` stores are real and active on disk. However, the proposed fix is partially w

### 33. [LOW] render_coverage.py module docstring falsely states Patrologia books are patrologia_pending

- **Dimension:** opt-render  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/render_coverage.py:12-15`
- **Evidence:** Docstring says: `"1ch, 2ch, ezr, neh, job rendered from printed bilingual Ge'ez+French critical editions. Today they show up as patrologia_pending (PDFs exist under GAPS/3_Chronicles/ etc.)"`. The `.py` files for all five books exist in `content/translations/geez-tewahedo/` (confirmed by glob: `1ch.py`, `2ch.py`, `ezr.py`, `neh.py`, `job.py`). Because `_list_rendered()` correctly returns them in the `rendered` set and `_per_edition_report()` skips books already rendered (line 207: `if book in rendered: continue`), the actual report shows them as rendered, not pending. The docstring was written when render was future and was never updated when the patrologia ingest shipped (τ.6.x.5.x). It misleads any reader (human or Claude) about the current project state.
- **Fix:** 1. Module docstring lines 12-15: replace "Today they show up as patrologia_pending (PDFs exist under GAPS/3_Chronicles/ etc.)" with "Ingest complete as of τ.6.x.5.x (2026-05-20); they now appear as rendered in the inventory." 2. Comment at line 156: replace "Render is pending; printed bilingual Ge'ez+French critical edition." with "Render complete (τ.6.x.5.x). These books appear as rendered for geez-tewahedo; set used to classify any still-pending edition." 3. Summary key at line 250: rename "patrologia_track_books_pdf_available" to "patrologia_track_books_rendered" and compute it as len(_PATROLOGIA_TRACK_BOOKS & set(editions["geez-tewahedo"]["rendered_books"])). 4. Pretty-printer at line 267: update to read "patrologia track: {N} books rendered" removing the "(ingest pending)" suffix. No byte-stability risk (coverage script is not part of the build pipeline); no marathon-core touch required.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — I confirmed the finding is real by reading the file and checking the directory. All five patrologia-track .py files (1ch.py, 2ch.py, ezr.py, neh.py, job.py) exist under C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\content\translations\geez-tewahedo\. The module docstring at lines 12-15 states these books "show up as patrologia_pending" and the comment at line 156 says "Render is pending" — both are factually wrong. The summary key at line 250 is named "patrologia_track_books_pdf_available" and the pretty-printer at line 267 outputs "books with PDFs ready (ingest pending)" — also stale. Th

### 34. [LOW] render_coverage._list_rendered normalises stems via _BOOK_ALIASES but lint_rules.check_render_coverage_no_regression duplicates its own expected-set logic without normalisation — coherence debt

- **Dimension:** opt-vision  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/lint_rules.py:948–1070`
- **Evidence:** `render_coverage._list_rendered()` applies `_BOOK_ALIASES = {"ex": "exo", "1k": "1ki", "2k": "2ki"}` to normalise stems, meaning `render_coverage.run_all()` reports `"exo"` as rendered even when the file is `ex.py`. The lint check in `lint_rules.py` duplicates this logic but does NOT import or use `_BOOK_ALIASES` — it builds `actual = {p.stem ...}` raw and compares against its own hand-maintained `expected_geez/amharic` sets. These two paths describe the same facts in different codes (`"ex"` vs `"exo"`). A future alias addition (e.g. if a `1k.py` legacy file exists) would need updating in two places and could drift. Currently passes because the expected sets match the raw stems.
- **Fix:** In `YHWH v2.4/scripts/lint_rules.py`, inside `check_render_coverage_no_regression`, replace the raw-stem collection with a call to `render_coverage._list_rendered`:

```python
from scripts import render_coverage as _rc  # add at top of function or module

# replace line 1042:
actual = _rc._list_rendered(ed_dir)
```

The expected sets must then use canonical 3-letter codes (`"exo"` not `"ex"`). Change line 977 from `"ex"` to `"exo"` and line 1006 from `"ex"` to `"exo"` in the amharic set. After this change, any future alias added to `render_coverage._BOOK_ALIASES` is automatically honored by the lint check — no second update needed.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Independently verified by reading both files in full.  render_coverage.py line 51: `_BOOK_ALIASES = {"ex": "exo", "1k": "1ki", "2k": "2ki"}`. Line 171: `out.add(_BOOK_ALIASES.get(p.stem, p.stem))` — so `_list_rendered` normalizes `ex.py` → `"exo"`.  lint_rules.py lines 960–1042: `check_render_coverage_no_regression` builds `actual = {p.stem for p in ed_dir.glob("*.py") if not p.stem.startswith("_")}` (raw stems, no normalization) and compares against hand-maintained `expected_geez`/`expected_amharic` sets that contain `"ex"` at line 977 (not `"exo"`).  The actual file on disk is `content/trans

### 35. [LOW] url_override bypasses the PD-sources domain allowlist at validation time, relying solely on http.get's runtime SSRFBlockedError to block non-allowlisted hosts

- **Dimension:** security  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/api/sources.py:163-186`
- **Evidence:** if url_override is not None:
    if not isinstance(url_override, str) or not url_override.startswith(("http://", "https://")):
        return {"status": "error", ...}
    ...  # builds a one-off Source with the override URL, passes it to fetch_source

The check at line 164 only validates the scheme prefix (http/https), not the host. Arbitrary hosts (http://169.254.169.254/..., http://internal-service.local/) pass this validation gate. The actual block happens later when the parser calls `_http.get(url, allowlist=DEFAULT_PD_SOURCES_ALLOWLIST)` which raises SSRFBlockedError, caught by fetch_source's bare `except Exception` (fetch_sources.py:528). The guard works today, but it is fragile: it relies on every parser in PARSERS unconditionally passing its url argument to `_http.get` with the correct allowlist. A future parser that calls urllib directly or uses a different allowlist would silently allow SSRF.
- **Fix:** The finder's proposed fix is correct and safe. Add an explicit allowlist check immediately before constructing the one-off Source in `YHWH v2.4/scripts/api/sources.py` at line 163:

```python
if url_override is not None:
    if not isinstance(url_override, str) or not url_override.startswith(("http://", "https://")):
        return {"status": "error", "code": "invalid_url", "http": 400,
                "message": "url_override must be an http(s) URL"}
    # Defense-in-depth: validate host at the API boundary, independent of
    # per-parser enforcement inside _http.get.
    from scripts.core.http import DEFAULT_PD_SOURCES_ALLOWLIST, SSRFBlockedError
    from scripts.core.http import _check_allowlist
    try:
        _check_allowlist(url_override, DEFAULT_PD_SOURCES_ALLOWLIST)
    except SSRFBlockedError as e:
        return {"status": "error", "code": "ssrf_blocked", "http": 400,
                "message": f"url_override host not in PD-sources allowlist: {e}"}
    ...
```

This is purely additive (new early-return path, no existing behavior changed), touches no marathon-core files, and has no byte-stability impact on the 9 KJV editions.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Code confirmed by direct reading:  1. VALIDATION GAP IS REAL. At sources.py:164, `url_override` is only checked for scheme prefix (`http://` or `https://`). Arbitrary internal hosts (169.254.169.254, internal-service.local) pass this check and a one-off Source is constructed from them.  2. CURRENT GUARD WORKS. Every active parser in PARSERS calls `_http.get(url, allowlist=DEFAULT_PD_SOURCES_ALLOWLIST)`, which invokes `_check_allowlist` *before* any network I/O (http.py:167). The one stub parser `_parse_ccel_text` returns None immediately without making any HTTP call. The bare `except Exception

### 36. [LOW] trusted_html claim for lxx-greek and greek-nt has no ingest-time enforcement — HTML-special chars would be emitted raw

- **Dimension:** security  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/core/popup_versions.py:132-138`
- **Evidence:** `_TRUSTED_HTML: frozenset[str] = frozenset({'wlc', 'lxx-greek', 'greek-nt'})` with comment 'verified free of HTML-special chars at ingest (0 verses contain <>&)'. In generate_verse_popups.py:43: `body = text if v.get("trusted_html") else _html.escape(text)` — trusted versions pass through raw. But extract_lxx_swete.py's `_clean_greek()` function (lines 101-104) only strips Unicode sigla and bracket markers; it does NOT assert or strip `<`, `>`, `&`. Similarly, extract_byzantine_nt.py's `_clean_greek_nt()` (lines 37-38) only strips pilcrows and whitespace. No test verifies the absence of HTML-special characters in the ingested translation files. If either upstream CSV is regenerated from a source that has `&` (e.g. XML-escaped entities like `&alpha;`) or `<`, those characters would be placed raw into the EPUB `<aside class="vnote">` HTML without escaping.
- **Fix:** Add a guard loop in each extractor's `write_translation`, immediately before the `.write_text()` call, that asserts no verse contains HTML-special characters. For `extract_lxx_swete.py` (after line 173, inside the `for code in sorted(by_code):` loop):

```python
for c, v, t in by_code[code]:
    if any(ch in t for ch in ('<', '>', '&')):
        raise ValueError(f"{TRANSLATION_ID} {code} {c}:{v} contains HTML-special char: {t!r}")
```

Apply the identical guard in `extract_byzantine_nt.write_translation` (after line 98). This makes the documented "verified at ingest" claim mechanically enforced rather than a manual one-time assertion. It is a purely additive safety net: it fires only if upstream CSVs are replaced with corrupt/XML-encoded content, has no effect on current clean data, and does not touch any marathon-core file or alter the 9-KJV-edition output.
- **Verdict (1 skeptic[s]):** refuted=False conf=medium — I read all four cited files directly. The mechanics described in the finding are accurate: (a) `_TRUSTED_HTML` in `popup_versions.py:138` includes `lxx-greek` and `greek-nt`; (b) `generate_verse_popups.py:43` passes trusted versions raw without `html.escape`; (c) `extract_lxx_swete._clean_greek()` (lines 101-104) and `extract_byzantine_nt._clean_greek_nt()` (lines 37-38) strip sigla/pilcrows but perform no assertion that `<`, `>`, or `&` are absent; (d) there is no test that verifies HTML-special-char absence. However, the *currently ingested* data is clean: Grep across all 50 `lxx-swete-greek

### 37. [LOW] Note label field injected into EPUB HTML without HTML-escaping in build_aside()

- **Dimension:** security  ·  **kind:** find
- **Location:** `YHWH v2.4/scripts/inject.py:216-220`
- **Evidence:** In build_aside(): `f' <span class="note-label">{label}</span> '` — `label` (note tuple index 6, stored verbatim from the API payload via dict_to_tuple at web_helpers.py:144) is interpolated directly without html.escape(). The note `body` (index 7) correctly goes through sanitize_html at line 209, but `label` does not. A publisher-saved note with label='<script>alert(1)</script>' would emit that tag verbatim into the EPUB HTML file. Same code also emits `kind`, `full_id`, `cat`, and `cat_label` raw, though those are constrained by the config vocabulary.
- **Fix:** The proposed fix is correct and safe as written. Apply `html.escape()` to `label` before interpolation in `build_aside()` at inject.py:220. The `cat_label` escape is also correct since it appears in an HTML attribute at line 219. No changes to marathon core, no schema changes, and no impact on the 9 KJV editions (their labels are plain ASCII). The fix:

```python
safe_label = html.escape(str(label or ""))
safe_cat_label = html.escape(str(cat_label or ""))
```

Then replace `{label}` with `{safe_label}` at line 220 and `title="{cat_label}"` with `title="{safe_cat_label}"` at line 219. The `glyph` variable is derived from `glyph_for(kind)` (config-controlled) and does not need escaping. The `kind` variable appears in class/id attributes and is constrained by the config vocabulary (lowercase alpha), so it is low priority but wrapping it in `html.escape()` is harmless if desired for completeness.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Code confirmed at inject.py:189-223: `build_aside()` receives `label` as a plain string parameter and interpolates it directly at line 220 via `f' <span class="note-label">{label}</span> '` without any escaping. The `body_html` at line 209 correctly passes through `sanitize_html()`, but `label` does not. The label originates from tuple index 6, loaded via `ast.literal_eval` from the stored `.py` corpus (notes_io.py:193). The corpus is written by `write_book` (web_helpers.py:182) using Python `repr()` of whatever string came from the web API payload via `dict_to_tuple` (web_helpers.py:144) — no

### 38. [LOW] Tautological lru_cache test: `hits >= 0` can never fail

- **Dimension:** tests  ·  **kind:** find
- **Location:** `YHWH v2.4/tests/test_canonical_verse_counts.py:137-146`
- **Evidence:** ```python
def test_repeat_calls_are_cached(self):
    """The helper is decorated with lru_cache; second call is a hit."""
    canonical_book_shape("gen")
    info = _book_shape_cached.cache_info()
    assert info.hits >= 0  # at least the count is exposed; non-zero hits
```
The docstring says "second call is a hit" but the body only calls `canonical_book_shape("gen")` ONCE. After one call the cache has `hits=0` (first call is always a miss). The assertion `info.hits >= 0` is trivially satisfied because `CacheInfo.hits` is a non-negative integer by Python stdlib contract — it is literally impossible for it to be negative. This means: (a) if `@lru_cache` is removed from `_book_shape_cached` and replaced with any function that exposes `.cache_info()` returning an object with `hits=0`, the test still passes; (b) if someone adds a second call to `canonical_book_shape("gen")` but the cache is broken (e.g., cache key mutated), the test still passes because `hits` only needs to be `>= 0`. The S7 rule (lru_cache discipline) and S8 (tests that would catch the demo breaking) are both violated.
- **Fix:** The finder's fix is correct. Apply as-is to C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\tests\test_canonical_verse_counts.py lines 137-146:

```python
def test_repeat_calls_are_cached(self):
    """The helper is decorated with lru_cache; second call is a hit."""
    from scripts.core.canonical_verse_counts import canonical_book_shape, _book_shape_cached
    _book_shape_cached.cache_clear()  # isolate from prior test calls
    canonical_book_shape("gen")  # miss
    canonical_book_shape("gen")  # hit
    info = _book_shape_cached.cache_info()
    assert info.hits >= 1, f"expected at least one cache hit after two calls; got hits={info.hits}"
```

No changes to production code, build pipeline, or marathon core needed.
- **Verdict (2 skeptic[s]):** refuted=False conf=high — Independently verified by reading both the test file (lines 137-146) and the implementation in scripts/core/canonical_verse_counts.py. The facts are:  1. `canonical_book_shape("gen")` (line 157 of the impl) calls `_book_shape_cached("gen")` exactly once, making it a cache MISS, not a hit. 2. After one call, `_book_shape_cached.cache_info().hits` is 0. The assertion `info.hits >= 0` is trivially satisfied since CacheInfo.hits is a non-negative integer by Python stdlib guarantee. 3. The docstring says "second call is a hit" but there is no second call in the test body. 4. The comment `# at least

### 39. [LOW] Redundant tautological assertion `chapters_collated >= 0` immediately superseded by `>= 1`

- **Dimension:** tests  ·  **kind:** find
- **Location:** `YHWH v2.4/tests/test_manuscript_kings.py:67`
- **Evidence:** ```python
assert rep["chapters_pending"] + rep["chapters_collated"] == 47
assert rep["chapters_collated"] >= 0   # line 67 — TAUTOLOGICAL
# Positive pin: 1ki:1 is calibrated+collatable now, so at least one collated.
assert rep["chapters_collated"] >= 1   # line 69 — supersedes line 67
```
`rep["chapters_collated"]` is constrained to `[0, 47]` by the accounting invariant on line 66, so `>= 0` is trivially true. The comment on line 68 acknowledges the intent is `>= 1`, making line 67 dead code. Any regression that sets `chapters_collated = -1` would first fail the accounting invariant on line 66 (`pending + collated == 47` would be violated), not line 67. The `>= 0` assert is unreachable as a standalone catcher.
- **Fix:** Delete line 67 only. The surrounding context remains unchanged:

```python
assert rep["chapters_total"] == 47
# Accounting invariants that hold throughout the marathon.
assert rep["chapters_pending"] + rep["chapters_collated"] == 47
# Positive pin: 1ki:1 is calibrated+collatable now, so at least one collated.
assert rep["chapters_collated"] >= 1
```

The finder's proposed fix is correct and safe as stated.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Read lines 59-79 of C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\tests\test_manuscript_kings.py directly. The code is exactly as described: line 66 asserts `pending + collated == 47` (which bounds collated to [0,47]), line 67 asserts `collated >= 0` (trivially satisfied by that bound and by the non-negative nature of the count), and line 69 asserts `collated >= 1` (the real meaningful floor). The `>= 0` assert on line 67 cannot independently catch any regression: if collated were somehow -1, line 66 would fire first (47 - (-1) = 48 != 47). Line 69 then re-asserts the stricter real floor. 

### 40. [INFO] REPO_MAP test-file count stale: claims 169, actual is 178

- **Dimension:** docs  ·  **kind:** find
- **Location:** `YHWH v2.4/dev/REPO_MAP.md:17`
- **Evidence:** '169 pytest files (`test_*.py`) + `conftest.py` + `fixtures.py` + `fixtures/`'

Grep for 'def test_' across tests/test_*.py finds 178 matching files. SESSION_STATE batch-1 updated REPO_MAP to 169, but batch-1 itself added +3 new test files and batch-2 added +2 more — neither was reflected back into REPO_MAP. The check_repo_map_complete lint deliberately skips prose counts so this cannot be auto-caught.
- **Fix:** In C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\dev\REPO_MAP.md line 17, change "169 pytest files" to "178 pytest files". Given that this count drifts with every new test file, the finder's alternative of "170+ pytest files" is the more durable choice — it avoids future staleness without requiring the lint to enforce an exact count.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Read REPO_MAP.md line 17 directly — it states "169 pytest files (`test_*.py`)". Ran Grep in count mode across `tests/test_*.py` in the actual repo, which returned "Found 90459 total occurrences across 178 files." The count is off by 9. The finding is factually confirmed. Impact is limited to a developer-facing documentation file; there is zero effect on EPUB output, byte stability, runtime behavior, or the 9 KJV editions. The `check_repo_map_complete` lint intentionally skips prose counts so this cannot self-correct. Severity should be downgraded from medium to info: it is purely a stale numbe

### 41. [INFO] REPO_MAP §dev omits dev/SESSION_PLAYBOOK.md

- **Dimension:** docs  ·  **kind:** find
- **Location:** `YHWH v2.4/dev/REPO_MAP.md:48`
- **Evidence:** §dev Bootstrap + state line: 'CLAUDE_PROJECT_RULES.md (rules), SESSION_STATE.md (live snapshot), PLAN_2026-05-29-roadmap.md (master plan), IN_FLIGHT.md (live tracker), CHANGELOG.md, MATRIX_MAP.md (data-flow), REPO_MAP.md (this).'

dev/SESSION_PLAYBOOK.md exists and is explicitly referenced in CLAUDE_PROJECT_RULES.md §0 as 'Lifecycle companion: dev/SESSION_PLAYBOOK.md — the order-of-operations guide (session start → work → verify → finish-clean) with the consolidated verification gates'. It is absent from the REPO_MAP §dev listing.
- **Fix:** Add SESSION_PLAYBOOK.md to REPO_MAP.md line 48's §dev Bootstrap + state bullet. The finder's proposed text is correct: insert `SESSION_PLAYBOOK.md (session lifecycle + verification gate commands)` between `MATRIX_MAP.md (data-flow)` and `REPO_MAP.md (this)`. No other change needed.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Independently verified all three facts the finder claims. (1) `dev/SESSION_PLAYBOOK.md` physically exists (Glob confirms). (2) REPO_MAP.md line 48 lists the §dev Bootstrap + state bullet and SESSION_PLAYBOOK.md is absent from it — confirmed by direct Read. (3) CLAUDE_PROJECT_RULES.md explicitly names SESSION_PLAYBOOK.md as a "Lifecycle companion" at §0 (line 57) and references it again at line 95. The omission is real. Impact is documentation-only: no EPUB output, no runtime behavior, no byte-stability concern. The blast radius is bounded to navigability — a session consulting REPO_MAP won't d

### 42. [INFO] cross_refs_stripped build stat overcounts — subn returns total matches, not just strippings

- **Dimension:** opt-build  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/build_edition.py:2180-2193`
- **Evidence:** ```python
new_text, n1 = link_re.subn(_check_anchor, text)
stats["cross_refs_stripped"] += n1
...
new_text2, n2 = file_only_re.subn(_check_file_only, new_text)
stats["cross_refs_stripped"] += n2
```
`re.subn` returns the count of ALL pattern matches (substitutions attempted), not the count where the replacement string differed from the original. `_check_anchor` returns `m.group(0)` (unchanged string) for valid links, and the visible text (stripped) for dangling links. So `n1` = total cross-references scanned, not just those stripped. `n2` similarly overcounts file-only references. This inflated value propagates to the `.stats.json` sidecar via `_write_stats_sidecar` and to the build console output.
- **Fix:** The proposed fix is correct. Use a nonlocal integer incremented only in the stripping branch of each callback, then add that to the stat instead of using the subn return count. For _check_anchor: initialise stripped_n1 = 0 before the def, add nonlocal stripped_n1, increment it only in the two `return visible` branches, then do `stats["cross_refs_stripped"] += stripped_n1` in place of `+= n1`. Mirror the pattern for _check_file_only with stripped_n2. The _ placeholder can replace the now-unused subn count. No changes to the file-writing path (line 2195-2196), EPUB output, or byte-gate are needed.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — Confirmed by reading the actual code at C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\build_edition.py lines 2168-2193. The finding is factually correct: `re.subn` returns the count of every pattern match (every invocation of the replacement callable), not only the invocations where the returned string differed from the matched text. `_check_anchor` returns `m.group(0)` (unchanged) for valid links and `visible` (stripped) for dangling ones, but `subn` counts both paths identically. So `n1` = total `<a href="...#...">` anchors scanned, not dangling anchors stripped; `n2` = total fil

### 43. [INFO] Ingest pipeline orchestration: CONFIRM-OPTIMAL — the ~10 driver shape is the right architecture

- **Dimension:** opt-ingest  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/core/at_scale_base.py:1-143`
- **Evidence:** The mint-7 D1 extraction correctly consolidated `candidate_to_dict`, `NT_BOOKS`, ANSI colors, `iter_target_verses`, and `resolve_books` into `at_scale_base`. The 10 `write_queue` copies retain distinct semantics (append-all vs. kind-replace vs. content-hash-dedup), which is load-bearing differentiation — not cargo-cult duplication. The AI drivers correctly adopt `parallel_map` for I/O-bound API calls; the non-AI drivers run serially (data is in-memory, no I/O bottleneck). There is no better shape: a single unified driver would require encoding every source's heterogeneous iteration pattern (TSK=book/chapter/verse dict, Nave=reverse-index, KJV text-required for hebrew/greek, commentary=verse lookup, etc.) into a single abstraction that would be more complex than the current per-driver files.
- **Fix:** The proposed `append_candidates(out_path, new_dicts, *, replace_kind=None)` in `at_scale_base.py` is the right direction but covers only 8 of 9 drivers. Kenyon's content-hash-dedup (`run_kenyon_at_scale.py` lines 64-76) is a third semantic variant not accommodated by `replace_kind`. A complete helper would need a fourth parameter, e.g. `dedup_key_fn: Callable | None = None`, where kenyon passes `lambda c: (c["verse"], c["kind"], c["draft_body"])`. Without that, kenyon stays as a local copy. The collapse from 9 copies to 1 (plus 1 for kenyon, or 1 with the dedup_key_fn extension) is a genuine quality improvement but has no correctness impact on the current sequential-run mode — defer until a natural edit touches one of these files.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — I read all 9 non-manuscript write_queue implementations directly. The finder's taxonomy is accurate: there are exactly three semantic variants across the 9 copies.  Variant A — append-all, no dedup (naves, xref, torrey, ethiopian): read existing candidates list, append new ones with IDs continuing from len(existing). Four copies that are structurally near-identical, differing only in docstrings.  Variant B — kind-replace (hebrew `lang-hebrew`, greek `lang-greek`, ai_xrefs `xref-thematic`, ai_notes `comm-ai`): read existing, filter out any candidate whose `kind` matches the driver's own kind, t

### 44. [INFO] Shared AI detector instance across parallel threads mutates `last_usage` non-atomically

- **Dimension:** opt-ingest  ·  **kind:** optimization
- **Location:** `YHWH v2.4/scripts/run_ai_xrefs_at_scale.py:151-165`
- **Evidence:** `detector = detector_factory()` creates ONE detector (and one client, which holds `self.last_usage`). Then `parallel_map(_work, targets, workers=workers)` calls `detector.detect(...)` from N threads simultaneously. Inside `_default_completion_fn` (sources_ai_clients.py line 207): `self.last_usage = {...}`. N threads write to the same attribute concurrently. The final value is whichever thread finished last — the cost-verification telemetry read by the user (`client.last_usage` after the run) is stale/wrong. Same pattern in run_ai_notes_at_scale.py line 149-165.
- **Fix:** The finder's option (a) is the right fix: move `detector = detector_factory()` inside `_work` so each thread owns its own client instance and its own `last_usage`. The lru_cache'd `_anthropic_client()` singleton (and its connection pool) continues to be shared across threads, which is intentional and thread-safe per the Anthropic SDK. The per-thread `_AnthropicClient` wrapper is lightweight (no network setup).

In `run_ai_xrefs_at_scale.py`, replace lines 151-162:

```python
# BEFORE
detector = detector_factory()
...
def _work(t):
    book, chapter, verse_num, verse_text = t
    return (book, chapter, detector.detect(book, chapter, verse_num, verse_text))
```

```python
# AFTER
def _work(t):
    book, chapter, verse_num, verse_text = t
    det = detector_factory()
    return (book, chapter, det.detect(book, chapter, verse_num, verse_text))
```

Apply the identical change to `run_ai_notes_at_scale.py` lines 149-161. No other changes needed. The serial path (`workers <= 1`) is unaffected — `detector_factory()` is called once per verse either way. The `workers=1` default means this has zero regression risk for current usage.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — The finding is technically accurate. In `run_ai_xrefs_at_scale.py` (line 151) and `run_ai_notes_at_scale.py` (line 149), a single `detector` instance is created outside `_work`, then `_work` closes over it and is dispatched to N threads via `ThreadPoolExecutor` when `workers > 1`. Inside `_default_completion_fn` (`sources_ai_clients.py` line 207), `self.last_usage = {...}` is a plain instance-attribute write with no lock. Concurrent threads writing `self.last_usage` is a data race; the final value is whichever thread completes last.  However, severity must be calibrated to actual impact:  1. T

### 45. [INFO] CONFIRMED OPTIMAL: Vision-transcription marathon method (Patrologia Esther / Kings-Samuel) — MAX-1-heavy, tight crops, per-step commits, AGENT path

- **Dimension:** opt-vision  ·  **kind:** optimization
- **Location:** `YHWH v2.4/docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md:`
- **Evidence:** The ratified execution doctrine (AGENT path MAX-1-heavy-agent, tight region crops ≤1568 px, per-step commits, `/clear` between steps, controller renders PNGs to disk then passes paths) was designed to defeat three real OOM crashes caused by stacking whole-folio LANCZOS-upscaled images (~30–60 MB buffered per agent × 3 stacked). The _vision_notes.md convergence experience (findings (h)–(p)) confirms the method works: crash-recovery succeeds from agent transcripts, multi-pass adjudication catches errors single-pass misses, and the RAM discipline holds. With Opus 4 (1M context): (1) the OOM vector is IMAGE BYTES in memory, not text tokens — 1M context does not reduce the 10MB-per-folio RAM cost of image loading, so MAX-1-heavy remains correct; (2) tight crops are sharper per model token AND lower RAM — still optimal; (3) the AGENT path constraint (no paid API budget, no `anthropic` SDK installed) is unchanged; (4) Workflow orchestration is already in use (convergence workflows per _vision_notes.md (n)). One concrete refinement IS available but is evolutionary not structural: Opus 4's larger context could batch the final SYNTHESIS / cross-page consistency check (comparing all already-transcribed pages' JSON simultaneously to catch cross-page glyph-habit drifts like the ካ/ክ split) in a single medium-weight agent instead of the current page-by-page adjudication. This applies only to the synthesis step, never to the per-page transcription (which must stay MAX-1 for RAM).
- **Fix:** Confirmed optimal: keep MAX-1-heavy-agent, tight region crops ≤1568 px, per-step commits, /clear between heavy steps, AGENT path, controller-passes-paths not bytes. One evolutionary addition to consider when resuming Esther at p28: after completing a batch of 4–6 pages, run a single medium-weight Opus 4 synthesis agent with all completed pages' JSON in context (under 100k tokens total for ~6 pages of transcription output) to flag cross-page glyph-habit drifts before they propagate further. This replaces the ad-hoc cross-page checking the controller currently does manually. RAM cost: ~30–60 MB for text JSON vs 10 MB per image — well within the medium-agent budget. No plan edits required now; the existing per-page convergence workflow already covers this for individual pages.
- **Verdict (1 skeptic[s]):** refuted=False conf=high — I read the full plan at `YHWH v2.4/docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md` and the full `_vision_notes.md` at `YHWH v2.4/content/translations/sources/patrologia/_vision_notes.md`.  The _vision_notes.md confirms every empirical claim the finding makes:  1. MAX-1-heavy constraint validated by actual OOM crashes — the notes record THREE crash events (p26 OOM, p27 crashed twice) across the already-completed pages 24–27. Findings (l) and (n) explicitly attribute these to RAM pressure from stacked image bytes. The plan's "Never-single-thread" + concurrency cap (heavy >100k 


## Refuted (dropped — for the record)

| Sev | Dimension | Title | Why refuted (first skeptic) |
|-----|-----------|-------|------------------------------|
| MEDIUM | correctness | batch_insert_notes uses only on-disk notes to compute insertion offset for new notes in th | I read the actual code at lines 318–395 of YHWH v2.4/scripts/promote.py and traced the claimed failure scenario carefully.  The finder claims that two new notes |
| LOW | correctness | filter_books_for_canon Pass 1.5 reads post-splice files but id_inventory was built before  | I read the actual code at lines 2129-2196 in build_edition.py.  The finding's core concern is that Pass 2 modifies files (line 2196 `f.write_text`) without upda |
| LOW | security | theme_css injected into <style> block without sandboxing in preview HTML returned via JSON | I read preview.py lines 66-73 (theme CSS loading), line 384 (usage), and lines 412-440 (HTML composition). The unsanitized interpolation at line 419 is confirme |
| LOW | security | api_sources_cache_fetch url_override bypasses the SSRF allowlist at the validation layer ( | I read `scripts/api/sources.py` lines 163-187 and `scripts/core/http.py` in full, plus `scripts/fetch_sources.py`.  What the code actually does:  1. The scheme- |
| LOW | security | audit_log._summarize_args redacts secrets by kwarg name only; positional args are logged v | I read `_summarize_args` at lines 274-295 and `_short_repr` at lines 298-311 of `/YHWH v2.4/scripts/core/audit_log.py`. The finding accurately describes the cod |
| LOW | security | Content-Disposition filename in the EPUB download route is taken directly from the URL reg | Read lines 1570–1586 of YHWH v2.4/scripts/web.py directly. The finding's core claim is that the Content-Disposition header is set BEFORE api_download_export is  |
| INFO | security | The .env file exists on disk with an empty VOYAGE_API_KEY= and is not in .gitignore's carv | I read C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\.env directly: it contains exactly one line, `VOYAGE_API_KEY=`, with an empty value — no actual secret  |
| MEDIUM | code-debt | _iter_note_ref_traditions and _iter_note_ref_attribution_years are near-clone walkers with | I independently read both cited regions.  The finding is accurate in its structural description: the two functions share nearly identical boilerplate (directory |
| MEDIUM | tests | No test pins `coord_in_canonical_extent` rejection inside `promote_candidate` for the Tewa | I read all cited files directly.  The finding has two parts: (a) the canonical guard bypasses Tewahedo-distinctive books, and (b) there is no test pinning the h |
| MEDIUM | data-validity | coord_in_canonical_extent('aes', ch, v) returns False for ALL aes chapters including ch 10 | I read `canonical_verse_counts.py` lines 138-172 directly. The finder's analysis is correct that `_book_shape_cached("aes")` returns an empty tuple `()` (becaus |
| LOW | data-validity | html_chapter_count('aes') docstring incorrectly claims the promote guard does not block ae | I traced the full call chain by reading the actual source files.  `_book_shape_cached("aes")`: starts ch=1, calls `load_kjv_skeleton("aes", 1)` which filters `c |
| LOW | concurrency-caching | translations.versification_of() reads the book file on every call with no caching | The code at lines 227-241 of scripts/core/translations.py does exactly what the finder claims: it calls `path.read_text()` on every invocation with no caching,  |
| LOW | cross-module | bookcode_canonical lint rule does not cover the LINK_XREFS ABBREV map's usage via the rema | I read extract_naves_ccel.py lines 119–121 and lint_rules.py lines 1966–2046 directly.  The remap() function (line 121) returns: CCEL_ABBREV.get(a) or NAVES_BOO |
| MEDIUM | opt-vision | lint_rules.check_render_coverage_no_regression anchors legacy `"ex"` stem — will false-fai | I read lint_rules.py:977 and 1006 directly — both `expected_geez` and `expected_amharic` do contain `"ex"`. I confirmed via Glob that `ex.py` physically exists  |
| LOW | opt-vision | Three ref-id generators use `:02d` for chapter but `_aside_existing_re` was widened to `\d | All cited code was read directly. The three generators in build_edition.py (lines 145, 342, 2642) do use `f"ref-{prefix}{ch_i:02d}{vs_i:02d}{suffix}"`, and inje |
| INFO | opt-build | OPTIMIZATION EVALUATION — build pipeline is CONFIRM-OPTIMAL for cache-warm path; one concr | I read the actual code at lines 3008-3036 (build_edition.py) and the full build_epub.py. The finding's core claim — that in-process ThreadPoolExecutor threads p |
| MEDIUM | opt-ingest | `write_queue` in 8 non-AI drivers: read-modify-write is not protected against concurrent d | I read every relevant file directly. The TOCTOU pattern is real as code structure: each driver does read_text → atomic_write, and atomic_write (os.replace) only |
| MEDIUM | opt-ingest | `_AnthropicClient._valid_book_codes` lazy-init is a double-check without lock in parallel  | I read the actual code. `_valid_codes()` at lines 147-152 of `scripts/core/sources_ai_clients.py` is a lock-free lazy initializer. The concurrency scenario requ |
| MEDIUM | opt-ingest | `run_hebrew_at_scale.write_queue` silently deletes lang-hebrew candidates added by a prior | I read run_hebrew_at_scale.py lines 44-62, run_greek_at_scale.py lines 45-62, promote.py (update_queue_status lines 489-499 and the three call sites at lines 58 |
| LOW | opt-render | lint_rules.check_render_coverage_no_regression uses raw file stems (ex, est_patrologia) in | I read lint_rules.py lines 960-1052 and render_coverage.py lines 45-172, and confirmed the Glob output for geez-tewahedo.  Claim 1 — "ex" is non-canonical: The  |
| INFO | opt-render | RENDER-COVERAGE lane: CONFIRM-OPTIMAL with one gap; STANDALONE EN back-translation lane: f |  The finding claims the render-coverage lane is "CONFIRM-OPTIMAL" after applying two fixes from prior findings, but the claim is internally contradictory and th |

## Completeness-critic gaps (seed the next round)

- **inject.py build_aside() — label field injected raw into EPUB HTML** — The audit found this finding (`Note label field injected into EPUB HTML without HTML-escaping in build_aside()`), but the verification of the parallel path in scripts/core/preview.py was not done. preview._render_note_aside() at line ~120 c  _Lens:_ Read scripts/core/preview.py lines 115-145. Search for `note-label` and `label` across all injection paths (inject.py, matter_pages.py, web_content.py) and confirm html.escape() is applied at every output site, not just the one build_aside(
- **filter_books_for_canon Pass 1.5 TOC-block loop — unsorted tmp.glob() producing non-deterministic output** — The audit flagged this (finding: `filter_books_for_canon Pass 1.5 TOC-block loop uses unsorted tmp.glob()`). The audit concluded it is 'fragile but deterministic because each file's output is independent.' However, Pass 2 (`for f in tmp.glo  _Lens:_ Read build_edition.py filter_books_for_canon() lines 2129-2220. Count every `tmp.glob('*.html')` call and check whether the PROCESSING ORDER of any pass could affect the cross_refs_stripped stat or a file being written. The id_inventory dic
- **config.py lru_cache loaders — no cache invalidation after build_edition atomic writes to editions.yaml/kinds.yaml** — scripts/api/editions.py correctly calls config.load_editions.cache_clear() and matrix.compute_matrix.cache_clear() after every API mutation. BUT: config.load_kinds(), config.load_categories(), and config.load_books() have no documented inva  _Lens:_ Grep for `load_kinds.cache_clear`, `load_categories.cache_clear`, `load_books.cache_clear` across all of scripts/. If any code path rewrites those YAML files (migrations, admin endpoints), verify whether the lru_cache is cleared. Also check
- **Versification remap completeness — normalize_coord() in popup_versions.py is identity for all versions except wlc** — popup_versions.normalize_coord() docstring says 'B1: identity for every version (no per-source remaps yet)'. This means lxx-greek, vulgate, arabic, jps, douay all serve verse data without remapping from canonical KJV coords to their own num  _Lens:_ Read content/translations/vulgate-clementine/gen.py and content/translations/arabic-vandyke/gen.py — check whether the VERSES tuples use KJV chapter/verse numbering or the source's own. Cross-reference scripts/extract_vulgate.py (or equival
- **at_scale_base.iter_target_verses — lazy-import config/translations called inside a tight loop** — iter_target_verses() lazy-imports config and translations inside the function body, which is correct for avoiding circular imports. However, the actual verse iteration yields thousands of times, and the lazy import is re-checked on every ca  _Lens:_ Read scripts/core/at_scale_base.py iter_target_verses() and confirm whether config.books_by_code() is called per-iteration or once. Check whether books_by_code() is served from lru_cache (it is NOT — it's a non-cached wrapper). Determine if
- **corpus_index rebuild() — _CACHED_CONN reset outside rebuild lock creates a race with concurrent connection() callers** — The audit flagged this finding explicitly: '_CACHED_CONN reset in rebuild() is outside the rebuild lock — race with concurrent connection() calls in ThreadingHTTPServer'. But the fix domain was not explored. Specifically: connection() at li  _Lens:_ Read corpus_index.py lines 602-675 (rebuild post-build conn reset + connection() function). Map the exact execution interleaving where a ThreadingHTTPServer worker thread could enter connection() between a rebuilder's _CACHED_CONN=None assi
- **Test coverage of filter_html() with both disabled_kinds AND disabled_html_ref_ids simultaneously** — filter_html() has two independent filtering passes: kind-level (Phase lambda) and per-note-id (Phase rho.1). The audit found the per-note regex loop is O(|disabled_ids| * |text|). Test files test_scripts.py and test_traditions_psi8.py cover  _Lens:_ Search tests/ for calls to filter_html() that supply both a non-empty disabled_kinds set and a non-empty disabled_html_ref_ids set. If none exist, write a synthetic HTML fixture that contains a note of kind X (which is disabled) with an exp
- **matter_pages.py render_copyright_page — annotation_count argument not validated to exclude tradition/time-filtered notes** — The audit confirmed the finding 'Copyright page and About page embed matrix annotation count that ignores tradition/time filters.' render_copyright_page() receives annotation_count as a plain int parameter and renders it directly. The audit  _Lens:_ Read matter_pages.py render_about_page() and render_symbol_legend_page() for any annotation_count or category_count parameter. Grep build_edition.build_one() for every call to matter_pages.render_* and confirm each count argument is the pos
- **Standalone Bible build path (build_standalone.py) — not covered by any correctness findings** — The audit was explicitly told build_standalone.py is off-limits for edits (marathon core). However the correctness dimension should still have flagged bugs OBSERVED in its outputs (crashes, wrong data). The audit returned zero marathon-boun  _Lens:_ Read scripts/build_standalone.py's verse-lookup logic to confirm whether it uses scripts.core.translations.get_verse() (which would hit the same exo.py filename gap) or a different path. Verify that build_standalone.py for the geez-tewahedo
- **Reading plans — book code validation against canonical book list not audited** — scripts/core/reading_plans.py parses plan YAML files under content/reading_plans/. The _REF_RE regex captures a book code as `[a-z0-9]+` (any 1-4 lowercase alphanumeric) and returns it without validating it against books.yaml. A plan entry   _Lens:_ Read scripts/core/reading_plans.py parse_verse_ref() and load_plan(). Check whether the returned book_code is validated against config.books_by_code() keys. Search content/reading_plans/*.yaml for any book codes that match the legacy alias 
- **Geez/Amharic standalone Bible — apparatus JSON sidecar not covered by any tests** — scripts/core/standalone_store.py generates both a VERSES .py file and a _apparatus.json sidecar for each book. The exo.py/ex.py filename mismatch finding covers the VERSES store. The apparatus.json sidecar is a parallel artifact that is als  _Lens:_ Grep tests/ for 'standalone_store' or 'apparatus'. If no tests exist, verify whether build_standalone.py loads the apparatus sidecar and what happens on a missing-file error (silent degradation vs crash). Confirm the apparatus filename is g
- **batch_insert_notes dedup body-only check — fixed body + repaired attribution is silently dropped** — The audit found this: 'batch_insert_notes dedup checks only body, not attribution — prevents attribution repair on previously-promoted notes.' The finding was confirmed but the FIX direction was not analyzed. Changing the dedup key to inclu  _Lens:_ Read scripts/promote.py batch_insert_notes() and scripts/core/notes_io.load_notes(). Determine whether promote.py has a 'note already exists' guard that checks attribution separately from the body-dedup. Confirm whether the correct fix is (