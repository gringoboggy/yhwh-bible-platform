# The Matrix — data-flow & integrity map

> Map for humans + future Claude. "The matrix" = the **editions × kinds count
> grid** (`scripts/core/matrix.py`): "if I shipped edition X now, how many notes
> of each kind would appear?" It is anchored on the same edition profiles
> (`content/editions.yaml`) that drive the **build pipeline** — so the matrix and
> the EPUB build are two consumers of one source of truth.
>
> Counts (2026-05-21, after the reference-corpus rebuild): **11 editions · 5 canons
> · 15 categories · 71 kinds · 87 books · 13 translation dirs · 67,715 notes**.
> (Was 70 kinds / 52,973 notes on 2026-05-20; `dict-easton` added + Nave's rebuilt +
> Easton's ingested — see "Reference-corpus ingestion" below.) Re-verify with
> `dev/trace_matrix.py`; integrity target: **0 unresolved references.**

## Top → bottom (source leads to output)

```
CONFIG  (content/*.yaml)  — the rows, columns, and leaves
  editions.yaml ......... 11 edition profiles      → the matrix ROWS
  kinds.yaml ............ 71 kinds → category       → the matrix COLUMNS
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
content/notes/<book>.py        (67,715 notes — SOURCE; 2026-05-21 reference-corpus rebuild)
content/translations/<id>/*.py (verse text as data — SOURCE; powers matrix/parallel/standalone)
        |
        v  inject   (ebible build step 1 = scripts/inject.py --all-books)
        |   Strategy-A: id="v-<book>-<ch>-<v>" anchors.  Strategy-B (late canon):
        |   find_chapter_region_b/find_verse_region_b on id="ch-<bxx>-c<ch>"; when a chapter's
        |   verses spill across a split-file boundary, find_verse_region_b_spill resolves them
        |   from the next file's head (guarded to the last-anchor chapter). Word-anchor miss →
        |   verse-end fallback (resolve_marker_insertion). scripts/audit_base_html.py classifies
        |   regular vs split-file-irregular chapters + enumerates the residual.
        v
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

**THE GAP — RESOLVED (2026-05-21):** the base scripture HTML was recovered from the v28a-50 snapshot
and COMMITTED (`5ee2ad1`) so it can no longer be silently lost; `ebible build` produces valid EPUBs
again. The inject tail was then closed to ~99.5% by the Strategy-B spill resolver (see the inject step
above); the residual is base-HTML versification/coverage (1 Enoch 37-108, the aes WEB↔KJV scheme),
enumerated in `dev/AUDIT_2026-05-21-inject-tail-residual.md`. To re-derive a clean inject from scratch:
`git checkout 5ee2ad1 -- epub_working/` then `inject --all-books` (idempotent; reflects the current
corpus). NOTE — still latent: `run.py` / `add_note.py` reference the lost `source_archive/` +
`kings_session/` injectors; superseded by `inject.py` but would fail if invoked (retire/repoint TODO).

## Reference-corpus ingestion (PD reference works → notes)

The reusable pipeline that turns a public-domain reference work into verse-keyed notes feeding the
SOURCE above. Each source is a clean, committed text under `content/sources/`; a per-source parser
builds the per-verse mapping; notes are written via one batched inserter. Coordinate validation drops
impossible `(book, ch, v)` at the boundary so OCR/parse noise never reaches the corpus.

```
content/sources/<work>_source.txt   (clean committed text, extracted from a CCEL PDF)
  Nave's Topical:  naves_ccel_source.txt   -> scripts/extract_naves_ccel.py
                   (CCEL abbrevs; expand_refs carry-forward; note "Jud" = Judges, not Jude)
                   -> fetch_sources._build_naves_indices  (canonical-range VALIDATION)
                   -> content/sources/naves_topical.json  (4,604 topics / 100,983 refs)
                   -> NaveTopicalDetector  -> 26,335 `topic-nave` notes
  Easton's Dict:   eastons_ccel_source.txt -> scripts/extract_eastons_ccel.py
                   (• headwords; FULL book names via EASTON_BOOK; first ch:v ref = primary verse)
                   -> 3,779 `dict-easton` notes  (kind dict-easton, category hist)
        |
        v  scripts.promote.batch_insert_notes  (one read+write per book; per-verse free suffix +
        |    dedup; reuses format_tuple_text/pick_free_suffix — replaces per-note O(n²) inserts)
        v
content/notes/<book>.py
```

**Data-quality guard:** `fetch_sources._naves_coord_in_extent` rejects coordinates beyond a book's
canonical extent (`canonical_verse_counts.canonical_book_shape`); books with no canonical shape
(Tewahedo distinctives) are kept unvalidated. This closed a defect where an OCR'd Nave's source had
injected ~114 impossible-coordinate notes. **Book codes MUST match `content/notes/`** — the project
uses `eze`/`joe`/`nah`/`jam`/`phi` (+ `jdg` Judges, `jud` Jude); a code mismatch silently drops a
book's notes (caught + fixed for 5 books during the 2026-05-21 rebuild). Source provenance lives in
`content/sources/ATTRIBUTIONS.md`.
