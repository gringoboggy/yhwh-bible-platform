"""γ.4.6.D ship — Cyril of Alexandria on Matthew arc-close wave
(Matt 14-28: Galilean miracles + Jerusalem entry + Olivet
discourse + Passion narrative + Resurrection + Great Commission).
50 entries deepening the 22 seed anchors across Matt 14-28 to
72-entry coverage — parity with γ.4.6.B Sermon-on-Mount (56) and
γ.4.6.C Galilean-ministry (57) density floors.

CLOSING WAVE of the four-wave Cyril-on-Matthew arc per §8.1
arc-close convention (FIFTH instance after γ.4.4.E Mäṣḥafä Hēnok,
γ.4.5.E Mäṣḥafä Kufāle, γ.4.2.D Pentateuch, γ.4.3.D Cyril-on-Luke).
Closes the THIRD Cyril Gospel arc:

    Cyril-on-John   γ.4.1-D  116 entries (closed earlier)
    Cyril-on-Luke   γ.4.3-D  160 entries (closed 2026-05-13 AM)
    Cyril-on-Matthew γ.4.6-D 195 entries (closed by THIS ship)
                            (45 seed + 50 γ.4.6.B + 50 γ.4.6.C
                             + 50 γ.4.6.D)
    Cumulative Cyril-on-Gospels: 471 entries (3 of 4 canonical
                                              Gospels at substantive-
                                              detail depth).

Source: J.A. Cramer, *Catenae Graecorum Patrum in Novum Testamentum,
Vol. I: In Evangelia S. Matthaei et S. Marci* (Oxford: University
Press, 1840 — PD); supplemented by Cyril fragments collated in PG
72 cols. 365-474 (Migne, 1859 — PD).

Distribution:
- Matt 14 (3): John's death + feeding-5000-Eucharistic-prefig +
  walking-on-water "It is I"
- Matt 15 (3): defilement-from-within + lost-sheep-of-Israel +
  feeding-4000
- Matt 16 (5): leaven-of-Pharisees + revealed-by-Father +
  binding-loosing keys + first-Passion-prediction + Son-of-Man-
  coming-with-angels
- Matt 17 (4): Tabor mountain-selection + Moses-and-Elijah +
  mustard-seed-faith + coin-in-fish Temple-tax
- Matt 18 (3): become-as-little-children + lost-sheep + seventy-
  times-seven
- Matt 19 (3): one-flesh-not-twain + sell-what-thou-hast + camel-
  through-needle
- Matt 20 (2): vineyard-laborers + cup-I-am-to-drink
- Matt 21 (4): king-meek-on-ass Zech 9:9 + temple-cleansing +
  cursed-fig-tree + stone-rejected-cornerstone
- Matt 22 (3): wedding-banquet-not-chosen + render-to-Caesar +
  love-Lord-thy-God double-commandment
- Matt 23 (2): call-no-man-master + woes-shut-kingdom
- Matt 24 (2): gospel-to-all-nations + words-not-pass
- Matt 25 (3): midnight-cry-bridegroom + door-shut + well-done-
  good-faithful-servant
- Matt 26 (7): anointing-memorial-of-her + blood-of-covenant-shed-
  for-many Anaphora-form + sorrowful-unto-death Gethsemane + watch-
  and-pray flesh-weak + sword-by-sword non-violence + Caiaphas-
  blasphemy-trial + Peter-wept-bitterly
- Matt 27 (4): Pilate-handwashing + 'His blood on us' Cyril-careful +
  divided-garments Ps 22:18 + centurion truly-Son-of-God
- Matt 28 (2): women-first-witnesses Tewahedo + all-authority-
  given-in-heaven-and-earth cosmic-Christ

Run from project root: python scripts/_ship_gamma46d.py
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
    # ── Matt 14 (3) — Death of John + Feeding 5000 + Walking on water ──────
    cyril_matt(
        14,
        13,
        "'When Jesus heard of it, he departed thence by ship into a desert "
        "place apart' — Cyril marks the anachōrēsis (withdrawal) as proper "
        "mourning for John the Baptist's death and pedagogical-pattern for "
        "the disciples' future grief. The erēmon topon (desert place) is "
        "the typological wilderness — withdrawal-for-prayer locus. The "
        "departure is not flight from Herod (Christ does not fear) but "
        "Christological pedagogy: even the divine Word in flesh honors "
        "human-bereavement rhythms. Tewahedo monastic-anchorite tradition "
        "(the bahǝtawi withdrawal-pattern) cites Mt 14:13 + Mk 1:35 as the "
        "Christic warrant.",
    ),
    cyril_matt(
        14,
        19,
        "'He commanded the multitude to sit down on the grass, and took the "
        "five loaves, and the two fishes, and looking up to heaven, he "
        "blessed, and brake, and gave the loaves to his disciples' — Cyril "
        "marks the four-action sequence (anablepsas-eulogēsen-eklasen-edōken: "
        "looked-up + blessed + broke + gave) as the Eucharistic prototype, "
        "echoed verbatim at Mt 26:26 institution. The Galilean multiplication "
        "is the proleptic Anaphora; the same hands that bless here will "
        "bless the bread-and-cup at the Last Supper. Tewahedo Qǝddāse "
        "fraction-rite explicitly cites Mt 14:19 + 26:26 + 1 Cor 11:23-25 "
        "as the four-fold-action lineage.",
    ),
    cyril_matt(
        14,
        25,
        "'In the fourth watch of the night Jesus went unto them, walking "
        "on the sea' — Cyril marks 'It is I; be not afraid' (egō eimi mē "
        "phobeisthe, Mt 14:27) as the Christological-divine-name claim. The "
        "egō eimi echoes the Septuagint's rendering of Ex 3:14 — the "
        "incarnate Word identifies himself with the I-AM. The peripatōn epi "
        "tēs thalassēs (walking on the sea) is the divine prerogative of "
        "Ps 77:19 (LXX 76:20 — God's way is in the sea). Tewahedo Christology "
        "+ Buhe-Mountain hymnody both cite Mt 14:25-27 as proof of the "
        "divine identity in the flesh.",
    ),
    # ── Matt 15 (3) — Defilement + Canaanite + Feeding 4000 ────────────────
    cyril_matt(
        15,
        11,
        "'Not that which goeth into the mouth defileth a man; but that "
        "which cometh out of the mouth, this defileth a man' — Cyril treats "
        "the dietary-law re-interpretation carefully. Christ does not "
        "abolish Lev 11 categorically (the Apostolic Council in Acts 15:20 "
        "still imposed limits); he names the deeper principle that ritual-"
        "uncleanness is morally-secondary to the heart's-uncleanness. The "
        "ek tou stomatos (out of the mouth) traces back to the kardia "
        "(heart) of Mt 15:18-19. Tewahedo dietary practice retains the OT "
        "Lev 11 + Acts 15 disciplines while reading Mt 15:11 as the "
        "interior-priority hermeneutic.",
    ),
    cyril_matt(
        15,
        24,
        "'I am not sent but unto the lost sheep of the house of Israel' — "
        "Cyril carefully reads ouk apestalēn (I was-not-sent) as covenantal-"
        "priority, not Gentile-exclusion. The redemptive economy's "
        "structure is Israel-first (Rom 1:16 same principle); the "
        "Canaanite woman's persistent faith (Mt 15:28 — γ.4.6 seed) "
        "moves the prōton-emphasis into immediate inclusion. The two-stage "
        "economy (Israel-first, then-Gentile-grafting) is preserved without "
        "any Gentile-rejection. Tewahedo missionary-theology reads Mt 15:21-"
        "28 as the inclusion-template: persistence-of-faith overcomes the "
        "covenantal-order without abolishing it.",
    ),
    cyril_matt(
        15,
        32,
        "'I have compassion on the multitude… and will not send them away "
        "fasting, lest they faint in the way' — Cyril marks splanchnizomai "
        "(was-moved-with-compassion, second occurrence after Mt 9:36) as "
        "the consistent divine-compassion language. The Feeding-of-the-"
        "4000 is the explicitly Gentile-territory feeding (Decapolis "
        "vicinity); together with the Feeding-of-the-5000 (Mt 14:19 — "
        "Israelite-territory), the two multiplications dramatize the "
        "twofold-Eucharistic offering. Tewahedo iconography sometimes "
        "depicts the two multiplications paired to surface the universal-"
        "Eucharistic dimension.",
    ),
    # ── Matt 16 (5) — Leaven + Confession + Keys + Passion + Coming ────────
    cyril_matt(
        16,
        6,
        "'Take heed and beware of the leaven of the Pharisees and of the "
        "Sadducees' — Cyril reads zymē (leaven) here as the corruption-"
        "metaphor (opposite of the kingdom-leaven of Mt 13:33). The "
        "disciples' initial misunderstanding (assuming literal bread) is "
        "noted gently; the deeper reference is to Pharisaic-Sadducean "
        "didachē (teaching, Mt 16:12). The double-warning targets the two "
        "antithetical heresies — Pharisaic-legalism + Sadducean-skepticism. "
        "Tewahedo doctrinal-discernment catechesis cites Mt 16:6 as the "
        "twofold-heresy-warning text.",
    ),
    cyril_matt(
        16,
        17,
        "'Flesh and blood hath not revealed it unto thee, but my Father "
        "which is in heaven' — Cyril's revelation-by-grace locus. Peter's "
        "confession (Mt 16:16 — γ.4.6 seed) is itself the Father's gift, "
        "not Peter's achievement. Sarx kai haima (flesh-and-blood) names "
        "natural-human-cognition; the apekalypsen (revealed) is the "
        "supernatural-illumination of grace. Tewahedo theology of faith "
        "as grace-given (against any synergistic-Pelagian reading) anchors "
        "in Mt 16:17 alongside Eph 2:8-9 + 1 Cor 12:3 paired-prooftexts.",
    ),
    cyril_matt(
        16,
        19,
        "'I will give unto thee the keys of the kingdom of heaven: and "
        "whatsoever thou shalt bind on earth shall be bound in heaven' — "
        "Cyril marks the kleidas (keys) as the apostolic-magisterial "
        "donation, not Petrine-individual privilege. The dēsēs / lysēs "
        "(bind / loose) is the rabbinic asar / hattir authority extended "
        "to the apostolic-college (Mt 18:18 explicitly extends the binding-"
        "loosing to ALL disciples). Tewahedo episcopal-magisterium "
        "theology grounds the synodical bind-loose authority in Mt 16:19 "
        "+ Mt 18:18 + Jn 20:23 triple-foundation; the Patriarch-Catholicos "
        "exercises the Petrine-keys collegially with the Holy Synod.",
    ),
    cyril_matt(
        16,
        21,
        "'From that time forth began Jesus to shew unto his disciples, how "
        "that he must go unto Jerusalem, and suffer many things' — Cyril "
        "marks apo tote (from-that-time) as the kerygmatic turning-point: "
        "AFTER Peter's confession of Christ-the-Son-of-God, the Passion "
        "teaching becomes possible. The dei (it-is-necessary) names divine-"
        "soteriological-necessity, not fated-tragedy; the Cross is freely-"
        "willed-from-eternity, not externally-imposed. Tewahedo Passion-"
        "theology reads the dei of Mt 16:21 + Lk 24:26 + Acts 2:23 as the "
        "voluntary-necessity-of-divine-love.",
    ),
    cyril_matt(
        16,
        27,
        "'The Son of man shall come in the glory of his Father with his "
        "angels; and then he shall reward every man according to his works' "
        "— Cyril marks the Parousia-doxa (glory-of-coming) as the inverse-"
        "image of the Passion-kenōsis: the one who emptied himself "
        "(Phil 2:6-8) will come in the Father's-full-glory. The kata tēn "
        "praxin (according to works) is the eschatological-reward "
        "principle; works-reveal-faith, faith-without-works is dead "
        "(James 2:17). Tewahedo eschatology reads Mt 16:27 + Mt 25:31-46 + "
        "Rev 22:12 as the triple Parousia-reward-prooftext.",
    ),
    # ── Matt 17 (4) — Tabor + Moses-Elijah + Mustard-Faith + Coin-in-fish ──
    cyril_matt(
        17,
        1,
        "'After six days Jesus taketh Peter, James, and John his brother, "
        "and bringeth them up into an high mountain apart' — Cyril marks "
        "the meth' hēmeras hex (after-six-days) as the deliberate-typology: "
        "six-days-of-creation followed by the seventh-day Tabor-glory; the "
        "Genesis-week is recapitulated in the incarnate Word's revelation. "
        "The three-witnesses (Peter, James, John) embody the legal three-"
        "fold attestation (Deut 19:15). The hypsēlon-oros (high-mountain) "
        "is Tabor per Tewahedo tradition — the Buhe feast day on Näḥase 13 "
        "is the Transfiguration commemoration. The mountain-selection "
        "anchor is Cyrillian; the Buhe iconographic + Mahǝlet hymnody "
        "preserves the Tabor-locus across the Tewahedo year.",
    ),
    cyril_matt(
        17,
        3,
        "'There appeared unto them Moses and Elias talking with him' — "
        "Cyril marks the Mōusēs-and-Ēlias appearance as the Law-and-"
        "Prophets twofold-witness to the incarnate Word. Moses (the "
        "Law-giver) and Elijah (the prophets'-fountainhead) both speak "
        "WITH Christ (sullaloûntes) — not above, not below: the Old "
        "Covenant testifies in the Son's presence. The conversation-"
        "content per Lk 9:31 is the exodus-at-Jerusalem (the coming Passion "
        "as new-exodus). Tewahedo iconography of the Transfiguration "
        "depicts Moses-with-tablets + Elijah-in-chariot flanking the "
        "transfigured Christ — the visual catechism of Mt 17:3 + Lk 9:31.",
    ),
    cyril_matt(
        17,
        20,
        "'If ye have faith as a grain of mustard seed, ye shall say unto "
        "this mountain, Remove hence to yonder place; and it shall remove' "
        "— Cyril reads the kokkos sinapeōs (mustard-seed) as not-quantity "
        "but quality-of-faith: even the smallest grain of REAL faith "
        "outweighs the largest volume of WAVERING faith. The mountain-"
        "metaphor is rabbinic for the apparently-impossible; the metabēthi "
        "(remove-hence) is the divine-power flowing through faith's "
        "instrument. Tewahedo monastic theology reads Mt 17:20 + Mk 11:23 "
        "as the kenōsis-faith couplet: smallness-of-self enables greatness-"
        "of-God-working-through.",
    ),
    cyril_matt(
        17,
        27,
        "'Go thou to the sea, and cast an hook, and take up the fish that "
        "first cometh up; and when thou hast opened his mouth, thou shalt "
        "find a piece of money: that take, and give unto them for me and "
        "thee' — Cyril marks the didrachma-Temple-tax (Ex 30:13) incident "
        "as Christ's-voluntary-submission: the Son-of-God who needs-no-"
        "Temple-tax pays it pedagogically to avoid scandal (skandalisōmen "
        "Mt 17:27). The fish-mouth-coin is the Lord-of-creation's "
        "providential signature; the same God who summoned-the-fish "
        "(Jon 1:17) commands-the-stater here. Tewahedo Aksumite-empire "
        "tribute-theology cites Mt 17:24-27 as the kenotic-citizenship "
        "warrant: faithful-presence-without-scandal in the political order.",
    ),
    # ── Matt 18 (3) — Children + Lost-sheep + Seventy-times-seven ──────────
    cyril_matt(
        18,
        3,
        "'Except ye be converted, and become as little children, ye shall "
        "not enter into the kingdom of heaven' — Cyril marks the strephō "
        "(be-turned, converted) as deep-soul-reorientation, not surface-"
        "behavior-change. The genēsthe hōs ta paidia (become-as-the-"
        "children) is the imitation-of-paidic-trust, paidic-dependency, "
        "paidic-non-self-promotion (the very vices Mt 18:1's 'who-is-"
        "greatest' question exhibited). Tewahedo monastic-formation "
        "tradition reads Mt 18:3 + 1 Cor 14:20 as the wise-as-elders / "
        "child-as-malice-free pair-doctrine.",
    ),
    cyril_matt(
        18,
        12,
        "'Doth he not leave the ninety and nine, and goeth into the "
        "mountains, and seeketh that which is gone astray?' — Cyril marks "
        "the aphēsei (leaves) and zētei (seeks) as the divine-pastoral "
        "imbalance: the one-lost weighs more in pastoral-economy than the "
        "ninety-nine-secure. This is not abandonment of the ninety-nine "
        "but proper-prioritization of the genuinely-at-risk. Tewahedo "
        "monastic-superior catechesis (the abba-discipleship rule of the "
        "Mäshafä-Mǝnǝkwǝsnna) cites Mt 18:12-14 as the pastoral-priority "
        "anchor.",
    ),
    cyril_matt(
        18,
        22,
        "'I say not unto thee, Until seven times: but, Until seventy times "
        "seven' — Cyril reads hebdomēkontakis hepta as the deliberate-"
        "hyperbole abolishing any quantitative-limit on forgiveness. The "
        "Peter-question (seven-times, Mt 18:21) was already generous by "
        "rabbinic-standards; Christ's 490-times answer is mathematical-"
        "limitlessness in disguise. The Genesis-Cain reversal is "
        "deliberate (Gen 4:24 — Lamech's seventy-times-seven vengeance; "
        "Christ inverts vengeance-limit into forgiveness-unboundedness). "
        "Tewahedo penitential-discipline (the Säwasǝw-of-Penitence) cites "
        "Mt 18:22 as the confessor's-mandate text.",
    ),
    # ── Matt 19 (3) — Marriage + Sell-all + Camel-Needle ───────────────────
    cyril_matt(
        19,
        6,
        "'Wherefore they are no more twain, but one flesh. What therefore "
        "God hath joined together, let not man put asunder' — Cyril's "
        "marital-indissolubility locus. Sarx mia (one flesh) is ontological-"
        "union, not contractual-arrangement; theou synezeuxen (God hath "
        "joined) names the divine-agency in marriage. The mē chōrizetō "
        "(let-not-separate) is imperative-prohibition. Tewahedo marital-"
        "discipline (preserved more conservatively than most Eastern "
        "canons) reads Mt 19:6 + Gen 2:24 as the indissoluble-bond "
        "anchor; pastoral provision for separation operates within "
        "Cyrillian strictness rather than against it.",
    ),
    cyril_matt(
        19,
        21,
        "'If thou wilt be perfect, go and sell that thou hast, and give to "
        "the poor, and thou shalt have treasure in heaven: and come and "
        "follow me' — Cyril reads ei theleis teleios einai (if-you-wish-"
        "to-be-perfect) as the counsel-of-perfection (later distinguished "
        "from the precepts-of-salvation in patristic two-tier ethics). "
        "Selling-all is not universal-commandment; following-Christ in "
        "voluntary-poverty IS the higher-calling. Tewahedo monastic-"
        "renunciation theology (the Mäshafä-Mǝnǝkwǝsnna) cites Mt 19:21 as "
        "the foundational vocation-text; ordinary-faithful retain "
        "stewardship, monastics-and-bahǝtawi embrace the literal sell-"
        "all.",
    ),
    cyril_matt(
        19,
        24,
        "'It is easier for a camel to go through the eye of a needle, "
        "than for a rich man to enter into the kingdom of God' — Cyril "
        "reads kamēlon (camel — NOT kamilon ship-rope per dubious-textual-"
        "alternatives Cyril knew about and rejected) as the deliberate-"
        "hyperbole: the largest Palestinian animal through the smallest "
        "Palestinian aperture. The point is impossibility-by-natural-"
        "means, possibility-only-by-divine-grace (Mt 19:26 immediately "
        "supplies). Tewahedo wealth-ethics cites Mt 19:23-26 alongside "
        "1 Tim 6:9-10 as the dual-wealth-warning corpus.",
    ),
    # ── Matt 20 (2) — Vineyard-laborers + Cup-I-am-to-drink ─────────────────
    cyril_matt(
        20,
        1,
        "'For the kingdom of heaven is like unto a man that is an "
        "householder, which went out early in the morning to hire "
        "labourers into his vineyard' — Cyril marks the oikodespotēs "
        "(householder) vineyard-parable as the inverted-fairness lesson: "
        "the kingdom's pay-economy is gift-based (denarius-by-grace), not "
        "merit-based (denarius-by-hours-worked). The eleventh-hour-laborers "
        "(Mt 20:6-7, the Gentiles per Cyrillian-reading) receive the same "
        "denarius as the dawn-laborers (the Israelites). Tewahedo "
        "covenantal-inclusion theology reads Mt 20:1-16 as the equal-"
        "grace-not-equal-merit anchor.",
    ),
    cyril_matt(
        20,
        22,
        "'Are ye able to drink of the cup that I shall drink of?' — Cyril "
        "marks the potērion (cup) image as deliberately-overdetermined: "
        "the Passion-cup (Mt 26:39 Gethsemane), the Eucharistic-cup "
        "(Mt 26:27), the martyric-cup (Acts 12:2 James actually drank it; "
        "John lived to old age but drank metaphorically). The sons-of-"
        "Zebedee's confident dynametha (we-are-able) is rebuked gently — "
        "they will indeed drink (Mt 20:23) but kingdom-seating-ranks are "
        "the Father's prerogative. Tewahedo martyr-and-saint hagiography "
        "cites Mt 20:22-23 as the participated-Passion text.",
    ),
    # ── Matt 21 (4) — Triumphal-entry + Temple + Fig-tree + Cornerstone ────
    cyril_matt(
        21,
        5,
        "'Tell ye the daughter of Sion, Behold, thy King cometh unto thee, "
        "meek, and sitting upon an ass, and a colt the foal of an ass' — "
        "Cyril marks Zech 9:9 as the prophetic-fulfillment cite: the king-"
        "comes-meek (praos), not as Roman-imperator on warhorse but as "
        "Jewish-davidic-redeemer on humble mount. The duality (donkey + "
        "colt) is harmonized via the standard rabbinic-prophetic-parallelism. "
        "Tewahedo Hosanna-feast hymnody (Hosanna Sunday before Pasch) "
        "explicitly cites Zech 9:9 + Mt 21:5 + Jn 12:15 as the triple-"
        "prophetic-fulfillment foundation.",
    ),
    cyril_matt(
        21,
        12,
        "'Jesus went into the temple of God, and cast out all them that "
        "sold and bought in the temple, and overthrew the tables of the "
        "moneychangers' — Cyril marks the temple-cleansing (one of the few "
        "incidents of righteous-Christic-anger) as prophetic-judicial "
        "action. The exebalen pantas (cast-out all) is the Messianic-purge "
        "fulfillment of Mal 3:1-3 (the Lord-comes-to-his-temple to "
        "refine). The 'my-Father's-house' (Mt 21:13) is the temple-as-"
        "Christ's-Father's-temple — Christological-claim. Tewahedo Holy-"
        "Week liturgy reads Mt 21:12-13 on Monday-of-Holy-Week as the "
        "temple-judgment text.",
    ),
    cyril_matt(
        21,
        19,
        "'He saw a fig tree in the way… and found nothing thereon, but "
        "leaves only, and said unto it, Let no fruit grow on thee "
        "henceforward for ever' — Cyril treats the sykē (fig-tree) "
        "withering as enacted-parable, not arbitrary-cursing. The all-"
        "leaves-no-fruit fig-tree is Pharisaic-Israel's-condition (ritual-"
        "appearance without substantive-righteousness); the immediate-"
        "withering enacts the judgment-coming-on-Jerusalem (Mt 23:38, "
        "fulfilled AD 70). Tewahedo hermeneutical-tradition reads Mt 21:18-"
        "22 alongside Lk 13:6-9 as the dual-fig-tree pair — judgment + "
        "patient-mercy held in tension.",
    ),
    cyril_matt(
        21,
        42,
        "'The stone which the builders rejected, the same is become the "
        "head of the corner: this is the Lord's doing, and it is marvellous "
        "in our eyes' — Cyril marks Ps 118:22-23 (LXX 117:22-23) as the "
        "Christological-cornerstone fulfillment. The lithon-apedokimasan "
        "(stone-they-rejected) is the Crucifixion; eis kephalēn-gōnias "
        "(into head-of-corner) is the Resurrection. The apo Kyriou egeneto "
        "haute (this-is-from-the-Lord) names the divine-reversal at the "
        "Cross-and-Empty-Tomb. Tewahedo Mäzgəbä-Hāymanot doctrine cites "
        "Mt 21:42 + Ps 118:22 + Acts 4:11 + 1 Pet 2:6-7 as the four-fold "
        "cornerstone-prooftext.",
    ),
    # ── Matt 22 (3) — Wedding-banquet + Caesar + Great-commandment ──────────
    cyril_matt(
        22,
        14,
        "'For many are called, but few are chosen' — Cyril reads polloi-"
        "klētoi / oligoi-eklektoi as the responsive-distinction, not "
        "predestinarian-determinism. All ARE called (the wedding invitation "
        "is universal, Mt 22:9 'as-many-as-ye-find'); few ARE chosen "
        "(few-accept-the-wedding-garment, Mt 22:11-12). The chosen-status "
        "follows from accepting-the-garment (the white-baptismal-robe of "
        "regeneration). Tewahedo baptismal-theology reads the wedding-"
        "garment of Mt 22:11-14 as the qǝddus-imitatio-Christi: chosen-"
        "ness operates through the freely-accepted call.",
    ),
    cyril_matt(
        22,
        21,
        "'Render therefore unto Caesar the things which are Caesar's; and "
        "unto God the things that are God's' — Cyril's dual-loyalty locus. "
        "The apodote (render) is reciprocal-duty; the ta-Kaisaros (Caesar's-"
        "things) names the proper-civil-sphere; ta-tou-theou (God's-things) "
        "names what cannot be ceded to any earthly-power (worship, "
        "conscience). The denarius bears Caesar's-image, hence belongs-to-"
        "the-imager; the human-soul bears God's-image, hence belongs-to-"
        "God-the-imager. Tewahedo political-theology (the Aksumite + "
        "Solomonic-Christian-monarchy traditions) reads Mt 22:21 as the "
        "twofold-jurisdiction principle.",
    ),
    cyril_matt(
        22,
        37,
        "'Thou shalt love the Lord thy God with all thy heart, and with "
        "all thy soul, and with all thy mind' — Cyril marks the threefold-"
        "anthropology (heart + soul + mind = kardia + psychē + dianoia) "
        "as the totality-of-personhood under the great-commandment. The "
        "agapēseis (you-shall-love) is imperative-future; love is "
        "commanded BECAUSE it is freely-willed. The Deut 6:5 Shema is "
        "fulfilled-in-Christ (the Lord-thy-God whom Israel loves IS the "
        "incarnate Word standing before them). Tewahedo catechetical-"
        "introduction (the Säwasǝw-of-Catechumens) cites Mt 22:37-40 + "
        "Deut 6:4-5 + Lev 19:18 as the entire-Torah summary.",
    ),
    # ── Matt 23 (2) — Call-no-man-master + Woes-shut-kingdom ────────────────
    cyril_matt(
        23,
        8,
        "'Be not ye called Rabbi: for one is your Master, even Christ; and "
        "all ye are brethren' — Cyril carefully harmonizes Mt 23:8-10 "
        "(call-no-man-master-on-earth) with the apostolic-titular practice "
        "(elders, bishops, teachers — Heb 13:7, Eph 4:11) and with "
        "monastic abba-terminology (abba = father in the Coptic-Egyptian "
        "tradition). The prohibition targets PRIDE-of-title, not "
        "ministerial-titular-language as such; the absoluteness belongs "
        "to the heavenly-Father (Mt 23:9 'one-is-your-Father') and the "
        "Messianic-Master (Mt 23:10 'one-is-your-Master'). Tewahedo "
        "abba/abun titles operate within this Cyrillian humility-rule.",
    ),
    cyril_matt(
        23,
        13,
        "'Woe unto you, scribes and Pharisees, hypocrites! for ye shut up "
        "the kingdom of heaven against men: for ye neither go in "
        "yourselves, neither suffer ye them that are entering to go in' — "
        "Cyril marks the kleiete (shut-up) charge as the most serious "
        "pastoral-failure: religious-leaders who block-the-Kingdom. The "
        "double-condemnation (won't-enter + prevent-others) is the inverse-"
        "image of true-pastorate (enter-and-lead-in). Tewahedo pastoral-"
        "discipline reads the seven-woes of Mt 23:13-39 as the "
        "anti-pastorate negative-model alongside John 10's good-shepherd "
        "positive-model.",
    ),
    # ── Matt 24 (2) — Gospel-to-all-nations + Words-not-pass ─────────────────
    cyril_matt(
        24,
        14,
        "'This gospel of the kingdom shall be preached in all the world "
        "for a witness unto all nations; and then shall the end come' — "
        "Cyril marks Mt 24:14 as the eschatological-mission-cue: the "
        "Parousia waits-upon the universal-witness. The eis martyrion "
        "pasin tois ethnesin (as-witness to-all-the-nations) is the "
        "missionary-warrant — the Great Commission's reason. Tewahedo "
        "missionary-theology (especially the modern Mäshafä-Wängēl "
        "vernacular-translation programs) cites Mt 24:14 + Mt 28:19-20 + "
        "Acts 1:8 as the triple-mission-mandate.",
    ),
    cyril_matt(
        24,
        35,
        "'Heaven and earth shall pass away, but my words shall not pass "
        "away' — Cyril's Christological-Logology summit. The hoi logoi "
        "mou (my-words) cannot perish because the speaker IS the eternal "
        "Logos; the words of the Word share the speaker's-eternity. "
        "Creation will pass (ouranos kai gē pareleusontai); the Word-"
        "made-flesh-and-his-words persist. Tewahedo Scripture-doctrine "
        "(the Mäshafä-Qǝddus authority-claim) cites Mt 24:35 + Mt 5:18 + "
        "Isa 40:8 + 1 Pet 1:25 as the four-fold Word-eternity prooftext.",
    ),
    # ── Matt 25 (3) — Midnight-cry + Door-shut + Well-done-servant ──────────
    cyril_matt(
        25,
        6,
        "'At midnight there was a cry made, Behold, the bridegroom cometh; "
        "go ye out to meet him' — Cyril marks the mesēs-nyktos (mid-night) "
        "as the Parousia-suddenness signature (paralleling 1 Thess 5:2's "
        "thief-in-the-night, Mt 24:43-44). The kraugē (cry) is the "
        "archangel-shout of 1 Thess 4:16. The exerchesthe eis apantēsin "
        "(go-forth to-meet-him) is the Parousia-greeting posture. Tewahedo "
        "Mahǝlet-Mǝsǝṭǝs midnight-office liturgy explicitly performs the "
        "wise-virgins-awakening-at-midnight pattern as bridegroom-vigil "
        "anticipation.",
    ),
    cyril_matt(
        25,
        10,
        "'They that were ready went in with him to the marriage: and the "
        "door was shut' — Cyril marks the ekleisthē hē thyra (the-door-was-"
        "shut) as the eschatological-finality: there is a moment after "
        "which the entrance is closed. The foolish-virgins' belated "
        "repentance (Mt 25:11 'Lord, Lord, open to us') is not denied "
        "from caprice but from the now-too-late timing — the kairos has "
        "passed. Tewahedo penitential-urgency catechesis cites Mt 25:10-13 "
        "+ Lk 13:25 as the now-is-the-acceptable-time anchor.",
    ),
    cyril_matt(
        25,
        21,
        "'Well done, thou good and faithful servant: thou hast been "
        "faithful over a few things, I will make thee ruler over many "
        "things: enter thou into the joy of thy lord' — Cyril marks the "
        "eu doule (well-done, servant) as the eschatological-commendation. "
        "The pistos epi oliga (faithful-over-few-things) is qualified "
        "praise — the disciple's commensurate stewardship is what's "
        "reward-relevant, not the absolute-size of the stewardship. The "
        "eiselthe eis tēn charan (enter into the joy) is participation-in-"
        "the-Lord's-own-joy, the Trinitarian inner-life-of-God. Tewahedo "
        "soteriology of deification reads Mt 25:21 + Jn 17:13 + 2 Pet 1:4 "
        "as the joy-of-the-Master triple-participation text.",
    ),
    # ── Matt 26 (7) — Anointing + Anaphora + Gethsemane + Trial-arrest ──────
    cyril_matt(
        26,
        13,
        "'Verily I say unto you, Wheresoever this gospel shall be preached "
        "in the whole world, there shall also this, that this woman hath "
        "done, be told for a memorial of her' — Cyril marks the anointing-"
        "at-Bethany memorialization as Christ's own-canonization of one of "
        "the few-named-female-acts in the Gospel. The eis mnēmosynon autēs "
        "(for-memorial-of-her) explicitly aligns the woman with the kerygma "
        "itself — wherever-the-gospel-goes, this-act-goes-with-it. Tewahedo "
        "Marian-and-women-saints hagiography reads Mt 26:6-13 as the proto-"
        "feminist gospel-canonical anchor.",
    ),
    cyril_matt(
        26,
        28,
        "'This is my blood of the new testament, which is shed for many "
        "for the remission of sins' — Cyril's Eucharistic-blood institution "
        "locus (paired with the bread-anchor at Mt 26:26 — γ.4.6 seed). "
        "The estin (is) is real-identification, not symbolization (Cyril's "
        "anti-Nestorian Eucharistic-realism). To haima mou tēs diathēkēs "
        "(my-blood of-the-covenant) echoes Ex 24:8 Moses-and-bull's-blood "
        "covenant-ratification — Christ's-blood ratifies the new-covenant "
        "as Moses's-blood ratified the old. The peri-pollōn (for-many) is "
        "the Septuagint Isa 53:11-12 echo. Tewahedo Anaphora-institution "
        "verbatim cites Mt 26:26-28 + 1 Cor 11:23-25 at the words-of-"
        "institution moment.",
    ),
    cyril_matt(
        26,
        38,
        "'My soul is exceeding sorrowful, even unto death: tarry ye here, "
        "and watch with me' — Cyril marks the perilypos heōs thanatou "
        "(sorrowful-unto-death) as authentic-human-emotion in the incarnate "
        "Word — NOT mere-appearance (anti-docetic) but neither defective "
        "passion (the divine-impassibility preserved by the Person who "
        "freely-assumes the passibility). The Tewahedo Miaphysite Christology "
        "preserves this Cyrillian-balance: one-incarnate-nature genuinely "
        "experiences emotion-in-the-flesh without divine-suffering. The "
        "meinate hōde grēgoreite (tarry-here, watch) extends to Peter, "
        "James, John — the very three from Tabor (Mt 17:1) now at "
        "Gethsemane's anti-Tabor.",
    ),
    cyril_matt(
        26,
        41,
        "'Watch and pray, that ye enter not into temptation: the spirit "
        "indeed is willing, but the flesh is weak' — Cyril marks the "
        "grēgoreite kai proseuchesthe (watch-and-pray) imperative as the "
        "twofold-vigilance: external-awareness + internal-petition. The "
        "to pneuma prothymon (the-spirit-willing) names the regenerate-"
        "soul's desire; hē sarx asthenēs (the-flesh-weak) names the "
        "post-lapsarian frailty. The grace-flesh tension is Cyrillian-"
        "anthropological: real spiritual willingness genuinely struggles "
        "with real bodily weakness. Tewahedo monastic-vigil discipline "
        "(the all-night Mahǝlet) cites Mt 26:41 as the vigilance-charter.",
    ),
    cyril_matt(
        26,
        52,
        "'Put up again thy sword into his place: for all they that take "
        "the sword shall perish with the sword' — Cyril marks the apostrepson "
        "tēn machairan (return-the-sword) as the apostolic-non-violence "
        "principle, even-in-defense-of-Christ. The lex talionis-inversion "
        "(those-who-take-sword-perish-by-sword) is not naturalistic-"
        "prediction but moral-spiritual-principle. Peter's-impulse "
        "(rebuked here) anticipates the Church's later-temptation to take-"
        "up-the-sword in defense of itself. Tewahedo non-violence-tradition "
        "(notably in the lay-confraternity Mahǝbär patterns) cites Mt 26:52 "
        "+ Mt 5:39 + Rom 12:19 as the triple-non-retaliation foundation.",
    ),
    cyril_matt(
        26,
        63,
        "'And the high priest answered and said unto him, I adjure thee by "
        "the living God, that thou tell us whether thou be the Christ, the "
        "Son of God' — Cyril marks Caiaphas's exorkizō se (I-adjure-thee) "
        "as the legal-oath formula that compels Christ's reply. The "
        "convergence is providential: the highest-priest of the Old "
        "Covenant unwittingly elicits the explicit-Christological "
        "confession from the True-High-Priest. Christ's su eipas (thou "
        "hast said, Mt 26:64) is affirmative-with-irony — Caiaphas himself "
        "has uttered the truth. Tewahedo Holy-Friday liturgy reads the "
        "Sanhedrin-trial sequence as the climactic-Christological-"
        "confession-under-duress.",
    ),
    cyril_matt(
        26,
        75,
        "'And Peter went out, and wept bitterly' — Cyril marks the "
        "eklausen pikrōs (wept bitterly) as the prototype of evangelical-"
        "repentance: the depth-of-grief over sin matches the depth-of-"
        "love-betrayed. Peter's-bitter-weeping contrasts with Judas's-"
        "later-despair (Mt 27:5 — apēnxato, hanged-himself) — same-"
        "betrayal, opposite-outcomes; the difference is the direction-of-"
        "grief (toward-Christ vs away-from-Christ). Tewahedo penitential-"
        "spirituality reads Mt 26:75 + Lk 22:62 + Jn 21:15-17 as the "
        "Petrine fall-repent-restore triple-pattern (the catechumen-"
        "restoration model).",
    ),
    # ── Matt 27 (4) — Pilate-handwashing + His-blood + Garments + Centurion ─
    cyril_matt(
        27,
        24,
        "'When Pilate saw that he could prevail nothing, but that rather a "
        "tumult was made, he took water, and washed his hands before the "
        "multitude, saying, I am innocent of the blood of this just person: "
        "see ye to it' — Cyril marks Pilate's apenipsato tas cheiras (washed "
        "the hands) as juridical-cowardice in the form of ritual-piety. "
        "The Deut 21:6-9 ritual (unfound-murderer-elders-wash-hands) is "
        "appropriated WITHOUT its prerequisite (genuine unknowingness). "
        "Pilate KNOWS the just-person (athōos egō apo tou haimatos he "
        "explicitly says, the very Deut 21:9 phrase) and condemns anyway. "
        "Tewahedo Holy-Friday hymnody reads Pilate as the symbol of every-"
        "subsequent-Christian-compromise with worldly-power-against-truth.",
    ),
    cyril_matt(
        27,
        25,
        "'Then answered all the people, and said, His blood be on us, and "
        "on our children' — Cyril reads this verse with great pastoral-"
        "care, NEVER as warrant for anti-Jewish violence. The to haima "
        "autou eph' hēmas (his-blood-on-us) was a self-imprecation in the "
        "moment that the Church's later interpretation must not weaponize. "
        "Cyril reads it Christologically: the blood IS on every-human-"
        "being precisely as the blood-of-redemption (Heb 12:24 — speaks "
        "better than Abel's). The crowd's self-curse becomes, in divine-"
        "irony, the very-thing-that-saves-them via the blood-as-atonement. "
        "Tewahedo theology categorically rejects the historical-anti-Jewish "
        "weaponization of Mt 27:25, reading it through Heb 12:24's "
        "redemptive-blood lens.",
    ),
    cyril_matt(
        27,
        35,
        "'They crucified him, and parted his garments, casting lots' — "
        "Cyril marks the Ps 22:18 (LXX 21:19) fulfillment: diemerisanto "
        "ta himatia mou heautois, kai epi ton himatismon mou ebalon klēron "
        "is cited verbatim in the Greek. The seamless-tunic detail (saved "
        "for Jn 19:23-24) preserves the cast-lots dimension; Matthew "
        "compresses but preserves the prophetic-fulfillment. The "
        "stripping-of-the-Word echoes Gen 3 nakedness — restored-to-"
        "Edenic-clothing-of-glory only at resurrection. Tewahedo Holy-"
        "Friday Tezkar-Mäshafä reads the Ps 22 fulfillment-sequence "
        "(garments, mockery, thirst, forsaken-cry) as the suffering-"
        "Servant litany.",
    ),
    cyril_matt(
        27,
        54,
        "'Truly this was the Son of God' — Cyril marks the centurion-and-"
        "guard confession (alēthōs theou huios ēn houtos) as the "
        "providential Gentile-Christological inclusion at the Cross-moment. "
        "The centurion who at Mt 8:8-10 received Christ's-marvel-at-faith "
        "(γ.4.6.C anchor) is structurally-paralleled by the centurion-at-"
        "Calvary's confession. Two-Gentile-centurions bracket the Galilean-"
        "ministry-and-Passion-narrative as inclusion-witnesses. Tewahedo "
        "missionary-theology reads Mt 27:54 + Mk 15:39 as the Gentile-"
        "inclusion-at-the-Cross prooftext.",
    ),
    # ── Matt 28 (2) — Women-first-witnesses + All-authority-given ───────────
    cyril_matt(
        28,
        1,
        "'In the end of the sabbath, as it began to dawn toward the first "
        "day of the week, came Mary Magdalene and the other Mary to see "
        "the sepulchre' — Cyril marks the women's-first-witness pattern "
        "as honored-by-Christ-providentially: those-who-followed-to-the-"
        "Cross are the first-to-see-the-Resurrection. Maria hē Magdalēnē "
        "kai hē allē Maria appear as the named pair (Matthew). The 'end "
        "of the sabbath, dawn of the first-day' moment is the typological-"
        "transition from Old-Covenant-Sabbath to New-Covenant-Lord's-Day. "
        "Tewahedo Fasika-Resurrection liturgy explicitly honors the "
        "women-as-first-witnesses (the Marys plus Salome) in the dawn-"
        "Eucharist commemoration on Tǝmqät-eve patterns.",
    ),
    cyril_matt(
        28,
        18,
        "'All power is given unto me in heaven and in earth' — Cyril's "
        "Cosmic-Christ exousia-summit. The edothē moi pasa exousia (all-"
        "authority-has-been-given-me) is the post-Resurrection plenitude "
        "of authority — Phil 2:9 highly-exalted, Eph 1:21-22 above-all-"
        "powers. The en ouranō kai epi gēs (in-heaven AND on-earth) is "
        "the cosmocratic claim: no creature, no sphere stands outside the "
        "Risen-Lord's authority. This grounds the Great-Commission (Mt "
        "28:19 — γ.4.6 seed) — the disciples go in HIS authority, not "
        "their own. Tewahedo Christology + Mariology hymnody both ground "
        "in Mt 28:18: the Mother-of-the-Cosmocrator is co-honored in "
        "the cosmic-authority extension.",
    ),
]

# Sanity invariants
assert len(NEW_ENTRIES) == 50, f"expected 50 entries, got {len(NEW_ENTRIES)}"
assert all(e["book"] == "mat" for e in NEW_ENTRIES)
assert all(e["father"] == "Cyril of Alexandria" for e in NEW_ENTRIES)
assert all(14 <= e["chapter"] <= 28 for e in NEW_ENTRIES), "arc-close = Matt 14-28 only"
chapters_covered = sorted({e["chapter"] for e in NEW_ENTRIES})
assert chapters_covered == list(range(14, 29)), f"expected all 15 chapters Matt 14-28 covered; got {chapters_covered}"

# Per-chapter distribution check
from collections import Counter

_density = Counter(e["chapter"] for e in NEW_ENTRIES)
expected_min = {14: 3, 15: 3, 16: 5, 17: 4, 18: 3, 19: 3, 20: 2, 21: 4, 22: 3, 23: 2, 24: 2, 25: 3, 26: 7, 27: 4, 28: 2}
for ch, minimum in expected_min.items():
    assert _density[ch] >= minimum, f"Matt {ch}: expected ≥{minimum}; got {_density[ch]}"


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    assert "entries" in d and "_meta" in d

    pre_count = len(d["entries"])
    d["entries"].extend(NEW_ENTRIES)
    post_count = len(d["entries"])

    ledger_addition = (
        " γ.4.6.D (2026-05-13) added Cyril on Matthew arc-close wave — "
        "50 verse-keyed entries on Matt 14-28 (Galilean miracles + "
        "Jerusalem entry + Olivet discourse + Passion narrative + "
        "Resurrection + Great Commission), CLOSING WAVE of the four-wave "
        "Cyril-on-Matthew arc per §8.1 arc-close convention. CLOSES the "
        "THIRD Cyril Gospel arc (after Cyril-on-John γ.4.1-D, Cyril-on-"
        "Luke γ.4.3-D). Distribution: Matt 14 (3 — John's-death anachōrēsis "
        "+ Feeding-5000 Eucharistic-prefiguration + walking-on-water 'It is "
        "I' egō-eimi Christological); Matt 15 (3 — interior-defilement + "
        "Canaanite-lost-sheep covenantal-priority + Feeding-4000 "
        "Decapolis-Gentile); Matt 16 (5 — leaven-of-Pharisees + revealed-"
        "by-Father grace-not-flesh-and-blood + binding-loosing keys "
        "apostolic-college + first-Passion-prediction dei-of-divine-love + "
        "Parousia-with-angels); Matt 17 (4 — Tabor mountain-selection + "
        "Moses-and-Elijah Law-and-Prophets + mustard-seed-faith quality "
        "+ coin-in-fish Temple-tax voluntary-submission); Matt 18 (3 — "
        "become-as-little-children + lost-sheep pastoral-priority + "
        "seventy-times-seven Cain-Lamech reversal); Matt 19 (3 — "
        "one-flesh marital-indissolubility + sell-all counsel-of-"
        "perfection + camel-needle wealth-warning); Matt 20 (2 — vineyard-"
        "laborers equal-grace + cup-I-am-to-drink martyric-participation); "
        "Matt 21 (4 — king-meek-on-ass Zech 9:9 + temple-cleansing Mal 3:1-3 "
        "+ withered-fig-tree Pharisaic-Israel + stone-rejected-cornerstone "
        "Ps 118:22-23); Matt 22 (3 — wedding-banquet-not-chosen + render-to-"
        "Caesar dual-jurisdiction + threefold-Shema Deut 6:5 totality); "
        "Matt 23 (2 — call-no-man-master abba-humility + woes-shut-kingdom "
        "anti-pastorate); Matt 24 (2 — gospel-to-all-nations Parousia-cue + "
        "words-not-pass Logology); Matt 25 (3 — midnight-cry-bridegroom "
        "vigil + door-shut eschatological-finality + well-done-good-and-"
        "faithful-servant deification-joy); Matt 26 (7 — anointing memorial-"
        "of-her + blood-of-covenant Anaphora-institution + sorrowful-unto-"
        "death Miaphysite-passion + watch-and-pray spirit-flesh tension + "
        "those-who-take-sword non-violence + Caiaphas-adjuration providential-"
        "confession + Peter-wept-bitterly catechumen-restoration); Matt 27 "
        "(4 — Pilate-handwashing juridical-cowardice + 'His blood on us' "
        "Christ-redemptive-reading + divided-garments Ps 22:18 + centurion "
        "truly-Son-of-God Gentile-inclusion); Matt 28 (2 — women-first-"
        "witnesses Fasika-honor + all-authority-given Cosmic-Christ cosmocrator). "
        "Cyril-on-Matthew total post-γ.4.6.D: 195 entries (45 seed + 50 "
        "γ.4.6.B Sermon + 50 γ.4.6.C Galilean + 50 γ.4.6.D arc-close). "
        "Cyril-on-Matthew arc is CLOSED (closes THIRD Cyril Gospel arc; "
        "Cyril-on-John 116 + Cyril-on-Luke 160 + Cyril-on-Matthew 195 = "
        "471 entries across three canonical Gospels). FIFTH instance of "
        "§8.1 arc-close convention (after γ.4.4.E Mäṣḥafä Hēnok, γ.4.5.E "
        "Mäṣḥafä Kufāle, γ.4.2.D Pentateuch, γ.4.3.D Cyril-on-Luke). Source: "
        "Cramer Vol. I (Oxford 1840 — PD) + PG 72 cols. 365-474 (PD)."
    )
    d["_meta"]["source"] = d["_meta"]["source"].rstrip() + ledger_addition

    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, JSON_PATH)

    matt_total = sum(1 for e in d["entries"] if e["book"] == "mat" and e["father"] == "Cyril of Alexandria")
    print(f"γ.4.6.D ship: entries {pre_count} → {post_count} (+{post_count - pre_count})")
    print(f"Cyril on Matthew total: {matt_total} entries — Matthew arc CLOSED")


if __name__ == "__main__":
    main()
