"""Overview crops to orient on the full folio before targeted Phase 2 cropping."""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

OUT = Path(os.environ.get("TEMP", "/tmp")) / "1ki5_r1_p2"
OUT.mkdir(parents=True, exist_ok=True)
ROOT = Path(__file__).resolve().parents[3]
F030V = ROOT / "GAPS" / "2_Kings" / "GG-00106" / "1-Kings" / "1-Kings_f030v.jpg"
F031R = ROOT / "GAPS" / "2_Kings" / "GG-00106" / "1-Kings" / "1-Kings_f031r.jpg"


# Save downscaled overview to fit in vision context budget
def overview(src, scale, name):
    im = Image.open(src)
    w, h = im.size
    im2 = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    p = OUT / f"{name}.png"
    im2.save(p)
    print(f"{name}: {im2.size} → {p}")


overview(F030V, 0.85, "f030v_overview")
overview(F031R, 0.85, "f031r_overview")
