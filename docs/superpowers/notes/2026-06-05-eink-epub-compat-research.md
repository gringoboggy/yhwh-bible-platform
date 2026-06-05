# Cross-reader EPUB compatibility research

**Audience:** YHWH Bible-platform Windows build lane. **Purpose:** de-risk four work items — D2 (popup footnote mechanism), D3 (Kobo-safe TOC + title-page/layout structural rendering), D4 (large-file performance / file-splitting plan), D5 (embedded original-language fonts) — by recording what each target reader actually does with the EPUB3 features we depend on, and the single cross-reader-safe pattern to emit for each. Every topic below was researched and then adversarially fact-checked; where the skeptic's verdict corrected the support rating or reasoning, the corrected position is what is recorded here.

**The three readers (as scoped):**
- **Kobo (color e-ink)** — the user's ~$300 color Kobo (Libra Colour / Clara Colour class, Nickel reading stack, current firmware ~4.42–4.45, 2025–2026). Sideloaded. The binding device for D2/D3/D4/D5 because it has two distinct render paths (plain `.epub` via the Adobe RMSDK/Digital-Editions WebKit; `.kepub.epub` via Kobo's own NetFront/ACCESS WebKit) and the weakest CSS/feature support of the three.
- **Apple Books** — iOS + macOS, WebKit engine. The de-facto reference implementation for popup footnotes and the most standards-complete target.
- **Google Play Books** — Android app + iOS app + web reader. Chromium/Blink-derived engines, but re-processes uploaded EPUBs server-side into an internal format, so per-property CSS fidelity is the least predictable and the web reader is the weakest surface.

**How to read the support ratings:** `supported` = works reliably with the recommended markup; `partial` = works with caveats / only on one path / firmware-dependent; `unknown` = no authoritative source and no clean first-hand test, must be device-verified; `unsupported` = does not work. Confidence is the fact-checked final confidence for the whole topic. **No rating substitutes for on-device testing** — the EPUB spec leaves popup/presentation behavior to the reading system, so cross-reader divergence is permanent and spec-permitted.

## Quick-reference support matrix

| Feature topic | Kobo (color e-ink) | Apple Books | Google Play Books | Confidence |
|---|---|---|---|---|
| 1. Popup footnotes (`noteref` + `<aside epub:type=footnote>`) | partial | supported | unknown | medium |
| 2. `<details>`/`<summary>` collapsible TOC | partial | supported | unknown | medium |
| 3. CSS flexbox in reflowable | partial | supported | partial | medium |
| 4. Embedded `@font-face` fonts (Hebrew/Greek/Ge'ez) | partial | supported | partial | medium |
| 5. `position:absolute` / full-bleed cover & title-page art | partial | partial | partial | high |
| 6. Large single-file XHTML perf / file-splitting | partial | supported | unknown | medium |
| 7. KePub vs plain sideloaded EPUB (the engine itself) | partial | supported | partial | high |

Notes: For topic 5 (full-bleed), "supported"/"partial" all converge on the same conclusion — true edge-to-edge bleed is unachievable in *reflowable* on every reader; fixed-layout is the only spec-blessed route — hence the high confidence on a uniform "partial". For topics 1, 2 and 6, Google Play Books is `unknown` (not `partial`) deliberately: Google documents nothing and re-renders server-side, so it is genuinely untested, not merely caveated.

---

## 1. EPUB3 popup footnotes — `epub:type="noteref"` link + `<aside epub:type="footnote">`

**De-risks D2 (cross-reader popups; "nothing pops up on Kobo").** Final confidence: **medium.**

### Per-reader verdict

**Kobo (color e-ink) — partial.** The #1 cause of "nothing pops up" is that the book is a **plain sideloaded `.epub` that was never converted to KePub** — popups are a feature of Kobo's WebKit KePub renderer, not the Adobe-derived plain-EPUB path. Confirmed on the user's own hardware family: a 2023–2024 MobileRead thread (Libra Colour, Oct 2024) states flatly "You can't have pop-up footnotes with regular EPUB," and popups appeared only after KePub conversion. Once it *is* a KePub, four additional conditions (Kobo's own) must hold for any link to auto-pop:
1. link points **FORWARD** (target after the source);
2. target node ≥ **9 characters** stripped of tags;
3. target node ≤ **5000 characters**;
4. ids must be **ASCII**, first char an ASCII letter — non-ASCII ids (e.g. Ge'ez/Hebrew-derived) silently break the popup and just jump (confirmed Nov-2024 thread, an EPUB-spec rule not Kobo-only).

The old "put the id on `<aside>` and Kobo just jumps to the top of the file" tension is **legacy ADE-era (≈2018) and now OBSOLETE** — do not move the id to an inner `<p>` (that breaks Apple and is unnecessary on the modern KePub stack). Kobo does not consistently auto-hide `<aside epub:type=footnote>`, so a non-popped note may remain visible inline. *Gap:* no public report confirms popup behavior specifically on the 2024–2025 color e-ink units (fw 4.41–4.45) — inferred from the e-ink-class statement only.

**Apple Books — supported.** This is the reference implementation. Apple's Book Asset Guide ("Pop-up Footnotes") documents exactly `<a epub:type="noteref">` + `<aside epub:type="footnote">` with matching id. Apple **force-hides** the footnote aside from the main flow and overrides author CSS (`aside{display:block!important}` is ignored), so you cannot rely on the note also showing inline. Requires `xmlns:epub` on `<html>`. id goes **on the `<aside>`** and must match the link href. Documented escape hatch: replace `<aside>` with `<div>`/`<p>` and the note shows in a popup *and* inline.

**Google Play Books — unknown.** No authoritative Google statement and no clean reproducible test confirming whether the app or web reader pops up vs jumps. Google re-processes uploaded EPUBs server-side into an internal format, so behavior can change independent of markup and must be verified on an *actually-uploaded* title, separately in the Android app and the web reader. The safe fact: the bidirectional-link + visible-backlink markup degrades to tap-to-jump-and-return regardless.

### Recommended markup (the one cross-reader-safe pattern — ship as-is)

Reference and note in the **same XHTML file**, note placed **after** the reference:

```html
<!-- on <html> -->
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:epub="http://www.idpf.org/2007/ops">
...
<!-- reference -->
<a epub:type="noteref" role="doc-noteref" href="#fn1" id="fnref1"><sup>1</sup></a>
...
<!-- note: id on the <aside>, ASCII id, content ≥9 chars, AFTER the reference -->
<aside epub:type="footnote" role="doc-footnote" id="fn1">
  <p>Note text… <a epub:type="backlink" role="doc-backlink" href="#fnref1">↩</a></p>
</aside>
```

Hard rules that satisfy all three at once: (1) id **on the `<aside>`**; (2) **ASCII-only ids**, first char a letter (`^[A-Za-z][A-Za-z0-9._:-]*$`); (3) link **forward**, target text 9–5000 chars; (4) a **real visible back-link** inside the note; (5) do **not** architect around the note also appearing inline (auto-hide is reader-dependent). For Kobo, **convert to `.kepub.epub`** before sideloading. If you want the note also visible at chapter end on every reader, use a separate `<section epub:type="endnotes" role="doc-endnotes">` with `<li epub:type="endnote">`.

### Refuted / stale claims (from the skeptic)
- **OBSOLETE: "move the id to inner `<p>` for Kobo."** Legacy ADE-era; breaks Apple, unneeded on modern KePub. Favor id-on-`<aside>`.
- **Mis-sourced KePub requirement.** The KePub-required fact comes from kepubify's docs + practitioner reports, **not** the Kobo README (which states no `.kepub` extension is required for the *feature* — it is about which *renderer* runs).
- **Spec status updated.** EPUB 3.3 is now a full W3C Recommendation (2026-01-13) and still does **not** mandate popup rendering — divergence is permanent.
- **Color-unit gap.** "Works on color e-ink" is inferred from the e-ink-class statement; no primary report confirms or refutes it on fw 4.41–4.45.

### Notes for the implementer
Ship the pattern above. Enforce ASCII ids in the id generator — our corpus has Ge'ez/Amharic/Hebrew text; **no note id may ever be derived from non-Latin script**. epubcheck will not flag a "works but won't pop up" id, so add our own guard/test for `^[A-Za-z][A-Za-z0-9._:-]*$`. Watch the ≥9-char floor: a terse note like `cf. 2Ki 3` (~8 chars) may silently fail to pop on Kobo — pad/min-length or accept jump-fallback for ultra-short notes. Beware **kepubify overreach**: Kobo pops up *any* internal link meeting the 4 conditions, so on a cross-reference-dense Bible kepubify can turn *all* internal links into popups — inspect a converted sample on-device (see topic 7 for the cross-ref-popup hazard). Apple needs only a smoke check. For Google Play Books, test an actually-uploaded title in app + web reader if in scope.

---

## 2. `<details>`/`<summary>` disclosure elements (collapsible TOC)

**De-risks D3 (Kobo-safe TOC; "TOC messed up").** Final confidence: **medium.** No support verdict flipped on fact-check.

### Per-reader verdict

**Apple Books — supported.** WebKit has long, native, focusable, VoiceOver-announced `<details>`/`<summary>` support, and it needs **no JavaScript** (so it sidesteps EPUB's optional-scripting problem). Apple's Asset Guide: "Interactive content is supported for both flowing books and fixed-layout books." The one real risk, shared by all paginated readers: when `<details>` is expanded, revealed content can be pushed off the bottom of the current page and may not reflow onto the next (DAISY KB). High confidence the widget renders/toggles; medium on paginated-expand behavior. (The only element-specific a11y datapoint is a 2022 test; everything newer is engine-capability inference — re-confirm on a current Books build.)

**Kobo (color e-ink) — partial / element-status genuinely unknown.** Two-engine reality decides it: a plain `.epub` renders via the older ADE WebKit (least likely to toggle `<details>`); `.kepub.epub` triggers Kobo's newer WebKit (far more likely to render/toggle). Kobo's published epub-spec **does not list `<details>`/`<summary>` at all**, and no forum report confirms or denies it on Libra/Clara-class devices. On e-ink the off-page-on-expand hazard is worse (slow refresh, hard page boundaries, column pagination). Net: likely-works-as-KePub / likely-static-or-broken-as-plain-EPUB, both unconfirmed.

**Google Play Books — unknown.** Engine is Chromium/Blink (full native `<details>` support) and the element needs no scripting — but Play Books re-processes uploaded EPUBs server-side and may flatten/strip disclosure markup, and its publisher help says it doesn't support "interactive functionality such as that enabled by JavaScript." No primary source confirms a `<details>` toggle survives ingestion. Do not depend on the toggle; author visible-by-default.

### Recommended markup / CSS (cross-reader-safe — ship as written)

```html
<!-- PRIMARY navigation is always the EPUB3 nav doc -->
<nav epub:type="toc"><ol><li><a href="...">Genesis</a></li>...</ol></nav>

<!-- in-page collapsible TOC, native, no JS, OPEN by default -->
<details open>
  <summary>Genesis</summary>
  <ol><li><a href="...">Gen 1</a></li>...</ol>
</details>
```

```css
/* DAISY KB fallback so older engines that ignore `hidden` still collapse */
*[hidden] { display: none; }
/* do NOT style summary with display:contents or display:none */
```

The load-bearing rule: **every `<details>` is `open` by default** and the links inside are **never** hidden behind a `hidden` attribute / `display:none` that only the toggle removes. So if any reader (plain-EPUB Kobo, or Play Books after re-render) ignores or flattens the widget, the user still sees a fully-expanded clickable list — not a dead summary label. Keep each disclosure group **short (~one screen or less)** to avoid the off-page-on-expand failure.

### Refuted / stale claims
- **a11y data dating refined:** the only element-specific datapoint is a 2022-05-27 test (~4 yrs old); the Apple "supported" rating rests on engine capability + that aging test, not an Apple-Books-specific `<details>` test.
- **W3C FXL quote is FXL-framed:** the "details disrupts the page" line in epub-fxl-a11y is fixed-layout context (W3C Group Note, 2026-04-02). Carry the reflowable off-page hazard via the two DAISY KB pages (details.html, hidden.html), which *are* reflow-general.
- **Play Books transform is practitioner-sourced, not Google docs:** Google's help page mentions only the JS limitation, not server-side normalization. Attribute the flatten risk to The Digital Reader / MobileRead, not Google's help.

### Notes for the implementer
Because navigation's spine is the **nav doc** (every reader exposes it via its own TOC UI — this is what actually fixes "TOC messed up") and the in-page TOC is **open-by-default**, navigation never breaks on any reader even in the worst case; the only thing at stake on-device is whether the collapse animation works — so D3 is genuinely de-risked. For Kobo, ship a `.kepub.epub` variant and prefer **kepubify over Calibre** for the conversion (modifies source less, parses HTML properly, least likely to mangle `<details>`). Surface the trade-off: a `.kepub.epub` sideload **disables bookmarking/notes** vs a plain `.epub` — consider shipping both. epubcheck passes `<details>`/`<summary>` clean.

---

## 3. CSS flexbox (`display:flex`) in reflowable EPUB content

**De-risks D3 (TOC/title-page layout).** Final confidence: **medium.** No verdict flipped.

### Per-reader verdict

**Apple Books — supported.** WebKit, mature unprefixed flexbox; viewport units (`vh`/`vw`) with flexbox for centered/bottom-anchored title pages are well supported and Apple's guide even recommends viewport units for images in flowing books. A 2026 practitioner source independently lists Apple Books flexbox as "strong." Caveats are graceful: large user font sizes overflow a `vh` container onto the next page (degradation, not break); page-spanning flex grids fight column pagination — keep containers small and self-contained.

**Kobo (color e-ink) — partial.** Two-engine reality: on the newer `.kepub` WebKit, basic `display:flex` with `align-items`/`justify-content` for a title page generally renders; on the legacy `.epub` (ADE) path it is unreliable. Recent (2026) practitioner evidence says modern Kobo flexbox support is "strong," strongest on the `.kepub.epub` path — so the enhancement *will* likely render on a current color Kobo. The "unopenable file" fear is **less scary than originally framed** (see refuted claims). No vendor statement on flexbox exists; support is inferred; firmware behavior is version-opaque.

**Google Play Books — partial.** Chromium/Blink (flexbox supported at engine level); basic `display:flex` generally renders. "Partial" because there is **no Google doc** affirming flexbox in reflowable EPUB, and Play Books **re-flows uploads** (applies CSS → computes page breaks → chops HTML per-page → re-applies CSS), so rendering can diverge app vs web reader vs post-conversion. Keep flex simple (single container, shallow nesting); verify in both the Android app and the web reader.

### Recommended markup / CSS (progressive enhancement — ship as-is)

```css
/* DEFAULT — readable everywhere, no flexbox (this is what a non-flex engine sees) */
.titlepage { text-align: center; }
.titlepage .title  { margin-top: 30vh; }   /* nudges toward center; harmless margin otherwise */
.titlepage .bottom { margin-top: 3em; }

/* ENHANCEMENT — only engines that report flex opt in */
@supports (display: -webkit-flex) or (display: flex) {
  .titlepage {
    min-height: 95vh;            /* min-height, NEVER fixed height — respects user font-size */
    display: -webkit-flex;       /* -webkit- first for the older Kobo/ADE WebKit */
    display: flex;
    -webkit-flex-direction: column; flex-direction: column;
    -webkit-justify-content: center; justify-content: center;
  }
  .titlepage .title  { margin-top: 0; }
  .titlepage .bottom { margin-top: auto; }  /* pin to bottom only in flex mode */
}
```

Rules: keep flex containers small/self-contained (title page, a TOC row, a caption cluster) — no page-spanning grids; `min-height` + `vh`, never fixed height; include the `-webkit-` prefix alongside the standard property; the layout must be fully usable with the `@supports` block removed (that is exactly what a non-flex engine sees).

### Refuted / stale claims
- **Date error:** EPUB 3.3 became a W3C Recommendation **25 May 2023** (minor updated Rec 27 Mar 2025), **not "Jan 2025"** — fix in any shipped doc/comment.
- **"Unopenable file" risk overstated:** pandoc issue #8379 was **pandoc-specific** (its own column-div flexbox CSS) on **one** PocketBook device, and was **FIXED in pandoc 3.1.9** (flexbox no longer used by default). Never a documented Kobo failure. Keep the readable block fallback (costs nothing) but do **not** describe an unopenable Kobo as expected.
- **False corroboration dropped:** the "EPUB 3 Books Crashing PocketBook" thread was a **DRM** issue, not flexbox — do not cite it.
- **Engine-name ambiguity:** the authoritative Kobo spec says plain `.epub` = "Adobe Digital Editions WebKit" and `.kepub.epub` = "Kobo WebKit"; ignore the secondary RMSDK/NetFront wording for this question.

### Notes for the implementer
Ship the pattern as-is. Relax the internal assumption that Kobo mangles `vh` (Kobo staff said in 2018 that `vh` support is now broad — see topic 5). epubcheck passes `display:flex`; the CSS-008 errors people hit were the `:has()` token, fixed in epubcheck 5.3.0 — use a current epubcheck. On-device test both `.epub` and `.kepub.epub` paths on the color Kobo (and confirm the `.epub` path *opens*), with a large user font size set.

---

## 4. Embedded `@font-face` fonts (WOFF/WOFF2/OTF/TTF), subsetting, obfuscation — for Hebrew, Greek (Cardo), Ethiopic (Abyssinica SIL)

**De-risks D5 (legible original-language fonts on Kobo).** Final confidence: **medium.**

### Per-reader verdict

**Kobo (color e-ink) — partial.** Embedded `@font-face` fonts work on current color Kobo for both sideloaded plain EPUB and KePub, with three load-bearing caveats:
1. **Format:** Kobo's spec lists "TTF, OTF, and WOFF (v.1.0)". **WOFF2 is NOT listed — treat as unsupported on e-ink Nickel. Embed OTF or TTF.**
2. **User font selector overrides the embedded font:** only the **"Publisher Default" / "Original" / "Document Default"** selection preserves the embedded font; any built-in font the user picks wins. This is the central D5 risk — built-in Kobo fonts **lack Ethiopic** and may lack full Hebrew/polytonic-Greek coverage, so a non-rendered embedded font = tofu/.notdef boxes.
3. **KePub is NOT the safe default for embedded fonts** (corrected, see below): the KePub reader stylesheet applies `* { font-family: %1 !important; }` to **all** elements, overriding embedded `@font-face` everywhere unless "Publisher Default" is chosen; the plain-EPUB/RMSDK reader only overrides `body, p` and has better typography (ligatures/kerning/hyphenation). Build and on-device-test **both**.

Do **not** obfuscate (display-error risk, no licensing need for open OFL fonts). If subsetting, subset against the **actual corpus codepoints** incl. every Ge'ez syllable, Hebrew letter + niqqud + cantillation mark, Greek base + polytonic combining mark — keep an unsubsetted build to diff.

**Apple Books — supported.** Renders embedded OpenType/TrueType. **Hard requirement for reflowable books:** the OPF must declare `ibooks:specified-fonts = true`, or Apple Books drops the embedded fonts and substitutes a system font (the #1 cause of "my Greek/Hebrew font isn't showing on iOS"). Use only **Unicode-encoded** fonts (Cardo / SBL Hebrew / Abyssinica SIL) — never Latin-codepoint-remapping legacy fonts. *Correction:* Apple's own asset guide lists only OpenType/TrueType/SVG — **WOFF2 is overstated; prefer OTF** (also keeps one asset set with Kobo).

**Google Play Books — partial.** Partner Center lists "Embedded fonts ✔" but documents no font-format/obfuscation/subsetting matrix. Server-side processing + per-surface (Android vs iOS vs web) inconsistency makes fidelity non-guaranteed; the web reader is weakest. Blink/HarfBuzz should shape complex scripts well where the embedded font is actually used. Embed OTF, robust fallback chain, don't rely on obfuscation, test the Android app **and** the web reader.

### Recommended markup / CSS (one shared asset set)

```css
/* one @font-face per weight/style — Kobo/RMSDK does NOT synthesize bold/italic */
@font-face { font-family:'Cardo';         font-weight:normal; font-style:normal; src:url('../fonts/Cardo-Regular.otf'); }
@font-face { font-family:'AbyssinicaSIL'; font-weight:normal; font-style:normal; src:url('../fonts/AbyssinicaSIL-Regular.otf'); }

/* language-tagged spans with a fallback chain so a dropped/overridden font degrades to a system font, not .notdef */
.geez   { font-family:'AbyssinicaSIL', serif; }   /* xml:lang="gez" */
.hebrew { font-family:'SBL Hebrew', serif; }       /* xml:lang="he"  */
.greek  { font-family:'Cardo', serif; }            /* xml:lang="grc" */
```

```xml
<!-- OPF: the Apple gate (harmless on Kobo/Google) -->
<package ... prefix="ibooks: http://vocabulary.itunes.apple.com/rdf/ibooks/vocabulary-extensions-1.0/">
  <meta property="ibooks:specified-fonts">true</meta>
  <item href="fonts/Cardo-Regular.otf" id="f-cardo" media-type="font/otf"/>
```
Also ship `META-INF/com.apple.ibooks.display-options.xml` with `specified-fonts=true` for EPUB2/belt-and-suspenders. Body text: no `font-size` or `1em`. Add a prominent front-matter note instructing Kobo readers to pick **"Publisher Default" / "Original"** in the Aa menu (more load-bearing under KePub).

### Refuted / stale claims
- **REFUTED for this use case: "KePub is preferable for embedded original-language fonts."** Backwards. KePub's `* { font-family: %1 !important; }` overrides embedded fonts on all elements; plain EPUB (RMSDK) preserves them more readily and has better typography. KePub's wins are page-turn speed/search/zoom, not font fidelity.
- **Engine identity:** plain `.epub` = RMSDK (white-label Adobe Digital Editions), **not** "bare-bones WebKit"; the WebKit (NetFront/ACCESS) renderer is the KePub path.
- **Apple WOFF2 overstated:** Apple's guide lists only OpenType/TrueType/SVG. Don't rely on Apple-documented WOFF2 — embed OTF/TTF.
- **Latin-remap warning mis-sourced:** the "legacy print fonts that remap Latin codepoints are inappropriate" rule is correct but traces to eBook-standards lineage (FlightDeck), not verbatim Apple text — keep the rule, soften the Apple attribution.
- **Spec ideal ≠ Kobo reality:** EPUB RS 3.3 §6.3 *mandates* WOFF2 support for conformant visual reading systems, but Kobo e-ink does not conform — "the spec requires WOFF2" does not mean "Kobo renders WOFF2."

### Notes for the implementer
Embed **OTF** (triple-confirmed: Kobo lists only TTF/OTF/WOFF v1.0; Apple lists only OpenType/TrueType/SVG; expert Jiminy Panoz says "stick with OTF"). Emit the `ibooks:specified-fonts` gate always. One `@font-face` per weight/style; lang-tagged spans with a generic-family fallback. No obfuscation (if ever forced: IDPF method = **SHA-1**, not MD5, of the whitespace-stripped UTF-8 unique identifier as key, XOR the first 1040 bytes, `encryption.xml` algorithm `http://www.idpf.org/2008/embedding`, key not stored). Verify niqqud/cantillation/polytonic **mark positioning on-device** — Calibre/Sigil can look right while the device drops or mis-positions marks. The exact Libra/Clara Colour default-on behavior and mark positioning are **unverified in any source** — device-test-gated.

---

## 5. `position:absolute` and full-bleed cover / title-page images; SVG vs fixed-layout

**De-risks D3 (#5/#6 title-page art renders + aligns).** Final confidence: **high** (verdicts confirmed against primary sources; none refuted).

### Per-reader verdict (all three: partial)

**Kobo (color e-ink) — partial.** True edge-to-edge bleed in *reflowable* is not reliably achievable on a plain sideload, but a **full-PAGE** image (fills the content viewport, RS margins present) is. The **cover** is special-cased: it must live in its own XHTML file, Kobo runs its **Fixed-Layout renderer** for it, and you must use an `<img>` tag (**never** CSS `background-image`, or Kobo's auto cover extraction fails). For interior art, use **percentages** (`width:80%; height:auto`), avoid negative positioning, avoid styling bare `div`/`span`. Crucially, genuinely full-screen image pages on current color firmware are a **file-format outcome** (`.kepub.epub`) more than a CSS outcome — MobileRead Oct-2024 (Libra Colour) found full-screen image pages came from the kepub path while plain `.epub` left headers/footers.

**Apple Books — partial.** Most viewport-unit-friendly for full-PAGE images; Apple's guide sanctions `img { height: 50vh; }` for flowing books and requires real `<img>` (not `svg:image`). Hard limits: interior images ≤ **5.6 million pixels**; ~10 MB un-encoded image data per XHTML; sRGB; JPEG/PNG. Known quirk: Apple's injected CSS can ignore `max-height` — pair `vh` with `object-fit:contain`. For genuine bleed, Apple's guidance is pre-paginated fixed-layout.

**Google Play Books — partial.** Most restrictive: hard **3200px cap** on width/height attributes of `<image>`/`<svg>` tags and referenced files; CSS normalization means `max-height` and `page-break-before:always` are unreliable; `vh` unreliable. Supports SVG and fixed-layout (EPUB 2 and 3). For precise/full-bleed, deliver that page as fixed-layout.

### Recommended markup / CSS (cross-reader-safe — ship as-is)

```html
<body class="fullpage">
  <section class="titleart" epub:type="title-page">
    <img src="../images/titleart.jpg" alt="..." />   <!-- real <img>, never <svg><image> nor background-image -->
  </section>
</body>
```

```css
html, body { margin: 0; padding: 0; height: 100%; }
section.titleart { height: 100%; text-align: center; page-break-before: always; }
img { display: block; margin: 0 auto; max-width: 100%; height: auto; }
img:only-of-type { height: 100%; width: auto; object-fit: contain; }   /* percentage base every engine honors */
@supports (height: 100vh) {                                            /* guarded enhancement */
  img:only-of-type { height: 100vh; max-height: 100vh; }
}
```

Keep source images **≤ 3200px longest side** (Play Books cap) and **≤ 5.6 Mpx** (Apple), sRGB, PNG/JPEG. Cover in its own XHTML with a plain `<img>`. **Do not attempt true edge-to-edge bleed in reflowable** — no reading system guarantees it; for genuine bleed make that page (or the cover) **fixed-layout** (`rendition:layout pre-paginated` + viewport meta + an absolutely-positioned image filling the declared viewport). For Kobo full-screen interior art, also ship `.kepub.epub`.

### Refuted / stale claims
- **STALE: "Kobo's `vh` discouragement stands."** It does not. The discouragement lived only in archived issue #36, not the current README, and Kobo staff (bdugas, 2018-01-24) softened it: "VH seems to have much more verbose browser support… In recent years we haven't come across other display issues caused by use of VH." Keep the guarded `@supports`/`vh` layer but **do not engineer around a phantom Kobo `vh` failure**; percentages remain the floor.
- **Spec date:** EPUB 3.3 reached final W3C Recommendation **13 January 2026**.
- **Attribution:** "pagination of absolutely-positioned reflowable content is not guaranteed" comes from w3c/epub-specs issue #327 (`position:absolute` IS in the profile via CSS 2.1; only `position:fixed` is excluded), not a verbatim spec sentence.
- **No reflowable-bleed mechanism ever shipped** (W3C publ-cg issue #3, Dave Cramer 2017; repo archived 2022) — fixed-layout is the only route.

### Notes for the implementer
Ship the pattern. The one substantive change vs prior assumptions: stop treating Kobo as `vh`-hostile. On-device, test plain `.epub` vs `.kepub.epub` side-by-side (same book), confirm the cover renders edge-to-edge vs full-page-with-margins, and verify `vh` fills the color e-ink panel. Verify macOS Books vs iOS Books separately, and the Play Books Android app vs web reader separately.

---

## 6. Large single-file XHTML performance on e-ink; chapter/file splitting

**De-risks D4 (Kobo slow/crash; file-splitting plan).** Final confidence: **medium.** All three verdicts held on fact-check.

### Per-reader verdict

**Kobo (color e-ink) — partial.** **Root mechanism:** Nickel lays out an *entire* spine XHTML at once and paginates via CSS multi-column; on a plain sideload, page boundaries are not pre-computed, so it must reflow the whole document before showing a page, and it gets slower the deeper you read. Concrete forum evidence (2012–2015 firmware): a monolithic 325–355-page / 43-chapter XHTML produced multi-minute "Processing content" stalls, fixed by one-file-per-chapter; page-turn timings KePub ≈1.26s vs plain sideloaded EPUB ≈1.93–3.52s vs split EPUB ≈1.71–2.21s. **Limits:** Kobo caps embedded content at **10 MB per HTML file** and **1 GB per EPUB** — our 2–3.4 MB spine files are under the hard cap (so they load) but are exactly the monolith pattern that causes the stalls. **Separate crash class:** a **colon in an `<a>` name/href** value (e.g. `name="Carnap:23a"`) makes Nickel HANG on "Processing content" / can soft-brick the add — structural, not size, directly relevant to this repo's nested-anchor/coordinate-id hygiene.

**Apple Books — supported.** Opens large reflowable EPUBs without the e-ink crash/stall (far more CPU/RAM), but Apple **explicitly tells publishers to split:** "In flowing books, divide each chapter into its own XHTML document" and "Separating chapters into documents improves performance in Apple Books." Use real `h1`/`h2` headings (Apple relies on HTML semantics for layout). Envelope: EPUB ≤ 2 GB (recommended ≤ 500 MB); our text-heavy ~99 MB-uncompressed corpus is comfortably within limits.

**Google Play Books — unknown.** No documented per-XHTML size limit, no split recommendation, no large-file performance characteristics for app or web reader. Publisher limit is < 2 GB; EpubCheck-valid, cover present, complete book required. A separate **personal-upload 100 MB per-file cap** (distinct from the 2 GB publisher limit) applies to whole-EPUB personal uploads — trivially satisfied since the corpus zips far below 100 MB. Server-side re-render means behavior could diverge — flag for testing.

### Recommended structure (cross-reader-safe — ship as-is)

Split the corpus into multiple moderate spine files — **one natural unit per file** (for this Bible, prefer **one book per XHTML**, or **one chapter per XHTML** for very large books), each **~100–300 KB uncompressed**, never above ~1 MB, well under the 10 MB cap. Real semantic `h1`/`h2`/`h3` headings, external CSS, **colon-free** `id`/`name`/`href` fragments. **Do not over-fragment below ~100 KB** (Calibre ignores splits < 100 KB and Nickel's reassembly overhead makes tiny chunks slower). Then layer a **KePub variant** (kepubify or Calibre 8+ native KEPUB) on top for Kobo: pre-computed pagination (`div#book-columns > div#book-inner` + `koboSpan` fragments) and store-class page-turn speed. Keep it epubcheck **0/0/0/0**.

### Refuted / stale claims
- **Two different metrics conflated:** the "25KB split helps page-turn" (latency) and "over-splitting below ~100KB made it WORSE — 3.5 min" (initial load/seek) are **different measurements** and can move in opposite directions. The "100–300 KB sweet spot" is an inference from one 2012-era thread, **not a measured optimum**.
- **Second "Processing content" root cause:** import-time **SQLite/TOC indexing** (~100 DB entries per book), distinct from in-book reflow — splitting into more files can *increase* the per-book TOC/DB entry count. "Processing content" is two phenomena.
- **Tooling updated:** as of **Calibre 8.0 (Mar 2025)** KEPUB conversion is **built into Calibre core** — the KoboTouchExtended plugin is no longer required (still works); or use kepubify.
- **Hard numbers are old-firmware:** all the multi-minute / page-turn figures are Kobo Touch/Glo/Aura 2012–2015. The 2024 Libra/Clara Colour is much faster; 2024 (jonsdocs) + 2025 (sangsara) reports confirm the *qualitative* slow-sideload problem persists with KePub as the fix, but **no primary measurement of our 2–3.4 MB Ge'ez/Amharic spine files on color-Kobo hardware exists** — treat the absolute figures as worst-case.

### Notes for the implementer
Make the split the **default base structure** (one cross-reader structure satisfies Apple's own guidance + Kobo monolith-avoidance + Google-neutral), wired through the one resolver (per MATRIX_MAP doctrine), **not** a per-edition flag. The KePub is a **Kobo-only additional output artifact** (like the σ.5 standalone-cover work) — wire it as an optional build target, not a transform of the canonical EPUB. **Do not keep the 2–3.4 MB monolith for any reader.** Keep all id/name/href fragments **colon-free** (verify the coordinate-id scheme emits no colons before shipping). epubcheck 0/0/0/0 is a Kobo *stability* lever (the 2025 Clara Colour freeze report attributes lockups to EPUB *errors* — bad markup / missing font specs), not just a validity nicety.

---

## 7. Kobo KePub vs vanilla sideloaded EPUB — the engine itself

**De-risks D2/D3/D4 (the Kobo rendering engine).** Final confidence: **high.**

### Per-reader verdict

**Kobo (color e-ink) — partial.** A Kobo routes by **file extension**: plain `.epub` → Adobe RMSDK / Digital-Editions WebKit; `.kepub.epub` (double extension) → Kobo's own NetFront/ACCESS WebKit. The kepub transform is not a different container — it rewrites XHTML to add `div#book-columns > div#book-inner` (a pagination target) and `<span class="koboSpan" id="kobo.N.M">` around each fragment. Per the kepubify package: "Highlighting, bookmarking, and other related features don't work without this" (i.e., the *kepub render path's own* highlight mechanism). **Kepub-only / kepub-better:** faster page-turn/tap, faster large-highlight selection, **footnote previews (popup)**, double-tap image zoom, smoother grayscale dither, "minutes left" stat, precise position memory. **Better on plain `.epub`** (kepub-reader bugs): hyphenation, full justification, **embedded-font support**, full-screen without font clipping. **No interactive JavaScript** on e-ink — never make content depend on JS.

Three corrections that matter for *this* book:
1. **Bookmark/annotation tradeoff is REVERSED for sideloaded books.** Kobo's official README: naming a sideloaded file `.kepub.epub` **DISABLES bookmarking and note-keeping**, while a plain `.epub` (RMSDK path) is the one that enables sideload bookmarking/search/highlighting.
2. **Popup footnotes are a KEPUB-only behavior on the current Colour line** — correct `aside`/`noteref` markup alone does **not** pop up on a sideloaded plain `.epub`.
3. **HIGH-IMPACT for a Bible:** kepub conversion auto-converts ordinary **internal cross-reference links into popups** when the target has an `#id`, ≥9 visible chars, ≤5000 chars, and points forward. A verse-cross-reference-dense Bible will sprout spurious popups in kepub form — one user abandoned kepub over exactly this.

Also: keep content XHTML + the `.opf` in a **subfolder** (`OEBPS/`, `text/`), **never the EPUB root** — Kobo mishandles root-level content (the documented fix for a footnote regression).

**Apple Books — supported.** Most standards-complete. Popup footnotes native and reliable (`<a epub:type="noteref">` + `<aside epub:type="footnote">`; only `<aside>` auto-hides; requires `xmlns:epub` on `<html>`; RTL via inner `<p style="direction:rtl">`). Prefer `page-break-after: always` for chapter ends. Dark-mode custom text color via `class="ibooks-dark-theme-use-custom-text-color"` or `:root{color-scheme:light dark}` + `prefers-color-scheme` (both current, not deprecated) — relevant if red-letter/colored Scripture text matters.

**Google Play Books — partial.** Accepts EPUB 2/3/3.3 (3.3 preferred), fixed-layout, standard noteref/aside popups in the apps. **Least faithful renderer:** re-paginates by chopping XHTML into per-page documents and re-applying CSS, so loss shows as structural/pagination artifacts. Google itself tells publishers to self-add as Content Reviewer and eyeball the **web reader**, and to supply a PDF for layout-critical books. Keep CSS conservative + well-namespaced; provide navigable fallbacks.

### Recommended footnote markup / CSS (cross-reader-safe)

```html
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
...
<a epub:type="noteref" role="doc-noteref" href="#fn1"><sup>1</sup></a>
...
<aside id="fn1" class="footnote" epub:type="footnote" role="doc-footnote">
  <p>note text… <a epub:type="backlink" role="doc-backlink" href="#fnref1">↩</a></p>
</aside>
```

```css
/* defensive hide via your OWN class, so a non-popup engine doesn't dump the note mid-paragraph */
aside.footnote { display: none; }
```

Use the **class selector**, not an `epub|` attribute selector (see refuted claims). Keep `epub:type` semantics + `xmlns:epub` on `<html>` so popup-capable readers (Apple, GPB apps, Kobo kepub where firmware cooperates) still pop. Styling rules that hold everywhere: linked (not inline) stylesheets; specific class selectors, never bare `div`/`span`; `font-variant:small-caps` (never `font-size`) for small caps; cover via `<img>`; images `width:80%;height:auto`; embed all non-system fonts.

### Refuted / stale claims
- **Bookmark tradeoff was stated backwards** (see verdict point 1) — sideloaded `.kepub.epub` *loses* bookmarks/notes; plain `.epub` keeps them.
- **Cross-ref-popup hazard was omitted** — high-impact for a Bible (verdict point 3).
- **Invalid CSS in the prior pattern:** `aside[epub|type~="footnote"]{display:none} @namespace epub "...";` — the `@namespace` at-rule **must precede all style rules**, so the prefix is undeclared and the rule is dropped. Use `aside.footnote{display:none}` instead.
- **Stale date:** the MobileRead 278792 popup-footnote regression is **2016** (Kobo Aura One, fw 4.0.7523), not 2018 — and it surfaced the still-relevant root-directory fix.
- **Firmware baseline:** current Colour line is fw **4.45.23640 (Feb 2026)** — a generic bug-fix release with no documented rendering/footnote changes.

### Notes for the implementer
**Ship twice, with corrected roles.** Plain `.epub` = the **bookmarking/notes-friendly AND cross-reference-safe** artifact. KePub = the **fast-render + popup-footnote + reading-stats** artifact, but it can disable sideload bookmarks/notes **and** mangle cross-refs into popups — do not present it as strictly better. **Highest-priority on-device test:** build one chapter with both footnotes and several verse-to-verse cross-reference links, convert to kepub, and check whether the cross-ref links wrongly pop up. If they do, options: ship cross-refs only in the plain `.epub`; make targets fail one popup criterion; or ship kepub without inline cross-ref links. Keep all content XHTML + `.opf` in a subfolder. Never depend on JS.

---

## Canonical cross-reader-safe recommendations (mapped to D2 / D3 / D4 / D5)

These are the opinionated, implementable defaults for the Windows lane. Where a Kobo-only artifact is needed, it is an **additional build output**, not a transform of the canonical EPUB.

### D2 — popup footnote mechanism
- **Emit:** semantic noteref/aside in the **same XHTML file**, note **after** the reference, **id on the `<aside>`**, plus `role` attributes for accessibility, plus a **visible back-link** inside every note. Add `xmlns:epub` on every content `<html>`.
- **id generator (hard guard):** ids must match `^[A-Za-z][A-Za-z0-9._:-]*$`, **ASCII only** — never derive an id from Ge'ez/Amharic/Hebrew script. Add a build test for this (epubcheck won't catch a "won't pop up" id). **No colons in any fragment id/name/href** (Kobo hang/soft-brick).
- **≥9-char note floor:** ultra-short notes (`cf. 2Ki 3`) may not pop on Kobo — pad or accept jump-fallback.
- **Defensive hide via a class selector** (`aside.footnote{display:none}`), never the `epub|` attribute selector (invalid without a leading `@namespace`). Keep the note reachable via the link target.
- **Do not** architect around the note showing inline — auto-hide is reader-dependent.
- **Kobo:** popups require the **KePub** artifact; also beware kepubify converting cross-reference links into spurious popups (test, then constrain).

### D3 — Kobo-safe TOC + title-page / layout
- **Navigation spine = the EPUB3 `nav[epub:type=toc]` doc.** This is what fixes "TOC messed up" — every reader exposes it via its own TOC UI.
- **In-page collapsible TOC:** native `<details>`/`<summary>`, **no JS**, **`<details open>` by default**, links never hidden behind a toggle-only state. Keep each group ~one screen. Add `*[hidden]{display:none;}`.
- **Layout (flexbox):** progressive enhancement — readable **block default outside `@supports`**, then `@supports (display:-webkit-flex) or (display:flex)` layering `-webkit-`-prefixed + standard props, `min-height` + `vh` (never fixed height), small self-contained containers (no page-spanning grids). Do **not** engineer around a phantom Kobo `vh` failure.
- **Title-page / cover art:** real `<img>` (never `background-image`, never `<svg><image>`); cover in its **own XHTML**; percentage base + guarded `@supports(height:100vh)` + `object-fit:contain`. Source images **≤ 3200px longest side, ≤ 5.6 Mpx, sRGB, PNG/JPEG**. **No true reflowable edge-to-edge bleed** — use fixed-layout for any genuinely bleed/pixel-precise page.

### D4 — performance / file-size
- **Split the corpus** into multiple moderate spine files — **one book per XHTML** (one chapter for very large books), **~100–300 KB** each, never > ~1 MB, well under the 10 MB cap. **Do not over-fragment below ~100 KB.** Real `h1`/`h2`/`h3`, external CSS, **colon-free** fragments.
- Make the split the **default base structure** (one resolver), **not** a per-edition flag. **Never keep the 2–3.4 MB monolith** for any reader.
- **Kobo KePub** as an optional additional output (kepubify or Calibre 8+ native) for pre-computed pagination + store-class speed.
- Keep epubcheck **0/0/0/0** — it's a Kobo *stability* lever, not just validity.

### D5 — embedded original-language fonts
- **Embed OTF** (or TTF) — **never WOFF2-only** (Kobo e-ink and Apple's documented formats both exclude it). Manifest `media-type="font/otf"`.
- **Apple gate (always emit):** `ibooks:specified-fonts=true` on `<package>` + `META-INF/com.apple.ibooks.display-options.xml` with `specified-fonts=true`. Without it Apple drops embedded fonts.
- **One `@font-face` per weight/style** (Kobo/RMSDK doesn't synthesize bold/italic). Lang-tagged spans (`he`/`grc`/`gez`) with a **generic-family fallback chain** so a dropped/overridden font degrades to a system font, not `.notdef`.
- **Unicode-only fonts** — Cardo (Greek/polytonic), SBL Hebrew (Hebrew + niqqud/cantillation), Abyssinica SIL (Ge'ez). Never Latin-codepoint-remapping legacy fonts.
- **Do not obfuscate** (open OFL fonts; obfuscation adds Kobo display-error risk).
- **Subset only against the actual corpus codepoints** (every Ge'ez syllable, Hebrew letter + niqqud + cantillation, Greek base + polytonic mark); keep an unsubsetted build to diff.
- **Front-matter note for Kobo readers:** select "Publisher Default" / "Original" in the Aa menu (more load-bearing under KePub, whose `* {font-family !important}` overrides embedded fonts).

### Kobo packaging doctrine (cross-cutting)
- **Ship twice for Kobo:** plain `.epub` = bookmarking/notes-friendly + cross-reference-safe; `.kepub.epub` = popup footnotes + fast render + reading-stats, **but** can lose sideload bookmarks/notes and mangle cross-refs into popups. Neither is strictly better — surface the tradeoff to the user.
- Keep content XHTML + `.opf` in a **subfolder** (`OEBPS/`/`text/`), never the EPUB root.
- **Prefer kepubify** over Calibre for conversion where minimal source mangling matters (e.g. `<details>`); Calibre 8+ native KEPUB is also fine for the perf artifact.
- **No interactive JavaScript** anywhere — Kobo e-ink has none and the spec only *SHOULDs* scripting.

---

## Open questions / must-test on the physical Kobo

These are the low-confidence, device-specific, or genuinely-unknown items. The user's hands-on check on the actual color Kobo (Libra Colour / Clara Colour, current firmware) is the only ground truth. **Capture the firmware string each time** (expect 4.41.x–4.45.x).

1. **(D2) Popup footnotes on the color e-ink units.** No public report confirms or denies popup behavior on the 2024–2025 color units (fw 4.41–4.45). Build/sideload a real `.kepub.epub` and verify a footnote pops up; verify a plain `.epub` does **not** (expected). Calibre's viewer is **not** a proxy for Nickel.
2. **(D2/D7) Cross-reference-popup hazard — HIGHEST PRIORITY.** Build one chapter with footnotes **and** several verse-to-verse cross-reference links, convert to kepub, and check whether the cross-ref links wrongly pop up (trigger: `#id` target, ≥9 visible chars, ≤5000 chars, points forward). Decide the mitigation (cross-refs plain-`.epub`-only / break a criterion / drop inline cross-refs in kepub) before locking the kepub build.
3. **(D5/D7) Bookmark/notes loss under `.kepub.epub`.** Confirm on *this* unit whether a sideloaded `.kepub.epub` really disables bookmarking/note-keeping vs a plain `.epub`.
4. **(D5) Embedded Ge'ez/Ethiopic + Hebrew/Greek rendering through both engines.** Test the embedded font in **both** the plain `.epub` (RMSDK) and `.kepub.epub` (NetFront) artifacts. Verify: (a) does a fresh sideload show the embedded font by default or need "Publisher Default"? (b) do **Hebrew niqqud + cantillation** and **Greek polytonic** combining marks position correctly on-device (Ge'ez has no complex shaping; Hebrew/Greek mark positioning is the risk)? (c) confirm OTF (not WOFF2) is what renders.
5. **(D3) `<details>`/`<summary>` toggle.** Untested in all public sources for any Kobo (the spec doesn't list the element). Does it render and tap-toggle as a `.kepub.epub`? Does it fall back to static-open as a plain `.epub`? Test expand-near-page-bottom (reflow vs clip).
6. **(D3) Flexbox + `vh` on the color panel.** Confirm the title page renders centered/bottom-anchored on **both** `.epub` and `.kepub.epub`, that the `.epub` path **opens** at all, and that `min-height`+`vh` grows (not clips) with a **large user font size** set.
7. **(D3/#5) Cover edge-to-edge vs full-page-with-margins**, and whether full-screen interior art needs the `.kepub` path (Oct-2024 evidence says it does).
8. **(D4) Split granularity + load/turn timing.** Measure **first-open layout time** AND **deep-in-file page-turn latency** for (a) the current 2–3.4 MB monolith, (b) per-book/per-chapter split, (c) a KePub build — on the actual **Ethiopic** content, not Latin samples. The "100–300 KB" target is a 2012-era inference, not a measured optimum; measure both metrics (they can move in opposite directions) before locking granularity.
9. **(cross-cutting) Coordinate-id colon check.** Verify the build emits **no colons** in any `id`/`name`/`href` fragment (a colon makes Nickel hang on "Processing content" / soft-brick the add).

Also (if Google Play Books is a real distribution target): upload a test title, self-add as Content Reviewer, and verify popup footnotes, `<details>`, flexbox, embedded fonts, and the split build in **both** the Android app and the **web reader** (the weakest surface) — Google re-renders server-side, so sideload-upload behavior may differ and Kobo findings do not transfer.

---

## References

1. **Kobo EPUB spec — README (footnotes/endnotes, popup conditions, platform support, engine split, fonts, obfuscation, FXL, CSS best practices)** — https://github.com/kobolabs/epub-spec/blob/master/README.md — PRIMARY (Kobo/Rakuten). e-ink (except original/Wi-Fi) + iOS pop up; Desktop/Android/Windows just follow links. The 4 popup conditions (forward; target ≥9 chars stripped; ≤5000 chars; references a node). Plain `.epub` = Adobe Digital Editions WebKit (enables sideload bookmarking/search/highlighting); `.kepub.epub` = Kobo WebKit (DISABLES sideload bookmarking/notes). "TTF, OTF, and WOFF (v.1.0) fonts are supported by all Kobo platforms" (no WOFF2). 2017 obfuscation support. eInk: MathML Y, CSS-anim Y, interactive JS N, SMIL N, A/V N, FXL Y. Cover in own XHTML, `<img>` not background-image, percentages over px. Recommends the toc nav element. Undated living doc.
2. **Kobo epub-spec repo (top-level)** — https://github.com/kobolabs/epub-spec — Hard limits: 10 MB per HTML file, 1 GB per EPUB, ~3.8 Mpx FXL viewport; over-limit files "should still load… take longer… more memory." Does NOT list flexbox or `<details>`/`<summary>`.
3. **Kobo epub-spec Issue #59 — aside/noteref/footnote support** — https://github.com/kobolabs/epub-spec/issues/59 — PRIMARY user report: Kobo Forma sideloaded KePub (fw 4.33.19759, 7/2022) — aside not hidden, no popup; works on iOS; partial in Calibre. No staff resolution.
4. **Kobo epub-spec Issue #36 — viewport height (vh) units** — https://github.com/kobolabs/epub-spec/issues/36 — Kobo's original vh discouragement; **Kobo staff (bdugas, 2018-01-24) SOFTENED it**: vh now has broad support, no recent vh display issues. The caution lives only here, not the current README.
5. **Kobo epub-spec Issue #16 — clarify pop-up note behavior / version support** — https://github.com/kobolabs/epub-spec/issues/16 — PRIMARY question (2015) on firmware/app support and same-file-only behavior. Question only.
6. **Kobo epub-spec Issue #3 — Font support (OTF/WOFF core media types vs TTF)** — https://github.com/kobolabs/epub-spec/issues/3 — 2014: Kobo supports OTF/WOFF/TTF; EPUB3 core types are OTF/WOFF (TTF needs a fallback). No WOFF2/subsetting detail.
7. **Kobo epub-spec Issue #17 — obfuscated fonts** — https://github.com/kobolabs/epub-spec/issues/17 — 2015: non-sideloaded titles with obfuscated fonts fell back to the default font; support later confirmed 2017. Basis for "don't rely on obfuscation."
8. **MobileRead — Pop-up footnotes gone AWOL in fw 4.0.7523** — https://www.mobileread.com/forums/showthread.php?t=278792 — Kobo Aura One, **2016** (corrected from "2018"). Regression; fix = keep text/OPF out of the EPUB root (subfolder).
9. **MobileRead — Pop-Up Footnotes, Asides, and Compatibility** — https://www.mobileread.com/forums/showthread.php?t=296819 — Documents the legacy (≈2018 ADE-era) id-placement tension; now OBSOLETE for modern KePub.
10. **MobileRead — Pop-up footnotes in Kobo eReaders (2023–24, Libra Colour)** — https://www.mobileread.com/forums/showthread.php?t=364265 — PRIMARY, user's hardware family: popups require **KePub**, not plain EPUB3; documents the criteria by which kepub turns ordinary internal links into popups (#id target, ≥9 visible chars, ≤5000 chars, forward) — cross-reference hazard for a Bible. One user abandoned kepub.
11. **MobileRead — Kobo and Footnotes. Again.** — https://www.mobileread.com/forums/showthread.php?t=352480 — Sage/Forma/Libra H2O: no popups in KePub though fine in Calibre; fix = one-to-one HTML-file↔TOC mapping.
12. **MobileRead — Kobo jumping to footnotes instead of popup? (Nov 24 2024)** — https://www.mobileread.com/forums/showthread.php?p=4469732 — PRIMARY: non-ASCII (Chinese) ids break the Kobo popup on an already-converted KePub; ids must be ASCII, first char ASCII-alpha (an EPUB-spec rule); ASCII-id fix verified popping up on a real Kobo.
13. **MobileRead — Force visibility for epub:type="footnote"** — https://www.mobileread.com/forums/showthread.php?t=352393 — Apple Books force-hides `<aside epub:type=footnote>` and ignores `aside{display:block!important}`. Apple force-hides override author CSS.
14. **MobileRead — Embedded fonts in kepub goes hiding** — https://www.mobileread.com/forums/showthread.php?t=271836 — KEY: KePub reader stylesheet = `* { font-family: %1 !important; }` (overrides embedded `@font-face` on ALL elements unless "Publisher Default"); plain-EPUB reader = `body, p { font-family: -ua-default !important; }` (preserves embedded fonts more readily). Refutes "KePub is better for embedded fonts."
15. **MobileRead — kepub vs epub render engines** — https://www.mobileread.com/forums/showthread.php?t=328335 — Mar 2020: plain EPUB = RMSDK (Adobe DE) with better typography (ligatures/kerning/hyphenation); KePub = ACCESS NetFront (WebKit) with faster turns/search/zoom but weaker typography. "Try both."
16. **MobileRead Wiki — Kepub** — https://wiki.mobileread.com/wiki/Kepub — kepub vs sideloaded epub; per-sentence span ids drive location memory; `.kepub.epub` double extension; kepub advantages (footnote previews, image zoom, dither, stats) and plain-epub advantages (hyphenation, justification, font embedding, full-screen).
17. **MobileRead — Kobo Aura: enable publisher fonts embedded in epub?** — https://www.mobileread.com/forums/showthread.php?t=320161 — fw 3.8.0 (~2013-14): embedded fonts only show when "Publisher Default"/"Document Default" is selected. Old firmware — re-test.
18. **MobileRead — Problem with an embedded font on Kobo** — https://www.mobileread.com/forums/showthread.php?t=323355 — Aura H2O 2E, fw 4.15→4.17: an embedded OTF that failed was caused by a custom firmware PATCH, not Kobo; on stock fw "when the font was embedded, it displayed."
19. **MobileRead — publisher font (forcing/honoring embedded fonts)** — https://www.mobileread.com/forums/showthread.php?t=359868 — Most readers don't use the publisher font by default; some need "Publisher"/"Original"; some apps ignore embedded fonts. Supports user-override + fallback-chain + on-device test.
20. **MobileRead — Kobo Touch and Arabic (complex/non-Latin via fonts)** — http://www.mobileread.mobi/forums/showthread.php?t=140985&page=5 — Kobo built-in fonts have weak non-Latin coverage; Amharic/Ethiopic needed custom fonts; embedding the glyphs is the mitigation. Older, directional.
21. **MobileRead — Bug: colon in `<a>` name/href hangs "Processing content"** — https://www.mobileread.com/forums/showthread.php?t=177946 — Colons in anchor values (`Carnap:23a`, `Template:Honorverse`) make Nickel HANG / soft-brick the add; structural, not size. Keep fragments colon-free.
22. **MobileRead — How to speedup page turn on sideloaded epub (Kobo Touch fw 2.0)** — https://www.mobileread.com/forums/showthread.php?t=185697 — Whole-spine-file layout; page-turn timings KePub 1.26s / plain 1.93–3.52s / split 1.71–2.21s. DATED firmware. Measures page-turn latency (a 25KB split improved turns).
23. **MobileRead — epub load time, possible file optimizations?** — https://www.mobileread.com/forums/showthread.php?t=89615 — 4.2 MB EPUB w/ 100–300 KB HTML ≈ 2 min; over-splitting to 100 KB chunks ≈ 3.5 min (WORSE — load/seek). Calibre ignores splits < 100 KB. Measures initial load, not page-turn.
24. **MobileRead — Glo Sideload ePub slow to load** — https://www.mobileread.com/forums/showthread.php?t=231630 — Single giant file (325 pages) ≈ 5 min; "the bigger the chapter file, the longer it takes… gets worse as you read." Fixed by split + KePub.
25. **MobileRead — Normal for kobo to take forever on "Processing content"? (Aura H2O, 2015)** — https://www.mobileread.com/forums/showthread.php?t=261526 — SECOND root cause: import-time SQLite/TOC indexing (~100 DB entries/book), distinct from in-book reflow; a single bad-formatted book can hang the whole batch. Mitigate: small batches, keep powered, epubcheck-clean.
26. **MobileRead — EPUB3 CSS not implemented on Google Play Books** — https://www.mobileread.com/forums/showthread.php?t=237490 — Publisher reports of Play Books ignoring large parts of EPUB3 CSS. Basis for "partial / verify on device."
27. **MobileRead — Flexbox in ePub3 (Apr 2021), DNSB** — https://www.mobileread.com/forums/showthread.php?t=338796 — "Support for Flexbox is, at best, spotty so be prepared to work around that." 2021; pre-dates the 2026 "strong on Kobo" report.
28. **MobileRead — Collapsible TOC? (t=279639)** — https://www.mobileread.com/forums/showthread.php?t=279639 — You cannot control how a device renders the NCX/nav TOC; structure the nav TOC + a separate styled in-page HTML TOC.
29. **MobileRead Wiki — SVG (full-page/cover SVG wrapper pattern)** — https://wiki.mobileread.com/wiki/SVG — Canonical SVG-wrapper cover pattern; but FlightDeck/Apple advise plain `<img>` for broadest compatibility (SVG not supported on all readers).
30. **Apple — Pop-up Footnotes (Book Asset Guide)** — https://help.apple.com/itc/booksassetguide/en.lproj/itccf8ecf5c8.html — PRIMARY (Apple). `<a epub:type=noteref>` + `<aside epub:type=footnote>` with matching id; requires `xmlns:epub` on `<html>`; aside hidden from main flow; RTL via `<p>` direction; div/p keeps the note visible.
31. **Apple Books Asset Guide — Content Structure** — https://help.apple.com/itc/booksassetguide/en.lproj/itc8b763f645.html — "In flowing books, divide each chapter into its own XHTML document"; "Separating chapters into documents improves performance in Apple Books"; page break between documents; relies on HTML semantics (use real h1/h2).
32. **Apple Books Asset Guide — Best Practices for Fonts** — https://help.apple.com/itc/booksassetguide/en.lproj/itcb303b7bb5.html — "OpenType, TrueType, and SVG embedded fonts are supported" (WOFF/WOFF2 NOT listed); embedded fonts must be declared in OPF + CSS; sizes in em/px (main text no font-size or 1em); check hinting/metrics. Basis for "embed OTF, not WOFF2."
33. **Apple Books Asset Guide — Fonts Overview (specified-fonts)** — https://help.apple.com/itc/booksassetguide/en.lproj/itc74d42b31e.html — Flowing books honor embedded fonts when `specified-fonts` is true; readers can return to original fonts.
34. **Apple Books Asset Guide — Font Obfuscation** — https://help.apple.com/itc/booksassetguide/en.lproj/itca841e35de.html — Apple supports EPUB 3 font obfuscation (accepted but unnecessary for open fonts).
35. **Apple Books Asset Guide — Presentation and Styling** — https://help.apple.com/itc/booksassetguide/en.lproj/itc04314e64a.html — Prefer `page-break-after` for chapter breaks (TOC perf); dark-theme custom text color via `ibooks-dark-theme-use-custom-text-color` or `:root{color-scheme:light dark}`+`prefers-color-scheme`; insert soft hyphens.
36. **Apple Books Asset Guide — Interior Image Requirements** — https://help.apple.com/itc/booksassetguide/en.lproj/itca71ad3c33.html — Interior images ≤ 5.6 million px; ~10 MB un-encoded per XHTML; sRGB; JPEG/PNG; sanctioned `img{height:50vh;}`; "use the HTML img tag instead of wrapping images in svg:image." (Pixel cap history: 2 → 3.2 → 5.6 Mpx.)
37. **Apple Books Asset Guide 5.3.1 (top-level / static)** — https://help.apple.com/itc/booksassetguide/en.lproj/static.html — "Interactive content is supported for both flowing books and fixed-layout books." EPUB ≤ 2 GB (recommended ≤ 500 MB). Confirms current guide version 5.3.1.
38. **Google Play Books Partner Center — EPUB files** — https://support.google.com/books/partner/answer/3316879 — PRIMARY (Google). Accepts EPUB 3.3 (preferred)/3/2; supports fixed-layout; GIF/JPEG/PNG/SVG; **3200px cap** on width/height attrs of `<image>`/`<svg>` tags and referenced files; "Embedded fonts ✔" with no format/obfuscation/subsetting detail; "does not support interactive functionality such as that enabled by JavaScript"; advises Content-Reviewer eyeball + PDF for layout-critical books. Silent on flexbox/`<details>`/per-XHTML size.
39. **Google Play Books Partner Center — Book file guidelines** — https://support.google.com/books/partner/answer/3424254 — Each file < 2 GB (incl. cover); EpubCheck-valid; front cover + complete book required. No per-XHTML/split/performance guidance.
40. **The Digital Reader — Google Play Books doesn't serve EPUB as-is (server-side internal format)** — https://the-digital-reader.com/google-play-books-doesnt-support-epub-crazy-possibilities/ — SECONDARY/practitioner (Nate Hoffelder): Play Books re-renders/alters markup server-side (apply CSS → compute page breaks → chop HTML per-page → re-apply CSS). Basis for "may silently flatten `<details>` / diverge CSS" and the "unknown" verdicts.
41. **C. M. Sperberg-McQueen — Google Play Books and CSS** — https://cmsmcq.com/mib/?p=1405 — Expert write-up documenting Play Books dropping/overriding CSS; converts to an internal format.
42. **kepubify (Patrick Gaskin) — feature list / docs** — https://pgaskin.net/kepubify/ — PRIMARY tool. "On Kobo EPUBs, footnotes will appear as a pop-up dialog when supported by the original book"; "Fixed-layout, page spreads, MathML, HTML5… only supported on the KEPUB reader." "Page turns, font changes, highlighting, and searching are much more responsive on KEPUBs"; ~40–80x faster than Calibre. **This is the KePub-required citation (not the Kobo README).**
43. **kepubify docs — HTML handling vs Calibre** — https://pgaskin.net/kepubify/docs/ — kepubify "modifies source content less than Calibre and parses HTML properly" — recommend kepubify (not Calibre) to keep `<details>` etc. intact.
44. **kepub package — pkg.go.dev (pgaskin/kepubify/v4/kepub)** — https://pkg.go.dev/github.com/pgaskin/kepubify/v4/kepub — The exact transform: `div#book-columns > div#book-inner` pagination target + `koboSpan` fragments — "Highlighting, bookmarking, and other related features don't work without this." OPF cover normalized; metadata stripped; polyglot XHTML.
45. **calibre-kobo-driver (jgoguen)** — https://github.com/jgoguen/calibre-kobo-driver — KePub Output / KoboTouchExtended plugins enable kepub features; folded into Calibre 8.0 core.
46. **New in calibre 8.0** — https://calibre-ebook.com/new-in/seventeen — KePub view/convert/edit built into Calibre 8.0 (~Mar 2025); third-party Kobo plugins no longer required; EPUB auto-converts to KEPUB on send-to-Kobo.
47. **Good e-Reader — Calibre 8.0 native KEPUB conversion (Mar 2025)** — https://goodereader.com/blog/kobo-ereader-news/calibre-8-0-can-now-convert-e-books-to-kepub — Tooling update: native Calibre 8.0+ KEPUB; plugin no longer strictly required.
48. **jonsdocs — Fixing slow page turns on Kobo (ePub), 2 Aug 2024** — https://blog.jonsdocs.org.uk/2024/08/02/fixing-the-problem-of-slow-page-turns-on-kobo-epub/ — Recent confirmation the slow-page-turn problem persists; store KePub vs sideloaded plain EPUB; fix = convert to KePub.
49. **sangsara.net — Fixing freezing / battery drain on Clara Color, 23 Mar 2025** — https://sangsara.net/2025/03/23/fixing-freezing-and-battery-drain-issues-on-modern-kobo-readers-such-as-the-clara-color/ — Names the Clara Color; attributes lockups to EPUB ERRORS (bad markup / missing font specs) → reinforces epubcheck-0/0/0/0 discipline.
50. **How Frank Did It — A fix for slow ebooks (Kobo)** — https://howfrankdidit.com/a-fix-for-slow-ebooks — Monolith (cover + one file holding 355 pages / 43 chapters) was slow; fix = Sigil "Split at Markers" one file per chapter.
51. **Kobo Blog — Libra Colour & Clara Colour launch** — https://www.kobo.com/news/now-in-colour-bring-your-books-to-life-with-the-new-kobo-libra-colour-and-kobo-clara-colour-ereaders — In-scope color hardware released 2024-04-30 (Clara BW same wave); faster than the 2012–2015 devices the hard numbers come from.
52. **Kobo firmware downloads (Patrick Gaskin)** — https://pgaskin.net/KoboStuff/kobofirmware.html — Current Clara Colour/Clara BW on the 4.42.x line (4.42.23296, 3 Jun 2025); 2024 update notes mention handling "outdated CSS" but no flexbox/layout specifics — firmware-opaque.
53. **Software Update 4.45 for latest Kobo eReaders (the-ebook-reader)** — https://blog.the-ebook-reader.com/2026/02/26/software-update-4-45-released-for-latest-kobo-ereaders/ — Dates current Colour-line firmware (4.45.23640, Feb 2026); release notes are generic bug-fixes.
54. **Rakuten Kobo Help — Load fonts onto your Kobo eReader** — https://help.kobo.com/hc/en-us/articles/13009477876631-Load-fonts-onto-your-Kobo-eReader — First-party current doc: sideloaded fonts via a `/fonts` directory; the font picker governs which font is used (consistent with "select Publisher Default").
55. **Flexbox prevents EPUB opening — pandoc issue #8379 (Oct 2022)** — https://github.com/jgm/pandoc/issues/8379 — Pandoc's OWN column-div flexbox CSS made an EPUB unopenable on ONE PocketBook Pro 912; **FIXED in pandoc 3.1.9** (flexbox no longer used by default). Pandoc-specific, never a Kobo failure.
56. **pandoc 3.1.9 release / changelog** — https://github.com/jgm/pandoc/releases/tag/3.1.9 — "For compatibility with older readers, flexbox is not used by default to style column/columns divs in EPUB." Resolution of #8379.
57. **DAISY KB — The details element** — https://kb.daisy.org/publishing/docs/html/details.html — © 2026. "Support for the details element in EPUB reading systems is still inconsistent"; expanding "can cause the content of a page to be pushed off screen (will not reflow onto the next)"; "provides a way to expand and collapse… without depending on JavaScript." Strongest basis for the no-JS advantage + the off-page hazard.
58. **DAISY KB — Hidden content / hidden attribute** — https://kb.daisy.org/publishing/docs/html/hidden.html — © 2026. "Expanding may force content below the element off the bottom of the current page, making it unavailable to sighted readers"; CSS fallback `*[hidden]{display:none;}`; "does not require scripting support." Support for open-by-default + never-hide-behind-toggle.
59. **DAISY KB — Notes** — https://kb.daisy.org/publishing/docs/html/notes.html — AUTHORITATIVE (Matt Garrish / DAISY). Recommended accessible markup pairing `epub:type` with `role=doc-noteref`/`doc-footnote`/`doc-backlink`; `aside` for footnotes; `section epub:type=endnotes` for grouped endnotes.
60. **a11ysupport.io — HTML details element** — https://a11ysupport.io/tech/html/details_element — `<details>` "supported" on WebKit/Safari + VoiceOver (iOS & macOS) and Chrome/Chromium; single test last updated 2022-05-27 (~4 yrs old — the only element-specific datapoint).
61. **W3C EPUB Fixed Layout Accessibility (epub-fxl-a11y)** — https://www.w3.org/TR/epub-fxl-a11y/ — W3C Group Note (2026-04-02). "Expanding details elements within a fixed layout page is also likely to disrupt the page" — FXL-framed; pair with the DAISY KB pages for the reflowable mechanism.
62. **W3C EPUB Accessibility — Fixed Layout Challenges (note context)** — https://www.w3.org/TR/epub-fxl-a11y/ — (same doc) confirms the page-disruption risk of expanding `<details>`; mechanism applies to paginated reflowable too.
63. **W3C EPUB 3.3 — Recommendation (13 January 2026)** — https://www.w3.org/TR/epub-33/ — PRIMARY/NORMATIVE. `epub:type` structural semantics defined; popup PRESENTATION left entirely to the reading system (non-normative). Font core media types (font/ttf, font/otf, font/woff, font/woff2); §4.4 font obfuscation (key from unique identifier, XOR first 1040 bytes, encryption.xml); cover-image a manifest property; `rendition:layout` pre-paginated = FXL; SVG a core media type but not all RS render it.
64. **EPUB 3.3 becomes a W3C Recommendation (W3C News, 25 May 2023)** — https://www.w3.org/news/2023/epub-3-3-becomes-a-w3c-recommendation/ — Corrects the "Jan 2025" date: EPUB 3.3 first reached Recommendation 25 May 2023.
65. **Updated W3C Recommendation: EPUB 3.3 (W3C News, 27 March 2025)** — https://www.w3.org/news/2025/updated-w3c-recommendation-epub-3-3/ — Minor updated Rec (conformance clarifications only); nothing changed about CSS support / rendering obligations. EPUB 3.4 working drafts published same day.
66. **W3C EPUB Reading Systems 3.3 (Recommendation)** — https://www.w3.org/TR/epub-rs-33/ — §6.3: visual RS "MUST support TrueType, OpenType, WOFF, and WOFF2 font resources referenced from @font-face rules" (the spec ideal Kobo e-ink does not meet); scripting only SHOULD; `epub:type` behavior association is MAY (so popup behavior is implementation-defined); SHOULD support deobfuscation.
67. **W3C EPUB Reading Systems 3.4 (in progress)** — https://www.w3.org/TR/epub-rs-34/ — Does not mandate popup rendering for footnotes/asides; confirms divergence is spec-permitted.
68. **W3C epub-specs Issue #327 — absolute positioning clarification** — https://github.com/w3c/epub-specs/issues/327 — `position:absolute` IS in the EPUB CSS profile (only `position:fixed` excluded); the "avoid absolute positioning" note targets arbitrary/EPUB-2.x RS; graceful degradation encouraged. Attribution for "pagination of absolutely-positioned content not guaranteed."
69. **W3C publ-cg Issue #3 — reflowable image-bleed (archived)** — https://github.com/w3c/publ-cg/issues/3 — Dave Cramer (2017); repo archived 2022-04-26. No standard CSS mechanism for reflowable full-bleed ever shipped — FXL is the only route.
70. **W3C epub-specs Issue #1687 — RS handling of container directory structure** — https://github.com/w3c/epub-specs/issues/1687 — Some RS (Kobo named) mishandle content not in the OPF's directory or a descendant — keep XHTML + OPF in a subfolder, never the EPUB root.
71. **IDPF EPUB OCF 3.0.1 — Font obfuscation algorithm** — https://idpf.org/epub/301/spec/epub-ocf.html — Key = SHA-1 of the UTF-8 unique identifier with XML whitespace removed; XOR the first 1040 bytes; encryption.xml algorithm `http://www.idpf.org/2008/embedding`; key must NOT be stored. Corrects the imprecise "MD5" phrasing.
72. **IDPF EPUB 3 Accessibility Guidelines — Notes** — https://idpf.github.io/a11y-guidelines/content/xhtml/notes.html — Note refs use `<a epub:type=noteref>`; in-flow notes use `<aside epub:type=footnote>`; grouped notes use `<section epub:type=endnotes>`.
73. **Calibre viewer — role="doc-noteref" makes footnotes pop up (Kovid Goyal)** — https://www.mobileread.com/forums/showthread.php?t=333703 — Add `role="doc-noteref"` so the Calibre viewer pops up; Calibre viewer ≠ Kobo Nickel — do not use it as a Kobo proxy.
74. **koreader — `<aside epub:type=footnote>` rendered twice (Issue #8623)** — https://github.com/koreader/koreader/issues/8623 — A 3rd reading system renders aside footnotes both inline and at page bottom — aside auto-hide is NOT universal; reinforces "do not rely on auto-hide."
75. **EPUBSecrets — Easy CSS Wins (Jiminy Panoz, 2017)** — https://epubsecrets.com/easy-css-wins.php — The `.titlepage` flex pattern (`min-height:95vh; display:flex; flex-direction:column; margin-top:auto`); flexbox needs a feature query + fallbacks; large user font-size overflows the container.
76. **BlitzTricks — CSS tricks to improve your eBooks (Friends of EPUB / Jiminy Panoz)** — https://friendsofepub.github.io/eBookTricks/ — `@supports (display:-webkit-flex) or (display:flex)` wrapping `-webkit-`-prefixed + standard flex, `min-height`+`vh`, with fallbacks. Basis of the cross-reader flex pattern.
77. **Ebook Title Page Formatting (ebookpbook, 30 Mar 2026)** — https://www.ebookpbook.com/2026/03/30/ebook-title-page-word-formatting/ — Most recent device-specific flex evidence: "Flexbox support is strong on Kindle, Apple Books, and Kobo, but some older e-ink devices may not render it correctly"; recommends `display:flex; align-items:center; min-height:100vh` with `margin-top:30vh` fallback.
78. **Jiminy Panoz — Image wizardry in eBooks** — https://medium.com/@jiminypan/image-wizardry-in-ebooks-3ea96064d0a6 — `height:Nvh` + `object-fit:contain` for full-page images; `max-height` is overridden/ignored in Apple Books; Play Books doesn't support `page-break-before:always`; float expensive in legacy RMSDK.
79. **JayPanoz / Soma wiki — How to embed fonts** — https://github.com/JayPanoz/Soma/wiki/How-to-embed-fonts — Exact `ibooks:specified-fonts` OPF syntax + package prefix; EPUB2 `com.apple.ibooks.display-options.xml` alternative. "Stick with OTF" (don't stake your life on WOFF; WOFF2 not discussed). Independent corroboration of "embed OTF, not WOFF2."
80. **FlightDeck Handbook — Cover Images** — https://ebookflightdeck.com/handbook/coverimage — Plain `<img>` cover with `body{margin:0;padding:0}`, `section height:95%`, `img:only-of-type{height:95vh}`; explicitly AGAINST `<svg>` cover wrappers. Basis for the conservative cover pattern.
81. **FlightDeck Handbook — Embedded Fonts (Unicode-only / no Latin-remap)** — https://ebookflightdeck.com/handbook/fonts — Verbatim warning that Hebrew/Sanskrit print fonts which remap Latin codepoints are "not appropriate for eBooks, and will prove problematic." Correct attribution for the "Unicode-only fonts" rule.
82. **Helicon Books — Footnotes in EPUB3** — https://www.heliconbooks.com/?id=blog&postid=EPUB3Footnotes — Standard noteref/aside markup; "Do not put special styles for the aside tag as you don't know how the reading system will show it"; iBooks=popup, others jump-with-back-button; EPUB3 gives no rule for footnote display.
83. **Liz Castro — Creating pop-up footnotes in EPUB 3** — http://pigsgourdsandwikis.blogspot.com/2012/05/creating-pop-up-footnotes-in-epub-3-and.html — Foundational reference for the `epub:type` noteref+footnote popup technique (2012).
84. **publisha.org — Footnotes, Endnotes, Sidenotes and Popup Notes** — https://www.publisha.org/pages/footnotes/ — Confirms Apple iBooks + "later Kobo devices" support; non-popup readers fall back to hyperlinks. Does not address Google Play Books.
85. **Google Play Books personal-upload 100 MB cap (Android Police, 2014)** — https://www.androidpolice.com/2014/02/28/google-doubles-play-books-file-size-upload-limit-to-100mb-per-file/ — PERSONAL-library upload limit = 100 MB per file, max ~1,000 books/account — distinct from the 2 GB publisher limit, applies to the whole EPUB.
86. **EPUBSecrets — Updated BISG EPUB 3.0 Support Grid** — https://epubsecrets.com/updated-bisg-epub-3-0-support-grid.php — Checked but STALE for flexbox (2012 grid predates flexbox in reading systems) — noted so it isn't relied on.
87. **epubcheck Issue #1605 — CSS `:has()` false positive (CSS-008), fixed v5.3.0** — https://github.com/w3c/epubcheck/issues/1605 — `display:flex` PASSES epubcheck; the CSS-008 rejection was the `:has()` token, fixed in epubcheck 5.3.0. Use a current epubcheck; it cannot verify device rendering.

---

*Produced 2026-06-05 (Mac lane) by a verified multi-agent web-research pass (run `wf_9e7ad47b-155`): 7 topics, each independently researched, then adversarially fact-checked, then synthesized. Ratings are evidence-based but **no rating substitutes for an on-device test** — see "Open questions / must-test on the physical Kobo." De-risks D2/D3/D4/D5 of `docs/superpowers/plans/2026-06-05-epub-reading-experience-overhaul.md`.*
