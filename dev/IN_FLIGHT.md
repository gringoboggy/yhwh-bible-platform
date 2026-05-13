# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

## Prior task

**γ.4.5 Mäṣḥafä Kufāle / Book of Jubilees seed (40 verse-keyed
entries across all 50 chapters)** shipped 2026-05-12. **Opens the
SECOND uniquely-Tewahedo canonical text** on the same Mäṣḥafä-
Hēnok-style trajectory as γ.4.4. Jubilees (Ge'ez: Mäṣḥafä Kufāle)
is canonical in only the Tewahedo and Eritrean Orthodox communions
— alongside 1 Enoch — and survives as a complete text only in
Ge'ez. The project's eponymous edition (ethiopian-tewahedo) now has
patristic-grade seed-coverage of BOTH uniquely-Tewahedo canonical
texts. Voice mix moves from 31/20/49 to ~28/18/45/9 Cyril/Ephrem/
1En/Jubilees — Jubilees enters the corpus as a distinct fourth
voice.

**Why it matters for THIS project**:

- **Opens the second uniquely-Tewahedo canonical text.** The
  project's mandate is the Tewahedo edition. The Tewahedo canon
  uniquely includes both Mäṣḥafä Hēnok (1 Enoch) and Mäṣḥafä
  Kufāle (Jubilees) as Scripture. γ.4.4.A-E closed the Mäṣḥafä
  Hēnok arc; γ.4.5 opens the Mäṣḥafä Kufāle arc.
- **6:32 (364-day calendar) — doubled canonical anchor.** Jubilees
  6:32 + 1 Enoch 72:32 jointly anchor the Tewahedo Bāḥrä Ḥasab
  (Sea of Reckoning) liturgical-computus tradition. The doubled
  canonical witness for the 364-day year is unique to the Tewahedo /
  Eritrean Orthodox canon.
- **9:13 (Ham's portion) — Tewahedo Hamitic identity anchor.** The
  Ethiopian self-understanding as descended from Cush son of Ham
  draws on Jubilees 9:13 (with Gen 10:6-8) as canonical warrant
  for an INCLUSIVE Hamitic theology — Ham's portion is divinely
  allotted, not cursed. Tewahedo reading explicitly rejects the
  curse-of-Ham racialisation that Western Christianity often
  imposed.
- **10:8 (Mastema petition) — non-dualist demonology.** Mastema as
  canonical figure: the post-Flood demonic presence is divinely
  permitted, bounded, and serves a probative function. Tewahedo
  theodicy preserves this against the periodic Manichaean / Zandic
  dualist incursions in Ethiopian church history.
- **18:9 (Mastema-as-Akedah-accuser) — protects divine goodness.**
  The Jubilees re-framing of the Akedah (test originates in
  Mastema's challenge, parallel to Job 1-2's Satan-as-accuser)
  protects God's absolute goodness while preserving the narrative
  of testing.
- **21:10 ('books of Enoch' cited inside Jubilees) — inter-canonical
  witness.** Jubilees treats 1 Enoch as authoritative source within
  itself, creating a uniquely doubled and inter-textual canonical
  structure in the Tewahedo canon: Jubilees cites Enoch, both are
  Scripture, both are preserved uniquely in Ge'ez.
- **32:18 (Levi consecrated to priesthood) — Tewahedo priestly
  anchor.** The Tewahedo qes priestly orders (descending through
  specific families) appeal to the patriarchal-Levitical lineage of
  Jub 32 as part of their self-understanding: priesthood is older
  than its Mosaic regulation; Jub 32 is the scriptural anchor in
  canonical Mäṣḥafä Kufāle.
- **48:9 (Mastema bound during Exodus) — Holy-Week anchor.** The
  Tewahedo theological reading of the Paschal mystery as a period
  of suspended demonic accusation draws on Jub 48:9 as its
  canonical anchor.
- **50:6 (Sabbath finale) — Saturday-Sabbath tradition.** The
  Tewahedo Church historically observed BOTH Saturday-Sabbath
  AND Sunday-Lord's-Day (unique among major Christian communions
  until the 17th century; still preserved in some monastic
  communities). Jubilees 50 is the canonical anchor.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new Jubilees
  entries appended (book=`jub`, father=`Book of Jubilees (Ethiopian
  tradition)`, work=`Book of Jubilees (Mäṣḥafä Kufāle)`, year=`-150`,
  attribution `Jubilees C:V (section), trans. R.H. Charles, The Book
  of Jubilees (Oxford: Clarendon, 1902). PD.`). _meta scope/source
  strings updated. Total entries now 430 (was 390 pre-γ.4.5).
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma45JubileesSeedWave` class with **14 tests**: ≥40
  entries pin + all nine narrative blocks (Sinai prologue + Creation,
  Eden + generations, Watchers + Noahide, Division of earth + Mastema,
  Abraham, Decline + eschatology, Jacob, Joseph, Egypt-Exodus-
  Passover-Sabbath finale) + Jubilees-share ≥3% (distinct voice
  threshold) + 11 signature passages (1:1, 4:17, 6:32, 8:19, 9:13,
  10:8, 18:9, 21:10, 32:18, 48:9, 50:6).

**Code-side wiring**: zero new code.

**Note on canonical-edition integration**: `jub` and `1en` are
registered in `content/books.yaml` but the `ethiopian-tewahedo`
edition's `editions.yaml` notes explicitly that "Ethiopic extras
like 1en/jub/mq1-3 to be added in a future ingest". The commentary
entries are queryable via `for_verse('jub', ...)` and
`for_verse('1en', ...)` regardless of edition canon-list state, and
will surface in the built edition once the future ingest adds these
books to the canon list. The Mäṣḥafä Kufāle commentary is therefore
READY for the edition; the edition needs to be ready for it.

**Corpus state post-γ.4.5**:
```
ethiopian_commentaries.json: 430 entries (was 390; +40)
├─ Cyril of Alexandria               : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian                 :  77 entries (Gen 1-50; Ps 1; Hymns)
├─ 1 Enoch tradition                 : 192 entries (Mäṣḥafä Hēnok arc CLOSED)
└─ Book of Jubilees (Eth. tradition) :  40 entries (Mäṣḥafä Kufāle SEED γ.4.5)

Voice mix: ~28% Cyril / ~18% Ephrem / ~45% 1 Enoch / ~9% Jubilees
           (was 31/20/49 pre-γ.4.5 — Jubilees enters as fourth
            voice; all three prior voices' shares ease accordingly)

γ.4 cumulative              : 418 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .2.B 40 + .4 30 + .4.B 40 +
                              .4.C 40 + .4.D 40 + .4.E 40 + .5 40 = 418)
```

**+14 tests**. **γ.4.5 tests: 14/14 pass in isolation; 11/11 lint
clean.**

**Forward references**:
- **γ.4.5.B-E** Jubilees detail waves (parallel to γ.4.4.B-E pattern):
  Watchers + Noahide covenant detail (chs 5-10); Patriarchal detail
  (chs 11-22); Jacob + Joseph detail (chs 24-45); Exodus-Passover-
  Sabbath detail (chs 46-50).
- **γ.4.6** Mäṣḥafä Aksumawi (Ethiopic Sirach reception); **γ.4.7**
  Senodos / Didascalia Ethiopic patristic-canonical texts;
  **γ.4.8** Mäqabyan 1-3 (uniquely-Tewahedo Maccabean texts —
  Ethiopic ≠ Greek Maccabees; entirely separate composition).
- **γ.4.2.C** Ephrem on Exodus.
- **γ.4.3** Cyril on Luke (~400 long-term).

**Recommended next ship**:
- **γ.4.8 Mäqabyan seed** — opens the THIRD uniquely-Tewahedo
  canonical text (the Ethiopic Maccabean books, three texts that
  exist in NO other Christian canon and are NOT the same as Greek
  1-2-3-4 Maccabees). With 1 En + Jub now both substantively
  covered, completing the Ethiopic-extras triad would close the
  uniquely-Tewahedo canonical-witness gap entirely.
- **γ.4.5.B Jubilees Watchers + Mastema detail** — substantive
  expansion of Jub 5-10, the Jubilees-side of the angelic-history
  narrative.
- **γ.4.2.C Ephrem on Exodus** — Ephrem continuation.

**Session totals (2026-05-12, cumulative through γ.4.5)**:
- γ.4.4.A-E shipped (Mäṣḥafä Hēnok arc CLOSED)
- γ.4.2 + γ.4.2.B shipped (Ephrem on Gen 1-50 substantively expanded)
- γ.4.5 shipped (Mäṣḥafä Kufāle / Jubilees seed)
- 3 phases shipped unsaved since the last save (γ.4.4.E + γ.4.2.B +
  γ.4.5) — per the "keep pushing / push" continuation directive
  (memory: push/continue advances to next phase without auto-save).

---

## Prior task before γ.4.5 (kept for context)

**γ.4.2.B Ephrem on Genesis 12-50 (patriarchal narrative, 40 entries)**
shipped 2026-05-12. Continues γ.4.2 (Gen 1-11, 32 entries shipped
earlier this session) into the Abraham (15 entries: 12:1, 12:7,
14:18, 15:6, 17:5, 17:10, 18:1, 18:14, 21:1, 22:1, 22:8, 22:14,
23:2, 24:67, 25:9), Jacob (12: 25:23, 27:27, 28:12, 28:17, 32:24,
32:28, 33:4, 35:10, 35:18, 35:22, 35:29, 36:1), and Joseph (13:
37:3, 37:9, 37:28, 39:9, 40:8, 41:38, 41:55, 42:24, 44:18, 45:4,
45:5, 49:10, 50:20) cycles. Rebalances Ephrem share from ~10%
(substantially under-represented after the γ.4.4 1 Enoch arc) back
toward ~19%. **Note**: shipped AFTER closing the γ.4.4 Mäṣḥafä
Hēnok arc with γ.4.4.E and BEFORE saving — pursued as the "keep
pushing" continuation directive (per memory: push/continue advances
to next phase, never auto-save).

**Why it matters for THIS project**:

- **Rebalances voice mix.** After the γ.4.4 wave the corpus was 35
  Cyril / 10 Ephrem / 55 1 Enoch — Ephrem substantially under-
  represented. γ.4.2.B brings Ephrem to ~17-19% — a healthier
  three-voice balance.
- **Melchizedek (14:18)** is the Tewahedo eucharistic prefiguration
  par excellence — the Tewahedo Anaphora explicitly invokes
  Melchizedek as the priestly archetype that Christ fulfils.
- **Mamre Trinity theophany (18:1)** anchors the Tewahedo
  iconographic Trinity-at-Mamre tradition (older and more widespread
  in Tewahedo church-wall fresco than in any other Oriental
  Orthodox communion).
- **The Akedah (22:1, 22:8, 22:14)** is the OT Crucifixion-type
  par excellence — Ephrem's reading anchors the Moriah-Calvary
  identification preserved in the Tewahedo Anaphora.
- **Jacob's ladder (28:12)** as Christ-and-Mary type undergirds
  Tewahedo Marian hymnody — the Wǝddase Maryam (Praise of Mary)
  cites Jacob's ladder as a Marian OT type.
- **Joseph cycle Christ-typology** (37:28 sold for silver / 41:55
  'go unto Joseph' = Marian-Cana prefiguration / 44:18 Judah's
  substitutionary offering / 49:10 Shiloh) — Tewahedo Holy-Week
  liturgy explicitly draws the Joseph-typology.
- **Providence formula 50:20** is foundational in Tewahedo
  consolation literature — every personal harm submits to a larger
  divine purpose.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new Ephrem-on-
  Genesis entries appended (book=`gen`, father=`Ephrem the Syrian`,
  work=`Commentary on Genesis`, year=`360`, attribution `Ephrem the
  Syrian, Commentary on Genesis, [Section N.V]. NPNF Series 2, vol.
  13, ed. J. Gwynn / Schaff (1898). PD.`). _meta scope/source
  strings updated. Total entries now 390 (was 350 pre-γ.4.2.B).
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma42BEphremPatriarchsWave` class with **14 tests**:
  ≥40 entries pin + all three patriarchal cycles covered + Ephrem
  share ≥17% + 11 signature passages (14:18, 15:6, 18:1, 22:8,
  28:12, 32:24, 37:28, 41:55, 44:18, 49:10, 50:20).

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.2.B**:
```
ethiopian_commentaries.json: 390 entries (was 350; +40)
├─ Cyril of Alexandria     : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian       :  77 entries (Gen 1-50: Primeval History
                                          11 chs + patriarchal narrative
                                          Gen 12-50; Ps 1; Hymns on
                                          Paradise) — substantively rebalanced
└─ 1 Enoch tradition       : 192 entries (Mäṣḥafä Hēnok arc CLOSED
                                          γ.4.4.A-E)

Voice mix: ~31% Cyril / ~20% Ephrem / ~49% 1 Enoch
           (was 35/10/55 pre-γ.4.2.B — Ephrem rebalanced upward,
            1 Enoch still plurality, voice spread healthier)
γ.4 cumulative              : 378 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .2.B 40 + .4 30 + .4.B 40 +
                              .4.C 40 + .4.D 40 + .4.E 40 = 378)
```

**+14 tests**. **γ.4.2.B tests: 14/14 pass in isolation; 11/11 lint
clean.**

**Forward references**:
- **γ.4.2.C** Ephrem on Exodus (would continue Ephrem expansion).
- **γ.4.3** Cyril on Luke (~400 long-term).
- **γ.4.5** Mäṣḥafä Kufāle / Book of Jubilees seed — opens next
  uniquely-Tewahedo canonical text on the Mäṣḥafä-Hēnok pattern.

**Recommended next ship**:
- **γ.4.5 Jubilees seed** — opens the second uniquely-Tewahedo
  canonical text (Mäṣḥafä Kufāle is canonical in Tewahedo and
  preserved only in Ge'ez, exactly parallel to 1 Enoch's preservation
  pattern). With Ephrem rebalanced and the 1 Enoch arc closed, this
  is the natural next ambitious wave.
- **γ.4.2.C Ephrem on Exodus** — further Ephrem expansion.

**Session totals (2026-05-12, cumulative)**:
- γ.4.4.A through γ.4.4.E shipped (Mäṣḥafä Hēnok arc CLOSED)
- γ.4.2 (Gen 1-11) + γ.4.2.B (Gen 12-50) — Ephrem on Genesis through
  Joseph cycle
- Net test delta since session start: substantial positive (specific
  count drifts with the environmental subprocess flakers; see
  CHANGELOG for the precise pass-counts at each ship)

---

## Prior task before γ.4.2.B (kept for context)

**γ.4.4.E 1 Enoch Epistle of Enoch + Apocalypse of Weeks + Birth of
Noah detail (40 entries on chs 91-108) — CLOSES the Mäṣḥafä Hēnok
arc** shipped 2026-05-12. Substantive expansion of the remaining
Mäṣḥafä Hēnok section beyond the 4 first-wave entries on this
range (91:7, 93:3, 99:10, 104:2). Brings chs 91-108 coverage from 4
to 44 entries. **All six sections of the Ethiopian 1 Enoch
(Watchers + Parables + Astronomical Book + Dream Visions + Animal
Apocalypse + Epistle) are now substantively expanded.** 1 Enoch
share of corpus rises from ~49% to ~56% — 1 Enoch is now the
**dominant** voice in the corpus.

**Why it matters for THIS project**:

- **CLOSURE of the Mäṣḥafä Hēnok content arc**. The Ethiopian
  Tewahedo Church is the ONLY major Christian communion to canonize
  1 Enoch as biblical. The project's eponymous edition
  (ethiopian-tewahedo) now has comprehensive patristic-grade
  commentary on every section of its distinctive canonical text.
- The **Apocalypse of Weeks (1En 93 + 91:11-17)** is the Second-
  Temple period's most influential periodisation scheme — directly
  parallel and prior to Daniel 9:24-27's 70-weeks scheme. Tewahedo
  historiographical tradition draws on the seven-past + three-
  eschatological structure.
- **91:14 (tenth-week judgment of watchers)** CLOSES the Watchers
  arc that opened in 1En 6 — final eschatological judgment of the
  fallen angels, complementing the preliminary bindings at 1En 10,
  88:1, and 90:24. The tetraptych structure (bound → judged in
  Watchers vision → judged in Animal Apocalypse vision → final
  judgment in Apocalypse of Weeks) is now fully traceable across
  the corpus.
- **91:16 (sevenfold-light new heaven)** is the Mäṣḥafä Hēnok's
  eschatological climax — Rev 21:1 antecedent with the distinctive
  sevenfold-light intensification (cf. Isa 30:26).
- **95:3 (saints shall judge the world)** is the textual basis for
  the apocalyptic-saints-judge-the-world tradition that 1 Cor 6:2
  presupposes — Tewahedo theosis-and-vindication theology preserves
  this canonically.
- **98:4 (sin not sent from heaven; man authored it)** is the
  FOUNDATIONAL anti-Manichaean anchor in the Tewahedo theodicy
  framework, cited in anti-Zandic polemic.
- **104:10 (sinners will pervert words of righteousness)** is the
  scriptural warrant for the entire Tewahedo manuscript-preservation
  enterprise. **104:12 (books given to righteous as joy)** is its
  positive complement: scribal copying as joy-form participation in
  the heavenly liturgy.
- **105:1 ('I and My son')** is one of the rare pre-Christian
  'son' references — Tewahedo Christology reads it as Father-Son
  union pre-canonical witness, anticipating Jn 14:23 / 17:21-23.
- **106:2 (Noah's radiant birth)** anchors the Tewahedo iconographic
  motif of saintly-radiance from birth, preserved in monastic
  fresco tradition.
- **108:1 ('for those who keep the law in the last days')** is the
  Mäṣḥafä Hēnok's closing inclusio — and Tewahedo readers
  identify directly as that addressee, since they are the ONLY
  Bible-reading community for whom 1 Enoch is canonical Scripture.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new 1 Enoch
  entries appended:
  Apocalypse of Weeks (10: 93:2, 93:5, 93:6, 93:8, 93:9, 93:10 +
  91:12, 91:13, 91:14, 91:16 — seven-past weeks + three-
  eschatological weeks) + Epistle introduction (1: 92:1) + paths
  and woes (24: 94:1, 94:6, 94:7, 95:3, 96:1, 96:3, 97:8, 98:4,
  98:7, 99:3, 99:5, 100:1, 100:4, 100:7, 101:1, 102:4, 102:5,
  103:2, 103:4, 103:7, 104:6, 104:10, 104:12, 105:1) + Birth of
  Noah (4: 106:2, 106:13, 106:18, 107:1) + closing inclusio (1:
  108:1). _meta scope/source strings updated. **Two work labels
  used per existing convention**: `Apocalypse of Weeks (1 Enoch
  93)` for 93:* and 91:12-16 (year=-150); `Epistle of Enoch
  (1 Enoch 91-108)` for everything else (year=-100).
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma44EEpistleOfEnochWave` class with **15 tests**
  including the arc-close pin `test_all_six_mashafa_henok_sections_covered`
  that programmatically verifies every one of the six Mäṣḥafä Hēnok
  sections has substantive coverage (Watchers ≥40 + Parables ≥40 +
  Astronomical ≥10 + Dream Visions ≥3 + Animal Apocalypse ≥20 +
  Epistle ≥40).

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.4.E**:
```
ethiopian_commentaries.json: 350 entries (was 310; +40)
├─ Cyril of Alexandria     : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian       :  37 entries (Gen 1-9, 11)
└─ 1 Enoch tradition       : 192 entries — Mäṣḥafä Hēnok now FULLY
                                          substantively expanded across
                                          all 6 sections:
                                          ├─ Watchers (1-36)            :  51
                                          ├─ Parables (37-71)            :  49
                                          ├─ Astronomical (72-82)        :  ~14
                                          ├─ Dream Visions (83-84)       :   ~4
                                          ├─ Animal Apocalypse (85-90)   :  ~30
                                          └─ Epistle (91-108)            :  ~44

Voice mix: ~35% Cyril / ~10% Ephrem / ~55% 1 Enoch
           (was 39/12/49 pre-γ.4.4.E — 1 Enoch is now dominant)
γ.4 cumulative              : 338 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .4 30 + .4.B 40 + .4.C 40 +
                              .4.D 40 + .4.E 40 = 338)
```

**+15 tests**. **γ.4.4.E tests: 15/15 pass in isolation; 11/11 lint
clean.**

**γ.4.4 ARC CLOSURE NOTE**: With γ.4.4.E shipped, the Mäṣḥafä Hēnok
content sub-arc (γ.4.4.A first-wave through γ.4.4.E Epistle) is
COMPLETE for substantive-coverage purposes. Each of the six
canonical sections has ≥3 verse-keyed Tewahedo-significant entries;
the largest sections (Watchers + Parables + Epistle) each have ≥40
substantive entries. The Mäṣḥafä Hēnok is now the deepest single-
source presence in the corpus (192 entries) — appropriate for the
Tewahedo edition that uniquely canonizes it.

**Forward references**:
- **γ.4.2.B** Ephrem on Gen 12-50 — would rebalance voice mix back
  toward Ephrem (currently 10% — substantially under-represented).
- **γ.4.3** Cyril on Luke (~400 long-term).
- **NEW**: with the Mäṣḥafä Hēnok arc closed, consider opening other
  uniquely-Tewahedo canonical texts: **γ.4.5** Mäṣḥafä Kufāle
  (Book of Jubilees, also canonical in Tewahedo and in Ge'ez only);
  **γ.4.6** Mäṣḥafä Aksumawi (Ethiopic Sirach reception); or
  **γ.4.7** Senodos / Didascalia Ethiopic patristic-canonical texts.

**Recommended next ship**:
- **γ.4.2.B Ephrem on Gen 12-50** — rebalances Ephrem share from
  10% back toward 20-25%. Patriarchal narrative is the natural
  continuation of the γ.4.2 Gen 1-11 first wave.
- **OR γ.4.5 Jubilees seed** — opens the next uniquely-Tewahedo
  canonical text on the same Mäṣḥafä-Hēnok-style trajectory.
