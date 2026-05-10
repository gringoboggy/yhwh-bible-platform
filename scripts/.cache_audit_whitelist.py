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

# ---- Read-once singletons in scripts/core/sources.py ----
# Lazy-loaded PD source data; values don't change during a single
# process. Reloading from disk on demand would just be wasted I/O.
_.strongs_hebrew
_.tsk

# ---- Env-dependent singleton in scripts/core/sources.py ----
# Anthropic API client built from ANTHROPIC_API_KEY env var.
# Cleared by restarting the process, not by cache_clear().
_._anthropic_client
