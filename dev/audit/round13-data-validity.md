# Round-13 GRAND AUDIT — data-validity completeness gap CLOSED (Mac)

The round-13 deep-audit "data-validity" dimension **returned 0/0** — it checked code
paths but never enumerated the live corpus the code reads (`round13-mac-survivors.json`
`completeness[0]`). This closes that gap: a real enumeration of every translation +
notes store, the findings it surfaces, and their adversarially-verified disposition.

- **Tool (Mac-owned, durable):** `dev/audit_translation_integrity.py` — parses every
  `content/translations/<id>/*.py` (`VERSES`) and `content/notes/*.py` (`NOTES`) with
  `ast.literal_eval` and asserts the structural invariants the loaders silently assume.
  `--selftest` exercises every FAIL/WARN path on synthetic known-bad fixtures (13/13),
  so the gate provably *can* fail (closes completeness gap 3 — "a gate that cannot fail
  in a test is not a gate"). Live run: **0 FAIL · 23 WARN · 6 INFO (exit 0)**.
- **Verification provenance:** Workflow `wf_cd10903a-1a1` (5 agents — blast-radius trace,
  faith-critical legitimacy verdict, independent re-scan, + two adversarial refuters).
  **No finding was refuted; both the shipped-output verdict and the scripture-legitimacy
  verdict survived hard adversarial scrutiny at high confidence** (the blast-radius
  verifier *executed* the live standalone render to confirm).

## Corpus health (the good news)

- **Notes corpus is structurally pristine** — every `content/notes/*.py` entry is a
  uniform arity-9 tuple with all-int chapter/verse keys; **zero** dup-key/non-int defects.
- **Zero impossible coordinates** anywhere (no `chapter-missing` — no "Genesis 87:12"
  parse noise in any of the 529 translation stores). Every out-of-extent coordinate is a
  legitimate, well-known versification difference (LXX Psalm splits, Hebrew Gen 32:33,
  4 Ezra 7's "missing verses", the Tobit GII recension), **not** corruption.
- **No scripture-data change is warranted by this audit.** The faith-critical Ge'ez
  Psalter data is correct as shipped.

## Findings

| # | sev | class | finding | owner |
|---|-----|-------|---------|-------|
| DV1 | low (latent) | correctness | Ge'ez-Psalter occurrence-multi collapse | hold for merge (dev-console-only; `scripts/core/translations.py`) |
| DV2 | low (latent) | correctness | `coord_in_canonical_extent` used `1≤v≤count`, wrong for non-1-start `aes` ch10 | ✅ **FIXED (`5bac50d5`, Mac, TDD + byte-stable)** |
| DV3 | info | classification | `VERSIFICATION="own"` under-applied to Tewahedo stores | merge triage (sensitive data) |
| DV4 | low (latent) | book_code_canonical | `ex→exo` (+`1k`/`2k`) store-stem aliases scattered across 5 local maps, not centralized | hold for merge (cross-file refactor) |

### DV1 — Ge'ez-Psalter occurrence-multi collapse (the headline; shipped output NOT affected)

`content/translations/geez-tewahedo/psa.py` and its parallel `geez-tewahedo-en/psa.py`
each carry **9 duplicate `(chapter, verse)` coordinates** — `(21,14) (36,24) (36,25)
(46,9) (68,2) (71,19) (101,3) (115,9) (144,18)` — where the two occurrences carry
**different text** (18 coords total, perfectly parallel across the two stores).

- **The data is legitimate — do NOT renumber.** These are the LXX/Rahlfs Ge'ez Psalter's
  *source-authoritative* numbering (the store header: "Source numbering is authoritative —
  NOT renumbered against the floor"). The legitimacy verifier mapped each to canonical
  Hebrew/LXX (e.g. `21:14` = Heb 22:13b/14; `36:24/25` the Ps 37 acrostic; `71:19` = the
  classic LXX Ps 71 colophon "Ended are the songs of David"). `data_action=no-data-change`,
  zero coords flagged as typos, high confidence, **not refuted**.
- **No shipped artifact is affected.** The only shipped surface that renders these stores
  is the **standalone Ge'ez Bible EPUB** via `scripts/build_standalone.py`, which is
  **occurrence-aware**: it reads the raw `VERSES` list in source order with `tx._load_book`
  and keys the EN back-translation by `(verse, occurrence)` — the verifier executed it and
  confirmed Ps 36 ships `v-psa-36-24` **and** `v-psa-36-24-2`, both distinct texts. The 9
  KJV editions carry no Ge'ez popups (`popup_versions.VERSION_REGISTRY` has no Ge'ez id),
  and every other `get_verse`/`get_chapter` consumer is provably blocked from the Ge'ez
  store or runs only on the `web.py` localhost dev console.
- **The defect is real but latent:** `translations._book_index_cached` builds
  `{(c, v): t}` (translations.py:155) → `get_verse()` drops `occ0` last-write-wins for an
  `own`-versification store; and `web_content.api_chapter` rebuilds a `{verse: text}` dict
  off `get_chapter` (web_content.py:116) → same collapse. Today this only manifests in the
  **localhost builder UI** (the parallel-column reader silently drops `occ0` on those 9
  Psalms verses); it is a **latent landmine** if a future edition ever wires a Ge'ez/`own`
  store as a shipped `popup_translation`.
- **Remediation (WIN, low priority):** make the dev-console consumer occurrence-preserving
  (don't collapse `get_chapter` rows into a `{v:t}` dict in `web_content.api_chapter`), and
  document the `own`-store `get_verse` constraint. The **durable guardrail is already in
  place** — `audit_translation_integrity.py` now permanently WARNs on any `own`-store
  dup-coord, so a future Ge'ez-popup wiring gets a heads-up.

### DV2 — `coord_in_canonical_extent` wrong for non-1-start books — ✅ FIXED (`5bac50d5`)

The `kjv` store's `aes` (Additions to Esther) carries verses **10:11, 10:12, 10:13** — the
KJV-Apocrypha numbers Esther-Additions ch10 as verses **4–13** (continuing from canonical
Esther 10:3). `coord_in_canonical_extent` modeled the extent as `1 <= v <= count` (count =
10), so it **wrongly rejected** legitimate `aes 10:11/12/13` (the promote-boundary guard
would drop any future ingest there) and **wrongly accepted** impossible `aes 10:1/2/3`
(ch10 starts at v4). (`_book_shape_cached` already handled the chapter-START case — `aes`
resolves to chapters 10..16; the residual defect was within-chapter verse numbering.)

**Fixed (Mac, `5bac50d5`, entirely within `canonical_verse_counts.py` — the off-limits
`manuscript_collation.load_kjv_skeleton` already returns full `(ch,verse,text)` rows):**
new `_book_verse_sets_cached` captures the ACTUAL verse numbers per chapter;
`_book_shape_cached` derives counts from it (the `canonical_book_shape` count contract is
unchanged); `coord_in_canonical_extent` tests true **membership**. **Proven byte-stable** —
across the whole skeleton, **1361 of 1362 chapters are exactly `{1..count}`**, so membership
≡ the old range check everywhere except `aes` 10 (wrong→right); no current store has `aes`
10:1-3 or notes at 10:11-13, so no live data changes today. TDD:
`tests/test_canonical_extent_membership.py` (red-first on the 2 `aes` cases + a
slow-tagged whole-skeleton byte-stability sweep); regression green
(`test_aes_notes_extent` · `test_canonical_verse_counts` · `test_promote_html_chapter_guard`
· `test_mint11_phase3`). *(No other non-1-start folded addition exists in the skeleton —
the whole-skeleton sweep confirmed `aes` 10 is the sole case.)*

### DV3 — `VERSIFICATION="own"` under-applied to the Tewahedo translation stores (classification)

The `own` flag (which tells consumers "these coords are source numbering, not KJV") is set
on only the **8 marathon files** (`psa/1sa/2sa/1ki` × `geez-tewahedo` + `geez-tewahedo-en`).
But the **entire Amharic Tewahedo Psalter** (747 LXX-numbered verse-overflow coords) and
Ge'ez `2es` (71, the 4 Ezra 7 long recension) also carry non-KJV numbering **undeclared** →
`versification_of()` defaults them to `"canonical"`. Mostly latent (no current consumer
range-checks/renumbers these stores), but a genuine metadata-classification gap.

**Disposition: merge triage, not a unilateral Mac change** — adding `VERSIFICATION="own"`
to faith-content stores touches scripture-adjacent data and could shift consumer behavior;
the auditor's per-store `INFO nonkjv-versification` rollup keeps it visible for the joint
merge to decide.

### DV4 — Tewahedo store-stem aliases (`ex→exo`, `1k`, `2k`) are scattered, not centralized (`book_code_canonical` class)

Four Tewahedo stores name Exodus `ex.py` (`geez-tewahedo`, `geez-tewahedo-en`,
`amharic-tewahedo`, `amharic-tewahedo-en`); the canonical stem is `exo`. **The deeper
finding (on investigation): `ex→exo` is a *deliberate but decentralized* convention** —
the `ex→exo` / `1k→1ki` / `2k→2ki` store-stem mapping already lives in **5 separate local
maps** (`scripts/core/sources_lexicon.py:448`, `scripts/link_xrefs.py:45`,
`scripts/render_coverage.py:56`, `scripts/gen_website_progress.py:39`, + the reverse
`exo→ex` in `scripts/core/translations.py:43`), but is **absent from the central
`scripts/core/book_codes.BOOK_CODE_ALIASES`**. So any path that normalizes only through
`canonical_book_code` (e.g. `coord_in_canonical_extent` → `FileNotFoundError` → keep-all)
**silently skips validation** of these stores. Latent (Ge'ez/Amharic aren't wired as
popups). **Remediation = centralize (hold for the joint merge — cross-file, WIN's core):**
fold `ex/1k/2k` into `BOOK_CODE_ALIASES` and delegate the 5 local maps, carefully (the
reverse `translations.py` map is a canonical→store lookup — don't double-convert). The
auditor now permanently WARNs (`book-code-noshape`) so a new such stem can't slip in.

## What's Mac-owned vs handed to WIN

- **DONE (Mac, this session):** the reusable auditor (`dev/audit_translation_integrity.py`,
  green + selftest 13/13 + ruff-clean), this verified findings record, **and the DV2 fix
  (`5bac50d5`, TDD + byte-stable)** — the one true correctness defect, remediated.
- **Held for the joint merge (all low/latent):** DV1 dev-console occurrence-preserve
  (`web_content.py`; localhost-only, no shipped impact) · DV4 store-stem alias
  centralization (cross-file refactor of 5 maps) · **DV3** versification-declaration
  triage (sensitive faith-content metadata). None block a ship; the auditor WARNs keep
  all three permanently visible.
- **Suggested follow-up (WIN, `scripts/lint_rules.py`):** wire
  `audit_translation_integrity.audit_repo(...)` (fail on any `FAIL`) into the pre-commit
  lint so the data-validity invariant is enforced every commit, not just on demand.
