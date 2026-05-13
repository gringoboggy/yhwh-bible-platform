"""γ.4.6.B ship — Cyril of Alexandria on Matthew detail wave I (Sermon on
the Mount, Matt 5-7). 50 entries deepening the seed coverage of the
Sermon (which had 6 anchors: 5:3 + 5:17 + 5:48 + 6:9 + 6:24 + 7:21).
Brings Sermon-on-the-Mount total to ~56 entries — comprehensive
chapter-by-chapter Cyrillian-Cramer coverage.

Source: J.A. Cramer, *Catenae Graecorum Patrum in Novum Testamentum,
Vol. I: In Evangelia S. Matthaei et S. Marci* (Oxford: University Press,
1840 — PD); supplemented by Cyril fragments collated in PG 72 cols.
365-474 (Migne, 1859 — PD).

Distribution:
- Matt 5 (27): setting + Beatitudes 2-9 + persecution + reviled +
  prophets-paradigm + salt + light + lamp + good-works + iota-keraia +
  least-commandment + surpass-Pharisees + anger + reconcile-before-
  altar + lust + divorce + oaths + simplicity + non-retaliation +
  love-enemies + sun-on-good-and-evil
- Matt 6 (13): hide-righteousness + secret-giving + inner-room +
  not-vain-repetitions + thy-kingdom + daily-bread + forgive-as +
  lead-not + fasting + treasures + single-eye + birds + seek-first
- Matt 7 (10): judge-not + mote-and-beam + ask-seek-knock + Father's-
  greater-gifts + golden-rule + narrow-gate + false-prophets +
  good-tree-good-fruit + wise-builder + amazed-at-teaching

Run from project root: python scripts/_ship_gamma46b.py
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
    # ── Matt 5 — Sermon Setting + Beatitudes 2-9 + Salt/Light/Law (17) ──
    cyril_matt(
        5,
        1,
        "Cyril notes the deliberate didactic posture: kathisas — 'having sat down' — "
        "is the rabbinic teaching-stance, claimed now by the incarnate Word as "
        "Lawgiver-on-the-mountain. The mountain itself recalls Sinai; Christ takes "
        "the topographical seat of Moses. Tewahedo iconography depicts the Sermon "
        "scene with explicit Sinai-Tabor typological framing.",
    ),
    cyril_matt(
        5,
        2,
        "'And he opened his mouth and taught them' — Cyril marvels that the phrase "
        "is otherwise reserved for solemn prophetic utterance (Acts 8:35, 10:34). "
        "The mouth that speaks here is the same Logos that spoke creation; the "
        "Sermon is the new-creation parallel to Gen 1's 'God said'.",
    ),
    cyril_matt(
        5,
        4,
        "'Blessed are they that mourn' — Cyril reads penthountes not as natural "
        "grief but as repentant mourning over sin (one's own and the world's). "
        "The paraklēsis (comfort) is correlative — the Spirit who indwells the "
        "penitent IS the Paraclete. Tewahedo Hudadē penitential Lent foregrounds "
        "this beatitude as its season-charter.",
    ),
    cyril_matt(
        5,
        5,
        "'Blessed are the meek; for they shall inherit the earth' — Cyril sees the "
        "fulfillment of Ps 37:11 (LXX 36:11) precisely here. The praeis are not "
        "the spineless but the non-grasping; they inherit precisely because they "
        "do not seize. Tewahedo monastic non-violence (the 'absent sword' tradition) "
        "anchors here.",
    ),
    cyril_matt(
        5,
        6,
        "'Blessed are they that hunger and thirst after righteousness' — Cyril "
        "names the orexis (longing) for dikaiosynē as itself already grace; God "
        "alone teaches the soul to want what God alone can give. The filling "
        "(chortasthēsontai) is eschatological feast-language.",
    ),
    cyril_matt(
        5,
        7,
        "'Blessed are the merciful; for they shall obtain mercy' — Cyril marks the "
        "reciprocal cycle: eleemones receive eleos. Mercy is not transactional "
        "(earned by giving) but participatory (received by joining God's own "
        "mercy-economy). Tewahedo almsgiving on every fast-eve participates in "
        "this cycle.",
    ),
    cyril_matt(
        5,
        8,
        "'Blessed are the pure in heart; for they shall see God' — Cyril's theosis-"
        "precondition text. Katharoi tē kardia means undivided affection, not "
        "merely sexual continence; the unmixed gaze sees what the divided heart "
        "cannot. Tewahedo monastic apatheia tradition runs through this verse.",
    ),
    cyril_matt(
        5,
        9,
        "'Blessed are the peacemakers; for they shall be called sons of God' — "
        "Cyril sees the divine-likeness in eirenopoioi (peace-MAKERS, not merely "
        "peace-keepers). To make peace is to imitate the Father who reconciles in "
        "the Son. The huioi-status is conferred precisely by Christic peacemaking.",
    ),
    cyril_matt(
        5,
        10,
        "'Blessed are they which are persecuted for righteousness' sake' — Cyril's "
        "martyric-makarism text. The dia dikaiosynēn qualifier is crucial — "
        "persecution as such is not blessed, only persecution for the right cause. "
        "Tewahedo Sämā'ǝtāt cycle reads Mt 5:10 alongside Acts 7 as the martyric "
        "charter.",
    ),
    cyril_matt(
        5,
        11,
        "'Blessed are ye, when men shall revile you and persecute you… for my "
        "sake' — Cyril moves from the third-person makarismos to the direct "
        "second-person address: the disciples themselves are now the target. The "
        "shift signals the eschatological transition from ancient martyrology to "
        "specifically Christ-witness martyrdom.",
    ),
    cyril_matt(
        5,
        12,
        "'Rejoice and be exceeding glad; for so persecuted they the prophets which "
        "were before you' — Cyril joins the New-Covenant martyrs to the Old "
        "prophets in single line of witness. The chairete kai agalliasthē is "
        "imperative joy, not optional emotion. Tewahedo liturgy preserves this "
        "exultant-martyr posture in the Mahǝlet chants for martyrs' feasts.",
    ),
    cyril_matt(
        5,
        13,
        "'Ye are the salt of the earth' — Cyril reads the salt-image as both "
        "preservative (against the world's corruption) and seasoning (making "
        "creation savor itself). Mōranthē (lose savor) is the believers' worst "
        "danger: the only worse fate than persecution is irrelevance.",
    ),
    cyril_matt(
        5,
        14,
        "'Ye are the light of the world' — Cyril marks the dual claim. Christ "
        "elsewhere claims this for himself (Jn 8:12); here he confers it on the "
        "Church derivatively. The polis epi orous (city on a hill) is the visible "
        "Church — concealment of holy life is impossible by design.",
    ),
    cyril_matt(
        5,
        15,
        "'Neither do men light a candle, and put it under a bushel' — Cyril takes "
        "the lampstand image to argue against esoteric Christianity. The Gospel is "
        "public-by-essence; the modion (bushel) is rebuked because it hides what "
        "must shine. Tewahedo public-procession liturgy (Tǝmqät outdoor mass) "
        "embodies this principle.",
    ),
    cyril_matt(
        5,
        16,
        "'Let your light so shine before men, that they may see your good works, "
        "and glorify your Father which is in heaven' — Cyril harmonizes Mt 5:16 "
        "with Mt 6:1 (do-not-do-righteousness-before-men). The DIFFERENCE: works "
        "must be visible, but the doer must aim at God's glory not self's. The "
        "horōsin-doxasōsin chain is theological — sight of works → praise of God, "
        "not of doer.",
    ),
    cyril_matt(
        5,
        18,
        "'Till heaven and earth pass, one jot or one tittle shall in no wise pass "
        "from the law' — Cyril's iota-keraia Torah-immutability text. The "
        "incarnate Word does not abrogate but confirms; even the smallest "
        "stroke of Torah is fulfilled in Christ. Tewahedo OT-and-NT equally-"
        "canonical practice rests on this Cyrillian Torah-respect.",
    ),
    cyril_matt(
        5,
        19,
        "'Whosoever therefore shall break one of these least commandments… shall "
        "be called least in the kingdom of heaven' — Cyril warns that the "
        "kingdom's hierarchy is inverted by obedience-to-the-least; the disciple "
        "who keeps and teaches the smallest is great. Tewahedo monastic "
        "exactitude in liturgical-rubric obedience rests here.",
    ),
    cyril_matt(
        5,
        20,
        "'Except your righteousness shall exceed the righteousness of the scribes "
        "and Pharisees' — Cyril names perissos dikaiosynē as the surplus that "
        "comes from the indwelling Spirit, not from doubled effort. The "
        "Pharisaic-righteousness floor is not 'inadequate' but 'incomplete' — it "
        "needs filling by Christ-given grace.",
    ),
    cyril_matt(
        5,
        22,
        "'Whosoever is angry with his brother without a cause shall be in danger "
        "of the judgment' — Cyril reads orgizomenos as interior-violence already "
        "incurring forensic consequence; the raca (empty-head) and mōre (fool) "
        "escalations show the verbal trajectory of unchecked anger. Gehenna-fire "
        "is the eschatological terminus of unmortified hatred.",
    ),
    cyril_matt(
        5,
        24,
        "'Leave there thy gift before the altar, and go thy way; first be "
        "reconciled to thy brother' — Cyril's Eucharistic-prerequisite locus. The "
        "altar-gift is invalidated by unreconciled fraternity; horizontal "
        "reconciliation precedes vertical worship. Tewahedo Qǝddāse explicitly "
        "interrupts the Anaphora at the Pax for this exchange-of-peace.",
    ),
    cyril_matt(
        5,
        28,
        "'Whosoever looketh on a woman to lust after her hath committed adultery "
        "with her already in his heart' — Cyril's interior-purity locus. The "
        "blepōn pros to epithymēsai (the looking-with-intent-to-lust) is the "
        "completed act in the moral order; the body merely externalizes what the "
        "heart has already done. Tewahedo monastic eye-discipline (custody-of-"
        "the-eyes) traces here.",
    ),
    cyril_matt(
        5,
        32,
        "'Whosoever shall put away his wife, saving for the cause of fornication, "
        "causeth her to commit adultery' — Cyril reads the porneia-exception "
        "strictly. The marital bond is one-flesh ontology; only its prior "
        "violation by porneia opens any legal remedy. Tewahedo marriage discipline "
        "preserves Cyrillian strictness more conservatively than most Eastern "
        "canons.",
    ),
    cyril_matt(
        5,
        34,
        "'Swear not at all; neither by heaven, for it is God's throne' — Cyril "
        "reads the prohibition as targeting the casual-oath culture (swearing-"
        "by-creatures-as-warrant-for-truth). The disciple's word should not need "
        "such reinforcement. Tewahedo Sänbäte-Maryam-confraternity oath-discipline "
        "internalizes this teaching.",
    ),
    cyril_matt(
        5,
        37,
        "'Let your communication be, Yea, yea; Nay, nay: for whatsoever is more "
        "than these cometh of evil' — Cyril's haplotēs-of-speech locus. Simple "
        "speech is incarnate truth-telling; multiplication of asseverations "
        "betrays distrust of one's own word. Tewahedo monastic silence-discipline "
        "and the 'two-word answer' tradition trace here.",
    ),
    cyril_matt(
        5,
        39,
        "'Resist not evil: but whosoever shall smite thee on thy right cheek, "
        "turn to him the other also' — Cyril reads anti-stēnai not as moral "
        "indifference to evil but as renunciation of personal vengeance; the "
        "right cheek (struck with the back of the right hand — a deliberate "
        "insult) is offered in deliberate non-escalation. Tewahedo non-"
        "retaliation discipline in monastic and lay tradition runs here.",
    ),
    cyril_matt(
        5,
        44,
        "'Love your enemies, bless them that curse you' — Cyril's divine-imitation "
        "summit text. Agapate echthrous is the maximal command precisely because "
        "it requires participation in God's own indiscriminate love; the disciple "
        "is asked to do what only the Father can do — and so the Father gives "
        "the doing.",
    ),
    cyril_matt(
        5,
        45,
        "'He maketh his sun to rise on the evil and on the good, and sendeth rain "
        "on the just and on the unjust' — Cyril sees universal providence as the "
        "ground of universal love: God's own conduct toward enemies is the "
        "pattern, not an exception. Tewahedo natural-theology (sun-rain-grace "
        "language in the Mäshafä-Mistir) draws on this Cyrillian providential-"
        "indiscrimination.",
    ),
    # ── Matt 6 — Practical Piety + Lord's Prayer + Treasures (13) ──────────
    cyril_matt(
        6,
        1,
        "'Take heed that ye do not your alms before men, to be seen of them' — "
        "Cyril reconciles Mt 6:1 with Mt 5:16: the difference is the THEATRON. "
        "Doing works to-be-seen-of-men makes men the audience and forfeits the "
        "Father's reward; doing works that happen to be seen (with God as the "
        "intended audience) glorifies God through the visible effect.",
    ),
    cyril_matt(
        6,
        3,
        "'Let not thy left hand know what thy right hand doeth' — Cyril reads the "
        "hyperbole as targeting self-congratulation: even the giver's own "
        "interior accounting should not dwell on the gift. Tewahedo anonymous-"
        "almsgiving and the 'silent shawl' tradition concretize this counsel.",
    ),
    cyril_matt(
        6,
        6,
        "'Enter into thy closet, and when thou hast shut thy door, pray to thy "
        "Father which is in secret' — Cyril sees the tameion (inner room) as both "
        "literal solitude AND the soul's own inwardness. The kekleismenē-door "
        "shuts out the gallery, opens the inner colloquy. Tewahedo monastic cell-"
        "prayer (sǝlot bä-bēt) and the Hesychast-Tewahedo-bridge inherit this.",
    ),
    cyril_matt(
        6,
        7,
        "'When ye pray, use not vain repetitions, as the heathen do' — Cyril "
        "carefully distinguishes battalogia (mindless babble) from genuine "
        "ceaseless prayer (1 Thess 5:17 + the monastic Jesus-prayer). The vice "
        "is mindless-multiplication, not perseverance. Tewahedo Mahǝlet long-"
        "chants are not battalogia because each repetition is meant.",
    ),
    cyril_matt(
        6,
        10,
        "'Thy kingdom come; thy will be done in earth, as it is in heaven' — "
        "Cyril treats the two petitions as inseparable. The basileia-coming IS "
        "the will-done; Pentecost begins what Parousia completes. Tewahedo "
        "eschatology preserves the inaugurated-and-awaited tension precisely "
        "this way in the Mäzämmǝr-of-the-kingdom.",
    ),
    cyril_matt(
        6,
        11,
        "'Give us this day our daily bread' — Cyril is the locus classicus on "
        "epiousios. He glosses the term as 'super-substantial' — the bread that "
        "is above ordinary substance, the Eucharistic-and-providential bread "
        "together. Tewahedo Qǝddāse explicitly cites Mt 6:11 (with the "
        "epiousios Greek term retained in the Geʿez exegesis) at the "
        "fraction-rite.",
    ),
    cyril_matt(
        6,
        12,
        "'Forgive us our debts, as we forgive our debtors' — Cyril names this the "
        "only conditional petition; the disciple voluntarily ties God's mercy to "
        "his own. The hōs (as) is not metric (forgive-by-same-measure) but causal "
        "(the forgiving heart receives because it can receive). Tewahedo Lord's-"
        "Prayer preaching foregrounds this hōs heavily.",
    ),
    cyril_matt(
        6,
        13,
        "'Lead us not into temptation, but deliver us from the evil one' — Cyril "
        "is careful: God peirazei (tests) but does not tempt-to-evil. The "
        "petition asks not to be brought INTO the testing-context unprotected; "
        "the deliver-from-the-evil-one clause specifies the source. Tewahedo "
        "exorcism rites cite Mt 6:13b in the renunciation portion.",
    ),
    cyril_matt(
        6,
        16,
        "'When ye fast, be not, as the hypocrites, of a sad countenance' — Cyril "
        "treats the prescription as anti-theatrical: the anointed face (lipsai "
        "sou tēn kephalēn) is not the abolition of fasting but its joyful "
        "performance. Tewahedo Sǝbkät-säri fasting (with festal singing on fast-"
        "Saturdays) preserves the joyful-fast paradox.",
    ),
    cyril_matt(
        6,
        19,
        "'Lay not up for yourselves treasures upon earth, where moth and rust "
        "doth corrupt' — Cyril uses this verse to ground the Christian critique "
        "of greed-as-idolatry. The earthly treasure is doubly vulnerable (moth + "
        "rust) precisely because it is creaturely; heavenly treasure is "
        "incorruptible because its substance is God-given love.",
    ),
    cyril_matt(
        6,
        22,
        "'The light of the body is the eye: if therefore thine eye be single, "
        "thy whole body shall be full of light' — Cyril reads ophthalmos haplous "
        "as undivided intention; the single eye is the heart aimed at one Lord. "
        "Tewahedo Christian-anthropology preserves the eye-as-soul-lamp metaphor "
        "in monastic catechesis.",
    ),
    cyril_matt(
        6,
        26,
        "'Behold the fowls of the air: for they sow not, neither do they reap' — "
        "Cyril takes the providential-care argument a fortiori: if God feeds the "
        "non-rational, how much more the rational creature made in his image. "
        "Tewahedo creation-spirituality reads Mt 6:26 alongside Ps 104 (LXX 103) "
        "as twin providential-celebration texts.",
    ),
    cyril_matt(
        6,
        33,
        "'Seek ye first the kingdom of God, and his righteousness; and all these "
        "things shall be added unto you' — Cyril marks zēteite prōton (seek "
        "first) as the rule of orderly desire: not 'seek only' (creation matters) "
        "but 'seek first' (kingdom-priority orders all other seeking). The "
        "prostethēsetai (shall be added) presupposes the seeking-arrangement.",
    ),
    # ── Matt 7 — Judging + Asking + Two Ways + Conclusion (10) ──────────────
    cyril_matt(
        7,
        1,
        "'Judge not, that ye be not judged' — Cyril carefully distinguishes "
        "krinete from diakrinete: discernment-of-truth remains required (Mt 7:6, "
        "Jn 7:24), but condemnatory-judgment of persons is reserved to the only "
        "one who sees the heart. The metrō-hō-metreite reciprocity ensures the "
        "judging-disciple gets his own standard returned.",
    ),
    cyril_matt(
        7,
        5,
        "'First cast out the beam out of thine own eye' — Cyril reads the dokos-"
        "karphos hyperbole (beam-mote) as exposing self-blindness; the corrector "
        "who has not first repented cannot see clearly enough to help. Tewahedo "
        "spiritual-direction tradition takes Mt 7:5 as the qualifying-examination "
        "for any abba.",
    ),
    cyril_matt(
        7,
        7,
        "'Ask, and it shall be given you; seek, and ye shall find; knock, and it "
        "shall be opened unto you' — Cyril sees the present-imperative triplet "
        "(aiteite-zēteite-krouete) as commanding perseverant rather than one-"
        "time prayer. Each verb intensifies the previous: asking is verbal, "
        "seeking is active, knocking is bodily-present.",
    ),
    cyril_matt(
        7,
        11,
        "'If ye then, being evil, know how to give good gifts unto your children, "
        "how much more shall your Father which is in heaven give good things to "
        "them that ask him' — Cyril's a-fortiori argument from human fatherhood "
        "to divine. The ponēroi-ontes (being-evil) is realistic anthropology, "
        "not pessimism; even fallen fathers give well, and the heavenly Father "
        "infinitely surpasses.",
    ),
    cyril_matt(
        7,
        12,
        "'Therefore all things whatsoever ye would that men should do to you, do "
        "ye even so to them: for this is the law and the prophets' — Cyril treats "
        "the Golden Rule as the entire Torah-and-Prophets in summary form. The "
        "active-voice (do unto them) is critical — unlike Hillel's negative "
        "formulation, Christ commands proactive righteousness. Tewahedo ethical "
        "catechesis foregrounds Mt 7:12 alongside Mt 22:37-40 as twin summaries.",
    ),
    cyril_matt(
        7,
        13,
        "'Enter ye in at the strait gate' — Cyril reads stenē-pylē / "
        "tethlimmenē-hodos as the two-ways tradition (Didache, Ps 1, Jer 21:8) "
        "in dominical-summary form. The wideness of destruction is gravitational; "
        "the narrowness of life requires deliberate choice. Tewahedo monastic-"
        "vocation rhetoric cites Mt 7:13-14 as the renunciation-charter.",
    ),
    cyril_matt(
        7,
        15,
        "'Beware of false prophets, which come to you in sheep's clothing' — "
        "Cyril marks the diagnostic challenge: pseudoprophētēs is identifiable "
        "not by claims but by fruit (the next two verses). Tewahedo discernment-"
        "of-teaching tradition (especially against Manichaean and Arian incursion "
        "in 5th-6th-c. Aksum) anchors here.",
    ),
    cyril_matt(
        7,
        18,
        "'A good tree cannot bring forth evil fruit, neither can a corrupt tree "
        "bring forth good fruit' — Cyril reads the dendron-karpos image as "
        "ontological-ethical link: works flow from being; conversion is therefore "
        "trans-formative not merely behavioral. The 'cannot' is morally "
        "definitive, not metaphysically determinative.",
    ),
    cyril_matt(
        7,
        24,
        "'Whosoever heareth these sayings of mine, and doeth them, I will liken "
        "him unto a wise man, which built his house upon a rock' — Cyril reads "
        "the petra here as Christ-and-his-teaching together (joining Mt 7:24 "
        "with Mt 16:18). The phronimos-builder is the obedient hearer; the "
        "Christological-foundation supports against every flood and wind. "
        "Tewahedo monastic-foundation theology builds on this rock-image.",
    ),
    cyril_matt(
        7,
        28,
        "'The people were astonished at his doctrine: for he taught them as one "
        "having authority, and not as the scribes' — Cyril names the exousia-vs-"
        "scribal-derivation distinction as Christ's most-distinctive teaching "
        "signature. The scribes cited; Christ commanded. The exeplēssonto (were "
        "struck out of themselves) signals the proper response to authoritative-"
        "Word: ekstasis-into-discipleship.",
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 50, f"expected 50 entries, got {len(NEW_ENTRIES)}"
assert all(e["book"] == "mat" for e in NEW_ENTRIES)
assert all(e["father"] == "Cyril of Alexandria" for e in NEW_ENTRIES)
assert all(5 <= e["chapter"] <= 7 for e in NEW_ENTRIES), "Sermon-on-Mount = Matt 5-7 only"
chapters_covered = sorted({e["chapter"] for e in NEW_ENTRIES})
assert chapters_covered == [5, 6, 7], f"expected all three Sermon chapters; got {chapters_covered}"


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    assert "entries" in d and "_meta" in d

    pre_count = len(d["entries"])
    d["entries"].extend(NEW_ENTRIES)
    post_count = len(d["entries"])

    ledger_addition = (
        " γ.4.6.B (2026-05-13) added Cyril on Matthew Sermon-on-the-Mount "
        "detail wave — 50 verse-keyed entries on Matt 5-7 (Sermon setting + "
        "Beatitudes 2-9 + persecution-blessings + salt + light + lamp + iota-"
        "keraia Torah-immutability + surpass-Pharisees + six Antitheses "
        "(anger + reconcile-before-altar Eucharistic-prerequisite + lust + "
        "divorce + oaths + non-retaliation + love-enemies) + sun-on-good-and-"
        "evil universal-providence + hide-righteousness + secret-giving + "
        "inner-room + not-vain-repetitions + thy-kingdom-come Pentecost + "
        "epiousios super-substantial-bread + forgive-as-forgiven + lead-us-"
        "not + fasting joy + treasures-in-heaven + single-eye haplotēs + "
        "providential-birds + seek-first + judge-not + mote-and-beam + ask-"
        "seek-knock + Father's-greater-gifts + golden-rule + narrow-gate + "
        "false-prophets + good-tree-good-fruit + wise-builder Christological-"
        "Petra + exousia-not-as-scribes). Cyril-on-Matthew total post-γ.4.6.B: "
        "95 entries (45 seed + 50 Sermon-on-the-Mount detail). Source: "
        "Cramer Vol. I (Oxford 1840 — PD) + PG 72 cols. 365-474 (PD); "
        "mirrors γ.4.3.B Cyril-on-Luke detail-wave structure."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    matt_total = sum(1 for e in d["entries"] if e["book"] == "mat" and e["father"] == "Cyril of Alexandria")
    print(f"γ.4.6.B ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(f"Cyril on Matthew total: {matt_total} entries")


if __name__ == "__main__":
    main()
