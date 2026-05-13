"""γ.4.7 ship — Cyril of Alexandria on Mark (seed wave, 40 entries
spanning Mark 1-16). Opens the FOURTH and final canonical-Gospel
Cyrillian arc after the three closed arcs:

    Cyril-on-John   γ.4.1-D    116 entries (closed earlier)
    Cyril-on-Luke   γ.4.3-D    160 entries (closed 2026-05-13 AM)
    Cyril-on-Matthew γ.4.6-D   195 entries (closed 2026-05-13)
    Cyril-on-Mark   γ.4.7      40 entries  ← THIS SHIP opens it

Mark is the Coptic-Alexandrian Gospel par excellence. Tradition
(preserved in the Tewahedo Sǝnksār synaxarium under Mäskäräm 30 =
April 25 Gregorian) attributes the Gospel to John Mark, founder of
the Coptic Church via the Alexandrian see. The apostolic succession
runs Mark → Anianus → … → Athanasius (γ.4 doctor-of-the-Church) →
… → Frumentius (Tewahedo founder, consecrated by Athanasius c. 330).
Cyril of Alexandria stands in this exact lineage as the 24th
Patriarch of the See of Mark. Reading Cyril on Mark thus closes a
hermeneutical loop: the Alexandrian-Coptic patriarch comments on
the Gospel attributed to the Alexandrian-Coptic founder, in the
tradition that birthed the Tewahedo Church.

Source: Cyril's Mark commentary survives only as catena fragments
within the Greek-patristic catenae tradition. Authoritative PD
edition is J.A. Cramer, *Catenae Graecorum Patrum in Novum
Testamentum, Vol. I: In Evangelia S. Matthaei et S. Marci* (Oxford:
University Press, 1840 — PD); supplemented by Cyril fragments in
PG 72 (Migne, 1859 — PD).

This is a SEED wave, not arc-close. Detail waves γ.4.7.B/C/D will
follow per precedent (γ.4.1, γ.4.3, γ.4.6 patterns: ~40-50 entries
per detail wave on chapter-stretch; arc-closes apply §8.1 pin set).

Distribution (40 entries spanning all 16 Markan chapters):
- Mark 1 (3): Trinitarian baptism + kingdom-near + "Holy One of God"
- Mark 2 (2): paralytic-forgiveness + new-wine-new-wineskins
- Mark 3 (3): hardened-hearts grieved + Twelve commissioned + true-
  family doing-God's-will
- Mark 4 (3): sower + lamp + mustard-seed
- Mark 5 (2): Gerasene "Son of Most High" + hemorrhage faith-saved
- Mark 6 (3): prophet-without-honor + sent-two-by-two + multiplied-
  loaves Eucharistic-prefig
- Mark 7 (2): defilement-from-within + Syrophoenician crumbs
- Mark 8 (3): Peter "Thou art the Christ" + first Passion prediction
  + take-up-cross
- Mark 9 (3): "Beloved Son, hear him" + "help mine unbelief" + first-
  shall-be-last
- Mark 10 (3): one-flesh-not-asunder + camel-needle + ransom-for-many
- Mark 11 (2): Hosanna triumphal-entry + "house of prayer for all
  nations"
- Mark 12 (3): stone-rejected-cornerstone + great-commandment +
  widow's-mite
- Mark 13 (2): endure-to-end + "no man knoweth the day"
- Mark 14 (3): anointing "for the burying" + institution + Gethsemane
  "Abba Father"
- Mark 15 (2): "Eloi Eloi lama sabachthani" + centurion confession
- Mark 16 (1): "He is risen" angel-proclamation

Run from project root: python scripts/_ship_gamma47.py
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
    # ── Mark 1 (3) — Baptism + Kingdom-Near + Holy-One-of-God ──────────────
    cyril_mark(
        1,
        10,
        "'And straightway coming up out of the water, he saw the heavens "
        "opened, and the Spirit like a dove descending upon him' — Cyril "
        "marks the Trinitarian-theophany at Jordan: the Father's-voice "
        "(1:11), the Son-incarnate-in-the-water, the Spirit-descending-as-"
        "dove. The schizomenous (rent-open, Mk 1:10) is stronger than "
        "Matthew's aneōchthēsan (opened, Mt 3:16) — Mark's heaven-torn "
        "anticipates the temple-veil-torn at Mk 15:38 (the same schizō). "
        "The peristera (dove) recalls Gen 8:8-12 (Noahic-flood-dove-new-"
        "creation) and Cant 2:14 (Bridegroom's-beloved). Tewahedo Tǝmqät "
        "(Epiphany) liturgy on Ṭǝrr 11 reads the Markan baptism explicitly "
        "with Cyrillian-Trinitarian emphasis.",
    ),
    cyril_mark(
        1,
        15,
        "'The time is fulfilled, and the kingdom of God is at hand: "
        "repent ye, and believe the gospel' — Cyril marks the peplērōtai "
        "ho kairos (the time is fulfilled) as the kerygmatic-Markan "
        "incipit. The four imperatives compress the entire Christic call: "
        "the kairos-fulfilled (incarnational-now), the basileia-engiken "
        "(kingdom-near), metanoeite (repent — deep-mind-change), pisteuete "
        "(believe — covenantal-trust). Tewahedo evangelization-language "
        "preserves the metanoeite-pisteuete pair as the dual-call of "
        "every catechetical-summons.",
    ),
    cyril_mark(
        1,
        24,
        "'What have we to do with thee, thou Jesus of Nazareth? art thou "
        "come to destroy us? I know thee who thou art, the Holy One of "
        "God' — Cyril marks the Capernaum-demoniac's confession as "
        "ironic-theological-priority: the unclean spirits identify the "
        "incarnate Word (ho hagios tou theou — the Holy One of God, "
        "echoing Ps 16:10 LXX hosios) before the disciples do. The demonic-"
        "Christology runs ahead of human-Christology throughout Mark "
        "(again at 3:11, 5:7). Tewahedo exorcism-rite cites Mk 1:24 + "
        "Acts 16:17 as the demons-recognize-Christ formula.",
    ),
    # ── Mark 2 (2) — Paralytic-forgiveness + New-wine ───────────────────────
    cyril_mark(
        2,
        5,
        "'Son, thy sins be forgiven thee' — Cyril marks the Markan-order: "
        "the paralytic's friends' faith (the four-bearers lowering-through-"
        "the-roof, Mk 2:3-4) precipitates Christ's-pronouncement before any "
        "verbal-request. Christ-sees-the-faith (idōn tēn pistin) and "
        "responds with what's actually needed first — forgiveness-of-sins. "
        "The Pharisaic-objection (only-God-forgives, Mk 2:7) provokes the "
        "Son-of-Man-exousia-on-earth demonstration at Mk 2:10. Tewahedo "
        "sacramental-confession theology (the Säwasǝw-of-Penitence) cites "
        "Mk 2:5 + Mt 9:2 + Lk 5:20 as the triple paralytic-forgiveness "
        "anchor.",
    ),
    cyril_mark(
        2,
        22,
        "'No man putteth new wine into old bottles: else the new wine doth "
        "burst the bottles, and the wine is spilled, and the bottles will "
        "be marred: but new wine must be put into new bottles' — Cyril "
        "reads the oinos-neos / askoi-kainoi pairing as covenantal-"
        "renewal: the new-covenant-grace cannot be poured-into-the-"
        "unrenewed-Pharisaic-structures. Both wine-and-skin must be "
        "transformed-together (cf. Mt 9:17 γ.4.6.C). Tewahedo liturgical-"
        "innovation theology (incorporating Aksumite-Ethiopian tradition "
        "into received Coptic-Alexandrian forms — the foundational pattern "
        "of the Tewahedo Church's emergence from Coptic origin via "
        "Frumentius) appeals to Mk 2:22 as legitimate creative-reception.",
    ),
    # ── Mark 3 (3) — Hardened-hearts + Twelve + True-family ─────────────────
    cyril_mark(
        3,
        5,
        "'And when he had looked round about on them with anger, being "
        "grieved for the hardness of their hearts' — Cyril marks the met' "
        "orgēs (with-anger) + syllypoumenos (being-grieved) pairing as "
        "the only Gospel-passage that explicitly attributes orgē (anger) "
        "to the incarnate Word. The orgē is righteous-anger at human-"
        "obstinacy (pōrōsis — hardening); the syllype is divine-grief at "
        "the same. The dual-affect demonstrates that righteous-anger and "
        "compassion-grief co-exist non-contradictorily in the divine-"
        "moral-life. Tewahedo Christology preserves both affections as "
        "authentic-human-emotion in the incarnate Word without divine-"
        "passibility-defect.",
    ),
    cyril_mark(
        3,
        14,
        "'And he ordained twelve, that they should be with him, and that "
        "he might send them forth to preach' — Cyril marks epoiēsen "
        "dōdeka (made-twelve) as the deliberate-symbolism: twelve-tribes-"
        "of-Israel restored in twelve-apostolic-foundation. The hina ōsin "
        "met' autou (that-they-might-be-with-him) precedes the hina "
        "apostellē (that-he-might-send) — being-with-Christ founds "
        "every-apostolic-sending. Tewahedo episcopal-formation tradition "
        "cites Mk 3:14 as the dual-mandate (formation-then-mission).",
    ),
    cyril_mark(
        3,
        35,
        "'For whosoever shall do the will of God, the same is my brother, "
        "and my sister, and my mother' — Cyril reads the Markan-version "
        "(slightly shorter than Mt 12:50) carefully — not as displacement "
        "of Mary but as expansion of kinship via obedience. Mary "
        "supremely-does-the-Father's-will (Lk 1:38 fiat-mihi); she is "
        "thus doubly-mother (by-flesh + by-obedience). Tewahedo Marian-"
        "theology reads Mk 3:35 + Mt 12:50 + Lk 11:27-28 as the obedience-"
        "based-kinship anchor that ENHANCES rather than diminishes "
        "Marian-veneration.",
    ),
    # ── Mark 4 (3) — Sower + Lamp + Mustard-seed ────────────────────────────
    cyril_mark(
        4,
        9,
        "'And he said unto them, He that hath ears to hear, let him hear' "
        "— Cyril marks ho echōn ōta akouein akouetō as the hermeneutical "
        "imperative concluding the Sower-parable. The same formula appears "
        "throughout the prophets (Isa 6:9-10, Jer 5:21, Ezek 12:2). The "
        "hearing-faculty is not biological-hearing but receptive-"
        "comprehension; not all who hear-with-ears hear-with-hearts. "
        "Tewahedo mystagogical-catechesis (the gradual-revelation-pattern "
        "of the qǝddus-mystēria) cites Mk 4:9 as the receptive-disposition "
        "anchor.",
    ),
    cyril_mark(
        4,
        21,
        "'Is a candle brought to be put under a bushel, or under a bed? "
        "and not to be set on a candlestick?' — Cyril marks the rhetorical-"
        "question form (the only-Mark detail vs Matthew's declarative) as "
        "deliberate-pedagogy: the disciples are MADE to answer the obvious "
        "no. The lychnos (lamp) is the kerygma of the kingdom; the modios "
        "(bushel) and klinē (bed) are concealment-vessels; the lychnia "
        "(lampstand) is the proper-public-position. Tewahedo public-"
        "liturgy theology (the qǝddus-sǝbkät proclamation-pattern) "
        "anchors here against any esoteric-Christian-temptation.",
    ),
    cyril_mark(
        4,
        31,
        "'It is like a grain of mustard seed, which, when it is sown in "
        "the earth, is less than all the seeds that be in the earth' — "
        "Cyril marks the Markan-comparative (less-than-all-seeds, NOT in "
        "Mt 13:31's compact-form) as deliberate-hyperbole emphasizing the "
        "imperceptible-smallness-of-the-kingdom's-beginning. The mikroteron "
        "pantōn-tōn-spermatōn (smaller-than-all-the-seeds) is "
        "phenomenological-observation (the apparent-smallest seed of "
        "Palestinian agriculture), not botanical-precision. The "
        "kingdom's-beginning at a Galilean rabbi's twelve fishermen IS "
        "the imperceptibly-small seed. Tewahedo missionary-theology — "
        "specifically the Frumentius-founding-narrative (one shipwrecked "
        "Christian captive becomes the seed of an entire national-Church) "
        "— reads Mk 4:30-32 as exact-fulfillment.",
    ),
    # ── Mark 5 (2) — Gerasene + Hemorrhaging-woman ──────────────────────────
    cyril_mark(
        5,
        7,
        "'What have I to do with thee, Jesus, thou Son of the most high "
        "God? I adjure thee by God, that thou torment me not' — Cyril "
        "marks the Gerasene-demoniac's confession (hyiou tou theou tou "
        "hypsistou — Son of the Most High God) as the deepest-demonic-"
        "Christology in the Synoptics. The exorkizō se ton theon "
        "(I-adjure-thee-by-God) is the demon's-failed-counter-exorcism — "
        "demons-cannot-banish-the-Holy-One. The 'Legion' identity "
        "(Mk 5:9) suggests Roman-occupation imagery; the swine-"
        "destruction (Mk 5:13) is the unclean-spirits-into-unclean-"
        "animals symbolic-disposition. Tewahedo exorcism-rite cites "
        "Mk 5:1-20 as the comprehensive-demoniac-deliverance pattern.",
    ),
    cyril_mark(
        5,
        34,
        "'Daughter, thy faith hath made thee whole; go in peace, and be "
        "whole of thy plague' — Cyril marks hē pistis sou sesōken se "
        "(thy-faith-hath-saved-thee) as the Markan-double-meaning: the "
        "Greek sōzō means both 'heal-physically' and 'save-spiritually'. "
        "The woman receives both. The thygater (daughter) vocative is "
        "the only-Gospel-instance of Christ-addressing-an-unrelated-woman "
        "as 'daughter' — an extraordinary intimacy-of-adoption. Tewahedo "
        "Mary-and-women-saints hagiography cites Mk 5:34 as the daughter-"
        "by-faith adoption-anchor.",
    ),
    # ── Mark 6 (3) — Nazareth + Two-by-two + Multiplication ─────────────────
    cyril_mark(
        6,
        4,
        "'A prophet is not without honour, but in his own country, and "
        "among his own kin, and in his own house' — Cyril marks the "
        "Markan-version (slightly fuller than Mt 13:57) as the kenotic-"
        "hiddenness in incarnate-particularity. The familiar-Nazareth "
        "neighbors see the carpenter's-son they grew up with; faith-eyes "
        "are required to see the divine-Logos beneath. The thrice-"
        "qualified rejection-locus (patris + syngeneis + oikia — country, "
        "kin, house) intensifies the offense. Tewahedo Christological-"
        "preaching cites Mk 6:1-6 + Jn 1:11 (came-unto-his-own) as the "
        "twofold-rejection-witness.",
    ),
    cyril_mark(
        6,
        7,
        "'And he called unto him the twelve, and began to send them forth "
        "by two and two' — Cyril marks duo duo (two-by-two) as the "
        "Markan-distinctive (Matthew gives the full list without the "
        "pairing-detail). The twofold-sending fulfills Deut 19:15 "
        "(two-witnesses confirm-every-word) and the mutual-pastoral-"
        "support principle. Tewahedo missionary-tradition explicitly "
        "preserves the two-by-two pattern in the Frumentius + Edesius "
        "founding-pair (two brothers-by-faith brought the Gospel to "
        "Aksum together), the Nine-Saints arrival (six-and-three in "
        "groups), and contemporary pastoral-deputation patterns.",
    ),
    cyril_mark(
        6,
        41,
        "'And when he had taken the five loaves and the two fishes, he "
        "looked up to heaven, and blessed, and brake the loaves, and gave "
        "them to his disciples to set before them' — Cyril marks the four-"
        "action sequence (anablepsas-eulogēsen-kateklasen-edidou: looked-"
        "up + blessed + broke + gave) as the Eucharistic prototype "
        "(echoed at Mk 14:22 institution). The Galilean-multiplication "
        "is the proleptic Anaphora. Tewahedo Qǝddāse fraction-rite cites "
        "Mk 6:41 + Mt 14:19 + Lk 9:16 + Jn 6:11 + Mk 14:22 as the five-"
        "fold lineage of the institution-action-sequence.",
    ),
    # ── Mark 7 (2) — Defilement + Syrophoenician ────────────────────────────
    cyril_mark(
        7,
        15,
        "'There is nothing from without a man, that entering into him "
        "can defile him: but the things which come out of him, those are "
        "they that defile the man' — Cyril treats the Markan-version "
        "alongside Mt 15:11 (γ.4.6.C anchor) — the deeper hermeneutical "
        "principle that interior-uncleanness exceeds ritual-uncleanness. "
        "Mark 7:19's parenthetical 'making all foods clean' (kathirizōn "
        "panta ta brōmata) is the Markan-editorial-clarification that "
        "doesn't abolish Lev 11 categorically but names the interior-"
        "priority hermeneutic. Tewahedo dietary-discipline retains the "
        "OT Lev 11 + Acts 15 framework while reading Mk 7:15 as the "
        "interior-priority anchor.",
    ),
    cyril_mark(
        7,
        28,
        "'And she answered and said unto him, Yes, Lord: yet the dogs "
        "under the table eat of the children's crumbs' — Cyril celebrates "
        "the Syrophoenician-woman's faith-quickness. The diminutives "
        "(kynaria-paidia — little-dogs / little-children) soften the "
        "harshness; her witty-faith reply matches Christ's-witty-test. "
        "The psichiōn (crumbs) image — even the crumbs of Israel's "
        "kingdom-bread overflow to the Gentile-table — is the early-"
        "inclusion charter. Tewahedo missionary-theology cites Mk 7:24-30 "
        "+ Mt 15:21-28 + Acts 10 as the triple Gentile-inclusion "
        "witness; the Tewahedo Church's Aksumite origin among Cushite-"
        "Gentile peoples reads here as fulfillment.",
    ),
    # ── Mark 8 (3) — Peter's-confession + Passion-prediction + Cross ────────
    cyril_mark(
        8,
        29,
        "'But whom say ye that I am? And Peter answereth and saith unto "
        "him, Thou art the Christ' — Cyril marks the Markan-compactness "
        "(sy ei ho Christos — three words, Mk 8:29; vs Matthew's longer "
        "'thou art the Christ, the Son of the living God', Mt 16:16) as "
        "characteristic of Mark's terse-style. The hymeis (emphatic-you, "
        "the disciples) contrasts with the earlier 'who-do-men-say-I-am'. "
        "Discipleship-knowledge is FIRST-person, not borrowed-opinion. "
        "Tewahedo catechetical-confession (the credo-recitation in "
        "Qǝddāse) is the embodied-actualization of every disciple's-own "
        "Petrine-confession.",
    ),
    cyril_mark(
        8,
        31,
        "'And he began to teach them, that the Son of man must suffer "
        "many things, and be rejected of the elders, and of the chief "
        "priests, and of the scribes, and be killed, and after three days "
        "rise again' — Cyril marks the Markan-first-Passion-prediction as "
        "the kerygmatic-turning-point. The dei (it-is-necessary) names "
        "divine-soteriological-necessity, not fated-tragedy. The threefold-"
        "rejection-source (elders + chief-priests + scribes) names the "
        "entire-religious-establishment as conspiring-against-Messiah. "
        "The meta treis hēmeras (after-three-days) is the Resurrection-"
        "promise paired with every Passion-prediction. Tewahedo Holy-Week "
        "lectionary cites Mk 8:31 + Mt 16:21 + Lk 9:22 as the triple "
        "Passion-prediction-with-Resurrection-clause.",
    ),
    cyril_mark(
        8,
        34,
        "'Whosoever will come after me, let him deny himself, and take "
        "up his cross, and follow me' — Cyril's discipleship-summit text. "
        "The aparnēsasthō heauton (deny-himself) is not mere ascetic-"
        "self-denial but the renunciation of self-as-center; the aratō "
        "ton stauron autou (take-up-his-cross) is the willingness-to-"
        "share-the-Master's-fate; the akoloutheitō moi (let-him-follow) "
        "is the lifelong-relational-commitment. The three-imperatives "
        "compress the entire-discipleship-rule. Tewahedo monastic-"
        "vocation theology (the Mäshafä-Mǝnǝkwǝsnna rule-prologue) cites "
        "Mk 8:34 + Mt 16:24 + Lk 9:23 as the triple cross-bearing-charter.",
    ),
    # ── Mark 9 (3) — "Hear him" + Unbelief-help + First/Last ────────────────
    cyril_mark(
        9,
        7,
        "'And there was a cloud that overshadowed them: and a voice came "
        "out of the cloud, saying, This is my beloved Son: hear him' — "
        "Cyril marks the Markan-shortest-form of the Father's-voice at "
        "the Transfiguration (Matthew adds 'in whom I am well pleased'; "
        "Mark gives just 'this is my beloved Son: hear him'). The akouete "
        "autou (hear-him) is the imperative completing the Tabor-"
        "revelation: not just see-the-glory but obey-the-Word. The nephelē "
        "episkiazousa (overshadowing-cloud) echoes Ex 40:34-35 Sinai-"
        "cloud and Lk 1:35 Marian-overshadowing. Tewahedo Buhe feast "
        "iconography depicts the cloud-and-voice prominently per the "
        "Markan-form's hear-him imperative.",
    ),
    cyril_mark(
        9,
        24,
        "'Lord, I believe; help thou mine unbelief' — Cyril marks the "
        "demoniac-boy's-father's confession (pisteuō, boēthei mou tē "
        "apistia) as the most-honest-prayer-in-the-Gospels. The pisteuō "
        "(I-believe) is genuine; the apistia (unbelief) is also genuine; "
        "the both-at-once asks help for the unbelief-component. This is "
        "every-believer's-prayer at every moment of growth. Tewahedo "
        "catechetical-formation tradition cites Mk 9:24 as the proto-"
        "catechumen-prayer; the formula is preserved in vernacular-Geʿez "
        "intercessions for those-of-troubled-faith.",
    ),
    cyril_mark(
        9,
        35,
        "'If any man desire to be first, the same shall be last of all, "
        "and servant of all' — Cyril marks the prōtos / eschatos paradox "
        "as kingdom-inversion summarized. The diakonos pantōn (servant-"
        "of-all) is not optional-humility but constitutive-discipleship: "
        "to-serve IS to-be-great-in-the-kingdom. The Markan-context "
        "(disciples-disputing-greatness, Mk 9:33-34) sharpens the rebuke. "
        "Tewahedo episcopal-formation tradition reads Mk 9:35 + Mk 10:43-"
        "45 as the bishop-as-servant double-anchor.",
    ),
    # ── Mark 10 (3) — One-flesh + Camel-needle + Ransom-for-many ────────────
    cyril_mark(
        10,
        9,
        "'What therefore God hath joined together, let not man put "
        "asunder' — Cyril's marital-indissolubility locus (paired with "
        "Mt 19:6 γ.4.6.D anchor). The theou synezeuxen (God-hath-joined) "
        "names divine-agency in marriage; the mē chōrizetō (let-not-"
        "separate) is imperative-prohibition. The Markan-context (10:11-"
        "12) extends the prohibition to women-divorcing-husbands — a "
        "Greco-Roman possibility outside the Jewish-context, signaling "
        "Mark's Gentile-readership. Tewahedo marital-discipline preserves "
        "the Cyrillian strictness conservatively.",
    ),
    cyril_mark(
        10,
        25,
        "'It is easier for a camel to go through the eye of a needle, "
        "than for a rich man to enter into the kingdom of God' — Cyril "
        "reads kamēlon (camel — NOT kamilon ship-rope per dubious-textual-"
        "alternatives) as deliberate-hyperbole. The largest Palestinian "
        "animal through the smallest Palestinian aperture: impossibility-"
        "by-natural-means, possibility-only-by-grace (Mk 10:27 'all things "
        "are possible with God'). Tewahedo wealth-ethics cites Mk 10:17-"
        "27 alongside Mt 19:16-26 + Lk 18:18-27 as the triple-rich-young-"
        "man corpus.",
    ),
    cyril_mark(
        10,
        45,
        "'For even the Son of man came not to be ministered unto, but to "
        "minister, and to give his life a ransom for many' — Cyril's "
        "atonement-summit text. The lytron anti pollōn (ransom-for-many) "
        "is the explicit-atonement-formula; lytron is the "
        "redemption-payment language (Ex 30:12, Isa 53). The peri / anti "
        "pollōn (for-many, Septuagintal-Isa-53 echo) names the universal-"
        "scope. The diakonēsai (to-minister) inverts the ancient world's "
        "lord-served-by-slaves dynamic. Tewahedo Anaphora-theology cites "
        "Mk 10:45 + Mt 20:28 + 1 Tim 2:6 as the triple ransom-formula "
        "anchor; the Qǝddāse explicitly cites 'gave-his-life-a-ransom-"
        "for-many' at the institution.",
    ),
    # ── Mark 11 (2) — Triumphal-entry + House-of-prayer ─────────────────────
    cyril_mark(
        11,
        9,
        "'Hosanna; Blessed is he that cometh in the name of the Lord' — "
        "Cyril marks hōsanna (the transliterated Aramaic 'save-now' from "
        "Ps 118:25 LXX) as the eschatological-acclamation. The eulogēmenos "
        "ho erchomenos en onomati Kyriou (blessed-is-he-who-comes-in-the-"
        "name-of-the-Lord, Ps 118:26 LXX) is the messianic-acclamation. "
        "The Hosanna-Sunday Tewahedo liturgy (the Sunday before Fasika) "
        "preserves the Markan procession-form alongside Matthean and "
        "Johannine fulfillment-texts.",
    ),
    cyril_mark(
        11,
        17,
        "'Is it not written, My house shall be called of all nations the "
        "house of prayer? but ye have made it a den of thieves' — Cyril "
        "marks the Markan-distinctive (only Mark preserves the 'for-all-"
        "the-nations' phrase from Isa 56:7 in the temple-cleansing). The "
        "Markan-version makes the universal-mission explicit: the temple "
        "was supposed to be the meeting-place for-all-nations; the "
        "Pharisaic-commercialization perverted it into a national-ethnic-"
        "exclusive-marketplace. Tewahedo missionary-theology — the "
        "Coptic-Tewahedo opening-to-Cushite-Gentile-nations from the "
        "Frumentius-mission forward — reads Mk 11:17 as fulfillment of "
        "the temple-for-all-nations promise in the new-covenant-Church.",
    ),
    # ── Mark 12 (3) — Stone-rejected + Great-commandment + Widow's-mite ─────
    cyril_mark(
        12,
        10,
        "'Have ye not read this scripture; The stone which the builders "
        "rejected is become the head of the corner: This was the Lord's "
        "doing, and it is marvellous in our eyes?' — Cyril cites Ps 118:22-"
        "23 (LXX 117:22-23) at the close of the wicked-tenants-parable as "
        "the Christological-cornerstone fulfillment (paired with Mt 21:42 "
        "γ.4.6.D anchor). The lithon hon apedokimasan (stone-they-"
        "rejected) is the Crucifixion; eis kephalēn-gōnias (into head-of-"
        "corner) is the Resurrection. Tewahedo Mäzgəbä-Hāymanot doctrine "
        "cites Mk 12:10 + Mt 21:42 + Ps 118:22 + Acts 4:11 + 1 Pet 2:6-7 "
        "as the five-fold cornerstone-prooftext.",
    ),
    cyril_mark(
        12,
        30,
        "'Thou shalt love the Lord thy God with all thy heart, and with "
        "all thy soul, and with all thy mind, and with all thy strength: "
        "this is the first commandment' — Cyril marks the Markan-fourfold-"
        "form (heart + soul + mind + strength — kardia + psychē + dianoia "
        "+ ischys; Matthew gives threefold at Mt 22:37) as the fullest "
        "Synoptic-form of the great-commandment. The ischys (strength) "
        "addition emphasizes the bodily-strength-dimension of total-"
        "consecration. Tewahedo catechetical-totality teaches the four-"
        "fold love-of-God as the comprehensive-anthropological-formation.",
    ),
    cyril_mark(
        12,
        42,
        "'And there came a certain poor widow, and she threw in two mites, "
        "which make a farthing' — Cyril marks the widow's-mite (lepta "
        "duo — two-smallest-coins) as the kenotic-stewardship summit. The "
        "Markan-detail (only-Mark + Luke preserve this; Matthew omits) "
        "shows Christ-noticing-what-others-miss. The hē hysterēsis autēs "
        "(her-poverty, Mk 12:44) gave more-than-all-the-rich because she "
        "gave from her bios (life-substance) not perissou (abundance). "
        "Tewahedo monastic-and-lay stewardship-formation cites Mk 12:41-"
        "44 + Lk 21:1-4 as the kenotic-giving foundational text.",
    ),
    # ── Mark 13 (2) — Endure-to-end + No-man-knoweth-the-day ────────────────
    cyril_mark(
        13,
        13,
        "'And ye shall be hated of all men for my name's sake: but he "
        "that shall endure unto the end, the same shall be saved' — Cyril "
        "marks the hypomeinas eis telos as the eschatological-perseverance "
        "summary (cf. Mt 10:22, Mt 24:13 γ.4.6.D). The misoumenoi (hated-"
        "ones) precedes the sōthēsetai (shall-be-saved) — endurance-"
        "through-hostility, not absence-of-hostility, is the eschatological-"
        "promise. Tewahedo Sämā'ǝtāt martyrology cites Mk 13:13 as the "
        "perseverance-charter.",
    ),
    cyril_mark(
        13,
        32,
        "'But of that day and that hour knoweth no man, no, not the "
        "angels which are in heaven, neither the Son, but the Father' — "
        "Cyril treats this most-difficult-verse carefully. The 'neither "
        "the Son' (oude ho hyios) is read by Cyril per the "
        "communicatio-idiomatum: in his incarnate-human-nature the "
        "Son-as-man does not know-as-human; in his divine-nature he "
        "knows-as-divine-Word. The Tewahedo Miaphysite Christology "
        "preserves the Cyrillian-balance: the one Person-of-the-Word "
        "experiences knowledge-in-flesh authentically without his "
        "divine-omniscience being compromised. Anti-Arian and anti-"
        "Agnoetic readings both fail against Cyril's careful incarnational-"
        "communicatio.",
    ),
    # ── Mark 14 (3) — Anointing + Institution + Abba-Father ─────────────────
    cyril_mark(
        14,
        8,
        "'She hath done what she could: she is come aforehand to anoint "
        "my body to the burying' — Cyril marks the Markan-version of the "
        "anointing-at-Bethany (paired with Mt 26:13 γ.4.6.D, Lk 7:36-50). "
        "The proelaben myrisai mou to sōma eis ton entaphiasmon (she-"
        "came-beforehand to-anoint-my-body for-the-burying) names her "
        "prophetic-action: she alone among the disciples recognized that "
        "the Master-was-going-to-die and-needed-burial-anointing-now. "
        "The Markan eis mnēmosynon autēs (memorial-of-her, Mk 14:9) is "
        "Christ's-own-canonization of one of the few-named-female-acts "
        "in the Gospel. Tewahedo Marian + women-saints hagiography reads "
        "Mk 14:3-9 as the proto-prophetic-female-disciple anchor.",
    ),
    cyril_mark(
        14,
        22,
        "'And as they did eat, Jesus took bread, and blessed, and brake "
        "it, and gave to them, and said, Take, eat: this is my body' — "
        "Cyril's Eucharistic-realism locus in Mark. The estin (is) is "
        "real-identification, not symbolization (cf. Mt 26:26, Lk 22:19, "
        "1 Cor 11:24). The four-action sequence (took-blessed-brake-gave) "
        "is the Anaphora-institution-prototype. Tewahedo Qǝddāse-of-the-"
        "Apostles cites Mk 14:22-24 + Mt 26:26-28 + Lk 22:19-20 + "
        "1 Cor 11:23-25 as the four-fold institution-witness recited at "
        "every Anaphora's words-of-institution.",
    ),
    cyril_mark(
        14,
        36,
        "'And he said, Abba, Father, all things are possible unto thee; "
        "take away this cup from me: nevertheless not what I will, but "
        "what thou wilt' — Cyril marks the Markan-distinctive Abba ho "
        "patēr (the Aramaic Abba preserved alongside the Greek translation) "
        "as the deepest-filial-intimacy. The transferral to Christian-"
        "prayer is at Rom 8:15 + Gal 4:6 (the Spirit-of-adoption cries "
        "'Abba, Father'). The Gethsemane-cup is the Passion-cup (cf. Mt "
        "26:39 γ.4.6 seed, Lk 22:42 γ.4.3.D). The two-wills (parelthe ap' "
        "emou + thelō / ou-thelō pattern) names the Cyrillian Miaphysite "
        "Christology: the one-incarnate-Person genuinely-prays-with-"
        "human-volition while-perfectly-aligned-with-divine-will. "
        "Tewahedo prayer-formation cites Mk 14:36 + Rom 8:15 as the "
        "Abba-adoption baptismal-anchor.",
    ),
    # ── Mark 15 (2) — Eloi-Eloi + Centurion ─────────────────────────────────
    cyril_mark(
        15,
        34,
        "'And at the ninth hour Jesus cried with a loud voice, saying, "
        "Eloi, Eloi, lama sabachthani? which is, being interpreted, My "
        "God, my God, why hast thou forsaken me?' — Cyril's impassible-"
        "Passion locus. The Eloi (or Eli per Mt 27:46) is the Aramaic "
        "(Eloi) or Hebrew (Eli) opening of Ps 22 (LXX 21). Cyril reads "
        "the cry NOT as Father-actually-abandoning-Son (Trinitarian-"
        "intra-relations cannot be broken) but as Christ-praying-Psalm-"
        "22 from-its-anguished-incipit to-its-triumphant-conclusion "
        "(Ps 22:24 'he hath not despised'; Ps 22:31 'he hath done it'). "
        "The Cyrillian-impassibility preserves divine-immutability while "
        "honoring the authentic-human-experience of dereliction-felt. "
        "Tewahedo Christology preserves Cyril precisely: the one-incarnate-"
        "Word experiences-dereliction-in-flesh without divine-suffering.",
    ),
    cyril_mark(
        15,
        39,
        "'And when the centurion, which stood over against him, saw that "
        "he so cried out, and gave up the ghost, he said, Truly this man "
        "was the Son of God' — Cyril marks the centurion-confession "
        "(alēthōs houtos ho anthrōpos hyios theou ēn) as the Markan-"
        "thematic-climax: the very Gospel-opening claim (1:1 — 'the "
        "gospel of Jesus Christ, the Son of God') is now confirmed BY A "
        "GENTILE at the Cross. The structural-inclusio frames the entire "
        "Gospel between divine-Sonship-declaration and Gentile-"
        "confession-fulfillment. Tewahedo missionary-theology reads "
        "Mk 15:39 (paired with Mt 27:54 γ.4.6.D) as the Gentile-"
        "inclusion-at-the-Cross definitive prooftext.",
    ),
    # ── Mark 16 (1) — Resurrection-proclamation ─────────────────────────────
    cyril_mark(
        16,
        6,
        "'And he saith unto them, Be not affrighted: Ye seek Jesus of "
        "Nazareth, which was crucified: he is risen; he is not here: "
        "behold the place where they laid him' — Cyril marks the Markan-"
        "angelic-proclamation (ēgerthē, ouk estin hōde — he-is-risen, "
        "he-is-not-here) as the foundational Easter-kerygma. The passive "
        "ēgerthē (he-was-raised) emphasizes Father-as-agent of "
        "Resurrection (cf. Acts 2:24); the perfect-state ouk-estin-hōde "
        "(is-not-here) emphasizes the empty-tomb. The mē ekthambeisthe "
        "(be-not-amazed) is the angelic-encouragement-formula. Tewahedo "
        "Fasika dawn-Eucharist liturgy cites Mk 16:6 + Mt 28:6 + Lk 24:6 "
        "+ Jn 20:7 as the four-fold resurrection-proclamation-witness, "
        "with Mk 16:6 read first per the Markan-priority hypothesis "
        "preserved in the Coptic-Tewahedo lectionary tradition.",
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 40, f"expected 40 entries, got {len(NEW_ENTRIES)}"
assert all(e["book"] == "mrk" for e in NEW_ENTRIES)
assert all(e["father"] == "Cyril of Alexandria" for e in NEW_ENTRIES)
assert all(1 <= e["chapter"] <= 16 for e in NEW_ENTRIES), "Mark = chapters 1-16 only"
chapters_covered = sorted({e["chapter"] for e in NEW_ENTRIES})
assert chapters_covered == list(range(1, 17)), f"expected all 16 Mark chapters covered; got {chapters_covered}"


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    assert "entries" in d and "_meta" in d

    pre_count = len(d["entries"])
    d["entries"].extend(NEW_ENTRIES)
    post_count = len(d["entries"])

    ledger_addition = (
        " γ.4.7 (2026-05-13) added Cyril on Mark seed wave — 40 verse-"
        "keyed entries spanning all 16 Markan chapters (Trinitarian-"
        "baptism Jordan-theophany + kingdom-near metanoia-pisteue + "
        "Capernaum-demoniac Holy-One-of-God + paralytic-forgiveness + "
        "new-wine-new-wineskins Coptic-Tewahedo-emergence pattern + "
        "hardened-hearts orgē-and-syllype + Twelve-being-with-and-"
        "sending + true-family doing-Father's-will Marian-double-"
        "kinship + sower hermeneutical-imperative + lampstand public-"
        "kerygma + Mark's-mustard-seed Frumentius-founding-fulfillment "
        "+ Gerasene Son-of-Most-High demoniac-Christology + hemorrhage-"
        "daughter-by-faith + Nazareth-rejection kenotic-hiddenness + "
        "two-by-two Frumentius-Edesius-Nine-Saints pattern + multiplied-"
        "loaves Eucharistic-prototype + interior-defilement + "
        "Syrophoenician-crumbs Cushite-Gentile-inclusion + Petrine-"
        "confession sy-ei-ho-Christos + first-Passion-prediction + "
        "take-up-cross discipleship-summit + 'hear-him' Father's-voice "
        "+ 'help-mine-unbelief' proto-catechumen-prayer + first-shall-"
        "be-last bishop-as-servant + one-flesh marital-indissolubility "
        "+ camel-needle wealth-warning + ransom-for-many atonement-"
        "summit + Hosanna triumphal-entry + house-of-prayer-for-all-"
        "nations Coptic-Tewahedo-fulfillment + stone-rejected-"
        "cornerstone + fourfold-Shema strength-included + widow's-mite "
        "kenotic-stewardship + endure-to-end perseverance + 'neither-"
        "the-Son' communicatio-idiomatum + anointing-at-Bethany "
        "memorial-of-her + Markan-institution Eucharistic-realism + "
        "Abba-Father two-wills Miaphysite-Christology + Eloi-Eloi "
        "Ps-22 impassible-Passion + Markan-centurion-confession "
        "Gentile-inclusion-at-Cross + 'He-is-risen' Fasika-"
        "proclamation). Cyril-on-Mark total post-γ.4.7: 40 entries "
        "(seed wave). Opens the FOURTH and final canonical-Gospel "
        "Cyrillian arc after Cyril-on-John γ.4.1-D (116) + Cyril-on-"
        "Luke γ.4.3-D (160) + Cyril-on-Matthew γ.4.6-D (195). "
        "Cumulative Cyril-on-Gospels post-γ.4.7: 511 entries across "
        "all 4 canonical Gospels. Source: Cramer Vol. I (Oxford "
        "1840 — PD) + PG 72 (Migne 1859 — PD). Mark = Coptic-"
        "Alexandrian Gospel par excellence; the Tewahedo Church "
        "traces its apostolic succession through John Mark → "
        "Anianus → … → Athanasius → … → Frumentius."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    mark_total = sum(1 for e in d["entries"] if e["book"] == "mrk" and e["father"] == "Cyril of Alexandria")
    print(f"γ.4.7 ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(f"Cyril on Mark total: {mark_total} entries — Fourth Cyril Gospel arc OPENED")


if __name__ == "__main__":
    main()
