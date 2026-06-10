# Send-to-Kindle E999 investigation (2026-06-10, Mac)

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
