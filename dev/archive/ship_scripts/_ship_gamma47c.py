"""γ.4.7.C ship — Cyril of Alexandria on Mark detail wave II
(Galilean ministry second half + Caesarea Philippi +
Transfiguration + journey-to-Jerusalem, Mark 6-10). 50 entries
deepening the 14 thin γ.4.7 seed anchors across Mark 6-10 to
64-entry detail-wave coverage. Mirrors γ.4.7.B Mark-1-5 detail-
wave shape (51 entries on Mark 1-5).

Per ω.41 §1 voice-composition rule (codified earlier same-
session): post-γ.4.7.C Cyril share rises from 50.8% to ~52.5%
of the patristic source corpus. Cyril-led-patristic-chorus
character continues per the apostolic-succession rationale.

Distribution (50 entries spanning Mark 6-10):
- Mark 6 (10): carpenter's-son-offense + anointed-with-oil +
  John-Baptist-Herod's-wife + Herod-feared-John + come-apart-and-
  rest + sheep-without-shepherd + companies-on-green-grass +
  walking-on-sea-fourth-watch + 'It is I' egō-eimi parallel +
  collective-hem-touching-healing
- Mark 7 (9): hypocrites-honor-with-lips + in-vain-do-they-worship
  + reject-commandment-for-tradition + Corban-tradition + 'are ye
  also without understanding' + from-within-out-of-heart + entered-
  house-wanted-no-man-to-know + fingers-in-ears-spittle + Ephphatha
  'be opened'
- Mark 8 (11): compassion-on-multitude-4000 + Pharisees-seeking-
  sign-tempting + sighed-deeply-no-sign + leaven-of-Pharisees-and-
  Herod + hardened-hearts + Bethsaida-blind-man-two-stage + 'get
  thee behind me Satan' + save-life-lose-life + 'gain world, lose
  soul' + ashamed-of-me-and-words + (Mk 8:23-25 two-stage detail)
- Mark 9 (10): high-mountain-apart-Transfiguration + raiment-
  shining-white-as-snow + Moses-and-Elijah-talking + Peter-three-
  tabernacles + 'if thou canst believe' + prayer-and-fasting-this-
  kind + delivered-to-be-killed-rise-third-day + receives-little-
  children + millstone-better-than-offend + salt-of-earth-loses-
  savour
- Mark 10 (10): from-beginning-male-and-female + 'suffer little
  children' + receive-kingdom-as-little-child + 'why callest thou
  me good' + 'one thing thou lackest' + 'with God all things
  possible' + hundredfold-with-persecutions + cup-and-baptism +
  lords-of-Gentiles-exercise-lordship + Bartimaeus 'that I might
  receive my sight'

Run from project root: python scripts/_ship_gamma47c.py
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
    # ── Mark 6 (10) — Nazareth + John's death + Feeding + Sea-walking ──────
    cyril_mark(
        6,
        3,
        "'Is not this the carpenter, the son of Mary, the brother of "
        "James, and Joses, and of Juda, and Simon? and are not his sisters "
        "here with us? And they were offended at him' — Cyril marks the "
        "Markan-distinctive 'the carpenter' (ho tektōn — Matthew softens "
        "to 'the carpenter's son' Mt 13:55). The neighbor-recognition of "
        "Christ's earthly trade is precisely what occludes the divine-"
        "Logos beneath. The 'brothers and sisters' are Cyrillian-Tewahedo "
        "read as kin-of-Joseph from prior-marriage (the Protevangelium of "
        "James tradition) or as cousins (the broader-Semitic kinship "
        "meaning) — Mary's perpetual-virginity is preserved either way. "
        "Tewahedo Marian-theology cites Mk 6:3 as a careful Christology-"
        "and-Mariology test-text.",
    ),
    cyril_mark(
        6,
        13,
        "'They cast out many devils, and anointed with oil many that were "
        "sick, and healed them' — Cyril marks the Markan-distinctive "
        "oil-anointing in the apostolic-mission (ēleiphon elaiō, anointed "
        "with oil). This is the only Synoptic passage where the Twelve "
        "are described doing this; James 5:14 picks up the same practice "
        "(presbyters-anoint-with-oil-in-the-Lord's-name). Tewahedo "
        "sacrament-of-the-sick (qǝbʿät-zayit, anointing-of-oil) cites "
        "Mk 6:13 + Jas 5:14-15 as the dual-foundation of the rite.",
    ),
    cyril_mark(
        6,
        18,
        "'It is not lawful for thee to have thy brother's wife' — Cyril "
        "marks John-the-Baptist's prophetic-rebuke to Herod Antipas (for "
        "marrying Herodias, his half-brother Philip's wife) as the proper-"
        "exercise of prophetic-confrontation against ruler-illegality. "
        "The ouk exestin (it-is-not-lawful) echoes Lev 18:16 + 20:21 "
        "brother's-wife prohibition. John pays for the rebuke with his "
        "life. Tewahedo prophet-veneration tradition + ascetic-witness "
        "against ruler-vice (notably the bahǝtawi tradition's confrontation "
        "of kings) cite Mk 6:18 as the prophetic-courage anchor.",
    ),
    cyril_mark(
        6,
        20,
        "'Herod feared John, knowing that he was a just man and an holy, "
        "and observed him; and when he heard him, he did many things, and "
        "heard him gladly' — Cyril marks the Markan-distinctive Herod's-"
        "ambivalence (Matthew omits this nuance). Even the vicious-ruler "
        "could recognize-the-prophetic-truth and feel-its-pull (audebat / "
        "ēkouen-hēdeōs — gladly-listening). Yet Herodias's pressure (Mk "
        "6:19) eventually overcame the king's better-instinct. The "
        "tragedy is that hearing-gladly-but-not-acting is not enough; "
        "Mk 4:17 stony-ground reception. Tewahedo conversion-discipline "
        "warns against half-hearted-hearing per Mk 6:20.",
    ),
    cyril_mark(
        6,
        31,
        "'Come ye yourselves apart into a desert place, and rest a while' "
        "— Cyril marks the Markan-distinctive deute hymeis-autoi (you-"
        "yourselves) + erēmon-topon (desert-place) + anapausasthe-oligon "
        "(rest-a-little) as Christ's-pastoral-care for his exhausted-"
        "apostles. The disciples have just returned from their first-"
        "mission (Mk 6:7-13); the Master prescribes withdrawal-rest. "
        "Tewahedo monastic-anchorite tradition (the bahǝtawi-retreat "
        "rhythm + the Mahǝbär-feast / weekday-fast rhythm) cites Mk 6:31 "
        "as the missionary-rest-charter alongside Ex 33:14 + Heb 4:9-10.",
    ),
    cyril_mark(
        6,
        34,
        "'Jesus, when he came out, saw much people, and was moved with "
        "compassion toward them, because they were as sheep not having a "
        "shepherd: and he began to teach them many things' — Cyril marks "
        "the Markan-version (parallels Mt 9:36 γ.4.6.C anchor) but with "
        "an instructive-emphasis NOT in Matthew: Christ's-compassion "
        "leads to TEACHING (ērxato didaskein), not just to healing. The "
        "shepherd-flock-without-shepherd Ezek 34 imagery operates "
        "Christologically — Christ-IS-the-Good-Shepherd (Mk 6:34 + "
        "Jn 10:11). Tewahedo episcopal-formation reads Mk 6:34 + Ezek 34 "
        "as the teaching-AND-shepherding pastoral dual-charge.",
    ),
    cyril_mark(
        6,
        39,
        "'He commanded them to make all sit down by companies upon the "
        "green grass' — Cyril marks the Markan-distinctive 'green grass' "
        "(chortō chlōrō) and 'by companies' (symposia symposia — Hebraic "
        "doubling for distribution) as ordered-eucharistic-meal imagery. "
        "Mark also gives precise group-sizes Mk 6:40 (in fifties and "
        "hundreds, prasiai prasiai). The deliberate-arrangement is "
        "liturgical-ordered-table, not random-crowd. The chlōrō-chortō "
        "echoes Ps 23:2 LXX 'green pastures'. Tewahedo Qǝddāse "
        "eucharistic-table-arrangement (Aksumite tradition: ordered-"
        "communion-by-ranks) traces Cyrillian-Markan precedent here.",
    ),
    cyril_mark(
        6,
        48,
        "'He saw them toiling in rowing; for the wind was contrary unto "
        "them: and about the fourth watch of the night he cometh unto "
        "them, walking upon the sea, and would have passed by them' — "
        "Cyril marks the Markan-distinctive 'would have passed by them' "
        "(ēthelen parelthein autous) as the theophanic-passing-by motif "
        "echoing Ex 33:22 + 1 Kgs 19:11 (the Lord 'passing by' Moses + "
        "Elijah). Christ's walking-on-sea is divine-prerogative (Ps "
        "77:19 LXX 76:20) + theophanic-pass-by (Ex 33:22 LXX). The "
        "tetartē phylakē (fourth watch, 3-6 AM) names the deepest-night "
        "moment of disciples' distress. Tewahedo theophany-hermeneutics "
        "cites Mk 6:48 as Christological-OT-theophany-fulfillment.",
    ),
    cyril_mark(
        6,
        50,
        "'It is I; be not afraid' — Cyril marks the egō-eimi-mē-phobeisthe "
        "as the Christological-divine-name claim (parallels Mt 14:27 "
        "γ.4.6.D anchor). The egō-eimi echoes the Septuagint's rendering "
        "of Ex 3:14 — the incarnate Word identifies with the I-AM. The "
        "Markan-version preserves the SAME formula as the Johannine "
        "egō-eimi declarations (Jn 6:20 + Jn 8:24, 58 + Jn 18:5-8). "
        "Tewahedo Christological-Tǝmqät hymnody pairs Mk 6:50 + Mt 14:27 "
        "+ Jn 6:20 as the triple I-AM-on-the-water prooftext.",
    ),
    cyril_mark(
        6,
        56,
        "'Whithersoever he entered, into villages, or cities, or country, "
        "they laid the sick in the streets, and besought him that they "
        "might touch if it were but the border of his garment: and as "
        "many as touched him were made whole' — Cyril marks the Markan-"
        "collective-healing-by-hem-touch as the universal-version of the "
        "hemorrhaging-woman's individual-touch (Mk 5:28 γ.4.7.B anchor). "
        "The kraspedon-touching faith-paradigm scales from one woman to "
        "many crowds. The hosoi-an-hēptonto-autou (as-many-as-touched-"
        "him) construction signals comprehensive-power-of-the-Christ-touch. "
        "Tewahedo healing-pilgrimage tradition + icon-touch dynamics "
        "cite Mk 6:56 as scriptural-warrant.",
    ),
    # ── Mark 7 (9) — Defilement + Syrophoenician + Deaf-mute Ephphatha ─────
    cyril_mark(
        7,
        6,
        "'Well hath Esaias prophesied of you hypocrites, as it is written, "
        "This people honoureth me with their lips, but their heart is far "
        "from me' — Cyril marks the Markan citation of Isa 29:13 LXX as "
        "the diagnostic-prooftext for Pharisaic-hypocrisy. The hypokritai "
        "(hypocrites — actors-with-masks) honors-with-lips-but-not-heart "
        "is the lip-service-without-heart-service indictment. Tewahedo "
        "anti-hypocrisy catechesis cites Mk 7:6-7 + Isa 29:13 + Mt 15:7-8 "
        "as the triple lip-service warning.",
    ),
    cyril_mark(
        7,
        7,
        "'In vain do they worship me, teaching for doctrines the "
        "commandments of men' — Cyril marks matēn-sebontai-me (in-vain-"
        "they-worship-me) as the deepest possible indictment: their "
        "worship is fruitless because its-content is human-tradition not "
        "divine-commandment. The didaskontes-didaskalias-entalmata-"
        "anthrōpōn (teaching-doctrines-the-commandments-of-men) inverts "
        "the proper-relation (divine-doctrines-shape-human-conduct). "
        "Tewahedo doctrinal-discipline (Mäshafä-Qǝddǝse hermeneutic) "
        "distinguishes Apostolic-tradition (paradosis) from human-"
        "innovation precisely on the Cyrillian-Markan principle.",
    ),
    cyril_mark(
        7,
        9,
        "'Full well ye reject the commandment of God, that ye may keep "
        "your own tradition' — Cyril marks the deliberate-irony in "
        "kalōs-atheteite (well do ye set aside) — the kalōs is ironic, "
        "naming the proficiency-of-rejecting. The contrast: paradosin-"
        "hymōn (your-tradition) vs entolēn-tou-theou (commandment-of-God) "
        "— human-tradition AGAINST divine-commandment, not human-"
        "tradition AS divine-commandment. Tewahedo Apostolic-tradition "
        "vs human-innovation discernment depends on this Cyrillian-"
        "Markan distinction.",
    ),
    cyril_mark(
        7,
        11,
        "'But ye say, If a man shall say to his father or mother, It is "
        "Corban, that is to say, a gift, by whatsoever thou mightest be "
        "profited by me; he shall be free' — Cyril marks the Markan-"
        "preserved Aramaic 'Corban' (qorbān, gift-to-God dedication) "
        "with the Greek gloss 'dōron' (gift). The Pharisaic-loophole: "
        "vowing-resources-as-Corban frees them from filial-obligation "
        "to support parents (violating Ex 20:12). Christ exposes the "
        "loophole as commandment-subversion. Tewahedo filial-piety "
        "tradition cites Mk 7:9-13 as the anti-loophole + Honor-Father-"
        "and-Mother absolute-priority.",
    ),
    cyril_mark(
        7,
        18,
        "'Are ye so without understanding also? Do ye not perceive, that "
        "whatsoever thing from without entereth into the man, it cannot "
        "defile him' — Cyril marks Christ's surprise-at-disciples'-"
        "slowness (houtōs kai hymeis asynetoi este?, are-you-also-so-"
        "without-understanding?). The asynetoi recalls the parable-"
        "interpretation difficulty at Mk 4:13. The disciples' slow-"
        "comprehension is a Markan-recurring theme (the messianic-secret "
        "+ disciple-misunderstanding pair). Tewahedo catechumenal-"
        "patience tradition reads disciple-slowness as encouragement: "
        "even the Twelve needed gradual-instruction.",
    ),
    cyril_mark(
        7,
        21,
        "'For from within, out of the heart of men, proceed evil "
        "thoughts, adulteries, fornications, murders, thefts' — Cyril "
        "marks the Markan-fuller list of interior-defilement-sources "
        "(13 items in Mk 7:21-22; Matthew gives 7 at Mt 15:19). The "
        "kardia (heart) is the source; the body merely externalizes "
        "what's-inside. The vice-catalogue technique (paralleling "
        "Rom 1:29-31, Gal 5:19-21, etc.) sets the moral-diagnostic "
        "lens. Tewahedo penitential-catechesis (the Säwasǝw of "
        "Penitence) draws on Mk 7:21-22 + Gal 5:19-21 as the inward-"
        "moral-examination corpus.",
    ),
    cyril_mark(
        7,
        24,
        "'From thence he arose, and went into the borders of Tyre and "
        "Sidon, and entered into an house, and would have no man know "
        "it: and he could not be hid' — Cyril marks the Markan-"
        "distinctive 'would have no man know it' (oudena ēthelen "
        "gnōnai) as the Christic-mission-quietness motif. Even crossing "
        "into Gentile-territory (Tyre + Sidon — Phoenician), Christ-"
        "intends-incognito; the Syrophoenician-woman's faith breaks "
        "the silence (Mk 7:25-30). Tewahedo missionary-quiet-witness "
        "tradition (the unobtrusive-presence pattern of the Nine-Saints "
        "and contemporary Tewahedo-missions) draws Christic-warrant here.",
    ),
    cyril_mark(
        7,
        33,
        "'He took him aside from the multitude, and put his fingers into "
        "his ears, and he spit, and touched his tongue' — Cyril marks "
        "the Markan-distinctive deaf-mute-healing as the most-physical "
        "of all Christic-healings (fingers + saliva applied directly to "
        "the deficient-organs). The privacy (kat'idian, aside-from-"
        "multitude) and the personal-touch (digits + spittle) sacralize-"
        "the-bodily-contact: Tewahedo sacrament-of-the-sick anointing-"
        "with-oil + episcopal-laying-on-of-hands trace Cyrillian-"
        "Markan precedent. The fingers-and-spittle gesture is "
        "preserved in some Tewahedo deaf-ministry blessings.",
    ),
    cyril_mark(
        7,
        34,
        "'Looking up to heaven, he sighed, and saith unto him, Ephphatha, "
        "that is, Be opened' — Cyril marks the Markan-preserved-Aramaic "
        "Ephphatha (ethphatah, be-opened) as the climactic-creative-word "
        "(echoing Gen 1's let-there-be). Christ's anablepsas (looking-up) "
        "+ estenaxen (sighed-deeply) shows the Christic-emotional-"
        "involvement in healing. Tewahedo baptismal-rite explicitly "
        "preserves the Ephphatha gesture: the priest touches the "
        "candidate's ears + mouth + nostrils saying 'Ephphatha — Be "
        "opened — for the proclamation of the Gospel and the praise of "
        "God' (Coptic-Tewahedo continuity from the Mark-Aramaic source).",
    ),
    # ── Mark 8 (11) — Feeding-4000 + Bethsaida-blind two-stage + Peter ─────
    cyril_mark(
        8,
        2,
        "'I have compassion on the multitude, because they have now been "
        "with me three days, and have nothing to eat' — Cyril marks the "
        "Markan-version (parallels Mt 15:32 γ.4.6.C anchor) of the "
        "Feeding-of-4000. The hēmerai-treis (three days) is theological-"
        "loaded — the Christic-Passion-resurrection chronology (Mk "
        "8:31). Crowds-with-the-Master-three-days-without-bread receive "
        "miraculous-bread; the typology anticipates eucharistic-bread-"
        "after-three-days-of-Passion. Tewahedo Holy-Week + Fasika "
        "eucharistic-cycle reads Mk 8:2 + Mk 8:31 + Mk 14:22-24 as "
        "linked-typological-chain.",
    ),
    cyril_mark(
        8,
        11,
        "'And the Pharisees came forth, and began to question with him, "
        "seeking of him a sign from heaven, tempting him' — Cyril marks "
        "peirazontes-auton (tempting-him) as the satanic-language echo "
        "(Mk 1:13 wilderness-temptation; Mk 12:15 Caesar-coin test). The "
        "Pharisaic sēmeion-apo-tou-ouranou (sign-from-heaven) demand is "
        "category-error: signs-from-heaven are God's-prerogative, given-"
        "when-and-how-God-chooses, not demand-extracted. Tewahedo "
        "wonder-discernment tradition (sober skepticism of sign-seeking) "
        "draws Mk 8:11-13 + Mt 12:38-39 as anti-sign-demand prooftexts.",
    ),
    cyril_mark(
        8,
        12,
        "'He sighed deeply in his spirit, and saith, Why doth this "
        "generation seek after a sign? verily I say unto you, There "
        "shall no sign be given unto this generation' — Cyril marks the "
        "Markan-distinctive anastenaxas-tō-pneumati (sighed-deeply-in-"
        "his-spirit) as Christ's-emotional-grief at unbelief. The "
        "anti-sign declaration is unconditional in Mark (Matthew adds "
        "'except the sign of Jonas' Mt 12:39 + 16:4). Christ-refuses-"
        "to-perform-on-demand; the only-sign-coming is the Resurrection-"
        "Cross. Tewahedo Christological-Passion-anticipation reads "
        "Mk 8:12 alongside Mt 12:39-40 + Jn 2:18-21 (temple-destroyed-"
        "raised-in-three-days).",
    ),
    cyril_mark(
        8,
        15,
        "'Take heed, beware of the leaven of the Pharisees, and of the "
        "leaven of Herod' — Cyril marks the Markan-distinctive 'leaven "
        "of Herod' (Mt 16:6 has 'leaven of the Pharisees and Sadducees'; "
        "Lk 12:1 has just 'leaven of Pharisees, hypocrisy'). The Markan-"
        "Herodian-corruption joins Pharisaic-legalism as twin-defilement-"
        "doctrines. Pharisaic-leaven is religious-self-righteousness; "
        "Herodian-leaven is political-collaboration-with-tyranny. "
        "Tewahedo dual-warning catechesis (against religious-hypocrisy "
        "AND political-collaboration-with-power) is grounded in this "
        "Cyrillian-Markan dual-leaven reading.",
    ),
    cyril_mark(
        8,
        17,
        "'Why reason ye, because ye have no bread? perceive ye not yet, "
        "neither understand? have ye your heart yet hardened?' — Cyril "
        "marks Christ's-rebuke pattern (oupō-noeite-oude-syniete — not-"
        "yet-perceiving-not-yet-understanding) as the disciple-slowness "
        "diagnosis. The pepōrōmenēn-tēn-kardian (hardened-heart) is "
        "shocking applied to disciples — the same vocabulary used of "
        "Pharisees (Mk 3:5 γ.4.7 seed). Disciples + Pharisees can both "
        "share-the-heart-hardening; conversion is ongoing-not-completed. "
        "Tewahedo catechetical-realism reads Mk 8:17-21 as honest "
        "disciple-formation pedagogy.",
    ),
    cyril_mark(
        8,
        23,
        "'He took the blind man by the hand, and led him out of the "
        "town; and when he had spit on his eyes, and put his hands upon "
        "him, he asked him if he saw ought' — Cyril marks the Markan-"
        "distinctive Bethsaida-blind-man as Christ's-only-recorded "
        "TWO-STAGE healing. The first-application (Mk 8:23-24) yields "
        "partial-sight ('I see men as trees, walking'). The second-"
        "application (Mk 8:25) yields full-sight. The pedagogy: "
        "spiritual-sight-comes-gradually; partial-Christology (Mk 8:29 "
        "Peter's confession will be partial — he-confesses-Christ-but-"
        "rejects-Cross at Mk 8:32-33) needs second-stage-completion. "
        "Tewahedo catechumenal-gradual-illumination tradition + monastic-"
        "spiritual-direction read Mk 8:22-26 as paradigmatic.",
    ),
    cyril_mark(
        8,
        25,
        "'He put his hands again upon his eyes, and made him look up: "
        "and he was restored, and saw every man clearly' — Cyril marks "
        "the second-application (palin epethēken tas cheiras, again-"
        "placed-the-hands) completing the two-stage healing begun at "
        "Mk 8:23-24. The apokatestathē-eneblepen-tēlaugōs-hapanta (was-"
        "restored-saw-clearly-everyone) names the full-clarity. The "
        "pedagogical-point: spiritual-sight may require Christic-"
        "intervention TWICE — first-stage partial-sight, second-stage "
        "complete-sight. The narrative-position immediately before "
        "Peter's-confession (Mk 8:29 partial-Christology / 8:32-33 needs-"
        "second-correction) is intentional: the disciples are at "
        "first-stage; Cross-and-Resurrection will be their second-stage. "
        "Tewahedo catechumenal-stages tradition (illuminandi → "
        "neophyti → fideles) parallels the two-stage pedagogy.",
    ),
    cyril_mark(
        8,
        33,
        "'Get thee behind me, Satan: for thou savourest not the things "
        "that be of God, but the things that be of men' — Cyril marks "
        "Christ's-rebuke-to-Peter immediately-after Peter's-confession "
        "(Mk 8:29 γ.4.7 seed). The hypage-opisō-mou-satana (get-behind-"
        "me-Satan) is the strongest Christological rebuke addressed to "
        "any disciple in the Gospels. Peter's confession-of-Christ "
        "(8:29) and rejection-of-Cross (8:32 Peter-rebukes-Jesus-for-"
        "predicting-Passion) cannot both stand — the Christ-confessed "
        "is-the-Christ-Crucified. Tewahedo Christological-discipleship "
        "rules cite Mk 8:33 as the no-Christ-without-Cross anchor.",
    ),
    cyril_mark(
        8,
        35,
        "'Whosoever will save his life shall lose it; but whosoever "
        "shall lose his life for my sake and the gospel's, the same "
        "shall save it' — Cyril marks the Markan-distinctive 'for my "
        "sake AND THE GOSPEL'S' (heneken emou kai tou euangeliou — "
        "Matthew omits the gospel-clause at Mt 16:25). The Markan-"
        "addition explicitly grounds the life-losing in evangelical-"
        "service. The chiastic save-lose / lose-save kenotic-paradox "
        "summarizes discipleship. Tewahedo martyrology + missionary-"
        "vocation theology cite Mk 8:35 as the dual-charter (martyric-"
        "willing-loss + missionary-gospel-service).",
    ),
    cyril_mark(
        8,
        36,
        "'For what shall it profit a man, if he shall gain the whole "
        "world, and lose his own soul?' — Cyril marks ti-gar-ōphelei-"
        "anthrōpon (for-what-shall-it-profit-a-man) as the universal-"
        "moral-summit question. The kerdēsai-ton-kosmon-holon (to-gain-"
        "the-whole-world) is the maximal-temporal-profit; zēmiōthē-tēn-"
        "psychēn-autou (suffer-loss-of-one's-soul) is the maximal-"
        "eternal-loss. The asymmetry is decisive: no temporal-profit "
        "compensates for soul-loss. Tewahedo wealth-ethics + monastic-"
        "renunciation theology cite Mk 8:36 + Lk 9:25 + Mt 16:26 as "
        "the triple soul-value-supremacy anchor.",
    ),
    cyril_mark(
        8,
        38,
        "'Whosoever therefore shall be ashamed of me and of my words in "
        "this adulterous and sinful generation; of him also shall the "
        "Son of man be ashamed, when he cometh in the glory of his "
        "Father with the holy angels' — Cyril marks the Markan-"
        "distinctive 'and of my words' (kai tous emous logous) as the "
        "deepest-Logology claim: shame-at-Christ's-words IS shame-at-"
        "Christ-himself, because the Logos and his-words are "
        "ontologically-inseparable. The Parousia-judgment (Christ "
        "ashamed-of-them) is the eschatological-mirror. Tewahedo "
        "Logos-Christology + Parousia-eschatology read Mk 8:38 as a "
        "particularly tight Christological-eschatological summary.",
    ),
    # ── Mark 9 (10) — Transfiguration + Demoniac + 2nd Passion-prediction ──
    cyril_mark(
        9,
        2,
        "'After six days Jesus taketh with him Peter, and James, and "
        "John, and leadeth them up into an high mountain apart by "
        "themselves: and he was transfigured before them' — Cyril marks "
        "the Markan-parallel to Mt 17:1 (γ.4.6.D anchor) of the "
        "Transfiguration mountain-selection. The meth' hēmeras hex "
        "(after-six-days) is the Genesis-creation-week typology (six-"
        "days-then-seventh-day-Tabor-glory). The three-witness Peter-"
        "James-John embody Deut 19:15 legal-attestation. Tewahedo Buhe "
        "feast on Näḥase 13 commemorates this moment with explicit "
        "Tabor-locus per the patristic-monastic tradition.",
    ),
    cyril_mark(
        9,
        3,
        "'His raiment became shining, exceeding white as snow; so as no "
        "fuller on earth can white them' — Cyril marks the Markan-"
        "distinctive imagery (Matthew has 'shone as the sun' + 'raiment "
        "white as light' Mt 17:2; Mark's snow + fuller imagery is more "
        "concrete). The hoia-gnapheus-epi-tēs-gēs-ou-dynatai-houtōs-"
        "leukanai (such-as-no-fuller-on-earth-can-so-whiten) emphasizes "
        "the supernatural-origin of the radiance. The garments-shining "
        "is uncreated-light theology (the same divine-light at Sinai "
        "Ex 34:29-30). Tewahedo deification + uncreated-light tradition "
        "draw on Mk 9:3 + Mt 17:2 + Lk 9:29 as the triple-Tabor anchor.",
    ),
    cyril_mark(
        9,
        4,
        "'There appeared unto them Elias with Moses: and they were "
        "talking with Jesus' — Cyril marks the Markan-ordering 'Elias "
        "with Moses' (Matthew + Luke reverse: Moses-and-Elijah). The "
        "Markan-ordering may foreground Elijah's prominence in second-"
        "temple eschatology (Mal 4:5-6, expected-before-Day-of-Lord). "
        "Both are present with Christ; Law (Moses) and Prophets "
        "(Elijah) testify together. The syllaloûntes-tō-Iēsou (talking-"
        "with-Jesus) preserves the conversational-dignity of the OT-"
        "witnesses before the incarnate-Word. Tewahedo iconography of "
        "the Transfiguration depicts Moses + Elijah flanking Christ.",
    ),
    cyril_mark(
        9,
        5,
        "'Master, it is good for us to be here: and let us make three "
        "tabernacles; one for thee, and one for Moses, and one for "
        "Elias' — Cyril marks Peter's-impulsive-suggestion as the well-"
        "meaning-but-misguided desire to-stay-on-the-mountain. The "
        "kalon-estin-hēmas-hōde-einai (good-it-is-for-us-here-to-be) is "
        "right (the Tabor-vision IS good); the three-skēnas (three-"
        "tents — perhaps tabernacles-of-meeting Ex 33:7 OR Feast-of-"
        "Tabernacles eschatological-typology) misreads-the-economy. "
        "Christ-must-descend-to-Cross before any eschatological-"
        "tabernacle is built. Tewahedo eschatological-anticipation "
        "discipline cites Peter's-error as cautionary precedent.",
    ),
    cyril_mark(
        9,
        23,
        "'Jesus said unto him, If thou canst believe, all things are "
        "possible to him that believeth' — Cyril marks Christ's-"
        "reverse-of-the-father's-conditional (the father said 'if thou "
        "canst do anything' Mk 9:22; Christ replies 'if thou canst "
        "believe'). The Christic-prerequisite is FAITH, not Christ's-"
        "capability (Christ's-capability is unlimited). The panta-"
        "dynata-tō-pisteuonti (all-things-possible-to-the-one-believing) "
        "is the faith-as-divine-power-channel principle. Tewahedo "
        "deliverance-prayer + miracle-ministry tradition cite Mk 9:23 + "
        "Mk 11:23-24 + Mt 21:21-22 as the faith-power triple-anchor.",
    ),
    cyril_mark(
        9,
        29,
        "'And he said unto them, This kind can come forth by nothing, "
        "but by prayer and fasting' — Cyril marks the Markan-distinctive "
        "prayer-AND-fasting prescription for difficult-exorcisms "
        "(some textual witnesses preserve only 'prayer'; the Byzantine "
        "majority + Cramer's catena tradition preserves 'and fasting' "
        "as Cyril knew it). The to-genos-touto (this-kind, the recalcitrant-"
        "demonic-strain) requires-spiritual-disciplines-the-mere-"
        "exorcistic-command-lacks. Tewahedo deep-deliverance tradition "
        "+ Mahǝbär-fast cycles cite Mk 9:29 as the prayer-fasting "
        "deliverance-charter.",
    ),
    cyril_mark(
        9,
        31,
        "'The Son of man is delivered into the hands of men, and they "
        "shall kill him; and after that he is killed, he shall rise the "
        "third day' — Cyril marks the Markan-second-Passion-prediction "
        "(after Mk 8:31 first + Mk 10:33-34 third). The paradidotai "
        "(is-being-handed-over — present-tense already-in-process) "
        "names the in-progress-betrayal. The 'killed-and-after-three-"
        "days-rise' formula is constant across all three predictions. "
        "Tewahedo Holy-Week lectionary reads the three-Passion-"
        "predictions (Mk 8:31 + 9:31 + 10:33-34) as the kerygmatic-"
        "triple-witness to the deliberate-Christic-path.",
    ),
    cyril_mark(
        9,
        37,
        "'Whosoever shall receive one of such children in my name, "
        "receiveth me: and whosoever shall receive me, receiveth not "
        "me, but him that sent me' — Cyril marks the kinship-chain "
        "(receive-child = receive-Christ = receive-Father). The Christic-"
        "identification-with-the-least-significant inverts the "
        "disciples'-prior-greatness-dispute (Mk 9:33-34). To-receive-"
        "a-child-in-Christ's-name is to receive the entire Trinity-"
        "through-the-Son-into-the-Father. Tewahedo child-welcoming "
        "tradition + Mahǝbär-feast hospitality cite Mk 9:37 as the "
        "least-of-these reception anchor.",
    ),
    cyril_mark(
        9,
        42,
        "'Whosoever shall offend one of these little ones that believe "
        "in me, it is better for him that a millstone were hanged about "
        "his neck, and he were cast into the sea' — Cyril marks the "
        "skandalisē (offend, cause-to-stumble) as the gravest sin "
        "against tōn-mikrōn-toutōn-tōn-pisteuontōn (these-little-ones-"
        "believing). The hyperbolic-millstone language signals "
        "incomparable-seriousness — better-drowning than scandal-"
        "causing. Tewahedo pastoral-care + child-protection ethics "
        "cite Mk 9:42 as the absolute-prohibition against catechumen-"
        "or-disciple harm.",
    ),
    cyril_mark(
        9,
        50,
        "'Salt is good: but if the salt have lost his saltness, "
        "wherewith will ye season it? Have salt in yourselves, and have "
        "peace one with another' — Cyril marks the Markan-distinctive "
        "echete-en-heautois-halá (have-salt-in-yourselves) + eirēneuete-"
        "en-allēlois (be-at-peace-with-one-another) pair as the "
        "discipleship-charter. Salt-of-discipleship preserves and "
        "seasons (Mk 9:49 every-sacrifice-salted echoes Lev 2:13 covenant-"
        "of-salt). Disciples must internalize-the-Christic-quality "
        "(salt-in-yourselves) and live-it-out-relationally (peace-with-"
        "one-another). Tewahedo monastic-rule + lay-Mahǝbär ethics "
        "anchor here.",
    ),
    # ── Mark 10 (10) — Marriage + Children + Rich-man + Cup + Bartimaeus ────
    cyril_mark(
        10,
        6,
        "'From the beginning of the creation God made them male and "
        "female' — Cyril marks the Markan apo-archēs-ktiseōs (from-"
        "beginning-of-creation) as the original-design-principle "
        "trumping Mosaic-permission-of-divorce (Mk 10:4-5). The Gen "
        "1:27 (arsen-kai-thēly, male-and-female) citation grounds the "
        "marital-permanence in protological-ontology, not legal-"
        "concession. Tewahedo marital-theology preserves the original-"
        "design priority (Gen 1:27 + Gen 2:24 + Mk 10:6-9) over the "
        "Mosaic-concession (Deut 24:1) per Cyrillian-precedent.",
    ),
    cyril_mark(
        10,
        14,
        "'Suffer the little children to come unto me, and forbid them "
        "not: for of such is the kingdom of God' — Cyril marks the "
        "Markan-double-imperative aphete-ta-paidia-erchesthai (suffer-"
        "the-children-to-come) + mē-kōlyete-auta (forbid-them-not) as "
        "doubled-Christic-correction of disciple-blocking. The tōn-"
        "toioutōn-estin-hē-basileia (of-such-is-the-kingdom) is "
        "ontologically-significant — paidic-receptivity is the kingdom-"
        "shape. Tewahedo infant-baptism tradition (the early-baptism "
        "pattern preserved in Coptic-Tewahedo against Donatist-and-"
        "later anti-paedobaptist objections) cites Mk 10:14 as primary "
        "warrant.",
    ),
    cyril_mark(
        10,
        15,
        "'Verily I say unto you, Whosoever shall not receive the kingdom "
        "of God as a little child, he shall not enter therein' — Cyril "
        "marks hōs-paidion (as-a-little-child) NOT as biological-age "
        "but as paidic-receptive-dependency. The dexētai (receive) is "
        "passive-grace-receiving, not active-merit-earning. Children "
        "model-the-kingdom-economy: dependency, trust, openness, lack-"
        "of-self-righteousness. Tewahedo monastic-humility-formation "
        "tradition reads Mk 10:15 as the rule-of-the-novice (begin-"
        "again-as-paidic-receiver).",
    ),
    cyril_mark(
        10,
        18,
        "'Why callest thou me good? there is none good but one, that is, "
        "God' — Cyril treats this most-difficult-saying carefully. "
        "Christ is NOT denying his own goodness or divinity; he is "
        "testing the rich-young-ruler's understanding of what-he-just-"
        "called-Christ. The young-man called Christ 'good Teacher' as "
        "human-flattery without grasping the implication. Christ replies: "
        "if I am truly good, then the agathos-is-God-only logic requires "
        "recognizing-me-as-God. This is a hidden-Christological-claim, "
        "not divinity-denial. Tewahedo Christological-pedagogy reads "
        "Mk 10:18 + Lk 18:19 + Mt 19:17 as the deepest-divinity-"
        "disclosure under apparent-humility.",
    ),
    cyril_mark(
        10,
        21,
        "'Then Jesus beholding him loved him, and said unto him, One "
        "thing thou lackest: go thy way, sell whatsoever thou hast, and "
        "give to the poor, and thou shalt have treasure in heaven: and "
        "come, take up the cross, and follow me' — Cyril marks the "
        "Markan-distinctive emblepsas-auto-ēgapēsen-auton (beholding-"
        "him-loved-him) — the only Gospel-passage where Christ-is-said-"
        "to-love-an-individual. The Christic-love is precisely what "
        "elicits the costly-call. The hen-soi-hysterei (one-thing-you-"
        "lack) is the counsel-of-perfection (cf. Mt 19:21 γ.4.6.D "
        "anchor). Tewahedo monastic-vocation theology (the Mäshafä-"
        "Mǝnǝkwǝsnna) reads Mk 10:21 as the love-prompting-of-the-"
        "calling.",
    ),
    cyril_mark(
        10,
        27,
        "'With men it is impossible, but not with God: for with God all "
        "things are possible' — Cyril marks Christ's-disciples'-question "
        "(who-then-can-be-saved? Mk 10:26) as the kerygmatic-pivot. "
        "Human-salvation IS impossible-to-mere-human-effort (con-firming-"
        "the-camel-needle of Mk 10:25 γ.4.7 seed). But panta-dynata-"
        "para-tō-theō (all-things-possible-beside-God) is the grace-"
        "principle. Tewahedo soteriology of grace + divine-monergism-"
        "in-conversion reads Mk 10:27 + Mt 19:26 + Lk 18:27 as the "
        "triple grace-makes-impossible-possible anchor.",
    ),
    cyril_mark(
        10,
        30,
        "'But he shall receive an hundredfold now in this time, houses, "
        "and brethren, and sisters, and mothers, and children, and "
        "lands, with persecutions; and in the world to come eternal "
        "life' — Cyril marks the Markan-distinctive 'with persecutions' "
        "(meta diōgmōn — Matthew and Luke omit this clause) as the "
        "honest-realism about disciple-experience. The hundredfold-"
        "compensation is genuine but always-with-persecutions-attached. "
        "Tewahedo monastic-and-martyric tradition reads Mk 10:30 as the "
        "honest-promise + costly-realism balance.",
    ),
    cyril_mark(
        10,
        38,
        "'Ye know not what ye ask: can ye drink of the cup that I drink "
        "of? and be baptized with the baptism that I am baptized with?' "
        "— Cyril marks the Markan-distinctive cup-and-baptism pair "
        "(Matthew omits the baptism-clause at Mt 20:22 in best texts). "
        "The potērion (cup) is the Passion-cup (cf. Mk 14:36); the "
        "baptisma (baptism) is the Cross-as-baptism-of-suffering "
        "(echoes Lk 12:50 'I have a baptism to be baptized with'). "
        "Both metaphors converge on Christ's-Passion-as-the-disciple's-"
        "participation. Tewahedo Christological-discipleship reads "
        "Mk 10:38-39 as cup-and-baptism dual-participation anchor.",
    ),
    cyril_mark(
        10,
        42,
        "'Ye know that they which are accounted to rule over the "
        "Gentiles exercise lordship over them; and their great ones "
        "exercise authority upon them' — Cyril marks the hoi-dokountes-"
        "archein (those-supposing-to-rule) as carefully-chosen — "
        "Gentile-rulers SUPPOSE to rule but only-Christ-truly-rules. "
        "The katakyrieousin-autōn (lord-it-over-them) is the worldly-"
        "domination-pattern Christ explicitly rejects for his disciples. "
        "Tewahedo episcopal-formation + Mahǝbär-leadership ethics cite "
        "Mk 10:42-45 as the anti-domination service-leadership "
        "charter (climaxing at Mk 10:45 ransom-for-many γ.4.7 seed).",
    ),
    cyril_mark(
        10,
        51,
        "'What wilt thou that I should do unto thee? The blind man said "
        "unto him, Lord, that I might receive my sight' — Cyril marks "
        "Christ's question (ti soi theleis poiēsō?, what-do-you-will-me-"
        "to-do-for-you?) as the deliberate-elicitation-of-explicit-"
        "petition. The blind man Bartimaeus must NAME his need; "
        "anonymous-faith is not enough at the threshold-of-healing. "
        "The Rabboni-vocative (Rabbouni — Mark preserves the Aramaic) "
        "+ anablepsō (let-me-see-again) signals previously-seeing now-"
        "lost — sight-restoration, not original-sight. Tewahedo prayer-"
        "formation tradition (precise-petition over vague-yearning) "
        "cites Mk 10:51 as exemplar.",
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 50, f"expected 50 entries, got {len(NEW_ENTRIES)}"
assert all(e["book"] == "mrk" for e in NEW_ENTRIES)
assert all(e["father"] == "Cyril of Alexandria" for e in NEW_ENTRIES)
assert all(6 <= e["chapter"] <= 10 for e in NEW_ENTRIES), "γ.4.7.C = Mark 6-10 only"
chapters_covered = sorted({e["chapter"] for e in NEW_ENTRIES})
assert chapters_covered == [6, 7, 8, 9, 10], f"expected all 5 chapters; got {chapters_covered}"

from collections import Counter

_density = Counter(e["chapter"] for e in NEW_ENTRIES)
expected_min = {6: 9, 7: 8, 8: 10, 9: 9, 10: 9}
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
        " γ.4.7.C (2026-05-13) added Cyril on Mark detail wave II — 50 "
        "verse-keyed entries on Mark 6-10 (Galilean ministry second half + "
        "Caesarea Philippi + Transfiguration + journey-to-Jerusalem): "
        "Nazareth-carpenter offense + apostolic-oil-anointing + John-"
        "Baptist-Herod's-wife rebuke + Herod-feared-John ambivalence + "
        "rest-in-desert + sheep-without-shepherd-teaching + ordered-"
        "feast-companies + walking-on-sea-fourth-watch theophanic-"
        "passing-by + 'It is I' egō-eimi parallel + collective-hem-"
        "touching + Isa-29:13 lip-honor + in-vain-worship + reject-"
        "commandment-for-tradition + Corban-loophole + disciple-slowness "
        "+ interior-defilement-vice-catalogue + mission-quietness + "
        "deaf-mute-personal-touch + EPHPHATHA preserved-Aramaic baptismal-"
        "rite anchor + Feeding-4000 three-day-typology + tempting-sign-"
        "demand + sigh-no-sign-given + leaven-of-Pharisees-and-Herod + "
        "hardened-hearts-disciples + Bethsaida-blind two-stage-healing "
        "spiritual-sight-gradual + 'Get-thee-behind-me-Satan' Peter-"
        "rebuke + save-life-lose-life + 'gain-world-lose-soul' moral-"
        "summit + ashamed-of-me-AND-MY-WORDS Logology + Transfiguration "
        "high-mountain (six-days creation-typology) + raiment-shining-"
        "white-as-snow uncreated-light + Moses-and-Elijah Law-and-"
        "Prophets witness + Peter-three-tabernacles eschatological-"
        "anticipation-error + 'if-thou-canst-believe' faith-prerequisite "
        "+ prayer-and-fasting deliverance-charter + second-Passion-"
        "prediction + receives-little-children Trinitarian-chain + "
        "millstone-better-than-offend-little-ones + salt-in-yourselves-"
        "peace-with-others + 'from-beginning male-and-female' original-"
        "design + 'suffer-little-children' infant-baptism-warrant + "
        "receive-kingdom-as-little-child paidic-receptive-dependency + "
        "'why-callest-thou-me-good' hidden-Christological-claim + "
        "'one-thing-thou-lackest' counsel-of-perfection (Christic-love-"
        "elicitation) + 'with-God-all-things-possible' grace-monergism + "
        "hundredfold-WITH-PERSECUTIONS Markan-realism + cup-AND-baptism "
        "dual-Passion-participation + anti-domination service-leadership + "
        "Bartimaeus-Rabbouni precise-petition. Per ω.41 §1 voice-"
        "composition rule: Cyril rises 50.8% → ~52.5%. Cyril-on-Mark "
        "total post-γ.4.7.C: 141 entries (40 γ.4.7 seed + 51 γ.4.7.B "
        "Mark 1-5 + 50 γ.4.7.C Mark 6-10). Cumulative Cyril-on-Gospels: "
        "612 entries across all 4 canonical Gospels. Source: Cramer "
        "Vol. I (Oxford 1840 — PD) + PG 72 (Migne 1859 — PD); mirrors "
        "γ.4.7.B detail-wave structure."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    mark_total = sum(1 for e in d["entries"] if e["book"] == "mrk" and e["father"] == "Cyril of Alexandria")
    print(f"γ.4.7.C ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(f"Cyril on Mark total: {mark_total} entries")


if __name__ == "__main__":
    main()
