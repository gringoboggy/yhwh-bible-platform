# Kobo device-QA round 3 — 2026-06-10 (user, 11 screenshots) — FINDINGS

Artifact tested: `G:\YHWH-Ethiopian-Bible-koboQA-r3.kepub.epub` (34.6 MB, the
turn-61 `kr2c` build with the full K-R2 arc). Source images:
`C:\Users\bogda\OneDrive\Desktop\kobo_img\kobo1–11.jpg`. User verdict:
**"OMG BIG WIN — maybe 4-5 fixes needed now"**. Catalog = K-R3-#.

## ✅ CONFIRMED FIXED (round-2 closes)
- **K-R2-1 title bleed GONE** — kobo3: the Genesis title page (art + BOOK I +
  title) owns its page completely; "formatting title pages is great now! no
  more bleed. the chapters follow each other nicely."
- **K-R2-4 numerals CENTERED** — kobo2/8: the chapter "2" sits centered
  mid-flow; no stranded numerals observed.
- **The ToC-jump symptom is GONE** (the piece isolation worked — see K-R3-1
  for what remains of that badge).
- **Original scripts RENDER in the Footnote preview** — kobo1/7 show real
  Hebrew + Greek + Arabic glyphs (no tofu). NOTE: confirm with the user which
  reading font was active (Cardo from `G:\fonts`?) — this is the font-pack
  ship-gate datum and it LOOKS like a pass.

## K-R3-1 (HIGH) — Gen 1:1 ◈15 still does not open (no longer mis-navigates)
The round-2 ToC-jump is gone, but the badge still doesn't pop. Gen 1:1's
merged aside is the piece's largest (23 KB, 15 notes). Hypotheses, in order:
(a) Kobo declines oversized/complex asides for the preview — find the size
threshold by comparing the largest aside that DOES pop; (b) its aside got
cross-piece-promoted (see K-R3-4 — same mechanism, silent flavor).
Repro next session: locate `vnotes-gen-1-1` in the r3 kepub; check whether
its badge href is bare (`#vnotes-gen-1-1`) or promoted (`piece.html#…`).

## K-R3-2 (HIGH) — popup content renders as ONE run-on line; Greek letter-spreads
kobo1/5/6/7: the Footnote-preview dialog flattens our aside's block structure
(`section.vn-group` / `.vn-cat-head` / `.vn-source` / `.vn-item` all flow as
one continuous paragraph — bylines, category labels and note bodies run
together). Separately, the Greek (LXX) text spreads out with visible gaps
between letters/words (kobo7).
- Fix direction (research + experiment): determine WHAT the Kobo preview
  preserves (plain `<p>`? `<br/>`? list items?) and emit those separators in
  the aside markup (build-time, option-safe, harmless on conformant readers
  where the CSS blocks already render). Likely shape: a `<br/>`/`<p>`
  boundary per `.vn-item` + per `.vn-cat-head`.
- Greek spreading: inspect the LXX house markup (`<em>`-per-word) + any
  letter-spacing CSS on `.vnote-greek` under the koboSpan transform.
- The in-book "See more" view presumably renders the full cascade correctly
  (it is the real page) — verify while in there.

## K-R3-3 (MED) — end-of-chapter notes spill into the next chapter's start
User: "a lot of the notes at the end of chapters spill over to beginning of
next chapter from last verse of previous chapter." Likely the same seam
mechanism as K-R3-4 (asides/badges hugging the piece boundary) — diagnose
together.

## K-R3-4 (HIGH) — repeated badge clusters + "teleport to chapter 1 start" (the DEEP SWEEP)
kobo8 (Gen 2 start): a cluster of number+badge pairs renders BEFORE Gen 2:1's
text, and the user reports "in chapter 2 a whole bunch of them repeat; the
first 5 for first verse of chapter 2 teleports me to chapter 1 start."
**Mechanism hypothesis (fits everything):** at piece seams the first-
referencer-wins aside attribution put some ch-2 verses' merged asides in the
PREVIOUS (ch-1) piece; the splitter then legally promoted those bare badge
hrefs to cross-file links — and a cross-file noteref NAVIGATES on Kobo
instead of popping → "teleport to chapter 1 start". The repeats may be the
same seam verses' badges/anchors surviving on both sides of a pop.
**The user's ask is exactly right: a deep sweep that everything points at the
same place.** Next session:
1. Extend `dev/verify_kr2_build.py`: (a) global id-uniqueness across pieces
   (the synthetic tests pin it; the artifact gate does not yet); (b) count
   PROMOTED (cross-file) noteref hrefs — the popup contract requires ~0;
   every promoted badge href = a broken popup verse. Run on the r3 kepub.
2. Fix the splitter so a verse's badge + its merged aside are NEVER separated
   across a piece/pop boundary (attribution must follow the pops; consider
   attributing an aside to the piece holding its BADGE anchor id rather than
   first-referencer).
3. Re-run gates + rebuild → round 4.

## K-R3-5 (LOW/research) — the [+] "do you want to read" prompt on Prayer of Azariah
kobo10/11: the native ToC shows "[+]" on "The Prayer of Azariah …" and
tapping it raises a Kobo modal (Back / Read). That is Kobo's NESTED-nav
drill-down UI: a nav entry with CHILDREN gets [+] and a Read-the-parent
prompt. Why only Azariah has it: inspect the r3 nav.xhtml/ncx nesting around
the Daniel-appendix demotion (paz/sus/bel) — likely its entries got nested
under that navPoint.
**User's idea — can we USE this affordance deliberately?** Candidates to
evaluate (presentation-doctrine: builder options, not hardcoded):
- per-book chapter drill-down in the native ToC (`reader_native_toc_chapters`
  already enriches nav with chapter children — on Kobo that would mean every
  book gets [+] → tap → chapter list, with "Read" = book start. That might
  genuinely be BETTER navigation on Kobo than the flat book list);
- appendix grouping (Daniel + its three Greek additions as children);
- front/back-matter grouping (one "About this Bible" parent).
Research both: confirm the trigger markup + whether the modal wording is
fixed ("Read") or derived. If chapter drill-down looks good, offer it as an
edition option gated to the eink target (TARGET_CAPS).

## kobo9 note (observed, minor)
The Prayer-of-Azariah appendix heading renders as a near-empty standalone
page ("Continuation of Daniel with Greek Portions"). The forced splitting
isolates appendix headings like book titles. Acceptable (a clean separator
page) — but if round 4 wants it tighter, exempt non-bp appendix headings from
title-singleton treatment.

## ★ TURN-62 ROOT CAUSES (artifact-diagnosed — supersedes the hypotheses above)

**K-R3-4/K-R3-3 — NOT the splitter.** The r3 kepub has **0 promoted noterefs** and
**0 duplicated href-targeted ids** (the promotion hypothesis is refuted; the new
verifier gate-4 now pins both). The real mechanism: inject's spill resolver bakes
some of a chapter-last verse's xref/topic markers AFTER the next chapter's heading
(pre-existing in `epub_working/`, invisible as tiny numbered sups), and
`apply_badge_markers` placed the merged badge "at the LAST marker's position" —
past the heading. **264 instances** (gen 46, exo 34, num 32, deu 30, 1sa 25 …).
kobo8's cluster = `◈5`(gen 1:31, spilled) + `1` + `◈2`(gen 2:1) + `2`. FIXED:
the badge placement clamps to the verse's own text end (before its `</p>`) when
the region crosses a chapter boundary; spilled markers still merge into the aside
(collection unchanged). Pinned by
`test_chapter_last_verse_badge_stays_in_its_chapter` + verifier gate-4c.

**K-R3-1 + the "teleport" — Kobo preview-decline → navigate fallback.** Vendor
research (kobolabs/epub-spec + MobileRead, see the research report in this turn's
session): the eInk popup is a generic fragment-link heuristic — pops only when the
target's stripped text is ≥9 and ≤~5000 chars (community: possibly to-EOF);
otherwise the tap NAVIGATES. Our navigate target sits inside the `hidden=""`
notes-section ⇒ no rendered position ⇒ Kobo lands at FILE START — which for piece
000_02 is Gen 1:1 ("teleport to chapter 1 start"; at Gen 1:1 itself it looks like
"nothing happened" = K-R3-1). Sizes: gen-1-1 23.0KB (declines), gen-1-3 9.8KB
(POPS — kobo5/6), gen-1-31 6.3KB (declined — but its badge was the SPILLED one;
post-fix datum needed). Round 4 carries a named tap matrix to pin the threshold.
Keep `hidden=""` (eInk does NOT auto-hide asides — unhiding renders all notes
inline).

**K-R3-2 — the preview is a TAG-STRIPPED plain-text extraction** (vendor-doc'd);
no markup survives, so block separators can never render there. FIXED build-time:
plain-text separators baked into the merged aside (`.vn-sep` spans — ¶ before
category heads, ◦ before source bylines, • before each note row), hidden by CSS
everywhere CSS applies (real page; Apple Books popups). Greek letter-spreading:
likely the dialog's own full-justification of long lines — recheck on round 4.

**K-R3-5 — NOT nested nav.** The r3 nav.xhtml + toc.ncx are both FLAT (one entry
per book, distinct piece files); 047_04 is a pure 1.2KB title singleton. The
[+]/Read modal is almost certainly Kobo's TITLE-OVERFLOW expander — Azariah's is
the longest book name in the ToC (58 chars). The chapter-drill-down idea needs a
real nested-navPoint experiment (`reader_native_toc_chapters`) to evaluate — Mac.

**NEW pre-existing BASE finding (separate arc, NOT this round):** at **117
chapter starts** (psa 31, job 14, eze 6, gen 2/11/32/37/43, …) the base has NO
verse text between the `v-{code}-{ch}-1` and `v-{code}-{ch}-2` vn-links — v1's
text sits after v2's anchor (gen 2: "1 2 The heavens…"), so the v2 number
visually labels v1's text and the v1/v2 translation popups pair off-by-one
against what the eye reads. Pre-existing bake artifact (1,318 chapter starts are
normal), shipped since v0.0.3. Fixing = a surgical base sweep (all editions
change) — needs its own verified arc; handed to the lane board.

## ROUND-4 USER TEST MATRIX (hand to the user with the r4 kepub)

1. **Gen 2 start (kobo8 retest):** the badge cluster before 2:1 should be GONE —
   Gen 1:31's ◈ now sits at the end of 1:31's text, before the big "2". Spot-check
   2-3 other chapter ends (Gen 4→5, Exo 19→20): no badges after a chapter numeral.
2. **Popup tap matrix (the preview-decline threshold — tap each, note POP /
   NOTHING / JUMP):** Gen 1:1 ◈ (23K — predict NOTHING/JUMP) · Gen 1:26 ◈ (20K —
   predict NOTHING/JUMP) · Gen 2:2 ◈ (19K — predict NOTHING/JUMP) · Gen 1:3 ◈
   (10K — popped in round 3, control) · Gen 1:31 ◈ (6K, now correctly placed —
   the KEY datum) · Gen 2:1 ◈ (3K — predict POP).
3. **Separators:** open any study popup — category/source/note rows should now be
   separated by ¶ ◦ • glyphs INSIDE the preview dialog (instead of one run-on
   line). On the real page (and in the in-book notes), the glyphs must be
   INVISIBLE.
4. **Greek spreading recheck (kobo7):** is the gappy Greek just full-width
   justification of short lines, or per-letter spacing? A photo of one line
   suffices.
5. **Which reading font was active during round 3's kobo1/7?** (Cardo from
   G:\fonts?) — the font-pack ship gate needs that datum.

## Next-session WIN sequence (proposed)
1. K-R3-4 deep sweep (verifier extensions: id-uniqueness + promoted-noteref
   count) → splitter fix (badge↔aside same-piece invariant) → this likely
   resolves K-R3-1 and K-R3-3 too.
2. K-R3-2 preview separators (+ Greek spacing inspect).
3. Rebuild + gates + kepub + `G:\` → round 4.
4. K-R3-5 nav-nesting research (Mac candidate).
Ask the user at round 4: which reading font was active during kobo1/7 (the
font-pack ship gate needs that datum).
