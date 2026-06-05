# Edition Cover + Truthful Front Matter — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every built edition a clean "HOLY BIBLE" cover (overflow-proof) + a "Your Edition" first page, with counts and a symbol glossary that are **build-accurate** — i.e. they honor the ρ.3 hierarchical per-book/chapter/note choices — plus default covers for the Ge'ez/Amharic standalone Bibles.

**Architecture:** A single build-accurate counter (`resolved_note_counts`) becomes the source of truth for every "what you built" surface, computed by reusing the build's own note-filter resolution so the printed numbers always equal the real EPUB. The cover compositor draws a fixed main title + a builder-chosen subtitle with a wrap-then-shrink fitter that can't overflow. The front matter is reordered to lead with a truthful "Your Edition" page; the glossary stays a separate symbol reference but is repointed at the new counter.

**Tech Stack:** Python stdlib backend; Pillow (cover composition); the existing matter-page renderers (`scripts/matter_pages.py`); `editions.yaml` flat-field schema; pytest. No new runtime deps (Pillow + epubcheck/Java already used).

**Status:** SHIPPED 2026-06-04 — all 6 phases (σ.1–σ.6) complete, subagent-driven (per-task spec + code-quality review + visual QA), 5-leg pushed. epubcheck 0/0/0/0, byte-stability determinism gate + the σ.1 cross-check (resolved counts == built EPUB) green. σ.1 caught/fixed 2 pre-existing build bugs (2-Esdras orphan-spillover + a stray base marker). Spec: `docs/superpowers/specs/2026-06-04-edition-cover-and-truthful-front-matter-design.md`. Executor: Windows. σ phase tag.

---

## Pre-flight (read once)

- Spec §3 (the design), §3.4 (the build-accurate counter — the crux), §6 (byte-stability obligations), §8 (phasing).
- **Patterns / seams to read first (locate by NAME — `build_edition.py` line numbers shift):**
  - `scripts/build_edition.py` → `build_one`: find where it assembles `disabled_kinds_for_filter` and `disabled_html_ref_ids` (search those identifiers + `compute_symbol_disabled_html_ref_ids` + `force_on`). This is the resolution σ.1 must reuse. Also `apply_edition_cover`, and the front-matter injection block (search `inject_copyright_page` / `inject_symbol_legend_page` / `inject_about_page`).
  - `scripts/build_edition.py` → `_iter_note_ref_symbols` (yields per-note `(ref_id, note_id, book, chapter, verse, suffix, kind, category)`) — the corpus iterator σ.1 tallies over.
  - `scripts/core/config.py` → `enabled_kind_codes` (edition-wide) + `enabled_kind_codes_for(edition, all_kinds, book, chapter)` (per-coordinate).
  - `scripts/matter_pages.py` → `_legend_categories_for_edition` (:~245), `render_symbol_legend_page` (:~267), `inject_symbol_legend_page` (:~301), `render_about_page` (:~411), `inject_about_page`, and the front-matter inject order.
  - `scripts/generate_edition_covers.py` → `_compose_cover` (:~139), `_fit_title_font` (:~129), `EDITIONS` (:~52), `title_for_edition` (:~65), the geometry consts (`FINAL_WIDTH/HEIGHT`, `TITLE_MARGIN_X`, `TITLE_MAX_WIDTH`, `TITLE_CENTER_Y`, `TITLE_FONT_MAX/MIN`, `FONT_TITLE_PATH`).
  - `scripts/core/covers.py` → `COVER_TEMPLATES`, `resolve_cover_path`. `scripts/api/covers.py` → `api_apply_cover_template`. `scripts/api/editions.py` → `EDITABLE_TEXT`, `api_save_edition_meta`, `api_customize_data`. `scripts/templates/customize.py` → the cover-template picker + `buildCustomizePayload`/`saveEdition`.
  - `scripts/build_standalone.py` → `build_standalone` (cover no-op ~:276).
  - `scripts/core/matrix.py` → `note_counts_for_edition` (:~414, the stale "actually-shipping" docstring), `breakdown_by_category` (:~425), `potential_for_kind`.

**Windows env (every test run):** `$env:PYTHONUTF8="1"`; `$env:PYTHONPATH="C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4"`; `py -3`; pytest `--basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`; **one test file at a time** (RAM); PowerShell only (the repo path has a space). `ruff format` changed files before each commit (the pre-commit hook runs `ruff format --check .` + `lint_rules.py` + mypy). Per-task LOCAL commit via `pwsh -File save.ps1 -Message "…"`; full 5-leg `save-all.ps1` at each phase close.

**Edition-mutation isolation (for any test that writes `editions.yaml`):** mirror `tests/test_build_my_bible_c2_4.py::_IsolatedEdition` — `shutil.copy` backup + `try/finally` restore + `config.load_editions.cache_clear()` + `matrix.compute_matrix.cache_clear()`. After such tests, `git status --short content/editions.yaml` MUST be clean.

**Byte-stability note:** σ.2 + σ.3 deliberately change the cover + front-matter output for ALL editions (intended). After σ.3 close, re-run the determinism gate (`tests/test_byte_stability_gate.py`) — it checks build-twice equality, which still holds; if any stored digest baseline exists for cover/matter bytes, re-pin it. Do NOT treat the intended cover/matter change as a regression.

---

## Phase σ.1 — Build-accurate counter (headless; the foundation)

**Files:**
- Create: `scripts/core/edition_stats.py`
- Modify: `scripts/build_edition.py` (extract a reusable filter-set helper from `build_one`)
- Test: `tests/test_edition_stats.py` (new)

### Task σ.1.1: Extract the build's filter-set computation into a reusable helper

The build already computes, inside `build_one`, the two sets that decide which notes ship: `disabled_kinds_for_filter` (whole-kind strip) and `disabled_html_ref_ids` (per-ref overrides incl. tradition/time/per-book-chapter symbol OFF, minus force-on). Factor that into one function so the counter and the build agree by construction.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_edition_stats.py
from __future__ import annotations


def test_filter_sets_helper_exists_and_shapes():
    from scripts.build_edition import compute_edition_filter_sets
    from scripts.core import config

    ed = config.editions_by_id()["catholic-study"]
    disabled_kinds, disabled_ref_ids = compute_edition_filter_sets(ed)
    assert isinstance(disabled_kinds, set)
    assert isinstance(disabled_ref_ids, set)
```

- [ ] **Step 2: Run it — expect ImportError**

Run: `$env:PYTHONUTF8="1"; $env:PYTHONPATH="C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4"; py -3 -m pytest tests/test_edition_stats.py -q --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: FAIL (`cannot import name 'compute_edition_filter_sets'`).

- [ ] **Step 3: Implement the extraction.** In `scripts/build_edition.py`, find the lines inside `build_one` that build `disabled_kinds_for_filter` and `disabled_html_ref_ids` (search those names + `compute_symbol_disabled_html_ref_ids`). Move that logic verbatim into a new module-level function and call it from `build_one` (no behavior change — `build_one` now calls the helper):

```python
def compute_edition_filter_sets(edition: dict) -> tuple[set[str], set[str]]:
    """Return (disabled_kinds_for_filter, disabled_html_ref_ids) — exactly the
    two sets build_one uses to strip notes. Single source of truth for "what
    ships" so edition_stats.resolved_note_counts matches the built EPUB.
    Folds in: edition-wide disabled kinds (minus symbol-overridden kinds),
    per-book/chapter symbol OFF, tradition + time filters, force-off note ids,
    minus force-on note ids."""
    # <-- the exact body lifted from build_one; preserve every line/order -->
```

Then in `build_one`, replace the inlined block with `disabled_kinds_for_filter, disabled_html_ref_ids = compute_edition_filter_sets(edition)`.

- [ ] **Step 4: Prove zero behavior change (byte-stability).** Run the determinism gate once:

Run: `$env:PYTHONUTF8="1"; $env:PYTHONPATH="C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4"; py -3 -m pytest tests/test_byte_stability_gate.py -q --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: PASS (the extraction is a pure refactor — builds unchanged).

- [ ] **Step 5: Run the new test — expect PASS.** Then commit:

```
pwsh -File save.ps1 -Message "σ.1.1: extract compute_edition_filter_sets from build_one (reusable, zero behavior change)"
```

### Task σ.1.2: `resolved_note_counts` — tally what actually ships

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_edition_stats.py  (append)
def test_resolved_counts_match_no_override_edition():
    from scripts.core import edition_stats, config
    ed = config.editions_by_id()["catholic-study"]
    rc = edition_stats.resolved_note_counts(ed)
    assert rc["total"] > 0
    assert sum(rc["per_book"].values()) == rc["total"]
    assert sum(rc["per_category"].values()) == rc["total"]
    assert isinstance(rc["popup_languages"], list)


def test_resolved_counts_honor_per_book_off(tmp_path):
    # Turning a family OFF for one book drops exactly that book's notes of that
    # family from the totals — proving hierarchy-awareness.
    import shutil
    from pathlib import Path
    from scripts.core import config, edition_stats
    import scripts.web as web

    REPO = Path(__file__).resolve().parent.parent
    yml = REPO / "content" / "editions.yaml"
    backup = tmp_path / "ed.bak"
    shutil.copy(yml, backup)
    try:
        config.load_editions.cache_clear()
        before = edition_stats.resolved_note_counts(config.editions_by_id()["catholic-study"])
        web.api_save_edition_meta("catholic-study", {"note_families_off_per_book": {"gen": ["xref"]}})
        config.load_editions.cache_clear()
        from scripts.core import matrix as m; m.compute_matrix.cache_clear()
        edition_stats.resolved_note_counts.cache_clear()
        after = edition_stats.resolved_note_counts(config.editions_by_id()["catholic-study"])
        assert after["total"] < before["total"]              # some gen xrefs dropped
        assert after["per_book"].get("gen", 0) < before["per_book"]["gen"]
    finally:
        shutil.copy(backup, yml)
        config.load_editions.cache_clear()
        from scripts.core import matrix as m2; m2.compute_matrix.cache_clear()
        edition_stats.resolved_note_counts.cache_clear()
```

- [ ] **Step 2: Run — expect FAIL** (`No module named 'scripts.core.edition_stats'`). Same pytest command as σ.1.1 Step 2.

- [ ] **Step 3: Implement `scripts/core/edition_stats.py`**

```python
"""σ.1 — build-accurate edition statistics.

resolved_note_counts() is THE source of truth for every "what you built"
surface (the Your-Edition page, the glossary, the live console). It reuses
build_one's exact filter sets (build_edition.compute_edition_filter_sets) so
the printed numbers always equal the real EPUB and honor the ρ.3 hierarchical
per-book/chapter/note choices."""

from __future__ import annotations

from functools import lru_cache

from scripts.core import config


def _edition_signature(edition_id: str) -> tuple:
    ed = config.editions_by_id().get(edition_id, {})
    # fields that change what ships — keep in sync with compute_edition_filter_sets inputs
    keys = (
        "canon", "enabled_categories", "enabled_kinds", "disabled_kinds",
        "note_families_on_per_book", "note_families_off_per_book",
        "note_families_on_per_chapter", "note_families_off_per_chapter",
        "disabled_note_ids", "enabled_note_ids",
        "traditions", "traditions_per_book", "time_period",
        "popup_languages_default", "popup_languages_per_book",
        "popup_languages_per_chapter", "popup_languages_per_verse",
    )
    return tuple((k, repr(ed.get(k))) for k in keys)


def resolved_note_counts(edition: dict) -> dict:
    """Return {total, per_book:{book:n}, per_category:{cat:n}, per_kind:{kind:n},
    popup_languages:[lang...]} for the notes that ACTUALLY ship in this edition."""
    return _resolved_note_counts_cached(edition["id"], _edition_signature(edition["id"]))


@lru_cache(maxsize=64)
def _resolved_note_counts_cached(edition_id: str, _sig: tuple) -> dict:
    from scripts.build_edition import compute_edition_filter_sets, _iter_note_ref_symbols
    from scripts.core import matrix as matrix_mod

    edition = config.editions_by_id()[edition_id]
    canon_books = matrix_mod.compute_matrix().edition_canon_books.get(edition_id, set())
    kinds_by_code = config.kinds_by_code()
    disabled_kinds, disabled_ref_ids = compute_edition_filter_sets(edition)

    per_book: dict[str, int] = {}
    per_category: dict[str, int] = {}
    per_kind: dict[str, int] = {}
    total = 0
    for ref_id, _note_id, book, _ch, _vs, _suffix, kind, category in _iter_note_ref_symbols():
        if book not in canon_books:
            continue
        if kind in disabled_kinds:
            continue
        if ref_id in disabled_ref_ids:
            continue
        total += 1
        per_book[book] = per_book.get(book, 0) + 1
        per_category[category] = per_category.get(category, 0) + 1
        per_kind[kind] = per_kind.get(kind, 0) + 1

    # popup languages that appear anywhere in this edition (default + any override)
    from scripts.build_edition import _resolve_popup_languages, decode_per_book_languages
    langs: set[str] = set(_resolve_popup_languages(edition, "\x00edition-default"))
    for bk in canon_books:
        langs |= set(_resolve_popup_languages(edition, bk))
    # (per-chapter/verse overrides only narrow within a book; union of book-level
    # + default is the truthful "languages used" set for the summary)

    return {
        "total": total,
        "per_book": per_book,
        "per_category": per_category,
        "per_kind": per_kind,
        "popup_languages": sorted(langs),
    }


def cache_clear() -> None:  # test hook
    _resolved_note_counts_cached.cache_clear()


resolved_note_counts.cache_clear = cache_clear  # type: ignore[attr-defined]
```

- [ ] **Step 4: Run the two tests — expect PASS.** (If `_iter_note_ref_symbols`'s tuple arity differs, adjust the unpack to match its actual yield — confirm by reading it.)

- [ ] **Step 5: Build-tally cross-check (the integrity pin).** Add a test that builds `catholic-study` to an EPUB and asserts the rendered note count equals `resolved_note_counts(ed)["total"]`. Reuse the build harness from `tests/test_covers.py::TestCoverReachesEpub` (it shows how to build to a temp dir + open the zip). Count surviving `note-ref` markers across the built XHTML and assert `== total`. Mark it `slow`.

```python
# tests/test_edition_stats.py (append)
import pytest
@pytest.mark.slow
def test_resolved_total_equals_built_epub_note_count(tmp_path):
    from scripts.core import config, edition_stats
    # build catholic-study to tmp (mirror tests/test_covers.py build harness),
    # then count note-ref markers in the built XHTML; assert == resolved total.
    ed = config.editions_by_id()["catholic-study"]
    expected = edition_stats.resolved_note_counts(ed)["total"]
    built_count = _build_and_count_note_refs("catholic-study", tmp_path)  # helper per test_covers pattern
    assert built_count == expected
```

- [ ] **Step 6: Commit + phase save**

```
pwsh -File save.ps1 -Message "σ.1.2: resolved_note_counts — build-accurate counts honoring the ρ.3 hierarchy (+cross-check vs built EPUB)"
```
Then full: `pwsh -File save-all.ps1 -Message "σ.1 close: build-accurate edition counter" -Label sigma1-counter`

---

## Phase σ.2 — Cover redesign (HOLY BIBLE + subtitle, overflow-proof)

**Files:**
- Modify: `scripts/generate_edition_covers.py`, `content/editions.yaml`
- Test: `tests/test_cover_fit.py` (new), extend `tests/test_cover_templates.py`

### Task σ.2.1: Add `cover_main_title` + `display_name` fields (back-compat)

- [ ] **Step 1: Failing test**

```python
# tests/test_cover_fit.py
from __future__ import annotations
def test_cover_text_for_edition_reads_fields():
    from scripts.generate_edition_covers import cover_text_for_edition
    main, subtitle = cover_text_for_edition("catholic-study")
    assert main == "HOLY BIBLE"            # default main title
    assert isinstance(subtitle, str)        # display_name (falls back to title)
```

- [ ] **Step 2: Run — expect FAIL** (`cannot import name 'cover_text_for_edition'`).

- [ ] **Step 3: Implement.** In `generate_edition_covers.py`, replace `title_for_edition` with:

```python
def cover_text_for_edition(edition_id: str) -> tuple[str, str]:
    """(main_title, subtitle). main_title defaults to 'HOLY BIBLE'; subtitle is
    the builder's display_name (falls back to the edition title; '' → no subtitle)."""
    ed = config.editions_by_id().get(edition_id, {})
    main = (ed.get("cover_main_title") or "HOLY BIBLE").strip()
    subtitle = ed.get("display_name")
    if subtitle is None:
        subtitle = ed.get("title", "")
    return main, subtitle.strip()
```

Delete the hardcoded `EDITIONS` title strings (keep the stem→edition mapping only if still needed for batch regen; otherwise read `cover_template` from editions.yaml).

- [ ] **Step 4: Run — expect PASS. Commit.**
```
pwsh -File save.ps1 -Message "σ.2.1: cover_text_for_edition reads cover_main_title + display_name (HOLY BIBLE default)"
```

### Task σ.2.2: Overflow-proof fitter (wrap, then shrink, guaranteed fit)

- [ ] **Step 1: Failing test**

```python
# tests/test_cover_fit.py (append)
def test_long_title_never_overflows():
    from scripts.generate_edition_covers import fit_text_block, TITLE_MAX_WIDTH
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (1024, 1536)); draw = ImageDraw.Draw(img)
    long = "The Extraordinarily Long Ethiopian Tewahedo Commemorative Study Bible Personal Heirloom Edition"
    lines, font = fit_text_block(draw, long, TITLE_MAX_WIDTH, max_pt=72, min_pt=20)
    for line in lines:
        w = draw.textbbox((0, 0), line, font=font)[2]
        assert w <= TITLE_MAX_WIDTH, f"line overflows: {line!r} ({w}px > {TITLE_MAX_WIDTH})"
```

- [ ] **Step 2: Run — expect FAIL** (`cannot import name 'fit_text_block'`).

- [ ] **Step 3: Implement `fit_text_block`** (wrap-then-shrink): for each font size from max→min, greedily word-wrap into lines that each fit `max_width`; if every line fits, return `(lines, font)`; if even at `min_pt` a single word is too wide, hard-break that word so it still fits. Use it for BOTH the main title and (smaller pt range) the subtitle in `_compose_cover`. Refactor `_compose_cover(main_title, subtitle)` to draw the wrapped main block centered, a short rule, then the wrapped subtitle beneath, all within the safe band.

- [ ] **Step 4: Run — expect PASS.**

- [ ] **Step 5: Regenerate the 9 editions' covers + the determinism check.** Run the cover generator for all standard editions; visually spot-check one (the cover JPG under `content/covers/`); run `tests/test_cover_templates.py` (still green). Commit.
```
pwsh -File save.ps1 -Message "σ.2.2: overflow-proof wrap-then-shrink fitter; HOLY BIBLE + subtitle composition; regen covers"
```

### Task σ.2.3: editions.yaml fields + clean default display_names

- [ ] Set `cover_main_title: "HOLY BIBLE"` implicitly (default — no edit needed) and add a clean `display_name` to each of the 9 editions (short, e.g. `"Ethiopian Tewahedo Bible"`, `"Catholic Edition"`) via `_patch_yaml_entry` or hand-edit preserving comments. Run `tests/test_validate_schemas.py`. **Phase save:** `pwsh -File save-all.ps1 -Message "σ.2 close: HOLY BIBLE cover + overflow-proof fitter + display names" -Label sigma2-cover`

---

## Phase σ.3 — Front matter ("Your Edition" page + reorder + glossary→counter)

**Files:** Modify `scripts/matter_pages.py`, `scripts/build_edition.py`. Test: `tests/test_matter_pages_your_edition.py` (new), extend `tests/test_presentation_polish.py`.

### Task σ.3.1: Glossary uses the build-accurate counter

- [ ] **Step 1: Failing test** — a force-on note in an otherwise-off family makes its category's symbol appear in the legend; a family off across all books drops it.

```python
# tests/test_matter_pages_your_edition.py
def test_legend_reflects_resolved_counts(tmp_path):
    # off xref edition-wide but force-on one xref note → legend still lists xref.
    # (isolate editions.yaml per _IsolatedEdition; assert via _legend_categories_for_edition)
    ...
```

- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Repoint `_legend_categories_for_edition`** from `matrix.breakdown_by_category(edition_id)` to `edition_stats.resolved_note_counts(edition)["per_category"]`. Keep the rest (sort_order, count>0 filter, `id="legend-<cat>"` anchors).
- [ ] **Step 4: Run — PASS. Commit.**

### Task σ.3.2: "Your Edition" page (from render_about_page)

- [ ] **Step 1: Failing test** — `render_your_edition_page(edition, stats, version)` returns XHTML containing the display_name heading, the description (notes) when set, a "What's inside" line, the total, and a per-book table; counts come from `resolved_note_counts`.
- [ ] **Step 2: Run — FAIL.**
- [ ] **Step 3: Implement** `render_your_edition_page` (rework `render_about_page`): heading = `edition.get("display_name") or edition.get("title")`; italic blockquote of `description` if non-empty; "What's inside" = canon name + book count + the note families present (`per_category` keys → category labels) + popup languages (`stats["popup_languages"]` → labels) + theme; **Total** = `stats["total"]`; a per-book `<table>` in canonical book order from `stats["per_book"]`. Add `inject_your_edition_page` writing `your-edition.xhtml` + OPF manifest/spine entry **right after titlepage, before copyright** + nav TOC entry. Keep the separate legend page.
- [ ] **Step 4: Run — PASS.**
- [ ] **Step 5: Reorder front matter** in `build_edition.py`: inject order becomes titlepage → your-edition → copyright → legend → (dedication if any) → scripture. Remove the old About injection (its content now lives in Your-Edition). Update `tests/test_presentation_polish.py` colophon/identity expectations.
- [ ] **Step 6: epubcheck + nested-anchors.** Build flagship `catholic-study`; run `epubcheck` (0/0/0/0 — see `reference_epubcheck`), `py -3 scripts/check_nested_anchors.py` + `pytest tests/test_nested_anchors.py`. Commit + **phase save** `-Label sigma3-frontmatter`.

---

## Phase σ.4 — `/customize` edition-identity control

**Files:** Modify `scripts/api/editions.py`, `scripts/api/covers.py`, `scripts/templates/customize.py`. Test: extend `tests/test_cover_templates.py` / add `tests/test_edition_identity_api.py`.

- [ ] **Task σ.4.1:** Add `display_name` + `cover_main_title` to `EDITABLE_TEXT` in `api_save_edition_meta`, to `api_customize_data`'s returned record, and to clone-carry. TDD a round-trip test (isolate editions.yaml). Commit.
- [ ] **Task σ.4.2:** In `customize.py`, add a "Your edition's name & notes" card: a `<select id="display-name-pick">` of suggestions computed in JS from the customize data (canon + whether note families/popups are enabled → e.g. "<canon> Bible", "<canon> Study Bible" only when study families are on, "Holy Bible" = empty subtitle) + a "✏ Custom…" option revealing a text input; a `<textarea>` bound to `description`. Wire both into `buildCustomizePayload` (they're `input,select` per RULES §6.4) → `saveEdition` (POST `/api/edition-meta/<id>`). On save, call the existing cover re-compose path. Add a console test asserting the controls render + the fields post. Commit.
- [ ] **Task σ.4.3:** Extend `api_apply_cover_template` (`scripts/api/covers.py`) to compose using `cover_text_for_edition(edition_id)` (main + subtitle) instead of the old single title. TDD compose-uses-new-fields. Commit.
- [ ] **Task σ.4.4 (vertical-overflow guard — from the σ.2 code review):** σ.2's `fit_text_block` guarantees HORIZONTAL fit only; `_compose_cover` centers the main+rule+subtitle stack about `TITLE_CENTER_Y` with no vertical bound, so a pathological long `cover_main_title`/`display_name` (now enterable via this console) could push text off the top/bottom (Pillow silently clips). Two-part fix, both here since σ.4 introduces the input: (a) **cap the inputs** — add a `maxlength` to the name `<select>`/custom-input + the `cover_main_title` field (e.g. 48 chars) so pathological lengths can't reach the compositor; (b) **clamp in the compositor** — in `_compose_cover`, clamp the block's `top_y` to a top-safe margin and, if the combined main+subtitle height exceeds the vertical safe band, shrink the subtitle's `max_pt`/`min_pt` (re-fit) until it fits; update `fit_text_block`/`_compose_cover` docstrings + the `test_compose_cover_long_subtitle_never_overflows` test to assert the text block's pixel bounds stay within the safe band (not just `img.size`). TDD with a pathological-length input. Commit + **phase save** `-Label sigma4-identity`.

---

## Phase σ.5 — Ge'ez / Amharic default covers

**Files:** Modify `content/editions.yaml`, `scripts/build_standalone.py`, `scripts/generate_edition_covers.py` (font fallback). Test: extend `tests/test_covers.py`.

- [ ] **Task σ.5.1:** Ethiopic-capable cover font. Verify `FONT_TITLE_PATH` (Times bold) renders Ethiopic; if not, add an Ethiopic font fallback used when the title/subtitle contains Ethiopic codepoints (reuse a font the project already ships for manuscript/standalone rendering — search the standalone/manuscript code for the font path). TDD: composing a cover with an Ethiopic main title produces a non-blank glyph region (assert the title bbox is drawn / pixels differ from background).
- [ ] **Task σ.5.2:** In `editions.yaml` set for `standalone-geez`: `cover_template: "05_missal_central_red"`, `cover_main_title: "መጽሐፍ ፡ ቅዱስ"`, `display_name: "Ge'ez Tewahedo Bible"`; for `standalone-amharic`: `cover_template: "01_ornate_leafy_brown"`, `cover_main_title: "መጽሐፍ ቅዱስ"`, `display_name: "Amharic Tewahedo Bible"`. Compose both covers (`generate_edition_covers._generate_one`) so `cover_image` points at the generated files.
- [ ] **Task σ.5.3:** In `build_standalone.build_standalone`, ensure the composed cover is applied (today `apply_edition_cover` no-ops on `cover_image=""`; now they have a real `cover_image`). Build a standalone EPUB; `epubcheck` 0/0/0/0; visually confirm the Ethiopic cover. TDD: the standalone build's `cover.jpeg` matches the composed file (mirror `TestCoverReachesEpub`). Commit + **phase save** `-Label sigma5-geez-amharic-covers`.

---

## Phase σ.6 — Live-console reconcile + wipe stale framing

**Files:** Modify `scripts/core/matrix.py` (docstring), `scripts/web_editions.py` / `scripts/templates/build_tracker.py`. Test: extend the build-tracker tests.

- [ ] **Task σ.6.1:** Route the `/build-tracker` total/per-book/per-category counts through `edition_stats.resolved_note_counts` so the live preview matches the built book (today it uses the edition-wide matrix). Keep the per-book × per-chapter grid; where a per-chapter resolved count is needed, use `enabled_kind_codes_for(edition, all_kinds, book, ch)`. TDD: an override edition's `/build-tracker` total equals `resolved_note_counts` total. (`/build-my-bible` already resolves per-coordinate — add an assertion that its resolved counts agree.)
- [ ] **Task σ.6.2 (copyright-page counts — from the σ.3 code review):** `inject_copyright_page` (`scripts/matter_pages.py`) still prints "N annotations across M categories" from the edition-wide matrix (`total_for_edition` + the mint-9 #8 `annotation_count_override` build_one computes at `build_edition.py` ~:3527-3530, and `breakdown_by_category` for the category count). Post-σ.3 the adjacent glossary + the Your-Edition page use `resolved_note_counts`, so an override-edition that zeroes a category shows e.g. "5 categories" on copyright but 4 symbols on the legend, and the annotation total overstates the real EPUB by the base-coverage residual. **Route both through `resolved_note_counts`**: `annotation_count = stats["total"]`, `category_count = len([n for n in stats["per_category"].values() if n > 0])`; **remove the now-redundant `annotation_count_override` param + build_one's `_annot_override`/`_count_in_scope_disabled_ref_ids` override block** (resolved_note_counts subsumes it + is strictly more accurate — "wipe outdated stuff"). TDD: copyright count == legend count == Your-Edition total == resolved total. This changes the printed count for all editions (intentional truthfulness fix) → re-run epubcheck flagship + the determinism gate.
- [ ] **Task σ.6.3:** Fix `note_counts_for_edition`'s docstring in `matrix.py` (it is edition-wide *potential*, not "actually-shipping") and audit other call sites of the edition-wide counts that imply "shipping"; repoint user-facing ones to `resolved_note_counts`, leave `potential_for_kind` (legitimately "potential"). `py -3 scripts/lint_rules.py` clean. Commit + **final 5-leg save** `-Label sigma-complete` + update truth records (SESSION_STATE/IN_FLIGHT/CHANGELOG) + INDEX (mark this plan SHIPPED).

---

## Self-review notes

- **Spec coverage:** §3.1 cover → σ.2; §3.2 identity → σ.4; §3.3 Your-Edition + de-dup → σ.3; §3.4 build-accurate counter → σ.1 (+consumed by σ.3/σ.6); §3.5 Ge'ez/Amharic → σ.5; live-console + wipe-stale → σ.6. All covered.
- **Type consistency:** `resolved_note_counts(edition) -> {total, per_book, per_category, per_kind, popup_languages}` used identically in σ.3/σ.6; `cover_text_for_edition(id) -> (main, subtitle)` used in σ.2/σ.4; `compute_edition_filter_sets(edition) -> (set, set)` defined σ.1.1, used σ.1.2.
- **Ground-truth pin:** σ.1.2 Step 5 (build tally == resolved total) is the integrity guard the whole feature rests on — do not skip it.
- **Byte-stability:** σ.1 is a pure refactor (gate green). σ.2/σ.3 intentionally change cover + matter output for all editions — re-verify determinism + re-pin baselines; this is intended, not a regression.
- **Marathon core untouched:** σ never edits `content/manuscript/**` or the transcription pipeline — file-disjoint from the Windows content lane.
