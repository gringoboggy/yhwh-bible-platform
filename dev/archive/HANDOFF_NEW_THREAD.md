# HANDOFF — for a fresh Claude on a new thread

This file is for a future instance of Claude opening this project from
scratch. Read this top-to-bottom and you'll be ready to continue.

## What this project is

An EPUB platform for building **multi-edition study Bibles** from a
single master corpus. The Ethiopian Tewahedo edition is the flagship,
but the architecture supports unlimited editions (Catholic, Evangelical,
Jewish, Scholarly-Academic, plus future ones via cloning).

**Scope expanded mid-project** — this is now a white-label authoring
platform for schools, denominations, and small publishers. The user is
non-technical but is directing the architecture with strong product
instincts. The endgame is being able to demo to a buyer ("click a few
buttons → here's your customized Bible") and have them say yes.

## Where things are

```
/home/claude/                      project root
  scripts/web.py                   the unified web UI (one big file,
                                   ~4,300 lines, all 8 routes live here)
  scripts/build_edition.py         per-edition EPUB build pipeline
  scripts/build_epub.py            packages the EPUB
  scripts/build_onix.py            ONIX 3.0 metadata for distribution
  scripts/core/                    shared library (config, notes_io,
                                   html_utils, ui, sources, detectors,
                                   matrix)
  content/notes/<code>.py          1,381 notes across 87 books
  content/books.yaml               87-book registry with id_prefix
  content/kinds.yaml               63 note kinds (e.g. word, comm-rabbinic)
  content/categories.yaml          14 categories (the 14 symbols)
  content/editions.yaml            5 editions + their per-edition config
  content/canons.yaml              canon definitions (87/73/66 books etc)
  content/themes.yaml              theme registry
  content/themes/*.css             5 theme stylesheets
  content/scenarios/               saved hypothetical edition profiles
  content/onix.py                  ONIX defaults (legacy — pi.2 partly
                                   superseded this for OPF)
  epub_working/                    master HTML + stylesheet.css that the
                                   build pipeline filters per-edition
  exports/                         built per-edition EPUBs (gitignored)
  tests/test_scripts.py            133 pytest cases
  tests/test_core.py               core lib tests
  audit.py                         project linter (run before committing)
  HANDOFF_README_v7.md             ledger of every commit, what changed
  dev/SCOPE_2026-05-07.md          scope doc + 4 addendums
  dev/PLAN_2026-05-07.md           current sequence of phases (read this)
```

## The current state

```
v28a-50  2026-05-07  Bible Builder Wizard  ← latest tag
133 pytest passing, audit clean (198 INFO / 0 WARN)
ship-check 6/7 (the failing check is intentional ONIX TODO; commits are
              tagged with --no-verify because of this; not a bug)
```

Eight web routes live, all cross-linked in their headers:

```
/             note editor (the original UI)
/matrix       category × edition toggle grid
/sources      browse-by-book + per-note disable per edition
/export       buyer-facing pre-flight summary + build + download
/customize    edit symbols/labels + edition meta + verse-popup flag + theme
/audit        attribution quality dashboard
/publisher    full publishing metadata (imprint, ISBN, copyright, authors, BISAC)
/wizard       6-step Bible Builder for buyer demos
```

## The user's mental model & preferences

The user is non-technical. They ARCHITECT through clear product vision.
They delegate sequencing decisions to Claude. They:

- Trust Claude to pick the right next thing without long debates
- Say "push", "go", "do it all" when they want execution
- Get frustrated by Claude pausing to ask questions when sequencing is
  delegated — just execute
- Save artifacts on demand, never auto-save
- Want sanity audits and cleanup periodically
- Want the MOST POLISHED demo possible to show buyers

## Memory rules currently in effect

These are stored in the user's persistent memory and apply across all
sessions:

```
1. Before any zip/save/archive output: ALWAYS ask first whether to
   save and whether slim or full. "Continue/proceed/go ahead" are
   NOT save commands.

2. During long tasks: pause around the 7-min mark of a single
   response (or sooner if a logical seam appears) to avoid crashing
   the response. Stop, summarize, resume next turn.

3. When the user delegates sequencing ("you decide", "whatever order",
   "do it all", "push"), Claude picks the order without asking, using
   these priorities: (1) safest/most-foundational changes first,
   additive over destructive, defaults that preserve existing behavior;
   (2) what most directly serves the user's stated end-goal (currently:
   a buyer demo where clicking a few buttons produces a customized
   Bible); (3) bundle paired phases together; (4) split at logical
   seams for the 7-min budget.
```

## How a typical work session goes

1. User says "push" or names a phase (e.g. "do tau.1 next")
2. Claude reads dev/PLAN_2026-05-07.md to confirm next phase
3. Claude implements the change (backend → smoke test → UI → tests)
4. Claude updates HANDOFF_README_v7.md ledger row + Last updated line
5. `git add -A && git commit --no-verify -m "v28a-NN: ..."`  (must use
   --no-verify because of the intentional ONIX TODO in ship-check)
6. `git tag -a v28a-NN -m "..."`
7. Tell user what just happened, ask whether to push on or save

When the user says "save", Claude asks slim vs full unless they specify.

## Where to look in dev/PLAN_2026-05-07.md

The plan tracks done phases vs upcoming. Currently:

```
DONE:
  v28a-32..35   λ        pipeline polish
  v28a-36..40   μ        symbol-toggle stack
  v28a-41       η.1      sample notes for empty categories
  v28a-42       σ.1+σ.2  buyer-facing /export
  v28a-43       ν.1      symbol/label customization
  v28a-44       ν.2      edition meta + verse-popup flag
  v28a-45       ν.3      theme picker
  v28a-46       ξ.4      attribution audit
  v28a-47       ρ.1+ρ.2  per-note disable (book + chapter level toggling)
  v28a-48       π.1      publisher console UI
  v28a-49       π.2      publishing block wired into OPF
  v28a-50       π.5      Bible Builder Wizard

NEXT (in order):
  ξ.5            edition-diff view (sales/demo tool — pure read-only)
  ν.2.5-A        verse-popup disable side (strip clickability)
  τ.1            translation extractor (KJV first, public domain)
  τ.1.5          translation picker per edition
  ν.2.5-B        verse-popup enable side (inject popup HTML using τ.1)

LATER:
  π.3 π.4        front/back matter editor + cover upload
  σ.3 σ.4 σ.5    PDF / print PDF / web-viewer bundle
  ο.*            school-classroom features
```

## Critical conventions Claude must follow

### Note IDs (Phase ρ.1)

Stable note ID format: `<book_code>:<chapter>:<verse>[<suffix>]:<kind>`
e.g. `gen:1:1a:word`. Maps to HTML format `ref-<prefix><cc><vv><suffix>`
e.g. `ref-g0101a` via `html_ref_id_from_note_id()` in web.py.

### Custom YAML parser quirk

`scripts/core/config.py` has its own YAML parser (`_parse_yaml_records`).
It interprets `      - field: value` as a NEW RECORD START. So when
emitting list items that contain colons (like note IDs `gen:1:1a:word`
or BISAC codes), the items must be **double-quoted**:

```yaml
disabled_note_ids:
  - "gen:1:1a:word"     # quoted — parser sees as scalar
authors:
  - "Dr. Jane Editor (editor)"   # quoted — safe
```

The `_patch_yaml_list_field()` and `api_save_note_toggle()` helpers
already do this. Future code that emits lists into editions.yaml MUST
follow this pattern.

### YAML field type preservation

`_patch_yaml_entry()` in web.py (Phase ν.2 fix) preserves YAML scalar
types:
- `verse_popups: false` stays a real bool, not a `"false"` string
- `copyright_year: 2026` stays a number where appropriate
- already-quoted strings pass through

If you add a new boolean or numeric edition field, this will Just Work.

### MARC relators codes (Phase π.2)

In `scripts/build_edition.py`, `_parse_author("Name (role)")` returns
a (name, marc_code) tuple. Recognized roles map to standard codes:
aut/edt/trl/fwd/ill/com/win/aft. Unknown roles default to `aut`.

### Backward compatibility (Phase π.1 + π.2)

`PUBLISHING_DEFAULTS` is defined in BOTH `scripts/web.py` AND
`scripts/build_edition.py:_resolve_publishing()`. They MUST stay in
sync. If you add a publishing field, add it to both.

### The 5-edition lineup (don't change without reason)

```
ethiopian-tewahedo    87-book Ethiopian canon — flagship
catholic-study        Catholic 73-book — largest commercial market
evangelical-reformed  Reformed Protestant
jewish-study          Tanakh-only
scholarly-academic    full apparatus, all comm-* kinds
```

## Test invocation

```bash
cd /home/claude
python3 -m pytest tests/ -q          # all 133 tests, ~1 second
python3 audit.py                     # project linter (197 INFO ok)
python3 ship-check.py                # build readiness (6/7 ok; ONIX TODO is
                                       intentional — this is why commits
                                       use --no-verify)
```

## Build invocation

```bash
# CLI build (what the /export and /wizard UIs wrap):
python3 scripts/build_edition.py catholic-study \
    --output-dir exports --version v28a --force
```

## Web UI invocation

```bash
python3 scripts/web.py             # localhost:8765
python3 scripts/web.py --port 9000
```

Or via the unified CLI:
```bash
python3 -m scripts.ebible web
```

## When the user says "save"

Always ask slim vs full first (memory rule #1).

```bash
# Slim (~7-8 MB): scripts + content + tests + dev + epub_working +
#                 top-level files. Excludes .git, .tools, .cache, exports.
# Full (~80 MB): everything except .cache (which is huge and
#                regenerable from pyproject.toml).
```

Both go to `/mnt/user-data/outputs/` and use `present_files`.

## When something feels wrong

If a git operation fails, check:
- ship-check is the LAST hook; ONIX TODO check fails intentionally.
  Use `--no-verify` for commits. This is documented and not a bug.
- `.backups/` directories exist in epub_working and content. Don't
  remove them — they're rollback safety nets.

## What to avoid

- **Never** modify the existing 1,371 user-original notes. The η.1 set
  added 10 sample notes anchored to specific verses; future sample
  additions should follow the same attribution pattern (cite
  provenance + cite "Sample reference; see [source]").
- **Never** silently change the 5 edition IDs or canon names — they're
  referenced everywhere.
- **Don't** auto-save zips. The user explicitly added a memory rule
  about this.
- **Don't** ask for sequencing approval when the user delegates — just
  execute and explain after.

## When in doubt, the truth is in:

- `dev/PLAN_2026-05-07.md` — current sequence
- `dev/SCOPE_2026-05-07.md` — scope (4 addendums attached)
- `HANDOFF_README_v7.md` — ledger of every commit's intent
- `git log --oneline | head -20` — actual history
- `python3 -m pytest tests/ -q` — verifies nothing is broken

Welcome aboard. The user is great to work with — clear vision, trusts
delegation, appreciates speed. Push on with confidence.
