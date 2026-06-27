"""Round-14 — wire the per-build EPUB gates G3/G4/G5 into the (slow) regression
suite. This is the program's "G3/G4/G5 -> ALL_CHECKS (cheap per-build)"
deliverable, realised as ONE slow test (CI runs ``-m slow``): build a single
representative eink study edition and run all three freshly-built gates on its
*pre-kepub* EPUB, asserting each PASSES.

catholic-study eink exercises every gate at once: the file-split cross-piece
idmap (G3 ``audit_idmap_frags``), the badge-collapse conservation (G4
``audit_badge_conservation`` — needs the ``.stats.json`` sidecar build_one
writes), and the eink study-glossary navigate-cap contract (G5
``audit_glossary_contract``). The gates run on the pre-kepub build output, which
is why this lives here and not in reader_sim's post-kepub artifact gates (kepub
koboSpan inflation would skew the G5 codepoint cap).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

REPO = Path(__file__).resolve().parents[1]
_GATES = ("audit_idmap_frags.py", "audit_glossary_contract.py", "audit_badge_conservation.py")


def test_round14_build_gates_pass_on_catholic_study_eink(tmp_path):
    """A fresh catholic-study eink build passes G3 (idmap) + G4 (badge) + G5 (glossary)."""
    from scripts import build_edition as be
    from scripts.core import config

    be.build_one("catholic-study", tmp_path, "v28a-r14gate", config.load_kinds(), force=True, target_reader="eink")
    epubs = list(tmp_path.glob("*.epub"))
    assert len(epubs) == 1, f"expected exactly one EPUB, got {len(epubs)}"
    epub = epubs[0]

    failures: list[str] = []
    for gate in _GATES:
        args = [sys.executable, str(REPO / "dev" / gate), str(epub)]
        if gate == "audit_badge_conservation.py":
            args.append("--require-sidecar")  # build_one wrote the sidecar -> enforce, don't skip
        if gate == "audit_idmap_frags.py":
            # round-15 D2 presence floor: catholic-study eink resolves ~100k frag+noteref
            # anchors (round-14: 57k frag + 45k noteref), so a count below 10k means the
            # build dropped its cross-references wholesale -> FAIL instead of vacuous-green.
            args += ["--min-links", "10000"]
        proc = subprocess.run(args, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if proc.returncode != 0:
            failures.append(f"{gate} (exit {proc.returncode}):\n{(proc.stdout + proc.stderr)[-800:]}")
    assert not failures, "round-14 build gate(s) FAILED on catholic-study eink:\n" + "\n\n".join(failures)
