"""R1 fix-round applier for 1Ki5 GG witness. Phase 1: apply CRITICAL + MAJOR fixes.

Per τ.6.x.4.c marathon protocol: this script applies the 5 CRITICAL + 4 MAJOR
defects from REVIEW_2026-05-20-1ki5-GG-R1.md verbatim, then calls
scripts.core.manuscript_records.write_witness to atomic-write the updated witness.
write_witness re-validates and re-derives canonical tokens from geez.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.core.manuscript_records import (  # noqa: E402
    write_witness,
    validate_witness,
    _screen_non_ethiopic,
)
from scripts.core.manuscript_self_check import (  # noqa: E402
    screen_witness_for_class_failures,
)

WITNESS_PATH = ROOT / "content" / "manuscript" / "kings" / "calibration" / "1ki5_witnessGG.json"

# ---------------------------------------------------------------------------
# Verses (post-R1 fix-round, Phase 1: all CRITICAL + MAJOR applied per review)
# ---------------------------------------------------------------------------

verses = [
    # ─── v1 ────────────────────────────────────────────────────────────────
    # M-1: ወፈነወሙ → ወፈነሙ (drop phantom ወ; flagged AMBIGUOUS by reviewer; Phase 2 re-verify)
    # M-2: ንጉሠ → ንጉሥ (1st-order → 6th-order; flagged AMBIGUOUS; Phase 2 re-verify)
    {
        "v": 1,
        "column": "f030v-M-L23",
        "line_start": 23,
        "geez": (
            "ወፈነሙ ፡ ኪራም ፡ ንጉሥ ፡ ጢሮስ ፡ ለደቁ ፡ ነበ ፡ ሰሎምን ፡ አበ ፡ ሰምዓ ፡ ከመ ፡ "
            "ቀብዕም ፡ ይነግሥ ፡ ህየንተ ፡ ዳዊት ፡ አቡሁ ፡ እስመ ፡ ያፈቅሮ ፡ ኪራም ፡ ለዳዊት ፡ "
            "በኩሉ ፡ መዋዕሊሁ"
        ),
        "uncertain": [
            {
                "marker": "uncertain",
                "note": "rubric kefl 24 (ክፍል ፡ ፳ ወ፬) immediately precedes verse 1 — first verse after the rubric",
            },
            {
                "marker": "damaged",
                "note": (
                    "R1 M-1 applied per review: ወፈነወሙ→ወፈነሙ (phantom medial ወ removed). "
                    "Reviewer self-flagged AMBIGUOUS-PARCHMENT; Phase 2 re-verify pending."
                ),
            },
            {
                "marker": "damaged",
                "note": (
                    "R1 M-2 applied per review: ንጉሠ→ንጉሥ (1st-order ሠ → 6th-order ሥ, "
                    "standard absolute-state form). Reviewer self-flagged AMBIGUOUS-PARCHMENT; Phase 2 re-verify pending."
                ),
            },
            {
                "marker": "uncertain",
                "note": "v1 'ለደቁ' (f030v-M v1 body) — final ቁ could be 2nd-order ቱ; vowel-order topology micro-confusion; defer to CAM",
            },
            {
                "marker": "uncertain",
                "note": "v1 'አበ ፡ ሰምዓ' non-idiomatic vs standard 'እስመ ፡ ሰምዓ'; resolution-limited; honest variant noted",
            },
        ],
    },
    # ─── v2 ────────────────────────────────────────────────────────────────
    # N-1 (MINOR — left as-is for now per review's "optional this round"; flagged in notes)
    {
        "v": 2,
        "column": "f030v-M-L29",
        "line_start": 29,
        "geez": (
            "ወስአከ ፡ ሰሎምን ፡ ጎባ ፡ ኪራም ፡ እንዘ ፡ ይብል ፡ ተአምር ፡ ዕሊከ ፡ ለዳዊት ፡ አቡየ ፡ "
            "ከመ ፡ ተከእና ፡ ነዲቅ ፡ ቤተ ፡ ለስመ ፡ እግዚአብሐር ፡ እምስኩ ፡ በእንተ ፡ አዕባዕ ፡ "
            "ዘአውዳ ፡ እስከ ፡ አመ ፡ አግብአሙ ፡ እግዚአብሐር ፡ ታሕተ ፡ እደሁ"
        ),
        "uncertain": [
            {
                "marker": "uncertain",
                "note": (
                    "first column-break: word spans f030v-M end → f030v-R start, "
                    "'ዕሊከ | ለዳዊት' (column boundary verified; final ከ of ዕሊከ at column-bottom, "
                    "ለ-prefix starts f030v-R top)"
                ),
            },
            {
                "marker": "uncertain",
                "note": (
                    "v2 'ተከእና' may be 'ተከ + ✣ + ና' (✣→እ mis-parse class per CRITICAL C-2 pattern); "
                    "MINOR per review; not corrected this round pending Phase 2/3 re-verify"
                ),
            },
            {
                "marker": "uncertain",
                "note": "v2 'ዕሊከ' non-idiomatic vs standard 'ለዐልየ'/'ላዕለ'; resolution-limited; honest variant noted",
            },
        ],
    },
    # ─── v3 (no defects flagged) ────────────────────────────────────────────
    {
        "v": 3,
        "column": "f030v-R-L5",
        "line_start": 5,
        "geez": ("ወይእዜሰ ፡ አዕረፈኒ ፡ እግዚአብሐር ፡ ሲተ ፡ እምእስላ ፡ ውድየ ፡ ወአልቦ ፡ ዘይስላጥ ፡ ወአልቦ ፡ ዘያምፅ ፡ ሰእኪት"),
        "uncertain": [],
    },
    # ─── v4 (no defects flagged) ────────────────────────────────────────────
    {
        "v": 4,
        "column": "f030v-R-L8",
        "line_start": 8,
        "geez": (
            "ወናሁ ፡ አነ ፡ እብል ፡ ከመ ፡ እሕነዕ ፡ ቤተ ፡ ለስመ ፡ እግዚአብሐር ፡ እምላእኪየ ፡ "
            "በከመ ፡ ይቤሉ ፡ እግዚአብሐር ፡ ለዳዊት ፡ አቡየ ፡ ወልድከ ፡ ዘእህበክ ፡ ዘይከርሰዕል ፡ "
            "መንበርከ ፡ ህየንቴክ ፡ ውእቱ ፡ የሐንፅ ፡ ቤተ ፡ ለስምየ"
        ),
        "uncertain": [],
    },
    # ─── v5 ────────────────────────────────────────────────────────────────
    # N-5 (MINOR): 'ሊባናስ' vs 'ሊባኖስ' inconsistency — flag, do not fix
    {
        "v": 5,
        "column": "f030v-R-L14",
        "line_start": 14,
        "geez": (
            "ወይእዜኒ ፡ አዝዝ ፡ ይግዝሙ ፡ ሊተ ፡ እዕወዕ ፡ እምሊባናስ ፡ ወናሁ ፡ አግብርትየኒ ፡ "
            "ይኩኑ ፡ ምስለ ፡ አግብርቲከ ፡ ወዐስብ ፡ አግብርቲከ ፡ እሁበክ ፡ በከመ ፡ ትቤእ ፡ "
            "እከመ ፡ ሰሊክ ፡ ተእምር ፡ ከመ ፡ አልብነ ፡ ዘየአምር ፡ ግዝመ ፡ ዕፅ ፡ ከመ ፡ ሰብእ ፡ "
            "ሲደና"
        ),
        "uncertain": [
            {
                "marker": "uncertain",
                "note": "ሲደና (Sidonians) — final ና could be alternate vowel-order",
            },
            {
                "marker": "uncertain",
                "note": (
                    "v5 'እምሊባናስ' may be 'እምሊባኖስ' (a/o vowel topology micro-confusion); "
                    "internal inconsistency with v7 'እምሊባኖስ' and v12 'ሊባናስ' — flagged for Phase 2/3 re-verify"
                ),
            },
        ],
    },
    # ─── v6 ────────────────────────────────────────────────────────────────
    # C-1 (CRITICAL): ጠቢላሰ → ጠቢበ ፡ ላዕለ (line-break split mis-merge)
    # M-3 (MAJOR): ወከበ → ወሶበ (likely "and when"; AMBIGUOUS — apply per review, mark for Phase 2)
    {
        "v": 6,
        "column": "f030v-R-L23",
        "line_start": 23,
        "geez": (
            "ወሶበ ፡ ሰምዓ ፡ ኪራም ፡ ቃለ ፡ ሰሎምን ፡ ተፈሥሐ ፡ ፈድፋደ ፡ ወይቤ ፡ ይትባረክ ፡ "
            "እግዚአብሐር ፡ ዮም ፡ ዘውሁቦ ፡ ለዳዊት ፡ ወልደ ፡ ጠቢበ ፡ ላዕለ ፡ ዝንቱ ፡ ሕዝብ ፡ ብዙኅ"
        ),
        "uncertain": [
            {
                "marker": "uncertain",
                "note": "rubric kefl 26 (ክፍል ፡ ፳ ወ፮) precedes verse — kicks off Hiram's reply section",
            },
            {
                "marker": "damaged",
                "note": (
                    "R1 C-1 applied per review: ጠቢላሰ→ጠቢበ ፡ ላዕለ (line-break-split mis-merge "
                    "where C-2 conflated 'ጠቢበ|ላዕለ' into single 'ጠቢላሰ' and dropped 'ላዕለ'). "
                    "Same class as 1Ki4 'ሳዕ|ለ'→'ሳቦሉ'. Reviewer cited f030v-R lines y=1040-1080."
                ),
            },
            {
                "marker": "damaged",
                "note": (
                    "R1 M-3 applied per review: ወከበ→ወሶበ (standard Ge'ez idiom 'and when he heard'). "
                    "Reviewer self-flagged AMBIGUOUS-PARCHMENT (ሶ/ከ confusion not in topology §2 "
                    "explicitly); Phase 2 re-verify pending."
                ),
            },
        ],
    },
    # ─── v7 ────────────────────────────────────────────────────────────────
    # C-2 (CRITICAL): three ✣→እ mis-parses — ዘበእ ፡ ከእ → ዘበእከ ✣ ;
    #                                       መፍቅደ ፡ ከእ → መፍቅደከ ✣ ;
    #                                       እምሊባኖስከእ → እምሊባኖስከ ✣
    # C-3 (CRITICAL): ዕወወለ ፡ ዘድሮን → ዕወወ ✣ ዘድሮና  (the trailing ለ is a body cross artifact;
    #                                              ዘድሮና has 4th-order ና not 1st-order ን)
    {
        "v": 7,
        "column": "f030v-R-L29",
        "line_start": 29,
        "geez": (
            "ወለእኪሁ ፡ ኪራም ፡ ነበ ፡ ሰሎምን ፡ እንዘ ፡ ይብል ፡ ሰማዕኩ ፡ ኩሎ ፡ ዘበእከ ✣ ዓቢየ ፡ "
            "አነ ፡ እንብር ፡ ኩሎ ፡ መፍቅደከ ✣ ዕወወ ✣ ዘድሮና ፡ ዘፀውቄና ፡ ደቅየ ፡ ያውርዱ ፡ "
            "እምሊባኖስከ ✣ እስከ ፡ ባሕር"
        ),
        "uncertain": [
            {
                "marker": "damaged",
                "note": (
                    "R1 C-2 applied per review: three systematic ✣→እ mis-parses corrected "
                    "(ዘበእ ፡ ከእ → ዘበእከ ✣; መፍቅደ ፡ ከእ → መፍቅደከ ✣; እምሊባኖስከእ → እምሊባኖስከ ✣). "
                    "C-2 had conflated wordspace ፡ with body-cross ✣ and promoted ✣ to fidel እ "
                    "in 2nd-person-suffix-ከ positions. Confirmed pattern per topology §1 update."
                ),
            },
            {
                "marker": "damaged",
                "note": (
                    "R1 C-3 applied per review: ዕወወለ ፡ ዘድሮን → ዕወወ ✣ ዘድሮና (the trailing ለ "
                    "of ዕወወለ was a body-cross artifact; ዘድሮና has 4th-order ና not 1st-order ን). "
                    "Cedars + cypress; cf. v9 ዕወዕ ፡ ቀድሮና. ዕወወ/ዕወዕ may be legitimate scribal variants."
                ),
            },
        ],
    },
    # ─── v8 ────────────────────────────────────────────────────────────────
    # C-2 (CRITICAL): ፈቀደከእ → ፈቀደከ ✣  (✣→እ mis-parse)
    # M-4 (MAJOR): ወትህብሊ → ወትህብ (phantom ሊ; AMBIGUOUS per review)
    # N-3 (MINOR): እለ ፡ ህየ — left as-is, flagged
    # N-6 (MINOR): ለስብእ — left as-is, flagged
    {
        "v": 8,
        "column": "f030v-R-L34",
        "line_start": 34,
        "geez": (
            "ወአነ ፡ እግብር ፡ አሕማሬ ፡ ውስተ ፡ ባሕር ፡ እስከ ፡ መካንከ ፡ ነበ ፡ ትትሜጠወኒ ፡ "
            "ወእነብር ፡ እለ ፡ ህየ ፡ ወእንሣዕለ ፡ እንተ ፡ መዓብር ፡ ፈቀደከ ✣ ወትህብ ፡ ሲሳየ ፡ "
            "ለስብእ ፡ ቤትየ"
        ),
        "uncertain": [
            {
                "marker": "damaged",
                "note": (
                    "R1 C-2 applied per review: ፈቀደከእ → ፈቀደከ ✣ (✣→እ mis-parse; same "
                    "2nd-person-suffix-ከ + body-cross pattern as v7)."
                ),
            },
            {
                "marker": "damaged",
                "note": (
                    "R1 M-4 applied per review: ወትህብሊ → ወትህብ (phantom ሊ removed; expected "
                    "idiom 'ወትህብ ፡ ሲሳየ' = 'and you give food'). Reviewer self-flagged "
                    "AMBIGUOUS-PARCHMENT; Phase 2/3 re-verify pending."
                ),
            },
            {
                "marker": "uncertain",
                "note": (
                    "v8 'እለ ፡ ህየ' may be 'እ ✣ ህየ' (line-break + body cross); MINOR per review; "
                    "not corrected this round pending Phase 2/3 re-verify"
                ),
            },
            {
                "marker": "uncertain",
                "note": "v8 'ለስብእ' may be 'ለሰብእ' (ሰ/ስ Solomon-family per topology §2); MINOR; not corrected",
            },
        ],
    },
    # ─── v9 (no defects flagged) ────────────────────────────────────────────
    {
        "v": 9,
        "column": "f030v-R-L41",
        "line_start": 41,
        "geez": "ወወሁቦ ፡ ኪራም ፡ ለሰሎምን ፡ ዕወዕ ፡ ቀድሮና ፡ ወጸውቄና ፡ ወኩሎ ፡ ዘፈቀደ",
        "uncertain": [],
    },
    # ─── v10 ───────────────────────────────────────────────────────────────
    # C-4 (CRITICAL): both ስኪራም → ለኪራም (ለ/ስ topology §2 family)
    {
        "v": 10,
        "column": "f030v-R-L43",
        "line_start": 43,
        "geez": (
            "ወሰሎምን ፡ ወሁ ፡ ለኪራም ፡ ፳ ሺ ፡ በመስፈርት ፡ ቆርሰ ፡ ሰርናየ ፡ ሲሳየ ፡ ወመዓኛ ፡ "
            "ከመ ፡ ለቤቱ ፡ ፳ ፡ በመስፈርት ፡ ቤት ፡ ቅብዓ ፡ ቅዱሰ ፡ ወ ፪ ፡ ወደነፀ ፡ ወከመዝ ፡ "
            "ወሁቦ ፡ ሰሎምን ፡ ለኪራም ፡ በበ ፡ ዓመት"
        ),
        "uncertain": [
            {
                "marker": "uncertain",
                "note": "rubric kefl 30 (ክፍል ፡ ፴) precedes — first 30-series rubric",
            },
            {
                "marker": "uncertain",
                "note": (
                    "oil-measures '፳ ... ወ፪ ወደነፀ' — 20 of pure oil + 2 of beaten oil? Or "
                    "'፳ ወ፪' compound (22)? digit reading at resolution limit"
                ),
            },
            {
                "marker": "damaged",
                "note": (
                    "R1 C-4 applied per review: both ስኪራም→ለኪራም (ለ/ስ topology §2 family; "
                    "standard 'la-Kiram' = 'to Hiram'). Reviewer cited f030v-R bottom lines, "
                    "wide-topped curved ለ not narrower ስ. Same class as 1Ki4 'ፈስግ'→'ፈለግ', "
                    "'እስ ይስሕቡ'→'እለ ይስሕቡ'."
                ),
            },
        ],
    },
    # ─── v11 ───────────────────────────────────────────────────────────────
    # N-2 (MINOR): ጥበባ → ጥበበ — left as-is, flagged
    {
        "v": 11,
        "column": "f031r-L-L2",
        "line_start": 2,
        "geez": (
            "ወወሁቦ ፡ እግዚአብሐር ፡ ለሰሎምን ፡ ጥበባ ፡ በከመ ፡ ይቤሉ ፡ ወኮነ ፡ ሰላም ፡ "
            "በማእክሊ ፡ ሰሎምን ፡ ወበማእክለ ፡ ኪራም ፡ ወተመሐሉ ፡ ወገብሩ ፡ ኪዳነ ፡ ማእክሎሙ"
        ),
        "uncertain": [
            {
                "marker": "uncertain",
                "note": (
                    "v11 'ጥበባ' may be 'ጥበበ' (ቤ/በ topology §2 micro-confusion; both = wisdom); "
                    "MINOR per review; not corrected this round"
                ),
            },
        ],
    },
    # ─── v12 ───────────────────────────────────────────────────────────────
    # C-5 (CRITICAL): ወረነወ → ወፈነወ (parchment-anchored; two-loop ፈ vs single-curl ረ)
    {
        "v": 12,
        "column": "f031r-L-L8",
        "line_start": 8,
        "geez": (
            "ወፈነወ ፡ ሰሎምን ፡ ንጉሥ ፡ ዐወርት ፡ እምኩሉ ፡ እስራኤል ፡ ወከነ ፡ ዐወርት ፡ ፴ ሺ ፡ "
            "ዐደው ፡ ወይፈኑ ፡ እምኒሆሙ ፡ ፲ ሺ ፡ ውስተ ፡ ሊባናስ ፡ ፩ ፡ ወርሐ ፡ ወያስተባርዮም ፡ "
            "ከመዝ ፡ ፩ ፡ ወርሕን ፡ ይሐልዉ ፡ ውስተ ፡ ሊባናስ ፡ ወ ፪ ፡ ወርሕን ፡ ውስተ ፡ "
            "አብያቲሆሙ ፡ ወአዶኒራም ፡ መልአከ ፡ ጸወርያን"
        ),
        "uncertain": [
            {
                "marker": "uncertain",
                "note": "rubric kefl 30 (ክፍል ፡ ፴) precedes — second 30-series rubric, conscription section",
            },
            {
                "marker": "damaged",
                "note": (
                    "R1 C-5 applied per review: ወረነወ→ወፈነወ (parchment-anchored at 12× LANCZOS; "
                    "second fidel has two-loop/double-curl structure of ፈ, not single vertical + "
                    "bottom-loop of ረ). New ፈ/ረ topology §2 family confirmed by reviewer."
                ),
            },
        ],
    },
    # ─── v13 (no fixes; AMBIGUOUS items left for C-7 collation) ─────────────
    {
        "v": 13,
        "column": "f031r-L-L16",
        "line_start": 16,
        "geez": (
            "ወቦ ፡ ለሰሎምን ፡ ፸ ሺ ፡ ጸወረ ፡ እርሰን ፡ ወ ፹ ሺ ፡ ወቀርት ፡ እለ ፡ ውስተ ፡ ደብር ፡ "
            "ዘእንበለ ፡ ከያማን ፡ መስእክት ፡ ላዕለ ፡ ግብረ ፡ ሰሎምን ፡ ማእየወኪያሲቃን ፡ ገባር ፡ "
            "ወእስተደስው ፡ ዕፀወ ፡ ወእባነ ፡ ፫ ፡ ዓመተ"
        ),
        "uncertain": [
            {
                "marker": "uncertain",
                "note": "rubric kefl 30 (ክፍል ፡ ፴) precedes — third 30-series rubric, bearers/hewers section",
            },
            {
                "marker": "uncertain",
                "note": (
                    "ማእየወኪያሲቃን — looks Greek-derived (cf. ἀρχιτεκτονικός 'master-builders') — "
                    "orthography at resolution limit"
                ),
            },
            {
                "marker": "uncertain",
                "note": "chapter-end marker: next rubric ክፍ ፡ ? begins 1Ki6:1 (ወእምዝ አመ ኮነ ፬፻ ወ?…)",
            },
            {
                "marker": "uncertain",
                "note": (
                    "all three ክፍል ፡ ፴ rubrics (v10/v12/v13) — internally inconsistent unless "
                    "MS allows kefl re-numbering OR ወ? second-digit invisible at JPG resolution. "
                    "AMBIGUOUS-PARCHMENT per review §5; defer to CAM cross-ref + higher-res CUDL."
                ),
            },
        ],
    },
]

transcription_notes = (
    "Hand: GG-00106 careful 3-column book hand. Damage: clean (no significant ink loss). "
    "Boundary: 1Ki4 ends f030v-M just before rubric ክፍል ፡ ፳ ወ፬ (last words of ch.4: "
    "'...እምኩሉ ፡ ነገሥት ፡ ምድር ፡ እለ ፡ ሰምዑ ፡ ጥበቢሁ'). 1Ki5 begins f030v-M at red rubric "
    "ክፍል ፡ ፳ ወ፬ ❈ followed by 'ወፈነሙ ኪራም ንጉሥ ጢሮስ...' 1Ki5 ends f031r-L mid-bottom at "
    "'...ወእባነ ፡ ፫ ዓመተ' just before the next rubric (ክፍ ፡ ?) which introduces "
    "'ወእምዝ አመ ኮነ ፬…' (1Ki6:1). No ምዕራፍ rubric appears on these folios — this MS segments "
    "by ክፍል only. The chapter 5 boundary is reconstructed from the natural narrative-unit "
    "break (Hiram-Solomon correspondence + temple-preparation levy). Intra-chapter rubrics "
    "observed: ክፍል ፡ ፳ ወ፬ (v1), ፳ ወ፭ (v2), ፳ ወ፮ (v6), ፴ (v10), ፴ (v12), ፴ (v13). Topology "
    "says the multi-፴ pattern is unusual; the third '፴' may actually be ፴ ወ፩/፪ at the "
    "resolution limit. Numeral discriminations resolved via stylistic cap-curl: ፴ (30) "
    "clearly distinct from ፫ (3) — verified at lines L9 (30,000 levy), L16 (70k/80k "
    "bearers/hewers); both 70k+80k match KJV/MT recension. Stylistic note: small red marks "
    "appear between every word position in this MS — read as ፡ (wordspace) per topology, "
    "except where the larger ✣ body-cross appears (confirmed instances v6, v7, v8 — see "
    "R1 fixes below). Larger ❈ knot crosses appear after each ክፍል rubric per topology §1. "
    "\n\n"
    "R1 fix-round (2026-05-20) applied per REVIEW_2026-05-20-1ki5-GG-R1.md:\n"
    "- CRITICALs (5): C-1 v6 ጠቢላሰ→ጠቢበ ፡ ላዕለ (line-break-split mis-merge); "
    "C-2 v7+v8 ✣→እ mis-parse class — four instances of 'ከእ' resolved to 'ከ ✣' "
    "(ዘበእከ ✣, መፍቅደከ ✣, እምሊባኖስከ ✣, ፈቀደከ ✣); "
    "C-3 v7 ዕወወለ ፡ ዘድሮን → ዕወወ ✣ ዘድሮና; "
    "C-4 v10 both ስኪራም→ለኪራም (ለ/ስ topology §2 family); "
    "C-5 v12 ወረነወ→ወፈነወ (new ፈ/ረ topology §2 family — to be appended to topology after APPROVE).\n"
    "- MAJORs (4): M-1 v1 ወፈነወሙ→ወፈነሙ (phantom medial ወ; reviewer-AMBIGUOUS, Phase 2 re-verify); "
    "M-2 v1 ንጉሠ→ንጉሥ (1st→6th order; reviewer-AMBIGUOUS, Phase 2 re-verify); "
    "M-3 v6 ወከበ→ወሶበ (and-when idiom; reviewer-AMBIGUOUS, Phase 2 re-verify); "
    "M-4 v8 ወትህብሊ→ወትህብ (phantom ሊ; reviewer-AMBIGUOUS, Phase 2 re-verify).\n"
    "- MINORs (6): N-1/N-2/N-3/N-5/N-6 left as-is per review's 'optional this round' guidance, "
    "surfaced as uncertain entries; N-4 v1+v2 non-idiomatic forms surfaced as honest variants.\n"
)

if __name__ == "__main__":
    record = write_witness(
        witness="GG",
        book="1ki",
        chapter=5,
        source_images=[
            "GAPS/2_Kings/GG-00106/1-Kings/1-Kings_f030v.jpg",
            "GAPS/2_Kings/GG-00106/1-Kings/1-Kings_f031r.jpg",
        ],
        folio_sigla=["f030v", "f031r"],
        verses=verses,
        transcription_notes=transcription_notes,
        output_path=WITNESS_PATH,
    )

    ok, errs = validate_witness(record)
    print(f"validate_witness: ok={ok}, errs={errs}")
    for v in record["verses"]:
        non_eth = _screen_non_ethiopic(v)
        if non_eth:
            print(f"non_ethiopic v{v['v']}: {non_eth}")
    print("non_ethiopic_screen: CLEAN (no flags reported above this line)")

    flags = screen_witness_for_class_failures(record, chapter_class="NARRATIVE")
    print(f"NARRATIVE screen: {flags}")

    total_tokens = sum(len(v["tokens"]) for v in record["verses"])
    print(f"Total tokens: {total_tokens}")
    print(f"Written to: {WITNESS_PATH}")
    print(f"File size: {WITNESS_PATH.stat().st_size} bytes")
