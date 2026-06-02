"""ξ.13 — append-only audit log for mutation endpoints.

Every mutation that touches `content/` (api_save_edition, api_save_kind,
api_apply_kind_to_all_editions, etc.) appends one NDJSON line to
``<user_data>/audit/<YYYY-MM>.ndjson`` recording who/what/when. For
solo / desktop use the audit log is a self-debugging tool ("what did
I just change, again?"); for retail / regulated deployments it's
also the compliance trail.

Design choices:

  - **NDJSON, not SQLite**: text format that survives Python
    upgrades, plays nice with grep + jq + tail -f, and never has
    schema migrations. Append cost is one fsync.
  - **Monthly rotation**: ``2026-05.ndjson`` rolls into
    ``2026-06.ndjson`` automatically. No size-based rotation
    surface; compliance retention is the operator's call (delete
    old monthly files when their retention window expires).
  - **Append-only**: never edit, never truncate. Ledger integrity
    means every line is immutable once written; corrections are
    new entries (`action: "correction", references: "..."`).
  - **Decorator pattern**: `@audit_endpoint(action="save_edition")`
    on api_save_*. Captures endpoint name, action label, args
    (sanitized), result `status`/`code`, and elapsed time. One
    line per route invocation.
  - **Best-effort**: a write failure on the audit log MUST NOT
    fail the underlying operation. The route returns its real
    result; the audit-log failure is logged via stdlib logging and
    swallowed.

Per CLAUDE_PROJECT_RULES §10 (stdlib only on the backend): pure
stdlib (`json` + `time` + `pathlib`). No external deps.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from collections.abc import Callable


_log = logging.getLogger(__name__)


# ξ.17 SEC-005 — sensitive kwarg names that get redacted in the
# audit log args summary. The intent is to catch the obvious cases
# (api_key, password, token, secret, Authorization, bearer) without
# trying to be exhaustive. Future endpoints that accept new sensitive
# fields should add to this set.
_REDACT_KEYS: frozenset[str] = frozenset(
    {
        "api_key",
        "apikey",
        "anthropic_api_key",
        "openai_api_key",
        "password",
        "passwd",
        "secret",
        "token",
        "bearer",
        "authorization",
        "auth",
        "session_id",
        "session_token",
        "cookie",
    }
)


# ξ.17 SEC-005 — boundary marker the chain-verifier uses to recognise
# pre-hash-chain lines. Lines written before this phase don't carry
# a `prev_hash` field; the verifier treats their hashes as the
# initial chain seed.
_CHAIN_GENESIS = "0" * 64


def _audit_dir() -> Path:
    """Resolve `<user_data>/audit/`. Created on first append."""
    from scripts.core import paths

    base = paths.user_data_root() / "audit"
    return base


def audit_log_path(
    *,
    when: datetime | None = None,
    base_dir: Path | None = None,
) -> Path:
    """Path to the current month's NDJSON file. Overridable via
    `base_dir` for tests; defaults to `_audit_dir()`."""
    when = when or datetime.now(timezone.utc)
    yyyy_mm = when.strftime("%Y-%m")
    base = base_dir if base_dir is not None else _audit_dir()
    return base / f"{yyyy_mm}.ndjson"


def _prior_month_file(path: Path) -> Path | None:
    """The most-recent existing ``YYYY-MM.ndjson`` sibling that sorts
    strictly before ``path``. Monthly filenames sort chronologically,
    so the lexicographically-greatest earlier name is the prior month
    (or any older file across a rotation gap). Returns ``None`` when no
    earlier file exists.
    """
    try:
        earlier = sorted(p for p in path.parent.glob("*.ndjson") if p.name < path.name)
    except OSError:
        return None
    return earlier[-1] if earlier else None


def _last_line_hash(path: Path) -> str:
    """ξ.17 SEC-005 — return the sha256 of the last line in `path`,
    or ``_CHAIN_GENESIS`` only when there is no prior history at all.

    When ``path`` does not exist yet — the first write of a new month —
    fall back to the most-recent PRIOR monthly sibling's last-line hash
    so the chain stays continuous across month rollovers. ``verify_chain``
    carries its expected hash *across* files, so the new month's first
    ``prev_hash`` must equal the previous month's last line, NOT the
    genesis seed (otherwise the chain reads "broken" every rollover).
    Only the very first audit line ever written (no file AND no prior
    sibling) seeds from ``_CHAIN_GENESIS``.

    Reads the file once and walks lines from the end so the cost is
    bounded by the size of the trailing line, not the whole file.
    """
    if not path.is_file():
        prior = _prior_month_file(path)
        if prior is None:
            return _CHAIN_GENESIS
        path = prior
    try:
        # The file is line-oriented and append-only; reading it whole
        # is bounded by the monthly rotation. For NDJSON at <1 KB per
        # line × 10K lines/month, that's ~10 MB worst case — fine.
        text = path.read_text(encoding="utf-8")
    except OSError:
        return _CHAIN_GENESIS
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return _CHAIN_GENESIS
    return hashlib.sha256(lines[-1].encode("utf-8")).hexdigest()


def append(
    *,
    endpoint: str,
    action: str = "",
    result: str = "ok",
    base_dir: Path | None = None,
    when: datetime | None = None,
    **fields: Any,
) -> Path | None:
    """Append one entry to the current month's audit log. Returns
    the file path on success, ``None`` on failure (with the
    underlying error logged).

    Standard fields: ``timestamp`` (ISO-8601 UTC), ``endpoint``,
    ``action``, ``result``. Additional kwargs flow into the entry
    as-is; non-JSON-serializable values fall back to ``str(value)``.

    ξ.17 SEC-005 — every entry carries a ``prev_hash`` field that is
    the sha256 of the previous line. Tampering with any line breaks
    the chain forward; ``verify_chain()`` surfaces the break to the
    /audit-log console. Lines written before ξ.17 don't have
    ``prev_hash``; the verifier treats those as the genesis seed.
    """
    when = when or datetime.now(timezone.utc)
    entry: dict[str, Any] = {
        "timestamp": when.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "endpoint": endpoint,
        "action": action,
        "result": result,
        **fields,
    }
    try:
        path = audit_log_path(when=when, base_dir=base_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Compute prev_hash from the chain tail BEFORE writing this
        # entry: this month's last line, or — on a new month's first
        # write — the prior month's last line (continuous chain).
        # Only the very first line ever seeds from genesis.
        entry["prev_hash"] = _last_line_hash(path)
        line = json.dumps(entry, ensure_ascii=False, default=str)
        # Append in text mode with a trailing newline.
        with path.open(
            "a", encoding="utf-8"
        ) as f:  # atomic-waived: append-only audit log; truncation would lose history
            f.write(line + "\n")
        return path
    except Exception as e:
        _log.warning("audit_log.append failed: %s", e)
        return None


def verify_chain(*, base_dir: Path | None = None) -> dict:
    """ξ.17 SEC-005 — walk every audit-log file (oldest first) and
    verify that each entry's ``prev_hash`` matches the sha256 of
    the previous line on disk.

    Returns ``{"status": "ok"|"broken"|"empty", "checked": N,
    "first_break": {file, line_number, expected, actual} | None,
    "ungated_lines": M}``. ``ungated_lines`` counts pre-ξ.17 lines
    that lack the ``prev_hash`` field — those are not failures
    (the chain genesis is documented as "pre-ξ.17 history") but
    they are reported so an operator can see how many lines
    pre-date the integrity story.
    """
    base = base_dir if base_dir is not None else _audit_dir()
    if not base.is_dir():
        return {"status": "empty", "checked": 0, "first_break": None, "ungated_lines": 0}
    monthly = sorted(base.glob("*.ndjson"))
    if not monthly:
        return {"status": "empty", "checked": 0, "first_break": None, "ungated_lines": 0}

    expected_hash = _CHAIN_GENESIS
    checked = 0
    ungated = 0
    for path in monthly:
        try:
            lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        except OSError:
            continue
        for line_num, line in enumerate(lines, start=1):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                # Malformed line breaks the chain.
                return {
                    "status": "broken",
                    "checked": checked,
                    "first_break": {
                        "file": path.name,
                        "line_number": line_num,
                        "reason": "malformed JSON",
                    },
                    "ungated_lines": ungated,
                }
            actual_prev = entry.get("prev_hash")
            if actual_prev is None:
                # Pre-ξ.17 line — count and re-seed.
                ungated += 1
            elif actual_prev != expected_hash:
                return {
                    "status": "broken",
                    "checked": checked,
                    "first_break": {
                        "file": path.name,
                        "line_number": line_num,
                        "expected": expected_hash,
                        "actual": actual_prev,
                    },
                    "ungated_lines": ungated,
                }
            expected_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
            checked += 1
    return {"status": "ok", "checked": checked, "first_break": None, "ungated_lines": ungated}


def read_recent(
    *,
    n: int = 50,
    base_dir: Path | None = None,
) -> list[dict]:
    """Return the most recent ``n`` audit-log entries across all
    monthly files (newest first). Skips malformed lines silently
    so a partial corruption doesn't break the whole read.

    Pure read; no side effects."""
    base = base_dir if base_dir is not None else _audit_dir()
    if not base.is_dir():
        return []
    # Newest month first.
    monthly = sorted(base.glob("*.ndjson"), reverse=True)
    out: list[dict] = []
    for path in monthly:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # Last-line-first: walk in reverse so the newest entries
        # in the most recent month win.
        for line in reversed(text.splitlines()):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(out) >= n:
                return out
    return out


def _summarize_args(args: tuple, kwargs: dict) -> dict:
    """Best-effort summary of call arguments for the audit log.
    Strips known-large fields (HTML bodies, dict payloads larger
    than 200 chars) so the log stays readable.

    ξ.17 SEC-005 — kwargs whose name matches the redaction allowlist
    (api_key, password, token, secret, Authorization, etc.) are
    masked as ``"[REDACTED]"`` before logging. Catches the obvious
    secret-leak class without trying to be exhaustive.
    """
    summary: dict[str, Any] = {}
    if args:
        # Positional args: capture types + short reprs only.
        summary["args"] = [_short_repr(a) for a in args]
    for k, v in kwargs.items():
        # ξ.17 redaction — case-insensitive match against the
        # sensitive-kwarg allowlist.
        if k.lower() in _REDACT_KEYS:
            summary[k] = "[REDACTED]"
        else:
            summary[k] = _short_repr(v)
    return summary


def _short_repr(value: Any, *, max_len: int = 200) -> Any:
    """Short representation for audit-log fields. Strings truncated;
    dicts/lists summarized by length; primitives passed through."""
    if isinstance(value, str):
        if len(value) <= max_len:
            return value
        return value[:max_len] + f"…[+{len(value) - max_len}]"
    if isinstance(value, dict):
        return {"<dict>": f"{len(value)} keys"}
    if isinstance(value, (list, tuple)):
        return {"<seq>": f"{len(value)} items"}
    if isinstance(value, (int, float, bool, type(None))):
        return value
    return str(value)[:max_len]


def audit_endpoint(action: str = "") -> Callable:
    """Decorator: wrap a mutation handler so each call appends a
    line to the audit log. The wrapped function's behavior is
    unchanged; only the side-effect of logging is added. Failures
    in the audit log itself are swallowed so the underlying op
    isn't disturbed.

    Usage::

        @audit_endpoint(action="save_edition")
        def api_save_edition(edition_id, payload):
            ...
    """

    def _decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            t0 = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
            except Exception:
                # Log the failure, then re-raise. Never swallow.
                append(
                    endpoint=fn.__name__,
                    action=action or fn.__name__,
                    result="raised",
                    elapsed_ms=round((time.perf_counter() - t0) * 1000, 2),
                    args=_summarize_args(args, kwargs),
                )
                raise
            # Capture status/code if the result is a dict (the
            # project's pure-function-thin-route-adapter convention).
            status = "ok"
            code = ""
            if isinstance(result, dict):
                # `{"status": "ok"}` and `{"error": "..."}`/`{"ok": True}`
                # are the conventions across the codebase.
                if result.get("status") == "error" or "error" in result:
                    status = "error"
                    code = result.get("code") or result.get("error") or ""
                elif result.get("status") == "ok" or result.get("ok") is True:
                    status = "ok"
            append(
                endpoint=fn.__name__,
                action=action or fn.__name__,
                result=status,
                code=code,
                elapsed_ms=round((time.perf_counter() - t0) * 1000, 2),
                args=_summarize_args(args, kwargs),
            )
            return result

        return _wrapper

    return _decorator
