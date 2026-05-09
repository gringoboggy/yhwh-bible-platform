# Scope addendum — ψ.7 edition templates + new built-in editions

**Date:** 2026-05-09. Companion to `dev/PLAN_2026-05-09.md` §5.1
(the SHORT TRACK ψ.7-A / ψ.7-B sub-phases).

**Phases covered:**

  - **ψ.7-A** four new built-in editions
  - **ψ.7-B** edition template starter packs (folder + API + wizard)
  - **ψ.7-C** (speculative, post-v1.x) edition template marketplace

This addendum captures the user's 2026-05-09 ask to "add more
editions" — both as fully-shipped built-ins (the dropdown grows
from 5 → 9 traditions) and as starter-pack templates buyers clone
on demand from the wizard.

---

## 1. ψ.7-A — four new built-in editions

### 1.1 What ships

Four `editions:` entries appended to `content/editions.yaml`. The
existing 5 stay unchanged.

| New id | Canon used | Distinctive lens | Sub-kinds foregrounded |
|---|---|---|---|
| `eastern-orthodox` | `orthodox` (78b — already defined; currently unused) | LXX-leaning OT; Patristic / Byzantine commentary; foregrounds liturgy-byzantine | comm-orthodox, liturgy-byzantine, comm-patristic |
| `anglican-bcp` | `catholic` (76b; Apocrypha as deuterocanonical) | BCP-style apparatus; lectionary integration | comm-anglican, liturgy-bcp, comm-patristic |
| `lutheran-confessional` | `protestant` (66b) | Reformation-era commentary; Apocrypha as separate section | comm-reformation, comm-lutheran, comm-confessional |
| `coptic-orthodox` | `ethiopian` (87b — Coptic shares ~78 with Tewahedo) | Coptic patristic + ascetic-monastic emphasis | comm-coptic, liturgy-coptic, comm-patristic |

### 1.2 Schema strategy

Per CLAUDE_PROJECT_RULES §9 "Add a new edition feature": schema
additive, defaults preserve back-compat, build pipeline is a no-op
on the new fields when unset. Each new edition adds ~30 YAML lines.
No Python changes — the loader iterates editions generically.

Required fields per new edition (template):

```yaml
  - id: <id>
    canon: <canon-id>
    title: "..."
    short_title: "..."
    isbn: "978-XXX-XXXXX-XX-X"   # placeholder; real ISBNs are buyer-side
    target_audience: "..."
    enabled_categories:
      - lang
      - text
      - xref
      - hist
      - lit
      - comm
      - compare
      - liturgy
    enabled_kinds:
      - <foregrounded comm-* / liturgy-* sub-kinds>
    disabled_kinds:
      - <kinds that conflict with this tradition's posture>
    max_phase: mvp
    cover_image: "covers/<id>.jpg"
    notes: "1-2 sentence editorial justification"
    popup_languages_default:
      - "english"
      - <tradition-relevant language>
    popup_translation: ""
```

### 1.3 Per-edition kind tuning

| Edition | enabled_kinds notable adds | disabled_kinds notable subs |
|---|---|---|
| `eastern-orthodox` | comm-orthodox, liturgy-byzantine, comm-patristic, comm-cappadocian | comm-reformation (rejects sola-scriptura framing), dist-mariological (handled differently than Catholic), comm-evangelical |
| `anglican-bcp` | comm-anglican, liturgy-bcp, comm-patristic, comm-evangelical (broad-church) | dist-mariological (BCP is non-Marian), comm-tridentine |
| `lutheran-confessional` | comm-reformation, comm-lutheran, comm-confessional | dist-mariological, comm-orthodox (different posture on tradition), comm-tridentine |
| `coptic-orthodox` | comm-coptic, liturgy-coptic, comm-patristic, comm-monastic | comm-reformation, comm-evangelical (non-Eastern hermeneutic) |

**These are starting points, not commitments** — publishers tune
per their imprint.

### 1.4 Build pipeline impact

Zero. The build pipeline:

  1. Loads editions.yaml
  2. For each edition: filter notes by canon ∩ enabled_kinds
  3. Render

Adding 4 entries means 4 more iterations on `python scripts/build_all_editions.py`
(api_build_all). The existing `total_per_edition` map in
api_corpus_progress / api_attribution_audit absorbs them.

### 1.5 Tests

  - **Each new edition loads:** `config.load_editions()` returns 9
    entries with canonical id ordering preserved.
  - **Canon ref valid:** each `canon` field maps to an entry in
    `content/canons.yaml`.
  - **Filter yields >0 notes:** matrix shows non-zero `total_potential`
    for each new edition.
  - **build_one() succeeds:** smoke build produces a non-empty
    EPUB for each new edition (mocked via the §9 injectable-callable
    pattern; no real EPUB output in tests).
  - **Round-trip via api_save_edition_meta:** publisher-editable
    fields (title / short_title / isbn / cover_image / notes /
    popup_languages_default) edit + reload cleanly.

### 1.6 Rollback

Pure data addition; if any edition causes a build issue, comment
out the YAML block and the existing 5 are untouched.

---

## 2. ψ.7-B — edition template starter packs

### 2.1 What ships

  - **`content/edition_templates/`** — new folder of 5-7 partial
    YAML records. Each is a partial `editions.yaml`-style block with:
      - `template_id` (instead of `id`)
      - `template_label` (shown in the wizard picker)
      - `template_description` (shown as wizard hover text)
      - all the usual edition fields (canon / enabled_categories /
        etc.) as the default starting state
  - **`api_edition_templates_list()`** — pure function returning
    `[{template_id, label, description, canon, ...}, ...]`
  - **`api_create_edition_from_template(template_id, new_id, new_title)`**
    — clones the template into a fresh `editions.yaml` entry with
    user-supplied id/title overrides; runs ν.4 clone validation
  - **Wizard step 1 — "Start from template…" button** — opens a
    modal listing the templates; click → fills the form with the
    template's defaults; user proceeds through the existing wizard
    flow with editing freedom

### 2.2 Templates to ship

| Template | Description | Canon | Audience |
|---|---|---|---|
| `monastic-daily-office` | Daily office reading order; low-density apparatus; brevity-focused | catholic | Religious orders, oblates |
| `school-friendly-nrsv` | Large fonts, simple kinds, no Hebrew/Greek popups, simplified comm-* | protestant | Schools, students K-12 |
| `children` | Large fonts, illustrations slot, simplified commentary, family-rhythm chapters | protestant | Family / Sunday school |
| `family-devotional` | Q&A-style apparatus, mid-density, family-reading rhythm | protestant or catholic | Lay families |
| `scholarly-academic-with-apparatus` | Mirrors the existing built-in for clone-and-tweak (rename ISBN, retitle, ship as own SKU) | ethiopian | Academic publishers |
| `anglican-bcp` (mirror) | Same content as the ψ.7-A built-in but as a clonable template | catholic | Anglican publishers wanting a tweak baseline |
| `lutheran-confessional` (mirror) | Same content as the ψ.7-A built-in | protestant | Lutheran publishers |

The mirror templates (`anglican-bcp`, `lutheran-confessional`) let
publishers who want a 95%-match-with-1-tweak start from a known
configuration rather than scratch.

### 2.3 Template YAML format

```yaml
template_id: monastic-daily-office
template_label: "Monastic daily office"
template_description: >
  Daily office reading order. Brevity-focused apparatus suitable
  for religious orders, oblates, and lay use of the canonical hours.
  Apocrypha included; commentary leans ascetic / contemplative.

# Below: same as an editions.yaml entry, used as defaults
canon: catholic
title: "Monastic Daily Office Bible"     # placeholder; user edits
short_title: "MDO Bible"                  # placeholder; user edits
isbn: "978-0-000000-00-0"                 # placeholder; user supplies
target_audience: "Religious orders, oblates, lay practitioners of the canonical hours"
enabled_categories:
  - lang
  - text
  - xref
  - hist
  - lit
  - comm
  - compare
  - liturgy
enabled_kinds:
  - comm-monastic
  - comm-patristic
  - liturgy-bcp
disabled_kinds:
  - comm-evangelical
  - comm-reformation
max_phase: mvp
cover_image: ""
notes: "Compact daily-office layout. Defer non-essential apparatus."
popup_languages_default:
  - "english"
  - "latin"
popup_translation: ""
```

### 2.4 API contracts

```python
def api_edition_templates_list() -> dict:
    """Return [{template_id, label, description, canon, summary}, ...]
    sorted by template_id alphabetically. Read-only; safe to cache."""

def api_create_edition_from_template(
    template_id: str,
    new_id: str,
    new_title: str,
) -> dict:
    """Clone the template into editions.yaml with user-supplied
    id/title overrides. Runs ν.4 validation (id is unique, canon
    exists, kinds resolve). Returns {"status": "ok", "edition_id": new_id}
    or {"status": "error", "code": "...", "http": 4xx, "message": "..."}.

    On success, the new edition appears in /customize, /publisher,
    /matrix immediately (no restart)."""
```

### 2.5 Wizard integration

Step 1 currently asks: canon / kinds / theme. After ψ.7-B:

  1. **At the top of step 1**, add a "Start from template…" button
     above the canon picker.
  2. **Clicking opens a modal** listing the 5-7 templates with
     label + description + canon badge.
  3. **Selecting a template** populates the canon picker + kind
     toggles + theme defaults from the template's YAML.
  4. **User proceeds through the wizard** with full editing
     freedom — the template was just a starting state.
  5. **Wizard's existing "Save edition" calls
     api_create_edition_from_template** instead of the manual
     api_save_edition_meta path; the existing path remains for
     "Start from scratch" users.

### 2.6 Tests

  - **Each template parses:** every file in `content/edition_templates/`
    loads cleanly; every required field present.
  - **Templates can be applied:** smoke test that creates a fresh
    edition from each template; created edition passes ν.4
    validation.
  - **API list is sorted + read-only:** ordering pinned;
    GET-style endpoint never mutates.
  - **API create rejects duplicates:** trying to clone with an
    existing `new_id` returns 409 with a clear message.
  - **API create rejects invalid:** unknown template_id → 404;
    missing fields → 400.
  - **Wizard button renders + opens modal:** template HTML smoke
    test for the new button + modal markup.
  - **Wizard modal lists every template:** for each template_id in
    `content/edition_templates/`, the modal contains a row.

---

## 3. ψ.7-C — edition template marketplace (speculative, deferred)

Post-v1.x. Out of scope for ψ.7-A/B. Captured here for completeness:

  - Let users export their custom edition as a template YAML
  - Re-import / share via GitHub gist / file upload / URL fetch
  - Could become a community "edition gallery"

Defer scoping until ψ.7-A + ψ.7-B prove the format. The existing
ν.4 clone + validation machinery is already nearly all of what
this needs; the missing piece is import + signature verification
(could ride on the same Sparkle-style appcast infrastructure ψ.7-C's
spec would borrow from θ.3 if it ever lands).

---

## 4. Working agreements

  - ψ.7-A ships first, ψ.7-B second. Per the §3 sequencing rule,
    ψ.7-B depends on having concrete editions to mirror as templates.
  - Both phases land as ONE save tag if shipped same session, or
    separate tags if split.
  - The existing 5 editions are untouched. ψ.7-A is purely
    additive. ψ.7-B adds new files + API + UI; existing flows
    unchanged.
  - Visual review on user (per project rules on UI changes): walk
    /customize / /publisher / /wizard with each new edition
    selected; sign off or file specific tweaks.
