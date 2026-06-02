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
        """Updated mint-11 (2026-06-02): 2ki still has collated content but no
        rendered py module (Phase-3 render is post-marathon) and must report as
        MARATHON-PENDING, not silently missing. 1ki/1sa/2sa have since been
        rendered (marathon + Patrologia) and now appear under rendered_books."""
        from scripts.render_coverage import run_all

        rep = run_all()
        ge = rep["editions"]["geez-tewahedo"]
        marathon = ge["marathon_pending"]
        assert "2ki" in marathon, marathon
        # 1ki/1sa/2sa were rendered and are no longer marathon_pending.
        rendered = set(ge["rendered_books"])
        for b in ("1ki", "1sa", "2sa"):
            assert b in rendered, (b, sorted(rendered))
            assert b not in marathon, (b, marathon)

    def test_patrologia_books_now_rendered(self):
        """1Ch, 2Ch, Ezr, Neh, Job were rendered into geez-tewahedo from
        the Patrologia Orientalis printed bilingual critical editions
        (τ.6.x.5.x). They were previously patrologia_pending; the tool now
        reports them under rendered_books and they no longer appear in the
        pending/missing sets."""
        from scripts.render_coverage import run_all

        rep = run_all()
        ge = rep["editions"]["geez-tewahedo"]
        rendered = set(ge["rendered_books"])
        patrologia = {"1ch", "2ch", "ezr", "neh", "job"}
        assert patrologia <= rendered, (
            f"Patrologia books should be rendered in geez-tewahedo; rendered={sorted(rendered)}"
        )
        # And they should no longer be reported as pending.
        pending = set(ge.get("patrologia_pending", [])) | set(ge.get("missing", []))
        assert not (patrologia & pending), f"Patrologia books still reported pending: {sorted(patrologia & pending)}"


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
