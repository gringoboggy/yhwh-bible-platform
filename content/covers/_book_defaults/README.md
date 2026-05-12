# Shared book covers — publisher's curated 66-cover set

**Ingested:** 2026-05-12.
**Source:** `C:\Users\bogda\Documents\book_covers\by_book\<NN_BookName>\primary.jpg`
(the publisher's curated cover set with alt variants stored
alongside in the source folder).
**Scope:** Protestant 66-book canon. Maps cleanly to YHWH project
book codes; Ethiopic-canon extras (1en, jub, mq1-mq3, 4ba, paz,
sus, bel, man, 1es, 2es, tob, jdt, wis, bar, lje, sir, aes) are
not yet covered.

## Inventory

```
gen.jpg   exo.jpg   lev.jpg   num.jpg   deu.jpg
jos.jpg   jdg.jpg   rut.jpg
1sa.jpg   2sa.jpg   1ki.jpg   2ki.jpg   1ch.jpg   2ch.jpg
ezr.jpg   neh.jpg   est.jpg
job.jpg   psa.jpg   pro.jpg   ecc.jpg   sng.jpg
isa.jpg   jer.jpg   lam.jpg   eze.jpg   dan.jpg
hos.jpg   joe.jpg   amo.jpg   oba.jpg   jon.jpg   mic.jpg
nah.jpg   hab.jpg   zep.jpg   hag.jpg   zec.jpg   mal.jpg
mat.jpg   mrk.jpg   luk.jpg   jhn.jpg   act.jpg
rom.jpg   1co.jpg   2co.jpg   gal.jpg   eph.jpg   phi.jpg
col.jpg   1th.jpg   2th.jpg   1ti.jpg   2ti.jpg   tit.jpg
phm.jpg   heb.jpg   jam.jpg
1pe.jpg   2pe.jpg
1jn.jpg   2jn.jpg   3jn.jpg
jud.jpg   rev.jpg
```

Total: 66 files.

## How editions consume these

This directory is a **shared cover inventory** — any edition can
reference these paths in its `book_covers` block in
`content/editions.yaml`. The `scripts/core/covers.py` docstring
explicitly anticipates this: "paths can point anywhere under
`content/` to keep the door open for shared covers across editions."

The Ethiopian Tewahedo edition (`ethiopian-tewahedo`) is the first
edition to consume the shared set — its `book_covers` block in
editions.yaml points at every cover in this directory (the 66 books
it shares with the Protestant canon; the Ethiopic-canon extras have
no covers yet).

To add covers to another edition, append a `book_covers:` block to
that edition's entry in `editions.yaml`:

```yaml
    book_covers:
      - "gen=covers/_book_defaults/gen.jpg"
      - "exo=covers/_book_defaults/exo.jpg"
      ...
```

Or use the `/covers` console's per-edition upload UI to override
specific books with edition-specific art.

## Source folder structure

The publisher's source folder also contains:

- `by_book/<NN_BookName>/alt_01.jpg` + `alt_02.jpg` — alternates
  for the primary. Available for swap if a primary doesn't suit
  a specific edition.
- `all_sorted/` — original numbered render set (`00`–`51+`) before
  per-book curation.
- `coverage_map.md` — the publisher's audit notes documenting which
  image went where + the v3 cross-contamination fix.
- `PLAN.md` — the publisher-side planning doc.

## Forward direction

- **Ethiopic-canon extras**: the 21 books in the Tewahedo canon
  not in the Protestant 66 (1en, jub, mq1-mq3, 4ba, paz, sus,
  bel, man, 1es, 2es, tob, jdt, wis, bar, lje, sir, aes, etc.)
  need their own covers. Either commission per-book art or
  reuse thematic alternates from `all_sorted/`.
- **Per-edition overrides**: the catholic-study / coptic-orthodox
  / evangelical-reformed editions have different aesthetic
  voices; some books may benefit from edition-specific covers.
  Use the /covers console upload UI for per-book override.
