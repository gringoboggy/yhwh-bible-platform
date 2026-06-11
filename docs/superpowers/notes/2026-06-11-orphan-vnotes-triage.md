# Orphan vnote asides — triage verdict (WIN, 2026-06-11; Mac turn-71 TRIAGE→WIN)

**Status:** TRIAGED — one class, root-caused by execution; fix assigned to Mac
(build_edition.py arc). Diagnostic: `dev/_triage_orphan_vnotes.py` (scans the
base by default or any `.epub`/`.kepub.epub` argument; counts footnote asides
with no incoming href and no incoming noteref, grouped by book).

## Measurements (by execution)

| surface | total footnote asides | orphans | breakdown |
|---|---|---|---|
| base `epub_working/` | 128,097 | **0** (both definitions) | — |
| r6 eth artifact (epub) | 66,880 | **206** | aes 205 · est 1 (`vnote-est-10-5`) |
| Mac's kindle artifact (board turn-72) | — | **1,598** | 2es 944 · 1es 448 · aes 205 · est 1 |

## Root cause — ONE class: body-section removal drops markers but not asides

In the base, every `vnote-aes-*` aside is correctly paired with a
`vn-link`/noteref on its verse (verified: `index_split_028.html` carries both
the `id="v-aes-1-1"` noteref and the aside). The asides are all
**`vnote-empty` placeholders** ("[no text in this edition; verse marker
only]").

In the eth artifact: the aes **body section is removed entirely** (the 83-book
superset fold — aes folds into Daniel/Esther; body text AND markers gone:
zero `v-aes-*` ids, zero body-text hits) — but the 205 `vnote-aes-*` asides
ride along in the notes block (`index_split_028_02.html`), now unreachable.
`vnote-est-10-5` = the same shape at one coordinate (Greek-Esther extent verse
10:5; KJV Esther ends 10:3 — its marker never survives the arrangement).

On canon-FILTERED editions the same mechanism fires for whole excluded books:
catholic-study drops 1es/2es bodies via the canon splice → their 944+448
vnote asides orphan identically (Mac's 1,598 = this class at canon scale; the
`gate-canon-filtered-editions` lesson again — the splice has edge cases the
superset hides).

## Impact

- **Kobo/Apple/everywhere:** dead `display:none` bytes only (~60 KB eth) —
  hygiene, not user-visible.
- **Kindle: USER-VISIBLE.** `apply_kindle_unhide` + the kindle_safe visible
  endnotes mean every orphan renders as a reachable-by-scrolling endnote row
  reading "[no text in this edition; verse marker only]" — ×1,598 on
  catholic-study kindle builds. Also re-inflates the hidden/visible char
  budget the E3013 work just spent down. **This makes the fix part of the
  K-KIN acceptance path, not backlog hygiene.**

## Fix (Mac — the fold/canon-splice passes live in build_edition.py)

When a pass removes a book's body section (superset fold OR canon splice), it
must drop that book's `vnote-{code}-*` asides in lockstep (same commit:
`vnote-est-10-5`'s one-coordinate case = drop any vnote aside whose
`v-{code}-{ch}-{v}` anchor is absent post-removal — that generalization covers
both). Gate: extend `dev/verify_kr2_build.py` with an orphan-aside check
(gate 4j; `dev/_triage_orphan_vnotes.py` is the working scan to lift). Expect:
eth 206→0, kindle 1,598→0; popup-generator side needs NO change (the base
pairing is correct — this is purely an edition-build filter gap).
