# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac).** `git pull` → **`ab33f543`+** · `bash dev/start_session_radars_mac.sh`. **STK `144600Z` UPLOAD FAIL (user-confirmed 2026-06-19):** strict gate **0/0/0/0** but **no new library file** (`com.amazon.Lassen` still 3 files). Bisect signal: **545 spine / 155 glossary pieces** vs proven-deliverable `143407Z` (**390 spine / 0 glossary**). **WIN:** Kindle lane takeover + STK bisect per turn 139. **Mac:** Apple/Play sim + pre-work; HOLD catalog. mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🪟 WIN).** `git pull` → **`turn 139`+** (rebase if behind). **Day plan (2026-06-19, user-directed):** autonomous test-only arc — **no human device taps** unless an STK upload lands unprompted. **WIN:** `ci.py` IN FLIGHT (~6h) → rx-surfaces → Kobo `--sim` → **Kindle lane takeover** (structural/M4b gates + STK-failure bisect; Mac hands off) → **sim-pipeline fidelity audit** (map `--gate`/`--sim` → `EREADERS`/`platform-matrix` → device oracle → gaps). **Mac:** Apple Books + Play Books sim depth (Thorium CDP + Books.app proxy); STK poll only if `144600Z` arrives; **pre-work commits** for WIN (artifacts + tap matrices + Kindle notes). Baton **windows**; mode=parallel.
>
> **Samuel+Kings:** Mac 6/6 @ full `GAPS/` · WIN skips `test_every_referenced_image_exists` when `GAPS/` incomplete (env-only).
>

## Session wrap (Mac, 2026-06-18) — Christian-scope scrub PUSHED

**Shipped @ `cbf939b8` + `ec6520e3`:** retired notes-only / non-Christian edition SKUs · non-Christian note kinds dropped · ~123 corpus notes removed · base HTML prune (122 ids) · M3/M4 **35** assets · catalog regen · `prune_orphan_base_notes.py` · detector/test cleanup.

**Deferred to release tag (v0.1.1 or v1.0.0):** public note/edition counts (README · GitHub/GitLab profile · website hero · RELEASE_NOTES · social card).

**In-flight:** WIN `ci.py` GREEN · format-matrix rebuild for 35-column catalog · optional word-note editorial pass (Rashi citations in linguistics).

## Recent ships (full chronology: `dev/CHANGELOG.md`; rotated entries: `dev/archive/SESSION_STATE_archive.md`)

- **Mint-cleanup arc COMPLETE (LANE 0, Phases 0–6)** — anti-bloat lint guards · bootstrap slim · roadmap refresh · archive sweep · decommercialize (~5,300 LOC) · enforce gates (mypy + remote/CI) · **polish (mint-6: `/distribution` console · superpowers INDEX+lint · `audit_caches`→preflight · sonar/`/exec` scrub)**. Plan `docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md`.
- Standalone Ge'ez Bible — Phases A-C shipped (`scripts/build_standalone.py`; 4 books; epubcheck 0/0/0/0; catalog study editions byte-stable).
- English back-translation of the Ge'ez — collated Kings/Samuel (324 v) + all 151 Psalms (`content/translations/geez-tewahedo-en/`).
- Phase D own-versification re-ingest — Patrologia vision-transcription lane; PO Esther paused ~p35 (see the top journal entries).

## Next — autonomous day plan (2026-06-19)

> **v1.0.0 RELEASE GATE** + **Reader Sim Lab** (`plans/2026-06-18-reader-simulation-lab.md`). User: plan ~24h parallel work; **tests/sim only** (skip scheduled human tap rounds); Mac sends pre-work; WIN takes Kindle after Kobo.

### WIN schedule

| Block | Work |
|---|---|
| **0–6h** | `ci.py` GREEN (`PYTHONUTF8=1`; no parallel pytest/builds) |
| **While CI** | Kobo `--gate` (gate-only epubcheck) · sim-fidelity audit scaffold · `--ping` |
| **Post-green** | rx-surfaces (eth + catholic-study) · Kobo `--sim` · Kindle `--gate --m4b` + STK-failure bisect · `ci.py --reader-sim-gates` · sim fidelity report · dishonest/stub audit if RAM free |
| **Hand Mac** | rx-surfaces summary · kindle gate findings · sim-oracle gap table |

### Mac schedule

| Block | Work |
|---|---|
| **Primary** | Apple: Thorium CDP + Books.app on tablet artifacts · Play: Thorium everywhere + emulator spike |
| **STK** | Poll `144600Z` if upload lands — **automated only**; document ingest, skip user tap matrix |
| **Pre-work WIN** | Stage `build/reader-sim/` updates · `STAGING_MANIFEST.md` · M2/M5 tap assertion rows · Kindle handoff notes (`file:line` + what Mac tried) |
| **Overflow** | Esther Patrologia · CAM pre-pull · 1ki EN ch11+ |

**HOLD:** M4 catalog regen until sim audit + Kindle structural re-gate green on WIN.

## Inventory pointers

> `dev/MATRIX_MAP.md` = data-flow + base-HTML; `dev/REPO_MAP.md` = file/folder index; `dev/SESSION_PLAYBOOK.md` = lifecycle/gates; `dev/EREADERS.md` = the e-reader compatibility tracker (per-reader caps/quirks/QA — update every device round); `dev/TOOLCHAIN.md` = tool inventory. Popup versions: `scripts/core/popup_versions.py`. Standalone build: `scripts/build_standalone.py`. Manuscript engine: `scripts/core/manuscript_collation.py`. mint-6 surfaces: `scripts/api/distribution.py` + `scripts/templates/distribution.py` (`/distribution` console); `docs/superpowers/INDEX.md` (plans/specs index, guarded by `check_superpowers_coherence`).

## Conventions (unchanged)

Local commit during work; milestone = `bash dev/save_mac.sh -m "…"` (Mac) or `save-all.ps1` (Win). **Remote:** `origin` = GitLab + `github` = GitHub mirror (both private). Tests: `.venv/bin/python -m pytest` + `export PYTHONUTF8=1`. "continue" ≠ "save".

## Console inventory (web.py UI surface, 21)

`APIHELP_HTML` · `AUDIT_HTML` · `AUDIT_LOG_HTML` · `BUILD_MY_BIBLE_HTML` · `BUILD_TRACKER_HTML` · `COMPARE_HTML` · `COVERS_HTML` · `CUSTOMIZE_HTML` · `DIFF_HTML` · `DISTRIBUTION_HTML` · `EXPORT_HTML` · `GREEK_HTML` · `HEBREW_HTML` · `HOME_HTML` · `INDEX_HTML` · `MATRIX_HTML` · `OPS_HTML` · `PREFLIGHT_HTML` · `PUBLISHER_HTML` · `SOURCES_HTML` · `WIZARD_HTML`. Roles since the idiot-proof IA: `HOME_HTML` = the reader-friendly landing at `/` + `/home`; `INDEX_HTML` = the maintainer note editor at `/notes` (+ legacy `/index.html`). Each cross-links to the others (lint_rules check 6.2).