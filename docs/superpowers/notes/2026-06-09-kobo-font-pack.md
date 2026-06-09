# Kobo font-pack add-on — artifact shape + licensing + Guide copy (K-R2-3 prep)

**Status:** PREP COMPLETE (Mac, 2026-06-09) — licensing entries landed in-repo;
artifact + Guide copy below are ready to ship the moment WIN builds the pack.
**Context:** `notes/2026-06-09-kobo-round2-device-qa.md` K-R2-3 — the Kobo
Footnote-preview dialog renders with KOBO'S system font (embedded fonts style
body text only), so Hebrew/Greek/Arabic popups tofu in the preview regardless
of our EPUB embeds. User-approved mitigation: a sideloadable font pack (the
Kobo exposes a root `fonts/` folder). Fonts are already staged on the user's
device (G:\fonts) for the next eyeball — **the experiment to confirm before
shipping the pack: does the preview dialog follow a user-selected reading
font?** (User selects e.g. Cardo as the reading font, re-opens a translation
popup.)

## 1. Artifact shape

- **Name:** `yhwh-kobo-font-pack.zip` (attach to the GitHub release alongside
  the EPUB/kepub; merge into `SHA256SUMS.txt` like every other asset).
- **Layout (flat — the user copies the ttf files into the Kobo's `fonts/`
  folder; no nesting so there is nothing to get wrong):**
  ```
  Cardo-Regular.ttf
  Cardo-Italic.ttf
  Cardo-Bold.ttf
  NotoSerifEthiopic-Regular.ttf
  NotoNaskhArabic-Regular.ttf
  README.txt          ← install steps (the Guide copy §3, plain-text form)
  LICENSE-OFL.txt     ← full OFL 1.1 text (required: standalone font
                         redistribution must carry the license — unlike
                         in-EPUB embedding, which needs no notice)
  ```
- **Sources:** Cardo ×3 + Noto Serif Ethiopic come straight from
  `content/assets/fonts/` (already committed, already licensed). **Noto Naskh
  Arabic is NOT in the repo yet** — WIN adds the binary when building the pack:
  the notofonts arabic release static build,
  `NotoNaskhArabic-Regular.ttf` from
  <https://github.com/notofonts/arabic/releases> (full/ttf, hinted), the same
  provenance pattern as the K② Ethiopic ttf. Pin the release version + byte
  size in `LICENSES.md` when it lands (the entry's placeholders are marked).
  Commit it under `content/assets/fonts/` so the pack is reproducible — it is
  **font-pack-only** (NOT added to `EMBED_FONT_PATHS`; nothing in the EPUB
  references it, and the preview dialog wouldn't use an embed anyway).
- **Why these five:** Cardo = Hebrew + polytonic Greek + Latin (the popup
  scripts); Noto Serif Ethiopic = Ge'ez/Amharic fidel; Noto Naskh Arabic = the
  Van Dyck Arabic popups (kobo4's full tofu). All OFL 1.1. The ◈ badge
  (U+25C8) is covered by Kobo's own UI fonts in body text under Publisher
  default; if the user eyeball still shows lone boxes under a pack font,
  K-R2-3 mitigation 3 (configurable badge glyph) is the follow-up, not a pack
  change.
- **Build recipe (WIN, at pack time):** zip the five ttf files +
  `README.txt` + `LICENSE-OFL.txt`; `gh release upload` + re-merge
  `SHA256SUMS.txt`. No pipeline wiring needed — it is a static artifact; a
  `dev/` one-liner or manual zip both fine. Keep filenames EXACTLY as above
  (the Guide quotes them).

## 2. Licensing — DONE this turn

- `content/assets/fonts/LICENSES.md` → new "Kobo font-pack add-on" section:
  Noto Naskh Arabic (Google/notofonts, OFL 1.1) registered with
  version/size placeholders for WIN to pin at pack-build time; notes the pack
  reuses the already-registered Cardo + Noto Serif Ethiopic.
- `content/sources/ATTRIBUTIONS.md` → font-pack bullet added under
  "Images & fonts" (single attribution index stays complete).

## 3. Guide copy (READY — apply to `website/src/how-to-use.html` ONLY when the
pack is live in a release; never advertise an artifact that does not exist)

Insert after the existing Kobo pop-up tip callout (`how-to-use.html:55`), as a
new callout/sub-block in Path 1 · Step 2:

```html
<p class="callout"><strong>Optional — better Hebrew, Greek, Geʽez and Arabic
on Kobo.</strong> Kobo’s quick note pop-ups use your reader’s own font, which
often lacks these alphabets (you’ll see hollow boxes). The free
<a href="releases.html">font pack</a> fixes that:</p>
<ol>
  <li>Download <code>yhwh-kobo-font-pack.zip</code> from the downloads page
    and unzip it.</li>
  <li>Connect your Kobo with the USB cable. In the Kobo’s drive, make a
    folder called <code>fonts</code> at the top level (next to the
    <code>.kobo</code> folder) if it isn’t already there.</li>
  <li>Copy the five <code>.ttf</code> files into that <code>fonts</code>
    folder and eject the Kobo.</li>
  <li>On the Kobo, open the Bible, tap the centre of the page → the
    <em>Aa</em> (text) settings → <em>Font face</em> → choose
    <strong>Cardo</strong>. The ancient-language pop-ups now use it too.</li>
</ol>
```

Plain-text twin of the same steps goes in the pack's `README.txt`.

## 4. Open gates before shipping

1. **User eyeball** (staged already): preview dialog follows the reading font?
   If NO — the pack still helps body text + "See more" views; re-scope the
   Guide copy's promise accordingly (drop "pop-ups now use it too").
2. WIN: acquire + commit the Naskh binary, pin version/size in LICENSES.md,
   build + upload the zip, merge SHA256SUMS, then apply §3 to the Guide.
