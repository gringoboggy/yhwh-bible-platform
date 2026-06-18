# Kindle STK device QA — post-scrub ethiopian-tewahedo m4b (2026-06-18)

**Status:** FAIL (2026-06-18) — **165347Z STK load FAIL**; **221232Z staged awaiting re-tap**.
**Devices:** Kindle for Mac (`com.amazon.Lassen`) + user phone — **same behaviour**.  
**Artifacts:** Both uploaded builds (incl. `…2026-06-18T143407Z-kindle-m4b.epub` and the prior m4b variant).  
**STK delivery:** PASS (titles arrived; poll `stk_poll_watch` PASS @ 16:23 UTC).  
**Structural gates:** PASS (`verify_kindle_safe` / `verify_kindle_m4b` / epubcheck) — gates do not catch KFX link resolution.

## Failures (user-confirmed)

1. **Book title pages** (e.g. Genesis BOOK I) split across **3 pages**.
2. **Chapter-tail study notes** (M4b layout) appear **between chapters** — Kobo-like styling is OK visually, but:
   - No **chapter:verse** label on each note block.
   - No **link back** to the source verse.
3. **`vn-link` / language markers** at verse **start** (no end-of-verse study badges on KFX):
   - Tapping **1:1** does **not** open translation text — **teleports** to nearest study-notes page.
   - Pattern: Gen **1:1** → page before **ch4** notes; markers track forward to notes before **ch8**, **ch11**, etc.
4. **In-EPUB TOC** (not reader-native): chapter number links **too crowded**.

## STK load failure — 165347Z (2026-06-18)

**Symptom:** Send-to-Kindle upload of `…165347Z-kindle-m4b.epub` **failed to load** on Kindle for Mac + phone. Prior builds `…220354Z` and `…143407Z` **delivered** (tap QA failed only).

**Root cause:** Turn-130 fix inlined **1,781** `vnote-*` translation asides directly into scripture paragraphs (+2.7 MB HTML). Structural gates green; KFX conversion rejected the package.

## Fix (Mac turn 131 — revised)

| Failure | Fix |
|---|---|
| `vn-link` teleports to study notes | Expose `vnote-*` in visible per-chapter `kindle-chapter-translations` tail blocks (same file); strip hidden `verse-refs-section` — **no inline hoisting** (`m4b-5` gate) |
| Study notes lack coord/back-link | `vn-back` → `#v-{book}-{ch}-{v}` + `<strong>{ch}:{v}</strong>` on each relocated `vnotes-*` aside |
| All study blocks at file tail | Inject `kindle-chapter-study` at end of each chapter (before next `ch-anchor`) |
| Title page 3-page split | `apply_kindle_m4b_css`: drop forced `page-break-after` on `.book-title-page`; relax frame `break-inside` |
| ToC pills crowded | `toc-chapter-row a { margin: 0 0.35em; display: inline-block; }` |

**Gates (221232Z):** `tests/test_kindle_m4b.py` 17/17 · `verify_kindle_m4b` PASS · **epubcheck 0/0/0/0** · `M4B=1 gate.sh` PASS · 0 inline vnotes in prose · 1600 `kindle-chapter-translations` blocks.

**Also fixed:** multi-chapter study/vnote injection recomputes anchor positions each pass (prevents `vnotes-1en-13-8-s1` orphan on Strategy-B spill files).

**Staged for STK:** `~/Desktop/YHWH-reader-sim/kindle/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_2026-06-18T221232Z-kindle-m4b.epub`

**Follow-up fixes (prior arc):** injection snap outside `verse-p` · Strategy-B back-links → `#ch-b*-c*` when no `#v-*` anchor.

## Implication

Do **not** regen catalog kindle column on WIN until Mac STK device **re-PASS** on fresh ethiopian m4b upload.

## References

- Design: `docs/superpowers/notes/2026-06-18-m4b-kindle-fork-design.md`
- Prior phone QA: `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`
- Tracker: `dev/EREADERS.md` §Kindle