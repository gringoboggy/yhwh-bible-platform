# v1.0.0 device-QA remediation — 2026-06-28

Triggered by the user's three-reader QA round (Kobo + Apple + Kindle, with the
first **high-resolution** screenshots) on the freshly-staged v1.0.0 artifacts,
plus a content decision. This is the live tracker for closing the v1.0.0 gate.
**The tag is NOT cut until these are fixed, rebuilt, and re-QA'd.**

Screenshots: `OneDrive/Desktop/{kobo_img,apple_img,kindle_img}`.

## ★ Content change (user decision) — DONE in source, cascade pending
- **Remove all machine-authored "User" notes.** They carry no PD source; the user
  confirmed he wrote none. **1,364 notes removed** across 14 books (gen 450, 1en
  232, exo 102, num 77, deu 76, lev 75, 1sa 71, 2sa 63, 1ki 59, jos 53, 2ki 48,
  jdg 45, rut 12, 1ch 1) via `scripts/remove_user_notes.py` (AST line-range, self-
  verifying). **Source notes 91,712 → 90,348.** ruff-clean; zero "User" attributions
  remain (87 docstring examples are not notes).
- **COUNT SWEEP (user directive):** the new headline count must be true on **every
  edition × every platform (Kobo/Apple/Kindle/Play/everywhere) × every OS the app
  runs on**, in **all EPUB/OPF metadata**, the **auto-generated Guide-to-the-Notes +
  per-book counts**, AND every hard-coded surface — **website, README, social card,
  GitLab + GitHub repo descriptions + release notes**, SESSION_STATE corpus-truth.
  Most regenerate on rebuild; hard-coded ones swept by hand + verified. Shipped
  superset was 91,555 → confirm exact on rebuild (~90,191).

## Findings by reader

### CRITICAL (block the gate)
- **[Apple] Reading direction flips backwards.** After the TOC / study-notes guide,
  swiping forward pages *backwards* through the book; glitches hard right after the
  first TOC page. **Apple-only**, but affects every edition. Suspected `page-progression-direction`
  / a `dir="rtl"` leak from Hebrew/Arabic content into the spine/nav. ROOT-CAUSE TBD.
- **[Kindle] Note/translation links teleport to the wrong place → notes never show.**
  Every popup lands on the **last badge of its backmatter chunk**: Gen 1–3 → end of
  Gen 3; ch 4–26 → end of ch 26; ch 27–49 → end of ch 49; ch 50+ → last badge before
  Book 2. So no note or translation is ever reachable. The ranges = the Kindle
  backmatter file-split boundaries → anchors resolve to the spine FILE, not the note
  `id`. ROOT-CAUSE TBD.

### MEDIUM
- **[Apple + Kindle] Edition ID misplaced.** Apple: alone on its own 2nd page. Kindle:
  tacked onto the end of the "Study Notes Book Count" page, before the copyright page.
  Should sit with the copyright/colophon text.
- **[Kindle] Body text not justified** (Apple/Kobo are justified).
- **[Kindle] ToC chapter pills very tightly packed.**
- **[Kindle] Book title pages split across 2 pages** (was 3 — improvement; want 1).
- **[Kindle] Note badges distributed/formatted strangely.**

### LOW / cosmetic
- **[Kobo] Stray `·` (U+00B7) clutter** before every category heading, every source
  line, an orphan `·` above each note heading, and as `· · ·` / `°` / `»»»` separators
  in translation popups. **ROOT-CAUSED** (see below). User: remove all.
- **[Kobo] Badge spacing drift** in justified verse text; lone badge wraps to next line
  with a big gap. **ROOT-CAUSED** (see below).
- **[Kobo] Return-to-verse `1:1` button missing** on the first category (Historical/
  Cultural) for the first pages; present on later categories. (Workflow agent failed —
  re-investigate; lead = round-16 H2 `verse_anchored` / `_study_verse_return_link`.)
- **[Kobo] A few residual mid-verse line breaks** (WS1 leftovers; page breaks are FIXED).
- **[Kobo] Translation popups cluttered + Greek letter-spacing broken.** ★ Apple proves
  the underlying HTML is GOOD — on Apple the same popup renders clean (label + text per
  language, perfect Greek). So the `·`/`°`/`»»»` and the broken Greek are **Kobo-only
  artifacts of the WS3 eink separators + Kobo's CSS-blind "Footnote preview."** Fix =
  drop/rework the eink separators in the translation popup; verify Greek on the rebuilt kepub.

## Root causes captured (Kobo, from the parallel investigation workflow)
- **`·` clutter:** WS3 eink separators leaking out of verse-popups into backmatter +
  translation popups. Sites: `scripts/build_edition.py` 2645–2647 (`_VN_SEP_CAT_EINK` /
  `_VN_SEP_BYLINE_EINK` / `_VN_SEP_ITEM_EINK`), 3999–4010 (`_emit_cascade_sections`),
  2675 (`_KOBO_VNOTE_GAP` = `· · ·`), 2676–2684 (`_VNOTE_BR_BEFORE_P_RE` +
  `add_eink_vnote_preview_breaks`), 3817–3826, 4425–4434; `scripts/matter_pages.py`
  1044–1098. Fix: gate the WS3 separators OFF in the backmatter glossary (`is_backmatter`)
  and exclude `vnote-source-label` from the gap regex — both eink-gated, non-eink bytes
  unchanged.
- **Badge spacing:** verse paragraphs `text-align: justify` (`epub_working/stylesheet.css:379`);
  badges are inline `<a class="verse-notes-badge">` / `study-glossary-jump`
  (`build_edition.py:4456–4525`) joined by plain spaces, no nowrap. Fix: eink-gated CSS
  `display:inline-block; white-space:nowrap` on the badges + `.badge-trail` (non-eink untouched).

## 2026-06-28 (cont.) — Play round (4th reader) + GENERALIZED root causes

Play Books QA (navy `everywhere` EPUB, the M5 artifact). Verified by grepping the
**actual built** `index_split_*.html` (400 content files; the body lives in
`.html`, not `.xhtml` — earlier `--include=*.xhtml` saw only the 9 front/back
matter files). Findings:

- **The `·`/bullet in note "headings" is NOT eink-only — it is the SAME `vn-sep`
  system on every profile, glyph-swapped, leaking through CSS-blind POPUP
  renderers.** `build_edition.py:2631-2633` defines the non-eink separators
  `_VN_SEP_ITEM`=`•`, `_VN_SEP_CAT`=`¶`, `_VN_SEP_BYLINE`=`◦` (each lead-padded
  with U+2028); `2645-2647` the eink variants (all `·`). They are designed to be
  **hidden** by `_VN_SEP_HIDE_CSS` → `.vn-sep{display:none}` (2648-2652) and only
  surface in CSS-blind raw-text extractors. The built everywhere EPUB confirms:
  148× `¶` immediately before each `vn-cat-head`, `◦` before every
  `vnote-source-label`, 203× `•` before note items — all `display:none` in the
  main flow but **EXPOSED in Play's footnote popup** (same failure class as Kobo's
  Footnote overlay). So the user sees `¶`/`◦` on Play exactly where Kobo shows `·`.
  → Fix is cross-profile, not eink-gated: kill the visible glyph in the popup
  family on every profile; keep structure via block `<p>` (Play's popup honoured
  per-witness `<p>` line breaks in img 4 — the glyph is redundant there). Kobo's
  fully-flattened overlay is the only renderer that needs *any* visible mark;
  rework that one to the least-obtrusive device-proven form and re-QA.
- **Category headings themselves are CLEAN on everywhere** — `<span
  class="vn-cat-sym">⌂</span> Historical / Cultural`, zero `·` adjacent. The other
  134 222 middots in the Play build are LEGITIMATE: Greek *ano teleia* `·` inside
  the Septuagint text, and topical "appears under: A · B · C" / cross-ref verse
  lists. **Do not touch those.**
- **"Two badges" = note-collection SPLIT parts, not a second system.** Gen 1:1 →
  `vbadge-…-s1` (title "2 notes, part 1 of 2") + `vbadge-…-s2` ("12 notes, part 2
  of 2"): one verse's 14 notes split across two sibling popups, one badge each.
  The split exists for Kobo's limited popup buffer (Kobo r7 byte-aware split) and
  leaks onto Apple/Play/Kindle, which don't need it. Per verse the user also sees
  the verse-start `vn-link` (translation popup) — so a split verse shows vn-link +
  2 study badges. DECISION (user, 2026-06-28): **single merged badge** on
  Apple/Play/Kindle/computer; keep the split **Kobo-only** (eink). Separators:
  **clean, no marker** — drop every visible `¶`/`◦`/`•`/`·`; line structure from
  block `<p>` + surviving `<br>`/U+2028 only.
- **Stale-artifact note:** the staged Play EPUB (built 09:11, pre-removal) still
  carries `User original`/`User paraphrase` source labels — the rebuild drops them
  (confirms the User-notes removal + rebuild are both required).
- Play translation popup renders CLEAN (per-language `<p>` + redundant `◦`),
  like Apple → confirms the Greek/letter-spacing breakage is **Kobo-only**.
- Play open questions carried forward: Edition-ID on the study-count page (cross-
  platform); badge spacing drift (non-eink too → un-gate the nowrap CSS fix); bad
  page breaks; ToC expandable like Apple (Play keeps `<nav>` collapsed/stuck —
  reader limitation; attempt, don't block).

### Critical-fix sites CONFIRMED
- **Apple direction:** `epub_working/content.opf:92` `<spine toc="ncx">` →
  add `page-progression-direction="ltr"` (regen at `build_edition.py` preserves
  the spine tag verbatim → propagates to every edition). Base-invariant gate +
  golden re-baseline apply.
- **Kindle teleport:** matrix builds Kindle via `build_kindle.py` non-m4b path
  (`m4b=False`, :29) → notes stay inline+hidden with same-file `#frag` hrefs →
  Kindle resolves to the spine FILE = teleport to last badge. The **m4b** path
  (`make_kindle_m4b`) relocates notes to a real backmatter file with cross-file
  hrefs = true endnotes — which is the correct Kindle model ("no popups by
  design; notes become visible endnotes"). Fix = build Kindle with m4b + extend
  the relocate to translation `vnote-*` asides (currently only study `vnotes-*`).

## PROGRESS LOG (2026-06-28, live)

Code fixes applied so far (commit `3c46a46d` = batch 1; batch 2 pending commit):
- ✅ **Apple LTR direction** — `epub_working/content.opf:92` spine `page-progression-direction="ltr"`. (batch 1)
- ✅ **Single merged badge off-Kobo** — `build_edition.py` `split_cap` gated to eink (one badge per verse on Apple/Play/Kindle/computer; split stays Kobo-only). (batch 1)
- ✅ **Clean separators (no marker)** — `build_edition.py` `_VN_SEP_*` (non-eink → hidden U+2028 only; eink → bare `<br>`); `_KOBO_VNOTE_GAP=""`; comments updated. (batch 1)
- ✅ **Badge-spacing drift** — `epub_working/stylesheet.css` `.verse-notes-badge,.study-glossary-jump,.vn-link { display:inline-block; white-space:nowrap }` (un-gated; Kobo + Play). (batch 2)
- ✅ **Edition-ID relocation** — moved the `Edition ID + Build` line from the "Your Edition"/study-count page to the **copyright page** (`matter_pages.py render_copyright_page`, threaded `version` via `inject_copyright_page`; removed from `render_your_edition_page`). Reverses the 2026-06-09 move. (batch 2)
- 🔄 **Kindle teleport (CRITICAL)** — delegated to a focused agent: route the matrix Kindle cell through the m4b endnote-relocate path AND extend the relocate to translation `vnote-*` asides (keep all content). In progress.
- ⏸ **Kobo return-link missing (first category)** — DEFERRED to post-rebuild device re-QA. The return link IS emitted for *every* category (`build_edition.py:3949` via `_study_verse_return_link`), so the symptom is device-side (the first/largest category's bottom-anchored link likely scrolls off Kobo's footnote overlay), not a code miss. Diagnose on the rebuilt kepub; candidate fix = also place the link at the top of each category aside.
- ⏳ **Still to do before the rebuild:** residual mid-verse line breaks (WS1); Kindle layout polish (justification / ToC pills via `kindle_post._flatten_toc_pills` / title-page split — after the Kindle agent returns, same file); Play ToC expandable (attempt; likely a Play reader limitation).

Tests: the separator/badge-merge/edition-ID changes intentionally change build output → unit tests asserting the old glyphs/placement (`test_ws3_popup_separators`, `test_popup_split`, the matter-page tests) + the 9-KJV golden are updated together in the post-rebuild pass (step 5).

## Remediation sequence (one rebuild, not many)
1. ✅ Content: User notes removed (validate + commit).
2. Root-cause the 2 CRITICAL bugs (Apple direction, Kindle teleport) + finalize return-link / line-breaks / translation.
3. Apply ALL code fixes (eink-gated where Kobo-only; cross-platform where shared) — TDD/byte-aware.
4. **One** full rebuild of every edition × format.
5. Re-baseline the 9-KJV golden (note removal changes the badged/backmatter cells).
6. Count sweep — auto-counts via rebuild + hand-sweep the hard-coded surfaces; verify consistency.
7. Re-stage all device artifacts; user re-QA each reader.
8. Only then is the gate re-evaluated. **Do NOT cut the tag.**
