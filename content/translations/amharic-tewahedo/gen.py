"""Translation: amharic-tewahedo · Book: gen

Π.0 seed shipped 2026-05-14 (Modern Amharic, Tewahedo tradition).
Full ingest is τ.7.x — publisher chooses source (nehemiah-osc.org
modern Amharic; eBible.org amh VPL if available; the parallel-
Bible Amharic column as cross-witness).

Text in Ethiopic script (Unicode block U+1200-U+137F). Read left-
to-right. Pairs with geez-tewahedo (τ.6) as the modern parallel
to the classical liturgical Ge'ez. Together they reproduce the
printed EOTC parallel-Bible inside the EPUB popup system.

The 3-verse Genesis 1:1-3 seed proves the wire-up. The Amharic
matches the standard modern Tewahedo Bible text (1962 BSE first
complete Amharic Bible and subsequent EOTC printings). The exact
Tewahedo edition that drives τ.7.x bulk ingest is publisher-
selected.
"""

TRANSLATION = "amharic-tewahedo"
BOOK = "gen"
VERSES = [
    (1, 1, "በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።"),
    (
        1,
        2,
        "ምድርም ቅርጥ የሌላት ባዶ ነበረች፥ ጨለማም በጥልቁ ላይ ነበረ፤ የእግዚአብሔርም መንፈስ በውኆች ላይ ይንቀሳቀስ ነበር።",
    ),
    (1, 3, "እግዚአብሔርም ብርሃን ይሁን አለ፤ ብርሃንም ሆነ።"),
]
