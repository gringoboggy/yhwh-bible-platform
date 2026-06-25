# Kobo run-on-popup research — why study-note popups read as one wall & the fix

> Research brief for the WIN lane (owner of `scripts/build_edition.py`). Audience: an engineer who will implement the fix and device-test on a real color Kobo. Be ready to A/B against the user's own "Cardo" reading font in the native **Footnote preview** overlay.
>
> Date: 2026-06-24 · Lane: written on Mac (verify/research), for WIN to implement. This file is FINDINGS ONLY — no scripts/content/epub_working edits. Sources are inline: `file:line` for code, full URLs for web. Every code claim was re-checked against the working tree; the decisive U+2028-survival claim was checked against a *built* `.kepub.epub`.

## TL;DR

The run-on is **not** in our build and **not** in kepubify. The study/cascade `verse-notes` popups emit good nested block structure (`<aside>` > `<section>` > `<div class="vn-item">` > `<p>`), and kepubify v4.0.4 preserves every one of those block parents. The collapse happens at **read time, inside Kobo Nickel's native "Footnote preview" overlay**, which renders the linked node through a hardcoded native stylesheet that drops the book's CSS and supplies its own zero-margin `p { font-size:%1px; line-height:1.4em; }` rule — so sibling blocks abut with no gap. Our **only** inter-block separators in this family are hidden `<span class="vn-sep">` spans carrying a U+2028 LINE SEPARATOR; the overlay's plain-text extractor drops that U+2028 (verified: kepubify *keeps* it — it is present 70× in a built kepub — so the drop is Nickel's, at render). Result: category heads, source bylines, and individual notes render indistinguishably as one block. **The one recommended fix:** give the study/cascade family the same treatment the translation (`vnote-*`) family already ships under K-R14 — an **eink-gated, visible literal separator (`<br>` + a dot-rule glyph) carried as real text inside each block**, because the project's own device A/B proves that only *visible literal text and `<br>`* survive the Nickel extractor (hidden spans, U+2028-in-span, and CSS margins do not). It must be **eink-gated** so the 9 KJV / non-eink editions stay byte-identical, and the marker glyph must be the device-proven `·` (U+00B7) dot-rule, NOT `•` (U+2022), which this device's own QA disqualified as a near-crash. The fix is block-to-block only; whether note *bodies* need the same treatment is an open question for the device A/B.

## Problem statement

The user reports: on his **color Kobo** (Cardo reading font, eInk target), tapping a study-note badge opens the native Footnote preview and **"everything runs on in one sentence"** — the multi-category, multi-source, multi-note apparatus shows as a single undifferentiated flow (`docs/superpowers/notes/2026-06-14-kobo-round7-device-qa.md:51-54`, K-R7-3: *"still no popup formatting so everything doesnt run on in one sentance"; Footnote preview shows all language blocks concatenated*).

This is the study/cascade `verse-notes` family. (The sibling translation `vnote-*` family had the same symptom; it was already given a fix under K-R14 — see §1. The study family was not, and that is the residual bug.)

## Current state (from the codebase)

### What we emit (structure Y — and it is good structure)

The study/cascade popup is real nested block markup, baked at **emission** time:

```
<aside class="… verse-notes" id="vnotes-…" epub:type="footnote">
  <p class="vn-back">↩ <strong>ch:v</strong></p>
  <section class="vn-group note-cat-…">
    <p class="vn-cat-head">[SEP_CAT]<span class="vn-cat-sym">glyph</span> Category</p>
    <div class="vn-source">
      <p class="vn-source-byline">[SEP_BYLINE]Source</p>
      <div class="vn-item note-…">[SEP_ITEM]<p>…note body…</p></div>
      <div class="vn-item note-…">[SEP_ITEM]<p>…note body…</p></div>
    </div>
  </section>
</aside>
```

Emit sites (`scripts/build_edition.py`): the merged single-`<aside>`-per-unit at `:4303-4308`; the cascade `<section>`/`vn-cat-head`/`vn-source-byline` at `_emit_cascade_sections` (`:3831`, separators injected at `:3854` and `:3866`); the per-note `<div class="vn-item">` row at `_badge_aside_inner_to_row` (`:2812`, separator at `:2825`); split-note continuation rows at `_chunk_vn_item_row` (`:3537`, separators at `:3579` and `:3581`).

### The separators we use (the actual defect)

The three separator constants (`scripts/build_edition.py:2600-2602`), verbatim:

```python
_VN_SEP_ITEM   = '<span class="vn-sep"> • </span>'
_VN_SEP_CAT    = '<span class="vn-sep"> ¶ </span>'
_VN_SEP_BYLINE = '<span class="vn-sep"> ◦ </span>'
```

These are **hidden** (`<span class="vn-sep">` + `.vn-sep { display: none; }` at `:2607`) and carry a **U+2028 LINE SEPARATOR** as their only line-break payload. The design intent (`:2590-2599`, K-R5-7 / K-R6-3) was: CSS hides them wherever CSS applies (the page, any conformant popup), and the CSS-blind eInk preview's raw-text extractor would surface the U+2028 as a real line start. The earlier `\n` variant was found on-device to COLLAPSE in the Footnote dialog (whitespace-normalized), so it was flipped to U+2028 (`:2596-2599`, K-R6-3).

**Why this fails for the study family:** K-R14 (`:2626-2628`) documents that Kobo's tag-stripped Footnote preview *drops* U+2028 inside `.vn-sep` spans, and that plain `<br>` + a visible dot-rule paragraph survive the extractor better. The K-R14 fix was applied — but only to the translation `vnote-*` family (see next).

### The K-R14 fix exists — but only for the translation family

The K-R14 survivable separators (`scripts/build_edition.py:2629-2638`):

```python
_KOBO_VNOTE_BR  = '<br class="kobo-vnote-br" />'
_KOBO_VNOTE_GAP = '<p class="vnote-kobo-sep"> · · · </p>'   # visible · · · dot-rule
```

These are injected by `add_eink_vnote_preview_breaks` (`:2638`), whose regex `_VNOTE_BR_BEFORE_P_RE` (`:2632-2635`) matches **only** `<p class="vnote-…">` paragraphs — the translation family. The pass runs through `apply_vnote_preview_separators` (`:2780-2810`), and its eink leg is already gated: *"K-R14 `<br>` breaks apply only when `target_reader` resolves to `eink`"* (`:2786-2787`, the `eink = … resolve_target_reader(edition) == "eink"` guard at `:2789`). The underlying runtime pass `add_vnote_preview_separators` (`scripts/core/vnote_separators.py:15-18`) is hardcoded to `vnote-text` / `vnote-source-label` classes (`:11-12`) and inserts the **same hidden U+2028 `.vn-sep` spans** — i.e. the runtime pass is translation-only and the survivable-`<br>` leg layered on top of it is translation-only.

**Net: the study/cascade `verse-notes` family never receives any Nickel-survivable separator.** Its only separators are the hidden U+2028 `.vn-sep` spans baked at emission (`:2600-2602`), which Nickel drops.

### eink CSS already carries the K-R14 chrome (so the hook is half-built)

`_EINK_READER_CSS` (appended by `apply_eink_reader_css` only when `resolve_target_reader == "eink"`, `:2417-2421`) already contains the K-R14 break rule and the translation dot-rule styling (`:2388-2391`):

```css
.vnote-kobo-sep { text-align: center; margin: 0.4em 0 0.1em; … }
br.kobo-vnote-br { line-height: 1.6; }
```

So the eink-gated CSS append path and a proven `br.kobo-*-br { line-height:1.6 }` precedent already exist; the study-family fix mirrors them.

### kepubify does NOT flatten the structure (verified twice)

- **Source.** kepubify v4.0.4 `kepub/transform.go`: `transformContentKoboSpans` skip set is exactly `Script, Style, Pre, Audio, Video, Svg, Math` — **`aside` is not in it**, so `<aside>`/`<section>`/`<div>`/`<p>` all hit the default case and are recursed into, with only inline `<span class="koboSpan">` wrappers *added*. `transformContentClean` removes only U+FFFD, Adobe Adept meta, and empty MS-Word `o:p`/`st1:*` tags — never `p`/`div`/`section`/`aside` (verified via raw source, URL in Sources).
- **Empirical.** Unzipping a real built study kepub (`build/matrix-m3/YHWH-catholic-study-v0.1.0-kobo-navy.kepub.epub`): the `verse-notes` cascade survives intact — `<aside class="study-glossary-cat verse-notes" … epub:type="footnote"> > <section class="vn-group note-cat-xref"> > <div class="vn-item note-xref-citation"> > <p class="note-tradition-label">…`. Block structure fully preserved.

### kepubify KEEPS the U+2028 — the drop is Nickel's, at render time (decisive correction)

The project's round-7 QA note hedged: *"kepubify wraps every text node in koboSpan — the preview extractor **likely** flattens spans and drops U+2028"* (`docs/superpowers/notes/2026-06-14-kobo-round7-device-qa.md:54-56`). The K-R14 source comment phrases it as "drops U+2028 … after kepubify's koboSpan pass" (`build_edition.py:2626-2628`). To remove the ambiguity I checked the built artifact directly:

- In `build/matrix-m3/YHWH-catholic-study-v0.1.0-kobo-navy.kepub.epub`, U+2028 appears **70 times**, each inside `<span class="vn-sep"><span class="koboSpan" id="kobo.0.1"> • </span></span>`. The character is present and intact post-kepubify.
- Confirmed by source: kepubify's `splitSentences` classifies only ASCII `\t \n \f \r` and space as whitespace; U+2028 is `InputAny` and is **preserved** inside its koboSpan (it is not whitespace-stripped, and `isSpace(" • ")` is false because the bullet is a non-space, so the segment is wrapped and kept).

**Therefore: kepubify does not lose U+2028. Kobo Nickel's tag-stripped Footnote *preview* extractor drops it at read time.** This is corroborated by the project's own `dev/CHANGELOG.md:658` (*"survives Kobo tag-strip better than U+2028 spans"*). The downstream conclusion is unchanged — Nickel is the culprit and visible literal text + `<br>` is the answer — but the causal chain must be stated correctly: do **not** attribute the drop to kepubify/koboSpan.

## Findings — the load-bearing questions, answered

### Q1. Where exactly does the run-on happen — our build, kepubify, or the device?

**The device, at read time.** Attribution, separated cleanly:

- **We emit good block structure** (§ above; `:3831`, `:2812`, `:4303-4308`). Not the cause.
- **kepubify preserves it** and preserves U+2028 (verified by source + built artifact). Not the cause.
- **Kobo Nickel's native Footnote preview overlay flattens at render.** It is a native-Qt dialog that drops the book stylesheet and applies a hardcoded `p { font-size:%1px; line-height:1.4em; }` rule, so sibling blocks abut. The hardcoded paragraph rule and native-dialog override are documented in the firmware-patch source pgaskin/kobopatch-patches#55 (`DictionaryView::fontSize()`, `RegularTouchLabel`, the CSS moved into `libnickel.so`) — a maintainer-grade primary source. And the overlay's content is sourced through a **tag-stripped plain-text extractor**, which is why visible glyphs/`<br>` survive but hidden spans / U+2028-in-span / CSS margins do not (project device A/B: K-R6-3 `build_edition.py:2596-2599`; K-R14 `:2626-2628`; round-7 QA `2026-06-14-kobo-round7-device-qa.md:51-59`).

The Footnote preview is reachable **only** on the `.kepub.epub` artifact — a plain `.epub` does not pop on Kobo (`dev/TOOLCHAIN.md:41`: *"Kobo footnote popups require the KePub artifact; a plain `.epub` won't pop on Kobo"*).

### Q2. What separators actually survive the Nickel Footnote extractor?

From the project's own on-device A/B (the most authoritative evidence for *our* exact pipeline), only two mechanisms are proven survivors, and two are proven non-survivors:

| Mechanism | On-device result | Source |
|---|---|---|
| `\n` whitespace between blocks | **COLLAPSES** (whitespace-normalized) | `build_edition.py:2596-2599` (K-R6-3) |
| U+2028 inside hidden `.vn-sep` span | **DROPPED** by the tag-strip extractor (survives kepubify; Nickel drops it) | `build_edition.py:2626-2628` (K-R14); `2026-06-14-kobo-round7-device-qa.md:54-56` |
| CSS margins / `display` toggles | not surfaced (book CSS dropped in overlay) | kobopatch-patches#55; PublishDrive-style CSS-strip reports |
| Plain `<br>` element | **SURVIVES** | `build_edition.py:2626-2628`; `2026-06-14-…:57-59` |
| Visible dot-rule `<p>` (`· · ·`, U+00B7) | **SURVIVES** and renders in Cardo | `build_edition.py:2630` (`_KOBO_VNOTE_GAP`) |

Untested by our A/B (treat as non-surviving until proven): `<ul>/<ol>/<li>`, `white-space:pre`. No primary source confirms these survive the eInk overlay; the CSS-stripping evidence argues against them.

### Q3. Which glyphs are safe in Cardo in the overlay on THIS device?

Glyph coverage on this device is *not* assumable — there is direct prior evidence of failures:

- `·` (U+00B7) — **PROVEN safe**: it is the live `_KOBO_VNOTE_GAP` dot-rule already shipping in the translation fix (`build_edition.py:2630`), confirmed rendering on-device.
- `•` (U+2022 BULLET) — **HAZARD on this device**: the round-7 badge A/B disqualified the `dot` (•) style: *"DISQUALIFIED — EPUB barely loads / near-crash on Kobo"* (`2026-06-14-kobo-round7-device-qa.md:137`). The glyph itself renders, but the artifact near-crashed. That was the *badge* context (an interactive inline noteref), mechanically distinct from a passive popup-body separator, so it may not transfer — but it is direct prior evidence that `•` has caused instability on this exact device and must NOT be adopted blind. (Note: `_VN_SEP_ITEM` already uses `•` today inside the hidden span (`:2600`), but that span is `display:none` on every CSS-honoring target and its content is *dropped* by the overlay — so `•` is never actually visible on this device today. Making it visible is the new risk.)
- `⁎` (U+2051) — **PROVEN bad**: rendered as an *empty bordered box* (glyph missing from the Kobo font) in the same A/B (`2026-06-14-kobo-round7-device-qa.md:140`). Precedent that asterisk-class glyphs are unsafe.
- `❖` (U+2756) — PROVEN absent from Cardo → blank box, already worked around on eink (`build_edition.py:2645-2651`). Further precedent that Cardo coverage must be tested, never assumed.
- `¶` (U+00B6), `◦` (U+25E6) — **untested on-device**; behind the A/B.

**Conclusion: the only device-proven-safe visible separator glyph is `·` (U+00B7).** The prescription therefore makes the `·` dot-rule the PRIMARY separator face and treats `•`/`¶`/`◦` as A/B-gated alternatives only.

## Root cause

The precise mechanism for OUR failure:

1. The user taps a study-note badge. Because the artifact is a `.kepub.epub`, Kobo Nickel opens its **native Footnote preview overlay** (`dev/TOOLCHAIN.md:41`).
2. The overlay renders the linked `<aside>`'s content through a **tag-stripped plain-text extractor** under a **hardcoded native stylesheet** (`p { font-size:%1px; line-height:1.4em; }`, zero margins) — the book's CSS is not applied (kobopatch-patches#55).
3. Our study/cascade family's only inter-block separators are **hidden `<span class="vn-sep">` spans carrying U+2028** (`build_edition.py:2600-2602`). kepubify preserves them (U+2028 present 70× in the built navy kepub), but Nickel's extractor **drops the U+2028** (K-R14, `:2626-2628`), and `.vn-sep`'s `display:none` plus the hardcoded zero-margin `p` rule mean there is nothing visible to separate the blocks.
4. So the category heads, source bylines, and each `vn-item` note flatten into one undifferentiated run of text — exactly the user's "run on in one sentence" report (`2026-06-14-kobo-round7-device-qa.md:51-54`).
5. The translation `vnote-*` family does NOT have this bug, because K-R14 already gave it visible `<br>` + a `·`-dot-rule `<p>` on eink (`:2629-2638`, regex-gated to `vnote-*` at `:2632-2635`). The study family was never wired into that pass — that asymmetry is the residual defect.

Coverage is not the problem; the structure is good; the separators just don't survive the overlay.

## Recommended fix (for WIN)

Give the study/cascade `verse-notes` family the same eink-gated, Nickel-survivable separators the translation family already has — visible literal text (the device-proven `·` dot-rule) plus `<br>` — replacing the hidden U+2028 `.vn-sep` spans **on eink only**. Do not touch the non-eink path.

### (1) Markup — eink-only separator faces

Add eink variants of the three separator constants. Use the **device-proven `·` (U+00B7)** as the visible marker, not `•`. Each separator is a `<br>` plus a short visible literal run, carried as ordinary text (so the overlay's extractor surfaces it and koboSpan wraps it as a kept segment). Illustrative faces:

```python
# eink-only — Nickel-survivable (visible literal · dot-rule + hard break).
# · (U+00B7) is the only on-device-proven separator glyph (see §Q3); do NOT use • (U+2022).
_VN_SEP_ITEM_EINK   = '<br class="kobo-vn-br" /> · '   # " · "  before each note row
_VN_SEP_CAT_EINK    = '· '                                  # "· "   before each category head
_VN_SEP_BYLINE_EINK = '<br class="kobo-vn-br" /> · '   # " · "  before each source byline
```

(`vn-cat-head` is already the first child of its `<section>`, so its face needs no leading `<br>`; the byline and item rows are mid-flow and do.)

Resulting eink study popup (one category, one byline, two notes), illustrative:

```html
<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote">
  <p class="vn-back"><a href="#vbadge-gen-1-1-s1" class="note-back" title="Back">↩</a> <strong>1:1</strong></p>
  <section class="vn-group note-cat-lexical">
    <p class="vn-cat-head">·&#160;<span class="vn-cat-sym" aria-hidden="true">⚏</span> Lexical</p>
    <div class="vn-source">
      <p class="vn-source-byline"><br class="kobo-vn-br" />&#160;·&#160;Strong's</p>
      <div class="vn-item note-strongs"><br class="kobo-vn-br" />&#160;·&#160;<p>…note one body…</p></div>
      <div class="vn-item note-strongs"><br class="kobo-vn-br" />&#160;·&#160;<p>…note two body…</p></div>
    </div>
  </section>
</aside>
```

Well-formedness: a `<br/>` + bare text immediately inside `<div class="vn-item">`, before its child `<p>`, is valid flow content. This mirrors exactly how `_VN_SEP_ITEM` is placed *today* (`build_edition.py:2825`, `<div class="vn-item …">{_VN_SEP_ITEM}{body}</div>`), and that shipping markup validates epubcheck 0/0/0/0. The empirical structure confirms it: in the built kepub the existing separator sits as the div's first child (`<div class="vn-item …"><span class="vn-sep">…</span><p>…</p>`). Keep the `<br>`/text as the div's first inline children — do NOT push them inside the child `<p>` when the body wrapper is a `<div>`.

**koboSpan precision:** the marker text and the following child `<p>` become **separate** koboSpans (separate element children — verified: `…id="kobo.0.1"> • </span></span><p …><span … id="kobo.1.1">…`), not one combined span. Both survive, so the safety property holds; just do not describe them as wrapped together.

### (2) CSS — eink stylesheet only

The markers are deliberately VISIBLE on eink (CSS-hidden does not survive). Give the new `<br>` line-height room, exactly as the K-R14 vnote rule already does:

```css
/* eink only — study/cascade popup separators are visible literal · dot-rule;
   give the kobo-safe break line-height so notes don't abut. */
br.kobo-vn-br { line-height: 1.6; }
```

Place it in the eink branch where `br.kobo-vnote-br { line-height: 1.6; }` already lives (`build_edition.py:2391`). On non-eink targets the existing `.vn-sep { display:none; }` rule (`:2607`) and the hidden U+2028 spans stay — page rendering is unchanged, because non-eink readers honor the real block CSS.

**What NOT to rely on (proven-negative — do not add):** CSS margins/padding for popup separation; `display` toggles on the source aside; `<ul>/<ol>/<li>` or `white-space` (untested, CSS-strip makes them unreliable); hidden-span U+2028 (Nickel drops it); and crucially the `•` (U+2022) glyph as a *visible* marker (near-crash on this device, §Q3).

### (3) Emitters WIN must change (all `scripts/build_edition.py`)

Each swap is the existing constant → its eink-gated variant, branching on `resolve_target_reader(edition) == "eink"` (`:1979`):

1. `_emit_cascade_sections` cat-head separator, **`:3854`**: `_VN_SEP_CAT` → eink-gated `_VN_SEP_CAT_EINK`.
2. `_emit_cascade_sections` source-byline separator, **`:3866`**: `_VN_SEP_BYLINE` → eink-gated `_VN_SEP_BYLINE_EINK`.
3. `_badge_aside_inner_to_row` per-note item separator, **`:2825`**: `_VN_SEP_ITEM` → eink-gated `_VN_SEP_ITEM_EINK`.
4. `_chunk_vn_item_row` split-note continuation separators, **`:3579` and `:3581`**: `_VN_SEP_ITEM` → eink-gated `_VN_SEP_ITEM_EINK`.
5. eink CSS: add `br.kobo-vn-br { line-height:1.6; }` near `:2391`.

**Implementation prerequisite (load-bearing):** `_emit_cascade_sections` (`:3831`), `_badge_aside_inner_to_row` (`:2812`), and `_chunk_vn_item_row` (`:3537`) currently take **no edition argument**. The eink flag must be threaded into them (or the separator-constant set selected once per edition and passed down). Without that threading the swap cannot be eink-conditional and byte-stability breaks. Do NOT route this through `apply_vnote_preview_separators` / `scripts/core/vnote_separators.py` — that pass is hardcoded to the `vnote-*` translation classes and must stay byte-stable for them.

### eink-gating + byte-stability implication

**CRITICAL constraint:** the 9 KJV editions and all non-eink targets must stay **byte-identical** (regression invariant).

- **By construction, non-eink bytes are unchanged:** every swap is gated to `eink`, and the non-eink path keeps the exact existing constants (`_VN_SEP_ITEM` etc.) and the `.vn-sep { display:none }` CSS. This mirrors the already-shipped K-R14 eink-gating pattern (`:2786-2789`).
- The 4 study editions that emit this family (`ethiopian-tewahedo`, `catholic-study`, `eastern-orthodox`, `evangelical-reformed`) carry `note_group_by_category: true` (`content/editions.yaml:47,193,247,295`) and no stored `target_reader` (default `everywhere`); their eink/KJV variants are produced by `apply_target_override` (`:1985`) on the same records. So eink and non-eink come off the same edition record and the gate is the only thing keeping them apart — the threading in §3 is what makes that safe.
- **No automated golden-hash gate protects the 9 KJV.** The standing byte-stability test is a *determinism* test on representatives, not a frozen-hash check of KJV. The only safety net for this change is a **manual regen + `git diff` over all editions** (off-device) confirming the 9 KJV / non-eink outputs are frozen. Treat that as **mandatory**, not optional.
- **The eink study popups change size** (adding visible `·`/`<br>` markers inflates serialized bytes, and each new inter-tag text run is wrapped by kepubify's koboSpan, `_KEPUB_SPAN_OVERHEAD = 85` B/segment, `:3346`). This feeds the byte-cap split driver (`DEFAULT_NOTE_POPUP_SPLIT_BYTE_CAP = 8_858`, `:3345`) whose device-derived refusal bracket is (8,858 .. 9,273] (`:3325-3333`). **Action:** after the change, re-run the split estimator and the built-kepub hard floor **gate 4n** (`dev/verify_kr2_build.py:317`, `BYTE_FLOOR = 8_858`, judges only koboSpan-bearing artifacts at `:321-337`). The estimator over-estimates (85 vs measured worst 81.3 B, `:3336`), so it stays a safe upper bound, but gate 4n on the built kepub is the acceptance check — some borderline units may split one unit earlier.

## Device-test plan (the user must run this on the real color Kobo)

Build TWO eink `.kepub.epub` artifacts of the same study verse with a multi-note, multi-category, multi-source popup (e.g. the `gen 1:1` / `gen 1:2` units named in the byte-cap forensics, `build_edition.py:3330`), sideloaded as `.kepub.epub` (plain `.epub` won't pop, `dev/TOOLCHAIN.md:41`):

- **A (control):** current build — `verse-notes` study popup with hidden U+2028 `.vn-sep` spans only.
- **B (treatment):** the §1–§3 prescription — visible `·` dot-rule + `<br class="kobo-vn-br">` per block, eink-gated.

Tap the study badge on each and photograph the Footnote preview overlay. Confirm:

1. In **B**, each note item, each category head, and each source byline starts on its own visually separated line (run-on broken); in **A** they run together (reproduces the bug). Also confirm the popup STOPS at the end of the note unit and does not bleed into the next verse (boundary check, O4).
2. The `·` (U+00B7) marker renders in Cardo in the overlay (no missing-glyph box). This is the proven-safe glyph; it should pass. (Closes O3 for `·`.)
3. The popup still **OPENS** for the largest treated unit — pick the worst-case unit near the byte cap and confirm it POPS rather than navigates, cross-checked against gate 4n's measured bytes. This is the critical "does it still load" check — the round-7 `•` near-crash (`2026-06-14-…:137`) is the reason to verify load, not just render.
4. Cross-reference / original-language sub-blocks *inside* a single note body (if present) also separate. If a note body has multiple paragraphs and they still collapse, the same `<br>`+`·` treatment must extend into the per-note body wrapper (`scripts/inject.py:211` `build_aside`, wrap `div|p` selected at `:247`) — currently OUT of scope (O1).
5. **Optional alternate-glyph leg:** only if a denser look is wanted, A/B `¶`/`◦` (untested, O3) — but `·` is the safe default; do not ship `•` as a visible marker without an explicit "does it still load" pass.

Secondary controls (off-device): regen + `git diff` proving the 9 KJV / non-eink outputs are byte-identical; gate 4n on the built eink study kepub; epubcheck 0/0/0/0 on a built eink study artifact (validity is by-precedent — the existing `:2825` placement ships clean — not yet executed for the new markup).

## Confidence & open questions

**Well-supported (high confidence):**
- Root cause is Nickel's native Footnote preview overlay (tag-stripped extractor + hardcoded zero-margin `p` rule), not our build and not kepubify — code + built-artifact + kobopatch-patches#55 + project device A/B.
- kepubify preserves block structure AND U+2028 — verified by source (skip set, `splitSentences`, clean pass) and by a built kepub (U+2028 present 70×). The drop is Nickel's, at render.
- Only visible literal text and `<br>` survive the overlay; hidden spans / U+2028-in-span / CSS margins do not — project device A/B (K-R6-3, K-R14) + dev/CHANGELOG.md:658.
- The study family currently has no Nickel-survivable separator (the K-R14 fix is regex-scoped to `vnote-*` only) — code-verified.
- `·` (U+00B7) is the only device-proven-safe visible separator glyph; `•` near-crashed and `⁎`/`❖` boxed on this device — round-7 QA.
- Byte-stability is preserved by construction on non-eink via eink-gating, but there is no automated KJV golden gate — manual regen+diff is mandatory.

**Open questions (resolved only by the device A/B):**
- **O1 (in-note structure).** This fix separates note ITEMS, category heads, and source bylines — not multiple blocks *within* one note body. If real study notes have multi-paragraph / original-language / cross-ref sub-blocks inside one `<div class="vn-item">`, those inner boundaries still collapse; extending the treatment into `inject.py build_aside` (`:211`, `:247`) would be needed. Confirm via A/B step 4 before committing the extra change.
- **O2 (untested survivors).** `<ul>/<ol>/<li>`, `white-space:pre`, CSS margins are not confirmed to survive the overlay; the prescription deliberately avoids them. Any future use needs its own device test.
- **O3 (glyph coverage).** `·` is proven; `¶` (U+00B6) and `◦` (U+25E6) are untested; `•` (U+2022) is a known near-crash on this device and must not be a *visible* marker without an explicit load-test. A/B step 2/5 closes this.
- **O4 (boundary over-run).** Whether the overlay over-runs past `</aside>` into following siblings on this device is unverified by primary GitHub sources (no clean citation; the merged single-`<aside>`-per-unit emission at `:4303-4308` plus the `-sN` id discipline likely prevent it). A/B step 1 confirms.

## Sources

### Code (all `/Volumes/MacHD2/yhwh-bible-platform/`)
- `scripts/build_edition.py:2596-2607` — separator constants + `.vn-sep{display:none}` + K-R6-3 (`\n` collapses → U+2028) rationale.
- `scripts/build_edition.py:2626-2638` — K-R14: Nickel preview drops U+2028 in `.vn-sep` after koboSpan; `<br>` + visible dot-rule survive; `_KOBO_VNOTE_BR`, `_KOBO_VNOTE_GAP` (`·` U+00B7); `add_eink_vnote_preview_breaks` (translation-only regex `:2632-2635`).
- `scripts/build_edition.py:2388-2391` — eink CSS already ships `.vnote-kobo-sep` + `br.kobo-vnote-br { line-height:1.6 }`.
- `scripts/build_edition.py:2417-2421` — `apply_eink_reader_css` eink gate; `:2482-2506` — `_NOTE_CASCADE_CSS` / `apply_note_cascade_css`.
- `scripts/build_edition.py:2780-2810` — `apply_vnote_preview_separators` (eink gate at `:2789`, K-R14 leg eink-only).
- `scripts/build_edition.py:2812-2825` — `_badge_aside_inner_to_row` (per-note `_VN_SEP_ITEM` at `:2825`, no edition arg).
- `scripts/build_edition.py:3325-3346` — byte-cap split driver: refusal bracket (8,858..9,273], `DEFAULT_NOTE_POPUP_SPLIT_BYTE_CAP=8_858`, `_KEPUB_SPAN_OVERHEAD=85`.
- `scripts/build_edition.py:3537-3581` — `_chunk_vn_item_row` split-note continuation `_VN_SEP_ITEM` at `:3579`,`:3581`.
- `scripts/build_edition.py:3831-3866` — `_emit_cascade_sections` (cat-head `_VN_SEP_CAT` at `:3854`, byline `_VN_SEP_BYLINE` at `:3866`, no edition arg).
- `scripts/build_edition.py:4303-4308` — merged single-`<aside>`-per-unit emission.
- `scripts/build_edition.py:1979` — `resolve_target_reader`; `:1985` — `apply_target_override`.
- `scripts/core/vnote_separators.py:11-18` — runtime pass scoped to `vnote-text`/`vnote-source-label` only.
- `scripts/inject.py:211,247` — `build_aside` per-note body wrap (`div` vs `p`).
- `content/editions.yaml:47,193,247,295` — the 4 study editions' `note_group_by_category: true`.
- `dev/verify_kr2_build.py:317-337` — gate 4n: `BYTE_FLOOR=8_858`, kepub-only serialized-byte floor.
- `dev/CHANGELOG.md:658` — "survives Kobo tag-strip better than U+2028 spans".
- `dev/TOOLCHAIN.md:41,63` — kepub required for popups (plain `.epub` won't pop); confirm ids survive koboSpan.
- `docs/superpowers/notes/2026-06-14-kobo-round7-device-qa.md:51-59` (K-R7-3: run-on report + `<br>` fix direction), `:137` (`dot`/`•` DISQUALIFIED, near-crash), `:140` (`⁎` U+2051 empty box).
- Built artifact (empirical): `build/matrix-m3/YHWH-catholic-study-v0.1.0-kobo-navy.kepub.epub` — U+2028 present 70× inside `<span class="vn-sep"><span class="koboSpan">…</span></span>`; full `verse-notes` cascade intact post-kepubify.

### Web (verified this session)
- kepubify v4.0.4 transform source (skip set, `splitSentences` whitespace classes, clean pass): https://raw.githubusercontent.com/pgaskin/kepubify/v4.0.4/kepub/transform.go
- Kobo native dialog + hardcoded `p { font-size:%1px; line-height:1.4em; }` paragraph rule, `RegularTouchLabel`, `DictionaryView::fontSize()`: https://github.com/pgaskin/kobopatch-patches/issues/55
- Kobo footnote/popup behavior + heuristic spec: https://github.com/kobolabs/epub-spec/blob/master/README.md

### Corrections folded in from the two adversarial verdicts
1. **Mechanism (both verdicts):** the U+2028 drop is **Nickel's tag-stripped Footnote extractor at read time**, NOT kepubify/koboSpan. Verified by source (`splitSentences` keeps U+2028; `aside` not in skip set) and by the built kepub (U+2028 present 70×). The doc now states kepubify preserves it and Nickel drops it.
2. **Glyph safety (verdict 2):** `•` (U+2022) is a documented near-crash on this device (`2026-06-14-…:137`); the prescription's PRIMARY visible separator is the device-proven `·` (U+00B7) dot-rule, with `•`/`¶`/`◦` demoted to A/B-gated alternates and a mandatory "does it still load" check.
3. **koboSpan precision (verdict 2):** the marker text and following `<p>` are SEPARATE koboSpans, not one combined span — corrected in §1.
4. **Implementation prerequisite (verdict 2):** `_emit_cascade_sections`, `_badge_aside_inner_to_row`, `_chunk_vn_item_row` take no edition arg; the eink flag MUST be threaded in for the gate to work — stated as load-bearing in §3.
5. **Citation hygiene (verdict 1):** dropped the over-reach citations (kobolabs/epub-spec#32 "employee-acknowledged" and the threefold #59 use); the native-dialog + hardcoded `p`-rule mechanism is sourced to the maintainer-grade kobopatch-patches#55, "kepub required to pop" to `dev/TOOLCHAIN.md:41`, and O4 is marked unverified by primary GitHub sources.
6. **Validity/byte gates (verdict 2):** epubcheck validity is by-precedent (not executed) → run it as an acceptance gate alongside gate 4n and the non-eink byte-diff.

— End of brief. File: `dev/audit/kobo-popup-formatting-research.md`. Quality template: `dev/audit/kobo-font-override-research.md`. Adversarial verdicts: WS3 verdict 1 (root cause) + verdict 2 (prescription), both folded in.
