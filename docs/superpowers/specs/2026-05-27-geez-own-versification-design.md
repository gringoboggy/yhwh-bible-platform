# Ge'ez own-versification collation & standalone-Bible design

**Created:** 2026-05-27. **Status:** architecture approved (brainstormed + user-approved this session); implementation plan to follow (`docs/superpowers/plans/2026-05-27-geez-own-versification-plan.md`).

**Supersedes:** the *structural* use of the KJV verse spine in the manuscript collation path. KJV is retained ONLY as a secondary cross-reference, never as the Ge'ez Bible's structure.

**Companions:** `docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md` (witness transcription/review mechanics — UNCHANGED), `dev/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md` (the two-standalone-Bibles north star), `dev/CLAUDE_PROJECT_RULES.md` §1.

---

## 1. Problem & motivation

The standalone Ge'ez Bible — a north-star goal: *"a full version with its own books and chapters"* — was being collated onto the **KJV verse spine**. KJV is a 66-book Protestant/Masoretic canon: it lacks the Ethiopian-only books entirely (Mäqabyan I–III, Jubilees, 1 Enoch, 4 Baruch, …), and even for shared books like Kings it imposes a **Masoretic versification foreign to the Ge'ez/LXX "3–4 Kingdoms" recension** the manuscripts actually follow.

The implementation had drifted from the original spec intent (KJV as a *semantic anchor / sanity check*) into **KJV-as-structure**: `manuscript_collation._map_objects_to_spine` proportionally bins each witness's sense-units onto `load_kjv_skeleton`'s N rows, and `manuscript_qa._SEMANTIC_PASS_FLOOR = 95` *penalizes* a recension for not filling all KJV slots.

**1 Kings 6 surfaced the category error:** CAM has 33 sense-units, GG 18, KJV 38 → 5 KJV rows are unfillable → 86.84% "semantic fail", despite **0 fabrication** and faithful, adversarially-reviewed witnesses. The data was honest; the *frame* was wrong — it measured a Ge'ez recension against a Masoretic ruler and called the difference a defect.

**Decision (user, 2026-05-27):** the standalone Ge'ez Bible is structured on the **Ge'ez tradition's OWN versification (PRIMARY)**; KJV becomes a maintained **SECONDARY cross-reference** wherever the book exists in KJV.

---

## 2. Key facts grounding the design (codebase research, this session)

- The KJV-coordinate assumption is **global**, baked at three layers:
  1. **Ingest** — `scripts/extract_parallel_pdf.py::renumber_against_floor` *discards* the recension's own chapter/verse labels and refills KJV-derived `*_VERSE_COUNTS` floors. The current Ge'ez store is KJV-*reshaped*, not merely KJV-aligned.
  2. **Translation store** — `scripts/core/translations.py` keys every verse on `(chapter, verse)` with no versification-scheme attribute.
  3. **Build / popups** — the base HTML (`epub_working/`) is KJV-numbered WEB text; popups attach by KJV coordinate; `generate_verse_popups.py` skips any book lacking a KJV source ("Ethiopic-only — deferred").
- **An own-versification precedent already exists:** Ge'ez **Psalms** was ingested with `source_authoritative: true` and **skips** `renumber_against_floor`, keeping its own Rahlfs/LXX numbering. This is the model to generalize.
- The **witness JSONs store each manuscript's OWN sense-unit numbering** (GG `v:1..N`, CAM `v:1..M`); the KJV projection happens *downstream* inside `collate()`. Therefore **re-collation is mechanical from the existing witnesses — zero re-transcription.**
- The **standalone build path is unbuilt**: `content/editions.yaml` has `standalone-geez` / `standalone-amharic` records (`standalone: true`, `base_translation: geez-tewahedo`) but `build_edition.py` only *skips* them; `base_translation` is read by nothing. Greenfield.
- **Biggest risk = source data, not code:** Samuel & Kings are NOT in the Ge'ez store (the marathon IS their ingest); the other 15 store books are KJV-renumbered ocr-tier3 (~53–67% coverage) and need re-ingest from versification-preserving sources for true own-numbering.

---

## 3. Architecture — five layers (evidence → standalone Bible)

### 3.1 Evidence (immutable, unchanged)
The blind-transcribed, adversarially-reviewed witness JSONs at `content/manuscript/<track>/calibration/<ref>_witness{GG,CAM_hires}.json`, each in its OWN sense-unit numbering. **Sacrosanct — never re-transcribed.** The marathon's C-1…C-6 transcription/review mechanics (and the blindness + honesty contract) are UNCHANGED.

### 3.2 Collation (re-architected) — `scripts/core/manuscript_collation.py`
`collate()` produces a **base-witness-structured** collation:
- **Primary verses = the base witness's sense-units.** Base chosen by the existing `_pick_base` decision-of-record (CAM by default; the fuller witness on a material-extent split). For 1ki6: CAM's 33 units ARE the 33 Ge'ez verses.
- **The other witness aligns to the base by Ge'ez↔Ge'ez `align_verse`** (the existing Needleman-Wunsch fold-skeleton aligner — same-language, feasible) → an apparatus per base verse (agree / disagree / lacuna / insertion).
- **Drop `_map_objects_to_spine`'s proportional KJV-binning** for the primary structure (it remains only as a fallback used by nothing in the new path).
- **Retained HARD gates:** token-conservation (every witness token appears exactly once), lacuna-honesty (apparatus lacunae == witness `⟦illegible⟧` count), no-fabrication.
- **Metrics become Ge'ez-internal:** witness-agreement % + lacuna counts. **KJV-coverage is recorded as an *informative* cross-ref statistic (via §3.3), NOT a pass/fail floor.** `_SEMANTIC_PASS_FLOOR` is replaced by: "every base sense-unit has legible content OR an honest lacuna, and the other witness's tokens are all conserved."
- **Output shape** (`<ref>_collation.json`, re-shaped): `{book, chapter, base_witness, base_rationale, primary_verses: [{geez_v, geez_text, tokens, apparatus: [{base, other, class}], flags}], kjv_xref, metrics}`.

### 3.3 Cross-reference (new tool) — `scripts/core/geez_kjv_xref.py`
Partial cross-language anchoring (FULL Ge'ez→English semantic matching stays out of scope — the paid model is de-scoped):
- **Hard anchors:** numerals (Ge'ez ፬፻፹ → 480 via a Ge'ez-numeral parser) + proper nouns (transliteration match: ሰሎሞን↔Solomon, ግብጽ↔Egypt, ሊባኖስ↔Lebanon, ኪሩብ↔cherub) matched against the KJV verse text, plus any reviewer-note KJV references parsed where present.
- **Order-preserving interpolation** fills the unanchored base verses between hard anchors.
- **Confidence per mapping:** `anchored` (a hard token matched) vs `interpolated` (positional). Recorded honestly — interpolation is never presented as certainty.
- **Output:** a sidecar `kjv_xref: {geez_v: {kjv: [(book,ch,v),…], confidence}}` folded into the collation and (later) the store. **NEVER written into the immutable witnesses.**
- **Ethiopian-only books** (no KJV): the xref is simply absent — the Ge'ez stands alone.

### 3.4 Store (own-versification)
The standalone Bible's text store keyed to **Ge'ez's own numbering**, generalizing the Psalms `source_authoritative: true` precedent (skip `renumber_against_floor`):
- **Samuel/Kings:** the store is GENERATED from the base-structured collations (§3.2) — each base verse → a store verse at its own `(ch, geez_v)` coordinate, carrying the EN back-translation + the KJV xref.
- **Loader change:** add an explicit `versification` attribute to the translation-store model (`own` vs the default canonical-KJV) in `scripts/core/translations.py` — small + localized.
- The 15 existing KJV-renumbered store books need re-ingest for own-versification (Phase D, data-gated).

### 3.5 Render (new path)
A `standalone: true` branch in `build_one` (or a dedicated `scripts/build_standalone.py`) that:
- Renders the Ge'ez Bible body **from the own-versification store** (Ge'ez verse N as the spine — NOT the KJV-numbered base HTML).
- Popups carry: the EN back-translation (from the Ge'ez wording) + the KJV cross-reference ("KJV ref: 1 Kings 6:1") + the apparatus (other-witness variants) as study notes.
- Reuses the EPUB/OPF/matter/cover infra (`build_epub.py`, `patch_opf`, matter pages).
- **The 9 KJV editions are untouched** — the byte-stable invariant is preserved (they never read the standalone path).

---

## 4. Phased build sequence (clean-first, data-risk-last; parallelism noted)

- **Phase A — collation engine re-architecture + re-collate.** Re-shape `collate()` to base-witness-primary; re-collate the **10 done chapters** (1ki1–6 + the 4 Samuel goldens 1sa1/1sa3/1sa17/2sa11) from existing witnesses. **The 4 Samuel `*_collation.json` calibration GOLDENS stay byte-stable** (new base-structured outputs go to clearly-named new files) so the engine-vs-hand invariant + `TestCalibrationInvariants` don't break. Embarrassingly parallel (per-chapter pure function). **No data risk.**
- **Phase B — the geez→kjv cross-ref tool** (§3.3) + apply to the re-collated chapters. Parallel per chapter. Honest confidence tagging.
- **Phase C — the standalone render path** (§3.5) + the first standalone Ge'ez Bible EPUB from Samuel/Kings (+ Psalms, which already has own-versification). End-to-end proof of the pipeline.
- **Phase D — own-versification re-ingest of the 15 KJV-renumbered store books** (data-gated: the GAPS folder + clean PD critical editions per SCOPE §3/§4). Book-by-book as sources confirm. The real risk, isolated last.
- **Cross-cutting — RULES codification:** the no-shortcuts principle + the never-single-thread / side-task-automation rule (§8).

**Why this order:** Phases A–C carry **no data risk** (the marathon witnesses + the Psalms precedent suffice) → a complete, correct standalone Ge'ez Bible for Samuel/Kings ships *without* waiting on source acquisition; the data-gated breadth comes in D.

**The marathon continues** (witness transcription for the remaining Kings/Samuel chapters) — but from now it feeds **base-witness-structured** collations, so 1ki6's "fail" simply dissolves.

---

## 5. Error handling & honesty gates
- **Token conservation** (HARD) — unchanged.
- **Lacuna honesty** (apparatus lacunae == witness `⟦illegible⟧`) — unchanged.
- **No fabrication** (no output text absent from a witness) — unchanged, cardinal.
- **Cross-ref confidence honesty** — `anchored` vs `interpolated` explicitly tagged; interpolation never shown as certainty.
- The marathon's blind-transcription + adversarial-review honesty contract — UNCHANGED.

## 6. Testing
- Keep the 4 Samuel calibration goldens as the immutable engine-vs-hand reference; add NEW base-structured expectation tests (the base structure is deterministic from the witnesses).
- Re-collation regression per chapter: token conservation, lacuna honesty, base-pick, apparatus completeness.
- Cross-ref unit tests: the Ge'ez-numeral parser, the proper-noun transliteration matcher, interpolation monotonicity, confidence tagging; anchor cases drawn from 1ki6 (v1 = 480; vv11–12; v38 = 11th-year completion).
- Standalone render: a build smoke (the Ge'ez Bible EPUB builds + epubcheck 0/0) + the 9-editions-byte-stable proof.

## 7. Scope boundaries
- **IN:** the collation re-architecture (§3.2), the cross-ref tool (§3.3), the own-versification store model (§3.4) + the standalone render path (§3.5), the re-collation of the 10 done chapters (Phase A), the RULES codification (§8).
- **IN (data-gated, Phase D):** re-ingest of the 15 store books for own-versification.
- **OUT (for now):** the Amharic standalone Bible's full ingest (same architecture applies; sequenced after the Ge'ez proof); the paid cross-language translation model (de-scoped); any change to the 9 KJV editions.

## 8. Cross-cutting rules (to codify this session)
- **No shortcuts / completeness-first.** There is time. Any task may be **paused** to do it right and complete. If a **better, more-complete** approach appears, **stop and re-plan** (thought-out, optimized, reorganized) rather than patching forward. Elevate to a top-level RULES principle.
- **Never single-thread / side-task automation.** Always run **≥2 lanes**; when one side task completes, **auto-pick the next** from a maintained side-task backlog (CAM hi-res pre-pulls, base-structured re-collations, cross-ref anchoring, code-debt tail, doc-coherence, Phase-D source acquisition, …). Codify the backlog + the auto-pick rule so the project never idles a single lane.

---

## 9. Phase C — resolved decisions (2026-05-28, brainstormed + user-approved)

Phase C is detailed + locked this session; its implementation plan is `docs/superpowers/plans/2026-05-28-geez-standalone-render-plan.md`. The §3.4–§3.5 architecture is unchanged — these decisions resolve the open points and refine two specifics.

1. **EN back-translation = pipeline-first; EN as the next lane (user, 2026-05-28).** No own-versification content has English yet (`geez-tewahedo-en` holds only ocr-tier3 `gen`/`ex`/`lev`; Psalms + the 10 collated Kings/Samuel chapters have none). So Phase C ships the render path + proof EPUB with popups = **KJV cross-ref + variant apparatus** (data that already exists from Phases A/B), and the faithful EN back-translation (agent path + adversarial review, generalizing the Track-F method to own-vers content) follows as the **immediate next lane**, folded into the popups after. The render path must exist before EN can be wired regardless; this gives EN its own careful reviewed pass. The north-star "popups carry the EN of the actual Ge'ez wording" is unchanged — only **sequenced**. EN is **explicitly absent** in the first proof, **never faked from KJV**.

2. **`versification` is PER-BOOK, not per-store (refines §3.4).** `geez-tewahedo` is a mixed store: `psa` (HaCohen critical edition) + the new Kings/Samuel = `own`; the other 32 ocr-tier3 books stay `canonical` until Phase D re-ingest. Implement as a `VERSIFICATION` book-module attribute (default `"canonical"`, opt-in `"own"`), read by `translations.versification_of(translation, book)` + surfaced in `translation_meta`. Default-unset = byte-identical for the 9 KJV editions + every existing translation.

3. **Render architecture = dedicated `scripts/build_standalone.py` (refines §3.5).** It GENERATES the Ge'ez body XHTML from the own-vers store (Ge'ez verse *N* is the spine — there is no KJV-numbered base HTML to inject into), attaches per-verse popups (xref + apparatus), then reuses the shared `build_epub`/`patch_opf`/matter/cover machinery. build-all/matrix routes `standalone: true` editions here. Chosen over a `standalone: true` branch inside `build_one` so the 9-KJV-editions path is **literally untouched** and cannot regress the byte-stable invariant.

4. **C2 store output.** The driver reads each `<ref>_collation_v2.json` → `content/translations/geez-tewahedo/{1ki,1sa,2sa}.py` (`VERSES=[(ch, geez_v, geez_text)]` at the base witness's own coordinate, `VERSIFICATION="own"`) + a `<book>_apparatus.json` sidecar carrying per-verse `kjv_xref` + apparatus for the popups. Collations only — the 4 Samuel goldens + the immutable witnesses are untouched.

5. **First proof EPUB content (C4).** The 10 collated Kings/Samuel chapters (full pipeline: collation→store→xref→apparatus→render) + Psalms (a complete own-vers book; a cheap Ge'ez→KJV Psalms xref pass reusing the Phase-B tool gives its popups real cross-refs, since LXX vs KJV Psalms numbering genuinely diverges). Gate: `epubcheck 0/0` + the 9-editions-byte-stable proof (regen + `git diff`).

**Phase-C result (2026-05-28):** all of the above shipped + verified — proof EPUB `standalone-geez` = 4 books / 161 chapters, popups = KJV xref + apparatus (NO English yet), epubcheck 0/0/0/0; the 9 KJV editions byte-stable (`epub_working/` untouched; catholic-study epubcheck 0/0/0/0). The SDD review caught + fixed a faithfulness bug (Ps 36 non-adjacent dup verses must render in source order). Commits 5e8afdc8→89e3b59b. Phase D's "cheap flag-only wins" were **refuted** on verification — the 6 patrologia books are KJV-renumbered (COLOMETRIC-MERGE) and need real re-ingest, like the ocr-tier3 books.

---

## 10. EN back-translation lane — resolved decisions (2026-05-28, brainstormed + user-approved)

The standalone Ge'ez Bible's signature feature (§3.5, RULES §1): its verse popups carry a **faithful English back-translation of the actual Ge'ez wording** — never the KJV, never a scholarly claim. Phase C deliberately sequenced this as the **next lane** (pipeline-first, §9.1). Detailed plan: `docs/superpowers/plans/2026-05-28-geez-en-backtranslation-plan.md`. Proof-first: **1 Kings 6** end-to-end, then scale at the user's pace.

1. **Method = careful + adversarial review (agent-path; user, 2026-05-28).** A **translator** subagent reads the clean own-vers Ge'ez (`geez-tewahedo/<book>.py`, source order) and renders each verse into faithful English; a **reviewer** subagent independently checks each verse for faithfulness (drift, over-reach, KJV-contamination, fabricated certainty where the Ge'ez is `⟦illegible⟧`/uncertain); the translator revises to convergence — mirroring the manuscript marathon's R1/R2 rigor. No paid API (Claude Max subagents, the established Track-F method, now *reviewed*). The English is faithful to the **Ge'ez wording**, NOT KJV/NRSV-aligned.

2. **Store + tier.** Lands in the existing `content/translations/geez-tewahedo-en/` store as `<book>.py` (`VERSES=[(ch, geez_v, english)]`), keyed on the **same own-vers coordinates** as the Ge'ez body (a mixed-coordinate store, like `geez-tewahedo` — each EN book matches its source book's numbering). A NEW provenance tier — `ai-back-translation-reviewed-tier3` (clean source + adversarial review, a notch above the gen/ex/lev `ai-back-translation-tier4` OCR back-translations) — registered in `scripts/core/provenance_tiers.py`.

3. **Render wiring.** `standalone-geez` already declares `popup_translation: geez-tewahedo-en`. The standalone renderer (`build_standalone._render_vnote`) looks up the EN for each verse and, when present, emits a `<p class="vnote-text">` English para in the vnote popup — alongside the existing KJV xref + apparatus. The standalone GENERATES vnotes, so it emits the EN para directly (no post-pass). The 9 KJV editions never render the standalone path → unaffected. The popup labels the English as the back-translation reading-aid (honest framing; the tier is the provenance record).

4. **Honesty gates (cardinal).** English faithful to the Ge'ez (reviewer-enforced), NOT KJV. Labeled an AI reading-aid (the `tier3` provenance), not a scholarly translation. Verse-by-verse alignment with the Ge'ez body (same coords). Where the manuscript marked a verse illegible/uncertain, the English says so (brackets) — never fabricates certainty.

5. **Proof scope = 1 Kings 6 (33 verses).** Translate + adversarial-review → `geez-tewahedo-en/1ki.py` (ch 6) → wire the renderer → rebuild the standalone EPUB → confirm the English appears in the 1ki6 popups → `epubcheck 0/0` + the 9-editions-byte-stable invariant holds. Then check in before scaling (Kings/Samuel ≈324 verses, then Psalms ≈2,522).

6. **Full-scope note (deferred to the scaling step).** Dup-verse chapters (e.g. Ps 36's non-adjacent 24/25/24/25, per the Phase-C fix) need the EN keyed by source-order position, not just `(ch, v)`, so the two distinct verses get their two distinct English. The proof (1 Kings 6, unique verse numbers) does not hit this; the render's `chapter_verses_in_source_order` already iterates in source order, so the EN lookup must align to that iteration (an occurrence index), addressed when Psalms is scaled.

---

## 11. Phase D — resolved decisions (2026-05-28, brainstormed + user-approved)

Phase D (§4, §7) is the data-gated own-versification re-ingest of the 32 KJV-renumbered `geez-tewahedo` store books. These decisions resolve its open points (scope, source mapping, ordering, honesty/deferral); the §3.4 own-vers-store architecture is unchanged. Detailed implementation plan to follow: `docs/superpowers/plans/2026-05-28-geez-phase-d-reingest-plan.md`.

**Store state (verified on disk 2026-05-28).** 36 books: **4 already `own`** (`psa` via HaCohen/Ludolf; `1ki`/`1sa`/`2sa` via the marathon collations) + **32 KJV-renumbered** needing re-ingest — 6 `patrologia-printed-tier1` + 26 `ocr-tier3` (`parallel-bible-eotc`).

1. **Scope = clean-source-first + distinctive-source acquisition (user, option B).** Three streams:
   - **D1 — ready sources (8 books).** The 6 Patrologia books (`1ch`,`2ch`,`ezr`,`neh`,`est_patrologia`,`job`) — their Patrologia-Orientalis PDFs are already on disk under `GAPS/` — plus `sir` (51 ch) and `wis` (19 ch) from the authorized HaCohen/TAU site (the exact path that produced Psalms; not yet cached).
   - **D2 — distinctive acquisition (parallel background lane).** Acquire clean PD Geʽez critical editions for the uniquely-Tewahedo books: **1 Enoch** (Charles, *The Ethiopic Version of the Book of Enoch*, 1906) and **Jubilees** (Charles, *Maṣḥafa Kufālē*, 1895) first — highest uniqueness value, PD by age, findable on archive.org — then **Meqabyan I–III** and **4 Baruch** pending a clean-source check.
   - **Deferred (18 OCR-only).** The narrative OT (14: `gen`,`ex`,`lev`,`num`,`deu`,`jos`,`jdg`,`rut`,`est`,`2es`,`tob`,`jdt`,`bar`,`bel`), Prayer of Azariah (`paz` — HaCohen carries it only embedded in Daniel, not separately addressable), and the NT (`mat`,`phm`,`jud`) have ONLY the OCR-garbled `parallel-bible-eotc` PDF. Faithful own-versification is not recoverable from garbled OCR, so they stay `ocr-tier3`/canonical, **excluded from the own-vers standalone Bible**, documented honestly, and revisited only if a clean source is acquired. Never force-converted (forcing it = the KJV-numbering category error this redesign fixed, or fabricated verse boundaries). (The 6 Ethiopian-only books `1en`/`jub`/`mq1-3`/`4ba` are NOT in this deferred set — they are the D2 acquisition targets above. Tally: D1 8 + D2 6 + deferred 18 = 32.)

2. **Source map (on-disk verified 2026-05-28).**

   | Group | Books | Source edition | Location |
   |---|---|---|---|
   | Patrologia | `1ch`,`2ch` | PO-23 fasc-4 Grébaut 1932 | `GAPS/3_Chronicles/…Grebaut_1932.pdf` (47 MB) |
   | Patrologia | `ezr`,`neh` | PO-13 fasc-5 Pereira 1919 | `GAPS/4_Ezra-Nehemiah/…Pereira_1919.pdf` (31 MB) |
   | Patrologia | `est_patrologia` | PO-9 fasc-1 Pereira 1913 | `GAPS/5_Esther/…Pereira_1913.pdf` (40 MB) |
   | Patrologia | `job` | PO-2 fasc-5 Pereira 1907 | `GAPS/6_Job/…Pereira_1907.pdf` (40 MB); HaCohen cross-validates |
   | HaCohen | `sir`,`wis` | HaCohen/TAU digitized critical editions | fetchable (authorized); cache `content/translations/sources/hacohen-geez/` |
   | Acquire (D2) | `1en`,`jub`,`mq1-3`,`4ba` | Charles 1906/1895 + TBD per book | web (archive.org), calibrate-first GO/NO-GO |

3. **Architecture — generalize `source_authoritative` (refines §3.4).** One principle across all source families: *trust the source edition's own versification; do NOT call `renumber_against_floor`; emit `VERSIFICATION="own"`.* (Accuracy note: the §9 "COLOMETRIC-MERGE" label for the patrologia books was imprecise — they are KJV-renumbered via `extract_patrologia_pdf`'s `renumber_against_floor` wrapper over `canonical_book_shape`; the remedy is the same either way: bypass the floor-renumber, preserve the source's numbering.) Per family:
   - **Patrologia** — add a `source_authoritative` path to `scripts/extract_patrologia_pdf.py` that preserves the PO edition's own chapter/verse structure instead of the `canonical_book_shape` floor-renumber.
   - **HaCohen (`sir`,`wis`)** — add per-book parsers beside `parse_hacohen_psalter` (the 2026-05-16 external-source design built this to extend) → fetch→cache→parse→`source_authoritative`, calibrate-first per book.
   - **Distinctive (D2)** — per-source parsers for the acquired Charles editions; same `source_authoritative` output.
   - **Common output:** each book → `content/translations/geez-tewahedo/<book>.py` (`VERSIFICATION="own"`, a provenance tier matching its source class — patrologia-printed / digitized-critical-edition / a new one for the Charles editions) + a Geʽez→KJV xref sidecar via the Phase-B tool where KJV exists (Ethiopian-only books have no KJV → no xref; they stand alone). The standalone renderer picks each up by adding it to `build_standalone._STANDALONE_BOOKS`.

4. **Ordering — proof-first, safest-first (RULES §3, sequencing delegated to Claude).**
   1. **Proof = Esther (`est_patrologia`)** end-to-end (PDF on disk, self-contained): re-ingest own-vers → store + apparatus → Geʽez→KJV xref → add to the standalone → rebuild EPUB → `epubcheck 0/0` + the 9-editions byte-stable proof. Validates the generalized Patrologia `source_authoritative` path on one book before scaling.
   2. **Batch the rest of D1** — the other 5 Patrologia (`job` early, since HaCohen cross-validates it) + `sir`/`wis` (HaCohen).
   3. **D2 acquisition runs as a background lane throughout** (never-single-thread, RULES §2.5): verify+fetch 1 Enoch / Jubilees → calibrate-first GO/NO-GO → ingest as each confirms.
   4. **EN back-translation follows per book as its own reviewed lane** (the Psalms/Kings translator+reviewer method, §10) — pipeline-first, EN-next; not blocking the own-vers ship.

5. **EN back-translation = following lane, not inline (consistent with §9.1/§10).** Each newly own-versified book gets its faithful EN back-translation (translator + independent reviewer subagents, tier `ai-back-translation-reviewed-tier3`) AFTER its own-vers ship, at the user's pace — so the own-vers Bible grows in book-breadth first, with EN trailing per book.

6. **Two-Esther resolution.** The store has both `est` (`ocr-tier3`, parallel-PDF) and `est_patrologia` (Patrologia). The standalone Bible uses the own-versified `est_patrologia`; the `ocr-tier3` `est` is superseded for the standalone (it remains available for any KJV-coordinate consumer). Final book-code/canon wiring is a plan detail.

7. **Honesty gates (cardinal, unchanged).** 0 fabrication · calibrate-first GO/NO-GO per book (the source structure must parse cleanly or the book is deferred — never a silent renumber) · xref confidence tagged `anchored`/`interpolated` · each module records the exact edition, editor/digitizer, PD basis, fetch/ingest date, and tier · the 9 KJV editions stay byte-stable (they never enter `build_standalone`) · the witnesses + 4 Samuel goldens are immutable.

8. **Scope boundaries / non-goals.** No change to the 9 KJV editions or any non-`geez-tewahedo` translation. The Amharic standalone Bible (same architecture) stays sequenced after the Geʽez breadth. The paid cross-language model stays de-scoped. Deferred OCR-only books are not force-converted. D2 acquisition is bounded to user-authorized PD sources; a book with no clean source is deferred, not faked.

**⚑ Correction (2026-05-28, post-feasibility-check — supersedes decisions 3-4 for the Patrologia path + the proof book).** Reading the actual `scripts/extract_patrologia_pdf.py` + the shipped `est_patrologia.py` revealed the PO PDFs are **scans with no text layer**, extracted by **Tesseract OCR** — which LOSES the margin Ethiopic verse-numerals and bleeds the French apparatus footnotes into the verse text (`est_patrologia.py` v1:2 is half editor's variant-notes). So the PO's own versification was **never captured** and cannot be "preserved" by a `source_authoritative` flag-bypass. The 6 Patrologia books therefore need a **vision-transcription lane** (an Opus vision agent reading the PO page images: capture the margin Ethiopic numerals + the Geʽez body, exclude the French apparatus) — feasible and *easier* than the manuscript marathon (clean printed critical edition, not a scribal hand), but a **heavier lane**, not a flag. The **HaCohen path stays clean + proven** (it produced Psalms from clean Unicode Geʽez with correct verse numbers). Re-scope: **D1a = HaCohen (`wis`, `sir`) — the clean/ready lane + the proof; D1b = Patrologia (6 books) — vision-transcription lane (gets its own detailed plan at its start).** The **proof book switches from Esther to Wisdom of Solomon (`wis`, 19 ch, HaCohen)** — validates the full own-vers pipeline (per-book parser → own-vers store → Geʽez→KJV xref → standalone render → epubcheck 0/0 → 9-editions byte-stable) on a clean source, fast. (User-approved 2026-05-28.) Implementation plan: `docs/superpowers/plans/2026-05-28-geez-phase-d-reingest-plan.md`.
