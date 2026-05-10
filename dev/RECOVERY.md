# Recovery guide

> **Phase tag:** ω.11. Companion to the `scripts/recover.py` CLI.

This document catalogs the "I broke something — how do I fix it?"
paths the YHWH platform's editor users could realistically hit.
Every mutation in the project goes through
`notes_io.atomic_write` + `notes_io.ensure_backup`
(`scripts/lint_rules.py:check_atomic_writes` enforces this), so
nearly every file you might damage has a timestamped `.bak` waiting
in a sibling `.backups/` directory.

The decision tree below maps **symptom → diagnosis → command**.
When in doubt, the most common path is:

    python scripts/recover.py list-backups <path>
    python scripts/recover.py restore <path>

…which restores from the newest backup, after backing up the
current (broken) contents itself so the restore is also reversible.

---

## 1. Common symptoms

### 1.1 `content/notes/<book>.py` parses to an empty list

**Symptom.** Running `pytest` shows a per-book test failing with
"NOTES list is empty"; the matrix shows zero notes for that book;
opening the file shows it's been truncated or has a Python syntax
error.

**Diagnosis.** A hand-edit (or merge conflict resolution, or a
bulk-rename gone wrong) corrupted the literal-tuple data. Because
`notes_io.load_notes` uses `ast.literal_eval`, anything that's not
a clean tuple-of-tuples becomes `None`.

**Recover.**

    python scripts/recover.py list-backups content/notes/<book>.py
    python scripts/recover.py restore content/notes/<book>.py

The latest `.bak` file replaces the broken one. Then:

    pytest tests/test_scripts.py -k "TestPsi"
    python scripts/lint_rules.py

### 1.2 `content/editions.yaml` lost all editions

**Symptom.** `python -c "from scripts.core import config; print(len(config.load_editions()))"`
prints `0`. /matrix shows no editions in the dropdown. /publisher
shows "no editions" message.

**Diagnosis.** The project's custom `_parse_yaml_records` parser
expects a specific format (2-space indent for record markers,
4-space for fields). Tools that re-emit YAML using `yaml.safe_dump`
produce valid YAML that the project parser can't read. The ω.16
edition-snapshots phase shipped a parser-roundtrip safety net to
prevent this; pre-ω.16 mutations could have damaged the file.

**Recover.**

    python scripts/recover.py verify-yaml content/editions.yaml
    # If the parser fails:
    python scripts/recover.py list-backups content/editions.yaml
    python scripts/recover.py restore content/editions.yaml
    # Verify after:
    python scripts/recover.py verify-yaml content/editions.yaml

The `verify-yaml` subcommand runs the file through the project's
custom parser and reports the record count. A clean parse with
≥1 record is the success criterion.

### 1.3 `dev/IN_FLIGHT.md` stuck `active` after a crashed session

**Symptom.** `lint_rules.py` reports
"in-flight task active for X.Yh (stale)". You know there's nothing
in flight — the marker just never got flipped back during a
session that crashed or was force-killed.

**Diagnosis.** The marker is hand-flipped during a session ship.
A crash before the post-ship update leaves it `active`.

**Recover.**

    python scripts/recover.py flip-inflight idle

The CLI prompts for confirmation (type `yes`) and backs up
`IN_FLIGHT.md` before flipping. Pass `--yes` to skip the prompt
in a script.

### 1.4 Build pipeline left a stale `tmp/full_*` directory or lock file

**Symptom.** `python scripts/build_edition.py <id>` complains about
a temp dir that already exists, or `editions/*.epub` mtimes are
ancient even though the corpus changed.

**Diagnosis.** The build pipeline shells out to `build_epub.py`
and creates `tmp/full_<edition>/`; on success it cleans up, on
crash it leaves the dir behind.

**Recover.** No new tool needed — `scripts/cleanup.py` already
covers this:

    python scripts/cleanup.py --dry-run    # preview
    python scripts/cleanup.py              # actually remove

The cleanup script knows about `tmp/`, `epub_working/.backups/`,
`__pycache__`, etc.

### 1.5 Linter false positive blocking a save

**Symptom.** `lint_rules.py` reports a structural drift you've
verified is intentional. You can't ship without the linter clean,
but you don't want to weaken the check across the board.

**Diagnosis.** The linter's structural checks (cross-link
invariant, encoder-order check, etc.) catch *most* drift but
occasionally flag legitimate exceptions. Each check has its own
rationale in `scripts/lint_rules.py`.

**Recover.** This is a documentation-only path today — the
`--ack <check_id> --reason <text>` flag mentioned in the original
ω.11 spec didn't ship in this phase. Workarounds:

1. **Fix the underlying invariant**, even if it means a small
   refactor. The check exists for a reason.
2. **Document the exception in the CHANGELOG** alongside the
   shipping commit so future Claude understands the
   intentional drift.
3. **File a follow-on phase** (e.g. ω.11.1) to add `--ack`
   support to the linter if the need recurs.

Don't bypass the linter without leaving a written note — that's
the failure mode this whole guide is here to prevent.

### 1.6 Snapshot restore reports "would lose edition" before writing

**Symptom.** `api_snapshot_restore` returns
`{"status": "error", "code": "format_validation_failed"}`.

**Diagnosis.** The ω.16 restore path runs a parser-roundtrip
safety check before the actual write. If the rewritten
`editions.yaml` would fail the project's custom parser, the
write is aborted before any damage. This is by design — the
prior generation of restore_snapshot DID damage editions.yaml
via `yaml.safe_dump`, so the safety net was added.

**Recover.** No file damage to undo (write was aborted). Look
at the snapshot's `edition.yaml` for shape mismatches — most
commonly a hand-edited snapshot record contains nested dicts
the project parser doesn't support. Edit the snapshot or
delete + re-create it.

---

## 2. CLI reference

`scripts/recover.py` exposes four subcommands:

### `list-backups <path>`

Lists every `.bak` file matching `<stem>.<TIMESTAMP><suffix>.bak`
in `<path>`'s sibling `.backups/` directory, newest first. Each
line shows the timestamp, file size, and backup filename.

Empty output means there are no backups for that file (and
therefore nothing to restore — the file may never have been
edited via the project's atomic-write helpers).

### `restore <path> [--from <bak-path>]`

Restores `<path>` from a backup. Without `--from`, picks the
newest available. With `--from <path>`, restores from a specific
`.bak` file (must match the target's stem; the CLI rejects
mis-stem mismatches as a safety check).

Before overwriting, the command backs up the current contents to
the same `.backups/` dir, so a botched restore is itself
recoverable. The chosen backup's bytes are read into memory
*before* the rollback-backup is written, guarding against
second-resolution timestamp collisions where the rollback could
otherwise clobber the source.

Output reports the restored path, source backup, and the
rollback-backup path (if any).

### `verify-yaml <path>`

Runs the file through the project's custom `_parse_yaml_records`
parser. Reports `record_count` on success. Use this AFTER any
manual edit to `editions.yaml`, `kinds.yaml`,
`categories.yaml`, etc. to catch format mismatches before they
propagate through the build pipeline.

Standard YAML linters (yamllint) won't catch the kinds of
mismatches this check exists for — the project parser is more
restrictive than the YAML 1.1/1.2 spec.

### `flip-inflight {idle, active} [--yes]`

Flips `dev/IN_FLIGHT.md`'s `<!-- TRACKER-STATE: ... -->` marker.
Without `--yes`, prompts the user to type `yes` to confirm
(destructive: a real in-flight task that's mid-flight should NOT
be flipped to `idle`).

If the marker is already in the target state, the command no-ops
and reports `current_state`.

---

## 3. What this doc is NOT

- **Not a backup strategy.** The project relies on
  `notes_io.ensure_backup`'s in-process `.backups/` per-file
  history (default `max_keep=50`). For longer-horizon recovery,
  use git: `git log -- <path>`, `git checkout <commit> -- <path>`.
- **Not for hardware failure or filesystem corruption.** If the
  filesystem itself is unreliable, the `.backups/` files are no
  more trustworthy than the originals. Restore from a known-good
  external source (git, an off-machine clone, or a manual
  snapshot).
- **Not for accidental commits.** Use git's existing recovery
  patterns (`git reset`, `git revert`, `git reflog`).

---

## 4. Adding new recovery scenarios

When a new failure mode emerges in a session, add an entry to §1
above with:

- **Symptom.** What the operator actually sees.
- **Diagnosis.** What's structurally wrong.
- **Recover.** Concrete commands (preferably wrapping a CLI
  subcommand of `scripts/recover.py`; new scenarios that need
  a new subcommand should add it).

Cross-reference from `dev/SECURITY.md` §7 if the failure mode
involves secrets / env vars / auth.
