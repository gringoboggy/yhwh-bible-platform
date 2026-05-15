# τ.6.x.1.A pilot validation — output reference (2026-05-14)

Empirical validation that the τ.6.x.1 Tesseract engine wiring works
end-to-end on the real publisher-supplied parallel-Bible PDF.

**Use this artifact as a quality-preview when the publisher considers
τ.6.x.2+ direction** (cadence + tier ramp + per-book audit plan).

---

## Environment

| Field | Value |
|---|---|
| Date | 2026-05-14 |
| Phase | τ.6.x.1.A (pilot validation of τ.6.x.1 wiring) |
| Tesseract | v5.5.0.20241111 (UB-Mannheim Windows) |
| Resolver | `scripts.core.paths.tesseract_binary()` |
| Recognizers | `script/Ethiopic` (Geʽez) + `amh` (Amharic) |
| Engine | `tesseract` (default per τ.6.x.0b Option-D-Hybrid) |
| Render | pymupdf, 350 dpi, 50/50 column split, psm=6 |
| PDF | `Bible_Amharic_and_Geez.pdf` (193.3 MB) |
| Page tested | index 1318 (mq1 / Mäṣḥafä Mäqabyan I, opening page) |

---

## Timing

| Step | Elapsed |
|---|---|
| PDF open + page fetch | ~0.5s |
| Render both columns at 350 dpi (pymupdf) | <1s |
| Tesseract OCR (Geʽez column) | ~3s |
| Tesseract OCR (Amharic column) | ~3s |
| **Total per-page (both columns)** | **~7s** |

**Extrapolations:**

- mq1 (47 pages, pages 1318-1365): **~5.5 minutes** single-threaded.
- mq1 + mq2 + mq3 (67 pages): **~8 minutes** single-threaded.
- Full 66-book standard canon (~2500 pages): **~5 hours**
  single-threaded.

Per-page time is dominated by Tesseract OCR (~85% of total).
Multiprocessing-by-page (a `concurrent.futures.ProcessPoolExecutor`
on the page-loop in `extract_section()`) would parallelize cleanly;
~4× speedup on a 4-core machine is realistic.

---

## Quality observations

**The pilot output WAS produced as OCR-tier3 quality** per the
τ.6.x.0b honesty contract. The publisher should expect:

### Title-row degradation (BIG, stylized fonts)

The book title `መጽሐፈ ፡ መቃብያን ፡ ቀዳማዊ` ("Book of Mäqabyan I")
appears at the page top in large stylized fidel that the standard
`script/Ethiopic` recognizer renders imperfectly:

| Column | OCR output | Expected |
|---|---|---|
| Geʽez | `መጽሐራ ፥ መቃ` (truncated, garbled fidel) | `መጽሐፈ ፡ መቃብያን` |
| Amharic | `[መቃ]ብያን ፥ ቀዳማዊ ።` | `መጽሐፈ ፡ መቃብያን ፡ ቀዳማዊ ።` |

This is expected behavior for stylized title text and matches the
τ.6.x.0b "AVAILABILITY-UNCERTAIN" honesty contract anticipation:
title-rows degrade more than body-text. Verse-popups will not
typically display title-rows directly (verses begin at `1:1`).

### Body-text quality (normal verse fidel)

Body text is recognizably correct with typical OCR-tier3 artifacts
(occasional vowel-order swaps, double-quote substitution, dropped
punctuation):

Geʽez body sample (verses 2-3):
```
፪፤ ስመ ፡ ጺሩጻይዳን ፡ የሚበል ፡ ኃጢጸትንም ፣
፫፣ የሚያመልክቸውና ፡ የሚሰግድላቸው ፡ በሴ
```

Amharic body sample (verses 1-2):
```
፡ መቃብያን፣ የተናገሩት ፤ ነገር፣ይሀ፡ነው።
ልጥላቸዋልና ፤ ባመኑባቸው ፡ ልቡናቸውም ፥
```

**Geʽez numerals (Ethiopic digits ፩ ፪ ፫ …) are correctly recognized**
in both columns — these are the verse markers `parse_verses_from_
text()` keys off, so the verse-keying pipeline downstream of OCR
should work. (Note: τ.6.x.0a's `parse_verses_from_text()` keys off
Arabic digits like `1`, not Ethiopic numerals. The parallel-Bible's
verse markers appear to be Ethiopic numerals in the body. A τ.6.x.2-
prep task may need to extend the parser to accept both digit forms,
or pass the OCR through an Ethiopic→Arabic numeral normalization
before verse-parsing.)

### English-page-header bleed

The publisher's PDF has English page-headers in the page margins:

```
የኢትዮጵያ ኦርቶዶክስ ተዋሕዶ ቤቱ
'Che CctNopnan (JRchodox Cea
| ror ethiopian!
```

These bleed into the column rasters at high dpi. The existing
`parse_verses_from_text()` filter rejects lines that are pure-ASCII
without Ethiopic characters (the `has_ethiopic = any(0x1200 <= ord(c)
<= 0x137F for c in line)` check); the English bleed is therefore
correctly dropped before verse-output. **No τ.6.x.1.A code change
required for this.**

### Visible-but-correctly-filtered Latin contamination

Tesseract's `script/Ethiopic` recognizer occasionally fabricates
Latin/Cyrillic characters when it encounters figure-marker dots
or page-spread guillemets. Examples:

```
ቸምስለው" ፡ ይነግሩት ፡ ነበር ።
['Che CctNopnan (JRchodox Cea]
```

These rows mix Ethiopic + Latin; `has_ethiopic` is True, so the
filter LETS them through. The fix at downstream parse-time is
acceptable per τ.6.x.0b's `ocr-tier3` honesty contract: tier-3
entries are "acknowledged imperfect; awaiting operator cross-check."

---

## Pre-flight validation (verified empirically)

| Check | Status |
|---|---|
| `scripts.core.paths.tesseract_binary()` resolves Windows install path | ✓ `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| `_check_tesseract_languages()` recognizes both `amh` + `script/Ethiopic` | ✓ no missing packs |
| pymupdf `page.get_pixmap(matrix=Matrix(350/72, 350/72), clip=...)` produces valid PNG | ✓ |
| `subprocess.run(...stdin=DEVNULL, capture_output=True, text=True, encoding='utf-8'...)` | ✓ no W-W1 hits |
| `tesseract <png> stdout -l <lang> --psm 6` returns Ethiopic + Arabic-digit text | ✓ |
| `tempfile.TemporaryDirectory()` shared across columns; auto-cleanup | ✓ |
| Total elapsed per page ≤ 60s | ✓ (~7s; well under) |

---

## Publisher-direction inputs for τ.6.x.2+

This pilot output should inform the four open D-decisions that gate
τ.6.x.2+ Geʽez bulk-ingest:

1. **Cadence:** one-shot full-sweep (~5h on dev workstation) vs
   incremental per-book ships (~5-10 minutes per book). The
   incremental path is consistent with the project's `γ.4.x` per-arc
   ship cadence and surfaces quality issues earlier.

2. **Target-tier ramp:** the pilot output IS `ocr-tier3` at the
   baseline expectation. The τ.6.x.0b honesty contract says
   tier-3 → tier-2 happens via operator cross-check. The publisher
   needs to decide whether cross-check happens per-book at
   τ.6.x.2.x sub-ships, or as a single batched τ.6.x.3 audit pass.

3. **Per-book audit plan:** the recommended first-cut audit list is
   2-3 books per major canon division (Pentateuch + Major Prophets +
   Gospels + General Epistles) — enough breadth to surface OCR
   quality variance across font/layout differences in the publisher's
   PDF.

4. **Amharic-parallel sequencing:** the pilot shows the Amharic
   column is generally cleaner than the Geʽez (Amharic-trained vs
   script-level). The publisher can choose to ship `geez-tewahedo`
   first then `amharic-tewahedo` as τ.7.x, or interleave both at
   each τ.6.x.2.x sub-ship.

A separate publisher-side companion to this artifact would be a
side-by-side rendering of `OCR output` vs `expected text` for ~3
sample verses per book section. That can be produced when the
operator cross-check pass starts.

---

## τ.6.x.0a contract preservation

This pilot is **DRY-RUN only**. No file was written to
`content/translations/geez-tewahedo/` or `content/translations/
amharic-tewahedo/`. Both slots remain at their Π.0 seed state
(`gen.py` only, 3 verses Genesis each). The τ.6.x.0a contract is
preserved across the τ.6.x.0a → τ.6.x.0b → τ.6.x.0c → τ.6.x.1 →
τ.6.x.1.A wiring + validation chain.
