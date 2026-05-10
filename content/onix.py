"""
onix.py — ONIX 3.0 metadata config for retailer / distributor catalogs.

Per-edition ONIX records are emitted by ``scripts/build_onix.py``. Each
record describes one EPUB product as Amazon / Apple Books / Kobo /
OverDrive / ProQuest would catalog it. Fields marked TODO_* must be
filled in before submission to a distributor.

The structure follows ONIX for Books 3.0 reference names. Code list
values use the official ONIX code lists (Issue 67+) and BISAC subject
codes.

REFERENCE:
  ONIX 3.0:    https://www.editeur.org/93/Release-3.0-Downloads/
  Code lists:  https://www.editeur.org/14/Code-Lists/
  BISAC:       https://bisg.org/page/bisacedition
"""

# ──────────────────────────────────────────────────────────────────
# Project-wide defaults applied to every edition unless overridden.
# ──────────────────────────────────────────────────────────────────

DEFAULTS = {
    # Publisher / imprint
    "publisher": "TODO_PUBLISHER_NAME",  # Legal entity publishing the work
    "imprint": "",  # Often same as publisher; leave empty if so
    "publisher_country": "US",  # ISO 3166-1 alpha-2
    # Primary contributor (the editor of the apparatus)
    "contributor": {
        "role": "B01",  # ONIX list 17. B01=Edited by; A01=Author
        "name": "TODO_CONTRIBUTOR_FULL_NAME",
        "name_inverted": "TODO_LAST, First",  # "Last, First" — required for catalog sorting
        "biographical_note": "",
    },
    # Languages — ISO 639-2/B 3-letter codes
    "language": {
        "primary": "eng",  # English (base translation + apparatus)
        "secondary": [  # Auxiliary languages used in apparatus
            "heb",  # Hebrew (with vowel-pointing)
            "grc",  # Ancient Greek (LXX, NT)
            "gez",  # Ge'ez (classical Ethiopic)
            "amh",  # Amharic (modern Ethiopic)
        ],
    },
    # Publication
    "publication_date": "TODO_YYYYMMDD",  # ONIX requires 8-digit YYYYMMDD
    "copyright_year": "TODO_YYYY",
    "edition_type": "REV",  # ONIX list 21. REV=Revised; CRI=Critical; SCH=Scholarly
    # Audience
    "audience": {
        "code": "04",  # ONIX list 28. 04=Professional/scholarly
        "description": (
            "Scholarly readers, clergy, students of biblical languages and traditions, and serious lay readers."
        ),
    },
    # Product form (digital ebook)
    "product_form": "EB",  # ONIX list 150. EB=E-publication
    "product_form_detail": "E101",  # ONIX list 175. E101=EPUB
    # Approximate measure (87-book corpus + apparatus)
    "word_count": 950000,  # Order-of-magnitude; refine if desired
    # Sales rights — start worldwide non-exclusive; tighten per-territory later
    "sales_rights": {
        "type": "01",  # ONIX list 46. 01=Sale w/ non-exclusive rights
        "territory": "WORLD",  # ONIX uses "WORLD" or ISO country lists
    },
    # Default supplier / availability stub (each retailer can override)
    "supply": {
        "role": "01",  # ONIX list 93. 01=Publisher to end-customers
        "availability": "20",  # ONIX list 65. 20=Available
        "price": {
            "type": "02",  # ONIX list 58. 02=RRP excluding tax
            "amount": "TODO_PRICE_USD",  # Decimal e.g. "29.99"
            "currency": "USD",
        },
    },
}


# ──────────────────────────────────────────────────────────────────
# Per-edition records. Each becomes one <Product> in the ONIX message.
# ──────────────────────────────────────────────────────────────────

EDITIONS = [
    {
        "id": "ethiopian-tewahedo",
        "isbn": "TODO_ISBN_13_ETHIOPIAN",
        "title_full": "The Ethiopian Tewahedo Bible — Scholar's Edition",
        "title_subtitle": ("The 87-Book Canon with Andemta Tradition Apparatus"),
        "description": (
            "The complete Ethiopian Tewahedo canon — the broadest "
            "scriptural canon of any Christian tradition, comprising 87 "
            "books — presented in a critical study apparatus that "
            "integrates classical Andemta commentary, Synaxarium "
            "references, and Ge'ez linguistic notes alongside Hebrew, "
            "Greek, and contextual Ancient Near Eastern analysis. "
            "Distinctive content includes 1 Enoch, Jubilees, and Meqabyan "
            "I-III with full cross-canon parallel references."
        ),
        "bisac": [
            "REL049000",  # Christianity / Orthodox
            "REL006040",  # Biblical Studies / Old Testament / General
            "REL006400",  # Biblical Studies / Bible Reference
        ],
    },
    {
        "id": "catholic-study",
        "isbn": "TODO_ISBN_13_CATHOLIC",
        "title_full": "The Catholic Study Bible — Annotated Edition",
        "title_subtitle": ("The Deuterocanonical Canon with Patristic and Magisterial Apparatus"),
        "description": (
            "The Catholic deuterocanonical canon presented with a study "
            "apparatus drawing on the Church Fathers (Augustine, Jerome, "
            "Chrysostom, Aquinas), conciliar definitions, and the modern "
            "Magisterium. Features Hebrew and Greek lexical notes, "
            "parallel passage references, and detailed commentary on each "
            "book of the deuterocanon (Tobit, Judith, Wisdom, Sirach, "
            "Baruch, 1-2 Maccabees, plus Greek additions to Daniel and "
            "Esther)."
        ),
        "bisac": [
            "REL006020",  # Biblical Studies / Bible / Catholic
            "REL006040",
            "REL006400",
        ],
    },
    {
        "id": "evangelical-reformed",
        "isbn": "TODO_ISBN_13_EVANGELICAL",
        "title_full": "The Reformed Study Bible — Annotated Edition",
        "title_subtitle": ("The Protestant Canon with Reformation and Modern Critical Apparatus"),
        "description": (
            "The 66-book Protestant canon with a study apparatus rooted "
            "in the Reformed tradition — Calvin, Luther, the Westminster "
            "divines, modern evangelical scholarship — alongside "
            "patristic-era commentary (Augustine especially) and rigorous "
            "Hebrew and Greek lexical analysis. Notes on textual variants, "
            "cross-canon parallels, and biblical theology."
        ),
        "bisac": [
            "REL006080",  # Biblical Studies / Bible / Protestant
            "REL006400",
            "REL082000",  # Theology
        ],
    },
    {
        "id": "jewish-study",
        "isbn": "TODO_ISBN_13_JEWISH",
        "title_full": "The Tanakh Study Bible — Critical Edition",
        "title_subtitle": ("Hebrew Scripture with Rabbinic, Targumic, and Modern Apparatus"),
        "description": (
            "The Tanakh in its traditional tripartite order (Torah, "
            "Nevi'im, Ketuvim) with a study apparatus drawing on classical "
            "rabbinic sources (Rashi, Maimonides, Ibn Ezra, the Targumim, "
            "the Talmud, and the major Midrashim), modern Jewish biblical "
            "scholarship (Sarna, Levenson, Alter), and detailed Hebrew "
            "lexical analysis with vowel-pointing and grammatical notes."
        ),
        "bisac": [
            "REL040040",  # Judaism / Sacred Writings
            "REL006040",
            "REL040000",  # Judaism / General
        ],
    },
    {
        "id": "scholarly-academic",
        "isbn": "TODO_ISBN_13_ACADEMIC",
        "title_full": "The Critical Study Bible — Comprehensive Scholarly Edition",
        "title_subtitle": ("All Canons, Full Apparatus — Hebrew, Greek, Ge'ez, ANE Context"),
        "description": (
            "The most comprehensive scholarly edition: all 87 books of the "
            "Ethiopian Tewahedo canon with the full apparatus across every "
            "tradition (patristic, rabbinic, reformation, modern critical, "
            "Ethiopian, Orthodox, Catholic), complete Hebrew with "
            "vowel-pointing, Greek (LXX and NT) lexical notes, Ge'ez "
            "classical-language notes, Ancient Near Eastern parallel-text "
            "apparatus (Enuma Elish, Gilgamesh, Atrahasis, Ugaritic, Code "
            "of Hammurabi), and rigorous textual-variant analysis. "
            "Designed for seminary, university, and research-library use."
        ),
        "bisac": [
            "REL006400",
            "REL006040",
            "REL006700",  # Biblical Studies / Exegesis & Hermeneutics
        ],
    },
]
