# RunPod Pod Bootstrap Runbook — Sam/Kings cloud-draft (fresh-session aid)

> **Status:** ⛔ DROPPED 2026-06-04 — the VM/cloud-pod approach was tried (RunPod Samuel bulk, 2026-06-04) and **FAILED** (1sa2 ran 2h10m then CAM error; chapters 2–51 instant-failed; 0 usable output), then **dropped by the user** (*"drop all the vm plans, we're doing it all the way we have been"*); the pod was terminated. Sam/Kings continues on the **LOCAL agent-path marathon** (`plans/2026-05-17-kings-manuscript-collation.md`). Kept for history; do NOT resurrect without a new explicit user decision. (Companion banner wording: the spec + plan below.)

> Execution aid for P1 of `specs/2026-06-02-samkings-cloud-draft-at-scale-design.md`. Written 2026-06-02 so a **fresh session** can take the pod from deploy → smoke-test without re-discovering anything. The pipeline (`run_manuscript_*_at_scale.py`) already passes 152 tests locally; this is operations, not code.

## Account state — READY (verified 2026-06-02, this session)
- **RunPod**: logged in via **GitHub OAuth**, balance **$17.00**.
- **SSH public key**: added **account-wide** (Settings → SSH Public Keys) + **verified clean** after a reload. ⚠ It had a stray `❯ ` shell-prompt prefix on first paste (would have broken SSH); fixed to exactly `ssh-ed25519 AAAAC3…gringo.boggy@myyahoo.com` = the N95's `~/.ssh/id_ed25519.pub`. The matching **private key lives only on the N95** (agent-backed, passphrase-protected) — so the N95 is the machine that SSHes INTO the pod.
- **Chosen pod**: **RTX A5000 — 24 GB VRAM · 50 GB RAM · 9 vCPU · $0.28/hr** (on-demand). The GPU is wasted (we don't use it) but CPU pods >2 vCPU were all **"Out of capacity"**, and RunPod is GPU-first so the GPU pods are what's actually available. 50 GB RAM ≈ **7 parallel vision agents** (9 vCPU → Workflow cap 7); ~$17 ÷ $0.28 ≈ **60 hrs**.
- **Template**: *Runpod Pytorch 2.8.0* (Ubuntu 24.04 + Python + CUDA — heavy, but has Python ready). **Override = KEEP** (it's not a glitch): 30 GB container + 50 GB volume @ `/workspace` + **TCP port 22 (SSH)** + HTTP 8888 (Jupyter). The TCP 22 is what enables SSH + `scp`/`rsync`.

## Fresh-session sequence

### 1. Deploy — USER clicks (the only $-spend)
`console.runpod.io/deploy` → **GPU** tab → **All** → **RTX A5000** ($0.27, 50 GB RAM, 9 vCPU) → confirm Storage = 30 GB container + 50 GB volume `/workspace` and the override still exposes **TCP 22** → **Deploy Pod**. (The deploy form does NOT persist across sessions — re-staging is ~5 clicks. The SSH key DOES persist, account-wide.)

### 2. Connection string — read from the console
Pods page → the running pod → **Connect** → copy the SSH command. Two forms RunPod gives:
- **Direct** (if the pod has a public IP + the exposed TCP 22): `ssh root@<IP> -p <PORT> -i ~/.ssh/id_ed25519` → **supports `scp`/`rsync`** (needed for the GAPS upload). **Prefer this.**
- **Proxy/basic**: `ssh <podid>-<hash>@ssh.runpod.io -i ~/.ssh/id_ed25519` → terminal only, **no `scp`**.
If only the proxy is available, use `runpodctl send`/`receive` for the GAPS transfer instead of `rsync` (step 5).

### 3. Auth token — USER on the N95
`! claude setup-token` → authorize in the browser → copy the printed token (long-lived, weeks). This is what lets Claude Code run on the pod against the **Max subscription** (no API spend). Keep it for step 4.

### 4. Bootstrap — Claude drives over SSH from the N95
SSH in (`ssh root@<IP> -p <PORT> -i ~/.ssh/id_ed25519`) and run the script below. It installs Node + Claude Code, clones the repo, installs Python deps. **Decide the private-repo clone auth first** (the repo is private on GitLab+GitHub): simplest = a **GitHub fine-grained PAT** (read-only, this repo) in the HTTPS URL; alternative = generate a keypair on the pod and add the pub as a **read-only deploy key** on the GitHub repo. The script assumes a `GH_PAT` env var.

```bash
#!/usr/bin/env bash
set -euo pipefail

# --- inputs (set these before running) ---
: "${CLAUDE_CODE_OAUTH_TOKEN:?set the token from 'claude setup-token' on the N95}"
: "${GH_PAT:?set a GitHub read-only fine-grained PAT for the private repo}"
REPO_URL="https://${GH_PAT}@github.com/gringoboggy/yhwh-bible-platform.git"
WORK=/workspace/yhwh

# --- Node + Claude Code ---
if ! command -v node >/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi
npm install -g @anthropic-ai/claude-code
export CLAUDE_CODE_OAUTH_TOKEN
claude --version

# --- clone (code only; GAPS images come via step 5) ---
git clone --depth 1 "$REPO_URL" "$WORK"
cd "$WORK/YHWH v2.4"

# --- Python deps (pytorch template already has python3 + pip) ---
python3 -m pip install --upgrade pip
[ -f requirements.txt ] && python3 -m pip install -r requirements.txt || true
python3 -m pip install pytest PyMuPDF pyyaml anthropic pillow

# --- sanity ---
python3 -c "import fitz, yaml, anthropic; print('deps OK', fitz.__doc__[:30])"
echo "BOOTSTRAP DONE — repo at $WORK/YHWH v2.4 ; GAPS upload (step 5) is next"
```

### 5. GAPS upload — ~1 GB Sam/Kings images (NOT in git)
From the **N95** (PowerShell/WSL), direct-SSH path:
```
rsync -avz -e "ssh -p <PORT> -i ~/.ssh/id_ed25519" \
  "GAPS/1_Samuel" "GAPS/2_Kings" \
  root@<IP>:"/workspace/yhwh/YHWH v2.4/GAPS/"
```
(no direct SSH → `runpodctl send <dir>` on the N95, `runpodctl receive <code>` on the pod). Only Sam/Kings is needed for this run (~1 GB), not the whole GAPS tree.

### 6. Smoke test — prove the service before the real run
On the pod (Linux — no `PYTHONUTF8`/`--basetemp` Windows quirks needed):
```
cd "/workspace/yhwh/YHWH v2.4"
python3 -m pytest tests -k manuscript -q          # expect 152 passed (matches N95)
```
Then **one folio-vision call** end-to-end (render a CAM/GG crop + a single Opus vision pass on it) timed for **tokens + wall-time → $/folio**. Green + sane cost ⇒ green-light the real Sam/Kings run (P0 folio-mapping or the at-scale drivers, per the program plans).

### 7. Cost guard + teardown
- **STOP** the pod (don't TERMINATE) when not actively working — per-second billing; stopped cost ≈ **$0.014/hr** (just the volume). TERMINATE erases `/workspace` (the repo + the GAPS upload) → avoid.
- Watch the balance; the run has a budget guard in the plan (P2/P3). $17 ≈ 60 active hours.

## Open items to settle live (fresh session)
1. **Private-repo clone auth** on the pod — GitHub PAT (quickest) vs pod deploy key. Pick one before step 4.
2. **Direct SSH availability** — confirm this A5000 pod gets a public IP + TCP 22 (for `rsync`); else `runpodctl` for GAPS.
3. **First-SSH check** — the `❯` key bug is fixed + verified, but confirm `ssh` actually authenticates on the first connect.
4. **Template weight** — the Pytorch-CUDA image is ~10 GB; if the 30 GB container feels tight, a plain `runpod/base` Ubuntu template is lighter (needs `apt install python3-pip`).

## Related
Spec `specs/2026-06-02-samkings-cloud-draft-at-scale-design.md` · P0 plan `plans/2026-06-02-samkings-folio-index-p0-plan.md` · memory `reference_runpod_cloud_budget`.
