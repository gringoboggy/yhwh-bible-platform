"""lane_watch — cross-lane poll helper (no network in unit tests)."""

from scripts import lane_watch as lw


def test_int_turn_parses():
    assert lw._int_turn({"turn": "111"}) == 111
    assert lw._int_turn({}) == 0
    assert lw._int_turn({"turn": "nope"}) == 0


def test_exit_code_matrix():
    assert (
        lw._exit_code({"offline": True, "fetch_ok": False, "behind": False, "remote_ahead": False, "incoming": False})
        == 2
    )
    assert (
        lw._exit_code({"offline": False, "fetch_ok": True, "behind": True, "remote_ahead": False, "incoming": False})
        == 10
    )
    assert (
        lw._exit_code({"offline": False, "fetch_ok": True, "behind": False, "remote_ahead": False, "incoming": True})
        == 20
    )
    assert (
        lw._exit_code({"offline": False, "fetch_ok": True, "behind": True, "remote_ahead": True, "incoming": True})
        == 30
    )
    assert (
        lw._exit_code({"offline": False, "fetch_ok": True, "behind": False, "remote_ahead": False, "incoming": False})
        == 0
    )


def test_remote_handoff_header_parses_frontmatter(tmp_path, monkeypatch):
    sample = "---\nmode: parallel\nturn: 42\nfrom: windows\nwindows: pytest triage\n---\n\n## body\n"

    def fake_git(*args, **kwargs):
        if args[:3] == ("show", "origin/main:dev/LANE_HANDOFF.md"):
            return 0, sample, ""
        return 1, "", ""

    monkeypatch.setattr(lw, "_git", fake_git)
    h = lw._remote_handoff_header()
    assert h["turn"] == "42"
    assert h["from"] == "windows"
    assert h["windows"] == "pytest triage"


def test_check_flags_unpushed_handoff(monkeypatch, tmp_path):
    monkeypatch.setattr(lw, "REPO", tmp_path)
    monkeypatch.setattr(lw, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(lw, "LOG_PATH", tmp_path / "log.txt")
    (tmp_path / "dev").mkdir()
    (tmp_path / "dev" / "LANE_HANDOFF.md").write_text(
        "---\nmode: parallel\nturn: 99\nfrom: mac\nmac: idle\nwindows: idle\n---\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(lw, "_fetch", lambda: True)
    monkeypatch.setattr(lw, "_auto_pull", lambda: (False, ""))
    monkeypatch.setattr(lw, "_handoff_dirty", lambda: False)
    monkeypatch.setattr(lw, "_committed_handoff_header", lambda: {"turn": "99"})
    monkeypatch.setattr(lw, "_incoming_check", lambda: (1, ""))
    monkeypatch.setattr(
        lw,
        "_remote_handoff_header",
        lambda: {"turn": "98", "from": "windows"},
    )
    monkeypatch.setattr(
        "scripts.lane_ping.gather",
        lambda: {"status": "CLEAR", "unpushed": 2, "remotes": {}, "baton": {}},
    )
    monkeypatch.setattr("scripts.lane_handoff.detect_lane", lambda repo: "mac")
    info = lw.check(auto_pull=False, quiet_log=True)
    assert info["unpushed_handoff"] is True
    assert info["local_turn"] == 99
    assert info["remote_turn"] == 98


def test_active_queue_skips_round9_section(tmp_path, monkeypatch):
    monkeypatch.setattr(lw, "QUEUE_PATH", tmp_path / "MAC_WORK_QUEUE.md")
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "MAC_WORK_QUEUE.md").write_text(
        "## Active queue\n\n"
        "- [x] done item\n"
        "- [ ] first open task\n"
        "\n## Round 9 queue (after gate)\n\n"
        "- [ ] should not pick this\n",
        encoding="utf-8",
    )
    assert lw._next_mac_queue_item() == "first open task"


def test_mirror_skew_detects_divergent_tips():
    ping = {
        "remotes": {
            "origin": {"remote_tip": "aaa1111", "cached": "aaa1111"},
            "github": {"remote_tip": "bbb2222", "cached": "bbb2222"},
        }
    }
    skew, o, g = lw._mirror_skew(ping)
    assert skew is True
    assert o == "aaa1111"
    assert g == "bbb2222"


def test_auto_pull_runs_fetch_then_rebase(monkeypatch):
    # Dirty-tree gating moved OUT of _auto_pull into check() (which auto-commits
    # a dirty tree then pulls — see test_check_* below), so _auto_pull is now a
    # pure fetch+rebase. MUST stub _git so the test never touches the real repo
    # (the old test left _git unmocked → ran a live `git fetch`/`rebase`).
    calls = []

    def fake_git(*args, timeout=30):
        calls.append(args)
        return (0, "ok", "")

    monkeypatch.setattr(lw, "_git", fake_git)
    pulled, msg = lw._auto_pull()
    assert pulled is True
    assert ("fetch", "origin", "--quiet", "--prune") in calls
    assert any(a[:2] == ("rebase", "origin/main") for a in calls)


def test_auto_pull_aborts_rebase_on_failure(monkeypatch):
    # On a failed rebase, _auto_pull must auto-abort so later git ops/saves are
    # not left mid-rebase, and surface "REBASE FAILED". _git fully stubbed.
    calls = []

    def fake_git(*args, timeout=30):
        calls.append(args)
        if args[:2] == ("rebase", "origin/main"):
            return (1, "", "conflict")
        return (0, "", "")

    monkeypatch.setattr(lw, "_git", fake_git)
    pulled, msg = lw._auto_pull()
    assert pulled is False
    assert "REBASE FAILED" in msg
    assert ("rebase", "--abort") in calls


def test_check_flags_uncommitted_handoff(monkeypatch, tmp_path):
    monkeypatch.setattr(lw, "REPO", tmp_path)
    monkeypatch.setattr(lw, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(lw, "LOG_PATH", tmp_path / "log.txt")
    (tmp_path / "dev").mkdir()
    (tmp_path / "dev" / "LANE_HANDOFF.md").write_text(
        "---\nmode: parallel\nturn: 100\nfrom: windows\nmac: idle\nwindows: idle\n---\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(lw, "_fetch", lambda: True)
    monkeypatch.setattr(lw, "_auto_pull", lambda: (False, ""))
    monkeypatch.setattr(lw, "_incoming_check", lambda: (1, ""))
    monkeypatch.setattr(lw, "_handoff_dirty", lambda: True)
    monkeypatch.setattr(
        lw,
        "_committed_handoff_header",
        lambda: {"turn": "99", "from": "windows"},
    )
    monkeypatch.setattr(
        lw,
        "_remote_handoff_header",
        lambda: {"turn": "99", "from": "windows"},
    )
    monkeypatch.setattr(
        "scripts.lane_ping.gather",
        lambda: {"status": "CLEAR", "unpushed": 0, "remotes": {}, "baton": {}},
    )
    monkeypatch.setattr("scripts.lane_handoff.detect_lane", lambda repo: "windows")
    info = lw.check(auto_pull=False, quiet_log=True)
    assert info["uncommitted_handoff"] is True
    assert info["unpushed_handoff"] is True


def test_check_auto_pull_on_remote_board_ahead(monkeypatch, tmp_path):
    monkeypatch.setattr(lw, "REPO", tmp_path)
    monkeypatch.setattr(lw, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(lw, "LOG_PATH", tmp_path / "log.txt")
    (tmp_path / "dev").mkdir()
    (tmp_path / "dev" / "LANE_HANDOFF.md").write_text(
        "---\nmode: parallel\nturn: 10\nfrom: windows\nmac: idle\nwindows: idle\n---\n",
        encoding="utf-8",
    )
    pulls: list[str] = []

    def fake_pull():
        pulls.append("yes")
        (tmp_path / "dev" / "LANE_HANDOFF.md").write_text(
            "---\nmode: parallel\nturn: 11\nfrom: windows\nmac: idle\nwindows: work\n---\n",
            encoding="utf-8",
        )
        return True, "pulled"

    monkeypatch.setattr(lw, "_fetch", lambda: True)
    monkeypatch.setattr(lw, "_auto_pull", fake_pull)
    monkeypatch.setattr(lw, "_working_tree_dirty", lambda: False)
    monkeypatch.setattr(lw, "_handoff_dirty", lambda: False)
    monkeypatch.setattr(lw, "_committed_handoff_header", lambda: {"turn": "10"})
    monkeypatch.setattr(lw, "_incoming_check", lambda: (1, ""))
    monkeypatch.setattr(
        lw,
        "_remote_handoff_header",
        lambda: {"turn": "11", "from": "windows", "windows": "work"},
    )
    monkeypatch.setattr(
        "scripts.lane_ping.gather",
        lambda: {"status": "CLEAR", "unpushed": 0, "remotes": {}, "baton": {}},
    )
    monkeypatch.setattr("scripts.lane_handoff.detect_lane", lambda repo: "mac")
    info = lw.check(auto_pull=True, quiet_log=True)
    assert pulls == ["yes"]
    assert info["auto_pulled"] is True
