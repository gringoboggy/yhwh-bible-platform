# Session Playbook — work this project + finish every session CLEAN

**Purpose:** the **lifecycle-ordered** checklist a Claude session follows so the repo stays professionally sound and **passes every check at session-end**. Companion to `CLAUDE_PROJECT_RULES.md` (the *topic*-organized rules, §0–§15) — this is the *order-of-operations* + the consolidated **verification gates** and **gotchas** in one place. On any conflict of detail, RULES §N is the authority (cross-referenced below). A one-off user instruction beats both for that turn.

---

## 0. The contract (what "done + clean" means)

Every session that touched code/content/docs ends with **all of these green** and the tree **consistent** (source ↔ build agree):

`lint_rules` 0 warn / 0 fail (all checks pass) · `ruff format --check` clean · `ebible verify` errors=0 (all asides paired) · `validate_taxonomy` 100% (live source-corpus count in `dev/SESSION_STATE.md`; shipped = per-edition filter) · `trace_matrix` 0 unresolved · `validate_schemas` 6/6 · targeted tests for every touched module green · (if you touched the build/corpus) one+ edition built → `epubcheck` 0/0/0/0.

Then `SESSION_STATE.md` + `CHANGELOG.md` are updated **together** and `IN_FLIGHT.md` reflects reality. **Save cadence (RULES §4, 2026-06-17 crash-safe):** **local-commit** micro-edits freely; **save** (push both remotes) autonomously after every coherent slice — **without asking, without waiting on input** (Windows: `save-all.ps1`; Mac: `save_mac.sh` — §6.6). **Never pause for confirmation. Never end with unpushed commits.** **And never tell the user a session is "done / safe to stop / safe to /clear" — or that work is "committed" or "backed up" — without first running `git log -1` + `git status -b` and reporting the TRUE state (§6.7).** Unpushed commits = other lane cannot see work; uncommitted work = crash-loss risk.

---

## 1. SESSION START — orient, in this order

1. **Read the bootstrap triad** (RULES §0): `dev/CLAUDE_PROJECT_RULES.md` → `dev/SESSION_STATE.md` → `dev/PLAN_2026-05-29-roadmap.md`. Then `dev/IN_FLIGHT.md` — check the `<!-- TRACKER-STATE: idle|active -->` marker. SessionStart hooks: `dev/cc-hooks/bootstrap-triad.{ps1,sh}` (installed per-box to repo-parent `.claude/hooks/` — see RULES §0). Cross-lane sync is **seam-based** (no persistent radars — the runaway-radar machinery was removed 2026-06-20): the save scripts run `lane_ping --before-push` and pull-rebase when behind + clean, so the user never says "pull" (RULES §4). Optionally run `py -3 scripts/lane_ping.py` once at session start to see whether the other lane pushed.

2. **Check auto-memory** — the `MEMORY.md` index (durable user prefs, gotchas, decisions).
3. **"Where does X live / how does data flow?"** → read `dev/MATRIX_MAP.md` + `dev/REPO_MAP.md` **first**; never grep blind (RULES §0).
4. **Free RAM before heavy work — AGGRESSIVE, every session (16 GB box; bootstrap-mandated, RULES §0).** End **every** process not needed for Windows / the network / Claude / Claude's toolchain — not just leaked runtimes. **PROTECT** (never kill — the safety boundary): Windows core (`svchost`/`dwm`/`Registry`/`Memory Compression`/`Secure System`/`csrss`/`lsass`/…), the session tree (`claude`/`pwsh`/`powershell`/`WindowsTerminal`/`explorer` — map it via a `$PID` parent-chain walk so it's never a target), `node` (MCP + runtime), `MsMpEng`+AV (**stays ON**), the network stack. **KILL** (recoverable): 0-window background browsers + `msedgewebview2`, cloud-sync (`iCloud*`/`OneDrive`/`Dropbox`), vendor updaters (Intel DSA/`esrv`), optional MS apps (`M365Copilot`/`Widgets`/`AppActions`/Cross-Device), `SystemSettings`, the respawning shell hosts (`SearchHost`/`StartMenuExperienceHost`/`ShellExperienceHost`), and any **leaked** `python`/`java` orphaned by a prior crash. Report reclaimed RAM. Also clear stale temp/build artifacts (repo-parent `_*` probe + `_*epubcheck` dirs, orphaned PyInstaller `_MEI*`, `hs_err_pid*`/`replay_pid*` JVM logs). Pairs with the §2 heavy-trio-sequential rule + the §6.5 session-end junk-sweep.
5. **Set up the environment (§2) before running anything.**

---

## 2. ENVIRONMENT — Windows; get this right or everything fails

| Thing | Value / rule |
|---|---|
| Python | `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` — **never** bare `python`/`python3` (broken Store stub). |
| UTF-8 | Always `$env:PYTHONUTF8="1"` (else ~72 tests fail with cp1252 errors). |
| Shell | PowerShell. **`save-all.ps1` / `save.ps1` run via PowerShell only**, never the Bash tool (spaced path + `>`/`→` glyphs become redirects → stray files). `save.ps1` is leg-1 only — milestone saves use `save-all.ps1`. |
| epubcheck | `java` IS on PATH on this box (Oracle JRE 1.8.0_491 via the `java8path` shim; Temurin was uninstalled in the 2026-06-10 env curation — and the 5.1.0 jar runs CLEAN under Java 8: full 26 MB EPUB 0/0/0/0 proven 2026-06-10). **Always pass `--jar` the PyPI site-package jar** (auto-discovery hits a broken wrapper). **One JVM at a time** (concurrent JVMs crash HotSpot → delete any `hs_err_pid*.log`/`replay_pid*.log` before continuing). |
| RAM (16 GB) | Run the **heavy trio — `inject --all-books` / a full `build_edition` / the epubcheck JVM — ONE at a time, never in parallel** (nor alongside a broad pytest sweep), or risk MemoryError / HotSpot crash. Background a long one and wait for it before starting the next. |
| Acquired sources | `_acquire/` is **one level above** the repo (gitignored). |
| Throwaway probes | live in the **repo parent** (outside git); delete when done. |

> **🖥️ Mac lane (2nd machine):** the table above is the **Windows N95** lane. On the **Mac** (2017 iMac) the toolchain differs — Python = `.venv/bin/python` (uv-managed 3.14; **not** `python3` = system 3.9), tests via `.venv/bin/python -m pytest` (+ `export TMPDIR=/Volumes/MacHD2/…` for OCR tests run under the Bash tool), **milestone save = `bash dev/save_mac.sh -m "..."`** (local commit + `lane_ping --before-push` + push `origin` + `github`; no E:/F: bundles — Windows-only), Tesseract via conda-forge. Local commits during work = plain `git commit`. See memory `reference_mac_dev_env`.

---

## 3. ARCHITECTURE — so changes land in the right place (RULES §1, MATRIX_MAP)

- **Source of truth = `content/`**: `notes/<book>.py` (the corpus), `translations/<id>/*.py`, and the `*.yaml` config (editions / kinds / categories / canons / books).
- **Pipeline:** `content/notes` → `scripts/inject.py` (into base HTML) → `epub_working/` (built HTML with markers + asides) → `scripts/build_edition.py` (copy → filter by canon + enabled-kinds → zip) → EPUB.
- **⚠ `inject` is ADDITIVE** — it injects *missing* source notes; it does **NOT** prune asides whose source note was deleted. To drop notes from the build after deleting them from source, prefer the **SURGICAL** method (below); the **bare-base regen** (`git checkout <base> -- epub_working/` → `inject --all-books` → `generate_verse_popups` → `resync_marker_glyphs`) **is LOSSY** and should be avoided post-translations.
  - **⚠⚠ WHY bare-base regen is LOSSY (proven 2026-05-24 phi/jam):** `generate_verse_popups` uses `harvest_existing_langs` to PRESERVE popup content the resolver can't rebuild (e.g. cross-book deutero mappings). Restoring the bare base wipes that content → harvest finds nothing → it is **permanently lost** (proven: a from-base regen dropped `vnote-paz-1-30`'s Douay+Vulgate). It also re-qualifies ~88 unrelated xref hrefs. So a full from-base regen does NOT byte-reproduce HEAD.
  - **✅ SURGICAL method (lossless, isolated) — use this to remove orphaned notes:** from HEAD's `epub_working`, regex-remove the orphaned markers (`<a class="note-ref note-<kind>" …>…</a>`) AND asides (`<aside class="note note-<kind>" …>…</aside>`) from the affected book's split file(s) (find via `config.books_by_code()[code]['files']`), then `inject --book <code>` to add the replacement notes. No `generate_verse_popups` needed (notes don't affect verse-popups). Verify CONTENT-level by **aside-by-id diff** (HEAD vs working), never raw line-diff; only the changed book's split file(s) should differ. ⚠ split files are **shared** between books, so confirm the removed `<kind>` only belongs to the target book before a blanket regex (e.g. only phi/jam carry `lang-hebrew` among NT books).
- **`ebible verify` checks marker↔aside *pairing*, NOT source-correspondence** — so a source/build mismatch (e.g. orphaned asides) passes verify **silently**. Keep source ↔ build consistent yourself.
- **Matrix (editions × kinds):** every per-edition control flows through **one resolver** that `matrix == build == config` (`tests/test_enabled_kinds_unified.py`).
- **Corpus scale:** live figures (source notes · kinds · categories) in `dev/SESSION_STATE.md` (do not hard-code here — they rot) · 87 books · 6 editions.

---

## 4. WORKING — conventions (RULES §6/§7/§8/§9 for detail)

- **TDD** — failing test first (RED), then fix (GREEN). [`superpowers:test-driven-development`]
- **Byte-compat invariant** — for any regen/refactor, PROVE zero unintended change: regen + `git diff` shows **only** the intended change (pure deletions/additions, no reformat churn). This has caught real bugs.
- **Don't break the tree** — first programming project; correctness is the bar. Verify before claiming done; no `--no-verify`/shortcut bypasses.
- **`tests/test_scripts.py` is runnable again** — **976 tests, ~2.9 min, green** (2026-05-24). Both blockers fixed: D.hang (9 socket tests → `ThreadingHTTPServer` + `test_ops` mocks `api_preflight`) and **D.slow** (a session-autouse conftest fixture, `_stub_exports_epubcheck`, stubs the real epubcheck/Java run over the populated `exports/` dir — minutes per call — while leaving `TestEpubcheckWrapper`'s tmp-dir calls real). The old "NEVER run the full test_scripts.py" rule is **retired** — a full run is a normal ~3 min now. `test_web_filesplit.py` (88 tests, **~45 s**) and `test_matrix_psi35.py` (39, **~87 s**) — the session-autouse `_stub_exports_epubcheck` conftest fixture removed the worst cost (the `api_preflight()`→epubcheck-over-`exports/` path; test_web_filesplit alone made 15 such calls), but they've since grown to the **2 slowest non-build files** (re-measured 2026-05-31; the "~11 s/~12 s" here was stale, as was the "23 min" myth elsewhere). Both are now `slow`-tagged (mint-7 E2) → `pytest -m "not slow"` skips them; the genuinely-slow lane is real edition builds (`test_byte_stability_gate.py` ~205 s). Targeted node-ids / `-k` are still faster for single-test iteration (RAM pressure: one file at a time).
- **`subprocess.run` → always `stdin=subprocess.DEVNULL`** on Windows (WinError 6).
- **ruff-format before save** every file you generated/regenerated — **especially `content/translations/<id>/` stores** (recurs on every ingest) — or the pre-commit hook blocks (RULES §4).
- **Grep is unreliable for Greek** (Unicode NFC mismatch) — verify Greek by Read.
- **`editions.yaml` shows git-modified mid-test** from a benign CRLF flip — trust `git diff`, not `git status`.
- **Book codes** — canonical 3-letter stems: `phi` jam `joe` eze `nah` jhn. Legacy aliases (`php`/`jas`/`jol`/`ezk`/`nam`/`joh`/`mar`) are normalized by `_normalize_book_code` in *some* paths but compared **raw** in others (the ★BUGCLUSTER). When adding book-code logic, **use canonical or normalize first**, and add a regression test that asserts on the canonical code.
- **Agent concurrency cap** (memory): heavy (>100k tok) ≤1 · medium (30–100k) ≤2 · light ≤4; drain before re-dispatch.

---

## 5. VERIFICATION GATES — what "passing code checks" *is* (run from repo root)

Prelude: `$env:PYTHONUTF8="1"; $py="C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe"`

| Gate | Command | Green = |
|---|---|---|
| Invariant linter | `& $py scripts\lint_rules.py` | **0 warn / 0 fail** (all checks pass; count grows as checks are added — assert the invariant, not a fixed N) |
| Format | `& $py -m ruff format --check .` | all files formatted |
| Matrix integrity | `& $py dev\trace_matrix.py` | 0 unresolved refs (6 editions) |
| Repo-map complete | `& $py dev\trace_repo.py` | complete |
| Taxonomy | `& $py scripts\validate_taxonomy.py` | 100% (every source-note coord valid; live total in SESSION_STATE) |
| Schemas | `& $py scripts\validate_schemas.py` | 6/6 ok |
| Pairing | `& $py -m scripts.ebible verify` | errors=0 (all asides paired) |
| Matrix==build==config | `& $py -m pytest tests\test_enabled_kinds_unified.py -q` | pass |
| Touched modules | `& $py -m pytest tests\<file>.py -q` (per module) | pass |
| Build cert (build/corpus touched) | build edition(s) + epubcheck (PATH `java` + `--jar`, one JVM) | epubcheck **0/0/0/0** |

**Pre-commit hook** runs `ruff format --check .` + `lint_rules.py` — both must pass or the commit is **blocked**. It does **NOT** run the test suite — run targeted tests yourself.

Build one edition fast: `& $py scripts\build_edition.py <edition> --force --output-dir <tmp>` (~3 min), then `& $py scripts\epubcheck.py --editions-dir <tmp>` (PATH `java` works as-is; always `--jar` the site-package jar; ~1 min). Pick the hardest case (`catholic-study` = canon-spliced + popup-heavy).

**⚠ After a CORPUS change, `inject` BEFORE you build.** `build_edition.py` zips the pre-baked `epub_working/` base; promoting notes alone does NOT put them in any build. Run `inject --all-books` first (RULES §9 step 8 — the bake-and-prove gate). **Tell-tale: if the rebuilt EPUB is the same size as before your change, you forgot to inject** — you just re-validated the old corpus.

---

## 6. SESSION END — finish clean, in this order (RULES §11/§12)

1. **§12 pre-summary audit — the RULES §12 5-point checklist:** test-count reconcile (the count matches what the summary will claim — do NOT hard-code a baseline; it rots) · phase-mention scan (any new Greek-letter phase tag in code appears in `CHANGELOG.md`) · `IN_FLIGHT.md` `TRACKER-STATE` marker correct · linter ack (`lint_rules` 0 warn / 0 fail) · **commit/backup git-truth** (`git log -1` + `git status -b`; see §6.7).
2. **Update `SESSION_STATE.md` AND `CHANGELOG.md` together** — their mtimes must be within ~6h or the freshness check warns. Update the `IN_FLIGHT.md` banner + marker. (Don't pin durable phase tags onto SESSION_STATE/IN_FLIGHT — they roll.)
3. **ruff-format** every generated/regenerated file.
4. **Run the §5 gates** — confirm green. Prove byte-compat for any regen.
5. **Delete ALL junk + temp before committing.** The save scripts (`save-all.ps1`, `save.ps1`, `dev/save_mac.sh`) all stage via `git add -A`, so any stray file gets swept into the commit. Remove: repo-parent throwaway probes (`_*.py`, `_probe_*`, `_vg_*`) + `_*epubcheck`/build temp dirs, orphaned PyInstaller `_MEI*` dirs, `hs_err_pid*`/`replay_pid*` JVM crash logs, and any unneeded `.bak` from `ensure_backup`. Then **`git status` must show ONLY the intended changes** — no stray/junk files. (Also frees RAM/disk on the 16 GB box — see §1.4.)
   **⚠ GIT-CLONE / WORK-DIR DELETION GATE (user-directed 2026-06-11, "that should always be a thing" — STANDING, both lanes):** before deleting ANY repo clone or work directory, PROVE it holds nothing unique: (a) `git -C <dir> status --porcelain` → must be empty (no dirty/untracked work); (b) its HEAD must be contained in the surviving copy's history — `git -C <live> merge-base --is-ancestor <stale-HEAD> HEAD` exits 0; (c) check for local-only branches/stashes (`git -C <dir> branch -vv`, `git -C <dir> stash list`) if the clone ever did real work. Only an all-clear on every check licenses the delete; any miss ⇒ surface to the user instead. (First applied: the 3 stale `yhwh-website` publish clones, 2026-06-11.)
6. **Save (RULES §4 crash-safe cadence):**
   - **During work:** local-commit micro-edits — Windows: `& ".\save.ps1" -Message "…"` (PowerShell only; does **NOT** push). Mac: `git add -A` + `git commit -m "…"`. Commit freely; do not wait for permission.
   - **After each coherent slice (autonomous — no asking):** Windows: `& ".\save-all.ps1" -Message "…"` (`-Label`, `-Yes`, `-DryRun` as needed) — five legs when E:/F: mounted. Mac: `bash dev/save_mac.sh -m "…"` (commit if dirty + `lane_ping --before-push` + push both remotes). Triggers: per the **RULES §4 list** (gate green · truth-record edit · before risky/long jobs · before wrap · ahead of origin). **Auto-rebase if BEHIND.**
   - **`save.ps1` alone is not a complete save** — never report "backed up" until push legs landed (`git status -b` ahead/behind = 0).
7. **⚠ SAVE TRUTH GATE — before ANY "done / safe to stop / safe to /clear / saved / backed up" statement (RULES §12 audit point 5).** Run `git log -1 --oneline` + `git status -b`. Report the ACTUAL state. Uncommitted = **WARNING**. Committed but unpushed = **WARNING** — other lane cannot see work. Full save = remotes in sync; Windows bundle on E:/F: when mounted.

---

## 7. CURRENT OPEN WORK (see `dev/PLAN_2026-05-29-roadmap.md` for the full forward sequence)

- **No deadline — quality / completeness over speed** (RULES §2; memory `project_deadline`).
- **Critical path:** the **mint-cleanup arc (Phases 0–6) and the deep-audit arc are COMPLETE.** Current = **Phase D1b** (PO Esther own-vers vision lane, paused ~p35) → finish Esther → other Patrologia books (1ch/2ch/ezr/neh/job) → (TIER-3, last) the two standalone Geʽez/Amharic Bibles; plus the LANE T correctness/depth backlog (★bookcode-canonicalization tail · >50-ch at-scale backfill · security · Phase-E · code-debt). See `dev/PLAN_2026-05-29-roadmap.md`.
- **Critical data lanes (own-vers §4 — parallel; neither blocks the standalone render):** the Kings/Samuel manuscript marathon + the Phase-D own-versification re-ingest. Method RATIFIED = the **AGENT** vision path (paid script-API out of scope; the old `run_manuscript_*_at_scale.py` script-path is retired), MAX 1 heavy agent, ≤1568px crops, per-unit commits.
- **Backlog (corpus-correctness first):** the ★BUGCLUSTER book-code canonicalization + the >50-chapter at-scale backfill; then security / coverage / no-KJV-popups / Phase-E / code-debt per the roadmap's LANE T. Verify current state before re-scoping (several may be partly done since the old plan).

---

*Keep this file current alongside CLAUDE_PROJECT_RULES.md. If a gate or gotcha changes, update §5/§2/§4 here so the next session inherits the truth.*
