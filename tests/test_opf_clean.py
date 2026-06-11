"""Phase 4.5 (decommercialize) — OPF cleanliness guard.

The 2026-05-14 free-public pivot dropped retail identifiers (ISBN); Phase 4
removed the last academic/retail OPF metadata scaffolding too — the DOI hook,
the LCCN hook, and their ``onix:codelist5`` identifier-type refinements. The
generated ``content.opf`` now carries exactly ONE ``dc:identifier``: the
deterministic generator URN ``urn:yhwh:edition:<id>`` (a build id, not a
commercial book identifier).

This pins that cleanliness so a future edit can't reintroduce a retail/academic
identifier without a test failing. It exercises the real OPF generator
(``build_edition.patch_opf``) on a representative base package document — no
network, no full EPUB build.
"""

import importlib

# A representative base content.opf — same shape as the epub_working base that
# patch_opf rewrites (mirrors tests/test_omega0_free_public_pivot.py's fixture).
_BASE_OPF = (
    "<?xml version='1.0'?>\n"
    '<package version="3.0">\n'
    '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
    '<dc:title>X</dc:title><dc:creator id="creator">Public Domain</dc:creator>\n'
    '<meta refines="#creator" property="role" scheme="marc:relators">aut</meta>\n'
    '<meta refines="#creator" property="file-as">Public Domain</meta>\n'
    '<dc:contributor id="contributor">calibre</dc:contributor>\n'
    "<dc:date>2020-01-01</dc:date><dc:language>en</dc:language>\n"
    "</metadata></package>"
)


class TestOpfClean:
    @classmethod
    def setup_class(cls):
        cls.be = importlib.import_module("scripts.build_edition")
        edition = {"id": "catholic-study", "title": "Catholic Study", "publisher_name": "Free Press"}
        cls.opf = cls.be.patch_opf(_BASE_OPF, edition, "v1")

    def test_emits_generator_urn_identifier(self):
        # The single surviving identifier IS the generator URN (EPUB3 unique-id anchor).
        assert 'id="pub-id"' in self.opf
        assert "urn:yhwh:edition:catholic-study" in self.opf

    def test_no_doi_metadata(self):
        assert "urn:doi" not in self.opf
        assert "TODO_DOI" not in self.opf
        assert 'id="doi"' not in self.opf

    def test_no_lccn_metadata(self):
        assert "urn:lccn" not in self.opf
        assert "TODO_LCCN" not in self.opf
        assert 'id="lccn"' not in self.opf

    def test_no_onix_codelist_or_isbn(self):
        # onix:codelist5 was the identifier-type scheme for the DOI(06)/LCCN(13)/
        # ISBN(15) refinements — all gone now.
        assert "onix:codelist5" not in self.opf
        assert "urn:isbn" not in self.opf
        assert "TODO_ISBN" not in self.opf

    def test_no_target_stamp_on_untargeted_editions(self):
        # kindle_safe: the yhwh:target-reader stamp is additive-only — an
        # edition without target_reader must emit no stamp (byte-identity).
        assert "yhwh:target-reader" not in self.opf

    def test_multilang_block_restored_for_non_kindle(self):
        # K-R5-6 (round 5b, REAL regression caught by the user): the turn-67
        # Kindle-E999 fix dropped the K-R2-5 multi-value dc:language block
        # UNCONDITIONALLY — but Kobo's tag-stripping Footnote preview keys its
        # fallback fonts on the OPF declarations (per-span lang never survives
        # the strip), so Publisher Default went tofu for Hebrew/Greek/Ge'ez.
        # E999 is Amazon's validator, nobody else's: the single-language form
        # is correct ONLY for kindle-target builds. Everyone else gets the
        # block back, now also declaring ar (the Van Dyck Arabic popups exist
        # per-span; the old block oddly lacked it).
        assert self.opf.count("<dc:language>") == 6
        assert "<dc:language>en-US</dc:language>" in self.opf
        for lang in ("hbo", "grc", "arc", "gez", "ar"):
            assert f"<dc:language>{lang}</dc:language>" in self.opf, lang

    def test_single_dc_language_when_kindle_target(self):
        # The E999 single-value form stays — target-gated to kindle builds.
        edition = {
            "id": "catholic-study",
            "title": "Catholic Study",
            "publisher_name": "Free Press",
            "target_reader": "kindle",
        }
        opf = self.be.patch_opf(_BASE_OPF, edition, "v1")
        assert opf.count("<dc:language>") == 1
        assert "<dc:language>en-US</dc:language>" in opf
        for dropped in ("hbo", "grc", "arc", "gez", "ar"):
            assert f"<dc:language>{dropped}</dc:language>" not in opf
