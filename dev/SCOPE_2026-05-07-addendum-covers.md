# Scope addendum — Per-book covers + upload UI (Phase π.4)

**Added:** 2026-05-07, after ν.2.7-A.
**Origin:** direct user request — "About the Cover/Book Cover UI tool.
It's [set up] to work properly between each book and each Bible has the
correct amount of covers… the shorter [editions] won't show options
for covers on books that don't exist in that edition. Also is there a
way to allow the user to ATTACH pictures (with rules on size and all
that) directly through the UI?"

## What exists today

```
editions.yaml        each edition has a single cover_image string
content/covers/      empty (placeholder paths point nowhere)
print_cover.py       generates ONE printed-paperback PDF cover per
                     edition (spine width + barcode); not per book
```

There is no per-book cover model and no upload UI. π.4 was a placeholder
line item in `dev/PLAN_2026-05-07.md`.

## What this phase builds

### π.4-A — Model, canon-filtered API, storage (foundation)

Schema additions to editions.yaml:

```yaml
- id: catholic-study
  cover_image: "covers/catholic-study/main.jpg"   # main edition cover
  book_covers:                                     # per-book covers
    - "gen=covers/catholic-study/books/gen.jpg"
    - "exo=covers/catholic-study/books/exo.jpg"
    # Books not listed → no cover for that book (build pipeline
    # uses the standard chapter-1 page header, no image).
```

Encoded as a list of `"<book_code>=<path>"` strings — same indirection
pattern used for `popup_languages_per_book` (see CLAUDE_PROJECT_RULES.md
§7.2 and the build_edition encoder/decoder pair). The project's custom
YAML parser does not handle nested mappings; this format keeps the file
parseable.

API additions:
- `GET /api/covers` returns one record per edition:
  ```json
  {
    "edition_id": "catholic-study",
    "main_cover": {"path": "...", "exists": true|false,
                   "width": 1200, "height": 1800, "size_kb": 412},
    "book_covers": [
      {"book_code": "gen", "title": "Genesis",
       "path": "...", "exists": true|false,
       "width": ..., "height": ..., "size_kb": ...},
      …  // ONLY books in this edition's canon, in canonical order
    ]
  }
  ```
- The `book_covers` list is filtered by the edition's canon AND ordered
  by `content/books.yaml` position (Rule §6.1). Reformed editions ship
  66 entries, Tanakh 39, Ethiopian 87.
- Missing files are reported (`exists: false`) but the slot still
  appears so the publisher can fill it.

Storage layout:
```
content/covers/<edition_id>/main.<ext>
content/covers/<edition_id>/books/<book_code>.<ext>
```

### π.4-B — Upload backend + UI

Upload backend:
- `POST /api/covers/<edition_id>/main`             (multipart)
- `POST /api/covers/<edition_id>/book/<book_code>` (multipart)
- `DELETE /api/covers/<edition_id>/main`
- `DELETE /api/covers/<edition_id>/book/<book_code>`

Validation rules (rejected with a clear error before disk write):

| Rule              | Limit                                    |
|-------------------|------------------------------------------|
| Max file size     | 10 MB                                    |
| Min dimensions    | 600 × 900 px                             |
| Max dimensions    | 4000 × 6000 px                           |
| MIME types        | image/jpeg, image/png, image/webp        |
| Aspect ratio      | within ±20 % of 2:3 portrait (book-jacket) |
| Disk path safety  | reject `..`, absolute paths, hidden files |

Atomic writes via `notes_io.atomic_write`; existing covers backed up
to `.backups/` via `notes_io.ensure_backup` before being replaced.

UI:
- New console at `/covers` (cross-linked from every other console
  per Rule §6.2).
- Per-edition card; books listed in canonical Book/Chapter order
  (Rule §6.1) with a slot per book.
- Each slot shows a thumbnail (or placeholder), filename,
  dimensions, file size. Click → file picker. Drag-drop also
  supported.
- "Apply main cover to all books" preset for publishers who want a
  uniform jacket, "Clear all book covers" for resetting.
- Validation feedback inline; failed uploads do not mutate disk.

### π.4-C (DEFERRED) — Build-pipeline integration

The build pipeline reads `book_covers` and inserts each cover image
at its book's chapter-1 page in the built EPUB. Main cover stays as
the EPUB jacket / title page (already wired today via
`content.opf cover_image`).

Deferring this until π.4-B ships and we see real covers being
uploaded. The schema + API stand on their own — π.4-C is purely
build-side and adds no risk to the demo before then.

## Sequencing

```
π.4-A   Per-book cover model + canon-filtered API + storage     NEXT*
        ~ Pure data layer + read endpoints. No UI yet.
        ~ Schema additions are additive (book_covers absent =
          no per-book covers, builds byte-identical).
        ~ Risk: LOW   Effort: 1 turn

π.4-B   Upload backend + /covers UI                             AFTER
        ~ Multipart handling in BaseHTTPRequestHandler is new
          ground; needs careful size + safety guards.
        ~ Risk: LOW-MED   Effort: 1–2 turns

π.4-C   Build-pipeline integration (insert covers in EPUB)      LATER
        ~ Defer until publishers have actually uploaded covers
          and we know what the placement contract should be.
        ~ Risk: MED   Effort: 1 turn
```

*"NEXT" relative to the deferred queue. ν.2.7-B (popup-language UI)
remains ahead of π.4-A in the active sequence — it finishes a feature
mid-flight; π.4 starts a new one.

## Where this fits in the master plan

Inserted after ν.2.7-B in `dev/PLAN_2026-05-07.md`. Removed from the
"deferred / optional" tail of that doc (was a single-line placeholder)
and replaced with the three sub-phases above.

## Sequencing principle reminder

Per CLAUDE_PROJECT_RULES.md §3 — schema and API land before UI. UI lands
before build-pipeline integration. This means a publisher can edit
cover assignments via API before they can see a UI; and the build
pipeline ignores the new field until π.4-C wires it. Each step ships
on its own and improves the demo incrementally.
