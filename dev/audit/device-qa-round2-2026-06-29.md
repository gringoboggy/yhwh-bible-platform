# v1.0.0 device-QA — ROUND 2 findings + fix plan (2026-06-29)

> **Purpose.** Round-1 remediation (batches 1–4 + rebuild) was re-QA'd by the user on
> **four readers** (Kobo · Apple · Kindle · Google Play). This captures every result so a
> **fresh session can plan the best fix order** (the user asked to plan in a new session).
> **The v1.0.0 tag stays uncut.** Round-1 tracker: `dev/audit/device-qa-v1.0.0-2026-06-28.md`.
>
> **Evidence:** screenshots in `OneDrive/Desktop/{kobo_img,apple_img}`; staged artifacts in
> `OneDrive/Desktop/QA/` + the Kobo kepub on `G:`. The full Kobo image catalog (per-image,
> with verse refs + user annotations) is in the chat transcript of this session.

---

## ✅ CONFIRMED FIXED by round-1 (do not re-touch)

- **Apple "reads backwards" → FIXED** — pages flip forward normally (the `page-progression-direction="ltr"` spine pin worked).
- **Apple ToC → FIXED** — works as intended, no longer runs backwards.
- **Apple teleports → FIXED** — note/verse links resolve correctly.
- **Copyright page + Edition-ID placement → FIXED** (user-confirmed) — the Edition-ID now sits on the copyright page (batch-2 move + the 9-KJV golden re-baseline held).
- **Notes look clean** on Apple + Play — user "loves them."
- **Body badges/paragraph formatting** look nice on Apple + Play.
- **Count cascade → live** at 90,181 (website/brand/repo, Mac lane).
- **Kindle teleport (M4b) is structurally correct** — but the artifact was rejected by Amazon (E999); see A1.

---

## OPEN ISSUES — grouped by ROOT CAUSE (for the planning session)

### A. Hidden `notes-section` at chapter ends  ← RECURRING culprit (hits Kindle + Play)

The per-chapter `<aside class="notes-section" epub:type="footnotes" hidden="">` wrapper (large) is
the common cause of two reader failures.

- **A1 — Kindle E999 (Send-to-Kindle REJECTED). ✅ FIXED THIS SESSION** (`scripts/core/kindle_post.py`,
  committed). The M4b relocation emptied the asides into the glossary but left the wrapper behind,
  holding only its chrome (`<hr>` + `<h3>Notes</h3>`) + the whitespace where asides used to sit —
  several **>14K chars**; a HIDDEN block beyond ~10K is the classic E999 trigger. Fix: widened
  `_EMPTY_NOTES_SECTION_RE` to drop any notes-section with NO surviving note `<aside>` child, +
  added an `_oversized_hidden_blocks` E999 gate to `verify_kindle_m4b`. Verified on the built
  artifact: 61 wrappers removed, hidden >10K blocks **4 → 0**. **Needs the rebuild to re-test on the device.**
- **A2 — Play Books page-number jumps ~85 pages at chapter ends.** Page count leaps where the page
  breaks are; the page number also lags (doesn't update until you turn 2+ pages, though content moves
  normally). Examples (corrected): end of **ch3** p21/20087 → next p107 → **ch4** p108; end of **ch8**
  p115 → p200 → **ch9** p201; end of **ch11** p205 → p289 → **ch12** p290. Hypothesis: in the
  everywhere/Play build the notes-section is NOT relocated (full + hidden) and Play counts it as
  ~85 phantom pages. ⚠ Partly a Play quirk; **investigate** whether a `page-break` around the hidden
  notes-section, or relocating/reshaping it for Play, removes the phantom pages. **Decision needed:**
  does Play warrant its own profile (like Kindle's M4b), or a lighter tweak?

### B. Scripture-body badge placement (Kobo) — "badge / verse-marker / badge"

Per-category badges are spliced at the verse's note **anchor** (the last note-marker), which for
many verses sits right after the verse number, **before** the verse text — e.g. **Gen 17:3**
`"exceedingly. ◈ 3 ◈ Abram fell…"`. CONFIRMED in the built HTML (`[v-17-3 marker][badge][text]`).
Desired layout: **all of a verse's badges clustered at the verse TEXT END** ("number / verse / badge").
- Code: `scripts/build_edition.py` ~4557–4562 (the mid-chapter "replace the LAST marker" path) +
  the chapter-boundary branch ~4542–4554. This is the historical, **byte-stable** placement — moving
  badges to text-end will **change the 9-KJV golden** (re-baseline needed) and affects all editions.
- Verse refs seen broken (Genesis): 6:2/5/6, 8:11/15/19, 10:6–7, 17:3, 17:22–23, 19:1, 27:44, 29:2,
  30:1, 34:4–10, 36:41–42, 37:15–17, 40:5, 42:37–38, 45:21–26, 46:13–14, 48:1–5, 49:14–15.
- No verse text is actually missing (the user's "missing verses" = the badge clutter hiding the text).

### C. inline-block badge CSS breaks Kobo's justified flow (batch 2)

`epub_working/stylesheet.css:855` — `.verse-notes-badge, .study-glossary-jump, .vn-link { display:inline-block; white-space:nowrap }`
was added (batch 2, un-gated) to stop badge drift in justified text, but on Kobo's Nickel renderer
inline-block in justified flow causes extra line breaks + clustering + awkward spacing (the user is
"not too bothered" by the spacing itself, but it compounds B). **Fix direction:** gate it OFF eink
(Kobo → plain inline, the last-version body the user accepted); keep it for Apple/Play (re-QA Play).

### D. Title pages render on 2 pages (Apple + Kindle + Play)

Every book title page splits across 2 pages (want 1). `_KINDLE_M4B_CSS` cut Kindle 3→2 already.
**Fix:** device-tuned pagination CSS (keep-together / reduce size) — verify on the rebuilt artifacts.

### E. Stray empty matter page (Apple + Play)

- Apple: empty page between the Study-Note-Count page and the Copyright page.
- Play: empty page between the last ToC page and the first Book-title page.
- Likely a spurious blank in the matter-page spine sequence (`scripts/matter_pages.py` /
  `inject_*` ordering). **Fix:** find + remove the stray page; verify the front-matter spine order.

### F. Study-note rendering (Kobo)

- **F1 — empty leading line before every note body** (between the italic source line and the body) —
  wastes vertical space. Confirmed on all back-matter notes (Easton→"CREATION", Ephrem→body, etc.).
- **F2 — return-to-verse link needs scrolling** on long notes — present on later categories, missed
  at the top on the first/longest. Add a return link at the TOP of each note (not only the bottom).

### G. Note typography enhancement (Apple + Play + Kindle — user request)

User loves the clean notes but wants richer, logical typography: **header → BOLD + ALL CAPS**,
**subheader → BOLD**, **special info → italic** (+ underline where possible). Applies to the note
render across readers. Design choice — confirm the element→style mapping with the user when planning.

### H. Font / glyph defects in translation popups (Kobo)

- **Greek:** diacritics dropped + letters exploded into single spaced glyphs (ἐποίησεν → "π ο η σ ε ν",
  θεὸς → "θ ε ς"). Accented Greek is the casualty.
- **Arabic:** missing-glyph tofu boxes (□) inside some words (e.g. بِزْرًا□).
- **Transliteration (Strong's/dict):** dropped leading char — "Elohim"→"lôhiym", "Rome"→"Eome",
  "in"→"n" — the SAME dropped-accented/leading-char class as the Greek.
- Hypothesis: embedded-font glyph-coverage gaps for combining diacritics/accented forms, **or** a
  kepubify koboSpan boundary dropping the first char of a run. Hebrew/Latin render fine. **Needs a
  focused investigation spike** (font coverage vs koboSpan boundary; Kobo-only — Apple/Play render Greek OK).

### Cross-cutting

- The **`◦` separator still shows** between languages in translation popups on every reader — batch 1
  cleaned only the STUDY cascade `_VN_SEP_*`, not the translation `vnote` separators
  (`add_vnote_preview_separators`, `test_marker_style::TestVnotePreviewSeparators` still asserts `◦`).
  Decide whether to clean those too (user hasn't complained, but it's the same clutter class).

---

## Sequencing notes for the plan

- **One rebuild at the end** (every edition × format; flagship eink last/solo, OOM-aware) → re-stage all 4 → re-QA.
- **Golden impact:** B (badge placement) and C (un-gating inline-block off eink — base CSS) will change the
  9-KJV golden → re-baseline + cross-OS re-verify (Mac). A1 is already done (kindle path; golden cells use
  `make_kindle_safe`, not M4b, so A1 doesn't touch the golden).
- **Independent / parallelizable:** H (font spike), A2 (Play investigation), G (note typography) can be scoped separately.
- **Lowest-risk quick wins:** E (stray matter page), F1 (note empty line), C (eink inline-block gate).
- **Highest-value + riskiest:** B (badge clustering — golden re-baseline) and A2 (Play pagination).

## Done this session (2026-06-29)
- A1 Kindle E999 root-caused + FIXED + gated (committed).
- Full 4-reader diagnosis (this doc).
- Round-1 wins confirmed (LTR/ToC/teleport/copyright+edition-id).
