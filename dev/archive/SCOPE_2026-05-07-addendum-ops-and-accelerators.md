# Scope addendum — Operations, accelerators, and depth (Phases ν / ψ / χ / ω)

**Added:** 2026-05-07, after ψ.2.
**Origin:** strategic delegation — "Add everything you said, find the
most logical way to add this to the scope, build any tools / injectors
/ security to save time while working toward completion."

The user has handed maximum autonomy and explicitly requested
infrastructure that accelerates the rest of the work. This addendum
captures every suggestion from the prior brainstorm turn plus the
meta-tooling needed to ship them efficiently, organized by existing
phase clusters where they fit and one new cluster (ω) for operations.

---

## 1. Sequencing principle

Per CLAUDE_PROJECT_RULES.md §3, the order below is governed by:
foundational + bandwidth-efficient first, then user-facing features
that compound on the foundation, then polish. Meta-tools (anything
that makes future work faster) ship before the user-facing features
that benefit from them.

## 2. Phase assignments

```
ν.4   Edition cloning                     features extending ν customization
ν.5   Change-impact preview before save
ν.6   Reader experience (chapter labels)  shipped during this addendum's
      ν.6.1 Book ToC ornament UI            implementation; properly tracked
                                            here for continuity

ψ.3   Corpus progress bar (omnipresent widget)    buyer-demo polish
ψ.4   Translation comparison view (/compare)
ψ.5   Sample-chapter PDF export
ψ.6   Operator dashboard (/ops)
ψ.7   Edition template starter packs

χ.9   Note conflict detector                      quality/corpus extension

ω.0   Meta-tooling and developer accelerators     OPS cluster (NEW)
ω.0.1 Rules linter (scripts/lint_rules.py + preflight integration)
ω.0.2 Console scaffolding helper (scripts/scaffold_console.py)
ω.0.3 Test-fixture sharing module (tests/fixtures/)

ω.1   Backup restore UI
ω.2   Build-all-editions one-click
ω.3   API reference page (/api/help auto-generated)
ω.4   Auth gating on mutation endpoints (admin token)
ω.5   Multi-user / reviewer roles                 deferred (not urgent)
```

ω is fitting for the operations / safety cluster — the last Greek
letter, signaling "things that mature a project from prototype to
production."

## 3. Each phase, briefly

### ν.4 — Edition cloning

**Why now**: foundational for ψ.7 (templates), ω.5 (reviewer workflows),
and any "what-if" experimentation. Also: the platform's whole pitch is
"buyer makes their own edition" — clone is the most natural starting
verb for that flow.

**Spec**:
- New API: `POST /api/editions/clone` with body `{source_id, new_id, new_title}`
- Validates `new_id` is fresh, kebab-case, no whitespace
- Copies the full edition record from `editions.yaml` — every field,
  including `popup_languages_per_book` and `book_covers` (encoded
  list format means a deep copy is a shallow value copy)
- Optionally clones cover files on disk: source `content/covers/<src>/...`
  → new `content/covers/<new>/...`. Default: don't clone (publisher
  uploads their own); flag to opt in.
- New UI affordance on `/customize`: "Clone this edition →" button per
  edition card → modal with `new_id` + `new_title` fields
- Cross-link in `/publisher` and `/wizard` too — natural starting points

**Edge cases**: clone of an edition that has no per-book covers should
not crash on cover-clone step; clone with `clone_files=true` should
ensure_backup if the destination already exists.

**Tests**: round trip clone preserves every field; rejects duplicate id;
rejects malformed id; clone with files=true copies disk artifacts;
clone deep-copies decoded popup_languages_per_book (mutating the clone
must not affect the source).

### ν.5 — Change-impact preview before save

**Why**: Today saving a kind-toggle change is opaque — publisher
clicks save, build EPUB, finds out 247 notes vanished. Preview the
diff first.

**Spec**:
- New API: `POST /api/editions/<id>/preview-impact` with the same
  payload as `api_save_edition_meta`
- Returns: `{notes_added: int, notes_removed: int, kinds_added: [...],
  kinds_removed: [...], by_book: {<code>: {added, removed}}}`
- Computed in-memory; nothing written
- UI: "Preview impact" button next to "Save" on `/customize`
- Renders a small diff card: "247 notes will be removed across these
  books: gen, exo, …"

**Tests**: preview matches actual save delta; preview with no changes
returns all zeros; per-book diff correct.

### ν.6 — Reader experience (chapter labels + reader's TOC display)

**Already shipped** during this addendum's implementation; documented
here so the scope tracking matches reality. The work was found
mid-conversation when a test-count audit surfaced 7 unfamiliar tests;
the user correctly identified that I was mid-UI-task on this when an
unrelated topic interrupted.

**What's in ν.6** (complete):
- `chapter_number_format`: `digit` | `word` | `word_chapter`
  ("42" / "Forty-Two" / "Chapter Forty-Two")
- `chapter_number_decoration`: 10 styles — `plain`, `dashes`,
  `em_dashes`, `stars`, `asterisks`, `bullets`, `ornament` (❦),
  `fleurons` (❧), `wave`, `double_lines`
- Helpers: `chapter_number_to_word(n)` covers 1–150;
  `format_chapter_label(n, style)`; `decorate_chapter_label(label, deco)`
- `apply_chapter_decoration(epub_dir, edition)` rewrites body chapter
  headings; wired into `build_edition.py` between canon-filtering and
  copyright-page injection. No-op on default settings (back-compat).
- `/customize` "Reader experience" card with chapter format + chapter
  decoration selects (each option shows an inline preview)
- Schema-only fields whose build-pipeline rendering is queued for a
  follow-up phase: `reader_toc_collapsible`, `reader_toc_default_open`
  (the in-book ToC's existing `<details>` already supports these
  semantically; the build pass that conditionally adds/removes the
  `open` attribute is queued).

### ν.6.1 — Book ToC ornament UI (this turn)

**Why now**: pairs naturally with ν.6's deferred reader_toc fields —
same render surface (the in-book ToC) and same publisher-side decision
("how does this edition's ToC look?"). Adding the picker now means
the eventual single render-pass phase has all its inputs collected.

**Spec**:
- New `BOOK_TOC_ORNAMENTS` registry in `build_edition.py`; entries are
  `(preview_glyph, description)` tuples
- 6 starter options: `none`, `square`, `cross_latin`, `cross_lalibela`,
  `star_david`, `fleur` — covers every retail SKU's tradition
  appropriately. Adding more is a one-line change.
- `book_toc_ornament` field validated in `api_save_edition_meta`;
  unknown values rejected with the list of valid options
- Picker added to the "Reader experience" card on `/customize`,
  between the chapter controls and the reader_toc checkboxes; option
  labels include the preview glyph plus a tradition tag
- Italic deferral note updated to mention book_toc_ornament alongside
  reader_toc as queued for the same follow-up phase

**Critical design choice**: tradition-correct rather than guessed.
The platform serves Catholic, Reformed, Jewish, Ethiopian, and
scholarly editions. Rendering a Latin cross in a Hebrew Bible would
be a serious commercial mistake; the picker forces an explicit
publisher choice rather than a tradition-blind default.

**Tests**: ornament registry contains the 6 required entries with
the right shape; api_save accepts known values + persists; rejects
unknown values with helpful error; UI surfaces all options + tradition
tags; deferral note mentions ornament.

**Deferred (same follow-up phase as reader_toc_*)**: the build-pipeline
`apply_reader_toc_transforms` pass that injects the chosen ornament
SVG before each book's `<summary>` and conditionally adds the `open`
attribute based on `reader_toc_default_open`.

### ψ.3 — Corpus progress bar (omnipresent widget)

**Why**: explicit north-star is 35–40K notes. Today the goal is in docs.
Bring it on-screen so every console hit is a tiny reminder of the
trajectory.

**Spec**:
- Small fragment in every console header: `1,381 / 35,000 (4%)` with
  a thin progress bar
- Reads from `compute_matrix()` (already cached); zero overhead per
  page load beyond what's already happening
- Insertion mechanism: a single `<span id="corpus-progress">` slot in
  each header HTML, hydrated by a tiny shared script bundle
- Pulls the target number from `dev/SESSION_STATE.md`'s north-star
  block? No — that's a docs file. Pull from a constant in
  `scripts/web.py`: `CORPUS_TARGET = 35_000`

**Tests**: widget appears in all 10+ consoles' HTML; progress
percentage computed correctly at known counts; gracefully shows
"loading…" if the API call fails.

### ψ.4 — Translation comparison view (/compare)

**Why**: buyer-demo gold. With τ.1 (KJV) shipped and τ.2 future
translations queued, side-by-side rendering becomes a compelling
preview without needing a full EPUB build.

**Spec**:
- New console `/compare`
- Inputs: pick book + chapter; select 2–3 translations from
  `translations.list_translations()` plus the original-language
  data we have (Hebrew/Greek for OT/NT)
- Renders a verse-by-verse table; one column per selected source
- Useful side-effect: this is the "EPUB preview" lite — sets the
  pattern that ψ.1 (full live preview) will extend

**Tests**: page renders; selected translations all appear; missing
verses show as `—`; canonical-order verse rows.

### ψ.5 — Sample-chapter PDF export

**Why**: lets publishers share preview material on Substack / pitch
decks without committing to a full EPUB build. Lower friction = more
demos.

**Spec**:
- New endpoint: `POST /api/sample/<edition_id>?book=gen&from=1&to=3`
  → returns a small PDF
- Reuses the build_edition pipeline's filter logic; emits to PDF
  rather than EPUB. PDF library: stdlib only is hard; `reportlab` is
  the standard choice but adds a dependency. Decision deferred —
  evaluate when we get there. May land as HTML-only first, with PDF
  as ψ.5.1 follow-up.

**Tests**: endpoint returns 200 + bytes; selecting an out-of-canon
book returns a clear 404.

### ψ.6 — Operator dashboard (/ops)

**Why**: single "are we OK?" page for the project owner. Low priority
but very high value when it's needed.

**Spec**:
- New console `/ops`
- Sections: test count + pass/fail (from a stored last-run timestamp),
  last save tag, latest CHANGELOG entry, corpus count + δ since last
  build, server uptime, on-disk free space
- Every section is a tiny composed call to existing data; no new
  computation engine
- Mostly read-only; one "run preflight now" button

**Tests**: page renders; each section's data source is wired correctly.

### ψ.7 — Edition template starter packs

**Why**: a buyer who doesn't know what to build needs concrete starting
points. "I want an Anglican BCP edition" → click → done.

**Spec**:
- A folder `content/edition_templates/` with one YAML per template:
  Anglican BCP, monastic daily office, school-friendly NRSV-style,
  scholarly-academic-with-apparatus, etc. Each is a partial
  `editions.yaml`-style record.
- New API: `GET /api/edition-templates` list; `POST /api/editions/from-template`
  with body `{template_id, new_id, new_title}` clones the template
  via the ν.4 cloning machinery
- UI: a "Start from template…" button on the wizard's first step

**Tests**: each template parses; templates can be applied to create
new editions; created editions pass validation.

### χ.9 — Note conflict detector

**Why**: as corpus grows past 10K via χ.6/χ.1/χ.7, two PD sources may
produce contradictory notes at the same verse + same kind. Surface
those for editorial review.

**Spec**:
- Composes existing notes_io with a new pass: group notes by
  (book, chapter, verse, kind), flag groups with ≥2 notes from
  different sources where text similarity is below a threshold
- Surfaces in `/audit` as a new tab "potential conflicts"
- Cheap: groupby on the existing in-memory notes; no new corpus
  scan

**Tests**: known-conflict fixture surfaces; same-source dupes don't;
threshold tuning produces sensible output.

### ω.0 — Meta-tooling cluster (the axe-sharpeners)

**ω.0.1 — Rules linter** (`scripts/lint_rules.py`)
- Automated check that the project's own rules hold
- Verifies: every console links to every other (§6.2); every per-book
  API filters by canon (§6.1); every encoder produces canonical-
  order output; every Markdown addendum referenced in the index;
  every memory rule has a corresponding rules-doc section
- Integrates with preflight: ψ.2 gains a new "Rules compliance" check
  that runs the linter; failures show as ⚠ in the dashboard
- This is the highest-leverage meta-tool: it catches drift the moment
  it's introduced, instead of letting it accumulate

**ω.0.2 — Console scaffolding helper** (`scripts/scaffold_console.py`)
- Generate a new console's HTML constant + nav scaffolding + the
  cross-link insertion across all existing consoles, in one command:
  `python3 scripts/scaffold_console.py NEWNAME --title "New Thing"`
- Saves ~30 min per new console; relevant given ψ.3, ψ.4, ψ.6, ω.1
  are all new consoles

**ω.0.3 — Test-fixture sharing module** (`tests/fixtures/`)
- Hoist `_make_png`, `_multipart_body`, etc. out of TestEditionMeta
  and TestCovers into a shared module. Today they're duplicated;
  duplication grows as more endpoints accept binary uploads.

### ω.1 — Backup restore UI

**Why**: `.backups/` already exists with timestamped snapshots
(every atomic_write triggers an `ensure_backup`). Surface it.

**Spec**:
- New endpoint: `GET /api/backups/<file>` lists backups for a file
- New endpoint: `POST /api/backups/<file>/restore` with `{snapshot_id}`
- UI: small "version history" link on the publisher / customize / covers
  consoles → modal listing backups with timestamps + "restore" buttons

**Tests**: list returns; restore swaps content; cache invalidates.

### ω.2 — Build-all-editions one-click

**Why**: today `/export` is per-edition; a buyer wants to ship all 5.

**Spec**:
- New endpoint: `POST /api/build-all` runs build_edition for every
  edition, packages outputs into a single zip
- UI: "Build all 5 editions" button on `/export`

**Tests**: returns multi-edition zip; per-edition errors surface
without aborting the whole batch.

### ω.3 — API reference page (auto-generated)

**Why**: `/api/*` surface has grown; future Claude or future dev
benefits from a single doc page enumerating every route.

**Spec**:
- New console `/api/help` (HTML page, despite the path)
- Auto-generated from a route registry built at startup by
  introspecting the `do_GET` / `do_POST` / `do_PUT` / `do_DELETE`
  methods OR by maintaining a small declarative table
- Per route: method, path, brief description, sample payload

**Tests**: every actual route appears in the registry; sample
payloads parse.

### ω.4 — Auth gating on mutation endpoints

**Why**: today every endpoint is unauthenticated. Local-only is fine
for now; if this ever gets hosted publicly, an unauthenticated upload
endpoint is a serious problem. A tiny env-var-based admin token now
costs almost nothing and unlocks public hosting later.

**Spec**:
- If env var `EBIBLE_ADMIN_TOKEN` is set:
  - Every POST / PUT / DELETE on `/api/*` requires an `Authorization:
    Bearer <token>` header
  - Mismatch → `401 Unauthorized`
  - GETs remain unauthenticated (read-only is fine)
- If env var unset: behavior unchanged from today (backward-compatible
  default)
- Document in `dev/CLAUDE_PROJECT_RULES.md` §10 ("What this project
  is NOT" → add: "Not unauthenticated when hosted publicly — set
  EBIBLE_ADMIN_TOKEN")

**Tests**: with token set, missing header → 401; wrong token → 401;
correct token → 200; with token unset, all endpoints behave as before.

### ω.5 — Multi-user / reviewer roles (deferred)

Out of scope for now. Re-evaluate when the project hits a real
multi-editor use case.

## 4. Recommended sequence

```
THIS TURN
  ν.4    edition cloning              foundational; unlocks ψ.7, ω.1, χ.9
  ω.4    auth gating                  cheap; protects future deploys
  ω.0.1  rules linter                 catches drift on every push

NEXT TURN
  ψ.3    corpus progress bar          tiny, every-console psychological lift
  ν.5    change-impact preview        prevents save regret
  ω.0.2  scaffold tool                accelerates next 5+ consoles

LATER
  ψ.4    translation comparison
  χ.6    TSK xref scaling             biggest corpus jump
  ψ.7    edition templates
  ω.1    backup restore UI
  ω.0.3  test fixture sharing
  ω.2    build-all-editions
  ψ.5    sample-chapter export        (PDF dep decision needed)
  ω.3    API reference page
  ψ.6    operator dashboard
  χ.9    note conflict detector

DEFERRED (until pulled forward)
  ω.5    multi-user / reviewer roles
  ψ.1    live EPUB preview
  π.4-C  per-book covers in built EPUB
  τ.2    future translations
```

## 5. Where this fits in the master plan

Replaces the "deferred / optional" tail of `dev/PLAN_2026-05-07.md`
with the sequence above. Master PLAN updated separately to mirror
this ordering.
