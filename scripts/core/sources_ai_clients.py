"""
sources_ai_clients.py — Anthropic-backed AI source clients extracted from
the ``sources`` god-module.

The χ-AI-xrefs cross-reference proposer and the χ-AI-notes first-draft note
generator, the cached module-level SDK client they share, the optional
response-cache wrapper, and their singleton accessors. Prompt / model /
schema constants live in ``sources_ai_prompts``; the construction contract
(``SourceMissingError`` when neither SDK+key nor an injected
``completion_fn`` is available) comes from ``sources_base``.

Extracted verbatim from ``sources.py`` (module split 2026-05-26).
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from collections.abc import Callable

from .sources_base import SourceMissingError
from .sources_ai_prompts import (
    AI_NOTE_CACHE_TTL,
    AI_NOTE_OUTPUT_SCHEMA,
    AI_NOTE_SYSTEM_PROMPT,
    AI_XREF_CACHE_TTL,
    AI_XREF_OUTPUT_SCHEMA,
    AI_XREF_SYSTEM_PROMPT,
    DEFAULT_AI_NOTE_MODEL,
    DEFAULT_AI_XREF_MODEL,
)


# ----------------------------------------------------------------------
# Anthropic-backed thematic xref client (Phase χ-AI-xrefs)
# ----------------------------------------------------------------------


def _with_cache(inner: Callable, cache) -> Callable:
    """Wrap a ``completion_fn`` so identical (model, system, user) inputs are
    served from *cache* instead of re-calling the API.

    Opt-in: only applied when an at-scale driver constructs a client with
    ``cache=...``. The cached unit is the model's JSON response — the
    expensive part — keyed by a content hash, so a re-run pays only for
    verses whose text (or the model/prompt) changed. The default
    construction path is byte-identical to before (no cache → no wrap).
    """
    from . import work_cache as _wc

    def wrapped(system_prompt, user_message, *, model):
        key = _wc.key_for(model, system_prompt, user_message)
        hit = cache.get(key)
        if hit is not None:
            return json.loads(hit)
        result = inner(system_prompt, user_message, model=model)
        cache.put(key, json.dumps(result, ensure_ascii=False))
        return result

    return wrapped


class AnthropicXrefClient:
    """LLM-backed proposer for thematic / typological / idiomatic
    cross-references. Phase χ-AI-xrefs (2026-05-08).

    Construction contract mirrors the static-source loaders: raises
    ``SourceMissingError`` when neither a real Anthropic SDK + API key
    nor an injected ``completion_fn`` is available. ``prospect.py``'s
    resilient detector instantiation catches that and skips the
    detector silently — same graceful-degrade contract as
    ``NaveTopical`` when its JSON cache is absent.

    The injected ``completion_fn(system_prompt, user_message, *,
    model)`` returns the parsed completion as a Python dict matching
    the documented shape. Tests pass a stub fn so no real network
    calls are made.

    The default ``completion_fn`` uses the ``anthropic`` SDK with
    prompt caching on the system prompt — repeated per-verse calls
    only pay for the per-verse user message after the first call,
    cutting cost roughly 10×.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_AI_XREF_MODEL,
        completion_fn: Callable | None = None,
        cache=None,
    ) -> None:
        self.model = model
        if completion_fn is not None:
            self._completion_fn = completion_fn
        else:
            # Validate the real-SDK preconditions before locking in the
            # default fn — fail at construction time, not on first call.
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise SourceMissingError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Set it (export ANTHROPIC_API_KEY=...) or pass an "
                    "injected completion_fn."
                )
            try:
                import anthropic  # noqa: F401
            except ImportError as e:
                raise SourceMissingError(
                    "The 'anthropic' Python SDK is not installed. "
                    "Install it (pip install anthropic) or pass an "
                    "injected completion_fn."
                ) from e
            self._completion_fn = self._default_completion_fn

        # Validation set: only book codes the platform actually has are
        # accepted from the model. Built lazily because importing
        # config at module-load time would be heavier than necessary.
        self._valid_book_codes: set[str] | None = None

        # Telemetry from the most recent _default_completion_fn call.
        # Stub completion_fns leave this as None; the real SDK path
        # populates it so the at-scale driver can verify cache hits
        # before paying for a full run. Shape:
        #   {"input_tokens": int, "output_tokens": int,
        #    "cache_creation_input_tokens": int,
        #    "cache_read_input_tokens": int, "request_id": str | None}
        self.last_usage: dict | None = None

        # Opt-in response cache (at-scale --cache). Wrap last so it decorates
        # whichever completion_fn was selected above.
        if cache is not None:
            self._completion_fn = _with_cache(self._completion_fn, cache)

    @property
    def attribution(self) -> str:
        return f"Claude AI ({self.model}, Anthropic, 2026); reviewer-curated."

    def _valid_codes(self) -> set[str]:
        if self._valid_book_codes is None:
            from . import config as _cfg

            self._valid_book_codes = set(_cfg.books_by_code().keys())
        return self._valid_book_codes

    def propose_xrefs(
        self,
        book: str,
        chapter: int,
        verse: int,
        verse_text: str,
        *,
        top_n: int = 3,
    ) -> list[dict]:
        """Ask the model for up to ``top_n`` thematic xref proposals
        for the given verse. Returns a list of dicts with fields
        ``target_book``, ``target_chapter``, ``target_verse``,
        ``kind_subclass``, ``reasoning``, ``confidence``. Defensive
        against malformed model output (returns ``[]``)."""
        user_message = (
            f"Propose up to {top_n} cross-references for:\n"
            f"  Book:    {book}\n"
            f"  Chapter: {chapter}\n"
            f"  Verse:   {verse}\n"
            f"  Text:    {verse_text}\n"
        )
        # Catch only failures we can defensively degrade through —
        # SDK errors (with retry exhausted), JSON-shape failures the
        # schema didn't catch, value coercion errors. Programming
        # errors (TypeError, AttributeError, etc.) propagate so they
        # surface in tests rather than silently producing empty
        # outputs.
        try:
            parsed = self._completion_fn(
                AI_XREF_SYSTEM_PROMPT,
                user_message,
                model=self.model,
            )
        except (json.JSONDecodeError, ValueError, OSError):
            return []
        except Exception as e:
            # Anthropic SDK exceptions are dynamically-named subclasses
            # of APIError; we can't import the SDK at module top
            # without breaking the no-dep test path, so catch by name.
            if type(e).__module__.startswith("anthropic"):
                return []
            raise

        if not isinstance(parsed, dict):
            return []
        proposals = parsed.get("proposals")
        if not isinstance(proposals, list):
            return []

        valid = self._valid_codes()
        out: list[dict] = []
        for p in proposals[:top_n]:
            if not isinstance(p, dict):
                continue
            target_book = p.get("target_book")
            if not isinstance(target_book, str) or target_book not in valid:
                continue
            try:
                # `dict.get()` may return None; the surrounding
                # try/except catches `int(None)` as TypeError. Mypy
                # treats `p.get(...)` as `Any` since `p` is untyped,
                # so no ignore is needed at the callsite.
                target_chapter = int(p.get("target_chapter"))
                target_verse = int(p.get("target_verse"))
            except (TypeError, ValueError):
                continue
            if target_chapter < 1 or target_verse < 1:
                continue
            try:
                confidence = float(p.get("confidence", 0.0))
            except (TypeError, ValueError):
                continue
            # Clamp confidence into [0, 1]
            confidence = max(0.0, min(1.0, confidence))
            kind_subclass = p.get("kind_subclass") or "thematic"
            if kind_subclass not in ("typological", "thematic", "idiomatic"):
                kind_subclass = "thematic"
            reasoning = p.get("reasoning") or ""
            if not isinstance(reasoning, str):
                reasoning = ""
            out.append(
                {
                    "target_book": target_book,
                    "target_chapter": target_chapter,
                    "target_verse": target_verse,
                    "kind_subclass": kind_subclass,
                    "reasoning": reasoning.strip(),
                    "confidence": confidence,
                }
            )
        return out

    def _default_completion_fn(
        self,
        system_prompt: str,
        user_message: str,
        *,
        model: str,
    ) -> dict:
        """Real SDK call. Only reached when the constructor confirmed
        the SDK + API key are available.

        Uses three Anthropic SDK features for cost + correctness:

        - **Prompt caching with 1h TTL** on the system prompt so
          per-verse calls only pay for the user message after the
          first call. The 4096-token-minimum-prefix invariant for
          Haiku 4.5 is satisfied by the padded system prompt above.
        - **Structured output** via ``output_config.format`` with a
          json_schema. The model is forced to return valid JSON of
          the documented shape — no regex-strip-fences hack, no
          json.JSONDecodeError on stray prose.
        - **Cached SDK client** at module level (see
          ``_anthropic_client()`` below) so the 31K-call full pass
          doesn't reconstruct the client per verse.

        Populates ``self.last_usage`` so the at-scale driver can
        verify cache hits and report cost telemetry before
        committing to a long paid run."""
        client = _anthropic_client()
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {
                        "type": "ephemeral",
                        "ttl": AI_XREF_CACHE_TTL,
                    },
                }
            ],
            messages=[{"role": "user", "content": user_message}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": AI_XREF_OUTPUT_SCHEMA,
                },
            },
        )
        # Capture telemetry before parsing so cache-hit info survives
        # even if the JSON parse fails downstream (it shouldn't —
        # the schema enforces shape — but record it regardless).
        usage = response.usage
        self.last_usage = {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
            "cache_creation_input_tokens": getattr(
                usage,
                "cache_creation_input_tokens",
                0,
            ),
            "cache_read_input_tokens": getattr(
                usage,
                "cache_read_input_tokens",
                0,
            ),
            "request_id": getattr(response, "_request_id", None),
        }
        # output_config.format guarantees the first content block is
        # text containing valid JSON matching the schema.
        text = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        )
        return json.loads(text)


@lru_cache(maxsize=1)
def _anthropic_client():
    """Cached Anthropic SDK client. The default constructor reads
    ANTHROPIC_API_KEY from the env, parses platform config, and
    builds an httpx pool — re-running per call (31K calls for the
    full pass) wastes that setup cost. SDK retries (default
    max_retries=2) handle 429 / 5xx automatically.

    Lazy-imported inside the function so module load doesn't fail
    when the SDK isn't installed (the no-API-key code path)."""
    import anthropic

    return anthropic.Anthropic()


@lru_cache(maxsize=1)
def anthropic_xref_client() -> AnthropicXrefClient:
    """Return the singleton AnthropicXrefClient (lazy-loaded once).
    Raises ``SourceMissingError`` if the SDK/API key are unavailable."""
    return AnthropicXrefClient()


# ----------------------------------------------------------------------
# AI-augmented note generator — Phase χ-AI-notes (2026-05-10)
#
# Sibling of AnthropicXrefClient. Same SDK plumbing, same caching
# discipline, same defensive degradation contract. Different prompt
# (proposes new note prose for a verse, not links between verses) and
# different output schema.
#
# See dev/SCOPE_2026-05-09-addendum-ai-notes.md for the full spec.
# ----------------------------------------------------------------------


class AnthropicNoteClient:
    """LLM-backed first-draft note generator. Phase χ-AI-notes (2026-05-10).

    Sibling of :class:`AnthropicXrefClient`. Same construction
    contract: raises :class:`SourceMissingError` when neither a
    real Anthropic SDK + API key nor an injected ``completion_fn``
    is available. ``prospect.py``'s resilient detector
    instantiation catches that and skips the detector silently —
    same graceful-degrade contract as :class:`NaveTopical` when
    its JSON cache is absent.

    The injected ``completion_fn(system_prompt, user_message, *,
    model)`` returns the parsed completion as a Python dict
    matching the documented shape. Tests pass a stub fn so no
    real network calls are made.

    The default ``completion_fn`` uses the ``anthropic`` SDK with
    prompt caching on the system prompt — repeated per-verse calls
    only pay for the per-verse user message after the first call,
    cutting cost roughly 10×. Distinct from
    :class:`AnthropicXrefClient` only in prompt + schema; the
    SDK plumbing, cache TTL, telemetry shape, and exception-
    handling contract are identical.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_AI_NOTE_MODEL,
        completion_fn: Callable | None = None,
        cache=None,
    ) -> None:
        self.model = model
        if completion_fn is not None:
            self._completion_fn = completion_fn
        else:
            # Validate the real-SDK preconditions before locking in the
            # default fn — fail at construction time, not on first call.
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise SourceMissingError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Set it (export ANTHROPIC_API_KEY=...) or pass an "
                    "injected completion_fn."
                )
            try:
                import anthropic  # noqa: F401
            except ImportError as e:
                raise SourceMissingError(
                    "The 'anthropic' Python SDK is not installed. "
                    "Install it (pip install anthropic) or pass an "
                    "injected completion_fn."
                ) from e
            self._completion_fn = self._default_completion_fn

        # Validation set: only book codes the platform actually has are
        # accepted from the model. Built lazily because importing
        # config at module-load time would be heavier than necessary.
        self._valid_book_codes: set[str] | None = None

        # Telemetry from the most recent _default_completion_fn call.
        # Stub completion_fns leave this as None; the real SDK path
        # populates it so the at-scale driver can verify cache hits
        # before paying for a full run. Same shape as
        # AnthropicXrefClient.last_usage.
        self.last_usage: dict | None = None

        # Opt-in response cache (at-scale --cache). Wrap last so it decorates
        # whichever completion_fn was selected above.
        if cache is not None:
            self._completion_fn = _with_cache(self._completion_fn, cache)

    @property
    def attribution(self) -> str:
        return f"Claude AI ({self.model}, Anthropic, 2026); reviewer-curated. AI-generated first draft, edited and approved by a human reviewer before publication."

    def _valid_codes(self) -> set[str]:
        if self._valid_book_codes is None:
            from . import config as _cfg

            self._valid_book_codes = set(_cfg.books_by_code().keys())
        return self._valid_book_codes

    def draft_note(
        self,
        book: str,
        chapter: int,
        verse: int,
        verse_text: str,
        *,
        tradition: str | None = None,
    ) -> dict | None:
        """Ask the model for a first-draft note for the given verse.

        Returns a dict with fields ``kind_class``, ``label``,
        ``body_html``, ``confidence``, ``sources_consulted``,
        ``reviewer_flags`` — OR ``None`` when the model judges the
        verse not to warrant a draft (genealogy, transitional
        narrative, formulaic opening, etc.).

        Defensive against malformed model output: returns ``None``
        on schema violation, parse failure, or SDK error rather
        than raising. Programming errors (TypeError,
        AttributeError) propagate so they surface in tests.

        ``tradition`` is an optional edition-level tradition tag
        (e.g. ``"eastern-orthodox"``) that gets passed into the
        user message so the model can write in that tradition's
        idiom. Defaults to None (general/non-tradition-tagged).
        """
        anchor_line = f"  Book:    {book}\n  Chapter: {chapter}\n  Verse:   {verse}\n  Text:    {verse_text}\n"
        if tradition:
            user_message = f"Draft a first-draft note for the verse below. The edition's tradition tag is '{tradition}' — write in that tradition's idiom and concerns where appropriate.\n\n{anchor_line}"
        else:
            user_message = f"Draft a first-draft note for the verse below.\n\n{anchor_line}"

        # Catch only failures we can defensively degrade through —
        # SDK errors (with retry exhausted), JSON-shape failures the
        # schema didn't catch, value coercion errors. Programming
        # errors (TypeError, AttributeError, etc.) propagate so they
        # surface in tests rather than silently producing empty
        # outputs. Identical contract to AnthropicXrefClient.
        try:
            parsed = self._completion_fn(
                AI_NOTE_SYSTEM_PROMPT,
                user_message,
                model=self.model,
            )
        except (json.JSONDecodeError, ValueError, OSError):
            return None
        except Exception as e:
            if type(e).__module__.startswith("anthropic"):
                return None
            raise

        if not isinstance(parsed, dict):
            return None

        # Verify the verse_anchor matches what we asked for. A model
        # that returns a draft for a different verse is misbehaving;
        # drop the draft rather than write it under the wrong anchor.
        anchor = parsed.get("verse_anchor")
        if not isinstance(anchor, dict):
            return None
        if anchor.get("book") != book:
            return None
        try:
            if int(anchor.get("chapter", 0)) != chapter:
                return None
            if int(anchor.get("verse", 0)) != verse:
                return None
        except (TypeError, ValueError):
            return None

        note = parsed.get("note")
        if note is None:
            return None
        if not isinstance(note, dict):
            return None

        kind_class = note.get("kind_class")
        if kind_class not in ("explanatory", "study", "translation"):
            return None

        label = note.get("label")
        if not isinstance(label, str) or not label.strip():
            return None

        body_html = note.get("body_html")
        if not isinstance(body_html, str) or not body_html.strip():
            return None

        try:
            confidence = float(note.get("confidence", 0.0))
        except (TypeError, ValueError):
            return None
        # Clamp confidence into [0, 1]
        confidence = max(0.0, min(1.0, confidence))

        sources_consulted = note.get("sources_consulted") or []
        if not isinstance(sources_consulted, list):
            sources_consulted = []
        sources_consulted = [s for s in sources_consulted if isinstance(s, str)]

        reviewer_flags = note.get("reviewer_flags") or []
        if not isinstance(reviewer_flags, list):
            reviewer_flags = []
        reviewer_flags = [s for s in reviewer_flags if isinstance(s, str)]

        return {
            "kind_class": kind_class,
            "label": label.strip(),
            "body_html": body_html.strip(),
            "confidence": confidence,
            "sources_consulted": sources_consulted,
            "reviewer_flags": reviewer_flags,
        }

    def _default_completion_fn(
        self,
        system_prompt: str,
        user_message: str,
        *,
        model: str,
    ) -> dict:
        """Real SDK call. Only reached when the constructor confirmed
        the SDK + API key are available.

        Mirrors :meth:`AnthropicXrefClient._default_completion_fn`:

        - **Prompt caching with 1h TTL** on the system prompt so
          per-verse calls only pay for the user message after the
          first call. The 4096-token-minimum-prefix invariant for
          Haiku 4.5 is satisfied by the padded system prompt above.
        - **Structured output** via ``output_config.format`` with a
          json_schema. The model is forced to return valid JSON of
          the documented shape — no regex-strip-fences hack, no
          json.JSONDecodeError on stray prose.
        - **Cached SDK client** at module level (see
          ``_anthropic_client()``).

        Populates ``self.last_usage`` so the at-scale driver can
        verify cache hits and report cost telemetry before
        committing to a long paid run."""
        client = _anthropic_client()
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {
                        "type": "ephemeral",
                        "ttl": AI_NOTE_CACHE_TTL,
                    },
                }
            ],
            messages=[{"role": "user", "content": user_message}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": AI_NOTE_OUTPUT_SCHEMA,
                },
            },
        )
        # Capture telemetry before parsing so cache-hit info survives
        # even if the JSON parse fails downstream.
        usage = response.usage
        self.last_usage = {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
            "cache_creation_input_tokens": getattr(
                usage,
                "cache_creation_input_tokens",
                0,
            ),
            "cache_read_input_tokens": getattr(
                usage,
                "cache_read_input_tokens",
                0,
            ),
            "request_id": getattr(response, "_request_id", None),
        }
        text = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        )
        return json.loads(text)


@lru_cache(maxsize=1)
def anthropic_note_client() -> AnthropicNoteClient:
    """Return the singleton AnthropicNoteClient (lazy-loaded once).
    Raises ``SourceMissingError`` if the SDK/API key are unavailable."""
    return AnthropicNoteClient()
