# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🪟 WIN, turn 124).** **NOW:** `ci.py` finish · `rx-surfaces` · gate-only sim prep (no matrix builds). **Mac parallel:** `stk_channel.sh` + Thorium sim layers. Kobo `--sim` wired. Plan: `plans/2026-06-18-reader-simulation-lab.md`. Baton **windows**; mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac, turn 124).** **START:** `git pull --rebase origin main` → read `dev/LANE_HANDOFF.md` turn 124 block → `dev/MAC_WORK_QUEUE.md` §Turn 124 → `bash dev/lane_watch_mac.sh --bg`. **DO (prep only — NO matrix builds while WIN `ci.py` runs):** (1) `dev/reader_sim/kindle/stk_channel.sh` — STK → Kindle-for-Mac poll, not Previewer; gate on `~/Desktop/YHWH-kindle-m4b-qa/` (2) Thorium/CDP wire `apple/sim.sh` + `play/thorium_spike.sh`; flip `SIM_LAYERS_READY` in `scripts/reader_sim.py` when green (3) m4b-2 `ethiopian-tewahedo` fix if quick. **ACK** pull through `8e3169b2+`. **DEFERRED:** native reader `plans/2026-06-18-yhwh-native-reader-deferred.md`. Baton **mac** (truth_owner); mode=parallel.
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
