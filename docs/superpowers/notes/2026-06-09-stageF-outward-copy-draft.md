# STAGE-F outward copy — v0.1.0 announcement (DRAFT for the user to post/publish)

**Status:** DRAFT, doc-only. The user posts/publishes these. Written 2026-06-09 (Mac lane,
backlog item #3 of the v0.1.0 app-UX re-plan).

**★ HONESTY GATE — read before publishing.** As of this draft the repo is NOT yet released
at v0.1.0:

- `VERSION` on disk still reads **`0.0.3`**; the released artifacts on GitHub/the releases
  page are still **v0.0.3** (`.epub`, `.kepub.epub`, `.exe`, `.dmg`, `.AppImage`, `SHA256SUMS.txt`).
- v0.1.0 = the **next** release. It must be CUT (VERSION bump → all three desktop binaries
  rebuilt fresh + EPUB/`.kepub` + SHA256 + release uploaded + site + social-card `<meta>`)
  before ANY of this copy is true on the public surfaces. Per `feedback_deploy_means_build_and_deploy`,
  "deploy" = rebuild-then-publish; a stale on-disk build is not a deploy.
- Things this copy must NOT claim as shipped because they are NOT in the cut yet:
  - The **idiot-proof end-user landing** / the maintainer note-editor moved off the default
    page — DESIGN STAGE only (Mac backlog #1; spec pending).
  - The **rich-text "font button" note editor** (Bold/Italic toolbar replacing raw HTML) —
    PLANNED, not built (WIN step 3).
  - **EB Garamond self-hosted IN THE APP** — the η.1 skin REQUESTS it but the app does not
    serve it yet, so it currently falls back to Georgia (`_design.py:178-180`). The website
    self-hosts the real font; the app does not. So: "the app now leans toward the site's
    illuminated look" is honest; "the app uses the exact same font as the site" is NOT (yet).
  - The **macOS native window** is PROVEN on the Mac (`2026-06-08-M1-native-window-verification.md`),
    but the FIX only reaches users once the v0.1.0 `.dmg` is rebuilt + notarized + uploaded.
    Until that dmg is live, do not announce "macOS now opens its own window" as a downloadable
    fact. (It is correct to announce it AS PART OF the v0.1.0 release the moment that dmg ships.)

So: **publish A–D below only after the v0.1.0 cut is live on the releases page + GitHub
release.** The WIN hand-off at the bottom lists exactly which surfaces to flip and in what order.

**Voice anchors** (matched to `website/src/index.html` + `releases.html`): faith-respectful;
free forever / no account / no cloud / no tracking; the full Ethiopian Tewahedo canon (83
books, 91,733 notes, 5 canon traditions); "still a beta on the 0.x track"; honest about rough
edges; first-person from Bogdan / Gringo Boggy where it's a personal note; British-ish
spelling and the typographic apostrophe (’) the site uses; em-dashes, not "click here".

---

## (a) v0.1.0 release notes — GitHub / GitLab release body

> Paste as the release description for the `v0.1.0` tag. Keep the title line as the release
> name. Headings are `##`/`###` so they render on both GitHub and GitLab.

---

# YHWH Ya’ Way — v0.1.0 (still a beta)

**The device-QA & polish release.** This is a milestone bump from v0.0.3 — the first release
with the desktop app dressed in the same illuminated-manuscript look as the website, the
macOS app fixed to open in its own window, and a round of fixes that came straight from
reading the Bible on real devices. It is **still a beta** on the 0.x track: an early, complete
build with rough edges welcome and your feedback wanted. (v1.0.0 comes later, once this
upgrade has proven itself in real use.)

Free forever. Runs entirely on your own computer — Windows, macOS, and Linux. No account, no
cloud, no tracking.

## What’s inside

The full **Ethiopian Tewahedo Study Bible** — one 83-book superset that already contains the
Protestant, Catholic, and Orthodox canons plus the books treasured especially in the Ethiopian
tradition (1 Enoch, 2 Enoch, Jubilees, the three books of Meqabyan, 4 Baruch, the Prayer of
Manasseh, 1 and 2 Esdras, 1 Clement). **91,733 study notes** across every family — word
studies, textual notes, cross-references, historical and cultural background, literary
analysis, commentary across traditions, topical indexes, and dictionary entries — all
toggleable. Original-language verse popups in **Hebrew, Greek, Latin, and Arabic**. Five canon
traditions, nine starting editions, and a clean **EPUB 3** export validated to zero errors and
zero warnings.

## New in v0.1.0

### A new illuminated-manuscript look for the app
The desktop builder now wears the same warm, parchment-and-ink aesthetic as
[the website](https://www.yhwhyaway.com) — a vellum-toned background, dark-brown banner with a
gold rule, gold primary buttons, gold-tinted borders, and a serif body. The app and the site
now feel like one piece. (The note-editor screen was also tidied: aligned, capitalised column
headers, wrapping book titles, and example placeholders.)

### macOS now opens in its own window
The macOS app used to open the builder in your default browser at a `localhost` address. It
now opens in its **own native window** — its own icon, its own dock entry, no browser, no
address bar — the way an installed program should. (Windows and Linux already opened natively.)

### Fixes from reading it on real devices
A round of fixes came from reading the full Bible on Apple Books and a Kobo e-reader:

- **Justified body text is now the default** for the Ethiopian Bible, so you no longer have to
  turn it on in your reader. Justification is scoped to running prose only — titles, headings,
  the contents, and tables stay as designed — which also fixes the contents list spacing out
  when a reader’s global justify was on.
- **Tidier study notes.** Repeated attributions and category prefixes are de-duplicated at
  build time, losslessly — every distinct point is kept, but a source is named once and a
  category isn’t repeated line after line.
- **Book title pages stay put.** The frame around a book’s title and art no longer bleeds onto
  the next page (it’s capped and kept from splitting across a page).
- **The “Your Edition” page reads correctly.** The honest per-book note-count list no longer
  clips its book-name column off the left edge on Apple Books.

### Under the hood
A large internal cleanup landed too: a stricter set of build-time guards (so out-of-extent
note coordinates and a few latent caching bugs can’t reappear), shared at-scale tooling, and a
fully re-verified build pipeline — the EPUB still validates to **zero errors, zero warnings**,
and the nine King-James-canon editions remain byte-for-byte identical where you change nothing.

## Download

- **Ethiopian Tewahedo Study Bible** — `.epub` (Apple Books and most readers) · `.kepub.epub`
  (Kobo, for the tap-to-read footnote popups).
- **Desktop builder app** — Windows `.exe` · macOS `.dmg` · Linux `.AppImage` (x86_64).

Every file is posted with a **SHA-256 checksum** (`SHA256SUMS.txt`) so you can confirm your
copy downloaded completely and wasn’t altered in transit. On Windows the `.exe` is
code-signed; on macOS the `.dmg` is Apple-notarized. Prefer to run from source? With Python
3.14+ you can clone the repository and launch it directly.

## A note on “beta”

This is shared openly and honestly. The Bible text and all the study notes are real and drawn
from named public-domain sources — nothing is invented for you, and AI-drafted commentary
exists only as an opt-in kind that is **off** in every edition unless you deliberately turn it
on. Found a bug, or a passage or attribution that looks wrong? That is exactly what a beta is
for — please tell me.

**Free for everyone, always.** No paid tier, no locked feature, nothing held back.

---

## (b) Website “What’s changed” blurb — releases.html

> Drop-in for the `What’s changed` list on `website/src/releases.html` (the section that keeps
> the latest ≤3 entries). Add this as the new top `<h3>` block above the existing
> `v0.0.3` block, matching the existing bullet style. Also update the hero / latest-release
> card copy + the version-stamped download links (see WIN hand-off).

```html
<h3 class="sub-h">v0.1.0 — the illuminated look, a native macOS window &amp; device-QA fixes</h3>
<ul class="prose">
  <li>A new <strong>illuminated-manuscript look</strong> for the desktop app — vellum and ink,
    a gold-ruled banner, gold buttons, serif type — so the program now matches the website.</li>
  <li>On <strong>macOS</strong>, the app now opens in its own native window (its own icon and
    dock entry), instead of opening a browser at a localhost address.</li>
  <li><strong>Justified body text by default</strong>, scoped to running prose only — so you
    no longer have to switch it on in your reader, and the contents list no longer spaces out.</li>
  <li>Tidier notes: repeated attributions and category prefixes are de-duplicated (losslessly —
    every distinct point is kept); the “Your Edition” page no longer clips its book names; book
    title pages no longer bleed onto the next page.</li>
  <li>Still a beta on the 0.x track — an early, complete build, with your feedback wanted.</li>
</ul>
```

> Also flip these strings on the releases page when the cut is live: the hero tagline /
> “Latest” card name + meta from `v0.0.3` → `v0.1.0`; the desktop-app sentence “is
> **v0.0.3**” → **v0.1.0**; all six download hrefs `…/v0.0.3/…` → `…/v0.1.0/…` and the
> filenames `0.0.3` → `0.1.0`; the `SHA256SUMS.txt` link; and the three `verify-cmd`
> examples (`YHWH-0.0.3.dmg` → `YHWH-0.1.0.dmg`, etc.). The home page hero ribbon (“Public
> Beta — almost here”) should change to reflect the beta being live if it hasn’t already.

---

## (c) Short note — “the app now matches the site / illuminated-manuscript look”

> A standalone paragraph the user can drop anywhere — a “what’s changed” aside, an About-page
> note, a forum/Discord post, or a caption. Honest about scope: it’s the app’s look that now
> leans toward the site’s; the exact same self-hosted serif is a refinement still landing.

**The app now wears the same robes as the website.** From v0.1.0 the desktop builder is
dressed in the same illuminated-manuscript style as www.yhwhyaway.com — a warm vellum page,
ink-brown banner with a thin gold rule, gold buttons, gold-tinted borders, and a serif body —
so opening the program feels like opening the site, not a different tool. It’s a calm,
old-book feel that suits what the program is for: gathering Scripture and study in one place
and putting it in your hands. (The look will keep tightening toward the site’s exact
typography in the betas to come.)

---

## (d) X / social post drafts (the user posts them)

> 2–3 standalone drafts. Pick one or thread them. Each is independently honest and under ~280
> chars. Swap the link for the live releases URL once the cut is posted. The user can attach
> `website/social-card.png` (or a screenshot of the new manuscript-look app) as the image.

**Draft 1 — the headline beat (the new look + native window):**
> YHWH Ya’ Way v0.1.0 is out (still a beta) 📜
>
> The free study-Bible builder now wears the same illuminated-manuscript look as the site —
> vellum, ink, gold. And on macOS it finally opens in its own window, not a browser.
>
> Full Ethiopian Tewahedo Bible · 83 books · free, no tracking.
> https://www.yhwhyaway.com/releases.html

**Draft 2 — the “read it on a real device” / honesty beat:**
> Read the whole thing on a Kobo and an iPad, then fixed what I saw: justified text by default,
> tidier notes (a source named once, no repeated labels), book title pages that stay put.
>
> YHWH Ya’ Way v0.1.0 — free, beta, your feedback wanted.
> https://www.yhwhyaway.com/releases.html

**Draft 3 — the mission / faith beat (short, shareable):**
> The Word of God is for everyone — and everything that helps you study it belongs in one place.
>
> YHWH Ya’ Way v0.1.0: build your own Ethiopian Tewahedo study Bible, free, on your own computer.
> 91,733 notes, toggleable. No account, no cloud, no tracking.
> 📜 https://www.yhwhyaway.com

**(Optional) Draft 4 — a follow-up reply for the thread:**
> All free, always — no paid tier, nothing locked. The Bible text + every note come from named
> public-domain sources; AI commentary is opt-in and off by default. It’s a beta, so if a
> passage or attribution looks wrong, tell me — that’s what a beta is for.

---

## Source check (so the copy stays accurate)

- VERSION line + v0.0.3 scope: `VERSION` (top of repo).
- v0.1.0 scope + release-target ruling: `docs/superpowers/notes/2026-06-08-device-qa-and-note-presentation-rehaul.md`
  (findings 1b, 2, 3, 4+5, 6, 7; "RELEASE TARGET … v0.1.0 — STILL A BETA").
- η.1 manuscript skin shipped to the app console: commit `82144f6a`; payload
  `scripts/templates/_design.py` (MANUSCRIPT_SKIN_CSS ~183, apply_manuscript_skin ~255),
  injected at `scripts/web.py:1235`.
- Note-attribution de-dup S1 shipped: commit `f01f64d9` (`note_attribution_dedup`,
  build-time, lossless).
- macOS native-window fix PROVEN (not yet in a released dmg):
  `docs/superpowers/notes/2026-06-08-M1-native-window-verification.md`.
- Voice / canon facts / "what beta means" / free-forever framing:
  `website/src/index.html` + `website/src/releases.html`.
- EB Garamond is self-hosted on the SITE only (`website/style.css:6-27`, `website/fonts/`);
  the APP does not serve it yet (`scripts/templates/_design.py:178-180`) → do not claim
  identical fonts.
