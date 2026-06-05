"""Defects #2 + #4 of the auto-note re-ingest: lang-greek θεός (G2316) head-drop +
φῶς (G5457) etymology-leak. See ``docs/superpowers/notes/2026-06-06-auto-note-reingest-plan.md`` §2/§4.

The first tests pin the curated ``_GREEK_DEF_OVERRIDES`` fix in the lexicon loader
(pass as soon as the override is in place). The last ones are full-population store
invariants (pass after ``scripts/_reingest_greek_glosses.py --write`` has rewritten
the existing notes) plus the lint guard."""

from __future__ import annotations

import ast
from pathlib import Path

from scripts.core.detectors import GreekWordDetector
from scripts.core.sources_lexicon import _GREEK_DEF_OVERRIDES, StrongsGreek
from scripts.lint_rules import check_greek_gloss_quality

REPO = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO / "content" / "notes"


def _store_lang_greek() -> list[tuple[str, int, int, str, str]]:
    out: list[tuple[str, int, int, str, str]] = []
    for p in sorted(NOTES_DIR.glob("*.py")):
        if p.name == "__init__.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "NOTES" for t in node.targets):
                for t in ast.literal_eval(node.value):
                    if len(t) >= 8 and t[4] == "lang-greek":
                        out.append((p.stem, t[0], t[1], t[2], t[7]))
    return out


def _gloss(body: str) -> str:
    return body.split("</strong>", 1)[1].strip() if "</strong>" in body else body


# --- loader-level (the curated override) -----------------------------------------


def test_override_restores_theos_primary_sense():
    entry = StrongsGreek().get("G2316")
    assert entry is not None
    # the "supreme Divinity" head is back, the figurative tail still present
    assert entry.definition == _GREEK_DEF_OVERRIDES["G2316"]
    assert entry.definition.startswith("a deity, especially the supreme Divinity")
    assert "figuratively, a magistrate" in entry.definition


def test_override_strips_phos_etymology_leak():
    entry = StrongsGreek().get("G5457")
    assert entry is not None
    assert entry.definition == _GREEK_DEF_OVERRIDES["G5457"]
    assert entry.definition.startswith("luminousness (")
    assert "compare G5316" not in entry.definition
    assert entry.definition.count("(") == entry.definition.count(")")  # parens balanced


def test_detector_body_theos_carries_the_god_sense():
    entry = StrongsGreek().get("G2316")
    body = GreekWordDetector._format_body("", entry, "")
    assert (
        body
        == "<strong>Theós (<em>θεός</em>).</strong> a deity, especially the supreme Divinity; figuratively, a magistrate; by Hebraism, very."
    )
    assert not _gloss(body).startswith("figuratively,")


# --- full-population store invariants (pass after _reingest_greek_glosses.py --write) ---


def test_no_lang_greek_head_drop_or_paren_imbalance():
    offenders = []
    for c, ch, v, s, body in _store_lang_greek():
        g = _gloss(body)
        if g.startswith(("figuratively,", "compare ")) or g.count("(") != g.count(")"):
            offenders.append(f"{c} {ch}:{v}{s}")
    assert not offenders, f"{len(offenders)} lang-greek glosses still malformed, e.g. {offenders[:5]}"


def test_every_theos_note_has_the_supreme_divinity_sense():
    theos = [(c, ch, v, s, b) for c, ch, v, s, b in _store_lang_greek() if "(<em>θεός</em>)" in b]
    assert theos, "no θεός notes found in store"
    bad = [f"{c} {ch}:{v}{s}" for c, ch, v, s, b in theos if "a deity, especially the supreme Divinity" not in b]
    assert not bad, f"{len(bad)} θεός notes missing the primary sense, e.g. {bad[:5]}"


def test_every_phos_note_has_no_etymology_leak():
    phos = [(c, ch, v, s, b) for c, ch, v, s, b in _store_lang_greek() if "(<em>φῶς</em>)" in b]
    assert phos, "no φῶς notes found in store"
    bad = [f"{c} {ch}:{v}{s}" for c, ch, v, s, b in phos if "compare G5316" in b or "luminousness" not in b]
    assert not bad, f"{len(bad)} φῶς notes still leak the etymology, e.g. {bad[:5]}"


def test_lint_guard_passes():
    result = check_greek_gloss_quality()
    assert result["status"] == "pass", result["message"]
