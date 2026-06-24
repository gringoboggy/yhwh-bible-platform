# Kobo reading-font-override research — why Hebrew fails & the fix

> Research brief for the WIN lane (owner of `scripts/build_edition.py`). Audience: an engineer who will implement the fix and device-test on a real color Kobo. Be ready to A/B against the user's own "Cardo" reading-font setting.
>
> Date: 2026-06-24 · Lane: written on Mac, for WIN to implement. Sources are inline as URLs.

## TL;DR

The Hebrew tofu is **not** a Cardo coverage problem (Cardo embeds fine and does cover pointed Hebrew). It is Kobo's **kepub firmware override**: as soon as the user selects any *named* reading font (e.g. "Cardo") in the Aa menu, libnickel injects a user-origin rule `* { font-family: <userfont> !important; }` that clobbers **every** publisher `font-family` — and a *user/UA-origin `!important` beats an author `!important` regardless of selector specificity*, so even `.vnote-hebrew{…!important}` would not win. Our `.vnote-hebrew` rule has **no `!important` at all**, putting it in the lowest cascade tier. **The one recommended fix is two-pronged and both prongs are required:** (1) add `!important` to every original-language vnote `font-family` (`.vnote-hebrew`, `.vnote-greek`, **`.vnote-greek-nt`**, `.vnote-geez`/`.vnote-amharic`) and **embed + name an Arabic face** (`Noto Naskh Arabic`, already on disk, OFL) for `.vnote-arabic`; and (2) ship a **front-matter "Publisher Default" instruction page**, because the user-font override is firmware-level and the `!important` change only out-ranks the *universal* injected rule on the *in-flow* text — it cannot reach Kobo's native footnote-**preview** overlay (which always uses the reader font), for which the sideloaded `yhwh-kobo-font-pack.zip` remains the belt-and-suspenders mitigation.

## Problem statement

The user reports: on his **color Kobo**, with **"Cardo" selected as his reading font**, Hebrew in the original-language popups renders as **boxes/blanks (tofu)** — even though:

- **Cardo is embedded** in the EPUB as three TTF faces (`Cardo-Regular/Italic/Bold.ttf`) via `scripts/style_config.py:94-98` (`EMBED_FONT_PATHS`) and copied into the EPUB at build (`build_edition.py:7487` copytree of `epub_working/fonts/`).
- **Cardo covers Hebrew including vowel-pointing** — confirmed in `content/assets/fonts/LICENSES.md:13-15,41-45` ("covers Latin, polytonic Greek, and Hebrew (including vowel-pointing) … the single embedded face that guarantees a legible glyph"). It has **no `unicode-range`**, so any stack naming "Cardo" can use it for any script it covers.
- **`.vnote-hebrew` names "Cardo" first** in its `font-family` stack (`epub_working/stylesheet.css:327-339`).

So by the local cascade the Hebrew glyph *should* resolve to embedded Cardo. It does not, on-device. The defect is therefore a **render-path/override** issue, not a glyph-coverage or a `lang`-attribute issue.

## Current state (from the codebase)

### Fonts embedded in the EPUB (4 faces, all TTF, all OFL 1.1)

| Family | Files | Scripts | `unicode-range`? | Where |
|---|---|---|---|---|
| **Cardo** | `Cardo-Regular/Italic/Bold.ttf` (3 faces) | Latin + polytonic Greek + Hebrew (w/ pointing) | **No** → usable by any "Cardo" stack | `style_config.py:96-98`; `stylesheet.css:18-38` |
| **Noto Serif Ethiopic** | `NotoSerifEthiopic-Regular.ttf` (1 face, v2.102, 384 KB) | Ethiopic/Ge'ez/Amharic **only** | **Yes** — scoped to 5 Ethiopic blocks → inert for Latin/Hebrew/Greek/Arabic | `style_config.py:106-112`; `stylesheet.css:39-50` |

`Noto Naskh Arabic` (`NotoNaskhArabic-Regular.ttf`, 291,980 B, OFL 1.1) **exists on disk** (`content/assets/fonts/`) but is **NOT embedded** — not in `EMBED_FONT_PATHS`, no `@font-face`, no OPF item. Per `LICENSES.md:116-133` it ships **only** in the sideloaded `yhwh-kobo-font-pack.zip`. So Arabic has **zero in-book coverage**.

### The exact `.vnote-*` CSS (font-family lines, verbatim)

```css
/* epub_working/stylesheet.css:327-339 — Hebrew. NO !important. */
.vnote-hebrew {
    text-align: right;
    font-family: "Cardo", "SBL Hebrew", "Ezra SIL", "Frank Ruehl CLM", "Times New Roman", serif;
    font-size: 1.05em; line-height: 1.7; margin: 0.1em 0 0.3em 0;
}

/* epub_working/stylesheet.css:341-349 — Greek (OT/LXX). NO !important. */
.vnote-greek {
    font-family: "Cardo", "SBL Greek", "GFS Didot", "Times New Roman", serif;
    font-size: 1.0em; line-height: 1.55; margin: 0.1em 0 0.3em 0;
}
```

- **`.vnote-greek-nt`** (used by the Greek NT, `popup_versions.py:49`) has **NO dedicated `font-family` rule** anywhere — it falls through to the body/`.vnote` default stack, **not** to `.vnote-greek`'s Cardo stack.
- **`.vnote-arabic`** is defined **only** in `_EINK_READER_CSS` (`build_edition.py:2397-2399`), eink targets only, and has **NO `font-family`** — Arabic falls back to the body stack (Noto Serif Ethiopic is range-scoped away; nothing covers Arabic) → tofu. On non-eink targets there is **no `.vnote-arabic` rule at all**.
- **`.vnote-geez`/`.vnote-amharic`** font-family rules live only in `apply_style.py:235-262` — the **stale managed region that is NOT run for this base** (`stylesheet.css:10-11`). They also name the **wrong family** (`"Noto Sans Ethiopic"`) vs. the embedded `"Noto Serif Ethiopic"`. So no `.vnote-geez` font-family ships; body Ge'ez relies on the range-scoped body `@font-face`.
- **No `font-family` declaration on any `.vnote-*` script class uses `!important`.** (`!important` appears only on margins / `.vn` verse-num rules — unrelated.)

### `lang` attribute usage

`lang` (but **never `xml:lang`**) is emitted on labeled-version popup `<p>` spans by `generate_verse_popups.py:45-49`, from `popup_versions.py` `VERSION_REGISTRY`: Hebrew `<p class="vnote-hebrew" dir="rtl" lang="he">`, Greek `lang="grc"`, Arabic `dir="rtl" lang="ar"`. **`lang`/`xml:lang` does not select a font on its own** — see Q-findings below — so this is not the cause; it is an a11y/TTS hint only (and the missing `xml:lang` is a minor strict-XML completeness gap, not a render bug).

### eink CSS + kepubify

`_EINK_READER_CSS` (`build_edition.py:2359-2400`, appended by `apply_eink_reader_css` only when `target_reader=="eink"`, wired at `build_edition.py:7530`) adds **no `@font-face` and no `font-family` for any script**. It does not re-point `.vnote-hebrew`/`.vnote-greek` to the embed. kepubify is a **bare invocation** — `kepubify -o <dest.kepub.epub> <source.epub>`, no flags (`build_format_matrix.py:198-202`, pinned v4.0.4). It wraps text in `<span class="koboSpan">` and the body in `#book-columns > #book-inner`, but injects **no competing font CSS**. The kepub is byte-derived from the already-styled eink EPUB.

### OPF font items

The committed `epub_working/content.opf` has **zero** font `<item>` entries. They are injected at build by `patch_opf_fonts()` (`build_edition.py:6802-6854`), iterating `EMBED_FONT_PATHS` → 4 items (`font-cardo-regular`, `font-cardo-italic`, `font-cardo-bold`, `font-noto-serif-ethiopic-regular`), all `media-type="font/ttf"`. `NotoNaskhArabic` gets **no** item (not in `EMBED_FONT_PATHS`).

### Specific weaknesses

1. **No `!important`** on any original-language `font-family` → loses to Kobo's injected override (and even loses to it *with* `!important`, but `!important` is the necessary first step — see Q1).
2. **No embedded Arabic face and no Arabic `font-family`** → guaranteed tofu in-book regardless of CSS.
3. **`.vnote-greek-nt` has no `font-family`** → inherits body serif; Kobo won't fall back from a generic Latin/`serif` name to a Greek face → Greek-NT at risk.
4. **`.vnote-geez`/`.vnote-amharic` font-family never ships** (stale region) and names the wrong family.
5. **No front-matter "Publisher Default" instruction** — the only firmware-sanctioned lever to defeat the override is undocumented to the user.
6. Reliance on the **same font the user picked**: the body stack deliberately dropped Cardo + `!important` so the reader's chosen font wins; that is exactly what lets the override reach the popups.

## Findings — the three handoff questions, answered

### Q1. Does an element/class-level forced `@font-face` (or `font-family !important`) still win, or does Kobo's global override clobber it?

**Kobo's global override clobbers a plain author rule outright, and a *user/UA-origin* `!important` beats an *author* `!important` regardless of specificity — BUT among the cascade tiers our rule currently sits in, adding `!important` is still the necessary and (for in-flow text) sufficient author-side move.** This needs care, because the four research angles look superficially contradictory; here is the reconciled, decisive answer:

- On a stock kepub, when a *named* reading font is selected, libnickel (`KepubBookReader::pageStyleCss`) injects literally `* { font-family: <userfont> !important; }`. This is verbatim from the firmware patch source that targets that exact string — pgaskin's *"Un-Force user font-family in KePubs"* patch — which describes the behavior as *"a very heavy-handed method … overriding all fonts set by the publisher in the book unless 'Publisher Default' is selected."* ([kobopatch-patches geoffr.yaml](https://github.com/pgaskin/kobopatch-patches/blob/master/src/versions/4.16.13162/libnickel.so.1.0.0.yaml/geoffr.yaml); [MobileRead t=365692](https://www.mobileread.com/forums/showthread.php?t=365692), [t=271836](https://www.mobileread.com/forums/showthread.php?t=271836), [t=366602](https://www.mobileread.com/forums/showthread.php?t=366602)).
- **The injected rule carries `!important` but has the lowest possible specificity (`*` = 0,0,0).** Per the CSS cascade, `!important` flips the origin order so user/UA-important beats author-important — *"important styles from user's or user-agent's style sheets … override [author important] … even if the selector from a lower precedence origin has greater specificity"* ([MDN Cascade](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_cascade/Cascade); [W3C CSS2 §6](https://www.w3.org/TR/1998/REC-CSS2-19980512/cascade.html)). **The critical empirical question is which origin the kepub injection is actually treated as.**
  - If libnickel injects it as a **user/UA-origin** sheet, then *no* author rule — any specificity, with or without `!important` — can beat it; the only levers are "Publisher Default", the firmware patch, or glyph-fallback (Angles 1 & 2 emphasize this conservative reading).
  - If it is injected as an **author-origin** sheet (which the patch's WebKit page-style injection mechanism and several empirical reports suggest), then it is `*{…!important}` at author-important tier, and **`.vnote-hebrew{…!important}` (specificity 0,1,0, author-important) out-specifies it and wins** (Angle 4 documents this precisely: *"any class-level `!important` beats the universal `!important`"*).
- **Decision for WIN:** treat `!important` as **necessary and high-value, and likely sufficient for in-flow popup text, but device-test it as the deciding evidence.** It is free, it is the only author-side lever that has any chance, and multiple practitioners report it working for class-level rules. If the real-device A/B shows Hebrew *still* tofus with `!important` present, then on this firmware the injection is user-origin and **no CSS fix exists** — fall through to the "Publisher Default" front-matter instruction (which always works) + the sideload pack.

**Net:** A bare class rule (our current state) definitely loses. `.class { … !important }` is the maximal author-CSS lever and is the right thing to ship; "Publisher Default" + the font pack are the guaranteed backstops.

### Q2. How do other EPUB publishers reliably render Hebrew/Greek/Arabic under a user-selected Latin reading font on Kobo?

They do **not** rely on author CSS alone. The documented, publisher-relied-upon recipe (Kobo's own spec + scripture/academic publishers) is:

1. **Embed a real Unicode font for each non-Latin script and name that family explicitly on the run's class** — never let a non-Latin run inherit a generic `serif`/Latin family. *"If your font is not embedded or you are not using the correct language code, readers might only see empty white squares or question marks"* ([PublishDrive: non-Latin scripts](https://help.publishdrive.com/embedding-font-for-non-latin-scripts)); one `@font-face` per weight/style, then apply the family to the element ([FlightDeck handbook](https://ebookflightdeck.com/handbook/fonts), [O'Reilly *EPUB 3 Best Practices* ch.4](https://www.oreilly.com/library/view/epub-3-best/9781449329129/ch04.html)).
2. **Ship kepub** so Kobo's missing-glyph fallback is alive — *plain EPUB on Kobo has essentially no glyph fallback; kepub does* ([MobileRead Kepub wiki](https://wiki.mobileread.com/wiki/Kepub): kepub = *"Automatic Font Substitution if current font is missing a glyph that is available in another font"*; [t=310530](https://www.mobileread.com/forums/showthread.php?t=310530) — a font fine in Calibre's viewer showed boxes on-device because the e-reader has no system fallback library).
3. **Add a front-matter note instructing the reader to select "Publisher Default."** This is Kobo's official, twice-stated mitigation: *"If the reading experience of a book requires that the embedded font be used, consider adding a note to the front matter. Instruct the user to select the 'Publisher Default' font option."* ([kobolabs/epub-spec](https://github.com/kobolabs/epub-spec/blob/master/README.md)).
4. **Fallback escape hatch:** if you can't rely on embeds, tell users to pick **Georgia**, which *"correctly renders the greatest set of scripts"* ([kobolabs/epub-spec](https://github.com/kobolabs/epub-spec/blob/master/README.md)).
5. **Use TTF/OTF/WOFF1 — never WOFF2** (Kobo ignores WOFF2; matches our prior Ge'ez-tofu fix). Our all-TTF faces are correct.

A caveat that bites scripture publishers specifically: the kepub fallback is **name-driven, not coverage-driven** — *"the reader does have serif fonts for Chinese, however it won't use the CJK serif fonts when the book asks for `font-family: serif;`"* ([kobopatch-patches #115](https://github.com/pgaskin/kobopatch-patches/issues/115)). That directly indicts our `.vnote-greek-nt` (no family → generic serif → no Greek fallback) and `.vnote-arabic` (no family, no embed).

### Q3. Is "Publisher Default" the only path, or is there a per-script CSS / `lang=` / `@font-face` technique Kobo honours?

**"Publisher Default" is the only *guaranteed* path; `!important` on the element is the best author-CSS attempt; `lang=`/`:lang()`/`unicode-range` buy nothing extra on Kobo.**

- **`lang` / `xml:lang` / `:lang(he)` as a font trigger: NO.** The CSS Working Group is explicit: *"The `lang` attribute itself does not trigger font selection — CSS rules must explicitly apply different fonts based on language context"* ([w3c/csswg-drafts #1744](https://github.com/w3c/csswg-drafts/issues/1744)). A `:lang(he){font-family:…}` rule is just an ordinary `font-family` rule with a fancy selector — *functionally identical to our existing `.vnote-hebrew` class* and subject to the same override. DAISY confirms `lang`/`xml:lang` are *"accessibility and text-to-speech purposes only — not font selection or visual rendering"* ([DAISY language KB](https://kb.daisy.org/publishing/docs/epub/language.html)). Kobo's spec never mentions `lang`/`:lang` for fonts ([kobolabs/epub-spec](https://github.com/kobolabs/epub-spec)). **So setting `xml:lang` is good a11y hygiene but will NOT fix the tofu.**
- **`@font-face` + `unicode-range` as a routing mechanism: NOT honoured by Kobo as a feature.** Kobo's spec documents no `unicode-range` descriptor. Our Ethiopic `@font-face` works *only because Ge'ez codepoints exist in no other font in the stack, so that `@font-face` is the sole glyph source* — i.e. it behaves as a plain `@font-face`, not because Kobo routes by codepoint. The same pattern would **not** rescue Arabic, which has no embedded face at all ([w3c/csswg-drafts #1744](https://github.com/w3c/csswg-drafts/issues/1744); [kobolabs/epub-spec](https://github.com/kobolabs/epub-spec); [MobileRead t=346747](https://www.mobileread.com/forums/showthread.php?t=346747) — boxes even with the full font embedded when it isn't the active face).
- **Specificity / `!important`: see Q1** — the only author-CSS lever, with the firmware-origin caveat; device-test is the arbiter.
- **Standard `.epub` vs `.kepub` differ:** standard EPUB (Adobe RMSDK) injects the looser `body, p { font-family: -ua-default !important; }` (so some per-element fonts survive); kepub injects the universal `*{…!important}` (nothing escapes). We ship **kepub** to Kobo → the *stricter* path. Don't be misled by a standalone `.epub` that renders Hebrew correctly — that is the RMSDK engine, not the kepub the user actually reads ([t=271836](https://www.mobileread.com/forums/showthread.php?t=271836), [t=365692](https://www.mobileread.com/forums/showthread.php?t=365692)).

## Root cause

The precise mechanism for OUR failure:

1. The user has selected **"Cardo" as his reading font** in the Kobo Aa menu. This makes the kepub renderer inject `* { font-family: Cardo !important; }` (the device's notion of "Cardo", or whichever face the firmware maps that menu choice to — **not** the book's embedded `@font-face` Cardo).
2. Our `.vnote-hebrew { font-family: "Cardo", …; }` carries **no `!important`**, so it sits in the lowest author tier and is unconditionally overridden by the injected universal rule. The Hebrew run is therefore rendered by **whatever face the firmware resolved the Aa "Cardo" selection to**, not by our embedded Cardo TTF.
3. If that firmware-resolved face lacks pointed-Hebrew coverage (and Kobo does **not** do per-glyph fallback to the book's embedded Cardo for it), the Hebrew run gets no covering glyph → **tofu boxes**. The body stack having dropped Cardo + `!important` (so the reader font wins) is exactly what *enables* this override to reach the popups.
4. **Additionally / independently**, the same defect appears in Kobo's native **footnote-PREVIEW overlay**, which renders with the reader's font and ignores the book's `@font-face` entirely (documented in `LICENSES.md:102-109`, device-QA K-R2-3). No stylesheet `!important` reaches that overlay because the overlay is not styled by our CSS — this is the part only the sideload pack / "Publisher Default" can address.

So: **two stacked failures** — (a) in-flow popup text loses Cardo to the universal override (CSS-addressable via `!important`, modulo the firmware-origin caveat), and (b) the preview overlay always uses the reader font (not CSS-addressable; needs Publisher Default + the font pack). Cardo's coverage is fine throughout; coverage is not the problem.

## Recommended fix (for WIN)

A minimal, device-testable change in three parts. Do **all three** — they are complementary, not alternatives.

### (1) Fonts to embed

- **Hebrew + Greek:** keep **Cardo** (already embedded, OFL 1.1, covers Latin + polytonic Greek + pointed Hebrew). No new Hebrew/Greek font needed — coverage was never the issue. *(If a future device-test ever shows Cardo's Hebrew specifically failing even under Publisher Default, the canonical scholarly fallback is **SBL Hebrew** / **SBL Greek** — free for non-commercial use — but do not add them now; Cardo is sufficient and already shipping.)*
- **Arabic:** **embed `Noto Naskh Arabic`** (`NotoNaskhArabic-Regular.ttf`, already on disk at `content/assets/fonts/`, OFL 1.1, Naskh = the book-typography Arabic register). Why: Arabic currently has **no in-book coverage at all** → guaranteed tofu independent of the override. This is the only script whose fix requires a new embed. Copy the binary into `epub_working/fonts/` so the build's copytree ships it.

### (2) Exact CSS to add

Add `!important` to every original-language `font-family`, give `.vnote-greek-nt` an explicit Cardo stack, correct `.vnote-geez`/`.vnote-amharic` to the **embedded** family name, and add the Arabic `@font-face` + family. Copy-pasteable:

```css
/* --- NEW @font-face: Arabic (add next to the existing Cardo/Ethiopic blocks
       in epub_working/stylesheet.css, ~line 50). TTF, no unicode-range needed
       (Arabic block is disjoint from every other embedded face). --- */
@font-face {
  font-family: "Noto Naskh Arabic";
  src: url("fonts/NotoNaskhArabic-Regular.ttf");
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}

/* --- Original-language vnote font-family rules: add !important so the rule
       out-ranks Kobo's injected `* { font-family: <userfont> !important; }`
       (the only author-CSS lever; see brief Q1). Keep every other property
       byte-identical to avoid collateral diff. --- */
.vnote-hebrew {
  font-family: "Cardo", "SBL Hebrew", "Ezra SIL", "Frank Ruehl CLM", "Times New Roman", serif !important;
}
.vnote-greek {
  font-family: "Cardo", "SBL Greek", "GFS Didot", "Times New Roman", serif !important;
}
/* Greek NT currently has NO font-family — give it the Cardo stack explicitly
   so it does not inherit the body serif (Kobo won't fall back serif->Greek). */
.vnote-greek-nt {
  font-family: "Cardo", "SBL Greek", "GFS Didot", "Times New Roman", serif !important;
}
/* Ge'ez/Amharic: name the EMBEDDED family ("Noto Serif Ethiopic"),
   NOT the never-shipped "Noto Sans Ethiopic". */
.vnote-geez,
.vnote-amharic {
  font-family: "Noto Serif Ethiopic", "Abyssinica SIL", "Nyala", serif !important;
}
/* Arabic: currently has NO font-family anywhere. Name the new embed. */
.vnote-arabic {
  font-family: "Noto Naskh Arabic", "Amiri", "Scheherazade New", serif !important;
}
```

Implementation placement notes for WIN:
- The Hebrew/Greek/Greek-NT/Arabic rules can live in the **base** `epub_working/stylesheet.css` (so all targets benefit, not just eink — see byte-stability note below). The existing eink `.vnote-arabic` chrome rule in `_EINK_READER_CSS` (`build_edition.py:2397-2399`) stays as-is (it only adds borders/spacing, no `font-family`), so the base `.vnote-arabic { font-family … }` is additive and won't conflict.
- Do **not** revive `apply_style.py`'s stale `.vnote-geez` block — author the corrected rule directly in the base sheet, consistent with the existing hand-authored region (`stylesheet.css:10-11` note).

### (3) OPF / manifest changes

Add `Noto Naskh Arabic` to `EMBED_FONT_PATHS` in `scripts/style_config.py:94-113` (the list-of-dicts schema; **no `unicode_range` key** — Arabic's block is disjoint so it needs no scoping):

```python
{"path": "fonts/NotoNaskhArabic-Regular.ttf", "family": "Noto Naskh Arabic", "weight": "normal", "style": "normal"},
```

`patch_opf_fonts()` (`build_edition.py:6802-6854`) then auto-emits `<item id="font-noto-naskh-arabic-regular" href="fonts/NotoNaskhArabic-Regular.ttf" media-type="font/ttf"/>` before `</manifest>` — no other OPF edit needed. Update `content/assets/fonts/LICENSES.md` to move the Arabic entry from "font-pack only" to "embedded" (it is already OFL-cleared at lines 116-135).

### (4) `lang` / `xml:lang` attributes

**Not required for the font fix** — `lang` does not trigger font selection (Q1/Q3). The existing `lang="he"/"grc"/"ar"` + inline `dir="rtl"` are correct and sufficient for rendering. *Optional a11y/strict-XML polish (do separately, not as part of this fix):* also emit `xml:lang` alongside `lang` in `generate_verse_popups.py:45-49` (XML processors read `xml:lang`; if both present `xml:lang` wins). This is cosmetic for fonts — do not let it gate the font fix.

### (5) Front-matter "Publisher Default" instruction page — REQUIRED

Add a short front-matter page (or a line in the existing front-matter/about page) for **eink/Kobo targets** instructing the reader: *"For correct Hebrew, Greek, and Arabic display, open the font menu (Aa) and select **Publisher Default**. If you prefer your own reading font, install the YHWH font pack onto your Kobo's `fonts/` folder."* This is Kobo's officially documented and **only guaranteed** mechanism to suppress the override, and it is also the only thing that fixes the native footnote-**preview** overlay (which no stylesheet can reach). Gate it to eink so the 9 KJV byte-stable editions on other targets are untouched (see below).

### eink-only vs all-targets + byte-stability implication

**CRITICAL constraint:** the 9 KJV editions must stay **byte-stable** (regression gate). The font-family `!important` edits change the **base stylesheet**, which is shared across all editions/targets. Therefore:

- **The `!important` + Arabic `font-family` + corrected Ge'ez-family CSS** is safe to apply to the **base sheet (all targets)** **only if** the original-language popups do not appear in the 9 KJV editions' output (KJV is English-only; the `.vnote-hebrew/greek/arabic/geez` classes should not be present in KJV piece HTML). **WIN must verify this with the byte-stability gate**: regenerate all editions and `git diff` the 9 KJV outputs. If KJV output is unchanged → ship in the base sheet. If any KJV byte changes (e.g. the CSS text itself ships in the KJV stylesheet) → **gate the new rules to eink** via `_EINK_READER_CSS` (and/or the non-KJV editions) so KJV bytes are frozen. The `!important` additions to *rule text that already ships in KJV's CSS* would themselves change KJV bytes even if no element uses them — so the safe default is: **append the original-language `!important`/family rules and the Arabic `@font-face` via the eink/non-KJV path, not the universally-shipped base sheet**, unless the diff proves KJV is untouched.
- The **front-matter Publisher Default page** must be **eink-only** (don't add front-matter to KJV/tablet/kindle outputs that don't have the override problem and are byte-gated).
- Prove zero-change on KJV via regen + `git diff` (the project's standing "matrix == build" / byte-stability invariant). The Arabic embed adds a new OPF item + a new font file: `patch_opf_fonts` iterates `EMBED_FONT_PATHS` for *every* edition (verified `build_edition.py:6820`), so adding Arabic to that global list **will** add the OPF item + ship the font to KJV too → that **breaks KJV byte-stability**. **Mitigation — the recommended default is (b), the GATED path** (revised per the adversarial review below): either (a) accept that all editions now carry the Arabic font (re-baseline the byte gate with explicit, recorded WIN sign-off), or **(b) gate the Arabic embed *and* the `!important`/family rule additions to the editions that actually emit those vnote classes** (eink/non-KJV), leaving the KJV regression baseline untouched. **Why (b) is the default, not (a):** there is **no automated golden-hash gate protecting the 9 KJV** — `test_byte_stability_gate.py` only proves build *determinism* on 3 representatives (ethiopian-tewahedo / catholic-study / evangelical-reformed), and KJV identity is held *"by construction"* vs the v0.1.0 baseline (`b5ad8c98`, CHANGELOG). So the **only** thing that catches a KJV regression from this work is the **manual regen + `git diff` over *all* editions** — making the lower-risk, doctrine-aligned move the gated path that never touches the KJV baseline. Re-baselining is acceptable only with explicit sign-off recorded in the gate.

### Ranked fallback options if the primary doesn't survive device-test

1. **Publisher Default front-matter instruction (already in the fix) becomes the primary** — if `!important` does *not* rescue in-flow Hebrew on-device (firmware injects user-origin), this is the guaranteed lever. Make the instruction prominent.
2. **Sideloaded `yhwh-kobo-font-pack.zip`** (already exists; Cardo ×3 + Noto Serif Ethiopic + Noto Naskh Arabic into the Kobo `/fonts` root, reboot) — the belt-and-suspenders fallback that also fixes the preview overlay. Keep shipping it; document it in the same front-matter note.
3. **Instruct users to pick "Georgia"** (renders the most scripts) as a no-sideload fallback for users who won't touch Publisher Default ([kobolabs/epub-spec](https://github.com/kobolabs/epub-spec)).
4. **SVG-render the original-language runs** — GeoffR's bulletproof-but-heavy workaround (inline SVG sized `height:1em;width:auto`, immune to the font override). Impractical for whole-verse Hebrew/Greek; last resort only ([t=271836](https://www.mobileread.com/forums/showthread.php?t=271836)).
5. **Firmware patch** (`Un-Force user font-family in KePubs`) — not shippable in the EPUB (the *user* must patch their device); document it as an advanced option only.

## Device-test plan

For WIN, on the **real color Kobo**:

1. **Build target.** Build a **non-KJV edition that contains original-language popups** (e.g. `ethiopian-en` or whichever ships `.vnote-hebrew`/`.vnote-greek`/`.vnote-arabic`), with `target_reader=eink`, packaging `kepub.epub`. Confirm the build produced the kepub via the `kobo` matrix cell (`build_edition.py:2048-2057`).
2. **kepubify.** Confirm the artifact is the kepubified `.kepub.epub` (kepubify v4.0.4, `build_format_matrix.py:198-202`). Verify the embedded fonts are present in the zip (`fonts/Cardo-*.ttf`, `fonts/NotoSerifEthiopic-Regular.ttf`, **`fonts/NotoNaskhArabic-Regular.ttf`**) and the OPF has all font `<item>`s.
3. **Sideload & open** on the Kobo. Navigate to a verse with a Hebrew popup (and one with Greek, Greek-NT, Arabic, Ge'ez).
4. **A/B against the user's reading font — this is the decisive test:**
   - **Set the Aa font to "Cardo" (the user's setting)** → open the Hebrew popup. **Look for:** does Hebrew render as real pointed glyphs, or boxes? (Test both the in-flow expanded note *and* the native footnote-preview overlay separately — they can differ.) This tells you whether the `!important` change defeated the universal override on in-flow text.
   - **Set the Aa font to "Publisher Default"** → re-open the same popups. Hebrew/Greek/Arabic should all render correctly here (embedded faces honoured). If they do NOT even under Publisher Default, the problem is embedding/format, not the override — re-check OPF items + that the files are TTF (not WOFF2).
   - **Set the Aa font to "Georgia"** → sanity-check the documented "renders most scripts" fallback.
5. **Per-script checklist of what to look for:** Hebrew with vowel-points (not just consonants), polytonic Greek accents/breathings, **Greek-NT** (the class that previously had no font-family — confirm it now matches Greek, not a boxy serif), Arabic (contextual joined forms, RTL order — confirm the new embed works at all), Ge'ez fidel (confirm the corrected family name didn't regress the body Ge'ez).
6. **Record** which Aa setting yields correct Hebrew. The verdict on Q1 (does author `!important` beat the kepub override on this firmware?) comes **only** from step 4's "Cardo" case — document it in `dev/audit/` for both lanes.
7. **Byte-stability gate** (off-device, before/with the build): regenerate all editions, `git diff` the 9 KJV outputs, confirm frozen (or re-baseline with explicit sign-off per the eink-gating decision above).

## Confidence & open questions

**Well-supported by sources (high confidence):**
- The override mechanism `* { font-family: <userfont> !important; }` and that it fires only for *named* fonts, not "Publisher Default" — verbatim from firmware patch source + multiple MobileRead expert threads + Kobo's official spec.
- A plain author rule (no `!important`) is always clobbered — multiple independent sources.
- `lang`/`:lang()`/`unicode-range` do not give Kobo a font-routing capability beyond a plain `font-family` — W3C CSSWG, DAISY, Kobo spec.
- Kobo's fallback is name-driven and won't go from generic `serif` to a non-Latin face — kepubify issue #115; so `.vnote-greek-nt` (no family) and `.vnote-arabic` (no family, no embed) are genuine in-book bugs regardless of the override.
- WOFF2 unsupported / TTF correct; "Publisher Default" + front-matter note is Kobo's official mitigation; sideload `/fonts` is the supported user-font channel — Kobo spec + help docs.
- The footnote-**preview** overlay always uses the reader font and is not stylesheet-addressable — Kobo behavior + our own device-QA K-R2-3.

**Needs the real-device test to confirm (the one genuine open question):**
- **Does author `.class { font-family: … !important }` actually beat the kepub override on the user's firmware?** The sources split: if libnickel injects user-origin, *no* author `!important` wins and only Publisher Default works (Angles 1-2's conservative reading); if author-origin, `.vnote-hebrew{…!important}` wins (Angle 4's reading, with practitioner reports). **Only the step-4 "Cardo" A/B on the real Kobo settles this.** Either way the recommended fix is correct: `!important` is free and is the best author lever, and the Publisher-Default front-matter + font pack are the guaranteed backstops. Ship all of them; let the device test tell us whether the in-flow `!important` alone is enough or whether the user must select Publisher Default.

## Adversarial review (Mac, 2026-06-24) — verdict + corrections folded in

An independent skeptic pass (workflow `wf_4a06fb2b-cc8`) re-checked every load-bearing claim against the
repo. **Verdict: recommendationSound = true** (ship all three parts), **confidence = LOW *without the
device test*** (the in-flow `!important`-vs-override question is genuinely undecided by sources — see Q1).
The fix is correct to ship regardless, because `!important` is free + the best author lever, and Publisher
Default + the font pack are the guaranteed backstops.

**Verified against the repo (no flaws — these strengthen the brief):**
- `patch_opf_fonts()` (`build_edition.py:6820`) extends from `EMBED_FONT_PATHS` and patches the OPF for
  **every** edition with no per-edition gating → a global Arabic add ships the 285 KB font + `<item>` to the
  9 KJV editions. (Drives the gated-path recommendation above.)
- `test_byte_stability_gate.py` is a **determinism** test on 3 representatives (ethiopian / catholic-study /
  evangelical-reformed), **not** a golden-hash freeze of the 9 KJV. **No automated test catches a KJV byte
  change from this work** — the manual `regen + git diff epub_working` over *all* editions is the *only* catch
  and is therefore **mandatory**, not optional.
- The **dominant byte risk is the `!important` edit to the shared base `stylesheet.css`** (copied verbatim into
  every edition at `build_edition.py:7487`): even though KJV emits no Hebrew/Greek elements, changing the rule
  *text* alters KJV's `stylesheet.css` bytes → breaks the "by construction" identity. This is *the* reason the
  rule additions must take the eink/non-KJV path, not just the Arabic embed.
- `lang=` (no `xml:lang`) is emitted at `generate_verse_popups.py:47`; the fix correctly does **not** require
  `xml:lang` (lang/`:lang()` don't trigger font selection on Kobo) → the missing-emitter gap does **not** block
  the fix.
- `arabic` + `greek-nt` are **live today** (`popup_versions.py` `_BAKED_NOW` + `DEFAULT_POPUP_WITNESSES`) → the
  Arabic-tofu and greek-nt-no-font bugs are **real and shipping**, not hypothetical.
- `Noto Naskh Arabic` is on disk (`NotoNaskhArabic-Regular.ttf`, 291,980 B, OFL 1.1), Naskh = correct book
  register, embeddable. Cardo (OFL 1.1) genuinely covers pointed Hebrew + polytonic Greek. No legality/coverage gap.
- `unicode-range` is **not** a Kobo font-routing feature; Arabic needs no `unicode_range` key (its block is
  disjoint from every embedded face) — the brief relies on the `@font-face` being the sole glyph source, correctly.

**Corrections folded into the brief (WIN, do these):**
1. **Prefer the GATED path (eink/non-KJV) over re-baselining** — done above; re-baseline only with recorded sign-off.
2. **State plainly: no automated KJV golden gate exists** → manual regen+`git diff` over *all* editions is the
   only safety net for this change. Done above.
3. **Headline byte risk = the shared-stylesheet rule-text change**, not just the Arabic OPF item. Done above.
4. **Device A/B is a HARD gate** before declaring the in-flow `!important` fix done (Q1 is only settled on-device).
5. **Confirm the Arabic font copy-step** — `NotoNaskhArabic-Regular.ttf` lives in `content/assets/fonts/`; it must
   be copied into `epub_working/fonts/` so the build copytree ships it (the `@font-face url("fonts/…")` resolves).

— End of brief. File: `dev/audit/kobo-font-override-research.md`. Adversarial review: `wf_4a06fb2b-cc8`.
