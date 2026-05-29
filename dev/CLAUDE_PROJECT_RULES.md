# Claude project rules — the Bible publishing platform

**Last updated:** 2026-05-21 (de-staled + indexed; corpus/plan/map pointers refreshed).
**Purpose:** the durable, in-repo reference for how any Claude
(or returning-user) should think about working on this project.
Memory comes and goes; this doc is the source of truth.

If anything in this doc conflicts with a one-off instruction from the
user, the user wins for that turn — but the rule stays as written.

**Operational guard — package installs under auto-mode (added 2026-05-25):** Before
installing ANY package that is NOT already in a committed dependency manifest
(`requirements*.txt`, `pyproject.toml` `[project]` / `[project.optional-dependencies]`,
`package.json`), proactively **ask the user to turn auto mode OFF first**, then install
once they confirm. Auto-mode soft-denies agent-chosen undeclared-package installs as a
supply-chain risk (also wired in `~/.claude/settings.json` `autoMode.soft_deny`), so
attempting one under auto hits a surprise mid-task denial. No pause is needed if the
package is already declared in a manifest or the user explicitly asked to install it.
The durable fix is to DECLARE build/tool deps in a manifest.

**Operational guard — sources are NOT missing (added 2026-05-26):** Before concluding that
any corpus / ingest / translation / popup work is "blocked on missing sources" — or asking the
user to supply a source — **STOP. Every source this project needs is already on-disk OR has a
documented plan.** Look properly first, in this order: (1) read the plans — `dev/archive/PLAN_2026-05-21.md`
§4.1 + `dev/AUDIT_2026-05-23-DEEP.md` (they inventory what exists + where); (2) check `content/sources/`,
`content/translations/sources/`, `_acquire/` (one level above the repo, gitignored), the **top-level
PDFs** (arbitrary filenames — do NOT grep by book name, you'll miss them), the `GAPS/` Geʽez folder,
and the **web sources the plans name** (e.g. la.wikisource for the Clementine Latin appendix, archive.org
for the patristic works); (3) verify CURRENT status against `dev/CHANGELOG.md`, not stale plan labels.
This was a **3× recurring** mistake (Claude wrongly declared "blocked on sources" + asked the user to
supply them, 2026-05-26). The ONLY legitimate source ask is a genuine licensing/credential gate (per the
license-flagging rule) — never "I can't find it." (Memory: `sources-already-in-place`.)

**Operational guard — re-Read the big truth-record MDs RIGHT BEFORE editing them (added 2026-05-28, user-directed):**
`dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`, and `dev/CHANGELOG.md` are large enough that the **Read tool returns a
truncated/partial view** — and a *truncated* read does **NOT** satisfy the Edit tool's "must read first" gate. So an
`Edit` attempted after only the session's earlier truncated read (or after an `offset` read that itself errors on the
token cap) fails with *"File has not been read yet"* and wastes a round-trip. **Before editing any of these (or any file
big enough to truncate on Read): do a fresh small-region `Read` of the exact lines you're about to change — e.g.
`Read(path, limit=6)` for a top-of-file prepend — immediately before the `Edit`, in the same or the prior step.** These
files are newest-entry-at-top, so a `limit=6` head read covers the usual prepend target; for a mid-file edit, read a
small window around it. This is cheap and removes the retry loop entirely. (Cost three failed edits on the Task-4
truth-record update, 2026-05-28, before a clean head-read fixed it. Memory: `reread-before-editing-big-md`.)

## Rules map — which § governs what (jump here first)

| § | Governs |
|---|---|
| **0** | Bootstrap protocol — read-order (RULES → SESSION_STATE → PLAN) + the always-there maps (MATRIX_MAP, REPO_MAP). |
| **1** | North star — the builder demo; corpus depth; patristic-voice composition; the two standalone parallel Bibles; the self-upgrading matrix. |
| **2** | Universal principles (carried from SCOPE 05-07/08). |
| **3** | Sequencing rules (how to order work). |
| **4** | Save semantics — "save" = local commit; checkpoint saves; "continue" ≠ "save". **⚠ BEFORE every save: `python -m ruff format <every file you generated/regenerated>` — ESPECIALLY `content/translations/<id>/` stores (recurs on EVERY ingest) — or the pre-commit hook `ruff format --check .` BLOCKS the commit. ruff reflows whitespace only (data + baked popups unchanged). Full rule: §7 "Formatting + committing".** |
| **5** | Phase / commit tracking. |
| **6** | UI conventions — canonical book/chapter order, cross-linking, styling, reactivity, additive-feature defaults. |
| **7** | Code conventions — backend, schema migrations, project structure, one-shot ship scripts. |
| **8** | Testing conventions — arc-close pin convention. |
| **9** | **Mental models** — step-by-step recipes: add an edition feature / translation / popup language / per-book asset / uploadable binary / static route / meta-tool / aggregate API / feature endpoint / **corpus-growth (χ-cluster)** / four-tier defensive system / style knob / god-module extraction / Δ-family index-backed op. |
| **10** | What this project is NOT (scope guardrails). |
| **11** | Continuity protocol — keep `SESSION_STATE.md` current. |
| **12** | Retrospective protocol — keep `CHANGELOG.md` + the rules current. |
| **13** | Topic-shift protocol — audit before pivoting. |
| **14** | Session-resume / state-uncertainty audit. |
| **15** | **Chain of command** — the tier hierarchy (user > rules > skills > defaults) as a matrix. |

Companion maps: `dev/MATRIX_MAP.md` (data-flow + base-HTML), `dev/REPO_MAP.md` (file/folder index), `dev/PLAN_2026-05-24-end-scope.md` (roadmap), `dev/CHANGELOG.md` (shipped chronology).

**Lifecycle companion: `dev/SESSION_PLAYBOOK.md`** — the order-of-operations guide (session start → work → **verify** → finish-clean) with the **consolidated verification gates** ("what passing checks means") + the consolidated environment/gotcha list in one place. Read it when you need the session-end checklist or the exact gate commands; this RULES file remains the topic-organized authority on each rule.

---

## 0. Bootstrap protocol — read these three files first

Every fresh session begins by reading, in this order:

```
1. dev/CLAUDE_PROJECT_RULES.md   (this file — rules + conventions)
2. dev/SESSION_STATE.md          (live snapshot — what just shipped,
                                  what's next, current test count)
3. dev/PLAN_2026-05-24-end-scope.md  (master sequence — deadline-aware
                                  end-scope plan; PLAN_2026-05-21 is
                                  retained in dev/archive/ for
                                  Track B/C detail + phase-history)
```

**"continue" / "push" / "go ahead" at the start of a fresh session DOES NOT bypass this read-order** (added 2026-05-27 — a recurring miss): those words mean *read the triad first, THEN resume the in-flight work*, never *skip to the task*. The triad (~700-900 lines) IS the minimum orientation; a `git log` or a SESSION_STATE-only peek is NOT a substitute for it. A project **SessionStart hook** (`.claude/hooks/bootstrap-triad.ps1`, wired in `.claude/settings.json` at the repo-parent cwd) now injects this reminder at every session start as a forcing function — memory alone can't enforce a per-session automated behavior; only a hook can.

**Session-start environment-health check (after the triad — added 2026-05-27):** Once the triad is read, and *before* starting the in-flight work, do a quick environment pass and surface anything off — never silently mutate the environment:
- **Updates** — check whether Claude Code itself and the enabled plugins have updates available; if so, tell the user and apply **only on their OK** (updates take effect after a restart). Do NOT force an auto-update mid-session: it can shift behavior under live work and cuts against the commit/backup discipline (§4). The *awareness* is the value; the *applying* waits for consent. **After applying any plugin update you MUST run `/reload-plugins`** (user-directed 2026-05-29) so the updated plugins take effect in the live session without losing conversation context — do not leave updated-but-unloaded plugins for the next restart. (A Claude Code *core* update still requires a full restart; only plugin updates are picked up by `/reload-plugins`.)
- **MCP / tools** — confirm the enabled MCP servers connected this session (their tools are present; the user can eyeball `/mcp`); flag any that failed to start. The environment is **tokenless by design** (the user's standing "no external/API hooks, minimal plugins" preference): only local, no-login MCP servers are enabled (e.g. playwright, chrome-devtools, serena, context7), so a failed server means a missing local runtime (Node / Chrome / uv), **never** a login gate. Never re-add a login-required plugin or sonar to make a check "pass."
- Fold the result into the same one-line post-triad confirmation: *phase · what's next · env OK (or the one thing that's off)*.

Ordering is deliberately **after** the triad, not before: orientation is the cheap, established first ritual, and since updates need a restart it would be wasteful to update before re-reading. Keep this to a few seconds — a sanity check, not an audit. (A forcing-function copy can live in the `bootstrap-triad` SessionStart hook if this proves easy to skip.)

**Session-start RAM clear — aggressive + automatic (after the triad, alongside the env-health check — added 2026-05-27, user-directed "make this part of bootstrap protocol"):** this is a RAM-constrained 16 GB box and the user dedicates the machine to Claude, so at **every** session start, before the in-flight work, **end every process NOT needed to run Windows, the network, Claude, or Claude's own toolchain** — freeing RAM for the marathon's heavy vision agents. This is now a **standing bootstrap step**, *not* gated on RAM pressure (the prior memory's "only if free RAM < ~3 GB" gate is **superseded**). Method:
1. **Enumerate** — free RAM (`(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory`), the top process groups by summed working-set, and walk UP from `$PID` (`Get-CimInstance Win32_Process` parent chain) to map THIS session's own tree so it is never a target — typically `pwsh`/`powershell` → `claude` → `WindowsTerminal` → `explorer`.
2. **PROTECT — never kill (this list IS the safety boundary):** Windows core (`svchost`, `dwm`, `Registry`, `Secure System`, `Memory Compression`, `csrss`/`wininit`/`services`/`lsass`/`smss`/`winlogon`/`fontdrvhost`, `conhost`, `RuntimeBroker`, `WUDFHost`, `sihost`, the input hosts `ctfmon`/`TextInputHost`/`TabTip`); the **session tree** (`claude`, `pwsh`, `powershell`, `WindowsTerminal`, `explorer`); **`node`** (the local MCP servers + Claude's runtime — killing them breaks tools mid-session); **`MsMpEng` + all AV/security** (stays ON — declined to disable: no real RAM gain, genuine project-risk near the deadline, Defender auto-restarts anyway); the **network stack** (lives inside `svchost`).
3. **KILL — recoverable background bloat:** background browsers **only when they have 0 visible windows** (`Get-Process msedge,chrome,firefox | ? MainWindowTitle` — a visible window may hold unsaved work, so flag-don't-kill those), `msedgewebview2`, cloud-sync daemons (`iCloud*`/`OneDrive`/`Dropbox`), vendor updaters (Intel `DSAService`/`DSAUpdateService`/`esrv`, etc.), optional MS apps (`M365Copilot`, `Widgets`, `AppActions`, `CrossDeviceService`/`CrossDeviceResume`/Phone Link), the `SystemSettings` app, and the instantly-respawning shell hosts (`SearchHost`, `StartMenuExperienceHost`, `ShellExperienceHost`). Also any **leaked `python`/`java`** orphaned by a crashed prior session (a fresh session has none of its own running yet). Use `Stop-Process -Id <id> -Force` per-process so a denied service is *reported*, not silently skipped.
4. **Report** the kill table + RAM reclaimed, and **flag (don't blind-kill) any unfamiliar large consumer** for the user to decide. Fold the freed-RAM figure into the same one-line post-triad confirmation (*phase · next · env OK · RAM freed*).

Under auto-mode this runs **without a per-session prompt** — the PROTECT-list is the safety boundary and every KILL target is recoverable (re-launches on demand; browsers restore tabs). Pause only for (a) a browser with open windows or (b) an unfamiliar large RAM consumer. The `bootstrap-triad` SessionStart hook reinforces this step alongside the triad read. (Memory: `session-hygiene`; concurrency interplay: `feedback-concurrent-agent-cap`; the session-END junk/temp sweep is the counterpart — PLAYBOOK §6.5.)

**Always-there maps (user-directed 2026-05-21):** for ANY "where does X
live / how does data flow / what feeds the build" question, check the maps
FIRST — never grep blind. `dev/MATRIX_MAP.md` traces the DATA-FLOW (config →
loaders → matrix/build/inject → consumers + the base-HTML structure & coverage)
and names the exact module; `dev/REPO_MAP.md` is the FILE/FOLDER index (every
directory + what's in it). Companions re-verify them: `dev/trace_matrix.py`
(matrix integrity) and `dev/trace_repo.py` (repo-map completeness) — the
pre-commit `lint_rules.py` enforces both (`plan_coherence`, `repo_map_complete`).

Then optionally — only when the user's ask implies them:
- `dev/CHANGELOG.md` for chronological history of what shipped
  when (skim it when the user references "last session" or
  "earlier work" without specifying)
- `dev/SCOPE_2026-05-07-addendum-*.md` for the specific feature spec
- `HANDOFF_README_v7.md` for deep architecture context (large; only
  when needed)
- `scripts/README.md` for tool reference
- The relevant `content/notes/<book>.py` or `content/candidates/<…>.json`
  for note-level work

After those 3 files, Claude is fully oriented: knows the rules, knows
the state, knows the sequence. **Total ~700-900 lines** — minimum
bandwidth orientation by design.

Never dump status to the user after orientation. Confirm in one line
("Read state, current at φ.1, next is π.4-B — proceeding") and
proceed to the actual request.

---

## 1. The north star

**The builder demo.** (Pivoted 2026-05-14 at Ω.0: project went from
for-sale publishing platform to free public app. ISBN / ONIX / sales
infrastructure dropped — see `dev/SCOPE_2026-05-14-omega0-free-
public-pivot.md`.) End-to-end:

```
1. Open /wizard
2. "Make a Catholic study Bible" (or pick another starting edition)
3. Step through 7 cards: start-from, branding, theme, content
   (canon + kinds), traditions, review, build
4. Click BUILD → an EPUB downloads with the chosen theme, only the
   picked notes, and verse popups in the configured languages.
   EPUB dc:identifier is a generator URN (urn:yhwh:edition:<id>:
   <build-hash>) — not an ISBN; the build is not for resale.
5. Builder says "wow, that's mine" — yes, that's it.
```

A companion `/build-tracker` console (Ω.0 cluster) shows the
builder exactly what is enabled in their current edition (per book
× chapter note counts, per-kind breakdown, canon coverage) so the
build choices are visible before BUILD is clicked.

### Corpus depth target

The Ethiopian Tewahedo edition is the **superset** that all other
editions filter from. **Original target corpus size: 35,000–40,000
notes** — long since exceeded. **Live count: see `dev/SESSION_STATE.md`**
(67,715 as of 2026-05-21; do NOT hard-code a figure here — it rots).
Drawn from public-domain sources via the `prospect → promote` pipeline
and the reference-corpus ingestion (`dev/MATRIX_MAP.md` → "Reference-corpus
ingestion"). Other editions are subsets; their note counts fall out
automatically from canon + kind filtering.

Corpus floor met with large headroom. Continued growth via reference-work
ingestion (Nave's, Easton's, …), χ-AI-xrefs (LLM-backed thematic
cross-references), and γ-cluster expansion is **opportunistic, not blocking** —
the depth claim against every competing free Bible app is
comfortably satisfied. Future γ-cluster ships add depth in specific
dimensions (Tewahedo distinctive readings, manuscript-text-critical
apparatus) rather than chasing raw count.

Every change should make the demo better, simpler, deeper, or
more impressive. If a change doesn't serve the demo, it should be
explicitly deferred unless the user pulled it forward.

### Patristic-source voice composition

**Codified at ω.41 hygiene bundle, 2026-05-13, per AUDIT_2026-05-13-
EOD EOD-W3:**

The γ.4 patristic source corpus (`content/sources/ethiopian_
commentaries.json`, currently 1,065 entries) is **Cyril-led** by
design. The four-voice composition is:

- **Cyril of Alexandria** (48.5%, 516 entries — Alexandrian-Coptic
  patriarchal commentary; the Tewahedo Christological doctrinal
  centerpiece via the Mark → Athanasius → Frumentius apostolic
  lineage).
- **Jubilees (Ethiopian tradition)** (18.8%, 200 entries — uniquely-
  Tewahedo-canonical OT pseudepigraphical witness).
- **1 Enoch (Ethiopian tradition)** (18.0%, 192 entries — uniquely-
  Tewahedo-canonical OT pseudepigraphical witness).
- **Ephrem the Syrian** (14.7%, 157 entries — Syriac patristic
  voice; the East-Syrian-Alexandrian bridge).

**Cyril's plurality is intentional, not accidental.** Cyril is the
24th Patriarch of the See of Mark, standing in direct apostolic
succession to John Mark (Coptic founder) and to Athanasius
(Tewahedo founder Frumentius's consecrator c. 330). His commentary
on the four canonical Gospels is the doctrinal heart of the
Tewahedo flagship. The corpus is therefore "Cyrillian-led patristic
chorus + three Tewahedo-canonical-OT + one Syriac supplement"
rather than an even four-voice quartet.

**If Cyril's share crosses 50% (single-father-majority threshold)**
in future γ.4.7.x detail-wave expansion, that is acceptable per
this rule — but flag it explicitly in the relevant SESSION_STATE
headline so the trajectory is visible. Balance with Ephrem or
pseudepigraphical expansion if a publisher uniqueness-angle pick
(per memory `v1_terminus`) calls for it.

### Five-voice extension (ω.41 §1.B / γ.4.9.D 2026-05-13)

**Extended at γ.4.9.D arc-close, 2026-05-13:** the corpus opened a
FIFTH voice with γ.4.9 Athanasius of Alexandria (the Tewahedo
apostolic-bridge: 20th Patriarch of the See of Mark + Frumentius's
consecrator c. 330 + author of Festal Letter 39 codifying the 27-book
NT canon). The five-voice composition was:

- Cyril of Alexandria — 48.86% (668 entries; 4 canonical-Gospel arcs)
- Jubilees (Ethiopian tradition) — 14.63% (200 entries)
- 1 Enoch (Ethiopian tradition) — 14.05% (192 entries)
- Ephrem the Syrian — 11.49% (157 entries)
- Athanasius of Alexandria — 10.97% (150 entries; γ.4.9.x arc closed)

At γ.4.9.C Cyril's share crossed DOWNWARD below 50% (51.5% → 49.96%)
as the natural consequence of two consecutive Athanasius detail-waves.
Cyril remained plurality-leader at 3.34× the next single-father. This
threshold-crossing was flagged in SESSION_STATE per the trajectory
rule above. The Cyril-remains-plurality-leader durable safeguard pin
in `TestGamma49DAthanasiusArcClose::test_cyril_remains_plurality_
leader_at_arc_close` guards this invariant against future voice-
mixing.

### Six-voice extension (ω.42 §1.C / γ.4.8 2026-05-14)

**Extended at ω.42 hygiene bundle paired with γ.4.8 ship, 2026-05-14:**
the corpus opened a SIXTH voice with γ.4.8 Mäṣḥafä Mäqabyan — the
THIRD uniquely-Tewahedo-canonical text alongside Mäṣḥafä Hēnok (1
Enoch) and Mäṣḥafä Kufāle (Jubilees). γ.4.8 had been DEFERRED across
the entire γ.4 corpus history pending PD source acquisition; the
2026-05-14 user-contributed CC0 1.0 English translation
(archive.org/details/three-books-of-meqabyan-cc0-translation) is the
canonical unblocker.

The six-voice composition is:

- **Cyril of Alexandria** — 47.48% (668 entries) — Alexandrian-
  Coptic patriarchal commentary; the Tewahedo Christological doctrinal
  centerpiece via the Mark → Athanasius → Frumentius apostolic lineage.
- **Jubilees / Mäṣḥafä Kufāle (Ethiopian tradition)** — 14.22% (200
  entries) — uniquely-Tewahedo-canonical OT pseudepigraphical witness.
- **1 Enoch / Mäṣḥafä Hēnok (Ethiopian tradition)** — 13.65% (192
  entries) — uniquely-Tewahedo-canonical OT pseudepigraphical witness.
- **Ephrem the Syrian** — 11.16% (157 entries) — Syriac patristic
  voice; the East-Syrian-Alexandrian bridge.
- **Athanasius of Alexandria** — 10.66% (150 entries) — Tewahedo
  apostolic-bridge: 20th Patriarch of See of Mark + Frumentius's
  consecrator.
- **Mäqabyan / Mäṣḥafä Mäqabyan (Ethiopian tradition)** — 2.84% (40
  entries; γ.4.8 seed; opens-the-sixth-voice) — uniquely-Tewahedo-
  canonical broader-canon Maccabees-named-but-distinct text (Maqabis-
  of-Benjamin + Maqabis-of-Moab + angelological/resurrection-doctrine
  cycles).

**Tewahedo-distinctive-canonical block:** the three uniquely-Tewahedo
canonical texts (Mäṣḥafä Hēnok + Mäṣḥafä Kufāle + Mäqabyan) jointly
hold 432/1407 = 30.71% of the patristic-and-canonical corpus — the
FIRST TIME the three together constitute a numerically significant
block. **Patristic-anchor majority** (Cyril + Ephrem + Athanasius)
holds at 975/1407 = 69.30%. **Cyril plurality** remains intact at
3.34× next-single-father (668 vs 200), guarded durably by the
`test_cyril_remains_plurality_leader_at_arc_close` pin (which asserts
Cyril > Athanasius AND Cyril > Jubilees — sufficient under all
plausible future expansion).

**Update — ω.43 / γ.4.8.E arc-close 2026-05-14:** the γ.4.8 Mäqabyan
arc is now CLOSED at the EIGHTH §8.1 instance, with the five-wave
detail-wave family (γ.4.8 seed + γ.4.8.B Mäqabyan-I detail + γ.4.8.C
Mäqabyan-II detail + γ.4.8.D Mäqabyan-III detail + γ.4.8.E arc-close)
all shipped. **Mäqabyan reached 200 entries — PARITY WITH JUBILEES at
200; TIE for 2ND-PLACE in the voice-ranking** (Cyril 668 / Jubilees 200
/ Meqabyan 200 / 1 Enoch 192 / Ephrem 157 / Athanasius 150). The
estimated end-state of ~120-160 entries was EXCEEDED by ~40-80 entries
— the broader scope (per memory `feedback_extensive_answers`) achieved
PARITY rather than mere benchmark-match. All three Mäqabyan books at
100% chapter coverage: mq1 36/36 + mq2 21/21 + mq3 10/10 = 67/67
chapters. The Mäqabyan trilogy is the FIRST γ.4 arc to achieve 100%
chapter-coverage across its entire scope. **Tewahedo-distinctive-
canonical block (Mäṣḥafä Hēnok + Mäṣḥafä Kufāle + Mäqabyan) at
37.78%** (592/1567) — strongest position in γ.4 corpus history;
directly supports v1.1 publisher-led uniqueness-angle pick per memory
`project_v1_terminus`. Cyril remains plurality-leader at 42.63% (sub-
50% trajectory continues; 3.34× next-single-father preserved). With
γ.4.8.E ALL SIX γ.4 PATRISTIC/CANONICAL VOICES are at substantively-
closed-arc depth.

### Parallel-Bible end-state — two standalone Bibles (codified 2026-05-16)

**This is a first-class north-star goal, not a popup feature.** The
τ.6.x (`geez-tewahedo`) + τ.7.x (`amharic-tewahedo`) per-book
parallel-Bible ingests exist to produce **TWO STANDALONE Bibles** —
a Ge'ez Bible and an Amharic Bible, each a full version with its
own books and chapters — each carrying, in **its own** verse
popups, a **faithful English translation of its actual Ge'ez /
Amharic wording** (a fresh rendering of what the text says — NOT
the KJV, NOT the English editorial baseline).

The per-book rendering already shipped is the FOUNDATION for this,
not popup-language data. Earlier in-repo framing (and a prior
session) treated `geez`/`amharic` as mere verse-popup language
slots — that is **superseded**. Verse-popup policy:

- **The other 9 editions:** NO Ge'ez/Amharic popups. Do not wire
  them into any edition's `popup_languages_default` /
  `popup_translation`.
- **The existing English `ethiopian-tewahedo` edition:** only
  *conditionally* — permitted ONLY if every verse count matches
  across all books and all chapters (full per-verse parity). A
  maybe, not a commitment.
- **The two standalone Bibles:** YES — their own verse popups
  carry the faithful English back-translation. This is the point.

Source policy: Amharic = as-written-in-the-parallel-Bible-PDF
(cited to that source); Ge'ez gaps filled from the `GAPS` folder
(DEFERRED — note-only until the user re-engages after rendering).
Sequence: finish rendering (the only active phase; keep shipping
per-book τ.7.x.* / τ.6.x.* under D1-a + D4-c) → constitute the two
standalone editions → finalize sources → English back-translation
→ wire into their own popups. Phases 2–5 are post-rendering; do
NOT pull them forward. Full spec:
`dev/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md`.

### Self-upgrading matrix rule (codified at audit U-belt 2026-05-20)

**When a step unlocks the next step, the next step is responsible for
upgrading its own plan/tools BEFORE executing.** The matrix is
self-evolving — it doesn't wait for the next session to add the lesson.

Concrete triggers + responses (the canonical examples; the rule
generalizes to ANY future unlock):

- **Found a new failure class** during C-3/C-6 review? → at C-9 close,
  the closing reviewer APPENDS the class to the relevant section of
  `content/manuscript/_reviewer_context/{GG,CAM}_topology.md` AND
  (if pattern-detectable) adds the detector to
  `scripts/core/manuscript_self_check.py`'s screen list — so the
  NEXT chapter inherits the lesson without re-discovery (METHOD
  NOTE 3 last bullet).
- **Found a new chapter complexity class** beyond NARRATIVE/LIST/
  REGNAL_FRAME (e.g., POETRY, APOCALYPSE, EPISTLE)? → extend
  `scripts/core/manuscript_chapter_class.py` BEFORE running the
  first chapter of the new class; add the class to
  `_LIST_CHAPTERS` / equivalent or create a new class block;
  pin via test.
- **Found a new provenance tier** (a new source quality you want to
  ship)? → register it in `scripts/core/provenance_tiers.TIERS`
  BEFORE shipping a book that uses it; the
  `provenance_tier_known` lint check will fail otherwise.
- **Found a new outside-repo dependency**? → either move it INSIDE
  the repo (and add to `.gitignore` if large) OR document its
  external location in `dev/CLAUDE_PROJECT_RULES.md`. As of
  2026-05-20 audit, GAPS/ is the canonical example: moved INSIDE
  (1 GB; gitignored) for backup self-containment.
- **Found a new track** for production rendering (a new source of
  Bible-text material)? → extend `scripts/render_coverage.py`
  with the track's coverage class; extend
  `scripts/core/canonical_verse_counts.CANONICAL_BOOKS` if the
  track produces books with KJV skeletons; ship a design spec
  under `docs/superpowers/specs/`.
- **Found a stale METHOD NOTE or rule**? → fix it IN THE PLAN at
  the same commit, with the reason in the CHANGELOG (don't leave
  the contradiction for the next session — the bootstrap triad
  is read fresh every session and contradictions cost orientation
  time).
- **Found that a test/lint check would have caught the defect
  earlier**? → add the test/lint check at the same commit; the
  "defect found ≠ defect prevented" pattern is the systematic-
  debugging "fix the root cause" rule applied at the meta level.

**The rule's general form:** every step that unlocks the next step
ALSO upgrades the matrix so the next step starts BETTER than this
one did. Documentation, helpers, lint pins, tier registry, plan
METHOD NOTES — all are extensible at C-9 (or at the equivalent
ship-close moment in non-marathon tracks). The next session's first
action should be reading the upgraded matrix, not re-discovering
yesterday's lesson.

## 2. Universal principles (from SCOPE_2026-05-08.md, carried verbatim from 05-07)

1. **Fully customizable.** Every UI element, symbol, marker, kind
   name, category, color, label — assume the user will want to
   change it. Defaults exist; nothing is hard-coded.

2. **Easy.** No YAML hand-editing required. No CLI knowledge
   required. No build-pipeline knowledge required. The dev tools
   should let a schoolteacher or parish priest produce their own
   edition.

3. **Verifiable by book/chapter order.** Every browsing /
   management UI defaults to organizing content in canonical
   reading order — Genesis → Exodus → … → Revelation, with
   chapters within a book numbered ascending. This is a *hard*
   requirement, not a stylistic preference. See §6.

4. **No shortcuts — completeness over speed (user-directed 2026-05-27; elevated to a top-level principle).** There is time; the deadline never licenses a shortcut. Always pick the most complete + correct path even when it is far more work, and **any task may be PAUSED to do it right**. If a **better, more-complete** approach surfaces mid-task, **STOP and re-plan it** (thought-out, optimized, reorganized) rather than patch forward on the inferior path. Momentum / bias-to-action never overrides correctness or completeness. *Canonical instance:* the 2026-05-27 Ge'ez-versification redesign — a 1ki6 KJV-binning patch was abandoned for a full base-witness own-versification re-architecture once the deeper, more-correct approach surfaced (`docs/superpowers/specs/2026-05-27-geez-own-versification-design.md`). Reinforces [[feedback_proper_clean_correct]] + [[feedback_extensive_answers]] + [[feedback_dont_self_narrow_scope]].

5. **Never single-thread — always run ≥2 lanes (user-directed 2026-05-27).** The project should never be doing only one thing. Keep a background lane busy alongside the foreground, and **when one side task completes, auto-pick the next** from the backlog below — never drop to one lane. Respect the workload-tiered concurrency cap ([[feedback_concurrent_agent_cap]]: heavy >100k tokens MAX 1 · medium 30–100k MAX 2 · light <30k MAX 4) and keep image bytes OUT of the controller context (pre-pulls QC by dimensions only, never read tiles in). **Side-task backlog — pick the next when a lane frees; keep this current:** CAM hi-res pre-pull of upcoming chapters · base-structured re-collation of pending chapters · geez→kjv cross-ref anchoring · the deferred Phase-E Clementine chapters (1es 5/8, 2es 14) · the code-debt audit tail (`dev/AUDIT_2026-05-26-FINDINGS.md`) · doc-coherence (MATRIX_MAP / REPO_MAP / CHANGELOG currency) · test-coverage growth · Phase-D own-versification source acquisition.

## 3. Sequencing rules

When the user delegates ordering ("do it all", "you decide",
"push", "whatever order"), Claude picks the sequence using these
priorities, in order:

1. **Safest / most-foundational first.** Additive changes over
   destructive. Defaults that preserve existing behavior. Schema
   migrations that produce byte-identical builds when the new
   field is unset.

2. **Buyer-demo value.** Phases that unlock or polish the demo
   come before phases that don't. Corpus depth (χ) is high-value.

3. **Pair related phases.** If two phases are obviously tied
   (schema + backend + UI for one feature), bundle them into one
   batch even if they ship as separate commits.

4. **Logical seams over arbitrary cutoffs.** Stop at a place
   where another Claude (or future-self) could pick up cleanly,
   not mid-function.

5. **The 7-minute budget.** Pause before crossing it. Better to
   stop, summarize where things stand, and resume next turn
   than push through and lose progress.

6. **Bandwidth-aware**. Re-reading existing infrastructure is
   cheaper than rebuilding it. Always inventory before scoping
   new work; always check whether a CLI tool already does the
   thing the user is asking for. The 47-script CLI surface is
   the source of truth — web consoles WRAP it, never replicate.

When a task could be sequenced multiple reasonable ways, **pick
the most logical one for the project as a whole**, even if the
user's casual phrasing suggests a different order. The user has
delegated this judgment; exercise it.

## 4. Save semantics

- **"Save" = a local git commit** (run `save.ps1` through **PowerShell ONLY** — never the
  Bash tool: the spaced repo path + `>`/arrow glyphs in a commit message break cmd and sweep
  stray files via `git add -A`). The pre-commit hook runs `ruff format --check .` +
  `lint_rules.py` — both must pass or the commit is BLOCKED (the hook does NOT run the test
  suite; run the relevant tests yourself). The GitHub remote was deleted 2026-05-12, so a save
  is a LOCAL commit only (`git push` fails until a remote is reconfigured).
- **⚠ BEFORE every save:** `python -m ruff format` every file you generated/regenerated —
  ESPECIALLY `content/translations/<id>/` stores (recurs on EVERY ingest) — or the hook blocks
  the commit. (Full rule: §7 "Formatting + committing".)
- **Every save updates dev/SESSION_STATE.md** (last shipped phase · next · test count ·
  in-flight notes) — non-negotiable for continuity (§11) — and **VERIFY the commit actually
  landed** with `git log`/`git status` before claiming "saved" (§12/§14 truth-gate). Never
  report a save that didn't happen.
- **"Backup" is a SEPARATE command from "save":** a commit is not a backup. Back up via
  `git bundle create <file> --all` (file BEFORE `--all`) to the external **E:/F:** drives
  (NEVER C: — system drive is low). **Backup CADENCE (user-directed 2026-05-26): proactively
  back up every 3rd commit** (track the count; bundle on commits 3, 6, 9, …), AND at every
  `/clear` checkpoint, AND whenever the user says "backup". This supersedes the prior
  "backup only on explicit command" rule.
- "Continue", "proceed", "go ahead", "push" are **NOT** save commands (here "push" = "advance
  to the next phase," not `git push`). Don't auto-commit at the end of a phase.

> **DORMANT — Claude-Desktop-era zip flow (do NOT use unless the user explicitly says "zip"):**
> before the Claude-Code transfer, "save" meant presenting a downloadable zip via the
> `present_files` tool with a slim-or-full ask. That flow is dormant — never build a zip or ask
> slim/full on a bare "save". If the user *explicitly* asks for a zip: **slim** excludes
> regenerable artifacts (`content/translations/sources/`, `epub_working/.backups/`,
> `__pycache__/`, `.pytest_cache/`, `*.bak`, `*.tmp`, `.git/`); **full** is the whole working tree.

### Checkpoint saves (added after a real instance)

A save can be issued *mid-task* when the user explicitly asks for
one. This is a **checkpoint save** and is a valid pattern, not an
error. At checkpoint time:

- IN_FLIGHT.md should be `<!-- TRACKER-STATE: active -->` with the
  current task's progress documented (what's done, what's pending).
  This is honest and matches the Tier-2 contract.
- SESSION_STATE.md should reflect that the save happened *during*
  the in-flight task. The next save tag captures the same task,
  fully shipped or further checkpointed.
- The linter's `inflight_freshness` check will show
  `active for X.Xh (fresh)` rather than `idle` — that's
  correct for a checkpoint; not a bug.

Why this matters: a checkpoint save preserves user-visible work
without forcing premature completion. The user might want a
zip "right now" even though the feature isn't done — to share,
to test offline, to back up before the next risky change. The
guardrail system (Tiers 1-4) accommodates this honestly rather
than pretending the task is finished.

First instance: v28a-64-full was issued mid-ψ.3 (corpus widget).
Second: v28a-65-full was issued mid-ν.5 customize wiring. Both
captured the partial state with IN_FLIGHT correctly active.

## 5. Phase / commit tracking

- The Greek-letter phase system: α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π
  ρ σ τ. Sub-phases use dotted suffixes: `ν.2.5-A`, `ν.2.5-B`,
  `ν.2.7-A`. Letter assignments are sticky — a feature lives
  with one letter forever.
- `dev/PLAN_<date>.md` is the master sequence doc. Every new
  phase gets inserted in the right position there.
- `dev/SCOPE_<date>-addendum-<topic>.md` for major feature
  specs that need more than a paragraph.
- Each shipped phase corresponds to a `v28a-NN` build tag.

## 6. UI conventions

### 6.1 Book/Chapter order is canonical

Any UI that lists books — pickers, matrices, summaries,
audits, diff views — uses the order from `content/books.yaml`.
That order is Genesis → Exodus → … → Revelation, then
Apocrypha / deutero in their canonical positions, then any
Ethiopian-only books at the end. **Do not sort books
alphabetically.** Do not sort by note count. Do not sort by
"importance". Reading order is the only correct order.

Where chapters are listed inside a book, sort ascending by
chapter number. Where verses are listed inside a chapter, sort
ascending by verse number.

Where a UI must show a different order (e.g. an audit sorted
by problem severity), the canonical order must remain *one
click away* — provide a "sort by canonical" button or default.

### 6.2 Cross-linking

Every console header links to every other console. The current
console is `font-semibold`; the others are
`text-blue-600 hover:underline`. New consoles must add their
link to every existing console's header AND list every existing
console in their own header.

The cross-link invariant is enforced by `scripts/lint_rules.py`
(check id `6.2`) and surfaced in the `/preflight` dashboard as
the **Rules compliance** check. When the linter complains, fix
it before saving — drift here only gets harder to fix later.

**Pre-existing exception** — the consoles' "matrix" nav link
points to `/` rather than `/matrix`. This is project-old
technical debt: `/` actually serves the note editor (INDEX_HTML),
not MATRIX_HTML. The display text "matrix" was chosen when the
editor was understood as the home view. The linter accepts both
`/` and `/matrix` as valid cross-link targets for the matrix
cluster. When this gets cleaned up, do it cross-cuttingly across
all console nav blocks at once and update the linter's
`matrix_aliases` set.

### 6.3 Styling

- Tailwind via CDN (`https://cdn.tailwindcss.com`). No other CSS
  frameworks. Don't introduce a build step for CSS.
- Inline `<style>` blocks for truly per-page touches; Tailwind
  utility classes for everything else.
- No JavaScript build step. Plain ES6 in `<script>` tags.

### 6.4 Reactivity & forms

When a console renders form fields, both `<input>` and
`<select>` (and `<textarea>` if added later) must participate in
the dirty-check + save logic. The pattern is
`box.querySelectorAll('input, select')` — never just `'input'`.

### 6.5 Defaults for additive features

A new UI control that adds a feature should default to the
"don't change anything" position. Publishers opt *in*, not *out*.

## 7. Code conventions

### 7.1 Backend

- One BaseHTTPRequestHandler in `scripts/web.py`. `/foo` for
  HTML, `/api/foo` for JSON. New routes add an `if path == …`
  branch in `do_GET` / `do_POST` / `do_PUT`.
- YAML for config (editions, kinds, canons, themes, _meta).
  Python files with tuple data for bulk content (notes,
  translations).
- Loading data files: `ast.literal_eval` only — never `exec`.
  Translation modules and notes modules look like Python but
  must not be executable. A corrupted or hostile data file
  must not run code.
- **Caching depends on file mutability**:
  - **User-editable runtime data** (notes, translations — files
    that publishers / the customize console can edit while the
    web process is running): cache with `lru_cache` keyed on
    `(path, mtime_ns)` so on-disk edits auto-invalidate without a
    restart. Canonical pattern: `scripts.core.notes_io.load_notes`
    + `_load_notes_cached(path_str, mtime_ns)`. Also used by
    `scripts.core.translations`.
  - **Project-internal published data** (Strong's dictionaries,
    TSK, Nave's, commentary corpora like
    `ethiopian_commentaries.json`, configuration loaders in
    `scripts.core.config`): cache as singletons via
    `@lru_cache(maxsize=1)`. These files are not edited at
    runtime by publishers; updates ship via git commits + process
    restart. Tests that mutate these files in fixtures MUST call
    `<loader>.cache_clear()` in their setup or `tmp_path` setup.
  - If a loader currently uses `maxsize=1` and you need it to
    react to runtime edits, upgrade it to the mtime-keyed pattern
    (don't retain the singleton and try to invalidate manually).
- Writes go through `notes_io.atomic_write`. Bulk or
  destructive writes go through `notes_io.ensure_backup` first.

### 7.2 Schema migrations

- Adding a field is **always** a no-op when the field is unset.
  Builds with the field unset must be byte-identical to builds
  before the field existed.
- New required fields are forbidden. If a field "must" be set,
  pick a sensible default and document it.
- The `_patch_yaml_entry` and `_patch_yaml_list_field` helpers
  in `scripts/web.py` are how you write YAML edits — they
  preserve comments, ordering, and surrounding structure. Don't
  rewrite YAML files with `yaml.dump`; that loses comments.

### 7.3 Project structure

Books use lowercase 3-letter codes: `gen`, `exo`, `1ki`, `tob`,
`lje`, `2es`, etc. The 87-book Ethiopian Tewahedo set is the
superset; smaller canons are subsets defined in
`content/canons.yaml`.

### 7.4 One-shot ship scripts

`scripts/_ship_*.py` files are one-shot ledgers of the entries
appended to `content/sources/*.json` (or similar) at a specific
ship moment. They are NOT re-runnable in normal operation; running
them again would duplicate entries (though N-W4 idempotency now
protects against this for χ-cluster ships).

**Retention rule (codified at ω.41 hygiene bundle, 2026-05-13,
per AUDIT_2026-05-13-EOD EOD-W4):**

- Retain `_ship_*.py` files in `scripts/` for **one full release
  cycle** after the relevant arc closes.
- After that, move them to `dev/archive/ship_scripts/<arc-tag>/`
  preserving the original filename. The arc-close commit message
  documents the script's retired-not-deleted status.
- Distinguish from permanent at-scale driver scripts
  (`scripts/run_*_at_scale.py`) which ARE re-runnable detectors
  and remain in `scripts/` indefinitely.

Distinct from the obsolete safety scripts (e.g.
`scripts/_dedup_ethiopian_notes.py` post-N-W4): those carry an
explicit "LOAD-BEARING-NO-LONGER" docstring banner and remain
in `scripts/` as emergency-restore tools, separately tracked
in the SESSION_STATE inventory under "obsolete safety scripts".

## 8. Testing conventions

- pytest classes named `TestX` per feature. Live in
  `tests/test_scripts.py` (most things) or `tests/test_core.py`
  (core modules).
- Both unit (helpers, parsers) and integration (against real
  on-disk data) where each pulls weight.
- A new feature isn't done until it has tests that would catch
  the demo breaking.
- Tests should restore any global state they mutate (use
  `tmp_path` and `shutil.copy` to back up files before edits;
  restore in `finally`).
- **State-aware over default-assumed.** A test that depends on
  the world being in a specific state (e.g., "IN_FLIGHT marker is
  idle") should *parse the actual state* and verify the
  contract-against-that-state, not assume the default. Default-
  assumed tests pass when the feature ships and silently break
  later when the world is legitimately not in default state
  (e.g., during in-flight work). The pattern: read the relevant
  marker first, branch on its value, assert the appropriate
  invariant for each branch. Caught when ψ.3's mid-task work
  flipped IN_FLIGHT to `active` and broke a test that assumed
  it was always `idle`.

### 8.1 Arc-close pin convention

Codified after the third instance of this pattern shipped (γ.4.4.E
Mäṣḥafä Hēnok arc-close, γ.4.5.E Mäṣḥafä Kufāle arc-close — both
2026-05-12, plus the share-pin → count-milestone repair pattern
documented in memory `feedback_share_pin_pattern.md`). When a
multi-wave content arc closes (a parent phase like γ.4.4 or γ.4.5
whose detail-wave sub-phases A/B/C/D/E ship across multiple turns),
the closing wave's test class MUST add three specific kinds of pin:

1. **`_meta` synchronization pin.** Assert that the JSON `_meta`
   `source` and/or `scope` block names the arc's parent phase tag
   AND every shipped sub-phase tag. Pattern: regex word-boundary
   match (`re.escape(phase) + r"(?![.A-Z])"`) so γ.4.4 doesn't
   accidentally match γ.4.4.B. Pin per sub-phase, not all in one
   test — granular failures are easier to diagnose.

2. **Absolute-count milestone pin.** Assert
   `corpus_count >= N` where N is the cumulative count at the
   arc's close. Use a count milestone (`enoch_count >= 190`), NEVER
   a share threshold (`share >= 30%`) — share-pins break
   mechanically when later content waves dilute the share, even
   though the historical achievement is preserved. See memory
   `feedback_share_pin_pattern.md` for the failure-mode rationale.

3. **`all_N_sections_covered` exhaustiveness pin.** Assert every
   section the arc was supposed to cover has substantive coverage
   (≥ a stated minimum count or a substantive-content marker).
   Pattern: a single test named like
   `test_all_six_<arc>_sections_substantively_covered` that
   iterates the expected section list and asserts each one. This
   prevents a future "I'll ship the Astronomical Book later" from
   silently leaving the arc partially closed.

Existing instances:

- γ.4.4.E (Mäṣḥafä Hēnok arc) — `TestGamma44EEpistleOfEnochWave`
  in `tests/test_ethiopian_gamma4.py` at the closing of the
  six-section 1 Enoch arc; arc-close pin
  `test_all_six_mashafa_henok_sections_covered`.
- γ.4.5.E (Mäṣḥafä Kufāle arc) — `TestGamma45EJubileesJosephExodusFinaleWave`
  at the closing of the Jubilees four-major-section arc; arc-close
  pin `test_all_six_jubilees_sections_substantively_covered` plus
  the `test_jubilees_milestone_count_at_arc_close` count milestone.
- ω.37 (W10 closure) — `TestGamma4MetaPhasesCoverage` extends the
  `_meta` synchronization pin pattern across every previously-
  shipped sub-phase (γ.4.4.B/C/D/E + γ.4.5/B/C/D/E), so future
  drift gets caught at commit time.

When to use this convention: only at the **closing wave** of a
multi-wave content arc, not at every intermediate wave. The
closing wave is identified by the arc's substantive-coverage
parity goal being reached (every section covered at the planned
depth); the closing test class is where these three pins live.

Anti-pattern: putting a share-pin in the arc-close class. Memory
`feedback_share_pin_pattern.md` documents why every share-pin
breaks mechanically on the next voice-broadening wave; the
arc-close convention exists in part to replace the failure-prone
share-pin pattern with the durable count-milestone pattern.

## 9. Mental models for common tasks

### "Add a new edition feature"

1. Schema: add field(s) to `editions.yaml`, default to back-compat.
2. Loader: surface the field in `api_customize_data` (and
   `api_publisher_data` if it's a publishing field).
3. Validator: extend `api_save_edition_meta` to accept and
   validate the field.
4. UI: add the form control in the right console, in
   Book/Chapter order if it's a per-book matrix.
5. Build pipeline: read the field in `build_one`; default behavior
   when unset.
6. Tests: round-trip + invalid-input + back-compat + UI present.

### "Add a new translation"

**On-disk format.** A translation is `content/translations/<id>/`: a
`_meta.yaml` (license + provenance) plus one `<book_code>.py` per book, each
exposing `TRANSLATION = "<id>"`, `BOOK = "<code>"`, and
`VERSES = [(chapter, verse, text), …]`. Loaded via `ast.literal_eval` only —
never executed. **Coordinates are canonical (KJV/WEB) numbering**, because the
base HTML the popups attach to is KJV-numbered; store each verse under the KJV
coordinate so the popup lands on the right verse.

**Two extractors, by source format:**
- **eBible "verse per line" .txt** → `scripts/extract_translation.py <id>`
  (its `TRANSLATIONS` registry documents each PD source). English / Latin /
  Arabic / JPS / Douay / Brenton-English, etc.
- **OSIS XML (morphhb, …)** → a dedicated per-source
  `scripts/extract_<id>.py` (e.g. `scripts/extract_wlc_morphhb.py`). The shared
  `scripts/core/versification.py` remaps the source's own verse numbering onto
  canonical KJV — `wlc_to_kjv_map` reads morphhb's `VerseMap.xml`; add a
  per-source map for each new original-language source. Validate every emitted
  coord with `canonical_verse_counts.coord_in_canonical_extent` (0 out-of-extent).

**Original-language house markup (the `<em>`-per-word format).** Hebrew/Greek
verse text is **trusted pre-formatted HTML** (`popup_versions.is_trusted_html`
→ passed to the aside renderer RAW, never escaped). The exact format, byte-pinned
against the recovered base in `tests/test_wlc_ingest.py`: **each word wrapped in
`<em>…</em>`, joined by single spaces**; morpheme `/` separators stripped;
maqaf-joined words kept in ONE `<em>` (`אֶת־הָאוֹר`); sof-pasuq glued onto the
last word (`…ךְ׃`); paseq is its own standalone `<em>׀</em>`; pe/samekh paragraph
markers dropped; and **scribal special letters the source nests *inside* a `<w>`
(large/suspended — the Shema, Lev 11:42, Judg 18:30, Num 27:5) must be fully
captured — read the whole element, not just `.text`, or you silently drop
letters.** Plain-text translations (English, etc.) are NOT trusted_html — they
are HTML-escaped at render.

**Formatting + committing (non-obvious — the pre-commit hook enforces it).** Both
extractors emit **one line per verse** (grep-able). Before saving a new/re-run
translation, run `python -m ruff format content/translations/<id>/`: ruff
(line-length 120) wraps any verse tuple over the limit onto multiple lines — most
em-per-word Hebrew/Greek verses wrap, matching how `kjv/*.py` is already stored.
**Skip this and the pre-commit hook `ruff format --check .` blocks the commit.**
ruff only reflows whitespace, never the string values, so the data + the baked
popups are unchanged (re-verify with one `get_verse` call if paranoid).

**Wiring it on:** flip the version's data on in
`scripts/core/popup_versions.py` (an original-language slot already in the base
lives in `_BAKED_NOW`; otherwise a version bakes once `get_verse` returns text)
→ regenerate (`python -m scripts.generate_verse_popups`) → verify the coverage
jump + spot-check sample verses + the named versification-divergence loci +
`ebible verify errors=0` + flagship `epubcheck 0/0/0/0`. The `/customize` console
discovers the translation automatically (no UI work unless it needs special
metadata). Existing instance: WLC seed → full 39-book / 23,142-verse ingest
(τ.5-A.x / Phase 2, 2026-05-23; `dev/CHANGELOG.md`).

### "Add a new popup language"

1. Find PD source data; place under
   `content/translations/sources/<lang_id>/` or similar.
2. Add a CSS class (`vnote-<lang>`) to the source HTML
   generation pipeline.
3. Register the language in
   `scripts.build_edition.POPUP_LANGUAGES`.
4. Update the populated test data on each shipping edition's
   `popup_languages_default` if the new language should be
   default-on.
5. The `/customize` per-book matrix picks it up automatically
   from `POPUP_LANGUAGES`.

### "Add a new per-book asset (covers, etc.)"

This is the same pattern used for `popup_languages_per_book` —
the project's custom YAML parser doesn't do nested mappings, so
per-book maps live as flat lists of `"<book_code>=<value>"`
strings on disk and decode to dicts in the API/UI layer.

1. Schema: add `<asset>_per_book` (list of strings) to
   `editions.yaml`. Default = absent / empty.
2. Encoder + decoder (mirror `encode_per_book_languages` /
   `decode_per_book_languages` in `scripts/build_edition.py`).
   Encoder MUST sort by canonical book order (Rule §6.1).
3. Filter by canon when surfacing in the API. If a book is not
   in the edition's canon, do NOT show a slot for it. (Tanakh
   shows 39, Reformed 66, Ethiopian 87.)
4. UI lists books in canonical order — read from `books_canonical`
   in `api_customize_data` (or a similar canonical-list field).
   Never sort books client-side.
5. If the asset is a file (cover image, etc.), the upload backend
   validates size, dimensions, MIME type, and aspect ratio
   BEFORE writing to disk; failed uploads must not mutate state.
   Use `notes_io.atomic_write` + `notes_io.ensure_backup`.

### "Add an uploadable binary asset (image, PDF, audio, etc.)"

Codified after the cover-upload pipeline shipped (π.4-B).
Reusable for any future binary upload surface.

1. **Validate first, write never until clean.** Define a
   `validate_upload_<thing>(bytes) → (ok, error, meta)` in
   `scripts/core/<asset>.py`. Order checks cheap-to-expensive:
   size cap → format magic-bytes → structural validity →
   semantic checks (dimensions, duration, aspect, etc.).
2. **Detect format from magic bytes, never the filename.**
   The filename is user-controllable; the bytes aren't.
3. **One canonical storage-path helper per asset** in the same
   module (see `storage_path_for_main` / `storage_path_for_book`).
   Future migrations consume this helper, never duplicate paths.
4. **Multipart parsing**: use `_parse_multipart` and
   `_extract_boundary` in `scripts/web.py`. Don't reach for
   `cgi.FieldStorage` (deprecated in 3.13) or pull in Werkzeug
   etc. The focused parser is one place to fix bugs.
5. **HTTP layer**: route POST to a dedicated `_handle_<asset>_upload`
   method on the request handler. Cap `Content-Length` at 2× the
   per-file limit so a hostile client can't tie up the server.
6. **Transactional write**: validate → `ensure_backup` existing
   file → `atomic_write_bytes` new file → save the YAML field
   pointing at the new path → on YAML-save failure, **roll back
   the file write** (unlink). Disk and YAML must never disagree.
7. **The `api_save_edition_meta` path validator** rejects
   absolute paths, `..`, hidden segments, and disallowed
   extensions; reuse it rather than invent per-asset rules.
8. **DELETE flow**: clear YAML first, then back up + unlink the
   file. If YAML clear fails, the file stays — partial state is
   detectable and recoverable, total state loss is not.
9. **Tests cover**: happy path round trip, every rejection path
   in the validator, "no file part" and "missing boundary" HTTP
   edge cases, "no disk write on validation failure", and DELETE
   leaves both YAML and disk clean.

### "Add a new static-file route (serve a directory back to the browser)"

Codified after π.4-B UI shipped — the `/content/covers/<...>`
route that serves uploaded covers back as `<img src=...>`.
Reusable for any future asset-serving route (built EPUBs, PDFs,
audio samples, etc.).

1. **Sandbox to a known-safe root.** Resolve the user-supplied
   path inside the safe directory; reject anything that escapes.
   The pattern:
   ```python
   file_path = (REPO / "content" / rel).resolve()
   safe_root = (REPO / "content" / "covers").resolve()
   try:
       file_path.relative_to(safe_root)
   except ValueError:
       return self._send_json({"error": "forbidden"}, status=403)
   ```
2. **Defensive rejection BEFORE the resolve check** — also block
   `..`, absolute paths, and hidden segments at the string level.
   Cheap, catches typos, and protects against `.resolve()` weirdness
   on platforms with symlink trickery.
3. **Use `_send_file`** in `scripts/web.py` — handles content-type
   from extension, sets a short `Cache-Control: public, max-age=60`
   so navigations between consoles don't re-fetch every image.
4. **Do NOT** add a write/upload path to a static-file route. Reads
   and writes live on different routes; the static-file route is
   read-only. Uploads always go through validated POST endpoints.
5. **Tests cover**: 200 on valid path, 404 on missing file, 403/404
   on `../` traversal, 403/404 on hidden-dir access. The route is
   security-critical; tests are non-optional.

### "Add a meta-tool that integrates with the preflight dashboard"

Codified after the rules linter shipped (ω.0.1). Reusable for any
future check / scanner / validator that should be both a CLI and a
visible signal in the readiness dashboard.

1. **CLI module first.** Put the tool in `scripts/<name>.py` with a
   pure `run_all() -> dict` API and a `main()` entrypoint. Standard
   shape for the dict:
   ```
   {
     "checks": [
       {"id": str, "name": str, "status": "pass"|"warn"|"fail",
        "message": str, "violations": list},
       ...
     ],
     "summary": {"total": int, "pass": int, "warn": int, "fail": int,
                 "clean": bool},
   }
   ```
2. **CLI exit codes.** `main()` returns 0 on clean, 1 on any failure.
   Suitable for pre-commit hooks and CI without further glue.
3. **Preflight composition.** In `_compute_preflight_uncached()` in
   `scripts/web.py`, append a check that imports `run_all` and folds
   the meta-tool's verdict into the dashboard:
   - status: `fail` if any sub-check fails, `warn` if any warn,
     `pass` otherwise
   - details: list of failing/warning sub-checks (don't dump the
     passing ones — readers want what's wrong)
   - jump_to: usually `/preflight` for code-level issues, or the
     specific console where the issue gets fixed
4. **Wrap the import in try/except** — if the meta-tool blows up,
   the dashboard should still render (with a `warn` for the missing
   check), not 500.
5. **Tests cover**: the CLI module imports cleanly; `run_all()` runs
   without raising on the current codebase; the preflight aggregator
   surfaces the check under its expected id.

### "Add a new aggregate API: compose, don't recompute"

Codified after the second instance of this pattern (ψ.3 corpus
progress widget composing api_attribution_audit; the first was
the preflight aggregator composing run_all + 7 other sub-checks).

When adding a new endpoint that summarizes data already produced
by another endpoint, **compose** the existing one rather than
re-walking the data:

1. Find the cheapest existing endpoint that already produces the
   raw counts you need. For corpus-totals, that's
   `api_attribution_audit()` (cached behind `_files_signature`).
2. Call it from the new endpoint. The cache makes repeated calls
   free.
3. Compute only the *derived* fields locally (deficits, percents,
   ranges).
4. Document in the docstring: "composes X; no new file scanning."

Why this matters: the project does many file-walks (87 books × N
note-files per edition). A second walk for "the same numbers"
doubles the cost on every page render and hides cache invalidation
bugs. One source of truth per kind of data.

Anti-pattern: writing a new `_count_all_notes()` helper when
`api_attribution_audit().counts.total` already exists.

### "Add a new feature endpoint: pure function + thin route adapter"

Codified after the sixth instance of this pattern (ν.5 customize
preview, ψ.5 sample-chapter export, ω.0.2 console scaffold,
ω.1 backup restore, ψ.6 ops dashboard, ω.2 build-all). Every
new feature endpoint we've added in the last two weeks has the
same shape and the pattern reliably produces tests that don't
need an HTTP server.

The shape:

```python
# Pure function — testable without HTTP
def api_x(arg1, arg2, *, kwarg=default) -> dict:
    """Returns {"status": "ok"|"error", "code": str?, "http": int?, ...}.
    No global state. No HTTP. No subprocess if avoidable."""
    if not arg1:
        return {"status": "error", "code": "invalid_input",
                "http": 400, "message": "..."}
    # ... real work ...
    return {"status": "ok", "data": ...}


# Thin route adapter — translates dict to HTTP
if path == "/api/x":
    result = api_x(arg1, arg2)
    if result.get("status") == "ok":
        return self._send_json(result)
    http_code = result.get("http") or 500
    return self._send_json({
        "error": result.get("code") or "internal_error",
        "message": result.get("message") or "",
    }, status=http_code)
```

Three rules:

1. **The pure function returns a dict, never raises for expected
   errors.** Validation failures, not-found, etc. all become
   `{"status": "error", "code": "...", "http": 4xx, "message": ...}`.
   Reserve raising for genuinely unexpected conditions.

2. **The route adapter does ONLY translation.** No business
   logic. No conditional fallbacks. If you find yourself writing
   `if/else` in the route block, push it back into the pure
   function.

3. **All inputs are explicit kwargs.** No `request.GET` reading
   inside the pure function. Parse the request in the route, pass
   plain Python values to the pure function. Tests construct the
   pure function call directly.

#### The injectable-callable variant (for orchestration)

When the pure function orchestrates a slow or environment-dependent
operation (subprocess, network, large compute), make the operation
itself an injectable callable parameter:

```python
def api_build_all_editions(*, version: str = "v28a",
                            build_one=None) -> dict:
    if build_one is None:
        build_one = api_export_build  # production default
    for ed_id in edition_ids:
        result = build_one(ed_id, version=version)
        # ... aggregate ...
```

Tests pass a fast mock instead of running real builds:

```python
def mock_build(edition_id, version="v28a"):
    return {"ok": True, "filename": f"mock_{edition_id}.epub"}

result = api_build_all_editions(build_one=mock_build)
```

Existing instances using this variant: `apply_plan(plan,
target_file=...)` from ω.0.2; `api_build_all_editions(*, build_one)`
from ω.2. Pattern instances of this exact shape: 2 of 6 (the
others use the basic shape because their work is light enough that
real calls are fine in tests).

Why this matters:

- **Tests stay fast.** ω.2's orchestration is exercised in 4
  tests, none of which run a real subprocess EPUB build.
- **The shape is uniform.** Future Claude (or future dev) can
  read the route block and immediately know where the logic
  lives. No surprise behaviour stuffed into the HTTP layer.
- **Errors degrade gracefully.** The dict-not-raise contract
  means a buggy validator can't take down the server with an
  uncaught exception — the error becomes a 500-with-message
  instead of a stack trace in the wfile.

Anti-pattern: writing logic inside the route handler that calls
`self._send_json(...)` mid-function. If you do this, the function
is no longer testable without an HTTP server and the test suite
will pull in `http.server` machinery for what should have been a
plain function call.

### "Add a new corpus-growth phase (the χ cluster pattern)"

Codified after χ.6 shipped twice (CrossRefDetector + HebrewWord-
Detector). Each new corpus-growth phase (χ.7 Nave's Topical, χ.1
Strong's Greek, χ.2-5 commentaries) follows this exact shape and
ships in roughly one focused turn. Don't re-derive — follow the
template.

**The pipeline shape:**

```
PD source data        →  Detector class               →  Candidates JSON         →  Promoted notes
(content/sources/        (scripts/core/detectors.py)     (content/candidates/        (content/notes/<book>.py)
 or content/                                              <book>_ch_<NNN>.json
 translations/)                                           — prospect.py format)
```

**Steps:**

1. **Acquire / verify the source data.** (First see the top-of-file
   "sources are NOT missing" guard for the full look-first inventory +
   the "never conclude blocked / don't ask the user to supply" rule.)
   Check `content/sources/` first — TSK and Strong's Hebrew already
   cache there. New corpora go in the same directory or under
   `content/<source>/`. Add to `scripts/core/sources.py` if a loader is needed.
   Update `content/sources/ATTRIBUTIONS.md` with the PD/CC notice.

2. **Add the kind code** to `content/kinds.yaml` if the new
   detector produces a category-prefixed kind not already there
   (e.g. `topic-nave`, `lang-greek`). Existing detectors reuse
   existing kind codes (`xref-citation`, `lang-hebrew`).

3. **Write the detector class** in `scripts/core/detectors.py`,
   mirroring `CrossRefDetector` (no verse text needed) or
   `HebrewWordDetector` (verse text required). Both extend the
   base `Candidate` dataclass return shape. Add to
   `ALL_DETECTORS` if it should run via `prospect.py`.

4. **Write the driver script** at `scripts/run_<kind>_at_scale.py`,
   modeled on `scripts/run_xref_at_scale.py` (no verse text
   needed) or `scripts/run_hebrew_at_scale.py` (reads verse text
   from `content/translations/kjv/<book>.py`). Both bypass
   `prospect.py`'s EPUB-build dependency by iterating cached
   source data directly. The driver writes candidates JSON in
   prospect's exact format so `promote.py` works unchanged.

5. **Run the driver.** First on a small book as smoke test
   (`--books jud` or similar). Inspect a sample candidate JSON.
   Then full corpus: `python3 scripts/run_<kind>_at_scale.py`.
   For threshold-based detectors (TSK has `--min-votes`), start
   conservative; lower if needed for more candidates.

6. **Batch promote** with `python3 scripts/batch_promote_xrefs.py
   --kind <kind>`. The `--kind` filter prevents accidentally
   promoting candidates of mixed kinds. The batch promoter is
   in-process (avoids per-file subprocess overhead) and
   idempotent (dedup against existing notes).

7. **Verify (source-level)**: `pytest` passes (the `>= 1381` corpus
   floors absorb growth), `lint_rules.py` passes, attribution audit
   shows the new notes attributed.

8. **⚠ BAKE-AND-PROVE GATE — a corpus change is NOT done until it is in a
   build.** Promoting only writes the SOURCE (`content/notes/`);
   `build_edition.py` zips the PRE-BAKED `epub_working/` base, so a build
   will NOT contain the new notes until you bake them in. Run, in order:
   `inject --all-books` (additive — `--dry-run` first to confirm it only ADDS,
   never deletes) → **`python scripts/check_nested_anchors.py` (run `--fix` if it
   reports any) + `pytest tests/test_nested_anchors.py`** → `ebible verify`
   (marker↔aside pairing) → rebuild a flagship edition → `epubcheck 0/0/0/0`.
   **If the rebuilt EPUB is the same size as before the change, you forgot to
   inject** — the notes are in no edition yet. Commit the changed `epub_working/`
   split files alongside the notes.
   - **⚠ The nested-`<a>` check is MANDATORY — epubcheck does NOT replace it.**
     `inject` can place a `note-ref` marker INSIDE a verse's `vn-link` anchor =
     nested `<a>` (invalid base XHTML). The build converts `vn-link <a>`→`<span>`,
     so the BUILT EPUB stays valid (epubcheck 0/0) even when the BASE carries
     thousands of nested `<a>` — only `test_nested_anchors` catches it. It was
     skipped after the Nave's/Easton's/Torrey ingests → **14,568** nested `<a>`
     accumulated undetected (found + `--fix`-repaired 2026-05-26). Corollary: a
     "full suite passed" claim from a CURATED SUBSET is NOT a green suite — name
     the tests you actually ran, and include the base-invariant (`test_nested_anchors`)
     + translation tests, not just `test_scripts`/`test_core`.

9. **CHANGELOG entry** with cumulative corpus math:
   `Was: N notes → Now: M notes (+delta · X% of 35K target)`.

**Why this works:**

- **Pure-function-API + thin route adapter** at the detector
  level (per the §9 pattern just above).
- **Compose, don't recompute**: the driver composes existing
  detector classes; the batch promoter composes existing
  `promote.promote_candidate`. Zero re-implementation.
- **Idempotent**: re-running the driver produces a superset of
  the previous candidates; dedup in promote skips already-
  shipped notes. Safe to re-run with different thresholds.

**Anti-pattern**: rebuilding `prospect.py` to bypass the EPUB
dependency. The driver script *uses* the existing detector class
and writes the same JSON format `prospect.py` would write — it's
just a different iteration source. `prospect.py` itself stays
unchanged. (See ω.0.7 "compose, don't recompute".)

**Anti-pattern**: subprocess-looping `promote.py` per file. The
in-process `batch_promote_xrefs.py` is ~80 lines and runs in
seconds where the loop would take minutes.

**Existing instances:**
- χ.6 (CrossRefDetector + run_xref_at_scale.py): +6,127 notes
- χ.6+ HebrewWord (HebrewWordDetector + run_hebrew_at_scale.py):
  +8,412 notes
- Together: 1,381 → 15,925 in one session via this pattern.
- Torrey's New Topical Textbook (`TorreyTopicalDetector` + `run_torrey_at_scale.py`): +~21,800 notes (2026-05-26).

### "Register a new note kind"

Codified after Track C Torrey (2026-05-26) had to reverse-engineer these
constraints mid-session. To add a `kind` to `content/kinds.yaml`:

1. **Mirror a sibling** in the same `category` (copy its `symbol`,
   `note_class`/`marker_class` shape, `label`, `phase`). Kinds SHARE their
   category's symbol; `inject.glyph_for` reads the per-kind `symbol`.
2. **Register only in a commit where the kind gains ≥1 note.** The `/preflight`
   `empty_kinds` check warns on any registered kind with zero notes across all
   editions (`scripts/api/preflight.py`), so ship the kind + its first notes
   together.
3. **Bump the count pins:** `record_count` in `tests/test_validate_schemas.py`
   (= editions + kinds; +1 per new kind) and the `content/kinds.yaml — N kinds`
   docstring in `scripts/core/matrix.py`.
4. **Edition enablement is automatic by category** — a new kind is enabled
   wherever its `category` is enabled (no `editions.yaml` edit needed); confirm
   with a build.

### "Build a defensive system: use the four-tier shape"

Codified after the second instance of this pattern: §15
(backend drift detection) and ω.0.6 (frontend crash defense)
both arrived at the same four-tier structure independently.
The shape generalizes — when the next defensive system is
needed (input-validation hardening, content-security policy,
data-integrity auditing, whatever), follow this template
instead of inventing a new arrangement.

#### The four tiers

```
TIER 4  Behavioral / protocol         FIRST line of defense
        (rule that Claude or a         The cheapest layer:
         human follows by              just judgment + a
         convention)                   small protocol doc.

TIER 1  Per-action audit              SECOND line
        (cheap programmatic check      A short script or
         right before the action       checklist that runs at
         completes)                    each commit / response.

TIER 2  State of record               PERSISTS across turns
        (a small visible file that     Survives compaction.
         declares "what's open")       If T1 missed, T2 still
                                       shows the open loop.

TIER 3  Continuous automated check    FINAL backstop
        (linter / preflight check      Runs on every preflight.
         that surfaces drift to        The auditable
         humans)                       "did anything escape?"
```

Why this specific shape: each tier covers a failure mode that
the others can't catch as cheaply. T4 is free per-turn but
relies on memory; T1 is cheap automation but only fires once;
T2 is a state record but doesn't enforce; T3 is enforcement
but expensive to add. Together they form defense in depth.

#### When to reach for this template

You're building a new defensive system if any of these are true:

- Multiple distinct failure modes need different detection
  methods
- Failures can leak across turns / sessions / pages
- A single check would have to run at multiple times to be
  effective
- There's a gradient of cost: cheap-but-fallible vs
  expensive-but-thorough

If none of these are true, **don't tier**. Single-purpose tools
(like `scripts/cleanup.py`) are correctly structured as one-pass
operations. Tiering them would be over-engineering. The audit
question to ask: "is there a failure mode that escapes the
single layer?" If no, single-layer is correct.

#### How to map a new defense to the four tiers

For each failure mode the new system must catch:

1. **Identify the canonical drift signature** — what does the
   failure look like in the world?
2. **Pick a primary tier** — usually the cheapest tier that
   can detect that drift mode. (T4 if it's a discipline issue,
   T3 if it's a structural invariant.)
3. **Pick a backstop tier** — usually one tier later in the
   chain so the check still runs even if the primary slips.
4. **Document in the system's CHANGELOG entry** which tier
   owns which drift mode, like §15's coverage matrix:
   ```
                          drift class A   drift class B   ...
   TIER 1 audit            PRIMARY         backstop
   TIER 2 state record     no              PRIMARY
   TIER 3 linter           backstop        backstop
   TIER 4 protocol         no              no
   ```

The matrix forces explicit thinking about coverage gaps. Any
column without a PRIMARY is a hole; any row without a PRIMARY
is a tier that's not pulling its weight.

#### Two existing instances (for reference)

- **§15 — Backend drift detection.** Built ω.0.4. Catches the
  "code shipped but not journaled" failure class. Primary
  tiers: T4 §13/§14 protocols, T1 §12 footnote audit,
  T2 IN_FLIGHT.md, T3 lint_rules.py.
- **ω.0.6 — Frontend crash defense.** Built one turn after the
  meta-pattern crystallized. Catches null-pointer / unexpected-
  exception / API-failure / unguarded-DOM-query failure classes.
  Primary tiers: T4 (graceful degradation discipline),
  T1 (input validation), T2 (safeFetch wrapper), T3 (browser
  DOM helpers + Tier 4 backstop).

A third instance applying this template would confirm it as a
durable pattern; until then it's two examples and a recipe.

### "Surface a developer-only style knob as a per-edition option"

Codified after ν.6 (reader experience) shipped. The project has a
long tail of style knobs in `scripts/style_config.py` and adjacent
modules that were originally developer-only constants. As publishers
need finer control, each gets surfaced individually following this
pattern.

1. **Schema first.** Add the new field to `editions.yaml`-style
   records via `api_save_edition_meta`'s `EDITABLE_TEXT` /
   `EDITABLE_BOOL` sets. Default value MUST preserve current
   behavior — additive features should never alter existing builds
   unless the publisher opts in.
2. **Validate enumerations.** If the field accepts a fixed set of
   values, define the set as a module-level constant in
   `scripts/build_edition.py` (e.g. `CHAPTER_NUMBER_FORMATS`) and
   reject unknown values from `api_save_edition_meta` with a clear
   error message that lists the valid options.
3. **Apply in build pipeline.** Add a per-edition pass in the
   `build_edition()` flow, between filter passes and packaging. The
   default (no-op) path must skip the file scan entirely so editions
   that don't use the feature build byte-identically.
4. **Idempotency.** The build pass runs over generated HTML; design
   the rewrite so running it twice produces the same output (e.g.
   regex matches digits, decorated output contains words → no
   re-match on second run). This protects against pipeline reruns.
5. **UI: collapsible card on /customize.** Group related knobs in a
   `<details>` block with a clear summary line. Stamp a small italic
   note under the controls if any setting "applies on next BUILD"
   so the publisher's mental model matches the actual flow.
6. **Tests cover**: each enumerated value renders correctly in
   isolation; the build-pipeline pass is a no-op for default
   settings; happy-path round trip via `api_save_edition_meta`;
   rejection of unknown values.
7. **Existing infrastructure check** — before scoping a new style
   knob, search `scripts/style_config.py`, `scripts/apply_style.py`,
   and `scripts/set_reader_toc.py` for the toggle. Many of the most
   useful knobs already exist as developer-only constants and just
   need surfacing through the schema + UI; reinventing them is the
   anti-pattern this rule guards against.

### "Extract a topic cluster from a god-module into scripts/api/<topic>.py"

Codified after the ω.35-B file-split track shipped eight instances
(B.1 snapshots, B.2 scenarios, B.3a covers-mutations, B.3b sources-
cache, B.4 customize, B.5 editions, B.6 exports/build, B.7 preflight
/audit/help/multipart). Each slice reduced web.py by 70–1200 lines;
cumulative 40.5% reduction (7670 → 4564 lines) with **zero** behavior
change at any HTTP boundary.

The same shape will recur when other god-modules need decomposing
(`scripts/build_edition.py`, `scripts/prospect.py`, etc.). Follow
this template; don't re-derive.

**The shape:**

1. **Identify a cohesive topic cluster.** A good slice is 3–10
   handlers that share an HTTP prefix (`/api/snapshots/*`), a domain
   concept (covers, sources, editions), or an internal helper graph
   (preflight + its cache helpers). Mixing two unrelated topics in
   one slice is the anti-pattern — split them.

2. **Create `scripts/api/<topic>.py`** with:
   - A module docstring naming the phase tag (ω.35-B.N), the handlers
     moved, what stayed in web.py and why, and the lazy-import
     pattern if applicable.
   - `from __future__ import annotations` so future PEP-604 type
     hints work on Python ≥ 3.10.
   - Module-level imports for libraries that are guaranteed
     non-circular (`config`, `audit_log`, `notes_io`, `pathlib`).
   - **NEVER** top-import from `scripts.web` — that's the circular
     hazard the lazy pattern is designed to dodge.

3. **Move handler bodies verbatim.** Don't refactor in the same
   commit as the extraction. Preserve every existing comment,
   docstring, decorator, error message. The diff should read
   "moved" not "rewrote." Behavior-changing improvements come in a
   separate, smaller follow-up slice.

4. **Lazy-import web.py-only dependencies inside the function body.**
   `_files_signature`, `_save_cover_bytes`, `api_attribution_audit`,
   etc., all stay in web.py for now. Their callers inside the
   extracted module import them at call time, NOT at module load
   time. This sidesteps the circular import that would otherwise
   block the split.

5. **Replace the inline defs in `scripts/web.py`** with a thin
   re-import block:

   ```python
   # ============================================================
   # <Topic> API (Phase <tag> / ω.35-B.N)
   # ============================================================
   # Implementation moved to scripts/api/<topic>.py.
   # Re-imports below preserve scripts.web.api_X for route-table
   # lambdas + tests that reference the flat namespace.
   from scripts.api.<topic> import (  # noqa: E402
       api_X,
       api_Y,
       ...
   )
   ```

   Route tables (`_SIMPLE_GET_ROUTES`, `_PUT_ROUTES`, etc.) and the
   legacy if/elif dispatch in `do_GET` / `do_POST` continue to
   reference `api_X` by its flat name — the re-import preserves the
   binding identity.

6. **Add a `TestOmega35BN<Topic>Extraction` class** with this
   uniform shape:
   - `test_<topic>_module_exists` — `hasattr(scripts.api.<topic>,
     "api_X")` for every moved name.
   - `test_handlers_backward_compatible_via_web` — every name is
     importable from `scripts.web` and callable.
   - `test_handlers_actually_live_in_new_module` — `is`-identity
     check between `scripts.web.api_X` and the canonical home, and
     `__module__ == "scripts.api.<topic>"`. For audit-decorated
     handlers, unwrap via `getattr(fn, "__wrapped__", fn)` before
     reading `__module__`.
   - `test_audit_decorator_preserved` — for every mutation handler
     wearing `@audit_log.audit_endpoint`, pin the decorator is still
     in place.
   - `test_web_py_does_not_define_<topic>_handlers_inline` — source-
     scan `scripts/web.py` for `def api_X(` and assert absence.
   - `test_route_table_still_dispatches_<topic>` — if applicable,
     pin that `_SIMPLE_GET_ROUTES` / `_PUT_ROUTES` / etc. still
     points at the (re-imported) callables.

7. **Cross-module retarget.** If other `scripts/api/*.py` modules
   lazy-import the helpers you're moving from `scripts.web` (legacy
   home), retarget them to the new canonical home in the same ship.
   Add a test asserting the source contains the new import path,
   not the old one — this prevents drift back.

8. **Update `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`,
   `dev/CHANGELOG.md`** with:
   - Slice name (ω.35-B.N) and what moved
   - Net line-count delta in web.py
   - Cumulative delta across the track (so progress reads as a
     trajectory, not a series of one-offs)
   - Test count and linter status

**Why this works:**
- **Zero downtime / zero behavior change.** Route registration is
  unchanged; the dispatcher resolves the same callable through the
  re-import. Existing tests pass without modification (they import
  from `scripts.web`).
- **Tests stay co-located.** The extraction tests live in
  `tests/test_scripts.py` next to the topic's existing tests, so
  related coverage stays together.
- **Lazy import sidesteps circularity.** `web.py` → `api/<topic>.py`
  is one-way at module-load time; `api/<topic>.py` → `scripts.web`
  is deferred until call time, by which point web.py is fully
  loaded.

**Anti-patterns:**

- Rewriting a handler mid-extraction. Move first, refactor later —
  the diff should be 100% movement so a regression is bisectable.
- Top-importing `scripts.web` from `scripts/api/<topic>.py`. That
  creates the circular import the lazy pattern dodges.
- Mixing two topics in one slice. Split them; smaller slices ship
  with smaller blast radius and clearer diffs.
- Forgetting the `__wrapped__` unwrap in the `__module__` test for
  audit-decorated handlers. The decorator wraps the function, so
  the raw `fn.__module__` reads the decorator's module, not the
  handler's.

**Existing instances:** ω.35-B.1 through ω.35-B.7. After B.7 closed
the file split for web.py, the pattern is durable enough to apply
elsewhere; future invocations can label themselves with their own
phase letter (the pattern is generic, not ω-only).

### "Build an index-backed alternative for an expensive file-walk operation (the Δ-family pattern)"

Codified after the ω.34/Δ-family arc shipped Δ.0 through Δ.9
(2026-05-10 → 2026-05-11). The pattern recurred in two
distinct operations (`compute_matrix` via Δ.4 and
`dashboard_stats` via Δ.5) and the *infrastructure* slices
(Δ.0, Δ.6, Δ.7, Δ.8, Δ.9) were collectively load-bearing —
the wire-flip attempts kept reverting until all five unblockers
were in place. Capture the shape so the next index-backed
optimization doesn't re-derive each unblocker.

**The setup:**

The codebase has an expensive file-walk operation (a function
that opens every `content/notes/*.py`, parses each, aggregates
something across the corpus). It's correct, slow (~3s on 51K
notes), and called frequently. An SQLite-indexed alternative
would be ~10× faster but introduces multi-process / xdist
correctness hazards that are easy to get wrong.

**The shape:**

1. **Build the equivalent function under a new name.** Don't
   rename or replace the file-walk yet. Add
   `<name>_indexed()` alongside `<name>()` in the same module,
   plus an equivalence test that pins both produce
   byte-identical output for the same inputs.

2. **The equivalence test is non-negotiable.** Δ.4's
   equivalence test caught the index path's first attempts
   diverging on disabled-kind filtering, empty-edition
   handling, and chapter-key dtype (int vs str). Skipping it
   would have shipped buggy migrations to production.

3. **A rebuild lock under `content/.locks/`** — the index is
   shared across xdist workers in tests + threads in
   production. Concurrent writes corrupt it. Use a file-based
   lock (`<feature>_rebuild.lock`) with `_acquire_rebuild_lock(*,
   timeout: float = 30.0)`. Pin TimeoutError-on-exceed with a
   short timeout in tests (held-lock setup + 0.2s acquire ->
   raises).

4. **TTL fingerprint cache** — `_compute_fingerprint()` stats
   every `notes/*.py` (87 files). On hot paths this hammers
   the OS. Memoize keyed on a monotonic clock with a
   configurable refresh interval (default 1s in production,
   0s in tests for force-rebuild patterns). After this lands,
   `connection()`'s rebuild check is a single dict-lookup in
   steady state. Without this, EVERY wire-flip attempt
   intermittently fails xdist because workers race to rebuild.

5. **`notes_io` invalidation hook** — when a notes file is
   rewritten by an editing tool, the index must invalidate so
   the next reader rebuilds. Wire a callback in
   `notes_io.atomic_write` that calls the index's
   `invalidate()` method. Without this, edits during a test
   run produce stale index reads and false-failing
   equivalence assertions.

6. **Per-worker index storage** — each xdist worker gets its
   own SQLite file path. The naming convention is
   `corpus_index_<worker_id>.sqlite` (worker_id = `gw0`,
   `gw1`, ... for xdist; `_serial_` for non-xdist runs).
   Per-worker storage prevents the cross-worker write race
   that defeated wire-flip attempts #1-4.

7. **Server warmup + session-scoped test fixture** — both
   prod and test cold-start cases pay the first-rebuild cost.
   In production, warmup happens at server boot (one-time).
   In tests, a session-scoped `corpus_index_warmup` fixture
   in `tests/conftest.py` builds the index before any test
   runs. Without warmup, cold tests random-fail because the
   first rebuild + an in-flight test write race on the lock.

8. **Wire-flip in a separate phase.** Even with all
   unblockers in place, the wire-flip is its own slice. The
   public function (e.g. `compute_matrix()`) gets a one-line
   change to call `compute_matrix_indexed()` instead of
   `_compute_matrix_via_file_walk()`. The file-walk
   implementation stays under its private name as the
   equivalence-test reference. **Do not delete the file-walk
   path** — it's the auditable "this is what the answer
   should be" reference.

9. **Test convention: no `force=True` in equivalence tests.**
   The early Δ.3/Δ.4 tests called
   `corpus_index.rebuild(force=True)` to deterministically
   produce a fresh index. On Windows under xdist, that races
   with other workers' cached connections (PermissionError
   on `sqlite` unlink). The correct pattern is
   `corpus_index.invalidate() + rebuild()` — same effect
   without the race. Δ.5+ uses this convention; earlier tests
   were retrofitted when Δ.6 shipped.

**Why this needs all 5 infrastructure slices:**

Each unblocker eliminates one failure mode. Skipping any one
makes the wire-flip flaky:

| Skip                     | Failure mode                          |
|--------------------------|---------------------------------------|
| (3) rebuild lock         | concurrent writes corrupt the index   |
| (4) TTL fingerprint cache | 87 stat() calls per query → xdist storm |
| (5) notes_io hook        | edits during test → stale index reads |
| (6) per-worker storage   | cross-worker write race → SQLite lock |
| (7) warmup fixture       | cold tests hit first-rebuild race    |

A wire-flip attempted before all five land will hit one of
these and revert. The Δ.4.1 wire-flip succeeded on attempt #5
specifically because Δ.6/Δ.7/Δ.8/Δ.9 (the four infra slices)
+ the equivalence-test convention (no force=True) all landed
first. Treat new index-backed optimizations the same way:
**land every unblocker before flipping any wire.**

**Existing instances:**
- Δ.4 + Δ.4.1: file-walk `compute_matrix` → SQL-indexed
  `compute_matrix_indexed`. Empirical: file-walk ~3.2s on
  51K corpus, indexed ~263ms cold (~12× speedup); both
  sub-millisecond after the parent-level `@lru_cache(maxsize=1)`
  serves.
- Δ.5 + Δ.5.1: same shape for `dashboard_stats`. TTL=1s caches
  fingerprints between calls; same per-worker SQLite path
  convention reused.

**Anti-patterns:**

- Wire-flipping before all five infrastructure unblockers
  exist (you'll revert).
- Deleting the file-walk reference implementation after the
  wire flip (you lose the equivalence-test anchor — needed
  for any future change to the index schema).
- Using `force=True` in equivalence tests (Windows xdist
  race; use `invalidate() + rebuild()` instead).
- Sharing one SQLite path across xdist workers (cross-worker
  write race; always per-worker).

## 10. What this project is NOT

- Not a learning management system. Schools are an audience,
  not a feature category.
- ~~Not a multi-language UI.~~ Lifted 2026-05-09 (PLAN θ.5).
  The editorial apparatus baseline is English; localized UI
  shells (Spanish, Portuguese, French, German) are now in scope
  for the LONG TRACK once a real buyer ask materializes. Bible
  *content* in many languages remains the whole point;
  *interface* in many languages joins it as a long-tail roadmap
  item rather than out of scope.
- ~~Not a print-on-demand pipeline.~~ **Partially lifted
  2026-05-12** — focus remains digital retail, but ψ.22
  (multi-format export: PDF / MOBI / HTML / TXT) is now an
  open MEDIUM item in PLAN §7. Print PDF for direct buyer
  consumption (sample chapter PDFs land in ε.7 press kits;
  full-edition PDF in ψ.22) is in scope. Full POD (KDP
  paperback / IngramSpark) is still deferred — the
  print-cover-customize wiring exists in content/
  customization.yaml but the build pipeline integration is
  beyond v1.x. **(Superseded by the 2026-05-14 free-public pivot —
  see §1: no retail / sales / ISBN / POD. Multi-format export
  (PDF / MOBI / HTML / TXT) survives only as a FREE download
  option, never a retail product; "buyer" in older rules now
  means the "builder" who makes their own free edition.)**
- Not a real-time collab tool. One editor at a time. Git
  history covers the audit trail.
- Not Flask / FastAPI / Django. Standard library only on the
  backend; Tailwind CDN on the frontend. No build step.

## 11. Continuity protocol — keep dev/SESSION_STATE.md current

**The point of this protocol:** the user pays for tokens. Future
Claude orienting via grep + read-everything is wasted bandwidth.
SESSION_STATE.md is a tight ~150-line snapshot that any Claude
can read in seconds and be fully oriented.

### When to update SESSION_STATE.md

Always update it when:

1. **A phase ships** — record the new "last shipped" entry, bump
   the test count, refresh "next up".
2. **A save is requested** — verify SESSION_STATE.md is current
   BEFORE committing. If the doc is stale, it gets fixed first
   (in the same commit). (The Claude-Desktop-era zip flow is
   dormant — see §4; "save" = a local git commit.)
3. **A scope change happens** — corpus goal, north-star
   clarification, deferral or reactivation of a phase, etc.
4. **An external dependency or assumption shifts** — e.g. a
   source corpus is fetched, a new translation lands, a CLI tool
   is added.

Optional/nice but not required: update on every push turn. Don't
trip on this — phase-ship + save-time covers most cases.

### What SESSION_STATE.md must contain

Required sections (kept short — every line earns its place):

- **Current phase** — what just shipped, plus its v28a-NN tag
  if assigned.
- **Test count** — total + delta from last save.
- **Next up** — the single most-likely next phase, with a
  one-liner on why it's next per §3 sequencing rules.
- **In-flight notes** — anything mid-stream that future Claude
  needs to know to continue cleanly. Empty is fine.
- **Inventory pointers** — short references to "where things
  live" so future Claude doesn't have to grep (e.g.
  "popup languages live in scripts/build_edition.py around
  line 1100; per-book covers in scripts/core/covers.py").
- **Active rules / scopes** — links to the addenda that
  actively apply to current work.

### What it must NOT contain

- Long narrative recaps. CLAUDE_PROJECT_RULES.md and the addenda
  are the long form.
- Code snippets. They drift; rely on the actual code.
- Decisions Claude could re-derive. The doc is for things that
  cost tokens to re-discover.

### Update etiquette

- Edit in place; don't append-only. The whole doc is a snapshot,
  not a journal.
- Keep it under ~150 lines. If it grows past that, the rules
  doc or the plan probably needs the overflow.
- When the user sends a save command, the SESSION_STATE update
  can be inline with the save turn — just do it before
  committing. Don't ask permission.

## 12. Retrospective protocol — keep CHANGELOG.md and the rules current

The chronological progress log lives in `dev/CHANGELOG.md`. It is
**append-only**, with new entries at the top, one block per
session. Anyone can scroll through it to review the project's
history without reading the codebase: future-self, an auditor,
a buyer's tech-due-diligence reviewer, a future Claude trying to
understand why a decision was made.

### When to write a CHANGELOG entry

Always:
- **At the end of any session that shipped ≥1 phase**, before
  pausing or saving. Even a one-line entry is fine if the
  session was small.
- **Before any save (commit)**, ensure the entry for that
  session exists.

What goes in an entry: see § "Entry format" below.

### When to additionally run a retrospective

A retrospective is a brief self-review beyond just logging. Run
one when **any** of these triggers fire after work ships:

1. **A new architectural pattern appeared** — e.g. the encoder/
   decoder pair for per-book maps; the validate-then-write upload
   pipeline. If this pattern is likely to recur, codify it as a
   mental model in §9.

2. **Existing infrastructure was discovered mid-work** — i.e.
   you almost reinvented something. Add or sharpen an inventory
   pointer in SESSION_STATE.md so future Claude finds it without
   the same surprise.

3. **A rule wobbled or had to be invented on the fly** — e.g.
   you had to choose between two reasonable interpretations of
   §3 sequencing. If the resolution was good, codify it as a
   refinement to the rule. If bad, document the lesson.

4. **A memory rule needed updating** — the cross-session memory
   store (the `memory/` dir, see "Learning capture" below) is the
   cheapest cross-session reminder system; add or update a memory
   entry when a durable preference / gotcha / lesson appears.

5. **A scope clarification happened** — the north star, corpus
   target, or any §1–§2 universal principle shifted. Update the
   rules and SESSION_STATE.md accordingly; CHANGELOG.md captures
   the change moment.

If none of those fire, just log and move on. Retrospection is a
tool, not a tax — don't run one for ritual's sake.

### Learning capture — feed BOTH persistence layers at phase-close

Lessons only compound if they outlive the session. There are TWO stores; a
phase-close retrospective feeds whichever fit, and they must NOT duplicate:

1. **In-repo docs** (project-specific, versioned, re-read every session via §0):
   a reusable how-to → a §9 mental-model recipe; what-shipped / next / inventory
   pointer → `dev/SESSION_STATE.md`; the dated journal → `dev/CHANGELOG.md`; a
   data-flow or "where does X live" fact → `dev/MATRIX_MAP.md` / `dev/REPO_MAP.md`;
   a rule that wobbled or went stale → fix it in THIS doc at the same commit (the
   §1 self-upgrading-matrix rule).
2. **Cross-session memory** (harness-level, loaded into every conversation):
   durable user preferences, working-style feedback, environment gotchas, and
   "this approach paid off / this trap cost time" lessons that are NOT tied to one
   file. Update an existing memory before adding a new one; link related ones.

**The split:** if a future Claude could re-derive it by reading the current repo,
it goes in-repo (or nowhere); if it's a preference, a cross-cutting gotcha, or a
*why* the code can't show, it goes to memory. **Cadence:** run this at every
phase-close and on the retrospective triggers above — not per-commit. Capturing is
cheap; re-discovering the lesson next session is not. (Example — 2026-05-23 WLC
ingest: the §9 "Add a new translation" recipe + SESSION_STATE / CHANGELOG /
MATRIX_MAP were updated in-repo; the test-suite hang-detection and the
categorize-every-diff verification discipline were saved to cross-session memory.)

### Mistakes & near-misses → root-cause, then codify a preventive guard (always, same commit)

When something goes WRONG or nearly does — a defect shipped, a false or over-stated
claim, a destructive/surprise action, a near-miss, or anything that "should not have
happened and is preventable" — fixing the instance is NOT enough. Run a brief
post-mortem and codify the cheapest durable guard so it cannot recur, **at the same
commit** (never defer it to "next session" — the next session resumes on "continue",
which never fires the deferred fix). This is non-negotiable for any preventable
lesson; a genuine one-off that truly cannot recur just gets logged and skipped.

1. **Root-cause first, never the symptom** (`superpowers:systematic-debugging` Iron
   Law). Patching where it surfaced without finding *why* guarantees recurrence.
2. **Pick the cheapest guard that makes recurrence impossible, by failure type:**
   - *Technical defect a check could catch* → add the test / lint / gate (the §1
     self-upgrading "defect found ≠ defect prevented" rule). Instances: the §9
     nested-anchor gate (after the 14,568-instance base regression); the
     `coord_in_canonical_extent` boundary guard (after out-of-extent notes); the
     `find_verse_region_b` root-fix + its TDD pins (after the same nesting recurred).
   - *Behavioral / process / judgment failure, or a* why *the code can't show* → a
     rule line in THIS doc and/or a cross-session memory (per the dual-store split
     above). Canonical instance: the commit/backup TRUTH GATE (§0 / §6.7 / §12 / §14
     + the `verify-commit-backup-truth` memory), added after the 2026-05-26 Torrey
     near-miss — verified work was reported "committed + backed up" while it sat
     uncommitted on disk.
   - *A rule that wobbled / an interpretation invented on the fly* → refine the rule
     (§12 retrospective trigger 3 above).
3. **Record it in the CHANGELOG** at that commit (what went wrong + the guard added)
   so the lesson is auditable, not silently absorbed.

The test of success: afterwards, the SAME mistake made the SAME way is caught
automatically or forbidden explicitly — by a machine check where possible, by a rule
where judgment is required. If no guard can make recurrence impossible, make it LOUD.
This generalizes the §1 self-upgrading rule (which fires on a step *unlocking* the
next) to the case where a *failure* is the trigger.

### Entry format

Each entry is a self-contained block, readable without context:

```
## YYYY-MM-DD — session-N — <one-line headline>

**Phases shipped:** ν.2.7-A, ν.2.7-B, π.4-A, φ.1, …
**Test delta:** +N (was M, now M+N)
**Save tag:** v28a-NN-{slim|full} (or "no save" / "pending")

What shipped (concrete, scannable):
- one bullet per concrete thing
- avoid prose; readers want the list

Notable decisions (only if any):
- the choice and the alternative considered, in 1–2 lines

Retrospective (only when triggered, see §12):
- pattern recognized: <description>; codified in §9 of rules
- inventory pointer added: <name>; see SESSION_STATE.md
- rule refined: <ref>; lesson was <one line>

Continuity pointers (links to relevant addenda or rule sections):
- dev/SCOPE_2026-05-07-addendum-...
- §6.1 (canonical book order rule)
```

### What CHANGELOG.md is NOT

- Not a replacement for git history (git is mechanical, this is
  editorial — what shipped *and why*).
- Not a replacement for SESSION_STATE.md (that's the *current*
  snapshot; this is the *journal*).
- Not for blow-by-blow micro-edits. One entry per *session*, not
  per *commit*.
- Not for retrospection that didn't happen. If §12 triggers
  didn't fire, don't fabricate them.

### Footnote — pre-summary audit (Tier 1, added after a real drift catch)

Before claiming "shipped X" — or "done / committed / backed up /
safe to /clear" — in any user-facing summary, run a 5-point audit.
Each item takes seconds; together they catch the drift class the
user previously had to catch manually.

1. **Test count reconcile** — run
   `pytest --collect-only -q | tail -1` and verify the number
   matches what the summary will claim. A divergence is almost
   always a sign that work was shipped without being tracked.
2. **Phase mention scan** — every Phase letter mentioned in the
   summary must appear in `dev/CHANGELOG.md` (this turn or
   earlier). If a phase letter shows up only in code/tests but
   not in CHANGELOG, you missed an entry.
3. **In-flight marker check** — `dev/IN_FLIGHT.md` should show
   `<!-- TRACKER-STATE: idle -->` if you're about to summarize a
   completed ship. If it's still `active`, either the work isn't
   done or you forgot to flip it.
4. **Linter ack** — run `python3 scripts/lint_rules.py`; for
   ship summaries, every check should be `pass` (or have a known,
   acknowledged warn). Don't ship over a `fail`.
5. **Commit/backup truth** — run `git log -1 --oneline` +
   `git status --short`. Any "done / committed / backed up / safe
   to /clear" claim MUST match git reality: HEAD shows this
   session's work, and (for a backup claim) the `git bundle --all`
   file exists on E:/F:. Uncommitted verified work → warn loudly
   ("NOT committed/backed up — say 'save'"), never reassure. NEVER
   defer a commit across a /clear (the next session resumes on
   "continue", which is not a commit trigger). This is the gate the
   other four don't cover — they verify work is *recorded*, not
   that a commit/backup *happened*.

Why these five specifically: each catches a different drift mode.
Tests vs claim catches **counted-but-not-recorded** work. Phase
mentions catch **shipped-but-not-journaled** work. In-flight
catches **task-left-open**. Linter catches **structural drift**
(cross-link, encoder order, doc references). Git-truth catches
**claimed-saved-but-uncommitted** work — the 2026-05-26 Torrey
near-miss: the prior session reported the work "committed and
backed up" while HEAD didn't reflect it and no bundle existed,
and all four other points passed.

The user caught me on (1) once and that was enough; the other
four are preventive layers.

---

## 13. Topic-shift protocol — audit before pivoting

The single most expensive failure mode of this conversation has
been **topic-shift drift**: I'm mid-task on feature A, the user
asks an unrelated question about B, I respond to B without first
recording where I was on A, and A's work gets orphaned in the
codebase. This was confirmed in a real drift event on
2026-05-07 — ν.6 chapter labels shipped fully but never landed
in the addenda; the user caught it manually by auditing test
counts.

The fix is a behavioral rule: **when the user pivots topic, the
pivot is a signal to close the loop, not to abandon it.**

### When the topic-shift protocol fires

The trigger is a new user message that is substantially
**off-topic from the immediately-prior assistant message**.
"Substantially" means:

- different phase / feature / system area
- different artifact (was code, now docs; was UI, now data)
- different mode (was building, now discussing)

A clarifying question on the same topic is NOT a topic shift.
"Push" / "Continue" / "Save" are NOT topic shifts.

### What the protocol says to do

Before responding to the new topic:

1. **Read `dev/IN_FLIGHT.md`** — is the marker `idle` or `active`?
2. **Check working-tree state** — `git status --short` if available;
   look for modified or new files that aren't yet documented.
3. **Run the linter** — `python3 scripts/lint_rules.py` surfaces
   any drift the user wouldn't catch manually.

If any of those signal in-flight work, **the first part of the
response is reconciling that work**. Either:

- finish it now (preferred — the pivot can wait one turn)
- explicitly note "I was mid-task on X; pausing it to address
  your new question; here's where it stood so I can resume"
- archive it as abandoned with a CHANGELOG note (rare; only when
  the pivot makes the in-flight work irrelevant)

Then engage with the new topic.

### Why this can't be fully automated

The linter's `check_inflight_freshness` and `check_untracked_phases`
catch *symptoms* of drift after the fact. They don't catch the
*moment* of topic shift, because that's a content-level
judgment about the user's message — and "are these two messages
about the same thing" is a question only a human-or-LLM-level
reader can answer.

So this rule is a behavioral commitment: notice topic shifts,
treat them as audit triggers. The automated checks are the
backstop for when this rule slips.

### What good adherence looks like

Bad (what happened on 2026-05-07):
> Me: [shipped ν.6 chapter labels via 7 tests + UI but didn't
> update CHANGELOG]
> User: "Should the book ToC have a square pill or no pill?"
> Me: "Great question, here's my opinion on pills... [pivots]"
> [ν.6 ships orphaned; user catches it 3 turns later]

Good (what would have prevented it):
> Me: [shipped ν.6 — but before any further response, runs the
> linter, sees CHANGELOG/SESSION_STATE haven't caught up, says:]
> "Before answering: I just shipped ν.6 chapter labels. Let me
> log that first, then I'll address pills."

The cost of the audit is small (one linter run, one CHANGELOG
update). The cost of skipping it is large (orphaned work, manual
audit by the user later).


## 14. Session-resume / state-uncertainty audit

A close cousin of §13. Where §13 fires on **the user pivoting**,
this one fires on **Claude being uncertain about state**. Different
trigger, same defense.

### When this protocol fires

Any time Claude has reason to think the working tree might be
in a different state than its in-context mental model:

- A `[NOTE: This conversation was successfully compacted...]`
  marker at the top of context — long stretches of work were
  summarized away
- A long stretch of session has elapsed since the last `view` or
  `bash_tool` call against a file
- An IN_FLIGHT or SESSION_STATE edit fails because the file's
  current content differs from what Claude expected
- A test count, file list, or grep result returns numbers Claude
  doesn't recognize from this turn's context
- An str_replace fails because the "old_str" isn't there anymore

### What this protocol says to do

**Before acting**, audit the actual state:

1. **Read `dev/IN_FLIGHT.md`** — what does the marker say? what
   does the active-task block describe?
2. **Grep for the phase / feature** Claude was about to work on —
   `grep -rn "ν\.5\|preview_impact" scripts/ tests/` — and check
   if it's already shipped
3. **Run `pytest --collect-only -q | tail -1`** — does the test
   count match the last claimed number?
4. **Run `python3 scripts/lint_rules.py`** — any warnings or
   failures?
5. **Run `git log -1 --oneline` + `git status --short`** — does
   HEAD reflect the work the *last* session claimed it committed,
   and are there uncommitted changes the user may believe were
   already saved? This is the backstop for a prior session's false
   "it's committed / backed up" sign-off (added after the
   2026-05-26 Torrey near-miss: 21,762 verified notes were left
   uncommitted on disk across a /clear despite a "committed +
   backed up" claim — the resume audit's other four steps don't
   look at git). If HEAD lags the last SESSION_STATE's described
   state, surface it FIRST and offer to commit (it needs an
   explicit "save").

If any of these surface state Claude didn't expect, **revise the
plan**. The user might think Claude is starting work that's
already shipped. Saying so explicitly ("I was about to start ν.5,
but the audit shows it's already shipped in PUBLISHER_HTML; the
remaining work is the CUSTOMIZE wiring") is honest and saves
both sides a wasted turn.

### Why this is separate from §13

§13 is about the **user's** signal (a topic pivot in their message).
§14 is about Claude's **own** signal (uncertainty in its mental
model). The protocols are similar — audit before acting — but the
trigger sources are different, so the cues to watch for are
different. A user pivot is rare (a few per session); state
uncertainty after compaction is common (every long session).

### Real instance

On 2026-05-07, after a context compaction, I was about to start
ν.5 (change-impact preview) from scratch. The IN_FLIGHT.md file
showed unexpected content I didn't write — "ν.5 change-impact
preview shipped 2026-05-07 in PUBLISHER_HTML; CUSTOMIZE_HTML
wiring is the natural follow-up." Treating this as a §14
trigger, I audited (`grep -n "ν\.5\|preview_impact" scripts/web.py`
showed extensive existing implementation; tests had 7 new tests
in `# ---------- Phase ν.5 :` block; CHANGELOG had a full ν.5
entry). The correct task was the customize-wiring follow-up,
not a from-scratch build. The audit caught it before any
duplicated work.


## 15. Chain of command — the tier hierarchy as a matrix

The drift-detection guardrails are organized as **four tiers**.
This section documents how they relate: which one fires first,
which catches what, and how they escalate when one slips.

### The two axes

There's a **chain** (precedence — who acts first) and a **matrix**
(coverage — what each tier specializes in catching). They're
orthogonal: the same tier appears in the chain at one position
and in the matrix specialized for one drift class.

### The chain — escalation order

```
TIER 4  Behavioral protocols      ← FIRST line of defense
        (§13 topic-shift,           Catches drift before it
         §14 state-uncertainty)     happens. If perfect, no
                                    other tier needs to fire.

TIER 1  Per-turn pre-summary      ← SECOND line
        audit (§12 footnote,        Catches drift before the
         5-point checklist)         user reads the response.

TIER 2  IN_FLIGHT.md tracker       ← STATE OF RECORD
        (§11, §4 checkpoint        Persistent evidence across
         saves)                     turns. Survives compaction.
                                    If T1 missed, T2 still
                                    shows what was open.

TIER 3  Continuous linter          ← FINAL backstop
        (scripts/lint_rules.py,     Surfaces drift to humans
         the invariant-check suite) on every preflight run.
                                    The auditable "did
                                    anything escape?"
```

The order matters: **earlier tiers are cheaper and prevent
later tiers from needing to fire**. Tier 4 is just human
judgment (free per-turn). Tier 1 is one shell command. Tier 2
is a file edit. Tier 3 is the same shell command but
broader-scoped. If you must pay any of these costs, pay the
earliest one.

### The matrix — what each tier catches first

```
                       drift class
                       ─────────────────────────────────────────
                       counted-but-  task-left-  structural   pivot/
                       not-recorded  open        invariant    state-uncertain
                       ─────────────────────────────────────────
TIER 1 audit           PRIMARY       secondary   no           no
TIER 2 IN_FLIGHT       no            PRIMARY     no           secondary
TIER 3 linter          backstop      backstop    PRIMARY      no
TIER 4 protocols       no            no          no           PRIMARY
```

Read this as: each drift class has one **primary** owner (the
tier that catches it earliest in its lifecycle) and possibly
one or more **secondary/backstop** owners.

- **counted-but-not-recorded** (e.g., test count claimed wrongly)
  → Tier 1 catches it before the user sees the wrong number
- **task-left-open** (e.g., shipped but undocumented)
  → Tier 2 catches it because the marker stays `active`
- **structural invariant** (e.g., a console without cross-links)
  → Tier 3's lint check catches it on the next preflight
- **pivot / state-uncertain** (e.g., resuming after compaction)
  → Tier 4's behavioral protocol catches it before any code runs
- **claimed-saved-but-uncommitted** (e.g., a "committed + backed
  up" claim while HEAD lags or no `git bundle` exists)
  → Tier 1's git-truth check (pre-summary audit point 5) catches
  it before the user reads the claim; the §14 resume audit
  (Tier 4) is the cross-session backstop. (Added with the §12
  5-point audit after the 2026-05-26 Torrey near-miss; kept out
  of the grid above only to keep it readable.)

### When to escalate

If a tier's PRIMARY ownership of a drift class slips, the
**backstop** tier covers — but there's a cost. The cost shows
up later, the user might catch it manually, and trust suffers.
Treat each escape (a thing the linter caught that the protocols
should have caught earlier) as a §12 retrospective trigger:
either the protocol needs sharpening, or the rule needs a
better automated backstop.

### Real example of the chain in action

The original drift event (early 2026-05-07): I shipped ν.6
chapter labels (code, tests, UI all complete) but never updated
CHANGELOG. The user caught it manually with a test-count
audit ("you claimed 262 tests, actual is 269"). At that point:

- Tier 4 had failed (I didn't audit before pivoting topics)
- Tier 1 didn't exist yet
- Tier 2 didn't exist yet
- Tier 3's `untracked_phases` check didn't exist yet

So the user was the de-facto Tier 5. After the catch, all
four tiers were built in one push (ω.0.4). Now if Tier 4
slips again, Tier 1 would catch the test-count mismatch
before claiming ship; if Tier 1 slips, Tier 2's stale-marker
check would surface in the next linter run; if Tier 2 slips
because the marker was never flipped, Tier 3's
`check_untracked_phases` flags the phase mention without a
CHANGELOG entry.

Four levels, one task: keep drift visible.



```
dev/PLAN_<date>.md                          master sequence doc
dev/SCOPE_<date>.md                         original scope statement
dev/SCOPE_<date>-addendum-<topic>.md        major feature specs
dev/ROADMAP_FUTURE.md                       deferred ideas
dev/SPEC_MU_SYMBOL_TOGGLE.md                symbol toggle (μ phase)
content/translations/<id>/_meta.yaml        per-translation metadata
HANDOFF_README_v7.md                        deep architecture handoff
```
