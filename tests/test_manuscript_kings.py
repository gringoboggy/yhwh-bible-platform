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


def test_driver_kings_track_reports_47_pending():
    import scripts.run_manuscript_collation_at_scale as drv

    rep = drv.run(dry=True, track="kings")
    assert rep["chapters_total"] == 47
    assert rep["chapters_pending"] == 47
    assert rep["chapters_collated"] == 0
    assert {x["book"] for x in rep["pending_needs_transcription"]} == {"1ki", "2ki"}


def test_driver_samuel_default_unchanged():
    import scripts.run_manuscript_collation_at_scale as drv

    rep = drv.run(dry=True)  # no track -> samuel
    assert rep["chapters_total"] == 55
    assert rep["chapters_collated"] == 4  # the 4 calibration chapters
