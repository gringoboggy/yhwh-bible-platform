# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac).** `git pull` → **`turn 143`+** · `bash dev/start_session_radars_mac.sh`. **Role: verifier + planner** (user 2026-06-19) — read `MAC_WORK_QUEUE.md` §**Operating model** first. On each WIN push: verify their slice (targeted pytest/sim) · write `## Mac verify` in `LANE_HANDOFF` · update `### Next scope (Mac)` (max 3). **Do not** patch `kindle_post.py` while WIN owns bisect. Parallel: mirror 141 scrub + Apple/Play sim. mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🪟 WIN).** `git pull` → **`turn 143`+**. **Role: builder** (user 2026-06-19) — implement; list **Mac verify commands** in each `save-all` message. **Next:** `ci.py` finish → `--lf` triage → GREEN → Kindle bisect → push. Read Mac `### Next scope` on pull. **`ci.py` RUNNING** (~14:07; no second full run). Last full gate: **17 failed + 1 error** / 8544 passed. **`pytest --lf`:** 5 persistent reds (build_smoke · hierarchical_symbols ×2 · matter_pages · samkings GAPS). mode=parallel.
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

### Mac (verifier + planner — see `MAC_WORK_QUEUE.md` operating model)

| # | Work | Status |
|---|---|---|
| 0 | **Operating model:** scope next slice · verify WIN's last push · report PASS/FAIL in `LANE_HANDOFF` | **STANDING** |
| 1 | Mirror turn 141 scrub on Mac disk | queued |
| 2 | Apple + Play sim depth (M2/M5 rows) — **parallel** while WIN runs `ci.py` | queued |
| 3 | After each WIN milestone: targeted verify (no dual Kindle fixes) | queued |
| — | Kindle code / STK uploads / catalog / overflow | **HOLD** until WIN bisect ships |

### Post-`ci.py` sequence (WIN builds · Mac verifies)

| Step | WIN (builder) | Mac (verify + scope) |
|------|---------------|----------------------|
| A | `ci.py` finishes → `pytest --lf` → fix reds → re-run `ci.py` until GREEN | Mirror scrub + sim; on WIN push: rerun touched tests + `lint_rules` |
| B | Kindle bisect in `kindle_post.py` → one m4b candidate → push with artifact path | `test_kindle_m4b` · spine/glossary counts vs `143407Z` · gate `--sim kindle` |
| C | If Mac verify PASS: user STK upload (Mac polls only) | Log STK arrival; scope rx-surfaces + Kobo sim for WIN |
| D | rx-surfaces · Kobo `--sim` · sim audit | Verify sim oracle rows; scope v1 gate remainder |

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