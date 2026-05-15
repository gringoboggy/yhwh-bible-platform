# τ.7.x.a.0 PILOT — Amharic Genesis page-range discovery + parser-extension finding

**Shipped:** 2026-05-15
**Triggered by:** user "save and continue" after τ.6.x.2.D D-decisions
codification — advancing to τ.7.x.a (Amharic Genesis full-book ingest)
per D4-c locked decision.
**Status:** PILOT — discovers Genesis page range + surfaces parser-
extension-needed finding for the full ingest. τ.7.x.a proper is
BLOCKED on τ.6.x.1.C parser extension (analogous to τ.6.x.1.A pilot
flagging τ.6.x.1.B parser extension).

**Form parallels** `dev/PILOT_TAU6X1A_OUTPUT.md` (the τ.6.x.1.A
pilot artifact that became the precedent for empirical-finding
documentation).

---

## §1 — Genesis page range (VERIFIED)

| Field | Value |
|---|---|
| section name | `genesis` |
| book_codes | `[gen]` |
| pdf_page_range | `[0, 85]` (0-indexed; inclusive both ends) |
| total pages | 86 |
| chapter_count_expected | 50 |
| pages per chapter (avg) | 1.72 |
| verified | `true` |
| verified_at_phase | `τ.7.x.a` (this pilot) |

**Discovery method:** Text-layer marker scan (`pymupdf.get_text()`)
across pages 0-150 + boundary inspection at pages 84-88.

**Marker hits supporting the range:**

| Page | Marker | Significance |
|---|---|---|
| 0 | `ኦሪት ዘልደት` | Geʽez Genesis title at top of first page |
| 0 | `ምዕራፍ ፩።` (OCR: `B ።`) | Chapter 1 marker |
| 0 | `በመጀመሪያ` | Amharic Gen 1:1 first word (also found at 10, 104 — likely cross-references) |
| 84 | Joseph era / Gen 50:4 content | Last clear Genesis content |
| 85 | Bible header banner + transition | End-of-Genesis page |
| 86 | `ዝ ውነቱ አስማቲሆሙ ለይቋቀ እስራኤል` | Exodus 1:1 ("These are the names of the sons of Israel") — start of Exodus |
| 88 | `ኦሪት ዘፀአት` (Exodus title) | Publisher convention: explicit title appears later in the book |

**Boundary precision rationale:** the publisher convention puts the
formal "ኦሪት ዘፀአት" header LATER within Exodus (page 88, around Exodus
2 narrative), not at the opening page of Exodus 1. Verified by
inspecting page 86 (which opens with Ex 1:1 content) and confirming
page 85 has no Exodus content. Therefore Genesis ends at page 85.

---

## §2 — OCR + text-layer timing

Single-page rendering + extraction timings on this Windows install
(Python 3.14.4, Tesseract v5.5.0.20241111, pymupdf):

| Engine | Per page | 86 pages × | Notes |
|---|---:|---:|---|
| Tesseract OCR (350 dpi) | ~7-8s | ~5.7-11.5 min | Both columns; can be 4× faster with `ProcessPoolExecutor` per τ.6.x.1.A pilot extrapolation |
| Text-layer (pymupdf `get_text()`) | ~6-60ms | ~0.5-5s | First page slow (~60ms; PDF index init), subsequent pages ~6ms |

**Recommendation for the full ingest:** prefer **text-layer engine**
over Tesseract for this PDF's Amharic column. The text-layer
extraction is **~1000× faster** AND produces visibly cleaner Ethiopic
text — the PDF embeds a pre-OCR'd text layer that is significantly
higher quality than re-OCRing the rendered page image. The text-
layer-engine output for page 0 contains recognizable Gen 1:1-14
verse-by-verse content with proper Amharic characters.

The Tesseract OCR by contrast produces more garbled output (e.g. the
chapter marker comes out as `ምፅራፍ ል፳።` instead of `ምዕራፍ ፩።`; the
amh language model trades fidel-character recognition fidelity for
broader script coverage).

---

## §3 — Quality observations (text-layer engine, pages 0-2)

**Page 0** produces clean recognizable Gen 1:1-14 text:

```
ምዕራፍ B ።
በመጀመሪያው ቁን እግዚአብሔር ሰማይንና ምድርን
[Gen 1:1 — note: PDF uses "በመጀመሪያው ቁን" = "in the first day"
 vs the standard Π.0 seed "በመጀመሪያ" = "in the beginning"; the
 publisher's parallel-Bible edition uses an expanded reading]
ምድር ግን በዶዋኝ ነበረች...
[Gen 1:2]
እግዚአብሔርም ብርሃን ይሁን አለ...
[Gen 1:3]
... and so on through approximately Gen 1:14
```

**Observation 1 — Variant Genesis 1:1 reading:** the PDF source's
Amharic Gen 1:1 reads `በመጀመሪያው ቁን እግዚአብሔር ሰማይንና ምድርን ፈጠረ` ("In
the first day God created the heavens and the earth") — an
expanded variant of the standard `በመጀመሪያ` opening. The Π.0 seed
used the standard form. **τ.7.x.a proper should preserve the
PDF's variant reading** since the publisher's edition is the
authoritative source for the Tewahedo parallel-Bible track.

**Observation 2 — Cross-references appear inline:** the PDF
interleaves biblical cross-reference markers between verse paragraphs
(e.g. `ቀ. ፲፫` = "Job 13", `አዮ. ቛ፮፡` = "Job 26:?", `መዝ. ዩሣ፡ ፲8።` =
"Ps 79:18 (?)"). These are short Ethiopic-or-mixed-script lines
matching the pattern `<book-abbrev>. <numeral>` — they look like
inline footnotes and should be FILTERED OUT by the parser before
verse-text accumulation.

**Observation 3 — Page-header bleed:** publisher's banner footer
appears at top of each page as ASCII garbage ("ndo Chueh Fach
ahd Cndex" / "northodox.ord"). The existing `has_ethiopic` filter
in `parse_verses_from_text` correctly handles this.

**Observation 4 — Body-text quality is GOOD.** Despite the
verse-marker-finding (next section), the actual Amharic body text
is highly readable in the text-layer extraction — fidel characters
are correctly preserved; sentence boundaries (`።`) and Ethiopic
punctuation (`፣`, `፤`, `፡`) appear as expected.

---

## §4 — EMPIRICAL FINDING: `paragraph_mode_parser_extension_needed`

**Critical finding analogous to τ.6.x.1.A's `verse_numeral_parser_
extension_needed`:**

The Amharic Genesis text **does NOT have leading verse numbers**.
Verses are paragraph-flowing, separated by paragraph breaks (blank
lines or consecutive newlines), NOT prefixed by `<digit>` or
`<ethiopic-numeral>` markers. The existing `parse_verses_from_text`
keys off `VERSE_NUM_RE = ^\s*(\d+)[.:\)\s]` which never matches —
producing **2 garbled verses for pages 0-5** instead of the expected
~150 verses (Gen 1-5 = 31+25+24+26+32 = 138 verses).

**Contrast with Meqabyan (τ.6.x.1.A pilot):**

| Section | Verse-marker style | Parser strategy |
|---|---|---|
| Meqabyan Geʽez column (page 1318) | Explicit Ethiopic-numeral prefix: `፪፤ ስመ ፡ ጺሩጻይዳን...` | `VERSE_NUM_RE` matches after τ.6.x.1.B's `normalize_verse_numerals()` pre-pass |
| Genesis Amharic column (page 0) | Paragraph-flowing, NO prefix; verses end at `።` | `VERSE_NUM_RE` does NOT match; parser produces near-empty output |

**Root cause:** the publisher's Tewahedo parallel-Bible PDF uses
DIFFERENT verse-marker conventions for different books:
- **Tewahedo-distinctive sections** (Meqabyan, etc.) carry explicit
  Ethiopic-numeral verse prefixes — likely because the source
  manuscripts have them.
- **Standard-canon books** (Genesis, etc.) flow as paragraph prose
  without explicit numbers — verses are visually counted by the
  reader against the chapter marker.

**Conjecture (untested at this pilot):** Exodus and other standard-
canon books likely share Genesis's paragraph-flowing convention;
Jubilees and 1 Enoch (Tewahedo-distinctive) likely share Meqabyan's
explicit-numeral convention. **Validation deferred to τ.7.x.b
(Exodus pilot) + τ.6.x.2.a (Geʽez Genesis pilot).**

---

## §5 — Resolution path: τ.6.x.1.C parser extension

The parser needs a **paragraph-mode verse-splitter** that:

1. **Detects chapter markers** the same as today
   (`CHAPTER_HEADER_RE` matches `ምዕራፍ <numeral>` patterns; already
   extended by τ.6.x.1.B to tolerate Ethiopic punctuation
   separators).

2. **Detects verse boundaries by paragraph breaks** rather than by
   leading digits. The simplest heuristic: a paragraph break is
   two-or-more consecutive newlines OR a single newline followed
   by a line that doesn't start with whitespace-continuation
   characters.

3. **Filters out cross-reference lines** matching patterns like
   `^<short-token>. <numeral>` where short-token is 1-4 Ethiopic
   characters (book abbreviations: `ቀ`=Qedus/saints, `አዮ`=Job
   abbreviation `አዮብ` shortened, `መዝ`=Mezmur/Psalms, etc.).
   Pattern proposed: `^[ሀ-ፗ]{1,5}[\.,]\s*[፩-፼\d]+[፡:፣]?\s*[፩-፼\d]*\s*$`.

4. **Numbers verses sequentially within each chapter**, starting
   from 1 immediately after the chapter marker.

5. **Validates against known verse counts per chapter** as a sanity
   check. For Genesis: chapters 1-50 have known verse counts
   (Gen 1=31, Gen 2=25, Gen 3=24, Gen 4=26, Gen 5=32, ...; the
   total Genesis verse count is 1533 in the Masoretic Text). Discard
   ingest results that diverge by more than ~10% from the expected
   total.

**Naming convention (proposed):** the parser-extension ship is
**τ.6.x.1.C** by analogy with τ.6.x.1.A → τ.6.x.1.B. The ship would
extend `parse_verses_from_text()` with a NEW `paragraph_mode=True`
keyword (default `False` for backward compatibility with Meqabyan
+ Tewahedo-distinctive book extraction).

**Estimated scope for τ.6.x.1.C:** ~½ to 1 session. Pure parser-
extension work; no engine changes, no source-data changes, no
content/translations/* writes. Pin tests would extend the existing
`test_parallel_bible_tau6x1.py` with a `TestTau6X1CParagraphMode`
class.

---

## §6 — Alternative source paths considered

Per the Π.0 seed of `content/translations/amharic-tewahedo/gen.py`:

> Full ingest is τ.7.x — publisher chooses source (nehemiah-osc.org
> modern Amharic; eBible.org amh VPL if available; the parallel-
> Bible Amharic column as cross-witness).

Three potential sources for τ.7.x.a:

| Option | Source | Status | Notes |
|---|---|---|---|
| A | parallel-Bible PDF (this pilot's target) | DEFAULT under D4-c | Requires τ.6.x.1.C parser extension; preserves variant readings (e.g. `በመጀመሪያው ቁን`) |
| B | nehemiah-osc.org modern Amharic | UNTESTED | Different source; may produce DIFFERENT readings than the publisher's parallel-Bible edition |
| C | eBible.org `amh` VPL | UNTESTED (status checked at τ.6.x.0a) | Verse-Per-Line format; would bypass parser-extension need entirely |

**Recommendation:** stick with Option A (parallel-Bible PDF) for
**source authority + reading consistency** with the publisher's
authorized edition. The τ.6.x.1.C parser extension is the cleanest
unblocker.

**If publisher elects Option B or C instead**, τ.7.x.a's path
changes substantially:
- Option B: new fetcher in `_fetchers.json`; new declarative source
  block in `_source.yaml`; no parser extension needed if the source
  is already verse-per-line; readings may diverge from the
  publisher's edition.
- Option C: similar to Option B; eBible.org `amh` is well-formatted
  but its readings reflect United Bible Societies' modern revision
  rather than the EOTC liturgical text.

---

## §7 — τ.7.x.a.0 PILOT closed-arc preservation

This pilot ship preserves ALL 17 closed-arc invariants from
AUDIT_2026-05-15-DEEP §1.8:

1. γ.4.8.E Mäqabyan 67/67 — unchanged (no Meqabyan touched)
2. γ.4.8.F Mäqabyan ≥212 entries — unchanged
3. Π.0.1 amharic-in-POPUP_LANGUAGES — unchanged
4. Π.0.4 EMBED_FONT_PATHS=[] — unchanged
5. τ.6.x.0a no-ingest contract — **PRESERVED** (no data written
   to either translation slot; structural_map extension is
   metadata, not data)
6. τ.6.x.0b honesty + Option-D authorization — unchanged
7. δ.1.0 entries=[] — unchanged
8. δ.1.x.A.0 batch_prep — unchanged
9. Π.1 jubilees + one_enoch + laodiceans sections — unchanged
10. Π.1 extraction_status historical pin — unchanged
11. Π.1.B laodiceans alternate-source — unchanged
12. Π.2.prep checklist — unchanged
13. Ω.0 free-public pivot — unchanged
14. τ.6.x.0c script/Ethiopic adoption — unchanged
15. τ.6.x.1 engine-wiring contract — unchanged (engine exercised
    but not modified)
16. τ.6.x.1.B parser-extension contract — unchanged (parser
    exercised; the finding `paragraph_mode_parser_extension_needed`
    is OUT-OF-CONTRACT for the parser's current scope — it's a
    NEW scope-extension request, not a regression)
17. τ.6.x.2.D D-decisions contract — **PRESERVED** (the
    D4-c Amharic-first sequencing is honored; τ.7.x.a is the next-
    up phase per the locked decisions; the τ.7.x.a.0 sub-phase is a
    discovery-pilot within τ.7.x.a, analogous to how τ.6.x.1.A
    was the pilot within τ.6.x.1+)

**The τ.7.x.a.0 PILOT does NOT mutate any of:**
- `scripts/extract_parallel_pdf.py` (engine + parser unchanged)
- `content/translations/*/{*.py}` beyond gen.py seeds (Π.0 contract
  preserved; gen.py still has 3 verses)
- `content/canons.yaml` / `content/editions.yaml` / `content/books.yaml`
- `content/notes/*.py`
- EPUB build outputs (`exports/` untouched)

**The τ.7.x.a.0 PILOT DOES mutate:**
- `content/translations/sources/parallel-bible-eotc/_source.yaml`
  (structural_map gains `genesis` entry + ocr_strategy gains
  `tau7xa_pre_pilot` block)
- This file: `dev/PILOT_TAU7XA_OUTPUT.md` (NEW)
- `tests/test_parallel_bible_tau7xa.py` (NEW)
- State docs (SESSION_STATE, IN_FLIGHT, CHANGELOG, PLAN,
  PI2_PRE_FLIGHT_CHECKLIST)
- `tests/test_omega4x_hygiene.py` share-pin → milestone-pin

---

## §8 — Pilot probe scripts (NOT committed)

The probe scripts I wrote during this pilot are one-shot debugging
tools (per project rule §3.1 sequencing — temporary inline scripts
are NOT shipped as `scripts/_*.py` shims):

- Page-range marker scan (pages 0-150 for Genesis + Exodus + chapter
  markers) — inline `PYEOF` heredoc; output captured in §1.
- Boundary inspection (pages 84-88 text-layer dump) — inline; output
  captured in §1.
- OCR smoke test (pages 0-2 Tesseract) — inline; output captured in
  §2-3.
- Text-layer smoke test (pages 0-5 + parse_verses_from_text) — inline;
  output captured in §3-4.

All probes deleted upon writing this artifact. The empirical findings
are codified here + in `_source.yaml::ocr_strategy.tau7xa_pre_pilot`.

---

## §9 — Next-phase sequence (post-τ.7.x.a.0)

Per the D4-c locked decision + this pilot's findings, the next-phase
sequence rewires from:

```
[Before τ.7.x.a.0]
τ.6.x.2.D ✓  →  τ.7.x.a  →  τ.7.x.b...z  →  τ.6.x.2.a...z  →  τ.6.x.3  →  Π.2
              (Amharic Genesis)
```

to:

```
[After τ.7.x.a.0 PILOT — this ship]
τ.7.x.a.0 ✓  →  τ.6.x.1.C  →  τ.7.x.a (proper)  →  τ.7.x.b...z  →  τ.6.x.2.a...z  →  τ.6.x.3  →  Π.2
 (pilot)       (parser extension)  (full ingest)
```

The τ.6.x.1.C parser-extension ship UNBLOCKS τ.7.x.a (proper) +
all subsequent τ.7.x.b...z + τ.6.x.2.a...z incremental ingests
(under the conjecture that all standard-canon books share Genesis's
paragraph-flowing convention).

**Phase ordering rewire is codified in:**
- `_source.yaml::ocr_strategy.tau7xa_pre_pilot.derived_phase_ordering`
  (NEW block — this ship)
- `dev/SCOPE_2026-05-14-parallel-bible.md` (extension at next ω-
  class touch; deferred since it's not blocking τ.6.x.1.C)
- `dev/PI2_PRE_FLIGHT_CHECKLIST.md` (gate dashboard extension to
  insert τ.6.x.1.C row above τ.7.x.a row)

---

## §10 — Empirical inputs for τ.6.x.1.C (parser-extension scope)

When τ.6.x.1.C ships, it should consume the following empirical
inputs from this pilot:

1. **Paragraph-mode regex candidate** (untested at pilot):
   ```python
   PARAGRAPH_BREAK_RE = re.compile(r"\n\s*\n+")
   ```

2. **Cross-reference line filter** (heuristic; refine empirically):
   ```python
   CROSS_REF_LINE_RE = re.compile(
       r"^[ሀ-ፗ]{1,5}[\.,]\s*[፩-፼\d]+[፡:፣]?\s*[፩-፼\d]*\s*$"
   )
   ```
   Matches: `ቀ. ፲፫`, `አዮ. ቛ፮፡ Is`, `መዝ. ዩሣ፡ ፲8።`, `መዝ, i ፡ 2s`
   Does NOT match: `በመጀመሪያው ቁን እግዚአብሔር ሰማይንና...` (verse text)

3. **Known verse-count floor per chapter** (calibration sanity check):
   ```python
   GENESIS_VERSE_COUNTS = {
       1: 31, 2: 25, 3: 24, 4: 26, 5: 32, 6: 22, 7: 24, 8: 22,
       9: 29, 10: 32, 11: 32, 12: 20, 13: 18, 14: 24, 15: 21,
       16: 16, 17: 27, 18: 33, 19: 38, 20: 18, 21: 34, 22: 24,
       23: 20, 24: 67, 25: 34, 26: 35, 27: 46, 28: 22, 29: 35,
       30: 43, 31: 55, 32: 33, 33: 20, 34: 31, 35: 29, 36: 43,
       37: 36, 38: 30, 39: 23, 40: 23, 41: 57, 42: 38, 43: 34,
       44: 34, 45: 28, 46: 34, 47: 31, 48: 22, 49: 33, 50: 26,
   }
   # Total = 1533 (Masoretic Text + LXX agreement for Genesis)
   ```

4. **Parser API extension proposal** (untested):
   ```python
   def parse_verses_from_text(
       text: str,
       *,
       paragraph_mode: bool = False,
   ) -> list[tuple[int, int, str]]:
       """...
       paragraph_mode=True: split verses by paragraph breaks
       (consecutive newlines) and number sequentially per chapter.
       Filter cross-reference lines. (τ.6.x.1.C)
       """
   ```

   Callers in `extract_section()` then pass `paragraph_mode=True`
   when the section is a standard-canon book (Genesis, Exodus, ...)
   and `paragraph_mode=False` when the section is Tewahedo-
   distinctive (Meqabyan, Jubilees, 1 Enoch — these have explicit
   numeral markers).

5. **Validation runtime regression-pin proposal** for τ.6.x.1.C:
   - After τ.6.x.1.C parser extension, re-run the page-0-through-5
     extraction → expect ≥138 verses (Gen 1:1 through Gen 5:32).
   - If the extension produces ≤120 or ≥160 (±15% tolerance), the
     parser needs further refinement.

---

*PILOT_TAU7XA_OUTPUT.md — τ.7.x.a.0 PILOT empirical findings,
2026-05-15. Surfaces the `paragraph_mode_parser_extension_needed`
finding that re-routes τ.7.x.a's blocking chain through τ.6.x.1.C
parser-extension before the full Amharic Genesis ingest can complete.
Analogous to dev/PILOT_TAU6X1A_OUTPUT.md (which surfaced the
`verse_numeral_parser_extension_needed` finding that was resolved by
τ.6.x.1.B).*
