"""Translation: geez-tewahedo-en · Book: gen

English back-translation of content/translations/geez-tewahedo/gen.py
(Ge'ez source, ocr-tier3 quality). Produced 2026-05-20 via Claude Opus 4.7
multilingual back-translation with OCR-noise smoothing.

Smoke scope: Genesis 1 only (~31 verses) — proof of concept.
Future chapters: follow the τ.7.x.<letter>.<lang>-en cadence once authorized.

Source quality: ai-back-translation-tier4
Extraction date: 2026-05-20
Ingest phase: τ.F.gen1.a
Tool: Claude Opus 4.7 multilingual back-translation (direct verse-by-verse)

Method notes:
- Back-translation is *faithful to the OCR'd source*, not aligned to KJV/NRSV.
- The Ge'ez OCR has verse-boundary drift: by source-verse ~25 the chapter-2
  chapter-marker (ምዕራፍ ፪) bleeds into the verse content and source-verses
  27-31 cover canonical Gen 2:1-10 material. The back-translation preserves
  this 1-to-1 with the source — it does NOT silently re-segment.
- OCR-garbled words smoothed via context where the topology is clear
  (e.g., source ``በሩዳሚ`` v1 ← canonical ``በቀዳሚ`` "in the beginning";
  ``ኔለማን`` ← ``ጽልመትን`` "darkness"; etc).
- Irrecoverable runs flagged inline as ``[OCR-illegible: ...]``.
"""

TRANSLATION = "geez-tewahedo-en"
BOOK = "gen"
SOURCE_QUALITY = "ai-back-translation-tier4"
SOURCE_PROVENANCE = "claude-opus-4-7-back-translation-of-geez-tewahedo"
EXTRACTION_DATE = "2026-05-20"
INGEST_PHASE = "τ.F.gen1.a"
VERSES = [
    (1, 1, "In the beginning God created the heavens and the earth."),
    (
        1,
        2,
        "And the earth was without form and void; it was not seen, and was "
        "not prepared. And darkness was upon the face of the deep, and the "
        "Spirit of God was hovering upon the face of the waters.",
    ),
    (1, 3, "And God said, Let there be light; and there was light."),
    (
        1,
        4,
        "And God saw the light, that it was good. And God divided between "
        "the light and the darkness. And God called the light Day, and the "
        "darkness he called Night. And there was evening and there was "
        "morning, one day.",
    ),
    (
        1,
        5,
        "And God said, Let there be a firmament in the midst of the waters, "
        "that it may divide between the waters and the waters. And it was "
        "so. And God made the firmament, and divided between the waters "
        "which were above the firmament and the waters which were under "
        "the firmament.",
    ),
    (
        1,
        6,
        "And God called the firmament Heaven; and God saw that it was "
        "good. And there was evening and there was morning, a second day.",
    ),
    (
        1,
        7,
        "And God said, Let the waters which are under the heaven be "
        "gathered together into one place, and let the dry land appear; "
        "and it was so. And the waters were gathered into their "
        "gatherings, and the dry land appeared.",
    ),
    (
        1,
        8,
        "And God called the dry land Earth, and the gathering of the "
        "waters he called Seas. And God saw that it was good.",
    ),
    (
        1,
        9,
        "And God said, Let the earth bring forth tender grass-shoots and "
        "herb yielding seed after its kind and after its likeness, [and "
        "the tree yielding fruit] whose seed is in itself upon the earth, "
        "each after its kind; and it was so.",
    ),
    (
        1,
        10,
        "And the earth brought forth tender grass-shoots, herb yielding "
        "seed after its kind and after its likeness, and the tree which "
        "bears fruit and makes its fruit whose seed is in itself, "
        "yielding [seed] after its kind upon the face of the earth. And "
        "God saw that it was good.",
    ),
    (
        1,
        11,
        "And there was evening and there was morning, a third day. And "
        "God said, Let there be lights in the firmament of the heaven to "
        "give light upon the earth, and to divide between the day and "
        "the night; and let them be for signs and for seasons and for "
        "days and for years; and let them be for lights in the firmament "
        "of the heaven to give light upon the earth; and it was so.",
    ),
    (
        1,
        12,
        "And God made the two great lights [OCR-garbled tail: the greater "
        "to rule the day and the lesser to rule the night, with the "
        "stars also — text mangled but topology preserved].",
    ),
    (
        1,
        13,
        "And God set them in the firmament of the heaven to give light upon the earth.",
    ),
    (
        1,
        14,
        "And to rule over the day and over the night, and to divide "
        "between the light and the darkness; and God saw that it was "
        "good.",
    ),
    (1, 15, "And there was evening and there was morning, a fourth day."),
    (
        1,
        16,
        "[OCR-noisy] And God said: Let the waters bring forth swarming "
        "creatures, living souls, and let birds fly above the earth upon "
        "the face of the firmament of the heaven; and it was so.",
    ),
    (
        1,
        17,
        "And God made the great sea-creatures, and every living soul that "
        "moves which the waters brought forth after their kinds, and "
        "every winged bird after its kind; and God saw that it was good.",
    ),
    (
        1,
        18,
        "And God blessed them, saying: Be fruitful and multiply, and fill "
        "the waters of the seas, and let the birds multiply upon the "
        "earth.",
    ),
    (1, 19, "And there was evening and there was morning, a fifth day."),
    (
        1,
        20,
        "And God said: Let the earth bring forth living souls after their "
        "kinds — cattle and creeping things and beasts of the earth after "
        "their kinds; and it was so. And God made the beasts of the "
        "earth after their kinds and all that creeps upon the earth "
        "after its kind, and the cattle of the earth after their kinds; "
        "and God saw that it was good. And God said: Let us make man in "
        "our image, after our likeness, that he may rule over the fish "
        "of the sea and the beasts of the earth and the birds of the "
        "heaven and the cattle and all the earth and everything that "
        "creeps upon the earth. And God made man, a living being, in "
        "the image of God; male and female he made them.",
    ),
    (
        1,
        21,
        "And God blessed them and said to them: Be fruitful and multiply, "
        "and fill the earth and subdue it; and rule over the fish of the "
        "sea and the beasts of the earth and the birds of the heaven, "
        "and every living thing and everything that creeps upon the "
        "earth.",
    ),
    (
        1,
        22,
        "And God said: Behold, I have given you all the herb-grass "
        "yielding seed which sprouts after its kind, and you shall sow "
        "it upon all the earth; and every tree in which is its seed "
        "yielding seed by its fruit shall be yours for food.",
    ),
    (
        1,
        23,
        "And to all the beasts of the earth, and to all the birds of the "
        "heaven, and to everything that creeps upon the earth in which "
        "is the breath of life, all the green herb shall be for food; "
        "and it was so.",
    ),
    (
        1,
        24,
        "And God saw all that he had made, and behold, it was very good.",
    ),
    (
        1,
        25,
        "And there was evening and there was morning, a sixth day. "
        "[OCR-bleedthrough: Ethiopian Orthodox Tewahedo Church Book of "
        "Genesis, opening of Ethiopia.]",
    ),
    (
        1,
        26,
        "[OCR-bleedthrough chapter-marker: alone, chapter 2.]",
    ),
    (
        1,
        27,
        "The heavens and the earth were finished, and all that is in them.",
    ),
    (
        1,
        28,
        "And God ended on the seventh day his work which he had made; "
        "and God rested on the seventh day from all his works. And God "
        "blessed the seventh day and sanctified it, because on it he "
        "rested from all his work which God had created to make. These "
        "are the generations of the heavens and the earth when they "
        "were created, in the day that the LORD God made the heavens "
        "and the earth.",
    ),
    (
        1,
        29,
        "And every plant of the field before it was in the earth, and "
        "every herb of the field before it grew. For [OCR-illegible: "
        "ጸዳም ሕያዝነመ] the LORD God had not [caused it to rain] upon the "
        "earth.",
    ),
    (
        1,
        30,
        "And there was not a man to till the ground; only a mist went up "
        "from the earth and watered the dry land. And the LORD God "
        "formed man of the dust of the ground, and breathed into his "
        "[OCR-illegible: ጓፅቋ] the breath of life [in the spirit of "
        "holiness?]; and man became a living soul. And the LORD God "
        "gave again from the earth every tree pleasant to the sight "
        "and good for food, and the tree of life in the midst of the "
        "garden, and the tree that gives knowledge of good and evil.",
    ),
    (
        1,
        31,
        "And a river went out from Eden to water the garden; and from "
        "there it was parted, becoming four headwaters of the world.",
    ),
]
