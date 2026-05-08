"""
Notes for The Book of Zephaniah (zep).

No notes yet — add tuples to the NOTES list below or use:
    python3 scripts/add_note.py --book zep --ch <N> --v <V> --anchor "…" \
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
        2, 3, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-amo-5-14">Amo 5:14</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        2, 3, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-amo-5-14">Amo 5:14</a> · <a href="#vnote-isa-26-20">Isa 26:20</a> · <a href="#vnote-jer-29-12">Jer 29:12</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        3, 17, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-psa-149-4">Psa 149:4</a> · <a href="#vnote-psa-147-11">Psa 147:11</a> · <a href="#vnote-isa-62-4">Isa 62:4</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        3, 17, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-psa-149-4">Psa 149:4</a> · <a href="#vnote-psa-147-11">Psa 147:11</a> · <a href="#vnote-isa-62-4">Isa 62:4</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        3, 19, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-isa-49-25">Isa 49:25</a> · <a href="#vnote-isa-60-14">Isa 60:14</a> · <a href="#vnote-jer-30-16">Jer 30:16</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    (
        3, 19, 'a', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-isa-49-25">Isa 49:25</a> · <a href="#vnote-isa-60-14">Isa 60:14</a> · <a href="#vnote-jer-30-16">Jer 30:16</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_ZEP = NOTES  # backward-compat alias
