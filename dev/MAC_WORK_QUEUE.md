# Mac work queue — operating model + current Mac scope

> **Lane-coordination-v2: WIN builds · Mac verifies + scopes** (RULES §4 + `dev/LANE_HANDOFF.md`
> STANDING). WIN owns implementation (`scripts/` · `tests/` · `ci.py` · matrix builds · Kindle
> bisect). On each WIN milestone, Mac: pull → run the WIN-listed verify commands → post PASS/FAIL
> in `dev/LANE_HANDOFF.md` → keep ≤3 next-scope items here. Mac must **not** dual-implement a fix
> WIN is shipping; Mac **may** run targeted `pytest` + sim gates + STK poll (user uploads); Mac
> must **not** run a full `ci.py` on the HDD while WIN's `ci.py` is in flight.

## Current scope (Mac) — max 3

> ✅ #1 (Opt# byte-verify) DONE 2026-06-21 — Opt#3 reverted, #2/#4/#5 kept. New scope below.

1. **Stage the user's DEVICE TESTS on the now-verified tree** (Opt#3 reverted → tablet badge path is
   correct again; the +72 restored `comm`/`word` notes are baked into the base). Build → gate → stage
   so the user can side-load to HIS devices (user-directed: "load me up new tests on the kobo and on
   my desktop"; memory `feedback_autonomous_work_ladder`):
   - **Kobo (priority):** the flagship `ethiopian-tewahedo` `.kepub.epub` first (his COLOR Kobo needs
     the kepub for popups — memory `kobo_color_ereader_end_stage_qa`), then the rest of the M3 set as
     bandwidth allows. Gate each: `epubcheck 0/0/0/0` · `verify_kr2_build` · kepubify v4.0.4. Stage to
     the external-drive handoff path (`YHWH-v2.4-releases/m3-kobo-…/`); name the files in LANE_HANDOFF.
   - **Apple/tablet:** rebuild a fresh `ethiopian-tewahedo --target-reader tablet` artifact (badges are
     restored now that Opt#3 is reverted) for the user's Apple Books device re-QA (STANDING M2
     §user-fail). Stage it; name the file.
   - **macOS desktop (optional, only if HDD/RAM allow):** re-cut the `.dmg` for a fresh desktop test.
2. **Report exact per-edition note + kind counts** from the rebuild (the +72 restored notes shifted the
   shipped numbers) → WIN owns the catalog count-cascade reconciliation (page/meta/og/social-card/
   GH-GL descriptions/EPUB metadata/trackers). **Do NOT dual-edit the catalog** — just post the numbers
   in `dev/LANE_HANDOFF.md`.
3. ✅ **DONE (2026-06-21) — Mirrored parity into Mac per-box memory + ACK** (`feedback_autonomous_work_ladder`;
   rules identical, no OS diff) — the seam-based no-background-radar model AND the
   NEW autonomy doctrine: autonomy is **user-triggered** (never auto-start work/radars on session
   startup) + the work-ladder (memory `feedback_autonomous_work_ladder`: advance program/EPUBs + stage
   device tests → defer human calls to `dev/HUMAN_DECISIONS.md` → else any program/epub/website/repo/
   metadata work → else transcribe Ge'ez/Amharic + publish to the site). The work-phase loop is being
   added to RULES; mirror it when it lands. Diff only real OS reasons.

> No full `ci.py` / full pytest on the 8 GB HDD box — targeted gates only; build one edition at a time, respect RAM.
