# Human decisions — what the project needs from the user

> **The answer to "what do you need from me?"** This is the durable, **append-only** queue of
> the only things that genuinely require Boggy (a real device he owns, an account/credential
> only he holds, a publish/tag he must trigger, or a judgment call the rules don't already
> settle). The autonomy doctrine (RULES §2.6 step 4, guard #5(a), memory
> `feedback_autonomous_work_ladder`) routes every human-gated need HERE instead of stopping the
> session — work continues on everything else.
>
> **Rules of this file:** append a row when a new human-need surfaces; never silently drop one.
> Mark a row **Resolved** (don't delete it) when the user acts, with the date. Anything NOT in
> this file is something Claude can and should do autonomously. This is NOT a rolling truth
> record — it does **not** rotate.

| Date raised | What's needed | Why it needs the user | What it unblocks | Raising lane | Status |
|---|---|---|---|---|---|
| 2026-06-21 | **Kobo tap round** on the COLOR Kobo (the flagship `ethiopian-tewahedo` `.kepub.epub`, then the rest of the M3 set) | Real on-device popup/tap behavior — only the physical color Kobo is the true oracle (memory `kobo_color_ereader_end_stage_qa`) | M3 Kobo catalog column goes live; v1.0.0 gate | windows | OPEN |
| 2026-06-21 | **Apple Books device re-QA** of the rebuilt tablet artifact (`ethiopian-tewahedo --target-reader tablet`, badges restored post-Opt#3 revert) | The user's prior device verdict was FAIL (§user-fail M2); only his Apple device confirms the fix | M2 Apple sign-off; v1.0.0 gate | windows | OPEN |
| 2026-06-21 | **Send-to-Kindle device check** — load the deliverable onto the user's own Kindle and confirm notes render as visible endnotes | STK upload + on-device read is the M4 acceptance oracle (KDP is only a test oracle, not the target — memory `project_kindle_sendtokindle_goal`) | M4 Kindle device sign-off; v1.0.0 gate | windows | OPEN |
| 2026-06-21 | **Google Play Books phone QA** of one edition | M5 needs a real phone upload + read; `live:false` until then | M5 Play column; v1.0.0 gate | windows | OPEN |
| 2026-06-21 | **Run the `v1.0.0` tag command** when the release plan's Definition of Done is green | Cutting the release tag is the user's call (the gate's final human step) | The v1.0.0 release | windows | OPEN |
| 2026-06-23 | **The verse/page where the `†` dagger badge jumped to the wrong "II" study note** (Kobo device-QA B-3) | Couldn't reproduce from the build — Gen 1:1 `†` resolves correctly; need the exact locus to trace the bad anchor/href | Closes Kobo device-QA B-3 (`dev/audit/kobo-device-qa-2026-06-23.md`) | windows | OPEN |
