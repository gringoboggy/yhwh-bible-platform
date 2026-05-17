# Samuel Phase-2 collation tool — SPEC REVISION (Task-5 premise correction)

**Date:** 2026-05-17 (rev. 3 — R6 engine-side correction)

**Rev. 3 (2026-05-17):** during Task-5 execution the implementer hit an
honest BLOCKED — `test_R6` (controller-written in rev.2) asserted the
*immutable hand golden's* `definitions == DEFINITIONS`, which fails for
`1sa3` (its golden `skeleton` carries a chapter-specific philological
annotation; the other 3 match). This was the **same class of defect as
the rev.1 base-pick fudge** — the controller again over-asserting the
human reference == the engine, contradicting this revision's own R8
thesis. Caught because the implementer refused to tune/edit-goldens and
reported BLOCKED. **Fix (rev. 3):** R6 is corrected to **engine-side
only** (below); the hand goldens may legitimately differ per R8. No
code/data/golden change; spec + plan test corrected.
**Status:** REVISION — supersedes the Phase-2 *plan's* Task-5 contract; amends
`docs/superpowers/specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md`
§5 (unit 3 contract clarification), §8 (success-criteria clarification — the
structural pins are RETAINED, see §3.4), and the D3 base-pick rule. The
2026-05-16 design spec remains APPROVED.
**Trigger:** Phase-2 (subagent-driven) reached Tasks 4-5; Task 4 shipped a
sound engine; Task 5 (the plan's "regression oracle") was found — and
controller-verified, then re-verified by two independent adversarial
reviewers — **mathematically impossible as written**. User decision at the
fork (2026-05-17): **pause & revise the spec.**
**Rev. 2 changes (from adversarial review, 2026-05-17):** the base-pick
rule (§3.3) is corrected from a fitted-threshold "derivation" (a
reverse-engineered fudge the review flagged) to an **honest two-clause
rule + a decision-of-record assertion**; the design-spec §8 **structural
pins are explicitly RETAINED** (§3.4), not dropped; R8 is **demoted** from
a committed artifact + meta-tool script to a docstring note + a QA-tool
line (no ceremony).

---

## 1. What happened (the verified finding)

The Phase-2 plan v1 defined **Task 5** as: *"the engine is correct iff it
reproduces all four Phase-1 calibration collations
(`1sa1`/`1sa3`/`1sa17`/`2sa11` `*_collation.json`) — exact `*_basis`
numerator/denominator for strict/skeleton/both-confident/semantic +
`base_witness_recommended` + `lacuna_counts`."* It called the four hand
collations a **"regression oracle"** and instructed "implement to the
oracle."

Tasks 1-4 shipped cleanly (engine core; metrics + hard token-conservation
gate; witness validator; narrative aligner + `collate()`), each passing a
two-stage spec + code-quality review.

**Task 5 cannot pass, and no engine can make it pass.** Independently
reproduced three times (the implementer, the controller, and two adversarial
reviewers) against the **real shipped `fold_skeleton`** and the **real
immutable goldens**:

1. **`1sa1_collation_hires.json` is internally non-functional for any pure
   classifier.** Using the actual shipped `fold_skeleton`:
   - **2 rows fold-IDENTICAL yet hand-classed `disagree`** —
     `ማህፀና`/`ማሕፀና` (v5, v6), both fold to `መሀፀነ`.
   - **4 rows fold-DIFFERENT yet hand-classed `agree`** —
     `ወዓጸው`/`ወዓፀወ`, `ዓጸው`/`ዓፀወ`, `ወተሐውስ`/`ወተኃውስ`,
     `ወተሰጥወት`/`ወተሠጥወቶ`.
   No pure function `f(gg, cam)` can map identical inputs to `disagree`
   while mapping different inputs to `agree`. A deterministic classifier is
   structurally incapable of reproducing `1sa1`.
2. **The four chapters demand mutually contradictory thresholds.** No single
   fold-edit-distance / ratio threshold reproduces *any* chapter exactly
   (best per-chapter 98.3 / 92.1 / 88.6 / 92.7%, never 100%; global optimum
   90.2% at d≤1, and the per-chapter optima conflict). `1sa3`/`1sa17`/`2sa11`
   carry 46 / 35 / 67 fold-DIFFERENT-but-`agree` rows — systematic human
   "same word, scribal variant" readings.
3. **The hand base-choice is philological, not metric** (see §3.3).
4. **The Tasks 1-3 classifier contract forbids the goldens' readings**
   (`TestFoldAndClassify` pins `classify_pair` to fold-equality; loosening
   it breaks shipped, reviewed tests *and* still fails per (2)).

**Root cause:** the four `*_collation.json` `alignment[]` arrays are
**per-token human philological adjudication**, produced during a
*measurement exercise*, not by an algorithm. Reproducing them requires the
answer key, not an engine.

## 2. Why the spec itself was never violated — the plan over-specified

- **Design-spec §5 unit 3** fixes the engine's *contract* (align by
  canonical chapter:verse; per verse → base / other /
  `{agree|disagree|lacuna}` / D3 resolution). §5's closing sentence,
  verbatim: *"this spec fixes the **units and their contracts, not their
  internals**."* It never requires reproducing the calibration files'
  agree/disagree counts. The v1 plan *invented* the regression oracle
  ("the four golden files ARE the spec"); the spec never said that.
- **Design-spec §8** = *"success criteria = the Phase-1 **metrics**
  extended book-wide in the QA report (per-chapter W↔W agreement /
  semantic-pass / uncertainty), held to the same GO bar"* + structural
  pins. The Phase-1 *metric* was the **hand** measurement that already
  produced the **GO (2026-05-17)**; an engine's own deterministic
  agreement number is a *new, different* number, surfaced and recorded
  honestly (§3.2 R8) — not a re-litigation of a gate the user already
  cleared, and not a reproduction of the hand `alignment[]`.

The plan author turned a *human measurement deliverable* into a *machine
regression oracle*. That single defect is what this revision corrects.

## 3. Revised contract (authoritative)

### 3.1 The four calibration collations are immutable HUMAN REFERENCE, not a regeneration target

`content/manuscript/samuel/calibration/*_collation.json` remain immutable
evidence and the human calibration reference that produced the GO. The
Phase-2 engine is **not** required (or able) to reproduce their
human-adjudicated `alignment[]`/agreement basis counts. Never edited; never
a pass/fail oracle for the engine's classifier.

### 3.2 Phase-2 engine success = the REPRODUCIBLE invariants

Simple honest framing: *the engine is a deterministic forward collator; the
4 calibration files are human reference; its correctness on those 4 chapters
is the conservation/semantic/lacuna/base/structure invariants below;
agreement % is the engine's own honest measurement, never claimed equal to
the hand counts.* Made testable as R1-R7 (+ R8 honesty + R9 retained pins):

- **R1 — Evidence validity.** `validate_witness` accepts both immutable
  witness records (bijection, geez↔tokens invariant, schema).
- **R2 — Token-conservation (HARD gate).** Every evidence token appears
  exactly once across the alignment (lacuna rows excepted) —
  `assert_token_conservation` must not raise. *(Engine passes 4/4.)*
- **R3 — Semantic-pass exact.** `semantic_pass_basis` reproduces the
  calibration exactly: `1sa1` 28/28, `1sa3` 21/21, `1sa17` 58/58,
  `2sa11` 27/27. *(Engine passes 4/4 — semantic is a narrative-beat
  check, not a token adjudication, hence reproducible; it is the spec's
  primary honest gate, §4/§8.)*
- **R4 — Lacuna exact.** `lacuna_counts` reproduces the immutable
  `⟦illegible⟧` bijection exactly: GG 16/1/0/0, CAM 0/0/0/0; `lacuna-*`
  excluded from agreement denominators. *(Engine passes 4/4.)*
- **R5 — Base = CAM (4/4) under the honest rule (§3.3).**
- **R6 — One byte-stable `definitions` set (ENGINE-side).** The
  *engine's* output `metrics.definitions == manuscript_collation.
  DEFINITIONS` on all four chapters (the engine emits the single folding
  contract identically every chapter). The **immutable hand goldens MAY
  carry chapter-specific philological annotations** the generic engine
  constant does not — `1sa3_collation.json`'s golden `skeleton`
  definition is annotated with that recension's documented ስ↔ለ
  s/l-swap + ሾሉ/ኵሉ fold tolerance; `1sa1`/`1sa17`/`2sa11` match — and
  are therefore **NOT** asserted equal to `DEFINITIONS` (asserting the
  human reference == the engine constant would contradict R8's "the
  hand reference intentionally differs from the engine's own
  measurement" thesis; this was a rev.2 plan-test over-assertion,
  controller-introduced, caught by the Task-5 implementer's honest
  BLOCKED, corrected in rev.3).
- **R7 — The five failure modes handled structurally** (calibration §4):
  spine == canonical KJV enumeration, never positional `v==v`; the `1sa17`
  GG-short vs CAM-long recensional minus is classed `disagree` and counted
  in the denominator, **never** `lacuna`; the `2sa11` GG vv.21-22 messenger
  doublet tokens are all preserved as one-sided `disagree` cells and
  conserved; lacuna only ever from `⟦illegible⟧`.
- **R8 — Honest-divergence recorded (NO artifact ceremony).** The honest
  fact — that the engine's strict/skeleton/both-confident are a
  reproducible deterministic measurement that *intentionally differs* from
  the per-token human adjudication (which already produced the GO) — is
  recorded in exactly two low-cost places: **(a)** the engine module
  docstring (a factual architectural note), and **(b)** the QA meta-tool
  (Unit E, Task 8) emits an informational `engine_vs_hand_divergence`
  check carrying both the engine's and the hand's per-chapter
  strict/skeleton/both-confident plus the explicit "intentionally differs;
  not a claim of equality; the GO was produced by the hand calibration"
  statement. **No committed markdown artifact, no separate report
  meta-tool script.** Overclaiming engine == hand is forbidden.
- **R9 — Design-spec §8 structural pins RETAINED (not dropped).** The
  following remain REQUIRED acceptance criteria, verified by their owning
  tasks (not assumed): `SAMUEL_VERSE_COUNTS` floor totals + the
  reconciled-module renumber shape (Phase-3 / Task 9 ship-gate scope —
  pinned there, named here so they are not lost); **apparatus
  well-formedness** (every verse with a recorded disagreement/lacuna has a
  structured apparatus entry — Task 7); the **lacuna-honesty pin** (no
  fabricated text where both witnesses fail — Task 7, spec §7);
  `_meta`/`_source` ingest-record + back-link pins and
  `lint_rules.py 11·0·0` + `ruff format` clean (Task 9 ship gate). R9 makes
  explicit that R1-R8 narrowing the *calibration* contract does NOT relax
  spec §8's structural discipline.

Strict/skeleton/both-confident agreement **percentages are NOT a pass/fail
oracle.** They are the engine's honest measurement, surfaced book-wide by
the QA tool (Unit E) and reported against the spec §4 reference bar **as the
engine's own metric** (sub-bar W↔W is `warn`/informational and EXPECTED for
distinct recensions — that is precisely why diplomatic-parallel was chosen
and the user already gave GO; it is not a build failure). This is design-
spec §8 read correctly, not a redefinition of failure as success.

### 3.3 Honest base-pick rule (D3 — corrected after review)

Design-spec D3 said *"the calibration sample empirically picks the base
witness."* It did: **CAM, 4/4** — and the user **ratified base = CAM
project-wide** (`dev/CALIBRATION_2026-05-16-samuel-widened.md` §4
"Decision (user)"). Base = CAM is therefore a **decision of record**, not a
number to be re-derived.

The v1 plan's illegible-count→flagged-ratio→CAM heuristic, and rev. 1's
attempt to "fix" it with a fitted material-separation threshold, were
**reverse-engineered to force "CAM 4/4"** (rev. 1's `_pick_base` literally
yielded GG for `2sa11`; only a tuned `>0.05` constant whose sole function
was to bury `2sa11`'s 0.0093 gap salvaged it — exactly the motivated-
reasoning failure mode this project's culture forbids). **That false
precision is removed.** The honest rule is two clauses + an assertion:

> 1. **Materially-different extent → the more complete recension.** If the
>    shorter witness covers `< 0.70 ×` the longer witness's verse-objects,
>    base = the witness transmitting the more complete recension. *(`1sa17`:
>    GG 20-verse SHORT vs CAM 58-verse LONG → **CAM**. Principled: the short
>    recension is not published as the base running text. This is grounded
>    in the calibration finding itself, not fitted.)*
> 2. **Otherwise → base = CAM, asserted as the decision of record.** Not a
>    metric derivation: cite
>    `dev/CALIBRATION_2026-05-16-samuel-widened.md` §4 "Decision (user)"
>    (base = CAM, ratified project-wide by the 2026-05-17 GO). No illegible
>    count, no flagged-ratio, no tuned constant.
> 3. **Surface-to-user safeguard.** If clause 1 ever selects a non-CAM base
>    for any future chapter, that is a **surface-to-user event** (recorded
>    and flagged for the user), never a silent base flip and never resolved
>    by a fitted tiebreak.

`base_rationale` records which clause fired and cites the GO. Verified
against the real witness verse-counts (GG/CAM): `1sa1` 28/28 → cl.2 CAM;
`1sa3` 21/21 → cl.2 CAM; `1sa17` 20/58 → cl.1 CAM (more complete);
`2sa11` 27/26 → cl.2 CAM. **CAM 4/4 with the literal code, no tuning.**

### 3.4 Unchanged

Design-spec §1-§4, §6 (Phase-3 render + apparatus store +
`manuscript-collation-tier2`), §7 (honesty contract — both-witness lacuna →
marked gap, never fabricated), §8 **structural pins (retained verbatim — see
R9)**, §9 (sources/attribution), §11 (non-goals). D1=B and D3 (base +
apparatus, disciplined eclectic fallback always recorded) unchanged. The
diplomatic-parallel model and base = CAM remain CONFIRMED (GO 2026-05-17).
Kings still reuses Phase-2/3 verbatim.

## 4. Consequence for the plan

`docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool.md` is
**SUPERSEDED** by
`docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool-v2.md`:

- **Tasks 1-4 — DONE & shipped** (commits `2f8872f`,
  `4f30e33`+`c2e9615`, `9408ac5`+`15f0e33`, `97cc1e7`). v1 commit `983cf1c`
  only added a "BLOCKED" docstring note → v2 Task 5 Step 1 rewrites that
  docstring to the factual architectural note.
- **Task 5 — REDEFINED** to R1-R9: an invariant/property regression test
  over the four calibration chapters. **No** byte-reproduction of hand
  `alignment[]`. **No** `manuscript_calibration_report.py` script and **no**
  committed `dev/CALIBRATION_2026-05-17-engine-vs-hand.md` (R8 demoted —
  the honest-divergence record lives in the engine docstring + the Task-8
  QA `engine_vs_hand_divergence` line).
- **Base-pick** — corrected per §3.3 (a clean two-clause + decision-of-
  record `_pick_base`; literally yields CAM 4/4; no fitted constant).
- **Tasks 6, 7, 9** carry over; Task 7 explicitly verifies the R9
  apparatus-well-formedness + lacuna-honesty pins; Task 9 the R9 floor /
  reconciled-shape / `_meta`/`_source` / lint pins.
- **Task 8** holds the **engine's own** W↔W/semantic/uncertainty to the
  spec §4 reference bar book-wide and emits the `engine_vs_hand_divergence`
  informational check (R8); it does not assert engine == hand.

No spec non-goal is changed; no scripture is fabricated; the four
calibration files stay immutable.

## 5. Sign-off

This revision is the deliberate path the user selected at the 2026-05-17
fork. It is grounded in: the thrice-verified impossibility proof (§1), the
2026-05-16 design-spec §5/§8 text (§2), the calibration finding + ratified
GO (§2-§3), and two independent adversarial reviews whose convergent
findings produced rev. 2 (the honest base rule, retained §8 pins, demoted
R8). It preserves the shipped engine, removes the impossible
over-specification **and the fitted-threshold fudge**, and keeps Phase-2
honest and movable. **Resume only after the user reviews this revision +
the v2 plan** (the user paused execution; do not auto-execute).
