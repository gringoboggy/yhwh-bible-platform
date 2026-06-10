# yhwhyaway.com — the website

A small, static, **multi-page** site (no framework, no tracking, self-hosted fonts).
The pages share one header/nav and one footer through a tiny build script. **Hosted on
GitHub Pages** (repo `gringoboggy/yhwh-website`) — **live at www.yhwhyaway.com**.

> The releases card upgrades itself client-side from the **GitHub Releases API**
> (`releases.js`) — no server needed. `build.mjs` emits `CNAME`, `.nojekyll`,
> `robots.txt`, and `sitemap.xml` into `dist/`, so the built folder is self-complete
> and a deploy can never drop the custom domain. (The old Spaceship-only `latest.php`
> + `.htaccess` were removed — GitHub Pages is static and runs no PHP/Apache.)

## How it's put together

```
website/
  partials/head.html   ← the shared top frame (head, header, nav) — edit nav here ONCE
  partials/foot.html   ← the shared footer (Connect row + give pointer) — edit ONCE
  src/*.html           ← each page's content + a tiny <!--page ...--> front-matter
  style.css            ← the one stylesheet (manuscript palette, WCAG AA)
  releases.js          ← upgrades the "latest release" card from the GitHub Releases API
  giscus/              ← lazy-loader + self-hosted theme for the comment widget
  fonts/ covers/ icons/ + favicons + social-card.png   ← static assets
  build.mjs            ← assembles pages into dist/ + emits CNAME/.nojekyll/robots.txt/sitemap.xml
  dist/                ← BUILT output (git-ignored) — this is what you upload
```

## Build it

```
node website/build.mjs
```

That stitches `partials/` into each `src/` page, fills per-page title/description,
marks the active nav link, and copies the assets — producing `website/dist/`.
Preview by opening `website/dist/index.html` (or serve the folder).

## Deploy it (GitHub Pages)

> **Why not Spaceship cPanel?** This Mac's network blocks the cPanel/FTP ports (2083/21);
> only 443 gets out, so the site is published over git (443) to GitHub Pages instead.
> The domain was disconnected from Spaceship web hosting to free its DNS; email (Spacemail)
> stays. See memory `reference_spaceship_hosting`.

Publish repo = **`github.com/gringoboggy/yhwh-website`** (public, static). To deploy an update:

> ⚠ **Multi-machine:** either Windows or the Mac can deploy. **`git pull` (or re-clone) your publish working copy first** so you don't clobber the other lane's deploy. (Windows deployed `54c3544` from a fresh clone on 2026-06-03 — note removal + creed reword — and enabled Enforce HTTPS once the cert provisioned.)

```
node website/build.mjs                          # produce website/dist/ — self-complete
                                                #   (includes CNAME, .nojekyll, robots, sitemap)
PUB=/Volumes/MacHD2/yhwh-site-publish           # working copy of the publish repo
git -C "$PUB" pull                              # don't clobber the other lane's deploy
rsync -a --delete --exclude='.git' website/dist/ "$PUB"/   # mirror dist exactly
git -C "$PUB" add -A
git -C "$PUB" -c user.email=gringoboggy@users.noreply.github.com commit -m "update site"
git -C "$PUB" push
```

Served at **www.yhwhyaway.com** (DNS via the Spaceship DNS API: apex `A` → 185.199.108–111.153,
`www CNAME` → `gringoboggy.github.io`). Commit with the GitHub no-reply email so personal
email never enters public history.

## Edit it

- **Change wording on a page** → edit `src/<page>.html`, rebuild, re-upload.
- **Change the nav or footer** → edit `partials/head.html` / `partials/foot.html` once.
- **Flip a roadmap stage** (e.g. In progress → Shipped) → in `src/roadmap.html`, change
  that stage's `class="stage is-active"` → `is-shipped` AND the badge word
  `<span class="stage-badge">In progress</span>` → `Shipped`. Rebuild.

## Launch checklist (the live swaps) — ✅ EXECUTED at v0.1.0 (2026-06-10); kept for the next launch-class event

The site went live with the v0.1.0 release. Historical notes: the "beta.N" tag naming
below was RETIRED before launch — releases use plain semver on the 0.x track (v0.1.0,
v0.1.1, … → v1.0.0); `releases.js` reads the public GitHub Releases API client-side.

1. **Public repo** — publish the source repo (Releases + Discussions enabled). Do **not**
   pick an OSI license in GitHub's dropdown ("source-available", not "open source").
   Repoint the header **Code** link (`partials/head.html`) and the download links
   (`src/beta.html`) at it.
2. **First build** — produce the binaries, generate `SHA256SUMS.txt` (run `python3 scripts/gen_checksums.py <dist-dir>`), and publish the
   release under the current `VERSION` semver tag.
   Swap the `is-pending` download spans in `src/beta.html` for real `<a download>` links
   and paste the real SHA-256 lines.
3. **Releases feed** — confirm the `REPO` constant in `releases.js` points at the public
   repo hosting the release. It reads the public GitHub Releases API client-side, so once
   the release is published the card + download buttons populate automatically — no token,
   no server.
4. **Comments** — ✅ DONE (live since 2026-06-04): Giscus app installed, the "Website
   feedback" discussion pre-created, and the `data-*` values filled on the `.giscus`
   element in `src/feedback.html`.
5. **Email** — set up + live-test forwarding for `gringo.boggy@yhwhyaway.com` before
   relying on it as the no-account fallback.
6. **Donations** — swap the `is-pending` give spans in `src/index.html` for the live
   Ko-fi / PayPal / Sponsors links when ready.
