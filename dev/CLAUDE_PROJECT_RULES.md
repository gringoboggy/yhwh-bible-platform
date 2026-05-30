# Claude project rules — the Bible publishing platform

**Purpose:** the durable, in-repo reference for how any Claude (or returning user)
should think about working on this project. Memory comes and goes; this doc is the
source of truth. If anything here conflicts with a one-off user instruction, the
user wins for that turn — but the rule stays as written.

**Finished-arc history, frozen stats, and per-instance tallies extracted from this
file live in `dev/archive/RULES_HISTORY.md`** — pointers below name what moved.

**Operational guards (durable behavioral defaults — keep all three):**
1. **Package installs under auto-mode** — before installing ANY package NOT already
   in a committed manifest (`requirements*.txt`, `pyproject.toml`, `package.json`),
   ask the user to turn auto-mode OFF first, then install once they confirm
   (auto-mode soft-denies undeclared installs as a supply-chain risk). No pause if
   the package is already declared or the user asked for it. Durable fix: DECLARE
   build/tool deps in a manifest.
2. **Sources are NOT missing** — never conclude corpus/ingest/translation/popup
   work is "blocked on missing sources" or ask the user to supply one. Look first,
   in order: the plans (`dev/archive/PLAN_2026-05-21.md` §4.1 +
   `dev/AUDIT_2026-05-23-DEEP.md`); then `content/sources/`,
   `content/translations/sources/`, `_acquire/` (one level above the repo,
   gitignored), the top-level PDFs (arbitrary filenames — don't grep by book), the
   `GAPS/` Geʽez folder, the web sources the plans name; then verify current status
   against `dev/CHANGELOG.md`. The only legitimate source ask is a genuine
   licensing/credential gate. (Memory: `sources-already-in-place`.)
3. **Re-Read the big truth-record MDs right before editing them** —
   `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/CHANGELOG.md` truncate on Read,
   and a truncated read does NOT satisfy the Edit "must read first" gate. Do a fresh
   small-region `Read` of the exact lines you're about to change (e.g.
   `Read(path, limit=6)` for a top-of-file prepend; a small window for a mid-file
   edit) immediately before each Edit. (Memory: `reread-before-editing-big-md`; RULES §0.)

## Rules map — which § governs what (jump here first)

| § | Governs |
|---|---|
| **0** | Bootstrap protocol — read-order triad + the always-there maps (MATRIX_MAP, REPO_MAP) + the post-triad env-health & RAM-clear step. |
| **1** | North star — the builder demo; corpus depth; patristic-voice invariant; the two standalone parallel Bibles; the self-upgrading matrix. |
| **2** | Universal principles. |
| **3** | Sequencing rules (how to order work). |
| **4** | Save semantics — "save" = local commit; checkpoint saves; "continue" ≠ "save". |
| **5** | Phase / commit tracking. |
| **6** | UI conventions — canonical book/chapter order, cross-linking, styling, reactivity, additive-feature defaults. |
| **7** | Code conventions — backend, schema migrations, project structure, one-shot ship scripts. |
| **8** | Testing conventions — arc-close pin convention. |
| **9** | **Mental models** — step-by-step recipes: edition feature / translation / popup language / per-book asset / uploadable binary / static route / meta-tool / aggregate API / feature endpoint / corpus-growth (χ-cluster) / register note kind / four-tier defensive system / style knob / god-module extraction / Δ-family index-backed op. |
| **10** | What this project is NOT (scope guardrails). |
| **11** | Continuity protocol — keep `SESSION_STATE.md` current. |
| **12** | Retrospective protocol — keep `CHANGELOG.md` + the rules current. |
| **13** | Topic-shift protocol — audit before pivoting. |
| **14** | Session-resume / state-uncertainty audit. |
| **15** | **Chain of command** — the tier hierarchy (user > rules > skills > defaults) as a matrix. |

Companion maps: `dev/MATRIX_MAP.md` (data-flow + base-HTML), `dev/REPO_MAP.md`
(file/folder index), `dev/PLAN_2026-05-29-roadmap.md` (roadmap), `dev/CHANGELOG.md`
(shipped chronology). **Lifecycle companion: `dev/SESSION_PLAYBOOK.md`** — the
order-of-operations guide (session start → work → verify → finish-clean) with the
consolidated verification gates + the environment/gotcha list in one place; read it
for the session-end checklist or exact gate commands. This RULES file remains the
topic-organized authority on each rule.

---

## 0. Bootstrap protocol — read these three files first

Every fresh session begins by reading, in this order:

```
1. dev/CLAUDE_PROJECT_RULES.md       (this file — rules + conventions)
2. dev/SESSION_STATE.md              (live snapshot — what shipped, what's next, test count)
3. dev/PLAN_2026-05-29-roadmap.md    (master forward sequence; PLAN_2026-05-21
                                      retained in dev/archive/ for Track B/C detail
                                      + phase-history)
```

**"continue" / "push" / "go ahead" at the start of a fresh session DOES NOT bypass
this read-order** — those words mean *read the triad first, THEN resume the in-flight
work*, never *skip to the task*. The triad (~700-900 lines) IS the minimum
orientation; a `git log` or SESSION_STATE-only peek is NOT a substitute. A project
**SessionStart hook** (`.claude/hooks/bootstrap-triad.ps1`, wired in
`.claude/settings.json` at the repo-parent cwd) injects this reminder at every
session start as a forcing function.

**Always-there maps:** for ANY "where does X live / how does data flow / what feeds
the build" question, check the maps FIRST — never grep blind. `dev/MATRIX_MAP.md`
traces the DATA-FLOW (config → loaders → matrix/build/inject → consumers + the
base-HTML structure & coverage) and names the exact module; `dev/REPO_MAP.md` is the
FILE/FOLDER index. Companions re-verify them (`dev/trace_matrix.py`,
`dev/trace_repo.py`); the pre-commit `lint_rules.py` enforces both
(`plan_coherence`, `repo_map_complete`).

**Post-triad env-health + RAM-clear step (after the triad, before in-flight work):**
do a quick environment pass and an aggressive RAM clear — **see `dev/SESSION_PLAYBOOK.md`
§1 for the full enumeration** (the env-health checks: Claude Code / plugin updates
apply only on user OK + `/reload-plugins` after a plugin update; MCP/tools are
tokenless local-only, a failed server = missing local runtime never a login gate; and
the RAM-clear PROTECT-list / KILL-list / report procedure on this 16 GB box). Never
silently mutate the environment; never re-add a login-required plugin to make a check
pass. Fold the result into the one-line post-triad confirmation: *phase · what's next
· env OK · RAM freed*. (Memory: `session-hygiene`; concurrency interplay:
`feedback-concurrent-agent-cap`; the session-END junk sweep is the counterpart —
PLAYBOOK §6.5.)

Optionally, only when the user's ask implies them: `dev/CHANGELOG.md` (chronology);
`dev/SCOPE_*-addendum-*.md` (feature spec); `HANDOFF_README_v7.md` (deep
architecture, large); `scripts/README.md` (tool reference); the relevant
`content/notes/<book>.py` / `content/candidates/<…>.json` for note-level work.

After the triad Claude is fully oriented. **Never dump status to the user** —
confirm in one line ("Read state, current at φ.1, next is π.4-B — proceeding") and
proceed to the actual request.

---

## 1. The north star

**The builder demo.** The project is a free public app (no for-sale publishing
surface). End-to-end:

```
1. Open /wizard
2. "Make a Catholic study Bible" (or pick another starting edition)
3. Step through 7 cards: start-from, branding, theme, content (canon + kinds),
   traditions, review, build
4. Click BUILD → an EPUB downloads with the chosen theme, only the picked notes,
   and verse popups in the configured languages. EPUB dc:identifier is a generator
   URN (urn:yhwh:edition:<id>:<build-hash>) — a generator id, not a commercial book identifier; the build is not for resale.
5. Builder says "wow, that's mine" — yes, that's it.
```

A companion `/build-tracker` console shows the builder exactly what is enabled in
their current edition (per book × chapter note counts, per-kind breakdown, canon
coverage) so build choices are visible before BUILD is clicked.

### Corpus depth target

The Ethiopian Tewahedo edition is the **superset** that all other editions filter
from. Original target corpus size was 35,000–40,000 notes — long since exceeded with
large headroom. **Live count: see `dev/SESSION_STATE.md`** (do NOT hard-code a figure
here — it rots). Drawn from public-domain sources via the `prospect → promote`
pipeline and reference-corpus ingestion (`dev/MATRIX_MAP.md` → "Reference-corpus
ingestion"). Other editions are subsets; their note counts fall out automatically
from canon + kind filtering. Continued growth (reference works, χ-AI-xrefs, γ-cluster
expansion) is **opportunistic, not blocking** — the depth claim against every
competing free Bible app is comfortably satisfied; future γ-cluster ships add depth in
specific dimensions (Tewahedo distinctive readings, manuscript text-critical
apparatus) rather than chasing raw count.

Every change should make the demo better, simpler, deeper, or more impressive. If a
change doesn't serve the demo, defer it explicitly unless the user pulled it forward.

### Patristic-source voice composition (invariant)

The γ.4 patristic source corpus (`content/sources/ethiopian_commentaries.json`) is a
**Cyril-led patristic chorus + the three uniquely-Tewahedo-canonical voices (1 Enoch /
Jubilees / Meqabyan)** plus the Syriac (Ephrem) and apostolic-bridge (Athanasius)
supplements. **Cyril remains plurality-leader by design**, guarded by
`test_cyril_remains_plurality_leader_at_arc_close` (asserts Cyril > Athanasius AND
Cyril > Jubilees — sufficient under all plausible future expansion). If Cyril's share
crosses 50% in future detail-wave expansion, that is acceptable but flag it in the
SESSION_STATE headline so the trajectory stays visible; balance with Ephrem or
pseudepigraphical expansion if a v1.1 uniqueness-angle pick (memory `v1_terminus`)
calls for it. **Full six-voice statistical history (γ.4.4–γ.4.9 + the Meqabyan
arc-close) → see `dev/archive/RULES_HISTORY.md`.**

### Parallel-Bible end-state — two standalone Bibles (codified 2026-05-16)

**A first-class north-star goal, not a popup feature.** The τ.6.x (`geez-tewahedo`) +
τ.7.x (`amharic-tewahedo`) per-book parallel-Bible ingests exist to produce **TWO
STANDALONE Bibles** — a Ge'ez Bible and an Amharic Bible, each a full version with its
own books and chapters — each carrying, in **its own** verse popups, a faithful
English translation of its actual Ge'ez / Amharic wording (a fresh rendering of what
the text says — NOT the KJV, NOT the English editorial baseline).

The per-book rendering already shipped is the FOUNDATION for this, not popup-language
data. Verse-popup policy:
- **The other 9 editions:** NO Ge'ez/Amharic popups. Do not wire them into any
  edition's `popup_languages_default` / `popup_translation`.
- **The existing English `ethiopian-tewahedo` edition:** only *conditionally* —
  permitted ONLY if every verse count matches across all books and chapters (full
  per-verse parity). A maybe, not a commitment.
- **The two standalone Bibles:** YES — their own verse popups carry the faithful
  English back-translation. This is the point.

Source policy: Amharic = as-written-in-the-parallel-Bible-PDF (cited to that source);
Ge'ez gaps filled from the `GAPS` folder (DEFERRED — note-only until the user
re-engages after rendering). Sequence: finish rendering (the only active phase; keep
shipping per-book τ.7.x.* / τ.6.x.* under D1-a + D4-c) → constitute the two standalone
editions → finalize sources → English back-translation → wire into their own popups.
Phases 2–5 are post-rendering; do NOT pull them forward. Full spec:
`dev/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md`.

### Self-upgrading matrix rule (codified at audit U-belt 2026-05-20)

**When a step unlocks the next step, the next step is responsible for upgrading its
own plan/tools BEFORE executing.** The matrix is self-evolving — it doesn't wait for
the next session to add the lesson. Canonical triggers + responses (the rule
generalizes to ANY future unlock):

- **New failure class** found during C-3/C-6 review? → at C-9 close the closing
  reviewer APPENDS the class to the relevant section of
  `content/manuscript/_reviewer_context/{GG,CAM}_topology.md` AND (if
  pattern-detectable) adds the detector to
  `scripts/core/manuscript_self_check.py`'s screen list.
- **New chapter complexity class** beyond NARRATIVE/LIST/REGNAL_FRAME? → extend
  `scripts/core/manuscript_chapter_class.py` BEFORE running the first chapter of the
  new class; pin via test.
- **New provenance tier**? → register it in `scripts/core/provenance_tiers.TIERS`
  BEFORE shipping a book that uses it (`provenance_tier_known` lint fails otherwise).
- **New outside-repo dependency**? → either move it INSIDE the repo (gitignore if
  large) OR document its external location in this file. (GAPS/ is the canonical
  example: moved inside, 1 GB, gitignored.)
- **New production-rendering track**? → extend `scripts/render_coverage.py` with the
  track's coverage class; extend
  `scripts/core/canonical_verse_counts.CANONICAL_BOOKS` if it produces KJV-skeleton
  books; ship a design spec under `docs/superpowers/specs/`.
- **Stale METHOD NOTE or rule**? → fix it IN THE PLAN at the same commit, reason in
  the CHANGELOG (don't leave the contradiction for the next session).
- **A test/lint check would have caught the defect earlier**? → add it at the same
  commit ("defect found ≠ defect prevented" applied at the meta level).

**General form:** every step that unlocks the next ALSO upgrades the matrix so the
next step starts BETTER than this one did. Documentation, helpers, lint pins, tier
registry, plan METHOD NOTES — all extensible at C-9 (or the equivalent ship-close
moment in non-marathon tracks). The next session's first action should be reading the
upgraded matrix, not re-discovering yesterday's lesson.

## 2. Universal principles

1. **Fully customizable.** Every UI element, symbol, marker, kind name, category,
   color, label — assume the user will want to change it. Defaults exist; nothing is
   hard-coded.

2. **Easy.** No YAML hand-editing, no CLI knowledge, no build-pipeline knowledge
   required. The dev tools should let a schoolteacher or parish priest produce their
   own edition.

3. **Verifiable by book/chapter order.** Every browsing / management UI defaults to
   canonical reading order — Genesis → Exodus → … → Revelation, chapters ascending. A
   *hard* requirement, not a stylistic preference. See §6.

4. **No shortcuts — completeness over speed** (user-directed; a top-level principle).
   Always pick the most complete + correct path even when it is far more work, and
   **any task may be PAUSED to do it right**. If a better, more-complete approach
   surfaces mid-task, **STOP and re-plan it** rather than patch forward on the
   inferior path. Momentum / bias-to-action never overrides correctness or
   completeness. *Canonical instance:* the 2026-05-27 Ge'ez-versification redesign — a
   1ki6 KJV-binning patch was abandoned for a full base-witness own-versification
   re-architecture once the deeper approach surfaced
   (`docs/superpowers/specs/2026-05-27-geez-own-versification-design.md`). Reinforces
   `feedback_proper_clean_correct` + `feedback_extensive_answers` +
   `feedback_dont_self_narrow_scope`.

5. **Never single-thread — always run ≥2 lanes** (user-directed). The project should
   never be doing only one thing. Keep a background lane busy alongside the
   foreground, and **when one side task completes, auto-pick the next** from the
   backlog — never drop to one lane. Respect the workload-tiered concurrency cap
   (`feedback_concurrent_agent_cap`: heavy >100k tokens MAX 1 · medium 30–100k MAX 2 ·
   light <30k MAX 4) and keep image bytes OUT of the controller context (QC by
   dimensions only, never read tiles in). **Side-task backlog — pick the next when a
   lane frees; keep this current:** CAM hi-res pre-pull of upcoming chapters ·
   base-structured re-collation of pending chapters · geez→kjv cross-ref anchoring ·
   the deferred Phase-E Clementine chapters (1es 5/8, 2es 14) · the code-debt audit
   tail (`dev/AUDIT_2026-05-26-FINDINGS.md`) · doc-coherence (MATRIX_MAP / REPO_MAP /
   CHANGELOG currency) · test-coverage growth · Phase-D own-versification source
   acquisition.

## 3. Sequencing rules

When the user delegates ordering ("do it all", "you decide", "push", "whatever
order"), Claude picks the sequence using these priorities, in order:

1. **Safest / most-foundational first.** Additive changes over destructive. Defaults
   that preserve existing behavior. Schema migrations that produce byte-identical
   builds when the new field is unset.
2. **Builder-demo value.** Phases that unlock or polish the demo come before ones that
   don't. Corpus depth (χ) is high-value.
3. **Pair related phases.** If two phases are obviously tied (schema + backend + UI
   for one feature), bundle them into one batch even if they ship as separate commits.
4. **Logical seams over arbitrary cutoffs.** Stop at a clean handoff point where
   another Claude (or future-self) could pick up cleanly, not mid-function.
5. **Bandwidth-aware.** Re-reading existing infrastructure is cheaper than rebuilding
   it. Inventory before scoping new work; check whether a CLI tool already does the
   thing. The CLI surface is the source of truth — web consoles WRAP it, never
   replicate.

When a task could be sequenced multiple reasonable ways, **pick the most logical one
for the project as a whole**, even if the user's casual phrasing suggests a different
order. The user has delegated this judgment; exercise it.

## 4. Save semantics

- **"Save" = a local git commit** (run `save.ps1` through **PowerShell ONLY** — never
  the Bash tool: the spaced repo path + `>`/arrow glyphs in a commit message break cmd
  and sweep stray files via `git add -A`). The pre-commit hook runs `ruff format
  --check .` + `lint_rules.py` — both must pass or the commit is BLOCKED (the hook
  does NOT run the test suite; run the relevant tests yourself). The GitHub remote was
  deleted 2026-05-12, so a save is a LOCAL commit only (`git push` fails until a remote
  is reconfigured).
- **⚠ BEFORE every save:** `python -m ruff format` every file you generated /
  regenerated — ESPECIALLY `content/translations/<id>/` stores (recurs on EVERY
  ingest) — or the hook blocks the commit. ruff reflows whitespace only (data + baked
  popups unchanged). Full rule: §7 "Formatting + committing".
- **Every save updates `dev/SESSION_STATE.md`** (last shipped phase · next · test
  count · in-flight notes) — non-negotiable for continuity (§11) — and **VERIFY the
  commit actually landed** with `git log`/`git status` before claiming "saved"
  (§12/§14 truth-gate). Never report a save that didn't happen.
- **"Backup" is a SEPARATE command from "save":** a commit is not a backup. Back up
  via `git bundle create <file> --all` (file BEFORE `--all`) to the external **E:/F:**
  drives (NEVER C: — system drive is low). **Backup CADENCE: proactively back up every
  3rd commit** (bundle on commits 3, 6, 9, …), AND at every `/clear` checkpoint, AND
  whenever the user says "backup".
- "Continue", "proceed", "go ahead", "push" are **NOT** save commands (here "push" =
  "advance to the next phase," not `git push`). Don't auto-commit at the end of a
  phase.
- **Zip flow is DORMANT** (Claude-Desktop-era). Never build a zip or ask slim/full on
  a bare "save". Only if the user *explicitly* says "zip": slim excludes regenerable
  artifacts (`content/translations/sources/`, `epub_working/.backups/`, `__pycache__/`,
  `.pytest_cache/`, `*.bak`, `*.tmp`, `.git/`); full is the whole working tree.

### Checkpoint saves

A save can be issued *mid-task* when the user explicitly asks for one. This is a valid
pattern, not an error. At checkpoint time: IN_FLIGHT.md stays `<!-- TRACKER-STATE:
active -->` with the current task's progress documented; SESSION_STATE.md reflects the
save happened *during* the in-flight task; the linter's `inflight_freshness` showing
`active for X.Xh (fresh)` is correct, not a bug. A checkpoint preserves user-visible
work without forcing premature completion (to share, test offline, or back up before
the next risky change). *First instances → see `dev/archive/RULES_HISTORY.md`.*

## 5. Phase / commit tracking

- The Greek-letter phase system: α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ. Sub-phases use
  dotted suffixes: `ν.2.5-A`, `ν.2.7-A`. Letter assignments are sticky — a feature
  lives with one letter forever.
- `dev/PLAN_<date>.md` is the master sequence doc. Every new phase gets inserted in the
  right position there.
- `dev/SCOPE_<date>-addendum-<topic>.md` for major feature specs that need more than a
  paragraph.
- **Each shipped phase corresponds to a local git commit; the legacy v28a-NN build-tag
  scheme is retired.**

## 6. UI conventions

### 6.1 Book/Chapter order is canonical

Any UI that lists books — pickers, matrices, summaries, audits, diff views — uses the
order from `content/books.yaml`: Genesis → Exodus → … → Revelation, then Apocrypha /
deutero in their canonical positions, then any Ethiopian-only books at the end. **Do
not sort books alphabetically, by note count, or by "importance".** Reading order is
the only correct order. Chapters inside a book sort ascending by chapter number;
verses inside a chapter ascending by verse number. Where a UI must show a different
order (e.g. an audit sorted by problem severity), canonical order must remain *one
click away* (a "sort by canonical" button or default).

### 6.2 Cross-linking

Every console header links to every other console. The current console is
`font-semibold`; the others are `text-blue-600 hover:underline`. New consoles add
their link to every existing console's header AND list every existing console in their
own header. Enforced by `scripts/lint_rules.py` (check id `6.2`) and surfaced in
`/preflight` as **Rules compliance** — fix on linter complaint before saving.
**Pre-existing exception:** the consoles' "matrix" nav link points to `/` rather than
`/matrix` (project-old debt: `/` serves the note editor INDEX_HTML, not MATRIX_HTML).
The linter accepts both `/` and `/matrix` for the matrix cluster. When cleaned up, do
it cross-cuttingly across all console nav blocks at once and update the linter's
`matrix_aliases` set.

### 6.3 Styling

- Tailwind via CDN (`https://cdn.tailwindcss.com`). No other CSS frameworks. No CSS
  build step.
- Inline `<style>` blocks for truly per-page touches; Tailwind utility classes for
  everything else.
- No JavaScript build step. Plain ES6 in `<script>` tags.

### 6.4 Reactivity & forms

When a console renders form fields, both `<input>` and `<select>` (and `<textarea>` if
added) must participate in the dirty-check + save logic. The pattern is
`box.querySelectorAll('input, select')` — never just `'input'`.

### 6.5 Defaults for additive features

A new UI control that adds a feature defaults to the "don't change anything" position.
Publishers opt *in*, not *out*.

## 7. Code conventions

### 7.1 Backend

- One BaseHTTPRequestHandler in `scripts/web.py`. `/foo` for HTML, `/api/foo` for
  JSON. New routes add an `if path == …` branch in `do_GET` / `do_POST` / `do_PUT`.
- YAML for config (editions, kinds, canons, themes, _meta). Python files with tuple
  data for bulk content (notes, translations).
- Loading data files: `ast.literal_eval` only — never `exec`. Translation/notes
  modules look like Python but must not be executable; a corrupted or hostile data
  file must not run code.
- **Caching depends on file mutability:**
  - **User-editable runtime data** (notes, translations — editable while the web
    process runs): cache with `lru_cache` keyed on `(path, mtime_ns)` so on-disk edits
    auto-invalidate without a restart. Canonical pattern:
    `scripts.core.notes_io.load_notes` + `_load_notes_cached(path_str, mtime_ns)`; also
    `scripts.core.translations`.
  - **Project-internal published data** (Strong's, TSK, Nave's, commentary corpora
    like `ethiopian_commentaries.json`, config loaders in `scripts.core.config`):
    cache as singletons via `@lru_cache(maxsize=1)`. Updates ship via git commit +
    process restart. Tests that mutate these in fixtures MUST call
    `<loader>.cache_clear()` in setup.
  - If a `maxsize=1` loader needs to react to runtime edits, upgrade it to the
    mtime-keyed pattern (don't retain the singleton and invalidate manually).
- Writes go through `notes_io.atomic_write`. Bulk/destructive writes go through
  `notes_io.ensure_backup` first.

### 7.2 Schema migrations

- Adding a field is **always** a no-op when the field is unset. Builds with the field
  unset must be byte-identical to builds before the field existed.
- New required fields are forbidden. If a field "must" be set, pick a sensible default
  and document it.
- Write YAML edits via `_patch_yaml_entry` / `_patch_yaml_list_field` in
  `scripts/web.py` — they preserve comments, ordering, and surrounding structure.
  Don't rewrite YAML with `yaml.dump`; that loses comments.

### 7.3 Project structure

Books use lowercase 3-letter codes: `gen`, `exo`, `1ki`, `tob`, `lje`, `2es`, etc. The
87-book Ethiopian Tewahedo set is the superset; smaller canons are subsets in
`content/canons.yaml`. (Notes files use the *canonical* codes — joe/jhn/phi/jam/eze/
nah/mrk/psa — not the legacy grammar aliases; normalize book codes at ingest. Memory:
`feedback_book_code_canonical`.)

### 7.4 One-shot ship scripts

`scripts/_ship_*.py` files are one-shot ledgers of entries appended to
`content/sources/*.json` at a specific ship moment. NOT re-runnable in normal
operation (re-running duplicates entries, though N-W4 idempotency now protects
χ-cluster ships). **One-shot `_ship_*.py` ledgers are archived to
`dev/archive/ship_scripts/<arc>/` (original filename preserved) after their arc
closes; the arc-close commit documents the retired-not-deleted status.** Distinguish
from permanent at-scale driver scripts (`scripts/run_*_at_scale.py`) — re-runnable
detectors that stay in `scripts/` indefinitely — and from obsolete safety scripts
(e.g. `scripts/_dedup_ethiopian_notes.py`) which carry a "LOAD-BEARING-NO-LONGER"
docstring banner and stay as emergency-restore tools, tracked in the SESSION_STATE
inventory.

## 8. Testing conventions

- pytest classes named `TestX` per feature. Live in `tests/test_scripts.py` (most
  things) or `tests/test_core.py` (core modules).
- Both unit (helpers, parsers) and integration (against real on-disk data) where each
  pulls weight.
- A new feature isn't done until it has tests that would catch the demo breaking.
- Tests restore any global state they mutate (use `tmp_path` + `shutil.copy` to back
  up files before edits; restore in `finally`).
- **State-aware over default-assumed.** A test that depends on the world being in a
  specific state (e.g., "IN_FLIGHT marker is idle") should *parse the actual state*
  and verify the contract-against-that-state, not assume the default. Pattern: read
  the marker first, branch on its value, assert the appropriate invariant for each
  branch. (Caught when ψ.3's mid-task work flipped IN_FLIGHT to `active` and broke a
  test that assumed `idle`.)

### 8.1 Arc-close pin convention

When a multi-wave content arc closes (a parent phase like γ.4.4 whose detail-wave
sub-phases A/B/C/D/E ship across multiple turns), the closing wave's test class MUST
add three specific kinds of pin:

1. **`_meta` synchronization pin.** Assert the JSON `_meta` `source`/`scope` block
   names the arc's parent phase tag AND every shipped sub-phase tag. Pattern: regex
   word-boundary match (`re.escape(phase) + r"(?![.A-Z])"`) so γ.4.4 doesn't match
   γ.4.4.B. Pin per sub-phase, not all in one test — granular failures are easier to
   diagnose.
2. **Absolute-count milestone pin.** Assert `corpus_count >= N` (N = cumulative count
   at the arc's close). Use a count milestone (`enoch_count >= 190`), NEVER a share
   threshold — share-pins break mechanically when later waves dilute the share even
   though the historical achievement is preserved (memory `feedback_share_pin_pattern`).
3. **`all_N_sections_covered` exhaustiveness pin.** Assert every section the arc was
   supposed to cover has substantive coverage (≥ a stated minimum or a
   substantive-content marker). Pattern: a single test like
   `test_all_six_<arc>_sections_substantively_covered` iterating the expected section
   list. Prevents a future "I'll ship X later" from silently leaving the arc partially
   closed.

When to use: only at the **closing wave** of a multi-wave arc (identified by the arc's
substantive-coverage parity goal being reached), not at every intermediate wave.
**Anti-pattern:** a share-pin in the arc-close class — the convention exists in part to
replace the failure-prone share-pin with the durable count-milestone pattern.
*Existing instances (γ.4.4.E / γ.4.5.E / ω.37 test classes) → see
`dev/archive/RULES_HISTORY.md`.*

## 9. Mental models for common tasks

### "Add a new edition feature"

1. Schema: add field(s) to `editions.yaml`, default to back-compat.
2. Loader: surface the field in `api_customize_data` (and `api_publisher_data` if it's
   a publishing field).
3. Validator: extend `api_save_edition_meta` to accept and validate the field.
4. UI: add the form control in the right console, in Book/Chapter order if it's a
   per-book matrix.
5. Build pipeline: read the field in `build_one`; default behavior when unset.
6. Tests: round-trip + invalid-input + back-compat + UI present.

### "Add a new translation"

**On-disk format.** A translation is `content/translations/<id>/`: a `_meta.yaml`
(license + provenance) plus one `<book_code>.py` per book, each exposing `TRANSLATION =
"<id>"`, `BOOK = "<code>"`, and `VERSES = [(chapter, verse, text), …]`. Loaded via
`ast.literal_eval` only — never executed. **Coordinates are canonical (KJV/WEB)
numbering**, because the base HTML the popups attach to is KJV-numbered; store each
verse under the KJV coordinate so the popup lands on the right verse.

**Two extractors, by source format:**
- **eBible "verse per line" .txt** → `scripts/extract_translation.py <id>` (its
  `TRANSLATIONS` registry documents each PD source). English / Latin / Arabic / JPS /
  Douay / Brenton-English, etc.
- **OSIS XML (morphhb, …)** → a dedicated per-source `scripts/extract_<id>.py` (e.g.
  `scripts/extract_wlc_morphhb.py`). The shared `scripts/core/versification.py` remaps
  the source's own verse numbering onto canonical KJV — `wlc_to_kjv_map` reads
  morphhb's `VerseMap.xml`; add a per-source map for each new original-language source.
  Validate every emitted coord with `canonical_verse_counts.coord_in_canonical_extent`
  (0 out-of-extent).

**Original-language house markup (the `<em>`-per-word format).** Hebrew/Greek verse
text is **trusted pre-formatted HTML** (`popup_versions.is_trusted_html` → passed to
the aside renderer RAW, never escaped). The exact format, byte-pinned against the
recovered base in `tests/test_wlc_ingest.py`: **each word wrapped in `<em>…</em>`,
joined by single spaces**; morpheme `/` separators stripped; maqaf-joined words kept in
ONE `<em>` (`אֶת־הָאוֹר`); sof-pasuq glued onto the last word (`…ךְ׃`); paseq is its own
standalone `<em>׀</em>`; pe/samekh paragraph markers dropped; and **scribal special
letters the source nests *inside* a `<w>` (large/suspended — the Shema, Lev 11:42, Judg
18:30, Num 27:5) must be fully captured — read the whole element, not just `.text`, or
you silently drop letters.** Plain-text translations are NOT trusted_html — HTML-escaped
at render.

**Formatting + committing (the pre-commit hook enforces it).** Both extractors emit
**one line per verse** (grep-able). Before saving a new/re-run translation, run
`python -m ruff format content/translations/<id>/`: ruff (line-length 120) wraps any
verse tuple over the limit onto multiple lines — most em-per-word Hebrew/Greek verses
wrap, matching how `kjv/*.py` is stored. **Skip this and the pre-commit hook `ruff
format --check .` blocks the commit.** ruff only reflows whitespace, never the string
values, so data + baked popups are unchanged (re-verify with one `get_verse` call if
paranoid).

**Wiring it on:** flip the version's data on in `scripts/core/popup_versions.py` (an
original-language slot already in the base lives in `_BAKED_NOW`; otherwise a version
bakes once `get_verse` returns text) → regenerate (`python -m
scripts.generate_verse_popups`) → verify the coverage jump + spot-check sample verses +
the named versification-divergence loci + `ebible verify errors=0` + flagship
`epubcheck 0/0/0/0`. The `/customize` console discovers the translation automatically
(no UI work unless it needs special metadata). Existing instance: WLC seed → full
39-book / 23,142-verse ingest (τ.5-A.x / Phase 2, 2026-05-23; `dev/CHANGELOG.md`).

### "Add a new popup language"

1. Find PD source data; place under `content/translations/sources/<lang_id>/` or
   similar.
2. Add a CSS class (`vnote-<lang>`) to the source HTML generation pipeline.
3. Register the language in `scripts.build_edition.POPUP_LANGUAGES`.
4. Update each shipping edition's `popup_languages_default` if the new language should
   be default-on.
5. The `/customize` per-book matrix picks it up automatically from `POPUP_LANGUAGES`.

### "Add a new per-book asset (covers, etc.)"

Same pattern as `popup_languages_per_book` — the project's custom YAML parser doesn't
do nested mappings, so per-book maps live as flat lists of `"<book_code>=<value>"`
strings on disk and decode to dicts in the API/UI layer.

1. Schema: add `<asset>_per_book` (list of strings) to `editions.yaml`. Default =
   absent / empty.
2. Encoder + decoder (mirror `encode_per_book_languages` / `decode_per_book_languages`
   in `scripts/build_edition.py`). Encoder MUST sort by canonical book order (§6.1).
3. Filter by canon when surfacing in the API. If a book is not in the edition's canon,
   do NOT show a slot (Tanakh 39, Reformed 66, Ethiopian 87).
4. UI lists books in canonical order — read from `books_canonical` in
   `api_customize_data`. Never sort books client-side.
5. If the asset is a file (cover image, etc.), the upload backend validates size,
   dimensions, MIME type, and aspect ratio BEFORE writing to disk; failed uploads must
   not mutate state. Use `notes_io.atomic_write` + `notes_io.ensure_backup`.

### "Add an uploadable binary asset (image, PDF, audio, etc.)"

Reusable for any future binary upload surface (codified after the cover-upload pipeline
shipped, π.4-B).

1. **Validate first, write never until clean.** Define `validate_upload_<thing>(bytes)
   → (ok, error, meta)` in `scripts/core/<asset>.py`. Order checks cheap-to-expensive:
   size cap → format magic-bytes → structural validity → semantic checks (dimensions,
   duration, aspect).
2. **Detect format from magic bytes, never the filename.** The filename is
   user-controllable; the bytes aren't.
3. **One canonical storage-path helper per asset** in the same module (see
   `storage_path_for_main` / `storage_path_for_book`). Future migrations consume this
   helper, never duplicate paths.
4. **Multipart parsing:** use `_parse_multipart` + `_extract_boundary` in
   `scripts/web.py`. Don't reach for `cgi.FieldStorage` (deprecated in 3.13) or pull in
   Werkzeug.
5. **HTTP layer:** route POST to a dedicated `_handle_<asset>_upload` method. Cap
   `Content-Length` at 2× the per-file limit so a hostile client can't tie up the
   server.
6. **Transactional write:** validate → `ensure_backup` existing file →
   `atomic_write_bytes` new file → save the YAML field → on YAML-save failure, **roll
   back the file write** (unlink). Disk and YAML must never disagree.
7. **The `api_save_edition_meta` path validator** rejects absolute paths, `..`, hidden
   segments, and disallowed extensions; reuse it.
8. **DELETE flow:** clear YAML first, then back up + unlink the file. If YAML clear
   fails, the file stays — partial state is detectable and recoverable, total loss is
   not.
9. **Tests cover:** happy-path round trip, every rejection path, "no file part" + "missing
   boundary" HTTP edge cases, "no disk write on validation failure", and DELETE leaves
   both YAML and disk clean.

### "Add a new static-file route (serve a directory back to the browser)"

Codified after π.4-B's `/content/covers/<...>` route. Reusable for any asset-serving
route (built EPUBs, PDFs, audio samples).

1. **Sandbox to a known-safe root.** Resolve the user path inside the safe directory;
   reject escapes:
   ```python
   file_path = (REPO / "content" / rel).resolve()
   safe_root = (REPO / "content" / "covers").resolve()
   try:
       file_path.relative_to(safe_root)
   except ValueError:
       return self._send_json({"error": "forbidden"}, status=403)
   ```
2. **Defensive rejection BEFORE the resolve check** — also block `..`, absolute paths,
   and hidden segments at the string level.
3. **Use `_send_file`** in `scripts/web.py` — handles content-type from extension, sets
   a short `Cache-Control: public, max-age=60`.
4. **Do NOT** add a write/upload path to a static-file route — reads and writes live on
   different routes; the static route is read-only.
5. **Tests cover:** 200 on valid path, 404 on missing file, 403/404 on `../` traversal,
   403/404 on hidden-dir access. Security-critical; tests are non-optional.

### "Add a meta-tool that integrates with the preflight dashboard"

Reusable for any check / scanner / validator that should be both a CLI and a visible
signal in the readiness dashboard (codified after the rules linter shipped, ω.0.1).

1. **CLI module first.** `scripts/<name>.py` with a pure `run_all() -> dict` API and a
   `main()` entrypoint. Standard dict shape:
   ```
   {"checks": [{"id": str, "name": str, "status": "pass"|"warn"|"fail",
                "message": str, "violations": list}, ...],
    "summary": {"total": int, "pass": int, "warn": int, "fail": int, "clean": bool}}
   ```
2. **CLI exit codes.** `main()` returns 0 on clean, 1 on any failure. Suitable for
   pre-commit hooks and CI without further glue.
3. **Preflight composition.** In `_compute_preflight_uncached()` in `scripts/web.py`,
   append a check importing `run_all`: status `fail` if any sub-check fails, `warn` if
   any warn, else `pass`; details list only the failing/warning sub-checks; `jump_to`
   usually `/preflight` or the console where the issue gets fixed.
4. **Wrap the import in try/except** — if the meta-tool blows up, the dashboard still
   renders (with a `warn`), not a 500.
5. **Tests cover:** the CLI imports cleanly; `run_all()` runs without raising on the
   current codebase; the preflight aggregator surfaces the check under its expected id.

### "Add a new aggregate API: compose, don't recompute"

When adding an endpoint that summarizes data already produced by another endpoint,
**compose** the existing one rather than re-walking the data:

1. Find the cheapest existing endpoint that already produces the raw counts you need
   (for corpus-totals, `api_attribution_audit()`, cached behind `_files_signature`).
2. Call it from the new endpoint. The cache makes repeated calls free.
3. Compute only the *derived* fields locally (deficits, percents, ranges).
4. Document in the docstring: "composes X; no new file scanning."

Why: the project does many file-walks (87 books × N note-files per edition). A second
walk for "the same numbers" doubles cost on every page render and hides cache
invalidation bugs. **Anti-pattern:** writing `_count_all_notes()` when
`api_attribution_audit().counts.total` already exists. *Existing instances → see
`dev/archive/RULES_HISTORY.md`.*

### "Add a new feature endpoint: pure function + thin route adapter"

The shape:

```python
# Pure function — testable without HTTP
def api_x(arg1, arg2, *, kwarg=default) -> dict:
    """Returns {"status": "ok"|"error", "code": str?, "http": int?, ...}.
    No global state. No HTTP. No subprocess if avoidable."""
    if not arg1:
        return {"status": "error", "code": "invalid_input", "http": 400, "message": "..."}
    return {"status": "ok", "data": ...}

# Thin route adapter — translates dict to HTTP
if path == "/api/x":
    result = api_x(arg1, arg2)
    if result.get("status") == "ok":
        return self._send_json(result)
    http_code = result.get("http") or 500
    return self._send_json({"error": result.get("code") or "internal_error",
                            "message": result.get("message") or ""}, status=http_code)
```

Three rules:
1. **The pure function returns a dict, never raises for expected errors.** Validation
   failures, not-found, etc. become `{"status": "error", "code": "...", "http": 4xx,
   "message": ...}`. Reserve raising for genuinely unexpected conditions.
2. **The route adapter does ONLY translation.** No business logic, no conditional
   fallbacks. If you find `if/else` in the route block, push it into the pure function.
3. **All inputs are explicit kwargs.** No `request.GET` reading inside the pure
   function. Parse the request in the route, pass plain Python values; tests construct
   the pure call directly.

**Injectable-callable variant (for orchestration):** when the pure function
orchestrates a slow or environment-dependent operation (subprocess, network, large
compute), make the operation an injectable callable parameter so tests pass a fast mock
instead of running real builds:

```python
def api_build_all_editions(*, version: str = "v28a", build_one=None) -> dict:
    if build_one is None:
        build_one = api_export_build  # production default
    for ed_id in edition_ids:
        result = build_one(ed_id, version=version)
        # ... aggregate ...
```

Why: tests stay fast; the shape is uniform; errors degrade gracefully (the
dict-not-raise contract turns a buggy validator into a 500-with-message, not a wfile
stack trace). **Anti-pattern:** writing logic inside the route handler that calls
`self._send_json(...)` mid-function — no longer testable without an HTTP server.
*Existing instances + the injectable-variant instances → see
`dev/archive/RULES_HISTORY.md`.*

### "Add a new corpus-growth phase (the χ cluster pattern)"

Each new corpus-growth phase (χ.7 Nave's, χ.1 Strong's Greek, χ.2-5 commentaries)
follows this exact shape and ships in roughly one focused turn. Don't re-derive.

**The pipeline shape:**
```
PD source data        →  Detector class               →  Candidates JSON         →  Promoted notes
(content/sources/        (scripts/core/detectors.py)     (content/candidates/        (content/notes/<book>.py)
 or content/                                              <book>_ch_<NNN>.json
 translations/)                                           — prospect.py format)
```

**Steps:**
1. **Acquire / verify the source data.** (First see the top-of-file "sources are NOT
   missing" guard.) Check `content/sources/` first — TSK and Strong's Hebrew already
   cache there. New corpora go in the same directory or `content/<source>/`. Add a
   loader to `scripts/core/sources.py` if needed. Update
   `content/sources/ATTRIBUTIONS.md` with the PD/CC notice.
2. **Add the kind code** to `content/kinds.yaml` if the detector produces a
   category-prefixed kind not already there (`topic-nave`, `lang-greek`). Existing
   detectors reuse existing kind codes (`xref-citation`, `lang-hebrew`).
3. **Write the detector class** in `scripts/core/detectors.py`, mirroring
   `CrossRefDetector` (no verse text) or `HebrewWordDetector` (verse text required).
   Both extend the base `Candidate` dataclass return shape. Add to `ALL_DETECTORS` if
   it should run via `prospect.py`.
4. **Write the driver script** at `scripts/run_<kind>_at_scale.py`, modeled on
   `run_xref_at_scale.py` (no verse text) or `run_hebrew_at_scale.py` (reads verse text
   from `content/translations/kjv/<book>.py`). Both bypass `prospect.py`'s EPUB-build
   dependency by iterating cached source data directly, writing candidates JSON in
   prospect's exact format so `promote.py` works unchanged.
5. **Run the driver.** First on a small book as smoke test (`--books jud`). Inspect a
   sample candidate JSON. Then full corpus. For threshold-based detectors (TSK has
   `--min-votes`), start conservative; lower if needed.
6. **Batch promote** with `python3 scripts/batch_promote_xrefs.py --kind <kind>`. The
   `--kind` filter prevents promoting mixed kinds. The batch promoter is in-process and
   idempotent (dedup against existing notes).
7. **Verify (source-level):** `pytest` passes (corpus floors absorb growth),
   `lint_rules.py` passes, attribution audit shows the new notes attributed.
8. **⚠ BAKE-AND-PROVE GATE — a corpus change is NOT done until it is in a build.**
   Promoting only writes the SOURCE (`content/notes/`); `build_edition.py` zips the
   PRE-BAKED `epub_working/` base, so a build will NOT contain the new notes until you
   bake them in. Run, in order: `inject --all-books` (additive — `--dry-run` first to
   confirm it only ADDS, never deletes) → **`python scripts/check_nested_anchors.py`
   (run `--fix` if it reports any) + `pytest tests/test_nested_anchors.py`** → `ebible
   verify` (marker↔aside pairing) → rebuild a flagship edition → `epubcheck 0/0/0/0`.
   **If the rebuilt EPUB is the same size as before the change, you forgot to inject.**
   Commit the changed `epub_working/` split files alongside the notes.
   - **⚠ The nested-`<a>` check is MANDATORY — epubcheck does NOT replace it.** `inject`
     can place a `note-ref` marker INSIDE a verse's `vn-link` anchor = nested `<a>`
     (invalid base XHTML). The build converts `vn-link <a>`→`<span>`, so the BUILT EPUB
     stays valid (epubcheck 0/0) even when the BASE carries thousands of nested `<a>` —
     only `test_nested_anchors` catches it. Corollary: a "full suite passed" claim from
     a CURATED SUBSET is NOT a green suite — name the tests you actually ran, and
     include the base-invariant (`test_nested_anchors`) + translation tests, not just
     `test_scripts`/`test_core`. (Memory: `base-invariant-gating`.)
9. **CHANGELOG entry** with cumulative corpus math: `Was: N notes → Now: M notes
   (+delta · X% of 35K target)`.

**Why this works:** pure-function-API + thin route adapter at the detector level;
compose-don't-recompute (the driver composes existing detector classes; the batch
promoter composes existing `promote.promote_candidate`); idempotent (re-running
produces a superset; dedup in promote skips already-shipped notes).

**Anti-patterns:** rebuilding `prospect.py` to bypass the EPUB dependency (the driver
*uses* the existing detector class + writes the same JSON format `prospect.py` would —
`prospect.py` stays unchanged); subprocess-looping `promote.py` per file (the
in-process `batch_promote_xrefs.py` is ~80 lines, runs in seconds). *Existing instances
(χ.6 / HebrewWord / Torrey, + the 14,568 nested-`<a>` incident) → see
`dev/archive/RULES_HISTORY.md`.*

### "Register a new note kind"

To add a `kind` to `content/kinds.yaml`:
1. **Mirror a sibling** in the same `category` (copy its `symbol`,
   `note_class`/`marker_class` shape, `label`, `phase`). Kinds SHARE their category's
   symbol; `inject.glyph_for` reads the per-kind `symbol`.
2. **Register only in a commit where the kind gains ≥1 note.** The `/preflight`
   `empty_kinds` check warns on any registered kind with zero notes
   (`scripts/api/preflight.py`), so ship the kind + its first notes together.
3. **Bump the count pins:** `record_count` in `tests/test_validate_schemas.py` (=
   editions + kinds; +1 per new kind) and the `content/kinds.yaml — N kinds` docstring
   in `scripts/core/matrix.py`.
4. **Edition enablement is automatic by category** — a new kind is enabled wherever its
   `category` is enabled (no `editions.yaml` edit needed); confirm with a build.

### "Build a defensive system: use the four-tier shape"

When the next defensive system is needed (input-validation hardening, content-security
policy, data-integrity auditing), follow this template instead of inventing a new
arrangement.

```
TIER 4  Behavioral / protocol      FIRST line — cheapest layer: judgment + a small protocol doc.
TIER 1  Per-action audit           SECOND line — a short script/checklist that runs at each commit/response.
TIER 2  State of record            PERSISTS across turns — a small visible file declaring "what's open." Survives compaction.
TIER 3  Continuous automated check FINAL backstop — linter/preflight check that surfaces drift to humans.
```

Each tier covers a failure mode the others can't catch as cheaply: T4 is free per-turn
but relies on memory; T1 is cheap automation but fires once; T2 is a state record but
doesn't enforce; T3 enforces but is expensive to add. Together = defense in depth.

**Reach for this template** if any are true: multiple distinct failure modes need
different detection methods; failures can leak across turns/sessions/pages; a single
check would have to run at multiple times to be effective; there's a gradient of cost
(cheap-but-fallible vs expensive-but-thorough). **If none are true, don't tier** —
single-purpose tools (like `scripts/cleanup.py`) are correctly one-pass; the audit
question is "is there a failure mode that escapes the single layer?" If no,
single-layer is correct.

**Map a new defense to the tiers:** (1) identify the canonical drift signature; (2)
pick a primary tier (usually the cheapest that can detect that drift mode — T4 for a
discipline issue, T3 for a structural invariant); (3) pick a backstop tier (usually one
tier later); (4) document in the system's CHANGELOG entry which tier owns which drift
mode, as a coverage matrix:
```
                       drift class A   drift class B
TIER 1 audit            PRIMARY         backstop
TIER 2 state record     no              PRIMARY
TIER 3 linter           backstop        backstop
TIER 4 protocol         no              no
```
The matrix forces explicit thinking about gaps: any column without a PRIMARY is a hole;
any row without a PRIMARY is a tier not pulling its weight. *Existing instances (§15
backend drift detection · ω.0.6 frontend crash defense) → see
`dev/archive/RULES_HISTORY.md`.*

### "Surface a developer-only style knob as a per-edition option"

The project has a long tail of style knobs in `scripts/style_config.py` and adjacent
modules originally developer-only. As publishers need finer control, each gets surfaced
individually:

1. **Schema first.** Add the field to `editions.yaml`-style records via
   `api_save_edition_meta`'s `EDITABLE_TEXT` / `EDITABLE_BOOL` sets. Default MUST
   preserve current behavior.
2. **Validate enumerations.** If the field accepts a fixed set, define the set as a
   module-level constant in `scripts/build_edition.py` (e.g. `CHAPTER_NUMBER_FORMATS`)
   and reject unknown values with a clear error listing the valid options.
3. **Apply in build pipeline.** Add a per-edition pass in `build_edition()` between
   filter passes and packaging. The default (no-op) path must skip the file scan
   entirely so editions that don't use the feature build byte-identically.
4. **Idempotency.** Design the rewrite so running it twice produces the same output
   (e.g. regex matches digits, decorated output contains words → no re-match).
5. **UI: collapsible card on /customize.** Group related knobs in a `<details>` block
   with a clear summary line. Stamp a small italic "applies on next BUILD" note if
   relevant.
6. **Tests cover:** each enumerated value renders correctly in isolation; the
   build-pipeline pass is a no-op for default settings; happy-path round trip;
   rejection of unknown values.
7. **Existing infrastructure check** — before scoping a new style knob, search
   `scripts/style_config.py`, `scripts/apply_style.py`, `scripts/set_reader_toc.py` for
   the toggle. Many useful knobs already exist as developer-only constants and just need
   surfacing through schema + UI; reinventing them is the anti-pattern this guards
   against.

### "Extract a topic cluster from a god-module into scripts/api/<topic>.py"

The same shape recurs when god-modules need decomposing (`scripts/build_edition.py`,
`scripts/prospect.py`). Follow this template; don't re-derive.

1. **Identify a cohesive topic cluster.** A good slice is 3–10 handlers sharing an HTTP
   prefix (`/api/snapshots/*`), a domain concept (covers, sources, editions), or an
   internal helper graph (preflight + its cache helpers). Mixing two unrelated topics in
   one slice is the anti-pattern — split them.
2. **Create `scripts/api/<topic>.py`** with: a module docstring naming the phase tag,
   the handlers moved, what stayed in web.py and why, and the lazy-import pattern;
   `from __future__ import annotations`; module-level imports only for guaranteed
   non-circular libs (`config`, `audit_log`, `notes_io`, `pathlib`). **NEVER**
   top-import from `scripts.web` — that's the circular hazard.
3. **Move handler bodies verbatim.** Don't refactor in the same commit. Preserve every
   comment, docstring, decorator, error message. The diff reads "moved" not "rewrote."
4. **Lazy-import web.py-only dependencies inside the function body** (`_files_signature`,
   `_save_cover_bytes`, `api_attribution_audit` stay in web.py for now). Callers import
   them at call time, NOT module-load time — sidesteps the circular import.
5. **Replace the inline defs in `scripts/web.py`** with a thin re-import block:
   ```python
   # <Topic> API (Phase <tag>) — implementation moved to scripts/api/<topic>.py.
   # Re-imports preserve scripts.web.api_X for route-table lambdas + tests.
   from scripts.api.<topic> import (  # noqa: E402
       api_X, api_Y, ...
   )
   ```
   Route tables and the legacy if/elif dispatch continue referencing `api_X` by flat
   name — the re-import preserves binding identity.
6. **Add a `TestPhaseN<Topic>Extraction` class** with: `test_<topic>_module_exists`
   (`hasattr` for every moved name); `test_handlers_backward_compatible_via_web` (every
   name importable from `scripts.web` + callable);
   `test_handlers_actually_live_in_new_module` (`is`-identity between
   `scripts.web.api_X` and the canonical home + `__module__ ==
   "scripts.api.<topic>"`; for audit-decorated handlers unwrap via `getattr(fn,
   "__wrapped__", fn)` first); `test_audit_decorator_preserved` (pin
   `@audit_log.audit_endpoint` still in place); `test_web_py_does_not_define_<topic>_handlers_inline`
   (source-scan for `def api_X(` and assert absence); `test_route_table_still_dispatches_<topic>`
   if applicable.
7. **Cross-module retarget.** If other `scripts/api/*.py` lazy-import helpers you're
   moving from `scripts.web`, retarget them to the new canonical home in the same ship +
   add a test asserting the source contains the new import path.
8. **Update `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, `dev/CHANGELOG.md`** with: slice
   name + what moved; net line-count delta in web.py; cumulative delta across the track;
   test count + linter status.

**Why this works:** zero behavior change (route registration unchanged; dispatcher
resolves the same callable through the re-import); tests stay co-located; lazy import
sidesteps circularity (web.py → api/<topic>.py is one-way at module-load; api/<topic>.py
→ scripts.web is deferred until call time). **Anti-patterns:** rewriting a handler
mid-extraction; top-importing `scripts.web`; mixing two topics in one slice; forgetting
the `__wrapped__` unwrap in the `__module__` test. *Existing instances (the ω.35-B.1–B.7
file split, cumulative 40.5% web.py reduction) → see `dev/archive/RULES_HISTORY.md`.*

### "Build an index-backed alternative for an expensive file-walk operation (the Δ-family pattern)"

The codebase has an expensive file-walk operation (opens every `content/notes/*.py`,
parses each, aggregates across the corpus) — correct, slow (~3s on 51K notes), called
frequently. An SQLite-indexed alternative would be ~10× faster but introduces
multi-process / xdist correctness hazards. The shape:

1. **Build the equivalent function under a new name.** Add `<name>_indexed()` alongside
   `<name>()` in the same module, plus an equivalence test pinning both produce
   byte-identical output for the same inputs.
2. **The equivalence test is non-negotiable.** It catches the index path diverging on
   disabled-kind filtering, empty-edition handling, chapter-key dtype (int vs str).
3. **A rebuild lock under `content/.locks/`** — file-based (`<feature>_rebuild.lock`)
   with `_acquire_rebuild_lock(*, timeout: float = 30.0)`. Pin TimeoutError-on-exceed
   with a short timeout in tests.
4. **TTL fingerprint cache** — `_compute_fingerprint()` stats every `notes/*.py`;
   memoize keyed on a monotonic clock with a configurable refresh interval (default 1s
   prod, 0s tests). Without this, every wire-flip attempt intermittently fails xdist.
5. **`notes_io` invalidation hook** — wire a callback in `notes_io.atomic_write` that
   calls the index's `invalidate()`. Without it, edits during a test run produce stale
   index reads.
6. **Per-worker index storage** — `corpus_index_<worker_id>.sqlite` (worker_id = `gw0`,
   … for xdist; `_serial_` for non-xdist). Prevents the cross-worker write race.
7. **Server warmup + session-scoped test fixture** — prod warms at server boot; tests
   use a session-scoped `corpus_index_warmup` fixture in `tests/conftest.py`. Without
   warmup, cold tests random-fail.
8. **Wire-flip in a separate phase.** The public function gets a one-line change to
   call the indexed variant; the file-walk implementation stays under its private name
   as the equivalence-test reference. **Do not delete the file-walk path** — it's the
   auditable "this is what the answer should be" reference.
9. **No `force=True` in equivalence tests.** On Windows under xdist that races with
   other workers' cached connections (PermissionError on `sqlite` unlink). Use
   `invalidate() + rebuild()`.

**Land every unblocker before flipping any wire** — skipping any one (rebuild lock / TTL
cache / notes_io hook / per-worker storage / warmup fixture) makes the wire-flip flaky.
**Anti-patterns:** wire-flipping before all five infra unblockers exist; deleting the
file-walk reference after the flip; `force=True` in equivalence tests; sharing one
SQLite path across xdist workers. *Full Δ.0–Δ.9 detail + the skip→failure-mode table +
existing instances (Δ.4 compute_matrix · Δ.5 dashboard_stats) → see
`dev/archive/RULES_HISTORY.md`.*

## 10. What this project is NOT

The project is a **free public app** (pivoted 2026-05-14, Ω.0). It is:

- Not a learning management system. Schools are an audience, not a feature category.
- Not a retail / sales product. There are no commercial surfaces — no ISBN / ONIX / sales / POD / retail. <!-- term-ref-ok --> Multi-format export (PDF / MOBI / HTML / TXT) survives only as a FREE download option, never a retail product. "Builder" means the person who makes their own free edition (older rules say "buyer").
- Not a multi-language UI by default. The editorial apparatus baseline is English;
  localized UI shells (Spanish, Portuguese, French, German) are a long-tail roadmap
  item, not a near-term goal. Bible *content* in many languages is the whole point;
  *interface* in many languages is the long tail.
- Not a real-time collab tool. One editor at a time; git history is the audit trail.
- Not Flask / FastAPI / Django. Standard library only on the backend; Tailwind CDN on
  the frontend. No build step.

*The pre-pivot strike-through history (the lifted "multi-language UI" and "POD"
guardrails) → see `dev/archive/RULES_HISTORY.md`.*

## 11. Continuity protocol — keep dev/SESSION_STATE.md current

**The point:** the user pays for tokens. Future Claude orienting via grep +
read-everything is wasted bandwidth. SESSION_STATE.md is a tight ~150-line snapshot any
Claude can read in seconds to be fully oriented.

### When to update SESSION_STATE.md

Always update it when:
1. **A phase ships** — record the new "last shipped" entry, bump the test count,
   refresh "next up".
2. **A save is requested** — verify SESSION_STATE.md is current BEFORE committing; if
   stale, fix it first (same commit). ("save" = a local git commit; the zip flow is
   dormant — see §4.)
3. **A scope change happens** — corpus goal, north-star clarification, deferral or
   reactivation of a phase.
4. **An external dependency or assumption shifts** — a source corpus is fetched, a new
   translation lands, a CLI tool is added.

Optional but not required: update on every push turn. Phase-ship + save-time covers
most cases. **Always upgrade the truth-record to observed reality** (deduction →
observation) and commit it (user-directed; memory `feedback_session_state_always_current`).

### What SESSION_STATE.md must contain

Required (kept short — every line earns its place): **Current phase** (what shipped);
**Test count** (total + delta); **Next up** (the single most-likely next phase + a
one-liner on why per §3); **In-flight notes** (anything mid-stream future Claude needs;
empty is fine); **Inventory pointers** (short "where things live" references so future
Claude doesn't grep); **Active rules / scopes** (links to the addenda that actively
apply).

### What it must NOT contain

Long narrative recaps (the rules doc + addenda are the long form); code snippets (they
drift — rely on the actual code); decisions Claude could re-derive.

### Update etiquette

Edit in place; don't append-only (the whole doc is a snapshot, not a journal). Keep it
under ~150 lines. When the user sends a save command, the SESSION_STATE update is inline
with the save turn — do it before committing; don't ask permission.

## 12. Retrospective protocol — keep CHANGELOG.md and the rules current

The chronological progress log lives in `dev/CHANGELOG.md`. **Append-only**, newest at
top, one block per session. Anyone can scroll it to review history without reading the
codebase.

### When to write a CHANGELOG entry

Always: at the end of any session that shipped ≥1 phase (before pausing/saving — even a
one-line entry); before any save (commit), ensure the entry for that session exists.

### When to additionally run a retrospective

A brief self-review beyond logging. Run one when **any** trigger fires after work ships:
1. **A new architectural pattern appeared** — if likely to recur, codify it as a §9
   mental model.
2. **Existing infrastructure was discovered mid-work** (you almost reinvented something)
   — add/sharpen an inventory pointer in SESSION_STATE.md.
3. **A rule wobbled or had to be invented on the fly** — if the resolution was good,
   codify it as a rule refinement; if bad, document the lesson.
4. **A memory rule needed updating** — add/update a cross-session memory entry when a
   durable preference/gotcha/lesson appears.
5. **A scope clarification happened** — update the rules + SESSION_STATE.md; CHANGELOG
   captures the change moment.

If none fire, just log and move on. Retrospection is a tool, not a tax.

### Learning capture — feed BOTH persistence layers at phase-close

Lessons only compound if they outlive the session. TWO stores; a phase-close
retrospective feeds whichever fit, and they must NOT duplicate:
1. **In-repo docs** (project-specific, versioned, re-read every session via §0): a
   reusable how-to → a §9 recipe; what-shipped/next/inventory → SESSION_STATE.md; the
   dated journal → CHANGELOG.md; a data-flow/"where does X live" fact → MATRIX_MAP.md /
   REPO_MAP.md; a stale rule → fix it in THIS doc at the same commit.
2. **Cross-session memory** (harness-level, loaded into every conversation): durable
   user preferences, working-style feedback, environment gotchas, "this paid off / this
   trap cost time" lessons NOT tied to one file. Update an existing memory before adding
   a new one; link related ones.

**The split:** if a future Claude could re-derive it by reading the current repo, it
goes in-repo (or nowhere); if it's a preference, a cross-cutting gotcha, or a *why* the
code can't show, it goes to memory. **Cadence:** at every phase-close + on the
retrospective triggers — not per-commit.

### Mistakes & near-misses → root-cause, then codify a preventive guard (always, same commit)

When something goes WRONG or nearly does — a defect shipped, a false/over-stated claim,
a destructive/surprise action, a near-miss, or anything that "should not have happened
and is preventable" — fixing the instance is NOT enough. Run a brief post-mortem and
codify the cheapest durable guard so it cannot recur, **at the same commit** (never
defer to "next session" — the next session resumes on "continue", which never fires the
deferred fix). Non-negotiable for any preventable lesson; a genuine one-off that truly
cannot recur just gets logged and skipped.

1. **Root-cause first, never the symptom** (`superpowers:systematic-debugging` Iron
   Law). Patching where it surfaced without finding *why* guarantees recurrence.
2. **Pick the cheapest guard that makes recurrence impossible, by failure type:**
   - *Technical defect a check could catch* → add the test/lint/gate (the §1
     self-upgrading "defect found ≠ defect prevented" rule). Instances: the §9
     nested-anchor gate (after the 14,568-instance base regression); the
     `coord_in_canonical_extent` boundary guard (after out-of-extent notes); the
     `find_verse_region_b` root-fix + its TDD pins.
   - *Behavioral / process / judgment failure, or a* why *the code can't show* → a rule
     line in THIS doc and/or a cross-session memory (per the dual-store split).
     Canonical instance: the commit/backup TRUTH GATE (§0 / §12 / §14 + the
     `verify-commit-backup-truth` memory), after the 2026-05-26 Torrey near-miss.
   - *A rule that wobbled / an interpretation invented on the fly* → refine the rule.
3. **Record it in the CHANGELOG** at that commit (what went wrong + the guard added).

Success test: afterwards, the SAME mistake made the SAME way is caught automatically or
forbidden explicitly. If no guard can make recurrence impossible, make it LOUD. This
generalizes the §1 self-upgrading rule (which fires on a step *unlocking* the next) to
the case where a *failure* is the trigger.

### Entry format

Each entry is a self-contained block, readable without context:

```
## YYYY-MM-DD — session-N — <one-line headline>

**Phases shipped:** ν.2.7-A, ν.2.7-B, π.4-A, φ.1, …
**Test delta:** +N (was M, now M+N)
**Save tag:** (local commit hash / "no save" / "pending")

What shipped (concrete, scannable):
- one bullet per concrete thing

Notable decisions (only if any):
- the choice and the alternative considered, in 1–2 lines

Retrospective (only when triggered, see §12):
- pattern recognized: <description>; codified in §9 of rules
- inventory pointer added: <name>; see SESSION_STATE.md
- rule refined: <ref>; lesson was <one line>

Continuity pointers:
- dev/SCOPE_2026-05-07-addendum-...
- §6.1 (canonical book order rule)
```

### What CHANGELOG.md is NOT

Not a replacement for git history (git is mechanical, this is editorial — what shipped
*and why*); not a replacement for SESSION_STATE.md (that's the *current* snapshot, this
is the *journal*); not for blow-by-blow micro-edits (one entry per *session*, not per
*commit*); not for retrospection that didn't happen.

### Footnote — pre-summary audit (Tier 1)

Before claiming "shipped X" — or "done / committed / backed up / safe to /clear" — in
any user-facing summary, run a 5-point audit. Each takes seconds; together they catch
the drift class the user previously had to catch manually:

1. **Test count reconcile** — run `pytest --collect-only -q | tail -1` and verify the
   number matches what the summary will claim. A divergence usually means work shipped
   without being tracked.
2. **Phase mention scan** — every Phase letter in the summary must appear in
   `dev/CHANGELOG.md` (this turn or earlier). A phase only in code/tests = a missed
   entry.
3. **In-flight marker check** — `dev/IN_FLIGHT.md` should show `<!-- TRACKER-STATE: idle
   -->` if summarizing a completed ship. If still `active`, either the work isn't done
   or you forgot to flip it.
4. **Linter ack** — run `python3 scripts/lint_rules.py`; for ship summaries every check
   should be `pass` (or have a known, acknowledged warn). Don't ship over a `fail`.
5. **Commit/backup truth** — run `git log -1 --oneline` + `git status --short`. Any
   "done / committed / backed up / safe to /clear" claim MUST match git reality: HEAD
   shows this session's work, and (for a backup claim) the `git bundle --all` file
   exists on E:/F:. Uncommitted verified work → warn loudly ("NOT committed/backed up —
   say 'save'"), never reassure. NEVER defer a commit across a /clear. This is the gate
   the other four don't cover — they verify work is *recorded*, not that a commit/backup
   *happened*.

Why these five: each catches a different drift mode — tests-vs-claim catches
counted-but-not-recorded; phase mentions catch shipped-but-not-journaled; in-flight
catches task-left-open; linter catches structural drift; git-truth catches
claimed-saved-but-uncommitted. *The originating drift catches (the 2026-05-07 test-count
catch + the 2026-05-26 Torrey near-miss) → see `dev/archive/RULES_HISTORY.md`.*

---

## 13. Topic-shift protocol — audit before pivoting

The single most expensive failure mode of this project has been **topic-shift drift**:
mid-task on feature A, the user asks about B, you respond to B without first recording
where A stood, and A's work gets orphaned. The fix is a behavioral rule: **when the user
pivots topic, the pivot is a signal to close the loop, not to abandon it.**

### When the protocol fires

A new user message substantially **off-topic from the immediately-prior assistant
message**: different phase/feature/system area; different artifact (was code, now docs;
was UI, now data); different mode (was building, now discussing). A clarifying question
on the same topic is NOT a topic shift. "Push" / "Continue" / "Save" are NOT topic
shifts.

### What the protocol says to do

Before responding to the new topic: (1) **Read `dev/IN_FLIGHT.md`** — `idle` or
`active`? (2) **Check working-tree state** — `git status --short`; look for
modified/new files not yet documented. (3) **Run the linter** —
`python3 scripts/lint_rules.py`.

If any signal in-flight work, **the first part of the response is reconciling that
work**: finish it now (preferred — the pivot can wait one turn); or explicitly note "I
was mid-task on X; pausing it to address your new question; here's where it stood";
or archive it as abandoned with a CHANGELOG note (rare; only when the pivot makes the
in-flight work irrelevant). Then engage with the new topic.

### Why this can't be fully automated

The linter's `check_inflight_freshness` and `check_untracked_phases` catch *symptoms*
of drift after the fact, not the *moment* of topic shift — "are these two messages about
the same thing" is a content-level judgment only a human-or-LLM reader can answer. So
this rule is a behavioral commitment; the automated checks are the backstop for when it
slips. *The originating 2026-05-07 ν.6 drift narrative → see
`dev/archive/RULES_HISTORY.md`.*

## 14. Session-resume / state-uncertainty audit

A close cousin of §13. Where §13 fires on **the user pivoting**, this fires on **Claude
being uncertain about state**. Different trigger, same defense.

### When this protocol fires

Any time Claude has reason to think the working tree might differ from its in-context
mental model: a `[NOTE: This conversation was successfully compacted...]` marker at the
top of context; a long stretch since the last `view`/`bash` call against a file; an
IN_FLIGHT/SESSION_STATE edit fails because the file's content differs from what Claude
expected; a test count / file list / grep result returns numbers Claude doesn't
recognize; an str_replace fails because the "old_str" isn't there anymore.

### What this protocol says to do

**Before acting**, audit the actual state:
1. **Read `dev/IN_FLIGHT.md`** — what does the marker say? what does the active-task
   block describe?
2. **Grep for the phase / feature** Claude was about to work on (`grep -rn
   "ν\.5\|preview_impact" scripts/ tests/`) — check if it's already shipped.
3. **Run `pytest --collect-only -q | tail -1`** — does the test count match the last
   claimed number?
4. **Run `python3 scripts/lint_rules.py`** — any warnings or failures?
5. **Run `git log -1 --oneline` + `git status --short`** — does HEAD reflect the work
   the *last* session claimed it committed, and are there uncommitted changes the user
   may believe were saved? (Backstop for a prior session's false "it's committed /
   backed up" sign-off — the resume audit's other four steps don't look at git.) If HEAD
   lags the last SESSION_STATE's described state, surface it FIRST and offer to commit
   (it needs an explicit "save").

If any surface state Claude didn't expect, **revise the plan** and say so explicitly
("I was about to start ν.5, but the audit shows it's already shipped in PUBLISHER_HTML;
the remaining work is the CUSTOMIZE wiring") — honest, and saves both sides a wasted
turn.

### Why this is separate from §13

§13 is about the **user's** signal (a topic pivot); §14 is about Claude's **own** signal
(uncertainty in its mental model). Similar — audit before acting — but the trigger
sources differ. A user pivot is rare (a few per session); state uncertainty after
compaction is common (every long session). *The originating 2026-05-07 ν.5
post-compaction instance → see `dev/archive/RULES_HISTORY.md`.*

## 15. Chain of command — the tier hierarchy as a matrix

The drift-detection guardrails are organized as **four tiers**. This section documents
how they relate: which fires first, which catches what, how they escalate when one
slips. There's a **chain** (precedence — who acts first) and a **matrix** (coverage —
what each tier specializes in catching); they're orthogonal.

### The chain — escalation order

```
TIER 4  Behavioral protocols      ← FIRST line — catches drift before it happens.
        (§13 topic-shift,           If perfect, no other tier needs to fire.
         §14 state-uncertainty)
TIER 1  Per-turn pre-summary      ← SECOND line — catches drift before the user
        audit (§12 footnote,        reads the response.
         5-point checklist)
TIER 2  IN_FLIGHT.md tracker       ← STATE OF RECORD — persistent across turns,
        (§11, §4 checkpoint saves)  survives compaction. If T1 missed, T2 still
                                    shows what was open.
TIER 3  Continuous linter          ← FINAL backstop — surfaces drift to humans on
        (scripts/lint_rules.py)     every preflight. The auditable "did anything escape?"
```

**Earlier tiers are cheaper and prevent later tiers from needing to fire.** T4 is human
judgment (free per-turn); T1 is one shell command; T2 is a file edit; T3 is the same
command broader-scoped. Pay the earliest cost.

### The matrix — what each tier catches first

```
                       drift class
                       counted-but-  task-left-  structural   pivot/
                       not-recorded  open        invariant    state-uncertain
TIER 1 audit           PRIMARY       secondary   no           no
TIER 2 IN_FLIGHT       no            PRIMARY     no           secondary
TIER 3 linter          backstop      backstop    PRIMARY      no
TIER 4 protocols       no            no          no           PRIMARY
```

Each drift class has one **primary** owner (the tier that catches it earliest) and
possibly secondary/backstop owners. A fifth class — **claimed-saved-but-uncommitted** (a
"committed + backed up" claim while HEAD lags or no `git bundle` exists) → Tier 1's
git-truth check (pre-summary audit point 5) catches it before the user reads the claim;
the §14 resume audit (Tier 4) is the cross-session backstop (kept out of the grid only
for readability).

### When to escalate

If a tier's PRIMARY ownership of a drift class slips, the backstop tier covers — but at
a cost (it shows up later, the user might catch it manually, trust suffers). Treat each
escape (a thing the linter caught that the protocols should have caught earlier) as a
§12 retrospective trigger: either the protocol needs sharpening, or the rule needs a
better automated backstop. *The original drift event + the one-push build-out of all
four tiers (ω.0.4) → see `dev/archive/RULES_HISTORY.md`.*

Four levels, one task: keep drift visible.

---

```
dev/PLAN_<date>.md                          master sequence doc
dev/SCOPE_<date>.md                         original scope statement
dev/SCOPE_<date>-addendum-<topic>.md        major feature specs
dev/ROADMAP_FUTURE.md                       deferred ideas
dev/SPEC_MU_SYMBOL_TOGGLE.md                symbol toggle (μ phase)
content/translations/<id>/_meta.yaml        per-translation metadata
HANDOFF_README_v7.md                        deep architecture handoff
dev/archive/RULES_HISTORY.md                extracted finished-arc history (this file's source)
```
