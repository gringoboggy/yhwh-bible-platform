# W1 contingency — the AB① explicit-height recipe, pre-verified (Mac, turn 57, backlog #3)

_Fires ONLY IF the user's Apple Books re-test still shows AB① (title boxes pushing to the next
page) on the post-`d60e5eec` rebuild. If the re-test passes, archive this note unused.
Geometry pre-verified in Chrome headless (rig: 400×1600 portrait art, 1170×1560 viewport)._

## Why this might fire

The shipped AB① fix (`2030e7e0` + `d60e5eec` caps) is `max-height: 20em; max-height: 42vh;`
(+ object-fit). The review (W1, confirmed HIGH) flagged: `object-fit` only scales content
*within* the box — it cannot constrain the box. If Apple Books ignores `max-height` on a bare
`<img>` entirely (the documented root cause of AB① itself), nothing constrains the box and the
art still renders intrinsic-height. The project's own research (`2026-06-05-eink-epub-compat-research.md`
≈:477) prescribes **explicit `height` + object-fit** for Apple. The device is the oracle.

## The swap (property change only — same values, same em→vh order, same kepub re-caps)

`epub_working/stylesheet.css` — 4 rules, each `max-height` → `height`, **and DELETE the
`height: auto` declaration** (it would override the explicit height; verified in the rig):

| line | rule | shipped | contingency |
|---|---|---|---|
| :572 | `.bookpage-art` | `max-height: 20em; max-height: 42vh; width: auto; height: auto;` | `height: 20em; height: 42vh; width: auto;` |
| :581 | `.style-full-bleed .bookpage-art-bleed` | `max-height: 36em; max-height: 88vh; width: auto; height: auto;` | `height: 36em; height: 88vh; width: auto;` |
| :591 | `#book-inner .bookpage-art` | `max-height: 20em;` | `height: 20em;` |
| :592 | `#book-inner … .bookpage-art-bleed` | `max-height: 36em;` | `height: 36em;` |

Keep `object-fit: contain`, `max-width`, margins, radius/shadow exactly as-is.

## Pre-verification results (Chrome headless rig, 5 variants screenshotted + Pillow-measured)

1. **No regression where things already work:** candidate renders PIXEL-IDENTICAL to shipped
   in a compliant engine — bleed 344×1376 px (= the 88vh cap, aspect-true) both ways; framed
   164×656 (= 42vh) both ways.
2. **Degradation path (engine drops vh — the RMSDK/K③ case):** candidate-without-vh renders
   exactly **36em = 576 px tall, 144 px wide (aspect-true)** — the em explicit height applies,
   `width: auto` derives from it, contain never distorts.
3. **No letterbox in the common case:** with `width: auto` + explicit height, the box itself is
   aspect-true (paint == box) — `object-fit` only engages when `max-width` clamps very WIDE art,
   where contain letterboxes inside the box (invisible on the bleed variant; on the framed
   variant the shadow/radius would outline thin empty side-bands — same behaviour the shipped
   CSS already has in compliant engines, so no new visual cost).
4. **Mechanical trap caught:** leaving `height: auto` in place silently undoes the explicit
   height (cascade order) — the diff above removes it; a naive "swap max-height→height" that
   keeps `height: auto` ships a no-op.

## Pins to update in the same commit (assert the NEW shipped contract)

- `tests/test_presentation_polish.py:654` `"max-height: 42vh"` → `"height: 42vh"`; `:661`
  `"max-height: 88vh"` → `"height: 88vh"` (object-fit asserts at :656/:663 unchanged); refresh
  the `TestTitlePageArtFit` docstring (:645) to the explicit-height story.
- `tests/test_title_page_style.py:194-201` (em-before-vh ORDER pins): same property rename,
  ordering logic unchanged; `:207-210` (#book-inner em re-caps, `"vh" not in`): rename, and add
  `"height: auto" not in` to both rule pins — that's the trap-guard.

## Decision tree for the re-test

- AB① fixed by the shipped build → do nothing, archive this note.
- AB① persists → apply the table above verbatim (one commit: 4 CSS lines + the pins), rebuild,
  re-test. No HTML/base mutation, no OPF change, epubcheck-neutral (CSS property swap only).
- AB① persists even then → the remaining lever is dropping `break-inside: avoid` on
  `.book-title-frame` (stylesheet.css:544) so an over-tall frame paginates instead of pushing —
  visual cost (art may split from title); take only with the user's eyes on it.

— Mac, turn 57. Rig + screenshots: `/tmp/w1-test/` (ephemeral; measurements recorded above).
