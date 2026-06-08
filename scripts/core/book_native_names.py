"""book_native_names.py — Ge'ez + Amharic native-script names for the
87-book Ethiopian Tewahedo canon, plus Ethiopic-numeral conversion.

Phase ν.8 (Bilingual ToC). The native names live here rather than in
``content/books.yaml`` because:

  1. ``books.yaml`` is the canonical structural spine — adding two
     more fields per book inflates its line count without helping any
     consumer that doesn't render bilingual labels.
  2. A focused module is easier to maintain and audit (one file owns
     the Ethiopic strings + the standard EOTC nomenclature notes).
  3. Consumers that DO need the native names import them explicitly,
     making the dependency on the bilingual-ToC feature visible at
     the import site (rather than buried in a YAML field).

The names follow the standard Ethiopian Orthodox Tewahedo Church
(EOTC) printed-Bible nomenclature. Where Ge'ez and Amharic differ
(rare in book-name usage — Amharic Bibles typically retain the
Ge'ez book names as honorific titles), both are surfaced separately.

Sources for the standard names:

  - The Haile Selassie I Amharic Bible (1962) — the canonical
    modern Amharic edition.
  - The BFBS 1853 Ge'ez Old Testament + Pell-Platt 1830 Ge'ez NT
    — the historical printed Ge'ez Bibles.
  - The four-volume Ethiopian Tewahedo "Bible with Andemta"
    commentary printed editions.

Ethiopic-numeral system: the project's existing apparatus did not
have a shared numeral converter. The mapping shipped here covers
1-200 (Psalm 151 is the highest canonical chapter number in the
project's 87-book superset, so this comfortably covers every
possible ToC chapter entry).
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Ethiopic numerals
# ---------------------------------------------------------------------
#
# The Ge'ez numeral system is decimal with distinct glyphs for 1-9,
# 10/20/.../90, and 100. Numbers are formed by concatenation: 23 =
# 20 + 3 = ፳፫.
#
# Glyph table (Unicode block: ETHIOPIC NUMBERS, U+1369..U+137C):
#
#   1   ፩   U+1369        20  ፳   U+1373
#   2   ፪   U+136A        30  ፴   U+1374
#   3   ፫   U+136B        40  ፵   U+1375
#   4   ፬   U+136C        50  ፶   U+1376
#   5   ፭   U+136D        60  ፷   U+1377
#   6   ፮   U+136E        70  ፸   U+1378
#   7   ፯   U+136F        80  ፹   U+1379
#   8   ፰   U+1370        90  ፺   U+137A
#   9   ፱   U+1371        100 ፻   U+137B
#   10  ፲   U+1372        10000 ፼ U+137C
#
# For chapter numbers (max 151 in Psalms), we never need 10,000+. The
# converter handles 1-9999 conservatively — anything outside that
# range falls back to the Arabic digit form so a malformed call can't
# crash a build.

_ETHIOPIC_ONES = ["", "፩", "፪", "፫", "፬", "፭", "፮", "፯", "፰", "፱"]
_ETHIOPIC_TENS = ["", "፲", "፳", "፴", "፵", "፶", "፷", "፸", "፹", "፺"]


def ethiopic_numeral(n: int) -> str:
    """Convert a positive integer (1-9999) to Ethiopic numerals.

    Returns the Arabic-digit string for values outside [1, 9999] —
    defensive fall-back so a bogus chapter number can't crash an EPUB
    build. The project's superset canon tops out at Psalm 151, so the
    practical input range is [1, 151].

    Examples:
        ethiopic_numeral(1)    -> '፩'
        ethiopic_numeral(20)   -> '፳'
        ethiopic_numeral(23)   -> '፳፫'
        ethiopic_numeral(100)  -> '፻'
        ethiopic_numeral(151)  -> '፻፶፩'
    """
    if not isinstance(n, int) or n < 1 or n > 9999:
        return str(n)

    if n < 10:
        return _ETHIOPIC_ONES[n]
    if n < 100:
        tens = n // 10
        ones = n % 10
        return _ETHIOPIC_TENS[tens] + _ETHIOPIC_ONES[ones]
    # 100-9999. The Ge'ez convention reads as "(hundreds)፻(tens-ones)".
    # For 100 alone we emit just ፻. For 100*k where k≥2 we prefix the
    # coefficient (e.g. 200 = ፪፻). For the remainder under 100 we
    # use the same tens+ones logic.
    if n < 10000:
        hundreds = n // 100
        rest = n % 100
        if hundreds == 1:
            hundreds_part = "፻"
        else:
            hundreds_part = _ETHIOPIC_ONES[hundreds] + "፻"
        if rest == 0:
            return hundreds_part
        if rest < 10:
            return hundreds_part + _ETHIOPIC_ONES[rest]
        tens = rest // 10
        ones = rest % 10
        return hundreds_part + _ETHIOPIC_TENS[tens] + _ETHIOPIC_ONES[ones]
    return str(n)


# ---------------------------------------------------------------------
# Book-name mappings
# ---------------------------------------------------------------------
#
# Each book's record carries both `geez` and `amharic` keys. For most
# books the two are identical strings — the Ge'ez book title is
# adopted in Amharic Bibles as an honorific. Where the two diverge
# (e.g., Maccabees-named variants), each language gets its own entry.
#
# The chapter-word ("ምዕራፍ" — me'iraf, "chapter") is the same in both
# languages and is centralized below so future tweaks (e.g., adopting
# the alternative spelling ምዕራፍ vs ምእራፍ) land in one place.

CHAPTER_WORD_GEEZ = "ምዕራፍ"  # "me'iraf" — Ge'ez/Amharic for "chapter"
CHAPTER_WORD_AMHARIC = "ምዕራፍ"  # Identical in modern Amharic usage
CHAPTER_WORD_ENGLISH = "Chapter"


# Standard EOTC printed-edition names for the 87-book superset.
# Keys are the project's lowercase 3-letter codes. Values are dicts:
# {"geez": <native>, "amharic": <native>, "english": <english>}.
NATIVE_NAMES: dict[str, dict[str, str]] = {
    # ---- Pentateuch (Orit = "Torah") ----
    "gen": {"geez": "ኦሪት ዘፍጥረት", "amharic": "ኦሪት ዘፍጥረት", "english": "Genesis"},
    "exo": {"geez": "ኦሪት ዘጸአት", "amharic": "ኦሪት ዘጸአት", "english": "Exodus"},
    "lev": {"geez": "ኦሪት ዘሌዋውያን", "amharic": "ኦሪት ዘሌዋውያን", "english": "Leviticus"},
    "num": {"geez": "ኦሪት ዘኍልቍ", "amharic": "ኦሪት ዘኍልቍ", "english": "Numbers"},
    "deu": {"geez": "ኦሪት ዘዳግም", "amharic": "ኦሪት ዘዳግም", "english": "Deuteronomy"},
    # ---- Historical books ----
    "jos": {"geez": "መጽሐፈ ኢያሱ", "amharic": "መጽሐፈ ኢያሱ", "english": "Joshua"},
    "jdg": {"geez": "መጽሐፈ መሣፍንት", "amharic": "መጽሐፈ መሳፍንት", "english": "Judges"},
    "rut": {"geez": "መጽሐፈ ሩት", "amharic": "መጽሐፈ ሩት", "english": "Ruth"},
    "1sa": {"geez": "፩ኛ ሳሙኤል", "amharic": "፩ኛ ሳሙኤል", "english": "1 Samuel"},
    "2sa": {"geez": "፪ኛ ሳሙኤል", "amharic": "፪ኛ ሳሙኤል", "english": "2 Samuel"},
    "1ki": {"geez": "፩ኛ ነገሥት", "amharic": "፩ኛ ነገሥት", "english": "1 Kings"},
    "2ki": {"geez": "፪ኛ ነገሥት", "amharic": "፪ኛ ነገሥት", "english": "2 Kings"},
    "1ch": {"geez": "፩ኛ ዜና መዋዕል", "amharic": "፩ኛ ዜና መዋዕል", "english": "1 Chronicles"},
    "2ch": {"geez": "፪ኛ ዜና መዋዕል", "amharic": "፪ኛ ዜና መዋዕል", "english": "2 Chronicles"},
    "man": {"geez": "ጸሎተ ምናሴ", "amharic": "ጸሎተ ምናሴ", "english": "Prayer of Manasseh"},
    "jub": {"geez": "መጽሐፈ ኩፋሌ", "amharic": "መጽሐፈ ኩፋሌ", "english": "Jubilees"},
    "1en": {"geez": "መጽሐፈ ሄኖክ", "amharic": "መጽሐፈ ሄኖክ", "english": "1 Enoch"},
    "2en": {"geez": "መጽሐፈ ሄኖክ ካልዕ", "amharic": "መጽሐፈ ሄኖክ ካልዕ", "english": "2 Enoch"},
    "ezr": {"geez": "መጽሐፈ ዕዝራ", "amharic": "መጽሐፈ ዕዝራ", "english": "Ezra"},
    "neh": {"geez": "መጽሐፈ ነህምያ", "amharic": "መጽሐፈ ነህምያ", "english": "Nehemiah"},
    "1es": {"geez": "፩ኛ ዕዝራ ካልዕ", "amharic": "፩ኛ ዕዝራ ካልዕ", "english": "1 Esdras"},
    "2es": {"geez": "ዕዝራ ሱቱኤል", "amharic": "ዕዝራ ሱቱኤል", "english": "2 Esdras"},
    "tob": {"geez": "መጽሐፈ ጦቢት", "amharic": "መጽሐፈ ጦቢት", "english": "Tobit"},
    "jdt": {"geez": "መጽሐፈ ዮዲት", "amharic": "መጽሐፈ ዮዲት", "english": "Judith"},
    "est": {"geez": "መጽሐፈ አስቴር", "amharic": "መጽሐፈ አስቴር", "english": "Esther"},
    "aes": {"geez": "ተወሳኪ አስቴር", "amharic": "ተወሳኪ አስቴር", "english": "Additions to Esther"},
    # Mäqabyan trilogy — uniquely Tewahedo canonical (NOT 1-3 Maccabees).
    "mq1": {"geez": "፩ኛ መቃብያን", "amharic": "፩ኛ መቃብያን", "english": "Meqabyan I"},
    "mq2": {"geez": "፪ኛ መቃብያን", "amharic": "፪ኛ መቃብያን", "english": "Meqabyan II"},
    "mq3": {"geez": "፫ኛ መቃብያን", "amharic": "፫ኛ መቃብያን", "english": "Meqabyan III"},
    # ---- Wisdom ----
    "job": {"geez": "መጽሐፈ ኢዮብ", "amharic": "መጽሐፈ ኢዮብ", "english": "Job"},
    "psa": {"geez": "መዝሙረ ዳዊት", "amharic": "መዝሙረ ዳዊት", "english": "Psalms"},
    "pro": {"geez": "መጽሐፈ ምሳሌ", "amharic": "መጽሐፈ ምሳሌ", "english": "Proverbs"},
    "wis": {"geez": "ጥበበ ሰሎሞን", "amharic": "ጥበበ ሰሎሞን", "english": "Wisdom of Solomon"},
    "ecc": {"geez": "መጽሐፈ መክብብ", "amharic": "መጽሐፈ መክብብ", "english": "Ecclesiastes"},
    "sng": {"geez": "መኃልየ መኃልይ", "amharic": "መኃልየ መኃልይ", "english": "Song of Songs"},
    "sir": {"geez": "ጥበበ ሲራክ", "amharic": "ጥበበ ሲራክ", "english": "Sirach"},
    # ---- Major Prophets ----
    "isa": {"geez": "ትንቢተ ኢሳይያስ", "amharic": "ትንቢተ ኢሳይያስ", "english": "Isaiah"},
    "jer": {"geez": "ትንቢተ ኤርምያስ", "amharic": "ትንቢተ ኤርምያስ", "english": "Jeremiah"},
    "lam": {"geez": "ሰቆቃወ ኤርምያስ", "amharic": "ሰቆቃወ ኤርምያስ", "english": "Lamentations"},
    "bar": {"geez": "መጽሐፈ ባሮክ", "amharic": "መጽሐፈ ባሮክ", "english": "Baruch"},
    "lje": {"geez": "መልእክተ ኤርምያስ", "amharic": "መልእክተ ኤርምያስ", "english": "Letter of Jeremiah"},
    "4ba": {"geez": "፬ኛ ባሮክ", "amharic": "፬ኛ ባሮክ", "english": "4 Baruch"},
    "eze": {"geez": "ትንቢተ ሕዝቅኤል", "amharic": "ትንቢተ ሕዝቅኤል", "english": "Ezekiel"},
    "dan": {"geez": "ትንቢተ ዳንኤል", "amharic": "ትንቢተ ዳንኤል", "english": "Daniel"},
    "paz": {"geez": "ጸሎተ አዛርያ", "amharic": "ጸሎተ አዛርያ", "english": "Prayer of Azariah"},
    "sus": {"geez": "ሶስና", "amharic": "ሶስና", "english": "Susanna"},
    "bel": {"geez": "ቤልና ዘንዶ", "amharic": "ቤልና ዘንዶ", "english": "Bel and the Dragon"},
    # ---- Minor Prophets ----
    "hos": {"geez": "ትንቢተ ሆሴዕ", "amharic": "ትንቢተ ሆሴዕ", "english": "Hosea"},
    "joe": {"geez": "ትንቢተ ኢዩኤል", "amharic": "ትንቢተ ኢዩኤል", "english": "Joel"},
    "amo": {"geez": "ትንቢተ አሞጽ", "amharic": "ትንቢተ አሞጽ", "english": "Amos"},
    "oba": {"geez": "ትንቢተ አብድዩ", "amharic": "ትንቢተ አብድዩ", "english": "Obadiah"},
    "jon": {"geez": "ትንቢተ ዮናስ", "amharic": "ትንቢተ ዮናስ", "english": "Jonah"},
    "mic": {"geez": "ትንቢተ ሚክያስ", "amharic": "ትንቢተ ሚክያስ", "english": "Micah"},
    "nah": {"geez": "ትንቢተ ናሆም", "amharic": "ትንቢተ ናሆም", "english": "Nahum"},
    "hab": {"geez": "ትንቢተ ዕንባቆም", "amharic": "ትንቢተ ዕንባቆም", "english": "Habakkuk"},
    "zep": {"geez": "ትንቢተ ሶፎንያስ", "amharic": "ትንቢተ ሶፎንያስ", "english": "Zephaniah"},
    "hag": {"geez": "ትንቢተ ሐጌ", "amharic": "ትንቢተ ሐጌ", "english": "Haggai"},
    "zec": {"geez": "ትንቢተ ዘካርያስ", "amharic": "ትንቢተ ዘካርያስ", "english": "Zechariah"},
    "mal": {"geez": "ትንቢተ ሚልክያስ", "amharic": "ትንቢተ ሚልክያስ", "english": "Malachi"},
    # ---- Gospels ----
    "mat": {"geez": "ወንጌል ዘማቴዎስ", "amharic": "ወንጌል ዘማቴዎስ", "english": "Matthew"},
    "mrk": {"geez": "ወንጌል ዘማርቆስ", "amharic": "ወንጌል ዘማርቆስ", "english": "Mark"},
    "luk": {"geez": "ወንጌል ዘሉቃስ", "amharic": "ወንጌል ዘሉቃስ", "english": "Luke"},
    "jhn": {"geez": "ወንጌል ዘዮሐንስ", "amharic": "ወንጌል ዘዮሐንስ", "english": "John"},
    "act": {"geez": "ግብረ ሐዋርያት", "amharic": "ግብረ ሐዋርያት", "english": "Acts"},
    # ---- Pauline & general epistles ----
    "rom": {"geez": "ሮሜ", "amharic": "ሮሜ", "english": "Romans"},
    "1co": {"geez": "፩ኛ ቆሮንቶስ", "amharic": "፩ኛ ቆሮንቶስ", "english": "1 Corinthians"},
    "2co": {"geez": "፪ኛ ቆሮንቶስ", "amharic": "፪ኛ ቆሮንቶስ", "english": "2 Corinthians"},
    "gal": {"geez": "ገላትያ", "amharic": "ገላትያ", "english": "Galatians"},
    "eph": {"geez": "ኤፌሶን", "amharic": "ኤፌሶን", "english": "Ephesians"},
    "phi": {"geez": "ፊልጵስዩስ", "amharic": "ፊልጵስዩስ", "english": "Philippians"},
    "col": {"geez": "ቆላስይስ", "amharic": "ቆላስይስ", "english": "Colossians"},
    "1th": {"geez": "፩ኛ ተሰሎንቄ", "amharic": "፩ኛ ተሰሎንቄ", "english": "1 Thessalonians"},
    "2th": {"geez": "፪ኛ ተሰሎንቄ", "amharic": "፪ኛ ተሰሎንቄ", "english": "2 Thessalonians"},
    "1ti": {"geez": "፩ኛ ጢሞቴዎስ", "amharic": "፩ኛ ጢሞቴዎስ", "english": "1 Timothy"},
    "2ti": {"geez": "፪ኛ ጢሞቴዎስ", "amharic": "፪ኛ ጢሞቴዎስ", "english": "2 Timothy"},
    "tit": {"geez": "ቲቶ", "amharic": "ቲቶ", "english": "Titus"},
    "phm": {"geez": "ፊልሞና", "amharic": "ፊልሞና", "english": "Philemon"},
    "heb": {"geez": "ዕብራውያን", "amharic": "ዕብራውያን", "english": "Hebrews"},
    "jam": {"geez": "ያዕቆብ", "amharic": "ያዕቆብ", "english": "James"},
    "1pe": {"geez": "፩ኛ ጴጥሮስ", "amharic": "፩ኛ ጴጥሮስ", "english": "1 Peter"},
    "2pe": {"geez": "፪ኛ ጴጥሮስ", "amharic": "፪ኛ ጴጥሮስ", "english": "2 Peter"},
    "1jn": {"geez": "፩ኛ ዮሐንስ", "amharic": "፩ኛ ዮሐንስ", "english": "1 John"},
    "2jn": {"geez": "፪ኛ ዮሐንስ", "amharic": "፪ኛ ዮሐንስ", "english": "2 John"},
    "3jn": {"geez": "፫ኛ ዮሐንስ", "amharic": "፫ኛ ዮሐንስ", "english": "3 John"},
    "jud": {"geez": "ይሁዳ", "amharic": "ይሁዳ", "english": "Jude"},
    "rev": {"geez": "ራእየ ዮሐንስ", "amharic": "ራእየ ዮሐንስ", "english": "Revelation"},
}


def chapter_label_for(language: str, chapter_num: int) -> str:
    """Return the per-chapter label in ``language``.

    Ge'ez/Amharic use the same chapter-word (ምዕራፍ) plus an
    Ethiopic numeral. English uses "Chapter <N>" with an Arabic
    numeral.

    Unknown language values fall back to the Arabic-numeral English
    form so a malformed call still produces something sensible.
    """
    if language == "geez":
        return f"{CHAPTER_WORD_GEEZ} {ethiopic_numeral(chapter_num)}"
    if language == "amharic":
        return f"{CHAPTER_WORD_AMHARIC} {ethiopic_numeral(chapter_num)}"
    return f"{CHAPTER_WORD_ENGLISH} {chapter_num}"


# ---------------------------------------------------------------------
# ToC label formatting (Phase ν.8)
# ---------------------------------------------------------------------
#
# The enum of supported bilingual modes mirrors the field that
# editions.yaml + the /customize UI use. Keeping the canonical set
# here lets the API validator and the build pipeline share one
# source of truth.

TOC_BILINGUAL_OPTIONS: tuple[str, ...] = (
    "none",  # English only (default; back-compat byte-identical builds)
    "geez-english",  # ኦሪት ዘፍጥረት / Genesis
    "amharic-english",  # Same script as Ge'ez but allows publishers to label intent
    "both",  # Ge'ez + Amharic + English (where they differ); de-duplicates if identical
)

# Separator between native and English labels. Spec calls for " / "
# but localizing the separator at one place lets a future right-to-
# left or em-dash variant land without touching every caller.
_LABEL_SEP = " / "


def format_toc_book_label(book_code: str, toc_style: str) -> str:
    """Format ONE book entry's ToC label per ``toc_style``.

    ``toc_style`` is one of TOC_BILINGUAL_OPTIONS. For unknown
    book codes returns the English code uppercased — defensive
    fall-back so a malformed call doesn't crash an EPUB build.

    Idempotency: this function takes only the book CODE (not an
    already-formatted label), so it cannot accidentally wrap an
    already-bilingual string. The caller is responsible for
    arranging the call so each pass starts from a code, not a
    formatted output.

    Examples:
        format_toc_book_label("gen", "none")
            -> "Genesis"
        format_toc_book_label("gen", "geez-english")
            -> "ኦሪት ዘፍጥረት / Genesis"
        format_toc_book_label("gen", "amharic-english")
            -> "ኦሪት ዘፍጥረት / Genesis"
        format_toc_book_label("gen", "both")
            -> "ኦሪት ዘፍጥረት / Genesis"
            (Ge'ez and Amharic identical here so we de-duplicate.)
    """
    rec = NATIVE_NAMES.get(book_code or "")
    english = (rec or {}).get("english") or (book_code or "").upper()

    if toc_style == "none" or not rec:
        return english
    if toc_style == "geez-english":
        return f"{rec['geez']}{_LABEL_SEP}{english}"
    if toc_style == "amharic-english":
        return f"{rec['amharic']}{_LABEL_SEP}{english}"
    if toc_style == "both":
        if rec["geez"] == rec["amharic"]:
            return f"{rec['geez']}{_LABEL_SEP}{english}"
        return f"{rec['geez']}{_LABEL_SEP}{rec['amharic']}{_LABEL_SEP}{english}"
    return english


def format_toc_chapter_label(chapter_num: int, toc_style: str) -> str:
    """Format ONE chapter entry's ToC label per ``toc_style``.

    For "none" the output is just the Arabic digit (this matches
    the existing default-build output and preserves the byte-
    identical guarantee). For bilingual styles the output reads
    e.g. ``"ምዕራፍ ፩ / Chapter 1"``.

    Idempotency: like format_toc_book_label, this takes the raw
    integer rather than an already-formatted label.
    """
    if toc_style == "none":
        return str(chapter_num)
    if toc_style == "geez-english":
        return f"{chapter_label_for('geez', chapter_num)}{_LABEL_SEP}{chapter_label_for('english', chapter_num)}"
    if toc_style == "amharic-english":
        return f"{chapter_label_for('amharic', chapter_num)}{_LABEL_SEP}{chapter_label_for('english', chapter_num)}"
    if toc_style == "both":
        geez_part = chapter_label_for("geez", chapter_num)
        amharic_part = chapter_label_for("amharic", chapter_num)
        english_part = chapter_label_for("english", chapter_num)
        if geez_part == amharic_part:
            return f"{geez_part}{_LABEL_SEP}{english_part}"
        return f"{geez_part}{_LABEL_SEP}{amharic_part}{_LABEL_SEP}{english_part}"
    return str(chapter_num)
