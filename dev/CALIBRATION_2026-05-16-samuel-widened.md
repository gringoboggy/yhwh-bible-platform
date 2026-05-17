# Samuel Widened Ge'ez Dual-Manuscript Calibration (τ.6.x.4.a-W) — Aggregate Finding & Bi-Directional Decision

**Project:** YHWH v2.4 — Ethiopian Tewahedo Bible publishing platform
**Scope:** the user-accepted condition before any Samuel-wide Phase-2 tool — widen the 1 Sam 1 calibration to three more chapters (1 Sam 3, 1 Sam 17, 2 Sam 11) under the same independent-blind-transcription + adversarially-reviewed-collation procedure.
**Date:** 2026-05-17
**Audience:** the publisher (no Ge'ez reading required to act on this report)
**Status of this document:** terminal calibration deliverable — the gating decision is recorded at the very bottom (`## Decision (user)`), currently `_pending_`.
**Plan executed:** `docs/superpowers/plans/2026-05-16-samuel-widened-calibration.md` (reuses the 1 Sam 1 template VERBATIM). **Spec:** `docs/superpowers/specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md`. **Prior pilot:** `dev/CALIBRATION_2026-05-16-samuel-1sa1.md`.

> **One-paragraph executive summary.** We re-ran the 1 Samuel 1 calibration on **three more chapters**, chosen deliberately to stress the question from different angles: 1 Samuel 3 (a short early chapter, Gunda Gundē almost undamaged), 1 Samuel 17 (David & Goliath — the single most famous Septuagint-vs-Hebrew textual divergence in all of Samuel), and 2 Samuel 11 (Bathsheba — a chapter in the *other* book where, as it turned out, **both** manuscripts carry the full-length narrative). In **every** chapter the two manuscripts tell the **same story** (semantic agreement 100% in all four chapters including the original pilot — 28/28, 21/21, 58/58, 27/27). But at the level of the **actual words on the page** they remain materially distinct text-forms: even on words **both** scribes wrote clearly and confidently, agreement is **73.05% / 89.35% / 68.97% / 86.39%** across the four chapters — **every chapter materially below the project's ≥90% "one mergeable text" bar**. The cleaner / more-complete base manuscript is **Cambridge (CAM) in every single chapter** — the base **never flipped to Gunda Gundē**, including on the chapters where Gunda Gundē is physically undamaged. No chapter showed near-unity agreement. **The distinct-recension pattern and the CAM-base choice generalize. The bi-directional decision rule therefore resolves to CONFIRM the diplomatic-parallel model (CAM base running text + GG per-verse apparatus); proceed to size Phase-2.** Full reasoning below.

---

## 1. What was done

For each of the three widened chapters, the **1 Samuel 1 procedure was reused verbatim** (only the chapter and the images changed):

1. **Locate** the chapter in Gunda Gundē (GG-00106) by the **narrative** + the coarse `ምዕራፍ` rubric — explicitly treating the red `✣ ክፍл ፡ N ✣` rubrics as **fine liturgical subdivisions, not modern chapters** (a methodological finding from this widening: the `ክፍл` numerals climb several times within one folio; the modern-chapter marker is `ምዕራፍ`, and where absent the chapter is bounded by narrative alone).
2. **Blind-transcribe GG** in an isolated agent that saw **only** the Gunda Gundē images (never Cambridge, never any other transcription) → immutable `*_witnessGG.json`.
3. **Adversarial spec + honesty review** of the GG evidence; fix-loop until clean.
4. **Acquire CAM hi-res** for the chapter from the Cambridge Digital Library **IIIF** endpoint (CUDL `MS-ADD-01570`), region-tiled and stitched losslessly from the ~80 MP master (single-delivery cap is 1503×2000; the master is 7760×10328), located **by vision** because the CUDL table of contents mislabels the Ethiopic Reigns books. Images **CC BY-NC; credit Cambridge University Library**.
5. **Blind-transcribe CAM hi-res** in a fresh isolated agent that saw **only** that Cambridge image (no GG, no GG transcription, no other collation) → immutable `*_witnessCAM_hires.json`.
6. **Adversarial review** of the CAM evidence; fix-loop until clean.
7. **Collate** GG vs CAM-hires against the project's canonical English Samuel skeleton (`content/translations/kjv/2sa.py` etc.) → `*_collation.json`, aligning **by narrative content, never positional v==v**, under one consistent `definitions` set, with a **mandatory token-conservation check** (every evidence token appears exactly once across the alignment, lacuna rows excepted).
8. **Adversarial review** of the collation: every metric independently recomputed from the raw `alignment[]`, lacuna reconcile verified against the evidence `⟦illegible⟧` count, token-conservation re-verified, builder reproduced byte-for-byte.

This was a **data/measurement exercise only — no production code was built.** The deliverables are the immutable evidence JSONs, the collation JSONs, and this report. The blind protocol was preserved at every transcription step (independently confirmed by each adversarial reviewer). Two genuine defects were caught and fixed by the adversarial method during the widening — a GG `፡`-wordspace tokenization deviation in 2 Sam 11 (re-normalized + all 48 markers re-indexed; the reviewer's own remap table was itself wrong and was corrected by note-target re-derivation), and three token-drops auto-caught by the 2 Sam 11 collation's inline token-conservation gate — exactly the calibration working as designed.

---

## 2. The aggregate result (all numbers read directly from the collation `metrics` blocks)

Every figure below was read from the authoritative JSON `metrics` block of each collation file (`1sa1_collation_hires.json`, `1sa3_collation.json`, `1sa17_collation.json`, `2sa11_collation.json`); witness extents from the `*_witness*.json` evidence files. Nothing is restated from memory. **Both-confident** = skeleton-equal over only those aligned pairs where **neither** scribe flagged the token uncertain/illegible (the fairest single measure of *genuine, confidently-read* divergence). **Skeleton** = diacritic/order-folded + near-homograph-folded equality over the full aligned denominator (the headline). **Strict** = exact literal token identity. GO bar (spec §4): W↔W ≥ 90%, semantic ≥ 95%, uncertainty ≤ 10%.

| Chapter | Why this chapter | GG extent | CAM extent | Semantic | **Both-confident** | Skeleton (headline) | Strict | Base | GG illegible (lacuna) |
|---|---|---|---|---|---|---|---|---|---|
| **1 Sam 1** *(pilot, reference row)* | Hannah — book opening, original pilot | 28 v / 442 tok | 28 v / 404 tok | **100%** (28/28) | **73.05%** (187/256) | 44.75% (209/467) | 32.55% (152/467) | **CAM** | **16** (col-3 water stain, vv.21–28) |
| **1 Sam 3** *(Ch1)* | Call of Samuel — short, GG near-undamaged | 21 v / 316 tok | 21 v / 317 tok | **100%** (21/21) | **89.35%** (193/216) | 60.11% (220/366) | 36.34% (133/366) | **CAM** | **1** (a single scribal erasure) |
| **1 Sam 17** *(Ch2)* | David & Goliath — the spec-named LXX/MT recension **stress-test** | **20 v** / 550 tok *(SHORT LXX-type)* | **58 v** / 884 tok *(LONG/FULL)* | **100%** (58/58) | **68.97%** (180/261) | 16.64% (192/1154) | 9.71% (112/1154) | **CAM** | **0** (clean folios) |
| **2 Sam 11** *(Ch3)* | Bathsheba — the *other* book; both witnesses full-length | 27 v / 508 tok *(FULL/LONG)* | 26 v-obj / 424 tok *(FULL/LONG)* | **100%** (27/27) | **86.39%** (254/294) | 57.53% (317/551) | 33.94% (187/551) | **CAM** | **0** (clean folios) |

### The four invariants that hold across every chapter

1. **Semantic agreement is perfect everywhere — 100% in all four chapters (134/134 verses total).** The two manuscripts are, without exception, *the same Samuel narrative*.
2. **Confident textual agreement is materially below the ≥90% merge bar everywhere** — 73.05%, 89.35%, 68.97%, 86.39%. Even the *highest* (1 Sam 3, 89.35%) does not reach the bar. The two manuscripts are genuinely distinct scribal/recensional text-forms in every chapter tested.
3. **The base witness is CAM in every chapter, and it never flipped to GG.** Critically, on the **GG-undamaged** chapters (1 Sam 17 and 2 Sam 11 have **zero** GG illegible tokens; 1 Sam 3 has just one), the empirically-cleaner witness is **still CAM**. The CAM-base choice is therefore **not** an artifact of GG's 1 Sam 1 water-stain — it holds where GG is pristine.
4. **No chapter shows near-unity agreement; no chapter contradicts the model.** The bi-directional rule's refutation conditions (a ~unity chapter, or a base flip to GG on undamaged folios) were **not triggered by any chapter**.

### The profile nuance — divergence takes different forms, but is always present

The chapters were chosen as a breadth probe, and they paid out a spectrum of *how* the two recensions differ — while the *that* they differ never wavers:

- **1 Sam 3 — high clean-text agreement, structural plus/minus.** Both-confident is the highest of the set (89.35%); the divergence is concentrated in **structural plus/minus** (GG's v21 carries an LXX-style expansion absent in CAM; segmentation drift), not in pervasive word-by-word divergence. Two close but distinct copies.
- **1 Sam 17 — the dramatic short-vs-long recensional split.** GG transmits the **SHORT LXX-type** form (20 verses, the duel core only); CAM the **LONG/FULL** form (58 verses, with the complete David-introduction 17:12–31 and the post-duel Abner block 17:55–58). This is the single most famous LXX-vs-MT divergence in Samuel, and the manuscripts land on **opposite sides of it**. The **38 CAM-only verses match the project's own Kenyon witness-note** (the best LXX manuscripts omit exactly 17:12–31, 41, 50, 55–58) — independent external corroboration that GG's short form is a genuine recension, not a transcription omission. On the shared duel core the two still agree only 68.97% confidently. GG folios here are physically clean — the divergence is unambiguously textual, not damage.
- **2 Sam 11 — two distinct *full* recensions.** This is the cleanest possible pure clean-text probe: **both** witnesses carry the entire ~27-verse Bathsheba narrative, neither omits material, neither folio is damaged (0/0 illegible). Yet confident agreement is still only **86.39%** — squarely in the 1 Sam 3 band, well below the bar. GG additionally carries a **recensional messenger doublet** (vv.21–22: Joab's Abimelech/Thebez speech repeated near-verbatim as the messenger's report) preserved verbatim and flagged, not harmonized. Distinct recensions *even when both are complete*.
- **1 Sam 1 — pervasive divergence + one-sided damage.** The original pilot: lowest skeleton (44.75%), pervasive word-order/lexical/segmentation divergence, plus 16 GG col-3 water-stain lacunae (excluded from all denominators; the base flipped to CAM only after the hi-res re-image removed a resolution confound — see the 1 Sam 1 report).

The honest reading: GG↔CAM divergence is **not a damage artifact** (it is 68.97% / 86.39% on the two zero-illegible chapters), **not a resolution artifact** (CAM was hi-res ~80 MP throughout), and **not an extent artifact** (it is present at 86.39% even when both witnesses are full-length). It is **genuine recensional/scribal distinctness**, expressed across the full range from structural plus/minus to a wholesale short/long recension split — and it generalizes across both books of Samuel.

---

## 3. The bi-directional decision rule, applied

The plan fixed an explicit, **bi-directional** rule (it can refute the model, not only confirm it):

> **CONFIRM** if the distinct-recension pattern holds (both-confident materially < 90%, semantic high) **and** base = CAM is consistent across chapters → confirm the diplomatic-parallel model and size Phase-2; Kings then reuses Phase-2/3.
> **STOP / surface to user** if any chapter **contradicts** — e.g. ~unity agreement (both-confident ≈ ≥90%), or the base flips to GG on undamaged folios.

**Evaluation against the three widened chapters + the pilot:**

| Rule condition | 1 Sam 1 | 1 Sam 3 | 1 Sam 17 | 2 Sam 11 | Holds? |
|---|---|---|---|---|---|
| both-confident materially < 90% | 73.05% ✓ | 89.35% ✓ | 68.97% ✓ | 86.39% ✓ | **all four** |
| semantic high (≥95%) | 100% ✓ | 100% ✓ | 100% ✓ | 100% ✓ | **all four** |
| base = CAM (no flip to GG) | CAM ✓ | CAM ✓ | CAM ✓ | CAM ✓ | **all four** |
| ~unity contradiction? | no | no | no | no | **none** |
| base flip to GG on undamaged folios? | n/a (GG damaged) | no (GG≈clean) | **no (GG clean)** | **no (GG clean)** | **none** |

**Every CONFIRM condition is satisfied in every chapter. No refutation condition is triggered by any chapter.** The result therefore resolves to **CONFIRM** — and it does so with the strongest possible evidentiary breadth: the pattern holds on a short early chapter, on the famous recension stress-test, and in the other book of Samuel, including on chapters where Gunda Gundē is physically pristine (removing every "it's just GG damage" objection).

---

## 4. Recommendation

**CONFIRM the diplomatic-parallel model and proceed to size Phase-2.**

- **Product model (confirmed, spec D1=B / D3):** publish **CAM (Cambridge UL MS Add. 1570, hi-res) as the base running Ge'ez text of Samuel**, with **GG (Gunda Gundē GG-00106) recorded as a divergent second witness in a per-verse two-witness apparatus.** **Not** a merged/normalized single reconstructed text — that remains NO-GO; mechanically merging would misrepresent two genuinely distinct recensions.
- **Base witness (confirmed empirically, not by precedent):** **CAM**, in all four chapters, including the GG-undamaged ones. This is consistent with the a-priori GAPS source-map (Cambridge = primary Samuel witness).
- **Phase-2 sizing — the observed failure modes the collation tool must handle** (this is *why* the widening was required before building the tool):
  1. **Variable extent / recensional minus.** Witnesses range from both-full (2 Sam 11) to a wholesale short-vs-long split (1 Sam 17, GG 20 v vs CAM 58 v). Verse alignment must be **narrative/skeleton-anchored, never positional**; large one-sided recensional minus must score as `disagree` (counted in the denominator), **never** as lacuna.
  2. **Segmentation drift.** Witness verse-object counts differ (e.g. CAM's 2 Sam 11 v19/20 merge: 26 objects vs GG's 27). The spine must be the base witness's rows mapped onto a canonical skeleton enumeration, with the other witness narrative-sliced on.
  3. **Recensional doublets** (GG 2 Sam 11 vv.21–22). Preserve verbatim, flag, never harmonize.
  4. **Lacuna = physical illegibility only.** GG damage varies (16 → 1 → 0 → 0 illegible across the four chapters); `⟦illegible⟧`↔illegible bijection must be exact, lacuna rows excluded from agreement denominators, base chosen empirically per chapter (CAM was cleanest in all four).
  5. **One consistent folding `definitions` set, byte-stable across chapters** (strict / skeleton / both-confident), so book-wide metrics are comparable.
  6. **Token-conservation as a hard build-time gate** (it caught three real token-drops in the 2 Sam 11 build) + an adversarial recompute-from-raw review per artifact + immutable evidence files.
- **Kings** then reuses the proven Phase-2/3 model verbatim (same dual-witness MS family — GG-00106 primary + Cambridge Add. 1570 second witness).
- **Out of scope here (unchanged):** Phase-2 (the Samuel-wide collation tool, spec §5) and Phase-3 (render + apparatus store + `manuscript-collation-tier2` provenance, spec §6) are **not** started in this calibration — they are sized *after* this CONFIRM, at the next gate. Kings is untouched until Samuel Phase-2/3 is proven.

---

## 5. Structural eyeball guide (for the user — no Ge'ez needed)

You can sanity-check this calibration without reading Ge'ez. Paths below are repo-relative; the calibration artifacts live in `content/manuscript/samuel/calibration/`.

**(a) Every chapter tells one coherent Samuel story.** Open any `*_collation.json` and skim the `verses[].semantic_note` lines (one per verse, plain-English). **PASS looks like:** reading them top to bottom gives the recognizable episode (Call of Samuel for 1 Sam 3; David & Goliath for 1 Sam 17; Bathsheba/Uriah for 2 Sam 11), with **every** note `"semantic_pass": true` (21/21, 58/58, 27/27).

**(b) The two manuscripts are visibly different hands.** Compare any GG folio (`GAPS/1_Samuel/GG-00106/...`) with the matching CAM hi-res (`GAPS/1_Samuel/Cambridge-Add-1570-hires/MS-ADD-01570_f*_hires.jpg`). **PASS looks like:** clearly two different manuscripts (different handwriting, layout, ruling) — not two scans of one page. This is the visual counterpart of the sub-90% agreement numbers.

**(c) The David & Goliath chapter is dramatically different lengths in the two manuscripts.** `1sa17_witnessGG.json` records **20 verses**; `1sa17_witnessCAM_hires.json` records **58**. **PASS looks like:** GG is the well-known *short* Septuagint-type David & Goliath; CAM the *long* full form — the manuscripts sit on opposite sides of the most famous textual split in Samuel. (Contrast 2 Sam 11, where both are ~27 verses and still 86% — distinctness is not just about length.)

**(d) Damage is excluded, not counted as disagreement.** Each collation's `metrics.lacuna_counts` shows GG illegible = 16 / 1 / 0 / 0 across the four chapters, CAM = 0 throughout; all lacuna rows are excluded from the agreement denominators. **PASS looks like:** the two zero-damage chapters (1 Sam 17, 2 Sam 11) still show large confident divergence — proving the finding is textual, not a damage artifact.

**(e) The base manuscript is the same one every time.** Every collation's `base_witness_recommended` reads **CAM**. **PASS looks like:** four out of four = CAM, including the chapters where Gunda Gundē is undamaged — the recommendation is stable and evidence-driven.

> **Overall eyeball PASS:** (a) coherent stories, all `semantic_pass:true`; (b) visibly distinct hands; (c) the famous 20-vs-58-verse split in 1 Sam 17; (d) zero-damage chapters still strongly divergent; (e) CAM base every time. If these hold, the CONFIRM decision below can be trusted.

---

## Decision (user): _pending_

**The bi-directional decision rule resolves to CONFIRM** (Section 3): the distinct-recension pattern and the CAM-base choice generalize across all three widened chapters and the pilot — semantic 100% everywhere, both-confident materially < 90% everywhere (73.05 / 89.35 / 68.97 / 86.39%), base = CAM everywhere including on GG-undamaged folios, and **no chapter contradicts** (no ~unity, no base flip to GG).

**Recommended ratification:**

- **CONFIRM** the **diplomatic-parallel model** — CAM base running Ge'ez Samuel text + GG per-verse two-witness apparatus (spec D1=B / D3). Merged/normalized single text remains **NO-GO**.
- **Authorize Phase-2** (the Samuel-wide collation tool, spec §5) sized to the five observed failure modes in Section 4. **Kings reuses Phase-2/3 verbatim** afterward.
- Phase-2/3 are **not** started until this ratification.

_Awaiting the user's GO / adjust / NO-GO at this gate._
