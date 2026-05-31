# mint-8 — Deep audit (the convergence audit) + a reusable audit tool
**Status:** ROUND 1 EXECUTED 2026-05-31 — `deep-audit.js` built + run (106 agents, ~4.80M tokens; 70 findings → 57 verified). Findings → `../notes/2026-05-31-mint-8-findings.md`; fixes plan → `2026-05-31-mint-8-fixes-plan.md`. **NEXT SESSION: implement the fixes, then RE-AUDIT (convergence loop).** (Original intent below.) **NEXT SESSION: build the
reusable `deep-audit.js` workflow from this plan, RUN it, verify findings, implement fixes,
then RE-AUDIT.** mint-8 is hopefully the last *new* audit for a while — but the process below
runs to convergence, not to a fixed count.

> Successor to mint-7 (Phases A–E, COMPLETE). mint-7 already swept correctness / security /
> code-debt / tests / docs and shipped the fixes. mint-8 goes **broader and deeper**, adds an
> **optimization** dimension over the project's own task-plans, and — per user direction — is
> built as a **reusable tool** so every future audit reuses the engine instead of re-authoring it.

---

## 0. The standing convergence process (user-directed 2026-05-31)
```
audit  →  adversarially verify findings  →  implement fixes  →  RE-AUDIT  →  … repeat …
                                                                    └── until a full audit returns CLEAN
```
- **Exit criterion:** a complete audit round surfaces **zero new independently-verified findings**
  after the prior round's fixes are in. That round is the convergence proof.
- Each round REUSES the `deep-audit.js` tool (below); each round also feeds back what the prior
  round missed (new detectors / lenses) so the tool sharpens over time.
- mint-8 is one turn of this loop. If it finds substantive issues → fix → mint-9 = re-run the tool.

---

## 1. The two artifacts
**(A) This plan** — the dimensions, methodology, severity calibration, scope boundaries, exit criterion.

**(B) `\.claude/workflows/deep-audit.js`** — a REUSABLE named Workflow (parameterized over
scope / dimensions / depth via `args`). Invoked on demand: `Workflow({name:"deep-audit", args:{...}})`,
optionally wrapped in a `/deep-audit` slash command. Shape (mirrors mint-7's 15-agent workflow but
generalized): per dimension, fan out finder agents → **adversarially verify each finding with
independent skeptic agents (default-to-refuted)** → severity-calibrate → synthesize a findings doc +
a fixes plan. See §5 for the script outline.

**What already exists — do NOT rebuild (the STATIC audit tier is reusable today):**
`scripts/ci.py` (ruff/lint/mypy/vulture/pip-audit/pytest/coverage), `ebible audit`
(audit_caches/dead_code/types/deps), `scripts/lint_rules.py` (28 checks (subprocess_stdin added mint-8; bookcode_canonical mint-7)), `/preflight`. The GAP `deep-audit.js` fills is the **deep multi-agent**
audit (the mint-N style), which was ad-hoc each time.

---

## 2. Audit dimensions (broader + deeper than mint-7's six)
Each dimension is a finder lens; findings are independently verified before they count.

**Carried from mint-7 (re-run, since fixes may have shifted things):**
1. **Correctness** — logic errors, edge cases, silent-drop paths, off-by-one, error handling.
2. **Security** (single-user LOCAL app) — stored-XSS / injection into rendered HTML, secret handling
   (`auth.json`, keys), path-traversal on file routes, `ast.literal_eval`-not-`exec` discipline.
3. **Code-debt / dead code** — duplication, god-module growth, orphaned helpers, dead branches.
4. **Tests** — coverage gaps, guard adequacy (does a test FAIL on the pre-fix state?), missing meta-tests.
5. **Docs / data hygiene** — stale refs, archived-file pointers, drift between docs and code.

**NEW deeper dimensions (the project's load-bearing invariants):**
6. **Byte-stability / build-EPUB integrity** — the 9 KJV editions must build byte-stable; the
   base-invariant (`test_nested_anchors` + `check_nested_anchors`) after any `epub_working` mutation;
   matrix==build single-resolver invariant (every per-edition control flows through ONE resolver both
   matrix + build call); epubcheck 0/0 on the flagship. (mint-7 added a determinism gate — `tests/test_byte_stability_gate.py`; deepen it.)
7. **Data-coordinate validity** — out-of-extent OCR/candidate artifacts (the `*_ch_08x`/impossible-chapter
   files mint-7 A4 only swept for ezk/jol/nam); `coord_in_canonical_extent` at every promote/ingest boundary;
   verse-count parity for the standalone Bibles.
8. **Concurrency / caching contracts** — the `lru_cache` mtime-keyed vs `maxsize=1`-singleton discipline
   (RULES §7.1); the Δ-family index correctness (rebuild lock / TTL fingerprint / per-worker storage /
   notes_io invalidation hook); xdist/`--dist=loadfile` race safety; `subprocess.DEVNULL` on Windows.
9. **Cross-module invariants** — book-code canonicalization (the ★BUGCLUSTER — re-verify the mint-7
   `bookcode_canonical` lint holds across any NEW maps); the enabled-kinds 3-way divergence (MATRIX_MAP);
   the patristic-voice composition invariant; canonical book/chapter order everywhere (RULES §6.1).
10. **Marathon-core off-limits boundary** — VERIFY nothing in the audit's own fixes (or recent commits)
    touched `build_standalone.py` / `core/manuscript_*` / `core/po_vision_store.py` / `content/manuscript/**`
    / `patrologia/**` / `GAPS/`. This is a guard ON the audit, not a finding source.

**NEW — the OPTIMIZATION dimension (user-directed 2026-05-31): re-evaluate the project's OWN task-plans/tools.**
> Not bug-finding — *approach re-evaluation*. Several plans predate Opus 4.8 (1M-context) + ultracode +
> Workflow orchestration + parallel agents, so they may no longer be the most logical / optimized method.
For EACH remaining real project task, output **confirm-it's-optimal** OR **a concrete better plan**:
- **Vision-transcription marathon** (Patrologia Esther + the Kings/Samuel manuscript collation) — the
  OOM-era method (AGENT path, MAX-1-heavy-agent, tight ≤1568px crops, per-step commits, controller-renders/
  subagent-reads) was designed under tight RAM + pre-1M-context models. Is a Workflow-orchestrated,
  1M-context, multi-witness-parallel pipeline now strictly better (faster / cheaper / higher-fidelity)?
- **Build pipeline** — a single edition build is **~133 s** (re-zips a ~23 MB `epub_working/` tree per
  edition; mint-7 E3 measured this). Is the inject→filter→zip path optimizable (incremental builds, shared
  pre-filtered base, parallel edition builds)? This is a concrete, measured optimization target.
- **Ingest pipelines** (detector → candidate → promote; the χ-cluster, the at-scale drivers) — still the
  best shape post-`at_scale_base` dedup, or is there a better orchestration?
- **Render-coverage / standalone-build** lanes — optimal given current capabilities?
**Boundary:** this dimension targets the PROJECT'S WORK (transcription, ingest, build, render), NOT the
meta-tooling / env / plugin / save setup (those are already settled).

---

## 3. Methodology (per dimension)
1. **Find** — fan out finder agent(s) per dimension over the relevant subtree (read-only). Each returns
   structured findings `{severity, title, file, evidence, fix}`.
2. **Adversarially verify** — each finding goes to ≥1 independent skeptic agent prompted to REFUTE
   (default-to-refuted if uncertain); for findings that can fail multiple ways, use perspective-diverse
   verifiers (correctness / security / does-it-reproduce). Drop findings that don't survive.
3. **Severity-calibrate** — verifier may recalibrate (mint-7 recalibrated several critical→high/medium when
   blast radius was bounded — e.g. "no shipped-output corruption, KJV editions byte-stable").
4. **Synthesize** — a findings doc (raw + verifier reasoning) + a phased fixes plan (verifier-CORRECTED
   fixes, not raw first-drafts — mint-7 had several wrong first-draft fixes).

---

## 4. Constraints on the FIXES (same as mint-7)
- No deadline; quality over speed; most-complete + correct path.
- NEVER touch the Geʽez marathon core (dimension 10 guards this).
- 9 KJV editions stay byte-stable; additive schema only; atomic writes via `notes_io`.
- TDD where it fits; prove safety (`$env:PYTHONUTF8="1"; pytest` relevant scope; byte-compat invariant for
  build-touching changes); the per-phase 5-leg save (`save-all.ps1`).
- Codify a durable GUARD for any preventable class (RULES §12) — prefer a commit-time `lint_rules` check
  over a pytest-only guard for invariants that "recur every ingest" (the mint-7 `bookcode_canonical` pattern).

---

## 5. `deep-audit.js` outline (build next session)
```js
export const meta = { name: 'deep-audit', description: 'Deep multi-agent audit: find → adversarially verify → synthesize', phases:[{title:'Find'},{title:'Verify'},{title:'Synthesize'}] }
// args = { dimensions?: string[], scope?: string, depth?: 'normal'|'deep', round?: number }
const DIMENSIONS = args?.dimensions ?? [ /* §2: correctness, security, code-debt, tests, docs,
  byte-stability, data-validity, concurrency-caching, cross-module-invariants, optimization */ ]
// 1) FIND — pipeline per dimension: one (or N at deep) finder agent(s) → structured findings
// 2) VERIFY — for each finding, parallel skeptics prompted to REFUTE (default refuted); keep survivors
// 3) SYNTH — dedup, severity-calibrate, emit findings doc + phased fixes plan
// Reuse mint-7's structured-output schema; loop-until-dry for unknown-size discovery; completeness critic last.
```
Wrap optionally as a `/deep-audit` command. The findings + plan land under `docs/superpowers/` (like mint-7).

---

## 6. Exit
When a full `deep-audit` round returns **zero new verified findings** post-fix, declare convergence — the
codebase + the project's task-plans are audited clean to current depth. Until then, each round = re-run the
tool, fix, re-run.
