# Round 9 — parallel audit + platform EPUB research

**Status:** PLANNED — start only after Round-8 remediation gate is green.
**Supersedes for audit purposes:** Round-8 findings doc remains authoritative for closed ticks;
Round 9 re-verifies survivors + adds platform research dimensions.
**Pointers:** Round-8 runbook `plans/2026-06-15-round8-parallel-audit-session.md` · engine
`.claude/workflows/deep-audit.js` · merge `.claude/workflows/deep-audit-merge.js` ·
platform matrix `notes/2026-06-18-platform-implementation-matrix.md` (filled during R9).

---

## Gate — do not start Round 9 until

- [ ] `docs/superpowers/notes/2026-06-16-round8-split-audit-findings.md` — 0 open HIGH, 0 open MEDIUM
- [ ] Mac: `refactor.py` cache invalidation + `inject_book` write test + `ci.py` parity
- [ ] WIN: P4 gates green (`trace_matrix`, `ebible verify`, `lint_rules`, pytest shard spot)
- [ ] `SESSION_STATE` top entry: **ROUND-8 REMEDIATION COMPLETE**
- [ ] User handoff pack: Kobo tap list (plan §4 B6) + Play artifact path (`EREADERS.md` §Play)

Device QA (Kobo taps, Play phone) may run in parallel with the last Mac ticks; Round 9
starts from a merged remediation commit.

---

## Purpose

| Round 8 | Round 9 |
|---|---|
| Is the codebase honest and shippable? | Do we have a researched plan for each reader before coding M4b / M2 / Play / Kobo tail work? |
| Code + release surface audit | Code regression sweep **+** four platform research briefs |

**Deliverables (findings-only until user approves):**

1. Merged code audit survivors (regression)
2. `notes/2026-06-18-round9-audit-findings.md`
3. Four platform briefs: `notes/2026-06-18-platform-{apple,kobo,kindle,play}.md`
4. `notes/2026-06-18-platform-implementation-matrix.md` (options ranked per feature × reader)

---

## Lane capabilities (carry from Round 8)

### Windows

- Pytest shard gate (`scripts/pytest_gate_shard.py`)
- Artifact proof builds @ `dev/.audit-build/`
- `audit_epub_structure` + `verify_kr2_build` + popup S1/S2/S3
- `lane_watch.py` v3 cross-lane poll
- Platform research: **Kobo** (build path) + **Play Books** (staging)

### Mac

- Round-8b thorough 18-dim adversarial audit (Fable 5)
- Device-adjacent context: Apple Books, Kindle STK + phone QA
- M3 attach, ncx glossary, Phase 4 ingest guards
- Platform research: **Apple Books** + **Kindle**

---

## Engine setup (both lanes — local only, never commit LANE flip)

1. Pull; `lane_handoff.py mark-seen`
2. Edit `.claude/workflows/deep-audit.js`:
   - `const ROUND = 9`
   - `const NOW = '<session-date>'`
   - `const LANE = 'win'` or `'mac'`
3. Append Round-8 **CONFIRMED-KNOWN** / **LOW-deferred** to `DEFERRED_BY_DESIGN`
4. Feed `PRIOR_SURVIVOR_TITLES` from round-8 merged doc
5. Launch: `Workflow({ scriptPath: "<repo>/.claude/workflows/deep-audit.js" })`

### Startup log tripwire

| Lane | Expected dims |
|---|---|
| **win** | **11** — 7 replay + `platform-kobo` + `platform-play` + (replay includes tests-run…) |
| **mac** | **22** — 18 replay + `platform-apple` + `platform-kindle` |

If count wrong, LANE flip did not take — fix before running.

### Outputs

- **Mac:** `_audit-split/findings-mac.json` → push `lane-transfer/audit`
- **WIN:** `_audit-split/findings-win.json` locally until Mac branch in hand
- **Merge (WIN):** `deep-audit-merge.js` → `notes/2026-06-18-round9-audit-findings.md`
- **STOP** — present findings + platform briefs; no fixes until user approves

---

## Dimension split

### Replay (regression)

**WIN (7):** `tests-run`, `opt-build`, `byte-stability`, `rx-surfaces`, `claude-setup`,
`popup-integrity`, `github-gitlab`

**Mac (18):** per `round8-parallel-audit-session.md` §Round 8b list

**Extra lenses:** cross-edition bleed; `resolve_book_code` gaps; post-process paths
(`kindle_post`, kepubify); refactor/inject_book fixes verified

### Platform research (NEW — 4)

| Dim | Lane | Authoritative UX docs |
|---|---|---|
| `platform-apple` | Mac | `notes/2026-06-15-apple-m2-layout-directive.md`, `EREADERS.md` §Apple |
| `platform-kobo` | WIN | `EREADERS.md` §Kobo, K-R4/6/7/9 notes, `dev/kobo_tap_calibration.py` |
| `platform-kindle` | Mac | `notes/2026-06-15-kindle-phone-qa-kindle_img.md`, `kindle_post.py` |
| `platform-play` | WIN | `EREADERS.md` §Play protocol, M5 catalog row |

Each dim produces the template in `notes/2026-06-17-platform-research-template.md`.

---

## Parallel schedule

| Step | Windows | Mac |
|---|---|---|
| R9-0 | Pull; local `ROUND=9` `LANE=win` | Pull; local `LANE=mac` |
| R9-1 | Workflow (~5–8h) | Workflow (~5h Fable 5) |
| R9-2 | Write `platform-kobo.md` + `platform-play.md` | Write `platform-apple.md` + `platform-kindle.md` |
| R9-3 | `findings-win.json` | `findings-mac.json` + push branch |
| R9-4 | Merge + matrix synthesis | Pull; ACK |
| R9-5 | Milestone push; handoff **FINDINGS ONLY** | Review device caveats |

---

## Post-audit fix phase (after user approval)

| Phase | Work | Owner |
|---|---|---|
| F0 | Round-9 code HIGH/MED regressions | Parallel disjoint |
| F1 | Platform design docs from briefs | Mac M2/M4b · WIN Kobo/Play |
| F2 | M4b Kindle fork | Mac build · WIN byte gate |
| F3 | M2 Apple polish | Mac |
| F4 | Kobo K-R4-2 + user tap round 9 | WIN · user |
| F5 | Play profile decision + M5 fan-out | WIN · user phone |
| F6 | P4 + catalog 5/5 + tag prep | WIN |

---

## Operational rules (Round 8 lessons)

1. Verify startup dim count before leaving session
2. Mac: full find→verify→synthesize (not fast-pass grep)
3. WIN: pytest shard; one heavy job at a time (16 GB)
4. Handoff edits milestone-pushed (`lane_watch` UNPUSHED nag)
5. `LANE` + `REPO` local only
6. Merge → single findings doc → STOP for approval
7. Platform briefs committed with merge (not chat-only)