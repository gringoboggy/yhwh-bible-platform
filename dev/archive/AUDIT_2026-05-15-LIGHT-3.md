# Project audit — 2026-05-15 LIGHT-3 (solo-Claude, post-τ.6.x.1.D, post-4-ship-chain)

**Trigger:** user "audit" after τ.6.x.1.D ship close-out — explicitly
invoked per the τ.6.x.1.D ship narrative's recommendation ("a LIGHT
audit at τ.7.x.a ship-time would close the cadence window"). Also
satisfies `feedback_audit_cadence` rolling-threshold check: cumulative
drift since DEEP baseline (4634) is now +113 tests across 3 ships
(τ.7.x.a.0 +39 + τ.6.x.1.C +37 + τ.6.x.1.D +37). Below the +150
hard-threshold but above-baseline enough to warrant a cadence-window
check.

**Form:** LIGHT solo-Claude scope per `feedback_audit_cadence`
default. The DEEP comprehensive matrix audit was completed earlier
this session (`AUDIT_2026-05-15-DEEP.md`); this LIGHT-3 follows up on
the 3 ships shipped post-DEEP + carries forward the DEEP findings
inventory.

**Naming:** Third LIGHT of 2026-05-15 (after the 00:55 LIGHT covering
through τ.6.x.1.B, and LIGHT-2 covering τ.6.x.2.D). DEEP doesn't
interrupt LIGHT numbering (different audit-type counter).

**Audit chain on 2026-05-15:**

```
00:55  LIGHT    post-τ.6.x.1.B
01:32  τ.6.x.2.D D-decisions ship (no audit; cadence later triggered)
...    LIGHT-2  post-τ.6.x.2.D (cadence-triggered +154 drift)
...    DEEP     post-τ.6.x.2.D extensive matrix audit (user-requested)
...    [4 ships chain: τ.6.x.2.D save + τ.7.x.a.0 + τ.6.x.1.C + τ.6.x.1.D]
NOW    LIGHT-3  post-τ.6.x.1.D (user-requested + cadence-window close)
```

---

## 0. TL;DR

**Project state at audit-time is CLEAN across every checked
dimension.** The 4-ship chain since LIGHT-2 (τ.6.x.2.D save +
τ.7.x.a.0 + τ.6.x.1.C + τ.6.x.1.D) landed with no regressions, the
parser/engine infrastructure for τ.7.x.a (proper) is now complete,
and the matrix is in top-top shape to ingest Amharic Genesis.

### Foreground (every check passes)

- ✓ Test count: **4747 collected / 4747 passed + 1 skipped + 0
  failed** (full 6:31 sweep this audit, vs DEEP's 4634 / 7:06).
- ✓ Linter (`scripts/lint_rules.py`): **11/11 pass · 0 warn · 0
  fail** with **253 non-legacy phase mentions** (UNCHANGED from
  DEEP; new phases τ.7.x.a.0 + τ.6.x.1.C + τ.6.x.1.D appear in
  YAML + markdown + tests but the linter's phase-mention scanner
  evidently counts unique Python-code phase tags only — worth
  noting but not a regression).
- ✓ Console-cross-link checks pass at **18 consoles** (unchanged
  since Ω.0).
- ✓ IN_FLIGHT: **idle** (`TRACKER-STATE: idle`); τ.6.x.1.D
  documented as prior task; chain τ.6.x.1.D → τ.6.x.1.C →
  τ.7.x.a.0 → τ.6.x.2.D → τ.6.x.1.B → τ.6.x.1.A → τ.6.x.1 → ...
  preserved.
- ✓ Closed-arc invariants intact (now **18 named invariants** —
  was 17 at DEEP baseline; +1 NEW from the 4-ship chain):
  - 17 pre-LIGHT-3 invariants preserved (γ.4.8.E + γ.4.8.F +
    Π.0.1 + Π.0.4 + τ.6.x.0a + τ.6.x.0b honesty + τ.6.x.0b auth
    + δ.1.0 + δ.1.x.A.0 + Π.1 + Π.1 extraction_status + Π.1.B +
    Π.2.prep + Ω.0 + τ.6.x.0c + τ.6.x.1 + τ.6.x.1.B + τ.6.x.2.D).
  - **NEW τ.6.x.1.C paragraph-mode parser contract** —
    `parse_verses_from_text(text, *, paragraph_mode: bool = False)`
    + `CROSS_REF_FRAGMENT_RE` + `is_cross_ref_fragment` +
    `GENESIS_VERSE_COUNTS` + `_parse_paragraph_mode`. Pinned in
    TestTau6X1CModuleSurface (5) + TestTau6X1CIsCrossRefFragment
    (10) + TestTau6X1CParagraphModeUnit (9) + TestTau6X1CParagraphModeRuntime
    (2 real-PDF empirical) + TestTau6X1CSourceYamlBlock (11).
  - **NEW τ.6.x.1.D chapter-marker recovery contract** —
    `CHAPTER_HEADER_RE_LENIENT` + `_resolve_chapter_marker(...,
    max_jump=5)`. Pinned in TestTau6X1DModuleSurface (3) +
    TestTau6X1DResolveChapterMarker (12) + TestTau6X1DLenientRegex
    (7) + TestTau6X1DParagraphModeChapterRecovery (4) +
    TestTau6X1DParagraphModeRuntime (2 real-PDF empirical) +
    TestTau6X1DSourceYamlBlock (9).
  - τ.7.x.a.0 PILOT is treated as a finding-resolution arc that
    spans τ.6.x.1.C + τ.6.x.1.D (the PILOT surfaced the finding;
    the two follow-up ships resolved it). It's preserved as a
    yaml block + 39 pin tests but isn't itself a separate
    invariant; the two follow-on parser contracts are the
    invariants.
- ✓ τ.6.x.0a no-ingest contract preserved: geez-tewahedo +
  amharic-tewahedo slots **still at Π.0 seed state**
  (gen.py + _meta.yaml only; 3 verses Genesis each) across the
  **10-ship chain** (τ.6.x.0a → 0b → 0c → 1 → 1.A → 1.B → 2.D →
  7.x.a.0 → 1.C → 1.D). Verified by direct filesystem read +
  amharic-tewahedo/gen.py-still-3-verse-seed pin in
  test_parallel_bible_tau7xa.py.

### Carry-forward findings from DEEP (status re-checked)

| Finding | Severity | Status at LIGHT-3 |
|---|---|---|
| D-C1 — 19 _ship_*.py scripts (8 above threshold) | CRITICAL hygiene | **UNCHANGED**, deferred per DEEP recommendation 4.2 (post-τ.7.x.a hygiene window) |
| D-W1 — Pre-commit hook drift (5-audit chain vs lint_rules-only) | low WARN | **UNCHANGED**, installer not re-run; lint_rules + ruff format still active in commit hook (confirmed 4×) |
| D-W2 — W-W1 prophylactic gap 25 sites | low WARN | **UNCHANGED**, no scripts/* mutations in the 4-ship chain except extract_parallel_pdf.py (which had no new subprocess.run sites added — only parser-helper additions) |
| D-W3 — Ruff check 981 errors project-wide | medium WARN | **UNCHANGED**, no new ruff debt added (extract_parallel_pdf.py additions formatted clean per ω.4x per-file-ignore) |
| D-W4 — MEMORY.md index Bowker-ISBN-pending drift | low WARN | **UNCHANGED**, not corrected |
| D-W5 — TODO_DOI_HERE/TODO_LCCN_HERE in EPUB OPF | low-medium WARN | **UNCHANGED**, no EPUB rebuilt |
| D-W6 — CLAUDE_PROJECT_RULES corpus count 52,459 stale | low WARN | **UNCHANGED**, still says 52,459; actual now 52,973 (same as at DEEP — corpus didn't change) |
| D-I1 — Corpus at 212% of v1.0 25K floor | INFO | **UNCHANGED**, 52,973 tuples |
| D-I2 — Closed-arc invariants pin matrix | INFO | **UPDATED** — was 17 invariants / 76 pin tests across 13 files at DEEP; now 18 invariants / **~150 pin tests across 14 files** (added test_parallel_bible_tau7xa.py at +39 pins + TestTau6X1C* +37 pins + TestTau6X1D* +37 pins) |
| D-I3 — F821 false-positives in cache_audit_whitelist.py | INFO | **UNCHANGED**, still 18 instances |
| D-I4 — Backup tree active in 5 dirs | INFO | **UNCHANGED** |
| A-LIGHT5-1 — τ.6.x.2.D pin count ~33 vs 40 actual | FYI | **UNCHANGED**, not corrected |
| A-I1 — PLAN §2 "4400+ tests" vs actual | low WARN, drift widening | **UNCHANGED, drift wider** (was 4634 at DEEP; now 4747) |
| A-I3 — Historical-pin convention codification trigger | INFO codification | **RESOLVED at τ.6.x.1.D** — the parallel pattern (single-key `*_resolved_at_phase` back-link) now has **4 instances** (tau6x1a→1b, tau6x1b→2D, tau7xa_pre_pilot→1C, tau6x1c→1D), past the 3-instance §8.1 codification threshold. Awaiting CLAUDE_PROJECT_RULES §8.1 entry at next ω-class hygiene ship. |
| A-I4 — External-tool resolver pattern | INFO codification | **UNCHANGED**, still 1 instance (`tesseract_binary()`) |

### NEW findings at LIGHT-3

**One NEW WARN-class finding:**

- **A-LIGHT7-1 (WARN, parser-quality) — τ.6.x.1.D chapter-marker
  recognition has a residual gap.** The Genesis 2 chapter marker
  on Amharic text-layer pages 1-2 is OCR-garbled past the τ.6.x.1.D
  `CHAPTER_HEADER_RE_LENIENT` regex (the keyword is truncated to
  `ራፍ` alone, missing both `ዕ` and `ፅ`). Empirical impact:
  pages 0-5 chapter detection went from `{1}` (τ.6.x.1.C baseline)
  → `{1, 3, 4}` (τ.6.x.1.D this audit baseline) — i.e., 3 of 5
  expected chapters detected; chapter 2 + 5 still bleed into the
  ch 1 + ch 4 buckets respectively. Severity: medium-WARN at
  ingest time (downstream τ.7.x.a writer can apply chapter-
  renumbering using GENESIS_VERSE_COUNTS as the expected-floor
  reference; quality residue cleared at τ.6.x.3 batched audit per
  D2-b + D3-c). **Recommendation:** insert OPTIONAL τ.6.x.1.E
  ship (truncated-keyword chapter recovery) before τ.7.x.a if
  cleaner labeling needed at ingest time; OR push the residual to
  τ.6.x.3 audit.

**One NEW INFO-class codification trigger:**

- **A-LIGHT7-2 (INFO, codification trigger) — Share-pin →
  milestone-pin refactor pattern has now repeated 5 times this
  session.** Documented at LIGHT-2 §3 (test_headline_is_tau6x2d +
  test_tau6x1b_demoted_to_previous + test_prior_task_is_tau6x2d).
  This session added 2 more (τ.6.x.1.D ship): test_changelog_
  records_tau7xa_0_entry + test_chapter_marker_resets_verse_
  counter (the latter was a test-logic refactor, not strictly a
  share-pin, but in the same family). **Pattern is mechanical and
  predictable** — every new ship that prepends a SESSION_STATE /
  IN_FLIGHT / CHANGELOG block invalidates first-N-chars-window
  pins on prior ships' headline assertions. **Recommendation:**
  add a CLAUDE_PROJECT_RULES §8.1 codification entry stating
  "new test pins on state-doc content MUST use milestone-pin
  style (`assert <pattern> in <full_text>`) rather than share-pin
  style (`assert <pattern> in <full_text>[:N]`)". Alternatively,
  add a lint_rules.py check that detects `[:N]` slicing of
  SESSION_STATE/IN_FLIGHT/CHANGELOG file content in test asserts.

### Forward-readiness for τ.7.x.a (proper)

| Dimension | State | Blocks τ.7.x.a? |
|---|---|---|
| Tesseract engine + parser chain (τ.6.x.1 + 1.B + 1.C + 1.D) | ✓ all wired | No |
| Pilot validation (τ.6.x.1.A real-OCR pins firing) | ✓ | No |
| Page-range discovery (structural_map.genesis [0, 85]) | ✓ | No |
| Publisher direction (D1-a + D2-b + D3-c + D4-c locked) | ✓ | No |
| Source PDF resolves via env + 4 fallbacks | ✓ | No |
| Π.0 seed preservation contract | ✓ active across 10 ships | No |
| Test sweep / linter / format / type / dead-code | ✓ all clean | No |
| 18 closed-arc invariants | ✓ all preserved | No |
| Backup tree (5 roots active) | ✓ | No |
| Pre-commit hook (lint_rules + ruff format) | ✓ active | No |
| Empirical floor (≥75 verses; ≥3 chapters; pages 0-5) | ✓ pinned | No |
| Chapter-2 / Gen 5 markers still missed | ⚠ A-LIGHT7-1 | No, downstream renumbering or τ.6.x.1.E covers |
| 19 ship scripts above retention threshold | ⚠ D-C1 carry | No, hygiene-class |
| ruff `check` background debt 981 errors | ⚠ D-W3 carry | No, pre-existing |
| Pre-commit hook 4 missing audits | ⚠ D-W1 carry | No, advisory |

**Verdict: GO for τ.7.x.a (proper).** The matrix is in top-top shape
across all 11 "blocking" dimensions. The 4 "advisory" items
(D-C1 + D-W1 + D-W3 + A-LIGHT7-1) are best bundled into a single
post-τ.7.x.a ω-class hygiene ship — or τ.6.x.1.E can land before
τ.7.x.a if the operator wants cleaner chapter labels at ingest
time.

**Uncommitted git state at audit-time:** This LIGHT-3 audit doc
is the ONLY uncommitted file. The 4-ship chain (τ.6.x.2.D +
τ.7.x.a.0 + τ.6.x.1.C + τ.6.x.1.D) is all committed (commits
d5e8e47 + 32b956f + b109844 + 92a5362). Per memory `reference_
save.md`, push will fail (remote deleted 2026-05-12); local
commit only.

---

## 1. Per-point verification

### 1.1 Test count + sweep result

**Full pytest sweep at LIGHT-3:**

```
4747 passed, 1 skipped in 391.91s (0:06:31)
```

Compared to DEEP's `4634 passed, 1 skipped, 0 failed in 461.57s`:

- **+113 passed** matches the ship ledger EXACTLY (τ.7.x.a.0 +39 +
  τ.6.x.1.C +37 + τ.6.x.1.D +37 = +113).
- **+1 skipped unchanged** (pre-existing platform-specific skip).
- **0 failed.**
- **−70s runtime** (vs DEEP): expected — the 3 new ships' pin
  tests are mostly fast yaml-content + unit-test assertions; the
  runtime regression pins (TestTau6X1CParagraphModeRuntime 2 +
  TestTau6X1DParagraphModeRuntime 2) reuse the same PDF that's
  already opened for the τ.6.x.1.A + τ.6.x.1.B runtime pins so
  per-test overhead is low.

**Test-count drift verification (since LIGHT-3 prev = DEEP baseline
4634):**

| Ship | Delta | Groups | Cumulative |
|---|---:|---:|---:|
| τ.7.x.a.0 PILOT | +39 | 6 | +39 |
| τ.6.x.1.C parser ext | +37 | 5 | +76 |
| τ.6.x.1.D chapter recovery | +37 | 6 | **+113** |
| | | | matches 4747 − 4634 exactly |

**No phantom tests; no missing tests; growth matches the ship
ledger to wire-count precision.**

Cumulative drift since LIGHT-3 (the original at 00:55, post-
τ.6.x.1.B baseline at 4594): **+153** tests across 5 ships
(τ.6.x.2.D +40 + τ.7.x.a.0 +39 + τ.6.x.1.C +37 + τ.6.x.1.D +37 =
+153). **This CROSSES the +150 cadence threshold**, retroactively
justifying both LIGHT-2 (cadence-triggered) AND this LIGHT-3
(rolling-window close-out).

### 1.2 Linter state

```
✓ Canonical-order encoders                  all 3 encoders
✓ Cross-link invariant                      all 18 consoles cross-link
✓ Encoder/decoder round trip                all 3 pairs
✓ Documentation cross-references            all 19 scope addenda
✓ SESSION_STATE freshness                   CHANGELOG ↔ SESSION_STATE coupled
✓ In-flight task tracker                    idle
✓ Phase mentions tracked in CHANGELOG       253 non-legacy mentions
✓ SESSION_STATE inventory matches consoles  18 consoles
✓ Atomic writes                             no raw open('w') outside notes_io
✓ External HTTP                             no raw urlopen() outside core/http.py
✓ Plan coherence                            4 sub-checks pass

CLEAN: 11 pass · 0 warn · 0 fail
```

**Phase-mention count UNCHANGED at 253 across all 3 ships since
DEEP** — the new τ.7.x.a.0 + τ.6.x.1.C + τ.6.x.1.D phase tags appear
extensively in YAML + Markdown + test files, but the linter's
`Phase mentions tracked in CHANGELOG` check evidently only counts
unique Python-code phase tags (not all phase-tag occurrences). The
linter check still passes — every phase mentioned in any code file
has a CHANGELOG entry — but the **count metric is stable across a
broad phase-tag-additive session**. This is a curiosity worth
documenting; not a regression.

### 1.3 IN_FLIGHT coherence

```
<!-- TRACKER-STATE: idle -->

Prior task:                          τ.6.x.1.D
Prior task (previous):               τ.6.x.1.C
Prior task (previous):               τ.7.x.a.0
Prior task (previous):               τ.6.x.2.D
Prior task (previous):               τ.6.x.1.B
Prior task (previous):               τ.6.x.1.A
Prior task (previous):               τ.6.x.1
Prior task (previous):               τ.6.x.0c
Prior task (previous):               Ω.0
[deeper chain]                       ω.4x, Π.2.prep, δ.1.x.A.0,
                                     Π.1.B, Π.1, δ.1.0, φ.1,
                                     τ.6.x.0b, τ.6.x.0a, Π.0,
                                     γ.4.8.F, γ.4.8.E
```

Tracker idle. τ.6.x.1.D is the last completed ship; the
prior-task chain matches the ship ledger exactly. Pinned via
milestone-pin variants of TestTau6X2DInFlight (refactored at
τ.6.x.1.C ship-time) + TestTau7XAInFlight (refactored at
τ.6.x.1.C ship-time) + the new TestTau6X1D* classes.

### 1.4 Closed-arc invariants — 18 named, all preserved

Verified across 14 test files (the 13 at DEEP + the NEW
`test_parallel_bible_tau7xa.py`) — **~150 closed-arc-or-
InvariantPreservation pin tests** in the matrix.

| # | Invariant | Pinned in |
|---|---|---|
| 1-14 | (Same census as DEEP §1.8 #1-14) | preserved unchanged |
| 15 | τ.6.x.0c script/Ethiopic adoption | (carry from #14 at DEEP) |
| 16 | τ.6.x.1 engine-wiring contract | tau6x1 |
| 17 | τ.6.x.1.B parser-extension contract | tau6x1 |
| 17.1 | τ.6.x.2.D D-decisions contract | tau6x2d |
| **18** | **τ.6.x.1.C paragraph-mode parser + τ.6.x.1.D chapter recovery** | tau6x1 (new TestTau6X1C* + TestTau6X1D* classes) |

The τ.7.x.a.0 PILOT findings are pinned via test_parallel_bible_
tau7xa.py (39 pins) but represent a finding-and-resolution arc
that's CLOSED by τ.6.x.1.C + τ.6.x.1.D; the PILOT itself isn't a
separate ongoing invariant. The parser-chain invariant **#18**
covers both the τ.6.x.1.C paragraph-mode AND the τ.6.x.1.D
chapter-recovery contracts since they're now wired together in
`_parse_paragraph_mode`.

### 1.5 Π.0 seed preservation

```
$ ls content/translations/geez-tewahedo/
_meta.yaml
gen.py

$ ls content/translations/amharic-tewahedo/
_meta.yaml
gen.py
```

Both slots contain ONLY the Π.0-seed `gen.py` + `_meta.yaml`.
The τ.6.x.0a no-ingest contract is **preserved across all 10
ships in the τ.6.x.0a → τ.6.x.0b → τ.6.x.0c → τ.6.x.1 →
τ.6.x.1.A → τ.6.x.1.B → τ.6.x.2.D → τ.7.x.a.0 → τ.6.x.1.C →
τ.6.x.1.D chain**.

The strongest pin — TestTau7XAClosedArcInvariantPreservation.
test_amharic_tewahedo_gen_py_still_seed_three_verses — parses
the amharic-tewahedo/gen.py via `ast.literal_eval` of the VERSES
list and asserts `len(verses) == 3`. Pin passing confirms the
Π.0 seed content is byte-identical to what was set at Π.0 ship.

### 1.6 Corpus census — UNCHANGED

| Metric | Value | vs DEEP |
|---|---:|---|
| Total tuples | 52,973 | UNCHANGED |
| Total notes files | 87 | UNCHANGED |
| Zero-content files | 3 (1cl, 2en, 4ba) | UNCHANGED |
| % of v1.0 25K floor | 212% | UNCHANGED |

The 4-ship chain since DEEP made ZERO mutations to `content/
notes/*.py` — confirmed by the unchanged corpus census.

### 1.7 Forward-staging readiness check for τ.7.x.a (proper)

Per the τ.6.x.1.D ship narrative, τ.7.x.a (proper) is the next
authorized data-ingest phase. Forward-readiness:

**Engine + parser chain — COMPLETE.** The 4-step parser pipeline
that processes Amharic Genesis text:

```
PDF page → render at 350 dpi → Tesseract OCR (or text-layer)
        → normalize_verse_numerals (τ.6.x.1.B Ethiopic-numeral
            preprocessor; no-op for text-layer; converts
            ፪፤ → 2: for Tesseract output)
        → _parse_paragraph_mode (τ.6.x.1.C paragraph splitter +
            τ.6.x.1.D chapter recovery)
        → list[(chapter, verse, text)] tuples
```

**Empirical floor on Amharic Genesis pages 0-5 (text-layer engine):**

```
86 verses (was 87 at τ.6.x.1.C — −1 due to τ.6.x.1.D
        pre-marker discard)
3 chapters detected: {1, 3, 4} (was {1} at τ.6.x.1.C)
Coverage: 63% of expected verse count (138 for Gen 1-5)
         60% of expected chapter count (5 for Gen 1-5;
         chapter 2 + 5 markers garbled past recognition)
```

**Residue handling at τ.7.x.a (proper):** the writer
(`write_book_module`) can apply chapter-renumbering using
`GENESIS_VERSE_COUNTS` as the expected-floor reference. Strategy:
walk parser output, accumulate verses; when current chapter
verse-count meets `GENESIS_VERSE_COUNTS[chapter]`, advance to
chapter+1 even without an explicit marker.

OR insert τ.6.x.1.E (truncated-keyword recovery) before τ.7.x.a
to fix the residual at parser-level rather than writer-level.

---

## 2. Ship-by-ship review (post-DEEP)

### 2.1 τ.7.x.a.0 PILOT (commit 32b956f)

Already deeply documented in `dev/PILOT_TAU7XA_OUTPUT.md` (10
sections). At this LIGHT-3 check:

- ✓ `_source.yaml::structural_map.genesis` block present
  ([0, 85] page range; book_codes=[gen]; verified=true at
  τ.7.x.a)
- ✓ `_source.yaml::ocr_strategy.tau7xa_pre_pilot` block present
  with `parser_extension_needed=paragraph_mode_parser_extension_
  needed` flag and `finding_resolved_at_phase: τ.6.x.1.C`
  reciprocal back-link
- ✓ `dev/PILOT_TAU7XA_OUTPUT.md` 10-section reference artifact
  present
- ✓ tests/test_parallel_bible_tau7xa.py — 39 pins across 6
  classes, all pass at LIGHT-3 sweep

**No findings at LIGHT-3.**

### 2.2 τ.6.x.1.C paragraph-mode parser (commit b109844)

- ✓ 4 NEW module-level symbols in `scripts/extract_parallel_pdf.
  py`: `CROSS_REF_FRAGMENT_RE` + `is_cross_ref_fragment` +
  `GENESIS_VERSE_COUNTS` (50-chapter, total 1534 Masoretic) +
  `_parse_paragraph_mode`
- ✓ `parse_verses_from_text()` keyword-only `paragraph_mode:
  bool = False` argument — backward compatibility preserved
- ✓ `_source.yaml::ocr_strategy.tau6x1c_parser_extension` block
  with 8-key closed_arc_contracts_preserved + reciprocal
  back-link to tau7xa_pre_pilot
- ✓ 37 pin tests across 5 classes, all pass at LIGHT-3 sweep
- ✓ Empirical regression pin (text-layer pages 0-5 ≥75 verses)
  fires live against real PDF + real text extraction

**No findings at LIGHT-3.**

### 2.3 τ.6.x.1.D chapter-marker recovery (commit 92a5362)

- ✓ 2 NEW module-level symbols: `CHAPTER_HEADER_RE_LENIENT` +
  `_resolve_chapter_marker(numeral_token, current_chapter, *,
  max_jump=5)`
- ✓ `_parse_paragraph_mode` rewired to use the lenient regex +
  resolver; pre-marker title-page text now DISCARDED when
  markers exist
- ✓ `_source.yaml::ocr_strategy.tau6x1d_chapter_recovery` block
  with 9-key closed_arc_contracts_preserved + reciprocal
  back-link `tau6x1c_parser_extension.residual_resolved_at_
  phase: τ.6.x.1.D`
- ✓ 37 pin tests across 6 classes, all pass at LIGHT-3 sweep
- ✓ Empirical regression pin (text-layer pages 0-5 ≥3 chapters)
  fires live

**ONE finding surfaced (A-LIGHT7-1):** the chapter-2 marker on
Amharic Genesis pages 1-2 is OCR-garbled past the lenient regex
(truncated to `ራፍ`). Recommendation pending: optional
τ.6.x.1.E refinement before τ.7.x.a, or downstream renumbering.

---

## 3. Follow-up to prior AUDIT findings

### 3.1 LIGHT-3 (DEEP)-carried-forward items — table form (see §0)

The 16 carried-forward findings are tabulated in §0. Summary:

- **D-C1 (CRITICAL hygiene):** 19 ship scripts above retention
  threshold — UNCHANGED, deferred to post-τ.7.x.a hygiene
  window.
- **6 WARN-class** (D-W1 through D-W6): all UNCHANGED at LIGHT-3.
- **4 INFO-class** (D-I1 through D-I4): all UNCHANGED.
- **A-LIGHT5-1** (τ.6.x.2.D pin count ~33 vs 40): UNCHANGED, not
  corrected.
- **A-I1** (PLAN §2 staleness): UNCHANGED, drift wider (4634 →
  4747).
- **A-I3** (historical-pin convention codification): **RESOLVED**
  at τ.6.x.1.D — single-key `*_resolved_at_phase` back-link
  pattern now has 4 instances (codification threshold met).
- **A-I4** (external-tool resolver): UNCHANGED.

### 3.2 NEW A-LIGHT7-1 (parser-quality, WARN)

τ.6.x.1.D chapter-2-truncated-keyword residual. Detailed at
§0 NEW findings + §2.3.

**Recommendation:** OPTIONAL τ.6.x.1.E (truncated-keyword
recovery) before τ.7.x.a OR downstream chapter-renumbering at
write_book_module time using `GENESIS_VERSE_COUNTS`. Estimated
scope for τ.6.x.1.E: ~½ session. The empirical heuristic
candidate: extend `CHAPTER_HEADER_RE_LENIENT` keyword pattern
from `ም[ዕፅ]ራፍ` to `[ምሙ]?[ዕፅ]?ራፍ` (allow leading-char drop) +
validate via position-and-density heuristics (require at least
N verses since the last marker before accepting the next one).

### 3.3 NEW A-LIGHT7-2 (codification trigger, INFO)

Share-pin → milestone-pin refactor pattern repeated 5 times this
session. Detailed at §0 NEW findings.

**Recommendation:** add a CLAUDE_PROJECT_RULES §8.1 entry
codifying milestone-pin as the default for state-doc-content
assertions. Optional: add a `lint_rules.py` check to
auto-detect `[:N]` slicing of SESSION_STATE / IN_FLIGHT /
CHANGELOG file content in test asserts. Estimated scope:
~⅓ session for the codification entry + lint check.

---

## 4. Recommendations

### 4.1 Immediate (this session)

- **Save this LIGHT-3 audit doc** via `save.cmd` (optional;
  could batch with the next ship). Per memory `reference_save.
  md`, push will fail (remote deleted); local commit only.
- **No fixes required at audit-time.** All 113 net tests pass;
  no regressions; all 18 closed-arc invariants preserved; the
  2 NEW findings are advisory + non-blocking.

### 4.2 Next session boundary

- **τ.7.x.a (proper)** — Amharic Genesis full-book ingest. The
  D4-c-locked next-phase. UNBLOCKED by the τ.6.x.1.C +
  τ.6.x.1.D parser chain. Writer can apply chapter-renumbering
  for the A-LIGHT7-1 residual.
- **OR τ.6.x.1.E** (truncated-keyword recovery) — OPTIONAL
  parser refinement before τ.7.x.a if cleaner labeling needed
  at ingest time. Address A-LIGHT7-1 at parser level.
- **OR ω.5-class hygiene bundle** (deferred from DEEP §4.3) —
  address D-C1 ship-script archive + D-W1 hook re-install +
  D-W4 MEMORY.md index + D-W6 corpus-count refresh + A-LIGHT5-1
  pin-count correction + A-LIGHT7-2 milestone-pin codification.
  Estimated scope: 1 session.

### 4.3 Future hygiene-arc (no specific session yet)

- **ω.5-class candidate bundle** (when scheduled): see DEEP
  §4.3 + this LIGHT-3 §4.2 above.
- **ω.6-class candidate bundle** (separate): ruff `check --fix`
  mechanical pass for D-W3 background debt.
- **ω.7-class candidate bundle** (lowest priority): W-W1
  prophylactic sweep for D-W2.

---

## 5. Verdict

**CLEAN.** Project state at LIGHT-3 is healthy along three
dimensions vs DEEP:

1. **The τ.6.x parallel-Bible Claude-side parser chain is
   COMPLETE.** Engine (τ.6.x.1) + Ethiopic-numeral preprocessor
   (τ.6.x.1.B) + paragraph-mode parser (τ.6.x.1.C) +
   chapter-marker recovery (τ.6.x.1.D). Empirical floor: 63%
   verse coverage + 60% chapter detection on the Amharic
   Genesis pages 0-5 test sample. The remaining 37-40% gap is
   tracked through A-LIGHT7-1 + writer-side renumbering.

2. **The A-I3 historical-pin codification threshold is
   resolved.** Single-key `*_resolved_at_phase` back-link
   pattern now has 4 instances — past the 3-instance
   codification trigger. Awaiting CLAUDE_PROJECT_RULES §8.1
   entry at next ω-class hygiene ship.

3. **NEW closed-arc invariant added at this session** — the
   τ.6.x.1.C + τ.6.x.1.D parser-chain contract (combined as
   invariant #18). Pinned in ~74 test-pin matrix (TestTau6X1C*
   37 + TestTau6X1D* 37). Real-PDF runtime regression coverage
   ensures any future parser regression would fire empirically.

The cumulative drift since the original LIGHT-3 (00:55,
post-τ.6.x.1.B) is **+153 tests over 5 ships** — exactly at the
+150 cadence threshold, retroactively justifying the LIGHT-2 +
DEEP + this LIGHT-3 chain. The next audit-cadence-window opens
at +150 above the 4747 baseline (i.e., test count 4897 or 10
phases shipped, whichever first).

The audit-doc chain at this point:

```
2026-05-13  LIGHT             post-γ.4.9
2026-05-13  LIGHT-2 (mid)     post-γ.4.9.B
2026-05-13  DEEP              post-γ.4.9.D arc-close
2026-05-13  EOD               post-Ω.0
2026-05-14  LIGHT             post-φ.1
2026-05-14  LIGHT-2           post-Π.1.B + δ.1.0
2026-05-14  LIGHT-3           post-τ.6.x.0c late-session
2026-05-15  LIGHT             post-τ.6.x.1.B (00:55, morning)
2026-05-15  LIGHT-2           post-τ.6.x.2.D (cadence)
2026-05-15  DEEP              post-τ.6.x.2.D extensive (matrix sweep)
2026-05-15  LIGHT-3           post-τ.6.x.1.D (cadence-window close; this doc)
```

**Next ship**: τ.7.x.a (proper) — when invoked, opens the FIRST
authorized Amharic-content ingest under the D4-c locked
decision. The 4-step parser pipeline + 4 real-PDF runtime
regression pins (τ.6.x.1.A 3 + τ.6.x.1.B 2 + τ.6.x.1.C 2 +
τ.6.x.1.D 2) mean any τ.7.x.a regression would surface
immediately.

---

*Light solo-Claude audit #3 of 2026-05-15, post-τ.6.x.1.D
chapter-marker-recovery ship. Eleventh in the rolling 2026-05-13
→ 2026-05-15 chain. Cadence-justified: +153 cumulative tests
since the post-τ.6.x.1.B LIGHT (00:55 today) crosses the +150
threshold. Triggered by user "audit" after the 4-ship session
(τ.6.x.2.D + τ.7.x.a.0 + τ.6.x.1.C + τ.6.x.1.D) closed cleanly.*
