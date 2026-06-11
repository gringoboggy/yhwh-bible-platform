"""Fires-on-defect proof for the kindle_safe artifact gate (gate 5).

Synthetic minimal zips — the gate function is called directly so the other
gates' artifact requirements (pieces, nav, colophon) don't confound the test.
The gate judges ONLY artifacts whose OPF carries the yhwh:target-reader=kindle
stamp (no-reassert-ratified-bar: non-kindle artifacts are never held to the
kindle bar).
"""

import importlib.util
import io
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("verify_kr2_build", REPO / "dev" / "verify_kr2_build.py")
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_KINDLE_OPF = (
    "<package><metadata><dc:language>en-US</dc:language>\n"
    '<meta name="yhwh:target-reader" content="kindle"/>\n'
    "</metadata></package>"
)
_PLAIN_OPF = "<package><metadata><dc:language>en-US</dc:language>\n</metadata></package>"

_HIDE_CSS = ".notes-section, .notes-rule { display: none; }\n.verse-refs-section { display: none; }\n"
_KINDLE_CSS = (
    "/* === kindle_safe (target_reader=kindle) — Send-to-Kindle variant === */\n"
    ".notes-section { display: block; }\n.verse-refs-section { display: block; }\n"
)

_BIG = "x" * 11000
_PIECE_HIDDEN = (
    "<html><body><p>scripture</p>"
    f'<aside class="notes-section" epub:type="footnotes" hidden="">{_BIG}</aside>'
    "</body></html>"
)
# the post-forensics good shape: the kindle variant also STRIPS hidden=""
_PIECE_UNHIDDEN = (
    f'<html><body><p>scripture</p><aside class="notes-section" epub:type="footnotes">{_BIG}</aside></body></html>'
)


def _zip(opf: str, css: str, piece: str) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("content.opf", opf)
        z.writestr("stylesheet.css", css)
        z.writestr("index_split_000.html", piece)
    return zipfile.ZipFile(io.BytesIO(buf.getvalue()))


class TestKindleSafeGate:
    def test_fires_on_hidden_volume_over_10k(self):
        zf = _zip(_KINDLE_OPF, _HIDE_CSS, _PIECE_HIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert any("display:none" in f for f in fails), fails

    def test_green_when_kindle_css_overrides_the_hides(self):
        zf = _zip(_KINDLE_OPF, _HIDE_CSS + _KINDLE_CSS, _PIECE_UNHIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert fails == [], fails

    def test_skips_entirely_without_the_kindle_stamp(self):
        # >10K hidden + no stamp ⇒ not a kindle artifact ⇒ no kindle judgment
        zf = _zip(_PLAIN_OPF, _HIDE_CSS, _PIECE_HIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert fails == []

    def test_fires_on_multi_dc_language(self):
        opf = _KINDLE_OPF.replace(
            "<dc:language>en-US</dc:language>",
            "<dc:language>en-US</dc:language><dc:language>gez</dc:language>",
        )
        zf = _zip(opf, _HIDE_CSS + _KINDLE_CSS, _PIECE_HIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert any("dc:language" in f for f in fails), fails

    def test_fires_when_kindle_css_marker_absent(self):
        # stamp says kindle but the variant CSS never got appended — fail fast
        # with the clear message even if the volume math were somehow green
        zf = _zip(_KINDLE_OPF, _HIDE_CSS, "<html><body><p>s</p></body></html>")
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert any("kindle_safe CSS" in f for f in fails), fails

    def test_fires_on_residual_hidden_attr(self):
        # K-KIN forensics (2026-06-11): the variant must physically strip
        # hidden="" from footnote wrappers — Amazon's hidden-text counter may
        # not honor the author-CSS-over-[hidden] cascade, so a kindle artifact
        # carrying ANY hidden="" footnote wrapper is a stale/unsafe build.
        zf = _zip(_KINDLE_OPF, _HIDE_CSS + _KINDLE_CSS, _PIECE_HIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert any("hidden=" in f for f in fails), fails

    def test_hidden_attr_ok_without_kindle_stamp(self):
        zf = _zip(_PLAIN_OPF, _HIDE_CSS, _PIECE_HIDDEN)
        fails = _mod.kindle_safe_checks(zf, zf.namelist(), zf.read("content.opf").decode())
        assert fails == []


# ── gate 4k — demoted-appendix husk pieces ──────────────────────────────
_HUSK_PIECE = '<html><body><div class="appendix-section" id="bp-45"><h1>The Prayer of Azariah</h1></div></body></html>'
_MERGED_PIECE = (
    "<html><body>"
    '<div class="appendix-section" id="bp-45"><h1>The Prayer of Azariah</h1></div>'
    '<p class="verse-p">And they walked in the midst of the fire.</p>'
    "</body></html>"
)
_TITLE_SINGLETON = '<html><body><div class="book-title-page" id="bp-07"><h1>Ruth</h1></div></body></html>'


class TestHuskPieceGate4k:
    """4k fires on a frame-only appendix-section piece (the Kindle E24010/E24001
    TOC-husk class) and stays green for merged frames and real title singletons."""

    def test_fires_on_frame_only_appendix_piece(self):
        zf = _zip(_PLAIN_OPF, "", _HUSK_PIECE)
        fails = _mod.husk_piece_checks(zf, zf.namelist())
        assert any("bp-45" in f and "4k" in f for f in fails), fails

    def test_green_when_frame_flows_with_content(self):
        zf = _zip(_PLAIN_OPF, "", _MERGED_PIECE)
        assert _mod.husk_piece_checks(zf, zf.namelist()) == []

    def test_real_title_singleton_is_exempt(self):
        # 38 real book-title singletons ship in every artifact; Kindle accepts
        # them — only the demoted-frame husk is the refused class.
        zf = _zip(_PLAIN_OPF, "", _TITLE_SINGLETON)
        assert _mod.husk_piece_checks(zf, zf.namelist()) == []


# ── gate 4l — TOC refs must not target a demoted appendix frame ─────────
_FRAME_PIECE = (
    "<html><body>"
    '<div class="appendix-section" id="bp-45"><h1>The Prayer of Azariah</h1></div>'
    '<a id="ch-b45-c1" class="ch-anchor"></a>'
    '<p class="verse-p">And they walked in the midst of the fire.</p>'
    "</body></html>"
)


def _zip_with_nav(nav: str) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("content.opf", _PLAIN_OPF)
        z.writestr("index_split_047_02.html", _FRAME_PIECE)
        z.writestr("nav.xhtml", nav)
    return zipfile.ZipFile(io.BytesIO(buf.getvalue()))


class TestDemotedTocTargetGate4l:
    """4l fires when any TOC surface targets a demoted frame id (KFX refuses
    the frame div even merged mid-content) and stays green when the entry
    points at the book's first content anchor."""

    def test_fires_on_toc_ref_to_frame_id(self):
        zf = _zip_with_nav(
            '<html xmlns:epub="http://www.idpf.org/2007/ops"><body><nav epub:type="toc"><ol>'
            '<li><a href="index_split_047_02.html#bp-45">Azariah</a></li>'
            "</ol></nav></body></html>"
        )
        fails = _mod.demoted_toc_target_checks(zf, zf.namelist())
        assert any("bp-45" in f and "4l" in f for f in fails), fails

    def test_green_when_toc_targets_content_anchor(self):
        zf = _zip_with_nav(
            '<html xmlns:epub="http://www.idpf.org/2007/ops"><body><nav epub:type="toc"><ol>'
            '<li><a href="index_split_047_02.html#ch-b45-c1">Azariah</a></li>'
            "</ol></nav></body></html>"
        )
        assert _mod.demoted_toc_target_checks(zf, zf.namelist()) == []

    def test_silent_without_any_demoted_frame(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("content.opf", _PLAIN_OPF)
            z.writestr(
                "nav.xhtml",
                '<html xmlns:epub="http://www.idpf.org/2007/ops"><body><nav epub:type="toc"><ol>'
                '<li><a href="d.html#bp-07">Ruth</a></li></ol></nav></body></html>',
            )
        zf = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
        assert _mod.demoted_toc_target_checks(zf, zf.namelist()) == []
