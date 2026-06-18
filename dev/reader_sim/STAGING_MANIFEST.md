# Reader-sim artifact staging (updated turn 127, WIN session wrap)

Local paths under `build/reader-sim/` (gitignored). WIN pulls this manifest + copies from Mac disk or uses own caches.

| Reader | Status | Path / source |
|---|---|---|
| **kindle** | 6 m4b epubs staged | `build/reader-sim/kindle/*.epub` ← `~/Desktop/YHWH-kindle-m4b-qa/` |
| **kobo** | **WIN lane** — fresh build 2026-06-18 | `build/reader-sim/kobo/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-18T015027Z.kepub.epub` · `verify_kr2` **GREEN** · `--sim kobo` running |
| **play** | everywhere navy staged | `build/reader-sim/play/YHWH-ethiopian-tewahedo-v0.1.0-everywhere-navy.epub` ← stk-qa |
| **apple** | **GAP** — no `tablet` build on Mac | Needs `build_edition --target-reader tablet` post ci.py GREEN |

**STK live poll:** gate-only PASS (Kindle-for-Mac not installed on Mac box, 2026-06-18).

**Thorium live:** `--live` stub shipped; Thorium not installed on Mac box.

**`--sim` dry-run (2026-06-18):**
- **kindle** PASS (ethiopian m4b · gate + stk_channel gate-only)
- **play** PASS (everywhere navy from stk-qa)
- **kobo** **WIN owns end-to-end** (build · epubcheck · verify_kr2 · audit_popup_formula · `--sim kobo` · staging). Mac must not run kobo gates or epubcheck on HDD.
- **apple** SKIP (no tablet artifact)