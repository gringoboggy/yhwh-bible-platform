# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->

> **➤➤➤ 2026-05-31 (LATEST) — ▶ MINT-7 quality pass — AUDIT DONE, plan written, EXECUTION PENDING (start Phase A next session).** The mint-cleanup arc (Phases 0–6) is COMPLETE; the user scoped a follow-on "mint-7" = "all of them" (correctness + code-quality + security). A 15-agent audit (`wf_365eda78`, 6 dimensions × find→verify) found ~30 issues, 9 critical/high independently verified. NO mint-7 code shipped yet. **RESUME HERE:** read **`docs/superpowers/plans/2026-05-31-mint-7-quality-pass.md`** (Phases A–E, verifier-corrected fixes) + the raw findings `docs/superpowers/2026-05-31-mint-7-audit-findings.md`, then execute. **Order:** Phase A (★book-code BUGCLUSTER) → C (security, cheap+important) → B (at-scale) → D (debt) → E (tests/doc). Phase A first tasks: (A1) complete `_normalize_book_code` `_BOOK_CODE_ALIASES` (+mar→mrk, jol→joe, ezk→eze, nam→nah, php→phi); (A2) `TSK_BOOK_REMAP`→canonical + **rebuild `tsk_xrefs.json`** (the one LIVE gap, ~1,525 xrefs; ⚠ do NOT normalize the query in `Tsk.refs_for` — the data is legacy-keyed); fix `KENYON_BOOK_NAME_TO_CODE` (joel→joe/phil→phi/jas→jam); (A4) **DELETE** the 56 stale `ezk_/jol_/nam_*.json` candidate files (they're superseded duplicates — canonical eze_/joe_/nah_ already exist; migrating would COLLIDE); (A5) meta-test every book-code-map value is canonical + has a notes file. Save = full 5-leg (`save-all.ps1`) at each phase close. **All synced at `be80ad2e`** (local + GitLab + GitHub + E: + F:).
>
> **➤➤➤ PARALLEL LANE (paused) — Phase D1b: PO Esther vision marathon, PAUSED at p28** (continues canonical 1:8 `…ፈቃደ` tail → 1:9..). Method: controller renders `render_body_for_vision(doc[28], …, dpi=230, geez_top_fraction≈0.45 — re-check per page)` to OS temp → 2 blind Opus transcribers + adjudicator + calibration (per `_vision_notes` (h)–(p)); assemble 1:8 + 1:9..; Ethiopic-only codepoint-validate; write accumulator page `'28'`; commit. MAX 1 heavy vision agent; per-unit commits. Accumulator = pages 24+25+26+27. After all PO Esther units: Task-4 `est_patrologia.py` via `po_vision_store.write_po_vision_module(...)` → xref sidecar → standalone wiring (5 books, epubcheck 0/0, 9 editions byte-stable) → EN back-translation. Plan `docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md`; decisions `content/translations/sources/patrologia/_vision_notes.md`. (mint-7 and this Esther lane are independent — RULES §2.5 never-single-thread; pick either to advance.)
>

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via the Esther vision lane.

## Background backlog (never single-thread — RULES §2.5)

> When a lane frees, auto-pick the next: the mint-7 plan phases · CAM hi-res pre-pull · base-structured re-collation · geez→kjv xref anchoring · Phase-E Clementine (1es/2es) · doc-coherence currency · test-coverage growth · Phase-D source acquisition.
