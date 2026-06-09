# Adversarial review — WIN turn-57/58 commits (`d60e5eec` + `b96320a0`) + integration

**Lane:** Mac (backlog item 1/R3, turn-57/59 board) · **Date:** 2026-06-09 ·
**Method:** 3 review agents (one per commit + one integration) → every candidate
finding independently adversarially verified (refute-first) with real repo data.
Recovered from the workflow journal (`wf_12a4c922-823`) after a power
interruption; the run had completed.

## Verdict

**Both commits are faithful to their specs and the test repairs are genuine
re-homes, not weakened coverage.** 13 findings confirmed (3 filed medium — all
corrected to low/medium-nondefault on verification; the rest low/info), 2
refuted. **All actionable findings are FIXED in the commit carrying this doc.**

- `d60e5eec` (Kobo K①–K③): all three device-QA fixes correctly implemented —
  K① boundary gap at the right collision point, K② release-ttf swap complete
  (sha-identical twins, valid hinted sfnt, woff2 fully retired, OPF via
  extension mapping), K③ em-before-vh fallbacks + `#book-inner` re-caps proven
  inert in the plain EPUB and specificity-guaranteed post-kepubify. 45/45 tests
  re-verified green on Mac incl. the e2e built-EPUB gate. W① stays genuinely
  OPEN (Apple Books re-test gate).
- `b96320a0` (W3–W6 + red repairs): W3 dead-CSS deletion complete with a
  non-vacuous stays-dead pin; W4 call-site sweep complete; W5 **correctly
  deviated** from Mac's prescription (a ≥6 skin-count bump would have gone red —
  `MANUSCRIPT_SKIN_CSS` holds exactly 5 occurrences; pinning
  `WELCOME_OVERLAY_JS` directly was right); W6 wording matches ground truth.
  The 4 at-scale re-homes, 3 FieldSpecs, and CSP slice re-anchors all verify.

## Confirmed findings → dispositions (deduped; finder severity → verified)

| # | Finding | file:line | Sev (filed→verified) | Disposition |
|---|---------|-----------|----------------------|-------------|
| 1 | K② unicode-range omits **Ethiopic Extended-B** (U+1E7E0-1E7FF) prescribed by the Mac recipe; commit msg says "all four Ethiopic blocks" (Unicode has five — the recipe's 4 *ranges* were misread as 4 *blocks*). Font is cmap-verified glyph-backed in the block (28 codepoints, ttf AND the website woff2 — re-verified this session). Functionally inert today (all corpus Ge'ez sits in U+1200-137F); future-proofing for the standalone Ge'ez/Amharic Bibles. | `epub_working/stylesheet.css:48` · `scripts/style_config.py:111` · `scripts/templates/_design.py:249` · `website/style.css:26` (+dist) | med→low | **FIXED — fix-the-class:** range widened to the 5-block value at all 5 sites + both comment sets; `_ETHIOPIC_RANGE` pin updated. |
| 2 | Pin comment claims "Full Ethiopic coverage" while the value excluded Extended-B. | `tests/test_font_embed.py:49` | low | **FIXED** with #1 (value now actually full; comment re-trued). |
| 3 | **K① missed sibling:** numbers-mode `.note-ref` keeps the exact pre-fix `margin: 0 1px` tap-adjacency the badge was fixed for. Numbers mode = live `/customize` option (no shipping edition pins it; default badge). | `epub_working/stylesheet.css:177` | med→med (non-default path) | **FIXED:** adjacency rules `.note-ref + .vn-link { margin-left: 0.4em }` + kepub-only `#book-inner` 0.7em twin — gaps ONLY the marker→next-verse-number boundary (a blanket `.note-ref` right-margin would loosen mid-verse typography; markers sit inside the prose). New pin `test_numbers_mode_boundary_gap` beside `TestKoboTapGapCss`. |
| 4 | OPF pin weaker than its message: Noto item's media-type not specifically asserted (the whole-OPF `font/ttf` check is satisfied by Cardo). Not a live defect — `patch_opf_fonts` derives type from extension. | `tests/test_font_embed.py:209` | low | **FIXED:** pin now asserts `href="…ttf" media-type="font/ttf"` on the item itself (matches the `patch_opf_fonts` emission shape). |
| 5 | Third doc sibling missed by the K② sweep: `fonts/README.md` still said the Ethiopic binary is NOT committed and prescribed acquiring Noto **Sans** Ethiopic via `apply_style.py` (now forbidden). The recipe's "README already updated (Mac, this turn)" claim was false. | `content/assets/fonts/README.md` | low | **FIXED:** README rewritten to shipped reality (Serif v2.102 ttf, woff2 retired for Kobo, 5-block range, hand-authored @font-face workflow, no apply_style); φ.1 pins (`TestPhi1FontsReadmeAccurate`) kept green. |
| 6 | Truth-record count inflation: "9 stale main reds" is **8** (the `_send_json` CSP pin was green at the parent — offset 361 < 600; its rewrite was proactive hardening, not a repair) and W4 swept **11** call sites, not 10. | `dev/LANE_HANDOFF.md:8` + commit msg | low | **Recorded** here + corrected in the board/state update this turn (commit history itself is immutable). |
| 7 | **W4 fixed the instance, not the class:** 5 sibling `render_*` functions kept a never-read `version` param (`render_symbol_legend_page` / `render_sources_page` / `render_reference_tables_page` / `render_topical_index_page` / `render_merged_topical_index_page`). | `scripts/matter_pages.py` | med→low | **FIXED — whole class swept:** the 5 siblings **plus** the cascade the sweep exposed (`inject_copyright_page` / `inject_dedication_page` / `inject_symbol_legend_page` / `_write_topical_page` — dead once their render twins dropped it; the inject family was never uniform: `inject_reading_plans_page` already took 2 args). All call sites updated (`build_edition.py` + 4 test files). **Self-enforcing guard added** (`TestNoDeadVersionParams`, AST): no `matter_pages` function may declare a `version` it never reads. |
| 8 | W3 stays-dead pin is one-sided: guards the CSS file only — a render function re-emitting `class="copyright-heading"` would ship an unstyled class with no failing test. | `tests/test_presentation_polish.py:529` | info | **FIXED:** emitter-side twin added (`test_copyright_heading_has_no_emitter`, source-scans `scripts/`). |
| 9 | Spec §4.1 enumerates "all four" stacks but W5 itself added a 5th Ethiopic-fallback stack (`WELCOME_OVERLAY_JS`); the W5 pin's comment cited spec wording that didn't exist. | `specs/2026-06-09-app-eb-garamond-selfhosting.md:293` · `tests/test_skin_aa.py:275` | info | **FIXED:** spec gains the fifth-stack note (intentionally shorter, pinned separately); test comment re-trued to real spec language. |
| 10 | Verified-correct map (no defect — recorded so it is not re-litigated): `#book-inner` selectors inert in plain EPUB (zero occurrences in base HTML/scripts; id-specificity wins post-kepubify); Apple Books rendering unaffected (em-before-vh double declarations compute identically on vh-capable engines); `object-fit: contain` retained; K② file integrity (sha256 `af1790d3…60dd09` twins, 19-table hinted sfnt); 45/45 font/marker/title tests green on Mac incl. the e2e gate. Open by design: the user's device re-test (K①–K③, AB①②) + W①. | — | info | No action. |

## Refuted (do not re-file)

1. **"Fixed-window CSP test survivor silently SKIPS on drift"** — structurally
   impossible: every real `Content-Disposition` in `web.py` is the first arg of
   `self.send_header(...)`, so the anchor is always inside the −800 window; the
   `continue` only skips docstring mentions. Drift simulation → loud ASSERT-FAIL
   (the opposite of the claim). Intentionally-different sibling (in-dispatcher
   anchor; scan-to-next-def would destroy locality).
2. **"Turn-57 artifact-gate claims not reproducible on this Mac"** — provenance
   is disclosed in the handoff (WIN rebuilt + loaded G:\) and the gates are
   encoded in committed automation (`TestBuiltEpubContainsFonts`,
   `TestBadgeBuildIntegration`, `audit_epub_structure` BROKEN_NOTEREF); they
   re-fire on any rebuild. Lane truth-record working as designed.

## Re-verification of the fixes in this commit

- Website/app woff2 **independently cmap-parsed this session** (fontTools,
  ephemeral env): 528 mapped codepoints, 28 in Extended-B → the range widening
  is glyph-backed at every site, not just the EPUB ttf.
- Full targeted suites + the e2e built-EPUB font gate re-run green (see the
  commit message for counts).
- The board/state counts corrected per finding 6.
