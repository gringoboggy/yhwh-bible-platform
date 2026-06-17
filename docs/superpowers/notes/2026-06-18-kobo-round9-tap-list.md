# Kobo round 9 — device tap-list (user)

**Status:** READY 2026-06-17 — fresh `ethiopian-tewahedo` eink kepub built post-Round-9.
**Artifact:** `build/round9-kobo-tap/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-17T202652Z.kepub.epub` (40 MB)
**Gates:** `verify_kr2_build.py` ALL K-R2 GREEN · kepubify 1/0/0 · epubcheck on `.epub` reports RSC-012 on cross-file glossary `↩` links (pre-existing class; device path unchanged since round 9 ship)
**Sideload:** copy to the Kobo as `YHWH-koboQA.kepub.epub` (reuse the on-device filename — K-R5-1 font-reset lesson).

Prior checklist: `notes/2026-06-15-kobo-round9-device-qa.md`. Round-13 glossary navigate proof: `notes/2026-06-15-kobo-round13-device-qa.md`.

## What this answers

Round 9 gates **M3 catalog live claim** on user device PASS for the K-R9b/c glossary backmatter stack (no 73 MB crash regressions). One **gen 35:18** re-tap closes the round-5 translation-popup anomaly thread now that study badges navigate to glossary instead of preview.

## Protocol

Same reading conditions as rounds 4–6: Cardo (or chosen reading font) selected; footnote-preview taps **once** per badge/link. Record **P** = preview pops · **J** = jumps/navigates elsewhere · **N** = nothing visible (counts as J — piece-top landing).

## P0 — crash regressions (must not reset to home)

| # | Tap target | Expected | Result |
|---|---|---|---|
| 1 | **Gen 1:1** — each coloured study badge at verse end | J → Study Notes at matching category section; ↩ returns | |
| 2 | **Study Notes** (native ToC) | Opens glossary without crash | |
| 3 | Page into glossary from last scripture page forward | No crash | |
| 4 | Page into glossary from Sources backward | No crash | |
| 5 | **Gen 1:1** — no (1/7)…(7/7) popup split badges | Only category-coloured badges | |

## P1 — UX

| # | Tap target | Expected | Result |
|---|---|---|---|
| 6 | **BOOK I** title page | BOOK + numeral separated (K-R7-4b) | |
| 7 | **Gen 1:1** `vn-link` translation badge | P — preview pops | |
| 8 | Study Notes nested ToC | Per-book entries jump correctly | |

## P2 — bracket + gen 35:18 (closes round-5 anomaly)

Post-K-R9 the K-R4-2 **translation** popup pool has almost nothing in the 4,498–5,500 stripped bracket (study content lives in glossary). Calibration on this artifact (`dev/kobo_tap_calibration.py`) yields two anchor rows:

| # | Verse | Role | stripped | aside id | Expected |
|---|---|---|---|---|---|
| 9 | **1en 99:1** | control (round-5 pop floor class) | 2,778 | `vnote-1en-99-1` | P |
| 10 | **Deuteronomy 28:22** | control (glossary padded decline class) | 5,600 | `vnotes-deu-28-22-text` | J |
| 11 | **Genesis 35:18** — `vn-link` translation badge | re-tap (was 3,509 stripped inline study in round 5; now **788** stripped `vnote-gen-35-18`) | 788 | `vnote-gen-35-18` | **P** |
| 12 | **Genesis 35:18** — study category badge(s) at verse end | K-R9c navigate | — | glossary `vnotes-gen-35-18-*` | J → Study Notes |

Row 11 is the decisive re-tap: if **P**, the round-5 inversion was study-layout-specific and closed. If **J/N** on the translation link at 788 stripped, escalate to WIN (Option B in `notes/2026-06-18-platform-kobo.md`).

## After the taps

1. Fill the Result column (or report "rows 1–8 PASS, 11 P, 12 J").
2. Append verdict to `notes/2026-06-15-kobo-round9-device-qa.md` §Verdict template.
3. On PASS → `dev/EREADERS.md` §Kobo M3 live claim confirmed; WIN may refresh M3 SHA256 only if builder delta demands it.

## Maintainer measurements (this artifact)

| Metric | Value |
|---|---|
| Popup asides scanned | 76,936 |
| Pieces / title singletons | 1,050 / 83 |
| Max piece size | 882 KB |
| Translation `vnote` pop floor WARNs | 1ki 12:24 (6,985 stripped) · 1ki 2:35 · 2ki 6:32 |
| Glossary decline control | deu 28:22 @ 5,600 stripped |