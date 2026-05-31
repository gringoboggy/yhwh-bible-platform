"""Distribution rollup API (mint-6) — thin adapter over scripts.core.distribution.

Re-surfaces the free-distribution status view that the deleted /exec console once
hosted, now on the /distribution console. Read-only; composes
``distribution.rollup()`` over the full edition list (RULES §9 — compose, don't
recompute). The archive.org upload + press-kit endpoints it pairs with already
live in ``scripts/api/archive_org.py`` and ``scripts/api/press_kit.py`` and stay
wired as-is; this module only adds the per-edition × per-channel rollup.
"""

from __future__ import annotations


def api_distribution_rollup() -> dict:
    """Return the per-edition × per-channel (archive.org / own-site) distribution
    rollup for every edition. Read-only, no side effects.

    Returns ``{status: "ok", channels, editions, by_channel_coverage, overall}``
    on success, or ``{status: "error", code, http, message}`` if the underlying
    state / edition load fails (RULES §9 dict-not-raise contract — the route
    adapter translates the error dict to an HTTP status)."""
    try:
        from scripts.core import config, distribution

        state = distribution.load_distribution()
        editions = config.load_editions()
        result = distribution.rollup(state, editions)
        result["status"] = "ok"
        return result
    except Exception as e:  # noqa: BLE001 — surface as a dict, never 500 the route
        return {
            "status": "error",
            "code": "internal_error",
            "http": 500,
            "message": str(e),
        }
