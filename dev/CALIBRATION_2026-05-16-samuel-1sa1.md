# 1 Samuel 1 — Ge'ez Dual-Manuscript Calibration: GO / NO-GO Report

**Project:** YHWH v2.4 — Ethiopian Tewahedo Bible publishing platform
**Pilot:** 1 Samuel 1 (the Hannah narrative), Ge'ez, two-witness calibration
**Date:** 2026-05-16
**Audience:** the publisher (no Ge'ez reading required to act on this report)
**Status of this document:** terminal calibration deliverable — the gating decision is recorded at the very bottom (`## Decision (user)`), currently `_pending_`.

> **One-paragraph executive summary.** We transcribed 1 Samuel 1 independently from two Ge'ez manuscripts and compared them. Both manuscripts tell the *same story* in every one of the 28 verses (100% semantic agreement). But at the level of the *actual words on the page* they are materially different text-forms — even on words **both** scribes wrote clearly and confidently, the two manuscripts only agree **73.05%** of the time, and across all aligned word-slots only **44.75%**. That is far below the project's "one mergeable text" bar of ≥90%. **This is not a failure of the calibration — it is the calibration working.** It tells us the correct product is a *diplomatic parallel* (one base manuscript printed as the running text, the other recorded verse-by-verse as a divergent witness), which is exactly what the design spec already anticipated. The recommended base manuscript is **Cambridge (CAM)**. See `## GO / NO-GO recommendation` for the precise, honest finding.

---

## 1. What was done

**Chapter.** 1 Samuel chapter 1 — the Hannah narrative (Elkanah and his two wives; Hannah's barrenness, vow, and prayer at Shiloh; the birth and dedication of Samuel). 28 verses.

**Approach.** This was a **data/measurement pilot only (Approach A): no production code was built.** The deliverables are three transcription evidence files, two collation files, and this report. Nothing in the publishing pipeline was modified.

**The two witnesses and their sources.**

- **GG — Gunda Gundē, manuscript GG-00106.** 1 Samuel 1 sits on folio **f003r**. Full-page scan at roughly **5 megapixels**. The third column of this page carries a **water stain over the right edge of the later verses (vv. 21–28)**, which physically destroys part of the text there.
  - Source image (as recorded in the evidence file): `GAPS/1_Samuel/GG-00106/1-Samuel/1-Samuel_f003r.jpg`
- **CAM — Cambridge University Library, MS Add. 1570.** 1 Samuel 1 is on folio **106r**.
  - **First pass (low-res, resolution-confounded):** originally transcribed from a low-resolution (~1.6 MP) crop. Source image: `GAPS/1_Samuel/Cambridge-Add-1570/Samuel01.jpg`.
  - **Re-image (authoritative):** the user enabled a hi-res re-image. The controller re-pulled the page from the **Cambridge Digital Library IIIF endpoint** — collection **CUDL `MS-ADD-01570`, view 215 = folio 106r** — **tile-stitched losslessly from the 7760×10328 IIIF master**. Images are **CC BY-NC; credit: Cambridge University Library**. **Acquired 2026-05-16.** The hi-res master is roughly **80 MP**. Source image: `GAPS/1_Samuel/Cambridge-Add-1570-hires/MS-ADD-01570_f106r_1Sam1_hires.jpg`.

**Why the re-image was necessary — the resolution confound.** In the first (low-res) collation, CAM was imaged at ~1.6 MP against GG's ~5 MP. CAM's diacritics (the seven Ge'ez vowel orders) were frequently unreadable purely because of image quality, not because the scribe wrote anything different. This **confounded** the headline disagreement: we could not tell genuine scribal/textual divergence apart from "we just can't see CAM clearly." The low-res baseline (`1sa1_collation.json`) is retained **as the documented evidence that the confound was real**: it reported CAM uncertainty at **97/442 ≈ 21.95%** with **5** illegible CAM tokens and an explicit `asymmetry_note` stating the strict number "largely measures CAM's vowel-order diacritic illegibility (image quality), not scribal variance." Re-imaging CAM at ~80 MP removes that confound so the remaining disagreement can be measured honestly.

**Independence procedure.** Each witness was transcribed by an isolated agent that saw **only its own manuscript** — GG transcriber never saw CAM, CAM transcriber never saw GG, and the hi-res CAM was re-transcribed **blind** (no access to GG or to the prior low-res CAM transcription or collation). This prevents one manuscript's reading from contaminating the other and prevents the comparison from being talked into agreement.

**Review / fix loop.** Every step had an adversarial spec + honesty review. The authoritative hi-res collation passed **two review rounds**. Two defects were caught and fixed:
1. A **lacuna mis-classification**: three GG water-stain physical-loss rows (v24 align rows 6 & 19, v25 align row 7) had been scored as substantive `disagree`; they are GG damage and were re-classed `lacuna-gg` and **excluded** from the agreement denominator. (Class tally after fix: agree 209, disagree 258, lacuna-gg 16 — was agree 209 / disagree 261 / lacuna-gg 13.)
2. A **non-like-for-like delta**: the earlier delta block compared the hi-res skeleton against the low-res file's *reduced* (segmentation-trimmed, denom 326) skeleton and wrongly reported skeleton **fell**. Recomputed under one consistent definition for both resolutions, the like-for-like skeleton in fact **rose**. The resolution confound was real and is now removed — **but removing it did not collapse the disagreement** (see `## Metrics`).

---

## 2. Metrics vs the GO bar

All numbers below were **read directly from the JSON `metrics` block of the authoritative collation** `content/manuscript/samuel/calibration/1sa1_collation_hires.json` (witness counts read from the three `1sa1_witness*.json` evidence files). Nothing here is restated from memory.

The GO thresholds are spec §4: **witness↔witness agreement ≥ 90%**, **semantic-pass ≥ 95%**, **self-flagged uncertainty ≤ 10%**.

| Metric | Hi-res value | Raw fraction | Proposed GO threshold (spec §4) | Pass? |
|---|---|---|---|---|
| **W↔W strict** (exact literal token identity / aligned pairs) | **32.55%** | 152 / 467 | ≥ 90% | **NO** |
| **W↔W skeleton — HEADLINE** (diacritic/order-folded + near-homograph-folded equality / full aligned denom) | **44.75%** | 209 / 467 | ≥ 90% | **NO** |
| **W↔W both-confident** (skeleton-equal over pairs neither scribe flagged uncertain/illegible) | **73.05%** | 187 / 256 | ≥ 90% | **NO** |
| **Semantic-pass** (verses telling the same narrative episode) | **100.0%** | 28 / 28 | ≥ 95% | **YES** |
| **Self-flagged uncertainty — CAM** (base witness; hi-res) | **16.34%** | 66 / 404 | ≤ 10% | **NO** |
| **Self-flagged uncertainty — GG** (other witness; for context) | **21.95%** | 97 / 442 | ≤ 10% | **NO** |

> **Reading the table honestly.** Semantic agreement is perfect: every verse is the same Hannah-narrative episode. **Every textual-identity metric fails the ≥90% bar, and uncertainty exceeds the ≤10% bar on both witnesses.** The "both-confident" row is the fairest single number for *genuine* divergence — it throws out every token either scribe was unsure about and every damaged token — and even there the two manuscripts agree only **73.05%**, i.e. roughly **27% genuine, confidently-read divergence**. The skeleton headline (44.75%) means **~55% of aligned word-slots differ at the word level** even after folding away vowel-order and near-homograph spelling differences.

### Like-for-like low-res → hi-res deltas (from `metrics.delta_vs_lowres`)

Both resolutions recomputed under **one identical set of definitions** (`metrics.definitions`):

| Metric | Low-res (like-for-like) | Hi-res | Delta |
|---|---|---|---|
| Strict | 24.79% (119/480) | **32.55%** (152/467) | **+7.76 pts** |
| Skeleton | 24.79% (119/480) | **44.75%** (209/467) | **+19.96 pts** |
| Both-confident | 49.42% (85/172) | **73.05%** (187/256) | **+23.63 pts** |

**One-line honest interpretation (verbatim thesis from the JSON):** re-imaging CAM (uncertainty ~44% → ~16%, its low-res illegibles resolved) **did lift agreement materially — the resolution confound was real and is now removed — but removing it did not collapse the disagreement.** GG and CAM are materially distinct recensional/scribal text-forms of 1 Samuel 1 (word order, lexical choice, contraction, divergent name spelling, segmentation), not one text imaged at two resolutions. Higher fidelity sharpened and explained the divergence; it did not erase it.

> **Provenance-only note (do not compare to the table above).** The figures *originally reported* off the low-res file under its **own different definitions** were strict **24.79%**, skeleton **52.76%** (numerator over a *reduced* 326 denominator that dropped segmentation-surplus tokens), both-confident **62.21%** (different 107/172 basis). Per `delta_vs_lowres.as_originally_reported_lowres`, these are **NOT comparable** to the hi-res figures or to the like-for-like low-res figures — they are retained for provenance/audit trail only. The earlier (now-corrected) claim that skeleton "fell −8.29 pts" was an artifact of that definition mismatch.

> **Damage is not inflating these numbers.** GG's col-3 water stain produces exactly **16 illegible tokens** (lacuna-gg), and **all 16 are excluded from every agreement denominator**. CAM has **0** illegible tokens. The both-confident metric additionally excludes every flagged token on either side, so the 73.05% / 44.75% headline figures are neither inflated nor deflated by the one-sided GG damage. The ~27% confident divergence is genuine scribal/recensional variance.

---

## 3. Collation summary

**Source:** authoritative file `1sa1_collation_hires.json`, alignment class tally and `metrics.lacuna_counts` (read from the file).

- **Aligned token-pair classes:** **agree = 209**, **disagree = 258**, **lacuna-gg = 16**.
- **Aligned denominator** (agree + disagree, lacunae excluded) = **467**.
- **Lacuna counts:** GG = **16**, CAM = **0**, both = **0**. All 16 GG lacunae are the **col-3 water-stain loss across vv. 21–28** (v21=2, v22=2, v23=2, v24=4, v25=3, v26=1, v27=1, v28=1), and are **excluded from the agreement denominators**.
- **Verses:** 28 in every file; verse range 1–28 in GG, CAM low-res, and CAM hi-res alike.

**Key qualitative finding.** The narrative is **semantically identical: 28 / 28 verses pass** — every verse in both manuscripts tells the same episode of the Hannah story. **But the two manuscripts are materially DISTINCT recensional / scribal text-forms.** They differ pervasively in word order, lexical choice (different Ge'ez words for the same idea), contraction/enclitic splitting, divine-name and personal-name spelling, and verse-segmentation drift — and the segmentation drift gets *worse in the later verses* (low-res segmentation notes record GG-vs-CAM token-count gaps growing to Δ−11 at v24, Δ−9 at v25, Δ−6 at v20/v26). This is two genuinely different copies of the chapter, not one copy seen twice.

**Concrete example divergences** (GG token ↔ CAM token, from the hi-res alignment; these are *confident* readings on both sides unless noted):

1. **v1 — patronymic/place "Zophim":** GG **ዘመንሱፉ** ↔ CAM **ዘመሴቆ** — different lexical/orthographic form of the same Ramathaim-zophim element.
2. **v1 — relative/genitive particle:** GG **ዘእምነ** ↔ CAM **እምነ**, and GG **ወስሙ** ("and his name") ↔ CAM **ዘስሙ** ("whose name") — function-word and connective divergence.
3. **v1 — ancestor name (Zuph):** GG **ኑፊብ** ↔ CAM **ፁፍ** — substantively different name spelling for the same ancestor.
4. **v2 — lexical choice "children":** GG **ደቂቅ** ↔ CAM **ውሉድ** — two different Ge'ez words for "children/offspring," same meaning.
5. **v11 — divine epithet & verb morphology:** GG **ጸባዖት** ("of hosts/Sabaoth") ↔ CAM **ኃያል** ("mighty"); GG **እህቦ** ↔ CAM **ወእሁቦ** ("[and] I will give him"); plus large segmentation divergence in Hannah's vow (GG 31 tokens vs CAM 26).
6. **v20 — opening formula:** GG **ወእምዝ** ↔ CAM **ወኮነ** ("and it came to pass"); name **ሳመኤል** (GG) ≈ **ሳሙኤل** (CAM) for "Samuel" — a spelling difference recovered as agreement only under skeleton folding.

These are representative, not exhaustive: the disagreement class holds 258 such aligned pairs.

---

## 4. Recommended base witness

**Recommended base: CAM (hi-res Cambridge Add. 1570, f106r).** Rationale read verbatim from `1sa1_collation_hires.json` → `base_rationale`:

> CAM (hi-res Cambridge Add. 1570 f106r, ~80 MP IIIF master) is recommended. On completeness it is decisively superior: CAM has **0 illegible tokens** vs GG's **16** (GG's col-3 water stain destroys the right edge of vv.21-28). On uncertainty CAM is also lower (**16.3% = 66/404**) than GG (**21.9% = 97/442**), and CAM's residual uncertainty is **lexical/orthographic at diacritic-level legibility, not physical loss**. This **RESTORES the GAPS source-map** (Cambridge = primary Samuel witness, GG = second): the prior low-res pilot inverted it to GG only because CAM was under-imaged at ~1.6 MP; with CAM re-imaged at ~80 MP that confound is gone and the source-map ordering holds on the evidence.

Note the **base recommendation flipped between pilots**: the low-res `1sa1_collation.json` recommended **GG**. That GG pick was itself a **resolution artifact** (CAM was unreadable at 1.6 MP). With CAM properly imaged, the empirically-correct base is CAM, and this **agrees with the a-priori GAPS source-map** which designates Cambridge as the primary Samuel witness.

---

## 5. Structural eyeball guide (for the user — no Ge'ez needed)

You do not need to read Ge'ez to sanity-check this calibration. Each item below ties to an exact file you can open. **Paths as recorded in the evidence files are relative to the GAPS root** `C:/Users/bogda/Documents/YHWH-v2.4-full/`; the **absolute path you can double-click is given in parentheses.**

**(a) Confirm the hi-res Cambridge page is a clean 3-column page with a red heading.**
Open `GAPS/1_Samuel/Cambridge-Add-1570-hires/MS-ADD-01570_f106r_1Sam1_hires.jpg`
(`C:/Users/bogda/Documents/YHWH-v2.4-full/GAPS/1_Samuel/Cambridge-Add-1570-hires/MS-ADD-01570_f106r_1Sam1_hires.jpg`).
**PASS looks like:** a sharp, high-resolution page laid out in **three columns**, with a **red rubricated heading block at the top of the columns**, and individual letters/diacritics crisply visible (you should be able to see tiny dots and strokes clearly even if you can't read them). This is the witness chosen as the base text.

**(b) Confirm the Gunda Gundē page is visibly damaged on the right of column 3.**
Open `GAPS/1_Samuel/GG-00106/1-Samuel/1-Samuel_f003r.jpg`
(`C:/Users/bogda/Documents/YHWH-v2.4-full/GAPS/1_Samuel/GG-00106/1-Samuel/1-Samuel_f003r.jpg`).
**PASS looks like:** a 3-column page where the **right side of the third column is visibly water-stained / discoloured / damaged**. This damage is *why* GG has 16 unreadable words in the later verses (21–28) — and it is why GG was **not** chosen as the base, and why those damaged words were excluded from the scoring rather than counted as disagreements.

**(c) Confirm both transcriptions cover the whole chapter (~28 verses).**
The evidence files record exactly **28 verses each** (verse range 1–28): GG = **28 verses / 442 tokens** (`1sa1_witnessGG.json`), CAM hi-res = **28 verses / 404 tokens** (`1sa1_witnessCAM_hires.json`), CAM low-res = **28 verses / 400 tokens** (`1sa1_witnessCAM.json`). **PASS looks like:** all three say 28 verses; neither manuscript is missing the chapter.

**(d) Confirm the per-verse meaning reads as one coherent Hannah story.**
Open `content/manuscript/samuel/calibration/1sa1_collation_hires.json` and skim the `verses[].semantic_note` lines (one per verse, plain-English paraphrase, e.g. v20: *"In due time Hannah conceived and bore a son, named Samuel, for she asked him of the LORD"*; final verse: *"Therefore I lend/give him to the LORD all the days of his life; and he worshipped the LORD there"*).
**PASS looks like:** reading the 28 notes top-to-bottom tells the recognizable Hannah → vow → birth of Samuel → dedication story, with **every** note marked `"semantic_pass": true`.

**(e) Confirm the two pages are visibly different hands / layouts.**
Compare the two images from (a) and (b) side by side.
**PASS looks like:** they are **clearly two different manuscripts** — different scribal handwriting, different page layout/proportions, different ruling — *not* two scans of the same page. This is the visual counterpart of the central finding: these are two distinct witnesses, which is exactly why the numbers in `## Metrics` show real textual divergence rather than ~100% agreement.

> **Overall eyeball PASS:** (a) clean sharp 3-column Cambridge page with red heading; (b) visibly damaged right-of-column-3 on the Gunda Gundē page; (c) both ≈28 verses; (d) 28 coherent Hannah-story notes all `semantic_pass:true`; (e) two visibly distinct hands. If all five hold, the evidence behind this report is structurally sound and the GO/NO-GO finding below can be trusted.

---

## 6. GO / NO-GO recommendation

This is presented as the genuine **multi-part finding** it is, not a forced single yes/no. All gating numbers were read from `1sa1_collation_hires.json` `metrics`.

**(i) Against the spec §4 GO bar AS LITERALLY WRITTEN — which presumed "one text, two witnesses, mergeable" — the verdict is NO-GO** for producing a single merged / normalized reconstructed Ge'ez text of Samuel from these two manuscripts:
- W↔W skeleton **44.75%** and even W↔W both-confident **73.05%** are **far below the ≥90%** bar; strict is **32.55%**.
- Self-flagged uncertainty is **16.34%** (CAM, base) and **21.95%** (GG), both **above the ≤10%** bar.
- Mechanically merging or normalizing GG and CAM into one text would **misrepresent the manuscripts**, because ~27% of confidently-read, undamaged tokens genuinely diverge (word order, lexis, contraction, name spelling, segmentation). There is no honest single "the Ge'ez text" to print from this pair.

**(ii) Independently, the verdict is GO for CAM hi-res as a standalone Samuel base text:**
- **100%** semantic pass (28/28), **0** illegible tokens, residual uncertainty **~16%** that is **lexical/orthographic at diacritic-level legibility, not physical loss**, imaging at diacritic resolution (~80 MP IIIF master), and the **GAPS source-map is restored** (Cambridge = primary Samuel witness). CAM on its own is a sound, legible, complete base for 1 Samuel 1.

**(iii) Recommended path — a diplomatic parallel.** Publish **CAM as the base running Ge'ez text**, with **GG recorded as a divergent second witness in a per-verse apparatus**. This is **not a workaround** — it is exactly what the design spec already anticipated: **D1 = B (text + two-witness apparatus)** and **D3 (base witness + apparatus, base chosen empirically)**. This pilot has now *empirically chosen the base* (CAM) and *empirically established that an apparatus is required* (the divergence is real). **Frame this as a SUCCESSFUL, honest calibration outcome:** the pilot's job was to discover the correct product model for Ge'ez Samuel, and it did — the answer is "diplomatic parallel, CAM base," not "merge." A 100%-semantic / ~73%-confident-textual result that cleanly resolves the product model is a calibration that worked, not one that failed.

**(iv) Explicit condition before scaling Samuel-wide.** Do **not** generalize a recension-level conclusion from a single chapter — especially one where GG lost vv. 21–28 to a water stain. **Before committing the diplomatic-parallel model across all of Samuel, widen the pilot to ≥ 2–3 more chapters** (ideally including chapters where GG is undamaged) to confirm the divergence pattern and the CAM-base choice hold beyond 1 Samuel 1. One chapter is a thin basis for a book-wide recensional claim.

---

## 7. If NO-GO — offramps

The merge-model NO-GO maps onto spec §4's offramps as follows, with the design implication of each:

**(a) Higher-resolution CAM offramp — ALREADY EXERCISED.** Spec §4's first offramp ("re-image the weaker witness at higher resolution") has been *done*: CAM was re-pulled at ~80 MP from the CUDL IIIF master. It **worked** in the sense that it removed the resolution confound (CAM uncertainty ~44% → ~16%; like-for-like agreement rose +7.76 / +19.96 / +23.63 pts). **But it did not convert the merge-model to GO**, because it revealed that the residual disagreement is *genuine recensional/scribal divergence*, not image quality. This offramp is spent; there is no further resolution lever on CAM.

**(b) Adopt the diplomatic-parallel model — RECOMMENDED.** Treat CAM as base text + GG as a recorded second witness in a per-verse apparatus (spec D1=B / D3). **No further data is needed for the *model decision*** — the evidence already determines it. The only open item is *confidence at scale*, addressed by (c).

**(c) Widen the calibration to more chapters — RECOMMENDED.** Run the same independent-transcription + collation pilot on **≥ 2–3 additional Samuel chapters** (prefer chapters where GG is undamaged, to test the divergence pattern without the col-3 water-stain confound). This validates that "CAM base + GG apparatus, materially divergent" generalizes before any Samuel-wide production commitment.

**(d) Optionally source a third / published Ge'ez Samuel as a tie-breaker witness.** A third independent witness (e.g. a published critical Ge'ez Samuel) would let the apparatus adjudicate GG-vs-CAM divergences (majority / oldest-reading logic) rather than merely record them. Optional, not required for the model decision.

**Recommendation: (b) + (c)** — adopt the diplomatic-parallel model now (the data already mandates it), and widen the calibration to 2–3 more chapters before scaling Samuel-wide. (d) is a worthwhile later enhancement; (a) is exhausted.

---

## Decision (user): _pending_
