# YHWH Ya' Way

A free, **local** desktop app for building **custom study Bibles**. Start from
the Ethiopian Tewahedo 83-book superset (tens of thousands of study notes,
multi-language verse popups), pick a tradition, choose which note kinds and
books to include, theme it, and export a standards-clean EPUB — all on your own
machine. No account, no server, no cloud.

> **Status:** v0.1.0 (public beta, live) — single-user local app. The program is
> © 2026 Bogdan Zorlescu (all rights reserved); the incorporated Bible texts are
> public-domain / CC. See [Licensing & attributions](#licensing--attributions).

## What you get

- **Two standalone Geʽez &amp; Amharic Bibles** *(in progress)* — transcribed
  directly from the manuscripts, each with a faithful English back-translation.
  The project's distinctive heart.
- **9 built-in study editions across 5 canon shapes** — Ethiopian Tewahedo,
  Catholic, Eastern &amp; Coptic Orthodox, Anglican, Lutheran, Reformed, and
  Jewish/Tanakh — each a filtered view of the one 83-book superset.
- **91,553 study notes** (cross-references, Strong's Hebrew/Greek, patristic
  commentary, Nave's Topical, Easton's Dictionary, …) that you toggle on or off
  per edition.
- **Original-language verse popups** — Hebrew (WLC), Greek (LXX + Byzantine NT),
  Latin (Clementine Vulgate), and Arabic (Van Dyck), chosen per edition.
- A **wizard** plus customize / preview consoles, so a non-technical builder can
  produce their own edition without editing YAML or touching a CLI.
- Output is a standards-clean **EPUB 3** (epubcheck reports 0 errors / 0
  warnings on every edition).

## Quick start — use it

**Desktop app:** download the build for your system from the
[latest release](https://github.com/gringoboggy/yhwh-bible-platform/releases/latest)
— Windows (`.exe` installer), macOS (`.dmg`), or Linux (`.AppImage`) — and run
it. The app opens in its own window; a first-run welcome guides you to the
wizard. No Python required.

> Want to build that release artifact yourself? See
> [Packaging the desktop app](#packaging-the-desktop-app).

## Run from source (developers)

Requires **Python 3.14+**.

```bash
pip install -r requirements.txt     # one runtime dependency (PyYAML)
python scripts/launcher.py          # opens the UI (native window, or browser)
```

Then open **`/wizard`** and build your first edition (below). To run only the
local web server (no desktop shell):

```bash
python -m scripts.web               # serves http://127.0.0.1:8765/
```

## Build an edition (the core flow)

1. Open **`/wizard`**.
2. Pick a starting edition (e.g. "Catholic Study Bible").
3. Step through the cards: start-from → branding → theme → content (canon +
   note kinds) → traditions → review → **Build**.
4. Click **Build** — a themed EPUB downloads carrying only the notes you picked
   and verse popups in the languages you chose.

Power users can drive the same pipeline from the CLI:

```bash
./ebible build <edition-id>         # build one edition
make build                          # full pipeline: all editions + validation
```

## Developer workflows

Everything routes through the unified **`./ebible`** CLI (or `make`):

| Command | What it does |
|---|---|
| `make status` | corpus + edition snapshot |
| `make build` | source notes → master HTML → editions → validate |
| `make test` | run the test suite |
| `make ship` | the ship-check integrity gate |
| `make ship-full` | ship-check + epubcheck (needs a JRE on PATH) |
| `make audit` | code-quality gate (vulture / mypy / pip-audit) |
| `make commit-ready` | ship-check + tests — run before committing |

On Windows, tests need UTF-8: `set PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8=1`).

## Packaging the desktop app

```bash
pip install -r dev/requirements-desktop.txt   # pinned pyinstaller + pywebview
pyinstaller dev/launcher.spec                  # → a frozen Windows app (~400 MB)
```

The frozen binary bundles the corpus + base EPUB HTML and writes built EPUBs to
a persistent per-user data dir (override with the **`YHWH_DATA_DIR`** env var,
e.g. a roomier drive). A hard concurrent-build cap
(**`YHWH_MAX_CONCURRENT_BUILDS`**, default 1) protects local resources. Smoke-
test a frozen build end-to-end with `python dev/smoke_desktop.py`.

## Project map

| Doc | Purpose |
|---|---|
| [`dev/CLAUDE_PROJECT_RULES.md`](dev/CLAUDE_PROJECT_RULES.md) | rules + conventions (read first) |
| [`dev/SESSION_STATE.md`](dev/SESSION_STATE.md) | current state — what shipped, what's next |
| [`dev/REPO_MAP.md`](dev/REPO_MAP.md) | file / folder index |
| [`dev/MATRIX_MAP.md`](dev/MATRIX_MAP.md) | data flow: config → loaders → matrix → build |
| [`scripts/README.md`](scripts/README.md) | CLI tool reference |
| `HANDOFF_README_v7.md` | deep architecture context |

## Licensing & attributions

- **Program:** © 2026 Bogdan Zorlescu. All rights reserved. See [`LICENSE`](LICENSE).
- **Bible texts:** public-domain / CC sources (WEB, KJV, WLC Hebrew, LXX-Swete
  Greek, Byzantine NT, Clementine Vulgate, Douay-Rheims, JPS 1917, Van Dyck
  Arabic, …). Per-source provenance:
  [`content/sources/ATTRIBUTIONS.md`](content/sources/ATTRIBUTIONS.md).
- **Commentary / reference corpora:** public-domain (Nave's Topical, Easton's
  Dictionary, TSK, patristic sources) — documented in the same file.
- **Cover templates** (25 designs): the publisher's own Midjourney-generated art
  + a hue-shift pipeline —
  [`content/covers/templates/README.md`](content/covers/templates/README.md).
- **Per-book cover art:** the publisher's curated set —
  [`content/covers/_book_defaults/README.md`](content/covers/_book_defaults/README.md).
- **Fonts:** SIL Open Font License 1.1 only —
  [`content/assets/fonts/LICENSES.md`](content/assets/fonts/LICENSES.md).

## Support the work

YHWH Ya' Way is free — no paywall, no account, no tracking.

Support is optional and funds continued work, especially the transcription of the
standalone **Geʽez &amp; Amharic Bibles** from the manuscripts. It doesn't unlock
anything.

- **Ko-fi** — https://ko-fi.com/gringoboggy
- **PayPal** — https://paypal.me/gringoboggy
- **GitHub Sponsors** — https://github.com/sponsors/gringoboggy

GitHub and GitLab also show a **Sponsor** button on this repository, configured
in [`.github/FUNDING.yml`](.github/FUNDING.yml).

## Notes

- **Remotes:** the repository is mirrored to GitLab and GitHub; history is also
  backed up off-machine via `git bundle --all`.
- Large image assets (~159 MB of cover templates) are committed directly; Git
  LFS is **not** currently configured (a future option if repo size grows).
- **Secrets:** keep any API keys in `.env` (gitignored); never commit them.
