# YHWH v2.4 "Mint" Cleanup + Automated Guardrails — Implementation Plan
**Status:** COMPLETE — all Phases 0–6 shipped + synced 2026-05-31 (HEAD ad945f62)

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` (recommended) to implement this plan phase-by-phase, fresh subagent per task, two-stage review between tasks. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make the project "mint" — strip the accumulated bloat (truth-record journals, dead commercial-era code, sprawled docs, a stale roadmap), and install automated guardrails so none of it can silently rebuild.

**Architecture:** Guards-FIRST. Add ~11 size/sprawl/orphan/term checks into the existing `scripts/lint_rules.py` `ALL_CHECKS` registry — each auto-propagates to BOTH the pre-commit gate AND the `/preflight` dashboard (one add → two surfaces). They ship RED (everything is over budget today), which then *forces* the cleanup work and locks it permanently. Cleanup follows in dependency order. The Geʽez marathon core is never touched.

**Tech stack:** Python 3 (stdlib + ruff + mypy), `lint_rules.py` check-registry pattern, `notes_io.atomic_write`, PowerShell hooks, GitHub Actions (when a remote is restored). **Language verdict from the audit: KEEP PYTHON — a rewrite loses on engineering merit, not just schedule** (strongest ecosystem for lxml/EPUB/Pillow/PDF/Unicode-Geʽez; single-user offline batch tool, no hot path; mypy already clean; solo-maintainability is best served by the language the maintainer knows).

**Source:** the 2026-05-29 8-agent mint-audit. Full verified report persisted at `…/tasks/wwkqbhood.output` (87 KB).

---

## Guiding constraints (apply to every task)

1. **No deadline, no cost ceiling.** Optimize purely for clean/correct/maintainable. Bigger-but-right is allowed; reject only change-for-change's-sake.
2. **NEVER touch the Geʽez marathon core.** Off-limits: `scripts/build_standalone.py`, `scripts/core/manuscript_*`, `scripts/core/po_vision_store.py`, `content/manuscript/**`, `content/translations/sources/patrologia/**`, the `GAPS/` tree, Phase-D work. Cleanup everywhere else proceeds at full pace without tiptoeing.
3. **Prove safety before claiming done.** After any change: `$env:PYTHONUTF8="1"; pytest` (relevant scope) must pass. For anything that could affect a build: **byte-compat invariant** — regenerate the EPUB(s), `git diff` `epub_working/` must be empty, flagship `epubcheck` 0/0/0/0, 9 KJV editions byte-stable.
4. **Atomic writes only** — any file write goes through `scripts.core.notes_io.atomic_write` (raw `open('w')` trips the existing `atomic_writes` lint check at `lint_rules.py:853`).
5. **Commit per task; back up every 3rd commit** to E:/F: via `git bundle`. Save via `save.ps1` (PowerShell only).

---

## The lint check contract (shared by all new guards)

Every check is a function returning the project's standard dict (RULES §9):

```python
{"id": str, "name": str, "status": "pass" | "warn" | "fail", "message": str, "violations": list}
```

Register it in the `ALL_CHECKS` dict (`scripts/lint_rules.py:1368`). That single registration makes it run in `.githooks/pre-commit` AND render in `/preflight` (`_compute_preflight_uncached` composes `run_all()`). FIXERS register at `lint_rules.py:1493`. No new infrastructure is built — we extend the registry.

---

## Guardrail catalog (Phase 0 deliverable)

| id | tier | what it checks | threshold |
|---|---|---|---|
| `truth_record_budget` | **FAIL**/warn | byte size + `➤➤➤` count of SESSION_STATE, IN_FLIGHT, CLAUDE_PROJECT_RULES | SS/IF: FAIL>120KB, WARN>60KB(SS)/40KB(IF), max 2 entries; RULES: WARN>50KB |
| `commercial_orphans` | **FAIL** | removed module stems reappearing as files/imports under `scripts/` | zero tolerance (denylist: sales, license_key, license_state, onix, build_onix, print_cover) |
| `commercial_terms` | **FAIL** | commercial vocab in live `scripts/`+`dev/` (royalty, KDP, retailer, Apple Books, Google Play, ISBN, ONIX, pricing, sales_record) | FAIL outside allowlist (archive_org + the "what this is NOT" pivot note) |
| `retired_terms` | **FAIL** | denylist in `dev/*.md` rules/process docs (`2026-06-07`, `hard deadline`, `sonar`) | FAIL on match |
| `triad_plan_consistency` | **FAIL** | PLAN filename in RULES §0, SESSION_PLAYBOOK, bootstrap-triad.ps1 byte-identical + resolves live | FAIL on divergence/archived |
| `dev_doc_sprawl` | warn | count of live `dev/*.md`; dated AUDIT/SCOPE/CALIBRATION/PILOT/PROPOSAL/SESSION_END older than active PLAN & unreferenced | WARN > 40 (currently 87) |
| `rules_no_frozen_stats` | warn | dated-arc-tag + percentage lines, or >8 stat tokens, in CLAUDE_PROJECT_RULES.md | WARN |
| `changelog_size` | warn | byte size of dev/CHANGELOG.md (do NOT auto-rotate) | WARN > ~1.5MB |
| `stray_artifacts` | **FAIL** | working tree junk (`*.pyc` outside ignores, `*.tmp`, debug `*.log`, top-level names with `>`/arrows, zero-byte `dev/*.md`, stray PDFs/images staged into scripts/dev, `.sonar` dirs) | FAIL; `# stray-waived` allowlist |
| `doc_cross_references` | warn | **UPGRADE existing (`:360`)**: scan `dev/archive/` recursively; validate PLAN/intra-repo links in SESSION_STATE/SECURITY/README resolve | WARN on unreferenced live SCOPE / dangling path |
| `repo_map_complete` | **FAIL** | **UPGRADE existing (`:1237`)**: per-dir file COUNT match vs live `os.scandir`; reverse path-exists for every path cited | flip WARN→FAIL on drift/missing |

Plus a **save.ps1 file-count gate** (defense-in-depth, not a lint check): before `git add -A`, if >200 files would stage, print and require `--yes`.

---

## PHASE 0 — Install the guards RED (foundational; no dependencies; pure additive lint code)

**Why first:** they ship RED (SESSION_STATE/IN_FLIGHT/RULES over budget, dev/ has 87 docs, commercial stems + TODO placeholders present) and turn the cleanup into a gate the codebase demands. Low risk — additive code + tests only; touches nothing the marathon uses.

**Files:** Modify `scripts/lint_rules.py` (add to `ALL_CHECKS` @ 1368; upgrade `check_doc_cross_references` @ 360, `check_repo_map_complete` @ 1237). Test `tests/test_lint_guardrails.py` (new). Modify `save.ps1`.

### Task 0.1 — `check_truth_record_budget`
- [ ] **Step 1 — failing test** in `tests/test_lint_guardrails.py`:
```python
from scripts import lint_rules
def test_truth_record_budget_flags_oversize(tmp_path, monkeypatch):
    big = tmp_path / "SESSION_STATE.md"
    big.write_text("➤➤➤\n" * 5 + "x" * 130_000, encoding="utf-8")
    monkeypatch.setattr(lint_rules, "REPO", tmp_path)
    r = lint_rules.check_truth_record_budget()
    assert r["status"] == "fail"
    assert any("SESSION_STATE" in v for v in r["violations"])
```
- [ ] **Step 2 — run, expect FAIL** (`AttributeError: check_truth_record_budget`): `$env:PYTHONUTF8="1"; pytest tests/test_lint_guardrails.py::test_truth_record_budget_flags_oversize -v`
- [ ] **Step 3 — implement** in `lint_rules.py` (near the other `check_*` defs):
```python
_TRUTH_BUDGETS = {
    "dev/SESSION_STATE.md":        {"soft": 60_000,  "hard": 120_000, "max_entries": 2},
    "dev/IN_FLIGHT.md":            {"soft": 40_000,  "hard": 120_000, "max_entries": 2},
    "dev/CLAUDE_PROJECT_RULES.md": {"soft": 50_000,  "hard": None,    "max_entries": None},  # WARN-only, curated
}
def check_truth_record_budget():
    violations, status = [], "pass"
    def _worse(s):  # fail > warn > pass
        nonlocal status
        if s == "fail" or (s == "warn" and status == "pass"):
            status = s
    for rel, b in _TRUTH_BUDGETS.items():
        p = REPO / rel
        if not p.exists():
            continue
        size = p.stat().st_size
        if b["hard"] and size > b["hard"]:
            violations.append(f"{rel}: {size:,}B > HARD {b['hard']:,}B"); _worse("fail")
        elif size > b["soft"]:
            violations.append(f"{rel}: {size:,}B > soft {b['soft']:,}B"); _worse("warn")
        if b["max_entries"] is not None:
            n = p.read_text(encoding="utf-8").count("➤➤➤")
            if n > b["max_entries"]:
                violations.append(f"{rel}: {n} entries > {b['max_entries']}"); _worse("warn")
    msg = "truth records within budget" if not violations else \
          f"{len(violations)} budget issue(s) — run `python scripts/rotate_truth_records.py --apply`"
    return {"id": "truth_record_budget", "name": "Truth-record size budget",
            "status": status, "message": msg, "violations": violations}
```
- [ ] **Step 4 — register** in `ALL_CHECKS` (`:1368`): add `"truth_record_budget": check_truth_record_budget,`.
- [ ] **Step 5 — run, expect PASS** (test) + run `python scripts/lint_rules.py` and confirm it now reports `truth_record_budget` **fail** against the real (oversize) files.
- [ ] **Step 6 — commit:** `feat(lint): truth_record_budget guard (ships RED — forces Phase 1 slim)`

### Task 0.2 — `check_commercial_orphans` + `check_commercial_terms`
- [ ] Failing tests: a temp `scripts/` containing `sales.py` (orphan) and a file with `KDP` ⇒ both FAIL.
- [ ] Implement: `commercial_orphans` = deterministic denylist of stems `{sales, license_key, license_state, onix, build_onix, print_cover}` appearing as a file under `scripts/` OR as an `import`/`from` target anywhere in `scripts/`; allowlist `archive_org`. `commercial_terms` = regex denylist `{royalty, KDP, retailer, Apple Books, Google Play, ISBN, ONIX, pricing, sales_record}` scanned over live (non-`archive/`, non-`test_`) `scripts/` + `dev/*.md`; allowlist archive_org files + the explicit `§10 "what this is NOT"` pivot line. **NOT vulture** (audit verified vulture@100 finds 0 — the orphans are route-reachable).
- [ ] Register both; run — they ship **RED** (the modules still exist). Commit.

### Task 0.3 — `check_retired_terms` + `triad_plan_consistency`
- [ ] Failing tests. Implement `retired_terms` (denylist `2026-06-07`, `hard deadline`, `sonar` across `dev/*.md`); `triad_plan_consistency` (the `PLAN_*.md` filename referenced in `CLAUDE_PROJECT_RULES.md` §0, `SESSION_PLAYBOOK.md`, `.claude/hooks/bootstrap-triad.ps1` must be byte-identical and resolve to a live, non-archived file). Register; both ship **RED** today. Commit.

### Task 0.4 — `check_dev_doc_sprawl`, `check_rules_no_frozen_stats`, `check_changelog_size` (all WARN)
- [ ] Failing tests. Implement per the catalog (counts/heuristics; WARN tier). Register. Commit.

### Task 0.5 — `check_no_stray_artifacts` (FAIL)
- [ ] Failing test (temp tree with a `.tmp` + a `__pycache__` outside ignore ⇒ FAIL). Implement using `git ls-files --others --exclude-standard` + staged set; junk patterns per catalog; `# stray-waived` allowlist constant. Register. Commit.

### Task 0.6 — UPGRADE `check_doc_cross_references` (archive-aware) — **unblocks Phase 3**
- [ ] Failing test: an archived `dev/archive/scope/SCOPE_x.md` referenced by PLAN must satisfy the check.
- [ ] Modify `:360` so the "actual" set globs `dev/**` including `dev/archive/` recursively; add dangling-path validation for `dev/PLAN_*.md` + intra-repo links cited in SESSION_STATE/SECURITY/README (resolved if found live OR in archive). Add unit test pinning archived-SCOPE-satisfies. Commit.

### Task 0.7 — UPGRADE `check_repo_map_complete` (count-drift + reverse path; flip WARN→FAIL)
- [ ] Failing test: a fabricated count mismatch ⇒ FAIL.
- [ ] Modify `:1237` to (a) compare documented per-dir counts vs live `os.scandir` (use `dev/trace_repo.py`'s inventory), (b) reverse-assert every concrete path cited in REPO_MAP exists, (c) status `fail` on drift/missing. **Note:** ships RED until Phase 5 regenerates REPO_MAP — acceptable (it's a foundational guard; Phase 5 turns it green). Commit.

### Task 0.8 — `save.ps1` file-count gate
- [ ] Add ~6 lines before `git add -A`: `$staged = git status --porcelain; if (($staged | Measure-Object).Count -gt 200 -and $args -notcontains '--yes') { print list; exit 1 }`. Manual test with a dummy. Commit.

**Phase 0 acceptance:** `python scripts/lint_rules.py` runs all new checks; the RED ones are exactly the expected (truth_record_budget, commercial_orphans, commercial_terms, retired_terms, triad_plan_consistency, dev_doc_sprawl WARN, repo_map_complete). New tests green. **No production code path touched** — pure lint additions.

---

## PHASE 1 — Slim the bootstrap (foundational) → turns truth_record_budget / frozen_stats / retired_terms GREEN

**Recovers ~140k of the ~200k per-session bootstrap tokens.** History preserved behind pointers; the marathon's authoritative ledger lives in `content/manuscript/**/manifest.yaml`, so trimming narrative is safe.

### Task 1.1 — `scripts/rotate_truth_records.py` (the FIXER)
- [ ] TDD: write the rotator. Dry-run default, `--apply` to write. Splits `dev/SESSION_STATE.md` / `dev/IN_FLIGHT.md` on the `> **➤➤➤ <date>` entry marker; keeps the newest `KEEP_ENTRIES` (default 10) + the stable trailing sections live; appends the rest to `dev/archive/SESSION_STATE_archive_<oldest-kept-date>.md` (+ IN_FLIGHT equiv) with a one-line header. Uses `notes_io.atomic_write`. Tests pin: round-trips, keeps stable sections, never drops the live entry.
- [ ] Register in `FIXERS` (`:1493`) as the fixer for `truth_record_budget` (mirror the `_fix_freshness` pattern) so `python scripts/lint_rules.py --fix` self-heals. Commit.

### Task 1.2 — Rotate the two truth-records + fix dangling pointers
- [ ] Run `python scripts/rotate_truth_records.py --apply`. Verify SESSION_STATE/IN_FLIGHT now < soft budget, ≤2 `➤➤➤`. In the same edit fix: SESSION_STATE:155 dangling pointer → live `dev/PLAN_2026-05-29-roadmap.md` (created Phase 2); drop the `2026-06-07` deadline framing; set IN_FLIGHT `## ➤➤➤ ACTIVE` to the real Phase-D1b Esther state (replace the stale Kings block). Re-run lint → `truth_record_budget` GREEN. Commit + E:/F: backup.

### Task 1.3 — Slim `CLAUDE_PROJECT_RULES.md` to durable invariants
- [ ] Extract finished-arc NARRATIVE to `dev/archive/RULES_HISTORY.md`: the γ.4 patristic-voice composition + Five/Six-voice extensions (§1, lines ~180-300), the Δ-family/ω.35-B/χ-cluster per-instance tallies in §9, the §8.1 shipped-pin enumeration, the three dated "Operational guard" blocks (compress to one-line imperatives folded into the relevant §). Keep each as a ONE-LINE durable invariant (e.g. "Cyril remains plurality-leader — guarded by `test_cyril_remains_plurality_leader_at_arc_close`"). 
- [ ] **Resolve the 6 verified contradictions in the same pass:** deadline framing → "completeness over speed" principle sans date; PLAN-filename (§0 vs PLAYBOOK) → both name the one live plan; retired `_ship_*.py` rule → drop (0 files); v28a-NN build-tag → "saves are git commits now"; 7-min test budget → "stop at logical seams"; §0 RAM/env duplication → one-line pointer to PLAYBOOK §1.
- [ ] Re-frame §1 north-star + §10 "what this is NOT" to the free-public present tense (no strike-throughs). Target RULES ~25-30k tokens. Re-run lint → `frozen_stats` + `retired_terms` GREEN; add RULES to `truth_record_budget` WARN tier. Commit.

---

## PHASE 2 — Refresh the roadmap (foundational→high-value) → turns triad_plan_consistency GREEN

### Task 2.1 — `dev/PLAN_2026-05-29-roadmap.md` (replace, not add — `PLAN_SINGULAR` is a hard lint invariant)
- [ ] Write one fresh deadline-free roadmap reflecting REALITY: standalone Phases A-C **shipped** (`build_standalone.py`, 4 books); Phase D **in progress** via the D1b Patrologia vision lane (current critical path); then D2 distinctive sources; then remaining TIER-2 depth. Adopt the own-vers design §4 dependency model (standalone render NOT gated on full marathon — marathon + Phase-D re-ingest are parallel data-supply lanes). Encode dependency edges as `Depends:` lines (for `lint_plan` DEPENDS_VALID).
- [ ] `git mv` `PLAN_2026-05-24-end-scope.md` + `SCOPE_2026-05-14-parallel-bible.md` → `dev/archive/`. Update RULES §0, SESSION_PLAYBOOK §1/§7, `.claude/hooks/bootstrap-triad.ps1` to name the new plan identically. Re-run lint → `triad_plan_consistency` + `plan_coherence` GREEN. Commit.

---

## PHASE 3 — Archive sweep (high-value) → turns dev_doc_sprawl GREEN

> Blocker handled in Phase 0 Task 0.6 (cross-ref is now archive-aware). Pure `git mv`, no logic.

### Task 3.1 — sweep ~75 dated finished docs
- [ ] `git mv` into `dev/archive/{audits,calibration,proposals,scope,session-ends}/`: all `AUDIT_*` (except the newest deep audit if still referenced), `CALIBRATION_*`, `PILOT_*`, `PROPOSAL_*`, `SESSION_END_*`, `CODESPELL/TRUFFLEHOG_FINDINGS_*`, the `SCOPE_*` addenda, and `HANDOFF_README_v7.md`. KEEP live: RULES, SESSION_STATE, IN_FLIGHT, active PLAN, MATRIX_MAP, REPO_MAP, SESSION_PLAYBOOK, CHANGELOG, SCHEMAS, SECURITY, PERF_BUDGETS, the build/installer scripts, `trace_*`/`lint_rules`.
- [ ] Add `dev/archive/README.md` index by family+date. Run FULL `lint_rules` → confirm no stranded reference; `dev_doc_sprawl` GREEN. Commit.

---

## PHASE 4 — Decommercialize (high-value, the big one — careful, protect the build)

> ~5,300 LOC removed. **Verified hazards** (do NOT blind-delete): `build_edition.py:2586` imports `press_kit.resolve_cover_path`; `archive_org.py:113-130` uses `press_kit` + `distribution` for *legit free* distribution; `tests/test_omega0_…::TestObsoleteModulesCarryBanner` *forbids* deletion; `auth.py`/`totp.py` are LIVE 2FA — KEEP. Exact route-table line numbers in `web.py` are read from the live file at execution time (audit cites ~507-535, 613-671, 760-840, 1001-1005 — verify before editing).

### Task 4.1 — flip the banner-pin test FIRST
- [ ] In `tests/test_omega0_free_public_pivot.py`: rename `TestObsoleteModulesCarryBanner` → `TestCommercialModulesRemoved`; flip assertions from "banner exists" to "these paths do NOT exist". Run → it now FAILS (modules still present) — that failure drives the deletion. Commit.

### Task 4.2 — relocate the one live dependency
- [ ] Move `press_kit.resolve_cover_path` → `scripts/core/covers.py`; update the `build_edition.py:2586` import; run `pytest tests/test_build*.py` + build a flagship EPUB → epubcheck 0/0, `epub_working/` diff empty. Commit.

### Task 4.3 — delete the fully-dead commercial code
- [ ] Delete `scripts/core/{license_key,license_state,sales}.py`, `scripts/api/{license,sales}.py`, `scripts/build_onix.py`, `scripts/print_cover.py`, `content/onix.py`, the `/exec` console (`templates/exec.py` + `scripts/api/exec.py` + its CONSOLES entry + route + `tests/test_exec_*.py`), and `tests/test_{license,sales}_*.py`. Remove their imports + every route-table entry in `web.py`, the `route_for_constant` mapping in `lint_rules.py` `check_cross_link_invariant` (138-158), and the `content/onix.py` mtime sentinel at `build_edition.py:1961`. Run FULL `pytest` + `check_routes.py` (half-removed route → FAIL catches mistakes). Commit.

### Task 4.4 — decommercialize (not delete) press_kit + distribution
- [ ] `distribution.py`: prune `DISTRIBUTION_CHANNELS` to `{archive_org, own_site}` (drop kdp/apple/google); remove the api/distribution mark/unmark UI routes (keep `mark_shipped` as a library call). `press_kit.py`: drop the print(KDP) cover variant + retail prose; keep `blurb_500`/`description` + web/social cover. Update `tests/test_distribution_*.py` + `tests/test_archive_org_*.py` to the trimmed set (the archive.org test guards the path still works). Commit.

### Task 4.5 — remove OPF commercial metadata + add the cleanliness test
- [ ] Delete the DOI/LCCN/`onix:codelist5` emission at `build_edition.py:1248-1255` (the `urn:yhwh:…` generator identifier at :1246 is sufficient). Add `tests/test_opf_clean.py`: build a sample EPUB, assert `content.opf` contains none of `TODO_DOI`, `TODO_LCCN`, `onix:codelist5`. Wire into the ship/epubcheck gate.
- [ ] **Prove zero EPUB-output change** for the surviving editions via regen + `git diff epub_working/` (empty) + epubcheck 0/0/0/0 + 9 editions byte-stable. Re-run lint → `commercial_orphans` + `commercial_terms` GREEN; `TestCommercialModulesRemoved` GREEN. Commit + E:/F: backup.

---

## PHASE 5 — Enforce the already-green gates (high-value)

### Task 5.1 — regenerate REPO_MAP + MATRIX_MAP (post-deletion)
- [ ] `python dev/trace_repo.py` → regenerate `REPO_MAP.md` with true counts; update `MATRIX_MAP.md` (drop commercial fields/routes). Re-run `repo_map_complete` (now FAIL-on-drift from Phase 0) → GREEN. Commit.

### Task 5.2 — wire mypy + fix the duplicate hook
- [ ] Add a `mypy` step to `.githooks/pre-commit` on its already-green scope (`scripts/core` + `build_edition.py`). Delete the dormant `dev/git-hooks/pre-commit`; rewrite `install_hooks.cmd` to just `git config core.hooksPath .githooks`. Fix `pyproject.toml` line-length comment (says 88/100; config is 120) + add `requires-python` aligned with README + mypy `python_version`. Fix `SECURITY.md:4` dead link → `dev/archive/`. Commit.

### Task 5.3 — restore a remote + CI (the single biggest pro-bar gap)
- [ ] Reconnect a private GitHub/Codeberg remote. Add `.github/workflows/ci.yml` running `python scripts/ci.py` (ruff-check, lint_rules, mypy, pytest, coverage floor) on push/PR + a macOS job for the dmg build. Pin `coverage` in `requirements-dev.txt` so the floor never silently skips. (This also unblocks the macOS notarized build path.) Commit + push.

---

## PHASE 6 — Polish (lowest priority; do last)

- [ ] **SessionEnd hygiene hook:** `dev/cc-hooks/session-end-hygiene.ps1` runs `python scripts/cleanup.py --apply --pycache-only` + `python scripts/lint_rules.py` and prints WARN/FAIL before save (advisory). Register via `install_cc_hooks.ps1` (Start + End, idempotent).
- [ ] Sweep the 56 stale `.sonar` dirs (`Get-ChildItem -Recurse -Directory -Force -Filter .sonar | Remove-Item -Recurse -Force`) + root `*.log` scratch; remove the `.gitignore:72-75` sonar lines.
- [x] `docs/superpowers/INDEX.md` + `Status:` headers on the 23 plans/16 specs + `check_superpowers_coherence` (mint-6: backfilled, _ENFORCE flag True).
- [ ] **Optional / only if warranted:** lift the last inline `do_GET/do_POST` route bodies in `web.py` into the pure-`api_*`+table pattern; `changelog_size` WARN tier; a TypedDict view at the `notes_io` boundary (only if tuple-index churn bites).

---

## NOT doing (verified, on the merits — not schedule)

- **No language rewrite** (Rust/Go/TS/C#) — Python is the strongest fit; rewrite = pure regression risk + discards maintainer fluency for zero functional gain.
- **No splitting web.py / build_edition.py / extractors for size** — large FILES of small cohesive functions, not god-modules; splitting risks the build for no clarity gain.
- **No DB / no replacing the data-as-tuples store** — deliberate, correct, dependency-free, git-diffable; a TypedDict view is the only optional refinement.
- **Do NOT delete `auth.py`/`totp.py`/`api/auth`/`api/audit`** — LIVE 2FA admin gate (`web.py:1404-1441`).
- **Do NOT delete `press_kit`/`distribution` outright** — load-bearing for the build + archive.org free distribution; trim commercial halves only.
- **Do NOT auto-rotate CHANGELOG** — `check_untracked_phases` substring-searches the live file; WARN-only, manual month-roll with a coupled check update.
- **Do NOT set up paid Apple/Sparkle codesigning now** — frame the scripts as "future"; the real infra gap is the remote+CI.

---

## Self-review

- **Coverage:** every audit finding maps to a task (guards → Phase 0; SS/IF/RULES bloat → Phase 1; roadmap → Phase 2; doc sprawl → Phase 3; commercial code + OPF → Phase 4; REPO_MAP/mypy/hooks/CI/CONTRIBUTING/pyproject → Phase 5; .sonar/SessionEnd/superpowers-index/optional refactors → Phase 6).
- **Dependencies honored:** guards before cleanup; archive-aware cross-ref (0.6) before the sweep (3); banner-flip (4.1) + cover relocation (4.2) before deletion (4.3); REPO_MAP regen (5.1) after deletions.
- **Marathon protected** in every phase (constraint 2).

## Execution handoff

Recommended: **subagent-driven-development** — fresh subagent per task, two-stage review between tasks, byte-compat + full-pytest gates at each commit. Phase 0 is the safe, high-leverage start (additive lint only). Each phase's exact edits are produced against the live files at execution time (no fabricated line numbers).
