"""Tests for scripts/rotate_truth_records.py — the truth-record rotator/FIXER.

Pins: keeps the header + newest N entries + the stable trailing section; archives
the rest; never drops the live (newest) entry; round-trips when keeping all; the
apply path writes both the trimmed live file and the newest-first archive batch.
"""

from scripts import rotate_truth_records as rot


def _n_entries(text):
    """Count journal ENTRY-START lines (not the bare glyph — the archive intro
    legitimately mentions the marker in prose)."""
    return sum(1 for ln in text.splitlines() if ln.startswith("> **➤➤➤"))


def _make(dates, tail="## STABLE SECTION\n\nkeep me always\n"):
    """Build a synthetic truth-record: title header, ``dates`` (newest first) as
    journal entries, then a stable ``## `` trailing section."""
    head = "# Title — snapshot\n\n"
    body = "".join(f"> **➤➤➤ {d} — entry for {d}**\n>\n" for d in dates)
    return head + body + "\n" + tail


class TestPlanRotation:
    def test_keeps_newest_and_archives_rest(self):
        text = _make(["2026-05-29", "2026-05-28", "2026-05-27", "2026-05-26", "2026-05-25"])
        plan = rot.plan_rotation(text, keep=2)
        assert plan["changed"] is True
        assert plan["entries_after"] == 2
        assert plan["archived"] == 3
        # Newest two live, older three archived.
        assert "2026-05-29" in plan["live"] and "2026-05-28" in plan["live"]
        for d in ("2026-05-27", "2026-05-26", "2026-05-25"):
            assert d not in plan["live"]
            assert d in plan["archive_batch"]
        # Stable trailing section survives.
        assert "## STABLE SECTION" in plan["live"] and "keep me always" in plan["live"]
        # Header survives.
        assert plan["live"].startswith("# Title — snapshot")

    def test_archive_batch_carries_date_range(self):
        text = _make(["2026-05-29", "2026-05-28", "2026-05-27", "2026-05-25"])
        plan = rot.plan_rotation(text, keep=1)
        assert plan["date_range"] == ("2026-05-25", "2026-05-28")
        assert "2026-05-25..2026-05-28" in plan["archive_batch"]

    def test_no_op_when_within_keep(self):
        text = _make(["2026-05-29", "2026-05-28"])
        plan = rot.plan_rotation(text, keep=2)
        assert plan["changed"] is False
        assert plan["live"] == text  # exact round-trip when keeping all

    def test_keep_all_round_trips(self):
        text = _make(["2026-05-29", "2026-05-28", "2026-05-27"])
        assert rot.plan_rotation(text, keep=10)["live"] == text

    def test_never_drops_the_live_entry(self):
        text = _make(["2026-05-29", "2026-05-28", "2026-05-27"])
        for k in (1, 2, 3):
            assert "2026-05-29" in rot.plan_rotation(text, keep=k)["live"]

    def test_handles_no_tail_section(self):
        # IN_FLIGHT-style file whose only "## " is the trailing ACTIVE block; here
        # there is no trailing section at all → tail is empty, entries still rotate.
        text = "# T\n\n" + "".join(f"> **➤➤➤ 2026-05-2{d} — e**\n>\n" for d in (9, 8, 7))
        plan = rot.plan_rotation(text, keep=1)
        assert plan["changed"] is True and plan["entries_after"] == 1
        assert "2026-05-29" in plan["live"]


def _make_arrow(dates, tail="## Background backlog\n\nstable backlog text\n"):
    """Build a synthetic IN_FLIGHT-style record whose entries use the ``> **▶``
    marker with status glyphs BEFORE the date (the live IN_FLIGHT shape)."""
    head = "# In-flight work — tracker\n\n<!-- TRACKER-STATE: active -->\n\n"
    body = "".join(f"> **▶ ✅ DONE {d} (🪟 Windows, turn) — entry for {d}.**\n>\n" for d in dates)
    return head + body + "\n" + tail


class TestJournalArrowMarker:
    """IN_FLIGHT's entries start ``> **▶ …`` (not ``> **➤➤➤``) — the rotator must
    treat BOTH marker families as entry starts (mint 3.1)."""

    def test_arrow_entries_rotate(self):
        text = _make_arrow(["2026-06-10", "2026-06-09", "2026-06-08", "2026-06-07", "2026-06-06"])
        plan = rot.plan_rotation(text, keep=2)
        assert plan["changed"] is True
        assert plan["entries_after"] == 2 and plan["archived"] == 3
        assert "2026-06-10" in plan["live"] and "2026-06-09" in plan["live"]
        for d in ("2026-06-08", "2026-06-07", "2026-06-06"):
            assert d not in plan["live"] and d in plan["archive_batch"]
        assert "## Background backlog" in plan["live"]

    def test_mixed_markers_rotate_together(self):
        # Newer ▶ entries above older ➤➤➤ entries (the live IN_FLIGHT shape).
        arrows = "".join(f"> **▶ 🔄 {d} (win) — e**\n>\n" for d in ("2026-06-10", "2026-06-09"))
        legacy = "".join(f"> **➤➤➤ {d} — e**\n>\n" for d in ("2026-05-31", "2026-05-30", "2026-05-29"))
        text = "# T\n\n" + arrows + legacy + "\n## TAIL\n\nkeep\n"
        plan = rot.plan_rotation(text, keep=2)
        assert plan["entries_before"] == 5 and plan["entries_after"] == 2
        assert "2026-06-10" in plan["live"] and "2026-06-09" in plan["live"]
        for d in ("2026-05-31", "2026-05-30", "2026-05-29"):
            assert d not in plan["live"] and d in plan["archive_batch"]

    def test_bold_continuation_lines_are_not_entries(self):
        # Continuation lines inside an entry may start "> **WIN-LANE…" / "> **MAC…"
        # — bold, but NOT an entry marker. They must ride with their entry.
        text = (
            "# T\n\n"
            "> **▶ ON BOOT 2026-06-08 (🪟 Windows) — run the split audit.**\n"
            "> **WIN-LANE steps:** (1) pull (2) run\n"
            "> **MAC LANE** runs LANE='mac'\n>\n"
            "> **▶ ✅ DONE 2026-06-07 (🪟 Windows) — older entry.**\n>\n"
            "> **▶ ✅ DONE 2026-06-06 (🪟 Windows) — oldest entry.**\n>\n"
        )
        plan = rot.plan_rotation(text, keep=1)
        assert plan["entries_before"] == 3
        # The kept entry carries its continuation lines.
        assert "WIN-LANE steps" in plan["live"] and "MAC LANE" in plan["live"]
        assert "2026-06-07" in plan["archive_batch"] and "2026-06-06" in plan["archive_batch"]

    def test_arrow_date_range_extracted_mid_line(self):
        text = _make_arrow(["2026-06-10", "2026-06-09", "2026-06-08", "2026-06-06"])
        plan = rot.plan_rotation(text, keep=1)
        assert plan["date_range"] == ("2026-06-06", "2026-06-09")


def _make_board(n_turns, protected_at=None, fm_extra=""):
    """Synthetic LANE_HANDOFF: YAML frontmatter + ``## `` turn sections (newest
    first), optionally inserting the protected STANDING section at an index."""
    fm = f"---\nmode: parallel\nturn: 69\nfrom: windows\n{fm_extra}truth_owner: windows\nholder: windows\n---\n\n"
    secs = [
        f"## ▶ Windows → Mac (turn {70 - i}, 2026-06-{10 - i:02d}) — headline {70 - i}\n\nbody for turn {70 - i}.\n\n"
        for i in range(n_turns)
    ]
    if protected_at is not None:
        secs.insert(
            protected_at,
            "## ⚠ STANDING — both lanes (do NOT rotate this section out of the file)\n\nstanding doctrine.\n\n",
        )
    return fm + "".join(secs)


class TestBoardRotation:
    """LANE_HANDOFF rotation (mint 3.3): frontmatter + the newest N turn sections
    + any 'do NOT rotate' section stay live; older sections archive."""

    def test_keeps_frontmatter_and_newest_two(self):
        text = _make_board(5)
        plan = rot.plan_board_rotation(text, keep=2)
        assert plan["changed"] is True
        assert plan["entries_before"] == 5 and plan["entries_after"] == 2
        assert plan["live"].startswith("---\nmode: parallel")
        assert "turn 70" in plan["live"] and "turn 69" in plan["live"]
        for t in ("turn 68", "turn 67", "turn 66"):
            assert t not in plan["live"] and t in plan["archive_batch"]

    def test_protected_section_survives_any_keep(self):
        text = _make_board(4, protected_at=2)
        plan = rot.plan_board_rotation(text, keep=1)
        assert "do NOT rotate" in plan["live"] and "standing doctrine." in plan["live"]
        assert "do NOT rotate" not in plan["archive_batch"]
        # keep=1 → only the newest turn section stays besides the protected one.
        assert "turn 70" in plan["live"] and "turn 69" not in plan["live"]

    def test_no_op_when_within_keep(self):
        text = _make_board(2)
        plan = rot.plan_board_rotation(text, keep=2)
        assert plan["changed"] is False
        assert plan["live"] == text  # exact round-trip on no-op

    def test_pointer_line_present_exactly_once(self):
        text = _make_board(5)
        plan = rot.plan_board_rotation(text, keep=2)
        assert plan["live"].count(rot._BOARD_POINTER) == 1
        # Rotating the already-rotated text again must not duplicate the pointer.
        plan2 = rot.plan_board_rotation(plan["live"], keep=1)
        assert plan2["live"].count(rot._BOARD_POINTER) == 1

    def test_date_range_from_headings(self):
        text = _make_board(4)
        plan = rot.plan_board_rotation(text, keep=2)
        assert plan["date_range"] == ("2026-06-07", "2026-06-08")


class TestCountEntries:
    """``count_entries`` is the single resolver the lint's entry-count check
    shares with the rotator (one resolver per control — RULES doctrine)."""

    def test_journal_counts_both_marker_families(self):
        arrows = "> **▶ ✅ 2026-06-10 — a**\n>\n> **➤➤➤ 2026-06-09 — b**\n>\n"
        text = "# T\n\n" + arrows + "## TAIL mentions `> **➤➤➤` in prose\n\nx\n"
        assert rot.count_entries("dev/IN_FLIGHT.md", text) == 2

    def test_board_counts_only_rotatable_sections(self):
        text = _make_board(3, protected_at=1)
        assert rot.count_entries("dev/LANE_HANDOFF.md", text) == 3

    def test_unknown_record_returns_none(self):
        assert rot.count_entries("dev/CLAUDE_PROJECT_RULES.md", "# x\n") is None

    def test_backslash_rel_normalized(self):
        text = "# T\n\n> **➤➤➤ 2026-06-10 — a**\n>\n"
        assert rot.count_entries("dev\\SESSION_STATE.md", text) == 1


class TestRotateAll:
    def _setup(self, tmp_path, monkeypatch, n=6):
        monkeypatch.setattr(rot, "REPO", tmp_path)
        (tmp_path / "dev").mkdir()
        dates = [f"2026-05-{29 - i:02d}" for i in range(n)]
        (tmp_path / "dev" / "SESSION_STATE.md").write_text(_make(dates), encoding="utf-8")
        # IN_FLIGHT with a "## ➤➤➤ ACTIVE" trailing block (heading uses the glyph
        # but NOT the **-marker → must be preserved, not counted as an entry).
        (tmp_path / "dev" / "IN_FLIGHT.md").write_text(
            _make(dates, tail="## ➤➤➤ ACTIVE — current task\n\nthe live task block\n"), encoding="utf-8"
        )
        return dates

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch)
        before = (tmp_path / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        res = rot.rotate_all(keep=2, dry_run=True)
        assert res["applied"] is False
        assert (tmp_path / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8") == before
        assert not (tmp_path / "dev" / "archive" / "SESSION_STATE_archive.md").exists()

    def test_apply_trims_live_and_archives(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, n=6)
        res = rot.rotate_all(keep=2, dry_run=True)  # preview first
        assert res["applied"] is False and res["changes"]
        res = rot.rotate_all(keep=2, dry_run=False)
        assert res["applied"] is True
        live = (tmp_path / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        arch = (tmp_path / "dev" / "archive" / "SESSION_STATE_archive.md").read_text(encoding="utf-8")
        # Live keeps 2 entries + stable tail; archive holds the other 4.
        assert _n_entries(live) == 2
        assert "## STABLE SECTION" in live
        assert _n_entries(arch) == 4
        # IN_FLIGHT: 2 entries live + the ACTIVE block (the heading is NOT an entry).
        iflive = (tmp_path / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert _n_entries(iflive) == 2
        assert "## ➤➤➤ ACTIVE — current task" in iflive and "the live task block" in iflive

    def test_second_rotation_prepends_newest_batch(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, n=6)
        rot.rotate_all(keep=4, dry_run=False)  # archive the 2 oldest first
        rot.rotate_all(keep=2, dry_run=False)  # then archive 2 more (newer than the first batch)
        arch = (tmp_path / "dev" / "archive" / "SESSION_STATE_archive.md").read_text(encoding="utf-8")
        # Sentinel present once; the two batch headers present; newer batch above older.
        assert arch.count(rot._BATCH_SENTINEL) == 1
        assert arch.count("<!-- archived:") == 2
        first_batch = arch.index("2026-05-26..2026-05-27")  # the newer (2nd) rotation batch
        older_batch = arch.index("2026-05-24..2026-05-25")  # the older (1st) rotation batch
        assert first_batch < older_batch

    def test_apply_rotates_the_board_into_existing_log(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch, n=2)  # journals already within budget
        (tmp_path / "dev" / "LANE_HANDOFF.md").write_text(_make_board(5, protected_at=3), encoding="utf-8")
        # Pre-existing archive log already carrying the batch sentinel (the live
        # dev/archive/LANE_HANDOFF_LOG.md is migrated to this format once).
        (tmp_path / "dev" / "archive").mkdir()
        (tmp_path / "dev" / "archive" / "LANE_HANDOFF_LOG.md").write_text(
            f"# LANE_HANDOFF archived log\n\nintro prose.\n\n{rot._BATCH_SENTINEL}\n\n## old turn 22\n\nx\n",
            encoding="utf-8",
        )
        res = rot.rotate_all(keep=2, dry_run=False)
        assert res["applied"] is True
        live = (tmp_path / "dev" / "LANE_HANDOFF.md").read_text(encoding="utf-8")
        arch = (tmp_path / "dev" / "archive" / "LANE_HANDOFF_LOG.md").read_text(encoding="utf-8")
        assert live.startswith("---\nmode: parallel") and "do NOT rotate" in live
        assert "turn 70" in live and "turn 69" in live and "turn 68" not in live
        # New batch landed after the sentinel, ABOVE the legacy section.
        assert arch.count(rot._BATCH_SENTINEL) == 1
        assert arch.index("turn 68") < arch.index("## old turn 22")
        assert "intro prose." in arch  # legacy header untouched
