# Split deep-audit — run plan (2026-06-05 · round 5 · end-of-project / beta sweep)

**Status:** READY 2026-06-05 — auditor bumped to round 5 + made current (new `rx-surfaces` dim) + split-ready (LANE win/mac); two fresh sessions run disjoint dims (N95=tests/builds · Mac=code-review) → merge on the N95. Informational (beta ships regardless).

> **Two FRESH sessions** (Windows N95 + Mac) run `deep-audit` **split across both machines**, then merge
> on the N95. **Informational:** the `v1.0.0-beta.1` beta ships today regardless — findings feed the
> post-beta fix queue ("beta being beta").
> Auditor: `.claude/workflows/deep-audit.js` — already **round 5**, **made current** (new `rx-surfaces`
> dimension), and **split-ready** (LANE mechanism). No further engineering needed; just set LANE + run.

## Why split (and why NOT a VM)
The audit's ultimate throughput ceiling is the **Max rate limit, which is per-account, not per-machine** — a
rented VM shares it and adds setup/cost (ruled out for any occasion). But the N95 alone runs the auditor at a
**cap of 2 concurrent agents** (4-core local limit), leaving rate headroom unused. The two machines you ALREADY
own use **different resources**: the N95 (SSD) runs the dims that execute **pytest + builds** (local-compute
heavy); the Mac runs the **code-review** dims (model-call-bound, disk-light — the Mac is HDD-bound). So they
truly parallelize with minimal contention, and the combined local concurrency saturates the rate ceiling the
N95 can't reach alone. Zero cost, zero setup.

## The split — 16 dimensions, disjoint
| LANE | Machine | Dimensions | Why this machine |
|---|---|---|---|
| **win** | N95 (SSD) | `tests-run` · `opt-build` · `byte-stability` · `rx-surfaces` | execute pytest + build EPUBs (epubcheck, cross-piece link scan) → need the fast disk + local compute |
| **mac** | Mac (HDD) | `correctness` · `security` · `code-debt` · `tests` · `docs` · `data-validity` · `concurrency-caching` · `cross-module` · `marathon-boundary` · `opt-vision` · `opt-ingest` · `opt-render` | read + reason (model-call-bound), disk-light |

(`LANE_DIMS` is committed in `deep-audit.js`; `LANE='all'` default runs the full made-current set on one box.)

## Made current (what changed vs mint-11 round 4)
- **New `rx-surfaces` dimension** (2 finders) — audits the code shipped AFTER mint-11 that the other dims only
  under-cover: the **file-splitter** (`apply_file_split` — cross-piece href integrity, well-formed cuts, spine
  completeness = silent dead-link data-loss), the **badge-merge** (`apply_badge_markers` — note-count
  conservation + unescaped-interpolation XSS), the **nav enrichment** (`enrich_nav_chapters` — must run LAST;
  the NAV-011 spine-order class), **font embed** (`@font-face` OPF-declaration), **scaffold-strip** (over-greedy
  regex), and the **dict-easton re-ingest** (`_reingest_eastons.py` — XHTML-escape + body pairing + the
  truncation guard). Build-verifying → assigned to the **win** lane.
- `ROUND` 4→5, `NOW` →`2026-06-05`. The 15 prior dims are unchanged (their targets already include
  `build_edition.py` etc.; `rx-surfaces` adds the emphasis).

## Run protocol — each fresh session
1. `git fetch origin && git checkout main && git pull --ff-only origin main` — both lanes at the SAME HEAD.
2. Edit `.claude/workflows/deep-audit.js`: set `const LANE = 'win'` (N95) or `'mac'` (Mac). **One-line LOCAL
   edit — do NOT commit it** (the audit is read-only; LANE='all' stays the committed default).
3. Launch `Workflow({scriptPath: "<repo>/.claude/workflows/deep-audit.js"})`. **Confirm the startup log:**
   `deep-audit round 5 | depth=deep | <N> dimensions | …` — win → **4** dims, mac → **12** dims. (If it echoes
   16, your LANE edit didn't take — fix before letting it run.)
4. On completion, parse `JSON.parse(<output-file>).result` → `{survivors, dropped, fixesPlanMarkdown,
   completeness}`. Save your lane's survivors JSON.

## Merge protocol — the N95 owns it
1. **Mac** writes its result to `_audit-split/findings-mac.json`, commits it to a throwaway transfer branch
   **`lane-transfer/audit`** (mirrors `lane-transfer/rules`), pushes. (Read-only audit → never touches main.)
2. **N95** `git fetch` + checks out `lane-transfer/audit` → now has both `findings-win.json` +
   `findings-mac.json`.
3. **N95** runs a merge-synthesize — template = `.claude/workflows/deep-audit-continue.js` (its
   inject-findings-as-literal → verify-first → synthesize pattern): inject BOTH lanes' survivors → optional
   re-verify the cross-lane union → **ONE** synthesize (phased fixes plan, authoritative counts) + completeness
   critic.
4. Output `docs/superpowers/notes/2026-06-05-round5-split-audit-findings.md` (the merged fixes plan); commit on
   main; delete `lane-transfer/audit`.

## Sequence (USER-decided 2026-06-05: "#2–5 first")
- **Mac completes the re-ingest FIRST** — defects **#2–5** (lang-greek Theós 1,196 · topic-torrey 596 ·
  lang-greek Phōs 76 · topic-nave 87) per `docs/superpowers/notes/2026-06-06-auto-note-reingest-plan.md`, one
  defect per commit, same ship bar. Only #1 (dict-easton un-cap, `a3f456a6`) has shipped so far.
- **THEN both lanes sync → run this split audit on the COMPLETE content** (#1–5 corrected). Auditing the final
  state, not a half-corrected one, was the user's call — clean-and-complete over strict ship-today.
- The audit is still INFORMATIONAL for the beta (a beta can ship even with surviving findings); findings → a
  prioritized fix pass (security + silent-data-loss first). **#2–5 are NOT added to the auditor's
  `DEFERRED_BY_DESIGN`** — they will be FIXED before the audit runs, so there is nothing to defer.
- **[USER] review item:** `rev 1:8` has a pre-existing "A Alpha" duplicate dict-easton note (head glued "A A")
  that the re-ingest left untouched — de-dup or leave; the audit may flag it (known, minor).

## Constraints
- **Read-only:** the audit never commits to main; the per-lane `LANE` edit stays local-uncommitted.
- **Off-limits marathon core** (`build_standalone.py`, `core/manuscript_*`, `GAPS/`) — read-only context only.
- **No VM** — ruled out for any occasion ([[reference_runpod_cloud_budget]]); the split is the sanctioned way
  to lift the N95 cap.
