# Session state — current snapshot

> **➤➤➤ FRESH SESSION START HERE (🪟 WIN, turn 106).** `/resume` → `git pull` @ turn 106 → read **`WIN_INGEST.md`** on external drive (below). **Then:** fix **11 pytest reds** (list below) + `test_work_cache` → re-run `pytest -m "not slow"` → **Phase 3** (`build_edition.py` / `generate_verse_popups.py` / `config.py`). **Covers shipped (Mac turn 106):** 86× Midjourney + gradient (`midjourney_first`). **Pending WIN code:** `/covers` → built-in / upload / none only. Baton **windows**; mode=parallel.
>
> **External drive (copy Mac USB → `E:\`):** `YHWH-v2.4-releases/book-title-covers-midjourney-gradient-2026-06-16/` — `WIN_INGEST.md` · `SHA256SUMS.txt` · `composed/` (86 JPG) · `_midjourney_new20/` · `meta/`. Mac path: `/Volumes/MacHD2/YHWH-v2.4-releases/...`
>
> **Audit2 fix pass GREEN (Mac turn 106, @ `874a9e1c+`):** the 11 triaged reds + `test_persists_to_disk` all pass under `pytest -m "not slow and not done_gate"` (11/11 verified Mac). Fixes: `save_book_cover_jpeg` restore · standalone chapter count 165 · `prospect.candidate_to_dict` re-export · kindle_safe test fixture · `1ki:22` manifest status `calibrated`→`pending` (empty folios). **`test_every_chapter_has_both_witness_folios[kings]`** stays **done_gate** (P0 folio index — run only with `-m done_gate`). **WIN next:** Phase 3 (`build_edition.py` / `generate_verse_popups.py` / `config.py`). One job at a time.
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