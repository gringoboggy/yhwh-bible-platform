# INJECTOR_DUPLICATION.md

Status: **acknowledged · low-priority**

## What audit.py A6 detects

The audit's A6 check looks for duplicated logic between `inject.py`,
`promote.py`, and the editorial-workflow scripts (`add_note.py`,
`new_note.py`, `bulk_edit.py`). It finds shared patterns around:

- HTML pattern matching (anchor-finding regexes)
- NOTES list serialization (tuple → Python source)
- Strategy-A vs Strategy-B book detection
- ID-format helpers (`vnote-CODE-CH-V`, `note-XXNNNN`, etc.)

## Why we accept the duplication

Each script has a slightly different concern:

```
inject.py        marker + aside generation, embedded in HTML stream
promote.py       lift candidates → source notes, attribution-aware
add_note.py      interactive append to a single book file
new_note.py      non-interactive scaffold-only generator
bulk_edit.py     find/replace across all NOTES tuples
```

A premature shared abstraction would couple their evolution. We've
seen this before — the early `notes_io.py` extraction (β.2) was
worth it because all five tools genuinely need atomic writes and
backup behaviour. But the smaller helpers (e.g. `vnote_id(book, ch, v)`)
diverge per script:
- `inject.py` needs the ID *and* the surrounding HTML context
- `promote.py` needs the ID *and* the source-tuple shape
- `add_note.py` needs the ID *and* the user-prompt flow

A single `make_vnote_id()` helper would have to accept all three
contexts as arguments and become a god-function. Better to leave the
small patterns duplicated until they stabilize.

## When to revisit

Refactor opportunities open up if any of these become true:

```
1. A new injector script is needed (3rd full re-implementation
   would be the trigger; we have 2 today: inject.py + add_note.py)

2. Strategy-B handling expands beyond the current chapter-anchor
   fallback (e.g. supports verse-range anchors). At that point,
   centralising the strategy-detection helper pays off.

3. We drop one of the existing scripts (e.g. consolidating
   add_note.py into the web UI). That changes the caller count.
```

Until then, A6 stays as a single WARN finding and we accept it.

## How to silence it

If a future maintainer wants A6 to pass:

1. Update `audit.py` to expect `dev/INJECTOR_DUPLICATION.md` (this file)
   and treat the WARN as INFO when the file exists.
2. Or extract `scripts/core/note_serialization.py` with the genuinely
   shared parts and refactor the five callers.
3. Option 1 is the right call until evolution settles.
