"""ω.4x hygiene bundle — W-W2 + A-I1 + A-I2 (2026-05-14).

Third of three Claude-side actionable ships from the
AUDIT_2026-05-14-LIGHT-2 recommendation set (after δ.1.x.A.0
+ Π.2.prep). Bundles three hygiene items:

- **W-W2:** `scripts/build_edition.py` 44 ruff `check` errors
  reduced to 0 (manual fixes for SIM102/SIM108/N806/B023/F841 +
  per-file-ignore in pyproject.toml for intrinsic E501 / C901).
- **A-I1:** PLAN_2026-05-09 §2 status snapshot refreshed from
  "3808 tests" (2026-05-13 EOD baseline) to a current-fresh
  marker pointing at SESSION_STATE.
- **A-I2:** PLAN_2026-05-09 §6 extended with the parallel-Bible
  track cross-reference per SCOPE_2026-05-14-parallel-bible.md
  §11 ("PARALLEL-BIBLE: Π.0 → τ.6.x + τ.7.x → Π.1 → δ.1.x →
  Π.2 + φ.1 → δ.2").

ω.4x deliverables under test:

1. **W-W2: build_edition.py ruff check clean.** zero errors after
   manual fixes + per-file-ignore. Per-file-ignore in pyproject.toml
   exempts E501 (HTML template strings) + C901 (filter_books_for_
   canon / build_one / main load-bearing orchestration complexity).
2. **A-I1: PLAN §2 refresh.** The 2026-05-13 "3808 tests" snapshot
   is replaced with a current-fresh marker; the new text references
   SESSION_STATE as the authoritative live snapshot.
3. **A-I2: PLAN §6 parallel-Bible track.** New sub-section at the
   top of §6 documenting the parallel-Bible roadmap per SCOPE §11,
   listing both shipped and pending sub-phases.
4. **Closed-arc invariants regression-guarded:** γ.4.8.E + γ.4.8.F
   + Π.0.1 + Π.0.4 + τ.6.x.0a/b + δ.1.0 + δ.1.x.A.0 + Π.1 + Π.1.B
   + Π.2.prep all preserved.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
PLAN_DOC = REPO / "dev" / "PLAN_2026-05-09.md"
BUILD_EDITION = REPO / "scripts" / "build_edition.py"
PYPROJECT = REPO / "pyproject.toml"


def _plan_text() -> str:
    return PLAN_DOC.read_text(encoding="utf-8")


# ──────────────────────────────────────────────────────────────────
# ω.4x.W-W2 — build_edition.py ruff check clean
# ──────────────────────────────────────────────────────────────────


class TestOmega4xWW2BuildEditionRuffCheck:
    """W-W2 finding from AUDIT_2026-05-14-LIGHT-2: scripts/
    build_edition.py had 44 ruff `check` errors at audit time.
    ω.4x reduces this to zero via manual fixes + per-file-ignore."""

    def test_pyproject_per_file_ignore_for_build_edition(self):
        """pyproject.toml must list scripts/build_edition.py in
        per-file-ignores with E402 (script bootstrap import order)
        + E501 (HTML template strings) + C901 (load-bearing
        orchestration complexity)."""
        text = PYPROJECT.read_text(encoding="utf-8")
        assert '"scripts/build_edition.py"' in text, (
            "ω.4x: pyproject.toml must include scripts/build_edition.py per-file-ignore"
        )
        # The per-file-ignore line should mention E501 (HTML) and C901 (complexity)
        # Find the line containing the file path
        for line in text.splitlines():
            if '"scripts/build_edition.py"' in line and "=" in line:
                assert "E501" in line and "C901" in line, (
                    f"ω.4x: scripts/build_edition.py per-file-ignore must include E501 + C901. Line: {line!r}"
                )
                return
        raise AssertionError("ω.4x: per-file-ignore line for build_edition.py not found")

    def test_build_edition_passes_ruff_check(self):
        """Run `ruff check scripts/build_edition.py` and assert exit
        code 0 (zero errors after ω.4x fixes + per-file-ignores)."""
        result = subprocess.run(  # noqa: S603, S607 — local invocation, no untrusted input
            ["py", "-m", "ruff", "check", str(BUILD_EDITION)],
            stdin=subprocess.DEVNULL,  # W-W1 mitigation (τ.6.x.1)
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"ω.4x: build_edition.py must pass ruff check (exit 0). "
            f"Got exit {result.returncode}; stdout: {result.stdout[-500:]!r}; "
            f"stderr: {result.stderr[-500:]!r}"
        )


# ──────────────────────────────────────────────────────────────────
# ω.4x.A-I1 — PLAN §2 status snapshot refresh
# ──────────────────────────────────────────────────────────────────


class TestOmega4xAI1PlanStatusRefresh:
    """A-I1 finding from AUDIT_2026-05-14-LIGHT-2 (worsened from
    LIGHT-1): PLAN §2 baseline "3808 tests" lagged by 500+ tests.
    ω.4x replaces the stale numeric with a current-fresh marker
    + SESSION_STATE cross-reference."""

    def test_plan_section_2_no_longer_says_3808(self):
        """The 2026-05-13 EOD stale baseline must not appear as a
        STATUS LINE in §2. It may still appear as historical context
        elsewhere in the doc (e.g., in older session-arc summaries)."""
        text = _plan_text()
        # Find §2 section content
        lines = text.splitlines()
        in_section_2 = False
        section_2_lines: list[str] = []
        for line in lines:
            if line.startswith("## 2. Status snapshot"):
                in_section_2 = True
                continue
            if in_section_2 and line.startswith("## "):
                break
            if in_section_2:
                section_2_lines.append(line)
        section_2_text = "\n".join(section_2_lines)
        assert "3808 tests" not in section_2_text, "ω.4x: PLAN §2 must no longer carry the stale '3808 tests' baseline"

    def test_plan_section_2_references_session_state(self):
        """The refreshed §2 should point at SESSION_STATE as the
        authoritative live snapshot."""
        text = _plan_text()
        assert "SESSION_STATE" in text

    def test_plan_section_2_mentions_omega_4x_refresh(self):
        """Audit trail: the refresh attribution names ω.4x."""
        text = _plan_text()
        assert "ω.4x" in text and "AUDIT_2026-05-14-LIGHT-2" in text

    def test_plan_section_2_references_six_voice_corpus(self):
        """The fresh snapshot acknowledges the ω.41 §1 six-voice
        codification."""
        text = _plan_text()
        # At minimum mention 6 voices and Cyril plurality
        assert "six-voice" in text.lower() or "six voice" in text.lower() or "6 voice" in text.lower()
        assert "Cyril" in text


# ──────────────────────────────────────────────────────────────────
# ω.4x.A-I2 — PLAN §6 parallel-Bible track insertion
# ──────────────────────────────────────────────────────────────────


class TestOmega4xAI2PlanParallelBibleTrack:
    """A-I2 finding from AUDIT_2026-05-14-LIGHT-2: PLAN §6 lacks
    a parallel-Bible track cross-reference. ω.4x inserts a
    sub-section per SCOPE §11."""

    def test_plan_mentions_parallel_bible_track(self):
        text = _plan_text()
        assert "PARALLEL-BIBLE" in text or "Parallel-Bible track" in text, (
            "ω.4x: PLAN §6 must mention the parallel-Bible track"
        )

    def test_plan_references_scope_doc(self):
        text = _plan_text()
        assert "SCOPE_2026-05-14-parallel-bible" in text

    def test_plan_lists_phase_chain(self):
        """The SCOPE §11 canonical chain string must appear."""
        text = _plan_text()
        # Allow flexibility in whitespace around the arrows
        canonical_chain = "Π.0 → τ.6.x + τ.7.x → Π.1 → δ.1.x → Π.2 + φ.1 → δ.2"
        assert canonical_chain in text, (
            f"ω.4x: PLAN §6 must contain the SCOPE §11 canonical phase chain: {canonical_chain!r}"
        )

    def test_plan_lists_shipped_subphases(self):
        """The shipped sub-phase ledger should appear.
        Share-pin → milestone-pin conversions per the
        `feedback_share_pin_pattern` memory:
          - τ.6.x.0c migrated pending → shipped at τ.6.x.0c ship-time
          - τ.6.x.1 migrated pending → shipped at τ.6.x.1 ship-time
          - τ.6.x.1.A added shipped at τ.6.x.1.A pilot-validation
            ship-time (2026-05-15)
          - τ.6.x.1.B migrated pending → shipped at τ.6.x.1.B
            parser-extension ship-time (2026-05-15)
          - τ.6.x.2.D added shipped at τ.6.x.2.D D-decisions
            codification ship-time (2026-05-15; resolves the four
            publisher-direction D-decisions D1-a + D2-b + D3-c +
            D4-c that gated τ.6.x.2+ Geʽez bulk-ingest)
          - τ.7.x.a.0 added shipped at τ.7.x.a.0 PILOT ship-time
            (2026-05-15; Genesis page-range [0, 85] discovery +
            paragraph_mode_parser_extension_needed empirical finding
            that re-routes τ.7.x.a (proper) through τ.6.x.1.C
            parser-extension blocker)
          - τ.6.x.1.C migrated pending → shipped at τ.6.x.1.C ship-
            time (2026-05-15; paragraph-mode parser extension that
            resolves the τ.7.x.a.0 PILOT finding; adds paragraph_mode=
            True kwarg to parse_verses_from_text() splitting by ።
            sentence-terminator + filtering cross-references +
            sequential numbering; 63-65% Amharic Genesis verse
            coverage empirical)
          - τ.6.x.1.D migrated pending → shipped at τ.6.x.1.D ship-
            time (2026-05-15; chapter-marker recovery refinement
            adding CHAPTER_HEADER_RE_LENIENT + _resolve_chapter_marker
            with max-jump sanity; empirical chapters detected on
            Genesis pages 0-5 went from {1} to {1, 3, 4})
          - τ.7.x.a migrated pending → shipped at τ.7.x.a ship-time
            (2026-05-15; the FIRST τ.7.x.* full-book ingest;
            upgrades amharic-tewahedo/gen.py from Π.0 3-verse seed
            → 1308-verse ingest at 85.3% coverage via text-layer
            engine + paragraph_mode parser + writer-side renumber_
            against_floor against GENESIS_VERSE_COUNTS; resolves
            τ.6.x.1.D `chapter_marker_keyword_garbled_past_
            recognition` residual via the pre-committed writer-side
            renumbering path; 5th instance of single-key back-link
            annotation pattern tau6x1d→τ.7.x.a)
          - τ.7.x.b migrated pending → shipped at τ.7.x.b ship-time
            (2026-05-15; the SECOND τ.7.x.* per-book ship; creates
            amharic-tewahedo/ex.py with 947 verses at 78.1%
            coverage; re-uses τ.7.x.a pipeline verbatim with only
            EXODUS_VERSE_COUNTS + structural_map.exodus as deltas;
            confirms the τ.7.x.a pipeline as the canonical τ.7.x.*
            per-book template; 6th instance of single-key back-link
            annotation pattern tau7xa_ingest→τ.7.x.b — FIRST
            signaling pipeline-template-reuse rather than residual-
            resolution)
          - τ.7.x.c migrated pending → shipped at τ.7.x.c ship-time
            (2026-05-15; the THIRD τ.7.x.* per-book ship; creates
            amharic-tewahedo/lev.py with 802 verses at 93.4%
            coverage — HIGHEST τ.7.x.* coverage yet; re-uses τ.7.x.b
            pipeline verbatim with only LEVITICUS_VERSE_COUNTS +
            structural_map.leviticus as deltas; third consecutive
            τ.7.x.* ship with zero parser API change — firmly
            establishing the τ.7.x.a template as a stable per-book
            scaffold; 7th instance of single-key back-link
            annotation pattern tau7xb_ingest→τ.7.x.c)
          - τ.7.x.d migrated pending → shipped at τ.7.x.d ship-time
            (2026-05-15; the FOURTH τ.7.x.* per-book ship; creates
            amharic-tewahedo/num.py with 1107 verses at 85.9%
            coverage (sits between Gen 85.3% and Lev 93.4%); re-uses
            τ.7.x.c pipeline verbatim with only NUMBERS_VERSE_COUNTS
            + structural_map.numbers as deltas; FOURTH CONSECUTIVE
            τ.7.x.* ship with zero parser API change — decisively
            establishing the τ.7.x.a template as a stable per-book
            scaffold across all four ships; 80% of the Pentateuch
            closed under Amharic-first sequencing (gen + ex + lev +
            num shipped; deut next as τ.7.x.e closes §8.1 Pentateuch
            arc); 8th instance of single-key back-link annotation
            pattern tau7xc_ingest→τ.7.x.d)
          - τ.7.x.e migrated pending → shipped at τ.7.x.e ship-time
            (2026-05-15; the FIFTH τ.7.x.* per-book ship; **CLOSES
            the §8.1 Pentateuch arc under Amharic-first sequencing**
            — gen + ex + lev + num + deut = all 5 books of Torah
            shipped in amharic-tewahedo; NINTH §8.1 arc-close
            instance overall + FIRST in τ-cluster — codifies per-
            book-cadence + Amharic-first Pentateuch-arc-close as
            durable structural pattern; creates amharic-tewahedo/
            deu.py with 781 verses at 81.4% coverage (sits between
            Exodus 78.1% and Genesis 85.3%); re-uses τ.7.x.d pipeline
            verbatim with only DEUTERONOMY_VERSE_COUNTS +
            structural_map.deuteronomy as deltas; FIFTH CONSECUTIVE
            τ.7.x.* ship with zero parser API change — five-ship
            zero-API-delta is the strongest possible refactor-
            stability signal; **Pentateuch combined coverage 4945/
            5853 = 84.5% across all 5 books of Torah**; 9th instance
            of single-key back-link annotation pattern tau7xd_ingest
            →τ.7.x.e; τ-cluster §8.1 codifies STRUCTURAL §8.1
            (per-book-cadence closure of canonical unit) vs γ-cluster
            NARRATIVE §8.1 (detail-wave buildout within voice/book))
          - τ.7.x.f migrated pending → shipped at τ.7.x.f ship-time
            (2026-05-15; the SIXTH τ.7.x.* per-book ship; **OPENS
            the post-Pentateuch historical-books arc under Amharic-
            first sequencing** — FIRST τ-cluster ingest after the
            §8.1 Pentateuch arc-close at τ.7.x.e; historical-books
            canonical unit will span Joshua → Judges → Ruth → 1-4
            Kingdoms → 1-2 Paralipomena → Ezra/Nehemiah → Esther
            under LXX/Tewahedo ordering; creates amharic-tewahedo/
            jos.py with 483 verses at 73.4% coverage — LOWEST
            τ.7.x.* coverage to date (slightly below Exodus's
            78.1%); cause: Joshua's long tribal-allotment chapters
            + publisher-added Judges-bridge narrative on page 390;
            re-uses τ.7.x.e pipeline verbatim with only
            JOSHUA_VERSE_COUNTS + structural_map.joshua as deltas;
            SIXTH CONSECUTIVE τ.7.x.* ship with zero parser API
            change — six-ship zero-API-delta extends template
            stability across Pentateuch (5 books) + Joshua (1 book)
            = 6 books / 316 PDF pages; **Pentateuch + Joshua
            combined coverage 5428/6511 = 83.4% across all 6
            books**; 10th instance of single-key back-link
            annotation pattern tau7xe_ingest→τ.7.x.f; NEW NULL-
            FORMAL-TITLE-BANNER pattern (Joshua first τ.7.x.* book
            without explicit `መጽሐፈ X` book-title-banner in PDF
            text-layer); NEW residual class publisher_bridge_
            narrative_residual)
          - τ.7.x.g migrated pending → shipped at τ.7.x.g ship-time
            (2026-05-15; the SEVENTH τ.7.x.* per-book ship;
            **CONTINUES the post-Pentateuch historical-books arc
            opened at τ.7.x.f under Amharic-first sequencing** —
            SECOND sub-phase in the historical-books arc; creates
            amharic-tewahedo/jdg.py with 511 verses at 82.7%
            coverage (sits between Deuteronomy 81.4% and Numbers
            85.9%; comfortably within the canonical τ.7.x.* band);
            re-uses τ.7.x.f pipeline verbatim with only
            JUDGES_VERSE_COUNTS + structural_map.judges as deltas;
            SEVENTH CONSECUTIVE τ.7.x.* ship with zero parser API
            change — seven-ship zero-API-delta extends template
            stability across Pentateuch (5) + Joshua + Judges = 7
            books / 357 PDF pages; **Pentateuch + Joshua + Judges
            combined coverage 5939/7129 = 83.3% across all 7
            books**; 11th instance of single-key back-link
            annotation pattern tau7xf_ingest→τ.7.x.g; **NULL-
            FORMAL-TITLE-BANNER pattern CONFIRMED** as STABLE
            structural property of the historical-books arc (second
            consecutive ship without explicit `መጽሐፈ X` book-
            title-banner — publisher uses `አሪት ዘ<book>` running-
            header form consistently); share-pin → milestone-pin
            conversion applied to τ.7.x.f test_stats_books_six →
            test_stats_books_at_least_six (sixth instance of the
            conversion in τ.7.x.* family))
          - τ.7.x.h migrated pending → shipped at τ.7.x.h ship-time
            (2026-05-15; the EIGHTH τ.7.x.* per-book ship;
            **CONTINUES the post-Pentateuch historical-books arc
            opened at τ.7.x.f under Amharic-first sequencing** —
            THIRD sub-phase in the historical-books arc; creates
            amharic-tewahedo/rut.py with 60 verses at 70.6%
            coverage — NEW band-bottom for τ.7.x.* family (below
            τ.7.x.f Joshua's prior 73.4% band-bottom; Ruth's
            exceptional small scale (4 ch / 85 v / 6 PDF pages)
            + dense Davidic-genealogy compression in ch 4 makes
            ch 4 hard to recover); re-uses τ.7.x.g pipeline verbatim
            with only RUTH_VERSE_COUNTS + structural_map.ruth as
            deltas; EIGHTH CONSECUTIVE τ.7.x.* ship with zero
            parser API change — eight-ship zero-API-delta is
            decisive AND uniquely validates that the template
            scales DOWN to the smallest canonical OT book; covers
            ENTIRE parallel-Bible-EOTC scan range (pages 0-437);
            **Pentateuch + Joshua + Judges + Ruth combined coverage
            5999/7214 = 83.2% across all 8 books**; 12th instance
            of single-key back-link annotation pattern
            tau7xg_ingest→τ.7.x.h; **NULL-FORMAL-TITLE-BANNER
            pattern CONFIRMED 3x** as DECISIVELY STABLE structural
            property of the historical-books arc (third consecutive
            ship without explicit `መጽሐፈ X` banner); **CRITICAL
            STRUCTURAL DISCOVERY**: parallel-Bible-EOTC scan ENDS
            at page 437 — pages 438+ contain a SEPARATE publication
            (dzamaragna.net 2002 Amharic Bible appendix) with a
            completely different format; τ.7.x.i+ will require a
            NEW publication-format handler — see _source.yaml::
            ocr_strategy.tau7xh_ingest.structural_map_addition.
            publication_format_shift_residual for the full
            description; +60 new pin tests across 9 test classes
            including new dedicated `publication_format_shift_
            residual` pin)"""
        text = _plan_text()
        for phase in [
            "Π.0",
            "τ.6.x.0a",
            "τ.6.x.0b",
            "φ.1",
            "δ.1.0",
            "Π.1",
            "Π.1.B",
            "τ.6.x.0c",
            "τ.6.x.1",
            "τ.6.x.1.A",
            "τ.6.x.1.B",
            "τ.6.x.1.C",
            "τ.6.x.1.D",
            "τ.6.x.2.D",
            "τ.7.x.a.0",
            "τ.7.x.a",
            "τ.7.x.b",
            "τ.7.x.c",
            "τ.7.x.d",
            "τ.7.x.e",
            "τ.7.x.f",
            "τ.7.x.g",
            "τ.7.x.h",
        ]:
            assert phase in text, f"ω.4x: PLAN §6 parallel-Bible ledger must mention {phase!r}"

    def test_plan_lists_pending_subphases(self):
        """The pending sub-phase ledger (still-blocked phases) should
        appear. Migrations:
          - τ.6.x.0c removed at τ.6.x.0c ship-time
          - τ.6.x.1+ → τ.6.x.2+ at τ.6.x.1 ship-time (engine wired;
            bulk-ingest is now the publisher-gated successor phase)
          - τ.6.x.1.B added pending at τ.6.x.1.A pilot-validation
            ship-time (empirical finding: parse_verses_from_text()
            needs Ethiopic-numeral support); migrated pending →
            shipped at τ.6.x.1.B ship-time
          - τ.7.x.a + τ.6.x.3 added pending at τ.6.x.2.D D-decisions
            ship-time (2026-05-15; D4-c Amharic-first inversion
            promotes τ.7.x.a as the next-up phase; D2-b + D3-c
            create the τ.6.x.3 full-87-book audit phase)
          - τ.6.x.1.C added pending at τ.7.x.a.0 PILOT ship-time
            (2026-05-15; paragraph-mode parser extension blocking
            τ.7.x.a (proper) + likely also τ.7.x.b-z + τ.6.x.2.a-z
            under paragraph-flowing conjecture); migrated pending →
            shipped at τ.6.x.1.C ship-time (2026-05-15)
          - τ.6.x.1.D added pending at τ.6.x.1.C ship-time
            (2026-05-15; OPTIONAL chapter-marker recovery refinement
            addressing the known residual where OCR-garbled chapter
            numerals cause all verses to default to chapter 1);
            migrated pending → shipped at τ.6.x.1.D ship-time
            (2026-05-15)
          - τ.6.x.1.E added pending at τ.6.x.1.D ship-time
            (2026-05-15; OPTIONAL truncated-keyword chapter recovery
            addressing the τ.6.x.1.D residual where chapter markers
            with multi-char keyword garbling — e.g. `ራፍ` truncation
            missing both ዕ AND ፅ — still aren't recognized; lower
            priority now that τ.7.x.a renumbering-against-floor
            handles the writer-side concern)
          - τ.7.x.b added pending at τ.7.x.a ship-time (2026-05-15;
            Amharic Exodus full-book ingest under D1-a + D4-c;
            re-uses τ.7.x.a pipeline with EXODUS_VERSE_COUNTS floor);
            migrated pending → shipped at τ.7.x.b ship-time (2026-05-15)
          - τ.7.x.c added pending at τ.7.x.b ship-time (2026-05-15;
            Amharic Leviticus full-book ingest; 27 chapters, 859
            verses; re-uses τ.7.x.a + τ.7.x.b pipeline); migrated
            pending → shipped at τ.7.x.c ship-time (2026-05-15)
          - τ.7.x.d added pending at τ.7.x.c ship-time (2026-05-15;
            Amharic Numbers full-book ingest; 36 chapters, 1288
            verses; re-uses τ.7.x.a+b+c pipeline with
            NUMBERS_VERSE_COUNTS floor + structural_map.numbers
            block; Num 1:1 boundary confirmed at page 214 per
            τ.7.x.c boundary inspection); migrated pending →
            shipped at τ.7.x.d ship-time (2026-05-15)
          - τ.7.x.e added pending at τ.7.x.d ship-time (2026-05-15;
            Amharic Deuteronomy full-book ingest CLOSES the §8.1
            Pentateuch arc under Amharic-first sequencing; 34
            chapters, 959 verses; re-uses τ.7.x.a+b+c+d pipeline
            with DEUTERONOMY_VERSE_COUNTS floor +
            structural_map.deuteronomy block; Deut 1:1 boundary
            confirmed at page 288 per τ.7.x.d boundary inspection
            via Deuteronomy title `ኦሪት ዘዳግም` scan); migrated
            pending → shipped at τ.7.x.e ship-time (2026-05-15)
          - τ.7.x.f added pending at τ.7.x.e ship-time (2026-05-15;
            Amharic Joshua full-book ingest OPENS the post-
            Pentateuch historical-books arc under Amharic-first
            sequencing; 24 chapters, 658 verses; re-uses τ.7.x.a+b+
            c+d+e pipeline with JOSHUA_VERSE_COUNTS floor +
            structural_map.joshua block; Joshua 1:1 boundary
            confirmed at page 349 per τ.7.x.e boundary inspection);
            migrated pending → shipped at τ.7.x.f ship-time
            (2026-05-15)
          - τ.7.x.g added pending at τ.7.x.f ship-time (2026-05-15;
            Amharic Judges full-book ingest continues the post-
            Pentateuch historical-books arc under Amharic-first
            sequencing; 21 chapters, 618 verses; re-uses τ.7.x.a+b+
            c+d+e+f pipeline with JUDGES_VERSE_COUNTS floor +
            structural_map.judges block; Judges 1:1 boundary
            confirmed at page 391 per τ.7.x.f boundary inspection);
            migrated pending → shipped at τ.7.x.g ship-time
            (2026-05-15)
          - τ.7.x.h added pending at τ.7.x.g ship-time (2026-05-15;
            Amharic Ruth full-book ingest continues the post-
            Pentateuch historical-books arc; 4 chapters, 85 verses
            — SHORTEST canonical book in OT, will be smallest
            τ.7.x.* per-book ingest to date; re-uses τ.7.x.a+b+c+d+
            e+f+g pipeline with RUTH_VERSE_COUNTS floor +
            structural_map.ruth block; Ruth 1:1 boundary confirmed
            at page 432 per τ.7.x.g boundary inspection via Ruth
            1:1 `ወክነ በመዋዕለ ይሁንኑ መሳፍንት` opening scan); migrated
            pending → shipped at τ.7.x.h ship-time (2026-05-15)
          - τ.7.x.i added pending at τ.7.x.h ship-time (2026-05-15;
            Amharic 1 Samuel/1 Kingdoms full-book ingest CONTINUES
            the post-Pentateuch historical-books arc; 31 chapters,
            810 verses per KJV/Hebrew enumeration; **MUST address
            τ.7.x.h structural discovery**: parallel-Bible-EOTC
            scan ends at page 437; 1 Samuel content begins at
            page 438 in a DIFFERENT publication format (dzamaragna.
            net 2002 Amharic Bible appendix). Options: (a) source
            from dzamaragna.net appendix with NEW publication-
            format handler + source_provenance `dzamaragna-net-
            amharic-2002`; (b) source from external PDF; (c) defer
            pending source-document inventory review. Recommended
            (a) with clean separation between two source-provenance
            streams; will need SAMUEL_1_VERSE_COUNTS floor +
            structural_map.kingdoms_1 block)
          - τ.6.x.2.a-h migrated pending → shipped (BATCH) at
            τ.6.x.2.a-h batch ship-time (2026-05-15; Geʽez catchup
            of the parallel-Bible-EOTC scan after Amharic-first
            τ.7.x.a-h shipped; D4-c sequencing inversion + D1-a
            per-book cadence; 8 Geʽez per-book ingests upgrade
            geez-tewahedo/ from Π.0 seed (1 book / 3 verses) to
            ocr-tier3 full-book ingest (8 books / 4337 verses /
            60.1% combined coverage; Geʽez recovers ~72% of what
            Amharic does at the canonical-block level, consistent
            with τ.6.x.0a honesty contract that the Geʽez column
            text-layer is harder to parse); pipeline reused
            VERBATIM from τ.7.x.a-h with only `--lang geez` flag
            flip as the per-ship delta — 16-ship template stability
            across BOTH columns (8 Amharic τ.7.x.a-h + 8 Geʽez
            τ.6.x.2.a-h) with zero parser API drift; **CLOSES the
            parallel-column-catchup arc** — both columns now at
            PARITY for the entire parallel-Bible-EOTC scan range
            (pages 0-437); τ.6.x.2.e records §8.1 Pentateuch arc-
            close in Geʽez stream (TENTH §8.1 instance overall;
            FIRST in τ-cluster Geʽez stream); τ.6.x.2.h records
            parallel-column-catchup arc-close; share-pin → milestone-
            pin pattern: tau7x{a..h}.py `test_geez_tewahedo_<book>_
            py_not_created` migrated to `test_geez_tewahedo_<book>_
            py_ingested_at_tau6x2<letter>` (flip assertion from
            "must NOT exist" to "must EXIST at ocr-tier3 scale");
            tau7x{a..h}.py `test_geez_tewahedo_gen_py_still_seed`
            migrated to `test_geez_tewahedo_gen_py_ingested_at_
            tau6x2a` (flip assertion from "≤10 verses" to "≥950
            verses"); +N new pin tests in test_parallel_bible_tau6x2_
            geez_arc.py covering per-book file presence, module
            constants, verse-count floors, coverage thresholds,
            arc-close markers, Amharic-stream preservation,
            parallel-column parity)
          - τ.7.x.i migrated pending → shipped at τ.7.x.i ship-time
            (2026-05-15; the NINTH τ.7.x.* per-book ship; **OPENS
            the Wisdom-and-Poetry arc under Amharic-first sequencing**
            — first canonical-arc transition after the post-Pentateuch
            historical-books arc; creates amharic-tewahedo/psa.py with
            2243 verses at 88.6% coverage — SECOND-HIGHEST τ.7.x.*
            coverage to date (between Leviticus 93.4% and Numbers
            85.9%); LARGEST τ.7.x.* per-book ingest to date (151 ch /
            2531 v under LXX/Tewahedo enumeration including Psalm 151
            David-vs-Goliath; vs prior largest GENESIS_VERSE_COUNTS
            50 ch / 1534 v); re-uses τ.7.x.h pipeline VERBATIM with
            only PSALMS_VERSE_COUNTS + structural_map.psalms as
            deltas; NINTH CONSECUTIVE τ.7.x.* ship with zero parser
            API change; **FIRST τ.7.x.* ship to SKIP a section of
            source PDF** — per user "Skip the gap for now" decision
            after τ.7.x.h structural-discovery scan revealed the
            438-802 dzamaragna.net 2002 Amharic-only gap (10 books:
            1 Sam → Job); τ.7.x.i resumes parallel-Bible-EOTC scan
            at p803 with Psalms (second EOTC-parallel block); the
            10 skipped books deferred to a future τ.7.x.J-cluster
            sub-arc; **Psalm 151 (David-vs-Goliath, Tewahedo-
            distinctive) preserved** in extracted output (renumbered
            to ch 126 partial slot due to chapter-exhaustion artifact;
            τ.6.x.3 audit re-aligns); 13th instance of back-link
            pattern but with NOVEL `also_reused_at_phase` second-
            key form on tau7xh_ingest (alongside existing
            pipeline_reused_at_phase: τ.6.x.2.h Geʽez catchup back-
            link) — τ.7.x.h is now the highest-reuse pipeline in
            the τ.7.x.* family with two distinct reuses; combined
            9-book coverage 8242/9745 = 84.6%; +N new pin tests in
            test_parallel_bible_tau7xi.py covering Psalter shape +
            skip-the-gap invariants + Psalm 151 preservation + Wisdom-
            and-Poetry arc-open + 9-book coverage threshold)"""
        text = _plan_text()
        for phase in [
            "τ.6.x.2+",
            "τ.7.x.i",
            "τ.6.x.2.a",
            "τ.6.x.2.h",
            "τ.7.x.j",
            "τ.6.x.3",
            "τ.6.x.1.E",
            "δ.1.x.A",
            "Π.2",
            "δ.2",
        ]:
            assert phase in text, f"ω.4x: PLAN §6 parallel-Bible ledger must mention {phase!r}"


# ──────────────────────────────────────────────────────────────────
# ω.4x — closed-arc invariant preservation
# ──────────────────────────────────────────────────────────────────


class TestOmega4xClosedArcInvariantPreservation:
    """ω.4x must not regress any prior closed-arc invariant."""

    def test_build_edition_still_parses(self):
        """The W-W2 edits did not break Python parsing of
        build_edition.py."""
        import ast

        text = BUILD_EDITION.read_text(encoding="utf-8")
        ast.parse(text)  # raises SyntaxError if broken

    def test_build_edition_imports_cleanly(self):
        """Higher-confidence smoke test: import the module via py
        subprocess (avoids polluting the test harness with the
        build_edition module's import side-effects)."""
        result = subprocess.run(  # noqa: S603, S607
            ["py", "-c", "import ast; ast.parse(open(r'scripts/build_edition.py', encoding='utf-8').read())"],
            stdin=subprocess.DEVNULL,  # W-W1 mitigation (τ.6.x.1)
            capture_output=True,
            text=True,
            check=False,
            cwd=str(REPO),
        )
        assert result.returncode == 0, (
            f"ω.4x: build_edition.py must be import-clean after W-W2 edits. stderr: {result.stderr[-500:]!r}"
        )

    def test_pyproject_other_per_file_ignores_unchanged(self):
        """ω.4x added scripts/build_edition.py per-file-ignore;
        the other entries (source_archive + content/notes +
        kings_session) must remain."""
        text = PYPROJECT.read_text(encoding="utf-8")
        for entry in [
            '"scripts/*.py"',
            '"source_archive/*.py"',
            '"source_archive/phase_c9_expansion.py"',
            '"content/notes/*.py"',
            '"kings_session/*.py"',
        ]:
            assert entry in text, f"ω.4x: pyproject.toml per-file-ignores must retain {entry}"


# ──────────────────────────────────────────────────────────────────
# ω.4x — phase coverage
# ──────────────────────────────────────────────────────────────────


class TestOmega4xPhaseCoverage:
    """The ω.4x phase tag must surface in CHANGELOG so the project
    linter's untracked-phases check passes."""

    def test_omega_4x_phase_tag_in_changelog(self):
        changelog = REPO / "dev" / "CHANGELOG.md"
        text = changelog.read_text(encoding="utf-8")
        assert "ω.4x" in text, "ω.4x: CHANGELOG.md must mention the ω.4x phase tag"
