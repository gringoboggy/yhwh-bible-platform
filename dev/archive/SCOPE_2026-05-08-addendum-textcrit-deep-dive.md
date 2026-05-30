# Scope addendum — χ.0+ deep dive (extended PD textual-criticism)

**Added:** 2026-05-08, after χ-AI-xrefs infrastructure shipped. User
flagged the desire to expand the textual-criticism corpus beyond
χ.0's single Kenyon volume, drawing more PD textual-criticism
literature into the `text-witness` kind. Per the χ.0 spec
("future textual-criticism phases will reuse the `text-witness`
kind + detector pattern"), the infrastructure already generalizes;
this addendum stages the next 3-4 ingest sub-phases.

## Why this is its own addendum

χ.0 shipped exactly one source (Kenyon 1895). The user has confirmed
intent to deepen the textual-criticism layer. Each next source is
~1 session of work that mirrors χ.0 exactly — stage PDF + OCR →
register source loader → register detector subclass (or reuse
`KenyonReferenceDetector` directly) → driver → batch promote. The
spec block here keeps the per-source ordering, source-availability
notes, and book-name maps in one place rather than splattering across
the CHANGELOG.

## Source candidates (PD, archive.org-accessible)

All sources below are pre-1929 (US public-domain by date), or have
been verified as PD worldwide. Archive.org is the primary lookup
(user has an archive.org account per memory `reference_external_tools.md`).

```
χ.0.1  Westcott & Hort 1881           ~ 1 session · LOW
       *The New Testament in the Original Greek* — Volume II:
       Introduction & Appendix. ~600 pp of pure NT textual-
       criticism prose by the architects of the modern critical
       text. Vol. II *Introduction* is the densest English textual-
       criticism text in the PD canon.
       Source: archive.org/details/newtestamentinor02wescuoft
       Author died 1892 (Hort) / 1901 (Westcott). PD worldwide.
       Realistic yield: ~150-300 verse-anchored notes; covers
       NT broadly with deep coverage in Mark and the Pauline epistles.
       Edition synergy: every Christian edition; particularly
       valuable for Reformed/academic editions.

χ.0.2  Burgon 1883                    ~ 1 session · LOW
       *The Revision Revised* — F.G. Burgon's 600-page
       counter-W&H polemic. Defends the Byzantine / Textus
       Receptus tradition. Worth ingesting alongside χ.0.1
       so the corpus represents both sides of the 1881-1900
       textual debate (the publisher / reviewer can pick which
       view to surface per-edition via traditions tags).
       Source: archive.org/details/revisionrevised00burguoft
       Author died 1888. PD worldwide.
       Realistic yield: ~100-200 notes; concentrated in NT.
       Edition synergy: KJV-Only / Traditional / Anglican editions
       (where the Byzantine text is the publisher's preferred line).

χ.0.3  Souter 1913                    ~ 1 session · LOW
       *The Text and Canon of the New Testament* — A.S. Souter's
       compact handbook. Shorter than W&H or Burgon (~250 pp);
       broader-coverage and more textbook-style. Good complement
       because the verse references are more evenly distributed
       across the NT than W&H (which front-loads Mark + Pauline).
       Source: archive.org/details/textcanonofnewte00soutuoft
       Author died 1949 — but published 1913 in the US (PD by date).
       Realistic yield: ~75-150 notes; even NT distribution.

χ.0.4  Driver 1890                    ~ 1 session · LOW-MED
       *Notes on the Hebrew Text and the Topography of the
       Books of Samuel* — S.R. Driver's verse-by-verse Hebrew
       textual notes. The OT counterpart to W&H's NT focus —
       fills the otherwise-thin OT side of the `text-witness`
       coverage (Kenyon is OT-light; W&H/Burgon/Souter are NT-only).
       Source: archive.org/details/notesonhebrewte00drivgoog
       Author died 1914. PD worldwide.
       Realistic yield: ~200-400 notes; deep coverage of 1-2 Samuel,
       lighter for the rest of OT.
       Risk MEDIUM: heavy use of inline Hebrew script in the OCR;
       may need a regex-tolerance pass beyond what χ.0's
       `_clean_kenyon_context()` already does.
       Edition synergy: any OT-heavy edition; especially the
       Jewish Study Bible primary.
```

## Optional later candidates (parked, lower priority)

```
χ.0.5  Robertson 1925                 ~ 1 session · LOW
       *An Introduction to the Textual Criticism of the New
       Testament*. Just inside US PD by date (pre-1929 cutoff).
       Successor to Souter, slightly broader. Ship if χ.0.1-χ.0.4
       reveal NT coverage gaps.

χ.0.6  Tregelles 1854                 ~ 1 session · LOW
       *An Account of the Printed Text of the Greek New Testament*.
       Pre-W&H critical history — useful for the historical-
       awareness layer but verse density is lower (more about
       editorial decisions than per-verse readings).

χ.0.7  Tischendorf 1866 (English)     ~ 1 session · LOW
       *When Were Our Gospels Written?* English translation of
       Tischendorf's defense of the Sinaiticus discovery. NT-focused;
       lighter on per-verse analysis, heavier on manuscript-history
       narrative. Useful but lower per-verse-note yield than the
       above.
```

## Implementation pattern (unchanged from χ.0)

Each sub-phase is a 1-session ingest:

1. **Stage PDF** from archive.org → user runs `pdftotext` → text file
   lands at `content/sources/<id>_textcrit.txt`. Update
   `content/sources/ATTRIBUTIONS.md`.
2. **Register source loader** in `scripts/core/sources.py`. Two
   options:
   - **Subclass-per-source** (mirror `KenyonText`): one loader class
     + one `<src>_text()` singleton per author. Best when the
     citation format differs significantly (e.g. footnote-style
     citations vs inline-prose citations).
   - **Generic loader** (`PdTextcritText` accepting a path + a
     book-name map): one loader serves all sources whose citation
     format is "BookName Chapter. Verse" or "BookName Chapter:Verse"
     (the χ.0 KENYON regex shape). Cleaner; ship if the first 2-3
     candidates all match the regex.
   The decision is made when the second source ships — not now.
3. **Register detector** in `scripts/core/detectors.py`. Same kind
   (`text-witness`), same body shape, same OCR-cleanup pass. The
   detector class either subclasses `KenyonReferenceDetector`
   (overriding the `_build_index` source) or composes with a
   pluggable index builder.
4. **Driver script** `scripts/run_<src>_at_scale.py`. Mirror of
   `run_kenyon_at_scale.py`. Merge-not-clobber against existing
   chapter files (TSK, Hebrew, Greek, Nave, Kenyon, AI-xref +
   prior textual-criticism sources all coexist).
5. **Smoke + batch promote**: `--books mat,1sa` first; full corpus
   second. `python3 scripts/batch_promote_xrefs.py --kind
   text-witness` promotes (the existing batch promoter already
   filters by kind).
6. **Verify + CHANGELOG entry** per the standard ship loop.

## Design decision parked: "merge into one χ.0.1 omnibus or
ship per-source?"

Two options for χ.0.1 onward:

- **Omnibus χ.0.1**: one phase ingests all 4 candidate sources.
  Faster total throughput; less per-source overhead in detectors.py;
  one CHANGELOG entry for the whole pass.
- **Per-source χ.0.1, χ.0.2, χ.0.3, χ.0.4**: each ships independently,
  with its own driver + tests + smoke run. Slower throughput but
  each ship has a clean rollback point and the per-source detector
  can be tuned for the specific OCR quirks of that scan.

**Default: per-source.** Mirrors the χ.7 / χ.1 / χ.0 pattern of one
ship per source. The user's "deep dive" framing implies depth-over-
speed; per-source ships allow the reviewer to look at the candidate
JSON between sources and tune confidence floors / max-per-verse caps
for the next pass. Switch to omnibus only if χ.0.1 + χ.0.2 reveal
the per-source overhead is excessive (e.g. 80% code reuse across
sources).

## Cumulative corpus delta (estimate)

Conservative reviewer-promote yields per source (after typical 30-50%
rejection at the promote-CLI stage):

```
χ.0.1 W&H 1881         ~ 100-200 notes (NT-heavy)
χ.0.2 Burgon 1883      ~ 60-120 notes  (NT-heavy)
χ.0.3 Souter 1913      ~ 50-100 notes  (NT, even distribution)
χ.0.4 Driver 1890      ~ 150-300 notes (1-2 Sam deep, OT-broad light)
                       ─────────────────────
Total:                  ~ 360-720 notes  (~ +1-2K notes after
                                          aggressive batch promote)
```

This is a smaller delta than χ-AI-xrefs (~5-15K) or χ.6 (+6K) but
each note is a high-quality, source-attributed manuscript-witness
note from a recognized textual-criticism authority. The corpus
gains depth (multiple authors per verse where they overlap; multiple
manuscript traditions discussed) rather than breadth.

## Tradeoffs / known limits

- **OCR quality varies.** archive.org PDFs are scanned at varying
  qualities. W&H Vol II is well-scanned (Toronto's copy);
  Burgon's *Revision Revised* has multiple available scans of
  varying quality. `pdftotext` output should be smoke-tested before
  full extraction.
- **Hebrew/Greek inline tokens** in W&H, Driver, Souter render as
  garbled OCR. χ.0's `_clean_kenyon_context()` strips only the
  loudest artifacts (carets, backslashes, repeated punctuation);
  inline Hebrew/Greek may need an additional cleanup pass for
  Driver specifically. Defer until χ.0.4 ships.
- **Citation density varies wildly.** W&H Introduction Volume II
  averages ~1 verse citation per page; Burgon averages ~3-4 per
  page (denser polemic style); Souter is closer to Kenyon's density.
  The driver's existing `--max-per-verse` cap handles this.
- **Cross-source duplicates are expected.** Multiple authors
  discussing the same Codex Alexandrinus reading at the same verse
  will produce multiple candidates. The promote.py dedup is on
  exact body match — different attributions + reasoning keep them
  distinct. The reviewer at promote time decides whether to keep
  one or all.

## v1.0 inclusion

**Not in the v1.0 terminus** per memory `project_v1_terminus.md`.
The textual-criticism corpus is a v1.x quality multiplier — it
sharpens the `text-witness` apparatus that χ.0 introduced but does
not gate the v1.0 candidate. Slot it in **after** v1.0 ships, or
pull individual sub-phases forward if a buyer ask demands deeper
manuscript-history coverage (e.g. an academic publisher).

The pre-v1.0 corpus path remains: χ-AI-xrefs (paid, user-side, +5-15K)
+ χ.7 Nave's user-side completion (+2-3K) + χ.1 Greek user-side
completion (+5-10K) → ω.5 → θ.1 → θ.2 → v1.0 candidate.
