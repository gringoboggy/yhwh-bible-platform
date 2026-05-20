"""Translation: geez-tewahedo-en · Book: gen

English back-translation of content/translations/geez-tewahedo/gen.py
(Ge'ez source, ocr-tier3 quality). Produced 2026-05-20 via Claude Opus 4.7
multilingual back-translation with OCR-noise smoothing.

Smoke scope: Genesis 1-5 (~138 verses) — Gen 1 shipped τ.F.gen1.a;
Gen 2-5 extends at τ.F.gen.b (107 new verses across chapters 2/3/4/5).
Future chapters: follow the τ.7.x.<letter>.<lang>-en cadence once authorized.

Source quality: ai-back-translation-tier4
Extraction date: 2026-05-20
Ingest phase: τ.F.gen.b
Tool: Claude Opus 4.7 multilingual back-translation (direct verse-by-verse)

Method notes:
- Back-translation is *faithful to the OCR'd source*, not aligned to KJV/NRSV.
- The Ge'ez OCR has heavy verse-boundary drift through chapters 2-5: the
  source's chapter boundaries are shifted ~10-15 verses behind canonical
  KJV by chapter 3, because the OCR'd EOTC recension folds the canonical
  Gen 2:1-10 prologue into source ch.1 v.27-31, and the canonical chapter
  endings/openings are absorbed into prior verses via OCR-bleedthrough
  chapter-markers (``ምዕራፍ ፪``, ``ምዕራፍ ፫``, ``ምዕራፍ ፬``, ``ምዕራፍ ፭``).
  The back-translation preserves this 1-to-1 with the source — it does
  NOT silently re-segment. Approximate source↔canonical mapping per
  chapter is given in inline comments at chapter boundaries.
- OCR-garbled words smoothed via context where the topology is clear
  (e.g., source ``በሩዳሚ`` v1 ← canonical ``በቀዳሚ`` "in the beginning";
  ``ኔለማን`` ← ``ጽልመትን`` "darkness"; etc).
- Irrecoverable runs flagged inline as ``[OCR-illegible: ...]``.
- EOTC marginalia (chapter-marker bleed-throughs, scribal cross-references)
  preserved as ``[xref: ...]`` or ``[OCR-bleedthrough ...:]`` rather than
  silently dropped or rewritten.
"""

TRANSLATION = "geez-tewahedo-en"
BOOK = "gen"
SOURCE_QUALITY = "ai-back-translation-tier4"
SOURCE_PROVENANCE = "claude-opus-4-7-back-translation-of-geez-tewahedo"
EXTRACTION_DATE = "2026-05-20"
INGEST_PHASE = "τ.F.gen.b"
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
    # Source ch.2 ≈ canonical Gen 2:11-3:13 (verse-boundary drifted by
    # ~10 verses; canonical Gen 2:1-10 was absorbed into source ch.1
    # verses 27-31; OCR-bleedthrough chapter-3 marker appears mid-ch.2).
    (
        2,
        1,
        "The name of the first river is Pishon; it is the one that "
        "encompasses all the land of Havilah; and there is gold there.",
    ),
    (
        2,
        2,
        "And the gold of that land is good; and there is bdellium there and the onyx-stone (carbuncle).",
    ),
    (
        2,
        3,
        "And the name of the second river [OCR-noisy: ``ልክልክ ፈለግ``, "
        "canonical Gihon]; it is the one that encompasses all the land "
        "of Cush. And the third [river is] Tigris; it is the one that "
        "flows over against Assyria. And the fourth river is the "
        "Euphrates.",
    ),
    (
        2,
        4,
        "And the LORD God took the man whom he had made, and placed "
        "him in the garden, that he might till it and keep it.",
    ),
    (
        2,
        5,
        "And the LORD God commanded Adam and said to him: Of every tree that is in the garden, eat.",
    ),
    (
        2,
        6,
        "But of the tree of [knowledge of good and evil — OCR-garbled "
        "for ``ህያር ወያሌፉ ሠናየ`` 'living/knowing good'] you shall not "
        "eat from it, for on the day you eat from it you shall surely "
        "die.",
    ),
    (
        2,
        7,
        "And the LORD God said: It is not good for the man [to be "
        "alone]; let us make him [a helper — OCR-illegible: "
        "``ሎቕ ቢቋ ጃይረድይ``].",
    ),
    (
        2,
        8,
        "[OCR-bleedthrough chapter-marker: Ethiopian Orthodox "
        "Tewahedo Church Book of Genesis, opening of chapter 2.] "
        "And the LORD God formed again from the earth every beast "
        "of the field and every bird of the heaven, and brought them "
        "to Adam to see what he would call them; and whatever Adam "
        "called every living soul, so was its name. And Adam called "
        "all their names — the cattle, and all the birds of the "
        "heaven, and all the beasts of the field; but for Adam there "
        "was not found a helper suitable for him.",
    ),
    (
        2,
        9,
        "And the LORD God brought a sleep upon Adam, and he slept; "
        "and the LORD God took one of his ribs, and filled up flesh "
        "in its place.",
    ),
    (
        2,
        10,
        "And the LORD God built the rib which he had taken from Adam [into a woman], and brought her to Adam.",
    ),
    (
        2,
        11,
        "And Adam said: This is bone of my bones and flesh of my "
        "flesh; this one shall be called my partner, for from her "
        "[husband / from man] she came.",
    ),
    (
        2,
        12,
        "Therefore a man shall leave his father and his mother and "
        "cleave to his wife, and the two of them shall become one "
        "flesh.",
    ),
    (
        2,
        13,
        "And Adam and his wife were both naked, and were not ashamed.",
    ),
    (
        2,
        14,
        "[OCR-bleedthrough chapter-marker: chapter 3.] And the "
        "serpent of the earth was more cunning than all the beasts "
        "of the field which the LORD God had made; and the serpent "
        "of the earth said to the woman: What is this that God said "
        "to you, that you shall not eat from any tree that is in the "
        "garden?",
    ),
    (
        2,
        15,
        "And the woman said to the serpent of the earth: Of the fruit "
        "of every tree which is in the garden [we shall eat].",
    ),
    (
        2,
        16,
        "But of the [tree] alone that is in the midst of the garden, God said to us that we shall not eat from it.",
    ),
    (
        2,
        17,
        "And lest you touch it [or you will die], he said.",
    ),
    (
        2,
        18,
        "And the serpent of the earth said to the woman: You shall not surely die.",
    ),
    (
        2,
        19,
        "For God knows that on the day you eat from it, your eyes "
        "shall be opened, and you shall become as God, knowing good "
        "and evil. And when the woman saw that the tree was good for "
        "food and pleasant to look at, and that their eyes would be "
        "opened, and they would become as gods — they thought; and "
        "they took and sewed fig leaves and made for themselves "
        "loincloths.",
    ),
    (
        2,
        20,
        "And they heard the voice of the LORD God walking in the "
        "garden in the cool of the day; and Adam and his wife hid "
        "themselves from before the LORD God among the trees of the "
        "garden.",
    ),
    (
        2,
        21,
        "And the LORD God called to Adam and said to him: Where art thou, Adam?",
    ),
    (
        2,
        22,
        "And Adam said: I heard your voice while you were walking in "
        "the garden, and I was afraid because I was naked, and I hid "
        "myself.",
    ),
    (
        2,
        23,
        "[OCR-noisy] And the woman, recognizing the good [tree], "
        "took of its fruit and ate; and she gave also to her husband "
        "with her, and he ate.",
    ),
    (
        2,
        24,
        "[OCR-bleedthrough chapter-marker: Ethiopian Orthodox "
        "Tewahedo Book of Genesis, chapter heading.] And the LORD "
        "God said: Who told you that you were naked? Have you eaten "
        "from the tree which I commanded you not to eat from?",
    ),
    (
        2,
        25,
        "And Adam said: The woman whom you gave to be with me, she gave to me [from the tree], and I ate.",
    ),
    # Source ch.3 ≈ canonical Gen 3:13-4:20.
    (
        3,
        1,
        "And the LORD God said to the woman: Why have you done this? "
        "And the woman said: The serpent of the earth deceived me, "
        "and I ate.",
    ),
    (
        3,
        2,
        "And the LORD God said to the serpent of the earth: Because "
        "you have done this thing, cursed are you above all the "
        "cattle and above all the beasts of the field; upon your "
        "breast you shall go, and dust you shall eat all the days of "
        "your life. And I will put enmity between you and the woman, "
        "between your seed and her seed; he shall watch your head, "
        "and you shall guard his heel.",
    ),
    (
        3,
        3,
        "And to the woman God said: I will greatly multiply your "
        "sorrow and your pain; in pain you shall bear children; and "
        "your desire shall be toward your husband, and he shall rule "
        "over you.",
    ),
    (
        3,
        4,
        "And to Adam he said: Because you have listened to the voice "
        "of your wife and have eaten from the tree which I commanded "
        "you not to eat from — cursed shall be the earth in your "
        "labor; in pain you shall eat from it all the days of your "
        "life.",
    ),
    (
        3,
        5,
        "Thorns and thistles shall it bring forth to you, and you "
        "shall eat the herb of the field. By the sweat of your face "
        "you shall eat your bread, until you return to the earth from "
        "which you were taken; for dust you are, and to dust you "
        "shall return.",
    ),
    (
        3,
        6,
        "And Adam called his wife's name Eve, because she is the mother of all the living.",
    ),
    (
        3,
        7,
        "And the LORD God made for Adam and for his wife garments of skin, and clothed them.",
    ),
    (
        3,
        8,
        "And the LORD God said: Behold, Adam has become as one of us, "
        "knowing good and evil; and now, lest he stretch out his "
        "hand and take from the tree of life, and eat, and live "
        "forever. [OCR-noisy passage] And the LORD God sent Adam "
        "out from the garden [of joy], that he might till the earth "
        "from which he was taken; and he drove him out and stationed "
        "him before the garden of joy.",
    ),
    (
        3,
        9,
        "And he placed for the cherubim and the seraphim in their "
        "hands a flaming sword that turns about, to guard the ways "
        "of the tree of life.",
    ),
    (
        3,
        10,
        "[OCR-bleedthrough chapter-marker: chapter 4.] And Adam knew "
        "Eve his wife, and she conceived and bore Cain; and she said: "
        "We have gotten a man with the help of the LORD. And she "
        "again bore his brother Abel; and Abel was a keeper of "
        "[sheep], and Cain was a tiller of the ground. "
        "[OCR-bleedthrough: Ethiopian Orthodox Tewahedo Church.] "
        "And it was after many days that Cain brought from the fruit "
        "of the ground an offering to the LORD.",
    ),
    (
        3,
        11,
        "And Abel also brought an offering from the firstlings of his "
        "flock and from the fat of them; and the LORD looked upon "
        "Abel and upon his offering.",
    ),
    (
        3,
        12,
        "But upon Cain and upon his offering he did not look; and Cain was very grieved, and his countenance fell.",
    ),
    (
        3,
        13,
        "And the LORD God said to Cain: Why are you grieved, and why has your countenance fallen?",
    ),
    (
        3,
        14,
        "If you have brought rightly to me, but not rightly divided, "
        "you have sinned. Be still; the desire of [sin] is toward "
        "you, and you shall rule over it.",
    ),
    (
        3,
        15,
        "And Cain said to Abel his brother: Come, let us go out to "
        "the field; and it came to pass, while they were in the "
        "field, that Cain rose up against Abel his brother and slew "
        "him.",
    ),
    (
        3,
        16,
        "And the LORD God said to Cain: Where is Abel your brother? "
        "And Cain said: I do not know — am I my brother's keeper?",
    ),
    (
        3,
        17,
        "And the LORD God said: What have you done, Cain? The voice "
        "of your brother Abel's blood has reached me from the "
        "earth. And now, cursed shall be the earth which has opened "
        "her mouth to receive your brother's blood from your hand.",
    ),
    (
        3,
        18,
        "When you till her, she shall no longer yield to you her "
        "strength; a vagabond and a wanderer you shall be upon the "
        "earth.",
    ),
    (
        3,
        19,
        "And Cain said to the LORD: My iniquity is too great [to be forgiven].",
    ),
    (
        3,
        20,
        "Behold, you are driving me out today from the face of the "
        "earth, and from before your face I shall be hidden; and I "
        "shall be a vagabond and a wanderer upon the earth, and "
        "everyone who finds me will kill me.",
    ),
    (
        3,
        21,
        "And the LORD God said to him: Not so; whoever kills Cain, "
        "vengeance shall be taken on him sevenfold. And the LORD "
        "set a mark upon Cain, that no one finding him should kill "
        "him. And Cain went out from before the face of the LORD, "
        "and dwelt in the land of Nod, over against Eden.",
    ),
    (
        3,
        22,
        "And Cain knew his wife, and she conceived and bore Enoch; "
        "and he built a city, and called the name of that city after "
        "his son Enoch. And Enoch begot Irad, and Irad begot "
        "Mehujael, and Mehujael begot Methushael, and Methushael "
        "begot Lamech.",
    ),
    (
        3,
        23,
        "And Lamech took for himself two wives: the name of the one "
        "[was] Adah, and the name of the second [was] Zillah.",
    ),
    (
        3,
        24,
        "And [Adah] bore to him Jabal; and he was the father of all such as dwell in tents and in herds of livestock.",
    ),
    # Source ch.4 ≈ canonical Gen 4:21-6:13.
    (
        4,
        1,
        "[OCR-bleedthrough chapter-marker: Ethiopian Orthodoxy "
        "Tewahedo Church, chapter heading.] And his brother's name "
        "was Jubal, and he was the one who saw [played] the harp and "
        "the pipe.",
    ),
    (
        4,
        2,
        "And Zillah also bore to Tubal[-Cain], and he was a forger "
        "[smith] of bronze and iron; and the sister of Tubal-Cain "
        "was Naamah.",
    ),
    (
        4,
        3,
        "[OCR-noisy] [And Lamech said to his wives:] Adah and "
        "Zillah, hear my voice, you wives of Lamech, hearken to my "
        "speech; for I have slain a man for my wounding, and a young "
        "man for my hurt.",
    ),
    (
        4,
        4,
        "For Cain shall be avenged sevenfold, and Lamech "
        "seventy-and-sevenfold. And Adam knew again his wife, and "
        "she conceived and bore him a son and called his name Seth, "
        "saying: God has appointed me another seed in place of Abel, "
        "whom Cain slew. And to Seth also a son was born, and he "
        "called his name Enosh; and he was the one who began to call "
        "on the name of the LORD. "
        "[OCR-bleedthrough chapter-marker: chapter 5. — This is the "
        "book of the generations of mankind.] And on the day God "
        "created Adam, he made him in the likeness of God; male and "
        "female he made them, and blessed them.",
    ),
    (
        4,
        5,
        "And he called their name Adam on the day he created them. "
        "And Adam lived [two hundred and thirty] years, and begot a "
        "son in his own likeness and according to his image, and "
        "called his name Seth.",
    ),
    (
        4,
        6,
        "And the days of Adam after he begot Seth were [seven hundred years; and] he begot sons and daughters.",
    ),
    (
        4,
        7,
        "And all the days of Adam were nine hundred and thirty years, "
        "and he died. And Seth lived two hundred and thirty years, "
        "and begot Enosh; and Seth lived after he begot Enosh seven "
        "hundred and seven years, and begot sons and daughters.",
    ),
    (
        4,
        8,
        "And all the days of Seth were nine hundred and twelve years, and he died.",
    ),
    (
        4,
        9,
        "And Enosh lived [one hundred and ninety] years, and begot "
        "Cainan. And Enosh lived after he begot Cainan seven hundred "
        "and fifteen years, and begot sons and daughters.",
    ),
    (
        4,
        10,
        "And all the days of Enosh were nine hundred and five years, "
        "and he died. And Cainan lived [one hundred and seventy] "
        "years, and begot Mahalalel; and Cainan lived after he begot "
        "Mahalalel seven hundred and forty years, and begot sons and "
        "daughters.",
    ),
    (
        4,
        11,
        "And all the days of Cainan were nine hundred and ten years, and he died.",
    ),
    (
        4,
        12,
        "And Mahalalel lived [one hundred and sixty-five] years, and "
        "begot Jared. And Mahalalel lived after he begot Jared seven "
        "hundred and thirty years, and begot sons and daughters.",
    ),
    (
        4,
        13,
        "And all the days of Mahalalel were eight hundred and ninety-five years, and he died.",
    ),
    (
        4,
        14,
        "And Jared lived [one hundred and sixty-two] years, and begot Enoch.",
    ),
    (
        4,
        15,
        "[OCR-noisy] And Jared lived after he begot Enoch eight hundred years, and begot sons and daughters.",
    ),
    (
        4,
        16,
        "And all the days of Jared were nine hundred and sixty-two years, and he died.",
    ),
    (
        4,
        17,
        "And Enoch lived [one hundred and sixty-five] years, and "
        "begot Methuselah. And Enoch [walked with God] after he "
        "begot Methuselah two hundred years, and begot sons and "
        "daughters.",
    ),
    (
        4,
        18,
        "And all the days of Enoch were three hundred and sixty-five "
        "years; and Enoch walked with God, and was not found, "
        "because God had hidden him.",
    ),
    (
        4,
        19,
        "And Methuselah lived [one hundred and eighty-seven] years, "
        "and begot Lamech. And Methuselah lived after he begot "
        "Lamech [seven hundred and eighty-two] years, and begot sons "
        "and daughters. And all the days of Methuselah were nine "
        "hundred and sixty-nine years, and he died.",
    ),
    (
        4,
        20,
        "And Lamech lived [one hundred and eighty-eight] years, and "
        "begot a son; and he called his name Noah, saying: This one "
        "shall give us rest from our toil and from the sorrow of "
        "our hands and from the ground which the LORD cursed. And "
        "Lamech lived after he begot Noah five hundred and "
        "sixty-five years, and begot sons and daughters. And all the "
        "days of Lamech were [seven hundred and fifty-three] years, "
        "and he died.",
    ),
    (
        4,
        21,
        "And Noah was [five hundred] years old, and Noah begot three sons: Shem, and Ham, and Japheth.",
    ),
    (
        4,
        22,
        "And it came to pass, when the sons of men began to multiply "
        "upon the earth, and fair daughters were born to them. And "
        "when the sons of God saw that the daughters of men were "
        "fair, they took for themselves wives from those whom they "
        "chose. And the LORD said: My Spirit shall not abide in "
        "mankind forever, for they are flesh; and their days shall "
        "be a hundred and twenty years.",
    ),
    (
        4,
        23,
        "And there were giants on the earth in those days; and also "
        "after that, when the sons of God came in to the daughters "
        "of men, and they bore to them — these are the giants from "
        "the beginning of the world, men of renown. And when the "
        "LORD saw that the wickedness of mankind upon the earth was "
        "great, and that all the thoughts of their heart at all "
        "times were only evil, all their days — the LORD repented "
        "that he had made mankind upon the earth.",
    ),
    (
        4,
        24,
        "And the LORD took counsel and said: I will blot out mankind "
        "whom I have created from the face of the earth — from man "
        "to beast and to the beasts [of the field] and the birds of "
        "the heaven, and to the creeping things — for I repent that "
        "I have made them.",
    ),
    (
        4,
        25,
        "[OCR-bleedthrough chapter-marker: Ethiopian Orthodox "
        "Tewahedo Church, Book of Genesis, chapter 6.] But Noah "
        "found grace before the LORD. And these are the generations "
        "of Noah: a righteous man was Noah, and perfect; and from "
        "his birth he pleased the LORD. And Noah begot three sons: "
        "Shem, and Ham, and Japheth. And the earth was corrupt "
        "before the LORD, and was filled with violence.",
    ),
    (
        4,
        26,
        "And the LORD looked upon the earth, and behold, it was "
        "corrupted; and all flesh had corrupted his way upon the "
        "earth. And the LORD God said to Noah: The end of mankind "
        "has come before me, for the earth is filled with violence "
        "because of them; and behold, I will destroy them from the "
        "earth.",
    ),
    # Source ch.5 ≈ canonical Gen 6:14-8:14.
    (
        5,
        1,
        "And make for yourself an ark of four-sided [gopher-wood], "
        "and pitch it within and without with pitch [from outside "
        "and inside].",
    ),
    (
        5,
        2,
        "And thus you shall make it: three hundred cubits its length, "
        "fifty cubits its breadth, and thirty cubits its height. And "
        "make a window for the ark, and to a cubit you shall finish "
        "it above; and set the door of the ark in its side; with "
        "lower, second, and third decks shall you make it.",
    ),
    (
        5,
        3,
        "And behold, I bring a flood of waters upon the earth, to "
        "destroy all flesh in which is the breath of life from under "
        "heaven; and everything that is upon the earth shall die. "
        "But I will establish my covenant with you, and you shall "
        "come into the ark — you, and your wife, and your sons, and "
        "your sons' wives with you.",
    ),
    (
        5,
        4,
        "And of all the cattle, and of the [flying creatures — OCR-garbled ``እፅዋፍ``], and of all that creeps.",
    ),
    (
        5,
        5,
        "And of all the beasts, and of all flesh, you shall bring "
        "two of every kind into the ark with you — male and female. "
        "Of all flying creatures after their kinds, and of all "
        "cattle after their kinds, and of all the beasts of the "
        "earth after their kinds — they shall come to you, two by "
        "two, that they may be kept alive with you. And take with "
        "you of all food that is eaten, and gather it to you; and it "
        "shall be food for you and for them — for all the beasts "
        "and the cattle — as the LORD God commanded.",
    ),
    (
        5,
        6,
        "And the LORD God said to Noah: Enter, you and all your house, into the ark.",
    ),
    (
        5,
        7,
        "For you have I seen righteous before me in this generation. "
        "[OCR-noisy passage] And of clean beasts you shall bring "
        "with you sevens by sevens, [OCR-bleedthrough: Ethiopian "
        "Orthodox Tewahedo Church, Book of Genesis, chapter "
        "heading.] male and female; and of beasts that are not "
        "clean, two by two, male and female. And of clean birds of "
        "the heaven, sevens by sevens, male and female, and of birds "
        "of the heaven that are not clean, two by two, male and "
        "female — to keep their seed alive upon all the earth. For "
        "after seven days I shall bring rain upon the earth, forty "
        "days and forty nights, and I will blot out all that moves "
        "upon the earth.",
    ),
    (
        5,
        8,
        "And Noah did all that the LORD God commanded him. And Noah "
        "was six hundred years old when the flood waters came upon "
        "all the earth. And Noah and his wife and his sons and his "
        "sons' wives with him entered into the ark because of the "
        "flood waters.",
    ),
    (
        5,
        9,
        "And of clean birds and unclean birds, and of clean beasts "
        "and unclean beasts, and of every thing that creeps upon the "
        "earth.",
    ),
    (
        5,
        10,
        "They entered to Noah into the ark, male and female, as the LORD God commanded Noah.",
    ),
    (
        5,
        11,
        "And it came to pass after seven days that the flood waters came upon all the earth.",
    ),
    (
        5,
        12,
        "In the six hundredth year of Noah's life, in the second "
        "month, on the [seventeenth — OCR-garbled] day of the dark "
        "[part of the moon], and on that day all the fountains of "
        "the deep were broken up, and the windows of heaven were "
        "opened. And there was rain upon the earth forty days and "
        "forty nights.",
    ),
    (
        5,
        13,
        "On that day Noah and Shem and Ham and Japheth, the sons of "
        "Noah, and his wife and his sons' wives with him, entered "
        "into the ark.",
    ),
    (
        5,
        14,
        "And the beasts of the field after their kinds, and all the "
        "cattle after their kinds, and all that creeps and all the "
        "birds after their kinds.",
    ),
    (
        5,
        15,
        "They came in to Noah into the ark from every flesh in which "
        "is the breath of life — two of each, male and female, of "
        "every flesh, as the LORD God had commanded; and the LORD "
        "shut the ark from outside.",
    ),
    (
        5,
        16,
        "And the flood was upon the earth forty days and forty "
        "nights; and the water increased, and lifted up the ark, and "
        "it was raised above the earth.",
    ),
    (
        5,
        17,
        "And the waters prevailed exceedingly upon the earth, and "
        "increased; and the ark was borne upon the waters. And the "
        "waters prevailed yet more upon the earth, and all the high "
        "mountains which are under heaven were covered.",
    ),
    (
        5,
        18,
        "Fifteen cubits the water was lifted up above them; and "
        "every flesh died that creeps upon the earth — of the birds "
        "and of the cattle and of every beast of the earth, and "
        "every man.",
    ),
    (
        5,
        19,
        "And everything in whom is a spirit, and everything that is upon the dry land, died.",
    ),
    (
        5,
        20,
        "[OCR-bleedthrough chapter-marker: Book of Genesis, chapter "
        "heading.] And everything that moves upon the face of the "
        "earth was wiped out — from mankind to beast and the birds "
        "of the heaven; and only Noah remained, and those that were "
        "with him in the ark.",
    ),
    (
        5,
        21,
        "And the water was lifted up above the earth a hundred and fifty days.",
    ),
    (
        5,
        22,
        "And God remembered Noah and all the beasts and all the "
        "cattle and all that were with him in the ark; and God "
        "brought a wind upon the earth, and the waters subsided.",
    ),
    (
        5,
        23,
        "And the fountains of the deep were stopped up, and the "
        "[waters] were restrained, and the rain from heaven ceased.",
    ),
    (
        5,
        24,
        "And the waters went on receding and going off from the face "
        "of the earth; and after a hundred and fifty days the waters "
        "decreased.",
    ),
    (
        5,
        25,
        "And the ark rested in the seventh month, on the [seventeenth] "
        "day of the dark [part of the moon], upon the mountain of "
        "Ararat.",
    ),
    (
        5,
        26,
        "And the waters continued to go down and decrease until the "
        "tenth month; and on the [first day] of the tenth month the "
        "tops of the mountains were seen.",
    ),
    (
        5,
        27,
        "And it came to pass, after forty days, that Noah opened the "
        "window of the ark which he had made; and he sent forth the "
        "raven, that it might see [the condition of] the face of "
        "the earth.",
    ),
    (
        5,
        28,
        "And [the raven] went and did not return until the waters "
        "were dried up [from the earth]. And [Noah sent forth] the "
        "dove from the ark to see if the waters had ceased from the "
        "face of the earth; and the dove found no resting place for "
        "the sole of her foot, and returned to him [into the ark "
        "to him].",
    ),
    (
        5,
        29,
        "And he waited yet seven days, and again sent forth the dove "
        "out of the ark, that she might see [the face of the earth].",
    ),
    (
        5,
        30,
        "And the dove returned to him at evening, and behold, in her "
        "mouth was a fresh olive-leaf; and Noah knew that the waters "
        "had subsided from the earth.",
    ),
    (
        5,
        31,
        "And he waited yet another seven days, and sent forth the "
        "dove, and she did not [return again] — the water having "
        "subsided from the earth — [OCR-noisy passage; "
        "OCR-bleedthrough: Ethiopian Orthodox Tewahedo Church.] "
        "And it came to pass, in the six hundred and first year of "
        "Noah's life, in the first month, on the first day of the "
        "month, that the waters were dried up from the earth; and "
        "Noah removed the covering of the ark which he had made, "
        "and looked, and behold, the waters were dried up from the "
        "face of the earth.",
    ),
    (
        5,
        32,
        "And in the second month, on the twenty-seventh day of the dark [part of the moon], the earth was dry.",
    ),
]
