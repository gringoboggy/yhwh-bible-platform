# Future Roadmap — Explicitly Deferred Ideas

Ideas raised, evaluated, and consciously postponed. Not abandoned — just
out of scope for the current shippable product.

Owner notes: revisit this list when major milestones land (after first
retail submission, after first sales data, after editorial team grows
beyond solo).

---

## Web UI for note editing

**Status:** **BUILT in v28a-27 (Phase ι.2) — see scripts/web.py.** Originally
deferred to post-retail-launch; built earlier per direct user request.

**What shipped:**
- stdlib-only HTTP server (no Flask dependency)
- 3-column SPA: books / notes-in-book / editor
- Per-edit save through `atomic_write` + `ensure_backup`
- Live HTML preview, per-kind word-budget feedback inline
- Per-kind template scaffolds for adding new notes
- Filter notes by kind, text, or quality-flag status
- Default localhost-only bind (`--host 0.0.0.0` opt-in)
- Launched via `./ebible web`

---

## Other ideas explicitly deferred

### Note state machine (draft → reviewed → approved)
**Why deferred:** Overkill for solo editor; git history covers what
matters. Revisit if/when editorial team has multiple reviewers.

### Cross-edition diff viewer
**Why deferred:** `git diff v28a-N v28a-M` already provides this. A
GUI version would be nice but isn't pulling its weight.

### Snapshot tests for built EPUBs
**Why deferred:** epubcheck + the manual smoke-test cover the regression
risk. Snapshot tests would lock in HTML formatting that we may want to
change deliberately.

### Hypothesis (property-based) tests
**Why deferred:** Nice-to-have for fuzzing input parsing. Not pulling
weight against the existing 41 unit tests for a project this size.

### Concurrent inject across books
**Why deferred:** Measured wash on this system (I/O bound, not CPU
bound). Real-world deployments may differ.

### HTML minification beyond DEFLATE
**Why deferred:** Measured 0.4% reduction post-DEFLATE. DEFLATE already
saturates the redundancy.

### Custom DSL for notes (replacing tuples)
**Why deferred:** Tuples are fine. A DSL adds parser maintenance burden.

### IDE / VS Code extension
**Why deferred:** Niche audience (one person). Existing tooling is
adequate.

### Auto-generated API docs
**Why deferred:** Docstrings + `--help` cover discovery for a project
this size.

---

## Items definitely NOT planned (out of mission)

- Modern English translation of any book (out of license scope —
  unchanged).
- ~~Audio Bible / TTS rendering~~ — **lifted.** The ρ-cluster
  (ρ.1-ρ.5) is now scheduled per
  `dev/SCOPE_2026-05-08-addendum-audio-epubs.md`. PD LibriVox
  recordings embedded via EPUB 3 native `<audio>`. Not TTS —
  curated PD human-narrated audio.
- Mobile native apps (web is sufficient — unchanged).
- ~~Print-on-demand pipeline~~ — **partially lifted 2026-05-12.**
  Print PDF for sample chapters (ε.7 press kits) + full-edition
  multi-format export (ψ.22 — PDF / MOBI / HTML / TXT) are in
  scope. KDP paperback + IngramSpark integration are still
  deferred.
- ~~Multi-language UI~~ — **lifted 2026-05-09 (PLAN θ.5).**
  Localized UI shells (Spanish, Portuguese, French, German) are
  in the LONG TRACK once a real buyer ask materializes. The
  editorial apparatus baseline remains English.

## 2026-05-12 refresh

This page's "Web UI for note editing" deferred-but-built entry
remains accurate (built in ι.2). The "Other ideas explicitly
deferred" section is still relevant. Lifted-items above moved
from "definitely NOT" to "active/scheduled" per the post-v1.0
operating model (see `dev/PROPOSAL_FEATURE_LANDSCAPE.md` §6).
