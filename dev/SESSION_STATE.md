# Session state — current snapshot

> **➤➤➤ 2026-06-15 (🖥️ Mac, turn 91 — ★ KINDLE PHONE QA INGESTED + FRESH-SESSION PREP PUSHED).** User phone QA on M4 STK pack (`~/Desktop/YHWH-kindle-stk-qa/`, 01 navy + 05 scholarly): badge taps align to **chapter page-break anchors** (3:24→8:10→11:26…); translation badges inert; ToC cramped; reference tables OK. Doc: `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`. **Next Mac session:** Kindle presentation fork (M4b) — study → backmatter (mirror WIN K-R9c); per-verse translation trial; STK re-gate. M3 fan-out 41/45 at push. Pulled WIN `bc4af802`. Baton **windows** (truth_owner); mode=parallel. TRACKER-STATE active.
>
> **➤➤➤ 2026-06-15 (🪟 Windows, turn 93 — ★ K-R9b/c SHIPPED + QA KEPUB READY).** Round-9 crash root cause: 73 MB `index_split_900.html` (naive `</section>` on nested `vn-group`). **Shipped K-R9b:** `split_study_glossary_document` → 107 pieces, nested Study Notes ToC. **Shipped K-R9c:** per-category coloured study badges (glyph+hue) → navigate to matching glossary section (no `noteref`). QA build: `Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-15T135228Z.kepub.epub` — forensics + `verify_study_backmatter` PASS. **BLOCKED on user:** round-9 device taps (`docs/superpowers/notes/2026-06-15-kobo-round9-device-qa.md`). **Next fresh session:** toolchain/plugin audit plan (`docs/superpowers/plans/2026-06-15-toolchain-plugin-update-audit.md`). Baton **windows**; mode=parallel. TRACKER-STATE active.
>
> **➤➤➤ 2026-06-15 (🪟 Windows, turn 92 — ★ K-R8 INGESTED + K-R7-2e SHIPPED).** Round-8 device QA (`kobo_img/1–6.jpg`): K-R7-2d **structural pass** — mid-badges pop; s7/singleton **jump to correct inline note** (not chapter teleport); inline Commentary blocks visible (user loves layout, fears page count). **Shipped K-R7-2e:** default **popup mode** (DOM-order anchors CSS-hidden) vs opt-in `reader_eink_study_inline`; **K-R7-4b** eyebrow span split; font **deselect/re-select Cardo** doc. **Next gate:** rebuild QA kepub (popup default) → user re-tap + BOOKI check. **Mac:** M3 hold until popup-mode QA. Baton **windows** (truth_owner); mode=parallel. TRACKER-STATE active.
>

## Recent ships (full chronology: `dev/CHANGELOG.md`; rotated entries: `dev/archive/SESSION_STATE_archive.md`)

- **Mint-cleanup arc COMPLETE (LANE 0, Phases 0–6)** — anti-bloat lint guards · bootstrap slim · roadmap refresh · archive sweep · decommercialize (~5,300 LOC) · enforce gates (mypy + remote/CI) · **polish (mint-6: `/distribution` console · superpowers INDEX+lint · `audit_caches`→preflight · sonar/`/exec` scrub)**. Plan `docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md`.
- Standalone Ge'ez Bible — Phases A-C shipped (`scripts/build_standalone.py`; 4 books; epubcheck 0/0/0/0; the 9 KJV editions byte-stable).
- English back-translation of the Ge'ez — collated Kings/Samuel (324 v) + all 151 Psalms (`content/translations/geez-tewahedo-en/`).
- Phase D own-versification re-ingest — Patrologia vision-transcription lane; PO Esther paused ~p35 (see the top journal entries).

## Next

> **v1.0.0 RELEASE GATE (plan: `docs/superpowers/plans/2026-06-14-v1.0.0-release-plan.md`).** **Mac next:** Kindle presentation fork (M4b) per `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md` · finish M3 fan-out + handoff. **WIN:** Kobo round-9 user taps · toolchain audit · M3 attach after Kobo PASS. **User:** Kobo round-9 taps · Kindle STK re-test when M4b ships · Play phone QA. **No tag until plan §8 complete.**

## Inventory pointers

> `dev/MATRIX_MAP.md` = data-flow + base-HTML; `dev/REPO_MAP.md` = file/folder index; `dev/SESSION_PLAYBOOK.md` = lifecycle/gates; `dev/EREADERS.md` = the e-reader compatibility tracker (per-reader caps/quirks/QA — update every device round); `dev/TOOLCHAIN.md` = tool inventory. Popup versions: `scripts/core/popup_versions.py`. Standalone build: `scripts/build_standalone.py`. Manuscript engine: `scripts/core/manuscript_collation.py`. mint-6 surfaces: `scripts/api/distribution.py` + `scripts/templates/distribution.py` (`/distribution` console); `docs/superpowers/INDEX.md` (plans/specs index, guarded by `check_superpowers_coherence`).

## Conventions (unchanged)

Local commit via `save.cmd`/`save.ps1` (PowerShell). **Remote RESTORED 2026-05-30** — `origin` = GitLab + `github` = GitHub mirror (both `gringoboggy`, private); `git push` to both works. Tests: full interpreter path + `$env:PYTHONUTF8="1"`, one file at a time. "continue" ≠ "save". Scope frozen 2026-05-20 (consolidation phase).

## Console inventory (web.py UI surface, 21)

`APIHELP_HTML` · `AUDIT_HTML` · `AUDIT_LOG_HTML` · `BUILD_MY_BIBLE_HTML` · `BUILD_TRACKER_HTML` · `COMPARE_HTML` · `COVERS_HTML` · `CUSTOMIZE_HTML` · `DIFF_HTML` · `DISTRIBUTION_HTML` · `EXPORT_HTML` · `GREEK_HTML` · `HEBREW_HTML` · `HOME_HTML` · `INDEX_HTML` · `MATRIX_HTML` · `OPS_HTML` · `PREFLIGHT_HTML` · `PUBLISHER_HTML` · `SOURCES_HTML` · `WIZARD_HTML`. Roles since the idiot-proof IA: `HOME_HTML` = the reader-friendly landing at `/` + `/home`; `INDEX_HTML` = the maintainer note editor at `/notes` (+ legacy `/index.html`). Each cross-links to the others (lint_rules check 6.2).
