"""
content/ — single source of truth for Ethiopian Bible EPUB project data.

Project scope
-------------
The Ethiopian Tewahedo Bible — Scholar's Edition: aiming to be the most
comprehensive study Bible ever assembled in EPUB format. The 87-book
Ethiopian canon (broader than any Catholic, Orthodox, or Protestant
canon), augmented with a deep apparatus of original-language notes
(Hebrew + Septuagint Greek), interpretive commentary, textual-variant
analysis, and cross-references — combining comparative ANE context,
rabbinic and patristic readings, archaeology, and literary parallels.
Depth at every chapter and verse.

Layout
------
  books.yaml          canonical 87-book registry (codes, bxx, files, strategy, ch_count, id_prefix)
  kinds.yaml          commentary note kinds (symbol, css class, label)
  notes/<code>.py     per-book notes lists (one file per canonical book)

All scripts in scripts/ read from here. Legacy locations
(source_archive/, kings_session/) remain for historical reference;
the dead stub directory kings_session/notes/ and the dead shim
kings_session/notes_data.py were removed in the 2026-05-06 sweep.
"""
