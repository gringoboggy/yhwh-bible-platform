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
