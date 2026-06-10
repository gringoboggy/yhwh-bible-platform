from scripts.core import manuscript_manifest as mm


def test_samuel_default_back_compat():
    mm.load_manifest.cache_clear()
    man = mm.load_manifest()  # no arg -> samuel (unchanged)
    assert "1sa" in man and "2sa" in man
    assert man["1sa"][1]["status"] == "calibrated"


def test_kings_track_loads_47_chapters():
    mm.load_manifest.cache_clear()
    man = mm.load_manifest(track="kings")
    # Durable structural contract (track parameterization, book set, chapter counts).
    assert set(man) == {"1ki", "2ki"}
    assert len(man["1ki"]) == 22 and len(man["2ki"]) == 25
    # State-aware: every chapter is in a valid state; pending+calibrated == 47 total
    # (no chapter stuck in a bad state), regardless of marathon progress.
    statuses = [man["1ki"][c]["status"] for c in range(1, 23)] + [man["2ki"][c]["status"] for c in range(1, 26)]
    assert all(s in {"pending", "calibrated"} for s in statuses)
    assert statuses.count("pending") + statuses.count("calibrated") == 47
    # 1ki:1 is the first chapter calibrated by the marathon; once done it stays calibrated — a positive regression pin.
    assert man["1ki"][1]["status"] == "calibrated"
    # 2ki:25 is the last chapter the marathon reaches, so pending for essentially its whole run — a regression tripwire, not a transient to be "fixed".
    assert man["2ki"][25]["status"] == "pending"


def test_chapter_entry_track_aware():
    mm.load_manifest.cache_clear()
    man = mm.load_manifest(track="kings")
    e = mm.chapter_entry(man, "1ki", 1)
    # chapter_entry contract: exactly these keys, status is a valid state.
    assert set(e) == {"GG", "CAM", "status"}
    assert e["status"] in {"pending", "calibrated"}
    # Generic per-status invariant across the whole 47-chapter marathon.
    # State-aware: branch on each chapter's status marker and assert that
    # branch's contract. round-7: a PENDING chapter may legitimately carry
    # PRE-STAGED folios (the standing "CAM/GG hi-res pre-pull of upcoming
    # chapters" side-task stages folios before calibration) — the old
    # pending⇒EMPTY assert was a "not-yet" pin the marathon outgrew. The
    # structural contract holds for every state; folios-populated is required
    # only once CALIBRATED.
    for book, n in (("1ki", 22), ("2ki", 25)):
        for c in range(1, n + 1):
            ce = mm.chapter_entry(man, book, c)
            assert set(ce) == {"GG", "CAM", "status"}
            assert set(ce["GG"]) == {"folios", "source_images"}
            assert set(ce["CAM"]) == {"folios", "views"}
            assert isinstance(ce["GG"]["folios"], list) and isinstance(ce["GG"]["source_images"], list)
            assert isinstance(ce["CAM"]["folios"], list) and isinstance(ce["CAM"]["views"], list)
            if ce["status"] != "pending":
                assert ce["status"] == "calibrated"
                assert ce["GG"]["folios"] and ce["GG"]["source_images"]
                assert ce["CAM"]["folios"] and ce["CAM"]["views"]
    # 1ki:1 is the first chapter calibrated by the marathon; once done it stays calibrated — a positive regression pin.
    pin = mm.chapter_entry(man, "1ki", 1)
    assert pin["status"] == "calibrated"
    assert pin["GG"]["folios"] and pin["CAM"]["folios"]
    # 2ki:25 is the last chapter the marathon reaches, so pending for essentially its whole run — a regression tripwire, not a transient to be "fixed". (Pre-staged folios are allowed; only the STATUS is pinned.)
    tail = mm.chapter_entry(man, "2ki", 25)
    assert tail["status"] == "pending"


def test_driver_kings_track_accounting():
    import scripts.run_manuscript_collation_at_scale as drv

    rep = drv.run(dry=True, track="kings")
    # Durable: track param honored -> 47 Kings chapters total.
    assert rep["chapters_total"] == 47
    # Accounting invariants that hold throughout the marathon.
    assert rep["chapters_pending"] + rep["chapters_collated"] == 47
    # Positive pin: 1ki:1 is calibrated+collatable now, so at least one collated.
    # (mint-9 #39: the prior `>= 0` line was redundant — this `>= 1` subsumes it.)
    assert rep["chapters_collated"] >= 1
    # Subset, not equality: a book drops out once all its chapters finish.
    assert {x["book"] for x in rep["pending_needs_transcription"]} <= {"1ki", "2ki"}


def test_driver_samuel_default_unchanged():
    import scripts.run_manuscript_collation_at_scale as drv

    rep = drv.run(dry=True)  # no track -> samuel
    assert rep["chapters_total"] == 55
    assert rep["chapters_collated"] == 4  # the 4 calibration chapters
