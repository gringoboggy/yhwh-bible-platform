# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->

> **➤➤➤ 2026-05-21 RESUME-AFTER-ACCIDENTAL-CLOSE (user "superpowers on and continue. think i closed you by mistake") — 1ki5 R1 fix-round LANDED ON DISK in the prior session (witness mtime 20:43, ~10s after `_r1_fix_apply.py` helper). Validated this session: schema PASS (13 verses), NARRATIVE-class screen `[]` PASS, 103 manuscript tests green. Committing the R1 work + the prior session's trim/archive in one atomic crash-recovery commit. Then dispatching R2 spec-compliance review alone in BG per the workload-tiered cap (HEAVY = MAX 1 concurrent).**
>
> Landed on disk (now being committed):
> - **τ.6.x.4.c 1ki5 R1 fix-round** — 5 CRITICAL + 4 MAJOR applied per `dev/marathon_reviews/1ki5/REVIEW_2026-05-20-1ki5-GG-R1.md`. Witness `content/manuscript/kings/calibration/1ki5_witnessGG.json` re-written via `write_witness()` (canonical schema; 13 verses; +112 / -31 lines incl. uncertain-marker rationale per fix). Helper script `dev/marathon_reviews/1ki5/_r1_fix_apply.py` retained as the audit-trail of which fix maps to which review item.
> - **Phase-2 re-verification helpers** — `dev/marathon_reviews/1ki5/_p2_crop.py` + `_p2_overview.py` (LANCZOS crop generators for the AMBIGUOUS-PARCHMENT loci flagged by R1; output to `%TEMP%\1ki5_r1_p2\`, never repo-internal).
> - **IN_FLIGHT.md trim** — 386KB → ~11KB; superseded banners archived to `dev/IN_FLIGHT_archive_2026-05-20.md` (6,681 lines of historical context preserved for git-blame).
>
> Next (dispatched after this commit; HEAVY alone in BG):
> - **τ.6.x.4.c 1ki5 R2 spec-compliance review** — fresh adversarial reviewer reads the R1-applied witness, re-checks every CRITICAL + MAJOR vs parchment evidence, produces `dev/marathon_reviews/1ki5/REVIEW_2026-05-20-1ki5-GG-R2.md` with verdict (APPROVED / NEEDS_FIX / BLOCKER). MUST also Phase-2 re-verify the 4 `AMBIGUOUS-PARCHMENT` loci the R1 fix-round self-flagged (M-1 ወፈነወሙ→ወፈነሙ, M-2 ንጉሠ→ንጉሥ, M-3 ወከበ→ወሶበ, M-4 ወትህብሊ→ወትህብ) — without Phase-2 evidence, these MUST be downgraded to BLOCKER. **HEAVY class.** No other agents until this drains and commits.
>
> Held-back queue (sequential per cap; NOT dispatched until R2 lands + user check-in per `feedback_marathon_pacing`):
> 1. **τ.6.x.4.c 1sa2 fresh C-2 re-pass** — full blind re-transcription with corrected methodology (≥6× LANCZOS, post-rubric `❈`, multi-illegible honesty, NEW `ይ`/`ግ`/`ን` + `ሰ`/`ል` + `ደ`/`ድ` families, v29 fabrication watchout); overwrite `content/manuscript/samuel/calibration/1sa2_witnessGG.json`.
> 2. **τ.6.x.4.c 1ki6 C-1+C-2 blind GG** — next Kings chapter advance; NEW `1ki6_witnessGG.json` from f031r 1Ki6:1 boundary.
>
> **[Resumes / supersedes — the 23:30 3RD-CRASH hand-off banner below documents the cap rewrite; that rule remains in force. The PRIOR resume banner (which dispatched the now-LANDED R1 fix-round) is superseded by this LANDED note.]**

> **➤➤➤ 2026-05-20 ~23:30 EST — 3RD CRASH (same day, parallel-agent OOM AT THE NEW 3-CAP) + RULE REWRITTEN + NO RE-DISPATCH THIS SESSION (read FIRST; supersedes the 22:30 2ND-CRASH banner below for state, but its commit 7a20eca remains valid).**
>
> Crash signature: `memory allocation of 30982500 bytes failed` (Rust panic in the harness process). At-time-of-crash state: **3 in-flight BG agents** (the "safe" new cap from the 22:30 banner), each running 19–20 min, downstream token counts **132.2k + 153.0k + 126.1k = ~411k tokens of streamed agent output buffered in parent** — same buffer pressure as crash #2's 7-agent wave, with less than half the agent count. **All 3 agents died with zero disk delta** (no commits landed; witness files on disk unchanged from their pre-dispatch state).
>
> **Root cause (corrected):** The "3-agent cap" rule from the 22:30 banner mistook agent count for the OOM driver. **Real driver is cumulative buffered output × time.** Heavy manuscript-vision agents (CUDL+LANCZOS+verse-by-verse blind transcription, R1 fix-rounds applying 5+ critical defects) routinely emit 100–150k tokens per agent. Three of those = the same parent-buffer pressure as seven small NT-pre-pass / BT-smoke / OT-Ge'ez-gap-fill agents from the 22:51 wave (which landed 16 ships cleanly).
>
> **NEW RULE (memory `feedback_concurrent_agent_cap` rewritten):** workload-tiered, not count-flat:
> - **Heavy** (>100k tokens/agent: manuscript-vision, R1/R2 fix-rounds with all-criticals, deep-evidence multi-chapter sweeps, full-doc constitutional reviews) → **MAX 1 concurrent**, drain before next.
> - **Medium** (30–100k: standard chapter extraction, Patrologia book-ship, multi-chapter NT pre-pass) → MAX 2 concurrent.
> - **Light** (<30k: single-chapter NT epistles, single-chapter Ge'ez gap-fills, BT smoke, hygiene sweeps) → up to 4 concurrent.
> - Mixing heavy+light still counts the heavy's full budget; buffer is one bucket.
> - Drain before re-dispatching; never queue on top of in-flight.
> - Between batches: commit landed work + `/clear` or fresh session to release accumulated parent context.
>
> **Secondary mitigation surfaced by this crash:** IN_FLIGHT.md is currently **386KB**. The crash-recovery loop reads it in full at every fresh session, eating ~50–80k tokens of parent budget BEFORE any agent dispatch. Heavy waves on top of that baseline are unsafe by design. **Action item for the next clean session: trim IN_FLIGHT.md aggressively** — keep the latest banner + the active task section, archive all superseded banners (the 22:30 / 22:00 / 16:45 / 2026-05-19 prior-resume blocks) to `dev/IN_FLIGHT_archive_2026-05-20.md`. Target <50KB.
>
> **This session takes NO action beyond:**
> 1. Writing this banner (you are reading it now)
> 2. Rewriting memory `feedback_concurrent_agent_cap.md` and updating MEMORY.md index
> 3. Committing both (one atomic commit)
> 4. Handing off to user for fresh-session restart
>
> **The 3 agents that died (no disk delta — re-dispatch unchanged in next session, but ONE AT A TIME per the new rule):**
> - τ.6.x.4.c **1ki5 R1 fix-round** — apply 5 CRITICAL + 4 MAJOR per `dev/marathon_reviews/1ki5/REVIEW_2026-05-20-1ki5-GG-R1.md`; overwrite `content/manuscript/kings/calibration/1ki5_witnessGG.json`. **HEAVY class.** Run first, alone.
> - τ.6.x.4.c **1sa2 fresh C-2 re-pass** — full blind re-transcription with ≥6× LANCZOS + corrected methodology + v29 fabrication watchout; overwrite `content/manuscript/samuel/calibration/1sa2_witnessGG.json`. **HEAVY class.** Run second, alone, after 1ki5 lands.
> - τ.6.x.4.c **1ki6 C-1+C-2 blind GG** — next Kings chapter advance; new `1ki6_witnessGG.json` from f031r 1Ki6:1 boundary. **HEAVY class.** Run third, alone, after 1sa2 lands.
>
> **Resume pointer (next session):** read this banner → read updated `feedback_concurrent_agent_cap` → start a fresh `/clear`-ed session → dispatch 1ki5 ALONE in background, await completion notification, commit witness, then 1sa2 ALONE, then 1ki6 ALONE. Total wall-clock per chapter ~20 min × 3 sequential = ~60 min, but zero crash risk vs ~0 min of "parallel" that loses 100% of the work.

> **[ARCHIVE NOTE 2026-05-20 23:30 EST]:** Prior crash banners (22:30 2ND-CRASH, 22:00 RECOVERY, 16:45 EOD-hygiene) and ALL historical/closed arcs were moved to `dev/IN_FLIGHT_archive_2026-05-20.md` during this trim (386KB → ~15KB). Read this file first; consult the archive only when chasing historical context.

## ➤➤➤ ACTIVE — τ.6.x.4.c KINGS dual-manuscript collation + render MARATHON (started 2026-05-17)

> **⏭⏭⏭ CURRENT RESUME POINT (2026-05-20) — authoritative; supersedes the 2026-05-19 block below.**
> - **1 Kings 4 ✅ marathon-complete** (GG R7 APPROVED CLEAN + CAM R3 APPROVED CLEAN; 11 review files on disk; manifest flipped `1ki:4 → calibrated`). 1Ki4 was the first LIST-class chapter and converged in 7 GG rounds + 3 CAM rounds vs the expected 2–3 — the new chapter classifier (audit U4) is the response.
> - **AUDIT-DRIVEN UPGRADES SHIPPED (Kings marathon matrix U1+U2+U4, 2026-05-20):**
>   - **U1 — canonical witness writer.** `scripts.core.manuscript_records.write_witness(...)` derives canonical `tokens` from `geez`, auto-assigns `token_index` for illegible markers, validates the record, and raises before writing if invalid. The C-2/C-5 subagent prompt template in `docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md` now FORBIDS raw `json.dump` and MANDATES this helper, closing the schema-drift path that produced 1Ki4's non-canonical witnesses. +4 tests `TestWriteWitness` (round-trip; canonical-keys-only; rejects bad marker; transactional — no file on validation failure).
>   - **U2 — 1Ki4 schema-debt cleanup.** Migrated `1ki4_witnessGG.json` + `1ki4_witnessCAM_hires.json` to canonical schema (geez byte-identical pre/post; tokens regenerated via `_geez_to_tokens`; uncertain markers normalized to `{uncertain, damaged, illegible}`; extra top-level keys `manuscript`/`phase`/`ref` stripped). Deleted the one-shot `scripts/run_1ki4_collation.py` workaround. Ran `scripts/run_manuscript_collation_at_scale.py --track kings --write` to rebuild `content/apparatus/1ki.json` cumulatively — now **159 apparatus entries across 1ki:1-4** (was 34 from 1Ki4 alone). `content/manuscript/kings/collation/1ki{1,2,3}_collation.json` byte-identical (CRLF noise only); `1ki4_collation.json` regenerated from the migrated witnesses (same logical content as the one-shot's output).
>   - **U4 — chapter complexity classifier.** New `scripts.core.manuscript_chapter_class.chapter_profile(book, chapter) → {class, screens, expected_rounds_min, expected_rounds_max}` returning `NARRATIVE` / `LIST` / `REGNAL_FRAME`. Known LIST: `1ki:4`. Known REGNAL_FRAME: `1ki:15-16, 2ki:13-17`. Default = NARRATIVE (conservative). Class-specific screens encode the LIST failure families (`ለ`/`ስ`, `ይ`/`ደ`, `ያ`/`ደ`, cross-glyph normalization, numeral-vs-letter) and the REGNAL extras (regnal-year numerals, patronymic chains, mother+city formula). Plan template now adds **METHOD NOTE 3**: C-1 must call `chapter_profile()`; C-2/C-5 prompts embed the returned `screens` verbatim above the existing CARDINAL RULE; `expected_rounds_max` sets the escalation bar. +8 tests `TestClassify` + `TestChapterProfile`.
> - **Manifest state:** `47 total / 4 calibrated / 43 pending` (1ki:1-4 calibrated; next pending = `1ki:5`).
> - **⏭ NEXT BATCH** = `1 Kings 5` (Solomon's preparations for the temple; Hiram of Tyre) — **NARRATIVE-class** per `chapter_profile("1ki", 5)`; expected 2–4 rounds. GG source = `GAPS/2_Kings/GG-00106/1-Kings/` continuing from `f030v` (1Ki4 end); CAM begins at the next position after 1Ki4 ends on `f127v` (likely continues into `f128r` — fresh CUDL pull expected). Full C-1…C-9 per the per-chapter procedure; NO C-10. **Awaiting user go-ahead per the single-chapter cadence** (memory `feedback_marathon_pacing`); a CONTRADICTS trigger still stops immediately.

**User-directed** ("the next step is the full rendering and transcribing of kings"). Executing
`docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md` via
`superpowers:subagent-driven-development`. Kings reuses Phase-2/3 VERBATIM (design spec §3/§6);
diplomatic-parallel + base=CAM are the already-ratified 2026-05-17 GO for this manuscript family
(GG-00106 + Cambridge Add.1570) — **no fresh user-GO gate**; 1 Kings 1 is the bi-directional
safety-stop (contradiction → STOP & surface to user).

**Scope:** Stage 0 (additive track-parameterize manifest loader + at-scale driver, samuel=default
byte-identical; seed `content/manuscript/kings/manifest.yaml` 1ki 1-22 + 2ki 1-25) → Stage 1 (the
47-chapter blind dual-witness marathon, isolated GG+CAM transcription per the Samuel VERBATIM
template, collate via the shipped Phase-2 tool) → Stage 2 (Phase-3 render `geez-tewahedo/1ki.py`
+ `2ki.py` + apparatus + `manuscript-collation-tier2`).

**Cross-session ledger:** `content/manuscript/kings/manifest.yaml` (chapters flip `pending`→
`calibrated` as each is done) + `run_manuscript_collation_at_scale.py --track kings` dry report
+ the 12-item task list. Local commit only (remote deleted) — no push, no zip.
