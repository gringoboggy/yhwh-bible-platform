"""
Notes for The Book of Obadiah (oba).

No notes yet — add tuples to the NOTES list below or use:
    python3 scripts/add_note.py --book oba --ch <N> --v <V> --anchor "…" \
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
        "GOD",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>ʼĕlôhîym (<em>אֱלֹהִים</em>).</strong> gods in the ordinary sense; but specifically used (in the plural thus, especially with the article) of the supreme God; occasionally applied by way of deference to magistrates; and sometimes as a superlative. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H430, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        1,
        "a",
        "Lord",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>ʼădônây (<em>אֲדֹנָי</em>).</strong> the Lord (used as a proper name of God only). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H136, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        3,
        "",
        "ground",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>ʼădâmâh (<em>אֲדָמָה</em>).</strong> soil (from its general redness). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H127, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        3,
        "a",
        "heart",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>Lêb (<em>לֵב</em>).</strong> the heart; also used (figuratively) very widely for the feelings, the will and even the intellect; likewise for the centre of anything. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H3820, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        4,
        "",
        "LORD",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>ʼădônây (<em>אֲדֹנָי</em>).</strong> the Lord (used as a proper name of God only). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H136, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        7,
        "",
        "peace",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>Shâlôwm (<em>שָׁלוֹם</em>).</strong> safe, i.e. (figuratively) well, happy, friendly; also (abstractly) welfare, i.e. health, prosperity, peace. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H7965, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        8,
        "",
        "LORD",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>ʼădônây (<em>אֲדֹנָי</em>).</strong> the Lord (used as a proper name of God only). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H136, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        15,
        "",
        "LORD",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>ʼădônây (<em>אֲדֹנָי</em>).</strong> the Lord (used as a proper name of God only). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H136, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        16,
        "",
        "holy",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>Qâdôwsh (<em>קָדוֹשׁ</em>).</strong> sacred (ceremonially or morally); (as noun) God (by eminence), an angel, a saint, a sanctuary. <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H6918, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        17,
        "",
        "",
        "xref-citation",
        "Cross-ref",
        "Cite.",
        '<strong>Cross-references.</strong> <a href="index_split_050.html#ch-b50-c9">Amo 9:11</a> · <a href="index_split_060.html#ch-b86-c21">Rev 21:27</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        "Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.",
    ),
    (
        1,
        18,
        "",
        "LORD",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>ʼădônây (<em>אֲדֹנָי</em>).</strong> the Lord (used as a proper name of God only). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H136, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    (
        1,
        21,
        "",
        "LORD",
        "lang-hebrew",
        "Hebrew",
        "Hebrew.",
        "<strong>ʼădônây (<em>אֲדֹנָי</em>).</strong> the Lord (used as a proper name of God only). <em>[Reviewer: extend this with context, theological reading, and any cross-canon resonance before promoting.]</em>",
        "Strong's H136, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD.",
    ),
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_OBA = NOTES  # backward-compat alias
