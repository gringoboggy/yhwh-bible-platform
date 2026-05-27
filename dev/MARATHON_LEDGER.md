# Marathon ledger — Kings + Samuel dual-witness transcription

**Purpose.** Per-chapter cadence telemetry for the τ.6.x.4.c (Kings) and τ.6.x.4.b/follow-on (Samuel) marathons. One row per `(book, chapter)` at C-9 close. Rolling ETA falls out of `(avg days/chapter × pending)`. Append-only.

**Schema.** Pipe-delimited table; date is the C-9 commit date (UTC); rounds count fresh-reviewer cycles before APPROVED CLEAN; `r1_defects` is the C-3/C-6 R1 hard-defect count (the chapter's apparent difficulty at first contact); `class` is from `chapter_profile()`.

**Append rule** (codified at audit U-belt 2026-05-20). At C-9 close, the controller appends ONE row for the closed chapter. No row update / mutation — corrections go in a new row with `corrects` field. Stale rows are NOT struck through; ledger reflects reality at write time.

---

## Kings — τ.6.x.4.c

| ref   | class      | c9_date    | days | gg_rounds | cam_rounds | r1_defects | commit   | notes |
|-------|------------|------------|-----:|----------:|-----------:|-----------:|----------|-------|
| 1ki1  | NARRATIVE  | 2026-05-18 |   1  |     3     |     3      |     27     | 9bb9976  | safety-stop MATCHES; 2 CAM column-boundary scripture omissions caught at R1 |
| 1ki2  | NARRATIVE  | 2026-05-19 |   1  |     4     |     3      |     30     | 40fd8a8  | engine base SURFACE-TO-USER → segmentation-granularity artifact; user kept base=CAM |
| 1ki3  | NARRATIVE  | 2026-05-19 |   1  |     5     |     1+adj  |     13     | (1ki3 final) | 5 fresh reviewer rounds + glyph adjudicator + 4 fixes (heaviest GG-side so far); CAM converged in 1+adj |
| 1ki4  | LIST       | 2026-05-20 |   2  |     7     |     3      |    110     | 092afd3  | first LIST-class chapter (officer registry + wisdom names); chapter classifier built in response; schema-rot witnesses migrated post-C-7 to canonical schema |
| 1ki5  | NARRATIVE  | 2026-05-26 |  ~1  |     2     |     2      |     15     | (1ki5 C-9) | R1 prior-session; this session = GG R2 (reverted 3 of 4 MAJOR harmonizations to inked glyphs) + CAM C-4..C-9. CAM located on f127v-R + f128r-L, NOT the arithmetic-predicted f128r+f128v (chapters span columns). CAM R1 found 5 (3 hid behind uncertain flags drifting to the printed Bible). semantic 100%, base=CAM, ww 12.6% (distinct-recension); 0 fabrication / lacuna 0 |

**Rolling stats (post-1Ki4 close):**

- chapters_done = 4 / 47 = 8.5%
- avg_days_per_chapter = 5 / 4 ≈ 1.25 (note: this includes 2026-05-17 Stage-0 setup + 2026-05-18 1Ki1; 1Ki2+3 same-day; 1Ki4 = 2 days)
- gg_rounds_avg = 4.75 (vs plan's "expect 2-3"; deviation traced to 1Ki4 LIST class + 1Ki3 CAM-side complexity)
- cam_rounds_avg = 2.5 (closer to plan's expectation)
- rolling_eta = 43 chapters × 1.25 days = **~54 more days at current pace**

**Levers applied so far** (audit-driven, 2026-05-20):
- U1 canonical writer prevents schema rot (no future 1Ki4-style migration debt)
- U4 chapter-class screens pre-screen the LIST/REGNAL failure families (target: cut LIST round count from 7 to 4-5)
- U5 topology files persist scribal-hand references (target: cut every round count by ~1)
- (Pending) U7 CAM pre-pull eliminates per-chapter CUDL fetch time

**Next class predictions** (for ETA modeling):
- 1Ki5–13 → NARRATIVE (expect 2-4 rounds each)
- 1Ki15-16 → REGNAL_FRAME (expect 4-8 rounds each; first REGNAL chapter will be a calibration of expected_rounds)
- 1Ki14, 17-22 → NARRATIVE
- 2Ki1-12 → NARRATIVE
- 2Ki13-17 → REGNAL_FRAME (expect 4-8 each)
- 2Ki18-25 → NARRATIVE

If U4 + U5 deliver the modeled speedup (NARRATIVE 2-3, LIST 4-5, REGNAL_FRAME 4-6 instead of the worst-case bars), revised ETA = 43 × 1.0 days = **~43 days**. If they OVERperform (NARRATIVE 2, LIST/REGNAL 4), ~35 days.

---

## Samuel — τ.6.x.4.a + .a-W + (deferred marathon)

| ref     | class       | c9_date    | days | gg_rounds | cam_rounds | r1_defects | commit   | notes |
|---------|-------------|------------|-----:|----------:|-----------:|-----------:|----------|-------|
| 1sa1    | NARRATIVE   | 2026-05-16 |   1  |     —     |     —      |     —      | (calibration gate) | Hannah's birth; original Phase-1 gate; method-proving |
| 1sa3    | NARRATIVE   | 2026-05-17 |  ≈0.3 |    —     |     —      |     —      | (a-W)    | Samuel's call; widened-calibration |
| 1sa17   | NARRATIVE   | 2026-05-17 |  ≈0.3 |    —     |     —      |     —      | (a-W)    | David & Goliath; stress-test (GG SHORT 20v / CAM LONG 58v) |
| 2sa11   | NARRATIVE   | 2026-05-17 |  ≈0.3 |    —     |     —      |     —      | (a-W)    | Bathsheba; both witnesses FULL/LONG |

*Samuel rounds data not back-filled — the Phase-1 calibration ran with a different (less-instrumented) workflow than Kings. Going forward (when the Samuel marathon resumes), the same per-chapter telemetry applies.*

**Samuel marathon ETA** (51 chapters pending; conservative classifier coverage applied): assuming same per-class rates as projected Kings, 51 × 1.0 days = **~51 days** once started. Samuel marathon is currently DEFERRED — see `dev/IN_FLIGHT.md`.

---

## Notes on interpretation

- `days` is wall-clock between C-1 and C-9, NOT just active-work time. The user-driven single-chapter cadence (`feedback_marathon_pacing`) intentionally extends wall-clock with check-in pauses; that's a feature, not a bug.
- `r1_defects` is the C-3 R1 (for GG; C-6 R1 for CAM) hard-defect count BEFORE any fix-rounds. It correlates with class (LIST/REGNAL > NARRATIVE) and with chapter-genre (registry > narrative). When it spikes unexpectedly on a NARRATIVE-class chapter, suspect mis-classification — surface to the user.
- `commit` is the C-9 final calibration commit hash (the manifest-flip-+-collation commit). Earlier checkpoint commits (mid-fix) are NOT recorded here.
- `corrects` (if added in a row) means this row supersedes an earlier ref's data due to a post-hoc finding (e.g., a future audit reveals 1Ki4's r1_defects was over-counted). Earlier row STAYS; new row adds correction without rewriting history.
