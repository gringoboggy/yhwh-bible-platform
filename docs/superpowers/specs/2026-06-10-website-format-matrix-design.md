# Website Format Matrix — every full canon edition, per-device, with the 5×5 covers

**Status:** REVISED 2026-06-11 (was READY 2026-06-10) — user-directed scope (turn 69): the WEBSITE's Downloads catalog offers ALL 9 full-version (notes + translations) canon editions in 5 per-device formats; 5 formats ↔ 5 cover designs × 5 colour choices = the full 25-template cover set. Design proposed here; phases sequence into the v1.0.0 assessment. Kindle pillar = the Mac's active `kindle_safe` arc; Kobo pillar gated on the K-R4-2 calibration; Play Books gated on the user's offered phone-QA.

**2026-06-11 revision:** the Mac adversarial spec review
(`docs/superpowers/notes/2026-06-10-matrix-spec-review.md`) found 4 blocking
classes; this revision folds in their fixes. Blocker #1 (the `--target-reader`
build flag + cache-key fold) is **IMPLEMENTED** (build_edition.py /
build_cache.py + `tests/test_target_reader_override.py`); blockers #2–#4 are
specced below as M1/M2 work items.

## 1. The directive (user, 2026-06-10)

> "I want to offer all the FULL VERSION (notes / translations) canon Bibles we
> offer in each format (Apple Books, Kobo, Kindle, Google Play Books (which I
> can check on my phone if need be) and whatever else — a fifth would be nice
> because that would cover all the Bible Covers we offer 5x5 with colour
> choice) … on the website that is."

Interpretation (defaults set per the presentation-doctrine; every mapping below
is Boggy-overridable):

- **"All the full-version canon Bibles" = the 9 canon/notes editions**
  (ethiopian-tewahedo · catholic-study · evangelical-reformed · jewish-study ·
  scholarly-academic · eastern-orthodox · anglican-bcp · lutheran-confessional ·
  coptic-orthodox), built with their full note + translation complement. The two
  standalone Ge'ez/Amharic editions stay in LANE P (they can join the catalog as
  rows 10–11 once P2 constitutes them).
- **"Each format" = 5 device-target builds** (the fifth = **standard EPUB,
  "computer & everywhere else"** — Calibre, Thorium, ADE, Nook).
- **"On the website" = the Downloads page becomes a catalog** (edition ×
  format × colour). Artifacts are hosted as GitHub release assets exactly like
  the current v0.1.0 set; the site links them.

## 2. The product matrix

9 editions × 5 formats = **45 base artifacts**; × 5 cover colours = **225
variants** (see §4 — variants are cheap cover-swaps of the 45, not 225 builds).
Per-reader capability/quirk knowledge lives in **`dev/EREADERS.md`** (the
compatibility tracker, user-directed turn 69) — this table names the build
profiles; that file carries the evidence.

| # | Format (catalog label) | target_reader profile | Packaging | Device acceptance gate |
|---|---|---|---|---|
| 1 | Computer & everywhere else | `everywhere` (current vanilla build) | `.epub` | already shipped (v0.1.0 = this) |
| 2 | Apple Books | `tablet` | `.epub` | already proven (Mac/user rounds; title-box + layout fixes shipped) |
| 3 | Kobo & e-ink | `eink` | `.kepub.epub` via kepubify | K-R4-2 cap calibrated (round-5 taps) + gate 4g |
| 4 | Kindle | `kindle` (NEW target — the Mac arc adds it) | `.epub` for Send-to-Kindle | Mac `kindle_safe` arc (K-KIN-1..4 + Send-to-Kindle re-verify) |
| 5 | Google Play Books | start from `everywhere`; promote to its own target only if QA demands | `.epub` (upload-to-library) | USER phone-QA (offered in the directive); Play accepts EPUB 2/3 uploads, EPUB3 feature support varies per platform |

**One-resolver invariant (RULES doctrine):** every per-format behavior flows
through the existing `target_reader` resolver (schema → `api_save_edition_meta`
`valid_targets` → TARGET_CAPS → `build_edition`). The matrix adds **no second
control path**; format builds are the 9 editions built under different
`target_reader` values (the build flag overrides the edition default at build
time — it must NOT mutate `editions.yaml`, so the 9 editions' stored defaults
stay byte-stable).

**IMPLEMENTED 2026-06-11 (review blocker #1 + corollary):**
`scripts/build_edition.py --target-reader <target>` folds the override into a
COPY of the edition record at the top of `build_one` (`apply_target_override`),
so every downstream consumer sees it through the one resolver. The cache key
(`build_cache.compute_cache_key(..., target_reader=)`) hashes the **resolved**
target (override-equal-to-stored hits the same entry; the normalization
invalidated all pre-M1 keys once). The same wrong-format class was closed in
the legacy mtime shortcut: override artifacts are named
`Ethiopian_Bible_<id>_<version>_<target>_<timestamp>.epub` and
`is_output_current` is target-aware in both directions. The sidecar carries
`target_reader` (the CI manifest/catalog reads format truth per asset).
`--all --target-reader X` skips the standalone editions (no target profiles;
LANE P). Standalone + explicit override = hard error, never a silent ignore.
Tests: `tests/test_target_reader_override.py`. Proven on a real artifact:
catholic-study × eink, OPF stamp + sidecar + naming all carry `eink`.

## 3. Covers — the 5×5 mapping

`content/covers/templates/` is exactly **5 designs × 5 colours**
(black/brown/forest/navy/red). Default format↔design mapping (taste call —
flag to Boggy, override is one table edit):

| Format | Design |
|---|---|
| Computer & everywhere else | `01_ornate_leafy` |
| Apple Books | `02_classical_corner` |
| Kindle | `03_beadline` |
| Kobo & e-ink | `04_minimal_lines` (highest e-ink contrast) |
| Google Play Books | `05_missal_central` |

Colour = the downloader's pick on the site (5 swatches per format). Every one
of the 25 templates is used, per the directive.

## 4. Build + variant pipeline

1. **Base builds (45):** matrix driver builds each edition × format profile.
   Full gates per base: `verify_kr2_build.py` + epubcheck 0/0/0/0 +
   nested-anchor + (eink) kepubify clean.
2. **Colour variants (×5 → 225) — REVISED per review blocker #2; M1 core
   SHIPPED 2026-06-11.** The shipped covers are Pillow **composites** ("HOLY
   BIBLE" + edition subtitle via `fit_text_block`), and the OPF cover slot is
   `image/jpeg` — so "rezip with the raw template PNG" is wrong twice
   (title-less art + PNG bytes in a JPEG slot = epubcheck fail). The variant
   generator instead: **composite per (edition × design × colour) → JPEG →
   swap into the base under `build_epub.py`'s deterministic writer
   discipline** (mimetype-first / STORED / fixed 1980 date — bare `rezip`
   guarantees neither determinism nor zip discipline); kepub variants re-swap
   **after** kepubify. **SHIPPED:** `scripts/swap_epub_cover.py` (JPEG
   magic-byte gate, byte-preserving rewrite, 7 pins; proven on a real round-6
   artifact, epubcheck 0/0/0/0) + `generate_catalog_composite` /
   `m1_catalog_plan` in `scripts/generate_edition_covers.py`. **The 18 M1
   composites are COMMITTED under `content/covers/catalog/`** (generated on
   the canonical Windows fonts) — CI swaps the committed bytes and never
   composites in-runner, which kills the ubuntu font-divergence class at the
   root (supersedes the earlier "pin Pillow + fonts on ubuntu" mitigation;
   M2's 225-composite set decides commit-vs-pin separately). Light gates per
   variant: zip integrity + cover presence; epubcheck runs per M1 asset (18
   is cheap) — per-design spot-sampling starts at M2 scale.
3. **CI, not local (the bandwidth decision) — topology REVISED per review
   blockers #3/#4.** A GitHub Actions workflow (precedent: `build-linux.yml` —
   pinned tool installs, fail-fast `gh release view`) builds the matrix and
   uploads assets to the version's GitHub release. **Job topology: one job per
   edition (9-way matrix), formats serial within the job** — a single job
   blows the 6-hour cap (45 builds + 45 epubcheck + 9 kepubify + 225
   composites). **SHA256SUMS is NOT self-merged per job** — the build-linux
   download→grep→append→`--clobber` precedent is safe only single-job; 9+
   concurrent jobs = lost-update on the release asset. Matrix jobs upload ONLY
   their own assets; **one `needs:`-gated fan-in job regenerates
   SHA256SUMS.txt from the full asset list and uploads it once** — that job is
   also the natural "release complete" signal the catalog generator keys on.
   The repo is public (free minutes); epubcheck (PyPI jar + Temurin on ubuntu)
   and kepubify (pinned version + sha256, like appimagetool) install
   in-runner. **~5–6 GB of artifacts never touch the home connection.** Local
   builds remain for QA only. Canon editions need no gitignored assets (GAPS
   is Ge'ez-only); fonts are in-repo. **De-dupe note (review LOW):** until the
   everywhere/tablet/computer profiles diverge, 27 of the 45 base artifacts
   are byte-aliases — build ~18 real bases + alias the rest; the catalog's
   Apple cell aliases the everywhere artifact until `tablet` has a real
   profile delta.
4. **Naming:** `YHWH-<edition-id>-v<version>-<format>-<colour>.epub`
   (Kobo keeps `.kepub.epub`). The current flagship name stays as an alias of
   the ethiopian-tewahedo × everywhere × default-colour artifact so existing
   links don't break.

## 5. Website catalog UI

- The Downloads page gains the catalog: **edition picker (9, canonical order)
  × format tabs (5) × colour swatches (5)** → one download link + its SHA256.
  Default view = ethiopian-tewahedo × Computer-&-everywhere × the format's
  design in black.
- Backed by a **generated manifest** (`scripts/gen_release_catalog.py`, modeled
  on `gen_website_progress.py`): editions.yaml + the format table + release tag
  → JSON inlined by `website/build.mjs` at site build (static site, no client
  fetch, no build step added). **The format↔profile↔design table gets ONE
  in-repo home (review MED): a `FORMAT_MATRIX` constant beside
  `TARGET_READERS` in build_edition.py**, consumed by CI + the catalog
  generator + the site build — never re-typed per consumer (the MATRIX_MAP-#3
  drift class). **Catalog gating (review MED):** a column appears only when
  the release carries the FULL expected edition × colour asset count for that
  format — and the generator must paginate the GitHub asset listing (a
  ~232-asset release truncates a naive GET at 100 → columns vanish or
  over-claim). The 83-count corollary applies to catalog copy (guide asset
  names, verify-cmd examples, meta descriptions) — sweep + pin a guard test.
- Per-device guidance stays in the Guide (turn-68's per-device walkthroughs
  already cover Apple/Kobo/Android/computer + the Kindle not-yet note — that
  note flips when the Kindle column ships).
- Never-over-claim: a format column appears on the site ONLY when its artifacts
  exist in the release (the manifest generator reads the actual asset list via
  the GitHub API at generation time, or is fed the uploaded set).

## 6. Sequencing (proposal — final say at the v1.0.0 assessment, task ④)

| Phase | Ships | Gated on |
|---|---|---|
| M1 | `--target-reader` flag + cache-key fold (✅ DONE 2026-06-11) · `FORMAT_MATRIX` constant (✅ + `COVER_COLOURS` + `catalog_asset_name`, 18 pins) · the 18 M1 design-default composites (✅ committed `content/covers/catalog/`) · CI matrix workflow (✅ `.github/workflows/format-matrix.yml` + driver `scripts/build_format_matrix.py`, per-edition jobs + SHA256SUMS fan-in) · catalog generator (✅ `scripts/gen_release_catalog.py`: full-count gating, paginated assets, legacy-Kobo cell) · catalog UI (✅ releases.html band + no-JS fragment), formats 1–2 (everywhere + Apple) × 9 editions | remaining: dispatch the workflow against a release + regen catalog + redeploy the site |
| M2 | + colour variants (the composite-swap generator) | M1 |
| M3 | + Kobo column (×9 kepub) | K-R4-2 cap fix post-calibration (round-5 taps) |
| M4 | + Kindle column | Mac `kindle_safe` lands + Send-to-Kindle acceptance |
| M5 | + Play Books column | user phone-QA round on an M1 artifact |

**Never-remove-live (review MED):** the site serves the v0.1.0 flagship kepub
TODAY — the M1 catalog carries that existing artifact as the Kobo cell until
M3 replaces it; shipping the catalog must not remove a live offering.

Round-5 (current queue item ③) is unchanged and feeds M3: the calibration
tap-list pins the Kobo cap.

## 7. Explicitly NOT in scope

- No wizard/builder changes — this is the READY-MADE catalog; custom builds
  remain the wizard's job.
- No commercial framing anywhere (free downloads, plain copy).
- No per-edition stored `target_reader` mutations — the 9 editions'
  `editions.yaml` blocks stay untouched; format is a build-time parameter.
- Standalone Ge'ez/Amharic — LANE P owns them; catalog rows reserved.

## 8. Open items for Boggy (defaults set, all overridable)

1. The format↔design mapping table (§3). — **ANSWERED 2026-06-11: per-edition
   covers, not per-format. See Addendum A.**
2. The fifth format choice (standard EPUB recommended; alternatives: PDF
   export, Nook-specific) — standard EPUB also serves Nook.

## Addendum A (2026-06-11, user-directed) — per-edition signature covers

Boggy's call on open item 1, superseding §3's per-format design table and
§5's "format's design in black" default ("I don't want it to say '— black'
after every edition … each one of those has one of the 5 colours and one of
the cover styles … display the cover we picked"):

- **Every catalog asset wears the EDITION's own cover** — the recorded/factory
  template each edition already ships with (`cover_template` / the σ.2 factory
  map, now one-homed as `scripts.core.config.EDITION_COVER_TEMPLATES` with the
  resolver `edition_cover_template`). `build_edition.edition_cover_signature`
  parses it to `(design, colour)`. The nine signatures span 4 designs × all 5
  colours — the variety the directive asks the catalog to showcase.
- **`FORMAT_MATRIX.cover_design` is retired**; formats define only the build
  profile + packaging. The asset name's colour leg is the edition's signature
  colour (`build_format_matrix.cell_asset_name`), so the card a visitor sees
  is byte-for-byte the cover inside the file they download.
- **No cover swap for signature assets** — the base build already embeds the
  edition's cover; the driver copies the base to the asset name.
  `swap_epub_cover.py` + the committed-composite discipline (§4.2) remain the
  M2 leg: `catalog_colour_variant_plan()` = 9 editions × their OWN design × 5
  colours (45 composites), offered as per-cell colour picks.
- **Gating re-keyed:** a format column lights only when EVERY edition's
  signature-colour asset is published; M2 variant colours light per cell, only
  where that edition's variant exists. The legacy never-remove-live cells now
  cover both flagship files (epub on `everywhere`, kepub on `kobo`) while
  their columns are dark.
- **UI:** the `<details>` per-device lists are replaced by one cover CARD per
  edition (the edition's `website/covers/<id>.jpg`, title, one download link
  per live format — no colour words as link text). The Downloads page's
  "Read the Ethiopian Bible" band and the catalog band merged into one
  "Read the Bible — Choose Your Edition" band; the index "Choose your cover"
  template showcase retired in favour of the real covers on the catalog cards.
- **Migration protocol (hardened per the 2026-06-11 adversarial review — 6
  confirmed findings, all addressed):** the 18 old-model (format-design ×
  black) release assets are superseded. The four whose names collide with the
  two black-signature editions (evangelical-reformed, lutheran-confessional ×
  everywhere/apple) are clobbered by the re-run. Ordered steps, each gated:
  1. Dispatch format-matrix on the tag; proceed ONLY on an ALL-GREEN run
     (fail-fast:false means a partial run leaves stale colliding files
     satisfying the name-presence gate — review findings #2/#4).
  2. Verify the 4 colliding asset names were re-uploaded by THIS run
     (`gh api …/assets` `updated_at` > dispatch time) — the freshness check
     the name-only gate cannot do.
  3. Regen the catalog (the new `check_no_withdrawal` guard refuses to write
     a manifest that darkens a previously-live column — never-remove-live is
     now structural, review findings #1/#3; the committed catalog fragment
     stays at its live state until this step succeeds) → build → deploy.
  4. AFTER the deploy, delete the 14 remaining old-model assets from the
     release + prune their SHA256SUMS lines (they'd otherwise poison M2
     variant cells — review finding #5; sums-membership is NOT a provenance
     signal, the fan-in MERGES old lines forward).
  5. Regen + redeploy once more (variant-clean manifest; no visible change).
3. Whether colour variants ship in v1.0.0 (M2) or trail it.
