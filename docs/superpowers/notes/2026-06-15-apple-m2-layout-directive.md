# Apple Books (M2) — layout directive (user, 2026-06-15)

**Status:** user directive — design north star for the `tablet` / Apple column.  
**Not a build task yet** — Kindle M4b fork and M3 Kobo fan-out stay in flight; this doc
pins what Apple must keep when Mac picks up M2 prep.

## The original idea (before Kobo/Kindle forks)

Apple Books was the **proof reader** for §4.1 `marker_style=badge`: EPUB3 popup footnotes
(`noteref` → `aside`) fire in place, scripture stays clean, and the note-count badge worked
very well. User verdict (M2 device QA, 2026-06-09): *"VERY CLEAN and nice"* — popups PASS
on Apple; inline ◈+count badges read cleanly (Gen 1:1 = ◈19).

That layout is the **reference model**. Kobo and Kindle needed separate presentation forks
because their engines do not honor the same popup contract — those compromises must **not**
bleed into Apple builds.

## Scripture layout (non-negotiable on Apple)

Per verse, two tap targets only:

| Position | What | Opens |
|----------|------|--------|
| **Verse start** | `vn-link` on the verse number | Translation popup (`vnote-{code}-{ch}-{v}`) — Hebrew, Greek, LXX, etc. |
| **Verse end** | **One study badge** with the note count | Merged study popup (`vnotes-{code}-{ch}-{v}-s1`) — all editorial notes for that verse |

Rules:

1. **One badge per verse at the end** — not per-note superscripts, not per-category chips,
   not multiple study markers inline. The badge carries the count (e.g. ◈18) exactly as the
   original badge design intended.
2. **Translation before verse text** — verse number leads; popup opens the witness text.
3. **Study badge after verse text** — last inline marker position; popup opens the merged
   listing for that verse.
4. **Every note still ships** — badge mode collapses *markers*, not content. Lossless merge +
   cascade grouping (S1/S2/S3) happens inside the popup, not by moving notes out of scripture.

## What we polish (inside Apple's plain popup system)

Apple has no custom overlay — we get the reader's native footnote sheet. Work here is
**presentation only**:

- Translation popups (`vnote-*`): typography, RTL scripts, trusted HTML rendering, spacing.
- Study popups (`verse-notes`): category cascade (verse → category → source → note), tinted
  cards, dedup, legibility — all using reader-robust cues (weight, borders, indents) with
  backgrounds as enhancement only (M2 backgrounds-off pass proved the hierarchy survives).

Do **not** chase Kobo kepub preview quirks or Kindle KFX anchor behavior when tuning Apple.

## What Apple does NOT get (other readers' forks)

| Reader | Fork | Why Apple stays different |
|--------|------|---------------------------|
| **Kobo** (`eink`) | Study badges → Study Notes glossary backmatter (K-R9b/c); per-category badges; `reader_eink_study_layout` | Kobo's coarse tap box + kepub forward-scan; popup preview strips markup |
| **Kindle** (`kindle`) | Suppress inline markers; visible endnotes; chapter-tail `notes-section` (M4b) | KFX mis-resolves `#` anchors across page-breaks; no true popups |

Apple (`target_reader=tablet`): keep **inline badge + inline popup asides** — the path that
already passed M2-1 on device.

## Build profile (when M2 column work starts)

- **Artifact:** plain `.epub` (no kepubify, no `kindle_post`).
- **Target:** `tablet` (M2 matrix column).
- **Defaults to preserve:** `marker_style=badge`, inline `verse-notes-badge` at verse end,
  `vn-link` at verse start, `note_group_by_category` cascade in the popup (ethiopian superset
  and editions that opt in).
- **Gate:** user Apple device re-test after any presentation change; epubcheck 0/0/0/0;
  M2 backgrounds-off structure pass still green.

## Evidence / lineage

- Original wins: `docs/superpowers/notes/2026-06-08-device-qa-and-note-presentation-rehaul.md`
  (◆N badges, "very very very decent").
- M2 popup PASS: `docs/superpowers/notes/2026-06-09-M2-device-qa-results.md` (AB①② fixed;
  M2-1 ✅ Apple + Kobo).
- Badge implementation: `scripts/build_edition.py` `apply_badge_markers()` (eink backmatter
  branch is **off** when `target_reader != eink`).
- CSS contract: `epub_working/stylesheet.css` §4.1 `.verse-notes-badge` / `.marker-badge`.
- Kobo layout decision (translation=start, badge=end): same M2 doc, finding K① — **same
  geometry on Apple**; only Kobo needed extra margin for tap precision.
- Kindle fork direction: `docs/superpowers/notes/2026-06-15-kindle-phone-qa-kindle_img.md` §Next
  session — explicitly **not** Apple's model.

## Lane queue (user directive 2026-06-15)

Device QA order: Kindle M4b (batched fixes) → **Mac M2 Apple prep** (this directive) →
user tests Apple → WIN M5 Play Books → user tests Play. Kobo catalog stays on round-9 hold.