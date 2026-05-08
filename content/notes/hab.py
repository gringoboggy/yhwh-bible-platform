"""
Notes for The Book of Habakkuk (hab).

No notes yet — add tuples to the NOTES list below or use:
    python3 scripts/add_note.py --book hab --ch <N> --v <V> --anchor "…" \
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
        1, 5, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-act-13-40">Act 13:40</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 1, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-isa-21-8">Isa 21:8</a> · <a href="#vnote-isa-62-6">Isa 62:6</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 2, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-isa-30-8">Isa 30:8</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 2, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-isa-30-8">Isa 30:8</a> · <a href="#vnote-rev-14-13">Rev 14:13</a> · <a href="#vnote-rev-1-18">Rev 1:18</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 3, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-psa-27-14">Psa 27:14</a> · <a href="#vnote-heb-10-36">Heb 10:36</a> · <a href="#vnote-ezk-12-25">Ezk 12:25</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 3, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-psa-27-14">Psa 27:14</a> · <a href="#vnote-heb-10-36">Heb 10:36</a> · <a href="#vnote-ezk-12-25">Ezk 12:25</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 4, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-rom-1-17">Rom 1:17</a> · <a href="#vnote-heb-10-38">Heb 10:38</a> · <a href="#vnote-gal-3-11">Gal 3:11</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 4, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-rom-1-17">Rom 1:17</a> · <a href="#vnote-heb-10-38">Heb 10:38</a> · <a href="#vnote-gal-3-11">Gal 3:11</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 14, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-isa-11-9">Isa 11:9</a> · <a href="#vnote-psa-22-27">Psa 22:27</a> · <a href="#vnote-psa-72-19">Psa 72:19</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 14, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-isa-11-9">Isa 11:9</a> · <a href="#vnote-psa-22-27">Psa 22:27</a> · <a href="#vnote-psa-72-19">Psa 72:19</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 20, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-zec-2-13">Zec 2:13</a> · <a href="#vnote-zep-1-7">Zep 1:7</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 20, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-zec-2-13">Zec 2:13</a> · <a href="#vnote-zep-1-7">Zep 1:7</a> · <a href="#vnote-psa-46-10">Psa 46:10</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        3, 2, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-psa-85-6">Psa 85:6</a> · <a href="#vnote-psa-90-13">Psa 90:13</a> · <a href="#vnote-hos-6-2">Hos 6:2</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        3, 18, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-job-13-15">Job 13:15</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        3, 18, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-job-13-15">Job 13:15</a> · <a href="#vnote-php-4-4">Php 4:4</a> · <a href="#vnote-mic-7-7">Mic 7:7</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        3, 19, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2sa-22-34">2Sa 22:34</a> · <a href="#vnote-psa-18-33">Psa 18:33</a> · <a href="#vnote-php-4-13">Php 4:13</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        3, 19, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2sa-22-34">2Sa 22:34</a> · <a href="#vnote-psa-18-33">Psa 18:33</a> · <a href="#vnote-php-4-13">Php 4:13</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_HAB = NOTES  # backward-compat alias
