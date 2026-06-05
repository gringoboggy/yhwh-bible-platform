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

## Browser QA (real runtime, Playwright)

Served the built `dist/` locally and loaded the pages in a real browser:

- **`releases.html`** — `releases.js` runs, hits the GitHub Releases API, gets a
  **404 (the repo is private pre-launch)**, and **gracefully falls back**: the
  "v1.0.0-beta.1 — almost here" card + the 3 pending platform buttons render
  intact, **no uncaught JS exception**. The single console entry is the browser's
  own log of that 404 network response — intrinsic to any client-side API poll and
  **self-resolving the moment the repo is public + a release exists** (then the
  fetch is 200 and the card auto-populates). Page renders correctly (verified by
  screenshot).
- **`index.html`** — **0 console errors**; all **5 images load** (lazy, confirmed
  after scroll, 0 broken); meta description 162 chars; OG image wired.
- **`robots.txt`, `sitemap.xml`, `404.html`, `CNAME`** all serve 200 from the
  built site.

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

## Deploy status — built + committed; live push pending authorization

These fixes are built, audited clean, and committed to the monorepo `website/`
(pushed to both remotes). The **live GitHub Pages deploy was NOT pushed** — auto-mode
gated the production deploy of the public site as needing the owner's explicit
authorization (correctly: pushing to `gringoboggy/yhwh-website` updates the live
www.yhwhyaway.com). The current live site is unaffected and healthy; the deploy was
verified locally (rsync into the publish repo keeps `CNAME` + `.nojekyll` intact),
then the publish repo was reset to pristine.

To go live (the deploy is fully reproducible from the pushed source):
`node website/build.mjs` → mirror `website/dist/` into `/Volumes/MacHD2/yhwh-site-publish`
→ commit (GitHub no-reply email) → push (see `website/README.md` "Deploy it"). The
change is additive and degrades gracefully (the releases feed keeps its static
fallback until a public release exists), so it carries no visible-regression risk.

*Read-only audit + cheap-win fixes — `website/**` only, file-disjoint from the
Windows RX arc. Companion to the turn-11/12 launch backlog.*
