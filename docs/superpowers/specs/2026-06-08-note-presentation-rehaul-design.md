# Note-presentation rehaul — build-time, lossless, reader-robust cascade (design spec)

**Status:** READY 2026-06-08 · Mac-led design · **build implementation = WIN (Stage C of the v0.1.0 master plan)**. Adversarially reviewed (3 corpus-level critics) and corrected before delivery.
**Scope:** the implementation-ready design for master-plan laundry-list **item 1** — turning the device-QA §4+5 evidence + the note-presentation NORTH STAR into a concrete, build-time, **lossless**, **option-gated** transform of how a verse's editorial notes render in the EPUB.
**Findings-only HOLD:** this is a *design doc* (a new file, blocks nothing). No build code is touched until the v0.1.0 master plan is ratified; this spec is what WIN implements when it is.

## 0. What this spec is, and what it deliberately does NOT re-author

This spec **extends already-shipped code and already-written design**. It must NOT restate work that exists:

- **Already SHIPPED in `scripts/build_edition.py`** (`apply_badge_markers`, lines 1856–2074; invoked from `build_one` at **`:4497`**, runs only when `marker_style == "badge"` at `:4496`): the per-verse marker→badge collapse (`<sup class="marker-badge">◈{n_show}</sup>`, `:2045`), the merge of N per-note asides into one `<aside class="verse-notes">`, the **category-rank ordering** (`_POPUP_CATEGORY_RANK`, derived from `_POPUP_CATEGORY_ORDER` `:1806-1823`, order `hist, comm, xref, text, lang, lit, compare, apol, dev, liturgy, ped, modern, vis, dist, topic`), the **in-verse exact-row dedup** (`seen_rows`, normalized `" ".join(row.split())`, `:1971-1991`), and the **cross-verse dedup** (`seen_book_rows`, `:1911,1996-2001`, with `_XVERSE_DEDUP_EXCLUDE = {"xref","topic"}` `:1853`). **The rehaul EXTENDS this function — it does not introduce dedup, grouping, or the badge from scratch. The existing two-layer dedup runs FIRST, unchanged; the cascade transforms what survives it.**
- **The tinted-card palette is SHIPPED hard-coded** in `epub_working/stylesheet.css:846-879` (the RX-beta2 per-category soft-fill + 4px left border). **Reference it; do not re-author it.** ⚠ Reconciliation: the 06-06 spec §3.2 proposed making this palette *data-driven* via a `color`/`background` field per record in `content/categories.yaml`. That proposal is **SUPERSEDED / deferred for v0.1.0** — the palette stays hard-coded, **no `categories.yaml` colour field is added** (consistent with the master-plan "additive only; no registry edits" constraint). The 06-06 §2④ note "tinted cards never built" is now **stale** (they shipped).
- **Already DESIGNED in the 06-06 docs** (`docs/superpowers/specs/2026-06-06-beta-device-qa-presentation-design.md` §3.1–3.2, plan Phase 2): the `◈` marker + `marker_style`, the fixed category order, the `note_popup_style`/`note_marker_glyph` fields, the high-level "two-layer dedup" idea — all reference, don't re-author.
- **Owned by OTHER master-plan stages / 06-06 phases** (OUT of scope here): justify/typography (Ph1 / finding 1b), the pill-ToC + native-ToC (Ph3 / findings 1·1c), the stats-popup bug (finding 2), title-page bleed (Ph6 / finding 3), the desktop-app nav prettify (finding 6), the macOS native window (finding 7), the corpus-prune of duplicate tuples (Ph5).

What this spec **adds** (the delta `master-plan.md:144-148` asked for): the exact **cascade markup** (verse→category→source→note) in reader-robust primitives; the **per-stage dedup predicates** (finer than the live exact-row key); the **completeness / never-drop-a-distinct-point guard**; the **reader-robust acceptance tests**; and the **per-stage option wiring + byte-stability obligation**.

---

## 1. Grounding facts (the data we have to work with)

**Note record** — `content/notes/<book>.py`, a top-level `NOTES = [...]` of positional tuples (`content/notes/gen.py:7-13`, `scripts/core/config.py:27-104`):

```
(chapter, verse, suffix, anchor, kind, title, label, body_html [, attribution])
   0        1       2       3       4     5      6       7            8 (optional)
```

- **There is NO stored `category`, `source`, or `term` field.** Three derivations are load-bearing:
  - **category** = `kinds.yaml[kind].category` — derived from `kind` (field 4) via `inject.category_for(kind)` (`scripts/inject.py:147`). 15 categories, each with a glyph + label + sort order (`content/categories.yaml:13-103`).
  - **source** = the **`attribution` string** (field 8), free text, e.g. `"Strong's H1254, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD."`. Read by `config.note_attribution()` (`config.py:125-133`). The SAME source recurs verbatim across many notes — this repetition is the redundancy.
  - **label** = field 6 = a short **kind-level** code (`"Hebrew."`, `"Easton."`, `"Cite."`, `"Topic."`, `"MS."`, `"Note"`) — NOT the category label. The kind's default label is in `kinds.yaml` (`label:`). (This distinction is the crux of S1 — see §3.)
  - **term/headword** = the leading `<strong>…</strong>` inside `body_html` (field 7); the anchored word in the verse is `anchor` (field 3).

**The 15 categories** (`content/categories.yaml`, id · glyph · label, in sort order):
`lang ⌘ Linguistic` · `text ✧ Textual/Critical` · `xref ‖ Cross-references` · `hist ⌂ Historical/Cultural` · `lit ⌇ Literary` · `comm ◇ Commentary/Tradition` · `compare ☩ Comparative Religion` · `dev ✶ Devotional/Applied` · `liturgy ☧ Liturgical` · `apol ⚖ Apologetic` · `modern ⊛ Modern Issues` · `ped ◯ Pedagogical` · `vis ❑ Visual/Media` · `dist ❖ Edition-Distinctive` · `topic ✦ Topical`. (The device-QA doc's "◇⌂⌘▌⚖○✦" was an approximation; these are authoritative. One per-kind glyph override: `comm-ai` → `Ⓐ`, `kinds.yaml:497-501`.) **Quirk:** `dict-easton` is filed under category **`hist`** (verified via `category_for`), not a dedicated "Dictionary" category — see §9.

**The live per-category "spine" CSS requires a kind sub-code, not a bare category class.** The shipped left-border rules are `[class*="note-lang-"]`, `[class*="note-hist-"]`, … (`epub_working/stylesheet.css:733-773`) — they match a **trailing-hyphen kind class** like `note-lang-hebrew`. A bare category class (`note-lang`, `note-hist`, `note-topic`) does **not** contain that substring and matches **nothing**; only `.note-comm` has a bare legacy rule (`:226`). **Consequence for §2:** a cascade *group* element cannot inherit a per-category spine from a `note-{cat}` class — the spec adds explicit group spine rules. A *leaf* `.vn-item` is fine: it keeps `note-{kind}` (with the hyphen), so it still matches both the spine and the tinted card.

**The current rendered output (the "transform FROM").** In `badge` mode `apply_badge_markers` emits one merged aside per verse (`:2029-2035`), FLAT: a `vn-back` header (`↩ <strong>{ch}:{v}</strong>`) then a flat join of `<div class="vn-item note-{kind}">` rows (one per surviving note, category-rank-ordered). **What is missing** is the cascade structure — category headers, source bylines, and the removal of the repeated per-note label / source restatement.

**Reader-robustness palette** (from `docs/superpowers/notes/2026-06-05-eink-epub-compat-research.md`). Carry structure with primitives that survive on the weakest engine (e-ink Kobo / Adobe RMSDK / Apple Books); tinted cards are enhancement only:

| Reliability | Properties |
|---|---|
| **SURVIVES everywhere → carry hierarchy here** | `font-weight`, `font-variant-caps:small-caps` (research endorses over `font-size`), `font-style:italic`, `<hr>`, **`border-left` / `border-bottom` rules**, `margin`/indent, `letter-spacing`, list markers, `<blockquote>`, Unicode glyph **as inline text accompanied by its label text** |
| **ENHANCEMENT-only → never the SOLE cue** | `background-color` (and *actively artifact-prone* on iOS Apple Books with inline `padding`+`super`, `stylesheet.css:180-182`), `border-radius`, `box-shadow`, custom decorative `@font-face` (WOFF2 unsupported on Kobo/Apple), flexbox/grid (e-ink ignores flex, `:477`) |

**Acceptance principle (north star, non-negotiable):** *turn CSS backgrounds (and embedded fonts) off → the note block is still clearly structured, hierarchical, and category-identifiable.* The glyph must always be paired with its label **text** (never glyph-only — tofu risk; that is why inline markers are numeric).

---

## 2. The cascade — exact markup (deliverable D3)

Mirror the canon's own `book → chapter → verse`. A verse's notes cascade **verse → category → source → note**, ordered + consistent every time:

```html
<aside class="verse-notes" id="vnotes-{code}-{ch}-{v}" epub:type="footnote">
  <p class="vn-back"><a href="#vbadge-{code}-{ch}-{v}" class="note-back" title="Back">↩</a> <strong>{ch}:{v}</strong></p>

  <!-- one <section> per CATEGORY present on the verse, in _POPUP_CATEGORY_RANK order -->
  <section class="vn-group note-cat-{cat}">          <!-- note-cat-{cat}, NOT note-{cat}: gets an explicit group spine (below) -->
    <p class="vn-cat-head"><span class="vn-cat-sym" aria-hidden="true">{glyph}</span> {Category label}</p>

    <!-- one block per SOURCE within the category, in first-appearance order -->
    <div class="vn-source">
      <p class="vn-source-byline">{source named once — see S1}</p>
      <div class="vn-item note-{kind}">{note body — per-note label suppressed when it is the kind default}</div>
      <div class="vn-item note-{kind}">{another note from the same source}</div>
    </div>
    <div class="vn-source"> … another source … </div>
  </section>

  <section class="vn-group note-cat-{cat}"> … next category … </section>
</aside>
```

**Why these elements (reader-robust rationale):**

- **`<p class="vn-cat-head">`, NOT a real `<hN>`.** A heading inside an `epub:type="footnote"` aside is a real native-ToC/nav-harvest hazard (the nav doc is the navigation spine, and we cannot control how a reader renders headings in notes). A `<p>` styled with **weight + small-caps + a `border-bottom` hairline** is just as strong a cross-reader cue and avoids harvesting. For accessibility, `role="heading" aria-level="4"` MAY be added (zero visual change). The category **label text is always present** beside the glyph, so identity survives where the glyph font is missing.
- **`section.vn-group` carries category COLOUR via an EXPLICIT per-category `border-left`** added in the gated robust-CSS append (below) — it does **NOT** inherit from `note-{cat}` (the live `[class*="note-{cat}-"]` spine selectors do not match a bare category class; see §1). The class is `note-cat-{cat}` to avoid any accidental match with the kind-level spine rules.
- **`.vn-cat-head`'s `border-bottom` is a HEADER cue, not the category-colour cue** — category colour is delivered by the group's `border-left`. (Stated so the two are not conflated.)
- **`<p class="vn-source-byline">` names the source once** (italic/small-caps weight) — the load-bearing output of S1.
- **`.vn-item` is unchanged structurally** — it keeps `note-{kind}`, so it still matches the shipped leaf spine + tinted card. Indentation (`margin-left`) under `.vn-source` expresses cascade depth via a survivable property.

**Required CSS — robust layer** (a new gated append helper in `build_edition.py`; §7). Uses only survivable properties:

```css
.verse-notes .vn-group        { margin: 0.55em 0; }
/* category COLOUR — explicit per-category group spine for ALL 15 categories.
   Reuse the exact hue values already in stylesheet.css:733-773 (e.g. lang #8B6508,
   comm #0B3D91, apol #2E5E3E, …). One rule per category: */
.verse-notes .vn-group.note-cat-{cat} { border-left: 3px solid {category-hue}; padding-left: 0.6em; }
.verse-notes .vn-cat-head     { font-weight: 700; font-variant-caps: small-caps; letter-spacing: 0.04em;
                                font-size: 0.86em; margin: 0.15em 0 0.3em; padding-bottom: 0.12em;
                                border-bottom: 1px solid rgba(110, 88, 64, 0.35); }   /* header cue, NOT category colour */
.verse-notes .vn-cat-sym      { margin-right: 0.3em; }
.verse-notes .vn-source       { margin-left: 0.7em; margin-bottom: 0.25em; }          /* cascade indent */
.verse-notes .vn-source-byline{ font-style: italic; font-weight: 600; font-size: 0.82em; color: #6E5840; margin: 0.2em 0 0.1em; }
.verse-notes .vn-source .vn-item { margin-left: 0.5em; }                              /* leaf indent under source */
```

**Enhancement layer = the 06-06 tinted-card palette, unchanged** (`stylesheet.css:846-879`, selectors still match `.verse-notes .vn-item`). The only requirement this spec adds: **the cards must never be the sole cue** — the group `border-left`, the `.vn-cat-head` weight+rule, the byline weight, and the indents must all survive so that, with every `background`/`border-radius`/`box-shadow` rule removed, the cascade is still fully legible and category-identifiable (the §5 acceptance test enforces this against the *merged* stylesheet).

### Worked example — Genesis 1:1 (illustrative)

Gen 1:1 carries **17 note tuples**; one exact-duplicate `xref` (suffix `""` vs `"c"`) is dropped by the live `seen_rows`, so the badge reads **`◈16`** (post-dedup unique count, `:2045`). After S1+S2+S3a (bylines below are *illustrative of the intended polish* — see the S1 byline contract in §3):

```
1:1 ↩
  ⌂ Historical / Cultural
      Easton's Illustrated Bible Dictionary (1897)
        • CREATION — "In the beginning" God created…
        • HEAVEN — (1.) Definitions. The phrase "heaven and earth"…
      (reference sample, η.1)
        • Ancient Near Eastern context — Gen 1 shares structural features…
  ◇ Commentary / Tradition
      Ephrem the Syrian — Commentary on Genesis
        • Ephrem reads "In the beginning"…
  ‖ Cross-references
      Treasury of Scripture Knowledge (1830s)
        • Jhn 1:1 · Heb 11:3 · Isa 45:18
  ✧ Textual / Critical
      Kenyon, Our Bible and the Ancient Manuscripts (1895)
        • Manuscript witness…
  ⌘ Linguistic
      (user paraphrase)
        • Bereshit (בְּרֵאשִׁית) — "In the beginning"…
        • Baraʼ (בָּרָא) and the LXX choice…
      A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894)
        • Bârâʼ (בָּרָא) — to create…
        • ʼerets (אֶרֶץ) — the earth…
        • Shâmayim (שָׁמַיִם) — the sky…
        • ʼĕlôhîym (אֱלֹהִים) — God…
  ⚖ Apologetic
      (reference sample, η.1)
        • Harmonization: Gen 1 vs Gen 2…
  ◯ Pedagogical
      (reference sample, η.1)
        • Book summary (pedagogical)…
  ✦ Topical
      Nave's Topical Bible · Torrey's New Topical Textbook
        • Topics: Creation · Earth · God · Heaven · Denunciations against
```

The four Strong's notes drop their repeated `Hebrew.` per-note label (the `⌘ Linguistic` header carries the category once) and show the source byline once; the two topic-index notes merge into one lossless union citing both sources. **Every distinct point is preserved** — nothing dropped, only re-parented + de-duplicated. (Residual, by design: where a note's `body_html` *itself* opens with an authored source restatement — e.g. a leading bold "Dictionary (Easton's)." inside the Easton body — S1 does **not** edit the body, so that in-body prefix remains; cleaning it is a future careful pass, not v0.1.0.)

---

## 3. The staged transforms — exact predicates (deliverable D1)

All stages operate **inside `apply_badge_markers`** (effective only under `marker_style == "badge"` — the eth default; in `numbers` mode the flat per-note asides are unchanged, and a flag set under `numbers` is a silent no-op — surface this in the `/customize` help text). The existing `seen_rows` + `seen_book_rows` dedup runs first, unchanged. Each stage reuses existing helpers (`category_for`, `_POPUP_CATEGORY_RANK`, `note_attribution`, `_badge_aside_inner_to_row`).

### S1 — Attribution de-dup → one source byline (build-time, ZERO info loss, do first)

S1 renders each source **once** as `.vn-source-byline` and suppresses the redundant **per-note label**.

- **`source_key(attribution)`** (the canonical grouping key, also the basis of the display byline):
  1. strip a leading per-instance locator — **`Strong's [HG]\d+[,\s]*`** (covers Hebrew **and Greek** Strong's, and the no-comma `Strong's H7779 (PD)` form);
  2. strip a trailing citation locator on per-locator commentary — chapter/verse markers `\b[IVXLC]+\.\d+\b` (e.g. Ephrem `Commentary on Genesis I.11` / `I.14` / `II.2`) and the series tail (`NPNF…`, `vol\.\s*\d+`) — so per-locator commentary from one author+work collapses to ONE byline rather than one-per-locator;
  3. strip trailing licence/PD boilerplate **loop-until-stable** with `((\.?\s*(PD|Public domain|Digital edition[^.]*|CC-BY[^.]*)\.?)+)$` (one anchored pass strips only one segment — TSK's "(1830s). PD. Digital edition…, CC-BY 4.0." needs the repeat to reach the clean "treasury of scripture knowledge (1830s)");
  4. casefold + collapse internal whitespace.
  - *Verified safe for grouping:* across all 1,043 distinct attributions only 2 keys collapse >1 attribution, both intended (all Strong's H/G-numbers → one key; one `Alter`/`alter` casing). Stripping the Strong's number is lossless because the headword lives in the body. Notes with empty/`None` attribution group under one "—" (unattributed) bucket.
- **Display byline** = the **algorithmic** trimmed form of `source_key`'s pre-casefold source string (author + work + year, locator + boilerplate removed) — *this is the contract* (lossless, deterministic). The §2 example bylines are *illustrative of the intended polish*; an **optional curated display-name map** for the highest-frequency sources (Strong's, TSK, Easton, Nave's, Torrey, the named fathers) MAY be added for cosmetic polish, but it is not required and **must never change `source_key`** (grouping). Note: a date like Ephrem's "(c. 360)" lives in the body/label, not the attribution — do not expect it in the algorithmic byline.
- **Per-note label suppression** (the fix to the de-dup goal): suppress the leaf's `<span class="note-label">` **when its text — normalized (strip a trailing `.`, casefold) — equals the KIND's default label** (`kinds.yaml[kind].label`, e.g. `lang-hebrew`→`Hebrew`, `topic-nave`→`Topic`). *Verified:* this fires for **85,936 / 91,733 notes (93.7%)** and correctly **RETAINS** the ~5,797 whose label carries unique info beyond the kind default (e.g. `comm-ethiopian` "Athanasius of Alexandria (350)." — a distinct father + date). Do **NOT** key on the category label (it never equals the kind label → the predicate would never fire). S1 does **not** edit `body_html` (fragile — see the §2 residual note).
- **`comm-ethiopian` double-byline guard:** these bodies are pre-wrapped `<aside>` fragments carrying their OWN inner byline. Detect a self-attributing body by a **structural marker** (an inner byline element / nested `<aside>` in `body_html`) — NOT by token-matching the author string against the attribution (the attribution may say "Ethiopian Orthodox Tewahedo" while the body names a father) — and **suppress the GROUP byline** for such notes (apply per-note for ALL comm-ethiopian, not only single-note groups, since a verse can carry two). Emit a build-time suppression count/manifest so the implementer can eyeball a few verses.
- **Lossless invariant:** S1 only relocates the source string (to the byline) and suppresses a label that merely repeats the kind default; no leaf note is dropped; the distinct-point set is conserved (§4).

### S2 — Group by CATEGORY → SOURCE → emit the cascade markup (build-time, ZERO info loss)

S2 turns the flat surviving-row list into the §2 cascade.

- **Bucket key:** `(category_rank(kind), source_key(attribution))`. Category order = the existing `_POPUP_CATEGORY_RANK`. Source order within a category = first-appearance (stable). Note order within a source = existing doc order (`suffix`).
- **Emit** one `section.vn-group note-cat-{cat}` per category (one `.vn-cat-head` = glyph + label), one `.vn-source` per source (one `.vn-source-byline` + its `.vn-item` leaves). The repeated category prefix vanishes because the label lives once in the header (delivered jointly by S1's label suppression + the header).
- **Lossless invariant:** pure re-grouping — every row that survived the live dedup appears exactly once under its `(category, source)`; surviving-row count out == in.
- **Composition:** S2 owns the cascade emission; S1 controls per-note label/byline dedup *within* it. If S2 is OFF, output stays flat; if S2 ON and S1 OFF, the byline still renders once but per-note labels are retained. Default eth = S1+S2 both ON.

### S3a — Topic-note dedup + Nave's/Torrey union (build-time, easy, safe)

- **Within a topic note** (`category_for(kind) == "topic"`), parse the term list after `appears under:` (verified: all 48,099 topic notes use this `Topics. … appears under: …` form; terms never contain commas), split on `,`, trim, **dedup case-insensitively preserving first-occurrence order**, then **render every surviving term in Title Case** (`CREATION`/`Creation` → `Creation`) with `·` separators (Nave stores UPPERCASE, Torrey Title Case → normalize to Title Case for a uniform union).
- **Union-merge** all topic-category notes on the verse (`topic-nave` + `topic-torrey`) into ONE `Topics:` note whose term set is the case-insensitive union (first-appearance order, Title-cased), citing every contributing source in the byline (`Nave's Topical Bible · Torrey's New Topical Textbook`).
- **Lossless invariant:** the output term set equals the case-insensitive union of all input term sets (a build-time assertion, §4); no contributing source dropped from the citation.

### S3b — Collapse NEAR-identical bodies within a verse (careful; default OFF / opt-in)

- **Predicate:** within a verse **and within the same category**, compute **Jaccard similarity over the set of casefolded `\w+` tokens of the tag-stripped body**. Collapse a pair only when `Jaccard ≥ 0.92`. Keep the **longest** plain-text body; footnote the dropped note's source on the kept note (`(also: <source>)`).
- **Hard guards (completeness is non-negotiable):** never collapse across different categories; never below threshold; never collapse two notes with different `anchor` words unless their bodies still clear the threshold (so the בְּרֵאשִׁית/בָּרָא twins — *different words, different bodies, Jaccard ≈ 0.15* — stay separate; the four Strong's entries score <0.12; S2's co-location already answers the visual "described twice" concern). Every collapse writes a manifest entry (§4) for [USER] review.
- **Note:** the exact-duplicate `xref` (Gen 1:1 suffix `""`/`"c"`) is *already* removed by `seen_rows` — S3b is strictly for NON-identical near-dups.

### S4 — Semantic combine across sources (DEFERRED, opt-in, not wired in v0.1.0)

Risky for completeness + heavy (LLM build pass). **Deferred**; **no field wired** in v0.1.0. Reserved name: `note_semantic_combine`.

---

## 4. Completeness / never-drop-a-distinct-point guard (deliverable D2)

The live code has only `notes_deduped` / `notes_collapsed` counters — not a conservation proof. This spec mandates a build-time guard:

- **`body_fingerprint(note)`** = SHA-1 of the tag-stripped, whitespace-normalized, casefolded **stored `body_html` (field 7)** — computed ONCE before any rendering / label-prepend, so it is **invariant under S1's label/byline relocation** (do NOT fingerprint the rendered row).
- A **distinct point** = a `(source_key, body_fingerprint)` pair (topic notes are handled separately, below).
- **`DISTINCT_IN`** = the set of `(source_key, body_fingerprint)` pairs that **SURVIVE the existing two-layer live dedup** (`seen_rows` in-verse **and** `seen_book_rows` cross-verse — both run first, unchanged). Exact/near duplicates the live layers removed are *not* distinct points and are excluded from IN.
- **For S1, S2 (pure, must be lossless):** assert `DISTINCT_OUT == DISTINCT_IN`. A violation **fails the build** (a stage dropped/mutated a distinct point).
- **For topic notes (S3a):** EXCLUDE them from the general `(source_key, body_fingerprint)` assertion (the union-merge intentionally changes both key components). Their invariant is a **term-SET union keyed on `term_casefold` ONLY** (source-independent): assert `OUT term-set == ∪ IN term-sets`, plus a separate check that **no contributing source is dropped from the byline citation**.
- **For S3b (lossy-by-design, bounded):** every collapse appends to a manifest `<build-output_dir>/_rehaul/nearbody_collapses_<edition>.jsonl` (derive the dir from the build's `output_dir`, NOT a CWD-relative `dist/` — `apply_badge_markers` runs under a caller-supplied temp tree, and `dist/` is gitignored anyway) — one record `{verse, kept_id, dropped_id, jaccard, kept_len, dropped_len, alt_source}`. Guard: assert every record has `jaccard ≥ 0.92` and a non-empty `alt_source` footnote on the kept note; a test asserts S3b never fires below threshold and never produces a collapse whose dropped source is absent from the kept note.

---

## 5. Reader-robust acceptance criteria (deliverable D4)

New tests (none exist in 06-06 §5's grouping/colour tests):

1. **`test_note_cascade_structure_present`** — build a small eth fixture; for a multi-category verse assert: one `section.vn-group` per present category in `_POPUP_CATEGORY_RANK` order; each group has exactly one `p.vn-cat-head` whose **text contains the category label** (not glyph-only); multi-source categories have one `p.vn-source-byline` per source; a kind-default per-note label appears **zero** times outside the header (and a *non-default* label, e.g. a comm-ethiopian father name, is retained).
2. **`test_note_cascade_backgrounds_off_still_structured`** — load **BOTH** the gated robust-CSS append **AND** `epub_working/stylesheet.css`, build the cascade DOM, strip only `background`/`background-color`/`border-radius`/`box-shadow` declarations, then assert: each `.vn-group` resolves to a `border-left` with **width > 0 AND a non-transparent colour**, and **at least two different categories resolve to different border-left colours** (so a single uniform rule can't satisfy it); `.vn-cat-head` retains `font-weight:700` + a `border-bottom`; `.vn-source`/`.vn-item` retain an indent. (Encodes the north-star acceptance line; meaningful only because it resolves the cascade against the merged stylesheet — the gated append alone has the group spine, the leaf spine comes from the base sheet.)
3. **`test_note_cascade_glyph_has_label_text`** — every `.vn-cat-sym` glyph is accompanied by its category label **as text** in the same header (fonts-off / tofu safety).
4. **Build guard (in the structural-audit lint pass):** no `.vn-cat-head` / `.vn-source-byline` is a `<div>` styled by background only; category identity must be expressible as text + border with backgrounds removed.

---

## 6. Option wiring + byte-stability (deliverable D5)

**Fields** — flat per-edition booleans in `content/editions.yaml` (the parser favours flat scalars; mirror the shipped `verse_popups` bool):

| Field | Stage | Code default (absent) | eth edition |
|---|---|---|---|
| `note_attribution_dedup` | S1 | `False` | `True` |
| `note_group_by_category` | S2 (cascade) | `False` | `True` |
| `note_topic_dedup` | S3a | `False` | `True` |
| `note_nearbody_collapse` | S3b | `False` | `False` (opt-in) |
| *(reserved)* `note_semantic_combine` | S4 | — not wired | — |

**Resolving §6.5-vs-"default-on":** §6.5 wants additive features to default to "don't change anything," so the **code** default for every absent field is `False` (`edition.get(field, False)`) — an unset build is byte-identical. "Default-on for the Ethiopian Bible" = **explicitly set the flags `True` on the `ethiopian-tewahedo` edition record only** (a deliberate, one-time byte re-baseline of *that* edition). The 9 KJV editions leave the fields absent ⇒ `False` ⇒ byte-identical. Builders flip per-edition in `/customize`. *This does not break the byte-stability gate:* the gate's determinism assertion is on **catholic-study** only (`test_byte_stability_gate.py:92`); eth is used only for the distinctness check, so eth's `True` flags do not trip it.

**Wiring (RULES §9; mirror `verse_popups` at every layer):**
1. `scripts/web_editions.py` `api_customize_data` (~`:400`, beside `verse_popups`): add `"note_attribution_dedup": e.get("note_attribution_dedup", False)`, etc.
2. `scripts/api/editions.py`: add each field to **`EDITABLE_BOOL`** (in **`api_save_edition_meta`**, `:726-731`) so the SAVE path writes a real YAML bool, **and** to the **`EDITABLE`** set (in **`api_preview_edition_changes`**, `:605-644`) so the `/customize` preview-diff surfaces it. **Do NOT add to `EDITABLE_TEXT`** (`:692-725` — that would coerce the bool to a string). The bool save path validates `True/False`, writes via `_patch_yaml_entry`, and clears `load_editions` + `compute_matrix` caches (`:1067-1091`) — no new write code.
3. `scripts/templates/customize.py`: add one checkbox per field under a "Note presentation" sub-section, `${e.<field> ? 'checked' : ''}`; the generic `querySelectorAll('input, select, textarea')` collection (`:1474-1483`) picks it up with zero per-field JS (RULES §6.4). Help text: explain each toggle **and note the toggles are effective only under `marker_style = badge`** (the eth default; under `numbers` they are a no-op).
4. `scripts/build_edition.py`: read the flags **inside `apply_badge_markers` from the already-passed `edition`** (`edition.get("note_attribution_dedup", False)` etc. — no signature change; `apply_badge_markers` is invoked at `:4497`). **Each stage MUST short-circuit to a zero-touch no-op when its flag is `False`** — the proven pattern is `apply_reader_toc_transforms` (`:2755-2764`).

**Cache caveat (`scripts/core/build_cache.py:274-279`):** `compute_cache_key` JSON-serializes the whole edition record, so an **absent** field leaves the key unchanged (byte-identity preserved); a field written at its default still busts the cache (harmless, deterministic) — prefer leaving it absent on the 9 editions. The rehaul reads **no new input file** (it transforms already-loaded notes; `build_edition.py` source is already hashed), so **no cache-key input change is needed**.

**Byte-stability proof obligation (WIN runs, per change):**
1. **PRIMARY:** `tests/test_byte_stability_gate.py::test_editions_build_valid_distinct_and_flagship_is_deterministic` (slow-tagged ~205s — run explicitly; on Windows pass `--basetemp` + `PYTHONUTF8=1`). Builds eth/catholic-study/jewish-study, rebuilds the flagship, asserts identical normalized per-member zip digest (the gate normalizes the generator URN, `dcterms:modified`, `dc:date`, copyright year). **For the 9 KJV editions specifically: assert their EPUB OUTPUT is byte-identical when the flags are absent** (the load-bearing latent-when-unset check).
2. **GUARD (not the primary proof):** `apply_badge_markers` operates on the per-edition **temp tree**, NOT `epub_working/`, so a regen should leave `epub_working/` untouched — confirm `git diff epub_working/` is empty as a guard that the rehaul did not accidentally mutate the base, but the real byte check is item 1's per-edition output.
3. **Flagship `catholic-study` epubcheck 0/0/0/0** (a canon-filtered edition — `feedback_gate_canon_filtered_editions`), via the `--jar` path.
4. **Nested-anchor guard** after any base mutation: `test_nested_anchors` + `check_nested_anchors --fix` (`feedback_base_invariant_gating`).
5. `ebible verify errors=0`.
6. **Re-baseline `ethiopian-tewahedo`** intentionally (its flags are `True` ⇒ its bytes change by design) and visually QA on a real device (Apple Books + an e-ink/`.kepub` path for the backgrounds-off acceptance).

**Back-compat unit tests** (mirror `test_reader_toc_transforms_default_is_no_op`, `tests/test_scripts.py:4912-4923`): each stage with its flag absent/`False` returns zero-touch stats and leaves HTML byte-identical. Plus `test_customize_data` exposure + a `test_save_*_round_trip` per field (real YAML bool, comments preserved, other editions don't gain the key).

---

## 7. Implementation map (where each piece lands; deliverable D6)

| Piece | File · anchor | Action |
|---|---|---|
| Stage flags read | `build_edition.py` `apply_badge_markers` (read from passed `edition`) | 4 `edition.get(..., False)` reads inside the function; no signature change; call site unchanged at `:4497` |
| Cascade bucketing + emission (S1/S2/S3a/S3b) | `apply_badge_markers` `:1856-2074` (row assembly `:1960-2003`, aside emit `:2029-2035`) | replace the flat `"".join(rows)` with grouped `section.vn-group` emission; reuse `_POPUP_CATEGORY_RANK`, `category_for`, `note_attribution`, `_badge_aside_inner_to_row`; existing `seen_rows`/`seen_book_rows` run first, unchanged |
| `source_key` + display byline + kind-default-label table | new helper near `apply_badge_markers`; kind labels from `config.kinds_by_code()` | §3 S1 |
| Completeness guard | new helper + assertions in `apply_badge_markers` | §4 invariants; S3b manifest under the build `output_dir` |
| Robust CSS append | **define** `apply_note_cascade_css` near `apply_note_popup_style` (`:1761-1771`); **call** it in `build_one`'s gated `css_path.is_file()` append block (`:4286-4303`, mirroring the `apply_note_popup_style` call at `:4297-4303`) | §2 CSS (incl. the 15 explicit per-category group spines), appended only when `note_group_by_category` on |
| Tinted-card palette | `epub_working/stylesheet.css:846-879` | **unchanged** (reference, don't re-author) |
| Option fields | `web_editions.py` `api_customize_data` (`:400`); `api/editions.py` `EDITABLE` (`:605-644`, preview) **+** `EDITABLE_BOOL` (`:726-731`, save), NOT `EDITABLE_TEXT`; `templates/customize.py` | §6 wiring |
| Tests | `tests/test_scripts.py`, `tests/test_byte_stability_gate.py` | §4/§5/§6 tests |

---

## 8. Stage sequencing for WIN (safest first)

`S3a` (cheap, obviously-correct topic union) + `S1` (label/byline dedup) → then `S2` (cascade emission, the structural change) → re-baseline eth + device QA → `S3b` later as a separate, default-OFF, manifest-reviewed opt-in. Each stage = its own commit + its own byte-stability proof. `S4` deferred.

## 9. Open decisions (flagged for WIN / [USER]; do not block)

- **`dict-easton` files under category `hist`.** In the cascade, Easton entries render under `⌂ Historical / Cultural`. For v0.1.0 keep this (no taxonomy/registry edit) — the **source byline** "Easton's Illustrated Bible Dictionary (1897)" makes it explicit. A dedicated `dict` category is a possible future `categories.yaml` addition (out of scope).
- **`comm-ethiopian` pre-wrapped body / byline double-print** — the structural-marker detection (§3 S1) is flagged for a quick eyeball on a few `comm-ethiopian` verses during implementation (the suppression manifest supports this).
- **ADE as a distinct target:** the e-ink research treats Kobo plain-`.epub` (Adobe RMSDK = white-label ADE WebKit) as the ADE-class path; the §5.2 backgrounds-off test covers the CSS-stripping class regardless.

## 10. Constraints carried (master plan + RULES)
- **Build-time, lossless, additive, reversible, option-gated** — never re-write the 91,733 stored notes (RULES §2/§7.2).
- **Never touch the marathon core** (`build_standalone.py`, `core/manuscript_*`, etc.) — this spec only touches the 9-edition / eth EPUB build path.
- **9 KJV editions byte-identical when the fields are absent**; eth is the single intentional re-baseline.
- **Completeness is non-negotiable** — the §4 guard is the enforcement, not a guideline.

---

## Addendum A — extra reader-helper popup: same-file category-legend footnote (user-sanctioned 2026-06-08; Stage C builder option)

**Why.** The user sanctioned an extra popup *if it helps the reader*. The highest-value help: when a reader sees the cascade's category glyph (◇ ⌂ ⌘ …) they can tap it to learn what that category MEANS, **inline, without leaving the verse**. Today the in-note `.note-sym` cross-file link `legend.xhtml#legend-{cat}` is emitted in `scripts/inject.py:230` (`build_aside`; also re-baked at `scripts/resync_marker_glyphs.py:179`), with the destination row + description rendered in `scripts/matter_pages.py:280-284`. A cross-file link NAVIGATES away (jarring) and, being cross-file, never pops as a footnote. This addendum adds an in-file popover using the SAME proven mechanism as the existing note popups.

**Mechanism (native EPUB3, NO JS) — emitted POST-SPLIT, per output piece (this is load-bearing).** EPUB3 footnote popovers (`epub:type="noteref"` ↔ `epub:type="footnote"`) render inline ONLY when the referrer and the target aside are in the **same XHTML file** (Apple Books shows a popover; cross-file navigates). ⚠ The reader file-splitter is **default-ON** (`DEFAULT_READER_FILE_SPLIT=True`, ~0.4 MB target, `build_edition.py:2189`): each book is fragmented into many output pieces, and `rewrite_links` (`build_edition.py:2446`) promotes any noteref whose target id lives in a *different* piece to a cross-file href. So a per-BOOK shared aside (one copy, in one piece) would make the glyph NAVIGATE in every other piece — strictly worse than today. **Therefore the popup is built by a PASS THAT RUNS AFTER `apply_file_split`, on each output piece, entirely in the per-edition TEMP tree (never `epub_working/`).** Gated by `note_category_legend_popup`; a no-op when off ⇒ 9 KJV byte-identical.

For each output piece, when the flag is on:
1. Find every cascade category header in the piece — `section.vn-group.note-cat-{cat} > p.vn-cat-head > span.vn-cat-sym` (the category id `{cat}` is read off the enclosing group's `note-cat-{cat}` class). **§2's header markup is unchanged** — the popup is a purely post-split decoration, so there is NO §2/Addendum markup conflict.
2. For each category present in the piece, emit ONE **piece-local** category-legend aside into a notes-section container in that piece (XHTML `hidden=""`, same structure as `ensure_chapter_notes_section`, `scripts/inject.py:602`, `id="notes-{bxx}-c{ch}"`):
   ```html
   <aside class="cat-legend note-cat-{cat}" id="catlegend-{piecestem}-{cat}" epub:type="footnote">
     <p><span class="cat-legend-sym" aria-hidden="true">{glyph}</span>
        <strong class="cat-legend-label">{label}</strong> — {description}.
        <a class="cat-legend-more" href="legend.xhtml#legend-{cat}">Full guide ›</a></p>
   </aside>
   ```
   `{piecestem}` = the output file stem (e.g. `index_split_010`) so the id is unique per FILE; `{description}` reuses the `categories.yaml` `description` (one source of truth; rendered in `matter_pages.py:284`, read via `config.load_categories()`, `scripts/core/config.py:288`).
3. Rewrite each in-piece header glyph `span.vn-cat-sym` → a same-file noteref:
   ```html
   <a class="vn-cat-sym" id="catref-{piecestem}-{cat}-{n}" href="#catlegend-{piecestem}-{cat}" epub:type="noteref" title="What is &ldquo;{label}&rdquo;?">{glyph}</a>
   ```
   `{n}` increments per occurrence and is unique **within the output file** (a piece holds several chapters in one id-space — reset `{n}` per piece, NOT per chapter). All occurrences in the piece point at the ONE piece-local `catlegend-{piecestem}-{cat}` aside (glossary-term pattern: many noterefs → one footnote target, epubcheck-valid; the aside carries **no** `note-back ↩` — a footnote needs none). The `catref-`/`catlegend-` id prefixes are disjoint from the existing `ref-`/`note-`/`vbadge-`/`vnotes-`/`legend-` namespaces (verified).

Because the aside is co-emitted into the SAME piece as its referrers, every glyph noteref is same-file ⇒ it actually pops.

**Reader-robustness + fallback (the load-bearing guarantee).** This is the exact mechanism the shipped note popups use (`apply_badge_markers` replaces the first per-note aside in place, `build_edition.py:2058`, inside `<aside class="notes-section" epub:type="footnotes" hidden="">`, `inject.py:602`), so its behaviour matches them — Apple Books pops the popover (device-QA-confirmed for note popups; the `hidden` parent does not block the popover, as Apple force-reveals footnote asides). The UNIVERSAL fallback for any reader that does not pop a footnote is the **already-shipped "A Guide to the Notes" page** (`legend.xhtml`, written + put in the OPF spine + nav ToC unconditionally by `inject_symbol_legend_page`, `matter_pages.py:306,336-346`, called at `build_edition.py:4519`); each cat-legend aside also links "Full guide ›" to it. So the popover is **pure progressive enhancement** — where it works it saves a page-jump; where it doesn't, nothing is lost vs today (the glyph + the always-visible legend page remain). An e-ink-primary edition may leave it OFF.

**Stage-C device-QA open items (verify on real devices, with the §5 backgrounds-off pass):** (a) on a reader that neither pops a footnote nor honours `hidden`, a noteref jumps to the in-piece aside — benign; confirm on Apple Books + ADE. (b) **`.kepub` / Kobo:** `kepubify` auto-converts forward internal links meeting its conditions (target id; ≥9 chars; ≤5000 chars; forward) into popups (e-ink research §1, §7-③) — the cat-legend noterefs clear the 9-char floor (good, they pop), but adding another internal-noteref class to a cross-reference-dense Bible compounds the documented "kepub sprouts spurious popups" hazard; verify the `.kepub` build does not over-popup. `catref-`/`catlegend-` ids are ASCII + hyphen-only (no colon/non-ASCII), so they never trip the research §1 non-ASCII-id silent break.

**Reader-robust acceptance for the popup:** the header always prints the category `{label}` text beside the glyph, so a missing-glyph font never hides the category; the popover content leads with the label text, not the glyph; no background/card is load-bearing. (Folds into the §5 `test_note_cascade_glyph_has_label_text` assertion.)

**Secondary option — split an overloaded note (`note_split_long_bodies`, default OFF / opt-in).** When a single note's rendered body exceeds a plain-text length threshold, render a short lead-in (headword + first clause) in the merged `verse-notes` aside and move the FULL body into its own dedicated `epub:type="footnote"` aside reachable by a "more ›" noteref. **Splitter caveat (same root cause):** a long body is exactly what pushes a piece over the 0.4 MB target, so the lead-in and its full-body aside must be **co-located in the same output piece by construction** (emit the body aside into the same piece as its lead-in, in the post-split pass) for the "more ›" to pop; where co-location is impossible it degrades to a cross-file navigate — still **lossless**, and the §4 guard treats the relocated full body as a conserved distinct point. Opt-in, separate from the legend popup, lower priority.

**Builder options (wire per §6; `EDITABLE_BOOL` + `EDITABLE`, NOT `EDITABLE_TEXT`; code default `False` ⇒ 9 KJV byte-identical; eth `True`; effective only under `marker_style = badge`):**

| Field | What | Code default | eth |
|---|---|---|---|
| `note_category_legend_popup` | category-glyph → same-piece legend popover | `False` | `True` |
| `note_split_long_bodies` | overloaded-note → own popup | `False` | `False` (opt-in) |

**epubcheck / base-invariant:** the header glyph becomes ONE `<a>` inside `<p class="vn-cat-head">` — no nested `<a>` (the leaf `.note-sym` anchors are unchanged), so `check_nested_anchors` stays clean; many noterefs → one footnote target is epubcheck-valid; the cat-legend asides ride in the existing per-piece notes-section container (`hidden=""`, no new file structure). The whole pass runs in the per-edition temp tree post-split, so it carries the §6 byte-stability proof obligation and never mutates `epub_working/`.

**Implementation hook:** a new gated pass that runs **after `apply_file_split`** (so co-location is per output piece), reading `note_category_legend_popup` from the edition; reuse `config.load_categories()` (symbol + label + description) and the existing legend description text (do NOT duplicate it). Emit nothing when the flag is off.
