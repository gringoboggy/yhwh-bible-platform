"""Regression tests for dev/audit_popup_formula.py (the wired reader_sim Kobo gate).

Round-13 audit finding #7 + a latent root-cause: the gate's generic attribute
parser could not read the ``epub:`` namespace prefix, so ``_aside_index`` skipped
EVERY ``<aside epub:type="footnote">`` -> the aside index was always empty -> the
gate flooded NO_ASIDE on every same-file popup and could never reach the
LONG_TARGET / CROSS_FILE / BACKWARD / NO_BACKLINK checks. On top of that it
flagged the K-R9c study-glossary backmatter cascade (cross-file ``study-glossary-jump``
navigate badges + oversized ``study-glossary-cat`` navigate targets) as defects,
even though that layout is BY DESIGN. These tests pin the fix and mirror the
device-proven floors used by the authoritative gate dev/verify_kr2_build.py
(POP_FLOOR 4,498 / GLOSSARY_DECLINE_HI 7,748).
"""

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("audit_popup_formula", REPO / "dev" / "audit_popup_formula.py")
apf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(apf)


def _body(n_words: int) -> str:
    # "lorem " -> 6 chars; _strip_len collapses whitespace + drops the trailing
    # space, so stripped length is 6*n - 1 (deterministic, lets us straddle floors).
    return "lorem " * n_words


def _aside(aid: str, cls: str, ref_id: str, body: str) -> str:
    return (
        f'<aside epub:type="footnote" class="{cls}" id="{aid}">'
        f'<a epub:type="backlink" href="#{ref_id}">↩</a> {body}</aside>'
    )


def _ref(cls: str, rid: str, href: str) -> str:
    return f'<a class="{cls}" epub:type="noteref" id="{rid}" href="{href}">*</a>'


def test_aside_index_parses_epub_type_footnote():
    """Root-cause guard: the aside index must populate for namespaced epub:type."""
    piece = _ref("vn-link", "r1", "#a1") + _aside("a1", "vnote", "r1", _body(5))
    idx = apf._aside_index({"index_split_001.html": piece})
    assert "a1" in idx, "aside index empty -> _attrs cannot read epub:type (the latent bug)"


def test_backmatter_design_produces_no_violations():
    """The K-R9c study-glossary backmatter cascade is BY DESIGN -> zero violations.

    Exercises: a small same-file popup (OK), a cross-file study-glossary-jump
    badge (exempt), an oversized vnote translation aside (honest WARN, not a
    fail), and a study-glossary-cat navigate target under the 7,748 ceiling (OK).
    """
    prose = (
        _ref("vn-link", "vnlink-1", "#vnote-1")
        + _aside("vnote-1", "vnote", "vnlink-1", _body(5))
        + _ref("study-glossary-jump badge-cat-comm", "vbadge-2", "index_split_099.html#sg-2")
        + _ref("vn-link", "vnlink-3", "#vnote-3")
        + _aside("vnote-3", "vnote", "vnlink-3", _body(1034))  # ~6,203 stripped: > pop floor
    )
    glossary = (
        '<div class="study-glossary-entry" id="e-2">'
        + _aside("sg-2", "study-glossary-cat verse-notes", "vbadge-2", _body(1000))  # ~5,999 < 7,748
        + "</div>"
    )
    res = apf.audit({"index_split_005.html": prose, "index_split_099.html": glossary})
    assert res["violations"] == [], res["violations"]
    assert any("vnote-3" in w for w in res["warns"]), res["warns"]


def test_genuine_defects_still_flagged():
    """Real defects must still surface after the by-design exemptions are added."""
    prose = (
        _ref("note-ref", "nr-1", "other.xhtml#x-1")  # genuine PROMOTED (non-jump cross-file)
        + _ref("verse-notes-badge", "vbadge-4", "#vnotes-4")
        + _aside("vnotes-4", "verse-notes", "vbadge-4", _body(870))  # ~5,219 > pop floor -> LONG_TARGET
        + _ref("vn-link", "vnlink-5", "#missing-5")  # unresolved target
    )
    glossary = _aside(
        "sg-9",
        "study-glossary-cat verse-notes",
        "vbadge-9",
        _body(1400),  # ~8,399 > 7,748
    )
    res = apf.audit({"index_split_005.html": prose, "index_split_099.html": glossary})
    v = "\n".join(res["violations"])
    assert "PROMOTED" in v and "nr-1" in v, v
    assert "LONG_TARGET" in v and "vnotes-4" in v, v
    assert "LONG_GLOSSARY" in v and "sg-9" in v, v
    assert "UNRESOLVED" in v and "vnlink-5" in v, v
    # the by-design jump/glossary classes must NOT appear as violations
    assert "study-glossary-jump" not in v


def test_exit_code_zero_when_only_warns():
    prose = _ref("vn-link", "r1", "#a1") + _aside("a1", "vnote", "r1", _body(1034))
    res = apf.audit({"index_split_001.html": prose})
    assert res["violations"] == []
    assert res["warns"]
