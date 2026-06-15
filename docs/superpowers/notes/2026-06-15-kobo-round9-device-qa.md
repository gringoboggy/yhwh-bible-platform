# Kobo round 9 — device QA checklist (K-R9b + K-R9c)

**Build:** `Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-15T135228Z.kepub.epub`  
**Path:** `build/kobo-marker-ab/` (also copy to `G:\YHWH-koboQA.kepub.epub` when testing)  
**Prior round:** round 8 FAIL — 73 MB monolithic `index_split_900.html` crashed Kobo on s7/7, Study Notes ToC, and paging into glossary.

## What changed (builder)

| ID | Change |
|---|---|
| **K-R9b** | Dedicated `split_study_glossary_document` — depth-aware section parse (nested `vn-group` sections), cuts at book heads + verse asides → **107 spine pieces** (max ~720 KB; no 73 MB file). |
| **K-R9c** | **Per-category coloured badges** at verse end (eink backmatter default): one badge per note category present; hue matches S2 cascade; badge shows category glyph (+ count when >1). Tap = **navigate** to `#vnotes-{book}-{ch}-{v}-{cat}` in glossary (not footnote popup). |
| **K-R9b nav** | Study Notes ToC entry expands to nested per-book links (`#study-{code}`). |
| **K-R7-4b** | BOOK + numeral eyebrow spans (carried forward — user confirmed PASS). |

## Forensics (pre-device)

- Study glossary files: **107** (`index_split_900_00.html` … `_106.html`)
- Largest HTML in kepub: scripture ~932 KB (normal); **no** `index_split_900.html` monolith
- `dev/verify_study_backmatter.py`: **PASS**
- Gen 1:1 badges: per-category (`badge-cat-hist`, `badge-cat-comm`, …) — **not** s1…s7 popup units

## Device tap matrix (user)

### P0 — crash regressions (must not reset to home)

1. **Gen 1:1** — tap each coloured badge at verse end; should open Study Notes at the matching coloured section; ↩ returns to verse.
2. **Study Notes (native ToC)** — opens glossary without crash.
3. **Page into glossary** — from last scripture page forward, and from Sources backward; no crash.
4. **No s7/7 popup split** — there should be **no** (1/7)…(7/7) badges on Gen 1:1; only category-coloured badges.

### P1 — UX

5. **BOOK I** title page — BOOK and numeral still separated (K-R7-4b).
6. **Translation vn-link** — still popup at verse start (formatting polish = separate).
7. **Chapter flow** — no stray page breaks between chapters (user noted improvement in round 8/9).
8. **Study Notes nested ToC** — per-book entries jump to correct book section.

### P2 — known open

9. **Clement / deuterocanon extras** — verse translator numbers not clickable (separate inject gap).
10. **Glossary piece size** — some pieces ~700 KB (under Kobo crash threshold vs 73 MB; tune 400 KB cap later if needed).

## Verdict template

| Check | PASS / FAIL | Notes |
|---|---|---|
| Gen 1:1 category badges → glossary | | |
| Study Notes ToC | | |
| Paging into/out of glossary | | |
| BOOK I | | |
| Translation popups | | |

**Round 9 overall:** PASS / FAIL — blocks M3 catalog until PASS.