# In-flight work — current task tracker

<!-- TRACKER-STATE: idle -->

> **➤➤➤ 2026-05-31 (LATEST) — ✅ MINT-CLEANUP ARC COMPLETE (LANE 0, Phases 0–6); tracker reset to idle — no task mid-execution.** mint-6 polish shipped this session in 5 local commits (`451ac84c` sonar/log sweep + `/exec` scrub · `3955d398` superpowers INDEX + `check_superpowers_coherence` lint · `d33188ae` `/distribution` console · `26289067` `audit_caches`→preflight · `3ed0473b` adversarial-review fixes). Additive only — no build-pipeline edit; 9 KJV editions byte-stable; cross-link 18 consoles; `lint_rules` 0 fail (lone warn = CHANGELOG-size). A 4-reviewer adversarial workflow over the diff confirmed 8 findings, all fixed. DECLINED (minimal-hooks): SessionEnd hygiene hook. Full detail in `dev/CHANGELOG.md` (2026-05-31 mint-6) + the master plan (Phases 0–6 ✓). **Backups: local commits only this session — push to GitLab+GitHub + E:/F: bundle still pending at the time of writing.**
>
> **➤➤➤ NEXT-RESUME (critical path) — Phase D1b: PO Esther vision marathon, PAUSED at p28** (continues canonical 1:8 `…ፈቃደ` tail → 1:9..). Method: render `render_body_for_vision(doc[28], …, dpi=230, geez_top_fraction≈0.45 — re-check per page)` to OS temp (controller renders; subagents Read the PNG) → 2 blind Opus transcribers + adjudicator + a calibration check (per `_vision_notes` (h)–(p)); assemble 1:8 (concatenate its p28 head onto the p27 `…ፈቃደ` tail) + 1:9..; Ethiopic-only codepoint-validate; write accumulator page `'28'`; commit. MAX 1 heavy vision agent; per-unit commits; controller renders / subagents Read. Accumulator so far = pages 24+25+26+27. **After all PO Esther units:** Task-4 final write `est_patrologia.py` via `po_vision_store.write_po_vision_module(slot='est_patrologia', book='est', verses=<assembled; DROP the p24/p25/p26 partials, use the complete verses in their completing pages>, po_book='est', page_range=(24,65))` → `ruff format` → Task 5 xref sidecar → Task 6 standalone wiring (build 5 books, epubcheck 0/0, 9 editions byte-stable) → Task 7 EN back-translation. Plan `docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md`; decisions `content/translations/sources/patrologia/_vision_notes.md`.
>

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via the Esther vision lane.

## Background backlog (never single-thread — RULES §2.5)

> When a lane frees, auto-pick the next: CAM hi-res pre-pull of upcoming chapters · base-structured re-collation of pending chapters · geez→kjv cross-ref anchoring · the deferred Phase-E Clementine chapters (1es 5/8, 2es 14) · the code-debt audit tail · doc-coherence currency (MATRIX_MAP / REPO_MAP / CHANGELOG) · test-coverage growth · Phase-D own-versification source acquisition.
