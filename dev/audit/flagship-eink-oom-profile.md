# Flagship eink build — OOM memory profile (P1)

> **Mac → WIN, 2026-06-25.** Where the `ethiopian-tewahedo --target-reader eink` build's remaining
> memory peak lives, after your two streaming fixes (`_merge_scripture_base_files` `23973e7d`,
> `write_eink_study_backmatter_page` `a9c3857b`). **Findings-only — you implement the reductions in
> `build_edition.py`.** Reusable profiler shipped: **`dev/audit/eink_oom_profile.py`** (tracemalloc +
> RSS sampler, ready to run for empirical confirmation — see "Empirical status" below).
>
> **★★ 2026-06-26 UPDATE — re-profiled after your #1 streaming fix (`d6c3d270`); it DIAGNOSES the
> "~1.4 GB post-retarget" site you couldn't. Jump to "Post-#1 re-measure" at the bottom.** TL;DR: peak
> dropped 3591 → 2460 MB tracked (RSS 2937 → 2865 — barely, Python retains freed arenas). The remaining
> ~2 GB is `_iter_study_glossary_pieces` STILL holding the ~485 MB glossary **~3× at once** (`text` kept
> alive for fallback-yields + `_split_head_body_tail` + `_study_index_section_parts` slice sets). The
> docstring's "peak ~one ~480 MB copy" is **not** achieved.

## TL;DR — THE remaining OOM driver (verified by code, one-line fix)

> **★ EMPIRICAL (flagship `ethiopian-tewahedo --target-reader eink`, completed under tracemalloc on the
> 8 GB Mac, 2026-06-25): peak RSS 2937 MB · tracemalloc-tracked peak 3591 MB.** The empirical run
> **corrects the "73 MB" docstring figure** — the flagship study-glossary is **~480–490 MB** (the corpus
> grew to ~91 k notes / ~30 k glossary entries) — and shows the **dominant** peak is not the never-freed
> list alone but **`split_study_glossary_document` / `apply_file_split` holding ~5 SIMULTANEOUS full
> copies of that ~480 MB glossary** (read_text + 3 slice stages + pieces ≈ 2.4 GB), with the never-`del`'d
> ~489 MB entries list co-residing on top. See "Empirical results" below for the per-line table.

Two co-dominant problems, both centred on the same ~480 MB study glossary:

**(A) The split pipeline copies the ~480 MB glossary ~5× at once.** `split_study_glossary_document`
(`build_edition.py:5071`) does `read_text` → `_split_head_body_tail` → `_study_index_section_parts` →
`_study_glossary_chunk_atoms` → `pieces.append(head+body+tail)` — each a **full-size copy**, all alive at
the same instant inside `apply_file_split`'s `plan` dict. Empirically ≈ 2.4 GB. **This is the biggest single
cost** (the static pass under-weighted it because the docstring said 73 MB).

**(B) `stats["_study_backmatter_entries"]` (~489 MB) is built, consumed once, and NEVER released** — it
rides in `stats` (which `build_one` returns) through `inject_back_matter`, the nav passes, **all of
`apply_file_split`**, and the zip, so it co-resides with (A) at the peak.

**Fixes, by leverage:**
1. **Stream the glossary split (biggest win, ~2 GB).** Refactor `split_study_glossary_document` +
   `apply_file_split` to chunk the glossary incrementally and write each piece to disk as produced,
   releasing each slice — never hold `read_text` + all slice stages + all pieces simultaneously.
2. **`del stats["_study_backmatter_entries"]` (cheap, ~489 MB, one line).**
   ```python
   # scripts/build_edition.py — right AFTER line 8082 (after inject_eink_study_backmatter consumed it
   # and both bm_stats fields are extracted), BEFORE inject_back_matter at :8083:
   del stats["_study_backmatter_entries"]
   ```
   eink-specific; the returned `stats` keeps the integer count, just not the payload list.

Together these take the ~2.9 GB peak to well under 1 GB. (1) is the structural fix; (2) is the cheap
immediate relief. Also fix the stale `split_study_glossary_document` docstring (`:5075`, "73 MB" → ~480 MB).

## Build architecture — where to look (and where NOT to)

The peak is **in the `build_edition.py` process** (the inject → badge → backmatter → `apply_file_split`
chain inside `build_one`). The `build_epub.py` zip step is a **subprocess** that streams **per file**
(`zf.writestr(zi, path.read_bytes(), compresslevel=9)`, `build_epub.py:161`) — it never holds the whole
EPUB in memory, so it is **not** the hog. Therefore in-process tracemalloc on `build_one` captures the
remaining site class (the profiler runs `build_one` in-process for exactly this reason).

## Ranked remaining memory-peak sites (file:line verified)

> **Note on the "73 MB" figures below:** those were the static pass's read of the stale
> `split_study_glossary_document` docstring. The **empirical run measured the flagship glossary at
> ~480–490 MB** — so multiply every "73 MB" here by ~6.6×, and see the empirically-re-ranked order in the
> TL;DR + "Empirical results". The *sites* are all correct; only the magnitudes were under-stated.

### #1 — the glossary entries list is never freed → co-resides with the split (#2)
- Built incrementally in `apply_badge_markers`: init `scripts/build_edition.py:4032`
  (`"study_backmatter_entries": []`), appended per verse at `:4274`
  (`stats["study_backmatter_entries"].append((…, code, unit_aside))` — each `unit_aside` is the full
  `<div class="study-glossary-entry">…</div>` HTML for one verse; summed over the 87-book superset ≈ the
  whole **73 MB** glossary as tens of thousands of `str` objects).
- Promoted into `build_one`'s `stats` at `:8036`, consumed once at `:8080`
  (`inject_eink_study_backmatter`). **`grep` confirms NO `del` of it anywhere** — so it stays alive in
  `stats` through `:8083` `inject_back_matter` → `:8126` `apply_file_split` → `:8144+` the zip → the
  `return stats`. **Fix:** the `del` above. This is the single highest-leverage change.

### #2 — `apply_file_split` materializes every piece of every file at once (whole glossary 2–3×)
- `scripts/build_edition.py:5467`–`5486`: `plan: dict[str, list[tuple[str,str]]]` accumulates **all
  pieces of all source files simultaneously** — `text = p.read_text(...)` (`:5469`) reads the 73 MB
  glossary file whole, and `split_study_glossary_document` (defined `:5071`, the *"73 MB monolith"*
  docstring) builds `atoms` (`:5090`) + `groups` (`:5096`) — additional full-length copies of the inner
  text held at the same time as the incoming `text` and the outgoing `plan` pieces. The glossary is
  resident ~2–3× here, **on top of #1's orphaned copy**.
- **Fix:** stream the split — process one source file at a time and write each piece to disk as produced
  (drop `text`/`atoms`/the piece after writing) instead of holding every file's pieces in one `plan`
  dict; make the id-map pass (`:5536`) a separate cheap scan over the on-disk pieces. (eink-specific in
  magnitude: the merged single scripture stream + the glossary file only exist on eink.)

### #3 — `apply_badge_markers`: all body HTML (`file_texts`) co-resident with the growing entries list
- `scripts/build_edition.py:4040`–`4046`: `file_texts: dict[str,str]` lazily loads but **accumulates
  every surviving split file** (the whole scripture body, tens of MB), held until the function returns
  (`:4418`) — peaking simultaneously with the 73 MB `study_backmatter_entries` it is building (#1).
- **Fix:** free each `file_texts[fname]` right after its write-back (`:4415`); and append glossary
  entries to an on-disk shard (NDJSON / temp file) as each verse is emitted rather than into `stats[...]`.

### #4 — Secondary (all targets): two full-body-HTML dicts never freed
- `:7983` `pre_badge_texts = {name: read_text() …}` and `:8041` `repair_texts = {name: read_text() …}` —
  each holds **all** body HTML at once, written back (`:8018` / `:8058`) but never `del`'d, so two
  redundant whole-body copies linger in `build_one`'s frame through file-split + zip. Scripture-body
  sized (not 73 MB) and on every target → a steady baseline, not the eink spike.
- **Fix:** `del pre_badge_texts` after `:8019`; `del repair_texts` after `:8059`.

### #5 — Minor / inherent
- `notes_io.load_notes` `@lru_cache(maxsize=256)` (`scripts/core/notes_io.py:216`) can hold up to 256
  parsed note files — bounded + evictable, well below the glossary; not the driver. The whole-file
  `read_text` of the 73 MB glossary at `:5469` is inherent to splitting and is subsumed by the #2 fix.
- NOTE: `sorted(entries, …)` at `scripts/matter_pages.py:1109` is **not** a second 73 MB copy — `sorted()`
  returns a new list of references to the same tuples/strings (~a few MB of pointers). Don't over-weight it.

## Recommended implementation order (WIN) — empirically re-ranked
1. **Stream `split_study_glossary_document` + `apply_file_split`** (the ~5× ~480 MB copy = ~2.4 GB, the
   biggest single cost; chunk + write-per-piece, release each slice). **This is the structural fix.**
2. **`del stats["_study_backmatter_entries"]` after `:8082`** (one line, frees ~489 MB before file-split/zip).
3. **`del pre_badge_texts` / `del repair_texts`** (`:8019` / `:8059`; ~131 + 16 MB, trivial).
4. Free `file_texts` rows in `apply_badge_markers` (`:4415`) + shard glossary entries to disk (deeper).
Also correct the stale `split_study_glossary_document` docstring (`:5075`: "73 MB" → ~480 MB).
All are determinism-neutral (free/stream the same bytes) → re-verify with the byte-stability gate; eink
output unchanged; 9-KJV untouched (the glossary path is eink-only; the `del`s are free-after-use no-ops).

## Empirical results — flagship eink, COMPLETED under tracemalloc (2026-06-25, 8 GB Mac)
Ran `dev/audit/eink_oom_profile.py ethiopian-tewahedo --target-reader eink` (force=True) after clearing
the box. **Build completed in 2702 s** (45 min — tracemalloc roughly halves throughput; a normal build is
much faster). **Peak RSS (ru_maxrss) = 2937 MB · tracemalloc-tracked peak = 3591 MB.** That ~2.9 GB peak
is why it OOMs "under RAM pressure" (build cache + a parallel `--all` build + other apps tip a 16 GB box,
and an uncleared 8 GB box has no room at all).

**Top allocators by file:line at peak** (the ~480 MB glossary, copied many times):

| MB | blocks | site | what |
|---:|---:|---|---|
| 538 | 14 | `pathlib:788` (`f.read()`) | file reads (the glossary `read_text` + body reads) |
| 489 | 30,148 | `build_edition.py:4271` | **the never-`del`'d entries list** — glossary-entry `<div>` HTML strings |
| 488 | 4 | `build_edition.py:4720` | `_split_head_body_tail` slice of the glossary |
| 488 | 2 | `build_edition.py:5043` | `_study_index_section_parts` slice |
| 482 | 29,674 | `build_edition.py:5065` | `_study_glossary_chunk_atoms` chunk copies |
| 480 | 1,373 | `build_edition.py:5120` | `split_study_glossary_document` `pieces.append(head+body+tail)` |
| 149 | 501 | `build_edition.py:5010` | `split_html_document` pieces (scripture body) |
| 148 | 61 | `build_edition.py:2639` | `add_eink_vnote_preview_breaks` regex `.sub` (full-copy) |
| 135 | 47 | `<frozen codecs>` | utf-8 decode of the reads |
| 131 | — | `build_edition.py:7983` | `pre_badge_texts` whole-body dict (never freed) |

The five ~480–490 MB rows (`5469`/`4720`/`5043`/`5065`/`5120`) are the SAME glossary held simultaneously
across the split stages ⇒ ≈ 2.4 GB; plus the 489 MB orphaned entries list (`4271`) co-resident ⇒ the
~2.9 GB peak. Confirms (A)+(B) above and the empirical re-rank. The profiler is reusable for the post-fix
re-measure (`dev/audit/eink_oom_profile.py`; falls back to `catholic-study --target-reader eink`).

## Post-#1 re-measure — the remaining "post-retarget" site DIAGNOSED (2026-06-26, mac)

Re-ran `dev/audit/eink_oom_profile.py ethiopian-tewahedo --target-reader eink` after the #1 streaming
fix (`d6c3d270`). **Build COMPLETED in 2694 s on the 8 GB Mac (via memory-compression).**

| metric | pre-#1 | post-#1 |
|---|---:|---:|
| tracemalloc-tracked peak | 3591 MB | **2460 MB** |
| sampler peak current | 3582 MB | 2333 MB |
| peak RSS (ru_maxrss) | 2937 MB | **2865 MB** |

The #1 fix freed ~1130 MB of *tracked* allocation (it removed the cross-FILE `plan`-dict that pooled
every file's pieces), but **RSS barely moved (2937 → 2865)** — Python keeps freed arenas resident, and a
big co-resident core remains. **This is the "~1.4 GB post-retarget" site your monitor saw OOM but
couldn't diagnose. It is actually ~2 GB, not 885 MB — the "885 MB monitored peak" under-measured the
true whole-build peak** (the monitor likely sampled outside the glossary-split window).

**Top live allocations at the post-#1 peak** (all the same ~485 MB glossary, multiple times):

| MB | site | what's live |
|---:|---|---|
| 485 | `build_edition.py:5547` → `pathlib:788` | `p.read_text()` — the whole glossary `text` passed into `_iter_study_glossary_pieces` |
| 485 | `build_edition.py:4751` (via `:5120` `_split_head_body_tail`) | `head, body, tail = text[:a], text[a:b], text[b:]` — a 2nd full copy |
| 485 | `build_edition.py:5074` (via `:5125` `_study_index_section_parts`) | `body_prefix, sec_open, inner, body_suffix` — a 3rd full copy |
| 356 | `build_edition.py:4300` (via `apply_badge_markers:8119`) | the `study-glossary-entry` `<div>` strings list |
| 258 | `build_edition.py:5096` (via `:5132` `_study_glossary_chunk_atoms`) | the chunk-atom copies of `inner` |

≈ **2.07 GB** in the top five — the ~485 MB glossary held **~3× simultaneously inside one
`_iter_study_glossary_pieces` call** (`text` + `_split_head_body_tail` slices + `_study_index_section_parts`
slices), plus the 356 MB entries list and 258 MB chunk atoms.

**Why it's still ~3×, despite the `del body`:** the generator keeps **`text` alive for its whole duration**
(every fallback `yield (stem, text)` path references the parameter), so the original 485 MB is never freed
while `_split_head_body_tail(text)` (another 485 MB) and then `_study_index_section_parts(body)` (another
485 MB) run. The `del body` only frees one of the three; `text`, `head`/`tail`, and the section-part
wrappers stay co-resident.

**Fix (deeper than #1 — the real terminus):** make `_iter_study_glossary_pieces` **index-based / single-pass**
so the glossary is held ~1× for real:
1. **Don't keep `text` alive for fallbacks** — decide the fallback (`len(text) <= target`, or split-failure)
   FIRST and return; once the section-split path is committed, drop `text` before slicing.
2. **Work with offsets into `text`, not full-size slices.** Replace `_split_head_body_tail` +
   `_study_index_section_parts` (which each return whole-length slice tuples) with `text.find()` boundary
   offsets, then slice + yield + release only each ~0.4 MB piece. No `head`/`body`/`tail`/`inner` full copies.
3. Optionally shard the `apply_badge_markers` entries (`:4300`, 356 MB) to a temp file incrementally instead
   of the in-RAM list (your earlier #3) — removes the co-resident 356 MB during the badge phase.
After (1)+(2) the glossary peak should fall from ~1.45 GB to ~0.49 GB (one copy), taking the whole build
well under 1 GB. Byte-identical (same cut points / same piece bytes — only the *order/lifetime* of the
slices changes). Re-run `eink_oom_profile.py` to confirm; catholic-study + canon-filtered editions already
build clean, so the gate is the flagship superset only.
