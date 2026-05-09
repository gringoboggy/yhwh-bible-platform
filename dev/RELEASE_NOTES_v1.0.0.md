# Release notes — v1.0.0

**Date:** 2026-05-09
**Status:** prep complete; tagging is user-side
**Tag command:** `git tag -a v1.0.0 -m "v1.0.0 — first commercial release candidate" && git push origin v1.0.0`
**Prior:** the session-handoff metadata file `VERSION` (originally
a free-form snapshot from the v2.2 era) is now the canonical
semver source for build tooling. Line 1 is the version string;
everything below is metadata.

---

## What v1.0.0 is

The YHWH Bible Publishing Platform — a desktop application for
non-technical publishers (parish priests, schoolteachers, lay
editors, retail imprints) to produce study Bibles tuned for their
tradition + audience without learning a CLI, build pipeline, or
YAML editor.

The buyer demo, end-to-end:

  1. Open `/wizard`
  2. "Make a Catholic study Bible" (or pick another tradition,
     or start from one of 7 starter-pack templates)
  3. Step through ~8 cards: canon, kinds, theme, publisher meta,
     per-note tweaks, popup languages, traditions, preview
  4. Click BUILD → an EPUB downloads with the publisher's imprint,
     ISBN, copyright, theme, tradition stack, only their picked
     notes, and verse popups in the languages they configured

That demo works. v1.0.0 is the first release where it's
commercially shippable.

---

## Headline numbers

| Metric | v1.0.0 |
|---|---|
| **Notes in corpus** | 51,394 (2× the v1.0 floor; ~150% of original 35K target) |
| **Books in canon (Ethiopian Tewahedo flagship)** | 87 |
| **Built-in editions** | 9 |
| **Starter-pack templates** | 7 |
| **Web consoles** | 13 |
| **Tests** | 1048 (all passing) |
| **Linter checks** | 11/11 (cross-link, encoder order, plan coherence, atomic writes, external HTTP, …) |
| **Lint compliance** | 100% — all 11 checks clean per save |

---

## What ships in v1.0.0

### Buyer-facing

- **13 web consoles** sharing one design-system source of truth
  for cross-link nav + buyer-arc polish CSS (focus rings, 150ms
  transitions, click feedback, dirty-state pill, step fade-in
  keyframe). 12 fully unified; the 13th (`/index` note editor)
  intentionally has its own dark-mode layout.
- **9 built-in editions** spanning every major Christian +
  Jewish tradition's expected canon + apparatus:
    - ethiopian-tewahedo (Ethiopian Orthodox / 87 books)
    - catholic-study (Roman Catholic / 76 books)
    - evangelical-reformed (Protestant / 66 books)
    - jewish-study (Tanakh / 39 books)
    - scholarly-academic (full apparatus / 87 books)
    - eastern-orthodox (Greek / Russian / Antiochian Orthodox / 78 books)
    - anglican-bcp (Anglican / Episcopal BCP / 76 books)
    - lutheran-confessional (LCMS / WELS / ELS / ILC / 66 books)
    - coptic-orthodox (Coptic Orthodox / 87 books)
- **7 starter-pack templates** for clone-and-tweak via the
  wizard: monastic-daily-office, school-friendly-nrsv, children,
  family-devotional, scholarly-academic-with-apparatus,
  anglican-bcp (mirror), lutheran-confessional (mirror).
- **Cross-denominational compare apparatus (ψ.8)** — the v1.0
  differentiator. A single popup, hovering one verse, shows
  editorial notes from every tradition the publisher chose to
  include (Catholic, Protestant, Eastern Orthodox, Jewish,
  Tewahedo, plus a denominationally-neutral "Cross-tradition"
  bucket for linguistic + structural notes).
- **Reader-EPUB polish (ψ.17)** — drop caps, subtle verse-number
  treatment, chapter heading rhythm, @page margins for print
  readers / Calibre / Apple Books PDF export. Every theme
  inherits the polish without overriding distinctive character.
- **Per-edition customization** of: title, ISBN, copyright,
  publisher imprint, cover image (upload OR text-on-gradient via
  the wizard), themes (5), kinds (63 across 14 categories),
  popup translations + languages (per-edition default + per-book
  override), traditions (per-edition default + per-book override),
  reader experience (chapter number format + decoration + ToC
  ornament + ToC dropdown behavior), and per-note disable
  toggles.
- **Matrix sidebar (ψ.18 / ψ.18.1)** — at-a-glance corpus density
  visualization on `/matrix`. Per-symbol totals + per-book
  sparklines + click-to-expand chapter drilldown showing top-5
  books with full-width per-chapter density. Live-updates as
  you toggle kinds.

### Operator-facing

- **Cross-link invariant** enforced by lint check 6.2 — every
  console links to every other (12 of 13 consoles; /index
  exempt by design).
- **Plan-coherence linter** (ω.15) — verifies every PLAN-claimed-
  shipped phase has a CHANGELOG entry, every PLAN-open phase has
  not yet shipped, every Depends: reference resolves to a known
  phase id.
- **In-flight task tracker** (`dev/IN_FLIGHT.md`) with
  TRACKER-STATE marker — survives compaction; future-Claude
  knows immediately if work was open mid-stream.
- **Atomic-write audit** (ω.9) + **external-HTTP audit** (ω.10) +
  **input-validation foundation** (ξ.1) + **path-traversal
  hardening** (ξ.2) + **XSS prevention sweep** (ξ.4).
- **Snapshot / restore** flow — backups via
  `notes_io.ensure_backup`, recoverable from any operator
  console.
- **Build-all editions** with per-edition success/fail reporting
  + zip download (failures don't abort the batch).
- **Save = git push** to a private GitHub repo with pre-commit
  hook running the 11-check linter.

### Infrastructure

- **Desktop binary chain (θ.1 + θ.2 + θ.3 + θ.4)**:
    - PyInstaller launcher (`scripts/launcher.py` +
      `dev/launcher.spec`)
    - PyWebView native shell (auto-selects when frozen + pywebview
      importable; falls back to browser otherwise)
    - Sparkle (macOS) / WinSparkle (Windows) data plane —
      appcast generator + parser + version comparator
    - DMG / Inno Setup / AppImage builders with optional code-
      signing (Apple Dev ID / Authenticode)
- **Per-user data location resolver (ω.5)** —
  `scripts/core/paths.py` resolves content/ to in-tree (dev) or
  `user_data_dir()/YHWH/content/` (installed). One-shot migration
  helper bootstraps existing in-tree content into user data on
  first run of an installed binary.
- **AI cross-reference detector** (χ-AI-xrefs, infrastructure
  shipped) — Anthropic SDK-backed thematic xref proposals via
  Haiku 4.5 with prompt caching. Cost-gated (~$72 for full 31K-
  verse pass); user opts in per session.

---

## Distribution

v1.0.0 ships **unsigned binaries by default**. Signed
distribution is opt-in via env vars:

  - **macOS DMG** (`./dev/build_dmg.sh`) — set
    `CODESIGN_IDENTITY` + `NOTARIZE_KEYCHAIN_PROFILE` for signed
    + notarized distribution. **Apple Developer ID Application**
    cert ($99/yr) required.
  - **Windows installer** (`dev/build_msi.cmd`) — uncomment
    `SignTool=` in `dev/installer.iss`. **Authenticode cert**
    ($200-400/yr) required.
  - **Linux AppImage** (`./dev/build_appimage.sh`) — no signing
    required.

Unsigned macOS / Windows builds run fine for personal / dev use;
Gatekeeper / SmartScreen will warn first-time users on
download. Signing removes the warning.

---

## What's user-side after the v1.0.0 tag

The release tag itself is one git command (see top of this file).
Beyond that:

  - **Build per-platform binaries** for distribution:
    ```
    pip install pyinstaller pywebview
    pyinstaller dev/launcher.spec     # → dist/YHWH.{exe,app}
    ./dev/build_dmg.sh                # macOS DMG
    dev\build_msi.cmd                 # Windows installer (needs Inno Setup 6)
    ./dev/build_appimage.sh           # Linux AppImage
    ```
  - **Visual QA** the 13 consoles in a browser + a built EPUB
    in Apple Books / Calibre / Kobo / Kindle. Sign off or file
    `v1.0.1` patch fixes.
  - **(Optional, paid)** Run `χ-AI-xrefs` for ~$72 to add
    ~5K thematic xref-* notes via Anthropic Haiku 4.5.
  - **(Optional, paid)** Acquire Apple Developer ID +
    Authenticode certs for signed distribution.

---

## What's NOT in v1.0.0 (v1.x roadmap highlights)

The plan tracks 84 open phases organized into 7 tracks (RELEASE,
SHORT, MEDIUM, LONG, HARDENING, USER-SIDE, PARKED). Full ledger
in `dev/PLAN_2026-05-09.md` §7. Highlight set:

| Track | Phase | What it adds |
|---|---|---|
| SHORT | ψ.18.2 | Matrix per-chapter expand-all (long tail beyond top-5 books) |
| SHORT | ψ.20 | Note-density heat-map on /matrix |
| SHORT | ψ.21 | One-click 5-chapter PDF sample export |
| SHORT | υ.3 | Search across editions in /sources |
| SHORT | υ.8 | Verse-of-the-day JSON / RSS feed |
| MEDIUM | ψ.1 | Live EPUB preview (the biggest "wow" upgrade) |
| MEDIUM | ρ.1 | LibriVox audio-augmented EPUBs |
| MEDIUM | χ.2-5 | Matthew Henry / Calvin / Catena Aurea / Rashi commentaries |
| MEDIUM | ψ.19 | Reading plans (chronological / one-year / lectionary) |
| MEDIUM | ω.16 | Edition snapshots (immutable v-tagged retail snapshots) |
| MEDIUM | π.6 | Cover designer (text + gradient + font) |
| LONG | χ-AI-notes | AI-augmented build-time note generation |
| LONG | ψ.22 | Multi-format export (PDF / MOBI / HTML / TXT) |
| LONG | θ.5 | Localized UI (Spanish / Portuguese / French / German) |

84 total open phases plus 5 parked (design call needed) plus 5
indefinitely deferred (with rationale). See PLAN §7 for the
complete ledger.

---

## Acknowledgements

Built collaboratively over the course of the YHWH-v2.4 session
arc. Public-domain source data: TSK (cross-references), Strong's
Hebrew + Greek (lexicons), Nave's Topical (topic-nave),
Kenyon's *The Text of the Greek Bible* (textual criticism),
ebible.org (translations), openscriptures (Strong's), Berean
Interlinear Bible (alignment data, deferred).

Tooling: Python 3.13 standard library + a curated short list of
external dependencies (PyInstaller + PyWebView for the desktop
binary, Anthropic SDK for the AI detectors, weasyprint pinned
for ψ.21+ PDF generation, watchdog for ω.21 watch mode). No
front-end build pipeline; Tailwind via CDN.
