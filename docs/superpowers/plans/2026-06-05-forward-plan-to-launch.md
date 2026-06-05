# Forward plan — to launch (9 editions mint) and beyond (2026-06-05)

**Status:** ACTIVE 2026-06-05 — the master forward plan from this point. Done-line = the 9 KJV editions mint; Ge'ez/Amharic = future updates. Grounded by the `forward-plan-survey` workflow (editions-readiness · backlog-triage · website/socials). Spine: re-ingest #2–5 (Mac) → split audit + fix pass → [USER] device test → launch `v1.0.0-beta.1` → post-launch Growth/Outreach + the Ge'ez/Amharic arc.

> **The done-line (user-set 2026-06-05):** the program is DONE when the **9 KJV/English study editions work as intended — mint**. The **Ge'ez + Amharic standalone Bibles are FUTURE updates** (shipped when those transcriptions finish), not launch blockers. This lifts whole lanes (LANE D / M / P — all Ge'ez/Amharic/manuscript) off the critical path. **Main concern right now: the program + the 9 editions in mint condition.** Carry the "9 now, Ge'ez/Amharic coming" message to the website + socials.

---

## Where we are (survey-grounded)
The 9 editions are **structurally mint already**: every edition builds to valid EPUB (epubcheck 0/0/0/0 on the flagships incl. the canon-filtered case), 0 nested anchors / 0 broken links, the byte-stable invariant holds, and the whole **RX** (Kobo reading-experience: scaffold strip · cross-reader CSS · embedded fonts · badge note-display · file-splitter · Kobo-safe/native ToC), **σ** (HOLY-BIBLE cover + truthful front matter), and **ρ.3** (hierarchical customization) arcs shipped. **The remaining gap to "mint" is NOT structural** — it's (a) content-correctness (re-ingest #2–5), (b) the audit gate, (c) the human eyeball, (d) launch logistics.

---

## The critical path (the spine) — ordered
| # | Step | Machine | Blocks "mint"? |
|---|------|---------|----------------|
| 1 | **Re-ingest #2–5** — lang-greek Theós (1,196) · topic-torrey (596) · lang-greek Phōs (76) · topic-nave (87); one defect/commit, §0 ship bar (build BOTH eth + catholic-study, epubcheck 0/0/0/0; XHTML-escape new prose). **In flight.** | **Mac** | ✅ yes |
| 2 | **Split deep-audit (round 5) on the COMPLETE content** → merge on N95 → **prioritized fix pass** (security + silent-data-loss first; fold in the live LANE-T correctness subset the audit surfaces). The formal mint gate. | **Both** (win=tests/builds dims · mac=code-review dims) | ✅ yes |
| 3 | **e-reader device test** — sideload the built EPUBs on the color Kobo + Apple Books; confirm art/fonts/popups/ToC/speed. The one check only the user can do. | **USER** | ✅ yes |
| 4 | **Launch `v1.0.0-beta.1`** — see Launch section. Gated on: Apple notarization (pending Apple) + the audit + the user's explicit go. | Mac + Windows + USER | launch, not "mint" |

**Re-ingest #2–5 → audit → device test are the three real gates to "mint."** Everything after is launch logistics + post-launch.

---

## Both-machines task split (from here)
**MAC (baton now):**
1. Re-ingest #2–5 (in flight) → signal complete + push.
2. Then its **split-audit half** (12 read-only code-review dims; `LANE='mac'`) → push `findings-mac.json` to branch `lane-transfer/audit`.
3. When Apple notarization clears: finish it (`dev/notary_autofinish.sh` → staple → checksums) + flip `NOTARIZATION_STATUS.md`.

**WINDOWS (N95):**
1. Hold off main-repo work while Mac holds the baton for #2–5 (collision-free prep only).
2. After Mac signals #2–5 done: pull → run the **split-audit win half** (`LANE='win'`: tests-run · opt-build · byte-stability · rx-surfaces) → **merge** both lanes (`deep-audit-merge.js`, pre-built) → write `docs/superpowers/notes/2026-06-05-round5-split-audit-findings.md`.
3. **Lead the fix pass** (the audit's phased plan; byte-stability gate per build-path fix).
4. Stage the **launch swaps** (website copy diff + the release mechanics) ready for the user's go.
5. Collision-free now: apply the merged memory set (`lane-transfer/rules`); refresh stale VERSION metadata text; draft release notes.

**USER:**
1. The e-reader device test (after the fix pass produces the final EPUBs).
2. The launch go: cut the GitHub Release, publish the public source repo, complete email-forwarding test, approve the website launch-copy flip + post the socials launch.
3. Tiny decision: the `rev 1:8` "A Alpha" duplicate note (de-dup or leave).

---

## Launch `v1.0.0-beta.1` — the swaps (execute at the user's go, NOT before)
Artifacts: **Windows `dist/YHWH.exe`** (built + smoke-passed) · **macOS DMG** (signed; awaiting Apple notarization) · Linux AppImage (per the build chain) · the **2 EPUB editions** (built + 0-broken-links). `website/README.md` "Launch checklist" already documents the exact go-live swaps.

**★The website already carries the correct message** — it says **9 editions** everywhere (no "11" claim) and already frames Ge'ez/Amharic as future/in-progress. The ONLY change is flipping the **pre-launch "almost here" wording to "it's live" + activating the download buttons.** Specific edits (the `website/` dir under `YHWH v2.4/`):
- `src/index.html:25` hero ribbon "Public Beta — almost here" → "The public beta is here. Download →" (flip only once binaries are posted).
- `src/index.html:308–309` get-the-program → "is here — download today… builds nine English study editions; the standalone Ge'ez and Amharic Bibles are still being transcribed and arrive in future updates."
- `src/releases.html:13,14–17,38–39` taglines "almost here" → "is here / ready to try"; latest-release card → live.
- `src/releases.html:49–53` the three `is-pending` download placeholders → real `<a download>` links to `/releases/latest` + paste the SHA-256 lines.
- `src/roadmap.html:55–60` "Opening soon" stage → `is-shipped` / "Shipped — the first public release (Beta) is live." (Ge'ez stage at 49–53 STAYS "In progress" — correct.)
- `partials/head.html:47` repoint the "Code" nav link to the published public repo.
- Donations (`index.html:334–339`) already honest — only swap the GitHub-Sponsors `is-pending` span if/when approved.
Then `node website/build.mjs` → push the `yhwh-website` publish repo.

**Socials** (centralized in `partials/foot.html` + donations): X **@GringoBoggy** · GitHub/GitLab **gringoboggy** · email **gringo.boggy@yhwhyaway.com** · Ko-fi/PayPal live · Giscus comments live. **Launch posts are drafted** (survey result — short X version + long Ko-fi/Facebook version, both carrying "9 editions now, Ge'ez+Amharic coming as free updates"); they're ready to post at launch and seed the Growth/Outreach lane.

### Website — a DEDICATED Ge'ez & Amharic progress section (user-requested 2026-06-05)
Give the **Ge'ez + Amharic Bibles their own dedicated section/page** on the site (its own home — e.g. a `progress.html` page, or a prominent "The Ge'ez & Amharic Bibles" section), tracking the transcription work in detail:
- **Completion bar per Bible** (Ge'ez X% · Amharic Y%) + the English study program shown as "ready / launching." Per-component bars are clearer + more honest than one blended "whole project %".
- A **per-book status breakdown** — a grid/table of which books are transcribed/own-versified ✓, which are underway, which pending (e.g. "1 & 2 Samuel ✓ · Kings underway · …"), so progress is concrete, not just a number.
- The **narrative**: the careful, witness-by-witness manuscript work + method — the community sees the project's most distinctive effort move forward (builds trust AND anticipation).
- **The sources, shown/linked:** link the actual manuscripts + scholarly archives being transcribed (e.g. the Cambridge **CUDL MS Add. 1570** IIIF for Samuel/Kings, **Patrologia Orientalis**, the HaCohen apocrypha) — public scholarly sources, so linking is appropriate; it adds transparency + scholarly credibility and lets people SEE the real folios behind the work.
- **"What further support makes possible":** tie the section to the free-will offering — with support, the work goes faster (more witnesses collated, more books transcribed, the **Amharic** begun). **★INVIOLABLE:** the Word / digital output ALWAYS stays free; a gift *accelerates* the free work, it never *unlocks* it (per the monetization plan — revenue only on convenience/artifacts/support). This makes the section an honest, compelling fundraising narrative around a concrete, honorable cause.
- **Data-driven, not hand-maintained:** generate a small `progress.json` at build time from the REAL coverage (`scripts/render_coverage.py` + the `geez-tewahedo` own-versification store), and have `website/build.mjs` (or a tiny client fetch like the existing `releases.js`) render the section from it — so the numbers can never drift from reality.

This makes the "future update" honest AND visible, honors the manuscript work with its own stage, and gives it a real fundraising story. **It has grown past a single bar into a feature in its own right** (progress + per-book status + source links + funding narrative) — **Windows-buildable launch-prep, collision-free with the re-ingest**, but give it a proper **brainstorm → mini-spec** when we build it (presentation = a configurable option, per the project ethos).

---

## Backlog disposition (against the done-line)
**KEEP (do before/at launch — the 9-edition mint + builder + launch):** the split audit; the RX/builder customization tails (hierarchical-customize A/B/C2→C3, themes+popups, presentation-polish, fully-customizable-builder roadmap, Torrey-topical-index merge, builder-UI phases 3–4); website + monetization-Phase-1 (launch pages); and the launch-facing **LANE-T correctness subset**: **bookcode ★P0 BUGCLUSTER**, preview-XSS through `sanitize_html`, coverage-floor, smoke-cleanup, dead-checks→preflight, scoped code-debt, identity-docs decommercialize-tail, asset-licensing/attribution, [USER] eyeball. *(Most of these the audit will surface or confirm; fold them into the post-audit fix pass.)*

**DROP (already shipped / realized — just clear stale INDEX/roadmap statuses):** σ cover plan+spec; mint-10 & mint-11 plans (audit arc CLOSED `e4db438b`); lane-handoff design+plan; deep-audit-&-forward design; douay-vulgate design; verse-popup-regeneration design; LANE-0 mint-cleanup; LANE-A standalone-Ge'ez Phases A–C. *(A quick INDEX/roadmap status-sweep is itself a small KEEP task.)*

**DEFER → future updates (Ge'ez/Amharic/manuscript — not dropped):** LANE D (Phase-D own-versification re-ingest), LANE M (Kings/Samuel manuscript marathon), LANE P (the two-standalone parallel-Bible end-state); all the Ge'ez specs/plans (patrologia, own-versification, colometric, external-ingest, samkings, NT-Ge'ez-scope, tewahedo-reverification); LXX-Swete + translation-spine-arc + reverify (parallel-corpus depth); LANE-T chap-backfill, no-kjv-popups, phase-E, track-C, data-hygiene, vision-ocr; the Mac-second-lane-bringup (its workload IS the deferred corpus); the parked irregular-layout residual (Ethiopian-canon-only books).

---

## Post-launch lanes (future updates — deferred, not dropped)
1. **Growth / Outreach** (organic, NO automation — user-directed). Research the most influential reverent/church voices + communities on X (Orthodox / Catholic / Ethiopian-Tewahedo / Reformed / Bible-study / patristics / seminary) into a ranked map; craft value-first messaging per cluster + a small press-kit; run a tracked, sincere cadence (organic shares/reviews). The system is *organized genuine outreach at scale*, never bots/spam (which break X's rules + would taint a faith project). Owned by one lane post-launch; a deep-research pass → an outreach playbook.
2. **Ge'ez + Amharic standalone Bibles** — the big future-update arc: LANE D (own-versification re-ingest) → LANE M (manuscript marathon, user-paced) → LANE P (constitute the two standalone editions, then their EN back-translation popups). Ship as free updates "when they're ready, done right."
3. **Depth / polish updates** — the deferred LANE-T opportunistic items (track-C topical, phase-E appendix, translation-spine, etc.) as occasional free updates.

---

## Constraints carried
Never touch the off-limits marathon core; the 9 KJV editions MUST stay byte-stable (additive schema; `notes_io.atomic_write`); 5-leg save per phase; two-lane baton discipline (one committer to main at a time; `git fetch`+rebase before push). Quality/completeness over speed — but the done-line is concrete now: **9 editions, mint.**
