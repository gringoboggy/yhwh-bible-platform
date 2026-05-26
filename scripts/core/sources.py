"""
sources.py — Loaders for the public-domain reference corpora cached
under ``content/sources/`` by ``scripts/fetch_sources.py``.

Each source class loads lazily (first call) and caches in memory. The
public API is read-only; ``fetch_sources.py`` is the only writer.

Public API:
    StrongsHebrew()         — entries keyed by H-number
    StrongsGreek()          — entries keyed by G-number  (Phase χ.1)
    Tsk()                   — cross-refs keyed by (book, chapter, verse)
    NavesTopical()          — topical-concordance hits, both directions
                              (Phase χ.7)
    KenyonText()            — PD textual-criticism prose (Phase χ.0)
    AnthropicXrefClient()   — LLM-backed xref proposer (Phase χ-AI-xrefs)
"""

from __future__ import annotations

# This module was split into focused sub-modules (god-module split
# 2026-05-26). Every public name is re-exported here (noqa: F401) so
# existing call sites keep working unchanged — both
# ``from scripts.core import sources; sources.X`` and
# ``from scripts.core.sources import X``. The underscore names re-
# exported below (_normalize_book_code, _BOOK_CODE_ALIASES,
# _sources_dir, _anthropic_client, ...) are imported externally too.
from .sources_base import (  # noqa: F401
    SourceMissingError,
    _BOOK_CODE_ALIASES,
    _REPO_ROOT,
    _SOURCES,
    _normalize_book_code,
    _sources_dir,
)
from .sources_lexicon import (  # noqa: F401
    KENYON_BOOK_NAME_TO_CODE,
    KenyonReference,
    KenyonText,
    NaveTopicHit,
    NavesTopical,
    StrongsEntry,
    StrongsGreek,
    StrongsGreekEntry,
    StrongsHebrew,
    TorreyTopicHit,
    TorreyTopical,
    Tsk,
    TskCrossRef,
    kenyon_text,
    naves_topical,
    strongs_greek,
    strongs_hebrew,
    torrey_topical,
    tsk,
)
from .sources_commentary import (  # noqa: F401
    CatholicCommentaries,
    CatholicCommentary,
    EthiopianCommentaries,
    EthiopianCommentary,
    PatristicCommentaries,
    PatristicCommentary,
    ProtestantCommentaries,
    ProtestantCommentary,
    RabbinicCommentaries,
    RabbinicCommentary,
    ReformationCommentaries,
    ReformationCommentary,
    catholic_commentaries,
    ethiopian_commentaries,
    patristic_commentaries,
    protestant_commentaries,
    rabbinic_commentaries,
    reformation_commentaries,
)
from .sources_ai_prompts import (  # noqa: F401
    AI_NOTE_CACHE_TTL,
    AI_NOTE_OUTPUT_SCHEMA,
    AI_NOTE_SYSTEM_PROMPT,
    AI_XREF_CACHE_TTL,
    AI_XREF_OUTPUT_SCHEMA,
    AI_XREF_SYSTEM_PROMPT,
    DEFAULT_AI_NOTE_MODEL,
    DEFAULT_AI_XREF_MODEL,
)
from .sources_ai_clients import (  # noqa: F401
    AnthropicNoteClient,
    AnthropicXrefClient,
    _anthropic_client,
    _with_cache,
    anthropic_note_client,
    anthropic_xref_client,
)
