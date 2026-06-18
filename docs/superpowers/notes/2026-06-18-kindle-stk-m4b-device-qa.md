# Kindle STK device QA — post-scrub ethiopian-tewahedo m4b (2026-06-18)

**Status:** FAIL — major formatting / navigation on KFX after Send-to-Kindle.  
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

## Implication

M4b chapter-tail + `vn-link` anchor model is **not KFX-safe** on the consumer STK channel (regresses turn-84 `kindle_safe`-only UX). Fix belongs in `scripts/core/kindle_post.py` (`apply_kindle_m4b`) and/or a Kindle-specific notes presentation branch — **Mac lane**. Do **not** regen catalog kindle column on WIN until Mac re-proves STK taps.

## References

- Design: `docs/superpowers/notes/2026-06-18-m4b-kindle-fork-design.md`
- Prior phone QA: `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`
- Tracker: `dev/EREADERS.md` §Kindle