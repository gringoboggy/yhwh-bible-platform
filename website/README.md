# yhwhyaway.com — the website

A small, static, **multi-page** site (no framework, no tracking, self-hosted fonts).
The pages share one header/nav and one footer through a tiny build script, and a single
PHP file provides the "latest version" feed. Hosted on **Spaceship Web Hosting (cPanel)**.

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

## Deploy it (Spaceship cPanel)

Upload the **contents of `website/dist/`** into `public_html` (cPanel File Manager,
FTP, or cPanel Git). Only built files leave the repo — the rest of the monorepo never
touches the server. `.htaccess` (included in dist/) sets HTTPS, the canonical `www`
redirect, the Content-Security-Policy, and the one CORS header the comment theme needs.

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
2. **First build** — produce the binaries, generate `SHA256SUMS.txt`, and publish the
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
