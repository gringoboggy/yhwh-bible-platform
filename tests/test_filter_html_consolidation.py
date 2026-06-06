"""round-5 audit Phase 4 (LOW) — prove the consolidated kind-filter is byte-identical.

``filter_html`` used to strip disabled-kind markers + asides with a per-kind loop
(~2 regex compiles + 2 full-text scans PER disabled kind). It now strips them with
ONE marker alternation + ONE aside alternation over all disabled kinds (2 scans per
file), pre-built once per edition by ``build_one`` and threaded into every
``filter_html`` call. The consolidation is safe because every ``note-ref`` / ``note``
element carries exactly one ``note-{kind}`` class (mutually exclusive) and markers
never nest, so the element SET removed — and the ``markers`` / ``asides`` totals —
are independent of whether the deletions are batched.

These tests pin that equivalence against an inline reproduction of the OLD per-kind
loop, run over REAL base HTML (``epub_working``), for three disabled-kind sets and
for BOTH code paths (the in-function fallback build and the pre-built kwargs that
``build_one`` passes). Fast — one file + regex, no full build.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _reference_kind_filter(text: str, disabled_kinds: set) -> tuple[str, dict]:
    """The historical per-kind loop, reproduced verbatim — the ground truth the
    consolidated path must match byte-for-byte."""
    counts = {"markers": 0, "asides": 0}
    for kind in disabled_kinds:
        marker_re = re.compile(rf'<a class="note-ref note-{re.escape(kind)}"[^>]*>.*?</a>', re.DOTALL)
        text, n = marker_re.subn("", text)
        counts["markers"] += n
        aside_re = re.compile(rf'<aside class="note note-{re.escape(kind)}"[^>]*>.*?</aside>', re.DOTALL)
        text, n = aside_re.subn("", text)
        counts["asides"] += n
    return text, counts


def _gen1_base_html() -> str:
    """The real gen ch1 split file (the canonical numbers base) — dense with
    note-ref markers across many kinds, so the alternation has real alternatives."""
    book = config.get_book("gen")
    epub = REPO / "epub_working"
    for fname in book["files"]:
        t = (epub / fname).read_text(encoding="utf-8")
        if 'id="v-gen-1-1"' in t:
            return t
    raise AssertionError("gen 1 base file not found")


def _present_kinds(text: str) -> list[str]:
    return sorted(set(re.findall(r'<a class="note-ref note-([a-z0-9-]+)"', text)))


def _kind_sets(text: str):
    """A spread of disabled-kind sets: a single kind, all-but-one, and every kind
    present — each must consolidate identically."""
    present = _present_kinds(text)
    assert len(present) >= 2, f"need ≥2 note kinds in the base for a meaningful test; got {present}"
    return [
        {present[0]},
        set(present[:-1]),
        set(present),
    ]


class TestFilterHtmlKindConsolidation:
    def test_in_function_build_matches_per_kind_loop(self):
        from scripts.build_edition import filter_html

        text = _gen1_base_html()
        for disabled in _kind_sets(text):
            ref_text, ref_counts = _reference_kind_filter(text, disabled)
            # No kwargs → filter_html builds the combined regexes itself.
            out_text, out_counts = filter_html(text, disabled)
            assert out_text == ref_text, f"consolidated output diverged for kinds={sorted(disabled)}"
            assert out_counts["markers"] == ref_counts["markers"], sorted(disabled)
            assert out_counts["asides"] == ref_counts["asides"], sorted(disabled)

    def test_prebuilt_kwargs_match_per_kind_loop(self):
        # The path build_one actually uses: pre-build the pair once, pass it in.
        from scripts.build_edition import filter_html, _build_disabled_kind_res

        text = _gen1_base_html()
        for disabled in _kind_sets(text):
            ref_text, ref_counts = _reference_kind_filter(text, disabled)
            mre, are = _build_disabled_kind_res(disabled)
            out_text, out_counts = filter_html(text, disabled, kind_marker_re=mre, kind_aside_re=are)
            assert out_text == ref_text, f"prebuilt-kwarg output diverged for kinds={sorted(disabled)}"
            assert out_counts["markers"] == ref_counts["markers"], sorted(disabled)
            assert out_counts["asides"] == ref_counts["asides"], sorted(disabled)

    def test_empty_disabled_kinds_is_a_noop(self):
        from scripts.build_edition import filter_html, _build_disabled_kind_res

        text = _gen1_base_html()
        # Empty set → no kind regexes, text unchanged, zero counts.
        assert _build_disabled_kind_res(set()) == (None, None)
        out_text, out_counts = filter_html(text, set())
        assert out_text == text
        assert out_counts["markers"] == 0 and out_counts["asides"] == 0

    def test_prefix_kind_names_do_not_cross_match(self):
        # A kind whose name prefixes another (e.g. xref vs xref-foo) must only
        # remove its own markers — the trailing '"' after the alternation group
        # guarantees it. Synthetic fixture with both forms present.
        from scripts.build_edition import filter_html

        html = (
            "<p>"
            '<a class="note-ref note-xref" id="ref-a">x</a>'
            '<a class="note-ref note-xref-foo" id="ref-b">y</a>'
            "</p>"
            '<aside class="note note-xref" id="note-a">A</aside>'
            '<aside class="note note-xref-foo" id="note-b">B</aside>'
        )
        # Disable only "xref": the "xref-foo" marker + aside must survive.
        out, counts = filter_html(html, {"xref"})
        assert 'id="ref-a"' not in out and 'id="note-a"' not in out, "xref not removed"
        assert 'id="ref-b"' in out and 'id="note-b"' in out, "xref-foo wrongly removed by xref"
        assert counts["markers"] == 1 and counts["asides"] == 1
        # And it matches the per-kind reference exactly.
        ref_text, ref_counts = _reference_kind_filter(html, {"xref"})
        assert out == ref_text
        assert counts["markers"] == ref_counts["markers"] and counts["asides"] == ref_counts["asides"]
