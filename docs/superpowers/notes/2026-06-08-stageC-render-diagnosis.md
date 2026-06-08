# Stage-C render-first diagnosis — finding 3 (title-page) + finding 2 (Your-Edition stats table)

**Status:** DIAGNOSIS for WIN (Stage C). Mac-led; WIN implements + verifies on-device. 2026-06-08.
**Inputs:** the user's 8 Apple-Books device screenshots (`~/Desktop/IMG_0167–0172,0176,0177`), the live `epub_working/index_split_000.html` title-page HTML, `epub_working/stylesheet.css`, and `scripts/matter_pages.py`.

## ⚠ Why a browser render is NOT the verification here (read first)
Both findings are **paginated-reader (Apple Books) behaviors that a scrolling desktop browser cannot reproduce**, so a Playwright/Chrome render would be misleading, not confirming:
- **Finding 3** is a *page-bleed* — a box spilling onto the **next page**. A browser scrolls continuously; it has no fixed-height "next page," so it physically cannot show the bleed.
- **Finding 2** renders *correctly* in a standards browser (`width:100%` is honored); the clip is an **Apple Books `table-layout:fixed` column-sizing quirk**. Chrome would show a clean table and hide the bug.

So this diagnosis is grounded in the **actual HTML/CSS + the device screenshot** (the real evidence), and the **verification gate is on-device Apple Books** with the rebuilt EPUB (WIN, Stage C). This is the opposite of a blind fix: each fix below names the ONE off element with a `file:line`.

---

## Finding 3 — book title-page "bleeds onto the next page" (it is NOT a misalignment)

**The reframe that ends the blind-fixing:** the title-page text **is already centered** — `.bookpage-eyebrow`, `.bookpage-title`, `.bookpage-subtitle`, `.bookpage-rule` all carry explicit `text-align:center` (`stylesheet.css:540-543`), added by RX-beta2 ⑩ (comment at `:535-539`) precisely to beat `body p{text-align:left}`. Re-centering does nothing because **horizontal alignment is already correct.** The actual defect is **vertical / pagination**: a bordered box that grows taller than one reader page and spills over.

**The ONE off element + mechanism.** The framed box is `.book-title-frame` (`stylesheet.css:529-534`):
```css
.book-title-frame { display: inline-block; margin: 0 auto; max-width: 92%;
                    border: 1px solid rgba(11,61,145,0.32); border-radius: 0.4em;
                    padding: 1.2em 0.9em 1.0em 0.9em; background: rgba(184,134,11,0.04); }
```
It holds eyebrow + subtitle + title + rule and, on books with a plate, `.bookpage-art` (`:549`):
```css
.bookpage-art { display: block; max-width: 58%; height: auto; margin: 0 auto 0.9em auto;
                border-radius: 0.3em; box-shadow: 0 2px 8px rgba(0,0,0,0.25); }
```
Two compounding causes:
1. **`.bookpage-art` is sized by `max-width:58%` with NO height cap.** A 2:3 portrait plate's height = `0.58 × column-width × 1.5`, which on a phone column is ~300px+ before any text — so the framed box is already tall, and at larger reader fonts the text block grows on top of it. (Genesis carries no plate — `index_split_000.html:2326-2333` is eyebrow/subtitle/title/rule only — so the bleed is worst on books WITH a per-book art plate, matching the user's "title/picture" wording.)
2. **`.book-title-frame` is `display:inline-block` with no `break-inside:avoid`.** An inline-block box cannot paginate; when its height exceeds one reader page the bordered/filled box visibly continues onto the next page.

**Exact CSS fix (WIN — gated builder CSS append or base sheet; byte-stability per the note-rehaul spec §6):**
1. **Cap the art by viewport HEIGHT so it can never dominate a page** (the primary fix):
   ```css
   .bookpage-art { max-width: 58%; max-height: 42vh; width: auto; height: auto; }
   /* full-bleed variant too, so even edge-to-edge art stays on its own page: */
   .book-title-page.style-full-bleed .bookpage-art-bleed { max-height: 88vh; width: auto; }
   ```
2. **Make the frame paginate cleanly** (structural; helps the no-art books and is the durable guard):
   ```css
   .book-title-frame { display: block; break-inside: avoid; page-break-inside: avoid; }
   ```
   (`display:block` keeps centering via the parent `.book-title-page{text-align:center}` + the frame's own `margin:0 auto; max-width:92%`, and a block honors `break-inside` far better than an inline-block. `break-inside:avoid` is a hint a reader may ignore if the box still can't fit — which is exactly why the art **height cap** in step 1 is the load-bearing change.)
3. Optional, do NOT re-center anything (it is already centered; touching alignment is the failed path).

**Verify (WIN, Stage C):** rebuild eth, open on **Apple Books** at the largest 2–3 font steps, on a book **with** a per-book art plate (e.g. one of the `content/covers/_book_defaults/*` books). Confirm the framed box stays within one page. (A browser cannot show this — paginate-only bug.)

---

## Finding 2 — "Your-Edition" per-book table: book-name column clipped off the LEFT edge

**Evidence (IMG_0177).** The per-book note-count table renders with every book name clipped on its **left** ("Genesis"→"nesis", "Deuteronomy"→"uteronomy", "Wisdom of Sirach…"→"n of Sirach…", "Gospel … to Matthew"→"o Matthew"), the right-aligned count column pinned at the right edge, and a large empty middle. The user perceived a "whole-page spreadsheet popup."

**What it actually is (clarify so WIN doesn't chase a phantom modal):** this is the **"Your Edition" EPUB front-matter PAGE** — the first content page after the cover — rendered by `render_your_edition_page` (`scripts/matter_pages.py:430-490`), CSS at `stylesheet.css:575-588`. It is a normal spine page reached by a tap/link, **not a popup/modal**. The only bug is the table overflow; the "full-page" feel is just that it is a page.

**The ONE off element + mechanism.** The render emits (`matter_pages.py:483-490`):
```html
<table class="your-edition-perbook">
  <thead><tr><th>Book</th><th>Notes</th></tr></thead>
  <tbody><tr><td class="ye-book">Genesis</td><td class="ye-count">4,903</td></tr> … </tbody>
</table>
```
with CSS (`stylesheet.css:581-587`):
```css
.your-edition-perbook { width: 100%; table-layout: fixed; … }
.your-edition-perbook th { text-align: left; … }            /* no width on either <th> */
.your-edition-perbook .ye-count { width: 4.5em; text-align: right; white-space: nowrap; }  /* width on a tbody <td> */
```
Standards fact: under **`table-layout: fixed`, column widths are taken from the FIRST ROW's cells (the `<th>`s) or a `<col>`/`<colgroup>` — widths set on later (tbody) rows are IGNORED.** Here neither `<th>` has a width and there is no `<colgroup>`, so fixed layout has **no definite column widths to honor**; Apple Books resolves the under-specified fixed table by reverting to a content-driven intrinsic width that exceeds the 100% viewport and renders the table wider than the screen — the name column overflows off the left while the right-aligned `.ye-count` stays at the right edge. (Chrome honors `width:100%` and renders it cleanly, which is why this is an Apple-Books fixed-layout edge case.)

**Exact fix — recommend (B); (A) is the minimal alternative.** Both eliminate the overflow regardless of the precise Apple-Books quirk:

- **(B) Reader-robust — drop the `<table>` for a float-based 2-column block** (Apple Books *and* e-ink mishandle `<table>` layout broadly; this matches the note-rehaul "reader-robust structure first" north star, and `float:right` is already used + proven in this EPUB at `.note-back`, `stylesheet.css:202`). In `render_your_edition_page` emit per row:
  ```html
  <p class="ye-row"><span class="ye-count">{n:,}</span><span class="ye-book">{title}</span></p>
  ```
  (count first in source so the float clears correctly), with CSS:
  ```css
  .your-edition-perbook { /* replaced by .ye-rows wrapper */ }
  .ye-row    { margin: 0.12em 0; line-height: 1.3; clear: both; font-size: 0.86em; }
  .ye-count  { float: right; width: 4.5em; text-align: right; color: #6E5840; white-space: nowrap; }
  .ye-book   { display: block; overflow-wrap: break-word; word-break: break-word; }
  ```
  No `table-layout` dependency → cannot overflow; degrades cleanly on e-ink. Keep the `Book / Notes` header as a styled `<p>`.

- **(A) Minimal — give fixed layout definite widths via `<colgroup>`** (keeps the `<table>`): emit `<colgroup><col class="ye-col-book"/><col class="ye-col-count"/></colgroup>` immediately after `<table …>`; add `.your-edition-perbook .ye-col-count{width:4.5em} .your-edition-perbook .ye-col-book{width:auto}`. (Equivalent: move the width onto the header — `.your-edition-perbook th:last-child{width:4.5em}`.) This gives `table-layout:fixed` the first-row widths it needs and keeps the name column on-screen.

**Verify (WIN, Stage C):** rebuild eth, open the "Your Edition" page on **Apple Books**; confirm names are fully visible left-aligned with counts at the right. Re-check on a `.kepub`/Kobo path too (the table quirk is reader-class-wide).

---

## Summary for WIN
| Finding | The ONE off element | Exact fix | Verify |
|---|---|---|---|
| 3 — title-page bleed (NOT alignment) | `.bookpage-art` no height cap (`stylesheet.css:549`) + `.book-title-frame` is `inline-block`/no `break-inside` (`:529`) | art `max-height:42vh`; frame `display:block` + `break-inside:avoid` | Apple Books, largest fonts, a book WITH art |
| 2 — Your-Edition table clipped left | `<table.your-edition-perbook>` fixed-layout with no first-row/`<colgroup>` widths (`matter_pages.py:486`, `stylesheet.css:581-587`) | (B) float-based `.ye-row` block, or (A) add `<colgroup>` widths | Apple Books + `.kepub`, "Your Edition" page |

Neither is an alignment problem; both are byte-stability-gated build-CSS/markup changes on the eth edition (9 KJV unaffected when the change is scoped to the eth build or shipped as a base-CSS fix that re-baselines all editions intentionally — WIN's call per the note-rehaul spec §6 byte-stability gate).
