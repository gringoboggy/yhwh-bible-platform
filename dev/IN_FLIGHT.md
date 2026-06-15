# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->

> **▶ 🔄 2026-06-15 (🪟 Windows, turn 92 — K-R8 INGESTED + K-R7-2e POPUP MODE).** Round-8 QA ingested (`docs/superpowers/notes/2026-06-15-kobo-round8-device-qa.md`). K-R7-2d confirmed; shipped K-R7-2e (hidden anchors default) + K-R7-4b eyebrow spans + font refresh docs. **BLOCKED on user:** popup-mode rebuild QA → mid-badge pop + BOOKI + s7 jump behavior. Pass → Mac re-fan M3 45 + catalog path. Baton **windows**; mode=parallel.
>
> **▶ 🔄 2026-06-14 (🖥️ Mac, turn 90 — M3 FAN-OUT RUNNING).** Pipeline shipped: `build_format_matrix` kepubify post-process + `dev/M3_Kobo_Assets_v0.1.0.txt`. catholic-study smoke 5/5 green. Autonomous `build/m3_fanout.sh` building 45 → `build/matrix-m3/` (7/45 at commit; ethiopian-tewahedo active). Next after 45/45: SHA256SUMS + external drive `m3-kobo-v0.1.0/` handoff for WIN attach. User Kobo taps gate catalog live. Baton **windows**; mode=parallel.
>
> **▶ 2026-06-14 (🪟 Windows, turn 90 — ★ v1.0.0 RELEASE PLAN ACTIVE).** Plan: `docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`. Parallel tracks: A audit round 8 · B M3 Kobo · C M5 Play · D docs · E content (opportunistic). M4 DONE (turn 89). Tag blocked until §8 DoD. WIN: audit + orphan gate. Mac: M3 fan-out. User: device QA rounds. Baton **windows**; mode=parallel.
>
> **▶ ✅ 2026-06-14 (🪟 Windows, turn 89 — ★ M4 CATALOG + WEBSITE LIVE).** Attached 45 Kindle EPUBs to v0.1.0 release; merged SHA256SUMS; `gen_release_catalog` → live columns everywhere/apple/kindle (188 assets); website deployed (`yhwh-website` c8c87d5). **M4 arc COMPLETE.** Baton **windows** (truth_owner); mode=parallel.
>
> **▶ ✅ 2026-06-14 (🖥️ Mac, turn 87 — ★ M4 LIVE ON DEVICE + WIN handoff ready).** 45/45 M4 fan-out built+gated; external drive handoff complete. **User STK 6/6 PASS** (ethiopian-tewahedo superset, jewish-study, catholic-study brown, evangelical-reformed, scholarly-academic, eastern-orthodox). EREADERS + truth triad updated; pushed for WIN attach/deploy. Baton **windows** (truth_owner); mode=parallel.
>
> **▶ ✅ 2026-06-14 (🖥️ Mac, turn 86 PULL) — WinGrok M4_Kindle_Assets + kindle_post + 1ki10 + dead-variant + round-7 mirrored on Mac; all viable (exact 45 gen via .venv+export, hooks .githooks, ruff/lint 0f, 308v 1ki10); AGENTS + asset header updated for future Groks (cross-platform format, no mangling); fresh session prep + truth rotation done; pushed both remotes (radar clear).** See SESSION_STATE top for full Mac verification details. Baton **windows** (truth_owner); mode=parallel.
>
> **▶ ✅ 2026-06-14 (🪟 Windows, turn 86 — round-7 `test_marker_style` + `test_note_rehaul` 6 fixes closed + full verification green; push clears red main; dead-variant consolidation STARTED).** All 6 fixes in (marker_style + note_rehaul sweeps). Re-ran full `test_marker_style.py` + `test_note_rehaul.py` (background) — confirmed the 6 pass AND the `_badge_counts` changes (both copies, in the two test classes) introduced no regressions. Triad (LANE_HANDOFF + IN_FLIGHT + CHANGELOG) updated for freshness. Committed + pushed; this clears the red on GitHub `Tests` / main. **Now taking up ② dead-variant consolidation (per LANE_HANDOFF turn-85/86 agreement):** retire the `--target-reader kindle` FAIL variant (`apply_kindle_safe_css` / `apply_kindle_toc_rows` / `apply_kindle_unhide` / `apply_kindle_strip_hidden` + gate-5 wiring + tied CSS/comments in `build_edition.py`) to the single production `kindle_post` path (`scripts/core/kindle_post.py` + `build_kindle.py` + matrix `post_process: kindle_safe`). Using `mac-kindle-pre-rebase` (0d0f0cb8) as the verified-clean removal reference (byte-identity at the time + 308 tests). is_kindle_target + K-KIN (B/C cap/compaction) emitter logic (still used for base + matrix) kept; only the dead in-pipeline apply fns + call sites + variant-specific gate removed. Production M4 fan-out / kindle_post / 45 artifacts untouched (additive cleanup, no perturb to running overnight build). **NEXT (after this entry):** M4 45-artifact fan-out (Mac autonomous) → user STK re-confirm → WIN attaches catalog + deploys (gen_release_catalog + website). Triad updated; ② marked DONE with test sweeps. Baton **windows** (truth_owner); mode=parallel.
> Mac mirrored M4_Kindle_Assets_v0.1.0.txt (45 assets + Win/Mac Python gens + hygiene for catalog attach; first-class committed artifact). 1ki10 integrated (ch10 evidence). Rotation mirrored.

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via the Esther vision lane.

## Background backlog (never single-thread — RULES §2.5)

> When a lane frees, auto-pick the next: the mint-7 plan phases · CAM hi-res pre-pull · base-structured re-collation · geez→kjv xref anchoring · Phase-E Clementine (1es/2es) · doc-coherence currency · test-coverage growth · Phase-D source acquisition.
