# Cambridge MS Add. 1570 — scribal-hand topology reference

**Purpose.** Persistent same-scribe reference for every C-6 CAM adversarial reviewer subagent. Read this FIRST on every round so the subagent does not re-derive stroke patterns and known failure classes from scratch. Codified after the 1Ki1–1Ki4 marathon, where the CAM side proved consistently HEAVIER than GG (denser hand; more red-rubric register; line-end glyph-drop ambiguity; column-boundary scripture-omission risk).

**Updating rule.** Append-only. The reviewer who closes a chapter's C-6 (APPROVED CLEAN) appends newly-confirmed facts; stale references struck-through with the refuting round + chapter.

---

## 1. Hand description

Cambridge University Library MS Add. 1570 (1588–89 CE Ethiopian Old Testament). Hi-res images pulled via CUDL IIIF (memory `cudl-iiif-access`); CC BY-NC, attribution "Cambridge University Library." Three-column book hand with red rubrication.

**The CAM hand is denser than GG.** More glyphs per line, more abbreviated forms, more red-rubric register, and a busier `✣`-and-`፡` background that makes the rubric-vs-tinted-separator axis especially hard. The marathon's empirical pattern is `CAM C-6 takes more work than GG C-3` (1Ki3: GG 5 rounds + 4 fixes vs CAM 1 round + adjudicator + fix; but the CAM side's defects are HIGHER-stakes per-instance — homoeoteleuton / boundary omissions / pseudo-archaism).

CAM also carries **marginalia in a side-margin register** — OUT OF SCOPE per design-spec §2. Ignore side-margin notes. Do not transcribe.

The two body cross-glyphs are the SAME as GG (`✣` U+2723 in body; `❈` U+2748 reserved for rubric companions). Body geez contains only `✣`.

## 2. CAM-specific failure classes (in addition to all GG-side classes from `GG_topology.md`)

**Read `GG_topology.md` §2 first** — every fidel-family class there ALSO fires on CAM (the printed-Bible harmonization, the `ለ`/`ስ`, the `ይ`/`ደ`, the `ያ`/`ደ` final-syllable). CAM-specific ADDITIONS:

### Homoeoteleuton scripture-drop ✪✪ (worst CAM-specific class)

A scribe (or the transcriber) skips between two identical-or-similar phrases (`A...A`), losing the intervening text. C-6 R1 of 1Ki2 caught this on `ውስተ መቃብር … ውስተ መቃብር` — losing ≈1 Kings 2:7–9 (the Barzillai-kindness + Shimei-son-of-Gera/Bahurim/Mahanaim/Jordan-oath charge). The transcriber rationalized it as "the CAM recension is shorter here"; ON THE PARCHMENT the full text is present.

**Pattern.** Wherever CAM is materially shorter than GG (or the printed Bible) at a verse span, FIRST check for a homoeoteleuton skip at the boundary. Compare paragraph endpoints in the transcription against the parchment; if a recognizable Hebrew/Greek/Ge'ez stock phrase appears twice with a gap, suspect the skip.

### Column / folio-boundary scripture omission ✪✪

CAM-side equivalent of GG's METHOD NOTE 2. CAM 1Ki1 had **TWO column-turn omissions** that were misread as "recensional minuses" (f126r col1→col2 lost std v15/16; col3→f126v-L lost std v42). After boundary re-trace, the full text was on the page — the original C-5 had skipped lines at the column edge.

**Pattern.** At every column/folio turn, glyph-by-glyph trace continuity. A genuinely short / compressed recension IS the expected distinct-recension signal — but it MUST be PROVEN at the boundary by physical text-continuity, not assumed. The `feedback_reverify_conservative_nogo` lesson applies.

### Dittography fabrication ◎

C-6 R1 of 1Ki2 caught a fabricated `❈` body-cross duplication in v15. Same direction in REGNAL chapters with numeral-stack repeats. Re-verify any apparent dittography at 16x+ before assuming the parchment has it.

### Divine-name harmonization ◎

C-6 R1 of 1Ki2 caught a chapter-wide harmonization of `እግዚእብሔር` (CAM-hand form) to printed-edition `እግዚአብሔር` (19 occurrences). The hand's actual form may differ from the printed Bible's spelling — verify the divine-name fidels at 20x+ against the actual ink, not the expected spelling.

### Pseudo-archaism ✪ (CARDINAL RULE cuts both ways)

C-6 risk inverse to the GG-side risk. Where GG transcribers tend to **smooth toward printed Bible**, CAM transcribers (in this marathon's pattern) sometimes **invent archaisms** that are not on the page. Examples from 1Ki3: `ቅድሜክ-ምስሌክ` 6-word compression where the page had distinct words; `ሠናይ` 1st-order where the parchment had a different order. The reviewer's "this looks more archaic than the printed Bible" instinct is NOT a green light — the CARDINAL RULE applies in BOTH directions: only the inked glyphs are right.

### Sub-rubric numeral disambiguation ◎

CAM 1Ki4 had FOUR intra-chapter `ክፍል N` sub-rubrics (at L20, M8, M19, M27) whose numerals are at the resolution limit between similar Ethiopic numeral forms. AMBIGUOUS-PARCHMENT acceptable.

## 3. Layout / column-register references

CAM folios run **f126r → f127v** (approximate) for Kings 1 + 2 + 3, with f128r reached at 1Ki4–5. The IIIF ToC `structures` MISLABEL the Ethiopic Reigns — locate every chapter by VISION of its narrative, never by ToC label. Anchor: 1 Sam 1 = view 215 = f106r.

**Column reading order:** Left → Middle → Right per recto folio, then top of next folio's Left. A column boundary is the highest-risk position for scripture-omission per §2.

**Recto → verso turn:** the right-column-bottom of `f<N>r` connects to the left-column-top of `f<N>v`. Same continuity rule.

## 4. Rubric `✣ ክፍል N ✣` register

CAM uses fine `ክፍል` (liturgical-subdivision) numerals throughout. The numerals climb `፮ ፯ ፰ ፱ ፲ ፲፩` WITHIN a single modern chapter — these are NOT modern chapter markers. Per memory `samuel-finding`: anchor modern chapter bounds on the NARRATIVE + the coarse `ምዕራፍ` rubric; treat `ክፍል` numerals as noise for chapter bounds.

## 5. Resolution-limited (AMBIGUOUS-PARCHMENT) classes

Same as GG (`GG_topology.md` §5) plus CAM-specific:

- **Sub-rubric numeral form disambiguation** at fine `ክፍል N` positions — multiple instances per chapter; HONEST-flag and carry forward.
- **`✣` rubric vs tinted-`:` separator** axis is HEAVIER on CAM than GG because of the denser red-rubric register. Same resolution-limit applies.

---

**Reviewer pre-flight (every C-6 round):** read §1–§5 of THIS file + §1–§5 of `GG_topology.md` (all the GG fidel-family classes apply to CAM too), then do the chapter-specific reading. After APPROVE, append newly-confirmed references to the relevant section.


## 1 Kings 5 confirmed findings (tau.6.x.4.c, 2026-05-26)

Appended at C-6 close per the self-upgrading-matrix rule (the C-6 reviewer ran read-only this session; controller appends; all Geez below is copied verbatim from the validated witness JSONs).

- **Divine name is the 1st-order form `እግዚእብሔር`** (1st-order initial fidel), NOT the printed 4th-order spelling. Verified on the same line vs the wide 4th-order vowel of the following word (v3/4/5/12). Transcribe the inked 1st-order form; do NOT harmonize to the printed divine name.
- **Column-edge / column-bottom / line-end is THE harmonization hotspot, and it hides inside `uncertain` flags.** On 1ki5 CAM, 3 of the 5 C-6 R1 errors were tokens the transcriber had FLAGGED `uncertain` while its guess drifted to the printed Bible, each at a column edge: v12 (col-bottom) inked `ጽኑዓ` (printed form differs at the first glyph); v8 (col-edge) inked `ኪራሲም` (ending misread); v17 (line-end) inked `ዘኢኮነ` (negation dropped). **Reviewer rule: treat every `uncertain`-flagged token as a SUSPECTED harmonization and re-adjudicate it against the ink** -- the flag marks exactly where the transcriber guessed, and guesses drift to the printed form.
- **Dropped function/content words at line-junctions:** v15 had dropped the conjunction `ወ` before the 2nd myriad-numeral; v16 had dropped the content word `ስዶማን` at a line-junction. Trace running text across every column/line break.
- **Myriad-numeral class:** large counts are red, bracketed numerals (`፸ ፻` / `፹ ፻` = 70k / 80k). The hundred-vs-myriad mark is at the resolution limit -- transcribe the inked hundred-mark + flag `damaged`; do NOT silently promote to a myriad mark.
- **Correction-oval:** a hand-drawn ellipse may encircle a word (v1) with NO marginal replacement/caret -- transcribe the inked main-line glyphs + flag uncertain; do NOT smooth to the printed form.
- **Segmentation:** CAM segmented 1ki5 into 18 verses (~ the printed division) vs GG's compressed 13 -- in this family CAM is the finer-segmented, printed-closer witness.
