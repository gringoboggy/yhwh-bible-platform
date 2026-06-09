# K-R2-1 research — kepub page-break behavior (VERDICT: split at book boundaries)

**Status:** RESEARCH COMPLETE (Mac, 2026-06-09) — 4-angle web sweep, 49 claims,
every load-bearing claim adversarially re-verified against re-fetched sources
(workflow `wf_6a024ee1-9f0`). **The answer is unambiguous and vendor-documented.**
**Consumer:** WIN's K-R2 fix sequence step 2 (`notes/2026-06-09-kobo-round2-device-qa.md`).

## The one-line answer

Kobo's e-ink kepub renderer supports **NO page-breaking CSS at all** — this is
Kobo's own documentation, not folklore. The ONLY break mechanism it guarantees
is **a new HTML file in the spine**. The K-R2-1 fix is therefore
**(a) splitter-cut-at-book-boundaries** — make every
`<section class="book-title-page">` file-initial in its `index_split_NNN.html`.

## Verified facts (each re-fetched + quote-checked by the adversarial pass)

1. **Vendor table, unconditional:** `github.com/kobolabs/epub-spec` (Kobo's
   official EPUB guidance; last pushed 2025-09-24 with the table intact) lists
   **N for every one of the 12 page-break variants on "eInk/EPD — Kobo eInk
   devices"** (the Libra-Colour class included) — `before:always`,
   `after:always`, `inside:avoid`, all of them. Only the iOS/Android Kobo apps
   support `before/after:always`. (The README's 2016 "work is underway" line
   never materialized — see 3.)
2. **The only guaranteed break:** README line 322 verbatim: *"A page break will
   occur whenever the reading system encounters a new html file. Creating a new
   file is the best way to establish page breaks across all Kobo apps. Support
   for other page-break methods is not consistent."* This exactly explains the
   device evidence: our breaks DO fire at existing `index_split_NNN` boundaries
   and are ignored mid-file (kobo22's ToC→title→ch1 jam).
3. **A decade-persistent, Kobo-acknowledged:** epub-spec issue #18 — Kobo staff
   2015 ("we will be testing") → 2016 ("our level of support is documented") →
   community 2021 ("still a problem five years later") → zero evidence any
   firmware (incl. the 2024-era colour line) added support. `break-after: page`
   fails identically (Standard Ebooks tools#187, plus "Kobo got back to me,
   this is a known issue... no ETA").
4. **The failure is categorical, not nesting/mid-file-conditional:** no source
   documents ANY condition under which break CSS works on e-ink kepub (SE#187's
   failing case was top-level elements, no wrapper nesting) — so there is no
   "direct children of `#book-inner`" trick to chase. The `#book-inner`
   column-pagination mechanism theory is plausible but UNVERIFIED (flagged by
   the adversarial pass); `-webkit-column-break-*`/`break-before: column` has
   **zero documented attempts** either way on kepub — speculative A/B at best.
5. **kepubify is break-neutral:** code search over `pgaskin/kepubify` = zero
   page-break handling; its only injected style is
   `div#book-inner { margin-top: 0; margin-bottom: 0; }`. Our CSS survives
   conversion untouched; the failure is the renderer, not the converter.
6. **Two renderers on the same device:** plain `.epub` sideloads render via the
   ADE/RMSDK engine, where `page-break-before` DOES work — but sideloaded
   kepub gets tap-popups; plain epub gets working CSS breaks but no kepub
   features (and note: sideloaded kepub disables Kobo bookmarking/annotations
   per the README — already our shipped tradeoff, unchanged).
7. **No perf penalty for more/smaller spine files:** Kobo's limits are 10 MB
   per file / 1 GB per book; page-turn latency is CPU-bound, not
   file-count-bound (NiLuJe's Forma benchmarks). calibre's own epub→kepub path
   splits at every `page-break-before` — file-per-break is the established
   practice.

## Prescription for WIN (K-R2 fix step 2)

1. **`apply_file_split`: force a piece boundary immediately BEFORE every
   `<section class="book-title-page">`** so each book's title page starts a
   fresh spine file. Keep the existing size-based splitting within books.
   This also collaterally helps K-R2-2 (the early-Genesis merged asides stop
   sharing a piece with the front-matter/ToC tail, so a Kobo NAVIGATE fallback
   no longer looks like "jump to ToC start").
2. **Keep the existing `page-break-*`/`break-*` CSS** — Apple Books honors it,
   Kobo ignores it harmlessly, kepubify passes it through.
3. **Cautions (sourced):**
   - After re-splitting, verify kepubify's dummy-titlepage heuristic still does
     the right thing with the new first spine file (its "first spine entry
     treated specially" heuristic is documented as subject to change).
   - Never emit BOTH a forced `-after` and `-before` at the same boundary
     (blank-page risk on some engines).
   - Re-run the full artifact gate (epubcheck 0/0/0/0 · nested-anchor ·
     noteref in-file resolution — splitting changes which file every
     cross-piece href lands in) **and gate on canon-filtered catholic-study**,
     not just eth (the splitter+canon-filter edge-class, RULES experience).
4. **Optional zero-cost experiment** (do NOT gate on it): add
   `break-before: column; -webkit-column-break-before: always;` to
   `.book-title-page` alongside the existing breaks — untested hypothesis per
   #4 above; the split is the fix either way.

## Sources (all fetched + adversarially re-checked)

kobolabs/epub-spec README + issue #18 · pgaskin/kepubify `transform.go` +
pkg.go.dev kepub docs · pgaskin Kobo-Reader#68 · standardebooks/tools#187 ·
MobileRead t=344570 / t=346874 / t=272220 / t=284268 / t=334622 / t=358723 ·
friendsofepub BlitzTricks · w3.org css-break-3.
