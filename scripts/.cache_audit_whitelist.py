"""ω.30 — `@lru_cache` whitelist: caches that legitimately don't
need an explicit `cache_clear()` call.

Two categories qualify:

  1. **Signature-keyed caches** (`_cached_*` in scripts/web.py) —
     the cache key includes a "signature" (a tuple of file paths +
     mtimes via `_files_signature(...)`). When files change, the
     signature changes, the lookup misses, the underlying function
     re-runs. No manual invalidation needed — the cache key carries
     the freshness signal.

  2. **Read-once singletons** (PD source data, env-dependent
     resolvers) — values that don't change during a single process's
     lifetime. The cache is the value; clearing it would just force
     a re-read with no behavioral change.

Adding to this list is a deliberate "this cache is correct without
a clear path" decision, similar to ω.26's vulture whitelist. Each
entry below has a documented rationale.

Run::

    python scripts/audit_caches.py
"""

# ---- Signature-keyed caches in scripts/web.py ----
# Cache key includes `_files_signature(...)` results; when files
# change, the key changes, the cache misses. Documented in the
# `_cached_*` block at scripts/web.py:80-100.
_._cached_attribution_audit
_._cached_edition_diff
_._cached_publisher_data
_._cached_covers
_._cached_preflight

# ---- Read-once singletons in scripts/core/sources.py (post-split: sources_lexicon.py) ----
# Lazy-loaded PD source data; values don't change during a single
# process. Reloading from disk on demand would just be wasted I/O.
_.strongs_hebrew
_.tsk
_.torrey_topical  # Torrey's New Topical Textbook (1897 PD); read-once singleton like the above (Track C ingest)
_._topic_vocab  # scripts/build_edition.py — Nave's+Torrey topic-name vocab from the same immutable PD JSONs; updates ship via git commit + restart (§7.1)

# ---- Env-dependent singleton in scripts/core/sources.py ----
# Anthropic API client built from ANTHROPIC_API_KEY env var.
# Cleared by restarting the process, not by cache_clear().
_._anthropic_client

# ---- Read-once singletons over immutable manuscript / canonical data ----
# §7.1 "project-internal published data" tier: the underlying files are
# immutable within a process (KJV spine, folio image masters, calibration
# witnesses), so the cache IS the value — clearing it would only force a
# wasted re-read with no behavioral change. Each function's docstring
# documents this rationale.
_.load_kjv_skeleton  # scripts/core/manuscript_collation.py — KJV spine rows
_._book_shape_cached  # scripts/core/canonical_verse_counts.py — shape derived from the KJV spine
_.load_image  # scripts/core/manuscript_vision.py — immutable folio image masters
_._collate_case  # scripts/manuscript_qa.py — immutable calibration witnesses + collation

# ---- Read-once singleton in scripts/core/versification.py ----
# `_psalm_map()` builds the static LXX/Vulgate↔KJV psalm-renumbering
# table once from constants (no inputs). The cache IS the value —
# clearing it would only force a wasted, identical rebuild.
_._psalm_map  # scripts/core/versification.py — static psalm-renumber table
_._web_anchors  # scripts/_fix_chapter_verse_boundaries.py — round-7 WEB ground-truth fixture (content/sources/web_boundary_anchors.json, committed + immutable in-process; the fixer re-runs per invocation, updates ship via git commit)

# ---- Pure-function compiled-regex caches ----
# Compiled-regex builders keyed only on their argument (e.g. a book-id
# prefix) — pure functions of the key, no external/runtime state. The
# cache IS the compiled pattern; clearing it would only force an
# identical recompile. No write path can invalidate them.
_._aside_existing_re  # scripts/inject.py — per-prefix existing-aside-id pattern (mint-8 hot-regex hoist; lru_cache(256))
