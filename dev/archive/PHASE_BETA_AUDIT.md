# Phase β Audit Report

**Date:** 2026-05-06 (post v28a-6 save)
**Scope:** Read-only inventory pass over `scripts/`, `content/`, `epub_working/`,
`source_archive/`, `kings_session/`. No destructive changes.
**Method:** AST scan + grep + filesystem stat + duplicate-function detection.

---

## Headline numbers

- **9,954 LOC** across 32 top-level scripts + 4 core modules
- **5 confirmed function duplications** (highest: `load_notes_from_text` × 5 copies)
- **0 / 4** note-writer scripts use atomic writes (HIGH RISK)
- **0** hash manifests / corruption detection
- **0** version control infrastructure (relies on save zips for rollback)

---

## PART 1 — Security & corruption-prevention findings

Ranked by severity. Every finding has a concrete fix and an effort estimate.

### S1. Note-writer scripts are NOT atomic — `[CRITICAL]`

**The risk.** Four scripts mutate `content/notes/<book>.py` files via direct
`path.write_text(...)`:

- `scripts/promote.py` (line ~221) — single book per call
- `scripts/add_note.py` (line ~213) — single book per call
- `scripts/attribute.py` (line ~217) — **walks all 87 books** in `--all-books` mode
- `scripts/bulk_edit.py` — N books per call

If the process is killed mid-write (Ctrl-C at the wrong instant, OOM, disk full,
power loss), the file is left **half-written and unparseable**. The notes for
that book are lost without a recent backup.

`attribute.py --all-books` (which I ran during Phase 4) wrote all 1,371 notes
across 87 files in sequence with zero crash protection. We got lucky.

**The fix.** Replace `path.write_text(text)` with the atomic pattern:

```python
def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)   # atomic on POSIX
```

Place in `scripts/core/notes_io.py`. Update all 4 writers + `promote.py`'s
queue-status writer (line 287). **Effort: ~30 min.**

### S2. No hash manifest / corruption detection — `[HIGH]`

**The risk.** If a notes file is silently corrupted (truncated download,
external tool, filesystem error), there's no way to know until the next
`verify.py` run — and even that won't catch *content* corruption, only
parse failures.

**The fix.** Add `scripts/manifest.py`:

- On save, walk `content/notes/*.py` and compute SHA-256 of each
- Store `content/notes/.manifest.json` with `{filename: sha256, mtime, size}`
- On bootstrap (or before any write), verify manifest matches actual files
- Flag any drift to the user

**Effort: ~45 min.** Run as a verification step in the bootstrap protocol.

### S3. No automatic pre-write backup — `[HIGH]`

**The risk.** Bulk operations like `attribute.py --all-books` or
`bulk_edit.py` could destroy the entire corpus on a regex error (one bad
substitution rule applied to 87 files). The save zip is the only fallback,
which may be hours stale.

**The fix.** Add `ensure_backup(book_path)` helper in `scripts/core/notes_io.py`:

- Before any mutation, copy `content/notes/<book>.py` →
  `content/notes/.backups/<book>.<ISO-timestamp>.py.bak`
- Auto-prune backups older than 7 days (or keep last 50 per book)
- Lightweight; only fires on writes, not reads

**Effort: ~30 min.** Pair with S1 in the same refactor.

### S4. No version control — `[MEDIUM]`

**The risk.** All rollback flows through saved zips. Per-edit history doesn't
exist. If a v28a-N change introduces a subtle bug, finding the introducing
edit requires diffing against the previous zip.

**The fix.** `git init` + `.gitignore` (excludes `.tools/`, `.cache/`,
`__pycache__/`, generated EPUBs, large binaries). Commit on every save.
Doesn't replace the save-zip workflow — augments it.

**Effort: ~15 min** initial setup; commits become a one-liner per save.

### S5. Cached PD corpora are writable — `[LOW]`

**The risk.** `content/sources/` holds the Strong's Hebrew dictionary
(~2 MB) and TSK cross-references (~5 MB). These are immutable PD data;
any write to them is by definition a bug or corruption.

Currently `chmod 755` (writable). An accidental script bug or external
tool could overwrite them with no warning.

**The fix.** `chmod 444` on the cached files. Add a check in
`fetch_sources.py` that only chmod-rewrites them on legitimate refetch.

**Effort: ~10 min.**

### S6. Candidate JSON files written non-atomically — `[LOW]`

`promote.py` line 287 updates candidate status with direct
`queue_path.write_text(json.dumps(...))`. Same atomicity risk as S1
but lower impact (candidates are recreated by `prospect.py` if lost).

**The fix.** Same `atomic_write` helper from S1. **Effort: 5 min** (one
line change after S1 is in place).

---

## PART 2 — Consolidation findings

Ranked by ROI (lines saved per refactor minute).

### C1. `load_notes_from_text` duplicated 5× — `[HIGH ROI]`

**Confirmed byte-identical** in:

- `scripts/bibliography.py`
- `scripts/citation_index.py`
- `scripts/glossary.py`
- `scripts/note_diff.py`
- `scripts/note_search.py`

Plus a near-duplicate `load_notes(path)` in `scripts/dashboard.py` that
does the same AST walk but takes a path instead of text.

**Lines saved:** ~70 across 6 files.

**The fix.** Move to `scripts/core/notes_io.py` as
`load_notes_from_text(text)` and `load_notes(path)`. Update 6 imports.
**Effort: ~30 min.**

### C2. `strip_tags` duplicated 4× — `[MEDIUM ROI]`

In `bibliography.py`, `note_diff.py`, `note_quality.py`, `note_search.py`.

**Lines saved:** ~20.

**The fix.** Move to a new `scripts/core/html_utils.py` module. Add
related helpers (`word_count`, the regex-based HTML cleaner). Update 4
imports. **Effort: ~15 min.**

### C3. `err` / `info` helpers + color constants — `[LOW ROI but quick]`

`err()` defined 4×, `info()` defined 3×. ANSI color constants
(`GREEN`, `RED`, `YELLOW`, `DIM`, `BOLD`, `RESET`) defined in 6+ files.

**Lines saved:** ~50.

**The fix.** Consolidate into `scripts/core/ui.py`. Update imports across
~10 files. **Effort: ~30 min** (more files touched).

### C4. `source_archive/` and `kings_session/` — `[KEEP, don't refactor now]`

12 KB and 60 KB respectively, only 3 Python files total. The Strategy-A
injector lives in `source_archive/` (queued for restoration in Phase ε).
Leave alone; revisit when Phase ε starts.

### C5. `nav.xhtml` / `toc.ncx` patching is partly modular — `[KEEP]`

`apply_style.py` has `patch_nav()` and `patch_visible_toc()`;
`set_reader_toc.py` has its own ToC ops. There's some overlap but not
clean duplication. Defer to Phase γ when we touch the in-book ToC anyway.

---

## PART 3 — Suggested sequencing for Phase β implementation

Two clusters; do **β.1 (security)** first because that's where the real risk lives.

### β.1 — Security pack `[~2 hours total]`

1. Create `scripts/core/notes_io.py` with `atomic_write()`,
   `ensure_backup()`, `load_notes_from_text()`, `load_notes()` _(also
   covers C1)_
2. Update 4 note-writer scripts (`promote.py`, `add_note.py`,
   `attribute.py`, `bulk_edit.py`) + `promote.py`'s queue-status writer
   to use atomic write + ensure_backup
3. Create `scripts/manifest.py` (SHA-256 manifest builder + verifier)
4. Add manifest verification to bootstrap protocol (HANDOFF banner step)
5. `chmod 444 content/sources/*` + verify in `fetch_sources.py`

**Result:** Note files become crash-safe; corruption becomes detectable;
PD corpora become tamper-evident.

### β.2 — Consolidation pack `[~1 hour total]`

6. Create `scripts/core/html_utils.py` (covers C2)
7. Create `scripts/core/ui.py` (covers C3)
8. Update imports across ~15 files
9. Run all tests: `verify.py`, `validate_taxonomy.py`, dashboard render

**Result:** ~140 LOC removed across the codebase; single source of truth
for shared helpers.

### β.3 — Optional infra `[~15 min, defer if you want]`

10. `git init` + initial commit + `.gitignore`

---

## NOT addressed by this audit (separate phases)

- **In-book ToC fix** (items 6, 7) — Phase γ
- **`retag.py` for legacy `comm` reclassification** — Phase δ
- **Strategy-A injection restoration** — Phase ε
- **More PD fetchers** (Charles 1913, Catena Aurea, BDB) — Phase ε
- **ONIX 3.0 metadata** — Phase ζ
- **Content authoring at scale** — Phase η

---

## Recommendation

Execute **β.1 first** in its own save unit. The atomic-write fix is the only
concrete corruption risk in the codebase right now and we just ran the most
exposed tool (`attribute.py --all-books`) without it. Then **β.2** as a
clean second pass. Then **Phase γ** (ToC) can begin.

Total Phase β implementation effort: ~3 hours of focused work, two save units.
