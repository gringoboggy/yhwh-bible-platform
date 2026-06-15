# Kobo round-7 device QA — findings (K-R7)

**Status:** INGESTED 2026-06-14 (WIN/Grok) — user round-7 report + 8 screenshots
(`C:\Users\bogda\OneDrive\Desktop\kobo_img\1.jpg` … `8.jpg`) on the
2026-06-14 QA kepub (`YHWH-Ethiopian-Bible-koboQA.kepub.epub` on `G:\`).
Artifact: `build/kobo-qa/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-14T191511Z.kepub.epub`
(ethiopian-tewahedo superset; chip badges; 7-way gen 1:1 split).

**HEADLINE:** Major popup progress — translation link + most gen 1:1 study units
now open. **M3 still blocked** by: (1) last-in-sequence / singleton-note decline,
(2) popup preview still run-on (U+2028 ineffective post-kepubify), (3) BOOK
eyebrow spacing (nbsp in markup insufficient under small-caps), (4) residual
page-break seams (chapters sharing a page).

## K-R7-1 ✅ PROGRESS — first note + gen 1:1 mostly working

- User: "the first note now works" — the `vn-link` translation popup (`vnote-gen-1-1`)
  opens (img 5-style Footnote preview with Hebrew/Greek/Latin).
- Gen 1:1: "all the notes work except the last one" (img 7: chip badges `1 1 4 1 4 3 1`
  on the verse line; seven split units `vbadge-gen-1-1-s1` … `s7` in artifact).
  **Last failing unit = `vnotes-gen-1-1-s7`** (1 note, part 7/7, 1,676 B serialized).
- Round-6 baseline was 1/3 on gen 1:1 (only `s2` popped). Round-7 = **6/7** — real
  improvement; the remaining failure is positional (last badge), not size-monotonic.

## K-R7-2 ⚠ OPEN — "last-note class": trailing badge + singleton 1/1 share one Kobo bug

- User (round 7): "the last still doesnt and therefore will not work half the time
  when it's just 1/1 single note or teleport on that note."
- User (follow-up, refined): **a singleton 1/1 is treated as a last note** — same
  failure mode: no popup, or teleport backwards. Not two separate bugs; one class.
- **Unified pattern:** any verse where the study badge is the **rightmost noteref
  on the line with nothing after it**:
  - Multi-part: gen 1:1 `vbadge-…-s7` (7th chip, rightmost on verse)
  - Singleton: gen 1:12/13/15/17/18/19 (`title="1 note"`, no part suffix — still
    `-s1` in id, but visually lone badge at verse end)
  - In artifact, inter-badge spaces exist (`badge = " ".join(unit_badges)`) but
    **no trailing anchor after the final badge** before `</p>`.
- Hypothesis: Kobo's noteref hit-test / forward-scan **declines or mis-resolves
  the terminal link** on the verse line (size is NOT the axis — `s7` is smallest
  but `s1`/`s2`/`s4` single-note parts in the same verse work because they are
  not terminal).
- **Fix direction (WIN, build_edition `apply_badge_markers`):** emit a trailing
  non-link anchor after the badge cluster — e.g. `<span class="badge-trail" 
  aria-hidden="true">\u00a0</span>` or ZWSP — so the terminal noteref is never
  the last box on the line. Rebuild + re-device.
- **Next device taps (USER, optional confirmation):** gen 1:1 s7 only (P/J/N) vs
  gen 1:12 singleton — expect identical failure shape if hypothesis holds.

## K-R7-3 ⚠ OPEN — popup preview formatting (run-on wall of text)

- User: "still no popup formatting so everything doesnt run on in one sentance."
- Screenshots 2 + 5 confirm: Footnote preview shows all language blocks concatenated
  (Hebrew/Greek/Latin labels + text in one flow).
- Artifact has U+2028 inside `.vn-sep` spans (K-R6-3 shipped), but **kepubify wraps
  every text node in `koboSpan`** — the preview extractor likely flattens spans and
  drops U+2028 line separators.
- **Fix direction (WIN):** eink-only popup separators using `<br/>` before each
  `vnote-source-label` / `vn-cat-head` / `vn-source-byline` (HTML breaks survive
  tag-strip better than Unicode sep inside koboSpan). Re-device after rebuild.

## K-R7-4 ⚠ OPEN — BOOK eyebrow spacing (K-R6-4 not sufficient)

- User: "still no space between BOOK and Numeral." Img 8: title page shows `BOOKI`
  (visually fused).
- Artifact **does** carry `BOOK&#160;I` (nbsp) inside koboSpan — emitter fix landed.
  Kobo's `font-variant:small-caps` + `letter-spacing:0.22em` + italic still eats
  even nbsp visually.
- **Fix direction (WIN):** add `word-spacing: 0.35em` (or split BOOK / numeral into
  separate spans with padding) on `.bookpage-eyebrow` for `target_reader: eink`.
  Verify Apple Books unchanged.

## K-R7-5 ✅ CLOSED (carry) — languages

- User: "languages work." Confirms K-R5-6 / K-R6-1 still holding on round-7 build.

## K-R7-6 ✅ CLOSED (carry) — long notes

- User: "long notes work." Multi-part splits (e.g. gen 1:1 `s3` 4-note part) open.

## K-R7-7 ⚠ OPEN — page-break seams

- User: "still a few page break issues." Img 6: Genesis ch 36 closing + ch 37
  heading on **same page** (expected fresh page at chapter boundary on Kobo).
- Kobo ignores CSS `page-break-*` inside `#book-inner` (K-R2-1) — only spine-file
  splits guarantee breaks. File-splitter may be packing ch-heading into prior piece
  when under byte cap.
- **Fix direction (WIN):** tighten `apply_file_split` to force piece break at every
  `ch-heading` for eink target (even when under soft cap), or isolate chapter
  openers like book-title pages.

## Verdict for v1.0.0 plan §B6

| Tap item | Round-7 result |
|---|---|
| Gen 1:1 split units | **6/7 pass** (`s7` fails) |
| Gen 35:18 re-tap | Not reported this round |
| Arabic popup spot-check | Pass (languages work) |
| BOOK II eyebrow | **Fail** (BOOKI fused) |
| Long chapter / no teleport | Partial — singletons still teleport |

## K-R7-8 — non-number marker alternatives (user request)

- User: find something other than numbers for Kobo study markers if possible.
- **Ruled out:** `◈` — never rendered on Kobo (any font).
- **Still valid:** bordered chip CSS (the box renders; only the *character inside*
  was a digit, which blends with the verse-number translation popup `1`).
- **New `marker_badge_style` options (eink A/B):**
  - `dot` → `•` (bullet; classic “note here”)
  - `dagger` → `†` (traditional footnote mark)
  - `asterisk` → `⁎` (alternate footnote mark)
  - `lozenge` → `◇` (matches legend commentary symbol — proven in popups)
  - `chip` → count digit (current default)
- **Honest limit:** multi-part verses (gen 1:1 ×7) cannot show distinct symbols
  per part without counts or letters — the `title` attribute still says
  “part N of M”; tap to discover.
- **Geometry fix ships with this:** `badge-trail` nbsp after every badge cluster
  (K-R7-2) — changing glyph alone does not fix terminal decline; test both.
- **A/B build:** `py -3 dev/build_kobo_marker_ab.py ethiopian-tewahedo` → five
  desktop kepubs `YHWH-MarkerAB-<edition>-<style>.kepub.epub`.

**M3 column: NOT LIVE.** Blocks v1.0.0 until K-R7-2 + K-R7-3 + K-R7-4 resolved
or documented as honest limitations in `EREADERS.md`.

---

## K-R7-8b — Marker A/B device results (2026-06-14 evening)

**Screenshots:** `kobo_img/1.jpeg`, `2.jpeg`, `3.png`, `4.png` (Desktop folder).
**Builds tested:** five `YHWH-MarkerAB-*` kepubs on `G:\` (chip / dot / dagger /
asterisk / lozenge). `badge-trail` shipped in all; **did not fix** K-R7-2.

### Per-style verdict

| Style | Device result |
|---|---|
| `chip` (digits) | Renders; same teleport/last-note bugs as all variants |
| `dot` (•) | **DISQUALIFIED** — EPUB barely loads / near-crash on Kobo |
| `dagger` (†) | Renders; user likes (“cross type thing”) |
| `lozenge` (◇) | Renders; user likes (“diamond”) |
| `asterisk` (⁎ U+2051) | **Empty bordered box** — glyph missing from Kobo font; chip CSS border still draws |

**Not the empty box:** dagger, lozenge, chip, dot (dot crashes but • glyph renders).

### Formatting progress (K-R7-3 partial)

User: formatting attempts “finally take hold” in translation + note popups (img 4:
gen 1:12 Footnote preview shows Hebrew/Greek/Latin/Ge'ez blocks). Run-on still
present in many notes; improvement is real but incomplete.

### K-R7-2 still uniform across all marker glyphs

- Gen 1:1 last unit (`s7`) — still fails.
- Gen 1:12 singleton — still teleports to **chapter start** (every A/B variant).
- Forensics: badge was sandwiched `…good.</span>[badge][trail][space]<a vn-link v13>`.

### WIN fixes shipped (post A/B)

1. **`asterisk` → ASCII `*`** — replaces U+2051 so Kobo shows a glyph inside the chip.
2. **New styles:** `dagger+count` (`†4`), `lozenge+count` (`◇7`) for multi-part splits.
3. **K-R7-2b eink placement:** badges insert immediately **after the verse vn-link**
   (not at last inline marker / verse tail) — removes terminal sandwich against the
   next verse's translation noteref. `dot` dropped from A/B script.
4. Rebuild: `py -3 dev/build_kobo_marker_ab.py ethiopian-tewahedo` → six kepubs.