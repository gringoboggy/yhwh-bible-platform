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


def test_build_allowed_all_layers_wired():
    for rid in ("kobo", "kindle", "apple", "play"):
        assert reader_sim.build_allowed(rid)[0] is True, rid


def test_build_force_override():
    allowed, reason = reader_sim.build_allowed("apple", force=True)
    assert allowed is True
    assert "force" in reason.lower()


def test_agent_sim_ready_when_all_packs_shipped():
    ok, msg = reader_sim.agent_sim_ready()
    assert ok is True
    assert "unlocked" in msg.lower()


def test_sim_reader_kindle_has_stk_layer():
    rep = reader_sim.sim_reader("kindle", Path("nope.epub"))
    assert "sim_checks" in rep
    assert any(c["name"] == "stk_channel_sim" for c in rep["sim_checks"])


def test_artifact_for_reader_subdir_layout(tmp_path):
    (tmp_path / "kindle").mkdir()
    (tmp_path / "kobo").mkdir()
    k1 = tmp_path / "kindle" / "Ethiopian_Bible_ethiopian-tewahedo_0.1.0-kindle-m4b.epub"
    k2 = tmp_path / "kindle" / "Ethiopian_Bible_catholic-study_0.1.0-kindle-m4b.epub"
    k1.write_bytes(b"x")
    k2.write_bytes(b"y")
    assert reader_sim._artifact_for_reader(tmp_path, "kindle") == k1


def test_thorium_cdp_on_round9_epub():
    epub = Path("build/round9-kobo-tap/Ethiopian_Bible_ethiopian-tewahedo_0.1.0_eink_2026-06-17T202652Z.epub")
    if not epub.is_file():
        return
    from dev.reader_sim import thorium_cdp

    results = thorium_cdp.probe_epub(epub, "apple")
    assert all(r.passed for r in results if r.name != "thorium_binary")
