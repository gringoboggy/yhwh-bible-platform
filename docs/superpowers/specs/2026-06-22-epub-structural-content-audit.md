# Spec — EPUB structural + content audit (verse → chapter → book → out-of-book), every edition × every platform

**Status:** DRAFT 2026-06-22 — spec written; auditor (`dev/audit_book_structure.py`) build started. To be built + run on **Opus 4.8** next session (the round-10 deep-audit ran on Sonnet/Haiku and was abandoned). Covers verse (+2 markers) → chapter → book → out-of-book × every edition × every format.

**Created 2026-06-22** (user-directed during the Kobo device-QA session). **Thoroughness over speed** — "I don't care how long it takes."

## Goal
A systematic, repeatable audit of the **rendered** epub/kepub output that catches **redundancies, contradictions, and structural errors at every level**, run across **every edition × every platform/format we ship**. Distinct from the code/product deep-audit (`.claude/workflows/deep-audit.js`), which audits source code — **this audits the built BOOK output**.

## Levels — bottom-up; a level must be clean before the next, a book fully clean before the next book
1. **Verse** — the verse and its **two markers** (the verse-number marker + the note/popup badge):
   - both markers present where expected; the badge `href` resolves to an existing aside; **badge count == actual note count**; no duplicate / orphan markers or ids; verse text present and non-empty.
   - **redundancy:** no repeated category/kind headings within a verse's notes; no duplicated notes; no double-listed topic.
   - **contradiction:** the note's own verse ref matches where it sits; marker target == the verse it's on.
   *(CONFIRMED 2026-06-22: "the 2 markers" = the verse-number marker + the note badge.)*
2. **Chapter** — verses ascending, no gaps / duplicates; chapter heading present + correct; continuation correct; **no spurious line/page breaks mid-chapter** (e.g. the reported Gen 10:6→10:7 break); breaks present only where designed (chapter / book starts).
3. **Book** — chapters in order; book title page present + correct; no break errors; book marked green only when verse+chapter+break checks all pass.
4. **Out-of-book** — intros, ToC(s), front/back matter, the study-notes/glossary section, copyright, sources/acknowledgments: structure correct, no redundancy/contradiction, all internal links resolve, ToC entries match real targets.

## Check families
- **Redundancy:** repeated headings; duplicated notes/markers; the category-grouping redundancy (`note_group_by_category`); topic double-listing (`note_topic_dedup`); repeated front/back-matter blocks.
- **Contradiction:** badge count vs rendered note count; marker target vs actual location; heading vs content; ToC entry vs actual destination; per-edition canon vs books actually present.
- **Structural:** verse/chapter/book ordering; heading presence + correctness; **line/page-break correctness** (none spurious, none missing); id uniqueness; link/anchor resolution.

## Scope — every version/platform
- **Editions:** `ethiopian-tewahedo` (flagship) · `catholic-study` · `evangelical-reformed` · `eastern-orthodox` (+ the standalone Geʽez / Amharic Bibles when they ship).
- **Formats/platforms:** base `.epub` · Kobo `.kepub` · Kindle (Send-to-Kindle / m4b) · Apple / tablet · desktop-app epub. Each format's transforms can introduce platform-specific structure, so the audit runs **per (edition × format)**.

## Implementation
- A **deterministic Python audit script** — extend `dev/verify_kr2_build.py` (already checks noteref-resolve / dup-ids / ch-spilled-badges) into a full level-by-level structural pass. Deterministic = exhaustive, repeatable, zero token cost, OOM-safe (parsing built HTML is light).
- Parses each built epub/kepub's HTML; emits a **per (edition × format × book)** matrix of PASS/FAIL with `file:line` + the exact defect.
- The few **judgment-needing** redundancy/contradiction calls (where deterministic rules can't decide) escalate to a per-book LLM pass.
- A book is "green" only when verse + chapter + book + breaks + out-of-book all align.

## Sequencing
- **Build the script now** (light) while the code deep-audit runs.
- **Run** on the already-built epubs (`m3-kobo-v0.1.0`, base, …) — light parsing, no OOM.
- Triage → fix (folding in the in-flight note-redundancy + page-break + translation fixes) → re-run until **every (edition × format × book) is green**, then the out-of-book sweep.

## Relationship to existing gates
- `verify_kr2_build.py` = the seed (noteref/dup-id/badge subset). This spec is its superset.
- `deep-audit.js` = code/product (orthogonal — keep both).
- Findings that are content/source defects route to the normal fix flow; platform-transform defects route to the build pipeline.
