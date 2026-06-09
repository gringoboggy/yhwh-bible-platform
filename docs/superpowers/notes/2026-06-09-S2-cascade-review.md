# S2 cascade impl — adversarial review (Mac → WIN, turn 44 item 1)

_Mac lane, 2026-06-09. Adversarial review of WIN's note-rehaul **S2 cascade** (`90ac7dc9` / `a1a27b49`) against the Mac-authored spec `2026-06-08-note-presentation-rehaul-design.md`, run as a 6-dimension workflow (`wf_2cd615c5-726`): each finding independently refuted by a second agent; the suite run live. **This is the gate before WIN flips the eth flags `True` and re-baselines — fix the 🔴 cluster first.**_

## Verdict
**The cascade FOUNDATION is correct and safe to bake — but one root defect ships a visible attribution bug in the eth Bible.** Confirmed-good (do not touch): the §2 markup matches element-for-element; the robust-layer CSS matches §2 property-for-property; all **15 group-spine hues + 15 header glyphs** are exact; wiring is byte-safe + correctly gated (off editions byte-identical); a 2nd `apply_badge_markers` pass is a byte no-op; the unattributed-bucket merge is lossless; **`pytest tests/test_note_rehaul.py` = 36 passed, 0 failed** (S1 14 + S2 22). The flag-OFF path is empirically SHA256-identical to pre-S2 — the 9-KJV invariant holds.

**7 findings confirmed, 7 refuted.** The confirmed set reduces to **ONE root cause + two regex fragilities it un-hides + three low/robustness items.**

---

## 🔴 FIX BEFORE THE ETH RE-BASELINE — the root cause

### SK-1 / BYLINE-1 (HIGH) — comm-ethiopian self-attribution detection is DEAD on baked HTML
`_SELF_ATTRIBUTING_BODY_PREFIX = '<aside class="note-comm-ethiopian">'` (`build_edition.py:1930`) is matched against the **rendered row** at `:2360` (S2 group-byline suppress) and `:1987` (S1 in-body self-attribution suppress). The marker is genuinely present in the **STORED** tuple bodies (`content/notes/*.py`, 1579/1589 — the comment at `:1924-1929` is correct; the "comment is wrong" finding was **refuted**). **But `apply_badge_markers` reads the BAKED HTML** (`epub_working/`, copied into the temp tree), and the bake **strips the inner `<aside>`** — root-caused at the sanitizer: `scripts/core/html_sanitize.py` `ALLOWED_TAGS` (`:73-136`) does **not** include `aside`, and `aside` is not in `TAGS_DROP_CONTENT`, so `handle_starttag` drops the tag and keeps the text. → the marker never appears in `row` → **`suppress_byline` is always `False`.**

**Two consequences, both shipping in the eth bake as-is:**
1. **Double-attribution** — the comm-ethiopian group byline prints AND the father's name shows in the body (the exact spec §9 concern, now confirmed on shipped data).
2. **It un-hides the ragged bylines below (SK-2 / POLISH-1).** Those ragged `_source_display` strings are **all on comm-ethiopian sources**, which were *supposed* to be byline-suppressed — so the regex raggedness was meant to be invisible. With suppression dead, **the ragged bylines render.** (The test-phase agent initially downgraded SK-2/POLISH-1 by assuming suppression works — that assumption is exactly what BYLINE-1 refutes, so the downgrade does not hold. The findings are **coupled**.)

**Fix** (`build_edition.py:1950-1953` / `:1987` / `:2360`): detect self-attribution against the **BAKED row structure**, not the stored `<aside>` prefix. The father byline survives the bake as `<strong>…</strong> <em>…</em> <small>(…)</small>` immediately after the (optional) note-label span and before the first body `<p>`. Match that shape (or have the bake preserve a stable marker class on the surviving element). **Add a test that feeds a real BAKED comm-ethiopian row** (not a synthetic body carrying the raw `<aside>` — the current green tests use synthetic markers, which is why this slipped; that "tests are synthetic" sub-finding was itself refuted as overstated, but the lesson stands: pin against baked structure).

> **Fix-order payoff:** fixing BYLINE-1 *first* stops the double-attribution **and** re-suppresses the comm-ethiopian bylines, which makes SK-2 / POLISH-1 invisible again. So this one fix collapses most of the visible blast radius.

---

## 🟠 FIX WITH IT — regex fragilities (real bugs; blast radius coupled to BYLINE-1)

### SK-2 (HIGH→ regex bug; visible today via BYLINE-1) — `_SOURCE_LOCATOR_RE` over-strips, leaves a dangling `Bk`
`_SOURCE_LOCATOR_RE = r"\s+[IVXLC]+\.\d+\s*$"` (`:2034`) strips `I.11` but leaves the structural word `Bk`: `_source_display('Cyril of Alexandria, Commentary on John, Bk I.11 (NPNF S2 V14). PD.')` → `'Cyril of Alexandria, Commentary on John, Bk'`. **116 such bylines in eth `jhn`**, merging 11 distinct books under one ungrammatical byline. (These are comm-ethiopian → suppressed once BYLINE-1 is fixed, but the regex is still wrong for any non-suppressed source.)
**Fix** `:2034`: absorb a preceding `Bk|Book|Hom\.?|Homily` in the same strip, e.g. `(?:,?\s*(?:Bk|Book|Hom\.?|Homily)\s+)?[IVXLC]+\.\d+\s*$`, then re-trim edges.

### POLISH-1 (MEDIUM) — single-pass series-strip leaves a dangling `NPNF Series N`
`_SOURCE_SERIES_RE.sub` runs once (`:2055`). For `'…on 6:4-9. NPNF Series 2, vol. 13. PD.'` the boilerplate cut leaves `…NPNF Series 2, vol. 13`; the anchored series regex then strips only `vol. 13`, leaving `NPNF Series 2`. **Fix** `:2055`: loop the series-strip to a fixpoint (`for _ in range(2): s = _SOURCE_SERIES_RE.sub("", s)`) or run it after a leading-NPNF strip.

### BYLINE-4 (note for the BYLINE-1 fix) — use `all()`, not `any()`
`_emit_cascade_sections` suppresses the group byline via `any(rr.suppress_byline for rr in src_rows)` (`:2130`). Latent today (no row sets the flag). When you fix BYLINE-1, change to **`suppress = src_rows and all(rr.get("suppress_byline") for rr in src_rows)`** so a rare mixed source bucket can never hide a co-bucketed *non*-self-attributing row's byline.

---

## 🟡 LOW / robustness (not bake-blocking; fold in or document)

- **S2-GUARD-1** (`:2364-2372`) — the spec §4 headline guard (`DISTINCT_OUT == DISTINCT_IN` over `(source_key, body_fingerprint)`) is **not implemented**; the shipped guard is the weaker per-verse leaf count, and `_body_fingerprint` (`:1997-2004`) is **dead code**. Either implement the set-based guard, or **document the downgrade** citing S2-GUARD-2's construction proof (below) so the spec and code agree.
- **S2-GUARD-2** (INFO, supports the above) — `_emit_cascade_sections` provably cannot drop/duplicate a row (`setdefault(...).append(r)` once per row `:2114`; emit once `:2133`), so leaf-count == n_show is a sound *construction proof* of conservation for the emission step. Cite it if you take the document-the-downgrade route.
- **S2-GUARD-3** (`:2367`) — `inner_rows_html.count('class="vn-item')` is a raw substring count over **unescaped stored note bodies**. Robust today (0 of 88 stores contain that literal) but a **latent false-FAIL that would HALT the eth build** if any future body ever contains `class="vn-item`. Harden to the wrapper token: `count('<div class="vn-item n')`.
- **SK-4** (`spec §3:163`) — the spec's "only 2 keys collapse >1 attribution" is **stale**: the live corpus now has **22** over-collapse keys (19 are comm-ethiopian, masked only by the *currently-broken* suppression; 3 render, of which 2 are the intended Strong's collapse). Update the count + the render-vs-suppressed split so the safety claim rests on "only 3 RENDERING keys collapse, all intended/lossless."

## ✅ Refuted (7) — do not act
S2-MARKUP-INFO-1 (no-byline-for-unattributed is correct, not a "—" bucket); **SK-3** (id-form cross-check PASSES 100% across Strategy A / B-bxx / B-id_prefix incl. non-empty suffixes — the `_note_attribution_index` keying is sound); CSS-INFO-1 (hues+glyphs all match); **BYLINE-2** (the "tests are synthetic so suppression untested" claim — overstated/false); **BYLINE-3** (the 1579/1589 comment is accurate, not contradicted); BYTE-1 / BYTE-3 (byte-safety + guard-can't-false-trip are positive verifications).

---

## Re-verify gate (before flipping the eth flags)
After the 🔴+🟠 fixes, build eth and **render, with backgrounds off (per the M2 matrix):** (a) a comm-ethiopian verse (e.g. an `exo`/`jhn` verse with patristic notes) — confirm **no double-attribution** and **no ragged `Bk`/`NPNF` byline**; (b) Gen 1:1 (`◈16`) — confirm the full cascade; (c) a `jhn` Cyril verse — confirm bylines are grammatical. Then the standard BAKE-AND-PROVE gate (inject → nested-anchor → ebible verify → epubcheck 0/0/0/0).

— Mac, turn 44 item 1. Items 2 (M2 QA matrix) + 4 (HOME AA colors) also delivered this milestone; 3 (STAGE-F copy) + 5 (dmg recipe) remain. Workflow: `wf_2cd615c5-726`.
