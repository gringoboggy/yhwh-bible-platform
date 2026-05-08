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
        1, 17, '', '',
        'xref-citation', 'Cross-ref',
        'Cite.',
        '<strong>Cross-references.</strong> <a href="#vnote-amo-9-11">Amo 9:11</a> · <a href="#vnote-rev-21-27">Rev 21:27</a>. <em>[Reviewer: select 1–3 most relevant; rewrite as a thematic note rather than a list before promoting.]</em>',
        'Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0.',
    ),
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_OBA = NOTES  # backward-compat alias
