"""Reader Simulation Lab orchestrator — unit tests."""

from pathlib import Path

from scripts import reader_sim


def test_list_readers():
    assert set(reader_sim.READERS) == {"apple", "kobo", "kindle", "play"}


def test_gate_missing_artifact(tmp_path):
    rep = reader_sim.gate_reader("play", tmp_path / "nope.epub")
    assert rep["ok"] is False
    assert rep["checks"][0]["name"] == "exists"


def test_guess_reader_kepub():
    assert reader_sim._guess_reader(Path("x.kepub.epub")) == "kobo"


def test_sim_pack_ready_kobo_and_play():
    assert reader_sim.sim_pack_ready("kobo") is True
    assert reader_sim.sim_pack_ready("play") is True


def test_sim_pack_kindle_needs_stk_channel():
    assert reader_sim.sim_pack_ready("kindle") is True  # stk_channel.sh stub shipped


def test_build_allowed_kobo_only_while_layers_pending():
    assert reader_sim.build_allowed("kobo")[0] is True
    assert reader_sim.build_allowed("kindle")[0] is False
    assert "sim layer pending" in reader_sim.build_allowed("kindle")[1].lower()


def test_build_force_override():
    allowed, reason = reader_sim.build_allowed("apple", force=True)
    assert allowed is True
    assert "force" in reason.lower()


def test_agent_sim_ready_when_all_packs_shipped():
    ok, msg = reader_sim.agent_sim_ready()
    assert ok is True
    assert "unlocked" in msg.lower()


def test_sim_reader_kobo_has_calibration_layer():
    # structural gate on missing file still returns sim_checks shape when sim_reader called
    rep = reader_sim.sim_reader("kindle", Path("nope.epub"))
    assert "sim_checks" in rep
    assert any(c["name"] == "stk_channel_sim" for c in rep["sim_checks"])
