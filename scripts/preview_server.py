#!/usr/bin/env python3
"""
preview_server.py — Serve ``epub_working/`` on localhost for browser dev.

Lets you click through the EPUB in a browser without packaging it first.
Just run, point your browser at the printed URL, and refresh after edits.

This is the minimum-viable version: pure-stdlib HTTP server, no
auto-reload. If you want auto-refresh on file change today, pair it with
a tool like ``entr`` or your editor's own preview integration.

Examples:
    python3 scripts/preview_server.py
        # serve ./epub_working/ on http://localhost:8000

    python3 scripts/preview_server.py -p 8080
        # custom port

    python3 scripts/preview_server.py --no-cache
        # send no-cache headers so refreshes always re-fetch

Stop with Ctrl-C.

Exit codes:
    0  shut down cleanly (Ctrl-C)
    2  setup error (epub_working missing, port in use, …)
"""

import argparse
import http.server
import socketserver
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EPUB_DIR = REPO_ROOT / "epub_working"

GREEN = "\033[92m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"


class QuieterHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with optional no-cache headers and tidier logs."""

    no_cache = False

    def end_headers(self):
        if self.no_cache:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        # One short line per request, no ANSI to keep terminals clean.
        sys.stderr.write(f"  {self.address_string()}  {fmt % args}\n")


def make_handler_class(directory: str, no_cache: bool):
    """Build a handler class bound to a directory + no-cache preference."""
    cls = type(
        "BoundHandler",
        (QuieterHandler,),
        {"no_cache": no_cache},
    )

    def factory(*a, **kw):
        return cls(*a, directory=directory, **kw)

    return factory


def main() -> None:
    p = argparse.ArgumentParser(
        description="Serve epub_working/ for browser-based development.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("-p", "--port", type=int, default=8000, help="port (default 8000)")
    p.add_argument(
        "--epub-dir",
        type=Path,
        default=EPUB_DIR,
        help="directory to serve (default: epub_working/)",
    )
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="send no-cache headers so refreshes always re-fetch",
    )
    p.add_argument("-b", "--bind", default="127.0.0.1", help="bind address (default 127.0.0.1)")
    args = p.parse_args()

    if not args.epub_dir.is_dir():
        print(f"{RED}ERROR: not a directory: {args.epub_dir}{RESET}", file=sys.stderr)
        sys.exit(2)

    handler = make_handler_class(str(args.epub_dir.resolve()), args.no_cache)

    try:
        with socketserver.TCPServer((args.bind, args.port), handler) as httpd:
            try:
                rel = args.epub_dir.relative_to(REPO_ROOT)
            except ValueError:
                rel = args.epub_dir
            url_base = f"http://{args.bind}:{args.port}"
            entry_pages = ("titlepage.xhtml", "introduction.xhtml", "nav.xhtml", "index_split_000.html")
            entry = next((e for e in entry_pages if (args.epub_dir / e).is_file()), "")
            print(f"\n  {GREEN}serving{RESET} {rel}/  on  {url_base}/")
            if entry:
                print(f"  start here: {url_base}/{entry}")
            if args.no_cache:
                print(f"  {DIM}(no-cache headers enabled){RESET}")
            print(f"  {DIM}(Ctrl-C to stop){RESET}\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped.")
    except OSError as e:
        if e.errno in (48, 98, 10048):  # EADDRINUSE on macOS / Linux / Windows
            print(
                f"{RED}ERROR: port {args.port} already in use. Try -p {args.port + 1}{RESET}",
                file=sys.stderr,
            )
            sys.exit(2)
        raise


if __name__ == "__main__":
    main()
