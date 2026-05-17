# tests/test_manuscript_collation.py
import importlib

mc = importlib.import_module("scripts.core.manuscript_collation")


class TestFoldAndClassify:
    def test_strict_identity_is_agree(self):
        assert mc.classify_pair("ዳዊት", "ዳዊት") == "agree"

    def test_skeleton_fold_diacritic_order(self):
        # same consonantal skeleton, different vowel order → skeleton-equal → agree
        assert mc.fold_skeleton("ሳሙኤል") == mc.fold_skeleton("ሳመኤል")
        assert mc.classify_pair("ሳሙኤል", "ሳመኤል") == "agree"

    def test_clearly_different_is_disagree(self):
        assert mc.classify_pair("ደቂቅ", "ውሉድ") == "disagree"

    def test_one_sided_row_is_disagree(self):
        assert mc.classify_pair("ዳዊት", "") == "disagree"
        assert mc.classify_pair("", "ዳዊት") == "disagree"

    def test_is_strict_identity_helper(self):
        assert mc.is_strict("ዳዊት", "ዳዊት") is True
        assert mc.is_strict("ሳሙኤል", "ሳመኤል") is False
        assert mc.is_strict("ዳዊት", "") is False
