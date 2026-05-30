# Scope addendum — Tooling roadmap (Phases υ, φ, χ, ψ)

**Added:** 2026-05-07, after π.4-A.
**Origin:** strategic delegation — "Everything you can think of I want done.
Check though, there might already be a system in place for populating."

The user's instinct was correct: a substantial amount of the tooling I'd
sketched **already exists as CLI tools**. This addendum reframes the
roadmap around the actual gap, which is **CLI surfacing + corpus
expansion + performance**, not net-new feature invention.

---

## 1. Inventory of existing infrastructure

So future Claude / future user does not rebuild it.

### Note ingestion (auto-populate) — already complete as CLI

| Component                     | Path                          | What it does                          |
|-------------------------------|-------------------------------|---------------------------------------|
| PD source fetcher             | `scripts/fetch_sources.py`    | Downloads PD reference corpora        |
| Source loaders                | `scripts/core/sources.py`     | Lazy-load cached corpora              |
| Detector framework            | `scripts/core/detectors.py`   | Pluggable verse-scan detectors        |
| Candidate generator           | `scripts/prospect.py`         | Run detectors → JSON review queue     |
| Promotion tool                | `scripts/promote.py`          | Interactive: candidate → real note    |
| Single-note authoring         | `scripts/add_note.py`         | Programmatic note insertion           |
| HTML injector                 | `scripts/inject.py`           | Insert markers + asides into EPUB HTML|

**Today's detectors:** `HebrewWordDetector`, `CrossRefDetector` (2).

**Today's source corpora:**
`content/sources/strongs_hebrew.json` (Strong's Hebrew lexicon)
`content/sources/tsk_xrefs.json` (Treasury of Scripture Knowledge)
Both are placeholder/zero-byte today; `fetch_sources.py` populates them.

**What this means:** the auto-population pipeline I described in
brainstorming **already exists**. Adding a new PD source = one ingestor
function in `fetch_sources.py` + one detector class in `detectors.py`.
Adding a new detector = one class registered in `ALL_DETECTORS`. The
framework does the rest.

### Quality, coverage, and search — already exist as CLI

| Tool                       | Purpose                                       |
|----------------------------|-----------------------------------------------|
| `coverage.py`              | Per-book/chapter coverage heatmap (data)      |
| `verify.py`                | Audit wrapper, pre-flight friendly            |
| `note_quality.py`          | Per-note quality flags                        |
| `note_search.py`           | Substring/regex search across notes           |
| `note_diff.py`             | Diff between two note snapshots               |
| `citation_index.py`        | Inverse cross-ref graph; asymmetry detector   |
| `glossary.py`              | Auto Hebrew/Greek glossary builder            |
| `check_xrefs.py`           | Cross-ref validator                           |
| `check_a11y.py`            | Accessibility audit                           |
| `check_manifest.py`        | Manifest validator                            |
| `validate_taxonomy.py`     | Kind/category schema validation               |
| `bulk_edit.py`             | Find/replace across notes                     |
| `retag.py`                 | Bulk reclassify notes by kind                 |
| `link_xrefs.py`            | Auto-create xref links from text patterns     |
| `sync_html_kinds.py`       | Repair HTML classes after retag               |

### Translation extraction — partially complete

| Tool                       | Status                                        |
|----------------------------|-----------------------------------------------|
| `extract_translation.py`   | Working; KJV ingested (36,822 verses)         |
| `core/translations.py`     | Read API; lru_cached                          |
| Future PD translations     | Vulgate, Targum Onkelos, Peshitta, Ge'ez,     |
|                            | Sahidic Coptic — see ν.2.7 addendum           |

### Build pipeline — exists, mostly sequential

`build_edition.py`, `build_epub.py`, `build_onix.py` — rebuild from
scratch every time. Per-edition is independent so parallelism is
viable but not implemented.

---

## 2. Real gaps (what's actually missing)

Reframed against what exists, the genuine gaps fall into four clusters.

### Cluster υ — CLI surfacing (highest leverage)

The CLI tools listed above are not accessible from the web UI. A
schoolteacher / parish priest can't run `python3 scripts/prospect.py`.
Surfacing existing tools in the web app multiplies their value without
new feature invention.

```
υ.1  /sources console upgrade — show source corpus state, "fetch all"
       button that wraps fetch_sources.py via subprocess + status
υ.2  /prospect console — pick book + chapter, run detectors, review
       candidate queue inline (replaces CLI prospect.py + promote.py)
υ.3  /coverage console — render coverage.py output as a heatmap grid
       (rows = books in canon, cols = kinds; cells colored by density)
υ.4  /search console — note_search.py via web; faceted (book ∧ kind ∧
       edition ∧ source); also exposes citation_index.py asymmetries
υ.5  /bulk console — bulk_edit.py + retag.py with diff preview before
       apply; safety rails surfaced in UI
υ.6  /glossary console — glossary.py output as a navigable table;
       click a term → see every verse it appears in (Strategy-A nav)
```

Each of these is **wrapping an existing CLI** in a web view. Risk: low.
Effort: 1-2 turns each. Combined: completes the buyer-demo apparatus
("you can run every audit and bulk operation without touching a
terminal").

### Cluster φ — performance / bandwidth / scale

Genuine new infrastructure. Each item is concrete and measurable.

```
φ.1  Server-side caching of derived endpoints                  EASY WIN
       compute_matrix already lru_cached on file mtimes; extend
       same pattern to api_attribution_audit, api_edition_diff,
       api_covers (read-side), api_publisher_data. Cuts repeat-
       request latency to ~zero on those endpoints.
       Effort: 1 turn. Risk: none.

φ.2  Client-side IndexedDB cache for /api/customize
       Heavy payload (200KB+) loaded once per session today;
       cache it locally with If-Modified-Since revalidation.
       Drops perceived navigation time across customize/covers/
       sources to instant on warm cache.
       Effort: 1 turn. Risk: low (additive; falls back to fetch
       if no IndexedDB).

φ.3  Streaming / paginated /api/customize
       Today: one big payload. Could split into /api/customize/core
       (categories, kinds, editions — 30KB) + /api/customize/notes
       (loaded only by consoles that need note bodies).
       Effort: 1 turn. Risk: low.

φ.4  Incremental builds in build_edition.py
       Track per-source-file content hash + per-edition-config
       hash; only rebuild combinations whose inputs changed.
       60+ files × 5 editions × 60s → ~5s on a typical edit.
       Effort: 2 turns. Risk: medium (cache invalidation always is).

φ.5  Build pipeline parallelism (cross-edition)
       multiprocessing.Pool(5) for build_all over the 5 editions.
       Within an edition, I/O-bound (the PLAN doc already noted
       "concurrent inject is a wash"). Across editions, real wins.
       Effort: 1 turn. Risk: low (CPU-bound parts are independent).

φ.6  Image optimization on cover upload (folds into π.4-B)
       Auto-resize > 2000px → 1500px JPEG q85; halves typical
       cover upload size and EPUB embedded size.
       Effort: half turn. Risk: none.

φ.7  Pre-built EPUB cache keyed on (edition_id, config_hash)
       Buyer hits BUILD on a config that another buyer already
       built → instant download from cache. Useful once the
       buyer-demo URL is public.
       Effort: 1 turn. Risk: medium (cache invalidation).
```

### Cluster χ — corpus & detector expansion (the auto-populate multiplier)

This is the cluster that makes the buyer demo feel deep instead of
shallow. Each PD source ingested adds thousands of attributable
candidate notes.

```
χ.1  Strong's Greek lexicon ingestor + GreekWordDetector
       Counterpart to today's HebrewWordDetector, for NT verses.
       Sources: openscriptures Strong's Greek (PD).
       Yields: lang-greek candidate notes across NT.
       Effort: 1 turn (mirror of existing HebrewWordDetector).

χ.2  Matthew Henry's Commentary ingestor + CommentaryDetector
       Sources: ccel.org Matthew Henry (PD, 6 vols).
       Yields: comm-protestant candidate notes per pericope.
       Effort: 2 turns (parsing + chunking).

χ.3  Calvin's Commentaries ingestor
       ccel.org Calvin (PD).
       Yields: comm-reformation candidate notes.
       Effort: 2 turns.

χ.4  Catena Aurea ingestor (Aquinas's compilation of patristic
     commentary on the Gospels)
       PD; well-structured by chapter+verse.
       Yields: comm-patristic candidate notes (NT only).
       Effort: 2 turns.

χ.5  Rashi commentary ingestor
       PD Rashi text on Tanakh, well-structured per verse.
       Yields: comm-rabbinic candidate notes (Tanakh).
       Effort: 2 turns.

χ.6  TSK xref population — switch CrossRefDetector ON in earnest
       The TSK corpus is already cached; the detector exists; the
       scaling-up just hasn't been done. Running prospect → promote
       on every book yields ~30,000 xref candidates.
       Effort: 1 turn (scaling existing pipeline; no new code).

χ.7  Nave's Topical Bible ingestor
       PD topical concordance — yields topic-* candidate notes.
       Effort: 1 turn.

χ.8  BDB / LSJ lexicon ingestion (deferred — copyright varies)
       Brown-Driver-Briggs and Liddell-Scott-Jones are PD but the
       digital editions are not always; need careful sourcing.
       Effort: 2-3 turns. Risk: license diligence.
```

After χ.1 + χ.6 + χ.7 alone, the corpus could grow from 1,381 notes
to 10,000+ — without a single hand-authored note.

### Cluster ψ — preview + pre-flight (buyer-demo polish)

Genuinely new, not surfacing existing CLIs.

```
ψ.1  Live EPUB preview — render one chapter as the reader will see it
       Inline iframe in /customize or /wizard; uses the build pipeline's
       per-file output, applies the active theme + popup-language config
       + popup translation. Click verse markers to test popups in-place.
       This is the single biggest "wow" moment for non-technical users.
       Effort: 2-3 turns. Risk: medium (theme + popup composition).

ψ.2  Pre-flight checklist — one button, all audits
       Consolidates verify.py + check_xrefs.py + check_a11y.py +
       attribution audit + canon validation + cover completeness
       + popup-translation coverage. Runs all, surfaces problems
       as a checklist with click-to-jump links.
       Should run before BUILD. Optional pre-build gate.
       Effort: 1-2 turns. Risk: low (composes existing tools).

ψ.3  Live build progress + log streamer
       Today BUILD is opaque; user clicks and waits. Replace with
       a SSE-streamed log + per-phase progress bars (extracting,
       filtering, packaging, validating). Even with the same
       runtime, the UX feels 3× faster.
       Effort: 1-2 turns. Risk: low.

ψ.4  In-browser EPUB validator — epubcheck via pyodide / WASM
       Optional; run epubcheck locally without a network roundtrip.
       Lots of edge cases on the server side.
       Effort: 3+ turns. Risk: high (epubcheck is a Java tool).
       DEFERRED until ψ.1-3 ship.
```

---

## 3. Recommended sequence

Per CLAUDE_PROJECT_RULES.md §3 (safest/most-foundational first;
buyer-demo value second; bundle paired phases):

```
IMMEDIATE — already in flight
  π.4-B    Cover upload backend + /covers UI                NEXT (active)

EASY WINS — small, visible, foundational
  φ.1      Server-side caching (audits + diffs + covers)    THEN
            ~ 30 min real work; visibly faster across consoles.
  ψ.2      Pre-flight checklist                              THEN
            ~ Composes existing audits; one new console.
            Buyer demo gains a "ship-ready check" button.

MULTIPLIER PUSH — corpus expansion (auto-populate becomes real)
  χ.1      Strong's Greek + GreekWordDetector
  χ.6      TSK cross-ref scaling (no new code, just runs)
  χ.7      Nave's Topical
  → After this trio, corpus jumps to 10,000+ notes. Buyer
    demo no longer feels like a tech demo, feels like a real
    Bible.

WOW MOMENT
  ψ.1      Live EPUB preview — the buyer-demo crown jewel
            Bigger than φ.* combined for the demo's emotional
            impact. Schedule once corpus is dense (so preview
            shows real apparatus, not empty pages).

UI SURFACING
  υ.1      /sources console upgrade
  υ.3      /coverage heatmap
  υ.4      /search console (faceted)
  υ.2      /prospect console (auto-populate UI)
  υ.5      /bulk console (find/replace + retag)
  υ.6      /glossary console
  → Each surfaces one existing CLI tool. Independent; can
    parallelize across turns.

PERFORMANCE — once base UX is solid
  φ.2      IndexedDB client cache
  φ.3      Streaming /api/customize
  φ.4      Incremental builds
  φ.5      Build parallelism
  φ.6      Image optimization (folds into π.4-B)
  φ.7      Pre-built EPUB cache (when buyer URL goes public)

POLISH
  ψ.3      Live build progress streamer
  ψ.4      In-browser epubcheck (deferred)

CORPUS EXPANSION (PHASE 2)
  χ.2      Matthew Henry's Commentary
  χ.3      Calvin's Commentaries
  χ.4      Catena Aurea
  χ.5      Rashi
  χ.8      BDB / LSJ (license-permitting)

  + τ.2 from popup-languages addendum:
    Vulgate, Targum Onkelos, Peshitta, Ge'ez, Sahidic Coptic
    translations
```

## 4. What this scope does NOT mean

- "Everything in one session" — no. This is months of work taken in
  the right order. A single turn ships one or two phases.
- "Rebuild what already works" — no. The CLI tools above are the
  source of truth; web consoles WRAP them, not replicate them.
- "Build before checking" — no. Per the user's wisdom in this turn:
  always verify what exists before scoping new work.

## 5. Where this fits in the master plan

Inserted after the π.4 cluster in `dev/PLAN_2026-05-07.md`. The
deferred `ROADMAP_FUTURE.md` items (Web UI for note editing — already
shipped; cross-edition diff viewer — already shipped as ξ.5) are
already out of date; this addendum supersedes the deferred list.
