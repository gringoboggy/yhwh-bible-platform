# Session state — current snapshot

**Updated:** 2026-05-08, after σ.3 GitHub backup workflow shipped.
**Save tag:** initial git push (`ea0fbeb`) + tooling fix (`3f014c0`)
to `bridge4kaladin-collab/yhwh-bible-platform`, private. Saves are
now git pushes, not zips — see "GIT BACKUP" in the inventory below
and the root-level `save.cmd` / `save.ps1` helpers.

> 📖 **First time reading this?** Then go read
> `dev/CLAUDE_PROJECT_RULES.md` first, then come back here, then
> `dev/PLAN_2026-05-08.md`. Three files = full orientation.
>
> **Also peek** at `dev/IN_FLIGHT.md` — if its
> `<!-- TRACKER-STATE: ... -->` marker is `active`, work is open.

---

## Status snapshot

```
13 consoles · 393 tests · 8/8 linter · 5 editions · 15,925 notes

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

## Current phase: σ.3 GitHub backup workflow shipped

The project is now backed up on GitHub at
`https://github.com/bridge4kaladin-collab/yhwh-bible-platform`
(PRIVATE; no collaborators; default branch `main`). Initial push:
1668 files, 653,880 lines, commit `ea0fbeb`. From this point forward
"save" means "git push", not "build zip" — per PLAN_2026-05-08 σ.3.
Two one-command wrappers at the repo root:
`./save.cmd "what changed"` (preferred — works under default Windows
PowerShell execution policy) or `./save.ps1 "what changed"` (only
works if execution policy is RemoteSigned/Bypass; .cmd shells out
to PowerShell with `-ExecutionPolicy Bypass`). Both run
add + commit + push end-to-end; default message is a timestamp.
New session: `git pull` first.

`.claude/` was added to `.gitignore` (per-machine permission cache,
not portable). 393 tests still green; nothing in the runtime changed.

**Prior phase:** χ.7 Nave's Topical infrastructure (16 new tests,
0 corpus notes — data fetch + promote remain user-side, blocked on
network egress to archive.org / openbible.info).

**Cumulative this session:**
```
σ.3:         repo init + private push (no test delta)
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
ω.6  Verified baseline                  NEXT (zero-risk; ~10 min)
     Run pytest once on this Windows install; smoke-test the
     web server's 13 consoles. Proves the baseline works before
     any new feature changes touch it.

ω.7  Persistent dev ergonomics          AFTER ω.6 (~30 min)
     (a) Add C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\
         Scripts to user PATH so `pytest` works without `python3 -m`.
     (b) Install `.git/hooks/pre-commit` running `lint_rules.py`
         so save.cmd can never push something failing 8/8 linter.
         Tracked-in-repo template at `dev/git-hooks/pre-commit`
         + `dev/install_hooks.cmd` so future machines replicate
         with one command.

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

INGESTION INFRA — already complete as CLI:
  scripts/fetch_sources.py / scripts/core/sources.py
  scripts/core/detectors.py (HebrewWordDetector, CrossRefDetector,
                              NaveTopicalDetector — χ.7)
  scripts/prospect.py / scripts/promote.py
  scripts/add_note.py / scripts/inject.py

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
