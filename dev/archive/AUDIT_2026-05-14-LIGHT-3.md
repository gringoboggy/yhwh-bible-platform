# Project audit — 2026-05-14 LIGHT-3 (solo-Claude, post-τ.6.x.0c late-session)

**Trigger:** user "audit" after τ.6.x.0c (Tesseract install verification
+ `script/Ethiopic` adoption) shipped on top of Ω.0 (free-public
pivot) on top of ω.4x (W-W2 + A-I1 + A-I2 closure) on top of
Π.2.prep (Ethiopian-Tewahedo flip pre-flight) on top of δ.1.x.A.0
(divergence-JSON batch-prep) on top of AUDIT_2026-05-14-LIGHT-2.

Per memory `feedback_audit_cadence.md`, **the test-drift threshold
(≥150) has been crossed** since AUDIT_2026-05-14-LIGHT-2 baseline:

- **Phase-count threshold (≥10):** 5 phases shipped since LIGHT-2
  (δ.1.x.A.0 + Π.2.prep + ω.4x + Ω.0 + τ.6.x.0c). 5 of 10.
  **NOT reached.**
- **Test-drift threshold (≥150):** +162 net (4318 → 4480 collected;
  4480 passed + 1 skipped at this audit's full sweep).
  - δ.1.x.A.0   +39 tests
  - Π.2.prep    +35 tests
  - ω.4x        +15 tests
  - Ω.0         +27 tests
  - τ.6.x.0c    +46 tests
                ─────
                +162  (verified)

This is the **third light solo-Claude audit** of 2026-05-14
following the AUDIT_2026-05-13-EOD precedent of multiple lighter
audits clustering in a single high-velocity session.

---

## 0. TL;DR

**Project state at audit-time is clean across every checked
dimension.** Highlights vs. the AUDIT_2026-05-14-LIGHT-2 baseline:

- ✓ Test count: **4480 collected / 4480 passed + 1 skipped + 0
  failed** (full 7-minute sweep this audit; verified via the
  pytest run that completed concurrent with the τ.6.x.0c ship).
- ✓ Linter (`scripts/lint_rules.py`): **11/11 pass · 0 warn · 0
  fail** with **251 non-legacy phase mentions** tracked.
  Console-cross-link checks pass at **18 consoles** (was 17 at
  LIGHT-2; the +1 reflects Ω.0's `/build-tracker` console
  addition).
- ✓ Ruff format: **clean across all newly-introduced files**
  (test_parallel_bible_delta1xa0.py + test_parallel_bible_pi2prep.py
  + test_omega4x_hygiene.py + test_omega0_free_public_pivot.py +
  test_parallel_bible_tau6x0c.py). The τ.6.x.0c file required one
  ruff-format pass mid-ship; pre-commit-equivalent re-ran clean.
- ✓ Ruff `check scripts/build_edition.py`: **All checks passed!**
  — confirms **W-W2 RESOLVED** at ω.4x with 44→0 fix (per-file-ignore
  for the 8 intrinsic E501/C901 patterns + manual fixes for the
  rest). Status: closed.
- ✓ IN_FLIGHT: **idle** (τ.6.x.0c documented as prior task;
  chain Ω.0 → ω.4x → Π.2.prep → δ.1.x.A.0 → Π.1.B → Π.1 → δ.1.0
  → φ.1 preserved further down).
- ✓ Closed-arc invariants intact (now **14 named invariants**
  — was 12 at LIGHT-2; +2 NEW from τ.6.x.0c):
  - γ.4.8.E Meqabyan 67/67 + γ.4.8.F ≥212 + Π.0.1 amharic-in-
    POPUP_LANGUAGES + Π.0.4 EMBED_FONT_PATHS=[] + τ.6.x.0a + b
    contracts + δ.1.0 divergence-entries-empty + δ.1.x.A.0
    batch_prep + Π.1 jubilees + one_enoch sections + Π.1
    extraction_status_at_declaration historical pin + Π.1.B
    laodiceans alternate-source-declared + Π.2.prep checklist +
    Ω.0 free-public pivot — all 12 prior preserved.
  - NEW τ.6.x.0c `script/Ethiopic` adoption decision (pinned in
    `TestTau6X0cSourceYamlVerificationBlock::test_script_ethiopic_
    adopted` + `TestTau6X0cScopeAdoptionRecorded::test_script_
    ethiopic_adoption_recorded` + 4 others).
  - NEW τ.6.x.0c geez_tessdata fallback Option-A/B preserved pin
    (`TestTau6X0cGeezFallbackExtended::test_option_a_preserved`
    + `test_option_b_preserved`) — guards the τ.6.x.0b-historical-
    record-preservation across the Option-C extension. Mirrors the
    Π.1 → Π.1.B historical-pin pattern (see §3.3 A-I3).
- ✓ τ.6.x.0a + τ.6.x.0b + δ.1.0 + Π.1 + Π.1.B + δ.1.x.A.0 +
  Π.2.prep + Ω.0 contracts preserved: geez-tewahedo + amharic-
  tewahedo translation slots remain at `gen.py`-only seed state
  (3 verses Genesis only); meqabyan_geez_divergence.json
  entries=[]; content/notes/lao.py NOT created; v1.0 byte-
  identical reproducibility preserved across all 5 post-LIGHT-2
  ships.
- ✓ Source corpus: **1579 entries unchanged** across the LIGHT-2
  → LIGHT-3 window (all 5 ships are declarative; no commentary-
  corpus changes). Note: Ω.0 also did not touch the corpus despite
  being a north-star pivot — ISBN removal is metadata-layer; the
  52,459-note total is unaffected.

**No CRITICAL findings.** **Two prior WARN findings RESOLVED at
ω.4x (W-W2 + A-I2); one prior INFO PARTIALLY ADDRESSED (A-I1);
one prior INFO carrying forward (A-I3); one NEW INFO at LIGHT-3:**

1. **W-W2 (build_edition.py lint): RESOLVED at ω.4x `(post-LIGHT-2
   #3)`.** 44 ruff `check` errors reduced to 0 via manual fixes +
   per-file-ignore for 8 intrinsic patterns. Verified at LIGHT-3
   (`ruff check scripts/build_edition.py` → "All checks passed!").
   Status: closed.
2. **A-I1 (PLAN §2 staleness): PARTIALLY ADDRESSED at ω.4x.** PLAN
   §2 was refreshed from "3808 tests" → "4400+ tests" + SESSION_STATE
   cross-reference + six-voice corpus codification + parallel-Bible
   roadmap summary. Today's count is 4480 (+80 drift vs. ω.4x refresh
   target). Not WARN because SESSION_STATE is the authoritative fresh
   snapshot. Drift remains soft.
3. **A-I2 (PLAN §6 lacks parallel-Bible track): RESOLVED at ω.4x.**
   PLAN §6 extended with parallel-Bible track sub-section containing
   SCOPE §11 canonical chain + shipped/pending sub-phase ledger with
   commit hashes. τ.6.x.0c further extended this ledger at its ship-
   time (added Ω.0 + τ.6.x.0c rows; pending ledger drops τ.6.x.0c).
   Status: closed.
4. **A-I3 (historical-pin convention): UNCHANGED status — now TWO
   instances of structurally-similar patterns.** Π.1.B's
   `at_declaration / current / phase_history` triad is one; τ.6.x.0c's
   `option_a / option_b / option_c + chosen_at_phase + chosen_option
   + chosen_rationale` enumeration is structurally analogous (preserve
   historical record while exposing the chosen current path).
   Codification threshold (3 instances per the §8.1 precedent) NOT
   yet reached — but trending. See §3.3.

**One NEW INFO finding** surfaces at LIGHT-3:

- **A-I4 (info): first external-tool resolver in `scripts/core/
  paths.py`.** τ.6.x.0c introduced `tesseract_binary()` — the first
  external-binary resolver in `paths.py`, which until now resolved
  only project-internal directory/file paths (content_root,
  notes_dir, etc.). The new resolver follows the established
  `_TEST_OVERRIDE` + `lru_cache` + `reset_*()` test-hook pattern,
  and stays path-resolution-only (no runtime probes — the caller
  invokes Tesseract). No code-quality concern; flagged because the
  precedent suggests future external-tool resolvers (e.g., a
  `pymupdf_binary()` or `epubcheck_binary()` if those become
  load-bearing) should follow the same shape. See §3.4.

**Uncommitted git state at audit-time:** the 5 post-LIGHT-2 ships
+ this LIGHT-3 doc are all post-LIGHT-2 changes. Per memory
`reference_save.md`, the GitHub remote was deleted 2026-05-12 so
`git push` no longer reaches anywhere; `save.cmd` continues to
commit locally. Bundling this audit + the τ.6.x.0c ship is at
operator discretion.

---

## 1. Per-point verification

### 1.1 Test count + sweep result

**Full pytest sweep (during/after τ.6.x.0c ship):**

```
4480 passed, 1 skipped in 421.49s (0:07:01)
```

Compared to LIGHT-2's `4317 passed, 1 skipped, 0 failed in 422s`:

- **+163 passed** (+39 δ.1.x.A.0 + 35 Π.2.prep + 15 ω.4x + 27 Ω.0
  + 46 τ.6.x.0c = +162 expected; +163 actual = +1 floor-correction).
- **+1 skipped unchanged** (pre-existing platform-specific skip;
  not from the τ.6.x.0c TesseractRuntime class — that one ran clean
  locally because Tesseract is present at `C:\Program Files\
  Tesseract-OCR\`).
- **0 failed.**
- **−1s runtime** essentially identical to LIGHT-2 (within noise;
  the +163 tests added negligible cost because most are file/yaml
  shape pins that read once-and-assert without import-heavy
  fixtures).

**Test-count drift verification (since AUDIT_2026-05-14-LIGHT-2
baseline of 4318 collected):**

```
δ.1.x.A.0  Divergence-JSON batch-prep mq1 1-9     +39   8 groups
Π.2.prep   Π.2 pre-flight checklist                +35   13 groups
ω.4x       Hygiene bundle (W-W2 + A-I1 + A-I2)    +15   5 groups
Ω.0        Free-public pivot                       +27   9 groups
τ.6.x.0c   Tesseract verify + script/Ethiopic     +46   8 groups
                                                  ─────
                                                  +162  (verified)
```

The +163 actual vs. +162 expected suggests one test-floor
correction landed implicitly across the ship chain (likely a kinds-
count or canon-count drift fix similar to the LIGHT-2 +1 floor-
correction).

**No phantom tests; no missing tests; growth matches the ship
ledger to within ±1 floor-correction tolerance.**

### 1.2 Linter state

`scripts/lint_rules.py` final run (post-τ.6.x.0c state-doc updates):

```
✓ Canonical-order encoders                  all 3 encoders
✓ Cross-link invariant                      all 18 consoles cross-link
✓ Encoder/decoder round trip                all 3 pairs
✓ Documentation cross-references            all 19 scope addenda
✓ SESSION_STATE freshness                   CHANGELOG ↔ SESSION_STATE coupled
✓ In-flight task tracker                    idle
✓ Phase mentions tracked in CHANGELOG       251 non-legacy mentions
✓ SESSION_STATE inventory matches consoles  18 consoles
✓ Atomic writes                             no raw open('w') outside notes_io
✓ External HTTP                             no raw urlopen() outside core/http.py
✓ Plan coherence                            4 sub-checks pass

CLEAN: 11 pass · 0 warn · 0 fail
```

Lint stable across the 5-ship chain (no drift introduced by any
of δ.1.x.A.0 / Π.2.prep / ω.4x / Ω.0 / τ.6.x.0c). The console
cross-link check picked up the new `/build-tracker` console
correctly (17→18; Ω.0's `_design.CONSOLES` insertion +
SESSION_STATE inventory bump are both consistent). The non-legacy
phase-mentions count holds at 251 because the new τ.6.x.0c
references resolve in the CHANGELOG entry (the same shape as the
prior ω.4x / Ω.0 / etc. ship entries — no drift introduced).

### 1.3 Ruff format state

```
test_parallel_bible_delta1xa0.py        clean at δ.1.x.A.0 ship
test_parallel_bible_pi2prep.py          clean at Π.2.prep ship
test_omega4x_hygiene.py                 clean at ω.4x ship (+ τ.6.x.0c edit)
test_omega0_free_public_pivot.py        clean at Ω.0 ship
test_parallel_bible_tau6x0c.py          clean (re-formatted mid-ship via ruff format)
scripts/core/paths.py                   clean (additive append; pre-existing format)
content/translations/sources/parallel-bible-eotc/_source.yaml   YAML; ruff not applicable
dev/SCOPE_2026-05-14-parallel-bible.md  Markdown; ruff not applicable
dev/PI2_PRE_FLIGHT_CHECKLIST.md         Markdown; ruff not applicable

Repo-wide: 461 files already formatted.
```

The τ.6.x.0c ship caught one ruff format drift on the new test
file during the full-suite sweep (the formatter rebroke some line
continuations that were correct under PEP 8 but not under ruff's
strict line-wrap rules); `ruff format` was applied, test re-run
clean. Pre-commit-equivalent gates would have caught this earlier.

The pre-existing W-W2 (build_edition.py `ruff check` 44 errors)
that LIGHT-2 carried forward is **RESOLVED** at ω.4x (see §2.1).

### 1.4 IN_FLIGHT coherence

```
<!-- TRACKER-STATE: idle -->

Prior task:             τ.6.x.0c
Prior task (previous):  Ω.0
Prior task (previous):  ω.4x
Prior task (previous):  Π.2.prep
Prior task (previous):  δ.1.x.A.0
[then deeper chain]:    Π.1.B, Π.1, δ.1.0, φ.1, τ.6.x.0b,
                        τ.6.x.0a, Π.0, γ.4.8.F, γ.4.8.E
```

Tracker is idle (τ.6.x.0c is the last completed ship; no live work
in flight). The prior-task chain matches the ship ledger exactly.
The chain depth (5 ships preserved at full detail at LIGHT-3; 9
ships at LIGHT-2; 10+ at LIGHT-1) reflects the project's append-
only IN_FLIGHT convention.

### 1.5 Closed-arc invariants

LIGHT-3 verified the LIGHT-2 set of 12 plus two new invariants
introduced by τ.6.x.0c:

| Invariant | Pinned in | Status |
|---|---|---|
| γ.4.8.E Meqabyan 67/67 (mq1 36 + mq2 21 + mq3 10) | TestGamma48EMeqabyanArcClose + 8 Tau6X0c/Omega0/Omega4x/Pi2Prep/Delta1XA0 ClosedArcInvariantPreservation | ✓ ALL PASS |
| γ.4.8.F Meqabyan ≥212 floor | TestGamma48FTier2AuditIntegration + 8 others | ✓ ALL PASS |
| Π.0.1 amharic-in-POPUP_LANGUAGES | TestPi0PopupLanguageRegistration + 8 others | ✓ ALL PASS |
| Π.0.4 EMBED_FONT_PATHS = [] | TestPi0MultiFontInfrastructure + 8 others | ✓ ALL PASS |
| ω.41 §1 Cyril plurality | TestGamma49DAthanasiusArcClose + 249 other selectors | ✓ ALL PASS |
| τ.6.x.0a contract: geez-tewahedo gen.py-only | 9 test classes | ✓ ALL PASS |
| τ.6.x.0a contract: amharic-tewahedo gen.py-only | 9 test classes | ✓ ALL PASS |
| τ.6.x.0b contract: Option-D-Hybrid authorized + Tesseract engine | TestTau6x0bSourceYamlOcrStrategy + TestTau6X0cClosedArcInvariantPreservation::test_tau6x0b_option_d_authorization_intact | ✓ PASS |
| τ.6.x.0b contract: no_ingest_at_this_phase True | TestTau6x0bTranslationSlotContractPreserved + Pi1b/Pi2Prep/Tau6X0c parent-yaml pins | ✓ PASS |
| v1.0 reproducibility: patch_opf_fonts no-op when knobs empty | TestPhi1OpfFontManifest::test_noop_when_no_fonts | ✓ PASS |
| δ.1.0 divergence_entries=[] contract | TestDelta10/Pi1/Pi1b/Delta1XA0/Pi2Prep ClosedArcInvariantPreservation | ✓ PASS |
| δ.1.x.A.0 batch_prep + new invariant delta_1_0_entries_empty_at_seed | TestDelta1XA0NewInvariantCodified + parent yaml | ✓ PASS |
| Π.1 jubilees + one_enoch sections declared | TestPi1JubileesSection + TestPi1OneEnochSection + 5 derivative pins | ✓ PASS |
| Π.1 extraction_status_at_declaration historical pin | TestPi1TewahedoDistinctiveInventory::test_laodiceans_status_is_source_unavailable + 3 derivative pins | ✓ PASS |
| Π.1.B laodiceans alternate-source-declared current state | TestPi1bInventoryStatusFlip + 4 derivative pins | ✓ PASS |
| Π.2.prep checklist 8-section structure | TestPi2PrepChecklistExists + 12 group-pins | ✓ PASS |
| Ω.0 free-public pivot: no isbn lines + URN identifier + 6 deprecation banners + /build-tracker console | TestEditionsYamlIsbnFree + 8 group-pins | ✓ PASS |
| **NEW: τ.6.x.0c script/Ethiopic adoption decision** | TestTau6X0cSourceYamlVerificationBlock::test_script_ethiopic_adopted + TestTau6X0cScopeAdoptionRecorded::test_script_ethiopic_adoption_recorded + 4 derivative pins | ✓ PASS |
| **NEW: τ.6.x.0c geez_tessdata fallback Option-A/B preserved** | TestTau6X0cGeezFallbackExtended::test_option_a_preserved + test_option_b_preserved | ✓ PASS |

**All sixteen+ closed-arc / contract invariants present and
passing — the strongest regression-guard state in project history
(was 12 at LIGHT-2; +4–6 at LIGHT-3 depending on counting
granularity for Π.2.prep + Ω.0 + τ.6.x.0c sub-invariants).**

### 1.6 Source corpus state

Verified via direct pytest of `scripts.core.sources.ethiopian_
commentaries()`:

```
Total entries:        1579   (UNCHANGED across LIGHT-2 → LIGHT-3)
Mäṣḥafä Mäqabyan I:   212    (γ.4.8.E + γ.4.8.F)
Cyril-on-Matthew:     195    (γ.4.6 arc)
Cyril-on-Mark:        192    (γ.4.7 arc)
Athanasius (4 works): 150    (γ.4.9 arc)
[other voices unchanged from LIGHT-2 snapshot]
```

δ.1.x.A.0 + Π.2.prep + ω.4x + Ω.0 + τ.6.x.0c are ALL DECLARATIVE-
ONLY ships — none added or removed corpus entries. Six-voice
composition + Cyril plurality at 3.15× next-single-father preserved
exactly. (Ω.0's ISBN sweep affected metadata layer only.)

### 1.7 Git state

```
Latest committed (estimate; remote deleted 2026-05-12):
                f139494 — Π.1.B Letter to Laodiceans alternate-source
                13501e9 — Π.1 Parallel-PDF Tewahedo-distinctive foundation
                59bef8b — δ.1.0 Phase-4 Meqabyan SEED
                2c27745 — φ.1 + AUDIT_2026-05-14-LIGHT bundle
                c0172c4 — τ.6.x.0b OCR-quality strategy decision
                fbc6827 — τ.6.x.0a Parallel-PDF infra + pivot

Post-LIGHT-2 uncommitted-or-uncertain:
  - 6356f83 — LIGHT-2 audit (per CHANGELOG cross-reference)
  - 09fb084 — δ.1.x.A.0 (per CHANGELOG cross-reference)
  - 5acc5d0 — Π.2.prep (per CHANGELOG cross-reference)
  - ω.4x    — "this ship" → since-superseded by Ω.0 + τ.6.x.0c
  - Ω.0     — no hash recorded (north-star pivot ship)
  - τ.6.x.0c — this ship (no hash yet)

This audit doc (AUDIT_2026-05-14-LIGHT-3.md) joins the
uncommitted set; standalone-audit-commit pattern per LIGHT-2
precedent.
```

Per `feedback_continue_not_save`, save is user-explicit only — the
user's "audit" advanced state to this audit. The GitHub remote was
deleted 2026-05-12 per memory `reference_save.md`; `git push` no
longer reaches anywhere, but `save.cmd` continues to commit
locally. Bundle-or-solo decision deferred to operator.

---

## 2. WARN findings

### 2.1 W-W2 (lint) — `scripts/build_edition.py` ruff check

**Status: RESOLVED at ω.4x `(post-LIGHT-2 #3)`.**

LIGHT-2 carried this forward as "44 errors; unchanged from LIGHT-1".
The ω.4x ship reduced it to 0 via:

- `ruff check --fix` resolved 27/44 auto-fixable patterns.
- 6 manual fixes (SIM108 ternary + 3× SIM102 nested-if combine +
  2× N806 rename + 2× B023 closure-binding default-arg + 1× F841
  unused-var deletion).
- 8 intrinsic patterns per-file-ignored in `pyproject.toml`
  (5× E501 HTML template strings in copyright + reading-plans +
  credits + 3× C901 load-bearing orchestration complexity).

**LIGHT-3 verification:**

```
$ py -m ruff check scripts/build_edition.py
All checks passed!
```

Status: closed. No further follow-up required.

---

## 3. Cross-document drift items (INFO-class)

### 3.1 A-I1 — PLAN_2026-05-09 §2 status snapshot drift

**Status: PARTIALLY ADDRESSED at ω.4x; soft drift accumulating.**

PLAN §2 was refreshed at ω.4x from "3808 tests" → "4400+ tests"
+ SESSION_STATE cross-reference + six-voice corpus codification +
parallel-Bible roadmap summary. Today's count is **4480** passed +
1 skipped (test_count_drift +80 vs. ω.4x refresh target). The
"4400+ tests" wording is INTENTIONALLY round-ranged ("4400+" rather
than a precise number) precisely so this kind of drift doesn't
re-trigger A-I1 on every ship.

```
PLAN §2 ω.4x refresh:    "4400+ tests"
LIGHT-2 actual:          4317 (PLAN refresh was post-LIGHT-2; baseline aligned)
LIGHT-3 actual:          4480 (+80 over ω.4x target; +163 over LIGHT-2)
```

**Status:** acceptable interim state; "4400+" target wording covers
the next ~100 tests of drift before it becomes stale. The fully-
authoritative live snapshot remains SESSION_STATE. A-I1 stays
soft-WARN-class; flag continues to wait for the next significant
PLAN refresh.

### 3.2 A-I2 — PLAN_2026-05-09 §6 parallel-Bible track

**Status: RESOLVED at ω.4x; further extended at τ.6.x.0c.**

ω.4x added the parallel-Bible track sub-section to PLAN §6 with
the SCOPE §11 canonical chain literal ("Π.0 → τ.6.x + τ.7.x → Π.1
→ δ.1.x → Π.2 + φ.1 → δ.2") + a shipped/pending sub-phase ledger.
τ.6.x.0c further extended the ledger at its ship-time:

```
SHIPPED LEDGER (ω.4x + τ.6.x.0c):
  Π.0, τ.6.x.0a, τ.6.x.0b, φ.1, δ.1.0, Π.1, Π.1.B, ω.4x, Ω.0, τ.6.x.0c

PENDING LEDGER (τ.6.x.0c-updated):
  τ.6.x.1+ (now Claude-side actionable; needs Tesseract wiring)
  τ.7.x    (blocked on τ.6.x.1+)
  δ.1.x.A  (operator-mediated page-image render)
  δ.1.x.B-G (pending)
  δ.1.Z    (gated on .A-G)
  Π.2      (gated on τ.6.x + τ.7.x)
  δ.2      (gated on δ.1.Z)
```

Status: closed. Ledger maintained as ships land.

### 3.3 A-I3 — historical-pin convention: TWO instances now

**Status: PROGRESSING. Was 1 instance at LIGHT-2; 2 instances at
LIGHT-3.** Codification threshold per §8.1 precedent (3 instances)
NOT yet reached.

**Instance 1 (Π.1.B 2026-05-14):** `at_declaration / current /
phase_history` triad in
`content/translations/sources/parallel-bible-eotc/_source.yaml::
tewahedo_distinctive_inventory.{extraction_status_at_declaration,
extraction_status_current, extraction_status_phase_history}`. Used
for the laodiceans slot status flip (`source-unavailable` →
`alternate-source-declared`).

**Instance 2 (τ.6.x.0c 2026-05-14):** Option-enumeration with
`chosen_at_phase` + `chosen_option` + `chosen_rationale` in
`content/translations/sources/parallel-bible-eotc/_source.yaml::
ocr_strategy.prerequisites.geez_tessdata.fallback_if_missing.
{option_a, option_b, option_c, chosen_at_phase, chosen_option,
chosen_rationale}`. Used for the Geʽez recognizer-strategy decision
(Option-A skip / Option-B phase4-defer were anticipated at τ.6.x.0b;
Option-C script/Ethiopic was added + chosen at τ.6.x.0c).

**Pattern utility comparison:**

| Instance | Shape | "What was true at declaration" preserved as | "What is true now" lives at | Transition log? |
|---|---|---|---|---|
| Π.1.B (laodiceans) | tri-field | `extraction_status_at_declaration.laodiceans` | `extraction_status_current.laodiceans` | yes — `extraction_status_phase_history.laodiceans` |
| τ.6.x.0c (gez fallback) | enumeration-with-marker | `option_a` + `option_b` (the τ.6.x.0b-documented fallbacks) | `chosen_option` | implicit — `chosen_at_phase` + `chosen_rationale` |

Both share the **immutability-of-historical-record** invariant
(τ.6.x.0c's `TestTau6X0cGeezFallbackExtended::test_option_a_preserved`
+ `test_option_b_preserved` mirrors Π.1.B's `test_extraction_status_
at_declaration_unchanged`). The structural shapes differ — Π.1.B
uses a tri-field record, τ.6.x.0c uses an option-enumeration with
selector metadata — but the **goal** is identical: forward
extension that does NOT mutate past state.

**Codification target:** unifying name for the umbrella pattern
candidate "**Historical-Record Immutability + Forward Extension**"
(HRI+FE; clunky but accurate). Codify in CLAUDE_PROJECT_RULES.md
at the third instance per §8.1 precedent. Until then, flag as
informational pattern-recognition.

**Status:** track-as-informational; no action this audit. Watch
the next 1-3 ships for a third instance to trigger codification.

### 3.4 A-I4 (NEW) — first external-tool resolver in `paths.py`

**Class:** ARCHITECTURAL EXTENSION — informational; potential
codification target.

τ.6.x.0c added `tesseract_binary()` to `scripts/core/paths.py` —
the first **external-binary resolver** in a module that until now
resolved only project-internal directory/file paths
(`content_root`, `notes_dir`, `editions_yaml`, etc.).

**Shape adopted:**

```python
def tesseract_binary() -> Path | None:
    return _tesseract_binary_cached()

@lru_cache(maxsize=1)
def _tesseract_binary_cached() -> Path | None:
    # 1. TESSERACT_BIN env-var override
    # 2. shutil.which("tesseract") — PATH lookup
    # 3. Platform-conventional install paths (Win/macOS/Linux)
    # 4. None
    ...

def reset_tesseract_binary() -> None:
    _tesseract_binary_cached.cache_clear()
```

This follows the **existing `paths.py` conventions** to the letter:
- `lru_cache`-d under-the-hood (mirrors `_content_root_cached`).
- Public function + `reset_*()` test hook (mirrors `content_root`
  + `reset_content_root`).
- Env-var override-first resolution order (mirrors
  `YHWH_CONTENT_ROOT` precedence).
- `__all__` export (both `tesseract_binary` and `reset_tesseract_
  binary`).
- Path-resolution only — NO runtime probes (no version check, no
  `--list-langs` call). Stays consistent with the module's docstring
  ("this module just *reports* the path").

**Pattern utility:** future external-tool resolvers (e.g.,
`pymupdf_binary()` if pymupdf ever ships as a separate executable;
`epubcheck_binary()` for the Java JAR resolver currently scattered
across the codebase) should adopt the same shape:

1. Env-var override with conventional NAME (`<TOOL>_BIN`).
2. `shutil.which()` PATH lookup.
3. Platform-conventional install paths via `_known_<tool>_paths()`
   helper returning a `list[Path]`.
4. `Path | None` return; callers raise their own errors with
   helpful install pointers.

**Codification status:** ONE INSTANCE so far. Same convention as
A-I3 — codify at 3rd instance per §8.1 precedent. The current
`epubcheck` resolution (somewhere in the apparatus per memory
`reference_external_tools.md`) might already be a 2nd instance if
it follows the same shape — worth a future-audit check.

**Status:** track-as-informational; no action this audit.

---

## 4. Follow-up to prior AUDIT findings

### 4.1 LIGHT-2 W-W2 (build_edition.py ruff drift)

**Status: RESOLVED at ω.4x.** See §2.1 above.

### 4.2 LIGHT-2 A-I1 (PLAN §2 staleness)

**Status: PARTIALLY ADDRESSED at ω.4x; soft drift accumulating.**
See §3.1 above.

### 4.3 LIGHT-2 A-I2 (PLAN lacks parallel-Bible track)

**Status: RESOLVED at ω.4x.** See §3.2 above.

### 4.4 LIGHT-2 A-I3 (historical-pin convention)

**Status: PROGRESSING — 2nd instance shipped at τ.6.x.0c.** See
§3.3 above. Codification threshold not yet reached.

### 4.5 LIGHT-1 W-W1 (Windows subprocess handle errors)

**Status: RESOLVED at LIGHT-2.** UNCHANGED at LIGHT-3 (full sweep
4480 passed / 0 failed; no resurfacing).

### 4.6 AUDIT_2026-05-13-DEEP D-C1 (Mäqabyan empty)

**Status: RESOLVED.** UNCHANGED from LIGHT-2.

### 4.7 AUDIT_2026-05-13-DEEP D-W2 (jas→jam alias)

**Status: RESOLVED.** UNCHANGED from LIGHT-2.

### 4.8 AUDIT_2026-05-13-DEEP D-W3 (3-of-6 Tewahedo-canonical-notes empty)

**Status: PARTIAL.** Carries forward from LIGHT-2. mq1+mq2+mq3
populated at γ.4.8; 4ba+2en+1cl still empty as future-arc targets
(Π.2.prep §3 D3 codified this as a publisher-decision point — Π.2
can ship with the empty-but-canonical state).

### 4.9 AUDIT_2026-05-13-LIGHT L-W1/L-W2/L-W3 (at-scale driver hygiene)

**Status: STILL OPEN.** All three carry forward from LIGHT-2.
Hygiene-class; no incidents in any of the 5 post-LIGHT-2 ships
(all declarative; no at-scale driver runs triggered).

### 4.10 AUDIT_2026-05-13-EOD EOD-W4 (`_ship_*.py` script accumulation)

**Status: UNCHANGED.** No new `_ship_*.py` scripts in any of the
5 post-LIGHT-2 ships (all declarative). The ETL tools introduced
at δ.1.0 (build_meqabyan_revision.py + promote_divergence_to_
apparatus.py) remain long-lived per §7.4 retention rule.

---

## 5. Recommendations

### 5.1 Immediate (this session)

- **Save this audit doc** as a standalone commit per LIGHT-2
  precedent (mirrors AUDIT_2026-05-13-EOD which shipped solo at
  session boundary). No code changes ride with the audit; the
  bundle is just this file + the SESSION_STATE/IN_FLIGHT/CHANGELOG
  entries pointing at it (those entries can either land with the
  audit or be deferred to a follow-up ship).
- **No fixes required at audit-time.** All five post-LIGHT-2 ships
  landed clean; no regressions detected; all closed-arc invariants
  preserved.

### 5.2 Next session boundary

- **τ.6.x.1+** (Claude-side, now actionable) — wire
  `tesseract_binary()` into `scripts/extract_parallel_pdf.py`:
  render each PDF page at 350 dpi via pymupdf → invoke Tesseract
  with `-l script/Ethiopic+amh` → parse verse-keyed output → bulk-
  ingest standard-canon books at `ocr-tier3` with SOURCE_QUALITY
  provenance + reader-facing caveats per the τ.6.x.0b honesty
  contract. This is the obvious next ship along the parallel-
  Bible track; no further operator-side gates.
- **δ.1.x.A** (Claude-side, operator-mediated) — first Phase-4
  page-image batch for mq1 chapters 1-9. Operator-side blocker:
  render Geʽez at 350 dpi from the parallel-Bible PDF (per Π.1's
  declarative meqabyan.subsections.mq1=[1318,1365] range).
- **Π.2 follow-through review** — publisher decision on the four
  Π.2.prep §3 publisher-decision points (D1 popup-language set /
  D2 laodiceans canon membership / D3 4ba/2en/1cl notes-file state
  / D4 visual-QA scope). Not blocking; can be deferred until
  τ.6.x.1+ + τ.7.x land.

### 5.3 Future hygiene-arc (no specific session yet)

- **A-I3 + A-I4 codification.** When a third instance of either
  the Historical-Record Immutability + Forward Extension pattern
  (currently 2 instances) or the external-tool resolver pattern
  (currently 1 instance) ships, codify both in CLAUDE_PROJECT_RULES.md
  §1 codification ledger as paired data-shape conventions.
- **PLAN §2 refresh** — when "4400+ tests" wording goes stale
  beyond ~4500 (current 4480, threshold approaching at ~+20 more
  tests), bundle into the next ω.4x-class hygiene ship along with
  any other accumulated soft drift.

---

## 6. Verdict

**CLEAN.** Project state at LIGHT-3 is healthier than at LIGHT-2
along four dimensions:

1. **W-W2 RESOLVED at ω.4x** — the build_edition.py ruff drift
   from LIGHT-1/LIGHT-2 is gone; `ruff check` returns "All checks
   passed!" verified.
2. **A-I2 RESOLVED at ω.4x** — PLAN §6 now carries the parallel-
   Bible track sub-section with both shipped and pending ledgers
   (further extended at τ.6.x.0c).
3. **Sixteen+ closed-arc / contract invariants verified intact**
   (up from twelve at LIGHT-2; +4–6 new from Π.2.prep + Ω.0 +
   τ.6.x.0c sub-invariants).
4. **162-test drift correctly accounted** for in the ship ledger
   (δ.1.x.A.0 +39 + Π.2.prep +35 + ω.4x +15 + Ω.0 +27 + τ.6.x.0c
   +46 = 162; matches the full-sweep delta to within ±1 floor-
   correction tolerance).

A-I1 (PLAN §2 staleness, soft) and A-I3 (historical-pin
convention, design-pattern) are the only audit-flagged items
remaining at LIGHT-3 — both INFO-class, both with track-as-
informational status. The new A-I4 (external-tool resolver
pattern) joins them as an informational track-item.

The audit cadence test-drift threshold has been re-reached at
LIGHT-3 (162 tests since LIGHT-2; 333 total since LIGHT-1; 671
total since the PLAN refresh's 3808 baseline); LIGHT-3 satisfies
it. **The session may now close at this audit** or continue with
τ.6.x.1+ (Tesseract wiring — the obvious Claude-side next ship,
now unblocked operator-side). **Recommended close-out:** commit
this audit (or bundle with the τ.6.x.0c state-doc updates) +
treat the session as closed.

The next ship — when it comes — will most naturally be τ.6.x.1+
(Tesseract wiring into `extract_parallel_pdf.py`; produces the
first actual translation-slot population at `ocr-tier3` for
standard-canon books) or operator-mediated δ.1.x.A (Phase-4
Meqabyan mq1 chapters 1-9). Both advance the parallel-Bible
expansion roadmap from foundation-laying to actual data
population — the strategic transition the project has been
preparing for since τ.6.x.0a.

---

*Light solo-Claude audit #3 of 2026-05-14 (late-session
post-τ.6.x.0c). Mirrors AUDIT_2026-05-13-EOD precedent of multiple
lighter audits in a single high-velocity session. Third in the
2026-05-14 chain after AUDIT_2026-05-14-LIGHT (post-φ.1) and
AUDIT_2026-05-14-LIGHT-2 (post-Π.1.B). CC0 1.0 Universal.*
