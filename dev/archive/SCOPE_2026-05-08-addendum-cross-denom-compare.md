# Scope addendum — Cross-denominational compare apparatus (Phase ψ.8)

**Added:** 2026-05-08, after σ.3 shipped.
**Origin:** strategic-direction question from the user — "anything to
make it unique or ultra awesome?" Cross-denominational compare was the
top recommendation; user added it to active scope alongside ρ.1
(audio EPUBs) with an instruction to "do everything in the most
logical way".

## What this phase does

Today the platform produces 5 separate editions, each carrying its own
denominational viewpoint in its notes (Catholic, Protestant, Orthodox,
Jewish, Tewahedo). A buyer who wants to compare interpretations across
traditions must own all 5 EPUBs and switch between them. This phase
collapses that experience: a single popup, hovering one verse, surfaces
the editorial notes for that verse from every tradition the publisher
chose to include — side by side.

This is the **single most distinctive thing** the platform can ship.
No major Bible publisher offers a verse-level cross-denominational
note compare. It leans entirely on infrastructure that already exists
(notes are already kind-tagged; editions are already canon-filtered)
and adds one new axis: **tradition**.

## Schema change — the tradition axis

Each note today has `book`, `chapter`, `verse`, `kind`, `body`, plus
optional metadata. ψ.8 adds:

```python
("gen", 1, 1, "comm-doctrine", "<p>...</p>", {
    "tradition": "catholic",   # NEW — one of CANONICAL_TRADITIONS
    "source": "douay-rheims",  # already optional
    ...
})
```

`CANONICAL_TRADITIONS` is a closed set defined in
`scripts/core/traditions.py` (new file):

| id          | display label              | typical sources                          |
|-------------|----------------------------|------------------------------------------|
| catholic    | Catholic                   | Douay-Rheims notes, Haydock              |
| protestant  | Protestant                 | Geneva, MacArthur, Scofield (where PD)   |
| orthodox    | Eastern Orthodox           | Patristic citations, Catena Aurea        |
| jewish      | Jewish                     | Rashi, JPS notes, Talmudic citations     |
| tewahedo    | Ethiopian Tewahedo         | Ge'ez patristics, Andamta commentary     |
| cross       | Cross-tradition            | TSK xrefs, Strong's (denominationally    |
|             |                            | neutral linguistic / structural)         |

The default for any new note is `cross` — opt-in tagging of
denominational notes happens during ingestion (χ.* phases) or via
batch retag (one-time migration in ψ.8.0).

## Backfill — assigning traditions to existing 15,925 notes

`ψ.8.0` is a one-shot migration phase that walks the existing corpus
and assigns traditions:

| existing kind / source            | assigned tradition |
|-----------------------------------|--------------------|
| `xref-citation` (TSK)             | `cross`            |
| `lang-hebrew` (Strong's Hebrew)   | `cross`            |
| `lang-greek` (Strong's Greek)     | `cross`            |
| `topic-nave` (Nave's Topical)     | `cross`            |
| sample-seed notes per edition     | edition-mapped     |
| hand-authored notes               | edition-mapped     |

"Edition-mapped" means: notes that live in a specific edition's
content directory (or are explicitly tied to one of the 5 editions in
a `_meta` field) inherit the edition's denominational identity. The
mapping is in `traditions.yaml`:

```yaml
edition_to_tradition:
  catholic_study_bible: catholic
  reformed_study_bible: protestant
  orthodox_study_bible: orthodox
  jewish_study_bible: jewish
  ethiopian_tewahedo: tewahedo
```

Notes not living in any of those edition trees (the bulk — TSK, Hebrew,
Greek, Nave's are all in `content/notes/<book>.py`) get `cross`. The
migration is idempotent and produces a one-line CHANGELOG entry per
1,000 notes touched.

## Build pipeline change

Today the popup HTML is built by `scripts/build_edition.py` and
contains the language-stack (English / Hebrew / Greek) per ν.2.7. ψ.8
adds a new section to the popup: **the tradition stack**.

```
┌──────────────────────────────────────┐
│ verse popup                          │
├──────────────────────────────────────┤
│ ENGLISH text                         │
│ HEBREW text                          │   ← ν.2.7 (existing)
│ GREEK text                           │
├──────────────────────────────────────┤
│ Catholic note      ▸ (collapsed)     │
│ Protestant note    ▸ (collapsed)     │   ← ψ.8 (new)
│ Orthodox note      ▸ (expanded)      │
│ Jewish note        ▾ — Rashi: ...    │
│ Tewahedo note      — (none)          │
└──────────────────────────────────────┘
```

Implementation rules:

1. **Tradition order is canonical**, not alphabetical.
   The order is fixed in `CANONICAL_TRADITIONS` (catholic, protestant,
   orthodox, jewish, tewahedo, cross). `cross` notes appear above the
   tradition stack (linguistic stuff like "Strong's H7225" makes more
   sense above the denominational layer than below).
2. **Empty traditions render as nothing**, not "(none)". The mockup
   above shows "(none)" only for human reading.
3. **Each tradition collapses to its first 80 chars** by default; click
   to expand. Reading the full apparatus is opt-in per tradition per
   verse — keeps the popup compact even when 5 traditions are present.
4. **The reader can choose per-edition which traditions to include.**
   The new field on each edition is `traditions_default` (list).
   Example: a "Reformed Study Bible" edition might include
   `[protestant, cross]` only; a "Comparative Study Bible" master
   edition might include all 6.

## UI — /customize gets a Traditions card

A new collapsible card in the customize console (mirrors the existing
Reader Experience and Popup Languages cards):

```
☐ Traditions to include in popup
  Default for this edition:
  ☑ Catholic           ☐ Protestant
  ☐ Orthodox           ☐ Jewish
  ☐ Tewahedo           ☑ Cross-tradition (linguistic / xrefs)

  ☐ Per-book overrides (advanced)
    [matrix UI like ν.2.7's per-book languages]

  Note: the order traditions appear in the popup is fixed by
  canonical convention, not by the order you toggle them on.
```

## Tests

Per the project's §9 mental model "Add a new edition feature":

- Schema round-trip: tradition field saved + loaded preserves value.
- Default behavior: an edition without `traditions_default` ships
  byte-identical to pre-ψ.8 builds. (Critical for the §7.2
  "no-op when unset" rule.)
- Migration idempotency: running the ψ.8.0 backfill twice produces
  the same corpus.
- Build pipeline: a popup with 3 traditions enabled renders 3
  tradition blocks; a popup with 0 traditions enabled renders the
  language stack only.
- Filter respect: an edition with `traditions_default: [catholic]`
  silently omits notes tagged with other traditions from popups,
  even when those notes are in the same content tree.
- Canonical-order encoder: traditions in popup appear in
  CANONICAL_TRADITIONS order regardless of input dict iteration order.
  (Adds to the linter's `check_canonical_order_encoders` set.)

## Sub-phasing

```
ψ.8.0  Backfill                   one-shot migration of 15,925 notes
ψ.8.1  Schema + traditions module  scripts/core/traditions.py + YAML field
ψ.8.2  Build pipeline              tradition stack in popup HTML
ψ.8.3  Customize UI                Traditions card + per-book matrix
ψ.8.4  Per-book overrides          encoder/decoder pair (mirrors ν.2.7)
ψ.8.5  Wizard step                 buyer demo flow asks "which traditions?"
```

ψ.8.0 ships in isolation (no UI yet — runs once, commits the corpus
re-tag). ψ.8.1 + ψ.8.2 + ψ.8.3 ship as one batch (schema is meaningless
without build-pipeline output and a UI to set it). ψ.8.4 and ψ.8.5
follow as separate phases.

## v1.0 inclusion

ψ.8 is **promoted to the v1.0 terminus**, replacing the prior
"θ.2 + χ.1 + corpus ≥ 25K" definition with:

```
v1.0 = θ.2 + χ.1 + ψ.8 + corpus ≥ 25K notes
```

Without ψ.8 the platform is "yet another edition factory". With it,
the platform is "the only Bible publishing platform with cross-
denominational apparatus". That's the v1.0 differentiator.

## Tradeoffs / known limitations

- **Authoring debt.** The 5 sample-seeded editions today don't all have
  notes in their canonically-mapped tradition. Filling them out is a
  separate corpus-growth effort (likely χ.2-χ.5 commentary ingestors,
  which already exist as planned phases). ψ.8 ships even with sparse
  per-tradition coverage; popups simply omit empty traditions.
- **No auto-translation across traditions.** A Catholic Haydock note
  isn't auto-translated into a Protestant equivalent. The popup shows
  what's there, sourced from each tradition's PD apparatus.
- **Popup density risk.** With 5 traditions active, popups can run
  long even with collapse. Mitigated by (a) per-edition filtering, (b)
  default-collapsed state, (c) first-80-char preview.
- **Pedagogical neutrality is a stance, not absence of stance.** The
  platform doesn't editorialize *which* tradition is correct; it lets
  the reader see them side-by-side. Some buyers may prefer a single-
  tradition product without compare; that's the per-edition opt-in.
