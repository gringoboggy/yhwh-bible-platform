# The Matrix — data-flow & integrity map

> Map for humans + future Claude. "The matrix" = the **editions × kinds count
> grid** (`scripts/core/matrix.py`): "if I shipped edition X now, how many notes
> of each kind would appear?" It is anchored on the same edition profiles
> (`content/editions.yaml`) that drive the **build pipeline** — so the matrix and
> the EPUB build are two consumers of one source of truth.
>
> Counts (verified 2026-05-20 via `dev/trace_matrix.py`): **11 editions · 5 canons
> · 15 categories · 70 kinds · 87 books · 13 translation dirs**. Integrity:
> **0 unresolved references.**

## Top → bottom (source leads to output)

```
CONFIG  (content/*.yaml)  — the rows, columns, and leaves
  editions.yaml ......... 11 edition profiles      → the matrix ROWS
  kinds.yaml ............ 70 kinds → category       → the matrix COLUMNS
  categories.yaml ....... 15 categories             (column groups; AI-gate via enable_ai_notes)
  canons.yaml ........... 5 canons → book-code sets  (book filter; ethiopian = 87-book superset)
  books.yaml ............ 87 books                   (canonical spine / order)
  translations/<id>/ .... 13 dirs                    (base_translation, popup_translation)
  traditions / themes / customization / source_dates / edition_templates/* / scenarios/*
        |
        v
LOADERS  scripts/core/config.py   (lru-cached: load_editions/books/kinds/categories, *_by_id/code)
        |
        +───────────────────────────────────────────────+
        v                                                 v
MATRIX  scripts/core/matrix.py                       BUILD  scripts/build_edition.py
  compute_matrix()                                     compute_enabled_kinds()   <== MIRRORS matrix
    -> core/corpus_index.compute_matrix_indexed()      filter_html()  (canon book-splice + kind
    -> Matrix(per_chapter, edition_enabled_kinds)        filter + tradition labels + time filter
    derived views: enabled / potential / per_book        + popup languages/translation)
        |                                              patch_opf() / render_copyright_page()
        v                                                _apply_popup_languages_and_translation()
  CONSUMERS of the grid:                                    |
    web.py (customize / symbol-toggle UI)                   v
    scripts/matrix.py (CLI)                             build_epub.py -> covers/ + title_pages/
    api/{customize,editions,exports,preflight}.py            -> EPUB  (the actual output)
    dashboard.py, core/snapshots.py, edition_templates.py
        |
        v
VALIDATORS (gate everything):
  api/preflight.py · validate_schemas.py · validate_taxonomy.py
  lint_rules.py (pre-commit hook) · check_manifest.py · check_content.py
  dev/trace_matrix.py  (this map's reference-tracer)
```

## Bottom → top ("I see X in the output — where did it come from?")

- **A note in the EPUB** <- `content/notes/<book>.py` (carries a `kind` code) <- survived
  `build_edition.filter_html` because `kind ∈ edition's enabled-kinds` (= `enabled_categories`'
  kinds + `enabled_kinds` − `disabled_kinds` − AI-gated unless `enable_ai_notes`) **and**
  `book ∈ canons.yaml[edition.canon].books`.
- **A book present / spliced out** <- `canons.yaml[edition.canon].books` (a subset of `books.yaml`).
- **A verse popup** <- `popup_translation` (-> `translations/<id>/`) + `popup_languages_default`
  / `popup_languages_per_book`.
- **Cover / OPF metadata** <- `cover_image`, `authors`, `bisac_codes` -> `patch_opf`.
- **A count cell in the matrix UI** <- `matrix.compute_matrix().enabled[ed][kind]` <- `per_chapter`
  <- `notes_io.load_notes(notes/<book>.py)`.

## Variable trace table (editions.yaml field -> resolves against -> consumed by)

| field | resolves against | consumed by | trace |
|---|---|---|---|
| `canon` | `canons.yaml` ids | matrix book-scope; build book-splice | OK 5/5 |
| `enabled_categories` | `categories.yaml` ids | matrix `_enabled_kinds_for_edition`; build `compute_enabled_kinds` | OK |
| `enabled_kinds` / `disabled_kinds` | `kinds.yaml` codes | same (both paths) | OK |
| `enable_ai_notes` | gate for `AI_DRAFTED_KINDS` (`comm-ai`) | matrix + build kind gate | OK |
| `popup_translation` | `translations/<id>/` | build `_replace_verse_popup_translation` | OK (`kjv`, `*-en`, `""`) |
| `base_translation` | `translations/<id>/` | standalone build body (deferred τ.G.x.*) | OK |
| `popup_languages_default` / `_per_book` | language ids | build `_apply_popup_languages_and_translation` | not ref-checked (lang names) |
| `cover_image` | `content/covers/` | `patch_opf` / covers | OK (empty on standalones = skipped) |
| `max_phase` | phase tag on kinds | phase filter | not checked by tracer |
| `traditions_default` / `_per_book` | `traditions.yaml` | build tradition filter | not checked by tracer |

## Findings — accreted, low-risk cleanup targets

The reference graph is sound (0 dangling refs). The blemishes are cosmetic/structural,
products of organic growth from the original 1-Bible builder:

1. **Stale docstring** — `core/matrix.py` says "5 edition profiles" / "63 kinds"; actual
   **11 / 70**. Code reads dynamically, so behavior is fine; only the doc lies.
2. **`editions.yaml` comment drift** — section-header comments sit *above* the previous
   edition's trailing `popup_languages_default` block, so the comment for edition N+1 appears
   to caption edition N's last key (e.g. the "catholic / largest English market" header sits
   above `ethiopian-tewahedo`'s `popup_languages_default`). Values are per-edition sensible, but
   confirm `ethiopian-tewahedo`'s `[english, hebrew, greek]` popups are intended.
3. **Logic divergence — RESOLVED (2026-05-20).** "Which kinds ship in this edition" was implemented
   THREE times with drifting gates: `build_edition.compute_enabled_kinds` (phase gate, no ai-gate),
   `matrix._enabled_kinds_for_edition` (ai-gate, no phase gate), `config._kinds_in_edition` (phase
   gate, no ai-gate). The matrix therefore **over-counted** vs. the actual build for the 10 editions
   with `max_phase` < `phase3` (e.g. `ethiopian-tewahedo` showed 25 phase-gated kinds the EPUB never
   contained, incl. its own explicitly-enabled `dist-typological`/`dist-mariological`).
   **Fixed:** one canonical `config.enabled_kind_codes(edition, all_kinds)` applying BOTH gates
   (precedence: explicit-`disabled_kinds` > phase gate > AI double-opt-in > `enabled_kinds`/category);
   `matrix._enabled_kinds_for_edition`, `build_edition.compute_enabled_kinds`, and
   `config._kinds_in_edition` all delegate to it. Invariant pinned by
   `tests/test_enabled_kinds_unified.py` (matrix == build == config for every edition). Matrix counts
   dropped to the correct build-matching values; build output unchanged (`comm-ai` corpus = 0).
4. **Vestigial ψ.35 layering** — `Matrix.enabled/potential/per_book` are now derived projections
   kept only so old `m.enabled[ed]` reads keep working. A future slice could drop them for
   `@cached_property`.

## Re-run the integrity trace

```
py dev/trace_matrix.py        # read-only; reuses the real config loaders; prints per-edition trace
```
Exit is report-only today. Wire into `validate_taxonomy.py` / pre-commit if you want it enforced.

## Build pipeline (downstream of the matrix) & the base-HTML gap

Reverse-engineered 2026-05-21 while verifying the deliverable builds. The matrix decides WHICH
notes/books ship per edition; the build turns that into the EPUB the user downloads:

```
content/notes/<book>.py        (52,973 notes — SOURCE)
content/translations/<id>/*.py (verse text as data — SOURCE; powers matrix/parallel/standalone)
        |
        v  inject   (ebible build step 1 = scripts/inject.py --all-books)
epub_working/index_split_*.html   <== BASE SCRIPTURE HTML (calibre-split chunks; the scripture
        |                             TEXT source-of-truth, edited IN PLACE — NOT rendered from
        |                             translations. Notes land as id="note-X" paired with
        |                             href="#note-X"; verses carry id="v-<book>-<ch>-<v>".)
        v  build_edition.py <id>   (filter notes per edition via config.enabled_kind_codes + canon)
per-edition working copy
        v  build_epub.py / build.sh   (mimetype-first store-only zip)
<edition>.epub   (deliverable; dc:identifier = urn:yhwh:edition:<id> — CC0, not for sale)
```

Health invariant: **paired=N/N** — every `href="#note-X"` has a matching `id="note-X"`. Check before/after any build.

**THE GAP (2026-05-21):** `epub_working/` (the base scripture HTML) is a build artifact that is NOT
in the current repo — never committed, now absent — so `inject` errors "no readable HTML files" and
`ebible build` dies at step 1. The legacy injectors `run.py` references (`source_archive/`,
`kings_session/`) are also gone. **Recovery source:** `…/Ethiopian_Bible_HANDOFF_v9_2026-05-05`
contains `epub_working/index_split_*.html` (all 87 books' text, TOC-wired) + `source_archive/` +
`kings_session/` + a built 4.6 MB EPUB. The 05-05 base text is TEXT-complete for the 87-book English
canon; the current 52,973 notes re-inject fresh (injector is idempotent). The standalone Ge'ez/Amharic
Bibles need their own base HTML (newer, separate).

**Production risk it exposes:** the scripture base HTML is a large, hand-edited, UNCOMMITTED calibre
artifact — losing it (as happened) blocks every build. Fix options in
`dev/AUDIT_2026-05-21-smoother-running.md`.
