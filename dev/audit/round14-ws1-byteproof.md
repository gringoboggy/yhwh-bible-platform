# Round-14 WS1 158-verse re-split — all-edition BUILD byte-proof

Run 2026-06-26 18:02:45Z · PRE=5039cda0 (pre re-split) · POST=6b690361 (re-split applied) · 9 KJV byte-stable cells · 38 re-split base files.

The re-split is a USER-RATIFIED base change, NOT build-output-neutral — it fills 158 empty verse anchors, removing the build's KJV empty-anchor fill (`¶ And God spake…` = the WS1 weird-symbol/KJV-bleed) and restoring correct WEB body. So a char delta is EXPECTED. The verdict checks the change is CONFINED + EXPLICABLE:

- **INV-1** no inner member added/dropped · **INV-2** every differing member is a re-split descendant OR a link-only (href piece-retarget) TOC/xref file · **INV-3** 0 dead cross-file links in POST · **INV-4** both builds rc 0.

| # | edition | target | verdict | INV1 | INV2 | INV3 | dead/total links | differ (resplit/linkonly/?) | char Δ | rc |
|---|---------|--------|---------|------|------|------|------------------|------------------------------|--------|----|
| 1 | catholic-study | everywhere | ✅ PASS | ✓ | ✓ | ✓ | 0/12225 | 91 (91/0/0) | 10173 | 0/0 |
| 2 | evangelical-reformed | everywhere | ✅ PASS | ✓ | ✓ | ✓ | 0/12369 | 115 (110/5/0) | 10369 | 0/0 |
| 3 | eastern-orthodox | everywhere | ✅ PASS | ✓ | ✓ | ✓ | 0/12512 | 115 (110/5/0) | 10369 | 0/0 |
| 4 | catholic-study | tablet | ✅ PASS | ✓ | ✓ | ✓ | 0/12115 | 37 (37/0/0) | 10173 | 0/0 |
| 5 | evangelical-reformed | tablet | ✅ PASS | ✓ | ✓ | ✓ | 0/12248 | 37 (37/0/0) | 10173 | 0/0 |
| 6 | eastern-orthodox | tablet | ✅ PASS | ✓ | ✓ | ✓ | 0/12391 | 37 (37/0/0) | 10173 | 0/0 |
| 7 | catholic-study | kindle | ✅ PASS | ✓ | ✓ | ✓ | 0/12186 | 50 (50/0/0) | 10173 | 0/0 |
| 8 | evangelical-reformed | kindle | ✅ PASS | ✓ | ✓ | ✓ | 0/12319 | 50 (50/0/0) | 10173 | 0/0 |
| 9 | eastern-orthodox | kindle | ✅ PASS | ✓ | ✓ | ✓ | 0/12462 | 50 (50/0/0) | 10173 | 0/0 |

## Verdict

**PASS** — across all 9 KJV byte-stable cells the 158-verse re-split's built-EPUB delta is fully CONFINED + EXPLICABLE: no member added/dropped (INV-1), every differing member is a re-split-file descendant (WEB relocation + KJV empty-anchor-fill removal) or a link-only TOC/xref retarget (INV-2), and 0 dead cross-file links remain (INV-3); both builds succeed (INV-4). The 9 cells get a NEW byte-baseline (ratified) — G1's golden must be stamped from POST.

Finished 2026-06-26 18:03:54Z.

## Per-cell differing files (diagnostic)

- **catholic-study everywhere** — 91 differ (91 re-split, 0 link-only)
- **evangelical-reformed everywhere** — 115 differ (110 re-split, 5 link-only)
- **eastern-orthodox everywhere** — 115 differ (110 re-split, 5 link-only)
- **catholic-study tablet** — 37 differ (37 re-split, 0 link-only)
- **evangelical-reformed tablet** — 37 differ (37 re-split, 0 link-only)
- **eastern-orthodox tablet** — 37 differ (37 re-split, 0 link-only)
- **catholic-study kindle** — 50 differ (50 re-split, 0 link-only)
- **evangelical-reformed kindle** — 50 differ (50 re-split, 0 link-only)
- **eastern-orthodox kindle** — 50 differ (50 re-split, 0 link-only)
