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


def test_cross_product_grid_clean_after_f1() -> None:
    """F1 REMEDIATED (round-16 Phase H): ``computer`` is now an explicit alias of
    ``everywhere`` (build_edition.TARGET_READER_ALIASES), so the cross-product grid no
    longer surfaces it as an ORPHAN OPTION and the whole grid is clean."""
    res = cx.audit_grid()
    assert not any("ORPHAN OPTION" in f and "computer" in f for f in res.fails), (
        f"computer should be an alias, not an orphan; grid fails={res.fails}"
    )
    assert res.green, f"cross-product grid should be clean after F1; fails={res.fails}"


def test_cross_product_reads_wizard_cards_and_detects_drift() -> None:
    """R16 Phase E (#11) — the gate now reads BOTH the /customize dropdown and the
    wizard target CARDS (a parallel target_reader entry point) and FAILs on drift."""
    # The wizard cards parse and include the computer target.
    assert "computer" in set(cx._wizard_reader_options())
    # The two real surfaces currently agree → no SURFACE DRIFT on the real grid.
    assert not any("SURFACE DRIFT" in f for f in cx.audit_grid().fails)
    # Inject a divergent /customize set → the parity check fires.
    drift = cx.audit_grid(reader_options=["everywhere"])
    assert any("SURFACE DRIFT" in f for f in drift.fails), drift.fails


def test_customize_completeness_selftest_non_tautological() -> None:
    """Dim-9: the build-read detector distinguishes a read field from an unread one."""
    assert cc._selftest() == 0


def test_customize_completeness_clean_after_f2() -> None:
    """F2 REMEDIATED (round-16 Phase H): ``verse_marker_glyph`` was RETIRED (control +
    validator + schema spec + loader echo + the catholic-study ``¶`` value all removed),
    so the completeness gate no longer surfaces it as an orphan and the path is clean."""
    res = cc.audit_completeness()
    assert not any("verse_marker_glyph" in f for f in res.fails), (
        f"verse_marker_glyph should be retired, not an orphan; fails={res.fails}"
    )
    assert res.green, f"customize-completeness should be clean after F2; fails={res.fails}"


def test_output_hygiene_selftest_non_tautological() -> None:
    """The html-integrity / code-leak detector flags synthetic leaks + nested-<a>, clean text 0."""
    assert hy._selftest() == 0
