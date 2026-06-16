# Per-book title-page cover art refresh — creative brief + execution plan

**Status:** QUEUED (post-audit / next art ship). **Not started** in round-8 audit session.

## User direction (2026-06-15)

- **Same family of style** as the main edition Bible covers — leather, gold tooling, liturgical framing.
- **Modest extra colour** — not abundant; deep reds and related hues that fit the Ethiopian / study-Bible theme.
- **Sharper than today** — current `covers/_book_defaults/*.jpg` read soft/blurry; target **clearer detail** without going photoreal.
- **Painterly realism** — “more real but not too real”: illustrated leather scenes, not stock photos or hyperreal CGI.
- **Border cohesion** — reuse border language from main covers (`content/covers/templates/`, `content/assets/borders/`).

## Current inventory

| Location | Count | Notes |
|---|---|---|
| `content/covers/_book_defaults/` | 66 JPG | Protestant canon; ingested 2026-05-12 from publisher `book_covers/by_book` |
| Ethiopic extras (1en, jub, mq*, 4ba, paz, sus, bel, man, 1es, 2es, tob, jdt, wis, bar, lje, sir, aes, …) | **0** | Listed in `_book_defaults/README.md` |
| Main edition templates | 25 PNG | `content/covers/templates/` — 5 styles × 5 colorways, 1792×2688 |
| Reusable borders | 6 PNG | `content/assets/borders/` — alpha overlays for compositing |

Ethiopian Tewahedo `book_covers` in `content/editions.yaml` already points at `_book_defaults/` for the shared 66.

## Style anchors (Ethiopian default)

| Role | Asset |
|---|---|
| Main cover reference | `content/covers/templates/05_missal_central_red.png` |
| Border overlay | `content/assets/borders/border_01_ornate_royal.png` or `border_05_corner_accent.png` |
| Colour palette | Deep crimson leather, muted gold tooling, occasional burgundy/wine accents — **no** neon or rainbow |

## Generation pipeline (Grok Imagine session)

1. **Audit** — list all 83 shipped book codes vs existing JPG; flag missing + worst blur offenders.
2. **Master prompt block** (reuse every book):
   - 5:8 vertical book-cover plate, deep crimson leather grain, gold missal-style corner frame, soft directional light, sharp tooled detail, painterly illustration (not photograph), no text, no watermark.
3. **Per-book subject** — one symbolic motif per book (e.g. Genesis: creation light / garden; Exodus: tablets; Psalms: harp & scroll). Keep subjects modest, not busy.
4. **Consistency pass** — `image_edit` from one approved “plate master” per style batch so hue and border weight match across the set.
5. **Composite** — optional Python/Pillow step: generated scene + border PNG alpha + slight vignette to match main-cover gamma.
6. **Export** — JPG ~1200×1800 (or match template aspect), sRGB, filename `{code}.jpg` in `_book_defaults/`.
7. **Wire** — update `editions.yaml` `book_covers` for missing Ethiopic codes; rebuild one edition smoke (`ethiopian-tewahedo` eink) and spot-check title pages on Kobo.

## Quality bar

- [ ] Border weight matches main cover at thumbnail size
- [ ] No readable text in art (title is HTML/CSS overlay)
- [ ] Sharper leather grain than current set at 100% zoom
- [ ] Deep red family consistent across all 83
- [ ] No photoreal faces or copyrighted iconography

## Sequencing

Runs **after** deep-audit round 8 merge (FINDINGS-ONLY gate). Estimated: 2–3 dedicated sessions (batch by OT / NT / Ethiopic extras), not mixed with Kobo QA or audit fixes.