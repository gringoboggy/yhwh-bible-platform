# In-flight work — current task tracker

<!-- TRACKER-STATE: active -->

> **▶ 🔄 2026-06-15 (🪟 Windows, turn 94 — K-R13–K-R15 + AUDIT ROUND 8 PREP).** Kobo round 13 **PASS**; shipped K-R14 (vnote preview gaps) + K-R15 (verse-line/page-break/empty-verse fixes). Round-15 kepub on `G:\` + Desktop (`…T230843Z`). **User:** spot-check round-15 (Gen 2:7 popup formatting · Gen 8:15 verse text on NEXT rebuild with translations fallback · no line/page breaks). **NEXT FRESH SESSION — DO NOT START IN THIS SESSION:** parallel **deep-audit round 8** (edition cross-bleed / matrix-vs-build / rx-surfaces). Protocol: `docs/superpowers/plans/2026-06-08-round6-split-audit-plan.md` + engine `.claude/workflows/deep-audit.js` — set `ROUND=8`, `NOW=2026-06-15`, `LANE=mac` on Mac / `LANE=win` on N95 (local only, never commit LANE flip). Mac dims (14): correctness · security · code-debt · cross-module · data-validity · dist-packaging · … Win dims (7): tests-run · byte-stability · rx-surfaces · popup-integrity · opt-build · … Mac pushes `lane-transfer/audit` with `findings-mac.json`; Win merges via `deep-audit-merge.js`. **FINDINGS-ONLY — no fixes until plan approved.** Deferred: EPUB colour polish (ToC/pills/matter pages). Baton **mac**; mode=parallel.
>
> **▶ 🔄 2026-06-15 (🖥️ Mac, turn 91 — KINDLE PHONE QA + NEXT-SESSION PREP).** Ingested user phone QA (STK pack 01/05; page-break anchor pattern; translation vs study split goal). Truth note: `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`. **Parallel Mac backlog:** Kindle presentation fork (M4b) — mirror Kobo K-R9 study-backmatter model; per-verse translation layout trial; STK phone re-test. M3 fan-out 41/45 → finish 45 + handoff when idle.
>
> **▶ 🔄 2026-06-15 (🪟 Windows, turn 92 — K-R8 INGESTED + K-R7-2e POPUP MODE).** Round-8 QA ingested (`docs/superpowers/notes/2026-06-15-kobo-round8-device-qa.md`). K-R7-2d confirmed; shipped K-R7-2e (hidden anchors default) + K-R7-4b eyebrow spans + font refresh docs. Pass → Mac re-fan M3 45 + catalog path. Baton **windows**; mode=parallel.
>

## Standalone status (unchanged)

> Phases A-C shipped (`build_standalone.py`, 4 books, epubcheck 0/0/0/0); EN back-translation done for collated Kings/Samuel + all 151 Psalms; Phase D (own-vers re-ingest) in progress via the Esther vision lane.

## Background backlog (never single-thread — RULES §2.5)

> When a lane frees, auto-pick the next: the mint-7 plan phases · CAM hi-res pre-pull · base-structured re-collation · geez→kjv xref anchoring · Phase-E Clementine (1es/2es) · doc-coherence currency · test-coverage growth · Phase-D source acquisition.