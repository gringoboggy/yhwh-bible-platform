# Mac work queue — operating model + current Mac scope

> **Operating model ("WIN builds · Mac verifies + scopes") — canonical statement = the
> `dev/LANE_HANDOFF.md` STANDING section (RULES §4).** Mac, on each WIN milestone: pull → run the
> WIN-listed verify commands → post PASS/FAIL in LANE_HANDOFF → keep only its current ≤3-item
> scope below. No dual-implementing a fix WIN is shipping; no full `ci.py` on the HDD while WIN's
> is in flight.

## Current scope (Mac) — max 3

> ✅ #1 (Opt# byte-verify) DONE 2026-06-21 — Opt#3 reverted, #2/#4/#5 kept. New scope below.

1. **Stage the user's DEVICE TESTS on the now-verified tree** (Opt#3 reverted; +72 notes baked in):
   - **Kobo (priority): ✅ DONE + STAGED (2026-06-21).** Flagship `ethiopian-tewahedo` — 5 colour
     `.kepub.epub` built, each epubcheck 0/0/0/0 + ALL K-R2 GREEN (noterefs 36,350 all-resolve), staged
     to `/Volumes/MacHD2/YHWH-v2.4-releases/m3-kobo-v0.1.0/` (`SHA256SUMS-ethiopian-refresh-2026-06-21.txt`).
     Ready for the user's COLOR-Kobo tap round (memory `kobo_color_ereader_end_stage_qa`).
   - **⏭ NEXT SESSION (not started — no new long jobs at wrap):** the other 3 catalog editions' Kobo
     refresh (catholic-study · evangelical-reformed · eastern-orthodox; the staged set is stale Jun-14 +
     includes RETIRED SKUs to purge) · **Apple/tablet** `ethiopian-tewahedo --target-reader tablet`
     rebuild for M2 §user-fail re-QA · optional `.dmg` re-cut.
2. ✅ **DONE (2026-06-21) — per-edition note + kind counts POSTED** in `dev/LANE_HANDOFF.md` "Mac wrap"
   (superset 91,555 note-refs; per-edition shipped = base − filtered). Unblocks WIN's Phase-F cascade.
   Did NOT dual-edit the catalog.
3. ✅ **DONE (2026-06-21) — Mirrored parity into Mac per-box memory + ACK** (`feedback_autonomous_work_ladder`;
   rules identical, no OS diff) — the seam-based no-background-radar model AND the NEW autonomy
   doctrine: autonomy is **user-triggered** (never auto-start work/radars on session startup) + the
   work-ladder. The unified work-phase loop has now LANDED as **RULES §2.6** (the canonical home; see
   also `dev/HUMAN_DECISIONS.md`) — **mirror §2.6 into Mac memory (Phase H).** Diff only real OS reasons.

> No full `ci.py` / full pytest on the 8 GB HDD box — targeted gates only; build one edition at a time, respect RAM.
