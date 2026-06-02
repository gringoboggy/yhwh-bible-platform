# Tewahedo Re-Verification & Triaged Re-Ingest Program — Design Spec

**Date:** 2026-06-02
**Status:** design — direction approved (user, 2026-06-02: scope = "both tracks", sequencing = "A — proof → QA-parallel → triaged scale", "build it"). Per-phase implementation plans follow this spec.
**Phase tag:** extends **LANE D** (own-versification re-ingest) and adds **LANE Q** (quality-assurance of the existing own-vers corpus). Sub-phase tags assigned per implementation plan.

> **For agentic workers:** read the bootstrap triad (RULES → SESSION_STATE → the live roadmap PLAN) first, then this spec. Companion data: the corpus inventory in `dev/CHANGELOG.md` + the per-source `_meta.yaml`/provenance headers; the calibration/failure-class library in `content/translations/sources/patrologia/_vision_notes.md` and `content/manuscript/_reviewer_context/{GG,CAM}_topology.md`; the D2 readiness recon `docs/superpowers/notes/2026-05-28-d2-source-readiness.md`.

---

## 1. Purpose & north-star tie-in

The Ethiopian Tewahedo edition is the **superset** every other edition filters from, and the **two standalone Bibles** (Ge'ez + Amharic, each with a faithful English back-translation in its own popups — LANE P) are a first-class north-star goal. Today the Ge'ez/Amharic content is mostly **weak 2026-05-15 Tesseract OCR** (KJV-renumbered, lossy), with only a small high-fidelity core (manuscript collation + Psalms + the in-flight Esther vision).

This program uses the **matured post-mint-11 system + Opus 4.8 + 1M context + ultracode multi-agent orchestration + the high-fidelity transcriptions already produced** to:
- **Track 1 (LANE Q):** QA the existing high-value own-versified work to the 4.8 standard — find and fix residual errors, upgrade the 4.7-era English back-translations.
- **Track 2 (LANE D, scaled):** replace the weak OCR bulk via **triaged** own-versification re-ingest — routing each book to the cheapest *faithful* method.

End-state: a faithful, own-versified, manuscript/critical-edition-grounded Ge'ez (and Amharic) Bible — the deepest free Tewahedo apparatus in existence — feeding the two standalone Bibles.

**Cardinal invariant (unchanged):** the 9 KJV editions stay **byte-stable** throughout (`build_standalone` is the only consumer of `geez-tewahedo`; the 9 never enter it). Every ship proves it.

---

## 2. Current state — the four quality strata

| Stratum | Books | Method / model | Versification | State |
|---|---|---|---|---|
| **Weak OCR bulk** | ~35 Ge'ez + ~28 Amharic | Tesseract OCR of one parallel-Bible EOTC PDF, 2026-05-15 (`ocr-tier3`) | KJV-renumbered (lossy) | Slated for Track-2 replacement |
| **High-value own-vers** | 1sa (3 ch), 2sa (1 ch), 1ki (6 ch) dual-witness collation; **psa (151 ch)** HaCohen critical ed.; est_patrologia (in-flight) | The mature convergence method | Own (source-authoritative) | Track-1 QA target; the reference gold standard |
| **EN back-translation** | gen/exo/lev (tier4 unreviewed); psa/1ki/1sa/2sa (tier3 reviewed) | **Opus 4.7** | Aligned to its Ge'ez source | Track-1 QA + 4.8 upgrade |
| **Patrologia printed-OCR** | job/1ch/2ch/ezr/neh/est | Tesseract, 2026-05-20 (`patrologia-printed-tier1`) — flagged insufficient (margin numerals + apparatus lost) | KJV-renumbered | Track-2 printed-vision (Esther first, in-flight) |

Detailed per-book inventory: the 2026-06-02 corpus-inventory recon (see `dev/SESSION_STATE.md` of this date) + the provenance headers.

---

## 3. The reframe — triage by source, vision only where required

The weak OCR bulk does **not** all need vision transcription. With 4.8 + the now-available source recon, each remaining book routes to the **cheapest faithful method**:

| Route | When | Cost | Examples |
|---|---|---|---|
| **parse** | clean digital/Unicode Ge'ez exists | hours | 1 Enoch (Charles-1906 Ge'ez OCR layer / OCP), HaCohen Wisdom + Sirach (clean text, needs verse-markup only) |
| **printed-vision** | a printed critical edition exists | days/book | the Patrologia set (est, job, 1ch, 2ch, ezr, neh) |
| **dual-witness marathon** | manuscript-only | weeks/book | the Kings/Samuel remainder |
| **QA-in-place** | already own-versified & high-fidelity | cheap | the Track-1 targets |

Routing is decided by a per-book **source-triage recon** (§4.1), generalizing the D2 readiness note. This shrinks the slow-vision portion to its irreducible minimum — the key to making "finish the rest" tractable.

---

## 4. Architecture

Two tracks over one shared substrate, orchestrated by ultracode workflows under a hardware profile.

### 4.1 Shared substrate (build once; both tracks use it)

**(a) Source-triage recon.** A per-book readiness record (format: clean-Unicode / printed-critical / manuscript-only / already-own-vers; verse-markup present?; PD status; URL/location) → a `route ∈ {parse, printed-vision, dual-witness, qa-in-place}` + a priority. Produced by light text-only research agents (the D2-recon pattern), accumulated to `docs/superpowers/notes/<date>-tewahedo-source-triage.md` and a machine-readable routing table. Re-verify each documented blocker/NO-GO with real data (memory `feedback_reverify_conservative_nogo`).

**(b) The reference / method library — "use our transcriptions as help," made concrete.** Three reusable assets feed *every* new pass:
- **The failure-class library:** `_vision_notes.md` (a)–(r) (vision), the GG/CAM scribal-topology files + the chapter-class screens (manuscript) — the durable "HOW to read" knowledge, never the WHAT (blindness rule preserved: blind transcribers get reading-discipline screens, never recension content).
- **The finished high-fidelity transcriptions** (Psalms, the collation, Esther) as the calibration gold standard for glyph/typesetter habits.
- **Semantic anchors:** the **EN back-translations**, the **LXX/KJV skeleton**, and editor translations (Pereira's French) — used to cross-check the Ge'ez and to *detect harmonization* (the trick that caught the rejected B2 pass on Esther p28). Anchors are calibration only — **excluded from the verse text** and never an authority to overwrite the print/parchment.

**(c) Hardware profile.** One config knob, e.g. `profiles: {n95: {vision_concurrency: 1, light_concurrency: 2}, mac: {vision_concurrency: N, light_concurrency: M}}`. The orchestrator reads the active profile; nothing else changes when hardware improves. The OOM root-cause was whole-folio LANCZOS upscale + stacked heavy agents (both already eliminated by tight ≤1568px crops + MAX-1 sequencing) — so on a big-unified-memory Mac the heavy-vision cap genuinely lifts.

**(d) Orchestration.** ultracode `Workflow` scripts, profile-gated: light work (parse, recon, QA-of-clean-text, EN review) runs parallel up to `light_concurrency`; heavy vision runs sequentially up to `vision_concurrency`. Crash-resilient (resumable workflows + on-disk accumulators), per the marathon discipline.

### 4.2 Track 1 — LANE Q: QA the high-value own-vers corpus to the 4.8 standard

A **reusable QA harness** (a parameterized Workflow). For each already-own-versified unit:
1. Re-read with 4.8 against (a) its source image/text, (b) its semantic anchor (EN/LXX/French), (c) the failure-class library.
2. **Adversarially hunt the known error classes** (harmonization toward the standard text, column/folio boundary-omission, low-contrast glyph-order, OCR noise) — a systematic error-hunt + adjudication, NOT blind re-transcription.
3. Adjudicate discrepancies (controller crux-verification on load-bearing cruxes); produce a per-unit QA report + fixes.
4. The EN back-translations (4.7) get a faithfulness re-check vs the Ge'ez + a 4.8 upgrade where they drift.

Targets: 1sa/2sa/1ki collation (10 ch), Psalms (151 ch), est_patrologia (as pages land), the EN stores. Byte-stable (fixes touch own-vers stores only).

### 4.3 Track 2 — LANE D scaled: triaged own-vers re-ingest

Per-book pipeline (the proven D1b shape, generalized): **recon → route → execute (parse / printed-vision / dual-witness) → own-vers store (`VERSIFICATION="own"`, no KJV renumber) → KJV xref sidecar → add to `_STANDALONE_BOOKS` → rebuild + epubcheck 0/0 + 9 editions byte-stable → EN trailing lane → Track-1 QA.**

**Priority order** (highest uniqueness value first): the distinctive Tewahedo-canonical books (1 Enoch, Jubilees, Meqabyan I–III, 4 Baruch) + the Patrologia set (Esther in-flight, then Job/Chronicles/Ezra/Nehemiah), then the remaining OCR-bulk books. Esther is the end-to-end **proof that gates** the scale-up.

---

## 5. Sequencing (Approach A)

1. **Finish the Esther vision proof** (foreground; validates the full vision→store→xref→standalone→epubcheck lane). In-flight, paused p28.
2. **Track-1 QA in parallel** (the light lane; never-single-thread) — banks quick wins and *sharpens the failure-class library* used by Track 2.
3. **Track-2 triaged scale** once the proof + QA validate and sharpen the method — priority-ordered, book-by-book, each ship byte-stable.

---

## 6. The honesty contract (cardinal — unchanged, applies to every pass)

- **No fabrication:** transcribe only what is on the page/parchment; genuine illegibility → `⟦illegible⟧` + a matching flag; never a guessed word.
- **No harmonization:** transcribe the source glyphs even where they differ from the standard Bible; flag, never smooth. **A pass that recites the standard text instead of reading (detected via the semantic anchors + fabricated content for cut-off verses) is rejected WHOLESALE** (`_vision_notes (q)`).
- **Apparatus / editor-translation excluded** from the verse text — calibration anchors only (`_vision_notes (r)`).
- **Codepoint-gate** Ethiopic-only per ship; **confidence-tagged** xrefs; **byte-stable** 9 KJV editions; **marathon-core evidence immutable**.

---

## 7. Error handling / failure modes

- **Harmonization** → the (q) rejection rule + semantic-anchor cross-check.
- **Crash/OOM** → resumable workflows + on-disk accumulators + the documented crash-recovery method (recover a completed StructuredOutput from the agent transcript; never re-run a heavy fan-out "to be safe"). Profile-gated concurrency prevents the stacked-heavy-agent OOM.
- **Non-convergence** → the `escalate_if_unbounded` rule (surface to the user past the class's expected rounds rather than mechanically iterate).
- **Source genuinely absent/blocked** → honest NO-GO recorded in the recon (re-verified with real data), the book deferred — never fabricated, never "blocked on sources" without the look-first protocol (RULES §0 guard 2).

---

## 8. Testing / verification gates (every ship)

Byte-stability gate (9 KJV editions) · flagship epubcheck 0/0/0/0 · Ethiopic-only codepoint-gate · `lint_rules.py` + mypy + ruff-format · the honesty/own-vers pins (`VERSIFICATION="own"`, no renumber, xref confidence-tagged, apparatus excluded) · `test_nested_anchors` after any `epub_working` mutation. Per-book QA report archived.

---

## 9. Decomposition — the implementation plans that follow this spec

| Plan | Scope | Depends |
|---|---|---|
| **P0 — Shared substrate + Track-1 QA harness** | source-triage recon (full canon) + hardware-profile config + the reusable QA Workflow + the reference/library wiring | — |
| **P1 — Track-1 QA execution** | run the QA harness over collation (1sa/2sa/1ki) + Psalms + the EN stores; fix + report | P0 |
| **P2 — Esther proof completion** | finish the in-flight est_patrologia vision (p29→65) → store → xref → standalone → proof gates | (in-flight) |
| **P3+ — Track-2 triaged re-ingest** | per priority order: distinctive books (parse where clean: 1 Enoch; vision where needed: Jubilees/Meqabyan/4 Baruch) + the Patrologia set; one plan per book or coherent batch | P0, P2 |

Each plan: TDD for code, agent-driven + adversarially-reviewed for content, byte-stable, 5-leg save per coherent batch, self-upgrading-matrix (append new failure-classes as they appear).

---

## 10. Out of scope

- The 9 KJV editions (byte-stable, untouched) and all commercial surfaces (dropped 2026-05-14).
- The **paid API script-path** (`manuscript_vision.py` at-scale) — remains inert infra; no budget. Revisit only if the user funds an API key (would change Track-2 throughput dramatically).
- No DB / no language rewrite / no web.py-split-for-size (project-wide de-scopes hold).

---

## 11. Self-upgrading-matrix & open questions (resolved at the relevant plan)

- **Amharic depth:** Track-2 covers Ge'ez first; Amharic own-vers re-ingest is sequenced after the Ge'ez breadth proof (own-vers spec §7 / LANE P) — its source is the parallel-Bible PDF (printed-vision or improved parse), decided in its own recon.
- **Profile values for `mac`:** set empirically when the hardware arrives (sample free RAM during the first concurrent heavy run, as the CAM pre-pull rule does).
- **Distinctive-book sources:** 1 Enoch = GO parse-first (Charles-1906 Ge'ez OCR layer; OCP licensing nuance → prefer Charles/self-segmentation); Jubilees = vision-required (Charles-1895 scan, gibberish OCR); Meqabyan/4 Baruch = re-verify the PD-Ge'ez availability per book in the P3 recon (the documented Meqabyan NO-GO is re-checked, not assumed).
