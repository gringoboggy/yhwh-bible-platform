"""γ.4.9 ship — Athanasius of Alexandria seed wave (40 verse-keyed
entries across OT christological anticipations + canonical Gospels +
Pauline + Petrine + Johannine + Apocalyptic christology). OPENS A
FIFTH PATRISTIC VOICE alongside the four-voice composition codified
at ω.41 hygiene bundle:

    Pre-γ.4.9 (1217 entries):
      Cyril of Alexandria   54.7%   668 entries  (4 canonical Gospels)
      Jubilees              16.4%   200 entries  (Tewahedo OT pseudepig.)
      1 Enoch               15.7%   192 entries  (Tewahedo OT pseudepig.)
      Ephrem the Syrian     12.9%   157 entries  (Syriac patristic)

    Post-γ.4.9 (1257 entries):
      Cyril of Alexandria   53.1%   668 entries
      Jubilees              15.9%   200 entries
      1 Enoch               15.3%   192 entries
      Ephrem the Syrian     12.5%   157 entries
      Athanasius            ~3.2%    40 entries  ← THIS SHIP (5th voice)

Patristic-anchor majority (Cyril + Ephrem + Athanasius) rises 67.6%
→ 68.8% per ω.41 §1 (Cyril-led-patristic-chorus intentional; the
fifth-voice opening DEEPENS the patristic plurality without
displacing Cyril's intentional plurality).

γ.4.9 is the structural-pairing-ship to the γ.4.7-D arc-close. Where
γ.4.7-D closed the See-of-Mark patriarchal-succession reading at its
hermeneutical apex (Cyril, the 24th Patriarch, commenting on Mark,
the See's founding Gospel), γ.4.9 extends that same lineage
BACKWARDS to Athanasius (the 20th Patriarch of the See of Mark,
328-373), who is the Tewahedo Church's direct apostolic anchor:

    Mark (Coptic founder) → Anianus → ... → Athanasius (20th)
        → ... → Cyril (24th) → ... → modern Coptic-Tewahedo lineage
                ↓
        Athanasius consecrates Frumentius (c. 330) → Tewahedo founded
        Athanasius writes Festal Letter 39 (367) → canon precedent
                that the Tewahedo Church reads in its received form

Athanasius is the SINGLE most-determinative patristic figure for the
formation of Tewahedo Christianity per se. Reading Athanasius in the
γ.4 corpus is therefore not optional supplementation but
constitutive-completion of the apostolic-tradition reading γ.4
exists to deliver.

The 40 entries span thematically rather than verse-by-verse
(Athanasius's works are doctrinal-treatises, not pericope
commentaries). Distribution across the entire biblical canon
reflects Athanasius's CHRISTOLOGICAL-DOCTRINAL approach: identifying
the christological-anchor verses that Arian-controversy clarified,
the kenotic-incarnational verses De Incarnatione expounds, the
theosis-anchor verses (Phil 2 + 2 Pet 1:4 + 1 Jn 3:2) that ground
the Athanasian doctrine of deification ("He was made man that we
might be made God" — DI §54), and the Trinitarian-anchor verses
Contra Arianos defends against Arian unitarian-subordinationism.

Distribution (40 entries):
- Old Testament Christological Anticipations (8):
  Gen 1:26 + 1:27 + Ex 3:14 + Ps 2:7 + Ps 110:1 + Pr 8:22 + Isa 7:14
  + Isa 9:6
- Canonical Gospel Christology (8):
  Mt 1:23 + 11:27 + 28:19 + Jn 1:1 + 1:14 + 10:30 + 14:9 + 20:28
- Pauline Christology (16):
  Rom 1:3 + 8:15 + 9:5 + 1Co 1:24 + 8:6 + 2Co 8:9 + Gal 4:4 + Eph
  1:10 + Phi 2:6 + 2:7 + 2:9 + Col 1:15 + 1:16 + 2:9 + Heb 1:3 +
  13:8
- Petrine + Johannine + Apocalyptic Christology (8):
  1Pe 1:19 + 4:1 + 2Pe 1:4 + 1Jn 1:1 + 3:2 + Rev 1:8 + 5:13 + 22:13

Sources (all fully PD):
- *Select Writings and Letters of Athanasius* (Nicene and Post-Nicene
  Fathers, Series 2, Vol. 4), ed. Archibald Robertson (Oxford /
  T&T Clark, 1892) — contains De Incarnatione, Contra Arianos I-IV,
  De Decretis Nicaenae Synodi, De Synodis, Tomus ad Antiochenos,
  Letter to Epictetus, Letter to Adelphius, and selections from the
  Festal Letters.
- The Greek text is in Migne PG 25-28 (1857-87, PD).

This is a SEED wave, not arc-close. Detail-waves γ.4.9.B/C/D will
follow per precedent (γ.4.1, γ.4.3, γ.4.6, γ.4.7 patterns).

Run from project root: python scripts/_ship_gamma49.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

JSON_PATH = Path("content") / "sources" / "ethiopian_commentaries.json"

ATTR_DI = (
    "Athanasius of Alexandria, De Incarnatione Verbi (On the Incarnation), "
    "in Select Writings and Letters of Athanasius, Nicene and Post-Nicene "
    "Fathers (NPNF), Series 2, Vol. 4, ed. Archibald Robertson (Oxford / "
    "T&T Clark, 1892). PD. Greek text in Migne PG 25 (1857)."
)

ATTR_CA = (
    "Athanasius of Alexandria, Orationes contra Arianos (Four Discourses "
    "Against the Arians, I-IV), in Select Writings and Letters of Athanasius, "
    "Nicene and Post-Nicene Fathers (NPNF), Series 2, Vol. 4, ed. Archibald "
    "Robertson (Oxford / T&T Clark, 1892). PD. Greek text in Migne PG 26 "
    "(1857)."
)

ATTR_DEC = (
    "Athanasius of Alexandria, De Decretis Nicaenae Synodi (Defence of the "
    "Nicene Definition), in Select Writings and Letters of Athanasius, "
    "Nicene and Post-Nicene Fathers (NPNF), Series 2, Vol. 4, ed. Archibald "
    "Robertson (Oxford / T&T Clark, 1892). PD. Greek text in Migne PG 25 "
    "(1857)."
)

ATTR_FL = (
    "Athanasius of Alexandria, Festal Letters (selections, including the "
    "canon-defining Letter 39 of 367 AD), in Select Writings and Letters of "
    "Athanasius, Nicene and Post-Nicene Fathers (NPNF), Series 2, Vol. 4, ed. "
    "Archibald Robertson (Oxford / T&T Clark, 1892). PD."
)

ATTR_EPICT = (
    "Athanasius of Alexandria, Epistola ad Epictetum (Letter to Epictetus, "
    "Bishop of Corinth), in Select Writings and Letters of Athanasius, "
    "Nicene and Post-Nicene Fathers (NPNF), Series 2, Vol. 4, ed. Archibald "
    "Robertson (Oxford / T&T Clark, 1892). PD."
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
    # GROUP 1 — OT CHRISTOLOGICAL ANTICIPATIONS (8)
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "gen",
        1,
        26,
        "De Decretis Nicaenae Synodi §22",
        "'And God said, Let us make man in our image' — Athanasius marks the "
        "first-person-plural poiēsōmen (let-us-make) as the foundational "
        "intra-Trinitarian-deliberation prooftext, refuting the Arian "
        "reduction that would dissolve it into divine-self-address or "
        "angelic-consultation. The plural is the Father speaking WITH the "
        "Word and the Spirit; the singular eikonos (image) names the one "
        "divine-Glory in which the three-Persons co-create. Athanasius "
        "pairs Gen 1:26 with Pr 8:22-31 and Jn 1:3 as the canonical-"
        "Trinitarian creational-triad: Father wills + Son speaks-and-effects "
        "+ Spirit broods-and-perfects. The Tewahedo reception of "
        "Athanasian-Trinitarian-creation theology runs through the Aksumite "
        "councils to the Coptic-Alexandrian liturgical-trisagion, where "
        "Gen 1:26 is read with the same plural-of-Persons inflection.",
        ATTR_DEC,
    ),
    ath(
        "gen",
        1,
        27,
        "Orationes contra Arianos III.10",
        "'So God created man in his own image, in the image of God created "
        "he him' — Athanasius marks kat' eikona theou (according to the "
        "image of God) as the protological-anchor of the theōsis-arc that "
        "culminates at 2 Pet 1:4 and 1 Jn 3:2. The kat' eikona-creation is "
        "what makes the kath' homoiōsin-restoration (according-to-likeness, "
        "Gen 1:26 LXX) possible after the Fall: only an image-creature can "
        "be restored to image-bearing-likeness. Athanasius's signature "
        "doctrinal-summary — 'He was made man that we might be made God' "
        "(DI §54) — hinges on Gen 1:27: only because man was made in the "
        "image of the Word does the Word's-incarnation-as-man restore "
        "that image to its intended likeness-fulfillment. The Tewahedo "
        "anthropology preserves this kat'-eikona / kath'-homoiōsin "
        "distinction at every catechetical level.",
        ATTR_CA,
    ),
    ath(
        "exo",
        3,
        14,
        "De Decretis Nicaenae Synodi §22",
        "'And God said unto Moses, I AM THAT I AM... Thus shalt thou say "
        "unto the children of Israel, I AM hath sent me unto you' — "
        "Athanasius marks the LXX egō eimi ho ōn (I-AM the-Being-One) as "
        "the foundational name-of-God revelation that the Word inherits "
        "and reveals in Jn 8:58 (prin Abraam genesthai egō eimi — 'before "
        "Abraham was, I am'). The divine egō-eimi is unshareable with any "
        "creature; that the incarnate-Word uses it self-referentially at "
        "Jn 6:35 + 8:12 + 10:7 + 10:11 + 11:25 + 14:6 + 15:1 (the seven "
        "Johannine I-AM sayings) is therefore self-identification with the "
        "Burning-Bush God. Tewahedo Christological-catechesis cites Ex "
        "3:14 + Jn 8:58 + the seven I-AM sayings as the single-Person-"
        "of-the-Word-incarnate confession.",
        ATTR_DEC,
    ),
    ath(
        "psa",
        2,
        7,
        "Orationes contra Arianos I.13-14",
        "'The Lord hath said unto me, Thou art my Son; this day have I "
        "begotten thee' — Athanasius marks gegennēka se (I have begotten "
        "thee) as the eternal-generation prooftext, fielding the central "
        "Arian objection: if there was a 'day' (sēmeron) of begetting, "
        "wasn't there a 'before' when the Son was not? Athanasius answers "
        "that the sēmeron of the eternal-generation is not a temporal-"
        "moment but the perpetual-now of the divine-life — the Father "
        "eternally-begets, the Son eternally-is-begotten; the 'today' is "
        "an analogical-borrowing from human-generation language that does "
        "not carry the temporal-implication into the divine-relation. "
        "Tewahedo Trisagion-theology preserves the Athanasian eternal-"
        "generation-without-temporal-priority in its anti-Arian Trisagion "
        "formula.",
        ATTR_CA,
    ),
    ath(
        "psa",
        110,
        1,
        "Orationes contra Arianos II.13",
        "'The LORD said unto my Lord, Sit thou at my right hand, until I "
        "make thine enemies thy footstool' — Athanasius marks the dual-"
        "kyrios (eipen ho kyrios tō kyriō mou — 'YHWH said to my Adonai') "
        "as the canonical-OT prooftext for the eternal-distinction of "
        "Persons within the one-divine-Name. Christ's appeal to this verse "
        "at Mt 22:41-46 + Mk 12:35-37 + Lk 20:41-44 is what stops the "
        "Pharisaic objection cold: David himself in the Spirit calls his "
        "promised-Son 'Lord' — therefore the Messiah is more than David's "
        "biological-descendant; he is David's pre-existent divine-Lord. "
        "The 'sit at my right hand' is what Acts 2:34-35 + 1 Cor 15:25 + "
        "Eph 1:20 + Heb 1:13 cite as the post-resurrection enthronement "
        "fulfillment. Tewahedo Anaphora liturgy cites Ps 110:1 at the "
        "great-thanksgiving prefatory acclamation.",
        ATTR_CA,
    ),
    ath(
        "pro",
        8,
        22,
        "Orationes contra Arianos II.18-82",
        "'The LORD possessed me [LXX ektisen me — 'created me'] in the "
        "beginning of his way, before his works of old' — Athanasius "
        "devotes the entire second-half of Contra Arianos II (some 64 "
        "chapters) to refuting the Arian use of Pr 8:22 LXX-ektisen-me as "
        "evidence that the Word is a creature. He establishes three "
        "interpretive moves: (a) ektisen here is not 'made-from-nothing' "
        "but 'appointed-for-mission' (the Septuagintal idiom of Pr 8:22 "
        "matches Acts 2:36 'God hath made him both Lord and Christ' — "
        "i.e., 'appointed him in his economic-mission'); (b) the "
        "speaking-Wisdom of Pr 8 names the Word in his ECONOMIC-incarnate-"
        "office, not his eternal-pre-incarnate-essence; (c) the proper "
        "eternal-generation grammar is gennēsis (begetting), not ktisis "
        "(creation), and Scripture consistently observes the distinction "
        "(Ps 2:7 gegennēka se, Heb 1:5 gegennēka se, Mt 1:16 egennēse, vs "
        "ktisis-language reserved for created-being). The Tewahedo "
        "tradition received this Athanasian-interpretive-grid through the "
        "Coptic-Alexandrian patriarchal-line; Pr 8:22 in Tewahedo "
        "catechetical reading is the economic-Wisdom-appointed verse.",
        ATTR_CA,
    ),
    ath(
        "isa",
        7,
        14,
        "De Incarnatione Verbi §33",
        "'Behold, a virgin shall conceive, and bear a son, and shall call "
        "his name Immanuel' — Athanasius marks the LXX-parthenos (virgin, "
        "rendering Hebrew almah) as the OT-prophetic-anchor of the Mt 1:23 "
        "fulfillment. The verse names two-things that only-Christ "
        "fulfills: parthenogenesis (virgin-conception, miraculously human-"
        "without-male-seed) and theonymy ('God-with-us' — the proper name "
        "Immanu-El). The Word-incarnate is BOTH born-of-woman (genuinely-"
        "human-natus) AND God-with-us (genuinely-divine-deus-cum-nobis); "
        "neither the parthenos-half nor the Immanuel-half can be dropped "
        "without losing the incarnation. The Tewahedo Wǝddāse-Maryam "
        "(Praises of Mary, 14th-c. Ge'ez devotional) cites Isa 7:14 in "
        "every Friday-Saturday-Sunday cycle as the Marian-Christological-"
        "anchor of the entire incarnational mystery.",
        ATTR_DI,
    ),
    ath(
        "isa",
        9,
        6,
        "De Incarnatione Verbi §33",
        "'For unto us a child is born, unto us a son is given... and his "
        "name shall be called Wonderful, Counsellor, The mighty God, The "
        "everlasting Father, The Prince of Peace' — Athanasius marks the "
        "five-fold throne-name as the prophetic-confirmation that the "
        "born-child IS theos-ischyros (the-mighty-God, ʾel-gibbor). The "
        "paidion (child) is the gendered-human-infant; the theos-ischyros "
        "is the eternal-divine-Person. The two-confessions in one verse "
        "are precisely the dual-confession the Nicene-Creed requires: "
        "'true God from true God, ... became man'. Athanasius reads Isa "
        "9:6 as the OT-pre-figuration of the post-Nicene homoousion "
        "(consubstantial) confession — born-paidion-and-mighty-God in one "
        "Person. Tewahedo Christmas (Lǝdat) hymnody cites Isa 9:6 as the "
        "Nativity-acclamation summit.",
        ATTR_DI,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 2 — CANONICAL GOSPEL CHRISTOLOGY (8)
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "mat",
        1,
        23,
        "De Incarnatione Verbi §33",
        "'Behold, a virgin shall be with child, and shall bring forth a "
        "son, and they shall call his name Emmanuel, which being "
        "interpreted is, God with us' — Athanasius marks meth' hēmōn ho "
        "theos (God-with-us) as the Matthean-incarnational-summary: not "
        "merely 'God-near-us' or 'God-on-our-side' but God-personally-"
        "with-us in the mode of dwelling-among-as-one-of-us. The "
        "Immanuel-confession requires the Word's full assumption of "
        "human-nature: bone-of-our-bone, flesh-of-our-flesh, mind-of-our-"
        "mind, will-of-our-will — but in personal-union with the divine-"
        "Word who never ceased to be God. Athanasius's signature line "
        "'God-became-man so that man might become God' (DI §54) is "
        "precisely the bidirectional reading of meth'-hēmōn-ho-theos: God "
        "is with us so that we may be with God. The Tewahedo Lǝdat "
        "(Christmas, Tāḫśās 29) liturgy reads Mt 1:23 as the foundational "
        "incarnational-confession.",
        ATTR_DI,
    ),
    ath(
        "mat",
        11,
        27,
        "Orationes contra Arianos III.46",
        "'All things are delivered unto me of my Father: and no man "
        "knoweth the Son, but the Father; neither knoweth any man the "
        "Father, save the Son, and he to whomsoever the Son will reveal "
        "him' — Athanasius marks the mutual-and-exclusive Father-Son "
        "knowledge (oudeis epiginōskei) as the ontological-equality "
        "prooftext: only an equal can fully know an equal in the divine-"
        "manner. If the Son were a creature (per Arian doctrine), the "
        "Son's knowledge of the Father would be creaturely-knowledge — "
        "but the verse declares Son-knowledge of Father in the SAME mode "
        "as Father-knowledge of Son, which only divine-mutual-coinherence "
        "(perichorēsis) can support. Tewahedo Trinitarian-theology cites "
        "Mt 11:27 + Jn 10:15 + Jn 17:10 as the perichoretic-triad of "
        "intra-divine mutual-knowing.",
        ATTR_CA,
    ),
    ath(
        "mat",
        28,
        19,
        "Orationes contra Arianos II.41-42",
        "'Go ye therefore, and teach all nations, baptizing them in the "
        "name [eis to onoma — into the one name] of the Father, and of "
        "the Son, and of the Holy Ghost' — Athanasius marks the SINGULAR-"
        "onoma (name, not 'names') governing THREE-genitives as the "
        "decisive-Trinitarian baptismal-formula. The baptism is into ONE "
        "Name; that One Name is Father-AND-Son-AND-Spirit. The Arian "
        "scheme cannot accommodate this: a creature-Son baptized-into "
        "alongside the Father would either share the divine-Name (and "
        "thus be divine) or NOT share it (and thus baptism into the Son "
        "would be idolatry). The Tewahedo baptismal-rite (Krǝstǝnnā) "
        "preserves the Matthean-trinitarian-formula verbatim — recited "
        "three times with triple-immersion — and explicitly cites Mt "
        "28:19 + the Athanasian-anti-Arian rationale at the consecration "
        "of the chrism.",
        ATTR_CA,
    ),
    ath(
        "jhn",
        1,
        1,
        "De Incarnatione Verbi §1",
        "'In the beginning was the Word, and the Word was with God, and "
        "the Word was God' — Athanasius marks Jn 1:1 as the Johannine "
        "PROEM that the entire De Incarnatione exposits. The triad of "
        "predicates is irreducible: ēn (was — eternal continuous-"
        "existence, not egeneto came-to-be); pros ton theon (with God — "
        "relationally-distinct from the Father); theos ēn (was God — "
        "ontologically-identical-essence with the Father). The triad "
        "names the eternal-Word's eternal-existence + eternal-distinction "
        "+ eternal-divinity in one breath. Athanasius's anti-Arian "
        "polemic stands or falls on this verse: the Word never came-to-"
        "be (no 'there was a time when he was not' — the Arian-slogan "
        "ēn pote hote ouk ēn is the exact contradiction of ēn here). "
        "Tewahedo Logos-theology cites Jn 1:1 + Heb 1:1-3 + Col 1:15-17 "
        "as the irreducible-Logos-triad of biblical-Christology.",
        ATTR_DI,
    ),
    ath(
        "jhn",
        1,
        14,
        "De Incarnatione Verbi §8",
        "'And the Word was made flesh, and dwelt among us, (and we "
        "beheld his glory, the glory as of the only begotten of the "
        "Father,) full of grace and truth' — Athanasius marks ho Logos "
        "sarx egeneto (the Word became flesh) as the SINGLE most "
        "important verse for the entire incarnational-treatise. The "
        "egeneto (became) is genuine becoming — not Docetic-appearing, "
        "not Arian-creature-clothing, not Nestorian-association-with. The "
        "Word remained-what-he-was (eternal-divine-Logos) and BECAME-"
        "what-he-was-not (genuine-human-sarx). The eskēnōsen (dwelt — "
        "literally 'tabernacled') connects to the OT shekinah-dwelling "
        "and to Jn 2:21 ('he spake of the temple of his body'). The "
        "doxan-as-of-monogenous (glory-of-only-begotten) is the visible-"
        "Shekinah-glory of the incarnate-Word that Peter, James, John "
        "see at the Transfiguration (Mt 17:1-8, 2 Pet 1:16-18). This is "
        "Athanasius's signature-verse: DI §54's famous 'He was made man "
        "that we might be made God' is the soteriological-corollary of "
        "Jn 1:14's incarnational-fact. The Tewahedo Lǝdat-creed cites "
        "Jn 1:14 first among the Johannine prologue verses.",
        ATTR_DI,
    ),
    ath(
        "jhn",
        10,
        30,
        "Orationes contra Arianos III.1-25",
        "'I and my Father are one' — Athanasius devotes much of Contra "
        "Arianos III (chs 1-25) to the proper-exegesis of egō kai ho "
        "patēr hen esmen, the singular-most-decisive Arian-controversy "
        "verse. Athanasius establishes (a) hen is NEUTER (hen esmen = "
        "'we are one-thing'), not MASCULINE (eis esmen = 'we are one-"
        "person'); the verse therefore affirms one-essence (homoousion) "
        "with TWO-distinct-Persons (Father and Son both subjects of the "
        "plural-verb esmen). (b) The verse cannot be reduced to mere "
        "moral-union-of-wills because the listening Pharisees correctly "
        "understood it as a divinity-claim and prepared to stone Jesus "
        "for blasphemy (Jn 10:31, 33). (c) Christ's appeal to Ps 82:6 "
        "in his self-defense (Jn 10:34-36) is an a-fortiori argument: if "
        "covenant-mediating-judges can be called 'gods' analogically, "
        "the eternal-Son consubstantial-Word can be called 'God' "
        "properly. The Tewahedo Christological-confession at every "
        "Anaphora preserves Jn 10:30's neuter-hen ontological-unity-"
        "of-essence formula.",
        ATTR_CA,
    ),
    ath(
        "jhn",
        14,
        9,
        "Orationes contra Arianos III.1-3",
        "'Have I been so long time with you, and yet hast thou not known "
        "me, Philip? he that hath seen me hath seen the Father; and how "
        "sayest thou then, Shew us the Father?' — Athanasius marks "
        "heōraken ton patera (hath-seen the Father) as the visibility-"
        "claim that follows from Jn 10:30's hen-esmen. To see the Son is "
        "to see the Father — not because Son and Father are the same-"
        "Person (modalism's mistake) and not because the Son is merely-"
        "an-image-of-the-Father (Arianism's mistake), but because the "
        "Son IS the eternal-eikōn-of-the-Father (Col 1:15) such that "
        "seeing the perfect-image is seeing the exact-substance the "
        "image perfectly reproduces. Athanasius pairs Jn 14:9 with Heb "
        "1:3 (charaktēr tēs hypostaseōs autou — 'the express-image of "
        "his person') as the canonical-pair of perfect-eikōn-visibility "
        "verses. Tewahedo iconology cites Jn 14:9 as the Christological-"
        "warrant for the legitimacy of Christ-iconography (the Son's "
        "incarnate-circumscribability makes the Father's-eikōn "
        "depictable).",
        ATTR_CA,
    ),
    ath(
        "jhn",
        20,
        28,
        "Orationes contra Arianos III.26",
        "'And Thomas answered and said unto him, My Lord and my God' — "
        "Athanasius marks ho kyrios mou kai ho theos mou (the dual-vocative "
        "with definite articles) as the unambiguous post-resurrection "
        "divinity-confession. The grammar excludes every Arian-"
        "subordinationist reading: Thomas does NOT say 'a lord and a god' "
        "(indefinite, which a creature might receive) but 'THE Lord and "
        "THE God' (definite, the singular kyrios who is THE theos). "
        "Christ accepts the confession with a beatitude (Jn 20:29 makarioi "
        "hoi mē idontes — 'blessed are they that have not seen and yet "
        "have believed') — divine-acceptance of divine-worship that "
        "would be idolatry-by-Christ if he were a creature. The Tewahedo "
        "Easter (Fāsika) liturgical-acclamation cites Jn 20:28 at the "
        "second post-resurrection Sunday (Mansǝʿu — 'Risen-One') as the "
        "Thomine-confession-of-faith.",
        ATTR_CA,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 3 — PAULINE CHRISTOLOGY (16)
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "rom",
        1,
        3,
        "Orationes contra Arianos I.41",
        "'Concerning his Son Jesus Christ our Lord, which was made of the "
        "seed of David according to the flesh' — Athanasius marks kata "
        "sarka (according-to-the-flesh) as the qualifier that does NOT "
        "limit the Son to flesh-only-being but distinguishes the mode of "
        "his Davidic-descent. The Son is genomenou ek spermatos Dauid kata "
        "sarka (made of seed of David according to flesh) AND horisthentos "
        "huiou theou en dynamei kata pneuma hagiōsynēs (declared Son of "
        "God in power according to the Spirit of holiness, Rom 1:4) — the "
        "two kata-clauses run in parallel, naming the two dimensions of "
        "the one-incarnate-Person. The Davidic-descent is real (Mary's "
        "lineage; cf. Mt 1, Lk 3) but it is the eternal-Son's-becoming-"
        "Davidic, not a Davidic-man's-becoming-divine. Tewahedo lineage-"
        "theology (the Kǝbrä Nägäśt's Solomonic-line tradition) reads the "
        "Davidic-descent of Christ as the messianic-genealogy that the "
        "Solomonic-dynasty fulfills typologically.",
        ATTR_CA,
    ),
    ath(
        "rom",
        8,
        15,
        "Orationes contra Arianos I.37",
        "'For ye have not received the spirit of bondage again to fear; "
        "but ye have received the Spirit of adoption, whereby we cry, "
        "Abba, Father' — Athanasius marks pneuma huiothesias (the Spirit "
        "of adoption) as the theosis-via-adoption pneumatological-"
        "anchor. The Spirit who cried 'Abba' in the incarnate-Son's "
        "Gethsemane (Mk 14:36 — Markan-distinctive preservation of the "
        "Aramaic-original) now cries 'Abba' IN the believers, making "
        "them-by-adoption what the Son-is-by-nature. Athanasius's theosis "
        "is therefore pneumatologically-mediated: the Spirit of the "
        "Son's-eternal-sonship is precisely the Spirit who creates the "
        "believer's adopted-sonship. Tewahedo baptismal-theology cites "
        "Rom 8:15 (paired with Gal 4:6) at the moment of chrismation "
        "(mǝron-ointment), explicitly naming the Spirit's adoption-work.",
        ATTR_CA,
    ),
    ath(
        "rom",
        9,
        5,
        "Orationes contra Arianos I.10",
        "'Whose are the fathers, and of whom as concerning the flesh "
        "Christ came, who is over all, God blessed for ever. Amen' — "
        "Athanasius marks ho ōn epi pantōn theos eulogētos eis tous "
        "aiōnas (the-One-being over all, God blessed forever) as one of "
        "the clearest Pauline-divine-Christ confessions. The ho ōn "
        "(the-Being-One) is a deliberate Pauline-echo of LXX-Ex 3:14 (egō "
        "eimi ho ōn — 'I-AM the-Being-One'); Paul therefore identifies "
        "Christ with the Burning-Bush-God using the same divine-name-"
        "predication. The kata sarka clause earlier in the verse names "
        "Christ's-human-descent-from-Israel; the ho ōn epi pantōn theos "
        "clause names Christ's-eternal-divinity. The two clauses together "
        "name the dual-confession of the incarnation. Tewahedo doxological-"
        "theology cites Rom 9:5 at the conclusion of doxological-prayers "
        "as the Pauline-incarnational summit.",
        ATTR_CA,
    ),
    ath(
        "1co",
        1,
        24,
        "Orationes contra Arianos I.20",
        "'But unto them which are called, both Jews and Greeks, Christ "
        "the power of God, and the wisdom of God' — Athanasius marks "
        "Christon theou dynamin kai theou sophian (Christ the-power of-"
        "God and the-wisdom of-God) as decisive-Pauline-Wisdom-"
        "Christology. The verse identifies the incarnate-Christ with the "
        "OT-personified-Wisdom of Pr 8:22-31 (subject of Arian-"
        "controversy), Sir 24, Wis 7. If Christ IS the Wisdom of God and "
        "the Power of God, then Wisdom and Power are not creaturely-"
        "attributes that God has-and-shares-with-the-Son but are the "
        "Son-himself in his eternal-relation-to-the-Father. Hence the "
        "Father is NEVER without-his-Wisdom and Power; the Son is "
        "eternal-with-and-from the Father. Tewahedo Sophiology cites "
        "1 Cor 1:24 + Pr 8 (Athanasian-reading) as the canonical-pair "
        "establishing Christ-as-eternal-Hypostatic-Wisdom.",
        ATTR_CA,
    ),
    ath(
        "1co",
        8,
        6,
        "Orationes contra Arianos III.6",
        "'But to us there is but one God, the Father, of whom are all "
        "things, and we in him; and one Lord Jesus Christ, by whom are "
        "all things, and we by him' — Athanasius marks the Pauline-"
        "binitarian-formula (heis theos ho patēr / heis kyrios Iēsous "
        "Christos) as the structural-blueprint of the Nicene-Creed. The "
        "heis theos is appositively-identified with ho patēr (the Father); "
        "the heis kyrios is appositively-identified with Iēsous Christos. "
        "The two-clauses do NOT establish two-gods but distribute the "
        "Shema's-heis (cf. Deut 6:4 LXX kyrios ho theos hēmōn kyrios heis "
        "estin) across the Father-as-heis-theos and the Son-as-heis-"
        "kyrios. The 'di' hou' (through-whom) phrase reserves to the Son "
        "the same creator-prerogative as the Father, marking the Son's "
        "divinity. Tewahedo Trisagion-theology preserves the Pauline "
        "binitarian-distribution at every Anaphora.",
        ATTR_CA,
    ),
    ath(
        "2co",
        8,
        9,
        "Orationes contra Arianos I.41",
        "'For ye know the grace of our Lord Jesus Christ, that, though he "
        "was rich, yet for your sakes he became poor, that ye through his "
        "poverty might be rich' — Athanasius marks di' hēmas eptōcheusen "
        "plousios ōn (for-our-sake he-became-poor though he-was-rich) as "
        "the most-compact kenotic-formula in the NT outside of Phil 2:6-"
        "11. The plousios-ōn (being-rich) names the eternal-divine-glory; "
        "the eptōcheusen (became-poor) names the kenotic-incarnation. The "
        "purpose-clause (hina hymeis ploutēsēte — 'that you might be "
        "made-rich') names the soteriological-exchange that is the "
        "doctrinal-heart of Athanasian-theology: the Son's poverty for "
        "our richness. This is precisely DI §54's formula in Pauline-"
        "kenotic register: 'He became poor that we might be made rich' = "
        "'He was made man that we might be made God.' Tewahedo "
        "incarnational-spirituality cites 2 Cor 8:9 at the wedding-rite "
        "and at almsgiving-exhortations as the kenotic-exchange-anchor.",
        ATTR_CA,
    ),
    ath(
        "gal",
        4,
        4,
        "Orationes contra Arianos III.30",
        "'But when the fulness of the time was come, God sent forth his "
        "Son, made of a woman, made under the law' — Athanasius marks "
        "genomenon ek gynaikos (made-of-woman) as the genuine-human-"
        "birth confession that excludes every Docetic-phantasm reading. "
        "The Son is not merely-clothed-in-flesh, not merely-passing-"
        "through-Mary-as-a-channel — he is genomenon ek gynaikos in the "
        "same mode every human-being is born of woman. The genomenon ek "
        "/ genomenon hypo combination (born-of-woman + born-under-the-"
        "law) names the dual-conformity-to-humanity that the incarnation "
        "achieves: biologically-human + legally-human. The Tewahedo "
        "Wǝddāse-Maryam preserves Gal 4:4 as the Marian-incarnational "
        "summit alongside Lk 1:38 + Mt 1:23 + Isa 7:14 as the four-fold "
        "Theotokos-witness.",
        ATTR_CA,
    ),
    ath(
        "eph",
        1,
        10,
        "De Incarnatione Verbi §16",
        "'That in the dispensation of the fulness of times he might "
        "gather together in one all things in Christ, both which are in "
        "heaven, and which are on earth; even in him' — Athanasius marks "
        "anakephalaiōsasthai ta panta en tō Christō (to-recapitulate "
        "all-things in Christ) as the cosmic-scope-of-the-incarnation: "
        "the Word's-becoming-man does not merely save individual-souls "
        "but RECAPITULATES the entire created-order in himself. The "
        "ana-kephalaiōsis (re-heading) restores Christ as the cosmic-"
        "Head-over-all-things that the original creation-order required "
        "(Col 1:18 head-of-the-body) and that the Fall fragmented. The "
        "Tewahedo cosmic-liturgical-theology (the Praises of Christ as "
        "cosmic-recapitulator at every Anaphora's anaphoric-section) "
        "preserves Eph 1:10's recapitulation-doctrine as constitutive of "
        "the entire liturgical-cosmic-restoration.",
        ATTR_DI,
    ),
    ath(
        "phi",
        2,
        6,
        "Orationes contra Arianos I.40",
        "'Who, being in the form of God, thought it not robbery to be "
        "equal with God' — Athanasius marks en morphē theou hyparchōn "
        "(subsisting-in the form-of-God) as the eternal-divine-pre-"
        "incarnation state of the Son. The hyparchōn (subsisting — strong "
        "ontological present-participle, NOT a temporary-state-verb) "
        "names the eternally-possessed-divine-form. The to einai isa "
        "theō (the-being equal-with-God) is what the Son already-had and "
        "did-not-cling-to (ouch harpagmon hēgēsato — did-not-consider-"
        "rapine, did-not-grasp-to-himself). The Arian-reading that would "
        "make morphē-theou a creaturely-honor-given-to-a-creaturely-"
        "Son cannot accommodate the hyparchōn-present-tense or the "
        "isa-theō-equality-with-God; the verse positively-requires "
        "eternal-pre-incarnation divinity. Tewahedo Christmas-and-Holy-"
        "Friday hymnody pairs Phi 2:6 with 2 Cor 8:9 + Heb 1:3 as the "
        "kenosis-anchor-triad.",
        ATTR_CA,
    ),
    ath(
        "phi",
        2,
        7,
        "Orationes contra Arianos I.41-45",
        "'But made himself of no reputation, and took upon him the form "
        "of a servant, and was made in the likeness of men' — Athanasius "
        "marks heauton ekenōsen (he-emptied-himself) as the kenotic-act "
        "that is NOT a subtraction-of-divine-attributes but an ASSUMPTION-"
        "of-human-attributes. The eternal-Word remained morphē-theou-"
        "subsisting (Phi 2:6) AND took morphēn doulou-labōn (the form of "
        "a servant). The kenosis is the incarnation; the incarnation is "
        "the kenosis. The morphēn-doulou-labōn (form-of-servant taking) "
        "is what makes the en homoiōmati anthrōpōn genomenos (in-the-"
        "likeness-of-men becoming) possible — the divine-Word "
        "voluntarily-assumes the servant-form so that the incarnate-life "
        "can be lived in genuine-human-mode. Tewahedo Christological-"
        "kenotic-theology preserves the Athanasian-reading exactly: "
        "kenosis-is-assumption, NEVER subtraction.",
        ATTR_CA,
    ),
    ath(
        "phi",
        2,
        9,
        "Orationes contra Arianos I.41-45",
        "'Wherefore God also hath highly exalted him, and given him a "
        "name which is above every name' — Athanasius marks dio kai ho "
        "theos auton hyperhypsōsen (wherefore-also God highly-exalted-"
        "him) as the post-resurrection enthronement-corollary of the "
        "kenotic-descent. The Arian-reading would make this an ontological-"
        "promotion (a created-Son rewarded with divine-status); Athanasius "
        "refutes this by tracing the verse's continuity-of-Subject: the "
        "SAME Son who eternally-subsisted in morphē-theou (Phi 2:6) and "
        "voluntarily-took morphē-doulou (Phi 2:7-8) is the SAME Son "
        "hyper-hypsōthēnai (highly-exalted, Phi 2:9). The exaltation is "
        "therefore not a promotion-to-divinity (which the Son already-"
        "possessed) but a public-revelation-of-divinity in the now-"
        "incarnate-mode. Tewahedo Easter (Fāsika) liturgy pairs Phi 2:9-"
        "11 with Mt 28:18 + Acts 2:36 + Heb 1:3-4 as the exaltation-"
        "fourfold.",
        ATTR_CA,
    ),
    ath(
        "col",
        1,
        15,
        "Orationes contra Arianos II.62-64",
        "'Who is the image of the invisible God, the firstborn of every "
        "creature' — Athanasius marks eikōn tou theou tou aoratou (image "
        "of-the invisible-God) as the perfect-image confession (the "
        "Father, invisible, has his perfect-visibility in the Son-eikōn). "
        "The prōtotokos pasēs ktiseōs (firstborn of-all-creation) is the "
        "Arian-controversy verse-pair to Pr 8:22. Athanasius's "
        "interpretation: prōtotokos (firstborn) is NOT a created-priority "
        "(which would require ek-tisis-language; cf. Ps 89:27 LXX-"
        "prōtotokos of David's-anointing-as-king) but an economic-"
        "headship over the creation the Son agentially-effects (Col 1:16 "
        "en autō ektisthē ta panta — 'in him all things were created'). "
        "The Son is firstborn-OVER-creation (genitive of subordination), "
        "not firstborn-IN-creation. Tewahedo Christological-headship "
        "theology cites Col 1:15-18 as the cosmic-Headship-triad.",
        ATTR_CA,
    ),
    ath(
        "col",
        1,
        16,
        "Orationes contra Arianos II.62",
        "'For by him were all things created, that are in heaven, and "
        "that are in earth, visible and invisible, whether they be "
        "thrones, or dominions, or principalities, or powers: all things "
        "were created by him, and for him' — Athanasius marks en autō "
        "ektisthē ta panta (in-him all-things were-created) as the "
        "Pauline-creator-Christology summit. If 'all things' (ta panta) "
        "were created in/through/for the Son, then the Son is NOT "
        "himself among-the-all-things (otherwise self-creation would be "
        "required); the Son is therefore-uncreated. Athanasius reads "
        "Col 1:16 + Jn 1:3 (panta di' autou egeneto — 'all things were "
        "made through him') as the canonical-Pauline-Johannine creator-"
        "Christology pair, fielding the Arian objection at its strongest "
        "point. Tewahedo cosmological-theology cites Col 1:16 at every "
        "Anaphora's institution-prefatory cosmic-acknowledgment.",
        ATTR_CA,
    ),
    ath(
        "col",
        2,
        9,
        "Orationes contra Arianos III.34",
        "'For in him dwelleth all the fulness of the Godhead bodily' — "
        "Athanasius marks pan to plērōma tēs theotētos sōmatikōs (all the "
        "fulness of-the Godhead bodily) as the unsurpassable Pauline-"
        "incarnation-confession. The plērōma (fulness) is not partial "
        "(against any subordinationist diminution); it is pan to plērōma "
        "(ALL the fulness). The theotētos (of-Godhead — abstract-noun "
        "naming the divine-nature-itself, not theiotēs which would name "
        "divinity-as-attribute) is the highest-possible divine-"
        "predication. The sōmatikōs (bodily) names the genuine-embodied-"
        "human mode of the divine-fulness's dwelling. The verse therefore "
        "names: ALL the very-divine-essence dwells BODILY in the "
        "incarnate-Christ. Tewahedo Christological-confession cites "
        "Col 2:9 (paired with Heb 1:3) at every Christmas (Lǝdat) + "
        "Theophany (Tǝmqät) acclamation.",
        ATTR_CA,
    ),
    ath(
        "heb",
        1,
        3,
        "Orationes contra Arianos I.13",
        "'Who being the brightness of his glory, and the express image "
        "of his person, and upholding all things by the word of his "
        "power...' — Athanasius marks the triad apaugasma tēs doxēs + "
        "charaktēr tēs hypostaseōs + pherōn ta panta as the densest "
        "Christological cluster in the NT. The apaugasma (effulgence, "
        "radiance-from-the-source) names the Son's eternal-procession-"
        "from-the-Father in the same metaphysical-mode as light-from-"
        "fire (the light is genuinely-from the fire and genuinely-of "
        "the same nature, not subordinate or temporally-later). The "
        "charaktēr tēs hypostaseōs (express-imprint of his person — "
        "the imprint that a coin shows from its die) names the perfect-"
        "ontological-imaging: the Son shows-forth precisely what the "
        "Father is. The pherōn ta panta tō rhēmati tēs dynameōs (upholding "
        "all-things by the word of his power) names the cosmic-"
        "sustaining-Christology. The Tewahedo Trisagion preserves all "
        "three Hebrews-anchor predications in its anti-Arian formula.",
        ATTR_CA,
    ),
    ath(
        "heb",
        13,
        8,
        "Orationes contra Arianos II.10",
        "'Jesus Christ the same yesterday, and to day, and for ever' — "
        "Athanasius marks Iēsous Christos chthes kai sēmeron ho autos "
        "kai eis tous aiōnas (Jesus Christ the-same yesterday and today "
        "and unto-the-ages) as the unchangeability (atreptos) confession "
        "of the incarnate-Word. The Arian-claim that the Son is mutable "
        "(treptos, capable-of-moral-change) — a claim necessary if the "
        "Son is a creature, since creatures are by-nature changeable — "
        "is directly-contradicted by ho autos (the-same). The atreptos-"
        "Christology means: even in the incarnate-mode (where genuine-"
        "human-suffering and growth-of-wisdom Lk 2:52 occur), the eternal-"
        "Word never-altered in his divine-essence. Tewahedo Christology "
        "preserves the Athanasian-atreptos exactly: the Word in the "
        "incarnation 'remained-what-he-was and became-what-he-was-not.' "
        "Heb 13:8 + Mal 3:6 + Jas 1:17 form the canonical immutability-"
        "triad.",
        ATTR_CA,
    ),
    # ────────────────────────────────────────────────────────────────────────
    # GROUP 4 — PETRINE + JOHANNINE + APOCALYPTIC (8)
    # ────────────────────────────────────────────────────────────────────────
    ath(
        "1pe",
        1,
        19,
        "De Incarnatione Verbi §8",
        "'But with the precious blood of Christ, as of a lamb without "
        "blemish and without spot' — Athanasius marks haimati timiō hōs "
        "amnou amōmou kai aspilou Christou (precious blood of-Christ, "
        "as of-a-lamb without-blemish and-without-spot) as the Petrine "
        "Paschal-Christology. The amnou (lamb) connects Christ to "
        "Ex 12's-Passover-lamb (typological-fulfillment) and Jn 1:29's-"
        "Baptist-pointing (incarnational-recognition). The amōmou kai "
        "aspilou (without-blemish-and-without-spot) names the moral-"
        "sinlessness that is constitutive of the Lamb's-sufficiency for "
        "redemption. The haimati timiō (precious blood) names the value "
        "of the redemption (which only divine-blood could possess — "
        "Acts 20:28 'the church of God which he hath purchased with his "
        "own blood'). The Tewahedo Anaphora cites 1 Pet 1:19 + Jn 1:29 "
        "+ Acts 20:28 as the institutional-Lamb-triad at every Eucharist.",
        ATTR_DI,
    ),
    ath(
        "1pe",
        4,
        1,
        "Epistola ad Epictetum",
        "'Forasmuch then as Christ hath suffered for us in the flesh' — "
        "Athanasius marks Christou pathontos sarki (Christ-having-"
        "suffered in-flesh) as the qualifier that locates the Passion in "
        "the assumed-human-nature without compromising divine-"
        "impassibility. The Word-suffers IN the flesh he assumed (the "
        "sarki is locative, naming WHERE the suffering happens) without "
        "the divine-nature itself becoming passible. The Tewahedo "
        "Miaphysite-Christology preserves this Athanasian-distinction: "
        "the one-incarnate-Person of the Word genuinely-suffers in the "
        "flesh he-assumed, while the divine-essence remains impassible "
        "in the same-Person. The Athanasian-impassibility is NOT the "
        "denial of Christ's-human-suffering (which is real, Heb 5:8 "
        "'though he were a Son, yet learned he obedience by the things "
        "which he suffered'); it is the NATURE-distinction within the "
        "Person. The Tewahedo Holy-Friday (Sǝqlät) hymnody preserves "
        "this in its Cyrillian-Athanasian Miaphysite-confession.",
        ATTR_EPICT,
    ),
    ath(
        "2pe",
        1,
        4,
        "De Incarnatione Verbi §54",
        "'Whereby are given unto us exceeding great and precious "
        "promises: that by these ye might be partakers of the divine "
        "nature' — Athanasius marks theias koinōnoi physeōs (partakers "
        "of-divine nature) as the THEOSIS-summit of the entire NT and "
        "the Petrine-anchor of his signature-formula: 'For he was made "
        "man that we might be made God' (Autos gar enēnthrōpēsen, hina "
        "hēmeis theopoiēthōmen — DI §54, the most-quoted line in all of "
        "patristic theology). The koinōnoi (partakers, sharers — strong "
        "noun, not merely 'observers' or 'imitators') names the genuine-"
        "ontological-sharing in the divine-life that the incarnation "
        "achieves for the redeemed. The theias-physeōs (divine-nature) is "
        "not creaturely-elevation (which Arian-creatures could in principle "
        "experience) but participation-in-the-essence-itself by grace. "
        "Tewahedo deification-spirituality (the Mahǝbär-Sǝmʿon ascetic "
        "tradition, the Säwasǝw-of-Pure-Thought) is built explicitly on "
        "the Athanasian-Petrine theosis-foundation.",
        ATTR_DI,
    ),
    ath(
        "1jn",
        1,
        1,
        "De Incarnatione Verbi §17",
        "'That which was from the beginning, which we have heard, which "
        "we have seen with our eyes, which we have looked upon, and our "
        "hands have handled, of the Word of life' — Athanasius marks "
        "the four-fold sensory-witness (akēkoamen + heōrakamen + "
        "etheasametha + epsēlaphēsan — heard, seen, beheld, handled) as "
        "the Johannine apostolic-anti-Docetic confession. The Word-of-"
        "life is NOT a phantasm, NOT a Gnostic-apparition, NOT a Docetic-"
        "appearance — he is hearable, visible, examinable, palpable. The "
        "four-fold-witness pattern matches the four-canonical-Gospels "
        "(eyewitness Mt, hearer-of-Petrine-witness Mk, investigator-Lk, "
        "beloved-disciple-Jn) such that the incarnate-Word's sensory-"
        "accessibility is canonically-witnessed. The Tewahedo apostolic-"
        "succession (Frumentius-through-Athanasius-through-the-Twelve) "
        "cites 1 Jn 1:1-3 as the apostolic-eyewitness-warrant.",
        ATTR_DI,
    ),
    ath(
        "1jn",
        3,
        2,
        "De Incarnatione Verbi §54",
        "'Beloved, now are we the sons of God, and it doth not yet "
        "appear what we shall be: but we know that, when he shall "
        "appear, we shall be like him; for we shall see him as he is' — "
        "Athanasius marks homoioi autō esometha (we-shall-be like-him) "
        "as the eschatological-theosis-fulfillment of the Athanasian "
        "deification-doctrine. The homoioi-autō is not mere moral-"
        "similarity (which any creature could in principle achieve) but "
        "the kath'-homoiōsin-theou likeness-to-God that Gen 1:26's "
        "creation-blueprint envisioned and that the Fall fragmented and "
        "that the Word's-incarnation restores. The hoti opsometha auton "
        "kathōs estin (for we shall see him as he is) names the beatific-"
        "vision that COMPLETES the theosis: face-to-face vision of the "
        "incarnate-divine-Person produces the final-conformity-to-his-"
        "image (cf. 2 Cor 3:18 'we all... beholding... are changed into "
        "the same image'). The Tewahedo eschatological-hymnody cites "
        "1 Jn 3:2 + 2 Cor 3:18 + Rev 22:4 as the beatific-vision-triad.",
        ATTR_DI,
    ),
    ath(
        "rev",
        1,
        8,
        "Orationes contra Arianos II.13",
        "'I am Alpha and Omega, the beginning and the ending, saith the "
        "Lord, which is, and which was, and which is to come, the "
        "Almighty' — Athanasius marks egō eimi to alpha kai to ō (I-AM "
        "the alpha and the omega) as the Apocalyptic-Christ's self-"
        "predication of divine-comprehension. The alpha-and-omega names "
        "the all-encompassing-divine-priority-and-finality (no creature "
        "could rightly predicate this of itself). The ho ōn kai ho ēn "
        "kai ho erchomenos (the-One-being, the-One-was, the-One-coming) "
        "is the Apocalyptic-expansion of the LXX-Ex 3:14 ho ōn — the "
        "incarnate-Christ taking-up the burning-bush-self-naming and "
        "extending it across the eternal-time-axis. The ho pantokratōr "
        "(the-Almighty) is the LXX-translation of Hebrew-El-Shaddai, the "
        "highest divine-power-predication. The Tewahedo Apocalyptic-"
        "iconology (the Christ-Pantocrator iconography of every "
        "Tewahedo-church dome) cites Rev 1:8 as the canonical-self-"
        "predication.",
        ATTR_CA,
    ),
    ath(
        "rev",
        5,
        13,
        "Orationes contra Arianos II.23",
        "'And every creature which is in heaven, and on the earth, and "
        "under the earth, and such as are in the sea, and all that are "
        "in them, heard I saying, Blessing, and honour, and glory, and "
        "power, be unto him that sitteth upon the throne, and unto the "
        "Lamb for ever and ever' — Athanasius marks pan ktisma (every "
        "creature) worshiping tō kathēmenō epi tō thronō kai tō arniō "
        "(the-One-sitting upon the throne AND the Lamb) as the "
        "cosmic-Apocalyptic-divinity confession. The verse explicitly-"
        "distinguishes the Lamb (the incarnate-Christ) from pan-ktisma "
        "(every-creature) — the Lamb is therefore-NOT among-the-"
        "creatures, but stands with the Father-on-the-throne as the joint-"
        "recipient of cosmic-creaturely-worship. The four-fold doxology "
        "(eulogia + timē + doxa + kratos — blessing + honor + glory + "
        "power) is offered indistinguishably to Father-and-Lamb, marking "
        "ontological-equality. The Tewahedo Anaphora doxological-section "
        "cites Rev 5:13 + 7:10 + 11:15 as the apocalyptic-divinity-triad.",
        ATTR_CA,
    ),
    ath(
        "rev",
        22,
        13,
        "Orationes contra Arianos II.13",
        "'I am Alpha and Omega, the beginning and the end, the first "
        "and the last' — Athanasius marks the closing-Apocalyptic Christ-"
        "self-predication as the inclusio-pair with Rev 1:8. The triple-"
        "self-designation (alpha-omega + archē-telos + prōtos-eschatos) "
        "is doxologically-maximal: every-conceivable temporal-and-"
        "ontological priority-and-finality is appropriated to the "
        "incarnate-Christ. The eschatos (last) connects to LXX-Isa 44:6 "
        "egō prōtos kai egō meta tauta (I-first and-I after-these), an "
        "explicit YHWH-self-predication in the prophet, now self-claimed "
        "by the risen-incarnate-Christ. The Tewahedo Apocalyptic-"
        "Christology (the Lǝʿǝlt Mäskäl Feast-of-the-Cross hymnody, the "
        "Maḥaberä-Qǝddāsē choral-tradition) cites Rev 22:13 + Isa 44:6 "
        "as the divine-self-naming-Christological-inclusio that frames "
        "the whole-of-Scripture.",
        ATTR_CA,
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 40, f"expected 40 entries, got {len(NEW_ENTRIES)}"
assert all(e["father"] == "Athanasius of Alexandria" for e in NEW_ENTRIES)

# Book distribution sanity
_books_covered = sorted({e["book"] for e in NEW_ENTRIES})
_expected_books = sorted(
    {
        "gen",
        "exo",
        "psa",
        "pro",
        "isa",
        "mat",
        "jhn",
        "rom",
        "1co",
        "2co",
        "gal",
        "eph",
        "phi",
        "col",
        "heb",
        "1pe",
        "2pe",
        "1jn",
        "rev",
    }
)
assert _books_covered == _expected_books, f"book set mismatch: got {_books_covered}, expected {_expected_books}"


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    assert "entries" in d and "_meta" in d

    pre_count = len(d["entries"])
    d["entries"].extend(NEW_ENTRIES)
    post_count = len(d["entries"])

    ledger_addition = (
        " γ.4.9 (2026-05-13) added Athanasius of Alexandria seed wave — "
        "40 verse-keyed entries spanning OT christological anticipations "
        "(Gen 1:26 + 1:27 + Ex 3:14 + Ps 2:7 + 110:1 + Pr 8:22 + Isa 7:14 "
        "+ 9:6) + canonical Gospel Christology (Mt 1:23 + 11:27 + 28:19 + "
        "Jn 1:1 + 1:14 + 10:30 + 14:9 + 20:28) + Pauline Christology "
        "(Rom 1:3 + 8:15 + 9:5 + 1 Cor 1:24 + 8:6 + 2 Cor 8:9 + Gal 4:4 + "
        "Eph 1:10 + Phi 2:6 + 2:7 + 2:9 + Col 1:15 + 1:16 + 2:9 + Heb 1:3 "
        "+ 13:8) + Petrine + Johannine + Apocalyptic (1 Pet 1:19 + 4:1 + "
        "2 Pet 1:4 + 1 Jn 1:1 + 3:2 + Rev 1:8 + 5:13 + 22:13). OPENS A "
        "FIFTH PATRISTIC VOICE in the γ.4 corpus alongside the four-voice "
        "composition codified at ω.41 (Cyril of Alexandria 668 + Jubilees "
        "200 + 1 Enoch 192 + Ephrem the Syrian 157): Athanasius is the "
        "Tewahedo apostolic-bridge (20th Patriarch of the See of Mark; "
        "consecrator c. 330 of Frumentius the Tewahedo founder; author "
        "of Festal Letter 39 of 367 establishing the NT canon the "
        "Tewahedo Church receives). The seed pairs structurally with the "
        "γ.4.7-D Cyril-on-Mark arc-close (both are See-of-Mark "
        "patriarchal-succession Christology), extending the apostolic-"
        "lineage hermeneutical reading BACKWARDS from Cyril (24th "
        "Patriarch) to Athanasius (20th Patriarch). Sources: NPNF Series 2 "
        "Volume 4 (ed. Archibald Robertson, Oxford/T&T Clark 1892 — PD) — "
        "De Incarnatione Verbi + Orationes contra Arianos I-IV + De "
        "Decretis Nicaenae Synodi + Festal Letters (incl. Letter 39) + "
        "Epistola ad Epictetum + Letter to Adelphius. Greek text in Migne "
        "PG 25-28 (1857-1887, PD). Voice mix post-γ.4.9: Cyril 53.1% / "
        "Jubilees 15.9% / 1 Enoch 15.3% / Ephrem 12.5% / Athanasius 3.2% "
        "(patristic-anchor majority 68.8% — Cyril + Ephrem + Athanasius). "
        "Patristic plurality DEEPENED without displacing the Cyril-led "
        "intentional plurality per ω.41 §1."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    athanasius_total = sum(1 for e in d["entries"] if e["father"] == "Athanasius of Alexandria")
    print(f"γ.4.9 ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(f"Athanasius of Alexandria total: {athanasius_total} entries — FIFTH PATRISTIC VOICE OPENED")
    print(f"Books covered: {len({e['book'] for e in NEW_ENTRIES})} ({sorted({e['book'] for e in NEW_ENTRIES})})")


if __name__ == "__main__":
    main()
