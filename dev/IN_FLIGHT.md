# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

## Prior task

**γ.4.4.B 1 Enoch Watchers detail (40 entries on chs 1-36)** shipped
2026-05-12. Substantive expansion of the Watchers section beyond
the 11 first-wave entries. Brings Watchers coverage from 11 to 51
entries across 30 distinct chapters (out of section's 36); 1 Enoch
share of corpus rises from 17% to 31% — now substantively the
second-heaviest voice.

**Why it matters for THIS project**: the Watchers section is the
Mäṣḥafä Hēnok's most theologically load-bearing component — textual
root of Tewahedo demonology (15:8 demons as disembodied antediluvian
giants), seven-archangel veneration (20:1), forgivable-vs-unforgivable
sin distinction (13:8), Gehenna-fire eschatology (10:13), pagan-
idolatry-as-demon-sacrifice etiology (19:1 → 1 Cor 10:20), Ethiopian
imperial 'Negus Negesti' title etymology (9:4 'King of kings').

**Files**:
- `content/sources/ethiopian_commentaries.json` — 40 new 1 Enoch
  Watchers entries appended covering all 5 sub-arcs: prologue
  (1:3, 2:1, 5:4, 5:7) + descent (6:2, 6:5, 7:5, 8:4, 9:1, 9:4,
  9:8, 10:1, 10:13, 11:1) + intercession (12:1, 12:4, 13:5, 13:8,
  14:1, 14:25, 15:8, 16:1) + first journey (17:1, 17:5, 18:14,
  19:1, 19:3) + second journey (20:1, 21:7, 23:1, 24:4, 25:3,
  25:5, 26:1, 27:2, 29:2, 32:3, 33:3, 34:1, 36:1). _meta updated.
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma44BWatchersDetailWave` class with 12 tests.

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.4.B**:
```
ethiopian_commentaries.json: 230 entries (was 190; +40)
├─ Cyril of Alexandria     : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian       :  37 entries (Gen 1-9, 11)
└─ 1 Enoch tradition       :  72 entries (1en 5 books; Watchers
                                          substantively expanded —
                                          30 of 36 chs covered)

Voice mix: 53% Cyril / 16% Ephrem / 31% 1 Enoch
           (was 64/19/17 pre-γ.4.4.B)
Six-tradition coverage     : 286 entries (was 246)
γ.4 cumulative              : 218 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 32 + .4 30 + .4.B 40 = 218)
```

**+12 tests**. **3433 / 3434 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **γ.4.4.C** Parables detail (Son-of-Man Christology expansion).
- **γ.4.4.D** Astronomical + Dream Visions / Animal Apocalypse.
- **γ.4.4.E** Epistle of Enoch detail.
- **γ.4.2.B** Ephrem on Gen 12-50.
- **γ.4.3** Cyril on Luke (~400 long-term).

**Session totals (2026-05-12)**:
```
τ.6 Ge'ez seed                                      +15 tests
χ.2 SEED Matthew Henry                              +32 tests
χ.4 SEED Catena Aurea                               +34 tests
χ.3 SEED Calvin                                     +35 tests
χ.5 SEED Rashi                                      +34 tests
γ.4.1.A Cyril on John (first wave)                  +12 tests
γ.4.1.B Cyril on John (second wave)                 +10 tests
γ.4.1.C Cyril on John (third wave)                  +14 tests
AUDIT_2026-05-12-B                                    0 tests (doc-only)
γ.4.2 Ephrem on Genesis (first wave)                +12 tests
γ.4.1.D Cyril on John (fourth wave — CLOSES γ.4.1)  +15 tests
γ.4.4 1 Enoch (first wave — all 5 books)            +11 tests
γ.4.4.B 1 Enoch Watchers detail                     +12 tests
                                  session total:   +236 tests
                                  3197 → 3433 (serial; 1 skipped)
```

**Recommended next ship**:
- **γ.4.4.C Parables detail** — expand Son-of-Man Christology
  section (1En 37-71). Would push 1 Enoch share toward 35-40%.
- **γ.4.2.B Ephrem on Gen 12-50** — patriarchal narrative; would
  push Ephrem share back toward 20-25%.
- **PAUSE** — session has 13 phase ships + 2 audits + 2 side-ships.
  Voice mix is substantively three-anchored; corpus state is clean;
  natural pause point.

## Prior task

**γ.4.4 1 Enoch first wave (all five books — 30 entries)** shipped
2026-05-12. First substantive expansion of the **third anchor** of
the Ethiopian Tewahedo corpus — the Mäṣḥafä Hēnok (Book of Enoch)
that the Tewahedo canon uniquely receives as Scripture. **First
entries in the corpus to use the Tewahedo-only "1en" book code.**

**Why it matters for THIS project**: brings the 1 Enoch share of
the Ethiopian corpus from 1% (pre-γ.4.4) to 17% — substantively
three-anchored at last (Cyril 64% / Ephrem 19% / 1 Enoch 17%). The
Mäṣḥafä Hēnok is the SINGLE BIGGEST canonical differentiator of
the Tewahedo Bible from every other major Christian communion's
canon; its substantive presence in the buyer-facing apparatus is
load-bearing for the v1.x flagship uniqueness claim.

**1 Enoch 1:9 pin** — THE verse Jude 1:14-15 quotes verbatim in
the canonical NT. Jude's apostolic-canonical quotation of 1 Enoch
as inspired prophecy is the strongest textual basis for the
Tewahedo canon's reception of 1 Enoch as Scripture.

**1 Enoch Son of Man Christology** (chs 46, 48, 62, 71) — develops
the Danielic Son of Man into a sustained pre-Christian Jewish
messianic-cosmic-judge figure. The NT's "Son of Man" Christology
(84 Synoptic + 13 Johannine uses) presupposes this Enochic
development. Tewahedo reception preserves what other canons obscure.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 30 new 1 Enoch
  entries appended across all five canonical books: Watchers
  (1:1, 1:9, 6:1, 6:6, 7:2, 8:1, 10:4, 14:8, 14:18, 15:1, 22:5) +
  Parables (37:1, 38:1, 46:1, 46:3, 48:2, 48:6, 51:1, 62:5, 71:14)
  + Astronomical (72:1, 81:5) + Dream Visions / Animal Apocalypse
  (83:3, 85:1, 90:9, 90:37) + Epistle of Enoch (91:7, 93:3, 99:10,
  104:2). All cite R.H. Charles 1912 trans (Oxford: Clarendon —
  fully PD since 2002 UK / 2008 US per copyright math). _meta block
  updated to document γ.4.4 wave-1 + the three-anchored voice
  distribution.
- `tests/test_ethiopian_gamma4.py` — new `TestGamma44EnochFirstWave`
  class with 11 tests: 1en-book-code-present + all-five-books-
  represented + 1-Enoch-substantively-present (≥15% share) + 6
  signature passages (Jude 1:9 / Watchers 6:1 / throne vision 14:18
  / Son of Man 46:1 / Enoch-as-Son-of-Man 71:14 / Messianic White
  Bull 90:37) + γ.4.4 _meta name + Charles/1912/PD per entry.

**Code-side wiring**: zero new code. The "1en" book code is new
to the corpus but the existing EthiopianCommentaryDetector +
EthiopianCommentaries loader handle any book code as string — no
infrastructure changes needed.

**Corpus state post-γ.4.4 wave-1**:
```
ethiopian_commentaries.json: 190 entries (was 160 after γ.4.1.D; +30)
├─ Cyril of Alexandria     : 121 entries (John 1-7 + 11-21 — COMPLETE)
├─ Ephrem the Syrian       :  37 entries (Gen 1-9, 11)
└─ 1 Enoch tradition       :  32 entries (1en chs 1-104 + 2 Gen xrefs)

Voice mix: 64% Cyril / 19% Ephrem / 17% 1 Enoch
           (substantively three-anchored at last)
Six-tradition coverage     : 246 entries (was 216)
γ.4 cumulative              : 178 entries beyond γ.4 seed
                             (.1.A 30 + .1.B 27 + .1.C 29 + .1.D 30 +
                              .2 wave-1 32 + .4 wave-1 30 = 178)
```

**+11 tests**. **3421 / 3422 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **γ.4.4.B-E** 1 Enoch expansion beyond first wave (decompose by
  book: Watchers / Parables / Astronomical+Dream Visions / Epistle).
- **γ.4.2.B** Ephrem on Gen 12-50 (patriarchal narrative).
- **γ.4.2.C/D** Ephrem on Exodus / Numbers + Deuteronomy.
- **γ.4.3** Cyril on Luke (~400 long-term target).
- **γ.4.5** Ephrem's Hymns on Paradise (~80 entries).
- **γ.4.6** Cyril's Letters + Thesaurus (~150-200 entries).

**Session totals (2026-05-12)**:
```
τ.6 Ge'ez seed                                      +15 tests
χ.2 SEED Matthew Henry                              +32 tests
χ.4 SEED Catena Aurea                               +34 tests
χ.3 SEED Calvin                                     +35 tests
χ.5 SEED Rashi                                      +34 tests
γ.4.1.A Cyril on John (first wave)                  +12 tests
γ.4.1.B Cyril on John (second wave)                 +10 tests
γ.4.1.C Cyril on John (third wave)                  +14 tests
AUDIT_2026-05-12-B                                    0 tests (doc-only)
γ.4.2 Ephrem on Genesis (first wave)                +12 tests
γ.4.1.D Cyril on John (fourth wave — CLOSES γ.4.1)  +15 tests
γ.4.4 1 Enoch (first wave — all 5 books)            +11 tests
                                  session total:   +224 tests
                                  3197 → 3421 (serial; 1 skipped)
```

**Recommended next ship**:
- **γ.4.2.B Ephrem on Gen 12-50** — patriarchal narrative; would
  push Ephrem share toward 25-30%, closer to corpus parity.
- **γ.4.4.B 1 Enoch Watchers detail** — substantively expand the
  Watcher section (chs 1-36) toward fuller coverage.
- **PAUSE** — session has 12 phase ships + 2 audits + 2 side-ships.
  Voice distribution is now substantively three-anchored
  (64/19/17), a natural completion-point for the γ.4 expansion arc.

## Prior task

**γ.4.1.D Cyril on John (fourth wave: John 15-21) — CLOSES γ.4.1**
shipped 2026-05-12. 30 substantive Cyril-on-John entries covering
John 15-21 (Vine + Spirit + Paraclete + sorrow-to-joy + High-Priestly
Prayer + Garden + arrest + Pilate + Passion + tetelestai + Resurrection
+ Receive-the-Holy-Ghost + restoration of Peter). γ.4.1 is now CLOSED
modulo the unfillable Jn 8-10 manuscript gap (Cyril's Books VII-VIII
LOST).

**Why it matters for THIS project**: completes the Cyrilline John
commentary arc that started with the γ.4 seed. The four waves
together cover the full Gospel of John substantively (modulo the
manuscript-tradition gap at Jn 8-10). The Tewahedo theological
inheritance from Cyril — especially the Christology of one incarnate
nature of the Word, the eucharistic realism of the Bread of Life
discourse, the pneumatology of progressive economy, and the
Trinitarian perichoresis — is now substantively present in the
buyer-facing apparatus across the entire Gospel.

**γ.4.1 SUMMARY** (single-session arc):
```
γ.4.1.A  John 1-4    Logos prologue + Cana + Nicodemus + Samaritan  30 ✓
γ.4.1.B  John 5-7    Bethesda + Bread of Life + Tabernacles         27 ✓
γ.4.1.C  John 11-14  Lazarus + Last Supper + Farewell I              29 ✓
γ.4.1.D  John 15-21  Vine + High-Priestly Prayer + Passion + Resurr  30 ✓
                                                       cumulative: 116
γ.4.1 CLOSED 2026-05-12 modulo Jn 8-10 (Cyril Books VII-VIII LOST).
```

**Files**:
- `content/sources/ethiopian_commentaries.json` — 30 new Cyril-on-
  John entries appended covering Jn 15:1/15:5/15:13/15:16/15:26/
  15:27 + 16:7/16:13/16:20/16:28/16:33 + 17:1/17:3/17:5/17:17/
  17:21/17:24 + 18:6/18:11/18:36/18:38 + 19:11/19:26/19:30/19:36 +
  20:17/20:22/20:29 + 21:15/21:17. _meta block updated to document
  γ.4.1.D + the CLOSED-modulo-gap status of γ.4.1.
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma41DCyrilJohn15Through21` class with 14 tests including
  the **γ.4.1-closes-modulo-Jn-8-10 pin** that asserts coverage
  spans all extant Cyrilline chapters (Jn 1-7 + 11-21).

**Code-side wiring**: zero new code.

**Corpus state post-γ.4.1.D**:
```
ethiopian_commentaries.json: 160 entries (was 130 after γ.4.2 wave-1; +30)
├─ Cyril of Alexandria     : 121 entries (was 91; +30)
│  ├─ John coverage         : chs 1-7 + 11-21 (Cyrilline-John COMPLETE)
│  └─ 8-10 PERMANENTLY UNAVAILABLE (Books VII-VIII LOST)
├─ Ephrem the Syrian       :  37 entries (unchanged)
└─ 1 Enoch tradition       :   2 entries (unchanged)

Voice mix: Cyril 76% / Ephrem 23% / 1 Enoch 1%
           (was 70/28/2 pre-γ.4.1.D)
Six-tradition coverage     : 216 entries (was 186)
γ.4.1 cumulative           : 116 entries (CLOSED)
```

**+14 tests**. **3409 / 3410 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **γ.4.2.B** Ephrem on Genesis 12-50 (patriarchal narrative,
  ~40-60 entries) — would push Ephrem share toward 35-40%.
- **γ.4.2.C** Ephrem on Exodus (~40-60 entries).
- **γ.4.2.D** Ephrem on Numbers + Deuteronomy (~30-40 entries).
- **γ.4.3** Cyril on Luke (Payne Smith 1859 PD, ~400 long-term
  target).
- **γ.4.4** 1 Enoch verse-keyed (Charles 1912 PD, ~300 entries) —
  would bring 1 Enoch share substantively up (currently 1%).

**Session totals (2026-05-12)**:
```
τ.6 Ge'ez seed                                      +15 tests
χ.2 SEED Matthew Henry                              +32 tests
χ.4 SEED Catena Aurea                               +34 tests
χ.3 SEED Calvin                                     +35 tests
χ.5 SEED Rashi                                      +34 tests
γ.4.1.A Cyril on John (first wave)                  +12 tests
γ.4.1.B Cyril on John (second wave)                 +10 tests
γ.4.1.C Cyril on John (third wave)                  +14 tests
AUDIT_2026-05-12-B                                    0 tests (doc-only)
γ.4.2 Ephrem on Genesis (first wave)                +12 tests
γ.4.1.D Cyril on John (fourth wave — CLOSES γ.4.1)  +14 tests
                                  session total:   +212 tests
                                  3197 → 3409 (serial; 1 skipped)
```

**Recommended next ship**:
- **γ.4.2.B Ephrem on Gen 12-50** — patriarchal narrative; pushes
  Ephrem share toward 35-40% (closer to corpus parity with Cyril).
- **γ.4.4 1 Enoch first wave** — the Tewahedo-unique canon
  distinctive; currently 1% of corpus. Substantive expansion would
  highlight the Tewahedo flagship uniqueness.
- **PAUSE** — session has 10 phase ships + 2 audits + 2 side-ships.
  Healthy stopping point if user wants.

## Prior task

**γ.4.2 Ephrem on Genesis (first wave: Gen 1-11)** shipped 2026-05-12.
First ship per AUDIT_2026-05-12-B N+1 recommendation. 32 substantive
verse-keyed entries from Ephrem the Syrian's Commentary on Genesis
(NPNF Series 2 Vol 13, Gwynn/Schaff trans., Oxford 1898 — PD).
Covers Genesis 1-11 (primeval history: creation week + Sabbath +
Eden + Fall + protoevangelium + Cain-Abel + Enoch translation +
Noah-flood-rainbow + Babel).

**Why it matters for THIS project**: rebalances the γ.4 Ethiopian
corpus voice distribution from **93% Cyril / 5% Ephrem / 2% 1 Enoch**
(post-γ.4.1.C) to **70% Cyril / 28% Ephrem / 2% 1 Enoch** — bringing
the corpus shape substantively closer to the documented dual-anchor
claim (Syriac Ephrem + non-Chalcedonian Alexandrian Cyril as the
two patristic anchors of Oriental Orthodox communion). Ephrem on
Genesis is foundational for Tewahedo creation theology + the Andəmta
homiletic tradition. The seed pins load-bearing Ephremic-Syriac
patristic readings: image/likeness distinction (1:26 — theosis
foundation), Adam-Christ + Eve-Church typology (2:21 — ecclesiology
root), Syriac protoevangelium (3:15), Enoch translation (5:24 —
Mäṣḥafä Hēnok authority), ark-Church typology (6:14), rainbow-bow
covenant (9:13), Babel-Pentecost inverse (11:9).

**Files**:
- `content/sources/ethiopian_commentaries.json` — 32 new
  Ephrem-on-Genesis entries appended covering Gen 1:2/1:4/1:6/1:11/
  1:14/1:20/1:26/1:31 + 2:2/2:9/2:18/2:21 + 3:4/3:7/3:9/3:15/3:19/
  3:24 + 4:7/4:9/4:16 + 5:24/5:29 + 6:3/6:8/6:14 + 7:11 + 8:21 +
  9:13/9:25 + 11:4/11:9. Each entry ~120-180 word paraphrase. _meta
  block updated to document γ.4.2 wave-1 + the rebalanced voice
  distribution.
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma42EphremGenesisFirstWave` class with 12 tests pinning
  Ephrem-substantively-present (≥30) + voice-rebalance-achieved
  (Cyril <80%) + Gen 1-11 chapter coverage + 7 doctrinal anchors +
  γ.4.2 _meta name + NPNF/Vol 13/PD citation per entry.

**Code-side wiring**: zero new code. γ.4.2 wave-1 is pure content
expansion within the γ.4 infrastructure shipped 2026-05-11.

**Corpus state post-γ.4.2 wave-1**:
```
ethiopian_commentaries.json: 130 entries (was 98 after γ.4.1.C; +32)
├─ Cyril of Alexandria     :  91 entries (unchanged — John 1-7+11-14+19)
├─ Ephrem the Syrian       :  37 entries (was 5; +32 — Genesis 1-11)
└─ 1 Enoch tradition       :   2 entries (unchanged)

Voice mix: Cyril 70% / Ephrem 28% / 1 Enoch 2%
           (was 93/5/2 — AUDIT-recommended rebalance achieved)
Six-tradition coverage     : 186 entries (was 154)
γ.4 cumulative content      : 118 entries beyond γ.4 seed
                             (γ.4.1.A 30 + γ.4.1.B 27 + γ.4.1.C 29 +
                              γ.4.2 wave-1 32 = 118)
```

**+12 tests**. **3395 / 3396 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **γ.4.1.D** Cyril on John 15-21 — closes γ.4.1 modulo Jn 8-10 gap.
- **γ.4.2.B** Ephrem on Exodus — pushes Ephrem toward ~35-40%.
- **γ.4.2.C** Ephrem on Numbers + Deuteronomy — Pentateuch closure.
- **γ.4.4** 1 Enoch verse-keyed entries — would bring 1 Enoch share
  up substantively (currently 2%).

**Session totals (2026-05-12)**:
```
τ.6 Ge'ez seed                                      +15 tests
χ.2 SEED Matthew Henry                              +32 tests
χ.4 SEED Catena Aurea                               +34 tests
χ.3 SEED Calvin                                     +35 tests
χ.5 SEED Rashi                                      +34 tests
γ.4.1.A Cyril on John (first wave)                  +12 tests
γ.4.1.B Cyril on John (second wave)                 +10 tests
γ.4.1.C Cyril on John (third wave)                  +14 tests
AUDIT_2026-05-12-B                                    0 tests (doc-only)
γ.4.2 Ephrem on Genesis (first wave)                +12 tests
                                  session total:   +198 tests
                                  3197 → 3395 (serial; 1 skipped)
```

**Recommended next ship** (per AUDIT_2026-05-12-B + this ship):
- **γ.4.1.D Cyril on John 15-21** — closes γ.4.1 modulo the
  unfillable Jn 8-10 gap. Voice mix would shift back toward Cyril
  slightly (~73%); still well below pre-γ.4.2 93%.
- **γ.4.2.B Ephrem on Exodus** — pushes Ephrem share toward 35-40%,
  fuller dual-anchor parity.
- **AUDIT_2026-05-12-C** — third audit of the day if user requests.

## Prior task

**AUDIT_2026-05-12-B** shipped 2026-05-12. Second solo-Claude audit
of the day, user-invoked after the χ.2-5 commentary cluster CLOSED
and γ.4.1 advanced through 3 of 4 planned waves. Doc-only; no
phase, no test delta, 11/11 lint clean.

**Key findings**:
- AUDIT_2026-05-12 recommendations were ~80% consumed within
  hours (PLAN-REFRESH-2 + ξ.21 + ξ.26 all shipped same day).
  Audit-cadence rule continues to work.
- Two new drift items: (viii) PLAN §5 MEDIUM TRACK status drift on
  χ-cluster SEED-vs-ETL.x decomposition; (ix) γ.4 corpus voice
  imbalance (93% Cyril after γ.4.1.C).
- One minor cleanup: (x) CRLF/LF warnings on every save.
- 5 new patterns established this session: SEED+ETL.x decomposition;
  anti-fabrication pin (γ.4.1.C Jn 8-10 lost-books guard); year-
  range anti-merge pin; per-tradition title prefix; CRLF/LF noise.

**Recommended next-N-session ordering** (audit-derived):
- **N+1 γ.4.2 Ephrem on Genesis first wave** — rebalances 93%
  Cyril voice mix toward documented dual-anchor claim.
- **N+2 γ.4.1.D Cyril on John 15-21** — closes γ.4.1 modulo
  unfillable Jn 8-10 manuscript gap.
- **N+3 doc-refresh trio**: PLAN §5 χ-cluster status normalization
  + RULES §1 corpus target update + .gitattributes EOL fix.
- **N+4 publisher decision checkpoint**: money items (B.AI.1+2
  + π.9; B.AI.4 + B.AI.5 already removed) + γ.4.x continuation +
  ξ.18.x style-src direction.

**Files**:
- `dev/AUDIT_2026-05-12-B.md` — new audit memo (~570 lines).
- `dev/CHANGELOG.md` — audit ship block prepended.

**3383 / 3384 tests pass serially (1 skipped); 11/11 lint clean.**
No code changes.

**Session totals (2026-05-12) post-audit**:
```
τ.6 Ge'ez seed                                      +15 tests
χ.2 SEED Matthew Henry                              +32 tests
χ.4 SEED Catena Aurea                               +34 tests
χ.3 SEED Calvin                                     +35 tests
χ.5 SEED Rashi                                      +34 tests
γ.4.1.A Cyril on John (first wave)                  +12 tests
γ.4.1.B Cyril on John (second wave)                 +10 tests
γ.4.1.C Cyril on John (third wave)                  +14 tests
AUDIT_2026-05-12-B                                    0 tests (doc-only)
                                  session total:   +186 tests
                                  3197 → 3383 (serial; 1 skipped)
```

## Prior task

**γ.4.1.C Cyril on John (third wave: John 11-14)** shipped 2026-05-12.
Continues the γ.4.1 Tewahedo flagship expansion. γ.4.1.A shipped 30
entries on John 1-4; γ.4.1.B shipped 27 on John 5-7; γ.4.1.C adds 29
on John 11-14 (Lazarus + Last Supper + Farewell Discourse I).
**Skips John 8-10** — Cyril's Books VII-VIII covering those chapters
are LOST in the manuscript tradition.

**Why it matters for THIS project**: γ.4.1.C covers the Christological-
pneumatological climax of the central Johannine section. The Lazarus
pericope (John 11) anchors Cyril's resurrection-Christology + the
Christian liturgical-vocabulary of death as sleep. The John 14
perichoresis-Paraclete cluster (14:9-10, 14:16-17, 14:28) is the
textual foundation of patristic Trinitarian theology — including
the most-contested anti-Arian verse (Jn 14:28 "My Father is greater
than I") which Cyril resolves via the assumed-humanity vs eternal-
nature distinction. The John 13 foot-washing is enacted annually in
the Tewahedo Holy Thursday liturgy.

**Files**:
- `content/sources/ethiopian_commentaries.json` — 29 new Cyril-on-
  John entries appended (Jn 11:4/11:11/11:25/11:26/11:35/11:40/
  11:41/11:43 + 12:24/12:27/12:31/12:32/12:46 + 13:1/13:14/13:18/
  13:31/13:34/13:35 + 14:1/14:2/14:6/14:9/14:10/14:16/14:17/14:20/
  14:26/14:28). Each entry ~120-200 word paraphrase. _meta block
  updated to document γ.4.1.C + the cumulative state (Cyril now
  91 of 98 = 93%) and to note the John 8-10 manuscript-tradition gap.
- `tests/test_ethiopian_gamma4.py` — new
  `TestGamma41CCyrilJohn11Through14` class with 14 tests pinning
  John 11-14 coverage + 11 doctrinal anchors + anti-fabrication pin
  for Jn 8-10 (no Cyril content allowed there) + NPNF/Vol 14/PD pin
  + γ.4.1.C _meta name. test_cyril_is_heaviest_voice bumped from
  ≥50 to ≥80 expected.

**Code-side wiring**: zero new code. γ.4.1.C is pure content expansion.

**Corpus state post-γ.4.1.C**:
```
ethiopian_commentaries.json: 98 entries (was 69 after γ.4.1.B; +29)
├─ Cyril of Alexandria     : 91 entries (was 62; +29 — all on John)
│  ├─ John chapters covered: 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14, 19
│  │                         (chs 8-10 unavailable — Books VII-VIII LOST)
│  └─ Per-chapter counts   : 1×14, 2×5, 3×8, 4×5, 5×10, 6×10, 7×7,
│                            11×8, 12×5, 13×6, 14×10, 19×1
├─ Ephrem the Syrian       :  5 entries (unchanged)
└─ 1 Enoch tradition       :  2 entries (unchanged)

Six-tradition coverage     : 154 entries (was 125)
γ.4.1 cumulative wave-1+2+3: 86 of 600 target (~14%)
```

**+14 tests**. **3383 / 3384 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **γ.4.1.D** — Cyril on John 15-21 (Vine discourse + High-Priestly
  Prayer + Passion + Resurrection appearances). ~30-40 more entries.
  Closes γ.4.1 Cyril-on-John ETL (modulo the unfillable Jn 8-10 gap).
- **γ.4.2** — Ephrem on Genesis (NPNF S2 V13). ~200-300 entries.
  Would rebalance the voice mix from current 93% Cyril dominance.

**Session totals (2026-05-12)**:
```
τ.6 Ge'ez seed                                      +15 tests
χ.2 SEED Matthew Henry                              +32 tests
χ.4 SEED Catena Aurea                               +34 tests
χ.3 SEED Calvin                                     +35 tests
χ.5 SEED Rashi                                      +34 tests
γ.4.1.A Cyril on John (first wave)                  +12 tests
γ.4.1.B Cyril on John (second wave)                 +10 tests
γ.4.1.C Cyril on John (third wave)                  +14 tests
                                  session total:   +186 tests
                                  3197 → 3383 (serial; 1 skipped)
```

**Recommended next ship**:
- **γ.4.1.D Cyril on John 15-21** — closes γ.4.1 Cyril-on-John ETL.
  ~30-40 more entries.
- **γ.4.2 Ephrem on Genesis** — rebalances voice mix (currently 93%
  Cyril); the Syriac anchor deserves expansion comparable to Cyril's.
- **AUDIT** — session well past audit-cadence triggers (≥10 phases +
  ≥150 tests). Solo-Claude audit would consolidate state.

## Prior task

**γ.4.1.B Cyril on John (second wave: John 5-7)** shipped 2026-05-12.
Continues the γ.4.1 Tewahedo flagship expansion. γ.4.1.A shipped 30
entries covering John 1-4; γ.4.1.B adds 27 entries covering John 5-7
— arguably the theologically heaviest stretch of Cyril's entire John
commentary (Father-Son discourse + Bread of Life + Living Water).

**Why it matters for THIS project**: the Bread of Life discourse
(John 6) is the central locus classicus for Cyril's eucharistic
realism — the doctrine that shapes the entire Tewahedo Anaphora
tradition. The John 5 discourse contains the strongest Trinitarian-
equality texts in the Gospel (5:18 "equal with God"; 5:26 "as the
Father hath life in Himself" — the textual root of eternal
generation). The Living Water passages (Jn 7:37-39) anchor Cyril's
pneumatology of progressive economy (the Spirit was 'not yet given'
before the glorification — the textual root of the entire post-
Pentecost pneumatology Tewahedo inherits via the Anaphora of Cyril's
epiclesis prayers).

**Files**:
- `content/sources/ethiopian_commentaries.json` — 27 new Cyril-on-
  John entries appended (Jn 5:8/5:17/5:18/5:19/5:21/5:22/5:24/5:26/
  5:39/5:46 + Jn 6:11/6:27/6:35/6:38/6:44/6:51/6:53/6:54/6:55/6:63
  + Jn 7:16/7:17/7:24/7:37/7:38/7:39/7:46). Each entry ~120-180 word
  paraphrase. _meta block updated to document γ.4.1.B + the cumulative
  state (Cyril is now 62 of 69 = 90% of the Ethiopian corpus).
- `tests/test_ethiopian_gamma4.py` — new TestGamma41BCyrilJohn5Through7
  class (10 tests pinning John 5-7 coverage + 7 doctrinal anchors +
  NPNF/Vol 14/PD citation pin per entry + γ.4.1.B _meta name).
  test_cyril_is_heaviest_voice bumped from ≥20 to ≥50 expected entries.

**Code-side wiring**: zero new code. γ.4.1.B is pure content expansion
within the γ.4 infrastructure shipped 2026-05-11.

**Corpus state post-γ.4.1.B**:
```
ethiopian_commentaries.json: 69 entries (was 42 after γ.4.1.A; +27)
├─ Cyril of Alexandria     : 62 entries (was 35; +27 — all on John)
│  ├─ John chapters covered: 1, 2, 3, 4, 5, 6, 7, 19
│  └─ Per-chapter counts   : 1×13, 2×6, 3×8, 4×5, 5×10, 6×10, 7×7, 19×1
├─ Ephrem the Syrian       :  5 entries (unchanged)
└─ 1 Enoch tradition       :  2 entries (unchanged)

Six-tradition coverage     : 125 entries (was 98)
```

**+10 tests**. **3369 / 3370 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **γ.4.1.C** — Cyril on John 11-14 (Lazarus + Last Supper +
  Farewell Discourses). ~30-40 more entries.
- **γ.4.1.D** — Cyril on John 15-21 (Vine + High-Priestly Prayer +
  Passion + Resurrection). ~30-40 more entries.
- **Manuscript gap note**: Cyril's Books VII-VIII covering John
  8-10 are LOST in the manuscript tradition; no Cyril expansion is
  possible for those chapters. A future Ephrem-on-John or
  Andəmta-on-John phase could fill the gap.
- **γ.4.2** — Ephrem on Genesis (NPNF S2 V13). ~200-300 entries.

**Session totals (2026-05-12)**:
```
τ.6 Ge'ez seed                                      +15 tests
χ.2 SEED Matthew Henry                              +32 tests
χ.4 SEED Catena Aurea                               +34 tests
χ.3 SEED Calvin                                     +35 tests
χ.5 SEED Rashi                                      +34 tests
γ.4.1.A Cyril on John (first wave)                  +12 tests
γ.4.1.B Cyril on John (second wave)                 +10 tests
                                  session total:   +172 tests
                                  3197 → 3369 (serial; 1 skipped)
```

**Recommended next ship**:
- **γ.4.1.C Cyril on John 11-14** — Lazarus + Last Supper +
  Farewell Discourses. ~30-40 more entries.
- **γ.4.1.D Cyril on John 15-21** — Vine + High-Priestly Prayer +
  Passion + Resurrection. ~30-40 more entries.
- **γ.4.2 Ephrem on Genesis** — diversify the voice mix; Cyril
  is at 90% of the corpus, switching to Ephrem rebalances toward
  the Syriac anchor.
- **AUDIT** — session has hit ≥10 phases + ≥150 tests (well into
  audit-cadence territory).

## Prior task

**γ.4.1 Cyril on John (first wave: John 1-4)** shipped 2026-05-12.
First substantive expansion of the Ethiopian Tewahedo flagship
corpus — γ.4 shipped 12 seed entries; γ.4.1 adds 30 Cyril-on-John
entries from NPNF S2 V14 (Pusey/Randell trans, Oxford 1874-1885).
**Activation criteria met**: publisher's explicit direction to ship
γ.4.1 constitutes the formal Tewahedo-as-v1.x-uniqueness-angle
confirmation required by `dev/SCOPE_2026-05-12-addendum-gamma-4-expansion.md`.

**Why it matters for THIS project**: the Ethiopian Tewahedo Church
preserves Cyril's Christology more fully than any other living
Christian communion — the Anaphora of Cyril is in regular liturgical
use. γ.4.1's 30-entry expansion makes Cyril the heaviest single voice
in the corpus (35 of 42 total Ethiopian entries = 83%), aligning the
buyer-facing apparatus with the Tewahedo Church's actual theological
center of gravity. The new entries pin the load-bearing Cyrilline
anchors: communicatio idiomatum (Jn 3:13), anti-Arian Christology
(Jn 1:3), revelatory epistemology (Jn 1:18), Lamb of God typology
(Jn 1:29), baptismal regeneration (Jn 3:5), Trinitarian soteriology
(Jn 3:16), ontological theology (Jn 4:24).

**Files**:
- `content/sources/ethiopian_commentaries.json` — 30 new Cyril-on-
  John entries appended (Jn 1:3 / 1:4 / 1:5 / 1:9 / 1:11 / 1:12 /
  1:13 / 1:18 / 1:23 / 1:29 / 1:33 / 1:51 / 2:4 / 2:7 / 2:11 / 2:19
  / 2:21 / 3:3 / 3:5 / 3:6 / 3:8 / 3:13 / 3:14 / 3:16 / 3:36 / 4:14
  / 4:23 / 4:24 / 4:34 / 4:42). Each entry: ~120-180 word paraphrase
  of Cyril's interpretive position. The `_meta` block updated to
  document γ.4.1 wave + Pusey/Randell PD translator chain. The 2
  existing γ.4 Cyril-on-John seed entries (Jn 1:1, 1:14) also
  updated to cite Pusey/Randell for consistency.
- `tests/test_ethiopian_gamma4.py` — new `TestGamma41CyrilJohn`
  class with 12 tests pinning Cyril-as-heaviest-voice + John 1-4
  chapter coverage + 9 doctrinal anchors + NPNF/Vol 14/PD citation
  pin + _meta documents γ.4.1 expansion.

**Code-side wiring**: zero new code. γ.4.1 is pure content
expansion within the γ.4 infrastructure shipped 2026-05-11
(EthiopianCommentaryDetector, EthiopianCommentaries loader,
comm-ethiopian kind, ethiopian-tewahedo edition tradition mapping).
The existing detector picks up the new entries automatically.

**Corpus state post-ship**:
```
γ.3 patristic_commentaries.json    : 8 entries  (Augustine on Gen)
γ.4 + γ.4.1 ethiopian_commentaries.json : 42 entries
  ├─ Cyril of Alexandria  : 35 entries (33 on John + 2 other)
  ├─ Ephrem the Syrian    :  5 entries (Gen + Hymns on Paradise + Ps 1)
  └─ 1 Enoch tradition    :  2 entries (Gen 6:1, 6:4)
χ.2 protestant_commentaries.json   : 12 entries (Matthew Henry)
χ.3 reformation_commentaries.json  : 12 entries (Calvin)
χ.4 catholic_commentaries.json     : 12 entries (Catena Aurea)
χ.5 rabbinic_commentaries.json     : 12 entries (Rashi)

Total six-tradition coverage: 98 entries.
```

**+12 tests**. **3359 / 3360 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **γ.4.1.B** — Cyril on John 5-7 (Bethesda discourse + Bread of
  Life + Tabernacles). ~20-30 more entries.
- **γ.4.1.C** — Cyril on John 11-14 (Lazarus + Last Supper +
  Farewell Discourses). ~30-40 more entries.
- **γ.4.1.D** — Cyril on John 15-21 (Vine discourse + High-
  Priestly Prayer + Passion + Resurrection appearances). ~30-40
  more entries.
- **γ.4.2** — Ephrem on Genesis (NPNF S2 V13). ~200-300 entries.
- **γ.4.3** — Cyril on Luke (Payne Smith 1859 PD). ~400 entries.

**Session totals (2026-05-12, since first χ.2 ship)**:
```
τ.6 Ge'ez seed                                      +15 tests
χ.2 SEED Matthew Henry                              +32 tests
χ.4 SEED Catena Aurea                               +34 tests
χ.3 SEED Calvin                                     +35 tests
χ.5 SEED Rashi                                      +34 tests
γ.4.1 Cyril on John (first wave)                    +12 tests
                                  session total:   +162 tests
                                  3197 → 3359 (serial; 1 skipped)
```

**Recommended next ship** (PIVOT or CONTINUE):
- **γ.4.1.B Cyril on John 5-7** — continue the Tewahedo flagship
  expansion through Cyril's extant Books V-VI (Bethesda discourse,
  Bread of Life, Tabernacles). ~20-30 more entries.
- **γ.4.2 Ephrem on Genesis** — switch voice to the Syriac anchor;
  NPNF S2 V13. ~200-300 entries.
- **AUDIT** — audit-cadence triggers tripped (≥10 phases + ≥150
  tests this session). Solo-Claude audit per `memory/feedback_audit_cadence.md`.
- **ψ.30 matrix accessibility** — publisher-facing console polish.
- **Money authorization** — B.AI.1 + B.AI.2 cover-gen unblock
  decision.

## Prior task

**χ.5 SEED Rashi's Commentary on the Tanakh** shipped 2026-05-12.
**CLOSES the χ.2-5 commentary cluster** — all four denominational
seeds shipped in a single session (χ.2 Henry / χ.3 Calvin / χ.4
Catena Aurea / χ.5 Rashi). +135 cumulative tests for the cluster
(3134 → 3347 passing serially).

**Why it matters for THIS project**: the `jewish-study` edition
declares `jewish` in `traditions_default` but had no
`comm-rabbinic` notes to surface in the ψ.8 cross-denominational
popup. χ.5 ships the first batch of rabbinic-tradition notes —
Rashi specifically — making the jewish-study edition's Jewish
lens substantive. The ψ.8 popup now has SUBSTANTIVE coverage for
ALL FOUR major Western traditions (Patristic + Tewahedo +
Protestant + Catholic + Reformation + Rabbinic). The buyer-facing
differentiator is now genuinely multi-traditional rather than
Protestant-default.

**Two Jewish-distinctive pins** the seed guards against drift:
- **Ps 22:1** ("My God, why hast thou forsaken me") — Rashi reads
  as David's prophetic vision of Esther in exile, NOT
  Christological prefigurement of the Cross.
- **Isa 53:3** ("He was despised") — Rashi reads as corporate
  Israel suffering exile for the nations, NOT individual messiah.
These are the two most-disputed Jewish-Christian interpretive
texts; pinning them ensures the comm-rabbinic kind retains its
genuinely-Jewish voice across the entire χ.5.x expansion.

**Files**:
- `content/sources/rabbinic_commentaries.json` — new schema-v1
  seed; field name `commentator` (mirrors χ.2 / χ.3 — Rashi
  isn't a Father); 12 paraphrased Rashi entries weighted toward
  Pentateuch + key Jewish-distinctive readings; every attribution
  cites medieval Hebrew + "PD" (Rashi d. 1105); PD _meta block
  explicitly addresses the English-translation-may-not-be-PD
  issue (most modern Rashi translations are in copyright; seed
  paraphrases work from the medieval Hebrew directly).
- `scripts/core/sources.py` — `RabbinicCommentary` frozen
  dataclass + `RabbinicCommentaries` lazy loader (by_verse +
  by_commentator) + `rabbinic_commentaries()` `@lru_cache(maxsize=1)`
  singleton. Mirrors χ.2 / χ.3 API.
- `scripts/core/detectors.py` — `RabbinicCommentaryDetector`
  class (kind="comm-rabbinic", confidence 0.95, plain year
  display — all χ.5 seed voices post-AD). draft_title prefix
  "Rabbinic —". Appended to `ALL_DETECTORS` after
  `ReformationCommentaryDetector` — candidate-order lineage now
  γ.3 → γ.4 → χ.2 → χ.4 → χ.3 → χ.5 (patristic → tewahedo →
  protestant → catholic → reformation → rabbinic).

**Kind reuse**: `comm-rabbinic` pre-existed in kinds.yaml (line
417-425). χ.5 is first phase to emit it. No kinds.yaml change.

**Tradition wiring**: pre-existing. traditions.yaml maps
jewish-study → jewish; ψ.8 surfaces comm-rabbinic notes for the
edition automatically.

**Tests**: tests/test_rabbinic_chi5.py — 34 tests across 5
classes. TestChi5DataFile × 8 (parses, meta block, ≥12 entries,
required fields, Rashi + PD marker, year range 1070-1105 anti-
merge pin, Gen 1:1 present). TestChi5RabbinicCommentariesLoader
× 7 (frozen dataclass, by_verse + by_commentator, empty for NT
books — Rashi scope, Rashi present, Maimonides empty —
χ.5.x not χ.5, SourceMissingError on absent cache).
TestChi5DetectorContract × 8 (registered after Reformation —
lineage pin, kind=comm-rabbinic, candidate shape with Rabbinic
title prefix, confidence=0.95, empty for NT verses + out-of-seed
Gen verses, verse_text ignored, body XSS-escapes, plain year
display). TestChi5KindIsRegistered × 2. TestChi5Coverage × 9
(Pentateuch-weighted ≥6, iconic Gen 1:1 "zo'ek darshani"
opening, Akedah, Shiloh prophecy Jewish read, Shema, Akiva pin,
**Ps 22:1 Jewish-distinctive** + **Isa 53:3 corporate-Israel** —
both load-bearing for the Jewish-Christian boundary, Rashi-only-
voice anti-merge pin).

**+34 tests**. **3347 / 3348 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **χ.5.x** — user-side full Rashi ETL from primary Hebrew (PD
  by age) + fresh paraphrases OR confirmed-PD English. ~3-7K
  notes target per PLAN.
- **χ.5.y Maimonides** — add the Rambam (1138-1204) as another
  comm-rabbinic voice.
- **χ.5.z Ibn Ezra + Ramban + Targumim** — additional rabbinic
  voices.

**χ.2-5 CLUSTER CLOSED**. Session totals:

```
χ.2  Matthew Henry          comm-protestant   +32 tests   SEED ✓
χ.4  Aquinas (Catena Aurea) comm-catholic     +34 tests   SEED ✓
χ.3  Calvin                 comm-reformation  +35 tests   SEED ✓
χ.5  Rashi                  comm-rabbinic     +34 tests   SEED ✓
                            cluster total:    +135 tests
                            3134 → 3347 (serial; 1 skipped)
```

**Recommended next ship** (PIVOT — χ-cluster is done):
- **γ.4.1 Cyril's John commentary** (extend Tewahedo flagship from
  12 seed entries → ~400-600 via NPNF S2 V14). Activation criteria
  per `dev/SCOPE_2026-05-12-addendum-gamma-4-expansion.md` say
  publisher confirmation of v1.x uniqueness angle; this session's
  Tewahedo-direction trajectory (τ.6 Ge'ez + γ.4 + now all 4
  cluster seeds with comm-ethiopian as the flagship voice)
  constitutes implicit confirmation.
- **ψ.30 matrix accessibility** — publisher-facing console polish.
  Single autonomous phase, no money gate.
- **Money authorization** — B.AI.1 + B.AI.2 cover-gen are gated on
  publisher provider pick (Anthropic / OpenAI / Stability budget
  decision).
- **Audit cadence** — per `memory/feedback_audit_cadence.md`: 22+
  phases shipped this session, +213 tests cumulative. Both
  thresholds (≥10 phases + ≥150 tests) tripped — audit
  recommendation is in scope. Would be a lighter solo-Claude
  audit, not parallel-subagent sweep.

## Prior task

**χ.3 SEED Calvin's commentaries** shipped 2026-05-12. Third
ship in the χ-commentary cluster (after χ.2 Matthew Henry +
χ.4 Catena Aurea); closes the magisterial-Western half. Only
χ.5 Rashi remains open in the χ.2-5 cluster.

**Why it matters for THIS project**: the `evangelical-reformed`
edition was getting only χ.2's broader post-Reformation Henry-
flavored notes via its `protestant` tradition declaration. χ.3
adds the narrowly 16th c. magisterial-Reformation voice — Calvin
specifically — which the Reformed self-identification expects to
surface FIRST. The `lutheran-confessional` edition also benefits
(both editions map to `protestant` tradition via traditions.yaml).
The seed pins Calvin's signature Reformed exegetical anchors:
**sola fide** (Rom 3:21 + Gal 2:16), **sola gratia** (Eph 2:8),
**accommodation** (Gen 1:1 — Calvin's hermeneutical signature),
**regulative principle** (Exo 20:3), **providence** (Rom 8:28),
**covenant theology** (Jer 31:33).

**Calvin Translation Society edition**: the standard PD English
translation (Edinburgh, 22 volumes 1843-1855, ed. Owen / Beveridge
/ Pringle / King) — all translators died well before the 1929 PD
cutoff. CCEL hosts the full text under PD.

**Files**:
- `content/sources/reformation_commentaries.json` — new schema-v1
  seed file mirroring χ.2 protestant_commentaries (field name
  `commentator`, not `father` — Calvin is a 16th c. Reformer,
  not a Father). 12 paraphrased Calvin entries with balanced
  coverage: **OT × 6** (Gen 1:1, 3:15, Exo 20:3, Ps 23:1, Isa
  7:14, Jer 31:33) + **NT × 6** (Mat 6:9, Joh 1:1, Rom 3:21,
  8:28, Gal 2:16, Eph 2:8). Every entry year in 1540-1564
  (Calvin's commentary period — anti-merge with χ.2's 1700-
  1721 Matthew Henry range).
- `scripts/core/sources.py` — `ReformationCommentary` frozen
  dataclass + `ReformationCommentaries` lazy loader (indexes
  by_verse + by_commentator) + `reformation_commentaries()`
  `@lru_cache(maxsize=1)` singleton. Mirrors χ.2 API exactly.
- `scripts/core/detectors.py` — `ReformationCommentaryDetector`
  class (kind="comm-reformation", confidence 0.95, **plain year
  display** — no BC/AD branching since all magisterial Reformers
  are post-1500; matches χ.2 contract). Candidate `draft_title`
  prefixes "Reformation —" (distinct from χ.2's "Protestant —"
  for downstream UI differentiation). Appended to `ALL_DETECTORS`
  after `CatholicCommentaryDetector` so the candidate-order
  lineage is γ.3 → γ.4 → χ.2 → χ.4 → χ.3 (patristic → tewahedo
  → protestant → catholic → reformation).

**Kind reuse**: `comm-reformation` pre-existed in kinds.yaml
(line 447-455; declared with the kinds-v2 schema). χ.3 is the
first phase to actually emit it. No kinds.yaml edit needed; no
kinds-count pin bump.

**Tradition wiring**: pre-existing. traditions.yaml maps
evangelical-reformed + lutheran-confessional → protestant; both
editions surface comm-reformation notes automatically via ψ.8.

**Tests**: tests/test_reformation_chi3.py — 35 tests across 5
classes. TestChi3DataFile × 8 (parses, meta block, ≥12 entries,
required fields, Calvin attribution + PD marker, year range
1540-1564 anti-merge pin, Gen 1:1 present).
TestChi3ReformationCommentariesLoader × 7 (frozen dataclass,
by_verse + by_commentator, empty for Revelation since Calvin
never commented on it, Calvin present, Luther returns empty —
χ.3.x not χ.3, SourceMissingError on absent cache).
TestChi3DetectorContract × 8 (registered after Catholic —
lineage pin, kind=comm-reformation, candidate shape with
Reformation title prefix, confidence=0.95, empty for out-of-
seed verses, verse_text ignored, body XSS-escapes, plain year
display). TestChi3KindIsRegistered × 3 (comm-reformation in
kinds.yaml + comm-protestant coexists as sibling — anti-merge
pin). TestChi3Coverage × 9 (OT × 6, NT × 6, sola fide × 2 pins,
sola gratia, accommodation, idolatry, providence, covenant
theology, Calvin-only-voice anti-merge pin).

**+35 tests**. **3313 / 3314 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **χ.3.x** — user-side full Calvin Translation Society Edinburgh
  1843-1855 ETL (CCEL). ~5-10K notes target per PLAN.
- **χ.3.y Luther + Zwingli** — additional comm-reformation voices.
  Luther on Galatians + Genesis Lectures + Romans; Zwingli on his
  OT prophet sermons. All PD.
- **χ.5 Rashi** — the LAST open χ.2-5 cluster phase. Jewish;
  `comm-rabbinic` kind (existing).

**Recommended next ship**: χ.5 Rashi (closes the entire χ.2-5
cluster) — Jewish exegetical voice, 11th c. France, comm-rabbinic
kind already exists. Or pivot — γ.4.1 corpus expansion / ψ.30
matrix a11y / money authorization for B.AI.* items.

## Prior task

**χ.4 SEED Aquinas's Catena Aurea** shipped 2026-05-12. Second
ship in the χ-commentary cluster (after χ.2 Matthew Henry); next
per PLAN_2026-05-09 execution-order recommendation (χ.2 → **χ.4**
→ χ.3 → χ.5).

**Why it matters for THIS project**: the `catholic-study` edition
declares `catholic` in `traditions_default` but had only generic
patristic notes (γ.3 Augustine-on-Genesis seed) to surface in the
ψ.8 cross-denominational popup. χ.4 ships the first batch of
*medieval Catholic reception* notes — Father voices framed by
Aquinas's editorial hand, distinct from raw patristic content. The
`anglican-bcp` edition (catholic via its deuterocanonical canon)
gains identical coverage automatically — no edition-level change
needed. The seed pins the signature Catholic exegetical anchor:
**Mt 16:18 *Tu es Petrus*** (papal-primacy verse).

**Catena Aurea ("Golden Chain")**: Aquinas's compilation
(1262-1273 at Pope Urban IV's request) of selected patristic
exegesis on the four Gospels — ~80 Greek and Latin Fathers
stitched together verse-by-verse. THE standard medieval Catholic
biblical apparatus.

**Files**:
- `content/sources/catholic_commentaries.json` — new schema-v1
  seed file mirroring γ.3 / γ.4 / χ.2 commentary files. Field
  name `father` (every Catena voice IS a Father — the Catholic
  framing is in the *kind*, not the schema). 12 paraphrased
  entries across all four Gospels: Matthew × 4 (1:1 / 5:3 /
  16:18 / 27:46), Mark × 2 (1:1 / 16:15), Luke × 3 (1:46 / 2:14
  / 24:13), John × 3 (1:1 / 1:14 / 20:28). Every attribution
  includes "Catena Aurea" + "PD".
- `scripts/core/sources.py` — `CatholicCommentary` frozen
  dataclass + `CatholicCommentaries` lazy loader (indexes
  by_verse + by_father) + `catholic_commentaries()`
  `@lru_cache(maxsize=1)` singleton.
- `scripts/core/detectors.py` — `CatholicCommentaryDetector`
  class (kind="comm-catholic", confidence 0.95, BC/AD-aware year
  display mirroring γ.4, draft_title prefix
  "Catholic (Catena Aurea) — " + draft_label suffix
  "via Catena Aurea." for popup chipping). Appended to
  `ALL_DETECTORS` after `ProtestantCommentaryDetector` so the
  candidate-order lineage is γ.3 → γ.4 → χ.2 → χ.4 (patristic →
  tewahedo → protestant → catholic).

**Kind reuse**: `comm-catholic` pre-existed (line 437-445 of
kinds.yaml). χ.4 is the first phase to actually emit it. No
kinds.yaml edit needed.

**Tradition wiring**: pre-existing. `content/traditions.yaml`
already maps `catholic-study → catholic`; the anglican-bcp
edition also declares catholic in its traditions_default. ψ.8
surfaces comm-catholic notes for both automatically.

**Tests**: tests/test_catholic_chi4.py — 34 tests across 5
classes. TestChi4DataFile × 9 (parses, meta block, Catena Aurea
named, ≥12 entries, required fields, attribution + PD marker,
Gospels-only — pin against scope creep, Mt 1:1 present).
TestChi4CatholicCommentariesLoader × 7 (frozen dataclass,
by_verse + by_father, empty for non-Gospel books gen/act,
Augustine present, SourceMissingError on absent cache).
TestChi4DetectorContract × 8 (registered after Protestant —
lineage pin, kind=comm-catholic, candidate shape with Catena
Aurea title prefix + label suffix, confidence=0.95, empty for
non-Gospel verses, verse_text ignored, body XSS-escapes, AD
rendering for post-Christian year). TestChi4KindIsRegistered ×
2. TestChi4Coverage × 8 (all four Gospels; Mt 16:18 *Tu es
Petrus* papal-primacy anchor; Augustine + Chrysostom + Jerome
all appear).

**+34 tests**. **3278 / 3279 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **χ.4.x** — user-side full Catena Aurea ETL from the
  Newman/Pusey/Keble/Pattison 1841-1845 Oxford edition (CCEL
  hosts full text). ~3-8K notes target per PLAN.
- **χ.3 Calvin** — next in PLAN execution order (χ.2 → χ.4 → χ.3
  → χ.5). Calvin tags as `comm-reformation` kind, not
  `comm-catholic`.
- **χ.5 Rashi** — Jewish; `comm-rabbinic` kind (existing).

**Recommended next ship**: χ.3 Calvin's Commentaries (Reformed
expositor, comm-reformation kind — kind already exists; pattern
identical to χ.2 / χ.4). Or pivot — γ.4.1 corpus expansion / ψ.30
matrix a11y / money authorization.

## Prior task

**χ.2 SEED Matthew Henry's Exposition** shipped 2026-05-12.
First ship after the translation foundation arc closed with
τ.6 — pivots from translation-depth to corpus growth via the
χ-commentary cluster. Per PLAN_2026-05-09 §χ.2-5 execution-
order recommendation (χ.2 Matthew Henry → χ.4 Catena → χ.3
Calvin → χ.5 Rashi), χ.2 ships first because Matthew Henry's
*Exposition of the Old and New Testament* (1706-1721) is the
most-circulated PD Protestant commentary.

**Why it matters for THIS project**: the `evangelical-reformed`
edition declares `protestant` in `traditions_default` (via
`content/traditions.yaml`) but had NO `comm-protestant` notes
to surface in the ψ.8 cross-denominational popup. χ.2 ships
the first batch of Protestant tradition notes, closing that
surface. Henry anchors the χ.2.x expansion roadmap (Spurgeon /
Edwards / Hodge as future commentators).

**Files**:
- `content/kinds.yaml` — new `comm-protestant` kind, sibling
  of (not replacement for) the narrower `comm-reformation`
  kind which stays scoped to 16th c. magisterial Reformers
  (Luther / Calvin / Zwingli). Label "Protestant", description
  names Henry / Spurgeon / Edwards / Hodge.
- `content/sources/protestant_commentaries.json` — new schema-v1
  seed file mirroring γ.3 / γ.4 commentary files. **Field
  name `commentator` (not `father`)** — Henry isn't a Father
  in any historical sense; the semantic distinction is
  preserved in the dataclass + loader API. 12 paraphrased
  entries across Gen 1:1, 1:3, 1:26, 2:7, 3:1, 3:15
  (protoevangelium), 6:5 (total depravity), Ps 1:1, 23:1,
  John 1:1, 1:14, 19:34. Every entry carries full attribution
  + explicit "PD" marker.
- `scripts/core/sources.py` — `ProtestantCommentary` frozen
  dataclass + `ProtestantCommentaries` lazy loader (indexes
  by_verse + by_commentator) + `protestant_commentaries()`
  `@lru_cache(maxsize=1)` singleton.
- `scripts/core/detectors.py` — `ProtestantCommentaryDetector`
  class (kind="comm-protestant", confidence 0.95, direct-lookup
  by (book, chapter, verse), HTML-escaped body via
  `_format_body()`, **plain year display** — no BC/AD branching
  needed since all Protestant expositors are post-Reformation,
  simpler than γ.4's BC-handling for 1 Enoch's c. 200 BC
  entries). Appended to `ALL_DETECTORS` after
  `EthiopianCommentaryDetector` (γ.4) so candidate ordering is
  Father-canonical first → Tewahedo-distinctive second →
  Protestant-English third.

**Tradition wiring**: pre-existing. `content/traditions.yaml`
already maps `evangelical-reformed → protestant`, so ψ.8
picks up comm-protestant notes for the evangelical-reformed
edition automatically. No traditions.yaml edit needed.

**Tests**: tests/test_protestant_chi2.py — 32 tests across 5
classes. TestChi2DataFile × 8 (parses, meta block, ≥12 entries,
required fields, PD marker, post-Reformation year range, Gen
1:1 present). TestChi2ProtestantCommentariesLoader × 7 (frozen
dataclass, by_verse + by_commentator lookup, empty-list for
unknowns, SourceMissingError on absent cache). TestChi2DetectorContract
× 8 (registered after Ethiopian — candidate-order pin,
kind=comm-protestant, candidate shape, confidence=0.95, empty
for uncommented verses, verse_text ignored, body XSS-escapes,
plain year display distinct from γ.4 BC/AD). TestChi2KindIsRegistered
× 3 (comm-protestant in kinds.yaml + comm-reformation coexists —
anti-merge pin). TestChi2Coverage × 6 (Genesis / Psalms / John;
Gen 3:15 protoevangelium; Gen 6:5 total-depravity anchor; Henry
sole commentator).

**+32 tests**. **3244 / 3245 tests pass serially (1 skipped);
11/11 lint clean.**

**Forward references**:
- **χ.2.x** — user-side full ETL from CCEL / Project Gutenberg
  Matthew Henry text dump. ~5-15K notes target per PLAN.
- **χ.3 Calvin** — next in PLAN execution order (χ.2 → χ.4 → χ.3
  → χ.5). Calvin tags as `comm-reformation` kind, not
  `comm-protestant`.
- **χ.4 Catena Aurea** — Catholic patristic-chain commentary.
- **χ.5 Rashi** — Jewish.

**Recommended next ship**: χ.4 Catena Aurea (next per PLAN
execution order — Catholic patristic-chain compiled by Aquinas;
~3-8K notes target; Latin translation passes needed). Or pivot
to ψ.30 a11y / money authorization / γ.4.1 corpus expansion.

## Prior task

**τ.6 Ge'ez Tewahedo Bible seed** shipped 2026-05-12. Closes
the translation-foundation arc this session. Reinforces the
v1.x flagship (ethiopian-tewahedo edition) with its native
scriptural language. Ge'ez (ግዕዝ) is the liturgical /
scriptural language of the Ethiopian Orthodox Tewahedo Church;
the Tewahedo Bible's manuscript tradition dates from 4th-6th
c. CE.

**Why it matters for THIS project**: 1 Enoch and Jubilees
survived as complete texts ONLY in Ge'ez — those are the
canonical anchors of γ.4's commentary work (Ethiopian
Tewahedo seed). R.H. Charles' 1912 1 Enoch translation
(referenced in γ.4) worked from Ge'ez manuscripts.

**Files**:
- `scripts/extract_translation.py` — geez-tewahedo entry
  documenting PD basis (Pell-Platt 1830 BFBS + BFBS 1853 OT
  + Dillmann 1865 Lexicon; underlying mss 4th-15th c.),
  Unicode block coverage (U+1200-U+137F + supplement +
  extended + extended-A), LTR script, Tewahedo numerals.
- `content/translations/geez-tewahedo/_meta.yaml` — full PD
  documentation; canonical-distinctives notes naming
  1 Enoch / Jubilees / Meqabyan; editorial-decision note
  that ethiopian-tewahedo edition's popup_languages_default
  doesn't currently declare `geez` (publisher decision to
  opt in).
- `content/translations/geez-tewahedo/gen.py` — 3-verse seed:
  ቀዳሚሁ ገብረ እግዚአብሔር ሰማየ ወምድረ።  (Gen 1:1) /
  ወምድርሰ ኢታስተርኢ ... ይጼልል መልዕልተ ማይ።  (Gen 1:2) /
  ወይቤ እግዚአብሔር ለይኩን ብርሃን ወኮነ ብርሃን።  (Gen 1:3).

**Tests**: tests/test_translations_tau6.py — 15 tests across
6 classes. TestTau6FlagshipReinforcement pins that the
ethiopian-tewahedo flagship edition exists + the runtime
composes geez-tewahedo cleanly (edition-agnostic discovery —
any edition can opt in by listing `geez` in
popup_languages_default). TestNineTranslationsRegistered
pins the post-ship count at 9.

**Translation foundation post-ship**: 9 translations on disk.
Every popup_language declared in any edition's
popup_languages_default has at least seed coverage. The
TestPopupLanguageCoverageClosed invariant (from τ.10-A) holds.

Forward reference: τ.6.x user-side full ingest covering the
Tewahedo 87-book canon (6 books beyond KJV+Apocrypha: 1
Enoch, Jubilees, Meqabyan 1-3, Letter to the Laodiceans).

**+15 tests**. **3212 / 3213 tests pass serially (1 skipped);
11/11 lint clean.**

**Translation arc CLOSED this session.** Subsequent
translation work shifts from foundation-building to depth-
deepening (τ.7 GNT manuscript, τ.5-B WLC unpointed, τ.8
Geneva, τ.9 ASV+YLT, τ.11 Reformation partials) or PIVOTS
off translations (ψ.30 a11y, χ.2-5 patristic, γ.4.1 corpus,
money authorization).

## Prior task

**τ.10-A Van Dyck Arabic Bible seed** shipped 2026-05-12.
Closes the last popup-language gap after the τ.5-A + γ.5 +
τ.4 + τ.3 + τ.2 wave. Coptic-orthodox edition was the only
one of 9 to declare `arabic` in popup_languages_default;
arabic-vandyke now provides matching translation data.

**Files**:
- `scripts/extract_translation.py` — TRANSLATIONS dict
  extended with arabic-vandyke entry; PD basis fully
  documented (all 5 translators died before 1929 cutoff).
- `content/translations/arabic-vandyke/_meta.yaml` — new;
  canonical coverage note (Van Dyck is Protestant
  66-book — deuterocanonical-Arabic Bible candidate for a
  future τ-phase); RTL via ν.2.7.
- `content/translations/arabic-vandyke/gen.py` — new; 3-verse
  Genesis seed with tashkīl; opens فِي ٱلْبَدْءِ خَلَقَ ٱللهُ;
  closes فَكَانَ نُورٌ.

**Tests**: tests/test_translations_tau10a.py — 14 tests
across 5 classes. Notable: the **TestPopupLanguageCoverageClosed
× 2** class programmatically audits every edition's
popup_languages_default and asserts zero gaps remain. This
becomes a permanent invariant going forward — adding a new
popup-language declaration in any edition without matching
translation data will fail the test.

**Popup-language coverage state — CLOSED**:

| Language | Declared by | Coverage |
|---|---|---|
| english | All 9 editions | kjv (full) + jps + lxx-brenton-english + douay-rheims (seeds) |
| hebrew | 6 editions | wlc (seed) — τ.5-A |
| greek | 8 editions | lxx-brenton-greek (seed) — γ.5 |
| latin | 1 (anglican-bcp) | vulgate-clementine (seed) — τ.3 |
| arabic | 1 (coptic-orthodox) | arabic-vandyke (seed) — τ.10-A |

8 translations on disk total: kjv full + 7 Gen 1:1-3 seeds.
Each full ingest is a separate user-side τ-x.x ship per the
documented pattern.

Forward references: τ.10-A.x user-side full ingest. Logged in
CHANGELOG.

**+14 tests**. **3197/3198 tests pass serially (1 skipped);
11/11 lint clean.**

**Translation tier-1 wave CLOSED.** The popup-language
foundation is now complete. Subsequent translation work shifts
from "close coverage gaps" to "deepen specific tradition
support" (τ.6 Ge'ez for Tewahedo flagship; τ.7 Greek NT
manuscript; τ.8-11 Reformation-era English; or pivot to
non-translation tracks).

## Prior task

**τ.4 + τ.3 + τ.2 translation tier-1 wave** shipped 2026-05-12.
Three seeds shipped together to close the SESSION_END §4
first-wave translation work in one ship (N+2/N+3/N+4 batched
because the publisher value compounds — Latin↔English Catholic
pair from τ.3+τ.2 + LXX Greek↔English pair from γ.5+τ.4).

**Three new translations** (all 3-verse Genesis seeds following
γ.5 / τ.5-A pattern):

- **τ.4 `lxx-brenton-english`** — Brenton 1844 LXX English
  side. Companion to existing γ.5 `lxx-brenton-greek` —
  Brenton printed Greek + English in parallel columns. PD
  (Brenton died 1862; 1844 edition predates every PD cutoff).
- **τ.3 `vulgate-clementine`** — Pope Clement VIII's 1592
  authorized edition of Jerome's Latin Vulgate. PD by age
  (Jerome d. 420 AD; Clementine 1592). Notes distinguish
  Clementine (PD) from Stuttgart/Weber-Gryson (NOT PD) and
  Nova Vulgata (NOT PD) — only Clementine works for the
  publisher's PD-distribution constraint.
- **τ.2 `douay-rheims`** — Challoner-revised Douay-Rheims
  English Catholic Bible, 1899 John Murphy reprint, PD by age.
  Pairs with τ.3 as the Catholic-tradition translation pair.

**Files**: 3 new content/translations/<id>/{_meta.yaml, gen.py}
trios + scripts/extract_translation.py TRANSLATIONS dict
extended with 3 new entries (full PD documentation +
user-side ingest path).

**Tests**: tests/test_translations_tau4_tau3_tau2.py — 28
tests across 10 classes. Translation-specific phrasing pins
(JPS "unformed and void", DRA "Be light made" / "void and
empty", Vulgate "In principio" / "Fiat lux", LXX-Eng
"unsightly and unfurnished"). JointCoverage class pins the
distinct-traditions invariant on Gen 1:2 (KJV and JPS
verbatim-agree on Gen 1:1 but diverge on 1:2) and the
Vulgate→DRA calque trail (Fiat lux → Be light made).

**State after ship**: 7 translations registered. Of the 9
editions' popup_languages_default declarations:

| Language | Declared by | Coverage |
|---|---|---|
| hebrew | 6 editions | ✓ τ.5-A (jps + wlc) |
| greek | 8 editions | ✓ γ.5 + τ.4 |
| latin | 1 (anglican-bcp) | ✓ τ.3 |
| arabic | 1 (coptic-orthodox) | ✗ no τ-phase yet |

Arabic remains the only popup-language gap. PD Arabic Bible
exists (Van-Dyck 1865; eBible.org `arb-vandyke`) — candidate
for a future τ-phase if the coptic-orthodox edition becomes
a near-term priority.

**+28 tests**. **3183 / 3184 tests pass serially (1 skipped);
11/11 lint clean.**

Forward references: τ.2.x + τ.3.x + τ.4.x (all user-side full
ingests). Logged in CHANGELOG for the linter's phase-mentions
check.

**Translation tier-1 wave: CLOSED.** The publisher decision
point referenced in AUDIT_2026-05-12 §5 N+5 has now arrived
— next ship is either an Arabic seed (closes the last
popup-language gap), τ.6 Ge'ez (flagship native language),
τ.5-B WLC-unpointed variant, or pivot to a different track
(ψ.30 matrix a11y, χ.2-5 patristic, γ.4.1 corpus expansion,
or money-item authorization).

## Prior task

**τ.5-A JPS 1917 + WLC Hebrew seed** shipped 2026-05-12.
First ship after SESSION_END_2026-05-12's translation-gap
audit. Per the closer's §4 N+1 recommendation: close the
Hebrew column for the 6 of 9 editions that declare `hebrew`
in popup_languages_default.

**Two halves shipped together as one phase** (γ.5 LXX-seed
pattern):

- `jps` — Jewish Publication Society 1917 Tanakh (English).
  PD basis: Schechter died 1915, Adler 1940; JPS itself
  placed 1917 edition in public domain.
- `wlc` — Westminster Leningrad Codex (Hebrew). PD basis:
  Kimball transcription explicitly PD per tanach.us;
  Leningrad Codex B19A (1008 CE) PD by age.

**Files**:
- `scripts/extract_translation.py` — TRANSLATIONS dict
  extended with jps + wlc entries (title / short_title /
  license / source URL + package / notes documenting
  user-side ingest path).
- `content/translations/jps/_meta.yaml` — schema v1; full
  PD documentation; user-side ingest steps; JPS-conventions
  notes.
- `content/translations/jps/gen.py` — 3-verse Genesis seed
  (Gen 1:1-3) with canonical JPS phrasing ("unformed and
  void", "hovered", single-quoted speech).
- `content/translations/wlc/_meta.yaml` — Kimball/Leningrad
  documentation; Unicode handling for niqqud + te`amim;
  RTL rendering via ν.2.7's popup-languages machinery.
- `content/translations/wlc/gen.py` — 3-verse Hebrew seed
  with full niqqud + te`amim; opens on בְּרֵאשִׁית בָּרָא
  אֱלֹהִים; closes on וַיְהִי־אוֹר.
- `tests/test_translations_tau5a.py` — 21 tests across 6
  classes (Registry / Discovery / JpsSeed / WlcSeed / Pairing
  / meta-shape).

**Runtime verification** (post-ship):
- `scripts.core.translations.list_translations()` returns
  `['jps', 'kjv', 'lxx-brenton-greek', 'wlc']` (was 2).
- `has_translation('jps')` + `has_translation('wlc')` both
  True.
- `get_verse('jps', 'gen', 1, 1)` returns the canonical
  JPS opening; `get_verse('wlc', 'gen', 1, 1)` returns the
  Hebrew opening with niqqud.

**Auto-surfaces in**: /customize console's
popup_translation dropdown + /compare console's
side-by-side rendering (no UI code change — both compose
`list_translations()` output dynamically).

**+21 tests** in tests/test_translations_tau5a.py.

**3155 / 3156 tests pass serially (1 skipped); 11/11 lint
clean.**

Forward references: τ.5-A.x (user-side full 39-book Hebrew
ingest) + τ.5-B (WLC-without-niqqud unpointed variant). Both
logged in CHANGELOG for the linter's phase-mentions check.

**Recommended next ship**: τ.4 Brenton LXX (English side) —
full ingest from the current 3-verse γ.5 Greek-only seed.
After: τ.3 Vulgate, τ.2 Douay-Rheims, then per publisher
direction.

## Prior task

**SESSION_END_2026-05-12** shipped — professional handoff
closer for the longest single-conversation arc in the
project's history. Doc-only; no test delta; 11/11 lint clean.

`dev/SESSION_END_2026-05-12.md` (~250 lines) captures:

1. **38+ ships chronologically** (commits 3d19ef4 → 60d9e57)
   across Month 5 (closed) + Month 6 non-money queue (closed)
   + 5 doc-only removals + audit + PLAN-REFRESH-2.

2. **Code-residue audit for the 5 removed features**
   (B.AI.4/5/6/7 + δ.9) per publisher request to verify the
   removals cleaned up anything in the code. **Result: zero
   residue.**
   - scripts/core/copilot.py + scripts/core/verse_card.py:
     never existed (proposal-only entries).
   - No `import smtplib` / SMTP usage anywhere in scripts/.
   - All textual matches are strikethrough removal markers in
     dev/ docs or append-only historical CHANGELOG entries.
   - One near-match: verse_of_day matches in scripts/web.py +
     scripts/core/verse_of_day.py + test_scripts.py are υ.8
     (existing PD RSS feed, read-only daily verse rotation);
     NOT the removed δ.9 email subscription. Names overlap;
     scope doesn't. υ.8 stays.

3. **Translation status reality check** per publisher request
   ("I want to make sure there are more than just greek and
   hebrew translations available for the verses. latin and
   all that is still in there right?"). Honest answer
   surfaced: **the project ships exactly ONE full
   verse-by-verse translation today — KJV English.** The
   lxx-brenton-greek translation is a 3-verse seed (Genesis
   1:1-3 only, from γ.5). Editions DECLARE hebrew/greek/
   latin/arabic in popup_languages_default but the underlying
   translation data isn't on disk. Hebrew = γ.1 Strong's
   word-lookup only (lemma + morphology, not full text).
   Greek = γ.2 Strong's word-lookup + 3-verse LXX seed.
   Latin = not shipped at all. Arabic = not shipped at all.
   The τ-cluster (τ.2-τ.12) covers all of these in PLAN §7
   but none have shipped yet.

4. **Recommended next-session ordering**:
   - N+1: **τ.5-A JPS + WLC Hebrew ingest** (highest leverage
     — closes the Hebrew column for 6 of 9 editions; PD
     source; mirrors the τ.1 KJV pattern; ~1.5-2 sessions).
   - N+2: τ.4 Brenton LXX English (full ingest from the
     3-verse seed; ~1 session).
   - N+3: τ.3 Vulgate Latin (closes the Latin column for
     anglican-bcp; ~1.5 sessions).
   - N+4: τ.2 Douay-Rheims (Catholic English; ~1 session).
   - N+5+: per publisher direction (more τ, money
     authorization for B.AI.1+B.AI.2, γ.4.1 corpus expansion,
     ψ.30 matrix a11y, or uniqueness angles B/D/E from
     AUDIT_2026-05-10 §5).

The translation work jumped to top priority because closing
the gap improves every edition (9 of 9 declare languages they
don't fully serve) and is fully autonomous (no money
authorization needed for PD source ingest).

**3134/3135 tests pass serially (1 skipped); 11/11 lint
clean.** Doc-only ship.

## Prior task

**EPUB-scope reckoning: B.AI.5 + B.AI.6 + B.AI.7 + δ.9
REMOVED** shipped 2026-05-12. Doc-only per publisher direction
("can B.AI.5 actually be implemented in an EPUB and work on
EPUB readers? i feel like it's way out of scope" → confirmed
unimplementable; same root cause then audited for similar
items). No phase number; no test delta; 11/11 lint clean.

**Root cause**: EPUB readers sandbox JavaScript severely —
Apple Books/iBooks blocks XHR/fetch to external domains,
Kindle KFX strips most JS, Google Play Books blocks
cross-origin network, Calibre/ADE inconsistent. Any feature
requiring runtime network calls from the EPUB is
unimplementable in the actual shipped product.

**Four features failed the EPUB-scope test**:
- **B.AI.5** AI co-pilot (Cmd+J) — Anthropic API calls from
  EPUB JS blocked. Use cases were 100% publisher-console
  operations (scenario synthesis, blurb drafting).
- **B.AI.6** Daily devotional auto-curation — needs LLM call
  + SMTP. Neither callable from EPUB. Pure publisher-side.
- **B.AI.7** Marketing copy generator — depended on B.AI.5
  (orphaned by its removal). Also: "Amazon/Apple Books
  product copy" doesn't ship in the EPUB.
- **δ.9** Email subscription for verse-of-day — verbatim from
  proposal "pure backend; SMTP". Publisher web-server
  endpoint; no way for EPUB JS to subscribe.

**Items considered but kept** (per "everything else is
good"): ε.4 + ε.5 (publisher analytics — they're business-ops
tools you run alongside the platform); ξ/ω/ζ clusters
(publisher console UX); ο.6 "Built with YHWH" badge (DOES
ship in EPUB footer); B.AI.1+B.AI.2 cover gen (output ships
in EPUB); π.9 Bowker ISBN (appears on EPUB).

**12 strike-edits** in `dev/PROPOSAL_FEATURE_LANDSCAPE.md`:
§1.2 amazing-features rewrite, §3 Track summary recount, §5
Track E + Track J tables with vacant slots, §5 dependency-
graph art, §6 Month 6 recount 7→5 sessions, §7 tool catalog
removes scripts/core/copilot.py entry, §8 risk register, §9.3
publisher decisions, §11 acceptance criteria.

**Slot vacancy policy**: ALL five removed slots (B.AI.4 +
B.AI.5 + B.AI.6 + B.AI.7 + δ.9) intentionally LEFT VACANT in
numbering. Historical chronological docs (CHANGELOG, prior
IN_FLIGHT prior-task blocks, prior SESSION_STATE snapshot
blocks, AUDIT_2026-05-12) preserved unchanged — those are
append-only point-in-time records. Do NOT re-use these slot
numbers; assign fresh numbers if similar features are
genuinely needed in the future.

**Track J (AI features) post-reckoning**: narrowly scoped to
cover-generation artifacts that ship in the EPUB (B.AI.1 +
B.AI.2 + B.AI.3, all money-gated on publisher provider pick).

**Track E (reader experience) post-reckoning**: δ.1-δ.8 only.
Every retained item genuinely ships inside the EPUB
(localStorage state, EPUB-side CSS/JS, manifest.json for the
PWA published HTML edition).

**3134/3135 tests pass serially (1 skipped); 11/11 lint
clean.** No code changes; no test changes.

## Prior task

**π-book-covers ingest + B.AI.4 removal** shipped 2026-05-12.
Content + doc-only; no phase number assigned (extends existing
π.4 cover system; no code surface added). No test delta.
11/11 lint clean.

Two parts:

1. **Book covers ingest**: copied the publisher's 66-cover
   curated set from
   `C:\Users\bogda\Documents\book_covers\by_book\<NN_BookName>\primary.jpg`
   into `content/covers/_book_defaults/<book_code>.jpg`
   (Protestant 66-book canon, all books). Wired the Ethiopian
   Tewahedo edition's `book_covers:` YAML block in
   content/editions.yaml to reference all 66 shared paths.
   Added `content/covers/_book_defaults/README.md`
   documenting the inventory + opt-in pattern for other
   editions. Exercises the "paths can point anywhere under
   content/" door that `scripts/core/covers.py` explicitly
   documented as the shared-covers-across-editions pattern.
   Ethiopic-canon extras (1en, jub, mq1-3, 4ba, paz, sus,
   bel, man, 1es, 2es, tob, jdt, wis, bar, lje, sir, aes,
   etc. — 21 books) not covered by this ingest; future
   ingest opportunity.

2. **B.AI.4 sharable verse cards removed**: per publisher
   direction, the social-distribution lever is out of scope.
   7 strike-edits across `dev/PROPOSAL_FEATURE_LANDSCAPE.md`
   (§1.2 amazing-features bullet, §5 Track B table row + the
   dependency-graph art, §6 Month 6 sequence with recount
   from 7 to 6 sessions, §7 tool catalog, §9.3 publisher
   decisions, §11 acceptance criteria). Slot B.AI.4
   intentionally left VACANT in numbering to preserve
   historical references; do not re-use. Historical mentions
   in CHANGELOG / prior IN_FLIGHT prior-task blocks / prior
   SESSION_STATE snapshot blocks / AUDIT_2026-05-12 audit
   corpus snapshot left as-is — those are append-only
   point-in-time records.

**Month 6 status post-removal**: 5 of 6 shipped (γ.4 + ζ.9
+ ξ.18 + ξ.21 + ξ.26). Only B.AI.5 AI co-pilot (Cmd+J)
remains, gated on publisher authorization for Anthropic API
runtime budget.

**3134 / 3135 tests pass serially (1 skipped); 11/11 lint
clean.** No code changes; no test changes.

Per-publisher "finish autonomous" direction: continuing to
the next autonomous item after this ship.

## Prior task

**ξ.26 license-key validation** shipped 2026-05-12. Month 6
#5 — CLOSES the autonomous non-money queue. HMAC-SHA256
substituted for PROPOSAL-spec'd Ed25519 (stdlib-first
invariant § 6.3 forbids the `cryptography` library; soft
enforcement per § 9.5 doesn't justify asymmetric crypto; LK2
format prefix reserved for ξ.26.x Ed25519 upgrade if hard
enforcement ever required).

Three pieces:
- `scripts/core/license_key.py` — `LICENSE_PREFIX = "LK1"`;
  `ENV_SIGNING_KEY = "EBIBLE_LICENSE_SIGNING_KEY"`;
  `is_enforced()` reads the env var (fail-open when unset for
  dev / first-run convenience); `mint(edition_id, *,
  expires_iso, secret=None, issued_at_iso=None)` builds the
  LK1 string + HMAC-SHA256 signature; `verify(license_str, *,
  secret=None, now=None)` returns an envelope with reason ∈
  {ok, no_enforcement, missing, wrong_format,
  unsupported_version, bad_signature, expired}. Constant-time
  signature compare via hmac.compare_digest. Format prefix
  reserved for LK2 (Ed25519) future upgrade.
- `scripts/core/license_state.py` — sparse JSON state at
  content/licenses.json mirroring auth.py / distribution.py /
  press_kit.py persistence discipline (atomic write +
  ensure_backup + whitelist-on-save + empty-state default).
  set_license / remove_license / get_license / load /
  save helpers.
- `scripts/api/license.py` — 3 endpoints: GET
  /api/license/status returns per-edition rollup with
  has_key + valid + reason; PUT /api/license/<edition>
  verifies BEFORE persisting (refuses bad signature / expired
  / edition mismatch so bad keys don't get stuck in state);
  DELETE /api/license/<edition> idempotent. Audit-logged.
  Status endpoint NEVER reveals the stored key string.

Soft-enforcement contract pinned: API never refuses a request
based on license state; status endpoint surfaces validity so
future UI can render warning banner; build/preview/publish
paths must not crash on missing or invalid keys.

Routes registered: GET /api/license/status →
_SIMPLE_GET_ROUTES (20→21); PUT /api/license/<edition> →
_PUT_ROUTES (11→12); DELETE /api/license/<edition> →
_DELETE_ROUTES (7→8). Count tests bumped on both PUT + DELETE.

**+43 tests** in tests/test_license_xi26.py (44 cases in file; 1 deselected at collection):
TestXi26Constants × 2, EnforcementToggle × 3, Mint × 7,
Verify × 9 (round-trip, bad sig, expired, wrong secret,
unsupported version, malformed, missing, fail-open, now
injection), LicenseStateLoadSave × 5, SetRemove × 4,
ApiStatus × 4 (incl never-reveals-stored-key pin),
ApiSet × 5, ApiRemove × 2, RouteRegistration × 3.

**3134 / 3135 tests pass serially (1 skipped); 11/11 lint
clean.**

Forward reference: ξ.26.x Ed25519 upgrade for hard
enforcement (LK2 format prefix; verify() dispatches on
prefix for side-by-side migration). Logged in CHANGELOG so
linter phase-mentions check stays clean.

**Month 6 status: autonomous non-money queue CLOSED.**
Remaining work blocked on publisher decision: B.AI.4 +
B.AI.5 money items, or new direction (γ.4.x / ψ.30 / χ.2-5 /
uniqueness angles B/D/E).

## Prior task

**ξ.21 TOTP-based 2FA for admin auth** shipped 2026-05-12.
Month 6 #4 — stdlib-only RFC 6238 implementation (no pyotp
dep) + persisted enrollment + admin-auth gate extension.

Four pieces:
- `scripts/core/totp.py` — pure-stdlib TOTP: generate_secret
  (160-bit base32 via secrets.token_bytes), current_code (RFC
  6238 HMAC-SHA1, 30s step, 6 digits), verify_code (±1-step
  default drift, constant-time compare via
  hmac.compare_digest, malformed rejection without raising),
  provisioning_uri (otpauth://totp/Issuer:Label?secret=...&
  algorithm=SHA1&digits=6&period=30; URL-encodes label +
  issuer). Verified against all 6 RFC 6238 Appendix B test
  vectors (parametrized).
- `scripts/core/auth.py` — sparse JSON state at
  content/auth.json mirroring distribution.py persistence
  (atomic write + ensure_backup + whitelist-on-save).
  load_auth / save_auth / enroll_totp / disable_totp /
  is_totp_enabled / get_totp_secret.
- `scripts/api/auth.py` — 4 endpoints: GET /status surfaces
  flags + enrollment metadata but never the secret; POST
  /begin generates pending secret + URI WITHOUT persisting;
  POST /confirm verifies code then persists (two-step
  pattern prevents lockout from a never-proved enrollment);
  POST /disable requires a valid current code (refuses
  without proof so an attacker who bypassed the gate can't
  also nuke 2FA).
- `scripts.web.Handler._check_admin_auth` doubled in size to
  handle the factor matrix: Bearer token:code parsed via
  str.partition(':') so tokens containing colons round-trip
  correctly; back-compat preserved when neither factor is
  configured (ω.4 default-open behavior unchanged).

Routes registered: GET /api/auth/status →
_SIMPLE_GET_ROUTES (19→20); 3 POST /api/auth/totp/{begin,
confirm,disable} → _POST_ROUTES (9→12; count test bumped).

Deliberate scope choices: QR-code rendering DEFERRED to
ξ.21.x (publisher pastes otpauth URL into authenticator app;
QR rendering needs ~300 lines hand-rolled Reed-Solomon or a
CDN dep conflicting with §6.3); single-use recovery codes
also DEFERRED to ξ.21.x (acceptable for solo-admin: edit
content/auth.json directly to disable if locked out).

**+54 tests** in tests/test_totp_xi21.py: Rfc6238Vectors × 6
parametrized, SecretGeneration × 5, ProvisioningUri × 4,
VerifyCode × 7, AuthStateLoadSave × 4, EnrollDisable × 6,
ApiBegin × 2, ApiConfirm × 4, ApiDisable × 4, ApiStatus × 3,
AdminAuthGate × 5 (neither/token-only/totp-only/both factor
combinations), RouteRegistration × 3.

**3091 / 3092 tests pass serially (1 skipped); 11/11 lint
clean.**

Forward references: ξ.21.x (QR-code SVG rendering + single-
use recovery codes) logged in CHANGELOG for linter phase-
mentions check.

## Prior task

**PLAN-REFRESH-2** shipped 2026-05-12. Doc-only refresh per
AUDIT_2026-05-12 §5 N+1 ("highest-leverage single action; closes
5 of 7 named drift items in one pass" — actually closed 6 of 7).
No phase shipped, no test delta, no code change; 11/11 lint
clean.

Seven distinct doc changes in one ship:

1. **`dev/PLAN_2026-05-09.md` §7 ledger** — Month 5+6 ships
   added to ✓ list (ε.1-ε.3 + ε.6-ε.7 + ο.4 + γ.4 + ζ.9 +
   ξ.18 + ν.7 + ν.10 + ψ.35 + ψ.36-A + ψ.37 + ψ.38 +
   ω.35-A.1-A.11 + ω.35-B.1-B.7 + ω.37/38/39/47 + Δ.6/7/10/12/15
   + ζ.1-9 + γ.1-5 + δ.1-2).

2. **`dev/PLAN_2026-05-09.md` §10.1 operating model** — new
   section cross-referencing `PROPOSAL_FEATURE_LANDSCAPE.md` §6
   as the canonical post-v1.0 sequence doc. Documents Month
   1-6 status + AUDIT §5 next-N table.

3. **`dev/PLAN_2026-05-09.md` §11 addenda index** — two new
   stubs:
   - `dev/SCOPE_2026-05-12-addendum-xi-18-x-style-src.md`
     (style-src tightening trade-off: option A Tailwind-build
     / B hash-CSP / C accept current surface).
   - `dev/SCOPE_2026-05-12-addendum-gamma-4-expansion.md`
     (γ.4.x corpus expansion roadmap — 6 PD-source ETL
     sub-phases targeting ~1.5K-1.8K entries total).

4. **`dev/CLAUDE_PROJECT_RULES.md` §1 corpus target** —
   updated to reflect actual 51,394 notes (147% of original
   upper bound; floor met; growth opportunistic).

5. **`dev/CLAUDE_PROJECT_RULES.md` §10 NOT-list** — POD line
   partially lifted (PDF in scope via ε.7 + ψ.22; KDP/IngramSpark
   still deferred).

6. **`dev/ROADMAP_FUTURE.md`** — three "definitely NOT
   planned" items reconciled: Audio Bible (lifted; ρ-cluster
   scheduled), POD (partial), Multi-language UI (lifted
   2026-05-09).

7. **`dev/IN_FLIGHT.md` prune** — chain truncated from ~30+
   "Prior task" entries (~8,643 lines) to last 5 (this entry +
   AUDIT + ξ.18 + ζ.9 + γ.4 + ο.4 = 275 lines, -97%). CHANGELOG
   carries the authoritative chronological record.

**Drift items addressed: 6 of 7** (POD/i18n line in §10 was
partial — LMS / native-apps / Flask lines unchanged because
they remain accurate). 18 scope addenda now indexed in PLAN §11
(was 16).

**3037 / 3038 tests pass serially (1 skipped); 11/11 lint
clean.** No code changes.

## Prior task

**AUDIT_2026-05-12** shipped 2026-05-12. Doc-only solo-Claude
audit triggered by `feedback_audit_cadence.md` after Month 5
closure + ≥150 test-count drift both tripped. No phase shipped;
no test delta; lint 11/11 clean.

Single output: `dev/AUDIT_2026-05-12.md` (~250 lines). Sections:

- TL;DR — 2026-05-11 audit's 12 named items mostly shipped (11 of
  12); audit-cadence rule is working.
- Arc statistics — Month 5 + Month 6 opening: 32 ships, +784
  tests; web.py 4,564 → 4,921 (no god-module regression).
- Status table for AUDIT_2026-05-11 recommendations.
- 5 new drift findings: money-gate dominance, ξ.18.x style-src
  trade-off unspeced, PROPOSAL operating model not in PLAN,
  IN_FLIGHT prior-task chain bloat, test-suite balance.
- Route/console/module inventory: 60 table-routed endpoints,
  17 consoles unchanged, 5 new core + 4 new api modules, 5
  new content/ JSON state files.
- Recommended next-N-session ordering: N+1 PLAN-REFRESH-2 → N+2
  ξ.21 2FA → N+3 ξ.26 license-key → N+4 publisher decision.
- Closing: highest-leverage single action is PLAN-REFRESH-2
  (doc-only, ~1 hour, closes 5 of 7 named drift items).

Method: mechanical inventory pass (route table counts via Python
introspection, file sizes via `wc -l`, console count via CONSOLES
tuple length) + recommendation drafting + carry-over flagging.

**3037 / 3038 tests pass serially (1 skipped); 11/11 lint clean.**
No code changes.

## Prior task

**ξ.18 CSP nonces** shipped 2026-05-12. Month 6 #3 — per-
request nonce on script-src; HTML responses get the strict
policy + every &lt;script&gt; gets nonce="X"; JSON/file/zip
responses keep the legacy _CSP_POLICY as defense-in-depth.

Three pieces in scripts/web.py::Handler:
- `_generate_nonce()` staticmethod — secrets.token_urlsafe(16)
  → 22-char base64-urlsafe string; 128 bits of entropy per
  RFC 8941 recommendation.
- `_csp_with_nonce(nonce)` classmethod — builds the strict CSP:
  script-src 'self' 'nonce-<value>' https://cdn.tailwindcss.com.
  style-src deliberately keeps 'unsafe-inline' (Tailwind Play
  CDN compat; tightening needs a build step that §6.3 forbids).
- `_SCRIPT_TAG_RE` class regex + `_inject_script_nonces(html,
  nonce)` classmethod — adds nonce="X" to every &lt;script tag
  variant (no-attr, src=, async, multi-line); regex boundary
  prevents false matches on &lt;scripts&gt;/&lt;scripting&gt;;
  idempotent on already-noncified HTML; preserves internal
  whitespace.

Plumbing:
- `_send_security_headers(*, nonce=None)` kwarg added: when None
  emits the legacy `_CSP_POLICY` (defense in depth for
  JSON/file/zip), when string emits `_csp_with_nonce(nonce)`.
- `_send_html(html)` generates a fresh nonce per call → runs
  injector → sends strict CSP with matching nonce. Nonce
  rebuilds on every render so a cached prior response can't
  replay-attack the current one.

**+26 tests** in `tests/test_csp_nonce_xi18.py`:
NonceGeneration × 3, CspWithNonce × 5 (drops 'unsafe-inline'
from script-src, includes nonce, keeps style-src
'unsafe-inline', other directives preserved, Tailwind CDN
allowed), ScriptInjection × 9 (every &lt;script tag variant +
boundary check vs &lt;scripts&gt;/&lt;scripting&gt; +
idempotence + real EXEC_HTML), SendHtmlContract × 4 with
fake-handler smoke tests, LegacyPolicyPreserved × 2 (ξ.3
contract stays green), JsonResponsesUseLegacyCsp × 3.

**3037 / 3038 tests pass serially (1 skipped); 11/11 lint clean.**

Forward reference: ξ.18.x style-src nonce tightening (needs a
Tailwind-build migration; conflicts with §6.3 "no build step"
today). Logged in CHANGELOG so the linter's "phase mentioned
in code" check stays clean.

## Prior task

**ζ.9 first-run tour** shipped 2026-05-12. Month 6 #2 —
in-house tour overlay engine (no Shepherd.js / CDN
dependency per invariant I.1 "no heavy framework creep");
mirrors Shepherd/Driver/Intro public API shape so future
migration is cheap. + 6-step /exec first-run walk-through.

Three pieces:
- `scripts/templates/_design.py::THEME_TOUR_JS` — new ~330-
  line script constant exposing `window.ebibleTour.{start,
  skip, next, back, startIfFirstRun, reset}`. UX contract:
  dim backdrop + halo on the target (box-shadow provides the
  per-step dim), positioned tooltip with viewport clamping
  via top/bottom/left/right `position` field (default
  `bottom`), centred-modal mode for null-selector steps,
  ARIA `role=dialog` + `aria-modal=true` + `aria-labelledby`
  referencing the title's id, keyboard nav (ESC=skip,
  ←/→=back/next), focus moves to Next button on each step
  with prior focus restored on close, click-outside does NOT
  dismiss (avoid accidental skip), reduced-motion friendly.
  All caller-supplied strings (title, body) inserted via
  textContent. localStorage gate (default key
  `ebible_tour_seen_v1`); `startIfFirstRun(storageKey,
  steps, opts)` short-circuits when the flag is set;
  `reset(storageKey)` clears it for future /apihelp
  restart-link wiring. Each step has a counter
  ("Step N of M") + Back disabled on step 0 + Next reads
  "Done" on the last step.
- `scripts/templates/_design.py::apply_design_system` —
  `<!-- THEME_TOUR_JS -->` marker substitution registered
  + the docstring marker catalog updated to list ζ.9.
- `scripts/templates/exec.py` — `<!-- THEME_TOUR_JS -->`
  marker inserted in the head + 6-step tour declared in an
  IIFE at the bottom of the dashboard script, gated on
  `window.ebibleTour` presence. Steps: welcome modal → KPI
  tiles (`#kpi-grid`) → sales import (`#sales-import-section`)
  → distribution checklist (`#distribution-section`) → press
  kit + archive.org (`#press-kit-section`) → closing modal
  with Cmd+K pointer + /apihelp-restart hint. Storage key
  `ebible_tour_exec_v1` (per-console namespacing so future
  /matrix or /publisher tours can be tracked independently).

**+21 tests** in `tests/test_tour_zeta9.py`:
TestZeta9JsConstantShape × 2, MarkerSubstituted × 2,
MarkerDocumented × 1, XssGuards × 4 (pin textContent over
innerHTML for every caller-controlled string), StorageKey
× 2, Accessibility × 4 (ARIA + ESC handler), ExecWiring × 6
(step count + selectors + modal-bookend pattern + first-run
guard).

**3011 / 3012 tests pass serially (1 skipped); 11/11 lint clean.**

## Prior task

**γ.4 Ethiopian Tewahedo commentary** shipped 2026-05-12.
Month 6 — the flagship payload per PROPOSAL ("the Tewahedo
Bible's primary differentiator"). Opens Month 6 by taking the
v1.x uniqueness angle first.

Three pieces:
- `content/sources/ethiopian_commentaries.json` — new 12-entry
  seed JSON. _meta block documents PD basis (Ephrem the Syrian
  via NPNF Series 2 vol 13 ed. Schaff 1898 + Cyril of
  Alexandria via NPNF vols 7+14 + R.H. Charles, The Book of
  Enoch, Oxford 1912 — all firmly out of copyright). Entries
  cover Gen 1:1/1:3/1:26/2:7/3:1/6:1/6:4 + Ps 1:1+23:1 + John
  1:1/1:14/19:34. Three traditions represented: Ephrem (Syriac
  patristic — Tewahedo theological influence), Cyril
  (non-Chalcedonian Alexandrian — Miaphysite Christology
  foundational to the Oriental Orthodox communion of which
  Tewahedo is one of five canonical jurisdictions), and 1 Enoch
  (Tewahedo-canonical Watchers tradition; the only major
  Christian communion to canonize 1 Enoch).
- `scripts/core/sources.py` — `EthiopianCommentary` frozen
  dataclass mirroring `PatristicCommentary` exactly +
  `EthiopianCommentaries` lazy loader (indexes by_verse +
  by_father, raises SourceMissingError on absent JSON) +
  `ethiopian_commentaries()` `@lru_cache(maxsize=1)` singleton.
- `scripts/core/detectors.py` — `EthiopianCommentaryDetector`
  class (kind="comm-ethiopian", confidence 0.95, direct-lookup
  by (book, chapter, verse), HTML-escaped body via
  `_format_body()` with **BC/AD-aware year renderer** so 1
  Enoch's c. 200 BC dating renders as "200 BC" not "-200 AD",
  `note-comm-ethiopian` CSS class for theme styling, reviewer
  notes reference the Andəmta tradition cross-check). Appended
  to `ALL_DETECTORS` after `PatristicCommentaryDetector` (γ.3)
  so candidate ordering is Father-canonical first,
  Tewahedo-distinctive second.

**Kind reuse**: `comm-ethiopian` already existed in
content/kinds.yaml ("Ethiopian Tewahedo tradition — Andəmta
commentary, Synaxarium, Fetha Nagast"). γ.4 is the first phase
to populate it. No kinds.yaml edit needed.

**Tradition wiring**: pre-existing. content/traditions.yaml
already maps ethiopian-tewahedo→tewahedo, so ψ.8 picks up
comm-ethiopian notes for the ethiopian-tewahedo edition
automatically.

**+30 tests** in `tests/test_ethiopian_gamma4.py`:
TestGamma4DataFile × 7, EthiopianCommentariesLoader × 8,
DetectorContract × 9, KindIsRegistered × 2, Coverage × 4.

**2990 / 2991 tests pass serially (1 skipped); 11/11 lint clean.**

Forward reference: γ.4.x is the natural follow-on — NPNF +
Charles ETL into the 1K-note corpus the PROPOSAL §6 names as
the eventual target. Logged in CHANGELOG so the linter's
"phase mentioned in code" check stays clean.

## Prior task

**ο.4 archive.org auto-upload** shipped 2026-05-11. Month 5 #7
— CLOSES Month 5. Drop-to-archive.org button on /exec; composes
ε.7 press-kit ZIP + S3-style PUT + ε.6 distribution auto-mark.

Three pieces:
- `scripts/core/archive_org.py` — `ENV_ACCESS_KEY` /
  `ENV_SECRET_KEY` / `ENV_CREATOR` env-var name constants;
  `DISTRIBUTION_CHANNEL = "archive_org"` matches
  distribution.DISTRIBUTION_CHANNELS; `IDENTIFIER_PREFIX_DEFAULT
  = "yhwh-bible-"`; `ARCHIVE_S3_BASE = "https://s3.us.archive.org"`;
  `is_configured()` True iff both env vars set + non-whitespace;
  `sanitize_identifier(edition_id, *, prefix)` collapses invalid
  chars → dash, strips leading dots/dashes, ≥5-char + ≤100-char
  guards, empty input → "yhwh-bible-untitled" fallback;
  `build_metadata_headers(edition, blurbs)` emits the full
  x-archive-meta-* header set (title / description / mediatype=
  texts / collection=opensource / language=eng / creator /
  licenseurl=CC0) with CR/LF stripping (defense against HTTP
  response splitting); `upload_press_kit(edition, blurbs,
  zip_bytes, *, filename, http_fn=None)` PUTs via injectable
  http_fn (defaults to scripts.core.http.put with the archive-
  org upload allowlist); exceptions from http_fn become
  ok:False envelope rather than re-raise; identifier still
  computed on network failure so audit trail can correlate.
- `scripts/core/http.py` extended — new `put(url, body, *,
  headers, timeout, retries, backoff, retry_on_status,
  allowlist, sleep_fn, urlopen)` returning (status_code,
  response_bytes); mirrors get()'s retry / timeout / SSRF
  discipline (fails closed on missing allowlist). New
  `DEFAULT_ARCHIVE_ORG_UPLOAD_ALLOWLIST = {"s3.us.archive.org",
  "archive.org"}` frozenset kept separate from PD-sources
  allowlist since uploads are privileged write traffic.
- `scripts/api/archive_org.py` — `api_archive_org_status()` GET
  returns `{configured, message, identifier_prefix,
  env_var_access, env_var_secret}` (env var *names* surfaced so
  UI can tell publisher exactly what to set);
  `api_archive_org_upload(edition_id, payload, *, http_fn=None)`
  POST composes press_kit.build_zip + archive_org.upload_press_kit
  + distribution.mark_shipped(edition_id, "archive_org",
  url=...) — returns one envelope describing all three side-
  effects with distribution_marked + distribution_error fields;
  503 when creds missing; 404 on unknown edition; upload
  failure → ok:False with distribution NOT marked; distribution
  side-effect failure → upload reported ok:True but
  distribution_marked=False with the exception in
  distribution_error. Audit-logged.

/exec extended with archive-org section co-located with press-
kit (the upload composes press-kit ZIP): status banner loaded
from /api/archive-org/status names the exact env vars to set;
Upload button disabled by default until status confirms
configured=true, POSTs to /api/archive-org/upload/<edition>
with ζ.6 toast on result, refreshes distribution checklist via
loadDistribution() so the auto-marked archive_org cell flips
in the UI.

Routes registered: GET `/api/archive-org/status` →
`_SIMPLE_GET_ROUTES`; POST `/api/archive-org/upload/<edition>`
→ `_POST_ROUTES` (count test 8→9).

**+38 tests** in `tests/test_archive_org_omicron4.py`:
TestOmicron4Constants × 4, IsConfigured × 3, SanitizeIdentifier
× 5, MetadataHeaders × 4, UploadPressKit × 5, ApiStatus × 2,
ApiUpload × 5, ExecTemplate × 4, RouteRegistration × 2,
HttpPutHelper × 3, Integration × 1.

**2960 / 2961 tests pass serially (1 skipped); 11/11 lint clean.**

**MONTH 5 CLOSED** — all 7 non-money items shipped (Δ.15 /
ε.1 / ε.2 / ε.3 / ε.6 / ε.7 / ο.4).


---

*Prior-task entries from before ο.4 (Month 5 #7) pruned 2026-05-12
per AUDIT_2026-05-12 §4d (IN_FLIGHT chain bloat). The authoritative
chronological record lives in `dev/CHANGELOG.md`. Each prior task
above also has its own CHANGELOG entry with full detail.*
