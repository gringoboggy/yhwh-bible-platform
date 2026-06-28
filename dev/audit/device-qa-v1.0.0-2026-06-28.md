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

## Remediation sequence (one rebuild, not many)
1. ✅ Content: User notes removed (validate + commit).
2. Root-cause the 2 CRITICAL bugs (Apple direction, Kindle teleport) + finalize return-link / line-breaks / translation.
3. Apply ALL code fixes (eink-gated where Kobo-only; cross-platform where shared) — TDD/byte-aware.
4. **One** full rebuild of every edition × format.
5. Re-baseline the 9-KJV golden (note removal changes the badged/backmatter cells).
6. Count sweep — auto-counts via rebuild + hand-sweep the hard-coded surfaces; verify consistency.
7. Re-stage all device artifacts; user re-QA each reader.
8. Only then is the gate re-evaluated. **Do NOT cut the tag.**
