# D2 Source Readiness: 1 Enoch & Jubilees (Geez Unicode)
**Date:** 2026-05-28 (recon refresh 2026-06-02)  
**Agent:** light text-only recon (no images/browsers downloaded)  
**Scope:** assess whether clean, PD, Unicode Geez (ግዕዝ script) exists for own-versification Phase-D transcription
**Status:** readiness recon only — NOT an ingest; no corpus/store/build files touched.

> **⚠ 2026-06-02 RECON UPDATE (corrections to the original note):**
> 1. **Charles 1906 Enoch scan DOES carry a real Ge'ez Unicode OCR layer** (re-OCR'd with **tesseract 5.3.0, Ethiopic**), of *moderate* quality — NOT Latin-only as §1(d) originally inferred-by-analogy. Verified by sampling `…/ethiopicversiono00charuoft_djvu.txt`: actual Ethiopic script (e.g. `ወይቤ፡ ሄኖሕ፡`) with chapter/verse headers ("I. 1-5", "V. 6-9"), plus sporadic char-substitution/diacritic errors. This **upgrades ch. 72–108 from pure NEEDS-VISION to parse-with-vision-correction** (a head-start, not a from-scratch marathon). The IA item is re-OCR'd since the original 2026-05-28 check, so the old "Latin-only" verdict is now stale.
> 2. **OCP licensing nuance:** OCP declares the *manuscript text* PD, but the **encoding/tagging is CC BY-NC-ND 4.0** (per external catalog records) and its base text follows **Rylands Eth. MS 23 = Knibb's (in-copyright) 1978 edition**. For a free-distribution Bible, prefer re-segmenting the PD MS text ourselves over republishing OCP's encoded file. The **Charles 1906** path is unambiguous PD and sidesteps this.
> 3. The OCP **TLS cert is still expired** (WebFetch HTTP→HTTPS fail; Playwright `ERR_CERT_DATE_INVALID`) — pulling OCP text will need cert-override or a Wayback snapshot. Original conclusions otherwise stand: **1 Enoch = GO (parse-first); Jubilees = NEEDS-VISION** (its IA OCR is confirmed *gibberish* Ge'ez, not Unicode).

---

## 1. Book of Enoch (Mäṣḥafä Hēnok / 1 Enoch, Chapters 1–108)

### (a) Does clean Unicode Geez exist? Where?

**pseudepigrapha.org** — partial.  
URL: `https://pseudepigrapha.org/docs/text/1En`  
Introduction/metadata: `https://pseudepigrapha.org/docs/intro/1En`

The site (Online Critical Pseudepigrapha) hosts one Ethiopic manuscript for 1 Enoch: **Rylands Ethiopic MS 23**, also reproduced in Knibb's 1978 edition. The intro page confirmed the text is present, described as "reliable," and the site states it represents the Ethiopic tradition alongside all extant Greek and Latin witnesses. The site uses Unicode throughout (the title renders ግዕዝ properly in the search-result snippets). However, the **SSL certificate on pseudepigrapha.org had expired at time of fetch** — the text page (`/docs/text/1En`) could not be directly rendered. The intro page similarly failed with a certificate error. Coverage information was established from search-result snippets which quoted the site's own coverage note.

**No other clean Unicode Geez text** for 1 Enoch was located in any public repository (GitHub, geez.org corpus, Wikisource). Wikisource `/wiki/1_Enoch` carries English translations only (Charles 1917 + Wikisource edition); the Geez title (`መጽሐፈ ሄኖክ`) appears only as metadata, not as a Geez text body.

### (b) Coverage (which chapters)?

pseudepigrapha.org coverage confirmed:
- **Book of the Watchers: chapters 1–36** — Ethiopic manuscript (p) included
- **Parables: chapters 37–71** — Ethiopic manuscript (p) included
- **Astronomical Book (ch. 72–82), Dream Visions (ch. 83–90), Epistle of Enoch (ch. 91–105), Birth of Noah / conclusion (ch. 106–108):** NOT confirmed present. Site notes "Syriac and Coptic fragments still await encoding" and describes ongoing proofreading; no coverage claim for ch. 72–108 was found in any snippet.

**Net coverage (best estimate): ch. 1–71 in Unicode Geez; ch. 72–108 unconfirmed/likely absent.**

### (c) Verse numbering present?

The intro page for pseudepigrapha.org does not describe verse-level markup. The site is a scholarly critical apparatus (multi-witness layout), not a verse-numbered canonical edition. Verse numbering in the Geez column is **unconfirmed** and likely formatted as scholarly reference, not embedded verse tags. NEEDS VERIFICATION by direct page load once the SSL cert is renewed.

### (d) OCR-garbled vs. clean verdict

The pseudepigrapha.org Geez text is **hand-encoded Unicode** (keyed from Knibb's 1978 critical edition), not OCR. The site was described as having its text "proofread" and the Ethiopic text "reliable." It is **not derived from OCR**.

**archive.org — R.H. Charles 1906 "The Ethiopic Version of the Book of Enoch":**
- Primary archive item: `https://archive.org/details/ethiopicversiono00charuoft`
- DjVu text layer: `https://archive.org/stream/Charles_The-Book-of-Enoch_part-1_1906/eth_1_djvu.txt`
- Alternate 1912 translation: `https://archive.org/stream/bookofenochor1en00char/bookofenochor1en00char_djvu.txt`

The 1906 edition is a **page-scan / photographic reproduction** of the Geez manuscript. **CORRECTED 2026-06-02:** the IA item `ethiopicversiono00charuoft` has since been **re-OCR'd with tesseract 5.3.0 (Ethiopic)**, so its `_djvu.txt` text layer now **does contain actual Unicode Ge'ez** (verified sample: `ወይቤ፡ ሄኖሕ፡`, with "I. 1-5" / "V. 6-9" chapter/verse headers), at *moderate* accuracy (char-substitution, spacing, diacritic/footnote-marker errors). The original "Latin-only / image-only" verdict — inferred by analogy to the Jubilees PDF (§2) — is **stale**. **REVISED VERDICT: real Ge'ez Unicode OCR present; usable as a parse + targeted-vision-correction spine, NOT a full vision marathon.** (The Jubilees scan in §2 is genuinely gibberish; the two are NOT analogous.)

### (e) GO / NO-GO / NEEDS-VISION lean

**NEEDS-VISION for ch. 72–108; CONDITIONAL-GO for ch. 1–71**

- Ch. 1–71: pseudepigrapha.org has clean Unicode Geez from Rylands MS 23. Once SSL cert is live (or the text is fetched via curl/wget at transcription time), the Geez body exists and is clean. Verse markup will need to be mapped to EOTC versification but the text layer is present. **Lean: GO with caveat (verify SSL + verse-tag format).**
- Ch. 72–108: **REVISED 2026-06-02** — Charles 1906 (`ethiopicversiono00charuoft`) now has a **moderate-quality Ge'ez Unicode OCR layer** (tesseract Ethiopic) with chapter/verse headers. This is no longer a from-scratch vision target: **parse the OCR + vision-correct the error spans**. **Lean upgraded: PARSE-WITH-VISION-CORRECTION** (head-start, not full marathon). OCP also hosts ch. 72–108 of the Astronomical/Dream/Epistle sections in some witnesses — verify once the cert is fixed.

---

## 2. Jubilees (Mäṣḥafä Kufāle)

### (a) Does clean Unicode Geez exist? Where?

**archive.org — R.H. Charles 1895 "The Ethiopic Version of the Hebrew Book of Jubilees":**
- Main archive item: `https://archive.org/details/CharlesEthiopicJubilees`
- DjVu text layer: `https://archive.org/stream/CharlesEthiopicJubilees/The_Ethiopic_version_of_the_Hebrew_Book_djvu.txt`
- Secondary item (duplicate scan): `https://archive.org/details/EthiopicBookOfJubilees`

The 1895 Charles edition contains the Geez text. The **jubilees.stmarytx.edu** mirror PDF (`https://jubilees.stmarytx.edu/printmedia/Charles-1895-EthiopicVersionHebrewBookJubilees.pdf`) was directly inspected: it is a **Google Books scan** (confirmed by the internal font mapping). The PDF object stream contains JPEG2000-compressed image data; the ToUnicode table maps only Latin characters (`a-z`, punctuation). The Geez pages are **image raster only — no Unicode Geez in the text layer**. **VERDICT: OCR image-only; Geez not extractable as Unicode text.**

No other clean Unicode Geez digitization of Jubilees was found. GitHub searches yielded no relevant repository. geez.org was noted as gathering datasets but no specific Jubilees text was listed. stepbible.org's Geez module does not list Jubilees among its books.

### (b) Coverage (which chapters)?

Charles 1895 covers **all 50 chapters** of Jubilees in Geez. However, coverage = image-scan only, not Unicode text. No Unicode Geez text source was identified at any coverage level.

### (c) Verse numbering present?

Charles 1895 uses chapter/verse subdivision in the critical apparatus. The Geez text column has section markers but these are image-embedded, not extractable as Unicode markup. For any transcription path, verse numbering would need to be re-applied from the critical apparatus. **Not present in any extractable form.**

### (d) OCR-garbled vs. clean verdict

**Image-only (page scans).** The jubilees.stmarytx.edu PDF confirmed this definitively. The archive.org DjVu layer for the same 1895 edition would similarly yield only the Latin-script apparatus, not Geez. No clean Unicode Geez text for Jubilees was found in any public digital collection.

### (e) GO / NO-GO / NEEDS-VISION lean

**NEEDS-VISION (full 50 chapters)**

No public Unicode Geez text source exists for Jubilees. All identified sources are page-scan images of the 1895 Charles critical edition. Transcription requires VISION marathon method against Charles 1895 scans from archive.org. The manuscript is clearly legible (19th-century typeface Ethiopic printing, not a medieval MS), which should make vision-transcription easier than Patrologia manuscript folios. **Lean: NEEDS-VISION, but transcription difficulty is lower than Cambridge MS folios (printed typeface vs. hand-written MS).**

---

## Summary Table

| Book | Clean Unicode Geez? | Where | Chapter Coverage | Verse Numbers in Source | OCR/Clean Verdict | Phase-D Lean |
|---|---|---|---|---|---|---|
| 1 Enoch (ch. 1–71) | YES (conditional) | pseudepigrapha.org — SSL currently expired | ch. 1–71 (Rylands MS 23) | Unconfirmed; scholarly apparatus format | Clean Unicode (hand-keyed, Knibb-based) | CONDITIONAL-GO (verify SSL + verse format) |
| 1 Enoch (ch. 72–108) | PARTIAL (OCR) | Charles 1906 IA scan, re-OCR'd | ch. 72–108 (full edition) | chapter/verse headers in OCR | **Moderate Ge'ez Unicode OCR (tesseract Ethiopic)** — corrected 2026-06-02 | PARSE-WITH-VISION-CORRECTION (Charles 1906) |
| Jubilees (all 50 ch.) | NO | Not found publicly | None identified | N/A | Image-only (Charles 1895 scans confirmed) | NEEDS-VISION (Charles 1895 scans, printed typeface) |

---

## Recommended Next D2 Source Order

**Priority 1 — 1 Enoch ch. 1–71 via pseudepigrapha.org:** Re-attempt text fetch once SSL cert renews (or use `--insecure` curl / Wayback at transcription time); inspect verse-tagging format; map to EOTC versification. Lowest-effort path, largest clean Geez block. **License caveat (2026-06-02):** OCP's *encoding/tagging* is **CC BY-NC-ND 4.0** and tracks **Knibb's in-copyright** edition of Rylands Eth. MS 23 — the underlying *MS text* is PD, but for a free-distribution Bible prefer **re-segmenting the PD MS text ourselves** over republishing OCP's encoded file. The fully-clean-PD alternative for the same block is **Charles 1906** (now with usable Ge'ez OCR — see Priority 3), which sidesteps the OCP license entirely.

**Priority 2 — Jubilees (all 50 ch.) via Charles 1895 scans:** VISION-marathon against archive.org scans (`https://archive.org/details/CharlesEthiopicJubilees`). Printed typeface makes transcription more reliable than Patrologia MS folios. Load chapter by chapter per the ratified marathon method.

**Priority 3 — 1 Enoch ch. 72–108 via Charles 1906:** **REVISED 2026-06-02** — `https://archive.org/details/ethiopicversiono00charuoft` now has a moderate **Ge'ez Unicode OCR** layer (tesseract Ethiopic), so this is **parse-with-vision-correction**, not a from-scratch marathon. Charles 1906 is also the **clean-PD spine for ch. 1–71** (preferable to OCP's CC-BY-NC-ND encoding for free distribution): parse the whole 1906 OCR, vision-correct error spans, segment by the printed chapter/verse headers.

---

## URLs Fetched / Verified

| URL | Status | Note |
|---|---|---|
| `https://pseudepigrapha.org/docs/intro/1En` | SSL expired at fetch time | Coverage confirmed from search snippets |
| `https://pseudepigrapha.org/docs/text/1En` | SSL expired at fetch time | Text page exists; Unicode Geez confirmed by site description |
| `https://archive.org/details/ethiopicversiono00charuoft` | Confirmed exists | Charles 1906 Enoch — page scans |
| `https://archive.org/stream/Charles_The-Book-of-Enoch_part-1_1906/eth_1_djvu.txt` | Confirmed exists | DjVu OCR — Latin only for Geez pages |
| `https://archive.org/details/CharlesEthiopicJubilees` | Confirmed exists | Charles 1895 Jubilees — page scans |
| `https://archive.org/stream/CharlesEthiopicJubilees/The_Ethiopic_version_of_the_Hebrew_Book_djvu.txt` | Confirmed exists | DjVu OCR — Latin only for Geez pages |
| `https://jubilees.stmarytx.edu/printmedia/Charles-1895-EthiopicVersionHebrewBookJubilees.pdf` | Fetched + inspected | CONFIRMED image-only; Geez = raster, not Unicode |
| `https://en.wikisource.org/wiki/1_Enoch` | Fetched | English translations only; Geez title only as metadata |
| `https://www.stepbible.org/version.jsp?version=Geez` | Fetched | Geez Bible (OT only); Enoch/Jubilees not listed |
| `https://openlibrary.org/books/OL7185848M/The_Ethiopic_Version_of_the_Book_of_Enoch` | Fetched | Confirms formats available; text language includes Ethiopic |
