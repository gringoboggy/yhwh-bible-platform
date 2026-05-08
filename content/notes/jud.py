"""
Notes for The Letter from Jude (jud).

No notes yet — add tuples to the NOTES list below or use:
    python3 scripts/add_note.py --book jud --ch <N> --v <V> --anchor "…" \
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
        1, 1, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-1pe-1-5">1Pe 1:5</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 2, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-1-2">2Pe 1:2</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 3, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-1ti-6-12">1Ti 6:12</a> · <a href="#vnote-php-1-27">Php 1:27</a> · <a href="#vnote-jud-1-20">Jud 1:20</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 4, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-2-1">2Pe 2:1</a> · <a href="#vnote-gal-2-4">Gal 2:4</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 4, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-2-1">2Pe 2:1</a> · <a href="#vnote-gal-2-4">Gal 2:4</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 4, 'b', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-2-1">2Pe 2:1</a> · <a href="#vnote-gal-2-4">Gal 2:4</a> · <a href="#vnote-2pe-2-10">2Pe 2:10</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 5, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-heb-3-16">Heb 3:16</a> · <a href="#vnote-num-26-64">Num 26:64</a> · <a href="#vnote-1co-10-1">1Co 10:1</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 6, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-2-4">2Pe 2:4</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 6, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-2-4">2Pe 2:4</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 6, 'b', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-2-4">2Pe 2:4</a> · <a href="#vnote-mat-25-41">Mat 25:41</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 7, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-deu-29-23">Deu 29:23</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 9, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-zec-3-2">Zec 3:2</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 9, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-zec-3-2">Zec 3:2</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 9, 'b', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-zec-3-2">Zec 3:2</a> · <a href="#vnote-2pe-2-11">2Pe 2:11</a> · <a href="#vnote-deu-34-6">Deu 34:6</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 11, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-2-15">2Pe 2:15</a> · <a href="#vnote-1jn-3-12">1Jn 3:12</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 14, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-deu-33-2">Deu 33:2</a> · <a href="#vnote-heb-11-5">Heb 11:5</a> · <a href="#vnote-psa-50-3">Psa 50:3</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 17, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-3-2">2Pe 3:2</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 18, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2pe-3-3">2Pe 3:3</a> · <a href="#vnote-2ti-4-3">2Ti 4:3</a> · <a href="#vnote-2ti-3-1">2Ti 3:1</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 20, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-eph-6-18">Eph 6:18</a> · <a href="#vnote-rom-8-26">Rom 8:26</a> · <a href="#vnote-1co-14-15">1Co 14:15</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 20, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-eph-6-18">Eph 6:18</a> · <a href="#vnote-rom-8-26">Rom 8:26</a> · <a href="#vnote-1co-14-15">1Co 14:15</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 20, 'b', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-eph-6-18">Eph 6:18</a> · <a href="#vnote-rom-8-26">Rom 8:26</a> · <a href="#vnote-1co-14-15">1Co 14:15</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 21, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-1jn-4-16">1Jn 4:16</a> · <a href="#vnote-heb-9-28">Heb 9:28</a> · <a href="#vnote-lam-3-25">Lam 3:25</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 22, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-jas-5-19">Jas 5:19</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 23, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-1ti-4-16">1Ti 4:16</a> · <a href="#vnote-1co-15-33">1Co 15:33</a> · <a href="#vnote-rev-3-4">Rev 3:4</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 24, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2ti-4-18">2Ti 4:18</a> · <a href="#vnote-eph-3-20">Eph 3:20</a> · <a href="#vnote-col-1-22">Col 1:22</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 24, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2ti-4-18">2Ti 4:18</a> · <a href="#vnote-eph-3-20">Eph 3:20</a> · <a href="#vnote-col-1-22">Col 1:22</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 24, 'b', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-2ti-4-18">2Ti 4:18</a> · <a href="#vnote-eph-3-20">Eph 3:20</a> · <a href="#vnote-col-1-22">Col 1:22</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        1, 25, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-1ti-1-17">1Ti 1:17</a> · <a href="#vnote-rev-5-13">Rev 5:13</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_JUD = NOTES  # backward-compat alias
