# Kindle STK device QA — post-scrub ethiopian-tewahedo m4b (2026-06-18)

**Status:** FAIL (2026-06-18) — **165347Z + 221232Z STK load FAIL**; **rebuild in flight** (revert vnote relocation).
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

## STK load failures — 165347Z + 221232Z (2026-06-18)

**Symptom:** Send-to-Kindle uploads **failed to load** on Kindle for Mac + phone. Prior builds `…220354Z` and `…143407Z` **delivered** (tap QA failed only).

| Build | vnote layout | Result |
|---|---|---|
| `143407Z` | hidden tail (`notes-section`) | **STK delivery PASS** |
| `165347Z` | 1,781 inline after verse-p | **STK load FAIL** |
| `221232Z` | 1,600 `kindle-chapter-translations` blocks (unhidden) | **STK load FAIL** |

**Root cause:** Any relocation/unhide of translation `vnote-*` popups breaks KFX load. The proven STK shape leaves them in hidden tail sections (pre-turn-130 behavior).

## Fix (Mac turn 131 — revised again)

| Failure | Fix |
|---|---|
| `vn-link` teleports to study notes | **Deferred** — restore hidden-tail vnotes for STK delivery first; tap fix is separate arc |
| STK load fail on vnote exposure | **Do not extract** `vnote-*` in `apply_kindle_m4b_html`; keep hidden tail only (`m4b-5` blocks inline hoisting) |
| Study notes lack coord/back-link | `vn-back` → `#v-{book}-{ch}-{v}` + `<strong>{ch}:{v}</strong>` on each relocated `vnotes-*` aside |
| All study blocks at file tail | Inject `kindle-chapter-study` at end of each chapter (before next `ch-anchor`) |
| Title page 3-page split | `apply_kindle_m4b_css`: drop forced `page-break-after` on `.book-title-page`; relax frame `break-inside` |
| ToC pills crowded | `toc-chapter-row a { margin: 0 0.35em; display: inline-block; }` |

**Gates (next build):** `tests/test_kindle_m4b.py` 16/16 · `m4b-5` no-inline guard · study injection recompute · hidden-tail vnotes preserved.

**Also fixed:** multi-chapter study injection recomputes anchor positions each pass (prevents `vnotes-1en-13-8-s1` orphan on Strategy-B spill files).

**Follow-up fixes (prior arc):** injection snap outside `verse-p` · Strategy-B back-links → `#ch-b*-c*` when no `#v-*` anchor.

## Implication

Do **not** regen catalog kindle column on WIN until Mac STK device **re-PASS** on fresh ethiopian m4b upload.

## References

- Design: `docs/superpowers/notes/2026-06-18-m4b-kindle-fork-design.md`
- Prior phone QA: `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`
- Tracker: `dev/EREADERS.md` §Kindle