#!/usr/bin/env python3
"""Wave 4 (W4.1) — packaged-desktop-binary smoke test.

Proves the FROZEN PyInstaller binary actually works end-to-end — something the
unit suite (tests/test_desktop_theta.py) cannot, because it exercises the
launcher with injected collaborators, never the real `.exe`.

What it does:
  1. Launch the binary headless: `<exe> --shell browser --no-browser --port <p>`
     (browser shell + no auto-open = a pure local server, no PyWebView window).
  2. Poll `http://127.0.0.1:<p>/` until it returns 200 (the frozen one-file
     binary self-extracts + runs first-run user-data migration on launch, so
     this can take a while — hence the generous default timeout).
  3. Optionally (`--build-edition <id>`) POST `/api/export/build/<id>` and assert
     the build succeeds + names an output EPUB — the real "can it produce an
     EPUB" proof.
  4. Tear the process tree down (one-file binaries spawn a child bootloader).

Exit code 0 = smoke passed, 1 = failed. Stdlib-only so it adds no deps and runs
anywhere the binary does. CI-wireable (point `--exe` at the build artifact).

Examples:
    python dev/smoke_desktop.py --exe dist/YHWH.exe
    python dev/smoke_desktop.py --exe dist/YHWH.exe --build-edition jewish-study
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def find_free_port() -> int:
    """Ask the OS for a free TCP port (bind to 0, read it back, release)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(url: str, timeout_s: float) -> bool:
    """Poll ``url`` once a second until it answers 200 or ``timeout_s`` elapses."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, OSError, TimeoutError):
            pass
        time.sleep(1.0)
    return False


def trigger_build(base: str, edition_id: str, timeout_s: float) -> tuple[bool, str]:
    """POST /api/export/build/<id> and report (ok, message). Build is synchronous
    server-side, so the POST blocks until the EPUB is written (or fails)."""
    req = urllib.request.Request(
        f"{base}/api/export/build/{edition_id}",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return False, f"request failed: {e}"
    try:
        data = json.loads(body)
    except ValueError:
        return (status == 200, f"status {status}, non-JSON body: {body[:200]}")
    # api_export_build returns a dict; treat an explicit error/ok=False as failure.
    fname = data.get("filename") or data.get("file") or ""
    if status == 200 and data.get("error") is None and data.get("ok", True):
        return True, f"built {fname or '(epub)'}"
    return False, f"status {status}: {body[:300]}"


def terminate_tree(proc: subprocess.Popen) -> None:
    """Kill the launched process AND its children (one-file PyInstaller binaries
    run a child bootloader process)."""
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    else:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Smoke-test the packaged YHWH desktop binary.")
    p.add_argument("--exe", type=Path, default=Path("dist/YHWH.exe"), help="path to the built binary")
    p.add_argument("--port", type=int, default=0, help="port (default: an OS-assigned free port)")
    p.add_argument("--timeout", type=float, default=150.0, help="seconds to wait for the server to come up")
    p.add_argument("--build-edition", default=None, help="also build this edition id and assert an EPUB results")
    p.add_argument("--build-timeout", type=float, default=240.0, help="seconds to allow for the build POST")
    p.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="pass --skip-bootstrap to the launcher (skip first-run user-data migration; reads bundled content read-only — faster + repeatable, avoids the multi-GB copy)",
    )
    args = p.parse_args(argv)

    if not args.exe.is_file():
        print(f"FAIL: binary not found: {args.exe}", file=sys.stderr)
        return 1

    port = args.port or find_free_port()
    base = f"http://127.0.0.1:{port}"
    cmd = [str(args.exe), "--shell", "browser", "--no-browser", "--port", str(port)]
    if args.skip_bootstrap:
        cmd.append("--skip-bootstrap")
    print(f"launching: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
    )
    try:
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            print(f"FAIL: binary exited immediately (code {proc.returncode}).\n{out}", file=sys.stderr)
            return 1

        print(f"waiting up to {args.timeout:.0f}s for {base}/ …")
        if not wait_for_server(f"{base}/", args.timeout):
            print(f"FAIL: server never responded 200 at {base}/ within {args.timeout:.0f}s", file=sys.stderr)
            return 1
        print(f"PASS: server is up at {base}/")

        if args.build_edition:
            print(f"building edition '{args.build_edition}' (up to {args.build_timeout:.0f}s) …")
            ok, msg = trigger_build(base, args.build_edition, args.build_timeout)
            print(f"{'PASS' if ok else 'FAIL'}: build — {msg}")
            if not ok:
                return 1

        print("SMOKE PASSED")
        return 0
    finally:
        terminate_tree(proc)


if __name__ == "__main__":
    sys.exit(main())
