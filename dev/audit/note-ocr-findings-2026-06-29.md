# Note OCR-corruption findings — device-QA round-2 cluster H-c (2026-06-29)

## What

The round-2 device QA surfaced "Eome" / "n" garbage in a Genesis study note on Kobo. The
exploration showed this is **source-data OCR corruption** (it renders identically on every
reader, not a Kobo render bug): scanned page "furniture" — a running page header + its page
number, `-- THE SEPTUAGINT. 61 10-13 Ps. 106. 27 133.` — bled into the note body during
extraction, together with single-character OCR slips ("Rome"→"Eome", dropped leading letters).

## Detector

`dev/audit_note_ocr.py` — `detect_note_ocr_noise(body)` flags the running-header + page-number
signature; `scan_notes_dir()` sweeps `content/notes/*.py`. Re-runnable; pinned by
`tests/test_audit_note_ocr.py` (incl. a **corpus-wide clean** assertion, so a future ingest
that reintroduces the class fails CI). Run: `py -3 dev/audit_note_ocr.py [--json OUT.json]`.

## The class (all three are the SAME Kenyon passage)

The source is Frederic G. Kenyon, *Our Bible and the Ancient Manuscripts* (1895, PD),
describing **Codex Vaticanus**. It was ingested at all three of the manuscript's lacuna loci,
each fragment independently OCR-garbled:

| Note | Was | Now |
|---|---|---|
| `gen` 1:1d (text-witness) | "...n Library at Eome. ... 2 Kings 2. 5-7, **-- THE SEPTUAGINT. 61 10-13 Ps. 106. 27 133.**" | "...in the Library at Rome. ... 2 Kings 2. 5-7." |
| `2ki` 2:5b (text-witness) | "**t** contains the whole Bible ... 2 Kings 2. 5-7, **-- THE SEPTUAGINT. 61 ... 6 of its original cont**" | "It contains the whole Bible ... 2 Kings 2. 5-7." |
| `psa` 106:27 (text-witness) | "...2 Kings 2. 5-7, **-- THE SEPTUAGINT. 61 ... 133. 6** of its original contents ... the ; Old Testament ... ; **bat** the Prayer of Manasses ... included in it. **The t**" | "...2 Kings 2. 5-7, of its original contents, so far as the Old Testament is concerned; but the Prayer of Manasses and the books of Maccabees were never included in it." |

**Fix policy (faith-driven no-guessing):** removed only *confirmed* OCR artifacts (the
running-header/page-number furniture, mid-word truncations like "cont"/"The t") and corrected
only *unambiguous single-character* slips ("Eome"→"Rome", "t"→"It", "bat"→"but"). No prose was
invented. Complete, readable sentences (e.g. the Prayer-of-Manasses / Maccabees clause) were
preserved.

## Residual — handed to the corpus lane (source-verification, low priority)

The **scripture-reference punctuation inside these three notes is still OCR-mangled** —
`Gen. 1. 1 46. 28 : 2 Kings 2. 5-7` should read `Gen 1:1–46:28; 2 Kings 2:5-7` (the Vaticanus
lacunae). Normalizing it correctly needs the Kenyon source page (not currently on-disk), so it
is deferred to a source-verified corpus pass rather than guessed here. If higher fidelity is
wanted, acquire Kenyon (1895) and reconstruct all three fragments against the original; the
detector + corpus-clean test guard against any *new* running-header noise meanwhile.

Golden impact: these are note-body byte changes → folded into the end-of-arc 9-KJV re-baseline.
