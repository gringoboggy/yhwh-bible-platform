# Website fonts (self-hosted)

These fonts are self-hosted so the site needs **no third-party CDN** — consistent
with the site's "no tracking" promise. All are licensed under the
**SIL Open Font License 1.1**, which permits embedding/serving without restriction.

| Family | Use on site | Files | Copyright |
|---|---|---|---|
| **EB Garamond** | Latin body + headings | `eb-garamond-latin-{400-normal,400-italic,600-normal,700-normal}.woff2` | © The EB Garamond Project Authors — see `OFL-EBGaramond.txt` |
| **Noto Serif Ethiopic** | Geʽez / Amharic marks (ኪዳን, cover labels) | `noto-serif-ethiopic-ethiopic-400-normal.woff2` | © The Noto Project Authors — see `OFL-NotoSerifEthiopic.txt` |

**Source:** optimized `woff2` subsets from [Fontsource](https://fontsource.org/)
via the jsDelivr mirror (`https://cdn.jsdelivr.net/npm/@fontsource/...`).

The `@font-face` rules live at the top of `../style.css` with `font-display: swap`
(text shows immediately in the Georgia/serif fallback, then swaps) and a
`unicode-range` that scopes the Ethiopic font to Ethiopic codepoints only.

To add weights/subsets later, drop the matching `*.woff2` into this folder and add a
parallel `@font-face` block. Latin-ext is intentionally omitted; the lone modifier
letter `ʽ` in "Geʽez" falls back gracefully.
