# mint-7 — Quality Pass (correctness · code-debt · security · tests/hygiene)
**Status:** in progress — audit COMPLETE (2026-05-31, 15-agent workflow `wf_365eda78`); plan written + findings saved; **execution PENDING (start Phase A next session)**.

> Source audit: 6-dimension multi-agent audit of the post-mint-cleanup tree, each
> critical/high finding independently verified. Raw findings (with verifier
> reasoning + severity recalibrations): `docs/superpowers/2026-05-31-mint-7-audit-findings.md`.
> Successor to the mint-cleanup arc (Phases 0–6, COMPLETE). User scoped mint-7 as
> "all of them" — correctness + code-quality + the audit's new security/test/doc findings.

## Guiding constraints (every task)
- **No deadline / quality over speed.** Pick the most complete + correct path.
- **NEVER touch the Geʽez marathon core** (`build_standalone.py`, `core/manuscript_*`,
  `core/po_vision_store.py`, `content/manuscript/**`, `patrologia/**`, `GAPS/`).
- **9 KJV editions stay byte-stable**; additive schema only; atomic writes via `notes_io`.
- **TDD where it fits**; prove safety: `$env:PYTHONUTF8="1"; pytest` (relevant scope) +
  for any build-touching change the byte-compat invariant (regen + empty `git diff
  epub_working/` + flagship epubcheck 0/0/0/0).
- **Save = full 5-leg sync** (RULES §4 / `save-all.ps1`) at each phase close.
- **Use the verifier-CORRECTED fixes below**, not the raw finding's first-draft fix
  (several first-draft fixes were wrong — noted inline).

---

## Phase A — ★ Book-code BUGCLUSTER (the correctness lead; the ★ from MEMORY `feedback_book_code_canonical`)

The verifiers confirmed the cluster but **corrected the impact model**: the canonical
notes ARE already promoted (Nave's was rebuilt clean 2026-05-09→13); the legacy-coded
candidate files on disk are **stale duplicates**, and the live gap is **TSK** (whose
JSON was never rebuilt) + several **latent** detector maps that would silently drop
notes the moment new content is prospected.

- [ ] **A1 — Complete the central `_normalize_book_code`.** In `scripts/core/sources_base.py`
  `_BOOK_CODE_ALIASES` (currently only joh→jhn, ps→psa, jas→jam) add the 4–5 missing
  real legacy codes: `mar→mrk, jol→joe, ezk→eze, nam→nah, php→phi` (mirror
  `extract_torrey_ccel._LEGACY_TO_CANON`, the canonical 8-entry list). Delete the stale
  `_BOOK_CODE_ALIASES_LONGFORM` comment (sources_base.py:59 — references a dict that
  doesn't exist). **Effort S.**
- [ ] **A2 — Fix the source-of-truth maps to emit canonical codes.**
  - `scripts/fetch_sources.py` `TSK_BOOK_REMAP` (~:153): `Ezek→eze, Joel→joe, Nah→nah,
    Phil→phi, Jas→jam` (also inherited by `NAVES_BOOK_REMAP`). Then **rebuild**
    `tsk_xrefs.json` (`python scripts/fetch_sources.py --force tsk`). This is the one
    LIVE gap: ~1,525 TSK xrefs across ezk/jol/nam/php/jas are currently unreachable via
    canonical lookup (mirrors the fix already done for Nave's). **HIGH. Effort M.**
  - `scripts/core/sources_lexicon.py` `KENYON_BOOK_NAME_TO_CODE`: `joel→joe` (:485),
    `phil/philippians→phi` (:525-526), `jas/james→jam` (:545-546). Latent (no Kenyon
    Joel/Phil/James candidates on disk yet). **Effort S.**
  - **⚠ DO NOT** add `_normalize_book_code(book)` *inside* `Tsk.refs_for()` — the TSK
    DATA is legacy-keyed, so normalizing the QUERY (ezk→eze) returns 0 results. Fix the
    data/map, not the query. (This was the raw finding's wrong first-draft fix.)
- [ ] **A3 — Normalize at detector/driver boundaries (defense-in-depth).**
  `CrossRefDetector.detect()` (detectors.py:464) normalize `target_book` before building
  `href="#vnote-{target_book}-..."`. At-scale drivers (`run_xref/naves/torrey_at_scale.py`)
  apply `_normalize_book_code` to the book list iterated from source-JSON keys. **Effort S.**
- [ ] **A4 — Delete the stale legacy-coded candidate files** (NOT migrate — `eze_ch_*` etc.
  already exist; renaming would collide). Remove the 56 git-tracked `ezk_ch_*.json` (incl.
  the impossible `ezk_ch_081`), `jol_ch_*.json`, `nam_ch_*.json` under `content/candidates/`.
  Optionally add a coord-validity sweep for the other out-of-extent OCR artifacts
  (deu_ch_081/082/097, num_ch_08x, isa_ch_080-087, jer_ch_082-087, …). **Effort S.**
- [ ] **A5 — Guard it (TDD).** Meta-test: every value in `KENYON_BOOK_NAME_TO_CODE`,
  `TSK_BOOK_REMAP`, and the other book-name maps is in `config.books_by_code()` AND has a
  `content/notes/<code>.py` file (strengthen `test_scripts.py:8328` which only spot-checks
  9 codes). Consider a `lint_rules` check `bookcode_canonical` so the BUGCLUSTER can never
  silently return. **Effort M.**

## Phase B — At-scale coverage + integrity
- [ ] **B1 — AI at-scale chapter cap.** `run_ai_xrefs_at_scale.py:155` + `run_ai_notes_at_scale.py:156`
  use `book_meta.get("chapters", 50)` — `books.yaml` key is `ch_count`, so it ALWAYS
  returns 50, silently skipping Psalms 51-150, Isaiah 51-66, Jeremiah 51-52, Sirach 51-65,
  1 Enoch 51-108, etc. Change to `ch_count` (one line each; siblings hebrew/greek are
  correct). Verify with `--books psa --dry-run` → 150 chapters. **HIGH. Effort S.**
  (NOTE: re-running the AI content at scale to actually fill the gap is a SEPARATE,
  possibly-metered content run — flag it; the code fix is what mint-7 ships.)
- [ ] **B2 — `run_xref_at_scale.py` write_queue overwrites** (:62-77) — the lone driver of 9
  that clobbers instead of append-merges, silently deleting other drivers' pending
  candidates + resetting ids. Copy the naves/torrey append-merge pattern (~15 lines). **Effort S.**

## Phase C — Security (single-user LOCAL app; integrity/secret focus)
- [ ] **C1 — Stored XSS in `/api/sample/`.** `web_content.py:366-369` (`_render_sample_html`)
  interpolates the note body verbatim; `_send_html` then noncifies every `<script>`,
  so an injected `<script>` from a note body gets a valid CSP nonce and executes. Wrap:
  `body = sanitize_html(str(n[7] or ""))` (mirror `preview.py:133-135`). **HIGH. Effort S.**
- [ ] **C2 — `content/auth.json` not gitignored.** Stores the enrolled TOTP base32 secret;
  `save.ps1`'s `git add -A` would commit it on first 2FA enrollment. Add `content/auth.json`
  (and for consistency `content/distribution.json`, `content/press_kit.json` runtime-state)
  to `.gitignore`. **Effort S.**
- [ ] **C3 — Build-All ZIP undownloadable.** `api_download_export` (exports.py:406) regex
  only allows `Ethiopian_Bible_*.epub`; the combined zip is `All_Editions_*.zip` → every
  download 400s. Add the zip shape to the allowlist. **Effort S.**

## Phase D — Code-debt + dead code
- [ ] **D1 — `scripts/core/at_scale_base.py`** — extract the 10× copy-pasted `candidate_to_dict`,
  the 4× `NT_BOOKS` set, the 9× ANSI color constants; import in all drivers + `prospect.py`
  + `detectors.py`. write_queue stays per-driver (intentionally different). **Effort M.**
- [ ] **D2 — Legacy error paths bypass `_send_json`.** `web.py:1678` (/api/sample/ error) +
  :1701 (/api/backups error) skip Content-Length + security headers; replace with `_send_json`. **S.**
- [ ] **D3 — Dead code.** Archive `scripts/_split_web_html.py` → `dev/archive/` (split done,
  flagged 2026-05-23); delete orphaned `apply_style._chapter_label` (:434) + `bulk_inject.find_template_files`
  (:241) (0 call sites); WIRE the built-but-uninvoked `_replace_verse_popup_translation`
  (build_edition.py:600, 5 tests, no caller) as a builder option OR mark not-yet-wired;
  wire the `ebible audit` aggregator (audit_caches/dead_code/types/deps) into `scripts/ci.py`
  / `.gitlab-ci.yml` (currently only audit_caches reaches preflight). **S–M.**
- [ ] **D4 — `catholic_commentaries.json` 'mar'** — fixed by A1 (`mar→mrk` alias); 2 Catena
  entries (Bede/Gregory on Mark) currently silent-drop on prospect. Verify after A1. **S.**

## Phase E — Tests + doc/data hygiene
- [ ] **E1 — Lint-check meta-test.** 8 of 26 `ALL_CHECKS` have no unit test (encode_decode,
  encoder_canonical_order, provenance_tier, render_coverage, ephemeral_doc_pins,
  plan_coherence, freshness, manuscript_witnesses). Add a meta-test iterating `ALL_CHECKS`
  + targeted tests for the correctness-critical ones. **M.**
- [ ] **E2 — Slow-test hygiene.** Add a `slow` marker; tag `test_web_filesplit.py` +
  `test_matrix_psi35.py` (~23 min each); session-scope `compute_matrix()` (called 10× uncached
  in psi35); apply-or-remove the dead `serial` marker (pyproject.toml:153). **M.**
- [ ] **E3 — Golden byte-stability gate** for the 9 KJV editions (build all 9, assert a golden
  content hash; behind the `slow` marker). Closes the gap that nothing currently pins the
  byte-stable invariant the whole project leans on. **L.**
- [ ] **E4 — Doc fixes.** `dev/ROADMAP_FUTURE.md:75` archive-path (`SCOPE_2026-05-08…` →
  `dev/archive/…`); `dev/PROPOSAL_FEATURE_LANDSCAPE.md` + `marathon_reviews/README.md` stale
  `PLAN_2026-05-09/21/24` refs → the live roadmap (or archive pointer). Optional CHANGELOG
  month-roll (38,530 lines; WARN-only, not blocking). **S–M.**

---

## Suggested order
A (correctness/bugcluster) → C (security, cheap+important) → B (at-scale) → D (debt) → E
(tests/doc). Save (5-leg) at each phase close; back up E:/F: every 3rd commit (automatic
via `save-all.ps1`). Verify byte-stability after anything touching detectors/promote/build.

## Severity ledger (verifier-calibrated)
- **HIGH:** TSK rebuild (A2), AI ch_count (B1), stored-XSS (C1).
- **MEDIUM:** Kenyon map (A2), `mar` alias (A1/D4), run_xref append (B2), auth.json gitignore
  (C2), Build-All zip (C3), legacy `_send_json` (D2), at_scale_base (D1), verse-popup-swap +
  ebible-audit wiring (D3), lint meta-test (E1), slow markers (E2), golden gate (E3).
- **LOW:** stale candidate files (A4 — zero content impact, hygiene only), orphaned helpers
  (D3), stale comments (A1/E4), `serial` marker (E2).
