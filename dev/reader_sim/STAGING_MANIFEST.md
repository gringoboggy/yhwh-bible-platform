# Reader-sim artifact staging (updated turn 127, WIN session wrap)

Local paths under `build/reader-sim/` (gitignored). WIN pulls this manifest + copies from Mac disk or uses own caches.

| Reader | Status | Path / source |
|---|---|---|
| **kindle** | 6 m4b epubs staged | `build/reader-sim/kindle/*.epub` ← `~/Desktop/YHWH-kindle-m4b-qa/` |
| **kobo** | **WIN lane** — fresh build 2026-06-18 | `build/reader-sim/kobo/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-18T015027Z.kepub.epub` · `verify_kr2` **GREEN** · `--sim kobo` running |
| **play** | everywhere navy staged | `build/reader-sim/play/YHWH-ethiopian-tewahedo-v0.1.0-everywhere-navy.epub` ← stk-qa |
| **apple** | tablet staged | `build/reader-sim/apple/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_tablet_2026-06-18T021121Z.epub` · epubcheck 0/0/0/0 |

**STK live poll:** gate-only PASS (`Amazon Kindle.app` present; no `com.amazon.Kindle` library container, 2026-06-18).

**Thorium live:** `--live` stub shipped; Thorium not installed on Mac box.

**`--sim all` (2026-06-18, Mac `YHWH_SKIP_KOBO_SIM=1`):**
- **kobo** SKIP — WIN lane
- **play** PASS
- **kindle** PASS (stk gate-only — no `com.amazon.Kindle` container; SendToKindleExtension only)
- **apple** PASS (tablet · chapter nav ToC per RX P4a)