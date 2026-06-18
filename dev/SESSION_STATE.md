# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac, turn 128).** `git pull` → **`c74c8c15`+**. **`MAC_WORK_QUEUE.md` §Turn 128**. **Bootstrap auto-starts BOTH radars** (`start_session_radars_mac.sh`). **STANDING:** never ask · never idle · `--replan` when radar pings · `--next` when blocked. **Shipped:** STK Lassen · `--sim all` 3/3 · reader-sim-gates hook. **Pending:** STK arrival poll · Play emulator · Esther transcription · WIN `ci.py` GREEN. **SKIP kobo.** Baton **mac**; mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🪟 WIN).** `git pull` → **`c74c8c15`+**. **Bootstrap auto-starts BOTH radars** (`start_session_radars.ps1`). **Job 1:** pytest → `ci.py` GREEN. **Job 2:** kobo `--sim`. **Job 3:** rx-surfaces. **Never idle** · **replan periodically** (`STRATEGIC_REPLAN_CHECKLIST.md`). Baton **mac**; mode=parallel.
>
> **Samuel+Kings:** Mac 6/6 @ full `GAPS/` · WIN skips `test_every_referenced_image_exists` when `GAPS/` incomplete (env-only).
>

## Session wrap (WIN turn 130, 2026-06-18)

**Shipped this session:** dual-radar bootstrap + strategic replan ping (`--replan` / `STRATEGIC_REPLAN_CHECKLIST`) · pytest fixes WIP · Mac §128 + Esther transcription · STANDING: never idle · both radars auto-start every session.

**Observed blockers:** `ci.py` not yet GREEN — hierarchical_symbols_build slow tests + rx-surfaces remain. Kobo `--sim` epubcheck slow on WIN (K-R2 GREEN).

## Recent ships (full chronology: `dev/CHANGELOG.md`; rotated entries: `dev/archive/SESSION_STATE_archive.md`)

- **Mint-cleanup arc COMPLETE (LANE 0, Phases 0–6)** — anti-bloat lint guards · bootstrap slim · roadmap refresh · archive sweep · decommercialize (~5,300 LOC) · enforce gates (mypy + remote/CI) · **polish (mint-6: `/distribution` console · superpowers INDEX+lint · `audit_caches`→preflight · sonar/`/exec` scrub)**. Plan `docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md`.
- Standalone Ge'ez Bible — Phases A-C shipped (`scripts/build_standalone.py`; 4 books; epubcheck 0/0/0/0; the 9 KJV editions byte-stable).
- English back-translation of the Ge'ez — collated Kings/Samuel (324 v) + all 151 Psalms (`content/translations/geez-tewahedo-en/`).
- Phase D own-versification re-ingest — Patrologia vision-transcription lane; PO Esther paused ~p35 (see the top journal entries).

## Next

> **v1.0.0 RELEASE GATE (plan: `docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`).** **Round 9 Mac COMPLETE.** **WIN:** pytest → `ci.py` GREEN · kobo `--sim` · rx-surfaces. **Mac:** §Turn 128 STK live + reader-sim help. **No tag until plan §8 complete.**

## Inventory pointers

> `dev/MATRIX_MAP.md` = data-flow + base-HTML; `dev/REPO_MAP.md` = file/folder index; `dev/SESSION_PLAYBOOK.md` = lifecycle/gates; `dev/EREADERS.md` = the e-reader compatibility tracker (per-reader caps/quirks/QA — update every device round); `dev/TOOLCHAIN.md` = tool inventory. Popup versions: `scripts/core/popup_versions.py`. Standalone build: `scripts/build_standalone.py`. Manuscript engine: `scripts/core/manuscript_collation.py`. mint-6 surfaces: `scripts/api/distribution.py` + `scripts/templates/distribution.py` (`/distribution` console); `docs/superpowers/INDEX.md` (plans/specs index, guarded by `check_superpowers_coherence`).

## Conventions (unchanged)

Local commit during work; milestone = `bash dev/save_mac.sh -m "…"` (Mac) or `save-all.ps1` (Win). **Remote:** `origin` = GitLab + `github` = GitHub mirror (both private). Tests: `.venv/bin/python -m pytest` + `export PYTHONUTF8=1`. "continue" ≠ "save".

## Console inventory (web.py UI surface, 21)

`APIHELP_HTML` · `AUDIT_HTML` · `AUDIT_LOG_HTML` · `BUILD_MY_BIBLE_HTML` · `BUILD_TRACKER_HTML` · `COMPARE_HTML` · `COVERS_HTML` · `CUSTOMIZE_HTML` · `DIFF_HTML` · `DISTRIBUTION_HTML` · `EXPORT_HTML` · `GREEK_HTML` · `HEBREW_HTML` · `HOME_HTML` · `INDEX_HTML` · `MATRIX_HTML` · `OPS_HTML` · `PREFLIGHT_HTML` · `PUBLISHER_HTML` · `SOURCES_HTML` · `WIZARD_HTML`. Roles since the idiot-proof IA: `HOME_HTML` = the reader-friendly landing at `/` + `/home`; `INDEX_HTML` = the maintainer note editor at `/notes` (+ legacy `/index.html`). Each cross-links to the others (lint_rules check 6.2).