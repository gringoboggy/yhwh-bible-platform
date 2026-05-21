"""Tests for scripts/run_manuscript_review_at_scale.py (lever 4).

The review driver runs the manuscript R-round adversarial review as a
standalone script: it sends folio images + the witness JSON to the vision
API and writes a REVIEW.md + machine-readable defects JSON. The agent/main
thread reads only that text — no image bytes ever enter the harness buffer
(the root cause of the 2026-05-20/21 OOM crashes).

A ``FakeVision`` stub stands in for ``AnthropicVisionClient`` so these
tests need neither Pillow, the anthropic SDK, nor an API key.
"""

import json

WITNESS = {
    "witness": "GG",
    "book": "1ki",
    "chapter": 5,
    "source_images": ["GAPS/x/1-Kings_f030v.jpg", "GAPS/x/1-Kings_f031r.jpg"],
    "folio_sigla": ["f030v", "f031r"],
    "verses": [
        {
            "v": 1,
            "column": "f030v-M-L23",
            "line_start": 23,
            "geez": "ወፈነሙ ፡ ኪራም",
            "tokens": ["ወፈነሙ", "ኪራም"],
            "uncertain": [],
        }
    ],
}


class FakeVision:
    """Stand-in for AnthropicVisionClient.analyze."""

    def __init__(self, out):
        self._out = out
        self.last_usage = None
        self.model = "fake-model"

    def analyze(self, system_prompt, text, image_blocks, *, output_schema, max_tokens=4096):
        self.seen = {
            "system": system_prompt,
            "text": text,
            "blocks": image_blocks,
            "schema": output_schema,
        }
        return self._out


def test_run_review_assembles_result():
    from scripts.run_manuscript_review_at_scale import run_review

    model_out = {
        "overall_verdict": "NEEDS_FIX",
        "boundary_verdict": "ok",
        "omission_check": "none",
        "defects": [
            {
                "verse": 1,
                "severity": "CRITICAL",
                "locus": "v1",
                "current": "x",
                "parchment": "y",
                "fix": "z",
                "defect_class": "le/se",
            },
            {
                "verse": 1,
                "severity": "MINOR",
                "locus": "v1",
                "current": "a",
                "parchment": "b",
                "fix": "c",
                "defect_class": "vowel",
            },
        ],
        "new_ambiguous": ["foo"],
    }
    fake = FakeVision(model_out)
    res = run_review(
        WITNESS,
        vision_client=fake,
        topology_text="TOPOLOGY-MARKER",
        image_blocks=[{"type": "image"}],
        current_round=1,
    )
    assert res["hard_defects"] == 1  # CRITICAL counts, MINOR does not
    assert res["new_ambiguous"] == 1
    assert res["chapter_class"]  # non-empty class string
    assert "escalation" in res and "escalate" in res["escalation"]
    assert res["defects"] == model_out["defects"]
    # topology + witness geez flowed into the prompt the model saw
    assert "TOPOLOGY-MARKER" in fake.seen["system"]
    assert "ወፈነሙ" in fake.seen["text"]


def test_run_review_defensive_on_empty_model_out():
    from scripts.run_manuscript_review_at_scale import run_review

    res = run_review(
        WITNESS,
        vision_client=FakeVision({}),
        topology_text="T",
        image_blocks=[],
        current_round=1,
    )
    assert res["defects"] == []
    assert res["hard_defects"] == 0
    # escalate_if_unbounded: zero hard defects => no escalation
    assert res["escalation"]["escalate"] is False


def test_render_review_md_contains_verdict_and_defects():
    from scripts.run_manuscript_review_at_scale import render_review_md, run_review

    model_out = {
        "overall_verdict": "NEEDS_FIX",
        "boundary_verdict": "verified",
        "omission_check": "none",
        "defects": [
            {
                "verse": 7,
                "severity": "CRITICAL",
                "locus": "v7 cross",
                "current": "ከእ",
                "parchment": "ከ ✣",
                "fix": "reattach suffix",
                "defect_class": "body-cross",
            }
        ],
        "new_ambiguous": [],
    }
    res = run_review(
        WITNESS,
        vision_client=FakeVision(model_out),
        topology_text="T",
        image_blocks=[],
        current_round=1,
    )
    md = render_review_md(res)
    assert "NEEDS_FIX" in md
    assert "v7" in md and "CRITICAL" in md


def test_write_outputs(tmp_path):
    from scripts.run_manuscript_review_at_scale import run_review, write_outputs

    res = run_review(
        WITNESS,
        vision_client=FakeVision(
            {
                "overall_verdict": "APPROVE",
                "boundary_verdict": "",
                "omission_check": "",
                "defects": [],
                "new_ambiguous": [],
            }
        ),
        topology_text="T",
        image_blocks=[],
        current_round=2,
    )
    md_path, json_path = write_outputs(res, out_dir=str(tmp_path), current_round=2)
    assert md_path.exists() and json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["witness"] == "GG"
    assert data["book"] == "1ki" and data["chapter"] == 5
