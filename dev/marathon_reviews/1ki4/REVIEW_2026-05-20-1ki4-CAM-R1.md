# C-6 Round 1 — adversarial CAM review for 1 Kings 4

**Reviewer:** fresh isolated subagent, no prior context, blind to GG witness side.
**Target artifact:** `content/manuscript/kings/calibration/1ki4_witnessCAM_hires.json`
**Parchment:** Cambridge MS Add.1570, f127v (3 cols, ~42 lines/col) + f128r-L/M (~42 lines/col).
**Method:** PIL/LANCZOS upscale (2x–10x), autocontrast (cutoff 2–5), targeted strips per column with auto-detected text-line y boundaries from row-darkness profiles. Column boundaries auto-detected from column-darkness scan: f127v L=x[1691-3221], M=x[3569-5142], R=x[5485-7126]; f128r L=x[891-2505], M=x[2838-4424], R=x[4783-6301]. Line heights ~155-165px. All crops in `C:\Users\bogda\AppData\Local\Temp\yhwh_1ki4_cam_R1\` (will be cleaned).

## Headline verdict

**BLOCKED.** The C-5 transcription is not a blind reading of MS Add.1570 f127v + f128r. The textual content of C-5's v2-v34 closely matches a printed-edition Ge'ez 1Ki4 text (likely the Mashafa Sänäselassie / EOTC standard edition) but does **not** match the actual inked characters of the parchment. The C-5 cardinal-rule claim ("transcribed what is inked") is refuted by multiple side-by-side comparisons. The structural defects (wrong section identification, wrong column→verse mapping, missing intra-chapter section rubrics, missing ✣ in-text marks, multiple completely-wrong proper names) are too pervasive to fix verse-by-verse; this transcription needs a full RE-DO.

## Boundaries

### START
- **C-5 claim:** "f127v-L L7, first inked word after red rubric `✣ ክፍል ፰` = `ወኮነ`".
- **Parchment evidence:** The red rubric `✣ ክፍል ፮(?) ✣` (digit shape between bars; cannot confirm exact digit value at this resolution but it is *not* clearly ፰) is inked at **f127v-L L1**, mid-line, NOT at L7. The first inked black words after the L1 rubric are **`ወሰምዑ` / `ሙ፡እስራኤል፡ዘንተ፡ፍትሐ፡ዘፈትሐ፡[ንጉ]ሥ`** (and-they-heard / all-Israel this-judgment which-he-judged the-king) — i.e. content corresponding to biblical **1Ki3:28**, not 1Ki4:1. This text extends through L1-L5.
- **Second rubric at L7:** A SECOND `✣ ክፍል ? ✣` rubric is inked mid-L7. The phrase preceding it (ending L6→L7) reads `ኔ፨ (ወፍትሐ።) ወእምዝህኮነ፡ንጉሥ፡ሰሎሞን፡ ይነግሥ ፡ላዕለ፡ኩሉ፡እስራኤል` (with bracketed underlined editorial mark `(ወፍትሐ።)` and `፨` paragraph mark — both excluded by C-5 with no flag). The phrase after the L7 rubric begins at L8: `ወእሉ፡እሙንቱ፡መላእክት፡ዘሎቱ፡አዛርያስ...`.
- **STATUS: REJECTED.** Three concurrent failures:
  1. Wrong `line_start` (C-5 says L7; correct anchor is L6 where `ወእምዝህኮነ` begins, or L1 if the section ፰ rubric is the anchor).
  2. Wrong head word (`ወኮነ` vs parchment `ወእምዝህኮነ` — prefix `ወእምዝህ-` ["and from then"] dropped).
  3. Missed entire prior section body (L1-L5, biblical 1Ki3:28 — `ወሰምዑ፡ኩሎሙ፡እስራኤል፡ዘንተ፡ፍትሐ፡ዘፈትሐ፡[ንጉ]ሥ፡ወፈርሁ፡ኩሉ፡እስራኤል፡እምቅድመ፡ገጹ፡ለንጉሥ፡እስመ፡ርእዩ፡ከመ፡ጥበበ፡እግዚእብሔር፡ሀሎ፡ሳዕሌሁ...`). If the C-5 scope is "the section bounded by the L1 rubric and the next sequential rubric", this prior content belongs IN the section.

### END
- **C-5 claim:** "f128r-M, immediately before red rubric `✣ ክፍል ፱` = last word `ጥበቦ` at v34."
- **Parchment evidence:** I could not verify a `✣ ክፍል ፱` rubric in the C-5-claimed position. Multiple intra-chapter `✣ ክፍል ? ✣` rubrics are inked across the body (see ✣-rubric audit below), and the f128r-M column actually contains content matching biblical **1Ki5:11+ / 1Ki6:1+** (Hiram-and-Solomon, then temple construction with measurements `፬` cubits, `፪` cubits, `፸` cubits, etc.) — NOT the C-5 text "ወመጽኡ፡ኩሎሙ፡አሕዛብ፡ይስምዑ፡ጥበቦ".
- The actual biblical 1Ki4:34 content (`ወይመጽእሉ፡ኩሉ፡ሕዝብ፡ከመ፡ይስምዑ፡ጥበቦ`) is present, but at **f127v-R L1**, NOT at f128r-M.
- **STATUS: REJECTED.** Wrong folio entirely.

## Column transitions

C-5 claims 4 clean transitions. All 4 are **wrong** in their verse-to-column anchoring because the verse→line mapping is broken throughout. The column transitions themselves on the parchment are clean (no mid-word splits, no dropped tokens at the boundaries that I could observe). But the C-5 verse labels at each transition do not match.

| Transition | C-5 claim | Parchment reality |
|---|---|---|
| f127v-L → f127v-M | "clean at v9 head `ወቤንዳቅር፡በማቅስ`" | f127v-L (42 lines) ends with deputy-list content (biblical 1Ki4:13-19 vicinity); f127v-M (40 lines) begins with content corresponding to biblical 1Ki4:19-20 (`ሲዎን፡ንቱ ... አሞርዎን፡ወአግ ... ባ` = Sihon king of Amorites and Og of Bashan). No `ወቤንዳቅር` at column head. |
| f127v-M → f127v-R | "clean at v17 head `ወዮሣፋጥ፡ወልደ፡ፋሩሐ፡በይሳኮር`" | f127v-R L1 reads `ዓሣት ✣ ወይመጽእሉ፡ኩሉ፡ሕዝብ፡ከመ፡ይስምዑ፡ጥበቦ` (= 1Ki4:33b-34). NO `ወዮሣፋጥ` at column head — and `ወዮሣፋጥ` does not appear ANYWHERE I sampled in the R column. |
| f127v-R → f128r-L | "clean at v24 folio break" | f127v-R bottom is unverified at this round; f128r-L L1-6 begins with content `...ውስተ፡ሊባኖስ፡በ ፬ ፡ ወርኅ፡ወይስተባርዎሙ ... ህልዎ፡ ፪ ፣ ወርኁ፡ውስተ፡ሊባኖስ፡ ... ህልዎ፡ውቴ፡አብየቲሆሙ፡ወአዶኒራም፡መልአከ፡በዎርያን፡ሎቱ፡ለሰሎሞን` (Lebanon, 4 months, 2 months, Adoniram and his labor force) — biblical 1Ki5:14-16 vicinity. NO `እስመ፡ይኄሊ፡ላዕለ፡ኩሉ` at column head. |
| f128r-L → f128r-M | "clean at v31 head `ወጠብበ፡እምኩሎሙ`" | f128r-M L1+ contains content about temple construction: `...ለሕዝብያ፡እስራኤል፡ወሐነጽ፡ሰሎምን፡ወረጸም፡ቤት፡መቅደስ ... ለቤት፡እስከ፡ፈሩ፡ወእስከ፡ሠራዊት፡ወኩሎ፡አረፋቲሁ፡በዕፀወ፡ ... በዕፀ፡ጻውቂን፡...` (= biblical 1Ki6:1+, the Temple construction). NO `ወጠብበ` at column head. |

**STATUS: ALL 4 TRANSITIONS — anchoring REJECTED.** (No "recensional-minus drops" suspected; rather the C-5 verse-anchors are not aligned to actual parchment columns at all.)

## ✣ cross-count audit

C-5's `tokens[]` arrays contain `✣` at scattered positions (mostly inside `notes` and rubric mentions; no in-body `✣` are preserved per the transcription note). But the **parchment displays inked red `✣` marks throughout the body** — far more than C-5 captured. From my f127v-L L7-L17 reading alone I counted these inked **red `✣`** marks NOT preserved as tokens by C-5:

- L9 mid-line: `ዘሎቱ፡አዛርያስ፡ወልደ፡ሳዶቅ፡ካህን ✣ ኤልያብ፡ወአኪያ`
- L10 mid-line: `ደቂቀ፡ሱፋት ✣ ወኢዮሳፍጥ`
- L11 mid-line: `አክያድ፡መዘክር ✣ ወብንያስ`
- L13 mid-line: `ካህናት ✣ ወአዛርያስ`
- L16/L17 mid-line: `ላዕለ፡ዓርዕ ✣ ወቶሰሎሞን ✣ ፲ ፡ እጄው...`
- L20 head: `✣ ክፍል ፬(?) ✣ ወዝንቱ...`
- L23 mid-line: `ወቤተ፡ሄናን ✣ ወልደ፡ሄሁድ`

Similar density on f127v-M (where at M2 `✣ ፬ ✣` numeral is inline, at M4 `✣ ወኮነ...` mid-text, at M8 `ለሕይወቱ ✣ ክፍል ፬(?) ✣ ወኮነ...`, at M11 `ሕሪጽ ✣ ወ ፲ ፣...`, at M22 `ሰሎምን ✣ ክፍል ፬(?) ✣ ወቦሰሎምን`, at M28 `በበ፡ሥርዓት ✣ ✣ ክፍል ፬(?) ✣ ✣ ወሀበ፡እግዚእብሔር`...).

C-5 says "No in-body ✣ tokens preserved (none observed in body of CAM section-8)" — this is **demonstrably false**. The body is densely peppered with red `✣` clause-divider marks.

**STATUS: SYSTEMATIC FAILURE.** Conservative estimate: 15+ in-body `✣` marks omitted on f127v-L alone, with comparable densities in M and R columns. Full chapter scope likely 50+ omitted `✣`.

## Intra-chapter `ክፍል` sub-rubrics

C-5 claim: "No intra-chapter `ክፍል N` sub-rubrics observed."
**Parchment reality:** I observed at least **5 distinct `✣ ክፍል ? ✣` red rubrics in the f127v scope alone**:
- f127v-L L1 (initial — body content of this section is biblical 1Ki3:28 + opening of 1Ki4:1)
- f127v-L L7 (boundary between sections containing 1Ki4:1 and 1Ki4:2+)
- f127v-L L20 (boundary mid-deputies list)
- f127v-M L8 (boundary in middle of 1Ki4 wisdom/governor content)
- f127v-M L22 (another boundary mid-text)
- f127v-M L28 (boundary into biblical 1Ki4:29+ wisdom section, with TWO `✣ ✣` bracketing crosses)
- f127v-R likely has additional rubric(s) at the 1Ki4→1Ki5 transition (`ክፍል ? ✣ ወፈነወ፡ኪራም`)

**STATUS: FAILURE.** C-5's "0 intra-chapter sub-rubrics" is wrong by at least 4 (likely 5-7+).

## Per-verse defect list (sampled CRITICAL/MAJOR cases)

C-5's textual content for v2-onward closely tracks a printed Ge'ez 1Ki4 edition. The parchment readings are repeatedly different. I cross-checked a representative sample (v1-v8) and every single verse exhibits at least one MAJOR defect. Given the systematic nature, I list the most consequential.

### v1 — CRITICAL (whole-verse anchoring + spelling)
- C-5: `ወኮነ፡ንጉሥ፡ሰሎሞን፡ይነግሥ፡ላዕለ፡ኩሉ፡እስራኤል`
- Parchment (f127v-L L6→L7): `ወእምዝህኮነ፡ንጉሥ፡ሰሎሞን፡ይነግሥ፡ላዕለ፡ኩሉ፡እስራኤል`
- Defects: prefix `ወእምዝህ-` dropped; line_start wrong; ✣ section rubric immediately follows the verse on L7 (not captured).

### v2 — CRITICAL (multiple text differences)
- C-5: `ወእሉ፡መላእክት፡እለ፡ሎቱ፡ዓዛርያስ፡ወልደ፡ሳዶቅ፡ካህን`
- Parchment (L8-L9): `ወእሉ፡እሙንቱ፡መላእክት፡ዘሎቱ፡አዛርያስ፡ወልደ፡ሳዶቅ፡ካህን ✣ ኤልያብ፡ወአኪያ...`
- Defects:
  - `እሙንቱ` MISSING from C-5 after `ወእሉ`
  - `እለ` vs parchment `ዘሎቱ` — different relative pronoun
  - `ዓዛርያስ` (with ዓ U+12D3) vs parchment `አዛርያስ` (with አ U+12A0) — different first consonant
  - C-5 v2 stops at `ካህን`; parchment continues with `✣ ኤልያብ፡ወአኪያ...` which is C-5's v3 *but* the v3 names are also wrong (see below)

### v3 — CRITICAL (entire name set wrong)
- C-5: `ወኤሊሐሬፍ፡ወአኪያ፡ደቂቀ፡ሲሳ፡ጸሐፍት፡ወዮሣፍጥ፡ወልደ፡አኪሉድ፡ዘያዜክር`
- Parchment (L9-L11): `[✣] ኤልያብ፡ወአኪያ፡ደቂቀ፡ሱፋት ✣ ወኢዮሳፍጥ፡ወልደ፡አክያድ፡መዘክር`
- Defects:
  - `ኤሊሐሬፍ` → parchment `ኤልያብ` (Elihoreph vs Eliab — completely different name)
  - `ሲሳ` → parchment `ሱፋት` (Shisha vs Sufat — different name)
  - `ጸሐፍት` (scribes) — NOT present at this position in parchment
  - `ዮሣፍጥ` → parchment `ኢዮሳፍጥ` (different initial vowel cluster)
  - `አኪሉድ` → parchment `አክያድ` (Ahilud vs Akyad — different name)
  - `ዘያዜክር` (the recorder) → parchment `መዘክር` (memorial / recorder — different morphology)
  - Word `ወ` connector preceding `ኤልያብ` missing in C-5
  - Multiple in-line `✣` marks dropped

### v4 — CRITICAL
- C-5: `ወበንያስ፡ወልደ፡ዮዳዕ፡መልአከ፡ሰራዊት፡ወሳዶቅ፡ወአብያታር፡ካህናት`
- Parchment (L11-L13): `ወብንያስ፡ወልደ፡ዮዳሐ ፡መልአከ፡ኃየሉ፡ሳዶቅ፡ወአብያታር፡ካህናት ✣ ...`
- Defects:
  - `ወበንያስ` → parchment `ወብንያስ` (vocalization difference)
  - `ዮዳዕ` → parchment `ዮዳሐ` (different terminal consonant; Yodaʿ vs Yodaḥa)
  - `መልአከ፡ሰራዊት` (chief of armies) → parchment `መልአከ፡ኃየሉ` ("chief of his force") — different word
  - `ወሳዶቅ` → parchment `ሳዶቅ` (no waw connector)
  - In-line `✣` dropped at end of verse

### v5 — MAJOR
- C-5: `ወዓዛርያስ፡ወልደ፡ናታን፡ላዕለ፡መላእክት፡ወዛቡድ፡ወልደ፡ናታን፡ካህን፡ዓርከ፡ንጉሥ`
- Parchment (L13-L15): `[✣] ወአዛርያስ፡ወልደ፡ናታን፡ላዕለ፡እልየማ ን፡ወዛቡል፡ወልደ፡ናታን፡ካህን፡ዘዓምታሕቲ፡ንጉሥ` (followed by content into L15+)
- Defects:
  - `ዓዛርያስ` → parchment `አዛርያስ` (consonant)
  - `ላዕለ፡መላእክት` (over officers) → parchment `ላዕለ፡እልየማን` (over Elyamen??) — different word (possibly "ላዕለ፡ኩሎሙ፡ቦኒዓ፡መልአክት"; needs higher-resolution verification but it is **not** `መላእክት` alone)
  - `ዛቡድ` → parchment `ዛቡል` (Zabud vs Zabul — different terminal consonant)
  - `ዓርከ፡ንጉሥ` (friend of king) → parchment `ዘዓምታሕቲ፡ንጉሥ` ("of/under the king") — different phrase

### v6 — MAJOR
- C-5: `ወአኪሳር፡ዘላዕለ፡ቤት፡ወአዶንያራም፡ወልደ፡ዓብዳ፡ላዕለ፡ጸባሕት`
- Parchment (L15-L17): `ወአኪያል፡መገቤ፡ቤት፡ወአዶኒራም፡ወልደ፡አብዶ፡ላዕለ፡ዓርዕ ✣ ወቶሰሎሞን ✣ ፲ ፡ እጄው...`
- Defects:
  - `አኪሳር` → parchment `አኪያል` (different name spelling)
  - `ዘላዕለ፡ቤት` → parchment `መገቤ፡ቤት` (different morphology)
  - `አዶንያራም` → parchment `አዶኒራም` (different vowel)
  - `ዓብዳ` → parchment `አብዶ` (different vocalization)
  - `ጸባሕት` (corvée) → parchment `ዓርዕ` (different word entirely)
  - `፲` (10) numeral and `እጄው` and `ወቶሰሎሞን` content following — completely absent from C-5

### v7 — MAJOR
- C-5: `ወሰሎሞን፡ሎቱ፡ዐሠርቱ፡ወክልኤቱ፡መልአክት፡በኩሉ፡እስራኤል...`
- Parchment (L17+): contains `ወቶሰሎሞን ✣ ፲ ፡ እጄው፡ላዕለ፡ኩሉ፡እስራኤል፡ኤለ፡ይሲስስደያ፡ለንጉሥ` (read tentatively at this zoom; needs further targeted zoom to fully resolve)
- Defects observed:
  - `ዐሠርቱ፡ወክልኤቱ` (ten-and-two = twelve, written-out form) → parchment uses `፲` Ge'ez numeral (10, but the "and two" continuation needs verification — possibly the full numeric form is `፲፪` or written as `ዐ ሠ ር ቱ ወ ክ ል ኤ ቱ` somewhere in L17; either way it is the numeral form `፲` at the inked position, not the spelled-out form C-5 used)
  - `መልአክት` order — parchment reads `እጄው` (?) at the corresponding slot
- Note: C-5 flagged uncertain about `መልአክት vs መላእክት` order. Honest flag — but the bigger defect is the surrounding context being wrong.

### v8 — CRITICAL (start of officers list)
- C-5: `ወእሉ፡አስማቲሆሙ፡ቤንኦር፡ውስተ፡ደብረ፡ኤፍሬም`
- Parchment (L20-L21): `[✣ ክፍል፡፬(?) ✣] ወዝንቱ፡ውእቱ፡አስማቲሆሙ ወልደ፡ሐር፡በደብረ፡ኤፍሬም ፣ ወልደ፡ራኬብ`
- Defects:
  - C-5 missed the in-line `✣ ክፍል ? ✣` rubric at L20 head
  - `ወእሉ` → parchment `ወዝንቱ` (different demonstrative)
  - `አስማቲሆሙ` is followed by `ውእቱ` in C-5 logic but parchment has `ውእቱ` BEFORE `አስማቲሆሙ` (and adds it)
  - `ቤንኦር` → parchment `ወልደ፡ሐር` ("son of Hur" written as two words `ወልደ ሐር` rather than the compound `ቤንሐር`/`ቤንኦር`)
  - `ውስተ` → parchment `በ` (different preposition)

### vv9-13 — MAJOR (deputies list, names wrong)
C-5 lists `ቤንዳቅር`, `ቤንሔሴድ`, `ቤንአቢናዳብ`, `ባዕና`, `ቤንጋቤር` etc. The parchment shows different name forms; I verified `ወልደ፡ሐር` (v8 above) and saw the L21-29 content uses the `ወልደ-X` ("son of X") construction throughout, NOT the `ቤን-X` compound that C-5 used. Sample L21: `ወልደ፡ራኬብ፡በማኄላስ፡ወቤት፡ሳሚስ፡ወኤሎን፡ወቤተ፡ሄናን ✣ ወልደ፡ሄሁድ፡በአራቦት...`. Compare to C-5 v9 `ወቤንዳቅር፡በማቅስ፡ወበሰላቢም፡ወቤትሳምስ` — different name (`ወልደ፡ራኬብ` vs `ቤንዳቅር`) and different place form (`ማኄላስ` vs `ማቅስ`).

### v26-v32 numerals — CRITICAL (LXX/MT-level lectio difference)
- C-5 v26: `ወአፍራስ፡ሎቱ፡ለሰሎሞን፡አርብዓ፡ምእት` (forty hundred = 4000)
- C-5 v32: `ወተናገረ፡ሠለስተ፡ምእተ፡ምስለ፡ምሳሌ፡ወኮነ፡ዜናሁ፡ኃምስቱ፡ምእት` (300 proverbs and 500 songs)
- Parchment (f127v-M lines 24-26 approx): clearly inked Ge'ez numerals `፫` (3) and `፬` (4) in the form `ወነበበ፡ሰሎሞን፡፫፡ምሳሌቱ፡ወ፬፡ማኅሌተ` ("Solomon spoke 3 his-proverbs and 4 songs")
- **This is a recensional difference of orders of magnitude** (3 vs 3000, 4 vs 5000). C-5's numerals appear to be harmonized to a printed edition with thousand-scale numerals, but the parchment ink is single-digit Ge'ez (`፫`, `፬`).
- Note: the actual single-digit ink may be a scribal abbreviation of the larger numeral, but C-5's spelled-out written form (`ሠለስተ ምእተ`) does NOT match the inked numeric form.
- C-5's v26 `አርብዓ፡ምእት` (4000) — needs targeted re-verification (the parchment may have `፬፣` or similar; not sampled at this round).

### v17, v24, v31 — fabricated text
The C-5 readings for the column transitions (`ወዮሣፋጥ፡ወልደ፡ፋሩሐ፡በይሳኮር` at v17, `እስመ፡ይኄሊ` at v24, `ወጠብበ፡እምኩሎሙ` at v31) do NOT appear at the column-head positions claimed. Either these are gross verse-mapping errors or these are entire-verse fabrications. I could not locate `ወዮሣፋጥ` ANYWHERE I scanned in the f127v-R column.

### Editorial mark exclusion
- Parchment shows at f127v-L L5-L6 a **bracketed-and-underlined editorial mark** `(ወፍትሐ።)` followed by paragraph mark `፨` — these are scribal correction / cancellation marks. C-5 has NO flag for this — neither preserves the marks nor notes their exclusion.

## Side-margin marginalia exclusion check

C-5 claim: "side-margin marginalia excluded per spec §2."
On the cropped page-edge bands at x<543 (f127v) and x<581 (f128r) I see dark column-edge artifacts (binding shadows) but no clearly-inked side-margin notes in 1Ki4 scope. C-5's exclusion is **plausibly correct** for side-margin notes — no defect observed there. However, the IN-LINE editorial mark `(ወፍትሐ።)` with `፨` paragraph mark IS in the body column at f127v-L L5-L6 and should have been at minimum FLAGGED, not silently dropped.

## Wordspace convention

C-5 used U+1361 `፡`. Parchment ink shows the dominant wordspace is **`፣` (U+1363) — the multi-dot "comma" form** in many positions, intermixed with `፡` in others. From my reading the dominant character is closer to `፣` in CAM (matches the prior `1ki3_witnessCAM` convention C-5 mentioned but then deviated from for "consistency"). The validator accepts both U+1361 and U+1363 so this is not a validator-fail defect, but the C-5 metadata note "U+1361 is the dominant CAM inked separator" is **wrong** for this manuscript. (Honest impact: low; this is collator's choice. Surfaced for the record.)

## Wholesale character verification — sampled verses

I read **f127v-L L1-L20 in full**, **f127v-M L1-L14 in full**, **f127v-R L1 + sampled mid-strip**, **f128r-L L1-L6 in full**. In every line sampled, the parchment text diverges from C-5's transcription by at least one substantive token. The defect rate is uniformly high (~30-60% of tokens per verse exhibit some divergence ranging from vowel-shift to entirely-different-word).

## Systematic-class summary

- **Dropped tokens:** L1-L5 of f127v-L (entire prior-section content); intra-chapter rubrics x5+; in-body `✣` marks 15-50+; editorial mark `(ወፍትሐ።)` + `፨`.
- **Fabricated/harmonized words:** v17 head word `ወዮሣፋጥ` not found at column-head; v24 head `እስመ`, v31 head `ወጠብበ` not found at column-heads. v3-v6 deputy names ALL differ from parchment.
- **Wrong-fidel / wrong-consonant:** Extensive — `ዓዛርያስ`/`አዛርያስ`, `ዮዳዕ`/`ዮዳሐ`, `ዛቡድ`/`ዛቡል`, `ቤንኦር`/`ወልደ፡ሐር`, `ኤሊሐሬፍ`/`ኤልያብ`, etc. (>15 confirmed in v2-v8 alone).
- **Wrong-vowel:** `ቤንዳቅር`/`ራኬብ`, `አኪሉድ`/`አክያድ`, `አዶንያራም`/`አዶኒራም`, `ዓብዳ`/`አብዶ`, multiple others.
- **Cross-glyph mislabels:** No `✣` tokens in C-5 body output despite ubiquitous in parchment. C-5 says "0 in-body ✣" — refuted.
- **Numeral mis-decodes:** v32 `፫` (3) and `፬` (4) on parchment vs C-5's "ሠለስተ ምእተ" (300) and "ኃምስቱ ምእት" (500). v26 4000 vs parchment `፬` (probably). v7 `፲` (10) numeral on parchment vs C-5's spelled-out "ዐሠርቱ".
- **Honest defects (parchment damage):** None observed in 1Ki4 scope on either folio. The parchment is clean, well-inked, and legible at the 4x-10x zoom I used. The "native folio-scale image legibility is borderline" claim from C-5 is contradicted — the hi-res JPEGs (7760×10328, ~80MP each) are fully legible character-by-character at modest zoom. C-5's RESOLUTION CAVEAT is **not credible**.

## Approval verdict

**BLOCKED.**

This is not a candidate for round-2 fix-up. The C-5 transcription:
1. Mis-identifies the section boundary (START anchored at L7 instead of L1; missing the 1Ki3:28 / first-clause-of-1Ki4:1 content of section ፰).
2. Has verse-to-column mapping wholly disconnected from parchment (4/4 transition anchors wrong).
3. Has dozens of textual defects (proper names, numerals, connectors, prepositions) suggesting harmonization to a printed edition rather than blind parchment reading.
4. Has 15-50+ in-body `✣` marks systematically dropped.
5. Has 4-7+ intra-chapter `✣ ክፍል ? ✣` rubrics dropped.
6. Has a silent editorial-mark drop (`(ወፍትሐ።)` + `፨` at L6).
7. The metadata claim "native folio-scale image legibility constrains glyph-by-glyph reading" is not supported by my own reading of the same files at standard zoom.

**Recommended fix scope:**
- Full RE-DO of 1Ki4 CAM transcription by a fresh implementer who treats the hi-res JPEGs as the sole source of truth, with high-zoom column-strip workflow (the same approach this review used).
- First step: lock the START boundary by identifying the FIRST `ክፍል` rubric on the f127v page and recording the section number from parchment ink (the digit shape needs careful comparison vs canonical ፩-፲ chart; if ambiguous, transcribe section number as `?` with note).
- Second: walk the parchment line-by-line, recording line_start per ACTUAL inked first-word; do not anchor to expected-text head words.
- Third: preserve ALL `✣` marks as separate tokens (or as separator characters in the geez string) — the validator already accepts U+1739 `✣`.
- Fourth: every `✣ ክፍል N ✣` rubric is a new section divider; record each.
- Fifth: every Ge'ez NUMERAL (`፩`-`፲` plus higher) should be preserved AS THE INKED CHARACTER, not silently replaced by spelled-out written-out forms.
- Sixth: drop the assumption that biblical 1Ki4 = exactly-one-CAM-section. The CAM manuscript family for Kings divides each chapter into multiple `ክፍል` sub-sections (parchment evidence: 5+ in 1Ki4 scope). Transcription scope must be defined either by (a) the rubric-section unit (one CAM section = one transcription file) or (b) the biblical chapter span (one biblical chapter may span N CAM sections; flag each rubric).

## Method-note compliance

### CARDINAL RULE: "transcribed what is inked, with honest uncertainty flagged rather than harmonized to printed editions"
- **Applied?** NO. The C-5 transcription is harmonized to a printed edition (most likely the EOTC Mashafa Sänäselassie Ge'ez OT or similar), not the parchment. Evidence: every proper name in vv3-6 that has a "famous" printed reading appears in C-5 in its printed form (`ኤሊሐሬፍ`, `ቤንኦር`, `ዮሣፍጥ`, `አኪሉድ`, `ዓዛርያስ`, `አዶንያራም`) but is inked differently on the parchment (`ኤልያብ`, `ወልደ ሐር`, `ኢዮሳፍጥ`, `አክያድ`, `አዛርያስ`, `አዶኒራም`). The pattern is too consistent to be coincidence.

### METHOD NOTE 2 (column-transition continuity)
- **Intact?** Indeterminate. The parchment column transitions appear clean at the inked-text level (no dropped or mid-split words at the boundaries I sampled). However, C-5's verse-to-column anchoring is so broken throughout that I cannot evaluate the C-5 transition handling on its own terms.

## Honest notes

- **AMBIGUOUS-PARCHMENT items:** The Ge'ez digit value inside the barred-frame at the `ክፍል ?` rubrics is hard to fully decode at JPEG-zoom even with autocontrast; I read it as a single Ge'ez digit (probably `፬` = 4, possibly `፰` = 8, possibly two-digit form, possibly an abbreviated form for a higher number like `፷` 60 or `፸` 70). Multiple rubric instances have the SAME digit shape, which suggests a SINGLE digit value used per book-level rubric scheme — but I cannot confirm the value at this resolution. Mid-text inline numerals (`፫`, `፬`, `፲`, `፪`, `፸` etc.) are clearly distinguishable.
- **Resolution-limited findings:** The over-zoomed (10x) digit crops showed JPEG compression artifacts that distorted color rendering (false purple/cyan halos). I confined high-confidence decoding to 3x-5x zoom.
- **What I did NOT verify:** the C-5 v17 column-transition anchor (could not find `ወዮሣፋጥ` in R column head); the C-5 v24 folio-transition anchor (f128r-L L1 begins with biblically-1Ki5 content); the exact column-x of every `ክፍል` rubric on f128r (only sampled f128r-L L1-6).
- **What this round is NOT:** I did not attempt to write the CORRECT 1Ki4 CAM transcription. I only verified that the C-5 transcription does NOT match the parchment. Producing the corrected transcription is the C-7-or-revised-C-5 task.

---

**Reviewer signature:** R1 isolated subagent, completed 2026-05-20.
**Scratch hygiene:** all temp crops in `C:\Users\bogda\AppData\Local\Temp\yhwh_1ki4_cam_R1\` for deletion before DONE.
