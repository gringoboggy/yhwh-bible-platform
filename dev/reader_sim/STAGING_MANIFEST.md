# Reader-sim artifact staging (updated turn 127, Mac + WIN)

Local paths under `build/reader-sim/` (gitignored). WIN pulls this manifest + copies from Mac disk or uses own caches.

| Reader | Status | Path / source |
|---|---|---|
| **kindle** | 6 m4b epubs staged | `build/reader-sim/kindle/*.epub` ← `~/Desktop/YHWH-kindle-m4b-qa/` |
| **kobo** | **WIN lane** — fresh build 2026-06-18 | `build/reader-sim/kobo/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-18T015027Z.kepub.epub` · `verify_kr2` **GREEN** · Mac SKIP · WIN `--sim kobo` epubcheck slow (40 MB; gate-only K-R2 confirmed) |
| **play** | everywhere navy staged | `build/reader-sim/play/YHWH-ethiopian-tewahedo-v0.1.0-everywhere-navy.epub` |
| **apple** | 2× tablet staged | `ethiopian-tewahedo` `2026-06-18T021121Z` · `catholic-study` `2026-06-18T031711Z` (23.00 MB, epubcheck 0/0/0/0) |

**STK live poll:** gate-only PASS (`Amazon Kindle.app` present; no `com.amazon.Kindle` library container, 2026-06-18). M4b 6/6 structural re-gate PASS (turn 127).

**Thorium live:** Thorium 3.4.0 installed (`brew install --cask thorium`). `YHWH_THORIUM_LIVE=1` opens EPUB in Thorium; CDP tap asserts remain MCP/manual. Thorium = **agent sim proxy** for Apple (`tablet`) + Play (`everywhere`) — not a substitute for Apple Books device QA.

**`--sim all` (2026-06-18, Mac `YHWH_SKIP_KOBO_SIM=1` + `YHWH_THORIUM_LIVE=1`):**
- **kobo** SKIP — WIN lane
- **play** PASS (thorium+cdp)
- **kindle** PASS (stk gate-only)
- **apple** PASS (catholic-study tablet · thorium+cdp)