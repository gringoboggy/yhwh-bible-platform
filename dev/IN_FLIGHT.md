# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

> **▶ ✅ 2026-06-14 (🖥️ Mac, turn 86 PULL) — WinGrok M4_Kindle_Assets + kindle_post + 1ki10 + dead-variant + round-7 mirrored on Mac; all viable (exact 45 gen via .venv+export, hooks .githooks, ruff/lint 0f, 308v 1ki10); AGENTS + asset header updated for future Groks (cross-platform format, no mangling); fresh session prep + truth rotation done; pushed both remotes (radar clear).** See SESSION_STATE top for full Mac verification details. Baton **windows** (truth_owner); mode=parallel.
>
> **▶ ✅ 2026-06-14 (🪟 Windows, turn 86 — round-7 `test_marker_style` + `test_note_rehaul` 6 fixes closed + full verification green; push clears red main; dead-variant consolidation STARTED).** All 6 fixes in (marker_style + note_rehaul sweeps). Re-ran full `test_marker_style.py` + `test_note_rehaul.py` (background) — confirmed the 6 pass AND the `_badge_counts` changes (both copies, in the two test classes) introduced no regressions. Triad (LANE_HANDOFF + IN_FLIGHT + CHANGELOG) updated for freshness. Committed + pushed; this clears the red on GitHub `Tests` / main. **Now taking up ② dead-variant consolidation (per LANE_HANDOFF turn-85/86 agreement):** retire the `--target-reader kindle` FAIL variant (`apply_kindle_safe_css` / `apply_kindle_toc_rows` / `apply_kindle_unhide` / `apply_kindle_strip_hidden` + gate-5 wiring + tied CSS/comments in `build_edition.py`) to the single production `kindle_post` path (`scripts/core/kindle_post.py` + `build_kindle.py` + matrix `post_process: kindle_safe`). Using `mac-kindle-pre-rebase` (0d0f0cb8) as the verified-clean removal reference (byte-identity at the time + 308 tests). is_kindle_target + K-KIN (B/C cap/compaction) emitter logic (still used for base + matrix) kept; only the dead in-pipeline apply fns + call sites + variant-specific gate removed. Production M4 fan-out / kindle_post / 45 artifacts untouched (additive cleanup, no perturb to running overnight build). **NEXT (after this entry):** M4 45-artifact fan-out (Mac autonomous) → user STK re-confirm → WIN attaches catalog + deploys (gen_release_catalog + website). Triad updated; ② marked DONE with test sweeps. Baton **windows** (truth_owner); mode=parallel.
> Mac mirrored M4_Kindle_Assets_v0.1.0.txt (45 assets + Win/Mac Python gens + hygiene for catalog attach; first-class committed artifact). 1ki10 integrated (ch10 evidence). Rotation mirrored.

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via the Esther vision lane.

## Background backlog (never single-thread — RULES §2.5)

> When a lane frees, auto-pick the next: the mint-7 plan phases · CAM hi-res pre-pull · base-structured re-collation · geez→kjv xref anchoring · Phase-E Clementine (1es/2es) · doc-coherence currency · test-coverage growth · Phase-D source acquisition.
