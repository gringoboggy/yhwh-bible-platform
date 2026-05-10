"""
ui.py — Shared CLI helpers: ANSI color constants + err/info functions.

Consolidated from 6+ duplicates across scripts (Phase β.2 / C3). Use as:

    from scripts.core.ui import GREEN, RED, YELLOW, DIM, BOLD, RESET
    from scripts.core.ui import err, info, ok, warn

The colors are 16-color ANSI escapes — universally supported in
modern terminals. ``RESET`` clears all attributes.
"""

from __future__ import annotations

import sys

__all__ = [
    "GREEN",
    "RED",
    "YELLOW",
    "BLUE",
    "CYAN",
    "MAGENTA",
    "DIM",
    "BOLD",
    "RESET",
    "err",
    "info",
    "ok",
    "warn",
]

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def err(msg: str, *, exit_code: int = 1) -> None:
    """Print an error to stderr in red and exit with the given code."""
    print(f"{RED}✗ {msg}{RESET}", file=sys.stderr)
    sys.exit(exit_code)


def info(msg: str) -> None:
    """Print an informational note to stderr in dim style."""
    print(f"{DIM}{msg}{RESET}", file=sys.stderr)


def ok(msg: str) -> None:
    """Print a success line to stdout in green."""
    print(f"{GREEN}✓ {msg}{RESET}")


def warn(msg: str) -> None:
    """Print a warning to stderr in yellow."""
    print(f"{YELLOW}⚠ {msg}{RESET}", file=sys.stderr)
