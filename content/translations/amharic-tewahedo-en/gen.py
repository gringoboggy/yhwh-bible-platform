"""Translation: amharic-tewahedo-en · Book: gen

English back-translation of content/translations/amharic-tewahedo/gen.py
(Amharic source, ocr-tier3 quality). Produced 2026-05-20 via Claude Opus 4.7
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
- The Amharic OCR has heavy verse-boundary drift through chapters 2-5:
  the source's chapter boundaries are shifted ~7-12 verses behind
  canonical KJV by chapter 3, because the OCR'd EOTC recension folds
  the canonical Gen 2:1-7 prologue into source ch.1 v.27-31, and the
  canonical chapter endings/openings are absorbed into prior verses
  via OCR-bleedthrough chapter-markers. The back-translation preserves
  this 1-to-1 with the source — it does NOT silently re-segment.
  Approximate source↔canonical mapping per chapter is given in inline
  comments at chapter boundaries.
- OCR-garbled words smoothed via context where the topology is clear
  (e.g., source ``በመጀመሪያው ቁን`` v1 ← canonical ``በመጀመሪያው ቀን``
  "in the first day / in the beginning"; ``ኔለማን`` ← ``ጨለማን`` "darkness";
  the chapter-and-verse cross-reference "መዝ. ፻"/"መዝ. ፻ሣ፡ ፲፰" preserved
  as ``[xref: Ps ...]`` ).
- Irrecoverable runs flagged inline as ``[OCR-illegible: ...]``.
- EOTC marginalia (cross-references to Psalms, Job, Jeremiah, Matt 24,
  Heb 11, etc.) preserved as ``[xref: ...]`` rather than silently
  dropped or rewritten.
"""

TRANSLATION = "amharic-tewahedo-en"
BOOK = "gen"
SOURCE_QUALITY = "ai-back-translation-tier4"
SOURCE_PROVENANCE = "claude-opus-4-7-back-translation-of-amharic-tewahedo"
EXTRACTION_DATE = "2026-05-20"
INGEST_PHASE = "τ.F.gen.b"
VERSES = [
    (
        1,
        1,
        "In the beginning God [created] the heavens and the earth. But "
        "the earth was in chaos; it was unseen, and was not made firm. "
        "And darkness was upon the deep, and the breath which God had "
        "made was hovering upon the waters.",
    ),
    (1, 2, "And God said: Let there be light; and there was light."),
    (
        1,
        3,
        "And God saw the light, that it was beautiful in form. And God "
        "divided the light and the darkness. [xref: ch. 13.] And God "
        "called the light Day, and the darkness he called Night. And it "
        "was evening, and it was morning — one day. And God [said: in "
        "the midst of] the waters",
    ),
    (
        1,
        4,
        "in the middle, let there be a firmament — to divide between water and water; and it was so.",
    ),
    (
        1,
        5,
        "[xref: Job ... · Jer 1:1 ...] And God created the firmament; "
        "he divided as a boundary between the water under the firmament "
        "and the water above the firmament. [xref: Ps 104:18.]",
    ),
    (
        1,
        6,
        "And God called this firmament Heaven. And God saw that it was "
        "beautiful in form; and it was evening, and it was morning — "
        "the second day.",
    ),
    (1, 7, "God [said: let the waters] under the heavens [be gathered]."),
    (
        1,
        8,
        "[Let them be gathered] into one place, and let the dry land "
        "appear; and it was so. The waters were gathered into their "
        "gathering, and the dry land appeared. [xref: Ps ... ] And God "
        "called the dry land Earth, and the gathering of the outer "
        "waters he called Sea. And God saw that it was beautiful in "
        "form.",
    ),
    (
        1,
        9,
        "And God said: Let the earth bring forth — after their own "
        "course, after their kind, after their likeness — the sown "
        "grass-shoot that yields fruit, that gives seed [from within "
        "itself], the tree whose [seed is in itself], that [will be "
        "planted upon the earth] after its kind, that grows; and it "
        "was so.",
    ),
    (
        1,
        10,
        "And the earth brought forth — after its seed, after its kind, "
        "after its likeness — the sown grass-shoot, yielding fruit, "
        "giving its seed within itself, and the plant which grows upon "
        "the earth after its kind. And God saw that it was good.",
    ),
    (1, 11, "And it was evening; it was morning — the third day."),
    (
        1,
        12,
        "And God said: Let there be lights in the firmament of the "
        "heavens, that they may give light upon the earth, and that "
        "they may divide the day and the night; that they may be for "
        "signs, for days, for years, for an appointed mark.",
    ),
    (
        1,
        13,
        "[OCR-bleedthrough: Christian work 21.]",
    ),
    (
        1,
        14,
        "Religion and order — [let the lights] in the firmament of the "
        "heavens be [made]; that they may give light upon the earth; "
        "and it was so.",
    ),
    (
        1,
        15,
        "God [created] the three [OCR-noisy: most-radiant] lights — the "
        "greater light to give light by day, the lesser light "
        "[OCR-illegible: ክከቁ ጨብ ቴድ ደ ዳኘ ጌዴ ያታ ጴዷ/ን» መኽ ዳደ]. And God "
        "[set them in] the firmament of the heavens, that they may "
        "shine and give light upon the earth.",
    ),
    (
        1,
        16,
        "That they may rule over the day and over the night, that they "
        "may divide the light and the darkness — God saw that it was "
        "good in form.",
    ),
    (1, 17, "And it was evening, the [OCR-garbled: fourth?] day."),
    (
        1,
        18,
        "God [said]: Let [the waters] bring forth swarming creatures, "
        "and let [birds] fly above the earth, under the firmament of "
        "the heavens; and it was so.",
    ),
    (
        1,
        19,
        "God [created] the great sea-creatures and every moving living "
        "creature after its kind, and every winged bird after its kind. "
        "And God saw that it was good in form. And God said: Be "
        "fruitful and multiply, and fill the seas.",
    ),
    (
        1,
        20,
        "And let the birds multiply upon the earth. He blessed them. And it was evening; it was the fifth day.",
    ),
    (
        1,
        21,
        "God [said]: Let the earth bring forth the kinds of livestock, "
        "the creeping things, and the beasts of the earth — each after "
        "its kind.",
    ),
    (
        1,
        22,
        "God [made] the livestock after its kind, and all that creeps "
        "upon the earth after its kind, and the beasts of the earth "
        "after their kinds; and God saw that it was good in form.",
    ),
    (
        1,
        23,
        "And God said: Let us make man in our image, after our "
        "likeness — to rule over the fish of the sea, the beasts of "
        "the earth, the birds of the heaven, the livestock, the whole "
        "earth, and everything that creeps upon the earth. And God "
        "created man in the image of God; male and female he made "
        "them. And God blessed them; and he said to them: Be fruitful "
        "and multiply and fill the earth; and rule over the fish of "
        "the sea, the beasts of the earth, the birds of the heaven, "
        "the livestock — every living thing, and everything that "
        "lives upon the earth, rule over them.",
    ),
    (
        1,
        24,
        "And God said: Behold, I have given you the sown plant, with "
        "every tree growing after its kind, and every fruit-bearing "
        "tree of the field whose seed is in itself, sown after its "
        "fruit — to be food for you. And for every beast of the earth, "
        "and every bird of the heaven, and everything that lives upon "
        "the earth, and everything in which is the breath of life, "
        "every shoot of the herb-grass shall be food; and it was so.",
    ),
    (
        1,
        25,
        "And God saw all the creation that he had made — behold, it was good in form.",
    ),
    (1, 26, "And it was evening; it was the sixth day."),
    (
        1,
        27,
        "[OCR-bleedthrough chapter-marker: Christian religion-and-order, Chapter 2 — heading: chapter 2.]",
    ),
    (
        1,
        28,
        "The heavens and the earth were completed, and all that is in them. [xref: ch. 2:1.]",
    ),
    (
        1,
        29,
        "And God, having finished his work, rested on the seventh day. "
        "[OCR-garbled refrain.] God blessed the seventh day and "
        "sanctified it, because on it he ceased from all the work "
        "which he had begun.",
    ),
    (
        1,
        30,
        "God, when he began to create the heavens and the earth — these "
        "are the generations of the heavens and the earth from when "
        "they were made: [OCR-noisy] no shrub of the field was yet "
        "upon the earth, and every herb of the field had not yet "
        "sprouted, because God had not [caused it to rain] in this "
        "world.",
    ),
    (
        1,
        31,
        "And there was no man to till the earth, only a spring [of "
        "water] alone came up from the earth and watered the dry land. "
        "And God formed man from the dust of the earth, and breathed "
        "into his face the breath of life; and man became a living "
        "soul with the breath of life.",
    ),
    # Source ch.2 ≈ canonical Gen 2:8-3:8 (verse-boundary drifted by
    # ~7 verses; canonical Gen 2:1-7 was absorbed into source ch.1
    # verses 28-31; OCR-bleedthrough chapter-3 marker appears toward
    # the end of source ch.2).
    (
        2,
        1,
        "[xref: Ps ...] And the LORD God prepared from the east a "
        "garden of paradise, and placed the man whom he had made in "
        "the garden. And again the LORD God brought up from the "
        "ground every tree pleasant to look upon and good for food, "
        "and the tree of life in the midst of the garden, and the "
        "tree that gives knowledge of good and evil.",
    ),
    (
        2,
        2,
        "And [a river went out] to water the garden; and from there "
        "it divided into four [heads], and [will fill] the world.",
    ),
    (
        2,
        3,
        "The name of the first river is Pishon; it is the one that "
        "encircles all the land of Havilah, and there is gold there.",
    ),
    (
        2,
        4,
        "[xref: Gen. 1 / Rev. ?] And the gold of that land is good; "
        "there is shining stone there [precious stone — bdellium] "
        "and onyx.",
    ),
    (
        2,
        5,
        "[xref: Chronicles ...] The name of the second river is "
        "Gihon; it is the one that encircles all the land of "
        "Ethiopia [Cush].",
    ),
    (
        2,
        6,
        "The third river is Tigris; it is the one that encircles Persia [Assyria]. And the fourth river is Euphrates.",
    ),
    (
        2,
        7,
        "And the LORD God took the man whom he had made, and placed "
        "him in the garden, that he might till and watch and keep "
        "it.",
    ),
    (
        2,
        8,
        "And the LORD God commanded Adam, saying: Of every tree that is in the garden you may freely eat.",
    ),
    (
        2,
        9,
        "But of the tree that gives knowledge of good and evil, do not eat.",
    ),
    (
        2,
        10,
        "For on the day you eat from it, you shall surely die.",
    ),
    (
        2,
        11,
        "And the LORD God said: It is not good that the man should "
        "be alone; I will make for him a helper as his companion.",
    ),
    (
        2,
        12,
        "And again the LORD God formed from the earth all the beasts "
        "of the field and all the birds of the heaven, and brought "
        "them to Adam, [OCR-bleedthrough: Christian religion-and-"
        "order, chapter heading.] that he might call them by name; "
        "and whatever Adam called them, that was the name of every "
        "living creature.",
    ),
    (
        2,
        13,
        "[xref: Gen. 1:29.] And Adam named all the cattle, and all "
        "the birds of the heaven, and all the beasts of the field; "
        "but for Adam there was not found a helper [a companion]. "
        "And the LORD God brought a deep sleep upon Adam, and he "
        "slept; and the LORD God took one rib from his side, and "
        "filled up flesh in its place.",
    ),
    (
        2,
        14,
        "And the LORD God built this rib which he had taken from Adam's side into a woman, and brought her to Adam.",
    ),
    (
        2,
        15,
        "At that time Adam said: This is bone of my bone and flesh "
        "of my flesh; let her be my wife, for she was found out of "
        "her husband [from her man].",
    ),
    (
        2,
        16,
        "For this reason a man shall leave his father and his "
        "mother and cleave to his wife; and the two shall become "
        "one flesh.",
    ),
    (
        2,
        17,
        "[xref: Matt. 19 ?] And Adam and Eve were both naked, and were not ashamed.",
    ),
    (
        2,
        18,
        "Now the serpent was more cunning than all the beasts of "
        "the field which the LORD God had made; and the serpent of "
        "the field [said] to Eve: Why is it that the LORD God said "
        "to you, You shall not eat from any tree in the garden?",
    ),
    (
        2,
        19,
        "And Eve said to the serpent of the field: We may eat of the fruit of the trees in the garden.",
    ),
    (
        2,
        20,
        "But of the tree which is in the midst of the garden, [God "
        "said:] You shall not eat from it, neither shall you touch "
        "it.",
    ),
    (
        2,
        21,
        "[The serpent said:] The LORD God [lies — has deceived you]; you shall not surely die [he said].",
    ),
    (
        2,
        22,
        "[The serpent said to] Eve: [If you eat] you shall not die.",
    ),
    (
        2,
        23,
        "For God knows that on the day you eat from it, your eyes "
        "shall be opened, and you shall become as God, knowing good "
        "and evil — for this reason [he forbade you].",
    ),
    (
        2,
        24,
        "And when she saw that the tree was good for food, and that "
        "it was pleasant to look upon, and a tree to be desired to "
        "make one wise — when she saw, she cut from the fruit and "
        "ate; and she also gave to her husband, and he ate.",
    ),
    (
        2,
        25,
        "And the eyes of both of them were opened; they knew that "
        "they were naked, and were afraid; and they sewed fig leaves "
        "and made themselves coverings for their nakedness. "
        "[OCR-bleedthrough chapter-marker.] And at evening time, "
        "while [the LORD God] was walking in the garden, hearing the "
        "voice of the LORD God, Adam and Eve hid themselves from "
        "the face of the LORD God among the trees of the garden.",
    ),
    # Source ch.3 ≈ canonical Gen 3:9-4:15.
    (
        3,
        1,
        "And the LORD God called Adam and said to him: [Where are you?]",
    ),
    (
        3,
        2,
        "And Adam [said]: I heard your voice while you were walking "
        "in the garden, and I was afraid because I was naked, so I "
        "hid myself. [OCR-bleedthrough: Christian religion-and-"
        "order.] And the LORD God [said]: Who told you that you "
        "were naked? Have you eaten from the tree that I commanded "
        "you not to eat from?",
    ),
    (
        3,
        3,
        "And Adam said: The woman whom you gave to dwell with me, she gave to me, and I ate.",
    ),
    (
        3,
        4,
        "[xref: Job 38 ?] And the LORD God said to the woman: Why "
        "have you done this? And the woman said: The serpent of the "
        "field deceived me, and I ate.",
    ),
    (
        3,
        5,
        "And the LORD God said to the serpent of the field: Because "
        "you have done this thing, cursed are you above all the "
        "cattle and above all the beasts of the field; upon your "
        "breast you shall go, and dust you shall eat all the days "
        "of your life.",
    ),
    (
        3,
        6,
        "I will put enmity between you and the woman; between your "
        "seed and her seed — he shall watch your head, and you "
        "shall guard his heel.",
    ),
    (
        3,
        7,
        "And the LORD God [said] to the woman: I will greatly "
        "multiply your sorrow; in pain you shall bear children; "
        "your desire shall be toward your husband, and he shall "
        "rule over you, he said. And to Adam the LORD God said "
        "thus: Because you have listened to the voice of [the one "
        "who deceives you] and you have eaten from the tree which "
        "I commanded you not to eat from — cursed shall be the "
        "earth in your labor; in pain you shall eat all the days "
        "of your life.",
    ),
    (
        3,
        8,
        "Thorns and thistles it shall bring forth to you, and you "
        "shall eat the herb of the field. You are dust, and to "
        "dust you shall return; until you return to the earth from "
        "which you were taken, by your toil and sweat you shall eat "
        "bread, he said to him.",
    ),
    (
        3,
        9,
        "[xref: Gen 3:19; Ps. 90 ?]",
    ),
    (
        3,
        10,
        "[xref: ...] And Adam called his wife's name Eve, for she is the mother of all the living.",
    ),
    (
        3,
        11,
        "And the LORD God made for Adam and for Eve garments of "
        "skin, and clothed them. And the LORD God said: Behold, "
        "Adam has become as one of us, knowing good and evil; and "
        "now, lest he stretch out his hand and take from the tree "
        "of life and eat and live forever — [xref: Gen 3:22].",
    ),
    (
        3,
        12,
        "[xref: chapter 3:23.] So [the LORD God] sent Adam out, and "
        "drove him from the garden of joy; and placed him before "
        "the garden of joy.",
    ),
    (
        3,
        13,
        "And [he set] the cherubim with a flaming sword that turns every way to guard the way of the tree of life.",
    ),
    (
        3,
        14,
        "And Adam knew Eve his wife; she conceived and bore Cain. "
        "She said: We have gotten as our possession a son [whom] "
        "the LORD has given us.",
    ),
    (
        3,
        15,
        "And again she bore his brother Abel; and Abel was a keeper "
        "of sheep, and Cain was a tiller of the ground. "
        "[OCR-bleedthrough: Christian religion-and-order.] And it "
        "came to pass after much time that Cain brought of the "
        "fruit of the ground an offering to the LORD God.",
    ),
    (
        3,
        16,
        "And Abel also brought of the firstlings of his flock and "
        "of the fat thereof; and the LORD looked upon Abel and "
        "upon his offering.",
    ),
    (
        3,
        17,
        "But upon Cain and upon his offering he did not look; and "
        "Cain was very grieved, and his countenance fell. And the "
        "LORD God said to Cain: Why are you grieved?",
    ),
    (
        3,
        18,
        "What you have brought to me is not in truth; but if you "
        "had brought rightly to me [it would have been accepted]. "
        "You have sinned — be still; the desire of [sin] is toward "
        "you, and you shall rule over it.",
    ),
    (
        3,
        19,
        "And Cain said to his brother Abel: Come, let us go out to "
        "the field; and it came to pass, while they were in the "
        "field, that Cain rose up against his brother Abel and "
        "slew him.",
    ),
    (
        3,
        20,
        "And the LORD God said to Cain: Where is Abel your brother? "
        "And Cain said: I do not know — am I my brother's keeper?",
    ),
    (
        3,
        21,
        "[xref: 1 John ...] And the LORD God said to him thus: "
        "Cain, what have you done? Your brother Abel's blood cries "
        "to me from the earth. And now, cursed shall be the earth "
        "which has opened her mouth to drink your brother's blood "
        "from your hand, the blood you have shed.",
    ),
    (
        3,
        22,
        "When you till her, she shall no longer yield to you her "
        "strength; you shall be a fugitive and a vagabond upon the "
        "earth. And Cain said to the LORD God: My sin is too great "
        "[to be forgiven]; is it possible that you might pardon "
        "me?",
    ),
    (
        3,
        23,
        "Behold, you drive me out from the earth, and from your "
        "face I shall be hidden; I shall be a vagabond and a "
        "wanderer upon the earth, and whoever finds me will kill "
        "me.",
    ),
    (
        3,
        24,
        "[xref: Jer 41 ?] And the LORD God said: Not so; whoever "
        "kills Cain, on his behalf shall vengeance be taken "
        "sevenfold, he said. And the LORD God set a mark upon "
        "Cain, that whoever saw him should not kill him.",
    ),
    # Source ch.4 ≈ canonical Gen 4:16-5:23.
    (
        4,
        1,
        "And Cain went out from before the face of the LORD; he dwelt in the land of Nod, over against Eden.",
    ),
    (
        4,
        2,
        "And Cain knew his wife; she conceived and bore Enoch. And "
        "he built a city, and called the name of that city after "
        "the name of his son Enoch.",
    ),
    (
        4,
        3,
        "And Enoch begot Irad; and Irad begot Mehujael; and Mehujael begot Methushael; and Methushael begot Lamech.",
    ),
    (
        4,
        4,
        "And Lamech took for himself two wives: the name of the first was Adah; the name of the second was Zillah.",
    ),
    (
        4,
        5,
        "And Adah bore Jabal; he was the father of those who dwell "
        "in tents with herds of livestock [those who pasture cattle].",
    ),
    (
        4,
        6,
        "[OCR-bleedthrough refrain — appears to repeat Gen 4:6: "
        "Cain, from the fruit of the earth you grieve; your face "
        "is sorrowful. — Christian religion-and-order, chapter "
        "heading.]",
    ),
    (
        4,
        7,
        "And his brother's name was Jubal; he taught the playing of the harp and the pipe [flute].",
    ),
    (
        4,
        8,
        "And Zillah bore Tubal[-Cain]; he was a worker of bronze "
        "and brass; and his sister's name was Naamah. And Lamech "
        "said to his wives Adah and Zillah thus: Wives [of Lamech], "
        "hear my voice; hearken to my speech; for I have slain a "
        "man for my wound, and a young man for my hurt.",
    ),
    (
        4,
        9,
        "[xref: Ex. 21:23-25.]",
    ),
    (
        4,
        10,
        "For Cain shall be avenged sevenfold, and Lamech seventy-and-sevenfold.",
    ),
    (
        4,
        11,
        "And Adam again knew his wife; she conceived and bore a "
        "son, and called his name Seth, saying: [In place of] Abel "
        "whom Cain slew, my lord the LORD has appointed me another "
        "son.",
    ),
    (
        4,
        12,
        "And Seth bore a son, and called his name Enosh; he was the one who began to call upon the name of the LORD.",
    ),
    (
        4,
        13,
        "[xref: ...] This is the book of the creation of mankind. "
        "On the day God created Adam, in the image of God he made "
        "him; male and female he made them, and blessed them.",
    ),
    (
        4,
        14,
        "On the day he created them, he called him Adam.",
    ),
    (
        4,
        15,
        "And Adam lived two hundred and thirty years, and begot a "
        "son in his own likeness, and called his name Seth. [xref: "
        "Gen. 5:3.] And after he had begotten Seth, the days of "
        "Adam were seven hundred years, and he begot sons and "
        "daughters. [xref: Gen 5:4.]",
    ),
    (
        4,
        16,
        "[xref: Chr. 5:5.] And all the days of Adam were nine "
        "hundred and thirty years, and he died. [xref: Gen 5:5.] "
        "And Seth lived two hundred and five years, and begot "
        "Enosh.",
    ),
    (
        4,
        17,
        "[xref: Gen 5:7.] And after he begot Enosh, Seth lived "
        "seven hundred and seven years, and begot sons and "
        "daughters. And all the days of Seth were nine hundred and "
        "twelve years, and he died.",
    ),
    (
        4,
        18,
        "And Enosh lived one hundred and ninety years, and begot Cainan.",
    ),
    (
        4,
        19,
        "And after he begot Cainan, Enosh lived seven hundred and "
        "fifteen years, and begot sons and daughters. And all the "
        "days of Enosh were nine hundred and five years, and he "
        "died.",
    ),
    (
        4,
        20,
        "And Cainan lived one hundred and seventy years, and begot "
        "Mahalalel. And after he begot Mahalalel, Cainan lived "
        "seven hundred and forty years, and begot sons and "
        "daughters. And all the days of Cainan were nine hundred "
        "and ten years, and he died.",
    ),
    (
        4,
        21,
        "And Mahalalel lived one hundred and sixty-five years, and begot Jared.",
    ),
    (
        4,
        22,
        "And after Mahalalel begot Jared, he lived seven hundred "
        "and thirty years, and begot sons and daughters. And all "
        "the days of Mahalalel were eight hundred and ninety-five "
        "years, and he died.",
    ),
    (
        4,
        23,
        "And Jared lived one hundred and sixty-two years, and "
        "begot Enoch. [OCR-bleedthrough: Christian religion-and-"
        "order, chapter heading.]",
    ),
    (
        4,
        24,
        "And after Jared begot Enoch, he lived eight hundred years, and begot sons and daughters.",
    ),
    (
        4,
        25,
        "And all the days of Jared were nine hundred and sixty-two "
        "years, and he died. And Enoch lived one hundred and "
        "sixty-five years, and begot Methuselah.",
    ),
    (
        4,
        26,
        "[OCR-noisy passage] After he begot [Methuselah], Enoch lived two hundred years, and begot sons and daughters.",
    ),
    # Source ch.5 ≈ canonical Gen 5:24-7:12.
    (
        5,
        1,
        "[xref: ...] And all the days of Enoch were three hundred "
        "and sixty-five years. And Enoch pleased the LORD; and the "
        "LORD hid him away, and he was not found.",
    ),
    (
        5,
        2,
        "[xref: Heb. 11:5.] And Methuselah lived one hundred and eighty-seven years, and begot Lamech.",
    ),
    (
        5,
        3,
        "And after he begot Lamech, Methuselah lived seven hundred "
        "and eighty-two years, and begot sons and daughters. And "
        "all the days of Methuselah were nine hundred and "
        "sixty-nine years, and he died.",
    ),
    (
        5,
        4,
        "And Lamech lived one hundred and eighty-eight years, and "
        "begot a son. And he called his name Noah, saying: This "
        "one shall comfort us concerning the labor I bring up from "
        "my weariness, and concerning the earth which the LORD "
        "cursed. [xref: Gen 3:17-19.]",
    ),
    (
        5,
        5,
        "And after he begot Noah, Lamech lived five hundred and "
        "sixty-five years, and begot sons and daughters. And all "
        "the days of Lamech were seven hundred and fifty-three "
        "years, and he died. And Noah was five hundred years old; "
        "and Noah begot three sons. Their names are Shem, Ham, and "
        "Japheth.",
    ),
    (
        5,
        6,
        "And it came to pass, when the children of men began to "
        "multiply upon the face of the earth, that fair daughters "
        "were born to them. And the sons of God saw that the "
        "daughters of men were fair to look upon; and they took to "
        "themselves wives from those whom they chose.",
    ),
    (
        5,
        7,
        "[xref: Job 1:6 / 2:1.] And the LORD God said thus: My "
        "Spirit shall not abide in mankind forever, for they are "
        "flesh; and their days shall be a hundred and twenty "
        "years.",
    ),
    (
        5,
        8,
        "In those days there were giants upon the earth; and even "
        "after that time the [sons of God] bore [children] to them. "
        "These are the giants from of old, men of renown. And when "
        "the LORD saw that the sin of the children of men upon the "
        "earth was great, and at every time and from the days of "
        "their youth they went into wickedness, and their thoughts "
        "in all their days inclined toward evil —",
    ),
    (
        5,
        9,
        "The LORD repented that he had made man upon the earth. "
        "And the LORD said within himself: I will blot out from "
        "the face of the earth the man whom I have created — from "
        "man to beast, from beast to creeping things and the birds "
        "of the heaven — for I repent that I have made them. "
        "Again, the sons of God [came in to the daughters of men]. "
        "[OCR-bleedthrough: Christian religion-and-order, chapter "
        "heading.] But Noah found favor in the sight of the LORD.",
    ),
    (
        5,
        10,
        "And these are the generations of Noah: Noah was a "
        "righteous man and perfect; from his birth he pleased the "
        "LORD.",
    ),
    (
        5,
        11,
        "[xref: Gen ...]",
    ),
    (
        5,
        12,
        "[xref: Ps 18 ? · Heb ?]",
    ),
    (
        5,
        13,
        "[xref: 1 Chr / 2 Tim ?] And Noah begot three sons: Shem, Ham, Japheth.",
    ),
    (
        5,
        14,
        "And the earth was corrupted before the LORD, and was "
        "filled with sin [violence]. And the LORD saw that the "
        "earth was corrupted, and that all flesh had corrupted "
        "their way upon the earth. And the LORD God said to Noah "
        "thus: The end [of the days] of mankind has come before "
        "me, because by them the earth is filled with sin; and "
        "behold, I will destroy them from the earth.",
    ),
    (
        5,
        15,
        "[xref: 1 Cor 6:9-10 / 1 Pet ?]",
    ),
    (
        5,
        16,
        "Make for yourself an ark of squared wood [gopher-wood]; "
        "[divide it into] rooms; and cover its inside and outside "
        "with pine-resin pitch.",
    ),
    (
        5,
        17,
        "Make its length three hundred [cubits], its breadth fifty [cubits], and its height thirty cubits.",
    ),
    (
        5,
        18,
        "Make a window for the ark; finish it to a cubit at the "
        "top; and at the side make a door for it [a side-door]. "
        "Make for it stages — lower, second, and third decks — "
        "make it.",
    ),
    (
        5,
        19,
        "Behold, I bring the flood of waters upon the earth, to "
        "destroy from under heaven and from above the earth all "
        "flesh in which is the breath of life; everything that "
        "lives shall die — every flesh that has flesh.",
    ),
    (
        5,
        20,
        "But with you I will establish my covenant; you shall come "
        "into the ark — you, your wife, your sons, and your sons' "
        "wives with you.",
    ),
    (
        5,
        21,
        "And of every flesh, of birds, of cattle, of every creeping "
        "thing — male and female of each you shall take with you "
        "into the ark, so that they may live with you. Of birds "
        "after their kind, of cattle after their kind, of every "
        "creeping thing upon the earth after its kind, two by two "
        "they shall come in to you — male and female — that they "
        "may be fed with you.",
    ),
    (
        5,
        22,
        "And of all food that is eaten, take with you and gather "
        "it to yourself; and it shall be food for you, and for "
        "all the beasts and the cattle.",
    ),
    (
        5,
        23,
        "And Noah did all that the LORD God commanded him. [xref: Heb. 11:7.]",
    ),
    (
        5,
        24,
        "And the LORD God said to Noah: In this generation I have "
        "found you righteous before me; therefore go in, you and "
        "all your kin, into the ark, he said. [xref: Matt. "
        "24:38-39.]",
    ),
    (
        5,
        25,
        "[OCR-noisy] Of clean beasts you shall take with you seven "
        "[pairs], male and female. "
        "[OCR-bleedthrough: Christian religion-and-order, Book of "
        "Genesis, chapter 6.] Of beasts that are not clean, take "
        "two by two, male and female.",
    ),
    (
        5,
        26,
        "[xref: ...] Of clean birds of the heaven, seven [pairs], "
        "male and female; of birds of the heaven that are not "
        "clean, two by two, male and female. [OCR-noisy refrain] "
        "For after seven days I will bring rain upon the earth, "
        "forty days and forty nights; and I will blot out "
        "everything that lives upon the earth. And Noah did "
        "everything that the LORD God commanded him.",
    ),
    (
        5,
        27,
        "[xref: chapter F.] At that time Noah was six hundred years old; and the flood waters came upon all the earth.",
    ),
    (
        5,
        28,
        "And Noah entered into the ark; his wife and his sons and "
        "his sons' wives entered with him because of the flood "
        "waters. [And there came in] clean and unclean birds, clean "
        "and unclean cattle, and everything that lives upon the "
        "earth.",
    ),
    (
        5,
        29,
        "As the LORD God commanded Noah, male and female they entered into the ark to Noah.",
    ),
    (
        5,
        30,
        "And after seven days it came to pass that the flood waters came upon all the earth.",
    ),
    (
        5,
        31,
        "In the six hundredth year of Noah's life, in the second "
        "month, when the moon of the dark [part of the lunar cycle] "
        "had reached its first quarter — on the [seventeenth — "
        "OCR-garbled] day of the month, the flood waters were upon "
        "the earth. On that day all the fountains were broken up, "
        "and the windows of heaven were opened.",
    ),
    (
        5,
        32,
        "[xref: Isa. 12:? ] And upon the earth there was rain [forty days and forty] nights.",
    ),
]
