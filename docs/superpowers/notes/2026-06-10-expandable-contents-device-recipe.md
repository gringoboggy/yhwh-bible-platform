# Expandable-Contents device recipe — verifying the tablet-only collapsible ToC on Apple Books

**Status:** READY (Mac, 2026-06-10 — turn-61 backlog item 6). One page; run it in any
future Apple Books round when the user has the iPad/iPhone in hand. ~5 minutes of
device time.
**Context:** `25230b0f` made the expandable in-content Contents a **strict opt-in**
(`reader_toc_collapsible: true`; flat always-visible chapter pills are the default
everywhere). The wizard offers the option only for the 📱 tablet target
(`wizard.py TARGET_CAPS`). No shipping edition sets it, so it has **never been
device-tested in its opt-in form** — this recipe is that test.

## 1. Build the test artifact (either lane, ~5 min)

Use **catholic-study** (small canon, the standard QA edition). Do NOT commit the
flag — this is a local QA build only:

1. In `content/editions.yaml`, add to the catholic-study block:
   `reader_toc_collapsible: true`
   (leave `reader_toc_default_open` unset — collapsed-by-default is the shape we
   ship; it is also the stricter test).
   *Alternative, zero-edit path: open `/customize` in the app, tick the
   now-working "expandable Contents" checkbox on catholic-study, and build from
   the console.*
2. Build: `python scripts/build_edition.py catholic-study --force --output-dir build/toc-qa --version toc-qa`
3. **In-zip pre-check (before burning device time):** unzip and confirm the
   in-content ToC kept its `<details>` blocks — `grep -c "<details" <toc-page>`
   should equal the canon's book count, and NO `open=""` attributes present.
   (With the flag absent, the build UNWRAPS details → if you see zero
   `<details>`, the flag didn't reach the build — stop and fix.)
4. Revert the editions.yaml line (or skip if you used /customize).
5. AirDrop / Files-app the `.epub` (plain EPUB — Apple Books; the kepub/Kobo is
   NOT part of this test, e-ink is gated off this feature by design).

## 2. What to look for on the device (the eyeball list)

Open the in-content Contents page (the pill ToC, not Apple's native ToC menu):

| # | Check | Pass looks like |
|---|-------|-----------------|
| 1 | Books render **collapsed** with a disclosure marker (▸ or similar) | One row per book, no chapter pills visible |
| 2 | Tapping the **marker / row** expands to the chapter pills | Pills appear in place; page doesn't jump |
| 3 | Tapping the **book NAME** (it is a link inside `<summary>`) | ★ the critical ambiguity: does it NAVIGATE to the book or toggle the disclosure? Either is acceptable — record which, the wizard copy may need a phrase |
| 4 | Expand a book → tap a **chapter pill** | Navigates to that chapter correctly (file-split pieces — the href crosses files) |
| 5 | Collapse state while scrolling / leaving + returning | No stuck-open/stuck-closed weirdness |
| 6 | Page-position UI (slider/page count) after several expand/collapse cycles | No reflow confusion |

Also worth 30 seconds: the same checks in **macOS Apple Books** if the Mac is at
hand (different engine vintage than iOS).

## 3. Recording the result

- PASS → `TARGET_CAPS.tablet.toc_expandable: true` is device-proven; note it in
  the board + the capability table (`notes/2026-06-10-target-caps-research.md`,
  the Apple Books row's "device-verified" column) and the option's wizard copy
  can stay as-is.
- FAIL/AMBIGUOUS (esp. check 3 trapping users) → flip `TARGET_CAPS.tablet` to
  `toc_expandable: false` with an honest gate_reason, leaving the /customize
  power-user path available — the strict-opt-in default means NO shipped edition
  changes either way.

## 2b. THIS-MAC leg (no iPad needed — user offered the Kindle app, 2026-06-10)

A flagged test build is STAGED on this Mac:
`build/toc-qa/Ethiopian_Bible_catholic-study_toc-qa_2026-06-10T035903Z.epub`
(catholic-study with `reader_toc_collapsible: true`; in-zip pre-check PASSED —
75/75 books in `<details>`, none forced open; the yaml flip was local-only and
reverted, `git checkout` verified). Two
desktop data points, ~3 minutes total:

- **Apple Books (macOS):** double-click the `.epub` in `build/toc-qa/` (or
  `open -a Books <path>`). Run the §2 checks 1–4. macOS Books shares lineage
  with iOS Books but is a different engine vintage — a pass here raises
  confidence in `TARGET_CAPS.tablet`; record it separately from the iPad datum.
- **Kindle app (macOS):** import the same `.epub` (File → Import, or drag onto
  the app — the app converts it the same way Send-to-Kindle does). We do NOT
  target Kindle in the wizard, but users WILL try it; what survives conversion
  (details interactive / flattened / content shown) is honesty data for the
  "everywhere" copy. Record: does the in-content ToC show the chapter pills at
  all, and do the book rows toggle?

Both results go in the same §3 table; neither replaces the iPad eyeball (iOS
Books is the actual `tablet` target).

## Why this is safe to defer

Default-off everywhere; the wizard gates it to tablet; e-ink/ADE readers that
cannot operate `<details>` still render the pills (they ignore the element and
show content). The only risk this test retires is the tablet-side UX itself.
