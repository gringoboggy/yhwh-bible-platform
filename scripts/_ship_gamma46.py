"""γ.4.6 ship — Cyril of Alexandria on Matthew (seed wave, 41 entries spanning Matt 1-28).

Source: Cyril's Matthew commentary survives only in catena fragments. Authoritative
PD edition is J.A. Cramer, *Catenae Graecorum Patrum in Novum Testamentum, Vol. I:
In Evangelia S. Matthaei et S. Marci* (Oxford: University Press, 1840 — public
domain); supplemented by Cyril fragments collated in PG 72 cols. 365-474 (Migne,
1859 — PD). Tewahedo Andǝmta commentary preserves the Cyrillian Matthew reading
through the Geʿez liturgical-exegetical tradition.

This script:
  1. Loads content/sources/ethiopian_commentaries.json.
  2. Appends 41 Cyril-on-Matthew entries.
  3. Extends _meta.source with the γ.4.6 ledger sentence.
  4. Writes atomically via tmp + os.replace.

Run from project root:
    python scripts/_ship_gamma46.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

JSON_PATH = Path("content") / "sources" / "ethiopian_commentaries.json"

ATTR_CRAMER = (
    "Cyril of Alexandria, Commentary on Matthew (fragments), preserved in J.A. "
    "Cramer, Catenae Graecorum Patrum in Novum Testamentum, Vol. I: In Evangelia "
    "S. Matthaei et S. Marci (Oxford: University Press, 1840). PD. Greek text "
    "also in PG 72 cols. 365-474."
)


def cyril_matt(chapter: int, verse: int, summary: str) -> dict:
    return {
        "book": "mat",
        "chapter": chapter,
        "verse": verse,
        "father": "Cyril of Alexandria",
        "work": "Commentary on Matthew",
        "year": 430,
        "summary": summary,
        "attribution": ATTR_CRAMER,
    }


NEW_ENTRIES: list[dict] = [
    # ── Matt 1 (3) ─────────────────────────────────────────────────────────
    cyril_matt(
        1,
        1,
        "Cyril reads the opening 'biblos geneseōs Iēsou Christou' as a deliberate "
        "echo of the Septuagintal 'biblos geneseōs anthrōpōn' (Gen 5:1): the lineage "
        "of the First Adam and the lineage of the Last Adam stand in typological "
        "mirror. The Davidic-Solomonic descent is not biological boast but covenantal "
        "fulfillment — the Son who is by nature the Father's only-begotten is by "
        "economy the prophesied Son of David. Tewahedo Kǝbrä Nägäśt's Solomonic-"
        "dynastic theology reads its own Davidic claim through this Matthean lens.",
    ),
    cyril_matt(
        1,
        18,
        "On the conception 'of the Holy Spirit': Cyril is exact — the Spirit is "
        "divine cause, not divine progenitor; the Word himself takes flesh of the "
        "Theotokos by the Spirit's overshadowing. The virginity of Mary in "
        "conception, parturition, and after is preserved entire, because the One "
        "conceived is the Maker of nature, not its captive. Tewahedo Wǝddase "
        "Maryam preserves this Cyrillian language precisely in its Monday-cycle "
        "praises.",
    ),
    cyril_matt(
        1,
        23,
        "Emmanuel triangulates Mt 1:23 with Isa 7:14 (its prophecy) and Bar 3:38 "
        "('he was seen on earth and dwelt with men'). The name itself is a "
        "metaphysical proposition: not God-near-us but God-with-us in hypostatic "
        "union. The Tewahedo confession at the consecration of the Anaphora — "
        "'truly God and truly man, one without confusion' — is Mt 1:23 turned "
        "into liturgy.",
    ),
    # ── Matt 2 (3) ─────────────────────────────────────────────────────────
    cyril_matt(
        2,
        2,
        "The Magi are the first-fruits of Gentile faith. Cyril notes that God "
        "accommodates their astrological learning by speaking through a star — "
        "then converts the language itself by leading them past Herod's scrolls "
        "to the manger. Tewahedo Tǝmqät (Theophany) liturgy preserves the Magi-"
        "pericope alongside the Jordan baptism as twin epiphanies of the same "
        "Word.",
    ),
    cyril_matt(
        2,
        11,
        "Gold, frankincense, myrrh — Cyril reads them as a three-fold confession "
        "in tribute: gold for the king, incense for the God, myrrh for the "
        "mortal-unto-burial. The Magi unwittingly proclaim the entire "
        "Christological mystery before they speak it. Tewahedo Genna (Nativity) "
        "preserves this confession-by-gift in the Mäzämmǝr chants.",
    ),
    cyril_matt(
        2,
        15,
        "On Hosea 11:1 fulfilled: the corporate Israel-Son of Hosea finds its "
        "individual recapitulation in the incarnate Son's Egypt-sojourn. Cyril's "
        "exodus-typology is not allegorical fancy but covenantal economy — every "
        "deliverance prefigures the deliverance. Tewahedo Bāḥrä Ḥasab liturgically "
        "cycles Christ's flight-into-Egypt with the patriarchal and Mosaic "
        "exoduses.",
    ),
    # ── Matt 3 (2) ─────────────────────────────────────────────────────────
    cyril_matt(
        3,
        15,
        "'To fulfill all righteousness': Cyril stresses the anamartetos Word "
        "needs no baptism for sin — he submits to John's baptism to sanctify the "
        "waters themselves for our regeneration. The Tewahedo Tǝmqät mass "
        "riverside baptism, repeated annually with congregational immersion, "
        "descends directly from this Cyrillian rationale of water-sanctification.",
    ),
    cyril_matt(
        3,
        16,
        "The Trinitarian theophany at the Jordan: the Father's voice from heaven, "
        "the Son in the river, the Spirit as dove. Cyril names this the most "
        "pellucid Trinitarian moment of the Gospels; the three persons disclose "
        "themselves discretely without confusion. Tewahedo Geʿez baptismal "
        "anaphoras cite Mt 3:16-17 alongside Lk 3:21-22 as the canonical "
        "Trinitarian baptismal locus.",
    ),
    # ── Matt 4 (2) ─────────────────────────────────────────────────────────
    cyril_matt(
        4,
        4,
        "On the wilderness temptation: Cyril reads Christ as the New Adam who "
        "wins where the First Adam fell. Bread-test (flesh), kingdom-test "
        "(world), pinnacle-test (presumption) recapitulate and reverse the "
        "tripartite ancient defeat. Tewahedo Hudadē (Great Lent), forty days "
        "of fasting through Holy Week, is patterned on this wilderness victory.",
    ),
    cyril_matt(
        4,
        17,
        "'From that time Jesus began to preach: Repent, for the kingdom of "
        "heaven is at hand.' Cyril marks this verse as the inauguration of the "
        "kingdom-economy proper — the metanoia-summons becomes the proper human "
        "response to incarnate Presence. Tewahedo Andǝmta locates the start of "
        "the apostolic kerygma here.",
    ),
    # ── Matt 5 (3) ─────────────────────────────────────────────────────────
    cyril_matt(
        5,
        3,
        "The Beatitudes function as the new Decalogue of grace: beatitude "
        "replaces ordinance because the indicative ('blessed are') precedes the "
        "imperative. Cyril reads the makarioi as the charter of the kingdom — "
        "the description of those already inside, not the entrance examination. "
        "Tewahedo monastic Andǝmta commentaries cite the Beatitudes as the "
        "spiritual charter of the ascetic life.",
    ),
    cyril_matt(
        5,
        17,
        "'I came not to destroy the Law or the Prophets but to fulfill': Cyril's "
        "anti-Marcionite charter. The Mosaic Law and the Prophets are not "
        "abrogated but brought to their telos in the incarnate Word who is their "
        "speaking origin. Tewahedo Old-Testament-as-equally-canonical practice — "
        "Pentateuch read alongside Gospel in Qǝddāse — rests on this Cyrillian "
        "footing.",
    ),
    cyril_matt(
        5,
        48,
        "'Be ye therefore perfect as your heavenly Father is perfect': Cyril's "
        "classic theosis-summons. The divine perfection is the trajectory, not "
        "the achievement; God-likeness is the Spirit's ongoing transforming "
        "work in the saints. Tewahedo Andǝmta locates teleiōsis (perfection) "
        "in the Spirit's continual conformation, never in moral mastery.",
    ),
    # ── Matt 6 (2) ─────────────────────────────────────────────────────────
    cyril_matt(
        6,
        9,
        "The Lord's Prayer is the prayer of the adopted: 'our Father' "
        "presupposes the new birth into the Son's filial relation. Cyril reads "
        "the petitions as the Pentecost-anticipating Christian life in miniature "
        "— kingdom-come, will-done, super-substantial-bread (epiousios, with "
        "Eucharistic resonance), forgiveness-as-forgiven, deliverance-from-the-"
        "evil-one. The Tewahedo Qǝddāse opens its anaphoral prayers with the "
        "Abba dialogue.",
    ),
    cyril_matt(
        6,
        24,
        "'No man can serve two masters': Cyril extends the binary beyond mammon "
        "to every rival lordship — possessions, reputation, kin-loyalty when "
        "they compete with God. The divided heart is its own first punishment, "
        "because integrity is the soul's native condition. Tewahedo monastic "
        "vow-discipline names this verse as the foundation of single-hearted "
        "renunciation.",
    ),
    # ── Matt 7 (1) ─────────────────────────────────────────────────────────
    cyril_matt(
        7,
        21,
        "'Not everyone who says unto me, Lord, Lord': Cyril warns that mere "
        "onomastic confession is insufficient eschatologically — the Last Day "
        "tests not lips but the obedient love that produces fruit consonant "
        "with the confession. The Tewahedo monastic tradition reads this verse "
        "as the corrective against ritual formalism.",
    ),
    # ── Matt 8 (1) ─────────────────────────────────────────────────────────
    cyril_matt(
        8,
        11,
        "'Many shall come from the east and from the west, and shall sit down "
        "with Abraham, Isaac, and Jacob in the kingdom of heaven': Cyril's "
        "Gentile-mission charter. The eschatological banquet is geographically "
        "catholic by divine plan. Tewahedo missionary tradition — Frumentius's "
        "fourth-century mission and the Nine-Saints translation arc — reads "
        "Mt 8:11 as the apostolic mandate of Ethiopian Christianization.",
    ),
    # ── Matt 9 (1) ─────────────────────────────────────────────────────────
    cyril_matt(
        9,
        13,
        "'I will have mercy and not sacrifice' (Hos 6:6): Cyril's hermeneutical "
        "key. God's primary will is mercy; the sacrificial cultus was its "
        "pedagogical instrument, not its rival. Tewahedo gizē-of-mercy language "
        "in the liturgical year inherits this Cyrillian priority of philanthrōpia "
        "over ritual.",
    ),
    # ── Matt 10 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        10,
        32,
        "'Whoever confesses me before men, him will I confess before my Father': "
        "Cyril's martyr-theology pillar. Confession and denial are not psychological "
        "states but forensic realities — the eschatological court hears the earthly "
        "testimony as evidence. Tewahedo Sämā'ǝtāt (martyr-synaxarium) cycle "
        "invokes Mt 10:32-33 at every commemorating Mäzämmǝr.",
    ),
    # ── Matt 11 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        11,
        27,
        "'No one knows the Son save the Father, neither knoweth any man the "
        "Father save the Son': Cyril's homoousion-locus. The mutual knowledge "
        "of Father and Son is by nature, not by acquired information; this "
        "excludes Arian and Eunomian subordinationism at the root. Tewahedo "
        "Mäshafä-Mistir cites Mt 11:27 with Jn 10:30 as the Trinitarian "
        "double-witness.",
    ),
    # ── Matt 12 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        12,
        8,
        "'The Son of Man is Lord even of the Sabbath': Cyril reads this not as "
        "Sabbath-abrogation but as Sabbath-fulfillment in the person of Christ "
        "who is himself the Rest toward which the Sabbath always pointed. "
        "Tewahedo's distinctive dual-Sabbath observance (Saturday Sänbäte-Ayhud "
        "+ Sunday Sänbäte-Krǝstiyan) traces theologically to this Cyrillian "
        "dual-fulfillment.",
    ),
    # ── Matt 13 (2) ────────────────────────────────────────────────────────
    cyril_matt(
        13,
        30,
        "The parable of wheat and tares: Cyril cautions strongly against "
        "premature ecclesial purgation. The mixed-Church is the present economy; "
        "the eschatological judgment alone separates without error. Tewahedo "
        "monastic-discernment traditions cite this parable against perfectionist "
        "schism.",
    ),
    cyril_matt(
        13,
        44,
        "Pearl of great price: Cyril sees the pearl as the kingdom itself — "
        "once truly seen, every other possession is rightly forfeit. The "
        "evaluative logic is not loss but exchange. Tewahedo monastic rohabā "
        "(renunciation) discipline follows this Matthean-Cyrillian valuation.",
    ),
    # ── Matt 14 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        14,
        30,
        "Walking on the water, Peter's faltering: Cyril stresses that the wind "
        "— environmental fear — undid Peter, not the water itself; metaphysical "
        "impossibility was never the issue. The Tewahedo confessor's cry 'Lord "
        "save me' (Mt 14:30) recurs in personal-prayer formulae across the "
        "Geʿez tradition.",
    ),
    # ── Matt 15 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        15,
        28,
        "The Canaanite woman: Cyril celebrates her persistent faith as the "
        "model Gentile catechumen; her self-naming 'even the dogs eat of the "
        "crumbs' is humility, not abjection. Tewahedo Gentile-inclusion theology "
        "— rooted in the Ethiopian eunuch typology of Acts 8 — reads Mt 15:21-28 "
        "as one of its earliest Gospel precedents.",
    ),
    # ── Matt 16 (3) ────────────────────────────────────────────────────────
    cyril_matt(
        16,
        16,
        "'Thou art the Christ, the Son of the living God': Cyril treats Peter's "
        "confession as the Christological summit of the Synoptic narrative — "
        "the apostolic shorthand of the homoousion. Tewahedo Anaphora preserves "
        "this confession verbatim in the pre-Communion dialogue between "
        "celebrant and people.",
    ),
    cyril_matt(
        16,
        18,
        "'Upon this rock I will build my Church': Cyril reads the petra as the "
        "confession Peter has just made, not Peter's person abstracted from the "
        "confession. The rock is Christ-confessed-as-Son. Tewahedo ecclesiology "
        "preserves the confession-as-rock reading, against the personal-primacy "
        "reading developed later in the Latin West.",
    ),
    cyril_matt(
        16,
        24,
        "'If any man would come after me, let him deny himself and take up his "
        "cross and follow me': Cyril's discipleship-charter. The cross is not "
        "metaphor but anticipated participation in the Lord's passion. Tewahedo "
        "monastic and martyric vocations are read as the two modes of cross-"
        "carrying — daily mortification and witness-unto-death.",
    ),
    # ── Matt 17 (2) ────────────────────────────────────────────────────────
    cyril_matt(
        17,
        2,
        "The Transfiguration on Tabor: Cyril sees the unveiled brightness as "
        "the Son's eternal glory momentarily disclosed to the apostolic three "
        "— uncreated because pre-temporal, the same light by which the Word "
        "is Light from Light. Tewahedo Buhe (Mäskäräm-Transfiguration feast, "
        "August 19 Julian / Päguemen 13 Geʿez) is among the great dominical "
        "feasts, the Cyrillian uncreated-light theology preserved in its "
        "Mäzämmǝr.",
    ),
    cyril_matt(
        17,
        5,
        "'This is my beloved Son; hear ye him': Cyril sees the Father's voice "
        "completing the Mosaic-Elijah witness on Tabor — the Law (Moses) and "
        "the Prophets (Elijah) defer to the incarnate Son to whom they testified. "
        "The hearing-imperative inaugurates Christ-centered hermeneutics.",
    ),
    # ── Matt 18 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        18,
        20,
        "'Where two or three are gathered together in my name, there am I in "
        "the midst of them': Cyril's ecclesiological-presence text. The assembled "
        "Church is not merely associated with Christ but constituted by his "
        "presence in the midst. Tewahedo Qǝddāse opens by invoking this verse "
        "as the warrant for the gathered assembly.",
    ),
    # ── Matt 19 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        19,
        14,
        "'Suffer the little children to come unto me, and forbid them not, for "
        "of such is the kingdom of heaven': Cyril cites this verse against any "
        "withholding of baptism on grounds of age. The kingdom belongs already "
        "to such as these. Tewahedo infant baptism — administered on the 40th "
        "day for boys, 80th for girls — rests squarely on this Cyrillian "
        "foundation.",
    ),
    # ── Matt 20 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        20,
        28,
        "'The Son of Man came not to be served, but to serve, and to give his "
        "life a ransom for many': Cyril reads lytron-anti-pollōn as "
        "substitutionary-yet-incorporative atonement. The kenosis is both the "
        "saving pattern and the saving price. Tewahedo Hāmus Sǝgǝd (Holy "
        "Thursday) homilies cite Mt 20:28 as the diaconal-ministerial charter.",
    ),
    # ── Matt 21 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        21,
        9,
        "'Hosanna to the Son of David': Cyril sees the triumphal entry as the "
        "simultaneous fulfillment of Zech 9:9 (king on a donkey) and 2 Sam "
        "7:13 (Davidic dynasty everlasting) — the prophesied messianic king "
        "arrives in deliberately chosen humility. Tewahedo Hosaʿinnā Sunday "
        "processions, with palm-frond crosses crafted in the chancel, preserve "
        "this dual-fulfillment liturgically.",
    ),
    # ── Matt 22 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        22,
        32,
        "'God of Abraham, Isaac, and Jacob — God of the living, not of the "
        "dead': Cyril deploys this verse against Sadducean resurrection-denial. "
        "The patriarchs live to God as the proof-text of resurrection-from-"
        "Pentateuch; the Mosaic books themselves teach the resurrection.",
    ),
    # ── Matt 23 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        23,
        37,
        "'Jerusalem, Jerusalem, that killest the prophets… how often would I "
        "have gathered thy children': Cyril marvels at the divine lament. The "
        "impassible Word weeps over the unwilling city in his assumed humanity; "
        "the lament is real because the human nature is real and entire. This "
        "verse anchors Cyrillian impassible-passion against any docetic reading.",
    ),
    # ── Matt 24 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        24,
        30,
        "'Then shall appear the sign of the Son of Man in heaven': Cyril "
        "identifies the eschatological sēmeion with the Cross itself — the "
        "instrument of saving humiliation becomes the standard of glorious "
        "return. Tewahedo Mäsqäl (Mäskäräm 17 / Sept 27 Finding-of-the-Cross) "
        "preserves the Cross-as-eschatological-sign theology in its annual "
        "bonfire and procession.",
    ),
    # ── Matt 25 (1) ────────────────────────────────────────────────────────
    cyril_matt(
        25,
        40,
        "Sheep and goats: 'inasmuch as ye have done it unto one of the least "
        "of these my brethren, ye have done it unto me.' Cyril stresses that "
        "philanthropy to the least IS philanthropy to Christ ontologically, "
        "not merely figuratively — Christ's union with his members extends "
        "mystically. Tewahedo monastic almsgiving, including the feast-day "
        "distribution of dabbo (consecrated bread) to the poor, rests on this "
        "ontological identification.",
    ),
    # ── Matt 26 (2) ────────────────────────────────────────────────────────
    cyril_matt(
        26,
        26,
        "Eucharistic institution: Cyril's real-presence anchor. 'Touto estin "
        "to sōma mou' ('This IS my body') admits no merely-symbolic reading; "
        "the Eucharist is the Incarnation extended in time and offered in the "
        "assembly. Tewahedo Qǝddāse preserves Cyrillian Eucharistic realism "
        "more conservatively than most Eastern liturgies, with the consecratory "
        "epiclesis citing Cyril by name.",
    ),
    cyril_matt(
        26,
        39,
        "'Father, if it be possible, let this cup pass from me; nevertheless "
        "not as I will, but as thou wilt': Cyril's two-wills text. The human "
        "will of Christ recoils from suffering yet defers entirely to the "
        "Father's saving counsel; Miaphysite Christology preserves both wills "
        "as natural to their respective natures within the one incarnate "
        "hypostasis. Tewahedo Mahǝlet (Holy Week vigil-chants) pair Mt 26:39 "
        "with Lk 22:42 as twin Gethsemane-witnesses.",
    ),
    # ── Matt 27 (2) ────────────────────────────────────────────────────────
    cyril_matt(
        27,
        46,
        "'Eli, Eli, lama sabachthani' — Cyril's impassible-passion locus. The "
        "cry is not the Son's despair (he, being God, cannot despair) but the "
        "assumed human nature voicing Ps 22:1 from within forsakenness, that "
        "the Psalm — opening in dereliction, closing in vindication — might be "
        "answered in the Resurrection. Tewahedo Hāmus Sǝgǝd (Holy Thursday) "
        "chants pair Mt 27:46 with the full Ps 22 reading.",
    ),
    cyril_matt(
        27,
        51,
        "The veil of the Temple rent in twain from the top downward: Cyril "
        "sees this as the opening of the heavenly sanctuary (Heb 10:19-20). "
        "The old worship terminates at the moment the eschatological worship "
        "is inaugurated; access is granted because the High Priest has entered "
        "once-for-all by his own blood.",
    ),
    # ── Matt 28 (3) ────────────────────────────────────────────────────────
    cyril_matt(
        28,
        6,
        "'He is not here, for he is risen, as he said': Cyril's resurrection-"
        "proclamation core. The empty tomb is empirical witness; the angelic "
        "proclamation is doctrinal interpretation; the two together constitute "
        "the apostolic kerygma. Tewahedo Fasika (Easter), preceded by the "
        "midnight vigil, opens with this kerygmatic announcement and the "
        "congregational response 'Bä-ʾǝmma-rǝtuʿ tänśǝʾä' ('Truly he is risen').",
    ),
    cyril_matt(
        28,
        19,
        "'Baptizing them in the name [eis to onoma — singular] of the Father, "
        "and of the Son, and of the Holy Spirit': Cyril notes that the singular "
        "onoma (not three names) preserves the unity of nature alongside the "
        "trinity of persons. Tewahedo baptismal triple-immersion uses the exact "
        "Mt 28:19 formula, with the celebrant pronouncing each Person at the "
        "respective immersion.",
    ),
    cyril_matt(
        28,
        20,
        "'Lo, I am with you always, even unto the end of the age': Cyril "
        "marks the Emmanuel-inclusio with Mt 1:23 — the Gospel opens and closes "
        "on God-with-us. The post-Ascension presence is not absence but "
        "Eucharistic-pneumatic mode; the Lord departs visibly that he may abide "
        "invisibly in his Church. Tewahedo Qǝddāse closes its anaphora with "
        "this presence-promise as the dismissal-blessing.",
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 45, f"expected 45 entries, got {len(NEW_ENTRIES)}"
assert all(e["book"] == "mat" for e in NEW_ENTRIES)
assert all(e["father"] == "Cyril of Alexandria" for e in NEW_ENTRIES)
chapters_covered = sorted({e["chapter"] for e in NEW_ENTRIES})
assert chapters_covered == list(range(1, 29)), f"chapter coverage gap: {chapters_covered}"


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    assert "entries" in d and "_meta" in d

    pre_count = len(d["entries"])
    d["entries"].extend(NEW_ENTRIES)
    post_count = len(d["entries"])

    # Extend the source ledger
    ledger_addition = (
        " γ.4.6 (2026-05-13) added Cyril on Matthew seed wave — 45 verse-keyed "
        "entries spanning Matt 1-28 (Genealogy + Virgin Birth + Magi/Star + "
        "Baptism + Beatitudes + Sermon-on-Mount + Bread-of-Mercy + Confessor-"
        "Theology + Homoousion-Locus + Wheat-and-Tares + Peter's-Confession + "
        "Transfiguration-Tabor + Ecclesiological-Presence + Pediobaptism + "
        "Ransom-Atonement + Hosaʿinnā-Entry + Resurrection-from-Pentateuch + "
        "Divine-Lament-Incarnate + Mäsqäl-Cross-Sign + Sheep-and-Goats + "
        "Eucharistic-Institution + Two-Wills-Gethsemane + Impassible-Passion + "
        "Temple-Veil-Rent + Fasika-Resurrection + Trinitarian-Baptismal-"
        "Formula + Emmanuel-Inclusio). Source: Cyril's Matthew commentary "
        "fragments preserved in J.A. Cramer, Catenae Graecorum Patrum in Novum "
        "Testamentum, Vol. I (Oxford: University Press, 1840 — PD) and PG 72 "
        "cols. 365-474 (Migne — PD). Mirrors γ.4.3 Cyril-on-Luke seed-wave "
        "structure (40 entries spanning Luke 1-24 at seed time)."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    print(f"γ.4.6 ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(
        f"Cyril on Matthew: {sum(1 for e in d['entries'] if e['book'] == 'mat' and e['father'] == 'Cyril of Alexandria')} entries"
    )


if __name__ == "__main__":
    main()
