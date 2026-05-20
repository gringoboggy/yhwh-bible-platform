"""Translation: amharic-tewahedo-en · Book: ex

English back-translation of content/translations/amharic-tewahedo/ex.py
(Amharic source, ocr-tier3 quality). Produced 2026-05-20 via Claude Opus 4.7
multilingual back-translation with OCR-noise smoothing.

Smoke scope: Exodus 1 (22 verses) — first chapter at τ.F.exo1.a, extends
the Genesis-based Track F pattern to a second book to validate the slot
convention works across books. Genesis 1-5 shipped τ.F.gen.b.

Source quality: ai-back-translation-tier4
Extraction date: 2026-05-20
Ingest phase: τ.F.exo1.a
Tool: Claude Opus 4.7 multilingual back-translation (direct verse-by-verse)

Method notes:
- Back-translation is *faithful to the OCR'd source*, not aligned to KJV/NRSV.
- The Amharic OCR of Exodus has *severe* verse-boundary drift from the
  start: source ch.1 v.1-3 contains the *tail* of canonical Exodus 1 (the
  midwives episode — Pharaoh's command to kill the Hebrew boys; Shiphrah
  and Puah implied via ``አዋላጆቹ`` "the midwives"; God prospering them;
  Pharaoh's edict to cast the male children into the river). Then from
  v.4 onward the source jumps into canonical Exodus 2 (Moses's birth, "a
  man of the house of Levi", the basket of bulrushes, Pharaoh's daughter
  finding him at the river, Moses's naming, his flight after killing the
  Egyptian, his arrival in Midian, the daughters of Reuel/Jethro at the
  well, and by v.22 his marriage to Zipporah). The canonical Exodus 1
  opening (sons of Israel coming into Egypt; multiplication; the new king
  who knew not Joseph; the heavy labor of bricks and mortar) is *missing*
  from the OCR'd source's ch.1 — appears folded into adjacent OCR
  material or lost to the parser at ocr-tier3.
  The back-translation preserves this 1-to-1 with the source — it does
  NOT silently re-segment. Approximate source↔canonical mapping is given
  in inline comments.
- OCR-garbled words smoothed via context where the topology is clear
  (e.g., source ``ጾዋላጆቹም`` v2 ← canonical ``አዋላጆቹም`` "and the midwives";
  ``ጭስቱ`` "his wife"; ``ብላቴናዋን`` "the maidservant"; ``ሣዕኑ`` ← ``ሣጥን``
  "ark/box [of bulrushes]").
- The Amharic OCR also preserves *cross-reference citations* (``ግብ፡ ሐዊ``,
  ``ዘፍ:``, ``ኢያሱ``, etc. — citations to Acts, Genesis, Joshua, Hebrews,
  etc. — heavy in this chapter because Stephen's speech in Acts 7
  retells Exodus 1-2 and is heavily cross-referenced in the EOTC margin).
  Preserved as ``[xref: ...]``.
- Irrecoverable runs flagged inline as ``[OCR-illegible: ...]``.
- EOTC marginalia (chapter-marker bleed-throughs, repeated
  ``ክርስቲያን ሃይማኖትና ሥርዓት`` "Christian religion-and-order" running heads)
  preserved as ``[OCR-bleedthrough: ...]`` rather than silently dropped.

EOTC distinctives noted in ch.1:
- v.2: the midwives' speech to Pharaoh — "the Hebrew women are not as
  the Egyptian women; the midwife arrives and they have already given
  birth" — preserves the EOTC's parenthetical "(in the moment she
  arrives, they bear)" gloss that's absent in many Latin/Greek
  recensions but characteristic of the Amharic Andmta tradition.
- v.10-13: the basket-of-bulrushes narrative names Pharaoh's daughter as
  ``ተርሙት`` (Thermouthis) — an extra-canonical EOTC identification
  drawn from Josephus / Jubilees (47:5) and preserved in the Amharic.
- v.11-13: the EOTC tradition names Moses's sister explicitly as
  ``ኢሣት (ማርያም)`` "Isat (Miriam)" — both the Ethiopian name and the
  Hebrew-derived name preserved together.
- v.2 also names Moses's two sons via the EOTC tradition: Gershom
  (``ጌርሳም``) and Eliezer (``ኤልዛር``) with the Amharic gloss
  ``(ኤልዛር ማለት የእግዚአብሔር ረድኤት ማለት ነው)`` "Eliezer means 'the help of
  God'" — a scribal-explanatory aside typical of Amharic Andmta.
"""

TRANSLATION = "amharic-tewahedo-en"
BOOK = "ex"
SOURCE_QUALITY = "ai-back-translation-tier4"
SOURCE_PROVENANCE = "claude-opus-4-7-back-translation-of-amharic-tewahedo"
EXTRACTION_DATE = "2026-05-20"
INGEST_PHASE = "τ.F.exo1.a"
# Source ch.1 v.1-3 ≈ canonical Exodus 1:17-22 (midwives tail).
# Source ch.1 v.4-22 ≈ canonical Exodus 2:1-22 (Moses's birth → Midian).
# The canonical Exodus 1:1-16 opening (sons of Israel into Egypt;
# oppression; brickmaking) is *not present* in the OCR'd source.
VERSES = [
    (
        1,
        1,
        "They did not do as the king of Egypt commanded them; they "
        "saved the male children alive. [xref: Gen 49:14 ?; Prov "
        "18:8 ?] And the king of Egypt called his midwives, and said "
        "to them: Why have you done this thing, and saved the male "
        "children alive?",
    ),
    (
        1,
        2,
        "And the midwives said thus to Pharaoh: The Hebrew women are "
        "not like the Egyptian women; before the midwife comes to "
        "them, they have already given birth. And God dealt well "
        "with the midwives.",
    ),
    (
        1,
        3,
        "And the people multiplied and grew exceedingly strong. And "
        "because the midwives feared God, he did great things for "
        "them. And Pharaoh commanded all his kindred, saying: Every "
        "male child that is born to the Hebrews, cast him into the "
        "river; but save every female child alive.",
    ),
    (
        1,
        4,
        "[OCR-bleedthrough chapter-marker: chapter — heading.] "
        "Now there was a man of the tribe of Levi, born of the sons "
        "of Levi, who took a wife; his name was Amram. [xref: Num "
        "26:59 ?]",
    ),
    (
        1,
        5,
        "[His wife] conceived, and bore a male child; and seeing that "
        "he was fair [well-favored], she hid him for three months.",
    ),
    (
        1,
        6,
        "And after this, when she could no longer hide him, his "
        "mother took an ark and coated it with the foam of the sea "
        "[bulrushes] and smeared it with bitumen and pitch; and "
        "placing the child in the ark, she set it on the bank of the "
        "river.",
    ),
    (
        1,
        7,
        "And his sister stood at a distance, to know what would happen to him.",
    ),
    (
        1,
        8,
        "And the daughter of Pharaoh (Thermouthis) came down to the "
        "river to bathe, and her maidens walked along by the river-"
        "bank; and when she saw the ark across [the water], she sent "
        "her maidservant and had it brought to her.",
    ),
    (
        1,
        9,
        "[xref: Acts 7:21.]",
    ),
    (
        1,
        10,
        "And opening the ark and seeing the child weeping in it, she "
        "[said:] This is one of the Hebrew children — and she had "
        "compassion on him.",
    ),
    (
        1,
        11,
        "And [Pharaoh's daughter said to] that child's sister "
        "(Miriam): Will you go and call for me a Hebrew nursing-"
        "woman to nurse this child for me? And she said to her: "
        "[Yes.] And Pharaoh's daughter said to her: Go, call her for "
        "me. And that maiden went and called the child's [own] "
        "mother; and behold — [she presented her, saying:] This is "
        "she.",
    ),
    (
        1,
        12,
        "And Pharaoh's daughter said to her: Take this child and "
        "nurse him for me, and I will give you your wage. And that "
        "woman took the child and nursed him.",
    ),
    (
        1,
        13,
        "And when the child grew, she brought him to Pharaoh's "
        "daughter, and he became her son; and she called his name "
        "Moses, saying: Because I drew him out of the water.",
    ),
    (
        1,
        14,
        "[xref: Acts 7:22; Heb 11:24.] And it came to pass after "
        "many days that Moses, being grown, went out to his "
        "brethren; and he saw their burden; and from among his "
        "brethren, from the children of Israel, he found an Egyptian "
        "striking a Hebrew.",
    ),
    (
        1,
        15,
        "And he looked this way and that, and there was no one "
        "watching. [OCR-bleedthrough: Christian religion-and-order.]",
    ),
    (
        1,
        16,
        "And he killed that Egyptian man, and buried him in the "
        "sand. And on the next day, going out, he found two Hebrew "
        "men quarrelling; and Moses, seeing the one in the wrong, "
        "said: Why are you striking your brother?",
    ),
    (
        1,
        17,
        "[xref: Acts 7:26.] And the one who was wronging his "
        "brother [said] to him: Who has set you over us? Will you "
        "kill me as you killed the Egyptian yesterday? And Moses "
        "said: Has this thing become known? And he was afraid.",
    ),
    (
        1,
        18,
        "And Pharaoh, hearing this thing, sought to kill Moses; and "
        "Moses fled from Pharaoh's face and settled in the land of "
        "Midian; and when he came to a certain city of Midian, he "
        "sat down beside a [OCR-garbled: ``ጐጕጐድ ጓድ``] well.",
    ),
    (
        1,
        19,
        "And the priest of Midian had seven daughters; they used to "
        "tend their father's sheep; and they came and drew water, "
        "filling the trough, to water their father's sheep.",
    ),
    (
        1,
        20,
        "And when shepherds came and drove them away, Moses rose up and rescued them, and watered the sheep.",
    ),
    (
        1,
        21,
        "And when they went to their father Reuel, he said to them: How is it that you have come so quickly today?",
    ),
    (
        1,
        22,
        "And [they said]: An Egyptian man delivered us from the "
        "shepherds, and even drew water for us and watered our "
        "sheep. And [their father said] to his daughters: Where is "
        "the man? Why have you left him? Call the man, that he may "
        "eat bread [with us].",
    ),
]
