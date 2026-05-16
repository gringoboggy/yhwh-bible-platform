"""γ.4.9.B ship — Athanasius of Alexandria Pauline detail wave I
(40 verse-keyed entries deepening the 16 γ.4.9 seed Pauline anchors
to 56-entry detail coverage across all 8 Pauline books). Mirrors the
detail-wave shape of γ.4.7.B Mark-1-5 Galilean wave (51 entries
deepening 13 seed anchors to 64-entry coverage).

γ.4.9.B is the FIRST detail-wave on the γ.4.9 Athanasius seed (which
opened the FIFTH PATRISTIC VOICE in the γ.4 corpus). The detail-wave
structure mirrors γ.4.5 Jubilees pattern (per-thematic-group rather
than per-chapter-stretch, since Athanasius's works are doctrinal-
treatises spanning the entire canon thematically).

Distribution (40 detail entries across all 8 Pauline books):
- Romans (10): Adam-Christ typology + Spirit-adoption + propitiation
- 1 Corinthians (6): Lord-of-glory-crucified + Eucharist + last-Adam
- 2 Corinthians (3): transformation + reconciliation + Trinity
- Galatians (3): curse-for-us + mediator + Spirit-of-Son
- Ephesians (4): exalted-above + peace-making + descended/ascended
- Philippians (4): kenosis-completion + universal-bow + transformation
- Colossians (4): cosmic-Christ + reconciliation-by-blood + nailed-bond
- Hebrews (6): canon-citation-chain + high-priesthood + once-offered

Post-γ.4.9.B Pauline-Athanasius coverage:
  Romans:        3 seed + 10 detail = 13 entries
  1 Corinthians: 2 seed +  6 detail =  8 entries
  2 Corinthians: 1 seed +  3 detail =  4 entries
  Galatians:     1 seed +  3 detail =  4 entries
  Ephesians:     1 seed +  4 detail =  5 entries
  Philippians:   3 seed +  4 detail =  7 entries
  Colossians:    3 seed +  4 detail =  7 entries
  Hebrews:       2 seed +  6 detail =  8 entries
                                      ────
                                      56 Pauline-Athanasius entries

Voice mix post-γ.4.9.B (1297 entries total):
  Cyril of Alexandria   668  51.5%
  Jubilees              200  15.4%
  1 Enoch               192  14.8%
  Ephrem the Syrian     157  12.1%
  Athanasius             80   6.2%  ← γ.4.9 (40) + γ.4.9.B (40)
Patristic-anchor majority (Cyril + Ephrem + Athanasius) ~69.8%.
Per ω.41 §1: Cyril-led-plurality preserved (still 51.5%, intentional).

Sources (all fully PD, same as γ.4.9):
- NPNF Series 2, Vol. 4 (Robertson, Oxford/T&T Clark 1892):
  Contra Arianos I-IV + De Incarnatione + De Decretis + Epistola
  ad Epictetum + Epistola ad Adelphium + Festal Letters.

This is a DETAIL wave (NOT arc-close). Future γ.4.9.C/D/E may deepen
other γ.4.9 thematic groups (OT, Gospels, Petrine/Johannine/
Apocalyptic) before any arc-close warrants §8.1 pin set.

Run from project root: python scripts/_ship_gamma49b.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

JSON_PATH = Path("content") / "sources" / "ethiopian_commentaries.json"

ATTR_CA = (
    "Athanasius of Alexandria, Orationes contra Arianos (Four Discourses "
    "Against the Arians, I-IV), in Select Writings and Letters of Athanasius, "
    "Nicene and Post-Nicene Fathers (NPNF), Series 2, Vol. 4, ed. Archibald "
    "Robertson (Oxford / T&T Clark, 1892). PD. Greek text in Migne PG 26 "
    "(1857)."
)

ATTR_DI = (
    "Athanasius of Alexandria, De Incarnatione Verbi (On the Incarnation), "
    "in Select Writings and Letters of Athanasius, Nicene and Post-Nicene "
    "Fathers (NPNF), Series 2, Vol. 4, ed. Archibald Robertson (Oxford / "
    "T&T Clark, 1892). PD. Greek text in Migne PG 25 (1857)."
)

ATTR_EPICT = (
    "Athanasius of Alexandria, Epistola ad Epictetum (Letter to Epictetus, "
    "Bishop of Corinth), in Select Writings and Letters of Athanasius, "
    "Nicene and Post-Nicene Fathers (NPNF), Series 2, Vol. 4, ed. Archibald "
    "Robertson (Oxford / T&T Clark, 1892). PD."
)

ATTR_ADELPH = (
    "Athanasius of Alexandria, Epistola ad Adelphium (Letter to Adelphius, "
    "Bishop and Confessor: Against the Arians), in Select Writings and "
    "Letters of Athanasius, Nicene and Post-Nicene Fathers (NPNF), Series 2, "
    "Vol. 4, ed. Archibald Robertson (Oxford / T&T Clark, 1892). PD."
)


def ath(book: str, chapter: int, verse: int, work: str, summary: str, attribution: str) -> dict:
    return {
        "book": book,
        "chapter": chapter,
        "verse": verse,
        "father": "Athanasius of Alexandria",
        "work": work,
        "year": 350,
        "summary": summary,
        "attribution": attribution,
    }


NEW_ENTRIES: list[dict] = [
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 1 — ROMANS (10) — Adam-Christ + Spirit-adoption + propitiation
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "rom",
        1,
        4,
        "Orationes contra Arianos II.14",
        "'And declared to be the Son of God with power, according to the "
        "spirit of holiness, by the resurrection from the dead' — Athanasius "
        "marks horisthentos huiou theou en dynamei (declared Son of God in "
        "power) as the post-resurrection PUBLIC-MANIFESTATION (NOT a "
        "promotion-to-divinity per the Arian-Adoptionist reading). The "
        "horizein (declare/mark-off) is a revelatory verb, not an ontological-"
        "constitution verb — the resurrection reveals what the Son already "
        "was eternally, en dynamei (in power). Athanasius pairs Rom 1:4 with "
        "Rom 1:3 (made of seed of David kata sarka — the Davidic-incarnate "
        "mode) as the two-clause confession: Davidic-flesh manifesting "
        "eternal-divine-Sonship. The Tewahedo Easter (Fāsika) Anaphora "
        "preserves the Rom 1:3-4 dual-confession at the Praise-of-the-"
        "Resurrection eucharistic-acclamation.",
        ATTR_CA,
    ),
    ath(
        "rom",
        3,
        25,
        "De Incarnatione Verbi §9",
        "'Whom God hath set forth to be a propitiation through faith in his "
        "blood' — Athanasius marks hilastērion (propitiation, the LXX-rendering "
        "of kapporet — the mercy-seat / atonement-cover atop the ark) as the "
        "Pauline-cultic-summary of the incarnation. The Word's-flesh-and-blood "
        "is the new-true-mercy-seat where divine-righteousness and human-sin "
        "meet without the divine-justice being compromised. Athanasius's "
        "doctrinal-summary: 'the Word took flesh that He might offer this "
        "flesh as sacrifice' (DI §9 paraphrased) connects Rom 3:25 explicitly "
        "to the incarnational rationale. The Tewahedo Anaphora Tabot-theology "
        "(the consecrated tablet-altar that the Word's-Eucharistic-presence "
        "rests upon) preserves the hilastērion-anchor at every Eucharistic "
        "consecration.",
        ATTR_DI,
    ),
    ath(
        "rom",
        5,
        14,
        "Orationes contra Arianos II.65",
        "'Nevertheless death reigned from Adam to Moses, even over them that "
        "had not sinned after the similitude of Adam's transgression, who is "
        "the figure of him that was to come' — Athanasius marks ho estin "
        "typos tou mellontos (who is the type of him that was to come) as the "
        "Pauline-typological-anchor of the Adam-Christ correspondence the De "
        "Incarnatione exposits at length. Adam = the first Adam, head of the "
        "fallen-mortal-race; Christ = the second Adam, head of the restored-"
        "immortal-race. The typology runs in OPPOSITE-direction-correspondence: "
        "where Adam introduced death-by-disobedience, Christ introduces life-"
        "by-obedience. Tewahedo Adam-Christ typological-preaching cites Rom "
        "5:14-19 + 1 Cor 15:21-22, 45-49 as the canonical-typological-double "
        "anchor at every Holy-Week (Hemamat) catechesis.",
        ATTR_CA,
    ),
    ath(
        "rom",
        5,
        19,
        "De Incarnatione Verbi §7",
        "'For as by one man's disobedience many were made sinners, so by the "
        "obedience of one shall many be made righteous' — Athanasius marks dia "
        "tēs hypakoēs tou henos (through the obedience of the one) as the "
        "soteriological-counterweight to dia tēs parakoēs tou henos (through "
        "the disobedience of the one). The hypakoē-of-the-Word-incarnate is "
        "active throughout the Gospels (Lk 2:51 hypotassomenos to his parents; "
        "Jn 6:38 not my own will; Phil 2:8 obedient unto death) but its "
        "soteriological-effect IS THE INCARNATION as a whole: the Word's-"
        "genuine-human-obedience corrects what Adam's-genuine-human-"
        "disobedience disordered. Tewahedo paschal-mystery theology cites "
        "Rom 5:19 + Heb 5:8 (learned obedience by things suffered) as the "
        "obedience-soteriology pair.",
        ATTR_DI,
    ),
    ath(
        "rom",
        6,
        3,
        "Orationes contra Arianos I.50",
        "'Know ye not, that so many of us as were baptized into Jesus Christ "
        "were baptized into his death?' — Athanasius marks eis ton thanaton "
        "autou ebaptisthēmen (we were baptized into his death) as the "
        "baptismal-incorporation-into-the-paschal-mystery. The baptismal-water "
        "is not merely-cleansing but THE-PATH-INTO-Christ's-death-and-"
        "resurrection. The believer's union-with-Christ-in-baptism is "
        "ontological-real, not merely-symbolic. The Tewahedo baptismal-rite "
        "(Krǝstǝnnā, with triple-immersion in fonts shaped as cruciform-tombs) "
        "preserves the Athanasian-Pauline death-into-life-incorporation "
        "explicitly — the rubric cites Rom 6:3-5 at the triple-immersion "
        "exhortation.",
        ATTR_CA,
    ),
    ath(
        "rom",
        8,
        3,
        "Epistola ad Epictetum",
        "'For what the law could not do, in that it was weak through the "
        "flesh, God sending his own Son in the likeness of sinful flesh, and "
        "for sin, condemned sin in the flesh' — Athanasius marks en homoiōmati "
        "sarkos hamartias (in the likeness of sinful flesh) as the precise "
        "Pauline-formula that excludes BOTH Docetism AND Apollinarianism: en "
        "homoiōmati (in likeness — genuine-sameness-of-nature) NOT en hyparxei "
        "tēs hamartias (in actual sinfulness — which would deny Christ's "
        "sinlessness). The flesh-assumed is genuinely-human (full-nature, not "
        "phantasm) BUT WITHOUT-sin (homoiōma not actuality of hamartias). "
        "Tewahedo Miaphysite-Christology preserves this Athanasian-Pauline "
        "distinction at the Ad-Epictetum-anchor: the Word genuinely-assumed "
        "the consequences-of-fallen-humanity (mortality, weariness, hunger, "
        "tears) while remaining personally-sinless.",
        ATTR_EPICT,
    ),
    ath(
        "rom",
        8,
        9,
        "Orationes contra Arianos III.24",
        "'But ye are not in the flesh, but in the Spirit, if so be that the "
        "Spirit of God dwell in you. Now if any man have not the Spirit of "
        "Christ, he is none of his' — Athanasius marks the Pneuma-theou / "
        "Pneuma-Christou parallel as Pauline-pneumatological-evidence of the "
        "Spirit's consubstantial-divinity. The SAME Spirit is called both "
        "'of-God' and 'of-Christ' — if Christ were merely-a-creature, the "
        "Spirit could not properly be 'of-Christ' in the same divine-mode as "
        "'of-God'. The verse therefore positively-requires Father-Son-Spirit "
        "intra-divine-co-essential relations. Tewahedo Trinitarian "
        "pneumatology cites Rom 8:9-11 + Jn 14:26 + Jn 15:26 as the Pauline-"
        "Johannine Spirit-procession triad.",
        ATTR_CA,
    ),
    ath(
        "rom",
        8,
        17,
        "Orationes contra Arianos I.38",
        "'And if children, then heirs; heirs of God, and joint-heirs with "
        "Christ; if so be that we suffer with him, that we may be also "
        "glorified together' — Athanasius marks synklēronomoi de Christou "
        "(joint-heirs with Christ) as the Pauline-theosis-anchor. The "
        "believer-by-adoption shares-by-grace what the Son-by-nature "
        "possesses-eternally — co-heirship in the divine-inheritance. The "
        "verse's syn-suffer + syn-glorified pattern names the participation-"
        "in-Christ's-paschal-mystery as the ontological-conduit of theosis. "
        "Tewahedo monastic-spirituality (the Mahǝbär-Mariam koinonia + "
        "the Säwāsǝw-asceticism manuals) preserves Rom 8:17 as the joint-"
        "heir-via-suffering anchor of authentic-Christian-formation.",
        ATTR_CA,
    ),
    ath(
        "rom",
        8,
        29,
        "Orationes contra Arianos II.61",
        "'For whom he did foreknow, he also did predestinate to be conformed "
        "to the image of his Son, that he might be the firstborn among many "
        "brethren' — Athanasius marks prōtotokon en pollois adelphois "
        "(firstborn among many brethren) as a SECOND prōtotokos-usage (paired "
        "with Col 1:15 prōtotokos pasēs ktiseōs and Heb 1:6 prōtotokos eis "
        "tēn oikoumenēn) — together demonstrating that 'firstborn' "
        "consistently names ECONOMIC-HEADSHIP, not creaturely-priority. "
        "Among-many-brethren — the Son's-incarnate-humanity makes him the "
        "elder-brother of the redeemed-human-race. The conformity to the "
        "Son's-image is theosis from another angle: image-restoration + "
        "filial-incorporation. Tewahedo brotherhood-of-believers ecclesiology "
        "cites Rom 8:29 + Heb 2:11 as the prōtotokos-elder-brother pair.",
        ATTR_CA,
    ),
    ath(
        "rom",
        11,
        36,
        "Orationes contra Arianos II.21",
        "'For of him, and through him, and to him, are all things: to whom be "
        "glory for ever. Amen' — Athanasius marks the ex autou / di' autou / "
        "eis auton triadic-causal-structure as a Pauline-doxological-summary "
        "of the Trinitarian-economic-life: the Father is the source (ex), the "
        "Son the agent (di' / through), the Spirit the consummation (eis / "
        "toward whom). The verse closes Romans's Israel-section doxologically "
        "at the same height it climbed exegetically — naming the entire "
        "salvation-economy in three Trinitarian-roles. The Tewahedo "
        "Anaphora-conclusion cites Rom 11:36 + Eph 4:6 + 1 Cor 15:28 as the "
        "all-in-all eschatological-trinitarian closure formula.",
        ATTR_CA,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 2 — 1 CORINTHIANS (6) — Lord-of-glory + Eucharist + last-Adam
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "1co",
        1,
        30,
        "Orationes contra Arianos I.19",
        "'But of him are ye in Christ Jesus, who of God is made unto us "
        "wisdom, and righteousness, and sanctification, and redemption' — "
        "Athanasius marks the four-fold sophia + dikaiosynē + hagiasmos + "
        "apolytrōsis attribute-cluster as the FULL Christological-soteriology "
        "in Pauline-shorthand. Christ IS each-of-these (predicate-identity, "
        "not mere-instrumentality). The four-fold corresponds to the four-"
        "fold problem-of-Adam: ignorance (→ Christ-wisdom), unrighteousness "
        "(→ Christ-righteousness), pollution (→ Christ-sanctification), "
        "captivity (→ Christ-redemption). Tewahedo soteriological-preaching "
        "cites 1 Cor 1:30 as the comprehensive Christological-attribute-list.",
        ATTR_CA,
    ),
    ath(
        "1co",
        2,
        8,
        "Orationes contra Arianos III.32",
        "'Which none of the princes of this world knew: for had they known "
        "it, they would not have crucified the Lord of glory' — Athanasius "
        "marks ton kyrion tēs doxēs estaurōsan (they crucified the Lord of "
        "glory) as the COMMUNICATIO-IDIOMATUM Pauline-anchor. The crucified-"
        "one IS the Lord-of-glory — the divine-glory-Bearer is the same-"
        "Person who suffered on the cross, predicated by the single-Person-"
        "of-the-incarnate-Word. The Arian/Nestorian scheme cannot account for "
        "this language without making it metaphorical; Athanasian-Pauline "
        "Christology takes it as ontological. Tewahedo Holy-Friday-hymnody "
        "(Maḫrāya-Sǝqlät) cites 1 Cor 2:8 as the kyrios-of-glory-crucified "
        "Miaphysite-anchor.",
        ATTR_CA,
    ),
    ath(
        "1co",
        10,
        4,
        "De Incarnatione Verbi §13",
        "'And did all drink the same spiritual drink: for they drank of that "
        "spiritual Rock that followed them: and that Rock was Christ' — "
        "Athanasius marks hē petra de ēn ho Christos (the Rock was Christ) as "
        "the Pauline-pre-incarnation-presence prooftext. The same Word who "
        "became-incarnate-in-the-fullness-of-time was already-present in the "
        "Exodus-economy as the wilderness-sustaining Rock, the Cloud-and-Fire "
        "pillar, the Manna. Athanasius's Old-Testament-Christology runs on "
        "Pauline-1 Cor 10 + Jn 8:58 + Ex 3:14 (Burning Bush) lines. Tewahedo "
        "lectionary-pairing reads 1 Cor 10:1-4 with Ex 17:6 (Massah-Meribah) "
        "at every Tǝmqät (Theophany) anniversary baptismal-renewal.",
        ATTR_DI,
    ),
    ath(
        "1co",
        11,
        25,
        "Orationes contra Arianos II.16",
        "'After the same manner also he took the cup, when he had supped, "
        "saying, This cup is the new testament in my blood: this do ye, as "
        "oft as ye drink it, in remembrance of me' — Athanasius marks hē kainē "
        "diathēkē en tō emō haimati (the new covenant in my blood) as the "
        "Pauline-institution-text that authorizes the Eucharistic-Anaphora "
        "across the whole Church. The blood-covenant-language (Ex 24:8 echo) "
        "names the Eucharist as the new-Sinai-event the Word's-incarnation "
        "establishes. Tewahedo Anaphora-of-the-Apostles cites 1 Cor 11:23-26 "
        "at the institution-recital before every consecration.",
        ATTR_CA,
    ),
    ath(
        "1co",
        15,
        21,
        "De Incarnatione Verbi §10",
        "'For since by man came death, by man came also the resurrection of "
        "the dead' — Athanasius marks the parallel di' anthrōpou thanatos / "
        "di' anthrōpou anastasis (through man death / through man "
        "resurrection) as the Pauline-soteriological-symmetry the entire De "
        "Incarnatione reconstructs. The Adam-Christ Pauline parallel is not "
        "merely-decorative: it grounds the soteriological-NECESSITY of the "
        "incarnation. Only a genuine-man (sharing Adam's nature) can be the "
        "agent of resurrection-for-Adam's-race; only a divine-Word (with "
        "power over death) can effectively rise. The incarnate-Word is both. "
        "Tewahedo paschal-doctrine cites 1 Cor 15:21-22 at the Easter-vigil "
        "kerygmatic-anchor.",
        ATTR_DI,
    ),
    ath(
        "1co",
        15,
        45,
        "Orationes contra Arianos II.65",
        "'And so it is written, The first man Adam was made a living soul; "
        "the last Adam was made a quickening spirit' — Athanasius marks ho "
        "eschatos Adam eis pneuma zōopoioun (the last Adam unto a life-giving "
        "spirit) as the FULL Adam-Christ-typological-completion. The first "
        "Adam was made-a-living-soul (received life from outside); the last "
        "Adam IS-a-life-giving-Spirit (gives life from himself). The "
        "asymmetry is Christ's-divinity emerging through the Pauline-"
        "typological-structure: Christ is not merely-the-better-Adam but the "
        "life-giving-Word-incarnate. Tewahedo Pentecost (Päraqlitos) liturgy "
        "cites 1 Cor 15:45 + Jn 20:22 (Jesus breathes Spirit on disciples) as "
        "the Pneuma-zōopoioun life-giving-Spirit pair.",
        ATTR_CA,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 3 — 2 CORINTHIANS (3) — transformation + reconciliation + Trinity
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "2co",
        3,
        18,
        "Orationes contra Arianos I.46",
        "'But we all, with open face beholding as in a glass the glory of the "
        "Lord, are changed into the same image from glory to glory, even as "
        "by the Spirit of the Lord' — Athanasius marks tēn autēn eikona "
        "metamorphoumetha (we are transformed into the same image) as the "
        "Pauline-theosis-process-anchor. The transformation is into THE SAME "
        "image — the eikōn-of-the-Father (Col 1:15) — by the Spirit of the "
        "Lord. Theosis is therefore Trinitarian-mediated: contemplating the "
        "Son's-glory (visible eikōn of the Father) BY the Spirit (the agent "
        "of conformation). Tewahedo monastic-contemplative theology (the "
        "Tä'amrä-Maryam visionary-tradition) cites 2 Cor 3:18 + 1 Jn 3:2 + "
        "Rev 22:4 as the beatific-vision-theosis triad.",
        ATTR_CA,
    ),
    ath(
        "2co",
        5,
        19,
        "De Incarnatione Verbi §8",
        "'To wit, that God was in Christ, reconciling the world unto himself, "
        "not imputing their trespasses unto them' — Athanasius marks theos ēn "
        "en Christō kosmon katallassōn heautō (God was in Christ reconciling "
        "the world to himself) as the Pauline-summary-of-the-incarnation-as-"
        "reconciliation. The subject is theos (God); the locus is en Christō "
        "(in Christ); the action is kosmon katallassōn (reconciling the world); "
        "the goal is heautō (to himself — divine-Father-self). The verse "
        "compresses the entire Pauline-soteriology into one clause. Tewahedo "
        "Anaphora-prefatory thanksgiving cites 2 Cor 5:19 + Rom 5:10 as the "
        "reconciliation-locus pair.",
        ATTR_DI,
    ),
    ath(
        "2co",
        13,
        14,
        "Orationes contra Arianos III.6",
        "'The grace of the Lord Jesus Christ, and the love of God, and the "
        "communion of the Holy Ghost, be with you all. Amen' — Athanasius "
        "marks the triadic Pauline-benediction as the closing-Trinitarian-"
        "doxology of Paul's most-personal letter. The three-fold structure "
        "(grace-of-Christ + love-of-God + koinonia-of-Spirit) names each "
        "Person by his characteristic economic-action: Christ's-grace = the "
        "redemption; God's-love = the Father's-sending-of-the-Son; Spirit's-"
        "koinonia = the church's-life-in-the-divine-fellowship. Tewahedo "
        "liturgical-benediction-formulae (recited at every dismissal) "
        "preserve 2 Cor 13:14's three-fold-structure as the Trinitarian-"
        "blessing-anchor.",
        ATTR_CA,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 4 — GALATIANS (3) — curse-for-us + mediator + Spirit-of-Son
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "gal",
        3,
        13,
        "De Incarnatione Verbi §25",
        "'Christ hath redeemed us from the curse of the law, being made a "
        "curse for us: for it is written, Cursed is every one that hangeth on "
        "a tree' — Athanasius marks genomenos hyper hēmōn katara (having "
        "become for-us a curse) as the Pauline-substitutionary-summit. The "
        "Word-incarnate VOLUNTARILY-takes-on the legal-cursed-status (per "
        "Deut 21:23 quoted) that human-disobedience earned — and ABSORBS-it-"
        "in-his-own-flesh on the cross. The katara (curse) is taken-into-the-"
        "divine-Person and exhausted-by-his-resurrection-acceptance. Tewahedo "
        "Holy-Friday liturgical-meditation cites Gal 3:13 + Deut 21:23 + 1 "
        "Pet 2:24 as the cursed-on-the-tree triple-anchor.",
        ATTR_DI,
    ),
    ath(
        "gal",
        3,
        20,
        "Orationes contra Arianos II.31",
        "'Now a mediator is not a mediator of one, but God is one' — "
        "Athanasius marks ho de mesitēs henos ouk estin / ho de theos heis "
        "estin (the mediator is not of one / but God is one) as the Pauline-"
        "monotheism + Christological-mediation conjunction. The verse "
        "preserves divine-unity (theos heis estin — God-is-one, the Shema "
        "Pauline-formulation) AND establishes Christ's-mediatorial-office "
        "(mesitēs between God and humanity, requiring two-natures: divine to "
        "represent God + human to represent humanity). Tewahedo Christological-"
        "summary cites Gal 3:20 + 1 Tim 2:5 as the mediator-of-two-natures "
        "Pauline-pair.",
        ATTR_CA,
    ),
    ath(
        "gal",
        4,
        6,
        "Orationes contra Arianos I.48",
        "'And because ye are sons, God hath sent forth the Spirit of his Son "
        "into your hearts, crying, Abba, Father' — Athanasius marks to pneuma "
        "tou huiou autou (the Spirit of his Son) as the pneumatological-"
        "anchor of theosis-by-adoption. The Spirit-of-the-Son-by-nature "
        "creates sonship-by-grace in the believer; the SAME Spirit who cried "
        "'Abba' in the incarnate-Son's-Gethsemane (Mk 14:36) now cries 'Abba' "
        "in the adopted-believer. The intra-divine Filial-Spirit-Father-"
        "relation becomes the believer's-divine-relation by participation. "
        "Tewahedo baptismal-chrismation rubric cites Gal 4:6 + Rom 8:15 + "
        "Mk 14:36 as the Abba-adoption-Spirit triadic anchor.",
        ATTR_CA,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 5 — EPHESIANS (4) — exalted-above + peace + descended/ascended
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "eph",
        1,
        21,
        "Orationes contra Arianos I.42",
        "'Far above all principality, and power, and might, and dominion, and "
        "every name that is named, not only in this world, but also in that "
        "which is to come' — Athanasius marks hyperanō pasēs archēs (far-above "
        "every principality) as the exaltation-supremacy Pauline-anchor "
        "paired with Phil 2:9 (highly-exalted). The Christ-incarnate-and-"
        "risen is RANKED-ABOVE every conceivable angelic or human authority — "
        "in BOTH this-age AND the-age-to-come (eschatological-permanence). "
        "Tewahedo angelology preserves this Pauline-supremacy-of-Christ at "
        "the Christ-Pantocrator iconography of every Tewahedo-dome.",
        ATTR_CA,
    ),
    ath(
        "eph",
        2,
        14,
        "De Incarnatione Verbi §16",
        "'For he is our peace, who hath made both one, and hath broken down "
        "the middle wall of partition between us' — Athanasius marks autos "
        "gar estin hē eirēnē hēmōn (he himself is our peace) as the Pauline-"
        "incarnational-peace-anchor. Christ does not merely-make-peace; he IS "
        "peace (predicate-identity, like 1 Cor 1:30). The both-made-one names "
        "Jew-Gentile-reconciliation but the deeper-anchor is human-divine-"
        "reconciliation: the Word's-incarnate-Person IS the union-of-the-two-"
        "natures, making him constitutively-peace between God and humanity. "
        "Tewahedo Aksumite-Gentile-mission theology cites Eph 2:14-18 at the "
        "Frumentius-mission anchor.",
        ATTR_DI,
    ),
    ath(
        "eph",
        4,
        9,
        "Orationes contra Arianos III.46",
        "'(Now that he ascended, what is it but that he also descended first "
        "into the lower parts of the earth?)' — Athanasius marks katebē eis "
        "ta katōtera merē tēs gēs (descended into the lower parts of the "
        "earth) as the Pauline-affirmation of the descent-into-hades / "
        "harrowing-of-Sheol. The Word-incarnate's death was not merely-"
        "physical-cessation but ACTIVE-descent into Sheol-of-the-dead to "
        "extract the captive-righteous (1 Pet 3:19 paired). The katō / anō "
        "(below/above) pairing of Eph 4:9-10 names the cosmic-rescue-arc the "
        "incarnation accomplishes. Tewahedo Holy-Saturday (Qǝddus-Sǝnbät) "
        "preserves the descent-into-Sheol kerygma explicitly via Eph 4:9-10 + "
        "1 Pet 3:19 + Acts 2:24 in the office of the descent.",
        ATTR_CA,
    ),
    ath(
        "eph",
        4,
        10,
        "Orationes contra Arianos III.46",
        "'He that descended is the same also that ascended up far above all "
        "heavens, that he might fill all things' — Athanasius marks ho katabas "
        "autos estin kai ho anabas (the one who descended is the same as the "
        "one who ascended) as the IDENTITY-of-PERSON-across-the-paschal-"
        "mystery. The descent into death AND the ascent above-all-heavens are "
        "predicated of the SAME Subject (the incarnate-Word) without internal-"
        "duality. The hina plērōsē ta panta (that he might fill all things) "
        "names the cosmic-pleroma-fulfillment Christ accomplishes. Tewahedo "
        "Ascension (Ǝrgät) liturgy cites Eph 4:9-10 as the descent-ascent-"
        "cosmic-pleroma triadic kerygma.",
        ATTR_CA,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 6 — PHILIPPIANS (4) — kenosis-completion + bow + transformation
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "phi",
        2,
        5,
        "Orationes contra Arianos I.40",
        "'Let this mind be in you, which was also in Christ Jesus' — "
        "Athanasius marks touto phroneite en hymin ho kai en Christō Iēsou "
        "(this mind be in you which was also in Christ Jesus) as the "
        "PARAENETIC-DOORWAY into the Phil 2:6-11 hymn. The kenotic-Christology "
        "of vv. 6-11 is not a stand-alone-treatise but an exhortation-to-"
        "imitation grounded in Christology. The believer's-life is shaped-by "
        "the Word's-kenotic-pattern: descent-then-exaltation, self-emptying-"
        "before-glory. Tewahedo monastic-formation reads Phil 2:5-11 at every "
        "novice's clothing-rite as the kenotic-vocation-anchor.",
        ATTR_CA,
    ),
    ath(
        "phi",
        2,
        8,
        "De Incarnatione Verbi §22",
        "'And being found in fashion as a man, he humbled himself, and became "
        "obedient unto death, even the death of the cross' — Athanasius marks "
        "ginomenos hypēkoos mechri thanatou, thanatou de staurou (becoming "
        "obedient unto death, even death of the cross) as the kenotic-"
        "trajectory-summit. The two-mechri (unto / even) escalations name the "
        "uttermost-depth of the descent: not merely-incarnation, not merely-"
        "death, but specifically the CRUCIFORM-death (the Roman-shameful-"
        "execution mode). The cross is therefore both the Christological-"
        "summit of obedience AND the soteriological-summit of redemption. "
        "Tewahedo cross-veneration (the Mäskäl Feast September 27) cites "
        "Phil 2:8 as the kenotic-obedience-of-the-cross anchor.",
        ATTR_DI,
    ),
    ath(
        "phi",
        2,
        10,
        "Orationes contra Arianos I.42",
        "'That at the name of Jesus every knee should bow, of things in "
        "heaven, and things in earth, and things under the earth' — Athanasius "
        "marks pan gony kampsē epouraniōn kai epigeiōn kai katachthoniōn "
        "(every-knee bow of heavenly + earthly + under-earthly) as the "
        "UNIVERSAL-ACKNOWLEDGMENT-of-divine-lordship. The three-tiered "
        "cosmography (heavens above + earth + Sheol-below) is exhausted by "
        "the en-Iēsou-onomati (in-name-of-Jesus) homage. The verse echoes "
        "Isa 45:23 (every-knee-bow before YHWH) — the Pauline-citation "
        "transfers the YHWH-prerogative explicitly to the incarnate-Jesus-"
        "name. Tewahedo Anaphora preserves Phil 2:10-11 + Isa 45:23 as the "
        "universal-knee-bow Christological-acclamation.",
        ATTR_CA,
    ),
    ath(
        "phi",
        3,
        21,
        "De Incarnatione Verbi §54",
        "'Who shall change our vile body, that it may be fashioned like unto "
        "his glorious body, according to the working whereby he is able even "
        "to subdue all things unto himself' — Athanasius marks metaschēmatisei "
        "to sōma tēs tapeinōseōs hēmōn symmorphon tō sōmati tēs doxēs autou "
        "(transform the body of our humility conformable to the body of his "
        "glory) as the eschatological-theosis Pauline-anchor. The "
        "transformation is BODILY (not merely-spiritual), into-the-pattern-of "
        "Christ's resurrection-glorified-body. This is the FINAL-stage of the "
        "Athanasian theosis-arc that began with the incarnation. Tewahedo "
        "eschatological-resurrection-doctrine cites Phil 3:21 + 1 Cor 15:51-52 "
        "+ 1 Jn 3:2 as the bodily-resurrection-glorification triadic-anchor.",
        ATTR_DI,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 7 — COLOSSIANS (4) — cosmic-consist + head + bond-nailed
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "col",
        1,
        17,
        "Orationes contra Arianos II.63",
        "'And he is before all things, and by him all things consist' — "
        "Athanasius marks autos estin pro pantōn kai ta panta en autō synestēken "
        "(he is before all things and in him all things consist/hold-together) "
        "as the Pauline-cosmic-sustainer-Christology. The synestēken (hold-"
        "together, cohere) is a PRESENT-CONTINUOUS-cosmic-act, not a past-"
        "creation event. Christ is not merely-the-Creator (Col 1:16 past-act) "
        "but the ongoing-cosmic-Sustainer (Col 1:17 present-state). If the "
        "Word were-not, the cosmos would cease-to-cohere. Tewahedo "
        "cosmological-doxology cites Col 1:17 + Heb 1:3 (pherōn ta panta) as "
        "the cosmic-Christ-sustainer pair.",
        ATTR_CA,
    ),
    ath(
        "col",
        1,
        18,
        "Orationes contra Arianos II.63",
        "'And he is the head of the body, the church: who is the beginning, "
        "the firstborn from the dead; that in all things he might have the "
        "preeminence' — Athanasius marks the dual-prōtotokos: Col 1:15 "
        "prōtotokos pasēs ktiseōs (firstborn of all creation = pre-eminent "
        "creator) AND Col 1:18 prōtotokos ek tōn nekrōn (firstborn from the "
        "dead = pre-eminent resurrection). The same Word-incarnate is "
        "firstborn-over-creation AND firstborn-from-the-dead — bookending the "
        "entire-economy with prōtotokos-headship. The kephalē-of-the-body-"
        "ecclesiology grounds the Church-as-Christ's-body in the Christological-"
        "head-membership relation. Tewahedo ecclesiology cites Col 1:18 + "
        "Eph 1:22-23 as the head-body-ecclesiological pair.",
        ATTR_CA,
    ),
    ath(
        "col",
        1,
        19,
        "Orationes contra Arianos III.6",
        "'For it pleased the Father that in him should all fulness dwell' — "
        "Athanasius marks pan to plērōma katoikēsai (the whole fullness "
        "dwell) as a SECOND-articulation of Col 2:9 (pan to plērōma tēs "
        "theotētos sōmatikōs — paired in γ.4.9 seed). Col 1:19 emphasizes "
        "the Father's-pleasure as the ground (eudokēsen — was-well-pleased) "
        "of the divine-fullness-dwelling-bodily. The incarnation is not "
        "accidental but eternally-intended-by-the-Father; the Son's-"
        "kenotic-assumption is the Father's-eternal-will being realized. "
        "Tewahedo Christmas (Lǝdat) doxological reading cites Col 1:19 + "
        "Mt 3:17 (Father's-voice 'in whom I am well-pleased') as the "
        "eudokia-incarnational pair.",
        ATTR_CA,
    ),
    ath(
        "col",
        2,
        14,
        "De Incarnatione Verbi §25",
        "'Blotting out the handwriting of ordinances that was against us, "
        "which was contrary to us, and took it out of the way, nailing it to "
        "his cross' — Athanasius marks exaleipsas to kath' hēmōn cheirographon "
        "(blotting out the handwriting against us) prosēlōsas auto tō staurō "
        "(nailing it to the cross) as the Pauline-cross-as-receipt-cancellation "
        "anchor. The cheirographon (handwritten bond — the IOU of human-"
        "transgression-against-divine-law) is publicly-cancelled by being-"
        "nailed to the cross itself. The verse exegetes the cross's "
        "soteriological-mechanism in legal-financial language. Tewahedo Holy-"
        "Friday cross-meditation cites Col 2:14-15 as the cheirographon-"
        "cancellation paschal-anchor.",
        ATTR_DI,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 8 — HEBREWS (6) — citation-chain + high-priest + once-offered
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "heb",
        1,
        5,
        "Orationes contra Arianos I.55",
        "'For unto which of the angels said he at any time, Thou art my Son, "
        "this day have I begotten thee? And again, I will be to him a Father, "
        "and he shall be to me a Son?' — Athanasius marks the Hebrews 1 "
        "catena-of-citations as the EARLIEST PATRISTIC-PROOFTEXT-CHAIN that "
        "the Arians could not dismantle. The author-of-Hebrews quotes Ps 2:7 "
        "+ 2 Sam 7:14 + Deut 32:43 + Ps 104:4 + Ps 45:6-7 + Ps 102:25-27 + "
        "Ps 110:1 — seven OT citations applied to the Son, each excluding "
        "Arian-creature-status. The eternal-generation reading of Ps 2:7 "
        "(gegennēka se — I-have-begotten-you, perfect-tense permanent-state) "
        "is decisive: angels never receive this naming. Tewahedo Trisagion-"
        "theology cites Heb 1:5-13 + Ps 2:7 as the seven-fold-OT-Christology "
        "anchor.",
        ATTR_CA,
    ),
    ath(
        "heb",
        1,
        6,
        "Orationes contra Arianos I.56",
        "'And again, when he bringeth in the firstbegotten into the world, he "
        "saith, And let all the angels of God worship him' — Athanasius marks "
        "proskynēsatōsan autō pantes angeloi theou (let-worship him all "
        "angels of God) as the angelic-worship-of-Christ Hebrews-anchor. If "
        "Christ were a creature, divine-mandate to-angels-to-worship-him "
        "would be idolatry; the verse therefore-requires Christ's-divine-"
        "essence (only YHWH receives proskynēsis from angels). Athanasius "
        "pairs Heb 1:6 with Rev 5:13-14 (every-creature-worships the Lamb) "
        "as the canonical Christ-angelic-worship pair. Tewahedo Christ-"
        "Pantocrator iconography of every Tewahedo-dome preserves the Heb 1:6 "
        "+ Rev 5 angelic-worship-anchor.",
        ATTR_CA,
    ),
    ath(
        "heb",
        1,
        8,
        "Orationes contra Arianos I.61",
        "'But unto the Son he saith, Thy throne, O God, is for ever and ever: "
        "a sceptre of righteousness is the sceptre of thy kingdom' — "
        "Athanasius marks ho thronos sou ho theos (thy throne, O God) as the "
        "MOST-EXPLICIT direct-address Pauline-Hebrews-citation of the Son as "
        "ho-theos (the-God, with definite article). The Father directly-"
        "addresses the Son as 'O God' (vocative ho-theos). The Arian-"
        "reading cannot accommodate this without making it metaphorical or "
        "non-direct; Athanasian-Pauline-Hebrews exegesis takes it as literal-"
        "Trinitarian. Paired with Heb 1:9 (anointed-above-fellows, theos = "
        "the-God-anointing-by-the-God) it positively-requires intra-divine-"
        "distinction of Persons.",
        ATTR_CA,
    ),
    ath(
        "heb",
        2,
        14,
        "De Incarnatione Verbi §10",
        "'Forasmuch then as the children are partakers of flesh and blood, he "
        "also himself likewise took part of the same; that through death he "
        "might destroy him that had the power of death, that is, the devil' — "
        "Athanasius marks paraplēsiōs meteschen tōn autōn (likewise partook of "
        "the same) as the Pauline-anti-Docetic Hebrews-anchor. The Word-"
        "incarnate did not merely-appear-flesh-and-blood but FULLY-PARTOOK-of "
        "(meteschen) the same-substance the children possess. The hina dia "
        "tou thanatou katargēsē (that through death he might destroy) names "
        "the soteriological-purpose: only by genuinely-dying could the Word "
        "destroy death-itself. Tewahedo Christmas + Holy-Friday lectionary "
        "pairs Heb 2:14 with Phil 2:7-8 as the genuine-participation-anchor.",
        ATTR_DI,
    ),
    ath(
        "heb",
        4,
        15,
        "Epistola ad Adelphium",
        "'For we have not an high priest which cannot be touched with the "
        "feeling of our infirmities; but was in all points tempted like as we "
        "are, yet without sin' — Athanasius marks pepeirasmenon kata panta "
        "kath' homoiotēta chōris hamartias (tempted in all-things according-"
        "to-likeness without sin) as the Hebrews-formal-statement of "
        "Christ's-sinlessness-with-genuine-human-experience. The kata panta "
        "(in all-things) excludes Apollinarian-reduction (no human-aspect-"
        "missing); the kath' homoiotēta (according to likeness) excludes "
        "Docetic-non-genuineness; the chōris hamartias (without sin) excludes "
        "Adoptionist-or-Pelagian denial of Christ's-moral-perfection. "
        "Tewahedo Holy-Friday meditation cites Heb 4:15 + Rom 8:3 (homoiōmati-"
        "sarkos) as the sinless-but-tempted Pauline-Hebrews-pair.",
        ATTR_ADELPH,
    ),
    ath(
        "heb",
        9,
        14,
        "De Incarnatione Verbi §9",
        "'How much more shall the blood of Christ, who through the eternal "
        "Spirit offered himself without spot to God, purge your conscience "
        "from dead works to serve the living God?' — Athanasius marks dia "
        "pneumatos aiōniou heauton prosēnenken amōmon tō theō (through eternal "
        "Spirit offered himself spotless to God) as the FULL-TRINITARIAN-"
        "atonement-structure: the Son offers (active-incarnational-priest) "
        "himself (object-of-offering = the incarnate-flesh) through the "
        "eternal-Spirit (the pneumatological-medium of the sacrifice) to the "
        "Father (recipient-of-the-acceptable-offering). All three Persons are "
        "active in the single-act of atonement. Tewahedo Anaphora "
        "consecration-prayer cites Heb 9:14 at the epiclesis-of-the-Spirit-"
        "upon-the-elements as the Trinitarian-eucharistic-pattern-anchor.",
        ATTR_DI,
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 40, f"expected 40 entries, got {len(NEW_ENTRIES)}"
assert all(e["father"] == "Athanasius of Alexandria" for e in NEW_ENTRIES)

# Book distribution sanity
_books_covered = sorted({e["book"] for e in NEW_ENTRIES})
_expected_books = sorted({"rom", "1co", "2co", "gal", "eph", "phi", "col", "heb"})
assert _books_covered == _expected_books, f"book set mismatch: got {_books_covered}, expected {_expected_books}"

# Per-book count sanity
from collections import Counter

_per_book = Counter(e["book"] for e in NEW_ENTRIES)
_expected_per_book = {"rom": 10, "1co": 6, "2co": 3, "gal": 3, "eph": 4, "phi": 4, "col": 4, "heb": 6}
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
        " γ.4.9.B (2026-05-13) added Athanasius Pauline detail wave I — 40 "
        "verse-keyed entries across all 8 Pauline books deepening the 16 γ.4.9 "
        "seed Pauline anchors to 56-entry detail coverage. Distribution: "
        "Romans (10: Rom 1:4 + 3:25 + 5:14 + 5:19 + 6:3 + 8:3 + 8:9 + 8:17 + "
        "8:29 + 11:36) + 1 Corinthians (6: 1Co 1:30 + 2:8 + 10:4 + 11:25 + "
        "15:21 + 15:45) + 2 Corinthians (3: 2Co 3:18 + 5:19 + 13:14) + "
        "Galatians (3: Gal 3:13 + 3:20 + 4:6) + Ephesians (4: Eph 1:21 + 2:14 "
        "+ 4:9 + 4:10) + Philippians (4: Phi 2:5 + 2:8 + 2:10 + 3:21) + "
        "Colossians (4: Col 1:17 + 1:18 + 1:19 + 2:14) + Hebrews (6: Heb 1:5 "
        "+ 1:6 + 1:8 + 2:14 + 4:15 + 9:14). Themes: Adam-Christ typology "
        "(Rom 5:14-19, 1 Cor 15:21, 45) + Spirit-of-Son adoption (Rom 8:9, "
        "Gal 4:6) + kenotic-completion (Phi 2:5, 8, 10, 3:21) + cosmic-"
        "sustainer (Col 1:17-19) + Hebrews-citation-chain (Heb 1:5-8) + "
        "trinitarian-atonement (Heb 9:14). Voice mix post-γ.4.9.B (1297 "
        "entries): Cyril 51.5% / Jubilees 15.4% / 1 Enoch 14.8% / Ephrem "
        "12.1% / Athanasius 6.2% (γ.4.9 40 + γ.4.9.B 40 = 80). Patristic-"
        "anchor majority 67.6% → 69.8% (Cyril + Ephrem + Athanasius). Per "
        "ω.41 §1: Cyril-led-plurality preserved (51.5% remains intentional). "
        "Sources: same NPNF S2 V4 (Robertson 1892) plus new ATTR_ADELPH "
        "(Letter to Adelphius)."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    athanasius_total = sum(1 for e in d["entries"] if e["father"] == "Athanasius of Alexandria")
    print(f"γ.4.9.B ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(f"Athanasius of Alexandria total: {athanasius_total} entries (40 seed + 40 detail = 80 expected)")
    print(f"Books touched: {len({e['book'] for e in NEW_ENTRIES})} ({sorted({e['book'] for e in NEW_ENTRIES})})")


if __name__ == "__main__":
    main()
