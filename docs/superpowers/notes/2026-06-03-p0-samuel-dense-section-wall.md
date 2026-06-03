# P0 Samuel folio-mapping — the dense-section wall + a foliation finding (2026-06-03)

> Autonomous P0 session note (Windows lane, baton held by Mac for the website — this is file-disjoint P0 work + a docs note, not a truth-record edit). Captures a genuine method limitation hit while folio-mapping 1 Samuel, plus a reliable foliation correction.

## What got mapped reliably this session
- **1sa 2** — GG backfilled from the existing witness JSON (CAM still needs IIIF). Reliable.
- **1sa 4–6** — full GG + CAM, vision-verified, HIGH confidence (distinctive content: ark / Ashdod / Dagon / Beth-shemesh / Kirjath-jearim). Committed.
- **1ki 6** — backfilled from existing witness JSONs (both witnesses). Reliable.
- **1sa 7–11** — committed but **PROVISIONAL** (see the wall below): GG/CAM 7:1 onsets were HIGH confidence (Kirjath-jearim, Mizpeh/Ebenezer), but 8/9/10/11 were ~70–75% (rubric-cadence + weak content), and a second careful CAM pass later contradicted the f110r assignment. Treat 1sa 7–11 as best-effort, **re-verify before/at transcription**.

## The foliation finding (reliable — USE THIS)
A careful CAM pass (81 tool calls, 4× zoom on the 7760×10328 masters) READ the penned recto folio numbers and confirmed:
- **CAM view→folio: 2 views per leaf, arithmetic HOLDS.** Anchor f106r = view 215. Odd view = recto (penned number, top-right under the inked "ነገሥት" header, at y≈0.10–0.14 — *below* the scale bar, which is why naive top-edge crops miss it); even view = verso (unnumbered, shares the leaf number). Verified: view221=f109r, 223=f110r, **225=f111r, 227=f112r, 229=f113r** (penned "109/110/111/112/113" read directly; view225/226/227 are byte-identical to the pre-existing f111r/f111v/f112r files).
- **★ Calibration label bug:** the 1sa17 calibration witness labels its images `f111r/f111v/f112r_1Sam17`. Careful content reading puts **1 Sam 15 on f111r** (Saul's confession 15:24, Agag hewn at Gilgal 15:33) and the **1 Sam 17 (David & Goliath) onset on f111v→f112r** (David + the Philistine + the lion/bear speech 17:34-36). So the calibration's *folio-number labels* for 1sa17 are likely off by ~one chapter-cluster. The transcribed 1sa17 CONTENT validated + collated, so the images do contain ch17 — only the folio sigla need a re-check. **Action: re-verify the `content/manuscript/samuel/manifest.yaml` 1sa17 CAM folio labels (f111r→?) and the calibration witness `folio_sigla` before relying on them.**

## The wall: why per-chapter mapping breaks in the dense middle
Two careful passes (51 and 81 tool calls) produced **conflicting and geometrically impossible** per-chapter folio assignments for 1sa 7–16:
- Pass A (7–11): f110r ≈ 1sa 11–12.
- Pass B (12–17): f110r ≈ 1sa 9; 1sa 10–15 all on f110v (≈140 verses on three columns — impossible).
Root causes:
1. **Recurring landmark phrases.** The Saul/Samuel/Philistine/Amalek narrative repeats the exact anchors we key on ("Samuel said to all Israel", "Amalek", "the Philistines", Mizpeh, Gilgal) across many chapters → content-matching mis-attributes folios.
2. **LXX versification.** The Ge'ez follows the LXX (1 Kingdoms), whose chapter/verse divisions differ from the KJV/MT we anchor against (esp. 1 Sam 17–18, ~45% shorter in LXX). So "KJV chapter N" is not a clean target in the manuscript.
3. **Density.** The script is dense + variable (28 v/side at 1sa1 vs ~10–19 elsewhere), so verse-count arithmetic can't disambiguate either.

**Conclusion:** precise per-chapter folio-mapping by KJV-landmark vision is reliable for *distinctive-content* chapters (1–6, 17, 31, named-event chapters) but **NOT** for the dense repetitive middle. P0's premise (cheaply pre-map folios *before* transcription) partly breaks there — you essentially must read the text to know the boundaries, which is the transcription itself.

## Recommended approaches (user decision)
1. **Fold mapping into transcription** for the dense runs: map a generous folio *range* per contiguous chapter-block (e.g. "1sa 7–11 ⊂ GG f005v–f007v, CAM f108v–f110v") and let the dual-witness transcription assign verses to chapters as it reads. (Coarser manifest granularity, but honest + robust.)
2. **Anchor on a digital Ge'ez/LXX 1 Samuel** reference text (if obtainable) instead of KJV — matches the actual recension + versification, removing the recurring-KJV-phrase ambiguity.
3. **Distinctive-only precise mapping:** precisely map only the distinctive-content chapters; leave the dense runs as ranges.

## Artifacts on disk (gitignored GAPS, kept for whoever resolves this)
CAM masters acquired this session: f107v, f108r, f108v, f109r, f109v, f110r, f110v (views 218–224) + views 225–230 (= f111r–f113v, folio-neutral names `MS-ADD-01570_view2NN_hires.jpg`). GG Samuel f003–f010 already on disk.
