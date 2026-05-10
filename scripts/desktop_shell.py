#!/usr/bin/env python3
"""Phase θ.2 — Native desktop shell (PyWebView wrapper).

Wraps the local web UI in a real native window: no address bar,
native title bar, native close button, native window-manager
chrome on every platform. The console UI itself is unchanged —
PyWebView simply renders the same pages a browser would, inside
a borderless WKWebView (macOS), WebView2 (Windows), or
WebKitGTK (Linux) frame.

Architecture: PyWebView's ``webview.start()`` blocks the calling
thread, so when the launcher selects native shell mode it runs
the HTTP server in a daemon thread and ``webview.start()`` on
the main thread. Closing the window unblocks ``start()``; the
launcher then calls ``server.shutdown()`` and exits.

Optional dependency: PyWebView is imported lazily via
``is_pywebview_available()``. The launcher falls back to the
browser flow when PyWebView is absent so dev environments
without it still work — only the desktop binary build needs it
pinned (see ``dev/launcher.spec`` hiddenimports).

Test surface (per §9 mental model — pure helpers + injectable
collaborators):

  * ``is_pywebview_available()`` — lazy import; cached True/False.
  * ``select_shell_mode(*, frozen, available, force=None)`` — picks
    ``"native"`` or ``"browser"`` based on environment + override.
  * ``window_config()`` — returns the window kwargs dict (title,
    width, height, etc.) so tests can assert defaults without
    invoking PyWebView.
  * ``open_in_native_shell(url, *, title, webview_module=None)`` —
    creates the window and blocks on ``start()``; the webview
    module is injectable for tests.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

DEFAULT_TITLE = "YHWH — Bible publishing platform"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 900
DEFAULT_MIN_WIDTH = 960
DEFAULT_MIN_HEIGHT = 600


@lru_cache(maxsize=1)
def is_pywebview_available() -> bool:
    """True iff ``import webview`` succeeds. Cached so repeated
    calls don't pay the import cost. Tests that need to flip this
    should call ``is_pywebview_available.cache_clear()``."""
    try:
        import webview  # noqa: F401
    except ImportError:
        return False
    except Exception:
        # Any other import-time failure (missing platform backend,
        # broken venv) is treated as "unavailable" so the launcher
        # falls back gracefully rather than crashing.
        return False
    return True


def select_shell_mode(
    *,
    frozen: bool,
    available: bool,
    force: str | None = None,
) -> str:
    """Return ``"native"`` or ``"browser"``.

    Precedence:
      1. ``force`` if provided ("native" or "browser"). Anything
         else (including "auto") falls through.
      2. Auto: native iff frozen AND PyWebView is importable;
         browser otherwise (dev mode prefers a real browser for
         devtools, copy/paste URL sharing, etc.)."""
    if force == "native":
        return "native"
    if force == "browser":
        return "browser"
    if frozen and available:
        return "native"
    return "browser"


def window_config(
    url: str,
    *,
    title: str = DEFAULT_TITLE,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    min_size: tuple[int, int] = (DEFAULT_MIN_WIDTH, DEFAULT_MIN_HEIGHT),
    resizable: bool = True,
) -> dict:
    """Return the kwargs dict passed to ``webview.create_window``.

    Pure function — exists primarily so tests can assert defaults
    without depending on PyWebView's API. The launcher passes the
    result through ``**`` to ``create_window``."""
    return {
        "title": title,
        "url": url,
        "width": width,
        "height": height,
        "min_size": min_size,
        "resizable": resizable,
    }


def open_in_native_shell(
    url: str,
    *,
    title: str = DEFAULT_TITLE,
    webview_module=None,
    debug: bool = False,
) -> None:
    """Create the native window and block on ``webview.start()``
    until the user closes it.

    ``webview_module`` is injectable for tests; production default
    is ``import webview``. Raises ``RuntimeError`` if PyWebView
    is unavailable AND the caller did not inject a substitute —
    this should never happen in the production code path because
    ``select_shell_mode`` guards against it, but we fail loudly
    rather than silently fall back to the browser here.

    ``debug=True`` enables PyWebView's developer console (right-
    click → Inspect Element on supported backends)."""
    if webview_module is None:
        try:
            import webview as webview_module  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "PyWebView is not installed. Install with "
                "`pip install pywebview` or run the launcher with "
                "`--shell browser`."
            ) from exc
    cfg = window_config(url, title=title)
    webview_module.create_window(**cfg)
    webview_module.start(debug=debug)
