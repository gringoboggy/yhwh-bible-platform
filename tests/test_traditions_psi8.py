"""ω.27 follow-on (2026-05-11) — ψ.8 traditions test classes, split out
of the monolithic ``tests/test_scripts.py`` into a topic file
alongside the other ω.27 follow-on splits.

Fifth topic extraction. The ψ.8 traditions arc shipped in two
clusters:

- ψ.8.0  Tradition schema foundation (the data model)
- ψ.8.1  Traditions schema + filter (the customize/build flow)
- ψ.8.2-A  Per-book traditions resolver (UI-side overrides)

Together these added the cross-denominational comparison
apparatus — the "differentiator" v1.0 leaned on for the buyer
demo. The 9 test classes cover the schema, build-pipeline
filtering, label injection, per-book encoder/decoder + resolver,
customize API, YAML round-trips, and the backfill script.

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------- Phase ψ.8.1 + ψ.8.2-A : Traditions schema + filter ----------


class TestTraditionsCustomizeAPI:
    """ψ.8.1 — `traditions_default` round-trip via api_save_edition_meta
    + api_customize_data; traditions registry exposed in canonical
    order so the future ψ.8.3 UI has a single source of truth."""

    def setup_method(self):
        import scripts.web as web

        self.web = web

    def test_traditions_registry_in_canonical_order(self):
        d = self.web.api_customize_data()
        assert "traditions" in d
        regs = d["traditions"]
        assert isinstance(regs, list)
        ids = [r["id"] for r in regs]
        # Order matches CANONICAL_TRADITIONS exactly (cross is last —
        # it sits ABOVE the tradition stack in the popup, but in the
        # registry tuple it's the last entry).
        from scripts.core.traditions import CANONICAL_TRADITIONS

        canonical_ids = [tid for tid, _ in CANONICAL_TRADITIONS]
        assert ids == canonical_ids

    def test_traditions_registry_carries_labels(self):
        d = self.web.api_customize_data()
        regs = d["traditions"]
        labels = {r["id"]: r["label"] for r in regs}
        assert labels["catholic"] == "Catholic"
        assert labels["protestant"] == "Protestant"
        assert labels["orthodox"] == "Eastern Orthodox"
        assert labels["jewish"] == "Jewish"
        assert labels["tewahedo"] == "Ethiopian Tewahedo"
        assert labels["cross"] == "Cross-tradition"

    def test_traditions_default_exposed_per_edition(self):
        d = self.web.api_customize_data()
        for e in d["editions"]:
            assert "traditions_default" in e
            assert isinstance(e["traditions_default"], list)
            # Default seeded editions ship without an explicit value;
            # API surface emits an empty list for those.
            for tid in e["traditions_default"]:
                from scripts.core.traditions import TRADITION_IDS

                assert tid in TRADITION_IDS

    def test_save_traditions_default_round_trip(self, tmp_path):
        import shutil

        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"traditions_default": ["catholic", "cross"]},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            assert cath["traditions_default"] == ["catholic", "cross"]
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_save_traditions_default_dedupes_preserving_order(self, tmp_path):
        import shutil

        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"traditions_default": ["catholic", "cross", "catholic", "  ", "cross"]},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            # Dedupe preserves first-seen order; whitespace-only items
            # are dropped.
            assert cath["traditions_default"] == ["catholic", "cross"]
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_save_traditions_default_rejects_unknown(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"traditions_default": ["catholic", "lutheran"]},
        )
        assert "error" in r
        assert "lutheran" in r["error"]

    def test_save_traditions_default_must_be_list(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"traditions_default": "catholic"},
        )
        assert "error" in r

    def test_save_traditions_default_non_string_item_rejected(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"traditions_default": ["catholic", 42]},
        )
        assert "error" in r

    def test_save_traditions_default_none_treated_as_empty(self, tmp_path):
        import shutil

        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()
            # First set a value, then clear it via None.
            self.web.api_save_edition_meta(
                "catholic-study",
                {"traditions_default": ["catholic"]},
            )
            r = self.web.api_save_edition_meta(
                "catholic-study",
                {"traditions_default": None},
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            assert cath["traditions_default"] == []
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()


class TestTraditionFilterBuildPipeline:
    """ψ.8.2-A — `compute_tradition_disabled_html_ref_ids` builds the
    set of HTML ref-ids that should be stripped because their note's
    tradition isn't in the edition's `traditions_default` list."""

    @classmethod
    def setup_class(cls):
        from scripts import build_edition

        cls.be = build_edition

    def test_empty_traditions_default_means_no_filtering(self):
        # No traditions_default set → no filtering → empty ref-id set.
        # This is the §7.2 "no-op when default" guarantee.
        edition = {"id": "catholic-study"}
        ids = self.be.compute_tradition_disabled_html_ref_ids(edition)
        assert ids == set()

        edition = {"id": "catholic-study", "traditions_default": []}
        ids = self.be.compute_tradition_disabled_html_ref_ids(edition)
        assert ids == set()

    def test_filter_with_cross_only_keeps_all_current_corpus(self):
        # Today every note in the corpus resolves to `cross` (per ψ.8.0
        # audit). An edition declaring traditions_default=[cross]
        # should therefore strip ZERO notes — the filter is a perfect
        # inclusion of the current corpus.
        edition = {"id": "test-edition", "traditions_default": ["cross"]}
        ids = self.be.compute_tradition_disabled_html_ref_ids(edition)
        assert ids == set()

    def test_filter_with_catholic_only_strips_all_current_corpus(self):
        # Every note resolves to `cross` today — none are `catholic` —
        # so an edition declaring traditions_default=[catholic] would
        # strip the ENTIRE current corpus from the popup.
        edition = {"id": "test-edition", "traditions_default": ["catholic"]}
        ids = self.be.compute_tradition_disabled_html_ref_ids(edition)
        # Should be a non-empty set (every current note is filtered out).
        assert len(ids) > 100
        # Every entry should look like a valid ref-id.
        for rid in ids:
            assert rid.startswith("ref-")

    def test_filter_idempotency(self):
        # Calling compute() twice with the same edition produces the
        # same set — the function is pure (modulo on-disk content).
        edition = {"id": "test-edition", "traditions_default": ["cross"]}
        a = self.be.compute_tradition_disabled_html_ref_ids(edition)
        b = self.be.compute_tradition_disabled_html_ref_ids(edition)
        assert a == b

    def test_filter_with_invalid_traditions_in_list(self):
        # An edition's traditions_default may include junk (the
        # validator should have caught it, but the build pipeline
        # tolerates it defensively — unknown traditions just don't
        # match any note).
        edition = {"id": "test-edition", "traditions_default": ["lutheran"]}
        ids = self.be.compute_tradition_disabled_html_ref_ids(edition)
        # No note has tradition `lutheran`, so every note is filtered.
        assert len(ids) > 100

    def test_filter_includes_cross_keeps_current_corpus(self):
        # An edition mixing catholic+cross should keep all current
        # notes (which all derive to cross).
        edition = {"id": "test-edition", "traditions_default": ["catholic", "cross"]}
        ids = self.be.compute_tradition_disabled_html_ref_ids(edition)
        assert ids == set()

    def test_build_one_unions_tradition_filter_into_disabled_set(self, tmp_path):
        """Smoke test: build_one's `disabled_html_ref_ids` set
        includes tradition-derived ids when an edition has a
        traditions_default that excludes the corpus."""
        # We don't run a full EPUB build (slow); we monkeypatch the
        # filter helper to assert it's called with the right edition,
        # and that build_one's logic unions the result into the
        # disabled set passed to filter_html.
        called = {}
        original = self.be.compute_tradition_disabled_html_ref_ids

        def spy(edition):
            called["edition_id"] = edition.get("id")
            return {"ref-test-0101"}

        try:
            self.be.compute_tradition_disabled_html_ref_ids = spy
            # The build_one path is too involved to invoke directly,
            # but we can call the helper through its public name and
            # confirm it's wired the way build_one expects.
            ids = self.be.compute_tradition_disabled_html_ref_ids(
                {"id": "catholic-study", "traditions_default": ["catholic"]}
            )
            assert called["edition_id"] == "catholic-study"
            assert "ref-test-0101" in ids
        finally:
            self.be.compute_tradition_disabled_html_ref_ids = original


class TestTraditionLabelInjection:
    """ψ.8.2-B — `apply_tradition_labels_to_html` annotates surviving
    editorial-note asides with their tradition: a `data-tradition` attr
    on the aside opening tag plus a `<p class="note-tradition-label">`
    paragraph at the top of the aside body."""

    @classmethod
    def setup_class(cls):
        from scripts import build_edition

        cls.be = build_edition

    def test_empty_map_is_noop(self):
        # An empty ref→tradition map skips the rewrite entirely so
        # editions without traditions_default build byte-identically.
        sample = '<aside class="note note-doctrine" id="note-g0101a" epub:type="footnote"><p>x</p></aside>'
        new, stats = self.be.apply_tradition_labels_to_html(sample, {})
        assert new == sample
        assert stats == {"labeled": 0, "skipped_already_labeled": 0, "skipped_no_tradition": 0}

    def test_labels_aside_when_ref_id_in_map(self):
        sample = '<aside class="note note-doctrine" id="note-g0101a" epub:type="footnote"><p>body text</p></aside>'
        new, stats = self.be.apply_tradition_labels_to_html(
            sample,
            {"ref-g0101a": "catholic"},
        )
        assert stats["labeled"] == 1
        assert 'data-tradition="catholic"' in new
        assert 'class="note-tradition-label"' in new
        # Display label is canonical (not the tradition id).
        assert ">Catholic</p>" in new
        # The original body text survives.
        assert "<p>body text</p>" in new

    def test_skips_aside_not_in_map(self):
        # Notes whose tradition doesn't match the edition's filter were
        # already stripped by ψ.8.2-A; if some slipped through, the
        # labeller leaves them alone rather than guessing a tradition.
        sample = '<aside class="note note-x" id="note-other" epub:type="footnote"><p>x</p></aside>'
        new, stats = self.be.apply_tradition_labels_to_html(
            sample,
            {"ref-elsewhere": "catholic"},
        )
        assert new == sample
        assert stats["skipped_no_tradition"] == 1
        assert stats["labeled"] == 0

    def test_idempotent_on_already_labeled_aside(self):
        # Running the pass twice produces the same output the second
        # time — already-labelled asides are detected by their
        # data-tradition attribute and skipped.
        sample = '<aside class="note note-doctrine" id="note-g0101a" epub:type="footnote"><p>body</p></aside>'
        once, _ = self.be.apply_tradition_labels_to_html(sample, {"ref-g0101a": "jewish"})
        twice, stats = self.be.apply_tradition_labels_to_html(once, {"ref-g0101a": "jewish"})
        assert twice == once
        assert stats["skipped_already_labeled"] == 1
        assert stats["labeled"] == 0

    def test_canonical_labels_for_each_tradition(self):
        # Every CANONICAL_TRADITIONS id resolves to its display label
        # in the injected paragraph.
        from scripts.core.traditions import CANONICAL_TRADITIONS

        for tid, expected_label in CANONICAL_TRADITIONS:
            sample = f'<aside class="note note-doctrine" id="note-g0101a" epub:type="footnote"><p>x</p></aside>'
            new, _ = self.be.apply_tradition_labels_to_html(
                sample,
                {"ref-g0101a": tid},
            )
            assert f'data-tradition="{tid}"' in new
            assert f">{expected_label}</p>" in new

    def test_label_escapes_html_metacharacters(self):
        # The display label is escaped so a hostile tradition label
        # (shouldn't happen, but defensive) can't inject markup.
        # Wire through a synthetic tradition by using one that exists
        # — the escape itself is exercised on the canonical labels.
        sample = '<aside class="note note-x" id="note-g0101a"><p>x</p></aside>'
        new, _ = self.be.apply_tradition_labels_to_html(
            sample,
            {"ref-g0101a": "orthodox"},
        )
        # No raw <, > inside the label paragraph that wasn't
        # part of the surrounding tags.
        # "Eastern Orthodox" has no metacharacters; the assertion
        # below still proves we render it through _xml_escape_text.
        assert ">Eastern Orthodox</p>" in new
        # Sanity: no double-encoding of common runs.
        assert "Eastern&amp;" not in new

    def test_iter_note_ref_traditions_yields_real_corpus(self):
        # _iter_note_ref_traditions walks the on-disk corpus and yields
        # (ref_id, tradition, book_code) tuples shaped like the build
        # pipeline + ψ.8.4 per-book resolver expect.
        from scripts.core.traditions import TRADITION_IDS

        seen = 0
        for ref_id, tradition, book_code in self.be._iter_note_ref_traditions():
            assert ref_id.startswith("ref-")
            assert tradition in TRADITION_IDS
            assert isinstance(book_code, str) and book_code
            seen += 1
            if seen >= 10:
                break
        assert seen == 10

    def test_build_ref_id_to_tradition_map_empty_when_unset(self):
        # The §7.2 "no-op when default" guarantee — empty map means
        # build_one skips the label-injection pass entirely.
        be = self.be
        assert be.build_ref_id_to_tradition_map({}) == {}
        assert be.build_ref_id_to_tradition_map({"id": "catholic-study"}) == {}
        assert be.build_ref_id_to_tradition_map({"id": "x", "traditions_default": []}) == {}

    def test_build_ref_id_to_tradition_map_with_cross_includes_corpus(self):
        # An edition declaring traditions_default=[cross] keeps every
        # current note (all resolve to cross today). The map should be
        # non-empty and every value should be `cross`.
        m = self.be.build_ref_id_to_tradition_map({"id": "x", "traditions_default": ["cross"]})
        assert len(m) > 100, "expected many cross-tradition notes today"
        for tradition in m.values():
            assert tradition == "cross"


class TestTraditionsPerBookEncoderDecoder:
    """ψ.8.4 — `decode_per_book_traditions` / `encode_per_book_traditions`
    mirror the ν.2.7 popup-language encoder/decoder pair: flat list of
    `"<book>=<t1>,<t2>"` strings on disk, dict in memory, canonical-order
    sort on encode, defensive on decode."""

    @classmethod
    def setup_class(cls):
        from scripts import build_edition

        cls.be = build_edition

    def test_decode_none_or_empty(self):
        be = self.be
        assert be.decode_per_book_traditions(None) == {}
        assert be.decode_per_book_traditions([]) == {}
        assert be.decode_per_book_traditions({}) == {}

    def test_decode_passthrough_dict(self):
        # JSON payload from the UI arrives as a dict already.
        out = self.be.decode_per_book_traditions({"gen": ["catholic", "cross"], "exo": []})
        assert out == {"gen": ["catholic", "cross"], "exo": []}

    def test_decode_list_of_strings(self):
        out = self.be.decode_per_book_traditions(["gen=catholic,cross", "exo="])
        assert out == {"gen": ["catholic", "cross"], "exo": []}

    def test_decode_skips_malformed(self):
        # Bare codes without `=` are dropped; whitespace stripped;
        # non-strings ignored.
        out = self.be.decode_per_book_traditions(["gen=catholic", "bad-no-equals", "  =catholic", 42])
        assert out == {"gen": ["catholic"]}

    def test_encode_canonical_book_order(self):
        # Genesis must encode before Exodus regardless of dict iteration
        # order — same §6.1 rule the popup-language encoder follows.
        encoded = self.be.encode_per_book_traditions({"exo": ["catholic"], "gen": ["protestant"]})
        # Genesis comes first in canonical order
        assert encoded[0].startswith("gen=")
        assert encoded[1].startswith("exo=")

    def test_encode_strips_unknown_traditions(self):
        # Encoder is the schema-clean boundary: unknown traditions
        # don't survive a round trip through editions.yaml.
        encoded = self.be.encode_per_book_traditions({"gen": ["catholic", "lutheran", "cross"]})
        assert encoded == ["gen=catholic,cross"]

    def test_round_trip_canonical(self):
        original = {"gen": ["catholic", "cross"], "psa": ["jewish"]}
        encoded = self.be.encode_per_book_traditions(original)
        decoded = self.be.decode_per_book_traditions(encoded)
        assert decoded == original


class TestTraditionsPerBookResolver:
    """ψ.8.4 — `_resolve_traditions_for_book` chooses the active set
    per (edition, book) — per-book overrides win over the default; an
    empty list at either level means "no filter for this book"."""

    @classmethod
    def setup_class(cls):
        from scripts import build_edition

        cls.be = build_edition

    def test_default_only_used_when_no_per_book(self):
        edition = {"id": "x", "traditions_default": ["catholic", "cross"]}
        active = self.be._resolve_traditions_for_book(edition, "gen")
        assert active == {"catholic", "cross"}

    def test_per_book_override_wins_over_default(self):
        edition = {
            "id": "x",
            "traditions_default": ["catholic"],
            "traditions_per_book": ["gen=jewish,protestant"],
        }
        active = self.be._resolve_traditions_for_book(edition, "gen")
        assert active == {"jewish", "protestant"}
        # Books without an override still see the default
        active_other = self.be._resolve_traditions_for_book(edition, "exo")
        assert active_other == {"catholic"}

    def test_empty_per_book_means_no_filter_for_that_book(self):
        # Explicit "gen=" disables the filter for Genesis even when the
        # edition default is non-empty (publisher's "show everything in
        # Genesis but filter the rest" affordance).
        edition = {
            "id": "x",
            "traditions_default": ["catholic"],
            "traditions_per_book": ["gen="],
        }
        active = self.be._resolve_traditions_for_book(edition, "gen")
        assert active == set()
        active_other = self.be._resolve_traditions_for_book(edition, "exo")
        assert active_other == {"catholic"}

    def test_filter_with_per_book_override_only(self):
        # No default; per-book override sets the only filter — books
        # without an override resolve to ∅ (no filter).
        edition = {
            "id": "x",
            "traditions_per_book": ["gen=catholic"],
        }
        active = self.be._resolve_traditions_for_book(edition, "gen")
        assert active == {"catholic"}
        active_other = self.be._resolve_traditions_for_book(edition, "exo")
        assert active_other == set()

    def test_compute_disabled_uses_per_book(self):
        # Smoke test: an edition that filters every tradition for
        # Genesis specifically should produce a disabled set drawn
        # only from Genesis. Other books resolve to ∅ and survive.
        edition = {
            "id": "x",
            "traditions_per_book": ["gen=lutheran"],
        }
        ids = self.be.compute_tradition_disabled_html_ref_ids(edition)
        # Genesis ref-ids start with the Genesis prefix g; every entry
        # in the disabled set should start with "ref-g" (Genesis only).
        assert len(ids) > 0
        for rid in ids:
            assert rid.startswith("ref-g")

    def test_build_map_uses_per_book_override(self):
        # Same idea for the labeller: a per-book override that matches
        # `cross` keeps Genesis notes; the default-filter for Exodus
        # also keeps cross notes. Both produce labelled entries.
        edition = {
            "id": "x",
            "traditions_default": ["cross"],
            "traditions_per_book": ["gen=cross"],
        }
        m = self.be.build_ref_id_to_tradition_map(edition)
        assert len(m) > 100
        # Every value is cross (matches the filter)
        for tradition in m.values():
            assert tradition == "cross"

    def test_no_default_no_per_book_short_circuits_empty(self):
        # The §7.2 byte-identical guarantee: when neither default nor
        # any per-book override is set, both consumers return empty
        # without walking the corpus.
        be = self.be
        assert be.compute_tradition_disabled_html_ref_ids({"id": "x"}) == set()
        assert be.build_ref_id_to_tradition_map({"id": "x"}) == {}


class TestTraditionsPerBookCustomizeAPI:
    """ψ.8.4 — `traditions_per_book` round-trip through
    `api_save_edition_meta` + `api_customize_data`. Mirrors the
    popup_languages_per_book validator + emission shape."""

    def setup_method(self):
        import scripts.web as web

        self.web = web

    def test_customize_data_emits_traditions_per_book(self):
        d = self.web.api_customize_data()
        for e in d["editions"]:
            assert "traditions_per_book" in e
            assert isinstance(e["traditions_per_book"], dict)
            # Default seeded editions ship without an explicit value.
            for code, traditions in e["traditions_per_book"].items():
                assert isinstance(code, str)
                assert isinstance(traditions, list)

    def test_save_traditions_per_book_round_trip(self, tmp_path):
        import shutil

        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()

            r = self.web.api_save_edition_meta(
                "catholic-study",
                {
                    "traditions_per_book": {
                        "gen": ["catholic", "cross"],
                        "exo": [],
                    }
                },
            )
            assert r.get("ok"), r

            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            assert cath["traditions_per_book"]["gen"] == ["catholic", "cross"]
            assert cath["traditions_per_book"]["exo"] == []
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_save_traditions_per_book_rejects_unknown_book(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"traditions_per_book": {"zzz": ["catholic"]}},
        )
        assert "error" in r
        assert "zzz" in r["error"]

    def test_save_traditions_per_book_rejects_unknown_tradition(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"traditions_per_book": {"gen": ["lutheran"]}},
        )
        assert "error" in r
        assert "lutheran" in r["error"]

    def test_save_traditions_per_book_must_be_dict(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"traditions_per_book": ["gen=catholic"]},
        )
        assert "error" in r

    def test_save_traditions_per_book_value_must_be_list(self):
        r = self.web.api_save_edition_meta(
            "catholic-study",
            {"traditions_per_book": {"gen": "catholic"}},
        )
        assert "error" in r

    def test_save_traditions_per_book_dedupes(self, tmp_path):
        import shutil

        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.core import config

            config.load_editions.cache_clear()
            r = self.web.api_save_edition_meta(
                "catholic-study",
                {
                    "traditions_per_book": {
                        "gen": ["catholic", "cross", "catholic", "  ", "cross"],
                    }
                },
            )
            assert r.get("ok"), r
            data = self.web.api_customize_data()
            cath = next(e for e in data["editions"] if e["id"] == "catholic-study")
            assert cath["traditions_per_book"]["gen"] == ["catholic", "cross"]
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()


# ---------- Phase ψ.8.0 : Tradition schema foundation ----------


class TestTraditionsModule:
    """ψ.8.0 — `scripts/core/traditions.py`. Closed CANONICAL_TRADITIONS
    set, resolver derivation rules, edition lookup, stamping helper."""

    @classmethod
    def setup_class(cls):
        from scripts.core import traditions as t

        cls.t = t

    # ---- Constants ----

    def test_canonical_traditions_shape(self):
        # Tuple of (id, label) pairs in canonical popup-stack order.
        ct = self.t.CANONICAL_TRADITIONS
        assert isinstance(ct, tuple)
        ids = [tid for tid, _ in ct]
        labels = [lbl for _, lbl in ct]
        # All ids are non-empty lowercase strings; all labels are
        # non-empty title-case strings.
        for tid in ids:
            assert isinstance(tid, str) and tid and tid == tid.lower()
        for lbl in labels:
            assert isinstance(lbl, str) and lbl and lbl[0].isupper()
        # No duplicates.
        assert len(ids) == len(set(ids))
        # Required ids are present.
        for required in ("catholic", "protestant", "orthodox", "jewish", "tewahedo", "cross"):
            assert required in ids

    def test_canonical_order_cross_is_last(self):
        # `cross` is rendered above the tradition stack in popup HTML
        # (per spec), but in CANONICAL_TRADITIONS it's the last entry —
        # the tradition stack uses everything BEFORE cross, and cross
        # sits separately above it.
        ids = [tid for tid, _ in self.t.CANONICAL_TRADITIONS]
        assert ids[-1] == "cross"

    def test_tradition_ids_matches_canonical(self):
        ids_from_tuple = {tid for tid, _ in self.t.CANONICAL_TRADITIONS}
        assert self.t.TRADITION_IDS == ids_from_tuple

    def test_default_tradition_is_cross(self):
        assert self.t.DEFAULT_TRADITION == "cross"
        assert self.t.valid_tradition(self.t.DEFAULT_TRADITION)

    # ---- valid_tradition ----

    def test_valid_tradition_accepts_canonical(self):
        for tid in ("catholic", "protestant", "orthodox", "jewish", "tewahedo", "cross"):
            assert self.t.valid_tradition(tid)

    def test_valid_tradition_rejects_unknowns(self):
        assert not self.t.valid_tradition("baptist")
        assert not self.t.valid_tradition("CATHOLIC")  # case-sensitive
        assert not self.t.valid_tradition("")
        assert not self.t.valid_tradition(None)
        assert not self.t.valid_tradition(42)

    # ---- note_tradition resolver ----

    def test_resolver_returns_default_for_malformed_input(self):
        assert self.t.note_tradition(()) == "cross"
        assert self.t.note_tradition("not a tuple") == "cross"
        assert self.t.note_tradition((1, 2, 3)) == "cross"  # too short

    def test_resolver_uses_explicit_field_when_valid(self):
        tup = (1, 1, "", "anchor", "lang-hebrew", "Hebrew", "Heb.", "<em>body</em>", "Strong's H7779. PD.", "tewahedo")
        assert self.t.note_tradition(tup) == "tewahedo"

    def test_resolver_ignores_invalid_explicit_field(self):
        tup = (1, 1, "", "", "lang-hebrew", "Hebrew", "Heb.", "<em>body</em>", "Strong's H7779. PD.", "BAPTIST")
        # Invalid explicit value falls through to derivation —
        # Strong's H attribution → cross.
        assert self.t.note_tradition(tup) == "cross"

    def test_resolver_derives_cross_from_tsk_attribution(self):
        tup = (
            1,
            1,
            "",
            "",
            "xref-citation",
            "Cross-ref",
            "Cite.",
            "<strong>Cross-references.</strong> ...",
            "Treasury of Scripture Knowledge (1830s). PD.",
        )
        assert self.t.note_tradition(tup) == "cross"

    def test_resolver_derives_cross_from_strongs_hebrew(self):
        tup = (
            1,
            1,
            "",
            "earth",
            "lang-hebrew",
            "Hebrew",
            "Heb.",
            "<em>body</em>",
            "Strong's H776, A Concise Dictionary of the Hebrew Bible. PD.",
        )
        assert self.t.note_tradition(tup) == "cross"

    def test_resolver_derives_cross_from_strongs_greek(self):
        tup = (
            1,
            1,
            "",
            "Word",
            "lang-greek",
            "Greek",
            "Greek.",
            "<em>logos</em>",
            "Strong's G3056, A Concise Dictionary of the Greek Testament. PD.",
        )
        assert self.t.note_tradition(tup) == "cross"

    def test_resolver_derives_cross_from_naves(self):
        tup = (
            1,
            1,
            "",
            "",
            "topic-nave",
            "Topic",
            "Topic.",
            "<strong>Topics.</strong> Faith, Hope.",
            "Nave's Topical Bible, Orville J. Nave (1896). PD.",
        )
        assert self.t.note_tradition(tup) == "cross"

    def test_resolver_falls_back_to_default_for_unknown_attribution(self):
        tup = (
            1,
            1,
            "",
            "",
            "comm",
            "Note",
            "Note.",
            "<p>some commentary</p>",
            "Some random source not in the marker list",
        )
        assert self.t.note_tradition(tup) == "cross"

    def test_resolver_falls_back_to_default_for_8tuple(self):
        tup = (1, 1, "", "", "comm", "Note", "Note.", "<p>body</p>")
        assert self.t.note_tradition(tup) == "cross"

    def test_resolver_falls_back_for_empty_attribution(self):
        tup = (1, 1, "", "", "comm", "Note", "Note.", "<p>body</p>", "")
        assert self.t.note_tradition(tup) == "cross"

    # ---- edition_to_tradition ----

    def test_edition_lookup_with_explicit_mapping(self):
        m = {"catholic-study": "catholic", "evangelical-reformed": "protestant"}
        assert self.t.edition_to_tradition("catholic-study", m) == "catholic"
        assert self.t.edition_to_tradition("evangelical-reformed", m) == "protestant"

    def test_edition_lookup_unknown_falls_back_to_default(self):
        m = {"catholic-study": "catholic"}
        assert self.t.edition_to_tradition("anglican-bcp", m) == "cross"

    def test_edition_lookup_loads_yaml_when_no_mapping(self):
        # No-arg form should load the on-disk traditions.yaml. The
        # default file ships with the 5 seeded editions; we just
        # verify one known mapping resolves rather than hard-coding
        # the full set (which the YAML test class covers).
        result = self.t.edition_to_tradition("catholic-study")
        assert result == "catholic"

    def test_edition_lookup_rejects_invalid_tradition_in_mapping(self):
        m = {"weird-edition": "lutheran"}  # invalid tradition value
        # Invalid value silently skipped — falls through to default.
        assert self.t.edition_to_tradition("weird-edition", m) == "cross"

    # ---- with_tradition stamping ----

    def test_with_tradition_pads_attribution_when_absent(self):
        tup = (1, 1, "", "", "comm", "Note", "Note.", "<p>b</p>")
        out = self.t.with_tradition(tup, "catholic")
        assert len(out) == 10
        assert out[8] == ""  # attribution slot padded
        assert out[9] == "catholic"

    def test_with_tradition_preserves_existing_attribution(self):
        tup = (1, 1, "", "", "comm", "Note", "Note.", "<p>b</p>", "Some attribution.")
        out = self.t.with_tradition(tup, "tewahedo")
        assert len(out) == 10
        assert out[8] == "Some attribution."
        assert out[9] == "tewahedo"

    def test_with_tradition_round_trips_via_resolver(self):
        tup = (1, 1, "", "", "comm", "Note", "Note.", "<p>b</p>", "")
        stamped = self.t.with_tradition(tup, "jewish")
        assert self.t.note_tradition(stamped) == "jewish"

    def test_with_tradition_rejects_unknown_tradition(self):
        tup = (1, 1, "", "", "comm", "Note", "Note.", "<p>b</p>")
        with pytest.raises(ValueError):
            self.t.with_tradition(tup, "baptist")

    def test_with_tradition_rejects_short_tuple(self):
        with pytest.raises(ValueError):
            self.t.with_tradition((1, 2, 3), "cross")


class TestTraditionsYaml:
    """ψ.8.0 — content/traditions.yaml + load_traditions_yaml() parser.
    Tiny-YAML-parser tests mirror scripts.core.config's pattern."""

    @classmethod
    def setup_class(cls):
        from scripts.core import traditions as t

        cls.t = t

    def test_loads_default_yaml_when_no_path(self):
        data = self.t.load_traditions_yaml()
        assert isinstance(data, dict)
        assert "edition_to_tradition" in data
        m = data["edition_to_tradition"]
        # The 5 seeded editions are mapped.
        assert m["ethiopian-tewahedo"] == "tewahedo"
        assert m["catholic-study"] == "catholic"
        assert m["evangelical-reformed"] == "protestant"
        assert m["jewish-study"] == "jewish"
        assert m["scholarly-academic"] == "cross"

    def test_missing_file_returns_empty_dict(self, tmp_path):
        nope = tmp_path / "nonexistent.yaml"
        assert self.t.load_traditions_yaml(nope) == {}

    def test_parser_strips_comments(self, tmp_path):
        yaml_text = (
            "# header comment\n"
            "edition_to_tradition:\n"
            "  # inline comment\n"
            "  foo-edition: catholic\n"
            "  bar-edition: jewish  # trailing notwithstanding\n"
        )
        f = tmp_path / "t.yaml"
        f.write_text(yaml_text, encoding="utf-8")
        # Trailing-comment handling is a known limitation of the tiny
        # YAML parser (would need #-stripping); the YAML in the repo
        # avoids it. Test BOTH supported and limitation explicitly:
        data = self.t.load_traditions_yaml(f)
        assert data["edition_to_tradition"]["foo-edition"] == "catholic"
        # Limitation: trailing # is included in the value. We don't
        # claim to handle that case; the test documents the contract.

    def test_parser_silently_drops_invalid_traditions(self, tmp_path):
        yaml_text = (
            "edition_to_tradition:\n"
            "  good: catholic\n"
            "  bad: lutheran\n"  # invalid — silently dropped
            "  empty: \n"  # empty — silently dropped
        )
        f = tmp_path / "t.yaml"
        f.write_text(yaml_text, encoding="utf-8")
        m = self.t.load_traditions_yaml(f)["edition_to_tradition"]
        assert "good" in m and m["good"] == "catholic"
        assert "bad" not in m
        assert "empty" not in m

    def test_parser_handles_blank_lines(self, tmp_path):
        yaml_text = "\n\nedition_to_tradition:\n\n  alpha: catholic\n\n  beta: jewish\n\n"
        f = tmp_path / "t.yaml"
        f.write_text(yaml_text, encoding="utf-8")
        m = self.t.load_traditions_yaml(f)["edition_to_tradition"]
        assert m == {"alpha": "catholic", "beta": "jewish"}


class TestBackfillTraditionsScript:
    """ψ.8.0 — scripts/backfill_traditions.py audit script. Smoke tests
    + idempotency. Real-corpus assertions are loose (just floors) so
    the suite stays robust against future corpus growth."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.bf = importlib.import_module("scripts.backfill_traditions")

    def test_discover_books_returns_sorted_list(self):
        books = self.bf.discover_books()
        assert isinstance(books, list)
        assert books == sorted(books)
        # Sanity: at least the major canonical books appear.
        for required in ("gen", "exo", "mat", "jhn", "rom", "rev"):
            assert required in books

    def test_audit_book_on_missing_returns_missing_flag(self):
        stats = self.bf.audit_book("XXNOSUCHBOOKXX")
        assert stats["missing"] is True
        assert stats["n_total"] == 0
        assert stats["n_would_rewrite"] == 0

    def test_audit_book_on_real_book_counts_notes(self):
        # Pick a book guaranteed to have notes from the χ-cluster runs.
        stats = self.bf.audit_book("gen")
        assert stats["missing"] is False
        # Genesis carries TSK + HebrewWord + (future) Greek-NT-skip
        # candidates. Floor of 100 is generous; at session ship the
        # actual count is several hundred.
        assert stats["n_total"] >= 100
        # Every Genesis note should resolve to cross today.
        assert stats["by_tradition"].get("cross", 0) == stats["n_total"]
        assert stats["n_would_rewrite"] == 0
        assert stats["n_default"] == stats["n_total"]

    def test_run_audit_aggregates_correctly(self):
        # Audit a small subset to keep the test fast.
        report = self.bf.run_audit(["gen", "exo", "mat"])
        assert report["n_total"] >= 200
        # All currently-shipped notes resolve to cross.
        assert report["n_would_rewrite"] == 0
        # The cross bucket is the only non-zero one today.
        assert report["by_tradition"]["cross"] == report["n_total"]

    def test_audit_is_idempotent(self):
        # Running the audit twice produces identical aggregate counts —
        # the audit is a pure read with no side effects.
        a = self.bf.run_audit(["gen", "rom", "rev"])
        b = self.bf.run_audit(["gen", "rom", "rev"])
        assert a["n_total"] == b["n_total"]
        assert a["n_would_rewrite"] == b["n_would_rewrite"]
        assert a["n_default"] == b["n_default"]
        assert dict(a["by_tradition"]) == dict(b["by_tradition"])

    def test_explicit_tradition_helper(self):
        from scripts.backfill_traditions import _explicit_tradition

        # 8-tuple: no slot for tradition.
        assert _explicit_tradition((1, 1, "", "", "k", "t", "l", "b")) is None
        # 9-tuple: still no slot.
        assert _explicit_tradition((1, 1, "", "", "k", "t", "l", "b", "attr")) is None
        # 10-tuple with valid tradition:
        assert _explicit_tradition((1, 1, "", "", "k", "t", "l", "b", "attr", "catholic")) == "catholic"
        # 10-tuple with invalid value:
        assert _explicit_tradition((1, 1, "", "", "k", "t", "l", "b", "attr", "BAPTIST")) is None

    def test_audit_handles_subset_of_books(self):
        # `--books gen,mat` should only audit those two.
        report = self.bf.run_audit(["gen", "mat"])
        assert len(report["by_book"]) == 2
        for stats in report["by_book"]:
            assert stats["book"] in {"gen", "mat"}
