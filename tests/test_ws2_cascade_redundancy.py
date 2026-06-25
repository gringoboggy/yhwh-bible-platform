"""WS2 note-cascade redundancy fix (Kobo deep-audit, 2026-06-25) — per Mac's
dev/audit/note-redundancy-findings.md.

Class 1: the grouped cascade (`_emit_cascade_sections`) drops the per-note leaf
`<a class="note-sym">` — the `vn-cat-head` already shows the category glyph once.
Class 2: `_strip_redundant_body_boilerplate` also strips the `xref-citation`
"<strong>Cross-references.</strong>" and `text-witness` "<strong>Manuscript witness.</strong>"
body lead-ins (which restate the category head/byline), by EXACT kind match.
"""

from scripts import build_edition as be


def _leaf(cat, glyph, label, body):
    return (
        f'<div class="vn-item note-{cat}-citation">• '
        f'<a class="note-sym" href="legend.xhtml#legend-{cat}" title="{label}">{glyph}</a> {body}</div>'
    )


class TestClass1DropLeafNoteSym:
    def test_grouped_cascade_drops_leaf_note_sym_but_keeps_leaf_and_header(self):
        rows = [
            {
                "cat": "xref",
                "source_key": "tsk",
                "source_display": "Treasury of Scripture Knowledge",
                "suppress_byline": False,
                "row": _leaf("xref", "‖", "Cross-references", '<a href="#a">Jhn 1:1</a> · <a href="#b">Heb 11:3</a>'),
            }
        ]
        out = be._emit_cascade_sections(rows, {"xref": ("‖", "Cross-references")})
        assert 'class="note-sym"' not in out  # leaf sym dropped (Class 1)
        assert 'class="vn-cat-sym"' in out and "‖" in out  # header glyph survives (once)
        assert 'class="vn-item' in out  # the leaf itself survives (conservation)
        assert "Jhn 1:1" in out and "Heb 11:3" in out  # the real payload survives
        assert out.count("‖") == 1  # glyph now appears exactly once (header only)

    def test_multiple_leaves_each_lose_their_sym(self):
        rows = [
            {
                "cat": "xref",
                "source_key": "t",
                "source_display": "TSK",
                "suppress_byline": False,
                "row": _leaf("xref", "‖", "Cross-references", '<a href="#a">A 1:1</a>'),
            },
            {
                "cat": "xref",
                "source_key": "t",
                "source_display": "TSK",
                "suppress_byline": False,
                "row": _leaf("xref", "‖", "Cross-references", '<a href="#b">B 2:2</a>'),
            },
        ]
        out = be._emit_cascade_sections(rows, {"xref": ("‖", "Cross-references")})
        assert 'class="note-sym"' not in out
        assert out.count("‖") == 1  # header only, not 1 + 2 leaves


class TestClass2StripBodyLeadIns:
    def test_xref_citation_lead_in_stripped(self):
        row = '<strong>Cross-references.</strong> <a href="#x">Jhn 1:1</a> · <a href="#y">Heb 11:3</a>'
        new, changed = be._strip_redundant_body_boilerplate(row, "xref-citation")
        assert changed is True
        assert "<strong>Cross-references.</strong>" not in new
        assert "Jhn 1:1" in new and "Heb 11:3" in new  # links survive

    def test_text_witness_lead_in_stripped(self):
        row = "<strong>Manuscript witness.</strong> P46 omits the clause."
        new, changed = be._strip_redundant_body_boilerplate(row, "text-witness")
        assert changed is True
        assert "<strong>Manuscript witness.</strong>" not in new
        assert "P46 omits the clause." in new

    def test_exact_kind_guard_does_not_strip_parallel(self):
        # A future hand-authored `parallel` note that opens with the same phrase must survive.
        row = "<strong>Cross-references.</strong> <a href='#x'>Gen 1:1</a>"
        new, changed = be._strip_redundant_body_boilerplate(row, "parallel")
        assert changed is False and new == row

    def test_existing_dict_and_topic_still_strip(self):
        d, dc = be._strip_redundant_body_boilerplate(
            "<strong>Dictionary (Easton's).</strong> CREATION — …", "dict-easton"
        )
        t, tc = be._strip_redundant_body_boilerplate(
            "<strong>Topics.</strong> This verse appears under: …", "topic-nave"
        )
        assert dc and "Dictionary (Easton's)" not in d
        assert tc and "<strong>Topics.</strong>" not in t
