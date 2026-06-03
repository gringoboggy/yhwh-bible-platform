---
holder: mac
from: windows
turn: 3
updated: 2026-06-03T17:51:10Z
status: working
---

## Done (turn 3, mac lane — this session)
- **Public presence set up end-to-end via Playwright-MCP browser automation:**
  - **GitHub** — profile name/bio/URL/location/timezone + GitLab social link, uploaded **avatar** (gold እግዚአብሔር), pinned **profile README** repo (`gringoboggy/gringoboggy`).
  - **GitLab** — profile bio, **made public**, GitHub link, job title, www URL, avatar + status "Building yhwhyaway.com"; project description/topics/wiki/avatar (via API).
  - **GitHub Sponsors** — rewrote short bio + introduction, opted-in to be featured, published **5 monthly tiers $1–$5 ("Sustainer", same reward)**. Stripe/bank/tax were already done; profile is **pending GitHub staff review**.
- **Brand assets** (`brand/`): 1280×630 social card, square avatar, favicon (32/180/512) rendered via Chrome from EB-Garamond / Noto-Serif-Ethiopic; reproducible `sources/` + **`BIOS.md`** (per-surface bios + domain email `gringo.boggy@yhwhyaway.com`, `paypal.me/gringoboggy`, `ko-fi.com/gringoboggy`). Wired OG card + favicons into `website/index.html`.
- **Tooling:** installed **Node LTS** (no-sudo, `~/.local`) + **Playwright MCP** (drives installed Chrome, persistent profile) on Mac — see [[reference_browser_automation_mac]].
- **Pulled + rebased Windows turn-2** (`8b6cb947` 1sa 1–17 folio map · `683bf66e` monetization plan · `34aabec9`); file-disjoint, clean linear history.

## Next (turn 3 continues / next session)
- **Mac (website lane):** website repo (`gringoboggy.github.io`) + GitHub Pages + custom domain — *re-confirm before creating the public repo*; **Spaceship DNS** (needs user's API key + secret); wire support links (GitHub Sponsors / PayPal / Ko-fi) + `.github/FUNDING.yml`; rebuild site content + `build_site.py` + Pages deploy.
- **Windows (P0 critical path):** continue folio-mapping **1sa 18–31 → 2sa 1–24 → 1ki 7–22 → 2ki 1–25** — READ `content/manuscript/_reviewer_context/SAMKINGS_FOLIO_ANCHOR_INDEX.md` first; CAM needs CUDL-IIIF acquire for most remaining folios.

## Watch-outs
- **Baton held by `mac` (status: working).** If a fresh session is Windows, `/resume --force` after confirming Mac is idle.
- ⚠ CAM on-disk filename `_1SamN_` suffixes are ~+3 shifted — map by the penned FOLIO number, not the suffix.
- ⚠ (Mac OCR) tests via Claude Bash need `export TMPDIR=/Volumes/MacHD2/<dir>`.
