# Design — Phase E: Clementine Latin appendix (`man` / `1es` / `2es`)

**Created:** 2026-05-26
**Status:** awaiting user review
**Phase:** Phase E (the deferred forward-piece in `dev/archive/PLAN_2026-05-21.md:210`)
**Companions:** `docs/superpowers/specs/2026-05-23-douay-vulgate-table-driven-design.md` (the proven Vulgate pipeline this reuses) · `scripts/core/versification.py` (`vulgate_to_kjv`, line 1463) · `dev/MATRIX_MAP.md` (translation-spine data-flow)

---

## 1. Problem & goal

The verse-popup spine baked the Clementine Vulgate for **74 books** (2026-05-23, `42a59e0`), but the eBible/Tweedale Vulgate source **omits the post-NT appendix**, so three deuterocanonical books carry no Latin column:

- **`man`** — Prayer of Manasseh (1 chapter)
- **`1es`** — 1 Esdras (KJV numbering; ~9 chapters)
- **`2es`** — 2 Esdras / 4 Ezra (16 chapters)

Today `man`/`1es` show KJV + LXX-Greek popups; `2es` shows KJV (its Greek is lost). **Goal:** add the Clementine Latin witness to these three books so their popups gain a Latin column, completing the Vulgate spine (74 → 77 books). For `2es`, Latin is the **primary** witness (no extant Greek).

**Purely additive:** every existing witness on these books (and all other books) stays byte-identical; only `vnote-vulgate` asides are added on `man`/`1es`/`2es`.

---

## 2. Grounding (verified 2026-05-26)

- **The gap is real:** `content/translations/vulgate-clementine/` has 74 book files + `_meta.yaml`; **none of `man`/`1es`/`2es`**.
- **`vulgate_to_kjv()` already maps `man` + `1es`** (they are present in `vul.json`; see the 05-23 design `:66`). Only **`2es` is absent from the versification table** and must be added.
- **Source confirmed on la.wikisource** (`Vulgata Clementina`), as the plan specified. Critical numbering map (the Vulgate I/II Esdrae are Ezra/Nehemiah, so the appendix is III/IV):

  | Project code | la.wikisource page | Vulgate name |
  |---|---|---|
  | `man` | `Vulgata_Clementina/Oratio_Manasse` | Oratio Manassae |
  | `1es` | `Vulgata_Clementina/Liber_Tertius_Esdrae` | 3 Esdras |
  | `2es` | `Vulgata_Clementina/Liber_Quartus_Esdrae` | 4 Esdras |

- **The existing `extract_vulgate.py` cannot be reused for ingest** — it reads eBible verse-per-line `.txt`; the source here is wikitext. A new, focused extractor is needed. `vulgate_to_kjv` (versification) IS reused unchanged for `man`/`1es`.

---

## 3. Design

### 3.1 Acquire — fetch + commit the raw source (reproducible)

Fetch the **raw wikitext** of the three pages (`…?action=raw`, or the MediaWiki API `action=query&prop=revisions&rvslots=main&rvprop=content&format=json`) and commit each as a clean source file under `content/translations/sources/vulgate-appendix/` (`oratio_manasse.wiki`, `esdras_iii.wiki`, `esdras_iv.wiki`). This matches the project's "clean committed source under `content/...`" pattern (RULES §9) and makes the ingest reproducible without re-fetching. The Clementine Vulgate text is public domain.

### 3.2 Extract — `scripts/extract_vulgate_appendix.py` (new)

A focused extractor (NOT a subclass of the eBible `extract_translation`):

```
parse each .wiki source → [(vulgate_ch, vulgate_vs, latin_text), …]
  (Clementine wikitext marks chapters + verses explicitly; strip wiki markup,
   normalize whitespace, keep the Latin verbatim — no transliteration)
→ remap each coord with versification.vulgate_to_kjv(code, ch, vs)
   (drop coords that map to None — out-of-extent / unmapped — never fabricate)
→ write content/translations/vulgate-clementine/<code>.py in the store format
   (TRANSLATION="vulgate-clementine", BOOK=<code>, VERSES=[(ch,vs,text),…],
    canonical KJV coordinates) + refresh _meta.yaml book list + counts
```

### 3.3 Versification — NO code change needed (verified 2026-05-26)

All three already map through the existing `vulgate_to_kjv`: **`man`** → identity branch (1 ch / 15 v), **`1es`** → already in `_VULGATE_SEGMENTS`, **`2es`** → identity branch (16 ch / 874 v). All three are in `CANONICAL_BOOKS`, so the `coord_in_canonical_extent` guard passes. **No edit to `versification.py`.**

The real task is **alignment verification**, especially for `2es` (4 Ezra has known versification variants): after extraction, compare the source's per-chapter verse counts to `canonical_book_shape(code)`. If they match, identity is safe. If `2es` diverges materially, **defer `2es`** (ship `man` + `1es`) rather than fabricate or silently drop — the extent guard already drops any out-of-skeleton coord to `None`, so a mismatch surfaces as missing verses, which the count-compare catches.

### 3.4 Bake — into the popup spine

`vulgate` is already a baked witness for the other 74 books, so the bake should pick up the new `man`/`1es`/`2es` store data automatically once the files exist — regenerate the affected books' asides (`python -m scripts.generate_verse_popups` for `man`/`1es`/`2es`, or the project's bake path) so each verse's `vnote` gains a `vnote-vulgate` segment. Confirm whether `popup_versions.py` gates the witness per-book (vs globally); only edit it if these books need explicit opt-in. **Only these three books change.**

### 3.5 Verify — the proven Vulgate gate (unchanged)

1. **Categorize-diff (additive-only):** the baked `vnote-vulgate` asides appear ONLY on `man`/`1es`/`2es`; every other version on every book (kjv/wlc/lxx-greek/greek-nt/arabic/jps/douay/vulgate-on-the-74) is **byte-identical**. (Mirror `_aside_compare` from the 05-23 ship.)
2. **Extent guard:** 0 out-of-canonical-extent coords (`coord_in_canonical_extent`).
3. **`ebible verify`** errors=0 (marker↔aside pairing).
4. **epubcheck catholic-study → 0/0/0/0** (catholic-study carries the apocryphal appendix; it is the plan's gate edition). Confirm the new Latin popups render.

---

## 4. Files touched

| File | Change |
|---|---|
| `content/translations/sources/vulgate-appendix/*.wiki` (NEW) | committed raw wikitext sources |
| `scripts/extract_vulgate_appendix.py` (NEW) | wikitext → store extractor (remap via `vulgate_to_kjv`) |
| `content/translations/vulgate-clementine/{man,1es,2es}.py` (NEW) | per-book stores (canonical coords) |
| `content/translations/vulgate-clementine/_meta.yaml` | +3 books, refreshed counts |
| `scripts/core/versification.py` | **no change** (verified: man=identity, 1es=existing segments, 2es=identity, all in canonical extent) |
| `scripts/core/popup_versions.py` | only if the witness is gated per-book (likely already global → no change) |
| `epub_working/index_split_*.html` | regenerated asides for the 3 books only (committed) |
| `tests/test_phase_e_vulgate_appendix.py` (NEW) | extractor counts · `2es` versification · additive-diff · extent guard |

---

## 5. Testing (TDD — write first)

- **`vulgate_to_kjv` `2es`:** representative coords map identity; a beyond-extent coord → `None`; `man`/`1es` representative coords still map (regression).
- **Extractor:** parses each `.wiki` fixture → expected `(ch,vs,text)` counts; wiki markup stripped; Latin kept verbatim; coords that remap to `None` are dropped.
- **Store round-trip:** the three new `.py` files load via `ast.literal_eval`; `_meta.yaml` lists 77 books.
- **Additive-diff (critical):** after bake, `vnote-vulgate` asides exist ONLY on `man`/`1es`/`2es`; all other versions/books byte-identical (categorize-diff).
- **Bake-and-prove gate (RULES §9):** `ebible verify` errors=0 · epubcheck catholic-study **0/0/0/0** · the three books' popups show a Latin column.
- Project gates: `lint_rules` 16/0/0 · `ruff format --check` clean (incl. the new store files — RULES §4).

---

## 6. Scope & risk notes

- **Additive only.** No base re-bake beyond the 3 books' asides; no other witness changes. This is the safety property the categorize-diff pins.
- **`2es` is the one genuine unknown.** If its wikitext versification proves to diverge materially from the canonical skeleton (not the expected identity), map only the verified range and document it — or, per the user's note at design approval, **`2es` may be deferred** and the ship lands `man` + `1es` (both already in the versification table). Decide at implementation time from the verified data, not by guessing.
- **Source licensing:** the Clementine Vulgate text is public domain; the wikitext transcription is fetched from la.wikisource per `PLAN_2026-05-21.md:210`. Credit la.wikisource in `_meta.yaml` provenance + `ATTRIBUTIONS.md`.

---

## 7. Out of scope (YAGNI)

- The broader "vision-OCR engine" generalization (`PLAN_2026-05-21.md:211`) — Phase E is "clean-digital-first"; OCR is a later arc.
- Any change to the 74 already-baked Vulgate books.
- Douay-English for the appendix (this spec adds Latin only; Douay appendix is a separate follow-on if wanted).
- Re-verifying the other prior translations (a separate queued item).
