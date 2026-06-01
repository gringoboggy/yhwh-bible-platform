"""mint-9 (deep-audit round 2) Phase-4 guards — concurrency & low-sev correctness.

#10 notes_io._invalidate_corpus_index_if_notes_file now also clears the
    compute_matrix singleton (was leaving the matrix grid stale after an
    editor save until process restart).
#37 inject.build_aside now HTML-escapes the note label + category title (body
    was already sanitized). Byte-identical on the current corpus (0/91,733
    labels contain <>&); prevents a future RSC-005 from an & in a label.
#36 the LXX-Swete + Byzantine-NT extractors enforce the trusted-html
    no-markup precondition at ingest (raise on <>& in a verse) — the trust
    that lets popup_versions render them raw is now checked, not just claimed.
#35 api_sources url_override is validated against the PD-sources allowlist at
    request time (defense-in-depth), failing closed with ssrf_blocked.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# #37 — label / category-title HTML escaping in build_aside
# ---------------------------------------------------------------------------


def test_build_aside_escapes_label() -> None:
    from scripts.inject import build_aside

    out = build_aside("comm-test", "tt0101a", "<script>&amp;", "<b>body</b>")
    # The raw "<script>" label must NOT appear unescaped in the note-label span.
    assert '<span class="note-label"><script>' not in out
    assert "&lt;script&gt;" in out


def test_build_aside_plain_label_unchanged_bytes() -> None:
    """A plain ASCII label (every shipped label) is byte-identical pre/post
    escaping — html.escape is a no-op on clean text."""
    from scripts.inject import build_aside

    out = build_aside("comm-test", "tt0101a", "Origen", "a note body")
    assert '<span class="note-label">Origen</span>' in out


# ---------------------------------------------------------------------------
# #36 — trusted-html ingest enforcement
# ---------------------------------------------------------------------------


def test_lxx_extractor_rejects_markup_in_trusted_verse(tmp_path) -> None:
    from scripts import extract_lxx_swete

    with pytest.raises(ValueError, match="HTML-special"):
        extract_lxx_swete.write_translation({"gen": [(1, 1, "Ἐν ἀρχῇ <b>x</b>")]}, tmp_path, 1)


def test_lxx_extractor_accepts_clean_greek(tmp_path) -> None:
    from scripts import extract_lxx_swete

    # Clean accented Greek (no <>&) writes without raising.
    extract_lxx_swete.write_translation({"gen": [(1, 1, "Ἐν ἀρχῇ ἐποίησεν")]}, tmp_path, 1)
    assert (tmp_path / "gen.py").is_file()


def test_byzantine_extractor_rejects_markup(tmp_path) -> None:
    from scripts import extract_byzantine_nt

    with pytest.raises(ValueError, match="HTML-special"):
        extract_byzantine_nt.write_translation({"mat": [(1, 1, "Βίβλος & γενέσεως")]}, tmp_path, 1)


# ---------------------------------------------------------------------------
# #35 — url_override allowlist defense-in-depth
# ---------------------------------------------------------------------------


def test_url_override_off_allowlist_blocked() -> None:
    from scripts.api import sources as api_sources
    from scripts.core.fetcher_config import KNOWN_PARSERS, load_fetcher_config

    try:
        cfg = load_fetcher_config()
    except Exception:
        pytest.skip("fetcher config unavailable")
    src = cfg.sources[0] if getattr(cfg, "sources", None) else None
    if src is None:
        pytest.skip("no configured sources to exercise the override path")

    parser = src.candidates[0].parser if src.candidates else next(iter(KNOWN_PARSERS))
    result = api_sources.api_sources_cache_fetch(
        src.id,
        url_override="https://evil.example.com/payload",
        parser_override=parser,
        fetch_fn=lambda *a, **k: (_ for _ in ()).throw(AssertionError("fetch_fn must not be reached")),
    )
    assert result.get("status") == "error"
    assert result.get("code") == "ssrf_blocked", result


# ---------------------------------------------------------------------------
# #10 — compute_matrix invalidated on notes-file write
# ---------------------------------------------------------------------------


def test_notes_write_clears_compute_matrix_cache(tmp_path, monkeypatch) -> None:
    from scripts.core import matrix as _matrix
    from scripts.core import notes_io

    called = {"n": 0}
    monkeypatch.setattr(_matrix.compute_matrix, "cache_clear", lambda: called.__setitem__("n", called["n"] + 1))
    # Simulate a write to a content/notes/*.py path.
    fake = tmp_path / "notes" / "gen.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("NOTES = []\n", encoding="utf-8")
    # The discriminator checks parent.name == "notes".
    notes_io._invalidate_corpus_index_if_notes_file(fake)
    assert called["n"] >= 1, "compute_matrix.cache_clear must be called on a notes-file write"


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-q"]))
