# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🪟 WIN, turn 125).** **NOW:** `ci.py` finish · `rx-surfaces` · ACK Mac `f3b12433` · stage `build/reader-sim/` from cached epubs · run `--sim all`. **No matrix builds** until `ci.py` GREEN. Plan: `plans/2026-06-18-reader-simulation-lab.md`. Baton **windows**; mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac, turn 125).** **READ FIRST:** `dev/LANE_HANDOFF.md` §**Mac turn 125 — full runbook** (10 sections: bootstrap · ACK · stage `build/reader-sim/` · STK live poll · Thorium `--live` · M4b 6-pack gate · `--sim all` · optional Play AVD · save cadence · done criteria). Queue: `MAC_WORK_QUEUE.md` §Turn 125. **NO** `build_edition` / matrix / `ci.py` until WIN `ci.py` GREEN. `lane_watch --bg`. Baton **mac** (truth_owner); mode=parallel.
>
> **Samuel+Kings manuscript images:** CAM acquire scripts idempotent; GAPS tree gitignored — `test_samkings_manifest_complete` **6/6 green** @ Mac turn 118.
>

## Recent ships (full chronology: `dev/CHANGELOG.md`; rotated entries: `dev/archive/SESSION_STATE_archive.md`)

- **Mint-cleanup arc COMPLETE (LANE 0, Phases 0–6)** — anti-bloat lint guards · bootstrap slim · roadmap refresh · archive sweep · decommercialize (~5,300 LOC) · enforce gates (mypy + remote/CI) · **polish (mint-6: `/distribution` console · superpowers INDEX+lint · `audit_caches`→preflight · sonar/`/exec` scrub)**. Plan `docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md`.
- Standalone Ge'ez Bible — Phases A-C shipped (`scripts/build_standalone.py`; 4 books; epubcheck 0/0/0/0; the 9 KJV editions byte-stable).
- English back-translation of the Ge'ez — collated Kings/Samuel (324 v) + all 151 Psalms (`content/translations/geez-tewahedo-en/`).
- Phase D own-versification re-ingest — Patrologia vision-transcription lane; PO Esther paused ~p35 (see the top journal entries).

## Next

> **v1.0.0 RELEASE GATE (plan: `docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`).** **Round 8 remediation COMPLETE** · **Round 9 Mac COMPLETE** @ turn 120. **WIN remainder:** rx-surfaces + full ci.py + merge; **user:** Kobo tap + Play QA. **M3:** 45/45 attached · **M4:** catalog live · website `efb7386`. **No tag until plan §8 complete.**

## Inventory pointers

> `dev/MATRIX_MAP.md` = data-flow + base-HTML; `dev/REPO_MAP.md` = file/folder index; `dev/SESSION_PLAYBOOK.md` = lifecycle/gates; `dev/EREADERS.md` = the e-reader compatibility tracker (per-reader caps/quirks/QA — update every device round); `dev/TOOLCHAIN.md` = tool inventory. Popup versions: `scripts/core/popup_versions.py`. Standalone build: `scripts/build_standalone.py`. Manuscript engine: `scripts/core/manuscript_collation.py`. mint-6 surfaces: `scripts/api/distribution.py` + `scripts/templates/distribution.py` (`/distribution` console); `docs/superpowers/INDEX.md` (plans/specs index, guarded by `check_superpowers_coherence`).

## Conventions (unchanged)

Local commit during work; milestone = `bash dev/save_mac.sh -m "…"` (Mac) or `save-all.ps1` (Win). **Remote:** `origin` = GitLab + `github` = GitHub mirror (both private). Tests: `.venv/bin/python -m pytest` + `export PYTHONUTF8=1`. "continue" ≠ "save".

## Console inventory (web.py UI surface, 21)

`APIHELP_HTML` · `AUDIT_HTML` · `AUDIT_LOG_HTML` · `BUILD_MY_BIBLE_HTML` · `BUILD_TRACKER_HTML` · `COMPARE_HTML` · `COVERS_HTML` · `CUSTOMIZE_HTML` · `DIFF_HTML` · `DISTRIBUTION_HTML` · `EXPORT_HTML` · `GREEK_HTML` · `HEBREW_HTML` · `HOME_HTML` · `INDEX_HTML` · `MATRIX_HTML` · `OPS_HTML` · `PREFLIGHT_HTML` · `PUBLISHER_HTML` · `SOURCES_HTML` · `WIZARD_HTML`. Roles since the idiot-proof IA: `HOME_HTML` = the reader-friendly landing at `/` + `/home`; `INDEX_HTML` = the maintainer note editor at `/notes` (+ legacy `/index.html`). Each cross-links to the others (lint_rules check 6.2).
