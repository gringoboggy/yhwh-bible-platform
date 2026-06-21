# Plan — Rules + Accuracy Consolidation (2026-06-21)

**Status:** ✅ READY TO IMPLEMENT — **staged for the NEXT session.** This is the prep artifact (user:
"find out what needs to be done and prepare for a new session where we will implement them"). Do NOT
implement in the session that wrote this.

**Inputs (both adversarially-verified):**
- Rules-system deep-audit — 47 confirmed findings. Verbatim edits: `docs/superpowers/notes/2026-06-21-rules-audit-findings.md` (run `wav5b34sh`).
- Website offer-accuracy audit — 9 confirmed findings (run `wnb2ijwmj`; embedded in Phase E below).
- The user's autonomy doctrine — memory `feedback_autonomous_work_ladder`.

**Prime directive for this work:** consolidate **by REFERENCE** (one canonical home + one-line pointers),
NEVER duplicate; do **not** re-bloat what the Grok cleanup just trimmed; every item ships with its
verification; the work-phase loop (§2.6) lands **LAST**, on a cleaned base.

**Judgment calls — RESOLVED (per the user's already-stated preferences; see §"Open for confirm" for the one residual):**
1. DEFER sink = **`dev/HUMAN_DECISIONS.md`** (a dedicated file — the user described it as the answer to "what do you need from me?"). DECIDED.
2. Marathon fallback scope = the loop's **"advance autonomously" step includes proactively staging Kobo `.kepub` + desktop device tests** (the user's ladder makes that priority work, not just fallback); **transcription is the LAST-resort fallback**. DECIDED.
3. Sequence = **consolidations FIRST, §2.6 loop LAST.** DECIDED (audit recommendation).
4. Regression lint guard for "background radar" = **RECOMMEND include** (matches the self-enforcing-system doctrine; cheap). Flagged for a yes/no in §"Open for confirm".

---

## How the next session runs this

1. `git pull` → read the triad → read this plan + the findings note.
2. Execute phases **A → H in order** (dependency-ordered). Local-commit per coherent slice; run each item's verification; `save-all.ps1` push at each phase boundary.
3. **Phase A is the prerequisite** for the §2.6 loop (Phase D) — the loop's step-1 pointer must land on already-fixed §4 text.
4. **Phase E** ends with a website rebuild + redeploy. **Phase F** is BLOCKED until Mac reports per-edition counts.
5. **Phase H** (Mac self-audit) goes out as `LANE_HANDOFF` rule-change-parity tasks, not WIN edits.
6. Done-contract at the end (see §Verification).

---

## Phase A — the radar contradiction seed (FIRST; unblocks the loop)

> One commit. Both edits are the same region of RULES §4.

- [ ] **A1** Fix the "background radar" contradiction — `dev/CLAUDE_PROJECT_RULES.md:549-551` (exact replacement in the findings note, item "contradiction/radar (THE seed)"). Canonical = §4:528-537. Keep :552-555 verbatim.
- [ ] **A2** Merge the duplicated §4 auto-pull blocks (528-537 + 549-555) into ONE (findings note: "redundancy (auto-pull stated 5×)"). Same region as A1 — do together. Leave AGENTS.md:106-110 + PLAYBOOK:19 (already correct pointers).
- **Verify:** `lint_rules.py` clean; grep RULES for "background radar" → only inside the "removed/no" negation.

## Phase B — contradictions + redundancy consolidations + bloat trims

> Several commits, one per logical item. Canonical-home rule: a fact lives in ONE place; others point.

Contradictions:
- [ ] **B1** Save-cadence digest drift — `AGENTS.md:346-347` → crash-safe cadence; reconcile with :362-364 (findings note: "contradiction (save cadence digest)").
- [ ] **B2** E:/F: partial-save disposition — `RULES:168, :474, :505-509, :1412-1413` (findings note: "contradiction (E:/F: partial-save)"). A STANDING-deferred drive = NOT "partial."

Redundancy → single canonical home + pointers:
- [ ] **B3** Save cadence (4 homes → RULES §4) — trim LANE_HANDOFF:80-86 · PLAYBOOK §6.6:105-108 · AGENTS.md:346-364 to pointers (findings note).
- [ ] **B4** Hard-coded corpus count (already rotted: 91,597≠live) — `PLAYBOOK:11,53,82` + `MATRIX_MAP:17-18,136,174` + `REPO_MAP:36` → "see SESSION_STATE.md."
- [ ] **B5** Pre-summary audit two shapes — `RULES:1393-1422` canonical; `PLAYBOOK §6.1:99` + §6.7:109 → pointer; **drop the hard-coded "≥7,667 collected."**
- [ ] **B6** Clone-deletion gate (2 homes) — canonical `PLAYBOOK §6.5:104`; reduce `LANE_HANDOFF:74` to a pointer; fix MEMORY.md:37→:38 citation.
- [ ] **B7** Book-count cascade (2 homes) — canonical `RULES:141-158`; **add the missing "release notes / GitHub release body" surface**; AGENTS.md:282-285 → pointer.
- [ ] **B8** MAC_WORK_QUEUE operating-model dup — collapse `MAC_WORK_QUEUE:3-8` to a pointer to LANE_HANDOFF STANDING.

Bloat → archive/invariant:
- [ ] **B9** Frozen stats in PLAYBOOK — `PLAYBOOK:11,53,82,84` → invariant + pointer. **Scope-fence:** keep "6 editions"/"6/6 schemas" + "83 shipped/87 registry."
- [ ] **B10** Test-narrative history — `PLAYBOOK:62` → move to `RULES_HISTORY.md`; one live line; no hard second-counts.
- [ ] **B11** Plugin roster snapshot — `RULES:234-253` → durable invariant ("trust the SessionStart hook's live `claude plugin list`").
- [ ] **B12** Stale mini file-index — delete `RULES:1566-1575`. **Precondition (same commit):** ensure REPO_MAP has `HANDOFF_README_v7.md` + `dev/ROADMAP_FUTURE.md`, then `py dev/trace_repo.py` + `repo_map_complete` lint.
- **Verify (phase):** `lint_rules.py` 0/0 · `trace_repo` complete · grep each moved fact resolves to one home.

## Phase C — cross-lane parity (hooks) + radar echoes

- [ ] **C1** Mac bootstrap baton→v2 model — `bootstrap-triad.sh:44,54-57` (findings note: "Mac bootstrap baton model"); fix inverted `.ps1:6` "Mirror of" claim; **add a lint/test asserting both hooks carry the same v2 substring** ("v2" + "BOTH lanes" + "TRUTH_OWNER").
- [ ] **C2** Mac session-start ping — add the prints-only-when-BEHIND `lane_ping` block to `bootstrap-triad.sh` (mirror `.ps1:119-135`, using `.venv/bin/python`→`python3`); rename both headers "LANE SYNC RADAR"→"LANE SYNC PING (seam check)"; delete the stale `.ps1:123-124` parenthetical. **Mark the Mac ping PENDING** at LANE_HANDOFF:120 + spec:55 until Mac re-installs+ACKs (→ Phase H).
- [ ] **C3** Backlog body radar residue — `AGENT_WORK_BACKLOG.md:20,21,23,25` reconcile to its own (correct) header (findings note).
- [ ] **C4** v2 design-spec radar echoes — `docs/superpowers/specs/2026-06-08-lane-coordination-v2-design.md:10,49` → seam wording.
- **Verify:** the new hook-parity test green; grep both hooks for "radar" → only "PING"/negation.

## Phase D — the work-phase loop §2.6 + HUMAN_DECISIONS.md (LAST, on the cleaned base)

- [ ] **D1** Create **`dev/HUMAN_DECISIONS.md`** (append-only table: date · what · why-needs-human · what-unblocks · raising-lane). Seed with the current open items (see below). Add to REPO_MAP.md (the `dev/` dangling-path lint hard-fails once cited). Add a one-line pointer near guard #5(a) RULES:77.
- [ ] **D2** Add **`§2.6 "Session work-phase loop"`** to RULES after §2.5 — POINTER-ONLY, 8 steps each ending in a §-pointer (findings note: "loop-fit (placement)"), with the **bold SAFEGUARD clause** (runs ONCE/session → clean quiescent stop; no watcher/poll/auto-continue; do NOT re-add the removed Grok radar scripts). Step structure per the resolved judgment call #2: step "advance" includes **staging Kobo+desktop device tests**; **transcription is the last-resort fallback**. Add the §2.6 row to the Rules-map table; mirror as ONE pointer in AGENTS.md + PLAYBOOK §4; collapse the inline ladder copies in MAC_WORK_QUEUE:31-34 + LANE_HANDOFF:7 to a §2.6 pointer.
- [ ] **D3** (if confirmed) Optional `lint_rules` guard flagging literal "background radar" outside negation/`dev/archive/`/CHANGELOG.
- **Seed `HUMAN_DECISIONS.md` with the current open human-gated items:** Kobo tap round (color Kobo) · Apple Books device re-QA of the rebuilt tablet artifact (M2 §user-fail) · Kindle Send-to-Kindle device check · Play Books phone QA (M5) · the `v1.0.0` tag command · the residual confirms in §"Open for confirm" below.
- **Verify:** `lint_rules.py` 0/0 (incl. the dangling-path check now satisfied); RULES reads coherently start→finish.

## Phase E — website offer-accuracy fixes (9) + rebuild + redeploy

> Edit `website/src/**`, then `node website/build.mjs` (0 dead links), then redeploy the publish clone. Counts here also touch Phase F — do the count-bearing ones (E7) consistent with F.

- [ ] **E1 (HIGH)** `how-to-use.html:58-60` — the stale "Kindle — Not yet" denial → the live Send-to-Kindle path (Kindle is `live:true`/M4; notes render as visible endnotes).
- [ ] **E2 (HIGH)** `ethiopian-bible-canon.html:54-55` — "1 & 2 Samuel — complete" is FALSE → move to in-progress with real coverage (1sa chs 1,3,17; 2sa ch 11); only Psalms 151/151 is "Complete."
- [ ] **E3 (HIGH)** `about-the-geez-bible.html:70-71` — same Samuel overstatement → "the chapters transcribed so far" (mirror the honest 1 Kings phrasing).
- [ ] **E4 (MED)** `index.html:48` — drop "Google Play Books" from the verified-reader list (it's `live:false`/M5); keep the generic "any standards-compliant reader."
- [ ] **E5 (MED)** `index.html:55` — remove "Anglican, Lutheran" as canon shapes (not real shapes / retired SKUs); keep Tanakh + generic examples.
- [ ] **E6 (MED)** `how-to-use.html:31` — drop/downgrade the Play Books endorsement (no Play column in the Releases matrix).
- [ ] **E7 (MED/LOW)** Canon counts — `how-to-use.html:130` Catholic "76" → the correct figure; `:132-133` Orthodox "78" → confirm against `content/canons.yaml` (one panelist refuted 78). **Coordinate with Phase F** (single source of truth for counts).
- [ ] **E8 (MED)** `geez.html:10-12` — scope "transcribed from manuscripts, witness-by-witness" to the **Geʽez** only; Amharic is as-written-from-PDF, not started ("a standalone Amharic Bible to follow").
- **Verify:** `node website/build.mjs` → "0 dead links"; rebuilt `index.html` byte-diff intended; redeploy publish clone; re-scrape og card if a count changed.

## Phase F — catalog count reconciliation (BLOCKED on Mac's per-edition counts)

> Mac is rebuilding the editions on the verified tree and will report exact per-edition note/kind counts (the +72 restored `comm`/`word` notes shifted them). WHEN those land:

- [ ] **F1** Sweep the full count cascade per RULES "Corollary" (now including release notes / GH release body per B7): page bodies · `<meta>`/og/twitter · social-card image (re-render) · GitHub + GitLab descriptions · EPUB metadata (`content.opf` `<dc:description>` + `introduction.xhtml`) · in-app trackers (`gen_website_progress.py`).
- [ ] **F2** Reconcile the website count numbers (91,553 → the new shipped figure) consistently with Phase E7.
- **Verify:** every surface in the cascade agrees; `gen_website_progress` shows no "not started."

## Phase G — small items

- [ ] **G1** Add "retard-proof" to the AGENTS.md public-copy guard (prime directive #10 / §10) alongside "idiot-proof" (the memory guard `feedback_plain_professional_copy` already covers it).
- [ ] **G2** Internal "idiot-proof" jargon (`test_home_idiotproof.py`, `2026-06-09-idiot-proof-app-design.md`, code comments) — **leave** (not public; renaming risks breaking refs) UNLESS the user asks. Listed for visibility.

## Phase H — Mac self-audit (→ LANE_HANDOFF rule-change-parity tasks, NOT WIN edits)

File the 7 Mac items from the findings note ("Mac self-audit") as parity tasks in `LANE_HANDOFF.md`:
save-cadence desync (HIGH) · lane-coordination v2 model · bootstrap re-install+ACK (after C1/C2) · radar-language sweep · §2.6 loop + HUMAN_DECISIONS.md mirror (after D) · stale-literal sweep · Mac RAM-hygiene line in `.sh` triad.

---

## Open for confirm (the one residual judgment call)

- **Regression lint guard (D3):** include the cheap pre-commit guard that flags a re-introduced literal "background radar"? Recommended **yes** (self-enforcing-system doctrine), but it is net-new lint surface — defaulting to include unless the user says skip.

(Everything else in the audit's "Propose to maintainer" is resolved above.)

## Verification / done-contract (at the end)

`py -3 scripts/ci.py` green · `py -3 scripts/lint_rules.py` 0 warn/0 fail · `py -3 dev/trace_matrix.py` 0 unresolved · `py -3 dev/trace_repo.py` complete · `py -3 -m scripts.ebible verify` errors=0 · the new hook-parity test green · `node website/build.mjs` 0 dead links · ≥1 canon-filtered edition rebuilt → epubcheck 0/0/0/0 (only if Phase F rebuild) · RULES reads coherently end-to-end · `IN_FLIGHT` TRACKER-STATE idle at close.
