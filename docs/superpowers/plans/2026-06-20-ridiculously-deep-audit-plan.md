# Ridiculously Deep Project Audit — Plan (post next big phase)

**Trigger:** Execute after completion of the next major phase (e.g., current M2/M3/M4 device or parity work, or Ge'ez standalone milestone).

**Auditor to use/update:** Primary reusable engine is `.claude/workflows/deep-audit.js` (parallel sub-agent, adversarial skeptic panel, find-verify-synth). In-repo complement: `audit.py` (code/EPUB), `dev/cc-hooks/memory_hygiene.py` (out-of-repo), `scripts/audit_*.py`, `dev/trace_*.py`, `scripts/ci.py`, `lint_rules.py`, `ebible verify`, `validate_*`, reader sim gates (`verify_kr2_build.py`, `reader_sim/`), `dev/REPO_MAP.md` / `MATRIX_MAP.md` integrity.

**Update the auditor first (before deep run):**
- Bump all PREAMBLE facts to current truth: v0.1.0+ (note count 91,553 shipped, 91,720 source, 4 canon + 2 standalone Ge'ez/Amharic in progress, consoles=21+, targets=Apple/Kobo/Kindle/Play + plain, etc.).
- Full cross-machine (Win N95 + Mac 8GB iMac): add "OS Divergences Matrix" dim or checks. Enforce identical in-repo rules/behavior (hooks, radars, save cadence, bootstrap, parity plan). Document/ implement only OS-required diffs (py invocation, paths, RAM kill lists/processes, bundle drives, shell, build tools, hook wiring, low-RAM restrictions for MCP/browser). Use `CROSS_LANE_RULES_PARITY_PLAN.md` as input.
- Redundancy engine: scan project (structure/dupe scripts), program (code dupe, god-modules), bibles (duplicate notes/bodies/xrefs across books/versions, overlapping popups, redundant verse strings in popups, duplicate content in books themselves), popups/language (dupe strings, identical asides).
- Contradiction engine: zero-tolerance scan for conflicting facts (counts, book numbers 83 vs 87, edition lists, version strings, rules vs code, online metadata vs local, Win vs Mac "truth", sim expectations vs actual). Fail on any.
- Sims focus: exhaustive on `reader_sim/`, `verify_kr2_build.py`, gates (apple/kobo/kindle/play). "What could go wrong": false negatives/positives, coverage gaps (e.g., all targets, all note kinds, long asides, cross-piece, KFX/ kepub specifics), improvements (more adversarial cases, parallel, better oracles, visual regression). Add dims for each sim target + "sim integrity".
- Optimizations everywhere: code perf/bloat, data (notes/popups/bibles dedup), rules (dupe text), repo/out-of-repo (memory bloat, dead files), website (dupe assets, build), GH/GL (release metadata, descriptions, SHA), CI/build matrix, automation (lane_watch/ping/handoff/radars/hooks — failure modes, guards). "Is this the optimal way?" verdict per surface.
- Markup integrity: zero broken <> , strings, pagebreaks, illogical formatting in *any* offered artifact (plain EPUB, Apple, Kobo kepub, Kindle m4b/safe, playbooks, docs, website). Extend B/C categories in audit.py + add variant-specific scans (e.g., for --target-reader).
- Two-machine automation safety: dedicated dim on lane_system, radars, save, handoff, bootstrap, parity. What can go wrong (dirty tree, behind misdetect, unpushed handoff, mirror skew, stale per-box memory, OS-specific exec diffs causing desync). Add/verify all safety guards. "Always consider both machines" rule.
- Online truth: checks for website (`website/dist/`, build.mjs), GH/GL (releases, metadata, descriptions, counts, social card, README/CHANGELOG sync). Any big change *must* update all truth records (SESSION_STATE, IN_FLIGHT, LANE_HANDOFF, online) to current truth in same change. Add "online sync" verification pass.
- Small/big work integrity: auditor must have "touch graph" or explicit "verify no cross-scale breakage" pass. Rule: after any change, run relevant auditor slice on "bigger" and "smaller" surfaces it might have touched.
- Adversarial + revised: use skeptic panels (runSkepticPanel), re-verify every finding vs live code/data *before* fix. Parallel sub-agents (cap per memory), merge, full revision pass.
- Update for current truth + OS: before run, sync facts from both machines (Win N95 specifics, Mac 8GB limits, paths, invocation). Make auditor "run on both" or produce Win/Mac reports + parity section.
- Everything considered: all work (Win/Mac) must consider full system (repo+out+website+online+both OS+automation+integrity+truth). Codify in RULES (new §9 below) and bootstrap.

**Execution cadence (new standing rule):**
- Smaller/focused sanity/audit passes: ad-hoc or on radar triggers, after any small change that might touch bigger (or vice versa).
- Ridiculously deep full audit: after each major phase close (adversarial, full dims, both lanes, verify-first fixes, no assumptions). "Step back" explicitly before/after big work.
- Windows (main) leads coordination; both execute split dims + parity.

**Deep audit structure (update deep-audit.js + audit.py + this plan before run):**
Dims (expand existing + new):
- Existing (code, data, tests, docs, security, etc.) + 
- Redundancies (multi-level: project/scripts, program, bibles/books/verses, popups/language/strings — dedup engine).
- Contradictions (zero-tolerance fact consistency across all, including Win/Mac, online/local, sim vs real).
- Sims (reader_sim + all verify_*/gates — exhaustive what-could-go-wrong, false results, coverage, improvements).
- Optimizations (everywhere listed above — "is optimal?" + safe impl).
- Markup (zero broken in all targets + docs + website).
- Two-machine automation (lane/radar/handoff/save/hooks/ parity — failure modes + guards).
- Online truth (GH/GL/website/releases/metadata/social — sync + update rule).
- Cross-OS/machine (parity plan enforcement, OS diffs only where code exec differs).
- Small/big integrity + "everything considered" pass.
Adversarial: skeptic panel per finding. Revised: full re-run of net after candidate fixes.

**Output:** findings (with file:line or equiv), severity, disposition (fix/plan/accept with reason), merged report, updated auditor, all truth records + online metadata refreshed to current, no broken markup anywhere.

**Pre-run:** bump auditor with current facts (both machines), sync CROSS_LANE_PARITY, add above dims. Run smaller slices first.

Update all docs (RULES, PLAYBOOK, AGENTS, plans, parity, auditor engine) with this requirement. Make "step back + audit" and "consider both machines + everything + online truth" explicit in every mental model and bootstrap.

This is now part of the self-upgrading matrix (RULES §1). Run after next big phase. Both lanes full consideration. Professional finish: zero redundancy, zero contradiction, zero broken, optimal everywhere.