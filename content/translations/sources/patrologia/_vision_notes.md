# Patrologia vision-transcription — calibration + decision record (D1b)

> Companion to `docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md`.
> This file is the canonical record of the Task-0 calibration decisions the plan references,
> AND the running self-upgrading-matrix log of per-chapter findings + recurring vision
> failure-classes (append during the Task-4 transcription so the next chapter inherits the lesson).

## Source
- **Esther** — `GAPS/5_Esther/Esther__PO-9-fasc-1_Pereira_1913.pdf` (694-page PDF; **Esther body = 0-indexed PDF pages 24–65**). Public domain (PO is pre-1923). Editor: Pereira 1913.

## PO Esther page layout (calibrated 2026-05-28 by rendering pp.24/32/35/37/48/60 + 230-DPI body strips)
Each page, top → bottom:
1. **French banner** — `LE LIVRE D'ESTHER. — <Roman ch>, <verse-range>` (or addition form `… — B, 1`); bracketed page-number at the corners. Tells the chapter/addition + verse span on that page.
2. **Ge'ez BODY** (larger type; ~top 6–42% of the page) — the scripture. **Verse numbers run down the margins** (left and/or right) AND as small inline superscripts; Additions carry a **letter label** in the margin (e.g. `B. 1`).
3. **Apparatus band** (smaller, dense Ge'ez; ~42–60%) — the editor's manuscript-variant readings, keyed to verse-number + manuscript **sigla (M / N / O / P / Q …)**. This is **editorial, NOT scripture — EXCLUDE it.**
4. **French translation** (bottom ~40%).

**Legibility = GO.** At 230 DPI / ≤1568px the body glyphs + margin numerals are clearly readable. The apparatus band is visually separable (smaller type, below the body) — a vision agent can transcribe the body + capture the margin numbers + exclude the apparatus, where the earlier Tesseract OCR could not (the OCR swept the Ge'ez-script apparatus into the verse text + lost the margin numerals → the current KJV-renumbered garbage `est_patrologia.py`, e.g. vv1:4–1:6 are almost pure apparatus).

**Render the body strip for vision** = top **0.45** of the page (banner + body + margins; apparatus + French excluded), DPI **230** (full-width ≈ 1518px, under the vision downsample cap). Reuse `extract_patrologia_pdf._render_strip_to_png` / the new `render_body_for_vision`.

## Pereira's own versification (the structure to preserve faithfully)
Canonical chapters (Roman, 1–10) **interleaved with the six LXX Additions A–F as LETTERED chapters with their own verse numbering**, in LXX reading order. Confirmed boundaries (from the banners):
- **A** (Mordecai's dream + plot, ~17 v) — opens the book, BEFORE canonical 1:1 (p24 margin `A`).
- **B** (the king's edict, ~7 v) — **SPLITS canonical chapter 3**: `3:1–13` → **`B:1–7`** → `3:14–15` (p35 banner `III, 9 — B, 1`; p37 banner `B, 5 — III, 15`).
- **C** (prayers of Mordecai & Esther, ~30 v) — after `4:17` (per the old OCR docstring banner `IV, 17 — C, 7`).
- **D** (Esther before the king, ~16 v) — after C (banner `C, 29 — D, 6`).
- **E** (the counter-edict, ~24 v) — after `8:12`.
- **F** (interpretation of the dream + colophon, ~11 v) — after `10:3`.
(Exact per-addition verse counts + host-chapter boundaries are read per-page during transcription; the STRUCTURE above is the calibration finding.)

## LOCKED decision (a) — Additions store-encoding
**Canonical chapters stay int (1–10). Each Addition's verses live INSIDE its host canonical chapter, at the source position where Pereira prints them, with STRING verse labels** (`"A1".."A17"`, `"B1".."B7"`, `"C1"…`, `"D1"…`, `"E1"…`, `"F1"…`).
- e.g. Esther chapter 3's stored `VERSES` (source order): `(3,1)…(3,13), (3,"B1")…(3,"B7"), (3,14), (3,15)`.
- Addition A → leading verses `(1,"A1")…(1,"A17")` before `(1,1)`. F → trailing verses in chapter 10. C+D → chapter 4 trailing (after 4:17), in C-then-D order.

**Why this is correct + safe (verified against `scripts/build_standalone.py`):**
- The renderer does `for ch in sorted(by_ch)` (build_standalone.py:252) — keeping **canonical chapters int** means `sorted()` never sees a mixed int/str chapter set ⇒ no `TypeError`, no clumping.
- The renderer **preserves verse source-order within a chapter** (`chapter_verses_in_source_order` :183; `render_chapter_body` does NOT re-sort verses) ⇒ the addition renders in its exact interleaved position (B between 3:13 and 3:14) — **faithful to Pereira**.
- `render_chapter_body` (:93–105) only **string-interpolates + dict-keys** the verse number (`seen[gv]`, `f"…{gv}…"`, `appmap.get(str(gv))`, `en_map.get((gv,occ))`) — it **never does int arithmetic on the verse** ⇒ **string verse labels are fully tolerated** (verified by reading the function).
- **Byte-stable for Kings/Samuel/Psalms:** they have only int verses → behavior unchanged.
- **No renderer surgery.** Rejected alternatives: string CHAPTER keys (break `sorted()`); int-offset addition chapters A=101…F=106 (clump additions after ch10, losing the interleave); continuous int verse renumber (collides with / shifts canonical verse numbers → breaks KJV xref + violates "trust the source numbering").

## LOCKED decision (b) — book-code / standalone wiring
- `translations` loads `est_patrologia.py` as a **slot distinct from `est.py`** (loader keys by file stem; probe confirmed both addressable, each currently 22 KJV-renumbered ch1 verses). ⇒ the own-vers transcription **OVERWRITES `est_patrologia.py`**; `est.py` (EOTC ocr-tier3) is **untouched** (honors patrologia design spec §6 decision B: keep both).
- Add `"est_patrologia"` to `build_standalone._STANDALONE_BOOKS` (currently `["1ki","1sa","2sa","psa"]`).
- Add `_canonical_book(slot)` → strips the `_patrologia` suffix → `"est"` for the KJV-xref (`kjv/est.py`) + canonical ordering.
- Add `_BOOK_TITLES["est_patrologia"] = "Esther"` (or map via `_canonical_book`) so the chapter heading reads "Esther N" not "est_patrologia N".
- Addition verses have **no KJV equivalent** → xref sidecar emits `{"kjv":[],"confidence":"none","apparatus":[]}` for them (honest; KJV Esther = 10 canonical chapters only).

## Page → content map (calibrated so far; extend during transcription)
| PDF page | Content (banner) |
|---|---|
| 24 | Addition **A** opens + canonical 1:1 (`ዘኣስቱር` title; margin `A`) |
| 32 | `II, 14–19` (canonical ch 2) |
| 35 | `III, 9 — B, 1` (canonical 3:9–13 → Addition **B** begins) |
| 37 | `B, 5 — III, 15` (Addition B:5 → returns to canonical 3:14–15) |
| 48 | `V, 12 — VI, 3` (canonical ch 5→6) |
| 60 | `IX, 5–15` (canonical ch 9) |

## GO / NO-GO = **GO**
Body legible · margin verse-numbers recoverable · apparatus separable · Additions representable faithfully with the locked encoding + zero renderer surgery. Proceed to the per-chapter vision transcription (plan Task 4), MAX 1 heavy Opus agent, calibrate on canonical ch 1 (+ Addition A) first, per-chapter commits. Job (clean linear ch 1–42, no additions) remains the documented fallback but is **not** needed.

## Recurring vision failure-classes (append during Task-4 transcription)
_(none yet — seed)_
- e.g. "apparatus-bleed at a column foot when the body is short on a page" → instruct the transcriber to stop at the first siglum-keyed line.
- e.g. "margin numeral X misread as Y at low contrast" → note the glyph pair.
