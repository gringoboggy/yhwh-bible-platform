# Cover templates — 25 master covers (5 styles × 5 colorways)

Source: yhwh-covers-pack (Midjourney + Python hue-shift pipeline).
Ingested 2026-05-11.

## Files

All 1792 × 2688 PNG, 5:8 aspect ratio (paperback book cover standard).

**Master styles:**

| ID | Style | Description |
|----|-------|-------------|
| `01_ornate_leafy` | Ornate Family Heirloom | Elaborate gold leafy corner ornaments, leaf-edge frame border |
| `02_classical_corner` | Classical Royal | Clean gold double-rule frame, four corner fleurons, raised spine bands |
| `03_beadline` | Premium Schuyler | Bead-and-line border with scrollwork corner ornaments |
| `04_minimal_lines` | Cambridge Minimal | Thin gold rules with tiny corner accents, restrained |
| `05_missal_central` | Catholic Missal | Ornate frame with central diamond/cross starburst, ecclesiastical |

**Colorways:**

- `red` — original Midjourney generation, deep crimson leather
- `brown` — chestnut/cognac heritage brown
- `navy` — deep navy blue leather, premium/distinctive
- `forest` — forest green, Geneva / pastoral tradition
- `black` — black calfskin, liturgical / formal

Filename convention: `{style_id}_{color}.png`.

## Usage

## Licensing & AI-art stance

The 25 master templates (1792×2688 PNG) were generated with Midjourney under a
paid subscription. At the time of generation the Midjourney ToS granted
commercial use rights to the subscriber for the outputs. The publisher claims
original editorial work on: the 5 style definitions and descriptions, the
exact 5 colourways (deep crimson, chestnut, navy, forest, black — implemented
via a deterministic hue-shift post-process), the curation/selection of the 25
combinations, and all file naming + packaging. The raw AI generations
themselves are not placed under CC0 or dedicated to the public domain; the
program + this editorial layer are © 2026 Bogdan Zorlescu (standard rights
reserved, source-available). Fonts used in related assets remain under their
OFL 1.1 terms (see `content/assets/fonts/LICENSES.md`).

These templates can be used as:

1. **Direct main covers** for an edition — upload via the
   `/api/covers/<edition>/main` endpoint or drop into
   `content/covers/<edition>/main.png`.
2. **Text-overlay sources** — π.6 cover composer (planned) will
   composite the edition's title and book name over a chosen
   template. The pure-image templates above let the composer
   pick fonts, sizing, and text colors without re-prompting AI.
3. **Brand-consistency anchors** — picking one style family
   for an edition's family of covers (main + per-book) creates
   visual cohesion across the EPUB.

## Pairing recommendation per edition canon (default suggestions)

| Edition family | Suggested style | Suggested color |
|---|---|---|
| Ethiopian Tewahedo | `05_missal_central` (Coptic/Ethiopian liturgical) | `red` or `brown` |
| Catholic Study | `01_ornate_leafy` | `brown` |
| Eastern Orthodox | `05_missal_central` | `navy` or `black` |
| Anglican BCP | `02_classical_corner` | `forest` |
| Lutheran Confessional | `04_minimal_lines` | `black` |
| Reformed | `04_minimal_lines` | `forest` (Geneva green) |
| Coptic Orthodox | `01_ornate_leafy` | `red` |
| Scholarly / Academic | `04_minimal_lines` | `black` |

These are starting suggestions, not rules. The publisher picks
per-edition via `/covers` console (existing) or the future
cover-composer (π.6).

## Reusable border PNGs

See `content/assets/borders/` — 6 transparent border PNGs from
the same pack. Useful for future AI-generated leather scenes
composited under the existing gold frame. Pipeline:

1. Generate a new leather background (AI or photo).
2. Composite border PNG over it (alpha-respect).
3. Save as a new template.

## Origin pipeline (for reference)

1. Generate one master cover per style in Midjourney with
   leather grain and gold tooling rendered together (5:8 aspect).
2. Hue-shift programmatically to derive color variants
   (HSV mask gold, transform non-gold pixels, gamma-correct).
3. Re-encode as PNG.

This avoids re-prompting AI for every colorway. One good master
→ unlimited colorways.

## File sizes

~9 MB per template × 25 = ~159 MB total. Acceptable git repo
footprint for shipped product assets. If repo size becomes a
concern, consider Git LFS (not currently configured).
