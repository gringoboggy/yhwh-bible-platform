# Deep Audit & Forward Plan — design spec (2026-05-23)

**Status:** approved (design) — proceeding to writing-plans.
**Author:** Claude (superpowers brainstorming flow).
**Companions:** `dev/CLAUDE_PROJECT_RULES.md`, `dev/MATRIX_MAP.md`, `dev/REPO_MAP.md`,
`dev/PLAN_2026-05-21.md` (to be superseded by `dev/PLAN_2026-05-23.md`).

## Why

The user asked to "switch focus to the deferred in-depth audit/optimization of
everything — every file inspected, no matter how small, top to bottom and back
up. No junk, no issues, no security problems. Not a single dead cell; everything
must lead somewhere. The rest of the project fully inspected and a detailed plan
for each remaining piece, with an evaluation of existing systems to see if they
can be done better. Every rule and all the maps must make full logical sense.
The rest of the plan absolutely fully planned out, and the matrix in absolutely
mint condition."

This is the **heavy parallel-subagent sweep** (memory `feedback_audit_cadence`),
not the lighter solo pass. The project is mature and already runs four tiers of
self-audit, so this audit deliberately targets the defect classes those nets
miss, fixes the safe ones, plans everything remaining, and re-certifies the
matrix.

## Scope (user-chosen)

- **Boundary:** the git repo `YHWH v2.4/` only. Tracked junk *inside* the repo is
  in scope; the parent-folder throwaway probes (`_vg_*.py`, `_probe_*.py`,
  screenshots, scratch JSON) and `_acquire/` clones are out of scope (outside
  version control; the user cleans those at will).
- **Fix mode:** fix safe/mechanical findings inline *with verification*; queue
  risky/behavior-changing findings for user go/no-go. **Nothing is committed
  until the user says "save"** (memory `feedback_continue_not_save`,
  `feedback_save_is_local_commit`).
- **Data depth:** the bulk generated data (67,713 note tuples across 87 books, 13
  translation stores, baked `epub_working/` HTML) is **integrity-validated +
  sampled** via the existing guards; every **generator / extractor / loader /
  validator** is read exhaustively. Defects live in the code that produces data,
  not in 67k hand-unreadable tuples.

## Success criteria (each must be evidenced)

1. **No dead cells** — every module, function, class, template, route, config
   key, kind, edition, tracked file is reachable from a real entry point (CLI,
   web route, test, build pipeline, data-load) or is removed/documented.
2. **No junk** — no tracked log files, scratch files, obsolete one-shot scripts
   past their §7.4 retention rule, or dead artifacts in the repo.
3. **No security holes** — fresh pass: secrets/`.env`, `literal_eval`-not-`exec`,
   static-route path traversal, multipart/upload validation, subprocess calls,
   server-emitted HTML.
4. **Rules + maps make full logical sense** — RULES, MATRIX_MAP, REPO_MAP, PLAN,
   SESSION_STATE, IN_FLIGHT, the ~17 SCOPE addenda: zero internal contradictions,
   zero stale claims vs. actual code, zero dangling cross-references.
5. **Matrix certifiably mint** — `trace_matrix` 0 unresolved, `validate_taxonomy`
   100%, the 3-way enabled-kinds invariant (matrix == build == config) holds,
   `ebible verify` errors=0, epubcheck 0/0/0/0, re-verified *after* the recent
   Arabic/JPS/Douay/Vulgate ships, with the certification written down.
6. **Rest of project fully planned** — every remaining piece scoped with steps,
   deps, effort, and a deadline-aware sequence (marathon = critical path to
   2026-06-07).
7. **Existing systems evaluated** — god-module candidates (`build_edition.py`,
   `prospect.py`, `core/sources.py` ~116KB, `core/versification.py`), the ψ.35
   matrix layering, duplicate logic, perf budgets, and the "test suite hangs"
   smell each get a verdict: improve-now / plan / won't-fix-with-reason.

## Targeting principle

The repo already runs **lint_rules (16 checks), trace_matrix, trace_repo,
audit.py (B1–B8)**, plus validate_taxonomy/schemas, ebible verify, and the
coord-extent guard; the matrix was clean on 2026-05-22. Re-running validators
proves little. The audit hunts the **8 axes that escape all four tiers**:

| # | Axis | Escape reason |
|---|------|---------------|
| 1 | Dead code / reachability | no vulture-style scan; route-tables + lazy imports + `literal_eval` data defeat naive detection |
| 2 | Junk files | trace_repo checks top-level *dir* documentation, not file-level cruft (e.g. the `*-pytest.log` pile in repo root) |
| 3 | Security | TRUFFLEHOG/CODESPELL findings date to 2026-05-10; a live `.env` exists |
| 4 | Rules/maps consistency | nothing machine-checks prose for contradiction or staleness-vs-code |
| 5 | Architecture / "done better" | perf + god-module smells aren't gated |
| 6 | Matrix re-certification | was clean *before* the recent translation-spine ships |
| 7 | Test-suite health | the "don't run full test_scripts.py — it hangs" workaround is itself a latent defect |
| 8 | Forward-plan completeness | the plan is the deliverable, not a check |

## Method

**Read/find phase — partitioned parallel read-only subagents.** Each returns a
structured findings report (finding · location · severity · suggested
disposition). Respects the workload-tiered agent cap (memory
`feedback_concurrent_agent_cap`: heavy ≤1, medium ≤2, light ≤4; drain before
re-dispatch). Partitions:

- **A** — `web.py` + `scripts/api/*` (HTTP surface; security-critical)
- **B** — `scripts/core/*`
- **C** — `scripts/*` tools + `scripts/templates/*`
- **D** — `tests/*` (skips/xfails, stale-count pins, the hang root-cause)
- **E** — `dev/*` docs + 3 maps + RULES + root docs (consistency + staleness)
- **F** — `content/` config+loaders + data integrity (run the guards) +
  `epub_working/` + `docs/superpowers/`
- **G** — cross-cutting security lens (secrets, subprocess, traversal, eval,
  uploads, served HTML)
- **H** — cross-cutting dead-code/junk/reachability graph (import + route +
  reference graph → unreferenced symbols/files)

**Synthesis + fix phase — centralized (me).** Agents find; I decide and fix. I
personally own security verdicts, rules/maps consistency edits, the matrix
re-certification, dead-code removal decisions (risky here: memory
`feedback_ruff_f401_reexport_hubs` — blind import removal once broke 10 tests via
re-export hubs), and the forward plan.

## Deliverables

1. `dev/AUDIT_2026-05-23-DEEP.md` — findings ledger: every finding by axis +
   severity + disposition (fixed / queued / won't-fix-with-reason).
2. Inline safe fixes — junk removal, doc-staleness, dead imports (test-verified),
   lint, broken cross-links — each verified; **uncommitted** until "save".
3. A queued-decisions list — risky/behavior-changing items + my recommendation,
   for user go/no-go.
4. `dev/PLAN_2026-05-23.md` — fully-scoped forward roadmap (supersedes
   PLAN_2026-05-21); marathon = critical path; every remaining piece with
   steps/deps/effort/sequence.
5. Matrix mint-certification — written proof block (re-run evidence) in the audit
   doc + MATRIX_MAP refresh.

## Guardrails (from user memories)

- **Byte-compat / matrix==build invariant** — any refactor/removal proves zero
  output change (regen + empty `git diff`; targeted tests green) before counting
  as done.
- **Verify before claiming** — every "fixed" backed by a command + its output.
- **Save semantics** — no commits by me; "continue" ≠ "save".
- **Risky → queued**, never auto-applied. Dead-code removal defaults to queued
  unless a clean test-verified proof exists.
- **Windows gotchas** — full Python path (`C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe`)
  + `$env:PYTHONUTF8="1"`; one test file at a time; never the full
  `test_scripts.py` (hangs — use `-k`); epubcheck one JVM at a time (Java 8
  off-PATH); `subprocess.run` needs `stdin=DEVNULL` on Windows.

## Sequence within the audit

Read-phase agents (waves, cap-respecting) → synthesize the ledger → apply safe
fixes + verify each → re-certify the matrix → audit rules/maps for consistency +
fix staleness → write the forward plan → present queued decisions + the ledger +
the plan.

## Out of scope

- Executing the planned forward work (Phase E, vision-OCR engine, Phase 3/4, the
  marathon chapters). This audit *plans* them; it does not build them.
- Parent-folder cleanup and `_acquire/` clones.
- Committing (the user issues "save").
