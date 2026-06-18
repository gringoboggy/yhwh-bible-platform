# YHWH Ya' Way — Ethiopian Tewahedo Bible builder (content + scripts system)

> **Scope.** This project aims to ship the most comprehensive study Bible
> ever assembled in EPUB format: the complete 87-book Ethiopian Tewahedo
> canon (broader than any Catholic, Orthodox, or Protestant canon), with a
> deep apparatus of original-language notes (Hebrew + Septuagint Greek),
> interpretive commentary, textual-variant analysis, and cross-references
> — combining comparative ANE context, rabbinic and patristic readings,
> archaeology, and literary parallels. Depth at every chapter and verse.

Single source of truth for project data, with CLI tools that wrap the existing
audit and injectors. Built in the Phase-1–4 refactor (2026-05-05).

## TL;DR

To add a note to any book:

```bash
python3 scripts/add_note.py \
    --book gen --ch 12 --v 5 \
    --anchor "took Sarai" --kind comm \
    --title "Departure from Haran" \
    --body "<strong>The call answered.</strong> Abram acts on..." \
    --inject --verify
```

That command validates everything, picks a unique suffix, writes the tuple
into `content/notes/gen.py`, runs the appropriate injector, and re-audits.

To check overall project health:

```bash
python3 scripts/run.py --check     # dry-run, never modifies HTML
python3 scripts/run.py             # interactive: prompts before applying
python3 scripts/run.py --yes       # auto-apply pending changes
```

## Directory layout

```
content/
├── books.yaml          single 87-book registry
├── kinds.yaml          commentary note kinds (symbol, css class, label)
└── notes/
    ├── gen.py          per-book NOTES list (one file per canonical book)
    ├── exo.py
    ├── 1en.py
    └── ... (87 total)

scripts/
├── core/
│   └── config.py       YAML loader: get_book(code), get_kind(code), ...
├── add_note.py         add a single note to a book
├── add_kind.py         register a new note kind (symbol, color, css)
├── verify.py           friendly audit wrapper
└── run.py              orchestrator: audit → inject pending → re-audit
```

The legacy locations (`source_archive/`, `kings_session/`) still exist; their
scripts now import from `content/` so both the new and old call paths work.

## Common tasks

### Add a note

```bash
python3 scripts/add_note.py \
    --book <code> --ch <N> --v <V> \
    --anchor "<exact substring>" --kind <comm|word|source|...> \
    --title "<tooltip>" --body "<strong>Title.</strong> Body..."
```

Optional flags:

- `--suffix m` — explicit suffix instead of auto-pick
- `--label "Note"` — explicit label (defaults to the kind's label)
- `--dry-run` — validate and print the tuple, don't write
- `--inject` — also run the injector (writes to HTML)
- `--verify` — also run the audit after injecting

The CLI:

1. Validates book code, kind, chapter range against `content/books.yaml`.
2. Validates anchor exists at the **exact verse** (not just somewhere in the
   book) using the same per-verse logic the injectors use.
3. Auto-picks the next free suffix from `m, n, p, q, b, c, d, ...` if multiple
   notes already exist on the same verse.
4. Refuses duplicates (same chapter+verse+suffix already in the file).
5. Appends a properly-formatted tuple to `content/notes/<code>.py`.

If the anchor doesn't match, the error message shows the actual verse text so
you can spot PDF double-spaces, curly-vs-straight quotes, or WEB-vocab
differences (e.g. "young goat" vs "kid", "today" vs "this day").

### Add a new note kind (symbol)

```bash
python3 scripts/add_kind.py \
    --code variant --symbol "†" \
    --label "Variant" --color "#2D5A3D" \
    --verify
```

The CLI:

1. Appends an entry to `content/kinds.yaml`.
2. Appends matching `.marker-<code>` and `.note-<code>` rules to
   `epub_working/stylesheet.css`.
3. Both injectors automatically pick up the new kind on next run (they load
   from `content/kinds.yaml`).

After registration, `scripts/add_note.py --kind variant` is immediately valid.

### Check project health

```bash
python3 scripts/verify.py                    # full audit + compact summary line
python3 scripts/verify.py --category B       # one category only
python3 scripts/verify.py --strict           # fail on WARN as well as ERROR
python3 scripts/verify.py --quiet            # summary only
```

### Daily workflow

```bash
python3 scripts/run.py
```

Output looks like:

```
=== Initial audit ===
✓ verify: errors=0  warnings=0  info=14  910/910 paired

=== Pending injections ===
Scanning 87 books for pending injections...
  gen    notes= 69  injected= 69  pending= 0  miss=0
  exo    notes= 87  injected= 87  pending= 0  miss=0
  ...
  1ch    notes=  3  injected=  1  pending= 2  miss=0  → 2 pending
  ...

2 book(s) have pending changes: 2 note(s) to insert, 0 anchor-miss(es).

Apply pending injections? [y/N]: y
```

Useful flags:

- `--check` — never write; just report
- `--yes` — auto-apply, no prompt
- `--book gen` — operate on one book
- `--skip-initial-audit` — faster if you just ran `verify.py`

## Validation & reporting (v25)

Five tools added in the v25 tooling roadmap. All default to read-only and
match the project conventions (argparse, color summary line, exit codes).

### `scripts/epubcheck.py` — W3C epubcheck wrapper

```bash
python3 scripts/epubcheck.py                  # auto-find latest .epub
python3 scripts/epubcheck.py --strict         # fail on warnings too
python3 scripts/epubcheck.py --require        # fail (exit 2) if not installed
python3 scripts/epubcheck.py --verbose        # show all findings
```

Fails soft if Java or the epubcheck JAR is unavailable (prints install
instructions, exits 0). Auto-discovers the JAR via PATH, `EPUBCHECK_JAR`
env var, `<repo>/.tools/`, or `~/.local/share/`. Most retailers run
epubcheck before listing — failing there means rejection.

### `scripts/check_xrefs.py` — broken-link finder (pure Python)

```bash
python3 scripts/check_xrefs.py                # all internal hrefs
python3 scripts/check_xrefs.py --asides-only  # only inside <aside> blocks
python3 scripts/check_xrefs.py --verbose
```

Validates every internal `href` resolves to a real `id` somewhere in the
EPUB. Companion to `link_xrefs.py`: catches typos in cross-reference
targets that the wrapping tool can't see. Cross-validated with epubcheck:
`broken-id` count exactly matches `RSC-012` count.

### `scripts/note_quality.py` — editorial quality flags

```bash
python3 scripts/note_quality.py               # all books
python3 scripts/note_quality.py --book gen
python3 scripts/note_quality.py --check too-short
python3 scripts/note_quality.py --strict      # fail on WARN too
```

Reads `content/notes/<code>.py` via `ast.literal_eval` (no code execution)
and flags 8 issues: empty-body, whitespace-anchor, malformed-html (ERROR);
no-opener, topic-only, too-short, too-long, presentational-tags (WARN).
Default exit 0 unless ERROR-severity findings or `--strict`.

### `scripts/dashboard.py` — single-file HTML report

```bash
python3 scripts/dashboard.py                  # writes ./dashboard.html
python3 scripts/dashboard.py -o /tmp/state.html
```

Generates a self-contained HTML page (no external CSS/JS/fonts) showing:
top-line counts, kind distribution bars, per-book progress table, SVG
density heatmap (book × chapter, hover for counts), and coverage gaps.

### `scripts/check_a11y.py` — WCAG 2.1 / EPUB Accessibility 1.1 audit

```bash
python3 scripts/check_a11y.py                 # full audit
python3 scripts/check_a11y.py --check contrast
python3 scripts/check_a11y.py --bg-color "#fff"  # override assumed bg
python3 scripts/check_a11y.py --strict        # fail on WARN too
```

5 checks: `lang`, `alt-text`, `contrast` (ERROR); `heading-skip`,
`presentational` (WARN). Implements WCAG 2.1 relative-luminance and
contrast-ratio formulas; verified against canonical values.

### `scripts/find_anchor.py` — propose anchor candidates for a verse

```bash
python3 scripts/find_anchor.py gen 1 26       # free 2–5-word substrings
python3 scripts/find_anchor.py gen 1 26 --all # also taken / overlapping
python3 scripts/find_anchor.py gen 1 26 --max-words 7
```

Eliminates the most common round-trip in a batch session — the anchor
collision. Shows the verse text, every existing note's anchor (with kind
+ suffix), and every distinct N-word substring not already in use.

### `scripts/note_diff.py` — diff two project states

```bash
python3 scripts/note_diff.py prev.zip .       # diff a save against working tree
python3 scripts/note_diff.py v24.zip v25.zip  # diff two saves
python3 scripts/note_diff.py --book gen prev.zip .
python3 scripts/note_diff.py --body-diff prev.zip .
```

Each side can be a directory or a `.zip`. AST-based loading — no exec.
Reports added / deleted / modified notes (sub-classified into anchor,
kind, body changes). Useful for changelog generation and editorial review.

### `scripts/preview_server.py` — local HTTP server for `epub_working/`

```bash
python3 scripts/preview_server.py             # http://127.0.0.1:8000/
python3 scripts/preview_server.py -p 8080
python3 scripts/preview_server.py --no-cache  # always re-fetch on refresh
```

Pure-stdlib HTTP server. Click through the EPUB in a browser without
packaging it first. Pair with `entr` or your editor's preview integration
if you want auto-reload on file change.

### `scripts/dashboard.py --heatmap-only` — coverage heatmap with clickable cells

```bash
python3 scripts/dashboard.py --heatmap-only   # writes coverage_heatmap.html
python3 scripts/dashboard.py --heatmap-only --link-prefix ""
    # if output will live inside epub_working/ (relative links flatten)
```

Standalone HTML/SVG heatmap of notes-per-chapter; cells are clickable
links into `epub_working/<file>#ch-bxx-cN`. Subset of the full dashboard,
toggled via flag (the roadmap's suggested implementation).

---

## Editorial / scholarship (v26)

Six tools from the roadmap's Backlog tier — daily-use editorial helpers
and one release orchestrator.

### `scripts/note_search.py` — tuple-aware grep

```bash
python3 scripts/note_search.py --body "Augustine"
python3 scripts/note_search.py --kind parallel --book gen
python3 scripts/note_search.py --regex --title "[Hh]ebrew"
python3 scripts/note_search.py --book gen --ch 1-11
python3 scripts/note_search.py --count          # only the count
```

Loads notes via AST (no exec). Filters compose (AND-ed). Highlighted
match snippets in colour terminals.

### `scripts/bulk_edit.py` — find/replace across notes safely

```bash
python3 scripts/bulk_edit.py "vinyard" "vineyard"            # dry-run
python3 scripts/bulk_edit.py "vinyard" "vineyard" --apply    # write + verify
python3 scripts/bulk_edit.py --regex "shma[ʿ']" "shema" --apply
python3 scripts/bulk_edit.py "Yahweh" "YHWH" --book gen
```

Text-level substitution across `content/notes/*.py` with full unified diff
preview. After `--apply`, automatically runs `verify.py` so the audit
consequence is visible in the same command.

### `scripts/citation_index.py` — inverse cross-reference graph

```bash
python3 scripts/citation_index.py                       # top 20 cited targets
python3 scripts/citation_index.py --target gen 1 1      # who cites this verse?
python3 scripts/citation_index.py --asymmetries         # per-book in vs. out
python3 scripts/citation_index.py --csv > citations.csv
```

Surfaces over-cited passages, missing cross-refs, and book-level
asymmetries in the apparatus.

### `scripts/bibliography.py` — extract every cited scholarly source

```bash
python3 scripts/bibliography.py                  # terminal summary
python3 scripts/bibliography.py --category Rabbinic
python3 scripts/bibliography.py --source "Targum"
python3 scripts/bibliography.py --html bibliography.html
```

Curated catalogue of patristic, rabbinic, modern, ANE, pseudepigraphic,
and translation sources (editable in the script). Counts each source's
mentions across the corpus and lists the citing notes.

### `scripts/glossary.py` — Hebrew/Greek word index

```bash
python3 scripts/glossary.py                      # terminal summary
python3 scripts/glossary.py --lang Hebrew
python3 scripts/glossary.py --search "tselem"
python3 scripts/glossary.py --html glossary.html
```

Parses `<strong>TRANSLIT (<em>ORIGINAL</em>) — 'gloss'.</strong>` openers
in `word`-kind notes and groups them by language with original-script
display.

### `scripts/release.py` — versioned save orchestrator

```bash
python3 scripts/release.py --version v26 --summary "..."          # dry-run
python3 scripts/release.py --version v26 --summary "..." --apply  # do it
python3 scripts/release.py --version v26 --summary "..." --apply --no-build
```

Probes current state, generates the ledger row + appendix stub, updates
the HANDOFF top status block, and (with `--apply`) builds the EPUB into
`Ethiopian_Bible_<version>_<timestamp>.epub`. The appendix stub is meant
to be fleshed out by hand afterwards.

---

## Multi-edition platform (v27)

The single master corpus emits N market-tuned EPUBs. Foundation: hierarchical
kind taxonomy in `content/kinds.yaml` (59 kinds across 14 categories) and
edition profiles in `content/editions.yaml` (8 tradition editions plus 2
standalone language Bibles).
Legacy kinds (`word`, `comm`, `source`, `parallel`) remain unchanged so all
existing 1,371 notes keep working.

### `scripts/build_edition.py` — per-edition EPUB filter+build

```bash
python3 scripts/build_edition.py --list           # editions and kind counts
python3 scripts/build_edition.py ethiopian-tewahedo
python3 scripts/build_edition.py catholic-study --output-dir releases/
python3 scripts/build_edition.py --all --version v27   # build all 5 editions
python3 scripts/build_edition.py reformed --dry-run    # report filter only
```

Filter resolution per kind (priority order): explicit `disabled_kinds` →
phase gate (`max_phase`) → explicit `enabled_kinds` → category gating
(`enabled_categories`). Legacy kinds always pass the phase gate. Stripped
markers and asides for disabled kinds are removed from the HTML; OPF gets
`dcterms:variant` and `dcterms:isVersionOf` metadata identifying the
edition build. Master corpus (`epub_working/`) is never modified — filter
operates in a tempdir.

### `scripts/validate_taxonomy.py` — sanity-check kinds/categories/editions

```bash
python3 scripts/validate_taxonomy.py            # full report
python3 scripts/validate_taxonomy.py --strict   # fail on warnings too
```

Catches duplicate codes, kinds pointing at missing categories, edition
profiles referencing missing kinds, CSS class collisions, etc. Run after
any taxonomy edit.

### Authoring with the extended taxonomy

```bash
# Add a tradition-specific note to demonstrate differential filtering:
python3 scripts/add_note.py gen 3 15 \
    --kind dist-mariological \
    --anchor "He will bruise your head" \
    --title "Marian" \
    --label "Marian." \
    --body "<strong>Protevangelium and the Marian reading.</strong> ..."

# Then rebuild — Reformed and Jewish editions will strip this note;
# Catholic, Tewahedo, and Scholarly editions will keep it.
python3 scripts/build_edition.py --all
```

---

## Authoring multiplier (v28a)

Pre-drafts candidate notes from public-domain reference corpora so the
user reviews and refines instead of starting from a blank page.

### `scripts/fetch_sources.py` — one-time PD corpus builder

```bash
python3 scripts/fetch_sources.py            # fetch missing only
python3 scripts/fetch_sources.py --force    # re-fetch
python3 scripts/fetch_sources.py --list     # status
```

Currently fetches Strong's Hebrew Dictionary (1894 PD; ~8,674 entries) and
the Treasury of Scripture Knowledge (1830s PD; ~344K cross-ref links).
Writes to `content/sources/` with `ATTRIBUTIONS.md` for licence trail.
Idempotent.

### `scripts/prospect.py` — generate candidate notes

```bash
python3 scripts/prospect.py gen 3                   # one chapter
python3 scripts/prospect.py gen --all-chapters      # whole book
python3 scripts/prospect.py gen 3 --only lang-hebrew,xref-citation
python3 scripts/prospect.py gen 3 --min-confidence 0.7
python3 scripts/prospect.py gen 3 --no-dedupe
```

Runs all detectors registered in `scripts/core/detectors.py` against
each verse. Detectors output `Candidate` records; prospect.py dedupes
against existing notes (heuristic: same kind-category + same anchor),
sorts, and writes a JSON review queue to
`content/candidates/<book>_ch_<n>.json`. A typical chapter produces
50–80 candidates.

Built-in detectors (extend by adding a class to detectors.py and
registering in `ALL_DETECTORS`):

- `HebrewWordDetector` → `lang-hebrew` candidates from a curated map of
  ~50 theologically-loaded Hebrew terms backed by Strong's lexical data
- `CrossRefDetector` → `xref-citation` candidates from TSK's
  community-vote-scored cross-references (top-N per verse)

### `scripts/promote.py` — review queue → real notes

```bash
python3 scripts/promote.py content/candidates/gen_ch_003.json
    # interactive walk: [s]kip / [p]romote / [v]iew / [q]uit

python3 scripts/promote.py content/candidates/gen_ch_003.json --list
    # status table only, no prompts

python3 scripts/promote.py content/candidates/gen_ch_003.json \
    --promote-id gen-3-15-041
    # non-interactive: promote one specific candidate

python3 scripts/promote.py content/candidates/gen_ch_003.json \
    --promote-top 5
    # non-interactive: promote highest-confidence N
```

Promotion writes a tuple to `content/notes/<book>.py` at the correct
sort position, picks the lowest free single-letter suffix on the
(chapter, verse), and updates the candidate's `status` field in the
queue so re-runs skip already-promoted items.

**Note on injection.** Promotion writes the source note. Translating
that to a rendered note in `epub_working/` is a separate downstream
step handled by the strategy-A or strategy-B injector — same chain
`add_note.py` uses. As of v28a, strategy-A injection is archived;
strategy-B books inject cleanly once their HTML is rendered.

---

## Build & maintenance

Three scripts handle the rest of the EPUB lifecycle. All three default to
**dry-run / read-only**; you must pass an explicit flag to write anything.

### `scripts/build_epub.py` — package the EPUB

```bash
python3 scripts/build_epub.py                      # default: ./Ethiopian_Bible.epub
python3 scripts/build_epub.py out/MyBible.epub     # custom path
python3 scripts/build_epub.py --no-bump out.epub   # skip metadata refresh
python3 scripts/build_epub.py --check              # validate only, no build
```

Produces a valid EPUB 3 (`mimetype` first and uncompressed, everything else
deflate-9). Replaces the legacy `build.sh`. By default also bumps two fields
in `content.opf` so the EPUB advertises the right modification date:

- `<dc:date>` → today (UTC, `YYYY-MM-DD`)
- `<meta property="dcterms:modified">` → now (UTC, ISO-8601)

Pass `--no-bump` to leave `content.opf` untouched.

### `scripts/check_manifest.py` — verify OPF/disk parity

```bash
python3 scripts/check_manifest.py            # report drift
python3 scripts/check_manifest.py --fix      # auto-add missing items
python3 scripts/check_manifest.py --strict   # exit 1 on any drift
```

Diffs `content.opf`'s `<manifest>` against the actual files in
`epub_working/`. Catches the common failure mode where a new chapter file is
added by hand but never registered in the manifest (which silently makes it
disappear from the published EPUB). With `--fix`, it auto-adds the missing
files with sensible default ids and media-types.

### `scripts/link_xrefs.py` — auto-link "cf. Genesis 1:1" references

```bash
python3 scripts/link_xrefs.py --dry-run             # preview
python3 scripts/link_xrefs.py --apply               # write changes
python3 scripts/link_xrefs.py --book gen --apply    # one book only
```

Wraps hand-typed cross-references like `cf. Luke 23:43` or `See Matt 3:16`
in `<a>` elements so readers can tap to navigate. Operates **only inside
`<aside class="note …">` and `<aside class="vnote">` blocks** — never the
PDF-derived verse text. Idempotent: re-running on already-linked content
does nothing. Verse-precision links go to `v-{code}-{ch}-{v}` anchors
(Strategy A books); chapter-level fallback to `ch-{bxx}-c{ch}` is used when
a verse anchor is unavailable (Strategy B books or out-of-range refs).

### `scripts/style_config.py` + `scripts/apply_style.py` — restyle the EPUB

```bash
# 1. Edit scripts/style_config.py to your taste:
#       MARGIN_SIDE         = "0.4em"
#       CHAPTER_FLOW        = "smart"
#       TOC_CHAPTER_FORMAT  = "num-only"
#       TOC_COLLAPSIBLE     = True
#       FONT_STACK          = '"IM Fell English", ...'
# 2. Apply:
python3 scripts/apply_style.py            # write changes
python3 scripts/apply_style.py --check    # preview only
python3 scripts/apply_style.py --revert-collapsible   # force-flat for testing
```

Single-command restyle: edit `style_config.py`, run `apply_style.py`, the
script patches `stylesheet.css`, `nav.xhtml`, and the visible TOC in
`index_split_000.html`.

The CSS edits live inside a sentinel-marked region — re-running is
idempotent and never disturbs hand-tuned CSS outside that region.

### Suggested release workflow

```bash
python3 scripts/verify.py            # 1. audit must be clean
python3 scripts/apply_style.py       # 2. restyle (no-op if config unchanged)
python3 scripts/check_manifest.py    # 3. manifest in sync
python3 scripts/link_xrefs.py --dry-run   # 4. (rarely) catch any new refs
python3 scripts/build_epub.py out/MyBible.epub   # 5. package
```

## File formats

### `content/books.yaml`

```yaml
books:
  - code: gen
    title: "The First Book of Moses, Genesis"
    bxx: "b00"
    bp: "bp-00"
    next_bp: "bp-01"
    ch_count: 50
    strategy: "A"
    id_prefix: "g"
    files:
      - "index_split_000.html"
      - "index_split_001.html"
      - "index_split_002.html"
```

`strategy: "A"` = deep-link verse anchors (`<a id="v-CODE-CH-V">`).
`strategy: "B"` = plain `<span class="vn">N</span>` markers.

### `content/kinds.yaml`

```yaml
kinds:
  - code: comm
    symbol: "◇"
    note_class: "note-comm"
    marker_class: "marker-comm"
    label: "Note"
    title_attr: "Note"
```

### `content/notes/<code>.py`

```python
NOTES = [
    (chapter, verse, suffix, anchor, kind, title, label, body_html),
    (12, 5, '', 'took Sarai', 'comm', 'Departure', 'Note',
     '<strong>The call answered.</strong> Abram acts on...'),
    ...
]
NOTES_<CODE> = NOTES  # backward-compat alias for legacy importers
```

Tuple fields:

| Field | Type | Meaning |
|---|---|---|
| `chapter` | int | chapter number |
| `verse` | int | verse number |
| `suffix` | str | `''` for first note on a verse; `'m'`, `'n'`, ... for additional notes |
| `anchor` | str | exact substring of WEB English in the verse to attach AFTER |
| `kind` | str | from `content/kinds.yaml`: `'word'`, `'comm'`, `'source'`, ... |
| `title` | str | tooltip on the noteref |
| `label` | str | bold label inside the aside (e.g. "Note", "Hebrew") |
| `body_html` | str | inline HTML; should lead with `<strong>Short title.</strong>` |

## Safety properties

- **No data destruction during the refactor.** Phase 1A/1B added new files only.
  Phase 1C modified `add_commentary.py` and `kings_session/strategy_b_inject.py`
  to import from `content/notes/` instead of inlining data — round-trip identity
  verified for all 13 books with notes. The 2026-05-06 sweep then removed the
  dead `kings_session/notes_data.py` shim and the `kings_session/notes/` stub
  directory (78 unused files), since nothing imported them.
- **Audit invariant**: `paired=N/N` (currently 1271/1271) holds across every
  Phase. `scripts/run.py` re-audits after applying any change.
- **The EPUB is never built automatically.** `python3 scripts/build_epub.py`
  remains a manual step per project policy.
- **Both `NOTES` and `NOTES_<CODE>` aliases exist** in every notes file —
  legacy importers continue to work.

## How the existing system relates

| Old | New | Status |
|---|---|---|
| `source_archive/add_commentary.py` BOOK_META + KIND_* dicts | `content/books.yaml` + `content/kinds.yaml` | New is authoritative; old loads from new |
| `source_archive/add_commentary.py` NOTES_<CODE> = [...] inlined | `content/notes/<code>.py` | New is authoritative; old imports from new |
| `kings_session/notes_data.py` NOTES_1KI / NOTES_2KI shim | `content/notes/1ki.py` + `2ki.py` | shim deleted 2026-05-06 (no active imports) |
| `kings_session/notes/notes_<code>.py` (78 stub files) | `content/notes/<code>.py` | directory deleted 2026-05-06 (no active imports) |
| `kings_session/inject_kings.py` (legacy A-injector) | `source_archive/add_commentary.py` | deleted 2026-05-06 (no call sites) |
| Hardcoded `KIND_SYMBOL/CLASS/MARKER` in both injectors | Loaded from `content/kinds.yaml` | Cutover complete |

## Troubleshooting

**"anchor not found inside <book> <ch>:<v>"** — the anchor substring isn't in
that exact verse. The error shows the actual verse text. Common causes:

- PDF double-spaces (e.g. `a  feast` vs `a feast`)
- Curly vs straight apostrophes (`'` U+2019 vs `'`)
- WEB vocabulary (`young goat`, `today`, `loving kindness`)

**"verse <ch>:<v> appears empty in the body"** — the verse contains only
markers, no text (Genesis 1:1 is one example; "In the beginning" is in 1:2).
Try the next verse.

**"injector failed (rc=2)"** — argument-name mismatch between the two
injectors: `add_commentary.py` uses `--book`, `strategy_b_inject.py` uses
`--code`. Internally `add_note.py` and `run.py` already handle this; you only
hit this if you call the injectors directly.

**Adding the first note to a previously-empty book** — works fine. The book's
stub file in `content/notes/` accepts the new tuple, the injector creates the
notes-section if it doesn't exist yet.

## Authoring + provenance (v28a)

### `scripts/fetch_sources.py` — one-time PD corpus builder

Downloads and caches public-domain reference corpora used by the prospecting
detectors. Two corpora cached:

- **Strong's Hebrew Dictionary** (Strong 1894, PD; 8,674 entries; ~1.9 MB) —
  feeds `HebrewWordDetector` (anchor → Strong's number → lemma + gloss).
- **Treasury of Scripture Knowledge** (1830s, PD; 344,799 cross-refs;
  ~5.4 MB) — feeds `CrossRefDetector` (verse → top-N parallel passages).

Run once on a fresh checkout:

```bash
python3 scripts/fetch_sources.py
```

Output goes to `content/sources/`. Re-run is idempotent.

### `scripts/prospect.py` — generate note candidates per chapter

Walks a chapter's anchors, runs each registered `Detector` over them, and
emits a JSON file of *candidate* notes (draft title / label / body /
attribution). Candidates are reviewed and either promoted (kept) or
dropped — they do not enter the corpus until promoted.

```bash
python3 scripts/prospect.py --book gen --chapter 3
# → content/candidates/gen_ch_003.json
```

### `scripts/promote.py` — review candidate notes; commit to corpus

Interactive CLI (or scriptable with `--promote-id` / `--promote-top N`)
that takes a candidate JSON and writes selected candidates into
`content/notes/<book>.py` as full 9-tuple notes (with attribution
preserved from the candidate's `source_attribution` field).

```bash
python3 scripts/promote.py content/candidates/gen_ch_003.json
python3 scripts/promote.py content/candidates/gen_ch_003.json --promote-id gen-3-15-041
python3 scripts/promote.py content/candidates/gen_ch_003.json --promote-top 5
```

### `scripts/attribute.py` — assign provenance to existing notes

Walks each book's notes file, infers an attribution string from each
note's body (regex pass detecting cited PD-era sources and named modern
scholars), and inserts it as the optional 9th tuple field. Skips notes
that already have attribution.

```bash
python3 scripts/attribute.py --book gen --dry-run
python3 scripts/attribute.py --book gen
python3 scripts/attribute.py --all-books
```

Modes: `--dry-run` (preview), `--book <code>` (single book),
`--all-books` (full corpus), `--interactive` (prompt per book).

### `scripts/core/config.py` — `NoteSpec` dataclass

The 9-field note schema (chapter, verse, suffix, anchor, kind, title,
label, body_html, attribution). `NoteSpec.from_tuple()` accepts both
8-field legacy and 9-field forms; `NoteSpec.to_tuple()` emits 8 when
attribution is None, 9 otherwise. Helper: `note_attribution(t)`.

### `scripts/core/detectors.py` — Detector registry

Defines the `Detector` base class and the two shipping detectors:

- **`HebrewWordDetector`** — anchor → Strong's H-number → lemma + gloss.
- **`CrossRefDetector`** — verse coordinate → TSK top-N parallel refs.

New detectors are added by subclassing `Detector` and registering in
`scripts/prospect.py`.

## See also

- `HANDOFF_README_v7.md` — full project handoff (the "where things stand" doc)
- `audit.py` — the original audit system; `verify.py` wraps it
- `PHASE_C10_PROCESS.md` — the original 10-step session workflow
