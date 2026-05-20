"""Pre-screened C-2/C-5 self-check helper (audit U-belt 2026-05-20).

The transcriber subagent calls `screen_witness_for_class_failures(witness,
chapter_class)` on its own JSON output BEFORE returning. The helper flags
likely defects matching the documented systematic-failure-class patterns
(per `GG_topology.md` §2). Obvious patterns get one self-fix pass before
C-3/C-6 dispatch — saving an adversarial review round on the easy stuff.

Trades off precision for recall: better to flag a borderline case and have
the transcriber re-verify than to miss a real defect that costs a review
round. False-positive flags cost ~30 seconds; false-negatives cost ~30 min.
"""


class TestNonEthiopicScreen:
    """The screen ALWAYS flags non-Ethiopic contamination, regardless of
    chapter class — Latin / mojibake bytes are never legitimate body
    geez. Validates the screen reuses validate_witness's existing logic
    (single source of truth)."""

    def test_latin_f_flagged(self):
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        wit = {
            "verses": [
                {
                    "v": 1,
                    "geez": "ወብእሲf",
                    "tokens": ["ወብእሲf"],
                    "uncertain": [],
                }
            ],
        }
        flags = screen_witness_for_class_failures(wit, "NARRATIVE")
        assert any("non-Ethiopic" in f for f in flags), flags


class TestNarrativeClassScreens:
    """NARRATIVE chapters: the only class-specific pattern is body `❈`
    (rubric-cross used in body where `✣` is correct). Other systematic
    classes (`ለ`/`ስ` etc.) don't pattern-detect without parchment, so
    they're left to C-3 review even on NARRATIVE."""

    def test_body_knot_cross_flagged(self):
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        wit = {
            "verses": [
                {
                    "v": 1,
                    "geez": "ወብእሲ❈ዘእምነ",
                    "tokens": ["ወብእሲ❈ዘእምነ"],
                    "uncertain": [],
                }
            ],
        }
        flags = screen_witness_for_class_failures(wit, "NARRATIVE")
        assert any("knot-cross" in f.lower() or "❈" in f for f in flags)


class TestListClassScreens:
    """LIST chapters get ALL the screens from `GG_topology.md` §2."""

    def test_de_prefix_verb_flagged(self):
        """Standard ይ-prefix verbs (ይበል, ይትገበር, etc.) written with ደ.
        Heuristic: look for tokens starting with ደ followed by Ge'ez
        characters that pattern-match the standard Ge'ez verb-prefix
        forms. Conservative: flag any chapter-initial-occurring `ደ`-
        prefixed token whose body matches a known standard form."""
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        # ደሁዳ for Judah (canonical ይሁዳ) — should flag on LIST
        wit = {
            "verses": [
                {
                    "v": 14,
                    "geez": "በምድረ ደሁዳ",
                    "tokens": ["በምድረ", "ደሁዳ"],
                    "uncertain": [],
                }
            ],
        }
        flags = screen_witness_for_class_failures(wit, "LIST")
        assert any("ደሁዳ" in f or "ይ/ደ" in f for f in flags), flags

    def test_es_relative_pronoun_flagged(self):
        """እስ where standard relative pronoun is እለ."""
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        wit = {
            "verses": [
                {
                    "v": 21,
                    "geez": "እስ ይስሕቡ",
                    "tokens": ["እስ", "ይስሕቡ"],
                    "uncertain": [],
                }
            ],
        }
        flags = screen_witness_for_class_failures(wit, "LIST")
        assert any("እስ" in f and "እለ" in f for f in flags), flags

    def test_no_list_screens_on_narrative(self):
        """The LIST-specific screens should NOT fire on a NARRATIVE
        chapter — `እስ` may be legitimate in some narrative contexts and
        the false-positive cost on every narrative verse would be too
        high."""
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        wit = {
            "verses": [
                {
                    "v": 1,
                    "geez": "እስ ይስሕቡ",
                    "tokens": ["እስ", "ይስሕቡ"],
                    "uncertain": [],
                }
            ],
        }
        flags = screen_witness_for_class_failures(wit, "NARRATIVE")
        # NARRATIVE — only the body-❈ class fires; እስ stays for C-3
        assert not any("እስ" in f and "እለ" in f for f in flags), flags


class TestRegnalFrameScreens:
    """REGNAL_FRAME inherits all LIST screens — same fidel families, plus
    multi-glyph regnal numerals (currently no specific pattern beyond
    what LIST catches)."""

    def test_regnal_inherits_list(self):
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        wit = {
            "verses": [
                {
                    "v": 1,
                    "geez": "በሐደስ እስ ነግሠ",
                    "tokens": ["በሐደስ", "እስ", "ነግሠ"],
                    "uncertain": [],
                }
            ],
        }
        flags = screen_witness_for_class_failures(wit, "REGNAL_FRAME")
        # the እስ check fires (inherited from LIST)
        assert any("እስ" in f for f in flags), flags


class TestEmptyAndCleanWitness:
    def test_clean_narrative_no_flags(self):
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        wit = {
            "verses": [
                {
                    "v": 1,
                    "geez": "ወሀሎ ብእሲ ዘእምነ አርማቴም",
                    "tokens": ["ወሀሎ", "ብእሲ", "ዘእምነ", "አርማቴም"],
                    "uncertain": [],
                }
            ],
        }
        flags = screen_witness_for_class_failures(wit, "NARRATIVE")
        assert flags == []

    def test_clean_list_no_flags(self):
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        wit = {
            "verses": [
                {
                    "v": 1,
                    "geez": "ወሰሎምን ንጉሥ ላዕለ ኩሉ እስራኤል",
                    "tokens": ["ወሰሎምን", "ንጉሥ", "ላዕለ", "ኩሉ", "እስራኤል"],
                    "uncertain": [],
                }
            ],
        }
        flags = screen_witness_for_class_failures(wit, "LIST")
        assert flags == []

    def test_unknown_class_defaults_to_narrative(self):
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        wit = {"verses": [{"v": 1, "geez": "ወሀሎ", "tokens": ["ወሀሎ"], "uncertain": []}]}
        # Bogus class shouldn't raise — fall through to NARRATIVE
        flags = screen_witness_for_class_failures(wit, "UNKNOWN_CLASS")
        assert isinstance(flags, list)


class TestFlagShape:
    def test_flag_includes_verse_and_token(self):
        from scripts.core.manuscript_self_check import (
            screen_witness_for_class_failures,
        )

        wit = {
            "verses": [
                {
                    "v": 14,
                    "geez": "በምድረ ደሁዳ",
                    "tokens": ["በምድረ", "ደሁዳ"],
                    "uncertain": [],
                }
            ],
        }
        flags = screen_witness_for_class_failures(wit, "LIST")
        assert any("v14" in f for f in flags), flags
