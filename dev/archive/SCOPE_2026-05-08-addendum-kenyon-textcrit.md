# Scope addendum — χ.0 Kenyon textual-criticism ingest

**Added:** 2026-05-08, after ψ.8 cluster shipped (the v1.0 differentiator
is now feature-complete). First χ-cluster phase since χ.1 Strong's
Greek shipped earlier in this session; first one fed by **local
public-domain text** rather than a network fetch.

## Origin

The user's `C:\Users\bogda\Documents\oldfindings.pdf` (16.7 MB) is the
full OCR'd text of **Frederic G. Kenyon's *Our Bible and the Ancient
Manuscripts* (1895)** — 18,394 lines / ~775 KB / ~390 pages, scanned
from Princeton Theological Seminary's library copy. Author died 1952;
first published 1895 (pre-1929 US PD cutoff). Public-domain worldwide.

A companion brief `Mesha.pdf` (4.2 MB, 11 pages, image-only PDF)
catalogues the structure and recommends six project applications.
The brief itself is not directly ingestible (no text layer), but its
recommendations informed this scope.

## Why this is its own χ-phase, not a τ translation phase

Kenyon's content is **textual criticism prose**, not Bible verse
content. It belongs in the corpus as a new note **kind** (`text-witness`
under the existing `text` category), tagged `tradition=cross` (the
denominationally-neutral bucket — manuscript history is shared across
all five seeded editions). Each promoted note attaches to the verse
its surrounding paragraph cites.

Other text-* kinds already exist (`text-dss`, `text-lxx`,
`text-samaritan`, `text-ethiopic`, `text-conjecture`). Kenyon's prose
covers all of these AND general manuscript-witness commentary that
none of them cleanly own. Rather than try to classify each Kenyon
paragraph into one of the existing kinds, this phase introduces one
new kind (`text-witness`) that captures "textual-critical commentary
from a manuscript-history perspective". Future fine-grained re-
classification can run as a separate retag pass.

## Realistic corpus delta

A regex pre-scan of `oldfindings.txt` finds **~70 precise verse
references** (book + chapter + verse). After OCR-noise filtering,
deduplication on (book, chapter, verse), and dropping references that
don't resolve to a known canonical book code, the realistic promotable
yield is **~50-100 notes**.

This is a smaller delta than χ.6 (+6,127 TSK) or χ.6+ HebrewWord
(+8,412), but it ships:

- A new `text-witness` kind exercised through the full pipeline
- Kenyon attribution in `content/sources/ATTRIBUTIONS.md`
- A reusable `KenyonReferenceDetector` pattern for future
  textual-criticism ingests (Bruce Metzger's *The Text of the New
  Testament*, Würthwein's *The Text of the Old Testament*, etc., once
  PD copies surface)
- A proof that prose-style sources can feed the χ-cluster pipeline

## Pipeline shape (mirrors the §9 χ-cluster pattern)

```
content/sources/kenyon_textcrit.txt   →   KenyonReferenceDetector       →   candidates JSON         →   Promoted notes
(staged from                              (scripts/core/detectors.py)      (content/candidates/        (content/notes/<book>.py)
 oldfindings.txt)                                                           <book>_ch_<NNN>.json)       text-witness, tradition=cross
```

## Implementation steps

1. **Stage source.** Copy `C:\Users\bogda\Documents\oldfindings.txt`
   into `content/sources/kenyon_textcrit.txt`. Update
   `content/sources/ATTRIBUTIONS.md` with the Kenyon 1895 entry.

2. **Add the `text-witness` kind.** New entry in `content/kinds.yaml`:
   - `code: text-witness`
   - `category: text`
   - `symbol: ✧` (inherits)
   - `note_class: note-text-witness`
   - `marker_class: marker-text-witness`
   - `label: Witness`
   - `title_attr: Manuscript-witness commentary`
   - `description: Textual-critical commentary on manuscript / version
     witnesses to a verse, drawn from PD textual-criticism literature.`
   - `phase: mvp`

3. **Source loader.** New `KenyonText` dataclass and singleton in
   `scripts/core/sources.py`. Reads `content/sources/kenyon_textcrit.txt`,
   exposes the full text + a list of verse-reference matches. Cached
   via the existing `lru_cache` pattern.

4. **Detector class.** `KenyonReferenceDetector` in
   `scripts/core/detectors.py`. Mirrors `CrossRefDetector`'s shape (no
   verse-text dependency). Walks the source text once, regex-matches
   verse references (`[1-3]?\s?[A-Z][a-z]+\.\s*\d+\.\s*\d+`), maps
   the abbreviated book name to the project's canonical book code,
   captures a 200-300 char window around each match as the note body,
   and emits one `Candidate` per match (deduped on (book, ch, vs,
   normalized-context-hash)). Emits as kind=`text-witness`,
   tradition=`cross`. Skips matches that don't resolve to a known
   book code.

5. **Driver.** `scripts/run_kenyon_at_scale.py` modeled on
   `run_xref_at_scale.py`. Iterates the source text once, invokes
   the detector, writes candidate JSON files in prospect's exact
   format. The `--books` flag scopes a smoke run to e.g. just `mat`.
   Idempotent on re-run.

6. **Smoke + batch promote.** Run on `--books gen mat` first, inspect
   sample candidate JSON, then full corpus. Promote with
   `python3 scripts/batch_promote_xrefs.py --kind text-witness`
   (the existing batch promoter already supports kind filtering).

7. **Verify.** `pytest` passes; `lint_rules.py` passes; attribution
   audit shows the Kenyon-attributed notes.

8. **CHANGELOG entry** with cumulative corpus math.

## Tests

Per the §9 χ-cluster pattern:

- **Detector unit tests** with synthetic fixtures (no I/O):
  - Verse reference parsing: simple, compound book ("1 Sam."), ranges,
    comma-lists, OCR artifacts.
  - Book-name → code mapping: standard abbreviations + full names +
    unknown rejected.
  - Context-window extraction: ~300 char window, paragraph-respecting
    boundaries, escape HTML metacharacters.
  - Dedup on (book, ch, vs, context-hash).
  - Tradition tag is `cross` (denominationally neutral).
  - Kind code is `text-witness`.
- **Driver smoke** (against staged fixture text, not the full Kenyon):
  - Writes candidate JSON in prospect's format.
  - `--books` filter scopes correctly.
  - Idempotent: re-running produces a superset of candidates.

## Tradeoffs / known limits

- **OCR noise.** Kenyon's text was OCR'd from a 1914-stamped library
  scan; some OCR artifacts (`j4-`, `Massoretic`-vs-`Massuretic`, etc.)
  will show up. The detector tolerates this defensively — unknown
  book codes silently skip, malformed numbers silently skip.
- **Yield is modest by design.** ~50-150 notes is small compared to
  the χ.6 / χ.6+ ingests. Justified by zero cost and the value of
  exercising a new content kind. Future textual-criticism phases
  (Metzger, Würthwein) will reuse the `text-witness` kind +
  detector pattern.
- **Per-verse only, not per-section.** Kenyon's chapter-level
  discussions of e.g. the Vulgate or the Curetonian Syriac don't have
  per-verse anchors. Those become readable as a separate
  `/textual-criticism` console (deferred — not in this phase) rather
  than per-verse notes.
- **English-only OCR.** Greek / Hebrew / Latin tokens in Kenyon are
  rendered as Latin transliterations or garbled OCR; we don't try
  to recover the originals. The note body is English prose with
  references to scripts, not the scripts themselves.

## v1.0 inclusion

χ.0 is **not** in the v1.0 terminus per memory `project_v1_terminus.md`
(which lists θ.2 + χ.1 + ψ.8 + ψ.10/12/13/14/17 + ω.8/9/10 + ξ.1/2/4
+ corpus ≥ 25K). It contributes to "corpus ≥ 25K" but is one of
several potential corpus paths. Ships now because:

- It's free (no API cost)
- Local source already on disk
- Proves the new content kind before the next textual-criticism
  ingest piles work on top of it
- 1-session scope

The bigger v1.0 corpus closures remain χ-AI-xrefs (~+5-15K, paid)
plus the user-side `fetch_sources.py` unblock (~+7-13K, free) for
χ.7 Nave's Topical and χ.1 Strong's Greek (both already
infrastructure-shipped earlier this session).
