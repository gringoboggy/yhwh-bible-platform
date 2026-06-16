# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🖥️ Mac, turn 107).** `/resume` → `git pull` @ turn 107. **Covers:** already in git (`midjourney_first` 86/86 @ turn 106) — WIN verified audit 0 missing + `ethiopian-tewahedo` 86-book `book_covers` wired. **▶ Mac:** (1) **Copy** `book-title-covers-midjourney-gradient-2026-06-16/` from MacHD2 → `E:\YHWH-v2.4-releases\` (WIN external mirror still missing — only v4-reimagine on E: today). (2) **Phase 4 disjoint:** phantom `1ma/2ma` purge · `ex`→`exo` alias · **1ki ch7–10 EN** · Windows artifact naming. (3) **M3 attach** 45 kepubs (`F:\…\m3-kobo-v0.1.0\`) → GitHub release + SHA256SUMS. **HOLD** `build_edition.py` until WIN Phase 3 green. Baton **mac**; mode=parallel.
>
> **➤➤➤ FRESH SESSION START HERE (🪟 WIN, turn 107).** `/resume` → `git pull` @ turn 107. **Covers ingest:** via git pull (audit 86/86 green); external MJ package on E: pending Mac copy. **pytest** turn-106 full rerun grinding → **Phase 3** on green (`build_edition.py` / `generate_verse_popups.py` / `config.py`). Parallel when idle: round-8 WIN 7-dim audit + `/covers` UX (built-in/upload/none). Baton **windows**; mode=parallel.
>
> **Audit2 fix pass GREEN (both lanes, @ `9eb0e917+`):** 11/11 under `not slow and not done_gate`; WIN rebased `b3e7b5af` (+ kings `1ki` 13–18 folio pre-stage). **`done_gate` kings folios** still intentional red (P0).
>
> **➤➤➤ 2026-06-16 (🖥️ Mac turn 106 — ★ MJ+GRADIENT SHIPPED + HANDOFF).** Policy reset: `_scenes/_midjourney/` + compose only; 20 Ethiopian extras; tests 9/9. Deprecated: alt04–06, Grok, ethnic variants.
>
> **➤➤➤ 2026-06-16 (🖥️ Mac, turn 98 — ★ ROUND-8b THOROUGH MAC AUDIT COMPLETE).** 35 survivors @ `b1b9dffd` on `lane-transfer/audit`. **WIN next:** 7 dims thorough + merge → `docs/superpowers/notes/2026-06-15-round8-split-audit-findings.md`.
>

## Recent ships (full chronology: `dev/CHANGELOG.md`; rotated entries: `dev/archive/SESSION_STATE_archive.md`)

- **Mint-cleanup arc COMPLETE (LANE 0, Phases 0–6)** — anti-bloat lint guards · bootstrap slim · roadmap refresh · archive sweep · decommercialize (~5,300 LOC) · enforce gates (mypy + remote/CI) · **polish (mint-6: `/distribution` console · superpowers INDEX+lint · `audit_caches`→preflight · sonar/`/exec` scrub)**. Plan `docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md`.
- Standalone Ge'ez Bible — Phases A-C shipped (`scripts/build_standalone.py`; 4 books; epubcheck 0/0/0/0; the 9 KJV editions byte-stable).
- English back-translation of the Ge'ez — collated Kings/Samuel (324 v) + all 151 Psalms (`content/translations/geez-tewahedo-en/`).
- Phase D own-versification re-ingest — Patrologia vision-transcription lane; PO Esther paused ~p35 (see the top journal entries).

## Next

> **v1.0.0 RELEASE GATE (plan: `docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`).** **Covers:** **86×1** Midjourney + gradient (turn 106); `/covers` UX simplification pending. **WIN:** fix 11 pytest reds → Phase 3 · round-8 7-dim audit + merge. **Device-QA ON HOLD** until audit+fixes. **M3:** 45/45 handoff done; attach waits post-audit. **No tag until plan §8 complete.**

## Inventory pointers

> `dev/MATRIX_MAP.md` = data-flow + base-HTML; `dev/REPO_MAP.md` = file/folder index; `dev/SESSION_PLAYBOOK.md` = lifecycle/gates; `dev/EREADERS.md` = the e-reader compatibility tracker (per-reader caps/quirks/QA — update every device round); `dev/TOOLCHAIN.md` = tool inventory. Popup versions: `scripts/core/popup_versions.py`. Standalone build: `scripts/build_standalone.py`. Manuscript engine: `scripts/core/manuscript_collation.py`. mint-6 surfaces: `scripts/api/distribution.py` + `scripts/templates/distribution.py` (`/distribution` console); `docs/superpowers/INDEX.md` (plans/specs index, guarded by `check_superpowers_coherence`).

## Conventions (unchanged)

Local commit via `save.cmd`/`save.ps1` (PowerShell). **Remote RESTORED 2026-05-30** — `origin` = GitLab + `github` = GitHub mirror (both `gringoboggy`, private); `git push` to both works. Tests: full interpreter path + `$env:PYTHONUTF8="1"`, one file at a time. "continue" ≠ "save". Scope frozen 2026-05-20 (consolidation phase).

## Console inventory (web.py UI surface, 21)

`APIHELP_HTML` · `AUDIT_HTML` · `AUDIT_LOG_HTML` · `BUILD_MY_BIBLE_HTML` · `BUILD_TRACKER_HTML` · `COMPARE_HTML` · `COVERS_HTML` · `CUSTOMIZE_HTML` · `DIFF_HTML` · `DISTRIBUTION_HTML` · `EXPORT_HTML` · `GREEK_HTML` · `HEBREW_HTML` · `HOME_HTML` · `INDEX_HTML` · `MATRIX_HTML` · `OPS_HTML` · `PREFLIGHT_HTML` · `PUBLISHER_HTML` · `SOURCES_HTML` · `WIZARD_HTML`. Roles since the idiot-proof IA: `HOME_HTML` = the reader-friendly landing at `/` + `/home`; `INDEX_HTML` = the maintainer note editor at `/notes` (+ legacy `/index.html`). Each cross-links to the others (lint_rules check 6.2).