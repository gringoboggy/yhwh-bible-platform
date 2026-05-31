# mint-8 deep-audit — Round 1 findings

**Status:** Round-1 audit COMPLETE (record/reference). Actionable plan → `../plans/2026-05-31-mint-8-fixes-plan.md`. Convergence loop: fix → re-audit until a round returns zero new verified findings.

> **Generated 2026-05-31** by the reusable engine `.claude/workflows/deep-audit.js` (depth=deep, 14 dimensions).
> Run: **106 agents · ~4.80M subagent tokens · ~3.25 h** (`wf_1b2fdc14-4fd`). The `args` override did not propagate, so it ran the full default dimension set — which was the intent anyway.
> **70 deduped findings → 57 verified survivors / 13 refuted.** Each finding was independently refuted by adversarial skeptic panels (default-to-refuted; critical=3 / high=2 / else=1 skeptics); only survivors are actionable.
> Severity (calibrated): high 6 · medium 20 · low 26 · info 5.
>
> **Companion:** `../plans/2026-05-31-mint-8-fixes-plan.md` (the phased plan to execute next session) · raw JSON: `2026-05-31-mint-8-audit-raw.json` (same dir).

## Survivor index (bug/correctness/security/debt/test/doc)

| # | Sev | Dimension | Title | Location |
|---|-----|-----------|-------|----------|
| 1 | HIGH | byte-stability | Wall-clock date embedded in every edition OPF via _resolve_publishing defaults | `YHWH v2.4/scripts/epub_utils.py:29-37` |
| 2 | HIGH | concurrency-caching | scripts/api/exports.py subprocess.run missing stdin=subprocess.DEVNULL — WinError 6 in production HTTP build endpoint | `YHWH v2.4/scripts/api/exports.py:197` |
| 3 | HIGH | correctness | find_aside_insertion_point regex `(\d{2})(\d{2})` cannot parse aside IDs for chapters >= 100 (1 Enoch chapters 100-108, Strategy-A …[clipped] | `YHWH v2.4/scripts/inject.py:606-608` |
| 4 | HIGH | correctness | write_book serialises attribution as {} (empty dict) instead of omitting the 9th field, corrupting the notes schema | `YHWH v2.4/scripts/web_helpers.py:131, 146, 174, 182` |
| 5 | HIGH | data-validity | Exodus translation data unreachable: all 4 Tewahedo stores use non-canonical filename `ex.py` instead of `exo.py` | `YHWH v2.4/content/translations/amharic-tewahedo/ex.py:1` |
| 6 | HIGH | tests | test_amharic_tewahedo_contains_gen_py is dead — def keyword buried inside a comment | `YHWH v2.4/tests/test_parallel_bible_tau6x1.py:834` |
| 7 | MEDIUM | byte-stability | ebible build pipeline omits check_nested_anchors guard after inject mutates epub_working/ | `YHWH v2.4/scripts/ebible.py:227-255` |
| 8 | MEDIUM | byte-stability | _resolve_publishing injects wall-clock date into OPF <dc:date>, breaking build reproducibility and poisoning the content-addressab …[clipped] | `YHWH v2.4/scripts/epub_utils.py:29-30` |
| 9 | MEDIUM | concurrency-caching | translations._book_index caches stale verse-lookup dict, bypassing mtime-keyed freshness of _load_book_cached | `YHWH v2.4/scripts/core/translations.py:120-128` |
| 10 | MEDIUM | concurrency-caching | scripts/build_edition.py subprocess.run for build_epub.py missing stdin=subprocess.DEVNULL — WinError 6 in dev build path | `YHWH v2.4/scripts/build_edition.py:3022-3033` |
| 11 | MEDIUM | correctness | find_aside_insertion_point treats higher-chapter asides as 'preceding', misorders re-injected notes in Strategy-B sections | `YHWH v2.4/scripts/inject.py:621` |
| 12 | MEDIUM | correctness | batch_insert_notes silently drops all inserts on SyntaxError in the generated output without informing the caller | `YHWH v2.4/scripts/promote.py:368-373` |
| 13 | MEDIUM | cross-module | edition_canon_books sorted alphabetically — violates RULES §6.1 canonical order (affects 3 UI dropdowns) | `YHWH v2.4/scripts/web_editions.py:335` |
| 14 | MEDIUM | data-validity | `aes` notes at KJV chapters 11-16 (roughly 70 notes) are permanently uninjectable: base HTML only has chapter anchors 1-10 | `YHWH v2.4/content/notes/aes.py:204-919` |
| 15 | MEDIUM | docs | ALL_CHECKS registry is 27 checks but every doc/test says 26 | `YHWH v2.4/tests/test_lint_rules.py:15, 37-38` |
| 16 | MEDIUM | docs | Mint-cleanup plan status still says 'Phase 6 active'; arc is COMPLETE | `YHWH v2.4/docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md:2` |
| 17 | MEDIUM | security | RSS feed: note body_html injected raw into CDATA — stored XSS + XML injection | `YHWH v2.4/scripts/core/verse_of_day.py:328-336` |
| 18 | MEDIUM | security | Stored-XSS in /sources console: truncateHTML returns raw note body HTML when ≤240 stripped chars | `YHWH v2.4/scripts/templates/sources.py:592-596` |
| 19 | MEDIUM | security | RSS feed embeds unsanitized note body_html inside CDATA description block | `YHWH v2.4/scripts/core/verse_of_day.py:328-336` |
| 20 | MEDIUM | tests | test_by_verse_empty_for_unknown assumes mat 1:1 has no patristic commentary (state-default violation, §8) | `YHWH v2.4/tests/test_patristic_gamma3.py:134-140` |
| 21 | LOW | byte-stability | build_cache.compute_cache_key omits epub_working/META-INF/ subdirectory from its hash, so container.xml changes do not invalidate  …[clipped] | `YHWH v2.4/scripts/core/build_cache.py:239-248` |
| 22 | LOW | code-debt | iter_target_verses and resolve_books duplicated byte-for-byte across both AI at-scale drivers | `YHWH v2.4/scripts/run_ai_notes_at_scale.py:117-147, 298-305` |
| 23 | LOW | concurrency-caching | scripts/bulk_edit.py auto-verify subprocess.run missing stdin=subprocess.DEVNULL — WinError 6 on Windows | `YHWH v2.4/scripts/bulk_edit.py:189-192` |
| 24 | LOW | correctness | promote.py batch_insert_notes breaks sort order for notes at the same chapter/verse when existing list is not in sorted order | `YHWH v2.4/scripts/promote.py:339-343` |
| 25 | LOW | correctness | write_book always emits 9th attribution field as `{}` for legacy 8-tuple notes, converting them to 9-tuples with a dict value that …[clipped] | `YHWH v2.4/scripts/web_helpers.py:174` |
| 26 | LOW | correctness | prospect.py and all run_*_at_scale.py write_queue functions use non-atomic writes for candidate JSON files | `YHWH v2.4/scripts/prospect.py:152` |
| 27 | LOW | correctness | batch_insert_notes silently drops notes whose chapter/verse key is absent from the input dict | `YHWH v2.4/scripts/promote.py:325-330` |
| 28 | LOW | data-validity | `add_note.py` chapter-range guard uses `books.yaml ch_count` instead of `coord_in_canonical_extent`, causing wrong accept/reject f …[clipped] | `YHWH v2.4/scripts/add_note.py:309-310` |
| 29 | LOW | data-validity | `books.yaml` `ch_count: 10` for `aes` is misleading: actual HTML has 10 chapters (1-10) but KJV skeleton has 7 chapters (10-16), c …[clipped] | `YHWH v2.4/content/books.yaml:296-302` |
| 30 | LOW | docs | MATRIX_MAP and REPO_MAP say 71 kinds; actual kinds.yaml has 72 | `YHWH v2.4/dev/MATRIX_MAP.md:17, 27, 133` |
| 31 | LOW | docs | Mint-7 plan status says 'execution PENDING' but it is COMPLETE; INDEX puts it in 'In progress' | `YHWH v2.4/docs/superpowers/plans/2026-05-31-mint-7-quality-pass.md:2` |
| 32 | LOW | docs | MATRIX_MAP says 13 translation dirs; actual filesystem has 14 | `YHWH v2.4/dev/MATRIX_MAP.md:32` |
| 33 | LOW | tests | Share-pin in γ.4.2 arc-close class violates §8.1 convention | `YHWH v2.4/tests/test_ethiopian_gamma4.py:1177-1180` |
| 34 | LOW | tests | test_detect_returns_empty_for_uncommented_verse assumes mat 1:1 has no patristic entry (same state-default violation) | `YHWH v2.4/tests/test_patristic_gamma3.py:221-228` |
| 35 | LOW | tests | promote_candidate coordinate guard not directly unit-tested — only batch_insert_notes is covered | `YHWH v2.4/tests/test_scripts.py:6617-6629` |
| 36 | INFO | cross-module | bookcode_canonical lint does not screen CCEL_ABBREV or EASTON_BOOK — coverage gap for future ingest-script edits | `YHWH v2.4/scripts/lint_rules.py:1995-2003` |
| 37 | INFO | docs | REPO_MAP scripts/api/ count is 17 but 18 files exist; scripts/templates/ count is 20 but 21 exist | `YHWH v2.4/dev/REPO_MAP.md:42-43` |
| 38 | INFO | docs | REPO_MAP tests count is 168 but 169 test_*.py files exist | `YHWH v2.4/dev/REPO_MAP.md:17` |
| 39 | INFO | docs | lint_rules.py check_superpowers_coherence docstring says 'mint-6 backfilled all 39'; count is now 41 | `YHWH v2.4/scripts/lint_rules.py:1357` |
| 40 | INFO | docs | REPO_MAP dev/archive section lists only PLAN_2026-05-07/08/09 as archived plans; two more exist | `YHWH v2.4/dev/REPO_MAP.md:51` |

## Detailed survivors

### 1. [HIGH] Wall-clock date embedded in every edition OPF via _resolve_publishing defaults

- **Dimension:** byte-stability
- **Location:** `YHWH v2.4/scripts/epub_utils.py:29-37`
- **Evidence:**

`now_year = datetime.now(timezone.utc).year` and `now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")` are used as fallback defaults for `copyright_year` and `publication_date` respectively. No edition in `editions.yaml` sets either field, so `edition.get(k) or v` always falls through to the live date. `patch_opf` then writes `<dc:date>{pub['publication_date']}</dc:date>` (the replaced line in `content.opf`) and a `<dc:rights>Copyright © {pub['copyright_year']} ...</dc:rights>` block into every built EPUB. Two builds of the same unchanged edition on different calendar days produce different `content.opf` bytes. The `test_byte_stability_gate._content_digest` normalises only `urn:yhwh:edition:*` URNs and `dcterms:modified`; it does NOT normalise `<dc:date>` or `<dc:rights>`, so a cross-midnight rebuild would fail the determinism assertion at line 90.

- **Fix:** In `epub_utils._resolve_publishing`, replace the two `datetime.now()` calls with static project-epoch defaults: `"copyright_year": "2026"` and `"publication_date": "2026-05-14"` (the Omega-0 free-public pivot date, already the canonical CC0 release point). These remain the defaults until an edition explicitly sets the fields. Alternatively, add these fields to every edition record in `editions.yaml`. Also extend `test_byte_stability_gate._content_digest` to normalise `<dc:date>` and the copyright year in `<dc:rights>` so future volatile defaults are caught at the test layer.
- **Verifier-corrected fix:** In `YHWH v2.4/scripts/epub_utils.py` lines 29-37, replace the two `datetime.now()` calls with static strings:

```python
defaults = {
    "publisher_name": "Independent",
    "publisher_url": "",
    "copyright_year": "2026",
    "copyright_holder": "",
    "copyright_notice": "All rights reserved.",
    "publication_date": "2026-05-14",   # Omega-0 free-public pivot date
    "language_code": "en",
    "cover_credit": "",
    "source_text_credit": "Scripture text based on the World English Bible (public domain).",
}
```

Remove the `now_year` and `now_date` local variables and the `datetime` import (if no longer used elsewhere in the file — it is not used elsewhere in epub_utils.py).

Additionally, in `YHWH v2.4/tests/test_byte_stability_gate.py`, extend `_content_digest` to also normalize the two remaining volatile OPF fields so the test can actually catch this class of regression going forward:

```python
_DATE_RE = re.compile(r"<dc:date>[^<]*</dc:date>")
_RIGHTS_YEAR_RE = re.compile(r"(Copyright © )\d{4}( )")

# inside _content_digest, after the existing _MODIFIED_RE substitution:
text = _DATE_RE.sub("<dc:date>NORMALIZED</dc:date>", text)
text = _RIGHTS_YEAR_RE.sub(r"\g<1>YYYY\g<2>", text)
```

These two changes together fix the root cause and harden the guard against future volatile-default regressions. No marathon-core files are touched; schema change is additive (only def …[clipped]
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): All four code claims independently verified by direct reading:

1. `epub_utils._resolve_publishing` (lines 29-30, 34, 37): both `datetime.now(timezone.utc).year` and `datetime.now(timezone.utc).strftime("%Y-%m-%d")` are called at build time and used as defaults for `copyright_year` and `publication_date`. Confirmed exactly as described.

2. `content/editions.yaml`: grep for `copyright_year` and `publication_date` returned zero matches — no edition record overrides these fields. The `edition.get(k) or v` fallback always falls through to the live-date defaults. Confirmed.

3. `build_edition.patc …[clipped]
  - skeptic 2 (high, refuted=false): Directly confirmed all claims by reading the code.

(a) Code does what the evidence claims: `epub_utils._resolve_publishing` (lines 29-30) calls `datetime.now(timezone.utc)` twice for `copyright_year` and `publication_date` defaults. `editions.yaml` has no `publication_date` or `copyright_year` fields in any edition, so the `edition.get(k) or v` fallback always resolves to the live wall-clock values. `patch_opf` in `build_edition.py` writes `<dc:date>{pub['publication_date']}</dc:date>` (line 1142) and a `<dc:rights>Copyright © {pub['copyright_year']} ...` block (lines 1223-1227). Because `str …[clipped]

### 2. [HIGH] scripts/api/exports.py subprocess.run missing stdin=subprocess.DEVNULL — WinError 6 in production HTTP build endpoint

- **Dimension:** concurrency-caching
- **Location:** `YHWH v2.4/scripts/api/exports.py:197`
- **Evidence:**

proc = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    cwd=str(REPO),
    timeout=timeout_s,
)

This is the non-frozen path of the /api/exports/build HTTP endpoint — the primary user-facing EPUB download button. No stdin=subprocess.DEVNULL. Per the project's W-W1 rule (memory feedback_w_w1_subprocess_devnull): 'On Windows pytest-from-PowerShell, every subprocess.run() must pass stdin=subprocess.DEVNULL or hits WinError 6.' The dev server is always launched from PowerShell on this Windows box. When the web server's HTTP-handler thread spawns build_edition.py via this subprocess.run, it inherits the invalid stdin handle and raises WinError 6 (ERROR_INVALID_HANDLE), aborting the build silently.

- **Fix:** Add stdin=subprocess.DEVNULL to the call:

proc = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    cwd=str(REPO),
    timeout=timeout_s,
    stdin=subprocess.DEVNULL,  # W-W1: Windows PowerShell guard
)

Match the pattern already used by scripts/ebible.py, scripts/ci.py, scripts/audit_types.py, etc.
- **Verifier-corrected fix:** Add stdin=subprocess.DEVNULL to the subprocess.run call at line 197:

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO),
        timeout=timeout_s,
        stdin=subprocess.DEVNULL,  # W-W1: Windows PowerShell guard
    )

The finder's fix is exactly correct. No changes needed.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently verified by reading the file. At line 197 of `YHWH v2.4/scripts/api/exports.py`, the `subprocess.run` call in the `else` branch (non-frozen path) lacks `stdin=subprocess.DEVNULL`. This branch executes on every dev-server build request launched from PowerShell — `getattr(sys, "frozen", False)` is `False` in that context, so the frozen/in-process path at line 191 is bypassed. The W-W1 project rule (documented in memory and applied to every other `subprocess.run` in the codebase — confirmed by grep: `ebible.py`, `ci.py`, `audit_types.py`, `lint_rules.py`, `ship-check.py`, `core/epub …[clipped]
  - skeptic 2 (high, refuted=false): Independently verified by reading the file. At line 197 of YHWH v2.4/scripts/api/exports.py, the subprocess.run call in the non-frozen branch of api_export_build is:

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO),
        timeout=timeout_s,
    )

No stdin=subprocess.DEVNULL is present. The frozen path (lines 187-194) is in-process (calls _be.build_one directly) and never reaches this subprocess.run, so the W-W1 risk is entirely on the non-frozen dev-server path — which is the primary runtime on this Windows box launched from Powe …[clipped]

### 3. [HIGH] find_aside_insertion_point regex `(\d{2})(\d{2})` cannot parse aside IDs for chapters >= 100 (1 Enoch chapters 100-108, Strategy-A)

- **Dimension:** correctness
- **Location:** `YHWH v2.4/scripts/inject.py:606-608`
- **Evidence:**

```python
existing_re = re.compile(
    r'<aside\s+class="note\s+[^"]+"\s+id="note-' + re.escape(prefix) + r'(\d{2})(\d{2})([a-z]?)"',
)
```
1 Enoch (code `1en`, id_prefix `1e`, Strategy-A) has 108 chapters. inject.py builds aside IDs via `full_id = f"{prefix}{ch:02d}{v:02d}{suffix or ''}"` — `{100:02d}` = `'100'` (3 digits). The regex expects exactly `\d{2}` (2 digits) for chapter, so `id="note-1e10001"` (ch=100,v=01) does not match. The fallback is `insertion = inside_start` for every note scanned, placing ALL re-injected 1En 100+ notes at the section head rather than their sorted positions.

- **Fix:** Change `(\d{2})(\d{2})` to `(\d+)(\d{2})` so the chapter group is greedy (one or more digits) while the verse group remains exactly 2 digits. The parse of `10001` then yields `existing_ch=100, existing_v=01` correctly. The wider `\d+` is safe because note IDs always end with a 2-digit verse and an optional letter.
- **Verifier-corrected fix:** In `scripts/inject.py` line 607, change `r'(\d{2})(\d{2})([a-z]?)"'` to `r'(\d+)(\d{2})([a-z]?)"'`.

The same fix must also be applied to `scripts/coverage.py` line 144, which has an identical `(\d{2})(\d{2})` pattern used to count injected notes per chapter — it will silently undercount all notes in 1 Enoch chapters 100–108 (reporting them as missing rather than present), giving a false coverage deficit. The finder's proposed fix is correct for inject.py; extend it to coverage.py.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently verified by reading the code:

1. `C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\inject.py` line 704: `full_id = f"{prefix}{ch:02d}{v:02d}{suffix or ''}"`. Python's `{100:02d}` produces `'100'` (minimum-width 2, no truncation), so ch=100 yields a 3-digit string.

2. Line 607: `r'(\d{2})(\d{2})([a-z]?)"'` — exactly 2 digits for chapter, 2 for verse. Against the string `10001"` (ch=100, v=01, no suffix): the regex engine tries `\d{2}`=`10`, `\d{2}`=`00`, `[a-z]?`=`""`, then expects `"` but finds `1`. No match. The aside for ch=100 is never found by `finditer`, so the in …[clipped]
  - skeptic 2 (high, refuted=false): All three key facts independently confirmed by reading the actual files:

1. C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\content\books.yaml line 200-202: `ch_count: 108`, `strategy: "A"`, `id_prefix: "1e"` for 1 Enoch — confirmed exactly as the finder states.

2. C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\inject.py line 704: `full_id = f"{prefix}{ch:02d}{v:02d}{suffix or ''}"` — Python's `:02d` zero-pads to minimum 2 digits but does NOT truncate. `{100:02d}` = `"100"` (3 chars), so a ch=100 note generates ID `"1e10001a"`.

3. inject.py line 607: `r'(\d{2})(\d{2})([a-z]?)"' …[clipped]

### 4. [HIGH] write_book serialises attribution as {} (empty dict) instead of omitting the 9th field, corrupting the notes schema

- **Dimension:** correctness
- **Location:** `YHWH v2.4/scripts/web_helpers.py:131, 146, 174, 182`
- **Evidence:**

tuple_to_dict (line 131): `"attribution": attribution or {}` converts None/empty to `{}`. dict_to_tuple (line 146): `d.get("attribution") or {}` returns `{}` when the value is `{}`. write_book (line 174): `attribution = rest[0] if rest else {}` then line 182: `lines.append(f"        {attribution!r},\n")` writes the literal `{}` into the .py file as a 9th tuple field. The canonical schema (config.py NoteSpec docstring) expects attribution to be `str | None`; an 8-field tuple with no attribution is the correct representation for notes without provenance. After a round-trip through the web UI, every previously-8-field note becomes a 9-field tuple with `{}` as the 9th field. Downstream consumers that do `isinstance(tup[8], str)` (validate_taxonomy.py line 178, dashboard.py line 139, traditions.py line 114) all get `False`, so the note is silently reported as unattributed even though it now has a 9th field. The build_edition._iter_note_ref_attribution_years does `tup[8] or ""` which is safe for an empty dict (falsy), but any code doing `.strip()` on a non-empty dict attribution would crash.

- **Fix:** In tuple_to_dict change `attribution or {}` to `attribution or ""` (line 131). In dict_to_tuple change `d.get("attribution") or {}` to `d.get("attribution") or None` (or `""`) (line 146). In write_book only emit the attribution line when it is a non-empty string: `if isinstance(attribution, str) and attribution.strip(): lines.append(f"        {attribution!r},\n")` — otherwise omit it, keeping the tuple at 8 fields. This restores the canonical 8-field / 9-field-with-string-only invariant that every downstream consumer assumes.
- **Verifier-corrected fix:** The proposed fix is correct and safe. Apply all three changes to `YHWH v2.4/scripts/web_helpers.py`:

Line 131 in `tuple_to_dict`: change `"attribution": attribution or {}` to `"attribution": attribution or ""`

Line 146 in `dict_to_tuple`: change `d.get("attribution") or {}` to `d.get("attribution") or None`

Lines 173-182 in `write_book`: make the attribution line conditional:
```python
ch, v, suffix, anchor, kind, title, label, body, *rest = tup
attribution = rest[0] if rest else None
lines.append("    (\n")
lines.append(f"        {ch}, {v}, {suffix!r},\n")
lines.append(f"        {anchor!r},\n")
lines.append(f"        {kind!r},\n")
lines.append(f"        {title!r},\n")
lines.append(f"        {label!r},\n")
lines.append(f"        {body!r},\n")
if isinstance(attribution, str) and attribution.strip():
    lines.append(f"        {attribution!r},\n")
lines.append("    ),\n")
```

This restores the 8-field / 9-field-with-non-empty-string invariant. No marathon core is touched. Notes already on disk are unaffected (confirmed zero `{}` instances). KJV edition byte-stability is preserved.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): 
Independently verified by reading all cited code. The bug is real and confirmed:

1. `tuple_to_dict` line 131: `attribution or {}` — when an 8-field note is loaded (9th slot padded to `None`), `None or {}` = `{}`. Confirmed exact text in web_helpers.py:131.

2. `dict_to_tuple` line 146: `d.get("attribution") or {}` — after the dict round-trips as JSON, `{} or {}` = `{}`. The 9th tuple field is `{}`. Confirmed exact text at line 146.

3. `write_book` line 174/182: for an 8-field note received from `dict_to_tuple`, `rest[0]` = `{}`, which is then serialised as `{},` in the .py file unconditiona …[clipped]
  - skeptic 2 (high, refuted=false): All three cited code points are confirmed by direct reading:

1. `web_helpers.py` line 131: `"attribution": attribution or {}` — confirmed. A None attribution (from an 8-field note tuple padded with None by `tuple_to_dict`) becomes `{}` in the returned dict.

2. `web_helpers.py` line 146: `d.get("attribution") or {}` — confirmed. When the dict value is `{}` (from step 1), this returns `{}`, so `dict_to_tuple` produces a 9-field tuple with `{}` at index 8.

3. `web_helpers.py` lines 174/182: `attribution = rest[0] if rest else {}` followed by unconditional `lines.append(f"        {attribution!r …[clipped]

### 5. [HIGH] Exodus translation data unreachable: all 4 Tewahedo stores use non-canonical filename `ex.py` instead of `exo.py`

- **Dimension:** data-validity (finder said critical, recalibrated to high)
- **Location:** `YHWH v2.4/content/translations/amharic-tewahedo/ex.py:1`
- **Evidence:**

File header: `"""Translation: amharic-tewahedo · Book: ex`. `translations.get_verse(translation, book_code, ...)` builds path via `TRANSLATIONS_DIR / translation / f"{book_code}.py"` (scripts/core/translations.py:55). Every pipeline call uses canonical code `exo` (from books.yaml), so `translations.get_verse("amharic-tewahedo", "exo", ...)` looks for `amharic-tewahedo/exo.py` which does not exist — it silently returns None for every Exodus verse. Same defect in `geez-tewahedo/ex.py`, `amharic-tewahedo-en/ex.py`, and `geez-tewahedo-en/ex.py`. Root in `_source.yaml:110`: `book_codes: [ex]` instead of `[exo]`. The tests at `tests/test_parallel_bible_tau7xb.py:123` pin the wrong code (`assert _exodus_block()["book_codes"] == ["ex"]`), confirming the defect propagated into the test suite.

- **Fix:** Rename all four files: `amharic-tewahedo/ex.py` → `amharic-tewahedo/exo.py`, `geez-tewahedo/ex.py` → `geez-tewahedo/exo.py`, `amharic-tewahedo-en/ex.py` → `amharic-tewahedo-en/exo.py`, `geez-tewahedo-en/ex.py` → `geez-tewahedo-en/exo.py`. Update the BOOK field in each file's docstring from `ex` to `exo`. Update `content/translations/sources/parallel-bible-eotc/_source.yaml` line 110: `book_codes: [exo]`. Update `content/translations/amharic-tewahedo/_meta.yaml` line 161 and `content/translations/geez-tewahedo/_meta.yaml` to `ingested_book_codes: [exo]`. Update all test pins in `tests/test_parallel_bible_tau7xb.py` that assert `book_codes == ["ex"]` or reference `ex.py` by name to use `exo`. Add `"ex": "exo"` to `scripts/core/sources_base._BOOK_CODE_ALIASES` so any future detector that emits `ex` normalises correctly.
- **Verifier-corrected fix:** The defect is latent and should be fixed when the τ.G.x.* standalone-build wiring lands, not before. At that point, the single safest fix is to add an alias dict directly in `YHWH v2.4/scripts/core/translations.py` mirroring the pattern already established in `render_coverage.py`:

In `translations.py`, replace `_book_path` (line 54-55) with:

```python
_TRANSLATION_BOOK_ALIASES: dict[str, str] = {"ex": "exo", "1k": "1ki", "2k": "2ki"}

def _book_path(translation: str, book_code: str) -> Path:
    resolved = _TRANSLATION_BOOK_ALIASES.get(book_code, book_code)
    return TRANSLATIONS_DIR / translation / f"{resolved}.py"
```

This is additive, zero-blast-radius for the 9 KJV editions (they use canonical codes already), and handles all three legacy 2-letter stems that render_coverage already knows about. Do NOT rename the `ex.py` files or change the test pins before the τ.G.* wiring is complete — the tests contractually verify the ingest artefact shape, and the file rename must be a coordinated commit that updates _source.yaml, _meta.yaml, the 4 files themselves, and all test pins atomically.
- **Adversarial verdict (3 skeptic[s]):**
  - skeptic 1 (high, refuted=false): The filename mismatch is confirmed real: all 4 Tewahedo stores use `ex.py` while `books.yaml` declares canonical code `exo`, and `translations.py:_book_path` (line 54-55) does zero aliasing — `get_verse("amharic-tewahedo-en", "exo", …)` would silently return None. The base HTML uses `vnote-exo-` aside IDs, confirmed by grepping `epub_working/index_split_000.html`.

However, the critical severity is NOT sustained for the current state:

1. Runtime blast radius = zero today. The only editions using Tewahedo translations (`standalone-geez`, `standalone-amharic`) have `standalone: true` in edition …[clipped]
  - skeptic 2 (high, refuted=false): I independently confirmed every factual claim in the finding:

1. All four `ex.py` files exist (Glob confirmed: `amharic-tewahedo/ex.py`, `geez-tewahedo/ex.py`, `amharic-tewahedo-en/ex.py`, `geez-tewahedo-en/ex.py`). No `exo.py` exists for any Tewahedo store; every other translation uses `exo.py` (kjv, jps, douay-rheims, vulgate-clementine, wlc, lxx-swete-greek, arabic-vandyke all have `exo.py`).

2. `scripts/core/translations.py:55` builds the path as `TRANSLATIONS_DIR / translation / f"{book_code}.py"` — no aliasing, no normalization. `books.yaml:21` confirms canonical code is `exo`. So `get …[clipped]
  - skeptic 3 (high, refuted=false): Independently verified the finding is real by reading all cited code, but the severity and fix completeness need correction.

CONFIRMED TRUE:
- All 4 Tewahedo stores (`amharic-tewahedo/ex.py`, `geez-tewahedo/ex.py`, `amharic-tewahedo-en/ex.py`, `geez-tewahedo-en/ex.py`) exist on disk; no `exo.py` equivalents exist in these dirs (confirmed via Glob).
- `translations.py:_book_path` builds `TRANSLATIONS_DIR / translation / f"{book_code}.py"` with zero alias normalization (line 55). Any call with canonical `"exo"` returns None/False.
- `_source.yaml` line 110 has `book_codes: [ex]` — confirmed.
-  …[clipped]

### 6. [HIGH] test_amharic_tewahedo_contains_gen_py is dead — def keyword buried inside a comment

- **Dimension:** tests
- **Location:** `YHWH v2.4/tests/test_parallel_bible_tau6x1.py:834`
- **Evidence:**

Line 834: `# Durable invariant: gen.py present (Π.0 seed or successor).def test_amharic_tewahedo_contains_gen_py(self):` — the `def` keyword appears at the tail of a `#` comment, so Python never sees it as a method definition. The intended docstring (lines 835-838) becomes a dead string literal inside `test_geez_tewahedo_still_gen_only`, and lines 839-843 (`slot = REPO / ... amharic-tewahedo` + `assert 'gen.py' in files`) execute as part of the wrong test. `test_amharic_tewahedo_contains_gen_py` does not exist in pytest's collection at all.

- **Fix:** Break line 834 so the `def` starts on its own line. Replace the end of line 834 with a newline before `def`:
```python
        # Durable invariant: gen.py present (Π.0 seed or successor).
    def test_amharic_tewahedo_contains_gen_py(self):
```
This separates the comment from the method definition, makes the docstring on lines 835-838 the method's docstring, and registers the test with pytest properly. Also verify the indentation level matches the class (one `    def`, not `        def`).
- **Verifier-corrected fix:** Split line 834 at the boundary between the comment text and the `def` keyword. The result should be:

        # Durable invariant: gen.py present (Π.0 seed or successor).
    def test_amharic_tewahedo_contains_gen_py(self):

The comment (8-space indent, inside the geez method body) stays on its own line. The `def` starts a new line at 4-space indent (class-method level), matching every other method in `TestTau6X1ClosedArcInvariantPreservation`. Lines 835-843 are already correctly indented for the new method body and require no changes. The fix is safe: test file only, no marathon core touched, no KJV edition build output or schema affected.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently verified by reading C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\tests\test_parallel_bible_tau6x1.py lines 812-843. Line 834 is exactly as cited: the token `def test_amharic_tewahedo_contains_gen_py(self):` appears at the tail of a `#` comment, so Python parses the entire line as a comment. Python never sees a method definition. Consequences confirmed: (1) pytest never collects `test_amharic_tewahedo_contains_gen_py` — the test does not exist; (2) lines 835-838 become a dead string literal inside `test_geez_tewahedo_still_gen_only`; (3) lines 839-843 (the amharic slot check  …[clipped]
  - skeptic 2 (high, refuted=false): Independently confirmed by reading the file. Line 834 of C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\tests\test_parallel_bible_tau6x1.py reads exactly: `        # Durable invariant: gen.py present (Π.0 seed or successor).def test_amharic_tewahedo_contains_gen_py(self):` — the `def` keyword is appended to the tail of a `#` comment, so Python never parses it as a method definition. The intended method body (lines 835-843: the docstring, the `amharic-tewahedo` slot lookup, and the `gen.py` assert) are absorbed into `test_geez_tewahedo_still_gen_only` as sequential statements after that meth …[clipped]

### 7. [MEDIUM] ebible build pipeline omits check_nested_anchors guard after inject mutates epub_working/

- **Dimension:** byte-stability
- **Location:** `YHWH v2.4/scripts/ebible.py:227-255`
- **Evidence:**

`cmd_build` runs `inject.py --all-books` (step that writes to `epub_working/`) followed immediately by `build_edition.py --all`, but never calls `check_nested_anchors`. CLAUDE_PROJECT_RULES §8 (line 808): 'Run…`python scripts/check_nested_anchors.py` (run `--fix` if it reports any)…' after inject. The base currently has 0 nested anchors (confirmed by grep), but the next inject that places a `note-ref` marker inside a `vn-link` verse anchor — a known inject failure mode documented in RULES §8 line 813-816 — would leave the base broken and go undetected until `ebible ship` is run. The built EPUB for verse-popups-enabled editions would carry nested `<a>` (invalid XHTML; RSC-005) because `_disable_vn_links` only fires when `verse_popups_enabled=False`.

- **Fix:** In `ebible.py cmd_build`, add a `check_nested_anchors` step between the inject and build-editions steps:
```python
steps = [
    ("inject (source → HTML)", "inject.py", ["--all-books"]),
    ("manifest (corpus hash)", "manifest.py", ["--build"]),
    ("nested-anchor guard", "check_nested_anchors.py", ["--fix"]),  # ADD THIS
]
```
The `--fix` flag is safe (idempotent; only rewrites files that have nesting). This closes the gap between the process rule and the automated pipeline.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): I read /YHWH v2.4/scripts/ebible.py lines 227-255 directly. The `steps` list in `cmd_build` contains exactly two entries: `inject.py --all-books` and `manifest.py --build`. There is no `check_nested_anchors.py` call anywhere between inject and the `build_edition.py` invocation. This matches the finder's claim exactly.

I also confirmed that `check_nested_anchors.py` IS called in `scripts/ship-check.py` line 81 (the `ebible ship` subcommand), so the guard is not absent from the project entirely — it just fires at ship time rather than build time.

CLAUDE_PROJECT_RULES §8 lines 808-816 explicitl …[clipped]

### 8. [MEDIUM] _resolve_publishing injects wall-clock date into OPF <dc:date>, breaking build reproducibility and poisoning the content-addressable cache

- **Dimension:** byte-stability (finder said high, recalibrated to medium)
- **Location:** `YHWH v2.4/scripts/epub_utils.py:29-30`
- **Evidence:**

`now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")` is used as the default for `publication_date` (line 37: `"publication_date": now_date`). Since no edition in `content/editions.yaml` sets `publication_date`, `_resolve_publishing` always returns today's date. `patch_opf` (build_edition.py:1142) then writes it into `<dc:date>` inside the packaged `content.opf`. Two builds on different calendar dates therefore produce different OPF bytes — the EPUB is not reproducible. Worse, `build_cache.compute_cache_key` hashes the edition record (which contains no `publication_date`) and `epub_working/` files, but not the current date, so a cache hit the next day serves a stale EPUB with yesterday's `<dc:date>`. The byte-stability test (`test_byte_stability_gate._content_digest`) normalizes `dcterms:modified` and the URN but NOT `<dc:date>`, so a run that crosses midnight would fail.

- **Fix:** Pin `publication_date` in every edition profile in `content/editions.yaml` (e.g. `publication_date: "2026-01-01"`) so `_resolve_publishing` returns a stable value instead of `datetime.now()`. Alternatively, change the fallback in `_resolve_publishing` from `now_date` to a project-level constant such as `"2026-01-01"` and document that editions.yaml is the canonical override. Either way, add `_DC_DATE_RE = re.compile(r'<dc:date>[^<]*</dc:date>')` normalization alongside `_MODIFIED_RE` in `test_byte_stability_gate._content_digest`.
- **Verifier-corrected fix:** Two complementary changes, both safe and additive:

1. In `YHWH v2.4/scripts/epub_utils.py` line 37, replace the `now_date` fallback with a pinned project constant:
   ```python
   "publication_date": "2026-01-01",
   ```
   This eliminates the `datetime.now()` call for this field entirely. No edition in editions.yaml currently sets `publication_date`, so this is a pure fallback change with no schema breakage.

2. In `YHWH v2.4/tests/test_byte_stability_gate.py`, add a `<dc:date>` normalizer alongside the existing `_MODIFIED_RE` (line 36):
   ```python
   _DATE_RE = re.compile(r"<dc:date>[^<]*</dc:date>")
   ```
   And apply it in `_content_digest` after line 61:
   ```python
   text = _DATE_RE.sub("<dc:date>NORMALIZED</dc:date>", text)
   ```
   This makes the stability test robust even if a future maintainer reintroduces a dynamic date default.

Optionally, add a `publication_date` key to each edition record in `content/editions.yaml` with a fixed value (e.g. `"2026-01-01"`) to make the intent explicit in config rather than relying on the fallback constant. Do NOT touch any marathon core files.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): All three sub-claims were independently verified by reading the actual source files.

(a) Code does exactly what evidence claims:
- `epub_utils.py` lines 29-30, 37: `now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")` is the literal fallback for `publication_date` in `_resolve_publishing`. Confirmed.
- `content/editions.yaml` has no `publication_date` key in any edition record (grep returned no matches). So the fallback fires on every build. Confirmed.
- `build_edition.py` lines 1139-1144: `patch_opf` writes `pub['publication_date']` directly into `<dc:date>` in the OPF. Confirmed.
- ` …[clipped]
  - skeptic 2 (high, refuted=false): All three claims in the finding independently confirmed by reading the code:

(a) CODE DOES WHAT EVIDENCE CLAIMS: `epub_utils.py` lines 29-30/37 confirmed — `datetime.now(timezone.utc)` is called twice and the formatted date string is assigned to the `"publication_date"` key in `defaults`. A grep of `content/editions.yaml` for `publication_date` returned no matches, so `edition.get("publication_date")` is always falsy and the `now_date` fallback is always taken. `build_edition.py` lines 1139-1145 confirmed — `patch_opf` does a `re.sub` that writes `pub['publication_date']` into `<dc:date>`. `t …[clipped]

### 9. [MEDIUM] translations._book_index caches stale verse-lookup dict, bypassing mtime-keyed freshness of _load_book_cached

- **Dimension:** concurrency-caching (finder said high, recalibrated to medium)
- **Location:** `YHWH v2.4/scripts/core/translations.py:120-128`
- **Evidence:**

@functools.lru_cache(maxsize=256)
def _book_index(translation: str, book_code: str) -> dict[tuple[int, int], str] | None:
    verses = _load_book(translation, book_code)
    ...
    return {(c, v): t for (c, v, t) in verses}

The cache key is (translation, book_code) only — no mtime. _load_book() is itself mtime-keyed (calls _load_book_cached(path_str, mtime_ns)), so a re-read after a file edit returns fresh tuples. But _book_index never calls _load_book() again after the first call: it permanently holds the dict built from the original mtime snapshot. All get_verse() / get_chapter() calls go through _book_index, so every verse lookup is stale until clear_cache() is called explicitly. During a 30-90s build_edition run (build_edition.py calls get_verse() thousands of times), an in-flight edit to a translation .py file would silently serve old verse text for the rest of the build.

- **Fix:** Include mtime_ns in the _book_index cache key so the dict is rebuilt when the file changes. Change the signature to:

@functools.lru_cache(maxsize=256)
def _book_index(translation: str, book_code: str, mtime_ns: int) -> dict[tuple[int, int], str] | None:
    path = _book_path(translation, book_code)
    verses = _load_book(translation, book_code)   # _load_book_cached is keyed on (path_str, mtime_ns) already
    ...

and update _load_book to thread mtime_ns through:

def _load_book(translation: str, book_code: str):
    path = _book_path(translation, book_code)
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return None
    return _load_book_cached(str(path), mtime_ns)

def _book_index_for(translation: str, book_code: str):
    path = _book_path(translation, book_code)
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return None
    return _book_index(translation, book_code, mtime_ns)

Change get_verse/get_chapter to call _book_index_for instead of _book_index directly. This mirrors exactly the _load_notes_cached / load_notes split in notes_io.py (RULES §7.1 canonical pattern). The clear_cache() function still calls _bo …[clipped]
- **Verifier-corrected fix:** The proposed fix is correct. The minimal safe implementation in `C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\core\translations.py`:

1. Add `mtime_ns: int` parameter to `_book_index`:
```python
@functools.lru_cache(maxsize=256)
def _book_index(translation: str, book_code: str, mtime_ns: int) -> dict[tuple[int, int], str] | None:
    verses = _load_book(translation, book_code)
    if verses is None:
        return None
    return {(c, v): t for (c, v, t) in verses}
```

2. Add a thin wrapper that resolves mtime and calls the above:
```python
def _book_index_for(translation: str, book_code: str) -> dict[tuple[int, int], str] | None:
    path = _book_path(translation, book_code)
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return None
    return _book_index(translation, book_code, mtime_ns)
```

3. Change `get_verse` to call `_book_index_for` instead of `_book_index`:
```python
def get_verse(translation: str, book_code: str, chapter: int, verse: int) -> str | None:
    idx = _book_index_for(translation, book_code)
    if idx is None:
        return None
    return idx.get((chapter, verse))
```

4. `clear_cache()` needs no change — `_book_index.cache_clear()` still works on the now-3-arg function.

This mirrors the `_load_book_cached`/`_load_book` split already in place and is safe: additive, no marathon-core files touched, byte-stab …[clipped]
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): The code at lines 120-128 of translations.py is exactly as described. `_book_index` is `lru_cache`'d on `(translation, book_code)` alone. Once populated, it never re-calls `_load_book()`, so a file edit is invisible to `get_verse()` until `clear_cache()` is explicitly called. This creates a verified asymmetry: `get_chapter()` (line 175) calls `_load_book()` directly and benefits from mtime-keyed freshness on every call, while `get_verse()` (line 169) goes through the permanently-cached `_book_index` dict. Both are public API — during a live web server session (the only long-lived process), edi …[clipped]
  - skeptic 2 (medium, refuted=false): The code at lines 120-128 of `YHWH v2.4/scripts/core/translations.py` is exactly as described: `_book_index` is decorated with `@functools.lru_cache(maxsize=256)` keyed only on `(translation, book_code)`, while `_load_book_cached` beneath it is keyed on `(path_str, mtime_ns)`. On the first call, `_book_index` delegates to `_load_book` (which is mtime-aware), builds the dict, and caches it permanently under the bare `(translation, book_code)` key. Subsequent calls return the stale cached dict without re-checking mtime. The finding is technically real.

However, the HIGH severity rating is wrong …[clipped]

### 10. [MEDIUM] scripts/build_edition.py subprocess.run for build_epub.py missing stdin=subprocess.DEVNULL — WinError 6 in dev build path

- **Dimension:** concurrency-caching
- **Location:** `YHWH v2.4/scripts/build_edition.py:3022-3033`
- **Evidence:**

result = subprocess.run(
    [
        sys.executable,
        str(REPO_ROOT / 'scripts' / 'build_epub.py'),
        str(output_path),
        '--epub-dir',
        str(tmp),
        '--no-bump',
    ],
    capture_output=True,
    text=True,
)

The non-frozen (dev mode) path of build_one() launches build_epub.py as a subprocess. No stdin=subprocess.DEVNULL. Any CLI invocation of build_edition.py from PowerShell, or the web server's build trigger, will hit WinError 6 on this call. The frozen path goes in-process and is safe; only the subprocess branch (the default dev path) is affected.

- **Fix:** Add stdin=subprocess.DEVNULL:

result = subprocess.run(
    [
        sys.executable,
        str(REPO_ROOT / 'scripts' / 'build_epub.py'),
        str(output_path),
        '--epub-dir',
        str(tmp),
        '--no-bump',
    ],
    capture_output=True,
    text=True,
    stdin=subprocess.DEVNULL,  # W-W1: Windows PowerShell guard
)
- **Verifier-corrected fix:** Add `stdin=subprocess.DEVNULL` to the subprocess.run call at `YHWH v2.4/scripts/build_edition.py` lines 3022-3033:

```python
result = subprocess.run(
    [
        sys.executable,
        str(REPO_ROOT / "scripts" / "build_epub.py"),
        str(output_path),
        "--epub-dir",
        str(tmp),
        "--no-bump",
    ],
    capture_output=True,
    text=True,
    stdin=subprocess.DEVNULL,  # W-W1: Windows PowerShell guard
)
```

The finder's proposed fix is correct and safe as stated.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Confirmed by direct code reading. The `else` branch at `YHWH v2.4/scripts/build_edition.py` lines 3022-3033 calls `subprocess.run(...)` with `capture_output=True, text=True` but no `stdin=subprocess.DEVNULL`. Every other `subprocess.run` in the codebase (verified across add_note.py, add_kind.py, audit_dead_code.py, audit_types.py, ci.py, verify.py, epubcheck.py, lint_rules.py, extract_parallel_pdf.py, ebible.py, ship-check.py) consistently includes `stdin=subprocess.DEVNULL` with explicit W-W1 comments. This is an omission, not a design choice. The blast radius: this branch is the default dev  …[clipped]

### 11. [MEDIUM] find_aside_insertion_point treats higher-chapter asides as 'preceding', misorders re-injected notes in Strategy-B sections

- **Dimension:** correctness (finder said high, recalibrated to medium)
- **Location:** `YHWH v2.4/scripts/inject.py:621`
- **Evidence:**

`precedes = existing_ch != ch or (existing_v, existing_s) < target` — when an aside from chapter 12 is already in a Strategy-B per-file notes-section and a new note for chapter 5 is being inserted, `existing_ch (12) != ch (5)` is True, so `precedes=True` and `insertion` advances past the ch-12 aside. The ch-5 note ends up inserted AFTER ch-12 notes, violating sort order. This fires on any re-injection run where new notes for an earlier chapter are added to a book that already has later-chapter notes injected.

- **Fix:** Replace line 621 with a full 3-key comparison: `precedes = (existing_ch, existing_v, existing_s) < (ch, v, suffix or '')`. Also update the `else` return to guard that the existing aside belongs to a later chapter before treating it as the insertion point: `else: if existing_ch == ch: return inside_start + m.start()` (continue iterating for existing_ch > ch rather than stopping).
- **Verifier-corrected fix:** Change only line 621 in C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\inject.py:

Before:
    precedes = existing_ch != ch or (existing_v, existing_s) < target

After:
    precedes = (existing_ch, existing_v, existing_s) < (ch, v, suffix or "")

The `else` branch (lines 632–634) already correctly returns `inside_start + m.start()` as the insertion point whenever `precedes` is False, which now includes both "same chapter, later verse" and "later chapter" cases. No change to the else branch is needed; the finder's second proposed change (guarding on `existing_ch == ch`) is incorrect — it would cause the loop to continue iterating instead of returning, leaving insertion at a stale position when an existing aside from a later chapter is encountered first.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): I read C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\inject.py lines 597–635 in full and confirmed the logic independently.

Line 621: `precedes = existing_ch != ch or (existing_v, existing_s) < target`

The docstring (lines 598–601) describes "the chapter's notes-section" and "(verse, suffix) order", revealing the function was designed for Strategy-A's per-chapter sections where all asides share the same chapter number. In that context `existing_ch != ch` is always False and the condition degenerates correctly to a 2-key sort.

For Strategy-B (books 1ki, 2ki, 1ch, 2ch, psa, job, i …[clipped]
  - skeptic 2 (high, refuted=false): I independently verified the code at YHWH v2.4/scripts/inject.py line 621. The expression `precedes = existing_ch != ch or (existing_v, existing_s) < target` is confirmed present. The condition `existing_ch != ch` is True regardless of whether the existing aside is from an EARLIER or a LATER chapter — both get treated as "precedes", advancing `insertion` past them. When a Strategy-B file already contains a later-chapter (e.g. ch=12) aside and a new note for an earlier chapter (e.g. ch=5) is being inserted, the loop hits the ch=12 aside, fires `precedes=True`, advances `insertion` past it, and  …[clipped]

### 12. [MEDIUM] batch_insert_notes silently drops all inserts on SyntaxError in the generated output without informing the caller

- **Dimension:** correctness
- **Location:** `YHWH v2.4/scripts/promote.py:368-373`
- **Evidence:**

Lines 368-373:
```python
try:
    ast.parse(new_text)
except SyntaxError:
    return 0
ensure_backup(book_path)
atomic_write(book_path, new_text)
return len(inserts)
```
If the splice of new tuple text produces invalid Python (e.g. because `format_tuple_text` produced a string containing an unescaped quote), `ast.parse` raises `SyntaxError`, the function returns `0`, and all N candidates are silently dropped. `batch_promote_xrefs.py` calls `batch_insert_notes` and checks `if n:` — a return of `0` is indistinguishable from "no candidates to insert", so the data loss is never surfaced to the operator. The backup is NOT created in this path (it happens AFTER the parse check), so there is no partial-write, but the silent discard of potentially hundreds of candidates is a real data-loss risk.

- **Fix:** Return a sentinel error value (e.g. `-1`) or raise an exception on SyntaxError so the caller can distinguish failure from empty. Minimally, log the error before returning: `import logging; logging.error("batch_insert_notes: generated SyntaxError for %s; dropping %d inserts", book_path, len(inserts))`. Better: raise `RuntimeError(f"splice produced invalid Python in {book_path}")` so `batch_promote_xrefs.py`'s `except Exception` handler prints the error.
- **Verifier-corrected fix:** Minimal safe fix — add a `logging.error` call before the silent `return 0` so the operator always sees the failure. At the top of `promote.py` add `import logging` (already has `import ast`). Then change lines 369-370:

```python
except SyntaxError as exc:
    logging.error(
        "batch_insert_notes: splice produced invalid Python in %s "
        "(%d insert(s) dropped): %s",
        book_path, len(inserts), exc,
    )
    return 0
```

Stronger alternative (recommended): raise instead of returning silently so `batch_promote_xrefs.py`'s caller chain surfaces it as a visible failure:

```python
except SyntaxError as exc:
    raise RuntimeError(
        f"batch_insert_notes: splice produced invalid Python in {book_path} "
        f"({len(inserts)} insert(s) dropped)"
    ) from exc
```

Root cause to fix separately: `py_str` in `format_tuple_text` does not escape embedded literal newlines, which is the most likely trigger. Add `s = s.replace('\n', '\\n').replace('\r', '\\r')` at the top of `py_str` before the quote-selection logic. This makes SyntaxError from newlines impossible rather than just surfaced.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): The code at YHWH v2.4/scripts/promote.py lines 367-373 is exactly as described. The `ast.parse` guard fires, returns `0`, and the caller in batch_promote_xrefs.py line 81 does `if n:` — making a SyntaxError-triggered `0` indistinguishable from "no candidates". No log message, no exception, no indication to the operator that N notes were silently discarded.

The finder's claim that `format_tuple_text` can produce invalid Python is realistic: `py_str` correctly handles single/double quote mixing (escape interior `"` when both present), but does NOT escape embedded literal newline characters. If  …[clipped]

### 13. [MEDIUM] edition_canon_books sorted alphabetically — violates RULES §6.1 canonical order (affects 3 UI dropdowns)

- **Dimension:** cross-module (finder said high, recalibrated to medium)
- **Location:** `YHWH v2.4/scripts/web_editions.py:335`
- **Evidence:**

`edition_canon_books = {ed_id: sorted(books) for ed_id, books in _mtx.edition_canon_books.items()}` — Python `sorted()` on a set of book codes produces alphabetical order (1ch, 1co, 1en, 1jn, 1ki…). The comment at lines 303-307 in the same function explicitly states: 'Per CLAUDE_PROJECT_RULES.md §6.1, any per-book UI must list books in books.yaml order… The UI reads the order from this payload — never sorts on its own — so the canonical-order rule has one source of truth.' Line 335 directly contradicts that stated intent. Three JS consumers iterate this list in order rather than re-sorting: (1) `customize.py:515` — 'Upload per-book art' `<select>` dropdown; (2) `customize.py:250-256` — customize-page EPUB preview book picker; (3) `wizard.py:893-898` — wizard preview book picker. The `web_covers.py` counterpart at line 189 correctly uses `sorted(canon_set, key=lambda c: book_rank.get(c, 1_000_000))` via a rank derived from `config.load_books()` — showing the correct pattern already exists in the same codebase.

- **Fix:** Replace line 335 with a canonical-order list comprehension that filters `config.load_books()` rather than sorting the set:

```python
_book_order = [b["code"] for b in config.load_books()]
edition_canon_books = {
    ed_id: [c for c in _book_order if c in books]
    for ed_id, books in _mtx.edition_canon_books.items()
}
```

This mirrors the pattern already used in `web_editions.py:93` (`book_order = list(books_idx.keys())`) and `web_covers.py:178-189`. No schema change; the API shape is identical (a list per edition-id). Add an entry to `tests/test_scripts.py` — assert that `api_customize_data()["edition_canon_books"]["ethiopian-tewahedo"]` has `"gen"` before `"mat"` and `"mat"` before `"rev"` (mirrors the existing `check_encoder_canonical_order` fixture pattern).
- **Verifier-corrected fix:** Line 315 in the same function already computes `books_canonical` from `config.load_books()`. Reuse it to avoid a redundant call:

```python
# books_canonical is already defined at line 315:
# books_canonical = [{"code": b["code"], ...} for b in config.load_books()]
_book_order = [b["code"] for b in books_canonical]
edition_canon_books = {
    ed_id: [c for c in _book_order if c in books]
    for ed_id, books in _mtx.edition_canon_books.items()
}
```

This is functionally identical to the finder's fix but avoids calling `config.load_books()` twice. The finder's fix is otherwise correct and safe; this is a minor efficiency improvement only.

Companion test addition to `tests/test_scripts.py` (mirrors the finder's suggestion, no changes needed to the fix itself):
```python
def test_customize_data_edition_canon_books_canonical_order(self):
    d = self.web.api_customize_data()
    cb = d["edition_canon_books"]
    et = cb["ethiopian-tewahedo"]
    assert et.index("gen") < et.index("mat") < et.index("rev")
```
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently confirmed by reading the cited code:

1. `YHWH v2.4/scripts/web_editions.py:335` contains exactly `edition_canon_books = {ed_id: sorted(books) for ed_id, books in _mtx.edition_canon_books.items()}`. Python `sorted()` on a `set[str]` of book codes yields alphabetical order (1ch, 1co, gen, mat, rev...).

2. The comment at lines 303-307 of the same function explicitly states the canonical-order rule from RULES §6.1 and that "the UI reads the order from this payload — never sorts on its own — so the canonical-order rule has one source of truth." Line 335 directly contradicts this sta …[clipped]
  - skeptic 2 (high, refuted=false): Independently verified all claims:

1. `YHWH v2.4/scripts/web_editions.py:335` does exactly `{ed_id: sorted(books) for ed_id, books in _mtx.edition_canon_books.items()}`. Python `sorted()` on a set of string book-codes produces alphabetical order (1ch, 1co, 1en, 1jn, 1ki…). Confirmed.

2. The comment at lines 303-307 in the same function explicitly states the canonical-order intent and that "The UI reads the order from this payload — never sorts on its own." The implementation directly contradicts this stated invariant. Confirmed.

3. Three JS consumers iterate the list in insertion order with …[clipped]

### 14. [MEDIUM] `aes` notes at KJV chapters 11-16 (roughly 70 notes) are permanently uninjectable: base HTML only has chapter anchors 1-10

- **Dimension:** data-validity (finder said high, recalibrated to medium)
- **Location:** `YHWH v2.4/content/notes/aes.py:204-919`
- **Evidence:**

The base HTML `epub_working/index_split_028.html` has chapter anchors `id="ch-b25-c1"` through `id="ch-b25-c10"` only (verified by grepping — `ch-b25-c11` through `ch-b25-c16` are absent). `inject.py:259` builds `start_marker = f'id="ch-{bxx}-c{ch}"'`; for a note at chapter 11 this becomes `id="ch-b25-c11"`, which is not found, so the note is silently dropped. `coord_in_canonical_extent` in `promote.py:403` validated these notes against the KJV `aes.py` skeleton (which uses LXX chapter numbering 10-16), passing all of chapters 11-16 as valid. But the HTML uses sequential numbering 1-10. `aes.py` line 204 shows the first chapter-11 note: `(11, 11, "", "light", "lang-hebrew", ...)`. Notes at chapters 13, 14, 15, and 16 are also present (confirmed at lines 458, 601, 700, 832). Approximately 70 of the ~90 total `aes` notes are permanently stranded.

- **Fix:** The notes at chapters 11-16 need their chapter coordinates remapped to the HTML sequential scheme (chapters 1-10 → HTML anchors ch-b25-c1 through ch-b25-c10). Determine the mapping: KJV chapter 10 = HTML chapter 10 (the 7th addition, already at end), KJV 11=HTML 1, 12=HTML 2, 13=HTML 3, 14=HTML 4, 15=HTML 5, 16=HTML 6 (or verify via the actual HTML structure). Then rewrite the affected notes tuples with the correct HTML chapter numbers. Additionally, fix the upstream defect in `promote.py:coord_in_canonical_extent` for `aes`: add a pre-promotion check that rejects notes whose chapter is not in `range(1, books.yaml["ch_count"] + 1)` for Strategy-B books where `ch_count` reflects the HTML chapter scheme, not the KJV scheme.
- **Verifier-corrected fix:** The finder's proposed chapter remap (11→1, 12→2, etc.) is wrong and would inject notes at incorrect verse positions. HTML chapter 1 has its own verses 1–22 (Esther narrative); a note remapped to (1, 11, ...) would target verse 11 of the main Esther narrative, not the KJV-ch-11 addition content. The merger is as extended long-verses, not chapter-parallel verse slots.

Safe options:
(a) **Delete the stranded drafts**: Remove all notes at chapters 11–16 from `content/notes/aes.py`. Every one of them contains `[Reviewer: extend this...]` — they are unreviewable stubs with no finished content. Removing them eliminates the false-injection-succeeded impression without losing any finished content. This is the right call for mint quality.

(b) **Add a lint warning**: In `lint_rules.py` (or equivalent), add a check that warns when `aes.py` contains notes at chapters outside the HTML's 1–10 range (i.e., chapters > `books.yaml["aes"].ch_count`). This would have caught this at add-time rather than silently at inject-time.

Do NOT change `promote.py:coord_in_canonical_extent` — it correctly validates against the KJV skeleton (chapters 10–16). The defect is in the note coordinates stored in `content/notes/aes.py`, not in the promote guard. Any future notes for the KJV-ch-11–16 Addition content must be authored with the HTML's merged coordinates: the text appears at HTML aes 1:1 (KJV ch 11), 3 …[clipped]
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): 
**What I independently verified:**

1. `epub_working/index_split_028.html` — confirmed by direct grep: chapter anchors `id="ch-b25-c1"` through `id="ch-b25-c10"` only; `ch-b25-c11` through `ch-b25-c16` are absent.

2. `content/notes/aes.py` — confirmed notes exist at chapters 11 (line 182), 13 (line 226), 14 (line 600), 15 (line 699), 16 (line 831). Count: approximately 68 of 83 total notes are at chapters 11–16.

3. `scripts/inject.py:733` — confirmed: `if f'id="ch-{bxx}-c{ch}"' in text:` uses the note's chapter coordinate verbatim. Notes at ch 11–16 search for `id="ch-b25-c11"` etc., which  …[clipped]
  - skeptic 2 (high, refuted=false): 
**Independently verified** by reading the actual code and HTML.

**Confirmed facts:**

1. `YHWH v2.4/epub_working/index_split_028.html` has anchors `id="ch-b25-c1"` through `id="ch-b25-c10"` and nothing beyond c10. Confirmed by direct grep (10 anchors found, zero for c11+).

2. `YHWH v2.4/content/books.yaml` line 297 confirms `aes` has `ch_count: 10` and `strategy: "B"` and `bxx: "b25"`.

3. `YHWH v2.4/content/notes/aes.py` lines 116–918 contain notes at chapters 11 (lines 116–224), 13 (lines 225–477), 14 (lines 478–675), 15 (lines 676–807), and 16 (lines 808–918). Chapter 10 notes exist at l …[clipped]

### 15. [MEDIUM] ALL_CHECKS registry is 27 checks but every doc/test says 26

- **Dimension:** docs (finder said high, recalibrated to medium)
- **Location:** `YHWH v2.4/tests/test_lint_rules.py:15, 37-38`
- **Evidence:**

Class docstring: `(8 of 26 ALL_CHECKS had no unit test before)` and comment `# Pin the registry size (26 at mint-7) so a check can't be dropped`. The actual `ALL_CHECKS` dict in `scripts/lint_rules.py` (lines 2045–2082) has 27 entries — `bookcode_canonical` was added in mint-7 Phase A, bringing the total to 27. The `>= 26` assertion still passes (27 >= 26) so it provides no protection against a silent drop to exactly 26.

- **Fix:** In `test_lint_rules.py` update the docstring count to 27 and the floor assertion to `>= 27`. Also update the three docs that say '26 checks': `docs/superpowers/plans/2026-05-31-mint-7-quality-pass.md` lines 158 and 176, and `docs/superpowers/plans/2026-05-31-mint-8-audit-plan.md` line 39.
- **Verifier-corrected fix:** In `YHWH v2.4/tests/test_lint_rules.py`:
- Line 15: change "8 of 26 ALL_CHECKS" → "8 of 27 ALL_CHECKS"
- Line 36: change comment "(26 at mint-7)" → "(27 at mint-7 after bookcode_canonical)"
- Line 38: change `>= 26` → `>= 27`

In `YHWH v2.4/docs/superpowers/plans/2026-05-31-mint-7-quality-pass.md`:
- Line 158: "runs all 26 ALL_CHECKS" → "runs all 27 ALL_CHECKS"
- Line 176: "8 of 26 ALL_CHECKS" → "8 of 27 ALL_CHECKS"

In `YHWH v2.4/docs/superpowers/plans/2026-05-31-mint-8-audit-plan.md`:
- Line 39: "26 checks incl. the mint-7 bookcode_canonical" → "27 checks (bookcode_canonical added in mint-7 Phase A)"

No other files need touching. This fix is entirely within tests and docs — it does not touch any build pipeline, marathon core, or KJV output paths.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently verified by reading the source files directly.

`C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\lint_rules.py` lines 2045–2082: ALL_CHECKS contains exactly 27 key-value entries (counted manually: "6.1", "6.2", "encode_decode", "docs", "repo_map_complete", "superpowers_coherence", "freshness", "truth_record_budget", "commercial_orphans", "commercial_terms", "retired_terms", "triad_plan_consistency", "stray_artifacts", "changelog_size", "dev_doc_sprawl", "rules_no_frozen_stats", "inflight", "untracked_phases", "code_doc_sync", "ephemeral_doc_pins", "atomic_writes", "exte …[clipped]
  - skeptic 2 (high, refuted=false): Independently confirmed all three claims in the finding:

1. `ALL_CHECKS` in `YHWH v2.4/scripts/lint_rules.py` lines 2045–2082 has exactly 27 entries — a grep for the entry pattern returns count=27. The last entry `"bookcode_canonical": check_book_codes_canonical` was added in mint-7 Phase A (comment at line 2079 says "mint-7 ★BUGCLUSTER").

2. `YHWH v2.4/tests/test_lint_rules.py` line 15 docstring reads "8 of 26 ALL_CHECKS had no unit test before" and line 38 asserts `len(self.mod.ALL_CHECKS) >= 26`. Both are stale: the real count is 27, not 26, so the floor would not catch a silent regressio …[clipped]

### 16. [MEDIUM] Mint-cleanup plan status still says 'Phase 6 active'; arc is COMPLETE

- **Dimension:** docs
- **Location:** `YHWH v2.4/docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md:2`
- **Evidence:**

`**Status:** in progress — Phases 0–5 shipped; Phase 6 (polish) active`. SESSION_STATE headline (confirmed 2026-05-31) reads: '✅ ALL PHASES 0–6 COMPLETE — the mint-cleanup arc is DONE (2026-05-31, HEAD ad945f62)'. The INDEX.md mirrors this stale status in the 'In progress' table at line 15. The `check_superpowers_coherence` lint checks structural presence of the Status header but does not validate semantic currency, so this drift is invisible to the linter.

- **Fix:** Update `Status:` to `COMPLETE — all Phases 0–6 shipped + synced 2026-05-31 (HEAD ad945f62)`. This will also fix the INDEX.md mirror once the lint coherence check re-runs (or update INDEX.md directly if it's manually maintained).
- **Verifier-corrected fix:** In `YHWH v2.4/docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md` line 2, change: `**Status:** in progress — Phases 0–5 shipped; Phase 6 (polish) active` to: `**Status:** COMPLETE — all Phases 0–6 shipped + synced 2026-05-31 (HEAD ad945f62)`. Then regenerate INDEX.md (or manually update line 15) to match — the INDEX.md entry for this plan is in the "In progress" table and must move to a "Complete" section with the updated status string. The lint check will then reflect clean truth. The proposed fix is correct and safe.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Confirmed by direct reading of both files. Line 2 of `YHWH v2.4/docs/superpowers/plans/2026-05-29-mint-cleanup-and-guardrails.md` reads exactly: `**Status:** in progress — Phases 0–5 shipped; Phase 6 (polish) active`. Line 15 of `YHWH v2.4/docs/superpowers/INDEX.md` mirrors that same stale status string verbatim. MEMORY.md and SESSION_STATE both declare all Phases 0–6 complete as of 2026-05-31 (HEAD ad945f62). The `check_superpowers_coherence` lint in `scripts/lint_rules.py` (lines 1351–1396) only checks: (a) presence of a `**Status:**` header in the first 25 lines via `_SUPERPOWERS_STATUS_RX` …[clipped]

### 17. [MEDIUM] RSS feed: note body_html injected raw into CDATA — stored XSS + XML injection

- **Dimension:** security (finder said high, recalibrated to medium)
- **Location:** `YHWH v2.4/scripts/core/verse_of_day.py:328-336`
- **Evidence:**

body_html = (headline_note or {}).get("body_html") or ""
...
description = (
    f"<p><strong>{_xml_escape(ref)}</strong></p>"
    + (f"<p><em>{_xml_escape(label)}</em></p>" if label else "")
    + (body_html if body_html else "")   # ← RAW, no sanitize_html call
)
...
f"      <description><![CDATA[{description}]]></description>\n"

body_html is taken directly from notes_payload (line 230: "body_html": spec.body_html or ""), which is the raw stored note body. Two concrete impact paths: (1) A note body containing ]]> prematurely closes the CDATA section, allowing arbitrary XML element injection into the RSS feed (fabricated <item> entries, rogue <link>, etc.). (2) A note body containing <script> or javascript: URLs passes unfiltered to any RSS reader that renders description HTML as markup. Neither sanitize_html nor _xml_escape is called on body_html before it enters the CDATA block. All other user-visible data on the same line (ref, label) are correctly _xml_escape'd, making this an inconsistent omission.

- **Fix:** Apply sanitize_html to body_html before interpolating it into the CDATA description:

from scripts.core.html_sanitize import sanitize_html
...
body_html = sanitize_html((headline_note or {}).get("body_html") or "")

Alternatively, since CDATA does not protect against ]]> within the content, also replace ]]> in the result: body_html_safe = sanitize_html(body_html).replace("]]>", "]]&gt;"). Mirror the sanitize_html calls already present in preview.py:133-135 and web_content.py:373 for the same note body field.
- **Verifier-corrected fix:** In YHWH v2.4/scripts/core/verse_of_day.py, replace line 328:

    body_html = (headline_note or {}).get("body_html") or ""

with:

    from scripts.core.html_sanitize import sanitize_html
    body_html_raw = (headline_note or {}).get("body_html") or ""
    body_html = sanitize_html(body_html_raw).replace("]]>", "]]&gt;")

The replace("]]>", "]]&gt;") step handles the XML-injection vector independently of what sanitize_html produces (it does not itself escape ]]>). The import can be placed at the top of the file alongside other core imports rather than inline. This mirrors the existing calls at preview.py:133-135 and web_content.py:373, touches no marathon-core files, and has zero effect on the KJV EPUB build path.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently verified by reading the code directly. In YHWH v2.4/scripts/core/verse_of_day.py lines 328-336, body_html is extracted from the notes payload (which stores spec.body_html verbatim) and interpolated raw into a CDATA block at line 336: `+ (body_html if body_html else "")`, which then lands in `f"<description><![CDATA[{description}]]></description>"` at line 345. No sanitize_html call occurs anywhere in this path. This is confirmed inconsistent: preview.py:133-135 and web_content.py:373 both call sanitize_html() on the same body_html field from the same note store. The RSS feed is a …[clipped]
  - skeptic 2 (high, refuted=false): Independently confirmed by reading the code:

1. `/YHWH v2.4/scripts/core/verse_of_day.py` line 328 retrieves `body_html` raw from the notes payload (which itself is sourced from `spec.body_html` — the stored note body, not sanitized at ingest time).

2. Line 336 interpolates it directly into `description` without any sanitization.

3. Line 345 wraps `description` in `<![CDATA[...]]>`. This CDATA wrapper does NOT protect against `]]>` appearing inside the body content — that sequence would prematurely close the CDATA section, allowing injection of arbitrary XML into the RSS feed (extra `<item> …[clipped]

### 18. [MEDIUM] Stored-XSS in /sources console: truncateHTML returns raw note body HTML when ≤240 stripped chars

- **Dimension:** security (finder said high, recalibrated to medium)
- **Location:** `YHWH v2.4/scripts/templates/sources.py:592-596`
- **Evidence:**

```js
function truncateHTML(html, n) {
  const stripped = (html || '').replace(/<[^>]+>/g, '');
  if (stripped.length <= n) return html;   // ← returns raw, unescaped HTML
  return escapeHTML(stripped.slice(0, n)) + '...';
}
```
This return value is used directly in an `innerHTML` template literal (line 559): `<div ...>${truncateHTML(n.body, 240)}</div>`. The `n.body` value comes from `api_sources_for_book` (web_sources.py:134) which returns the raw on-disk note body with no sanitization. Any note body with ≤240 stripped characters containing e.g. `<img src=x onerror=...>` will execute as DOM XSS. Event-handler attributes fire under nonce-CSP because the nonce only gates `<script>` elements, not `on*` handlers. Note bodies are publisher-authored plus AI-authored and are never sanitized before reaching this frontend path.

- **Fix:** Replace the raw-return branch with an escaped return: `if (stripped.length <= n) return escapeHTML(stripped);`. This matches the existing escaped branch for longer bodies. Alternatively, pass the short body through the same `escapeHTML` path unconditionally and accept that HTML markup is displayed as literal text in the truncated preview (the body_preview in the audit console already does this — see audit.py:240 `${escapeHTML(n.body_preview)}`). The sanitize_html backend sanitizer is NOT the right fix here because it is deliberately not called for this read path — the fix must be in the frontend helper.
- **Verifier-corrected fix:** Replace line 595 in `/YHWH v2.4/scripts/templates/sources.py`:

```js
// Before (unsafe for short bodies):
if (stripped.length <= n) return html;

// After (consistent with the truncated-body branch):
if (stripped.length <= n) return escapeHTML(stripped);
```

This matches the existing behavior for longer bodies (which already return `escapeHTML(stripped.slice(0, n)) + '...'`) and is safe — no marathon core touch, no KJV build impact.

The trade-off: `<strong>/<em>/<b>` formatting in short note bodies will no longer render as rich text in the sources console; they display as plain text. This is acceptable because: (a) the sources console is a publisher-review tool, not a presentation layer; (b) the `audit.py` console already uses this exact plain-text approach for previews; (c) the KJV EPUB output is unaffected (build pipeline does not use `truncateHTML`).

Note: the finder's claim that a "nonce-CSP" mitigates this is incorrect — there is no CSP at all in this codebase — but that absence does not change the fix recommendation.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently verified all cited code:

1. `truncateHTML` at `/YHWH v2.4/scripts/templates/sources.py` lines 592-596 is confirmed exactly as the finder quotes: the early-return branch at line 595 returns raw `html` (the unescaped note body) when stripped length ≤ 240.

2. Line 559 is confirmed: `<div class="text-sm text-slate-700 mt-1">${truncateHTML(n.body, 240)}</div>` inside a template literal that feeds `area.innerHTML = ...` at line 535.

3. `web_sources.py:134` (`body` key) confirms the raw on-disk value is passed with no sanitization.

4. The `audit.py:240` asymmetry is confirmed: the a …[clipped]
  - skeptic 2 (high, refuted=false): Independently verified all three claims:

1. CODE MATCHES EVIDENCE. Line 595 of `YHWH v2.4/scripts/templates/sources.py` reads `if (stripped.length <= n) return html;` — the raw, unescaped body HTML is returned. Line 559 assigns it to `innerHTML` via a template literal. Both confirmed by direct read.

2. THE RAW PATH IS REACHABLE IN PRACTICE. `web_sources.py` lines 113–134 pass `body` straight from the on-disk tuple into the JSON response with no sanitization call (no `sanitize_html`, no bleach, no escaping). Note bodies in `content/notes/*.py` contain real HTML (`<strong>`, `<em>`, `<a href=" …[clipped]

### 19. [MEDIUM] RSS feed embeds unsanitized note body_html inside CDATA description block

- **Dimension:** security
- **Location:** `YHWH v2.4/scripts/core/verse_of_day.py:328-336`
- **Evidence:**

```python
body_html = (headline_note or {}).get("body_html") or ""
description = (
    f"<p><strong>{_xml_escape(ref)}</strong></p>"
    + ...
    + (body_html if body_html else "")   # ← raw note body, no sanitize_html
)
# ...
f"      <description><![CDATA[{description}]]></description>\n",
```
`body_html` comes from `NoteSpec.body_html` (config.py:102 `body_html=tup[7]`) which is the raw stored note body. `sanitize_html` is called at the preview and sample-html render paths but NOT here. An RSS reader that renders the CDATA description as HTML (all major RSS readers do) will execute any injected `<script>` or event-handler content in the note body.

- **Fix:** Apply `sanitize_html` before interpolating the body into the description: `from scripts.core.html_sanitize import sanitize_html` then `body_html = sanitize_html((headline_note or {}).get('body_html') or '')`. This mirrors the approach used in `_render_note_aside` (preview.py:133-135) and `_render_sample_html` (web_content.py:373). The sanitizer preserves intended markup (`<em>`, `<a>`, `<strong>`, etc.) while stripping scripts and event handlers.
- **Verifier-corrected fix:** In C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\core\verse_of_day.py, add the import at the top of `rss_feed` (or at module level alongside the other core imports) and sanitize before interpolation:

At line 328, change:
    body_html = (headline_note or {}).get("body_html") or ""

To:
    from scripts.core.html_sanitize import sanitize_html  # add once at module top
    body_html = sanitize_html((headline_note or {}).get("body_html") or "")

Or as a module-level import alongside the existing ones (lines 38–40):
    from . import html_sanitize

Then at line 328:
    body_html = html_sanitize.sanitize_html((headline_note or {}).get("body_html") or "")

This exactly mirrors the approach in preview.py lines 133–135. No other changes needed; the fix is confined to verse_of_day.py and has no effect on EPUB build output.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Verified by direct reading of C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\core\verse_of_day.py lines 328–345. At line 228–230 (inside `pick_verse_for_date`) `body_html` is taken straight from `spec.body_html` (NoteSpec field 7, raw stored value) and packed into the notes payload dict without sanitization. At line 328 it is extracted from that dict and at line 336 inserted literally into `description`, which is then wrapped in `<![CDATA[...]]>` at line 345. No call to `sanitize_html` exists anywhere in verse_of_day.py (grep confirmed zero hits). `notes_io.py` also has no sanitize  …[clipped]

### 20. [MEDIUM] test_by_verse_empty_for_unknown assumes mat 1:1 has no patristic commentary (state-default violation, §8)

- **Dimension:** tests
- **Location:** `YHWH v2.4/tests/test_patristic_gamma3.py:134-140`
- **Evidence:**

```python
def test_by_verse_empty_for_unknown(self):
    pc = sources.patristic_commentaries()
    # Matthew has no seed commentary yet
    empty = pc.for_verse("mat", 1, 1)
    assert empty == []
```
This is a classic §8 violation: the test assumes `mat 1:1` is empty TODAY as a proxy for 'unknown verse returns []'. It encodes present world-state as a permanent contract. As soon as any future γ.3.x adds a Matthew commentary (the class docstring says 'No NT verses in the seed yet' — explicitly acknowledging this is temporary), this test flips from a legitimate empty-list contract to a false positive that breaks on the first NT expansion. The mutation that proves this is tautological: add a single `mat 1:1` entry to `patristic_commentaries.json` — the test fails immediately even though `for_verse` still correctly returns a list.

- **Fix:** Per §8, test the contract against state the test controls, not world state that can change. Replace the specific-verse check with a genuinely-unknown probe:
```python
def test_by_verse_empty_for_unknown(self):
    pc = sources.patristic_commentaries()
    # Use a coordinate that cannot exist in any real corpus:
    # a non-existent book code is the state-invariant empty case.
    empty = pc.for_verse("nonexistent-book-xyz", 99, 99)
    assert empty == [], f"for_verse on a non-corpus book must return []; got {empty}"
```
This mirrors the pattern already correctly used in `TestGamma4EthiopianCommentariesLoader.test_by_verse_empty_for_unknown` (line 167-168 of test_ethiopian_gamma4.py) which uses `'nonexistent-book-xyz'`.
- **Verifier-corrected fix:** Fix both state-default violations in the same edit to C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\tests\test_patristic_gamma3.py:

1. test_by_verse_empty_for_unknown (line 134-140) — replace the mat 1:1 probe with a structurally impossible coordinate, mirroring the Ethiopian pattern:

    def test_by_verse_empty_for_unknown(self):
        from scripts.core import sources

        pc = sources.patristic_commentaries()
        # Use a coordinate that cannot exist in any real corpus — a non-corpus
        # book code is the state-invariant empty case (§8: test the contract,
        # not present world-state).
        empty = pc.for_verse("nonexistent-book-xyz", 99, 99)
        assert empty == [], f"for_verse on a non-corpus book must return []; got {empty}"

2. test_by_father_empty_for_unknown (line 150-156) — same fix for the Origen probe:

    def test_by_father_empty_for_unknown(self):
        from scripts.core import sources

        pc = sources.patristic_commentaries()
        # Use a father name that cannot appear in any real corpus (§8).
        empty = pc.by_father("nonexistent-father-xyz")
        assert empty == []

No other files need changing. The fix is additive-safe and has no effect on build output.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Confirmed by reading C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\tests\test_patristic_gamma3.py lines 134-140 and the seed file C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\content\sources\patristic_commentaries.json.

The JSON seed contains zero entries with "book": "mat" (grep confirmed 0 matches). The test comment explicitly states "Matthew has no seed commentary yet", acknowledging this is transient world-state, not a permanent contract. The _meta block says "scope: Curated interpretive summaries verse-keyed to Genesis 1-3" — NT coverage is intended to arrive in a future γ.3.x.  …[clipped]

### 21. [LOW] build_cache.compute_cache_key omits epub_working/META-INF/ subdirectory from its hash, so container.xml changes do not invalidate the cache

- **Dimension:** byte-stability (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/scripts/core/build_cache.py:239-248`
- **Evidence:**

`for entry in sorted(epub_dir.iterdir(), key=lambda p: p.name): if entry.is_file() and not entry.name.startswith("."):` — `iterdir()` is non-recursive and `entry.is_file()` skips subdirectories. `epub_working/META-INF/container.xml` (the EPUB container declaration) and any future subdirectory assets (e.g. `epub_working/images/`) are never hashed. A change to `container.xml` would produce the same cache key and silently serve a stale EPUB.

- **Fix:** Replace the shallow `iterdir()` scan with a recursive `rglob('*')` scan, applying the same `should_skip` logic as `build_epub.collect_files` (i.e. excluding dotfiles and `onix/`): `for entry in sorted(epub_dir.rglob('*'), key=lambda p: str(p.relative_to(epub_dir))): if entry.is_file() and not any(part.startswith('.') for part in entry.relative_to(epub_dir).parts) and 'onix' not in entry.relative_to(epub_dir).parts: parts.append((f'epub:{entry.relative_to(epub_dir).as_posix()}', _hash_file(entry)))`
- **Verifier-corrected fix:** The proposed `rglob('*')` replacement is safe and correct if you want to close the gap defensively. A minimal, lower-noise variant that mirrors the existing dotfile-skip logic already present in the shallow scan:

```python
# 10. Templated EPUB input (epub_working/) — recursive to catch META-INF/container.xml.
epub_dir = _REPO / "epub_working"
if epub_dir.is_dir():
    for entry in sorted(epub_dir.rglob("*"), key=lambda p: str(p.relative_to(epub_dir))):
        if not entry.is_file():
            continue
        rel = entry.relative_to(epub_dir)
        # Skip dotfile dirs (.backups/) and the onix/ tree (excluded from EPUB packaging).
        if any(part.startswith(".") or part == "onix" for part in rel.parts):
            continue
        parts.append((f"epub:{rel.as_posix()}", _hash_file(entry)))
```

This matches the exclusions that `build_epub.py`'s `collect_files` applies (dotfiles + `onix`), keeping the cache key aligned with actual EPUB content. That said, given `container.xml` has no write path in the codebase, this fix can legitimately be deferred until a future change introduces a subdirectory that IS build-modified.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): The code at lines 239-248 of YHWH v2.4/scripts/core/build_cache.py is exactly as described: a shallow `epub_dir.iterdir()` with `entry.is_file()` guard that skips all subdirectories. `epub_working/META-INF/container.xml` exists on disk, is not excluded by any of `build_epub.py`'s `EXCLUDE_DIR_NAMES` or `EXCLUDE_PREFIXES`, and IS packaged into the final EPUB via `collect_files`'s `rglob`. So the structural gap is confirmed: a change to `container.xml` would not invalidate the cache key.

However, the severity is materially overstated. Across the entire codebase, zero scripts write to `container …[clipped]

### 22. [LOW] iter_target_verses and resolve_books duplicated byte-for-byte across both AI at-scale drivers

- **Dimension:** code-debt (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/scripts/run_ai_notes_at_scale.py:117-147, 298-305`
- **Evidence:**

run_ai_notes_at_scale.py lines 117-147 and 298-305 are byte-identical to run_ai_xrefs_at_scale.py lines 119-146 and 292-299. The notes-driver docstring even says 'Mirrors run_ai_xrefs_at_scale.iter_target_verses — kept separate to allow per-driver targeting filters in the future.' This is the same copy-then-diverge pattern that caused the silent ch_count/'chapters' bug fixed in mint-7 B1 (the fix comment 'mint-7 B1: books.yaml key is ch_count' appears in both copies at lines 132-134 of xrefs and 133-135 of notes). A future fix applied to one copy will silently miss the other.

- **Fix:** Add iter_target_verses(books, max_verses) and resolve_books(books_arg) to scripts/core/at_scale_base.py (which already owns candidate_to_dict, NT_BOOKS, and the ANSI constants for the same reason). Both AI drivers then import from there. The notes-driver docstring rationale ('allow per-driver targeting filters in the future') is not a blocker — per-driver overrides can always shadow the base function locally when that future need actually arrives.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently verified by reading both files. The two functions iter_target_verses (notes: lines 117-147, xrefs: lines 119-146) and resolve_books (notes: lines 298-305, xrefs: lines 292-299) are byte-identical between the two drivers, differing only in the notes-driver docstring which explicitly calls out the duplication. The mint-7 B1 fix comment ('mint-7 B1: books.yaml key is ch_count') appears identically in both copies at exactly the lines cited. at_scale_base.py already exists and was created in mint-7 D1 for exactly this de-duplication pattern (candidate_to_dict, NT_BOOKS, ANSI constants …[clipped]

### 23. [LOW] scripts/bulk_edit.py auto-verify subprocess.run missing stdin=subprocess.DEVNULL — WinError 6 on Windows

- **Dimension:** concurrency-caching (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/scripts/bulk_edit.py:189-192`
- **Evidence:**

result = subprocess.run(
    [sys.executable, str(REPO_ROOT / 'scripts' / 'verify.py'), '--quiet'],
    cwd=str(REPO_ROOT),
)

The --apply path of bulk_edit.py auto-runs verify.py as a subprocess after mutations. No stdin=subprocess.DEVNULL. Launched from PowerShell (the dev workflow), this will hit WinError 6. The tool is used for corpus edits so this hits in normal editorial use.

- **Fix:** Add stdin=subprocess.DEVNULL:

result = subprocess.run(
    [sys.executable, str(REPO_ROOT / 'scripts' / 'verify.py'), '--quiet'],
    cwd=str(REPO_ROOT),
    stdin=subprocess.DEVNULL,  # W-W1: Windows PowerShell guard
)
- **Verifier-corrected fix:** result = subprocess.run(
    [sys.executable, str(REPO_ROOT / "scripts" / "verify.py"), "--quiet"],
    cwd=str(REPO_ROOT),
    stdin=subprocess.DEVNULL,  # W-W1: Windows/PowerShell guard
)
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Read C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\bulk_edit.py lines 189-192 directly. The subprocess.run call is exactly as quoted — no stdin= argument, no DEVNULL anywhere in the file (grep confirmed zero matches). The project's W-W1 rule (in memory) is explicit: every subprocess.run on Windows/PowerShell must pass stdin=subprocess.DEVNULL or hits WinError 6. The call is on the hot --apply path used in normal editorial corpus work, not dead code. verify.py itself uses stdin=subprocess.DEVNULL for its own sub-calls (line 38), but that does not protect the outer invocation from bu …[clipped]

### 24. [LOW] promote.py batch_insert_notes breaks sort order for notes at the same chapter/verse when existing list is not in sorted order

- **Dimension:** correctness (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/scripts/promote.py:339-343`
- **Evidence:**

```python
for ech, ev, esuf, eend in existing:
    if (ech, ev, suffix_rank(esuf)) < new_key:
        after = eend
    else:
        break
```
The loop uses `break` on the first tuple that does NOT sort before `new_key`, assuming `existing` is sorted ascending. If any existing note tuple in the file is out of sort order (e.g., from a prior bulk edit that skipped sorting), `break` fires prematurely and the insertion point is set too early — notes land before already-existing tuples whose sort key is lower. Silent: no error, wrong order on disk.

- **Fix:** Change the `break` to `continue` so ALL existing tuples are scanned regardless of order, keeping `after = eend` only when `(ech, ev, suffix_rank(esuf)) < new_key`. Or add a pre-sort of `existing` by `(ech, ev, suffix_rank(esuf))` before the loop to make the early-exit safe.
- **Verifier-corrected fix:** In `batch_insert_notes` (line 343), change `break` to `continue` so all existing tuples are scanned regardless of file order:

```python
for ech, ev, esuf, eend in existing:
    if (ech, ev, suffix_rank(esuf)) < new_key:
        after = eend
    # no break — scan all tuples; file may not be perfectly sorted
```

Apply the identical fix to `insert_note_into_book_file` at line 248-249, which has the same pattern:

```python
        if existing_key < new_key:
            insert_after_lineno = tup.end_lineno
        # no break — scan all tuples
```

Both changes are safe: no marathon-core files are touched, schema is unchanged, the 9 KJV editions carry no notes-file dependency so byte-stability is unaffected. An alternative is to pre-sort `existing` by `(ch, v, suffix_rank(esuf))` before the loop (restoring the correctness of the early-exit), but the `continue` approach is simpler and equally correct.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): The code at `YHWH v2.4/scripts/promote.py` lines 339-343 is exactly as described. `existing` is populated by walking AST elements in file order (lines 310-320); there is no pre-sort before the loop. The `break` at line 343 fires on the first tuple whose sort key is not strictly less than `new_key`, which is only a correct early exit if `existing` is sorted ascending. No lint guard in `check_content.py` or elsewhere enforces or verifies sort order of notes tuples on disk. The identical pattern exists in `insert_note_into_book_file` at lines 246-249, which the finder did not cite.

However, the  …[clipped]

### 25. [LOW] write_book always emits 9th attribution field as `{}` for legacy 8-tuple notes, converting them to 9-tuples with a dict value that violates the str | None contract

- **Dimension:** correctness (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/scripts/web_helpers.py:174`
- **Evidence:**

```python
attribution = rest[0] if rest else {}
...
lines.append(f"        {attribution!r},\n")
```
For any note tuple with < 9 fields (`rest == []`), `attribution = {}`. Every note the web UI writes back to disk (even 8-tuple legacy notes) gains a 9th field `{}`. `NoteSpec.from_tuple(tup)` then stores `attribution = {}` (a dict) instead of `None` because `isinstance({}, str)` is False, breaking the dataclass type annotation. Code downstream that calls `spec.attribution.strip()` (e.g. future note-quality checks) would raise `AttributeError: 'dict' object has no attribute 'strip'`.

- **Fix:** Use `attribution = rest[0] if rest else None` (or `""`) and conditionally omit the 9th field when attribution is falsy: `if attribution: lines.append(f"        {attribution!r},\n")`. This preserves the 8-tuple legacy form for notes without attribution, matching how `promote.py`'s `format_tuple_text` handles it.
- **Verifier-corrected fix:** Fix all three cooperating sites in `YHWH v2.4/scripts/web_helpers.py`:

1. `tuple_to_dict` (line 131): change `"attribution": attribution or {}` to `"attribution": attribution or None` — the dict should carry `None` for absent attribution, not `{}`.

2. `dict_to_tuple` (line 146): change `d.get("attribution") or {}` to `d.get("attribution") or None` — this makes the returned tuple an 8-tuple when attribution is absent, matching the legacy form.

3. `write_book` (lines 174 + 182): change `attribution = rest[0] if rest else {}` to `attribution = rest[0] if rest else None`, then make the 9th field conditional — only emit it when truthy, matching `promote.py`'s `format_tuple_text` contract:

```python
attribution = rest[0] if rest else None
lines.append("    (\n")
lines.append(f"        {ch}, {v}, {suffix!r},\n")
lines.append(f"        {anchor!r},\n")
lines.append(f"        {kind!r},\n")
lines.append(f"        {title!r},\n")
lines.append(f"        {label!r},\n")
lines.append(f"        {body!r},\n")
if attribution:
    lines.append(f"        {attribution!r},\n")
lines.append("    ),\n")
```

This trims the spurious `{}` 9th field from all unattributed notes on the next web-UI save, restoring them to the 8-tuple legacy form and aligning `write_book` with the project-wide contract expressed in `promote.py:format_tuple_text` and `NoteSpec.to_tuple`. The 9 KJV editions are unaffected (b …[clipped]
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): The finding is confirmed by reading the code directly. Three cooperating defects form the bug cluster:

1. `web_helpers.py:174` — `attribution = rest[0] if rest else {}`: for any legacy 8-tuple (rest=[]), `attribution = {}`. Line 182 then unconditionally writes `{!r}` as the 9th field, converting every legacy note touched by the web UI.

2. `web_helpers.py:146` (dict_to_tuple) — `d.get("attribution") or {}`: when the API form submits an absent/empty attribution, the resulting tuple gets `{}` as 9th field rather than being an 8-tuple.

3. `web_helpers.py:131` (tuple_to_dict) — `"attribution": a …[clipped]

### 26. [LOW] prospect.py and all run_*_at_scale.py write_queue functions use non-atomic writes for candidate JSON files

- **Dimension:** correctness (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/scripts/prospect.py:152`
- **Evidence:**

`out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")` — a direct non-atomic write. The same pattern is copy-pasted across run_naves_at_scale.py:67, run_greek_at_scale.py:60, run_hebrew_at_scale.py:61, run_xref_at_scale.py:66, run_torrey_at_scale.py:65, run_kenyon_at_scale.py:95, run_ethiopian_at_scale.py:76, and others. If the process is interrupted mid-write (Ctrl-C, OOM kill), the JSON file is corrupt. The append-merge pattern in run_naves_at_scale.py's write_queue reads the existing file first — a corrupt existing file is silently caught (`except Exception: existing = []`) and lost.

- **Fix:** Replace with `notes_io.atomic_write(out_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")` in all write_queue functions. The `atomic_write` primitive is already imported or available in every script. This is a one-line change per file and matches the pattern used for notes files.
- **Verifier-corrected fix:** In each of the 8 affected files, add `from scripts.core.notes_io import atomic_write` to the imports block (alongside the existing `from scripts.core...` imports), then replace each `out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")` with `atomic_write(out_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")`. The `+ "\n"` matches the pattern already used in promote.py's atomic_write call for the same files. prospect.py already imports from scripts.core but not notes_io, so it needs the same addition. This is otherwise correct and safe — no marathon core files touched, no EPUB output affected, no schema changes.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): All cited write_text calls are confirmed by direct reading: prospect.py:152, run_naves_at_scale.py:67, run_greek_at_scale.py:60, run_hebrew_at_scale.py:61, run_xref_at_scale.py:66, run_torrey_at_scale.py:65, run_kenyon_at_scale.py:95, run_ethiopian_at_scale.py:76 — all use direct Path.write_text rather than atomic_write. None of the run_*_at_scale.py files import notes_io (verified by reading their import blocks). The append-merge scripts (run_naves, run_greek, run_hebrew, run_xref, run_torrey, run_kenyon, run_ethiopian) read the existing file first and suppress corrupt-parse errors with a bro …[clipped]

### 27. [LOW] batch_insert_notes silently drops notes whose chapter/verse key is absent from the input dict

- **Dimension:** correctness
- **Location:** `YHWH v2.4/scripts/promote.py:325-330`
- **Evidence:**

Lines 325-326: `ch = n.get("chapter", n.get("ch"))` / `v = n.get("verse", n.get("v"))`. If neither key is present, `ch = None`. Line 330: `if not coord_in_canonical_extent(book_path.stem, None, v): continue`. Inside that function, `canonical_book_shape` returns `{int: int}`, and `None in shape` is always `False`, so the function returns `False` and the note is silently skipped. No warning is emitted. In practice, all current callers supply the correct keys, but a future caller or a malformed candidate dict would cause silent data loss.

- **Fix:** Add an explicit guard before line 330: `if ch is None or v is None: continue  # malformed candidate dict — log at DEBUG`. Optionally emit a warning so the operator knows a candidate was skipped.
- **Verifier-corrected fix:** At `YHWH v2.4/scripts/promote.py` line 329 (immediately after `attribution = n.get("attribution")`), insert:

```python
if ch is None or v is None:
    import warnings
    warnings.warn(
        f"batch_insert_notes: skipping note missing chapter/verse keys: {n!r}",
        stacklevel=2,
    )
    continue
```

This makes the silent skip visible without altering any existing behavior. Using `warnings.warn` (rather than a bare `print`) is consistent with the project's pattern for operational warnings in library functions and does not require a logging dependency. No changes to marathon core; no effect on the 9 KJV edition outputs.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Verified by reading the actual code. Lines 325-326 of `YHWH v2.4/scripts/promote.py` do exactly what the finder claims: `ch = n.get("chapter", n.get("ch"))` yields `None` if neither key is present. Line 330 then calls `coord_in_canonical_extent(book_path.stem, ch, v)` with `ch=None`. In `scripts/core/canonical_verse_counts.py` line 172, the guard is `return chapter in shape and 1 <= verse <= shape[chapter]` — `None in {int: int}` is always `False`, so the function returns `False` and the note is skipped silently via `continue` at line 331, with no log or warning.

All current callers supply th …[clipped]

### 28. [LOW] `add_note.py` chapter-range guard uses `books.yaml ch_count` instead of `coord_in_canonical_extent`, causing wrong accept/reject for `aes` and silently wrong accept for other non-standard-start books

- **Dimension:** data-validity (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/scripts/add_note.py:309-310`
- **Evidence:**

`if book.get("ch_count", 0) > 0 and (args.ch < 1 or args.ch > book["ch_count"]): err(...)`. For `aes` with `ch_count: 10` in books.yaml, chapters 11-16 are rejected (correct — they have no HTML anchor), but chapters 1-9 are accepted (wrong — `aes` in the HTML does have those anchors but the KJV skeleton has no such content; however all of ch 1-9 exist as HTML anchors in the base HTML per `index_split_028.html`). The more material asymmetry is that `promote.py:403` uses `coord_in_canonical_extent` (allowing ch 11-16 through) while `add_note.py` uses `ch_count` (blocking ch 11-16). These two entry-points apply inconsistent validation rules for the same book, causing the corpus to accumulate notes at ch 11-16 (via promote) that the manual tool cannot add (via add_note). The CHANGELOG at line 1801 notes the scope of the original guard: "corpus-wide scan → 0 invalid-coordinate notes" — this relied solely on the KJV-skeleton check and did not catch the HTML-anchor mismatch.

- **Fix:** Unify the chapter validation at the promote boundary: in `promote_candidate` (promote.py:403) and `batch_insert_notes` (promote.py:330), add a secondary check using `books.yaml ch_count` for Strategy-B books: `if book_ch_count > 0 and chapter > book_ch_count: return False`. Load book metadata via `config.get_book(book)`. This makes the promote path consistent with `add_note.py` and stops future notes from landing at chapters beyond the HTML's anchor range. The `add_note.py` guard itself is correct as written; no change needed there.
- **Verifier-corrected fix:** The finder's fix direction is correct but the proposed implementation needs a minor correction: `promote.py` currently has no import of `scripts.core.config`, so `config.get_book(book)` is not available. The cleanest minimal fix adds the `ch_count` guard inline in `promote.py` using a dedicated helper rather than pulling in the full config module.

**Option A (minimal, no new import):** In `scripts/core/canonical_verse_counts.py`, add a thin helper that reads `ch_count` from books.yaml:

```python
@lru_cache(maxsize=256)
def html_chapter_count(book: str) -> int:
    """Return the HTML ch_count for *book* from books.yaml, or 0 if not set.
    This reflects the base-HTML chapter structure, which may differ from the
    KJV skeleton chapter numbering (e.g. aes: HTML uses chs 1-10, KJV uses 10-16)."""
    import yaml, pathlib
    books_yaml = pathlib.Path(__file__).parents[2] / "content" / "books.yaml"
    data = yaml.safe_load(books_yaml.read_text(encoding="utf-8"))
    for b in data.get("books", []):
        if b.get("code") == book:
            return b.get("ch_count", 0)
    return 0
```

Then in `promote.py`, after the existing `coord_in_canonical_extent` import, add:

```python
from scripts.core.canonical_verse_counts import coord_in_canonical_extent, html_chapter_count  # noqa: E402
```

And at `promote_candidate` (line 403) and `batch_insert_notes` (line 330), add a second  …[clipped]
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): I independently verified every factual claim in the finding by reading the actual source files.

**What the code does (verified):**

`YHWH v2.4/scripts/add_note.py` line 309: `if book.get("ch_count", 0) > 0 and (args.ch < 1 or args.ch > book["ch_count"])` — this guards against chapters beyond `ch_count` as stored in `books.yaml`. For `aes`, `ch_count: 10`.

`YHWH v2.4/scripts/promote.py` lines 330 and 403: both use `coord_in_canonical_extent(book, chapter, verse)` from `scripts/core/canonical_verse_counts.py`. That function builds chapter shape from `load_kjv_skeleton()` — the KJV skeleton at  …[clipped]

### 29. [LOW] `books.yaml` `ch_count: 10` for `aes` is misleading: actual HTML has 10 chapters (1-10) but KJV skeleton has 7 chapters (10-16), causing `coverage.py` and `generate_verse_popups.py` to iterate wrong chapter ranges

- **Dimension:** data-validity (finder said info, recalibrated to low)
- **Location:** `YHWH v2.4/content/books.yaml:296-302`
- **Evidence:**

`aes` entry: `ch_count: 10`. `coverage.py:182` uses `for c in range(1, ch_count + 1)` — this iterates HTML chapters 1-10, which is correct. `generate_verse_popups.py:300` does the same `range(1, ch_count + 1)` — also correct. Both scripts are already aligned with the HTML ch 1-10 scheme. However, `coord_in_canonical_extent` (KJV skeleton ch 10-16) is semantically inconsistent with the HTML ch 1-10 scheme. The `ch_count: 10` is the right value for the HTML-facing tools, but the `_meta.yaml` comment for `aes` at phase τ.7.x.m says `content/books.yaml fixes est at ch_count: 10 (Hebrew/Masoretic core; the Greek Additions are the SEPARATE b25 book)` — this comment conflates `est` and `aes` metadata. The `aes` ch_count commentary is absent. No functional bug in coverage/popup generation — both use the correct HTML chapter range. Informational for future maintainability.

- **Fix:** Add a comment in books.yaml for `aes`: `# ch_count = 10: sequential HTML chapter numbering (ch 1-10 in epub_working); KJV/LXX uses 10-16 which does NOT correspond — do not use coord_in_canonical_extent for aes inject-range validation`. This documents the dual-numbering system so future ingest and promotion code does not re-introduce the ch 11-16 promotion bug.
- **Verifier-corrected fix:** The proposed YAML comment is safe to add as written, but it should also explicitly flag the `coord_in_canonical_extent` no-op. A more complete comment for `content/books.yaml` at the `aes` entry:

```yaml
  - code: aes
    # ch_count = 10: sequential HTML chapter numbering (ch 1-10 in epub_working).
    # KJV/LXX uses ch 10-16; because canonical_verse_counts._book_shape_cached
    # probes from ch=1, canonical_book_shape("aes") returns {} and
    # coord_in_canonical_extent is a no-op for aes (always returns True).
    # Do NOT use coord_in_canonical_extent for aes promote-range validation.
    # Fix if/when aes notes are actively promoted: override the KJV chapter
    # mapping or add aes to TEWAHEDO_DISTINCTIVE_NO_KJV with hand-typed counts.
    ch_count: 10
```

No change to any Python file is required for correctness today (the no-op guard means no notes are silently dropped; the downside is no noise filtering on aes coordinates). If a future ingest ever promotes notes into `aes`, the correct fix is to add `aes` to `TEWAHEDO_DISTINCTIVE_NO_KJV` in `scripts/core/canonical_verse_counts.py` (with hand-typed verse counts for ch 10-16) or implement a ch-offset mapping — but that is additive and can wait until aes promotion is actually needed.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (medium, refuted=false): I independently verified the following:

1. `content/books.yaml` lines 292-300: `aes` has `ch_count: 10`, and the KJV skeleton `content/translations/kjv/aes.py` confirms the KJV data starts at chapter 10 (first tuple is `(10, 4, ...)`) and runs through chapter 16 — 7 KJV chapters total, none of which is chapter 1.

2. `scripts/coverage.py` line 182 and `scripts/generate_verse_popups.py` line 300 both use `range(1, ch_count + 1)`, iterating HTML chapters 1-10. This is correct for the HTML-facing tool layer; confirmed by the finding itself.

3. The real gap, confirmed by reading `scripts/core/ca …[clipped]

### 30. [LOW] MATRIX_MAP and REPO_MAP say 71 kinds; actual kinds.yaml has 72

- **Dimension:** docs (finder said high, recalibrated to low)
- **Location:** `YHWH v2.4/dev/MATRIX_MAP.md:17, 27, 133`
- **Evidence:**

`kinds.yaml` has exactly 72 `- code:` entries (verified by grep count = 72). `test_validate_schemas.py` line 212 correctly pins `assert result['record_count'] == 72` and its comment notes '71 → 72 with Track C Torrey (topic-torrey)'. MATRIX_MAP line 17 states `71 kinds`, line 27 states `kinds.yaml ........ 71 kinds`, and line 133 (Findings item 1) claims the RESOLVED docstring reads `71 kinds / 67,715 notes / 11 editions` — that resolved value itself is now stale. REPO_MAP line 30 states `kinds.yaml (71)`.

- **Fix:** In `MATRIX_MAP.md` update the three occurrences of '71 kinds' to '72 kinds'. In `REPO_MAP.md` line 30 change `kinds.yaml (71)` to `kinds.yaml (72)`.
- **Verifier-corrected fix:** The finder's fix is correct but incomplete. Update four locations:
1. YHWH v2.4/dev/MATRIX_MAP.md line 17: change "71 kinds" to "72 kinds" in the counts parenthetical.
2. YHWH v2.4/dev/MATRIX_MAP.md line 27: change `kinds.yaml ........ 71 kinds` to `kinds.yaml ........ 72 kinds`.
3. YHWH v2.4/dev/MATRIX_MAP.md line 133: the quoted resolved-docstring value `"71 kinds / 67,715 notes / 11 editions"` should be updated to `"72 kinds / 67,715 notes / 11 editions"` to match what matrix.py now actually says.
4. YHWH v2.4/dev/REPO_MAP.md line 30: change `kinds.yaml (71)` to `kinds.yaml (72)`.
No code, schema, or test changes needed. All four are prose-only edits to .md files — zero risk to EPUB byte-stability or marathon core.
- **Adversarial verdict (2 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently verified all claims by reading the source files directly. `kinds.yaml` grep count = 72 confirmed. `test_validate_schemas.py` line 212 asserts `result["record_count"] == 72` with an explicit comment "71 → 72 with Track C Torrey (topic-torrey)". `scripts/core/matrix.py` line 9 already reads "72 kinds" — the docstring was updated. However, MATRIX_MAP.md lines 17 and 27 still contain "71 kinds", and line 133 quotes the now-stale resolved docstring as `"71 kinds / 67,715 notes / 11 editions"`. REPO_MAP.md line 30 still reads `kinds.yaml (71)`. This is a genuine documentation drift: fo …[clipped]
  - skeptic 2 (high, refuted=false): Independently verified all cited locations. kinds.yaml has exactly 72 `code:` entries (grep count = 72), including `topic-torrey` at line 783 which was the 71→72 addition. test_validate_schemas.py line 212 correctly pins `result["record_count"] == 72` with an explicit comment documenting "71 → 72 with Track C Torrey (2026-05-25)". MATRIX_MAP.md line 17 reads "71 kinds", line 27 reads "kinds.yaml ........ 71 kinds", and line 133 states the RESOLVED docstring reads "71 kinds / 67,715 notes / 11 editions" — all three are stale counts. REPO_MAP.md line 30 reads "kinds.yaml (71)" — also stale. The  …[clipped]

### 31. [LOW] Mint-7 plan status says 'execution PENDING' but it is COMPLETE; INDEX puts it in 'In progress'

- **Dimension:** docs (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/docs/superpowers/plans/2026-05-31-mint-7-quality-pass.md:2`
- **Evidence:**

`**Status:** in progress — audit COMPLETE (2026-05-31, 15-agent workflow wf_365eda78); plan written + findings saved; **execution PENDING (start Phase A next session)**.` But SESSION_STATE headline and the plan's own Phase E section (line 157) both confirm `✅ PHASE E (E1/E2/E4 done; E3 shipped) ... COMPLETE — Phases A · C · B · D · E all shipped + synced 2026-05-31`. The INDEX.md `## In progress (9)` section count is also wrong by 1 (mint-7 is done; should be 8 in-progress).

- **Fix:** Update the plan's `Status:` header to `COMPLETE — Phases A · C · B · D · E all shipped + synced 2026-05-31`. Move the mint-7 entry from 'In progress' to 'Shipped' in INDEX.md, and correct the section header from `(9)` to `(8)`.
- **Verifier-corrected fix:** In C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\docs\superpowers\plans\2026-05-31-mint-7-quality-pass.md line 2, replace the entire Status line with: **Status:** COMPLETE — Phases A · C · B · D · E all shipped + synced 2026-05-31 (15-agent audit wf_365eda78). In C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\docs\superpowers\INDEX.md: (a) change "## In progress (9)" to "## In progress (8)"; (b) move the mint-7 table row (the 2026-05-31 Plan row) from the In progress table to the Shipped table. No other files need changing; marathon core and build pipeline are untouched.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Independently verified both cited locations. (1) C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\docs\superpowers\plans\2026-05-31-mint-7-quality-pass.md line 2 still reads "execution PENDING (start Phase A next session)" — stale text that contradicts line 157 onward where every phase (A, B, C, D, E) carries a checkmark and the Phase E block explicitly states "PHASE E … COMPLETE … 2026-05-31". (2) C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\docs\superpowers\INDEX.md line 14 places the mint-7 row under the "## In progress (9)" section header even though its own Status cell already reads …[clipped]

### 32. [LOW] MATRIX_MAP says 13 translation dirs; actual filesystem has 14

- **Dimension:** docs (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/dev/MATRIX_MAP.md:32`
- **Evidence:**

`translations/<id>/ .... 13 dirs` in the CONFIG section header comment. Actual directories under `content/translations/`: kjv, geez-tewahedo, amharic-tewahedo, geez-tewahedo-en, amharic-tewahedo-en, wlc, jps, lxx-brenton-english, lxx-brenton-greek, douay-rheims, vulgate-clementine, arabic-vandyke = 12 with `_meta.yaml`, plus lxx-swete-greek and byzantine-greek (both added during the τ.5/Phase 2 ingest waves, both have _meta.yaml as confirmed by grep) = 14. REPO_MAP line 32 independently says '13 dirs'.

- **Fix:** Update `MATRIX_MAP.md` line 32 from `13 dirs` to `14 dirs`. Update `REPO_MAP.md` line 32 translation dir count from `13 dirs` to `14 dirs`. Also add `lxx-swete-greek` and `byzantine-greek` to REPO_MAP's enumeration of partial pilots.
- **Verifier-corrected fix:** Update the count from 13 to 14 in both places where it appears:

1. `YHWH v2.4/dev/MATRIX_MAP.md` line 17: change "13 translation dirs" to "14 translation dirs".
2. `YHWH v2.4/dev/MATRIX_MAP.md` line 31: change "translations/<id>/ .... 13 dirs" to "translations/<id>/ .... 14 dirs".
3. `YHWH v2.4/dev/REPO_MAP.md` line 32: change "13 dirs" to "14 dirs"; add `lxx-swete-greek` and `byzantine-greek` to the partial-pilots list in the enumeration; and remove or qualify "Each has `_meta.yaml`" because `geez-tewahedo-en` and `amharic-tewahedo-en` currently lack that file (they are early-stage dirs with verse .py files only).

The corrected REPO_MAP line 32 description of the pilots clause should read something like: `and partial pilots (wlc, jps, lxx-brenton-{english,greek}, douay-rheims, vulgate-clementine, arabic-vandyke, lxx-swete-greek, byzantine-greek — gen.py only). All except geez-tewahedo-en / amharic-tewahedo-en have _meta.yaml.`

No code changes needed; this is a documentation-only fix. Safe for all editions.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): I independently verified all claims by reading the actual files.

MATRIX_MAP.md: Line 17 reads "13 translation dirs" and line 31 reads "translations/<id>/ .... 13 dirs". Both say 13.

Filesystem reality: The `_meta.yaml` glob found exactly 12 dirs with that file (kjv, geez-tewahedo, amharic-tewahedo, wlc, jps, lxx-brenton-english, lxx-brenton-greek, douay-rheims, vulgate-clementine, arabic-vandyke, lxx-swete-greek, byzantine-greek). Additionally, `geez-tewahedo-en` and `amharic-tewahedo-en` exist as directories (confirmed by grep and direct glob) but lack `_meta.yaml`. Total = 14 dirs.

REPO_M …[clipped]

### 33. [LOW] Share-pin in γ.4.2 arc-close class violates §8.1 convention

- **Dimension:** tests (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/tests/test_ethiopian_gamma4.py:1177-1180`
- **Evidence:**

`cyril_share = len(cyril) / total` then `assert cyril_share < 0.80` — this is exactly the pattern RULES §8.1 prohibits: 'NEVER a share threshold — share-pins break mechanically when later waves dilute the share even though the historical achievement is preserved (memory `feedback_share_pin_pattern`)'. Every future Ephrem/Jubilees/Meqabyan/Athanasius wave that adds non-Cyril entries will dilute `cyril_share` further below 0.80, keeping this test permanently green regardless of whether the γ.4.2 rebalance achievement itself was tampered with. The test also cannot catch a regression that accidentally inflates Cyril's count above 80% if corpus pruning removes the Ephrem entries.

- **Fix:** Replace the share-pin with an absolute-count milestone pin per §8.1. At γ.4.2 wave-1 ship time Ephrem had ≥30 entries (the γ.4.2 wave-1 count). Pin that directly:
```python
def test_voice_rebalance_achieved(self):
    # §8.1 absolute-count milestone pin: at γ.4.2 wave-1 close,
    # Ephrem had ≥30 entries — the corpus rebalance that reduced Cyril
    # dominance from 93% to sub-80% is preserved by this floor.
    ephrem = self.ec.by_father("Ephrem the Syrian")
    assert len(ephrem) >= 30, (
        f"γ.4.2 rebalance: ≥30 Ephrem entries (the milestone); found {len(ephrem)}"
    )
```
The `test_ephrem_now_substantively_present` test above it already pins `len(ephrem) >= 30`; if they are redundant at this value, raise the milestone to the actual shipped count (32 per the class docstring) in either or both.
- **Verifier-corrected fix:** Replace lines 1171-1180 with an absolute Cyril count ceiling pin (do NOT duplicate the already-present Ephrem floor at line 1165-1169):

```python
def test_voice_rebalance_achieved(self):
    # §8.1 absolute-count milestone pin: at γ.4.2 wave-1 close,
    # Cyril had 91 entries (per class docstring). Pin a ceiling so
    # a future ingest cannot silently re-inflate Cyril dominance.
    # A share-pin would break as γ.4.2.B-D add more Ephrem entries
    # (feedback_share_pin_pattern); an absolute ceiling is stable.
    cyril = self.ec.by_father("Cyril of Alexandria")
    assert len(cyril) <= 91, (
        f"γ.4.2 rebalance: Cyril must not exceed 91 entries "
        f"(the post-wave-1 milestone); found {len(cyril)}"
    )
```

If the real Cyril count at the time this test was written was higher than 91 (the docstring may be stale), verify with `len(self.ec.by_father("Cyril of Alexandria"))` against the live corpus and substitute that value. The `test_ephrem_now_substantively_present` at line 1165 already covers the Ephrem floor; no second Ephrem-count pin is needed.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): The code at lines 1177-1180 of `YHWH v2.4/tests/test_ethiopian_gamma4.py` does exactly what the finding describes: `cyril_share = len(cyril) / total` followed by `assert cyril_share < 0.80`. This is a share-pin.

The `feedback_share_pin_pattern` memory note and RULES §8.1 both prohibit share-threshold pins because future waves adding non-Cyril entries dilute the share and make the test permanently trivially-green as a regression guard. The class docstring at line 1128 explicitly notes future waves γ.4.2.B-D are planned, confirming this share will be diluted further.

The finding is real and ma …[clipped]

### 34. [LOW] test_detect_returns_empty_for_uncommented_verse assumes mat 1:1 has no patristic entry (same state-default violation)

- **Dimension:** tests (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/tests/test_patristic_gamma3.py:221-228`
- **Evidence:**

```python
def test_detect_returns_empty_for_uncommented_verse(self):
    d = detectors.PatristicCommentaryDetector()
    # No NT verses in the seed yet
    assert d.detect("mat", 1, 1, "") == []
    # Genesis verse without commentary
    assert d.detect("gen", 50, 1, "") == []
```
Both assertions assume world state: 'mat 1:1 is empty' (temporary — the comment says 'No NT verses … yet') and 'gen 50:1 is empty'. If either is filled by a future γ.3.x wave, this test fails not because the detector broke but because the world changed. The test should verify the contract (empty list for a verse with no data) against state the test controls.

- **Fix:** Use a controlled synthetic state or a provably-non-corpus coordinate:
```python
def test_detect_returns_empty_for_uncommented_verse(self):
    d = detectors.PatristicCommentaryDetector()
    # Non-existent book code is the state-invariant empty case.
    assert d.detect("nonexistent-book-xyz", 99, 99, "") == []
```
Alternatively, if a mid-book gap in the known corpus (a verse guaranteed to stay empty because the source has no commentary there) is needed for a specific reason, add a comment documenting the sentinel and a setup_class assertion that the verse is still empty before asserting on it.
- **Verifier-corrected fix:** Replace both world-state-dependent assertions with a single invariant-sentinel call. In `YHWH v2.4/tests/test_patristic_gamma3.py` lines 221-228:

```python
def test_detect_returns_empty_for_uncommented_verse(self):
    from scripts.core import detectors

    d = detectors.PatristicCommentaryDetector()
    # Use a coordinate that can never appear in the corpus:
    # an invalid book code is the true state-invariant empty case.
    assert d.detect("nonexistent-book-xyz", 99, 99, "") == []
```

This is correct and safe: the lookup indexes by book code and no valid expansion wave will ever insert `"nonexistent-book-xyz"`. It tests the contract (detector returns `[]` when the corpus has no matching entry) against state the test controls, rather than against the current absence of future γ.3.x data. The original `mat 1:1` and `gen 50:1` assertions should be dropped entirely — they add no coverage over the invariant case and will become spurious failures on the first NT or late-Genesis expansion.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): I read `YHWH v2.4/tests/test_patristic_gamma3.py` lines 221-228 and `YHWH v2.4/content/sources/patristic_commentaries.json` in full. The test code matches the evidence exactly. The JSON corpus currently holds 8 entries all in Genesis 1-3; there are no Matthew entries and no Genesis 50 entries, so both assertions pass today. However: (a) the inline comment "No NT verses in the seed yet" is the author's own acknowledgement that this is a transient state — the `_meta` block in the JSON explicitly documents that "future γ.3.x" will expand the corpus beyond the Augustine-on-Genesis seed, and Matthe …[clipped]

### 35. [LOW] promote_candidate coordinate guard not directly unit-tested — only batch_insert_notes is covered

- **Dimension:** tests (finder said medium, recalibrated to low)
- **Location:** `YHWH v2.4/tests/test_scripts.py:6617-6629`
- **Evidence:**

`TestCoordGuard.test_batch_insert_drops_out_of_range` calls `batch_insert_notes` which calls `coord_in_canonical_extent` internally. However `promote_candidate` in `scripts/promote.py` (line 403) has its OWN identical guard. The test never calls `promote_candidate` with an out-of-extent coord. Mutation: remove the guard at `promote.py:403` — no existing test catches it, because `TestPromoteCandidateIdempotency` only exercises valid coordinates and `TestCoordGuard` only goes through `batch_insert_notes`.

- **Fix:** Add a test in `test_promote_idempotency.py` that directly exercises the `promote_candidate` guard:
```python
def test_promote_candidate_drops_out_of_extent_coord(self, fake_book):
    """promote_candidate must return (False, '') for out-of-canonical-extent
    coordinates — the coord guard in promote.py:403 is load-bearing."""
    c = _candidate(
        verse=999,   # Gen has ≤31 verses per chapter; v=999 is out of extent
        chapter=1,
        # Use 'gen' so coord_in_canonical_extent can reject it
    )
    # We need the fake_book to be 'gen', not 'tst' (unknown books pass through).
    # So write a gen.py fixture:
    import scripts.promote as promote_mod
    notes_dir = fake_book["path"].parent
    gen_path = notes_dir / "gen.py"
    gen_path.write_text('NOTES = []\nNOTES_GEN = NOTES\n', encoding='utf-8')
    ok, _ = promote_mod.promote_candidate("gen", c)
    assert ok is False, "out-of-extent coord must be rejected by promote_candidate"
```
- **Verifier-corrected fix:** Add a standalone test (NOT reusing `fake_book` which is wired to "tst") to `test_promote_idempotency.py`. Use a `tmp_path`-based fixture for "gen" directly:

```python
def test_promote_candidate_drops_out_of_extent_coord(tmp_path, monkeypatch):
    """promote_candidate must return (False, '') for out-of-canonical-extent
    coordinates — the guard at promote.py:403 is load-bearing for the
    chi-cluster ingest path and is NOT exercised by the batch_insert_notes tests."""
    import scripts.promote as promote_mod

    notes_dir = tmp_path / "content" / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    gen_path = notes_dir / "gen.py"
    gen_path.write_text('NOTES = []\nNOTES_GEN = NOTES\n', encoding="utf-8")
    monkeypatch.setattr(promote_mod, "NOTES_DIR", notes_dir)

    c = {
        "id": "gen-1-999-001",
        "chapter": 1,
        "verse": 999,          # Gen 1 has 31 verses; 999 is out of extent
        "kind": "comm-ethiopian",
        "anchor": "",
        "draft_title": "T",
        "draft_label": "L",
        "draft_body": "<aside>body</aside>",
        "source_attribution": "Src. PD.",
        "source_name": "Src",
        "confidence": 0.9,
    }
    ok, suffix = promote_mod.promote_candidate("gen", c)
    assert ok is False, "out-of-extent coord must be rejected by promote_candidate guard"
    assert suffix == ""
```

This is a clean standalone test t …[clipped]
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): I read all three relevant files directly.

1. `test_promote_idempotency.py` lines 54–77: the `fake_book` fixture uses book code "tst" and monkeypatches `promote_mod.NOTES_DIR`. Every `promote_candidate` call in `TestPromoteCandidateIdempotency` uses `"tst"` as the book code.

2. `canonical_verse_counts.py` lines 166–172: `coord_in_canonical_extent` catches any exception from `canonical_book_shape` and returns `True` (keep); it also returns `True` when `shape` is empty. An unknown book code like "tst" falls through with `return True` — so the guard at `promote.py:403` is never triggered by any  …[clipped]

### 36. [INFO] bookcode_canonical lint does not screen CCEL_ABBREV or EASTON_BOOK — coverage gap for future ingest-script edits

- **Dimension:** cross-module (finder said low, recalibrated to info)
- **Location:** `YHWH v2.4/scripts/lint_rules.py:1995-2003`
- **Evidence:**

`check_book_codes_canonical` at lines 1995-2003 screens six map_specs plus one list_spec. `scripts.extract_naves_ccel.CCEL_ABBREV` and `scripts.extract_eastons_ccel.EASTON_BOOK` are not in the list. Both currently contain only canonical values (verified: `"Jas": "jam"`, `"Php": "phi"`, `"Mr": "mrk"`, `"Joh": "jhn"` all resolve to canonical), but the memory note `feedback_book_code_canonical` specifically records that this class of defect 'recurs every ingest' — meaning the guard was added precisely because new maps are created at ingest time. An unguarded map is one edit away from re-introducing the bug silently.

- **Fix:** Add both maps to `map_specs` in `check_book_codes_canonical`:

```python
map_specs = [
    ("scripts.core.sources", "KENYON_BOOK_NAME_TO_CODE"),
    ("scripts.fetch_sources", "TSK_BOOK_REMAP"),
    ("scripts.fetch_sources", "NAVES_BOOK_REMAP"),
    ("scripts.core.sources_base", "_BOOK_CODE_ALIASES"),
    ("scripts.extract_torrey_ccel", "_LEGACY_TO_CANON"),
    ("scripts.link_xrefs", "ABBREV"),
    ("scripts.extract_naves_ccel", "CCEL_ABBREV"),    # add
    ("scripts.extract_eastons_ccel", "EASTON_BOOK"),  # add
]
```

Both modules are already importable (they use only stdlib + project deps). The current values will pass clean; the guard prevents future edits from drifting silently.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Verified by reading the code directly.

(a) The code does exactly what the evidence claims. `check_book_codes_canonical` at lines 1995-2003 of `YHWH v2.4/scripts/lint_rules.py` has a `map_specs` list of 6 entries. `scripts.extract_naves_ccel.CCEL_ABBREV` and `scripts.extract_eastons_ccel.EASTON_BOOK` are absent from it.

(b) This is a genuine coverage gap, not intended behavior or a de-scoped item. The guard's own docstring at line 1966-1975 explicitly cites `feedback_book_code_canonical` and states this "recurs every ingest" — the guard exists precisely to catch future edits to these kinds of …[clipped]

### 37. [INFO] REPO_MAP scripts/api/ count is 17 but 18 files exist; scripts/templates/ count is 20 but 21 exist

- **Dimension:** docs (finder said medium, recalibrated to info)
- **Location:** `YHWH v2.4/dev/REPO_MAP.md:42-43`
- **Evidence:**

REPO_MAP line 42: `scripts/api/ (17)` — grep of `scripts/api/*.py` returns 18 files. REPO_MAP line 43: `scripts/templates/ (20)` — grep of `scripts/templates/*.py` returns 21 files. Both counts are off by 1, consistent with one new file added per directory after the REPO_MAP was last written (likely `api/distribution.py` and `templates/distribution.py` added in mint-6 for the `/distribution` console).

- **Fix:** Update REPO_MAP line 42 from `(17)` to `(18)` and line 43 from `(20)` to `(21)`.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Verified by direct file inspection. Glob of `scripts/api/*.py` returns exactly 18 files (including `distribution.py`); Glob of `scripts/templates/*.py` returns exactly 21 files (including `distribution.py`). REPO_MAP.md line 42 says `(17)` and line 43 says `(20)` — both off by 1, consistent with `distribution.py` being added to each directory during mint-6. The finding is factually correct. However, `dev/trace_repo.py` (the anti-rot guard for REPO_MAP) only checks whether top-level *directory names* appear in the REPO_MAP text — it does not parse or validate numeric counts. So no guard fails,  …[clipped]

### 38. [INFO] REPO_MAP tests count is 168 but 169 test_*.py files exist

- **Dimension:** docs (finder said medium, recalibrated to info)
- **Location:** `YHWH v2.4/dev/REPO_MAP.md:17`
- **Evidence:**

`168 pytest files (test_*.py)` — grep of `tests/test_*.py` returns 169 files. The count drifted by 1, consistent with `test_lint_rules.py` being extracted from `test_scripts.py` during mint-7 Phase E without REPO_MAP being updated.

- **Fix:** Update REPO_MAP line 17 from `168 pytest files` to `169 pytest files`.
- **Verifier-corrected fix:** In `YHWH v2.4/dev/REPO_MAP.md` line 17, change `168 pytest files` to `169 pytest files`. No other changes needed.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Directly verified: REPO_MAP.md line 17 reads `168 pytest files (test_*.py)`. A grep with output_mode=count over `tests/test_*.py` confirmed `Found 81695 total occurrences across 169 files` — the tool itself reports the exact file count as 169. The finding's claimed discrepancy of exactly 1 is confirmed. The proposed fix (change "168" to "169") is correct and safe: it is a doc-only edit to `dev/REPO_MAP.md`, touching no code, no build pipeline, no marathon core, and zero KJV byte-stability surface. The finder's attribution to `test_lint_rules.py` being extracted during mint-7 is plausible (that …[clipped]

### 39. [INFO] lint_rules.py check_superpowers_coherence docstring says 'mint-6 backfilled all 39'; count is now 41

- **Dimension:** docs (finder said low, recalibrated to info)
- **Location:** `YHWH v2.4/scripts/lint_rules.py:1357`
- **Evidence:**

Function docstring: `mint-6 backfilled all 39; _ENFORCE_SUPERPOWERS_COHERENCE makes drift a hard FAIL.` The superpowers corpus now has 41 files (25 plans + 16 specs per INDEX.md, verified by glob). The check itself is dynamic (`len(files)`) so it functions correctly; only the inline comment count is wrong.

- **Fix:** Update the docstring count from `39` to `41` on line 1357.
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): I read `YHWH v2.4/scripts/lint_rules.py` lines 1351–1357. The docstring at line 1357 states "mint-6 backfilled all 39". I then read `YHWH v2.4/docs/superpowers/INDEX.md` line 7, which states "**41 documents** — 25 plans · 16 specs". The count discrepancy is confirmed: the docstring says 39, the actual corpus is 41. The check itself (line 1359: `files = sorted(base.glob("plans/*.md")) + sorted(base.glob("specs/*.md"))`) is dynamic and unaffected — it counts whatever is present at runtime. The defect is confined to the docstring comment only; no shipped output, no KJV byte-stability, and no runt …[clipped]

### 40. [INFO] REPO_MAP dev/archive section lists only PLAN_2026-05-07/08/09 as archived plans; two more exist

- **Dimension:** docs (finder said low, recalibrated to info)
- **Location:** `YHWH v2.4/dev/REPO_MAP.md:51`
- **Evidence:**

`superseded plans (PLAN_2026-05-07/08/09)` — the `dev/archive/` directory also contains `PLAN_2026-05-21.md` and `PLAN_2026-05-24-end-scope.md` (confirmed by glob).

- **Fix:** Update the REPO_MAP line 51 enumeration to `superseded plans (PLAN_2026-05-07/08/09 + PLAN_2026-05-21 + PLAN_2026-05-24-end-scope)`.
- **Verifier-corrected fix:** Update YHWH v2.4/dev/REPO_MAP.md line 51 to: `superseded plans (PLAN_2026-05-07/08/09 + PLAN_2026-05-21 + PLAN_2026-05-24-end-scope) + ship_scripts/ (21 one-shot ship scripts) + old handoffs.`
- **Adversarial verdict (1 skeptic[s]):**
  - skeptic 1 (high, refuted=false): Read REPO_MAP.md line 51 directly. The text reads: `superseded plans (PLAN_2026-05-07/08/09) + ship_scripts/ (21 one-shot ship scripts) + old handoffs`. Glob of dev/archive/ confirms both PLAN_2026-05-21.md and PLAN_2026-05-24-end-scope.md exist there. The enumeration on that line specifically names plans by date, so the omission of two later archived plans is a real gap in the index. No build, byte stability, or test impact — pure docs defect. The proposed fix (adding the two missing plan names to the enumeration) is correct and safe.

## Optimization decisions (approach re-evaluation)

| # | Verdict-sev | Area | Recommendation |
|---|-------------|------|----------------|
| 1 | medium | is_output_current skips rebuild when notes files change (stale-build on cold cache) | Append all `content/notes/*.py` mtimes to the sources list: add `sources.extend(REPO_ROOT / 'content' / 'notes' / f for f in (REPO_ROOT / 'content' / 'notes').glob('*.py') if f.is_file())` inside `is_output_current`. Als …[clipped] |
| 2 | medium | subprocess.run missing stdin=subprocess.DEVNULL — Windows WinError 6 in test/harness contexts | Add `stdin=subprocess.DEVNULL` to the `subprocess.run` call: `result = subprocess.run([sys.executable, str(REPO_ROOT / 'scripts' / 'build_epub.py'), str(output_path), '--epub-dir', str(tmp), '--no-bump'], capture_output= …[clipped] |
| 3 | medium | render_coverage._CANONICAL_BOOKS missing 7 of 87 books.yaml entries, skewing all coverage counts | Add the seven missing codes to _CANONICAL_BOOKS in their canonical books.yaml position (man after 2ch; 2en after 1en; 1es after ezr/neh; aes after est; lje after bar; sus and 1cl at their canonical positions). Update the …[clipped] |
| 4 | medium | api_sample_html kind-filter bypasses config.enabled_kind_codes — AI notes and phase-gated kinds bleed into sam …[clipped] | Replace the manual enabled_kinds/disabled_kinds construction with a call to the canonical resolver. Change lines 275-291 to: `from scripts.core.config import enabled_kind_codes, load_kinds; enabled_kind_set = enabled_kin …[clipped] |
| 5 | medium | subprocess.run in api_export_build missing stdin=subprocess.DEVNULL — WinError 6 on Windows | Add stdin=subprocess.DEVNULL to the subprocess.run() call: proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO), timeout=timeout_s, stdin=subprocess.DEVNULL) |
| 6 | medium | api_sample_html edition-filter logic does not apply enabled_categories — kind-filter diverges from build_editi …[clipped] | Replace the inline filter logic with the same compute_enabled_kinds() call that build_edition uses: from scripts.core.matrix import _enabled_kinds_for_edition; from scripts.core.config import load_kinds; enabled = set(_e …[clipped] |
| 7 | low | filter_html recompiles O(files × kinds × 2) and O(files × disabled_refs × 2) regex patterns — hot build path | Pre-compile per-edition pattern sets once in `build_one`, before the HTML file loop. Change `filter_html` signature to accept `pre_compiled_kind_patterns: list[tuple[re.Pattern, re.Pattern]] \| None = None`. In `build_one …[clipped] |
| 8 | low | Double corpus walk for tradition-filter + tradition-label map when traditions_default is set | Merge the two passes into one helper `_compute_tradition_maps(edition) -> tuple[set[str], dict[str, str]]` that returns `(disabled_ref_ids, ref_id_to_tradition)` in a single walk. Notes are LRU-cached per mtime so the fi …[clipped] |
| 9 | low | BUILD OPTIMIZATION — BETTER PLAN: compresslevel 6 is the highest-value single change; pre-compiled regexes are …[clipped] | Change `compresslevel=9` to `compresslevel=6` in `scripts/build_epub.py` line 156. BYTE-STABILITY PROOF OBLIGATION (per project RULES): (1) run `ebible build --all` before the change, record all 9 EPUB SHA-256 hashes; (2 …[clipped] |
| 10 | low | TODO_CERTIFIER_NAME ships verbatim in every built EPUB's OPF accessibility metadata | Replace the placeholder with the actual publisher name. Since this is a free public platform, use the project name: `'    <meta property="a11y:certifiedBy">YHWH v2.4 Project</meta>\n'`. Alternatively, resolve it from `pu …[clipped] |
| 11 | low | All 9 run_*_at_scale write_queue functions use bare write_text — half-written candidate JSON on crash silently …[clipped] | In `at_scale_base.py` add `write_queue_atomic(path, payload)` that writes via `atomic_write` from `scripts.core.notes_io` (same tmp+rename dance already used for notes). Replace every `out_path.write_text(...)` in all 9  …[clipped] |
| 12 | low | batch_promote_xrefs.py default mode (without --by-book): calls promote_candidate + update_queue_status per can …[clipped] | Make `--by-book` the default (flip `args.by_book` to default True, rename old default to `--per-candidate` for the rare interactive use case). Update the docstring usage examples to show `--by-book` as the standard invoc …[clipped] |
| 13 | low | insert_note_into_book_file position-finding loop uses break-on-first-descending — silent mis-insertion if NOTE …[clipped] | Add a pre-flight sort check (or assert) at the top of both functions: `if not all(existing[i] <= existing[i+1] for i in range(len(existing)-1)): logging.warning('NOTES list in %s appears unsorted — insertion position may …[clipped] |
| 14 | low | is_output_current mtime cache ignores content/notes/*.py — corpus edits silently produce stale builds | Add content/notes/*.py mtime to the sources list. Simplest surgical fix: after line 1961 add `notes_dir = REPO_ROOT / 'content' / 'notes'; sources.extend(notes_dir.glob('*.py'))`. This makes the check correctly skip the  …[clipped] |
| 15 | low | do_POST fallthrough to do_PUT causes double _check_admin_auth() when no POST route matches | Replace the fallthrough with a direct 404 for unrecognized POST paths (matching the do_PUT/do_DELETE pattern), or factor the common PUT-compatible POST routes into a shared helper. Simplest fix: replace 'return self.do_P …[clipped] |
| 16 | low | lru_cache on _load_notes_cached uses path string + mtime_ns but mtime_ns resolution can be 1s on some Windows  …[clipped] | In atomic_write, after os.replace, also call clear_load_notes_cache() when the path is a notes file (same condition as _invalidate_corpus_index_if_notes_file). This is O(1) and idempotent. Alternatively, the atomic_write …[clipped] |
| 17 | low | api_restore_backup writes snapshot bytes without validating they are valid UTF-8 Python source before overwrit …[clipped] | When abs_path.suffix == '.py' and abs_path.parent.name == 'notes', validate the snapshot bytes: (1) decode as UTF-8, (2) call load_notes_from_text() on the decoded text, (3) reject with a 400 error if the result is None. …[clipped] |

### opt-1. [medium] is_output_current skips rebuild when notes files change (stale-build on cold cache)
- **Location/context:** `YHWH v2.4/scripts/build_edition.py:1956-1964`
- **Evidence:** `sources = list(EPUB_DIR.glob('*.html'))` then only appends `content.opf`, `nav.xhtml`, `stylesheet.css`, `editions.yaml`, `build_edition.py` — the 88 `content/notes/*.py` files are absent. If any note file is edited after the last EPUB build, `is_output_current` returns the old EPUB as 'current' and the build is silently skipped. The content-hash cache (ω.20-B) is correct but only fires BEFORE this check (lines 2741-2754); on a cold cache (after `cache_clear` or first run), the stale mtime guard fires and the user gets stale output without any warning.
- **Recommendation:** In `YHWH v2.4/scripts/build_edition.py` inside `is_output_current`, after line 1961, add:

```python
notes_dir = REPO_ROOT / "content" / "notes"
if notes_dir.is_dir():
    sources.extend(notes_dir.glob("*.py"))
sources.append(REPO_ROOT / "content" / "kinds.yaml")
sources.append(REPO_ROOT / "content" / "categories.yaml")
```

This mirrors the exact inputs covered by `compute_cache_key` sections 3 and 5, making the mtime guard consistent with the content-addressable guard. The `is_dir()` guard keeps it safe if the directory is absent on a fresh checkout. No other changes needed.

### opt-2. [medium] subprocess.run missing stdin=subprocess.DEVNULL — Windows WinError 6 in test/harness contexts
- **Location/context:** `YHWH v2.4/scripts/build_edition.py:3022-3033`
- **Evidence:** `result = subprocess.run([sys.executable, ..., '--no-bump'], capture_output=True, text=True)` — no `stdin=subprocess.DEVNULL`. Per project memory (`W-W1 subprocess DEVNULL`): on Windows under pytest-from-PowerShell every `subprocess.run()` without `stdin=subprocess.DEVNULL` hits WinError 6 (invalid handle) because the harness redirects stdin. This path executes on every non-frozen build (the `not getattr(sys, 'frozen', False)` branch at line 3014), meaning every `pytest`-invoked build test that reaches this line will fail with WinError 6 instead of the actual build error.
- **Recommendation:** At YHWH v2.4/scripts/build_edition.py line 3033, add stdin=subprocess.DEVNULL to the subprocess.run call:

result = subprocess.run(
    [
        sys.executable,
        str(REPO_ROOT / "scripts" / "build_epub.py"),
        str(output_path),
        "--epub-dir",
        str(tmp),
        "--no-bump",
    ],
    capture_output=True,
    text=True,
    stdin=subprocess.DEVNULL,
)

subprocess is already imported at line 46. No other changes needed.

### opt-3. [medium] render_coverage._CANONICAL_BOOKS missing 7 of 87 books.yaml entries, skewing all coverage counts
- **Location/context:** `YHWH v2.4/scripts/render_coverage.py:53-143`
- **Evidence:** The docstring says '81-book set' and the list has 84 entries. books.yaml defines 87 books. Seven codes present in books.yaml are absent from _CANONICAL_BOOKS: man (Prayer of Manasseh), 2en (2 Enoch), 1es (1 Esdras / Ezra Kali), aes (Additions to Esther), lje (Letter of Jeremiah), sus (Susanna), 1cl (1 Clement). These books silently fall into the `missing` bucket in every per-edition report, the preflight summary's `canonical_books` value is 84 not 87, and the `render_coverage_no_regression` lint baseline in lint_rules.py also omits them — so new renders of those books would never trigger a lint pass.
- **Recommendation:** 1. In YHWH v2.4/scripts/render_coverage.py, add the 7 missing codes to _CANONICAL_BOOKS at their canonical books.yaml positions (man after 2ch; 2en after 1en; 1es after neh; aes after est; lje after bar; sus after paz/bel Daniel appendices; 1cl at end after rev/4ba). Update the docstring at line 42 from "81-book set" to the correct count after the reconciliation.

2. Reconcile the 2 phantom codes (1ma, 2ma) that are in _CANONICAL_BOOKS but absent from books.yaml: either add them to books.yaml with proper bxx values if they belong in the Tewahedo 87-book canon, OR remove them from _CANONICAL_BOOKS. Without this step the list still mismatches books.yaml.

3. In YHWH v2.4/scripts/lint_rules.py check_render_coverage_no_regression (line 948), add rendered codes for any of the 7 newly recognized books that already have .py files in geez-tewahedo or amharic-tewahedo — do not add them preemptively, only when the .py file exists.

### opt-4. [medium] api_sample_html kind-filter bypasses config.enabled_kind_codes — AI notes and phase-gated kinds bleed into sample HTML
- **Location/context:** `YHWH v2.4/scripts/web_content.py:275-291`
- **Evidence:** Lines 275-276 read `enabled_kinds = set(edition.get('enabled_kinds') or [])` and `disabled_kinds = set(edition.get('disabled_kinds') or [])`, then filter with `(enabled_kinds is empty → allow all) AND kind NOT IN disabled_kinds`. This misses three gates that config.enabled_kind_codes() applies: (1) enabled_categories — notes whose kind belongs to an enabled category are invisible if enabled_kinds is empty but enabled_categories is non-empty; (2) max_phase gate — phase2/phase3 notes appear in samples for mvp editions; (3) AI double opt-in — comm-ai notes appear in editions that set comm-ai in enabled_kinds but omit enable_ai_notes: true. The comment on line 286 says 'Filter rule mirrors build_edition' but does not call the canonical resolver.
- **Recommendation:** In `YHWH v2.4/scripts/web_content.py`, replace the manual filter block at lines 275-292 with a call to the canonical resolver. At the top of the file (or in the relevant import block) add `from scripts.core.config import enabled_kind_codes, load_kinds`, then replace lines 275-292 with:

```python
enabled_kind_set = enabled_kind_codes(edition, load_kinds())
in_range = [
    n for n in all_notes
    if n and len(n) >= 8 and f <= n[0] <= t and n[4] in enabled_kind_set
]
```

Also update the module-level comment at line 157 from `edition.enabled_kinds + disabled_kinds for the kind filter` to `config.enabled_kind_codes() for the kind filter (canonical resolver, mirrors EPUB build)`.

No other files need changing. The EPUB build path (`build_edition`) is untouched. Byte-stability is unaffected because this function only produces sample HTML, never the EPUB artifact.

### opt-5. [medium] subprocess.run in api_export_build missing stdin=subprocess.DEVNULL — WinError 6 on Windows
- **Location/context:** `YHWH v2.4/scripts/api/exports.py:197-203`
- **Evidence:** proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO), timeout=timeout_s) — no stdin=subprocess.DEVNULL. Project rule (memory feedback_w_w1_subprocess_devnull): 'On Windows pytest-from-PowerShell, every subprocess.run() must pass stdin=subprocess.DEVNULL or hits WinError 6.' The EPUB build subprocess is launched from the web server's request thread; the server's stdin is the inherited terminal handle, which is invalid in this context.
- **Recommendation:** Add stdin=subprocess.DEVNULL to the subprocess.run() call at YHWH v2.4/scripts/api/exports.py line 197:

proc = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    cwd=str(REPO),
    timeout=timeout_s,
    stdin=subprocess.DEVNULL,
)

### opt-6. [medium] api_sample_html edition-filter logic does not apply enabled_categories — kind-filter diverges from build_edition
- **Location/context:** `YHWH v2.4/scripts/web_content.py:275-291`
- **Evidence:** enabled_kinds = set(edition.get('enabled_kinds') or []) ... if enabled_kinds and kind not in enabled_kinds: continue — the filter reads only the raw enabled_kinds list from the edition dict. The actual build pipeline (build_edition.py) resolves enabled_kinds as: categories→kinds union PLUS enabled_kinds MINUS disabled_kinds, with an AI-notes gate. The sample preview therefore shows wrong notes when an edition's primary kind selection comes from enabled_categories (the common case for most editions), because enabled_categories entries expand to N kinds at build time but the preview only sees the literal enabled_kinds list, which may be empty or a small override set.
- **Recommendation:** In YHWH v2.4/scripts/web_content.py, inside `api_sample_html`, replace lines 275-291 with:

```python
from scripts.core.config import enabled_kind_codes, load_kinds as _load_kinds
_enabled = enabled_kind_codes(edition, _load_kinds())
in_range = []
for n in all_notes:
    if not n or len(n) < 8:
        continue
    ch = n[0]
    if ch < f or ch > t:
        continue
    kind = n[4]
    if kind not in _enabled:
        continue
    in_range.append(n)
```

This delegates to the same `config.enabled_kind_codes` that both `build_edition.compute_enabled_kinds` and `matrix._enabled_kinds_for_edition` already call, ensuring the preview and the actual build are in sync. The `disabled_kinds` gate does not need a separate check because `enabled_kind_codes` already excludes disabled kinds (they are removed at step 1 of the resolver). No marathon-core files touched; no byte-stability impact on the 9-edition build.

### opt-7. [low] filter_html recompiles O(files × kinds × 2) and O(files × disabled_refs × 2) regex patterns — hot build path
- **Location/context:** `YHWH v2.4/scripts/build_edition.py:1001-1061`
- **Evidence:** Inside `filter_html` (called for each of 61 HTML files per edition), lines 1019-1032 loop over `disabled_kinds` and call `re.compile(...)` twice per kind per file. For an edition with 35 disabled kinds: 61 × 35 × 2 = 4,270 compile calls per build, all discarded. Lines 1036-1053 loop over `disabled_html_ref_ids` and call `re.compile(...)` twice per ref_id per file; for `catholic-study` (which has `traditions_default` set and potentially thousands of disabled ref_ids from `compute_tradition_disabled_html_ref_ids`), this is the dominant CPU cost per build.
- **Recommendation:** The fix is valid but needs both call sites covered and should remain backward-compatible.

In `build_one` (before line 2846 and before line 2768), build:

```python
kind_patterns = [
    (
        re.compile(rf'<a class="note-ref note-{re.escape(k)}"[^>]*>.*?</a>', re.DOTALL),
        re.compile(rf'<aside class="note note-{re.escape(k)}"[^>]*>.*?</aside>', re.DOTALL),
    )
    for k in disabled
]
ref_id_patterns = [
    (
        re.compile(rf'<a class="note-ref [^"]*" id="{re.escape(ref_id)}"[^>]*>.*?</a>', re.DOTALL),
        re.compile(
            rf'<aside class="note [^"]*" id="{re.escape(ref_id.replace("ref-", "note-", 1))}"[^>]*>.*?</aside>',
            re.DOTALL,
        ),
    )
    for ref_id in (disabled_html_ref_ids or [])
] if disabled_html_ref_ids else []
```

Change `filter_html` signature to accept `pre_compiled_kind_patterns` and `pre_compiled_ref_patterns` (both `list[tuple[re.Pattern, re.Pattern]] | None = None`). When not None, iterate the pre-compiled tuples directly instead of calling `re.compile` inside the loop. When None, fall back to current behavior (preserves backward compatibility for any direct test calls to `filter_html`).

Pass the pre-compiled lists from both the real build path (line 2848) and the dry_run path (line 2770).

This is byte-identical and the win is material only for editions with large `disabled_html_ref_ids` sets (tradition-fil …[clipped]

### opt-8. [low] Double corpus walk for tradition-filter + tradition-label map when traditions_default is set
- **Location/context:** `YHWH v2.4/scripts/build_edition.py:2647-2661`
- **Evidence:** `disabled_html_ref_ids |= compute_tradition_disabled_html_ref_ids(edition)` (line 2647) calls `_iter_note_ref_traditions()` which iterates all 67,715 notes. Then `ref_id_to_tradition = build_ref_id_to_tradition_map(edition)` (line 2661) calls `_iter_note_ref_traditions()` again — an identical second full walk. The two functions are logically complementary (one collects disabled refs, the other the surviving refs) and both iterate the same 87 note files.
- **Recommendation:** Merge the two passes into a single private helper `_compute_tradition_maps(edition: dict) -> tuple[set[str], dict[str, str]]` in `YHWH v2.4/scripts/build_edition.py`. The helper runs the early-exit guard once (`not has_default and not per_book → return set(), {}`), maintains one `book_active_cache`, walks `_iter_note_ref_traditions()` exactly once, and in the same loop body populates both `disabled: set[str]` (when `tradition not in active`) and `surviving: dict[str, str]` (when `tradition in active`). Replace the two call sites at lines 2647 and 2661 with a single unpacking call. `compute_tradition_disabled_html_ref_ids` and `build_ref_id_to_tradition_map` can be kept as thin public wrappers that delegate to the helper (for test-isolation / backwards compat), or inlined. Output is byte-identical. No marathon-core files touched.

### opt-9. [low] BUILD OPTIMIZATION — BETTER PLAN: compresslevel 6 is the highest-value single change; pre-compiled regexes are safe quick wins
- **Location/context:** `YHWH v2.4/scripts/build_epub.py:156`
- **Evidence:** Line 156: `compresslevel=9` in `build_epub.build()`. The zip step compresses a 23MB uncompressed EPUB tree. At level 9 (maximum), compression is CPU-bound and slow. Level 6 is the standard deflate trade-off (~30-50% faster at ~1-3% larger output). Profiling reference: Python's zipfile benchmarks show level-9 is 2-3× slower than level-6 for HTML/text-heavy archives. At 133s/edition, and with the zip step being a major fraction, level-6 is estimated to save 20-40s per edition.
- **Recommendation:** Change `compresslevel=9` to `compresslevel=6` at `YHWH v2.4/scripts/build_epub.py:156`. After the change, clear `exports/.cache/` (or run `scripts/preflight.py --cache-clear`) so no stale level-9 EPUB is served from the content-addressable cache under its now-wrong entry. The `test_byte_stability_gate.py` suite requires no update — the digest is over decompressed inner content, which is unchanged.

### opt-10. [low] TODO_CERTIFIER_NAME ships verbatim in every built EPUB's OPF accessibility metadata
- **Location/context:** `YHWH v2.4/scripts/build_edition.py:1265`
- **Evidence:** `'    <meta property="a11y:certifiedBy">TODO_CERTIFIER_NAME</meta>\n'` — this placeholder string is emitted into `content.opf` of every built EPUB. EPUB 3 accessibility spec and epubcheck ACC-004 treat `a11y:certifiedBy` as an advisory (not a hard fail), but the literal string `TODO_CERTIFIER_NAME` is visible to any reader software that surfaces accessibility metadata and would appear in any distribution channel inspection.
- **Recommendation:** At `YHWH v2.4/scripts/build_edition.py:1265`, replace:

`'    <meta property="a11y:certifiedBy">TODO_CERTIFIER_NAME</meta>\n'`

with:

`f'    <meta property="a11y:certifiedBy">{_xml_escape(pub["publisher_name"])}</meta>\n'`

This reuses `pub` (already resolved at line 1122) and the existing `_xml_escape` helper (already used on the lines immediately above), making the certifier name edition-specific and consistent with the publisher displayed in `<dc:publisher>`. No schema change, no byte-stability impact, no new dependency.

### opt-11. [low] All 9 run_*_at_scale write_queue functions use bare write_text — half-written candidate JSON on crash silently drops prior candidates
- **Location/context:** `YHWH v2.4/scripts/run_xref_at_scale.py:66`
- **Evidence:** `out_path.write_text(json.dumps(payload, ...), encoding='utf-8')` — identical in run_xref (L66), run_naves (L67), run_torrey (L65), run_hebrew (L61), run_greek (L60), run_ethiopian (L76), run_kenyon (L95), run_ai_xrefs (L112), run_ai_notes (L110), prospect.py (L152). Each does a read-merge-write cycle. On a kill/crash mid-write the JSON is half-written; the next at-scale run's `except Exception: existing = []` silently discards all prior promoted/pending candidates from that chapter file.
- **Recommendation:** In each of the 10 files (run_xref_at_scale.py, run_naves_at_scale.py, run_torrey_at_scale.py, run_hebrew_at_scale.py, run_greek_at_scale.py, run_ethiopian_at_scale.py, run_kenyon_at_scale.py, run_ai_xrefs_at_scale.py, run_ai_notes_at_scale.py, prospect.py), add `from scripts.core.notes_io import atomic_write` to the imports, then replace the single `out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")` line with `atomic_write(out_path, json.dumps(payload, indent=2, ensure_ascii=False))`. Do NOT add a centralized `write_queue_atomic` to at_scale_base.py — that module is documented as a dependency-free leaf (imports nothing from scripts) and the decentralized write_queue design is intentional. The notes_io._invalidate_corpus_index_if_notes_file hook is a no-op for .json files so there is no side-effect.

### opt-12. [low] batch_promote_xrefs.py default mode (without --by-book): calls promote_candidate + update_queue_status per candidate — O(n²) writes on large candidate sets
- **Location/context:** `YHWH v2.4/scripts/batch_promote_xrefs.py:119-155`
- **Evidence:** The default loop at L139-155 calls `promote_candidate(book, c)` for each candidate; `promote_candidate` calls `insert_note_into_book_file` which does a full `read+ast.parse+write` of the book file. For N candidates in the same book this is O(N × filesize). A full corpus batch (67k+ candidates, 88 book files) would trigger thousands of full-file rewrites. The `--by-book` fast path exists (L104) but is NOT the default and is undocumented in the primary usage comment.
- **Recommendation:** In `YHWH v2.4/scripts/batch_promote_xrefs.py`: change the `--by-book` argument (L94-98) from `action="store_true"` to `action="store_false"`, rename it `--per-candidate`, and add a `--by-book` flag that is simply the default (or flip the logic: add `args.per_candidate` boolean and default to the `promote_by_book` path). The simplest concrete change:

Replace the `--by-book` argument block with:
```python
p.add_argument(
    "--per-candidate",
    action="store_true",
    help="slow path: one file write per candidate (default before mint-8; use for debugging only)",
)
```

Then at L104 change `if args.by_book:` to `if not args.per_candidate:`.

Also update the module docstring (L8-9) to show the standard invocation without any flag, and note that `--per-candidate` is the legacy/debug path. No other files need changing.

### opt-13. [low] insert_note_into_book_file position-finding loop uses break-on-first-descending — silent mis-insertion if NOTES list is unsorted
- **Location/context:** `YHWH v2.4/scripts/promote.py:246-249`
- **Evidence:** ```python
if existing_key < new_key:
    insert_after_lineno = tup.end_lineno
else:
    break
```
The `break` assumes the NOTES list is sorted by (ch, v, suffix). If a legacy or manually-edited file has any out-of-order tuple, the loop stops early and the new note is inserted at the wrong position. The same pattern exists in `batch_insert_notes` L339-343. The `ensure_backup` + `ast.parse` sanity check catches a malformed file but not a sort-order violation.
- **Recommendation:** In both functions, replace the `else: break` with a full scan. In insert_note_into_book_file (promote.py ~line 246-249):

  if existing_key < new_key:
      insert_after_lineno = tup.end_lineno
  # remove the else: break — scan all tuples regardless

In batch_insert_notes (promote.py ~line 340-343):

  if (ech, ev, suffix_rank(esuf)) < new_key:
      after = eend
  # remove the else: break

Additionally, add a sort key to write_book() in web_helpers.py before serializing so future web-UI writes maintain sorted order:

  for tup in sorted(notes, key=lambda t: (t[0], t[1], (0,"") if t[2]=="" else (1,t[2]))):

This is safe, cheap (O(n log n) over a list that is already nearly sorted in practice), and does not affect byte stability of any edition build output since load_notes reads all tuples regardless of file order.

### opt-14. [low] is_output_current mtime cache ignores content/notes/*.py — corpus edits silently produce stale builds
- **Location/context:** `YHWH v2.4/scripts/build_edition.py:1943-1965`
- **Evidence:** is_output_current watches `epub_working/*.html`, `content.opf`, `nav.xhtml`, `stylesheet.css`, `editions.yaml`, `build_edition.py` — but NOT `content/notes/*.py`. The notes corpus is the primary per-edition variable: notes are injected into epub_working at inject time (pre-build), so they ARE baked into the base HTML. However editions.yaml edits (e.g. enabling a new kind) combined with an unchanged note corpus CAN legitimately produce a different EPUB. More critically: if the user edits a note after the last inject, then rebuilds without re-injecting, `is_output_current` returns the old EPUB as current. In a normal workflow (inject → build → edit note → build again without inject) the user gets the pre-edit EPUB. The content-addressable cache (`build_cache.compute_cache_key`) at lines 2723-2754 does NOT fall through to the mtime check when `cache_key` is None — the mtime check remains the sole fast path in that case.
- **Recommendation:** The content-addressable cache (`build_cache.compute_cache_key`) already hashes every in-canon `content/notes/<book>.py` at step 5, so the primary fast path is correct. The gap exists only in the `is_output_current` fallback, which runs only when `cache_key is None` (exception path). The proposed fix is valid for hardening that fallback: in `YHWH v2.4/scripts/build_edition.py` line 1961, after `sources.append(REPO_ROOT / "scripts" / "build_edition.py")`, add:

    notes_dir = REPO_ROOT / "content" / "notes"
    if notes_dir.is_dir():
        sources.extend(notes_dir.glob("*.py"))

Do NOT remove `is_output_current` entirely — it remains a useful fallback when the cache directory is absent or cleared. Note that `is_output_current` also misses `canons.yaml`, `kinds.yaml`, `categories.yaml`, and `books.yaml`; those could be added to the same sources list for completeness, but are equally low-priority since the content-addressable cache covers all of them too.

### opt-15. [low] do_POST fallthrough to do_PUT causes double _check_admin_auth() when no POST route matches
- **Location/context:** `YHWH v2.4/scripts/web.py:2054-2055`
- **Evidence:** do_POST (line 2016-2017) calls _check_admin_auth() first, then at line 2055 falls through to self.do_PUT() (line 1895-1897) which calls _check_admin_auth() a second time. With TOTP enabled this performs two TOTP code verifications on the same code. The supplied_code is validated against the same time window twice. Separately, do_POST already called _read_body() lazily (line 2036) for the first matching POST route; if no POST route matched, rfile is unread — so do_PUT's _read_body() call reads from the stream correctly. The auth double-call is the material issue.
- **Recommendation:** Replace line 2055 in `YHWH v2.4/scripts/web.py`:

    # Before:
    return self.do_PUT()

    # After:
    return self._send_json({"error": "not found"}, status=404)

This is a one-line change. No other modifications are needed. If any existing POST paths were intentionally sharing PUT handler logic via this fallthrough, they should be explicitly added to `_POST_ROUTES` instead — but reviewing `_POST_ROUTES` (lines 817–919) and `_PUT_ROUTES` shows no documented intent for shared routes, so the fallthrough appears to be an unintentional holdover from before the route-table migration rather than a deliberate design.

### opt-16. [low] lru_cache on _load_notes_cached uses path string + mtime_ns but mtime_ns resolution can be 1s on some Windows filesystems — stale cache window
- **Location/context:** `YHWH v2.4/scripts/core/notes_io.py:194-202`
- **Evidence:** @functools.lru_cache(maxsize=256) def _load_notes_cached(path_str: str, mtime_ns: int) — on FAT32 or some older Windows NTFS volumes, mtime granularity is 1–2 seconds. If atomic_write completes and a subsequent load_notes() call arrives within the same mtime second, it gets the stale cache entry because mtime_ns did not change. The _invalidate_corpus_index_if_notes_file hook in atomic_write (line 86) fires for notes files, but it only invalidates the corpus_index — it does NOT call clear_load_notes_cache(). So a rapid write→read within the same mtime-second window returns the old NOTES list.
- **Recommendation:** In YHWH v2.4/scripts/core/notes_io.py, add a call to clear_load_notes_cache() inside _invalidate_corpus_index_if_notes_file (the single-responsibility hook already called by both atomic_write and atomic_write_bytes), so both writers get the fix for free. Change lines 124-130 to:

    try:
        if path.suffix == ".py" and path.parent.name == "notes":
            clear_load_notes_cache()          # belt-and-suspenders: mtime resolution
            from scripts.core import corpus_index
            corpus_index.invalidate()
    except Exception:  # noqa: BLE001
        pass

This is one line added inside the existing try block. clear_load_notes_cache() is defined in the same file (line 225) so there is no import needed. Both atomic_write (line 86) and atomic_write_bytes (line 110) already call _invalidate_corpus_index_if_notes_file, so both get the fix. No marathon core files touched, no byte-stability impact (in-memory parse cache only), no new dependencies.

### opt-17. [low] api_restore_backup writes snapshot bytes without validating they are valid UTF-8 Python source before overwriting a notes file
- **Location/context:** `YHWH v2.4/scripts/web_content.py:644-645`
- **Evidence:** notes_io.atomic_write_bytes(abs_path, snapshot_bytes) — the restore writes raw bytes from the backup file without checking whether the target is a .py notes file that should be valid UTF-8 Python source. If the backup was of a notes file and the backup is somehow corrupt (truncated, binary garbage from a bad shutil.copy2), the notes corpus will be silently replaced with unparseable content. load_notes() then returns None for that book, which build_edition treats as an empty notes list — silently dropping all notes for that book from every future build.
- **Recommendation:** In `api_restore_backup` (YHWH v2.4/scripts/web_content.py), after reading `snapshot_bytes` at line 622 and before calling `atomic_write_bytes` at line 645, add a guard scoped to `.py` notes files only:

```python
if abs_path.suffix == ".py" and abs_path.parent.name == "notes":
    try:
        snapshot_text = snapshot_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return {
            "status": "error",
            "code": "invalid_snapshot",
            "http": 400,
            "message": "snapshot is not valid UTF-8 — will not restore a corrupt notes file",
        }
    from scripts.core.notes_io import load_notes_from_text
    if load_notes_from_text(snapshot_text) is None:
        return {
            "status": "error",
            "code": "invalid_snapshot",
            "http": 400,
            "message": "snapshot failed to parse as a notes module — will not restore",
        }
```

This mirrors the parse-before-write discipline already used in the corpus ingest pipeline, is gated strictly to `.py` notes files (so binary restores like cover images are unaffected), requires no new dependencies, and does not touch any marathon core file.

## Refuted findings (NOT actionable — convergence record)

| Sev | Dimension | Title | Why refuted (13 total) |
|-----|-----------|-------|-------------|
| medium | security | url_override in sources/cache/fetch bypasses the configured-source allowlist and can reach any http(s) host | I read the full call chain directly.  **What the code actually does:**  1. `api_sources_cache_fetch` (sources.py:163-187) checks only `startswith(("http://", "https://"))` at the API boundary - confirmed by reading the file.  2. `fetch_sour …[clipped] |
| low | security | TOTP provisioning_uri (containing the base32 secret) returned in plain-text JSON response without any transpor …[clipped] | I read the full file at C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4\scripts\api\auth.py and the relevant sections of scripts/web.py and scripts/core/audit_log.py.  The code does what the finding describes (returns secret + provisionin …[clipped] |
| low | security | api_download_export filename passed directly to Content-Disposition header without sanitization of the edition …[clipped] | I read all three relevant code sites directly.  1. `build_edition.py` line 2663 uses `strftime("%Y-%m-%dT%H%M%SZ")` which produces timestamps of the form `2026-05-31T123456Z` — dashes in the date part, no colons anywhere. The `All_Editions` …[clipped] |
| medium | code-debt | write_queue simple-append body duplicated identically across run_xref, run_naves, and run_torrey at-scale driv …[clipped] | I read all three cited files (run_xref_at_scale.py:39-67, run_naves_at_scale.py:39-68, run_torrey_at_scale.py:40-66) and confirmed the bodies are indeed identical. The finding is factually accurate as a code observation.  However, I also re …[clipped] |
| medium | docs | scripts/core/matrix.py docstring note count '67,715 today' is a stale snapshot | I read matrix.py lines 1-30 and confirmed line 13 says `content/notes/*.py — actual notes (67,715 today)`. I also read CLAUDE_PROJECT_RULES.md lines 145-159 in full. The "do NOT hard-code a figure here — it rots" prohibition at line 151 use …[clipped] |
| low | byte-stability | build_edition.build_one main filter loop (line 2846) and dry-run loop (line 2768) use unsorted glob — order is …[clipped] | I read the actual code at all four cited locations.  Lines 2768 and 2846 do use unsorted `glob("*.html")` — that part of the evidence is accurate. Lines 1574 and 1719 do use `sorted(...)` — the style inconsistency is real.  However the clai …[clipped] |
| medium | opt-vision | corpus_index._build_to uses PRAGMA synchronous=OFF — crash during rebuild loses the old index | Read lines 470-525 of YHWH v2.4/scripts/core/corpus_index.py directly. The finding's central claim — "the current except block (not shown here but absent) should unlink .tmp if os.replace has not yet run" — is factually wrong. The except bl …[clipped] |
| low | opt-vision | BACKUP_FILENAME_RE timestamp slice uses wrong index offsets — IndexError on malformed timestamps, silently fal …[clipped] | The finding is refuted. The slicing at web_content.py:523-524 operates on `ts`, which is the named capture group `ts` from `_BACKUP_FILENAME_RE` (line 448). That regex pattern is `\d{8}T\d{6}Z` — eight digits, literal `T`, six digits, liter …[clipped] |
| info | opt-vision | OPTIMIZATION RE-EVAL: Vision marathon method — CONFIRM-OPTIMAL for Patrologia Esther given today's constraints | I read the plan file (`YHWH v2.4/docs/superpowers/plans/2026-05-28-geez-patrologia-vision-plan.md`), the `_vision_notes.md` accumulator (`YHWH v2.4/content/translations/sources/patrologia/_vision_notes.md`), and the concurrency cap memory ( …[clipped] |
| info | opt-vision | OPTIMIZATION RE-EVAL: Kings/Samuel dual-manuscript marathon — CONFIRM-OPTIMAL with one parallelism improvement …[clipped] | I read the full Kings collation plan (`YHWH v2.4/docs/superpowers/plans/2026-05-17-kings-manuscript-collation.md`, lines 11–15) and the `feedback_concurrent_agent_cap` memory (all three updates, especially the 2026-05-27 update at lines 63– …[clipped] |
| high | opt-ingest | batch_insert_notes: intra-batch duplicate notes are not deduplicated — re-running a driver + --by-book promote …[clipped] | I read the actual code at YHWH v2.4/scripts/promote.py lines 307-355 and confirmed the mechanics described: `existing_bodies` is populated from on-disk tuples only and is never updated during the batch loop. The proposed fix (adding `existi …[clipped] |
| medium | opt-ingest | run_hebrew, run_greek, run_ai_xrefs, run_ai_notes write_queue: re-running the driver silently resets 'promoted …[clipped] | Verified by reading all four driver files and the full promote pipeline.  The finding is factually accurate about what the code does: `run_hebrew_at_scale.py` L49, `run_greek_at_scale.py` L48, `run_ai_xrefs_at_scale.py` L100, and `run_ai_no …[clipped] |
| low | opt-ingest | Ingest pipeline optimization: write_queue is copy-pasted across 9 drivers in at_scale_base.py's own module wit …[clipped] | I read all 10 write_queue definitions across the drivers and prospect.py.  The finding correctly observes the duplication (it is real) but the case for refactoring is weaker than presented, and the design is already deliberately documented. …[clipped] |

## Completeness gaps (seed the next convergence round)

1. **versification.py — LXX/Vulgate/Douay Psalm-map unit coverage vs the actual _psalm_map() function** — The audit found many ingest-level versification findings (Sirach segments, 1 Esdras, Judith) but the `_psalm_map()` function itself — the shared O(150-chapter) LXX↔KJV Psalm renumbering table reused by BOTH the LXX Swete path and the `vulgate_to_kjv` path — has no dedicated unit tests probing the fo …[clipped]  
   _Lens:_ Grep for `_psalm_map` in scripts/core/versification.py; read its logic; then grep for `lxx_to_kjv` or `_psalm_map` in tests/ to confirm no test calls it directly. Write one parametrized test class that feeds every four-seam Psalm chapter pair (ch 9, 10, 113, 114, 115, 146, 147) to `lxx_swete_to_kjv( …[clipped]
2. **standalone_store.py — bare write_text (non-atomic) for translation store writes that land in content/translations/** — The audit flagged non-atomic writes in prospect.py and all run_*_at_scale.py candidate-JSON functions, but missed standalone_store.py lines 84-85 and 162 where `build_book_store` and `build_psalms_apparatus` use bare `Path.write_text()` to produce `geez-tewahedo/<book>.py` and `<book>_apparatus.json …[clipped]  
   _Lens:_ Read scripts/core/standalone_store.py lines 80-90 and 155-165. Grep `write_text` in scripts/core/standalone_store.py to confirm all 3 instances are bare (no `atomic_write` import). Confirm `notes_io.atomic_write` exists and covers `.py` files. The fix is a 3-line import + call swap, but the gap is w …[clipped]
3. **corpus_index fingerprint uses mtime+size rather than content hash — not covered by byte-stability tests** — `corpus_index._compute_fingerprint()` uses `(stem, st_size, st_mtime_ns)` as its invalidation key. On Windows, NTFS mtime resolution is 100 ns but some file systems (FAT32, older Windows NFS mounts, some VMs) are 1-2 s. If two sequential atomic_writes land within the resolution window, the second wr …[clipped]  
   _Lens:_ Read scripts/core/corpus_index.py `_compute_fingerprint()` and `_FINGERPRINT_TTL_SEC`. Write a test that calls `atomic_write` twice in rapid succession (using time.sleep(0) between), then calls `corpus_index.fingerprint()` and asserts the second fingerprint differs from the first. If the two fingerp …[clipped]
4. **build_cache.compute_cache_key omits epub_working/ subdirectories (META-INF/ was flagged, but also onix/ subdirectory)** — The audit flagged that `compute_cache_key` only walks `epub_working/*.` top-level files, missing `META-INF/container.xml`. But there is also an `epub_working/onix/` subdirectory containing 5 ONIX XML files (listed in REPO_MAP §epub_working). These are vestigial commercial metadata but their presence …[clipped]  
   _Lens:_ Read scripts/core/build_cache.py lines 238-248 (the epub_working/ walk). Confirm that `entry.iterdir()` for subdirectories is not called (it isn't — `is_file()` gates every entry). Then list `epub_working/` with PowerShell `Get-ChildItem -Recurse` to inventory all subdirs (META-INF, onix at minimum) …[clipped]
5. **matter_pages.py / render_reading_plans_page — no dedicated test file; reading-plan parsing edge cases uncovered** — The `reading_plans.py` module has a regex parser (`_REF_RE`) for verse references like `gen 1:1-2:3` (cross-chapter) and `psa 1`, and `parse_verse_ref` returns `None` for 'unsupported shapes' — but no test directly exercises the parser's failure modes: what does it do with book codes not in books.ya …[clipped]  
   _Lens:_ Grep `reading_plans` in tests/test_scripts.py to find the existing coverage. Read scripts/core/reading_plans.py `parse_verse_ref()` and `_REF_RE`. Then check content/reading_plans/ (glob it) to see what plan files exist and what edge-case verse refs they contain. Write a test that calls `parse_verse …[clipped]
6. **verse_of_day.py — rss_feed body_html injection (already flagged as RSS XSS) BUT also: verse picker assumes notes are sorted; no test for edition-filtered corpus with zero notes** — The existing audit flagged `body_html` injected raw into CDATA. A second unexamined hazard in the same module: `_pick_verse` falls back across `(chapter, book)` combinations until it finds a verse with notes, using a deterministic `seed % len(candidates)` traversal. If an edition's canon has no note …[clipped]  
   _Lens:_ Read scripts/core/verse_of_day.py lines 115-200 (picker) and 292-356 (rss_feed). Check whether there is a test in test_scripts.py under 'verse_of_day' or 'rss_feed'. Write a test with a tmp_path notes_dir containing zero .py files and a monkeypatched edition, asserting rss_feed returns a syntactical …[clipped]
7. **extract_naves_ccel.py CCEL_ABBREV and extract_eastons_ccel.py EASTON_BOOK — the lint check `bookcode_canonical` explicitly does NOT cover these two maps** — The audit's last finding explicitly names `bookcode_canonical` lint not covering `CCEL_ABBREV` or `EASTON_BOOK`. This is a gap finder for the NEXT round: both maps were apparently correct at time of writing (all values are canonical codes) but neither map is guarded by the pre-commit lint. If a futu …[clipped]  
   _Lens:_ Read scripts/extract_naves_ccel.py lines 1-121 fully (CCEL_ABBREV + NAVES_BOOK_REMAP combined). Confirm whether NAVES_BOOK_REMAP also exists and whether it contains legacy aliases (`joh`, `jas`, `mar`, `ezk`, `nam`, `php`) that would bypass `_normalize_book_code`. Then read lint_rules.py `check_book …[clipped]
8. **_replace_verse_popup_translation() — tested but not wired; no integration test proving the popup-language prune path removes the right <aside> elements from the built EPUB** — The audit flagged that `_replace_verse_popup_translation` is NOT YET WIRED (mint-7 D3). But a second gap exists upstream: `_apply_popup_languages_and_translation()` in build_edition.py is wired and runs on every build — it prunes `<aside class="vnote">` elements whose version id is not in the editio …[clipped]  
   _Lens:_ Grep `_apply_popup_languages_and_translation` in scripts/build_edition.py to find the pruning logic (around lines 907-990). Check tests/test_popup_witnesses.py for whether any test calls `filter_html` or `_apply_popup_languages_and_translation` directly with a fake HTML chunk. The gap is confirmed i …[clipped]
9. **work_cache.py — WorkCache.get_or_compute() is not thread-safe between the get() check and the compute_fn() invocation** — WorkCache is explicitly designed for use from parallel_map's worker threads (docstring: `check_same_thread=False + a mutex`). The `get_or_compute` method calls `self.get(key)` (lock-protected), then RELEASES the lock, then calls `compute_fn()` (which may be a slow API call), then calls `self.put(key …[clipped]  
   _Lens:_ Read scripts/core/work_cache.py lines 40-90 (`get_or_compute` method). Check whether the lock is held during `compute_fn()` — it isn't. Write a test with `threading.Barrier` to confirm two threads calling `get_or_compute` with the same key both invoke the compute function (the current behavior). The …[clipped]
10. **NAVES_BOOK_REMAP in extract_naves_ccel.py — separate from CCEL_ABBREV, likely contains legacy codes, not audited** — The audit's bookcode_canonical finding scoped itself to CCEL_ABBREV and EASTON_BOOK by name. But extract_naves_ccel.py has a second book-code map, NAVES_BOOK_REMAP, that is used as a fallback in the `remap()` function (line 121: `CCEL_ABBREV.get(a) or NAVES_BOOK_REMAP.get(a) or NAVES_BOOK_REMAP.get( …[clipped]  
   _Lens:_ Read scripts/extract_naves_ccel.py lines 1-40 to find NAVES_BOOK_REMAP (it precedes CCEL_ABBREV in the file — read from the top). Confirm whether NAVES_BOOK_REMAP contains any of the legacy codes `joh`, `jas`, `mar`, `jol`, `ezk`, `nam`, `php`. If it does, grep content/sources/naves_topical.json for …[clipped]
