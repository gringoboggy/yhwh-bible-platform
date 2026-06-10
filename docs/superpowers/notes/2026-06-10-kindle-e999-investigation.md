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
