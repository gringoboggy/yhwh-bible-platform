# 1 Enoch 71 & 90 — PD Charles source text (for the round-13 `1en` base-content fix)

> **Purpose.** WIN root-caused the structural auditor's `1en` FAIL (ch 71 reads
> `[1..13, 46, 14..17]`) as a **split editorial bracket**, not a verse re-order: Charles's
> cross-reference "xlvi. 3" (Roman 46) *inside* a bracketed note was mis-ingested as a verse
> 46. The fix needs the authoritative PD source so the reconstruction is faithful (no guessing
> on scripture). This file supplies it. **WIN owns the content fix** (the store edit + anchor
> drop); Mac fetched the source (LANE_HANDOFF, 2026-06-24 — WIN's optional ask).
>
> **Provenance:** R.H. Charles, *The Book of Enoch* (English translation), public domain.
> Verbatim text from Wikisource (`en.wikisource.org/wiki/The_Book_of_Enoch_(Charles)`),
> corroborated against the sacred-texts 1917 edition (`/bib/boe/boe074.htm`, correct verse
> numbering + critical apparatus). **Textual variant flagged below — reconcile to OUR base,
> don't import a new wording.**

## Chapter 71 — full verbatim (17 verses; there is NO verse 46)

1. And it came to pass after this that my spirit was translated / And it ascended into the heavens: / And I saw the holy sons of God.
2. And I saw two streams of fire, / And the light of that fire shone like hyacinth, / And I fell on my face before the Lord of Spirits.
3. And the angel Michael [one of the archangels] seized me by my right hand, / And lifted me up and led me forth into all the secrets.
4. And he showed me all the secrets of the ends of the heaven, / And all the chambers of all the stars, and all the luminaries.
5. And he translated my spirit into the heaven of heavens, / And I saw there as it were a structure built of crystals.
6. And my spirit saw the girdle which girt that house of fire, / And on its four sides were streams full of living fire.
7. And round about were Seraphin, Cherubin, and Ophannin: / And these are they who sleep not / And guard the throne of His glory.
8. And I saw angels who could not be counted, / A thousand thousands, and ten thousand times ten thousand.
9. And they came forth from that house, / And Michael and Gabriel, Raphael and Phanuel, / And many holy angels.
10. And with them the Head of Days, / His head white and pure as wool, / And His raiment indescribable.
11. And I fell on my face, / And my whole body became relaxed, / And my spirit was transfigured.
12. And these blessings which went forth out of my mouth were well pleasing before that Head of Days.
13. **[Lost passage wherein the Son of Man was described as accompanying the Head of Days, and Enoch asked one of the angels (as in xlvi. 3) concerning the Son of Man.]**
14. This is the Son of Man who is born unto righteousness, / And righteousness abides over him, / And the righteousness of the Head of Days forsakes him not.
15. He proclaims unto thee peace in the name of the world to come; / For from hence has proceeded peace since creation.
16. All shall walk in his ways since righteousness never forsaketh him: / With him will be their dwelling-places, and with him their heritage.
17. And so there shall be length of days with that Son of Man, / And the righteous shall have peace and an upright way.

**∴ 17 verses, end of chapter.** The bracketed editorial note IS verse 13 (Charles brackets it
because the Ethiopic here is a lost/conflated passage). `xlvi. 3` = a cross-reference to **1 Enoch
46:3** (Roman numeral 46), embedded *inside* the v13 bracket — **it is not a verse number.**

### Diagnosis ↔ fix (confirms WIN's root-cause)

Our ingest fractured the single v13 bracket at "(as in **xlvi. 3**)": the Roman 46 was read as a
verse marker, so the bracket's tail became a spurious **v46** and the order came out
`…13, 46, 14…`. **Fix = merge the spurious v46 anchor's text back into v13's bracket + drop the
v46 anchor.** 1 Enoch 71 has exactly 17 verses.

⚠ **Textual variant — reconcile to OUR base, do not import a new wording.** Two PD editions differ
on the bracket's *tail*:
- **Wikisource (above):** "…concerning the Son of Man.]"
- **sacred-texts 1917:** "…concerning the Son of Man **as to who he was**.]"

WIN's diagnosis quoted our base as `…(as in` + the spurious v46 `) concerning the Son of Man as to
who he was.]` — i.e. OUR base already carries the **sacred-texts** wording ("as to who he was").
So the correct reconstruction is to re-join our own existing fragments (v13 head + the v46 tail)
into one v13 bracket — **not** to overwrite with the Wikisource short form. The source here is the
verification that the join is faithful and that no verse content is lost (only the false anchor).

## Chapter 90 — structure (WIN to cross-check our store for the same class)

Charles ch 90 = **the Dream-Visions climax**; verses numbered **1–42** (Charles groups several as
doublets; ~22 logical verses). It is **heavy with bracketed editorial notes** — flagged at
**XC.10, 13, 14, 15, 17, 18, 20, 27, 31, 35, 39** (Wikisource render). WIN's note said "(ch 90) the
same root-cause check": **check whether our `1en` ch 90 store has a similar spurious verse produced
by a Roman-numeral cross-reference mis-read inside one of those brackets** (the auditor's ch-90
finding, if any, should land on one of the bracketed verses above). Full ch-90 verbatim was not
captured here (the fast extractor summarized it); **re-fetch the exact verse if a specific spurious
anchor is implicated** — same Wikisource/sacred-texts source. If the auditor shows ch 90 verse order
contiguous, no fix is needed there.

## Sources

- [The Book of Enoch (Charles)/Chapter 71 — Wikisource](https://en.wikisource.org/wiki/The_Book_of_Enoch_(Charles)/Chapter_71)
- [The Book of Enoch (Charles)/Chapter 90 — Wikisource](https://en.wikisource.org/wiki/The_Book_of_Enoch_(Charles)/Chapter_90)
- sacred-texts 1917 edition, ch LXXI: `https://sacred-texts.com/bib/boe/boe074.htm` (403 to automated fetch; corroborated via search snippet for the v13 bracket tail "…as to who he was.]").
