# Curated `word`-kind study audit (the owner's own Hebrew/Greek word studies)

Companion to the [auto-note quality audit](2026-06-06-auto-note-quality-audit.md),
which explicitly flagged that the **curated multi-sentence word studies belong to a
separate `kind="word"` set** and must get their own purpose-aware audit rather than
being assumed-covered by the auto-note PASS. This is that audit.

## 1. Intro

**What this kind is.** 149 notes, `kind="word"`, across the Torah + Former Prophets
+ 1 Enoch (gen 52, exo 26, lev 14, num 13, deu 11, 1sa 11, jdg 5, 1ki 4, 2sa 3,
jos 3, rut 3, 1en 2). These are **the project owner's own hand-written scholarship**
— provenance `User original` (110) or `User paraphrase; references <sources>` (39:
LXX, Rashi, Genesis Rabbah, Targum Onqelos, Ugaritic, Enuma Elish, Mishnah/Sifra,
Augustine, Aquinas, Maimonides, Westermann/Walton/Sailhamer, et al.). Each is a
deliberate scholarly micro-essay on one word: lemma + transliteration + gloss +
grammatical / theological / comparative-Semitic discussion (242–1,164 chars, median
464). 124 lead with pointed Hebrew, 3 with Greek (LXX notes in Genesis), 22 are
romanized-only.

**Purpose-aware bar.** Unlike the terse auto-notes, brevity is *not* the design
here — these are meant to be substantive. So they are judged as finished, publishable
scholarly notes: accurate Hebrew/Greek, faithful transliteration, sound and
correctly-attributed claims, no overreach stated as settled fact. **Defensible
scholarly positions are not defects** — biblical word studies legitimately take
sides, and a recognized reading is not penalized even where another is arguable.

## 2. Method

- **Deterministic markup pre-check (full population, exact).** All 149 bodies were
  scanned for scaffold remnants, tag/paren balance, truncation, attribution, and
  template conformance. **100% clean** — 0 `[Reviewer]`/`TODO` remnants, 0 `<strong>`/
  `<em>`/paren imbalance, 0 trailing-ellipsis truncation, 0 missing attribution,
  100% open with a `<strong>` lemma lead-in. The RX Phase 1 scaffold strip never
  touched these curated notes, and nothing is malformed at the markup layer.
- **Judgment layer (full population, adversarial).** All 149 split into 15
  book-contiguous chunks; each chunk read by **two diverse lenses** — a Hebraist /
  linguistic lens (script, pointing, transliteration, morphology, gloss) and a
  source-scholarship lens (rabbinic/LXX/ANE/patristic attributions, factual and
  cross-reference claims, overreach). **Every flagged issue was then independently
  adversarially verified** by a skeptic prompted to *refute* it (the verifier's
  verdict governs — false flags against the owner's own work are costly). A final
  **completeness critic** scanned the whole corpus for systematic patterns the
  per-chunk finders would miss. 56 agents, ~1.75M tokens (run `wf_1520330d-942`).

## 3. Headline

**The corpus is scholarship-grade.** Across 149 notes the audit found **0 blocking
and 0 major defects**. The 20 confirmed issues (19 distinct) are **16 minor + 4
cosmetic** — precise, narrow refinements (a missing dagesh, a dropped qualifier on an
"appears only" claim, a midrash pinpoint off by a section). The adversarial layer
**refuted 5 candidate flags** as false (the owner was right). The finders explicitly
praised **~80 of the notes** as exemplary — flawless pointing, accurate LXX/Akkadian/
Ugaritic citations, contested etymologies responsibly hedged. This is a strong body
of original work; everything below is fine-tuning, not repair.

| Tier | Count | Nature |
|---|---|---|
| Blocking / major | **0** | — |
| Minor (verified) | 14 distinct | factual/cross-ref slips, transliteration, misattribution, overreach, lemma–verse |
| Cosmetic (verified) | 5 distinct | single missing points, internal-inconsistency glosses |
| Completeness-critic additions (1-pass) | ~5 | Greek-romanization class, tsade convention, versification, Babel pair, gen 16:13m |
| False flags refuted | 5 | the owner was correct |

## 4. Verified findings (doubly-adversarial: flagged by a lens, confirmed by a skeptic)

### 4.1 Transliteration / pointing

- **gen 1:21 — `תַּנִינִים` is missing the dagesh forte in the nun** (minor). The
  romanization "Tanninim" doubles the n (gemination), but the pointed Hebrew carries
  a dagesh only in the tav (lene), not the nun, so it reads *ta-nî-nîm*. The MT is
  `תַּנִּינִם`. **Fix:** point the nun — `תַּנִּינִים` (or defective `תַּנִּינִם`).
- **gen 5:29 — "Noḥa" inverts the furtive pataḥ of `נֹחַ`** (minor). The form is
  /ˈno.aḥ/ = **"Noaḥ"** (source of English "Noah"); "Noḥa" places the vowel *after*
  the ḥet (a metathesis that would suit `נֹחָה`, "she rested"). The note's own title
  uses "Noach." **Fix:** "Noaḥ (נֹחַ)".
- **deu 10:16 — "Mulot" should be "maltem"** (minor, confidence 0.97). The pointed
  `מַלְתֶּם` is unambiguously *maltem* (the MT form, "you shall circumcise"). "Mulot"
  would need a different vocalization not present in the verse. **Fix:** "Maltem"
  (or "U-maltem") `orlat l'vavkhem`.
- **gen 1:2c — "Ruḥ" should be "Ruaḥ"** (cosmetic). `רוּחַ` carries a furtive pataḥ
  → *ruaḥ*; "Ruḥ" reads like the Arabic *rūḥ*. The sibling note gen 1:2n already
  renders it "Ruaḥ." **Fix:** harmonize to "Ruaḥ."
- **exo 20:13 — `תִרְצָח` is missing the dagesh lene in the tav** (cosmetic). MT =
  `תִּרְצָח`. Consonants and the romanization "tirtzach" are correct; one missing
  point. **Fix:** `תִּרְצָח`.

### 4.2 Factual / cross-reference

- **gen 1:2c — `raḥef` "appears elsewhere only in Deut 32:11" omits Jer 23:9**
  (minor). The root `רחף` occurs three times in the MT: Gen 1:2 (Piel, "hover"),
  Deut 32:11 (Piel, eagle), **Jer 23:9 (Qal, bones "tremble")**. The claim is true
  only if scoped to the Pentateuch or the "hover" sense — and **the sibling gen 1:2n
  scopes it correctly**: "only one other place in the Pentateuch: Deut 32:11." The
  owner knows the precise form; gen 1:2c just dropped the qualifier. *(Flagged by
  both lenses independently.)* **Fix:** add the qualifier, matching gen 1:2n.
- **exo 19:5 — `segullah` "of Israel only in Deut 7:6, 14:2, 26:18, Mal 3:17" omits
  Ps 135:4** (minor). Ps 135:4 ("Israel for his *segullah*") is precisely an
  of-Israel/elective use. **Fix:** add Ps 135:4 (or soften "only" → "chiefly").
- **deu 10:16 — heart-circumcision "appears here for the first time" — Lev 26:41 is
  earlier** (minor). Lev 26:41 already has the uncircumcised-heart metaphor; Deut
  10:16 is the first *command* to circumcise the heart. **Fix:** credit Lev 26:41,
  or narrow the claim to "the first command."
- **1sa 2:12 — `b'nei beliyya'al` "the first occurrence of the formula in the OT" —
  it occurs earlier** (minor). The construct phrase is in Deut 13:14 and Judg 19:22;
  the bare noun in Deut 15:9. **Fix:** drop/qualify the priority claim.
- **gen 6:8 — the Jer 31:2 `matza chen` subject is labelled "the Servant" — it is
  Israel/the remnant** (minor). Jer 31:2 has no servant figure; "the Servant" falsely
  evokes the Isaianic Servant Songs. **Fix:** relabel "the wilderness remnant / Israel
  (Jer 31:2)."
- **gen 3:24b — "the plural kerubim appears 91 times" — 91 is all forms combined**
  (cosmetic). 91 = singular (~26) + plural (~62). **Fix:** "the word kerub/kerubim
  appears about 91 times … in all forms."

### 4.3 Misattribution (source pinpoints)

- **gen 2:7b — Genesis Rabbah 14:9 "reads neshamah as the highest" — it is the 3rd
  of 5** (minor). The midrash lists nefesh/ruach/neshamah/chayah/yechidah; in the
  classic scheme neshamah is the middle level, with chayah and yechidah above. The
  citation itself is correct. **Fix:** "treats neshamah as a distinguished/elevated
  soul-word" (drop "the highest").
- **gen 7:22 — fish-spared-the-flood teaching attributed to "Sifra on Lev 11:46"**
  (minor). The teaching is genuine but its source is **b. Sanhedrin 108a** (cited by
  Rashi ad loc.) / Genesis Rabbah; the Sifra on Lev 11:46 is a halakhic midrash on
  dietary classification, unrelated to the Flood. **Fix:** re-attribute to b. Sanhedrin
  108a / Rashi.
- **num 19:2 — Solomon-couldn't-understand-it pinpointed to "Bemidbar Rabbah 19:1" —
  it is 19:3** (minor). The chapter (19, Chukat) is right; the section is off.
  **Fix:** "Bemidbar Rabbah 19:3" (or cite generically "Bemidbar Rabbah, Chukat").
- **exo 25:8 — John 1:14 `eskēnōsen` "echoes this verse via the LXX" — the LXX of
  Exod 25:8 uses `ὀφθήσομαι`, not a σκηνόω form** (minor). The σκηνή/eskēnōsen
  resonance runs through the broader tabernacle vocabulary and the Hebrew `שָׁכַן`,
  not this verse's Greek. The sibling exo 25:8m gets it right ("the same root").
  **Fix:** drop "via the LXX."

### 4.4 Overreach (contested stated as settled)

- **deu 14:21 — the Ugaritic "boil a kid in milk" rite (KTU 1.23) presented as
  documented fact** (minor). The reading rests on a conjectural reconstruction (the
  original editor called it "simply conjectural") that later scholarship (Herdner
  1963; Dietrich/Loretz/Sanmartín 1976) largely abandoned; the text never specifies
  the kid is boiled in its *mother's* milk. **Fix:** hedge — "some earlier scholars
  read … ; that reading is now largely rejected."
- **1sa 10:1 — "Saul is the first `mashiaḥ` in the canonical narrative"** (minor).
  The anointed *priest* (`ha-kohen ha-mashiaḥ`, Lev 4:3, 5, 16; Aaron, Lev 8:12)
  precedes him canonically. The intended point is the first *royal* anointed. **Fix:**
  "the first king designated YHWH's anointed."

### 4.5 Lemma–verse mismatch

- **lev 20:26m — note keyed to Lev 20:26 but its lemma `הִבְדַּלְתִּי` is in Lev
  20:24** (minor). Lev 20:26 reads `וָאַבְדִּל` (*va'avdil*, wayyiqtol); the perfect
  `הִבְדַּלְתִּי` (*hivdalti*) is v.24. Same root (`בדל`), so the separation theme is
  intact, but the cited form belongs to the adjacent verse. **Fix:** re-key to lev
  20:24, or change the lemma to `וָאַבְדִּל`, or cite both vv.24+26 explicitly.

### 4.6 Internal inconsistency

- **1en 6:3 — Semjaza glossed two ways in one note** (cosmetic): "my name has seen"
  (title) vs "the name has seen" (body). Both parses of `שמיחזה` (*šem* vs *šem-î*)
  are defensible; the flip is just unreconciled. **Fix:** pick one, or note the
  `-î` dependency.

## 5. Completeness-critic additions (corpus-wide patterns; one verification pass + spot-checked here)

These came from the final critic scan rather than the doubly-adversarial loop; I
re-verified each against the actual note bodies, but they have not had a second
independent skeptic, so treat the *severity* as provisional.

- **Greek-romanization defect class — `gen 1:1b`, `gen 2:8`** (+ gen 1:2c "Ruḥ"
  above). The 3 Greek-script Genesis notes mishandle diphthongs/letters: gen 1:1b has
  **"ktiżeīn"** (κτίζειν → "ktizein"; the `ż` and macron-`ī` are bogus) and
  **"epoīēsen"** (ἐποίησεν → "epoiēsen"); gen 2:8 has **"paradēisos"** (παράδεισος →
  "paradeisos"; the `ει` diphthong wrongly macronized). The per-chunk Hebraist lenses,
  focused on Hebrew, systematically under-weighted Greek. **Fix:** normalize Greek
  romanization (`ει`→ei, `οι`→oi, `ζ`→z, `η`→ē).
- **Tsade (`צ`) romanization split — ~16 notes** (cosmetic, house-style). Rendered
  **"ts"** in 5 Genesis notes (tselem, tsela, yatsar, vayyitser) but **"tz"**
  everywhere else (Tzara, Tzur, ratzach, tirtzach, tzitzit, matzah, B'tzal'el,
  Yitzḥaq). Not an error — a consistency choice. **Fix:** pick one convention corpus-
  wide (the "tz" majority is the obvious target).
- **gen 16:13m — "Hagar … the only person in scripture who [names God]"**
  (contestable overreach; **verify before changing**). This is a widely-repeated
  observation, but arguably qualifiable — Abraham invokes/coins "El Olam" (Gen 21:33)
  and "El Elyon" (14:22), Jacob names an altar "El-Elohe-Yisrael" (33:20). The owner's
  claim reflects a real scholarly trope (Hagar as the only one to *give God a name*);
  if kept, consider "the only person who gives God a name" with that nuance.
- **gen 11:9 / gen 11:9p — Babel etymology unharmonized** (cosmetic): "Bab-ilu / gate
  of *the* god" vs "Bāb-ilim / gate of god." Both Akkadian forms are attested; the
  paired notes simply weren't reconciled. **Fix:** harmonize the pair.
- **Versification convention — `jdg 13:18` uses MT "Gen 32:29"** where gen 27:36 and
  gen 35:10 use English "Gen 32:28" for the same pericope (cosmetic). The corpus
  otherwise uses English numbering for cross-refs. **Fix:** "Gen 32:28" for
  consistency.
- *(Out of content scope, noted by the critic:)* 14 Genesis notes carry a descriptive
  `label` while their `title` field is the generic "Hebrew" — likely an extraction
  artifact, not a content defect.

## 6. False flags the adversarial layer refuted (the owner was right)

Recorded to show the verification did its job — these are **not** defects:

- **exo 2:23** (`צְעָקָה` as the outcry lemma) — a defensible representative motif-word
  for the verse's cry, not a wrong lexeme.
- **lev 1:1** (×2) — the Sifra attribution and the contrast with Balaam ("Numbers 22,
  where God only speaks") are correct.
- **num 13:33** — the Anakim/Execration-Texts link (Iy-ʿanaq, Berlin group) is real
  and appropriately framed.
- **1sa 25:29** — the `תנצב״ה` funerary-acronym derivation from `tz'ror ha-chayyim`
  is accurate.

## 7. Strengths (the dominant story)

The finders flagged ~80 notes as exemplary. A representative sample: **gen 1:2n**
(`רוּחַ אֱלֹהִים מְרַחֶפֶת` pointed flawlessly, the raḥef claim correctly bounded);
**gen 16:13m** (faithfully reproduces the genuinely unusual MT pointing `רֳאִי` with
ḥataf-qamats); **gen 32:28m** (correct *sin*-dot on `יִשְׂרָאֵל`); **exo 3:14** (correct
segol-pointing on `אֶהְיֶה`, accurate `egō eimi ho ōn`); **lev 16:8** (all four Azazel
readings accurately characterized); **deu 6:4** (all three Shema renderings presented
as grammatically possible); **jdg 12:6** (the Shibbolet samekh/shin dialect test);
**num 6:24-26** (the 3/5/7-word priestly-blessing structure verified exact);
**gen 2:8** (paradeisos as a Persian loan via Xenophon — etymology fully accurate);
**deu 32:4** (Tsur "six times in this chapter" — verified). Contested topics
(tehom/Tiamat, Pesach/pasāḥu, Azazel, El/Yahweh) are handled with hedging, not
overreach.

## 8. Prioritized remediation (all audit-only — no `content/notes/` was edited)

None blocks publication. In rough order of reader-facing value:

1. **Correct the 4 factual/cross-ref "only/first" claims** (gen 1:2c raḥef, exo 19:5
   segullah, deu 10:16 first-metaphor, 1sa 2:12 first-formula) — each is a one-clause
   qualifier; the owner's sibling notes often already have the right wording.
2. **Re-attribute the 3 source pinpoints** (gen 7:22 Sifra→Sanhedrin, num 19:2
   19:1→19:3, exo 25:8 drop "via the LXX") and soften gen 2:7b ("highest"→"elevated").
3. **Fix the 3 transliteration slips** (gen 1:21 dagesh, gen 5:29 Noaḥ, deu 10:16
   maltem) and re-key/relabel **lev 20:26m**.
4. **Hedge the 2 overreaches** (deu 14:21 Ugaritic, 1sa 10:1 first-mashiaḥ).
5. **Normalize the Greek romanizations** (gen 1:1b, gen 2:8, gen 1:2c) and the
   **tsade ts/tz** convention; harmonize the **Babel** and **raḥef** sibling pairs and
   the **32:28/32:29** versification — a single consistency pass.
6. Leave **gen 16:13m** unless the owner wishes to nuance "names God."

Because several defects are *internal inconsistencies* (a sibling note already states
the correct form), a useful root-cause check is to diff paired/sibling notes on the
same lemma and reconcile them.

## 9. References

Sources the notes engage (all PD / standard scholarly): the Masoretic Text (BHS/WLC),
the Septuagint, Targum Onqelos, Genesis/Bemidbar Rabbah, b. Sanhedrin & b. Ḥagigah,
the Sifra, BDB & HALOT lexica, Strong's, Ugaritic (KTU), the Egyptian Execration
Texts, and the standard critical literature cited per note. Hebrew/Greek facts above
were re-verified against BDB/HALOT and the MT/LXX.

---

*Read-only audit produced 2026-06-05 (Mac lane) by a verified multi-agent pass
(`wf_1520330d-942`): all 149 `kind="word"` notes, full population, two diverse lenses
per chunk, every flag adversarially refuted (verdict governs), plus a completeness
critic — 56 agents. **Audit only — no `content/notes/` were edited.** Companion to
[2026-06-06-auto-note-quality-audit.md](2026-06-06-auto-note-quality-audit.md).*
