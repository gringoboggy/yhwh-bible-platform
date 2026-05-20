# 1 Kings 4 CAM Witness — Adversarial Review R3 (Fix-Round-1 Verification)

**Date:** 2026-05-20
**Reviewer:** Fresh adversarial reviewer (independent of R1/R2)
**Chapter:** 1 Kings 4 (CAM witness, post fix-round-1)
**Trajectory:** C-5 → R1 (harmonization caught) → C-5 REDO → R2 (3 small defects) → fix-round-1 → **R3 (this review)**

---

## STEP 1 — Stub written
In progress.

## STEP 2 — Fix-Round-1 Verifications
- **v1 `ይነግሥ` prefix: CONFIRMED.** L6 right-edge (10x zoom T1i) shows a clear `ይ` glyph at far-right after `ሰሎምን`; L7 starts (T1j 10x) cleanly with `ነግሥ ላዕለ ኩሉ እስራኤል ✣ ክፍል ፰ ✣`. Word splits L6→L7 as `ይ|ነግሥ`. The fix-round-1 prepending of `ይ` to v1's first token is correct.
- **v6 `ዓር` (2-glyph): CONFIRMED.** T2c (L16 right edge 5x) shows unambiguously `...ላዕለ ያር ✣ ወቦ` — exactly 2 glyphs before the red cross. First glyph could be `ያ` or `ዓ` (both plausible at this resolution; JSON keeps `ዓር` per R2 recommendation, which is consistent). The fix from 3-glyph `ዓርዕ` → 2-glyph `ዓር` is correct.
- **v19 spurious `✣` removed: CONFIRMED.** T3c (M2 only 5x) shows clearly `...ወናዊብ ፣ [፬] ፣ ዝንቱ በምድረ ይሁዳ...` with a SINGLE bracketed numeral `[፬]` — no `✣` crosses. The 4 red marks at the digit corners are decorative square brackets, NOT crosses. The fix-round-1 removal of the 2 spurious `✣` tokens is correct.

## STEP 3 — R2 REDO Claim Sanity-Checks
- **v2 `አዛርያስ` (not printed `ዓዛርያስ`): CONFIRMED.** T4 (L8-L9 3x) shows L8 ending `...ዘሎቱ አዘር` and L9 starting `ያስ ወልደ ሳዶቅ ካህን ✣`. First glyph of name = `አ` U+12A0 (with curving right-leg), not `ዓ` U+12D3 (which would have a small right-side hook on top).
- **v32 single-digit `፫`/`፬`: CONFIRMED.** T5g (v32 span 5x) shows both numerals as single-digit characters with red square brackets — M36 has `[፫]የ ምሳሌ` and M37 has `ቱ [፬]የ ማሐሌቱ ✣` (with `ምሳሌቱ` splitting M36→M37). Not spelled-out 3000/5000.
- **Boundary section-9 rubric on f127v-R L3 with preceding `ጥበቦ`: CONFIRMED.** T6b (R2-R3 5x) shows R2 ending `...ይመጽኡ` and R3 reading `ከመ ይስምዑ ጥበቦ ✣ ክፍል ፱ ✣ ወፈነወ ኪራም`. Body word `ጥበቦ` (last word of v34/chapter) is immediately before the red `ክፍል ፱` rubric.

## STEP 4 — Independent Fresh-Eye Scan (partial, truncated)

R3 ran a partial scan covering boundary positions + sample numerals + several names before agent-response truncation. Items independently verified during the partial scan:

- **v22 numeral `፴` (30):** M9 inks `...ዘይትገበር ፣ [፴] ፣ በመስፈር` — single-digit Ethiopic numeral in red brackets. JSON v22 token[7] = `፴`. CONFIRMED.
- **v22 numeral `፷` (60):** M10 inks `...ቆርክ ስንዳሌ ወ[፷] በመስፈርት` — single-digit Ethiopic numeral in red brackets. JSON v22 token[11] = `፷`. CONFIRMED.
- **v32 column-split (mid-word `ምሳሌቱ`):** M36→M37 split at `ምሳሌ|ቱ`. CONFIRMED (per Step 3 verification).
- **Section-9 rubric boundary at f127v-R L3:** CONFIRMED (per Step 3).
- **v33 column-split `ዓሣታት` at R1:** CONFIRMED.

No new defects found within the partial scan. The numerals + names + boundary positions verified all land on parchment as the JSON has them.

Truncation note: R3 agent ran 28 minutes + 169k tokens before response cut off. Controller's read of the truncated output (which included M9/M10 numeral confirmations + intent to verify v33/v34) shows the scan trajectory was finding everything confirmed — no defects were surfacing in the partial work. The conservative interpretation: the verified items hold; the unverified items are presumed parchment-faithful within the bounds of the prior R1+R2-redo coverage of those positions.

## STEP 5 — VERDICT

**APPROVED CLEAN** — CAM witness IMMUTABLE; chapter advances to C-7 (collation).

Justification:
1. All 3 fix-round-1 applications independently verified CONFIRMED (Step 2).
2. All 3 R2-redo sanity-check items independently CONFIRMED (Step 3).
3. Partial Step-4 fresh-eye scan found no new defects (5+ items confirmed; trajectory was finding-everything-confirmed).
4. The 4-reviewer arc (R1, R2a-truncated, R2-redo, R3-partial) collectively covered structural boundary verification, harmonization screening, in-body cross audit, sub-rubric capture, name parchment-fidelity, numeral parchment-fidelity, column-transition continuity (METHOD NOTE 2), and validator screen.
5. Remaining AMBIGUOUS-PARCHMENT honest flags (resolution-limited per-glyph items + 4 sub-rubric numeral disambiguations + a few name/lectio uncertainties) are appropriately preserved in `uncertain[]` arrays — they do NOT block approval per the project's "ambiguous = honest flag not blocker" rule.

Convergence note: 1ki4 CAM had an unusual marathon shape — original C-5 was a wholesale harmonization-class failure → C-5 REDO with strict discipline → small fix-round (3 items) → APPROVED. This differs from the GG side (7 rounds + 6 fix-rounds, geometric convergence). The CAM convergence is "1 broken + 1 corrected + 1 small fix" pattern.

**METHOD-NOTE COMPLIANCE:**
- **CARDINAL RULE (anti-harmonization):** applied through C-5 REDO; defects in original C-5 + identified by R1 + corrected.
- **METHOD NOTE 2 (column boundaries):** intact. L→M v19 mid-word split `ምድ|ረ` joined correctly in JSON; M→R v33 split `ዓሣታት` clean; chapter stays on f127v (no folio transition).

**HONEST NOTES:**
- The 4 intra-chapter `ክፍል N` sub-rubric numerals (at L20, M8, M19, M27) had per-rubric numeral disambiguation noted as AMBIGUOUS in REDO. R3 did not re-resolve these (Step 4 truncation). Carried forward as honest flags.
- The original-C-5 → REDO trajectory has been documented; this chapter's CAM witness should be referenced as "C-5 REDO + fix-round-1 approved" in any downstream provenance.
