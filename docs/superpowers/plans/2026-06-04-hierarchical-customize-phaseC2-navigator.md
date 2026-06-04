# Hierarchical Customization — Phase C2: the `/build-my-bible` Navigator Console — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new `/build-my-bible` console — a **drill-down + breadcrumb** navigator (Bible → book → chapter → verse) where a builder toggles note-symbol families (and individual kinds) and translation-popup languages at every level, persisting through the existing API.

**Architecture:** A lazy read API (`api_build_my_bible`) feeds a single-panel drill-down UI (breadcrumb back, click to go deeper) that mirrors the `/sources` console pattern. Symbol toggles are tri-state (inherit/on/off) → computed into the `note_families_*_per_{book,chapter}` fields; popup toggles are language checklists → the `popup_languages_per_{book,chapter,verse}` fields; both persist via the Phase-C1 `api_save_edition_meta`. The individual-verse level reuses the `/sources` per-note toggle (`disabled_note_ids`) + adds the `enabled_note_ids` force-on write path. All shipped engines (Phase A/B) already make the build honor these fields.

**Tech Stack:** The project console stack — one `BaseHTTPRequestHandler` route in `scripts/web.py`, a `scripts/templates/build_my_bible.py` HTML template, Tailwind via CDN, plain ES6 (no build step). No new deps.

**Status:** SHIPPED 2026-06-04 — C2-2…C2-6 complete (commits `ce591d93`→`48d0f21f`, rebased onto Mac's `2064b86d`). The `/build-my-bible` navigator console: drill-down + breadcrumb; interactive symbol tri-state (book+chapter) + popup checklists (book/chapter/verse) saving via `PUT /api/edition-meta/<id>`; verse-level per-note "ships?" toggle via `PUT /api/edition/<id>/note-override`; Bible level read-only w/ /matrix + /customize cross-links. Byte-neutral (no build-path change; byte-stability gate + `git diff epub_working` empty); live Playwright QA passed (all 4 levels, both save flows, 0 console errors); per-task spec+quality + final holistic review all clean. C3 (polish) follows. Phase C2 of the hierarchical-customization spec (`docs/superpowers/specs/2026-06-04-hierarchical-edition-customization-design.md`, §8). UX = drill-down + breadcrumb (user-chosen).

---

## Pre-flight (read once)

- Spec §8 (the navigator design + API), §3 (the precedence model the UI must mirror), §10 (decisions).
- **Patterns to mirror** (read them):
  - `scripts/templates/sources.py` — the drill-down console: edition picker, left book rail, right notes-by-chapter panel, the per-note checkbox + `toggleNote()` → `PUT /api/edition/<id>/note-toggle`, the `disabled-notes` fetch. **This is the closest existing pattern — the navigator is a generalization of it.**
  - `scripts/templates/customize.py` — the per-book popup-languages + traditions matrices: `buildCustomizePayload()` / `saveEdition()` (POST `/api/edition-meta/<id>`), `renderKinds()` (category→kinds grouping), the state/dirty pattern (`querySelectorAll('input, select')`, RULES §6.4).
  - `scripts/templates/build_tracker.py` + `scripts/web_editions.py:api_build_tracker` — the per-book × per-chapter heat-grid + lazy per-book detail (`/api/build-tracker/<edition>/<book>`).
  - `scripts/web_editions.py:api_customize_data` — provides `books_canonical`, `edition_canon_books`, `categories` (id/label/symbol/sort_order), `kinds` (code/category/symbol/label), `popup_languages`, and (Phase C1) the decoded new per-coordinate fields.
  - The console framework: `scripts/templates/_design.py` `CONSOLES` list + `HEADER_NAV_LINKS`; `scripts/lint_rules.py` check `6.2` (every console cross-links to every other); `scripts/web.py` route registration (`_SIMPLE_GET_ROUTES` / `_REGEX_GET_ROUTES` + the `do_GET`/`do_POST` cascade).
  - Resolvers the UI must call to show resolved state: `config.enabled_kind_codes_for(edition, all_kinds, book, chapter)` (symbols) + `build_edition._resolve_popup_languages(edition, book, chapter, verse)` (popups). Counts/verses: `scripts/core/canonical_verse_counts.py` (verses per chapter), `config.books_by_code()[code]["ch_count"]`, `matrix` per-book/per-chapter accessors.
  - `scripts/api/editions.py:api_save_note_toggle` (`disabled_note_ids` per-note) — extend for `enabled_note_ids` force-on.

**Windows env (every test run):** `$env:PYTHONUTF8="1"`; `py -3`; `--basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`; PowerShell, one file at a time; `ruff format` before each commit; per-task LOCAL `pwsh -File save.ps1`; full 5-leg `save-all.ps1` at the last task. **Byte-neutral:** C2 touches the web/UI/API layer only — no `build_one`/resolver/`epub_working` change. A quick byte-stability gate at the end is a backstop, not the focus.

**Persistence model (how the UI saves) — read carefully.** The UI never writes YAML directly. It POSTs to `/api/edition-meta/<id>` (the Phase-C1 `api_save_edition_meta`, which validates + encodes the 6 keyed fields) for family-level symbol/popup changes, and to `/api/edition/<id>/note-toggle` (+ the new force-on path) for individual notes. The UI computes the **delta** for a touched coordinate and sends the whole field map for that field (the encoders are absolute-replace per field). Tri-state semantics: *inherit* = the token/key is ABSENT from the field; *on* = in `note_families_on_per_<scope>`; *off* = in `note_families_off_per_<scope>`. A coarse bulk toggle clears the finer entries in scope (spec §3.2) — the UI strips the now-redundant finer keys from the payload before POSTing.

---

## Task C2-1: the read API `api_build_my_bible`

**Files:** Create/extend `scripts/web_editions.py` (a new `api_build_my_bible` fn) + route in `scripts/web.py`. Test: `tests/test_build_my_bible_api.py` (new).

Three lazy levels (compose existing endpoints; RULES §9 "compose, don't recompute"):
- `GET /api/build-my-bible/<edition>` → `{edition:{id,title,short_title}, books_canonical:[{code,title,ch_count}], categories:[…], kinds:[…], popup_languages:[…], resolved_bible:{symbols:{<category>:on|off}, popups:[lang…]}, overrides:{note_families_on_per_book, …all 6 decoded…, disabled_note_ids, enabled_note_ids}}` — the edition overview + everything needed to render the Bible level + the book rail. Filter books to `edition_canon_books[edition]`.
- `GET /api/build-my-bible/<edition>/<book>` → `{book:{code,title,ch_count}, chapters:[{num, has_notes:bool, resolved:{symbols, popups}}], resolved_book:{…}}` — per-book detail (chapter list + each chapter's resolved state). `has_notes` from the matrix per-chapter counts.
- `GET /api/build-my-bible/<edition>/<book>/<ch>` → `{chapter:num, verses:[{vs, resolved:{symbols, popups}, notes:[{note_id, kind, category, symbol, title, disabled:bool, forced_on:bool}]}]}` — per-chapter detail incl. the individual notes per verse (compose `/api/sources/<book>` filtered to the chapter + `enabled_kind_codes_for`/`_resolve_popup_languages` for resolved state).

- [ ] **Step 1: failing tests** — for a real edition (e.g. `catholic-study`): the edition-level call returns `books_canonical` in canonical order filtered to its canon, the registries, and `resolved_bible.symbols`/`popups` matching `enabled_kind_codes_for(ed, kinds, <any book>)`/`_resolve_popup_languages(ed, <book>)`; the per-book call returns `ch_count` chapters; the per-chapter call returns verses with notes for a chapter known to have notes (e.g. `gen` ch 1). Assert shapes + that `resolved` matches the resolvers directly. Use a no-override edition so `resolved` == the edition default.
- [ ] **Step 2: run-fail.**
- [ ] **Step 3: implement** `api_build_my_bible(edition_id, book=None, chapter=None)` composing `api_customize_data` (registries + books_canonical + edition_canon_books + decoded overrides), `config.books_by_code()` (ch_count), `canonical_verse_counts` (verses/chapter), the matrix per-chapter accessor (has_notes), `/api/sources/<book>` data (notes), and the two resolvers (resolved state). Pure function returning a dict (RULES §9 pure-fn + thin-route). Add the 3 routes in `web.py` (regex `^/api/build-my-bible/([a-z0-9-]+)(?:/([a-z0-9]+))?(?:/(\d+))?$`).
- [ ] **Step 4: run-pass + lint + mypy.**
- [ ] **Step 5: commit LOCAL** `pwsh -File save.ps1 -Message "ρ.3 Phase C2-1: api_build_my_bible read API (lazy 3-level drill-down data)"`.

---

## Task C2-2: the console shell + registration

**Files:** Create `scripts/templates/build_my_bible.py` (`BUILD_MY_BIBLE_HTML`); modify `scripts/web.py` (serve `/build-my-bible`), `scripts/templates/_design.py` (`CONSOLES` += `("/build-my-bible","build my bible")`), and add the new console's link to every other console's `HEADER_NAV_LINKS` block (the §6.2 lint enforces this — run it).

- [ ] **Step 1:** write `BUILD_MY_BIBLE_HTML` — header with `HEADER_NAV_LINKS("/build-my-bible")`, an edition `<select>`, a breadcrumb `<nav>`, a left book rail, and a right level-panel `<div id="level-panel">`. Tailwind CDN, mirror `sources.py`'s shell. No interactivity yet (static shell + the JS skeleton).
- [ ] **Step 2:** register the route in `web.py` (serve the HTML); add `/build-my-bible` to `CONSOLES` in `_design.py`; add the cross-link to all existing console headers.
- [ ] **Step 3:** run `py -3 scripts/lint_rules.py` — the `6.2` cross-link check must pass (all consoles link to `/build-my-bible` and it links to all of them). Run any console-presence test (`test_scripts.py -k console` / the `SESSION_STATE inventory matches consoles` lint — update the console inventory count in `dev/SESSION_STATE.md` if pinned).
- [ ] **Step 4: commit LOCAL** `pwsh -File save.ps1 -Message "ρ.3 Phase C2-2: /build-my-bible console shell + route + cross-link registration"`.

---

## Task C2-3: drill-down navigation JS

**Files:** `scripts/templates/build_my_bible.py` (the JS).

- [ ] Implement: on edition select → fetch `/api/build-my-bible/<ed>`, render the book rail (canonical order, RULES §6.1) + the **Bible-level** panel (breadcrumb = "Bible"). Click a book → fetch `/api/build-my-bible/<ed>/<book>`, breadcrumb "Bible ▸ Genesis", render the chapter list. Click a chapter → fetch the per-chapter detail, breadcrumb "… ▸ Chapter 3", render the verse list. Click a verse → render the verse's notes (individual level). Breadcrumb segments are clickable (go back up). **Lazy** — fetch per level on demand; cache fetched levels in a JS map. Show a spinner while fetching. Match `sources.py`'s fetch/render idioms.
- [ ] Manual-ish test: a Playwright/`http.server` smoke (per memory `feedback_visual_qa_self_serviceable`) OR a JS-structure assertion test if the project has one; at minimum, a test that the route serves valid HTML and the API calls 200. Commit LOCAL.

---

## Task C2-4: symbol tri-state + popup-checklist controls + save

**Files:** `scripts/templates/build_my_bible.py` (the JS + the panel rendering).

- [ ] In each level panel render: **SYMBOLS** — one row per category (symbol + label) with a tri-state control (inherit/on/off); each category expands (a `<details>`) to its kinds (same tri-state). **POPUPS** — a language checklist (the `popup_languages` registry) reflecting the resolved set for this scope. Seed each control from the level's `resolved` state (faint "inherit" shows what it'd inherit).
- [ ] **Save logic:** on change, compute the field payload for the touched scope and POST `/api/edition-meta/<ed>`:
  - symbol tri-state at book level → update `note_families_on_per_book` / `note_families_off_per_book` maps (add the token to on/off, or remove for inherit); at chapter level → the `_per_chapter` maps (key `"book:ch"`). Kind tokens vs category tokens per spec §3.
  - popup checklist at chapter level → `popup_languages_per_chapter["book:ch"] = [langs]`; at verse level → `popup_languages_per_verse["book:ch:vs"]`; at book level → `popup_languages_per_book`.
  - **Bulk-clears-finer (spec §3.2):** when a coarse toggle changes, strip the now-redundant finer keys for that selectable in scope from the payload.
  - Participate in the dirty-check (`querySelectorAll('input, select')`, §6.4); re-fetch the affected level after save to re-seed `resolved`.
- [ ] Tests: an API round-trip test (the UI's computed payload → `api_save_edition_meta` → re-read via `api_build_my_bible` shows the new resolved state). Commit LOCAL.

---

## Task C2-5: the individual-verse level (notes + force-on)

**Files:** `scripts/templates/build_my_bible.py`; `scripts/api/editions.py` (extend the note-toggle for `enabled_note_ids`).

- [ ] At the verse level, render each note (symbol + kind + title + a checkbox = "ships?") and the per-verse popup checklist. The checkbox reflects the note's resolved state (family on/off + individual override). Toggling writes the right per-note override:
  - if the note's family is ON for this coordinate and you un-check → add to `disabled_note_ids` (existing `note-toggle`);
  - if the family is OFF and you check → add to `enabled_note_ids` (**force-on, new**);
  - re-check/uncheck to the resolved-default → remove from both.
- [ ] **Extend `api_save_note_toggle`** (or add `api_save_note_force_on`) to manage `enabled_note_ids` symmetrically to `disabled_note_ids` (the Phase-A build already honors `enabled_note_ids`). Add it to the `web.py` routes. TDD the API (add/remove a force-on id; conflict resolution — force-on wins).
- [ ] Tests: API round-trip for `enabled_note_ids`; a build-integration check is already covered by Phase A's `test_hierarchical_symbols_build.py`. Commit LOCAL.

---

## Task C2-6: byte-stability backstop + docs + 5-leg save

- [ ] **Byte-stability backstop:** C2 is web/UI/API only, but run `git status --porcelain epub_working` (empty) + the byte-stability gate once (it builds editions with no new fields → must stay byte-identical). Affected suites: `test_hierarchical_api`, `test_build_my_bible_api`, `test_scripts -k "edition or console or sources"`, lint (the §6.2 cross-link), mypy.
- [ ] **Visual QA (self-serviceable):** unzip-free — start the server, drive `/build-my-bible` with Playwright/Chrome-devtools MCP (memory `feedback_visual_qa_self_serviceable`): pick an edition, drill Bible→book→chapter→verse, flip a symbol off at book level + a popup off at verse level, confirm the breadcrumb + the save + the re-render. Screenshot.
- [ ] **Docs:** truth records (C2 shipped; pull Mac first if pushed); INDEX (this plan); update the console-inventory count + `SESSION_STATE` console list. ruff format. **5-leg `save-all.ps1`.**

---

## Self-review notes

- **Compose, don't recompute (RULES §9):** `api_build_my_bible` must COMPOSE `api_customize_data` + `/api/sources` + the resolvers + `canonical_verse_counts`, not re-walk the corpus. Lazy per level.
- **Canonical order everywhere (RULES §6.1):** books, chapters, verses all ascending/canonical.
- **Resolved state must use the REAL resolvers** (`enabled_kind_codes_for`, `_resolve_popup_languages`) so the UI shows exactly what the build will do — single source of truth.
- **Don't write YAML from the UI** — always go through `api_save_edition_meta` (validates) / the note-toggle APIs.
- **The existing `/sources` + `/customize` per-book matrices stay** — they write the SAME fields, so they remain consistent faster paths; `/build-my-bible` is the unified navigator (spec §8).
- **C3 (polish) is separate:** `/build-tracker` resolved-state annotation, website "How you make it yours" copy rewrite, reconciling `/customize`/`/sources` to surface the new chapter/verse levels.
