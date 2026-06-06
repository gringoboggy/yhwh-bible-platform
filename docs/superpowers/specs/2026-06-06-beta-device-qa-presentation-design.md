# Beta Device-QA — Reader Presentation & Distribution Polish

**Date:** 2026-06-06
**Status:** Approved design (brainstorming complete; ready for implementation plan)
**Source:** `v1.0.0-beta.1` real-device QA round-2 — Apple Books (iOS screenshots `iCloud Photos.zip`) + colour Kobo (`E:\epub-kobo-crops`), user-reported 2026-06-06.
**Companion specs:** `2026-05-24-epub-presentation-polish-design.md` (the original presentation design — this spec revises/extends it), `2026-06-05-epub-reading-experience-overhaul.md` (RX phases 1–5, shipped), `2026-06-05-eink-epub-compat-research.md` (authoritative Kobo/kepub findings).
**Recon:** workflow `wf_60224189-33c` (7 agents) mapped every affected subsystem to file:line; cited inline below.

---

## 1. Motivation

The beta is a **success** — the user calls it "a definitive win," Apple Books "way better than Kobo, very good beta," and on the colour Kobo the two original blockers (crash + tiny font) are **fixed**. This spec collects the polish items that real-device reading then surfaced. None block the live beta; all improve the read.

Two device contexts, one shared pipeline:
- **Apple Books** (iOS): popups work and look good; issues are typographic (tiny body, ragged-right) + note-popup content (redundant entries, no visual separation, OCR word-breaks) + the recurring book title-page misalignment.
- **Colour Kobo** (sideloaded EPUB): now renders smoothly, font legible — but popups don't fire at all, the native ToC is an endless chapter list, the in-content ToC looks unclickable, and body text isn't justified.

Guiding principle stays **RULES §2** — presentation changes are per-edition configurable settings with sensible defaults (the picks below), wired `editions.yaml → /customize → build pipeline`. Defaults are what the user chose here.

## 2. Findings ground-truth (from recon)

| # | Area | Root cause (file:line) |
|---|------|------------------------|
| ① | Markers all look like numbers | Translation marker **is the verse number** (`vn-link > span.vn`, `generate_verse_popups.py:91-107`); note marker is a bare count badge (`apply_badge_markers`, `build_edition.py:1959-1963`). Category symbols exist (`categories.yaml`, `inject.glyph_for`) but are moved into the popup. |
| ② | Duplicate cross-ref in note popup | **Corpus bug** — two byte-identical `xref-citation` tuples for Gen 1:1 (`content/notes/gen.py:16-26` suffix `""` + `:49-59` suffix `"c"`); `apply_badge_markers` has **no dedup** (`build_edition.py:1922-1955`). Systemic: ≥6 adjacent xref pairs in `gen.py` alone. |
| ③ | Notes feel redundant / unordered | Popup rows emitted in **reading order — no grouping, no sort, no separators** (`build_edition.py:1922-1955`). |
| ④ | No colour distinction | Per-category colour **exists as a thin left-border spine** (13 hues, `stylesheet.css:223-225, 640-679`) but no background fill; palette has collisions; not data-driven. §4.4 chip/pills + §4.2 tinted cards never built. |
| ⑤ | Body tiny on Apple, ragged-right both | `0.95em` + `line-height:1.32 !important` (RX-Phase-2 "amplification" block `stylesheet.css:341-357`); `text-align:left` in 4 places (54, 114, 244-246, 358). **No px/pt anywhere** — Apple honours the literal 0.95/1.32; Kobo masks it. Embedded Cardo forced ahead of reader-native serif via managed-region `!important` stack (`597-600`). |
| ⑥ | OCR word-breaks ("con- tains", "Eome") | Source-OCR line-break hyphenation + errors frozen into note bodies (Easton dictionary, manuscript-witness notes) in `content/notes/*.py`. |
| ⑦ | Kobo: no popups | **Definitive:** plain sideloaded EPUB3 footnotes do **not** pop on Kobo (Adobe RMSDK path). Markup is already correct (forward `noteref`→`aside epub:type=footnote`, ASCII ids). Requires a **`.kepub.epub`** variant (koboSpans) so Kobo's own WebKit renders them. Pipeline emits no kepub (`build_edition.py:4308`). |
| ⑧ | Kobo native ToC too long | `enrich_nav_chapters` adds a per-chapter navPoint to nav.xhtml + toc.ncx for every book, called whenever `reader_toc_books_only` (`build_edition.py:2765`, call site `4298-4299`). |
| ⑨ | In-content ToC "not clickable" | Book label **is** a real `<a href>` (`build_edition.py:2738`), but the maroon/bold ToC-link CSS uses a direct-child selector broken by the `<p class="toc-book-label">` wrapper (`stylesheet.css:437-446`), so it only matches global `a{}` = navy, no-underline → looks like plain text on grey e-ink. |
| ⑩ | Book title-page misalignment | Eyebrow/subtitle left, title centred (recurring). Strong hypothesis: `.book-title-frame` is a left-anchored `inline-block`; **render the current build first to pin the exact element** before coding (the standing render-first rule). |
| ⑪ | Website downloads | (separate surface) `website/src/releases.html` + `releases.js` — cramped layout, over-technical filenames, mobile layout off. |
| ⑫ | Empty / blank pages between chapters | (newly reported, confirmed in IMG_0112/0114/0115) the RX-P4b file-splitter (`apply_file_split`) puts each chapter-piece in its own spine item → forced page break + big blank tails (Luke 24:51-52, 24:53 each on a near-empty page); plus a fully-blank page after the title (the `.book-title-frame` height). Diagnose via the §3.7 audit. |
| ⑬ | Front-matter affordance + label stretch | (newly reported, IMG_0117) colophon "This Edition" label line renders **stretch-justified** ("Edition" left ⟷ "ID:" right); About/Your-Edition rows look **unexpectedly tappable**. Template-level front-matter render + CSS. |

## 3. The design

### 3.1 Inline markers — give each its own identity (①)
- **Verse number** stays bold inline, and remains the **translation marker** (tap → the original-language popup, whose header already reads "Genesis 1:1"). Keep its tappable styling (dotted underline). We do **not** stamp "1:1" on every verse (clutter + Kobo reflow); the coordinate lives prominently in the popup header.
- **Note marker** becomes a **category symbol + count**, default glyph **◈** (echoes the book's ❖ ornament, geometric-reliable, clearly not a number). Default mode stays **badge** (one per verse). Source: `apply_badge_markers` already extracts each verse's note kinds (`build_edition.py:1915`); emit `◈{n}` instead of `{n}` at `build_edition.py:1959-1963`; mirror the change in `resync_marker_glyphs.renumber_markers:155` for numbers-mode parity.
- **Glyph reliability:** verify ◈ (and the in-popup category glyphs) render on Apple Books + Kobo; if any tofu, embed a tiny symbol-font subset (the project already embeds via `EMBED_FONT_PATHS` / `patch_opf_fonts`). The original spec mandates this (§5.2/§10).
- **Configurable:** the note-marker glyph is a setting (default ◈); badge vs numbers stays the existing `marker_style`.

### 3.2 Note popup — tinted cards, grouped, de-duped (②③④)
- **Layout = tinted card per note (chosen: option A).** Each note sits in its own soft category-tinted card: category symbol + label + `ch:v` + body. Extends the existing left-border-spine palette to a full (soft) background fill.
- **Deconflicted palette** (e-ink-legible, contrast-safe, no collisions) keyed to the categories actually seen. Make it **data-driven**: add a `color` (and derived soft `background`) field per record in `content/categories.yaml`; the build emits the CSS from it instead of the hard-coded `stylesheet.css:640-679` block. Proposed (tunable):

  | Category | Symbol | Accent | Soft fill |
  |----------|--------|--------|-----------|
  | Historical / Cultural | ⌂ | `#8B5A2B` (umber) | `#F6EFE6` |
  | Commentary / Tradition | ◇ | `#0B3D91` (royal blue) | `#EAF0FA` |
  | Cross-references | ‖ | `#5C2E91` (violet) | `#F1ECF8` |
  | Textual / Manuscript | ✧ | `#A0202C` (crimson) | `#FaEDEE` |
  | Linguistic / Word-study | ⌘ | `#8B6508` (goldenrod) | `#F7F1E0` |
  | Topical | ✦ | `#4A5568` (slate) | `#EFF1F4` |
  | (rare: Literary ⌇, Comparative ☩, Liturgical ☧, Edition-Distinctive ❖) | — | quiet neutral `#5A5550` | `#F2F0EC` |

- **Grouping + fixed sort order** (most-useful → least, long topical last):
  1. ⌂ Note (Historical/Cultural context)
  2. ◇ Commentary / Tradition
  3. ‖ Cross-references
  4. ✧ Textual / Manuscript witness
  5. ⌘ Word study / Linguistic (incl. dictionary)
  6. ✦ **Topical (Nave's / Torrey) — always last, grouped together**
  - Rare near-empty categories slot by the same priority. Implement by bucketing rows by `category_for(kind)` + a curated order in `apply_badge_markers` row assembly (`build_edition.py:1922-1955`), with a category header/divider per group.
- **Dedup (②) — two layers:**
  - **Render-time** (safety, edition-safe): a seen-set on normalized `(kind, body)` while building rows in `apply_badge_markers:1922-1948` — skip exact repeats.
  - **Corpus cleanup** (root): a one-time pass over `content/notes/*.py` pruning duplicate tuples that collide on `(book, ch, v, kind, body, attribution)` across suffixes (the `promote.py:88-144` key, made suffix-independent). Size it first with a corpus-wide collision count (the formatting audit, §3.7).

### 3.3 Translation popup — one per verse, clear header (③ translation)
- Main pipeline is already strictly 1:1 (verified). Harden with a post-build uniqueness assertion over `vnote-*` / `vn-link` ids (no dup ids; every href target exists once) — folds into the formatting audit (§3.7).
- Ensure the **"Book ch:v" header is prominent** (`generate_verse_popups.py:34` already emits it).
- The user-seen "two popups, same translations" is most likely the **KJV-fallback** (`build_edition.py:1300-1302`: witness-less verses keep the same English) — the audit will flag adjacent identical-witness popups; confirm against a specific verse on the next device test.

### 3.4 Typography — justify, resize, let Kobo breathe (⑤⑥)
- **Justify** body scripture only: flip `text-align:left → justify` on the verse selectors (`stylesheet.css:358` `p.verse-p`, `114` `.verse-p,.verse-p-flush !important`), and narrow the force-left block (`244-246`) to target verse paragraphs so front-matter labels (`.intro-*`, `.your-edition-*`, `.bookpage-*`, `.legend-*`) stay left and never re-stretch (the §5.2 reason). Add `hyphens:auto; overflow-wrap:break-word` to avoid justify rivers.
- **Size — per-device (user goal: bigger on Apple, smaller on Kobo) IS achievable:** we already produce **two artifacts** (§3.5), so each carries its own default. The plain `.epub` (Apple Books) gets an **Apple-tuned larger** body (`stylesheet.css:357`, ~`1.05em`); the `.kepub.epub` (Kobo) gets a **Kobo-tuned smaller** body (~`0.92em`). Relax `line-height 1.32 → ~1.45` **dropping the `!important`** (`355`) so readers can still override. Mechanism: a `style_config.py` `BODY_FONT_SIZE`/`BODY_LINE_HEIGHT` knob (default = Apple value) that the kepub target overrides to the smaller Kobo value before conversion. **Fallback** if a single file is preferred: shared `1.0em`, nudged a touch smaller for Kobo. Exact values confirmed on the next device test.
- **Let Kobo use its native serif:** drop `Cardo` (and the dead `IM Fell English`/`Goudy`/`Sorts Mill` names) from the **body** font-family stacks (reconcile **both** the amplification stack `352-354` and the managed-region stack `597-600` — fix-the-class), or drop the `!important`, so body text falls through to the reader's serif. **Keep Cardo scoped to `.vnote-hebrew`/`.vnote-greek`** (Heb/Grk glyph coverage) and Noto Serif Ethiopic for the standalone Ge'ez Bibles.
- **De-hyphenation (⑥):** a careful corpus pass over `content/notes/*.py` (and re-bake into base) rejoining source-OCR line-break splits — `"con- tains" → "contains"` — using a dictionary/affix check, **never** touching legitimate hyphens (`cross-references`, `image-of-God`). Scope to the known OCR sources first (Easton dictionary `dict-easton`, manuscript-witness). Add obvious-error fixes only where unambiguous (e.g. leading-`n `→`In `, `Eome`→`Rome` flagged for review, not blind-replaced). Guard with a lint check + tests; re-verify byte-exact base reconstruction + epubcheck.

### 3.5 Kobo — book-level ToC + kepub popups + clickable in-content ToC (⑦⑧⑨)
- **Native ToC book-level only (⑧):** stop the unconditional `enrich_nav_chapters` (`build_edition.py:4298-4299`); gate it behind a **new per-edition field `reader_native_toc_chapters` (default false)**. Book-level becomes the default native ToC; editions can opt back in. Surface in `/customize` (RULES §6.5). nav.xhtml/toc.ncx already carry the book-level entries.
- **Kepub variant for popups (⑦):** add an **optional additional build target** producing `<edition>.kepub.epub` via **kepubify** (least source change) — an extra output, **not** a transform of the canonical EPUB. Guard rails: enforce ASCII ids starting with a letter (already true); suppress kepubify's auto-pop of *every* internal cross-reference link (xref-dense Bible). **Ship both** the plain `.epub` (keeps Kobo bookmarks/annotations on sideload) and the `.kepub.epub` (gets popups) — user picks per device. Final confirmation is the user's real-device test (firmware-specific).
- **In-content ToC clickable (⑨):** add a CSS rule for the books_only label link — extend the selector list at `stylesheet.css:437-446` to include `.toc-wrap li.toc-book > p.toc-book-label > a` (maroon `#7B0E0E`, `font-weight:600`, underline) and give `.toc-book-label` block padding for a large tap target. (Optionally restore a compact, Kobo-safe inline chapter-pill affordance behind a flag — deferred unless wanted.)

### 3.6 Book title page — centre the frame (⑩)
- **Render-first (non-negotiable):** build/unzip the current ethiopian-tewahedo EPUB, render a book title page (Playwright/localhost), pin the exact off-element. Strong hypothesis from the recon + crops: `.book-title-frame` is a left-anchored `inline-block` so short eyebrow/subtitle lines hug the left while the larger title extends right — the lines are centred *within* a frame that isn't centred in the plate (which is why re-applying `text-align:center` never helped). Fix = centre the frame in the plate (parent `text-align:center` / proper block centering), verify on re-render, then epubcheck. Base structure: `epub_working/index_split_*.html` `.book-title-page > .book-title-frame > .bookpage-eyebrow/.bookpage-subtitle/.bookpage-title/.bookpage-rule`; CSS `stylesheet.css ~:503-507`.

### 3.6a Empty / blank pages between chapters (⑫)
Newly reported: frequent blank pages between chapters. Likely causes (diagnose, fix the real one): (1) **forced page breaks** — `page-break-before:always`/`page-break-after:always` stacked on `.book-title-page`, `.ch-heading`, or chapter wrappers, so when a chapter already starts at a page boundary an extra blank page renders (esp. Apple Books' paginator); (2) **empty/near-empty `index_split_*` pieces** from the RX-P4b file-splitter (`apply_file_split`) — a boundary cut leaving a whitespace-only piece shows as a blank page. Fix surface: the §3.7 structural audit detects empty/near-empty pieces; the page-break CSS lives in `epub_working/stylesheet.css`. Collapse redundant stacked breaks to one break per chapter, and/or have the splitter drop/merge empty pieces. Verify by re-rendering a multi-chapter book on both readers (no stray blanks) + epubcheck.

### 3.6b Front-matter affordance + label stretch (⑬)
On the colophon / "This Edition" / "About this Edition" pages (confirmed IMG_0117): (a) label lines like "Edition ID:" render **stretch-justified** (big gap — "Edition" left, "ID:" right) — likely a `display:flex; justify-content:space-between` or a 2-word justified line; fix to a clean left-aligned `label: value` (a `<dl>` or simple left block — **never justify front-matter**, and make sure the §3.4 verse-justify never reaches these). (b) Some elements look **unexpectedly tappable** — likely the §5.3 category-symbol legend cross-links and/or in-note symbol-link styling bleeding onto the About page's category list; render the page (render-first) to pin each, keep the intentional legend cross-links, and ensure plain text (Edition-ID/urn, counts) carries no link affordance. Template-level (front-matter render functions + shared CSS) → one fix cascades to all editions.

### 3.7 Structural formatting audit (⑪ user-requested)
Because every notes-pill / translation-pill / book / chapter / verse is generated from the **same template, the format is uniform — any deviation is a bug.** Build:
- **One-time diagnostic** over the *built* EPUB(s): parse the XHTML and flag every anomaly — duplicate note/aside blocks (the doubled cross-ref), unbalanced/missing `<`/`>`, double-emitted loops, duplicate ids, broken/missing href targets, any pill off the canonical shape, witness-identical adjacent translation popups, OCR word-break residue. Output a triaged report; feed the dedup (§3.2) + de-hyphenation (§3.4) cleanups.
- **Permanent lint guard** (in the existing lint-rules harness) so the canonical-shape invariants can't regress. Run base-wide + on representative built editions.

### 3.8 Website downloads + versioning (⑪ → site)
`website/src/releases.html` + `releases.js`:
- **One clean Download block** for the current beta — the 3 platforms (Windows / macOS / Linux) side-by-side, **human-friendly labels** (e.g. "Windows app", "Mac app", "Linux app") not raw asset filenames; the technical filename + checksum behind a small "details" affordance. **Exactly one downloadable build — the current beta** (a newer beta replaces the older; we do not keep multiple downloadable betas).
- **Update log ("What's changed")** between versions — a short, human-readable changelog of what changed from the prior version, **capped at 3 entries (1 present + 2 past)**; the oldest drops off as new ones land. Notes only, not extra downloads. Separated visually from the download CTAs (your "releases shouldn't sit next to the beta buttons").
- **Fix mobile layout** (the cramped/weird look) — responsive stack on small screens.
- Build the site here; **deploy is the normal Pages step** (on the user's go / when the Mac lane is up).

### 3.9 Release the new beta (⑪ → release)
When the EPUB work (§3.1–§3.7) lands, **cut a NEW beta version** — `v1.0.0-beta.2` (the number **must differ** from `beta.1`; bump `VERSION`). Rebuild + re-sign the 3 platform artifacts + the Ethiopian Bible EPUB (Windows Azure-signed, macOS notarized, Linux AppImage), regenerate `SHA256SUMS.txt`, **replace** the live GitHub release (new tag, retire/supersede `beta.1`), and write the `beta.2 → beta.1` update-log entry (§3.8). The site's `releases.js` auto-surfaces the new prerelease.

## 4. Configurability (RULES §2 / §9)

New/changed `editions.yaml` fields (all back-compat, unset → default), surfaced in `/customize`, read in the pipeline:
- `note_marker_glyph` (default `◈`)
- `note_popup_style` → wire the long-stubbed `chip`/`pills` into the new **tinted-card** default (or a new `cards` value)
- category `color`/`background` (data-driven, from `categories.yaml`)
- `BODY_FONT_SIZE` / `BODY_LINE_HEIGHT` (`style_config.py` knobs)
- `reader_native_toc_chapters` (default false → book-level native ToC)
- `kepub_output` (default on for the build's additional target)

## 5. Testing / gates

- **Per change:** schema round-trip + invalid-input rejection + unset→default + `/customize` presence where a new field is added.
- **Markers:** badge verse → one `◈{n}`; numbers mode → `◈`-prefixed sequence; translation marker = verse number, popup header has `Book ch:v`.
- **Note popup:** rows grouped by the fixed category order, topical last; dedup proven on Gen 1:1 (one cross-ref block, not two); tinted-card CSS present; category colours render.
- **Typography:** `.verse-p` = justify; front-matter labels still left; `font-size 1.0em` + relaxed leading present, reader-overridable (no `!important`); body font stack no longer forces Cardo; Heb/Grk popups keep Cardo.
- **De-hyphenation:** byte-exact base reconstruction (`apply_map(HEAD)==working`); categorize-diff proves only targeted bodies changed; sample fixes correct, legitimate hyphens untouched; epubcheck clean.
- **Kobo ToC:** native nav = book-level (no chapter navPoints) unless `reader_native_toc_chapters`; in-content ToC label link styled clickable.
- **Kepub:** `.kepub.epub` produced, valid, koboSpans present, ids ASCII-letter-initial; cross-ref auto-pop suppressed.
- **Title page:** re-render shows eyebrow/subtitle/title on one centred axis; epubcheck clean.
- **Formatting audit:** diagnostic finds the known dup + zero false-criticals on a clean build; lint guard fails on a seeded violation.
- **Integrity (every phase):** ethiopian-tewahedo **+ a canon-filtered edition (catholic-study)** epubcheck 0/0/0/0; `ebible verify` errors=0; `check_nested_anchors` 0; base-invariant where `epub_working` is touched.

**Byte-compat note:** this **intentionally** changes built output. Do **not** assert "zero output change." Pin the new expected output; prove *non-targeted* parts unchanged via categorize-diff; the 9 KJV editions change only where these rules reach them.

## 6. Open items — resolved with recommendations

- **Translation marker label:** keep verse number (popup header carries the coordinate); do **not** stamp `1:1` per verse. *(Recommended; user "go with your idea.")*
- **Font size value:** ship `1.0em` / `line-height 1.45` default, reader-overridable; **fine-tune on the next device test** (the one value that genuinely needs the device).
- **Kepub:** ship **both** plain + kepub.
- **Native ToC:** new field default off → book-level default, configurable.
- **Dedup:** do **both** render-time + corpus cleanup.
- **Colours:** data-driven palette in `categories.yaml`, deconflicted, soft fills (option A).

## 7. Suggested phasing (for the plan)

1. **CSS quick wins (low risk, immediate):** justify `.verse-p`; in-content ToC link affordance; body size/leading; relax Cardo body dominance. One build, epubcheck-clean.
2. **Note popup overhaul:** tinted cards + data-driven category colours + grouping/sort + render-time dedup; the `◈` note marker. 
3. **Native ToC book-level field + kepub output target.**
4. **Corpus cleanups (gated on the audit):** the de-hyphenation pass + the duplicate-tuple prune.
5. **Formatting audit:** diagnostic + permanent lint guard (run it *before* 4 to size the work).
6. **Book title page:** render-first → fix.
7. **Website downloads + update log** (single current-beta download, "what's changed" capped at 3, mobile fix).
8. **Release `v1.0.0-beta.2`** — bump `VERSION`, rebuild + re-sign all 3 platforms + the Bible EPUB, regen checksums, replace the live release, write the `beta.2 → beta.1` log entry.

Each phase ends epubcheck-clean + gates green and is independently shippable. Quality over speed; no time-gating.
