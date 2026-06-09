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
    page — spec DONE (`2026-06-09-idiot-proof-app-design.md`), WIN implementing NOW (turn 57);
    not shipped until it lands. If it makes the cut, add its bullet then — not before.
  - The **rich-text "font button" note editor** — same arc, same rule (Mac's vector pack
    `tests/fixtures/normalize_body_vectors.json` is ready for WIN's TDD; still not built).
  - ~~EB Garamond self-hosted IN THE APP~~ **RE-TRUED turn 57:** `5508207a` completed the app
    self-host (Noto Serif Ethiopic face + stacks + launcher.spec `website/fonts` bundle), so
    after the cut "the app uses the same self-hosted fonts as the site" becomes honest — BUT
    only once the frozen rebuild is curl-verified serving `/fonts/` (review W2; the spec §6.3
    load-bearing test, still pending). Until that verify, keep the softer "leans toward" line.
  - The **macOS native window** is PROVEN on the Mac (`2026-06-08-M1-native-window-verification.md`),
    but the FIX only reaches users once the v0.1.0 `.dmg` is rebuilt + notarized + uploaded.
    Until that dmg is live, do not announce "macOS now opens its own window" as a downloadable
    fact. (It is correct to announce it AS PART OF the v0.1.0 release the moment that dmg ships.)
  - **Device-fix claims now hinge on the user's combined RE-TEST** (turn 57): the title-page
    fixes (AB① object-fit — review W1 says possibly insufficient, contingency prepped — and the
    Kobo K③ em-caps), the Kobo popup tap-gap (K①), and Ge'ez rendering on Kobo (K② ttf swap)
    are all SHIPPED IN CODE but unconfirmed on glass. "Book title pages stay put" and any Kobo
    bullet are publishable only after the re-test passes.
  - **Count re-true (turn 57): the corpus is 91,723** after the η.1 seed-note purge
    (`3bab5f4a`, 91,733 → 91,723) — this draft now says 91,723 throughout. ⚠ The WEBSITE still
    says the OLD 91,733 in FOUR places (`website/src/index.html` :3/:33/:131,
    `website/src/roadmap.html` :23) — flip them with the cut (WIN's site pass).

So: **publish A–D below only after the v0.1.0 cut is live on the releases page + GitHub
release.** The WIN hand-off at the bottom lists exactly which surfaces to flip and in what order.

**Voice anchors** (matched to `website/src/index.html` + `releases.html`): faith-respectful;
free forever / no account / no cloud / no tracking; the full Ethiopian Tewahedo canon (83
books, 91,723 notes, 5 canon traditions); "still a beta on the 0.x track"; honest about rough
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
Manasseh, 1 and 2 Esdras, 1 Clement). **91,723 study notes** across every family — word
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
> 91,723 notes, toggleable. No account, no cloud, no tracking.
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
- EB Garamond: self-hosted on the site AND (since `5508207a`, turn 54) in the app — faces +
  stacks + launcher.spec bundle. "Identical fonts" becomes claimable after the frozen rebuild
  is curl-verified serving `/fonts/` (review W2 — the §6.3 load-bearing test, pending).

---

## (e) EXPANDED "New in v0.1.0" — the note cascade as centrepiece (APPEND to the §(a) release body)

> **Why this exists.** The §(a) draft above leads with the manuscript skin and only mentions
> note de-dup as one small device-QA bullet — it is **missing the marquee feature of v0.1.0,
> the new study-note cascade.** This block is the corrected, reader-first "New in v0.1.0"
> section: paste it in **place of** the existing `## New in v0.1.0` section in §(a). It puts
> the redesigned note presentation first (what a reader actually SEES), then folds in the
> de-dup, the manuscript skin, the macOS native window, and the device-QA fixes so the whole
> reads as one coherent release.
>
> **★ HONESTY GATE applies in full — RE-TRUED turn 57.** The three gating flags
> (`note_attribution_dedup` / `note_group_by_category` / `note_topic_dedup`) are now **ON** in
> `content/editions.yaml` (WIN's turn-48 eth re-baseline) and the cascade is LIVE in the built
> Ethiopian-Tewahedo EPUB — it passed the backgrounds-off QA and the user's real-device pass
> (Gen 1:1 ◈15, six groups, both devices). What remains gated is the RELEASE: the cascade
> reaches readers only when the v0.1.0 cut is live (VERSION bumped → eth EPUB rebuilt fresh →
> `.kepub` → all three desktop binaries + the macOS `.dmg` notarised → `SHA256SUMS` merged →
> GitHub release uploaded → site + social-card `<meta>` flipped). Until then, do not announce
> the cascade as something a reader can download today — the released v0.0.3 EPUB predates it.

## New in v0.1.0

### Notes that read like a book, not a list

This is the heart of v0.1.0. When you tap a verse’s note badge — the small diamond **◈** with a
number beside it (**◈16** means sixteen distinct notes, after duplicates have been quietly
removed) — the notes no longer spill out as one long, repetitive list. They now **cascade**, in
the same shape as Scripture itself: as the Bible runs book to chapter to verse, a verse’s notes
run **verse → category → source → note**, so the eye can read down them instead of wading
through them.

Here is what that looks like when you open one:

- **Labelled groups, with a heading and a symbol.** The notes are gathered into named groups,
  one for each kind of note present on that verse, in a fixed most-useful-first order —
  historical and cultural background first, the long topical index always last. Each group opens
  with a small-caps heading that pairs the category’s manuscript-style glyph with its written
  name (for example, **⌂ Historical / Cultural**, or **⌘ Linguistic**). The name is always
  spelt out beside the symbol, so even on an e-reader that can’t draw the glyph you still read
  the category in plain words.
- **A coloured spine down each group.** Every group carries a thin coloured line down its left
  edge in that category’s own hue — gold for the language notes, deep blue for commentary,
  crimson for the textual notes, and so on. It is a quiet structural cue rather than decoration:
  the colour survives even with every background tint turned off, so the categories stay tellable
  apart on the plainest black-and-white e-ink screen.
- **Each source named once.** Within a group the notes are gathered by where they came from, and
  the source is printed **once**, as a short italic byline above the notes drawn from it — *Easton’s
  Illustrated Bible Dictionary (1897)*, or *Treasury of Scripture Knowledge* — instead of
  repeating the same attribution on every single line, the way it used to.
- **The notes themselves, indented beneath.** Under each byline sit the individual notes, stepped
  one indent further in, so you read down the cascade naturally: the category, then the source,
  then its notes. Little labels that only echoed the category — a bare “Hebrew.” stamped on every
  word study — are gone, because the heading has already said it once.
- **One merged list of topics, last.** The topical group — every theme a verse belongs to, such
  as Creation, Heaven, or God — always comes last, and the two topical sources (Nave’s and
  Torrey’s) are merged into a **single de-duplicated, dot-separated line** of themes, credited to
  both together, rather than two overlapping lists.

And nothing is ever thrown away. The notes are only re-parented and de-duplicated — never
dropped — so **every distinct point still survives**, exactly once. (The build even fails loudly
if a single point would go missing, so the “nothing lost” promise is checked, not just hoped
for.) The result is the same wealth of study material as before — the kind of apparatus you’d
find in a print study Bible — but laid out so you can actually read it.

### Tidier notes underneath the cascade

The same care runs under the surface. Repeated attributions and category prefixes are
de-duplicated at build time, **losslessly** — a source is named once rather than on every line,
a category isn’t repeated again and again, and where Nave’s and Torrey’s topical indexes overlap
their themes are merged into one clean, Title-cased list. Every distinct point is kept; only the
clutter is removed.

### A new illuminated-manuscript look for the app

The desktop builder now wears the same warm, parchment-and-ink aesthetic as
[the website](https://www.yhwhyaway.com) — a vellum-toned background, a dark-brown banner with a
gold rule beneath it, gold primary buttons, gold-tinted borders so each panel reads as its own
box, and a serif body throughout. The app and the site now feel like one piece. The look was
then made properly accessible (WCAG-AA): button hovers use a lighter gold, links and focus rings
an indigo, hint text was darkened to stay readable, a matching dark-manuscript palette was
finished for the dark-themed lookup screens, and a handful of near-invisible numbers and labels
were re-toned so they actually read. (The note-editor screen was tidied too: aligned, capitalised
column headers, wrapping book titles, and example placeholders.)

### macOS now opens in its own window

The macOS app used to open the builder in your default browser at a `localhost` address. It now
opens in its **own native window** — its own icon, its own dock entry, no browser and no address
bar — the way an installed program should. (Windows and Linux already opened natively.)

### Fixes from reading it on real devices

A round of fixes came straight from reading the full Bible on Apple Books and a Kobo e-reader:

- **Justified body text is now the default** for the Ethiopian Bible, so you no longer have to
  turn it on in your reader. Justification is scoped to running prose only — titles, headings,
  the contents, and tables stay as designed — which also fixes the contents list spacing out
  when a reader’s global justify was on.
- **Book title pages stay put.** The frame around a book’s title and art no longer bleeds onto
  the next page (it’s capped and kept from splitting across a page).
- **The “Your Edition” page reads correctly.** The honest per-book note-count list no longer
  clips its book-name column off the left edge on Apple Books.

### Under the hood

A large internal cleanup landed too: a stricter set of build-time guards (so out-of-extent note
coordinates and a few latent caching bugs can’t reappear, and so the cascade can never silently
lose a note), shared at-scale tooling, and a fully re-verified build pipeline — the EPUB still
validates to **zero errors, zero warnings**, and the nine King-James-canon editions remain
byte-for-byte identical where you change nothing.

---

## (f) Updated releases.html "What's changed" bullets — cascade added

> Replaces the §(b) `<ul>` so the changelog block names the cascade as the headline change.
> Add as the new top `<h3>` block above the existing `v0.0.3` block; same gate as §(b)
> (publish only when the v0.1.0 cut is live).

```html
<h3 class="sub-h">v0.1.0 — notes that read like a book, the illuminated look &amp; a native macOS window</h3>
<ul class="prose">
  <li><strong>A redesigned study-note popup.</strong> Tap a verse’s <strong>◈</strong> badge and the
    notes now <strong>cascade</strong> — gathered under a heading and symbol for each category
    (with a thin coloured spine down its edge), each source named <em>once</em> as a byline, the
    notes indented beneath, and all the topics merged into one line at the end — instead of one
    long, repetitive list. Nothing is dropped; every distinct point is kept.</li>
  <li><strong>Tidier notes throughout</strong> — repeated attributions and category prefixes are
    de-duplicated (losslessly), and Nave’s and Torrey’s topical indexes are merged into one clean list.</li>
  <li>A new <strong>illuminated-manuscript look</strong> for the desktop app — vellum and ink, a
    gold-ruled banner, gold buttons, serif type — so the program now matches the website.</li>
  <li>On <strong>macOS</strong>, the app now opens in its own native window (its own icon and dock
    entry), instead of opening a browser at a localhost address.</li>
  <li><strong>Justified body text by default</strong>, scoped to running prose only; the “Your
    Edition” page no longer clips its book names; book title pages no longer bleed onto the next page.</li>
  <li>Still a beta on the 0.x track — an early, complete build, with your feedback wanted.</li>
</ul>
```

> Source check for §(e)/§(f): the reader-facing cascade description matches the in-repo
> behaviour — `scripts/build_edition.py` `_emit_cascade_sections` (category heading + glyph +
> spelled-out label, source byline once, indented note leaves), `_CASCADE_CATEGORY_HUES` (the 15
> per-category spine hues), `_merge_topic_rows` (Nave’s + Torrey’s vocab-aware topic union), and
> the `_count_cascade_leaves` conservation guard (“S2 cascade conservation failure”). The badge
> glyph **◈** and the category glyphs/names match the legend on `website/src/index.html`
> (lines 151-167). **All three gating flags** are now ON in `editions.yaml` (re-trued turn 57 —
> the re-baseline flipped them; the cascade is live in the built eth EPUB and device-tested) —
> honest the moment the v0.1.0 cut makes that rebuilt EPUB the live download.

---

## (g) Two NEW X / social drafts for v0.1.0 (distinct from the four existing beats)

These extend section (d) of `/Volumes/MacHD2/yhwh-bible-platform/docs/superpowers/notes/2026-06-09-stageF-outward-copy-draft.md`. They are numbered 5 and 6 to follow the existing Drafts 1–4. Same publish gate: post only after the v0.1.0 cut is live — and Draft 5 specifically is honest **only once the rebuilt Ethiopian-Tewahedo EPUB carrying the cascade is the downloadable release artifact** (the cascade is latent/flag-off in every shipped EPUB today, so it must not be claimed before WIN's re-baseline EPUB is the live download). The user can attach `website/social-card.png` (or a screenshot of the new cascade popup / manuscript-look app).

**Draft 5 — the new study-note cascade (the apparatus is finally readable):**
> Tap a verse’s ◈ note badge and the study notes no longer pile up as one flat, repetitive list. In v0.1.0 they cascade — gathered by category, each source named once, colour-coded down the side.
>
> YHWH Ya’ Way — free, beta.
> https://www.yhwhyaway.com/releases.html

(245 chars by X’s count. Honest: matches `cascadeUserDescription` — category headers, source named once as a byline, per-category coloured spine [the `border-left` group spine in the code], nothing dropped. No false claim that it’s in a downloadable EPUB until the eth re-baseline ships; the cascade flags are absent from `editions.yaml` so it is latent/flag-off in every shipped EPUB today.)

**Draft 6 — build YOUR edition (pick your canon + which notes show):**
> Five canon traditions, nine editions — you choose. Build your own study Bible: pick which books are in, toggle whole families of notes, export a clean EPUB. Runs on your own computer — free forever, no account, no cloud.
>
> YHWH Ya’ Way v0.1.0 (beta) 📜
> https://www.yhwhyaway.com/releases.html

(275 chars by X’s count. Honest: five canon traditions + nine editions, per-edition canon choice, toggleable note families, and clean EPUB export are all shipped/established facts at v0.0.3 and carry over; "runs on your own computer" and the free/no-account/no-cloud framing match the site.)

Notes on honesty/voice held to: faith-respectful, British "colour"/"toggle(able)" spelling, typographic apostrophe (’), em-dashes (not "click here"), "still a beta on the 0.x track" implied via "(beta)"/"free, beta", each draft standalone + verified under 280 chars on X’s counter (URL counts as 23) + ends with the releases/site URL. Neither duplicates the existing four beats (new-look+native-window, read-on-device/honesty, mission/faith, all-free follow-up); the manuscript-look "app feels like the book" angle was deliberately avoided since Draft 1 + standalone (c) already cover the illuminated-look beat — Draft 6 takes the "build your own edition" angle instead. (Note: neither draft claims the app self-hosts EB Garamond, claims rebuilt v0.1.0 binaries, or claims the cascade is already downloadable — all per the doNotClaim list.)

---

## (h) Website Guide-page update — `how-to-use.html` Step 3 (the note cascade)

## PASTE INSTRUCTIONS

**File:** `/Volumes/MacHD2/yhwh-bible-platform/website/src/how-to-use.html`

**This is a section EDIT, not a new page.** Replace the existing **"Step 3 — read, and tap for more"** `<h3>` + `<p class="prose">` (lines 49–54) with the block below. Leave the Kobo tip callout (lines 55–56) exactly as it is, immediately after this new block. No nav, sitemap, or `build.mjs` change is needed — the page is already nav-linked as "Guide".

**Honesty gate:** This describes the cascade as it appears in the v0.1.0 eth EPUB. Do **not** publish until the v0.1.0 cut is live (VERSION bumped, eth EPUB with the cascade rebuilt + byte/epubcheck/nested-anchor-verified, release uploaded, site flipped). Until then the released EPUB is the pre-cascade v0.0.3 build and this copy would be inaccurate.

---

## READY-TO-PASTE HTML

```html
      <h3 class="sub-h">Step 3 — read, and tap for more</h3>
      <p class="prose">Read normally. Where a verse carries study notes, you’ll see a small
        <strong>◈</strong> diamond with a count beside it — <strong>◈16</strong> means sixteen
        distinct notes, once duplicates have been set aside. Tap it and the notes don’t spill out
        as one long, repetitive list. They open in a single tidy panel, gathered into a small
        <em>cascade</em> that reads like the Bible itself — verse, then category, then source,
        then the notes.</p>
      <p class="prose">Each kind of note present on the verse opens its own labelled group, in a
        fixed most-useful-first order — historical and cultural background first, the long
        topical list always last. Every group carries a small heading that pairs its old
        manuscript symbol with its name spelled out beside it, so you always know what you’re
        reading even on an e-reader that can’t draw the symbol:</p>
      <ul class="custom-list">
        <li><strong>⌂ Historical / Cultural</strong> — background, places, persons, and customs.</li>
        <li><strong>◇ Commentary / Tradition</strong> — interpretive readings across the
          traditions.</li>
        <li><strong>‖ Cross-references</strong> — parallels, citations, and echoes.</li>
        <li><strong>✧ Textual / Critical</strong> — variant readings and manuscript witnesses.</li>
        <li><strong>⌘ Linguistic</strong> — Hebrew, Greek, and other word studies.</li>
        <li><strong>✦ Topical</strong> — every theme the verse belongs to, kept to the very end.</li>
      </ul>
      <p class="prose">Each group also carries a thin <strong>coloured stripe</strong> down its
        left edge in that category’s own hue — gold for the word studies, deep blue for
        commentary, crimson for the textual notes, and so on. On a colour screen that hue tells a
        word study from a cross-reference from a piece of commentary at a single glance; and
        because the stripe sits in the structure itself — alongside the spelled-out heading and the
        stepped indentation — the groups stay clearly separated even on a plain black-and-white
        e-ink reader.</p>
      <p class="prose">Inside a group, each <strong>source is named just once</strong> — a short
        line in italics, such as <em>Easton’s Illustrated Bible Dictionary (1897)</em> or
        <em>Treasury of Scripture Knowledge</em> — set above the notes drawn from it, with the
        notes themselves stepped in beneath. No more reading the same attribution over and over on
        every line. The topical indexes come last of all, with the two topical sources gathered
        into one merged, de-duplicated line of themes. Nothing is ever thrown away — the notes are
        only re-grouped and tidied, never dropped, so every distinct point still survives.</p>
      <p class="prose">A separate marker opens the verse in its <strong>original languages</strong>
        (Hebrew, Greek, Latin, Arabic). If you built your own edition, the same families of notes
        you switched on or off appear here, in this same cascade. Use the reader’s own table of
        contents to jump between books and chapters, and the reader’s controls to change font size,
        spacing, and theme — the Bible follows your reader’s settings.</p>
```

---

A few notes on choices made, for the record:
- I dropped the now-inaccurate "grouped by kind" phrasing entirely and replaced it with the cascade story (verse → category → source → note), as the target spec directed.
- I showed only 6 of the 15 categories (the most-useful-first head of the order plus Topical-last) to keep it reader-facing rather than re-listing the full legend that already lives on `index.html#reading-the-notes`. The colour examples (gold/Linguistic, deep blue/Commentary, crimson/Textual) match `facts.categoryGlyphsAndColors` exactly.
- The colour-stripe paragraph was reworded so it doesn't overclaim: the hue distinguishes groups *on a colour screen*, while on a plain black-and-white/grayscale e-ink reader (where distinct hues collapse toward similar grays) it is the *structural* separation — the stripe's presence, the spelled-out heading, and the stepped indent — that keeps the groups apart. This matches what `facts.categoryGlyphsAndColors`/`cascadeUserDescription` actually claim (a structural cue that survives with background tints off), not "tell colours apart on monochrome".
- "coloured stripe" / "coloured" uses British-ish spelling to match the site; all apostrophes are the typographic ’; em-dashes throughout; no "click here". The `◈16` example and "set aside / never dropped" framing come straight from `cascadeUserDescription`.
- Honesty-safe: no version number is stated in this section, and the copy describes only the cascade apparatus (safe per `honesty.safeToClaimAfterCut` the moment the rebuilt eth EPUB is the download). It does not touch any do-not-claim item (no v0.1.0 claim, no font claim, no landing page, no rich-text editor).

**Secondary, optional (not done — outside this edit):** a one-line `v0.1.0` changelog bullet on `releases.html` "What's changed" mentioning the refined cascade. The Stage-F draft at `/Volumes/MacHD2/yhwh-bible-platform/docs/superpowers/notes/2026-06-09-stageF-outward-copy-draft.md` already has the broader release blurb; you could add "notes now read in a tidy cascade — grouped by category, each source named once, topics merged" to its `releases.html` block.

---

## (i) The FOLLOW-UP X THREAD — the days after the announcement (Mac, turn 57, backlog #4)

> The user's release model: **the announcement, then follow-ups** — one beat a day (or
> whenever it feels right) in the days after the v0.1.0 cut, each post standalone-honest,
> ≤280 chars (URL counts as 23), same voice anchors (faith-respectful, typographic ’,
> em-dashes, British-ish spelling). These are numbered F1–F5 to keep them distinct from
> Drafts 1–6 in §(d)/§(g), and none repeats those beats. Post in any order EXCEPT the gates
> noted. Attach a screenshot where suggested — a real picture beats any copy.

**F1 — the cascade, shown not told** *(attach: a screenshot of one verse’s opened ◈ popup —
Gen 1:1 is the show-piece)*
> This is one verse’s study notes — gathered by category, a coloured spine down each group,
> every source named once, the topics merged into a single line at the end.
>
> Built so a reader can actually read the apparatus, not wade through it.
> https://www.yhwhyaway.com/releases.html

**F2 — the Kobo / Ge’ez story** *(GATE: post only after the user’s Kobo re-test confirms K②
fidel renders + popups behave)* *(attach: a photo of the Kobo showing Ge’ez in a popup)*
> The Ethiopian Bible on a Kobo, with the Ge’ez script rendering properly in the note popups —
> the font travels inside the book, in a format e-readers actually understand.
>
> Tap-to-read footnotes via the .kepub build. Free, as always.
> https://www.yhwhyaway.com/releases.html

**F3 — the honesty story (the ten deleted notes)** *(no gate beyond the cut — this one is
already true and it is the strongest trust beat we have)*
> Before this release we found 10 notes in Genesis whose attribution said “sample” instead of
> naming a real source. We deleted all 10.
>
> The promise is: every note from a named public-domain source, nothing invented. A smaller
> apparatus that keeps its word beats a bigger one that doesn’t.

**F4 — the trust beat (verify your copy)** *(no extra gate)*
> Every download ships with a SHA-256 checksum. The Windows app is code-signed; the macOS app
> is Apple-notarized; the whole thing runs offline on your own computer — no account, no
> telemetry, nothing phoning home.
>
> Your Bible, on your machine, verifiably yours.
> https://www.yhwhyaway.com/releases.html

**F5 — what’s coming (the standalone Ge’ez + Amharic Bibles)** *(honesty: phrase as IN
PROGRESS — the transcription work is real and ongoing, no date promised)*
> Next on the bench: standalone Ge’ez and Amharic Bibles, transcribed from public-domain
> manuscripts and editions — with an English back-translation in the popups.
>
> Slow, careful work. It’ll be free when it’s ready, like everything else.
> 📜 https://www.yhwhyaway.com

> **Char counts (X’s counter, URL=23):** F1 ≈ 252 · F2 ≈ 245 · F3 ≈ 268 · F4 ≈ 262 · F5 ≈ 247.
> **Honesty check:** F1 = shipped cascade facts only (category groups, spine, byline-once,
> merged topics). F2 gated on the device re-test; "format e-readers understand" = the ttf swap,
> no woff2 jargon. F3 matches `3bab5f4a` exactly (10 notes, Genesis, sample attribution,
> user-decided removal); count claims avoided. F4 = SHA256SUMS + signing/notarization facts
> already true at v0.0.3 and carried forward by the cut gate. F5 promises no date and claims
> no completion — Phase-D status per `project_geez_phase_d_sources` (vision-transcription in
> progress; Psalms + Samuel/Kings marathon are the clean-verse base).
