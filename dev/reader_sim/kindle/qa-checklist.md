# Kindle — real-channel STK QA checklist

**Policy:** Agents run STK-channel sim (`stk_channel.sh` + `--sim kindle`) — not user phone matrix every round. Previewer = diagnostic bisect only. It names E-codes fast (`dev/kindle_bisect.py`) but **Previewer PASS ≠ Send-to-Kindle PASS** — the elaborate kindle variant passed Previewer yet failed STK; KDP/`kpp.amazon` preview is a different channel again. This harness exercises the **consumer delivery path**.

**Artifacts (post sim-pack unlock):**
- Standard: `py -3 scripts/reader_sim.py --build kindle --edition <ed> --version 0.1.0`
- M4b: add `--m4b`

**Automated structural gate:** `py -3 scripts/reader_sim.py --gate kindle --artifact <path> [--m4b]`
(runs `verify_kindle_safe` + optional `verify_kindle_m4b` + epubcheck — no Previewer gate)

## STK channel sim (the real oracle)

1. Stage artifact to `~/Desktop/YHWH-reader-sim/kindle/` (or `stk_channel.sh` when shipped)
2. Send via **Send-to-Kindle** — Mac app, `@kindle.com` email, or web upload (same path users hit)
3. Confirm arrival on **Kindle for Mac** or phone (not Previewer conversion alone)
4. Run tap matrix below

**Previewer appendix (diagnostic only):** if bisecting a structural failure, run KP3 CLI and scrape E-codes — never treat PASS as STK acceptance.

**Live library (Mac turn 128, 2026-06-18):** Kindle.app bundle id is **`com.amazon.Lassen`** (not legacy `com.amazon.Kindle`). Signed-in library detected — inventory snapshot **2 files** (1× kfx + 1× epub in Documents). `stk_channel.sh` fixed to probe Lassen first. Full arrival poll: send staged EPUB via Send-to-Kindle → `stk_channel.sh "$EPUB" --wait 3600`.

**Phone STK matrix (6 variants):** `docs/superpowers/notes/2026-06-18-m4b-kindle-fork-design.md` §7

| # | Tap | Pass |
|---|---|---|
| 1 | Gen 1:1 `vn-link` | Readable translation |
| 2 | Gen 1:3 multi-study | No inline ◈ clutter; chapter-tail study reachable (M4b) |
| 3 | Study-heavy chapter | No 3:24-style teleport |