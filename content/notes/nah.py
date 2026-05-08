"""
Notes for The Book of Nahum (nah).

No notes yet — add tuples to the NOTES list below or use:
    python3 scripts/add_note.py --book nah --ch <N> --v <V> --anchor "…" \
        --kind comm --title "…" --body "…"

Format (each tuple): (chapter, verse, suffix, anchor, kind, title, label, body_html [, attribution])
The 9th field (attribution) is optional during the v28a-* migration; identifies
the source / provenance of the note (e.g. "User original", "Strong's H7779 (PD)",
"Paraphrase summarising Westermann, Genesis 1-11 (1984)"). After migration
completes, validate_taxonomy.py will require it on every note.
See content/kinds.yaml for legal `kind` values; content/books.yaml for id_prefix.
"""

NOTES = [
    # (ch, v, suf, anchor, kind, title, label, body_html),
]

NOTES_NAH = NOTES  # backward-compat alias
