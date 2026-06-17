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
