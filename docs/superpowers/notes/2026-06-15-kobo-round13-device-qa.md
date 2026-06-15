# Kobo round 13 — device QA (K-R13 footnote + glyph + pad fix)

**Build:** `Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-15T213413Z.kepub.epub`  
**Kobo:** `G:\YHWH-koboQA.kepub.epub` · Desktop `YHWH-koboQA-round13.kepub.epub`

## Root cause (round 12 still 0 change)

1. **Padding was ineffective (K-R13c):** `.kobo-study-nav-pad` used NBSP filler, but `_stripped_len` collapses all `\s+` (including U+00A0) — a 5,600-NBSP pad counted as **one** character. Artifact forensics showed ~200–4,300 stripped per category despite `PAD` marker.
2. **Wrong target type:** `noteref` pointed at plain `<section>` inside a non-footnote wrapper; Kobo's footnote preview path expects `epub:type="footnote"` targets.
3. **Empty badge chips (2/6 on Gen 1:1):** Category glyphs ✧ ⌂ ✦ are missing from Cardo; Kobo showed empty bordered chips for `text`, `hist`, `topic`.

## K-R13 fix

| ID | Change |
|---|---|
| **K-R13a** | Each glossary category is a padded `<aside epub:type="footnote" class="study-glossary-cat">` with `id="vnotes-{book}-{ch}-{v}-{cat}"`. Verse wrapper is `<div class="study-glossary-entry">`. |
| **K-R13b** | E-ink study badge faces use Kobo-safe substitutes: `hist→H`, `text→†`, `topic→*`, `comm→◇`, etc. (glossary cascade headers unchanged). |
| **K-R13c** | Pad filler switched from NBSP to `.` (period) so stripped count reaches ≥ 5,600. Forensics: all Gen 1:1 / 2:10 categories now **5601 NAV+**. |

Translation `vn-link` popups unchanged.

## Device taps (P0)

1. **Gen 1:1** — all **6** badges must teleport (not popup).
2. **Gen 2:10** — badge **3/3** must teleport.
3. **Badge symbols** — all six Gen 1:1 chips show a visible glyph (H, ◇2, ‖2, †, ⌘7, *).
4. **Verse-number translation** — still popup.

**Round 13 overall:** **PASS** (2026-06-15) — Gen 1:1 all six badges teleport; Gen 2:10 badge 3/3 teleports; no empty badge chips; translation popups still work; Azariah ToC clean. Remaining: translation popup formatting polish; Study Notes lead copy updated for next build.