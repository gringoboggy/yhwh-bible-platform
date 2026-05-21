# Audit 2026-05-21 — "can anything run smoother?" (DB · production · safety · tools)

Requested by the user (deadline **2026-06-07**, free CC0 EPUB-builder demo). Whole-system review
after the matrix cleanup + reverse-engineering the build pipeline. Priorities for the 18-day window:
**P0** = blocks the deliverable · **P1** = high value, low risk · **P2** = nice-to-have / defer past deadline.

## Bottom line
The system is **fundamentally sound**: content is done (52,973 notes / 87 books), the data layer is a
proper sqlite+FTS index over `.py` source, the safety net is strong (3,374+ tests), and the app runs.
**One thing blocks the deliverable** — a lost build artifact (the base scripture HTML), recoverable
from the 2026-05-05 handoff. Almost every other "smoother" win is **purging pre-pivot commercial
cruft**, not changing architecture. This is a finish-and-polish job, not a rebuild.

---

## P0 — blocks the deliverable (do first)
1. **Restore the base scripture HTML and re-establish the build.** `epub_working/index_split_*.html`
   is missing (see `MATRIX_MAP.md` → "base-HTML gap"). Proof it's the blocker: `ebible doctor` →
   ship-check shows `verify: 0/0 paired` and `inject: 0 scanned` (nothing to pair/inject because
   there's no HTML). **Recover** from `…/Ethiopian_Bible_HANDOFF_v9_2026-05-05/epub_working/`, then
   `ebible build` (inject current 52K notes → manifest → editions → epubcheck). Verify **paired=N/N**
   + epubcheck clean. This makes the builder produce EPUBs again.

## Database / data layer — verdict: SOUND (no change needed)
- Source of truth: `content/notes/*.py` (87 files) + `content/translations/<id>/*.py`. Derived index:
  `core/corpus_index.py` = **sqlite + FTS5** (`compute_matrix_indexed` ~263 ms cold, lru-cached);
  `work_cache`/`build_cache`/`manuscript_index` = sqlite; migrations via `run_migrations.py`.
- Flat-file source + derived sqlite index is a good design for a CC0 demo. **No DB upgrade warranted.**
- **P2 (defer):** the scripture TEXT lives in *two* places — the base `index_split` HTML (build source)
  AND `translations/*.py` (matrix/parallel source). Long-term, rendering base HTML *from*
  `translations/*.py` would delete the fragile uncommitted artifact. Large change; post-deadline.

## Production / build — verdict: one P0 + reproducibility
- **P0:** missing base HTML (above).
- **P1 — make the build artifact safe.** Once recovered, **commit the base HTML** (or a clean
  note-free base) to git so a lost working dir can never block builds again. Add build *output*
  (`epub_working/onix/`, per-edition `*.epub`) to `.gitignore` — `epub_working/` currently shows
  untracked.
- **P1 — `ebible build` smoke test.** A test that builds one edition and asserts a valid EPUB +
  `paired=N/N` would have caught this gap immediately.
- **P2:** web app is `ThreadingHTTPServer` — fine for a local CC0 demo. `epubcheck` needs Java; confirm
  availability or document it.

## Safety net — verdict: STRONG
- **3,374+ test functions across 80+ files**, plus the `paired=N/N` ref invariant, `validate_taxonomy`,
  `validate_schemas`, manifest SHA-256, and the `lint_rules` pre-commit hook. Genuinely robust.
- **P1 — fix `ebible doctor`.** It's **slow, not hung** (runs the full `ship-check`, minutes), and its
  advice is **pre-pivot**: it counts `content/onix.py` TODOs and says "submit to Apple Books/KDP/Kobo" /
  `ship --retail`. Make it pivot-aware (drop ONIX + retail), and guard its subprocesses with
  `stdin=subprocess.DEVNULL` (Windows WinError-6 hazard).
- **P2 — split monolith test files** (`test_scripts.py` ~14k lines; `test_ethiopian_gamma4.py` 734
  tests) for maintainability. Defer.

## Tools / dev tooling — verdict: good CLI, purge commercial cruft
- The `ebible` CLI is rich and good (`status`/`doctor`/`build`/`web`/`inject`/`manifest`/…).
- **P1 — purge pre-pivot commercial cruft from the LIVE path** (clearest "smoother" win, matches CC0):
  - `ship-check.py` step 5 = `build_onix.py` → remove (ONIX is dead post-pivot; it's a failing gate
    for no reason and slows `doctor`).
  - `doctor` + `status` → drop the ONIX-TODO check + retailer advice (status silently writes
    `epub_working/onix/*.xml` as a side effect).
- **P2 — delete the quarantined commercial modules** (`build_onix.py`, `content/onix.py`,
  `print_cover.py`, `core/sales.py`, `core/distribution.py`, `api/{sales,distribution,press_kit,license}.py`)
  + their tests + routes, once they're out of the live path. Bigger blast radius (live test suites +
  routes); do after P0/P1.

---

## Recommended order for the 18 days
1. **P0** — recover base HTML → `ebible build` → confirm a valid EPUB (the deliverable lives again).
2. **P1** — commit the base HTML + `.gitignore` build output (never lose it again).
3. **P1** — fix `ebible doctor` (de-commercialize + DEVNULL-guard) + add the `ebible build` smoke test.
4. **P1** — strip ONIX/commercial from the `ship-check`/`status` path.
5. **P2 (if time)** — delete commercial modules; finish standalone Ge'ez/Amharic build wiring; split monolith tests.

**Nothing here is a re-architecture.** The hard parts (content, data layer, tests, the app) are done;
the work is recover-the-build + de-commercialize + protect-the-artifact.
