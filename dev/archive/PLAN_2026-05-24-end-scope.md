# End-Scope Master Plan — optimal order to the 2026-06-07 deadline

**Created 2026-05-24.** Consolidates everything added this session — the EPUB
presentation overhaul, the cover-customization sub-project, the back matter, and
a professional-readiness audit — with the pre-existing tracks, into ONE
deadline-aware sequence.

**Companions:** design spec `docs/superpowers/specs/2026-05-24-epub-presentation-polish-design.md`
(the WHAT) · `docs/superpowers/plans/2026-05-24-epub-presentation-polish.md`
(Phase-1 TDD tasks) · `dev/archive/PLAN_2026-05-21.md` (still authoritative for Track B/C
detail) · `dev/CLAUDE_PROJECT_RULES.md` (rules).

---

## ▶ Post-Wave-4 — ordered remaining backlog (user-prioritized 2026-05-25)

**Wave 4 is COMPLETE** (W4.1 frozen-build · W4.2 concurrent-build cap · W4.3 first-run welcome flow · W4.4 README + release artifact · W4.5 local CI gate + mypy-clean + coverage floor). The autonomous productionization stream (Waves 0–4) is **done**. The user set the remaining work in this order:

**TIER 1 — quick loose ends (next):**
1. **Activate the W4.5 coverage floor** — `pip install -r requirements-dev.txt` so `coverage` is installed → the `make ci` coverage step goes live; set a `--fail-under` baseline from the first real measurement.
2. **Git-LFS decision** for the cover templates — ✅ **DECIDED 2026-05-25: LEAVE AS-IS (no LFS).** Measured: `.git` 439 MB · `content/covers/templates` 193 MB (25 PNGs, ≤~8 MB each) · `_book_defaults` 9 MB. Three decisive reasons: (a) **no git remote** (deleted 2026-05-12) → LFS's remote-bandwidth/storage benefit is zero; (b) **`git bundle --all` — the E:/F: backup — excludes LFS media**: a bundle serializes the git object DB and captures only LFS *pointers*, not the blobs in `.git/lfs/objects/`, so adopting LFS would silently make every backup incomplete (restore = 193 MB of pointer stubs, not images); (c) each file is < GitHub's 100 MB/file hard limit and the repo is < the 1 GB soft cap, so even a *future* remote handles these in plain git. `git-lfs` is installed system-wide but `.gitattributes` has no `filter=lfs` (only EOL + `*.png/jpg binary` normalization). **Revisit ONLY IF** a remote is reconnected AND repo size nears the host cap — and that migration must ALSO move backups off `git bundle` (e.g. `git lfs fetch --all` + a separate media archive), so it is a coupled decision, not a drop-in.
3. **`smoke_desktop.py` self-cleanup** — remove the orphaned `_MEI*` extraction dirs left after the smoke's `taskkill /F` blocks PyInstaller's auto-cleanup.

**TIER 2 — opportunistic depth (NOT blocking — the product ships without these):**
4. **Track C corpus** — the 5 capped reference works (Matthew Henry · JFB · Barnes · Torrey · Vincent) via the χ-cluster pipeline (§9). Voyage AI embeddings de-scoped.
5. **7 no-KJV books' verse popups** (Meqabyan I-III · 2 Enoch · Jubilees · 4 Baruch · 1 Clement) — need PD/Geʽez source data.
6. **Phase E** — the Clementine Latin appendix (`man`/`1es`/`2es`), clean-digital-first.
7. **Code-debt hygiene** — the deep-audit P3/P4 tail (`dev/AUDIT_2026-05-23-DEEP.md`) + the visible ruff lint backlog + installing/wiring vulture + pip-audit (currently graceful-skipped in `make ci`).

**TIER 3 — the parallel-Bibles arc (first-class north-star), user-prioritized LAST:**
8. The two standalone Geʽez + Amharic Bibles (`dev/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md`): (1) finish Geʽez rendering = the **Track B** Kings/Samuel manuscript marathon (user-paced, calendar-bound critical path) → (2) constitute the standalone editions → (3) finalize sources (Amharic from the parallel-Bible PDF; Geʽez gaps from `GAPS/`) → (4) English back-translation of the actual wording → (5) wire into their own verse popups.

> This REORDERS the "marathon is primary" framing in the PARALLEL-tracks section below: with Wave 4 done, the user spends remaining Claude-time on the autonomous TIER-1 / TIER-2 work first and paces the TIER-3 marathon themselves. Separate and still open: the **[USER]** real-reader presentation eyeball (Apple Books / e-ink).

---

## Guiding lens — the deadline is "losing Claude" (2026-06-07)

Two consequences shape the order:
1. **Front-load what genuinely needs Claude** — the complex implementation
   (Phase-2 base-HTML re-bake, the cover composer). These are hardest to do solo.
2. **Make the project survivable solo** — backup, remote, CI, README, licensing
   docs — so it doesn't rot after Claude access ends.

Honest scope note: the autonomous stream below (Waves 0–4) is now large; **not
all of it will fit in 14 days** alongside the manuscript marathon. The point of
the order is that the highest-value, most-foundational, most-Claude-dependent
work ships first.

---

## Status — Waves 0–3 SHIPPED 2026-05-25 (the Phase-1 detail below is historical)

- ✅ DONE + verified: **left-align body text · cover fits the frame · colophon
  rewritten (real per-edition counts, no `TODO_`, no stale "1,371") · "A Guide to
  the Notes" edition-aware symbol glossary (clickable anchor ids).**
- ▶ REMAINING in Phase 1: **About-this-Edition** page (auto-generated specs +
  editable `description`) · **Dedication** page (optional, builder-typed) ·
  **Back matter** (Sources & Acknowledgments · Reference tables · Closing
  colophon) · **Phase-1 verification gate** (epubcheck reps · `ebible verify` ·
  lint · categorize-diff).
- ✅ Waves 1–3 are all COMMITTED (25e22cf→61226c5) + verified by the light post-Wave-3
  audit (`dev/AUDIT_2026-05-25-wave3-FINDINGS.md`); **Wave 4 (downloadable desktop app)
  is the next active wave.**

---

## The optimal order

### WAVE 0 — Foundation & safety (now; cheap; protects + enables everything)
- ✅ **Backup** (zip 2026-05-24 → C:, E:, F: triple-drive). GitHub remote deferred
  (user's Apple-auth/phone situation); revisit when feasible — it unblocks CI.
- **README** (user + dev on-ramp: what this is / install / run / build an edition).
- **Asset licensing** — document the Midjourney provenance + redistribution terms
  of the 25 cover templates + the book art + fonts; extend
  `content/sources/ATTRIBUTIONS.md` to cover images/fonts (text sources already done).
- **Git-LFS note** for the ~159 MB image assets; confirm `.env` (Voyage key) gitignored.
- WHY first: cheap; makes the project legal-to-distribute + survivable solo.

### WAVE 1 — Finish EPUB Presentation Phase 1 (close the in-flight seam)
- About-this-Edition · Dedication · Back matter (Sources / ref-tables / closing
  colophon) · verification gate.
- WHY now: mid-flight, testable via subagents, high visible value, no heavy deps.

### WAVE 2 — Cover sub-project (first impression; the user's stated priority)
- **2a — universal cover-title placement + title-only fix** (the screenshot bug):
  one title position clear of every design's ornament; drop subtitle + "Bible
  Builder" mark; proper centering (PIL `anchor`). Visual iteration (Claude-driven).
- **2b — the 25-design clickable picker** (the already-planned π.6 cover composer)
  + **per-book title-page art** (full-bleed/framed) + **builder upload** (reuse the
  existing `/api/covers/<edition>/main` pipeline) + **image alt-text**.
- WHY: the cover is the first thing a user sees; 2a is foundational for 2b.

### WAVE 3 — EPUB Presentation Phase 2 (configurable settings + base re-bake) — ✅ DONE 2026-05-25 (25e22cf→61226c5; verified by AUDIT_2026-05-25-wave3-FINDINGS.md)
- The four `editions.yaml` enum settings (`marker_style` · `verse_popup_style` ·
  `note_popup_style` · `title_page_style`) · markers→numbers · symbols-into-notes
  (+ clickable symbol→glossary link) · `‖` fix · widened popups / drop-KJV ·
  the Topical index (Nave's) back-matter page.
- WHY later: deepest + riskiest (shared base-HTML re-bake), most Claude-dependent;
  each setting is independently shippable.

### WAVE 4 — Productionization → DOWNLOADABLE DESKTOP APP (decided 2026-05-24) — ◀ IN PROGRESS (2026-05-25): **W4.1 ✅ DONE** — the existing θ.1/θ.2 desktop binary now BUILDS when frozen (4 frozen-only fixes: in-process build, bundled `epub_working/`, `-X utf8`, persistent `YHWH_DATA_DIR` output) + a `dev/smoke_desktop.py` harness; smoke builds a persistent EPUB. **W4.2–W4.5 remain:** concurrent-build cap · onboarding/empty-state UX · distribution README + release artifact · CI/mypy/coverage
**Delivery model = downloadable desktop app** (user 2026-05-24): package the existing
web UI + local server so a user double-clicks to run it locally — no Python, no server.
- **Packaging:** bundle Python + deps + assets into a one-folder/one-file app
  (PyInstaller, or a pywebview/Tauri-style native-window wrapper around the local
  `http.server`). A launcher starts the local server + opens the UI. Windows first
  (the dev platform); macOS/Linux later if wanted.
- **Security surface is LIGHT** — single-user local app, no hostile remote callers, so
  **CSRF / rate-limiting / public-server hardening are NOT needed** (a big scope cut vs
  hosting). Keep the existing input-validation, upload-safety, and path-sandbox checks.
- **Still in scope:** onboarding + preview + empty-state guardrails (UX for
  non-technical builders); a hard concurrent-build cap + the existing OOM caps (local
  resource safety); a smoke test that the packaged app launches + builds an EPUB.
- **Distribution:** a packaged installer/release artifact + the README explaining
  install + run.
- **CI + mypy + coverage floor** — solo-maintainability; needs a remote (deferred), but
  the gates run locally via `make` meanwhile.

### PARALLEL — Track B (manuscript marathon) + Track C (corpus)
Per `dev/archive/PLAN_2026-05-21.md` §4.0's ratified "two tracks in parallel," the Kings/Samuel
Geʽez dual-witness marathon continues at the user's check-in cadence, in the gaps.
It is calendar-bound and the binding constraint on how much transcription ships by
the deadline. **Strategic fork for the final 14 days:** how much Claude-time goes to
the marathon vs. this builder/presentation/productionization push. This session's
focus has been the builder; the order above assumes the builder push is primary and
the marathon is opportunistic — confirm if that's right.

---

## "Put it all in scope" — audit/product items, now tracked
Wave 0: backup ✅ · README · asset-licensing docs · Git-LFS · secrets hygiene.
Wave 4: hosting decision · CSRF / rate-limit / build-cap (if public) · onboarding /
preview / empty-states · CI · mypy + coverage enforcement.
These were the professional-readiness findings from the 2026-05-24 assessment.

## The one decision that shapes the order
**Hosting model** (Wave 4 gate) + the **marathon-vs-builder emphasis** (parallel
track). Everything else is sequenced and ready to execute in order.

---

## Scope companion documents (inherited from PLAN_2026-05-21 / lint-docs check)

These addenda remain on disk as the authoritative spec detail for each feature family.
They are listed here so the `lint_rules.py` docs-cross-reference check can locate them.

- `dev/SCOPE_2026-05-08.md` — base scope statement (supersedes the archived 05-07)
- `dev/SCOPE_2026-05-07-addendum-covers.md`
- `dev/SCOPE_2026-05-07-addendum-ops-and-accelerators.md`
- `dev/SCOPE_2026-05-07-addendum-popup-languages.md`
- `dev/SCOPE_2026-05-07-addendum-tooling-roadmap.md`
- `dev/SCOPE_2026-05-08-addendum-ai-xrefs.md`
- `dev/SCOPE_2026-05-08-addendum-audio-epubs.md`
- `dev/SCOPE_2026-05-08-addendum-cross-denom-compare.md`
- `dev/SCOPE_2026-05-08-addendum-kenyon-textcrit.md`
- `dev/SCOPE_2026-05-08-addendum-pd-translations.md`
- `dev/SCOPE_2026-05-08-addendum-prettification.md`
- `dev/SCOPE_2026-05-08-addendum-robustness.md`
- `dev/SCOPE_2026-05-08-addendum-security.md`
- `dev/SCOPE_2026-05-08-addendum-textcrit-deep-dive.md`
- `dev/SCOPE_2026-05-09-addendum-ai-notes.md`
- `dev/SCOPE_2026-05-09-addendum-edition-templates.md`
- `dev/SCOPE_2026-05-12-addendum-gamma-4-expansion.md`
- `dev/SCOPE_2026-05-12-addendum-xi-18-x-style-src.md`
- `dev/SCOPE_2026-05-14-parallel-bible.md`
- `dev/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md`
