"""ω.27 follow-on (2026-05-11) — χ-AI-xrefs test classes, split out
of the monolithic ``tests/test_scripts.py`` into a topic file
alongside the other ω.27 follow-on splits.

Eleventh topic extraction. The χ-AI-xrefs arc was the first
χ-cluster detector backed by an LLM API (Anthropic) rather
than a static cached source. The three test classes cover:

- TestAnthropicXrefClient — source-loader-level checks for the
  LLM client (injected completion_fn keeps tests offline)
- TestAIXrefDetector — detector-level checks (candidate shape,
  kind, attribution, budget-cap handling)
- TestRunAIXrefsAtScaleDriver — at-scale driver checks
  (per-chapter queue write, idempotency, dry-run mode)

Paired with the AI-content safety phase ξ.15 (HTML sandbox)
which is already in test_security_xi_late.py.

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# χ-AI-xrefs — AnthropicXrefClient + AIXrefDetector + driver
# (LLM-backed thematic cross-reference proposals; first χ-cluster
# detector backed by an API rather than a static cached source.)
# ============================================================


class TestAnthropicXrefClient:
    """Source-loader-level checks for the AI xref client. All tests
    use the injected ``completion_fn`` so no real network call is
    made; the real-SDK construction path is exercised only by the
    SourceMissingError checks."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources as src

        cls.src = src

    def test_construct_raises_when_no_api_key_and_no_completion_fn(
        self,
        monkeypatch,
    ):
        # Both env var and SDK absent (or env var absent alone is
        # enough since we check it first) → SourceMissingError.
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(self.src.SourceMissingError) as ei:
            self.src.AnthropicXrefClient()
        assert "ANTHROPIC_API_KEY" in str(ei.value)

    def test_construct_succeeds_with_injected_completion_fn(self):
        def stub_fn(system, user, *, model):
            return {"proposals": []}

        client = self.src.AnthropicXrefClient(completion_fn=stub_fn)
        assert client.model == self.src.DEFAULT_AI_XREF_MODEL
        assert "Claude AI" in client.attribution

    def test_propose_xrefs_parses_valid_response(self):
        def stub_fn(system, user, *, model):
            return {
                "proposals": [
                    {
                        "target_book": "isa",
                        "target_chapter": 53,
                        "target_verse": 5,
                        "kind_subclass": "typological",
                        "reasoning": "Suffering servant figure prefigures...",
                        "confidence": 0.85,
                    },
                ]
            }

        client = self.src.AnthropicXrefClient(completion_fn=stub_fn)
        out = client.propose_xrefs(
            "mrk",
            15,
            24,
            "And they crucified him,",
            top_n=3,
        )
        assert len(out) == 1
        p = out[0]
        assert p["target_book"] == "isa"
        assert p["target_chapter"] == 53
        assert p["target_verse"] == 5
        assert p["kind_subclass"] == "typological"
        assert p["confidence"] == 0.85

    def test_propose_xrefs_drops_unknown_book_codes(self):
        def stub_fn(system, user, *, model):
            return {
                "proposals": [
                    {
                        "target_book": "isa",
                        "target_chapter": 1,
                        "target_verse": 1,
                        "kind_subclass": "thematic",
                        "reasoning": "",
                        "confidence": 0.8,
                    },
                    {
                        "target_book": "xyz",
                        "target_chapter": 1,
                        "target_verse": 1,
                        "kind_subclass": "thematic",
                        "reasoning": "",
                        "confidence": 0.8,
                    },
                    {
                        "target_book": "fakeBook",
                        "target_chapter": 1,
                        "target_verse": 1,
                        "kind_subclass": "thematic",
                        "reasoning": "",
                        "confidence": 0.8,
                    },
                ]
            }

        client = self.src.AnthropicXrefClient(completion_fn=stub_fn)
        out = client.propose_xrefs("gen", 1, 1, "In the beginning")
        assert len(out) == 1
        assert out[0]["target_book"] == "isa"

    def test_propose_xrefs_clamps_confidence_to_unit_interval(self):
        def stub_fn(system, user, *, model):
            return {
                "proposals": [
                    {
                        "target_book": "psa",
                        "target_chapter": 1,
                        "target_verse": 1,
                        "kind_subclass": "thematic",
                        "reasoning": "x",
                        "confidence": 1.7,
                    },
                    {
                        "target_book": "psa",
                        "target_chapter": 1,
                        "target_verse": 2,
                        "kind_subclass": "thematic",
                        "reasoning": "x",
                        "confidence": -0.3,
                    },
                ]
            }

        client = self.src.AnthropicXrefClient(completion_fn=stub_fn)
        out = client.propose_xrefs("gen", 1, 1, "x")
        confidences = sorted(p["confidence"] for p in out)
        assert confidences == [0.0, 1.0]

    def test_propose_xrefs_returns_empty_on_malformed_response(self):
        # Non-dict response, non-list proposals, parse / IO failures
        # all degrade defensively to []. Programming errors do NOT —
        # see test_propose_xrefs_propagates_programming_errors.
        import json as _json

        # Build a fake exception whose module name starts with
        # "anthropic" — propose_xrefs catches these by module-name
        # prefix to avoid hard-importing the SDK at module load.
        class _FakeAPIError(Exception):
            pass

        _FakeAPIError.__module__ = "anthropic._exceptions"

        for stub in (
            lambda s, u, *, model: "not a dict",
            lambda s, u, *, model: {"proposals": "not a list"},
            lambda s, u, *, model: {"proposals": [None, "string", 42]},
            lambda s, u, *, model: (_ for _ in ()).throw(
                _json.JSONDecodeError("bad", "doc", 0),
            ),
            lambda s, u, *, model: (_ for _ in ()).throw(
                OSError("network down"),
            ),
            lambda s, u, *, model: (_ for _ in ()).throw(
                _FakeAPIError("rate limit"),
            ),
        ):
            client = self.src.AnthropicXrefClient(completion_fn=stub)
            assert client.propose_xrefs("gen", 1, 1, "x") == []

    def test_propose_xrefs_propagates_programming_errors(self):
        # Tightened exception handling: bugs in completion_fn surface
        # so they get caught in tests, not silently dropped at scale.
        def buggy_stub(system, user, *, model):
            raise TypeError("programming error — not a network blip")

        client = self.src.AnthropicXrefClient(completion_fn=buggy_stub)
        with pytest.raises(TypeError):
            client.propose_xrefs("gen", 1, 1, "x")

    def test_system_prompt_meets_haiku_4_5_cache_minimum(self):
        # CRITICAL: prompt caching on Haiku 4.5 silently does nothing
        # below a 4096-token prefix. The system prompt must clear
        # that threshold or the at-scale driver's cost projection
        # is wrong by 5-10×. Token estimate via the conservative
        # 4-chars-per-token rule (real ratio is closer to 3.5 for
        # technical/structured prose, so this is a floor).
        prompt = self.src.AI_XREF_SYSTEM_PROMPT
        est_tokens_floor = len(prompt) / 4.0
        assert est_tokens_floor >= 4096, (
            f"System prompt is too short for Haiku 4.5 caching. "
            f"chars={len(prompt)}, est_tokens_floor={est_tokens_floor:.0f}, "
            f"required>=4096. Add worked examples / anti-patterns; "
            f"do not lower this assertion."
        )

    def test_default_model_uses_alias_not_dated_id(self):
        # Aliases get capability updates without code changes; dated
        # snapshots pin to a specific model release. Skill recommends
        # alias unless reproducibility outweighs Anthropic's quality
        # bumps — for χ-AI-xrefs we want the bumps.
        assert self.src.DEFAULT_AI_XREF_MODEL == "claude-haiku-4-5"
        # No date suffix
        assert not any(
            c.isdigit() and i > len("claude-haiku-4-5") for i, c in enumerate(self.src.DEFAULT_AI_XREF_MODEL)
        )

    def test_cache_ttl_is_one_hour(self):
        # 1h TTL costs 2× to write but covers the full 31K-verse run
        # which takes ~30+ wall-clock minutes. 5-min ephemeral would
        # repeatedly invalidate.
        assert self.src.AI_XREF_CACHE_TTL == "1h"

    def test_output_schema_locks_proposal_shape(self):
        # The json_schema goes to output_config.format on the request
        # so the model is forced to emit the documented shape — no
        # regex-strip-fences hack needed.
        schema = self.src.AI_XREF_OUTPUT_SCHEMA
        assert schema["type"] == "object"
        assert "proposals" in schema["properties"]
        proposal = schema["properties"]["proposals"]["items"]
        required = set(proposal["required"])
        assert {"target_book", "target_chapter", "target_verse", "kind_subclass", "reasoning", "confidence"} <= required
        kind_enum = proposal["properties"]["kind_subclass"]["enum"]
        assert set(kind_enum) == {"typological", "thematic", "idiomatic"}
        assert proposal["additionalProperties"] is False

    def test_last_usage_starts_unset(self):
        # Stub completion_fns leave last_usage as None; only the real
        # SDK path populates it. Driver checks this attr to verify
        # cache hits before paying for a long run.
        client = self.src.AnthropicXrefClient(
            completion_fn=lambda s, u, *, model: {"proposals": []},
        )
        assert client.last_usage is None

    def test_propose_xrefs_caps_at_top_n(self):
        def stub_fn(system, user, *, model):
            return {
                "proposals": [
                    {
                        "target_book": "psa",
                        "target_chapter": i,
                        "target_verse": 1,
                        "kind_subclass": "thematic",
                        "reasoning": "",
                        "confidence": 0.8,
                    }
                    for i in range(1, 11)
                ]
            }

        client = self.src.AnthropicXrefClient(completion_fn=stub_fn)
        out = client.propose_xrefs("gen", 1, 1, "x", top_n=2)
        assert len(out) == 2

    def test_propose_xrefs_drops_invalid_chapter_or_verse(self):
        def stub_fn(system, user, *, model):
            return {
                "proposals": [
                    {
                        "target_book": "psa",
                        "target_chapter": 0,
                        "target_verse": 1,
                        "kind_subclass": "thematic",
                        "reasoning": "",
                        "confidence": 0.8,
                    },
                    {
                        "target_book": "psa",
                        "target_chapter": 1,
                        "target_verse": "x",
                        "kind_subclass": "thematic",
                        "reasoning": "",
                        "confidence": 0.8,
                    },
                    {
                        "target_book": "psa",
                        "target_chapter": 1,
                        "target_verse": 1,
                        "kind_subclass": "thematic",
                        "reasoning": "",
                        "confidence": 0.8,
                    },
                ]
            }

        client = self.src.AnthropicXrefClient(completion_fn=stub_fn)
        out = client.propose_xrefs("gen", 1, 1, "x")
        assert len(out) == 1
        assert out[0]["target_chapter"] == 1

    def test_default_completion_fn_wires_xref_ttl_and_schema(self, monkeypatch):
        # The real-SDK call body is the B1.8 de-dup target: the xref and
        # note clients share an identical messages.create skeleton differing
        # ONLY in the cache TTL and the output schema. Pin that the xref
        # client wires its OWN constants (AI_XREF_*), with a faked SDK
        # client so no network call is made. After the de-dup to a shared
        # base, a mis-wired class attr would flip these to the note
        # constants and fail here.
        from scripts.core import sources_ai_clients as aic

        captured = {}

        class _FakeUsage:
            input_tokens = 11
            output_tokens = 22
            cache_creation_input_tokens = 5
            cache_read_input_tokens = 3

        class _FakeBlock:
            type = "text"
            text = '{"proposals": []}'

        class _FakeResponse:
            usage = _FakeUsage()
            content = [_FakeBlock()]
            _request_id = "req_xref_1"

        class _FakeClient:
            def __init__(self):
                self.messages = self

            def create(self, **kwargs):
                captured.update(kwargs)
                return _FakeResponse()

        monkeypatch.setattr(aic, "_anthropic_client", lambda: _FakeClient())

        # Inject a stub at construction (bypasses the SDK precondition),
        # then call the real default fn directly to exercise the SDK body.
        client = self.src.AnthropicXrefClient(completion_fn=lambda s, u, *, model: {})
        result = client._default_completion_fn("SYS-PROMPT", "USER-MSG", model="claude-haiku-4-5")

        assert result == {"proposals": []}  # parses the response text as JSON
        assert captured["model"] == "claude-haiku-4-5"
        assert captured["max_tokens"] == 2048
        assert captured["system"][0]["text"] == "SYS-PROMPT"
        assert captured["system"][0]["cache_control"]["ttl"] == self.src.AI_XREF_CACHE_TTL
        assert captured["messages"] == [{"role": "user", "content": "USER-MSG"}]
        assert captured["output_config"]["format"]["schema"] is self.src.AI_XREF_OUTPUT_SCHEMA
        # Telemetry captured onto the instance for the at-scale driver.
        assert client.last_usage["input_tokens"] == 11
        assert client.last_usage["cache_read_input_tokens"] == 3
        assert client.last_usage["request_id"] == "req_xref_1"


class TestAIXrefDetector:
    """Detector-level checks for AIXrefDetector. Stubbed clients —
    no real API calls."""

    @classmethod
    def setup_class(cls):
        from scripts.core import detectors as det
        from scripts.core import sources as src

        cls.det = det
        cls.src = src

    def _stub_client(self, proposals):
        def stub_fn(system, user, *, model):
            return {"proposals": proposals}

        return self.src.AnthropicXrefClient(completion_fn=stub_fn)

    def test_detect_emits_candidates_with_correct_kind(self):
        client = self._stub_client(
            [
                {
                    "target_book": "isa",
                    "target_chapter": 53,
                    "target_verse": 5,
                    "kind_subclass": "typological",
                    "reasoning": "Suffering servant.",
                    "confidence": 0.85,
                },
            ]
        )
        detector = self.det.AIXrefDetector(client=client, min_confidence=0.7)
        cands = detector.detect("mrk", 15, 24, "they crucified him")
        assert len(cands) == 1
        c = cands[0]
        assert c.kind == "xref-thematic"
        assert c.book == "mrk"
        assert c.chapter == 15
        assert c.verse == 24
        assert c.detector == "AIXrefDetector"

    def test_detect_filters_below_min_confidence(self):
        client = self._stub_client(
            [
                {
                    "target_book": "isa",
                    "target_chapter": 1,
                    "target_verse": 1,
                    "kind_subclass": "thematic",
                    "reasoning": "weak",
                    "confidence": 0.5,
                },
                {
                    "target_book": "isa",
                    "target_chapter": 1,
                    "target_verse": 2,
                    "kind_subclass": "thematic",
                    "reasoning": "strong",
                    "confidence": 0.9,
                },
            ]
        )
        detector = self.det.AIXrefDetector(client=client, min_confidence=0.7)
        cands = detector.detect("gen", 1, 1, "x")
        assert len(cands) == 1
        assert cands[0].confidence == 0.9

    def test_detect_passes_top_n_to_client(self):
        captured = {}

        def stub_fn(system, user, *, model):
            return {"proposals": []}

        client = self.src.AnthropicXrefClient(completion_fn=stub_fn)
        # Wrap propose_xrefs to capture the top_n it received
        orig = client.propose_xrefs

        def spy(*a, **kw):
            captured["top_n"] = kw.get("top_n")
            return orig(*a, **kw)

        client.propose_xrefs = spy
        detector = self.det.AIXrefDetector(client=client, top_n=5)
        detector.detect("gen", 1, 1, "x")
        assert captured["top_n"] == 5

    def test_attribution_mentions_claude_ai(self):
        client = self._stub_client(
            [
                {
                    "target_book": "psa",
                    "target_chapter": 1,
                    "target_verse": 1,
                    "kind_subclass": "thematic",
                    "reasoning": "x",
                    "confidence": 0.8,
                },
            ]
        )
        detector = self.det.AIXrefDetector(client=client)
        cands = detector.detect("gen", 1, 1, "x")
        assert "Claude AI" in cands[0].source_attribution

    def test_body_includes_reasoning_and_reviewer_note_in_notes(self):
        client = self._stub_client(
            [
                {
                    "target_book": "isa",
                    "target_chapter": 53,
                    "target_verse": 5,
                    "kind_subclass": "typological",
                    "reasoning": "The servant's wounds prefigure the cross.",
                    "confidence": 0.85,
                },
            ]
        )
        detector = self.det.AIXrefDetector(client=client)
        cands = detector.detect("mrk", 15, 24, "they crucified him")
        body = cands[0].draft_body
        assert "Typological" in body
        assert "prefigure the cross" in body
        # RX Phase 1: the editorial scaffold no longer ships in the body; the
        # reviewer guidance lives in reviewer_notes=.
        assert "[Reviewer:" not in body
        assert "AI-proposed" in cands[0].reviewer_notes
        # link is to the target verse — the VISIBLE #v- anchor (round-7 P3
        # xref retarget: note-body links to hidden #vnote- containers made
        # Kobo NAVIGATE instead of pop; verify_kr2 gate 2b now FAILS any
        # #vnote- body link, so the detector emits #v- by design)
        assert "#v-isa-53-5" in body
        assert "vnote-isa-53-5" not in body

    def test_kind_subclass_unknown_falls_back_to_thematic(self):
        client = self._stub_client(
            [
                {
                    "target_book": "isa",
                    "target_chapter": 1,
                    "target_verse": 1,
                    "kind_subclass": "weirdsubclass",
                    "reasoning": "x",
                    "confidence": 0.8,
                },
            ]
        )
        detector = self.det.AIXrefDetector(client=client)
        cands = detector.detect("gen", 1, 1, "x")
        # The client normalises unknown subclass to 'thematic'
        assert "Thematic" in cands[0].draft_body

    def test_registered_in_ALL_DETECTORS(self):
        assert self.det.AIXrefDetector in self.det.ALL_DETECTORS

    def test_kind_xref_thematic_in_kinds_yaml(self):
        kinds_path = REPO_ROOT / "content" / "kinds.yaml"
        text = kinds_path.read_text(encoding="utf-8")
        assert "code: xref-thematic" in text
        assert "category: xref" in text

    def test_construct_without_client_propagates_source_missing(
        self,
        monkeypatch,
    ):
        # Real-default construction path: when no env key + no client,
        # __init__ must surface SourceMissingError so prospect.py's
        # resilient instantiation handler catches it.
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        self.src.anthropic_xref_client.cache_clear()
        with pytest.raises(self.src.SourceMissingError):
            self.det.AIXrefDetector()


class TestRunAIXrefsAtScaleDriver:
    """Driver-level checks. The driver imports translations + config
    for verse iteration; tests inject a fixture iterator + stub
    detector to avoid real KJV scans where convenient."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.driver = importlib.import_module("scripts.run_ai_xrefs_at_scale")
        from scripts.core import at_scale_base as asb
        from scripts.core import detectors as det
        from scripts.core import sources as src

        cls.asb = asb  # iter_target_verses/resolve_books live here (v0.1.0 STAGE A hoist)
        cls.det = det
        cls.src = src

    def _stub_detector_factory(self, proposals_per_verse=None):
        """Returns a callable that constructs a detector wired to a
        stub client; ``proposals_per_verse`` is a callable
        (book,ch,vs,text) -> list[dict] for fine-grained control."""
        if proposals_per_verse is None:

            def proposals_per_verse(b, c, v, t):
                return [
                    {
                        "target_book": "isa",
                        "target_chapter": 1,
                        "target_verse": v,
                        "kind_subclass": "thematic",
                        "reasoning": "stub",
                        "confidence": 0.8,
                    },
                ]

        def factory():
            class StubClient:
                attribution = "Claude AI (stub)."

                def propose_xrefs(self_inner, b, c, v, t, *, top_n=3):
                    return proposals_per_verse(b, c, v, t)[:top_n]

            return self.det.AIXrefDetector(
                client=StubClient(),
                top_n=3,
                min_confidence=0.7,
            )

        return factory

    def test_dry_run_writes_nothing_and_exits_zero(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        cand_dir = tmp_path / "candidates"
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)
        # No API key needed because we never reach the construction path.
        rc = self.driver.main(
            [
                "--dry-run",
                "--books",
                "jhn",
                "--max-verses",
                "10",
            ]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "Projected cost" in out
        assert "dry-run" in out
        assert not cand_dir.exists()

    def test_confirm_cost_required_above_threshold(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        cand_dir = tmp_path / "candidates"
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)
        threshold = self.driver.CONFIRM_COST_THRESHOLD
        rc = self.driver.main(
            [
                "--books",
                "jhn",
                "--max-verses",
                str(threshold + 1),
            ]
        )
        assert rc == 1
        out = capsys.readouterr().out
        assert "REFUSING" in out
        assert "--confirm-cost" in out
        assert not cand_dir.exists()

    def test_max_verses_caps_iteration(self, monkeypatch):
        # Use the real iter_target_verses against the real KJV data
        # and verify the cap is honored.
        verses = list(
            self.asb.iter_target_verses(
                ["jhn"],
                max_verses=5,
            )
        )
        assert len(verses) == 5
        for book, _ch, _vs, _text in verses:
            assert book == "jhn"

    def test_iter_target_verses_skips_books_without_kjv(self):
        # 'fakebook' doesn't exist in KJV — it should be skipped silently.
        verses = list(
            self.asb.iter_target_verses(
                ["fakebook", "jhn"],
                max_verses=3,
            )
        )
        assert len(verses) == 3
        for book, _ch, _vs, _text in verses:
            assert book == "jhn"

    def test_iter_target_verses_covers_high_chapter_books(self):
        # mint-7 B1 regression: the chapter cap read books.yaml's non-existent
        # "chapters" key → always 50, silently skipping Psalms 51-150, Isaiah
        # 51-66, etc. on every full-corpus AI run. With the ch_count fix all 150
        # Psalm chapters are iterated.
        chapters = {ch for _b, ch, _vs, _t in self.asb.iter_target_verses(["psa"], max_verses=10**9)}
        assert max(chapters) == 150, f"expected Psalms to reach ch 150, got {max(chapters)} (chapter cap regressed?)"
        assert len(chapters) == 150

    def test_ai_at_scale_drivers_use_ch_count_not_chapters(self):
        # Guard against re-introducing the wrong YAML key (books.yaml has
        # ch_count, never "chapters"). Source-scan, since the functional symptom
        # (silent under-coverage) is invisible at run time.
        #
        # mint-9: the chapter-iteration logic was deduped into
        # scripts/core/at_scale_base.iter_target_verses (mint-8 batch-1), so the
        # `ch_count` read lives THERE, not inline in each driver. v0.1.0 STAGE A
        # hoisted the WHOLE driver core (iteration + aggregation) into
        # at_scale_base.run_ai_detector, so the drivers now delegate via that.
        # The drivers must (a) never reintroduce the bad "chapters" key and
        # (b) delegate to the shared core (run_ai_detector → iter_target_verses);
        # the canonical ch_count read is pinned in at_scale_base. (Previously this
        # scanned the drivers for the literal ch_count read and went stale the
        # moment the logic was factored out — re-homed here per the same rule.)
        import pathlib

        repo = pathlib.Path(__file__).resolve().parent.parent
        for name in ("run_ai_xrefs_at_scale.py", "run_ai_notes_at_scale.py"):
            src = (repo / "scripts" / name).read_text(encoding="utf-8")
            assert 'get("chapters"' not in src, f"{name} uses the non-existent 'chapters' key (mint-7 B1)"
            assert "run_ai_detector" in src, f"{name} should delegate iteration to at_scale_base.run_ai_detector"
        assert "iter_target_verses" in (repo / "scripts" / "core" / "at_scale_base.py").read_text(encoding="utf-8"), (
            "at_scale_base.run_ai_detector must iterate via iter_target_verses"
        )
        base_src = (repo / "scripts" / "core" / "at_scale_base.py").read_text(encoding="utf-8")
        assert 'get("ch_count"' in base_src, "at_scale_base.iter_target_verses must read ch_count (mint-7 B1)"
        assert 'get("chapters"' not in base_src, "at_scale_base must not use the non-existent 'chapters' key"

    def test_run_xref_write_queue_appends_not_overwrites(self, tmp_path, monkeypatch):
        # mint-7 B2: run_xref_at_scale.write_queue must APPEND (preserve other
        # drivers' candidates on the same chapter file), not clobber + reset ids
        # — it was the lone driver of 9 that overwrote.
        import json

        import scripts.run_xref_at_scale as xref
        from scripts.core.detectors import Candidate

        monkeypatch.setattr(xref, "CANDIDATES_DIR", tmp_path)

        def cand(verse, body):
            return Candidate(
                book="gen",
                chapter=1,
                verse=verse,
                kind="xref-citation",
                anchor="",
                confidence=0.9,
                source_name="TSK",
                source_attribution="TSK. PD.",
                draft_title="Cross-ref",
                draft_label="Cite.",
                draft_body=body,
                detector="CrossRefDetector",
                reviewer_notes="",
            )

        p = xref.write_queue("gen", 1, [cand(1, "A1"), cand(2, "A2")])
        assert json.loads(p.read_text(encoding="utf-8"))["n_candidates"] == 2

        xref.write_queue("gen", 1, [cand(3, "B1")])
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data["n_candidates"] == 3, "write_queue clobbered instead of appending"
        assert [c["draft_body"] for c in data["candidates"]] == ["A1", "A2", "B1"]
        assert len({c["id"] for c in data["candidates"]}) == 3  # ids continue from tail, no collision

    def test_at_scale_base_is_the_single_candidate_json_shape_source(self):
        # mint-7 D1 + mint-10: the candidate-JSON shape has ONE source so it can
        # never drift between drivers. prospect + run_kenyon build the dict
        # directly via the shared candidate_to_dict; the 8 accumulator/kind-replace
        # drivers delegate writes to the shared append_candidates (which itself
        # calls candidate_to_dict) — neither path can fork the shape.
        import importlib

        from scripts.core import at_scale_base

        dict_builders = ["scripts.prospect", "scripts.run_kenyon_at_scale"]
        for name in dict_builders:
            mod = importlib.import_module(name)
            assert mod.candidate_to_dict is at_scale_base.candidate_to_dict, (
                f"{name} has its own candidate_to_dict copy"
            )

        delegators = [
            "scripts.run_greek_at_scale",
            "scripts.run_hebrew_at_scale",
            "scripts.run_naves_at_scale",
            "scripts.run_torrey_at_scale",
            "scripts.run_ethiopian_at_scale",
            "scripts.run_xref_at_scale",
            "scripts.run_ai_xrefs_at_scale",
            "scripts.run_ai_notes_at_scale",
        ]
        for name in delegators:
            mod = importlib.import_module(name)
            assert mod.append_candidates is at_scale_base.append_candidates, (
                f"{name} does not delegate to the shared append_candidates"
            )

    def test_at_scale_base_nt_books_shared_and_canonical(self):
        import scripts.run_greek_at_scale as g
        import scripts.run_hebrew_at_scale as h
        from scripts.core import at_scale_base, config, detectors

        # The Hebrew/Greek detectors + drivers all share the one NT_BOOKS object.
        assert detectors.NT_BOOKS is at_scale_base.NT_BOOKS
        assert h.NT_BOOKS is at_scale_base.NT_BOOKS
        assert g.NT_BOOKS is at_scale_base.NT_BOOKS
        # 27 canonical NT codes, all registered in books.yaml.
        assert len(at_scale_base.NT_BOOKS) == 27
        assert at_scale_base.NT_BOOKS <= set(config.books_by_code().keys())

    def test_at_scale_base_candidate_to_dict_shape(self):
        import types

        from scripts.core.at_scale_base import candidate_to_dict

        c = types.SimpleNamespace(
            book="gen",
            chapter=1,
            verse=1,
            kind="xref-citation",
            anchor="",
            confidence=0.912345,
            source_name="s",
            source_attribution="a",
            draft_title="t",
            draft_label="l",
            draft_body="b",
            detector="d",
            reviewer_notes="r",
        )
        d = candidate_to_dict(c, 3)
        assert d["id"] == "gen-1-1-003"
        assert d["confidence"] == 0.912  # rounded to 3 places
        assert d["status"] == "pending"
        assert set(d.keys()) == {
            "id",
            "verse",
            "kind",
            "anchor",
            "confidence",
            "source_name",
            "source_attribution",
            "draft_title",
            "draft_label",
            "draft_body",
            "detector",
            "reviewer_notes",
            "status",
        }

    def test_run_ai_xrefs_writes_prospect_format(self, tmp_path, monkeypatch):
        cand_dir = tmp_path / "candidates"
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)
        factory = self._stub_detector_factory()
        stats = self.driver.run_ai_xrefs(
            ["jhn"],
            max_verses=3,
            min_confidence=0.7,
            top_n=3,
            model="stub-model",
            detector_factory=factory,
        )
        assert stats["verses_processed"] == 3
        assert stats["candidates_written"] >= 1
        files = sorted(cand_dir.glob("jhn_ch_*.json"))
        assert files
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["book"] == "jhn"
        assert any(c["kind"] == "xref-thematic" for c in data["candidates"])

    def test_run_ai_xrefs_merges_with_existing_chapter_file(
        self,
        tmp_path,
        monkeypatch,
    ):
        # Pre-existing Kenyon candidate must survive the AI driver's
        # merge-not-clobber pass; only kind=xref-thematic gets replaced.
        cand_dir = tmp_path / "candidates"
        cand_dir.mkdir()
        prior = {
            "book": "jhn",
            "chapter": 1,
            "generated_at": "2026-01-01T00:00:00+00:00",
            "n_candidates": 1,
            "candidates": [
                {
                    "id": "jhn-1-1-001",
                    "verse": 1,
                    "kind": "text-witness",
                    "anchor": "",
                    "confidence": 0.55,
                    "source_name": "Kenyon 1895",
                    "source_attribution": "Kenyon PD",
                    "draft_title": "Witness",
                    "draft_label": "MS.",
                    "draft_body": "<strong>x</strong>",
                    "detector": "KenyonReferenceDetector",
                    "reviewer_notes": "",
                    "status": "pending",
                }
            ],
        }
        prior_path = cand_dir / "jhn_ch_001.json"
        prior_path.write_text(json.dumps(prior), encoding="utf-8")
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)

        # Stub the detector so it produces one candidate for jhn 1:1.
        factory = self._stub_detector_factory(
            proposals_per_verse=lambda b, c, v, t: (
                [
                    {
                        "target_book": "isa",
                        "target_chapter": 53,
                        "target_verse": 5,
                        "kind_subclass": "typological",
                        "reasoning": "x",
                        "confidence": 0.85,
                    }
                ]
                if (b, c, v) == ("jhn", 1, 1)
                else []
            ),
        )
        stats = self.driver.run_ai_xrefs(
            ["jhn"],
            max_verses=1,
            min_confidence=0.7,
            top_n=3,
            model="stub",
            detector_factory=factory,
        )
        assert stats["candidates_written"] >= 1

        merged = json.loads(prior_path.read_text(encoding="utf-8"))
        kinds = sorted(c["kind"] for c in merged["candidates"])
        assert "text-witness" in kinds  # prior survives
        assert "xref-thematic" in kinds  # new added
        ids = [c["id"] for c in merged["candidates"]]
        assert len(set(ids)) == len(ids)  # unique IDs

    def test_run_ai_xrefs_replaces_existing_xref_thematic_only(
        self,
        tmp_path,
        monkeypatch,
    ):
        # Re-running the driver must replace existing xref-thematic
        # entries (idempotent), not duplicate them.
        cand_dir = tmp_path / "candidates"
        cand_dir.mkdir()
        monkeypatch.setattr(self.driver, "CANDIDATES_DIR", cand_dir)
        factory = self._stub_detector_factory(
            proposals_per_verse=lambda b, c, v, t: (
                [
                    {
                        "target_book": "isa",
                        "target_chapter": 1,
                        "target_verse": 1,
                        "kind_subclass": "thematic",
                        "reasoning": "x",
                        "confidence": 0.85,
                    }
                ]
                if (b, c, v) == ("jhn", 1, 1)
                else []
            ),
        )

        self.driver.run_ai_xrefs(
            ["jhn"],
            max_verses=1,
            min_confidence=0.7,
            top_n=3,
            model="stub",
            detector_factory=factory,
        )
        first = json.loads((cand_dir / "jhn_ch_001.json").read_text(encoding="utf-8"))
        n_first = sum(1 for c in first["candidates"] if c["kind"] == "xref-thematic")

        self.driver.run_ai_xrefs(
            ["jhn"],
            max_verses=1,
            min_confidence=0.7,
            top_n=3,
            model="stub",
            detector_factory=factory,
        )
        second = json.loads((cand_dir / "jhn_ch_001.json").read_text(encoding="utf-8"))
        n_second = sum(1 for c in second["candidates"] if c["kind"] == "xref-thematic")
        assert n_second == n_first  # not duplicated

    def test_cost_per_verse_constant_pinned(self):
        # round-7 5.9: the dead `estimate_cost()` wrapper was removed (production
        # passes COST_PER_VERSE_USD directly into run_ai_driver_main's cost guard);
        # pin the constant itself — the cost-guard math is `n * COST_PER_VERSE_USD`.
        assert self.driver.COST_PER_VERSE_USD == 0.0023

    def test_resolve_books_default_is_canonical_kjv_intersection(self):
        books = self.asb.resolve_books(None)
        # Must include core books like Genesis and John, in canonical
        # order (Genesis first).
        assert "gen" in books
        assert "jhn" in books
        assert books.index("gen") < books.index("jhn")

    def test_resolve_books_explicit_arg_passes_through(self):
        books = self.asb.resolve_books("rom,gal,heb")
        assert books == ["rom", "gal", "heb"]


# ============================================================
# ω.5 — paths.py: per-user data location resolver. Single source
# of truth for content/ + build-output dirs; in-tree wins for
# dev, user_data_dir for installed binaries.
