"""Round-14 G1 — the KJV golden-hash gate (the headline build-pipeline gate).

The 9-KJV byte-stable set = {catholic-study, evangelical-reformed,
eastern-orthodox} × {everywhere, tablet, kindle} MUST ship byte-identical
whenever no scripture/base change occurs. Until now byte-stability was proven
only by ``test_byte_stability_gate.py`` (determinism: rebuild == rebuild) —
which CANNOT catch a leak that lands identically in BOTH rebuilds — plus a
manual regen + ``git diff``. This gate stores a reviewed golden content-digest
per cell and fails when a build drifts from it (closes B10 / proves-or-refutes
every eink-gating leak A1).

After round-14 **A1** (the ``ocf_member_bytes`` CRLF→LF chokepoint in
``scripts/core/zip_repro.py``, wired at ``build_epub.py`` + ``kindle_post.py``)
the digests are ALSO OS-independent: the SAME golden passes on Windows, macOS,
and Linux. The ubuntu CI workflow ``.github/workflows/kjv-golden.yml`` runs this
gate in check mode as the Linux-sided cross-OS proof (round-14 A4).

The digest reuses ``test_byte_stability_gate._content_digest`` (the per-build
URN / dcterms:modified / dc:date / rights-year are normalized out), so the
golden is over scripture + notes + structure, not a per-build identifier.

Regenerate the golden ONLY on a deliberate, reviewed base re-baseline::

    PYTHONUTF8=1 PYTHONPATH=. py -3 tests/test_kjv_golden_hash_gate.py --regen

Nine real full-edition builds (~2 min each) → the module is marked ``slow`` and
is deselected by ``-m "not slow"``.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pytest

# Reuse the existing volatile-field normalizer (single source of truth for what
# "byte-stable content" means) rather than re-deriving it here.
from tests.test_byte_stability_gate import _content_digest

pytestmark = pytest.mark.slow

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = Path(__file__).resolve().parent / "golden" / "kjv_golden_hashes.json"

# The 9 byte-stable cells. ``None`` target == the "everywhere" default build
# (``apply_target_override(None)`` returns the edition unchanged); tablet/kindle
# are matrix-M1 overrides. eink + the standalones are deliberately
# re-baselineable and are intentionally EXCLUDED from the golden.
BYTE_STABLE_EDITIONS = ("catholic-study", "evangelical-reformed", "eastern-orthodox")
BYTE_STABLE_TARGETS = (None, "tablet", "kindle")


def _cell_key(ed: str, target: str | None) -> str:
    return f"{ed}::{target or 'everywhere'}"


def _build_cell(ed: str, target: str | None, out_root: Path) -> Path:
    from scripts import build_edition as be
    from scripts.core import config

    out_dir = out_root / _cell_key(ed, target).replace("::", "__")
    out_dir.mkdir(parents=True, exist_ok=True)
    be.build_one(ed, out_dir, "v28a-golden", config.load_kinds(), force=True, target_reader=target)
    epubs = list(out_dir.glob("*.epub"))
    assert len(epubs) == 1, f"{_cell_key(ed, target)}: expected exactly 1 EPUB, got {len(epubs)}"
    return epubs[0]


def compute_cell_digests(out_root: Path) -> dict[str, str]:
    """Build all 9 byte-stable cells and return ``{cell_key: content_digest}``."""
    digests: dict[str, str] = {}
    for ed in BYTE_STABLE_EDITIONS:
        for target in BYTE_STABLE_TARGETS:
            epub = _build_cell(ed, target, out_root)
            digests[_cell_key(ed, target)] = _content_digest(epub)
    return digests


def _load_golden() -> dict[str, str]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_kjv_golden_hashes_match(tmp_path):
    """Every byte-stable cell's content-digest matches the committed golden."""
    if not GOLDEN_PATH.exists():
        pytest.skip(f"golden not yet generated: {GOLDEN_PATH} (run with --regen after a reviewed re-baseline)")
    golden = _load_golden()
    built = compute_cell_digests(tmp_path)
    mismatched = sorted(k for k in (set(golden) | set(built)) if golden.get(k) != built.get(k))
    assert not mismatched, (
        "KJV byte-stable cells drifted from the golden. If this is a DELIBERATE, reviewed base "
        "re-baseline, regenerate with `py -3 tests/test_kjv_golden_hash_gate.py --regen`. "
        f"Mismatched cells: {mismatched}"
    )


def _regen(out_root: Path) -> None:
    digests = compute_cell_digests(out_root)
    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN_PATH.write_text(json.dumps(digests, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(digests)} golden cell digests -> {GOLDEN_PATH}")
    for k in sorted(digests):
        print(f"  {k}: {digests[k]}")


def main() -> int:
    p = argparse.ArgumentParser(description="KJV golden-hash gate (round-14 G1)")
    p.add_argument("--regen", action="store_true", help="rebuild the 9 byte-stable cells and re-stamp the golden")
    p.add_argument("--out", type=Path, default=None, help="build output root (default: a fresh temp dir)")
    args = p.parse_args()
    out_root = args.out or Path(tempfile.mkdtemp(prefix="kjv-golden-"))

    if args.regen:
        _regen(out_root)
        return 0

    # check mode (CI / manual): build + compare, exit non-zero on drift/missing.
    if not GOLDEN_PATH.exists():
        print(f"ERROR: golden missing: {GOLDEN_PATH} (run with --regen)", file=sys.stderr)
        return 1
    golden = _load_golden()
    built = compute_cell_digests(out_root)
    drift = [k for k in sorted(set(golden) | set(built)) if golden.get(k) != built.get(k)]
    if drift:
        print("FAIL: KJV golden drift", file=sys.stderr)
        for k in drift:
            print(f"  {k}: golden={golden.get(k)} built={built.get(k)}", file=sys.stderr)
        return 1
    print(f"OK: {len(golden)} byte-stable cells match the golden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
