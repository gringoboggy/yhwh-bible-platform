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
| 5 | med | tests-run | orphaned module-level dir constants (`web_helpers.NOTES_DIR`/`REPO`, etc.) left by the routing "invite the stale-monkeypatch class" | ◻ OPEN — assess: remove the truly-unused ones, but `web_helpers.NOTES_DIR` is re-exported widely (`web.py`) → care needed; the conftest guard (#1) already backstops new leaks. |
| 6 | med | byte-stability | EPUB zip writers don't pin `ZipInfo.create_system` → Windows-built vs macOS/Linux-built EPUBs differ byte-wise (cross-machine repro + SHA256SUMS) | ◻ OPEN — pin `create_system=0` (Windows's current default → WIN byte-stable, Mac converges) in `zip_repro` + build_epub/kindle_post/swap_epub_cover; **byte-proof obligation** (build catholic-study, confirm WIN unchanged). |
| 7 | med | platform-kobo | `dev/audit_popup_formula.py` (wired Kobo gate) false-positives on the correctly-built backmatter kepub (study-glossary-jump navigate badges flagged PROMOTED/CROSS_FILE; 5,000-char LONG_TARGET contradicts proven device floors) | ◻ OPEN — dev-gate recalibration (study-glossary-jump is BY DESIGN; align the floor to the device-proven brackets). |
| 8 | low | tests-run | `test_translations_book_alias` stale `TRANSLATIONS_DIR` monkeypatch | ✅ FIXED (part of #1) |
| 9 | low | opt-build | `inject.py` marker `title="…"` interpolation not html-escaped (incomplete hardening of the build_aside class) | ◻ OPEN — escape it; **byte-proof** (no-op unless a title carries `<`/`&`/`"` — then it fixes broken/unsafe HTML). |

## Mac cross-OS verify — a NEW HIGH (not in the WIN deep-audit)

- **frozen-app off-by-one HIGH** — Mac found, cross-OS: my frozen guard returned `content_root() → user_data_root()`, but the first-run migration seeds content to `user_data_root()/content` → a frozen app would read an EMPTY content root. ✅ **FIXED** — guard (+ installed fallback) now returns `user_data_root()/"content"`; 36 frozen+paths tests green (commit `d19a4cab`).

## Mac half (in flight) + merge

- **Mac: `deep-audit` round-13 `LANE=mac`** (18 model-bound dims) + **the "down to verse, down to the word" structural+content pass** (`dev/audit_book_structure.py` across every edition×format×book; chase the `1en` misordering to a verdict) → `dev/audit/round13-mac-*` + `round13-structural.md`. See `LANE_HANDOFF.md`.
- **Merge → remediate the OPEN items together** (TDD + byte-proofs + commit-per-fix): #2 char-vs-byte (the big deliberate re-cut + golden re-baseline) · #5 orphaned constants · #6 zip create_system · #7 audit_popup_formula · #9 inject escape · `sources_base` lazy-PATH · device-QA (e-ink glyphs, K-R14 study-cascade separators) · any NEW Mac/structural findings.

## Disposition summary

**Both HIGHs + the leak class FIXED + pushed this session.** The OPEN items are MED/LOW (byte-proof-gated
or dev-tool/device-QA) + the deliberately-deferred char-vs-byte all-edition re-cut — the joint round-13
remediation phase, to run with Mac's half + structural findings.
