# TARGET_CAPS capability research — `<details>`/`<summary>` across EPUB readers

**Status:** COMPLETE (Mac, 2026-06-10, turn-61 backlog item 4) — 4-angle sweep
(incl. a **live firsthand test in this Mac's Apple Books**), every load-bearing
claim adversarially re-fetched (workflow `wf_3dc58349-d5f`). Same honesty bar as
the kepub-break research.
**Outcome:** the wizard map's four true/false values are **all correct as
shipped**; the gate_reason/note strings were upgraded to evidence-based copy
(`wizard.py` TARGET_CAPS, this commit; `test_reader_target.py` 13/13 green —
the pins are structural, not string-exact).

## Capability table (verified rows only; full evidence in the workflow journal)

| Reader | `<details>` behavior | Confidence / source class |
|---|---|---|
| **Apple Books, macOS** (Books 5.2 / macOS 13.7.8) | **Interactive** — full click round-trip: renders collapsed, `open` attr honored, click expands (page reflows), click collapses | **HIGH — firsthand live test on this Mac** (test EPUB + 3 screenshots in `/tmp`, verified by the adversarial pass) |
| **Apple Books, iOS/iPadOS** (2018 rewrite →) | **Interactive** (tap-expansion physically works; the epubtest "Fail" is a VoiceOver focus-management bug, not a render bug) | HIGH-med — epubtest 533 tester note verbatim + WebKit-native since iOS 6 + the macOS sibling proof |
| **Thorium Reader** (Electron/Readium) | Interactive | HIGH — epubtest pass |
| **calibre viewer** (4.0+, Chromium) | Interactive | MED — engine inference, no direct test |
| **KOReader** (crengine — Kobo/Kindle/PocketBook/Boox sideloaders) | **Ignored — content shown flat, permanently, by design** (maintainer: "we won't have any collapsing… we're not a dynamic web browser"; `fb2def.h` parses details/summary as plain containers) | HIGH — source code + maintainer statement |
| **Adobe Digital Editions 4.5** (+ the RMSDK e-ink lineage) | **Documented unsupported** ("On Windows, Detail, Bdi, Wbr tags are not supported" — Adobe's release notes); content-shown degradation is spec-implied, not vendor-stated | HIGH (unsupported) / MED (degradation shape) |
| **Kindle KF8/Enhanced Typesetting** | No `<details>` row in Amazon's supported-tags table (`<summary>` listed Yes — meaningless alone); static behavior undocumented. **Probed on this Mac 2026-06-10 (user logged in):** the Kindle Mac app has NO local-import path (no File→Import; `open` with an EPUB is ignored) — EPUB only enters via Send-to-Kindle cloud conversion, so on-device behavior is whatever Amazon's converter emits, never our markup directly. Full datum deferred: drag the toc-qa EPUB onto amazon.com/sendtokindle when convenient; it lands in the logged-in app for inspection | MED — primary spec, absent entry + firsthand ingress probe |
| **Google Play Books, Android** | ★ **The one probable closed-and-stuck reader** — "cannot be expanded or collapsed" (epubtest), custom non-WebKit engine, JS off. Default-closed content plausibly unreachable | MED — single AT-context test |
| **Kobo e-ink, kepub path** | **Unknown** — Kobo WebKit might render details natively but e-ink taps go to page-turns; no source either way | LOW — the one hole; 2-min Kobo check possible some round |
| **Spec baseline** (engine with no implementation) | Content shown (WHATWG rendering: the hiding lives in UA shadow-tree styling an engine without the feature doesn't have) | HIGH — spec |
| VitalSource / Bookworm / BoinIT (the other recorded fails) | Shown-but-can't-collapse — safe degradation | MED — epubtest |

## The three flagged questions, answered

1. **tablet=true is now adequately evidenced** (firsthand macOS + iOS tap proof
   + engine lineage). The device recipe
   (`2026-06-10-expandable-contents-device-recipe.md`) is **confirmation, not a
   gate** — what it still retires is product-level UX: the summary-link
   tap-ambiguity (check 3) and the DAISY paginated off-page-push caveat with
   LONG lists (Psalms' 150 pills is our worst case; the live test was 3 items).
2. **"E-ink ignores details and shows content anyway" is NOT a sourced
   universal** — true for KOReader (by design, forever), spec-implied for the
   RMSDK path, **unknown for Kobo's kepub WebKit**. Since `eink=false` means no
   shipped e-ink build ever carries `<details>`, nothing can break — but the
   gate copy now states design facts instead of the universal claim.
3. **Closed-and-stuck readers exist:** Google Play Books on Android (probable).
   This is the strongest argument for keeping `everywhere=false`, and it is now
   named in the everywhere gate_reason + the tablet note ("skip this option if
   you read in Play Books").

## Residual to-dos

- The **iPad eyeball** (recipe §2) for product UX — unchanged.
- Optional 2-min **Kobo kepub `<details>` probe** next time the Kobo is in hand
  (closes the one unknown; zero shipping impact either way).
- ⚠ Cut-checklist coupling spotted while in the file: the eink target's `note`
  says "The downloadable font pack covers…" — that string ships in the app, so
  the v0.1.0 cut must verify `yhwh-kobo-font-pack.zip` is actually live in the
  release (it is built+staged, upload gated on the user eyeball — see
  `2026-06-09-kobo-font-pack.md` §4) or soften the note before cutting.
- Housekeeping: the live test imported "Details Summary Render Test" into this
  Mac's Books library (possibly ×2) — remove via Books → right-click → Remove.
