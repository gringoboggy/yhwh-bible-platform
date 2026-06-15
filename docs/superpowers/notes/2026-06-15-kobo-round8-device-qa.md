# Kobo round-8 device QA — K-R7-2d ingested (K-R8)

**Status:** INGESTED 2026-06-15 (WIN) — user round-8 report + 6 screenshots
(`C:\Users\bogda\OneDrive\Desktop\kobo_img\1.jpg` … `6.jpg`) on
`G:\YHWH-koboQA.kepub.epub` (ethiopian-tewahedo · dagger+count · one-verse-per-line ON).

**Artifact:** `build/kobo-marker-ab/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-15T032829Z.kepub.epub`
(built from `e498fdd5` K-R7-2d — inline `verse-notes` after badge cluster; **no**
`reader_eink_study_inline` flag yet → study blocks rendered **visible** in flow).

**HEADLINE:** K-R7-2d is a **structural breakthrough** — not a popup-only fix. Inline
asides fix Kobo's forward-scan chain and unlock a **second presentation layer** the
user wants to keep (full Commentary / Cross-references in the page). Default ship
must split **popup mode** (compact) from **inline study mode** (opt-in; huge page count).

## K-R8-1 ✅ PROGRESS — popups + inline study both real

| Screenshot | What user saw |
|---|---|
| 1–2 | Gen 1:1 mid-badges — **Footnote preview popups** open with Hebrew/Greek/Latin/Geʽez blocks (dagger+count chips). Popup formatting improved vs round 7. |
| 3 | Title page — **BOOKI still fused** (K-R7-4 open on this build). |
| 4 | Gen 1:1 — translation `vn-link` popup still works. |
| 5 | Gen 6:10 — **full Cross-references block inline** in reading flow (not a popup). User: "doesn't seem to be part of the popups at all" — correct; K-R7-2d made aside **visible**. |
| 6 | Gen 1:27 — **Commentary / Tradition** inline (Mesopotamian cosmogony + Ephrem). Rich layout; "takes a lot of room." |

## K-R8-2 ✅ PARTIAL — terminal badge class (s7 / singleton)

- **Gen 1:1 last badge (s7):** no popup, but **navigates to the correct page** with the
  full inline note (not chapter-start teleport). User: may be acceptable with new layout.
- **Singleton pattern:** same class — jump-to-inline rather than quick-look.
- **Root cause confirmed:** document-order fix works; remaining gap is **UX choice**
  (popup vs jump vs inline), not scan failure.

## K-R8-3 ⚠ OPEN — page-count / dual layout strategy

- User concern: shipping all study material inline → "tens or hundreds of thousands
  of pages."
- **WIN shipped K-R7-2e (turn 92):**
  - **Default (`reader_eink_study_inline: false`):** inline DOM-order anchors +
    `verse-notes--eink-anchor { display: none; }` — compact reading; badges pop.
  - **Opt-in (`reader_eink_study_inline: true`):** round-8 visible Commentary blocks.
- **Next device round:** rebuild QA kepub in **popup mode** (default) — confirm
  mid-badges still pop + page stays compact; re-tap s7/singleton.

## K-R8-4 ⚠ OPEN — BOOK eyebrow spacing

- Img 3: `BOOKI` fused — nbsp-only K-R6-4 insufficient on Kobo kepub.
- **WIN shipped K-R7-4b:** split `<span class="eyebrow-book">BOOK</span><span
  class="eyebrow-num"> I</span>` + eink `margin-right` on `.eyebrow-book`.
- **Next device round:** title-page spot-check after rebuild.

## K-R8-5 ✅ DOC — popup font refresh quirk

- User: after new sideload, Hebrew/Greek/Arabic/Geʽez may tofu in popups until user
  **deselects and re-selects Cardo** in Aa → Font face (fonts still installed).
- Documented: `dev/EREADERS.md`, `website/src/how-to-use.html`, font-pack README.

## K-R8-6 ✅ CARRY — languages + long notes

- Languages work when font pick is refreshed.
- Long multi-part notes still open (round-7 carry).

## Verdict for v1.0.0 plan §B6

| Gate | Round-8 result |
|---|---|
| K-R7-2d forward-scan fix | **PASS** (s7/singleton → correct inline target) |
| Popup UX (mid-badges) | **PASS** |
| Default compact layout | **PENDING** — K-R7-2e popup mode needs device re-QA |
| BOOK eyebrow | **PENDING** — K-R7-4b needs device re-QA |
| M3 catalog attach | **HOLD** until popup-mode QA passes |

**M3 column: NOT LIVE.** Re-fan 45 from `e498fdd5`+K-R7-2e before attach.