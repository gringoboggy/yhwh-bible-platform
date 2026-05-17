# Samuel Widened-Calibration Plan (τ.6.x.4.a-W) — saved 2026-05-16

> **For the executing session:** REQUIRED SUB-SKILL — use `superpowers:subagent-driven-development`. This reuses the PROVEN 1 Samuel 1 calibration template VERBATIM, three more chapters. Steps are checkboxes.

**Status:** APPROVED & QUEUED by the user at the 1 Sam 1 gate (2026-05-16). This is the accepted **condition before any Samuel-wide Phase-2 tool**. Do NOT start Phase-2 until this plan completes and confirms the pattern.

**Why this exists.** The 1 Samuel 1 calibration (τ.6.x.4.a, COMPLETE — `dev/CALIBRATION_2026-05-16-samuel-1sa1.md`, commits `6882063`/`5a2c073`) found GG (Gunda Gundē GG-00106) and CAM (Cambridge UL MS Add. 1570) are narrative-identical (semantic 28/28) but **materially distinct recensional text-forms** (~73% both-confident, 44.75% skeleton — below the ≥90% merge bar); base witness = **CAM** (restores the GAPS source-map). User GO'd the **diplomatic-parallel** model (CAM base running text + GG per-verse apparatus; spec D1=B/D3), NOT a merged text. Condition: confirm the distinct-recension pattern + CAM-base **generalize beyond one chapter** before building Phase-2.

**Spec:** `docs/superpowers/specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md`. **Template:** the 1 Sam 1 plan `docs/superpowers/plans/2026-05-16-samuel-calibration-gate.md` (reuse its task structure, schemas, honesty contract, numeral rule, verification commands verbatim — only the chapter + images change).

## Chapters (confirmed)

| # | Chapter | Why | GG source folder |
|---|---------|-----|------------------|
| 1 | **1 Samuel 3** | Call of Samuel — short, narratively unmistakable (easy semantic anchor); early book so GG folio is near the start. | `GAPS/1_Samuel/GG-00106/1-Samuel/` (~f004–f006; **verify undamaged at locate-step**) |
| 2 | **1 Samuel 17** | David & Goliath — the spec §4-named recension **stress-test**; famously the largest LXX/MT–type divergence in Samuel → the strongest probe of "distinct recensions". | `GAPS/1_Samuel/GG-00106/1-Samuel/` (~f009–f012; verify) |
| 3 | **2 Samuel 11** | Bathsheba — a 2-Samuel narrative chapter (tests the pattern in the *other* half + a different GG quire). | `GAPS/1_Samuel/GG-00106/2-Samuel/` (f017v–f028v range; verify) |

CAM hi-res for each chapter: pull from the Cambridge CUDL IIIF endpoint per the saved method (auto-memory `cudl-iiif-access`): manifest `https://cudl.lib.cam.ac.uk/iiif/MS-ADD-01570`, id `…/MS-ADD-01570-000-{view:05d}.jp2`, region-tile the ~80MP master + stitch (single request caps 1503×2000); **the ToC mislabels the Ethiopic Reigns books — locate each chapter by VISION** (find the chapter's known narrative, not by ToC label). Reference points: 1 Sam 1 = view 215 / f106r; 1 Sam runs forward from there; 2 Sam follows 1 Sam. Save to `GAPS/1_Samuel/Cambridge-Add-1570-hires/` (Samuel) / a `2_Samuel`-appropriate hires dir for 2 Sam 11, named `MS-ADD-01570_f{NNN}_{ref}_hires.jpg`.

## Per-chapter procedure (reuse 1 Sam 1 template VERBATIM)

For EACH of the 3 chapters, run the 1 Sam 1 task sequence:

- [ ] **Locate** the chapter in GG (verify the GG folio is **undamaged**; if water/loss damaged like 1 Sam 1's col-3, note it and, if it would dominate, swap to an adjacent narratively-clear chapter and record the swap + reason).
- [ ] **Blind-transcribe GG** (isolated subagent, opus, GG images ONLY, never CAM) → `content/manuscript/samuel/calibration/{ref}_witnessGG.json`. Same Evidence schema, honesty contract (`⟦illegible⟧`⟺`illegible`), canonical numeral rule.
- [ ] **Adversarial spec+honesty review** of the GG evidence (independent subagent; fix-loop until ✅).
- [ ] **Acquire CAM hi-res** for the chapter from CUDL IIIF (controller; tile+stitch; QC the stitch + native legibility).
- [ ] **Blind-transcribe CAM hi-res** (fresh ISOLATED subagent, opus, that CAM image ONLY — no GG, no other transcription) → `{ref}_witnessCAM_hires.json`.
- [ ] **Adversarial review** of the CAM evidence (fix-loop until ✅).
- [ ] **Collate** GG vs CAM-hires + `content/notes/{book}.py` skeleton → `{ref}_collation.json`: strict / skeleton(headline) / both-confident W↔W (one consistent set of `definitions`), semantic-pass, base-witness, lacuna reconcile (every `⟦illegible⟧`⟹lacuna, excluded from agreement denom). Align by narrative content (no positional v==v).
- [ ] **Adversarial review** of the collation (independently recompute every metric from `alignment[]`; verify lacuna reconcile == evidence `⟦illegible⟧` count; fix-loop until ✅).

`{ref}` = `1sa3`, `1sa17`, `2sa11`. Evidence files are immutable.

## Aggregate decision (after all 3)

- [ ] Write `dev/CALIBRATION_2026-05-16-samuel-widened.md`: per-chapter table (semantic / both-confident / skeleton / strict / base-witness / GG-damage notes) + the 1 Sam 1 row for reference; the aggregate finding.
- [ ] **Decision rule:** if the **distinct-recension pattern holds** (both-confident materially <90%, semantic high) **and base=CAM** is consistent across chapters → **CONFIRM** the diplomatic-parallel model and proceed to size **Phase-2** (the collation tool, spec §5) to the observed failure modes; Kings then reuses Phase-2/3. If a chapter **contradicts** (e.g. ~unity agreement, or base flips to GG on undamaged folios) → STOP, surface to the user, do not assume the model.
- [ ] Local commit only (no push, no zip — project memory `save-is-local-commit`). Present the aggregate to the user (gate) before Phase-2.

## Out of scope

Phase-2 (the Samuel-wide collation tool) and Phase-3 (render + apparatus store + `manuscript-collation-tier2` provenance) — spec §5/§6 — are **not** started here; they are sized AFTER this widening confirms the pattern. Kings is untouched until Samuel Phase-2/3 is proven.

## Self-review

Reuses the proven, twice-reviewed 1 Sam 1 machinery with zero new infrastructure (only chapter + image inputs change). Independence + honesty contract + numeral rule + immutable-evidence carried verbatim. Chapter choice spans early-1Sam / the spec-named recension stress-test / a 2-Sam chapter — a deliberate breadth probe, not three easy wins. No placeholders; the decision rule is explicit and bi-directional (it can refute the model, not just confirm it).
