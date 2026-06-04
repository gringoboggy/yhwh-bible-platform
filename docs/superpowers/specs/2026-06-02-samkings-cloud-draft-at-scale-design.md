# Samuel/Kings Dual-Witness Draft-at-Scale on a Cloud Pod — Design Spec

**Status:** ⛔ DROPPED 2026-06-04 — the cloud-pod draft-at-scale approach was tried (RunPod Samuel bulk, 2026-06-04) and **FAILED** (0 usable chapters), then **dropped by the user** (*"drop all the vm plans"*); the pod was terminated. Sam/Kings continues via the local agent-path marathon. Kept for history. *(Was: design — approved 2026-06-02; draft-at-scale + auto-converge · full dual-witness per chapter · Approach B pre-index folios.)*

> Companion to: `specs/2026-06-02-tewahedo-reverification-and-triaged-reingest-design.md` (parent program), `specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md` (the dual-witness method), `plans/2026-05-17-samuel-phase2-collation-tool.md` (the authorized collation tool), `plans/2026-05-17-kings-manuscript-collation.md`. Hardware context: memory `reference_hardware_box_and_mac` + `reference_runpod_cloud_budget`.

---

> **⚙ Implementation reality (2026-06-02, post-codebase-exploration — supersedes any "build new tooling" reading below):** The dual-witness collation pipeline ALREADY EXISTS and is production-ready (`scripts/core/manuscript_{manifest,collation,reconcile,records,vision,chapter_class,rounds,self_check}.py` + the `run_manuscript_{transcribe,review,collation}_at_scale.py` track-parameterized drivers). Consequences: **(a)** the Phase-0 "folio index" = the EXISTING `content/manuscript/{samuel,kings}/manifest.yaml` (chapter → `{CAM:{folios,views}, GG:{folios,source_images}, status}`), seeded only for the 4 Samuel + 6 Kings calibration chapters → Phase 0 = COMPLETE it for the ~92 pending chapters (a vision task, **no new pipeline code**). **(b)** Phase 2's "dualwitness_chapter workflow" = the EXISTING at-scale drivers, run on the pod. **(c)** The two witnesses are **CAM (Cambridge Add. 1570) = base** and **GG (Gunda Gundē) = 2nd witness** (the §2/§3 prose below at first mislabeled the 2nd witness as "Cambridge"; CAM *is* Cambridge — corrected). **(d)** CAM hi-res is on disk only for the calibration chapters → Phase 0 must pull the rest via CUDL IIIF (`acquire_cudl_master.py`). P0 detail: `plans/2026-06-02-samkings-folio-index-p0-plan.md`.

## 1. Motivation

The Samuel/Kings dual-witness Ge'ez collation is the highest-fidelity own-versification work in the project, but it is **~90 chapters / ~2,700 verses from done** (1sa ~107 v of ~810; 2sa ~26 of ~695; 1ki ~191 of ~816; 2ki **0** of ~719). On this N95 box the marathon is permanently throttled — 16 GB soldered RAM forces MAX-1-heavy vision + a Workflow concurrency cap of 2, and it is user-paced (per-page check-in). At that rate the full Sam/Kings sweep is a very long road.

The user has loaded **$17 of RunPod credit** (GitHub-linked) to test whether a cloud pod — with more RAM + cores than the N95 — can run this heavy manuscript transcription **in parallel and autonomously**, to "see how much of Sam/Kings $17 can get done." This spec designs that run.

**Key reframe (settled in brainstorming):** the $17 rents *box time*, not transcription. The Opus vision runs on the user's **Max subscription** (remote; `claude setup-token` auth on the pod — no API spend). The pod buys **RAM + cores + a clean Linux env** so we can lift MAX-1-heavy → run many chapters concurrently. The real ceiling is the Max weekly quota, not the $17 — and the marathon's per-page burn is modest enough that quota is unlikely to bind for a measured run.

## 2. The three keystone decisions (user-approved 2026-06-02)

1. **Execution mode = draft-at-scale + auto-converge.** Run many chapters in parallel, autonomous (no per-page check-in). Per witness, 2 blind passes: where they **agree** → a clean draft; where they **diverge** → the chapter is **flagged for the Track-1 QA wave**. Maximizes volume while keeping a fidelity gate.
2. **Witness scope = full dual-witness per chapter.** Each chapter gets the complete method — BOTH manuscripts (base = **CAM** = Cambridge Add. 1570; 2nd witness = **GG** = Gunda Gundē) read and collated into the diplomatic-parallel + apparatus. Higher cost per chapter, fewer chapters per dollar, but each finished chapter is collation-complete (honors the project's quality-over-speed doctrine).
3. **Architecture = Approach B (pre-index folios, then autonomous).** The brittle, gotcha-prone step — locating each chapter's CAM + Cambridge folios *by vision* (CAM packs ~1.5–2 chapters per folio across 3 columns; locate-by-vision-not-arithmetic, per memory `feedback_cam_folio_location`) — is solved **once, carefully, up front** as a reusable folio index. The autonomous pod loop then runs against that index, so folio-location errors can't compound unattended across 90 chapters.

## 3. Architecture — four phases

### Phase 0 — Folio index (on the N95, cheap, BEFORE any pod spend)
Build `content/translations/sources/manuscripts/sam_kings_folio_index.json`: for every chapter of 1sa/2sa/1ki/2ki, the CAM folio(s) + view-id(s) and the Cambridge MS Add. 1570 folio(s)/IIIF view(s) that carry it, located by vision (re-using the CUDL IIIF access in memory `reference_cudl_iiif` + the existing collation tooling). Each entry records the column/region hints needed to crop the chapter. This is the one part that stays supervised; it is reusable forever and is the input contract for Phase 2.

### Phase 1 — Pod setup (one-time)
- Rent a **CPU pod** (Option-1-class — ~9 vCPU / 50 GB RAM @ ~$0.27/hr → ~63 h from $17 — or a cheaper **CPU-only** SKU if RunPod offers one; the GPU/VRAM on the listed pods is wasted for us). Verify live pricing in the RunPod console (Chrome, read-only, with the user) before committing.
- **Login** via GitHub OAuth. **Auth Claude Code** via `claude setup-token` (generated on the N95 where a browser exists → `CLAUDE_CODE_OAUTH_TOKEN` on the pod). No API key, no per-token spend — the Max subscription does the inference.
- **Code:** `git clone` from the GitHub mirror.
- **Images:** upload the **~1 GB GAPS Sam/Kings folios** to the pod's persistent volume (git can't carry them — `GAPS/` is gitignored + LFS is rejected). One-time transfer (scp/rsync or RunPod volume upload).
- **Attach:** the **VS Code RunPod extension** (Remote-SSH to the pod) or plain SSH + `tmux`.

### Phase 2 — The autonomous run (on the pod)
A crash-resilient Workflow that processes chapters **N-in-parallel** (N bounded by `min(16, vCPU−2)` and RAM headroom). Per chapter:
1. **Render** CAM + Cambridge crops from the folio index (PyMuPDF / IIIF tiles).
2. **2 blind vision passes per witness** (4 passes/chapter), each carrying the honesty-contract prompt (the (q)/(u)/(v) guards + calibration aids).
3. **Auto-converge per witness:** glyph-level agreement → accept; divergence → record the locus, mark the chapter `needs_qa`.
4. **Collate** the two witnesses into the diplomatic-parallel + apparatus (base = CAM), re-using the existing `manuscript_collation` engine / the authorized Phase-2 collation tool.
5. **Write** the chapter into the `geez-tewahedo` store (`1sa/2sa/1ki/2ki.py` + `_apparatus.json`), codepoint-gated (Ethiopic-only).
6. **Commit + push to GitHub AND GitLab per chapter** — on the pod this dual-remote push *is* the off-machine backup (the E:/F: bundle legs are local-to-the-N95; replaced here by the two remotes).
7. **Instrument:** append tokens / wall-time / convergence-rate / `$`-estimate per chapter to a run ledger.

### Phase 3 — Measure + decide
Run **one pilot chapter end-to-end first** (recommend 1sa, the most-calibrated) to (a) prove the pipeline works unattended on the pod and (b) measure real $/chapter + tokens/chapter + convergence rate. Then let the run continue to a **budget guard** (hard stop at a set $ spend, or when Sam/Kings drafts are complete). Final report: chapters drafted, $/chapter, convergence rate, and the `needs_qa` backlog handed to Track-1.

## 4. Components & interfaces

| Component | Purpose | Input → Output |
|---|---|---|
| `build_folio_index` (Phase 0) | locate CAM+Cambridge folios per chapter by vision | GAPS images / IIIF → `sam_kings_folio_index.json` |
| `render_chapter_crops` | crop CAM + Cambridge regions for a chapter | index entry → PNGs in pod temp |
| `dualwitness_chapter` workflow | 2 blind passes/witness → converge → collate | crops → chapter collation object + `needs_qa` flag |
| convergence gate | accept-or-flag per glyph locus | 2 passes → accepted text + divergence list |
| `geez-tewahedo` store writer | persist the chapter | collation object → `<bk>.py` + `_apparatus.json` |
| run ledger + budget guard | instrument + stop | per-chapter metrics → ledger + halt signal |

Each unit has one purpose and a clean interface; the folio index is the only cross-phase contract.

## 5. Honesty contract (unchanged, travels with every agent)
No fabrication, no harmonization toward the MT/standard text; verse endings + pluses verified against the glyphs (the (u) guard); a pass that recites instead of reads is rejected (the (q) guard); **load-bearing glyphs are re-verified even on A=B agreement** (the new (v) guard from Esther p34 — two independent passes can share a misread); apparatus is a calibration anchor, excluded from the verse text (the (r) guard); codepoint-gate Ethiopic-only; the 9 KJV editions are never touched (byte-stable by construction — this lane writes only `geez-tewahedo`).

## 6. Cost model (the $17, for reference)
$17 ÷ ~$0.27/hr ≈ **63 pod-hours** (Option-1-class). Full dual-witness = 4 vision passes + a collation per chapter; with ~7 chapters in flight, throughput is gated by the Max quota, not the pod. The pilot calibrates the true $/chapter; the budget guard makes "how far does $17 go" a measured, bounded experiment rather than an open spend. The folio index (Phase 0) and any GAPS upload happen **before** the meter starts.

## 7. Risks & mitigations
- **Folio-location is the brittle part** → solved up front in Phase 0 (Approach B), reusable, supervised.
- **Manuscript vision is harder than Esther's print** → the pilot chapter gates the full send; divergent chapters auto-flag to QA rather than ship silently.
- **Pod backup ≠ the 5-leg save** (no E:/F:) → the per-chapter dual-remote push is the off-machine guarantee; optionally pull a bundle to E:/F: when re-attaching from the N95.
- **Quota** → modest per-page burn + the budget guard; the run reports if it ever throttles.
- **Cost overrun** → hard budget guard + power the pod OFF between sessions (per-hour billing).

## 8. Decomposition → implementation phases (for `writing-plans`)
- **P0 — Folio index** (`sam_kings_folio_index.json`, on the N95). The prerequisite; gates everything.
- **P1 — Pod bring-up runbook** (rent/login/auth/clone/upload/attach) + the GAPS upload tool.
- **P2 — The `dualwitness_chapter` workflow** + convergence gate + store writer + ledger/budget-guard (built + unit-tested on the N95 against the index, *then* run on the pod).
- **P3 — Pilot chapter + measure** → then the bounded full run + the Track-1 QA hand-off.

## 9. Success criteria
A reproducible cloud lane that, from $17, produces **collation-complete dual-witness drafts** of as many Sam/Kings chapters as the budget allows, each codepoint-clean and committed to both remotes, with a measured $/chapter + a clean `needs_qa` backlog for Track-1 — and a folio index + pod runbook reusable for the rest of the re-verification program.
