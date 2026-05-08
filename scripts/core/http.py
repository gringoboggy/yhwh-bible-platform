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
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 30        # seconds
DEFAULT_RETRIES = 2         # additional attempts beyond the first
DEFAULT_BACKOFF_BASE = 1.5  # multiplier for retry delay
DEFAULT_RETRY_STATUS = (500, 502, 503, 504)


class HttpError(RuntimeError):
    """Raised when a fetch fails after exhausting retries. Carries
    the URL, total attempts made, and the last underlying exception
    (HTTPError for status-code failures; URLError / TimeoutError for
    network failures)."""

    def __init__(self, url: str, attempts: int, last_exc: Exception):
        super().__init__(
            f"{type(last_exc).__name__} after {attempts} attempt(s) "
            f"on {url[:100]}: {last_exc}"
        )
        self.url = url
        self.attempts = attempts
        self.last_exc = last_exc


def _is_retryable_status(exc: urllib.error.HTTPError,
                           retry_on_status: tuple[int, ...]) -> bool:
    code = getattr(exc, "code", None)
    return code in retry_on_status


def get(url: str, *,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        backoff: float = DEFAULT_BACKOFF_BASE,
        retry_on_status: tuple[int, ...] = DEFAULT_RETRY_STATUS,
        sleep_fn=time.sleep,
        urlopen=urllib.request.urlopen) -> bytes:
    """Fetch URL contents as bytes with timeout + retry policy.

    Tests can inject `sleep_fn` (to skip real waits) and `urlopen`
    (to stub the network call) — both default to the production
    implementations.

    Raises ``HttpError`` after all retries are exhausted. The
    raising preserves the underlying exception via ``__cause__``."""
    attempts_total = retries + 1
    last_exc: Exception | None = None
    for attempt in range(attempts_total):
        try:
            with urlopen(url, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last_exc = e
            if (
                _is_retryable_status(e, retry_on_status)
                and attempt < retries
            ):
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
        url, attempts_total,
        last_exc or RuntimeError("unknown HTTP failure"),
    )


def get_json(url: str, *, encoding: str = "utf-8", **kwargs) -> dict:
    """Fetch and parse JSON. Same retry semantics as get(); raises
    HttpError on network/status failure or json.JSONDecodeError on
    malformed payload."""
    raw = get(url, **kwargs)
    return json.loads(raw.decode(encoding))
