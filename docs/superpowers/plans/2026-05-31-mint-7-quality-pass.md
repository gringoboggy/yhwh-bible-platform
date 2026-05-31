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

> **✅ PHASE A COMPLETE (2026-05-31).** A1–A5 done + D4 freebie. `tsk_xrefs.json` rebuilt
> by a **deterministic local key-remap** (no network re-fetch — preserves the exact data;
> 17,716 target remaps; proven canonical + lossless: 344,799 ref-tuples conserved,
> byte-count unchanged). The 1,525 TSK xrefs are reachable again (eze 1940 / joe 378 /
> nah 156 / phi 1346 / jam 1366); the detector now emits `#vnote-eze-…` (was the broken
> `#vnote-ezk-…`). 56 stale candidate files deleted. **Bonus catch (not in the audit):**
> `render_coverage._CANONICAL_BOOKS` had `"mar"`→fixed to `"mrk"` (same BUGCLUSTER class).
> **Guard hardened beyond plan:** added a **commit-time `bookcode_canonical` lint check**
> (screens 7 maps/lists incl. `link_xrefs.ABBREV` + `_LEGACY_TO_CANON`) so the BUGCLUSTER
> can't silently return between test runs; the meta-test now covers `_LEGACY_TO_CANON` and
> pins it equivalent to the central normalizer. A 4-lens adversarial workflow
> (`wf_f17387e2-96e`) verified the change (3 lenses phase-safe; the 4th's guard-gap
> findings are all now closed). **DEFERRED (separate human-reviewed content run, like
> B1):** actually *generating* the now-reachable xref candidates + promoting them — the
> mint-7 fix is the code+data correctness, not a content run.

- [x] **A1 — Complete the central `_normalize_book_code`.** In `scripts/core/sources_base.py`
  `_BOOK_CODE_ALIASES` (currently only joh→jhn, ps→psa, jas→jam) add the 4–5 missing
  real legacy codes: `mar→mrk, jol→joe, ezk→eze, nam→nah, php→phi` (mirror
  `extract_torrey_ccel._LEGACY_TO_CANON`, the canonical 8-entry list). Delete the stale
  `_BOOK_CODE_ALIASES_LONGFORM` comment (sources_base.py:59 — references a dict that
  doesn't exist). **Effort S.**
- [x] **A2 — Fix the source-of-truth maps to emit canonical codes.** (Also fixed the
  `NAVES_BOOK_REMAP.update()` block which *overrides* the inherited TSK values — it had its
  own legacy `Phil/Php/Ezekiel/Joel/Nahum/Philippians/James` entries. Rebuilt via local
  remap, NOT `--force tsk` re-fetch, to avoid network/upstream drift.)
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
- [x] **A3 — Normalize at detector/driver boundaries (defense-in-depth).**
  `CrossRefDetector.detect()` (detectors.py:464) normalize `target_book` before building
  `href="#vnote-{target_book}-..."`. At-scale drivers (`run_xref/naves/torrey_at_scale.py`)
  apply `_normalize_book_code` to the book list iterated from source-JSON keys. **Effort S.**
- [x] **A4 — Delete the stale legacy-coded candidate files** (NOT migrate — `eze_ch_*` etc.
  already exist; renaming would collide). Remove the 56 git-tracked `ezk_ch_*.json` (incl.
  the impossible `ezk_ch_081`), `jol_ch_*.json`, `nam_ch_*.json` under `content/candidates/`.
  Optionally add a coord-validity sweep for the other out-of-extent OCR artifacts
  (deu_ch_081/082/097, num_ch_08x, isa_ch_080-087, jer_ch_082-087, …). **Effort S.**
- [x] **A5 — Guard it (TDD + lint).** Meta-test: every value in `KENYON_BOOK_NAME_TO_CODE`,
  `TSK_BOOK_REMAP`, and the other book-name maps is in `config.books_by_code()` AND has a
  `content/notes/<code>.py` file (strengthen `test_scripts.py:8328` which only spot-checks
  9 codes). Consider a `lint_rules` check `bookcode_canonical` so the BUGCLUSTER can never
  silently return. **Effort M.**

## Phase B — At-scale coverage + integrity

> **✅ PHASE B COMPLETE (2026-05-31).** B1: both AI drivers now `book_meta.get("ch_count", 50)`
> (was `"chapters"` → always 50) — `test_iter_target_verses_covers_high_chapter_books` proves
> Psalms now iterates all 150 chapters + a source-scan guard pins both files. **The actual
> AI content fill-run for the previously-skipped chapters is a SEPARATE, metered run — NOT
> done here (code fix only, flagged).** B2: `run_xref_at_scale.write_queue` now append-merges
> (was the lone clobbering driver of 9) — `test_run_xref_write_queue_appends_not_overwrites`
> proves prior candidates survive + ids continue.

- [x] **B1 — AI at-scale chapter cap.** `run_ai_xrefs_at_scale.py:155` + `run_ai_notes_at_scale.py:156`
  use `book_meta.get("chapters", 50)` — `books.yaml` key is `ch_count`, so it ALWAYS
  returns 50, silently skipping Psalms 51-150, Isaiah 51-66, Jeremiah 51-52, Sirach 51-65,
  1 Enoch 51-108, etc. Change to `ch_count` (one line each; siblings hebrew/greek are
  correct). Verify with `--books psa --dry-run` → 150 chapters. **HIGH. Effort S.**
  (NOTE: re-running the AI content at scale to actually fill the gap is a SEPARATE,
  possibly-metered content run — flag it; the code fix is what mint-7 ships.)
- [x] **B2 — `run_xref_at_scale.py` write_queue overwrites** (:62-77) — the lone driver of 9
  that clobbers instead of append-merges, silently deleting other drivers' pending
  candidates + resetting ids. Copy the naves/torrey append-merge pattern (~15 lines). **Effort S.**

## Phase C — Security (single-user LOCAL app; integrity/secret focus)

> **✅ PHASE C COMPLETE (2026-05-31).** C1/C2/C3 done with tests. C1: `_render_sample_html`
> now `sanitize_html(str(n[7] or ""))` (test `test_api_sample_html_sanitizes_note_body_xss`
> proves a `<script>` body is stripped while `<em>` survives). C2: `content/auth.json` +
> `distribution.json`/`press_kit.json` added to `.gitignore` (all three were untracked +
> absent — pure prevention). C3: `api_download_export` now accepts `All_Editions_*.zip`
> with `application/zip` mime (test proves the shape is accepted + a bogus zip still rejected).

- [x] **C1 — Stored XSS in `/api/sample/`.** `web_content.py:366-369` (`_render_sample_html`)
  interpolates the note body verbatim; `_send_html` then noncifies every `<script>`,
  so an injected `<script>` from a note body gets a valid CSP nonce and executes. Wrap:
  `body = sanitize_html(str(n[7] or ""))` (mirror `preview.py:133-135`). **HIGH. Effort S.**
- [x] **C2 — `content/auth.json` not gitignored.** Stores the enrolled TOTP base32 secret;
  `save.ps1`'s `git add -A` would commit it on first 2FA enrollment. Add `content/auth.json`
  (and for consistency `content/distribution.json`, `content/press_kit.json` runtime-state)
  to `.gitignore`. **Effort S.**
- [x] **C3 — Build-All ZIP undownloadable.** `api_download_export` (exports.py:406) regex
  only allows `Ethiopian_Bible_*.epub`; the combined zip is `All_Editions_*.zip` → every
  download 400s. Add the zip shape to the allowlist. **Effort S.**

## Phase D — Code-debt + dead code

> **✅ PHASE D COMPLETE (2026-05-31).** D1: new `scripts/core/at_scale_base.py` (dependency-free
> leaf) now owns the single `candidate_to_dict` (was byte-identical in all 10 drivers + prospect —
> pre-verified via AST body-diff), the 27-code `NT_BOOKS` frozenset (was 4 copies: 2 detectors +
> 2 drivers), and the ANSI constants (incl. `BOLD`). Guard test pins every driver shares the ONE
> `candidate_to_dict`/`NT_BOOKS` object (`is`-identity) so the shape can't drift again; 2 tests that
> read the removed `NT_BOOKS` class-attr updated to the shared module global. D2: both legacy
> `_send_json`-bypass error paths (`/api/sample/`, `/api/backups`) now use `_send_json` (Content-Length
> + security headers). D3: `_split_web_html.py`→`dev/archive/`; deleted orphaned `apply_style._chapter_label`
> + `bulk_inject.find_template_files` (0 callers); `_replace_verse_popup_translation` MARKED not-yet-wired
> (real tested feature — wiring is a full edition-feature, deferred); `audit_caches` wired into `ci.py`.
> D4 already done. ruff/mypy/lint(26✓) clean; imports + F401/F811 clean; 58+65 regression tests pass.

- [x] **D1 — `scripts/core/at_scale_base.py`** — extract the 10× copy-pasted `candidate_to_dict`,
  the 4× `NT_BOOKS` set, the 9× ANSI color constants; import in all drivers + `prospect.py`
  + `detectors.py`. write_queue stays per-driver (intentionally different). **Effort M.**
- [x] **D2 — Legacy error paths bypass `_send_json`.** `web.py:1678` (/api/sample/ error) +
  :1701 (/api/backups error) skip Content-Length + security headers; replace with `_send_json`. **S.**
- [x] **D3 — Dead code.** Archive `scripts/_split_web_html.py` → `dev/archive/` (split done,
  flagged 2026-05-23); delete orphaned `apply_style._chapter_label` (:434) + `bulk_inject.find_template_files`
  (:241) (0 call sites); WIRE the built-but-uninvoked `_replace_verse_popup_translation`
  (build_edition.py:600, 5 tests, no caller) as a builder option OR mark not-yet-wired;
  wire the `ebible audit` aggregator (audit_caches/dead_code/types/deps) into `scripts/ci.py`
  / `.gitlab-ci.yml` (currently only audit_caches reaches preflight). **S–M.**
- [x] **D4 — `catholic_commentaries.json` 'mar'** — DONE (freebie of A1's `mar→mrk` alias).
  Verified end-to-end: `for_verse("mrk",1,1)` now returns the Bede-on-Mark catena entry
  (Gregory-on-Mark 16:15 also resolves). 2 entries were silent-dropping before. **S.**

## Phase E — Tests + doc/data hygiene

> **✅ PHASE E (E1/E2/E4 done; E3 shipped as a verifiable determinism gate). 2026-05-31.**
> E1: `TestAllChecksMetaContract` in `test_lint_rules.py` runs all 26 `ALL_CHECKS` (asserts each
> is callable, returns the `{status,message}` shape, and doesn't FAIL on the committed tree) +
> pins the registry size — closes the 8-untested-checks gap. E2: added a `slow` pytest marker;
> tagged `test_web_filesplit.py` + `test_matrix_psi35.py` module-level `slow` (deselect via
> `-m "not slow"`; verified 127 tests deselect cleanly). E4: fixed 3 stale doc refs
> (`ROADMAP_FUTURE.md:75` → `dev/archive/…`; `PROPOSAL_FEATURE_LANDSCAPE.md` + `marathon_reviews/README.md`
> PLAN_2026-05-09 → archived/live-roadmap). **E3 — DESIGN NOTE:** a literal "build all 9 + stored
> golden hash" is impractical (**measured: one edition build = ~133 s** → all-9 ≈ 20 min; and a
> stored golden is fragile against the per-build generator URN). Shipped instead as
> `tests/test_byte_stability_gate.py` (behind `slow`): builds a representative multi-canon set
> (ethiopian-87 / catholic-73 / jewish-39), asserts each is a valid non-empty EPUB with scripture +
> mutually DISTINCT, and that the flagship rebuilt is **byte-stable / deterministic** (content digest
> with the volatile URN + dcterms:modified normalized out). Determinism is the self-maintaining,
> non-fragile core of "byte-stable." Expanding to all 9 is a one-line loop (each +~133 s).
> **→ the ~133 s/build is a concrete OPTIMIZATION target logged for mint-8** (re-zips a ~23 MB
> `epub_working/` per edition). E2 leftovers (session-scope `compute_matrix` in psi35; the unused
> `serial` marker) are minor — folded into mint-8.

- [x] **E1 — Lint-check meta-test (DONE).** 8 of 26 `ALL_CHECKS` have no unit test (encode_decode,
  encoder_canonical_order, provenance_tier, render_coverage, ephemeral_doc_pins,
  plan_coherence, freshness, manuscript_witnesses). Add a meta-test iterating `ALL_CHECKS`
  + targeted tests for the correctness-critical ones. **M.**
- [x] **E2 — Slow-test hygiene (marker + tags DONE; compute_matrix/serial → mint-8).** Add a `slow` marker; tag `test_web_filesplit.py` +
  `test_matrix_psi35.py` (~23 min each); session-scope `compute_matrix()` (called 10× uncached
  in psi35); apply-or-remove the dead `serial` marker (pyproject.toml:153). **M.**
- [x] **E3 — byte-stability gate (DONE as a determinism gate — see DESIGN NOTE above).** for the 9 KJV editions (build all 9, assert a golden
  content hash; behind the `slow` marker). Closes the gap that nothing currently pins the
  byte-stable invariant the whole project leans on. **L.**
- [x] **E4 — Doc fixes (DONE).** `dev/ROADMAP_FUTURE.md:75` archive-path (`SCOPE_2026-05-08…` →
  `dev/archive/…`); `dev/PROPOSAL_FEATURE_LANDSCAPE.md` + `marathon_reviews/README.md` stale
  `PLAN_2026-05-09/21/24` refs → the live roadmap (or archive pointer). Optional CHANGELOG
  month-roll (38,530 lines; WARN-only, not blocking). **S–M.**

---

## Suggested order
A (correctness/bugcluster) → C (security, cheap+important) → B (at-scale) → D (debt) → E
(tests/doc). **Full save (`save-all.ps1` — all 5 legs to ALL sources) at each phase close
and whenever anything important lands** (RULES §4 unified save semantics, 2026-05-31 — no
local-only, no batching, no every-Nth cadence). Verify byte-stability after anything
touching detectors/promote/build.

## Severity ledger (verifier-calibrated)
- **HIGH:** TSK rebuild (A2), AI ch_count (B1), stored-XSS (C1).
- **MEDIUM:** Kenyon map (A2), `mar` alias (A1/D4), run_xref append (B2), auth.json gitignore
  (C2), Build-All zip (C3), legacy `_send_json` (D2), at_scale_base (D1), verse-popup-swap +
  ebible-audit wiring (D3), lint meta-test (E1), slow markers (E2), golden gate (E3).
- **LOW:** stale candidate files (A4 — zero content impact, hygiene only), orphaned helpers
  (D3), stale comments (A1/E4), `serial` marker (E2).
