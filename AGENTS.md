# AGENTS.md — YHWH (“Ya’ Way”) Bible-publishing platform

Portable instructions for **any** coding agent (Grok Build, Codex, Cursor, Copilot, …)
working in this repo. This file is a **digest** — the full, authoritative rules live in
[`dev/CLAUDE_PROJECT_RULES.md`](dev/CLAUDE_PROJECT_RULES.md) (§-numbered) with the
lifecycle/gates in [`dev/SESSION_PLAYBOOK.md`](dev/SESSION_PLAYBOOK.md).

**Precedence:** a one-off instruction from the maintainer wins *for that turn* (the
written rule stays). Otherwise `dev/CLAUDE_PROJECT_RULES.md` wins over this digest.
**When in doubt, read the full rules** — do not guess from this page alone.

---

## What this project is

A **free, fully-local** app (desktop + from-source web console) that builds custom
study **EPUB 3** Bibles from one **Ethiopian Tewahedo superset** corpus. The user picks a
canon/tradition, toggles note *kinds* and verse-popup languages, themes it, and exports a
standards-clean EPUB — **no account, no server, no cloud, nothing for sale**.

- **The demo is the north star:** open `/wizard` → pick a starting edition → 7 cards →
  **BUILD** → an EPUB downloads with the chosen theme, only the picked notes, and verse
  popups in the configured languages. Every change should make that demo better, simpler,
  deeper, or more impressive — otherwise defer it.
- **One superset, many filtered views:** the `ethiopian-tewahedo` edition is the SUPERSET;
  every other edition is a **canon + kind filtered subset**. Note counts fall out of
  filtering automatically — never hand-set them, never fork a per-canon corpus.
- **Maintainer:** Bogdan (“Boggy”), a first-time programmer building this as a
  faith-driven free service. Explain accessibly; never dumb down the work; honor the faith
  respectfully.

## Prime directives (how to work here)

1. **Quality, completeness, correctness > speed or token cost.** No time-gating. Take the
   most complete, maintainable path even if it’s far more work. If a better approach
   surfaces mid-task, **stop and re-plan** rather than patch forward on an inferior one.
2. **Verify before you claim.** Never say done / saved / passing / fixed without running
   the command and reading the output. If something failed or is uncertain, say so plainly.
   Never overstate or reassure.
3. **Re-verify with real data** — your *own* optimistic re-scopes, any documented “no-go,”
   and computed analyses. Don’t assert from assumption.
4. **Root-cause, then fix the whole class.** A patterned defect → find *why*, fix every
   instance, and add a guard (test/lint/gate) so it can’t recur — **in the same commit**.
5. **Everything is configurable.** Propose UI / presentation / feature changes as **builder
   options** (an `editions.yaml` field with a back-compat default → a `/customize` control →
   a build-pipeline branch), never one hardcoded choice.
6. **Never unilaterally remove** a feature, content, or platform. Propose how to keep it and
   let the maintainer decide. A real defect you spot in passing is in-scope — fix it now.
7. **Sources are never “missing.”** Look in `content/sources/`, `content/translations/sources/`,
   `_acquire/` (one level above the repo, gitignored), the top-level PDFs (arbitrary
   filenames — don’t grep by book title), and `GAPS/` before ever concluding “blocked on
   sources.” The whole canon is already sourced.
8. **Use TDD.** Write the failing test (RED) first, then the fix (GREEN). A feature isn’t
   done until it has a test that would catch the demo breaking.
9. **Public-facing copy is plain and factual** — no grandiosity, false modesty, or
   charity/favor framing (free is neutral, not a gift). Never call the system “idiot-proof.”

## Tech stack

- **Backend:** Python **3.14+**, **standard library only** — `http.server` web console in
  `scripts/web.py` + `scripts/api/*` (one module per console area). **Never** Flask /
  FastAPI / Django. One runtime dependency: **PyYAML**.
- **Frontend:** **Tailwind via CDN** (`https://cdn.tailwindcss.com`), plain ES6 in
  `<script>` tags. **No CSS build step, no JS build step.** Console pages are raw-string
  HTML templates in `scripts/templates/*.py`.
- **Config:** `content/*.yaml` (`editions`, `kinds`, `categories`, `canons`, `books`,
  `_meta`), read **only** through the lru-cached loaders in `scripts/core/config.py`.
- **Corpus data = Python data files, not a database:** `content/notes/<book>.py` define a
  literal `NOTES = [(ch, v, suffix, anchor, kind, title, label, body[, attribution]), …]`;
  `content/translations/<id>/<book>.py` define one literal tuple per verse `(chapter, verse,
  "<text>")`. Parsed with **`ast.literal_eval` only — never `exec`/`eval`**.
- **EPUB pipeline:** inject notes into base scripture HTML → filter per edition → store-zip.
- **Validation tooling:** **epubcheck** (EPUB 3.3), **ruff** (format + lint, line-length
  120), **mypy** (typed surface only), **pytest**. Kobo artifact via **kepubify (pinned
  v4.0.4)**. The only Node step is the public site: `website/build.mjs`.

## Repository layout

| Path | What |
|---|---|
| `content/` | **Single source of truth** — `*.yaml` config, `notes/`, `translations/`, `sources/`, `covers/`, `themes/`, `candidates/` |
| `epub_working/` | **Base scripture HTML** (`index_split_000..060.html`) edited **in place** — the inject target / build source-of-truth, plus `content.opf`, `toc.ncx`, `nav.xhtml`. **These split files are SHARED across multiple books.** |
| `scripts/` | All code: `ebible.py` (CLI), `web.py`, build/inject pipeline; `scripts/core/` (config, matrix, notes_io, validation), `scripts/api/` (routes), `scripts/templates/` (console HTML) |
| `tests/` | pytest suite (`test_*.py`) + `conftest.py` |
| `dev/` | Docs + state: `CLAUDE_PROJECT_RULES.md`, `SESSION_PLAYBOOK.md`, `MATRIX_MAP.md`, `REPO_MAP.md`, `SESSION_STATE.md`, `CHANGELOG.md`, `EREADERS.md`, `TOOLCHAIN.md` |
| `exports/` | Generated EPUBs + stats. `build/`, `dist/`, `website/` are build artifacts (mostly gitignored). |

A **new undocumented top-level directory fails the `repo_map_complete` gate** — document it
in `dev/REPO_MAP.md` (regenerate the inventory read-only with `py dev/trace_repo.py`).

## Setup

```bash
pip install -r requirements.txt                 # runtime (PyYAML)
pip install -r requirements.txt -r requirements-dev.txt   # + pytest/ruff/mypy/epubcheck
git config core.hooksPath .githooks             # activate the pre-commit hook (once per clone)
```

Use a **real Python 3.14 interpreter**: macOS/Linux `python3`; **Windows `py -3`** (or the
full path `C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe`) — **never bare
`python`/`python3` on Windows** (it hits a broken Store-alias stub).

## Build / run / test / gate commands

Prefer the unified CLI / `make` surface (cross-platform); the direct script is the fallback.

```bash
# Run
python scripts/launcher.py                      # serves the UI — opens a BROWSER from source
                                                #   (native PyWebView window only in the FROZEN
                                                #    desktop build: dev/requirements-desktop.txt)
py -3 -m scripts.web                            # web console only → http://127.0.0.1:8765/

# Build
./ebible build <edition-id>                     # single edition, clean surface
py -3 scripts/build_edition.py <edition_id> --version <X> --output-dir <Y> --force
#   ^ edition_id is a POSITIONAL arg (easy to omit). --force skips the build cache.
#   --target-reader <everywhere|eink|tablet|computer|kindle> builds a reader target
#     WITHOUT mutating editions.yaml (folds into the cache key). Prefer it over editing YAML.
make build                                       # full pipeline: notes → base HTML → all editions → validate

# Validate
python -m scripts.epubcheck <file>.epub --jar "<site-packages>/epubcheck/epubcheck.jar" --quiet --require
#   ^ ALWAYS pass --jar (auto-discovery hits a broken wrapper). Run epubchecks sequentially.
kepubify -o out.kepub.epub in.epub               # Kobo .kepub.epub (footnote popups need it)

# Test
make test
pytest -m "not slow and not done_gate"           # fast loop (skips slow/red-by-design pins)

# Gates (all must be green before a "done"/"save" claim)
py -3 scripts/ci.py                              # full local CI: ruff-format-check, ruff check,
                                                 #   lint_rules.py, mypy, pytest, coverage floor
py -3 scripts/lint_rules.py                      # project-rule linter (Tier-3 preflight)
py -3 dev/trace_matrix.py                        # matrix↔build integrity, target 0 unresolved refs
ruff format .                                    # format generated files BEFORE committing
```

**Done-contract (every one green before claiming done/save):** `lint_rules` 0 warn / 0 fail ·
`ruff format --check` clean · `validate_taxonomy` 100% · `validate_schemas` 6/6 · `ebible
verify` errors=0 (all asides paired) · `trace_matrix` 0 unresolved · `trace_repo` complete ·
targeted tests for every touched module green · if you touched the build/corpus, ≥1 edition
built → **epubcheck 0/0/0/0**.

## Environment gotchas (Windows host — get these right or things fail spuriously)

- **`$env:PYTHONUTF8="1"`** before any pytest / content-reading run, or ~72 tests fail with
  cp1252 `UnicodeDecodeError`.
- **`--basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`** on every pytest run, or
  `tmp_path` tests ERROR with WinError 5. An all-errors-are-setup split is *this*, not a real
  failure. Run pytest **from the repo root**.
- **`subprocess.run`/`Popen` must pass `stdin=subprocess.DEVNULL`** when not feeding the
  child (else WinError 6). The `subprocess_stdin` lint **fails the commit** otherwise.
- **epubcheck:** a JRE must be on PATH; always pass `--jar` the site-packages jar.
- **Memory:** 16 GB box — run the heavy trio (`inject --all-books`, a full `build_edition`,
  the epubcheck JVM) **one at a time**, never alongside a broad pytest sweep. A pytest
  `MemoryError` in startup is an env signal, not a code defect — don’t retry in a loop; run
  one test file at a time. Slowest files: `test_byte_stability_gate.py` (~205s),
  `test_matrix_psi35.py` (~87s), `test_web_filesplit.py` (~45s) — all `slow`-tagged.
- **`content/editions.yaml` flickers as git-modified** mid-test from a benign CRLF→LF flip
  (never commits). Judge pollution by **`git diff` (content), not `git status`**.
- Verify **Greek/Geʽez** text by reading, not grep (Unicode NFC mismatch).

## Code conventions

- **Routes:** one `BaseHTTPRequestHandler` in `scripts/web.py`. `/foo` → HTML, `/api/foo` →
  JSON; new routes add an `if path == …` branch in `do_GET`/`do_POST`/`do_PUT`.
- **Feature endpoints = pure function + thin adapter.** The pure function returns a dict
  (`{"status": "ok"|"error", "code", "http", "message", ...}`) and **never raises for
  expected errors**; the route adapter does **only** dict→HTTP translation (no business
  logic). All inputs are explicit kwargs. Inject slow operations as a callable param so tests
  mock them.
- **Compose, don’t recompute.** A new aggregate endpoint calls the cheapest existing
  (cached) endpoint instead of re-walking the corpus.
- **Caching by mutability:** user-editable data (notes/translations) → `lru_cache` keyed on
  `(path, mtime_ns)` (via `notes_io.load_notes`); project-internal published data →
  `@lru_cache(maxsize=1)` singletons (tests that mutate them call `<loader>.cache_clear()`).
- **Writes:** all corpus writes go through **`notes_io.atomic_write`** (`atomic_write_bytes`
  for bytes); bulk/destructive writes call `notes_io.ensure_backup` first.
- **Security — file-serving & upload routes are sandboxed.** Any route that serves a file or
  accepts an upload MUST reject `..`, absolute paths, and hidden segments **at the string
  level first**, then `.resolve()` the path and confirm `file_path.relative_to(safe_root)`
  (403/404 on failure). Detect upload format from **magic bytes, never the filename**;
  validate before writing; on a YAML-save failure **roll back the file write** (unlink) so
  disk and YAML never disagree. Traversal + rejection-path tests are non-optional.
- **YAML edits** via `_patch_yaml_entry` / `_patch_yaml_list_field` — **never `yaml.dump`**
  (it drops comments and ordering).
- **Per-book settings (`*_per_book`)** are stored as a **FLAT list of `"<book_code>=<value>"`
  strings** (the custom YAML parser has no nested mappings), decoded to dicts only in the
  API/UI layer; the encoder MUST sort entries in **canonical book order**, and the API hides
  slots for books outside the edition’s canon.
- **Don’t blindly `ruff check --select F401 --fix`:** `scripts/web.py` and
  `scripts/templates/*` are re-export hubs; `--fix` wrongly strips their imports. Run the
  full suite after any F401 change.
- **Original-language verse text is trusted pre-formatted HTML** (`popup_versions.is_trusted_html`,
  rendered **raw**; plain-text translations are **HTML-escaped**). The house format is
  **byte-pinned by `tests/test_wlc_ingest.py`**: each word in `<em>…</em>` joined by single
  spaces, morpheme `/` stripped, maqaf-joined words kept in ONE `<em>`, sof-pasuq glued to the
  last word, paseq its own `<em>׀</em>`; **read the WHOLE `<w>` element, not just `.text`**, or
  nested scribal special letters are silently dropped. New translations live in
  `content/translations/<id>/` with coords remapped to canonical KJV via
  `scripts/core/versification.py`.

## Hard invariants (do not break — most are gate-enforced)

- **Byte-identical schema migrations:** adding an `editions.yaml` field is **always a no-op
  when unset** — a build with it unset must be byte-identical to before. **New *required*
  fields are forbidden** (pick a documented default).
- **`matrix == build` through ONE resolver:** every per-edition “which kinds ship” decision
  flows through the single `config.enabled_kind_codes(edition, all_kinds)` path that **all
  three** of `matrix._enabled_kinds_for_edition`, `build_edition.compute_enabled_kinds`, and
  `config._kinds_in_edition` delegate to — applying every gate in precedence order:
  explicit `disabled_kinds` > phase gate > AI double-opt-in (`enable_ai_notes`) >
  `enabled_kinds`/category. **Never add a fourth path or re-implement a gate.** Pinned by
  `tests/test_enabled_kinds_unified.py`. Drifting copies of this was the project’s most
  expensive defect.
- **Registering a note kind** in `content/kinds.yaml` requires bumping its count pins in the
  **same commit**: `record_count` in `tests/test_validate_schemas.py` and the `N kinds`
  docstring in `scripts/core/matrix.py`. Register a kind only in a commit where it gains ≥1
  note (the preflight `empty_kinds` check warns otherwise); edition enablement is automatic
  by category.
- **Prove byte-stability** of any output-preserving change: regen, then `git diff` is empty
  (judge by `git diff`, not `git status`). For additive changes, bucket *every* changed item
  into expected categories; investigate any “other.”
- **Canonical order, always:** every book-listing UI uses the order in `content/books.yaml`
  (Genesis → … → Revelation, then deutero/apocrypha, then Ethiopian-only); chapters and
  verses ascending. **Never** sort alphabetically / by count / by importance; alt sorts keep
  canonical one click away.
- **Book count = 83** in all public/user-facing copy (the shipped superset). The raw registry
  is 87 but four additions fold into Daniel/Esther — **never say 87 publicly**. A count change
  cascades across page bodies, `<meta>`/og/twitter tags, the social-card image,
  GitHub/GitLab descriptions, release notes, in-app trackers, and EPUB metadata.
- **Canonical 3-letter book codes** (`joe/jhn/phi/jam/eze/nah/mrk/psa`) — normalize at
  ingest. Legacy aliases target non-existent files → notes silently drop. The
  `bookcode_canonical` lint fails the commit; add any new map to it.
- **Translation coords are canonical KJV/WEB numbering** (the base HTML is KJV-numbered).
  Validate every emitted coord with `canonical_verse_counts.coord_in_canonical_extent` → 0
  out-of-extent.
- **Base HTML in `epub_working/` is edited in place** and is the scripture-text source of
  truth — **not** re-rendered from `content/translations/*.py` (a bare-base regen is LOSSY;
  see the pipeline section).
- **EPUB = mimetype-first, store-only zip;** every shipped edition must be **epubcheck
  0/0/0/0**. Gate HTML-structure changes on **both** the superset *and* a canon-filtered
  edition (e.g. `catholic-study`) — the canon splice has structural edge cases the superset
  never exercises.
- **Legal:** the program + original editorial work are “© 2026 Bogdan Zorlescu. All rights
  reserved.” Incorporated Bible texts (WEB / Strong’s / TSK / Douay / Vulgate / JPS / WLC /
  LXX / Byzantine) stay public domain, documented separately. **Never** re-introduce
  CC0/public-domain language for the program.
- **Don’t hard-code live counts** (note totals, edition/kind counts) — they rot. Read
  `dev/SESSION_STATE.md` for current figures; matter pages (colophon/about) compute counts
  live from `scripts/core/matrix` at build time.

## The EPUB pipeline & the bake-and-prove gate

```
content/notes/*.py ──inject──▶ epub_working/index_split_*.html ──build_edition (filter by
   canon + enabled-kinds) ──build_epub (store-zip)──▶ <edition>.epub  (epubcheck 0/0/0/0)
```

- **`inject` is additive-only** — it adds missing notes but **does not prune** asides whose
  source note was deleted. To *remove* notes, surgically regex-remove the orphaned
  markers+asides from the book’s split file, then `inject --book <code>`.
- ⚠ **`index_split_*.html` files are SHARED across books.** Find a book’s files via
  `config.books_by_code()[code]['files']`, and before any blanket per-kind regex confirm that
  kind belongs ONLY to the target book in those files (e.g. only `phi`/`jam` carry
  `lang-hebrew` among NT books) — or you’ll silently delete another book’s notes.
- ⚠ **Never bare-base regen to delete** (`git checkout <base> -- epub_working/` →
  `inject --all-books` → `generate_verse_popups`): it is **permanently lossy**.
  `generate_verse_popups` harvests existing popup content the resolver cannot rebuild
  (cross-book deutero mappings, e.g. Douay/Vulgate on cross-book additions); restoring the
  bare base wipes it, harvest finds nothing, and it does **not** byte-reproduce HEAD.
- **A corpus change is NOT done until it is baked into a build.** Promoting writes only
  `content/notes/`. Run, in order: `inject --all-books` (`--dry-run` first to confirm
  additive-only) → **`python scripts/check_nested_anchors.py --fix` + `pytest
  tests/test_nested_anchors.py`** (epubcheck does **not** catch base nested-`<a>`) → `ebible
  verify` → rebuild a flagship → epubcheck 0/0/0/0. **If the rebuilt EPUB is the same size as
  before, you forgot to inject.** Commit the changed `epub_working/` split files alongside the
  notes.
- ⚠ **`ebible verify` checks marker↔aside PAIRING only — NOT source↔build correspondence.**
  An orphaned aside (whose source note you deleted but didn’t un-bake) passes `verify`
  **silently**. A green `verify` is not proof the build matches the corpus — keep source and
  build consistent yourself.
- A **base-WIDE re-bake** (a `marker_style` change, a new popup version) mutates the shared
  base for **every** edition — prove it with the **byte-multiset categorize-diff** verifier
  (bucket every changed item; investigate any “other”) plus `scripts/resync_marker_glyphs.py`,
  not a plain `git diff` size check.
- Never report “full suite green” from a curated subset — name the tests you actually ran,
  and include the base-invariant + translation tests.

## Saving & git

- **During active work: commit LOCALLY only.** Don’t push per-commit.
- **On an explicit “save” / “commit” / “push” / “backup” / “sync”** (or at a major
  milestone): commit, then **push both remotes** — `origin` = GitLab (code home), `github` =
  GitHub mirror — and **verify each leg landed** (`git status -b` ahead/behind = 0). The main
  Windows box additionally bundles `git bundle --all` to external **E:** and **F:** (never
  C:). “continue” / “proceed” / “go ahead” mean *advance*, **not** save.
- **`ruff format`** every file you generated/regenerated **before** committing, or the
  pre-commit hook (`ruff format --check .` + `lint_rules.py` + mypy) blocks it. The hook does
  **not** run the test suite — run the relevant tests yourself first.
- **GitLab `main` is PROTECTED:** never amend / rebase / reset / force-push a pushed commit —
  **fix forward**. Pull before a milestone push.
- **`git add -A` sweeps stray temp files** — delete repo-parent throwaway probes (`_*.py`,
  build temp dirs, `hs_err_pid*` JVM logs) before committing; `git status` must show only the
  intended changes.
- **Update `dev/SESSION_STATE.md`** (last shipped · next · test count · in-flight) as part of
  every save, and add a `dev/CHANGELOG.md` entry for any session that shipped ≥1 phase.
- **Never claim committed/backed-up without `git log -1 --oneline` + `git status --short`.**
  Uncommitted verified work is a loud warning, not reassurance — and never defer a commit to
  a future session.

## Testing conventions

- `pytest` classes named `TestX` per feature, in `tests/test_scripts.py` (most) or
  `tests/test_core.py` (core modules). Cover both unit and integration against real on-disk
  data.
- Tests restore any global state they mutate (`tmp_path` + `shutil.copy`, restore in
  `finally`). Be **state-aware**: parse the actual `IN_FLIGHT`/world state and assert the
  contract for *that* state — don’t assume the default.
- **Arc-close pins:** at a multi-wave content arc’s close, add a `_meta` sync pin, an
  **absolute-count** milestone pin (`corpus_count >= N` — never a share-threshold, which
  breaks as later waves dilute the share), and an exhaustiveness pin.

## Scope guardrails — what this is NOT

- **Not** a learning-management system (schools are an audience, not a feature).
- **Not** a retail / sales product — **no ISBN / ONIX / sales / POD / retail** surfaces.
  Multi-format export (PDF/MOBI/HTML/TXT) survives only as a **free download**.
- **Not** a multi-language *UI* by default (apparatus baseline is English; Bible *content* in
  many languages is the whole point).
- **Not** a real-time collaboration tool — one editor at a time; git history is the audit
  trail.
- **Not** Flask / FastAPI / Django, and **no build step** — stdlib backend + Tailwind CDN.
- The EPUB `dc:identifier` is a generator URN (`urn:yhwh:edition:<id>`), a generator id —
  **not** a commercial book identifier. The build is not for resale.

---

*Authority: [`dev/CLAUDE_PROJECT_RULES.md`](dev/CLAUDE_PROJECT_RULES.md) (§0–§15) ·
lifecycle & exact gate commands: [`dev/SESSION_PLAYBOOK.md`](dev/SESSION_PLAYBOOK.md) ·
data-flow: [`dev/MATRIX_MAP.md`](dev/MATRIX_MAP.md) · file index: [`dev/REPO_MAP.md`](dev/REPO_MAP.md) ·
live state & counts: [`dev/SESSION_STATE.md`](dev/SESSION_STATE.md). This digest is
regenerated from those; when they change, update it or treat them as authoritative.*
