# `reader_native_toc_chapters` nested-navPoint evaluation (board item 9)

**Mac, 2026-06-10. Verdict up front: the nesting machinery already exists and is structurally correct; the open question is purely how Kobo eInk RENDERS depth, and the prior empirical datum says "flattened endless scroll" — so chapter drill-down on the Kobo native ToC is LIKELY a dead end, pending one cheap round-5 device datum.**

## What exists (code audit)

`enrich_nav_chapters` (`scripts/build_edition.py:3732`) is already a REAL nested implementation, not flat append:
- nav.xhtml: a nested `<ol class="toc-nav-chapters">` INSIDE each book `<li>` (true EPUB3 nav depth).
- toc.ncx: child `<navPoint>`s appended inside each book's navPoint + a depth-first gapless `playOrder` renumber (NCX-spec-correct).
- Runs post-canon-filter, pre-splitter (hrefs remapped by `apply_file_split`); no-op safe; opt-in via `reader_native_toc_chapters` (default OFF since RX-beta2 ⑧).

So "needs a real nested-navPoint experiment" requires NO new build code — only flipping the flag on a test build.

## The empirical record

- **RX-beta2 ⑧ (2026-06-06, real Kobo):** with chapter enrichment ON, the Kobo native ToC became an "endless scroll" on long-chapter books → demoted to opt-in. That observation is the flattening datum: Kobo eInk shows nested entries inline (indented at best), with NO collapse/expand affordance.
- **K-R3-5 correction (turn 62):** the Azariah [+]/Read modal on r3 was Kobo's TITLE-OVERFLOW expander (58-char book name), NOT nav nesting — r3 nav/ncx are FLAT. No evidence Kobo eInk has a drill-down UI for nav depth.
- TARGET_CAPS research (2026-06-10): Kobo doesn't operate `<details>` either — so the in-book expandable Contents can't substitute on eInk.

## The cheap round-5 experiment (only if the user still wants the datum)

1. Flip `reader_native_toc_chapters: true` on **catholic-study** (small canon), build + kepubify (same recipe as the staged toc-qa EPUB; revert the yaml after).
2. Verify in-zip: nested `<ol>` in nav.xhtml under e.g. Psalms; ncx navPoint children + gapless playOrder; epubcheck 0/0/0/0 (NAV-011 clean — ordering contract already handled by the run-last-among-nav-passes rule).
3. User step (30 s): open the Kobo native ToC → find Psalms → record: (a) one entry or 150+? (b) indentation? (c) any expander/drill-in? Photo.

## Recommendation

Keep default OFF. If round-5 confirms flattening (expected): mark the Kobo eInk capability honestly in TARGET_CAPS-style copy ("native chapter drill-down: not supported by the device UI"); chapter access on Kobo stays the in-content per-book pill ToC. The option remains available for readers whose native ToC DOES tree (e.g. Apple Books renders nav depth as collapsible sections — tablet targets already get `<details>` Contents via `target_reader` anyway). No further build work warranted.
