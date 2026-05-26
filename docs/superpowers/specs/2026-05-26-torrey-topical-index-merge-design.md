# Design — Surface Torrey in the EPUB Topical Index (Nave's + Torrey merge)

**Created:** 2026-05-26
**Status:** awaiting user review
**Phase:** Track C follow-on (post-Torrey-ingest "make it visible")
**Companions:** `dev/MATRIX_MAP.md` (presentation pipeline) · `dev/CLAUDE_PROJECT_RULES.md` §9 "add edition feature" + §6.5 additive-defaults · `scripts/matter_pages.py` (the topical-index back-matter functions)

---

## 1. Problem & goal

The 2026-05-26 Track C ingest promoted **21,762 `topic-torrey` notes** (Torrey's New Topical Textbook, 1897) into the corpus, but those notes are **filtered from inline markers** (Wave 3 policy) and the EPUB back-of-book Topical Index page is rendered **Nave's-only** (`matter_pages.build_topic_index` + `render_topical_index_page`). Net effect: Torrey enriches the corpus and the web app, but **a flagship EPUB reader never sees it**. This has been the standing open item in `SESSION_STATE.md` since the ingest.

**Goal:** merge Torrey into the EPUB topical index so a reader sees both topical authorities, with the relationship between them made honest and visible.

---

## 2. Grounding data (measured 2026-05-26, read-only analysis of both JSON caches)

The design is shaped by what the two sources *actually* are — not by the "corroboration" assumption in the backlog note:

| Measure | Result |
|---|---|
| Nave's topics | **4,604** — predominantly an ALL-CAPS **proper-name gazetteer** (`AARON`, `ABADDON`, people/places) |
| Torrey topics | **630** — **doctrinal/thematic**, Title Case (`Access to God`, `Adoption`, `Assurance`) |
| Exact-string name overlap | **0** (pure capitalization mismatch) |
| Casefold+strip name overlap | **166** themes (26% of Torrey, 3.6% of Nave's) |
| Of those, ≥1 shared verse | **162 / 166 = 98%**; 3,165 individually-corroborated verses |
| Near-total agreers (examples) | `vanity` 86 of 87/87 · `glorifying god` 62 of 63/63 · `assurance` 60 of 60/64 |

**Conclusions that drive the design:**

1. **The merge is mostly *complementary*, with a *corroboration core*.** Torrey adds ~464 doctrinal themes on top of Nave's name-heavy index; ~166 themes are shared, and where shared they genuinely co-cite verses (98%).
2. **Casefold normalization is mandatory** — exact match is literally 0, so a naive union would render the corroboration tag on nothing.
3. **Comma-base normalization is rejected** — it collapses Torrey's deliberate subtopics (`Affliction, Consolation Under` vs `Affliction, Prayer Under`) into one, destroying real editorial distinctions.
4. The corroboration tag honestly lands on **themes** (assurance, deceit, slander, marriage, prudence), not on the proper-name gazetteer — which is the right reader signal.

---

## 3. Design

### 3.1 Reader-facing result (Option A — unified, topic-tagged)

A single alphabetical Topical Index page. Each topic header carries a small source tag:

```
TOPICAL INDEX
A concordance of verses by theme, drawn from Nave's Topical Bible
(Orville J. Nave, 1896) and Torrey's New Topical Textbook (R.A. Torrey,
1897), both public domain. (N·T) marks themes both works treat; (N)
Nave's only; (T) Torrey only. Only verses present in this edition are shown.

Assurance (N·T)   Job 19:25; Ps 23:4; Rom 8:38; 2 Tim 1:12; ...
Adoption (T)      John 1:12; Rom 8:15; Gal 4:5; ...
Aaron (N)         Exod 4:14; Exod 28:1; Heb 5:4; ...
```

- **Tags:** `(N·T)` both · `(N)` Nave's only · `(T)` Torrey only (middle-dot U+00B7).
- **Display casing: Title Case.** Nave's `AARON` → `Aaron`; Torrey names kept verbatim (already Title Case). Reads consistently instead of shouting.
- **Honest intro:** coverage-first ("drawn from … and …"), corroboration as the trust signal — **no over-promise of verse-by-verse agreement**.

### 3.2 Merge algorithm — `build_merged_topic_index(naves, torrey, canon_books, book_order)`

New pure function in `matter_pages.py`. Returns `list[tuple[display: str, tag: str, refs: list[(book, ch, vs)]]]`.

```
norm(t)  = casefold → collapse internal whitespace → strip edge punctuation/quotes
           (NO comma split — preserves Torrey subtopics)

For each present source, group original topic names by norm(name); for each group
collect the union of its verse refs, canon-filtered (drop refs whose book ∉ canon_books
when canon_books is not None).

For the union of norm-keys across both sources:
    nav_refs = union of Nave's refs for that key   (∅ if absent)
    tor_refs = union of Torrey refs for that key    (∅ if absent)
    all_refs = sorted(set(nav_refs) | set(tor_refs), key=(book_order, ch, vs))
    if not all_refs: continue                        # no in-canon ref → omit topic
    tag = "N·T" if nav_refs and tor_refs else "N" if nav_refs else "T"
    display = torrey_original (verbatim)  if torrey has the key
              else _title_topic(naves_original)      # ALL-CAPS → Title Case
    # if a norm-key maps to >1 original name in the chosen source,
    # use the first in sorted() order (deterministic; collisions are rare)
    emit (display, tag, all_refs)

Sort emitted entries alphabetically by casefold(display).
```

- `_title_topic(s)` — helper that Title-Cases a Nave's ALL-CAPS name (`ABED-NEGO` → `Abed-Nego`), leaving possessive `'s` lowercase. Small, unit-tested.
- Refs are **deduped across sources** — the 13–21% that co-occur simply appear once (the natural representation; the `(N·T)` tag already conveys the agreement).

### 3.3 Render — `render_merged_topical_index_page(version, merged_index, book_abbrev)`

New render fn; mirrors `render_topical_index_page` but emits the tag span and the both-source intro:

```html
<p class="topic-entry"><span class="topic-name">Assurance</span>
  <span class="topic-src">(N·T)</span> Job 19:25; Ps 23:4; ...</p>
```

- New CSS class `.topic-src` (small, muted) in `epub_working/stylesheet.css`.
- `render_topical_index_page` gains an optional `intro=<current Nave's text>` param (default unchanged ⇒ **byte-identical** for the Nave's path). Used to give the Torrey-only mode its own attribution line.

### 3.4 Mode selection in `inject_back_matter`

Read the new edition field (default `"both"`); load each source independently (either may be missing in a given env). Branch:

| `topical_index_source` | Behavior |
|---|---|
| `naves` | Today's path exactly — `build_topic_index(naves)` + `render_topical_index_page()` (default intro). **Byte-identical to current builds.** |
| `torrey` | `build_topic_index(torrey)` + `render_topical_index_page(intro=Torrey)`. No tags. |
| `both` (default) | `build_merged_topic_index(naves, torrey, …)` + `render_merged_topical_index_page()`. |

**Graceful degradation** (preserves the existing `SourceMissingError` resilience): in `both` mode, if Torrey is missing → fall back to the Nave's path (byte-identical to today); if Nave's is missing → Torrey path; if both missing → skip the page entirely (as today). `topical_ok` stays the gate for OPF/spine/nav registration.

### 3.5 Configurability wiring (RULES §9 "add edition feature")

`topical_index_source` ∈ `{naves, torrey, both}`, **default `both`** (default lives in code; no `editions.yaml` edit needed — the field is written only when a builder picks a non-default value):

1. `scripts/api/editions.py` — add to the allowed-field list + an enum validator.
2. `scripts/web.py::api_customize_data` — surface per-edition value, default `"both"`.
3. `scripts/templates/customize.py` — a `<select>` (Both · Nave's only · Torrey's only).
4. `matter_pages.inject_back_matter` — reads `edition.get("topical_index_source")` (§3.4). No build_one signature change (the `edition` dict is already passed at `build_edition.py:2990`).

### 3.6 Sources & Acknowledgments page

Add a Torrey line to `_sources_sections()` (`matter_pages.py:~554`, right after the Nave's entry):

```
Torrey's New Topical Textbook, R.A. Torrey, 1897. Public Domain.
```

This static page already lists Nave's/Easton's unconditionally, so Torrey is listed unconditionally too (it is now a project source).

---

## 4. Files touched

| File | Change |
|---|---|
| `scripts/matter_pages.py` | + `build_merged_topic_index`, `render_merged_topical_index_page`, `_title_topic`; `render_topical_index_page` gains `intro=` (default unchanged); `inject_back_matter` mode branch; Torrey in `_sources_sections` |
| `scripts/core/sources.py` | (none — `torrey_topical()` loader already exists) |
| `scripts/api/editions.py` | allowed-field + enum validator for `topical_index_source` |
| `scripts/web.py` | `api_customize_data` surfaces the field (default `both`) |
| `scripts/templates/customize.py` | `<select>` control |
| `epub_working/stylesheet.css` | `.topic-src` style |
| `tests/test_topical_merge.py` (NEW) | merge/render/mode/config/byte-compat pins |
| `dev/launcher.spec` | ensure `content/sources/torrey_topical.json` is bundled (frozen app shows the merge, not the degraded Nave's-only) |

---

## 5. Testing (TDD — write first)

- **Merge logic:** both-source key → `N·T` + deduped union; Nave's-only → `N`; Torrey-only → `T`; casefold match (`ASSURANCE`+`Assurance` → one `N·T`); canon filter drops out-of-canon refs and omits a topic with no in-canon ref; refs in canonical order; alphabetical sort by display.
- **`_title_topic`:** `ABED-NEGO`→`Abed-Nego`, `GOD`→`God`, possessive left sane.
- **Render:** tag span present, both-source intro, HTML-escaping, empty-index fallback line.
- **Byte-compat (critical):** `topical_index_source="naves"` (and the `both`→Torrey-missing degrade path) produce **byte-identical** output to the current `build_topic_index`+`render_topical_index_page` — pin via direct comparison.
- **Config:** round-trip save/load; invalid value rejected; `api_customize_data` default `both`.
- **`inject_back_matter`:** each mode writes the expected page; Torrey-missing degrades to Nave's; both-missing skips (no OPF/spine/nav entry).
- **Bake-and-prove gate (RULES §9):** rebuild a flagship edition → **epubcheck 0/0/0/0**; topical page present with tags; `ebible verify` errors=0. Run `lint_rules` 16/0/0, `ruff format --check`, the full targeted suite.

---

## 6. Byte-compat & defaults note (explicit, user-approved)

Default `both` **changes existing editions' topical-index output** (the index grows + gains tags). This is an **intended, approved** product enhancement — the reason Torrey was ingested — not an accidental side effect, so it is a deliberate exception to RULES §6.5 "publishers opt in" / §7.2 "unset ⇒ byte-identical." The `naves` mode remains available and is held byte-identical to today by test. User confirmed default `both` on 2026-05-26.

---

## 7. Out of scope (YAGNI)

- Per-verse source marks (Option C) — rejected: noisy on e-ink; the 13–21% co-citation rate doesn't justify it.
- Two separate sections (Option B) — rejected: hides the corroboration the data shows is real.
- Edition-aware Sources page — the static unconditional listing is sufficient; per-edition source crediting is a larger change not needed here.
- Inline `topic-torrey` markers — Wave 3 deliberately filters topical notes from inline; unchanged.
- Voyage AI / semantic topic alignment beyond casefold — out of scope; the measured casefold result is sufficient.
