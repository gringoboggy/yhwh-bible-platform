# Website Format Matrix — every full canon edition, per-device, with the 5×5 covers

**Status:** READY 2026-06-10 — user-directed scope (turn 69): the WEBSITE's Downloads catalog offers ALL 9 full-version (notes + translations) canon editions in 5 per-device formats; 5 formats ↔ 5 cover designs × 5 colour choices = the full 25-template cover set. Design proposed here; phases sequence into the v1.0.0 assessment. Kindle pillar = the Mac's active `kindle_safe` arc; Kobo pillar gated on the K-R4-2 calibration; Play Books gated on the user's offered phone-QA.

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
2. **Colour variants (×5 → 225):** a deterministic **cover-swap generator** —
   rezip the base with the alternate cover PNG (and title-page art reference if
   the cover id is baked into OPF/titlepage). Light gates per variant: zip
   integrity + cover presence + manifest hash; epubcheck on a per-design spot
   sample (the swap touches no markup). Idempotent; variant SHA256s merge into
   SHA256SUMS.
3. **CI, not local (the bandwidth decision):** a GitHub Actions workflow
   (precedent: `build-linux.yml` — pinned tool installs, fail-fast
   `gh release view`, self-merging SHA256SUMS) builds the matrix and uploads
   assets to the version's GitHub release. The repo is public (free minutes);
   epubcheck (PyPI jar + Temurin on ubuntu) and kepubify (pinned version +
   sha256, like appimagetool) install in-runner. **~5–6 GB of artifacts never
   touch the home connection.** Local builds remain for QA only. Canon editions
   need no gitignored assets (GAPS is Ge'ez-only); fonts are in-repo.
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
  fetch, no build step added).
- Per-device guidance stays in the Guide (turn-68's per-device walkthroughs
  already cover Apple/Kobo/Android/computer + the Kindle not-yet note — that
  note flips when the Kindle column ships).
- Never-over-claim: a format column appears on the site ONLY when its artifacts
  exist in the release (the manifest generator reads the actual asset list via
  the GitHub API at generation time, or is fed the uploaded set).

## 6. Sequencing (proposal — final say at the v1.0.0 assessment, task ④)

| Phase | Ships | Gated on |
|---|---|---|
| M1 | CI matrix workflow + catalog UI, formats 1–2 (everywhere + Apple) × 9 editions, design-default colours | nothing — both formats are proven today |
| M2 | + colour variants (the cover-swap generator) | M1 |
| M3 | + Kobo column (×9 kepub) | K-R4-2 cap fix post-calibration (round-5 taps) |
| M4 | + Kindle column | Mac `kindle_safe` lands + Send-to-Kindle acceptance |
| M5 | + Play Books column | user phone-QA round on an M1 artifact |

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

1. The format↔design mapping table (§3).
2. The fifth format choice (standard EPUB recommended; alternatives: PDF
   export, Nook-specific) — standard EPUB also serves Nook.
3. Whether colour variants ship in v1.0.0 (M2) or trail it.
