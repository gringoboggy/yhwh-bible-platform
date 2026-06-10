# Full Project Audit Program (post-v0.1.0) — Implementation Plan

**Status:** IN PROGRESS 2026-06-10 — P1/P2 executing tonight (engine round-7 + overnight audit + K-R4-1 fix + ① design doc); P3–P5 follow the audit result.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute the user's post-v0.1.0 giant-audit directive (memory `project_full_final_audit_program`): upgrade the deep-audit engine for the program's full scope, run the round-7 everything-audit overnight on the N95 (win-solo, Mac retired till morning), land the round-4 device-QA fix arc (K-R4-1 now, K-R4-2 post-calibration) as v0.1.1 work, and produce the inputs for steps ③ decommission, ④ end-game two-lane master plan, ⑤ per-milestone re-audits.

**Architecture:** The reusable `.claude/workflows/deep-audit.js` engine (find → adversarially-verify → synthesize) is extended in-file (args don't propagate) with 7 new program dimensions (claude-setup, lane-system, github-gitlab, popup-integrity, stack-review, future-work, decommission), updated v0.1.0 facts, and an updated deferred-by-design list; models unpin to inherit Fable 5. While the audit runs in background (read-only, cap=2), the controller does file-disjoint light work: the K-R4-1 TDD fix, the MEMORY.md over-limit trim, and the ① Fable-5 system-mint design doc. Fixes ship verify-first (the engine METHOD: re-check every synthesized finding vs live code before implementing).

**Tech Stack:** Workflow JS orchestration · pytest (PYTHONUTF8=1, `--basetemp`, repo-CWD) · PowerShell · py -3 full-path interpreter.

**Program sequencing note (RULES §3 delegated judgment):** the user-set order is ① Claude-system mint → ② everything-audit. Tonight runs ①'s *engine half* first (the audit tool IS the instrument being sharpened), launches ②, and does ①'s *rules-redesign half* as a DESIGN doc in parallel — because the audit's claude-setup dimension feeds that redesign (findings about rule duplication/contradiction arrive overnight), implementing the redesign before the audit would discard its evidence.

---

## Phase map

| Phase | What | When |
|---|---|---|
| P1 | Truth records + QA-note commit; engine round-7 upgrade; launch audit | tonight, first |
| P2 | Parallel controller work: K-R4-1 fix (TDD) · MEMORY.md trim · ① mint design doc | tonight, while audit runs |
| P3 | Audit completes → verify-first triage → fixes plan → fix phases (incl. K-R4-2 design) | morning / next session |
| P4 | Round-5 device matrix (incl. threshold calibration taps) + rebuild + gates | after P3 fixes land |
| P5 | ③ decommission sweep · ④ end-game two-lane master plan (own writing-plans pass) · ⑤ re-audit cadence | subsequent sessions, with Mac |

---

### Task 1: Commit the round-4 QA note + truth records

**Files:**
- Already created: `docs/superpowers/notes/2026-06-10-kobo-round4-device-qa.md`
- Modify: `dev/SESSION_STATE.md` (prepend turn entry), `dev/IN_FLIGHT.md` (TRACKER-STATE active, this program)

- [x] **Step 1:** Fresh small `Read(limit=6)` of each truth-record's top right before each Edit (RULES guard #3 — truncated reads don't satisfy the Edit gate).
- [x] **Step 2:** Prepend the SESSION_STATE turn entry: round-4 QA ingested (K-R4-1/K-R4-2 root-caused, threshold bracketed 3,313<T≤7,748), audit program opened, engine round-7, audit launched.
- [x] **Step 3:** `git add` + local commit (`audit-program: round-4 QA ingest + program open`). LOCAL ONLY — no push (bandwidth cadence; milestone push comes at P3/P4 close).

### Task 2: Engine upgrade — deep-audit.js round 7

**Files:**
- Modify: `.claude/workflows/deep-audit.js`

- [x] **Step 1: Params.** `ROUND = 7`, `NOW = '2026-06-10'`. Keep `LANE = 'all'` (win-solo full set; Mac retired).
- [x] **Step 2: Models.** Remove the two `model: 'opus'` pins in `findDim`/`runSkepticPanel` (inherit the session model = Fable 5; faster + strongest; `args.model` still overrides). Leave synth/completeness unpinned as-is.
- [x] **Step 3: PREAMBLE facts.** Update SHIPPED STATE line: v0.1.0 (2026-06-10), note count 91,553 (the shipped post-consolidation number), release live at github `releases/tag/v0.1.0`, website deployed. Docs dim: replace the hard-coded "console inventory = 18" with "verify against `CONSOLES` in scripts/web.py".
- [x] **Step 4: dist-packaging prompt** version refs 0.0.3 → 0.1.0 (and "all 3 platforms + font pack + kepub ship").
- [x] **Step 5: DEFERRED_BY_DESIGN additions** (verbatim list in the engine file):
  - 117-chapter-start v1/v2 base displacement = KNOWN + DESIGNED (Mac 2026-06-10 verse-boundary-residual design; v0.1.1 WIN executes) — do not re-flag.
  - K-R4-1 (vnote separators) + K-R4-2 (preview-decline oversized asides) = KNOWN with a fix arc in flight (`notes/2026-06-10-kobo-round4-device-qa.md`) — popup-integrity must EXTEND beyond them, not re-derive them.
  - θ.4 update-feature deferred to v0.1.1 BY DECISION; X posts are POSTED-BY-USER; kepub cross-piece duplicate ids are kepub-generated and excluded by design.
- [x] **Step 6: Add the 7 new dimensions** (full prompts written in the engine; summary):
  - `claude-setup` (find, 2 finders): out-of-repo `~/.claude` settings/hooks/plugins/keybindings + project memory dir (+ the MEMORY.md size breach) + repo `.claude/` + RULES/PLAYBOOK — rule duplication across homes, contradictions, every-session token bloat, hook correctness, setup security. Feeds the ① redesign.
  - `lane-system` (find, 1): LANE_HANDOFF mechanics, lane_handoff.py/lane_ping.py, save-all legs + verification, board protocol, per-box memory mirroring discipline, failure modes.
  - `github-gitlab` (find, 1): read-only `gh api`/`gh release view`/`git ls-remote` checks — release-asset completeness vs SHA256SUMS, descriptions/counts, README/CHANGELOG/LICENSE visibility on both hosts, CI hygiene, mirror divergence, branch protection. Findings-only; GitLab API-gated items flagged for the Chrome-MCP settings task.
  - `popup-integrity` (find, 2): the K-R4 "nowhere else" sweeps on the shipped artifacts — S1 separator coverage across ALL `epub:type="footnote"` emitters; S2 stripped-size distribution per aside kind (list >3,300); S3 every `epub:type="noteref"` target's rendered-position (hidden-ancestor ⇒ teleport class). May run python zip-scans.
  - `stack-review` (optimization, 1): re-justify KEEP PYTHON + tooling/condensation upgrades against the REMAINING program; CONFIRM-OPTIMAL or BETTER PLAN, regression risk explicit.
  - `future-work` (optimization, 1): are the plans for yet-undone work (Phase-D vision, Kings/Samuel marathon, re-verification/re-ingest, parallel-Bible, verse-boundary fix, native-ToC option) optimal under today's capabilities? Per-plan verdict.
  - `decommission` (find, 1): candidates to retire — unarchived one-shot scripts, dead workflows/branches/artifacts/deps/docs — each with path + why-dead + archive-vs-delete recommendation. Never the marathon core/GAPS.
- [x] **Step 7: Dim ordering for cap=2 load spread:** `tests-run` first; `rx-surfaces` late; new read-only dims interleaved.
- [x] **Step 8: Syntax-validate** (top-level await/return are legal only in the runtime's async wrapper — `node --check` false-flags):
  `node -e "new (async()=>{}).constructor(require('fs').readFileSync('<path>','utf8')); console.log('OK')"`
- [x] **Step 9: Commit** (`audit-engine: round-7 program dims (claude-setup, lane-system, github-gitlab, popup-integrity, stack-review, future-work, decommission) + v0.1.0 facts + Fable inherit`).

### Task 3: Launch the overnight audit

- [x] **Step 1:** `Workflow({ scriptPath: '<repo>/.claude/workflows/deep-audit.js' })`, `run_in_background: true`. Confirm the startup log echoes `round 7` + the dimension count (the args-propagation tripwire).
- [x] **Step 2:** Record the runId in `dev/IN_FLIGHT.md` (recovery: `resumeFromRunId` reuses completed finders same-session; orphan-process protocol in memory `audit-orphan-processes` if it must be stopped).
- [x] **Step 3:** Schedule a long fallback wakeup (~50-60 min cadence) in case completion notification is missed; do NOT poll.

### Task 4 (parallel): K-R4-1 — vnote preview separators (TDD)

**Files:**
- Modify: `scripts/build_edition.py` (new pass near `_VN_SEP_*` consts :1906-1913; call site in `build_one` adjacent to `apply_badge_markers` :5248; CSS rule :1909-1913)
- Test: `tests/test_marker_style.py` (new class `TestVnotePreviewSeparators`)

- [x] **Step 1: Write the failing tests** — separator insertion on a real-shaped vnote fixture; idempotency (no double-insert on second run); the hide-CSS covers vnote scope:

```python
class TestVnotePreviewSeparators:
    """K-R4-1: the Kobo eInk Footnote preview is tag-stripped plain text; the
    vnote (translation) asides had no plain-text separators, so header + verse
    + every source-label + translation ran together as one line."""

    VNOTE = (
        '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">'
        "<p><strong>The First Book of Moses, Genesis 1:1.</strong></p>"
        '<p class="vnote-text">In the beginning God created the heaven and the earth.</p>\n'
        '  <p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>\n'
        '  <p class="vnote-hebrew" dir="rtl" lang="he"><em>ב</em></p>\n'
        '  <p class="vnote-source-label">Greek (Septuagint / Swete)</p>\n'
        '  <p class="vnote-greek" lang="grc">ΕΝ</p>\n'
        '<p><a href="#v-gen-1-1" class="vnote-back" title="Back">↩</a></p></aside>'
    )

    def test_source_labels_get_byline_separator(self):
        out = build_edition.add_vnote_preview_separators(self.VNOTE)
        assert out.count('<p class="vnote-source-label"><span class="vn-sep">◦ </span>') == 2

    def test_vnote_text_gets_paragraph_separator(self):
        out = build_edition.add_vnote_preview_separators(self.VNOTE)
        assert '<p class="vnote-text"><span class="vn-sep">¶ </span>In the beginning' in out

    def test_idempotent(self):
        once = build_edition.add_vnote_preview_separators(self.VNOTE)
        assert build_edition.add_vnote_preview_separators(once) == once

    def test_non_vnote_markup_untouched(self):
        html = '<p class="vnote-text-not">x</p><p class="source-label">y</p>'
        assert build_edition.add_vnote_preview_separators(html) == html

    def test_hide_css_covers_all_sep_scopes(self):
        # K-R4-1 widens the K-R3-2 rule: .vn-sep hides EVERYWHERE CSS applies,
        # not only under .verse-notes (vnote asides are not inside .verse-notes).
        assert re.search(r"(?<![.\w])\.vn-sep\s*\{[^}]*display:\s*none", build_edition._VN_SEP_HIDE_CSS)
```

- [x] **Step 2: Run to verify they fail** (`AttributeError: add_vnote_preview_separators` + the CSS regex miss):
  `$env:PYTHONUTF8="1"; py -3 -m pytest "tests/test_marker_style.py::TestVnotePreviewSeparators" -q --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"` (repo CWD)
- [x] **Step 3: Implement** —

```python
_VNOTE_SEP_LABEL_RE = re.compile(r'(<p class="vnote-source-label">)(?!<span class="vn-sep">)')
_VNOTE_SEP_TEXT_RE = re.compile(r'(<p class="vnote-text">)(?!<span class="vn-sep">)')


def add_vnote_preview_separators(html: str) -> str:
    """K-R4-1: bake plain-text separators into the vnote (translation) asides.

    Same mechanism as the K-R3-2 study-cascade separators: the Kobo eInk
    Footnote preview strips tags, so block structure must survive as text.
    ¶ before the verse text, ◦ before each source label; hidden by CSS
    everywhere CSS applies. Idempotent (the negative lookahead skips spans
    already present).
    """
    html = _VNOTE_SEP_TEXT_RE.sub(lambda m: m.group(1) + _VN_SEP_CAT, html)
    return _VNOTE_SEP_LABEL_RE.sub(lambda m: m.group(1) + _VN_SEP_BYLINE, html)
```

  CSS: change `:1912` `".verse-notes .vn-sep { display: none; }"` → `".vn-sep { display: none; }"` (class-wide; there is no context where a visible vn-sep is wanted under CSS). Call site: in `build_one`, in the same per-edition temp-tree pass loop that calls `apply_badge_markers` (:5248) — apply `add_vnote_preview_separators` to every html piece for EVERY edition (vnote popups exist in all editions; intended v0.1.1 output change, release-noted).
- [x] **Step 4: Run the new class + the adjacent suites** (`test_marker_style.py` whole file) — green.
- [x] **Step 5: Commit** (`K-R4-1: plain-text preview separators in vnote translation popups + class-wide vn-sep hide`).
- [x] **Step 6 (deferred to P4, RAM):** full eth rebuild + `dev/verify_kr2_build.py` + epubcheck + artifact spot-check happens with the P4 round-5 build, NOT tonight (never 2 heavy jobs beside the audit).

### Task 5 (parallel): MEMORY.md over-limit trim

**Files:**
- Modify: `C:\Users\bogda\.claude\projects\C--Users-bogda-Documents-YHWH-v2-4-full\memory\MEMORY.md` (25.4KB > 24.4KB cap — entries truncate-loaded)

- [x] **Step 1:** Shorten the longest index lines to ≤~200 chars by moving detail into their topic files (the topic files already carry it; verify before cutting); keep every entry one line. Do NOT delete entries.
- [x] **Step 2:** Verify the file is under 24.4KB.

### Task 6 (parallel): ① Fable-5 system-mint DESIGN doc

**Files:**
- Create: `docs/superpowers/notes/2026-06-10-fable5-system-mint-design.md`

- [x] **Step 1:** Inventory the every-session token surface: the triad line/char counts, SessionStart hook output, MEMORY.md, remember.md — measured numbers per item.
- [x] **Step 2:** Design per addendum-3 goals: single-home per rule (RULES vs PLAYBOOK vs memory vs boards — name the home for each duplicated rule class), deterministic hooks over re-read prose (candidates list), bootstrap-read slimming targets, memory index hygiene rules, zero what's-what ambiguity (naming/locations table).
- [x] **Step 3:** Mark which decisions WAIT for the audit's claude-setup findings (implementation = next session, findings in hand). Commit the doc.

### Task 7 (P3, after audit): verify-first triage + fixes plan

- [ ] **Step 1:** Parse the result (`JSON.parse(outputFile).result`): survivors, UNVERIFIED-flagged, dropped, fixesPlanMarkdown, completeness gaps.
- [ ] **Step 2:** Ground-truth VERIFICATION pass before any fix (the METHOD: prior rounds found ~40% of synthesized items ALREADY_FIXED/MISDESCRIBED; never blind-implement; re-verify fix arithmetic against live data per mint-11 P6).
- [ ] **Step 3:** Write `docs/superpowers/notes/2026-06-10-round7-findings.md` + a fixes plan; fold in: the K-R4-2 split-by-category design (check 1sa-16-12 / act-23-6 category composition vs the conservative cap), S2's gate-4g (warn-tier until T pinned), completeness-critic lenses for round 8.
- [ ] **Step 4:** Execute fix phases safest-first as LOCAL commits; tests/lints per fix; byte-gate proof for build-path changes (`feedback_bytecompat_and_matrix_invariant`).

### Task 8 (P4): round-5 device matrix + rebuild

- [ ] **Step 1:** Rebuild eth (`py -3 scripts/build_edition.py ethiopian-tewahedo --version ... --output-dir dist --force`) + verifier gates + epubcheck (`--jar` the site-package jar) + kepubify + kepub gates.
- [ ] **Step 2:** Compute the calibration tap-list from the NEW artifact: 5-6 real badges with stripped sizes ~3.5k/4.5k/5.5k/6.5k/7.5k (script: the zip-scan from the K-R4 QA note §K-R4-2) → write the round-5 matrix note: separator eyeball (translations now break apart) + calibration taps (pin T) + Greek-spreading recheck + reading-font datum.
- [ ] **Step 3:** Swap onto `G:\` (Move-Item the old copy to E:, never delete) when the Kobo is plugged in. Milestone 5-leg save (`pwsh -File save-all.ps1`) + LANE_HANDOFF board update for Mac's morning (its arms: item-8 K-R4-2 design review, W1 AB①, round-5 toc datum).

### Task 9 (P5): program steps ③/④/⑤

- [ ] **Step 1:** ③ Decommission sweep = its own fix-arc from the decommission dim's verified findings (archive-first, delete only with the user's standing rules).
- [ ] **Step 2:** ④ End-game two-lane master plan = its own writing-plans session (NOT tonight): current state → DONE-DONE (incl. Ge'ez/Amharic), win+mac standing work-streams, supersedes the v0.1.0 replan as the active master sequence.
- [ ] **Step 3:** ⑤ Re-audit cadence: re-run deep-audit (round 8+) after each major milestone, feeding completeness-critic lenses forward, until convergence at DONE-DONE.

---

## Self-review notes
- Spec coverage: program ①–⑤ all mapped (①: Tasks 2+6; ②: Tasks 3+7; ③: Task 9.1; ④: Task 9.2; ⑤: Task 9.3); round-4 directive mapped (fix: Task 4 + Task 7.3; "nowhere else" sweep: popup-integrity dim + S1-S3).
- The K-R4-2 fix is deliberately NOT implemented tonight: T unpinned (3,313<T≤7,748) and the conservative cap would over-split ~600 asides; the round-5 calibration (Task 8.2) pins T with one tap-pass first. This is sequencing, not deferral-for-effort.
- Hardware constraints honored: audit read-only at cap=2; no rebuild tonight beside it; pytest single-shard rules in the tests-run prompt.
