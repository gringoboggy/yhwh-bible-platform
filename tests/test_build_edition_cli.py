"""build_edition.py CLI — dry-run must not crash.

Regression guard for an UnboundLocalError in `main()`: the sequential path
printed the `✓ <output>.epub (N MB)` line unconditionally, but `tag` (and the
`output_path`/`size_mb` stats) only exist on a real build — so `--dry-run`
crashed after printing its filter stats. The dry-run path was untested, which
is how it stayed broken.
"""

from __future__ import annotations

import sys

import pytest


def test_dry_run_exits_cleanly(monkeypatch, capsys):
    from scripts import build_edition

    monkeypatch.setattr(sys, "argv", ["build_edition.py", "ethiopian-tewahedo", "--dry-run"])
    with pytest.raises(SystemExit) as exc:
        build_edition.main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "kinds enabled" in out  # filter stats printed
