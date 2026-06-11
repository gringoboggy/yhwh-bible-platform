# The Matrix — data-flow & integrity map

> **Two companion maps:** THIS file maps the **data-flow** (config → matrix → build →
> inject → ingestion + the base-HTML structure). For the **file/folder index** —
> "where does any directory/file live and what's in it" — see **`dev/REPO_MAP.md`**
> (regenerate/verify with `py dev/trace_repo.py`; the pre-commit `repo_map_complete`
> check fails-soft if a new top-level dir is undocumented). To search note *content*,
> use the SQLite+FTS index (`scripts/core/corpus_index.py` / `scripts/note_search.py`).
>
> Map for humans + future Claude. "The matrix" = the **editions × kinds count
> grid** (`scripts/core/matrix.py`): "if I shipped edition X now, how many notes
> of each kind would appear?" It is anchored on the same edition profiles
> (`content/editions.yaml`) that drive the **build pipeline** — so the matrix and
> the EPUB build are two consumers of one source of truth.
>
> Counts (2026-05-21 rebuild; notes re-counted 2026-06-02): **11 editions · 5 canons
> · 15 categories · 72 kinds · 87 books · 14 translation dirs · 91,733 notes**.
> (Was 70 kinds / 52,973 notes on 2026-05-20; `dict-easton` added + Nave's rebuilt +
> Easton's ingested — see "Reference-corpus ingestion" below.) Re-verify with
> `dev/trace_matrix.py`; integrity target: **0 unresolved references.**

## Top → bottom (source leads to output)

```
CONFIG  (content/*.yaml)  — the rows, columns, and leaves
  editions.yaml ......... 11 edition profiles      → the matrix ROWS
  kinds.yaml ............ 72 kinds → category       → the matrix COLUMNS
  categories.yaml ....... 15 categories             (column groups; AI-gate via enable_ai_notes)
  canons.yaml ........... 5 canons → book-code sets  (book filter; ethiopian = 87-book superset)
  books.yaml ............ 87 books                   (canonical spine / order)
  translations/<id>/ .... 14 dirs                    (base_translation, popup_translation)
  traditions / themes / customization / source_dates / edition_templates/* / scenarios/*
        |
        v
LOADERS  scripts/core/config.py   (lru-cached: load_editions/books/kinds/categories, *_by_id/code)
        |
        +───────────────────────────────────────────────+
        v                                                 v
MATRIX  scripts/core/matrix.py                       BUILD  scripts/build_edition.py
  compute_matrix()                                     compute_enabled_kinds()   <== MIRRORS matrix
    -> core/corpus_index.compute_matrix_indexed()      filter_html()  (canon book-splice + kind
    -> Matrix(per_chapter, edition_enabled_kinds)        filter + tradition labels + time filter
    derived views: enabled / potential / per_book        + popup languages/translation)
        |                                              patch_opf() / render_copyright_page()
        v                                                _apply_popup_languages_and_translation()
  CONSUMERS of the grid:                                    |
    web.py (customize / symbol-toggle UI)                   v
    scripts/matrix.py (CLI)                             build_epub.py -> covers/ + title_pages/
    api/{customize,editions,exports,preflight}.py            -> EPUB  (the actual output)
    dashboard.py, core/snapshots.py, edition_templates.py
        |
        v
VALIDATORS (gate everything):
  api/preflight.py · validate_schemas.py · validate_taxonomy.py
  lint_rules.py (pre-commit hook) · check_manifest.py · check_content.py
  dev/trace_matrix.py  (this map's reference-tracer)
```

## Bottom → top ("I see X in the output — where did it come from?")

- **A note in the EPUB** <- `content/notes/<book>.py` (carries a `kind` code) <- survived
  `build_edition.filter_html` because `kind ∈ edition's enabled-kinds` (= `enabled_categories`'
  kinds + `enabled_kinds` − `disabled_kinds` − AI-gated unless `enable_ai_notes`) **and**
  `book ∈ canons.yaml[edition.canon].books`.
- **A book present / spliced out** <- `canons.yaml[edition.canon].books` (a subset of `books.yaml`).
- **A verse popup** <- `popup_translation` (-> `translations/<id>/`) + `popup_languages_default`
  / `popup_languages_per_book`.
- **Hebrew/Greek/… text inside a verse popup** <- the baked `translations/<id>/<book>.py`, sourced
  per registered version by `generate_verse_popups.assemble_versions_for_verse` (registry order;
  baked only when `popup_versions.bakes_now`). **Translation ingestion** is per-source:
  `scripts/extract_<id>.py` (`extract_wlc_morphhb.py` — morphhb OSIS → `<em>`-per-word; `extract_lxx_swete.py`
  — Swete CSVs → PLAIN Greek; `extract_byzantine_nt.py` — byztxt CSV → plain accented Greek) →
  `scripts/core/versification.py` remaps the source's own numbering to **canonical KJV** (the
  `popup_versions.normalize_coord` seam) → per-book modules keyed by canonical coords, guarded at
  ingest by `canonical_verse_counts.coord_in_canonical_extent`. The remap is source-specific:
  `wlc_to_kjv_map` reads morphhb `VerseMap.xml` (WLC: Gen 31/32, Psalm superscriptions);
  `lxx_swete_to_kjv` is a hand-built map (LXX: Psalms renumber, Jeremiah's OAN reorder, Theodotion
  Daniel's Additions, the 1 Kings 20↔21 swap, Proverbs' 24/29 reorder, Esther's omitted Additions —
  every reorder content-aligned against KJV, not memory); `byzantine_to_kjv` is near-identity (the NT
  is KJV-standard) + the Romans-doxology reorder; `vulgate_to_kjv` (shared by `douay` + `vulgate`)
  is TABLE-DRIVEN — segments generated from the Copenhagen Alliance `vul.json` (composed
  vul→org→KJV), then gate-verified against the real Douay text (`_vg_verify` SHIFTS=0); `tob/jdt/sir`
  omitted (divergent recension), Daniel additions → `paz/sus/bel` cross-book, Esther additions
  auto-omit. **WLC = 39-book / 23,142-verse; LXX-Greek (Swete) = 39-OT / 22,893-verse (`vnote-greek`
  8,601→22,812); Greek-NT (Byzantine) = 27-NT / 7,953-verse (`vnote-greek-nt` 0→7,951); Arabic
  (Van Dyck) = 66-book / 31,102-verse; JPS (1917) = 39-book / 23,145-verse; Douay-Rheims + Clementine
  Vulgate = 74-book / ~33,344-verse body each (`vnote-douay`/`vnote-vulgate` +31,866/+31,865 baked,
  2026-05-23)**. **Phase E (2026-05-26)** added the Clementine **77th**-book spine: the la.wikisource
  deuterocanonical appendix `man`/`1es`/`2es` (Vulgate 74→77 books, +1,117 v → 34,460; `vnote-vulgate`
  baked on those 3 books only, additive-proven). The appendix does NOT route through `vulgate_to_kjv`'s
  Douay-tuned segments (they misalign la.wikisource's numbering — proven 1es 1:13); instead
  `scripts/extract_vulgate_appendix.py` carries its own verified per-chapter `_JOIN_PREV` correction
  table and DEFERS (omits + flags) 3 multi-shift name-list chapters (`1es` 5/8, `2es` 14). `brenton-en`
  is the remaining registry seed not yet baked.
- **Cover / OPF metadata** <- `cover_image`, `authors`, `bisac_codes` -> `patch_opf`.
- **A count cell in the matrix UI** <- `matrix.compute_matrix().enabled[ed][kind]` <- `per_chapter`
  <- `notes_io.load_notes(notes/<book>.py)`.

## Variable trace table (editions.yaml field -> resolves against -> consumed by)

| field | resolves against | consumed by | trace |
|---|---|---|---|
| `canon` | `canons.yaml` ids | matrix book-scope; build book-splice | OK 5/5 |
| `enabled_categories` | `categories.yaml` ids | matrix `_enabled_kinds_for_edition`; build `compute_enabled_kinds` | OK |
| `enabled_kinds` / `disabled_kinds` | `kinds.yaml` codes | same (both paths) | OK |
| `enable_ai_notes` | gate for `AI_DRAFTED_KINDS` (`comm-ai`) | matrix + build kind gate | OK |
| `popup_translation` | `translations/<id>/` | build `_replace_verse_popup_translation` | OK (`kjv`, `*-en`, `""`) |
| `base_translation` | `translations/<id>/` | standalone build body (deferred τ.G.x.*) | OK |
| `popup_languages_default` / `_per_book` | language ids | build `_resolve_popup_languages` → `_apply_popup_languages_and_translation` | unset → `DEFAULT_POPUP_WITNESSES` (5; `kjv` excluded — #6); last-resort English floor where no witness exists (RSC-012 guard); not ref-checked (lang names) |
| `cover_image` | `content/covers/` | `patch_opf` / covers | OK (empty on standalones = skipped) |
| `max_phase` | phase tag on kinds | phase filter | not checked by tracer |
| `traditions_default` / `_per_book` | `traditions.yaml` | build tradition filter | not checked by tracer |

### Presentation / reader-styling fields (Wave 2–3 — editions.yaml; unset == default)

| field | resolves against | consumed by | status |
|---|---|---|---|
| `title_page_style` | enum `{full-bleed, framed}` | build `apply_title_pages` (3432) + `patch_opf_book_images` (3500) | shipped 2026-05-25; **default flipped `full-bleed`→`framed` (RX P2, 2026-06-05 — full-bleed `position:absolute` overlays don't render on Kobo)** |
| `book_covers` (per-edition × per-book) | `content/covers/` override | `apply_title_pages` art resolution: override → `_book_defaults/<code>.jpg` → text-only | shipped 2026-05-25 |
| `cover_template` | `core/covers.COVER_TEMPLATES` (25 stems = 5 designs × 5 colours) | `api_apply_cover_template` (api/covers 72) → `_compose_cover` → `covers/<id>.jpg` | shipped 2026-05-25; default `""` |
| `verse_popup_style` | enum `{cards, stack}` | build `apply_verse_popup_style` (1395) — CSS append in `build_one` | shipped 2026-05-25; default `cards` |
| `note_popup_style` | enum `{chip, pills}` | build `apply_note_popup_style` (1432) — CSS append in `build_one` | shipped 2026-05-25; default `chip` |
| `marker_style` | enum `{numbers, badge}` | numbers: `inject.build_marker`/`build_aside` at source + `build_one` `renumber_markers` post-pass (gapless after canon). **badge: `apply_badge_markers` build-time post-pass (~1797) collapses a verse's per-note markers→ONE count-badge + merges its asides→ONE per-verse `verse-notes` footnote (native popup, no JS); base `epub_working/` untouched** | shipped 2026-05-25; **`badge` shipped + made DEFAULT (RX P5, 2026-06-05); `numbers` switchable** |
| `reader_file_split` | bool, `reader_file_split_target` (int) | **build-time `apply_file_split` post-pass (~2293) — runs LAST in `build_one` before zip: splits the 2–5 MB `index_split_*.html` into ~0.4 MB pieces (stack-aware cuts at book/chapter/verse boundaries), rewrites every cross-file href via a global id→piece map, regenerates the OPF manifest+spine + nav.xhtml + toc.ncx; base `epub_working/` untouched** | shipped RX P4b 2026-06-05; **default ON** (`DEFAULT_READER_FILE_SPLIT`); Kobo perf fix |
| `reader_toc_collapsible` / `reader_toc_default_open` / `book_toc_ornament` | bool / bool / enum | `apply_reader_toc_transforms` (~2268) — `false` unwraps the in-content `<details>` ToC accordion into a flat `<p class="toc-book-label">`+chapter `<ol>` (Kobo can't render `<details>`/flexbox) | shipped ν.6.x; **all 11 editions pinned `reader_toc_collapsible:false` (RX P4a, 2026-06-05) for the flat Kobo-safe ToC** |
| `style_config.EMBED_FONT_PATHS` | font files in `epub_working/fonts/` | `patch_opf_fonts` (~2962) registers manifest items; CSS `@font-face` (range-scoped) | shipped RX P3 2026-06-05: 3 Cardo faces (Latin/Greek/Hebrew) + Noto Serif Ethiopic |
| `topical_index_source` | enum `{both, naves, torrey}` | `inject_back_matter` → `_write_topical_page`: `both` = `build_merged_topic_index` (casefold-union, `(N·T)`/`(N)`/`(T)` tags) + `render_merged_topical_index_page`; `naves`/`torrey` = `build_topic_index` + `render_topical_index_page(intro=…)` | shipped 2026-05-26; default `both` |
| `description` / `dedication` | free text (`EDITABLE_TEXT`) | About-this-Edition / optional Dedication front-matter pages | shipped Phase 1 |
| `target_reader` | enum `TARGET_READERS` `{everywhere, eink, tablet, computer, kindle}` — **ONE resolver `resolve_target_reader`/`is_kindle_target` (build_edition, by `DEFAULT_MARKER_STYLE`)** consumed by api_save_edition_meta (valid set), web_editions `api_customize_data`, wizard `TARGET_CAPS`, and `build_one` | **kindle ⇒ the kindle_safe variant (turn-69 ①, Send-to-Kindle E999/E3013):** `apply_kindle_safe_css` CSS append (visible endnotes — un-hides `.notes-section`/`.verse-refs-section`/note-labels/`.vn-sep`; K-KIN-3 seam page-break fixes) + `apply_kindle_toc_rows` (ToC chapter pills→plain inline rows, post-`apply_bilingual_toc` pre-`apply_file_split`) + `patch_opf` stamps `yhwh:target-reader` (additive only when set) read by `dev/verify_kr2_build.py` gate 5 `kindle_safe_checks` (≤10K chars effective display:none + single dc:language) | shipped 2026-06-10 (Mac turn 69); default unset = `everywhere` = byte-identical no-op |

## Findings — accreted, low-risk cleanup targets

The reference graph is sound (0 dangling refs). The blemishes are cosmetic/structural,
products of organic growth from the original 1-Bible builder:

1. **Stale docstring — RESOLVED (2026-05-21).** `core/matrix.py`'s docstring now reads
   **72 kinds / 91,733 notes / 11 editions** (was "5 editions / 63 kinds", later "70 / 1,371").
2. **`editions.yaml` comment drift — RESOLVED (2026-05-21).** The 3 drifted section-header blocks
   (catholic / jewish / scholarly) sat above the *previous* edition's trailing
   `popup_languages_default`; each moved to just above its own `- id:` (pure comment reorder, data
   unchanged — verified 11 editions still load). `ethiopian-tewahedo`'s `[english, hebrew, greek]`
   popups confirmed intended (unchanged).
3. **Logic divergence — RESOLVED (2026-05-20).** "Which kinds ship in this edition" was implemented
   THREE times with drifting gates: `build_edition.compute_enabled_kinds` (phase gate, no ai-gate),
   `matrix._enabled_kinds_for_edition` (ai-gate, no phase gate), `config._kinds_in_edition` (phase
   gate, no ai-gate). The matrix therefore **over-counted** vs. the actual build for the 10 editions
   with `max_phase` < `phase3` (e.g. `ethiopian-tewahedo` showed 25 phase-gated kinds the EPUB never
   contained, incl. its own explicitly-enabled `dist-typological`/`dist-mariological`).
   **Fixed:** one canonical `config.enabled_kind_codes(edition, all_kinds)` applying BOTH gates
   (precedence: explicit-`disabled_kinds` > phase gate > AI double-opt-in > `enabled_kinds`/category);
   `matrix._enabled_kinds_for_edition`, `build_edition.compute_enabled_kinds`, and
   `config._kinds_in_edition` all delegate to it. Invariant pinned by
   `tests/test_enabled_kinds_unified.py` (matrix == build == config for every edition). Matrix counts
   dropped to the correct build-matching values; build output unchanged (`comm-ai` corpus = 0).
4. **Vestigial ψ.35 layering — WON'T-FIX (assessed 2026-05-21).** `Matrix.enabled/potential/per_book`
   are derived projections materialized in `__post_init__`. Converting to `@cached_property` is
   blocked by `@dataclass(frozen=True)` (cached_property can't write its cache to a frozen instance
   without un-freezing, which drops hashability/immutability) AND pointless — the class docstring
   notes every call site reads all three projections, so laziness saves nothing. The eager +
   `object.__setattr__` approach is the correct frozen-compatible solution; leave as-is.

## Re-run the integrity trace

```
py dev/trace_matrix.py        # read-only; reuses the real config loaders; prints per-edition trace
```
Exit is report-only today. Wire into `validate_taxonomy.py` / pre-commit if you want it enforced.

## Build pipeline (downstream of the matrix) & the base-HTML gap

Reverse-engineered 2026-05-21 while verifying the deliverable builds. The matrix decides WHICH
notes/books ship per edition; the build turns that into the EPUB the user downloads:

```
content/notes/<book>.py        (91,733 notes — SOURCE; post-Torrey reference-corpus close)
content/translations/<id>/*.py (verse text as data — SOURCE; powers matrix/parallel/standalone)
        |
        v  inject   (ebible build step 1 = scripts/inject.py --all-books)
        |   Strategy-A: id="v-<book>-<ch>-<v>" anchors.  Strategy-B (late canon):
        |   find_chapter_region_b/find_verse_region_b on id="ch-<bxx>-c<ch>"; when a chapter's
        |   verses spill across a split-file boundary, find_verse_region_b_spill resolves them
        |   from the next file's head (guarded to the last-anchor chapter). Word-anchor miss →
        |   verse-end fallback (resolve_marker_insertion). scripts/audit_base_html.py classifies
        |   regular vs split-file-irregular chapters + enumerates the residual.
        v
epub_working/index_split_*.html   <== BASE SCRIPTURE HTML (calibre-split chunks; the scripture
        |                             TEXT source-of-truth, edited IN PLACE — NOT rendered from
        |                             translations. Notes land as id="note-X" paired with
        |                             href="#note-X"; verses carry id="v-<book>-<ch>-<v>".)
        v  build_edition.py <id>   (filter notes per edition via config.enabled_kind_codes + canon)
per-edition working copy
        v  build_epub.py / build.sh   (mimetype-first store-only zip)
<edition>.epub   (deliverable; dc:identifier = urn:yhwh:edition:<id> — free, not for sale; program © Bogdan Zorlescu all-rights-reserved, sources PD)
```

Health invariant: **paired=N/N** — every `href="#note-X"` has a matching `id="note-X"`. Check before/after any build.

**Build parallelism + caching — ★CONFIRMED-OPTIMAL (round-7 audit, 2026-06-10; don't re-derive):**
`build_edition.py --all` runs editions on a `ThreadPoolExecutor(max_workers=5)` (build_one = disk
I/O + a GIL-releasing subprocess; more workers would OOM the 16 GB box), backed by the
content-addressable build cache (`scripts/core/build_cache.py`, `_PIPELINE_SCRIPTS` guarded by
`tests/test_build_cache.py::TestCacheCoverageGuard`) + an mtime incremental check. zip
`compresslevel` stays 9 (quality > build speed — declined optimization, on the merits).

**Format-matrix catalog flow (matrix M1 + the 2026-06-11 per-edition-signature
addendum — downstream of the build):** `FORMAT_MATRIX` + `COVER_COLOURS` +
`catalog_asset_name` + `edition_cover_signature` (build_edition.py, beside
`TARGET_READERS`) are the ONE home of the format↔target_reader↔packaging table and
the edition→(design, colour) cover identity (the signature parses the stem from
`scripts.core.config.edition_cover_template` / `EDITION_COVER_TEMPLATES` — the
factory map's one home, re-exported by generate_edition_covers). Consumers, never
re-typing it: `scripts/build_format_matrix.py` (the per-edition CI driver: base
build per distinct target via `--target-reader` → COPY the base to
`cell_asset_name` — the edition's own cover is already embedded; no swap → gates:
zip + `scripts/epubcheck.py --require --strict` + `dev/verify_kr2_build.py` →
`sums-<ed>.txt`) ← `.github/workflows/format-matrix.yml` (one job per edition;
SHA256SUMS fan-in job is the sole sums writer) → release assets →
`scripts/gen_release_catalog.py` (paginated asset list + SHA256SUMS →
`website/src/data/catalog.json` + `catalog.html`; column lights only when EVERY
edition's signature-colour asset is published; per-cell M2 variant colours;
legacy flagship epub + kepub cells while their columns are dark) →
`website/build.mjs` inlines at `{{release_catalog}}` on releases.html (one cover
card per edition — `website/covers/<id>.jpg`). M2 composites:
`generate_catalog_composite`/`catalog_colour_variant_plan` (9 editions × own
design × 5 colours, generate_edition_covers.py), committed when M2 ships —
`scripts/swap_epub_cover.py` is the M2 swap leg; CI never composites in-runner.

**THE GAP — RESOLVED (2026-05-21):** the base scripture HTML was recovered from the v28a-50 snapshot
and COMMITTED (`5ee2ad1`) so it can no longer be silently lost; `ebible build` produces valid EPUBs
again. To re-derive a clean inject from scratch: `git checkout 5ee2ad1 -- epub_working/` then
`inject --all-books` (idempotent; reflects the current corpus). The lost `source_archive/` +
`kings_session/` injectors that `run.py`/`add_note.py` shelled out to were repointed to
`scripts/inject.py` (commit `a935701`).

### Base-HTML structure & coverage — how to find / verify any book's scripture text

Per-book metadata: `config.get_book(code)` → `bxx` (canon position, 1-indexed — e.g. **1 Enoch = b16**),
`strategy` (A or B), `ch_count`, `files` (which `index_split_*.html` hold the book). Two anchor schemes:

| strategy | books | how a verse is located |
|---|---|---|
| **A** (early canon) | gen … rev (Protestant + most deutero) | verse anchor `id="v-{code}-{ch}-{v}"` |
| **B** (late / Tewahedo) | 1en, 2en, jub, mq1-3, … | chapter anchor `id="ch-{bxx}-c{ch}"` + `<span class="vn">{v}</span>` (verses may spill across a split-file boundary → `find_verse_region_b_spill`) |

Audit tools (`scripts/audit_base_html.py`, read-only, re-runnable):
- `--coverage` — per book, canonical chapters (1..`ch_count`) with NO anchor in the base = genuinely-missing scripture.
- `--verse-absent` — Strategy-A notes whose verse anchor is absent (versification gap).
- *(default)* — Strategy-B chapters whose anchor region holds no verse spans (spill chapters).

**Coverage state (verified 2026-05-21 via `--coverage`): 0 chapter gaps** — all **87 books / 1,702
chapters** are present in the base HTML; **no book is truncated**. (The earlier "1 Enoch 37-108
missing" note was a *stale pre-recovery artifact* — 1 Enoch has all 108 chapters in the v28a-50 base.)
The inject residual is **~156-161 notes that are verse-level versification mismatches** — the note's
*source* numbers a verse the base translation's chapter doesn't have, so it is **NOT addable content**:
by book `aes` 73 · `1en` 31 · `mq1-3` 33 · `sir` 10 · `jub` 9; by kind `lang-hebrew` 83 ·
`comm-ethiopian` 70 · `comm` 3. Detail: `dev/AUDIT_2026-05-21-inject-tail-residual.md`.

## Presentation / reader-styling pipeline (Wave 2–3)

How a per-edition presentation choice reaches the EPUB. There are **two distinct
delivery mechanisms** — knowing which one a setting uses tells you its risk and
whether it needs an inject re-bake. (The fields themselves are in the "Presentation
/ reader-styling fields" trace table above; design detail: the
`docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md` §4/§7.)

**(1) CSS-append — NO base re-bake (cheap · per-edition · reversible).** In
`build_edition.build_one`, AFTER the canon filter and the `theme` override, a
variant CSS block is **appended** to the edition's `stylesheet.css`; the popup /
note / title-page HTML is byte-unchanged. Same mechanism as the theme override —
so these settings never touch the shared base and need no inject re-run.
- `verse_popup_style` cards|stack → `apply_verse_popup_style` (1395): `cards`
  appends `_VERSE_POPUP_CARDS_CSS` (tinted witness cards, gold/purple spines on
  `.vnote-hebrew`/`.vnote-greek`); `stack` = flat base (no append).
- `note_popup_style` chip|pills → `apply_note_popup_style` (1432): `chip` appends a
  tinted label-chip rule on `.note .note-label` (specificity 0,2,0 — beats base
  `.note-label` 0,1,0, while the `note-comm-*` hide rule 0,2,1 still wins so
  intentionally-hidden labels stay hidden); `pills` = bordered tappable pills on
  `.note a:not(.note-back)` (the negative-space selector isolates in-note xrefs
  from the back-link glyph — baked xrefs carry no class of their own).
- `title_page_style` full-bleed|framed → `apply_title_pages` (3432) transforms each
  kept book's `book-title-frame` div + the `.book-title-page.style-*` CSS;
  `patch_opf_book_images` (3500) registers the art in the OPF (chain after
  `patch_opf_fonts`). Art resolution: `book_covers` override →
  `content/covers/_book_defaults/<code>.jpg` → text-only fallback.
- `cover_template` → `api_apply_cover_template` (api/covers 72) recomposes
  `covers/<id>.jpg` via `generate_edition_covers._compose_cover`; the build then
  ships it through the existing `apply_edition_cover` (3521) cover-swap step.

**(2) Base re-bake — shared base-HTML change (the riskier path).**
`marker_style=numbers` (shipped 2026-05-25, dfbff8a) changed `inject.build_marker` + `build_aside` (150/190), which
runs **base-wide** (per-book, into the shared `epub_working/index_split_*.html`) —
it is NOT a per-edition build-time toggle. Re-baking the shared base requires
proving only the intended markers changed: the byte-multiset **categorize-diff
verifier** + `scripts/resync_marker_glyphs.py` (Wave-3 prereqs). Same risk class as
the popup-version bake. Because each edition filters some markers, `build_one` runs a
per-edition `renumber_markers` post-pass (after the canon filter) so footnote numbers
stay gapless in every edition. The stray `‖` is the `xref` category glyph
(`categories.yaml:28`) reused as the `.note-back` char in `build_aside` (170); the
fix gives the back-link a fixed `↩` (as `vnote-back` already does in
`generate_verse_popups.py`) and renders the category symbol as a deliberate in-note
element (spec §4.4 / §12.4).

**§7 wiring (every enum field, per RULES §9):** `editions.yaml` (unset == default)
→ `api_customize_data` loader → `api_save_edition_meta` enum validator →
`/customize` control (`scripts/templates/customize.py`) → build read → tests
(round-trip · invalid-rejected · back-compat · UI-present · per-option render).

**Matter pages (built-in, NOT toggles)** — the `render_*_page` + `inject_*_page`
family in `build_edition.py` (OPF manifest + spine appended; extracted into `scripts/matter_pages.py` at prereq #2,
25e22cf, re-exported from `build_edition`):
- Front: Title → optional Dedication → Colophon (real computed counts via
  `core.matrix`; © Bogdan Zorlescu / "YHWH Ya' Way Editions") → "A Guide to the
  Notes" (edition-aware symbol legend; rows anchored `id="legend-<cat>"`) →
  About-this-Edition (`render_about_page` 2274 — auto-spec from resolved choices +
  the editable `description`). The placeholder `introduction.xhtml` is dropped.
- Back: Sources & Acknowledgments → Reference tables → Topical index → Closing colophon.
  Topical index: `inject_back_matter(…, canon_books)` → `_write_topical_page` reads the
  `topical_index_source` edition field (default `both`, shipped 2026-05-26). `both` merges
  Nave's (4,604 name-heavy topics) + Torrey (630 doctrinal topics) via
  `build_merged_topic_index` (casefold-union; `(N·T)`/`(N)`/`(T)` source tags — measured
  166 co-named themes, 162 co-citing ≥1 verse) → `render_merged_topical_index_page`.
  `naves`/`torrey` modes use the single-source `build_topic_index` →
  `render_topical_index_page(intro=…)`; the `naves` path is byte-identical to the
  2026-05-25 61226c5 Nave's-only ship (defaulted `intro=` param). OPF manifest + spine + nav
  updated. Both works are credited on the Sources & Acknowledgments page.

## Reference-corpus ingestion (PD reference works → notes)

The reusable pipeline that turns a public-domain reference work into verse-keyed notes feeding the
SOURCE above. Each source is a clean, committed text under `content/sources/`; a per-source parser
builds the per-verse mapping; notes are written via one batched inserter. Coordinate validation drops
impossible `(book, ch, v)` at the boundary so OCR/parse noise never reaches the corpus.

```
content/sources/<work>_source.txt   (clean committed text, extracted from a CCEL PDF)
  Nave's Topical:  naves_ccel_source.txt   -> scripts/extract_naves_ccel.py
                   (CCEL abbrevs; expand_refs carry-forward; note "Jud" = Judges, not Jude)
                   -> fetch_sources._build_naves_indices  (canonical-range VALIDATION)
                   -> content/sources/naves_topical.json  (4,604 topics / 100,983 refs)
                   -> NaveTopicalDetector  -> 26,335 `topic-nave` notes
  Easton's Dict:   eastons_ccel_source.txt -> scripts/extract_eastons_ccel.py
                   (• headwords; FULL book names via EASTON_BOOK; first ch:v ref = primary verse)
                   -> 3,779 `dict-easton` notes  (kind dict-easton, category hist)
        |
        v  scripts.promote.batch_insert_notes  (one read+write per book; per-verse free suffix +
        |    dedup; reuses format_tuple_text/pick_free_suffix — replaces per-note O(n²) inserts)
        v
content/notes/<book>.py
```

**Data-quality guard:** `fetch_sources._naves_coord_in_extent` rejects coordinates beyond a book's
canonical extent (`canonical_verse_counts.canonical_book_shape`); books with no canonical shape
(Tewahedo distinctives) are kept unvalidated. This closed a defect where an OCR'd Nave's source had
injected ~114 impossible-coordinate notes. **Book codes MUST match `content/notes/`** — the project
uses `eze`/`joe`/`nah`/`jam`/`phi` (+ `jdg` Judges, `jud` Jude); a code mismatch silently drops a
book's notes (caught + fixed for 5 books during the 2026-05-21 rebuild). Source provenance lives in
`content/sources/ATTRIBUTIONS.md`.
