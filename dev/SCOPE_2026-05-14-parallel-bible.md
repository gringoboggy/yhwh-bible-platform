# Master plan — Parallel-Bible (Geʽez + Amharic) integration

**Date:** 2026-05-14 — proposed scope-expansion plan, generated in
response to the user's request to integrate the
`C:\Users\bogda\Documents\project_maccabees_expansion` materials
(complete EOTC parallel Geʽez–Amharic Bible PDF, 2,539 pages; the
Phase-4 Geʽez-revision handoff package for Meqabyan; and the
revised v3 SOURCES/CROSS_REFERENCE/TIER2 apparatus already
integrated at γ.4.8.F).

**Status:** PROPOSED — awaiting publisher approval. No code or
content shipped yet; this is the strategic plan that will guide
the next 6–18 months of work.

**Companion docs:** `PLAN_2026-05-09.md` (still master sequence for
non-parallel-bible work); `CLAUDE_PROJECT_RULES.md`; the v3
TIER2_AUDIT.md (already integrated at γ.4.8.F);
`project_maccabees_expansion/01_MASTER_PLAN.md`.

---

## §1 — Where we stand today (2026-05-14, post-γ.4.8.F)

**Project state, terse:**
- v1.0 shipped 2026-05-10 (52,499+ notes, 4033 tests passing).
- v1.x in motion; v1.1 publisher-led uniqueness-angle pick pending.
- γ.4.8 Mäqabyan arc CLOSED at γ.4.8.E (200 entries, 67/67 chapter
  coverage); γ.4.8.F (12 Tier-2 entries) layered as post-arc-close
  apparatus refinement (just shipped + saved as commit `5d7c0fe`).
- Meqabyan now at 212 entries (sole 2nd-place); Tewahedo-distinctive-
  canonical block 38.25% (strongest position in γ.4 corpus history).
- 9 editions configured in `content/editions.yaml`;
  `ethiopian-tewahedo` is the flagship for the Tewahedo-distinctive
  market positioning.

**Infrastructure that already supports parallel-text scripture
(found during the May 2026 architectural survey, NOT new work):**

| Layer | Asset | Status |
|---|---|---|
| Translation registry | `content/translations/<id>/{_meta.yaml, <book>.py}` | EXISTS — 10 translations registered (KJV full, 9 others seeded incl. `geez-tewahedo`) |
| Geʽez translation slot | `content/translations/geez-tewahedo/` | EXISTS — τ.6 seed (3 verses Gen 1:1-3) |
| Translation loader API | `scripts/core/translations.py` | EXISTS — lazy/cached per-book; ast.literal_eval safety |
| Ingestion tool | `scripts/extract_translation.py` | EXISTS — eBible.org VPL → per-book .py |
| Popup-language registry | `POPUP_LANGUAGES` dict in `scripts/build_edition.py` | EXISTS — `geez` already declared (label "Ge'ez", content_class `vnote-geez`); also `aramaic` `latin` `coptic` `syriac`. **`amharic` is NOT yet declared.** |
| Edition-level language config | `popup_languages_default` + `popup_languages_per_book` in editions.yaml | EXISTS — ethiopian-tewahedo currently declares `english/hebrew/greek`; `geez` would be a one-line addition |
| Popup-stripper | `_apply_popup_languages_and_translation()` in build_edition.py | EXISTS — handles per-language paragraph removal correctly |
| CSS for popups | `.vnote-text` `.vnote-hebrew` `.vnote-greek` (with RTL handling for Hebrew) | EXISTS — `.vnote-geez` and `.vnote-amharic` would be parallel additions |
| Fonts | Single optional embed via `EMBED_FONT_PATH` (currently IM Fell English) | EXISTS — no Ethiopic font embedded; would need new asset + `@font-face` extension |
| Apparatus integration | 1567 → 1579 entries; Meqabyan apparatus at 212 with Wright 1877 / Cowley 1974b / Andǝmta / Senkessar / D'Abbadie all named | EXISTS — γ.4.8.F just shipped |

**The strategic conclusion:** the existing architecture is
**remarkably well-prepared** for this expansion. The seed work at
τ.6 (Geʽez) anticipated exactly this scope. What's needed is
substantively MORE DATA, plus a few targeted infra additions
(Amharic registration; Ethiopic font; CSS extensions; Phase-4
divergence-apparatus model). No fundamental architectural rebuild
is required.

---

## §2 — What the user has actually asked for

**The literal request (2026-05-14):**

> "i want to upgrade the scope of the project so please look at
> these files in `C:\Users\bogda\Documents\project_maccabees_expansion`.
> I want everything integrated in my program to make the epub that
> can be or hasn't been. even the whole bible in amharic and ge'ez
> from the files attached. I want you to think hard on how to
> integrate everything in our project based on where we are in the
> project currently. i want you to devise any tools or upgrades in
> the matrix, databases that need to be built, extensions of the
> matrix anything to combine the remaining tasks of the project
> with the new scope and create the most logical, professional and
> safe way accomplishing all of it"

**Decoded into concrete deliverables:**

1. **Whole Bible in Geʽez** — every canonical book has a Geʽez
   verse-by-verse text in the translation registry, ingested and
   selectable in the popup-language system. (Phase 4 documents
   call this the "complete EOTC Geʽez canon"; the parallel Bible
   PDF in the expansion folder is the source-of-record.)
2. **Whole Bible in Amharic** — same scope for Amharic; new
   translation slot `amharic-tewahedo` registered, ingested, and
   surfaced in popups. (The parallel Bible PDF's right-column
   Amharic supplements the nehemiah-osc.org Amharic that v1 used
   for Meqabyan.)
3. **Phase 4 Meqabyan Geʽez-revision** — execute the multi-session
   Geʽez-revision plan from the `project_maccabees_expansion/`
   handoff package: 67 chapters, careful page-image translation,
   divergence apparatus, eventual v3 Meqabyan text.
4. **EPUB integration** — the `ethiopian-tewahedo` flagship
   edition surfaces Geʽez + Amharic in verse popups (and optionally
   as alternate primary-text columns for sections like Meqabyan
   where parallel rendering is structurally distinctive).
5. **Tools / databases / matrix extensions** — whatever new
   infrastructure the publisher's vision requires, built once and
   reused across all 9 editions.
6. **Professional and safe** — preserve v1.0 reproducibility,
   regression-guard the γ.4.8.E arc-close, phased rollout with
   feature flags, no destructive operations to existing data.
7. **Combine with remaining tasks** — fold into the existing
   PLAN_2026-05-09 track structure (SHORT / MEDIUM / LONG /
   HARDENING / USER-SIDE / PARKED).

---

## §3 — The architecture

### §3.1 Existing data architecture (no change required)

```
                    ┌─────────────────────────────────────┐
                    │  EDITION (editions.yaml — 9 SKUs)   │
                    │  canon · popup_languages · kinds    │
                    └────────────┬────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────────┐
            │                    │                        │
            ▼                    ▼                        ▼
    ┌──────────────┐    ┌────────────────┐    ┌────────────────────┐
    │ BOOKS        │    │ TRANSLATIONS   │    │ NOTES (apparatus)  │
    │ books.yaml   │    │ translations/  │    │ content/notes/*.py │
    │ 87 books     │    │ <id>/<book>.py │    │ + sources/*.json   │
    └──────────────┘    │ KJV full;      │    │ 1579 ethio entries │
                        │ 9 others       │    │ 4033 tests         │
                        │ seeded         │    └────────────────────┘
                        └────────────────┘
            ┌────────────────────┼────────────────────────┐
            │                    │                        │
            ▼                    ▼                        ▼
    ┌──────────────┐    ┌────────────────┐    ┌────────────────────┐
    │ POPUP LANGS  │    │ FONTS / CSS    │    │ BUILD PIPELINE     │
    │ english /    │    │ apply_style.py │    │ build_edition.py   │
    │ hebrew /     │    │ vnote-text/    │    │ build_epub.py      │
    │ greek /      │    │ -hebrew/-greek │    │ epubcheck.py       │
    │ geez (decl.)/│    │ (RTL for Heb)  │    │ Per-edition SKU    │
    │ aramaic /    │    │ Optional font  │    │ build              │
    │ latin / etc. │    │ embed          │    └────────────────────┘
    └──────────────┘    └────────────────┘
```

### §3.2 What the expansion adds

```
                    ┌─────────────────────────────────────┐
                    │  EDITION (existing, surfaces new    │
                    │  geez + amharic in popups)          │
                    └────────────┬────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────────┐
            │                    │                        │
            ▼                    ▼                        ▼
    ┌──────────────┐    ┌────────────────┐    ┌────────────────────┐
    │ BOOKS        │    │ TRANSLATIONS   │    │ NOTES + DIVERGENCE │
    │ (unchanged)  │    │ + geez full*   │ ←  │ + δ.x divergence   │
    │              │    │ + amharic-     │    │   apparatus        │
    │              │    │   tewahedo NEW │    │   (Phase 4 output) │
    └──────────────┘    └────────────────┘    └────────────────────┘
                                ↑
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
    ┌──────────────────────┐         ┌─────────────────────┐
    │ τ.6.x EBIBLE INGEST  │         │ τ.7 AMHARIC INGEST  │
    │ gez-Geez VPL (eBible)│         │ amh VPL (eBible OR  │
    │ → geez-tewahedo/     │         │   nehemiah-osc.org) │
    │ all 66 books         │         │ → amharic-tewahedo/ │
    └──────────────────────┘         └─────────────────────┘

    ┌──────────────────────┐         ┌─────────────────────┐
    │ Π.1 PARALLEL-PDF     │         │ δ.1.x PHASE-4       │
    │ INGEST (Meqabyan)    │         │ MEQABYAN REVISION   │
    │ Page-image method    │         │ Per-chapter         │
    │ from parallel PDF    │         │ divergence apparatus│
    │ → geez-tewahedo/mq*  │         │ → divergence/       │
    │   (authoritative for │         │   meqabyan_*.json   │
    │   Meqabyan)          │         │ Multi-session, slow │
    └──────────────────────┘         └─────────────────────┘

* The infra additions: register `amharic` in POPUP_LANGUAGES
  (one-line change); add `.vnote-amharic` + `.vnote-geez`
  CSS blocks; embed Noto Sans Ethiopic OFL font; surface
  geez + amharic in ethiopian-tewahedo's popup_languages_default.
```

### §3.3 New clusters proposed

Per existing project nomenclature (τ for translations,
γ for corpus arcs, ω for hygiene, χ for AI-xrefs, ψ for matrix
collapse, ν for view, ξ for sanitizers):

| Cluster | Greek-letter mnemonic | Scope |
|---|---|---|
| **τ.6.x** | tau = translations (continuation of existing τ.6 seed) | Geʽez full Bible ingest |
| **τ.7.x** | tau = translations (NEW slot) | Amharic full Bible ingest |
| **Π.1.x** | Pi = Parallel-edition (NEW cluster) | Page-image Geʽez extraction for Meqabyan from the parallel PDF (authoritative book-level data) |
| **δ.1.x** | delta = divergence (NEW cluster) | Phase-4 Meqabyan Geʽez-vs-Amharic divergence apparatus — multi-session per the `project_maccabees_expansion/` handoff |
| **φ.1** | phi = font/typography (NEW cluster) | Ethiopic font embedding + CSS extensions |
| **ω.44+** | omega = hygiene | Rules updates, schema migrations, regression-guards for the new clusters |

Open Greek letters available for future clusters: α β ε ζ η θ ι
κ λ μ ο ρ σ υ.

### §3.4 Data flow for a Meqabyan verse in the v1.1+ edition

```
   USER CLICKS a verse anchor in EPUB at, say, 1 Mq 11:1
   (the Ṣiruṣaydan=Tyre+Sidon etymology verse)
                          │
                          ▼
   ╔══════════════════════════════════════════════════════════╗
   ║  Verse popup (aside.vnote) loaded                        ║
   ║                                                          ║
   ║  ENGLISH (primary)    [vnote-text]                       ║
   ║  ───────────────────────────────────                     ║
   ║  And he had many idols, which he served...               ║
   ║                                                          ║
   ║  GEʽEZ                [vnote-geez]                       ║
   ║  ───────────────────────────────────                     ║
   ║  ወቦ ብዙኃተ ጣዖታተ ዘያገብር ቅድሜሆሙ...                  ║
   ║  (Noto Sans Ethiopic embedded; 350-dpi quality readable) ║
   ║                                                          ║
   ║  AMHARIC              [vnote-amharic]                    ║
   ║  ───────────────────────────────────                     ║
   ║  ብዙ ጣዖታት ነበሩትና ለነርሱ ይሰግድ ነበር...                  ║
   ║                                                          ║
   ║  COMMENTARY           [from apparatus]                   ║
   ║  ───────────────────────────────────                     ║
   ║  Tewahedo — Meqabyan (Ethiopian tradition)               ║
   ║  Per seed 11:1 the name Ṣiruṣaydan etymologizes...       ║
   ║                                                          ║
   ║  DIVERGENCE NOTE      [from Π.1 + δ.1.x]                 ║
   ║  ───────────────────────────────────                     ║
   ║  The Geʽez here reads more tightly than v1's             ║
   ║  Amharic-based rendering; the Tyre+Sidon etymology       ║
   ║  is unambiguous in the Geʽez column...                   ║
   ╚══════════════════════════════════════════════════════════╝
```

All data already canonical in the translation registry + apparatus;
all rendering already done by existing build pipeline; only the
**data fill-in** (and the small infra additions) are new.

---

## §4 — Data sourcing strategy (the load-bearing decision)

The single most important decision is **where each tranche of
text comes from**, because the project's "honesty" stance
demands public-domain provenance and trustworthy text.

### §4.1 Geʽez source matrix

| Source | Scope | License | Quality | Best for |
|---|---|---|---|---|
| ~~eBible.org `gez-Geez_vpl.zip`~~ | ~~Full Bible~~ | — | — | **REMOVED — verified unavailable 2026-05-14 at τ.6.x.0 audit**. HTTP 404 on `gez-Geez/`; `details.php?id=gez-Geez` returns "ID not found"; eBible.org find-page lists 1,546 translations with ZERO `gez`/`geez` IDs. |
| **Parallel Bible PDF (`Bible_Amharic_and_Geez.pdf`)** | Full Bible 2,539 pages, **EOTC FULL BIBLE** edition | EOTC publication, public-interest scholarly use | PDF text layer: OCR garbled for Geʽez per Phase 4 docs (acceptable for Amharic). Page images authoritative for both. | **PRIMARY source post-τ.6.x.0 pivot** — replaces eBible.org as the unified parallel-Bible Geʽez + Amharic source for ALL books |
| **Pell-Platt 1830 BFBS NT** | New Testament | Public Domain | Clean printed source; need OCR or transcription | Secondary witness for the NT (future ingest) |
| **BFBS 1853 Geʽez Old Testament** | OT | Public Domain | Clean printed source; need OCR or transcription | Secondary witness for OT (future ingest) |

**Recommended strategy:**

1. **First tranche — `eBible.org gez-Geez_vpl.zip`** — bulk-ingest
   into `content/translations/geez-tewahedo/` for the 66 books in
   the standard Protestant + Catholic canon. This re-uses the
   already-built `scripts/extract_translation.py geez-tewahedo`
   pipeline (per the τ.6 seed's `_meta.yaml` which explicitly
   plans this).

2. **Second tranche — Parallel Bible PDF, page-image extraction**
   — for the **6 Tewahedo-distinctive books** (1 Enoch, Jubilees,
   Meqabyan 1-3, Letter to the Laodiceans) that are unlikely to
   be in eBible.org's standard package. The Phase-4 page-image
   method already established in `project_maccabees_expansion/`
   is the QUALITY METHOD; we extend it to these books.

3. **Third tranche — cross-witness validation** — for Meqabyan
   specifically, the Phase-4 work in `project_maccabees_expansion/`
   produces both (a) authoritative Geʽez verse text and (b) a
   divergence apparatus. These flow into BOTH the `geez-tewahedo`
   translation slot AND the new `δ.1.x` divergence apparatus.

### §4.2 Amharic source matrix

| Source | Scope | License | Quality | Best for |
|---|---|---|---|---|
| **nehemiah-osc.org Amharic** | Full Bible | EOTC-affiliated; CC-licensed | Modern Amharic, clean digital text — this is the source v1 already used | **Bulk ingest** for `amharic-tewahedo` translation slot (matches the Phase-1 source) |
| **eBible.org `amh_vpl.zip`** (if available) | Standard canon | Public Domain | Clean VPL | Alternative if available; cross-witness |
| **Parallel Bible PDF Amharic column** | Full Bible | EOTC publication | OCR partially garbled (less so than Geʽez per Phase 4 docs) | **Secondary witness** for cross-validation |

**Recommended strategy:**

1. **First tranche — `nehemiah-osc.org` ingest** — bulk text for
   `amharic-tewahedo`. The data has been used for v1 already so
   the licensing is known.

2. **Second tranche — Parallel Bible Amharic column** — cross-
   validation; particularly for Meqabyan, the parallel PDF's
   Amharic is a SECOND INDEPENDENT WITNESS (different from the
   nehemiah-osc.org Amharic v1 used). This is itself a scholarly
   contribution per the Phase-4 docs.

3. **Third tranche — divergence between Amharic witnesses** — if
   the parallel-PDF Amharic disagrees with nehemiah-osc.org
   Amharic, that's data; record it in the divergence apparatus.

### §4.3 Sourcing decision summary

```
Geʽez:    eBible.org primary  →  Parallel-PDF page-image fallback for Tewahedo-distinctive 6 books
Amharic:  nehemiah-osc.org primary  →  Parallel-PDF Amharic column for cross-witness
Meqabyan: Phase-4 page-image method (parallel-PDF) primary  →  v1 Amharic as comparison baseline
```

---

## §5 — The phased roadmap

Eight phases. Each phase is a discrete shippable artifact. Each
has explicit safety controls. Order is sequenced so that early
phases unblock later phases.

### Π.0 — INFRASTRUCTURE FOUNDATIONS (no content) [~1 session]

**Scope:** prepare every infra hook for the data ingests to come.
No new content. All changes are reversible and additive.

**Deliverables:**

1. Add `amharic` entry to `POPUP_LANGUAGES` dict in
   `scripts/build_edition.py` (1-line change matching the existing
   `geez` entry pattern: `"amharic": {"label": "Amharic",
   "content_class": "vnote-amharic", "has_label_para": True}`).
2. Add `.vnote-amharic` and `.vnote-geez` CSS blocks to
   `scripts/apply_style.py` mirroring the existing `.vnote-hebrew`
   pattern (LTR, slightly larger font-size for Ethiopic legibility,
   font-family fallback chain `"Noto Sans Ethiopic", "Abyssinica
   SIL", "Nyala", serif`).
3. Create `content/translations/amharic-tewahedo/_meta.yaml` (new
   translation slot, mirroring the `geez-tewahedo/_meta.yaml` τ.6
   seed structure).
4. Create one seed verse `content/translations/amharic-tewahedo/
   gen.py` with Genesis 1:1-3 to prove the wire-up (per
   the `geez-tewahedo` precedent).
5. Add Noto Sans Ethiopic OFL font asset under `content/themes/
   <theme>/fonts/` (decision: use `NotoSansEthiopic-Regular.ttf`
   ~400 KB, OFL license; document license in `content/themes/
   <theme>/fonts/LICENSES.md`).
6. Extend `style_config.py` `EMBED_FONT_PATH` system to accept
   multiple font embeds (currently single-font; refactor to list).
7. Add NEW test class `TestPi0InfrastructureFoundations` with
   pins:
   - `amharic` in `POPUP_LANGUAGES`
   - `.vnote-amharic` + `.vnote-geez` CSS classes emit correctly
   - `amharic-tewahedo` translation discoverable via
     `scripts.core.translations.list_translations()`
   - Font asset present + license documented
   - Multi-font embed mechanism doesn't break existing IM Fell
     English embed (regression-guard)
8. Build the `ethiopian-tewahedo` SKU in dry-run mode and verify
   epubcheck passes — the new CSS / font additions should be
   inert until data lands.

**Safety controls:**
- All changes are ADDITIVE; no existing entries modified.
- The seed translation slot is 3 verses only; no content
  promotion path triggered.
- ethiopian-tewahedo's `popup_languages_default` stays
  `[english, hebrew, greek]` for this phase; geez/amharic are
  declared-but-not-surfaced.
- Closed γ.4.8.E arc invariants regression-guarded.

**Exit criteria:** all infra hooks in place; 4033+ existing tests
still pass + new Pi.0 pin tests pass; epubcheck still green on a
dry-run build.

---

### τ.6.x — GEʽEZ FULL-BIBLE INGEST (66 standard-canon books) [~2-3 sessions]

**Scope:** ingest eBible.org `gez-Geez_vpl.zip` into the
`content/translations/geez-tewahedo/` slot for all 66 books in
the standard Protestant + Catholic canon.

**Deliverables:**

1. User downloads `gez-Geez_vpl.zip` from eBible.org (or we host
   it as a PD primary source in `content/translations/sources/
   geez-tewahedo/`).
2. Run `python scripts/extract_translation.py geez-tewahedo
   --report` — produces per-book .py files for ~66 books.
3. Update `content/translations/geez-tewahedo/_meta.yaml` with
   final book/verse counts.
4. Add pin tests:
   - `TestTau6XGeezFullBibleIngest`:
     - geez-tewahedo Genesis has ≥1,533 verses (Gen verse count)
     - geez-tewahedo books_seeded ≥ 66
     - geez-tewahedo verses_total ≥ 23,000 (rough PD-canon count)
     - Spot-check 5 representative verses against printed Pell-
       Platt 1830 / BFBS 1853 to confirm fidelity
5. **Surface `geez` in `ethiopian-tewahedo` `popup_languages_
   default`** — this is the FIRST USER-VISIBLE CHANGE; gated
   behind a build flag (`--enable-geez-popups`) for one ship,
   then promoted to default after a verification ship.

**Safety controls:**
- Bulk ingest runs in a `--dry-run` mode first; outputs are
  diffed against expectation before any file is written.
- Verse counts per book are PINNED in tests so accidental
  truncation is caught at commit time.
- The Phase-1 v1 translation is NOT modified; this is parallel-
  text addition, not replacement.

**Exit criteria:** all 66 PD-canon books in geez-tewahedo;
verse-level coverage ≥99%; spot-checks confirm fidelity;
ethiopian-tewahedo build produces popup-Geʽez correctly.

---

### Π.1 — PARALLEL-PDF EXTRACTION (Tewahedo-distinctive 6) [~3-4 sessions]

**Scope:** for the 6 books unique to the Tewahedo canon (1 Enoch,
Jubilees, Meqabyan 1-3, Letter to Laodiceans), extract Geʽez
from the parallel PDF via the Phase-4 page-image method.

**Deliverables:**

1. New tool `scripts/extract_parallel_pdf.py`:
   - Accepts a page-range (e.g. 832-907 for Meqabyan).
   - Renders left-column Geʽez at 350 dpi.
   - Produces a working JSON structure of verse-keyed text.
   - Page-image-only — no OCR-trust (per the Phase-4 honesty
     rule).
2. Operator workflow (multi-session):
   - For each Tewahedo-distinctive book, identify the scan-page
     range.
   - Render pages.
   - Read fidel + transcribe verse-by-verse into
     `content/translations/geez-tewahedo/<book>.py`.
   - Cross-check verse counts against the v1 English / Amharic.
3. Update `_meta.yaml` to flag the 6 books as Phase-4-page-image-
   sourced (provenance distinct from the eBible.org-bulk-sourced
   66).
4. Pin tests:
   - `Test_Pi1_TewahedoDistinctive_GeezCoverage`:
     - geez-tewahedo `1en` (1 Enoch) book exists + has ≥108
       chapters (Charles 1912 chapter count)
     - geez-tewahedo `jub` (Jubilees) book exists + has 50
       chapters
     - geez-tewahedo `mq1` `mq2` `mq3` books exist + 36/21/10
       chapters respectively
     - geez-tewahedo `lao` (Laodiceans) book exists if present
       in the parallel PDF

**Safety controls:**
- Page-image extraction is operator-mediated; no auto-promote
  from OCR.
- Each book gets a "source-provenance" attribution noting:
  parallel-PDF page-image extraction, scan-page range, date,
  operator (Claude session ID + human collaborator if any).
- v1 English translations of these books REMAIN PUBLISHED; this
  is parallel-text addition, not replacement.

**Exit criteria:** all 6 Tewahedo-distinctive books have Geʽez
text in geez-tewahedo at verse-level coverage; ethiopian-tewahedo
edition can surface Geʽez popups for these books.

---

### τ.7.x — AMHARIC FULL-BIBLE INGEST (parallel slot) [~2-3 sessions]

**Scope:** new `amharic-tewahedo` translation slot, bulk-ingested
from nehemiah-osc.org Amharic. Mirrors τ.6.x but for Amharic.

**Deliverables:**

1. `scripts/extract_translation.py` extended to support the
   nehemiah-osc.org format (likely needs a small adapter — the
   exact format is TBD pending inspection).
2. Bulk-ingest all 87 books of the Tewahedo canon (or as many as
   nehemiah-osc.org provides).
3. Cross-witness validation: parallel-PDF Amharic column is the
   SECONDARY witness; differences logged.
4. Pin tests:
   - `TestTau7XAmharicFullBibleIngest`:
     - amharic-tewahedo Genesis ≥1,533 verses
     - amharic-tewahedo books ≥ 66 (PD canon) or ≥87 (Tewahedo
       canon) depending on source coverage
     - Spot-checks against printed Amharic Bibles
5. Surface `amharic` in `ethiopian-tewahedo`
   `popup_languages_default` (same flag-gate pattern as τ.6.x).

**Safety controls:**
- Same as τ.6.x — dry-run, diff, pin verse-counts, no v1
  replacement.

**Exit criteria:** amharic-tewahedo at ≥99% verse-level coverage;
ethiopian-tewahedo edition surfaces Amharic popups; cross-witness
divergence log produced for `δ.0` baseline.

---

### δ.1.x — PHASE-4 MEQABYAN DIVERGENCE APPARATUS (multi-session) [~15-25 sessions]

**Scope:** execute the Phase-4 Geʽez-revision plan from the
`project_maccabees_expansion/` handoff package. Slow, deliberate,
multi-session.

**Deliverables (per the handoff package, integrated into our
project):**

1. `dev/PHASE4_MEQABYAN_TRACKER.md` — copy/adapt the existing
   `03_PROGRESS_TRACKER.md` into the project's dev/ directory as
   the canonical Phase-4 tracker. Mirrors the 67-chapter table.
2. `content/divergence/meqabyan_geez_divergence.json` — new
   apparatus data file. Schema:
   ```yaml
   {
     "_meta": {
       "source": "Phase-4 Geʽez-revision (project_maccabees_expansion/, δ.1.x cluster)",
       "schema_version": "1.0",
       "phases_shipped": ["δ.1.0", "δ.1.1", ...]
     },
     "entries": [
       {
         "book": "mq1", "chapter": 1, "verse": 1,
         "geez_text": "...",                        # the Geʽez per Π.1
         "amharic_text": "...",                     # the Amharic per τ.7 / nehemiah-osc.org
         "v1_english": "...",                       # the v1 English (from translation_continuation.md)
         "geez_revised_english": "...",             # the [GZ] fresh rendering per Phase 4
         "divergence_class": "lexical|structural|content|numbering|trivial",
         "divergence_note": "...",                  # the substantive note
         "operator_session": "γ.4.8.F-δ.1.0",       # who/when
         "confidence": 0.95,
         "flagged_for_review": false
       },
       ...
     ]
   }
   ```
3. New kind families in `content/kinds.yaml`:
   - `text-geez-revision` (the [GZ] fresh translation)
   - `compare-divergence-geez` (the divergence apparatus note)
4. New tool `scripts/build_meqabyan_revision.py` that assembles
   per-book `1Mq_geez_revision.md`, `2Mq_geez_revision.md`,
   `3Mq_geez_revision.md` from the divergence JSON.
5. New tool `scripts/promote_divergence_to_apparatus.py` —
   converts divergence-class=content notes into
   `comm-divergence-geez` apparatus entries (the per-verse
   inline-popup-visible commentary). δ.1.x ships these per
   sub-phase as the work proceeds.
6. **Phase-4 working method** — each session:
   - Pick the next un-done chapter from the tracker.
   - Render Geʽez column at 350 dpi per `02_METHODOLOGY.md`.
   - Translate verse-by-verse from page images.
   - Append entries to `meqabyan_geez_divergence.json`.
   - Run the build-meqabyan-revision tool to regenerate the
     per-book markdown.
   - Run promote-divergence-to-apparatus to surface any new
     content-class divergences in the apparatus.
   - Update PHASE4_MEQABYAN_TRACKER.md.
7. Pin tests `TestDelta1XPhase4MeqabyanRevision` — growing per
   sub-phase:
   - δ.1.0 (chapter coverage opening): N chapters covered
   - δ.1.x.A through δ.1.x.G — per-batch chapter floor pins
   - δ.1.Z (arc-close): all 67 chapters have divergence entries
     + GEEZ_DIVERGENCE_SUMMARY produced + v3 translation ready
     for publication

**Safety controls:**
- v1 English translation (the published one) is NEVER modified
  during δ.1.x; the divergence apparatus and revision markdown
  are separate artifacts.
- The arc-close pins from γ.4.8.E (67/67 chapter-coverage of
  Meqabyan apparatus entries) remain regression-guarded.
- Phase-4 honesty rules from the handoff (no OCR-trust, page-
  image authority, flag uncertain readings) ENCODED into the
  build_meqabyan_revision.py tool — it refuses to accept
  entries flagged with confidence < 0.8 without explicit
  override + reviewer signoff.
- v3 incorporation (the eventual merge of divergence-confirmed
  improvements into translation_continuation.md) is a SEPARATE
  PHASE (`δ.2`) gated on Phase-4 completion + publisher review.

**Exit criteria:** 67/67 chapters complete in divergence
apparatus; per-book revision files produced; PHASE4 tracker at
67/67; content-class divergences (if any) surfaced in
apparatus; v3-readiness gate met for δ.2 publication.

---

### φ.1 — FONT + TYPOGRAPHY POLISH [~1 session]

**Scope:** ensure Ethiopic script renders well across the major
EPUB readers (Adobe Digital Editions, Kindle, Calibre, Apple
Books, Kobo).

**Deliverables:**

1. Embed Noto Sans Ethiopic Regular + Bold in the EPUB OPF
   manifest.
2. CSS fine-tuning:
   - `.vnote-geez { font-family: "Noto Sans Ethiopic",
     "Abyssinica SIL", "Nyala", serif; line-height: 1.55;
     font-size: 1.05em; }`
   - `.vnote-amharic` mirror.
3. Page-level rendering test: produce a sample
   `ethiopian-tewahedo` build with Geʽez popups; visually QA on
   each of the 5 major reader platforms.
4. Pin tests `TestPhi1Typography`:
   - Font file embedded in OPF manifest
   - @font-face declaration present in style sheet
   - vnote-geez + vnote-amharic CSS rules emit correctly
   - epubcheck passes with no warnings on the new font

**Safety controls:**
- Font is OFL-licensed (re-distributable).
- License documented in `content/themes/<theme>/fonts/
  LICENSES.md`.
- Existing IM Fell English embed must continue to work
  (regression-guard).

**Exit criteria:** Ethiopic renders correctly on all 5 reader
platforms; epubcheck green; pin tests pass.

---

### Π.2 — POPUP SURFACING + ETHIOPIAN-TEWAHEDO DEFAULT UPDATE [~1 session]

**Scope:** flip the switch — ethiopian-tewahedo edition surfaces
geez + amharic in popups by default (no flag-gate). All other
editions continue with their existing popup_languages_default.

**Deliverables:**

1. Edit `content/editions.yaml` ethiopian-tewahedo:
   `popup_languages_default: [english, hebrew, greek, geez,
   amharic]`.
2. Build full ethiopian-tewahedo SKU; run epubcheck; visual QA.
3. Pin tests `TestPi2EthiopianTewahedoPopups`:
   - ethiopian-tewahedo popup_languages_default includes geez
     + amharic
   - Sample verses (e.g. 1 Mq 11:1, Gen 1:1) emit popups with
     all 5 languages
   - Other editions (catholic-study, evangelical-reformed, etc.)
     UNCHANGED — regression-guarded

**Safety controls:**
- Only ethiopian-tewahedo gets the change; 8 other editions
  preserved.
- All upstream data must be in place before this flip (gate on
  τ.6.x, Π.1, τ.7.x).

**Exit criteria:** ethiopian-tewahedo published v1.1 candidate
with Geʽez + Amharic surfacing by default.

---

### δ.2 — V3 MEQABYAN PUBLICATION (post-Phase-4 incorporation) [~1 session, gated on δ.1.Z]

**Scope:** incorporate the Phase-4 confirmed improvements into a
v3 of `translation_continuation.md` — the eventual public-facing
revised Meqabyan translation. Per the Phase-4 handoff: "The v1
translation stays as the published baseline until Phase 4 is
fully complete and reviewed. Every change is tracked and
justified."

**Deliverables:**

1. Produce `dev/V3_MEQABYAN_REVIEW.md` — a publisher-ready
   review document listing every content-class divergence from
   δ.1.x with publisher sign-off field.
2. Run `scripts/incorporate_geez_revisions.py` (new tool) that
   produces a v3 translation_continuation.md, audit-logged.
3. Publish v3 to archive.org as a revision of the existing
   three-books-of-meqabyan-cc0-translation item.
4. Update apparatus footers project-wide to reference the v3
   text + the Phase-4 divergence-summary.

**Safety controls:**
- Publisher sign-off REQUIRED before incorporation.
- v1 archive.org item is PRESERVED as the historical baseline;
  v3 is a new revision, not a destructive overwrite.
- All divergence notes from δ.1.x remain in the apparatus as
  the scholarly comparison record.

**Exit criteria:** v3 published; PHASE4 tracker fully closed;
δ.2 ship-script archived.

---

## §6 — Cross-cutting concerns

### §6.1 The matrix extensions

The project's "matrix" — the canon × tradition × edition product
matrix — gains TWO new dimensions:

1. **Translation language** (was implicit; now first-class).
   `editions.yaml`'s `popup_languages_default` becomes a more
   significant axis; future editions can be defined entirely by
   their language-mix (e.g. a hypothetical "Tewahedo Diaspora
   Trilingual" edition with English + Geʽez + Amharic in
   parallel-column primary text, not just popups).

2. **Source-witness provenance** (was per-translation in
   `_meta.yaml`; now per-verse). The δ.1.x divergence apparatus
   records WHICH WITNESS each verse claim derives from. This is
   the scholarly bookkeeping that the existing apparatus already
   does for commentary — now extended to translations.

### §6.2 Database changes

| Database | Current | Post-expansion |
|---|---|---|
| `content/translations/<id>/*.py` | 10 translations, 1 fully-populated (KJV), 9 seeded | 12 translations, ≥3 fully populated (KJV, geez-tewahedo, amharic-tewahedo) |
| `content/sources/ethiopian_commentaries.json` | 1579 entries | 1579 entries + δ-class divergence-comm entries added per δ.1.x ship |
| `content/divergence/` | NEW | Per-book divergence JSON files (meqabyan_geez_divergence.json + future per-book) |
| `content/themes/<theme>/fonts/` | NEW | NotoSansEthiopic-Regular.ttf + LICENSES.md |
| `content/translations/sources/geez-tewahedo/` | seed only | Full gez-Geez VPL ingest source (preserved) |
| `content/translations/sources/amharic-tewahedo/` | NEW | nehemiah-osc.org Amharic ingest source |
| `content/kinds.yaml` | 30+ kinds | + text-geez-revision + compare-divergence-geez |

### §6.3 Tools to build (consolidated)

| Tool | When | Purpose |
|---|---|---|
| `scripts/extract_parallel_pdf.py` | Π.1 | Page-image extraction from parallel-PDF for Tewahedo-distinctive books |
| `scripts/build_meqabyan_revision.py` | δ.1.x | Assemble per-book revision markdown from divergence JSON |
| `scripts/promote_divergence_to_apparatus.py` | δ.1.x | Convert content-class divergence notes → apparatus entries |
| `scripts/incorporate_geez_revisions.py` | δ.2 | Produce v3 translation_continuation.md |
| `scripts/extract_translation.py` (extended) | τ.7 | Adapter for nehemiah-osc.org Amharic format |
| `scripts/style_config.py` (extended) | Π.0 | Multi-font embed support |

### §6.4 Tests to add (consolidated)

| Test class | Phase | Pins |
|---|---|---|
| `TestPi0InfrastructureFoundations` | Π.0 | ~10 |
| `TestTau6XGeezFullBibleIngest` | τ.6.x | ~8 + per-book floor pins |
| `TestPi1TewahedoDistinctiveGeezCoverage` | Π.1 | ~12 (per-book + per-verse-count) |
| `TestTau7XAmharicFullBibleIngest` | τ.7.x | ~8 |
| `TestDelta1XPhase4MeqabyanRevision` | δ.1.x | growing per sub-phase; ~50 total at arc-close |
| `TestPhi1Typography` | φ.1 | ~6 |
| `TestPi2EthiopianTewahedoPopups` | Π.2 | ~8 |
| `TestDelta2V3MeqabyanPublication` | δ.2 | ~5 |
| `TestPiClusterMetaPhasesCoverage` | (extended) | per-sub-phase _meta pins |

Estimated test growth: 4033 → ~4150 (+~120 pins net).

### §6.5 Regression guards

The expansion MUST NOT disturb:

1. **v1.0 reproducibility** — the v1.0-tagged commit must still
   build the same EPUBs. (The new code paths are gated; the
   v1.0 build doesn't take them.)
2. **γ.4.8.E arc-close invariant** — mq1 36/36 + mq2 21/21 +
   mq3 10/10 = 67/67 chapter coverage of the Meqabyan apparatus.
   (Already pinned in γ.4.8.F's regression-guard test;
   re-asserted in δ.1.x.)
3. **γ.4.8.F Tier-2 audit substance pins** — Wright 1877 +
   Cowley 1974b + Andǝmta + Ṭǝr 21 + Liber Adami all named in
   _meta. (Already pinned.)
4. **Existing 4033 tests** — every existing test must still pass
   throughout the expansion. (Standard pre-commit requirement.)
5. **9 existing editions** — only `ethiopian-tewahedo` gets
   default-popup-language changes; the other 8 remain
   identical. (Pinned in `TestPi2EthiopianTewahedoPopups`.)

### §6.6 Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| eBible.org Geʽez VPL is incomplete or buggy | Medium | Π.1 fallback method (page-image extraction) covers the gaps; cross-witness validation at τ.6.x exit |
| nehemiah-osc.org Amharic format breaks `extract_translation.py` | Medium | Build the adapter at τ.7.0 first; dry-run before bulk |
| Ethiopic fonts render poorly on legacy Kindle | High | φ.1 explicitly tests on Kindle Paperwhite-class devices; document fallback behavior |
| Phase-4 work stretches beyond 25 sessions | Medium | The handoff package's "slow and steady" stance accepts this; the tracker is designed to survive arbitrary session-counts |
| Publisher changes mind about v3 incorporation | Low | δ.2 is the ONLY phase that touches the published translation; can be paused indefinitely; everything before δ.2 is reversible |
| Apparatus integration creates schema drift | Low | New kinds added to kinds.yaml with full schema; existing kinds unchanged; ω.44+ hygiene-pin enforces |
| Build-pipeline slowdown from large translation files | Medium | Lazy loading already in place per scripts/core/translations.py; lru_cache; benchmark at τ.6.x exit |
| Storage growth (added text + fonts + sources) | Low | Estimated +50-100 MB; trivial vs current repo size |

### §6.7 Integration with the existing PLAN_2026-05-09 track structure

The PLAN_2026-05-09 organizes work into tracks: Release / Short /
Medium / Long / Hardening / User-side / Parked. The parallel-Bible
expansion maps as follows:

| Cluster | Existing PLAN_2026-05-09 track | Why |
|---|---|---|
| Π.0 | Short (≤1 session) | Infrastructure-only |
| τ.6.x | Medium (~2-3 sessions) | Bulk ingest + verification |
| Π.1 | Medium (~3-4 sessions) | Operator-mediated, slow per session |
| τ.7.x | Medium (~2-3 sessions) | Bulk + adapter |
| δ.1.x | Long (~15-25 sessions) | Multi-session Phase-4 work |
| φ.1 | Short (~1 session) | Polish |
| Π.2 | Short (~1 session) | Edition flip |
| δ.2 | User-side gated | Publisher review required |

Total: 8 phases, ~25-40 sessions. Front-loaded on infra (Π.0)
and unblocked-first (τ.6.x + τ.7.x); back-loaded on slow careful
Phase-4 work (δ.1.x). The δ.2 publication is gated on δ.1.x
completion AND publisher sign-off.

---

## §7 — Recommended next-session actions

The user should pick ONE of these to authorize for the immediate
next session:

1. **(Recommended) Ship Π.0 infrastructure foundations** — the
   ~1-session piece that prepares every hook for the data ingests
   without touching content. Lowest risk, unblocks every other
   phase, gets the test scaffolding in place.

2. **Survey + audit pass** — per memory `feedback_audit_cadence`,
   the cumulative-phases-since-AUDIT_2026-05-13-DEEP is now 6
   (γ.4.8 + B + C + D + E + F); approaching the 10-phase
   threshold. A lighter solo-Claude audit before opening a major
   new cluster (parallel-Bible) is reasonable.

3. **Authorize the whole plan; start at Π.0** — commit to the
   full 8-phase roadmap; start executing in sequence. (Per memory
   `feedback_extensive_answers` the broadest scope.)

4. **Authorize a subset** — for example, only τ.6.x (Geʽez bulk
   ingest from eBible.org) without Π.1 / Π.2 / δ.1.x. Useful if
   the publisher wants the Geʽez surfacing fast but isn't ready
   for the multi-session Phase-4 commitment.

5. **Defer to v1.2** — keep the parallel-Bible plan documented
   but not started; ship the publisher-uniqueness-angle pick for
   v1.1 first (per memory `project_v1_terminus`).

**Default recommendation (Claude-side):** Option 3 — authorize
the full plan and start at Π.0. This is the broadest-scope
option per `feedback_extensive_answers`, gets the highest-value
data (the parallel-Bible texts) into the publishing pipeline
fastest, and treats Phase-4 Meqabyan as the slow-burn parallel
project the v3 handoff package designed it to be.

---

## §7.5 — τ.6.x.0a follow-up: OCR quality (NEW DECISION POINT, 2026-05-14)

The τ.6.x.0 pivot found that eBible.org's `gez-Geez_vpl.zip` is no
longer available; the parallel-Bible PDF is the primary source. The
τ.6.x.0a infrastructure ship built `scripts/extract_parallel_pdf.py`
and verified it runs end-to-end against the publisher's PDF —
**confirming the Phase-4 docs' warning that the OCR is garbled
for Geʽez**.

A pilot extraction of 1 Mq Ch 1 produced text with:
- Wrong vowel-order selections for Geʽez fidel
- Latin/English character bleed-through in the Geʽez column
  ("aut", "vee", "Lae" appearing inside ግዕዝ text)
- Verse numbers occasionally wrong (e.g. "1:33" appearing in a
  chapter with only 28 verses)
- Amharic column slightly better but still error-prone

**Per the τ.6.x.0a contract, the geez-tewahedo and amharic-tewahedo
translation slots REMAIN at their Π.0 seed state** (3 verses on
Genesis only). The OCR extraction tool exists and runs but does NOT
populate translation slots with garbled data. A follow-up phase
**τ.6.x.0b** must choose ONE of these source-quality strategies
before ANY full-Bible bulk ingest proceeds:

### Option A — Better OCR engine (Tesseract Amharic/Geʽez)
- Install Tesseract OCR with `tessdata` for Amharic (`amh`) and
  Geʽez (`gez` if available).
- Run Tesseract directly on the PDF page images.
- Pros: free, offline, controllable. Cons: still imperfect; Geʽez
  language pack may not exist (Tesseract has `amh` but `gez` is
  often missing).

### Option B — Cloud OCR (Google Cloud Vision / Azure / AWS Textract)
- Use a cloud OCR API with Amharic + Geʽez script support.
- Pros: state-of-the-art quality for Ethiopic. Cons: costs money;
  requires publisher authorization for API spend; sends scan
  images to a third party.

### Option C — Page-image manual transcription (Phase-4 method)
- Per `project_maccabees_expansion/02_METHODOLOGY.md §3`: render
  each page at 350 dpi, read the fidel directly, transcribe.
- Pros: highest quality; matches the Phase-4 method already in
  use for Meqabyan. Cons: slow (~1 chapter per session); not
  practical for whole-Bible bulk extraction (would take 50+
  sessions).

### Option D — Hybrid (recommended pending publisher input)
- Use OCR-tier-3 from the PDF as a STARTING BASELINE.
- Tag every entry with `SOURCE_QUALITY = "ocr-tier3"` so readers
  and downstream tools know.
- High-priority books (Meqabyan, 1 Enoch, Jubilees) get upgraded
  to `page-image-tier1` via the δ.1.x Phase-4 methodology.
- Other books stay at tier-3 with an explicit caveat in the
  reader-facing apparatus.
- This unblocks the wider bulk-ingest goal while preserving honesty.

**The τ.6.x.0b phase will resolve this choice with the publisher's
input. Until then, the τ.6.x.0a infrastructure stays in place but
extraction is gated to operator-authorized per-book runs only.**

---

## §8 — Open decisions for the user

These are the publisher-side choices the plan needs but cannot
make on its own. Each can be answered by a one-line direction.

1. **Authorize the plan?** YES / NO / SUBSET (specify clusters).
2. **Start phase:** Π.0 / τ.6.x / δ.1.x / audit-first / other.
3. **Geʽez source priority:** eBible.org-first / parallel-PDF-
   first / both-in-parallel.
4. **Amharic source priority:** nehemiah-osc.org-first /
   eBible.org-first / parallel-PDF-cross-witness-only.
5. **Font embedding:** Noto Sans Ethiopic OFL (recommended) /
   relying-on-reader-fallback / different-font-choice.
6. **Phase-4 cadence target:** few-chapters-per-session
   (Phase-4-handoff default) / faster-batch / slow-research-quality.
7. **v3 publication timing:** post-Phase-4-completion (default) /
   incremental-republishing / parked-indefinitely.

---

## §9 — File map of this plan

This plan touches the following files when executed:

**NEW files:**
- `content/translations/amharic-tewahedo/_meta.yaml`
- `content/translations/amharic-tewahedo/*.py` (87 books)
- `content/translations/sources/geez-tewahedo/gez-Geez_vpl.zip`
- `content/translations/sources/amharic-tewahedo/*` (TBD)
- `content/divergence/meqabyan_geez_divergence.json`
- `content/themes/<theme>/fonts/NotoSansEthiopic-Regular.ttf`
- `content/themes/<theme>/fonts/LICENSES.md`
- `scripts/_ship_pi0.py` + `_ship_tau6x.py` + `_ship_pi1.py` + etc.
- `scripts/extract_parallel_pdf.py`
- `scripts/build_meqabyan_revision.py`
- `scripts/promote_divergence_to_apparatus.py`
- `scripts/incorporate_geez_revisions.py`
- `dev/PHASE4_MEQABYAN_TRACKER.md`
- `dev/V3_MEQABYAN_REVIEW.md` (at δ.2 only)

**MODIFIED files:**
- `scripts/build_edition.py` — POPUP_LANGUAGES add `amharic`
- `scripts/apply_style.py` — add `.vnote-geez` `.vnote-amharic` CSS
- `scripts/style_config.py` — multi-font embed mechanism
- `scripts/extract_translation.py` — nehemiah-osc.org adapter
- `content/editions.yaml` — ethiopian-tewahedo popup_languages_default
- `content/kinds.yaml` — new kind families
- `content/translations/geez-tewahedo/*.py` — full ingest
- `tests/test_ethiopian_gamma4.py` — extend or add
  test_*_parallel_bible.py for the new test classes
- `dev/SESSION_STATE.md` — entries per ship
- `dev/IN_FLIGHT.md` — entries per ship
- `dev/CHANGELOG.md` — entries per ship
- `dev/CLAUDE_PROJECT_RULES.md` — extend §1 with Π/δ/φ cluster
  codifications

**UNCHANGED files:**
- `content/notes/*.py` for non-Meqabyan books (the apparatus
  body is untouched by this expansion until δ.2)
- `content/translations/*/{!geez-tewahedo, !amharic-tewahedo}`
  — other translation slots remain as-is
- 8 of 9 editions in `content/editions.yaml` — only
  ethiopian-tewahedo gets the popup-language update

---

## §10 — Project-rules update proposal (ω.44)

When the parallel-Bible cluster begins shipping, the
`CLAUDE_PROJECT_RULES.md` §1 codification ledger should be
extended with an `Update — ω.44 / Π.0 parallel-bible
infrastructure foundations 2026-XX-XX` block:

- **Naming convention:** `τ` for translations, `Π` for parallel-
  edition extraction, `δ` for divergence apparatus, `φ` for
  font/typography. Greek-letter mnemonics match content scope.
- **Phase-4 honesty rules:** OCR-text-of-PDFs is NEVER trusted
  for Geʽez transcription; page-image authority; uncertain
  readings flagged not guessed. Codified per the v3 handoff
  package's "single most important rule."
- **Source-witness provenance:** every translation slot has a
  `_meta.yaml` recording publisher / URL / fetched-date / source-
  date / PD-basis or license. Already established at τ.6;
  extended to all τ.x.
- **Closed-arc invariant preservation:** the γ.4.8.E ARC-CLOSE
  state (67/67 chapter coverage of Meqabyan apparatus) is
  regression-guarded in every parallel-Bible cluster's pin tests.
- **v1.0 reproducibility:** the v1.0 tag must continue to build
  the same EPUBs; new code paths are flag-gated until promoted.

---

## §11 — Comparison to PLAN_2026-05-09

`PLAN_2026-05-09.md` (the current master sequence) does NOT
explicitly include parallel-Bible work as a track. The closest
existing pointer is the τ.6 seed `_meta.yaml`'s mention of "user-
side full ingest from eBible.org's gez-Geez_vpl.zip package" and
the project memory `project_v1_terminus` flagging Tewahedo-
distinctive-canonical content as the v1.1 publisher-uniqueness
anchor.

**This plan is COMPLEMENTARY to PLAN_2026-05-09, not a
replacement.** Both run concurrently:
- PLAN_2026-05-09 owns the existing track structure for non-
  parallel-Bible work (apparatus expansion, hardening, release).
- THIS plan owns the parallel-Bible expansion clusters (τ.6.x +
  τ.7 + Π.1 + Π.2 + δ.1.x + δ.2 + φ.1).

PLAN_2026-05-09 §6 should be extended with a new line:
"PARALLEL-BIBLE (per SCOPE_2026-05-14-parallel-bible.md):
Π.0 → τ.6.x + τ.7.x → Π.1 → δ.1.x → Π.2 + φ.1 → δ.2"

---

*Plan compiled 2026-05-14 by Claude (Anthropic) in response to
the publisher's parallel-Bible scope-expansion request. No code
or content has been shipped yet; this document is the strategic
roadmap. CC0 1.0 Universal — no rights reserved on the plan
itself.*
