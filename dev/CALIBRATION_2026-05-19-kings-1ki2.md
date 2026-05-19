# 1 Kings 2 — Kings Dual-Manuscript Collation + base SURFACE-TO-USER resolution (τ.6.x.4.c)

**Project:** YHWH v2.4 — Ethiopian Tewahedo Bible publishing platform
**Chapter:** 1 Kings 2 (David's death-charge to Solomon; Adonijah/Abishag executed; Abiathar banished; Joab killed at the altar; Shimei confined then executed; the kingdom established).
**Date:** 2026-05-19
**Status of this document:** Per-chapter record. **NOT** a GO/NO-GO gate (Kings does not re-run a calibration gate — the diplomatic-parallel + base=CAM model was user-ratified 2026-05-17 for the GG-00106 + Cambridge Add. 1570 family; C-10 is 1 Kings 1 only). This doc exists because the shipped Phase-2 engine raised its **§3.3 clause-3 SURFACE-TO-USER** flag on this chapter and that must never be resolved silently.

> **One line:** Engine `_pick_base` clause-1 recommended base=GG; conservative re-verification proved this a **segmentation-granularity artifact, not missing scripture**; **user decision 2026-05-19 = keep base=CAM per the ratified 2026-05-17 decision-of-record**, recorded as an honest surfaced WARN (not a floor breach). Marathon continues.

---

## 1. What was done (C-4 … C-9)

- **C-4 acquire CAM hi-res.** 1 Kings 2 (CAM) located by vision = folios **f126v → f127r**. Both full ~80 MP CUDL IIIF masters were already on disk from the 1ki1 pull (folio-identity double-confirmed, f106r=view215 anchor, zero drift); reused as byte-identical `_1ki2_` copies — no fresh pull needed.
- **C-5 blind CAM transcription.** Isolated opus transcriber, CAM hi-res ONLY (no GG, no skeleton). Produced `content/manuscript/kings/calibration/1ki2_witnessCAM_hires.json`.
- **C-6 adversarial CAM review — converged in 3 rounds → APPROVED** (the 1ki1-CAM / 1ki2-GG precedent pattern):
  - **R1 (2 CRITICAL + systematic):** a homoeoteleuton drop (eye skipped between the two `ውስተ መቃብር`, losing ≈1 Kings 2:7–9 — the Barzillai-kindness + Shimei-son-of-Gera/Bahurim/Mahanaim/Jordan-oath charge); a fabricated dittography in old v15; a chapter-wide divine-name harmonization (`እግዚእብሔር` written as printed `እግዚአብሔር`, 19 occ.); plus enumerated `አ↔እ`/`ላ↔ለ` harmonizations.
  - **R2 (1 CRITICAL-bounded + 1 MAJOR + 3 sub-glyph):** the restored span verified faithful/complete/segmented; 9 of 11 fix parchment-over-reviewer overrides upheld; remaining: v4 `በሐቀ`→`በሐቀን`, v17 `ሐማም`→`ሕማም`, three sub-glyph normalizations.
  - **R3 (convergence check): APPROVED** — all 5 fixes faithful on-page, no regression (boundaries exact, restored span continuous/complete, divine-name sweep correct, de-dittography intact), validator `OK`, screen `CLEAN`.
  - CAM witness immutable + checkpoint-committed `b0d939e`. **27 verses** (coarse `✣ ክፍል` liturgical sectioning), 803 tokens, 0 illegible.
  - (GG witness 1ki2 = 46 verses, 777 tokens, immutable `c3db778` — approved in a prior session at C-3 R4.)
- **C-7 collate** via the shipped Phase-2 tool → `content/manuscript/kings/collation/1ki2_collation.json`.
- **C-8 adversarial collation review — APPROVED.** Every metric independently recomputed **byte-identical** to the engine's emitted `metrics`; **token-conservation exact** (GG 777/777, CAM 803/803, multiset-equal AND order-exact, 0 lost/duplicated); lacuna-honest (0/0/0, no fabricated agreement); semantic 46/46 genuine (spot-checked, no vacuous passes); base fields present & honest.

---

## 2. Metrics (read from `1ki2_collation.json` `metrics`; C-8-verified byte-identical)

| Metric | 1 Kings 2 | Basis | Reading |
|---|---|---|---|
| Semantic-pass | **100.0%** | 46 / 46 | every canonical spine verse narratively present |
| W↔W strict | 5.44% | 65 / 1195 | distinct recension |
| W↔W skeleton | 8.37% | 100 / 1195 | distinct recension |
| W↔W both-confident | 26.36% | 97 / 368 | materially < 90% → distinct recension (not ≈unity) |
| Self-flagged uncertainty | 1.42% | 11 / 777 (base=GG) | low |
| Lacuna counts | gg 0 · cam 0 · both 0 | — | nothing illegible; no fabrication possible |
| Base (engine `_pick_base` clause-1) | **recommended GG** | — | see §3 — segmentation-granularity artifact |

---

## 3. The base SURFACE-TO-USER event and its resolution

**Engine output (honest, left byte-identical — not mutated, per `no-reassert-ratified-bar` + the Samuel byte-identical contract):**
`base_witness_recommended = "GG"`; `base_rationale` = *"GG transmits the more complete recension (GG 46v vs CAM 27v; shorter < 0.70x longer -> material extent split, spec-revision 2026-05-17 §3.3 clause 1). base=CAM remains the project decision of record (2026-05-17 GO). SURFACE-TO-USER: clause 1 selected a non-CAM base; flag for the user, never a silent flip (§3.3 clause 3)."*

**Conservative re-verification (memory `feedback_reverify_conservative_nogo` — re-checked the engine's signal AND the optimistic counter-read with real data):**
- Clause-1 compares the **segment/verse COUNT** ratio as an extent proxy: CAM 27 / GG 46 = 0.587 (< 0.70 → trips).
- **True scripture extent (token count): CAM 803 / GG 777 = 1.033** — CAM is marginally *longer*, not materially shorter.
- semantic_pass 46/46 = 100%; lacuna 0/0/0; CAM C-6-adversarially-certified **complete** (the only real omission — the homoeoteleuton Barzillai/Shimei-Gera span — was caught at C-6 R1 and restored; make-or-break boundary check passed at R3).
- C-8 token-conservation: all 803 CAM tokens present in the collation alignment, order-exact; the 19 empty-`cam_tokens` spine rows `[3,5,8,10,13,15,17,20,22,25,27,30,32,34,37,39,42,44,46]` are CAM's coarser `✣ ክፍል` sections bundling ≈2 canonical verses each — the CAM text for those spine verses is present in the immediately preceding CAM-bearing row, **not absent**.
- **Conclusion:** the GG recommendation is a **segmentation-granularity artifact** of the verse-count-ratio heuristic, not a genuine material-extent shortfall. The ratified 2026-05-17 base=CAM decision-of-record remains philologically correct (distinct recension: both-confident 26.36% ≪ 90; CAM complete; semantic-identical narrative).

**User decision (2026-05-19):** **Keep base = CAM**, per the ratified 2026-05-17 decision-of-record. Recorded as an **honest surfaced WARN** (per `no-reassert-ratified-bar`: surface honestly, do not treat a ratified-model artifact as a per-build floor breach, do not mutate the shipped engine mid-marathon). The standalone Ge'ez Bible keeps CAM running text + GG per-verse apparatus for 1 Kings 2, consistent with 1 Kings 1 and the 2026-05-17 GO. The engine's `_pick_base` clause-1 heuristic (verse-count proxy mis-firing on segmentation granularity) is a candidate for a **separate, post-marathon** engine-precision cleanup run with the Samuel-equivalence regression — out of this marathon's scope, exactly as the 1ki1 cosmetic `lacuna_counts_note` WARN was deferred.

---

## 4. Consequence

base=CAM (decision-of-record) for 1 Kings 2. Manifest `1ki:2` → `calibrated`. Marathon continues continuously to the next queued chapter (1 Kings 3); no further user check-in (the model is ratified; this surfaced-WARN is now resolved and recorded). Witness JSONs immutable (GG `c3db778`, CAM `b0d939e`); collation + manifest + this doc committed together at C-9.
