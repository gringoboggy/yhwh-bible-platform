"""Lane-handoff baton core — pure file logic, no git side effects."""

from pathlib import Path

from scripts import lane_handoff as lh

INIT = (
    "---\n"
    "holder: windows\n"
    "from: windows\n"
    "turn: 0\n"
    "updated: 2026-06-03T00:00:00Z\n"
    "status: working\n"
    "---\n\n"
    "## Done\n- bootstrap\n\n## Next\n- start\n\n## Watch-outs\n- none\n"
)


def _repo(tmp_path: Path, lane: str = "windows") -> Path:
    (tmp_path / "dev").mkdir()
    (tmp_path / "dev" / "LANE_HANDOFF.md").write_text(INIT, encoding="utf-8")
    (tmp_path / "dev" / ".lane").write_text(lane, encoding="utf-8")
    return tmp_path


def test_parse_roundtrip():
    header, body = lh.parse(INIT)
    assert header["holder"] == "windows"
    assert header["turn"] == "0"
    assert "Done" in body
    # render -> parse is stable for the header keys
    h2, _ = lh.parse(lh.render(header, body))
    assert h2["holder"] == "windows" and h2["turn"] == "0"


def test_detect_lane_from_file(tmp_path):
    repo = _repo(tmp_path, lane="mac")
    assert lh.detect_lane(repo) == "mac"


def test_handoff_flips_holder_and_bumps_turn(tmp_path):
    repo = _repo(tmp_path, lane="windows")
    rc = lh.do_handoff(repo, to="mac", done="- finished P0 pilot", next="- map 1sa 7-11", watch="- GAPS only")
    assert rc == 0
    header, body = lh.load(repo)
    assert header["holder"] == "mac"
    assert header["from"] == "windows"
    assert header["turn"] == "1"
    assert header["updated"] != "2026-06-03T00:00:00Z"
    assert "map 1sa 7-11" in body


def test_handoff_refuses_non_holder(tmp_path):
    repo = _repo(tmp_path, lane="mac")  # baton says windows; this lane is mac
    rc = lh.do_handoff(repo, to="windows", done="x", next="y")
    assert rc == 1  # refused
    header, _ = lh.load(repo)
    assert header["holder"] == "windows" and header["turn"] == "0"  # unchanged


def test_handoff_force_overrides(tmp_path):
    repo = _repo(tmp_path, lane="mac")
    rc = lh.do_handoff(repo, to="mac", done="x", next="y", force=True)
    assert rc == 0
    assert lh.load(repo)[0]["holder"] == "mac"


def test_incoming_true_when_addressed_and_new(tmp_path, capsys):
    repo = _repo(tmp_path, lane="windows")
    lh.do_handoff(repo, to="windows", done="x", next="y", force=True)  # holder=windows, turn=1
    rc = lh.do_incoming(repo)
    assert rc == 0
    assert "INCOMING HANDOFF" in capsys.readouterr().out


def test_incoming_false_when_already_seen(tmp_path):
    repo = _repo(tmp_path, lane="windows")
    lh.do_handoff(repo, to="windows", done="x", next="y", force=True)
    lh.do_mark_seen(repo)
    assert lh.do_incoming(repo) == 1  # nothing new


def test_incoming_false_when_not_addressed(tmp_path):
    repo = _repo(tmp_path, lane="mac")  # baton holder=windows
    assert lh.do_incoming(repo) == 1
