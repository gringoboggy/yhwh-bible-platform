---
holder: mac
from: mac
turn: 14
updated: 2026-06-05
status: active
---

## ▶ Mac → Windows (turn 14, 2026-06-05) — ★MAC CLAIMS THE BATON for the user-greenlit auto-note RE-INGEST track (main-repo content + bake).

The user greenlit the re-ingest track (your turn-13 #3). It touches `content/notes/**` + a re-bake into `epub_working/**` — the exact shared files — so Mac is taking the baton to be the **sole main-repo worker** for it. You marked RX idle / "between tasks" (`6ac434b0`), so this is collision-safe. **Windows: if a session resumes, `/resume` and do NOT start main-repo work until Mac hands the baton back.** Mac is working the 5 ingest defects from the two content audits, each TDD + byte-verified (only the targeted notes change) + committed/pushed per fix:

1. **dict-easton un-cap** (1,431 truncations, 37.9% — the #1) + the `_HEAD` headword-spacing bug (~451).
2. **lang-greek Theós head-drop** (1,196 — every θεός gloss missing the "God" sense).
3. **topic-torrey ref-dump leak** (596).
4. **lang-greek Phōs paren-imbalance** (76).
5. **topic-nave description-as-heading** (87).

Audits: `docs/superpowers/notes/2026-06-06-auto-note-quality-audit.md` (the 5 defects) + `2026-06-06-word-kind-audit.md` (the owner's curated notes — separate, not this track). **★EXECUTION PLAN (READY): `docs/superpowers/notes/2026-06-06-auto-note-reingest-plan.md`** — full detail, the byte-minimal source+base lockstep method, the dry-run results (1,431 truncated + 792 glued, matching clean), the **FULL-articles** cap (user-chosen 2026-06-05) + a researched **zero-loss split-to-fit** design. A fresh session executes it (this session planned it; baton held by Mac). Baton returns to Windows when the track is done or paused.

> ⚠ **Fresh Mac session — before ANY content edit:** Windows was still finishing up (about to push) as of this turn. `git fetch` and pull/rebase Windows' finishing work FIRST so you execute on the latest base (avoids rebase churn on `content/notes`/`epub_working`). The user coordinates the timing ("pull when I tell you") — confirm with them before starting. Then begin with dict-easton #1 per the plan.

---

## ▶ Windows → Mac (turn 13, 2026-06-05) — ★RX BUILD READY: Phase 4 (Kobo TOC + file-splitter) landed + verified → your GATED cross-reader validation is GO (file-disjoint; baton STAYS `windows`).

The **EPUB Reading-Experience Overhaul is COMPLETE through Phase 4** (the last RX phase before the user's device test). Shipped overnight: **P4b file-splitter** (2–5 MB `index_split_*.html` → ~0.4 MB pieces; ethiopian-tewahedo 227 pieces / max 472 KB; default ON) + **P4a Kobo-safe in-content TOC** (unwrap `<details>` + drop `.toc-chapters` flexbox; chapters kept). The program-end gate caught a real canon-filter well-formedness bug (a chapter anchor nesting inside the previous chapter's `<p class="verse-p">`) → fixed with a unified stack-aware splitter; **catholic-study + ethiopian-tewahedo epubcheck 0/0/0/0**.

1. **★(GATED → NOW GO) Cross-reader validation — this is the "build ready" signal you were waiting for.** Build any edition from `main` (`$env:PYTHONUTF8=1; python -m scripts.build_edition ethiopian-tewahedo --force`) and **load it on Google Play Books (web) + Kindle Previewer**; extend the cross-reader compat matrix beyond Apple/Kobo (append to `docs/superpowers/notes/2026-06-05-eink-epub-compat-research.md`). The user runs the Kobo + Apple Books device test separately (batched at the very end).
2. **(if not done) the launch backlog** (turn 11–12): `word`-kind audit (✓ done `a25ed18b`), GitHub/GitLab repo-settings + visible files, `v1.0.0-beta.1` release once notarization clears, website Lighthouse/a11y/link audit. External/website — disjoint.
3. **(UNBLOCKED, but still USER-greenlight-gated) the auto-note re-ingest track** — RX has landed, so the P4 splitter/bake collision is resolved; you MAY start once the **user** greenlights it (dict-easton un-cap [1,431], lang-greek Theós [1,196], topic-torrey ref-dump [596], etc.).

**Do-NOT-touch while baton=windows:** `scripts/**`, `epub_working/**`, `content/notes/**`, `editions.yaml`, `build_edition.py`, `stylesheet.css`, `docs/superpowers/plans|specs/**`, the truth-records. **Safe:** `website/**`, `yhwh-website`, external accounts, macOS-local `dist/`, NEW doc files. `/sync` before ANY main-repo touch.

---

## ▶ Windows → Mac (turn 12, 2026-06-05) — REFRESHED QUEUE (file-disjoint; baton STAYS `windows`).

Your content-quality audit (`1091e4d2`) is ★excellent — full-population + adversarial, and it caught the dict-easton 37.9%-truncation that sampling alone missed. **Headline: RX Phase 1's scaffold strip is CLEAN across all 6 kinds** (validated). The defects you found are pre-existing INGEST bugs (a future re-ingest track — deferred, item 4). Thank you.

**Windows status:** RX Phases 1–3 SHIPPED; Phase 5 (badge) in flight; the new session continues with P4 (Kobo TOC restructure + the file-splitter). Windows still owns the build pipeline + content store. `/sync` before ANY main-repo touch.

**Your queue (top-to-bottom):**
1. **(immediate, read-only) Audit the curated `word`-kind studies** — your auto-note audit explicitly flagged that kind=`word` (the hand-written "User original/paraphrase" Hebrew/Greek studies, the multi-sentence ones) is a SEPARATE kind NOT covered by the auto-note pass. Same purpose-aware + adversarial method → NEW `docs/superpowers/notes/2026-06-06-word-kind-audit.md`. Read-only, disjoint.
2. **Finish the launch backlog** (turn 11, if not yet done): #2 GitHub+GitLab repo settings + visible-files (Chrome-MCP); #3 the `v1.0.0-beta.1` release + download-link flip once notarization clears; #4 the website Lighthouse/a11y/link audit. External/website — disjoint.
3. **(GATED) Cross-reader validation** — when Windows signals the FINAL post-P4 RX build is ready, load it on Google Play Books (web) + Kindle Previewer and extend the compat matrix beyond Apple/Kobo. Wait for the "build ready" signal.
4. **(DEFERRED — post-RX + user greenlight) The content re-ingest track your audit surfaced:** dict-easton un-cap re-ingest (1,431 truncated — the #1), lang-greek Theós head-drop (1,196), topic-torrey ref-dump leak (596), lang-greek Phōs (76), topic-nave description-as-heading (87). **Do NOT start it yet** — it touches `content/notes/**` + a bake (`epub_working/**`) which collides with Windows' RX P4 splitter; it waits until RX fully lands AND the user greenlights the track.

**Do-NOT-touch while RX runs:** `scripts/**`, `epub_working/**`, `content/notes/**`, `content/assets/fonts/**`, `editions.yaml`, `build_edition.py`, `inject.py`, `stylesheet.css`, `docs/superpowers/plans|specs/**`, the truth-records. **Safe:** `website/**`, the `yhwh-website` repo, external accounts (browser), macOS-local (`dist/`), NEW doc files.

---

## ▶ Windows → Mac (turn 11, 2026-06-05) — BACKLOG: work top-to-bottom (file-disjoint; baton STAYS `windows`).

So we stop round-tripping per task — here's your queue. `/sync` before ANY main-repo file edit; report at each close. **Do-NOT-touch (Windows owns this RX arc):** `scripts/**`, `epub_working/**`, `content/notes/**`, `content/assets/fonts/**`, `editions.yaml`, `build_edition.py`, `inject.py`, `stylesheet.css`, `docs/superpowers/plans|specs/**`, and the truth-records (`dev/SESSION_STATE.md`/`IN_FLIGHT.md`/`CHANGELOG.md`). **Safe zones:** `website/**`, the `yhwh-website` repo, external accounts (browser), macOS-local (`dist/`), NEW doc files.

1. **(running) Apple notarization** — the 30-min poller staples + regenerates `dist/SHA256SUMS.txt` when Apple clears (Apple-side backlog ~30h, 2 submissions pending). Let it finish; nothing else.
2. **GitHub + GitLab repo settings + visible-files pass (Chrome-MCP)** — per `project_github_gitlab_account_settings`. Both repos: reconcile description / topics / website-URL / social-preview / visibility / `main` branch-protection; ensure root `README.md` (Geʽez-led + cross-platform quick-start), `LICENSE` (**all-rights-reserved / source-available, NOT CC0**), `SECURITY.md` correct + matched across the mirror. Report passkey-gated items.
3. **Public-launch + v1.0.0-beta.1 release** — once notarization clears: cut the GitHub Release, flip website download links to the real artifact + `SHA256SUMS.txt`, verify Giscus + Ko-fi/PayPal live, test email forwarding for `gringo.boggy@yhwhyaway.com`. List blockers.
4. **Website launch-readiness audit** — Lighthouse / a11y / mobile / OG-meta / broken-link pass across all pages; fix cheap wins, list the rest (`website/**`).
5. **Auto-note content-quality audit (read-only)** — Phase 1 stripped the `[Reviewer:]` scaffold; assess whether the auto-notes read well now. Sample each kind (`topic-nave`/`topic-torrey`/`lang-hebrew`/`lang-greek`/`xref-citation`/`dict-easton`), flag the thin/raw ones, write to NEW `docs/superpowers/notes/2026-06-06-auto-note-quality-audit.md`. Audit + report only — NO `content/notes/` edits.
6. **(LATER — wait for Windows' "build ready" signal) Cross-reader validation** — load a fresh RX build on Google Play Books (web) + Kindle Previewer; extend the compat matrix beyond Apple/Kobo.

---

## ▶ Windows → Mac (turn 10, 2026-06-05) — NEXT TASK: finish Apple notarization + website σ-reflection (file-disjoint; baton STAYS `windows`).

**Thanks — your cross-reader compat research landed (`979bde50`, rebased under Windows' RX Phase 1).** Windows is now powering through the **EPUB Reading-Experience Overhaul** build: **RX Phase 1 (scaffold strip) SHIPPED**; Phases 2 (cross-reader CSS) → 3 (font embed) → 4 (Kobo structural + the new file-splitter) → 5 (`badge` default) are next, all on the build pipeline (`scripts/**`, `epub_working/**`, `content/**`, `editions.yaml`). **Baton stays `windows`.** Mac: `/resume --force` (file-disjoint), `/sync` before any main-repo touch.

**MAC TASK 1 (primary) — finish the owed Apple notarization.** The signed `dist/YHWH-1.0.0-beta.1.dmg` is on the Mac. Apple's notary service was mid-outage on 2026-06-04 — retry it now. Submission `0c0d10c1-5e3b-4c6c-a418-368edae22eea`; the exact `xcrun notarytool wait … && stapler staple … && spctl -a -vv … && gen_checksums.py dist` command + caveats (don't clear `dist/` until stapled; regen checksums AFTER stapling) are in `dev/IN_FLIGHT.md` (the Mac-lane entry). If Apple's notary is STILL down, report + switch to Task 2.

**MAC TASK 2 (secondary) — website σ-reflection (the deferred 'how you make it yours' copy, σ portion only).** σ shipped: the **HOLY BIBLE cover** + a **'Your Edition' first page** + build-accurate counts/glossary. Update the live site (`website/` → deploy to `yhwh-website`) to showcase the real cover + the 'what you built' page and flip any now-stale 'coming soon' copy that σ made real. **HOLD the badge / 'how notes display' copy** — badge mode is still being built (RX Phase 5); update that once Windows lands it. Disjoint (website repo).

**Do NOT touch (Windows owns this arc):** `scripts/**`, `epub_working/**`, `content/**`, `editions.yaml`, `docs/superpowers/**`, and the truth-records (`dev/SESSION_STATE.md` / `dev/IN_FLIGHT.md` / `dev/CHANGELOG.md`).

---

## ▶ Windows → Mac (turn 9, 2026-06-05) — NEW PARALLEL TASK: cross-reader EPUB compatibility research (file-disjoint; baton STAYS `windows`).

**Baton stays `windows` on purpose.** Windows is running the main-repo **EPUB Reading-Experience Overhaul** (the Kobo device-QA fixes): Layer A discovery workflow now → Phase 1 (strip the 88,773 `[Reviewer:…]` scaffolds + the generator/promote root-cause fix + a lint guard) → the deferred **badge** reading mode → cross-reader/Kobo polish. Windows keeps committing + pushing `main`. Master plan: `docs/superpowers/plans/2026-06-05-epub-reading-experience-overhaul.md`.

**MAC: pick this up with `/resume --force`** (file-disjoint — one new doc, no code). `/sync` before touching anything outside your doc.

**MAC TASK — Cross-reader EPUB compatibility research → `docs/superpowers/notes/2026-06-05-eink-epub-compat-research.md`** (full brief = the master plan's **Layer C**). For **Kobo** (color e-ink), **Apple Books**, and **Google Play Books**, document support + the cross-reader-safe pattern for: (a) EPUB3 popup footnotes (`epub:type="noteref"`/`"footnote"` + `<aside>`), (b) `<details>/<summary>`, (c) flexbox, (d) embedded `@font-face` fonts (formats, subsetting), (e) `position:absolute` / full-bleed images, (f) large single-file performance, (g) Kobo **KePub vs vanilla EPUB**. Each = supported / partial / unsupported + recommended markup + a citation. This de-risks Windows' D2/D3/D4/D5. **Pure web research + one doc — no build-pipeline files.**

**Secondary (only if that finishes):** finish the owed **Apple notarization** — `dist/YHWH-1.0.0-beta.1.dmg` is signed; the `notarytool wait → stapler staple → spctl → gen_checksums` command is in `dev/IN_FLIGHT.md`. Disjoint.

**Do NOT touch (Windows owns these this arc):** `content/notes/**`, `epub_working/**`, `scripts/**`, `editions.yaml`, and the truth-records (`dev/SESSION_STATE.md` / `dev/IN_FLIGHT.md` / `dev/CHANGELOG.md`).

---

## ▶ Windows → Mac (turn 8, 2026-06-04) — concert restart. Windows on σ build + Esther content (main repo); Mac's lane = the public-launch finish (separate website repo + external). Baton stays `windows`.

**State of the two lanes (user-directed; Mac was paused after finishing its side):**

- **Windows (me) holds the main-repo baton** and is running BOTH main-repo lanes: **(1) σ "Edition Cover + Truthful Front Matter"** — subagent-driven, plan `docs/superpowers/plans/2026-06-04-edition-cover-and-truthful-front-matter-plan.md` (σ.1 build-accurate `resolved_note_counts` → σ.2 HOLY-BIBLE cover → σ.3 "Your Edition" page → σ.4 /customize identity → σ.5 Ge'ez/Amharic covers → σ.6 live-console reconcile). **(2) Content** — the Ge'ez transcription marathon (Phase D1b Esther p35), Windows-only (local GAPS/CUDL assets). Windows commits + pushes the **main** repo; I own SESSION_STATE / IN_FLIGHT / CHANGELOG this turn.

- **Mac, on `/resume`: your lane is the public launch + website — a SEPARATE repo (`github.com/gringoboggy/yhwh-website`) + external/browser, file-disjoint from my main-repo work, so you do NOT need the main-repo baton to do it.** Pick up:
  1. **Finish Apple notarization** when the Apple notary outage clears — the exact `xcrun notarytool wait … && stapler staple … && spctl … && gen_checksums` command is in `dev/IN_FLIGHT.md` (the Mac-lane entry). The signed `dist/*.dmg` is on the Mac.
  2. **The remaining public-launch swaps** (post the `v1.0.0-beta.1` release, flip download links to the real artifact + checksums, Giscus go-live confirm) per `website/README.md` + the IN_FLIGHT Mac entries. (Note: Giscus/donations/HTTPS already shipped — verify, don't redo.)
  3. **The GitHub + GitLab account/repo settings pass** + add any missing visible files (README/CHANGELOG/LICENSE) via Chrome-MCP — memory `project_github_gitlab_account_settings`. LICENSE is **all-rights-reserved** (user decision, not CC0; already set in the repo).
  4. **DEFERRED until σ ships:** the website **"How you make it yours" copy** — do NOT rewrite it yet. Once Windows lands σ (the HOLY-BIBLE cover + "Your Edition" page + per-book/chapter/verse customization is live + truthful), update the site copy to match the real feature. Until then the current copy stands.

- **Coordination / watch-outs:** if you must touch the **main** repo, `/sync` first and coordinate — I hold the baton and am actively committing there. Your website pushes go to `yhwh-website` (its own repo) and don't contend. The E:/F: bundle legs are Windows-only.

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
