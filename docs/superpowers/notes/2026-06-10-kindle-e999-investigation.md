# Send-to-Kindle E999 investigation (2026-06-10, Mac)

> ## ★ RESOLVED + PRODUCTIZED — 2026-06-14 (turn 85)
>
> The whole arc below converged on the wrong oracle (Kindle Previewer / KDP), which
> the **real Send-to-Kindle channel falsified**. The single confirmed STK PASS is
> `june10recipe.epub` = a standard `everywhere` build + only two deltas: physically
> strip `display:none`/`visibility:hidden` (CSS + inline), and collapse `dc:language`
> to a single `en-US`. Empirically (measured PASS vs the FAILED `FIXED.epub`): Amazon's
> scanner counts **CSS display:none, NOT the HTML `hidden=""` attribute** (june10 kept
> 406 hidden footnote asides and delivered); the 2 MB file-merge, the kindle_safe CSS,
> `apply_kindle_toc_rows`, `apply_kindle_unhide`, the popup-language cap, and (B)
> compaction were all FALSIFIED extras (they made the FAIL shape).
>
> **Productized** as `--target-reader kindle` (2026-06-14): those transforms are removed
> / made opt-in, and the build now reproduces the june10 shape on every signal (377 files
> / 300 xhtml / 299 spine / single en-US / 0 display:none / vn-sep 132,949 / hidden 406 /
> no kindle_safe / full 4-lang apparatus / 0 compaction), stamp aside. epubcheck 0/0/0/0,
> gate-5 green, kindle/popup/format suite green. Build-mode artifact staged to the Desktop
> for the user's STK re-confirm. Plan + full reasoning:
> `docs/superpowers/plans/2026-06-14-kindle-recipe-productization.md`. The detailed
> CORRECTION/WIN sections below are kept for the lesson.

**Trigger:** the user emailed an EPUB to their Kindle library and received Amazon's
rejection email citing **E999**. Investigated via an 8-agent workflow (3 web research
angles + artifact probe + 4 adversarial verifications), all probes on the actual sent
artifact: `~/Desktop/Ethiopian_Bible_catholic-study_toc-qa_2026-06-10T035903Z.epub`
(the `<details>`-ToC test build; the only EPUB on this box).

## What E999 officially means

Amazon's "Troubleshoot Send to Kindle Errors" table (help node `T48rsVm3gY7KeGkKUk`),
verbatim: **"Send to Kindle Internal Error — The document(s) could not be delivered due
to an internal error. Please try sending your document(s) again in some time."**
It is the server-side CATCH-ALL, not a documented content-defect code (content problems
have their own codes: E001 unsupported format, E004 encrypted, E005 corrupt PDF, E013
incompatible elements; limits are E006 count / E007 50 MB / E008 recipients). The email
deliberately carries zero diagnostics — the real conversion error is hidden.

## Evidence-ranked causes for OUR artifact

1. **SUSPECT #1 — the multi-value `dc:language` block.** The sent EPUB's OPF declares
   FIVE languages: `en-US, hbo, grc, arc, gez` (Biblical Hebrew / Koine Greek / Aramaic
   / Ge'ez — none of the last four on Kindle's supported-language list). Injected at
   **`scripts/build_edition.py:1542`** (base OPF has plain `en`) ⇒ **present in every
   built edition incl. the shipped v0.1.0 release EPUBs** — so this candidate applies no
   matter which file the user actually sent. Why #1: (a) the single most-CONFIRMED
   community root cause for persistent EPUB E999 (post-Nov-2024, when Amazon tightened
   server-side EPUB validation) is an invalid/unsupported `dc:language`; (b) Amazon's own
   conversion-failure tips name "unsupported language" as a failure cause; (c) both
   verification agents independently flagged it as the best-matching signature.
2. **POSSIBLE — `<details>`/`<summary>` ToC** (75 pairs, this test build ONLY; flag is
   `false` on all 11 editions — verified). No official or community evidence ties it to
   hard failure (Kindle strips unsupported tags / degrades via E013, which still
   delivers); kept alive only because the post-2022 converter is a black box.
3. **POSSIBLE — converter timeout on footnote density** (44,484 `epub:type="footnote"`
   asides, ~111K hrefs, ~90K ids, 82.6 MB uncompressed). Phenomenology matches "internal
   error, try again later", but zero documented cases attribute E999 to link/aside
   volume; Amazon's complexity path is E013 degrade-don't-fail.
4. **RULED OUT — size/limits** (23.9 MiB < 50 MB email cap; dedicated codes E006/E007
   would fire instead) and **fonts/container** (4 clean TTFs, no encryption.xml, OCF
   layout perfect — mimetype first + stored).
5. **Also real: E999 is sometimes TRANSIENT** (its official remedy is literally "resend
   later"; community resend-success anecdotes are common, some confounded by delayed
   emails).

## Falsification protocol (one variable per resend)

1. **Resend the ORIGINAL file once, unchanged** — if it delivers, E999 was transient; stop.
2. **Resend the staged test copy** `~/Desktop/Ethiopian_Bible_catholic-study_kindle-langtest_2026-06-10.epub`
   (byte-identical content; OPF language block reduced to the single `en-US`; mimetype
   stored-first verified; 365/365 entries). Delivers ⇒ the language block is the trigger
   (and `<details>` is exonerated). Still E999 ⇒ next variable is the `<details>` ToC,
   then footnote density.
3. **Definitive local diagnostic if needed:** Kindle Previewer surfaces the real
   conversion error the E999 email hides (community-confirmed) — but it's an undeclared
   install on this Mac (operational guard #1: needs explicit user OK / auto-mode off).

## v0.1.1 fix path (if dc:language is confirmed)

Keep the multi-language declaration where it's correct EPUB 3 (it is), but make the
Kindle path safe: simplest = primary `en-US` only in `dc:language`, moving the
present-languages declaration to per-span `xml:lang` (already correct in content,
K-R2-5 audit) — or gate the extra `dc:language` elements behind the `target_reader`
wizard choice. Owner: shared build code (`build_edition.py:1542`) — WIN-lane domain by
recent touch; surfaced per Operational Guard #6. Whichever lane takes it: re-verify the
9-KJV byte-gate story (this is an OPF-only, per-edition-build change — base untouched).

**Cross-check note:** the Send-to-Kindle web uploader (200 MB cap) is an alternative
delivery path for testing without the email pipeline.

## Round 2 (same day — user reports "still failed" after resend)

Re-ranked by direct artifact measurement:

- **NEW SUSPECT #1 — display:none volume (documented HARD fail, E3013).** Kindle
  Publishing Guidelines hard-fail conversion when >10,000 characters are hidden via
  `display:none`. Our `stylesheet.css:204` `.notes-section, .notes-rule { display:
  none; }` (+ `.verse-refs-section:300`) hides **~486,188 text characters** across 288
  content docs — **48× over the threshold**, in EVERY edition (base CSS — this is how
  the popup-footnote pattern ships). Outranks dc:language: it is a *documented* hard
  failure with massive artifact evidence, present regardless of which file was sent.
- **EXONERATED — NCX targets:** all 76 resolve, zero on `<body>` (full programmatic
  resolution against the artifact).
- dc:language remains unresolved as a co-suspect (unknown whether the user's resend was
  the original or the langtest copy).

**Test artifact #2 staged:** `~/Desktop/Ethiopian_Bible_catholic-study_kindle-test2-visible_2026-06-10.epub`
= langfix (single `en-US`) + **all 6 `display:none` declarations stripped from
stylesheet.css** (0 inline occurrences existed; notes/refs sections render visibly —
cosmetic only, valid for a conversion test). `<details>` ToC left in (one variable at a
time; its evidence remains nil). If test 2 delivers ⇒ hidden-content volume (and/or
language) was the trigger; v0.1.1 product fix = a Kindle-target variant that renders
notes-sections visibly (endnote style) instead of display:none — Kindle's own popup
mechanism follows noteref links natively and does not need hidden asides. If test 2
still fails ⇒ test 3 strips the `<details>` ToC; after that, the footnote-density/
timeout hypothesis and Kindle Previewer (install-gated) are what remain.

## ✅ CONFIRMED (2026-06-10, same day)

**Test 2 DELIVERED to the user's Kindle library** (via the Send-to-Kindle web uploader,
amazon.ca). Diagnostic signature: the failing files died in 4–5 min (early validation
gate); test 2 processed ~12+ min (real conversion crunch) and succeeded.

**Verdict:**
- **Trigger = the `display:none` hidden-content volume (E3013 class), and/or the
  multi-value `dc:language` block** — test 2 changed exactly those two and nothing else.
  (Which of the two — or both — is unresolved only if the round-2 resend was the
  original; if it was the langtest copy, language-alone is proven insufficient and the
  display:none hide is the necessary fix.)
- **`<details>` ToC definitively EXONERATED** — test 2 delivered WITH all 75
  `<details>`/`<summary>` pairs intact. Kindle converts them fine.
- **Footnote-density/timeout EXONERATED** — the full 44K-aside conversion completed.

**v0.1.1 fix prescription (owner: shared build code — WIN domain by recent touch; both
halves cheap):**
1. `dc:language` → single `en-US` (drop the hbo/grc/arc/gez block at
   `build_edition.py:1542`; per-span `xml:lang` already carries the in-content language
   info, K-R2-5-audited). Low value vs proven risk — recommend dropping unconditionally.
2. Notes-section visibility: do NOT strip `display:none` ship-wide — compliant popup
   readers (Apple/Kobo) auto-suppress `epub:type="footnote"` asides, but the CSS hide is
   the safety net for readers that don't. Correct shape = `target_reader`-gating (the
   TARGET_CAPS machinery from K-R2 already exists): a Kindle/eink-safe variant renders
   notes-sections visibly (endnote style; Kindle's native popup follows noteref links).
   Wizard copy: name Send-to-Kindle compatibility explicitly.
3. Regression gate: a `kindle_safe` check (no >10K chars under display:none when the
   target is kindle; single dc:language) in the artifact verifier.

**Bonus:** the book is now ON the user's Kindle — first Kindle device-QA datum is
unblocked (round-1 Kindle eyeball possible whenever the user wants).

## Kindle round-1 device QA (Mac Kindle app, driven via screenshots, 2026-06-10)

**Working:** title-page ART renders (gold artwork + BOOK-N eyebrow + framed caption +
ornament); parchment page background carried; dense text pages clean; per-book NCX nav
+ footer labels correct; `<details>` converts safely (renders permanently EXPANDED, stray
▸ marker — conversion-proof, interactivity dropped); search/locations work.

**Issues (K-KIN-1…4):**
1. **No note popups** (user datum) — Kindle ignores our aside/popup pattern; with test-2's
   visible notes this is endnote-style reading, refs presumably jump. Kindle-variant
   design must accept follow-link footnotes (Kindle's native popup needs its own
   pattern; evaluate at the v0.1.1 kindle_safe work).
2. **ToC pills linearize** — one chapter pill per LINE (inline-flex lost in KFX), Genesis
   ToC spans several pages. Kindle-variant: plain inline text links or rows, not pills.
3. **Book seams shatter into up to 3 sparse pages** — caption band ("BOOK II / The Second
   Book of Moses"), a fully BLANK page, and the art page can each take a page
   (window-size dependent; locations 31849/32436/32439/32458 observed). Likely the title
   singleton pieces + title-div structure; acceptable beta, fold into the kindle variant.
4. `<details>` marker/expansion cosmetics (covered above).

Evidence: /tmp/kindle-qa-*.png (session-local). Next Kindle datum = user device eyeball
or the v0.1.1 kindle_safe variant build.

## Round 3 (2026-06-13, Mac) — STILL E999 on the SHIPSHAPE single-volume; override ≠ strip

**User re-reported E999** on the run-9 SHIPSHAPE full-apparatus build
(`~/Desktop/Ethiopian Bible - Catholic Study (Kindle).epub` = the renamed
`kindle-nosplit_2026-06-11T213913Z_rung-shipshape-full`; 23 MB zip / 73 MB raw,
62 spine pieces, 43,071 asides, 111,718 links, single `dc:language` en-US ✓).
**The user ran Kindle Previewer 3 THEMSELVES — clean — yet Send-to-Kindle
returns E999.** ⇒ the Previewer oracle is **FALSIFIED as a success predictor**
(runs 1–9 were tuned against it; "ET Supported / KPF written" ≠ Amazon accepts).

**Diagnosis — `display:none` OVERRIDE vs physical STRIP.** `apply_kindle_safe_css`
(`build_edition.py:2290`, `_KINDLE_SAFE_CSS` :2267) APPENDS a variant block that
overrides the base hides (`.notes-section`/`.verse-refs-section` → block,
`.vn-sep` → inline, `.note-label` → block) but the BASE `display:none` rules
(stylesheet ~204/300/972 + the note-label hides) remain physically in the CSS.
epubcheck + Previewer resolve the full cascade → see "shown" → green. **The only
artifact that EVER delivered (test-2, 2026-06-10) had every `display:none`
PHYSICALLY STRIPPED.** Across same-era builds: strip → delivered; override
(turn-71 kindle-safe AND this shipshape) → E999. ⇒ **leading hypothesis: Amazon's
Send-to-Kindle server scans RAW CSS for `display:none` over big-content
selectors and does NOT resolve the cascade**, so the override is invisible to it.
This RE-OPENS the hidden-text class that turn-71/78 "killed" — that exoneration
used the Previewer oracle, which never enforced this rule.

_Measurement correction:_ by effective cascade the shipshape file hides almost
nothing (the override unhides vn-sep/note-label); the ONLY distinguisher from
test-2 is the RAW presence of `display:none` strings. So gate-5 (which checked
the EFFECTIVE css, "955 chars") gave a false green — it must scan RAW.

**Test staged (one variable):** `~/Desktop/Ethiopian Bible - Catholic Study
(Kindle) TEST-nohide.epub` = the EXACT failing file with ALL `display:none` /
`visibility:hidden` removed (verified 0 hidden rules / 0 hidden attrs;
epubcheck 0/0/0/0; OCF mimetype-first). Every other shipshape trait held
constant. **Upload verdict PENDING — Amazon Send-to-Kindle service reported
temporarily unavailable 2026-06-13; user will retry when it is back.**
- DELIVERS ⇒ confirmed. Product fix: for the kindle target, STRIP (not override)
  `display:none`/`visibility:hidden` in the variant CSS + new artifact gate that
  fails on ANY raw `display:none` over content (gate-5 currently validates the
  EFFECTIVE css → false green).
- E999 again ⇒ hidden-CSS exonerated for real; pivot to diffing this build vs
  the 2026-06-10 delivered build. Research workflow (`wf_2c40ddfa-632`) hunting a
  server-faithful local oracle (Previewer CLI KFX export / Calibre KFX plugin).

## ✅ RESOLVED (2026-06-13, Mac) — display:none WAS the blocker; KDP-confirmed; in-build fix shipped

**The decisive run.** `TEST-nohide` FAILED Send-to-Kindle again (same opaque
E999) — BUT the user then uploaded it to **KDP**, where it **converted clean and
passed quality checks all the way to the pricing step.** So:
- **`display:none` hidden content WAS the Amazon blocker** — primary source:
  Kindle Publishing Guidelines v2026.1 §17.2.1 p.99, **`E3013`: "More number of
  characters are hidden using display:none than allowed limit. Limit: 10000."**
  Two strip→success results (test-2 STK delivery 06-10 + TEST-nohide KDP pass
  06-13) vs every hidden-content build failing.
- **Send-to-Kindle is the wrong channel to engineer against** — it is
  non-deterministic, blind (E999 = opaque catch-all), and unsupported (research
  `wf_2c40ddfa-632`; Universalis precedent). TEST-nohide's STK failure was STK
  flakiness, not a content defect; **KDP — the real publishing pipeline —
  accepts the full single-volume Bible.**
- **The override (display:block after base display:none) is invisible to
  Amazon's server**, which does NOT resolve the cascade (Kindle Previewer +
  epubcheck DO → false green for 9 runs). The fix must PHYSICALLY strip, not
  override. Our gate-5 made the same effective-cascade mistake.
- A side note: KP3 `-qualitychecks` (the pass we'd never run) pegged the 2017
  iMac CPU and never completed on this book — not a usable local oracle here.

**Fix shipped in-build (TDD):**
- `scripts/build_edition.py` → `apply_kindle_strip_hidden(tmp, edition)`
  (kindle-gated, runs after `apply_kindle_safe_css` + the splitter): physically
  removes every `display:none`/`visibility:hidden` (CSS + inline) AND drops the
  Kobo-only `.vn-sep` separator spans (which would otherwise show as stray
  ¶/◦/• once nothing hides them). No-op/byte-identical for non-kindle.
- `dev/verify_kr2_build.py` gate 5 → now scans **RAW** hidden selectors
  (`_raw_hidden_selectors`), fails on ANY content under a raw hide; the buggy
  `_effective_hidden_selectors` (false-green source) + `_CSS_DISPLAY_RE` deleted.
- Tests: `tests/test_kindle_strip_hidden.py` (5) + rewritten gate tests
  (override now FAILS, physical-strip GREEN).

**Proven artifact:** `catholic-study --target-reader kindle` rebuild =
**19.28 MB**, **0** display:none / visibility:hidden / hidden="" / vn-sep,
**43,220 popups intact**, single dc:language, **gate 5 GREEN**, **epubcheck
0/0/0/0**. Staged `~/Desktop/Ethiopian Bible - Catholic Study (Kindle)
FIXED.epub`. ⚠ Parity (Guard #4/#6): both edited files are WIN round-7 domain —
flagged on handoff (changes are in distinct functions, expected clean merge).

## ⚠ CORRECTION & AUTHORITATIVE RECONSTRUCTION (2026-06-14, Mac) — the "RESOLVED" section above is OVERSTATED; K-KIN is NOT confirmed on the real channel

The "✅ RESOLVED" section is **wrong about the channel** and is SUPERSEDED by this.
User-confirmed 2026-06-14: **the goal is Send-to-Kindle delivery** of the
program-emitted EPUB ("the kindle epubs our program makes are uploaded through
amazon to kindle"; "we're not making users go through KDP"). **KDP is NOT a
distribution path** (it would violate the 2026-05-14 free-public pivot) — it was
only ever a 2026-06-13 diagnostic ORACLE. (Source-of-truth re-confirmed: format-matrix
spec row 4 "Send-to-Kindle", `dev/EREADERS.md`, the `kindle` target docstring.)

**Two drifts (BOTH this Mac lane) put the arc on the wrong oracle/channel:**
1. **Turn 73 (06-11) — ORACLE drift:** success oracle switched to Kindle Previewer 3;
   STK uploads held. ALL of turns 73-78 (the byte/element/density bisection + the run-9
   SHIPSHAPE "single-volume full-apparatus PROVEN" claim) was measured on **KP3 only** —
   and KP3 was then FALSIFIED (user ran it clean while STK still E999'd).
2. **Turn 81 (06-13) — GOAL-CHANNEL drift:** TEST-nohide failed STK but passed KDP →
   declared "RESOLVED, STK flaky, KDP-publishable." That swapped the success criterion
   to the wrong channel.

**Complete Send-to-Kindle test record (the ONLY channel that counts):**
- 06-10 email toc-qa (display:none PRESENT) → FAIL E999 (~4-5 min validation gate)
- 06-10 resend → FAIL
- **06-10 WEB UPLOADER test-2 (display:none PHYSICALLY STRIPPED; full apparatus;
  hidden="" left; `<details>` ToC) → ✅ DELIVERED (~12 min) — THE ONLY STK SUCCESS EVER**
- 06-10/11 kindle_safe OVERRIDE (display:none not stripped) → FAIL (~1h)
- 06-11 retry → FAIL (~46-50 min)
- 06-11 unhide (display:none CSS still present) → FAIL (3rd consecutive)
- 06-13 shipshape OVERRIDE (user-ran KP3 CLEAN) → FAIL E999 (this falsified KP3)
- 06-13 TEST-nohide (display:none stripped) → FAIL E999 — **but STK was reportedly DOWN
  that day** (weak datum; this is the failure the turn-81 "flakiness" call leaned on)
- **FIXED.epub (the shipped fix) → NEVER uploaded to Send-to-Kindle**

**test-2 is UNRECOVERABLE** — `*.epub` is gitignored (`/Ethiopian_Bible*.epub`), never
committed (0 .epub in git history), not in Trash, no 06-10 build dir survives, no Time
Machine. Recipe (documented, reproducible): toc-qa full-apparatus + single en-US
dc:language + display:none physically stripped from CSS + hidden="" left intact +
`<details>` ToC.

**HONEST STATUS:** the in-build fix (`apply_kindle_strip_hidden` + RAW gate-5) is real,
TDD'd, and **likely NECESSARY** (the one STK success had display:none stripped; every
present/override build failed) — but **NOT proven SUFFICIENT on STK** (TEST-nohide
stripped + failed, albeit on a service-down day). **Send-to-Kindle delivery of the
shipped FIXED.epub is UNCONFIRMED.** Every numeric ceiling (bytes/elements/density,
`FILE_SPLIT_TARGET_KINDLE`=2 MB, `MAX_POPUP_LANGUAGES_KINDLE`=2) was KP3-measured on the
falsified oracle — **unverified on STK**; treat as unproven.

**NEXT — candidate #1:** upload `FIXED.epub` via the Send-to-Kindle **WEB UPLOADER**
(amazon.ca/sendtokindle — the channel test-2 succeeded on, NOT email). PASS → fix
confirmed on the real channel. FAIL → retry on a confirmed-up day (kill the service-down
confound), THEN reproduce test-2's recipe from source. **Cross-lane (WIN):** the website
FORMAT_MATRIX **M4 Kindle column is NOT actually unblocked** until an STK pass on a
PROGRAM build — do not light M4 on the stale "RESOLVED" claim.

_Full from-the-beginning reconstruction: workflow `wf_f714f284-c10` (2026-06-14, 9 agents,
every kindle doc + changelog + truth record + tooling cross-read)._

## ✅✅ RESOLVED FOR REAL (2026-06-14, Mac turn 84) — Send-to-Kindle ACCEPTS the `june10recipe` build

User-confirmed: `~/Desktop/Ethiopian Bible - Catholic Study (Kindle) june10recipe.epub`
**DELIVERED via Send-to-Kindle** (fast upload). This reproduces the proven test-2 recipe
and CONFIRMS the root cause **on the real channel** (not a proxy):

**Root cause (confirmed):** the transforms `FIXED.epub` piled on for the *falsified*
Kindle-Previewer oracle — **shipshape markup compaction + the 189-way file-split +
`hidden=""` attr-stripping** — are what broke Send-to-Kindle. The MINIMAL recipe works:
- `scripts/build_edition.py catholic-study` (standard *everywhere* build), then
- post-process: strip `display:none`/`visibility:hidden` (CSS + inline) · collapse
  `dc:language` → single `en-US` · **leave `hidden=""` attrs** · OCF re-zip
  (mimetype-first STORED).
- Result: 24.1 MB, 299 spine, full apparatus, epubcheck 0/0/0/0 → **STK-delivered (fast)**.

**Productization (the remaining open task):** the recipe is currently a standard build +
a deterministic post-process script. Re-point the `--target-reader kindle` build mode to
emit exactly this (DROP the shipshape/split/attr-strip transforms for kindle) so the
website generates it in one build → then WIN lights FORMAT_MATRIX **M4 Kindle**. Re-confirm
any productized build on the REAL Send-to-Kindle channel — the only valid oracle (memory
`feedback_validate_real_delivery_channel`).
