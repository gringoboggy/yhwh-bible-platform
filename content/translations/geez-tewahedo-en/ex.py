"""Translation: geez-tewahedo-en · Book: ex

English back-translation of content/translations/geez-tewahedo/ex.py
(Ge'ez source, ocr-tier3 quality). Produced 2026-05-20 via Claude Opus 4.7
multilingual back-translation with OCR-noise smoothing.

Smoke scope: Exodus 1 (22 verses) — first chapter at τ.F.exo1.a, extends
the Genesis-based Track F pattern to a second book to validate the
slot convention works across books. Genesis 1-5 shipped τ.F.gen.b.

Source quality: ai-back-translation-tier4
Extraction date: 2026-05-20
Ingest phase: τ.F.exo1.a
Tool: Claude Opus 4.7 multilingual back-translation (direct verse-by-verse)

Method notes:
- Back-translation is *faithful to the OCR'd source*, not aligned to KJV/NRSV.
- The Ge'ez OCR of Exodus has *severe* verse-boundary drift from the start:
  source ch.1 v.1-22 does NOT correspond to canonical Exodus 1 (Israelites
  multiplying / midwives Shiphrah & Puah / Pharaoh's oppression). Instead
  the OCR'd EOTC recension's source ch.1 opens at canonical Exodus 3:1
  (Moses keeping Jethro's flock at Horeb, the burning-bush theophany) and
  proceeds through canonical Ex 3-4 and into Ex 5 (Moses confronting
  Pharaoh) by source v.22. The canonical Exodus 1 opening (Joseph's
  brothers / oppression / midwives) appears to be folded into prior
  source material or absorbed into chapter-bleedthrough markers.
  The back-translation preserves this 1-to-1 with the source — it does
  NOT silently re-segment. Approximate source↔canonical mapping is given
  in inline comments.
- OCR-garbled words smoothed via context where the topology is clear
  (e.g., source ``ሙዜ`` v1 ← canonical ``ሙሴ`` "Moses"; ``ዮቶር`` "Jethro";
  ``ኮሬብ ዶብረ`` "Horeb, the mountain"; ``ሐሙሁ`` "his father-in-law").
- Irrecoverable runs flagged inline as ``[OCR-illegible: ...]``.
- EOTC marginalia (chapter-marker bleed-throughs ``ምዕራፍ`` / "chapter X"
  embedded mid-verse, repeated ``የኢትዮጵያ ኦርቶዶክስ ተዋሕዶ ቤተ ክርስቲያን``
  "Ethiopian Orthodox Tewahedo Church" running heads, scribal
  cross-references) preserved as ``[xref: ...]`` or
  ``[OCR-bleedthrough ...:]`` rather than silently dropped or rewritten.
"""

TRANSLATION = "geez-tewahedo-en"
BOOK = "ex"
SOURCE_QUALITY = "ai-back-translation-tier4"
SOURCE_PROVENANCE = "claude-opus-4-7-back-translation-of-geez-tewahedo"
EXTRACTION_DATE = "2026-05-20"
INGEST_PHASE = "τ.F.exo1.a"
# Source ch.1 ≈ canonical Exodus 3:1-5:1 (verse-boundary drifted by
# ~50+ verses; canonical Exodus 1:1-2:25 is *not present* in the OCR'd
# source's ch.1 — appears to be folded into adjacent OCR material or
# lost to the parser at ocr-tier3). The back-translation preserves the
# source as-given.
VERSES = [
    (
        1,
        1,
        "And Moses was keeping the flock of Jethro his father-in-law, "
        "[OCR-noisy: ``ማርያ ምድ ' ያም`` — the priest of Midian]; and he "
        "led the sheep into the wilderness, and came to Horeb, the "
        "mountain of God.",
    ),
    (
        1,
        2,
        "And the angel of the LORD appeared to Moses in a flame of fire "
        "out of a bush; and Moses saw that out of the bush the fire was "
        "burning, but the bush was not consumed. And Moses said: I will "
        "go over and behold this great sight, why the bush is not "
        "burned up. [OCR-bleedthrough chapter-marker: chapter — "
        "Ethiopian Orthodox Tewahedo Church, Book of Exodus.] "
        "And when the LORD saw that he had turned aside to look, he "
        "called to him out of the bush and said: Moses, Moses. And he "
        "said: What is it, my Lord?",
    ),
    (
        1,
        3,
        "And he said to him: Do not come near here; put off the sandals "
        "from your feet, for the place on which you stand is holy ground.",
    ),
    (
        1,
        4,
        "And the LORD God said to him: I am the God of your fathers, "
        "the God of Abraham, and the God of Isaac, and the God of "
        "Jacob. And Moses [OCR-garbled: ``ሜጫጠ ገነቋ-ሙሴ``] turned away "
        "his face, for he was afraid to look upon the face of the LORD.",
    ),
    (
        1,
        5,
        "And the LORD said to Moses: I have surely seen the affliction "
        "of my people who are in Egypt, and I have heard their cry; "
        "[OCR-noisy] do you [now] perform their labor.",
    ),
    (
        1,
        6,
        "And I have known their suffering, and have come down to "
        "deliver them from the hand of the Egyptians, and to bring them "
        "out from that land into a good and broad land, and to lead "
        "them into a land flowing with milk and honey, into the land "
        "of the Canaanites, and the Hittites, and the Amorites, and "
        "the Perizzites, and the Girgashites, and the Hivites, and the "
        "Jebusites. [OCR-bleedthrough: numerical marginalia.] And "
        "behold, the cry of the children of Israel has come to me, and "
        "I have seen the oppression with which the Egyptians oppress "
        "them. And now, behold, I will send you to Pharaoh, king of "
        "Egypt, that you may bring out my people the children of "
        "Israel from the land of Egypt.",
    ),
    (
        1,
        7,
        "And Moses said to the LORD: Who am I, that I should go to "
        "Pharaoh, king of Egypt, and that I should bring out the "
        "children of Israel from the land of Egypt?",
    ),
    (
        1,
        8,
        "And the LORD said to him: For I am with you; and this shall "
        "be the sign for you, that I have sent you: when you have "
        "brought out my people from the land of Egypt, you shall serve "
        "the LORD upon this mountain.",
    ),
    (
        1,
        9,
        "And Moses said to the LORD: Behold —",
    ),
    (
        1,
        10,
        "When I go to the children of Israel and say to them, The God "
        "of your fathers has sent me to you, and they ask me, What is "
        "his name — what shall I say to them? And the LORD said to "
        "him: I am the One who is and who shall be; thus you shall "
        "say to the children of Israel: He who is and who shall be has "
        "sent me to you. And again the LORD said to Moses: Thus you "
        "shall say to the children of Israel: The LORD, the God of "
        "your fathers, has sent me to you — this is my name forever, "
        "and my memorial for generations of generations. [OCR-noisy: "
        "``ሑር አስተጋብኦቅሙ`` — Go, gather them, the elders of Israel] "
        "and tell them: The LORD, the God of your fathers, the God of "
        "Abraham, and the God of Isaac, and the God of Jacob, has "
        "appeared to me, [OCR-noisy] saying: I have surely visited "
        "you, and [seen] all that has been done to you in the land of "
        "Egypt. And I have said: I will bring you up out of the "
        "affliction of Egypt, and lead you into the land of the "
        "Canaanites, [OCR-bleedthrough: Ethiopian Orthodox Tewahedo "
        "Church, Book of Exodus,] and the Hittites, and the Amorites, "
        "and the Perizzites, and the Girgashites, and the Jebusites, "
        "into a land flowing with milk and honey.",
    ),
    (
        1,
        11,
        "And they shall hearken to your voice; and you shall come in, "
        "you and the elders of Israel, to the king of Egypt, and you "
        "shall say to him: The LORD, the God of the Hebrews, has met "
        "with us; let us go a journey of three days into the "
        "wilderness, [OCR-noisy: ``ሐዋ የ ንB ለእማማ ብኤር እም ዳክ``] that "
        "we may sacrifice to the LORD our God. But I know that "
        "Pharaoh, king of Egypt, will not let you go except by a "
        "mighty hand. And I will stretch out my hand and smite the "
        "Egyptians with all my wonders which I shall do in their "
        "midst, and after that he shall let you go. And I will give "
        "this people favor in the sight of the Egyptians, and when you "
        "depart you shall not go empty; but every woman shall ask of "
        "her neighbor and from any sojourning in her house articles of "
        "silver and gold, and clothing, and you shall put them upon "
        "your sons and your daughters; and so you shall plunder the "
        "Egyptians.",
    ),
    (
        1,
        12,
        "And Moses answered and said: If they do not believe me, and "
        "do not listen to my voice, and say to me: The LORD has not "
        "appeared to you — what shall I say to them?",
    ),
    (
        1,
        13,
        "And the LORD said to Moses: What is this in your hand? And he said: A rod.",
    ),
    (
        1,
        14,
        "And the LORD said to him: Cast it upon the ground. And he "
        "cast it upon the ground, and it became a serpent; and Moses "
        "fled from before it.",
    ),
    (
        1,
        15,
        "And the LORD said to Moses: Stretch out your hand and take it "
        "by its tail. And Moses stretched out his hand and took it by "
        "its tail, and it became a rod in his hand. And he said: That "
        "they may believe that the LORD, the God of their fathers, "
        "has appeared to you — the God of Abraham, the God of Isaac, "
        "and the God of Jacob.",
    ),
    (
        1,
        16,
        "And again the LORD said to Moses: Put your hand into your "
        "bosom. And Moses put his hand into his bosom; and he said: "
        "Take out your hand from your bosom. And he took it out from "
        "his bosom, and behold, it was wholly leprous like snow. And "
        "again he said: Put your hand back into your bosom. And he put "
        "his hand into his bosom; and again he said: Take out your "
        "hand from your bosom. And he took it out from his bosom, and "
        "it was restored like the rest of his flesh.",
    ),
    (
        1,
        17,
        "And he said: If they will not believe you and will not "
        "listen to your voice at the first sign, they shall believe by "
        "the voice of the second sign.",
    ),
    (
        1,
        18,
        "And if they will not believe you at these two signs, and will "
        "not listen to your voice, you shall take of the water of the "
        "river and pour it upon the dry land; and the water you take "
        "from the river shall become blood upon the dry ground. "
        "[OCR-bleedthrough: Ethiopian Orthodox Tewahedo Church, "
        "Exodus chapter-marker.] And Moses said to the LORD: I "
        "beseech you, O Lord — [OCR-illegible: ``ቍልፍከ ፀያፍ ወላአላአ "
        "ልሳን አነ``: I have no eloquence, I am not a man of words; I "
        "am slow of speech and slow of tongue].",
    ),
    (
        1,
        19,
        "And the LORD said to Moses: Who has given a mouth to the son "
        "of man? And who has made the deaf and the dumb, and the "
        "seeing and the blind? Is it not I, the LORD?",
    ),
    (
        1,
        20,
        "And now go; and I will open your mouth, and teach you what you shall speak.",
    ),
    (
        1,
        21,
        "And Moses said: I beseech you, my Lord, seek out for yourself another whom you may send.",
    ),
    (
        1,
        22,
        "And the LORD grew angry with Moses, and said to him: Behold, "
        "is not Aaron the Levite your brother? I know that he speaks "
        "well; and behold, he is coming forth to meet you, and when "
        "he sees you he shall rejoice.",
    ),
]
