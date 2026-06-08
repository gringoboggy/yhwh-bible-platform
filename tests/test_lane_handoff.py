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


# --- v2: mode + per-lane task board + assign + prune -------------------------

V2 = (
    "---\n"
    "mode: parallel\n"
    "turn: 5\n"
    "from: windows\n"
    "updated: 2026-06-08T00:00:00Z\n"
    "status: working\n"
    "mac: run the deep-audit mac dims\n"
    "windows: idle\n"
    "truth_owner: windows\n"
    "holder: windows\n"
    "---\n\n"
    "## ⚠ STANDING — both lanes\n- keep me\n\n## ▶ windows → mac (turn 5)\n- audit\n"
)


def _repo_v2(tmp_path: Path, lane: str) -> Path:
    (tmp_path / "dev").mkdir()
    (tmp_path / "dev" / "LANE_HANDOFF.md").write_text(V2, encoding="utf-8")
    (tmp_path / "dev" / ".lane").write_text(lane, encoding="utf-8")
    return tmp_path


def test_incoming_fires_on_task_even_when_not_owner(tmp_path, capsys):
    """THE v2 fix: a Mac-directed task with truth_owner=windows still surfaces to Mac."""
    repo = _repo_v2(tmp_path, lane="mac")  # truth_owner=windows, but mac has a task
    rc = lh.do_incoming(repo)
    assert rc == 0
    out = capsys.readouterr().out
    assert "INCOMING HANDOFF" in out and "deep-audit" in out


def test_incoming_silent_for_idle_non_owner(tmp_path):
    repo = _repo_v2(tmp_path, lane="windows")  # windows is owner -> still addressed (owns truth-records)
    assert lh.do_incoming(repo) == 0
    # but a lane that is neither owner nor tasked stays silent:
    (repo / "dev" / "LANE_HANDOFF.md").write_text(V2.replace("mac: run the deep-audit mac dims", "mac: idle"), "utf-8")
    (repo / "dev" / ".lane").write_text("mac", encoding="utf-8")
    assert lh.do_incoming(repo) == 1


def test_assign_no_refusal_updates_board_without_transfer(tmp_path):
    repo = _repo_v2(tmp_path, lane="mac")  # mac is NOT the truth_owner
    rc = lh.do_assign(repo, mac="finished audit; verifying", note="- audit done")
    assert rc == 0
    header, body = lh.load(repo)
    assert header["truth_owner"] == "windows"  # ownership unchanged
    assert header["mac"] == "finished audit; verifying"
    assert header["turn"] == "6"
    assert "keep me" in body  # history preserved


def test_handoff_sets_mode_and_tasks_and_preserves_history(tmp_path):
    repo = _repo_v2(tmp_path, lane="windows")
    rc = lh.do_handoff(repo, to="mac", mode="exclusive", mac="own the bake", windows="idle", done="d", next="n")
    assert rc == 0
    header, body = lh.load(repo)
    assert header["mode"] == "exclusive"
    assert header["truth_owner"] == "mac" and header["holder"] == "mac"
    assert header["mac"] == "own the bake"
    assert "keep me" in body and "## ▶ windows → mac (turn 5)" in body  # old sections preserved


def test_prune_keeps_standing_and_recent(tmp_path):
    repo = _repo_v2(tmp_path, lane="windows")
    # add several turn sections via assign
    for i in range(8):
        lh.do_assign(repo, note=f"- turn note {i}")
    rc = lh.do_prune(repo, keep=3)
    assert rc == 0
    _, body = lh.load(repo)
    assert "STANDING" in body  # pinned
    assert (repo / "dev" / "archive" / "LANE_HANDOFF_LOG.md").exists()


def test_status_smoke(tmp_path, capsys):
    repo = _repo_v2(tmp_path, lane="mac")
    import scripts.lane_handoff as m

    orig = m.REPO
    m.REPO = repo
    try:
        assert m.do_status(repo) == 0
    finally:
        m.REPO = orig
    out = capsys.readouterr().out
    assert "mode=parallel" in out and "YOU (mac)" in out
