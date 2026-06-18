# Reader-sim artifact staging (turn 125, Mac)

Local paths under `build/reader-sim/` (gitignored). WIN pulls this manifest + copies from Mac disk or uses own caches.

| Reader | Status | Path / source |
|---|---|---|
| **kindle** | 6 m4b epubs staged | `build/reader-sim/kindle/*.epub` ← `~/Desktop/YHWH-kindle-m4b-qa/` |
| **kobo** | 1 kepub staged | `build/reader-sim/kobo/*.kepub.epub` ← `build/round9-kobo-tap/` |
| **play** | everywhere navy staged | `build/reader-sim/play/YHWH-ethiopian-tewahedo-v0.1.0-everywhere-navy.epub` ← stk-qa |
| **apple** | **GAP** — no `tablet` build on Mac | Needs `build_edition --target-reader tablet` post ci.py GREEN |

**STK live poll:** gate-only PASS (Kindle-for-Mac not installed on Mac box, 2026-06-18).

**Thorium live:** `--live` stub shipped; Thorium not installed on Mac box.

**`--sim` dry-run (2026-06-18):**
- **kindle** PASS (ethiopian m4b · gate + stk_channel gate-only)
- **play** PASS (everywhere navy from stk-qa)
- **kobo** epubcheck on 40 MB kepub >20 min on Mac HDD — defer to WIN lane
- **apple** SKIP (no tablet artifact)