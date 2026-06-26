# Charter — DEEP AUDIT of the new build pipeline + the resulting EPUBs (Mac plans, in PLAN MODE)

> **User directive (2026-06-25, to the Mac lane):** *"Use **plan mode** to plan a very deep
> audit for the new way the program builds the epubs and the resulting epubs — for any error,
> redundancies, contradictions. Everything in the program or the product it creates."* The user
> explicitly wants to **see Mac use plan mode**, so the immediate deliverable is the **PLAN**, not
> the execution.

## ▶ What Mac does (process)

1. **Pull first** (the WIN lane is actively landing the build-pipeline OOM fix + the 158-verse
   re-split — both are PART of "the new way" you're auditing; plan against the latest HEAD).
2. **`EnterPlanMode`.** Research the build pipeline + the product, then write a complete deep-audit
   **program/plan** to the plan file. **`ExitPlanMode`** to present it for the user's approval.
   *Do not begin executing the audit until the user approves the plan* — the user wants to review
   the plan first (this is their first time driving plan mode here).
3. After approval, this becomes a `dev/audit/<name>-program-*.md` program doc and runs as the next
   autonomous two-lane round (Mac read-only/structural/semantic dims; WIN owns build-path fixes),
   adversarially verified, loop-until-green — same shape as the round-10/11/13 + kobo-deep-audit
   programs (`dev/audit/kobo-deep-audit-program-2026-06-24.md` is the template).

## ▶ Scope — TWO targets, THREE lenses

The user named three lenses — **ERRORS · REDUNDANCIES · CONTRADICTIONS** — over **everything in
the program AND the product**. The plan must cover both targets under all three lenses.

### TARGET A — the PROGRAM (how it now builds the epubs)

The build pipeline was substantially re-architected in the last weeks; the audit must scrutinize the
**new** machinery, not just the legacy code. Key new/changed surfaces in `scripts/build_edition.py`
(+ `scripts/build_standalone.py`, `scripts/build_epub.py`) to audit:

- **Page-break re-architecture (eink):** `_merge_scripture_base_files` (per-book base-file merge),
  `_merge_mid_verse_breaks` (WS1 mid-verse re-join), `FILE_SPLIT_CEILING` (8 MB per-book sharding),
  the `_VN_LINK_RE`-removal packer change, `pack_book_chapters` (standalone per-book merge, Part 2b).
- **The file-split pipeline `apply_file_split`:** merge → mid-verse-merge → per-file split →
  cross-file opener pop → idmap scan → link rewrite → OPF/nav/ncx regen → study-glossary nav patch.
  Order-of-operations hazards, the eink-only branches, the byte-stability gating.
- **The eink study-backmatter glossary:** generation (`apply_badge_markers` entries →
  `inject_eink_study_backmatter` → the ~480 MB `index_split_900` monolith) + the split
  (`_iter_study_glossary_pieces` / **the NEW streaming `_iter_study_glossary_pieces_from_file`** /
  `_group_glossary_atoms` / `_study_glossary_chunk_atoms`).
- **OOM / memory management (NEW this session — pull for it):** the per-book bytes-streaming glossary
  split, the `badge_stats.pop` entries-list free, the tier-1 frees (`del pre_badge_texts` /
  `del repair_texts`). Audit for: correctness of the free-after-use claims, any *behavioral* drift
  vs the str path, and remaining peak-memory sites (Mac's `dev/audit/flagship-eink-oom-profile.md`).
- **WS2 note-cascade de-dup:** `_emit_cascade_sections` (leaf `note-sym` drop),
  `_strip_redundant_body_boilerplate` (xref / text-witness lead-in strip), the s1_dedup gating.
- **WS3 eink popup separators:** `_VN_SEP_{ITEM,CAT,BYLINE}_EINK`, `br.kobo-vn-br`, the kw-only
  `eink` threading through the cascade / badge / chunk / budget-pack / backmatter chains.
- **Eink font fixes:** the `!important` `font-family` rules for `.vnote-hebrew/greek/greek-nt/geez/
  amharic` in `_EINK_READER_CSS`.
- **The 158-verse WEB re-split (WIN landing it now):** the versification re-baseline of
  `epub_working/` — audit that it moved ONLY the 158 boundaries, changed no wording, and that every
  `#frag` still resolves across all editions.

**Program lenses:**
- **ERRORS** — bugs, off-by-ones, edge cases (empty inputs, single-book editions, canon-filtered
  editions, the standalone path), order-of-operations hazards, eink-gating *leaks* (a change meant
  to be eink-only that mutates the 9-KJV/tablet/default base), determinism breaks.
- **REDUNDANCIES** — duplicate passes over the same files, redundant `read_text`/`write_text`
  cycles, dead code paths, superseded helpers left behind, the same data computed twice, overlapping
  responsibilities between functions.
- **CONTRADICTIONS** — gates/auditors that disagree with the emitter, docstrings/comments that no
  longer match the code (e.g. the stale "73 MB" glossary figure), byte-stability *claims* vs reality
  (no KJV golden hash exists → claims must be proven by regen+diff), two passes that fight each other
  (one adds what another strips), config that contradicts the resolver.

### TARGET B — the PRODUCT (the resulting epubs)

Audit the **FINAL rendered epubs** — built fresh from HEAD, every **edition × format ×
reader-target** (the 4 study editions + the 9-KJV set + the 2 standalones; default / tablet / eink /
kindle targets). Not just the code — the actual zipped artifacts and their on-device behavior.

**Product lenses (dimensions):**
- **Structural integrity** — verse→chapter→book→out-of-book completeness per edition × format
  (`dev/audit_book_structure.py`); no dropped/duplicated/misordered verses; canon-filter edge cases
  (catholic-study splice).
- **Spine / page-breaks** — `dev/audit_spine_breaks.py`: 0 mid-chapter, breaks only at book titles;
  per-book merge held; standalones.
- **Verse-body formatting** — `dev/audit_verse_formatting.py`: 0 narrative mid-verse breaks, the
  empty-verse-anchor class (post re-split should be ~0 protocanon), stray ¶, badge-trail.
- **Popups / footnotes** — `dev/audit_popup_formula.py` + a semantic pass: same-file `#frag`
  contract, native-popup integrity, the eink run-on separators, the vnote U+2028 sibling (guard #7).
- **Note redundancy / contradiction** — the WS2 cascade: zero repeated category/byline/symbol/xref;
  no contradictory note bodies; broken markup.
- **Cross-file links / nav** — every `href`/`#frag` resolves to the piece that holds the id; nav.xhtml
  + toc.ncx well-formed, in spine order; study-glossary nested ToC.
- **Validity & fonts** — epubcheck 0/0/0/0 every artifact; embedded fonts present + referenced;
  original-language glyphs not tofu.
- **Byte-stability invariants** — the 9-KJV byte-stable set unchanged by any eink-gated change;
  matrix==build; prove by regen+`git diff`, NOT by assertion (no KJV golden hash exists).
- **Data validity / translation integrity** — `dev/audit_translation_integrity.py`: book-code
  canonicalization, versification declarations, no silent note drops.

## ▶ Infrastructure to leverage / extend (don't rebuild from scratch)

- **The engine:** `.claude/workflows/deep-audit.js` (run via `Workflow({scriptPath})`; round-8+ scope
  = project code/product ONLY; args don't propagate → edit DEFAULTS in-file; **run on the strongest
  model — never Sonnet**, StructuredOutput skips → false negatives).
- **Deterministic auditors:** `audit_book_structure.py` · `audit_spine_breaks.py` ·
  `audit_verse_formatting.py` · `audit_popup_formula.py` · `audit_translation_integrity.py`.
- **History/method:** rounds 10/11/13 (`dev/audit/round1*-*.md`), the kobo-deep-audit program,
  `dev/MATRIX_MAP.md` (data-flow/integrity map), `dev/audit/flagship-eink-oom-profile.md`.
- **Gates:** the byte-stability gate, `test_nested_anchors`, `ALL_CHECKS`, epubcheck (`--jar`).

## ▶ What the PLAN should contain (so the user can approve it)

1. **Dimensions** — the concrete audit dimensions for TARGET A (program) and TARGET B (product),
   each tagged ERROR / REDUNDANCY / CONTRADICTION, with the specific finder (deterministic auditor,
   `deep-audit.js` dim, or a multi-agent semantic pass) and the file/area it covers.
2. **Lane split** — which dimensions Mac runs (read-only code analysis, the structural/product epub
   audits on freshly-built macOS artifacts, semantic note/popup passes) vs which WIN owns (build-path
   fixes, byte-stability proofs, device builds). File-disjoint, parallel mode.
3. **Method per dimension** — deterministic finder where possible; multi-agent semantic pass
   (adversarially verified — N independent skeptics per finding, refute-by-default) where judgment is
   needed; how findings are recorded (`dev/audit/<round>-{survivors,plan}.md`).
4. **Loop-until-green protocol** — remediate everything surfaced (TDD + byte-stability proof on any
   build-path touch), loop until all dims clean + structural all-green + suite green + a clean device
   eyeball. Same "neither lane stops till the fixing is done" shape as prior programs.
5. **Scale** — this is "very deep / everything", so plan a large finder pool + 3–5-vote adversarial
   verification + a completeness critic ("what modality/claim/area is unaudited?").

## ▶ Coordination

- Parallel mode, file-disjoint; WIN (truth_owner) is concurrently landing the OOM fix + re-split +
  the Kobo device re-stage — **do not touch `scripts/build_edition.py` or `epub_working/`** while
  planning; the plan is `dev/audit/` + macOS builds.
- Present the plan via `ExitPlanMode` → user approves → it becomes the program doc → execute.
- Adversarially verify; record human-only needs in `dev/HUMAN_DECISIONS.md`.
