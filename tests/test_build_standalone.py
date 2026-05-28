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
