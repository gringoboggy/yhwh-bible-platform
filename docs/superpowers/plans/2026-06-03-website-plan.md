# Website — Free-Download Portal (yhwhyaway.com) — Implementation Plan

**Status:** in progress — 2026-06-03 (Mac lane). Direction CHOSEN by the user: **manuscript-reverent** (illuminated Ethiopian codex), built on warm-accessible's WCAG-2.2-AA contrast discipline. **Phase-1 clickable prototype BUILT + reviewed** (`website/index.html` + `style.css` + 9 cover thumbnails; the 11 editions; served on `:8787`). Tech = plain HTML/CSS + a small `build_site.py` generator (NO static-site generator); deploy free on **GitLab Pages → yhwhyaway.com** (GitHub `*.github.io` mirror). Planned by a 5-agent workflow (`wf_a8cbf1ad-eb5`).

## Model
LANDING-PAGE-FIRST static download portal for the free Ethiopian Tewahedo Bible EPUBs — **not** the live builder. Free, CC0, **no commerce, no tracking, no signup**. The EPUB editions are the product; the page's one job is: find the right edition → download it.

## Chosen direction — manuscript-reverent (+ grafts)
Warm vellum ground (`#F4ECD8`), ink-brown text (`#2B2118`, ~12:1), liturgical accents in gold/stole-red/Aksumite-indigo (**gold only on hairlines/marks/large text, never body**), one hand-inked processional cross as the sole ornament. Fonts: Noto Serif Ethiopic + EB Garamond (self-host in Phase 2). **Graft from warm-accessible:** documented contrast pairs, the plain-language "Which edition is for me?" guidance, `<details>` "What's inside" disclosures, 18px base, ≥44px targets. **Graft from modern-minimal:** let the leather-and-gold covers carry the color (quiet chrome), inline "format · size" on buttons, a last-built date in the footer.

## Editions (11, from `content/editions.yaml`)
- **Featured:** `ethiopian-tewahedo` (the deepest, 87-book canon).
- **Standalone Bibles:** `standalone-geez`, `standalone-amharic` (⚠ no cover art yet — Phase 2 generates typographic covers; English back-translation is an *in-edition* reading aid, NOT a separate EPUB → 11 cards, not 12).
- **Study editions (8):** catholic-study · coptic-orthodox · eastern-orthodox · anglican-bcp · evangelical-reformed · lutheran-confessional · jewish-study · scholarly-academic.

## Tech plan
Plain hand-written `index.html` + `style.css` (+ tiny `i18n.js` in Phase 2) — no SSG (zero Node/npm toolchain for a first-time maintainer). To avoid hand-duplicating 11 cards, a small **`scripts/build_site.py`** reads `editions.yaml` + a `site_copy.yaml` (en/am/gez strings) and emits the page; it also (1) makes ~400px cover thumbnails with Pillow, (2) reads each EPUB's byte size for the "Download EPUB · NN MB" label, (3) computes SHA-256. **EPUBs are never committed to git** (produced at deploy time, ~16–25 MB each). Deploy via a `pages` stage in `.gitlab-ci.yml`; Spaceship DNS (apex + `www` → GitLab Pages + TXT verify, Let's Encrypt). GitHub Pages = warm `*.github.io` mirror.

## Build sequence
- **Phase 0 — Export named EPUBs (BLOCKER).** `exports/` currently has only 4 hash-named cache blobs; emit `exports/epub/<id>.epub` for all 11 ids via the build pipeline before downloads can be wired.
- **Phase 1 — Clickable prototype. ✅ DONE** (`website/index.html` + `style.css`, placeholder covers/sizes, served + reviewed).
- **Phase 2 — Assets + look.** Self-host Noto Serif/Sans Ethiopic + Latin woff2 (`unicode-range`); generate the 2 missing typographic covers; wire `i18n.js` (lang toggle, English fallback no-JS).
- **Phase 3 — Generator.** Convert the hand-HTML into `build_site.py` (reads `editions.yaml` + `site_copy.yaml`); diff output vs the prototype for parity.
- **Phase 4 — Wire real downloads.** Copy `exports/epub/<id>.epub` → `website/public/downloads/`; verify all 11 buttons (keyboard, right-click Save-As, no-JS).
- **Phase 5 — Deploy.** `pages` CI stage; Spaceship DNS + HTTPS; confirm `yhwhyaway.com` serves + downloads over TLS; GitHub mirror.
- **Phase 6 — A11y QA.** axe/Lighthouse + screen-reader + real-device Ethiopic glyph + Kobo/Apple Books open test (batched; partly needs the user's devices).

## Accessibility (WCAG 2.2 AA — locked)
One `<h1>`, `<h2>` per section, `<h3>` per card; semantic landmarks; skip-link. Contrast ≥4.5:1 (verified on the palette). Full keyboard; visible `:focus-visible`. **Card contract (non-negotiable):** `<h3>` title + a real `<a download>` inside + `sr-only` edition name for unique link text + a stretched `::after` for whole-card click — NOT a card-wrapping anchor. Covers get meaningful `alt`. ⚠ **Geʽez + Amharic are LTR, not RTL** — only `lang` changes (`en`/`am`/`gez`, hyphens), never `dir="rtl"`. `prefers-reduced-motion` honored.

## Open decisions (for the user; sensible defaults in parens)
1. ~~Visual direction~~ — **DECIDED: manuscript-reverent.**
2. ~~Edition lineup~~ — **RESOLVED: 11 editions; English back-translation is in-edition, not a separate download.**
3. Two missing covers (geez/amharic): approve typographic placeholder covers on an oxblood field to match the leather set? (default: yes)
4. Canonical host: GitLab Pages primary, GitHub mirror? canonical `www.yhwhyaway.com` with apex redirect? (default: yes / www-canonical)
5. DNS: Claude drives Spaceship via Chrome MCP for apex/www + GitLab TXT, or the user pastes records? (default: Claude drives, per the "take over the sites" ask)
6. Footer support link: include a single quiet optional link, or omit for a clean no-commerce stance? (default: omit at launch)
7. Per-edition SHA-256 + "What's inside" canon/source-date copy: expose checksums? supply the per-edition canon text (or pull from `content/source_dates.yaml`)? (default: expose checksums)
8. Geʽez UI scope: full Geʽez UI strings, or reverent headings + scripture labels with English fallback? (default: headings/labels only; Amharic gets full UI)

## Reference — chosen landing-page wireframe (manuscript-reverent)
```
+--------------------------------------------------------------+
| [skip to downloads]                  EN | አማርኛ | ግዕዝ        |
| YHWH  ✛ ኪዳን                                                  |
+--------------------------------------------------------------+
|                          ✛  (processional cross)             |
|                         Y H W H                              |
|        The Ethiopian Tewahedo Bible — free to all            |
|   Public-domain sources, CC0. Geʽez · Amharic · English.     |
|   No cost. No signup. No tracking.                           |
|            [  Browse the editions  v  ]                      |
|==============================================================|
|  ─────────────── FEATURED EDITION ─────────────────          |
|  | [cover] The Ethiopian Tewahedo Study Bible · 87 books  |  |
|  |         [ Download EPUB — 24 MB ]                      |  |
|  ──────────── STANDALONE BIBLES ──────────────               |
|  | [cv] Geʽez Bible |  | [cv] Amharic Bible |               |
|  ────────── TRADITION STUDY EDITIONS (×8) ─────────          |
|  Which is for me? Pick the tradition you read in.            |
|  [Cath.][Coptic][E.Orth][Angl.] [Reform][Jewish][Luth.][Sch.]|
|==============================================================|
|  HOW TO READ — Apple Books · Kobo · Android · Desktop        |
|  ABOUT & THE FAITH — built from PD texts; CC0; reverent      |
|  LICENSE: CC0 1.0 + attribution · SHA-256 per edition ▸      |
+--------------------------------------------------------------+
|  ✛  No tracking. No cost.  ·  GitLab / GitHub mirror         |
+--------------------------------------------------------------+
```
Full research (a11y/i18n/download-UX patterns) + all 3 explored directions: workflow `wf_a8cbf1ad-eb5`.
