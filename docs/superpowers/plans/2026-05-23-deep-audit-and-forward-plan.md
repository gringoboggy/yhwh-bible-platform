# Deep Audit & Forward Plan — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Inspect every code/doc/config file in the `YHWH v2.4/` git repo for dead code, junk, security holes, and logical inconsistency; fix the safe findings (verified, uncommitted); re-certify the matrix as mint; and produce a fully-scoped forward plan for all remaining work toward the 2026-06-07 deadline.

**Architecture:** A partitioned **read-phase** of parallel read-only subagents (8 partitions A–H, dispatched in waves that respect the workload-tiered agent cap) feeds a centralized **synthesis + fix phase** owned by the main session. Findings land in `dev/AUDIT_2026-05-23-DEEP.md`; safe fixes are applied with byte-compat/test verification; the forward roadmap lands in `dev/PLAN_2026-05-23.md`.

**Tech Stack:** Python 3.14 (stdlib-only backend), pytest, ruff, the in-repo tools (`lint_rules.py`, `dev/trace_matrix.py`, `dev/trace_repo.py`, `audit.py`, `validate_taxonomy.py`, `validate_schemas.py`, `ebible verify`, `audit_base_html.py`), epubcheck (Java 8).

**Spec:** `docs/superpowers/specs/2026-05-23-deep-audit-and-forward-plan-design.md`

---

## Conventions for every task (read once)

- **Python:** `& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe"` with `$env:PYTHONUTF8="1"` set in the session. Bare `python`/`python3` is a broken Store stub — do not use.
- **Tests:** one file at a time; **never** the full `tests/test_scripts.py` (it hangs on build/socket smokes) — use `-k` selectors. `subprocess.run` in any new test helper passes `stdin=subprocess.DEVNULL`.
- **epubcheck:** Java 8 at `C:\Program Files\Java\jre1.8.0_491\bin` (off PATH); jar in the PyPI `epubcheck` site-package. One JVM at a time (concurrent JVMs crash HotSpot → delete any `hs_err_pid*.log`/`replay_pid*.log` before proceeding).
- **No commit** in any task. "save" is the user's word; this plan ends with everything staged-in-working-tree and a save offer.
- **Byte-compat invariant:** any task that regenerates an artifact or removes code proves zero output change (regen + empty `git diff` on the artifact; targeted tests green) before the task is "done".
- **Agent cap:** heavy ≤1, medium ≤2, light ≤4 concurrent; drain a wave before dispatching the next.

---

## Phase 0 — Baseline capture (prove "no regression" later)

### Task 0.1: Capture the green baseline

**Files:**
- Create: `dev/AUDIT_2026-05-23-DEEP.md` (skeleton + baseline block)

- [ ] **Step 1: Record git + tree state**

Run:
```powershell
git -C "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4" log --oneline -1
git -C "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4" status --short
```
Expected: HEAD `42a59e0`, clean tree. Record both in the audit doc's "Baseline" block.

- [ ] **Step 2: Record validator baseline**

Run (from repo root, `$env:PYTHONUTF8="1"`):
```powershell
& $py scripts\lint_rules.py
& $py dev\trace_matrix.py
& $py dev\trace_repo.py
& $py scripts\validate_taxonomy.py
& $py scripts\validate_schemas.py
& $py -m scripts.ebible verify
```
Expected: lint_rules 16/0/0; trace_matrix 0 unresolved; trace_repo complete; validate_taxonomy 100% / 67,713; validate_schemas clean; ebible verify errors=0 / 24,015 paired. Record each number in the Baseline block. **If any is NOT green, STOP and report** — the baseline must be green before auditing.

- [ ] **Step 3: Record test-collection baseline**

Run:
```powershell
& $py -m pytest tests/ --collect-only -q 2>$null | Select-Object -Last 1
```
Record the collected test count (expected ~6462+). This is the regression anchor.

- [ ] **Step 4: Snapshot the file inventory**

Run:
```powershell
git -C "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4" ls-files | Measure-Object -Line
git -C "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4" ls-files > $env:TEMP\yhwh_tracked_files.txt
```
Record tracked-file count. This list is the authoritative "what's in the repo" for the junk/dead-file axis (untracked-but-present files inside the repo are a separate finding class).

- [ ] **Step 5: Write the audit-doc skeleton**

Create `dev/AUDIT_2026-05-23-DEEP.md` with: Baseline block (above), and one empty section per axis (1–8) and per partition (A–H), each with a findings table (`| # | finding | location | severity | disposition |`).

---

## Phase 1 — Read-phase parallel sweep (8 partitions, A–H)

**Reusable agent prompt template** (fill `{PARTITION}`, `{FILE_SCOPE}`, `{LENS}`):

> You are auditing a mature, disciplined Python Bible-publishing repo at `C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4`. READ-ONLY: do not edit/write/commit anything. Scope: **{FILE_SCOPE}**. Lens: **{LENS}**.
> For every file in scope, report findings in these classes: (1) **dead code / unreachable** — functions/classes/branches/modules with no caller from a CLI entrypoint, web route table, test, build step, or data-loader (account for dynamic dispatch: route tables `_SIMPLE_GET_ROUTES`/`_PUT_ROUTES`, lazy imports, `__all__` re-export hubs, `ast.literal_eval`-loaded data, CLI `main()`); (2) **junk** — scratch/log/obsolete files, one-shot `_ship_*` past retention; (3) **bug/correctness risk**; (4) **security** — secrets, `exec`, path traversal, subprocess shell, unvalidated upload/multipart, unescaped served HTML; (5) **staleness** — comments/docstrings/docs that contradict the code; (6) **"could be done better"** — duplication, god-modules, perf, unclear boundaries.
> Output a markdown table: `| finding | file:line | class | severity (crit/high/med/low) | evidence | suggested fix |`. Cite exact `file:line`. Prefer high-confidence findings; mark uncertain ones "NEEDS-VERIFY". Do NOT fix anything. Report counts of files actually read vs. skipped. Keep under ~1200 words; attach the table.

File scopes per partition:
- **A** (security-critical HTTP): `scripts/web.py`, `scripts/api/**/*.py`
- **B** (core): `scripts/core/**/*.py`
- **C** (tools+templates): `scripts/*.py` (non-core top-level), `scripts/templates/**/*.py`
- **D** (tests): `tests/**/*.py` + `tests/conftest.py` + `tests/fixtures/**` — lens adds: skipped/xfail tests, stale hardcoded counts, and **root-cause why `pytest tests/test_scripts.py` hangs** (which test/fixture opens a socket/subprocess without teardown).
- **E** (docs/rules/maps): `dev/**/*.md`, `CLAUDE_PROJECT_RULES.md`, `MATRIX_MAP.md`, `REPO_MAP.md`, root `*.md` (`HANDOFF_README_v7.md`, `COPYRIGHT.md`, `LICENSE`, `VERSION`, `Makefile`, README files) — lens adds: internal contradictions, claims that contradict current code (verify a sample of named modules/functions still exist), dangling cross-references between docs.
- **F** (content+data+build artifacts): `content/**/*.yaml`, `content/**/*.py` (loaders + sample of data stores), `epub_working/` sanity, `docs/superpowers/**` — lens adds: config keys referenced nowhere; orphaned kinds/editions/canons; translation `_meta.yaml` provenance completeness.
- **G** (cross-cutting security): all of `scripts/` + `.env`/`.env.example`/`.githooks/` + `requirements.txt`/`pyproject.toml` — pure security lens (own the OWASP-style pass; G's findings supersede A–F's security notes on conflict).
- **H** (cross-cutting reachability/junk): build the repo-wide import + route + reference graph; output the list of **unreferenced modules**, **unreferenced top-level functions/classes**, and **tracked-but-junk files** (logs, scratch). This is the master "dead cell" list. Must account for the dynamic-dispatch false-positive sources listed in the template.

### Task 1.1: Dispatch Wave 1 (partitions A, B, H) — medium/heavy

- [ ] **Step 1:** Dispatch 3 agents? No — cap. A (medium), B (medium), H (medium) = 3 medium > cap(2). Split: dispatch **A + B** (2 medium) in parallel.
- [ ] **Step 2:** On drain, collect A + B reports into the audit doc partition sections.
- [ ] **Step 3:** Dispatch **H** alone (it depends on a full-repo graph; heavy-ish; run solo).
- [ ] **Step 4:** Collect H. Verify each agent reports `files read` ≈ `files in scope` (no silent skips); if an agent skipped files, re-dispatch for the remainder.

### Task 1.2: Dispatch Wave 2 (partitions C, D) — medium

- [ ] **Step 1:** Dispatch **C + D** (2 medium) in parallel.
- [ ] **Step 2:** Collect into the audit doc. For D, capture the test-hang root-cause as a named finding.

### Task 1.3: Dispatch Wave 3 (partitions E, F, G)

- [ ] **Step 1:** Dispatch **E + F** (2 medium) in parallel.
- [ ] **Step 2:** Collect. Dispatch **G** (security) alone (so its pass is undistracted + I review it personally).
- [ ] **Step 3:** Collect G.

### Task 1.4: Coverage reconciliation

- [ ] **Step 1:** Cross-check the union of "files read" across A–H against `$env:TEMP\yhwh_tracked_files.txt`. Any tracked code/doc/config file not covered by ≥1 partition gets a targeted follow-up read (by me, directly). Record coverage % in the audit doc. **Target: 100% of tracked `.py`/`.md`/`.yaml`/`.sh`/config files read.**

---

## Phase 2 — Synthesis

### Task 2.1: Build the consolidated findings ledger

- [ ] **Step 1:** Deduplicate findings across partitions (G's security view wins on security; H's reachability view wins on dead-code). Assign each a stable ID (`F-001`…).
- [ ] **Step 2:** Classify each finding's disposition: **SAFE-FIX** (mechanical, verifiable, no behavior change), **QUEUED** (risky/behavior-changing/judgment), or **WON'T-FIX** (with one-line reason).
- [ ] **Step 3:** Sort the ledger by severity then axis. This is the master section of `dev/AUDIT_2026-05-23-DEEP.md`.
- [ ] **Step 4:** Personally spot-verify every `crit`/`high` finding and every NEEDS-VERIFY before trusting it (agents can hallucinate `file:line`). Demote/correct as needed.

---

## Phase 3 — Apply SAFE-FIX findings (each verified, uncommitted)

> Procedure-per-class. For EACH safe-fix finding, the loop is: apply edit → run the finding's verification gate → if green, mark fixed in the ledger; if red, revert + re-classify to QUEUED.

### Task 3.1: Junk-file removal

- [ ] **Step 1:** For each tracked junk file (e.g. `*-pytest.log`, `.ingest_1en.log`, `_tau6x2t_jub_ocr.log`, stray scratch), confirm it's tracked (`git ls-files <f>`) and referenced nowhere (`grep`), then `git rm --cached`-equiv via deletion in working tree.
- [ ] **Step 2: Verify** — `& $py dev\trace_repo.py` still complete; `& $py scripts\lint_rules.py` 16/0/0; targeted import smoke of anything in the same dir. Record bytes reclaimed.

### Task 3.2: Doc-staleness fixes

- [ ] **Step 1:** Fix each stale doc claim found in partition E (starting with the known SESSION_STATE/IN_FLIGHT "uncommitted → actually committed at 42a59e0" drift). Edit in place; preserve structure.
- [ ] **Step 2: Verify** — `& $py scripts\lint_rules.py` (doc-xref + plan_coherence checks) 16/0/0.

### Task 3.3: Dead-import / trivially-dead-code removal (test-verified only)

- [ ] **Step 1:** For each dead symbol from H that is NOT a re-export hub / route-table target / `__all__` member (memory `feedback_ruff_f401_reexport_hubs`), remove it.
- [ ] **Step 2: Verify** — run the impacted module's targeted test file(s) `-k`; run `& $py scripts\lint_rules.py`; if the symbol was importable, grep tests for the name first. **Any failure → revert + reclassify QUEUED.** Dead code with ANY uncertainty stays QUEUED.

### Task 3.4: Lint + cross-link fixes

- [ ] **Step 1:** Run `& $py -m ruff check scripts tests` — categorize the residual (was 243). Apply only mechanically-safe categories per-rule (`ruff check --select <RULE> --fix`) followed by a targeted test run per batch (never a blind repo-wide `--fix`).
- [ ] **Step 2:** Fix any cross-link/console-nav violations (lint_rules 6.2).
- [ ] **Step 3: Verify** — `& $py -m ruff format --check .` clean; `& $py scripts\lint_rules.py` 16/0/0; the touched test files green.

---

## Phase 4 — Matrix mint re-certification

### Task 4.1: Re-prove the matrix invariants after the recent spine ships

- [ ] **Step 1:** Run, capturing output:
```powershell
& $py dev\trace_matrix.py            # expect 0 unresolved refs, all 11 editions
& $py scripts\validate_taxonomy.py   # expect 100% attributed / 67,713
& $py -m pytest tests/test_enabled_kinds_unified.py -q   # matrix == build == config
& $py -m scripts.ebible verify       # errors=0 / 24,015 paired
```
- [ ] **Step 2:** Build 2 representative editions + epubcheck (one JVM at a time): a max-canon (`ethiopian-tewahedo`) and a canon-spliced + popup-heavy (`catholic-study`). Expect 0/0/0/0 each.
- [ ] **Step 3: Write the certification block** in the audit doc: each command + its result + date, signed "matrix mint as of 2026-05-23 post-spine". Refresh `dev/MATRIX_MAP.md` counts if any drifted.

---

## Phase 5 — Rules + maps logical-consistency pass

### Task 5.1: Reconcile every rule and map against reality

- [ ] **Step 1:** From partition E's findings, build a contradiction/staleness list across RULES (§0–§15), MATRIX_MAP, REPO_MAP, PLAN, SESSION_STATE, IN_FLIGHT, the ~17 SCOPE addenda.
- [ ] **Step 2:** For each: verify against current code (grep the named module/function/flag). Fix stale prose in place; for genuine rule conflicts, present to user (QUEUED) rather than unilaterally rewriting a rule.
- [ ] **Step 3:** Verify the scope-addenda index in PLAN matches the files on disk (lint_rules doc-xref). Verify every doc cross-reference resolves.
- [ ] **Step 4: Verify** — `& $py scripts\lint_rules.py` 16/0/0 (plan_coherence, repo_map_complete, doc-xref all pass); `& $py dev\trace_repo.py` complete.

---

## Phase 6 — Author the fully-scoped forward plan

### Task 6.1: Write `dev/PLAN_2026-05-23.md` (supersedes PLAN_2026-05-21)

- [ ] **Step 1:** Re-audit current health (mirror PLAN_2026-05-21 §1 table) with this session's fresh numbers.
- [ ] **Step 2:** For EACH remaining piece, write a fully-scoped block (objective · concrete steps · dependencies · effort estimate · risk · verification gate):
  - Phase E — Clementine appendix Latin (`man`/`1es`/`2es`)
  - Shared vision-OCR engine (generalize `manuscript_vision.py` to printed PDFs)
  - Prior-translation re-verify-vs-table pass (WLC/LXX/Arabic/JPS)
  - Phase 3 — per-book version-selection UI
  - Phase 4 — per-note curation / source review
  - Track B — Kings/Samuel Geʽez dual-witness marathon + the two standalone Bibles (CRITICAL PATH)
  - Track C — corpus expansion (opportunistic, user-fed)
  - Track D — remaining cleanup/upgrades (incl. any QUEUED items from this audit)
  - Demo — the [USER] e-reader device check
- [ ] **Step 3:** Produce the **deadline-aware sequence** to 2026-06-07: marathon as the binding calendar constraint, the bounded autonomous backlog filling gaps (per the ratified §4.0 strategy).
- [ ] **Step 4:** Cross-reference the audit doc's QUEUED items into Track D so nothing is orphaned.
- [ ] **Step 5: Verify** — `& $py scripts\lint_rules.py` plan_coherence passes for the new plan; add the new plan to the scope-addenda/PLAN pointer chain (RULES §0, SESSION_STATE map layer).

---

## Phase 7 — Final reconciliation + present

### Task 7.1: Regression gate + state docs

- [ ] **Step 1:** Re-run the full Phase-0 baseline command set. **Every number must be ≥ baseline and every validator green** (test count not decreased except by intentionally-removed dead tests, which are itemized in the ledger).
- [ ] **Step 2:** Update `dev/SESSION_STATE.md` (what the audit shipped, next), `dev/IN_FLIGHT.md` (state), `dev/CHANGELOG.md` (one entry). **Do not commit.**
- [ ] **Step 3:** Run the §12 4-point pre-summary audit (test count reconcile, phase mention scan, in-flight marker, linter ack).

### Task 7.2: Present to user

- [ ] **Step 1:** Present: (a) the audit ledger summary (counts by severity/disposition, headline findings), (b) the QUEUED decisions list with recommendations for go/no-go, (c) the matrix mint-certification, (d) the forward plan. Offer "save" (the local commit) per save semantics.

---

## Self-review (spec coverage)

- Success criteria 1 (no dead cells) → Phase 1 (H) + Phase 3.3 + QUEUED list. ✓
- 2 (no junk) → Phase 1 (H) + Phase 3.1. ✓
- 3 (no security holes) → Phase 1 (G) + spot-verify in 2.1. ✓
- 4 (rules/maps sense) → Phase 1 (E) + Phase 5. ✓
- 5 (matrix mint) → Phase 4. ✓
- 6 (rest fully planned) → Phase 6. ✓
- 7 (systems evaluated) → Phase 1 "could be done better" class + QUEUED list + Phase 6 Track D. ✓
- Baseline/regression safety → Phase 0 + Phase 7.1. ✓
- No-commit / save semantics → Conventions + 7.2. ✓
