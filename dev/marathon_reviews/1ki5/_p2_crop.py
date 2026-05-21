"""Phase 2 parchment-crop helper for 1Ki5 GG R1 CRITICAL re-verification.

Generates LANCZOS-upscaled crops for each CRITICAL defect locus.
Writes to %TEMP%\\1ki5_r1_p2\\ — outside repo per harness convention.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image

OUT = Path(os.environ.get("TEMP", "/tmp")) / "1ki5_r1_p2"
OUT.mkdir(parents=True, exist_ok=True)

ROOT = Path(__file__).resolve().parents[3]
F030V = ROOT / "GAPS" / "2_Kings" / "GG-00106" / "1-Kings" / "1-Kings_f030v.jpg"
F031R = ROOT / "GAPS" / "2_Kings" / "GG-00106" / "1-Kings" / "1-Kings_f031r.jpg"


def crop(src, box, zoom, name):
    im = Image.open(src)
    c = im.crop(box)
    w, h = c.size
    c = c.resize((int(w * zoom), int(h * zoom)), Image.LANCZOS)
    p = OUT / f"{name}.png"
    c.save(p)
    print(f"{name}: src={src.name} box={box} zoom={zoom}× out={c.size} -> {p}")
    return p


# f030v is 1697 × 1712. Three columns L/M/R. Estimated column boundaries:
# L: x≈100-600,  M: x≈600-1100,  R: x≈1100-1600. Top margin ≈ 100.
# Lines run ~50px tall in a 3-col ms with ~50 lines per col → y ≈ top + 32 * line_no.

# Pass an argument to crop only specific items; default = all.
WHICH = sys.argv[1] if len(sys.argv) > 1 else "all"


def want(name):
    return WHICH == "all" or WHICH in name


# ── C-1: v6 ጠቢበ|ላዕለ line-break split (f030v-R, y≈1040-1080 in raw px) ──
# Per review: "lines around y=1040-1080 in raw px". v6 begins L23 of R column;
# col R top likely ~1100-1110 x. v6 starts at f030v-R-L23. The line containing
# 'ጠቢበ' should be near y=1040-1100 in 1712-tall image (mid-ish R column).
if want("C1"):
    # Generous f030v-R column strip first to see context
    crop(F030V, (1080, 980, 1697, 1180), 4, "C1_v6_R_strip_zoom4x")
    # Tighter focus on the line-break
    crop(F030V, (1100, 1010, 1697, 1100), 6, "C1_v6_linebreak_zoom6x")
    crop(F030V, (1100, 1030, 1697, 1080), 8, "C1_v6_linebreak_zoom8x")

# ── C-2: v7 multiple ✣/እ mis-parses; v8 same pattern ──
# v7 starts L29 of f030v-R; v8 starts L34.
# Lines L29-L41 = y range ~1300-1700 in column R (bottom region).
if want("C2"):
    crop(F030V, (1080, 1280, 1697, 1620), 4, "C2_v7_R_strip_zoom4x")
    # ዘበእከ ✣ ዓቢየ should be near v7 start ~L29
    crop(F030V, (1100, 1280, 1697, 1380), 6, "C2_v7_first_zoom6x")
    crop(F030V, (1100, 1380, 1697, 1480), 6, "C2_v7_mid_zoom6x")
    # ፈቀደከ ✣ (v8) — L34
    crop(F030V, (1100, 1480, 1697, 1620), 6, "C2_v8_zoom6x")

# ── C-3: v7 ዕወወ ✣ ዘድሮና (cedars/cypress block) ──
# Same general v7 region; should appear right after the ዓቢየ token.
if want("C3"):
    crop(F030V, (1100, 1380, 1697, 1500), 8, "C3_v7_cedars_zoom8x")

# ── C-4: v10 both ስኪራም → ለኪራም (f030v-R bottom lines, L43+) ──
# v10 starts L43; column R has ~50 lines so this is near the bottom.
if want("C4"):
    crop(F030V, (1080, 1620, 1697, 1712), 4, "C4_v10_R_bottom_zoom4x")
    crop(F030V, (1100, 1620, 1697, 1712), 8, "C4_v10_zoom8x")

# ── C-5: v12 ወረነወ → ወፈነወ (f031r-L, L8+) ──
# f031r is 1629 × 1690. L column ~x=100-600. v12 starts L8.
if want("C5"):
    crop(F031R, (90, 180, 600, 480), 4, "C5_v12_L_strip_zoom4x")
    crop(F031R, (90, 250, 400, 380), 8, "C5_v12_first_word_zoom8x")

print(f"\nDone. Crops in: {OUT}")
print(f"Files: {sorted(p.name for p in OUT.iterdir())}")
