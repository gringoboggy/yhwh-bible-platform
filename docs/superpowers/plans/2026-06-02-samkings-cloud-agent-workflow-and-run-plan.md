# Samuel/Kings Cloud Run — Agent-Path Workflow + Pilot + Bounded Run (P1–P4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** ⛔ DROPPED 2026-06-04 — the VM/cloud-pod approach was tried (RunPod Samuel bulk, 2026-06-04) and **FAILED** (1sa2 ran 2h10m then CAM error; chapters 2–51 instant-failed; 0 usable output), then **dropped by the user** (*"drop all the vm plans, we're doing it all the way we have been"*); the pod was terminated. Sam/Kings continues on the **LOCAL agent-path marathon** (`plans/2026-05-17-kings-manuscript-collation.md`). Kept for history; do NOT resurrect without a new explicit user decision. *(Was: ready — P1 buildable on the N95, free.)*

**Goal:** Produce collation-complete dual-witness Ge'ez drafts of the ~93 pending Samuel/Kings chapters on a rented cloud pod, with vision running on the Max subscription (zero API spend) and a hard budget guard — each chapter codepoint-clean, convergence-gated, and handed to the Track-1 QA wave where the two blind passes diverge.

**Architecture:** The transcription's vision call is the **agent path**, not the API path. A new batch Workflow (`.claude/workflows/samkings-dualwitness-batch.js`) runs *inside Claude Code on the pod* (authed by `claude setup-token` = the user's Max subscription). Per chapter it: renders CAM+GG crops (≤1568 px) → dispatches **2 blind Opus vision sub-agents per witness** (each Reads the crop, returns the `TRANSCRIBE_OUTPUT_SCHEMA` dict) → **converges** the two passes (agreement → clean draft; divergence → flag `needs_qa`) → feeds each accepted `model_out` to the **existing pure** `assemble_witness()` → writes the witness JSON in the exact on-disk contract → flips the manifest chapter to `calibrated` → runs the **existing, tested** `collate_base_structured()` pipeline. Everything downstream of the witness JSON is unchanged code. Output lands on the pod's durable network volume (`/workspace`) and is pulled back to the N95 in batches for the real 5-leg commit.

**Tech Stack:** Node + Claude Code (pod); Python 3.12 + PyMuPDF/Pillow/PyYAML (pod); the Workflow tool; existing `scripts/core/manuscript_{vision,records,collation,manifest,reconcile}.py` + `run_manuscript_{transcribe,review,collation}_at_scale.py` + `scripts/acquire_cudl_master.py`; pytest with `--basetemp` + `$env:PYTHONUTF8=1` (N95 tests per memories `reference_pytest_basetemp` / `feedback_pythonutf8`).

---

## Corrections this plan encodes (the "what we did wrong" from 2026-06-02)

1. **API path → agent path.** `run_manuscript_transcribe_at_scale.py` calls `client.messages.create` and `REFUSES` without `ANTHROPIC_API_KEY` (paid, out of budget per memory `reference_runpod_cloud_budget`). The cloud premise ("$17 buys box-time; inference rides the Max subscription") therefore requires a NEW orchestrator that drives vision via Claude Code sub-agents. This was never built — it is P1, the core of this plan. The drop-in seam is clean: `assemble_witness(model_out, …)` is pure, so a sub-agent that returns the same `model_out` replaces `vision_client.analyze` with zero downstream change.
2. **Transfer + auth.** A full-repo `git --all` bundle to a raw pod IP trips the auto-mode exfiltration classifier (correctly). Use the **lean ~75 MB tarball** (`scripts tests dev docs content` minus the heavy dirs — already built at `D:\yhwh-pod-subset.tgz`) over `scp` (rsync/runpodctl absent; scp + the agent-loaded ed25519 key are present). No GitHub credential on the pod.
3. **Frugal pod lifecycle.** Stopped pod = $0.00/hr displayed (network volume persists across Stop; only Terminate erases). The pod runs ONLY during active transcription; everything buildable on the N95 (P0 folio index, P1 workflow + tests) happens off-meter.
4. **Pod is OOM-proof.** The deployed A5000 reports a 128-core host / abundant RAM (allocation 9 vCPU / 25–50 GB); the N95's 16 GB OOM ceiling — the reason the API-path `manuscript_vision.py` was written and MAX-1-heavy was forced — does **not** bind on the pod. Real parallelism (Workflow cap `min(16, vCPU−2) ≈ 7`) is the entire point.

---

## Phase map

| Phase | What | Where | Meter | Gate to next |
|---|---|---|---|---|
| **P0** | Folio index: fill the 93 pending manifest entries (GG-walk on-disk + CAM IIIF acquire) | N95 | free | `tests/test_samkings_manifest_complete.py` green — see the P0 plan |
| **P1** | Build + unit-test the agent-path dual-witness workflow against the 4+6 **calibration** chapters | N95 | free | workflow reproduces a valid witness JSON + passing `base_structured_ok` for ≥1 calibration chapter |
| **P2** | Pod bring-up (corrected): start pod, lean-tarball transfer, deps, `setup-token`, GAPS upload, smoke | pod | **meter on** | `pytest -k manuscript` green on pod + one live vision pass returns valid schema |
| **P3** | Pilot: ONE chapter end-to-end on the pod via the workflow; measure tokens/wall-time/convergence/$ | pod | meter on | user reviews pilot fidelity + cost → GO |
| **P4** | Bounded autonomous run to the budget guard; per-batch pull-back + 5-leg commit on N95; `needs_qa` → Track-1 | pod | meter on | budget guard or Sam/Kings drafts complete |

P0 and P1 are independent and both free — do them in parallel on the N95. P2–P4 are gated on the user's "good pricing → feed it" trigger.

---

## P1 — The agent-path dual-witness workflow (N95, free, the core build)

**Files:**
- Create: `scripts/manuscript_assemble_witness.py` (thin CLI shim around the existing pure `assemble_witness` + `validate_witness`)
- Create: `scripts/manuscript_converge.py` (the convergence gate over two blind passes)
- Create: `.claude/workflows/samkings-dualwitness-batch.js` (the batch Workflow the pod's Claude Code runs)
- Test: `tests/test_manuscript_converge.py`
- Test: `tests/test_manuscript_assemble_witness_cli.py`

### Task 1: Convergence gate (`scripts/manuscript_converge.py`)

**Why:** draft-at-scale needs a deterministic, honest rule for "do the two blind passes agree?" reusing the collation engine's `fold_skeleton` so "same reading" is measured the way the rest of the pipeline measures it. Honors the honesty-contract guards: (q) a recite-not-read pass, (u) verse-ending pluses, (v) load-bearing glyphs even on A==B.

- [ ] **Step 1: Write the failing test** — `tests/test_manuscript_converge.py`

```python
"""Convergence gate over two blind transcription passes (model_out dicts)."""
from core.manuscript_converge import converge_passes  # adjust import to repo conftest pattern

def _mo(verses):  # minimal model_out
    return {"verses": verses, "transcription_notes": ""}

def test_identical_passes_fully_converge():
    a = _mo([{"v": 1, "geez": "ወይቤ ፡ ንጉሥ", "column": "c", "line_start": 1, "uncertain": []}])
    res = converge_passes(a, a)
    assert res["needs_qa"] is False
    assert res["convergence_pct"] == 100.0
    assert res["accepted"]["verses"][0]["geez"] == "ወይቤ ፡ ንጉሥ"
    assert res["divergent_loci"] == []

def test_token_divergence_flags_qa_and_records_locus():
    a = _mo([{"v": 1, "geez": "ወፈቀደ ፡ ንጉሥ", "column": "c", "line_start": 1, "uncertain": []}])
    b = _mo([{"v": 1, "geez": "ወረቀደ ፡ ንጉሥ", "column": "c", "line_start": 1, "uncertain": []}])  # ፈ→ረ misread
    res = converge_passes(a, b)
    assert res["needs_qa"] is True
    assert any(loc["v"] == 1 for loc in res["divergent_loci"])
    assert res["accepted"]["verses"][0]["geez"] == "ወፈቀደ ፡ ንጉሥ"  # pass A is the draft for divergent verses

def test_verse_only_in_one_pass_is_divergent():
    a = _mo([{"v": 1, "geez": "ሀ", "column": "c", "line_start": 1, "uncertain": []},
             {"v": 2, "geez": "ለ", "column": "c", "line_start": 2, "uncertain": []}])
    b = _mo([{"v": 1, "geez": "ሀ", "column": "c", "line_start": 1, "uncertain": []}])
    res = converge_passes(a, b)
    assert res["needs_qa"] is True
    assert any(loc["v"] == 2 for loc in res["divergent_loci"])
```

- [ ] **Step 2: Run it — confirm FAIL** (`ModuleNotFoundError: core.manuscript_converge`).

Run: `$env:PYTHONUTF8="1"; <python> -m pytest tests/test_manuscript_converge.py -v --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`

- [ ] **Step 3: Implement `scripts/manuscript_converge.py`**

```python
#!/usr/bin/env python3
"""Convergence gate over two blind transcription passes.

Each pass is a model_out dict ({"verses": [{"v","geez",...}], "transcription_notes"}).
Two verses "converge" iff their geez token sequences are fold_skeleton-equal
(the same equality the collation engine uses). Glyph-identical is reported
separately (the (v)-guard's load-bearing-glyph note). Any per-verse divergence
flags the chapter needs_qa and records the locus; the accepted draft uses pass
A for divergent verses so the chapter still has best-effort content.
"""
from __future__ import annotations

from scripts.core.manuscript_collation import fold_skeleton


def _toks(geez: str) -> list[str]:
    # wordspace U+1361 with surrounding spaces; tolerate raw splits
    return [t for t in geez.replace(" ፡ ", "").split("") if t.strip()]


def _verse_map(model_out: dict) -> dict[int, dict]:
    out = {}
    for mv in (model_out.get("verses") or []):
        if isinstance(mv, dict) and mv.get("v") is not None:
            out[mv["v"]] = mv
    return out


def converge_passes(pass_a: dict, pass_b: dict) -> dict:
    va, vb = _verse_map(pass_a), _verse_map(pass_b)
    all_v = sorted(set(va) | set(vb))
    divergent, identical, fold_equal = [], 0, 0
    for v in all_v:
        a, b = va.get(v), vb.get(v)
        if a is None or b is None:
            divergent.append({"v": v, "reason": "verse present in only one pass"})
            continue
        ag, bg = a.get("geez", ""), b.get("geez", "")
        if ag == bg:
            identical += 1
            fold_equal += 1
            continue
        ta, tb = [fold_skeleton(t) for t in _toks(ag)], [fold_skeleton(t) for t in _toks(bg)]
        if ta == tb:
            fold_equal += 1  # same reading, cosmetic glyph-order/diacritic diff
        else:
            divergent.append({"v": v, "reason": "token divergence", "a": ag, "b": bg})
    n = len(all_v)
    return {
        "needs_qa": bool(divergent),
        "convergence_pct": round(fold_equal / n * 100, 2) if n else 0.0,
        "identical_pct": round(identical / n * 100, 2) if n else 0.0,
        "divergent_loci": divergent,
        "accepted": pass_a,  # pass A is the draft; divergent loci are flagged for Track-1
        "verse_count": n,
    }
```

- [ ] **Step 4: Run it — confirm PASS** (same command as Step 2).
- [ ] **Step 5: Commit** — `git add scripts/manuscript_converge.py tests/test_manuscript_converge.py && git commit -m "feat(manuscript): convergence gate for blind dual-pass transcription"` then the 5-leg `save-all.ps1` (memory `reference_save`).

### Task 2: Assemble-and-write CLI shim (`scripts/manuscript_assemble_witness.py`)

**Why:** the Workflow (JS) cannot import Python. It needs a CLI that takes a converged `model_out` (JSON on stdin) + chapter coordinates and writes the witness JSON via the EXISTING pure assembler — so the artifact is byte-identical to the API path's.

**Files:** Create `scripts/manuscript_assemble_witness.py`; Test `tests/test_manuscript_assemble_witness_cli.py`.

- [ ] **Step 1: Write the failing test**

```python
import json, subprocess, sys
from pathlib import Path

def test_cli_writes_valid_witness(tmp_path):
    model_out = {"verses": [{"v": 1, "geez": "ወይቤ ፡ ንጉሥ", "column": "f003r-M-L1",
                             "line_start": 1, "uncertain": []}], "transcription_notes": "x"}
    out = tmp_path / "1ki5_witnessGG.json"
    proc = subprocess.run(
        [sys.executable, "scripts/manuscript_assemble_witness.py",
         "--book", "1ki", "--chapter", "5", "--witness", "GG",
         "--source-image", "GAPS/2_Kings/GG-00106/1-Kings/1-Kings_f030v.jpg",
         "--folio", "f030v", "--out", str(out)],
        input=json.dumps(model_out), text=True, capture_output=True,
        stdin=subprocess.DEVNULL if False else None,  # stdin carries model_out
    )
    assert proc.returncode == 0, proc.stderr
    rec = json.loads(out.read_text(encoding="utf-8"))
    assert rec["witness"] == "GG" and rec["book"] == "1ki" and rec["chapter"] == 5
    assert rec["verses"][0]["tokens"]  # tokens computed by _geez_to_tokens
```

- [ ] **Step 2: Run — confirm FAIL** (script missing).
- [ ] **Step 3: Implement** (reuses the existing pure functions — NO new transcription logic)

```python
#!/usr/bin/env python3
"""Assemble + validate + write a witness JSON from a converged model_out (stdin).

Drop-in for the API path's write step: reuses scripts.run_manuscript_transcribe_at_scale.assemble_witness
(pure) so the on-disk artifact matches byte-for-byte. Reads model_out JSON from
stdin; writes content/manuscript/<track>/calibration/<book><chapter>_witness<W>.json.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.run_manuscript_transcribe_at_scale import assemble_witness  # noqa: E402
from scripts.core.manuscript_records import validate_witness  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--book", required=True)
    p.add_argument("--chapter", type=int, required=True)
    p.add_argument("--witness", required=True, choices=["GG", "CAM"])
    p.add_argument("--source-image", action="append", default=[])
    p.add_argument("--folio", action="append", default=[])
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)
    model_out = json.load(sys.stdin)
    track = "kings" if args.book.endswith("ki") else "samuel" if args.book.endswith("sa") else "other"
    out = Path(args.out) if args.out else (
        REPO_ROOT / "content" / "manuscript" / track / "calibration"
        / f"{args.book}{args.chapter}_witness{args.witness}.json")
    rec = assemble_witness(model_out, book=args.book, chapter=args.chapter,
                           witness_sig=args.witness, source_images=args.source_image,
                           folio_sigla=args.folio or args.source_image)
    ok, errs = validate_witness(rec)
    if not ok:
        print(f"INVALID witness: {errs}", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run — confirm PASS.**
- [ ] **Step 5: Commit + 5-leg save** (`feat(manuscript): assemble-witness CLI shim for the agent path`).

### Task 3: The batch Workflow (`.claude/workflows/samkings-dualwitness-batch.js`)

**Why:** this is what the pod's Claude Code invokes. It pipelines over the folio-mapped pending chapters; the Workflow concurrency cap (`min(16, vCPU−2)`) gives the ~7-in-flight parallelism that the N95 cannot. Each agent Reads pre-rendered crop PNGs (rendered by a render step, NOT raw folios — keeps image bytes bounded ≤1568 px per the OOM lesson, though the pod won't OOM).

- [ ] **Step 1: Render step** — a small `scripts/manuscript_render_crops.py` that, given `(track, book, chapter)`, reads the manifest entry and writes the chapter's CAM + GG crops to `/workspace/crops/<book><chapter>/<witness>_<folio>.png` using `manuscript_vision.crop_and_encode(path,(0,0,1e9,1e9),max_edge=MAX_IMAGE_EDGE)` to PNG files (not base64). Test: a unit test asserting it emits one PNG per `source_image`/`view` in the entry and each is ≤1568 px on the long edge.
- [ ] **Step 2: Write `.claude/workflows/samkings-dualwitness-batch.js`** with this structure (the convergence + assemble + collate are shell/CLI calls the agents/stages make; vision is `agent()` reading the crop PNGs):

```javascript
export const meta = {
  name: 'samkings-dualwitness-batch',
  description: 'Dual-witness Ge\'ez draft-at-scale: 2 blind vision passes/witness, converge, collate, per chapter',
  phases: [{ title: 'Transcribe' }, { title: 'Collate' }],
}
// args = { track: 'samuel'|'kings', chapters: [{book, chapter, gg:{folios,images}, cam:{folios,views}}], maxChapters }
const chapters = (args?.chapters || []).slice(0, args?.maxChapters || 999)
const PROTOCOL = /* the _TRANSCRIBE_PROTOCOL text + (q)(u)(v) honesty guards, inlined */ '...'
const SCHEMA = /* TRANSCRIBE_OUTPUT_SCHEMA (verses[].{v,column,line_start,geez,uncertain}, transcription_notes) */ {}

async function blindPass(ch, witness, cropPaths, topology) {
  return agent(
    `${PROTOCOL}\n\n--- ${witness} topology ---\n${topology}\n\n` +
    `Transcribe ${ch.book} ${ch.chapter}, witness ${witness}. The crop PNGs at these paths are the folios in order: ${cropPaths.join(', ')}. Read each with the Read tool. Output every verse you can read.`,
    { label: `${ch.book}${ch.chapter}:${witness}`, phase: 'Transcribe', schema: SCHEMA }
  )
}

const results = await pipeline(
  chapters,
  async (ch) => {                                   // STAGE 1: render + 2 blind passes/witness + converge + write witness JSONs
    // render crops (bash: python scripts/manuscript_render_crops.py ...), then:
    const out = {}
    for (const w of ['GG', 'CAM']) {
      const crops = /* cropPaths for witness w from the render step */ []
      const [a, b] = await Promise.all([blindPass(ch, w, crops, ''), blindPass(ch, w, crops, '')])
      // converge + write via the CLI shims (bash):
      //   echo <converged model_out> | python scripts/manuscript_assemble_witness.py --book .. --chapter .. --witness w --out ..
      out[w] = { converged: /* converge_passes(a,b) result */ null }
    }
    return { ch, out }
  },
  async (r) => {                                    // STAGE 2: flip manifest -> calibrated; run existing collation driver
    // bash: python scripts/run_manuscript_collation_at_scale.py --track <track> --write   (for r.ch only)
    // bash: python -c "from scripts.core.manuscript_collation import collate_base_structured, base_structured_ok; ..."
    return { ch: r.ch, needs_qa: /* any witness diverged */ false, convergence: /* pct */ 0 }
  }
)
return { drafted: results.filter(Boolean), needs_qa: results.filter(r => r && r.needs_qa).map(r => r.ch) }
```

> NOTE: the JS stages shell out to Python via the agent's Bash tool for `manuscript_render_crops.py`, `manuscript_converge.py` (importable as a function via `python -c`), `manuscript_assemble_witness.py`, and `run_manuscript_collation_at_scale.py`. The vision is the `agent()` calls. The convergence result drives `needs_qa`. **Finalize the inlined PROTOCOL/SCHEMA text from `run_manuscript_transcribe_at_scale.py` (`_TRANSCRIBE_PROTOCOL`, `TRANSCRIBE_OUTPUT_SCHEMA`) verbatim during this step.**

- [ ] **Step 3: Validate the workflow loads** — `node --check .claude/workflows/samkings-dualwitness-batch.js` (syntax) + a dry structural review.
- [ ] **Step 4: Commit + 5-leg save** (`feat(workflow): samkings dual-witness batch (agent-path vision)`).

### Task 4: Unit-prove the workflow against a CALIBRATION chapter (N95, free)

**Why:** the 4 Samuel + 6 Kings calibration chapters have known-good CAM+GG images on disk AND immutable reference witness JSONs. Running the workflow on ONE (e.g. **1ki1** — small, both witnesses on disk, already calibrated) proves the agent path end-to-end on the N95 before any pod spend. This is the P1 GO gate.

- [ ] **Step 1:** Run the workflow with `args={track:'kings', chapters:[<1ki1 entry from the manifest>], maxChapters:1}` from THIS Claude Code session (the N95). MAX-1-heavy still applies on the N95 (cap=2) — that's fine for one chapter.
- [ ] **Step 2:** Assert the produced `1ki1_witnessGG.json` / `1ki1_witnessCAM.json` (a) pass `validate_witness`, (b) the geez↔tokens invariant holds, (c) `collate_base_structured` + `base_structured_ok` return OK. Compare convergence + the verse set against the immutable `content/manuscript/kings/calibration/1ki1_*` reference (sanity, not byte-equality — vision is stochastic).
- [ ] **Step 3:** Record the per-chapter token + wall-time cost (the N95 measurement; the pod will be faster/parallel). **CHECKPOINT — pause for user review of the calibration-chapter proof before P2.**
- [ ] **Step 4:** Commit the proof artifacts to `dev/marathon_reviews/` + 5-leg save; update the truth-record.

---

## P2 — Pod bring-up (corrected runbook; meter ON; user-triggered)

Prereqs: P0 green (folio index complete) + P1 green (workflow proven on a calibration chapter) + the user says "feed it" after spotting acceptable pricing.

- [ ] **Step 1: Restart the stopped pod** (or deploy fresh if Terminated / for better pricing). Re-read the **SSH-over-exposed-TCP** connect string from the console (Chrome) — the direct/SCP-capable form `ssh root@<IP> -p <PORT>`; the IP/PORT change on restart.
- [ ] **Step 2: Transfer the lean tarball** (one-time approval — auto-mode off OR a scoped `scp ... root@<pod>` permission rule):
  `scp -P <PORT> -i ~/.ssh/id_ed25519 D:\yhwh-pod-subset.tgz root@<IP>:/workspace/` then on the pod `mkdir -p /workspace/yhwh && tar -xzf /workspace/yhwh-pod-subset.tgz -C /workspace/yhwh`.
- [ ] **Step 3: Install tools** (the base64-over-ssh blob built this session, or scp a `pod-setup.sh`): Node 20 + `npm i -g @anthropic-ai/claude-code` + `pip install pytest PyMuPDF pyyaml pillow`; verify `claude --version`, `python3 -c "import fitz,yaml,PIL"`.
- [ ] **Step 4: Auth Claude Code** — user runs `! claude setup-token` on the N95 (browser), provides the token; set `CLAUDE_CODE_OAUTH_TOKEN` on the pod (env or `claude` config). ⚠ Treat the token as a secret; rotate after the run.
- [ ] **Step 5: Upload GAPS Sam/Kings** — `scp -r` only what the run needs (start with the pilot chapter's folios; full `GAPS/1_Samuel` + `GAPS/2_Kings` ≈ 988 MB before the bulk run). Includes the P0-acquired CAM hires (gitignored → not in the tarball).
- [ ] **Step 6: Smoke** — on the pod: `cd /workspace/yhwh/"YHWH v2.4" && python3 -m pytest tests -k manuscript -q` (expect 152 passed, matches N95, no Windows quirks) + ONE live `agent()` vision pass on a rendered crop (prove Claude Code vision works on the subscription). **Gate to P3.**

---

## P3 — Pilot chapter + measure (pod; meter ON)

- [ ] **Step 1:** Run `samkings-dualwitness-batch` for ONE pilot chapter — recommend **1sa 4** (contiguous with the calibrated 1sa 3; folio-anchored). Render → 4 vision agents → converge → collate → witness JSONs + collation on `/workspace`.
- [ ] **Step 2:** Measure: tokens, wall-time, convergence %, `needs_qa` y/n; derive **$/chapter** (= pod-hours × $0.27 ÷ chapters; vision is subscription = $0). Validate fidelity vs the honesty contract (codepoint-Ethiopic-only; no fabrication; (q)/(u)/(v) respected).
- [ ] **Step 3: Pull back + commit on N95** — `scp` the pilot's witness/collation JSON + manifest delta to the N95; 5-leg commit. **CHECKPOINT — user reviews pilot fidelity + $/chapter → GO/NO-GO for the bounded run.**

---

## P4 — Bounded autonomous run + budget guard (pod; meter ON)

- [ ] **Step 1:** Set the budget guard in `args`: `maxChapters` and/or a pod-hours ceiling derived from the remaining balance (e.g. `floor(balance / $0.27 / measured_hours_per_chapter)`), defaulting conservative. The run STOPS at the guard or when all Sam/Kings drafts complete.
- [ ] **Step 2:** Launch `samkings-dualwitness-batch` over the remaining pending chapters (folio-mapped from P0), ~7 in flight. A run ledger (`/workspace/run_ledger.jsonl`) appends per-chapter tokens/wall-time/convergence/needs_qa.
- [ ] **Step 3:** Pull back in batches — `scp` completed witness/collation JSONs + manifest deltas to the N95; 5-leg commit per batch (`/workspace` is durable network FS, so a crash loses nothing between pulls). Per-batch: codepoint-gate (Ethiopic-only) + `base_structured_ok` before commit.
- [ ] **Step 4:** **Stop the pod** the moment the guard hits or the run completes (frugal lifecycle).
- [ ] **Step 5: Hand-off** — the `needs_qa` chapter list (diverged passes) goes to the Track-1 QA wave (`specs/2026-06-02-tewahedo-reverification-and-triaged-reingest-design.md`). Final report: chapters drafted, $/chapter, convergence rate, `needs_qa` backlog. Update the truth-record + memory `reference_runpod_cloud_budget`.

---

## Cost model + budget guard

$17 ÷ $0.27/hr ≈ **63 pod-hours**. Vision = Max subscription = **$0 API**; the only $ is pod-time, so $/chapter = (wall-time/chapter ÷ chapters-in-flight) × $0.27. The pilot (P3) calibrates the real number; the guard makes "how far does $17 go" a measured, bounded experiment. Quota (Max weekly) is the only non-$ ceiling — and the single resource the pod lane shares with any parallel N95 lane (Esther etc.), see **Parallel-operation protocol** below; the ledger reports any throttle. Stopped pod = $0.00/hr; never leave it running idle.

## Frugal pod lifecycle (standing rule)

Pod runs ONLY during P2 smoke + P3 pilot + P4 run. Stop it (not Terminate) between work — `/workspace` (repo + GAPS + outputs) persists across Stop. Terminate only when the whole run is done and pulled back. P0 + P1 are 100% off-meter on the N95.

---

## Parallel-operation protocol — pod lane ∥ N95 lane (foolproof)

The cloud lane's payoff is that while the pod transcribes Sam/Kings autonomously, **this N95 stays free for another lane** (Esther / P0 / anything). For that to be foolproof the two lanes must not collide on the only three things they could share — git history, files, and the Max quota. By these rules they don't:

1. **Single committer = the N95; the pod NEVER pushes.** The pod writes its outputs ONLY to its durable `/workspace` volume (cluster network FS — survives Stop *and* crash). The N95 is the SOLE writer to GitLab/GitHub `main`: it `scp`-pulls completed chapters in batches and commits them via the 5-leg save. Every commit — pod results, Esther, anything — funnels through one machine, sequentially. So there is **no two-machine push race** against the protected `main`, and **no write credential ever sits on the rented box** (security). *(This promotes the former open-item (c) to a firm design decision — the pod is read-only w.r.t. the repo remotes.)*
2. **The lanes are file-disjoint.** The pod lane writes ONLY Sam/Kings (`content/manuscript/{samuel,kings}/`, `content/translations/geez-tewahedo/{1sa,2sa,1ki,2ki}.py` + their `_apparatus.json`). The Esther lane writes ONLY `est`/Patrologia files. Different files ⇒ even when both land in the same N95 commit sequence there is **nothing to merge-reconcile**. Neither lane touches `epub_working/`, so the **9 KJV editions stay byte-stable** regardless (the standing invariant).
3. **Shared Max quota = the one true shared ceiling, bounded on both sides.** RAM/CPU don't contend (different machines), but BOTH lanes draw inference from the one Max subscription — so the ceiling is *quota*, not hardware. The pod run carries a hard budget/chapter guard (P4 Step 1) and the ledger reports any throttle; the N95 Esther lane is user-paced. If quota binds, the throttling side **backs off and reports — never silently stalls**. Operating assumption: "two lanes, one quota"; the budget guard keeps the pod's share bounded.
4. **Pull-back is idempotent + crash-safe.** A batch pull = `scp` the completed `*_witness*.json` + collation + manifest delta from `/workspace` → commit on the N95. Re-pulling an unchanged chapter is a no-op. `/workspace` is the durable source of truth between pulls, so a pod Stop/crash loses nothing and the N95 can pull whenever it next attends, independent of any in-flight Esther work.
5. **Lifecycle-independent.** Stop/Start/Terminate of the pod has zero effect on N95 work and vice-versa. The N95 can run Esther through the entire pod run, only briefly interrupting itself to pull-and-commit a batch.

**Net:** the pod is a detached, file-disjoint, **no-push** worker whose only coupling to the N95 is (a) a periodic one-way `scp` pull and (b) the shared, budget-bounded Max quota. Both lanes run start-to-finish in parallel with **no manual reconciliation step**.

---

## Self-Review

**Spec coverage:** the design spec's Phase 1 (pod setup) → P2; Phase 2 (the "dualwitness_chapter workflow") → P1+P3+P4 (the spec's gap: it pointed at the API-path drivers; P1 builds the agent-path workflow that the spec actually requires per its own §1/§2 Max-subscription reframe); Phase 3 (measure+decide) → P3+P4 budget guard. Honesty contract (§5) → carried in the PROTOCOL + the convergence gate's (q)/(u)/(v) handling. P0 (folio index) → the existing P0 plan, referenced not duplicated. ✔

**Placeholder scan:** the workflow JS Task 3 intentionally leaves the inlined PROTOCOL/SCHEMA text as `'...'`/`{}` with an explicit instruction to copy `_TRANSCRIBE_PROTOCOL`/`TRANSCRIBE_OUTPUT_SCHEMA` verbatim from `run_manuscript_transcribe_at_scale.py` at build time — these are large existing constants, copied not invented (not a design gap). The vision/ops steps (P2–P4) are procedural by nature (live SSH/console). All Python code steps (converge, assemble shim) are complete + tested. ✔

**Type consistency:** the witness-record shape (`witness/book/chapter/source_images/folio_sigla/verses[{v,column,line_start,geez,tokens,uncertain}]/transcription_notes`) matches `assemble_witness`; `converge_passes` consumes the `model_out` shape (`verses[{v,geez,...}]`) that the vision `agent()` returns under `TRANSCRIBE_OUTPUT_SCHEMA`; `collate_base_structured(gg,cam,book=,chapter=)` + `base_structured_ok(out,gg,cam)` + `fold_skeleton` + `manuscript_records.validate_witness`/`_geez_to_tokens` + `acquire_cudl_master.fetch_master` all match the verified module APIs. ✔

**Open items — RESOLVED during the P1 build (2026-06-02):** (a) import pattern = `from scripts.core import manuscript_converge` (matched an existing test); (b) the render step writes **PNG-on-disk** (`scripts/manuscript_render_crops.py`, ≤1568 px) so agents `Read` files — built + tested; (c) **single-committer / pod-never-pushes is now FIRM** (see the Parallel-operation protocol) — no write credential on the rented box, no two-machine `main` race. **New, resolved:** the Workflow tool's `args` do **not** reliably propagate on this harness, so the batch workflow reads its run-config from a **JSON file via a bootstrap agent** (the controller writes the file before launching) — robust on both the N95 and the pod, and the mechanism the foolproof parallel protocol's pull-back relies on.
