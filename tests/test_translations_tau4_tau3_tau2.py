"""τ.4 + τ.3 + τ.2 — Brenton-LXX English + Vulgate Latin +
Douay-Rheims English seeds (2026-05-12).

Three translations shipped together as the SESSION_END_2026-05-12
§4 N+2/N+3/N+4 sequence. All follow the γ.5 / τ.5-A seed pattern
(3-verse Genesis + extract_translation.py registry entry; full
ingest deferred to τ.x.x user-side).

Coverage per translation:
- Registry pinning (TRANSLATIONS entry shape + PD-basis docs).
- Discovery (list_translations / has_translation / has_book).
- Seed content (Genesis 1:1-3 with translation-specific phrasing
  pins so future swaps are caught as deliberate changes).
- Meta shape (id / short_title / license / source_date pinned).

After this ship, the project ships seeds for 7 translations:
kjv (full), jps + wlc + lxx-brenton-greek + lxx-brenton-english +
vulgate-clementine + douay-rheims (all 3-verse Gen 1:1-3 seeds).
This closes the SESSION_END §4 first wave; remaining τ-cluster
work (τ.5-B WLC-unpointed, τ.6 Ge'ez, τ.7 GNT, τ.8 Geneva, etc.)
continues in subsequent sessions.

Pinning rationale: each seed has translation-specific lexical
choices that mark its tradition. JPS uses "unformed and void" (vs
KJV "without form, and void"). DRA uses "Be light made" (vs KJV
"Let there be light"). Vulgate uses "Fiat lux" (the lexical
ancestor). These pins catch silent regression if a future
contributor swaps in different source text.
"""

from __future__ import annotations


# --------------------------------------------------------------------
# τ.4 — Brenton LXX English (lxx-brenton-english)
# --------------------------------------------------------------------


class TestTau4Registry:
    def test_registered(self):
        from scripts.extract_translation import TRANSLATIONS

        assert "lxx-brenton-english" in TRANSLATIONS
        entry = TRANSLATIONS["lxx-brenton-english"]
        assert entry["short_title"] == "LXX-Eng"
        assert entry["license"] == "Public Domain"
        # Brenton 1844 + Brenton died 1862 → unambiguously PD.
        assert entry["source"]["source_date"] == 1844

    def test_notes_reference_brenton_greek_pair(self):
        from scripts.extract_translation import TRANSLATIONS

        entry = TRANSLATIONS["lxx-brenton-english"]
        # The pair-with-greek-side documentation is important; pin it.
        assert "lxx-brenton-greek" in entry["notes"]


class TestTau4Discovery:
    def test_in_list_translations(self):
        from scripts.core import translations

        assert "lxx-brenton-english" in translations.list_translations()

    def test_has_translation(self):
        from scripts.core import translations

        assert translations.has_translation("lxx-brenton-english") is True

    def test_has_book_gen(self):
        from scripts.core import translations

        assert translations.has_book("lxx-brenton-english", "gen") is True


class TestTau4Seed:
    def test_three_verses(self):
        from scripts.core import translations

        assert translations.book_verse_count("lxx-brenton-english", "gen") == 3

    def test_gen_1_1_brenton_phrasing(self):
        # Brenton renders ἐποίησεν as "made" (KJV uses "created"
        # for ברא in the MT Hebrew). This lexical choice marks
        # Brenton-English vs KJV — pin it.
        from scripts.core import translations

        v = translations.get_verse("lxx-brenton-english", "gen", 1, 1)
        assert v == "In the beginning God made the heaven and the earth."

    def test_gen_1_2_unsightly_and_unfurnished(self):
        # Brenton's distinctive rendering of ἀόρατος καὶ ἀκατασκεύαστος —
        # the LXX's translation of MT's tohu wa-bohu. Pin both adjectives.
        from scripts.core import translations

        v = translations.get_verse("lxx-brenton-english", "gen", 1, 2)
        assert "unsightly and unfurnished" in v

    def test_meta_short_title(self):
        from scripts.core import translations

        meta = translations.translation_meta("lxx-brenton-english")
        assert meta is not None
        assert meta["short_title"] == "LXX-Eng"


# --------------------------------------------------------------------
# τ.3 — Clementine Vulgate Latin (vulgate-clementine)
# --------------------------------------------------------------------


class TestTau3Registry:
    def test_registered(self):
        from scripts.extract_translation import TRANSLATIONS

        assert "vulgate-clementine" in TRANSLATIONS
        entry = TRANSLATIONS["vulgate-clementine"]
        assert entry["short_title"] == "Vulgate"
        assert entry["license"] == "Public Domain"
        # 1592 Clementine edition + Jerome died 420 AD → PD by age.
        assert entry["source"]["source_date"] == 1592

    def test_notes_distinguish_from_modern_vulgates(self):
        # The notes should clearly distinguish the Clementine (PD)
        # from Stuttgart and Nova Vulgata (NOT PD).
        from scripts.extract_translation import TRANSLATIONS

        entry = TRANSLATIONS["vulgate-clementine"]
        assert "Stuttgart" in entry["notes"] or "Weber-Gryson" in entry["notes"]


class TestTau3Discovery:
    def test_in_list_translations(self):
        from scripts.core import translations

        assert "vulgate-clementine" in translations.list_translations()


class TestTau3Seed:
    def test_three_verses(self):
        from scripts.core import translations

        assert translations.book_verse_count("vulgate-clementine", "gen") == 3

    def test_gen_1_1_in_principio(self):
        # The Vulgate's canonical opening. Pin verbatim.
        from scripts.core import translations

        v = translations.get_verse("vulgate-clementine", "gen", 1, 1)
        assert v == "In principio creavit Deus caelum et terram."

    def test_gen_1_3_fiat_lux(self):
        # Pin the most famous Latin Bible quotation. This is the
        # canonical Clementine phrasing.
        from scripts.core import translations

        v = translations.get_verse("vulgate-clementine", "gen", 1, 3)
        assert "Fiat lux" in v
        assert "Et facta est lux" in v

    def test_gen_1_2_spiritus_dei(self):
        # The Latin "Spiritus Dei ferebatur super aquas" — distinctive
        # rendering of the Hebrew ruach Elohim.
        from scripts.core import translations

        v = translations.get_verse("vulgate-clementine", "gen", 1, 2)
        assert "Spiritus Dei" in v
        assert "super aquas" in v

    def test_meta_short_title(self):
        from scripts.core import translations

        meta = translations.translation_meta("vulgate-clementine")
        assert meta is not None
        assert meta["short_title"] == "Vulgate"


# --------------------------------------------------------------------
# τ.2 — Douay-Rheims English (douay-rheims)
# --------------------------------------------------------------------


class TestTau2Registry:
    def test_registered(self):
        from scripts.extract_translation import TRANSLATIONS

        assert "douay-rheims" in TRANSLATIONS
        entry = TRANSLATIONS["douay-rheims"]
        assert entry["short_title"] == "DRA"
        assert entry["license"] == "Public Domain"
        # 1899 John Murphy Challoner-revision reprint.
        assert entry["source"]["source_date"] == 1899

    def test_notes_reference_vulgate_pair(self):
        from scripts.extract_translation import TRANSLATIONS

        entry = TRANSLATIONS["douay-rheims"]
        # DRA + Vulgate-Clementine ship as the Catholic-tradition pair.
        assert "vulgate-clementine" in entry["notes"].lower()


class TestTau2Discovery:
    def test_in_list_translations(self):
        from scripts.core import translations

        assert "douay-rheims" in translations.list_translations()


class TestTau2Seed:
    def test_three_verses(self):
        from scripts.core import translations

        assert translations.book_verse_count("douay-rheims", "gen") == 3

    def test_gen_1_1_dra_phrasing(self):
        # DRA's distinctive "created heaven, and earth" — note the
        # comma and the lack of "the heavens" plural. Tracks the
        # singular "caelum" from the Vulgate.
        from scripts.core import translations

        v = translations.get_verse("douay-rheims", "gen", 1, 1)
        assert v == "In the beginning God created heaven, and earth."

    def test_gen_1_3_be_light_made(self):
        # The famously archaic DRA rendering of Fiat lux. Pin
        # verbatim — this is the verse that marks the translation
        # tradition.
        from scripts.core import translations

        v = translations.get_verse("douay-rheims", "gen", 1, 3)
        assert v == "And God said: Be light made. And light was made."

    def test_gen_1_2_void_and_empty(self):
        # DRA "void and empty" (vs KJV "without form, and void").
        # DRA tracks the Vulgate's "inanis et vacua".
        from scripts.core import translations

        v = translations.get_verse("douay-rheims", "gen", 1, 2)
        assert "void and empty" in v

    def test_meta_short_title(self):
        from scripts.core import translations

        meta = translations.translation_meta("douay-rheims")
        assert meta is not None
        assert meta["short_title"] == "DRA"


# --------------------------------------------------------------------
# Joint coverage — all three plus the τ.5-A pair = 4 sessions of work
# --------------------------------------------------------------------


class TestJointCoverage:
    """Post-SESSION_END §4 first-wave shipping state."""

    def test_seven_translations_now_registered(self):
        from scripts.core import translations

        # τ.4 + τ.3 + τ.2 + τ.5-A (jps+wlc) + γ.5 (lxx-brenton-greek) +
        # τ.1 (kjv) = 7. Pin so subsequent τ-cluster ships are visible
        # at the test-count layer.
        ids = set(translations.list_translations())
        expected = {
            "kjv",
            "jps",
            "wlc",
            "lxx-brenton-greek",
            "lxx-brenton-english",
            "vulgate-clementine",
            "douay-rheims",
        }
        assert expected.issubset(ids), f"missing: {expected - ids}"

    def test_genesis_1_2_three_traditions_distinct(self):
        # Sanity: the Reformation Protestant (KJV), Jewish (JPS),
        # and Catholic (DRA) traditions render the second verse
        # distinctively (KJV "without form, and void"; JPS
        # "unformed and void"; DRA "void and empty"). Catches
        # accidental copy-paste between seeds. (Note: KJV and JPS
        # happen to agree verbatim on Gen 1:1 — both render
        # "heaven" singular following Hebrew shamayim — so the
        # divergence test uses verse 2.)
        from scripts.core import translations

        kjv = translations.get_verse("kjv", "gen", 1, 2)
        jps = translations.get_verse("jps", "gen", 1, 2)
        dra = translations.get_verse("douay-rheims", "gen", 1, 2)
        assert kjv != jps, "KJV and JPS should diverge in Gen 1:2"
        assert kjv != dra, "KJV and DRA should diverge in Gen 1:2"
        assert jps != dra, "JPS and DRA should diverge in Gen 1:2"

    def test_clementine_and_dra_pair_traceable(self):
        # The Vulgate's "Fiat lux" should be visibly the ancestor of
        # DRA's "Be light made" — pin both presences side-by-side.
        from scripts.core import translations

        vg = translations.get_verse("vulgate-clementine", "gen", 1, 3)
        dra = translations.get_verse("douay-rheims", "gen", 1, 3)
        assert "Fiat lux" in vg
        assert "Be light made" in dra
