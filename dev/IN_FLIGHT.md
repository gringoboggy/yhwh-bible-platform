# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->

> **▶ 🔄 2026-06-14 (🪟 Windows, turn 83 — CI health swept + Mac v1.0.0 laundry delivered; K-KIN STK verdict = FAIL recorded).** Bootstrapped; fixed BOTH CIs. (1) **GitLab** per-push pipelines were all `ci_quota_exceeded` (monthly CI minutes blown ~Jun 6 — NOT code; jobs never start) → `.gitlab-ci.yml` `workflow:rules` stops per-push pipeline creation (ends the failure-email spam; GitHub Actions stays the real per-push CI; manual/scheduled survive). (2) **GitHub** fast-gate green (Mac's KDP reword `7bec299b` pulled) + 2 stale `test_scripts.py` pins fixed (`bcp47` multi-lang/non-kindle + `enable_ai_notes` frozenset import) — verified pass; `popup_split` 52/52. (3) **Mac v1.0.0 laundry** = `notes/2026-06-14-mac-v1.0.0-laundry.md` (5-dim code-verified). **K-KIN:** user confirmed the shipped `FIXED.epub` FAILED on Send-to-Kindle (turn-82 candidate-#1 = ❌) → **M4 stays BLOCKED**; restart the Kindle arc against the STK oracle (Mac: reproduce test-2 recipe → STK web-uploader on a confirmed-up day → bisect on STK if still failing). Baton **windows** (truth_owner); mode=parallel.
>
> **▶ 🔄 2026-06-14 (🖥️ Mac, turn 82 — ★K-KIN Send-to-Kindle verification OPEN; the "RESOLVED" claim was CORRECTED to honest status).** Full from-the-beginning Kindle reconstruction done (workflow `wf_f714f284-c10`). The real goal channel is **Send-to-Kindle** (NOT KDP/Previewer — both falsified/wrong). The turn-81 "E999 RESOLVED" confirmed only KDP + the Previewer; **Send-to-Kindle delivery of the shipped `FIXED.epub` is UNCONFIRMED** (it was never STK-tested; the only STK success ever, test-2, is unrecoverable). The `apply_kindle_strip_hidden` fix is real + likely-necessary but not proven sufficient on STK. **PENDING USER (candidate #1):** upload `~/Desktop/Ethiopian Bible - Catholic Study (Kindle) FIXED.epub` via the Send-to-Kindle **WEB UPLOADER** (amazon.ca/sendtokindle). ON VERDICT — **update this record**: ✅ PASS → K-KIN truly resolved + WIN may light FORMAT_MATRIX M4; ❌ FAIL → retry on a confirmed-up STK day, then reproduce test-2's recipe from source. (The KDP "converting" run is a validity check only, not the goal verdict.) Detail: `docs/superpowers/notes/2026-06-10-kindle-e999-investigation.md` CORRECTION section + SESSION_STATE turn-82. Baton **windows** (truth_owner); mode=parallel.
>

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via the Esther vision lane.

## Background backlog (never single-thread — RULES §2.5)

> When a lane frees, auto-pick the next: the mint-7 plan phases · CAM hi-res pre-pull · base-structured re-collation · geez→kjv xref anchoring · Phase-E Clementine (1es/2es) · doc-coherence currency · test-coverage growth · Phase-D source acquisition.
