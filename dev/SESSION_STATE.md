# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac).** `git pull` → latest · `bash dev/start_session_radars_mac.sh`. **M4b Option B SHIPPED** — study glossary backmatter + badge navigate (`kindle_post.py`); **retired Option A** (`kindle-chapter-study` — 232708Z layout FAIL IMG_0469/0472/0473). **STK candidate:** `~/Desktop/YHWH-reader-sim/kindle/…2026-06-19T000000Z-kindle-m4b.epub` (30,344 badges → 156 glossary pieces · Gen 1 opens scripture). **Awaiting user STK upload** → device QA. **WIN:** hold M4 kindle catalog regen until device re-PASS. mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🪟 WIN).** `git pull` → **`84b3400c`+** (rebase if behind). **Done:** turn 136 canon-SKU scrub @ `96e3e86d` · M3 **20/20** kepubs gated green (`dev/m3_e2e_summary.md`, artifacts in `build/matrix-m3/`). **Job 1:** `py -3 scripts/ci.py` GREEN (`$env:PYTHONUTF8="1"`; expect **~6h** pytest+coverage). **Job 2:** rx-surfaces on fresh builds if ci green. **HOLD:** M4 kindle catalog regen until Mac STK re-PASS. **Do NOT** launch new long builds at session wrap. Baton **windows**; mode=parallel.
>
> **Samuel+Kings:** Mac 6/6 @ full `GAPS/` · WIN skips `test_every_referenced_image_exists` when `GAPS/` incomplete (env-only).
>

## Session wrap (Mac, 2026-06-18) — Christian-scope scrub PUSHED

**Shipped @ `cbf939b8` + `ec6520e3`:** edition SKU removal (`jewish-study`, `scholarly-academic`) · non-Christian note kinds dropped · ~123 corpus notes removed · base HTML prune (122 ids) · M3/M4 **35** assets · catalog regen · `prune_orphan_base_notes.py` · detector/test cleanup.

**Deferred to release tag (v0.1.1 or v1.0.0):** public note/edition counts (README · GitHub/GitLab profile · website hero · RELEASE_NOTES · social card).

**In-flight:** WIN `ci.py` GREEN · format-matrix rebuild for 35-column catalog · optional word-note editorial pass (Rashi citations in linguistics).

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