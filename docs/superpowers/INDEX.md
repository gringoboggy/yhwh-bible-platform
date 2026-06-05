# Superpowers — Plans & Specs Index

Status-grouped inventory of every strategic plan and design spec under `docs/superpowers/`. Each file carries a `**Status:**` header in its first lines; this index is generated from those headers and verified by the `superpowers_coherence` lint check (`scripts/lint_rules.py`).

> **Authoritative ship-ledger:** `dev/CHANGELOG.md`. The statuses here are a navigation aid, not a precise build record.

**62 documents** — 41 plans · 21 specs.

## In progress (18)

| Date | Type | Title | Path | Status |
|------|------|-------|------|--------|
| 2026-06-05 | Plan | RX Phase 4 — Kobo structural: compact TOC + build-time file-splitter | `plans/2026-06-05-rx-phase4-toc-and-filesplit-plan.md` | IN PROGRESS 2026-06-05 — Phase 4b file-splitter (`apply_file_split`) SHIPPED + epubcheck 0/0/0/0 (ethiopian-tewahedo → 227 pieces, max 472 KB from 5 MB; 0 broken links; default ON). Phase 4a (unwrap `<details>` TOC + drop `.toc-chapters` flexbox) + program-end gate remain |
| 2026-06-05 | Plan | EPUB Reading-Experience Overhaul (Kobo device-QA: strip 88,773 `[Reviewer:]` scaffolds · deferred `badge` note-display · cross-reader/Kobo fixes · original-language font embed) | `plans/2026-06-05-epub-reading-experience-overhaul.md` | program plan 2026-06-05 — Layer A discovery (D1–D6) running · Layer B 5 phases (strip → CSS → fonts → Kobo structural → badge) · Layer C Mac compat-research; constraint = ALL notes/features ON (declutter via display) |
| 2026-06-04 | Plan | Edition Cover + Truthful Front Matter (σ.1–σ.6: build-accurate counter · HOLY BIBLE cover · Your Edition page · /customize identity · Ge'ez/Amharic covers · live-console reconcile) | `plans/2026-06-04-edition-cover-and-truthful-front-matter-plan.md` | SHIPPED 2026-06-04 — all 6 phases done (σ.1 build-accurate counter · σ.2 HOLY-BIBLE cover + overflow-proof fitter · σ.3 "Your Edition" page + glossary→counter · σ.4 /customize identity control · σ.5 Ge'ez/Amharic Ethiopic covers · σ.6 count reconcile). Per-task spec+code review + visual QA; epubcheck 0/0/0/0; determinism + cross-check green. Commits `4bb03ba6`…`663987af` etc. (5-leg pushed). |
| 2026-06-04 | Plan | Hierarchical Customization — Phase C2: the `/build-my-bible` Navigator Console | `plans/2026-06-04-hierarchical-customize-phaseC2-navigator.md` | SHIPPED 2026-06-04 — C2-2…C2-6 done: the `/build-my-bible` navigator console (drill-down + breadcrumb; interactive symbol tri-state + popup checklists + per-note ships?-toggle; saves via `/api/edition-meta` + `/api/edition/<id>/note-override`). Byte-neutral; byte-stability gate + live Playwright QA passed; per-task + holistic review clean. C3 (polish) follows. |
| 2026-06-04 | Plan | Hierarchical Customization — Phase B: Popup-Language Engine | `plans/2026-06-04-hierarchical-customize-phaseB-popup-engine.md` | IN PROGRESS 2026-06-04 — ready to execute. Phase B of the hierarchical-customization spec (`docs/superpowers/specs/2026-06-04-hierarchical-edition-customization-design.md`, §6). Byte-stability gate = the ship bar. Phase A (symbols) shipped; Phase C (the `/build-my-bible` navigator) follows. |
| 2026-06-04 | Plan | Hierarchical Customization — Phase A: Symbol Engine | `plans/2026-06-04-hierarchical-customize-phaseA-symbol-engine.md` | IN PROGRESS 2026-06-04 — per-coordinate note-symbol resolution (Bible→book→chapter→individual) + `enabled_note_ids` force-on; 8 TDD tasks; byte-stable (9 KJV identical = ship gate); ready to execute. Phase B (popups) + Phase C (`/build-my-bible` navigator) follow |
| 2026-06-03 | Plan | Monetization & Sustainability — donations / print / hosted service / grants | `plans/2026-06-03-monetization-and-sustainability-plan.md` | in progress — Phase 1 (support-the-mission links: PayPal/GitHub Sponsors/Ko-fi) being built by the Mac lane; Phases 2–4 roadmap sequenced by speed-to-cash (print-on-demand → hosted open-core builder → commissions+grants); **inviolable constraint: the Word/digital stays free — revenue only on convenience/artifacts/support** |
| 2026-06-03 | Plan | Website — the YHWH builder program's home page (yhwhyaway.com) | `plans/2026-06-03-website-plan.md` | in progress — **RE-SCOPED**: the site is the builder PROGRAM's home page, NOT a download portal (no EPUBs); manuscript-reverent look CHOSEN; Phase-1 prototype shell built (`website/index.html`+`style.css`), CONTENT needs rebuild to the program-homepage framing; showcase + get-the-code + example gallery; plain HTML/CSS + `build_site.py` → GitLab Pages → yhwhyaway.com |
| 2026-06-03 | Plan | Mac second-lane bring-up + next steps | `plans/2026-06-03-mac-second-lane-bringup.md` | ready — Mac (2017 iMac) provisioned as a full 2nd lane **with push** (SSH → GitLab+GitHub; Windows pulls+combines, doesn't push); toolchain DONE (uv Py3.14 · claude CLI · VS Code · **Tesseract via conda-forge** — Homebrew unsupported on macOS 13) + GAPS & OCR PDFs in & verified; captures the bring-up, the 3 Mac-made cross-platform fixes (committed from the Mac), and the GAPS-unblocked work (Windows owns P0 folio-mapping) |
| 2026-06-02 | Plan | Samuel/Kings Folio Index (P0) — complete the dual-witness manifests | `plans/2026-06-02-samkings-folio-index-p0-plan.md` | ready — P0 of the Sam/Kings cloud-draft spec; vision-data task (complete `manuscript/{samuel,kings}/manifest.yaml` for ~92 pending chapters); completeness-gate test + per-book folio-mapping batches; supervised on the N95 before pod spend |
| 2026-06-02 | Plan | mint-11 — Phased fixes plan (round-4 deep-audit) | `plans/2026-06-02-mint-11-fixes-plan.md` | IN PROGRESS 2026-06-02 — 30 survivors (13 med / 14 low / 3 info; NO high/crit); Phase 1 (6 stale tests) SHIPPED (200 green); Phases 0/2/3/4/5/6 + 2 empty-panel HIGH re-verifies remain |
| 2026-06-01 | Plan | mint-10 — Phased fixes plan (round-3 re-audit, recovered + continued) | `plans/2026-06-01-mint-10-fixes-plan.md` | IN PROGRESS 2026-06-01 — Phase-1 leftovers + Phases 2–6 SHIPPED; only 4 opt-tier items remain (#11 ρ.1 filter + #12 _resolve_popup_languages hoist [both build-path → byte gate] + #13 render_coverage EN + #6 candidates_written stat). Then mint-10 = the LAST audit round (STOP) |
| 2026-05-28 | Plan | Ge'ez Phase D1b — Patrologia Vision-Transcription Lane (Esther proof) Impleme… | `plans/2026-05-28-geez-patrologia-vision-plan.md` | in progress — PO Esther vision marathon paused at p28 |
| 2026-05-28 | Plan | Ge'ez Phase D — Own-Versification Re-ingest (HaCohen lane + Wisdom proof) Imp… | `plans/2026-05-28-geez-phase-d-reingest-plan.md` | in progress — Phase D own-versification re-ingest lane |
| 2026-05-27 | Plan | Ge'ez Own-Versification Collation & Standalone-Bible — Implementation Plan | `plans/2026-05-27-geez-own-versification-plan.md` | in progress — Phases A–C shipped; Phase D re-ingest ongoing |
| 2026-05-23 | Plan | Plan — LXX Greek (Swete) full ingest · Phase 2 spine, sub-phase 2 | `plans/2026-05-23-lxx-swete-ingest.md` | IN PROGRESS — reconstruction core DONE (committed as a WIP checkpoint); the versificati… |
| 2026-05-23 | Spec | Translation-spine arc — Douay / JPS / Vulgate / Arabic (Phase-2 finish) | `specs/2026-05-23-translation-spine-arc.md` | IN PROGRESS 2026-05-23 — **Arabic ✓ + JPS ✓ SHIPPED (baked + verified, UNCOMMITTED); Do… |
| 2026-05-17 | Plan | Kings Dual-Manuscript Collation & Render Implementation Plan (τ.6.x.4.c) | `plans/2026-05-17-kings-manuscript-collation.md` | in progress — LANE M dual-witness marathon, user-paced |

## Planned / design (22)

| Date | Type | Title | Path | Status |
|------|------|-------|------|--------|
| 2026-06-04 | Spec | Edition Cover + Truthful Front Matter (Holy Bible cover · "Your Edition" page · build-accurate counts/glossary · Ge'ez/Amharic default covers) | `specs/2026-06-04-edition-cover-and-truthful-front-matter-design.md` | APPROVED 2026-06-04 — brainstormed w/ visual companion; σ.1–σ.6 phasing; build-accurate counter honors the ρ.3 hierarchical choices. Next: writing-plans. |
| 2026-06-04 | Spec | Hierarchical Edition Customization — navigate-your-Bible (4-level × 2-dimension) | `specs/2026-06-04-hierarchical-edition-customization-design.md` | APPROVED 2026-06-04 — 4 levels (Bible→book→chapter→individual) × 2 dimensions (note symbols + translation popups); Tier-1 + individual-note already ship; Phase A plan written + executing; Phases B (popups) / C (`/build-my-bible`) follow |
| 2026-06-03 | Spec | Lane-Handoff Baton System — design | `specs/2026-06-03-lane-handoff-baton-system-design.md` | design — direction approved (baton / turn-based: holder = sole pusher + truth-record owner); no manual relay · nothing strands · shared task board |
| 2026-06-03 | Plan | Lane-Handoff Baton System — implementation plan | `plans/2026-06-03-lane-handoff-baton-system-plan.md` | COMPLETE — built + tested 2026-06-03 (core 8 tests, /handoff·/resume·/sync, SessionStart incoming-check win+mac); Mac adoption pending (set dev/.lane=mac + wire local hook) |
| 2026-06-02 | Spec | Tewahedo Re-Verification & Triaged Re-Ingest Program — design spec | `specs/2026-06-02-tewahedo-reverification-and-triaged-reingest-design.md` | design — direction approved (both tracks; sequencing A); shared substrate + Track-1 QA harness = P0; per-phase plans P0–P3 follow |
| 2026-05-27 | Spec | Ge'ez own-versification collation & standalone-Bible design | `specs/2026-05-27-geez-own-versification-design.md` | architecture approved (brainstormed + user-approved this session); implementation plan … |
| 2026-05-26 | Plan | Phase E — Clementine Latin Appendix (`man`/`1es`/`2es`) Implementation Plan | `plans/2026-05-26-phase-e-clementine-latin.md` | open — LANE T backlog (man / 1es / 2es appendix) |
| 2026-05-26 | Spec | Design — Phase E: Clementine Latin appendix (`man` / `1es` / `2es`) | `specs/2026-05-26-phase-e-clementine-latin-design.md` | awaiting user review |
| 2026-05-26 | Spec | Design — Surface Torrey in the EPUB Topical Index (Nave's + Torrey merge) | `specs/2026-05-26-torrey-topical-index-merge-design.md` | awaiting user review |
| 2026-05-24 | Spec | EPUB Presentation Polish — Configurable Reader Styling | `specs/2026-05-24-epub-presentation-polish-design.md` | Approved design (brainstorming complete; ready for implementation plan) |
| 2026-05-23 | Spec | Deep Audit & Forward Plan — design spec (2026-05-23) | `specs/2026-05-23-deep-audit-and-forward-plan-design.md` | approved (design) — proceeding to writing-plans. |
| 2026-05-23 | Spec | Douay-Rheims + Clementine Vulgate — table-driven versification ingest | `specs/2026-05-23-douay-vulgate-table-driven-design.md` | Design — approved (direction + scope), pending spec review |
| 2026-05-22 | Spec | Master Roadmap — The Fully-Customizable Bible Builder | `specs/2026-05-22-fully-customizable-builder-roadmap.md` | DRAFT — awaiting user review (then per-phase `writing-plans` → execute) |
| 2026-05-22 | Spec | Design — Per-edition themes + tradition-aware multi-translation verse popups | `specs/2026-05-22-themes-and-multitranslation-popups-design.md` | DRAFT — awaiting user review (then → writing-plans) |
| 2026-05-22 | Spec | Verse-Popup Regeneration — Design Spec | `specs/2026-05-22-verse-popup-regeneration-design.md` | approved (design), pending implementation plan |
| 2026-05-20 | Spec | NT Ge'ez source scope — Track E research spec (multi-track sweep 2026-05-20) | `specs/2026-05-20-nt-geez-source-scope.md` | SCOPING / RESEARCH. Sibling to |
| 2026-05-20 | Spec | Patrologia Orientalis ingest — design spec (audit U-belt 2026-05-20) | `specs/2026-05-20-patrologia-ingest-design.md` | DESIGN — implementation pending. Companion to |
| 2026-05-17 | Plan | Samuel Phase-2 — Dual-Manuscript Collation Tool — Implementation Plan | `plans/2026-05-17-samuel-phase2-collation-tool.md` | APPROVED & AUTHORIZED by the user at the τ.6.x.4.a-W widened-calibration gate (2026-05-… |
| 2026-05-16 | Plan | Samuel Widened-Calibration Plan (τ.6.x.4.a-W) — saved 2026-05-16 | `plans/2026-05-16-samuel-widened-calibration.md` | APPROVED & QUEUED by the user at the 1 Sam 1 gate (2026-05-16). This is the accepted **… |
| 2026-05-16 | Spec | Ge'ez colometric-merge — design spec | `specs/2026-05-16-geez-colometric-merge-design.md` | design approved (brainstorming), pre-implementation. |
| 2026-05-16 | Spec | Ge'ez external PD-source ingest — design spec | `specs/2026-05-16-geez-external-source-ingest-design.md` | design (brainstorming spec-review loop — revises the |
| 2026-05-16 | Spec | Samuel & Kings — dual-manuscript Ge'ez collation: design spec | `specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md` | DESIGN APPROVED (brainstorming complete; pre-implementation). |

## Shipped (18)

| Date | Type | Title | Path | Status |
|------|------|-------|------|--------|
| 2026-05-31 | Plan | mint-8 — Deep audit (the convergence audit) + a reusable audit tool | `plans/2026-05-31-mint-8-audit-plan.md` | COMPLETE — `deep-audit.js` built + run (round 1: 106 agents, 57 verified findings); fixes shipped in batches 1–3; convergence loop continues as mint-9 |
| 2026-05-31 | Plan | mint-9 — Phased fixes plan (deep-audit round 2) | `plans/2026-05-31-mint-9-fixes-plan.md` | COMPLETE — all 6 phases shipped 2026-06-01 (`b1a39485`+); round-3 re-audit = mint-10 |
| 2026-05-31 | Plan | mint-8 — Phased fixes plan (round-1 audit) | `plans/2026-05-31-mint-8-fixes-plan.md` | COMPLETE — all batches 1–3 shipped (852ed8a4 / cf05d8e3 / 1ae94084); byte-gate PASSED; lint 28✓. H5 ex.py→exo + M8 compresslevel deferred-by-design |
| 2026-05-31 | Plan | mint-7 — Quality Pass (correctness · code-debt · security · tests/hygiene) | `plans/2026-05-31-mint-7-quality-pass.md` | COMPLETE — Phases A · C · B · D · E all shipped + synced 2026-05-31 |
| 2026-05-29 | Plan | YHWH v2.4 "Mint" Cleanup + Automated Guardrails — Implementation Plan | `plans/2026-05-29-mint-cleanup-and-guardrails.md` | COMPLETE — all Phases 0–6 shipped + synced 2026-05-31 (HEAD ad945f62) |
| 2026-05-28 | Plan | Ge'ez→English Back-Translation (1 Kings 6 Proof) Implementation Plan | `plans/2026-05-28-geez-en-backtranslation-plan.md` | shipped — EN core for Kings/Samuel (324 v) + all 151 Psalms |
| 2026-05-28 | Plan | Ge'ez→KJV Partial-Anchoring Cross-Reference Tool — Implementation Plan (Phase B) | `plans/2026-05-28-geez-kjv-xref-plan.md` | shipped — Ge'ez→KJV partial-anchoring xref tool (Phase B) |
| 2026-05-28 | Plan | Ge'ez Standalone-Bible Render Path (Phase C) — Implementation Plan | `plans/2026-05-28-geez-standalone-render-plan.md` | shipped — standalone render path (Phase C); 4-book proof EPUB |
| 2026-05-26 | Plan | Torrey Topical-Index Merge — Implementation Plan | `plans/2026-05-26-torrey-topical-index-merge.md` | shipped — Torrey topical index merged (full) |
| 2026-05-24 | Plan | EPUB Presentation Polish Implementation Plan | `plans/2026-05-24-epub-presentation-polish.md` | shipped — CSS + front-matter polish + configurable reader settings |
| 2026-05-23 | Plan | Deep Audit & Forward Plan — Implementation Plan | `plans/2026-05-23-deep-audit-and-forward-plan.md` | shipped — 8-agent audit synthesized; forward plan executed |
| 2026-05-23 | Plan | Douay-Rheims + Clementine Vulgate (table-driven) Implementation Plan | `plans/2026-05-23-douay-vulgate-table-driven.md` | shipped — Douay-Rheims + Clementine Vulgate ingested |
| 2026-05-22 | Plan | Per-Edition Themes Implementation Plan | `plans/2026-05-22-per-edition-themes.md` | shipped — per-edition theme CSS |
| 2026-05-22 | Plan | Plan B1 — Popup Multi-Version Model Refactor Implementation Plan | `plans/2026-05-22-popup-multiversion-model.md` | shipped — ordered multi-version popup model + registry |
| 2026-05-22 | Plan | Verse-Popup Regeneration Implementation Plan | `plans/2026-05-22-verse-popup-regeneration.md` | shipped — verse popups 24%→90.5% |
| 2026-05-21 | Plan | Inject-Tail Completion (base-HTML irregular-layout robustness) Implementation… | `plans/2026-05-21-inject-tail-completion.md` | shipped — inject coverage ~99.76% via the boundary-aware spill resolver |
| 2026-05-16 | Plan | Ge'ez External PD-Source Ingest Implementation Plan | `plans/2026-05-16-geez-external-source-ingest.md` | shipped — HaCohen path; Psalms own-versified (psa in the standalone) |
| 2026-05-16 | Plan | Samuel Calibration Gate (Phase 1) Implementation Plan | `plans/2026-05-16-samuel-calibration-gate.md` | shipped — 1 Sam 1 calibration GO (τ.6.x.4.a) |

## Superseded (4)

| Date | Type | Title | Path | Status |
|------|------|-------|------|--------|
| 2026-06-02 | Plan | Samuel/Kings Cloud Run — agent-path workflow + pilot + bounded run (P1–P4) | `plans/2026-06-02-samkings-cloud-agent-workflow-and-run-plan.md` | ⛔ DROPPED 2026-06-04 — VM/cloud approach tried (RunPod Samuel bulk FAILED) then dropped by the user; pod terminated; Sam/Kings stays on the local agent-path marathon |
| 2026-06-02 | Spec | Samuel/Kings Dual-Witness Draft-at-Scale on a Cloud Pod — design spec | `specs/2026-06-02-samkings-cloud-draft-at-scale-design.md` | ⛔ DROPPED 2026-06-04 — cloud-pod approach tried + failed + dropped by the user; pod terminated |
| 2026-05-17 | Plan | Samuel Phase-2 — Dual-Manuscript Collation Tool — Implementation Plan **v2** … | `plans/2026-05-17-samuel-phase2-collation-tool-v2.md` | superseded — by the 2026-05-27 own-versification re-architecture |
| 2026-05-17 | Spec | Samuel Phase-2 collation tool — SPEC REVISION (Task-5 premise correction) | `specs/2026-05-17-samuel-phase2-collation-spec-revision.md` | superseded — engine spec; replaced by the 2026-05-27 own-versification design |

