# Shared book title-page covers — Midjourney + gradient (Windows workflow)

**Active workflow (2026-06-16, user-directed):** original **Midjourney** scene
plates in `_scenes/_midjourney/{code}.jpg`, composed with **crimson grade +
soft vignette only** → `{code}.jpg` at 1024×1536. No Grok reimagines, no
ethnic white/black forks, no alt04/05/06 color-theme variants in the
publisher-facing product.

**Scope:** full Ethiopian canon (**86 books**). The first 66 Protestant plates
were the publisher's curated Midjourney set; the 20 Ethiopic extras were
added to match the same coherent MJ art family.

## Pipeline

```
_scenes/_midjourney/{code}.jpg  →  compose (grade + vignette)  →  {code}.jpg
```

- Manifest: `COVER_MANIFEST.yaml` (`scene_source: midjourney_first`)
- Script: `python scripts/generate_book_title_covers.py compose --variant default`
- JPEG: 1024×1536 @ q82 (~250 KB/plate)

## User-facing choices (policy — code simplification pending)

On `/covers`, publishers should see **three** choices per book, not four
built-in variants:

| Choice | Meaning |
|--------|---------|
| **Built-in** | Shared default `_book_defaults/{code}.jpg` (MJ + gradient) |
| **Your own** | Edition upload → `covers/{edition_id}/books/{code}.jpg` |
| **None** | No title-page image — text-only title page in the EPUB |

**Deprecated (do not extend):** A/B/C/D picker (`alt04/`, `alt05/`, `alt06/`),
Grok scenes in `_scenes/`, v5/v6 regen waves, ethnic `white/`/`black/` dirs.
Those artifacts may remain on disk for reference but are **not** part of the
shipping workflow.

On-disk sentinel for "none": `book_covers` entry `gen=` (empty value) — see
`scripts/core/covers.py` `decode_book_covers` docstring.

## How editions consume these

Any edition can reference paths in its `book_covers` block in
`content/editions.yaml`. Absence of a book key → factory built-in default.
Explicit empty value → no cover for that book.

The Ethiopian Tewahedo edition is the primary consumer of the full 86-set.

## Legacy / reference only

- `alt02/`, `alt03/`, `alt04/`, `alt05/`, `alt06/` — old alternate batches
- `v5_scenes.yaml` — inactive while `midjourney_first`
- `COVER_VARIANT_SELECTION.yaml` — v4 consolidate audit; not used for MJ workflow
- Publisher source folder notes (`coverage_map.md`, `PLAN.md`) — historical