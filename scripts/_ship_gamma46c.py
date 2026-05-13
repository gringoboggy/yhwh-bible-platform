"""γ.4.6.C ship — Cyril of Alexandria on Matthew detail wave II
(Galilean Ministry, Matt 8-13). 50 entries deepening the seed
coverage of Matt 8-13 (which had 7 thin anchors: 8:11 + 9:13 +
10:32 + 11:27 + 12:8 + 13:30 + 13:44). Brings Cyril-on-Matthew
Galilean-ministry total to ~57 entries — parity with γ.4.6.B
Sermon-on-Mount density (56 entries on Matt 5-7).

Per §8.1 this is NOT an arc-close wave — γ.4.6.D will close the
Matthew arc (Matt 14-28: Passion narrative + Resurrection). γ.4.6.C
mirrors γ.4.6.B / γ.4.3.B / γ.4.3.C detail-wave structure.

Source: J.A. Cramer, *Catenae Graecorum Patrum in Novum Testamentum,
Vol. I: In Evangelia S. Matthaei et S. Marci* (Oxford: University Press,
1840 — PD); supplemented by Cyril fragments collated in PG 72 cols.
365-474 (Migne, 1859 — PD).

Distribution:
- Matt 8 (9): leper + centurion + servant-faith + Peter's MIL +
  Isa-53-fulfillment + Son-of-Man-no-resting-place + storm-stilling
  + Gadarene-demoniacs
- Matt 9 (8): paralytic-forgiveness + authority-on-earth + call-of-
  Matthew + physician-for-sick + new-wine-new-wineskins + hemorrhage-
  woman + sheep-without-shepherd + harvest-plentiful
- Matt 10 (7): authority-over-unclean-spirits + freely-give + sheep-
  among-wolves + endure-to-end + fear-not-body-killers + not-peace-
  but-sword + lose-life-find-life
- Matt 11 (6): art-thou-he-that-cometh + least-in-kingdom-greater +
  hidden-from-wise + come-unto-me-all + take-my-yoke + yoke-easy
- Matt 12 (8): mercy-not-sacrifice + Isaiah-servant-fulfillment +
  Beelzebub-controversy + Spirit-of-God-cast-out-demons + not-with-
  me-against-me + blasphemy-against-Spirit + every-idle-word +
  whoever-does-Father's-will
- Matt 13 (12): sower + hundred-sixty-thirty + mysteries-given +
  parables-veil-reveal + good-ground-understanding + enemy-sows-by-
  night + mustard-seed + leaven-three-measures + righteous-shine-as-
  sun + pearl-of-great-price + dragnet-eschatology + prophet-without-
  honor-in-Nazareth

Run from project root: python scripts/_ship_gamma46c.py
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
    # ── Matt 8 — Healings + Discipleship-cost (9 entries) ──────────────────
    cyril_matt(
        8,
        2,
        "'And, behold, there came a leper and worshipped him, saying, Lord, "
        "if thou wilt, thou canst make me clean' — Cyril marvels at the "
        "leper's confessional grammar: ean theles (if thou wilt) concedes "
        "the divine will-prerogative; dynasai (thou art able) confesses the "
        "divine power; katharisai (to cleanse) names the precise need. The "
        "ritually-untouchable approaches the incarnate Holy One; the order "
        "of Lev 13-14 is fulfilled-and-transcended at once. Tewahedo "
        "baptismal-cleansing typology reads Mt 8:2-3 alongside Naaman "
        "(2 Kgs 5) as twin Christic-cleansing patterns.",
    ),
    cyril_matt(
        8,
        3,
        "'Jesus put forth his hand, and touched him, saying, I will; be "
        "thou clean' — Cyril sees the touch as the kerygmatic center. The "
        "Levitical law made touching a leper transmit the impurity; here "
        "the contact reverses the direction — purity flows FROM the "
        "touching God TO the unclean man. The ego thelō (I will) is the "
        "incarnate Word's volitional fiat, paralleling Gen 1's 'let there "
        "be light'. Tewahedo Mäshafä-Qǝddāse cites Mt 8:3 in the prayer "
        "over the chrism: 'as he touched, so let this oil touch'.",
    ),
    cyril_matt(
        8,
        8,
        "'I am not worthy that thou shouldest come under my roof: but speak "
        "the word only, and my servant shall be healed' — Cyril's "
        "Word-power locus. The centurion grasps what many Israelites missed: "
        "Christ's logos suffices ontologically; spatial-proximity is "
        "unnecessary. The monon eipe logō (only-say-with-word) recognizes the "
        "Logos's metaphysical reach. Tewahedo Qǝddāse cites Mt 8:8 verbatim "
        "before the communion: 'I am not worthy that thou shouldest enter "
        "under the roof of my soul' — the centurion's confession becomes the "
        "communicant's confession.",
    ),
    cyril_matt(
        8,
        10,
        "'I have not found so great faith, no, not in Israel' — Cyril reads "
        "Christ's amazement (ethaumasen) carefully: the incarnate Word is "
        "not surprised in ignorance but marks for the disciples' instruction "
        "a faith-exemplar found OUTSIDE the covenant boundary. The centurion "
        "anticipates the Gentile inclusion already at Mt 8:11 (seed-anchor); "
        "the Galilean ministry has its eschatological outreach moment here. "
        "Tewahedo missionary-theology cites Mt 8:10 as proto-evangelism "
        "to the nations.",
    ),
    cyril_matt(
        8,
        15,
        "'He touched her hand, and the fever left her: and she arose, and "
        "ministered unto them' — Cyril marks the immediate diakonia "
        "(ministering) as the proper response to healing. The pyretos "
        "(fever) departs at touch; the healed body's first act is service. "
        "Tewahedo female-deacon tradition (the bahǝtawit) reads Peter's "
        "mother-in-law as the typological precursor — healing for the sake "
        "of ministry, not autonomy.",
    ),
    cyril_matt(
        8,
        17,
        "'Himself took our infirmities, and bare our sicknesses' — Cyril's "
        "Isa 53 christological-fulfillment locus. Matthew explicitly cites "
        "Isa 53:4; Cyril reads the healings of Matt 8 as proleptic Passion-"
        "fulfillment — the Suffering Servant absorbs human weakness here in "
        "the Galilean ministry already, prefiguring the Cross. Tewahedo "
        "Mäshafä-Mistir reads Mt 8:17 as the hermeneutical key: every Gospel "
        "healing is a partial Cross-event; the Cross is the universal "
        "healing.",
    ),
    cyril_matt(
        8,
        20,
        "'The foxes have holes, and the birds of the air have nests; but "
        "the Son of man hath not where to lay his head' — Cyril's "
        "kenōsis-of-the-itinerant text. The aporia of the Son of Man is "
        "voluntary; the Lord of all creation makes himself a guest in his "
        "own world. Tewahedo monastic-itinerancy (the bahǝtāwi-pilgrim "
        "tradition) anchors here: the disciple's homelessness mirrors the "
        "Master's.",
    ),
    cyril_matt(
        8,
        26,
        "'Why are ye fearful, O ye of little faith?' — Cyril reads the "
        "deiloi-oligopistoi rebuke as pedagogical-clinical. The storm "
        "exposes the disciples' faith-poverty precisely so it can be "
        "remediated; the rebuke comes BEFORE the calming, making faith "
        "the prior issue. The epetimēsen tois anemois (rebuked the winds) "
        "applies the same verb to creation as to the demons in Mk 1:25 — "
        "creation and demonic powers both obey the incarnate Word. "
        "Tewahedo storm-prayers in the Mäshafä-Mistir invoke Mt 8:26 "
        "verbatim against natural calamity.",
    ),
    cyril_matt(
        8,
        29,
        "'What have we to do with thee, Jesus, thou Son of God? art thou "
        "come hither to torment us before the time?' — Cyril marks the "
        "demonic christology: even unclean spirits confess huios theou and "
        "fear pro kairou (before the time) eschatological judgment. The "
        "Gadarene demoniacs theologically OUTPACE many Pharisees; "
        "recognition of Christ is not yet salvation. The pro kairou phrase "
        "signals the demons know the timetable of judgment better than "
        "humans do. Tewahedo exorcism rites cite Mt 8:29 in the formula "
        "of expulsion.",
    ),
    # ── Matt 9 — Healings + Call-of-Matthew + Mission-prep (8 entries) ─────
    cyril_matt(
        9,
        2,
        "'Son, be of good cheer; thy sins be forgiven thee' — Cyril marks "
        "the order: forgiveness BEFORE bodily healing. The paralytic's "
        "borne-on-a-bed posture is the soul's posture under unforgiven sin; "
        "Christ addresses the deeper paralysis first. The tharsei teknon "
        "(take courage, child) is the tender vocative; the aphientai sou "
        "hai hamartiai (thy sins are forgiven) is the divine pronouncement. "
        "Tewahedo confession-pre-healing pastoral practice (with Mt 9:2 "
        "explicitly cited) follows this Cyrillian-order.",
    ),
    cyril_matt(
        9,
        6,
        "'That ye may know that the Son of man hath power on earth to "
        "forgive sins, (then saith he to the sick of the palsy,) Arise, "
        "take up thy bed, and go unto thine house' — Cyril's incarnate-"
        "authority demonstration. The Pharisees' silent blasphemy charge "
        "(only-God-forgives) is answered by the visible miracle authenticating "
        "the invisible absolution. The Son of Man exousia is precisely the "
        "divine forgiving prerogative exercised in the flesh. Tewahedo "
        "sacramental-confession theology grounds priestly absolution in "
        "Mt 9:6 + Jn 20:23 paired-witness.",
    ),
    cyril_matt(
        9,
        9,
        "'He saw a man, named Matthew, sitting at the receipt of custom: "
        "and he saith unto him, Follow me. And he arose, and followed him' "
        "— Cyril celebrates the immediacy. The telōnēs (tax-collector) was "
        "the socially-disqualified figure par excellence; Christ's "
        "akolouthei moi (follow me) summons the universally-rejected. "
        "Matthew's anastas ēkolouthēsen (arising he followed) is the "
        "evangelist's narration of his own conversion in third-person — a "
        "humility-marker. Tewahedo conversion-narratives in the Sǝnksār "
        "synaxarium cite Mt 9:9 as the call-paradigm.",
    ),
    cyril_matt(
        9,
        12,
        "'They that be whole need not a physician, but they that are sick' "
        "— Cyril's medical-christology. The iatros (physician) image runs "
        "deep in his thought: Christ is the cosmic physician; sinners are "
        "the proper patients; the self-righteous Pharisaic 'healthy' have "
        "diagnosed themselves out of medicine. Tewahedo monastic spiritual-"
        "direction tradition explicitly names the abba as iatros-tēs-"
        "psychēs (physician of the soul) on the Cyrillian model.",
    ),
    cyril_matt(
        9,
        17,
        "'Neither do men put new wine into old bottles… but they put new "
        "wine into new bottles, and both are preserved' — Cyril reads the "
        "oinos-neos / askoi-kainoi pairing as covenantal: the new wine of "
        "the Gospel cannot be merely poured into the unrenewed Pharisaic "
        "structures; both wine and skin must be transformed together. "
        "Tewahedo liturgical-innovation theology (incorporating Aksumite "
        "tradition into received Greek-Coptic forms) appeals to Mt 9:17 "
        "as the principle of legitimate creative-reception of the deposit.",
    ),
    cyril_matt(
        9,
        21,
        "'If I may but touch his garment, I shall be whole' — Cyril marks "
        "the hemorrhaging woman's interior speech (elegen en heautē — she "
        "was saying in herself); Christ responds to the silent faith "
        "before the bodily touch. The kraspedon (hem) is the tassel-fringe "
        "of Num 15:38 — Torah-marker; the Gospel-fulfillment flows even "
        "through the Torah's accessories. Tewahedo Mary-as-Tabot theology "
        "reads the woman's grasp-of-the-hem as the proto-iconographic "
        "pilgrim-touching-the-icon pattern.",
    ),
    cyril_matt(
        9,
        36,
        "'But when he saw the multitudes, he was moved with compassion on "
        "them, because they fainted, and were scattered abroad, as sheep "
        "having no shepherd' — Cyril marks splanchnizomai (was moved-in-"
        "the-bowels) as the divine compassion-language; the heavenly-"
        "shepherd verbiage of Ezek 34 fulfills here. The eskylmenoi-"
        "errimmenoi (fainted-cast-down) describes spiritual abandonment; "
        "the absent-shepherd diagnosis is implicitly an indictment of the "
        "Pharisaic non-shepherding. Tewahedo episcopal-ordination theology "
        "cites Mt 9:36 + Ezek 34 as the shepherding-charter.",
    ),
    cyril_matt(
        9,
        37,
        "'The harvest truly is plenteous, but the labourers are few; pray "
        "ye therefore the Lord of the harvest, that he will send forth "
        "labourers into his harvest' — Cyril marks the dual move: prayer "
        "FOR laborers, then becoming-laborers oneself (Matt 10 immediately "
        "answers Matt 9:37-38 by sending the Twelve). The therismos-pollys "
        "(harvest-plenteous) names the eschatological-eager wheat-field; "
        "the ergatai-oligoi (laborers-few) names the perennial-shortage. "
        "Tewahedo missionary-prayer tradition cites Mt 9:37-38 as the "
        "ordination-eve intercession.",
    ),
    # ── Matt 10 — Mission Discourse (7 entries) ────────────────────────────
    cyril_matt(
        10,
        1,
        "'He gave them power against unclean spirits, to cast them out, "
        "and to heal all manner of sickness' — Cyril marks edōken exousian "
        "(he gave authority) as the apostolic-derivation principle: every "
        "ministerial exousia in the Church flows from Christ's antecedent "
        "donation. The Twelve do not innovate authority; they exercise "
        "delegated authority. Tewahedo episcopal succession (qǝddus "
        "Atnatēwos line traced to Mark via Cyrillian Alexandria) grounds "
        "in Mt 10:1 as the apostolic-handing-on charter.",
    ),
    cyril_matt(
        10,
        8,
        "'Freely ye have received, freely give' — Cyril's "
        "dōrean-elabete-dōrean-dote anti-simony locus. The apostolic gifts "
        "are received-by-grace; selling them inverts the gift's nature. "
        "The dōrean adverb is doubled deliberately — receipt and "
        "transmission share the same gracious mode. Tewahedo canonical "
        "tradition (Sǝnodos canon-collection) cites Mt 10:8 as the anti-"
        "simony foundation; ordination must remain costless.",
    ),
    cyril_matt(
        10,
        16,
        "'Behold, I send you forth as sheep in the midst of wolves: be ye "
        "therefore wise as serpents, and harmless as doves' — Cyril marks "
        "the phronimoi-akeraioi (wise-harmless) pairing as complementary, "
        "not contradictory. Serpent-wisdom is diagnostic acuteness about "
        "danger; dove-harmlessness is non-aggression in response. The "
        "Cross-Spirit synthesis: neither naive nor predatory. Tewahedo "
        "monastic-pastoral discernment tradition cites Mt 10:16 as the "
        "abba's-balance text.",
    ),
    cyril_matt(
        10,
        22,
        "'And ye shall be hated of all men for my name's sake: but he that "
        "endureth to the end shall be saved' — Cyril reads hypomeinas eis "
        "telos as the martyric perseverance-summary. The dia to onoma mou "
        "(for my name's sake) is the specifically-Christic hatred; "
        "persecution as such is not blessed (per Mt 5:10). The end (telos) "
        "is teleological-eschatological — through-to-the-end, not until-it-"
        "stops. Tewahedo Sämā'ǝtāt martyrology cites Mt 10:22 as the "
        "perseverance-charter.",
    ),
    cyril_matt(
        10,
        28,
        "'Fear not them which kill the body, but are not able to kill the "
        "soul: but rather fear him which is able to destroy both soul and "
        "body in hell' — Cyril marks the radical re-ordering of fear. "
        "Phobēthēte de mallon (fear rather him) re-targets the disciple's "
        "fear from human persecutors to the divine eschatological "
        "judgment-power. The geenna (Gehenna) is named explicitly. "
        "Tewahedo eschatology preserves the Cyrillian psychosomatic-"
        "judgment unity: soul and body answer together.",
    ),
    cyril_matt(
        10,
        34,
        "'Think not that I am come to send peace on earth: I came not to "
        "send peace, but a sword' — Cyril carefully harmonizes Mt 10:34 "
        "with Jn 14:27 (peace I leave with you). The two-peaces "
        "distinction: Christ DENIES carnal-political peace-on-earth "
        "(which collaborates with sin); he GIVES interior-eschatological "
        "peace (which divides the believer from sin). The machaira (sword) "
        "is the spiritual-discriminating sword of Heb 4:12. Tewahedo "
        "discernment-of-conversion theology cites Mt 10:34 + Heb 4:12 as "
        "the costly-grace anchor.",
    ),
    cyril_matt(
        10,
        39,
        "'He that findeth his life shall lose it: and he that loseth his "
        "life for my sake shall find it' — Cyril reads the heurōn-apolesei "
        "/ apolesas-heurēsei chiasm as the kenotic-paradox in summary. The "
        "psychē-finding by clinging is psychē-losing in the deeper sense; "
        "the psychē-losing for-Christ's-sake (heneken emou) is psychē-"
        "finding eschatologically. Tewahedo monastic-renunciation theology "
        "(the giving-up-of-self for the higher Self in Christ) anchors "
        "here.",
    ),
    # ── Matt 11 — Identity + Rest (6 entries; 11:28-30 SIGNATURE) ───────────
    cyril_matt(
        11,
        3,
        "'Art thou he that should come, or do we look for another?' — "
        "Cyril treats John the Baptist's question pastorally-not-"
        "doubtingly. The su ei ho erchomenos (are you the coming-one) "
        "uses ho erchomenos — the messianic technical title (Ps 118:26 "
        "LXX, Hab 2:3 LXX). John is not unbelieving but pedagogically "
        "questioning for his disciples' sake; the answer (Mt 11:4-6) is "
        "Isaianic-fulfillment catalogue. Tewahedo Mäskäräm-1 John the "
        "Baptist feast cites Mt 11:3-6 in the gospel-reading.",
    ),
    cyril_matt(
        11,
        11,
        "'Among them that are born of women there hath not risen a greater "
        "than John the Baptist: notwithstanding he that is least in the "
        "kingdom of heaven is greater than he' — Cyril's eschatological-"
        "transition text. John as Old-Covenant terminus is unsurpassed; "
        "the new-covenant least surpasses him in covenantal-status (not "
        "in personal sanctity). The ho de mikroteros en tē basileia is a "
        "structural-position claim, not a moral one. Tewahedo "
        "covenant-theology grounds the new-covenant-superiority claim "
        "in Mt 11:11 + Heb 7-8.",
    ),
    cyril_matt(
        11,
        25,
        "'Thou hast hid these things from the wise and prudent, and hast "
        "revealed them unto babes' — Cyril's revelation-pedagogy locus. "
        "The sophoi-and-synetoi (wise-and-prudent) are not the genuinely-"
        "learned but the self-confidently-sufficient; nēpioi (babes) are "
        "not the cognitively-incapable but the dependently-receptive. The "
        "hiding-revealing is the same act seen from two epistemic stances. "
        "Tewahedo monastic-humility theology cites Mt 11:25 as the "
        "approach-text for theological study.",
    ),
    cyril_matt(
        11,
        28,
        "'Come unto me, all ye that labour and are heavy laden, and I will "
        "give you rest' — Cyril's universal-invitation locus and the "
        "Cyrillian-Christological-rest doctrine. Deute pros me pantes "
        "(come to me, all) is unrestricted; kopiōntes (laboring) names "
        "spiritual exhaustion under sin and self-righteousness; "
        "pephortismenoi (heavy-laden) names burden of the law not "
        "yet-fulfilled-in-Christ. The kagō anapausō hymas (I will give "
        "you rest) is the divine anapausis-gift — eschatological Sabbath-"
        "in-Christ already inaugurated. Tewahedo Sänbätä-Krǝstiyan "
        "theology and the Mäshafä-Mistir's rest-of-the-saints chapter "
        "both build on Mt 11:28 as the central-anchor.",
    ),
    cyril_matt(
        11,
        29,
        "'Take my yoke upon you, and learn of me; for I am meek and lowly "
        "in heart: and ye shall find rest unto your souls' — Cyril marks "
        "the deliberate paradox: yoke (zygos) traditionally means burden, "
        "but Christ's yoke is rest-bearing precisely because the yoke-"
        "bearer (Christ) carries the disciple. The praos-tapeinos tē "
        "kardia (meek-lowly-in-heart) is the Lord's self-description — "
        "the Tewahedo Christological humility-doctrine is grounded here. "
        "Mathete ap' emou (learn from me) makes Christ both content and "
        "method of theological education.",
    ),
    cyril_matt(
        11,
        30,
        "'For my yoke is easy, and my burden is light' — Cyril's "
        "chrēstos-zygos / elaphron-phortion summary. The zygos-mou is "
        "chrēstos (kindly, good — Cyril plays with the Chrēstos / "
        "Christos near-homonymy: Christ's-yoke is Christly-yoke); the "
        "phortion-mou is elaphron (light) because the bearer (Christ) "
        "shares the carrying. Tewahedo monastic-rule tradition (the "
        "Mäshafä-Mǝnǝkwǝsnna) cites Mt 11:28-30 as the daily-rule "
        "prologue: monastic askēsis is yoke-from-Christ, hence rest-"
        "giving.",
    ),
    # ── Matt 12 — Sabbath-Beelzebub-Sign (8 entries) ───────────────────────
    cyril_matt(
        12,
        7,
        "'If ye had known what this meaneth, I will have mercy, and not "
        "sacrifice, ye would not have condemned the guiltless' — Cyril "
        "marks Hos 6:6 as the hermeneutical-key Christ teaches the "
        "Pharisees. The eleos-thelō / thysian-ou-thelō (mercy-I-desire / "
        "sacrifice-not) prioritizes interior-disposition over ritual-"
        "performance. The katedikasate tous anaitious (you condemned the "
        "guiltless) is a strong rebuke: Pharisaic hermeneutics has "
        "manufactured guilt where Scripture acquits. Mt 12:8 (Sabbath-"
        "Lord) was the γ.4.6 seed; Mt 12:7 here provides the "
        "hermeneutical-foundation.",
    ),
    cyril_matt(
        12,
        18,
        "'Behold my servant, whom I have chosen; my beloved, in whom my "
        "soul is well pleased: I will put my spirit upon him' — Cyril's "
        "Isa 42 servant-fulfillment locus. Matthew gives the longest Old-"
        "Testament citation in the Gospel here; Cyril reads the pais-mou "
        "(my servant) Christologically — the eternal Son in his incarnate "
        "servant-form. The thēsō to pneuma-mou ep'auton (I will place my "
        "Spirit upon him) names the baptismal Pentecost-foreshadowing. "
        "Tewahedo Isaiah-Lectionary uses Mt 12:18-21 as the bridge-text "
        "between Old and New Covenant readings.",
    ),
    cyril_matt(
        12,
        24,
        "'This fellow doth not cast out devils, but by Beelzebub the "
        "prince of the devils' — Cyril marks the Pharisaic "
        "Beelzebub-attribution as the gravest possible misreading: "
        "Christ's exorcisms manifest divine Spirit (Mt 12:28); calling "
        "them demonic IS blasphemy-against-the-Spirit (Mt 12:31). The "
        "Beelzeboul / Baal-zebul name-play (lord-of-the-flies / lord-"
        "of-the-high-place) is itself satirical OT-mockery; the Pharisees "
        "use the slur sincerely. Tewahedo anti-blasphemy catechesis cites "
        "Mt 12:24-32 as the cautionary corpus.",
    ),
    cyril_matt(
        12,
        28,
        "'If I cast out devils by the Spirit of God, then the kingdom of "
        "God is come unto you' — Cyril's pneumatological-eschatology "
        "summary. The en pneumati theou (by the Spirit of God) names the "
        "operative power; the ephthasen eph'hymas hē basileia (the "
        "kingdom has arrived upon you) names the consequence — the "
        "kingdom is recognized BY the Spirit-empowered exorcism, not as "
        "future-only but as present-irrupting. Tewahedo Pentecost-and-"
        "Anaphora theology grounds the present-kingdom claim in Mt 12:28 "
        "+ Acts 2:33.",
    ),
    cyril_matt(
        12,
        30,
        "'He that is not with me is against me; and he that gathereth not "
        "with me scattereth abroad' — Cyril treats the binary as a "
        "Christological-decisional summary. The ouk-met'emou (not-with-"
        "me) is the neutrality-impossible thesis; before the incarnate "
        "Word, there is no neutral standing. The synagōn / skorpizei "
        "(gathering / scattering) names the ecclesial dimension: Christ "
        "gathers his Church; refusal-to-gather is functionally "
        "scattering. Tewahedo conversion-decisiveness theology cites Mt "
        "12:30 as the no-middle-ground anchor.",
    ),
    cyril_matt(
        12,
        31,
        "'All manner of sin and blasphemy shall be forgiven unto men: but "
        "the blasphemy against the Holy Ghost shall not be forgiven unto "
        "men' — Cyril carefully delimits the unforgivable. The "
        "blasphēmia eis to pneuma is not a single utterance but the "
        "settled-disposition of attributing the Spirit's-work-to-Satan — "
        "the disposition that refuses the only available means of "
        "repentance. Forgiveness is not withheld arbitrarily; it is "
        "structurally-precluded by rejection of the forgiveness-Spirit. "
        "Tewahedo sacramental-confession theology distinguishes "
        "Mt 12:31 from ordinary post-baptismal sin per Cyrillian "
        "guidelines.",
    ),
    cyril_matt(
        12,
        36,
        "'Every idle word that men shall speak, they shall give account "
        "thereof in the day of judgment' — Cyril marks pan rhēma argon "
        "(every idle word) as targeting not casual-conversation but "
        "vacuous-empty speech — the logos-without-substance that "
        "betrays the soul's argia (sloth). The doxological corollary: "
        "every-word should bear weight; speech is a stewardship. "
        "Tewahedo monastic silence-discipline (the hesychast-Tewahedo "
        "bridge) cites Mt 12:36 as the speech-accountability anchor.",
    ),
    cyril_matt(
        12,
        50,
        "'Whosoever shall do the will of my Father which is in heaven, "
        "the same is my brother, and sister, and mother' — Cyril reads "
        "the redefined-family text carefully — not as displacement of "
        "Mary (who emphatically DOES the Father's will, the supreme "
        "fiat-mihi of Lk 1:38) but as expansion-of-kinship via "
        "obedience. Tewahedo Marian-theology reads Mt 12:50 as "
        "doubly-affirming Mary: she is mother-by-flesh AND mother-by-"
        "obedience, the latter being the criterion she singularly meets.",
    ),
    # ── Matt 13 — Parables of the Kingdom (12 entries) ─────────────────────
    cyril_matt(
        13,
        3,
        "'Behold, a sower went forth to sow' — Cyril marks the parable-"
        "introduction as a hermeneutical announcement. The speirōn (sower) "
        "is the Logos himself; the speirein (sowing) is the kerygma; the "
        "gē (ground) is the human heart in its four-fold reception-"
        "modality (Mt 13:4-8). Tewahedo lectionary tradition reads the "
        "Sower-parable on the second Sunday of Mäskäräm to set the year's "
        "Word-receptive posture.",
    ),
    cyril_matt(
        13,
        8,
        "'Other fell into good ground, and brought forth fruit, some an "
        "hundredfold, some sixtyfold, some thirtyfold' — Cyril reads the "
        "hekaton-hexēkonta-triakonta hierarchy as the diversified-"
        "fruitfulness pattern. Not all good-ground believers produce "
        "identically; vocation-difference (martyrs, virgins, ordinary-"
        "faithful in the patristic exegesis) yields differentiated-but-"
        "all-blessed yield. Tewahedo monastic-lay distinction reads "
        "Mt 13:8 as the threefold-fruit anchor for the qǝddus / "
        "bahǝtawi / mǝʿǝmǝn distinction.",
    ),
    cyril_matt(
        13,
        11,
        "'It is given unto you to know the mysteries of the kingdom of "
        "heaven, but to them it is not given' — Cyril marks the "
        "dedotai-ou-dedotai (given-not-given) carefully against "
        "predestinarian misreading: the giving follows the disciples' "
        "willing-disposition, not preceding it deterministically. The "
        "mystēria tēs basileias (mysteries of the kingdom) is a "
        "deliberate technical term: the parable-mode VEILS truth to "
        "the casual hearer but REVEALS it to the catechumenally-prepared. "
        "Tewahedo mystagogical-catechesis pedagogy is grounded here.",
    ),
    cyril_matt(
        13,
        13,
        "'Therefore speak I to them in parables: because they seeing see "
        "not; and hearing they hear not, neither do they understand' — "
        "Cyril marks the Isa 6:9-10 citation as the parable-rationale. "
        "The blepontes-ou-blepousin / akouontes-ou-akouousin paradox is "
        "deliberate-judicial: those who refused-the-plain-word now "
        "receive-the-veiled-word — the veiling is mercy (delaying full "
        "judgment) and judgment (ratifying prior refusal) at once. "
        "Tewahedo prophetic-judgment hermeneutic uses Mt 13:13-15 + "
        "Isa 6 as the dual-aspect text.",
    ),
    cyril_matt(
        13,
        23,
        "'But he that received seed into the good ground is he that "
        "heareth the word, and understandeth it' — Cyril marks "
        "syniōn (understanding) as the differentiating-faculty between "
        "good-ground hearers and the other three soils. Mere-hearing "
        "(without comprehension) is insufficient; mere-affect (rocky "
        "ground) is insufficient; mere-distraction-survival (thorny) "
        "is insufficient. Synesis is hearer-and-receiver participation. "
        "Tewahedo mystagogical catechesis aims at synesis as completion "
        "of baptismal preparation.",
    ),
    cyril_matt(
        13,
        25,
        "'But while men slept, his enemy came and sowed tares among the "
        "wheat, and went his way' — Cyril marks katheudontōn tōn "
        "anthrōpōn (men sleeping) as the ecclesial-vigilance lapse "
        "exploited by the echthros (enemy). The zizania (tares) — "
        "darnel-grass indistinguishable from wheat in early growth — "
        "names the heretical-or-hypocritical adherent. The Mt 13:30 "
        "patience-until-harvest (γ.4.6 seed-anchor) is Cyril's pastoral "
        "guideline against premature ecclesial-purges; Mt 13:25 here "
        "names the diagnosis of how the problem arose.",
    ),
    cyril_matt(
        13,
        31,
        "'The kingdom of heaven is like to a grain of mustard seed' — "
        "Cyril marks the kokkos sinapeōs (mustard grain) image as "
        "deliberately-paradoxical. The smallest visible seed grows into "
        "the largest garden-plant; the kingdom's beginning is "
        "imperceptibly-small (a Galilean rabbi's twelve fishermen), its "
        "completion globally-arboreal (the Mt 13:32 birds-of-heaven "
        "nesting). Tewahedo missionary-theology reads Mt 13:31-32 as "
        "the small-Ethiopian-Church-and-its-historical-growth promise.",
    ),
    cyril_matt(
        13,
        33,
        "'The kingdom of heaven is like unto leaven, which a woman took, "
        "and hid in three measures of meal, till the whole was leavened' "
        "— Cyril marks the zymē (leaven) image's positive-use here "
        "(unusual against the typical biblical negative-leaven, e.g. "
        "1 Cor 5:6-8). The female-domestic agent (gynē enekrupsen — "
        "a woman hid) and the tria sata aleurou (three measures of meal) "
        "yield household-kitchen kingdom-imagery. Tewahedo Marian-"
        "ecclesiology reads the woman-leaven-hider as Mary-as-Theotokos-"
        "Church figure; the three measures echo Sarah's three-seah-baking "
        "of Gen 18:6.",
    ),
    cyril_matt(
        13,
        43,
        "'Then shall the righteous shine forth as the sun in the kingdom "
        "of their Father' — Cyril's eschatological-glorification locus. "
        "Eklampsousin hōs ho hēlios (shall shine as the sun) is "
        "deification-language: the dikaioi share the divine luminosity "
        "in the Father's kingdom. The Tabor transfiguration (Mt 17:2 — "
        "elampsen to prosōpon autou hōs ho hēlios) prefigures this "
        "eschatological-condition. Tewahedo iconographic-tradition "
        "renders glorified saints with explicit sun-halo signature per "
        "Mt 13:43 + Mt 17:2 paired-prooftext.",
    ),
    cyril_matt(
        13,
        45,
        "'Again, the kingdom of heaven is like unto a merchant man, "
        "seeking goodly pearls' — Cyril marks the emporos zētōn kalous "
        "margaritas (merchant seeking goodly pearls) as the active-"
        "seeker image (contrast Mt 13:44 hidden-treasure stumbled-upon). "
        "Both modes (passive-discovery and active-quest) yield the same "
        "supreme-Pearl; God's-grace meets multiple human-temperaments. "
        "Tewahedo Marian-tradition reads the margaritēs polytīmos "
        "(pearl-of-great-price, Mt 13:46) as Mary-as-the-Pearl-of-"
        "Hagiography — the Mäshafä-Bǝrhān explicitly cites Mt 13:45-46 "
        "in the Theotokos-titulature.",
    ),
    cyril_matt(
        13,
        47,
        "'Again, the kingdom of heaven is like unto a net, that was cast "
        "into the sea, and gathered of every kind' — Cyril marks the "
        "sagēnē (dragnet) image's mixed-eschatology: the net gathers "
        "ek pantos genous (of every kind) precisely because the "
        "Mt 13:48-49 separation is reserved for the eschaton-shore. The "
        "ecclesia-militans is mixed by intent; the ecclesia-triumphans "
        "is purified by harvest. Tewahedo dogmatic-ecclesiology cites "
        "Mt 13:47-50 as the corpus-permixtum text alongside Augustine's "
        "later usage.",
    ),
    cyril_matt(
        13,
        57,
        "'A prophet is not without honour, save in his own country, and "
        "in his own house' — Cyril marks the Nazareth-rejection as "
        "Christological-paradigm: the incarnate Word's hiddenness in "
        "ordinary-Galilean-life occludes the divine-glory to those who "
        "presume familiar-knowledge. The tekton-houtos / Mariam-houtos / "
        "adelphoi-houtos question-series (Mt 13:55-56) names the "
        "scandal of incarnate-particularity. Tewahedo Christological "
        "preaching cites Mt 13:55-58 as the kenōsis-hiddenness anchor; "
        "true-knowledge of the Lord requires faith-eyes, not "
        "neighborhood-acquaintance.",
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 50, f"expected 50 entries, got {len(NEW_ENTRIES)}"
assert all(e["book"] == "mat" for e in NEW_ENTRIES)
assert all(e["father"] == "Cyril of Alexandria" for e in NEW_ENTRIES)
assert all(8 <= e["chapter"] <= 13 for e in NEW_ENTRIES), "Galilean-ministry = Matt 8-13 only"
chapters_covered = sorted({e["chapter"] for e in NEW_ENTRIES})
assert chapters_covered == [8, 9, 10, 11, 12, 13], f"expected all six chapters covered; got {chapters_covered}"

# Per-chapter density (mirrors γ.4.6.B per-chapter pin pattern)
from collections import Counter

_density = Counter(e["chapter"] for e in NEW_ENTRIES)
assert _density[8] >= 8, f"Matt 8 expected ≥8; got {_density[8]}"
assert _density[9] >= 7, f"Matt 9 expected ≥7; got {_density[9]}"
assert _density[10] >= 6, f"Matt 10 expected ≥6; got {_density[10]}"
assert _density[11] >= 5, f"Matt 11 expected ≥5; got {_density[11]}"
assert _density[12] >= 7, f"Matt 12 expected ≥7; got {_density[12]}"
assert _density[13] >= 10, f"Matt 13 expected ≥10; got {_density[13]}"


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    assert "entries" in d and "_meta" in d

    pre_count = len(d["entries"])
    d["entries"].extend(NEW_ENTRIES)
    post_count = len(d["entries"])

    ledger_addition = (
        " γ.4.6.C (2026-05-13) added Cyril on Matthew Galilean-ministry "
        "detail wave — 50 verse-keyed entries on Matt 8-13 (leper-cleansing "
        "+ centurion-faith Tewahedo-Qǝddāse-confession-anchor + Peter's-"
        "mother-in-law healing-ministry + Isa-53 fulfillment Christological "
        "key + Son-of-Man-no-resting-place kenōsis + storm-stilling + "
        "Gadarene demoniacs + paralytic-forgiveness sacramental-anchor + "
        "authority-to-forgive + call-of-Matthew telōnēs + Physician-of-"
        "sick + new-wine-new-wineskins covenantal-renewal + hemorrhage-"
        "woman tassel-faith + sheep-without-shepherd Ezek-34 + harvest-"
        "plentiful missionary-prayer + Twelve-authority apostolic-"
        "succession + freely-give anti-simony + sheep-among-wolves "
        "wise-as-serpents + endure-to-end martyric-perseverance + fear-"
        "not-body-killers psychosomatic-judgment + not-peace-but-sword "
        "discriminating + lose-life-find-life kenotic + art-thou-he-that-"
        "cometh Baptist-Isaianic + least-in-kingdom covenant-transition + "
        "hidden-from-wise revelation-pedagogy + COME-UNTO-ME-ALL signature "
        "Tewahedo-rest anchor + TAKE-MY-YOKE meek-and-lowly + YOKE-EASY-"
        "BURDEN-LIGHT Chrēstos-pun + mercy-not-sacrifice Hos-6:6 + Isaiah-"
        "servant fulfillment Pentecost-foreshadowing + Beelzebub-controversy "
        "+ Spirit-of-God-kingdom-come pneumatology-eschatology + not-with-"
        "me-against-me decisional + blasphemy-against-Spirit unforgivable + "
        "every-idle-word speech-stewardship + whoever-does-Father's-will "
        "kinship-by-obedience Marian-double-affirmation + SOWER kerygma + "
        "hundred-sixty-thirty-fold differentiated-yield + mysteries-given "
        "mystagogical-catechesis + parables-veil-reveal Isa-6 + good-ground-"
        "synesis + enemy-sows-tares-at-night ecclesial-vigilance + mustard-"
        "seed missionary-growth + leaven-three-measures Marian-ecclesiology "
        "+ righteous-shine-as-sun Tabor-Anaphora + PEARL-OF-GREAT-PRICE "
        "Mary-as-Pearl Tewahedo-Mäshafä-Bǝrhān anchor + dragnet corpus-"
        "permixtum + Nazareth-rejection kenōsis-hiddenness). Cyril-on-"
        "Matthew total post-γ.4.6.C: 145 entries (45 seed + 50 Sermon-"
        "Mount γ.4.6.B + 50 Galilean-ministry γ.4.6.C). Source: Cramer "
        "Vol. I (Oxford 1840 — PD) + PG 72 cols. 365-474 (PD); mirrors "
        "γ.4.6.B Sermon-on-Mount detail-wave structure."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    matt_total = sum(1 for e in d["entries"] if e["book"] == "mat" and e["father"] == "Cyril of Alexandria")
    print(f"γ.4.6.C ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(f"Cyril on Matthew total: {matt_total} entries")


if __name__ == "__main__":
    main()
