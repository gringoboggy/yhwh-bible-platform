# Samuel & Kings — dual-manuscript Ge'ez collation: design spec

**Date:** 2026-05-16
**Status:** DESIGN APPROVED (brainstorming complete; pre-implementation).
**Relationship:** sub-effort of the standalone-Ge'ez-Bible end-state
(`dev/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md` +
`CLAUDE_PROJECT_RULES.md` §1). This fills the parallel-Bible PDF's
Ge'ez gap for the two books the French Patrologia Orientalis PDFs
do NOT cover, and feeds the standalone Ge'ez Bible.

---

## 1. Problem & context

The τ.6.x/τ.7.x parallel-Bible work ingests a *printed* parallel
Ge'ez–Amharic PDF (OCR / vision text-layer). Samuel & Kings are
**not** in a usable form there — their Ge'ez must come from
**handwritten manuscript folios** the user has cropped into
`C:\Users\bogda\Documents\YHWH-v2.4-full\GAPS`:

- **Samuel** — two independent witnesses:
  - Witness GG: `GAPS/Samuel/01_1-Samuel/` (30 imgs, f003r–f017v) +
    `02_2-Samuel/` (23 imgs, f017v–f028v) — the GG 00106 hand
    (Gunda Gundē, "all-in-one" historical-books MS).
  - Witness CAM: `GAPS/Samuel/1-2_Samuel__Cambridge_Add1570/`
    (40 imgs, Samuel1–40) — Cambridge MS Add. 1570 (1588–89 CE),
    CC BY-NC, credit Cambridge University Library.
- **Kings** — two witnesses (same pattern):
  `GAPS/Kings/1-2_Kings__GG106_primary/` +
  `1-2_Kings__Cambridge_Add1570_2nd_witness/`.

Both are careful 3-column Ethiopic **book hands** with red
rubrication; the Cambridge witness also carries marginal notes.
This is a **manuscript-collation** problem, not an OCR run. The
project's existing Ge'ez OCR (Tesseract `script/Ethiopic` + the
parallel-PDF text-layer) is print-trained and will not read these
hands. The realistic transcription engine is **direct vision
transcription** (the model reading each folio image) plus
**dual-witness collation** — the standard textual-critical method.

The other GAPS books (Chronicles, Ezra, Nehemiah, Esther, Job)
come from the French Patrologia Orientalis printed bilingual
critical editions — a much easier OCR target, handled on a
separate track, OUT OF SCOPE here.

---

## 2. Locked decisions (the decision record)

| # | Decision | Choice |
|---|----------|--------|
| **D1** | Deliverable scope | **B** — reconstructed Ge'ez verse text **+ a per-verse two-witness critical apparatus** (the apparatus is the "study notes"). |
| **D2** | Accuracy / calibration gate | **B** — always-on semantic-skeleton cross-check **+ a sample go/no-go gate** before scaling. **No external published Ge'ez reference** is available; the gate is the semantic check plus a structural eyeball of a calibration sample. |
| **D3** | Witness-disagreement policy | **A** — base-witness running text + apparatus; disciplined eclectic fallback when the base has a clear scribal slip/lacuna and the other witness is sound (always recorded). The **calibration sample empirically picks the base witness**. |
| **Approach** | Pipeline shape | **A** — **calibrate first**, then build a dedicated collation tool sized to what calibration revealed, then render via the proven τ.7.x conventions. |

Marginalia transcription (the rejected D1 option C) is **out of
scope** for this design; it may be a later pass once D1=B is proven.

---

## 3. Architecture & phasing

Inputs: Witness GG + Witness CAM + the project's existing
English/known Samuel verse skeleton (the semantic anchor).

- **Phase 1 — Calibration gate** (no tooling built). Transcribe one
  chapter from each witness by vision, semantic-check, measure,
  present sample, **GO/NO-GO**, pick base witness.
- **Phase 2 — Collation tool** (only if GO; sized to Phase-1
  findings). Folio manifest → per-folio transcription records →
  collation engine → reconciled text + apparatus → QA report.
- **Phase 3 — Render & integrate.** Reconciled Ge'ez Samuel →
  `geez-tewahedo/1sa.py` + `2sa.py` via the τ.7.x conventions;
  apparatus stored alongside; feeds the standalone Ge'ez Bible +
  fills the parallel-PDF Ge'ez Samuel gap.

**Kings reuses Phases 2–3 verbatim** after Samuel proves the
template.

**Proposed phase tag:** a new Ge'ez-stream sub-track
**`τ.6.x.4`** "manuscript-collation Ge'ez gap-fill" (τ.6.x.2 =
parallel-PDF Ge'ez catchup; .4 = manuscripts). Sub-phases:
`τ.6.x.4.a` = Samuel calibration gate, `τ.6.x.4.b` = Samuel
tool + render, `τ.6.x.4.c` = Kings, … The final letter is owned
by the user / `dev/PLAN_2026-05-09.md` per the §5 sticky-letter
rule; `τ.6.x.4` is a proposal, confirmable at spec review.

---

## 4. Phase 1 — Calibration gate (`τ.6.x.4.a`)

**Calibration chapter:** **1 Samuel 1 (Hannah & Samuel's birth).**
The book opening → trivial to locate on the first page of both
witnesses; narratively unmistakable → strongest possible semantic
check; recension-stable (no Hebrew/Ethiopic versification
ambiguity). Alternative stress-test on user request: 1 Samuel 17
(David & Goliath). Adjustable at spec review.

**Flow:**
1. Transcribe ch. 1 from Witness GG (vision; structured per verse;
   explicit `⟦damaged⟧` / `⟦illegible⟧` / `⟦?word⟧` markers).
2. Transcribe ch. 1 from Witness CAM **independently** (no
   cross-reading between the two).
3. Semantic-skeleton check: does each transcribed Ge'ez verse
   plausibly mean what Samuel 1:N is known to say (using the
   project's existing English Samuel + the known text)?
4. W↔W collation of the chapter (a preview of the real apparatus).
5. Compute the three honest metrics (below).
6. Present the sample to the user (page image + transcription +
   collation + English-sense), reviewable without reading Ge'ez.
7. **GO/NO-GO.** The cleaner / more-complete / more-legible
   witness for Samuel becomes the **base** (D3), decided
   empirically here — not assumed.

**The metric — honest by construction.** With no external
gold-standard text (D2), no true "accuracy %" is claimable. The
gate measures three things that are genuinely measurable:

- **W↔W agreement** — % of words where the two independent
  scribal copies match (high agreement ⇒ strong evidence both,
  and the reading, are right).
- **Semantic-pass** — % of verses whose transcription coherently
  matches the known Samuel content.
- **Self-flagged uncertainty** — % of tokens marked unsure
  (should cluster on visibly damaged spans, not clean text).

**Proposed GO bar (adjustable at spec review):** W↔W agreement
≥ 90% (word level) AND semantic-pass ≥ 95% of verses AND
self-flagged uncertainty ≤ 10% of tokens (and concentrated on
damage) AND the user's structural eyeball passes. The bar is
deliberately high: fabricated scripture is the worst possible
outcome, so stopping is preferable to shipping a shaky text.

**NO-GO offramps (cheap — no tooling built):** request
higher-resolution crops (Cambridge IIIF supports up to
1503×2000; supplied JPGs may be downscaled); try an easier book
first; the user sources a published Ge'ez Samuel for hard ground
truth; or accept an explicitly lower provenance tier with heavy
τ.6.x.3-audit deferral. NO-GO is a valid, intended outcome.

**User's role (no Ge'ez reading required):** sanity-check that
verse counts line up with Samuel 1, that flagged-uncertain spans
visibly correspond to damaged areas on the page image, that the
English-sense column reads as a coherent Samuel 1, and that the
two witnesses broadly track each other. GO/NO-GO on that basis.

**Phase-1 deliverable:** a calibration report (the sample, the
three metrics, the W↔W collation, the recommended base witness,
and a GO/NO-GO recommendation). No production code.

---

## 5. Phase 2 — The collation tool (only if Phase 1 GOes)

Five well-bounded units, each with one purpose, a defined
interface, and explicit dependencies:

1. **Folio manifest** (YAML). Per witness: the ordered page-image
   list → the Samuel chapter:verse range each folio covers, plus
   the Witness-GG ↔ Witness-CAM page correspondence by verse
   range. The manuscript analog of the parallel-PDF
   `structural_map`. Built by vision-scanning each folio (no
   machine metadata exists in manuscript scans). Depends on:
   the cropped images only.
2. **Per-folio transcription records** (JSON; immutable
   evidence). One record per (witness, folio): the vision
   transcription structured column→line→verse, with provenance
   (folio siglum, column, line), a confidence tag, and explicit
   `⟦damaged⟧`/`⟦illegible⟧`/`⟦?word⟧` markers. Never
   overwritten → fully auditable / re-derivable. Depends on:
   the manifest + images.
3. **Verse-alignment + collation engine** (pure function). Input:
   the two witnesses' transcription records. Aligns by canonical
   Samuel chapter:verse (manifest + semantic skeleton as the
   alignment key). Per verse → base reading / other reading /
   {agree | disagree | lacuna} class / resolved reading per D3
   (base stands; disciplined eclectic fallback when the base has
   a clear slip and the other is sound — always recorded).
   Depends on: records 2 + the semantic skeleton.
4. **Reconciliation output.** (a) the reconciled Ge'ez Samuel,
   verse-aligned; (b) the **two-witness apparatus** — per verse:
   base reading, variant(s), lacunae, which witness, the
   resolution and its reason. The apparatus is the D1=B "study
   notes". Depends on: the collation engine.
5. **QA / audit report.** The Phase-1 metrics extended
   book-wide: per-chapter W↔W agreement / semantic-pass /
   uncertainty + a list of unresolved cruxes for human review.
   Same shape as the project's `run_all()` meta-tools (rules §9).
   Depends on: the reconciliation output.

The tool's exact internal shape (helpers, file layout) is sized
to what Phase 1 reveals about the real failure modes; this spec
fixes the *units and their contracts*, not their internals.

---

## 6. Phase 3 — Render & integrate

**Reused verbatim from the τ.7.x machinery (no reinvention):**

- `content/translations/geez-tewahedo/1sa.py` + `2sa.py` written
  via `write_book_module` — **including the τ.7.x.t `repr()`
  serialization fix** (manuscript transcription will contain
  stray backslashes / control-char artifacts; canonical escaping
  is required here).
- A `SAMUEL_VERSE_COUNTS` floor (1 Sam + 2 Sam) +
  `renumber_against_floor`. The floor is the canonical CEILING
  with a **documented Ethiopic "Books of Reigns" recension
  caveat** (the Ethiopic/LXX Kingdoms enumeration can differ from
  the MT/KJV skeleton); τ.6.x.3 reconciles the exact recension —
  the identical pattern every prior τ.7.x book used.
- `_meta.yaml` (geez-tewahedo) + `_source.yaml` ingest records +
  a `test_*` pin file, mirroring the τ.7.x convention; the
  `lint_rules.py` + `ruff format` + regression gate; local commit
  only, no push, no zip (project memory).

**Two genuinely-new artifacts (justified, minimal):**

- **Apparatus store** — `content/apparatus/1sa.json` /
  `2sa.json`. The project has no apparatus store; D1=B requires
  one. Lightweight, versioned, test-pinned, well-formed-schema.
- **New provenance tier** — `manuscript-collation-tier2`
  (two-witness-collated + semantic-checked; honestly *above* the
  parallel-PDF `ocr-tier3`, *below* a true critical edition).
  Flows to reader-facing verse popups exactly as `ocr-tier3`
  provenance does.

**Feeds:** the standalone Ge'ez Bible's Samuel
(`dev/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md`) and
fills the parallel-PDF Ge'ez Samuel gap. **Kings then reuses
Phases 2–3 verbatim.**

---

## 7. Honesty contract & error handling

Carried from the project's `τ.6.x.0b` honesty contract and the
`lje`/`susanna` deferral precedents:

- **Both-witness lacuna** (a span damaged/illegible in *both*
  witnesses) → a **marked gap** in the text + recorded in the
  apparatus. **Never fabricated.**
- An **optional, clearly-tagged editorial sense-restoration**
  from the known skeleton is **publisher-opt-in, OFF by
  default** (rules §6.5 additive-defaults). When off, the gap
  stands as a gap.
- Every span carries provenance + a confidence/uncertainty flag.
  The per-folio raw records are immutable and re-derivable —
  the reconciled text and apparatus can always be regenerated
  and audited against the evidence.
- The `manuscript-collation-tier2` tag is surfaced to readers so
  provenance is never overclaimed.

---

## 8. Testing & success criteria

- **Success criteria = the Phase-1 metrics extended book-wide**
  in the QA report (per-chapter W↔W agreement / semantic-pass /
  uncertainty), held to the same GO bar as the gate.
- Pin tests mirroring the τ.7.x convention: `SAMUEL_VERSE_COUNTS`
  floor totals; manifest coverage (every Samuel chapter mapped
  in **both** witnesses); reconciled-module shape (renumber
  produces the expected chapters-full/partial/empty pattern, no
  overflow); apparatus well-formedness (every verse with a
  recorded disagreement/lacuna has a structured apparatus
  entry); the **lacuna-honesty pin** (no fabricated text where
  both witnesses fail); `_meta`/`_source` ingest-record + back-
  link pins.
- `scripts/lint_rules.py` 11·0·0 clean, `ruff format` clean, the
  focused regression gate green — same release discipline as
  every τ.7.x ship.

---

## 9. Sources & attribution (per `GAPS/SOURCES.md`)

- **Cambridge MS Add. 1570** (Ethiopian Old Testament, 1588–89
  CE) — the Samuel witness CAM and the 2nd-witness Kings.
  Images **CC BY-NC**; attribution: *Cambridge University
  Library*. Must be recorded in the project's attribution
  surface.
- **GG 00106** (Gunda Gundē Digital Library, Univ. of Toronto
  Scarborough) — the GG witness for Samuel and the primary
  Kings; bot-walled, supplied as user-cropped images.
- The new `_source.yaml` provenance block records both, the
  crop provenance, and the `manuscript-collation-tier2` tier.

---

## 10. What is needed from the user / open & adjustable items

- **At the Phase-1 gate:** the structural eyeball + the GO/NO-GO
  call (no Ge'ez reading required, per §4).
- **Possibly:** higher-resolution crops if Phase 1 NO-GOes on
  legibility (Cambridge IIIF up to 1503×2000; the supplied
  ~350 KB JPGs may be downscaled).
- **Confirmable at spec review:** the calibration chapter
  (default 1 Sam 1); the proposed phase tag `τ.6.x.4`; the
  proposed GO thresholds (90/95/10).

---

## 11. Out of scope / non-goals

- The French Patrologia Orientalis books (Chronicles, Ezra,
  Nehemiah, Esther, Job) — separate, easier printed-OCR track.
- Marginalia transcription (D1 option C — rejected for now).
- This is **not** an OCR pipeline, **not** a claim of
  gold-standard critical-edition accuracy, and **never**
  fabricates scripture where the witnesses fail.
- No implementation, tooling, or extraction begins until this
  spec is approved and (per the brainstorming flow) an
  implementation plan is written.
