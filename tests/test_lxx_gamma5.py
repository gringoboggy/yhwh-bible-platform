"""γ.5 — LXX (Septuagint Greek) translation pins.

Topic file (created alongside the γ.5 ship). The translation
system is filesystem-driven (`list_translations()` scans
`content/translations/`), so γ.5's contract is: the directory
exists, the meta file declares PD provenance, the gen.py
module parses, and the 3 seed verses are retrievable via the
existing API.

Coverage:
- TestGamma5LxxDirectoryLayout:    `content/translations/
  lxx-brenton-greek/` exists with `_meta.yaml` + `gen.py`.
- TestGamma5LxxMeta:               metadata declares the right
  id, title, license=PD, Brenton 1844 provenance.
- TestGamma5LxxDiscoverability:    `list_translations()` picks
  it up; `has_translation()` and `has_book()` both true.
- TestGamma5LxxSeedVerses:         the 3 canonical Genesis 1:1-3
  verses load correctly + contain Greek characters in the
  expected Unicode range (U+0370-U+03FF).
- TestGamma5LxxComposesWithGreekLookup: γ.5 + γ.2 compose —
  the LXX text contains Strong's-Greek-lookup-able words
  (we don't actually mine them here, just sanity-check that
  the Greek lemma surface is queryable via the existing API).

Pinning rationale: γ.5 is the first translation added since
KJV. Drift in the on-disk layout, the meta block, the verse
text, or the discovery contract would break the publisher's
ability to opt into LXX as a popup translation — and would
break the documented γ.5.x ETL handoff (which assumes this
seed shape).
"""

from __future__ import annotations


class TestGamma5LxxDirectoryLayout:
    """The directory structure mirrors KJV: `_meta.yaml` +
    per-book modules."""

    @classmethod
    def setup_class(cls):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        cls.dir = repo / "content" / "translations" / "lxx-brenton-greek"

    def test_translation_directory_exists(self):
        assert self.dir.is_dir(), f"missing translation dir at {self.dir}"

    def test_meta_yaml_exists(self):
        assert (self.dir / "_meta.yaml").is_file()

    def test_genesis_module_exists(self):
        assert (self.dir / "gen.py").is_file()


class TestGamma5LxxMeta:
    """Metadata declares the right id, license, and provenance."""

    @classmethod
    def setup_class(cls):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        meta_path = repo / "content" / "translations" / "lxx-brenton-greek" / "_meta.yaml"
        cls.meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))

    def test_id_is_lxx_brenton_greek(self):
        assert self.meta["id"] == "lxx-brenton-greek"

    def test_license_is_public_domain(self):
        # Buyer-facing claim is "free / unencumbered text". Pin
        # that the license stays PD — a copyright-restricted
        # translation would have to live under a different id.
        assert self.meta["license"] == "Public Domain", (
            f"license drift — expected Public Domain, got {self.meta.get('license')!r}"
        )

    def test_short_title_is_lxx(self):
        assert self.meta["short_title"] == "LXX"

    def test_source_cites_brenton_1844(self):
        source = self.meta.get("source") or {}
        # The PD basis is Brenton's 1844 edition. Pin the source
        # date (1844) and a Brenton mention somewhere in the
        # source block so a future contributor adding a copyright-
        # encumbered LXX (Rahlfs 1935, German Bible Society)
        # under this id has to update the test.
        assert source.get("source_date") == 1844, (
            f"source_date should be 1844 (Brenton); got {source.get('source_date')!r}"
        )
        package = source.get("package", "")
        publisher = source.get("publisher", "")
        assert "Brenton" in package or "Brenton" in publisher or "Bagster" in publisher, (
            f"source block missing Brenton / Bagster attribution: {source!r}"
        )

    def test_seed_stats_match_three_verses(self):
        # The seed is explicit: 1 book (Genesis), 3 verses (1:1-3).
        # Pin so a future contributor expanding the corpus updates
        # both the .py files AND the meta stats together.
        stats = self.meta.get("stats") or {}
        assert stats.get("books") == 1
        assert stats.get("verses") == 3


class TestGamma5LxxDiscoverability:
    """The discovery API surfaces LXX correctly."""

    def test_listed_in_translations(self):
        from scripts.core import translations as tx

        ids = tx.list_translations()
        assert "lxx-brenton-greek" in ids, f"LXX not discovered; got {ids}"

    def test_has_translation_returns_true(self):
        from scripts.core import translations as tx

        assert tx.has_translation("lxx-brenton-greek")

    def test_has_book_returns_true_for_genesis(self):
        from scripts.core import translations as tx

        assert tx.has_book("lxx-brenton-greek", "gen")

    def test_has_book_returns_false_for_unsupplied_books(self):
        # Seed is gen-only. Other OT books not yet seeded.
        from scripts.core import translations as tx

        for book in ("exo", "lev", "num", "deu", "psa"):
            assert not tx.has_book("lxx-brenton-greek", book), f"unexpected book {book!r} — seed should be Genesis only"

    def test_meta_api_returns_yaml_data(self):
        from scripts.core import translations as tx

        meta = tx.translation_meta("lxx-brenton-greek")
        assert meta is not None
        assert meta.get("id") == "lxx-brenton-greek"


class TestGamma5LxxSeedVerses:
    """The 3 seed verses (Gen 1:1-3) load correctly and contain
    legitimate Greek text."""

    @classmethod
    def setup_class(cls):
        from scripts.core import translations as tx

        cls.tx = tx

    def test_gen_1_1_text_present(self):
        v = self.tx.get_verse("lxx-brenton-greek", "gen", 1, 1)
        assert v is not None
        # Just check that it contains real Greek characters; the
        # exact text is pinned by the file itself + the canonical
        # opening "Ἐν ἀρχῇ" should appear.
        assert "Ἐν ἀρχῇ" in v, f"Gen 1:1 doesn't open with 'Ἐν ἀρχῇ': {v!r}"

    def test_gen_1_2_text_present(self):
        v = self.tx.get_verse("lxx-brenton-greek", "gen", 1, 2)
        assert v is not None
        # Brenton/LXX Gen 1:2 uses "ἀόρατος καὶ ἀκατασκεύαστος"
        # (invisible and unformed) — different from MT's
        # "tohu wabohu". Pin the distinctive LXX vocabulary.
        assert "ἀόρατος" in v, f"Gen 1:2 missing distinctive LXX vocabulary: {v!r}"

    def test_gen_1_3_text_present(self):
        v = self.tx.get_verse("lxx-brenton-greek", "gen", 1, 3)
        assert v is not None
        # "γενηθήτω φῶς" — "let there be light"
        assert "γενηθήτω" in v and "φῶς" in v

    def test_gen_chapter_returns_three_verses(self):
        ch = self.tx.get_chapter("lxx-brenton-greek", "gen", 1)
        assert len(ch) == 3, f"expected 3 verses in seed; got {len(ch)}"

    def test_unsupplied_verse_returns_none(self):
        # Gen 1:4 onwards isn't seeded yet (γ.5.x).
        v = self.tx.get_verse("lxx-brenton-greek", "gen", 1, 4)
        assert v is None

    def test_every_verse_contains_greek_unicode(self):
        # Belt-and-braces: every seed verse must contain at least
        # one character in the Greek Unicode block (U+0370-U+03FF
        # for Greek and Coptic; U+1F00-U+1FFF for polytonic
        # extended).
        for ch, vs in ((1, 1), (1, 2), (1, 3)):
            text = self.tx.get_verse("lxx-brenton-greek", "gen", ch, vs)
            has_greek = any((0x0370 <= ord(c) <= 0x03FF) or (0x1F00 <= ord(c) <= 0x1FFF) for c in (text or ""))
            assert has_greek, f"Gen {ch}:{vs} has no Greek characters: {text!r}"


class TestGamma5LxxComposesWithGreekLookup:
    """γ.5 + γ.2 compose: the LXX text contains words that have
    Strong's Greek entries; the existing /api/greek/<num> works
    against the underlying lexicon (γ.5 doesn't add new endpoints
    for this — it just makes the text available)."""

    def test_greek_lookup_api_still_works(self):
        # Defensive: confirm γ.2 + γ.5 don't conflict at module-
        # import time. The Greek lookup endpoint must keep
        # returning λόγος for G3056 even after the LXX is added.
        from scripts.api.greek import api_greek_lookup
        from scripts.core import sources

        # Cache-clear defense (per γ.2's pattern — chi1 may have
        # mutated cache earlier in the session).
        sources.strongs_greek.cache_clear()
        r = api_greek_lookup("G3056")
        assert r["status"] == "ok"
        assert r["lemma"] == "λόγος"

    def test_lxx_genesis_1_1_uses_greek_arche(self):
        # Gen 1:1's "Ἐν ἀρχῇ" is the same lemma as G746 (ἀρχή —
        # "beginning"). γ.5 + γ.2 composition opens the path to a
        # future γ.5.x feature where each LXX word in the popup
        # links to its Strong's Greek entry. This test pins
        # *that the underlying data exists* — not that the
        # linking is wired yet.
        from scripts.api.greek import api_greek_lookup
        from scripts.core import sources, translations as tx

        sources.strongs_greek.cache_clear()
        v = tx.get_verse("lxx-brenton-greek", "gen", 1, 1)
        assert "ἀρχῇ" in v, "Gen 1:1 doesn't contain 'ἀρχῇ' as expected"

        # And the corresponding Strong's entry must exist for the
        # future linking feature to have something to link to.
        r = api_greek_lookup("G746")
        assert r["status"] == "ok"
        assert "ἀρχή" in r["lemma"], f"G746's lemma should be ἀρχή; got {r['lemma']!r}"
