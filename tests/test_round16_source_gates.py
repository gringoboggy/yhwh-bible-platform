"""Round-16 build-free source gates wired into the per-push suite.

The round-16 Build-Program-Bulletproofing audit adds deterministic ``dev/audit_*.py``
gates. The BUILD-FREE ones (no EPUB rebuild — pure source/table analysis) run here on
every push: each ``--selftest`` proves the detector is non-tautological (SYNTHETIC, so it
stays valid after the findings are remediated). The artifact scanner ``audit_output_hygiene``
needs a built EPUB → its full run lives in ``test_round16_build_gates.py`` (slow); only its
synthetic selftest runs here.

Imported in-process (``conftest`` puts the repo root on ``sys.path``; ``dev`` is a PEP-420
namespace package) so the heavy ``scripts.*`` imports are paid once, not per subprocess.

NOTE (round-16 is FINDINGS-ONLY): the gates' REAL runs currently FAIL by design — they
surface the confirmed findings F1 (the ``computer`` orphan reader target) and F2 (the
``verse_marker_glyph`` orphan /customize field). Those are recorded in
``dev/audit/round16-remediation.md``; the "clean on the current tree" assertions are added
in the remediation phase (once the findings are fixed), per the round-15 D1 precedent.
"""

from __future__ import annotations

import dev.audit_cross_product as cx
import dev.audit_customize_completeness as cc
import dev.audit_output_hygiene as hy


def test_cross_product_selftest_non_tautological() -> None:
    """Dim-4: the orphan-option check fires on a valid-target/no-format-row grid + passes a full one."""
    assert cx._selftest() == 0


def test_cross_product_detects_computer_orphan() -> None:
    """Pins finding F1 — the real grid still surfaces the ``computer`` orphan (build-free, deterministic).

    This intentionally asserts the KNOWN-defect state; when F1 is remediated (a FORMAT_MATRIX
    row for ``computer`` or its removal from the /customize dropdown) this flips and is updated
    to assert the grid is clean."""
    res = cx.audit_grid()
    assert any("ORPHAN OPTION" in f and "computer" in f for f in res.fails), (
        f"expected the computer orphan; grid fails={res.fails}"
    )


def test_customize_completeness_selftest_non_tautological() -> None:
    """Dim-9: the build-read detector distinguishes a read field from an unread one."""
    assert cc._selftest() == 0


def test_customize_completeness_detects_verse_marker_glyph_orphan() -> None:
    """Pins finding F2 — ``verse_marker_glyph`` is validated/echoed but read nowhere on the
    build path. Updated to a clean-tree assertion once F2 is remediated."""
    res = cc.audit_completeness()
    assert any("verse_marker_glyph" in f for f in res.fails), (
        f"expected the verse_marker_glyph orphan; fails={res.fails}"
    )


def test_output_hygiene_selftest_non_tautological() -> None:
    """The html-integrity / code-leak detector flags synthetic leaks + nested-<a>, clean text 0."""
    assert hy._selftest() == 0
