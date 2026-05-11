#!/usr/bin/env python3
"""
check_routes.py — discover and audit the HTTP route surface of
``scripts/web.py``.

Phase ω.35-A (2026-05-11) — first response to AUDIT_2026-05-11
ARCH-01 ("scripts/web.py is now 7,461 lines"). The audit's
deeper recommendation was a `ROUTES = [(method, regex,
handler), ...]` table that would replace the hand-maintained
if/elif cascade in ``do_GET`` / ``do_POST`` / ``do_PUT`` /
``do_DELETE``. That dispatch refactor is **deferred to a
future ω.35-A.1**: rewriting ~1000 lines of cascade in one
session is high-risk against the 1973-test green state.

This phase ships the **observability foundation** for that
refactor: a CLI + Tier-3 preflight check that auto-discovers
every route by scanning ``do_GET`` / ``do_POST`` / ``do_PUT`` /
``do_DELETE`` for the two patterns the codebase uses
(``if path == "..."`` and ``m = re.match(r"^...")``), surfaces
the route count + method distribution, and flags two drift
classes a future operator could miss without it:

  - **Duplicate patterns** within a method (one path matches
    twice; the second branch is dead). Today the cascade order
    matters; the linter pin makes drift loud.
  - **Total route count** — a single number to track over
    time. The audit's #1 concern was the file growing; this
    surfaces growth in route count too.

The discovery is regex-based, not AST. A future enhancement
could ast.walk the Handler class for stricter parsing.

Run::

    python scripts/check_routes.py
    python scripts/check_routes.py --json

Returns ``{"checks": [...], "summary": {...}}`` matching the
project's standard preflight-aggregator shape (see §9
"Add a meta-tool that integrates with the preflight dashboard"
in CLAUDE_PROJECT_RULES.md).

Exit codes:
    0  clean
    1  any sub-check failed
    2  setup error (web.py missing)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_PY = REPO_ROOT / "scripts" / "web.py"


# ----------------------------------------------------------------------
# Data shape
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class Route:
    """One discovered route. ``pattern`` is the raw textual pattern as
    it appears in source — either a literal path (``"/api/foo"``) or a
    regex anchor (``"^/api/foo/([a-z0-9]+)$"``)."""

    method: str
    pattern: str
    is_regex: bool
    line: int


# ----------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------


# Match `if path == "/foo"` (single-route exact) and
# `if path == "/foo" or path == "/foo.html"` (two-route or-form).
_LITERAL_RE = re.compile(r'\s*if path == "(/[^"]*)"(?:\s+or\s+path\s*==\s*"(/[^"]*)")?\s*:')

# Match `m = re.match(r"^/foo/([a-z]+)$", path)` (or ..., self.path).
_REGEX_RE = re.compile(r'\s*m\s*=\s*re\.match\(\s*r"\^([^"]+)",\s*(?:path|self\.path)\s*\)')

# ω.35-A.1 — also discover `_SIMPLE_GET_ROUTES` table entries.
# Each line of the form `("/api/foo", handler_name),` registers a
# table-dispatched GET route. The discovery still considers these
# as GET (the table is GET-specific by design).
_TABLE_ENTRY_RE = re.compile(r'\s*\(\s*"(/[^"]+)"\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*\)\s*,?\s*$')

# ω.35-A.2 — also discover `_REGEX_GET_ROUTES` table entries.
# Each line of the form `(re.compile(r"^/api/foo/([a-z]+)$"), handler),`
# registers a regex-dispatched GET route. The regex pattern (without
# its leading `^`) is what gets recorded so the output matches the
# regex routes discovered from the legacy if/elif (which also strip
# the leading `^` via the `_REGEX_RE` capture group).
_REGEX_TABLE_ENTRY_RE = re.compile(
    r'\s*\(\s*re\.compile\(\s*r"\^([^"]+)"\s*\)\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*\)\s*,?\s*$'
)


def _method_for_line(text: str, line_no: int) -> str | None:
    """Walk backward from ``line_no`` to find the enclosing
    ``def do_<METHOD>`` definition. Returns the HTTP method name
    (e.g. ``"GET"``) or ``None`` if the route isn't inside a method.
    """
    lines = text.splitlines()
    for i in range(line_no - 1, -1, -1):
        m = re.match(r"\s*def\s+do_([A-Z]+)\(", lines[i])
        if m:
            return m.group(1)
    return None


def discover_routes(*, web_py_path: Path | None = None) -> list[Route]:
    """Scan ``scripts/web.py`` and return every route discovered in
    ``do_GET`` / ``do_POST`` / ``do_PUT`` / ``do_DELETE``.

    Discovery is regex-based; deliberately matches only the two
    patterns the codebase uses. A new dispatch style would need an
    update here. That's intentional — surfacing pattern drift is part
    of the value.
    """
    path = web_py_path or WEB_PY
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    table_routes: list[Route] = []
    legacy_routes: list[Route] = []
    in_method: str | None = None
    in_simple_get_table: bool = False
    in_regex_get_table: bool = False
    in_qs_regex_get_table: bool = False
    in_put_table: bool = False
    in_delete_table: bool = False
    in_post_table: bool = False
    for line_no, line in enumerate(lines, start=1):
        # ω.35-A.1 — track the `_SIMPLE_GET_ROUTES` table opening
        # so its `(path, handler)` tuples register as GET routes.
        if "_SIMPLE_GET_ROUTES" in line and "[" in line:
            in_simple_get_table = True
            continue
        if in_simple_get_table:
            te = _TABLE_ENTRY_RE.match(line)
            if te:
                table_routes.append(Route(method="GET", pattern=te.group(1), is_regex=False, line=line_no))
                continue
            # End of table on a closing `]`
            if line.strip().startswith("]"):
                in_simple_get_table = False
            continue

        # ω.35-A.4 — track the `_QS_REGEX_GET_ROUTES` table
        # opening. CHECKED BEFORE `_REGEX_GET_ROUTES` because the
        # latter's name is a substring of the former — substring
        # `in` would otherwise fire on the QS table's declaration
        # line and trigger the wrong branch.
        # Each entry is multi-line:
        #     (
        #         re.compile(r"^/api/foo/(...)$"),
        #         lambda m, qs: api_foo(...),
        #     ),
        # So we look specifically for a line that contains
        # `re.compile(r"^...")` while inside the block.
        if "_QS_REGEX_GET_ROUTES" in line and "[" in line:
            in_qs_regex_get_table = True
            continue
        if in_qs_regex_get_table:
            rx = re.match(r'\s*re\.compile\(\s*r"\^([^"]+)"\s*\)\s*,?\s*$', line)
            if rx:
                table_routes.append(Route(method="GET", pattern=rx.group(1), is_regex=True, line=line_no))
                continue
            # End of table on a closing `]` at start of line
            if line.strip().startswith("]"):
                in_qs_regex_get_table = False
            continue

        # ω.35-A.2 — track the `_REGEX_GET_ROUTES` table opening
        # so its `(re.compile(r"..."), handler)` tuples register
        # as GET regex routes.
        if "_REGEX_GET_ROUTES" in line and "[" in line:
            in_regex_get_table = True
            continue
        if in_regex_get_table:
            te = _REGEX_TABLE_ENTRY_RE.match(line)
            if te:
                table_routes.append(Route(method="GET", pattern=te.group(1), is_regex=True, line=line_no))
                continue
            if line.strip().startswith("]"):
                in_regex_get_table = False
            continue

        # ω.35-A.5 — track the `_PUT_ROUTES` table. Entries are
        # tuples `(re.compile(r"^..."), lambda m, payload:
        # api_X(...))` — match the regex pattern part. ruff may
        # reformat long entries onto multiple lines, so we accept
        # BOTH shapes:
        #   single-line:  (re.compile(r"^..."), lambda ...),
        #   multi-line:   `re.compile(r"^..."),` on its own line
        #                 (inside a multi-line tuple).
        if "_PUT_ROUTES" in line and "[" in line:
            in_put_table = True
            continue
        if in_put_table:
            te = re.match(r'\s*\(?\s*re\.compile\(\s*r"\^([^"]+)"\s*\)\s*,', line)
            if te:
                table_routes.append(Route(method="PUT", pattern=te.group(1), is_regex=True, line=line_no))
                continue
            if line.strip().startswith("]"):
                in_put_table = False
            continue

        # ω.35-A.6 — track the `_DELETE_ROUTES` table. Same shape
        # as `_PUT_ROUTES` but handler is `lambda m:` not
        # `lambda m, payload:`. Same multi-line tolerance.
        if "_DELETE_ROUTES" in line and "[" in line:
            in_delete_table = True
            continue
        if in_delete_table:
            te = re.match(r'\s*\(?\s*re\.compile\(\s*r"\^([^"]+)"\s*\)\s*,', line)
            if te:
                table_routes.append(Route(method="DELETE", pattern=te.group(1), is_regex=True, line=line_no))
                continue
            if line.strip().startswith("]"):
                in_delete_table = False
            continue

        # ω.35-A.7 — track the `_POST_ROUTES` table. Same shape
        # as `_PUT_ROUTES` (handler is `lambda m, payload:`).
        # Multi-line tolerance via `\(?` (optional opening paren) —
        # ruff reformats long lambdas onto multiple lines, putting
        # `re.compile(...)` on its own line.
        if "_POST_ROUTES" in line and "[" in line:
            in_post_table = True
            continue
        if in_post_table:
            te = re.match(r'\s*\(?\s*re\.compile\(\s*r"\^([^"]+)"\s*\)\s*,', line)
            if te:
                table_routes.append(Route(method="POST", pattern=te.group(1), is_regex=True, line=line_no))
                continue
            if line.strip().startswith("]"):
                in_post_table = False
            continue

        m = re.match(r"\s*def\s+do_([A-Z]+)\(", line)
        if m:
            in_method = m.group(1)
            continue
        # End of method when we hit a top-level def or class
        if re.match(r"^(def |class )", line):
            in_method = None
        if in_method is None:
            continue

        lit = _LITERAL_RE.match(line)
        if lit:
            primary, alias = lit.group(1), lit.group(2)
            legacy_routes.append(Route(method=in_method, pattern=primary, is_regex=False, line=line_no))
            if alias:
                legacy_routes.append(Route(method=in_method, pattern=alias, is_regex=False, line=line_no))
            continue

        rx = _REGEX_RE.match(line)
        if rx:
            legacy_routes.append(Route(method=in_method, pattern=rx.group(1), is_regex=True, line=line_no))
            continue

    # ω.35-A.1 — the migration intentionally leaves table-dispatched
    # routes ALSO in the legacy if/elif (as dead code) so the
    # discovery still finds them via the legacy regex if the table
    # is somehow malformed. Dedupe here — the table entry wins on
    # collision; the legacy duplicate is dropped from the
    # discovered set so the no_duplicate_patterns sub-check stays
    # clean. Unintentional duplicates (two if/elif branches for the
    # same path) still surface.
    table_keys = {(r.method, r.pattern) for r in table_routes}
    deduped_legacy = [r for r in legacy_routes if (r.method, r.pattern) not in table_keys]
    return table_routes + deduped_legacy


# ----------------------------------------------------------------------
# Sub-checks
# ----------------------------------------------------------------------


@dataclass
class CheckResult:
    id: str
    name: str
    status: str  # "pass" | "warn" | "fail"
    message: str
    violations: list = field(default_factory=list)


def _check_route_count(routes: list[Route]) -> CheckResult:
    """Surface the total route count. Pass at any count; trend over
    time is the signal."""
    by_method = Counter(r.method for r in routes)
    if not routes:
        return CheckResult(
            id="route_count",
            name="Route count",
            status="warn",
            message="no routes discovered (regex patterns may have changed?)",
        )
    parts = ", ".join(f"{m}={n}" for m, n in sorted(by_method.items()))
    return CheckResult(
        id="route_count",
        name="Route count",
        status="pass",
        message=f"{len(routes)} routes discovered ({parts})",
    )


def _check_no_duplicate_patterns(routes: list[Route]) -> CheckResult:
    """Within a single method, the same pattern cannot be reached
    twice — the second branch is dead code (cascade falls through
    on first match). Catches accidental duplication when adding a
    new route below an existing one with the same pattern."""
    by_key: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
    for r in routes:
        by_key[(r.method, r.pattern)].append(r.line)
    violations = []
    for (method, pattern), lines in by_key.items():
        if len(lines) > 1:
            violations.append(
                {
                    "method": method,
                    "pattern": pattern,
                    "lines": lines,
                }
            )
    if violations:
        return CheckResult(
            id="no_duplicate_patterns",
            name="No duplicate patterns",
            status="fail",
            message=f"{len(violations)} duplicate pattern(s) detected",
            violations=violations,
        )
    return CheckResult(
        id="no_duplicate_patterns",
        name="No duplicate patterns",
        status="pass",
        message="every (method, pattern) pair is unique",
    )


def _check_methods_covered(routes: list[Route]) -> CheckResult:
    """The Handler class implements 4 dispatch methods (GET/POST/
    PUT/DELETE). All four should have at least one route. Catches a
    method getting silently emptied during refactor."""
    expected = {"GET", "POST", "PUT", "DELETE"}
    seen = {r.method for r in routes}
    missing = sorted(expected - seen)
    if missing:
        return CheckResult(
            id="methods_covered",
            name="HTTP methods covered",
            status="warn",
            message=f"{len(missing)} method(s) have zero discovered routes: {', '.join(missing)}",
            violations=[{"missing_methods": missing}],
        )
    return CheckResult(
        id="methods_covered",
        name="HTTP methods covered",
        status="pass",
        message="all 4 dispatch methods (GET/POST/PUT/DELETE) have ≥1 route",
    )


def _check_regex_anchors(routes: list[Route]) -> CheckResult:
    """Every regex route should be anchored start-and-end with `^`
    and `$` — an unanchored pattern can match unexpectedly long
    paths and is a known footgun. The discovery regex strips the
    leading `^` already; this check looks at whether the surviving
    pattern ends with `$`.
    """
    violations = []
    for r in routes:
        if r.is_regex and not r.pattern.endswith("$"):
            violations.append(
                {
                    "method": r.method,
                    "pattern": r.pattern,
                    "line": r.line,
                }
            )
    if violations:
        return CheckResult(
            id="regex_anchors",
            name="Regex routes are end-anchored",
            status="fail",
            message=f"{len(violations)} regex route(s) missing end-anchor `$`",
            violations=violations,
        )
    return CheckResult(
        id="regex_anchors",
        name="Regex routes are end-anchored",
        status="pass",
        message="every regex route is anchored start-and-end",
    )


# ----------------------------------------------------------------------
# Aggregator
# ----------------------------------------------------------------------


def run_all(*, web_py_path: Path | None = None) -> dict:
    """Run all sub-checks. Standard preflight-aggregator shape per
    CLAUDE_PROJECT_RULES.md §9 ("Add a meta-tool that integrates
    with the preflight dashboard"):

        {
            "checks": [{id, name, status, message, violations}, ...],
            "summary": {total, pass, warn, fail, clean},
        }
    """
    routes = discover_routes(web_py_path=web_py_path)
    sub_checks = [
        _check_route_count(routes),
        _check_methods_covered(routes),
        _check_no_duplicate_patterns(routes),
        _check_regex_anchors(routes),
    ]

    summary = Counter()
    for c in sub_checks:
        summary[c.status] += 1
    summary["total"] = len(sub_checks)
    summary["clean"] = summary["fail"] == 0

    return {
        "checks": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "message": c.message,
                "violations": c.violations,
            }
            for c in sub_checks
        ],
        "summary": dict(summary),
        "route_count": len(routes),
    }


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description="ω.35-A — audit web.py route surface")
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    args = p.parse_args()

    result = run_all()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for c in result["checks"]:
            glyph = {"pass": "✓", "warn": "⚠", "fail": "✗"}[c["status"]]
            print(f"  {glyph} {c['name']:32s}  {c['message']}")
            for v in c["violations"]:
                print(f"      └─ {v}")
        s = result["summary"]
        clean = "CLEAN" if s["clean"] else "DRIFT"
        print(f"\n  {clean}: {s['pass']} pass · {s.get('warn', 0)} warn · {s.get('fail', 0)} fail")

    return 0 if result["summary"]["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
