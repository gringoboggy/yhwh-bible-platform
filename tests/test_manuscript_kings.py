import importlib
from scripts.core import manuscript_manifest as mm


def test_samuel_default_back_compat():
    mm.load_manifest.cache_clear()
    man = mm.load_manifest()  # no arg -> samuel (unchanged)
    assert "1sa" in man and "2sa" in man
    assert man["1sa"][1]["status"] == "calibrated"


def test_kings_track_loads_47_pending():
    mm.load_manifest.cache_clear()
    man = mm.load_manifest(track="kings")
    assert set(man) == {"1ki", "2ki"}
    assert len(man["1ki"]) == 22 and len(man["2ki"]) == 25
    assert all(man["1ki"][c]["status"] == "pending" for c in range(1, 23))
    assert all(man["2ki"][c]["status"] == "pending" for c in range(1, 26))


def test_chapter_entry_track_aware():
    mm.load_manifest.cache_clear()
    man = mm.load_manifest(track="kings")
    e = mm.chapter_entry(man, "1ki", 1)
    assert e["status"] == "pending"
    assert e["GG"] == {"folios": [], "source_images": []}
    assert e["CAM"] == {"folios": [], "views": []}
