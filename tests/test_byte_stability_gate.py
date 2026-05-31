"""mint-7 E3 — byte-stability gate for the publishable editions.

Nothing else in the suite does a REAL full-edition build (the build-all tests
mock ``build_one``). This gate builds real EPUBs and pins two invariants the
whole project leans on:

  1. each representative edition builds to a valid, non-empty EPUB containing
     scripture, and the editions are mutually DISTINCT (the canon/kind filter
     actually differentiates them);
  2. the flagship rebuilt is byte-STABLE — identical scripture+notes content
     (modulo the per-build generator URN / dcterms:modified), i.e. the build is
     deterministic.

A single edition build is ~2 min, so the whole module is marked ``slow`` and is
deselected by ``-m "not slow"`` (a full all-editions sweep just loops over more
ids — each +~2 min). Determinism is the testable core of "byte-stable": a stored
golden hash would be fragile against the per-build URN; reproducibility is
self-maintaining and catches the regression that actually matters.
"""

from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

# Representative spread of canons: Ethiopian (87) ⊃ Catholic (73) ⊃ Tanakh (39).
_EDITIONS = ["ethiopian-tewahedo", "catholic-study", "jewish-study"]
# Volatile, per-build OPF fields excluded from the content digest.
_URN_RE = re.compile(r"urn:yhwh:edition:[^<\"']+")
_MODIFIED_RE = re.compile(r"<meta[^>]*dcterms:modified[^>]*>[^<]*</meta>")


def _build(ed_id: str, out_dir: Path) -> Path:
    from scripts import build_edition as be
    from scripts.core import config

    out_dir.mkdir(parents=True, exist_ok=True)
    be.build_one(ed_id, out_dir, "v28a-t", config.load_kinds(), dry_run=False)
    epubs = list(out_dir.glob("*.epub"))
    assert len(epubs) == 1, f"{ed_id}: expected exactly 1 EPUB, got {len(epubs)}"
    return epubs[0]


def _content_digest(epub_path: Path) -> str:
    """SHA-256 over every inner file's (name, content), sorted, with the OPF's
    volatile generator URN + dcterms:modified normalized out — so the digest is
    over scripture + notes + structure, not the per-build identifier."""
    h = hashlib.sha256()
    with zipfile.ZipFile(epub_path) as z:
        for name in sorted(z.namelist()):
            data = z.read(name)
            if name.endswith(".opf"):
                text = data.decode("utf-8", "replace")
                text = _URN_RE.sub("urn:yhwh:edition:NORMALIZED", text)
                text = _MODIFIED_RE.sub("", text)
                data = text.encode("utf-8")
            h.update(name.encode("utf-8"))
            h.update(b"\0")
            h.update(data)
    return h.hexdigest()


def test_editions_build_valid_distinct_and_flagship_is_deterministic(tmp_path):
    digests: dict[str, str] = {}
    for ed in _EDITIONS:
        epub = _build(ed, tmp_path / ed)
        assert epub.stat().st_size > 100_000, f"{ed}: EPUB suspiciously small"
        with zipfile.ZipFile(epub) as z:
            names = z.namelist()
            assert "mimetype" in names, f"{ed}: no mimetype entry"
            assert z.read("mimetype") == b"application/epub+zip", f"{ed}: wrong mimetype"
            assert any(n.endswith(".xhtml") for n in names), f"{ed}: no scripture XHTML"
        digests[ed] = _content_digest(epub)

    # The canon/kind filter must actually differentiate the editions.
    assert len(set(digests.values())) == len(_EDITIONS), (
        "editions produced identical content — filter not differentiating"
    )

    # Determinism / byte-stability: a second build of the flagship yields the
    # same normalized content digest.
    flagship = _EDITIONS[1]  # catholic-study
    rebuilt = _build(flagship, tmp_path / f"{flagship}-rebuild")
    assert _content_digest(rebuilt) == digests[flagship], (
        f"{flagship} rebuilt with different content — build is non-deterministic (byte-stability not guaranteed)"
    )
