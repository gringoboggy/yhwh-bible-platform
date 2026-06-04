"""ρ.3 Phase C2-3 — tests for the /build-my-bible navigator console JS.

The static shell (C2-2) plus the drill-down navigation JS (C2-3). These
tests cover the two halves the task asks for:

  1. The console serves valid HTML containing the key DOM ids the JS
     drives (edition-picker, breadcrumb, book-list, level-panel) and the
     render/nav function names C2-3 wires (so a refactor that drops a
     function the markup depends on is caught), and the read-only-section
     markers that C2-4 / C2-5 will upgrade to interactive controls.

  2. The three ``api_build_my_bible`` levels return 200-equivalent
     (no ``error`` key) payloads of the expected shape for a real
     edition (``catholic-study``) at edition, book (``gen``), and
     chapter (``gen`` ch 1) levels. Called directly as the pure function
     (RULES §9) rather than over HTTP — the C2-1 test suite already
     drives the deeper shape assertions; this is the C2-3 smoke that the
     JS's three fetch targets all resolve.

Edition under test: ``catholic-study`` (no per-book/chapter overrides →
deterministic resolved state).
"""

from __future__ import annotations


class TestConsoleHtmlShell:
    """The served HTML carries the ids + functions the C2-3 JS relies on."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.build_my_bible import BUILD_MY_BIBLE_HTML

        cls.html = BUILD_MY_BIBLE_HTML

    def test_is_html_document(self):
        assert self.html.lstrip().startswith("<!DOCTYPE html>")
        assert "</html>" in self.html

    def test_key_dom_ids_present(self):
        for dom_id in ("edition-picker", "breadcrumb", "book-list", "level-panel"):
            assert f'id="{dom_id}"' in self.html, f"missing #{dom_id}"

    def test_render_and_nav_functions_present(self):
        # The render/nav surface the markup + handlers depend on. Dropping
        # any of these in a refactor would break the drill-down silently.
        for fn in (
            "function renderBreadcrumb(",
            "function renderBookList(",
            "function renderLevelPanel(",
            "function renderBiblePanel(",
            "function renderBookPanel(",
            "function renderChapterPanel(",
            "function renderSymbolsSection(",
            "function renderPopupsSection(",
            "function renderVerseRow(",
            "function renderNoteLine(",
            "function navToBook(",
            "function navToChapter(",
            "function goToLevel(",
        ):
            assert fn in self.html, f"missing JS fn: {fn}"

    def test_lazy_caches_declared(self):
        # Per-level caches keep re-visits from refetching.
        assert "BOOK_CACHE" in self.html
        assert "CHAPTER_CACHE" in self.html

    def test_read_only_section_markers_for_next_tasks(self):
        # C2-4 has shipped (the symbol tri-state + popup checklists are now
        # interactive), so its read-only marker is gone — its render
        # functions are exercised by the interactive controls instead. The
        # per-note disable/force-on row is still read-only (C2-5 owns it), so
        # that marker must remain.
        assert "C2-4 makes this interactive" not in self.html
        assert "C2-5 makes this interactive" in self.html

    def test_c2_4_interactive_controls_present(self):
        # The C2-4 interactive surface: tri-state symbol controls (book +
        # chapter) and popup checklists (book/chapter/verse) plus the save
        # flow that PUTs the absolute-replace field maps.
        for fn in (
            "function renderSymbolsControls(",
            "function wireSymbolsControls(",
            "function renderPopupsControls(",
            "function wirePopupsControls(",
            "function saveFields(",
            "function seedWorkFromOverview(",
            "function clearFinerSymbols(",
            "function clearFinerPopups(",
        ):
            assert fn in self.html, f"missing C2-4 JS fn: {fn}"
        # The tri-state option set + the autosave PUT target.
        assert "sym-cat-tri" in self.html
        assert "sym-kind-tri" in self.html
        assert "popup-lang-cb" in self.html
        assert "/api/edition-meta/" in self.html
        # Bible level stays read-only with cross-links to the edition-wide
        # editors (no edition-wide writes from this console in C2-4).
        assert 'href="/matrix"' in self.html
        assert 'href="/customize"' in self.html

    def test_calls_the_three_read_api_levels(self):
        # The JS must target all three C2-1 endpoints (edition/book/chapter).
        assert "/api/build-my-bible/" in self.html

    def test_uses_shared_escaper_not_raw_innerhtml(self):
        # XSS-safety: the shared ω.0.7 escaper must back the local esc() helper
        # AND the highest-risk server-supplied strings (note title/kind, book
        # title) must actually be wrapped in esc() before innerHTML — not merely
        # present somewhere in the file. (Integers like ch.num/v.vs are injected
        # raw by design — they are server-built range() ints, never strings.)
        assert "window.escapeHtml" in self.html
        for wrapped in ("esc(n.title", "esc(n.kind)", "esc(b.title)"):
            assert wrapped in self.html, f"server string not escaped: {wrapped}"


class TestApiThreeLevelsServeOk:
    """The three fetch targets the JS hits all resolve for a real edition."""

    @classmethod
    def setup_class(cls):
        from scripts.web_editions import api_build_my_bible

        cls.api = staticmethod(api_build_my_bible)

    def test_edition_level_ok(self):
        result = self.api("catholic-study")
        assert "error" not in result, result
        assert result["edition"]["id"] == "catholic-study"
        assert isinstance(result["books_canonical"], list)
        assert len(result["books_canonical"]) > 0
        # resolved_bible carries the SYMBOLS + POPUPS the Bible panel renders.
        assert "symbols" in result["resolved_bible"]
        assert "popups" in result["resolved_bible"]
        # registries the read-only sections label from.
        assert isinstance(result["categories"], list)
        assert isinstance(result["popup_languages"], list)

    def test_book_level_ok(self):
        result = self.api("catholic-study", book="gen")
        assert "error" not in result, result
        assert result["book"]["code"] == "gen"
        chapters = result["chapters"]
        assert len(chapters) == result["book"]["ch_count"]
        # ascending, 1..ch_count (canonical order — never client-sort)
        assert [c["num"] for c in chapters] == list(range(1, len(chapters) + 1))
        for c in chapters:
            assert "has_notes" in c
            assert "symbols" in c["resolved"]
            assert "popups" in c["resolved"]

    def test_chapter_level_ok(self):
        result = self.api("catholic-study", book="gen", chapter=1)
        assert "error" not in result, result
        assert result["chapter"] == 1
        verses = result["verses"]
        assert isinstance(verses, list)
        assert len(verses) > 0
        # ascending verse order
        assert [v["vs"] for v in verses] == sorted(v["vs"] for v in verses)
        # at least one note in gen ch1 with the read-only note shape the
        # verse-focus level renders.
        all_notes = [n for v in verses for n in v["notes"]]
        assert all_notes, "expected notes in gen ch1 for catholic-study"
        for n in all_notes:
            for field in ("note_id", "kind", "category", "symbol", "title", "disabled", "forced_on"):
                assert field in n, f"note missing {field!r}"

    def test_unknown_edition_returns_404(self):
        result = self.api("nonexistent-edition-xyz")
        assert "error" in result
        assert result.get("http") == 404
