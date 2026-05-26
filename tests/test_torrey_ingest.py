"""Tests for the Torrey's New Topical Textbook CCEL ingest (Track C, χ-cluster).

Torrey's New Topical Textbook (R.A. Torrey, 1897, public domain) is a topical
concordance structurally identical to Nave's Topical Bible: topic heading →
indented scripture-reference sub-entries. It therefore reuses Nave's CCEL
reference-expansion grammar, but needs its own parser because:

  * Torrey topics are Title-Case ("Access to God"), not Nave's ALL-CAPS.
  * Torrey nests recurring structural sub-labels ("Exemplified", "Illustrated",
    "Typified") that look like topics but are not — they recur under many topics,
    whereas a real topic appears exactly once in the alphabetical index.
"""

from __future__ import annotations

from scripts.extract_torrey_ccel import parse_text
from scripts.fetch_sources import _build_naves_indices


class TestTorreyParser:
    def test_extracts_title_case_topic_and_expands_refs(self):
        text = "Access to God\nIs of God — Ps 65:4.\nIs by Christ — Joh 10:7, 9; 14:6.\n"
        assert parse_text(text) == {
            "Access to God": [
                ["psa", 65, 4],
                ["jhn", 10, 7],
                ["jhn", 10, 9],
                ["jhn", 14, 6],
            ]
        }

    def test_filters_recurring_structural_sublabels(self):
        # "Exemplified" recurs under two distinct topics → structural sub-label,
        # NOT a topic; its member refs stay attributed to the enclosing topic.
        text = (
            "Adoption\n"
            "Explained — 2Co 6:18.\n"
            "Exemplified\n"
            "Moses. — Ge 12:1.\n"
            "Faith of Saints\n"
            "Described — Heb 11:1.\n"
            "Exemplified\n"
            "Abraham. — Ge 15:6.\n"
        )
        out = parse_text(text)
        assert "Exemplified" not in out
        assert out["Adoption"] == [["2co", 6, 18], ["gen", 12, 1]]
        assert out["Faith of Saints"] == [["heb", 11, 1], ["gen", 15, 6]]

    def test_ignores_page_noise(self):
        text = "1\nA\nTorrey's New Topical Textbook\nAlmsgiving\nCommanded — De 15:11.\niv\n2\n"
        out = parse_text(text)
        assert list(out.keys()) == ["Almsgiving"]
        assert out["Almsgiving"] == [["deu", 15, 11]]

    def test_topic_with_no_valid_refs_is_dropped(self):
        # Stray no-ref headings ("Contents", "Index") must not survive as
        # empty topics.
        text = "Contents\nIndex\nZeal\nRequired — Ro 12:11.\n"
        out = parse_text(text)
        assert "Contents" not in out
        assert "Index" not in out
        assert out["Zeal"] == [["rom", 12, 11]]

    def test_dewraps_wrapped_reference_continuation(self):
        # The CCEL text wraps long reference lines: the book token ("Heb")
        # ends one line and the "chapter:verse" tail wraps to the next. The
        # tail must rejoin its book (so the refs survive) and must NOT become
        # a fake numeric topic ("12:5-11.").
        text = "A\nAbasement\nThreatened — Pr 3:11,12; Heb\n12:5-11.\n"
        out = parse_text(text)
        assert not any(k[0].isdigit() for k in out)
        assert out["Abasement"] == [
            ["pro", 3, 11],
            ["pro", 3, 12],
            ["heb", 12, 5],
            ["heb", 12, 6],
            ["heb", 12, 7],
            ["heb", 12, 8],
            ["heb", 12, 9],
            ["heb", 12, 10],
            ["heb", 12, 11],
        ]

    def test_normalizes_legacy_book_codes_to_canonical(self):
        # "Joel" (full name) maps through the shared CCEL grammar's TSK fallback
        # to the LEGACY code "jol" — but the notes file is joe.py. It must
        # normalize to canonical "joe" or the note lands nowhere (no jol.py).
        text = "A\nAffliction\nReferenced — Joel 2:12.\n"
        out = parse_text(text)
        assert out["Affliction"] == [["joe", 2, 12]]

    def test_maps_torrey_jdj_abbreviation_to_judges(self):
        # Torrey renders Judges as "Jdj" (447x), which is absent from Nave's
        # CCEL abbreviation scheme. Unmapped, the whole ref-line would parse to
        # zero refs and be misread as a topic.
        text = "A\nAltars\nNatural rocks used as — Jdj 6:19-21.\n"
        out = parse_text(text)
        assert out["Altars"] == [["jdg", 6, 19], ["jdg", 6, 20], ["jdg", 6, 21]]
        assert not any("Natural rocks" in k for k in out)

    def test_dewraps_forward_emdash_wrapped_reference(self):
        # A sub-entry whose citation wrapped to the next line leaves the heading
        # ending in a bare em-dash; it must rejoin its refs, not become a topic.
        # The fragment shares the section's initial letter ("Covered" / "C"),
        # so the section gate cannot catch it — the forward em-dash merge must.
        text = "C\nCloud\nCovered it by day —\nEx 13:21; 40:38.\n"
        out = parse_text(text)
        assert not any(k.endswith("—") for k in out)
        assert "Covered it by day —" not in out
        assert out["Cloud"] == [["exo", 13, 21], ["exo", 40, 38]]

    def test_dewraps_hyphenated_word_wrapped_across_lines(self):
        # A prose description hyphenated across a line break ("destruc-" /
        # "tion") must glue back into one line, not leave a broken fragment topic.
        text = "T\nTyre\nThe ruins used to effect the destruc-\ntion of it — Eze 26:12.\n"
        out = parse_text(text)
        assert not any(k.endswith("-") for k in out)
        assert not any("destruc" in k for k in out)
        assert out["Tyre"] == [["eze", 26, 12]]

    def test_contents_letter_list_does_not_corrupt_section(self):
        # The front-matter Contents lists A, B, …, Z (page numbers stripped as
        # noise). That run must NOT leave the section letter stuck at the last
        # letter and reject the body's early A-topics (which precede the body's
        # own running "A" header).
        text = "Contents\nA\nB\nC\nD\nAccess to God\nIs of God — Ps 65:4.\n"
        out = parse_text(text)
        assert "Access to God" in out
        assert out["Access to God"] == [["psa", 65, 4]]

    def test_section_letter_gate_rejects_wrong_letter_subheader(self):
        # A unique grouping sub-header ("Should be set", initial S) under
        # section "A" must not become a topic; its member refs stay attributed
        # to the enclosing main topic. The frequency filter cannot catch a
        # once-occurring sub-header — the section-letter gate must.
        text = (
            "A\n"
            "Affections, The\n"
            "Should be supremely set upon God — De 6:3.\n"
            "Should be set\n"
            "Upon the commandments. — Ps 19:8.\n"
        )
        out = parse_text(text)
        assert "Should be set" not in out
        assert out["Affections, The"] == [["deu", 6, 3], ["psa", 19, 8]]


class TestBuildIndicesSourceKwarg:
    """The Torrey ingest reuses fetch_sources._build_naves_indices; it must
    accept a source label without changing Nave's default (byte-compat)."""

    def test_default_source_is_naves_backcompat(self):
        idx = _build_naves_indices({"X": [["gen", 1, 1]]})
        assert idx["_meta"]["source"] == "Nave's Topical Bible (1896, PD)"

    def test_explicit_source_label(self):
        idx = _build_naves_indices(
            {"X": [["gen", 1, 1]]},
            source="Torrey's New Topical Textbook (1897, PD)",
        )
        assert idx["_meta"]["source"] == "Torrey's New Topical Textbook (1897, PD)"


class TestTorreyTopicalLoader:
    """Integration tests against the generated content/sources/torrey_topical.json."""

    def test_singleton_and_size(self):
        from scripts.core import sources

        t = sources.torrey_topical()
        assert t is sources.torrey_topical()  # lru_cache singleton
        assert t.n_topics >= 600  # ~628 documented entries
        assert t.n_refs > 20000

    def test_reverse_index_lookup(self):
        from scripts.core import sources

        # Torrey lists Judges 6:19 ("Natural rocks used as [altars]") under "Altars".
        assert "Altars" in sources.torrey_topical().topics_for("jdg", 6, 19, top_n=50)

    def test_forward_index_lookup(self):
        from scripts.core import sources

        # "Access to God / Is of God — Ps 65:4."
        hits = {
            (h.target_book, h.target_chapter, h.target_verse)
            for h in sources.torrey_topical().verses_for("Access to God")
        }
        assert ("psa", 65, 4) in hits


class TestTorreyTopicalDetector:
    def test_emits_one_consolidated_candidate(self):
        from scripts.core.detectors import TorreyTopicalDetector

        cands = TorreyTopicalDetector(top_n=50).detect("jdg", 6, 19, "")
        assert len(cands) == 1
        c = cands[0]
        assert c.kind == "topic-torrey"
        assert (c.book, c.chapter, c.verse) == ("jdg", 6, 19)
        assert "Altars" in c.draft_body
        assert "Torrey" in c.source_attribution and "1897" in c.source_attribution

    def test_min_topics_gate_suppresses_candidate(self):
        from scripts.core.detectors import TorreyTopicalDetector

        assert TorreyTopicalDetector(min_topics=99).detect("jdg", 6, 19, "") == []


class TestTorreyNetNewDriver:
    def test_net_new_excludes_verses_nave_already_covers(self):
        # The user scoped Torrey to "net-new vs Nave's": for an overlapping book
        # (Genesis is heavily indexed in both), net-new must be a strict subset.
        from scripts.run_torrey_at_scale import run_torrey_for_book

        all_c = run_torrey_for_book("gen", dry_run=True)["candidates_written"]
        new_c = run_torrey_for_book("gen", dry_run=True, net_new=True)["candidates_written"]
        assert all_c > 0
        assert 0 <= new_c < all_c

    def test_overlap_only_is_exact_complement_of_net_new(self):
        # Full Torrey ships in two non-duplicating passes: --net-new (verses
        # Nave's lacks) then --overlap-only (verses Nave's covers). They must
        # partition the full set exactly, so no candidate is written twice.
        from scripts.run_torrey_at_scale import run_torrey_for_book

        all_c = run_torrey_for_book("gen", dry_run=True)["candidates_written"]
        new_c = run_torrey_for_book("gen", dry_run=True, net_new=True)["candidates_written"]
        ovl_c = run_torrey_for_book("gen", dry_run=True, overlap_only=True)["candidates_written"]
        assert ovl_c > 0
        assert new_c + ovl_c == all_c
