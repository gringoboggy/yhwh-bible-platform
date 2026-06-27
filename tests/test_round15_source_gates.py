"""Round-15 build-free source gates wired into the per-push suite.

The round-15 completeness audit adds deterministic ``dev/audit_*.py`` gates. The
BUILD-FREE ones (no EPUB rebuild — pure source/data analysis) run here on every push:
their ``--selftest`` proves the detector is non-tautological, and the real run proves the
current tree is clean. Build-NEEDING gates stay in ``test_round14_build_gates.py`` (slow).

Imported in-process (``conftest`` puts the repo root on ``sys.path``; ``dev`` is a PEP-420
namespace package) so the heavy ``scripts.core`` imports are paid once, not per subprocess.

D1's real run needs the live release asset list + SHA256SUMS (network), so only its
selftest runs here; the live check is a tag-time / manual step (see the gate docstring).
"""

from __future__ import annotations

import pytest

import dev.audit_canon_bookcount as d6
import dev.audit_migration_idempotence as d7
import dev.audit_release_assets as d1
import dev.audit_versification_coverage as d3


def test_d3_coverage_selftest_non_tautological() -> None:
    """The D3 detector flags a synthetic drop + out-of-extent map and passes clean coverage."""
    assert d3._selftest() == 0


@pytest.mark.slow
def test_d3_coverage_clean_on_current_tree() -> None:
    """Every Douay/Vulgate source verse maps non-None + in-extent (or is an allowlisted omit)."""
    for translation in d3._REMAP_TRANSLATIONS:
        res = d3.audit_translation(translation)
        assert res.green, f"{translation} versification coverage FAIL: {res.fails[:5]}"


def test_d3_fix_present_ps_2_13_and_4_10() -> None:
    """Round-15 D3 fix: the two dropped trailing verses now fold onto their KJV verse."""
    from scripts.core.versification import vulgate_to_kjv

    assert vulgate_to_kjv("psa", 2, 13) == ("psa", 2, 12)
    assert vulgate_to_kjv("psa", 4, 10) == ("psa", 4, 8)


def test_d1_release_asset_selftest_non_tautological() -> None:
    """The D1 detector flags retired-SKU / orphan-sum / missing-sum / stale-version assets."""
    assert d1._selftest() == 0


def test_d6_canon_bookcount_selftest_non_tautological() -> None:
    """The D6 detector flags a canon book-set divergence between two sources."""
    assert d6._selftest() == 0


def test_d6_canon_bookcount_clean_on_current_tree() -> None:
    """The 5 canon sources agree per edition + note counts are internally consistent + in-canon."""
    res = d6.audit()
    assert res.green, f"D6 canon/note cross-check FAIL: {res.fails[:5]}"


def test_d7_migration_idempotence_selftest_non_tautological() -> None:
    """The D7 checks fire on a deliberately-broken (marker-first, non-atomic) migration."""
    assert d7._selftest() == 0


def test_d7_migration_torn_safe_and_idempotent() -> None:
    """Real 0001 migration is marker-last + atomic + double-apply idempotent + torn-recoverable."""
    fails, _ = d7.audit()
    assert not fails, f"D7 migration idempotency FAIL: {fails[:5]}"
