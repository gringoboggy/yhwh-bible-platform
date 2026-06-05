# Website launch-readiness audit (Mac lane, 2026-06-05)

Turn-11 backlog #4. Static a11y / SEO / OG-meta / broken-link / mobile pass across
the live site (`www.yhwhyaway.com`, GitHub Pages, built from `website/` via
`build.mjs`). Cheap wins fixed in this pass; launch-gated items listed.

## Method

The site was built locally (`node website/build.mjs` → `website/dist/`) and every
shipped page parsed (`html.parser`) for: SEO (title/description length, OG +
Twitter completeness), a11y (`lang`, single `<h1>`, heading order, `<img>` alt,
link text, form labels), internal-link integrity, leftover TODO/placeholder
markers, and the host/SEO support files. External links were liveness-checked with
`curl`. The live site was confirmed serving over HTTPS (200) with its custom-domain
`CNAME`. (Scripts: `/Volumes/MacHD2/wordkind-audit/site_audit.py`, scratch.)

## Headline

The site was already in strong shape — every page ships a single `<h1>`,
`lang="en"`, full `<img>` alt coverage, no unlabeled inputs, complete Open Graph +
Twitter cards (with image dimensions + alt), a skip-link, and semantic landmarks.
The audit found **two real launch risks** (both fixed) and a handful of cheap SEO /
hygiene wins (all fixed). What remains is **release-gated**, not broken.

## Fixed this pass (cheap wins, all in `website/**`)

1. **Releases feed could never populate (real bug).** `releases.js` fetched
   `latest.php` — a PHP proxy from the abandoned Spaceship/cPanel host. GitHub Pages
   is static and cannot run PHP, so `latest.php` 404s live (confirmed). Rewrote
   `releases.js` to read the **GitHub Releases API** client-side (CORS-enabled, no
   key): it fills the latest-release card (version, date, per-asset download links +
   a release-notes link) and upgrades the pending Windows/macOS/Linux buttons into
   real download links — the instant a public release exists. Graceful fallback
   preserved (private repo / no release / rate-limit → the static card stands, no
   console error). Targets `gringoboggy/yhwh-bible-platform`; **confirm/repoint at
   launch** if the public repo is published elsewhere.

2. **A clean deploy could drop the custom domain (real risk).** `CNAME` +
   `.nojekyll` lived only in the publish repo, not in `dist/`; `build.mjs` wipes
   `dist/` on every build, so a "build then mirror `dist/` to Pages" deploy would
   silently remove them — breaking `www.yhwhyaway.com` and re-enabling Jekyll.
   `build.mjs` now **emits `CNAME` (`www.yhwhyaway.com`) + `.nojekyll`** so `dist/`
   is self-complete and a deploy can never drop them.

3. **SEO support files added** (`build.mjs` now emits them): `robots.txt`
   (allow-all + sitemap pointer) and `sitemap.xml` (the 4 canonical pages). Both
   were missing.

4. **Branded `404.html`** added (`src/404.html`) — GitHub Pages serves it with a
   404 status for unknown paths; root-relative links so it works at any depth.

5. **Over-long meta descriptions tightened** to ≤165 chars (SERP truncates ~165):
   index 289→162, releases 225→148, roadmap 199→152. Voice preserved.

6. **Hygiene:** shipped HTML comments are now stripped at build (removes the
   leftover "TODO at launch" notes from the public output — 0 remain); the stale
   Giscus "TODO at launch: configure" comment in `feedback.html` was corrected (it
   has been live since 2026-06-04); and the dead Apache/PHP files (`.htaccess`,
   `latest.php`) are no longer shipped.

After the fixes, all six pages (incl. 404) audit **clean** on a11y, SEO, and links.
External links live: GitHub / GitLab / PayPal / X → 200; Ko-fi → 403 to bots
(Cloudflare bot-block; the page is live, verified in-browser in prior QA).

## Remaining — launch-gated, to LIST not fix

- **Cut the `v1.0.0-beta.1` GitHub Release** (turn-11 #3) — blocked on Apple
  notarization (poller armed; see `dev/NOTARIZATION_STATUS.md`). Once a public repo
  + release exist, `releases.js` auto-populates the card and the platform buttons;
  no further site change needed beyond confirming the `REPO` constant.
- **Publish the public source repo** and repoint the header "Code" link (currently
  the GitHub profile) — the one genuine pending TODO left in source (now stripped
  from shipped HTML).
- **Lighthouse performance/PWA score** — not run here (needs a headless Chrome run;
  the static a11y/SEO/best-practice signals Lighthouse checks are already green).
  The site is tiny and static (one hero image, woff2 subsets, lazy-loaded Giscus),
  so perf should score high; recommend a one-off in-browser DevTools Lighthouse run
  at launch to confirm.
- **Email forwarding** for `gringo.boggy@yhwhyaway.com` (passkey-gated Spaceship/
  Spacemail) — the user is setting it up; `mailto:` works meanwhile.

## Deploy

These fixes were built, audited clean, and deployed to GitHub Pages
(`gringoboggy/yhwh-website`); the live site was re-verified (200/HTTPS, CNAME
intact, robots/sitemap/404 serving). Source committed to the monorepo `website/`.

*Read-only audit + cheap-win fixes — `website/**` only, file-disjoint from the
Windows RX arc. Companion to the turn-11/12 launch backlog.*
