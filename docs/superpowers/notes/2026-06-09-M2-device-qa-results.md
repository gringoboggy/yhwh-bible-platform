# M2 device-QA — results (Mac, turn 49, 2026-06-09)

_Run of `2026-06-09-M2-backgrounds-off-qa-matrix.md` against WIN's STAGE-C eth re-baseline
(`bf7ac846`). The eth EPUB was rebuilt locally on the Mac from committed source
(`build_edition.py ethiopian-tewahedo --force`, 25.81 MB — matches WIN's 25.85 MB ⇒
deterministic), unzipped, served, and rendered in Chrome with the enhancement layer stripped
(`* { background:none; background-color:transparent; border-radius:0; box-shadow:none }`) to
simulate Apple Night/Sepia + ADE/RMSDK + e-ink high-contrast._

## Verdict

**✅ The backgrounds-off cascade PASSES every self-serviceable structure + content cue — no
ship-blocking collapse.** With all fills/radii/shadows stripped, the verse→category→source→note
hierarchy still reads entirely from background-independent properties (border-left, weight,
small-caps, the spelled-out label text, italic bylines, indents). The tinted card fills are a
pure enhancement layer; nothing load-bearing depends on them.

**✅ The one finding is RESOLVED (WIN `3bab5f4a`, user GO'd "remove all 10")** — see the
"Finding" + "Post-purge re-verify" sections below. The seeded "Reference sample note (η.1)"
entries are purged; the apparatus is now entirely real, named-source material, and the v0.1.0
"nothing is invented" copy is honest.

The remaining checks (popup firing, pagination/legibility) are genuine device behaviours and
stay for the user's real-device pass (Apple Books + the colour Kobo).

## Evidence (backgrounds OFF)

> The render + computed-style table below were captured on the **pre-purge** build
> (Gen 1:1 = ◈18, 8 groups). The cascade **CSS and markup are unchanged** by the seed-note
> purge (the purge deleted note *content* only, not `_NOTE_CASCADE_CSS` / the emission logic),
> so the structure pass carries over verbatim; the **post-purge** counts (Gen 1:1 = ◈15,
> 6 groups) are re-verified in the section below.

Screenshot: `assets/2026-06-09-M2-gen1-1-backgrounds-off.png` — the **pre-purge** cascade with
the enhancement layer stripped (colored left-border spines, bold small-caps headers, italic
bylines, indented leaves all clearly visible). Note: the `hist` group's first byline visible in
this shot is the now-removed sample note (the finding); post-purge `hist` leads with the real
*Easton's Illustrated Bible Dictionary (1897)* byline. It is kept as the structure proof.

| check | cue | result | measured (computed style, backgrounds OFF) |
|---|---|---|---|
| **M2-2** | C1 category color | ✅ PASS | 8 groups, **8 distinct** `border-left: 3px solid` colors — hist `rgb(139,90,43)`=#8B5A2B, comm `#0B3D91`, xref `#5C2E91`, text `#A0202C`, lang `#8B6508`, apol `#2E5E3E`, ped `#6B5B4A`, topic `#5A5F7E`; every group `background-color: rgba(0,0,0,0)` after strip (no fill dependence) |
| **M2-3** | C2/C3 header + identity text | ✅ PASS | `.vn-cat-head` `font-weight:700`, `font-variant-caps:small-caps`, `border-bottom:1px solid`; text = **"⌂ Historical / Cultural"** — the category **words** follow the `aria-hidden` glyph, so identity survives a tofu glyph |
| **M2-4** | C4 source named once | ✅ PASS | `.vn-source-byline` `font-style:italic`, `font-weight:600`; one byline per source, not per leaf |
| **M2-5** | C5 cascade depth | ✅ PASS | `.vn-source` margin-left ≈11.05px, `.vn-source .vn-item` margin-left ≈7.9px — visible nesting without fills |
| **M2-6** | S1 label de-dup | ✅ PASS | lang group: 4 leaves carry the `Word.` kind-label **once**, not repeated per leaf |
| **M2-8** | S3a topic union | ✅ PASS | **one** topic group; byline cites both "Nave's Topical Bible, Orville J. Nave (1896) · Torrey…"; **no duplicate terms** |
| **M2-9** | category order | ✅ PASS | hist → comm → xref → text → lang → apol → ped → **topic (last)** — the fixed `_POPUP_CATEGORY_RANK` order |
| **M2-7** | comm-ethiopian byline | ✅ (WIN-verified) | WIN's re-baseline render-verify (a) confirmed the father byline renders in the body only, **no double-attribution** (BYLINE-1 fix live); not re-rendered here |

### Deferred to the user's real-device pass (device behaviours, not self-serviceable)
- **M2-1** popup fires — the cascade is delivered as a proper EPUB3 popup footnote
  (`aside epub:type="footnote"`, `id="vnotes-gen-1-1"`), hidden inline in a browser and popped
  on tap in the reader. Confirm it pops on Apple Books and that the kepub noterefs fire on Kobo.
- **M2-10** legibility — title-page bleed, Your-Edition table, justify/ToC, no empty pages: on
  glass, paginated. (The 5 STAGE-C findings ride along.)

## ✅ FINDING — RESOLVED (`3bab5f4a`) — was: seeded "sample" notes shipped in the eth Bible apparatus

> **RESOLVED 2026-06-09 (WIN `3bab5f4a`, user GO'd "remove all 10").** The 10 η.1 seed notes were
> purged from **both** places they lived — the live store `content/notes/gen.py` (10 tuples) **and
> the baked base** `epub_working/index_split_000.html` + `_001.html` (10 marker+aside pairs;
> surgical, not a re-bake → no drift regression). WIN's heads-up: because attribution is a
> build-time live lookup, removing only from `gen.py` would have left baked orphans — both cleaned.
> WIN-verified: base nested-anchor 0 + balanced, epubcheck 0/0/0/0, 175 tests green, no other
> placeholders anywhere. **The original finding is preserved below for the record; the post-purge
> re-verify is in the next section.**

**What:** `content/notes/gen.py` carries ~10–11 note entries whose **source/attribution field**
(the 7th tuple element) is the literal string _"Reference sample note (η.1) — clearly marked for
the empty category seeded so every symbol in the matrix has at least one displayable example."_
The note **bodies** are real, substantive content (e.g. Gen 1:1's "Ancient Near Eastern context.
Gen 1 shares structural features with the Babylonian *Enuma Elish*…"), but the **attribution** is
an explicit placeholder, not a named public-domain source.

**Where (gen.py lines):** 179, 190, 201, 2225, 2302, 7571, 8418, 14721, 24907, 24918 (+1). In the
built EPUB they surface on 5 Genesis verses, one per otherwise-empty category:
`gen-1-1` (hist), `gen-1-28` (modern), `gen-5-1` (vis), `gen-6-1` (compare), `gen-22-1` (liturgy).
They exist to give every category symbol ≥1 displayable example (for the legend/matrix/skin).

**Why it matters (potential honesty ship-blocker for v0.1.0):** the project's differentiator and
its public copy say the apparatus is entirely real, named-source material —
- the live About page ("calibrated-not-harmonized … from named public-domain sources"),
- the v0.1.0 release copy I just drafted, §(a)/(e) of `2026-06-09-stageF-outward-copy-draft.md`:
  _"The Bible text and all the study notes are real and drawn from named public-domain sources —
  nothing is invented for you."_

A reader opening Genesis 1:1 currently sees a "Reference sample note" byline in their study
Bible — invented attribution in Scripture's apparatus, which makes that honesty claim untrue.

**Recommendation (WIN's call — shared content):** **remove the seeded entries from `gen.py`
before the v0.1.0 cut.** The cost is only that 5 categories lose a Genesis demonstration note;
"every category has an example" is a legend/matrix concern that should be served by the legend
page (Addendum A) or a non-shipping preview, **not** by injecting sample content into the
canonical text. (Alternatives: gate them behind a non-shipping preview edition, or — least
preferred — keep them and soften the "nothing is invented" copy, which weakens the
differentiator.) If they are intentional and meant to stay, the §(a)/(e) outward copy and the
About page must be reconciled first.

## Post-purge re-verify (Mac, turn 51 — on the artifact the user will device-test)

Pulled WIN's `3bab5f4a`, rebuilt eth locally (`build/m2`, 25.81 MB) and re-checked the affected
verses on the **shipping** content:

- **Seeds gone:** `grep 'Reference sample note'` = **0** in `content/notes/gen.py` and **0** in the
  rebuilt EPUB. No `η.1` placeholders anywhere.
- **Gen 1:1 = ◈15** (was ◈18): **6** cascade groups — hist, comm, xref, text, lang, topic
  (15 `.vn-item` leaves). The sample-only `apol` + `ped` groups correctly vanished; `hist` now
  leads with the real **_Easton's Illustrated Bible Dictionary, M. G. Easton (1897)_** byline, not
  the sample. All real notes intact.
- **Sample-only verses now empty (expected):** `gen-5-1`, `gen-6-1`, `gen-22-1` have no notes block
  at all (their only note was the seed); `gen-1-28` dropped its `modern` group (kept xref + topic).
- **Structure unchanged:** the cascade `_NOTE_CASCADE_CSS` + emission logic are byte-identical, so
  the backgrounds-off PASS (C1–C6, the table above) holds verbatim on the post-purge build —
  re-confirmed the 6 groups carry distinct `note-cat-*` border-left classes, headers, bylines, and
  indents. The artifact at `build/m2/Ethiopian_Bible_…155343Z.epub` is the correct one to device-test.
- **Validated on the EXACT device-test artifact (turn 52, 2026-06-09):** `scripts/audit_epub_structure.py`
  → **0 critical** (DUP_NOTE_ROWS / DUP_IDS / BROKEN_NOTEREF / UNBALANCED_TAGS / NEAR_EMPTY all 0);
  **epubcheck 3.3** (openjdk 26) → **0 fatals / 0 errors / 0 warnings / 0 infos**. Footnote wiring intact:
  66,684 `epub:type="footnote"` + 66,498 `epub:type="noteref"` — the structure both Apple Books and the
  Kobo kepub popup engine key on. EPUB side-loaded to the Kobo (`YHWH-Ethiopian-Bible-M2-QA.epub`);
  the Kobo-native `.kepub.epub` (faithful M2-1 popup test) is being supplied by WIN (Mac lacks the
  pinned `kepubify` v4.0.4 — cross-lane parity).

## How to re-run (Mac)
```bash
.venv/bin/python scripts/build_edition.py ethiopian-tewahedo --force --output-dir build/m2
mkdir -p /tmp/u && unzip -oq build/m2/Ethiopian_Bible_*.epub -d /tmp/u
.venv/bin/python -m http.server 8753 --bind 127.0.0.1 &   # serve /tmp/u
# Playwright: navigate index_split_000_00.html → inject the background-strip <style>
# → getComputedStyle on #vnotes-gen-1-1 .vn-group / .vn-cat-head / .vn-source-byline
```

— Mac, turn 49. Self-serviceable M2 complete; device behaviours (M2-1, M2-10) + a user decision
on the seeded-notes finding remain.
