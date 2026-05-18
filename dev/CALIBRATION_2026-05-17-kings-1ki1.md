# 1 Kings 1 — Kings Dual-Manuscript SAFETY-STOP Confirmation (τ.6.x.4.c)

**Project:** YHWH v2.4 — Ethiopian Tewahedo Bible publishing platform
**Chapter:** 1 Kings 1 (Solomon's accession; David's old age, Adonijah's bid, Bathsheba/Nathan, Solomon anointed). 53-verse canonical KJV spine.
**Date:** 2026-05-18
**Status of this document:** NOT a GO/NO-GO gate. This is the **bi-directional safety-stop pattern-confirmation** for the Kings marathon. Kings does **not** re-run a calibration gate — the diplomatic-parallel model + base=CAM were **user-ratified 2026-05-17 (GO)** for this exact manuscript family (GG-00106 + Cambridge Add. 1570); Samuel Phase-1 was the one-time method-proving gate. 1 Kings 1 is transcribed/collated first only as an *implicit pattern check*: confirm the ratified pattern holds before the 47-chapter bulk; **stop and surface only if it CONTRADICTS**.

> **Verdict (one line):** **MATCHES the ratified distinct-recension pattern** — semantic 100.0% (53/53), both-confident 29.89%, base=CAM, no contradiction trigger fired → the marathon continues continuously, no user check-in (Task #14 validator-hardening gates the 1ki2–22 bulk).

---

## 1. What was done

Independent blind dual-witness vision transcription of 1 Kings 1 from two Ge'ez manuscripts, collated through the **already-shipped Phase-2 tool** (the τ.6.x.4.b Samuel-proven engine, reused verbatim — Stage 0 only track-parameterized the manifest loader + driver, samuel-default byte-identical).

- **GG — Gunda Gundē, MS GG-00106.** 1 Kings 1 = folios **f028v → f029r** (f028v all 3 columns + f029r left column + first ~30 lines of middle column). Source: `GAPS/2_Kings/GG-00106/1-Kings/1-Kings_f028v.jpg`, `…_f029r.jpg`. Hand "generally clean and legible at high magnification"; **0 illegible tokens**. Blind-transcribed (saw no CAM, no skeleton); adversarially reviewed; converged in **3 fix-rounds** against the anti-harmonization-to-printed-text failure class. Immutable, committed `eaf2063`. **53 verses.**
- **CAM — Cambridge UL MS Add. 1570.** 1 Kings 1 = folios **f126r → f126v** (f126r 3 columns → f126v left). Hi-res ~80 MP CUDL IIIF tile-stitched master (CC BY-NC, Cambridge University Library); folio identity double-confirmed (manifest label + f106r=view215 cross-check, zero drift). Source: `GAPS/2_Kings/Cambridge-Add-1570-hires/MS-ADD-01570_f126r_1ki1_hires.jpg`, `…_f126v_1ki1_hires.jpg`. Parchment "clean and the hand highly legible throughout 1 Kings 1 with only one genuinely abraded spot" (v30 red rubric → **1 honest `⟦illegible⟧`**). Blind-transcribed (saw no GG); adversarially reviewed; converged in **3 fix-rounds** — round-1 caught and restored **2 CRITICAL accidental column/folio-boundary scripture omissions** that had been mis-labelled "recensional minuses" (f126r col1→col2 lost std v15/16; col3→f126v-L lost std v42), re-segmented 50→**52 verses**. Immutable, committed `75ba7b2`.
- **Collation:** C-7 ran `mc.load_kjv_skeleton('1ki',1)` → `mc.collate(gg,cam,k,book='1ki',chapter=1)` → `mr.reconcile(col)` → `content/manuscript/kings/collation/1ki1_collation.json` (53-verse canonical spine). Committed `9bb9976` together with the manifest 1ki:1→`calibrated` flip.

**Independence + adversarial honesty review (C-8).** An independent reviewer re-ran the shipped engine end-to-end and **independently re-implemented every metric definition** from `verses[].alignment[]`. Result: **PASS** — all six metrics reproduced **byte-identical**; token-conservation 0 failures across all 53 rows; the lacuna bijection holds in both witness files; `_pick_base` independently re-derived as the honest two-clause decision-of-record picker (clause-1 material-extent test `52 < 0.70·53` = False → clause-2 returns CAM purely by citation of the ratified decision, **no fitted/numeric CAM-forcing constant**); v30 (CAM illegible) carries **0 GG-substituted tokens** (GG reading only in the apparatus, resolution="base"); v53 (CAM extent-minus) recorded `resolution:"marked-gap"` with GG **not** merged into running text; validator `OK` on both witnesses. One cosmetic prose imprecision tracked below (not a defect).

---

## 2. Metrics (read from `content/manuscript/kings/collation/1ki1_collation.json` `metrics`; C-8-verified byte-identical — nothing restated from memory)

| Metric | 1 Kings 1 value | Raw fraction | Bi-directional safety-stop reading |
|---|---|---|---|
| **Semantic-pass** (verses telling the same narrative beat vs the KJV spine) | **100.0%** | 53 / 53 | ≥ 95% → **MATCHES** (no `semantic < 95%` contradiction) |
| **W↔W strict** (exact literal token identity / aligned pairs) | 14.86% | 136 / 915 | far below 90% — distinct recension |
| **W↔W skeleton** (diacritic/order/near-homograph-folded / full aligned denom) | 19.78% | 181 / 915 | far below 90% — distinct recension |
| **W↔W both-confident** (skeleton-equal over pairs neither scribe flagged) | **29.89%** | 165 / 552 | materially < 90% → **MATCHES** (NOT ≈unity; no contradiction) |
| **Self-flagged uncertainty** (base=CAM) | 0.26% | 2 / 760 | negligible — clean, confidently-read text both sides |
| **Lacuna counts** | gg 0 · cam 1 · both 0 | — | `both=0` → no fabrication possible; honest |
| **Base witness** | **CAM** | — | base=CAM (did NOT flip to GG) → **MATCHES** |

GG (53 v) / CAM (52 v) extents are not materially different; the 1-verse delta + CAM-side recensional minuses are recorded honestly as `disagree`/`marked-gap`, not fabricated agreement.

---

## 3. Bi-directional safety-stop evaluation (the plan-header rule, applied explicitly)

**MATCHES the ratified pattern requires ALL of:** semantic ≥ 95% · both-confident materially < 90% on clean text · base = CAM · no contradiction.

1. **semantic ≥ 95%?** → 100.0% (53/53). **YES.**
2. **both-confident materially < 90% on clean text?** → 29.89%, on text both scribes read confidently (uncertainty 0.26%, GG 0 illegible, CAM 1). **YES** — this is the distinct-recension signal, exactly as ratified for this manuscript family.
3. **base = CAM?** → CAM, by the honest decision-of-record `_pick_base` (C-8-verified: no reverse-fitted constant). **YES.**
4. **no contradiction?** The three CONTRADICTS triggers, each checked:
   - *≈unity W↔W agreement ≥ 90% on a clean chapter?* → strict 14.86 / skeleton 19.78 / both-confident 29.89 — **all far below 90%**. NOT ≈unity. **No contradiction.**
   - *base empirically flips to GG on an undamaged folio?* → base = CAM; folios clean/undamaged (GG 0 illegible; CAM 1 abraded spot only). Base did **not** flip. **No contradiction.**
   - *semantic-pass < 95%?* → 100.0% ≥ 95%. **No contradiction.**

**All MATCHES criteria hold; no CONTRADICTS trigger fires → VERDICT: MATCHES.**

**Conservative re-verification (memory `feedback_reverify_conservative_nogo`).** The contradiction direction is *too-similar* (≈unity ≥ 90%), base-flip-to-GG, or semantic failure. 1 Kings 1 shows *more* textual divergence than the ratified Samuel 1 reference (1ki1 both-confident 29.89% / skeleton 19.78% vs 1sa1 73.05% / 44.75%), with **both folios essentially undamaged** (Samuel 1's GG had a vv.21–28 water stain; here GG is clean and CAM has a single abraded rubric). Greater divergence on cleaner text is **not** a new contradiction — it is *stronger* confirmation of the same ratified distinct-recension model (semantic-identical narrative, materially divergent Ge'ez recension, CAM base, per-verse apparatus). The optimistic "MATCHES" call survives adversarial re-check.

---

## 4. Tracked cosmetic note (C-8 finding — NOT a defect, no escalation)

The engine-emitted `metrics.lacuna_counts_note` prose says `⟦illegible⟧` is "excluded from every agreement denominator." Strictly, the single CAM `⟦illegible⟧` (v30) lands in a one-sided `disagree` cell which **is** one of the (agree+disagree) denominator rows; only `lacuna-*`-class rows are excluded. **Impact is honesty-conservative and ≤ 0.02 pp:** it can only *depress* agreement (strict 14.86→14.88, skeleton 19.78→19.80 if excluded), can never inflate, and can never be counted as agreement (GG side empty). It is **wording imprecision in a generated note string of the shipped, Samuel-byte-identical Phase-2 engine**, with **zero metric/data impact**. Per memory `no-reassert-ratified-bar`, this is recorded as an honest tracked WARN — it is **not** failed as a gate and the shipped engine is **not** mutated mid-marathon (doing so would risk the Samuel byte-identical regression contract Stage 0 deliberately preserved). Eligible for a separate engine-note-precision cleanup *outside* this marathon, run with the Samuel-equivalence regression.

---

## 5. Consequence (per the plan decision-inheritance rule)

**MATCHES → the marathon continues continuously, with no user check-in** (the diplomatic-parallel + base=CAM model is already user-ratified 2026-05-17 for GG-00106 + Cambridge Add. 1570; the safety-stop has confirmed it holds on 1 Kings 1, on cleaner text than the original gate chapter).

**Next:** **Task #14 — fold the corrected non-Ethiopic contamination screen (which whitelists the sanctioned `⟦illegible⟧` sentinel) into `validate_witness`**, verified to keep the 4 immutable Samuel goldens + the 71-test manuscript regression green. Task #14 **gates** the 1 Kings 2 → 22 then 2 Kings 1 → 25 bulk (Task #6 blocked by #14). After #14 lands, the bulk runs continuously, one chapter at a time (C-1…C-9 per chapter), manifest-tracked, no further safety-stop (C-10 is 1 Kings 1 only). Then Stage 2 (Phase-3 render `geez-tewahedo/1ki.py`+`2ki.py` + apparatus + `manuscript-collation-tier2`). Local commit only — no push, no zip.
