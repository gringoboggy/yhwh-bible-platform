# Douay-Rheims + Clementine Vulgate — table-driven versification ingest

**Date:** 2026-05-23
**Status:** Design — approved (direction + scope), pending spec review
**Supersedes for D/V methodology:** the eyeball-grind plan in `dev/IN_FLIGHT.md` "D/V GRIND IN PROGRESS"
**Extends:** `docs/superpowers/specs/2026-05-23-translation-spine-arc.md` (the Phase-2 translation-spine runbook). This doc changes only *how* the D/V versification map is derived; the extractor → `versification.<x>_to_kjv` → driver → bake → diff → epubcheck → docs pipeline is unchanged.

## Problem

Douay (`engDRA`) and the Clementine Vulgate (`latVUC`) share one Latin/Septuagintal versification, so one `versification.vulgate_to_kjv` adapter serves both. ~50–80 protocanonical chapters diverge from KJV by verse splits/merges/offsets and must be mapped. The prior session began this by hand-aligning Douay-English against KJV-English and proposing splits from word-overlap.

The bottleneck (documented in `dev/IN_FLIGHT.md`): Douay (Latin-derived) and KJV (Hebrew-derived) share only ~0.5 word overlap even when *correctly* aligned, so overlap cannot reliably pick the right split, and a per-chapter aligner is **structurally blind to cross-chapter boundary shifts** (e.g. Vulgate `Num 30:1 = KJV 29:40`). The prior plan therefore required eyeball verification of every one of ~75 chapters.

## Decision

Adopt an **authoritative, scholar-curated versification table** as the source of truth, verified against the project's real data, instead of overlap-guessing.

- **Source:** Copenhagen Alliance `versification-specification` — `standard-mappings/vul.json` (Vulgate→org) composed with `eng.json` (eng→org, inverted) to yield `vul→KJV`.
- **Why this beats the grind:** the cross-chapter shifts that defeat the per-chapter aligner are first-class entries in the table (`NUM 13:1→12:16`, `DEU 29:1→28:69`, `JOS 21:37→21:39`, `1KI 4:21-34→5:1-14`, `2CH 2:1→1:18`, `NEH 4:1-6→3:33-38`, `1SA 20:43→21:1`, `2SA 18:33→19:1`, …). Every "STILL TO DO" protocanonical book in the grind map is covered.
- **Scope (user-chosen):** focused D/V only. Two bonuses are logged as follow-ups (see below), not done here.

### Three sub-decisions

1. **License — facts only, no file vendoring.** Copenhagen *data* is **CC BY-SA 4.0** (share-alike), which conflicts with this repo's CC0 if vendored verbatim. Versification mappings are *facts* (uncopyrightable — the repo already hardcodes the same class of data in `canonical_verse_counts`). We extract the facts into the repo's own `_VULGATE_SEGMENTS` Python structures (a transformation), credit Copenhagen Alliance + UBS/SIL in `dev/CHANGELOG.md` and a source comment in `versification.py`, and keep the raw `_vrs_*.json` **outside** the git repo (working-dir parent, like the existing `_probe_*.py`/`_vg_*.py` throwaways).
2. **`wis` flips to INCLUDE.** The prior plan marked Wisdom "borderline — assess, maybe OMIT." `vul.json` *does* map `WIS`, so it is includable; the `_vg_verify` overlap gate is the backstop if the Latin text turns out to be a divergent recension after all.
3. **`_VULGATE_OMIT = {tob, jdt, sir}` stays.** Independently corroborated: `vul.json` has **no** mapping for `TOB/JDT/SIR` (the UBS/SIL community reached the same "different recension → don't map" conclusion). Those KJV verses keep their KJV + LXX-Greek popups; they simply get no Douay/Vulgate column.

## Architecture & components

```
_vrs_vul.json ─┐
_vrs_eng.json ─┤  _vg_gen.py (throwaway, repo-parent)
               └──► compose vul→org→eng(KJV)
                    ├─► emits _VULGATE_SEGMENTS / _VULGATE_PSALM_FIXES / _VULGATE_CROSS snippets
                    └─► emits DISCREPANCY REPORT vs (a) already-encoded segments
                                                   (b) actual eBible latVUC/engDRA verse counts
                                                   (c) existing _psalm_map (Psalms cross-check)
                         │
   (eyeball only the flagged discrepancies + the 14 Douay≠Vulgate chapters)
                         ▼
scripts/core/versification.py :: vulgate_to_kjv   ← _VULGATE_SEGMENTS filled
                         │
   ┌─────────────────────┴─────────────────────┐
scripts/extract_douay.py            scripts/extract_vulgate.py
   (extract(remap=vulgate_to_kjv)      (extract(remap=vulgate_to_kjv))
    + Douay-only per-source overrides)
                         │
            popup_versions._BAKED_NOW += {douay, vulgate}
                         ▼
        regen → categorize-diff → ebible verify → epubcheck → tests → docs
```

### Components (each independently testable)

1. **`_vg_gen.py`** (repo-parent, throwaway). Pure data transform: `vul.json` + `eng.json` → segment rules in the project's `_Seg = (src_lo, src_hi, kjv_ch|None, kjv_v_lo)` shape (`_HI = 9999` for open upper bound). Its second output — the **discrepancy report** — is the actual work product; the segments are mechanical.
   - **Composition:** Copenhagen maps every tradition to `org` (original H/G numbering); the KJV skeleton ≈ `org` for almost all non-Psalm books. So the base map is `vul → org` (from `vul.json`). The small, *known* `org↔KJV(eng)` deltas — `3jn 1:14/15`, `rev`, `mal 4↔3`, `joe 2↔3` — are reconciled from `eng.json` (or left identity), and **Psalms go through `_psalm_map`, not the composition** (see exception below). `eng.json` is not blindly inverted (its merges aren't 1:1-invertible); it is consulted only for those enumerated spots. Every emitted coord is validated against `canonical_verse_counts`; anything failing `coord_in_canonical_extent` is **reported, not emitted** — so a composition gap surfaces as a discrepancy rather than a silent mis-map.
   - **Psalms exception:** REUSE the existing content-verified `_psalm_map` (LXX/Vulgate→KJV); use `vul.json` PSA entries only to *cross-check* it and to confirm the 3 flagged per-psalm fixes (`psa 20/44/56`) land in `_VULGATE_PSALM_FIXES`.
2. **`versification.vulgate_to_kjv`** (exists, WIP). `_VULGATE_SEGMENTS` / `_VULGATE_PSALM_FIXES` / `_VULGATE_CROSS` get filled from the generated+verified rules. Logic unchanged: OMIT set → `None`; psalms → `_psalm_map`+fixes; segmented books → `_apply_segments`; else identity; final `coord_in_canonical_extent` guard.
3. **Daniel/Esther additions → `_VULGATE_CROSS`.** From the table: Vulgate `Dan 3:24-90 → paz` (Song of Three / Prayer of Azariah), `Dan 13 → sus`, `Dan 14 → bel`, `Dan 4` offset; `Esther 10-16 → aes` (or omit per the LXX-aes precedent). Cross-book callables, mirroring the LXX `_cross_book`.
4. **`_vg_verify.py`** (exists). Unchanged role: the objective post-encoding gate — applies the map to the English Douay and word-overlap-compares each KJV verse vs mapped-Douay; **SHIFTS = 0** required. Catches count-matching mis-maps the extent guard can't.
5. **Drivers `extract_douay.py` + `extract_vulgate.py`** (new, thin). `extract(source, remap=vulgate_to_kjv)` over `extract_translation`. The **14 Douay≠Vulgate chapters** (English split differs from the Latin) are per-source overrides in the drivers — now cross-checked against the table rather than guessed.

## Data flow & deuterocanon

- **Protocanon (39 OT + 27 NT):** table-driven segments, identity where the table is silent.
- **Deutero present in `vul.json`** and in the canonical skeleton → map from the table: `wis, bar, lje, sus, bel, paz(S3Y), 1es, man, 1ma, 2ma`. (`1ma/2ma` confirmed present in `canonical_verse_counts`.) Each still passes the `_vg_verify` overlap gate; any that reveals a divergent Latin recension is demoted to OMIT with a documented reason.
- **OMIT (`None`):** `tob, jdt, sir` — different recension, table-corroborated.

## Error handling & correctness gates

1. `_vg_gen.py` discrepancy report — the human-review surface. Three classes: (a) table vs already-encoded segment disagreements (e.g. the `gen 49` shift-start v31-vs-v32 mismatch — adjudicate against source text); (b) table vs actual eBible verse counts (data the table didn't anticipate); (c) `_psalm_map` vs `vul.json` PSA.
2. `coord_in_canonical_extent` guard at the adapter boundary (out-of-extent → `None`), as for every existing translation.
3. `_vg_verify.py` SHIFTS = 0 — structural+overlap gate per book.
4. **Byte-compat:** `remap=None` is byte-identical to a plain extract (already proven for the `apply_remap` infra). After baking, categorize-diff **by aside-id** (not line-diff — shared split files create false line-diffs) must show only `vnote-douay` / `vnote-vulgate` added, all other aside content unchanged.
5. `ebible verify` errors=0; `epubcheck` 0/0/0/0 on **catholic-study** + **anglican-bcp** (the editions that surface Latin/Catholic translations).

## Testing (TDD)

- `_vg_gen.py`: pin composed output against a handful of hand-verified anchors incl. the cross-chapter cases (`num 13:1→12:16`, `1ki 4:21→5:1`, `2ch 2:1→1:18`).
- `versification.vulgate_to_kjv`: representative coord per divergent book + each OMIT returns `None` + each `_VULGATE_CROSS` addition + Psalms reuse.
- Drivers: book/verse counts; the 14 Douay≠Vulgate overrides; `remap=None` byte-identity.
- Bake: categorize-diff additive-only; `ebible verify`; epubcheck on the 2 editions.
- Reuse the existing `_vg_verify.py` as a test-invoked gate where practical.

## Follow-ups (logged, NOT in this arc)

1. **`ethiopian_custom.json` as a Ge'ez-track reference.** Useful *cross-reference* (validate-don't-adopt) for the standalone Ge'ez/Amharic Bibles and the deferred no-KJV books: it encodes Prayer-of-Manasseh as `2Ch 33:26-38`, the Ethiopian Jeremiah OAN reorder, `Dan→S3Y/SUS/BEL`, Reproof↔Proverbs, Psalm 151→PS2, and candidate shapes for `jub/4ba/mq1/mq3`. Caveats: it OMITS 2 Enoch, 1 Clement, 2 Meqabyan, and its `ENO` shape looks non-standard (~42 ch vs the usual 108) — so it checks the project's manuscript-derived canon, it does not replace it. Same CC BY-SA → facts-only.
2. **Re-verify already-shipped segments against the table.** The `gen 49` discrepancy suggests the hand-derived WLC/LXX/Arabic/JPS segments may carry gen49-type off-by-ones. A fast pass diffing each shipped `*_to_kjv` against `vul.json`/`org.json`/`lxx.json` would catch them. Correctness fast-follow.

## Out of scope

- No change to the popup-version model, themes, covers, or build pipeline.
- No defaults change (`douay`/`vulgate` become *pickable* in `/customize` for the 9 non-geez/amharic editions via the `bakes_now` gate; per-edition default-on is a later tuning pass).
- No Ge'ez/no-KJV-book work (follow-up #1).
