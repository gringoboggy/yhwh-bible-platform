# Edition Cover + Truthful Front Matter — Design Spec

**Status:** APPROVED 2026-06-04 — brainstormed with the user (visual companion). Builder-named, "Holy Bible" cover; a "Your Edition" front page; build-accurate counts + glossary that honor the new hierarchical-customize choices; Ge'ez/Amharic default covers. Next: writing-plans → implementation.

**Phase tag:** σ (new — cover/front-matter identity arc).

---

## 1. Goal — the vision

A builder's edition should present itself **honestly and beautifully**:

- The **front cover** says **"HOLY BIBLE"** (clean, always fits) with a small optional subtitle = the name the builder chose for their version. No more long edition names spilling past the artwork border (the reported bug).
- The **first page inside** ("Your Edition") tells you exactly what this copy *is*: the builder's chosen name, their own notes, and an auto-generated, **always-truthful** summary of what they actually built — total notes, per-book counts, the note families included, and the popup languages.
- The **symbol glossary** lists only the symbols actually used — and, like the counts, it must reflect the builder's **new per-book / per-chapter / per-note choices**, not a stale edition-wide approximation.
- The two **standalone Bibles** (Ge'ez, Amharic) get sensible default covers, builder-overridable like every other edition.

North-star tie-in (RULES §1): this is the "wow, that's mine" moment — the builder opens their EPUB and the cover + first page say *this is the Bible I made*, accurately.

---

## 2. Scope reality (verified by the codebase map, 2026-06-04)

Current state (file:line anchors):

- **Cover composition** is programmatic (Pillow) in `scripts/generate_edition_covers.py`: `_compose_cover(template_stem, title)` (:139) draws the title via `ImageDraw.multiline_text` onto a 1024×1536 frame; `_fit_title_font` (:129-136) steps 72→28pt and **returns 28pt without re-checking fit** → long titles overrun the `TITLE_MARGIN_X=150px` safe zone. **This is the overflow bug.**
- **Cover title text** is a hardcoded multi-line string per edition in the `EDITIONS` list (`generate_edition_covers.py:52-62`); `title_for_edition()` (:65) falls back to `edition["title"]` for editions not in that list (the two standalone Bibles).
- **25 cover templates** live in `content/covers/templates/` = 5 families × 5 colors; registry `COVER_TEMPLATES` / `COVER_TEMPLATE_FAMILIES` in `scripts/core/covers.py:80-90`. Ethiopian-flavored: `05_missal_central` (Coptic/Ethiopian liturgical), `01_ornate_leafy` (heirloom).
- **Per-edition cover selection** already exists: `cover_template` field + the `/customize` picker → `api_apply_cover_template()` (`scripts/api/covers.py:72`) → composes + writes `content/covers/<id>.jpg` + saves `cover_image`+`cover_template`. Validated against `COVER_TEMPLATES` in `api_save_edition_meta` (`scripts/api/editions.py:752-758`). Build swaps the cover via `apply_edition_cover()` (`scripts/build_edition.py:2989`, called :3281); **no-op when `cover_image=""`** (the byte-stability path).
- **Front-matter pages** (`scripts/matter_pages.py`, injected at `build_edition.py:3461-3465`): `copyright.xhtml`, optional `dedication.xhtml`, `legend.xhtml` (the glossary, `render_symbol_legend_page` :267 / `_legend_categories_for_edition` :245), `about.xhtml` (`render_about_page` :411). The **titlepage.xhtml** is a static full-bleed cover image.
- **The glossary already filters to used categories**: `_legend_categories_for_edition` keeps categories with `count > 0` from `matrix.breakdown_by_category(edition_id)` (matter_pages.py:252).
- **The About page already auto-summarizes**: canon, annotation count across N categories, each category + count, witnesses, theme, and `edition["description"]` (currently empty for all editions). `render_about_page` (matter_pages.py:411-489).
- **★The counts are NOT hierarchy-aware.** `matrix.breakdown_by_category` → `note_counts_for_edition` → `compute_matrix().enabled` → built from edition-wide `enabled_kind_codes` (`matrix.py:270`). It does **not** consult `note_families_{on,off}_per_{book,chapter}`, `disabled_note_ids`, or `enabled_note_ids` (the Phase-A/B/C hierarchical fields). So the glossary + every count is correct **only** for editions with no overrides; the moment a builder uses the new per-book/chapter/note controls, the front matter **lies about the actual book**. `note_counts_for_edition`'s docstring ("actually-shipping notes") is now inaccurate.
- **The standalone Ge'ez/Amharic editions** (`standalone-geez`, `standalone-amharic` in `content/editions.yaml`) set `cover_image:""`, no `cover_template` → get the base master cover with **no composed title**. Built via `build_standalone.build_standalone()` (cover no-op at `build_standalone.py:276`).
- **The live `/build-my-bible` navigator** (shipped ρ.3 C2, 2026-06-04) already resolves symbol/popup state **per coordinate** via `config.enabled_kind_codes_for` + `_resolve_popup_languages` — it is the hierarchy-aware surface. The older `/build-tracker` console is matrix-based (edition-wide, stale for overridden editions).

---

## 3. The design

### 3.1 Cover — "HOLY BIBLE" + builder subtitle, overflow-proof

- The composed cover shows a **main title** (default `"HOLY BIBLE"`) and an optional **subtitle** = the edition's display name. If the subtitle is empty, the cover shows only the main title.
- **New/changed edition fields** (`content/editions.yaml`, all default-back-compat):
  - `cover_main_title` (string, default `"HOLY BIBLE"`) — the big cover word(s). The standalone Ge'ez/Amharic editions set their script forms (e.g. Ge'ez `መጽሐፍ ፡ ቅዱስ`, Amharic `መጽሐፍ ቅዱስ`). Honors RULES §2 "everything customizable."
  - `display_name` (string, default = `edition["title"]`) — the cover **subtitle** and the "Your Edition" page heading; the builder's chosen name. Set via the `/customize` name control (§3.2). Empty string ⇒ no subtitle on the cover.
- `generate_edition_covers.py` is refactored: drop the hardcoded `EDITIONS` title strings; `_compose_cover` takes `(main_title, subtitle)` and draws the main title large + the subtitle small beneath a rule. `title_for_edition()` becomes `cover_text_for_edition(edition_id)` returning `(cover_main_title, display_name)` read from the edition record.
- **Overflow-proof fitter:** `_fit_title_font` (and a new subtitle fitter) must guarantee fit — first shrink, then **word-wrap** to multiple lines if still too wide at the minimum size, so no text can ever exceed `TITLE_MAX_WIDTH` / the vertical safe band. A test feeds a deliberately long string and asserts the rendered text block stays within the safe box.

### 3.2 Edition identity control — on `/customize`

- A **name** control (the cover subtitle + "Your Edition" title): a `<select>` of **smart suggestions derived from what was actually built** (e.g. with study notes present → "… Study Bible"; plain → "… Reading Bible"; plus "Holy Bible" = blank subtitle), ending in **"Custom…"** → a free-text input. Default selection = the smart suggestion (which seeds `display_name`). Suggestions are computed UI-side from the edition's resolved content; the stored value is just `display_name`.
- A **notes** textarea → the existing `description` field (already editable + persisted; just surface it clearly here).
- Both `display_name` and `cover_main_title` join the `EDITABLE_TEXT` set in `api_save_edition_meta` (`scripts/api/editions.py`), clone-carry, and `api_customize_data`. Participate in the dirty-check (RULES §6.4). Changing the name re-composes the cover (existing `api_apply_cover_template` path, extended to read the new fields).

### 3.3 "Your Edition" front page + de-dup (consolidation)

- Rename/rework the existing **"About this Edition"** page into **"Your Edition,"** and move it to **immediately after the cover** (before copyright). It contains:
  1. The **display name** (large heading; falls back to `title` if unset).
  2. The builder's **notes** (`description`), shown as an italic blockquote.
  3. **"What's inside"** — auto: canon name + book count; the note **families included** with their counts; the **popup languages**; the theme. All from the build-accurate counter (§3.4).
  4. **Total notes** + a compact **per-book counts** table (canonical order).
- The **Glossary** ("A Guide to the Notes") **stays its own short page** (its per-category `id="legend-<cat>"` anchors are link targets for in-note symbols, and it's the quick symbol reference). **No triplication:** "Your Edition" *names* families + counts; the Glossary *defines* the symbols.
- **Per-chapter** counts are **not printed** (thousands of rows). They stay live in the builder console (`/build-my-bible` + `/build-tracker`), which already show the per-book × per-chapter grid. (User-approved.)

### 3.4 ★Build-accurate counts + glossary (the correctness fix — "wipe outdated stuff")

The single most important piece. Counts and the glossary must reflect the builder's **actual** choices, including the hierarchical overrides.

- **New single source of truth:** `resolved_note_counts(edition) -> {total, per_book: {book: n}, per_category: {cat: n}, per_kind: {kind: n}, popup_languages: [lang…]}` (home: `scripts/core/edition_stats.py`, or alongside the resolvers). It applies the **full** resolution the build uses: canon filter + `enabled_kind_codes_for(edition, all_kinds, book, chapter)` per coordinate + `disabled_note_ids` (force-off) + `enabled_note_ids` (force-on). Cached on an edition signature; uses `enabled_kind_codes_for`'s fast path so no-override editions stay cheap.
- **Ground-truth cross-check:** the build (`build_one`) already resolves + strips exactly the shipping notes. Tally the kept notes during the build and pin, in a test, that the build tally **equals** `resolved_note_counts(edition)` for representative editions (no-override + an override fixture). This guarantees the printed pages match the real EPUB.
- **The built pages consume `resolved_note_counts`:** the Glossary (`_legend_categories_for_edition`) and "Your Edition" switch from `matrix.breakdown_by_category` to `resolved_note_counts`. The glossary then shows a symbol iff its category has ≥1 note **after** hierarchical resolution (a force-on note in an otherwise-off family makes its symbol appear; a family turned off across all books drops its symbol).
- **The live preview uses the same resolution:** `/build-my-bible` is already per-coordinate. Reconcile `/build-tracker`: either route its counts through `resolved_note_counts` (preferred — one counter) or clearly relabel its grid as the edition-wide *potential*. "What you built" surfaces must not use the edition-wide-only path.
- **Wipe the stale framing:** fix `note_counts_for_edition`'s "actually-shipping" docstring (it's edition-wide potential, pre-hierarchy); audit other consumers of the edition-wide counts that imply "actually shipping" and repoint them to `resolved_note_counts` or correct the wording. Keep the matrix's edition-wide projection only where it legitimately means "potential if a kind were toggled" (e.g. `potential_for_kind`).

### 3.5 Ge'ez / Amharic default covers

- Assign defaults (builder-overridable via the existing `/customize` picker):
  - `standalone-geez` → `cover_template: 05_missal_central_red`, `cover_main_title: "መጽሐፍ ፡ ቅዱስ"`, `display_name` = "Ge'ez Tewahedo Bible".
  - `standalone-amharic` → `cover_template: 01_ornate_leafy_brown`, `cover_main_title: "መጽሐፍ ቅዱስ"`, `display_name` = "Amharic Tewahedo Bible".
- Compose their covers once (`generate_edition_covers._generate_one`) so `cover_image` points at the generated file, and ensure the standalone build path composites the cover (today `apply_edition_cover` is a no-op for them because `cover_image=""`). Confirm the Ethiopic glyphs render (the cover font must cover Ethiopic; if `timesbd.ttf` lacks Ge'ez, fall back to an Ethiopic-capable font already used by the project for manuscript/standalone rendering).

---

## 4. Storage schema (back-compat; byte-identical when unset on existing editions' rendered text)

New `editions.yaml` fields:
```yaml
cover_main_title: "HOLY BIBLE"   # default; standalone editions set Ethiopic script
display_name: ""                  # default → falls back to `title`; the builder's chosen name
# description: existing — the builder's notes (already editable + rendered)
# cover_template: existing — set defaults for the two standalone editions
```
Adding a field is a no-op when unset (RULES §7.2). For the 9 existing editions, `display_name` defaults to `title` and `cover_main_title` to "HOLY BIBLE" — but note §6: the cover + front matter are **deliberately** redesigned, so their rendered output changes for all editions on purpose (re-pin, not a regression).

---

## 5. Front-matter page flow

```
BEFORE:  Cover → Copyright → Legend(glossary) → About(details) → [scripture]
AFTER:   Cover → Your Edition(name · notes · what's-inside · total + per-book) → Glossary(only-used, hierarchy-accurate) → Copyright → [scripture]
```
Order rationale: identity + truthful summary first (the "wow, that's mine" page), the symbol reference next (link target for in-note symbols), copyright after. The closing colophon (back matter) is unchanged except it reads `display_name`/`title` consistently.

---

## 6. Byte-stability & integrity obligations

- This **deliberately** changes the cover image + front-matter XHTML for **all** editions (new cover text, new "Your Edition" page, reordered front matter). That is the intent — it is **not** the latent-field invariant. After implementation: re-verify the **determinism** gate (build twice → byte-identical), regenerate covers, run `epubcheck 0/0/0/0` on flagship + a standalone, run `test_nested_anchors` + `check_nested_anchors`, and **re-pin** any digest baselines the change moves.
- `apply_edition_cover` must still no-op when `cover_image=""` is intentionally kept (preserve `TestApplyEditionCover`), except where we now intentionally give the standalone editions a real cover.
- The build-accurate counter must equal the build's actual kept-note tally (the §3.4 cross-check test) — this is the core integrity pin.
- Ge'ez/Amharic Ethiopic glyphs must render in the cover (visual + epubcheck).

---

## 7. Testing

- **Cover fitter:** a long title + a long subtitle render fully within the safe box (no overflow); short text centers correctly; deterministic output.
- **Cover text source:** `cover_main_title` + `display_name` drive the composed cover; empty `display_name` → no subtitle.
- **Identity fields:** round-trip through `api_save_edition_meta`; surfaced in `api_customize_data`; clone-carry.
- **Build-accurate counts (the crux):** `resolved_note_counts` honors per-book/chapter on-off, force-on, force-off, canon; equals the build's kept-note tally for a no-override edition AND an override fixture; the glossary shows/hides a symbol per resolution (force-on surfaces a symbol; all-off hides it).
- **Your Edition page:** renders the name, notes, what's-inside, total + per-book; truthful against the build.
- **Glossary:** only categories with resolved count > 0; anchors preserved; in-note symbol links still resolve.
- **Standalone covers:** Ge'ez/Amharic get their composed covers + Ethiopic title; epubcheck clean.
- **Determinism gate** green; flagship + a standalone epubcheck 0/0/0/0.

---

## 8. Phasing (each shippable; TDD; 5-leg save; marathon core untouched)

- **σ.1 — Build-accurate counter (headless).** `resolved_note_counts` + the build-tally cross-check test. No page change yet. (Foundational; everything truthful depends on it.)
- **σ.2 — Cover redesign.** `cover_main_title` + `display_name` fields; refactor `generate_edition_covers` to main+subtitle; overflow-proof fitter; recompose the 9 editions' covers. Determinism re-pin.
- **σ.3 — Front matter.** "Your Edition" page (consumes σ.1) + reorder; switch the Glossary to σ.1; de-dup About. epubcheck + nested-anchors.
- **σ.4 — `/customize` identity control.** Name smart-dropdown + Custom + notes; wire to the new fields; re-compose-on-change.
- **σ.5 — Ge'ez/Amharic default covers.** Assign templates + Ethiopic titles; composite in the standalone build; epubcheck a standalone.
- **σ.6 — Live-console reconcile.** Route `/build-tracker` counts through σ.1 (or relabel as potential); confirm `/build-my-bible` agreement. Wipe the stale "actually-shipping" framing.

---

## 9. Non-goals (YAGNI)

- No per-chapter counts in the printed book (live console only — user-approved).
- No new cover-template artwork (use the existing 25).
- No change to how notes/popups are *resolved* by the build (σ reads the same resolvers; the engines shipped in ρ.3).
- No commercial/identity metadata (free-public pivot stands).

---

## 10. File-change map

- `scripts/generate_edition_covers.py` — main+subtitle composition; overflow-proof fitter; read fields not hardcoded list.
- `scripts/core/edition_stats.py` (new) — `resolved_note_counts`.
- `scripts/matter_pages.py` — "Your Edition" page (from `render_about_page`); Glossary → `resolved_note_counts`; reorder injection.
- `scripts/build_edition.py` — front-matter order; build-tally cross-check hook; read new fields.
- `scripts/build_standalone.py` — composite the standalone covers.
- `scripts/api/editions.py` — `display_name` + `cover_main_title` in EDITABLE / customize data / clone.
- `scripts/api/covers.py` — `api_apply_cover_template` reads new fields.
- `scripts/templates/customize.py` — the name smart-dropdown + Custom + notes control.
- `scripts/core/matrix.py` — fix the "actually-shipping" docstring; keep edition-wide projection only for "potential."
- `scripts/templates/build_tracker.py` / `web_editions.py` — reconcile live counts (σ.6).
- `content/editions.yaml` — new fields + standalone cover defaults.
- `content/covers/<edition>.jpg` — regenerated covers.
- `tests/` — per §7.
