"""§4.3 verse-popup witnesses — drop the duplicative/mismatched English KJV from
the default popups + widen the default witness set to Hebrew + Greek (LXX + NT)
+ Latin + Arabic. jps / douay / brenton-en stay available, off by default.

Per spec §12.3 this is an editions.yaml + build-fallback change, NOT a
generate_verse_popups change: the base bakes ALL witnesses; the per-edition
build PRUNES via build_edition._resolve_popup_languages reading
popup_languages_default (and the unset-default fallback). No base re-bake.
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DEFAULT = {"wlc", "lxx-greek", "greek-nt", "vulgate", "arabic"}
STANDARD_EDITIONS = (
    "ethiopian-tewahedo",
    "catholic-study",
    "evangelical-reformed",
    "jewish-study",
    "scholarly-academic",
    "eastern-orthodox",
    "anglican-bcp",
    "lutheran-confessional",
    "coptic-orthodox",
)


class TestDefaultWitnessConstant:
    def test_drops_kjv_and_is_the_five_witnesses(self):
        from scripts.core.popup_versions import DEFAULT_POPUP_WITNESSES

        assert set(DEFAULT_POPUP_WITNESSES) == DEFAULT
        assert "kjv" not in DEFAULT_POPUP_WITNESSES


class TestResolveDropsKjvAndWidens:
    def test_every_standard_edition_drops_kjv_and_carries_the_five(self):
        from scripts.build_edition import _resolve_popup_languages

        config.load_editions.cache_clear()
        eds = config.editions_by_id()
        for eid in STANDARD_EDITIONS:
            langs = _resolve_popup_languages(eds[eid], "gen")
            assert "kjv" not in langs, f"{eid} still resolves the English KJV into popups"
            assert DEFAULT <= langs, f"{eid} missing a default witness: {sorted(DEFAULT - langs)}"

    def test_standalone_bibles_keep_no_interlanguage_popups(self):
        # The two standalone Bibles use popup_translation for their EN
        # back-translation, NOT inter-language popups (project_parallel_bible).
        from scripts.build_edition import _resolve_popup_languages

        config.load_editions.cache_clear()
        eds = config.editions_by_id()
        for eid in ("standalone-geez", "standalone-amharic"):
            assert _resolve_popup_languages(eds[eid], "gen") == set()


class TestUnsetFallback:
    def test_unset_default_returns_five_witnesses_no_kjv(self):
        from scripts.build_edition import _resolve_popup_languages

        langs = _resolve_popup_languages({"id": "synthetic-no-default"}, "gen")
        assert langs == DEFAULT


def _vnlink(book, ch, vs):
    return (
        f'<a class="vn-link" id="v-{book}-{ch}-{vs}" href="#vnote-{book}-{ch}-{vs}" '
        f'epub:type="noteref" title="{book} {ch}:{vs}"><span class="vn">{vs}</span></a>'
    )


def _vnote(book, ch, vs, witnesses):
    paras = "".join(f'<p class="{cc}">{txt}</p>' for cc, txt in witnesses.items())
    return (
        f'<aside class="vnote" id="vnote-{book}-{ch}-{vs}" epub:type="footnote">'
        f"<p><strong>{book} {ch}:{vs}.</strong></p>{paras}"
        f'<p><a href="#v-{book}-{ch}-{vs}" class="vnote-back">↩</a></p></aside>'
    )


class TestKjvFallbackWhenNoOriginalWitness:
    """The popups reached 90.5% coverage via a KJV floor, so ~6% of verses carry
    ONLY the English KJV. Dropping kjv there would empty the popup AND break any
    note cross-ref that targets that vnote (epubcheck RSC-012). So when a verse
    has no active original-language witness, the English is KEPT as a last
    resort; where a real witness exists, the redundant English is dropped."""

    def _run(self):
        from scripts.build_edition import _apply_popup_languages_and_translation

        edition = {"id": "x", "popup_languages_default": list(DEFAULT)}
        html = (
            _vnlink("gen", 1, 1)
            + _vnlink("gen", 1, 2)
            + '<aside class="notes-section">'
            + _vnote("gen", 1, 1, {"vnote-text": "kjv only — no original"})
            + _vnote("gen", 1, 2, {"vnote-text": "kjv", "vnote-hebrew": "<em>בְּרֵאשִׁית</em>"})
            + "</aside>"
        )
        return _apply_popup_languages_and_translation(html, edition, "", "")

    def _segment(self, out, vid):
        return out.split(f'id="{vid}"', 1)[1].split("</aside>", 1)[0]

    def test_kjv_only_verse_keeps_english_and_stays_clickable(self):
        out, stats = self._run()
        assert 'id="vnote-gen-1-1"' in out  # popup kept (a valid cross-ref target)
        assert 'class="vnote-text"' in self._segment(out, "vnote-gen-1-1")  # not empty
        assert '<a class="vn-link" id="v-gen-1-1"' in out  # still clickable
        assert stats["kjv_fallbacks"] == 1

    def test_redundant_english_dropped_where_a_real_witness_exists(self):
        out, _ = self._run()
        seg = self._segment(out, "vnote-gen-1-2")
        assert 'class="vnote-hebrew"' in seg  # the Hebrew witness kept
        assert 'class="vnote-text"' not in seg  # the redundant English dropped


class TestOptInWitnessesStillAvailable:
    def test_jps_douay_brenton_resolvable_but_not_default(self):
        from scripts.core.popup_versions import DEFAULT_POPUP_WITNESSES, resolve_version_id

        for opt in ("jps", "douay", "brenton-en"):
            assert resolve_version_id(opt) == opt  # still a real, selectable witness
            assert opt not in DEFAULT_POPUP_WITNESSES  # just not on by default
