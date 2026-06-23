# Platform research — Apple Books (Round 9)

**Status:** Research complete — M2 prep input.
**Date:** 2026-06-18 · **Lane:** mac · **Dim:** `platform-apple`

---

## 1. Our target UX (non-negotiables)

From `dev/EREADERS.md` §Apple + `docs/superpowers/notes/2026-06-15-apple-m2-layout-directive.md`:

- **Artifact:** plain `.epub` (no kepubify, no `kindle_post`).
- **`target_reader`:** `tablet` (FORMAT_MATRIX `apple` row).
- **Per verse, two tap targets only:**
  - Verse **start:** `vn-link` → translation popup (`vnote-{code}-{ch}-{v}`).
  - Verse **end:** **one** study badge with count → merged `verse-notes` popup (`vnotes-*-s1`).
- **Polish inside Apple's native footnote sheet only** — typography, RTL, cascade cards.
- **Do NOT port:** Kobo K-R9 study glossary backmatter, per-category eink badges, Kindle M4b marker suppress.
- **Gate:** user Apple device re-test; epubcheck 0/0/0/0; M2 backgrounds-off structure pass stays green.

---

## 2. Official format support

| Topic | Vendor says | Our build uses |
|---|---|---|
| EPUB version | EPUB 3.3 supported; backwards compatible with EPUB 3 ([Apple Books Asset Guide 5.3.1](https://help.apple.com/itc/booksassetguide/en.lproj/static.html)) | EPUB 3; epubcheck 0/0/0/0 on shipped v0.1.0 |
| Popup footnotes (`noteref`/`aside`) | `epub:type="noteref"` anchor + `epub:type="footnote"` aside; aside text hidden in body, shown in popup ([Asset Guide §Pop-up Footnotes](https://help.apple.com/itc/booksassetguide/en.lproj/static.html)) | `vn-link` noteref + `aside.verse-notes` / `vnote-*` — **device-proven M2-1 PASS** |
| Embedded fonts | Supported, BUT for flowing/FXL books you **MUST set `ibooks:specified-fonts`=`true`** in the OPF or Apple Books may substitute its own reading font ([Fonts Overview](https://help.apple.com/itc/booksassetguide/en.lproj/itc74d42b31e.html); syntax: [EPUBSecrets](https://epubsecrets.com/tag/embedded-fonts), [Guido Henkel](https://guidohenkel.com/2015/04/custom-fonts-in-ibooks/)) | `style_config.EMBED_FONT_PATHS` + `patch_opf_fonts` register Cardo/Noto Ethiopic in the manifest, **but `ibooks:specified-fonts` + the `ibooks:` package prefix are ABSENT** (0 hits on shipped v28a OPF) → **GAP, see §4 / R13-1** |
| Page-break CSS | Flowing books reflow; spine order drives pagination | `apply_file_split` title-page singleton pieces (works on all targets; beneficial on Apple) |
| Collapsible ToC (`<details>`) | `nav epub:type="toc"` required; nested `<ol>` supported | `reader_toc_expandable` opt-in via wizard `TARGET_CAPS.tablet.toc_expandable=true` — **live-verified round-6** |
| RTL / multi-script | `dir` on package; `writing-mode` on body/html; footnote RTL via wrapped `<p style="direction:rtl">` | Popup `lang` spans + embedded fonts; no tablet-specific fork |

**Sources (cite URLs):**

- [Apple Books Asset Guide 5.3.1](https://help.apple.com/itc/booksassetguide/en.lproj/static.html) — pop-up footnotes, fonts, navigation, EPUB 3.3
- [W3C EPUB 3.3](https://www.w3.org/TR/epub-33/) — structural semantics
- Internal: `docs/superpowers/notes/2026-06-10-target-caps-research.md`, `2026-06-09-M2-device-qa-results.md`

---

## 3. How others achieved similar goals

| Technique | Who / where | Applies to us? |
|---|---|---|
| Verse-end single badge + count → one merged study popup | Our M2 device QA (◈18 Gen 1:1) — pre-Kobo fork design | **Yes — keep as north star** |
| `noteref` + hidden `aside` footnote pattern | Apple Asset Guide canonical example | **Yes — already our emitter** |
| Per-category inline markers | Many print study Bibles | **No on Apple** — Kobo-only compromise |
| Study notes in backmatter glossary | Kobo K-R9c model | **No on Apple** — breaks M2 inline-badge UX |

---

## 4. Gap vs our pipeline

| Gap | `build_edition` / post-process / `TARGET_CAPS` | Severity |
|---|---|---|
| **R13-1: OPF omits `ibooks:specified-fonts`=true + `ibooks:` package prefix** → Apple Books (flowing/tablet) may ignore embedded Cardo / Noto Serif Ethiopic and render body+popups in its own reading font; Geʽez/Hebrew/Greek can fall to system fallback. Fonts ARE in the manifest, so the asset is there — only Apple's opt-in flag is missing. | `scripts/build_edition.py` `patch_opf` (L1634-1857) never injects it; base `content.opf` `<package>` L2 has no `ibooks:` prefix; confirmed absent on shipped v28a artifact (0 hits) | **medium** |
| Popup typography polish (cascade legibility inside sheet) | `apply_badge_markers` + popup HTML generators — no tablet-specific CSS pass yet | low (device QA cosmetic) |
| Title-page centering residual | Known open Kobo/Apple device-QA item; CSS already `text-align:center` — needs render-then-diagnose | low (deferred) |
| Kobo `.vn-sep` spans in translation popups | Emitted on all targets; harmless on Apple (hidden in aside until popup) | none |
| eink study backmatter / per-category badges | Correctly gated off when `target_reader != eink` (`resolve_reader_eink_study_layout` L2216) | none — **no bleed** |
| `TARGET_CAPS.tablet.max_popup_languages` | `null` (no cap) — Apple honors full apparatus | none |

---

## 5. Options ranked

### Option A (recommended)

- **Change:** Ship M2 column as **status quo** `target_reader=tablet` everywhere build + optional FORMAT_MATRIX `apple` row; polish popup CSS only (cascade spines, RTL `lang` spans, font sizes inside `aside`).
- **Files:** `scripts/build_edition.py` (badge emitters only if markup tweak needed), `epub_working/stylesheet.css` §4.1, `scripts/templates/wizard.py` TARGET_CAPS (already correct).
- **Device proof:** User Apple re-test on ethiopian-tewahedo navy `.epub`; Gen 1:1 badge tap + translation tap; backgrounds-off pass.
- **Risk:** Low — additive CSS only; 9 KJV byte-stable editions unaffected (tablet is separate matrix column).

### Option B

- **Change:** Add `reader_tablet_popup_compact` flag to trim cascade HTML density inside popups (shorter bylines) without changing marker geometry.
- **Files:** `scripts/build_edition.py` popup merge path, `scripts/core/popup_versions.py`.
- **Device proof:** A/B screenshot on iPhone Apple Books.
- **Risk:** Medium — could drop visible attribution if over-trimmed.

### Option C (decline / defer)

- **Change:** Port Kobo per-category badges or study glossary backmatter to tablet.
- **Decline:** Violates M2 layout directive; Apple popups work with inline badges; Kobo compromises are engine-specific.

---

## 6. Open questions for device QA

1. After v0.1.0 popup cascade ship — do long `verse-notes` popups scroll smoothly on iPhone vs iPad (sheet height)?
2. Geʽez/Arabic inside translation popups — does Apple honor embedded Noto vs system fallback without font-pack sideload?
3. Collapsible ToC on 83-book edition — any scroll performance regression on phone?
4. Title-page book name alignment — which element is off-center (needs screenshot pinpoint, not blind CSS)?

---

## 7. Recommended implementation plan

| Step | Owner | Blocks |
|---|---|---|
| Build ethiopian-tewahedo `--target-reader tablet` from FORMAT_MATRIX | Mac | None |
| epubcheck 0/0/0/0 + verify_kr2 gates on tablet artifact | Mac | Build |
| Optional: tablet-only popup CSS pass (typography) | Mac | User GO on screenshots |
| User Apple device QA (M2 checklist) | User | Artifact on Desktop |
| Attach to v0.1.x release / website apple column if distinct from everywhere | WIN | Device PASS |

---

## R13 ADDENDUM (2026-06-18, mac, independent angle = official feature matrix)

Prior brief treated embedded fonts as fully handled. They are not — the asset ships but
Apple's flowing-book opt-in flag is missing.

### R13-1 (medium) — add the iBooks font opt-in to the tablet OPF

Apple Books, for a **flowing** book, applies publisher-embedded fonts only when the OPF
declares `ibooks:specified-fonts`=`true`. Without it, Apple Books can substitute its own
reading font even though Cardo / Noto Serif Ethiopic are embedded and manifest-listed — so
Geʽez / Hebrew / Greek body + popup text may render in a system fallback on M2 device.

- **Ground truth (verified):** `patch_opf` (`scripts/build_edition.py` L1634-1857) injects
  rights / BISAC / WCAG-a11y / `dc:language` / `yhwh:target-reader` but never the iBooks
  property; `<package>` (`content.opf` L2, and the shipped v28a artifact) has no `ibooks:`
  prefix; `grep -rn "specified-fonts\|ibooks:" scripts/` = 0 hits.
- **Fix (Option A — tablet-scoped, byte-safe):** when
  `resolve_target_reader(edition) == "tablet"`, in `patch_opf`:
  1. add to the `<package>` element
     `prefix="ibooks: http://vocabulary.itunes.apple.com/rdf/ibooks/vocabulary-extensions-1.0/"`,
  2. inject `<meta property="ibooks:specified-fonts">true</meta>` into `<metadata>`.
  Additive + target-gated ⇒ the 9 byte-stable KJV editions and every non-tablet column stay
  byte-identical; other readers ignore the namespaced property; epubcheck stays 0/0/0/0
  (registered ibooks vocabulary).
- **Decline alternatives:** emitting it on ALL targets perturbs byte-stable KJV editions for no
  Apple gain (Option B); `com.apple.ibooks.display-options.xml` is for FXL platform flags, not
  flowing-font opt-in (Option C).
- **Device proof:** rebuild tablet ethiopian superset → Apple Books M2 → confirm body + a Geʽez
  popup render in Cardo / Noto Serif Ethiopic (not default serif).

### Re-confirmed CONFIRM-OPTIMAL (no new gap)

- Popup footnotes: `noteref`→`footnote` aside, matching `id`/`href`, same spine file, `xmlns:epub`
  on every `<html>` — exactly Apple's canonical example (`build_edition.py` L4224/4237).
- Page-break CSS: `h1,h2,h3 { page-break-before:always; page-break-after:avoid }` +
  `.toc-wrap details { page-break-inside:avoid }` — honored by Apple; the `.marker-badge`
  baseline-shift already avoids the documented iOS vertical-bar artifact.
- `<details>` ToC: tablet-gated via `TARGET_CAPS.tablet.toc_expandable:true`.
- `dc:language` multi-value block restored for all non-kindle targets (`build_edition.py` L1738).

---

## R13 ADDENDUM #2 (2026-06-18, mac, independent angle [2/2] = study-Bible layout precedents + M2 directive compliance)

Fresh-eyes pass on the SAME artifact, weighted to the layout directive's "polish inside the
native popup sheet" clause and to study-Bible cascade precedent. Finds that the prior brief
**under-rated** the popup-typography line (§4 "low cosmetic") and **mis-stated** the `.vn-sep`
line (§4 row 4: "harmless on Apple … hidden in aside until popup"). New vendor research changes
the verdict.

### Vendor ground truth (newly cited)

Apple Books applies its **own presentation layer** to the footnote popover and **ignores author
stylesheet CSS inside it** — corroborated across four independent sources:

- [Apple Asset Guide — Pop-up Footnotes](https://help.apple.com/itc/booksassetguide/en.lproj/itccf8ecf5c8.html):
  the only styling hook Apple documents for the popup is wrapping note text in
  `<p style="direction:rtl">` — an **inline** style, not a class rule.
- [publisha.org — Footnotes/Popup Notes](https://www.publisha.org/pages/footnotes/):
  "It is not possible currently to modify the style of the popup text in Apple iBooks."
- [Pigs, Gourds & Wikis — pop-up footnotes in EPUB 3/iBooks](http://pigsgourdsandwikis.blogspot.com/2012/05/creating-pop-up-footnotes-in-epub-3-and.html)
  and [99problems issue #14](https://github.com/dvschultz/99problems/issues/14): CSS is ignored
  in the pop-over; images and intra-popup hyperlinks do not render inside the sheet.

What DOES survive in the popover: block `<p>`/`<div>` flow and **inline** elements
(`<strong>`, `<em>`, `<small>`, `<sup>`, U+2028 line separators, the `vn-sep` bullet glyphs).
What does NOT: any rule keyed on a class (`.vn-cat-head` small-caps + bottom-border,
`.vn-group` colored `border-left` category spines, `.vn-source-byline` italic via class,
`.vn-item` indents/tints, `note_popup_style=category-color` borders).

### R13-2 (medium) — the tablet cascade hierarchy is delivered by CSS classes Apple's popup discards

`apply_note_cascade_css` (`build_edition.py` L2452-2467) and `_note_popup_category_color_css`
(L2184-2227, default for tablet via `resolve_note_popup_style` L2238) build the verse→category→
source→note hierarchy **entirely through stylesheet rules** on `.vn-cat-head` / `.vn-group` /
`.vn-source-byline` / `.vn-item`. Inside Apple's native popover those rules are inert, so the
merged `verse-notes` listing collapses to an undifferentiated text run — the exact opposite of the
M2 directive's "tinted cards, category cascade, borders/weight/indents" polish (directive
lines 38-46). The directive's plan is **structurally impossible** to deliver via classes on Apple.

- **Fix (additive, tablet-scoped):** carry the cascade hierarchy in **inline** markup the popover
  honors — category headers wrapped in `<strong>`/`<small>` with an inline `font-variant:small-caps`
  style attribute (or a literal small-caps glyph run), source bylines already use the inline
  `<strong>/<em>/<small>` triad (keep it), and per-item delimiters via the surviving U+2028 + bullet
  separators (see R13-3, which currently deletes them). No class-only cue should be load-bearing for
  comprehension on tablet. Gate behind `resolve_target_reader == "tablet"` so KJV byte-stability and
  other columns are untouched.
- **Device proof:** tap Gen 1:1 ◈ badge on Apple Books → confirm category/source boundaries are
  visible in the sheet without relying on color or borders (backgrounds-off parity).

### R13-3 (medium) — `apply_tablet_popup_strip_separators` removes the only in-popup structure cues Apple can render

`apply_tablet_popup_strip_separators` (`build_edition.py` L2701-2727, wired at L7717) **physically
deletes** every `<span class="vn-sep">…</span>` on tablet builds. Those spans carry the U+2028 line
break + the `¶` (category) / `◦` (source byline) / `•` (item) bullets (defined L2570-2572) — i.e.
the inline plain-text delimiters that, per the vendor research above, are the ONE structuring
mechanism that survives Apple's CSS-blind popover. The function's own docstring concedes "Tablet
targets apply author CSS inconsistently inside footnote sheets," then responds by removing the
inline cues instead of leaning on them — leaving the merged listing visually flat in the popup. The
prior brief's §4 row 4 ("harmless on Apple … hidden in aside until popup") is therefore wrong: on
tablet the spans are not merely hidden, they are stripped, and their removal is a comprehension
regression inside the popover. The strip was added to stop stray bullets leaking in *body* view
when `.vn-sep{display:none}` is applied inconsistently — a real but narrower problem.

- **Fix:** do NOT blanket-strip on tablet. Either (a) keep the separators and prevent body-view leak
  by making them structurally invisible in body (wrap in the already-hidden `aside`, which Apple
  hides natively via `epub:type="footnote"` — so no body leak exists for asides), or (b) replace the
  class-hidden `vn-sep` span with an inline-styled span (`<span style="display:none">` is itself a
  class-free hide, but Apple's popover ignores `display:none` too — so prefer keeping the visible
  glyph and only stripping the leading U+2028 if it doubles a line). Net: separators must reach the
  Apple popover. Pair with R13-2 (they are the same hierarchy-in-the-popup problem).
- **Sweep:** one strip site (L7717) + one regex (`_VN_SEP_SPAN_RE` L2698); `apply_vnote_preview_separators`
  (L2730) is the producer. Checked both producer and consumer; no other tablet strip site exists.

### R13-4 (info / CONFIRM-OPTIMAL) — verse-end single-badge + verse-start vn-link matches study-Bible precedent

The directive's geometry (translation `vn-link` at verse start → witness popup; ONE count badge at
verse end → merged study popup) is the digital analogue of the **end-of-verse reference cluster**
used by center-column/reference print study Bibles
([Thomas Nelson — Bible layouts](https://www.thomasnelsonbibles.com/blog/guide-for-different-types-of-bible-layouts/),
[Crossway — ESV reference Bibles](https://www.crossway.org/articles/a-guide-to-esv-reference-bibles/)):
references collapse to the verse tail where the reader expects them, and the digit count stands in
for the print superscript cluster. `apply_badge_markers` (L3856-3879, `split_cap=0` on tablet via
L3245) produces exactly one merged `vnotes-*-s1` badge per verse — precedent-aligned, no change
needed. This is the layout to KEEP; R13-2/R13-3 only fix what happens AFTER the tap.