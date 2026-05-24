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
- `scripts/customize.py` title-page injection (`content/title_pages/<book>.html` fragments) + CSS; new per-book art reference.

## 5. Built-in (not toggles)

### 5.1 Front-matter consolidation
- Replace the ~6 placeholder pages with **2 pages**:
  1. **Title page** (clean).
  2. **Colophon:** "YHWH Ya' Way — <edition title> · Published by **YHWH Ya' Way Editions**, **2026** · © Bogdan Zorlescu" + canon summary + sources / PD bases + **real computed counts** (notes + categories for that edition).
- Remove **all** `TODO_` placeholders (sourced from `content/onix.py` defaults — a dead ONIX vestige).
- Replace the hardcoded **stale "1,371 / 14 categories"** with the edition's real computed counts.
- `scripts/build_edition.py::render_copyright_page` (+ `inject_copyright_page`).

### 5.2 Technical fixes (all editions)
- **Left-align** body text — remove the justified setting that stretched short lines ("Edition   ID:   …").
- **Cover fits in-frame** — `object-fit: contain` + corrected sizing on `.cover-img` (`scripts/build_edition.py::apply_edition_cover` + cover CSS).
- **Reliable glyphs** — inline markers use the badge/number (never tofu); the in-note category symbols use a glyph set verified to render in Apple Books / common EPUB fonts, **embedding a small font subset if any required glyph is unavailable** (verified during implementation).
- Remove all `TODO_`; compute real counts.

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
