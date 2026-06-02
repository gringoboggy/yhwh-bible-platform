"""The agent-path assemble-and-write shim (P1 of the Sam/Kings cloud plan).

Tests the pure `assemble_and_write` + the thin `main` (stdin-driven) directly —
no subprocess (keeps it off the W-W1 subprocess-stdin lint + fast).
"""

import io
import json
import sys

from scripts.manuscript_assemble_witness import assemble_and_write, main

MODEL_OUT = {
    "verses": [
        {"v": 1, "geez": "ወይቤ ፡ ንጉሥ", "column": "f030v-M-L1", "line_start": 1, "uncertain": []},
    ],
    "transcription_notes": "smoke",
}


def test_assemble_and_write_valid(tmp_path):
    out = tmp_path / "1ki5_witnessGG.json"
    ok, path, errors = assemble_and_write(
        MODEL_OUT,
        book="1ki",
        chapter=5,
        witness="GG",
        source_images=["GAPS/2_Kings/GG-00106/1-Kings/1-Kings_f030v.jpg"],
        folios=["f030v"],
        out_path=str(out),
    )
    assert ok, errors
    rec = json.loads(out.read_text(encoding="utf-8"))
    assert rec["witness"] == "GG"
    assert rec["book"] == "1ki"
    assert rec["chapter"] == 5
    # tokens computed from geez by assemble_witness (geez↔tokens invariant by construction)
    assert rec["verses"][0]["tokens"] == ["ወይቤ", "ንጉሥ"]


def test_main_reads_model_out_from_stdin(tmp_path, monkeypatch):
    out = tmp_path / "w.json"
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(MODEL_OUT)))
    rc = main(
        [
            "--book",
            "1ki",
            "--chapter",
            "5",
            "--witness",
            "CAM",
            "--source-image",
            "x.jpg",
            "--folio",
            "f001r",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    assert json.loads(out.read_text(encoding="utf-8"))["witness"] == "CAM"
