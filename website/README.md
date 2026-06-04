# yhwhyaway.com — the website

A small, static, **multi-page** site (no framework, no tracking, self-hosted fonts).
The pages share one header/nav and one footer through a tiny build script. **Hosted on
GitHub Pages** (repo `gringoboggy/yhwh-website`) — **live at www.yhwhyaway.com**.

> `latest.php` + `.htaccess` are **Spaceship-only** (PHP / Apache) and are NOT used on
> GitHub Pages — the publish step drops them and the releases card uses its static
> fallback. They remain in case the site ever moves to a PHP host.

## How it's put together

```
website/
  partials/head.html   ← the shared top frame (head, header, nav) — edit nav here ONCE
  partials/foot.html   ← the shared footer (Connect row + give pointer) — edit ONCE
  src/*.html           ← each page's content + a tiny <!--page ...--> front-matter
  style.css            ← the one stylesheet (manuscript palette, WCAG AA)
  releases.js          ← upgrades the "latest release" card from latest.php
  latest.php           ← serverless feed: asks GitHub for the newest release (server-side)
  giscus/              ← lazy-loader + self-hosted theme for the comment widget
  fonts/ covers/ icons/ + favicons + social-card.png   ← static assets
  build.mjs            ← assembles everything into dist/
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

```
node website/build.mjs                          # produce website/dist/
PUB=/Volumes/MacHD2/yhwh-site-publish           # clean working copy of the publish repo
rm -rf "$PUB"/*; cp -R website/dist/. "$PUB"/
rm -f "$PUB/.htaccess" "$PUB/latest.php"        # Spaceship-only; not used on Pages
printf 'www.yhwhyaway.com\n' > "$PUB/CNAME"     # custom domain
: > "$PUB/.nojekyll"
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

## Launch checklist (the live swaps)

Pre-launch, downloads/comments/version show "coming at launch" placeholders. To go live:

1. **Public repo** — publish the source repo (Releases + Discussions enabled). Do **not**
   pick an OSI license in GitHub's dropdown ("source-available", not "open source").
   Repoint the header **Code** link (`partials/head.html`) and the download links
   (`src/beta.html`) at it.
2. **First build** — produce the binaries, generate `SHA256SUMS.txt` (run `python3 scripts/gen_checksums.py <dist-dir>`), and publish the
   release as **v1.0.0-beta.1** (do not re-publish the old internal 1.0.0 tag publicly).
   Swap the `is-pending` download spans in `src/beta.html` for real `<a download>` links
   and paste the real SHA-256 lines.
3. **Releases feed** — set `$REPO` in `latest.php` and drop a read-only GitHub token in a
   file outside `public_html` (see the comment in `latest.php`).
4. **Comments** — install the Giscus app on the repo, PRE-CREATE the "Website feedback"
   discussion, then fill the `data-repo` / `data-repo-id` / `data-category-id` on the
   `.giscus` element in `src/feedback.html` from giscus.app.
5. **Email** — set up + live-test forwarding for `gringo.boggy@yhwhyaway.com` before
   relying on it as the no-account fallback.
6. **Donations** — swap the `is-pending` give spans in `src/index.html` for the live
   Ko-fi / PayPal / Sponsors links when ready.
