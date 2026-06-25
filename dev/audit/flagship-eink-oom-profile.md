# Flagship eink build — OOM memory profile (P1)

> **Mac → WIN, 2026-06-25.** Where the `ethiopian-tewahedo --target-reader eink` build's remaining
> memory peak lives, after your two streaming fixes (`_merge_scripture_base_files` `23973e7d`,
> `write_eink_study_backmatter_page` `a9c3857b`). **Findings-only — you implement the reductions in
> `build_edition.py`.** Reusable profiler shipped: **`dev/audit/eink_oom_profile.py`** (tracemalloc +
> RSS sampler, ready to run for empirical confirmation — see "Empirical status" below).

## TL;DR — THE remaining OOM driver (verified by code, one-line fix)

**`stats["_study_backmatter_entries"]` — the ~73 MB Kobo study-glossary entries list — is built up,
consumed once, and then NEVER released.** It rides inside `stats` (which `build_one` returns) straight
through `inject_back_matter`, the reading-plans/nav passes, **all of `apply_file_split`**, and the
**entire `build_epub` zip**. Because the source list outlives them, your two streaming fixes don't touch
the peak: at the moment `apply_file_split` runs, the orphaned 73 MB list co-resides with the splitter's
own 2–3× re-materialization of the same glossary (#2) → the worst co-residency moment in the build.

**Cheapest high-impact fix (frees ~73 MB before file-split + zip):**
```python
# scripts/build_edition.py — right AFTER line 8082 (after inject_eink_study_backmatter has consumed it
# and both bm_stats fields are extracted), BEFORE inject_back_matter at :8083:
del stats["_study_backmatter_entries"]
```
eink-specific (only populated when target=eink AND `reader_eink_study_layout == "backmatter"`); the
returned `stats` keeps the integer `study_backmatter_entries` count, just not the 73 MB payload list.

## Build architecture — where to look (and where NOT to)

The peak is **in the `build_edition.py` process** (the inject → badge → backmatter → `apply_file_split`
chain inside `build_one`). The `build_epub.py` zip step is a **subprocess** that streams **per file**
(`zf.writestr(zi, path.read_bytes(), compresslevel=9)`, `build_epub.py:161`) — it never holds the whole
EPUB in memory, so it is **not** the hog. Therefore in-process tracemalloc on `build_one` captures the
remaining site class (the profiler runs `build_one` in-process for exactly this reason).

## Ranked remaining memory-peak sites (file:line verified)

### #1 — THE driver: the 73 MB glossary entries list is never freed → co-resides with #2
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

## Recommended implementation order (WIN)
1. **#1 `del`** (one line, ~73 MB freed before file-split/zip) — do this first; likely resolves the OOM alone.
2. **#2 stream `apply_file_split`** per-file (removes the 2–3× glossary re-materialization).
3. **#4 `del pre_badge_texts` / `del repair_texts`** (trivial, cuts the steady baseline on every target).
4. **#3** free `file_texts` rows + shard the entries to disk (deeper; do if #1+#2 don't fully clear it).
All are determinism-neutral (free/stream the same bytes) → re-verify with the byte-stability gate; eink
output unchanged; 9-KJV untouched (#1/#2/#3 glossary half are eink-only; #4 is a free-after-use no-op).

## Empirical status — tracemalloc run PENDING (blocked on this box's RAM)
The empirical tracemalloc/RSS profile was **not run this session**: this 8 GB box is saturated — an
**orphaned runaway** (`PID 33524`, `.venv/bin/python -`, parent=launchd, 4.5 h at ~99 % CPU, holding
~3.1 GB) leaves only ~250–500 MB free, so launching a multi-GB eink build would thrash/freeze the
machine. The static analysis above is conclusive (verified file:lines + a confirmed missing `del`), so
#1 is actionable now without it. To capture the empirical peak (top allocators at peak + peak RSS +
crash point) once RAM is freed — kill `33524`, then:
```
.venv/bin/python dev/audit/eink_oom_profile.py ethiopian-tewahedo --target-reader eink
# if 8 GB still OOMs, the smaller fallback localizes the same per-write peak:
.venv/bin/python dev/audit/eink_oom_profile.py catholic-study --target-reader eink
```
The profiler keeps the tracemalloc snapshot from the highest point seen and, on `MemoryError`, dumps the
crash-point snapshot — so it produces a usable ranking whether the build completes or OOMs. I'll fold the
real numbers into this file when the box has headroom; the #1 fix doesn't wait on it.
