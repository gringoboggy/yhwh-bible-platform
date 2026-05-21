"""Tests for scripts/run_manuscript_transcribe_at_scale.py (C-2 offload).

The transcription driver turns folio images into a first-draft witness
JSON via one vision call — replacing the agent-reads-PNGs C-2 step that
fed the OOM crashes. The script computes `tokens` from the model's `geez`
using the validator's own tokenizer, so the geez<->tokens invariant holds
by construction and the output is structurally valid for C-3 review.

A ``FakeVision`` stub avoids Pillow / SDK / API-key needs.
"""


class FakeVision:
    def __init__(self, out):
        self._out = out
        self.last_usage = None
        self.model = "fake-model"

    def analyze(self, system_prompt, text, image_blocks, *, output_schema, max_tokens=4096):
        self.seen = {"system": system_prompt, "text": text, "schema": output_schema}
        return self._out


def test_assemble_witness_computes_tokens_and_validates():
    from scripts.core.manuscript_records import _geez_to_tokens, validate_witness
    from scripts.run_manuscript_transcribe_at_scale import assemble_witness

    model_out = {
        "verses": [
            {
                "v": 1,
                "column": "f030v-M-L23",
                "line_start": 23,
                "geez": "ወፈነሙ ፡ ኪራም",
                "uncertain": [],
            }
        ]
    }
    w = assemble_witness(
        model_out,
        book="1ki",
        chapter=5,
        witness_sig="GG",
        source_images=["GAPS/x/f030v.jpg"],
        folio_sigla=["f030v"],
    )
    # top-level shape
    assert w["witness"] == "GG" and w["book"] == "1ki" and w["chapter"] == 5
    # tokens computed via the validator's own tokenizer (invariant by construction)
    assert w["verses"][0]["tokens"] == _geez_to_tokens("ወፈነሙ ፡ ኪራም")
    # each verse carries exactly the 6 schema keys
    assert set(w["verses"][0]) == {"v", "column", "line_start", "geez", "tokens", "uncertain"}
    # and the assembled record passes the real validator
    ok, errors = validate_witness(w)
    assert ok, errors


def test_run_transcribe_flows_images_and_returns_witness():
    from scripts.run_manuscript_transcribe_at_scale import run_transcribe

    fake = FakeVision(
        {
            "verses": [
                {
                    "v": 1,
                    "column": "f030v-M-L23",
                    "line_start": 23,
                    "geez": "ወፈነሙ ፡ ኪራም",
                    "uncertain": [{"token_index": 0, "marker": "uncertain", "note": "rubric-adjacent"}],
                }
            ]
        }
    )
    w = run_transcribe(
        book="1ki",
        chapter=5,
        witness_sig="GG",
        source_images=["GAPS/x/f030v.jpg"],
        folio_sigla=["f030v"],
        vision_client=fake,
        topology_text="TOPOLOGY-MARKER",
        image_blocks=[{"type": "image"}],
    )
    assert w["verses"][0]["v"] == 1
    assert w["verses"][0]["uncertain"][0]["marker"] == "uncertain"
    assert "TOPOLOGY-MARKER" in fake.seen["system"]


def test_run_transcribe_empty_model_out_is_empty_witness():
    from scripts.run_manuscript_transcribe_at_scale import run_transcribe

    w = run_transcribe(
        book="1ki",
        chapter=5,
        witness_sig="GG",
        source_images=["GAPS/x/f030v.jpg"],
        folio_sigla=["f030v"],
        vision_client=FakeVision({}),
        topology_text="T",
        image_blocks=[],
    )
    assert w["verses"] == []
    assert w["witness"] == "GG"
