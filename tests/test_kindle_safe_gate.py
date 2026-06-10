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
        zf = _zip(_KINDLE_OPF, _HIDE_CSS + _KINDLE_CSS, _PIECE_HIDDEN)
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
