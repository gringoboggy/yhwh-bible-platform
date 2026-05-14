"""γ.4.7.D ship — Cyril of Alexandria on Mark ARC-CLOSE wave
(Mark 11-16: Jerusalem entry + temple cleansing + Olivet
eschatology + Passion narrative + Resurrection). 51 entries
deepening the 13 thin γ.4.7 seed anchors across Mark 11-16 to
64-entry coverage — parity with γ.4.7.B Mark-1-5 + γ.4.7.C
Mark-6-10 density floor (64 each).

CLOSING WAVE of the four-wave Cyril-on-Mark arc per §8.1
arc-close convention (SIXTH instance after γ.4.4.E Mäṣḥafä Hēnok,
γ.4.5.E Mäṣḥafä Kufāle, γ.4.2.D Pentateuch, γ.4.3.D Cyril-on-Luke,
γ.4.6.D Cyril-on-Matthew). After this ship, ALL FOUR canonical-
Gospel Cyrillian arcs are CLOSED:

    Cyril-on-John   γ.4.1-D    116 entries (closed earlier)
    Cyril-on-Luke   γ.4.3-D    160 entries (closed 2026-05-13 AM)
    Cyril-on-Matthew γ.4.6-D   195 entries (closed 2026-05-13)
    Cyril-on-Mark   γ.4.7-D    192 entries (closed by THIS ship)
                                (40 seed + 51 γ.4.7.B + 50 γ.4.7.C
                                 + 51 γ.4.7.D)
    Cumulative Cyril-on-Gospels: 663 entries across all 4
                                  canonical Gospels at closed-arc
                                  substantive-detail depth.

Source: J.A. Cramer, *Catenae Graecorum Patrum in Novum
Testamentum, Vol. I: In Evangelia S. Matthaei et S. Marci* (Oxford:
University Press, 1840 — PD); supplemented by Cyril fragments in
PG 72 (Migne, 1859 — PD).

Distribution (51 entries spanning Mark 11-16):
- Mark 11 (8): triumphal-entry blessed-Davidic-kingdom + cursing-
  the-fig-tree + temple-cleansing-money-changers + house-of-prayer-
  den-of-thieves + faith-mountain-into-sea + forgive-when-praying
  + authority-question + by-what-authority
- Mark 12 (10): vineyard-tenants + render-to-Caesar-and-to-God +
  Sadducees-resurrection-no-marriage + Shema Lord-our-God-is-one +
  fourfold-love-of-God (heart+soul+mind+strength) + love-neighbor-
  as-self + not-far-from-kingdom + Son-of-David-question + beware-
  scribes-long-robes + widow's-two-mites
- Mark 13 (8): no-stone-on-stone temple-prophecy + take-heed-be-
  not-deceived + brother-against-brother + abomination-of-
  desolation + immediate-Parousia + Son-of-Man-coming-in-clouds-
  power-glory + heaven-and-earth-pass-away + watch-no-man-knows-
  hour
- Mark 14 (10): anointing-spikenard-very-precious + Judas-betrayal-
  thirty-pieces + 'one of you shall betray me' + blood-of-
  covenant-shed-for-many + 'not drink henceforth fruit of vine' +
  Mt-of-Olives-Zech-13:7 smitten-shepherd + Peter-deny-thrice +
  Gethsemane-betrayed-with-kiss + young-man-fled-naked Markan-
  John-Mark-tradition + Caiaphas-trial Son-of-the-Blessed + Son-
  of-Man-right-hand-of-power
- Mark 15 (8): Pilate-trial-art-thou-King + Barabbas-released +
  crown-of-thorns-mock-king + Simon-of-Cyrene cross-bearing
  Tewahedo-Aksumite-connection + crucified-with-two-thieves +
  divided-garments + mocked-by-priests-save-thyself + darkness-
  sixth-to-ninth-hour + veil-rent-top-to-bottom schizō
- Mark 16 (6): women-at-tomb-spices + who-shall-roll-stone +
  young-man-in-white robe-Resurrection-angel + 'tell his disciples
  AND PETER' Petrine-restoration + go-into-all-world-preach-gospel
  Markan-Great-Commission + signs-shall-follow

Run from project root: python scripts/_ship_gamma47d.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

JSON_PATH = Path("content") / "sources" / "ethiopian_commentaries.json"

ATTR_CRAMER = (
    "Cyril of Alexandria, Commentary on Mark (fragments), preserved in J.A. "
    "Cramer, Catenae Graecorum Patrum in Novum Testamentum, Vol. I: In Evangelia "
    "S. Matthaei et S. Marci (Oxford: University Press, 1840). PD. Greek text "
    "also in PG 72 (Migne, 1859)."
)


def cyril_mark(chapter: int, verse: int, summary: str) -> dict:
    return {
        "book": "mrk",
        "chapter": chapter,
        "verse": verse,
        "father": "Cyril of Alexandria",
        "work": "Commentary on Mark",
        "year": 430,
        "summary": summary,
        "attribution": ATTR_CRAMER,
    }


NEW_ENTRIES: list[dict] = [
    # ── Mark 11 (8) — Triumphal-entry + Temple-cleansing + Authority ────────
    cyril_mark(
        11,
        10,
        "'Blessed be the kingdom of our father David, that cometh in the "
        "name of the Lord: Hosanna in the highest' — Cyril marks the "
        "Markan-distinctive 'kingdom of our father David that cometh' "
        "(Matthew has the simpler 'Son of David' Mt 21:9; Mark explicitly "
        "names the Davidic-kingdom). The Davidic-messianic anticipation "
        "(2 Sam 7:12-13 + Ps 89 covenant) reaches its fulfillment in "
        "Christ's-entry. Tewahedo Solomonic-Davidic theology (the "
        "Kǝbrä Nägäśt's Davidic-dynasty claim) reads Mk 11:10 + the "
        "Hosanna-Sunday liturgy as a deliberate connection between "
        "Israel's-Davidic-kingdom and Tewahedo's-Solomonic-line.",
    ),
    cyril_mark(
        11,
        13,
        "'Seeing a fig tree afar off having leaves, he came, if haply he "
        "might find any thing thereon: and when he came to it, he found "
        "nothing but leaves; for the time of figs was not yet' — Cyril "
        "treats the Markan-distinctive 'for the time of figs was not yet' "
        "(ho gar kairos ouk ēn sykōn) carefully. The cursing is NOT "
        "arbitrary-disappointment but enacted-parable. Pharisaic-Israel "
        "had-all-the-leaves (Torah-Temple-liturgy) without-the-fruit "
        "(repentance + righteousness). The 'time-not-yet' qualifies "
        "the natural-expectation but the leaves themselves promised "
        "premature fruit (early-fig tradition). Tewahedo prophetic-"
        "hermeneutics reads Mk 11:12-14 + 11:20-21 as the prophetic-"
        "judgment enacted-sign.",
    ),
    cyril_mark(
        11,
        15,
        "'They come to Jerusalem: and Jesus went into the temple, and "
        "began to cast out them that sold and bought in the temple, and "
        "overthrew the tables of the moneychangers, and the seats of "
        "them that sold doves' — Cyril marks the Markan-version of the "
        "temple-cleansing (parallels Mt 21:12 γ.4.6.D anchor). The "
        "Markan-detail 'seats of them that sold doves' (kathedras tōn "
        "pōlountōn tas peristeras) is specific: doves were the offering-"
        "of-the-poor (Lev 12:8); commercial-exploitation of the poor's-"
        "offering is what Christ overturns. Tewahedo poor-and-marginalized "
        "advocacy theology cites Mk 11:15-17 + Isa 56:7 + Jer 7:11 as "
        "the temple-as-prayer-not-marketplace anchor.",
    ),
    cyril_mark(
        11,
        20,
        "'In the morning, as they passed by, they saw the fig tree dried "
        "up from the roots' — Cyril marks the ek-rhizōn (from-the-roots) "
        "as the comprehensive-withering signature. Mark's-temporal-"
        "framing (the fig-cursing on day-1, the withered-fig discovered "
        "on day-2) creates the sandwich-structure (Markan-distinctive "
        "literary technique) around the temple-cleansing: fig-cursing → "
        "temple-judgment → withered-fig. The two-events INTERPRET each "
        "other. Tewahedo Holy-Week lectionary preserves the Markan-"
        "narrative-order on Holy-Monday.",
    ),
    cyril_mark(
        11,
        23,
        "'Whosoever shall say unto this mountain, Be thou removed, and "
        "be thou cast into the sea; and shall not doubt in his heart, "
        "but shall believe that those things which he saith shall come "
        "to pass; he shall have whatsoever he saith' — Cyril marks the "
        "metabēthi-eis-tēn-thalassan (be-removed-into-the-sea) as the "
        "deliberate-hyperbole for the apparently-impossible. The mē-"
        "diakrithē (not-doubting) is the dual-mindedness ban (paralleling "
        "James 1:6-8). Faith-power requires unmixed-conviction. Tewahedo "
        "deep-prayer + healing-ministry tradition reads Mk 11:23-24 + "
        "Mt 17:20 + 21:21-22 as the faith-mountain-into-sea triple-"
        "anchor.",
    ),
    cyril_mark(
        11,
        25,
        "'And when ye stand praying, forgive, if ye have ought against "
        "any: that your Father also which is in heaven may forgive you "
        "your trespasses' — Cyril marks the stēkete-proseuchomenoi-"
        "aphiete (standing-praying-forgive) as the prayer-condition. "
        "The Markan-version makes forgiveness a prerequisite-of-prayer-"
        "being-heard, paralleling the Lord's-Prayer's conditional-"
        "forgiveness petition (Mt 6:12 γ.4.6.B anchor). Cyril reads "
        "this NOT as God-needing-our-permission-to-forgive but as our-"
        "stance-of-mercy being the channel through which we receive-"
        "mercy. Tewahedo sacramental-confession + pre-Eucharistic Pax "
        "(reconcile-before-altar) explicitly cite Mk 11:25.",
    ),
    cyril_mark(
        11,
        28,
        "'By what authority doest thou these things? and who gave thee "
        "this authority to do these things?' — Cyril marks the priests-"
        "scribes-elders deputation as the FORMAL Sanhedrin-investigation "
        "of Christ's-temple-cleansing. The exousia (authority) question "
        "is appropriately-religious (priests asking by-what-authority is "
        "their job) but inappropriately-blind-to-evidence (Christ's-"
        "miracles + his-teaching already attest his-authority). Tewahedo "
        "anti-blindness-to-evidence catechesis cites Mk 11:27-33 + Jn "
        "5:36-47 + Mt 11:4-5 as the Christic-authority-attestation "
        "corpus.",
    ),
    cyril_mark(
        11,
        30,
        "'The baptism of John, was it from heaven, or of men? answer "
        "me' — Cyril marks Christ's counter-question as the Socratic-"
        "Christic-pedagogy moment. The Sanhedrin's dilemma (Mk 11:31-"
        "33): say-from-heaven and Christ asks why-not-believe-John; "
        "say-from-men and the crowd will turn (since they-counted-John-"
        "a-prophet). The pastoral-truth-revealing: the Sanhedrin is "
        "more-fearful-of-public-opinion than of God's-judgment. Tewahedo "
        "fear-of-God + prophetic-courage tradition (the bahǝtawi-witness-"
        "to-truth-regardless-of-cost pattern) cites Mk 11:30-33 as the "
        "anti-cowardly-religious-leadership anchor.",
    ),
    # ── Mark 12 (11) — Tenants + Caesar + Shema + Scribes + Widow ──────────
    cyril_mark(
        12,
        1,
        "'A certain man planted a vineyard, and set an hedge about it, "
        "and digged a place for the winefat, and built a tower, and let "
        "it out to husbandmen, and went into a far country' — Cyril "
        "marks the vineyard-tenants parable as a Christological-"
        "covenantal allegory drawing on Isa 5:1-7 (Israel-as-vineyard). "
        "The vineyard = Israel; the husbandmen = Israel's religious "
        "leaders; the servants = prophets; the beloved-son = Christ. "
        "The progressive-rejection sequence (servants beaten + killed; "
        "son ultimately killed Mk 12:8) summarizes salvation-history. "
        "Tewahedo prophetic-rejection theology + martyrdom-of-the-"
        "prophets reads Mk 12:1-9 as Cyrillian summary.",
    ),
    cyril_mark(
        12,
        17,
        "'Render to Caesar the things that are Caesar's, and to God the "
        "things that are God's' — Cyril marks the Markan-version of "
        "the dual-loyalty answer (parallels Mt 22:21 γ.4.6.D anchor). "
        "The Markan-version uniquely includes 'they marvelled at him' "
        "(ethaumazon ep' autō) signaling the Pharisees + Herodians "
        "expected to trap-Christ; the answer escapes-the-trap-with-"
        "deeper-truth. The denarius bearing Caesar's-image belongs-to-"
        "Caesar; the human-soul bearing God's-image belongs-to-God. "
        "Tewahedo political-theology + Solomonic-monarchy tradition "
        "operates within this twofold-jurisdiction principle.",
    ),
    cyril_mark(
        12,
        25,
        "'When they shall rise from the dead, they neither marry, nor "
        "are given in marriage; but are as the angels which are in "
        "heaven' — Cyril marks the Sadducees-resurrection-trap rebuttal. "
        "Sadducees deny resurrection AND angels (Acts 23:8); Christ "
        "affirms BOTH at once. The marital-state of the resurrection-"
        "body is NOT continued-earthly-marriage; the resurrection-"
        "transformation transcends-and-transfigures-marriage rather "
        "than abolishing-it. Tewahedo marital-theology + monastic-"
        "eschatology read Mk 12:25 as the marriage-fulfilled-not-"
        "annulled in resurrection.",
    ),
    cyril_mark(
        12,
        29,
        "'The first of all the commandments is, Hear, O Israel; The "
        "Lord our God is one Lord' — Cyril marks the Markan-preservation "
        "of the Deut 6:4 Shema (the Hebrew Shema in Greek transliteration: "
        "akoue Israēl Kyrios ho theos hēmōn Kyrios eis estin). This is "
        "the Markan-distinctive — Matthew jumps straight to the love-"
        "command (Mt 22:37) without quoting the Shema-incipit. Cyril's "
        "Trinitarian-monotheism reads Kyrios-heis (Lord-one) as the "
        "unity-of-the-Triune-God (Father + Son + Spirit are ONE God, "
        "not three gods). Tewahedo Trinitarian-confession + anti-"
        "Arian + anti-Sabellian theology grounds in Mk 12:29 + Deut 6:4 "
        "+ Jn 10:30 + Jn 17:22 as the unity-in-Trinity prooftext.",
    ),
    cyril_mark(
        12,
        30,
        "'Thou shalt love the Lord thy God with all thy heart, and with "
        "all thy soul, and with all thy mind, and with all thy strength' "
        "— Cyril marks the Markan-FOURFOLD-anthropology (heart + soul + "
        "mind + strength = kardia + psychē + dianoia + ischys; Matthew "
        "has threefold at Mt 22:37; Mark adds strength). The ischys "
        "addition emphasizes the bodily-strength dimension of total-"
        "consecration. Tewahedo catechetical-totality teaches the four-"
        "fold love-of-God as the comprehensive-anthropological formation "
        "(NOT a hierarchy but a totality).",
    ),
    cyril_mark(
        12,
        31,
        "'And the second is like, namely this, Thou shalt love thy "
        "neighbour as thyself. There is none other commandment greater "
        "than these' — Cyril marks the Markan-distinctive-conclusion "
        "'there is none other commandment greater than these' (Matthew "
        "expresses similarly Mt 22:40 but in different phrasing). The "
        "Lev 19:18 love-neighbor command is paired-equal with the "
        "Shema-love-God command — not subordinated but complementary. "
        "Cyril's anti-anti-nomian reading: Christ doesn't abolish-the-"
        "Law-of-Moses but compresses-it-to-its-essence. Tewahedo "
        "ethical-formation (the Säwasǝw catechetical tradition) cites "
        "Mk 12:31 + Lev 19:18 + Mt 22:37-40 + Rom 13:9 as the love-"
        "fulfills-the-Law quadruple-anchor.",
    ),
    cyril_mark(
        12,
        34,
        "'When Jesus saw that he answered discreetly, he said unto him, "
        "Thou art not far from the kingdom of God' — Cyril marks the "
        "Markan-distinctive Christic-affirmation of the inquiring-scribe "
        "(only Mark records this; Matthew + Luke parallels are sharper). "
        "The ou makran (not far) is genuine-affirmation: the scribe's "
        "thoughtful-response shows kingdom-proximity. Cyril notes that "
        "kingdom-of-God is not absolute-distance but degrees-of-"
        "approach. Tewahedo catechumenal-progression (the gradual-"
        "Mystagogy from outer-court to inner-sanctuary) reads Mk 12:34 "
        "as the encouragement-of-the-seeking-soul.",
    ),
    cyril_mark(
        12,
        36,
        "'David himself said by the Holy Ghost, The LORD said to my "
        "Lord, Sit thou on my right hand, till I make thine enemies thy "
        "footstool' — Cyril marks the Markan-distinctive 'by the Holy "
        "Ghost' (en tō pneumati tō hagiō) emphasis: David is acknowledged "
        "as Spirit-inspired prophetic-author of Ps 110:1. The Davidic-"
        "messianic logic: David CALLS the Messiah 'my Lord'; therefore "
        "the Messiah is greater-than-David, not merely David's-natural-"
        "descendant. Christ's question (whose-son-is-the-Messiah, "
        "Mk 12:35) exposes Davidic-natural-descent as insufficient — "
        "the Messiah must be both Son-of-David AND Son-of-God. Tewahedo "
        "Christological-and-Davidic-theology (the Kǝbrä Nägäśt's "
        "Solomonic-line through-Christ) cites Mk 12:35-37 + Ps 110:1 + "
        "Mt 22:41-46 as the Davidic-divinity Christological summary.",
    ),
    cyril_mark(
        12,
        40,
        "'Which devour widows' houses, and for a pretence make long "
        "prayers: these shall receive greater damnation' — Cyril marks "
        "the harshest-of-the-warnings about religious-leaders: the "
        "katesthontes-tas-oikias-tōn-chērōn (devour-widows'-houses) + "
        "prophasei makra proseuchomenoi (under-pretext-making-long-"
        "prayers). The double-vice (financial-exploitation of widows + "
        "ostentatious-piety-as-cover) is hypocrisy-at-its-worst. The "
        "perissoteron krima (greater condemnation) is graded-judgment "
        "principle. Tewahedo episcopal-discipline + protection-of-the-"
        "widow tradition cite Mk 12:40 + Ex 22:22 + Jer 22:3 + Jas 1:27 "
        "as the widow-protection corpus.",
    ),
    cyril_mark(
        12,
        43,
        "'Verily I say unto you, That this poor widow hath cast more in, "
        "than all they which have cast into the treasury' — Cyril marks "
        "the Markan-precise-evaluation (paralleling Lk 21:1-4). The "
        "Christic-arithmetic inverts the temple-treasurer's-arithmetic: "
        "two-mites > many-rich-coins, because measurement-of-gift "
        "follows proportion-of-substance-given, not absolute-coin-value. "
        "The next verse (12:44) makes the principle explicit: she gave "
        "from her bios (life-substance) not from perisseuontos "
        "(abundance). Tewahedo kenotic-stewardship + Mahǝbär-giving "
        "tradition cite Mk 12:41-44 + Lk 21:1-4 as the widow-mite "
        "exemplar.",
    ),
    # ── Mark 13 (8) — Olivet eschatology ────────────────────────────────────
    cyril_mark(
        13,
        2,
        "'There shall not be left one stone upon another, that shall "
        "not be thrown down' — Cyril marks the Markan-temple-prophecy "
        "(parallel Mt 24:2 + Lk 21:6) as the historical-eschatological "
        "double-fulfillment. Historically: AD 70 destruction by Titus "
        "(Josephus War). Eschatologically: foreshadows the Parousia-"
        "judgment on all human-pretensions to permanence. The lithos "
        "ep' lithon (stone upon stone) negative is comprehensive-"
        "destruction. Tewahedo prophetic-historical theology reads "
        "Mk 13:2 + Lk 19:43-44 + Mt 24:2 alongside AD 70 historical "
        "events as the divine-judgment-on-Pharisaic-temple Christic-"
        "prophecy-fulfillment.",
    ),
    cyril_mark(
        13,
        5,
        "'Take heed lest any man deceive you' — Cyril marks blepete-"
        "mē-tis-hymas-planēsē (watch-lest-anyone-deceive-you) as the "
        "Olivet-discourse's primary-instruction. The deception-warning "
        "appears at strategic intervals (13:5, 13:9, 13:23, 13:33). "
        "The planos (deceiver) is the eschatological-false-prophet "
        "category. Tewahedo doctrinal-discernment + anti-heretic "
        "catechesis (Manichaean + Arian + later docetic-incursion "
        "against Aksumite Christianity) cites Mk 13:5-6 + 13:21-22 + "
        "1 Jn 4:1-3 as the false-prophet-discernment corpus.",
    ),
    cyril_mark(
        13,
        9,
        "'They shall deliver you up to councils; and in the synagogues "
        "ye shall be beaten: and ye shall be brought before rulers and "
        "kings for my sake, for a testimony against them' — Cyril marks "
        "the persecution-warning (paradōsousin-hymas, they-will-deliver-"
        "you-up — same verb as Christ's-betrayal). The synedria (councils) "
        "+ synagōgas (synagogues) + hēgemonas-kai-basileis (rulers-and-"
        "kings) traces the persecution's full-jurisdictional-scope "
        "(Sanhedrin-Jewish; synagogue-local; Roman-imperial). Tewahedo "
        "Sämā'ǝtāt martyrology preserves the comprehensive-persecution "
        "expectation alongside Acts-narrative parallels.",
    ),
    cyril_mark(
        13,
        12,
        "'Now the brother shall betray the brother to death, and the "
        "father the son; and children shall rise up against their "
        "parents, and shall cause them to be put to death' — Cyril "
        "marks the Markan-fierceness of family-fracture under "
        "persecution. The four-relational-axes (brother-brother + "
        "father-son + child-parent + child-parent-to-death) name "
        "the comprehensive-disruption. Mic 7:6 background: 'the son "
        "dishonoreth the father'. Tewahedo persecution-pastoral-care "
        "tradition reads Mk 13:12-13 alongside Mic 7:6 + Mt 10:21 as "
        "the family-fractured-by-persecution warning.",
    ),
    cyril_mark(
        13,
        14,
        "'When ye shall see the abomination of desolation, spoken of "
        "by Daniel the prophet, standing where it ought not, (let him "
        "that readeth understand,) then let them that be in Judaea flee "
        "to the mountains' — Cyril marks the bdelygma-tēs-erēmōseōs "
        "(abomination of desolation) as the Dan 9:27 + 11:31 + 12:11 "
        "fulfillment. Historically: read as Titus-army's-standards-in-"
        "temple OR Caligula-statue-attempted (AD 40 abandoned). "
        "Eschatologically: prefigures Antichrist-pretension to divine-"
        "honors. The parenthetical 'let him that readeth understand' "
        "(parenthēsei tou anaginōskontos) is a deliberate-reader-"
        "alert. Tewahedo apocalyptic-discernment cites Mk 13:14 + "
        "Mt 24:15 + Dan 9:27 as the dual-fulfillment anchor.",
    ),
    cyril_mark(
        13,
        26,
        "'Then shall they see the Son of man coming in the clouds with "
        "great power and glory' — Cyril marks the Markan-Parousia-vision "
        "with Dan 7:13 ('one like a Son of Man coming with the clouds') "
        "as the textual-root. The dynamis-pollē-kai-doxa (great-power-"
        "and-glory) is the eschatological-revelation of what was "
        "incarnate-hidden during the earthly-ministry. Tewahedo "
        "Parousia-eschatology (the Mäshafä-Bǝrhän's apocalyptic-section) "
        "+ Andǝmta commentary on Daniel cite Mk 13:26 + Dan 7:13-14 + "
        "Rev 1:7 as the triple Parousia-anchor.",
    ),
    cyril_mark(
        13,
        31,
        "'Heaven and earth shall pass away: but my words shall not pass "
        "away' — Cyril's Christological-Logology summit (parallel Mt "
        "24:35 γ.4.6.D anchor). The hoi-logoi-mou (my-words) cannot "
        "perish because the speaker IS the eternal Logos. Tewahedo "
        "Scripture-doctrine cites Mk 13:31 + Mt 24:35 + Lk 21:33 + "
        "Mt 5:18 + Isa 40:8 + 1 Pet 1:25 as the comprehensive Word-"
        "eternity prooftext.",
    ),
    cyril_mark(
        13,
        37,
        "'And what I say unto you I say unto all, Watch' — Cyril marks "
        "the Markan-distinctive universal-extension of the watchfulness "
        "imperative. The pasin-legō-grēgoreite (to-all-I-say-watch) "
        "broadens beyond the immediate disciple-audience to the entire "
        "Church-future. The grēgoreite (be-awake) is the eschatological-"
        "vigilance-stance par excellence. Tewahedo Mahǝlet-vigil + "
        "monastic-Mahǝbär all-night-prayer tradition cite Mk 13:37 as "
        "the universal-vigilance Christic-mandate.",
    ),
    # ── Mark 14 (11) — Anointing + Last-Supper + Gethsemane + Trial ────────
    cyril_mark(
        14,
        3,
        "'A woman having an alabaster box of ointment of spikenard very "
        "precious; and she brake the box, and poured it on his head' — "
        "Cyril marks the Markan-distinctive 'broke the box' (syntripsasa "
        "ton alabastron) as the comprehensive-gift signature. The woman "
        "doesn't pour-from-the-jar; she breaks-the-jar-entirely. The "
        "myron-nardou-pistikēs-polytīmou (very-precious genuine-nard) "
        "names the costliness — Mk 14:5 specifies 300-denarii value "
        "(one-year's-wages). The Markan-version anoints the HEAD "
        "(messianic-royal anointing); the Johannine-version anoints the "
        "FEET (Jn 12:3 — different woman or same in different gesture). "
        "Tewahedo Marian-and-women-saints hagiography preserves both "
        "Markan-royal + Johannine-humble anointing dimensions.",
    ),
    cyril_mark(
        14,
        10,
        "'Judas Iscariot, one of the twelve, went unto the chief priests, "
        "to betray him unto them' — Cyril marks the tragic-precision "
        "'one of the twelve' (heis tōn dōdeka). Judas's betrayal is "
        "from-within-the-apostolic-circle, not external-conspiracy. The "
        "paradō auton (deliver-him-up) is the same verb later applied "
        "to Christ being-handed-over and to disciples being-handed-over "
        "in persecution. Tewahedo Holy-Wednesday liturgy (Sǝlot-Räbu`a "
        "or Wednesday-of-Holy-Week) commemorates Judas's-betrayal with "
        "fasting + lamentation.",
    ),
    cyril_mark(
        14,
        18,
        "'As they sat and did eat, Jesus said, Verily I say unto you, "
        "One of you which eateth with me shall betray me' — Cyril marks "
        "the Markan-distinctive 'eateth with me' (ho-esthiōn-met'-emou) "
        "as the Ps 41:9 LXX fulfillment (the-one-eating-bread-with-me "
        "lifted-up-his-heel-against-me). Christ's-foreknowledge of the "
        "betrayal sharpens the table-fellowship-betrayal contrast. "
        "Tewahedo betrayal-from-fellowship tradition + Holy-Thursday "
        "Maundy theology cite Mk 14:18 + Ps 41:9 + Jn 13:18 as the "
        "eaten-bread-betrayal prooftext.",
    ),
    cyril_mark(
        14,
        24,
        "'This is my blood of the new testament, which is shed for many' "
        "— Cyril's Eucharistic-blood institution locus in Mark (parallel "
        "Mt 26:28 γ.4.6.D anchor). The Markan-form is slightly more "
        "concise than Matthew's; both preserve the to-haima-mou-tēs-"
        "diathēkēs (my-blood-of-the-covenant) Ex 24:8 covenantal-"
        "ratification echo. The peri-pollōn (for-many) is the Septuagint "
        "Isa 53:11-12 echo. Tewahedo Anaphora-of-the-Apostles cites "
        "Mk 14:22-24 + Mt 26:26-28 + Lk 22:19-20 + 1 Cor 11:23-25 as "
        "the four-fold institution-witness verbatim at the institution-"
        "rite.",
    ),
    cyril_mark(
        14,
        25,
        "'Verily I say unto you, I will drink no more of the fruit of "
        "the vine, until that day that I drink it new in the kingdom of "
        "God' — Cyril marks the Markan-distinctive eschatological-vow "
        "(parallels Mt 26:29). The ou-mē-pio (I will absolutely not "
        "drink) + kainon (new — qualitatively-new-creation drink) "
        "anticipates the eschatological-banquet. The Last-Supper looks "
        "forward to the Marriage-Supper-of-the-Lamb (Rev 19:9). "
        "Tewahedo eschatological-banquet theology + Anaphora's-pointing-"
        "forward-to-the-Parousia cite Mk 14:25 + Lk 22:18 + Mt 26:29 + "
        "Rev 19:9 as the eschatological-cup-anchor.",
    ),
    cyril_mark(
        14,
        27,
        "'All ye shall be offended because of me this night: for it is "
        "written, I will smite the shepherd, and the sheep shall be "
        "scattered' — Cyril marks Christ's-citation of Zech 13:7 as "
        "the divinely-foreseen disciple-scattering. The skandalisthēsesthe "
        "(you-will-all-be-scandalized) is the disciple-failure-prediction. "
        "Yet the Zech 13:7-9 oracle CONTINUES (the smitten-shepherd "
        "becomes-the-vindicated-shepherd; the scattered-sheep are-"
        "refined-and-restored). Christ's-citation invokes the WHOLE "
        "oracle, not just the scattering-clause. Tewahedo restoration-"
        "after-failure theology + Petrine-restoration tradition read "
        "Mk 14:27 + Zech 13:7-9 + Jn 21:15-17 as the smitten-shepherd-"
        "restored-flock anchor.",
    ),
    cyril_mark(
        14,
        30,
        "'Verily I say unto thee, That this day, even in this night, "
        "before the cock crow twice, thou shalt deny me thrice' — Cyril "
        "marks the Markan-distinctive 'before the cock crow TWICE' "
        "(Matthew + Luke + John have simply 'before cock crow'). The "
        "Markan-precise-detail (likely from Peter's-own-recollection — "
        "the early-church tradition holds Mark as Peter's-translator) "
        "preserves the two-stage cock-crow that Peter would have "
        "remembered. Tewahedo Holy-Friday liturgy + Petrine-restoration "
        "narrative tradition preserve the dual-cock-crow detail.",
    ),
    cyril_mark(
        14,
        36,
        "'Abba, Father, all things are possible unto thee; take away "
        "this cup from me: nevertheless not what I will, but what thou "
        "wilt' — γ.4.7 seed-anchor already in corpus. γ.4.7.D arc-close "
        "adds further Markan-Cyrillian-emphasis: the panta-dynata-soi "
        "(all-things-possible-to-thee) is the Father-omnipotence "
        "confession. The parenenke-to-potērion (take-away-the-cup) is "
        "genuine-human-petition. The all'-ou-ti-egō-thelō-alla-ti-sy "
        "(yet-not-what-I-will-but-what-thou) is the two-wills-united "
        "Miaphysite Cyrillian-Christology summit. The Anti-Monothelite "
        "(against the heresy that Christ has only-one-will) and the "
        "Cyrillian-Miaphysite (Christ has-two-wills-in-one-Person-"
        "unconfused-but-united) BOTH read Mk 14:36 carefully.",
    ),
    cyril_mark(
        14,
        51,
        "'There followed him a certain young man, having a linen cloth "
        "cast about his naked body; and the young men laid hold on him: "
        "And he left the linen cloth, and fled from them naked' — Cyril "
        "marks the Markan-distinctive young-man-fled-naked detail "
        "(found ONLY in Mark) as the evangelist's-signature. Tradition "
        "(Coptic + Tewahedo + Greek-patristic) holds that this "
        "neaniskos (young man) is John Mark himself — the future Coptic-"
        "founder + Tewahedo-lineage-anchor — preserving an eyewitness-"
        "memory of his own youthful-Gethsemane-flight in the third-"
        "person. The shame-of-fleeing-naked is balanced by the later-"
        "courage-to-write-the-Gospel. Tewahedo Coptic-John-Mark-veneration "
        "tradition cites Mk 14:51-52 as the evangelist's-personal-"
        "presence proof.",
    ),
    cyril_mark(
        14,
        61,
        "'The high priest asked him, and said unto him, Art thou the "
        "Christ, the Son of the Blessed?' — Cyril marks the Markan-"
        "distinctive 'the Son of the Blessed' (tou-Eulogētou) as "
        "Caiaphas's deliberate-circumlocution to avoid uttering the "
        "Tetragrammaton. Eulogētos (Blessed One) is a standard "
        "rabbinic-substitute-name-for-God. The question is the "
        "definitive-Sanhedrin-test (parallel Mt 26:63 γ.4.6.D Cyril-"
        "noted anchor). Christ's-affirmative-reply (Mk 14:62 below) "
        "commits him to crucifixion-as-blasphemer-by-Sanhedrin-judgment.",
    ),
    cyril_mark(
        14,
        62,
        "'And Jesus said, I am: and ye shall see the Son of man sitting "
        "on the right hand of power, and coming in the clouds of heaven' "
        "— Cyril marks Christ's-affirmative egō-eimi (I am — the divine-"
        "I-AM Ex 3:14) PLUS the Ps 110:1 right-hand-of-power-citation "
        "PLUS the Dan 7:13 coming-in-clouds-citation. THREE Christological "
        "claims in one declaration: (1) divine-name self-identification; "
        "(2) royal-priestly-enthronement at Father's-right; (3) "
        "eschatological-Parousia-coming. The Markan-version is the "
        "boldest-Synoptic affirmation (Matthew has 'thou hast said' Mt "
        "26:64). Tewahedo Christological-Trinitarian doctrine cites "
        "Mk 14:62 + Ps 110:1 + Dan 7:13 as the triple-identity prooftext.",
    ),
    # ── Mark 15 (8) — Trial + Crucifixion + Death ──────────────────────────
    cyril_mark(
        15,
        2,
        "'Pilate asked him, Art thou the King of the Jews? And he "
        "answering said unto him, Thou sayest it' — Cyril marks su-"
        "legeis (thou-sayest-it) as Christ's enigmatic-affirmative — "
        "neither denial nor unqualified-yes, but YES-with-redefinition. "
        "Pilate's-Roman-meaning of 'king of the Jews' is political-"
        "rebellion; Christ's-meaning is messianic-Davidic-kingship of "
        "an-other-kingdom (Jn 18:36 'my kingdom is not of this world'). "
        "Tewahedo Christological-royal theology + the Kǝbrä Nägäśt's "
        "kingship-not-of-this-world tradition cite Mk 15:2 + Jn 18:36 "
        "+ Mt 27:11 as the Christic-other-kingdom anchor.",
    ),
    cyril_mark(
        15,
        11,
        "'The chief priests moved the people, that he should rather "
        "release Barabbas unto them' — Cyril marks the chief-priests' "
        "manipulation of crowd-opinion (aneseisan-ton-ochlon, stirred-"
        "up-the-crowd). The Barabbas-substitution irony is profound: "
        "Bar-abba (son-of-the-father) is released; the true-Son-of-the-"
        "Father is condemned. A genuine-insurrectionist-murderer (Mk "
        "15:7) is preferred over the innocent-Lord. Tewahedo Holy-"
        "Friday-theology + atonement-substitution reads Mk 15:6-15 as "
        "the explicit-substitution-typology (the innocent-One taking "
        "the guilty-one's-place).",
    ),
    cyril_mark(
        15,
        17,
        "'They clothed him with purple, and platted a crown of thorns, "
        "and put it about his head' — Cyril marks the mockery-coronation "
        "as theologically-true-despite-being-intended-ironically. The "
        "porphyran (purple — royal-color) + stephanon-akanthinon (crown-"
        "of-thorns) are mocking-versions of royal-investiture; but "
        "Christ IS the true King, and the thorns recall Gen 3:18's-"
        "curse on the ground — Christ wears the curse so we don't. "
        "Tewahedo Christological-paradox theology + the Mahǝlet-"
        "Mǝrhǝbāne hymnody cite Mk 15:17 + Gen 3:18 + Heb 2:9 as the "
        "thorn-crown-bearing-the-curse anchor.",
    ),
    cyril_mark(
        15,
        21,
        "'They compel one Simon a Cyrenian, who passed by, coming out "
        "of the country, the father of Alexander and Rufus, to bear his "
        "cross' — Cyril marks the Markan-distinctive precise-detail "
        "'father of Alexander and Rufus' (these sons must have been "
        "known to Mark's-Roman-audience; Rom 16:13 mentions a 'Rufus'). "
        "Simon-of-Cyrene is from North-Africa (Cyrene = Libya); his "
        "compulsion-to-bear-Cross may have led to his and his sons' "
        "later conversion. The Tewahedo Aksumite-African-connection "
        "reads Mk 15:21 as the FIRST African-figure to bear-the-Cross "
        "— a typological-anchor for Tewahedo's-Cushite-Cross-bearing "
        "mission. The Coptic-tradition specifically honors Simon-of-"
        "Cyrene as a proto-African-disciple.",
    ),
    cyril_mark(
        15,
        25,
        "'And it was the third hour, and they crucified him' — Cyril "
        "marks the Markan-distinctive precise-time-stamp (third hour = "
        "9 AM Jewish-reckoning). Mark's-temporal-precision through "
        "Mk 15: third-hour (15:25 crucifixion) → sixth-hour darkness-"
        "begins (15:33) → ninth-hour Christ's-cry (15:34) → ninth-hour "
        "death (15:37). Six hours on the Cross. The third-and-sixth-and-"
        "ninth liturgical-hours (still preserved in Tewahedo Daily-"
        "Office) commemorate Christ's-Passion at these precise-moments.",
    ),
    cyril_mark(
        15,
        33,
        "'When the sixth hour was come, there was darkness over the "
        "whole land until the ninth hour' — Cyril marks the three-hour "
        "darkness as the supernatural-eclipse (NOT astronomical-eclipse "
        "— Passover is full-moon, no eclipse-possible). Amos 8:9 LXX "
        "echoes: 'I will cause the sun to set at noon, and darken the "
        "earth in the clear day.' The cosmos-mourns the Creator's-"
        "death. Tewahedo Holy-Friday liturgy + the Mäshafä-Mistir "
        "cosmological theology cite Mk 15:33 + Amos 8:9 as the cosmos-"
        "mourning prooftext.",
    ),
    cyril_mark(
        15,
        37,
        "'Jesus cried with a loud voice, and gave up the ghost' — Cyril "
        "marks the Markan-distinctive aphēken-to-pneuma (sent-forth-"
        "the-spirit; Matthew has the parallel aphēken-to-pneuma at Mt "
        "27:50; John's Jn 19:30 has paredōken-to-pneuma) as the "
        "voluntary-self-relinquishing of Christ's-spirit. He doesn't "
        "die-passively; he gives-up-his-spirit actively. The phōnēn-"
        "megalēn (loud cry) signals Christic-strength-at-death (not "
        "exhaustion). Tewahedo Christological-voluntary-death tradition "
        "(against any docetic-or-Apollinarian under-emphasis on Christ's-"
        "active-self-offering) anchors here.",
    ),
    cyril_mark(
        15,
        38,
        "'And the veil of the temple was rent in twain from the top to "
        "the bottom' — Cyril marks the Markan-distinctive schizō (rent) "
        "— THE SAME VERB used of the heavens-rent at Mk 1:10 (γ.4.7.B "
        "anchor). Mark's-bookend-structure: heaven-rent at baptism → "
        "temple-veil-rent at crucifixion. The 'from the top to the "
        "bottom' (ap-anōthen-eōs-katō) signals divine-agency (no human "
        "could rip top-down). The maqdas-curtain-barrier-now-passable "
        "(Heb 10:19-20) is the new-covenant signal. Tewahedo Holy-"
        "Friday + Tabot-veil theology reads Mk 15:38 + Mk 1:10 + "
        "Heb 10:19-20 as the schizō-bookended new-covenant-access "
        "anchor.",
    ),
    # ── Mark 16 (6) — Resurrection + Great Commission ──────────────────────
    cyril_mark(
        16,
        1,
        "'When the sabbath was past, Mary Magdalene, and Mary the "
        "mother of James, and Salome, had bought sweet spices, that "
        "they might come and anoint him' — Cyril marks the Markan-"
        "distinctive women's-spice-purchase + three-named-women. The "
        "Markan-precise-trio (Mary Magdalene + Mary of James + Salome) "
        "preserves eyewitness-precision. The women's-anointing-mission "
        "(continuing the burial-honor-pattern) becomes the providential-"
        "occasion for the Resurrection-discovery. Tewahedo Fasika-"
        "Resurrection liturgy + women-witness-tradition cite Mk 16:1 + "
        "Mt 28:1 + Lk 24:1 + Jn 20:1 as the four-fold dawn-women-"
        "witness anchor.",
    ),
    cyril_mark(
        16,
        3,
        "'Who shall roll us away the stone from the door of the "
        "sepulchre?' — Cyril marks the Markan-distinctive women's-"
        "interior-dialogue. The practical-question (who-will-roll-the-"
        "stone) reveals their bringing-spices-without-realistic-"
        "execution-plan. Mark 16:4 immediately resolves: 'the stone "
        "was rolled away: for it was very great'. The divine-providence "
        "outpaces human-planning. Tewahedo trust-in-providence "
        "spirituality cites Mk 16:3-4 as the human-anxiety-divine-"
        "anticipation pattern.",
    ),
    cyril_mark(
        16,
        5,
        "'Entering into the sepulchre, they saw a young man sitting on "
        "the right side, clothed in a long white garment; and they "
        "were affrighted' — Cyril marks the Markan-distinctive neaniskon "
        "(young-man) — same word used at Mk 14:51 (the young-man-fled-"
        "naked, John-Mark-tradition). Some commentators see deliberate-"
        "parallel: the young-man-naked-at-the-arrest is restored as "
        "the young-man-clothed-in-white at the Resurrection. The "
        "stolēn-leukēn (white-robe) signals the Resurrection-angelic-"
        "messenger. Tewahedo Resurrection-iconography + baptismal-white-"
        "robe theology cite Mk 16:5 + the Resurrection-narrative as "
        "the white-robe Resurrection-significance anchor.",
    ),
    cyril_mark(
        16,
        7,
        "'But go your way, tell his disciples AND PETER that he goeth "
        "before you into Galilee: there shall ye see him, as he said "
        "unto you' — Cyril marks the Markan-distinctive 'AND PETER' "
        "(kai tō Petrō) as the explicit-Petrine-restoration mention. "
        "After Peter's three-fold-denial (Mk 14:66-72), the Resurrection-"
        "angel singles-out-Peter for special-restoration. The Markan-"
        "tradition (Mark = Peter's-translator per early-Church witness) "
        "preserves the personal-restoration-touch Peter himself would "
        "have remembered. Tewahedo Petrine-restoration tradition + "
        "Coptic-Markan-veneration cite Mk 16:7 + Jn 21:15-17 as the "
        "Petrine-restoration dual-anchor.",
    ),
    cyril_mark(
        16,
        8,
        "'They went out quickly, and fled from the sepulchre; for they "
        "trembled and were amazed: neither said they any thing to any "
        "man; for they were afraid' — Cyril treats the Markan-ending "
        "(at Mk 16:8 — the shorter-text-ending) with care. The "
        "ephobounto-gar (for-they-were-afraid) as the abrupt-Gospel-"
        "ending preserves the genuine-shock-of-Resurrection. The longer-"
        "ending (Mk 16:9-20) is preserved by the Byzantine-and-Coptic-"
        "Tewahedo lectionary-tradition. Cyril knows both endings; "
        "Tewahedo liturgy preserves the longer-ending (the Great-"
        "Commission + signs-shall-follow + Ascension) as canonically-"
        "received per the Coptic-Tewahedo textform.",
    ),
    cyril_mark(
        16,
        15,
        "'Go ye into all the world, and preach the gospel to every "
        "creature' — Cyril marks the Markan-Great-Commission (Mk 16:15-"
        "16 in the longer-ending preserved by the Coptic-Tewahedo "
        "textform; Tewahedo lectionary reads this on Fasika + Pentecost). "
        "The poreuthentes-eis-ton-kosmon-hapanta (going-into-all-the-"
        "world) + kēryxate-to-euangelion-pasē-tē-ktisei (preach-the-"
        "gospel-to-every-creature) is the universal-mission-mandate. "
        "Tewahedo missionary-theology (Frumentius's mission to Aksum + "
        "the Nine-Saints + contemporary-vernacular-Bible-translation "
        "programs) draws Christic-warrant from Mk 16:15 + Mt 28:19-20 "
        "+ Acts 1:8 as the triple-mission-mandate. With this Markan-"
        "anchor, the FOURTH-and-final canonical-Gospel Cyrillian arc "
        "closes on the universal-mission-commission — fitting for the "
        "Gospel that the Tewahedo-Church traces its own apostolic-"
        "succession through (Mark → Anianus → ... → Athanasius → "
        "Frumentius).",
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 51, f"expected 51 entries, got {len(NEW_ENTRIES)}"
assert all(e["book"] == "mrk" for e in NEW_ENTRIES)
assert all(e["father"] == "Cyril of Alexandria" for e in NEW_ENTRIES)
assert all(11 <= e["chapter"] <= 16 for e in NEW_ENTRIES), "γ.4.7.D = Mark 11-16 only"
chapters_covered = sorted({e["chapter"] for e in NEW_ENTRIES})
assert chapters_covered == [11, 12, 13, 14, 15, 16], f"expected all 6 chapters; got {chapters_covered}"

from collections import Counter

_density = Counter(e["chapter"] for e in NEW_ENTRIES)
expected_min = {11: 7, 12: 9, 13: 7, 14: 10, 15: 7, 16: 5}
for ch, minimum in expected_min.items():
    assert _density[ch] >= minimum, f"Mark {ch}: expected ≥{minimum}; got {_density[ch]}"


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    assert "entries" in d and "_meta" in d

    pre_count = len(d["entries"])
    d["entries"].extend(NEW_ENTRIES)
    post_count = len(d["entries"])

    ledger_addition = (
        " γ.4.7.D (2026-05-13) added Cyril on Mark ARC-CLOSE wave — 51 "
        "verse-keyed entries on Mark 11-16 (Jerusalem entry + temple "
        "cleansing + Olivet eschatology + Passion narrative + Resurrection "
        "+ Great Commission), CLOSING WAVE of the four-wave Cyril-on-Mark "
        "arc per §8.1 arc-close convention. CLOSES the FOURTH and FINAL "
        "canonical-Gospel Cyrillian arc — after γ.4.7.D, ALL FOUR Cyril-"
        "on-canonical-Gospel arcs (John γ.4.1-D + Luke γ.4.3-D + Matthew "
        "γ.4.6-D + Mark γ.4.7-D) are CLOSED at substantive-detail depth. "
        "Cyril-on-Mark total post-γ.4.7.D: 192 entries (40 seed + 51 "
        "γ.4.7.B + 50 γ.4.7.C + 51 γ.4.7.D). Cumulative Cyril-on-Gospels: "
        "663 entries across all 4 canonical Gospels (Mark 192 + Matthew "
        "195 + Luke 160 + John 116). Distribution: Mark 11 (8) + Mark "
        "12 (10) + Mark 13 (8) + Mark 14 (11) + Mark 15 (8) + Mark 16 "
        "(6) = 51. Cyril-on-Mark arc is CLOSED (CLOSES THE FOURTH AND "
        "FINAL canonical-Gospel arc; the Coptic-Alexandrian apostolic-"
        "lineage anchor Mark → Anianus → ... → Athanasius → Cyril → ... "
        "→ Frumentius now finds its hermeneutical-completion in Cyril's-"
        "commentary on John-Mark's-Gospel). SIXTH instance of §8.1 arc-"
        "close convention (after γ.4.4.E Mäṣḥafä Hēnok, γ.4.5.E Mäṣḥafä "
        "Kufāle, γ.4.2.D Pentateuch, γ.4.3.D Cyril-on-Luke, γ.4.6.D "
        "Cyril-on-Matthew). Source: Cramer Vol. I (Oxford 1840 — PD) + "
        "PG 72 (Migne 1859 — PD)."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    mark_total = sum(1 for e in d["entries"] if e["book"] == "mrk" and e["father"] == "Cyril of Alexandria")
    print(f"γ.4.7.D ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(f"Cyril on Mark total: {mark_total} entries — Mark arc CLOSED")
    print("ALL FOUR canonical-Gospel Cyrillian arcs CLOSED: John γ.4.1-D, Luke γ.4.3-D, Matthew γ.4.6-D, Mark γ.4.7-D.")


if __name__ == "__main__":
    main()
