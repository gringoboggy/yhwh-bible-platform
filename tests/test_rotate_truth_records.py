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
