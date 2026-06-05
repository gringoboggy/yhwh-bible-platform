#!/usr/bin/env node
// website/build.mjs — assemble the static site from shared partials.
//
// Zero dependencies: Node core only. No npm install, no package.json, no lockfile.
//
// The idea: you keep ONE copy of the page frame (the <head>, the header/nav, and
// the footer) in  partials/head.html  +  partials/foot.html . Each page's actual
// content lives in  src/<name>.html . This script stitches them together so the
// nav and footer can never drift between pages.
//
// What it does, per page in src/*.html:
//   1. reads the page's  <!--page ... -->  front-matter (title / desc / canonical / page)
//   2. fills those into the shared head
//   3. marks the current page's nav link with aria-current="page" (accessibility)
//   4. writes  head + body + foot  to  dist/<name>.html
// Then it copies the static assets (style.css, fonts, covers, icons, ...) into dist/.
//
// USE IT:    node website/build.mjs
// Then upload everything inside  website/dist/  to your host's  public_html .

import {
  readFileSync, writeFileSync, readdirSync, mkdirSync, rmSync, cpSync, existsSync,
} from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url)); // the website/ folder
const SRC = join(ROOT, 'src');
const PARTIALS = join(ROOT, 'partials');
const DIST = join(ROOT, 'dist');

// Static files/dirs copied verbatim into dist/ (the things the pages link to).
// (.htaccess + latest.php are intentionally NOT shipped — they are Apache/PHP-only
// and do nothing on the static GitHub Pages host; the releases feed now reads the
// GitHub Releases API client-side instead. See releases.js.)
const STATIC = [
  'style.css', 'releases.js', 'fonts', 'covers', 'showcase', 'icons', 'giscus',
  'favicon-32.png', 'favicon-512.png', 'apple-touch-icon.png', 'social-card.png',
];

const head = readFileSync(join(PARTIALS, 'head.html'), 'utf8');
const foot = readFileSync(join(PARTIALS, 'foot.html'), 'utf8');

// Replace a {{token}} with a literal string (no $-pattern surprises).
const fill = (s, token, value) => s.split(`{{${token}}}`).join(value);

// Start from a clean dist/.
rmSync(DIST, { recursive: true, force: true });
mkdirSync(DIST, { recursive: true });

for (const file of readdirSync(SRC).filter((f) => f.endsWith('.html'))) {
  const raw = readFileSync(join(SRC, file), 'utf8');

  // Pull the leading  <!--page  key: value  ... -->  front-matter.
  const fm = {};
  const m = raw.match(/<!--page([\s\S]*?)-->/);
  let body = raw;
  if (m) {
    for (const line of m[1].split('\n')) {
      const kv = line.match(/^\s*([a-z_]+)\s*:\s*(.+?)\s*$/);
      if (kv) fm[kv[1]] = kv[2];
    }
    body = raw.slice(m.index + m[0].length);
  }

  let pageHead = head;
  pageHead = fill(pageHead, 'title', fm.title || 'YHWH Ya’ Way');
  pageHead = fill(pageHead, 'desc', fm.desc || '');
  pageHead = fill(pageHead, 'canonical', fm.canonical || 'https://www.yhwhyaway.com/');

  // Mark the active nav link (WCAG 2.4.8) — a CSS cue is attached to [aria-current].
  if (fm.page) {
    pageHead = pageHead.replace(
      `data-nav="${fm.page}"`,
      `data-nav="${fm.page}" aria-current="page"`,
    );
  }

  // Assemble, then strip HTML comments from the shipped page (keeps the public
  // source clean and removes the leftover "TODO at launch" notes from the output).
  // Inline the generated Ge'ez/Amharic progress fragment (build-time, static).
  // Done BEFORE comment-stripping so the {{token}} is gone by output time.
  let bodyFilled = body;
  if (bodyFilled.includes('{{geez_progress}}')) {
    const fragPath = join(SRC, 'data', 'geez-progress.html');
    const frag = existsSync(fragPath) ? readFileSync(fragPath, 'utf8') : '<p>Progress data is being generated.</p>';
    bodyFilled = fill(bodyFilled, 'geez_progress', frag);
  }

  const out = (pageHead + bodyFilled.replace(/^\s*\n/, '') + foot)
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/\n{3,}/g, '\n\n');
  writeFileSync(join(DIST, file), out, 'utf8');
  console.log('built  dist/' + file);
}

for (const name of STATIC) {
  const from = join(ROOT, name);
  if (!existsSync(from)) { console.log('skip   ' + name + ' (not present yet)'); continue; }
  cpSync(from, join(DIST, name), { recursive: true });
  console.log('copied ' + name);
}

// Host + SEO files generated here so a clean dist/ is self-complete: a deploy can
// never accidentally drop the custom domain (CNAME) or re-enable Jekyll (.nojekyll).
const SITE = 'https://www.yhwhyaway.com';
const PAGES = ['/', '/roadmap.html', '/releases.html', '/feedback.html', '/geez.html'];
writeFileSync(join(DIST, 'CNAME'), 'www.yhwhyaway.com\n');
writeFileSync(join(DIST, '.nojekyll'), '');
writeFileSync(
  join(DIST, 'robots.txt'),
  'User-agent: *\nAllow: /\n\nSitemap: ' + SITE + '/sitemap.xml\n',
);
writeFileSync(
  join(DIST, 'sitemap.xml'),
  '<?xml version="1.0" encoding="UTF-8"?>\n'
    + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + PAGES.map((u) => `  <url><loc>${SITE}${u}</loc></url>`).join('\n')
    + '\n</urlset>\n',
);
console.log('emitted CNAME, .nojekyll, robots.txt, sitemap.xml');

console.log('\nDone → website/dist/   (push its contents to the GitHub Pages repo)');
