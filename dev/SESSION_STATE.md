# Session state — current snapshot

**Updated:** 2026-05-08, after χ.7 Nave's Topical infrastructure
+ scope refresh + close-out.
**Save tag:** YHWH v2.4-full (χ.7 infra + new SCOPE_2026-05-08 +
PLAN_2026-05-08 + bootstrap-protocol pointer flip + linter hardening
+ old top-level 05-07 docs archived; addenda kept; 393 tests · 8/8
linter · 15,925 notes).

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

## Current phase: χ.7 Nave's Topical infrastructure shipped

The χ-cluster pipeline pattern (driver iterating cached source data
+ batch promote with `--kind` filter) was extended to a third
detector. All code, tests, and docs are in place; the only blocker
to corpus growth is reaching a PD upstream for the source JSON
(archive.org / openbible.info egress is blocked from the
development sandbox).

**Cumulative this session:**
```
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
terminus (`θ.2 + χ.1 + corpus ≥ 25K = v1.0`). See
`dev/SCOPE_2026-05-08.md` for the matrix-change rationale and
`dev/PLAN_2026-05-08.md` for the full 12-phase order. Top of
queue right now:

```
χ.7 USER-SIDE COMPLETION (no Claude needed):
   1. Run `python3 scripts/fetch_sources.py` from a network-permitted
      env (or drop a pre-built naves_topical.json into content/sources/).
   2. `python3 scripts/run_naves_at_scale.py` → writes candidates JSON.
   3. `python3 scripts/batch_promote_xrefs.py --kind topic-nave` →
      promotes to real notes.
   4. Tell Claude the new corpus total; SESSION_STATE updates accordingly.

χ.1  Strong's Greek + GreekWordDetector  NEXT FOR CLAUDE
     Parallels existing HebrewWordDetector exactly:
       • fetch Strong's Greek lexicon (PD, openscriptures)
       • write GreekWordDetector (mirror HebrewWordDetector)
       • driver reads NT books from KJV translation
     Risk: LOW (clear parallel to existing code)
     Expected: 5-10K lang-greek notes
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
