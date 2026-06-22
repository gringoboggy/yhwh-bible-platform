# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE.** `git pull` → read `AGENTS.md` → the triad → this block → `dev/IN_FLIGHT.md`. **Grok-revert cleanup DONE + pushed** (2026-06-21; memory `project_grok_cleanup`). **Mac's Opt# byte-verify DONE** — Opt#3 (`33b79387`) changed build output → **REVERTED** (it dropped tablet badges); Opt#2/#4/#5 byte-neutral → kept. **★ Rules+accuracy consolidation EXECUTED (2026-06-21, Phases A–E,G,H — 9 commits; lint 35/0, all gates green).** The radar/contradiction fixes, count+redundancy+bloat consolidations, hook lane-v2 parity, **RULES §2.6 work-phase loop + `dev/HUMAN_DECISIONS.md`**, and 8 website accuracy fixes all landed (folding the 47-confirmed rules audit + 9-confirmed website audit). **Phase F DONE + LIVE-VERIFIED** (Mac, 2026-06-22): www.yhwhyaway.com live at **91,555** + re-rendered social card; og cache-bust `?v=20260622`; GitHub v0.1.0 release body corrected; `yhwh-website` `3ab8f70..fb4cfcc`. **Remaining = the v1.0.0 device-QA gate** (queued in `dev/HUMAN_DECISIONS.md`). See `dev/IN_FLIGHT.md`.
>
> **★ 2026-06-22 session — drive cleanup + Kobo QA + Opus-audit prep:** drives cleaned (~395 GB; D/E/F mirrored canonical `YHWH-v2.4-backups\` tree) + the GAPS/_acquire **junctions** (→ D: live storage) were deleted then FULLY recovered (`D:\YHWH-v2.4-GAPS`=892 via Mac's GAPS-FULL; memory `backup-drives`+`gaps-folder` — NEVER delete the D: junction targets). Kobo QA → 3 fixes in flight to batch-verify: (a) endnote per-kind redundancy **FIXED** via the 3 note-rehaul flags on catholic-study/evangelical-reformed/eastern-orthodox (`note_group_by_category`=one heading/category) — **pending rebuild-verify**; (b) Gen 10:6→7 Kobo page break (kepub-build artifact, not yet pinned); (c) translation-popup formatting (TBD). New program: **EPUB structural+content audit** (final-product testing per platform; spec `specs/2026-06-22-epub-structural-content-audit.md` + `dev/audit_book_structure.py` TBD). **Deep-audit round 10 ABANDONED** (ran on Sonnet — the `feature-dev:code-reviewer` agentType forced it; `deep-audit.js` now DEFAULTS agents to Opus). **★ NEXT SESSION (Opus 4.8):** (1) re-run `Workflow({scriptPath:'.claude/workflows/deep-audit.js', args:{round:10,scope:'product',lane:'all'}})` (Opus by default now); (2) rebuild catholic-study → verify the redundancy fix + pin/fix the Gen-10 page break + translation formatting → user tests all on Kobo; (3) build+run `dev/audit_book_structure.py` across editions×formats. WIN owns the #3 tablet/Apple clamp regression (Meqabyan bp-26/27/28 + K-R4-2 floor).
>
> **Samuel+Kings:** Mac 6/6 @ full `GAPS/`; **WIN GAPS recovered to 892 files (full) 2026-06-22** via Mac's GAPS-FULL zip (was 697 after the junction-delete incident).
>
> **Catalog truth (current):** **4** canon-shaped study editions × **5** cover colours = **20** M3/M4 assets; website catalog ~**187** assets on v0.1.0 (187-vs-188 to reconcile post-cleanup). Retired built-in SKUs must not return — `lint_rules.check_retired_edition_skus`.
>
> **Corpus truth (current — the canonical live figures; RULES §1 · MATRIX_MAP · SESSION_PLAYBOOK · REPO_MAP all point HERE rather than hard-code):** **91,712** source notes in `content/notes/` · **72** kinds · **15** categories · **87** books · **6** editions (registry). The shipped superset is **91,555** note-refs (was 91,553; Mac rebuild 2026-06-21 — ethiopian 91,555 · catholic-study 43,370 · evangelical-reformed 41,847 · eastern-orthodox 41,819); the website + brand surfaces (index/roadmap/README/BIOS/COPYRIGHT/social-card) are reconciled to it (Phase F).

## Release status (v0.1.0 live · v1.0.0 NOT tagged)

**Shipped (v0.1.0 track):** M1 everywhere · M2 Apple · M4 Kindle catalog columns live · the full Ethiopian Bible EPUB + Kobo kepub. ci pytest triage green · orphan inline-marker strip · 4-edition test pins.

**Blocks the v1.0.0 tag:** M2 Apple audit (K-R5-3 device re-test of the rebuilt tablet artifact) · Kindle STK device bisect (one deliverable m4b) · M3 Kobo (45 kepub + user taps) · **release assets + desktop binaries re-cut at tag** (the live v0.1.0 release assets still attach epubs for the two retired notes-only SKUs from the 2026-06-10 cut — the body now reads "four canon-shaped study editions", so re-cut the attached asset set at the v1.0.0 tag). *(Phase F website publish — DONE + LIVE 2026-06-22, Mac. Rules+accuracy consolidation — DONE 2026-06-21, Phases A–E,G,H. MacClaude Opt# byte-verify — DONE: Opt#3 reverted.)*

## Next — after the cleanup commits (WIN builds · Mac verifies)

> **Rule:** finish the cleanup arc first. Overflow (Esther · CAM · 1ki · extra website passes) = **HOLD**.

| # | WIN (builder) | Mac (verify + scope) |
|---|---------------|----------------------|
| 0 | Land the Grok-revert cleanup (local commits) | **byte-stability rebuild-verify** of the Opt# slices on the clean tree — esp. Opt#3 tablet badge `33b79387` (REVERT if output differs) |
| 1 | M2 Apple audit — K-R5-3 · justify scope · Easton/dict dedup | verify rebuilt tablet artifact + user-device re-test |
| 2 | Kindle STK bisect — glossary spine vs `143407Z`; one candidate m4b | `test_kindle_m4b` · spine/glossary counts · gate `--sim kindle` |
| 3 | rx-surfaces · Kobo `--sim` · sim audit | verify sim-oracle rows; scope the v1.0.0 gate remainder |

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