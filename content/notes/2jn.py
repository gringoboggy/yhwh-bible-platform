"""
Notes for John’s Second Letter (2jn).

No notes yet — add tuples to the NOTES list below or use:
    python3 scripts/add_note.py --book 2jn --ch <N> --v <V> --anchor "…" \
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
        1, 1, '', 'love',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Agápē (<em>ἀγάπη</em>).</strong> love, i.e. affection or benevolence; specially (plural) a love-feast. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G26, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 1, 'a', 'truth',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Alḗtheia (<em>ἀλήθεια</em>).</strong> truth. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G225, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 2, '', 'truth',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Alḗtheia (<em>ἀλήθεια</em>).</strong> truth. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G225, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, '', 'love',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Agápē (<em>ἀγάπη</em>).</strong> love, i.e. affection or benevolence; specially (plural) a love-feast. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G26, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'a', 'Lord',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Kýrios (<em>κύριος</em>).</strong> supreme in authority, i.e. (as noun) controller; by implication, Master (as a respectful title). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'b', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'c', 'God',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Theós (<em>θεός</em>).</strong> figuratively, a magistrate; by Hebraism, very. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2316, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'd', 'Grace',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Cháris (<em>χάρις</em>).</strong> graciousness (as gratifying), of manner or act (abstract or concrete; literal, figurative or spiritual; especially the divine influence upon the heart, and its reflection in the life; including gratitude). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5485, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'e', 'peace',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Eirḗnē (<em>εἰρήνη</em>).</strong> peace (literally or figuratively); by implication, prosperity. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G1515, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'f', 'Son',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Huiós (<em>υἱός</em>).</strong> a "son" (sometimes of animals), used very widely of immediate, remote or figuratively, kinship. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5207, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'g', 'Father',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Patḗr (<em>πατήρ</em>).</strong> a "father" (literally or figuratively, near or more remote). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G3962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'h', 'truth',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Alḗtheia (<em>ἀλήθεια</em>).</strong> truth. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G225, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 4, '', 'Father',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Patḗr (<em>πατήρ</em>).</strong> a "father" (literally or figuratively, near or more remote). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G3962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 4, 'a', 'truth',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Alḗtheia (<em>ἀλήθεια</em>).</strong> truth. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G225, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 5, '', 'love',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Agápē (<em>ἀγάπη</em>).</strong> love, i.e. affection or benevolence; specially (plural) a love-feast. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G26, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 6, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-1jn-5-3">1Jn 5:3</a> · <a href="#vnote-jhn-15-10">Jhn 15:10</a> · <a href="#vnote-1jn-2-24">1Jn 2:24</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 6, 'a', 'love',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Agápē (<em>ἀγάπη</em>).</strong> love, i.e. affection or benevolence; specially (plural) a love-feast. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G26, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 7, '', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 7, 'a', 'flesh',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Sárx (<em>σάρξ</em>).</strong> flesh (as stripped of the skin), i.e. (strictly) the meat of an animal (as food), or (by extension) the body (as opposed to the soul (or spirit), or as the symbol of what is external, or as the means of kindred), or (by implication) human nature (with its frailties (physically or morally) and passions), or (specially), a human being (as such). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G4561, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 8, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-heb-10-35">Heb 10:35</a> · <a href="#vnote-rev-3-11">Rev 3:11</a> · <a href="#vnote-1co-3-14">1Co 3:14</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 9, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-jhn-7-16">Jhn 7:16</a> · <a href="#vnote-col-3-16">Col 3:16</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 9, 'a', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 9, 'b', 'God',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Theós (<em>θεός</em>).</strong> figuratively, a magistrate; by Hebraism, very. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2316, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 9, 'c', 'Son',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Huiós (<em>υἱός</em>).</strong> a "son" (sometimes of animals), used very widely of immediate, remote or figuratively, kinship. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5207, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 9, 'd', 'Father',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Patḗr (<em>πατήρ</em>).</strong> a "father" (literally or figuratively, near or more remote). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G3962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 10, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-tit-3-10">Tit 3:10</a> · <a href="#vnote-rom-16-17">Rom 16:17</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 10, 'a', 'God',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Theós (<em>θεός</em>).</strong> figuratively, a magistrate; by Hebraism, very. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2316, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 11, '', 'God',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Theós (<em>θεός</em>).</strong> figuratively, a magistrate; by Hebraism, very. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2316, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_2JN = NOTES  # backward-compat alias
