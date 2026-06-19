# Kindle STK device QA — post-scrub ethiopian-tewahedo m4b (2026-06-18)

**Status:** FAIL (2026-06-18) — **232708Z layout FAIL** (device screenshots IMG_0469/0472/0473); **Option B rebuild staged** (`…2026-06-19T000000Z-kindle-m4b.epub`).
**Devices:** Kindle for Mac (`com.amazon.Lassen`) + user phone — **same behaviour**.  
**Artifacts:** Both uploaded builds (incl. `…2026-06-18T143407Z-kindle-m4b.epub` and the prior m4b variant).  
**STK delivery:** PASS (titles arrived; poll `stk_poll_watch` PASS @ 16:23 UTC).  
**Structural gates:** PASS (`verify_kindle_safe` / `verify_kindle_m4b` / epubcheck) — gates do not catch KFX link resolution.

## Failures (user-confirmed)

### 232708Z device screenshots (2026-06-18 — IMG_0469 / 0472 / 0473)

Artifact: `…2026-06-18T232708Z-kindle-m4b.epub` (Option A per-chapter injection). STK **load PASS**, layout **FAIL**.

| Screenshot | What it shows | Root cause (pipeline audit) |
|---|---|---|
| **IMG_0472** | Left page blank except chapter numeral **1**; right page opens with **"Study Notes — gen 1"** + Easton CREATION block + overlapping beige boxes; blue **"Back to 1885"** floater | `_snap_study_injection_pos` injects study block at **first** `verse-p-flush` in chapter (only 2 `<p` tags before ch2 anchor in a 150 KB flush paragraph) → notes render **before** scripture |
| **IMG_0473** | Gen **1:9**: cross-ref + topical study panels **left of** verse text; scripture **fragmented** on right; **"Back to 1885"** popup mid-page (Location 1565) | Same per-chapter injection + KFX cannot paginate inlined study HTML inside scripture spine pieces; `vn-back` / `noteref` resolves to wrong offset |
| **IMG_0469** | In-EPUB ToC (Revelation + 1 Clement chapter pills) with a **Genesis 2** study note (Eve/helper) floating bottom-right | Study HTML spliced into shared spine files that also carry ToC / book-title frames — KFX anchor map treats footnote-like blocks as valid jump targets from unrelated ToC links |

**User-visible summary:** no study **badges** (Option A removed them); chapters start with notes or are incomplete bits; ToC non-pill items and `vn-link` taps teleport ahead to the next injected block. **"Back to 1885"** is KFX mangling `vn-back` / source-year text (TSK 1885) when the back-link target is wrong.

### Prior failures (still on record)

1. **Book title pages** (e.g. Genesis BOOK I) split across **3 pages**.
2. **Chapter-tail study notes** (retired Option A) — wrong placement, not back-of-book.
3. **`vn-link` / translation markers** — tap teleports instead of popup (hidden-tail `vnote-*` shape; separate arc from study layout).
4. **In-EPUB TOC** — non-pill links land on random study blocks (IMG_0469).

## STK load failures — 165347Z + 221232Z (2026-06-18)

**Symptom:** Send-to-Kindle uploads **failed to load** on Kindle for Mac + phone. Prior builds `…220354Z` and `…143407Z` **delivered** (tap QA failed only).

| Build | vnote layout | Result |
|---|---|---|
| `143407Z` | hidden tail (`notes-section`) | **STK delivery PASS** |
| `165347Z` | 1,781 inline after verse-p | **STK load FAIL** |
| `221232Z` | 1,600 `kindle-chapter-translations` blocks (unhidden) | **STK load FAIL** |

**Root cause:** Any relocation/unhide of translation `vnote-*` popups breaks KFX load. The proven STK shape leaves them in hidden tail sections (pre-turn-130 behavior).

## Fix (Mac — Option B pivot, 2026-06-19)

**Decision:** abandon Option A (`kindle-chapter-study` per-chapter injection). Ship **Option B** — Kobo K-R9 mirror: study glossary backmatter + **keep** `verse-notes-badge` markers retargeted to `kindle_study_glossary_*.html#vnotes-…`.

| Failure | Fix |
|---|---|
| Notes at chapter start / fragmented chapters (IMG_0472/0473) | **Remove** per-chapter injection; extract `vnotes-*` into `kindle_study_glossary` spine (156 pieces on ethiopian) |
| No badges (232708Z) | **Keep** `verse-notes-badge`; retarget `href` to glossary fragment |
| ToC teleport (IMG_0469) | Study content no longer inlined in scripture/ToC spine files |
| `vn-link` translation teleport | **Unchanged** — hidden-tail `vnote-*` only (STK-deliverable); separate device arc |
| Title page 3-page split | `apply_kindle_m4b_css` (retained) |
| ToC pills crowded | `_flatten_toc_pills` + `toc-chapter-row` margin (retained) |

**Staged rebuild:** `~/Desktop/YHWH-reader-sim/kindle/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_2026-06-19T000000Z-kindle-m4b.epub`  
**Gates:** `tests/test_kindle_m4b.py` 13/13 · `verify_kindle_m4b` 0 fail · Gen 1 opens with scripture · 30,344 badges → glossary · 0 `kindle-chapter-study`.

## Implication

Do **not** regen catalog kindle column on WIN until Mac STK device **re-PASS** on fresh ethiopian m4b upload.

## References

- Design: `docs/superpowers/notes/2026-06-18-m4b-kindle-fork-design.md`
- Prior phone QA: `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md`
- Tracker: `dev/EREADERS.md` §Kindle