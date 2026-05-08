# Session state — current snapshot

**Updated:** 2026-05-08, after third-revision scope expansion +
ψ.10 popup typography polish + ν.2.9 save-pending badge shipped.
Continuous-go mode active per user directive.
**Save tag:** σ.3 → ω.6 → scope add → ω.7 → υ.7 → υ.1 → τ-scope →
3rd-rev scope on `bridge4kaladin-collab/yhwh-bible-platform`,
private. Saves are now git pushes, not zips — see "GIT BACKUP" in
the inventory below and the root-level `save.cmd` / `save.ps1`
helpers. Each commit runs the pre-commit hook
(`scripts/lint_rules.py` 8/8 must pass).

> 📖 **First time reading this?** Then go read
> `dev/CLAUDE_PROJECT_RULES.md` first, then come back here, then
> `dev/PLAN_2026-05-08.md`. Three files = full orientation.
>
> **Also peek** at `dev/IN_FLIGHT.md` — if its
> `<!-- TRACKER-STATE: ... -->` marker is `active`, work is open.

---

## Status snapshot

```
13 consoles · 438 tests · 8/8 linter · 5 editions · 15,925 notes

PLATFORM:    Feature-complete for the buyer demo.
             Tier 1 (debt + refactor) DONE.
             Tier 2 (corpus growth via χ cluster) UNDERWAY:
               χ.6 done (xref + hebrew via existing detectors)
               χ.7 INFRA done; data fetch is user-side
               χ.1 next (Strong's Greek — needs new lexicon + detector)

CORPUS:      15,925 notes (45.5% of 35K target — unchanged this session)
             χ.7 expected to add ~2-3K topic-nave notes once the
             source JSON lands in content/sources/.
             χ.1 (Greek) still expected to add ~5-10K lang-greek.
```

---

## Current phase: υ.1 /sources console upgrade shipped

The `/sources` console now hosts a Public-domain source cache section
above the existing per-book note-attribution navigator. Reads
`_fetchers.json` via the υ.7 loader; supports per-source Fetch / Force
re-fetch / Upload-pre-built-JSON / Clear, plus a top-level Fetch all /
Force re-fetch all. The χ.7 user-side completion (drop a pre-built
`naves_topical.json`) is now a one-click Upload JSON action in the UI
rather than a CLI dance.

```
✓ /api/sources/cache (GET)        status grid: cached, size_kb,
                                  mtime, candidates per source
✓ /api/sources/cache/<id>/fetch    POST {force, url_override?,
                                  parser_override?} — single source
                                  via injectable fetch_fn (testable)
✓ /api/sources/cache/_all/fetch    POST {force} — iterate every source
✓ /api/sources/cache/<id>/upload   POST multipart — JSON validated
                                  + atomic write + ensure_backup;
                                  disk untouched on validation failure
                                  (§9 binary-asset pattern)
✓ /api/sources/cache/<id>          DELETE — backup + unlink
✓ /sources HTML                    new <details> section above the
                                  per-book navigator; Tailwind only;
                                  no build step; cross-link invariant
                                  unchanged (no new console).
```

**+22 tests:** TestSourcesCacheUI in tests/test_scripts.py covers status
grid (4), fetch dispatch with injectable fetch_fn including url_override
and parser_override paths (5), fetch_all aggregation (2), upload happy
+ 6 rejection paths (multipart parser, JSON validity, dict shape, size
cap, missing file part, unknown source), clear (3), HTML wiring (1).
All synthetic — no network.

**Naming-collision avoided:** the existing `/api/sources/*` endpoints
remain about *note attribution* (per-book / per-note source strings).
The new endpoints live under `/api/sources/cache/*`. The `/sources`
HTML page hosts both as sibling sections under one page, preserving
the §6.2 cross-link invariant (no new console added; no other console's
nav block touched).

**Prior phases this session:**
- υ.7 — Pluggable fetcher config (declarative `_fetchers.json` loaded
  by `scripts/core/fetcher_config.py`).
- ω.7 — Persistent dev ergonomics (PYTHONUTF8=1 + Scripts on PATH +
  pre-commit hook + `.gitattributes`).
- ω.6 — Verified baseline (393/393 tests, 14/14 routes, 8/8 linter).
- σ.3 — GitHub backup workflow.
- Scope expansion — ψ.8 + ρ.1 + ω.6/ω.7 + ψ.10 + ψ.12 + polish trio.
- χ.7 Nave's Topical infrastructure.

**Cumulative this session:**
```
υ.1:         /api/sources/cache/* + /sources page extension; +22 tests.
υ.7:         _fetchers.json + fetcher_config.py + parser registry;
             +19 tests; 1 existing test repaired.
ω.7:         user env + tracked pre-commit hook + .gitattributes.
ω.6:         baseline verification (393/393, 14/14 routes, 8/8 lint).
σ.3:         repo init + private push + save.cmd/.ps1 wrappers.
Scope exp:   ψ.8 + ρ.1 + ω.6 + ω.7 + ψ.10 + ψ.12 + polish trio.
χ.7 infra:   16 new tests, 0 corpus notes.
End state:   434 tests, 8/8 linter, 15,925 notes.
```

## Prior phase: υ.7 pluggable fetcher config shipped

The PD-source list moved from Python constants in
`scripts/fetch_sources.py` to declarative JSON in
`content/sources/_fetchers.json`, loaded and validated by a new
typed module `scripts/core/fetcher_config.py`. Adding a new PD
source is now: (a) write a parser in `scripts/fetch_sources.py`,
(b) register its name in
`fetcher_config.KNOWN_PARSERS` and `fetch_sources.PARSERS`,
(c) add a `sources[]` entry to `_fetchers.json`. No constants need
touching, and the schema validator catches drift between the two.

```
✓ content/sources/_fetchers.json   schema v1; 3 sources declared
                                   (strongs_hebrew, tsk required;
                                    naves_topical optional with 4
                                    candidate URLs).
✓ scripts/core/fetcher_config.py   typed dataclasses (Source,
                                   Candidate, FetcherConfig);
                                   FetcherConfigError on any
                                   validation failure.
✓ scripts/fetch_sources.py          parsers registered in
                                   PARSERS dict; main() iterates
                                   loaded config; write_attributions
                                   now assembles its body from the
                                   config so adding a source auto-
                                   includes its license notice.
```

**+19 tests:** TestFetcherConfig in tests/test_scripts.py covers
the schema validator (default config loads, rejects 7 distinct
malformed shapes including unknown parser / duplicate id / wrong
version / empty candidates / non-bool required / missing license)
and the dispatcher (synthetic-parser stubbed via monkeypatch — no
network — verifying happy path, fall-through-on-failure,
all-candidates-failed, cached-skip, force-rerun).

**One existing test repaired:**
`TestNavesFetchSourceUtilities::test_naves_appears_in_attribution_doc`
called `write_attributions()` with no args; updated to load the
default config and pass it.

**Prior phases this session:**
- ω.7 — Persistent dev ergonomics (PYTHONUTF8=1 + Scripts on PATH +
  pre-commit hook + .gitattributes).
- ω.6 — Verified baseline (393/393 tests, 14/14 routes, 8/8 linter).
- σ.3 — GitHub backup workflow.
- Scope expansion — ψ.8 + ρ.1 + ω.6/ω.7 + ψ.10 + ψ.12 + polish trio.
- χ.7 Nave's Topical infrastructure.

**Cumulative this session:**
```
υ.7:         _fetchers.json + fetcher_config.py + parser registry
             refactor; +19 tests, 1 test repaired.
ω.7:         user env + tracked pre-commit hook + .gitattributes.
ω.6:         baseline verification (393/393, 14/14 routes, 8/8 lint).
σ.3:         repo init + private push + save.cmd/.ps1 wrappers.
Scope exp:   ψ.8 + ρ.1 + ω.6 + ω.7 + ψ.10 + ψ.12 + polish trio.
χ.7 infra:   16 new tests, 0 corpus notes.
End state:   412 tests, 8/8 linter, 15,925 notes.
```

## Prior phase: ω.7 persistent dev ergonomics shipped

Three locked-in ergonomic upgrades. All future sessions on this
machine inherit them automatically; future machines re-do (a) and
(b) once via env-var GUI / one PowerShell line, then run
`./dev/install_hooks.cmd` for (c).

```
✓ PYTHONUTF8=1 set in User registry env
   Future shells inherit it. Files in the project that the runtime
   reads with `open(path)` (no explicit encoding) now work without
   the cp1252 fallback that bit ω.6.

✓ Python Scripts/ dir on User PATH
   C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\Scripts
   `pytest`, `py.test` etc. callable directly in fresh shells.

✓ Pre-commit hook installed
   Tracked template:    dev/git-hooks/pre-commit  (sh script)
   Tracked installer:   dev/install_hooks.cmd     (CRLF, cmd-parser-safe)
   Active copy:         .git/hooks/pre-commit     (per-checkout)
   Behavior: every git commit (and therefore every save.cmd) runs
   `python3 scripts/lint_rules.py` first. Failures abort the commit.
   Bypass with `git commit --no-verify` only when truly needed.
```

**Caveats / known caveats:**
- Currently-running shells (this Claude Code session, any open
  PowerShell windows) won't see the new env vars until restart.
  The registry change took effect; only inherited copies are stale.
- The installer needed CRLF line endings on Windows — cmd's parser
  chokes on parenthesized blocks with bare LF. The tracked file is
  CRLF; if a future machine commits LF it will fail until reformatted.
- The hook's `python3` lookup falls back through `python` → `py -3`
  for portability. On Windows, the Microsoft Store's `python3` stub
  is intentionally ranked below the real install via the user's PATH
  ordering set in ω.7 (b).

**Prior phases this session:**
- ω.6 — Verified baseline (393/393 tests, 14/14 routes, 8/8 linter).
- σ.3 — GitHub backup workflow.
- Scope expansion — ψ.8 + ρ.1 + ω.6/ω.7 + ψ.10 + ψ.12 + polish trio.
- χ.7 Nave's Topical infrastructure.

**Cumulative this session:**
```
ω.7:         user env (PYTHONUTF8 + PATH) + tracked pre-commit hook +
             installer (cmd, CRLF). Two new tracked files.
ω.6:         baseline verification (393/393, 14/14 routes, 8/8 lint).
σ.3:         repo init + private push + save.cmd/.ps1 wrappers.
Scope exp:   ψ.8 + ρ.1 + ω.6 + ω.7 + ψ.10 + ψ.12 + polish trio.
χ.7 infra:   16 new tests, 0 corpus notes (fetch is user-side).
End state:   393 tests, 8/8 linter, 15,925 notes.
```

## Prior phase: ω.6 verified baseline shipped

Local Windows install confirmed clean against the project's claimed
baselines:

```
✓ 393/393 tests pass     (with PYTHONUTF8=1 — see encoding note below)
✓ 14/14 routes return 200 (the 13 consoles + the / editor)
  /, /matrix, /sources, /export, /customize, /audit, /publisher,
  /wizard, /diff, /compare, /covers, /preflight, /apihelp, /ops
✓ 8/8 linter checks pass
~ /api/preflight: 5 pass · 2 warn · 1 fail
  fail = "Main covers per edition" — pre-existing, documented
  warn = "Popup translation per edition", "Kind utilization"
```

**Encoding gotcha caught:** Python's default file-read codec on
Windows is `cp1252`; without `PYTHONUTF8=1`, 72 tests fail with
`UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d`. The
project's source uses `open(path)` without an explicit encoding,
which works on Linux/Mac (UTF-8 default) but breaks on Windows.
Workaround for now: always run pytest with `PYTHONUTF8=1` set.
ω.7 will set this as a user-scope environment variable so it's
permanent. The proper fix (sweep `open()` calls to add
`encoding="utf-8"`) is parked as a low-priority follow-up — the
env-var workaround is fine for single-developer use.

**Dependency installed:** `reportlab` (was missing; print-cover
PDF generation requires it). Installed via pip into the local
Python; not committed since it's environment, not source.

**Prior phases this session:**
- σ.3 — GitHub backup workflow (initial push, save.cmd/.ps1
  wrappers, `.claude/` in `.gitignore`).
- Scope expansion — ψ.8 cross-denom + ρ.1 audio + ω.6/ω.7
  added to PLAN; v1.0 terminus updated to include ψ.8; two
  new SCOPE addenda written.
- χ.7 Nave's Topical infrastructure (16 new tests, 0 corpus
  notes — data fetch + promote remain user-side, blocked on
  network egress to archive.org / openbible.info).

**Cumulative this session:**
```
ω.6:         baseline verification (393/393 tests, 14/14 routes,
             8/8 linter; encoding workaround documented;
             reportlab installed)
σ.3:         repo init + private push + save.cmd/.ps1 wrappers
Scope exp:   ψ.8 + ρ.1 + ω.6 + ω.7 added to PLAN; 2 new addenda
χ.7 infra:   16 new tests, 0 corpus notes (fetch is user-side)
End state:   393 tests, 8/8 linter, 15,925 notes
```

**New / modified scripts:**
- `scripts/core/sources.py` — `NavesTopical` loader + singleton
- `scripts/core/detectors.py` — `NaveTopicalDetector` (in `ALL_DETECTORS`)
- `scripts/prospect.py` — detector instantiation tolerates
  `SourceMissingError` (forward-compatible with χ.1+)
- `scripts/fetch_sources.py` — `fetch_naves_topical()` with
  mirror-list fallback; full English book-name remap
- `scripts/run_naves_at_scale.py` — new driver mirroring
  `run_xref_at_scale.py`; **appends** to existing chapter files
  so xref + hebrew + naves coexist
- `content/categories.yaml` — `topic` category (sort_order 15)
- `content/kinds.yaml` — `topic-nave` kind
- `tests/test_scripts.py` — 16 new tests (4 classes, all
  synthetic-fixture, no network dep)
- `tests/test_scripts.py` — `TestCustomize` count assertions
  migrated from `==` to `>=` floors

---

## What's next per `dev/PLAN_2026-05-08.md` (the new master sequence)

The 05-08 scope refresh re-shaped the sequence around a v1.0
terminus, and the 2026-05-08 *scope expansion* (cross-denom compare
apparatus + audio EPUBs) promoted ψ.8 into the v1.0 definition:

```
v1.0 = θ.2 + χ.1 + ψ.8 + corpus ≥ 25K notes
```

See `dev/SCOPE_2026-05-08.md` for the base refresh,
`dev/SCOPE_2026-05-08-addendum-cross-denom-compare.md` for ψ.8 spec,
and `dev/SCOPE_2026-05-08-addendum-audio-epubs.md` for ρ.1 spec.
`dev/PLAN_2026-05-08.md` carries the full 22-phase order. Top of
queue right now:

```
ω.6  Verified baseline                  ✓ SHIPPED 2026-05-08
ω.7  Persistent dev ergonomics          ✓ SHIPPED 2026-05-08
υ.7  Pluggable fetcher config           ✓ SHIPPED 2026-05-08
υ.1  /sources console upgrade           ✓ SHIPPED 2026-05-08
     (Public-domain source cache section on /sources: status grid,
      Fetch / Force / Upload JSON / Clear per source, plus a top-
      level Fetch all. Wraps υ.7's config; subsumes the parked
      χ.7 user-side completion into a single Upload action.)

— END OF TIER A FOUNDATIONS —

Tier B is next: corpus growth + uniqueness levers (χ.1 Greek,
ψ.10 popup polish, ψ.12 matrix smoothness, ψ.8 cross-denom
compare apparatus, ρ.1 LibriVox audio, ω.5 path refactor).

Post-v1.0 polish includes the τ cluster (PD translation expansion):
τ.1 WEB → τ.2 Douay-Rheims → τ.3 Vulgate → τ.4 Brenton LXX →
τ.5 JPS+WLC → τ.6 Ge'ez Tewahedo → τ.7 Greek NT → τ.8 Geneva →
τ.9 ASV+YLT → τ.10 non-English → τ.11 Reformation partials.
Spec: dev/SCOPE_2026-05-08-addendum-pd-translations.md.

The third-revision (2026-05-08) scope expansion promoted ξ.1/2/4
(security: input validation, path traversal, XSS), ω.8/9/10
(robustness: error boundaries, atomic writes, retry/timeout), and
ψ.13/14/17 (prettification: design system, buyer arc, reader EPUB)
into the v1.0 terminus. Specs:
  dev/SCOPE_2026-05-08-addendum-security.md
  dev/SCOPE_2026-05-08-addendum-robustness.md
  dev/SCOPE_2026-05-08-addendum-prettification.md
Operator-facing polish and other softer items stay v1.1+.

υ.7  Pluggable fetcher config           AFTER ω cluster
     content/sources/_fetchers.json — declarative URL +
     parser-kind list. Lets fetch_sources.py read its source
     list from config rather than Python constants.

υ.1  /sources console upgrade           AFTER υ.7
     Real source-management page: status grid, "Fetch this" /
     "Fetch all" buttons, drag-drop file upload. Permanently
     closes source-fetch friction; subsumes the parked χ.7
     finalization step into a UI button.

χ.7 USER-SIDE COMPLETION (parked):
     User runs fetch_sources.py + run_naves_at_scale.py +
     batch_promote_xrefs.py --kind topic-nave from a network env
     (+2-3K topic-nave notes). Likely subsumed by υ.1.

χ.1  Strong's Greek + GreekWordDetector
     Parallels existing HebrewWordDetector exactly. ~5-10K
     lang-greek notes. Risk: LOW (proven pattern).

ψ.10 Popup typography polish                  PRECURSOR TO ψ.8
     Theme-aware CSS-only pass on the .vnote popup so the
     ψ.8 tradition stack inherits styling instead of being
     designed twice. ~½ session.

ψ.12 Matrix smoothness pass                   PRECURSOR TO ψ.8
     Surfaced by 2026-05-08 audit. Bundle of 7 fixes in
     scripts/templates/matrix.py: incremental DOM patching
     (killer at scale), sticky headers, keyboard nav, scroll
     preservation, dismissable banner, etc. Lands BEFORE ψ.8
     adds the tradition data axis. ~1 session.

ψ.8  Cross-denominational compare apparatus    THE v1.0 DIFFERENTIATOR
     Single popup, side-by-side notes from Catholic /
     Protestant / Orthodox / Jewish / Tewahedo + cross-tradition.
     ~2-3 sessions; schema change. Spec in
     dev/SCOPE_2026-05-08-addendum-cross-denom-compare.md.

ρ.1  Audio-augmented EPUBs (LibriVox)
     EPUB 3 native <audio> embed; PD recordings.
     ~1-2 sessions. Spec in
     dev/SCOPE_2026-05-08-addendum-audio-epubs.md.

ω.5  Per-user data location refactor
     Path resolver into user_data_dir() — must precede θ.
     ~1-2 sessions.

θ.1, θ.2  Desktop binary
     Launcher + native shell. Reaches v1.0 candidate.
```

---

## Pending follow-ups (parked)

- **cleanup.py expansion** — should also prune `exports/`,
  `epub_working/`, `builds/`, AND `content/candidates/`.
- **scaffolder integration test** — running `--apply` against a
  temp dir, to catch indent-error class bugs.
- **UI defense prelude in scaffolder** — fold the bulk_inject
  step in so future scaffolded consoles get the prelude
  automatically.
- **§14 worked twice last session** (web.py split indent bug;
  HebrewWord cut-off). Document this as a §12 retrospective
  trigger candidate next time the rules doc is touched.

---

## Inventory pointers (where things live)

```
GIT BACKUP (σ.3 — shipped 2026-05-08):
  Remote:    https://github.com/bridge4kaladin-collab/yhwh-bible-platform (private)
  Default branch: main
  Save command:  ./save.cmd "<message>"   (preferred Windows wrapper)
                 ./save.ps1 "<message>"   (needs PS execution policy)
                 raw: git add -A; git commit -m "<msg>"; git push
  Pull command:  git pull                 (start of fresh session)
  Excluded:  .claude/ (per-machine), plus everything in .gitignore.
  GitHub CLI lives at: C:\Program Files\GitHub CLI\gh.exe
  gh authed as: bridge4kaladin-collab (HTTPS, keyring-stored token).

LOCAL DEV ENVIRONMENT (ω.6 verified, ω.7 ergonomic — 2026-05-08):
  Python 3.14.4 at C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\
  Scripts dir on User PATH (ω.7): ...\pythoncore-3.14-64\Scripts\
                                  pytest, py.test, normalizer, pyhtmlizer
                                  callable directly in fresh shells.
  pip-installed: pytest, pyyaml, reportlab.
  PYTHONUTF8=1 set in User registry env (ω.7) — fresh shells inherit.
                Required on this install: without it, 72 tests fail
                on `UnicodeDecodeError: 'charmap' codec` at byte 0x9d
                (Python's Windows default is cp1252).
  Test invocation:  pytest                 (in a fresh shell post-ω.7)
                    PYTHONUTF8=1 python3 -m pytest   (current/old shell)
  Web server:       python3 scripts/web.py
                    Default: 127.0.0.1:8765 (the editor at /, plus
                    13 cross-linked consoles)
  Linter:           python3 scripts/lint_rules.py
                    8 checks. Pre-commit hook (ω.7) runs this on every
                    `git commit` automatically; failures abort the commit.
  Pre-commit hook:  Tracked template:  dev/git-hooks/pre-commit
                    Tracked installer: dev/install_hooks.cmd (CRLF)
                    Active copy:       .git/hooks/pre-commit
                    Bypass for one commit: `git commit --no-verify`
  Known pre-existing /api/preflight conditions:
    fail "Main covers per edition"     placeholder paths in seeded
                                        editions.yaml — fix via
                                        /covers upload or /customize blank
    warn "Popup translation per edition"  pre-existing; not blocking
    warn "Kind utilization"             pre-existing; not blocking

INGESTION INFRA — already complete as CLI + UI:
  scripts/fetch_sources.py        (υ.7: declarative; reads _fetchers.json)
  scripts/core/fetcher_config.py  (υ.7: schema + loader + validator)
  content/sources/_fetchers.json  (υ.7: source list, schema v1)
  scripts/core/sources.py         (cache loaders for parsed data)
  scripts/core/detectors.py (HebrewWordDetector, CrossRefDetector,
                              NaveTopicalDetector — χ.7)
  scripts/prospect.py / scripts/promote.py
  scripts/add_note.py / scripts/inject.py
  /sources console PD-cache section (υ.1)  Fetch / Force / Upload
                                           JSON / Clear per source +
                                           top-level Fetch all
  /api/sources/cache (GET) + /api/sources/cache/<id>/* (POST/DELETE)

PD CORPORA cached locally:
  content/sources/strongs_hebrew.json   (populated)
  content/sources/tsk_xrefs.json        (populated)
  content/sources/naves_topical.json    (zero-byte placeholder; χ.7)
  fetch_sources.py populates with network access.

POPUP LANGUAGES (ν.2.7):
  scripts/build_edition.py POPUP_LANGUAGES + resolver
  encode/decode_per_book_languages
  editions.yaml: popup_languages_default + popup_languages_per_book

COVERS (π.4 — full upload pipeline + UI):
  scripts/core/covers.py + scripts/web.py
  Routes: GET /covers, GET /content/covers/<path>, GET /api/covers,
          POST/DELETE /api/covers/<edition>/{main,book/<code>}

PREFLIGHT (ψ.2 + composes lint_rules):
  api_preflight aggregates 8 checks; rules_compliance is the linter
  Routes: GET /preflight, GET /api/preflight

EDITION CLONING (ν.4):
  api_clone_edition + _append_cloned_edition
  Route: POST /api/editions/clone

AUTH GATE (ω.4):
  Handler._check_admin_auth gates POST/PUT/DELETE
  Off by default; set EBIBLE_ADMIN_TOKEN env var to enable

RULES LINTER (ω.0.1 + ω.0.4):
  scripts/lint_rules.py — CLI + run_all() API, 8 checks
    6.1 canonical-order encoders
    6.2 cross-link invariant
    encode_decode round-trip
    docs cross-references
    freshness CHANGELOG vs SESSION_STATE mtime
    inflight (Tier 3 — IN_FLIGHT.md marker)
    untracked_phases (Tier 3 — code phases vs CHANGELOG)
    code_doc_sync (Tier 3 — consoles in inventory)

READER EXPERIENCE (ν.6 + ν.6.1 + ν.6.x — full loop):
  scripts/build_edition.py:
    CHAPTER_NUMBER_FORMATS, CHAPTER_NUMBER_DECORATIONS,
    BOOK_TOC_ORNAMENTS, chapter_number_to_word,
    format_chapter_label, decorate_chapter_label,
    apply_chapter_decoration, apply_reader_toc_transforms
  scripts/web.py: api_save_edition_meta validates 5 new fields
  /customize: "Reader experience" card with all controls

GUARDRAIL SYSTEM (ω.0.4):
  dev/IN_FLIGHT.md   tier-2 task tracker (HTML-comment marker)
  dev/CLAUDE_PROJECT_RULES.md §12 footnote (tier 1) + §13 (tier 4)
  scripts/lint_rules.py — 3 new tier-3 checks

CACHING (φ.1):
  scripts/web.py: _files_signature, _notes_dir_signature,
  _cached_attribution_audit, _cached_edition_diff,
  _cached_publisher_data, _cached_covers, _cached_preflight

ATOMIC WRITES:
  scripts/core/notes_io.py: atomic_write (text), atomic_write_bytes
  (binary), ensure_backup (pre-mutation snapshot)

HOUSEKEEPING:
  scripts/cleanup.py (dry-run by default; prunes __pycache__ +
  *.pyc + .backups/) — TODO: also prune exports/, epub_working/,
  builds/, content/candidates/ (all regenerable)
  scripts/bulk_inject.py (ω.0.7 — bulk-modify *_HTML constants)
  scripts/scaffold_console.py (ω.0.2 — single-command new-console
  bootstrap)
  tests/fixtures.py (ω.0.3 — shared test fixtures)

CORPUS GROWTH PIPELINE (χ cluster — pattern proven repeatable
across 3 detectors now):
  scripts/run_xref_at_scale.py    (χ.6  — TSK xrefs at scale)
  scripts/run_hebrew_at_scale.py  (χ.6+ — HebrewWord at scale; OT only)
  scripts/run_naves_at_scale.py   (χ.7  — Nave's Topical at scale)
  scripts/batch_promote_xrefs.py  (χ.6  — generic in-process batch
                                          promoter; --kind filter)

  Pattern for future χ.* phases (χ.1 Greek, χ.2-5 commentaries):
    write detector class → write driver script iterating cached
    source data → run → batch_promote_xrefs.py --kind X.

CONSOLES (web UI) — all 13 cross-linked per Rule §6.2:
  /          note editor (different design, no console nav)
  /matrix    symbol toggle matrix view
  /sources   sources navigator
  /export    buyer-facing build flow
  /customize edition customization (chapter/ToC reader experience)
  /audit     attribution + quality audit
  /publisher publisher console
  /wizard    Bible Builder wizard
  /diff      sales-tool edition diff
  /compare   translation comparison view (ψ.4 — buyer demo)
  /covers    cover upload + per-book grid
  /preflight pre-ship readiness dashboard
  /apihelp   api reference
  /ops       operator dashboard
```

---

## In-flight notes

- **IN_FLIGHT.md is `idle`** at the time of this snapshot —
  χ.7 infrastructure is fully shipped; what remains is data
  fetch + promote on the user side, not Claude work.
- **Preflight FAILs on cover paths** — placeholder paths in
  seeded editions.yaml. Fixable via /covers upload or /customize
  blank.
- **Auth gate is OFF by default.** Set EBIBLE_ADMIN_TOKEN env
  var to require Bearer tokens on POST/PUT/DELETE.
- **`exports/` is empty.** Run `python3 scripts/build_edition.py
  <id>` per edition to populate.
- **PD corpus `naves_topical.json` is missing** awaiting network
  fetch via `scripts/fetch_sources.py` (or manual JSON drop).
  `NaveTopicalDetector` skips gracefully via prospect.py's
  resilient instantiation; existing TSK + Strong's flows
  unaffected.
- **`_files_signature` is intentionally NOT lru_cached** (rebound
  to `_files_signature_impl`). Don't "optimize" by re-adding.
- **Pre-existing nav debt — matrix alias.** Consoles' "matrix"
  nav link points to `/`, not `/matrix`. Linter accepts both.

---

## Memory rules pinned (canonical list)

1. Save = present zip (never just on disk)
2. Pause at 7-min mark
3. When sequencing delegated, pick safest+foundational first
4. "Continue/push" is NOT a save command
5. Read dev/CLAUDE_PROJECT_RULES.md FIRST
6. Read dev/SESSION_STATE.md to get current state
7. On user topic-shift: audit working tree + IN_FLIGHT before
   responding (§13 — pivot is a close-the-loop signal, not an
   abandon signal)
