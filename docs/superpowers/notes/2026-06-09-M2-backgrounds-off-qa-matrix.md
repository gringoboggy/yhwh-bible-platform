# M2 device-QA — backgrounds-off cascade QA matrix (Mac, turn 44 item 2)

_Mac lane, 2026-06-09. A mechanical, per-check device pass for verifying the S2 verse→category→source→note cascade stays **hierarchical + category-identifiable when CSS backgrounds and embedded fonts are stripped** — the reader-robust north star (rehaul spec §2 "cards must never be the sole cue" + §5 acceptance). Execute the moment WIN's STAGE-C EPUB lands; this is the M2 checklist so the run is fast._

## What "backgrounds-off" means and WHY it is the gate
The tinted per-category cards (`stylesheet.css:879-897`, `background:` fills) are an **enhancement layer only**. Many real readers strip them: Adobe RMSDK / ADE (the Kobo plain-`.epub` engine) drops `background` on note containers; Apple Books' Sepia/Night themes and "publisher styling off" re-ground cards; e-ink high-contrast modes flatten fills; missing-glyph fonts hide the category symbol. So the cascade's **survivable cues** must carry the whole hierarchy with every `background` / `background-color` / `border-radius` / `box-shadow` removed and with the category glyph font absent.

### The 6 survivable cues the cascade MUST carry without backgrounds (build_edition `_NOTE_CASCADE_CSS` + base spines)
| # | cue | CSS source | survivable property |
|---|---|---|---|
| C1 | category **color** | `.vn-group.note-cat-{cat}` border-left 3px solid {hue} | border (not background) |
| C2 | category **header** | `.vn-cat-head` font-weight:700 + small-caps + border-bottom hairline | weight + rule |
| C3 | category **identity (text)** | `.vn-cat-sym` glyph **+ the label text** in the same `<p>` | text always present |
| C4 | **source named once** | `.vn-source-byline` italic + weight:600 | italic + weight |
| C5 | **cascade depth** | `.vn-source` margin-left + `.vn-source .vn-item` margin-left | indent |
| C6 | leaf category (corroborating) | `.vn-item[class*="note-{cat}-"]` leaf border-left (base sheet) | border |

C1–C6 are the pass conditions. The tinted card fill (C-enh) is allowed to vanish; if anything **only** reads because of the card fill, that is a FAIL.

## Pre-flight — how to put each reader into a backgrounds-stripping state
| device / engine | how to strip backgrounds + fonts | notes |
|---|---|---|
| **Apple Books (iOS)** — primary | Themes → **Night** AND **Sepia** (each re-grounds cards); Aa → turn OFF "publisher font"; also test the **Original (white)** theme as the not-stripped control | Books honors `border-left` + weight; the theme re-grounds `background`, so cards flatten — exactly the test |
| **Kobo plain `.epub`** (ADE/RMSDK, e-ink) — secondary | load the non-kepub `.epub`; pick a reader font (overrides embedded); RMSDK drops note-container backgrounds by default | the truest backgrounds-off engine; the colour Kobo is the user's eyeball |
| **Kobo `.kepub.epub`** | load the kepub; same font override | also verify popups fire (kepubify converts noterefs) without over-popping (spec Addendum A device note) |
| **DevTools control (cheap pre-check, on the unzipped EPUB)** | serve the unzipped build via `python3 -m http.server`, open a chapter, in DevTools delete all `background`,`background-color`,`border-radius`,`box-shadow` declarations from the merged stylesheet | mirrors spec §5 test #2; do this FIRST to catch fails before touching a device |

## The QA matrix — run per device, on a KNOWN multi-category verse (Gen 1:1 = ◈16, ~8 categories)
| check | action | PASS | FAIL signature |
|---|---|---|---|
| **M2-1** open the badge | tap `◈N` on Gen 1:1 | a footnote/popup (Apple/kepub) or in-piece aside (ADE) opens with the merged listing | badge missing, or popup short rows vs the count |
| **M2-2** C1 category color | with theme stripping fills, look at each `section.vn-group` left edge | each category group shows a **colored left border**; **≥2 categories show *different* border colors** | all groups one color, or no border (only a card fill that's now gone) |
| **M2-3** C2/C3 category header | read each `.vn-cat-head` | bold small-caps header, with a hairline under it, **reading the category LABEL as words** (e.g. "Historical / Cultural") even if the glyph is tofu | header indistinguishable from body, or identity carried **only** by the glyph (gone when font missing) |
| **M2-4** C4 source byline | within a multi-source category (e.g. Linguistic = Strong's + paraphrase) | the source is named **once**, italic, above its notes; not repeated per note | byline repeated on every note, or absent where attribution exists |
| **M2-5** C5 cascade depth | scan indents | sources indent under the category header; notes indent under the source — visible **nesting** without backgrounds | flat list; no perceptible hierarchy once cards flatten |
| **M2-6** label de-dup (S1) | read the leaves under a Strong's/Hebrew group | the per-note "Hebrew." kind-label does **not** repeat on each leaf (the header carries it once); a **non-default** label (comm-ethiopian father name) **is** retained | repeated "Hebrew. … Hebrew. …", or a father's name wrongly dropped |
| **M2-7** comm-ethiopian byline | open a verse with comm-ethiopian notes | the father/source is shown (in the body), **not double-printed** as both a group byline AND in the body | the attribution appears twice |
| **M2-8** topic union (S3a) | open a verse with Nave's + Torrey topics | one topical block, terms unioned, both sources cited; no duplicate term | duplicate terms (HEAVEN, HEAVEN) or a source dropped |
| **M2-9** order | compare category order across several verses | categories in the fixed `_POPUP_CATEGORY_RANK` order every time, **topical LAST** | order varies verse to verse |
| **M2-10** legibility (the 5 STAGE-C findings ride along) | full read on the device | title-page bleed fixed, Your-Edition table fixed, justify/ToC OK, no empty pages | per the STAGE-C device-QA findings |

## Reporting
For each device × check: ✅ / ⚠ / ✗ with a screenshot ref. A single ✗ on **M2-2 / M2-3 / M2-5** (the structure cues) is **ship-blocking for v0.1.0** — it means the cascade collapses to a flat list when a reader strips backgrounds, defeating the north star. M2-6/7/8 fails are content-dedup regressions (also blocking). M2-4/9 are polish. File results into a `docs/superpowers/notes/2026-06-09-M2-device-qa-results.md` and route any code fix to WIN (Guard #6) with the cue # + `file:line` from `build_edition.py _NOTE_CASCADE_CSS` (`:1800-1815`) or `epub_working/stylesheet.css`.

— Mac, turn 44 item 2. Blocked-on: WIN's STAGE-C eth EPUB (post S3a + re-baseline). The structure cues here are exactly what the S2-review (item 1) verifies in source; M2 confirms them on glass.
