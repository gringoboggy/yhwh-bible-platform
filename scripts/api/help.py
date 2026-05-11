"""ω.35-B.7 — /apihelp data endpoint, extracted from scripts/web.py.

One handler: `api_help_data` (Phase ω.3). Enumerates every /api/* route
+ every /<console> route by regex-scanning the `scripts/web.py` source.
The result powers the `/apihelp` console; nothing here mutates state or
hits the network.

The scanner targets `scripts/web.py` specifically, even after the file
split: route tables (`_SIMPLE_GET_ROUTES`, `_REGEX_GET_ROUTES`,
`_QS_REGEX_GET_ROUTES`, `_PUT_ROUTES`, `_DELETE_ROUTES`) and the legacy
if/elif cascade all still live there. The extracted `scripts/api/*.py`
modules hold only handler function bodies — route registration is still
centralized in web.py.

Backward compatibility: re-exported from `scripts.web` so the route
table lambda (in `_SIMPLE_GET_ROUTES`) and any test that imports
`scripts.web.api_help_data` keeps working.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent


# Route patterns to recognize, in source-scan order. Each entry's
# regex captures the path. The regex matches the WHOLE source line
# (including leading whitespace) so context comments can be located
# from the same line index.
_ROUTE_PATTERNS = [
    # GET: if path == "/api/X":   or   if path == "/X" or path == "/X.html":
    (re.compile(r'^\s*if\s+path\s*==\s*"(/api/[^"]+)"'), "GET"),
    (re.compile(r'^\s*if\s+path\.startswith\("(/api/[^"]+)"'), "GET"),
    # POST: if self.path == "/api/X":
    (re.compile(r'^\s*if\s+self\.path\s*==\s*"(/api/[^"]+)"'), "POST"),
    # Pattern: m = re.match(r"^/api/X/...$", self.path)
    (re.compile(r'^\s*m\s*=\s*re\.match\(r"\^(/api/[^"$]+)\$"'), "PATTERN"),
    # ω.35-A.3 — also discover `_SIMPLE_GET_ROUTES` table entries.
    # Each line of the form `("/api/foo", api_foo),` registers a
    # table-dispatched GET route.
    (re.compile(r'^\s*\(\s*"(/api/[^"]+)"\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*\)\s*,?\s*$'), "GET"),
    # ω.35-A.3 — also discover `_REGEX_GET_ROUTES` table entries.
    # Each line of the form `(re.compile(r"^/api/foo/(...)$"), api_foo),`.
    # Strip leading `^` and trailing `$` to align with /apihelp's
    # human-friendly path display.
    (re.compile(r'^\s*\(\s*re\.compile\(\s*r"\^(/api/[^"$]+)\$"\s*\)\s*,'), "PATTERN"),
    # ω.35-A.4 — also discover `_QS_REGEX_GET_ROUTES` table entries.
    # The pattern is on its own line inside the multi-line entry:
    #     re.compile(r"^/api/foo$"),
    # Same regex as ω.35-A.3 but anchored to a standalone line
    # (entries in _REGEX_GET_ROUTES are single-line tuples).
    (re.compile(r'^\s*re\.compile\(\s*r"\^(/api/[^"$]+)\$"\s*\)\s*,?\s*$'), "PATTERN"),
]

# Console-page routes (HTML, not API). These get listed separately
# in the help page since they're a different kind of surface.
_CONSOLE_PATTERNS = [
    re.compile(
        r'^\s*if\s+path\s*==\s*"(/[a-z][^"/]*)"\s*or\s*'
        r'path\s*==\s*"\1\.html"'
    ),
]


def api_help_data() -> dict:
    """Enumerate every /api/* route + every /<console> route by
    scanning scripts/web.py source. The result powers the /apihelp
    console; nothing here mutates state or hits the network.

    Returns:
        {
          "status": "ok",
          "api_routes": [
            {"method": str, "path": str, "description": str,
             "phase": str | None, "line": int}, ...
          ],
          "consoles": [
            {"path": str, "description": str, "phase": str | None,
             "line": int}, ...
          ],
          "totals": {"api": int, "consoles": int},
        }
    """
    src_path = REPO / "scripts" / "web.py"
    try:
        lines = src_path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        return {"status": "error", "code": "source_read_failed", "http": 500, "message": str(e)}

    api_routes: list[dict] = []
    consoles: list[dict] = []
    seen_api: set[tuple[str, str]] = set()
    seen_console: set[str] = set()

    # Phase regex — matches "Phase X.Y" or "Phase Xx.Y" in
    # comments above a route. ω, ψ, etc. are real characters
    # in the codebase.
    phase_re = re.compile(r"Phase\s+([α-ωΑ-Ω][a-z]?\.[\w.\-]+)")

    def gather_context(line_idx: int, max_lookback: int = 8) -> str:
        """Walk backward from a route line collecting comment lines.
        Stop at the first non-comment, non-empty line OR after
        max_lookback lines."""
        comment_lines: list[str] = []
        for j in range(line_idx - 1, max(-1, line_idx - max_lookback), -1):
            line = lines[j].strip()
            if not line:
                if comment_lines:
                    break
                continue
            if line.startswith("#"):
                comment_lines.append(line.lstrip("#").strip())
            else:
                break
        comment_lines.reverse()
        return " ".join(comment_lines)

    for i, line in enumerate(lines):
        # API routes
        for pattern, method in _ROUTE_PATTERNS:
            m = pattern.match(line)
            if m:
                path = m.group(1)
                # The PATTERN method gets its placeholders
                # explicit (e.g. /api/translation/<id>/<book>)
                if method == "PATTERN":
                    # Convert regex segments like ([a-z0-9-]+) → <param>
                    path = re.sub(r"\(\[[^\]]+\]\+\)", "<param>", path)
                key = (method, path)
                if key in seen_api:
                    break
                seen_api.add(key)
                ctx = gather_context(i)
                phase_match = phase_re.search(ctx)
                api_routes.append(
                    {
                        "method": method if method != "PATTERN" else "GET/POST",
                        "path": path,
                        "description": ctx,
                        "phase": phase_match.group(1) if phase_match else None,
                        "line": i + 1,
                    }
                )
                break

        # Console pages
        for pattern in _CONSOLE_PATTERNS:
            m = pattern.match(line)
            if m:
                path = m.group(1)
                if path in seen_console:
                    break
                seen_console.add(path)
                ctx = gather_context(i)
                phase_match = phase_re.search(ctx)
                consoles.append(
                    {
                        "path": path,
                        "description": ctx,
                        "phase": phase_match.group(1) if phase_match else None,
                        "line": i + 1,
                    }
                )
                break

    # Sort: API routes by path; consoles by path
    api_routes.sort(key=lambda r: r["path"])
    consoles.sort(key=lambda r: r["path"])

    return {
        "status": "ok",
        "api_routes": api_routes,
        "consoles": consoles,
        "totals": {
            "api": len(api_routes),
            "consoles": len(consoles),
        },
    }
