"""
http.py — retry-and-timeout wrapper for outbound HTTP calls.

Phase ω.10 (2026-05-08). Every external HTTP fetch in the platform
(fetch_sources.py PD-source mirrors today; ρ.1 LibriVox audio + χ.2-5
commentary ingestors tomorrow) needs a defined timeout and a retry
policy. Today timeouts were inconsistent (30s in some places) and
there were zero retries, so a transient network blip would silently
fail the whole fetch.

This module is the single place to make outbound HTTP requests. The
linter check `check_external_http` (added alongside this module)
fails on any direct `urllib.request.urlopen` call outside this file.

Public API:
    HttpError                       — raised after retries exhausted
    get(url, **kwargs)              -> bytes
    get_json(url, **kwargs)         -> dict (json.loads of bytes)

Retry policy:
    - Retries on transient failures: URLError, TimeoutError, OSError,
      and HTTP 5xx responses (default: 500/502/503/504).
    - Does NOT retry on 4xx client errors (the caller's request was
      wrong; retrying won't help) or unexpected exceptions.
    - Exponential backoff: wait `backoff ** attempt` seconds between
      tries. Default backoff base 1.5 → 1.5s, 2.25s, ...
    - Total attempts = `retries + 1` (default 3 = first + 2 retries).

The module is self-contained and stdlib-only; importing it has no
side effects.
"""

from __future__ import annotations

import json
import time
import logging
import urllib.error
import urllib.parse
import urllib.request


# ξ.10 + ξ.10.1 — outbound URL allow-listing. Callers MUST pass
# `allowlist=` to pin which domains they expect to talk to. As of
# ξ.10.1 (2026-05-10) calls without an allowlist FAIL CLOSED:
# `SSRFBlockedError` is raised before any network I/O. Production
# call sites all migrated to one of the pre-built groups
# (`DEFAULT_PD_SOURCES_ALLOWLIST`, `DEFAULT_AI_BACKEND_ALLOWLIST`,
# `DEFAULT_DESKTOP_UPDATE_ALLOWLIST`).
_log = logging.getLogger(__name__)


class SSRFBlockedError(Exception):
    """Raised when a get() call's URL host is not in the supplied
    `allowlist`, OR when no `allowlist` is given at all (ξ.10.1
    fail-closed posture). Distinct from `HttpError` so callers can
    catch it specifically without conflating with network failures."""

    def __init__(self, url: str, host: str, allowlist):
        super().__init__(f"egress blocked: host {host!r} not in allowlist {sorted(allowlist)} (url={url[:120]})")
        self.url = url
        self.host = host
        self.allowlist = tuple(allowlist)


def _check_allowlist(url: str, allowlist) -> None:
    """Validate that `url`'s host is in `allowlist`. Allowlist may be
    a set / frozenset / tuple / list of host strings (lowercased,
    no scheme). Subdomain-aware: if the allowlist contains
    ``raw.githubusercontent.com``, requests to
    ``raw.githubusercontent.com/...`` and any subdomain like
    ``cdn.raw.githubusercontent.com`` are accepted; if it contains
    ``github.com``, ``api.github.com`` is also accepted.

    ξ.10.1 — `allowlist=None` raises `SSRFBlockedError` BEFORE any
    network I/O (was warn-and-continue in ξ.10). Every call site in
    `scripts/` was migrated to an explicit allowlist before this
    flip; if a future contributor adds a new caller they MUST pass
    one (production won't tolerate "I forgot").
    """
    if allowlist is None:
        # Fail-closed: no allowlist = no egress. Empty frozenset
        # surfaces in the error message so the caller knows what to
        # do (add `allowlist=DEFAULT_PD_SOURCES_ALLOWLIST` etc.).
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "<no-host>").lower()
        raise SSRFBlockedError(url, host, frozenset())
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        # No host (e.g. file: URLs, malformed) — let the underlying
        # urlopen raise its own error rather than swallow.
        return
    allow_set = {h.lower() for h in allowlist}
    if host in allow_set:
        return
    # Subdomain match: any of allowlist's entries is a suffix of host
    # (with a leading dot to avoid matching ``evil-github.com`` against
    # ``github.com``).
    for allowed in allow_set:
        if host.endswith("." + allowed):
            return
    raise SSRFBlockedError(url, host, allow_set)


DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_RETRIES = 2  # additional attempts beyond the first
DEFAULT_BACKOFF_BASE = 1.5  # multiplier for retry delay
DEFAULT_RETRY_STATUS = (500, 502, 503, 504)


class HttpError(RuntimeError):
    """Raised when a fetch fails after exhausting retries. Carries
    the URL, total attempts made, and the last underlying exception
    (HTTPError for status-code failures; URLError / TimeoutError for
    network failures)."""

    def __init__(self, url: str, attempts: int, last_exc: Exception):
        super().__init__(f"{type(last_exc).__name__} after {attempts} attempt(s) on {url[:100]}: {last_exc}")
        self.url = url
        self.attempts = attempts
        self.last_exc = last_exc


def _is_retryable_status(exc: urllib.error.HTTPError, retry_on_status: tuple[int, ...]) -> bool:
    code = getattr(exc, "code", None)
    return code in retry_on_status


def get(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF_BASE,
    retry_on_status: tuple[int, ...] = DEFAULT_RETRY_STATUS,
    allowlist=None,
    sleep_fn=time.sleep,
    urlopen=urllib.request.urlopen,
) -> bytes:
    """Fetch URL contents as bytes with timeout + retry policy.

    Tests can inject `sleep_fn` (to skip real waits) and `urlopen`
    (to stub the network call) — both default to the production
    implementations.

    ξ.10 — Pass ``allowlist`` (iterable of host strings) to pin
    which domains this call is authorised to reach. Calls without
    an allowlist log a warning and continue (back-compat); calls
    with a non-matching host raise ``SSRFBlockedError`` BEFORE
    any network I/O. Subdomain-aware: an allow-listed
    ``github.com`` accepts ``api.github.com`` etc.

    Raises ``HttpError`` after all retries are exhausted; raises
    ``SSRFBlockedError`` immediately if `allowlist` is set and
    the URL's host doesn't match. The raising preserves the
    underlying exception via ``__cause__``."""
    _check_allowlist(url, allowlist)
    attempts_total = retries + 1
    last_exc: Exception | None = None
    for attempt in range(attempts_total):
        try:
            with urlopen(url, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last_exc = e
            if _is_retryable_status(e, retry_on_status) and attempt < retries:
                sleep_fn(backoff ** (attempt + 1))
                continue
            # 4xx (always) or final attempt — surface as HttpError
            raise HttpError(url, attempt + 1, e) from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_exc = e
            if attempt < retries:
                sleep_fn(backoff ** (attempt + 1))
                continue
            raise HttpError(url, attempt + 1, e) from e

    # Defensive — the loop body always either returns or raises;
    # this branch is unreachable but kept for type-checkers.
    raise HttpError(
        url,
        attempts_total,
        last_exc or RuntimeError("unknown HTTP failure"),
    )


def get_json(url: str, *, encoding: str = "utf-8", **kwargs) -> dict:
    """Fetch and parse JSON. Same retry semantics as get(); raises
    HttpError on network/status failure or json.JSONDecodeError on
    malformed payload. Pass ``allowlist=...`` to opt into ξ.10's
    SSRF guard."""
    raw = get(url, **kwargs)
    return json.loads(raw.decode(encoding))


# ξ.10 — pre-built allow-list groups for common call sites.
# Cite from the call site so future audits can grep
# `from scripts.core.http import` and see which group each
# subsystem uses.
DEFAULT_PD_SOURCES_ALLOWLIST = frozenset(
    {
        "openscriptures.org",
        "ebible.org",
        "archive.org",
        "openbible.info",
        "raw.githubusercontent.com",
        "github.com",  # subdomain match catches api.github.com etc.
    }
)

DEFAULT_AI_BACKEND_ALLOWLIST = frozenset(
    {
        "api.anthropic.com",
    }
)

DEFAULT_DESKTOP_UPDATE_ALLOWLIST = frozenset(
    {
        "github.com",  # appcast hosted in releases
        "githubusercontent.com",
    }
)
