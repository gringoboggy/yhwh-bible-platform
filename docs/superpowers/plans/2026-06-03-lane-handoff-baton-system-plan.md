# Lane-Handoff Baton System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** IN PROGRESS — building 2026-06-03 (Windows builds the baton; Mac on the website). 6 TDD tasks. Spec: `specs/2026-06-03-lane-handoff-baton-system-design.md`.

**Goal:** A turn-based "baton" handoff so the Windows (N95) and Mac (iMac) Claude lanes pass work to each other over git with no manual relay, nothing stranded, and a shared task board.

**Architecture:** A committed baton file (`dev/LANE_HANDOFF.md`) names the holder (= active worker + sole pusher this turn). A pure-Python core (`scripts/lane_handoff.py`) reads/writes/validates it with no git side effects. Thin slash commands (`/handoff`, `/resume`, `/sync`) orchestrate git around the core, and the SessionStart hook on each machine auto-surfaces an incoming baton. Only the holder pushes → every push is a clean fast-forward.

**Tech Stack:** Python 3 (full interpreter path / `py -3`; `$env:PYTHONUTF8="1"`), pytest with `--basetemp` (memory `reference_pytest_basetemp`), Claude Code slash commands (markdown prompts) + SessionStart hooks (PowerShell on Windows, bash/zsh on Mac), git over SSH (both remotes, memory `reference_ssh_git_remotes`).

**Spec:** `docs/superpowers/specs/2026-06-03-lane-handoff-baton-system-design.md`.

---

### Task 1: Gitignore wiring + lane identity

**Files:**
- Modify: `.gitignore` (un-ignore `.claude/commands/`; ignore the two per-machine lane files)
- Create (per machine, NOT committed): `dev/.lane`

- [ ] **Step 1: Inspect the current `.claude` ignore block.**

Run: `rg -n "\.claude|^dev/\.lane" .gitignore`
Expected: the `.claude/*` ignore with negations for `settings.json` + `workflows/` (no `commands/` negation yet; no `.lane` rule).

- [ ] **Step 2: Add the negation + lane-file ignores.** Edit `.gitignore`: directly after the existing `!.claude/workflows/` line add:

```gitignore
!.claude/commands/
```

And in the `dev/` ignore section (or at the end of the file) add:

```gitignore
# Per-machine lane identity for the handoff baton (NOT committed — each box sets its own)
dev/.lane
dev/.lane_seen
```

- [ ] **Step 3: Create this machine's lane file.**

Run (Windows): `Set-Content -NoNewline dev/.lane 'windows'`
(On the Mac the equivalent is `printf mac > dev/.lane`.)

- [ ] **Step 4: Verify it is ignored (not staged).**

Run: `git status -s dev/.lane`
Expected: **no output** (ignored). And `git check-ignore dev/.lane` prints `dev/.lane`.

- [ ] **Step 5: Commit the gitignore change.**

```bash
git add .gitignore
git commit -m "lane-handoff: un-ignore .claude/commands/ + ignore per-machine dev/.lane[_seen]"
```

---

### Task 2: Deterministic core — `scripts/lane_handoff.py` (TDD)

**Files:**
- Create: `scripts/lane_handoff.py`
- Test: `tests/test_lane_handoff.py`

The core is pure (functions take an explicit `repo` path; no git). The CLI wires defaults.

- [ ] **Step 1: Write the failing tests** — `tests/test_lane_handoff.py`

```python
"""Lane-handoff baton core — pure file logic, no git side effects."""
from pathlib import Path

import pytest

from scripts import lane_handoff as lh

INIT = (
    "---\n"
    "holder: windows\n"
    "from: windows\n"
    "turn: 0\n"
    "updated: 2026-06-03T00:00:00Z\n"
    "status: working\n"
    "---\n\n"
    "## Done\n- bootstrap\n\n## Next\n- start\n\n## Watch-outs\n- none\n"
)


def _repo(tmp_path: Path, lane: str = "windows") -> Path:
    (tmp_path / "dev").mkdir()
    (tmp_path / "dev" / "LANE_HANDOFF.md").write_text(INIT, encoding="utf-8")
    (tmp_path / "dev" / ".lane").write_text(lane, encoding="utf-8")
    return tmp_path


def test_parse_roundtrip():
    header, body = lh.parse(INIT)
    assert header["holder"] == "windows"
    assert header["turn"] == "0"
    assert "Done" in body
    # render -> parse is stable for the header keys
    h2, _ = lh.parse(lh.render(header, body))
    assert h2["holder"] == "windows" and h2["turn"] == "0"


def test_detect_lane_from_file(tmp_path):
    repo = _repo(tmp_path, lane="mac")
    assert lh.detect_lane(repo) == "mac"


def test_handoff_flips_holder_and_bumps_turn(tmp_path):
    repo = _repo(tmp_path, lane="windows")
    rc = lh.do_handoff(repo, to="mac", done="- finished P0 pilot", next="- map 1sa 7-11", watch="- GAPS only")
    assert rc == 0
    header, body = lh.load(repo)
    assert header["holder"] == "mac"
    assert header["from"] == "windows"
    assert header["turn"] == "1"
    assert header["updated"] != "2026-06-03T00:00:00Z"
    assert "map 1sa 7-11" in body


def test_handoff_refuses_non_holder(tmp_path):
    repo = _repo(tmp_path, lane="mac")  # baton says windows; this lane is mac
    rc = lh.do_handoff(repo, to="windows", done="x", next="y")
    assert rc == 1  # refused
    header, _ = lh.load(repo)
    assert header["holder"] == "windows" and header["turn"] == "0"  # unchanged


def test_handoff_force_overrides(tmp_path):
    repo = _repo(tmp_path, lane="mac")
    rc = lh.do_handoff(repo, to="mac", done="x", next="y", force=True)
    assert rc == 0
    assert lh.load(repo)[0]["holder"] == "mac"


def test_incoming_true_when_addressed_and_new(tmp_path, capsys):
    repo = _repo(tmp_path, lane="windows")
    lh.do_handoff(repo, to="windows", done="x", next="y", force=True)  # holder=windows, turn=1
    rc = lh.do_incoming(repo)
    assert rc == 0
    assert "INCOMING HANDOFF" in capsys.readouterr().out


def test_incoming_false_when_already_seen(tmp_path):
    repo = _repo(tmp_path, lane="windows")
    lh.do_handoff(repo, to="windows", done="x", next="y", force=True)
    lh.do_mark_seen(repo)
    assert lh.do_incoming(repo) == 1  # nothing new


def test_incoming_false_when_not_addressed(tmp_path):
    repo = _repo(tmp_path, lane="mac")  # baton holder=windows
    assert lh.do_incoming(repo) == 1
```

- [ ] **Step 2: Run the tests — confirm they FAIL.**

Run: `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_lane_handoff.py -q --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: `ModuleNotFoundError: ... lane_handoff` (or collection error).

- [ ] **Step 3: Implement `scripts/lane_handoff.py`.**

```python
#!/usr/bin/env python3
"""Lane-handoff baton — deterministic core for the Windows<->Mac two-lane git flow.

The committed baton file dev/LANE_HANDOFF.md names the holder (= active worker +
sole pusher this turn). This module reads/writes/validates it with NO git side
effects (the slash commands run git). Spec:
docs/superpowers/specs/2026-06-03-lane-handoff-baton-system-design.md.

CLI:
  status        print holder/turn + whether THIS lane holds the baton
  handoff --to <windows|mac> --done .. --next .. [--watch ..] [--force]
  incoming      exit 0 + banner iff baton is addressed to this lane & turn>last-seen
  mark-seen     record the current turn as seen (called by /resume)

Lane identity: dev/.lane (gitignored) -> 'windows'|'mac'; fallback $YHWH_LANE;
fallback hostname heuristic (default windows).
"""
from __future__ import annotations

import argparse
import datetime
import os
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LANES = ("windows", "mac")


def baton_path(repo: Path = REPO) -> Path:
    return repo / "dev" / "LANE_HANDOFF.md"


def _lane_file(repo: Path = REPO) -> Path:
    return repo / "dev" / ".lane"


def _seen_file(repo: Path = REPO) -> Path:
    return repo / "dev" / ".lane_seen"


def detect_lane(repo: Path = REPO) -> str:
    f = _lane_file(repo)
    if f.exists():
        v = f.read_text(encoding="utf-8").strip().lower()
        if v in LANES:
            return v
    env = os.environ.get("YHWH_LANE", "").strip().lower()
    if env in LANES:
        return env
    host = socket.gethostname().lower()
    if "mac" in host or "imac" in host or host.endswith(".local"):
        return "mac"
    return "windows"


def parse(text: str) -> tuple[dict, str]:
    """Split `---\\n<frontmatter>\\n---\\n<body>` -> (header dict, body str)."""
    if not text.startswith("---"):
        raise ValueError("LANE_HANDOFF.md missing YAML frontmatter")
    _, fm, body = text.split("---", 2)
    header: dict[str, str] = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip()] = v.strip()
    return header, body.lstrip("\n")


def render(header: dict, body: str) -> str:
    order = ["holder", "from", "turn", "updated", "status"]
    keys = order + [k for k in header if k not in order]
    fm = "\n".join(f"{k}: {header[k]}" for k in keys if k in header)
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def load(repo: Path = REPO) -> tuple[dict, str]:
    return parse(baton_path(repo).read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def do_handoff(repo: Path, *, to: str, done: str = "", next: str = "",
               watch: str = "", force: bool = False) -> int:
    header, _ = load(repo)
    lane = detect_lane(repo)
    if header.get("holder") != lane and not force:
        print(f"REFUSED: this lane is '{lane}' but the baton is held by "
              f"'{header.get('holder')}'. Use --force only if the other lane is idle.",
              file=sys.stderr)
        return 1
    if to not in LANES:
        print(f"--to must be one of {LANES}", file=sys.stderr)
        return 2
    try:
        turn = int(header.get("turn", "0")) + 1
    except ValueError:
        turn = 1
    header.update({"holder": to, "from": lane, "turn": str(turn),
                   "updated": _now(), "status": "handing-off"})
    body = (
        f"## Done (turn {turn - 1}, {lane} -> {to})\n{done or '- (none recorded)'}\n\n"
        f"## Next (turn {turn}, {to} picks up)\n{next or '- (see truth-record)'}\n\n"
        f"## Watch-outs\n{watch or '- (none)'}\n"
    )
    baton_path(repo).write_text(render(header, body), encoding="utf-8")
    print(f"baton {lane} -> {to} (turn {turn}). Commit + push both remotes next.")
    return 0


def do_incoming(repo: Path = REPO) -> int:
    header, _ = load(repo)
    lane = detect_lane(repo)
    if header.get("holder") != lane:
        return 1
    try:
        turn = int(header.get("turn", "0"))
    except ValueError:
        turn = 0
    last = 0
    sf = _seen_file(repo)
    if sf.exists():
        try:
            last = int(sf.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            last = 0
    if turn <= last:
        return 1
    print(f"⮕ INCOMING HANDOFF from {header.get('from')} (turn {turn}) "
          f"-- run /resume to pull + combine.")
    return 0


def do_mark_seen(repo: Path = REPO) -> int:
    header, _ = load(repo)
    _seen_file(repo).write_text(str(header.get("turn", "0")), encoding="utf-8")
    return 0


def do_status(repo: Path = REPO) -> int:
    header, _ = load(repo)
    lane = detect_lane(repo)
    print(f"lane={lane} holder={header.get('holder')} turn={header.get('turn')} "
          f"from={header.get('from')} updated={header.get('updated')} "
          f"status={header.get('status')}")
    print("YOU HOLD THE BATON" if header.get("holder") == lane
          else f"baton is with {header.get('holder')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Lane-handoff baton core")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    h = sub.add_parser("handoff")
    h.add_argument("--to", required=True)
    h.add_argument("--done", default="")
    h.add_argument("--next", default="")
    h.add_argument("--watch", default="")
    h.add_argument("--force", action="store_true")
    sub.add_parser("incoming")
    sub.add_parser("mark-seen")
    args = p.parse_args(argv)
    if args.cmd == "status":
        return do_status()
    if args.cmd == "handoff":
        return do_handoff(REPO, to=args.to, done=args.done, next=args.next,
                          watch=args.watch, force=args.force)
    if args.cmd == "incoming":
        return do_incoming()
    if args.cmd == "mark-seen":
        return do_mark_seen()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests — confirm they PASS.**

Run: `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_lane_handoff.py -q --basetemp="C:\Users\bogda\AppData\Local\Temp\yhwh-pytest\bt"`
Expected: `8 passed`.

- [ ] **Step 5: Type + lint check** (the repo gates on these at commit).

Run: `py -3 scripts/audit_types.py` (mypy) and `py -3 -m ruff format scripts/lane_handoff.py tests/test_lane_handoff.py`
Expected: mypy clean; ruff reformats if needed.

- [ ] **Step 6: Commit.**

```bash
git add scripts/lane_handoff.py tests/test_lane_handoff.py
git commit -m "lane-handoff: deterministic baton core (parse/handoff/incoming) + tests"
```

---

### Task 3: Initialize the baton file `dev/LANE_HANDOFF.md`

**Files:**
- Create: `dev/LANE_HANDOFF.md`

- [ ] **Step 1: Create the initial baton** (Windows currently active → holder=windows, turn=0).

```markdown
---
holder: windows
from: windows
turn: 0
updated: 2026-06-03T00:00:00Z
status: working
---
## Done (init)
- Baton system created. Windows holds the baton (active lane).

## Next (windows)
- Continue P0 Sam/Kings folio-mapping.

## Watch-outs
- Only the holder pushes + edits SESSION_STATE/IN_FLIGHT/CHANGELOG this turn.
- Mac sets `dev/.lane` to `mac` (gitignored) before its first /resume.
```

- [ ] **Step 2: Verify the core reads it.**

Run: `py -3 scripts/lane_handoff.py status`
Expected: `lane=windows holder=windows turn=0 ...` then `YOU HOLD THE BATON`.

- [ ] **Step 3: Commit.**

```bash
git add dev/LANE_HANDOFF.md
git commit -m "lane-handoff: initialize baton file (windows holds, turn 0)"
```

---

### Task 4: Slash commands `/handoff`, `/resume`, `/sync`

**Files:**
- Create: `.claude/commands/handoff.md`
- Create: `.claude/commands/resume.md`
- Create: `.claude/commands/sync.md`

These are markdown PROMPTS (Claude executes the steps). They travel to Mac via git because Task 1 un-ignored `.claude/commands/`.

- [ ] **Step 1: Create `.claude/commands/handoff.md`.**

```markdown
---
description: Hand the baton to the other lane (write the handoff note, commit, push both remotes)
argument-hint: <to-mac|to-windows> [free-text note]
---
You are handing off the work baton to the other Claude lane. Arguments: `$ARGUMENTS`
(first token = `to-mac` or `to-windows`; the rest = an optional free-text note).

Do these steps in order, stopping if any fails:

1. Reconcile the truth-record for what THIS turn accomplished: update `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` (and `dev/CHANGELOG.md` if a coherent unit shipped) to observed reality. You own these files this turn (baton rule).
2. Decide the target lane from the first argument (`to-mac` -> `mac`, `to-windows` -> `windows`). Summarize what you finished (`--done`) and what the receiver should pick up (`--next`), plus any `--watch` gotchas, drawing on the note and the session.
3. Run: `py -3 scripts/lane_handoff.py handoff --to <target> --done "<done bullets>" --next "<next bullets>" --watch "<watch>"`. If it prints `REFUSED`, STOP and tell the user this lane does not hold the baton (do not `--force` without explicit user say-so).
4. Stage + commit: `git add dev/LANE_HANDOFF.md dev/SESSION_STATE.md dev/IN_FLIGHT.md dev/CHANGELOG.md` (+ any work files), commit with a message `lane-handoff: <lane> -> <target> (turn N) — <one-line>`.
5. Sync + push BOTH remotes: `git fetch origin && git fetch github && git rebase origin/main && git push origin main && git push github main`. Resolve any rebase conflict before pushing.
6. Report: "Baton handed to <target> (turn N). They'll see it at their next session start or on `/resume`." Do NOT keep working on baton-owned files after this — the other lane is now the holder.
```

- [ ] **Step 2: Create `.claude/commands/resume.md`.**

```markdown
---
description: Pick up an incoming baton from the other lane (fetch, combine, read the note)
---
You are checking for and picking up a handoff from the other Claude lane.

1. Fetch both remotes: `git fetch origin && git fetch github`.
2. Check the baton: `py -3 scripts/lane_handoff.py status`.
3. If it prints `baton is with <other>` (NOT this lane): tell the user the baton is still with the other lane and STOP (offer that, if they are certain the other lane is idle, you can `--force`-take it — but only on explicit confirmation).
4. If it prints `YOU HOLD THE BATON`: integrate the incoming work — `git rebase origin/main` (the lanes are file-disjoint + only the holder pushes, so this is a clean fast-forward; resolve any conflict by combining). Then print the `## Done` / `## Next` / `## Watch-outs` sections of `dev/LANE_HANDOFF.md` to the user, and run `py -3 scripts/lane_handoff.py mark-seen` so the session-start banner won't re-fire for this turn.
5. Confirm: "You now hold the baton (turn N). Picking up: <next summary>." Then begin that work.
```

- [ ] **Step 3: Create `.claude/commands/sync.md`.**

```markdown
---
description: Mid-turn durability — push the holder's work without handing off the baton
---
You are syncing this lane's work to the remotes WITHOUT handing off (you keep the baton).

1. Confirm you hold the baton: `py -3 scripts/lane_handoff.py status`. If `baton is with <other>`, STOP — only the holder pushes.
2. Stage + commit any pending work (use a precise message). If the tree is clean, skip.
3. `git fetch origin && git fetch github && git rebase origin/main && git push origin main && git push github main`. Resolve conflicts before pushing.
4. Report what was pushed. The baton stays with this lane.
```

- [ ] **Step 4: Verify the commands are tracked (Task 1's un-ignore worked).**

Run: `git add .claude/commands/ && git status -s .claude/commands/`
Expected: three `A` (added) entries for handoff.md, resume.md, sync.md.

- [ ] **Step 5: Commit.**

```bash
git commit -m "lane-handoff: /handoff /resume /sync slash commands"
```

---

### Task 5: SessionStart auto-check (both machines)

**Files:**
- Read then Modify: `.claude/settings.json` (understand the current SessionStart hook; avoid the shared-settings hazard)
- Modify: `dev/cc-hooks/bootstrap-triad.ps1` (Windows: add the incoming-check)
- Create: `dev/cc-hooks/bootstrap-triad.sh` (Mac: triad print + incoming-check)

**Shared-settings hazard:** `.claude/settings.json` is committed + shared. If its SessionStart hook command is a Windows-only `.ps1`, it breaks on Mac. The fix: each machine points SessionStart at its OS script via the per-machine, gitignored `.claude/settings.local.json`; the committed `.claude/settings.json` keeps only cross-platform hooks.

- [ ] **Step 1: Read the current hook wiring.**

Run: `py -3 -c "import json,sys; d=json.load(open('.claude/settings.json',encoding='utf-8')); print(json.dumps(d.get('hooks',{}).get('SessionStart','<none>'),indent=2))"`
Record whether the SessionStart command is the Windows `bootstrap-triad.ps1`. If it is, plan Step 4 moves it to local settings.

- [ ] **Step 2: Add the incoming-check to the Windows hook.** Append to `dev/cc-hooks/bootstrap-triad.ps1` (after the triad print), guarding so a failure never blocks the session:

```powershell
# --- lane-handoff incoming check (non-fatal) ---
try {
    git fetch origin --quiet 2>$null
    $banner = py -3 scripts/lane_handoff.py incoming 2>$null
    if ($LASTEXITCODE -eq 0 -and $banner) { Write-Output $banner }
} catch { }
```

- [ ] **Step 3: Create the Mac hook `dev/cc-hooks/bootstrap-triad.sh`** (triad pointer + the same incoming-check; executable):

```bash
#!/usr/bin/env bash
# Mac-lane SessionStart bootstrap (mirror of bootstrap-triad.ps1).
set +e
echo "================ YHWH PROJECT BOOTSTRAP (mac lane) ================"
echo "Read the triad: dev/CLAUDE_PROJECT_RULES.md, dev/SESSION_STATE.md, dev/PLAN_2026-05-29-roadmap.md"
echo "=================================================================="
# --- lane-handoff incoming check (non-fatal) ---
git fetch origin --quiet 2>/dev/null
banner="$(python3 scripts/lane_handoff.py incoming 2>/dev/null)"
if [ $? -eq 0 ] && [ -n "$banner" ]; then echo "$banner"; fi
```

- [ ] **Step 4: Resolve the hazard via local settings (documented, applied per machine).** In the plan-execution note for the Mac, instruct it to set its SessionStart command in `.claude/settings.local.json` (gitignored) to run `bootstrap-triad.sh`. If Step 1 found a Windows `.ps1` SessionStart in the SHARED `.claude/settings.json`, move that command into Windows' `.claude/settings.local.json` and remove it from the committed file (so Mac is not handed a `.ps1`). Verify locally: `py -3 -c "import json; json.load(open('.claude/settings.json',encoding='utf-8'))"` parses.

- [ ] **Step 5: Smoke the incoming-check both states.**

Run (no incoming, since Windows already holds + would mark-seen): `py -3 scripts/lane_handoff.py incoming; echo "exit=$LASTEXITCODE"`
Expected: exit 1 when turn already seen / not addressed; exit 0 + the `⮕ INCOMING HANDOFF` banner right after a handoff TO this lane.

- [ ] **Step 6: Commit.**

```bash
git add dev/cc-hooks/bootstrap-triad.ps1 dev/cc-hooks/bootstrap-triad.sh .claude/settings.json
git commit -m "lane-handoff: SessionStart incoming-check (win ps1 + mac sh) + settings hazard fix"
```

---

### Task 6: Index, docs, and end-to-end dry run

**Files:**
- Modify: `docs/superpowers/INDEX.md` (index the spec + this plan — `check_superpowers_coherence` lint requires it)
- Modify: `dev/CLAUDE_PROJECT_RULES.md` (one line pointing to the baton workflow)

- [ ] **Step 1: Index the new docs.** Read `docs/superpowers/INDEX.md`, add entries for the spec (`specs/2026-06-03-lane-handoff-baton-system-design.md`) and this plan under the right sections, and bump any doc-count the file pins.

- [ ] **Step 2: One-line rule pointer.** In `dev/CLAUDE_PROJECT_RULES.md` (near the save/remote section), add: "Two-lane work (Windows+Mac) uses the baton: only the holder pushes + edits truth-records; `/handoff` to pass, `/resume` to pick up. See `docs/superpowers/specs/2026-06-03-lane-handoff-baton-system-design.md`."

- [ ] **Step 3: Run the lint guard locally to confirm coherence passes.**

Run: `py -3 scripts/lint_rules.py` (or the pre-commit). Expected: `check_superpowers_coherence` passes (spec + plan indexed); no new fail.

- [ ] **Step 4: End-to-end dry run on a scratch copy** (proves the round trip without disturbing the live baton). Copy `dev/LANE_HANDOFF.md` + a temp `.lane` into a tmp dir and exercise the core:

```bash
py -3 -c "import shutil,tempfile,os; from pathlib import Path; import scripts.lane_handoff as lh; \
d=Path(tempfile.mkdtemp()); (d/'dev').mkdir(); \
shutil.copy('dev/LANE_HANDOFF.md', d/'dev'/'LANE_HANDOFF.md'); (d/'dev'/'.lane').write_text('windows'); \
print(lh.do_handoff(d,to='mac',done='- x',next='- y')); print(lh.load(d)[0]); \
(d/'dev'/'.lane').write_text('mac'); print('incoming(mac)=',lh.do_incoming(d))"
```
Expected: handoff returns 0; loaded holder=`mac`, turn=`1`; `incoming(mac)= 0` (banner printed).

- [ ] **Step 5: Full affected-suite check + commit.**

Run: `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_lane_handoff.py -q --basetemp="...\bt"`
Then:
```bash
git add docs/superpowers/INDEX.md dev/CLAUDE_PROJECT_RULES.md
git commit -m "lane-handoff: index spec+plan, rules pointer, e2e dry-run verified"
```

- [ ] **Step 6: Hand the baton to Mac** (the system's own first real use, once Mac is set up): `/handoff to-mac "baton system shipped; pull it; set dev/.lane=mac"`.

---

## Self-Review

**Spec coverage:** (1) no manual relay → Task 5 SessionStart incoming-check + Task 4 `/resume`. (2) nothing strands → baton core's holder-only push (Task 2) + `/handoff`/`/sync` push both remotes (Task 4). (3) shared task board → `dev/LANE_HANDOFF.md` Done/Next/Watch-outs (Tasks 2-3). Baton model (holder = sole pusher + truth-record owner) → enforced in `do_handoff` refusal (Task 2) + the command prompts (Task 4). Lane identity, edge cases (refuse-non-holder, force, already-seen) → Task 2 tests. Cross-OS hooks + shared-settings hazard → Task 5. ✔

**Placeholder scan:** no TBD/TODO; all code blocks complete; the `<target>`/`<done bullets>` tokens in the command PROMPTS are intentional substitution slots the executing Claude fills (not code placeholders). ✔

**Type/name consistency:** `parse`/`render`/`load`/`detect_lane`/`do_handoff`/`do_incoming`/`do_mark_seen`/`do_status` are used identically in the core, the CLI `main`, and the tests; the baton header keys (`holder`/`from`/`turn`/`updated`/`status`) match across the file format (Task 3), the core, and the tests. The CLI flag `--next` maps to the `next=` kwarg consistently. ✔

**YAGNI:** no quota-safety, no polling, no auto-merge — all excluded per the spec.
