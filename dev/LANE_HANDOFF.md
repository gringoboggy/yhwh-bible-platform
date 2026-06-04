---
holder: windows
from: mac
turn: 7
updated: 2026-06-03
status: active
---

## ⚠ Windows → Mac (turn 7, 2026-06-03) — Windows STEPPED INTO THE WEBSITE LANE (user-directed). Sync before any website work.

While you (Mac) were idle, the user had Windows edit the site copy, redeploy, and fix the HTTPS setting. **Do these in order before touching the website again:**

1. **`git pull` the MAIN repo.** Windows edited `website/src/index.html`: (a) **deleted** the "An honest word on how it works" per-book-limitation callout (user: "that note has to go"), and (b) **rewrote the hero creed** (`<p class="mission creed">`) into tightened copy — it was the user's own raw words and they wanted it de-quoted/tightened. New creed = "Everything for studying Scripture belongs in one place … come to Him *in your own way*, with a Bible you've shaped yourself." These ride in Windows' wind-down commit on `main`.
2. **★ PULL / RE-CLONE YOUR PUBLISH COPY BEFORE YOU DEPLOY.** Windows deployed **from Windows**: `node website/build.mjs` → pushed `dist/` to **`github.com/gringoboggy/yhwh-website`** (**commit `54c3544`**, `main`). Your `/Volumes/MacHD2/yhwh-site-publish` is now BEHIND that remote → `git -C "$PUB" pull` (or `rm -rf "$PUB"/*` + re-clone) FIRST, else your next deploy push is rejected or clobbers Windows' deploy.
3. **HTTPS is LIVE + ENFORCED.** The custom-domain Let's Encrypt cert provisioned; Windows ticked **Settings → Pages → Enforce HTTPS**. Verified: `https://www.yhwhyaway.com` loads clean over HTTPS, updated content live (note gone, new creed present).
4. **★ HOST = GITHUB PAGES (your `1dbc0f0f` pivot), NOT Spaceship cPanel.** The "Host = Spaceship Web Hosting Essential (cPanel)" lines in the **Mac-Next section below are STALE** — ignore them. Deploy is the README §"Deploy it (GitHub Pages)" flow (build → push `dist/` to `yhwh-website`; Pages serves `main`/root; CNAME + `.nojekyll` kept; `.htaccess`/`latest.php` dropped).

**Website copy is NOT final — still owed:**
- **Per-book note selection is being BUILT next session (Windows, before any manuscript).** It's currently edition-wide only (confirmed in `scripts/core/config.py:enabled_kind_codes` — no per-book dimension); the callout I removed described that OLD limitation. Once the feature ships, update the "How you make it yours" section to promise per-book note families (and the customization copy generally).
- The user wants **more copy tightened** ("re-word certain things") beyond the creed — a fuller voice pass is still owed across the pages.

## Done (turn 6 — Windows, file-disjoint from Mac's idle website lane)

**Windows lane (turn 6) — P0:**
- **★2 SAMUEL COMPLETE (1–24, both witnesses) → SAMUEL DONE.** Mapped 2sa 1–24 in 4 crop-based sub-batches; built reusable `scripts/manuscript_folio_crop.py` (native-res column tiles, fixes whole-folio downsample-to-illegible). CAM HIGH/name-confirmed (ምዕ headers + ክፍል፡ጾ rubrics; penned f117–f125), GG rubric+order cross-check (canonical, no transposition). `samuel/manifest.yaml` 2sa filled (11 calibrated); anchor index §15–§16. Gate: samuel has-folios PASSES (0 pending). Commits `03ac235c` + this commit. **NEXT = Kings.** (Pulled + rebased onto Mac's `ff9bfe14` cleanly — fully file-disjoint.)

**Mac lane (turn 6 side — website, file-disjoint from Windows P0) — WEBSITE v2 SHELL:**
- **★Website rebuilt: single-page → static MULTI-PAGE shell** (`4494a129`, pushed both remotes). Dep-free `website/build.mjs` injects shared `partials/head.html`+`foot.html` → `dist/` (gitignored); **5 pages** — index (migrated; beta CTA + ribbon; `#get-it` fixed — removed the stale "unzip/no setup" copy describing a non-existent zip) · roadmap (status-badged dev-stages timeline + fenced "with support, next") · beta (octagon program icon, honest unsigned-warning steps, SHA-256 verify, run-from-source) · releases (auto `latest.php` feed + static fallback) · feedback (Giscus via GitHub Discussions, lazy + self-hosted theme, mailto-first). Footer **Connect** row (X/GitHub/GitLab/Email inline SVG) + header **Code** link; `latest.php` server-side releases proxy; `.htaccess` strict CSP (+giscus CORS); `style.css` `--gold-foot` + dropped font `local()` + 44px targets. **★HOST = Spaceship Web Hosting Essential (cPanel)** (trial→CA$5.39/mo Jun 29; PHP/Node/cron) — NOT Cloudflare/GitHub-Pages (memory `reference_spaceship_hosting`). Decisions locked: full source at launch (scrub) · v1.0.0-beta.1 · notarize macOS now · mailto. Pre-launch placeholders; launch checklist in `website/README.md`. NOT deployed yet. Combined Windows' `f99983a1` (2 Samuel) cleanly first. **Baton left with `windows`** (did not seize — website is disjoint).

## Done (turn 5 — BOTH lanes wrapped, file-disjoint)

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
- **2 Samuel — ✅ DONE (turn 6).** Next = **KINGS (1ki 7–22 + 2ki 1–25).** READ `content/manuscript/_reviewer_context/SAMKINGS_FOLIO_ANCHOR_INDEX.md` FIRST (§10–§11 = Kings unique-event tables; §16 = method + book-end seams). GG 100% on disk: `GAPS/2_Kings/GG-00106/{1-Kings,2-Kings}/`. **CAM 1ki ≈ f126+ via CUDL-IIIF** (`scripts/acquire_cudl_master.py` with `$env:PYTHONPATH=<repo>`; f106r=view215, 2 views/leaf; verify each by penned recto number) — 1 Kings starts CAM f126r / GG f028v. Crop-based method (`manuscript_folio_crop.py`, CAM cols3×rows3 / GG cols3×rows2); MAX-1 heavy vision; sub-batch check-ins; manifest gate per batch.

**Mac (website phase) — v2 shell SHIPPED (`4494a129`); next = deploy + launch swaps:**
- **★Host = Spaceship Web Hosting Essential (cPanel)** — NOT GitHub Pages/Cloudflare. Deploy = `node website/build.mjs` → upload `website/dist/` into `public_html` (File Manager / FTP / cPanel Git). DNS already pointed (domain + hosting both at Spaceship). Memory `reference_spaceship_hosting`.
- **Launch swaps** (all in `website/README.md`): create the PUBLIC source repo (Releases + Discussions enabled; **NO OSI license** in GitHub's picker — "source-available") · first beta build **v1.0.0-beta.1** + generate `SHA256SUMS.txt` (build-chain step to add) · flip beta.html download spans → real `<a download>` + paste real SHA-256 · set `latest.php` `$REPO` + a read-only token file · wire Giscus `data-*` + **pre-create** the "Website feedback" discussion · set up + live-test email forwarding for gringo.boggy@yhwhyaway.com · flip donation spans to live Ko-fi/PayPal/Sponsors.
- **macOS signing:** notarize the `.dmg` now (Apple Dev membership paid) → clean open. **Windows** stays interim-unsigned (SmartScreen guidance live) until a code-signing cert is funded.
- **After launch:** first Ko-fi feed post + X launch post. Optional later: GitHub repo social-preview upload.

## Watch-outs
- **Baton: `windows`, status active** (re-claimed turn 6 — windows completed 2 Samuel; Mac idle on the website phase, file-disjoint). Both lanes' work is committed + pushed (GitLab + GitHub). A fresh **mac** session continues the website phase (`/resume --force` since windows holds the baton — file-disjoint); a **windows** session continues Kings.
- **Browser automation (mac):** Playwright MCP server was killed to free RAM (respawns on next browser tool call / reconnect). Persistent login profile `~/.yhwh-browser-profile` keeps GitHub/GitLab/X/Ko-fi/Spaceship sessions.
- ⚠ CAM on-disk filename `_1SamN_` suffixes are ~+3 shifted — map by penned FOLIO number (newly-acquired f114r+ are correctly named).
- ⚠ `acquire_cudl_master.py` needs `$env:PYTHONPATH=<repo>` (imports `scripts.core`).
- ⚠ (Mac) tests via Claude Bash need `export TMPDIR=/Volumes/MacHD2/<dir>`.
