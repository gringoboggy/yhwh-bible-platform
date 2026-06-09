#!/usr/bin/env python3
"""Phase θ.1 — Desktop launcher (PyInstaller-bundle entry point).

The single entry the desktop binary executes. Wraps
``scripts.web``'s ThreadingHTTPServer in:

  1. Optional first-run user-data migration (only when running
     frozen and the user-data ``content/`` dir lacks the
     ``editions.yaml`` marker — composes ω.5's
     ``scripts.migrate_to_user_data.perform_migration``).
  2. Robust port discovery (default 8765, falls back to an
     OS-assigned free port if 8765 is already bound).
  3. Server in the calling thread; browser auto-open scheduled
     on a daemon Timer so it fires after bind has succeeded.
  4. Block on ``serve_forever()``; clean shutdown on Ctrl-C.

In the frozen ``.exe`` / ``.app`` build, ``console=False`` in the
PyInstaller spec means there's no terminal window — the user
double-clicks the binary, the browser opens, and the user closes
the app by quitting the process tree (Task Manager / Activity
Monitor / killall). θ.2 will replace this loop with a native
window + Quit menu item.

Run (development):

    python3 scripts/launcher.py
    python3 scripts/launcher.py --port 9000
    python3 scripts/launcher.py --no-browser            # CI / headless
    python3 scripts/launcher.py --skip-bootstrap        # debug

Build (one-time, user-side — see ``dev/build_desktop.sh`` /
``dev/build_desktop.cmd``):

    pip install pyinstaller
    pyinstaller dev/launcher.spec        # produces dist/YHWH(.exe)

Per the §9 "pure function + thin route adapter" mental model,
the testable units are the helpers below; ``main()`` is the
thin orchestrator that wires them together with stdlib defaults
and accepts injectable callables for tests.
"""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import desktop_shell  # noqa: E402
from scripts.core import paths  # noqa: E402

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
BROWSER_DELAY_S = 0.5
SHELL_CHOICES = ("auto", "native", "browser")


def is_frozen() -> bool:
    """True when running inside a PyInstaller-built binary
    (``sys.frozen`` is set by the bootloader)."""
    return bool(getattr(sys, "frozen", False))


def find_free_port(preferred: int, host: str = DEFAULT_HOST) -> int:
    """Return ``preferred`` if it can bind, otherwise an OS-assigned
    free port. Pure utility — opens a socket, binds, reads the
    assigned port, closes. Caller binds the real server to the
    returned port immediately after — there's a TOCTOU window but
    it's acceptable for a single-user desktop launcher."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, preferred))
        except OSError:
            sock.bind((host, 0))
        return sock.getsockname()[1]


def should_run_first_run_migration() -> bool:
    """True iff we're running frozen AND the user-data ``content/``
    has not yet been bootstrapped (no ``editions.yaml`` marker).

    Dev (in-tree ``content/`` exists) returns False — the resolver
    serves the in-tree dir directly, no migration needed."""
    if not is_frozen():
        return False
    user_content = paths.user_data_root() / "content"
    return not (user_content / "editions.yaml").is_file()


def bootstrap_user_data(*, migrate_fn=None) -> dict:
    """First-run migration: copy bundled ``content/`` →
    ``user_data_root/content``. Idempotent. ``migrate_fn`` is
    injectable for tests; production default composes
    ``scripts.migrate_to_user_data``."""
    if migrate_fn is not None:
        return migrate_fn()
    from scripts.migrate_to_user_data import (
        _dst_content,
        _src_content,
        perform_migration,
    )

    return perform_migration(_src_content(), _dst_content())


def build_url(host: str, port: int) -> str:
    """Display URL for the bound address. ``0.0.0.0`` displays as
    ``localhost`` because most browsers won't navigate to
    ``http://0.0.0.0/``."""
    display_host = "localhost" if host == "0.0.0.0" else host
    return f"http://{display_host}:{port}/"


def start_server(host: str, port: int, *, server_factory=None):
    """Bind and return a ThreadingHTTPServer instance ready for
    ``serve_forever``. ``server_factory(host, port) -> server`` is
    injectable for tests; production default uses
    ``scripts.web.Handler``."""
    if server_factory is not None:
        return server_factory(host, port)
    from http.server import ThreadingHTTPServer

    from scripts.web import Handler

    return ThreadingHTTPServer((host, port), Handler)


def schedule_browser_open(
    url: str,
    *,
    delay: float = BROWSER_DELAY_S,
    opener=None,
) -> threading.Timer:
    """Spawn a daemon Timer that calls ``opener(url)`` after
    ``delay`` seconds. Default opener is ``webbrowser.open``.
    Returns the started Timer so callers can cancel or join."""
    if opener is None:
        opener = webbrowser.open
    timer = threading.Timer(delay, lambda: opener(url))
    timer.daemon = True
    timer.start()
    return timer


def main(
    argv: list[str] | None = None,
    *,
    server_factory=None,
    opener=None,
    migrate_fn=None,
    serve_fn=None,
    shell_fn=None,
) -> int:
    """Launcher entry point.

    Bootstraps user data on first frozen run, discovers a free
    port, starts the server, then either:

      * **native shell mode** (θ.2): server runs in a daemon
        thread, native PyWebView window blocks the main thread
        until the user closes it, then ``server.shutdown()``.
      * **browser mode** (θ.1 default): server runs in the main
        thread via ``serve_forever``; a daemon Timer opens the
        user's default browser. Ctrl-C shuts down cleanly.

    All five collaborators (server factory, browser opener,
    migration function, server-serve loop, native-shell function)
    are injectable so the full happy path can be exercised in a
    test without listening on a real socket or invoking PyWebView."""
    p = argparse.ArgumentParser(
        description=("YHWH desktop launcher — starts the local web server and opens the UI."),
    )
    p.add_argument("--host", default=DEFAULT_HOST, help="bind address (default: 127.0.0.1)")
    p.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=(f"preferred port (default: {DEFAULT_PORT}; auto-falls back to a free port if taken)"),
    )
    p.add_argument(
        "--no-browser",
        action="store_true",
        help=("browser mode only: don't auto-open the browser. Ignored in native shell mode."),
    )
    p.add_argument(
        "--skip-bootstrap", action="store_true", help=("skip first-run user-data migration even when running frozen")
    )
    p.add_argument(
        "--shell",
        choices=SHELL_CHOICES,
        default="auto",
        help=(
            "UI shell: 'native' (PyWebView window), "
            "'browser' (default browser tab), or "
            "'auto' (native when frozen + PyWebView "
            "installed, else browser)"
        ),
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help=("native shell: enable PyWebView dev tools (right-click → Inspect Element)"),
    )
    args = p.parse_args(argv)

    if not args.skip_bootstrap and should_run_first_run_migration():
        print("First run — copying bundled content/ to user-data dir…")
        result = bootstrap_user_data(migrate_fn=migrate_fn)
        copied = result.get("copied", 0)
        print(f"Copied {copied} files.")
        for err in result.get("errors", [])[:5]:
            print(f"  ! {err}")

    port = find_free_port(args.port, args.host)
    if port != args.port:
        print(f"Port {args.port} busy; using {port} instead.")

    server = start_server(args.host, port, server_factory=server_factory)
    url = build_url(args.host, port)
    frozen = is_frozen()
    pywebview_available = desktop_shell.is_pywebview_available()
    shell_mode = desktop_shell.select_shell_mode(
        frozen=frozen,
        available=pywebview_available,
        force=args.shell if args.shell != "auto" else None,
    )

    print()
    print("  YHWH — Bible publishing platform")
    print(f"  serving at: {url}")
    print(f"  shell:      {shell_mode}")
    # finding 7: make the native→browser fallback EXPLICIT. A frozen binary
    # auto-selects native; when the bundled PyWebView backend fails to import
    # (the launcher.spec hiddenimports gap), we silently land on browser — which
    # reads like normal behavior. Say so, so a packaging regression is visible.
    if shell_mode == "browser" and frozen and not pywebview_available and args.shell != "browser":
        print("  ! native window backend unavailable — falling back to the browser")
    if shell_mode == "browser":
        print("  Ctrl-C to stop")
    print()

    if shell_mode == "native":
        return _run_native(
            server,
            url,
            debug=args.debug,
            shell_fn=shell_fn,
        )
    return _run_browser(
        server,
        url,
        no_browser=args.no_browser,
        opener=opener,
        serve_fn=serve_fn,
    )


def _run_browser(server, url, *, no_browser, opener, serve_fn):
    """Browser shell mode: server runs in the main thread; a daemon
    Timer schedules ``opener(url)``. Ctrl-C triggers shutdown."""
    if not no_browser:
        schedule_browser_open(url, opener=opener)
    if serve_fn is None:
        serve_fn = server.serve_forever
    try:
        serve_fn()
    except KeyboardInterrupt:
        print("\n  stopping…")
        server.shutdown()
    return 0


def _run_native(server, url, *, debug, shell_fn):
    """Native shell mode: server runs in a daemon thread; the
    PyWebView window blocks the main thread until closed; then
    ``server.shutdown()`` and exit. ``shell_fn(url)`` is injectable
    for tests; production default is
    ``desktop_shell.open_in_native_shell``."""
    if shell_fn is None:

        def shell_fn(target_url):
            desktop_shell.open_in_native_shell(target_url, debug=debug)

    serve_thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    serve_thread.start()
    try:
        shell_fn(url)
    finally:
        server.shutdown()
        # Brief join so the thread tears down cleanly before exit.
        serve_thread.join(timeout=2.0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
