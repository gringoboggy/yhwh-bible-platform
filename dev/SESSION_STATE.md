# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac, turn 126 DONE).** **Shipped:** apple tablet (27.46 MB · epubcheck 0/0/0/0) · `--sim all` 3/3 with `YHWH_SKIP_KOBO_SIM=1` · toc probe RX P4a fix. **WIN owns:** kobo `--sim` + full `--sim all` 4/4. **Deferred:** STK live (no library container) · Thorium live. `STAGING_MANIFEST.md`. Baton **windows**; mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🪟 WIN).** `git pull` → **`ebbc2597`+**. **Job 1:** pytest triage → `ci.py` GREEN (15 reds mapped in `LANE_HANDOFF` §126 table). **Job 2:** finish Kobo — fresh kepub `2026-06-18T015027Z` staged · `verify_kr2` GREEN · complete `--sim kobo` + update `STAGING_MANIFEST.md`. **Job 3:** rx-surfaces close. **Do not** ask Mac to run kobo gates. Plan: `plans/2026-06-18-reader-simulation-lab.md`. Baton **mac**; mode=parallel.
>
> **Samuel+Kings manuscript images:** CAM acquire scripts idempotent; GAPS tree gitignored — `test_samkings_manifest_complete` **6/6 green** @ Mac turn 118 (WIN red = incomplete `GAPS/` only).
>

## Session wrap (WIN turn 127, 2026-06-18)

**Shipped this session:** turn 126 handoff to Mac (`debce7a9`) · Mac laundry list in `MAC_WORK_QUEUE` §126 + `LANE_HANDOFF` §126 · Kobo lane split (`ebbc2597`) · fresh WIN kobo kepub build started (`2026-06-18T015027Z` · K-R2 GREEN · staged under `build/reader-sim/kobo/`).

**Observed blockers:** `ci.py` RED — 15 pytest reds + 1 error. Reader Sim Lab gate: no `--sim all` until apple tablet artifact exists (Mac) + kobo `--sim` completes (WIN).

## Recent ships (full chronology: `dev/CHANGELOG.md`; rotated entries: `dev/archive/SESSION_STATE_archive.md`)

- **Mint-cleanup arc COMPLETE (LANE 0, Phases 0–6)** — anti-bloat lint guards · bootstrap slim · roadmap refresh · archive sweep · decommercialize (~5,300 LOC) · enforce gates (mypy + remote/CI) · **polish (mint-6: `/distribution` console · superpowers INDEX+lint · `audit_caches`→preflight · sonar/`/exec` scrub)**. Plan `docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md`.
- Standalone Ge'ez Bible — Phases A-C shipped (`scripts/build_standalone.py`; 4 books; epubcheck 0/0/0/0; the 9 KJV editions byte-stable).
- English back-translation of the Ge'ez — collated Kings/Samuel (324 v) + all 151 Psalms (`content/translations/geez-tewahedo-en/`).
- Phase D own-versification re-ingest — Patrologia vision-transcription lane; PO Esther paused ~p35 (see the top journal entries).

## Next

> **v1.0.0 RELEASE GATE (plan: `docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`).** **Round 8 remediation COMPLETE** · **Round 9 Mac COMPLETE** @ turn 120. **WIN remainder:** pytest triage · rx-surfaces · reader-sim kobo sim. **Mac:** apple tablet + STK/Thorium live. **M3:** 45/45 attached · **M4:** catalog live · website `efb7386`. **No tag until plan §8 complete.**

## Inventory pointers

> `dev/MATRIX_MAP.md` = data-flow + base-HTML; `dev/REPO_MAP.md` = file/folder index; `dev/SESSION_PLAYBOOK.md` = lifecycle/gates; `dev/EREADERS.md` = the e-reader compatibility tracker (per-reader caps/quirks/QA — update every device round); `dev/TOOLCHAIN.md` = tool inventory. Popup versions: `scripts/core/popup_versions.py`. Standalone build: `scripts/build_standalone.py`. Manuscript engine: `scripts/core/manuscript_collation.py`. mint-6 surfaces: `scripts/api/distribution.py` + `scripts/templates/distribution.py` (`/distribution` console); `docs/superpowers/INDEX.md` (plans/specs index, guarded by `check_superpowers_coherence`).

## Conventions (unchanged)

Local commit during work; milestone = `bash dev/save_mac.sh -m "…"` (Mac) or `save-all.ps1` (Win). **Remote:** `origin` = GitLab + `github` = GitHub mirror (both private). Tests: `.venv/bin/python -m pytest` + `export PYTHONUTF8=1`. "continue" ≠ "save".

## Console inventory (web.py UI surface, 21)

`APIHELP_HTML` · `AUDIT_HTML` · `AUDIT_LOG_HTML` · `BUILD_MY_BIBLE_HTML` · `BUILD_TRACKER_HTML` · `COMPARE_HTML` · `COVERS_HTML` · `CUSTOMIZE_HTML` · `DIFF_HTML` · `DISTRIBUTION_HTML` · `EXPORT_HTML` · `GREEK_HTML` · `HEBREW_HTML` · `HOME_HTML` · `INDEX_HTML` · `MATRIX_HTML` · `OPS_HTML` · `PREFLIGHT_HTML` · `PUBLISHER_HTML` · `SOURCES_HTML` · `WIZARD_HTML`. Roles since the idiot-proof IA: `HOME_HTML` = the reader-friendly landing at `/` + `/home`; `INDEX_HTML` = the maintainer note editor at `/notes` (+ legacy `/index.html`). Each cross-links to the others (lint_rules check 6.2).