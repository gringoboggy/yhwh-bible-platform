# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac).** `git pull` → **`turn 142`+** · `bash dev/start_session_radars_mac.sh`. **FOCUS RESET (user 2026-06-19):** finish **one** job list — no overflow until `#1` is done or blocked with `file:line`. **Your queue:** `MAC_WORK_QUEUE.md` §Turn 142. **(1)** Mirror WIN turn 141 scrub (lint `retired_edition_skus` · purge Desktop QA junk · deploy website if skew). **(2)** Apple + Play sim only (turn 139 §1–2). **HOLD:** Kindle code · STK uploads · M4 catalog · Esther/CAM/1ki overflow until WIN STK bisect lands. mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🪟 WIN).** `git pull` → **`turn 142`+**. **FOCUS RESET (user 2026-06-19):** release gate = **one vertical slice** — `ci.py` GREEN → Kindle STK glossary bisect vs proven `143407Z` (390 spine / 0 glossary) → then rx-surfaces/sim. **`ci.py` RUNNING** (started 2026-06-19 ~14:07 local; do not start a second full run). Last completed full gate: **17 failed + 1 error** / 8544 passed (~4h52m, pre–turn-141 scrub). **`pytest --lf`** (2026-06-18): **5 persistent reds** on WIN (build_smoke inject · hierarchical_symbols ×2 · matter_pages · samkings GAPS images). **STK blocker:** `144600Z` failed upload — 545 spine + 155 glossary pieces vs `143407Z`. **Mac:** mirror + sim only; baton **windows**; mode=parallel.
>
> **Samuel+Kings:** Mac 6/6 @ full `GAPS/` · WIN skips `test_every_referenced_image_exists` when `GAPS/` incomplete (env-only).
>
> **Catalog truth (current):** **4** canon-shaped study editions × **5** cover colours = **20** M3/M4 assets; website catalog **187** assets on v0.1.0. Retired built-in SKUs must not return — `lint_rules.check_retired_edition_skus`.

## Session wrap (WIN, 2026-06-19) — focus reset + agent bootstrap

**Shipped this session:** `AGENTS.md` fresh-session read order · `README.md` project map entry · user-directed lane focus reset (turn 142) · truth-record scrub (35→20 assets, ci status honest).

**Prior ships (turn 141):** retired edition SKU deep scrub · `retired_edition_skus` lint gate · public surfaces 4+2 · website catalog regen.

**Blocked:** M4 catalog regen · STK deliverability · v1.0.0 tag — until `ci.py` GREEN + one STK-deliverable m4b epub.

## Next — release gate slice (turn 142, user-directed)

> **Rule:** No new laundry-list items until the current `#1` is checked off or explicitly blocked. Overflow (Esther, CAM, 1ki, extra website passes) = **HOLD**.

### WIN (owns the open loop)

| # | Work | Status |
|---|---|---|
| 1 | `ci.py` GREEN — let in-flight run finish; triage reds if still failing | **RUNNING** |
| 2 | Kindle STK bisect — glossary spine off vs `143407Z` control; one candidate m4b | queued |
| 3 | rx-surfaces · Kobo `--sim` · sim-pipeline audit | **HOLD** until 1–2 |

### Mac (mirror + sim only)

| # | Work | Status |
|---|---|---|
| 1 | Mirror turn 141 scrub on Mac disk | queued |
| 2 | Apple Books + Play Books sim depth (M2/M5 matrix rows) | queued |
| — | Kindle / STK / catalog / overflow | **HOLD** |

## Recent ships (full chronology: `dev/CHANGELOG.md`; rotated entries: `dev/archive/SESSION_STATE_archive.md`)

- **Mint-cleanup arc COMPLETE (LANE 0, Phases 0–6)** — anti-bloat lint guards · bootstrap slim · roadmap refresh · archive sweep · decommercialize (~5,300 LOC) · enforce gates (mypy + remote/CI) · **polish (mint-6: `/distribution` console · superpowers INDEX+lint · `audit_caches`→preflight · sonar/`/exec` scrub)**. Plan `docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md`.
- Standalone Ge'ez Bible — Phases A-C shipped (`scripts/build_standalone.py`; 4 books; epubcheck 0/0/0/0; catalog study editions byte-stable).
- English back-translation of the Ge'ez — collated Kings/Samuel (324 v) + all 151 Psalms (`content/translations/geez-tewahedo-en/`).
- Phase D own-versification re-ingest — Patrologia vision-transcription lane; PO Esther paused ~p35 (see the top journal entries).

## Inventory pointers

> `dev/MATRIX_MAP.md` = data-flow + base-HTML; `dev/REPO_MAP.md` = file/folder index; `dev/SESSION_PLAYBOOK.md` = lifecycle/gates; `dev/EREADERS.md` = the e-reader compatibility tracker (per-reader caps/quirks/QA — update every device round); `dev/TOOLCHAIN.md` = tool inventory. Popup versions: `scripts/core/popup_versions.py`. Standalone build: `scripts/build_standalone.py`. Manuscript engine: `scripts/core/manuscript_collation.py`. mint-6 surfaces: `scripts/api/distribution.py` + `scripts/templates/distribution.py` (`/distribution` console); `docs/superpowers/INDEX.md` (plans/specs index, guarded by `check_superpowers_coherence`).

## Conventions (unchanged)

Local commit during work; milestone = `bash dev/save_mac.sh -m "…"` (Mac) or `save-all.ps1` (Win). **Remote:** `origin` = GitLab + `github` = GitHub mirror (both private). Tests: `.venv/bin/python -m pytest` + `export PYTHONUTF8=1`. "continue" ≠ "save".

## Console inventory (web.py UI surface, 21)

`APIHELP_HTML` · `AUDIT_HTML` · `AUDIT_LOG_HTML` · `BUILD_MY_BIBLE_HTML` · `BUILD_TRACKER_HTML` · `COMPARE_HTML` · `COVERS_HTML` · `CUSTOMIZE_HTML` · `DIFF_HTML` · `DISTRIBUTION_HTML` · `EXPORT_HTML` · `GREEK_HTML` · `HEBREW_HTML` · `HOME_HTML` · `INDEX_HTML` · `MATRIX_HTML` · `OPS_HTML` · `PREFLIGHT_HTML` · `PUBLISHER_HTML` · `SOURCES_HTML` · `WIZARD_HTML`. Roles since the idiot-proof IA: `HOME_HTML` = the reader-friendly landing at `/` + `/home`; `INDEX_HTML` = the maintainer note editor at `/notes` (+ legacy `/index.html`). Each cross-links to the others (lint_rules check 6.2).