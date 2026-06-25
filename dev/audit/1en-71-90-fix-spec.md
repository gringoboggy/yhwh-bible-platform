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

---

## P3 — 90:20–41 anchor-gap verdict + a SEPARATE 90:13–18 finding (Mac, 2026-06-25)

> WIN's P4 ask (laundry-list P3): "resolve the 90:20–41 anchor gap vs the PD Charles source —
> real missing-verse/anchor defect, or a faithful Charles-versification artifact?" Spec-only;
> no `content/` edits; no scripture guessing. **Evidence is OUR base** (`epub_working/index_split_022.html`,
> the file that actually holds 1En 90 — *not* `021`), cross-read against the Charles structure in
> `dev/audit/1en-charles-source-71-90.md`.

### Base reality for 1En 90 (anchors in document order)

`[1,2,3,4,5,6,7,8,9,10,11,12, 13, 16, 14, 17, 15, 18, 19, 42]` — i.e. **two** oddities:
**(I)** a 13→18 region whose anchors are interleaved `13,16,14,17,15`, and **(II)** a jump `19 → 42`
(vv20–41 carry no `vn-link` anchor).

### Verdict on (II) the 90:20–41 gap — FAITHFUL ARTIFACT, *not* a defect — NO fix required

The **text of vv20–41 is fully present**, inline in the `v-1en-90-19` paragraph, with each verse number
printed as **plain text** ("20 And I saw till a throne was erected…", "21 And the Lord called…", …,
"41 …"). A scan of that paragraph finds **all 22 inline markers 20,21,…,41** present and in order, plus
Charles's verbatim section headings embedded mid-paragraph: **"XC. 20-27. Judgement of the Fallen Angels,
the Shepherds, and the Apostates"** and **"XC. 28-38. The New Jerusalem, the Conversion of the surviving
Gentiles, the Resurrection…"**. v42 is anchored; the next anchor is `v-1en-91-1`.

So no scripture is missing — the base folded the long Animal-Apocalypse climax (Charles vv20–42) into one
anchored paragraph and kept the verse numbers as inline text. This is why the structural auditor's 293/294
did **not** FAIL it (text complete + monotonic). **Conclusion:** an *anchor-granularity* gap, not a
content/missing-verse defect. **Recommended action: NONE required.** Optional, purely-additive nicety
(low value): promote the inline "20".."41" numbers to `vn-link` anchors so those verses gain popups /
deep-links — but that is cosmetic granularity, touches no wording, and is **not** part of the round-13
1En fix. Do **not** treat 90:20–41 as a blocker.

### SEPARATE finding on (I) the 90:13–18 region — a REAL text-corruption defect (hand to WIN)

While confirming (II) I found a genuine defect in **1En 90:13–18**. Charles prints these verses as a
**doublet in two parallel columns** (his *g* / *q* recensions of the same vision). Our base ingested the
two columns **zippered word-by-word across the rows instead of read down each column**, producing
unreadable salad. Raw base (apparatus-stripped), verbatim:

> `13 And I saw till the †shepherds and† 16 All the eagles and vultures and eagles and those vultures and kites came, ravens and kites were gathered and †they cried to the ravens† that they together, and there came with should break the horn of that ram, and them all the sheep of the field, they battled and fought with it, and it yea, they all came together, and battled with them and cried that its help helped each other to break that might come. horn of the ram. 14 And I saw till that man, who wrote 17 And I saw that man, who wrote down the names of the the book according to the shepherds [and] carried up into the command of the Lord, till he presence of the Lord of the sheep [came opened that book concerning the and helped it and showed it everything: destruction which those twelve he had come down for the help of that last shepherds had wrought, and ram]. showed that they had destroyed much more than their predecessors, before the Lord of the sheep. 15 And I saw till the Lord of the sheep 18 And I saw till a great sword came unto them in wrath, and all who was given to the sheep, and the saw Him fled, and they all fell †into His sheep proceeded against all the shadow† from before His face. beasts of the field to slay them, and all the beasts and the birds of the heaven fled before their face.`

De-interleaving the columns recovers two coherent streams (illustrative — **VERIFY against Charles, do not
treat as authoritative**):
- **Left column → vv13,14,15:** "13 And I saw till the †shepherds and† eagles and those vultures and kites
  came, and there came with them all the sheep of the field, yea, they all came together, and helped each
  other to break that horn of the ram. 14 And I saw till that man, who wrote the book according to the
  command of the Lord, till he opened that book concerning the destruction which those twelve shepherds had
  wrought, and showed that they had destroyed much more than their predecessors, before the Lord of the
  sheep. 15 And I saw till the Lord of the sheep came unto them in wrath, and all who saw Him fled, and they
  all fell †into His shadow† from before His face."
- **Right column → vv16,17,18:** "16 All the eagles and vultures and ravens and kites were gathered
  together, and there came with them all the sheep of the field … and cried that its horn should break the
  horn of that ram, and they battled and fought with it, and it cried that its help might come. 17 And I saw
  that man, who wrote down the names of the shepherds [and] carried up into the presence of the Lord of the
  sheep [came and helped it and showed it everything: he had come down for the help of that last ram]. 18
  And I saw till a great sword was given to the sheep, and the sheep proceeded against all the beasts of the
  field to slay them, and all the beasts and the birds of the heaven fled before their face."

That the salad de-zips cleanly into two sensible streams is itself the proof of the mechanism (column
zipper), not random corruption.

**Severity:** MEDIUM — corrupted scripture *prose* in 1En 90:13–18 (vs. the 71:46 issue, which was only a
spurious anchor). **1En is Ethiopian-only** (`content/canons.yaml`) → **no 9-KJV byte-stability impact**.
**WIN store-edit prescription (no guessing — re-source first):** (1) re-fetch the full Charles ch90 vv13–18
verbatim (same Wikisource/sacred-texts source as the 71 fix; the existing `1en-charles-source-71-90.md` only
*summarized* ch90); (2) replace the zippered `v-1en-90-13…18` prose in `epub_working/index_split_022.html`
with the de-interleaved per-verse text (one coherent stream per verse), restoring anchor order to
`13,14,15,16,17,18`; (3) post-edit gates as in the 71 fix — `test_nested_anchors` + `check_nested_anchors
--fix`, structural auditor (90 order now ascending), rebuild Ethiopian-canon editions + epubcheck 0/0/0/0.
This is a **distinct, higher-priority** 1En ch90 item; the 20–41 anchor gap above needs nothing.
