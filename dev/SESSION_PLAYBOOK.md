# Session Playbook — work this project + finish every session CLEAN

**Purpose:** the **lifecycle-ordered** checklist a Claude session follows so the repo stays professionally sound and **passes every check at session-end**. Companion to `CLAUDE_PROJECT_RULES.md` (the *topic*-organized rules, §0–§15) — this is the *order-of-operations* + the consolidated **verification gates** and **gotchas** in one place. On any conflict of detail, RULES §N is the authority (cross-referenced below). A one-off user instruction beats both for that turn.

---

## 0. The contract (what "done + clean" means)

Every session that touched code/content/docs ends with **all of these green** and the tree **consistent** (source ↔ build agree):

`lint_rules 16/0/0` · `ruff format --check` clean · `ebible verify` errors=0 / 24,015 paired · `validate_taxonomy` 100% (67,713) · `trace_matrix` 0 unresolved · `validate_schemas` 6/6 · targeted tests for every touched module green · (if you touched the build/corpus) one+ edition built → `epubcheck` 0/0/0/0.

Then `SESSION_STATE.md` + `CHANGELOG.md` are updated **together**, `IN_FLIGHT.md` reflects reality, and **you only commit when the user says "save"** ("continue"/"push" ≠ save — RULES §4).

---

## 1. SESSION START — orient, in this order

1. **Read the bootstrap triad** (RULES §0): `dev/CLAUDE_PROJECT_RULES.md` → `dev/SESSION_STATE.md` → `dev/PLAN_2026-05-21.md` (incl. its **§4.1 forward refresh**). Then `dev/IN_FLIGHT.md` — check the `<!-- TRACKER-STATE: idle|active -->` marker.
2. **Check auto-memory** — the `MEMORY.md` index (durable user prefs, gotchas, decisions).
3. **"Where does X live / how does data flow?"** → read `dev/MATRIX_MAP.md` + `dev/REPO_MAP.md` **first**; never grep blind (RULES §0).
4. **Set up the environment (§2) before running anything.**

---

## 2. ENVIRONMENT — Windows; get this right or everything fails

| Thing | Value / rule |
|---|---|
| Python | `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe` — **never** bare `python`/`python3` (broken Store stub). |
| UTF-8 | Always `$env:PYTHONUTF8="1"` (else ~72 tests fail with cp1252 errors). |
| Shell | PowerShell. **`save.ps1` runs via PowerShell only**, never the Bash tool (spaced path + `>`/`→` glyphs become redirects → stray files). |
| epubcheck | Java 8 at `C:\Program Files\Java\jre1.8.0_491\bin` (**off PATH** — prepend it); jar bundled in the PyPI `epubcheck` site-package. **One JVM at a time** (concurrent JVMs crash HotSpot → delete any `hs_err_pid*.log`/`replay_pid*.log` before continuing). |
| Acquired sources | `_acquire/` is **one level above** the repo (gitignored). |
| Throwaway probes | live in the **repo parent** (outside git); delete when done. |

---

## 3. ARCHITECTURE — so changes land in the right place (RULES §1, MATRIX_MAP)

- **Source of truth = `content/`**: `notes/<book>.py` (the corpus), `translations/<id>/*.py`, and the `*.yaml` config (editions / kinds / categories / canons / books).
- **Pipeline:** `content/notes` → `scripts/inject.py` (into base HTML) → `epub_working/` (built HTML with markers + asides) → `scripts/build_edition.py` (copy → filter by canon + enabled-kinds → zip) → EPUB.
- **⚠ `inject` is ADDITIVE** — it injects *missing* source notes; it does **NOT** prune asides whose source note was deleted. To drop notes from the build after deleting them from source, prefer the **SURGICAL** method (below); the **bare-base regen** (`git checkout <base> -- epub_working/` → `inject --all-books` → `generate_verse_popups` → `resync_marker_glyphs`) **is LOSSY** and should be avoided post-translations.
  - **⚠⚠ WHY bare-base regen is LOSSY (proven 2026-05-24 phi/jam):** `generate_verse_popups` uses `harvest_existing_langs` to PRESERVE popup content the resolver can't rebuild (e.g. cross-book deutero mappings). Restoring the bare base wipes that content → harvest finds nothing → it is **permanently lost** (proven: a from-base regen dropped `vnote-paz-1-30`'s Douay+Vulgate). It also re-qualifies ~88 unrelated xref hrefs. So a full from-base regen does NOT byte-reproduce HEAD.
  - **✅ SURGICAL method (lossless, isolated) — use this to remove orphaned notes:** from HEAD's `epub_working`, regex-remove the orphaned markers (`<a class="note-ref note-<kind>" …>…</a>`) AND asides (`<aside class="note note-<kind>" …>…</aside>`) from the affected book's split file(s) (find via `config.books_by_code()[code]['files']`), then `inject --book <code>` to add the replacement notes. No `generate_verse_popups` needed (notes don't affect verse-popups). Verify CONTENT-level by **aside-by-id diff** (HEAD vs working), never raw line-diff; only the changed book's split file(s) should differ. ⚠ split files are **shared** between books, so confirm the removed `<kind>` only belongs to the target book before a blanket regex (e.g. only phi/jam carry `lang-hebrew` among NT books).
- **`ebible verify` checks marker↔aside *pairing*, NOT source-correspondence** — so a source/build mismatch (e.g. orphaned asides) passes verify **silently**. Keep source ↔ build consistent yourself.
- **Matrix (editions × kinds):** every per-edition control flows through **one resolver** that `matrix == build == config` (`tests/test_enabled_kinds_unified.py`).
- **Corpus scale:** 67,713 notes · 71 kinds · 15 categories · 87 books · 11 editions.

---

## 4. WORKING — conventions (RULES §6/§7/§8/§9 for detail)

- **TDD** — failing test first (RED), then fix (GREEN). [`superpowers:test-driven-development`]
- **Byte-compat invariant** — for any regen/refactor, PROVE zero unintended change: regen + `git diff` shows **only** the intended change (pure deletions/additions, no reformat churn). This has caught real bugs.
- **Don't break the tree** — first programming project, hard deadline. Verify before claiming done; no `--no-verify`/shortcut bypasses.
- **`tests/test_scripts.py` is runnable again** — **976 tests, ~2.9 min, green** (2026-05-24). Both blockers fixed: D.hang (9 socket tests → `ThreadingHTTPServer` + `test_ops` mocks `api_preflight`) and **D.slow** (a session-autouse conftest fixture, `_stub_exports_epubcheck`, stubs the real epubcheck/Java run over the populated `exports/` dir — minutes per call — while leaving `TestEpubcheckWrapper`'s tmp-dir calls real). The old "NEVER run the full test_scripts.py" rule is **retired** — a full run is a normal ~3 min now. Targeted node-ids / `-k` are still faster for single-test iteration (RAM pressure: one file at a time). ⚠ `test_web_filesplit.py` + `test_matrix_psi35.py` are still ~23 min (live socket/build smokes not yet given the same treatment) — prefer node-ids there.
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
| Invariant linter | `& $py scripts\lint_rules.py` | **16 pass / 0 warn / 0 fail** |
| Format | `& $py -m ruff format --check .` | all files formatted |
| Matrix integrity | `& $py dev\trace_matrix.py` | 0 unresolved refs (11 editions) |
| Repo-map complete | `& $py dev\trace_repo.py` | complete |
| Taxonomy | `& $py scripts\validate_taxonomy.py` | 67,713/67,713 (100%) |
| Schemas | `& $py scripts\validate_schemas.py` | 6/6 ok |
| Pairing | `& $py -m scripts.ebible verify` | errors=0 / 24,015 paired |
| Matrix==build==config | `& $py -m pytest tests\test_enabled_kinds_unified.py -q` | pass |
| Touched modules | `& $py -m pytest tests\<file>.py -q` (per module) | pass |
| Build cert (build/corpus touched) | build edition(s) + epubcheck (Java 8 on PATH, one JVM) | epubcheck **0/0/0/0** |

**Pre-commit hook** runs `ruff format --check .` + `lint_rules.py` — both must pass or the commit is **blocked**. It does **NOT** run the test suite — run targeted tests yourself.

Build one edition fast: `& $py scripts\build_edition.py <edition> --force --output-dir <tmp>` (~3 min), then `& $py scripts\epubcheck.py --editions-dir <tmp>` with Java 8 prepended to `$env:PATH` (~1 min). Pick the hardest case (`catholic-study` = canon-spliced + popup-heavy).

---

## 6. SESSION END — finish clean, in this order (RULES §11/§12)

1. **§12 4-point pre-summary audit:** (a) test-count reconcile (≥ baseline **7,064** collected; itemize any intentional removals); (b) phase-mention scan (any new Greek-letter phase tag in code must appear in `CHANGELOG.md`); (c) `IN_FLIGHT.md` `TRACKER-STATE` marker correct; (d) linter ack (`lint_rules` 16/0/0).
2. **Update `SESSION_STATE.md` AND `CHANGELOG.md` together** — their mtimes must be within ~6h or the freshness check warns. Update the `IN_FLIGHT.md` banner + marker. (Don't pin durable phase tags onto SESSION_STATE/IN_FLIGHT — they roll.)
3. **ruff-format** every generated/regenerated file.
4. **Run the §5 gates** — confirm green. Prove byte-compat for any regen.
5. **Only if the user said "save":** `& ".\save.ps1" -Message "<concise; no > < → glyphs>"` (PowerShell; does `git add -A` + commit; pre-commit hook runs; **push is disabled — no remote since 2026-05-12**). Otherwise leave it uncommitted on disk. **"continue" ≠ "save".**

---

## 7. CURRENT OPEN WORK (2026-05-24 — see `dev/PLAN_2026-05-21.md` §4.1 + `dev/AUDIT_2026-05-23-DEEP.md`)

- **Deadline: 2026-06-07.**
- **Critical path:** the Geʽez/Amharic Kings/Samuel manuscript marathon (Track B) — paced, **script-based** (`run_manuscript_*_at_scale.py`, not agents), OOM-aware.
- **Audit QUEUED backlog (PLAN §4.1):** P0 ★BUGCLUSTER (code-fix `c41e6d2` + **data-cleanup DONE 2026-05-24** — see below) · **P0 C1.chap >50-ch backfill** (re-run hebrew/greek at-scale for Psalms 51-150 / Isaiah / Jeremiah — runner-key-50-default, now code-fixed; NEXT) · P1 security G1 `file://` SSRF + G2 preview-XSS (open; CC0→all-rights-reserved done) · P2 wire the 4 dead audit-checks (`audit_dead_code/caches/deps/types`) into preflight.
- **✅ phi/jam DATA-cleanup — DONE 2026-05-24 (committed).** 165 spurious `lang-hebrew` stripped (AST-span, 1,815 pure deletions) + 270 `lang-greek` generated/promoted (phi 156, jam 114; `--min-confidence 0.65`); corpus 67,713→67,818. `epub_working` updated by the SURGICAL method (§3), NOT the lossy bare-base regen. TDD guard `TestNTBookLanguageInvariant`. All gates green. **Resolved findings (for the record):** the promote "didn't insert" symptom was the `book=php` code-drift (fixed by `c41e6d2` — 270/270 land with canonical codes); the "Hebrew-re-add" was `run_greek_at_scale.write_queue` merge-preserving stale non-greek candidates (mitigated by clearing the 19 stale `phi/jam/php/jas` candidate files first).

---

*Keep this file current alongside CLAUDE_PROJECT_RULES.md. If a gate or gotcha changes, update §5/§2/§4 here so the next session inherits the truth.*
