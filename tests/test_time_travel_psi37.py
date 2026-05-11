"""ψ.37 time-traveling commentary — tests for the source-date catalogue
and lookup function. Topic file (created alongside the ψ.37-A
data-model ship, follows the ω.27 follow-on convention from earlier
this session).

Coverage:
- TestSourceDatesCatalogue:  the YAML loads cleanly, has the expected
  shape, and is sorted longest-prefix-first.
- TestLookupYear:            unit tests for the lookup function across
  every catalogued source family + the empty / unmatched cases.
- TestSourceDatesCorpusCoverage: integration smoke that ≥95% of the
  live corpus's notes resolve to a year (load-bearing demo
  invariant — if a future χ-cluster adds a major source without
  cataloguing it, this test fails loudly so source_dates.yaml
  gets updated alongside the data load).

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------- Phase ψ.37-A : source-date catalogue + lookup ------------


class TestSourceDatesCatalogue:
    """ψ.37-A: `content/source_dates.yaml` loads, has expected shape,
    and is ordered for longest-prefix-wins matching."""

    def test_yaml_loads_with_sources_key(self):
        from scripts.core.source_dates import load_source_dates

        sources = load_source_dates()
        assert isinstance(sources, list)
        assert len(sources) > 0
        # Every entry has prefix + year + label
        for s in sources:
            assert "prefix" in s, f"missing 'prefix': {s!r}"
            assert "year" in s, f"missing 'year': {s!r}"
            assert "label" in s, f"missing 'label': {s!r}"
            assert isinstance(s["year"], int)
            assert isinstance(s["prefix"], str) and s["prefix"]
            assert isinstance(s["label"], str) and s["label"]

    def test_catalogue_sorted_longest_prefix_first(self):
        # Defensive sort in load_source_dates() — verify it works
        # even if the YAML drifts to a different order.
        from scripts.core.source_dates import load_source_dates

        sources = load_source_dates()
        prefixes = [s["prefix"] for s in sources]
        # Each consecutive pair must satisfy len(a) >= len(b)
        for i in range(len(prefixes) - 1):
            assert len(prefixes[i]) >= len(prefixes[i + 1]), (
                f"catalogue not sorted longest-first at index {i}: "
                f"{prefixes[i]!r} (len {len(prefixes[i])}) precedes "
                f"{prefixes[i + 1]!r} (len {len(prefixes[i + 1])})"
            )

    def test_known_source_families_present(self):
        # Pin the 4 major source families the corpus relies on.
        from scripts.core.source_dates import load_source_dates

        prefixes = [s["prefix"] for s in load_source_dates()]
        # TSK (Treasury of Scripture Knowledge) — 1834
        assert any(p.startswith("Treasury of Scripture Knowledge") for p in prefixes), (
            "TSK prefix missing from catalogue"
        )
        # Strong's (covers both H and G entries) — 1890
        assert "Strong's " in prefixes, "Strong's prefix missing"
        # Nave's Topical — 1897
        assert "Nave's Topical Bible" in prefixes, "Nave's Topical prefix missing"


class TestLookupYear:
    """ψ.37-A: ``lookup_year`` returns the right circa-year for each
    real-corpus attribution prefix, and None for unmatched / empty."""

    def test_strongs_hebrew(self):
        from scripts.core.source_dates import lookup_year

        assert lookup_year("Strong's H136, A Concise Dictionary of the Words in the Hebrew Bible, James Strong") == 1890

    def test_strongs_greek(self):
        from scripts.core.source_dates import lookup_year

        assert (
            lookup_year("Strong's G2316, A Concise Dictionary of the Words in the Greek Testament, James Strong")
            == 1890
        )

    def test_tsk_with_year_suffix(self):
        from scripts.core.source_dates import lookup_year

        assert lookup_year("Treasury of Scripture Knowledge (1830s)") == 1834

    def test_tsk_bare(self):
        from scripts.core.source_dates import lookup_year

        # Bare TSK prefix (without the (1830s) tag) — same year.
        assert lookup_year("Treasury of Scripture Knowledge, R. A. Torrey") == 1834

    def test_naves_topical(self):
        from scripts.core.source_dates import lookup_year

        assert lookup_year("Nave's Topical Bible, Orville J. Nave") == 1897

    def test_kenyon_full(self):
        from scripts.core.source_dates import lookup_year

        assert lookup_year("Frederic G. Kenyon, Our Bible and the Ancient Manuscripts") == 1903

    def test_kenyon_truncated_prefix(self):
        from scripts.core.source_dates import lookup_year

        # The corpus has some attributions truncated to "Frederic G" —
        # the shorter prefix catches them.
        assert lookup_year("Frederic G") == 1903

    def test_user_original_unmatched(self):
        from scripts.core.source_dates import lookup_year

        # User-authored notes are NOT contemporary historical sources —
        # they have no circa-year and the build-pipeline filter
        # treats them as failing any historical ceiling.
        assert lookup_year("User original") is None

    def test_user_paraphrase_unmatched(self):
        from scripts.core.source_dates import lookup_year

        # User paraphrases reference ancient texts but are themselves
        # contemporary commentary.
        assert lookup_year("User paraphrase; references LXX") is None
        assert lookup_year("User paraphrase; references Augustine") is None
        assert lookup_year("User paraphrase; references 1 Enoch") is None

    def test_empty_attribution(self):
        from scripts.core.source_dates import lookup_year

        assert lookup_year("") is None

    def test_unknown_source(self):
        from scripts.core.source_dates import lookup_year

        # A future commentary not yet catalogued — returns None
        # (treated as contemporary by the build filter).
        assert lookup_year("Some Future Commentary, Smith 2026") is None

    def test_longest_prefix_wins(self):
        # The catalogue has both "Treasury of Scripture Knowledge"
        # AND "Treasury of Scripture Knowledge (1830s)". A
        # full-1830s attribution must hit the LONGER prefix's
        # entry (defensive contract — both happen to share year=1834,
        # so the behavior is observable only via load_source_dates'
        # ordering, but the contract holds).
        from scripts.core.source_dates import load_source_dates, lookup_year

        # Both entries exist with the same year
        catalogue = load_source_dates()
        long_entry = next(s for s in catalogue if s["prefix"] == "Treasury of Scripture Knowledge (1830s)")
        short_entry = next(s for s in catalogue if s["prefix"] == "Treasury of Scripture Knowledge")
        assert long_entry["year"] == short_entry["year"] == 1834
        # The longer-prefix entry comes first in the sorted catalogue
        long_idx = catalogue.index(long_entry)
        short_idx = catalogue.index(short_entry)
        assert long_idx < short_idx, "longest-prefix-first ordering broken"
        # And the lookup uses the longer prefix's match
        assert lookup_year("Treasury of Scripture Knowledge (1830s)") == 1834


class TestSourceDatesCorpusCoverage:
    """ψ.37-A: load-bearing demo invariant — ≥95% of the live
    corpus's notes must resolve to a year. If a future χ-cluster
    adds a major source without cataloguing it in source_dates.yaml,
    this test fails loudly so the catalogue gets updated."""

    @classmethod
    def setup_class(cls):
        # Walk the live corpus once; capture (total, matched) counts.
        from scripts.core.source_dates import lookup_year

        notes_dir = Path(__file__).resolve().parent.parent / "content" / "notes"
        total = 0
        matched = 0
        for p in sorted(notes_dir.glob("*.py")):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in tree.body:
                if not isinstance(node, ast.Assign):
                    continue
                for tgt in node.targets:
                    if not (isinstance(tgt, ast.Name) and tgt.id == "NOTES"):
                        continue
                    try:
                        notes = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        continue
                    for tup in notes:
                        if len(tup) >= 9:
                            total += 1
                            if lookup_year(tup[8] or "") is not None:
                                matched += 1
        cls.total = total
        cls.matched = matched
        cls.coverage = matched / total if total else 0.0

    def test_corpus_coverage_at_least_95_percent(self):
        # Today's corpus: 97.3% matched. A 95% floor gives headroom
        # for legitimate User-original growth before this fails.
        assert self.coverage >= 0.95, (
            f"source_dates.yaml covers only {self.coverage:.1%} of the "
            f"corpus ({self.matched:,} of {self.total:,} notes); expected "
            f">=95%. A major source family probably needs cataloguing in "
            f"content/source_dates.yaml."
        )

    def test_corpus_has_meaningful_size(self):
        # Pin that the test actually scanned a non-trivial corpus —
        # if total is tiny, coverage % could be misleading.
        assert self.total >= 25000, (
            f"corpus scan yielded only {self.total:,} notes; expected >=25K (the 2026-05-08 minimum corpus floor)"
        )


# ---------- Phase ψ.37-B : build-pipeline filter ---------------------


class TestComputeTimeFilteredHtmlRefIds:
    """ψ.37-B: the build-pipeline filter that drops notes whose
    source's circa-year > edition.time_filter_ceiling, AND drops
    contemporary content (lookup_year is None) when a ceiling is set.

    Empty / None / 0 ceiling → no-op (set is empty). §7.2 byte-
    identical guarantee preserved for pre-ψ.37 editions.
    """

    def test_no_filter_returns_empty_set(self):
        from scripts.build_edition import compute_time_filtered_html_ref_ids

        # Absent field
        assert compute_time_filtered_html_ref_ids({}) == set()
        # Explicit None
        assert compute_time_filtered_html_ref_ids({"time_filter_ceiling": None}) == set()
        # Empty string (defensive)
        assert compute_time_filtered_html_ref_ids({"time_filter_ceiling": ""}) == set()
        # Zero / negative
        assert compute_time_filtered_html_ref_ids({"time_filter_ceiling": 0}) == set()
        assert compute_time_filtered_html_ref_ids({"time_filter_ceiling": -5}) == set()

    def test_ceiling_drops_post_ceiling_content(self):
        # 1850 ceiling drops Strong's (1890), Nave's (1897), Kenyon
        # (1903), AND contemporary User-original / paraphrase (None).
        from scripts.build_edition import compute_time_filtered_html_ref_ids

        dropped = compute_time_filtered_html_ref_ids({"time_filter_ceiling": 1850})
        # Floor 10K gives meaningful headroom without locking in
        # exact counts that shift with corpus growth.
        assert len(dropped) >= 10000, f"1850 ceiling dropped only {len(dropped):,}; expected >=10K"

    def test_ceiling_keeps_pre_ceiling_content(self):
        # 2000 ceiling drops only contemporary (no historical year).
        # Today's corpus: 1,381 User-original / paraphrase notes.
        from scripts.build_edition import compute_time_filtered_html_ref_ids

        dropped = compute_time_filtered_html_ref_ids({"time_filter_ceiling": 2000})
        # Today's corpus has ~1,381 contemporary notes; floor 500
        # gives headroom while pinning the contract (something dropped).
        assert 500 <= len(dropped) <= 5000, (
            f"2000 ceiling dropped {len(dropped):,}; expected 500-5000 (only contemporary content should be filtered)"
        )

    def test_drop_set_monotonic_with_ceiling(self):
        # Lower ceiling → MORE notes dropped (sub/superset relationship).
        from scripts.build_edition import compute_time_filtered_html_ref_ids

        d_1900 = compute_time_filtered_html_ref_ids({"time_filter_ceiling": 1900})
        d_2000 = compute_time_filtered_html_ref_ids({"time_filter_ceiling": 2000})
        # Everything dropped at 2000 must also be dropped at 1900
        assert d_2000.issubset(d_1900), "drop set is not monotonic — 2000-drops not a subset of 1900-drops"
        # And 1900 drops strictly more than 2000 (Kenyon's 1903 entries)
        assert len(d_1900) > len(d_2000)


# ---------- Phase ψ.37-C : edition schema + API validation ----------


class TestApiSaveEditionTimeFilterCeiling:
    """ψ.37-C: `api_save_edition_meta` accepts and validates the
    `time_filter_ceiling` field. None / int in [1500, 2100] / "null"
    are accepted; anything else returns an error envelope.
    """

    def test_accepts_int_year(self, tmp_path):
        import shutil

        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.api.editions import api_save_edition_meta
            from scripts.core import config

            config.load_editions.cache_clear()
            r = api_save_edition_meta("catholic-study", {"time_filter_ceiling": 1900})
            assert r.get("ok"), r
            eds = {e["id"]: e for e in config.load_editions()}
            assert eds["catholic-study"]["time_filter_ceiling"] == 1900
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_accepts_none_to_clear_filter(self, tmp_path):
        import shutil

        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.api.editions import api_save_edition_meta
            from scripts.core import config

            config.load_editions.cache_clear()
            # Set then clear
            r = api_save_edition_meta("catholic-study", {"time_filter_ceiling": 1900})
            assert r.get("ok"), r
            r = api_save_edition_meta("catholic-study", {"time_filter_ceiling": None})
            assert r.get("ok"), r
            eds = {e["id"]: e for e in config.load_editions()}
            assert eds["catholic-study"].get("time_filter_ceiling") is None
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()

    def test_rejects_out_of_range(self):
        from scripts.api.editions import api_save_edition_meta

        r = api_save_edition_meta("catholic-study", {"time_filter_ceiling": 999})
        assert "error" in r
        assert "1500-2100" in r["error"]

        r = api_save_edition_meta("catholic-study", {"time_filter_ceiling": 2200})
        assert "error" in r
        assert "1500-2100" in r["error"]

    def test_rejects_non_integer(self):
        from scripts.api.editions import api_save_edition_meta

        r = api_save_edition_meta("catholic-study", {"time_filter_ceiling": "nineteen hundred"})
        assert "error" in r
        assert "integer year or null" in r["error"]

        r = api_save_edition_meta("catholic-study", {"time_filter_ceiling": [1900]})
        assert "error" in r

    def test_accepts_string_digit(self, tmp_path):
        # The UI may send "1900" as a string; coerce it.
        import shutil

        path = REPO_ROOT / "content" / "editions.yaml"
        backup = tmp_path / "editions.preserve.yaml"
        shutil.copy(path, backup)
        try:
            from scripts.api.editions import api_save_edition_meta
            from scripts.core import config

            config.load_editions.cache_clear()
            r = api_save_edition_meta("catholic-study", {"time_filter_ceiling": "1900"})
            assert r.get("ok"), r
            eds = {e["id"]: e for e in config.load_editions()}
            assert eds["catholic-study"]["time_filter_ceiling"] == 1900
        finally:
            shutil.copy(backup, path)
            from scripts.core import config

            config.load_editions.cache_clear()


# ---------- Phase ψ.37-D : /customize UI integration -----------------


class TestCustomizeUiTimeFilter:
    """ψ.37-D: the /customize UI surfaces `time_filter_ceiling` from
    api_customize_data and renders a year-ceiling dropdown with the
    expected slider positions.
    """

    def test_api_customize_data_exposes_time_filter_ceiling(self):
        from scripts.web import api_customize_data

        result = api_customize_data()
        # Every edition has the field, defaulting to None.
        for ed in result["editions"]:
            assert "time_filter_ceiling" in ed, f"edition {ed['id']!r} missing time_filter_ceiling key"
            # Value is None or an int (whatever's in editions.yaml).
            v = ed["time_filter_ceiling"]
            assert v is None or isinstance(v, int), (
                f"edition {ed['id']!r}: time_filter_ceiling is {v!r}, expected None or int"
            )

    def test_customize_html_contains_time_travel_section(self):
        from scripts.templates.customize import CUSTOMIZE_HTML

        # The collapsible section header
        assert "Time-traveling commentary" in CUSTOMIZE_HTML
        assert "time-travel-section" in CUSTOMIZE_HTML
        # The data-field attribute the JS reads
        assert 'data-field="time_filter_ceiling"' in CUSTOMIZE_HTML

    def test_customize_html_contains_expected_year_ceilings(self):
        from scripts.templates.customize import CUSTOMIZE_HTML

        # Each slider position the demo relies on
        for value in ("null", "2000", "1900", "1895", "1885", "1850", "1700", "1611"):
            assert f'value="{value}"' in CUSTOMIZE_HTML, f"option value={value!r} missing from /customize HTML"
        # User-facing labels for the demo's key positions
        assert "no limit" in CUSTOMIZE_HTML
        assert "King James era" in CUSTOMIZE_HTML

    def test_customize_html_has_explanation_paragraph(self):
        # The collapsible body should explain the feature so the
        # buyer isn't confused by an empty 1611 result.
        from scripts.templates.customize import CUSTOMIZE_HTML

        assert "first published" in CUSTOMIZE_HTML
        assert "Applies on next BUILD" in CUSTOMIZE_HTML
        assert "User-original" in CUSTOMIZE_HTML
