"""Tests for scripts/core/manuscript_index.py.

A derived SQLite query layer over the manuscript witness JSONs — the
marathon's active data, which the existing `corpus_index.py` (notes-only)
does not cover. The witness corpus is ~20 files, so this index builds
on-demand in-memory (no lock/fingerprint/xdist machinery — that would be
over-engineering at this cardinality).

Core builder/query functions take an injected sqlite3 connection + plain
witness dicts, so tests need no filesystem.
"""

import sqlite3

W1 = {
    "witness": "GG",
    "book": "1ki",
    "chapter": 5,
    "source_images": ["GAPS/x/f030v.jpg"],
    "folio_sigla": ["f030v"],
    "verses": [
        {
            "v": 1,
            "column": "f030v-M-L23",
            "line_start": 23,
            "geez": "ወፈነሙ ፡ ኪራም",
            "tokens": ["ወፈነሙ", "ኪራም"],
            "uncertain": [
                {"token_index": 0, "marker": "uncertain", "note": "rubric-adjacent"},
                {"token_index": 1, "marker": "damaged", "note": "ink loss"},
            ],
        },
        {
            "v": 2,
            "column": "f030v-M-L24",
            "line_start": 24,
            "geez": "ንጉሥ ፡ ጢሮስ",
            "tokens": ["ንጉሥ", "ጢሮስ"],
            "uncertain": [],
        },
    ],
    "transcription_notes": "first draft",
}

W2 = {
    "witness": "CAM",
    "book": "1sa",
    "chapter": 2,
    "source_images": ["GAPS/y/f106r.jpg"],
    "folio_sigla": ["f106r"],
    "verses": [
        {
            "v": 1,
            "column": "f106r-L-L1",
            "line_start": 1,
            "geez": "ኪራም ፡ ለዳዊት",
            "tokens": ["ኪራም", "ለዳዊት"],
            "uncertain": [{"token_index": 0, "marker": "illegible", "note": "faded"}],
        }
    ],
    "transcription_notes": "",
}


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    return c


def test_build_index_populates_all_tables():
    from scripts.core.manuscript_index import build_index

    conn = _conn()
    build_index(conn, [W1, W2])
    assert conn.execute("SELECT COUNT(*) FROM witness").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM verse").fetchone()[0] == 3
    # tokens: 2+2+2 = 6
    assert conn.execute("SELECT COUNT(*) FROM token").fetchone()[0] == 6
    # uncertain: 2 + 0 + 1 = 3
    assert conn.execute("SELECT COUNT(*) FROM uncertain").fetchone()[0] == 3


def test_open_markers_all_and_filtered():
    from scripts.core.manuscript_index import build_index, open_markers

    conn = _conn()
    build_index(conn, [W1, W2])
    allm = open_markers(conn)
    assert len(allm) == 3
    # denormalized rows carry book/chapter/verse for cross-chapter triage
    assert {(r["book"], r["chapter"], r["v"], r["marker"]) for r in allm} == {
        ("1ki", 5, 1, "uncertain"),
        ("1ki", 5, 1, "damaged"),
        ("1sa", 2, 1, "illegible"),
    }
    dam = open_markers(conn, marker="damaged")
    assert len(dam) == 1 and dam[0]["marker"] == "damaged"


def test_marker_counts():
    from scripts.core.manuscript_index import build_index, marker_counts

    conn = _conn()
    build_index(conn, [W1, W2])
    counts = marker_counts(conn)
    assert counts == {"uncertain": 1, "damaged": 1, "illegible": 1}


def test_witness_coverage():
    from scripts.core.manuscript_index import build_index, witness_coverage

    conn = _conn()
    build_index(conn, [W1, W2])
    cov = witness_coverage(conn)
    rows = {(r["witness"], r["book"], r["chapter"], r["n_verses"]) for r in cov}
    assert rows == {("GG", "1ki", 5, 2), ("CAM", "1sa", 2, 1)}


def test_find_token_exact_across_witnesses():
    from scripts.core.manuscript_index import build_index, find_token

    conn = _conn()
    build_index(conn, [W1, W2])
    hits = find_token(conn, "ኪራም")  # appears in W1 v1 and W2 v1
    assert len(hits) == 2
    assert {h["book"] for h in hits} == {"1ki", "1sa"}


def test_build_index_skips_malformed_records():
    from scripts.core.manuscript_index import build_index

    conn = _conn()
    # a collation file or junk dict (no 'verses'/'witness') must be skipped,
    # not crash the build
    build_index(conn, [W1, {"not": "a witness"}, {"witness": "GG"}])
    assert conn.execute("SELECT COUNT(*) FROM witness").fetchone()[0] == 1


def test_dedupe_prefers_hires():
    from scripts.core.manuscript_index import dedupe_witnesses

    plain = {
        "witness": "CAM",
        "book": "1sa",
        "chapter": 1,
        "verses": [{"v": 1, "geez": "a", "tokens": ["a"], "uncertain": []}],
        "source_path": "/x/1sa1_witnessCAM.json",
    }
    hires = {
        "witness": "CAM",
        "book": "1sa",
        "chapter": 1,
        "verses": [
            {"v": 1, "geez": "a", "tokens": ["a"], "uncertain": []},
            {"v": 2, "geez": "b", "tokens": ["b"], "uncertain": []},
        ],
        "source_path": "/x/1sa1_witnessCAM_hires.json",
    }
    # order: plain first, hires second -> hires must win, count stays 1
    out = dedupe_witnesses([plain, hires])
    assert len(out) == 1
    assert "hires" in out[0]["source_path"]
    # GG and CAM of the same chapter are distinct keys (not collapsed)
    gg = {**plain, "witness": "GG", "source_path": "/x/1sa1_witnessGG.json"}
    out2 = dedupe_witnesses([plain, hires, gg])
    assert len(out2) == 2
