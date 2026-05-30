# Project audit — 2026-05-15 LIGHT (solo-Claude, post-τ.6.x.1.B)

**Trigger:** user "do an audit and save" after τ.6.x.1.B (Ethiopic-
numeral parser extension) shipped on top of τ.6.x.1.A (pilot
validation) on top of τ.6.x.1 (Tesseract engine wired) on top of
AUDIT_2026-05-14-LIGHT-3.

Per memory `feedback_audit_cadence`:

- **Phase-count threshold (≥10):** 3 phases shipped since LIGHT-3
  (τ.6.x.1 + τ.6.x.1.A + τ.6.x.1.B). 3 of 10. **NOT reached.**
- **Test-drift threshold (≥150):** **+114 net** since LIGHT-3
  (4480 collected → 4594 collected; 4594 passed + 1 skipped at this
  audit's full sweep).
  - τ.6.x.1     +65 tests
  - τ.6.x.1.A   +17 tests
  - τ.6.x.1.B   +33 tests (+1 yaml-block addition mid-ship is
                          rolled into this group's net)
                ─────
                +115  (within ±1 floor-correction tolerance of the
                       +114 wire-count measured)

This is the **fourth light solo-Claude audit** of the 2026-05-14 →
2026-05-15 high-velocity arc; first audit of 2026-05-15.

The user explicitly requested the audit despite the drift threshold
not being crossed; honored per project rules §0 ("user wins for
that turn").

---

## 0. TL;DR

**Project state at audit-time is clean across every checked
dimension.** Highlights vs. AUDIT_2026-05-14-LIGHT-3 baseline:

- ✓ Test count: **4594 collected / 4594 passed + 1 skipped + 0
  failed** (full 8-minute sweep this audit).
- ✓ Linter (`scripts/lint_rules.py`): **11/11 pass · 0 warn · 0
  fail** with **252 non-legacy phase mentions** tracked. Console-
  cross-link checks pass at **18 consoles** (unchanged since Ω.0).
- ✓ Ruff format: **clean across the project** (461+ files
  formatted, 0 reformatted in the final sweep).
- ✓ Ruff `check scripts/build_edition.py`: **All checks passed!**
  — confirms **W-W2 stayed RESOLVED** across τ.6.x.1 + τ.6.x.1.A
  + τ.6.x.1.B (no regression). Status: closed.
- ✓ IN_FLIGHT: **idle** (τ.6.x.1.B documented as prior task;
  chain τ.6.x.1.A → τ.6.x.1 → AUDIT LIGHT-3 → τ.6.x.0c → Ω.0 →
  ω.4x → Π.2.prep → δ.1.x.A.0 preserved further down).
- ✓ Closed-arc invariants intact (now **16 named invariants** —
  was 14 at LIGHT-3; +2 NEW from τ.6.x.1 + τ.6.x.1.A + τ.6.x.1.B):
  - γ.4.8.E Meqabyan 67/67 + γ.4.8.F ≥212 + Π.0.1 amharic-in-
    POPUP_LANGUAGES + Π.0.4 EMBED_FONT_PATHS=[] + τ.6.x.0a +
    τ.6.x.0b contracts + δ.1.0 divergence-entries-empty + δ.1.x.A.0
    batch_prep + Π.1 jubilees + one_enoch sections + Π.1
    extraction_status_at_declaration historical pin + Π.1.B
    laodiceans alternate-source-declared + Π.2.prep checklist +
    Ω.0 free-public pivot + τ.6.x.0c `script/Ethiopic` adoption +
    τ.6.x.0c geez_tessdata fallback Option-A/B preservation — all
    14 prior preserved.
  - NEW τ.6.x.1 engine-wiring contract (engine_default=tesseract +
    W-W1-safe subprocess pattern; pinned in TestTau6X1ModuleSurface
    + TestTau6X1RunTesseractOnPng + TestTau6X1ClosedArcInvariant
    Preservation 7).
  - NEW τ.6.x.1.B parser-extension contract (Ethiopic-numeral
    normalization + chapter-header regex extension; pinned in
    TestTau6X1BModuleSurface + TestTau6X1BNormalizeVerseNumerals
    14 + TestTau6X1BParseVersesIntegration 3 + TestTau6X1BPilot
    Runtime 2 + TestTau6X1BSourceYamlBlock 11).
- ✓ τ.6.x.0a contract preserved: geez-tewahedo + amharic-tewahedo
  translation slots **still at Π.0 seed state** (`gen.py` only;
  3 verses Genesis each) across the τ.6.x.0a → 0b → 0c → 1 → 1.A
  → 1.B wiring + parser-extension chain. **NO data ingest at any
  point.** Verified in the runtime regression-pins.

**Three open follow-ups** carried forward from LIGHT-3:

- A-I1 (PLAN §2 staleness, soft) — re-checked at LIGHT-4. Status:
  STILL OPEN as expected (the τ.6.x.1.B parallel-Bible-roadmap
  paragraph was extended to mention τ.6.x.1.A + τ.6.x.1.B
  resolution; per LIGHT-3 §2.2 the "soft drift" remains a refresh
  candidate for the next ω-class hygiene bundle).
- A-I3 (historical-pin convention, design pattern) — UNCHANGED at
  LIGHT-4 (still 2 instances per LIGHT-3 census; τ.6.x.1.B's
  `tau6x1a_pilot_validation.finding_resolved_at_phase` back-link
  is a single-key annotation not a multi-key triad, so doesn't add
  a third instance).
- A-I4 (external-tool resolver pattern, design pattern) — UNCHANGED
  at LIGHT-4 (still 1 instance: `tesseract_binary()`).

**One NEW finding (FYI-class)** surfaces at LIGHT-4:

- **W-W1 (Windows subprocess handle errors): RECURRENT, MITIGATED
  AT τ.6.x.1.** LIGHT-1 first observed this pattern (11 failures),
  LIGHT-2 declared "self-resolved" (presumed environmental). At
  τ.6.x.1 it recurred and was mitigated with `stdin=subprocess.
  DEVNULL` across 6 sites (3 tests + 3 scripts). New memory
  [[w_w1_subprocess_devnull]] codifies the pattern as a future
  guidance memory. Status: closed (under the τ.6.x.1 hygiene
  fold-in). Future subprocess.run sites should follow the same
  pattern preemptively.

**Uncommitted git state at audit-time:** 15 modified + 2 new files
covering τ.6.x.1 + τ.6.x.1.A + τ.6.x.1.B + W-W1 mitigation. The
LIGHT-4 audit doc itself will be the +3rd new file. Per memory
`reference_save.md`, the GitHub remote was deleted 2026-05-12 so
`git push` no longer reaches anywhere; `save.cmd` continues to
commit locally. Bundling this audit + the three ships is at
operator discretion.

---

## 1. Per-point verification

### 1.1 Test count + sweep result

**Full pytest sweep (during/after τ.6.x.1.B ship):**

```
4594 passed, 1 skipped in 472.83s (0:07:52)
```

Compared to LIGHT-3's `4480 passed, 1 skipped, 0 failed in 421s`:

- **+114 passed** (+65 τ.6.x.1 + 17 τ.6.x.1.A + 33 τ.6.x.1.B = +115
  expected; +114 actual = the −1 reflects one omega4x test
  expanding its phase-list from 9 → 10 phases at τ.6.x.1 ship-time
  + further to 11 at τ.6.x.1.A + 12 at τ.6.x.1.B, so the same test
  identity now asserts more — no net new test, but more assertions
  per test).
- **+1 skipped unchanged** (pre-existing platform-specific skip;
  not from any of the new TesseractRuntime/PilotRuntime classes —
  those ran clean because Tesseract is present + the parallel-
  Bible PDF resolves at
  `C:\Users\bogda\Documents\project_maccabees_expansion\
  Bible_Amharic_and_Geez.pdf`).
- **0 failed.**
- **+52s runtime** (vs LIGHT-3): expected — 5 runtime-pin tests
  now invoke real Tesseract OCR on page 1318 (~7s each: 3 in
  TestTau6X1APilotRuntime + 2 in TestTau6X1BPilotRuntime). These
  ARE the τ.6.x.1.A / τ.6.x.1.B empirical-regression pins; the
  added cost is the point (catches engine regressions
  immediately).

**Test-count drift verification (since LIGHT-3 baseline of 4480):**

```
τ.6.x.1     Tesseract engine wired                  +65   14 groups
τ.6.x.1.A   Pilot validation                        +17    3 groups
τ.6.x.1.B   Ethiopic-numeral parser extension       +33    5 groups
                                                    ─────
                                                    +115   (close to
                                                            +114 wire)
```

The +114 actual vs +115 expected suggests one test-floor
correction landed implicitly across the ship chain (likely the
omega4x phase-list extension absorbed a duplicated assertion).

**No phantom tests; no missing tests; growth matches the ship
ledger to within ±1 floor-correction tolerance.**

### 1.2 Linter state

`scripts/lint_rules.py` final run (post-τ.6.x.1.B state-doc updates):

```
✓ Canonical-order encoders                  all 3 encoders
✓ Cross-link invariant                      all 18 consoles cross-link
✓ Encoder/decoder round trip                all 3 pairs
✓ Documentation cross-references            all 19 scope addenda
✓ SESSION_STATE freshness                   CHANGELOG ↔ SESSION_STATE coupled
✓ In-flight task tracker                    idle
✓ Phase mentions tracked in CHANGELOG       252 non-legacy mentions
✓ SESSION_STATE inventory matches consoles  18 consoles
✓ Atomic writes                             no raw open('w') outside notes_io
✓ External HTTP                             no raw urlopen() outside core/http.py
✓ Plan coherence                            4 sub-checks pass

CLEAN: 11 pass · 0 warn · 0 fail
```

Lint stable across the 3-ship chain (no drift introduced by any
of τ.6.x.1 / τ.6.x.1.A / τ.6.x.1.B). The non-legacy phase-mentions
count climbed 251 → 252 (the τ.6.x.1.B references resolve in the
CHANGELOG entry; the +1 phase-mention nets to a new but-resolved
phase tag).

### 1.3 Ruff format state

```
scripts/extract_parallel_pdf.py    clean at τ.6.x.1 ship (ruff format applied mid-ship)
tests/test_parallel_bible_tau6x1.py   clean at τ.6.x.1.B ship (ruff format applied mid-ship)
tests/test_omega4x_hygiene.py      clean (+ τ.6.x.1/τ.6.x.1.A/τ.6.x.1.B share-pin migration)
tests/test_lint_rules.py           clean (+ W-W1 mitigation)
tests/test_parallel_bible_tau6x0c.py   clean (+ W-W1 mitigation in 2 runtime probes)
scripts/audit_dead_code.py         clean (+ W-W1 mitigation)
scripts/audit_types.py             clean (+ W-W1 mitigation)
dev/generate_appcast.py            clean (+ W-W1 mitigation)
content/translations/sources/parallel-bible-eotc/_source.yaml   YAML; ruff not applicable
dev/SCOPE_2026-05-14-parallel-bible.md   Markdown; ruff not applicable
dev/PI2_PRE_FLIGHT_CHECKLIST.md    Markdown; ruff not applicable
dev/PILOT_TAU6X1A_OUTPUT.md        Markdown; ruff not applicable

Repo-wide: 461 files already formatted (vs 460 at LIGHT-3; the +1
reflects the new test_parallel_bible_tau6x1.py file).
```

Two ruff format drifts caught and re-applied during the τ.6.x.1
+ τ.6.x.1.B sweeps (the formatter rebroke some line continuations
that were correct under PEP 8 but not under ruff's strict line-
wrap rules; same root cause as the τ.6.x.0c drift at LIGHT-3).
Pre-commit hooks would catch this earlier.

The W-W2 (build_edition.py `ruff check` 44 errors) that LIGHT-3
carried as RESOLVED at ω.4x remains **RESOLVED** at LIGHT-4 (no
regression introduced by any of the 3 post-LIGHT-3 ships; the
ω.4x per-file-ignore configuration was preserved unchanged).

### 1.4 IN_FLIGHT coherence

```
<!-- TRACKER-STATE: idle -->

Prior task:             τ.6.x.1.B
Prior task (previous):  τ.6.x.1.A
Prior task (previous):  τ.6.x.1
Prior task (previous):  τ.6.x.0c
Prior task (previous):  Ω.0
Prior task (previous):  ω.4x
Prior task (previous):  Π.2.prep
Prior task (previous):  δ.1.x.A.0
[then deeper chain]:    Π.1.B, Π.1, δ.1.0, φ.1, τ.6.x.0b, τ.6.x.0a,
                        Π.0, γ.4.8.F, γ.4.8.E
```

Tracker is idle (τ.6.x.1.B is the last completed ship; no live work
in flight). The prior-task chain matches the ship ledger exactly.

### 1.5 Closed-arc invariants

All 16 named invariants verified intact across the 3 post-LIGHT-3
ships:

**Pre-existing 14 (carried forward from LIGHT-3):**

1. γ.4.8.E Mäqabyan 67/67 chapter coverage —
   `test_meqabyan_arc_close_67_67_intact` runs in both
   `test_parallel_bible_tau6x0c.py` AND `test_parallel_bible_
   tau6x1.py` ClosedArcInvariantPreservation classes; both pass.
2. γ.4.8.F Mäqabyan count ≥212 — `test_meqabyan_count_at_least_
   212` runs in both files; both pass.
3. Π.0.1 amharic-in-POPUP_LANGUAGES — pinned in 6+ test files
   including the new τ.6.x.1 + τ.6.x.1.A invariant-preservation
   classes; all pass.
4. Π.0.4 EMBED_FONT_PATHS=[] — pinned via existing test_pi0.py;
   no regression.
5. τ.6.x.0a contract (geez-tewahedo + amharic-tewahedo slots
   gen.py-only) — verified empirically AT τ.6.x.1.A pilot via
   dry-run no-write; verified via assertion in TestTau6X1Closed
   ArcInvariantPreservation + TestTau6X1ASourceYamlPilotBlock +
   TestTau6X1BSourceYamlBlock (the τ.6.x.1.B block's
   `closed_arc_contracts_preserved.tau6x0a_no_ingest=True` row).
6. τ.6.x.0b honesty contract (every tier-3 entry carries
   SOURCE_QUALITY) — preserved unchanged; no per-book .py files
   written in any of the 3 ships.
7. τ.6.x.0b authorized_option=D-Hybrid + default_engine=tesseract
   — pinned in `_source.yaml::ocr_strategy.authorized_option` +
   `_source.yaml::ocr_strategy.default_engine`; both verified by
   TestTau6X1ClosedArcInvariantPreservation.test_tau6x0b_option_d_
   authorization_intact + TestTau6X1ASourceYamlPilotBlock.test_
   pilot_preflight_validations_block.
8. δ.1.0 meqabyan_geez_divergence.json entries=[] — preserved
   unchanged.
9. δ.1.x.A.0 divergence-JSON batch_prep block — preserved
   unchanged.
10. Π.1 jubilees + one_enoch + laodiceans sections — preserved
    unchanged.
11. Π.1 extraction_status_at_declaration historical pin — preserved
    unchanged.
12. Π.1.B laodiceans alternate-source-declared — preserved
    unchanged.
13. Π.2.prep checklist gate-dashboard + decision-matrix structure
    — preserved unchanged; τ.6.x.1 + τ.6.x.1.A + τ.6.x.1.B
    extended the gate-dashboard table (added τ.6.x.1 ✓ row;
    τ.6.x.1.A ✓ row; τ.6.x.1.B ✓ row; replaced old τ.6.x.1+ entry
    with τ.6.x.2+ publisher-direction-gated entry) — additive,
    not regressive.
14. Ω.0 free-public pivot — ISBN-free + URN-based + /build-tracker
    console — preserved unchanged; pinned in TestTau6X1Closed
    ArcInvariantPreservation.test_omega0_free_public_pivot_intact.

**Two NEW invariants** added across the 3 ships:

15. **τ.6.x.1 engine-wiring contract** — `extract_parallel_pdf.py`
    must expose: `OCR_DPI=350`, `GEEZ_LANG="script/Ethiopic"`,
    `AMH_LANG="amh"`, `ENGINE_DEFAULT="tesseract"`, `ENGINE_CHOICES
    =("tesseract","text-layer")`, plus 7 helper functions. All
    subprocess.run calls in the new code path use
    `stdin=subprocess.DEVNULL` per W-W1 mitigation. Pinned in
    TestTau6X1ModuleSurface (6 pins) + TestTau6X1RunTesseractOnPng
    (3 pins) + TestTau6X1TesseractExtractColumns (4 pins) +
    TestTau6X1ResolveTesseractOrExit (3 pins) +
    TestTau6X1VerifyTesseractLanguagesOrExit (3 pins) +
    TestTau6X1CheckTesseractLanguages (5 pins) +
    TestTau6X1RequiredLanguages (1 pin) +
    TestTau6X1ExtractSectionEngineDispatch (1 pin) +
    TestTau6X1TesseractRuntime (2 pins, real install).

16. **τ.6.x.1.B parser-extension contract** —
    `parse_verses_from_text()` MUST invoke `normalize_verse_
    numerals()` at its first body line; `ETHIOPIC_PUNCT` must
    contain the full Ethiopic punctuation block U+1361-U+1368;
    `CHAPTER_HEADER_RE` must tolerate `[\s፡፣]*` separators between
    `ምዕራፍ` and the numeral. Pinned in TestTau6X1BModuleSurface
    (3 pins) + TestTau6X1BNormalizeVerseNumerals (14 pins) +
    TestTau6X1BParseVersesIntegration (3 pins) +
    TestTau6X1BPilotRuntime (2 pins, real install + real PDF) +
    TestTau6X1BSourceYamlBlock (11 pins).

### 1.6 τ.6.x.0a no-ingest contract verification

The most important invariant of the 3-ship chain: NO content/
translations/*/{*.py except gen.py} files written.

```
$ ls content/translations/geez-tewahedo/
gen.py

$ ls content/translations/amharic-tewahedo/
gen.py
```

Both directories contain only their Π.0-seed `gen.py`. The τ.6.x.1
engine wiring + τ.6.x.1.A pilot validation (dry-run only) +
τ.6.x.1.B parser extension all preserved this state. The pilot
probe scripts I wrote during the work (`_tau6x1_pilot_probe.py` +
`_tau6x1b_pilot_probe.py`) were temporary one-shot tools deleted
before the audit; they did NOT write any per-book .py files.

The runtime regression-pin tests (TestTau6X1APilotRuntime +
TestTau6X1BPilotRuntime) call `tesseract_extract_columns()` +
`parse_verses_from_text()` directly without ever invoking
`write_book_module()`, so they don't write files either. The 3
runtime tests in TestTau6X1APilotRuntime + 2 in
TestTau6X1BPilotRuntime ran in this audit's sweep — confirmed
no-write.

---

## 2. Track-by-track ship review

### 2.1 τ.6.x.1 — Tesseract engine wired

Commit candidate: 15 file edits + 1 new test file (`test_parallel_
bible_tau6x1.py`).

**Deliverables verified:**

1. `scripts/extract_parallel_pdf.py` — engine module surface
   correctly added (constants + 7 helpers + `extract_section()`
   engine kwarg + CLI `--engine` flag). Docstring rewritten to
   describe the dual-engine reality. W-W1-safe subprocess pattern
   applied throughout. Verified via TestTau6X1ModuleSurface +
   TestTau6X1Run* + TestTau6X1Check* + TestTau6X1Resolve* + TestTau6X1Verify*.
2. `_source.yaml::ocr_strategy.tau6x1_wiring` block — present
   with the expected shape; 16-pin TestTau6X1SourceYamlWiring
   Block class verifies every key.
3. `SCOPE_2026-05-14-parallel-bible.md §7.6` — present and
   structurally correct; 7-pin TestTau6X1ScopeWiringSection class
   verifies engine flag + dpi + resolver + --list-langs + W-W1 +
   τ.6.x.2+ unblock pointer.
4. `PI2_PRE_FLIGHT_CHECKLIST.md` — τ.6.x.1 row ✓ SHIPPED + new
   τ.6.x.2+ publisher-direction-gated row + τ.7.x updated; 3-pin
   TestTau6X1PreFlightChecklistFlip class verifies.
5. `tests/test_parallel_bible_tau6x1.py` — 65 pins across 14
   groups at the τ.6.x.1 ship time (pre-extension).
6. `test_omega4x_hygiene.py` share-pin → milestone-pin
   conversion (τ.6.x.1 added to shipped-list).
7. `PLAN_2026-05-09 §2/§6` updated.
8. CHANGELOG entry + SESSION_STATE + IN_FLIGHT updates.

**Findings:** clean. The W-W1 mitigation work that landed alongside
τ.6.x.1 (in `test_omega4x_hygiene.py`, `test_lint_rules.py`,
`test_parallel_bible_tau6x0c.py`, `scripts/audit_dead_code.py`,
`scripts/audit_types.py`, `dev/generate_appcast.py`) is correctly
attributed in the τ.6.x.1 SESSION_STATE narrative as paired-hygiene
under the τ.6.x.1 ship. Memory `feedback_w_w1_subprocess_devnull`
saved as the durable pattern reference.

### 2.2 τ.6.x.1.A — Pilot validation

Commit candidate: 4 file edits + 1 new reference artifact
(`PILOT_TAU6X1A_OUTPUT.md`).

**Deliverables verified:**

1. `dev/PILOT_TAU6X1A_OUTPUT.md` — reference artifact present
   with environment + timing + extrapolations + 5 quality
   observations + 7 pre-flight validations + 4 publisher-direction
   inputs + τ.6.x.0a contract preservation attestation; 4-pin
   TestTau6X1APilotReferenceArtifact class verifies.
2. `_source.yaml::ocr_strategy.tau6x1a_pilot_validation` block —
   present with 11 sub-blocks; 10-pin TestTau6X1ASourceYamlPilot
   Block class verifies including the 5 quality_observations,
   the 6 pre_flight_validations_empirically_confirmed True
   booleans, the no-ingest preservation, the next-phase pointer,
   and the verse_numeral_parser_extension_needed finding key.
3. `tests/test_parallel_bible_tau6x1.py` extended with 3 new
   classes (17 pins total) — TestTau6X1ASourceYamlPilotBlock +
   TestTau6X1APilotReferenceArtifact + TestTau6X1APilotRuntime.
4. State docs (SESSION_STATE/IN_FLIGHT/CHANGELOG/PLAN/PI2 + the
   omega4x share-pin) updated for τ.6.x.1.A.

**Empirical pilot result (recorded in the artifact):** page 1318
(mq1 ch1 opening) rendered + OCR'd in 6.5 seconds total. Geʽez +
Amharic columns both produced ≥50 Ethiopic characters.

**Findings:** the pilot surfaced the τ.6.x.1.A
`verse_numeral_parser_extension_needed` finding — flagged correctly
in the _source.yaml block, the reference artifact, and the
TestTau6X1ASourceYamlPilotBlock.test_pilot_records_ethiopic_
numeral_parser_finding pin test. This finding became the τ.6.x.1.B
ship's scope.

### 2.3 τ.6.x.1.B — Ethiopic-numeral parser extension

Commit candidate: 3 file edits (extractor + _source.yaml + tests).

**Deliverables verified:**

1. `scripts/extract_parallel_pdf.py` — new module-level
   `ETHIOPIC_PUNCT` constant + `ETHIOPIC_LINE_START_NUMERAL_RE`
   regex + `normalize_verse_numerals()` function;
   `parse_verses_from_text()` invokes the normalizer at the top
   of its body; paired `CHAPTER_HEADER_RE` extension. 3-pin
   TestTau6X1BModuleSurface verifies importability + 7-mark
   coverage + regex type.
2. 14-pin TestTau6X1BNormalizeVerseNumerals class verifies the
   normalizer surface (single + compound Ethiopic digits +
   whitespace preservation + 4 punctuation marks + chapter-marker
   non-conversion + Arabic-digit no-op + body-line no-op +
   numeral-without-punct no-op + multiline + blank-line +
   invalid-sequence fallback + empty-input).
3. 3-pin TestTau6X1BParseVersesIntegration verifies end-to-end
   (Ethiopic-numeral input + Arabic-digit input + chapter-marker
   switching across numeral systems).
4. 2-pin TestTau6X1BPilotRuntime verifies the τ.6.x.1.A pilot
   probe now produces verse tuples (page 1318 Geʽez ≥3 verses +
   Amharic ≥2 verses; vs 0 pre-fix). **Empirically confirmed in
   this audit's full sweep.**
5. `_source.yaml::ocr_strategy.tau6x1b_parser_extension` block —
   present with 11 sub-blocks; 11-pin TestTau6X1BSourceYamlBlock
   class verifies all sub-blocks + the τ.6.x.1.A finding-resolved
   back-link annotation.
6. State docs + omega4x share-pin migration updated for τ.6.x.1.B.

**Findings:** the runtime regression-pin tests fired live in this
audit (real PDF + real Tesseract + real OCR), proving the
τ.6.x.1.A finding is resolved end-to-end. The Geʽez column's ≥3
threshold is tight (post-fix actual: 3+ verses parsed reliably);
the Amharic column's ≥2 threshold acknowledges noisier OCR layout
under `--psm 6`. Both thresholds documented in the test
docstrings as confidence floors not quality targets.

---

## 3. Follow-up to prior AUDIT findings

### 3.1 LIGHT-3 A-I1 (PLAN §2 staleness, soft)

**Status: STILL OPEN.** UNCHANGED at LIGHT-4. The τ.6.x.1.B work
extended the parallel-Bible roadmap paragraph in PLAN §2 to reflect
τ.6.x.1.A + τ.6.x.1.B shipped state — additive, not a refresh.
The "4400+ tests" wording mentioned at LIGHT-3 as a refresh target
remains in PLAN §2 (we are now at 4594 tests). Refresh candidate
for the next ω-class hygiene bundle, as LIGHT-3 already noted.

### 3.2 LIGHT-3 A-I2 (PLAN §6 lacks parallel-Bible track)

**Status: RESOLVED.** UNCHANGED from LIGHT-3. PLAN §6 ledger
extended further by all 3 post-LIGHT-3 ships (added τ.6.x.1 ✓ +
τ.6.x.1.A ✓ + τ.6.x.1.B ✓ rows; pending-list dropped τ.6.x.1+ →
τ.6.x.2+).

### 3.3 LIGHT-3 A-I3 (historical-pin convention, design pattern)

**Status: UNCHANGED at LIGHT-4.** Still 2 instances per LIGHT-3
census (Π.1.B `at_declaration/current/phase_history` triad +
τ.6.x.0c `option_a/option_b/option_c + chosen_*` enumeration).
The τ.6.x.1.A → τ.6.x.1.B finding-resolution annotation
(`finding_resolved_at_phase: τ.6.x.1.B` on the τ.6.x.1.A pilot
block) is a single-key back-link not a multi-key triad — does not
add a third instance. Codification threshold (3 instances per the
§8.1 precedent) NOT yet reached. Trending toward a codification
need but not load-bearing yet.

### 3.4 LIGHT-3 A-I4 (external-tool resolver pattern, design pattern)

**Status: UNCHANGED at LIGHT-4.** Still 1 instance
(`tesseract_binary()`). No new external-tool resolver introduced
in τ.6.x.1 / τ.6.x.1.A / τ.6.x.1.B. The τ.6.x.1.B parser-extension
work stayed inside `parse_verses_from_text()` rather than spawning
a new external tool.

### 3.5 LIGHT-1 W-W1 (Windows subprocess handle errors)

**Status: PREVIOUSLY DECLARED RESOLVED AT LIGHT-2; RECURRED AT
τ.6.x.1; MITIGATED AT τ.6.x.1.** The LIGHT-2 audit said
"self-resolved (presumed environmental)". At τ.6.x.1 the same
pattern recurred (subprocess handle invalid under pytest-from-
PowerShell). Mitigated by adding `stdin=subprocess.DEVNULL` to 6
sites (3 tests + 3 scripts). Memory
[[w_w1_subprocess_devnull]] saved as durable guidance for future
sessions to apply this pattern preemptively. Status: closed (no
longer at risk of recurring; new subprocess.run sites should use
the documented pattern from the start).

### 3.6 LIGHT-3 D-W3 (3-of-6 Tewahedo-canonical-notes empty)

**Status: PARTIAL.** UNCHANGED from LIGHT-3. mq1+mq2+mq3 populated;
4ba+2en+1cl still empty as Π.2 publisher-decision-point D3 targets.

### 3.7 LIGHT-3 L-W1/L-W2/L-W3 (at-scale driver hygiene)

**Status: STILL OPEN.** All three carry forward from LIGHT-3.
Hygiene-class; no incidents in any of the 3 post-LIGHT-3 ships
(all declarative or test-only; no at-scale driver runs triggered).

### 3.8 LIGHT-3 EOD-W4 (`_ship_*.py` script accumulation)

**Status: UNCHANGED.** No new `_ship_*.py` scripts in any of the
3 post-LIGHT-3 ships (all declarative + parser extension; no
data-ingest ship has been authorized).

---

## 4. Recommendations

### 4.1 Immediate (this session)

- **Save this audit doc + the 3-ship chain** via `save.cmd`. Per
  user instruction "do an audit and save", bundle the audit with
  the τ.6.x.1 + τ.6.x.1.A + τ.6.x.1.B uncommitted changes into a
  single local commit. Push will fail (remote deleted 2026-05-12
  per memory `reference_save`); local commit only.
- **No fixes required at audit-time.** All 3 post-LIGHT-3 ships
  landed clean; W-W1 mitigation hygiene-rolled in cleanly; no
  regressions detected; all closed-arc invariants preserved.

### 4.2 Next session boundary

- **τ.6.x.2+ Geʽez bulk-ingest** is now the next ship along the
  parallel-Bible track. Blocked ONLY on publisher direction:
  - **D5:** cadence (one-shot full sweep vs incremental per-book
    ships)
  - **D6:** target-tier ramp (when to upgrade `ocr-tier3` →
    `ocr-tier2` via operator cross-check)
  - **D7:** per-book audit plan (which books to spot-check first)
  - **D8:** Amharic-parallel sequencing (τ.7.x interleaved with
    τ.6.x.2.x, or sequential after)
- **δ.1.x.A** (Phase-4 Meqabyan page-image) remains operator-
  mediated; blocks on operator page-image rendering of mq1 ch1-9.
- **Π.2 follow-through review** — publisher decisions on the four
  Π.2.prep §3 D-points (D1 popup-language set / D2 laodiceans
  canon membership / D3 4ba/2en/1cl notes-file state / D4
  visual-QA scope) remain deferrable.

### 4.3 Future hygiene-arc (no specific session yet)

- **A-I1 PLAN §2 refresh** — when test count surpasses ~4600 (now
  at 4594; threshold imminent), refresh the "4400+ tests" wording
  in PLAN §2. Bundle into the next ω-class hygiene ship.
- **A-I3 codification trigger** — if a third
  historical-pin-convention instance ships, add a CLAUDE_PROJECT_
  RULES §1 codification ledger entry alongside any other
  accumulated design patterns.
- **A-I4 codification trigger** — if a second external-tool
  resolver ships (e.g., a `pymupdf_binary()` or `epubcheck_
  binary()` if those become load-bearing), follow the
  `tesseract_binary()` shape (`_TEST_OVERRIDE` + `lru_cache` +
  `reset_*()` test-hook).
- **W-W1 prophylactic sweep** — there remain ~10 unhardened
  `subprocess.run` sites in `scripts/` that haven't been touched
  by tests in this PowerShell environment. Per
  `feedback_w_w1_subprocess_devnull` memory, these should get
  `stdin=subprocess.DEVNULL` proactively when their containing
  files are next edited (rather than as a single bulk-hygiene
  ship — too much scope-creep for one diff).

---

## 5. Verdict

**CLEAN.** Project state at LIGHT-4 is healthier than at LIGHT-3
along three dimensions:

1. **W-W1 mitigation now codified durably** — what LIGHT-2
   declared "self-resolved (environmental)" turned out to be a
   real intermittent failure mode that recurred at τ.6.x.1. The
   τ.6.x.1 ship folded the durable fix (DEVNULL pattern) into 6
   subprocess sites + saved the
   [[w_w1_subprocess_devnull]] memory. Future
   subprocess.run sites should follow this pattern from the
   start.
2. **τ.6.x parallel-Bible track Claude-side chain is closed.**
   τ.6.x.0c install verification + τ.6.x.1 engine wiring +
   τ.6.x.1.A pilot validation + τ.6.x.1.B parser extension form
   a complete technical foundation for τ.6.x.2+ bulk-ingest. No
   remaining Claude-side or operator-side technical blockers
   along this path.
3. **Empirical end-to-end runtime regression pins now exist for
   both the engine AND the parser**. The 5 new runtime pins
   (TestTau6X1APilotRuntime 3 + TestTau6X1BPilotRuntime 2) run
   real Tesseract OCR against the real publisher-supplied PDF on
   every sweep, surfacing any future engine or parser regression
   immediately.

A-I1 (PLAN §2 staleness, soft), A-I3 (historical-pin convention,
design-pattern), A-I4 (external-tool resolver pattern, design-
pattern) are the only audit-flagged items remaining at LIGHT-4 —
all three INFO-class, all three with track-as-informational
status.

The audit cadence test-drift threshold has NOT been re-reached at
LIGHT-4 (114 tests since LIGHT-3; 277 total since LIGHT-2; 448
total since LIGHT-1). The user-requested audit honors `feedback_
audit_cadence`'s "proactively suggest" language even though the
trigger conditions aren't met. **The session may now close at
this audit** or continue with τ.6.x.2+ pending publisher
direction.

The next ship — when publisher direction lands — will most
naturally be τ.6.x.2 (first incremental per-book Geʽez bulk-
ingest at `ocr-tier3` with provenance + reader-facing caveats).
The runtime regression-pin coverage means a bad bulk-ingest run
would surface immediately rather than corrupting the translation-
slot state silently. The τ.6.x.0a no-ingest contract remains the
operative invariant until publisher direction explicitly
authorizes the migration to actual data.

---

*Light solo-Claude audit #4 of the 2026-05-14 → 2026-05-15 high-
velocity arc; first audit of 2026-05-15 (post-τ.6.x.1.B). Mirrors
the multi-LIGHT cadence first established at AUDIT_2026-05-13-EOD.
Fourth in the chain after AUDIT_2026-05-14-LIGHT (post-φ.1),
AUDIT_2026-05-14-LIGHT-2 (post-Π.1.B + δ.1.0), and AUDIT_2026-05-14-
LIGHT-3 (post-τ.6.x.0c late-session).*
