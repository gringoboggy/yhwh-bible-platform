"""
Notes for Paul’s Letter to Philemon (phm).

No notes yet — add tuples to the NOTES list below or use:
    python3 scripts/add_note.py --book phm --ch <N> --v <V> --anchor "…" \
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
        1, 1, '', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 2, '', 'church',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Ekklēsía (<em>ἐκκλησία</em>).</strong> a calling out, i.e. (concretely) a popular meeting, especially a religious congregation (Jewish synagogue, or Christian community of members on earth or saints in heaven or both). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G1577, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, '', 'Lord',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Kýrios (<em>κύριος</em>).</strong> supreme in authority, i.e. (as noun) controller; by implication, Master (as a respectful title). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'a', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'b', 'God',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Theós (<em>θεός</em>).</strong> figuratively, a magistrate; by Hebraism, very. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2316, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'c', 'Grace',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Cháris (<em>χάρις</em>).</strong> graciousness (as gratifying), of manner or act (abstract or concrete; literal, figurative or spiritual; especially the divine influence upon the heart, and its reflection in the life; including gratitude). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5485, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'd', 'peace',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Eirḗnē (<em>εἰρήνη</em>).</strong> peace (literally or figuratively); by implication, prosperity. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G1515, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 3, 'e', 'Father',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Patḗr (<em>πατήρ</em>).</strong> a "father" (literally or figuratively, near or more remote). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G3962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 4, '', 'God',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Theós (<em>θεός</em>).</strong> figuratively, a magistrate; by Hebraism, very. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2316, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 5, '', 'love',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Agápē (<em>ἀγάπη</em>).</strong> love, i.e. affection or benevolence; specially (plural) a love-feast. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G26, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 5, 'a', 'faith',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Pístis (<em>πίστις</em>).</strong> persuasion, i.e. credence; moral conviction (of religious truth, or the truthfulness of God or a religious teacher), especially reliance upon Christ for salvation; abstractly, constancy in such profession; by extension, the system of religious (Gospel) truth itself. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G4102, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 5, 'b', 'Lord',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Kýrios (<em>κύριος</em>).</strong> supreme in authority, i.e. (as noun) controller; by implication, Master (as a respectful title). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 6, '', 'faith',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Pístis (<em>πίστις</em>).</strong> persuasion, i.e. credence; moral conviction (of religious truth, or the truthfulness of God or a religious teacher), especially reliance upon Christ for salvation; abstractly, constancy in such profession; by extension, the system of religious (Gospel) truth itself. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G4102, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 6, 'a', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 7, '', 'love',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Agápē (<em>ἀγάπη</em>).</strong> love, i.e. affection or benevolence; specially (plural) a love-feast. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G26, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 8, '', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 9, '', 'love',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Agápē (<em>ἀγάπη</em>).</strong> love, i.e. affection or benevolence; specially (plural) a love-feast. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G26, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 9, 'a', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 10, '', 'son',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Huiós (<em>υἱός</em>).</strong> a "son" (sometimes of animals), used very widely of immediate, remote or figuratively, kinship. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5207, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 13, '', 'gospel',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Euangélion (<em>εὐαγγέλιον</em>).</strong> a good message, i.e. the gospel. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2098, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 14, '', 'mind',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Noûs (<em>νοῦς</em>).</strong> the intellect, i.e. mind (divine or human; in thought, feeling, or will); by implication, meaning. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G3563, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 15, '', 'season',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Kairós (<em>καιρός</em>).</strong> an occasion, i.e. set or proper time. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2540, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 16, '', 'Lord',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Kýrios (<em>κύριος</em>).</strong> supreme in authority, i.e. (as noun) controller; by implication, Master (as a respectful title). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 16, 'a', 'flesh',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Sárx (<em>σάρξ</em>).</strong> flesh (as stripped of the skin), i.e. (strictly) the meat of an animal (as food), or (by extension) the body (as opposed to the soul (or spirit), or as the symbol of what is external, or as the means of kindred), or (by implication) human nature (with its frailties (physically or morally) and passions), or (specially), a human being (as such). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G4561, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 20, '', 'Lord',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Kýrios (<em>κύριος</em>).</strong> supreme in authority, i.e. (as noun) controller; by implication, Master (as a respectful title). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 23, '', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 25, '', 'Lord',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Kýrios (<em>κύριος</em>).</strong> supreme in authority, i.e. (as noun) controller; by implication, Master (as a respectful title). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G2962, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 25, 'a', 'Christ',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Christós (<em>Χριστός</em>).</strong> anointed, i.e. the Messiah, an epithet of Jesus. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5547, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 25, 'b', 'spirit',
        'lang-greek', 'Greek',
        'Greek.',
        "<strong>Pneûma (<em>πνεῦμα</em>).</strong> a current of air, i.e. breath (blast) or a breeze; by analogy or figuratively, a spirit, i.e. (human) the rational soul, (by implication) vital principle, mental disposition, etc., or (superhuman) an angel, demon, or (divine) God, Christ's spirit, the Holy Spirit. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's G4151, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    (
        1, 25, 'c', 'grace',
        'lang-greek', 'Greek',
        'Greek.',
        '<strong>Cháris (<em>χάρις</em>).</strong> graciousness (as gratifying), of manner or act (abstract or concrete; literal, figurative or spiritual; especially the divine influence upon the heart, and its reflection in the life; including gratitude). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's G5485, A Concise Dictionary of the Words in the Greek Testament, James Strong (1894). PD.",
    ),
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_PHM = NOTES  # backward-compat alias
