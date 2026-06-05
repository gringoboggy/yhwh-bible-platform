# Auto-note re-ingest — execution plan (for a fresh session)

**Status:** READY TO EXECUTE. User-greenlit 2026-06-05; Mac holds the baton
(`LANE_HANDOFF` turn 14). Dry-run done; approach proven. This fixes the 5 ingest
defects the two content audits surfaced
([auto-note](2026-06-06-auto-note-quality-audit.md) +
[word-kind](2026-06-06-word-kind-audit.md)). **No content edited yet** — this is the
plan + the proven method.

## 0. Principle, gates, and the proven method

**Byte-minimal lockstep.** Each defect is a body rewrite. Apply it as an
**exact-string replacement in BOTH** `content/notes/*.py` (the SOURCE store) **and**
`epub_working/index_split_*.html` (the baked BASE), in lockstep — exactly the
pattern of `scripts/_strip_reviewer_scaffold.py` (RX Phase 1 changed 88,773 bodies
this way). Do NOT re-serialize the `.py` (ruff/ast churn) and do NOT do a full
`inject --all-books` re-bake (non-determinism risk). Touch only the changed bodies.

**Why exact-string replace is safe here:** a dict-easton/etc. body is written by
`promote.format_tuple_text.py_str` as a **double-quoted literal with no escaping**
for these bodies (the extractors strip `\` and convert `"`→`'`), so the body appears
**verbatim** between quotes in the `.py`, and verbatim in the base `.html`. The
dry-run confirmed: 0 of the dict-easton old bodies are missing from their source
`.py`.

**The ship bar (run after EVERY defect, before its commit):**
1. `check_nested_anchors --fix` → 0 (mandatory after any `epub_working` mutation —
   [[feedback_base_invariant_gating]]).
2. `categorize_diff` on the base → prove ONLY the targeted kind's bodies changed.
3. `ebible verify` paired-errors = 0.
4. Build **ethiopian-tewahedo** + **catholic-study**; **epubcheck 0/0/0/0** on both.
5. `ruff format` the changed `content/notes/*.py` ([[feedback_ruff_format_before_save]]),
   then lint (`scripts/lint_rules.py`) + `mypy` clean.
6. A regression guard per defect (see each) + a unit test.
7. Commit + push BOTH remotes per defect (small, reviewable commits). Mac is the sole
   pusher while it holds the baton.

**Pacing:** one defect per commit; check in after #1 (dict-easton) before the rest.
The build is slow on this HDD-bound Mac — budget minutes per `epubcheck`. Run tests
with `export TMPDIR=/Volumes/MacHD2/<dir>` and the venv python
(`.venv/bin/python`); `$env:PYTHONUTF8` is Windows-only.

**Staged dry-run assets (scratch, outside the repo):**
`/Volumes/MacHD2/wordkind-audit/easton_dryrun.py` (the analysis below) — reuse/adapt
it into the one-shot.

---

## 1. dict-easton — un-cap (FULL articles) + `_HEAD` glue fix  ★ DO FIRST

**Scale (dry-run, full population):** 3,779 dict-easton notes → **1,431 truncated**
(end with a literal `…`, exactly the audit) + **792 headword-glued** = **2,223 bodies
change**. Matching is clean: all 3,779 matched a source entry (0 unmatched, 0
ambiguous), every old body found verbatim in source `.py`. Base edge cases: **1** old
body not found in base, **4** found >1×.

**★ CAP DECISION (user, 2026-06-05): FULL ARTICLES — NO CAP.** Store the complete
Easton entry for every note. This honors "complete entry text" literally. The long
tail is real and must be made to work: full-body length is median 410, **p99 5,154,
max 42,535** (e.g. a JERUSALEM/MOSES-class entry). 61 entries exceed 4,000 chars.

### Root cause — `scripts/extract_eastons_ccel.py`
- **Truncation:** `MAX_BODY = 480`; lines 146–147 `if len(rest) > MAX_BODY: rest =
  rest[:MAX_BODY].rsplit(" ", 1)[0] + "…"` → severs mid-sentence + bakes a literal `…`.
- **Headword glue:** `_HEAD = re.compile(r"^([A-Z][A-Z0-9'’\-]*(?:\s+[A-Z0-9'’\-]+)*)")`
  — the continuation `\s+[A-Z0-9'’\-]+` greedily grabs the **single lead capital** of
  the next sentence-case word (`•FOREST Hebrews…` → head `"FOREST H"`, body
  `<strong>FOREST H</strong> ebrews…`).

### Permanent fix (the extractor — so future re-ingests are correct)
- **Drop the cap:** remove the `MAX_BODY` truncation in `build_notes` (store full
  `rest`). Keep the `re.sub(r"\s+", " ", …)` whitespace-normalise + the `\`-strip +
  `"`→`'` (they keep the tuple literal valid and the exact-match stable).
- **Fix `_HEAD`:** add a negative lookahead to the continuation:
  `r"^([A-Z][A-Z0-9'’\-]*(?:\s+[A-Z0-9'’\-]+(?![a-z]))*)"`.
  **Verified:** preserves genuine multi-word ALL-CAPS headwords (`BURNT OFFERING`,
  `SONG OF SOLOMON` — the continuation word is followed by space/EOL, not a lowercase
  letter), and only stops grabbing a lowercase word's lead cap. This is the sole
  difference between `_HEAD_OLD` and `_HEAD_NEW` in the dry-run, and it accounts for
  the 792 glue fixes.

### Re-ingest the existing notes (one-shot `scripts/_reingest_eastons.py`)
Model it on `_strip_reviewer_scaffold.py` (same lockstep, but a computed old→new
map instead of a regex). Algorithm (the dry-run already does steps 1–4):
1. Build `{(code,ch,v): [(head, full_new_body)]}` from `eastons_ccel_source.txt` via
   the FIXED `parse_entries`/`build_notes` (no cap, `_HEAD_NEW`). **640 coordinate
   collisions** (two entries whose primary ref is the same verse) → disambiguate by
   matching the store note's reconstructed text (`old_head + old_rest`) prefix against
   the candidate source chunks (the dry-run's prefix match resolved all — 0 ambiguous).
2. Parse each store `.py` via `ast` → existing dict-easton notes `(book,ch,v,suffix,
   old_body)`. **Read old bodies from the store directly — they are ground truth; do
   not try to reproduce the old extractor.**
3. Match by `(code,ch,v)` (+ prefix disambiguation for collisions). For `old_body !=
   new_body` (≈2,223), record the replacement.
4. **Precondition (ABORT on violation):** each old body must occur exactly once in its
   source `.py` and ≥1 in some base `.html`. Handle the known edge cases explicitly:
   the **1 base-miss** (locate that note — likely a source note never baked, or a
   coord typo; fix source↔base or skip-with-log, do NOT silently drop), and the **4
   base-multi** (replace ALL occurrences; verify they are the same note duplicated
   across split files, not distinct notes colliding on an identical body).
5. `--write`: exact-string replace `"<old_body>"`→`"<new_body>"` in the source `.py`
   and `<old_body>`→`<new_body>` in the base `.html`, lockstep. (For the `.py`, match
   the double-quoted literal; confirm no body contains `"`/`\`/newline — the extractor
   guarantees this, but assert it.)

### Make FULL articles work (the user's "so it works fine")
The 42 KB entries are the risk surface — VERIFY, don't assume:
- **epubcheck:** large `<aside>` bodies are valid XHTML (no element-size limit); build
  ethiopian-tewahedo + catholic-study → expect 0/0/0/0. If a giant aside ever trips
  RSC, reconsider a sentence-boundary cap at ~4 KB (the audit's fallback) — but only
  if forced.
- **File-splitter (P4b `apply_file_split`):** cuts at book/chapter/verse boundaries;
  a single 42 KB note's aside stays whole inside one ~0.4 MB piece. Confirm piece
  sizes stay sane (the splitter target is ~0.4 MB; a 42 KB note is fine) and 0 broken
  links after split.
- **Badge popup (P5 default):** a verse's notes merge into one per-verse footnote
  aside; the long entry is one scrollable item. Confirm it renders (load a built EPUB
  locally via http.server + the visual-QA flow, [[feedback_visual_qa_self_serviceable]]).
- **Corpus size:** measure the EPUB size delta (full articles add a few MB). Record
  it; flag if it pushes any single piece past the split target.

### Guard + test
- New lint guard `check_no_truncated_easton`: assert no `dict-easton` body's visible
  text ends with `…` (catches future re-truncation). Wire into `scripts/lint_rules.py`.
- `tests/test_easton_reingest.py`: (a) `_HEAD_NEW` keeps `BURNT OFFERING`, drops the
  `FOREST Hebrews` glue; (b) a known formerly-truncated entry (e.g. gen LAMECH /
  RAMESES, cited in the audit) is now complete (no `…`, ends on terminal punctuation);
  (c) full-population: 0 dict-easton bodies end with `…`.

---

## 1.5 If a full article doesn't fit — split with ZERO content loss (researched)

**User directive (2026-06-05): full articles; if one is too big to fit, split it so
ALL the content still fits — never drop text.**

**What "fit" means at each layer (researched vs the cross-reader compat doc,
`2026-06-05-eink-epub-compat-research.md`):**
- **File / EPUB — already fits, no split needed.** A 42 KB note is far under every
  documented cap: **Kobo 10 MB per HTML file** / 1 GB per EPUB; **Apple ~10 MB per
  XHTML** / EPUB ≤ 2 GB (rec ≤ 500 MB). The P4b `apply_file_split` already chunks
  spine files to ~0.4 MB pieces (cutting at book/chapter/verse boundaries; a single
  note's `<aside>` stays whole in one piece). So full articles LOAD fine everywhere.
- **epubcheck / XHTML — fits.** No element-size limit; a large `<aside>` is valid.
- **Popup DISPLAY — the only open question.** Whether a reader's footnote-popup
  widget visually truncates a very long single footnote is reader-specific and is NOT
  a documented fixed cap. **The (gated) cross-reader validation is the empirical
  test** — load a built EPUB on Apple Books / Kobo / Play Books / Kindle Previewer and
  check the longest entries (JERUSALEM-class) render in full in the popup.
- ⚠ **Kobo crash class (hygiene, not size):** a **colon in an `<a>` name/href**
  soft-bricks Nickel. The continuation-id scheme below must NOT introduce colons (use
  the existing coordinate-id hygiene).

**Conclusion:** ship **full single-note articles first** — they fit everywhere
documented. Split ONLY entries a reader is *proven* to truncate, at the measured
threshold. Do NOT pre-emptively split (it adds notes/complexity for the ~61 entries
>4 KB, most of which render fine).

**The split mechanism (if cross-reader testing forces it) — ZERO loss:**
1. **Chunk at natural boundaries, priority order:** Easton's own numbered senses
   `(1.) (2.) (3.)` → paragraph breaks → sentence boundaries (`. `). **Never
   mid-sentence, never an `…`.** Target a safe per-popup size (start ~4 KB; tune to the
   measured reader limit — keep it ONE tunable constant).
2. **Emit each chunk as a sibling dict-easton note at the SAME verse** (sequential
   suffixes, NO colons in ids). Chunk 1 leads `<strong>{HEAD}</strong>`; continuations
   lead `<strong>{HEAD} (cont.)</strong>`; title/label carries `(1/N)…(N/N)`. The
   complete article is preserved across N popups, each of which fits.
3. **Numbers mode:** the siblings are already separate markers → separate popups;
   automatic.
4. **Badge mode (the wrinkle — `apply_badge_markers`, `build_edition.py` ~1797 +
   `_badge_aside_inner_to_row` ~1782):** badge mode MERGES a verse's notes into ONE
   per-verse `verse-notes` aside, so sibling chunks re-merge and the per-verse aside
   can still be large. Hook the split HERE: when the merged aside (or a single row)
   exceeds the threshold, **start a new badge + footnote** (`vbadge-{code}-{ch}-{v}-2`,
   …) — i.e. paginate the per-verse footnote rather than emit one unbounded aside.
   This generalises to ANY verse whose merged notes exceed the threshold; same content,
   2+ badges.
5. **Verify:** rebuild + epubcheck 0/0/0/0; re-run cross-reader on the split build; a
   test asserts the concatenated chunks == the source article (nothing lost).

**Decision gate:** full single-note articles → cross-reader validation → split only the
proven-truncated entries. This keeps the common case simple and guarantees no content
is ever dropped.

---

## 2. lang-greek Theós head-drop — 1,196 bodies (100% of θεός)

**Defect:** every θεός gloss reads only `figuratively, a magistrate; by Hebraism,
very.` — the primary "God / supreme Divinity" sense is dropped. Greppable: it is the
lone corpus gloss shape `θεός</em>).</strong> figuratively, a magistrate`.
**Root cause:** a source-extraction defect (Strong's G2316 entry parsed from its tail
sub-sense). **Fix:** re-extract θεός from the Strong's Greek source with the full
primary gloss ("God, the supreme Divinity; figuratively, a magistrate; by Hebraism,
very"). Find the Greek extractor (`grep -rl 'lang-greek\|Strong' scripts/`), correct
the θεός parse (or special-case G2316), then lockstep-replace the 1,196 identical old
bodies → the corrected body in source + base. (Likely ONE old-body string → one
new-body string — a clean single replacement ×1,196 occurrences.)

## 3. topic-torrey ref-dump leak — 596 bodies (2.74%)

**Defect:** a scripture cross-reference list leaked into the topic field
(`…appears under: Zechariah 1:1 1:7…`); worst 2jn/3jn 1:1c at 7,160 chars.
Concentrated in luk/mrk/jhn/1jn/2jn/3jn/jud. **Detect:** topic text after `appears
under: ` matching `BookName \d+:\d+` runs. **Fix:** re-run the Torrey ingest with a
guard that rejects a verse-ref run as a "topic" (the χ-cluster ingest, `grep -rl
'topic-torrey\|Torrey' scripts/`); re-derive the affected 596 bodies (strip the
leaked ref-dump, keep the real topic labels) → lockstep-replace. Re-check other
ingest-heavy kinds for the same leak.

## 4. lang-greek Phōs paren-imbalance — 76 bodies

**Defect:** `…compare G5316 (φαίνω), G5346 (φημί)); luminousness…` — a dangling `)` +
a Strong's etymology/cross-ref fragment leaking into the gloss (4 open / 5 close
parens). Greppable: `compare G5316 (φαίνω), G5346 (φημί))`. **Fix:** correct the φῶς
(G5457) extraction to stop the etymology fragment leaking into the gloss + balance the
parens → lockstep-replace the 76. Same extractor as #2.

## 5. topic-nave description-as-heading — 87 bodies

**Defect:** a mis-parsed Nave **sub-entry description** captured as a topic heading:
22 phrase-only bodies (`The king of Babylon to be rewarded with the spoil of Egypt for
his service against.`) + 75 with the doubled terminal period (`…against..`). **Root
cause:** the Nave parser took a sentence-case description as a heading. **Fix (prefer
root-cause):** add a heading-vs-description discriminator to the Nave parser (real
headings are short ALL-CAPS; this is sentence-case ending in a period) and re-derive;
do NOT touch the genuine short ALL-CAPS single-label bodies (`AX`/`OG`/`AR`…).
**Verify:** after the fix a store-wide grep for `..` in topic-nave bodies → 0, and no
label list contains an internal period.

---

## 6. Order & coordination

Execute **1 → 2 → 3 → 4 → 5**, each a self-contained commit through the §0 gates,
checking in with the user after #1. Mac holds the baton (`LANE_HANDOFF` turn 14);
`/sync` is unnecessary while sole-holder, but `git fetch` + rebase before each push.
When the track is done (or paused), hand the baton back to Windows. The word-kind
findings (the owner's curated notes) are a SEPARATE, by-hand track — not part of this.

*Plan only — no `content/notes/` or `epub_working/` edited. Companion to the two
audit reports.*
