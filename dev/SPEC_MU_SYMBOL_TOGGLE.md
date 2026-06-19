# SPEC — Phase μ: Symbol Toggle Dev Tool

**Status:** Draft, awaiting decisions on open questions
**Author:** Claude + the project owner
**Last updated:** 2026-05-07
**Implements:** the original "biggest idea" of the project — turn the
14 categories × 63 kinds matrix into a clickable, demo-able artifact
rather than a YAML hand-edit experience.

---

## 1. Problem statement

The platform supports per-edition filtering on the symbol/kind axis, but
the only way to use that capability today is by hand-editing
`content/editions.yaml`. There is:

- no visualization of the 14 × 63 matrix
- no live count of "what would I lose / keep if I toggled this"
- no way for a non-technical stakeholder (publisher, editorial lead,
  product manager) to explore differentiation
- no way to save / name / compare scenarios
- no preview of the rendered effect
- no way to customize the actual glyph for a partner who prefers
  different symbols

This is the biggest unrealized idea in the project. The entire data
model — categories.yaml, kinds.yaml, editions.yaml, the build-time
filter — exists to support this kind of tool. It just hasn't been
built yet.

---

## 2. Audience & use cases

### Primary

- **Editorial leads** building or revising an edition profile.
  *"I want to see what a Latter-day Saint study Bible would look like —
  let me toggle on `dist-typological` + `compare-pseudepigrapha` and
  see what the count and category mix becomes."*

- **Publishing partners** evaluating fit during contract negotiation.
  *"Show me a 6,500-note Catholic edition with no rabbinic commentary
  and Marian devotional notes foregrounded."*

- **Product managers at Bible-app companies** curating per-cohort
  experiences.
  *"For seminary students, enable `lang-greek` + `text-dss` +
  `comm-modern-critical`; disable `dev-prayer`."*

### Secondary

- **Internal QA** spotting taxonomy drift (a kind has 0 notes, or 95%
  of notes in one category).

- **Marketing copy generation** — export "this edition includes …"
  for retail listings.

---

## 3. User stories

### Must-have (μ.1)

- **U1.** As an editorial lead, I open the tool and see all 14
  categories × 63 kinds laid out, with the symbol for each, with
  current edition's enabled state shown.

- **U2.** I click a category to toggle the entire family on/off.
  The note count for the active edition updates immediately.

- **U3.** I click a kind to toggle just that one. Counts update.

- **U4.** I switch the active edition (catholic-study,
  evangelical-reformed, …) from a dropdown. The toggles reflect that
  edition's current settings.

- **U5.** I save my changes. The tool updates editions.yaml in place
  (with a backup) — same workflow build_edition.py already expects.

### Should-have (μ.2)

- **U6.** I create a new edition profile from scratch. I name it,
  pick a base canon, set toggles, and save it as a new entry in
  editions.yaml.

- **U7.** I see a sample of 5 notes for any kind, to understand
  what I'm including/excluding.

- **U8.** I view two editions side-by-side as a diff:
  *which kinds are enabled in A but not B, and the note delta.*

- **U9.** I see per-category bar visualizations: how many notes
  fall into each category for the active edition.

### Stretch (μ.3)

- **U10.** I customize a category's symbol. Change ⌘ to ✎. The
  change writes to categories.yaml; subsequent builds use the new
  glyph.

- **U11.** I tune per-kind word budgets directly in the tool.

- **U12.** I see live HTML preview of one canonical verse rendering
  with the current toggle state.

- **U13.** I export a PDF report: "What's in this edition" — for
  marketing copy or investor decks.

---

## 4. Goals & non-goals

### Goals

- Make the matrix visible, tangible, and clickable
- Reduce the "edit YAML and rebuild" loop to a single click + save
- Demo well to non-technical stakeholders
- Live counts (no rebuild needed to see "how many notes")
- Persist named scenarios

### Non-goals

- Replace the build pipeline. The tool emits config; build_edition.py
  still does the work.
- Full WYSIWYG note editing. We have web.py for that.
- Multi-user collaboration. Single-author, local-first.
- Real-time sync to a remote server. Local files only.

---

## 5. UI shape (μ.1 baseline mockup)

```
┌─────────────────────────────────────────────────────────────────┐
│ E-Bible · Symbol Toggle Studio              edition: catholic ▾ │
│                                                                 │
│ ┌─────────────────────────────────────────┐  ┌───────────────┐ │
│ │ MATRIX                                  │  │ ACTIVE PROFILE│ │
│ │                                         │  │ catholic-study│ │
│ │ ⌘ Linguistic           [11 kinds] ●●●○○ │  │ canon: catholic│ │
│ │   ☑ word                              │  │ books: 76     │ │
│ │   ☑ lang-hebrew                       │  │ enabled       │ │
│ │   ☑ lang-greek                        │  │   kinds: 46   │ │
│ │   ☐ lang-aramaic                      │  │ notes: 1,124  │ │
│ │   …                                   │  │   would lose  │ │
│ │                                         │  │   if you      │ │
│ │ ✧ Textual / Critical    [6 kinds] ●●●●○│  │   saved: 247 │ │
│ │   ☑ source                            │  │               │ │
│ │   …                                   │  │ [Save] [Reset]│ │
│ │                                         │  └───────────────┘ │
│ │ ‖ Cross-references     [4 kinds] ●●●●○ │                     │
│ │   …                                   │  ┌───────────────┐ │
│ │                                         │  │ DIFF FROM ↓  │ │
│ │ ⌂ Historical / Cultural [7 kinds] ●●●●●│  │ ↑ as saved   │ │
│ │   ☑ hist-ane                          │  │ + lang-amharic│ │
│ │   ☑ hist-greco-roman                  │  │ - dev-prayer  │ │
│ │   …                                   │  │               │ │
│ │                                         │  └───────────────┘ │
│ │ … (more categories collapsed)           │                     │
│ │                                         │                     │
│ └─────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘

Click row symbol     → expand/collapse the kind list under it
Click checkbox       → toggle a single kind
Click category title → toggle all kinds in family
Each row's filled dots = % of kinds enabled (visual scan)
Active edition dropdown switches base; toggles update accordingly
```

### Color coding

- **Green check** — kind enabled in the active edition
- **Gray box** — kind disabled
- **Yellow asterisk** — kind has unsaved changes vs disk
- **Red exclamation** — would result in 0 notes for this edition

---

## 6. Data model

### Existing inputs (no schema changes)

```yaml
content/categories.yaml    14 categories × {id, label, symbol, sort_order}
content/kinds.yaml         63 kinds × {code, category, label, ...}
content/editions.yaml      5 editions × {id, canon, enabled_categories,
                                          enabled_kinds, disabled_kinds, …}
content/canons.yaml        5 canons × books
content/notes/*.py         1,371 notes (will grow to 25-30k)
```

### New persisted artifacts

```yaml
content/scenarios/*.yaml   user-saved hypothetical edition profiles
                            (μ.2+)
                            same shape as editions.yaml entry; lets you
                            iterate without polluting the real edition list
```

### Computed at runtime

- For each (edition, kind) cell: total notes attributed to that kind
  in the books that are in the edition's canon.
- Matrix is computed once at tool startup and cached; recomputed when
  notes/ changes.

---

## 7. Architecture options

### Option A — extend scripts/web.py with a new view (RECOMMENDED for μ.1)

```
GET /matrix              → matrix HTML page
GET /api/matrix/counts   → JSON: {kind_code: {edition_id: count}}
POST /api/edition/save   → atomic_write to editions.yaml + backup
GET /api/notes-sample    → 5 sample notes for a (kind, edition) cell
```

**Pros:** zero new dependencies; same stdlib HTTP server; ships with
existing tooling; uses already-cached config loaders.
**Cons:** vanilla JS for the UI; matrix rendering may need pagination
at full corpus scale.

### Option B — new standalone Tauri/Electron app

**Pros:** more polished; truly publisher-facing artifact;
desktop-quality interactions.
**Cons:** new tech stack; build complexity; we'd be maintaining a
second app.

### Option C — Streamlit/Gradio Python notebook UI

**Pros:** very fast to prototype; clean Python all the way down.
**Cons:** adds a heavy dependency; not as polished as bespoke HTML;
single-page only, harder to grow.

**Recommendation:** start with **Option A**. Promote to B only if a
real publishing partner needs a polished standalone artifact.

---

## 8. Implementation phases

### μ.1 — Matrix view + per-edition toggle (must-have)

```
+ scripts/web.py             new /matrix route + JSON APIs
+ scripts/core/matrix.py     compute (kind, edition) → note count grid
+ static/matrix.html         the UI
+ static/matrix.css          minimal styling
+ static/matrix.js           toggles + save flow
+ tests/test_matrix.py       count-grid logic
```

**Effort:** ~6-8 hours of focused work.
**Output:** a working tool that meets U1-U5.

### μ.2 — Profile management + diff (should-have)

```
+ /api/scenarios CRUD        for content/scenarios/*.yaml
+ side-by-side diff view      U8
+ note sample drawer          U7
+ bar visualizations          U9
```

**Effort:** ~4-5 hours.
**Output:** U6-U9.

### μ.3 — Customization stretch (nice-to-have)

```
+ inline symbol customization U10
+ per-kind word-budget slider U11
+ live verse preview          U12
+ PDF export                  U13
```

**Effort:** ~6-8 hours; some sub-tasks (U13) can be skipped if the
demand isn't there.

---

## 9. Risks & considerations

- **Performance at full corpus.** At 25-30k notes the count grid is
  87 × 63 ≈ 5,500 cells. Each cell needs a count. Done naively that's
  one scan per cell. Done correctly: one scan, accumulate into grid.
  Should be < 1 second.

- **Concurrent edits.** Single-user, local-only — but the tool may
  edit editions.yaml while build_edition.py is reading it. Use
  notes_io.atomic_write + ensure_backup (which we already have).

- **Naming collisions.** A user creates "scenario-1.yaml" then forgets
  about it. Need a clear "list / load / delete" UI.

- **Symbol changes are global.** Touching categories.yaml affects every
  edition's symbol. Need a confirmation dialog with "this changes ⌘
  to ✎ in all 5 editions; OK?"

- **Bias toward 'all on'.** Users may default to enabling everything
  without considering retail differentiation. The tool should display
  a "your edition has X kinds; the average commercial Bible study
  edition has Y" hint.

---

## 10. Open questions for user input

```
Q1  Build μ.1 first (matrix view + toggles + save), or do you want
    a clickable demo of the UI shape (HTML mockup, no real backend)
    before we commit to the full implementation?

Q2  For μ.2 scenarios — store them in content/scenarios/*.yaml as
    proposed, or keep them out of git as user-local drafts in a
    .scenarios/ dir?

Q3  Symbol customization (μ.3, U10) — is this ever a real publisher
    request, or is the symbol set already locked? If locked, drop U10
    from scope.

Q4  Do publishing partners need to RUN this tool themselves, or
    will an editorial lead always operate it on their behalf? This
    drives whether we polish a standalone artifact or keep it as
    an internal tool.

Q5  Should the tool also surface and let users tune per-kind WORD
    BUDGETS (note_quality.py thresholds), or is that a separate
    concern?

Q6  At what corpus size do we need pagination / lazy loading?
    1,371 notes is fine. 25,000 may need to load counts incrementally
    rather than all-at-once.
```

---

## 11. Acceptance criteria for μ.1 (definition of done)

- `python3 scripts/web.py` (or a new `python3 scripts/symbol_studio.py`)
  starts a server, prints a URL, and the matrix renders in the
  browser.
- All 14 categories visible with their symbols.
- Expanding a category shows its kinds.
- Switching the edition dropdown updates checkbox state for all kinds.
- Clicking a checkbox updates the live note count for the active
  edition (no full rebuild needed — counts come from the cached
  matrix).
- Save button writes to editions.yaml using atomic_write +
  ensure_backup, and the change persists across server restarts.
- Build pipeline reads the new state correctly (verifiable by
  running `ebible build` after a save).
- Tests cover: count grid correctness, toggle persistence, atomic
  write under concurrent read.

---

*End of spec. Open questions Q1-Q6 are blocking; everything else
falls out from those decisions.*
