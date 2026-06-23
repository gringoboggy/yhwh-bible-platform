"""ω.20-A — Build cache (content-addressable hash key).

The build pipeline is expensive (30-90s per edition). When the user
edits a single edition's record, only that edition needs rebuilding;
the others are byte-identical. ω.20 caches built EPUBs keyed on a
hash of every input that would affect the output — same inputs →
same key → cache hit → skip the rebuild and serve the prior artifact.

Public API (all pure functions; no module-level state besides the
default cache directory path):

    compute_cache_key(edition_id, *, version="v28a") -> str
        SHA-256 hex digest. Stable across runs for unchanged inputs.
        Raises ValueError if the edition is unknown.

    cache_lookup(key, *, cache_dir=None) -> Optional[Path]
        Path to the cached EPUB for `key`, or None.

    cache_store(key, src_path, *, cache_dir=None) -> Path
        Copy the file at `src_path` into the cache as `<key>.epub`.
        Atomic via notes_io.atomic_write_bytes. Returns the cache path.

    cache_clear(*, cache_dir=None) -> int
        Remove every `*.epub` from the cache directory. Returns the
        count removed.

    cache_dir_default() -> Path
        The on-disk cache root: `<repo>/exports/.cache/`.

The cache is content-addressable: per-edition clearing is unnecessary
because changing any input that affects an edition's output produces
a different key, leaving the old entry orphaned (collected by
cache_clear() when the user wants the disk space back).

Per CLAUDE_PROJECT_RULES §10 ("Standard library only on the backend"):
hashlib + json + os only. No external deps.

ω.20-B will wire the lookup/store calls into `build_one()` in
scripts/build_edition.py — additive integration that preserves the
no-cache code path when the cache is empty.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent.parent
_CONTENT = _REPO / "content"

# Build-pipeline source scripts whose code affects EPUB output bytes (mint-9 #1).
# build_one() orchestrates all of these; an edit to any must invalidate the
# content-addressable cache. Verified call edges (build_edition.py): module-level
# imports of epub_utils + matter_pages; call-time imports of style_config (:2264),
# resync_marker_glyphs (:2852), build_epub (:3023). resync_marker_glyphs in turn
# imports glyph helpers from inject.py, so inject's build-time logic is included.
# Explicit list, NOT a glob — a scripts/**/*.py glob would bust the cache on
# unrelated test/migration edits. apply_style is intentionally absent: it is only
# referenced in comments, never called in the build path (confirmed mint-9).
_PIPELINE_SCRIPTS = (
    "build_edition.py",
    "matter_pages.py",
    "epub_utils.py",
    "resync_marker_glyphs.py",
    "build_epub.py",
    "style_config.py",
    "inject.py",
    # mint-10 #2 — core/ modules whose DATA the build injects (not just code):
    # popup_versions drives POPUP_LANGUAGES + per-edition language stripping
    # across all 9 popup editions; traditions supplies CANONICAL_TRADITIONS
    # labels injected for catholic-study. Editing either used to serve a stale
    # cached EPUB. Paths are relative to scripts/ (the loop joins scripts/<name>).
    "core/popup_versions.py",
    "core/traditions.py",
    # mint-11 #22 — source_dates.lookup_year CODE (the source_dates.yaml DATA is
    # hashed separately at part 9b); a lookup_year algorithm change affects
    # time-filtered editions' output, so it must invalidate the cache too.
    "core/source_dates.py",
    # round-5 audit (2026-06-05) — close the WHOLE "build-path core module"
    # class. edition_stats was the flagged HIGH instance: matter_pages bakes
    # resolved_note_counts() into copyright/legend/your-edition pages, so editing
    # edition_stats.py served a STALE EPUB. Per "fix the class, not the instance",
    # the full audit of scripts.core imports made by the build_one orchestrators
    # (build_edition/matter_pages/epub_utils/resync_marker_glyphs/build_epub/
    # style_config/inject) added every sibling whose CODE shapes content BAKED
    # into the EPUB and is NOT already covered by a data hash. (The drift guard
    # is tests/test_build_cache.py::TestCacheCoverageGuard.) Each, with its bake
    # site:
    #   edition_stats      resolved_note_counts → copyright.xhtml / legend /
    #                      your-edition page (matter_pages.py) — the round-5 HIGH.
    #   book_native_names  format_toc_book_label → bilingual nav ToC
    #                      (build_edition.apply_bilingual_toc).
    #   reading_plans      load_plan → reading_plans.xhtml (matter_pages.py).
    #   sources            NavesTopical/TorreyTopical → topical.xhtml back-matter
    #                      (the topical JSON DATA is hashed at 9c; the loader CODE
    #                      that structures it into the page is not).
    #   covers             decode_book_covers/resolve_cover_path select + apply
    #                      the cover in build_one (the image BYTES are hashed at
    #                      part 8; the selection/decode CODE is not — and this
    #                      module decodes book_covers itself, so a divergent
    #                      covers.py would slip a different cover past the key).
    #   matrix             compute_matrix().edition_canon_books → the per-edition
    #                      book count printed in the matter pages (matter_pages.py
    #                      _edition_canon_book_count).
    "core/edition_stats.py",
    "core/book_native_names.py",
    "core/reading_plans.py",
    "core/sources.py",
    "core/covers.py",
    "core/matrix.py",
    # round-5 adversarial-review follow-up — the build-path core class is
    # TRANSITIVE, not just the orchestrators' DIRECT imports. Two of the six
    # above are thin shims whose real output-shaping code lives one module
    # deeper, and two the first pass wrongly waived as "data-hashed" actually
    # run output-shaping CODE live in build_one. (The full transitive closure is
    # enforced by tests/test_build_cache.py::TestCacheCoverageGuard.)
    #   config           enabled_kind_codes / enabled_kind_codes_for decide which
    #                    kinds/notes are STRIPPED from the baked EPUB
    #                    (compute_edition_filter_sets → filter_html) — code, not
    #                    the kinds.yaml DATA that parts 1-5 hash.
    #   translations     get_verse swaps verse text into popup vnote-text asides
    #                    live in build_one (_apply_popup_languages_and_translation)
    #                    for any popup_translation edition, incl. the Geʽez/Amharic
    #                    EN back-translation popups — code, not the part-6 DATA.
    #   corpus_index     builds Matrix.edition_canon_books → the matter-page book
    #                    count (matrix.compute_matrix delegates here).
    #   sources_lexicon  defines NavesTopical/TorreyTopical → topical.xhtml
    #                    back-matter structuring (sources.py only re-exports them).
    "core/config.py",
    "core/translations.py",
    "core/corpus_index.py",
    "core/sources_lexicon.py",
    # turn 129 — cache guard closure gaps (TestCacheCoverageGuard):
    #   book_codes        canonical_book_code / BOOK_CODE_ALIASES → topical.xhtml
    #                     verse refs via sources_base (config → sources_base).
    #   vnote_separators  add_vnote_preview_separators → popup vnote HTML
    #                     (build_edition.py module-level import).
    "core/book_codes.py",
    "core/vnote_separators.py",
)


def cache_dir_default() -> Path:
    """The project's on-disk cache root: ``<repo>/exports/.cache/``."""
    return _REPO / "exports" / ".cache"


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> str:
    """SHA-256 hex digest of a file's bytes. Returns the literal
    string ``"<missing>"`` if the file doesn't exist, so callers
    don't need to pre-check — a missing input still contributes a
    distinct, stable token to the cache key."""
    if not path.is_file():
        return "<missing>"
    return _hash_bytes(path.read_bytes())


def _resolve_canon_books(edition: dict) -> list[str]:
    """Return the sorted list of book codes for the edition's canon."""
    canon_id = edition.get("canon")
    if not canon_id:
        return []
    canons_path = _CONTENT / "canons.yaml"
    if not canons_path.is_file():
        return []
    try:
        import yaml
    except ImportError:
        return []
    data = yaml.safe_load(canons_path.read_text(encoding="utf-8")) or {}
    canons = data.get("canons") or {}
    rec = canons.get(canon_id) or {}
    books = rec.get("books") or []
    return sorted(b for b in books if isinstance(b, str))


def _referenced_translations(edition: dict) -> list[str]:
    """Translation-data DIRECTORY ids the build pipeline will read for `edition`.

    Each popup language/version token is resolved in two hops so the
    directory hash covers the data actually read on disk:
      1. ``popup_versions.resolve_version_id`` (mint-10) maps a legacy
         language alias to its registry version id.
      2. ``VERSION_REGISTRY[vid]["translation_id"]`` (mint-11) maps that
         registry id to the actual ``content/translations/<dir>/`` id —
         e.g. the registry key ``lxx-greek`` reads ``lxx-swete-greek``.
    Without hop 2, four of the five default witnesses (lxx-greek,
    greek-nt, vulgate, arabic) hashed a non-existent
    ``content/translations/<key>/`` dir (the ``<missing>`` token), so a
    real translation-data edit could silently miss the cache. Unknown ids
    fall back to the raw token (still degrades gracefully to ``<missing>``).
    """
    from scripts.core import popup_versions as _pv

    def _resolved(token: str) -> str:
        # mint-11 P5: map the registry version id to its actual translation-data
        # DIRECTORY id. Popup tokens like "lxx-greek"/"greek-nt"/"vulgate"/
        # "arabic" are registry KEYS, but their data lives under translation_id
        # ("lxx-swete-greek"/"byzantine-greek"/"vulgate-clementine"/
        # "arabic-vandyke"). Without this final hop, 4 of the 5 default witnesses
        # resolved to a non-existent content/translations/<key>/ dir (the
        # "<missing>" hash token), so a real translation-data edit could silently
        # miss the content-cache key. Unknown ids degrade gracefully to the token.
        vid = _pv.resolve_version_id(token) or token
        return _pv.VERSION_REGISTRY.get(vid, {}).get("translation_id") or vid

    refs: set[str] = set()
    pt = (edition.get("popup_translation") or "").strip()
    if pt:
        refs.add(_resolved(pt))
    # popup_languages_default + popup_languages_per_book reference
    # language ids; the build pipeline maps them to translation data.
    langs = edition.get("popup_languages_default") or []
    if isinstance(langs, list):
        for lang in langs:
            if isinstance(lang, str) and lang.strip():
                refs.add(_resolved(lang.strip()))
    # per_book / per_chapter / per_verse all share the same flat-list
    # format: ["<key>=<lang1>,<lang2>", ...].  Walk all three fields
    # using the same inline parse so the translation-data hash covers
    # version ids introduced via any granularity of override (ρ.3 B-5b).
    for field in (
        "popup_languages_per_book",
        "popup_languages_per_chapter",
        "popup_languages_per_verse",
    ):
        per_field = edition.get(field) or []
        if not isinstance(per_field, list):
            continue
        for entry in per_field:
            if not isinstance(entry, str) or "=" not in entry:
                continue
            _, _, langs_csv = entry.partition("=")
            for lang in langs_csv.split(","):
                if lang.strip():
                    refs.add(_resolved(lang.strip()))
    return sorted(refs)


def compute_cache_key(
    edition_id: str,
    *,
    version: str = "v28a",
    target_reader: str | None = None,
) -> str:
    """SHA-256 digest covering every input that affects this edition's
    EPUB output. Stable: same inputs → same key.

    Inputs included (each contributes a labeled, sorted token):
      - the edition's record (JSON-serialized, sort_keys=True) with the
        RESOLVED reader target normalized in (see below)
      - the version string
      - the canon book list for this edition's canon
      - kinds.yaml / categories.yaml / books.yaml (whole-file hashes)
      - themes.yaml (when the edition opts into a theme)
      - every in-canon ``content/notes/<book>.py``
      - every referenced translation directory's _meta.yaml plus
        its in-canon book files
      - reading-plan files for ``enabled_reading_plans``
      - the cover image bytes (main + per-book) when paths are set
      - the source ``scripts/build_edition.py``
      - every file under ``epub_working/`` (the build's templated
        input)

    ``target_reader`` is the matrix-M1 build-time override (spec-review
    blocker #1 corollary): the --target-reader flag changes output bytes
    without touching editions.yaml, so the key MUST hash the effective
    target or an override build would collide with the stored-default
    build and a wrong-format artifact would be served from cache. The key
    hashes the RESOLVED target (the sufficient statistic — every
    per-format behavior flows through resolve_target_reader), so an
    override equal to the record's own resolution hits the same entry,
    and a stale unknown stored value keys identically to the
    "everywhere" it resolves to. NOTE: normalizing the resolved target
    into the record changed every pre-M1 key once (a one-time full cache
    invalidation = one conservative rebuild per edition).

    Raises ValueError if the edition isn't in editions.yaml, or if
    ``target_reader`` is not a known target.
    """
    from scripts.core import config

    eds = config.editions_by_id()
    if edition_id not in eds:
        raise ValueError(f"unknown edition {edition_id!r}; known: {sorted(eds)}")
    edition = eds[edition_id]

    # Fold + normalize the reader target through the ONE resolver
    # (call-time import; build_edition imports this module call-time too,
    # so there is no import cycle).
    from scripts.build_edition import TARGET_READERS, resolve_target_reader

    effective = dict(edition)
    if target_reader is not None:
        if target_reader not in TARGET_READERS:
            raise ValueError(f"target_reader override {target_reader!r} not in {TARGET_READERS}")
        effective["target_reader"] = target_reader
    effective["target_reader"] = resolve_target_reader(effective)
    edition = effective

    parts: list[tuple[str, str]] = []

    # 1. Edition record + version.
    parts.append(
        (
            "edition",
            json.dumps(edition, sort_keys=True, ensure_ascii=False, default=str),
        )
    )
    parts.append(("version", version))

    # 2. Canon book list (resolved from canons.yaml).
    canon_books = _resolve_canon_books(edition)
    parts.append(("canon_books", json.dumps(canon_books)))

    # 3. Global config files.
    for name in ("kinds.yaml", "categories.yaml", "books.yaml"):
        parts.append((f"config:{name}", _hash_file(_CONTENT / name)))

    # 4. themes.yaml + the ACTIVE theme's CSS file: build_edition.py reads
    # content/themes/<theme_id>.css LIVE into stylesheet.css, but it lives
    # outside epub_working/ so item 10 misses it — without this, editing a
    # theme's CSS serves a stale EPUB (mint-9 #7). build_edition resolves
    # edition.get("theme", "classic"), so even editions with NO explicit theme
    # build with classic.css; hash it UNCONDITIONALLY (resolving the same
    # "classic" default) — the old `if theme_id:` gate skipped every
    # default-theme edition, so a classic.css edit served them a stale build
    # (round-11 W3b).
    theme_id = edition.get("theme", "classic")  # mirror build_edition.py:7422 EXACTLY (absent-key default; not `or`)
    parts.append(("themes.yaml", _hash_file(_CONTENT / "themes.yaml")))
    parts.append(
        (
            f"theme_css:{theme_id}",
            _hash_file(_CONTENT / "themes" / f"{theme_id}.css"),
        )
    )

    # 5. Every in-canon notes file.
    for code in canon_books:
        parts.append(
            (
                f"note:{code}",
                _hash_file(_CONTENT / "notes" / f"{code}.py"),
            )
        )

    # 6. Referenced translations: _meta.yaml + per-book files.
    for tx_id in _referenced_translations(edition):
        tx_dir = _CONTENT / "translations" / tx_id
        parts.append(
            (
                f"tx:{tx_id}:meta",
                _hash_file(tx_dir / "_meta.yaml"),
            )
        )
        for code in canon_books:
            parts.append(
                (
                    f"tx:{tx_id}:{code}",
                    _hash_file(tx_dir / f"{code}.py"),
                )
            )

    # 7. Reading-plan files referenced by the edition.
    for plan_id in edition.get("enabled_reading_plans") or []:
        if not isinstance(plan_id, str):
            continue
        plan_path = _CONTENT / "reading_plans" / f"{plan_id}.yaml"
        parts.append((f"plan:{plan_id}", _hash_file(plan_path)))

    # 8. Cover image bytes when a path is set.
    cover = (edition.get("cover_image") or "").strip()
    if cover:
        parts.append(("cover", _hash_file(_CONTENT / cover)))
    # mint-11 HIGH: the real per-book-cover field is "book_covers"; a prior
    # nonexistent field name meant per-book cover bytes were never hashed →
    # a changed cover served a stale cached EPUB. The "code=path" entry format
    # matches what web_covers writes (see covers.decode_book_covers).
    for entry in edition.get("book_covers") or []:
        if not isinstance(entry, str) or "=" not in entry:
            continue
        book_code, _, path = entry.partition("=")
        path = path.strip()
        if path:
            parts.append(
                (
                    f"cover:{book_code.strip()}",
                    _hash_file(_CONTENT / path),
                )
            )

    # 9. The build pipeline source itself — code changes invalidate.
    # build_one orchestrates more than build_edition.py: it calls matter_pages,
    # epub_utils, resync_marker_glyphs, style_config (theme/font application) and
    # hands packaging to build_epub. An edit to ANY of these changes the output
    # bytes, so all must contribute to the key or a code-only edit serves a stale
    # cached EPUB (mint-9 #1). Explicit allow-list, NOT a scripts/**/*.py glob —
    # a glob would spuriously bust the cache on unrelated test/migration edits.
    for script_name in _PIPELINE_SCRIPTS:
        parts.append(
            (
                f"pipeline:{script_name}",
                _hash_file(_REPO / "scripts" / script_name),
            )
        )

    # 9b. source_dates.yaml — read by compute_time_filtered_html_ref_ids for any
    # edition with a time_filter_ceiling; not under epub_working/, so hash it
    # directly or a date edit serves a stale time-filtered EPUB (mint-9 #17).
    parts.append(("source_dates.yaml", _hash_file(_CONTENT / "source_dates.yaml")))

    # 9c. Topical-index JSONs (Nave's + Torrey) — the topical back-matter page
    # is built from these; they live under content/sources/, NOT epub_working/,
    # so re-running either extractor must bust the cache or a stale topical
    # back-matter ships (mint-10).
    parts.append(("naves_topical.json", _hash_file(_CONTENT / "sources" / "naves_topical.json")))
    parts.append(("torrey_topical.json", _hash_file(_CONTENT / "sources" / "torrey_topical.json")))

    # 10. Templated EPUB input (epub_working/).
    # Recurse the whole tree (META-INF/container.xml, OEBPS/, etc.) so
    # the content-addressable key reflects every packed member, not just
    # the top-level files. Reuse build_epub.should_skip so the cache-key
    # file set tracks exactly what the packager includes (skips .git/
    # __pycache__/ the legacy-metadata subtree, EXCLUDE_NAMES, and dotfile-prefixed
    # components) — including ``mimetype``, which is packed first but is
    # still a real input that affects the output. Labels use the POSIX
    # relative path so subdir files get distinct, stable tokens.
    epub_dir = _REPO / "epub_working"
    if epub_dir.is_dir():
        from scripts import build_epub

        for entry in sorted(epub_dir.rglob("*"), key=lambda p: p.as_posix()):
            if not entry.is_file():
                continue
            rel = entry.relative_to(epub_dir)
            if build_epub.should_skip(rel):
                continue
            parts.append(
                (
                    f"epub:{rel.as_posix()}",
                    _hash_file(entry),
                )
            )

    parts.sort(key=lambda kv: kv[0])
    h = hashlib.sha256()
    for label, value in parts:
        h.update(label.encode("utf-8"))
        h.update(b"\0")
        h.update(value.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def cache_lookup(
    key: str,
    *,
    cache_dir: Path | None = None,
) -> Path | None:
    """Path to the cached EPUB for ``key``, or None when no entry
    exists. Pure read; no side effects."""
    cdir = cache_dir or cache_dir_default()
    candidate = cdir / f"{key}.epub"
    return candidate if candidate.is_file() else None


def cache_store(
    key: str,
    src_path: Path,
    *,
    cache_dir: Path | None = None,
) -> Path:
    """Copy the file at ``src_path`` into the cache as ``<key>.epub``.
    Atomic via ``notes_io.atomic_write_bytes`` so concurrent readers
    never see a half-written cache entry. Returns the cache path."""
    from scripts.core import notes_io

    src = Path(src_path)
    if not src.is_file():
        raise FileNotFoundError(f"src_path is not a file: {src}")
    cdir = cache_dir or cache_dir_default()
    cdir.mkdir(parents=True, exist_ok=True)
    target = cdir / f"{key}.epub"
    notes_io.atomic_write_bytes(target, src.read_bytes())
    return target


def cache_clear(*, cache_dir: Path | None = None) -> int:
    """Remove every ``*.epub`` from the cache directory. Returns the
    count removed. Idempotent on a missing cache dir (returns 0)."""
    cdir = cache_dir or cache_dir_default()
    if not cdir.is_dir():
        return 0
    removed = 0
    for entry in cdir.glob("*.epub"):
        try:
            entry.unlink()
            removed += 1
        except OSError:
            pass
    return removed
