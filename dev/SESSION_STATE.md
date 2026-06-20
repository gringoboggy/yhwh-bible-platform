# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac).** `git pull` → **`091a3f14`+** · `bash dev/start_session_radars_mac.sh`. **Role: verifier + planner** — read `AGENTS.md` → triad → this block · then `MAC_WORK_QUEUE.md` §Operating model. **First job:** verify WIN turn 144 ci triage (`LANE_HANDOFF` §Mac verify turn 144) → `## Mac verify (turn 144)` → `save_mac.sh`. **HOLD:** `kindle_post.py` · `build_edition.py` M2 fixes · STK uploads · catalog · overflow until WIN ships next slice. mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🪟 WIN).** `git pull` → **`091a3f14`+** · read `AGENTS.md` → triad → this block. **Role: builder.** **ci triage DONE** (turn 144): `pytest --lf` 9/9 · edition_stats cross-check PASS · orphan marker strip shipped. **Pick up #1:** M2 Apple audit (K-R5-3 book-title badge bleed · popup justify · Easton dedup — `LANE_HANDOFF` §user-fail) **or** #2 Kindle STK bisect vs `143407Z` (390 spine / 0 glossary). List **Mac verify commands** in each save. Full `ci.py` re-run optional. mode=parallel.
>
> **Samuel+Kings:** Mac 6/6 @ full `GAPS/` · WIN skips `test_every_referenced_image_exists` when `GAPS/` incomplete (env-only).
>
> **Catalog truth (current):** **4** canon-shaped study editions × **5** cover colours = **20** M3/M4 assets; website catalog **187** assets on v0.1.0. Retired built-in SKUs must not return — `lint_rules.check_retired_edition_skus`.

## Session wrap (WIN, 2026-06-20) — turn 145 fresh-session handoff @ `091a3f14`

**Shipped:** ci pytest triage (turn 144: 8 reds → 0 on `--lf`) · orphan inline marker strip · 4-edition test pins · focus-reset + WIN-builds/Mac-verifies docs (turns 142–143) · truth records refreshed for next session (turn 145). **Not started:** M2 Apple audit · Kindle STK bisect.

**Mac status @ handoff:** turn 142 saved @ `2193216c` (tablet profile + sim findings) · turn 144 verify **pending** on Mac box (commands in `LANE_HANDOFF`).

**Blocked:** M4 catalog · STK deliverability · v1.0.0 tag — until M2 audit + one STK-deliverable m4b.

## Next — release gate slice (turn 145, fresh session)

> **Rule:** No new laundry-list items until the current `#1` is checked off or explicitly blocked. Overflow (Esther, CAM, 1ki, extra website passes) = **HOLD**.

### WIN (owns the open loop)

| # | Work | Status |
|---|---|---|
| 1 | M2 Apple audit — K-R5-3 · justify scope · Easton/dict dedup (`LANE_HANDOFF` §user-fail) | **NEXT** |
| 2 | Kindle STK bisect — glossary spine off vs `143407Z`; one candidate m4b | queued |
| 3 | rx-surfaces · Kobo `--sim` · sim audit | **HOLD** until 1–2 |
| — | `ci.py` full re-run | optional (triage done @ turn 144) |

### Mac (verifier + planner — see `MAC_WORK_QUEUE.md` operating model)

| # | Work | Status |
|---|---|---|
| 0 | **Operating model:** scope next slice · verify WIN's last push · report PASS/FAIL in `LANE_HANDOFF` | **STANDING** |
| 1 | Mirror turn 141 scrub on Mac disk | **done** — retired SKU Desktop purge · catalog regen 187 · `retired_edition_skus` PASS |
| 2 | Apple + Play sim depth (M2/M5 rows) | **partial** — `195709Z` thorium gate PASS · `verify_kr2` K-R5-3 FAIL (262×) · Play gate PASS · **user device FAIL** → WIN audit |
| 3 | **Verify turn 144 ci triage** (pytest + `lint_rules` per CHANGELOG) | **NEXT on Mac** |
| 4 | After each WIN milestone: targeted verify (no dual Kindle/M2 fixes) | standing |
| — | Tablet-profile WIP (`build_edition.py`) | **saved** @ `2193216c` — device QA still FAIL; WIN owns M2 audit fix |
| — | Kindle code / STK uploads / catalog / overflow | **HOLD** until WIN bisect ships |

### Post-`ci.py` sequence (WIN builds · Mac verifies)

| Step | WIN (builder) | Mac (verify + scope) |
|------|---------------|----------------------|
| A | `ci.py` finishes → `pytest --lf` → fix reds → re-run `ci.py` until GREEN | Mirror scrub + sim **done**; on WIN push: rerun touched tests + `lint_rules` |
| B | Kindle bisect in `kindle_post.py` → one m4b candidate → push with artifact path | `test_kindle_m4b` · spine/glossary counts vs `143407Z` · gate `--sim kindle` |
| C | M2 Apple audit — fix K-R5-3 + justify + Easton redundancy per handoff §user-fail | Verify rebuilt tablet artifact + user device re-test |
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