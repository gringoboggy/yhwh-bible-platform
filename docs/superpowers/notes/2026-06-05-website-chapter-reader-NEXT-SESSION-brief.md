# NEXT-SESSION BRIEF — plan the website chapter-reader ("the Bible on the website")

**Status:** PREP / not started. **The next session's job is to PLAN this, not build it.**
Produce a spec + phased implementation plan; do NOT write feature code yet (user-directed:
"plan to PLAN that next session"). Runs while the win lane finishes its audit side.

Cross-refs: memory `project_website_reader_and_versioning` · `project_website_launch` ·
`project_parallel_bible_two_standalone_bibles` · `feedback_sources_already_in_place` (the
never-over-claim guard) · `dev/CLAUDE_PROJECT_RULES.md` Guard #2.

---

## The vision (user's words, 2026-06-05)
Turn the Geʽez/Amharic **progress-page pills into a real reader**: make each pill (and,
later, each *chapter*) **clickable → open that chapter on the website** showing the **Geʽez +
literal English** side by side. Advance the page to **chapter-by-chapter progress**, and "each
new thing we do we add there." Net effect: *"we'll basically be building the Bible on the
website too."* — a free, in-browser, no-download way to read the scripture we've transcribed.

## Hard constraints (do not violate; bake into the plan)
1. **Honesty / never over-claim** (Guard #2, same discipline as the EN badge): a pill/chapter is
   **clickable ONLY where real transcribed verse content exists.** "Source in hand" (PDF only,
   nothing transcribed) stays non-clickable / "in progress." A reader page must never render a
   stub/empty chapter as if it were real.
2. **Static + dep-free.** The site is `website/build.mjs` → `dist/` on **GitHub Pages**
   (no server, no PHP). Reader pages must be generated at build time as static HTML.
   [[project_website_launch]] · [[reference_spaceship_hosting]] (not Spaceship).
3. **Plain, never gaudy.** Manuscript-reverent, factual register (user re-emphasized "never
   nothing gaudy"). Reuse the existing `style.css` shell.
4. **Don't touch the EPUB build / shipping editions.** The reader reads the SAME source data but
   is a separate static surface; keep it byte-disjoint from `build_edition.py`/`epub_working/`.
5. **Single source of truth.** Generate the reader from the same `content/translations/**`
   stores the EPUBs use — never a divergent copy of the text.

## Versioning (DECIDED 2026-06-05 — don't re-litigate)
Two tracks: **app semver** (`v1.0.0-beta.1` → 1.0 when the *software* is glitch-free after human
testing) vs **content milestones** (Geʽez OT → Geʽez NT → Amharic OT → Amharic NT, four named
content releases on the roadmap/progress page). The reader is what makes the content milestones
*visible and navigable*. (Full detail in memory `project_website_reader_and_versioning`.)

---

## What the planning session must investigate FIRST (recon before the plan)
1. **Content coverage inventory — the gating fact.** Exactly which books/chapters have real
   Geʽez transcription AND literal-English back-translation, and how complete. Known so far:
   **Psalms** (151 ch, ~complete EN) is the only ~done one; **Samuel/Kings** partial (marathon);
   scattered own-vers. Walk `content/translations/` (geez-tewahedo, geez-tewahedo-en,
   amharic-tewahedo, geez-tewahedo-en collations) + the EN back-translation dirs. Quantify
   per-chapter verse coverage vs `canonical_verse_counts`. This determines what is clickable on
   day one (likely: Psalms + parts of Sam/Kings).
2. **The progress generator.** `scripts/gen_website_progress.py` already computes per-book status
   + the EN gate (≥50 real verse rows). Plan how to extend it to **per-chapter** coverage + emit
   the reader pages + wire the pill/cell links. Output feeds `website/src/data/`.
3. **The static reader build.** How `website/build.mjs` assembles pages (partials/head/foot →
   dist). Decide the reader-page generation path: a generator that emits e.g.
   `read/geez/psa/1.html` per available chapter, plus a book-landing + chapter-list.
4. **Fonts/rendering.** Noto Serif Ethiopic is already embedded for the EPUBs; confirm the web
   font + Geʽez (Ethiopic) rendering story for the site (the site already ships fonts).

## Open questions to RESOLVE in the planning session (turn into decisions)
- **Layout:** parallel two-column (Geʽez | literal English) vs interlinear vs a toggle? Verse
  numbering. RTL/LTR (Geʽez is LTR). Mobile.
- **Languages shown:** Geʽez + literal-English only (matches the two-standalone-Bibles scope), or
  also Amharic where available? (See [[project_parallel_bible_two_standalone_bibles]].)
- **Click granularity:** pill → book landing → chapter list → chapter reader? Or pill → first
  available chapter directly? How chapters that aren't ready appear (greyed, labelled).
- **"Clickable" threshold:** what counts as enough to be readable (whole chapter? ≥N verses? the
  EN badge uses ≥50 verse rows per book — pick the chapter-level analogue).
- **Chapter-progress UI:** a per-book chapter heatmap (verse-rows ÷ canonical counts), each ready
  cell linking into the reader. Where it lives (the geez progress page vs a new page).
- **Scale/perf:** Psalms alone = 151 pages; full canon eventually ~1,189 chapters × language(s).
  Static-page count, nav, sitemap, build time, SEO.
- **Accessibility:** semantic markup, font sizing, screen-reader handling of parallel text.
- **Provenance/attribution:** each reader page should carry the same honest source/attribution
  the EPUBs do.

## Deliverable of the planning session
A spec (`docs/superpowers/specs/`) + a phased implementation plan
(`docs/superpowers/plans/`) for the chapter-reader: coverage inventory → generator design →
reader-page templates → chapter-progress UI → pill/cell wiring → deploy. Phase 1 should target
the **content that already exists** (Psalms first) so it ships real value immediately and grows
as transcription advances.

## Explicitly OUT of scope next session
- Building the feature (PLAN only). · Any EPUB-pipeline change. · The public flip / the release
  (still gated on the win+mac audit merge). · Re-deciding the versioning (already settled).

## Boot order for the next session
Read the bootstrap triad, then THIS brief, then memory `project_website_reader_and_versioning`,
`website/README.md`, `scripts/gen_website_progress.py`, and sample `content/translations/**`
(start with Psalms). Then produce the spec + plan. Baton: **mac** (or per the live handoff).
