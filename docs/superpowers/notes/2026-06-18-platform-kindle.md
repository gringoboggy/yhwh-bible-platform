# Platform research — Kindle (Round 9 / round-13 re-verify)

**Status:** Research complete — M4b fork design input. Round-13 forensic re-verify (2026-06-23) appended below.
**Date:** 2026-06-18 (orig) · 2026-06-23 (round-13 addendum) · **Lane:** mac · **Dim:** `platform-kindle`

---

## 1. Our target UX (non-negotiables)

From `dev/EREADERS.md` §Kindle + `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`:

- **Delivery:** Send-to-Kindle → Amazon KFX conversion (no sideload).
- **Proven recipe:** everywhere build + `kindle_post.make_kindle_safe` (NOT the retired `--target-reader kindle` in-pipeline variant).
- **User goal (M4b):** Kobo-like split — **translation popups in scripture**, **study notes elsewhere** (suppress inline ◈/numbered markers).
- **Kindle has no true popup footnotes** — visible endnotes / navigate-to-anchor is the ceiling.
- **Gate:** `verify_kindle_safe` + epubcheck 0/0/0/0 + **phone STK spot-check** (link targets, not just delivery).

---

## 2. Official format support

| Topic | Vendor says | Our build uses |
|---|---|---|
| EPUB upload | Send-to-Kindle accepts EPUB; converts to KFX internally | `.epub` per FORMAT_MATRIX `kindle` row |
| Popup footnotes | KF8/KFX: footnotes typically endnotes or inline; pop-up model unreliable | Inline `noteref` + `hidden=""` asides — **phone QA FAIL on anchor resolution** |
| Internal `#` anchors | Historical KindleGen issues with anchors across page breaks ([Stack Overflow](https://stackoverflow.com/questions/9186437/problems-with-internal-links-anchors-in-mobi-output-from-kindlegen)) | Chapter `page-break-before` + per-piece `notes-section` at chapter tail → taps collapse to 3:24, 8:10, 11:26… |
| Embedded fonts | KFX re-flows; partial honoring | Full apparatus fonts in source EPUB; stripped to single `dc:language` in kindle_post |
| `display:none` | Amazon ingestion sensitive — E999 on multi-value `dc:language` | **Physically stripped** by kindle_post (proven june10) |
| Collapsible ToC | No `<details>` support | `toc_expandable` gated off in TARGET_CAPS.kindle |

---

## 3. How others achieved similar goals (commercial study-Bible endnote patterns)

| Technique | Who / where | Applies to us? |
|---|---|---|
| Visible endnotes / footnote section at chapter end | NIV Study, ESV Study (Kindle) | **Yes — M4b direction** |
| Suppress inline note markers; link from verse to end section | Common KFX-safe pattern | **Yes — primary M4b option (shipped Option B)** |
| Inline superscript markers + popup asides | Our everywhere build | **Fails on phone KFX** (proven) |
| Study glossary backmatter with jump links | Kobo K-R9c | **Shipped for Kindle as Option B** — badge → `kindle_study_glossary_*.html#vnotes-…`, ↩ back-link to verse |
| Minimal post-process over standard EPUB | june10recipe vs FIXED.epub failure | **Shipped** — `kindle_post` productized |

---

## 4. Why minimal `kindle_post` beat the elaborate variant

The retired `--target-reader kindle` variant tuned against the **Kindle Previewer** oracle:
source-label compaction + 2-popup language cap + `apply_kindle_toc_rows` + `apply_kindle_unhide`
+ `_KINDLE_SAFE_CSS` append + a 2 MB file-split. Previewer + epubcheck passed it; **Send-to-Kindle
ingestion (KFX) rejected it** (`FIXED.epub` FAIL, turn-83/84). The minimal recipe — strip
`display:none`/`visibility:hidden`, KEEP `.vn-sep` (visible language separators), collapse
`dc:language` → single `en-US`, KEEP `hidden=""`, OCF re-zip mimetype-first/stored — DELIVERS.
Lesson: the Previewer is not the STK oracle; clever Previewer-targeted transforms are exactly
what broke Amazon's converter. (`scripts/core/kindle_post.py` docstring; `dev/EREADERS.md` §Kindle.)

## 5. M4b fork — concrete HTML moves (shipped Option B, Kobo K-R9 mirror)

`apply_kindle_m4b` (`scripts/core/kindle_post.py`):
1. Extract every `vnotes-*` study aside out of scripture prose (`_extract_m4b_asides`).
2. Build a `kindle_study_glossary_NN.html` spine (155 pieces on ethiopian), book-grouped, ~400 KB split.
3. **Keep** `verse-notes-badge` markers; retarget their `href` `#vnotes-…` → `kindle_study_glossary_NN.html#vnotes-…`.
4. Translation `vnote-*` popups stay in their **hidden tail** `notes-section` (only STK-deliverable shape; any unhide/relocate → STK LOAD FAIL, 165347Z/221232Z).
5. `apply_kindle_m4b_css`: `.book-title-page page-break-after:auto` (title 3-page split) + `.toc-chapter-row` margins; `_flatten_toc_pills` for horizontal chapter rows.

Built-artifact verification (2026-06-19T144600Z ethiopian m4b): 30,339 badges retargeted,
0 same-file `#vnotes` leaks, 0 bare `#v-` in glossary, 1 `dc:language`, 0 hidden survivors,
0 `toc-chapters <ol>` leftover — gate-clean.

## 6. What STK 6/6 (2026-06-14) did NOT gate

- `noteref` → intended aside target (vs chapter page-break anchor)
- Translation `vn-link` tap behavior
- Inline marker density / visual clutter
- ToC horizontal chapter-row layout
- First-open KFX download/index time
- Location vs page-number user expectation
- **(round-13)** glossary ↩ back-link COMPLETENESS — see §7.

---

## 7. ★ Round-13 defect (2026-06-23): 371 study-glossary entries have no return link

`apply_kindle_m4b` drops the ↩ back-to-scripture link for **every study note on a book that
has no `v-{book}-{ch}-{verse}` verse anchor** — the 4 Ge'ez-only canon books that carry study
badges but no translation-popup verse anchors: **jub (192), mq1 (84), mq2 (50), mq3 (45) = 371**.

Mechanism (`scripts/core/kindle_post.py`):
- `_prepare_glossary_aside` (line 420) strips the aside's original `vn-back` whose href was
  `#vbadge-{book}-{ch}-{verse}-{seg}` — a VALID same-spine return anchor (the badge element
  carries that `id` in scripture, e.g. `vbadge-jub-24-3-s1` in `index_split_020_00.html`).
- `_glossary_back_link` (line 402) rebuilds the return link ONLY from `v-{book}-{ch}-{verse}`
  via `v_anchor_files`. For jub/mq* that key never exists → it returns the anchor-less fallback
  `<p class="vn-back"><strong>24:3</strong></p>` (no `<a>`).
- No gate catches it: `verify_kindle_m4b` checks m4b-1..6 only; none assert back-link presence.

Forward nav works (badge → glossary), but the reader is stranded in the 155-piece backmatter
with no way back to Jubilees / Meqabyan scripture. Books with `v-` anchors (gen/psa/mat/1en…)
are unaffected (1en: 0 anchor-less). Accounting exact: 29,968 anchored + 371 anchor-less = 30,339.

**Fix:** capture a `vbadge_files: dict[id→spine]` map alongside `v_anchor_files` (same scan,
`id="vbadge-…"`), and in `_glossary_back_link` fall back to
`{vbadge_spine}#vbadge-{book}-{ch}-{verse}-{seg}` when the `v-` anchor is missing — the original
back-target the code already throws away. Add a `verify_kindle_m4b_glossary_html` check: every
`<div class="study-glossary-entry">` must contain a `vn-back` `<a>` (fail if `<strong>`-only).

---

## References
- `scripts/core/kindle_post.py`, `scripts/build_kindle.py`, `scripts/build_format_matrix.py`
- `docs/superpowers/notes/2026-06-18-m4b-kindle-fork-design.md`, `…2026-06-18-kindle-stk-m4b-device-qa.md`
- `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`, `dev/EREADERS.md` §Kindle
