# Scope addendum — Per-book popup-language toggle (Phase ν.2.7)

**Added:** 2026-05-07, after ν.2.5-B shipped.
**Origin:** direct user request — "I want the developer/publisher to be
able to have an off/on button for all languages at the same time or any
variation of them show up in the popup based on what they want. Not
individually per verse marker but per book."

## What this phase does

Today every vnote popup shows three languages stacked together —
English, Hebrew (Masoretic), and Greek (Septuagint). The publisher
has no control over which appear. This phase adds:

  1. A **per-edition default** language set
  2. **Per-book overrides** for any books that need different languages
  3. The build pipeline strips language paragraphs from the popup
     asides based on the resolved configuration

The granularity is **per book** (not per verse marker, which would be
unmanageable; not only per edition, which is too coarse for canonical
needs like "no Greek for OT-only Tanakh editions"). 80-ish books per
canon × N languages = a tight matrix UI.

## Three states the publisher can choose

```
1. No popups at all              verse_popups: false   (Phase ν.2.5-A)
                                 → vn-links not clickable; reader sees
                                   verse numbers as inert text

2. Popups with all languages     verse_popups: true
                                 popup_languages_default: unset OR
                                   = [english, hebrew, greek]
                                 → unchanged from current behavior

3. Popups with chosen languages  verse_popups: true
                                 popup_languages_default: [english]
                                 popup_languages_per_book:
                                   dan: [english, aramaic]
                                   mat: [english, greek]
                                 → each book's popup contains exactly
                                   the languages listed; unlisted
                                   books inherit the default
```

State 2 is the default-default — every existing edition continues to
ship byte-identical popups unless the publisher opts in.

## Languages in scope

### Phase ν.2.7 — supported now (data already in source HTML)

| id        | full label                       | CSS class      |
|-----------|----------------------------------|----------------|
| english   | English (translation choice)     | vnote-text     |
| hebrew    | Hebrew (Masoretic / WLC)         | vnote-hebrew   |
| greek     | Greek (Septuagint / Brenton)     | vnote-greek    |

`english` is special — it's the slot controlled by the existing
`popup_translation` field (WEB by default, swappable to KJV via τ.1.5
+ ν.2.5-B). Toggling `english` off removes that paragraph entirely.

### Future languages (architected for, no source data yet)

| id        | full label                       | source needed                     | priority |
|-----------|----------------------------------|-----------------------------------|----------|
| aramaic   | Aramaic (Targum / portions)      | Targum Onkelos for OT;            | high     |
|           |                                  | original Aramaic in Dan 2:4-7:28, |          |
|           |                                  | Ezra 4:8-6:18                     |          |
| geez      | Ge'ez (Ethiopian Tewahedo)       | digitized Ge'ez Bible — flagship  | high     |
|           |                                  | edition's native language         |          |
| latin     | Latin (Vulgate)                  | Clementine Vulgate (PD)           | medium   |
| coptic    | Coptic (Sahidic)                 | Sahidic NT — relevant for Coptic  | low      |
|           |                                  | + Ethiopian editions              |          |
| syriac    | Syriac (Peshitta)                | Peshitta — relevant for Eastern   | low      |

The schema accepts any of these strings today; the build silently
ignores ones it can't render (no CSS class match → no paragraph to
strip), so adding a language later is purely additive: drop in source
text under the matching CSS class, register the id, done.

## Schema additions to editions.yaml

```yaml
- id: catholic-study
  ...existing fields...

  # Phase ν.2.7 — per-book popup-language control.
  # The build pipeline resolves languages for each book as:
  #   per_book.get(book_code, default)
  # If neither key is set, all languages are shown (back-compat).
  popup_languages_default:
    - english
    - hebrew
    - greek
  popup_languages_per_book:
    # Optional. Books not listed inherit popup_languages_default.
    # Example: drop Greek from a Tanakh-style edition's NT popups
    # mat: [english, hebrew]
    # ...
```

Defaults shipped in the populated test data (one sensible
configuration per edition, see "Populated test data" below).

## Resolution order at build time

```
For each <aside class="vnote" id="vnote-{book}-{ch}-{vs}">:
    languages = edition.popup_languages_per_book.get(book)
    if languages is None:
        languages = edition.popup_languages_default
    if languages is None:
        languages = ALL_LANGUAGES   # back-compat
    For each language in (ALL_LANGUAGES - languages):
        strip the matching <p class="vnote-source-label"> + content
        paragraph from this aside
    If 'english' was kept AND popup_translation is set:
        run the existing ν.2.5-B swap
```

This is `_replace_verse_popup_translation`'s natural extension — same
pass over each aside, same regex anchor, same byte-identical default
when the new fields are unset.

## Sequencing

```
ν.2.7-A   Schema + populated test data + backend filter           NEXT
          ~ Pure data + build-pipeline change. No UI yet.
          ~ Risk: LOW   Effort: 1 turn

ν.2.7-B   Per-book language picker UI in /customize               AFTER
          ~ Tight matrix view: rows = books in canon, cols = langs
          ~ "Apply default to all" + "All on" / "All off" presets
          ~ Risk: LOW   Effort: 1-2 turns
```

After ν.2.7-B ships, the buyer-demo flow extends:

```
1. /wizard → pick canon, kinds, theme, translation, popup languages
2. (One new card: per-book language matrix, with smart defaults
   pre-populated based on canon — e.g. "Tanakh editions don't show
   Greek by default because no NT")
3. BUILD → EPUB ships with exactly those languages in popups
```

## Populated test data (initial values)

To make this immediately testable without UI work, ν.2.7-A populates
sensible defaults on each shipping edition:

| edition              | popup_languages_default              | rationale                    |
|----------------------|--------------------------------------|------------------------------|
| ethiopian-tewahedo   | [english, hebrew, greek]             | flagship; show all three     |
| catholic-study       | [english, hebrew, greek]             | scholarly; show all          |
| evangelical-reformed | [english, greek]                     | Reformed prefers NT-Greek;   |
|                      |                                      | Hebrew via word notes only   |
| jewish-study         | [english, hebrew]                    | Tanakh-only; LXX irrelevant  |
| scholarly-academic   | [english, hebrew, greek]             | full apparatus               |

`popup_languages_per_book` is left empty (`{}`) on every edition so
publishers see only the per-edition default in effect — they can add
per-book overrides via the UI in ν.2.7-B.

## Where this fits in the master plan

Inserted after ν.2.5-B (which just shipped) and before any deferred
items. Updated in `dev/PLAN_2026-05-07.md` (master sequence doc).
