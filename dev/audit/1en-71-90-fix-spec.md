# 1 Enoch 71 (+ 90 check) base-content fix — exact store-edit spec

> **For WIN to apply in the content phase** (Mac is spec-only — no `content/`/base edits; no
> guessing on scripture). Source: the PD Charles text in `dev/audit/1en-charles-source-71-90.md`.
> Root cause (WIN's diagnosis, now pinned to exact file:line): Charles's cross-reference
> "(as in **xlvi. 3**)" *inside* the 1 Enoch 71:13 editorial bracket was ingested as a **verse
> anchor** (`v-1en-71-46`, `<span class="vn">46</span>`), fracturing one note into a spurious
> "verse 46". 1 Enoch 71 has **17 verses** — there is no v46.

## Location

All occurrences are in **ONE file**: `epub_working/index_split_021.html` (the 1 Enoch base page).
`grep` confirms the spurious id appears 4×, nowhere else in the repo:
- inline (the verse paragraph): `id="v-1en-71-46"` + its `href="#vnote-1en-71-46"`
- aside block: `id="vnote-1en-71-46"` + its back-link `href="#v-1en-71-46"`

No `v-1en-46-3` anchor exists, so an internal cross-link to 1 Enoch 46:3 is **not** available →
restore the reference as **plain text** ("xlvi. 3"), exactly as Charles printed it.

## Edit A — the inline verse text (the 1 Enoch 71 paragraph)

**Current** (the v13→v14 stretch, verbatim):

```html
…thousands and ten thousands of angels without number. [Lost passage wherein the Son of Man was described as accompanying the Head of Days, and Enoch asked one of the angels (as in <a class="vn-link" id="v-1en-71-46" href="#vnote-1en-71-46" epub:type="noteref" title="1 Enoch 71:46"><span class="vn">46</span></a>) concerning the Son of Man as to who he was.] <a class="vn-link" id="v-1en-71-14" …>14</a> And he (…
```

**Fixed** — delete the entire spurious `<a class="vn-link" id="v-1en-71-46" …>…46…</a>` anchor and
restore the cross-reference text `xlvi. 3` in its place:

```html
…thousands and ten thousands of angels without number. [Lost passage wherein the Son of Man was described as accompanying the Head of Days, and Enoch asked one of the angels (as in xlvi. 3) concerning the Son of Man as to who he was.] <a class="vn-link" id="v-1en-71-14" …>14</a> And he (…
```

So v13's bracket now reads as one continuous editorial note, and the next anchor is `v-1en-71-14`
(verses run 1…17, contiguous).

## Edit B — the asides (merge `vnote-1en-71-46` into `vnote-1en-71-13`, then delete it)

**Current** (two fragments — the bracket was split at "(as in"):

```html
<aside class="vnote" id="vnote-1en-71-13" epub:type="footnote"><p><strong>1 Enoch 71:13.</strong></p><p class="vnote-text">“And that Head of Days came with Michael and Gabriel, Raphael and Phanuel, thousands and ten thousands of angels without number. [Lost passage wherein the Son of Man was described as accompanying the Head of Days, and Enoch asked one of the angels (as in”</p><p><a href="#v-1en-71-13" class="vnote-back" title="Back">↩</a></p></aside>
<aside class="vnote" id="vnote-1en-71-46" epub:type="footnote"><p><strong>1 Enoch 71:46.</strong></p><p class="vnote-text">“) concerning the Son of Man as to who he was.]”</p><p><a href="#v-1en-71-46" class="vnote-back" title="Back">↩</a></p></aside>
```

**Fixed** — re-join into a single `vnote-1en-71-13` (insert `xlvi. 3` at the split point) and
**delete the `vnote-1en-71-46` aside entirely**:

```html
<aside class="vnote" id="vnote-1en-71-13" epub:type="footnote"><p><strong>1 Enoch 71:13.</strong></p><p class="vnote-text">“And that Head of Days came with Michael and Gabriel, Raphael and Phanuel, thousands and ten thousands of angels without number. [Lost passage wherein the Son of Man was described as accompanying the Head of Days, and Enoch asked one of the angels (as in xlvi. 3) concerning the Son of Man as to who he was.]”</p><p><a href="#v-1en-71-13" class="vnote-back" title="Back">↩</a></p></aside>
```

(The re-join uses OUR base's sacred-texts wording — "…concerning the Son of Man **as to who he
was**.]" — **not** the Wikisource short form, per WIN's instruction.)

## Post-edit gates (WIN)

1. **Base-invariant** after any `epub_working` mutation: `test_nested_anchors` + `check_nested_anchors --fix`
   (the build converts `vn-link`→`span`; a dropped/duplicated anchor would surface here). Memory
   `feedback_base_invariant_gating`.
2. **Structural auditor** (`dev/audit_book_structure.py`): 1 Enoch 71 verse order is now `[1..17]`
   contiguous (the prior `[1..13, 46, 14..17]` FAIL is cleared).
3. **Rebuild + epubcheck** the editions whose canon includes `1en` (Ethiopian-only — `content/canons.yaml:367`;
   **the 9 KJV editions do NOT include 1 Enoch → KJV byte-stability is unaffected**). Expect epubcheck 0/0/0/0
   and the v13 popup showing the full bracket; confirm **no** dangling noteref to the deleted
   `vnote-1en-71-46` remains.

## Chapter 90 — checked, CLEAR of this bug class (one separate observation)

WIN asked to cross-check the ch90 bracket class (Charles brackets at XC.10/13/14/15/17/18/20/27/31/35/39).
**Result: 1 Enoch 90 has NO cross-reference-as-anchor bug** — `grep` finds the `(as in <a class="vn-link"…>`
pattern **only** in ch71. Charles's ch90 editorial brackets did not spawn a spurious verse anchor in our store.

**Separate observation (NOT part of this fix — flag for WIN to assess vs the Charles source):** 1 Enoch 90's
verse anchors run **1…19 then jump to 42** (`v-1en-90-1` … `v-1en-90-19`, `v-1en-90-42`) — verses 20–41 are
not separately anchored. This is **monotonic** (19 < 42), so it is **not a misordering** (the structural
auditor's 293/294 did not FAIL it) and it is unrelated to the ch71 bracket bug. It is either the base folding
the long Animal-Apocalypse section (90:20–41) into the surrounding anchored blocks, or a genuine anchor gap.
WIN should compare against the Charles source to decide whether 90:20–41 need their own anchors; if so, that is
a separate completeness item, not part of the v46→v13 bracket-merge.

## Summary

| edit | file | action |
|---|---|---|
| A | `epub_working/index_split_021.html` (1En 71 paragraph) | delete spurious `<a … id="v-1en-71-46" …>46</a>`; restore plain text `xlvi. 3` |
| B | same file (asides) | merge `vnote-1en-71-46` text into `vnote-1en-71-13` (insert `xlvi. 3`); delete the `vnote-1en-71-46` aside |
| — | result | 1 Enoch 71 = 17 contiguous verses; v13 bracket whole; no v46 |
| ch90 | — | clear of this bug; flag the 90:20–41 anchor gap separately |
