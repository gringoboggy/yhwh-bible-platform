---
holder: mac
from: windows
turn: 5
updated: 2026-06-03
status: idle
---

## Done (this round — BOTH lanes wrapped, file-disjoint)

**Windows lane (turn 4) — P0:**
- **1 SAMUEL COMPLETE (all 31 ch, both witnesses).** Added 1sa 18–31 (GG companion pass + CAM pass, incl. the first **CUDL-IIIF acquire** of CAM f114r–f117v). Recension: GG (LXX) omits 18:1–5; CAM (MT-fuller) ch18 = 18:1 covenant; 1 Samuel ends mid-folio (GG f017v / CAM f117r), 2 Samuel 1 immediately after. `samuel/manifest.yaml` 1sa 1–31 filled (boundary-generous, status `pending`); anchor index §14 added. Gate: image-existence GREEN; samuel has-folios only 2sa pending (23). Commits `ab86dd87` + `f668218d`. Also documented Mac's `brand/` in `REPO_MAP.md`.

**Mac lane (turn 3 + this wrap) — public presence + payments, set up END-TO-END via Playwright-MCP browser automation** (external state; repo changes = brand assets + community-health files only):
- **GitHub** — profile (name/bio/URL/Ontario/Eastern TZ/GitLab link) + **avatar** (gold እግዚአብሔር) + pinned **profile README** repo `gringoboggy/gringoboggy` (public, has FUNDING.yml). **Sponsors**: profile copy + opt-in featured + **5 monthly tiers $1–$5 "Sustainer"** published → **PENDING GitHub staff review** (Stripe/bank/tax already done).
- **GitLab** — profile bio, **made public**, GitHub link, job title, www URL, avatar, status; project metadata (API).
- **X (@GringoBoggy)** — name "YHWH Ya' Way", bio, **avatar + 1500×500 header**, location, website; **intro post LIVE** (status 2062249007703843193).
- **Ko-fi (ko-fi.com/gringoboggy)** — name, avatar, About bio, **3:1 cover**, website→github link, **page intro**, $3 tip box. (No GitHub social connector on Ko-fi.)
- **Stripe** — descriptor/business-desc are GitHub-platform-controlled for Sponsors Express → nothing user-editable; the Sponsors profile IS the public bio. Handled.
- **Spaceship API** — ONE key `yhwhproj-dns` (id `kJ2qURJgxDj7BS2j9G7E`) **scoped to DNS-only** (Async/Read + DNS R/W + Domains Read/Write; Contacts/Billing/Transfer/SellerHub OFF). Secret in use = **`dnsissue`** (other secret = `spacekey`). Creds at **`~/.config/yhwh/spaceship.env`** (chmod 600, outside repo). Verified domains + dns-records reads → HTTP 200. Permission edits are **passkey-gated** (user-only).
- **Repo files (committed):** root `SECURITY.md` (report → gringo.boggy@yhwhyaway.com) + `.github/FUNDING.yml` (Sponsors/Ko-fi/PayPal) + `brand/x-header.png` (+ source). Brand kit + `brand/BIOS.md` earlier (`b7f5eed3`).
- **Handles:** GitHub `gringoboggy` · X `@GringoBoggy` · Ko-fi `ko-fi.com/gringoboggy` · PayPal `paypal.me/gringoboggy` · Sponsors (pending) · email **gringo.boggy@yhwhyaway.com**.

## Next

**Windows (P0 critical path):**
- **2 Samuel (1–10, 12–24).** READ `content/manuscript/_reviewer_context/SAMKINGS_FOLIO_ANCHOR_INDEX.md` FIRST (§9 = 2sa unique-event table). GG on disk: `GAPS/1_Samuel/GG-00106/2-Samuel/2-Samuel_f017v…f028v.jpg`. **CAM needs CUDL-IIIF acquire** past f117 (`scripts/acquire_cudl_master.py` with `$env:PYTHONPATH=<repo>`; anchor f106r=view215, 2 views/leaf; verify each by penned recto number). 2sa 11 calibrated (CAM f120r/v). Then 1ki 7–22 → 2ki 1–25. MAX-1 heavy vision; sub-batch check-ins; manifest gate per batch.

**Mac (website phase — option A "ship early"):**
- **Website**: publish the Phase-1 shell at **yhwhyaway.com** (ship now, iterate live). Needs public **`gringoboggy.github.io`** repo + GitHub Pages + custom domain → **then write Spaceship DNS** (apex A/AAAA + www CNAME) with the DNS-only key (ready). RE-CONFIRM before creating the public repo.
- **Site content:** links/handles footer · feedback/suggestions (form or mailto) · public **dev-notes/roadmap page** (funding tie-in: "with sponsorship → render ALL manuscripts online + paid sources").
- **Pre-release v0.x** of the builder: distribution that doesn't expose the main repo's commit history/emails (clean public release OR packaged download). **Before pre-release: set the .exe program icon** (user has assets/sizes ready → Windows build/PyInstaller).
- **After pre-release:** first Ko-fi feed post + X launch post. Optional later: GitHub repo social-preview upload.

## Watch-outs
- **Baton: `mac`, status idle** — both lanes' work this round is committed + pushed (GitLab + GitHub). A fresh **mac** session continues the website phase; a **windows** session continues 2 Samuel — file-disjoint, so either can `/resume --force` if it sees the other as holder.
- **Browser automation (mac):** Playwright MCP server was killed to free RAM (respawns on next browser tool call / reconnect). Persistent login profile `~/.yhwh-browser-profile` keeps GitHub/GitLab/X/Ko-fi/Spaceship sessions.
- ⚠ CAM on-disk filename `_1SamN_` suffixes are ~+3 shifted — map by penned FOLIO number (newly-acquired f114r+ are correctly named).
- ⚠ `acquire_cudl_master.py` needs `$env:PYTHONPATH=<repo>` (imports `scripts.core`).
- ⚠ (Mac) tests via Claude Bash need `export TMPDIR=/Volumes/MacHD2/<dir>`.
