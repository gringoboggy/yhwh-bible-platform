# Light post-Wave-3 audit — FINDINGS (2026-05-25)

**Audited HEAD:** `8a48ed3` (the audit-prep doc commit sitting one above the Wave-3
final `61226c5`; +39/−1, docs only).
**Scope:** `dev/AUDIT_2026-05-25-wave3-scope.md` — the light solo-Claude audit after
Wave 3 (3 infra prereqs + 7 features, `25e22cf`→`61226c5`).
**Environment:** this machine — `pythoncore-3.14-64\python.exe`, `PYTHONUTF8=1`,
Java 8 (1.8.0_491). All gates run from scratch.

## Verdict

**PASS** — Wave 3 is sound and current. Every integrity gate is green from scratch;
all three representative EPUB editions are epubcheck-clean; corpus + matrix intact.
One **pre-existing test-isolation bug** (full-sweep-only) was found and **fixed at
source** + hardened; six documentation-currency gaps were **fixed in-session**. Two
environment notes recorded. The project proceeds to **Wave 4** (productionization →
downloadable desktop app).

## A. Clean state + verification gates (from scratch)

| Gate | Result |
|---|---|
| `git status` | clean before the audit (HEAD `8a48ed3`) — only this audit's edits follow |
| E:/F: backup | `…-wave3-61226c5.bundle` (389.9 MB) present on **both** E: and F: |
| `lint_rules` | **16 / 0 / 0** |
| `ruff format --check .` | clean (1005 files) |
| `verify` | **errors=0** · 24015/24015 paired (84 warn / 608 info — pre-existing, non-fatal) |
| `validate_taxonomy` | **69969 / 69969 (100%)** · schema sound |
| `trace_matrix` | **0** unresolved (10 filtered editions OK) |
| `trace_repo` | **0** undocumented (10 top-level dirs) |
| epubcheck `ethiopian-tewahedo` (flagship, 23.89 MB) | **0/0/0/0** |
| epubcheck `catholic-study` (23.28 MB) | **0/0/0/0** |
| epubcheck `jewish-study` (tanakh small-canon, 16.36 MB) | **0/0/0/0** |
| test sweep (8 files, 1123 tests) | **1123 passed / 0 failed** (10m33s) after the Finding 1 fix |

Note: epubcheck required `--jar` (see Finding 2). All three exercise canon-filtered
popups + the topical index; the small-canon edition confirms filtering is clean.

## B. Wave-3 currency

- **MATRIX_MAP — FIXED.** Three stale "PLANNED Wave 3" labels (the `marker_style`
  trace row + the base-re-bake prose + the topical-index back-matter line) flipped to
  shipped. Added the missing data-flows: #6 unset popup default →
  `DEFAULT_POPUP_WITNESSES` (kjv excluded) + the last-resort English **KJV-floor**;
  #7 the build-time topical pipeline (`inject_back_matter(…, canon_books)` →
  `build_topic_index` canon-filter → `render_topical_index_page`) and the per-edition
  `renumber_markers` post-pass in `build_one`. Matter-pages note updated for the
  prereq-2 `scripts/matter_pages.py` extraction.
- **marker_style — OK.** Declarative field; `MARKER_STYLES = {"numbers"}` with `badge`
  deferred and correctly rendered `disabled` ("coming soon") in `/customize`
  (`customize.py:417`). Realized base-wide by the re-bake; field records the choice.
- **KJV-floor fallback — FIXED (doc).** Design spec §4.3 now records the deviation:
  English is kept only where no original-language witness exists (avoids empty popups
  / RSC-012 dangling vnote links); dropped everywhere a real witness is present;
  standalone Bibles (`popup_languages_default = []`) unaffected.
- **Dead code — OK (not dead).** `ALL_POPUP_LANGUAGES` has live call sites: the strip
  loop (`build_edition.py:979`), input validation (`api/editions.py:705`), and
  `/customize` enumeration (`web.py:1465`) — a distinct role from
  `DEFAULT_POPUP_WITNESSES` (the unset default). No orphaned popup machinery. (vulture
  not installed here; answered by reference grep.)
- **REPO_MAP — OK.** `repo_map_complete` (lint) + `trace_repo` both pass; the index is
  dir-level and the new Wave-3 files fall under already-documented dirs.

## C. Loose ends

- **EPUB size — OK.** Flagship 23.89 MB. `topical.xhtml` measured inside the built
  EPUB: **1264 KB uncompressed / 265 KB compressed** — the heaviest single XHTML by
  158× (next is `nav.xhtml` at 8 KB), ~1.1% of the EPUB. epubcheck clean.
- **PLAN — updated.** Wave 3 marked ✅ DONE; Wave 4 marked ◀ NEXT ACTIVE WAVE; the
  stale "Phase 1 (in flight) / UNCOMMITTED" status block refreshed to "Waves 0–3
  shipped".
- **[USER] device eyeball (unchanged, reader-only):** inline footnote numbers ·
  in-note category symbol + its legend tap-through · widened popups (He/Gr/La/Ar, no
  English where originals exist) · the topical index — on Apple Books / e-ink.

## Findings & fixes

### 1. [FIXED] Test-isolation bug — full-sweep-only `test_marker_glyphs` failure

The first full sweep failed **1 / 1123**:
`test_marker_glyphs::TestGlyphForDataDriven::test_all_15_category_symbols_reachable`
→ `category symbols never produced by any kind: {'lang': '✎'}`.

**Root cause (confirmed by reproduction):** `test_save_category_round_trip` and
`test_save_kind_round_trip` (`tests/test_scripts.py`) call `api_save_category` /
`api_save_kind`, which write the yaml **and** `cache_clear()` the
`load_categories` / `load_kinds` `@lru_cache(maxsize=1)` singletons — so the next read
**repopulates** the cache from the *modified* file (`lang → ✎`). Their `finally`
restored only the **file** (`shutil.copy`), never re-clearing the cache, so the stale
`lang → ✎` leaked into the later glyph test (which reads the singleton and finds no
kind produces `✎`, since the real `lang` kinds resolve to `⌘`). The victim passes in
isolation (19/19); files are **not** corrupted on disk (cache-only; `git status`
clean).

**Fix — source (the real root cause):** both round-trip tests now `cache_clear()`
`load_categories` / `load_kinds` + `compute_matrix` in `finally` **after** restoring
the file (RULES §7.1 — symmetric with what `api_save_*` itself clears). Minimal
reproduction (`save_category` + `save_kind` + the glyph test) flips **red → green**
(1 failed → 3 passed).

**Fix — defense-in-depth:** `test_all_15_category_symbols_reachable` now clears the
singletons at its start, making it state-independent (RULES §8 "state-aware over
default-assumed").

**Verified:** full re-sweep after the fix = **1123 passed / 0 failed** (10m33s); the
JPS transient the scope explicitly flagged did **not** recur (`test_popup_witnesses`
fully green in both sweeps — only `test_marker_glyphs` ever failed).

**Follow-up (flagged, not done):** a `conftest` autouse fixture that snapshots/clears
the config singletons between tests would prevent the entire class of cross-test
config-cache pollution (this is the same class as the JPS transient the scope flagged).
Left for a deliberate decision — broader than this light audit.

### 2. [ENV — recommend] epubcheck auto-discovery picks an unparseable wrapper

`scripts/epubcheck.py::find_epubcheck` resolves the PyPI `epubcheck.exe` PATH wrapper
(step 3) **before** the bundled jar. On this box the wrapper's stdout is not matched by
`SUMMARY_RE` → "could not parse epubcheck output" (exit 2) for every edition. The
bundled jar works perfectly via `--jar
…\site-packages\epubcheck\epubcheck.jar` (Java 8 → `0 fatals / 0 errors / 0 warnings
/ 0 infos`). **Recommend:** set `EPUBCHECK_JAR`, or have `ship-check`/preflight pass
`--jar`, or have `find_epubcheck` prefer the bundled package jar over the PATH wrapper.
Not fixed in-session — it touches cross-platform discovery order (the wrapper is
correct on brew/apt Linux/macOS), so flag for a deliberate call.

### 3. [NOTE — low] trace_repo `exports` census

`trace_repo` reported `exports files=18 .epub` while the directory held **0** epubs
(only `.cache/`) before the audit builds. The enforced check (undocumented dirs = 0)
passed and `exports/` is gitignored/regenerable, so this is cosmetic. Re-verify the
census source post-audit if convenient.

## Files changed by this audit

- Currency: `dev/MATRIX_MAP.md`, `dev/PLAN_2026-05-24-end-scope.md`,
  `docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md`
- Finding 1 fix: `tests/test_scripts.py`, `tests/test_marker_glyphs.py`
- `dev/AUDIT_2026-05-25-wave3-FINDINGS.md` (this file) · `dev/SESSION_STATE.md` (NEXT → Wave 4)
