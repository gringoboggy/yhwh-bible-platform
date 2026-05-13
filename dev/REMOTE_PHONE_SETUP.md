# Remote Claude Code from your phone — setup guide

**Purpose**: drive Claude Code from your phone (over cellular / café wifi /
anywhere) with the same file access as your desktop session — same `save.cmd`,
same `pytest`, same `git push`, same everything.

**Architecture**: phone (terminal app) → Tailscale (private network) →
Windows desktop (OpenSSH Server) → Claude Code CLI.

**Time**: ~15-20 minutes the first time. After that, opening Claude from
your phone is two taps.

---

## Why this approach (and not the alternatives)

| Option | Can edit YHWH v2.4 files? | Persistent session? | Cost | Verdict |
|---|---|---|---|---|
| **SSH + Tailscale → desktop Claude Code** | ✅ yes | ✅ same shell | free | **Recommended — full parity with desktop** |
| claude.ai/code in mobile browser | ❌ no (cloud-side) | ✅ via web | free / Pro / Max | Useful for chat about the repo, not for shipping |
| Anthropic mobile app (claude.ai) | ❌ no | n/a | free / Pro / Max | Chat only, no Claude Code |
| ngrok / Cloudflare Tunnel + SSH | ✅ yes | ✅ same shell | free tier OK | Works, but Tailscale is easier to maintain |

The desktop machine has the working tree, the test suite, the `.git`, and
the pre-commit hook. Anything that doesn't see those files can't actually
ship work — only describe it. SSH preserves full parity.

---

## Prerequisites

- Windows 10 build 1809+ or Windows 11 (we're on Windows 11 Pro per
  `dev/CLAUDE_PROJECT_RULES.md` § 0). OpenSSH Server is built-in;
  no download.
- A phone (iOS or Android).
- A Tailscale account (free tier covers 100 devices — way more than enough).
- An Anthropic API key OR Claude.ai Pro/Max subscription configured on
  the desktop's `claude` CLI (already done; you've been shipping ships
  all session).

---

## Step 1 — Enable OpenSSH Server on Windows

```powershell
# Run from an ELEVATED PowerShell (right-click → Run as administrator).
# Otherwise the Add-WindowsCapability cmdlet fails silently.

# 1. Install the OpenSSH Server feature
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 2. Start the service and set it to auto-start on boot
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

# 3. (Already done by the installer, but confirm) — firewall rule
Get-NetFirewallRule -Name *ssh*
# You should see "OpenSSH-Server-In-TCP" with Enabled=True
```

Default PowerShell session for SSH connections: **PowerShell 5.1**
(same as the harness Claude Code uses, per the PowerShell tool docs).
To force PowerShell 7 (if installed):

```powershell
# Only if you've installed PowerShell 7 (pwsh.exe) separately
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell `
    -Value "C:\Program Files\PowerShell\7\pwsh.exe" -PropertyType String -Force
```

---

## Step 2 — Install Tailscale on the Windows desktop

1. Download from https://tailscale.com/download/windows
2. Run the installer (no admin needed for personal install)
3. Sign in with Google / Microsoft / Apple ID — pick one and
   remember it; you'll use the same identity on the phone in Step 3
4. After sign-in, the machine joins your tailnet. Find its
   Tailscale IP:

```powershell
tailscale ip -4
# Returns something like: 100.X.Y.Z
# (Tailscale IPs are always 100.x.y.z in the CGNAT range)
```

5. Also note the hostname Tailscale assigned:

```powershell
tailscale status
# First line: hostname.tail<random>.ts.net
```

Either form works for SSH (IP or hostname). The hostname survives if
your Tailscale IP ever changes; prefer it.

---

## Step 3 — Install Tailscale on your phone

**iOS**: App Store → "Tailscale" → install → open → sign in with the
SAME identity you used in Step 2.

**Android**: Play Store → "Tailscale" → install → sign in same identity.

Once signed in and the toggle is ON, your phone is on the same private
mesh as your desktop. Verify by opening the Tailscale app — both
devices should appear in the device list.

---

## Step 4 — Install a terminal app on the phone

**iOS** (pick one):
- **Termius** — free tier is enough; clean SSH client with key
  management. https://termius.com
- **Blink Shell** — paid (~$20 once or subscription) but superb;
  iSH-class polish. https://blink.sh

**Android**:
- **Termius** — same as iOS, free tier works.
- **JuiceSSH** — long-standing Android favorite, free + paid tier.
  https://juicessh.com

---

## Step 5 — Set up SSH key authentication (security + convenience)

Password auth over SSH on Windows works but is slow per-keystroke and
exposes a brute-forceable password. Key auth is faster and password-less.

### On the phone

1. In your terminal app, generate an SSH key pair:
   - **Termius**: Settings → Keychain → New Key → Ed25519. Give it a
     memorable name like "phone-to-desktop"
   - **Blink Shell**: `config` command → SSH Keys → New Key → Ed25519
   - **JuiceSSH**: ⋮ menu → Manage Identities → ⋮ → New → Generate
     Key Pair → ED25519

2. Copy the **public key** (starts with `ssh-ed25519 AAAA...`) to your
   clipboard. The phone app gives you an "Export public key" or
   "Share" option.

3. Transfer the public key to your desktop. Easiest way: email it to
   yourself, or paste it into a private note in any cloud-synced
   notes app.

### On the desktop

```powershell
# 1. Make sure the authorized_keys file exists
New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" -Force
$keyfile = "$env:USERPROFILE\.ssh\authorized_keys"
if (-not (Test-Path $keyfile)) { New-Item -ItemType File -Path $keyfile }

# 2. Append your phone's public key to it (paste the key as the string)
Add-Content -Path $keyfile -Value "ssh-ed25519 AAAA...your_full_pub_key... phone-to-desktop"

# 3. Lock down permissions so sshd accepts the file
#    (Windows is picky about this; if you skip it, SSH silently rejects the key)
icacls $keyfile /inheritance:r /grant:r "${env:USERNAME}:F"
```

### Test from the phone

```bash
ssh bogda@<your-windows-tailscale-hostname>
# (replace <your-windows-tailscale-hostname> with the .ts.net hostname
#  from Step 2; example: lazarus.tail12345.ts.net)
```

If it logs you in without asking for a password, you're set. If it
falls back to a password prompt, the `authorized_keys` permissions
are wrong — re-run the `icacls` line.

---

## Step 6 — Cd into the project and launch Claude

In your phone SSH session:

```powershell
cd "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4"
claude
```

That's it. You're now in a Claude Code session with the same file
access, the same tests, the same `save.cmd`, the same `git push` as
your desktop. Per `dev/CLAUDE_PROJECT_RULES.md` § 0, Claude will read
the bootstrap triad (rules + SESSION_STATE + PLAN) and orient before
responding.

### First-message tip

Phone keyboards are slow. Start a session with a short message like
"continue" — Claude will read state and pick up where you left off,
honoring the χ-cluster execution sequence + the most-logical-path
discipline.

---

## Optional polish

### Persist the session across SSH drops

Cellular networks drop SSH connections randomly. Wrap Claude in
`tmux` so the session survives:

```powershell
# Install scoop if you don't have it
iwr -useb get.scoop.sh | iex

# Install tmux (via WSL or — easier on Windows — install Windows Terminal +
# use the SSH built-in; tmux on native Windows is painful)
```

**Easier alternative**: just reconnect. Claude Code's conversation
state lives in `~/.claude/projects/` and survives shell restarts; the
next `claude` invocation can resume via `/resume`.

### Tailscale ACL (multi-device hardening)

If you ever share your tailnet with someone else, lock SSH access
down to your own devices only:

1. Go to https://login.tailscale.com/admin/acls
2. Edit your ACL JSON to add (replace `your-email@example.com`):

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["your-email@example.com"],
      "dst": ["your-email@example.com:22"]
    }
  ]
}
```

This restricts port 22 (SSH) to your own devices only. Free-tier
default ACL is already permissive within your own account, so this is
only needed if you join shared tailnets.

### Magic DNS (cleaner hostnames)

Tailscale Magic DNS gives your desktop a short hostname like
`lazarus` instead of `lazarus.tail12345.ts.net`. Enable at
https://login.tailscale.com/admin/dns — once on, SSH becomes
`ssh bogda@lazarus`.

---

## Troubleshooting

**SSH connects but `claude` is "not recognized as a command"**
The Claude Code CLI was installed for your *user* but not on the
system PATH. Either:
- Add it to PATH manually: `[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\bogda\AppData\Local\Programs\Claude\bin", "User")`
- Or just invoke it by full path: `& "$env:LOCALAPPDATA\Programs\Claude\bin\claude.exe"`

**SSH connection succeeds but the prompt is `$` not PowerShell**
Default shell is set to something other than PowerShell. Set it:
```powershell
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell `
    -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -PropertyType String -Force
```

**`save.cmd` works on desktop but not over SSH**
The pre-commit hook (`dev/git-hooks/pre-commit`) needs `python` on
PATH. Per the `dev/CLAUDE_PROJECT_RULES.md` § 0 inventory, Scripts
dir is on User PATH via ω.7 — confirm with `(Get-Command python).Source`.
If empty, the SSH session inherited a stripped PATH; add Python
to system PATH instead of user PATH.

**Pytest hangs after a few seconds**
PYTHONUTF8 env var isn't set in the SSH session. Per
`memory/feedback_pythonutf8.md`, run with `$env:PYTHONUTF8="1"; python -m pytest`
or persist via `[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")`
(then re-SSH).

**Tailscale shows the device offline despite the toggle being ON**
Force a relog: in the Tailscale app, sign out and sign back in. On
Windows, run `tailscale up --force-reauth`.

---

## Daily use, post-setup

1. Unlock phone → open terminal app
2. Saved host → tap to connect (key auth is silent)
3. `cd "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4"`
4. `claude`
5. Type your message; ship as normal

Same `save.cmd` semantics, same `dev/IN_FLIGHT.md` continuity, same
everything. Phone is just a terminal.

---

## Security notes

- Tailscale is end-to-end encrypted (WireGuard); no traffic leaks to
  the public internet.
- The Tailscale IP (100.x.y.z) is *not* internet-reachable. Even if
  the IP leaked, no one outside your tailnet can connect.
- Tailscale auth uses your existing identity provider's MFA — if your
  Google/Microsoft/Apple account has 2FA on, your tailnet does too.
- The phone's SSH private key is stored in iOS Keychain / Android
  Keystore (hardware-backed on modern devices) — losing the phone
  doesn't expose it; the unlock screen lock guards it.
- If you lose the phone: revoke the device in the Tailscale admin
  console *and* remove its public key from `~/.ssh/authorized_keys`
  on the desktop. Both are one-line ops.

---

## Related references

- Save semantics: `./save.cmd "<message>"` per
  `dev/CLAUDE_PROJECT_RULES.md` § 4 (git add -A + commit locally;
  push fails until a new remote is configured).
- Bootstrap triad: `dev/CLAUDE_PROJECT_RULES.md`, `dev/SESSION_STATE.md`,
  `dev/PLAN_2026-05-09.md` (every fresh Claude session reads these
  first; phone sessions are no different).
