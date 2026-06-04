# Hierarchical edition customization — "navigate your Bible" design

**Status:** DRAFT (awaiting user review) · **Date:** 2026-06-04 · **Author:** Claude (brainstormed with Boggy)
**Proposed phases:** ρ.3 (symbol hierarchy) · ψ.8.5 (popup hierarchy) · ξ.1 (the `/build-my-bible` navigator console)
**Supersedes:** `2026-06-04-per-book-note-family-selection-design.md` (the per-book/3-tier draft — its resolver/ref-id/byte-stability groundwork is folded in here).
**Grounded by codebase maps:** `wf_8b11a5df-ff2`, `wf_fc24b036-8cc`.

---

## 1. Goal — the vision

Let the builder **navigate their edition exactly like a Bible**, and customize at every level of
that hierarchy. Open the Bible → it has options; open a book → options; open a chapter → options;
open a verse/note → flip individual items. Two things are controllable at every level:

- **Note symbols** — the note families (categories) and their individual kinds (the markers in the
  text).
- **Translation popups** — which translations appear in each verse's popup.

```
📖 BIBLE (edition)        symbols: on/off any family or kind   ·   popups: choose languages
   📕 BOOK                same options, scoped to the book        (overrides the Bible level)
      📄 CHAPTER          same options, scoped to the chapter     (overrides the book level)
         ✓ VERSE / NOTE   flip individual notes · per-verse popup (overrides the chapter level)
```

The drill-down navigation **is** what makes individual selection easy — you never hunt through
92,000 notes; you walk to the chapter and they're right there.

**Hard requirement (RULES §6.5):** with nothing overridden, every build is **byte-identical to
today.** Builders opt *in*. The 9 KJV editions stay byte-stable.

---

## 2. Scope reality (verified by codebase map)

| Piece | State |
|-------|-------|
| **Symbols — Bible level** | ✅ exists (`enabled_kind_codes`, `/matrix`) |
| **Symbols — book level** | ❌ new |
| **Symbols — chapter level** | ❌ new |
| **Symbols — individual (force-OFF)** | ✅ exists (`disabled_note_ids`, `/sources` checkboxes, Phase ρ.1/ρ.2) |
| **Symbols — individual (force-ON)** | ❌ new (`enabled_note_ids`) — user: "maximum options" |
| **Popups — Bible level** | ✅ exists (`popup_languages_default`) |
| **Popups — book level** | ✅ exists (`popup_languages_per_book`) |
| **Popups — chapter level** | ❌ new |
| **Popups — individual verse** | ❌ new |
| **The navigation UI** | ❌ new (`/build-my-bible`) |

**Key enabling finding:** the build already strips notes by an opaque set of HTML **ref-ids**, and a
ref-id (`ref-<prefix><cc><vv><suffix>`) **already encodes book+chapter+verse**. So per-chapter and
per-verse *symbol* control needs **no new build plumbing** — only a richer resolver that enumerates
the right ids. Popups need exactly **one** new resolver argument threaded to **one** existing call
site.

---

## 3. The unified model

### 3.1 Four levels, most-specific-wins

For any selectable, resolve its state at a coordinate by the **most specific explicit setting**:

```
individual (verse / note)  >  chapter  >  book  >  Bible (edition default)
```

Anything unset at a level **inherits** from the level above. Unset everywhere ⇒ byte-identical.

### 3.2 Bulk toggle clears finer overrides in scope (UX, user-stated)

When the builder flips a whole symbol (or popup language) on/off **at a level**, that is a clean
**bulk set**: the UI **clears the finer overrides for that selectable within that scope** before
applying (so a coarse decision doesn't silently leave stale finer exceptions underneath), then the
builder may add finer overrides again. This is a **UI behaviour**, not a resolution rule — the stored
data is just the per-level override sets, and the build resolves them most-specific-wins.

### 3.3 Two dimensions, slightly different per-level value types

- **Symbols** use **signed tokens** per scope (`on` / `off` lists; a token is a category id *or* a
  kind code). Signed because you want to flip one family without re-listing all of them, in either
  direction. Individual level = `disabled_note_ids` (off) + `enabled_note_ids` (force-on).
- **Popups** use an **absolute language set** per scope (most-specific scope's set wins outright),
  matching the existing `popup_languages_default` / `popup_languages_per_book` semantics.

### 3.4 Precedence detail

**Symbols** (note of kind `k`, category `c`, at `book:ch:vs+suffix`):
```
1. note-id ∈ enabled_note_ids      → ON  (ABSOLUTE finest: overrides family/tradition/time/disable/phase/AI;
                                          only limit = the note exists in the base corpus)
2. note-id ∈ disabled_note_ids     → OFF
3. chapter token (kind > category, OFF beats ON) in *_per_chapter["book:ch"]
4. book token    (kind > category, OFF beats ON) in *_per_book["book"]
5. edition default: k ∈ enabled_kind_codes(edition)        (the existing 4 gates)
HARD GATES (phase, AI) bound levels 3–5 — a family-level ON cannot bulk-enable a phase/AI kind —
but an explicit per-NOTE force-on (level 1) overrides them. Explicitness wins.
```

**Popups** (verse at `book:ch:vs`):
```
1. popup_languages_per_verse["book:ch:vs"]   if present  → that set
2. popup_languages_per_chapter["book:ch"]    if present  → that set
3. popup_languages_per_book["book"]          if present  → that set
4. popup_languages_default                   if set      → that set
5. DEFAULT_POPUP_WITNESSES                                → fallback
(legacy ids mapped via popup_versions.resolve_version_id, as today)
```

---

## 4. Storage schema (all exceptions-only; flat strings; byte-identical when empty)

The project's custom YAML parser supports flat list fields, not nested maps
(`config._parse_yaml_records`), so every per-scope field is a flat list of `"<key>=<values>"`
strings, encoded sorted by canonical book order then numeric chapter/verse.

**Symbols:**
```yaml
# Bible level — UNCHANGED existing fields:
enabled_categories: [...]   enabled_kinds: [...]   disabled_kinds: [...]
# Book level (signed tokens = category id | kind code):
note_families_on_per_book:      [ "gen=xref,comm-patristic" ]
note_families_off_per_book:     [ "exo=xref" ]
# Chapter level (key = book:ch):
note_families_on_per_chapter:   [ "gen:1=xref" ]
note_families_off_per_chapter:  [ "exo:3=comm" ]
# Individual level (key = full note-id book:ch:vs[suffix]:kind):
disabled_note_ids: [ "gen:1:1a:xref" ]     # EXISTS (force-off)
enabled_note_ids:  [ "exo:3:2:comm-patristic" ]  # NEW (force-on)
```

**Popups (absolute language set per scope):**
```yaml
popup_languages_default:     [ ... ]              # EXISTS (Bible level)
popup_languages_per_book:    [ "gen=wlc,lxx-greek" ]  # EXISTS (book level)
popup_languages_per_chapter: [ "gen:1=wlc" ]          # NEW (key = book:ch)
popup_languages_per_verse:   [ "gen:1:1=wlc,lxx-greek" ]  # NEW (key = book:ch:vs)
```

Decoders/encoders mirror `decode_per_book_languages`/`encode_per_book_languages`
(`build_edition.py:869`) and `decode_per_book_traditions` (`:178`), generalized to a `book:ch` /
`book:ch:vs` key. Validity filters: symbol tokens ∈ `category ids ∪ kind codes`; popup langs ∈
`POPUP_LANGUAGES`. Unknown keys/values rejected at write, trusted at build (existing split).

---

## 5. Build path — Dimension N (symbols)

**No new strip plumbing.** `build_one` already assembles `disabled_html_ref_ids`
(`build_edition.py:2744-2776`) from `disabled_note_ids` + tradition + time filters, and `filter_html`
strips exact ref-id matches (`:1115-1132`). We add three things:

1. **A richer corpus iterator.** `_iter_note_ref_traditions` (`:110-155`) yields
   `(ref_id, tradition, book)`. Add a sibling that yields
   `(ref_id, note_id, book, chapter, verse, suffix, kind, category)` (it already has `ch_i/vs_i/suffix`
   in scope at `:146-154`; add `kind = tup[4]` + a `kinds_by_code()`→`category` lookup). One iterator
   feeds both the resolver and the UI enumeration.

2. **`compute_symbol_disabled_html_ref_ids(edition)`** — mirrors
   `compute_tradition_disabled_html_ref_ids` (`:264-296`). **Short-circuits to empty** when no
   book/chapter/individual symbol override and no `enabled_note_ids` (the common case → no corpus
   walk, zero cost). Otherwise walks the iterator; for each note resolve §3.4-symbols; collect OFF
   ref-ids into the disabled set and force-ON ref-ids into a separate `force_on` set.

3. **Whole-kind-strip narrowing + force-on subtraction** in `build_one`:
   - `overridden_kinds` = kinds touched by any book/chapter token (categories expanded) ∪ kinds of
     `enabled_note_ids` notes.
   - `disabled_kinds_for_filter = (all_kinds − enabled) − overridden_kinds` (non-overridden
     edition-disabled kinds keep the efficient whole-kind strip; overridden kinds resolve at ref-id
     granularity, so a per-book/chapter/note ON can re-include them).
   - `disabled_html_ref_ids |= compute_symbol_disabled_html_ref_ids(edition)`
   - `disabled_html_ref_ids -= force_on_ref_ids` (level-1 force-on wins over everything, incl.
     tradition/time/disable).

**Byte-stability:** no symbol override + no `enabled_note_ids` ⇒ `overridden_kinds=∅`,
`disabled_kinds_for_filter == (all−enabled)` (today's value), compute returns ∅ ⇒ **identical**.

---

## 6. Build path — Dimension P (popups)

**One resolver, one call site.** Extend
`_resolve_popup_languages(edition, book_code, chapter=None, verse=None)` (`build_edition.py:839-866`)
with the §3.4-popup order (add `decode_per_chapter_languages` / `decode_per_verse_languages`). Change
the single call site inside the per-aside `_process` callback (`:1025`) from
`_resolve_popup_languages(edition, book)` to `_resolve_popup_languages(edition, book, chapter=ch,
verse=vs)` — `ch`/`vs` are already extracted at `:1018-1020`.

The per-verse bake already emits one `<aside class="vnote" id="vnote-{code}-{ch}-{vs}">` per verse
with **all** versions (`generate_verse_popups.py`); the strip already runs per-aside over
`ALL_POPUP_LANGUAGES` (`:1069-1073`); only the `active_langs` *input* becomes verse-aware. The
§4.3 last-resort-English keep (`:1066-1068`) and the standalone `popup_languages_default=[]` guard are
unchanged.

**Byte-stability:** absent `popup_languages_per_chapter`/`_per_verse` ⇒ resolver falls straight
through to the per-book/default tiers ⇒ identical set ⇒ identical strip ⇒ **byte-identical**.

---

## 7. Enumeration accessors (resolver + UI)

- Books (canonical, per-canon): `config.books_by_code()` / `config.load_books()`;
  `matrix.edition_canon_books` / `api_customize_data.books_canonical` + `edition_canon_books`.
- Chapters per book: `book["ch_count"]`; verse counts: `scripts/core/canonical_verse_counts.py`.
- Per-book/chapter note structure: `/api/sources/<book>` already returns notes grouped by chapter
  (`web_sources.py`); `/build-tracker` already exposes `per_book[].by_chapter[]` counts
  (`web_editions.py:46-188`); `matrix.per_book_kinds_dict` / `per_chapter`.
- Notes-in-(book,chapter) for the leaf UI: the new iterator (§5.1) + the existing `/api/sources/<book>`.

---

## 8. The `/build-my-bible` navigator console (UI)

A **new console** (agents' recommendation, over overloading `/customize`/`/sources`/`/matrix`, each
of which has a distinct single concern). It is the unified 4-level drill-down for **both** dimensions
and the heart of the "wow, that's mine" demo.

**Layout** (reuse `/sources` left-rail + `/build-tracker` heat-grid patterns):
```
[edition picker]
LEFT: books (canonical order, edition canon)
MAIN: breadcrumb  Bible ▸ Genesis ▸ ch 3 ▸ v 2
  At the CURRENT level, two panels:
   ① Symbols:  per-category rows (symbol + label), tri-state inherit/on/off,
               each expands to its kinds (tri-state). "Bulk = clear finer in scope."
   ② Popups:   the popup-language checklist (absolute set for this scope).
  Drill in: click a book → chapters; click a chapter → verses; click a verse → its notes + per-verse popups.
```

**Behaviour:** lazy-load per book then per chapter (sparse — only verses that have notes get symbol
rows; every verse can get a popup set). Tri-state controls compute the signed token / absolute set on
save. Bulk toggle clears finer overrides in scope (§3.2). Dirty-check includes all inputs/selects
(RULES §6.4). Books/chapters/verses in canonical order (RULES §6.1).

**API:**
- `GET /api/build-my-bible/<edition>` → edition meta + `books_canonical` (with `ch_count`) + the
  current per-level override state for both dimensions; per-book/chapter detail lazy via
  `GET /api/build-my-bible/<edition>/<book>` (and `/<book>/<ch>`).
- `PUT /api/build-my-bible/<edition>/config` → validates + merges + writes the per-scope fields via
  `notes_io.atomic_write` (the existing per-book / note-toggle write pattern; reuses the
  `_patch_yaml_*` helpers).

**Registration (RULES §6.2):** add `("/build-my-bible", "build my bible")` to `CONSOLES`
(`_design.py:2239`); serve the template in `web.py`; embed `HEADER_NAV_LINKS("/build-my-bible")`; the
§6.2 lint then enforces cross-linking across all consoles. The existing `/sources` per-note checkboxes
and `/customize` per-book matrices stay (they remain valid faster paths); `/build-my-bible` is the
unified navigator that also writes the same underlying fields, so they stay consistent.

---

## 9. Worked examples

1. **Cross-refs off whole-Bible, on in Genesis ch 1 only.** `disabled_kinds`/no-enable at edition;
   `note_families_on_per_chapter: ["gen:1=xref"]`. → `xref ∈ overridden_kinds` (not whole-stripped);
   the symbol compute disables `xref` ref-ids everywhere except `gen:1*`. Cross-refs appear only in
   Genesis 1.
2. **Commentary on book-wide, off in one chapter, one note forced back on.**
   `note_families_on_per_book:["psa=comm"]`, `note_families_off_per_chapter:["psa:23=comm"]`,
   `enabled_note_ids:["psa:23:1:comm-patristic"]`. → commentary throughout Psalms, suppressed in
   Psalm 23 — except the one patristic note on 23:1, which is force-on.
3. **Hebrew-only popups for the Torah, add LXX just in Genesis 1.**
   `popup_languages_per_book:["gen=wlc","exo=wlc",...]`, `popup_languages_per_chapter:["gen:1=wlc,lxx-greek"]`.
4. **One verse, special.** `popup_languages_per_verse:["psa:22:1=wlc,lxx-greek,vulgate"]` shows three
   languages only on Psalm 22:1.

---

## 10. Open decisions — resolved (defaults chosen; flag to change)

| # | Question | Decision |
|---|----------|----------|
| Levels | How many? | **Four:** Bible → book → chapter → individual (user). |
| Dimensions | Which? | **Two:** note symbols **and** translation popups (user). |
| Symbol granularity | Category or kind? | **Both** — category surface, kind drill-down (user). |
| Symbol value type | Absolute or signed? | **Signed tokens** (on/off) per scope — flip one family either direction. |
| Popup value type | Absolute or signed? | **Absolute language set** per scope (matches existing per-book popups). |
| Force-on | Tier-individual ON of an off-family note? | **Yes** (`enabled_note_ids`) — absolute finest, overrides all incl. phase/AI (user: "maximum options"). |
| Bulk vs fine | Coarse toggle effect | **Clears finer overrides in scope (UI)**; resolution stays most-specific-wins (user). |
| Non-canon keys | book/ch/verse outside canon | Reject unknown book codes at write; allow non-canon as harmless dead config (build skips). |
| UI home | New console or extend? | **New `/build-my-bible` console**; keep `/sources` + `/customize` matrices as valid faster paths writing the same fields. |
| Per-verse popup storage | size | Exceptions-only (only verses the builder touches) — scales. |

---

## 11. Testing & byte-stability proof obligations

- **Byte-stability gate** (`tests/test_byte_stability_gate.py`, ~205s) green; **regen 9 KJV + empty
  `git diff epub_working/`**; flagship `catholic-study` epubcheck 0/0/0/0; `test_nested_anchors` +
  `check_nested_anchors --fix`; `ebible verify`. The 9 KJV editions carry no overrides → must be
  byte-identical (the whole feature is latent until a builder sets something).
- **Resolvers:** `enabled_kind_codes_for(...)` == `enabled_kind_codes` with no override (extends the
  tri-path invariant); most-specific-wins across all 4 levels; OFF-beats-ON, kind-beats-category;
  hard gates not bypassable by family levels; `enabled_note_ids` force-on overrides everything.
  `_resolve_popup_languages` 4-level fallthrough + legacy-id mapping.
- **Encode/decode:** round-trip; `book:ch` + `book:ch:vs` keys; canonical-then-numeric sort; unknown
  filtered.
- **Build integration:** the worked examples (§9) each produce the right notes/popups per coordinate;
  `overridden_kinds` narrowing exact; compute short-circuits empty.
- **API + UI:** `/api/build-my-bible` shapes; `PUT config` happy-path + every rejection; the navigator
  renders canonical, lazy-loads, tri-state round-trips, dirty-check covers it; cross-link lint passes.

---

## 12. Phasing (each phase shippable + byte-stable; TDD; 5-leg save; marathon core untouched)

- **Phase A — Symbol hierarchy (headless engine).** book + chapter signed fields + `enabled_note_ids`;
  the corpus iterator; `compute_symbol_disabled_html_ref_ids`; `overridden_kinds` narrowing +
  force-on subtraction; the per-coordinate resolver. **Byte-stability gate is the ship bar.** A
  builder could hand-edit `editions.yaml` and it works. *(Subsumes the superseded per-book draft.)*
- **Phase B — Popup hierarchy (headless engine).** `popup_languages_per_chapter`/`_per_verse` +
  decoders; the `_resolve_popup_languages` signature + the `:1025` call-site change. Byte gate.
- **Phase C — `/build-my-bible` navigator console.** Template + JS drill-down (both dimensions, all
  levels, tri-state, bulk-clears-finer, lazy-load) + the API (`GET …/<edition>[/<book>[/<ch>]]`, `PUT
  …/config`) + cross-link registration. This is the "wow" — the experience over the engine.
- **Phase D — Visibility + copy + polish.** `/build-tracker` per-level resolved-state; rewrite the
  website "How you make it yours" copy to promise navigate-your-Bible control; reconcile `/sources` +
  `/customize` matrices to show/round-trip the new levels; doc/INDEX/REPO_MAP/MATRIX_MAP currency.

Phases A & B are independent (different fields/build hooks) and can land in either order; C depends on
both; D follows.

---

## 13. Non-goals

- No change to the Tier-1 resolver gate logic, the existing `/sources` per-note feature, or the
  per-book popup/tradition fields (all reused).
- No new EPUB output for the 9 KJV editions (byte-identical).
- No nested-YAML schema (keep flat `"key=values"` lists).
- No wildcard support in `filter_html` (the resolver enumerates concrete ids).
- Not pulling forward the manuscript/Patrologia lanes.

---

## 14. File-change map

| File | Change |
|------|--------|
| `scripts/build_edition.py` | new decoders/encoders (per-chapter/per-verse, symbol tokens); richer corpus iterator; `compute_symbol_disabled_html_ref_ids`; `overridden_kinds` + `disabled_kinds_for_filter` + force-on in `build_one`; `_resolve_popup_languages(...,chapter,verse)` + `:1025` call-site |
| `scripts/core/config.py` | per-coordinate symbol resolver `enabled_kind_codes_for(edition, all_kinds, book, chapter, note_id)` (+ a phase/AI gate helper) |
| `scripts/api/editions.py` | `EDITABLE` += new fields; validators; the `/build-my-bible` config writer (reuse `_patch_yaml_*`, `notes_io.atomic_write`); `enabled_note_ids` write |
| `scripts/web_editions.py` | `api_customize_data` decodes new fields; `api_build_my_bible(edition[,book[,ch]])` |
| `scripts/web.py` | routes: `/build-my-bible`, `/api/build-my-bible/...` |
| `scripts/templates/build_my_bible.py` | NEW navigator console template + JS |
| `scripts/templates/_design.py` | `CONSOLES` += `/build-my-bible` |
| `scripts/templates/{customize,sources,build_tracker}.py` | (Phase D) surface/round-trip new levels |
| `website/src/...` | (Phase D) "How you make it yours" copy |
| `tests/test_*` | resolvers, encode/decode, build integration (the §9 examples), byte-stability, API, UI-present |
| `docs/superpowers/INDEX.md` | register this spec |

---

## 15. Risks / watch-items

- **Byte-stability is the gate** on Phases A & B — prove with regen + diff before shipping.
- **Corpus-walk cost:** the symbol compute walks notes; it MUST short-circuit empty when no override
  (like the tradition filter) so standard builds pay nothing.
- **`overridden_kinds` narrowing** must be exactly `(all−enabled) − overridden_kinds`.
- **Token namespace:** category ids vs kind codes disjoint; validate against both; kind is more
  specific.
- **UI scale:** lazy-load per book/chapter; never ship a 31k-verse payload — sparse, on-demand.
- **Two write paths** (`/build-my-bible` and the existing `/sources` + `/customize`) must write the
  **same** underlying fields so they stay consistent — one set of validators/encoders, shared.
