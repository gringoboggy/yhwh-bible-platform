# Round-11 — Frozen-app `content_root()` HIGH surface (findings-only)

**Mac lane · 2026-06-23 · for WIN remediation (the round-10/-11 only-other HIGH).**
Method: 1 enumeration agent (general-purpose, exhaustive grep + read) → Mac-lane
independent completeness-critic verify pass (corrections applied below). **Findings-only —
nothing modified.** WIN applies the whole class in one guarded pass.

## The bug (why this is HIGH)

In the **frozen desktop app**, `paths.content_root()` would resolve to the read-only
PyInstaller `_MEIPASS` bundle. Every runtime site that composes a content path directly
from a per-module repo anchor (`REPO` / `_REPO_ROOT` / `_CONTENT` / `NOTES_DIR` / … =
`Path(__file__).resolve().parent…/ "content"`) therefore points at the read-only bundle:
**WRITES are lost on exit (or blocked by macOS Gatekeeper); READS see the stale bundled
copy, not the user's saved edits.** The READ↔WRITE coupling is the trap: fixing a writer
alone is not enough — if the matching reader still reads `_MEIPASS`, saved edits stay
invisible (see `config.py:50` below).

## The fix (two parts — WIN)

1. **Add the frozen guard to `paths._content_root_cached()`** mirroring
   `paths._build_output_root()` (`scripts/core/paths.py:254-292`, which already does
   `if getattr(sys, "frozen", False): return user_data_root()`). Today `content_root()`
   has no such guard.
2. **Route every site below through the resolver** instead of the REPO anchor:
   - notes → `paths.notes_dir()`  · any content file → `paths.content_root() / …`
   - typed: `paths.translations_dir()` · `paths.covers_dir()` · `paths.sources_dir()` ·
     `paths.candidates_dir()`
   - YAML: `paths.editions_yaml()` · `paths.kinds_yaml()` · `paths.categories_yaml()` ·
     `paths.canons_yaml()` · `paths.books_yaml()` · `paths.themes_yaml()` ·
     `paths.traditions_yaml()`
   - no helper yet (`scenarios/`, `press_kit.json`, `themes/`, `distribution.json`) →
     `paths.content_root() / "<name>"`, or add a helper.

   **Fixing only `web_helpers` is NOT enough** — `web_helpers.py:25/29` `REPO`/`NOTES_DIR`
   is re-exported widely, but each `scripts/api/*.py` and several `scripts/core/*.py`
   define their OWN duplicate `REPO`/`_REPO_ROOT`/`_CONTENT`; each must be migrated.
   Verify with the frozen app: a note save must land in
   `user_data_root()/content/notes/<book>.py`.

## Counts

**~19 WRITE site-groups (the data-loss sites) · ~17 READ site-groups · 11 runtime files.**
(The enumeration agent's summary said "14 WRITE / 16 READ"; the per-line table below is
authoritative and slightly larger — some rows bundle sibling line numbers.) CLI/ingest/
build/lint tools that compose `REPO/content` but never load in the frozen app are listed
in §4 as out-of-scope boundary.

## 1. WRITE sites — data-loss in the frozen app (fix FIRST)

| file:line | exact current expression | note |
|---|---|---|
| `web_helpers.py:159` (`write_book`, `atomic_write`@196) | `path = NOTES_DIR / f"{book_code}.py"` (`NOTES_DIR = REPO/"content"/"notes"` @29) | ★ **Primary in-app note-save writer** — the core data-loss site. |
| `api/editions.py:360` (`ensure_backup`+`atomic_write` @388/389) | `editions_path = REPO/"content"/"editions.yaml"` (`REPO`@52) | Save edition meta. |
| `api/editions.py:540` (`atomic_write_bytes`@542) | `abs_new = REPO/"content"/rel_new` | Cover-copy on edition clone (main cover). |
| `api/editions.py:558` (`atomic_write_bytes`@560) | `abs_new = REPO/"content"/rel_new` | Cover-copy on edition clone (per-book cover). |
| `api/editions.py:572` (`ensure_backup`+`atomic_write`@583/584) | `yaml_path = REPO/"content"/"editions.yaml"` | Edition clone → editions.yaml. |
| `api/editions.py:1286` (@1296/1297) | `path = REPO/"content"/"editions.yaml"` | Reorder/delete-edition writer. |
| `api/editions.py:1348` (@1384/1385) | `path = REPO/"content"/"editions.yaml"` | editions.yaml mutator. |
| `api/editions.py:1571` (@1583/1584) | `path = REPO/"content"/"editions.yaml"` | editions.yaml mutator. |
| `web_covers.py:114` (`atomic_write_bytes`@124, `unlink`@144) | `abs_path = REPO/"content"/rel_path` (`REPO` from web_helpers @19) | Cover-byte upload persister. |
| `api/covers.py:106` (`atomic_write_bytes`@121) | `abs_path = REPO/"content"/rel_path` (local `REPO`@104) | Generate-and-save edition cover. |
| `api/covers.py:157` (`ensure_backup`@159, `unlink`@161) | `abs_path = REPO/"content"/cur_path` (local `REPO`@145) | Clear book cover. |
| `api/covers.py:226` (`ensure_backup`@228, `unlink`@230) | `abs_path = REPO/"content"/cur_path` (local `REPO`@210) | Reset book cover to default. |
| `api/sources.py:326` (`ensure_backup`+`atomic_write_bytes`@330/331) | `cache_path = _sources_cache_dir()/src.cache_path` (`_sources_cache_dir()=REPO/"content"/"sources"`@52) | Source-cache upload. |
| `api/sources.py:367` (@371, `unlink`@372) | `cache_path = _sources_cache_dir()/src.cache_path` | Clear cached source. |
| `api/customize.py:72` (`ensure_backup`+`atomic_write`@79/80) | `path = REPO/"content"/"categories.yaml"` (`REPO`@38) | Save categories. |
| `api/customize.py:115` (@122/123) | `path = REPO/"content"/"kinds.yaml"` | Save kinds. |
| `api/scenarios.py:32` (→`mkdir`@191/378, `atomic_write`@200/382, `ensure_backup`@199/381/415, `unlink`@416) | `SCENARIOS_DIR = REPO/"content"/"scenarios"` (`REPO`@31) | Save/rename/delete scenario YAMLs. |
| `web_content.py:689` (`api_restore_backup`, `atomic_write_bytes`) | writes `abs_path` from `_resolve_content_path` (anchors `REPO/"content"` @499/501) | Backup-restore writer (shared gate w/ the §3 READ). |
| `core/press_kit.py:104` (`_press_kit_path`, write @161/163) | `return _REPO_ROOT/"content"/"press_kit.json"` (`_REPO_ROOT`@98) | Reachable via `api/press_kit.py:api_press_kit_save → set_blurbs`. |

## 2. READ sites — must migrate too (else fixed writes are invisible)

| file:line | exact current expression | note |
|---|---|---|
| `core/config.py:50` (`_CONTENT = _REPO_ROOT/"content"`; used @275, 287, 291, 308, 315, 333, 340) | `(_CONTENT/"books.yaml"\|"kinds.yaml"\|"categories.yaml"\|"editions.yaml").read_text()` | ★ **The readers behind every edition/kind/category endpoint.** Accessor `_books_yaml_path()`@53 returns `paths.books_yaml()` but the cached loaders bypass it. Migrate or saved edits stay invisible. |
| `web_content.py:284` | `notes_path = REPO/"content"/"notes"/f"{book}.py"` | Sample/preview note load. |
| `web_content.py:499/501/564/623` | `(REPO/"content").resolve()`, `(REPO/"content"/rel_path).resolve()` | `_resolve_content_path` + `api_list_backups`; shared gate (also backs the WRITE @689). |
| `web_editions.py:224` | `notes_dir = REPO/"content"/"notes"` (`book_file`@225, load@229) | Per-edition note read. |
| `web_editions.py:585` (`_load_themes`, `path.read_text()`@589) | `path = REPO/"content"/"themes.yaml"` | **READ** (theme registry). *(Mac verify correction — the agent had tentatively marked it WRITE.)* No themes.yaml writer was found in-app. |
| `web_notes.py:40/73/153/184` | `path = NOTES_DIR / f"{…}.py"` | Note read endpoints (`NOTES_DIR` from web_helpers). |
| `web_sources.py:72/108/171/275` | `path = NOTES_DIR / f"{…}.py"` | Source/coverage note reads. |
| `web_sources.py:253-255/383`, `web_matrix.py:389-393`, `web_covers.py:79/80`, `api/preflight.py:52-55` | `_files_signature(REPO/"content"/…yaml)` (editions/kinds/categories/canons/books) | Cache-signature reads — migrate so the signature tracks the SAME file the resolver serves. |
| `web.py:1964` | `covers_root = REPO/"content"/"covers"` | Serves `/content/covers/<rel>`. |
| `core/translations.py:36` (`TRANSLATIONS_DIR`; used @64, 75, 176, 184, 187, 256) | `TRANSLATIONS_DIR / translation / …` | Bible-text store reader. Accessor `_translations_dir()`@47 returns `paths.translations_dir()` but module bypasses it. (Read-only content in-app; migrate for correctness if stores ever move to user-data.) |
| `core/covers.py:42` (`CONTENT`; used @352) | `p = CONTENT / p` | `read_image_meta` cover-path resolver. Accessor `_covers_dir()`@45 exists; @352 bypasses. |
| `core/preview.py:51/52` (used @70/78) | `THEMES_DIR/f"{theme}.css"`, `NOTES_DIR/f"{book}.py"` | Preview-render theme/note reads. |
| `core/sources_base.py:17/26` | `_SOURCES = _REPO_ROOT/"content"/"sources"` | *(Mac verify addition)* accessor `sources_dir()`@32 returns `paths.sources_dir()`, but `_SOURCES` is still used as a back-compat fallback — migrate the fallback. |
| `core/traditions.py:159` | `p = Path(path) if path else DEFAULT_TRADITIONS_YAML` (`= _REPO_ROOT/"content"/"traditions.yaml"`@31) | *(Mac verify addition)* the load default is REPO-anchored; callers passing `paths.traditions_yaml()` are fine, but the default fallback bypasses — migrate the default. |

## 3. Already correct — route through the resolver (EXCLUDE)

`paths.py` itself (incl. `_build_output_root()` frozen guard = the reference pattern) ·
`api/exports.py:34` (`paths.exports_dir()`) · `core/snapshots.py` (`paths.content_root()`,
`paths.notes_dir()`) · `core/onboarding.py:25` (`paths.state_dir()`) · `core/event_log.py:54`,
`core/audit_log.py:88` (`paths.user_data_root()`) · `core/corpus_index.py:134/148`
(`paths.user_data_root()/"cache"`, `paths.notes_dir()`) · `core/reading_plans.py:59`
(`paths.content_root()/"reading_plans"`) · `core/verse_of_day.py:118/179` (`paths.notes_dir()`) ·
`launcher.py:92` (`paths.user_data_root()/"content"`).

**Dead-in-app (LOW — hygiene only):** `core/distribution.py` (`_REPO_ROOT/content/distribution.json`
writer) has **no live web/api caller** — `web.py:519` imports only `api_distribution_rollup`
(READ); the writer is reached only by the `archive_org` CLI. `web.py:65 SCENARIOS_DIR` is a
**dead constant** (1 ref = the def; the live one is `api/scenarios.py:32`) → delete, don't migrate.

## 4. Boundary — CLI/build/lint only (NOT loaded in the frozen app; migrate later, low priority)

`glossary.py:44` · `find_anchor.py:42` · `sync_html_kinds.py:51` · `bulk_edit.py:46` ·
`note_search.py:51` · `retag.py:61` · `promote.py:53` · `inject.py:63` ·
`fix_xref_targets.py:57` · `validate_taxonomy.py:143` · `audit_base_html.py:57/80` ·
`prune_orphan_base_notes.py:80` · `promote_divergence_to_apparatus.py:49/50` ·
`generate_edition_covers.py:49` · `fetch_sources.py:58` · `run_*_at_scale.py` ·
`extract_*` scripts · `build_standalone.py:21` · `customize.py:55-57` (CLI) · `refactor.py:57` ·
`core/standalone_store.py:19/83-87/163-166` (build-time corpus writer) · `core/manuscript_*` ·
`core/build_cache.py:51` · `core/source_dates.py:37` · `core/fetcher_config.py:47` ·
`lint_rules.py` (lint anchors).

## 5. Completeness note + Mac verify pass

**Confidence: high** for the runtime web/api/core layer. Enumeration greps:
`rg 'REPO\s*/\s*"content"|REPO_ROOT|/ "content"|/ '"'"'content'"'"'|NOTES_DIR|CONTENT_DIR|content_dir|Path(__file__)'`
+ a WRITE-primitive sweep (`atomic_write|ensure_backup|\.write_text|\.write_bytes|open\(...w|notes_io\.|shutil\.(copy|move)|\.unlink`)
across `scripts/web*.py scripts/api/*.py scripts/core/*.py`, every WRITE site read directly.

**Beyond the round-10 approximate list** (which under-counted): `config.py:50 _CONTENT`
(the editions/kinds/categories/books READERS — critical coupling); `press_kit.py:104`
(WRITE via `api_press_kit_save`); `translations.py`, `covers.py:352`, `preview.py:51/52`
bypassing-constant READs; `api/editions.py` has **6** editions.yaml writes + 2 cover-copy
writes (not just "note-save"); `web_content.py` shared gate = **4** anchor lines backing
both list (READ) and restore (WRITE @689).

**Mac independent verify pass — corrections to the agent output (verified against HEAD):**
1. `web_editions.py:585` is a **READ** (`_load_themes` → `read_text`), not a WRITE — moved to §2.
2. `sources_base.py:17/26` + `traditions.py:159` use the REPO-anchored constant as a
   **fallback** despite having `paths.*()` accessors → added to §2 (were in the agent's
   "already correct" list).
3. Confirmed (spot-read at HEAD): `web_helpers.py:159` primary note-save writer;
   `config.py:50 _CONTENT` reader coupling; `distribution.py` writer has no live caller;
   `web.py:65 SCENARIOS_DIR` is dead (delete).

**Blind spots (WIN double-check):** dynamic/`os.path.join`-built paths could evade the
`/ "content"` grep (the notes/editions/covers/sources/scenarios/customize/press_kit
surfaces are all covered; a NEW endpoint added after this sweep is the realistic gap).
