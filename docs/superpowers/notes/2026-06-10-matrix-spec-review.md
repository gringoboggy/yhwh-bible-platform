# Website-format-matrix spec — adversarial review (Mac turn 70, board arm)

**Status:** DELIVERED 2026-06-10 (Mac) — input for WIN's M1 implementation.

Reviewed: `docs/superpowers/specs/2026-06-10-website-format-matrix-design.md` (27 agents: 4 lens
critics x adversarial verification per finding; every HIGH/MED below survived a dedicated
refutation attempt against the live code; REFUTED items listed so they are not re-litigated).

**Verdict: the spec's shape is right (CI-built, catalog-gated, one-resolver) but M1 is NOT
implementable as written.** Two load-bearing mechanisms are specced against code that does not
exist or does the opposite, and two CI patterns break at matrix scale. Convergent across all
four lenses:

## The 4 blocking classes (fix the spec before M1)

1. **The build-time `target_reader` override flag DOES NOT EXIST.** The spec forbids mutating
   `editions.yaml` (§2/§7) yet provides no other way to build a non-everywhere target — today the
   ONLY path is exactly the editions.yaml mutation the spec forbids (and the same write-the-real-file
   class as the open item-② ordering bug). Fix: a `--target-reader` build flag that feeds
   `resolve_target_reader` (one resolver, unchanged), plumbed `build_one -> patch_opf/apply_*`.
   **Corollary (HIGH):** `compute_cache_key` hashes the EDITION RECORD, so a CLI override would be
   invisible to the build cache -> wrong-format artifacts served from cache, and gate 5 skips
   non-kindle stamps by design. The override MUST fold the resolved target into the cache key.
2. **The cover-variant mechanism is wrong as specced.** "Rezip the base with the alternate cover
   PNG" (a) puts PNG bytes in the OPF's `image/jpeg` `cover.jpeg` slot (epubcheck fail), (b) ships
   TITLE-LESS raw templates (shipped covers are Pillow COMPOSITES - 'HOLY BIBLE' + edition subtitle
   via `fit_text_block`), (c) the SS3 format-design mapping has NO code path and contradicts the
   shipped per-tradition covers, and (d) the ~18 M1 composites don't exist, so M1 is not
   "nothing-gated". Fix: composite per (edition x design x colour) -> JPEG -> swap via
   `build_epub.py`'s deterministic writer (mimetype-first/STORED/1980 date); kepub variants
   re-swap post-kepubify; add composite generation as explicit M1/M2 work; pin Pillow + fonts on
   ubuntu (the compositor's font candidates are Windows-first -> silent Cardo fallback divergence).
3. **SHA256SUMS self-merge races at matrix scale.** The build-linux.yml precedent
   (download->grep -v->append->sort -u->`--clobber`) is safe ONLY single-job; 9-45 concurrent
   matrix jobs = textbook lost-update (no CAS on release assets) -> silently missing checksum
   lines under the user-facing "one link + its SHA256" promise. Fix: matrix jobs upload ONLY
   their own assets; ONE `needs:`-gated fan-in job regenerates SHA256SUMS.txt and uploads once
   (also the natural "release complete" signal for the catalog generator).
4. **Job topology is unspecified and a single job blows the 6-hour cap** (45 builds + 45
   epubcheck + 9 kepubify + 225 composites). Fix: spec the matrix shape (e.g. one job per
   edition, formats serial within) + the fan-in job from #3.

## Verified MED (fix during M1, not blockers)

- **Parallel format table = MATRIX_MAP-#3 drift class** - the format<->profile<->design table needs ONE
  in-repo home (suggest: a `FORMAT_MATRIX` constant beside `TARGET_READERS` in build_edition.py,
  consumed by CI + catalog generator + site build).
- **M1->M3 sequencing REGRESSES the live Kobo column** - the site serves the v0.1.0 kepub TODAY;
  shipping a Downloads catalog without the Kobo column removes a live offering. Fix: M1 catalog
  carries the existing v0.1.0 kepub as the Kobo cell until M3 replaces it (never-remove-live).
- **Apple Books column today = stamp-only duplicate of everywhere** (~250MB near-identical assets;
  "proven" only because format 2 IS format 1). Either give `tablet` a real profile delta
  (reader_toc_collapsible default?) or alias the Apple cell to the everywhere artifact until it has one.
- **'Idempotent' variant SHAs need build_epub's zip discipline + pinned Pillow** - bare `rezip` guarantees neither.
- **Catalog truth decays between regenerations** + keeps a hand-fed escape hatch + GitHub asset
  listing paginates at 100 (a ~232-asset release truncates a naive GET -> columns vanish or
  PARTIAL columns over-claim). Gate each column on the FULL expected edition x colour asset count.
- **The 83-count corollary applies to the catalog** - Guide asset names, verify-cmd examples, meta
  descriptions duplicate download claims; sweep + pin a guard test.

## REFUTED (do not re-litigate)

- "Single-workflow exceeds the 6h cap" as stated in the profiles lens (the cap issue is real only
  under the single-JOB topology - the ci-workflow lens version stands, the blanket claim does not).
- "Workflow trigger starves the blocking tests.yml signal / GitLab quota risk" (separate workflows
  don't contend; nothing mirrors to GitLab).
- "Local QA builds never hash-match CI artifacts" (the spec already makes CI the hash-of-record by construction).
- "Gate 4g doesn't exist" - true as a citation nit (the spec invents the name) but the intended
  gate is verify_kr2_build's existing gate set + gate 5; spec should fix the reference, nothing to build.

## Notable LOWs

- 27 of the 45 "base artifacts" are build-side no-ops today (everywhere/tablet/computer produce
  identical content modulo the stamp) - the matrix can DEDUPE to ~18 real builds + aliases until
  profiles diverge.
- Format-keyed cover designs silently override per-edition branding (flagship identity flip) - make
  the format-design row a DEFAULT, edition cover_image still wins (presentation-configurable doctrine).
- Play-from-everywhere: CONFIRMED coherent with the research; residual risk correctly gated at M5.
