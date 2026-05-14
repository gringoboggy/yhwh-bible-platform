"""
Notes for The Book of Meqabyan II (mq2).

No notes yet — add tuples to the NOTES list below or use:
    python3 scripts/add_note.py --book mq2 --ch <N> --v <V> --anchor "…" \
        --kind comm --title "…" --body "…"

Format (each tuple): (chapter, verse, suffix, anchor, kind, title, label, body_html [, attribution])
The 9th field (attribution) is optional during the v28a-* migration; identifies
the source / provenance of the note (e.g. "User original", "Strong's H7779 (PD)",
"Paraphrase summarising Westermann, Genesis 1-11 (1984)"). After migration
completes, validate_taxonomy.py will require it on every note.
See content/kinds.yaml for legal `kind` values; content/books.yaml for id_prefix.
"""

NOTES = [
    (
        1,
        1,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>Opening of 2 Meqabyan: MAQABIS-OF-MOAB (distinct from Maqabis-of-Benjamin in 1 Mq per Horovitz 1905 p. 195 structural distinction explicitly verbatim — &#x27;a Benjamite martyr-father&#x27; vs &#x27;a Moabite king&#x27;). The Moabite-king Maqabis finds the Jews in Syria between the two rivers, slaughters them from the Jabbok river to the square of Jerusalem, destroys the holy city. Functions as PARALLEL-INVERSE of 1 Mq Ch. 1: where 1 Mq&#x27;s tyrant was Chaldean (Ṣiruṣaydan), here the tyrant is Moabite; where there Israel&#x27;s defenders were endangered, here Israel itself is destroyed. The verse establishes Maqabis-of-Moab as the principal protagonist of 2 Mq — beginning his arc at the moral nadir. His subsequent arc (chs. 2-4) is the LONGEST PORTRAIT of a Gentile convert to Mosaic religion in the entire Ethiopian biblical canon.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        1,
        10,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>&#x27;They made the corpses of your servants food for the birds of heaven. They made the flesh of your righteous ones food for the wild beasts of the desert&#x27; — DIRECT QUOTATION of Psalm 79:2-3 (LXX 78:2-3 &#x27;the dead bodies of your servants have they given to be food for the birds of the heaven, the flesh of your saints to the beasts of the earth&#x27;) — a psalm sung specifically about the destruction of Jerusalem and the desecration of the Temple. The quotation locates the present narrative theologically in the post-586-BCE &#x27;lament-over-Jerusalem&#x27; tradition, alongside Lamentations + Jeremiah&#x27;s prophecies + Ezekiel&#x27;s exile-oracles. Meqabyan&#x27;s use of Ps 79 is a structural-citation: the psalm becomes the LITURGICAL FRAME for the 2 Mq destruction-narrative.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        2,
        1,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>Prophet RE&#x27;AY (ረአይ, literally &#x27;Vision&#x27; or &#x27;Seeing&#x27;) arrives at Maqabis-of-Moab&#x27;s court — the PROPHETIC-CONFRONTATION moment. The name functions as proper-name-or-title (&#x27;the Seer,&#x27; cf. 1 Samuel 9:9 &#x27;he that is now called a Prophet was beforetime called a Seer&#x27;). The Geʽez phrasing ረአይ የሚሉት ነቢይ (&#x27;the prophet whom they call Re&#x27;ay&#x27;) is itself ambiguous between proper-name and generic seer-title. Re&#x27;ay functions as the prophetic-mediator who delivers God&#x27;s warning that initiates Maqabis&#x27;s conversion-arc — paralleling Nathan-to-David (2 Sam 12), Elijah-to-Ahab (1 Kgs 21), Jonah-to-Nineveh-king (Jon 3), and Daniel-to-Nebuchadnezzar (Dan 4) in the prophet-confronts-king Hebrew-Bible structural template.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        2,
        4,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>&#x27;Worse than the casting of spears and the shooting of arrows, I will bring upon you grievous HEART-DISEASE, ECZEMA, AND GOUT&#x27; — the prophet&#x27;s DISEASE-CATALOG draws on the DEUTERONOMY 28:27-35 COVENANT-CURSE LIST (&#x27;the LORD shall smite you with the boil of Egypt, and with the hemorrhoids, and with the scab, and with the itch, of which you cannot be healed... he shall smite you in the knees, and in the legs, with a sore botch that cannot be healed&#x27;). The threat is calibrated as worse than warrior&#x27;s-death-by-arrow that Maqabis fears — slow, humiliating, public. Tewahedo penitential preaching cites Deut 28 alongside 2 Mq 2:4 to articulate the category of physical-suffering-as-divine-instruction-to-repent. The chapter closes with Maqabis&#x27;s sackcloth-and-dust penitential response (vv. 9-11) paralleling Jonah 3:6 + Esther 4:1.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        3,
        2,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>MAQABIS-OF-MOAB DIGS A PIT AND ENTERS IT UP TO HIS NECK, weeping in extreme self-mortification — one of the MOST DISTINCTIVE PENITENTIAL IMAGES in Ethiopian biblical literature. The pit-immersion-penance has no direct biblical parallel and appears unique to Meqabyan. The closest analogues are the patristic Egyptian-and-Syrian ascetic-stationary-penance practices (cf. Apophthegmata Patrum on Egyptian solitary-anchorites; Simeon Stylites&#x27;s pillar-station; Theodoret of Cyrus Historia Religiosa on Syrian ascetics). The chapter as a whole is the CONVERSION CHAPTER: God responds through the prophet with a long forgiveness-speech (vv. 3-10) including a direct citation of Exodus 20:5-6 (third-and-fourth-generation / thousandth-generation formula at v. 9). Maqabis emerges from the pit (v. 11), confesses, prostrates himself at the prophet&#x27;s feet, is raised.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        4,
        15,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>MAQABIS-OF-MOAB AS RIGHTEOUS GENTILE CONVERT — Per CROSS_REFERENCE_APPENDIX-broadened parallels: Ruth Rabbah 2:9 (treating Ruth&#x27;s conversion as paradigm for righteous Gentile) + Targum Pseudo-Jonathan on Ruth 1:16 (with explicit conversion-formula expansion). Maqabis&#x27;s reform of his household — removing idols, sorcerers, and diviners (3:16) + learning Torah from the Jewish captive children he had brought from Jerusalem (3:17-19) — is the most explicit Gentile-king-converts-to-Mosaic-religion narrative in the Ethiopian biblical corpus. The chapter develops Maqabis as JUDGE-PATTERN exemplar — paralleling Joshua + Gideon + Samson + Barak + Deborah + Judith (vv. 1-3 catalog) — extending the deliverer-judge typology to the converted-Gentile-king. The theological climax of 2 Meqabyan: a Gentile king becomes a righteous-king-of-Israelite-pattern.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        6,
        1,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>MARTYRDOM-AND-APPEARANCE CHAPTER — structurally parallel to 1 Mq chs. 3-4 but compressed. The sons of Maqabis-of-Moab (named at 2 Mq 13:1 as the SECOND SET of &#x27;five sons of Maqabis,&#x27; mirroring the first five sons of Maqabis-of-Benjamin in 1 Mq — a NUMBER-SYMMETRY across the two books) refuse to sacrifice to Ṣiruṣaydan&#x27;s idols, are burned in fire, then appear post-mortem to the king at night with reproach. The post-mortem-appearance topos is paralleled in 4 Maccabees 17 (the mother-and-seven-sons memorial), in the apocryphal Acts of the Christian martyrs (Polycarp + Perpetua + Felicitas appearance traditions), and in patristic homily on the cult-of-the-martyrs. Meqabyan&#x27;s distinctive feature is the GUILT-INDUCING-REPROACH structure: the appearance is primarily a moral-judgment-on-the-king rather than consolation-for-the-faithful.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        12,
        11,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>DEATH OF ṢIRUṢAYDAN — narrative climax of the trilogy&#x27;s PRINCIPAL VILLAIN-ARC that has run from 1 Mq Ch. 1 through 2 Mq Ch. 12 (the MOST EXTENDED SUSTAINED-VILLAIN narrative in the Meqabyan corpus). Ṣiruṣaydan&#x27;s death pattern echoes the divine-judgment-on-prideful-kings tradition: Nebuchadnezzar at Daniel 4:31-37 (driven to graze like an ox) + Herod at Acts 12:23 (eaten by worms) + Antiochus IV at 2 Maccabees 9 (worm-infested + foul-smelling demise). Per Horovitz 1905 + Dillmann Lexicon Linguae Aethiopicae (1865): Ṣiruṣaydan etymology connects to TYRE + SIDON (Ṣiru + Ṣaydan), the Phoenician-coastal cities + canonical-type for arrogant maritime-commercial power (Ezekiel 26-28 prophecies). The villain-name is itself a TYPOLOGICAL CIPHER rather than historical-king identification.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        14,
        1,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>FOUR SECTARIAN ERRORS ABOUT RESURRECTION named explicitly — THE JEWS, THE SAMARITANS, THE PHARISEES, AND THE SADDUCEES. Meqabyan preserves the Second-Temple-and-Tannaitic categorical distinction between these four groups (cf. Josephus Antiquities 18.1.2-5 on the four philosophical schools; Acts 23:6-8 on Pharisees-and-Sadducees-disagreement-about-resurrection). The &#x27;Jews&#x27; category in Meqabyan refers to non-Christian Israel (&#x27;those who reject the resurrection of the body&#x27;). The chapter is THE LONGEST IN 2 MEQABYAN (36 verses) and the most theologically distinctive: the ANTI-SECTARIAN RESURRECTION-POLEMIC chapter. Meqabyan&#x27;s resurrection-polemic structures around refuting each group&#x27;s specific error — paralleling the Apostles&#x27; Creed clause &#x27;resurrection of the body&#x27; against Marcionite + Gnostic + Sadducean denials.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        14,
        19,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>FOUR-ELEMENTS RESURRECTION — Adam&#x27;s body composed of earth + water + fire + wind, returned to its elements at death, and reconstituted at resurrection by God&#x27;s gathering of those elements. Direct parallel to 3 Mq 4:10 (where the same anthropology is given in the creational rather than resurrectional context). The four-elements doctrine is the EMPEDOCLEAN/GALENIC Greek natural-philosophical anthropology, mediated to Ethiopian Christianity via Syriac and Coptic patristic literature (Ephrem Carmina Nisibena 65; Severus of Antioch Cathedral Homilies). The resurrection-by-elemental-reconstitution-doctrine is also in Tertullian De Resurrectione Carnis §52 + Theophilus of Antioch Ad Autolycum 1.13 (per CROSS_REFERENCE_APPENDIX Stage-3 broadening at 2 Mq 17). The chapter&#x27;s CORD-OF-SHEOL image (vv. 10-23) — the bond dragging soul to Hades grows from mother&#x27;s womb up through life — is a unique metaphor in EOTC literature.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        17,
        1,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>WHEAT-GRAIN DYING ANALOGY for resurrection — develops 1 Corinthians 15:36 (&#x27;thou fool, that which thou sowest is not quickened, except it die&#x27;) + John 12:24 (&#x27;except a corn of wheat fall into the ground and die, it abideth alone: but if it die, it bringeth forth much fruit&#x27;) with a beautiful symbolic-geography expansion: water + earth + sun + wind become resurrection-analogues of body + soul + fire-grace + breath. The vine-and-its-fruit imagery (vv. 5-8) echoes Isaiah 5:1-7 + John 15:1-8 (Christ-the-true-vine). Per CROSS_REFERENCE_APPENDIX Stage-3 broadening: the closest patristic parallels are Tertullian De Resurrectione Carnis §52 + Theophilus of Antioch Ad Autolycum 1.13 (late 2nd c.; earliest extended Christian use of botanical resurrection). The botanical-resurrection argument is one of the MOST DEVELOPED in patristic and Tewahedo eschatology.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    (
        18,
        7,
        "",
        "",
        "comm-ethiopian",
        "Tewahedo — Meqabyan (Ethiopian tradition)",
        "Meqabyan (Ethiopian tradition) (600).",
        '<aside class="note-comm-ethiopian"><strong>Meqabyan (Ethiopian tradition)</strong> <em>Second Book of Meqabyan (Mäṣḥafä Mäqabyan II)</em> <small>(c. 600 AD)</small><p>ADAMIC-MORTALITY DOCTRINE — &#x27;we are all sons of Adam, and we shall all die.&#x27; Direct echo of Romans 5:12 (&#x27;by one man sin entered into the world, and death by sin&#x27;) + 1 Corinthians 15:21-22 (&#x27;since by man came death, by man came also the resurrection of the dead&#x27;). Per CROSS_REFERENCE_APPENDIX-broadened parallels: 2 Baruch 23:4 (&#x27;when Adam sinned and death was decreed&#x27;) + 2 Baruch 48:42-43 + Apocalypse of Moses (Greek LAE) 14:2 (&#x27;on account of you [Adam] toils and labor were assigned to us&#x27;) + 4 Maccabees 18:7-8 (mother&#x27;s-virginity speech, useful for navigating the persistent genre-confusion between Meqabyan and LXX 2/4 Maccabees). The Adamic-mortality doctrine is the THEOLOGICAL FOUNDATION for Meqabyan&#x27;s resurrection-doctrine: humans are mortal BECAUSE OF Adam&#x27;s sin, and the resurrection is God&#x27;s RESTORATIVE-RESPONSE to that primordial mortality.</p></aside>',
        "Mäṣḥafä Mäqabyan I-III (Three Books of Meqabyan, መጽሐፈ መቃብያን) — Tewahedo broader-canon Ethiopian Maccabees, distinct from the Greek LXX 1-4 Maccabees (different content; shared title only). English translation from the Modern Amharic of the EOTC Bible (nehemiah-osc.org) by Claude (Anthropic) with collaborator, May 2026. Creative Commons CC0 1.0 Universal Public Domain Dedication (archive.org/details/three-books-of-meqabyan-cc0-translation). Apparatus integrates Josef Horovitz, 'Das äthiopische Maccabäerbuch,' Zeitschrift für Assyriologie XIX (1905), pp. 194-233 — PD primary scholarly study. 64-citation third-pass audit verdict matrix; 57 verified, 4 errors corrected, 3 interpretive readings flagged, 7 newly discovered parallels added. Dating widened to Aksumite-to-Solomonic Ethiopian Christian range (4th-14th c. CE); precise composition date undetermined in current scholarship per Horovitz 1905 non-commitment. Three books: 1 Mq 36 chapters (Maqabis-of-Benjamin martyrology vs Ṣiruṣaydan); 2 Mq 21 chapters (Maqabis-of-Moab conversion + sons' martyrdom + Ṣiruṣaydan's death); 3 Mq 10 chapters (homiletic + angelological dialogue + Satan-refused-Adam tradition + resurrection-doctrine).",
    ),
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_MQ2 = NOTES  # backward-compat alias
