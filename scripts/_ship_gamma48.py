"""γ.4.8 ship — Mäṣḥafä Mäqabyan (Three Books of Meqabyan) seed wave.
OPENS THE SIXTH PATRISTIC/CANONICAL VOICE in the γ.4 corpus — the third
uniquely-Tewahedo-canonical text (alongside 1 Enoch / Mäṣḥafä Hēnok and
Jubilees / Mäṣḥafä Kufāle).

40 verse-keyed seed entries spanning the three Mäqabyan books:
- 1 Mq (20 entries) across 14 chapters — martyrology of Maqabis-of-
  Benjamin and his five sons against the Chaldean king Ṣiruṣaydan;
  contains the EPONYM verse 2:14 from which the entire trilogy
  takes its title.
- 2 Mq (12 entries) across 11 chapters — Maqabis-of-Moab conversion
  cycle (the longest portrait of a Gentile convert in the entire
  EOTC canon) + a second martyrdom-cycle of his sons + the death of
  Ṣiruṣaydan + the anti-sectarian resurrection-polemic (vs Jews +
  Samaritans + Pharisees + Sadducees).
- 3 Mq (8 entries) across 5 chapters — homiletic anthology with the
  most theologically distinctive content of the trilogy: the first-
  person speech of the Devil + the Satan-refused-to-worship-Adam
  tradition + the "tenth tribe" angelic hierarchy + the four-elements
  anthropology + the EOTC canonical definition of "complete
  repentance" (ፍጹም ንስሓ).

γ.4.8 had been DEFERRED across the entire γ.4 corpus history — the
source corpus _meta.source ledger carries the marker "γ.4.8 Mäqabyan
seed (DEFERRED — PD source acquisition pending)" repeatedly through
γ.4.2.C/γ.4.2.D/γ.4.3/γ.4.5.B-E. The phase letter was held vacant
deliberately, waiting for PD source acquisition. The 2026-05-14 user-
contributed CC0 1.0 English translation (archive.org/details/three-
books-of-meqabyan-cc0-translation, translated from Modern Amharic of
the EOTC Bible at nehemiah-osc.org) is the canonical unblocker.
γ.4.8 ships at the moment the corpus's last structural gap closes.

Source provenance (per the user's SOURCES.md routing guide):
- Primary text: CC0 1.0 English translation (May 2026) from the
  Modern Amharic of the EOTC Bible (nehemiah-osc.org).
- Principal scholarly apparatus: Josef Horovitz, "Das äthiopische
  Maccabäerbuch," Zeitschrift für Assyriologie XIX (1905), pp. 194-
  233 — PD primary scholarly study, the foundational Western
  treatment of Meqabyan.
- 64-citation third-pass audit verdict matrix (CROSS_REFERENCE_
  APPENDIX.md): 57 verified / 4 documentable-errors-corrected / 3
  interpretive-readings-flagged / 7 newly-discovered-parallels-added.
- Tier 1 (use as-is, per SOURCES.md §7): all biblical citations,
  geographic/historical-context claims, verified Horovitz findings,
  Round-3-corrected patristic/pseudepigraphic citations.
- Tier 3 (reframe as interpretive, per SOURCES.md §7): Christological
  readings of 3 Mq (Horovitz's "von Christus nirgends die Rede"
  caveat retained); Aksumite-to-Solomonic dating widened to 4th-14th
  c.; Prov 8:22-30 reapplied from Wisdom to Adam at 3 Mq 4:15-18
  (creative midrashic move, not standard exegesis).

Voice-mix impact — γ.4.8 OPENS THE SIXTH VOICE:

    Pre-γ.4.8 (1367 entries):           Post-γ.4.8 (1407 entries):
      Cyril           668  48.87%          Cyril           668  47.48%
      Jubilees        200  14.63%          Jubilees        200  14.22%
      1 Enoch         192  14.05%          1 Enoch         192  13.65%
      Ephrem          157  11.49%          Ephrem          157  11.16%
      Athanasius      150  10.97%          Athanasius      150  10.66%
                                           Meqabyan         40   2.84%  ← THIS SHIP
                                                          ────
                                                          1407 entries

Cyril remains plurality-leader at 3.34× next-single-father (668 vs
200). Patristic-anchor majority (Cyril + Ephrem + Athanasius) holds
at ~69.2%; the Tewahedo-distinctive-canonical voices (Mäṣḥafä Hēnok
+ Mäṣḥafä Kufāle + Mäqabyan) hold (192+200+40)/1407 = 30.8% — for
the first time the three uniquely-Tewahedo canonical texts together
constitute a numerically significant block. The voice-composition
becomes a SIX-VOICE chorus (Cyril plurality + Ephrem patristic +
Athanasius patristic + 1 Enoch Tewahedo-canonical + Jubilees
Tewahedo-canonical + Mäqabyan Tewahedo-canonical). Requires ω.41 §1
extension to codify the six-voice composition (paired ω.42 hygiene
bundle in same commit).

Distribution (40 entries):
- 1 Mq (20): 2:5 + 2:14 + 2:17 + 2:22 + 2:27 + 3:1 + 5:1 + 6:1 + 8:1
  + 10:1 + 13:12 + 14:15 + 17:1 + 28:1 + 30:7 + 33:1 + 34:1 + 36:22
  + 36:29 + 36:45
- 2 Mq (12): 1:1 + 1:10 + 2:1 + 2:4 + 3:2 + 4:15 + 6:1 + 12:11 + 14:1
  + 14:19 + 17:1 + 18:7
- 3 Mq (8): 1:1 + 1:3 + 1:15 + 2:1 + 4:5 + 4:8 + 4:34 + 10:1

Cumulative-arc plan (estimated):
- γ.4.8 seed (THIS SHIP): 40 entries across 12 books, 3 Mäqabyan books opened
- γ.4.8.B detail wave (future): Mäqabyan I detail — deepens 1 Mq seeds
- γ.4.8.C detail wave (future): Mäqabyan II detail — deepens 2 Mq seeds
- γ.4.8.D detail wave (future): Mäqabyan III detail — deepens 3 Mq seeds
- γ.4.8.E arc-close (future): EIGHTH §8.1 instance — capstones + §8.1
  PIN #1+#2+#3 (Meqabyan count milestone ≥120-160; all_N_sections_
  covered exhaustiveness; _meta synchronization)

Run from project root: python scripts/_ship_gamma48.py

Post-ship pipeline (matches γ.4.9.x precedent):
    PYTHONUTF8=1 python scripts/run_ethiopian_at_scale.py
    PYTHONUTF8=1 python scripts/batch_promote_xrefs.py --kind comm-ethiopian

ELEVENTH production-scale verification of the N-W4 idempotency
contract. Notes-file impact: fills the empty mq1.py + mq2.py +
mq3.py files for the first time in the project's history (each was
0-tuple per AUDIT_2026-05-13-DEEP D-C1 finding).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

JSON_PATH = Path("content") / "sources" / "ethiopian_commentaries.json"

ATTR_MEQ = (
    "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — "
    "Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek "
    "LXX 1-4 Maccabees (different content; shared title only). English "
    "translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) "
    "by Claude (Anthropic) with collaborator, May 2026. Creative Commons "
    "CC0 1.0 Universal Public Domain Dedication "
    "(archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus "
    "integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift "
    "für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. "
    "64-citation third-pass audit verdict matrix; 57 verified, 4 errors "
    "corrected, 3 interpretive readings flagged, 7 newly discovered parallels "
    "added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range "
    "(4th-14th c. CE); precise composition date undetermined in current "
    "scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 "
    "chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 "
    "chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's "
    "death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-"
    "refused-Adam tradition + resurrection-doctrine)."
)


def meq(book: str, chapter: int, verse: int, work: str, summary: str) -> dict:
    return {
        "book": book,
        "chapter": chapter,
        "verse": verse,
        "father": "Meqabyan (Ethiopian tradition)",
        "work": work,
        "year": 600,
        "summary": summary,
        "attribution": ATTR_MEQ,
    }


WORK_MQ1 = "First Book of Meqabyan (Mäṣḥafä Mäqabyan I)"
WORK_MQ2 = "Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)"
WORK_MQ3 = "Third Book of Meqabyan (Mäṣḥafä Mäqabyan III)"


NEW_ENTRIES: list[dict] = [
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 1 — FIRST BOOK OF MEQABYAN (20 entries across 14 chapters)
    # Martyrology of Maqabis-of-Benjamin + his five sons vs Ṣiruṣaydan.
    # ────────────────────────────────────────────────────────────────────────
    meq(
        "mq1",
        2,
        5,
        WORK_MQ1,
        "'We have the God of our fathers, to whom we bow down — He who "
        "created heaven and earth, the sea and what is in it, the sun and "
        "the moon, the stars and the clouds. He is the true God whom we "
        "worship and in whom we trust' — the Meqabyan brothers' creation-"
        "confession of faith, framed as a CREEDAL CORRECTIVE that inverts "
        "the Chaldean king Ṣiruṣaydan's claim at 1:26-27 that his idols "
        "created the heavens, sun, moon, stars, winds and rains. The "
        "creation-formula correctly reassigns creation to the God of the "
        "patriarchs. Functions liturgically as the EOTC anti-idolatry creed "
        "rooted in the first commandment + Genesis 1 creation-account.",
    ),
    meq(
        "mq1",
        2,
        14,
        WORK_MQ1,
        "'Unless you bring us those warriors — THE MEQABYANS — we will burn "
        "your city with fire' — THE EPONYM VERSE of the entire trilogy. "
        "The king's troops apply the collective designation መቃብያንን (the "
        "Meqabyans) to Maqabis-of-Benjamin's sons. From this naming the "
        "ENTIRE THREE-BOOK TRILOGY (1 Mq + 2 Mq + 3 Mq) takes its title. "
        "The Geʽez form, retained in the Amharic, is the source of all later "
        "renderings (Meqabyan, Maqabyan, Maccabean in popular English usage). "
        "Per Horovitz 1905 p. 195 fn. 3 + Dillmann Lexicon Linguae "
        "Aethiopicae (1865): etymology shows Seleucid-coin attestation under "
        "Antiochus IV — but the Ethiopian Meqabyan narrative is otherwise "
        "INDEPENDENT of the Greek Maccabees (Horovitz 'von Christus nirgends "
        "die Rede'; the books are distinctively Ethiopian in content).",
    ),
    meq(
        "mq1",
        2,
        17,
        WORK_MQ1,
        "'They turned their faces toward the east, and stretching out their "
        "hands, they prayed together to God' — the eastward orientation in "
        "prayer is a FIXED EOTC LITURGICAL POSTURE (codified in Didascalia "
        "Apostolorum II.57, retained in Ethiopian practice). The verse's "
        "opening prayer-question functions as the brothers seeking divine-"
        "permission to refuse the king's edict — the resistance is not "
        "spontaneous defiance but a SANCTIONED ACT sought through prayer. "
        "Parallels Daniel 6:10 (Daniel praying with windows opened toward "
        "Jerusalem). The Tewahedo Office (Säʿatat / Liturgy of the Hours) "
        "preserves eastward-prayer as the canonical posture for all "
        "liturgical prayer.",
    ),
    meq(
        "mq1",
        2,
        22,
        WORK_MQ1,
        "'O Lord, God of our fathers — who did Your will and remained "
        "steadfast in Your law — YOU WHO SEARCH THE KIDNEYS AND THE HEART, "
        "God of Abraham, of Isaac, and of Jacob: as for us, we have trusted "
        "in You with our whole heart' — TRIPLE-PATRIARCH INVOCATION "
        "(Abraham + Isaac + Jacob, the standard EOTC liturgical formula) "
        "paired with the kidneys-and-heart-searcher epithet (ኵላሊትንና ልቡናን "
        "የምትመረምር) — a direct rendering of Psalm 7:9 / Jeremiah 11:20 / "
        "Revelation 2:23 (heart-and-kidneys triad). The composer worked "
        "within sustained Septuagintal idiom even though the narrative "
        "content is independent. The patriarchal invocation locks the "
        "brothers into covenant-history.",
    ),
    meq(
        "mq1",
        2,
        27,
        WORK_MQ1,
        "First death-and-resurrection scene of the trilogy — establishes "
        "the resurrection theme that will DOMINATE 3 Meqabyan. The brothers "
        "die under Ṣiruṣaydan's command and are subsequently restored "
        "(continuing into chs. 3-4), prefiguring the cycle that defines the "
        "Meqabyan martyrology: faithful witnesses die-and-rise as the "
        "demonstration of God's resurrection-power. Theologically anchors "
        "the entire trilogy's resurrection-doctrine; structurally inverts "
        "the LXX 2 Maccabees 7 seven-brothers martyrdom in that the "
        "Meqabyan brothers are physically formidable warriors who CHOOSE "
        "surrender to a higher commandment (cf. 2:8-10 bear-strangling + "
        "lion-killing feats reminiscent of Samson Judg. 14:5-6 and David's "
        "mighty men 2 Sam. 23:8-23).",
    ),
    meq(
        "mq1",
        3,
        1,
        WORK_MQ1,
        "Martyrdom climax: a voice from heaven names the three sons "
        "EXPLICITLY — Abya, Sila, Fentos (አብያ፥ ሲላ፥ ፈንቶስ) — and commands "
        "them to accept martyrdom. They are scourged, imprisoned three days, "
        "brought to the public square, tortured. The 'FIVE SONS OF "
        "MAQABIS' formulation (developed across chs. 3-4) is DISTINCTIVE to "
        "the Ethiopian narrative — it has NO parallel in the LXX 2 "
        "Maccabees account of the seven brothers. The bowing-beasts topos "
        "is paralleled in Daniel 6:22 and recurs across Christian martyr-"
        "acts (e.g. Acts of Paul and Thecla). Three-day imprisonment "
        "echoes Jonah 1:17 + Christ's three days in the tomb (Mt 12:40), "
        "patristically read as resurrection-figure.",
    ),
    meq(
        "mq1",
        5,
        1,
        WORK_MQ1,
        "Catalogue of proud kings whom God humbled — Re'aytawi (textually "
        "corrupt name, likely Pharaoh per Horovitz 1905 + crux-flag at "
        "CROSS_REFERENCE_APPENDIX §1 Mq 5:1), Nimrod, and Nebuchadnezzar — "
        "each given as moral exemplar against pride. The Re'aytawi crux is "
        "philologically interesting: the closest Geʽez tradition is the "
        "Conflict of Adam and Eve with Satan (Geʽez Adambuch — Dillmann "
        "1853 / Trumpp 1880 / Malan 1882) which uses comparable demonology-"
        "vocabulary. The chapter's homiletic pivot from narrative-martyrology "
        "to sustained-prophetic-indictment shapes the rest of 1 Mq's "
        "structure (chs. 5-36 are primarily homiletic-prophetic rather than "
        "narrative-martyrological).",
    ),
    meq(
        "mq1",
        6,
        1,
        WORK_MQ1,
        "Heavenly-palace ekphrasis — one of the most beautiful passages in "
        "1 Mq (vv. 1-18): the description of the dwelling of righteous "
        "kings (Abraham + Isaac + Jacob + David + Solomon + Hezekiah) in "
        "their heavenly abode. The ekphrasis-of-the-righteous-dwelling is a "
        "patristic-and-late-antique standard genre (cf. 4 Ezra 7:88-99, 2 "
        "Baruch 51:1-12, Apocalypse of Paul §§14-18); Meqabyan's distinctive "
        "feature is the SPECIFIC ROYAL roster (Hezekiah's addition to the "
        "patriarchal triad shifts the typology from patriarchal-fatherhood "
        "to royal-covenant-faithfulness — the Davidic-and-Hezekian "
        "exemplars of right kingship in 2 Kings / Isaiah 38). The second "
        "half of the chapter (vv. 20-38) is the Saul-Samuel-Amalek pericope "
        "exegeting 1 Sam 15 obedience-over-sacrifice.",
    ),
    meq(
        "mq1",
        8,
        1,
        WORK_MQ1,
        "Systematic exposition of resurrection through four natural "
        "parables — the MOST THEOLOGICALLY POLISHED chapter in 1 Mq. The "
        "argument proceeds through: (1) the vine and the tree (vv. 1-5), "
        "(2) the four elements gathered into the body (vv. 6-15), (3) "
        "day-and-night seasonal cycle (vv. 16-21), (4) the seed buried "
        "and rising (vv. 22-32). Per CROSS_REFERENCE_APPENDIX §10 the seed-"
        "buried argument (1 Mq 8:22-32) is the STRONGEST PAULINE PARALLEL "
        "in the entire trilogy to 1 Corinthians 15:36-38 ('that which thou "
        "sowest, thou sowest not that body that shall be, but bare grain... "
        "but God giveth it a body as it hath pleased him'). The four-element "
        "anthropology (earth + water + fire + wind) is the Empedoclean/"
        "Galenic Greek natural-philosophical anthropology mediated to "
        "Ethiopia via Syriac and Coptic patristic literature (parallel at "
        "3 Mq 4:10 + 2 Mq 14:19).",
    ),
    meq(
        "mq1",
        10,
        1,
        WORK_MQ1,
        "Argument-from-ancestral-burial for resurrection: the patriarchs — "
        "Adam + Abel + Seth + Noah + Shem + Abraham + Isaac + Jacob + "
        "Joseph + Moses + Aaron — sought to be buried with their kin "
        "PRECISELY SO THAT, at the resurrection, they would rise together. "
        "The reading reverses the typical ancestor-veneration motif: rather "
        "than the dead remaining in tombs as a memorial, burial-with-kin "
        "becomes a PROVISIONAL-PRACTICE awaiting communal resurrection. "
        "Connects to Genesis 23 (Abraham purchasing the Cave of Machpelah "
        "for Sarah's burial) + Genesis 49:29-32 (Jacob's burial instructions) "
        "+ Joshua 24:32 (Joseph's bones brought up from Egypt). The "
        "patristic parallel is in resurrection-of-the-flesh treatments — "
        "Tertullian De Resurrectione Carnis §52, Theophilus of Antioch Ad "
        "Autolycum 1.13.",
    ),
    meq(
        "mq1",
        13,
        12,
        WORK_MQ1,
        "EXPLICIT LUCIFER-FALL PASSAGE — vv. 12-13 directly cite Isaiah "
        "14:12-14 ('How art thou fallen from heaven, O day-star, son of the "
        "morning! how art thou cut down to the ground... I will ascend into "
        "heaven, I will exalt my throne above the stars of God'). 1 Mq "
        "preserves the standard patristic identification of Isa 14 with "
        "the fall of Satan (cf. Tertullian Adversus Marcionem 2.10, Origen "
        "De Principiis 1.5.4-5, Augustine City of God 11.15, Cassiodorus "
        "Commentary on Psalms). Meqabyan reads Isa 14 as theological-"
        "narrative — Lucifer's pride-and-fall as the originating event of "
        "the cosmic moral order, the structural pre-condition for the "
        "human moral arena that the rest of the trilogy occupies. The "
        "chapter is the ESCHATOLOGICAL PIVOT of 1 Mq.",
    ),
    meq(
        "mq1",
        14,
        15,
        WORK_MQ1,
        "Moses-and-Joshua exchange about the 'SOUND OF UNFERMENTED WINE' "
        "during the Sinai golden-calf episode — a WITTY GEʽEZ ETIOLOGICAL "
        "moment unique to Meqabyan within the Pentateuchal-reception "
        "tradition. The exchange exegetes Exodus 32:17-18 (Joshua hearing "
        "'the noise of war in the camp' / Moses replying 'it is not the "
        "voice of them that shout for mastery, neither is it the voice of "
        "them that cry for being overcome: but the noise of them that sing "
        "do I hear') by giving the 'singing' a specifically intoxicated "
        "tonality. The chapter as a whole retells the Flood-Noah covenant "
        "(vv. 1-3) + the Decalogue in five-commandment form (vv. 7-9) + "
        "the golden-calf narrative (vv. 11-18). The five-commandment "
        "Decalogue summary is itself a distinctive EOTC catechetical form.",
    ),
    meq(
        "mq1",
        17,
        1,
        WORK_MQ1,
        "SEBELYANOS (ሰብልያኖስ) — the unique-to-Meqabyan teacher of the "
        "Edomites and Amalekites, identified as a GEʽEZ RENDERING of "
        "BELIAR/BELIAL (the Second Temple personification of evil; cf. 2 "
        "Corinthians 6:15, Jubilees 1:20, Damascus Document IV.13-19, "
        "Testament of Reuben 4:7-11, Sibylline Oracles 3:63-74). Meqabyan "
        "preserves the Beliar-as-Antichrist-teacher tradition that runs "
        "from Qumran through Pauline polemic through patristic apocalyptic. "
        "Sebelyanos reappears at 2 Mq 9:2 as the teacher of Adam's first "
        "sin — extending the Beliar-tradition to a primordial-temptation "
        "role beyond the second-temple apocalyptic. The name is DIAGNOSTIC "
        "for Meqabyan's relationship to Second Temple Jewish-apocalyptic "
        "vocabulary preserved in Ethiopian Christianity.",
    ),
    meq(
        "mq1",
        28,
        1,
        WORK_MQ1,
        "SALVATION-HISTORY RETELLING — the longest chapter in 1 Meqabyan "
        "(49 verses) and the most explicit retelling of the biblical "
        "narrative in the entire book. Compresses canonical and "
        "deuterocanonical history from CAIN THROUGH ESTHER into a single "
        "sweep. Function: provides the Meqabyan reader with the "
        "scriptural-context for the trilogy's martyrologies, locating "
        "Maqabis-of-Benjamin's witness within the longer arc of Israel's "
        "faithful + unfaithful exemplars. Parallels the Sirach 44-50 "
        "'Praise of Famous Men' genre, Hebrews 11 'faith heroes' chapter, "
        "1 Maccabees 2:51-60 Mattathias's deathbed roll-call, and 4 "
        "Maccabees 18:11-13 + 18:7-8 (per CROSS_REFERENCE_APPENDIX-broadened "
        "2 Mq parallels). The Meqabyan version's distinctive integration "
        "of Esther into the patriarchal-prophetic roll is a Tewahedo-"
        "canonical reception emphasis.",
    ),
    meq(
        "mq1",
        30,
        7,
        WORK_MQ1,
        "'He who honors me, I will honor; he who loves me, I will love' — "
        "DIRECT CITATION of 1 Samuel 2:30 (the covenant-honor formula "
        "given by God to Eli the priest, prophesying the reduction of Eli's "
        "house). The verse functions in Meqabyan as the CONCISE COVENANT-"
        "FORMULA for the entire trilogy's theology: faithful witness "
        "(martyrdom-or-conversion) draws divine-honor; apostasy draws "
        "divine-disregard. The chapter as a whole develops God's renunciation "
        "of the house of Saul (vv. 1-6) leading to this formula at v. 7. "
        "The Tewahedo Liturgy of the Word recites 1 Sam 2:30 at the "
        "Trinity-Sunday and Royal-Lectionary offices.",
    ),
    meq(
        "mq1",
        33,
        1,
        WORK_MQ1,
        "'As David said, MEN ATE THE BREAD OF ANGELS' — direct citation of "
        "Psalm 78:25 LXX (ἄρτον ἀγγέλων ἔφαγεν ἄνθρωπος, 'the bread of "
        "angels man did eat'). Meqabyan reads the wilderness-manna "
        "typologically as ANGELIC-FOOD given to Israel — a reading "
        "preserved in Christian patristic and Jewish-Targumic tradition "
        "(cf. Wisdom 16:20 in the LXX/Apocrypha — 'thou feddest thine own "
        "people with angels' food'; Tg. Ps-J Exodus 16:15 expands the "
        "manna's angelic origin). The chapter develops a CONTRAST between "
        "the light-filled heavenly city awaiting good kings (vv. 8-10) and "
        "the Gehenna prepared for the wicked — anchoring the eschatological "
        "framework of 1 Mq's closing chapters.",
    ),
    meq(
        "mq1",
        34,
        1,
        WORK_MQ1,
        "FOUR-KINGDOMS APOCALYPSE — the most internally diagnostic chapter "
        "in 1 Mq for dating and provenance. Opening verses lay out a "
        "sequence of kingdom-pairings climaxing in an extraordinary claim "
        "about kingdom-establishment-over-kingdom. The four-kingdoms "
        "schema is parallel to Daniel 2 + Daniel 7 (the Babylon-Persia-"
        "Greece-Rome succession), but Meqabyan's specific ethnographic "
        "list — Judah + Cyprus + Samaria + Damascus + Babylon + India + "
        "Nubia + Sheba + Egypt + Ethiopia — extends the Danielic horizon "
        "INTO THE EAST (India + Sheba + Ethiopia) in a way distinctive to "
        "Ethiopian-Christian-apocalyptic. The chapter also contains a "
        "Nebuchadnezzar-to-Daniel citation about 'the spirit of God upon "
        "you' (Dan 5:14 echo), locating the apocalypse-genre within the "
        "Danielic tradition.",
    ),
    meq(
        "mq1",
        36,
        22,
        WORK_MQ1,
        "THEOLOGICAL CLIMAX OF 1 MEQABYAN — the triple-formula 'Abraham is "
        "my friend; Isaac is my favored one; Jacob is the beloved of my "
        "heart; in them I have been praised, says God who is all-powerful.' "
        "'Abraham my friend' (Abraham wedajē) directly echoes James 2:23 "
        "('Abraham believed God... and he was called the friend of God'), "
        "itself drawing on Isaiah 41:8 ('Abraham my friend' — ahavi / "
        "philos mou) and 2 Chronicles 20:7. The TRIPLE-PATRIARCH STRUCTURE "
        "is standard liturgical idiom, but the SPECIFIC GRADIENT (friend → "
        "favored → beloved) appears to be a Meqabyan composition. The "
        "pairing with 36:43 (Genesis 15:6 'Abraham believed God and it "
        "was reckoned to him as righteousness' — the same verse cited by "
        "Paul at Romans 4:3 and James at James 2:23) REPLICATES THE EXACT "
        "NEW TESTAMENT ABRAHAM-TYPOLOGY: faith-reckoned-as-righteousness + "
        "friendship-with-God.",
    ),
    meq(
        "mq1",
        36,
        29,
        WORK_MQ1,
        "HELLENISTIC-DEITY CATALOG — the most striking single piece of "
        "Hellenistic-era evidence in 1 Mq: Baal-of-Canaan + Dagon-of-the-"
        "Philistines + APOLLON (Greek Apollo) + ARṬEMADES (Greek Artemis "
        "with Geʽez -des ending) + SERAPION (Hellenistic-Egyptian Serapis). "
        "The pairing of Apollo + Artemis + Serapis is the STANDARD "
        "IMPERIAL-ROMAN-ERA civic pantheon of the eastern Mediterranean. "
        "The presence of SERAPIS is especially DIAGNOSTIC: the Serapeum "
        "of Alexandria was destroyed by Christians in 391 CE, after which "
        "the cult quickly declined. This catalog therefore most plausibly "
        "reflects a setting BEFORE c. 400 CE when Serapis-worship was "
        "still a live religious competitor — or alternatively a literary "
        "preservation of an earlier-stratum tradition. Either way, the "
        "verse is a TERMINUS-A-QUO anchor for Meqabyan's earlier-stratum "
        "composition layer (per Horovitz 1905 + CROSS_REFERENCE_APPENDIX "
        "§61 widened-dating).",
    ),
    meq(
        "mq1",
        36,
        45,
        WORK_MQ1,
        "DOCTRINAL CAPSTONE of 1 Meqabyan: 'the dead shall rise; those "
        "who did good works shall go to eternal life; and that those who "
        "did evil shall, at the resurrection of the dead, go to eternal "
        "punishment. But the righteous who did good works shall reign with "
        "him forever.' The closing tricolon — (1) the dead rise + (2) the "
        "righteous go to eternal life and reign with God + (3) the wicked "
        "are judged forever — is the TRINITY OF RESURRECTION-DOCTRINE "
        "that establishes the eschatological framework dominating the "
        "remaining two books. Direct parallel to John 5:29 (resurrection-"
        "of-life / resurrection-of-judgment) + Daniel 12:2 (those who awake "
        "to everlasting life / shame and everlasting contempt). Closes with "
        "DOUBLE-AMEN (አሜን፥ አሜን) — the standard EOTC book-closing "
        "doxological formula marking the decisive end of 1 Meqabyan.",
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 2 — SECOND BOOK OF MEQABYAN (12 entries across 11 chapters)
    # Maqabis-of-Moab conversion arc + second martyrdom cycle.
    # ────────────────────────────────────────────────────────────────────────
    meq(
        "mq2",
        1,
        1,
        WORK_MQ2,
        "Opening of 2 Meqabyan: MAQABIS-OF-MOAB (distinct from Maqabis-of-"
        "Benjamin in 1 Mq per Horovitz 1905 p. 195 structural distinction "
        "explicitly verbatim — 'a Benjamite martyr-father' vs 'a Moabite "
        "king'). The Moabite-king Maqabis finds the Jews in Syria between "
        "the two rivers, slaughters them from the Jabbok river to the "
        "square of Jerusalem, destroys the holy city. Functions as "
        "PARALLEL-INVERSE of 1 Mq Ch. 1: where 1 Mq's tyrant was Chaldean "
        "(Ṣiruṣaydan), here the tyrant is Moabite; where there Israel's "
        "defenders were endangered, here Israel itself is destroyed. The "
        "verse establishes Maqabis-of-Moab as the principal protagonist of "
        "2 Mq — beginning his arc at the moral nadir. His subsequent arc "
        "(chs. 2-4) is the LONGEST PORTRAIT of a Gentile convert to "
        "Mosaic religion in the entire Ethiopian biblical canon.",
    ),
    meq(
        "mq2",
        1,
        10,
        WORK_MQ2,
        "'They made the corpses of your servants food for the birds of "
        "heaven. They made the flesh of your righteous ones food for the "
        "wild beasts of the desert' — DIRECT QUOTATION of Psalm 79:2-3 "
        "(LXX 78:2-3 'the dead bodies of your servants have they given to "
        "be food for the birds of the heaven, the flesh of your saints to "
        "the beasts of the earth') — a psalm sung specifically about the "
        "destruction of Jerusalem and the desecration of the Temple. The "
        "quotation locates the present narrative theologically in the "
        "post-586-BCE 'lament-over-Jerusalem' tradition, alongside "
        "Lamentations + Jeremiah's prophecies + Ezekiel's exile-oracles. "
        "Meqabyan's use of Ps 79 is a structural-citation: the psalm becomes "
        "the LITURGICAL FRAME for the 2 Mq destruction-narrative.",
    ),
    meq(
        "mq2",
        2,
        1,
        WORK_MQ2,
        "Prophet RE'AY (ረአይ, literally 'Vision' or 'Seeing') arrives at "
        "Maqabis-of-Moab's court — the PROPHETIC-CONFRONTATION moment. "
        "The name functions as proper-name-or-title ('the Seer,' cf. 1 "
        "Samuel 9:9 'he that is now called a Prophet was beforetime called "
        "a Seer'). The Geʽez phrasing ረአይ የሚሉት ነቢይ ('the prophet whom they "
        "call Re'ay') is itself ambiguous between proper-name and generic "
        "seer-title. Re'ay functions as the prophetic-mediator who delivers "
        "God's warning that initiates Maqabis's conversion-arc — paralleling "
        "Nathan-to-David (2 Sam 12), Elijah-to-Ahab (1 Kgs 21), Jonah-to-"
        "Nineveh-king (Jon 3), and Daniel-to-Nebuchadnezzar (Dan 4) in the "
        "prophet-confronts-king Hebrew-Bible structural template.",
    ),
    meq(
        "mq2",
        2,
        4,
        WORK_MQ2,
        "'Worse than the casting of spears and the shooting of arrows, I "
        "will bring upon you grievous HEART-DISEASE, ECZEMA, AND GOUT' — "
        "the prophet's DISEASE-CATALOG draws on the DEUTERONOMY 28:27-35 "
        "COVENANT-CURSE LIST ('the LORD shall smite you with the boil of "
        "Egypt, and with the hemorrhoids, and with the scab, and with the "
        "itch, of which you cannot be healed... he shall smite you in the "
        "knees, and in the legs, with a sore botch that cannot be healed'). "
        "The threat is calibrated as worse than warrior's-death-by-arrow "
        "that Maqabis fears — slow, humiliating, public. Tewahedo penitential "
        "preaching cites Deut 28 alongside 2 Mq 2:4 to articulate the "
        "category of physical-suffering-as-divine-instruction-to-repent. "
        "The chapter closes with Maqabis's sackcloth-and-dust penitential "
        "response (vv. 9-11) paralleling Jonah 3:6 + Esther 4:1.",
    ),
    meq(
        "mq2",
        3,
        2,
        WORK_MQ2,
        "MAQABIS-OF-MOAB DIGS A PIT AND ENTERS IT UP TO HIS NECK, weeping "
        "in extreme self-mortification — one of the MOST DISTINCTIVE "
        "PENITENTIAL IMAGES in Ethiopian biblical literature. The pit-"
        "immersion-penance has no direct biblical parallel and appears "
        "unique to Meqabyan. The closest analogues are the patristic "
        "Egyptian-and-Syrian ascetic-stationary-penance practices (cf. "
        "Apophthegmata Patrum on Egyptian solitary-anchorites; Simeon "
        "Stylites's pillar-station; Theodoret of Cyrus Historia Religiosa "
        "on Syrian ascetics). The chapter as a whole is the CONVERSION "
        "CHAPTER: God responds through the prophet with a long forgiveness-"
        "speech (vv. 3-10) including a direct citation of Exodus 20:5-6 "
        "(third-and-fourth-generation / thousandth-generation formula at "
        "v. 9). Maqabis emerges from the pit (v. 11), confesses, prostrates "
        "himself at the prophet's feet, is raised.",
    ),
    meq(
        "mq2",
        4,
        15,
        WORK_MQ2,
        "MAQABIS-OF-MOAB AS RIGHTEOUS GENTILE CONVERT — Per CROSS_REFERENCE_"
        "APPENDIX-broadened parallels: Ruth Rabbah 2:9 (treating Ruth's "
        "conversion as paradigm for righteous Gentile) + Targum Pseudo-"
        "Jonathan on Ruth 1:16 (with explicit conversion-formula expansion). "
        "Maqabis's reform of his household — removing idols, sorcerers, "
        "and diviners (3:16) + learning Torah from the Jewish captive "
        "children he had brought from Jerusalem (3:17-19) — is the most "
        "explicit Gentile-king-converts-to-Mosaic-religion narrative in "
        "the Ethiopian biblical corpus. The chapter develops Maqabis as "
        "JUDGE-PATTERN exemplar — paralleling Joshua + Gideon + Samson + "
        "Barak + Deborah + Judith (vv. 1-3 catalog) — extending the "
        "deliverer-judge typology to the converted-Gentile-king. The "
        "theological climax of 2 Meqabyan: a Gentile king becomes a "
        "righteous-king-of-Israelite-pattern.",
    ),
    meq(
        "mq2",
        6,
        1,
        WORK_MQ2,
        "MARTYRDOM-AND-APPEARANCE CHAPTER — structurally parallel to 1 Mq "
        "chs. 3-4 but compressed. The sons of Maqabis-of-Moab (named at 2 "
        "Mq 13:1 as the SECOND SET of 'five sons of Maqabis,' mirroring "
        "the first five sons of Maqabis-of-Benjamin in 1 Mq — a NUMBER-"
        "SYMMETRY across the two books) refuse to sacrifice to Ṣiruṣaydan's "
        "idols, are burned in fire, then appear post-mortem to the king "
        "at night with reproach. The post-mortem-appearance topos is "
        "paralleled in 4 Maccabees 17 (the mother-and-seven-sons memorial), "
        "in the apocryphal Acts of the Christian martyrs (Polycarp + "
        "Perpetua + Felicitas appearance traditions), and in patristic "
        "homily on the cult-of-the-martyrs. Meqabyan's distinctive feature "
        "is the GUILT-INDUCING-REPROACH structure: the appearance is "
        "primarily a moral-judgment-on-the-king rather than consolation-"
        "for-the-faithful.",
    ),
    meq(
        "mq2",
        12,
        11,
        WORK_MQ2,
        "DEATH OF ṢIRUṢAYDAN — narrative climax of the trilogy's PRINCIPAL "
        "VILLAIN-ARC that has run from 1 Mq Ch. 1 through 2 Mq Ch. 12 "
        "(the MOST EXTENDED SUSTAINED-VILLAIN narrative in the Meqabyan "
        "corpus). Ṣiruṣaydan's death pattern echoes the divine-judgment-"
        "on-prideful-kings tradition: Nebuchadnezzar at Daniel 4:31-37 "
        "(driven to graze like an ox) + Herod at Acts 12:23 (eaten by "
        "worms) + Antiochus IV at 2 Maccabees 9 (worm-infested + foul-"
        "smelling demise). Per Horovitz 1905 + Dillmann Lexicon Linguae "
        "Aethiopicae (1865): Ṣiruṣaydan etymology connects to TYRE + "
        "SIDON (Ṣiru + Ṣaydan), the Phoenician-coastal cities + canonical-"
        "type for arrogant maritime-commercial power (Ezekiel 26-28 "
        "prophecies). The villain-name is itself a TYPOLOGICAL CIPHER "
        "rather than historical-king identification.",
    ),
    meq(
        "mq2",
        14,
        1,
        WORK_MQ2,
        "FOUR SECTARIAN ERRORS ABOUT RESURRECTION named explicitly — THE "
        "JEWS, THE SAMARITANS, THE PHARISEES, AND THE SADDUCEES. Meqabyan "
        "preserves the Second-Temple-and-Tannaitic categorical distinction "
        "between these four groups (cf. Josephus Antiquities 18.1.2-5 on "
        "the four philosophical schools; Acts 23:6-8 on Pharisees-and-"
        "Sadducees-disagreement-about-resurrection). The 'Jews' category "
        "in Meqabyan refers to non-Christian Israel ('those who reject the "
        "resurrection of the body'). The chapter is THE LONGEST IN 2 "
        "MEQABYAN (36 verses) and the most theologically distinctive: the "
        "ANTI-SECTARIAN RESURRECTION-POLEMIC chapter. Meqabyan's "
        "resurrection-polemic structures around refuting each group's "
        "specific error — paralleling the Apostles' Creed clause "
        "'resurrection of the body' against Marcionite + Gnostic + "
        "Sadducean denials.",
    ),
    meq(
        "mq2",
        14,
        19,
        WORK_MQ2,
        "FOUR-ELEMENTS RESURRECTION — Adam's body composed of earth + "
        "water + fire + wind, returned to its elements at death, and "
        "reconstituted at resurrection by God's gathering of those elements. "
        "Direct parallel to 3 Mq 4:10 (where the same anthropology is "
        "given in the creational rather than resurrectional context). The "
        "four-elements doctrine is the EMPEDOCLEAN/GALENIC Greek natural-"
        "philosophical anthropology, mediated to Ethiopian Christianity "
        "via Syriac and Coptic patristic literature (Ephrem Carmina "
        "Nisibena 65; Severus of Antioch Cathedral Homilies). The "
        "resurrection-by-elemental-reconstitution-doctrine is also in "
        "Tertullian De Resurrectione Carnis §52 + Theophilus of Antioch "
        "Ad Autolycum 1.13 (per CROSS_REFERENCE_APPENDIX Stage-3 broadening "
        "at 2 Mq 17). The chapter's CORD-OF-SHEOL image (vv. 10-23) — the "
        "bond dragging soul to Hades grows from mother's womb up through "
        "life — is a unique metaphor in EOTC literature.",
    ),
    meq(
        "mq2",
        17,
        1,
        WORK_MQ2,
        "WHEAT-GRAIN DYING ANALOGY for resurrection — develops 1 Corinthians "
        "15:36 ('thou fool, that which thou sowest is not quickened, "
        "except it die') + John 12:24 ('except a corn of wheat fall into "
        "the ground and die, it abideth alone: but if it die, it bringeth "
        "forth much fruit') with a beautiful symbolic-geography expansion: "
        "water + earth + sun + wind become resurrection-analogues of body "
        "+ soul + fire-grace + breath. The vine-and-its-fruit imagery "
        "(vv. 5-8) echoes Isaiah 5:1-7 + John 15:1-8 (Christ-the-true-vine). "
        "Per CROSS_REFERENCE_APPENDIX Stage-3 broadening: the closest "
        "patristic parallels are Tertullian De Resurrectione Carnis §52 + "
        "Theophilus of Antioch Ad Autolycum 1.13 (late 2nd c.; earliest "
        "extended Christian use of botanical resurrection). The botanical-"
        "resurrection argument is one of the MOST DEVELOPED in patristic "
        "and Tewahedo eschatology.",
    ),
    meq(
        "mq2",
        18,
        7,
        WORK_MQ2,
        "ADAMIC-MORTALITY DOCTRINE — 'we are all sons of Adam, and we shall "
        "all die.' Direct echo of Romans 5:12 ('by one man sin entered into "
        "the world, and death by sin') + 1 Corinthians 15:21-22 ('since by "
        "man came death, by man came also the resurrection of the dead'). "
        "Per CROSS_REFERENCE_APPENDIX-broadened parallels: 2 Baruch 23:4 "
        "('when Adam sinned and death was decreed') + 2 Baruch 48:42-43 + "
        "Apocalypse of Moses (Greek LAE) 14:2 ('on account of you [Adam] "
        "toils and labor were assigned to us') + 4 Maccabees 18:7-8 "
        "(mother's-virginity speech, useful for navigating the persistent "
        "genre-confusion between Meqabyan and LXX 2/4 Maccabees). The "
        "Adamic-mortality doctrine is the THEOLOGICAL FOUNDATION for "
        "Meqabyan's resurrection-doctrine: humans are mortal BECAUSE OF "
        "Adam's sin, and the resurrection is God's RESTORATIVE-RESPONSE "
        "to that primordial mortality.",
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 3 — THIRD BOOK OF MEQABYAN (8 entries across 5 chapters)
    # Homiletic anthology + angelological dialogue + resurrection-doctrine.
    # ────────────────────────────────────────────────────────────────────────
    meq(
        "mq3",
        1,
        1,
        WORK_MQ3,
        "'Concerning the MERCIFUL AND MEEK ONE who is to come in the latter "
        "time, who shall avenge himself against the cruel and deceiving "
        "Devil... the islands of Egypt rejoice.' One of the MOST "
        "DISTINCTIVELY MESSIANIC LINES in the trilogy. 'The merciful and "
        "meek one (ቸርና የዋህ) who is to come in the latter time' echoes "
        "MATTHEW 11:29 ('I am meek and lowly of heart') and the standard "
        "Christian-era messianic vocabulary. 'The islands of Egypt rejoice' "
        "likely draws on Isaiah 19:18-25 (Egypt and Assyria worship the "
        "LORD) — read in Christian patristic tradition as PROPHECY OF "
        "COPTIC AND AKSUMITE CHRISTIANITY. *Philological caveat (per "
        "Horovitz 1905 p. 196 + CROSS_REFERENCE_APPENDIX §62):* Horovitz "
        "noted 'von Christus nirgends die Rede' — there is nowhere any talk "
        "of Christ in Meqabyan, which he understood as deliberately OT-"
        "framed. The Christological reading at 3 Mq 1:1 is therefore "
        "Christian-readerly overlay; a non-Christological messianic reading "
        "is fully possible.",
    ),
    meq(
        "mq3",
        1,
        3,
        WORK_MQ3,
        "DEVIL'S HUBRIS-SPEECH (first-person): 'Who is above me? I will "
        "enter the depths of the sea; I will ascend to heaven; I will see "
        "the deeps; I will grasp the sons of Adam like the chicks of a bird.' "
        "Combines ISAIAH 14:13-14 ('I will ascend into heaven, I will exalt "
        "my throne above the stars of God') + EZEKIEL 28:2-19 (the king of "
        "Tyre's claim to divinity, extended through the cherub-in-Eden "
        "Satan-fall passage at 28:12-19) + 2 THESSALONIANS 2:4 (the man of "
        "lawlessness). The image of seizing humans 'LIKE BIRD-CHICKS' "
        "(እንደ ወፍ ጫጩት) is more visceral than the canonical models — "
        "emphasizing predation. Per CROSS_REFERENCE_APPENDIX Stage-3 "
        "newly-discovered-parallels: Ephrem the Syrian Carmina Nisibena "
        "54.9 + Hymnen contra Haereses 26.4.10 (Syriac patristic etymologies "
        "inherited by the Cave of Treasures); Jacob of Serugh's homilies "
        "on the Good Shepherd / fall of Satan (Bedjan 1905-10 / Brock 2006 "
        "Gorgias reprint).",
    ),
    meq(
        "mq3",
        1,
        15,
        WORK_MQ3,
        "THE SATAN-REFUSED-TO-WORSHIP-ADAM TRADITION — the most diagnostic "
        "angelological verse in 3 Meqabyan. The Devil himself states: 'For "
        'when I said "I will not bow to my inferior," God for the sake of '
        "their father Adam humbled me from my glory.' Found principally in: "
        "(a) the Latin VITA ADAE ET EVAE §§12-17 (Pettorelli-Kaestli CCSA "
        "18, Brepols 2012; absent from the Greek Apocalypse of Moses), where "
        "Satan tells Adam: 'on your account I was cast out from the "
        "heavens... when God blew into you the breath of life, and you "
        "were made in the image of God, Michael led you and said to me: "
        "Worship the image of God. And I said: I will not worship one "
        "inferior to me'; (b) 2 ENOCH 29:4-5 (longer recension J; cf. "
        "31:3-6 linking the fall explicitly to Adam); (c) the QUR'AN seven-"
        "passage cluster (Sura 2:34; 7:11-18; 15:28-38; 17:61; 18:50; "
        "20:116; 38:71-78 — Iblis refuses to bow to Adam); (d) the EOTC's "
        "CAVE OF TREASURES §2 (Budge 1927; Reeves OR ed.); (e) the proximate "
        "Geʽez recipient, the CONFLICT OF ADAM AND EVE WITH SATAN "
        "(Dillmann 1853 / Trumpp 1880 / Malan 1882); (f) among Jewish "
        "sources, only BERESHIT RABBATI of Moses ha-Darshan (Narbonne, 11th "
        "c.; Albeck ed. 1940 pp. 24-25). The verse provides the CANONICAL "
        "EOTC EXPLANATION FOR THE ORIGIN OF DEMONIC ENMITY TOWARD HUMANS: "
        "Satan was deposed BECAUSE he refused to worship the image of God "
        "in Adam.",
    ),
    meq(
        "mq3",
        2,
        1,
        WORK_MQ3,
        "'But you, who could not deceive my servant JOB — by honor I will "
        "inherit your throne to those of them; those whom you could not "
        "deceive, I will give the Kingdom of Heaven — says God who rules "
        "all.' Direct reference to JOB 1-2 — the prologue dialogue in "
        "which Satan attempts (with God's permission) to deceive Job "
        "through suffering and fails. The verse functions as GOD'S RESPONSE "
        "to the Devil's petition in Ch. 1: those whom the Devil could NOT "
        "deceive shall inherit his lost glory. Theological move: the "
        "Mäqabyan dialogue-form delivers what Augustine articulates in "
        "Enchiridion §29 + City of God 22.1 + Anselm Cur Deus Homo I.16-18 "
        "and Gregory the Great Homiliae in Evangelia 34 — the doctrine "
        "that THE NUMBER OF THE ELECT EQUALS THE NUMBER OF FALLEN ANGELS, "
        "and humans fill the empty seats. Meqabyan's distinctive contribution: "
        "the dialogue-form-delivery via the Devil's-own-petition.",
    ),
    meq(
        "mq3",
        4,
        5,
        WORK_MQ3,
        "ETYMOLOGY OF THE DEVIL'S NAME — explicitly given: 'You became "
        "proud; YOU WERE CALLED THE DEVIL; YOUR ARMIES WERE CALLED DEMONS.' "
        "ዲያብሎስ (Diabolos, the Greek loanword for 'slanderer') and አጋንንት "
        "(demons) become CATEGORY-NAMES DEFINED BY the rebellion-against-"
        "praise act. The verse implies: BEFORE pride, this being had a "
        "DIFFERENT NAME and identity; the name 'Devil' is itself the "
        "CONSEQUENCE OF THE FALL, not its cause. Theologically parallel to "
        "Ezekiel 28:14-15's 'thou wast perfect in thy ways from the day "
        "that thou wast created, till iniquity was found in thee' (the "
        "cherub-in-Eden / king-of-Tyre Satan-fall). The pre-fall name is "
        "patristically given as Lucifer (Latin lucifer = 'light-bearer'; "
        "cf. Tertullian + Origen + Augustine readings of Isa 14:12). "
        "Meqabyan's distinctive contribution: the post-fall name as "
        "etymologically-significant category.",
    ),
    meq(
        "mq3",
        4,
        8,
        WORK_MQ3,
        "'TENTH TRIBE' ANGELIC HIERARCHY — the Devil and his armies were "
        "the TENTH ORDER of angels created to praise God; their rebellion "
        "left the praise INCOMPLETE; God created Adam to fill the missing "
        "tenth. The NINE-ORDERS schema is articulated in PSEUDO-DIONYSIUS "
        "Celestial Hierarchy 6.2 (PG 3:200D), elaborated in chs. 7-9 "
        "(Seraphim/Cherubim/Thrones; Dominations/Powers/Authorities; "
        "Principalities/Archangels/Angels); a different ordering, also of "
        "nine orders, is given in GREGORY THE GREAT Homilies on the Gospels "
        "34 — uniquely Gregory's Hom. 34 unites the nine-orders enumeration "
        "WITH the lost-drachma/lost-sheep parable of Luke 15 in support of "
        "the humans-complete-the-angelic-number doctrine. The humans-replace-"
        "the-fallen-tenth doctrine is also in AUGUSTINE Enchiridion Ch. IX "
        "(§§28-30) + AUGUSTINE City of God 22.1 + ANSELM Cur Deus Homo "
        "I.16-18 (longest chapters in the entire work). Preserved in the "
        "EOTC's Mäṣḥafä Mälaʾek (Book of the Angels). The two strands "
        "(nine orders + humans completing the number) are routinely combined "
        "in late-antique and early-medieval Christian thought.",
    ),
    meq(
        "mq3",
        4,
        34,
        WORK_MQ3,
        "DEFINITION OF 'COMPLETE REPENTANCE' (ፍጹም ንስሓ, *feṣṣum nesseḥa*): "
        "sin + confession + weeping + non-return = full forgiveness. The "
        "verse provides the THEOLOGICAL FOUNDATION of EOTC sacramental "
        "confession, codified later in the FETHA NAGAST (Law of Kings, "
        "13th c.) and the Ethiopian monastic literature. The Devil cannot "
        "repent — not because God will not forgive him, but BECAUSE PRIDE "
        "FORBIDS CONFESSION; Adam can — because humility permits it. The "
        "asymmetry: irredeemability is not about sin's magnitude but about "
        "the refusal-to-confess. Direct parallel to John of Damascus De "
        "Fide Orthodoxa 2.4 (on angelic irrevocability); Maximus the "
        "Confessor Quaestiones ad Thalassium 1 (on Satan's non-repentance "
        "as ontological-rather-than-quantitative). The verse is THE FOUR-"
        "STEP penitential-rubric the EOTC sacrament of confession enacts: "
        "(1) sin acknowledged; (2) confessed verbally to the priest; (3) "
        "wept-over with contrition; (4) not-returned-to as effective-"
        "absolution mark.",
    ),
    meq(
        "mq3",
        10,
        1,
        WORK_MQ3,
        "CLOSING CHAPTER of 3 Meqabyan AND of the entire trilogy. Opens "
        "with the RESURRECTION-BY-ANALOGY argument: AS GOD CREATES SOULS "
        "WITHOUT PARENTS THROUGH HIS SPIRIT HOVERING OVER THE WATERS (Gen "
        "1:2), SO HE RAISES THE DEAD BY HIS WORD. The Genesis 1:2 ruach-"
        "elohim-merachefet ('Spirit of God moved upon the face of the "
        "waters') is read CHRISTOLOGICALLY-PNEUMATOLOGICALLY: the same "
        "creative-Spirit who hovers at creation-of-souls hovers at "
        "resurrection-of-bodies. The closing (vv. 24-29) is the FINAL "
        "WARNING against the Devil's lie that there is no resurrection + "
        "the call to prepare for migration 'from this earthly light to "
        "heavenly light.' The book ends (v. 29) with the doxological "
        "formula 'From today and unto eternity, Amen' (ከዛሬ ጀምሮ እስከ ዘለዓለም "
        "አሜን). This is the DECISIVE END of the full three-book trilogy "
        "and the canonical capstone of the Mäqabyan corpus.",
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 40, f"expected 40 entries, got {len(NEW_ENTRIES)}"
assert all(e["father"] == "Meqabyan (Ethiopian tradition)" for e in NEW_ENTRIES)

# Book distribution sanity (3 Mäqabyan books)
_books_covered = sorted({e["book"] for e in NEW_ENTRIES})
_expected_books = sorted({"mq1", "mq2", "mq3"})
assert _books_covered == _expected_books, f"book set mismatch: got {_books_covered}, expected {_expected_books}"

# Per-book count sanity (20 + 12 + 8 = 40)
from collections import Counter

_per_book = Counter(e["book"] for e in NEW_ENTRIES)
_expected_per_book = {"mq1": 20, "mq2": 12, "mq3": 8}
assert dict(_per_book) == _expected_per_book, (
    f"per-book count mismatch: got {dict(_per_book)}, expected {_expected_per_book}"
)


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    assert "entries" in d and "_meta" in d

    pre_count = len(d["entries"])
    d["entries"].extend(NEW_ENTRIES)
    post_count = len(d["entries"])

    ledger_addition = (
        " γ.4.8 (2026-05-14) added Mäṣḥafä Mäqabyan I-III seed wave — 40 "
        "verse-keyed entries across the three Mäqabyan books (1 Mq 20 + 2 "
        "Mq 12 + 3 Mq 8 = 40). OPENS THE SIXTH VOICE in the γ.4 patristic-"
        "and-canonical corpus — the THIRD uniquely-Tewahedo-canonical text "
        "alongside 1 Enoch / Mäṣḥafä Hēnok (γ.4.4) and Jubilees / Mäṣḥafä "
        "Kufāle (γ.4.5). γ.4.8 had been DEFERRED across the entire γ.4 "
        "corpus history pending PD source acquisition; the 2026-05-14 user-"
        "contributed CC0 1.0 English translation (archive.org/details/three-"
        "books-of-meqabyan-cc0-translation, translated from Modern Amharic "
        "of the EOTC Bible at nehemiah-osc.org by Claude with collaborator) "
        "is the canonical unblocker. Apparatus integrates Josef Horovitz "
        "'Das äthiopische Maccabäerbuch' (Zeitschrift für Assyriologie XIX, "
        "1905, pp. 194-233 — PD primary scholarly study); 64-citation third-"
        "pass audit verdict matrix (57 verified / 4 documentable-errors-"
        "corrected / 3 interpretive-readings-flagged with Horovitz caveats / "
        "7 newly-discovered-parallels-added). Distribution: 1 Mq (20: 2:5 "
        "creation-confession + 2:14 EPONYM-VERSE + 2:17 eastward-prayer "
        "Didascalia + 2:22 searches-kidneys-and-heart triple-patriarch + "
        "2:27 first-death-and-resurrection + 3:1 Abya-Sila-Fentos five-sons-"
        "of-Maqabis + 5:1 Re'aytawi crux + 6:1 heavenly-palace ekphrasis + "
        "8:1 vine-and-tree resurrection 1 Cor 15:36-38 + 10:1 patriarch-"
        "burial argument + 13:12 explicit-Lucifer-fall Isa 14:12-14 + 14:15 "
        "Moses-Joshua unfermented-wine wit + 17:1 Sebelyanos = Beliar + "
        "28:1 salvation-history compression Cain-to-Esther + 30:7 1 Sam "
        "2:30 covenant-honor-formula + 33:1 manna = bread-of-angels Ps 78:25 "
        "+ 34:1 four-kingdoms apocalypse + 36:22 Abraham-my-friend-Isaac-"
        "my-favored-Jacob-my-beloved triple-formula James 2:23 climax + "
        "36:29 Hellenistic-deity catalog Apollon-Artemis-Serapion dating-"
        "anchor pre-400 CE + 36:45 resurrection capstone double-Amen) + 2 "
        "Mq (12: 1:1 Maqabis-of-Moab parallel-inverse + 1:10 Psalm 79:2-3 "
        "lament-over-Jerusalem + 2:1 prophet Re'ay + 2:4 Deut 28 disease-"
        "catalog + 3:2 pit-self-mortification penitential + 4:15 Maqabis-"
        "conversion Gentile-king-righteousness Ruth Rabbah parallel + 6:1 "
        "second-five-sons martyrdom-and-appearance + 12:11 Ṣiruṣaydan-"
        "death narrative-climax of villain-arc + 14:1 four-sectarian-"
        "resurrection-errors + 14:19 four-elements resurrection Empedoclean-"
        "Galenic + 17:1 wheat-grain-dying 1 Cor 15:36 + Jn 12:24 + 18:7 "
        "Adamic-mortality Rom 5:12) + 3 Mq (8: 1:1 merciful-and-meek-one "
        "messianic Horovitz caveat-flagged + 1:3 Devil's hubris-speech "
        "Isa 14 + Ezk 28 + 2 Thess 2:4 + Ephrem-Carmina-Nisibena + 1:15 "
        "SATAN-REFUSED-TO-WORSHIP-ADAM Vita Adae §§12-17 + 2 Enoch + Cave "
        "of Treasures §2 + Qur'an seven-passage cluster + 2:1 Job 1-2 "
        "anti-deception + 4:5 Devil's-name-etymology Diabolos-slanderer + "
        "4:8 'tenth-tribe' angelic-hierarchy Pseudo-Dionysius + Gregory + "
        "Augustine + Anselm + 4:34 'complete repentance' EOTC sacramental-"
        "confession foundation + 10:1 closing-doxology resurrection-by-"
        "Spirit-hovering-waters Gen 1:2). Voice mix post-γ.4.8 (1407 "
        "entries): Cyril 47.48% / Jubilees 14.22% / 1 Enoch 13.65% / "
        "Ephrem 11.16% / Athanasius 10.66% / Meqabyan 2.84%. Cyril remains "
        "plurality-leader at 3.34× next-single-father (668 vs 200). "
        "Tewahedo-distinctive-canonical voices (Mäṣḥafä Hēnok + Mäṣḥafä "
        "Kufāle + Mäqabyan) hold 30.8% — for the first time the three "
        "uniquely-Tewahedo canonical texts together constitute a "
        "numerically significant block. SIX-voice composition codified in "
        "paired ω.42 hygiene bundle (CLAUDE_PROJECT_RULES §1 patristic-"
        "source-voice-composition extension to six voices + jas→jam "
        "_BOOK_CODE_ALIASES single-line fix per AUDIT_2026-05-13-DEEP D-W2 "
        "finding). ELEVENTH production-scale verification of N-W4 "
        "idempotency contract. mq1.py + mq2.py + mq3.py notes-files filled "
        "for the FIRST TIME in project history (each was 0-tuple per "
        "AUDIT_2026-05-13-DEEP D-C1 finding)."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    meq_total = sum(1 for e in d["entries"] if e["father"] == "Meqabyan (Ethiopian tradition)")
    print(f"γ.4.8 ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(f"Meqabyan total: {meq_total} entries — SIXTH PATRISTIC/CANONICAL VOICE opened")
    print(f"Books touched: {sorted({e['book'] for e in NEW_ENTRIES})}")
    print(f"Per-book counts: {dict(_per_book)}")
    print("γ.4.8 seed wave: Mäṣḥafä Mäqabyan SEED OPENED — γ.4.8 deferral cleared.")


if __name__ == "__main__":
    main()
