# EPUB Presentation Polish — Configurable Reader Styling

**Date:** 2026-05-24
**Status:** Approved design (brainstorming complete; ready for implementation plan)
**Companion specs:** `2026-05-22-fully-customizable-builder-roadmap.md` (this is the Phase 3/4 "presentation" slice), `2026-05-22-themes-and-multitranslation-popups-design.md`, `2026-05-22-verse-popup-regeneration-design.md`.

---

## 1. Motivation

A real-reader review of the flagship `ethiopian-tewahedo` EPUB in **Apple Books** (screenshots in `apple_books_screenshots/`) surfaced presentation problems that a browser does not expose:

- **Inline markers** are visual clutter: colored "pill" backgrounds placed mid-sentence, several rendering as empty boxes (tofu) when the reader's font lacks the glyph, breaking the reading line.
- **Verse popups** repeat the **English (KJV)** — which also *differs* from the WEB reading text (a confusing mismatch) — and show only Hebrew + Greek.
- **Book title pages** are bare text boxes: the 66 per-book images in `content/covers/_book_defaults/` exist but are not displayed there.
- **Front matter** is ~6 pages carrying `TODO_` placeholders (from the dead `onix.py` defaults), a hardcoded **stale** "1,371 annotations across 14 categories", and stretched **justified** spacing ("Edition   ID:   …").
- **Note popups** show a stray leading `‖` glyph and a single dense block.
- **Cover** does not fit the reader frame.

## 2. Guiding principle

RULES §2 — **"Fully customizable. … assume the user will want to change it. Defaults exist; nothing is hard-coded."** Therefore the presentation decisions become **per-edition configurable settings with sensible defaults**, wired through the established `editions.yaml` → `/customize` → build-pipeline pattern (RULES §9 "Add a new edition feature"). The user's chosen styles are the defaults; alternatives are selectable.

## 3. Goals / Non-goals

**Goals**
- Pleasing, readable output in real readers (Apple Books now; e-ink later).
- Presentation choices as configurable builder settings (defaults = the picks below).
- Fix the unambiguous bugs/placeholders.
- Apply across **all 11 editions** via the shared CSS + pipeline.

**Non-goals**
- Ge'ez/Amharic popups in the 9 non-standalone editions (reserved for the two standalone Bibles — `project_parallel_bible`).
- New translation ingestion beyond the existing 9-version registry (the Phase-E Latin appendix is tracked separately).
- Reference-work corpus expansion (capped 2026-05-24) / Voyage AI (de-scoped).

## 4. Configurable settings

Each is an `editions.yaml` field, back-compat (unset → default), surfaced in `/customize`, read in the build pipeline.

### 4.1 `marker_style` — inline note markers
- **Options:** `numbers` *(default — chosen 2026-05-24: inline, "safe always", renders on every device)* · `badge` *(offered, but DEFERRED — see below)*
- **`numbers`:** traditional **superscript footnote numbers** inline, one per note, opening individual asides. Always render (no tofu). This is the default and the only mode required for the immediate work.
- **`badge`:** scripture text carries **no** per-note inline markers. Each verse that has notes shows **one small verse-end badge** with the note count; tapping opens that verse's notes as a **list** (a per-verse note container, notes grouped by `(book, chapter, verse)`).
- **Both:** **no category symbols inline** — symbols move into the notes (see §4.4).
- **`badge` is DEFERRED.** It needs the per-verse note container whose exact base-HTML injection point is **not yet determined** (§10), and the user (2026-05-24) is likewise unsure of the best injection point. So `numbers` is the default and `badge` waits until that injection point is settled — implementing `numbers` first unblocks all the immediate presentation work. `scripts/inject.py` already emits per-note markers+asides today; `numbers` is a small change to that path (number glyph + drop inline category symbol); `badge` is the deeper two-mode rework, later.

### 4.2 `verse_popup_style` — original-language popup layout
- **Options:** `cards` *(default)* · `stack`
- **`cards`:** each witness in its own tinted card with a colored spine (e.g. gold = Hebrew, purple = Greek).
- **`stack`:** labeled stack with colored source labels + quiet dividers.
- Switched by a container class; same underlying data. CSS in the edition stylesheet; assembly in `scripts/generate_verse_popups.py::build_vnote_aside`.

### 4.3 Verse-popup **witnesses** (content) — existing `popup_languages_default` / `popup_languages_per_book`
- **Registry (9, in `scripts/core/popup_versions.py`):** `kjv`, `wlc` (Hebrew), `lxx-greek` (Swete), `greek-nt` (Byzantine), `brenton-en`, `douay`, `jps`, `vulgate` (Latin), `arabic`.
- **English base (`kjv`) removed** from popups — it duplicated/mismatched the WEB reading text.
- **Default witness set:** `wlc` + `lxx-greek` + `greek-nt` + `vulgate` + `arabic` (Hebrew, Greek LXX/NT, Latin, Arabic).
- **`jps`, `douay`, `brenton-en`:** available, **off by default**, selectable per edition/book.
- Popups render **only witnesses that exist** for a given verse (OT vs NT vs canon coverage).
- Already per-edition + per-book configurable; this change widens the default set and drops `kjv`.

### 4.4 `note_popup_style` — note/aside popup layout
- **Options:** `chip` *(default)* · `pills`
- **`chip`:** the note's **category symbol** + a **label chip** (e.g. `◇ PARALLEL`) → explanation body → cross-references as tidy links.
- **`pills`:** category label → cross-references as tappable pills → explanation.
- **Both:** the **category symbol renders inside the note** (its new home), and the stray `‖` is removed (it was the parallel-kind glyph leaking as a stray back-link).
- `scripts/inject.py::build_aside` + CSS.

### 4.5 `title_page_style` — book title pages
- **Options:** `full-bleed` *(default)* · `framed`
- **`full-bleed`:** the per-book image (`content/covers/_book_defaults/<book>.jpg`) as a full-page background with a dark scrim + the title overlaid for legibility.
- **`framed`:** the image as a framed plate/frontispiece above the title text on cream.
- Applies to all 66 books with art; books lacking art fall back to the current text-only title page.
- **Builder-uploadable per-book art (added 2026-05-24, user request):** the title-page image for any book in any of the 11 editions is **builder-overridable** — the publisher can drag in their own picture (size/format/dimension-validated) into the per-book art slot, and it replaces the default **while the title text stays exactly the same**. Resolution order: the edition's per-book uploaded override → `content/covers/_book_defaults/<book>.jpg` (default) → text-only title page (no art). This **reuses the existing cover infrastructure** — `book_covers` (per-edition × per-book) in `editions.yaml`, the `/covers` console, `scripts/core/covers.py` (magic-byte format validation + `cover_record_for_edition` resolver), and the π.4-B validated-binary-upload + RULES §9 "Add an uploadable binary asset" pattern (size cap, format-from-bytes, dimension/aspect checks, transactional write, sandboxed serve). The only genuinely new work is (a) **wiring the resolved per-book art into the EPUB title page at build time** and (b) a per-book drag-drop upload affordance in the `/covers` (or title-page) console if one isn't already present.
- Wiring: a new build-time `apply_title_pages(tmp, edition)` in `scripts/build_edition.py::build_one` (NOT `scripts/customize.py` — its `.html.frag` staging is orphaned, §12.5) that resolves each book's art via `covers.cover_record_for_edition` (override→default→none) + transforms the `book-title-frame` div to the chosen style **without altering the title text** + a `patch_opf_book_images` (modeled on `patch_opf_fonts`) to register the images in the OPF manifest; plus CSS.
- **Accessibility (user-approved 2026-05-24):** every per-book title image (default OR uploaded) must carry descriptive `alt` text (e.g. "Illustration — the Book of Genesis"); the master cover already has `alt`. The existing `check_a11y` preflight validates image alt-text + EPUB accessibility metadata, so the new images must not regress it — `apply_title_pages` sets `alt` on each injected `<img>`, and uploaded-art alt defaults to the book name.

### 4.6 Main cover selection (related — recommended Phase 2, pending user confirmation)
The 25-template main-cover library — **5 design families × 5 colours** (`01_ornate_leafy` · `02_classical_corner` · `03_beadline` · `04_minimal_lines` · `05_missal_central`) × (`black` · `brown` · `forest` · `navy` · `red`) — lives in `content/covers/templates/` and is **intact**. Today `scripts/generate_edition_covers.py` maps each edition to ONE template (editorial mapping) and bakes `content/covers/<edition-id>.jpg`; the builder can override via the `cover_image` path field (`api_save_edition_meta`), but the 25 options are **not exposed as a clickable picker** in `/wizard` or `/customize` (the library is referenced ONLY by the generator script — grep-confirmed 2026-05-24). Per RULES §2 (fully customizable), a builder-facing **cover-design + colour picker** (choose one of the 25 OR upload your own, reusing the §4.5 / π.4-B validated-upload pipeline) is a natural customization. **CONFIRMED in scope 2026-05-24 (user): the options are clickable.**

**Universal cover-title placement (user 2026-05-24, re `apple_books_screenshots/cover.png`):** because any edition can now pick any of the 5 designs, the title typography must sit in **one safe zone that works across ALL 5 designs** — clear of every design's ornament, especially the CENTRAL ornaments in `04_minimal_lines` and `05_missal_central` (the generator docstring already admits these clash with subtitle text). The current `scripts/generate_edition_covers.py` hardcodes `title_y=460` + manual bbox-centering (`x = center_x - line_w//2`, which ignores glyph side-bearing → slightly off-center). Fix = a title band validated visually against all 5 designs + proper centering via PIL `draw.text(..., anchor="ma")`/`"mm"`.

**Cover text = TITLE ONLY (user 2026-05-24):** drop the subtitle/short-title line AND the "Bible Builder" publisher mark from the generated cover — render ONLY the edition title (cleaner, and a single text block makes the cross-design universal placement far easier). The edition's descriptive specifics move OFF the cover onto the front-matter "About this Edition" page (§5.1). The title text itself is unchanged; only the subtitle + mark are removed and the title is repositioned/recentered.

## 5. Built-in (not toggles)

### 5.1 Front-matter consolidation
- Replace the ~6 placeholder pages with **2 pages**:
  1. **Title page** (clean).
  2. **Colophon:** "YHWH Ya' Way — <edition title> · Published by **YHWH Ya' Way Editions**, **2026** · © Bogdan Zorlescu" + canon summary + sources / PD bases + **real computed counts** (notes + categories for that edition).
- Remove **all** `TODO_` placeholders (sourced from `content/onix.py` defaults — a dead ONIX vestige).
- Replace the hardcoded **stale "1,371 / 14 categories"** with the edition's real computed counts.
- `scripts/build_edition.py::render_copyright_page` (+ `inject_copyright_page`).
- **Revised front-matter set (user 2026-05-24):** the cover carries the TITLE ONLY (§4.6); the edition's descriptive **specifics move OFF the colophon** onto a dedicated **"About this Edition"** front-matter page — **repurpose the placeholder `introduction.xhtml`** rather than dropping it. That page renders the edition's `description`; **make `description` builder-editable** in `/customize` (add to the `EDITABLE_TEXT` set + a `<textarea data-field="description">`) — **ONE optional spot** where the builder writes a brief paragraph on what they decided to do with this Bible, **or leaves it blank** (user 2026-05-24). When blank, the About page still renders its auto-generated specification; only the free-text paragraph is omitted. - **Optional dedication (user-approved 2026-05-24):** an optional builder-typed **Dedication** page right after the title page — a short free-text line/paragraph (a new editable `dedication` field in `/customize`; blank → omit the page), the conventional home for "For …". Same editable-field mechanism as `description`.
Front-matter order: **Title → Dedication (optional) → Colophon (counts/©/sources, NO long description) → A Guide to the Notes (§5.3) → About this Edition**.
- **Auto-generated specification (user 2026-05-24 — "generate the specs from what they pick"):** the "About this Edition" page is **generated at build time from the edition's RESOLVED choices** — canon + book count · the **verse-popup languages/witnesses** selected (`popup_languages_default` → witness labels via `popup_versions`) · the **note categories included + their counts** (the same edition-aware set as the Guide), rendered as a clear per-category list — `<Category label> — N notes` for every category present (e.g. "Commentary / Tradition — 2,690 notes · Apologetic — N notes · Topical — 26,335 notes"): this IS the "this edition has X study notes, Y apologetic notes…" display the user asked for (2026-05-24) · theme · total annotation count. So whatever the builder clicks in `/customize` is reflected on this page the moment they BUILD. **Strong reuse:** the `/build-tracker` console (RULES §1) ALREADY computes this "what's enabled in this edition" summary (canon coverage, per-kind/category breakdown, counts) — `render_about_page` formats that same composed data into a front-matter page. Sits alongside the optional builder-typed free-text `description`. Data sources (all already used by the build): `scripts.core.matrix`, `scripts.core.config`, `scripts.core.popup_versions`. **Fully doable — no new data, just formatting what the pipeline already resolves.** Empty/no choices → still renders the canon + counts; the free-text blurb is optional.

### 5.2 Technical fixes (all editions)
- **Left-align** body text — remove the justified setting that stretched short lines ("Edition   ID:   …").
- **Cover fits in-frame** — `object-fit: contain` + corrected sizing on `.cover-img` (`scripts/build_edition.py::apply_edition_cover` + cover CSS).
- **Reliable glyphs** — inline markers use the badge/number (never tofu); the in-note category symbols use a glyph set verified to render in Apple Books / common EPUB fonts, **embedding a small font subset if any required glyph is unavailable** (verified during implementation).
- Remove all `TODO_`; compute real counts.

### 5.3 Symbol legend — "A Guide to the Notes" (added 2026-05-24, user request)
Because §4.4 moves the category symbols **out of the running text and into the notes**, the reader needs a key to decode them (otherwise `◇ ✦ ⌂ ⌘ ✧ ‖ …` become unexplained decoration). Add a dedicated front-matter page, **"A Guide to the Notes,"** injected right after the colophon with its own `nav.xhtml` TOC entry, built the same way as the colophon (`render_*_page` + `inject_*_page`).
- **Edition-aware:** list only the categories that actually appear in *that* edition — iterate `content/categories.yaml` in `sort_order`, include a category iff `scripts.core.matrix.breakdown_by_category(edition_id).get(cat_id, 0) > 0`. Mirrors the "real computed counts" principle (§5.1).
- **Each row:** the category `symbol` + `label` + `description` + the edition's note-count for that category. Data source = `content/categories.yaml` (`id`/`label`/`symbol`/`description`/`sort_order`) via `config.load_categories()`.
- **Glyph reliability (§10):** the legend is the one place every symbol is shown deliberately — verify each renders in Apple Books / common EPUB fonts; embed a font subset if any does not.
- Built-in (like the colophon), not a per-edition toggle.
- **Edition-aware = exactly the user's ask (confirmed 2026-05-24):** a symbol appears in the guide ONLY if the builder's edition actually contains that category (notes > 0). Disabling a category in `/customize` (or a canon that excludes it) removes its symbol from the guide automatically — unused symbols never show.
- **Clickable cross-link (user 2026-05-24):** give each guide row a stable anchor `id="legend-<category-id>"` (added in Phase 1, Task 4); when the category symbols move into the notes (§4.4, Phase 2), each in-note symbol becomes a link to its guide entry (tap a symbol → jump to its definition). The guide is itself reachable from the reader TOC via its nav entry.

### 5.4 Back matter — end-of-book pages (user 2026-05-24: all four chosen; default-on all 11 editions, per-edition-configurable later)
Symmetric to the front matter; appended AFTER the last biblical book, each with a `nav.xhtml` TOC entry, built like the front-matter pages (`render_*_page` + `inject_*_page`; OPF manifest+spine append after the last bodymatter item).
1. **Sources & Acknowledgments** — the FULL public-domain/CC attribution list: WEB base text, Strong's, TSK cross-references, the patristic/canonical voices (Cyril, Ephrem, Athanasius, Jubilees, 1 Enoch, Meqabyan), and every translation witness baked/selected (WLC, LXX-Swete, Byzantine, Vulgate, Douay, JPS, Arabic, Brenton). Source: `content/sources/ATTRIBUTIONS.md` + per-note attribution + the popup-version registry. The FRONT colophon keeps only a BRIEF one-line sources pointer ("full credits at the back") to avoid duplication. **Easy, data-ready. Phase 1.**
2. **Closing colophon / "The End"** — a short dignified end page: "YHWH Ya' Way Editions · <edition title> · generated <build date> · `urn:yhwh:edition:<id>`" + a closing line. Genuinely the last page. **Trivial. Phase 1.**
3. **Reference tables** — weights, measures, money, and a biblical calendar (static reference content common in study Bibles). **Easy static. Phase 1.**
4. **Topical index (Nave's)** — a back-of-book index of verses by theme, generated from the 26,335 `topic-nave` notes (compose from the existing corpus; group by topic → verse list). Larger formatting effort. **Phase 2.**

Back-matter order (after the last book): **Sources & Acknowledgments → Reference tables → Topical index → Closing colophon**. All default-on for the 11 editions; a per-edition toggle to hide any can come later (RULES §2). EPUBs don't strictly need back matter (the TOC navigates), but a study Bible conventionally has it and it's the right home for source credits.

## 6. Scope

All **11 editions** (shared `stylesheet.css` + pipeline). Marker / popup-style / note-popup / title-page settings + per-book art apply everywhere; front-matter consolidation applies to each edition's front matter. Per-tradition default overrides can be added later but are not required for this work.

## 7. Architecture / wiring (per RULES §9)

For each new field (`marker_style`, `verse_popup_style`, `note_popup_style`, `title_page_style`):
1. **Schema** — add to `editions.yaml` with the default; unset == default (back-compat).
2. **Loader** — surface in `api_customize_data`.
3. **Validator** — `api_save_edition_meta` accepts + validates the enum.
4. **UI** — a `/customize` dropdown control.
5. **Build** — read in the pipeline; default behavior when unset.
6. **Tests** — round-trip, invalid-input rejection, back-compat, UI-present, and per-option rendering correctness.

Most settings switch a **container/body class**; the underlying data is unchanged. `marker_style` is the exception — it requires two emission paths in `inject.py`.

## 8. Testing

- **Per setting:** schema round-trip; `api_customize_data` exposes it; build emits the right mode/class; invalid value rejected; unset → default.
- **`marker_style=badge`:** a multi-note verse yields exactly one verse-end badge + a note-list container; **`=numbers`:** one inline superscript number per note + individual asides; neither emits inline category symbols.
- **Verse popups:** `kjv` absent; default set (`wlc`/`lxx-greek`/`greek-nt`/`vulgate`/`arabic`) present **when data exists**; per-verse existence respected; `cards`/`stack` class applied per setting.
- **Note popups:** category symbol present in-note; no stray `‖`; `chip`/`pills` layout per setting.
- **Front matter:** zero `TODO_` in output; computed counts present (not "1,371"); exactly 2 pages; left-aligned.
- **Cover:** `object-fit`/sizing present (extend `tests/test_covers.py`).
- **Title pages:** per-book art referenced per chosen style; text-only fallback when art absent.
- **Integrity:** representative editions epubcheck-clean after changes; `ebible verify` errors=0.

**Byte-compat note:** this **intentionally changes** built output, so the usual "zero output change" invariant does **not** apply. Instead, pin the **new** expected output (the new defaults) and prove the *non-targeted* parts (note bodies, verse text, counts of asides) are unchanged via categorize-diff.

## 9. Suggested implementation phasing (for the plan)

1. **Quick wins (low risk):** technical fixes (left-align, cover fit), front-matter consolidation + real counts + drop `TODO_`. No new settings; immediate visible improvement.
2. **CSS/template-variant settings:** `verse_popup_style`, `note_popup_style`, `title_page_style` + the widened popup witness default + drop `kjv` + book-art wiring + **`marker_style=numbers`** (the default — inline footnote numbers, no inline category symbols, symbols moved into the notes). Mostly schema + `/customize` + CSS/templates + a small `inject.py` marker tweak.
3. **Deferred / optional:** `marker_style=badge` — the per-verse-grouping + verse-end-badge mode in `inject.py` (resolve the base-HTML injection point first, §10). The default `numbers` already covers the immediate goal, so this can land later.

Each phase ends epubcheck-clean + gates green; each is independently shippable. Phases 1–2 are the committed scope; Phase 3 is deferred.

## 10. Open items resolved during implementation
- **Glyph reliability:** confirm which in-note category glyphs render in Apple Books; embed a font subset if any do not. (Decision is "numbers/badge inline = always safe; in-note symbols = verify + embed if needed.")
- **Base-HTML approach for the verse-end badge / per-verse note container:** confirm the cleanest injection point against the recovered base structure (`dev/MATRIX_MAP.md` "Base-HTML structure"). **Only blocks the DEFERRED `badge` mode** — the default `numbers` mode does not need it, so this does not block the committed Phase 1–2 work. (User noted 2026-05-24 they are also unsure of the best injection point; hence `numbers` is the default.)

## 11. Decisions captured (from brainstorming, 2026-05-24)
- Marker styles offered: **numbers (default — inline, "safe always") + badge (offered but DEFERRED; injection point TBD)** (symbols dropped from the inline picker; symbols live in notes).
- Popup layout: **cards (default) + stack**.
- Popup default witnesses: **Hebrew + Greek (LXX/NT) + Latin + Arabic**; JPS/Douay/Brenton selectable.
- Title-page: **full-bleed (default) + framed**.
- Note popup: **chip (default) + pills**.
- Front matter: **consolidate to 2 pages**; publisher **"YHWH Ya' Way Editions"**, date **"2026"**, © **Bogdan Zorlescu**.
- Scope: **all 11 editions**.
- Symbol legend: **a dedicated edition-aware "A Guide to the Notes" front-matter page** after the colophon (added 2026-05-24 — the necessary companion to moving symbols into the notes, §4.4/§5.3).
- Per-book title-page art: **builder-uploadable** (drag-in, size-restricted) per book per edition, reusing the existing cover-upload pipeline; title text unchanged; default = `_book_defaults/<book>.jpg` (added 2026-05-24, §4.5).
- Main cover options: the 25-template library (5 designs × 5 colours) is **intact**; a builder-facing **clickable** cover-design+colour picker (or upload-your-own) is **CONFIRMED Phase-2 scope** (user 2026-05-24), and the cover title must use a **universal placement** that works across all 5 designs + proper centering (§4.6).

## 12. Implementation corrections (discovered during planning recon, 2026-05-24)
Four reconnaissance passes over the code refined the spec's file-level claims. These are authoritative for the plan:
1. **The stale "1,371 annotations across 14 categories" is a hardcoded string literal at `scripts/build_edition.py:1344`** (inside `render_copyright_page`), NOT sourced from `content/onix.py`. The `TODO_` placeholders ARE real and DO leak onto the live copyright page: `inject_copyright_page` (`build_edition.py:1880`) loads `content/onix.py::DEFAULTS` and passes `publisher`/`contributor`/`copyright_year`/`publication_date` (all `TODO_*`) into `render_copyright_page`. Fix = switch the copyright page to consume `_resolve_publishing(edition)` (`build_edition.py:1025`, which already has real defaults) + computed counts from `scripts.core.matrix.total_for_edition` / `breakdown_by_category`.
2. **Front matter is not ~6 base pages.** The base `epub_working/` tree holds only `titlepage.xhtml` (the cover) + `introduction.xhtml` (placeholder copy); `copyright.xhtml` is generated at build time and its four `<h2>` sections *read* like several pages. "Consolidate to 2 pages" = collapse the copyright sections + drop the placeholder `introduction.xhtml` from the per-build manifest+spine.
3. **Dropping/widening verse-popup witnesses (§4.3) is NOT a `generate_verse_popups.py` change.** That script bakes ALL `_BAKED_NOW` witnesses (incl. `kjv`) into the shared base; the per-edition build PRUNES via `build_edition.py::_resolve_popup_languages` (730-753) reading `popup_languages_default`/`_per_book`. So drop-kjv/widen = edit each edition's `popup_languages_default` in `editions.yaml` (legacy ids `english/hebrew/greek` at lines 123,158,205,242,271,310,350,394,436; two empty at 501,542) + change the unset-default fallback (~749) so `kjv` is dropped everywhere. Physically re-baking the base to remove `kjv` is the heavier, optional path.
4. **`marker_style`: numbering must be COMPUTED** — markers carry no sequence number today (the `<sup>` holds the category glyph). `scripts/inject.py` runs **base-wide** (per-book, into the shared base), not per-edition. So `marker_style=numbers` lands as a base-wide change to `build_marker` (`inject.py:150`) + a numbering pass (reset boundary chosen explicitly) + dropping the inline glyph; the `editions.yaml` field defaults to `numbers` for forward-compat, and true per-edition marker switching waits for the deferred `badge` mode (a build-time post-pass). The `‖` is the `xref` category symbol (`categories.yaml:28`) reused as the `.note-back` back-link char in `build_aside` (`inject.py:190`) — fix = give the back-link a fixed `↩` (as `vnote-back` already does, `generate_verse_popups.py`) and render the category symbol as a deliberate in-note element.
5. **`title_page_style`:** the per-book art (`content/covers/_book_defaults/*.jpg`, 66 of 87 books) does NOT enter the EPUB today, and `scripts/customize.py`'s `.html.frag` staging is orphaned (no build-time consumer). Wire `title_page_style` through `build_edition.py::build_one` like `theme` / `apply_chapter_decoration` (a new `apply_title_pages` + a `patch_opf_book_images` modeled on `patch_opf_fonts`, `build_edition.py:2407`) — NOT through `customize.py`. The 21 art-less Ethiopic-canon books fall back to the current text-only title page.
