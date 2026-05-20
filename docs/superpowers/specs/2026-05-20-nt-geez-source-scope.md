# NT Ge'ez source scope — Track E research spec (multi-track sweep 2026-05-20)

**Status:** SCOPING / RESEARCH. Sibling to
`docs/superpowers/specs/2026-05-20-patrologia-ingest-design.md`. No code or
data changes from this spec — produces verdict + recommended phase tag
only.

**Goal:** Identify and document the source for NT Ge'ez ingest into
`content/translations/geez-tewahedo/` (currently 16 OT-only books — zero
of the 27 NT books).

## 1. Source verdict

**SOURCE IDENTIFIED — Class: parallel-PDF (parallel-bible-eotc).**

The publisher-supplied `Bible_Amharic_and_Geez.pdf` (2,539 pages)
contains a complete EOTC Ge'ez + Amharic parallel NT block running
roughly **p1567 to p2106** — 540 pages immediately after the OT pseudepigrapha
(Jubilees ends p1514, 1 Enoch ends p1566, the τ.7.x.t/u Π.1-mapped
blocks). Confirmed by direct PDF inspection (PyMuPDF; `doc.get_toc()`
returns 0 TOC entries — the publisher PDF has no bookmark hierarchy, so
boundaries were derived by header-text scan).

This is the **same source class** the OT side is already shipping out of
(`scripts/extract_parallel_pdf.py` at τ.7.x.* per-book cadence). The NT
side uses the identical column layout (Ge'ez left / Amharic right) and
identical OCR pipeline (Tesseract `script/Ethiopic` + `amh` at 350 dpi).

### Why not the alternative classes?

- **Patrologia Orientalis (GAPS/):** All four GAPS Patrologia volumes
  are OT-only (Chronicles, Ezra-Nehemiah, Esther, Job per
  `GAPS/SOURCES.md` + `GAPS/README.md`). No NT Patrologia volume is
  present in `GAPS/` or referenced anywhere in the in-repo source maps.
- **Manuscript image facsimiles:** The GG 00106 + Cambridge MS Add. 1570
  manuscripts cropped under `GAPS/1_Samuel/` and `GAPS/2_Kings/` cover
  Samuel + Kings only. No NT manuscript folios in-repo.
- **letter-to-laodiceans (lao):** Already wired via Lightfoot 1875 /
  M.R. James 1924 — but this slot is a single 20-verse pseudo-Pauline
  epistle in the EOTC broader canon, NOT a source for any of the 27
  standard NT books.

## 2. Coverage estimate — 26 of 27 NT books reachable

Empirical page boundaries from a full header scan of pp1567-2106:

| Book | Code | PDF pages | Page count | Notes |
|---|---|---|---|---|
| Matthew | mat | 1567-1635 | 69 | Already wired as τ.7.x.v (floor + structural_map; not yet rendered) |
| Mark | mrk | 1636-1677 | 42 | Header `ወንጌል ዘማርቆስ` |
| Luke | luk | 1678-1753 | 76 | Header `ወንጌል ዘሉቃስ` |
| John | jhn | 1754-1809 | 56 | Header `ወንጌል ዘዮሐንስ` |
| Acts | act | 1810-1883 | 74 | Header `ግብረ ሐዋርያት` |
| Romans | rom | 1884-1914 | 31 | Header `ኀበ ሰብአ ሮሜ` |
| 1+2 Corinthians | 1co + 2co | 1915-1961 | 47 | Headers `ኀበ ሰብአ ቆሮንቶስ` (combined block; needs within-section split similar to meqabyan trilogy) |
| Galatians | gal | 1962-1970 | 9 | Header `ኀበ ሰብአ ገላትያ` |
| Ephesians | eph | 1971-1981 | 11 | Header `ኀበ ሰብአ ኤፌሶን` |
| Philippians | phi | 1982-1994 | 13 | Header `ኀበ ሰብአ ፊልጵስዩስ` |
| 1+2 Thessalonians | 1th + 2th | 1995-2005 | 11 | Headers `ኀበ ሰብአ ተሰሎንቄ` (combined block) |
| 1+2 Timothy | 1ti + 2ti | 2006-2018 | 13 | Headers `ኀበ ጢሞቴዎስ` (combined block) |
| Titus | tit | 2019-2022 | 4 | Header `ኀበ ቲቶ` |
| Philemon | phm | 2023-2024 | 2 | Header `ኀበ ፊልሞና` |
| Hebrews | heb | 2025-2044 | 20 | Header `ኀበ ሰብክ ዕብራውያን` |
| 1+2 Peter | 1pe + 2pe | 2045-2057 | 13 | Headers `መልእክተ ጴጥሮስ` (combined block) |
| 1-3 John | 1jn + 2jn + 3jn | 2058-2065 | 8 | Headers `መልእክተ ዮሐንስ` (three-book combined block) |
| James | jam | 2066-2072 | 7 | Header `መልእክተ ያዕቆብ ሐዋርያ` |
| Jude | jud | 2073-2075 | 3 | Header `መልእክት ይሁዳ` |
| Revelation | rev | 2076-2106 | 31 | Header `ራእዩ ለዮሐንስ`; p2107 opens `መጽሐፈ ዲድስቅልያ` (Didascalia — post-NT) |

**Total: 540 PDF pages covering 26 of the 27 standard NT books.**

EOTC NT ordering observed in the PDF: Gospels → Acts → Pauline → Catholic
(after Pauline-Hebrews) → Revelation. Note: Hebrews sits in the Pauline
block per the EOTC tradition (between Philemon and Peter).

### The Colossians gap

**`col` (Colossians) was NOT found in the parallel-PDF.** A full
header scan of pp1567-2106 + a multi-spelling targeted search
(`ቆላስ`, `ቆልሳ`, `ቄላስ`, `ቈላስ`, `ኮላሣ`, `ኮላሰ`, etc.) yielded only false
positives inside cross-references in Luke / Acts / Titus. The
Philippians block (p1982-1994) is directly followed by the Thessalonians
opener at p1995. No standalone Colossians title page or running header
appears in the PDF.

This is the same pattern the `laodiceans` slot already documents:
declared in `books.yaml` (`col`, b71) but `present_in_pdf: False` in the
parallel-bible-eotc structural map. **Treatment: declare `colossians`
as a present_in_pdf:false slot in the structural_map (alongside
`susanna` + `laodiceans`); ingest deferred to a future
τ.6.x.NT.gap-fill / δ.x.col-alternate-source ship.**

Possible alternate sources for the Colossians gap (research only — not
in this spec's scope):

- Hänssler Verlag / Curt von Stosch (1980s-era EOTC Geʽez NT print)
- BSE (Bible Society of Ethiopia) Geʽez NT, if available as a digital
  scan
- A manuscript witness (Cambridge / EMML / Gunda Gundē catalogues — none
  currently in-repo)

## 3. Recommended starting book — Philemon (`phm`)

Philemon at pp2023-2024 is the smallest, simplest NT book reachable from
the source. Reasons:

- **Only 2 PDF pages** — the shortest single-book block in the entire NT
  region.
- **25 verses, 1 chapter** — matches the project's preferred "smallest
  smoke-test" cadence (Ruth at τ.7.x.h was 4 ch / 85 v / 6 pages; phm
  is the NT equivalent at smaller scale).
- **Single-book block** — unlike 1-2 Corinthians, 1-3 John, etc., the
  Philemon block needs NO within-section book-boundary splitter.
- **Header clearly resolvable** — `ኀበ ፊልሞና` matches the established
  `ኀበ ሰብአ <toponym>` Pauline-letter header pattern.
- **NT-standardized versification** — KJV/UBS-NA enumeration is the
  canonical CEILING for the renumber floor (per the τ.7.x.v Matthew
  methodology note: NT versification is highly standardized, so no
  γ-notes cross-validation is needed).

Comparison: 3 John (15 v) or 2 John (13 v) have FEWER verses BUT they
live in the combined `መልእክተ ዮሐንስ` 1-3 John block (pp2058-2065). That
block needs a within-section splitter before any of the three Johannine
letters can ship cleanly — the same problem as the Meqabyan trilogy at
τ.7.x.n. Philemon at p2023-2024 has no such complication.

## 4. Required pipeline work

The Track E ingest opens by **extending `extract_parallel_pdf.py`** — no
new tool is needed. The script already has the Tesseract + paragraph-mode
+ renumber-floor + multi-language column-extraction infrastructure;
Matthew was wired at τ.7.x.v as the first NT entry. Required additions:

### 4a. New `--renumber` choices

Add 26 NT book codes to the `--renumber` CLI argparse choices list (in
order encountered): `mark`, `luke`, `john`, `acts`, `romans`,
`first_corinthians`, `second_corinthians`, `galatians`, `ephesians`,
`philippians`, `first_thessalonians`, `second_thessalonians`,
`first_timothy`, `second_timothy`, `titus`, `philemon`, `hebrews`,
`james`, `first_peter`, `second_peter`, `first_john`, `second_john`,
`third_john`, `jude`, `revelation`. (Colossians excluded per §2; matthew
already shipped at τ.7.x.v.)

For Philemon specifically (the smoke-test book): one new floor dict
`PHILEMON_VERSE_COUNTS = {1: 25}` (KJV/UBS-NA enumeration).

### 4b. New BOOK_VERSE_COUNTS dicts

26 new per-chapter verse-count dicts, all using KJV/UBS-NA enumeration
per the τ.7.x.v methodology note (NT versification is standardized; no
γ-notes cross-validation). Approximate scale:

- Single-chapter books (`phm`, `2jn`, `3jn`, `jud`): trivial dicts.
- Short Catholic-Epistles (`jam`, `1pe`, `2pe`, `1jn`): 3-5 ch each.
- Gospels (`mat` already done; `mrk` 16 ch / `luk` 24 ch / `jhn` 21 ch).
- Acts (28 ch), Pauline (varies), Hebrews (13 ch), Revelation (22 ch).

### 4c. New `structural_map` entries in `_source.yaml`

26 new entries paralleling the existing `matthew: [1567, 1635]` shape.
For combined-block books (1-2 Cor, 1-2 Thes, 1-2 Tim, 1-2 Pet, 1-3 Jn),
add `subsections` maps similar to the meqabyan trilogy's hoisted
subsections (the τ.7.x.n declarative shape). For Colossians, declare
`present_in_pdf: false` per the `laodiceans` precedent.

### 4d. Within-section splitters

5 combined blocks need within-section splitting before per-book ship:

- 1-2 Corinthians (p1915-1961, ~47 pages)
- 1-2 Thessalonians (p1995-2005, ~11 pages)
- 1-2 Timothy (p2006-2018, ~13 pages)
- 1-2 Peter (p2045-2057, ~13 pages)
- 1-3 John (p2058-2065, ~8 pages)

The meqabyan-trilogy precedent (τ.7.x.n) used hand-derived
`subsections` page-ranges in `_source.yaml`. For Pauline pairs, the
within-block split is typically clean (a single `መልእክተ X ፪` running
header at the top of one page marks the second-letter boundary).
The 1-3 John block needs three sub-ranges (1jn p2058-2061, 2jn
p2062-2064, 3jn p2065 — derived from the header scan).

### 4e. NT-aware parser tolerance

The existing `extract_parallel_pdf.py` ALREADY has the τ.6.x.1.E NT
pericope/section-header rejection logic (`is_pericope_header`,
`PERICOPE_HEADER_RE`) and the τ.7.x.v "NT-overflow" guard in
`renumber_against_floor()` that raises ValueError on gross
over-segmentation. These were built for the Matthew floor and should
work for the rest of the NT without modification. Per-book verification
during ship will confirm.

### 4f. No new tool needed

Unlike Track P (Patrologia → new `extract_patrologia_pdf.py` for the
French-column layout), Track E reuses `extract_parallel_pdf.py`
unchanged at the engine layer — only the data tables + structural map
expand.

## 5. Risks / known issues

- **OCR quality variance:** The NT side of the parallel-PDF is the same
  OCR-tier3 source as the OT side. Expect identical `script/Ethiopic`
  recognition rates, identical `።`-terminator paragraph-mode parsing,
  identical `ምዕራፍ` chapter-marker garbling (the τ.6.x.1.D recovery
  pattern). No reason to expect NT quality to be lower than OT quality;
  the publisher used one OCR pipeline across the whole PDF.

- **The τ.7.x.v "NT-overflow" residual:** Matthew floor + structural_map
  shipped at τ.7.x.v, but `geez-tewahedo/mat.py` is NOT yet present —
  per the `extract_parallel_pdf.py` τ.6.x.1.E + τ.7.x.v comments + the
  `renumber_against_floor()` gross-overflow guard, an earlier ingest
  attempt hit the OT-narrative-tuned `።`/paragraph parser's structural
  mismatch against NT pericope/cross-ref apparatus. The fix (τ.6.x.1.E
  pericope-header rejection + `ክፍል N፡` filtering) is wired but not yet
  verified end-to-end on Matthew. **Track E ship is gated on Matthew
  end-to-end smoke success first** — Philemon at p2023-2024 is the
  recommended SECOND smoke (smallest NT block) after Matthew renders
  cleanly. If Matthew still fails to render, the τ.6.x.1.E mitigation
  needs further work before any NT book ships.

- **Header OCR garble of book-numeral suffix:** In combined-block books
  (e.g. `መልእክተ ጴጥሮስ ፪` for 2 Peter), the trailing Ethiopic numeral is
  often OCR-garbled to `8`, `B`, `፪*`, `፳`, etc. The within-section
  splitter must tolerate these — the τ.6.x.1.D `_resolve_chapter_marker`
  pattern (Geʽez-numeral → Arabic-digit fallback → sequential fallback)
  is the right base; an analogous helper for book-numeral resolution
  may be needed.

- **Colossians gap:** Documented in §2. Tracking forward as a
  present_in_pdf:false slot pending alternate-source acquisition.
  Track E does NOT block on this — 26 of 27 NT books ship from the
  parallel-PDF; col is a separate δ.x ship.

- **EOTC ordering vs Western ordering:** The PDF places Hebrews inside
  the Pauline block (between Philemon and Peter), reflecting the EOTC
  tradition that treats Hebrews as Pauline. Book-code preservation
  (`heb` at PDF p2025-2044) is fine — the book code is canon-independent;
  only the structural_map ordering needs to match the empirical PDF
  layout.

- **Mt + Jam + Jud cross-reference false-positive density:** During the
  header scan, the strings `ያዕቆብ` (James) and `ይሁዳ` (Jude/Judah) appear
  inside Matthew's chapter 1 genealogy (the OT-patriarch tribe names);
  the broad full-page search registered Mt as Jam/Jud false positives
  at p1567. The narrow first-line-of-running-header scan (the §2 table)
  filters these correctly — the per-book splitter must use the same
  narrow header scan, NOT a full-page substring match.

- **Combined-block sizing:** The 1-2 Corinthians block is 47 pages
  total (vs the meqabyan trilogy's 61 pages over 3 books). Splitting at
  the running header `ኀበ ሰብአ ቆሮንቶስ ፪` (with OCR-garbled numeral
  tolerance) is the standard within-section approach. No new design
  pattern needed.

## 6. Proposed phase tag — `τ.6.x.NT.a`

Aligns with the existing τ.6.x.* per-book cadence used for the
parallel-Bible-EOTC ingest stream (where `τ.6.x.0/1/2/3/4/5` arc-roots
correspond to OCR-strategy → engine-wiring → bulk-ingest → audit →
manuscript-collation → Patrologia respectively). The NT block is the
NEXT major arc opener after the τ.7.x.* OT-stream completion; using
`τ.6.x.NT.a` (instead of e.g. `τ.7.x.w` continuing the OT lettering)
visually marks the NT arc as a distinct workstream while keeping the
τ.6.x.* root.

Sub-phase recommendation:

- **`τ.6.x.NT.a` — pipeline extension + Philemon smoke ship**
  (single-chapter, 25-v, 2-page; verifies the τ.6.x.1.E + τ.7.x.v
  pericope/overflow guards on real NT data). May be preceded by a
  Matthew re-attempt as a Mt-verification ship.

- **`τ.6.x.NT.b` — Pauline single-block books (gal, eph, phi, tit,
  phm-already, heb)**

- **`τ.6.x.NT.c` — Pauline combined-block books (1-2 Cor, 1-2 Thes,
  1-2 Tim)** — within-section splitter ship

- **`τ.6.x.NT.d` — Catholic Epistles (jam, 1-2 Pet, 1-3 John, jud)**
  — second within-section-splitter ship

- **`τ.6.x.NT.e` — Gospels (mat-redo if needed, mrk, luk, jhn)**

- **`τ.6.x.NT.f` — Acts + Revelation** (largest single-block NT books)

- **`τ.6.x.NT.g` — Colossians gap declaration** (present_in_pdf:false +
  alternate-source research). Gated on publisher direction;
  parallel-track candidate to a δ.x.col-ingest ship.

The arc closes when 26 of 27 NT books are in
`content/translations/geez-tewahedo/` at `ocr-tier3`. The col slot
remains as documented-gap-pending-alternate-source.
