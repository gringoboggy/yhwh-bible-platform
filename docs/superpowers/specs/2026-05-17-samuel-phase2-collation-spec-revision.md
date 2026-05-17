# Samuel Phase-2 collation tool — SPEC REVISION (Task-5 premise correction)

**Date:** 2026-05-17
**Status:** REVISION — supersedes the Phase-2 *plan's* Task-5 contract; amends
`docs/superpowers/specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md`
§5 (unit 3 contract clarification), §8 (success criteria clarification), and
the D3 base-pick rule. The 2026-05-16 design spec remains APPROVED; this
document records what calibration + the Phase-2 build empirically proved and
corrects an over-specification the *plan* introduced.
**Trigger:** Phase-2 execution (subagent-driven) reached Tasks 4-5; Task 4
shipped a sound engine; Task 5 (the plan's "regression oracle") was found —
and independently controller-verified — to be **mathematically impossible as
written**. User decision at the fork (2026-05-17): **pause & revise the spec.**

---

## 1. What happened (the verified finding)

The Phase-2 plan `docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool.md`
defined **Task 5** as: *"the engine is correct iff it reproduces all four
Phase-1 calibration collations (`1sa1`/`1sa3`/`1sa17`/`2sa11`
`*_collation.json`) — exact `*_basis` numerator/denominator for
strict/skeleton/both-confident/semantic + `base_witness_recommended` +
`lacuna_counts`."* It called the four hand collations a **"regression
oracle"** and instructed "implement to the oracle."

Tasks 1-4 shipped cleanly (engine core, metrics + hard token-conservation
gate, witness validator, narrative aligner + `collate()`), each passing a
two-stage spec + code-quality review. Task 4's engine is a single general,
token-conserving, narrative-anchored collator (global Needleman–Wunsch over
`fold_skeleton` with a substitution model; content-anchored spine slicing;
empirical base pick; real per-cell uncertainty flags wired into
both-confident).

**Task 5 cannot pass, and no engine can make it pass.** Proven from multiple
independent angles by the implementer and **independently re-verified by the
controller against the real shipped `fold_skeleton` and the real immutable
golden files**:

1. **`1sa1_collation_hires.json` is internally non-functional for any pure
   classifier.** Using the actual shipped `fold_skeleton`:
   - **2 rows are fold-IDENTICAL yet hand-classed `disagree`** —
     `ማህፀና`/`ማሕፀና` at v5 and v6 (both fold to the same skeleton).
   - **4 rows are fold-DIFFERENT yet hand-classed `agree`** —
     `ወዓጸው`/`ወዓፀወ` (v5), `ዓጸው`/`ዓፀወ` (v6), `ወተሐውስ`/`ወተኃውስ` (v13), …
   No pure function `f(gg, cam)` can map identical inputs to `disagree`
   while mapping different inputs to `agree`. A deterministic classifier is
   structurally incapable of reproducing `1sa1`.
2. **The four chapters demand mutually contradictory thresholds.** Sweeping
   strict / fold-edit-distance ≤1/≤2/≤3 / ratio thresholds against each
   golden's own `alignment[]` rows: no single string rule reproduces even
   one chapter's agree/disagree split, and the per-chapter optima conflict
   (`1sa3` wants ≈ d≤1; `1sa1` wants *fewer* agree than even strict
   fold-equality). `1sa3`/`1sa17`/`2sa11` carry 46 / 35 / 67
   fold-DIFFERENT-but-`agree` rows — systematic human "same word, scribal
   variant" readings (proclitic `ስ-`/`ለ-` swaps, `ለ`-prefix presence,
   name-forms `ለኢዮአብ`/`ለኢያብ`).
3. **The hand base-choice is philological, not metric.** The plan's literal
   base rule (fewer `⟦illegible⟧` → lower flagged ratio → CAM) yields **GG**
   for `1sa17` (GG 0 illegible, ratio 0.0236 < CAM 0.0962) and `2sa11`
   (GG ratio 0.0945 < CAM 0.1038). Both goldens — and the user's ratified
   GO — choose **CAM**, on *recension-completeness / narrative-continuity*
   grounds (`1sa17`: CAM is the LONG/FULL 58-verse form, GG the SHORT
   20-verse LXX-type — you do not publish the short recension as the base
   running text).
4. **The Tasks 1-3 classifier contract forbids the goldens' readings.** The
   immutable `TestFoldAndClassify` pins `classify_pair` to fold-equality;
   loosening it to chase the goldens would break shipped, reviewed tests
   (and still fail per (2)).

**Root cause:** the four `*_collation.json` `alignment[]` arrays are
**per-token human philological adjudication** (scribal-variant-vs-genuine-
variant; recension primacy), produced during a *measurement exercise*, not
by an algorithm. Reproducing them requires the answer key, not an engine.

## 2. Why the spec itself was never violated — the plan over-specified

Re-reading the 2026-05-16 design spec against the plan:

- **§5 unit 3** (verse-alignment + collation engine) fixes the engine's
  *contract* — align by canonical chapter:verse via skeleton; per verse →
  base / other / `{agree|disagree|lacuna}` / D3 resolution. The section's
  closing sentence is explicit: *"this spec fixes the **units and their
  contracts, not their internals**."* It never requires the engine to
  reproduce the calibration files' specific agree/disagree counts.
- **§8 success criteria** = *"the Phase-1 **metrics** extended book-wide in
  the QA report (per-chapter W↔W agreement / semantic-pass / uncertainty),
  held to the same GO bar"* + structural pins: `SAMUEL_VERSE_COUNTS` floor,
  manifest coverage, reconciled-module shape, apparatus well-formedness,
  the lacuna-honesty pin, `_meta`/`_source` pins. **None** of these requires
  byte-reproducing the hand-adjudicated calibration `alignment[]`.
- **The calibration finding** (`dev/CALIBRATION_2026-05-16-samuel-widened.md`
  §1) states it was *"a data/measurement exercise only — no production code
  was built"*; the metrics were read from hand collations adversarially
  recomputed from raw `alignment[]`. Those agreement %s were **measurements
  that already fulfilled their purpose**: they produced the user's
  **GO (2026-05-17)** — diplomatic-parallel CONFIRMED, base = CAM confirmed.

The plan author turned a *human measurement deliverable* into a *machine
regression oracle*. That is the single defect. The spec's actual Phase-2
contract is satisfiable and largely already satisfied by the shipped engine.

## 3. Revised contract (authoritative)

### 3.1 The four calibration collations are immutable HUMAN REFERENCE, not a regeneration target

`content/manuscript/samuel/calibration/*_collation.json` remain immutable
evidence. They are retained as the **human calibration reference** that
produced the GO. The Phase-2 engine is **not** required (or able) to
reproduce their human-adjudicated `alignment[]`/agreement basis counts.
They are never edited; they are never a pass/fail oracle for the engine's
classifier.

### 3.2 Phase-2 engine success = the REPRODUCIBLE invariants (spec §5/§8, made precise)

The engine is correct iff, on each of the four calibration chapters
(witness JSONs + the project KJV skeleton as input):

- **R1 — Evidence validity.** `validate_witness` accepts both immutable
  witness records (honesty bijection, geez↔tokens invariant, schema).
- **R2 — Token-conservation (HARD gate).** Every evidence token appears
  exactly once across the alignment (lacuna rows excepted) —
  `assert_token_conservation` must not raise. *(Engine already passes 4/4.)*
- **R3 — Semantic-pass exact.** `semantic_pass_basis` reproduces the
  calibration exactly: `1sa1` 28/28, `1sa3` 21/21, `1sa17` 58/58,
  `2sa11` 27/27. *(Engine already passes 4/4 — semantic is the spec's
  primary honest gate, §4/§8, and it is reproducible because it is a
  narrative-beat check, not a token adjudication.)*
- **R4 — Lacuna exact.** `lacuna_counts` reproduces the immutable
  `⟦illegible⟧` bijection exactly: GG 16/1/0/0, CAM 0/0/0/0 across
  `1sa1`/`1sa3`/`1sa17`/`2sa11`; `lacuna-*` rows excluded from agreement
  denominators. *(Engine already passes 4/4.)*
- **R5 — Base = CAM (4/4) under the refined rule (§3.3).**
- **R6 — One byte-stable `definitions` set.** `metrics.definitions ==
  manuscript_collation.DEFINITIONS` on all four (the single folding set,
  spec §8 / failure-mode 5).
- **R7 — The five failure modes handled structurally** (calibration §4):
  spine == canonical KJV enumeration, never positional `v==v`; a large
  one-sided recensional minus (the `1sa17` GG-short vs CAM-long split) is
  classed `disagree` and counted in the denominator, **never** `lacuna`;
  the `2sa11` GG vv.21-22 messenger doublet tokens are all preserved as
  one-sided `disagree` cells and conserved; lacuna only ever from
  `⟦illegible⟧`.
- **R8 — Honest-divergence transparency artifact.** The engine emits a
  recorded report of its **own** deterministic strict / skeleton /
  both-confident figures for the four chapters **alongside** the hand
  calibration figures, explicitly stating the engine's classifier is a
  reproducible measurement that *intentionally differs* from the
  per-token human adjudication (which already produced the GO). This is
  the project-idiomatic honest-divergence record (cf. the `ocr-tier3`
  honesty records; memory `feedback_reverify_conservative_nogo`,
  `feedback_extensive_answers`). Overclaiming engine==human is forbidden.

Strict/skeleton/both-confident agreement **percentages are NOT a pass/fail
oracle.** They are the engine's honest measurement, surfaced book-wide by
the QA tool (Unit E) and held to the spec §4 GO bar **as the engine's own
metric** — exactly what spec §8 says ("Phase-1 *metrics* extended
book-wide … held to the GO bar"), not "reproduce the hand `alignment[]`."

### 3.3 Refined base-pick rule (D3 made precise from what calibration proved)

Spec D3 said *"the calibration sample empirically picks the base witness."*
It did: **CAM, 4/4**, ratified by the GO. The *reasoning* the calibration
revealed (finding §2-§4) is now encoded as the deterministic rule, replacing
the plan's illegible-count-only heuristic:

> **Base = the witness transmitting the more complete recension** when the
> two witnesses' extents differ materially (materially-different verse /
> narrative-beat coverage — e.g. `1sa17`: CAM 58-verse LONG vs GG 20-verse
> SHORT → **CAM**). **Otherwise the physically cleaner witness** (fewer
> `⟦illegible⟧`, then lower self-flagged-uncertainty ratio). **Ties → CAM**
> — the GAPS source-map primary Samuel witness, ratified project-wide by
> the 2026-05-17 GO.

This yields **CAM in all four chapters** (R5) deterministically and matches
the human reasoning in the finding. `base_rationale` must record which
clause fired and cite the GO. Because base = CAM is a **confirmed
project-wide decision** (calibration Decision; finding §4), the engine's
`base_witness_recommended` is the rule's output **and** is asserted == "CAM"
for Samuel; any future chapter where the rule would not yield CAM is a
**surface-to-user** event, never a silent base flip.

### 3.4 Unchanged

Spec §1-§4, §6 (Phase-3 render + apparatus store +
`manuscript-collation-tier2`), §7 (honesty contract — both-witness lacuna →
marked gap, never fabricated), §9 (sources/attribution), §11 (non-goals)
are **unchanged**. D1=B (reconstructed text + per-verse two-witness
apparatus) and D3 (base + apparatus, disciplined eclectic fallback always
recorded) are **unchanged**. The diplomatic-parallel model and base=CAM
remain CONFIRMED (GO 2026-05-17). Kings still reuses Phase-2/3 verbatim.

## 4. Consequence for the plan

`docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool.md` is
**SUPERSEDED** by
`docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool-v2.md`:

- **Tasks 1-4 — DONE & shipped** (commits `2f8872f`, `4f30e33`+`c2e9615`,
  `9408ac5`+`15f0e33`, `97cc1e7`; the engine is sound and reviewed). The
  v1 Task-4 commit stands; the v1 Task-5 commit `983cf1c` only added a
  "BLOCKED" diagnosis to the module docstring — v2 Task 5 step 1 rewrites
  that docstring to the factual architectural note (no longer "BLOCKED";
  the user resolved the fork).
- **Task 5 — REDEFINED** to R1-R8 (§3.2): an invariant/property regression
  test over the four calibration chapters + the honest-divergence
  transparency artifact. No byte-reproduction of hand `alignment[]`.
- **Base-pick** — refined per §3.3 (small, bounded engine change inside
  `collate()`; re-verified by R5).
- **Tasks 6, 7, 9** (manifest / reconcile+apparatus / driver+ship) — carry
  over essentially unchanged (diplomatic-parallel, base=CAM confirmed).
- **Task 8** (QA/audit meta-tool, Unit E) — clarified: it holds the
  **engine's own** computed W↔W/semantic/uncertainty to the spec §4 GO bar
  book-wide and **reports the honest engine-vs-hand divergence** for the
  calibration chapters; it does not assert engine == hand.

No spec non-goal is changed; no scripture is fabricated; the four
calibration files stay immutable.

## 5. Sign-off

This revision is the deliberate path the user selected at the 2026-05-17
fork ("pause & revise the spec"). It is grounded in: the controller-verified
impossibility proof (§1), the 2026-05-16 design spec §5/§8 text (§2), and
the calibration finding + ratified GO (§2-§3). It preserves the shipped,
reviewed engine, removes the impossible over-specification, and keeps
Phase-2 honest and movable. **Resume only after the user reviews this
revision + the v2 plan** (the user paused execution; do not auto-execute).
