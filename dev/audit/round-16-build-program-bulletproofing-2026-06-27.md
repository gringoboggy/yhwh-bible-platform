# Round-16 deep-audit program — Build-Program Bulletproofing (full output cross-product)

> **STATUS: ✅ USER-APPROVED (2026-06-27, plan mode) + PREPARED for autonomous two-lane execution — NOT YET RUNNING.**
> Set up at the close of round-15 (fully closed, both lanes). The user directed: audit the program that builds the
> EPUBs so it is bulletproof across **every way we offer the same Bibles** — each OS program (Win/Mac/Linux), each
> canonical edition, each reader version (Apple Books / Google Play / Kindle / Kobo / everywhere) — no broken `<>`,
> no code leak, logical+non-redundant markers/popups/notes, no unwanted page-breaks/whitespace, all options present.
> Run it **with the Mac alongside** (two-lane). This round is **FINDINGS-ONLY** (the rounds 14/15 pattern: gather +
> adversarially-verify all findings → a phased fixes plan for the user to approve; fixes are the SUBSEQUENT phase).

## How the autonomous sessions run this (both lanes, matching the round-14/15 process)

1. **Bootstrap + pull** the triad (RULES → SESSION_STATE → roadmap) + `dev/IN_FLIGHT.md` (TRACKER-STATE = round-16 READY)
   + this program doc + `dev/LANE_HANDOFF.md`.
2. **The engine is already configured** in `.claude/workflows/deep-audit.js` (committed with `LANE='all'`): `ROUND=16`,
   `NOW='2026-06-27'`, the 8 new dim objects appended, `ROUND16_DIMS` (11 dims) defined, the `DIMENSIONS` selector
   extended with a `ROUND===16` branch, round-15 D1–D9 + the round-14 build-source dims folded into
   `DEFERRED_BY_DESIGN`, round-15 fixes in `PRIOR_SURVIVOR_TITLES`.
3. **Each box flips ONLY its local `LANE` line** (`win` here / `mac` on the iMac) — never commit it; restore with
   `git checkout -- .claude/workflows/deep-audit.js` after the run. **Confirm the startup log echoes `argsRound=16`**
   (the args-don't-propagate guard — `(default)` is fine since the in-file default IS 16; a `ROUND` other than 16
   means the bump didn't take → invalid run).
4. **Run the engine** (`Workflow({scriptPath:".../.claude/workflows/deep-audit.js"})`) on the full 11-dim
   `ROUND16_DIMS` set — **identical on both lanes** (the `LANE` knob only picks REPO path + agent types; do NOT
   partition the dims per box — that caused the round-5 15× Mac failure). Each finding is adversarially refuted
   before it counts; a finding that re-raises a `DEFERRED_BY_DESIGN` item is refuted.
5. **Side-work (the lane difference):**
   - **WIN** runs the full-catalog **build-inspect harness** (below) CONCURRENTLY with its engine (model-bound
     finders parallelize with compute-bound builds — the round-14 model). Never pytest beside a build.
   - **MAC** **cross-OS verifies** (rebuild the 9 KJV golden cells on macOS → G1 byte-identity 9/9; one
     catholic-study eink on macOS → the gates PASS) + runs the 2 build-free source gates' `_selftest`.
6. **Gather + merge:** record every survivor + harness gate-FAIL + cross-OS delta into `dev/audit/round16-remediation.md`
   (one tracker, both lanes, file-disjoint; `truth_owner=windows`). Save cadence: local-commit per slice, push both
   remotes (WIN also E:/F: bundles) at each coherent slice. **STOP at a complete, verified, merged findings set + the
   phased fixes plan.** Do NOT apply fixes (the user approves remediation separately).

## Round-15 + round-14 SETTLED — deferred-by-design (do NOT re-litigate; a verifier MUST refute a re-raise)

These are encoded in `deep-audit.js` `DEFERRED_BY_DESIGN`; listed here for the human reader:

- **Round-15 D1** release-asset integrity — `dev/audit_release_assets.py` + the live v0.1.0 re-cut to 87 assets. Done.
- **Round-15 D2** xref subsystem — G3 xref-class breakout + `--min-xrefs 10000` floor (ethiopian 88,541 / catholic 55,774, 0 dead). Done.
- **Round-15 D3** Douay/Vulgate Ps 2:12/4:8 restored (surgical re-bake + golden re-stamp; Latin tails ship). Done.
- **Round-15 D4** `_cascade = s2_group` (`build_edition.py:4228`); dict-easton provenance restored. Done.
- **Round-15 D5** flagship glossary byte-streamer proven 690/690 @255 MB + G5 PASS + permanent regression. Done.
  *(The residual ~3×-copy glossary RAM surface IS in scope for the round-16 `builder-robustness` dim — that is a NEW
  resource finding, not a re-raise of D5's correctness proof.)*
- **Round-15 D6/D7/D8/D9** — canon book-count gate · migration torn-safe+idempotence gate · `audit_canonical_order`
  reading-flow gate (no defect) · kepub bare `-sN` rev-id = by-design. Done. (Round-16 `cross-module` REUSES
  `audit_canonical_order`; it does not re-derive D8.)
- **Round-14 build-source settlements** (file-split idmap-miss fallback · eink-gating isolation · WS2 cascade de-dup ·
  glossary streaming · the page-break re-arch · WS3 popup separators) + **est 10:2** (`_mv_displacement_would_corrupt`)
  + the A1 LF chokepoint + the 5 round-14 gates G1–G5 — SETTLED. Round-16 audits them for **regression/bleed only**.
- **Marathon core OFF-LIMITS** (read-only): `scripts/build_standalone.py`, `scripts/core/manuscript_*.py`,
  `scripts/core/po_vision_store.py`, `content/manuscript/**`, `content/translations/sources/patrologia/**`, `GAPS/`.
  (A read-only standalone *build* is fine — the marathon-core *code* is not edited.)

## Invariants every round-16 finding / eventual fix carries

- **9-KJV byte-stable** — any build-path fix is additive / eink- or customize-gated + carries a byte-identity proof
  (regen the 9 cells + `git diff`, or re-run **G1**). A new EPUB-build import must be added to `_PIPELINE_SCRIPTS`
  (the `TestCacheCoverageGuard` AST guard enforces it).
- **Additive schema only** · writes through `notes_io.atomic_write` / `ensure_backup` · **no paid API**.
- **A real defect spotted while scoping is in-scope** (don't self-narrow); a build-side fix to a data/format
  corruption class must mirror its detector (the round-14 #6 → `audit_verse_formatting.py` precedent).
- **FINDINGS-ONLY this round** — produce the verified findings + the phased plan; STOP before applying any fix.

## The 11 dimensions (D-keys = the `deep-audit.js` dim keys; all run on BOTH lanes)

> Source-reasoning finder lenses ("does the build CODE produce correct X for reader Y?"). Each PAIRS with an
> artifact/source gate the harness or a build-free test runs. The full scoped prompts live in `deep-audit.js`.

| # | dim key | what it hunts | ask | sev-bias | paired gate |
|---|---------|---------------|-----|----------|-------------|
| 1 | `correctness` | LOGIC defects in `build_one`'s 14 stages + the `web.py` build trigger (wrong output / dropped data / off-by-one / abort-to-noop shipping a WRONG artifact) | #1 #5 | high | — |
| 2 | `security` | XSS / HTML-injection / code-leak boundary (`sanitize_html`/`is_trusted_html`/`escape_attr`); merged-aside interpolation | #2 #5 | high/crit | shares hygiene |
| 3 | `builder-robustness` | RESOURCE/PROCESS failure ONLY: residual glossary 3×-copy OOM, torn `epub_working/` write, `subprocess.run` missing `stdin=DEVNULL`, frozen-vs-dev divergence, memory-pressure | #5 | high | lint |
| 4 | `cross-product` | **HEADLINE** — grid parity: matrix×editions×`TARGET_READERS` complete + declared==built (kindle row) + `/customize` reader opts ⊆ resolver (the `computer` orphan) + standalone-raises-on-target + cover-swap logic-neutral + phase-gating coherent + no orphan/dup cell | #3 #8 | high | `audit_cross_product` |
| 5 | `marker-logic-xreader` | vn-link/vnote + badge/numbers markers consistent + complete PER READER: no orphan marker, no badge→nowhere, no note-without-marker, no teleport; covers `numbers` editions (G4 gap) + all readers | #4 | high | hygiene + extend G4 |
| 6 | `html-integrity` | **HEADLINE** — balanced/escaped tags + NO template/code leak (`{{}}`/`{%%}`/repr/f-string artifacts/`[Reviewer:]`/raw `<` `>`) in emitted output; post-pass nested-`<a>` (G1 base-only blindspot) | #2 | critical | hygiene + `check_nested_anchors` + epubcheck |
| 7 | `whitespace-pagebreak` | unwanted page-break/spine-break/empty-space/stray-`<br>`/empty-verse/empty-aside/orphan-opener, per reader | #6 | medium | hygiene + `audit_spine_breaks` |
| 8 | `display-redundancy` | dup note/badge/category-header/byline/witness + redundant boilerplate/markup (both directions: missed-dedup AND dropped-distinct-note) | #7 | medium | hygiene |
| 9 | `options-completeness` | full §7 wiring per `/customize` field (field→loader→validator→control→build-read→test) + every enum reachable + orphan/dead/illogical/meaningless option | #8 | high | `audit_customize_completeness` |
| 10 | `os-binary-parity` | Win/Mac/Linux `launcher.spec`/`paths.py`/`sys.frozen`/`content_root`/`VERSION` parity + webview fallback + signing no-secret-leak + installer/dmg/AppImage chains (static) | #3 | medium | static (reuse dist-packaging + `build-linux.yml`) |
| 11 | `cross-module` | book-code canon, enabled-kinds 3-way unify, canonical order, one-resolver / matrix==build | #1 #3 | high | reuse `audit_canonical_order` (G6) |

## ★ Concrete seeds the scoping pass ALREADY found (start here; each needs a verified finding + a gate)

Surfaced read-only while scoping (NOT fixed — for the approved round-16 run):
1. **The `computer` orphan option** — `computer` is a valid `TARGET_READERS` value (`build_edition.py:1977`) AND a
   `/customize` reader option (`customize.py`), but has **no `FORMAT_MATRIX` row** (the 5 rows are
   everywhere/apple/kobo/kindle/play) → a silent alias of `everywhere` with no catalog asset + no test.
   (Ask #8 "all options logical and present" + ask #3.) → `cross-product` + `options-completeness`.
2. **kindle declared ≠ built** — the `FORMAT_MATRIX` `kindle` row declares `target_reader:"kindle"`, but the shipped
   recipe is the `everywhere` base + `kindle_post.make_kindle_safe` (the `--target-reader kindle` variant was
   retired). `cross-product` must assert declared==built or this stays invisible.
3. **Standalone target degeneracy** — `apply_target_override` (`build_edition.py:~2005`) **raises** on any standalone
   given `--target-reader`, so geez/amharic have exactly ONE build shape each; nothing must iterate a 4-reader
   cross-product over them. `cross-product` asserts the build passes NO target to standalones.
4. **The headline NEW gap (no gate today): code/template leak + built-artifact HTML well-formedness.** The
   `[Reviewer:]` scaffold lint runs commit-time only; there is no guard against `{{}}`/`{%%}`/repr/f-string artifacts
   or raw `<`/`>` reaching shipped HTML, and G1 nested-anchor checks the BASE only. → `html-integrity` + the new
   `audit_output_hygiene.py`. This is round-16's headline deliverable the way G1 was round-14's.

## The WIN build-inspect harness (full catalog — user choice 2026-06-27) — runs concurrently with the WIN engine

Build + inspect the **entire catalog SKU set** via the real CI path `scripts/build_format_matrix.py` (base build per
distinct target → cheap COPY + `swap_epub_cover.py` colour fan-out). RAM accounting: **12 base builds** (4 editions ×
{everywhere, tablet, eink}) + **4 kindle post-processes** (`kindle_post.make_kindle_safe` over each everywhere base) +
**2 standalone builds** + the **colour fan-out** (cheap copy+swap → ~80–102 assets). One cover-swap **spot-check** =
a non-signature colour byte-differs only in cover assets (covers the COVER_COLOURS logic-neutral claim once).

**Staging ladder (strict — one build at a time; never build‖build, never build‖pytest; engine finders MAY run
alongside, they're bandwidth not RAM):** lightest→heaviest — all everywhere/tablet/kindle-post cells first, then the
3 **filtered**-edition eink (catholic-study 73 / evangelical-reformed 66 / eastern-orthodox 78), then
**`ethiopian-tewahedo` eink LAST and SOLO** (the RAM ceiling: 87-book superset + the 255 MB glossary monolith; check
`CommitFree` first, reboot if the AppXSvc commit-leak RSS creep recurs — memory `reference-hardware-box-and-mac`),
then the 2 standalones. Per cell: **build → scan → free** (delete the working tree before the next build; never let
trees co-reside).

**Scan each built asset** with `scripts/epubcheck.py --require --strict` + `check_nested_anchors` +
`dev/verify_kr2_build.py` (kobo) + the existing G3/G4(extended)/G5/G6 + the ONE merged **`dev/audit_output_hygiene.py`**
pass (opens each EPUB once → 4 finding-families: html-integrity / whitespace / display-redundancy / marker-logic;
reuses `audit_spine_breaks` + `audit_badge_conservation` G4 + `audit_idmap_frags` G3). Scan EVERY colour asset
(catches swap defects). FAILs → `round16-remediation.md` tagged with artifact id + (edition, format, reader).

## Lane division — both lanes run all 11 dims; only the SIDE-WORK is partitioned (truth_owner = windows)

| Lane | Engine | Side-work |
|------|--------|-----------|
| **WIN** | all 11 `ROUND16_DIMS` (LANE='win': feature-dev:* agents) | the full-catalog build-inspect harness + `audit_output_hygiene` + the existing gates on the built artifacts; owns `build_edition.py` (the eventual fix-surface) |
| **MAC** | all 11 `ROUND16_DIMS` (LANE='mac': general-purpose/Plan agents) | cross-OS verify (9 KJV golden cells → G1 9/9 byte-identical; one catholic-study eink → gates PASS) + the 2 build-free source gates' `_selftest`/clean-tree on macOS |

File-disjoint, PARALLEL. Re-confirm tool/agent parity (Guard #4) before either lane runs a shared workflow (the Mac
lacks `feature-dev:*` — the engine already maps to general-purpose/Plan; confirm kepubify/epubcheck/Temurin-21 on the
iMac before it builds). Any defect one lane finds that the OTHER must fix → `dev/LANE_HANDOFF.md` + a findings file
(Guard #6 hand-off).

## Deliverables (gates authored during the run; permanent — the round-14/15 pattern)

- **2 build-free source gates** → new `tests/test_round16_source_gates.py` (mirror `test_round15_source_gates.py`;
  each ships a non-tautological `_selftest()`, runs every push, no EPUB): **`dev/audit_cross_product.py`** (dim 4 —
  the round-16 headline) · **`dev/audit_customize_completeness.py`** (dim 9 — §7 five-point wiring + enum reachability
  + orphan option).
- **1 merged artifact scanner** → **`dev/audit_output_hygiene.py`** (dims 5/6/7/8 in one parse), wired into a new
  `tests/test_round16_build_gates.py` (mirror `test_round14_build_gates.py`; `@slow`, builds catholic-study eink).
  The html-integrity/code-leak detector is the genuinely NEW one (extends the commit-time
  `check_no_reviewer_scaffolding` lint to BUILT output + `{{}}`/`{%%}` forms). REUSES `audit_spine_breaks` (page/spine)
  + `audit_badge_conservation` G4 (markers — **extended from badge-only to `numbers` + per-reader**) +
  `audit_idmap_frags` G3 (marker→target resolution).
- **1 lint** (dim 3): `lint_rules` checks — every `subprocess.run` carries `stdin=DEVNULL`; every `epub_working/`
  mutation routes through `notes_io.atomic_write`.
- **0 binary scanner** (dim 10): static spec/source analysis only; the 3-way binary truth is `build-linux.yml` CI +
  local Win/Mac.
- The live tracker `dev/audit/round16-remediation.md` (per-finding status, like round-14/15's).

## Done-definition ("the audit is fully run + all info gathered") — all six hold

1. **Engine, both lanes.** Find→Verify→Synthesize completed on WIN and MAC over all 11 `ROUND16_DIMS`; the startup log
   showed `ROUND=16`. No dim returned a structurally-empty finder pool that should have run.
2. **WIN harness.** All 12 base builds + 4 kindle post-processes + 2 standalones + the colour fan-out built
   (flagship-eink solo, OOM-clear); each green on epubcheck + `audit_output_hygiene` + G3/G4(extended)/G5/G6 + the 2
   build-free gates; every FAIL injected into the pool tagged with artifact id + (edition, format, reader).
3. **MAC cross-OS verify.** 9 KJV golden cells rebuilt on macOS → G1 byte-identity 9/9; one catholic-study eink on
   macOS → G3/G4/G5/G6 + `audit_output_hygiene` PASS; the 2 build-free gates' `_selftest` + clean-tree pass on macOS.
4. **Adversarial verify.** Every survivor (engine + harness) passed the default-refuted skeptic panel (crit 3 / high 2
   / else 1); any re-raise of a `DEFERRED_BY_DESIGN` item refuted; **UNVERIFIED** survivors (empty panel after retry)
   listed separately for human triage, never auto-confirmed.
5. **Completeness-critic + ask-coverage matrix.** The synth completeness-critic ran AND produced an explicit
   **8-asks × 11-dims coverage matrix**: every user ask has ≥1 dim that *actually searched* it; an ask with zero
   findings AND zero "confirmed-clean" corroboration is a coverage GAP (next-round seed), not a pass.
6. **Merge → one tracker.** Engine survivors (both lanes, `survivors[]` JSON) + harness gate-FAILs (`--json`) +
   xos-verify deltas dedup by the engine's `keyOf` (`file::title`) into `dev/audit/round16-remediation.md` (mirroring
   round14/15), each tagged `source ∈ {engine-win, engine-mac, harness, xos-verify}`, severity-calibrated, phased
   safest-first, with the verbatim `COUNT_LINE` (authoritative counts — no recompute). Merge modeled on
   `archive/deep-audit-continue.js`; final synth on WIN.

**Then STOP.** Remediation (FIX every finding TDD + byte-proof + loop-to-green) is the SUBSEQUENT phase the user
approves after reviewing the gathered findings — the rounds 14/15 pattern.
