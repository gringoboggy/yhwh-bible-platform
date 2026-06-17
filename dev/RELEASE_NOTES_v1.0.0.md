# Release notes — v1.0.0

**Status:** prep; the v1.0.0 tag is user-side. Current released build is **v0.1.0**.
**Project:** YHWH Ya' Way — a free, non-commercial Bible-publishing app.
**Rights:** © 2026 Bogdan Zorlescu. All rights reserved / source-available (see `LICENSE`).
**Tag command (user runs it):**
`git tag -a v1.0.0 -m "v1.0.0" && git push origin v1.0.0 && git push github v1.0.0`

> This file was rewritten 2026-06-14 to current reality. The pre-2026-05-14
> version described a commercial product (buyer/ISBN/retail framing); that is
> gone. The project is free and non-commercial — no sale, no account, no
> tracking. Earlier headline numbers (51,394 notes / 87 books / 13 consoles)
> were also stale.

---

## What v1.0.0 is

A desktop application that lets a non-technical editor — a parish priest, a
schoolteacher, a lay editor — produce a study Bible tuned to their tradition and
audience, without touching a CLI, a build pipeline, or a YAML file. The output is
a free EPUB the maker can read, share, or hand out. Nothing is for sale.

The builder demo, end to end:

  1. Open `/wizard`.
  2. Pick a starting edition (e.g. a Catholic study Bible) or a starter-pack template.
  3. Step through the cards: canon, note kinds, theme, branding, popup languages,
     traditions, review.
  4. Click **BUILD** → an EPUB downloads with the chosen theme, only the picked
     notes, and verse popups in the configured languages.

v1.0.0 is the first release where that demo is release-quality.

---

## Headline numbers

| Metric | v1.0.0 |
|---|---|
| Notes in the corpus | **91,720** (the deepest free Bible apparatus we know of) |
| Books in the flagship Ethiopian Tewahedo canon | **83** (the shipped superset all other editions filter from) |
| Built-in canon editions | **9** (+ 2 standalone Bibles in progress) |
| Web consoles | **21** |
| Automated tests | **8,000+**, run on every push (GitHub Actions) |

The corpus is drawn entirely from public-domain sources via a
prospect → promote pipeline plus reference-corpus ingestion. Other editions are
canon/kind subsets of the Ethiopian Tewahedo superset; their counts fall out of
filtering automatically.

---

## What ships in v1.0.0

### For the maker

- **9 built-in editions** spanning the major Christian and Jewish traditions'
  expected canon + apparatus: Ethiopian Orthodox (Tewahedo), Roman Catholic,
  Protestant (Reformed/Evangelical), Tanakh (Jewish), full scholarly apparatus,
  Eastern Orthodox, Anglican (BCP), Lutheran (confessional), and Coptic Orthodox.
- **Starter-pack templates** for clone-and-tweak via the wizard (daily office,
  school-friendly, children, family devotional, scholarly, and tradition mirrors).
- **Cross-denominational compare apparatus** — one popup over a verse shows the
  editorial notes from every tradition the maker chose to include, plus a neutral
  cross-tradition bucket for linguistic and structural notes.
- **Reader-EPUB polish** — drop caps, restrained verse numbering, chapter-heading
  rhythm, and print/`@page` margins; every theme inherits it without losing its
  character.
- **Per-edition customization** of title, branding/imprint, cover (upload or
  text-on-gradient), themes, note kinds, popup translations + languages
  (per-edition default and per-book override), traditions, and reader experience
  (chapter-number format, decoration, table-of-contents behavior), plus per-note
  disable toggles.
- **Matrix + build-tracker consoles** — at-a-glance corpus density and a live view
  of exactly what the current edition will contain before BUILD is clicked.

### Distribution (free downloads)

- **Website format matrix** — every edition is offered in multiple formats and
  cover colours from the site. The general-purpose ("everywhere") and Apple Books
  columns are **live**; the Kobo/e-ink, Kindle, and Google Play columns are in
  progress (see *Known limitations*).
- **Desktop binaries**, all built from source:
  - **Windows** — `.exe`, Authenticode-signed (Azure Trusted Signing).
  - **macOS** — `.dmg`, Apple-notarized and stapled.
  - **Linux** — `.AppImage` (unsigned by design).
- **Kindle** is delivered the free way: the maker downloads the EPUB and sends it
  to their own device via **Send-to-Kindle** — we do **not** publish to the Kindle
  Store. (The Send-to-Kindle path is still being finalized; see below.)

### Under the hood

- One standard-library backend (no Flask/Django), Tailwind via CDN, no front-end
  build step. Data lives as readable, git-diffable Python tuples and YAML — no
  database.
- A drift-guard system (per-turn audit, an in-flight tracker, and a continuous
  linter) keeps the docs, plan, and corpus honest across sessions.
- Desktop packaging via PyInstaller + a native window shell, with a privacy-clean
  update channel (adoption signal only; no telemetry, no install IDs, no phone-home).

---

## What is NOT in v1.0.0

- **No commercial surface.** No ISBN, no sale, no print-on-demand, no store
  metadata. Multi-format export survives only as a free download option.
- **No account, no tracking, no telemetry.**
- **In progress (not yet final):**
  - The two **standalone Ge'ez and Amharic Bibles** (own-versified text with a
    faithful English back-translation in their own popups) — partway: the Ge'ez
    standalone ships several books today; the rest trail their own reviewed lane.
  - The **Kindle** distribution column — the Send-to-Kindle delivery of the
    full-apparatus EPUB is not yet confirmed on a real device; it is being worked
    against the actual Send-to-Kindle channel, not a publishing dashboard.
  - The **Kobo/e-ink** and **Google Play** columns — pending final device QA.
- Opportunistic corpus depth (additional public-domain commentaries, AI
  cross-references) continues after v1.0.0; it is not a release gate.

---

## What's user-side after the tag

1. Apply the tag (command at the top).
2. Re-cut and re-sign the per-platform binaries for the new version
   (`dev/build_dmg.sh`, `dev/build_desktop.*` / `dev/sign_windows.ps1`,
   `dev/build_appimage.sh`), attach them to the release, and merge their SHA-256
   sums into `SHA256SUMS.txt`.
3. Deploy the website (the format-matrix catalog regenerates from the release).
4. Final real-device visual QA on the e-ink reader and reader apps.

---

## Acknowledgements

Built collaboratively over the YHWH v2.4 session arc. Public-domain source data:
the Treasury of Scripture Knowledge (cross-references), Strong's Hebrew + Greek
lexicons, Nave's Topical Bible, Kenyon's *The Text of the Greek Bible* (textual
criticism), Torrey's topical apparatus, ebible.org and openscriptures
(translations + lexical data), and the patristic chorus of the Ethiopian
commentary corpus. Tooling: the Python standard library plus a short, curated
dependency list; Tailwind via CDN; no front-end build pipeline.
