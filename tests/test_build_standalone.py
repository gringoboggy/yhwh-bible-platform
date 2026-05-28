import json
from pathlib import Path

import pytest

from scripts.core import translations as tx

REPO = Path(__file__).resolve().parent.parent
COLL = REPO / "content" / "manuscript" / "kings" / "collation"


class TestVersificationAttr:
    def test_parser_reads_own(self):
        assert tx._load_book_attr_from_text('VERSIFICATION = "own"\nVERSES = []', "VERSIFICATION") == "own"

    def test_parser_none_when_absent(self):
        assert tx._load_book_attr_from_text("VERSES = []", "VERSIFICATION") is None

    def test_parser_ignores_non_string(self):
        assert tx._load_book_attr_from_text("VERSIFICATION = 3\nVERSES = []", "VERSIFICATION") is None

    def test_versification_of_defaults_canonical(self):
        assert tx.versification_of("kjv", "gen") == "canonical"

    def test_versification_of_missing_book_is_canonical(self):
        assert tx.versification_of("kjv", "zzz") == "canonical"

    def test_psalms_is_own_versified(self):
        assert tx.versification_of("geez-tewahedo", "psa") == "own"


from scripts.core import standalone_store as ss


class TestStandaloneStore:
    def test_collation_to_entries_uses_own_numbering(self):
        coll = json.loads((COLL / "1ki6_collation_v2.json").read_text(encoding="utf-8"))
        verses, appmap = ss.collation_to_store_entries(coll)
        assert len(verses) == 33  # CAM's own sense-units, NOT 38 KJV
        assert verses[0] == (6, 1, coll["primary_verses"][0]["geez_text"])
        assert appmap["1"]["kjv"] == [["1ki", 6, 1]]  # v1 anchored to KJV 6:1
        assert appmap["1"]["confidence"] == "anchored"
        assert appmap["1"]["apparatus"]  # the GG-vs-CAM variant rows

    def test_build_book_store_writes_module_and_sidecar(self, tmp_path):
        paths = [COLL / f"1ki{n}_collation_v2.json" for n in range(1, 7)]
        res = ss.build_book_store("1ki", paths, tmp_path)
        assert res["book"] == "1ki" and res["chapters"] == 6 and res["verses"] > 0
        text = (tmp_path / "1ki.py").read_text(encoding="utf-8")
        verses = tx.load_book_verses_from_text(text)
        assert verses and all(len(t) == 3 for t in verses)
        assert tx._load_book_attr_from_text(text, "VERSIFICATION") == "own"
        am = json.loads((tmp_path / "1ki_apparatus.json").read_text(encoding="utf-8"))
        assert "6" in am and "1" in am["6"] and am["6"]["1"]["kjv"] == [["1ki", 6, 1]]
