"""Translation: wlc · Book: gen

τ.5-A seed shipped 2026-05-12 (Westminster Leningrad Codex Hebrew).
Full ingest is τ.5-A.x — user runs scripts/extract_translation.py wlc
after downloading the WLC source.

Hebrew text includes niqqud (vowel points) and te`amim (cantillation
marks). Unicode range U+0591-U+05C7. Renders right-to-left in the
runtime UI per ν.2.7's popup-languages RTL handling.
"""

TRANSLATION = "wlc"
BOOK = "gen"
VERSES = [
    (1, 1, "בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ׃"),
    (
        1,
        2,
        "וְהָאָרֶץ הָיְתָה תֹהוּ וָבֹהוּ וְחֹשֶׁךְ עַל־פְּנֵי תְהוֹם וְרוּחַ אֱלֹהִים מְרַחֶפֶת עַל־פְּנֵי הַמָּיִם׃",
    ),
    (1, 3, "וַיֹּאמֶר אֱלֹהִים יְהִי אוֹר וַיְהִי־אוֹר׃"),
]
