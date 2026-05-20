# REVIEW 2026-05-20: 1 Kings 4 CAM Witness — Round 2 (truncated-retry)

**Date:** 2026-05-20
**Reviewer:** Fresh adversarial agent (R2-retry-b)
**Target:** `content/manuscript/kings/calibration/1ki4_witnessCAM_hires.json`
**Parchment:** `GAPS/2_Kings/Cambridge-Add-1570-hires/MS-ADD-01570_f127v_1ki4_hires.jpg`
**Prior reviews:** R1 (defect catalogue) + R2a (truncated mid-analysis, partial findings preserved below)

---

## TRUNCATION SAFETY

This file is written **iteratively** to survive context truncation. If this report is incomplete, the partial findings below are the canonical R2 verdict — defer to them rather than re-running. The truncated R2a's L1-L10 reading is preserved below and confirmed (or refuted) section-by-section.

---

## STATUS

- [ ] In progress
- [x] Complete

**Final state:** verification complete; 4 defects identified (1 medium, 3 low), report written iteratively to survive truncation.

---

## VERDICT

### **NEEDS_FIX (round-1-of-CAM-fix)** — three small JSON edits required

The REDO is **substantially correct** on the most contested issues:
- Boundary START at L7 (with rubric on L7, body starts before rubric on L7) — REDO right; R2a's claim of "rubric on L6 / body on L7 starting with `ወእሉ`" is **REFUTED** (R2a confused biblical-chapter vs Ethiopic-`ክፍል` semantics).
- Boundary END at f127v-R L3 with `ጥበቦ` before `✣ ክፍል ፱ ✣` — REDO right (CONFIRMED).
- v2 `አዛርያስ`, v6 `አክያል`, v32 `፫`/`፬` numerals, v19 column-split `ምድ|ረ`, v5 `ስዶማን` (vs R1's `እልየማን`) — all REDO right (CONFIRMED).

But REDO has 3 specific defects requiring fix-round-1:
- **D1 (medium):** v1 first token should be `ይነግሥ` (recovering the `ይ` on L6) OR boundary-note must document the cross-chapter glyph split.
- **D2 (low):** v6 last token `ዓርዕ` has an extra letter; parchment shows 2 glyphs only (`ዓር` or `ያር`).
- **D3 (low):** v19 has two spurious `✣` cross tokens flanking the inline `፬` numeral; parchment shows only `[፬]` with red brackets (which REDO mistook for crosses).

**One investigation** for next-round: v19 second-deputy `ዑራ` vs `ሁሬ` (deferred — not critical for fix-round-1).

The R2a finding that triggered this review is partially **CORRECTED**: R2a's "L6 rubric / L7 body" was off-by-one and R2a's "v1 starts with `ወእሉ`" was wrong on substance. However R2a was right to flag a boundary issue — the actual defect is the missing `ይ` on v1 first word, not the wholesale v1 misassignment R2a proposed.

---

## SECTION 1 — Boundary verification (3 items)

Crops examined: `fL_L1to10_2x.jpg`, `fL_L5to9_3x.jpg`, `fL_L7to11_3x.jpg`, `fL_L6_rightedge_6x.jpg`.

### 1a. Rubric line position — REDO CORRECT, R2a OFF-BY-ONE

Parchment shows `✣ ክፍል ፰ ✣` (red, with surrounding `✣` crosses) on **L7** of the folio, INLINE at the END of the line containing `ነግሥ ላዕለ ኩሉ እስራኤል`.

- **R2a said rubric is on L6** — WRONG. R2a's line count is off-by-one (R2a's "L6" = my "L7"; R2a's "L7" = my "L8").
- **REDO says rubric is mid-L7 after v1 body** — CORRECT on line, CORRECT on position (after `እስራኤል`).

### 1b. First body word of 1Ki4 — R2a's claim REFUTED; REDO defective in a different way

Parchment evidence (high-zoom L6 right edge crop):
- L6 ends with `...ኮነ ንጉሥ ሰሎምን ይ` (with a clear `ይ` U+12ED hanging glyph at right margin).
- L7 begins with `ነግሥ ላዕለ ኩሉ እስራኤል ✣ ክፍል ፰ ✣`.

So the clause `ኮነ ንጉሥ ሰሎምን ይነግሥ ላዕለ ኩሉ እስራኤል` ("Solomon became king reigning over all Israel") spans L6→L7. This is the canonical Ge'ez 1Ki4:1 wording (matches MT 1Ki4:1).

**Cross-check against 1Ki3 CAM file:** `1ki3_witnessCAM_hires.json` v27 (last verse) ENDS with `...ወእምዝ፣ከነ፣ንጉሥ፣ሰሎምን` — confirming the 1Ki3 transcription already absorbed `ሰሎምን` and the `ይ` start-letter of `ይነግሥ` is the natural seam for 1Ki4 v1.

**R2a's claim REFUTED:** R2a said v1 first body word is `ወእሉ` — but `ወእሉ እሙንቱ መላእክት ዘሎቱ አዛርያስ...` is biblical 1Ki4:**v2** ("and these are his officials"), not v1. Biblical 1Ki4:1 = "Solomon was king over all Israel" = exactly the `(ይ)ነግሥ ላዕለ ኩሉ እስራኤል` content REDO has as v1. So REDO's v1 assignment is CORRECT in concept.

**HOWEVER — REDO has a different boundary defect:** REDO's v1 starts at L7 with `ነግሥ`, dropping the `ይ` prefix that hangs on L6 right edge. The proper v1 should be `ይነግሥ፣ላዕለ፣ኩሉ፣እስራኤል` (with `ይ` recovered from the L6→L7 word split). Currently REDO's `ነግሥ` is a truncation; the parchment word is `ይነግሥ`.

**Defect-fix options:**
- Option A: Update REDO v1 first token from `ነግሥ` to `ይነግሥ` and add an `uncertain[]` note documenting the L6→L7 split.
- Option B: Update 1Ki3 v27 to strip the trailing `ሰሎምን` (so 1Ki3 ends at `ወእምዝ ከነ ንጉሥ`) — but this is unwise as it disturbs the 1Ki3 file already shipped.
- **Recommended: Option A.** Lightweight, additive, accurate.

### 1c. Chapter end — REDO CLAIM CONFIRMED

Crop `fR_L1to5_v2_3x.jpg` shows f127v-R top:
- **L1:** `ዓሣታት ✣ ወይመጽኡ ኩሉ ሕዝብ ከመ ይስምዑ ጥበ`
- **L2:** `ቦ ለሰሎምን ወኩሎሙ ነገሥት ምድር ይመጽኡ`
- **L3:** `ከመ ይስምዑ ጥበቦ ✣ ክፍል ፱ ወ ✣ ወፈነወ ኪራም ንቱ`

`ጥበቦ` is the last word of 1Ki4 v34, immediately followed by red rubric `✣ ክፍል ፱ ✣` and then biblical 1Ki5:1 start `ወፈነወ ኪራም ንቱ(ሥ ጢሮስ)` on the same L3. **REDO's chapter-end is CORRECT.** Also v33 column-split (`ዓሣታት` at R1 head) is CONFIRMED.

---

## SECTION 2 — Sample-verify 5 REDO claims

Crops examined: `fL_L7to11_3x.jpg`, `fL_L13to14_v5_3x.jpg`, `fL_L15to16_v6_3x.jpg`, `fM_M30toM37_3x.jpg`, `fL_bottomtext_3x.jpg`, `fM_M1to5_3x.jpg`, `fM_M2only_4x.jpg`.

1. **v2 name `አዛርያስ`** — **CONFIRMED.** Parchment shows `አዛር` at end of L8 and `ያስ` at start of L9 — split form joins to `አዛርያስ` (አ U+12A0 + ዛ + ር + ያ + ስ, 5 glyphs). NOT `ዓዛርያስ` with ዓ. Matches REDO.

2. **v6 first deputy name `አክያል`** — **CONFIRMED.** L15 reads `...ቲ ንጉሥ ✣ ወአክያል መገቤ ቤት ወአዶኒ`. The name with waw connector is `ወአክያል`; bare name `አክያል` (አ + ክ + ያ + ል). Matches REDO. NOT `አኪሳር`.

3. **v32 numerals `፫` and `፬`** — **CONFIRMED.** Crop `fM_M30toM37_3x.jpg` shows both red-bracketed Ge'ez numerals on M35-M36: `[፫]የ ምሳሌ` and `[፬]የ ማሕሌቱ`. These are recensionally significant — printed editions give spelled "3000" and "5000" but CAM has single-digit ፫ / ፬. Matches REDO.

4. **v19 column-split `ምድረ` from `ምድ | ረ`** — **CONFIRMED.** L40 (last line of f127v-L) ends with `...ምድ` (glyphs ም + ድ at right margin); M1 (first body line of f127v-M) begins with `ረ ሲዎን ንቱሥ አሞርዎን ወዕግ ንቱሥ ባ`. The lone `ረ` completes `ምድረ`. Matches REDO column_split note.

5. **v5 contested word: REDO `ስዶማን` vs R1 `እልየማን`** — **REDO CONFIRMED, R1 REFUTED.** L13 reads `...ላዕለ ስዶማ|` with `ን` carrying to L14. The initial glyph is clearly `ስ` (U+1235, with characteristic "lasso" curve), NOT `እ` (U+12A5, which has a closed bowl). The second glyph is `ዶ` (U+12F6, with horizontal crossbar), NOT `ል` (U+120D, simple vertical L-stroke). So the word is **`ስዶማን`** as REDO claims.

### Additional finding (bonus): v6 last word

L16 reads `...ላዕለ ያር ✣ ወቦ ሰ` — the v6-last word before the cross is **2 glyphs** (`ያር` or `ዓር`), NOT 3 glyphs as REDO claims (`ዓርዕ`). REDO has an extra `ዕ` letter that the parchment doesn't show. Could be `ያር` (Yar = territory of Yar?) or `ዓር` (Ar = enemy/army?). Either way, REDO's `ዓርዕ` reading appears to have one too many letters.

### Additional finding (bonus): v19 first deputy

REDO v19 has `ወልደ ዑራ` as the second-deputy form (Uri); parchment L-bottom reads `ወልደ ሁሬ` (ሁ + ሬ). Possibly REDO mis-transcribed `ሁሬ` as `ዑራ`. AMBIGUOUS — both glyphs are similar in CAM hand; would need closer inspection.

---

## SECTION 3 — Cross-count audit (✣ red-crosses)

Sample verses cross-counted:

| Verse | REDO ✣ count | Parchment ✣ count | Match? |
|-------|------|-----|-----|
| v2 (end) | 1 | 1 (L9 between `ካህን` and `ኤልያብ`) | ✓ |
| v6 (end) | 1 | 1 (L16 between `ያር` and `ወቦ`) | ✓ |
| v19 (inline numeral) | **2** | **0** | ✗ DEFECT |

### v19 mismatch detail

REDO has `["✣", "፬", "✣"]` (3 tokens) bracketing the v19 inline numeral. Parchment M2 shows the numeral as `[፬]` — a red-bracketed Ge'ez digit, with the small red marks at the corners being **bracket punctuation**, NOT ✣ crosses (U+2723).

REDO's `uncertain[]` notes correctly identify the brackets as "red square brackets" for the numeral but ALSO add two separate `✣` cross tokens flanking it — those are spurious. The brackets ARE the same marks that REDO is double-counting as crosses.

**Defect:** v19 token sequence `[..., "ወናዊብ", "✣", "፬", "✣"]` should be `[..., "ወናዊብ", "፬"]` (or `"[፬]"` if literal preservation desired). Remove the two `✣` tokens at positions 13 and 15; keep the numeral.

---

## SECTION 4 — Defect list

| # | Severity | Verse | Defect | Source |
|---|----|----|----|----|
| D1 | MEDIUM | v1 | First token is `ነግሥ` but parchment L6→L7 boundary has `ይነግሥ` (the `ይ` glyph hangs on L6 right edge as a split-word fragment). Either v1 should start `ይነግሥ` (recover the L6 `ይ`), or document the L6→L7 split explicitly. | Section 1b |
| D2 | LOW-MEDIUM | v6 | Last lectio token is `ዓርዕ` (3 glyphs); parchment shows only 2 glyphs (`ያር` or `ዓር`). Likely an over-counted letter. | Section 2 bonus |
| D3 | LOW | v19 | Last 3 tokens are `["✣", "፬", "✣"]`; parchment shows only the bracketed numeral `[፬]` — the two `✣` tokens are spurious (REDO conflated bracket marks with cross marks). | Section 3 |
| D4 | LOW (AMBIGUOUS) | v19 | Second-deputy name is `ዑራ` in REDO; parchment may read `ሁሬ`. Glyph-pair similar in CAM hand — needs verification. | Section 2 bonus |

**No defect on:** boundary start (REDO v1 correctly aligns with biblical 1Ki4:1 content despite minor `ይ` prefix issue), boundary end (`ጥበቦ` before `✣ ክፍል ፱ ✣` on f127v-R L3 — CONFIRMED), v2 name `አዛርያስ`, v5 `ስዶማን` (REDO right, R1 wrong), v6 first-deputy `አክያል`, v32 numerals `፫`/`፬`, v19 column-split `ምድ|ረ`, v33 column-transition `ዓሣታት` at R1.

**R2a's central claim (v1 first word = `ወእሉ`) is REFUTED** — that's biblical v2's first word, not v1. R2a confused the lectionary section break (`ክፍል` rubric is a scribal divider INSIDE the biblical chapter) with the biblical chapter break (which is the content of `ኮነ ንጉሥ ሰሎምን (ይ)ነግሥ ላዕለ ኩሉ እስራኤል` itself).

---

## SECTION 5 — Recommended fix scope (fix-round-1-of-CAM)

**Three small JSON edits + one investigation:**

### Fix 1 (D1, MEDIUM) — v1 first token
Change v1 first token from `ነግሥ` → `ይነግሥ` (5 glyphs ይ+ነ+ግ+ሥ, prepending the `ይ` recovered from L6 right edge). Update `geez` string accordingly. Update `uncertain[]` note to document L6→L7 word split.

OR alternatively (less preferred):
Keep v1 first token as `ነግሥ` (with explicit note that the `ይ` prefix is on L6 in 1Ki3's transcription scope — i.e., a deliberate decision to put the cross-chapter glyph with the prior chapter).

### Fix 2 (D3, LOW) — v19 spurious crosses
Remove two `✣` tokens (positions 13 and 15) flanking the `፬` numeral in v19 tokens. Remove their corresponding `uncertain[]` notes. Update `geez` string to `... ✣ ወናዊብ ✣ ፬` (no trailing `✣`) or whatever the proper post-bracket-strip rendering is. **Verify:** the v19 end has only the `፬` numeral inside brackets — no flanking crosses.

### Fix 3 (D2, LOW-MEDIUM) — v6 last word
Change v6 last token from `ዓርዕ` (3 glyphs) → `ዓር` (2 glyphs) or `ያር` (2 glyphs). The parchment shows only 2 glyphs before the cross. Document the glyph-form choice in `uncertain[]`.

### Investigation (D4, LOW) — v19 second-deputy
Re-examine `ዑራ` vs `ሁሬ` at higher zoom on the parchment. Decision can be deferred to the next collation pass (C-7).

**Estimated effort:** ~10-15 min of JSON editing + 1 re-validation pass.

---

## APPENDIX — Prior R2a's preserved partial finding (L1-L10 of f127v-L)

- **L1:** `ሙ፣እስራኤል፣ዘንተ፣ፍትሐ፣ዘፈትሐ` (continuation of 1Ki3:28 from prior column/folio)
- **L2-L4:** more 1Ki3:28 content
- **L5:** editorial bracket `(ወፍትሐ።)` then `ወ እምዝ ኮነ ንጉሥ ሰሎ-` (with `ሰሎምን` splitting L5→L6)
- **L6:** `ሞን ላዕለ እስራኤል ✣ ክፍል [፰]` — **chapter rubric is on L6, not L7**
- **L7:** `ወእሉ እሙንቱ መላእክት ዘሎቱ` — first body word of 1Ki4 is `ወእሉ` (not `ነግሥ` as REDO has)
- **L8:** `ያስ ወልደ ሳዶቅ ካህን ኤልያብ ወአ` (continuation; `ያስ` = end of `አዛርያስ` from L7-L8 boundary)
- **L9:** `ደቂቅሁ ጸሐፍት✣ ወ ኢ ዮሳፍ ጥ ወልደ`
- **L10:** `አክየድ መዘክር ✣ ወብንያስ ወልደ`

R2a's conclusion: REDO has WRONG v1 first token (`ነግሥ` should be `ወእሉ`); REDO claim "L7 has rubric" is WRONG (L7 has BODY START; rubric is L6).
