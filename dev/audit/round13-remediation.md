# Round-13 GRAND AUDIT — remediation tracker

**The user's end-state directive (2026-06-23):** "if you both finish all the fixes, run the full
auditor together again, top to bottom, down to verse + word, no time limit." Both lanes ran it after
ALL round-10/11/12 remediation landed. This tracks the WIN half + the merge.

## WIN half — `deep-audit` round-13 `LANE=win` (6 compute dims) — DONE

`wf_64ba6cb1-f47` · 30 agents · ~4h · Opus · scope=product · correct repo (startup log verified) ·
deferred=19 (prior settled items; this session's deferrals deliberately NOT suppressed so the audit
surfaces them — triaged here). **12 deduped → 9 survived (2 high · 5 med · 2 low) · 3 refuted.**

| # | sev | dim | finding | status |
|---|-----|-----|---------|--------|
| 1 | **HIGH** | tests-run | conftest `_PROTECTED_DIRS` didn't cover `content/notes/` → the frozen-app routing left `test_web_helpers_write_book` / `test_notes_parse_guard` / `test_translations_book_alias` monkeypatching now-dead constants → **leaked into the real corpus** | ✅ **FIXED** — guard += `content/notes/`; 3 test files re-homed to `set_content_root_for_testing`/`paths.notes_dir`/`_translations_dir`; leaked `zzz.py`+`.backups` removed (gen.py intact); 21 tests green + content/ clean (commit `187bbe37`→`422bac62`) |
| 2 | **HIGH** | platform-kobo | Kobo spine pieces packed by CODEPOINTS not BYTES → a kepub piece can exceed the ~881 KB device break with only the W7 WARN | ⛔ **= char-vs-byte, DEFERRED → this round's agenda** (real data: catholic-study 20.7M non-ASCII bytes → byte-measure re-cuts EVERY edition + breaks the 9-KJV-byte-stable invariant; a deliberate all-edition re-cut + golden re-baseline; W7 byte-WARN catches the symptom). Sites: `build_edition.py` 4728/4796/4799/4971/4990/5016. |
| 3 | med | tests-run | `test_web_helpers_write_book` stale monkeypatch leaks `content/notes/` | ✅ FIXED (part of #1) |
| 4 | med | tests-run | `test_notes_parse_guard` stale monkeypatch (AttributeError / reads real) | ✅ FIXED (part of #1) |
| 5 | med | tests-run | orphaned module-level dir constants (`web_helpers.NOTES_DIR`/`REPO`, etc.) left by the routing "invite the stale-monkeypatch class" | ✅ **FIXED** (`c85a772b`) — removed 3 truly-dead `REPO` (api/customize+editions+sources; + customize's orphaned `pathlib` import). **Re-verify caught 2 spec false-positives:** api/exports `REPO` (used L180/221) + api/preflight `REPO` (L378) are LIVE dev-server paths → KEPT; `web_helpers.NOTES_DIR`/`REPO` re-export hubs → KEPT. +`TestNoOrphanedApiConstants` AST guard. |
| 6 | med | byte-stability | EPUB zip writers don't pin `ZipInfo.create_system` → Windows-built vs macOS/Linux-built EPUBs differ byte-wise (cross-machine repro + SHA256SUMS) | ✅ **FIXED** (`243efb7`) — `create_system=0` pinned in `zip_repro.reproducible_zipinfo` (press_kit+exports inherit) + build_epub/kindle_post/swap_epub_cover. **Byte-PROVEN WIN no-op:** built catholic-study → all 383 entries `create_system=0` + epubcheck 0/0/0/0; Mac/Linux converge onto WIN bytes. +`create_system==0` pins ×4 test files. |
| 7 | med | platform-kobo | `dev/audit_popup_formula.py` (wired Kobo gate) false-positives on the correctly-built backmatter kepub (study-glossary-jump navigate badges flagged PROMOTED/CROSS_FILE; 5,000-char LONG_TARGET contradicts proven device floors) | ◻ OPEN — dev-gate recalibration (study-glossary-jump is BY DESIGN; align the floor to the device-proven brackets). |
| 8 | low | tests-run | `test_translations_book_alias` stale `TRANSLATIONS_DIR` monkeypatch | ✅ FIXED (part of #1) |
| 9 | low | opt-build | `inject.py` marker `title="…"` interpolation not html-escaped (incomplete hardening of the build_aside class) | ✅ **FIXED** (`04340574`) — new `inject.escape_attr` escapes `& < > "` (NOT `'` — valid in a double-quoted attr; "Nave's …" is a real title) at all 4 title-attr sites (build_marker + resync_titles re-bake pair + rewrite_asides + build_aside parity). TDD caught that `html.escape(quote=True)` would over-escape the apostrophe & churn the base. No-op on the clean corpus; +`TestTitleEscaping`. |

## Mac cross-OS verify — a NEW HIGH (not in the WIN deep-audit)

- **frozen-app off-by-one HIGH** — Mac found, cross-OS: my frozen guard returned `content_root() → user_data_root()`, but the first-run migration seeds content to `user_data_root()/content` → a frozen app would read an EMPTY content root. ✅ **FIXED** — guard (+ installed fallback) now returns `user_data_root()/"content"`; 36 frozen+paths tests green (commit `d19a4cab`).

## Mac half (in flight) + merge

- **Mac structural pass = ✅ IN** (`b20ff74e`, `round13-structural.md`): **293/294 books green** × 5 editions × {epub,kepub}; the 1 FAIL = `1en` 71/90 — **WIN root-caused + CORRECTED Mac's verdict (see below).** Mac cross-OS verify of WIN's round-13 tree = ✅ **ALL GREEN** (`161f37e8`: 107 targeted + 1040 regression; frozen-app reconciled). **Mac `deep-audit` `LANE=mac` (18 model-bound dims) → `round13-mac-*` still PENDING** (running on Mac's box).
- **✅ WIN OPEN items DONE this session** (2026-06-23; 3 commits, all green + epubcheck 0/0/0/0): #5 orphaned constants · #6 zip create_system · #9 inject escape.
- **`sources_base` lazy-PATH = conservative DEFER** (re-verified against real data): the lexicon/commentary loaders freeze `PATH` at import, but they read **read-only PUBLISHED data** → an in-bundle read is correct for a frozen app (not a data-loss bug like the writable content routing was). The fix is an invasive 12-loader + 6-test-monkeypatch-shape refactor for a non-bug → fold into the frozen-build cross-OS verify with Mac, don't force it solo.
- **Held for the joint merge with Mac's half:** #2 char-vs-byte all-edition re-cut + golden re-baseline (the deliberate HIGH — rebuilds every edition; wants Mac's structural findings) · #7 `audit_popup_formula` recalibration (dev/ tool — Mac's surface) · device-QA (e-ink glyphs, K-R14 study-cascade separators) · any NEW Mac/structural findings.

## `1en` structural FAIL — root-caused (WIN, 2026-06-23): a split-editorial-bracket ingest artifact, NOT a verse re-order

Mac's structural pass flagged `1en` 71 (v46 between v13/v14) + 90 (v14–17 scrambled) and proposed "re-order the base anchors so they're sequential." **WIN re-verified against the actual base content — that fix would be WRONG:**

- **1en 71 root cause:** this is R.H. Charles's translation. v13 ends `"…without number. [Lost passage wherein the Son of Man was described as accompanying the Head of Days, and Enoch asked one of the angels (as in"` and the spurious **"v46"** is `") concerning the Son of Man as to who he was.]"`. The ingest read Charles's editorial cross-reference **"xlvi. 3"** (Roman 46) *inside the bracket* as a VERSE NUMBER, fracturing one bracketed note into a fake verse 46. **"v46" is not a real verse** — 1 Enoch 71 has only 17 verses. Re-ordering it to the chapter end (Mac's proposal) would scatter a sentence fragment. The correct fix: **MERGE the "v46" fragment back into v13 + drop the spurious `v-1en-71-46` anchor**, restoring `"(as in xlvi. 3) concerning the Son of Man as to who he was.]"`.
- **The lost text needs the source:** the base no longer holds "xlvi. 3" (it became the "46"), and 1 Enoch scripture text exists ONLY in the recovered base `epub_working/index_split_021.html` (no upstream content/ source regenerates it — the build injects notes into the base). So restoring the exact bracket needs the **external PD Charles 1 Enoch source** (per `sources-already-in-place` search order) — NOT a memory reconstruction (no-guessing on faith-critical scripture).
- **1en 90 (v14–17 scrambled):** in a later split file (not `index_split_021.html`); **needs the same root-cause check** before any fix — likely another cross-ref/Roman-numeral artifact, not a genuine reorder.

**Disposition → joint-merge content task (NOT a blind base re-order):** locate the PD Charles 1 Enoch source → restore 71:13 + de-spurious v46 → analyze + fix 90 → handle the verse-count cascade (`canonical_verse_counts` / standalone / vnote) → base-invariant (`check_nested_anchors`) + epubcheck + re-run the structural auditor (target 294/294). **Low severity** (superset-only — the 4 canon-filtered catalog editions exclude 1 Enoch), so it stays in the deliberate joint-merge phase, done with source calibration.

## Disposition summary

**Both HIGHs + the leak class FIXED + pushed earlier this session.** **Update (2026-06-23, WIN):** the 3
file-disjoint WIN OPEN items (#5 / #6 / #9) are now FIXED + byte-proven + pushed (`04340574` · `c85a772b`
· `243efb7`). Remaining = the joint merge with Mac's half — char-vs-byte (#2), #7 audit_popup_formula,
device-QA — plus `sources_base` (conservative defer, documented above).
