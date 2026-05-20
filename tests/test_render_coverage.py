"""Render-coverage inventory tool (audit 2026-05-20 — broadened from
Samuel/Kings to whole-project).

Reports which books of the canonical 87-book Tewahedo set are rendered
into each ``content/translations/<edition>/`` directory, by which source
track (manuscript / parallel-PDF / Patrologia / KJV-skeleton). Lets the
project see at a glance which tracks are advancing and which are paused.
"""


class TestCoverageReportShape:
    def test_run_all_returns_summary_and_per_edition(self):
        from scripts.render_coverage import run_all

        rep = run_all()
        assert "summary" in rep
        assert "editions" in rep
        # Summary fields the dashboard / preflight composer consumes
        assert "canonical_books" in rep["summary"]
        assert rep["summary"]["canonical_books"] >= 66  # at minimum protestant
        assert "geez_tewahedo_rendered" in rep["summary"]
        assert "amharic_tewahedo_rendered" in rep["summary"]

    def test_kjv_skeleton_has_protestant_subset(self):
        """KJV is the protestant 66-book subset — it does NOT have the
        Tewahedo distinctives (mq1-3, 1en, jub, 4ba, paz). The tool's
        canonical list is the Tewahedo SUPERSET; KJV's missing list
        is the Tewahedo-distinctive set."""
        from scripts.render_coverage import run_all

        rep = run_all()
        # KJV has the protestant 66; the Tewahedo superset has more
        assert rep["editions"]["kjv"]["rendered_count"] >= 60
        # Tewahedo distinctives are NOT in the protestant skeleton
        kjv_missing = set(rep["editions"]["kjv"]["missing"])
        tewahedo_distinctives = {"mq1", "mq2", "mq3", "1en", "jub", "4ba"}
        assert tewahedo_distinctives & kjv_missing, "expected at least one Tewahedo distinctive to be missing from KJV"


class TestGeezTewahedoCoverage:
    def test_calibration_chapters_drive_partial_render(self):
        """Samuel/Kings chapters have collated content but no rendered
        py module yet (Phase-3 render is post-marathon). Tool should
        report them as MARATHON-PENDING, not silently missing."""
        from scripts.render_coverage import run_all

        rep = run_all()
        # 1ki + 2ki + 1sa + 2sa should appear as marathon_pending
        # (collation exists, render does not)
        marathon = rep["editions"]["geez-tewahedo"]["marathon_pending"]
        assert "1ki" in marathon, marathon
        assert "2ki" in marathon, marathon
        # 1sa, 2sa have calibration chapters but full render still pending
        assert "1sa" in marathon, marathon
        assert "2sa" in marathon, marathon

    def test_patrologia_books_appear_as_pending(self):
        """1Ch, 2Ch, Ezr, Neh, Job have Patrologia PDFs on disk under
        GAPS/ but aren't rendered yet. Tool flags them as patrologia
        pending."""
        from scripts.render_coverage import run_all

        rep = run_all()
        ge = rep["editions"]["geez-tewahedo"]
        # Either as patrologia_pending OR as missing — tool's call
        pending = set(ge.get("patrologia_pending", [])) | set(ge.get("missing", []))
        assert {"1ch", "2ch", "ezr", "neh", "job"} & pending


class TestRunAllExitContract:
    """run_all() conforms to the §9 meta-tool shape used by lint_rules /
    api_preflight composers."""

    def test_run_all_dict_shape(self):
        from scripts.render_coverage import run_all

        rep = run_all()
        # Same shape as other meta-tools: summary + the dict body
        assert isinstance(rep, dict)
        assert "summary" in rep
        # Status keys consistent with other §9 tools
        summary = rep["summary"]
        for k in ("canonical_books", "geez_tewahedo_rendered", "amharic_tewahedo_rendered"):
            assert k in summary
            assert isinstance(summary[k], int)
