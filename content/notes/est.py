"""
Notes for The Book of Esther (est).

No notes yet — add tuples to the NOTES list below or use:
    python3 scripts/add_note.py --book est --ch <N> --v <V> --anchor "…" \
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
        1, 8, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1, 10, '', 'heart',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Lêb (<em>לֵב</em>).</strong> the heart; also used (figuratively) very widely for the feelings, the will and even the intellect; likewise for the centre of anything. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H3820, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1, 22, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        3, 11, '', 'good',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Ṭôwb (<em>טוֹב</em>).</strong> good (as an adjective) in the widest sense; used likewise as a noun, both in the masculine and the feminine, the singular and the plural (good, a good or good thing, a good man or woman; the good, goods or good things, good men or women), also as an adverb (well). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H2896, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        4, 11, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        4, 11, 'a', 'woman',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼishshâh (<em>אִשָּׁה</em>).</strong> a woman. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H802, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        4, 14, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-gen-45-4">Gen 45:4</a> · <a href="#vnote-1sa-12-22">1Sa 12:22</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        4, 14, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-gen-45-4">Gen 45:4</a> · <a href="#vnote-1sa-12-22">1Sa 12:22</a> · <a href="#vnote-isa-54-17">Isa 54:17</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        4, 14, 'b', 'peace',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Shâlôwm (<em>שָׁלוֹם</em>).</strong> safe, i.e. (figuratively) well, happy, friendly; also (abstractly) welfare, i.e. health, prosperity, peace. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H7965, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        4, 16, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-act-20-24">Act 20:24</a> · <a href="#vnote-2ch-20-3">2Ch 20:3</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        5, 4, '', 'good',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Ṭôwb (<em>טוֹב</em>).</strong> good (as an adjective) in the widest sense; used likewise as a noun, both in the masculine and the feminine, the singular and the plural (good, a good or good thing, a good man or woman; the good, goods or good things, good men or women), also as an adverb (well). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H2896, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        5, 9, '', 'heart',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Lêb (<em>לֵב</em>).</strong> the heart; also used (figuratively) very widely for the feelings, the will and even the intellect; likewise for the centre of anything. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H3820, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        5, 11, '', 'glory',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Kâbôwd (<em>כָּבוֹד</em>).</strong> properly, weight, but only figuratively in a good sense, splendor or copiousness. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H3519, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        5, 12, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        6, 6, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        6, 6, 'a', 'heart',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Lêb (<em>לֵב</em>).</strong> the heart; also used (figuratively) very widely for the feelings, the will and even the intellect; likewise for the centre of anything. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H3820, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        6, 7, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        6, 9, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        6, 11, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        7, 5, '', 'heart',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Lêb (<em>לֵב</em>).</strong> the heart; also used (figuratively) very widely for the feelings, the will and even the intellect; likewise for the centre of anything. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H3820, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        7, 9, '', 'good',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Ṭôwb (<em>טוֹב</em>).</strong> good (as an adjective) in the widest sense; used likewise as a noun, both in the masculine and the feminine, the singular and the plural (good, a good or good thing, a good man or woman; the good, goods or good things, good men or women), also as an adverb (well). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H2896, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        8, 8, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        8, 16, '', 'light',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼôwr (<em>אוֹר</em>).</strong> illumination or (concrete) luminary (in every sense, including lightning, happiness, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H216, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        8, 17, '', 'land',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼerets (<em>אֶרֶץ</em>).</strong> the earth (at large, or partitively a land). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H776, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        8, 17, 'a', 'good',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Ṭôwb (<em>טוֹב</em>).</strong> good (as an adjective) in the widest sense; used likewise as a noun, both in the masculine and the feminine, the singular and the plural (good, a good or good thing, a good man or woman; the good, goods or good things, good men or women), also as an adverb (well). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H2896, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        8, 17, 'b', 'fear',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Yirʼâh (<em>יִרְאָה</em>).</strong> fear (also used as infinitive); morally, reverence. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H3374, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        9, 2, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        9, 2, 'a', 'fear',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Yirʼâh (<em>יִרְאָה</em>).</strong> fear (also used as infinitive); morally, reverence. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H3374, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        9, 3, '', 'fear',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Yirʼâh (<em>יִרְאָה</em>).</strong> fear (also used as infinitive); morally, reverence. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H3374, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        9, 4, '', 'man',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼâdâm (<em>אָדָם</em>).</strong> ruddy i.e. a human being (an individual or the species, mankind, etc.). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H120, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        9, 19, '', 'good',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Ṭôwb (<em>טוֹב</em>).</strong> good (as an adjective) in the widest sense; used likewise as a noun, both in the masculine and the feminine, the singular and the plural (good, a good or good thing, a good man or woman; the good, goods or good things, good men or women), also as an adverb (well). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H2896, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        9, 22, '', 'good',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Ṭôwb (<em>טוֹב</em>).</strong> good (as an adjective) in the widest sense; used likewise as a noun, both in the masculine and the feminine, the singular and the plural (good, a good or good thing, a good man or woman; the good, goods or good things, good men or women), also as an adverb (well). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H2896, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        9, 30, '', 'peace',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Shâlôwm (<em>שָׁלוֹם</em>).</strong> safe, i.e. (figuratively) well, happy, friendly; also (abstractly) welfare, i.e. health, prosperity, peace. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H7965, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        10, 1, '', 'land',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>ʼerets (<em>אֶרֶץ</em>).</strong> the earth (at large, or partitively a land). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H776, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        10, 3, '', 'peace',
        'lang-hebrew', 'Hebrew',
        'Hebrew.',
        '<strong>Shâlôwm (<em>שָׁלוֹם</em>).</strong> safe, i.e. (figuratively) well, happy, friendly; also (abstractly) welfare, i.e. health, prosperity, peace. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>',
        "Strong's H7965, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_EST = NOTES  # backward-compat alias
