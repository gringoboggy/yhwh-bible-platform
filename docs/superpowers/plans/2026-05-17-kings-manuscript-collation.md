# Kings Dual-Manuscript Collation & Render Implementation Plan (τ.6.x.4.c)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task (fresh isolated subagent per transcription, two-stage review after each). Steps use checkbox (`- [ ]`) syntax for tracking. This is a **multi-session marathon** — execute continuously; the manifest is the durable cross-session state of record.

> **⚑⚑ EXECUTION METHOD — RATIFIED 2026-05-26 (user-directed; supersedes the script-path resume in the IN_FLIGHT crash banners AND tunes the agent path. READ THIS FIRST — it changes how every C-step below is run).**
> - **The paid SCRIPT-PATH is OUT OF SCOPE.** `scripts/run_manuscript_{transcribe,review,collation}_at_scale.py` + `scripts/core/manuscript_vision.py` need the optional `anthropic` SDK + a funded `ANTHROPIC_API_KEY` (`requirements.txt` gates it as "the paid corpus-augmentation pass"). There is **no API budget** → do NOT install `anthropic`, do NOT set/spend an API key, do NOT run those at-scale scripts for real. They remain as inert, committed infra (NOT deleted) should a key ever be funded. (Verified 2026-05-26: `anthropic` not installed, `ANTHROPIC_API_KEY` not set.)
> - **Run on the AGENT path** (Claude Max, no per-call cost) — the method that produced the clean 1ki1–4 calibrations. C-2/C-3/C-5/C-6 = isolated `Task` subagents reading image crops via the Read tool (as the per-chapter template below already describes).
> - **Crash fix — root-caused 2026-05-26 from the actual file sizes (GG folios 0.7 MB, CAM hi-res ~10 MB):** the 4 OOM crashes were NOT the source files. They were agents **LANCZOS-upscaling WHOLE folios 4–8×** (→ 30–60 MB buffered per agent for ~20 min) × **3 stacked** ≈ 400k tokens of parent-buffered output → Rust allocator panic. The vision pipeline downsamples anything past ~1568 px, so a whole-folio upscale was **doubly wasteful** — huge bytes the model discards AND tiny effective fidel resolution.
> - **THE FIX — zoom by TIGHT REGION CROP, never a whole-folio upscale.** Pre-crop one column / a few-verse band at high zoom, capped at ≤1568 px on the long edge (the fidel then fills the budget = *sharper* than the old whole-page upscale AND only ~1–3 MB). Write crops to an OS temp dir OUTSIDE the repo (the `git add -A` footgun) and read the small crop into the agent. This reconciles "keep upscaling for accuracy" with "small buffer." CAM hi-res masters are already region-zoomed — read one folio as-is, do not re-upscale.
> - **MAX 1 heavy vision agent at a time** (memory `feedback_concurrent_agent_cap`); fully drain before dispatching the next. Never stack heavy agents.
> - **Auto-commit each step** (`save.cmd "<msg>"`, PowerShell only) the moment its file lands on disk — crash insurance; a crash then loses ≤ 1 step's work.
> - **`/clear` (fresh session) between heavy steps** — this releases the accumulated parent buffer that actually caused the OOM. The controller resumes deterministically from the witness JSON + manifest on disk.
> - **Unit of work = ONE agent-step, NOT a chapter** (user 2026-05-26: "we are not doing chapters at a time"). The hybrid-cadence rule (METHOD NOTE 5) still governs user check-ins on LIST/REGNAL chapters; NARRATIVE chapters still flow, but each *agent step* is its own commit + `/clear` boundary.
> - **CAM hi-res pre-pull — bounded-concurrent accelerator (user-sanctioned 2026-05-27).** While a heavy GG/CAM vision agent runs, the controller MAY pre-pull the NEXT chapter's CAM hi-res CONCURRENTLY as a **low-buffer** task: `scripts/acquire_cudl_master.py <view> <output>` (download IIIF tiles → stitch → save to `GAPS/2_Kings/Cambridge-Add-1570-hires/`), then QC **programmatically** (dimensions + file size only) — **NEVER read full-res tiles into agent/controller context** (those bytes are the image-buffer the OOMs were made of; on disk they cost nothing). Pre-stages C-4, removing its serial wait. **RAM-gated:** sample free RAM during the first concurrent run; validated if free RAM holds > ~3 GB, else fall back to SEQUENTIAL (between heavy steps). This is the ONE sanctioned exception to "image work stays sequential," safe ONLY because the bytes land on disk, never in a context buffer.

**Goal:** Produce the reconstructed Ge'ez text + per-verse two-witness critical apparatus for **all of 1 Kings (22 ch) + 2 Kings (25 ch) = 47 chapters**, by blind dual-witness vision transcription (GG-00106 + Cambridge Add. 1570) collated through the **already-shipped Phase-2 tool**, then rendered into `geez-tewahedo/1ki.py` + `2ki.py` — feeding the standalone Ge'ez Bible and filling the parallel-PDF Ge'ez Kings gap.

**Architecture:** Kings **reuses Phase-2/3 verbatim** (design spec §3 line 78, §6 line 231). The collation *engine* (`scripts/core/manuscript_collation.py`, `manuscript_records.py`, `manuscript_reconcile.py`) is already book-agnostic. Only the manifest loader + at-scale driver are Samuel-hardcoded; Stage 0 makes them track-parameterized **additively** (samuel = default → byte-identical back-compat, rules §7.2). Stage 1 runs the proven Samuel per-chapter blind-dual-witness procedure VERBATIM across the 47-chapter queue. Stage 2 renders via the τ.7.x conventions + the design-spec §6 Phase-3 contract.

**Tech Stack:** Vision transcription (subagent reading JPGs via Read); hand-authored immutable JSON evidence (`content/manuscript/kings/calibration/`); the shipped Phase-2 Python tool; CUDL IIIF image acquisition (`curl` + Pillow tiling per memory `cudl-iiif-access`); `pytest` pins mirroring the τ.7.x convention; local git commit only (no push — remote deleted; no zip).

**Spec:** `docs/superpowers/specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md` (covers Kings explicitly). **Per-chapter template:** `docs/superpowers/plans/2026-05-16-samuel-calibration-gate.md` + `2026-05-16-samuel-widened-calibration.md` (reuse task structure, honesty contract, numeral rule, verification commands VERBATIM — only book/chapter/images change). **Phase-2 tool as shipped:** `docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool-v2.md`.

**Decision inheritance (NO fresh user-GO gate):** The diplomatic-parallel model + base=CAM + the distinct-recension finding were **user-ratified 2026-05-17 (GO)** for this exact manuscript family (GG-00106 + CAM Add. 1570). Samuel Phase-1 was the one-time method-proving gate; the design spec says Kings reuses Phases 2–3, **not** Phase 1. Therefore Kings does **not** re-run a calibration gate. **Safety stop (bi-directional, per the widened-calibration decision rule):** 1 Kings 1 is transcribed/collated first as an implicit pattern-confirmation. If 1 Kings 1 **contradicts** the ratified pattern (≈unity W↔W agreement ≥ 90% on a clean chapter, OR base empirically flips to GG on an undamaged folio, OR semantic-pass < 95%), **STOP the marathon and surface to the user** — do not assume the model. If 1 Kings 1 matches the pattern, proceed through the full queue continuously without further check-ins.

**Environment invariants (this Windows box — memories `python-interpreter-path`, `feedback_pythonutf8`, `reference_save`):**
- Python: `& "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe"` (bare `python`/`py -3` is a broken Store stub). Always prefix `$env:PYTHONUTF8="1"`.
- Commit via `./save.cmd "<msg>"` from the project root (resolves its own interpreter + runs the `lint_rules.py` pre-commit hook). `save.cmd` from PowerShell surfaces git CRLF warnings as a `NativeCommandError` even on success — look for `[main <hash>]` / "Saved locally", not the stderr noise.
- `subprocess.run(...)` in any test/script must pass `stdin=subprocess.DEVNULL` (memory `w_w1_subprocess_devnull`).
- Repo root for git + relative paths: `C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4`. **GAPS images live INSIDE the repo (since 2026-05-20 audit) at `<repo>/GAPS/2_Kings/…`** — gitignored (the 1 GB of binary images stays out of git history but stays with the working tree for backup-self-containment). Reference relative paths from the repo root (`GAPS/2_Kings/...` resolves directly when cwd=repo root).

---

## Source inventory (verified on disk 2026-05-17)

| Witness | Path | Contents |
|---|---|---|
| **GG 1 Kings** | `GAPS/2_Kings/GG-00106/1-Kings/` | `1-Kings_f028v.jpg` … `1-Kings_f040v.jpg` (~25 full-page ~5MP) |
| **GG 2 Kings** | `GAPS/2_Kings/GG-00106/2-Kings/` | `2-Kings_f040v.jpg` … `2-Kings_f053r.jpg` (~26 full-page; `f040v` is the shared 1Ki→2Ki boundary folio) |
| **CAM low-res** | `GAPS/2_Kings/Cambridge-Add-1570/` | `Kings_f126r.jpg` … `Kings_f146v.jpg` (~42 text-crops ~1.6MP — orientation/locating aid only; NOT the transcription source) |
| **CAM hi-res** | `GAPS/2_Kings/Cambridge-Add-1570-hires/` | **DOES NOT EXIST YET** — pulled per-chapter from CUDL IIIF (memory `cudl-iiif-access`); the CAM transcription source |

CUDL IIIF (memory `cudl-iiif-access`): manifest `https://cudl.lib.cam.ac.uk/iiif/MS-ADD-01570`; image id pattern `https://images.lib.cam.ac.uk/iiif/MS-ADD-01570-000-{view:05d}.jp2`; single delivery caps 1503×2000 so region-tile the ~80MP master in ≤1900px tiles `/{x},{y},{w},{h}/full/0/default.jpg` + stitch with Pillow; `User-Agent: Mozilla/5.0`; write temp JSON/tiles to a Windows path. **The ToC `structures` MISLABEL the Ethiopic Reigns books — locate every chapter by VISION of its known narrative, never by ToC label.** Anchor: 1 Sam 1 = view 215 = f106r; Samuel runs forward; Kings (3–4 Reigns) follows 2 Samuel. The CAM low-res `Kings_f126r…f146v` crops give the approximate Kings folio band — confirm each chapter's folio by vision against the GG narrative. Save stitched hi-res as `GAPS/2_Kings/Cambridge-Add-1570-hires/MS-ADD-01570_f{NNN}_{ref}_hires.jpg`. Images **CC BY-NC, credit "Cambridge University Library"** — recorded in `_source.yaml` provenance (Stage 2).

## Immutable witness schema — the SHIPPED contract (`scripts/core/manuscript_records.validate_witness`)

This is the **authoritative** schema (supersedes the Phase-1 plan's prototype). The GG/CAM evidence files MUST validate against it.

- **Top-level keys EXACTLY:** `{witness, book, chapter, source_images, folio_sigla, verses, transcription_notes}` — no more, no fewer.
- `witness` ∈ `{"GG","CAM"}`; `book` ∈ `{"1ki","2ki"}`; `chapter` = int.
- **Per-verse keys EXACTLY:** `{v, column, line_start, geez, tokens, uncertain}`.
- **`geez↔tokens` invariant (HARD):** `tokens` must equal `_geez_to_tokens(geez)`: replace each of `፡` (U+1361) `።` (U+1362) `፣` (U+1363) `✣` (U+2723) with an ASCII space; insert a space on each side of every Ethiopic numeral glyph `፩`–`፼` (U+1369–U+137C); `str.split()`; drop empties.
- **Honesty bijection (HARD):** the sentinel `ILLEGIBLE = "⟦illegible⟧"`. Every `⟦illegible⟧` element in `tokens` must have **exactly one** matching `uncertain[]` entry with `marker == "illegible"`.
- `uncertain[]`: each `{token_index:int (0-based, in range of tokens), marker, note}`; `marker` ∈ `{"uncertain","damaged","illegible"}`.
- `verses[].v` contiguous `1..N` from 1.

`{ref}` naming = `f"{book}{chapter}"` → `1ki1`, `1ki22`, `2ki1`, `2ki25`. Witness files: `content/manuscript/kings/calibration/{ref}_witnessGG.json` + `{ref}_witnessCAM_hires.json`. These are **immutable evidence** — never overwritten once reviewed-clean.

---

# STAGE 0 — Phase-2 infrastructure reuse (additive track parameterization)

Goal: make the manifest loader + at-scale driver work for `track ∈ {samuel, kings}` with **samuel as default so every existing Samuel call + the 29-test suite stays byte-identical** (rules §7.2 additive, no-op when unset). Seed the Kings manifest.

### Task 0.1: Track-parameterize the manifest loader

**Files:**
- Modify: `scripts/core/manuscript_manifest.py`
- Test: `tests/test_manuscript_kings.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_manuscript_kings.py
import importlib
from scripts.core import manuscript_manifest as mm


def test_samuel_default_back_compat():
    mm.load_manifest.cache_clear()
    man = mm.load_manifest()                      # no arg → samuel (unchanged)
    assert "1sa" in man and "2sa" in man
    assert man["1sa"][1]["status"] == "calibrated"


def test_kings_track_loads_47_pending():
    mm.load_manifest.cache_clear()
    man = mm.load_manifest(track="kings")
    assert set(man) == {"1ki", "2ki"}
    assert len(man["1ki"]) == 22 and len(man["2ki"]) == 25
    assert all(man["1ki"][c]["status"] == "pending" for c in range(1, 23))
    assert all(man["2ki"][c]["status"] == "pending" for c in range(1, 26))


def test_chapter_entry_track_aware():
    mm.load_manifest.cache_clear()
    man = mm.load_manifest(track="kings")
    e = mm.chapter_entry(man, "1ki", 1)
    assert e["status"] == "pending"
    assert e["GG"] == {"folios": [], "source_images": []}
    assert e["CAM"] == {"folios": [], "views": []}
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4"; $env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest tests/test_manuscript_kings.py -q`
Expected: FAIL — `load_manifest()` takes no `track` kwarg / kings manifest missing.

- [ ] **Step 3: Implement track parameterization**

Replace the loader internals in `scripts/core/manuscript_manifest.py`. Keep `_PENDING_DEFAULT` and `chapter_entry` signature. Change `MANIFEST_PATH` to a per-track resolver and key the cache on `track`:

```python
REPO = Path(__file__).resolve().parent.parent.parent

def _manifest_path(track: str) -> Path:
    return REPO / "content" / "manuscript" / track / "manifest.yaml"

@functools.lru_cache(maxsize=4)
def load_manifest(track: str = "samuel") -> dict:
    """Parsed folio manifest for *track* (``"samuel"`` default → unchanged
    back-compat; ``"kings"`` = the τ.6.x.4.c marathon). Cached per track;
    call ``load_manifest.cache_clear()`` after editing the YAML in tests."""
    raw = yaml.safe_load(_manifest_path(track).read_text(encoding="utf-8")) or {}
    return raw
```

Keep the module-level `MANIFEST_PATH = _manifest_path("samuel")` name bound for any external importer (back-compat). `chapter_entry` is unchanged (it already takes the loaded `man` dict).

- [ ] **Step 4: Run the test to verify it passes** (kings test still fails until 0.2 seeds the YAML — that is expected; `test_samuel_default_back_compat` MUST pass now)

Run: `… -m pytest tests/test_manuscript_kings.py::test_samuel_default_back_compat -q`
Expected: PASS.

- [ ] **Step 5: Commit**

`./save.cmd "tau.6.x.4.c Stage0.1: track-parameterize manuscript_manifest (samuel default = back-compat; kings track added)"`

### Task 0.2: Seed `content/manuscript/kings/manifest.yaml`

**Files:**
- Create: `content/manuscript/kings/manifest.yaml`
- Create (empty dir marker): `content/manuscript/kings/calibration/.gitkeep`, `content/manuscript/kings/collation/.gitkeep`

- [ ] **Step 1: Generate the seed manifest** (mirror `content/manuscript/samuel/manifest.yaml` structure exactly: book → int chapter → `{GG:{folios:[],source_images:[]}, CAM:{folios:[],views:[]}, status:pending}`; **all 47 pending**, folios filled per-chapter at the marathon locate-step).

Run this generator (writes the file deterministically — do NOT hand-type 47 blocks):

```python
cd "C:\Users\bogda\Documents\YHWH-v2.4-full\YHWH v2.4"; $env:PYTHONUTF8="1"; & "C:\Users\bogda\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c @'
import os, io
os.makedirs("content/manuscript/kings/calibration", exist_ok=True)
os.makedirs("content/manuscript/kings/collation", exist_ok=True)
open("content/manuscript/kings/calibration/.gitkeep","w").close()
open("content/manuscript/kings/collation/.gitkeep","w").close()
o = io.StringIO()
o.write("# content/manuscript/kings/manifest.yaml\n")
o.write("# Kings dual-manuscript folio manifest - tau.6.x.4.c.\n")
o.write("# Structure mirrors samuel/manifest.yaml: book -> chapter(int) -> {GG,CAM,status}.\n")
o.write("# All 47 chapters pending until each is blind-transcribed + collated under the marathon.\n")
for book, n in (("1ki",22),("2ki",25)):
    o.write(book+":\n")
    for c in range(1,n+1):
        o.write("  %d:\n" % c)
        o.write("    GG:\n      folios: []\n      source_images: []\n")
        o.write("    CAM:\n      folios: []\n      views: []\n")
        o.write("    status: pending\n\n")
open("content/manuscript/kings/manifest.yaml","w",encoding="utf-8",newline="\n").write(o.getvalue())
print("seeded", len(o.getvalue()), "bytes")
'@
```

- [ ] **Step 2: Run the full Task-0.1 test to verify it passes**

Run: `… -m pytest tests/test_manuscript_kings.py -q`
Expected: PASS (all three tests; kings manifest now loads 47 pending).

- [ ] **Step 3: Commit**

`./save.cmd "tau.6.x.4.c Stage0.2: seed content/manuscript/kings/manifest.yaml (1ki 1-22 + 2ki 1-25, all pending) + calibration/collation dirs"`

### Task 0.3: Track-parameterize the at-scale driver

**Files:**
- Modify: `scripts/run_manuscript_collation_at_scale.py`
- Test: append to `tests/test_manuscript_kings.py`

- [ ] **Step 1: Write the failing test**

```python
def test_driver_kings_track_reports_47_pending():
    import scripts.run_manuscript_collation_at_scale as drv
    rep = drv.run(dry=True, track="kings")
    assert rep["chapters_total"] == 47
    assert rep["chapters_pending"] == 47
    assert rep["chapters_collated"] == 0
    assert {x["book"] for x in rep["pending_needs_transcription"]} == {"1ki", "2ki"}


def test_driver_samuel_default_unchanged():
    import scripts.run_manuscript_collation_at_scale as drv
    rep = drv.run(dry=True)                       # no track → samuel
    assert rep["chapters_total"] == 55
    assert rep["chapters_collated"] == 4          # the 4 calibration chapters
```

- [ ] **Step 2: Run it to verify it fails**

Run: `… -m pytest tests/test_manuscript_kings.py::test_driver_kings_track_reports_47_pending -q`
Expected: FAIL — `run()` has no `track` kwarg.

- [ ] **Step 3: Implement** — parameterize the driver. Add a `TRACKS` table; thread `track` through `run()`/`main()`; derive `ref = f"{book}{ch}"` generically (drop the hardcoded `CALIBRATED_REFS`; collatability = manifest `status=="calibrated"` + both witness JSONs exist):

```python
TRACKS = {
    "samuel": {"chapters": {"1sa": 31, "2sa": 24}, "dir": "samuel"},
    "kings":  {"chapters": {"1ki": 22, "2ki": 25}, "dir": "kings"},
}

def _dirs(track: str):
    base = REPO_ROOT / "content" / "manuscript" / TRACKS[track]["dir"]
    return base / "calibration", base / "collation"

def _ref_for(book: str, ch: int) -> str:
    return f"{book}{ch}"                     # 1sa1, 1ki1, 2ki25 …

def run(dry: bool = True, track: str = "samuel") -> dict:
    cal_dir, coll_dir = _dirs(track)
    book_chapters = TRACKS[track]["chapters"]
    mm.load_manifest.cache_clear()
    man = mm.load_manifest(track=track)
    # … existing loop body, but: ref = _ref_for(book, ch);
    #   witness paths from cal_dir; _is_collatable uses status=="calibrated"
    #   AND (cal_dir/f"{ref}_witnessGG.json").is_file()
    #   AND (cal_dir/f"{ref}_witnessCAM_hires.json").is_file();
    #   _write_collation writes coll_dir/f"{ref}_collation.json";
    #   apparatus → mr.dump_apparatus(book, app) (already book-keyed).
```

`_is_collatable`, `_collate_chapter`, `_write_collation` take `cal_dir`/`coll_dir` params instead of the module constants. `main()` gains `--track {samuel,kings}` (default samuel). Keep `BOOK_CHAPTERS = TRACKS["samuel"]["chapters"]` bound for any external importer.

- [ ] **Step 4: Run both new tests + the FULL existing manuscript suite (regression — samuel MUST stay byte-identical)**

Run: `… -m pytest tests/test_manuscript_kings.py tests/ -q -k "manuscript or Manuscript or Calibration or Collation or Reconcile or Scale"`
Expected: PASS — new kings tests green; **all prior Samuel manuscript tests (29) still green** (samuel default path unchanged).

- [ ] **Step 5: Commit**

`./save.cmd "tau.6.x.4.c Stage0.3: track-parameterize run_manuscript_collation_at_scale (--track; generic ref=book+ch; samuel default byte-identical)"`

### Task 0.4: Verify the engine accepts Kings + lint/regression gate

**Files:** none (verification only).

- [ ] **Step 1: Confirm the semantic skeleton loads for Kings**

Run: `cd "…\YHWH v2.4"; $env:PYTHONUTF8="1"; & "…\python.exe" -c "from scripts.core import manuscript_collation as mc; s1=mc.load_kjv_skeleton('1ki',1); s2=mc.load_kjv_skeleton('2ki',1); print('1ki1 skel verses:',len(s1)); print('2ki1 skel verses:',len(s2)); assert s1 and s2"`
Expected: PASS — non-empty skeletons for 1ki/2ki. **If this raises/empty:** that is a real Stage-0 finding — STOP and report (the skeleton anchor is required by the collation engine; do not proceed to the marathon without it).

- [ ] **Step 2: Full lint + ruff + manuscript regression**

Run: `cd "…\YHWH v2.4"; $env:PYTHONUTF8="1"; & "…\python.exe" -m scripts.lint_rules; & "…\python.exe" -m ruff format --check scripts/core/manuscript_manifest.py scripts/run_manuscript_collation_at_scale.py tests/test_manuscript_kings.py; & "…\python.exe" -m pytest tests/ -q -k "manuscript or Manuscript or Calibration or Collation or Reconcile or Scale"`
Expected: `lint_rules` **11·0·0**; ruff clean; regression green. Commit any ruff reformat: `./save.cmd "tau.6.x.4.c Stage0.4: ruff-format + verify engine accepts Kings; lint 11.0.0"` (skip the commit if nothing changed).

---

# STAGE 1 — The 47-chapter blind dual-witness transcription marathon

**Reuses the Samuel per-chapter procedure VERBATIM** (`2026-05-16-samuel-calibration-gate.md` Tasks 1–7 + `2026-05-16-samuel-widened-calibration.md` per-chapter sequence). Only `(book, chapter, ref, GG source folder, CAM folio band)` change per chapter. Defined ONCE here as a parameterized template; the queue is the explicit ordered chapter list.

## The chapter queue (execute in this exact order)

**1 Kings:** `1ki` ch **1 → 22**.  **2 Kings:** `2ki` ch **1 → 25**.

- `1ki` GG source folder: `GAPS/2_Kings/GG-00106/1-Kings/` (folios `f028v`–`f040v`)
- `2ki` GG source folder: `GAPS/2_Kings/GG-00106/2-Kings/` (folios `f040v`–`f053r`)
- CAM low-res locating band (both): `GAPS/2_Kings/Cambridge-Add-1570/Kings_f126r…f146v.jpg`
- `ref = f"{book}{ch}"`. **1 Kings 1 (`1ki1`) is FIRST and is the safety-stop checkpoint** (see plan header "Decision inheritance").

## Per-chapter procedure template (run this 47× — once per queued chapter)

> **⚑⚑ METHOD NOTE — codified from the 1 Kings 1 safety-stop (2026-05-17); applies to EVERY chapter's C-2/C-3/C-5/C-6. This is the primary thing the safety-stop existed to learn.** The dominant, recurring GG/CAM vision-transcription failure mode is **harmonization toward the printed/standard Ethiopic Bible**: in a faded/ambiguous span the transcriber "recognises" a standard phrase and writes the *printed* form (inserted/dropped function words, printed word-order, standard vowel forms e.g. `አ` U+12A0 where the parchment has `እ` U+12A5, standard gemination) instead of the actual glyphs. On 1ki1 GG this needed **3 adversarial rounds** to fully extract (round-1 broad pattern v1–v15 → round-2 confirmed 8 fixes + 4 residuals → round-3 clean).
> - **C-2/C-5 transcriber prompt MUST forbid harmonization forcefully and UP FRONT** (a "CARDINAL RULE" section, not buried in the honesty contract): transcribe the parchment glyphs even when they differ from the expected Bible; wherever a recognisable standard phrase appears in faded text, transcribe what is actually written and flag `uncertain` — **NEVER** substitute the printed form; genuinely unreadable → `⟦illegible⟧` + matching `marker:"illegible"`, never the expected word.
> - **C-3/C-6 must hunt the harmonization class specifically** and run the fix-loop **to convergence (expect 2–3 rounds at this image resolution)**, sending each fix to a fresh self-contained fix-agent (SendMessage is unavailable here) with the reviewer's exact on-page readings + the cardinal rule + tight scope (touch only the flagged verses; all others byte-identical; programmatically diff to prove scope).
> - **SECOND dominant failure mode — accidental column/folio-boundary scripture OMISSION mis-labelled as a "recensional minus" (CRITICAL — the worst defect class: dropped scripture).** On 1ki1 CAM the transcriber dropped real scripture at TWO column turns (f126r col1→col2 lost std v15/16; col3→f126v-L lost std v42) and rationalised both as "recensional minuses"; caught only by the C-6 make-or-break check; restoration needed a boundary re-read + full re-segmentation (50→52 v). **C-5/C-2 transcriber prompts MUST mandate explicit text-continuity tracing across EVERY column AND every folio/recto-verso turn**: a word routinely splits across the turn (e.g. `ከንኪ`=`ከን`|`ኪ`; `ለሳደቅሁ`=`ለሳ`|`ደቅሁ`) so a verse boundary may NEVER fall mid-word; never "resume" at the next column/folio without confirming the running text is physically continuous (no skipped line/column); read column-bottom→column-top contiguously. **C-6/C-3 reviewer make-or-break check on EVERY chapter: every claimed recensional minus / short reading MUST be independently verified GENUINE by re-tracing the running text glyph-by-glyph across the relevant column & folio turns.** A "minus" actually present on the page = a CRITICAL defect → restore from the parchment (never paste a printed Bible). A genuinely short/compressed recension IS the expected distinct-recension signal — but it must be PROVEN at the boundary, not assumed (the `feedback_reverify_conservative_nogo` lesson: adjudicate on the source artefact, not the transcriber's rationalisation). Highest-risk spots: col1→col2, col2→col3, recto→verso, folio→folio.
> - **Explicit TERMINATION BAR** (give it to the reviewer to prevent orthographic ping-pong): APPROVE when faithful-to-parchment + no substantive word-level harmonization/fabrication remains + validator `OK` + non-Ethiopic screen `CLEAN`. Honestly-flagged **sub-glyph orthographic** uncertainty (vowel `አ`/`እ`, gemination, `ቂ`/`ቁ`) is ACCEPTABLE and must **NOT** be pushed back toward printed spelling — that re-introduces the harmonization. The reviewer adjudicates **strictly on the page image**, never on its own predicted/standard strings (on 1ki1 the parchment legitimately differed from the reviewer's orienting strings; the transcriber was right).
> - **Non-Ethiopic contamination screen in EVERY C-3/C-6** (the shipped validator does NOT catch Latin/mojibake — a literal `f` slipped into 1ki1 v40). **The screen MUST whitelist the sanctioned `⟦illegible⟧` sentinel** — that sentinel legitimately contains the Latin letters i,l,e,g,b, and the shipped validator itself *requires* it (bijection-enforced); a naive char-allowlist false-flags every chapter that has any illegible span (caught on 1ki1 CAM, which has 1 honest illegible — GG had 0, which is why GG slipped by). Correct one-liner: `& "…\python.exe" -c "import json; d=json.load(open('content/manuscript/kings/calibration/{ref}_witness{W}.json',encoding='utf-8')); E=lambda c: 'ሀ'<=c<='፿'; bad=[(v['v'],hex(ord(c))) for v in d['verses'] for c in v['geez'].replace('⟦illegible⟧',' ') if c!=' ' and not E(c)]+[(v['v'],'TOK:'+t) for v in d['verses'] for t in v['tokens'] if t!='⟦illegible⟧' and not all(E(c) for c in t)]; print('CLEAN' if not bad else bad[:20]); assert not bad"` must print `CLEAN`. (Allowed = Ethiopic block U+1200–U+137F + ASCII space + the whole-token `⟦illegible⟧`. Task #14 folds exactly this rule into `validate_witness`, verified to keep the 4 immutable Samuel goldens + the 71-test regression green; until #14 lands, run this corrected screen inline.)
> - After EVERY fix: recompute `tokens` per `_geez_to_tokens`, and re-verify `uncertain[].token_index` ranges + the `⟦illegible⟧`⟺`marker:"illegible"` bijection, then re-run validator + screen.
> - **Scratch-file discipline (the `git add -A` footgun — 75ba7b2 incident).** Every transcribe/review/fix subagent crops+upscales the ~80MP folios to read fidel. Their prompts MUST mandate writing ALL crop/scratch to an **OS temp dir OUTSIDE the repo** (e.g. `C:\Users\bogda\AppData\Local\Temp\<task>\`, the model the C-4 CUDL agent followed) and deleting it before reporting — NEVER the repo root. Subagent "cleaned up" claims are UNRELIABLE: the **controller MUST run `git status --short` and confirm zero stray scratch BEFORE every checkpoint/`save.cmd`** (which does `git add -A`). `.gitignore` carries `_rev_tmp*/` `_scratch*/` `*_crop_tmp/` as the defensive backstop, but the temp-dir mandate is the real fix — restate it verbatim in every C-2/C-3/C-5/C-6/fix dispatch.

> **⚑⚑ METHOD NOTE 3 — codified from the 1 Kings 4 retrospective (audit 2026-05-20); applies to EVERY chapter's C-1 and the resulting C-2/C-5 prompts.** The harmonization + boundary-omission notes above are NARRATIVE-class failure modes. 1Ki4 surfaced a distinct **LIST-class** failure profile (Solomon's officer registry + comparative-wisdom names): the C-3 R1 found 110+ defects across `ለ`/`ስ`, `ይ`/`ደ`, `ያ`/`ደ` name-fidel families, body-vs-rubric cross-glyph mis-labels, and red-numeral-vs-fidel-letter mis-decode — none of which fired on 1Ki1/1Ki2/1Ki3. The convergence took **7 GG rounds** (vs 3 for 1Ki1, 4 for 1Ki2, 5 for 1Ki3) because the C-2 prompt was not pre-screening for the list-class. The matrix now classifies each chapter at C-1 and embeds class-specific anti-failure screens in the C-2/C-5 prompt.
> - **At C-1, run `scripts.core.manuscript_chapter_class.chapter_profile(book, chapter)`** — returns `{class, screens, expected_rounds_min, expected_rounds_max}`. `class ∈ {NARRATIVE, LIST, REGNAL_FRAME}`. The known LIST chapter is `1ki:4`; the known REGNAL_FRAME chapters are `1ki:15`, `1ki:16`, `2ki:13-17`. Samuel coverage also wired: `1sa:13-15` REGNAL_FRAME, `2sa:8/20/23` LIST (audit U-belt 2026-05-20). Default for everything else is NARRATIVE (conservative — the classifier is a risk-screening tool, not a gate).
> - **The C-2/C-5 transcriber-prompt template MUST embed each screen from `chapter_profile.screens` verbatim** (the function returns NARRATIVE screens first, then LIST additions if applicable, then REGNAL additions). Controller assembles the prompt at C-1 by joining these screens above the existing CARDINAL RULE preamble.
> - **`expected_rounds_min`/`max` set realistic ETAs and the escalation bar.** Narrative: 2–4 rounds. List: 4–7. Regnal: 4–8. If a chapter's GG or CAM C-3/C-6 has NOT converged by `expected_rounds_max`, the reviewer MUST surface the open defect list to the user rather than mechanically iterate — that is the geometric-convergence-broken signal (per the systematic-debugging "3+ fixes = question the architecture" rule). **Enforced by `scripts.core.manuscript_rounds.escalate_if_unbounded(class, current_round, hard_defects, new_ambiguous=0)`** — the controller calls it between rounds (see C-3 + C-6 below).
> - **When a new failure class is found in the wild** (as the rubric-vs-tinted-`:` ambiguity emerged at 1Ki4 GG R7): the controller appends it to `scripts/core/manuscript_chapter_class.py`'s `_LIST_SCREENS` (or the appropriate class block) at C-9 close, so the next chapter inherits the lesson. This is how the class-screens grow without re-tuning the procedure mid-marathon.

> **⚑⚑ METHOD NOTE 4 — AMBIGUOUS-PARCHMENT convergence rule (codified at audit U-belt 2026-05-20).** Reviewers (C-3 GG and C-6 CAM) routinely identify items where the parchment ink is at the available zoom limit and the read cannot be definitively confirmed or refuted from the GG/CAM image alone. The 1Ki4 GG R7 alone added 2 such items (the rubric-vs-tinted-`:` axis at v5 mid + v9 tail); across the marathon they accumulate. Without an explicit convergence rule they pollute the immutable evidence indefinitely.
> - **Each AMBIGUOUS-PARCHMENT item flagged at C-3/C-6 follows one of four resolution paths AT C-7 (collation) OR LATER:**
>   1. **CAM cross-reference resolution.** If the SAME locus is unambiguous in the other witness (e.g., CAM clearly reads what GG-AMBIGUOUS-PARCHMENT suspected), the engine's alignment row settles it. The witness with the clearer reading is the source of truth; the apparatus records the divergence as a regular `disagree`/`agree`/`lacuna` class. **Drop the AMBIGUOUS flag** from the witness's `transcription_notes` at the next chapter close.
>   2. **Both-witness-confirmed lectio.** If both witnesses agree on the ambiguous reading at the same locus (rare but possible — e.g., both CAM and GG independently show a small red mark at the same inter-word boundary), the reading is recorded in the apparatus as a `lectio` variant + a structural note explains the resolution-limit. **Drop the AMBIGUOUS flag.**
>   3. **Higher-resolution re-pull resolution.** If the locus is genuinely critical (semantic differs by the read) AND CAM cross-ref doesn't settle it, request a higher-resolution CUDL master at C-7 (use `scripts/acquire_cudl_master.py <view> <output>` — the pre-pull tool ships the same code path). Save the new master + record in `transcription_notes`. **Drop the AMBIGUOUS flag** once the new master resolves.
>   4. **Honest archival.** If after CAM cross-ref + (optional) re-pull the item remains genuinely unresolvable at any available zoom, **archive the class in `content/manuscript/_reviewer_context/<GG|CAM>_topology.md` §5** (the resolution-limited section) and DROP the per-chapter flag from `transcription_notes`. The topology now carries the class forever; new chapters' reviewers won't re-discover it.
> - **No AMBIGUOUS flag persists past C-7 collation in a chapter's `transcription_notes`** — every flagged item resolves to one of the four paths above. If none of the paths apply, that is a SURFACE-TO-USER event (the reviewer surfaces "I cannot resolve this item by any of the four paths" to the user before C-9 commits).
> - **The closing C-3/C-6 reviewer's APPROVED CLEAN message reports the per-chapter ambiguous-item count + each item's chosen resolution path.** Lifecycle is auditable from the review records.

> **⚑⚑ METHOD NOTE 5 — Hybrid cadence (codified at audit U-belt 2026-05-20, supersedes the prior plan header's "continuous" default in light of memory `feedback_marathon_pacing`).** The plan header's "execute continuously" default and the user's memory-recorded preference for single-chapter check-ins are reconciled by class:
> - **NARRATIVE-class chapters: CONTINUOUS execution by default.** No user check-in between C-9 of one NARRATIVE chapter and C-1 of the next. The chapter classifier (`chapter_profile(book, ch)["class"] == "NARRATIVE"`) confirms class at C-1; if confirmed, after C-9 commit the controller immediately starts the next pending chapter's C-1. User can interrupt anytime; a CONTRADICTS or base-SURFACE-TO-USER trigger always stops regardless.
> - **LIST + REGNAL_FRAME-class chapters: STOP-AND-CHECK-IN at C-9.** These are the predictably-hard chapters (1Ki4 LIST was 7 GG rounds; REGNAL_FRAMES are projected 4-8). After C-9 commit, the controller reports the chapter close + the per-class trajectory data (rounds, hard-defects-by-round, ambiguous-classes) and AWAITS explicit user go-ahead before starting the next chapter (whether the next is NARRATIVE or LIST/REGNAL).
> - **Rationale.** Memory `feedback_marathon_pacing` reflects the user's preference to inspect heavy chapters; the existing single-chapter-blanket cadence over-corrected by stopping after every NARRATIVE chapter too (cost: ~0.5-1 day wait per chapter × 43 chapters = ~30 days of pure wait). The hybrid recovers ~30 days while preserving the inspection point on the chapters most likely to need user judgment.
> - **Override.** The user can switch to all-continuous OR all-single-chapter at any point by message; the override applies to the next chapter forward. The hybrid is the default, not a lock.

> **⚑⚑ METHOD NOTE 6 — scope-ahead look-ahead dossier + the BLINDNESS RULE (codified 2026-05-27).** A rolling **text-only** scope-ahead pass (concurrent-safe per memory `feedback-concurrent-agent-cap`: 1 heavy vision agent + ≤2 light text-only agents = no RAM pressure) maintains `dev/MARATHON_LOOKAHEAD.md` — per-chapter class/rounds, KJV ceiling, KNOWN LXX/recension divergences, folio-band estimates — kept AHEAD of the heavy front. It only helps if it REACHES the work, and only in the RIGHT places:
> - **CONTROLLER consumes it** at C-1 (folio-band → locating), C-4 (which CAM folio to pull), C-7 (collation — expect the divergence so a genuine minus/swap, e.g. 1ki20↔21, is not mis-aligned against the KJV skeleton or mis-flagged as a defect), and pacing (LIST/REGNAL → check-in).
> - **C-3/C-6 REVIEWERS** receive it ONLY as orientation: "a short/divergent/transposed reading may be a genuine recension feature here — but PROVE it on the ink." It does NOT lower the make-or-break boundary-omission bar (METHOD NOTE 2).
> - **The blind C-2/C-5 TRANSCRIBERS NEVER receive recension CONTENT.** Telling a blind transcriber "expect Naboth here" would induce the exact harmonization the CARDINAL RULE forbids. Only the class-`screens` from `chapter_profile` (HOW to read carefully, not WHAT the text says) reach transcriber prompts. **Blindness is preserved — the dossier accelerates everything AROUND the transcriber, never the transcriber itself.**
> - Every dossier claim is a PRE-WARNING to verify on parchment, never a fact. Planned automation: structure the dossier as per-chapter records surfaced by a `chapter_prep(book, ch)` helper alongside `chapter_profile`, each carrying a `verify_on_parchment` flag, so C-1 cannot forget it.

For the current `(book, ch, ref)`:

- [ ] **C-1 Locate in GG + classify the chapter.** Controller views the `{book}` GG folder images in folio order until chapter `ch` is found and its end (start of ch `ch+1`) is seen. Identify the GG folio siglum(s), column, line where ch `ch` begins/ends, using the **known Kings narrative** as the anchor (1 Kings: Solomon's accession/temple/Sheba/division of the kingdom; 2 Kings: Elijah's ascension/Elisha cycle/the divided-kingdom regnal frame/the fall of Samaria + Jerusalem). **Verify the GG folio is undamaged**; if water/loss damage dominates the chapter, note it (the apparatus + lacuna-honesty handles partial damage — do NOT swap chapters; record damage in `transcription_notes`). Methodological rule (memory + Samuel finding): the red `✣ ክፍል ፡ N ✣` rubrics are FINE liturgical subdivisions, **NOT** modern chapters — anchor on the modern-chapter NARRATIVE + the coarse `ምዕራፍ` rubric; treat `ክፍል` numerals as noise for chapter bounds. **Then call `chapter_profile(book, ch)` (per METHOD NOTE 3)** and capture the returned `{class, screens, expected_rounds_max}` for the C-2/C-5 prompts and the escalation bar. **Also consult `dev/MARATHON_LOOKAHEAD.md` for this `(book, ch)`** — its KJV-ceiling, known LXX/recension divergences, and folio-band estimate — and route it per the **BLINDNESS RULE (METHOD NOTE 6)**: recension-content + folio-band inform the CONTROLLER (locating here · C-4 CAM-folio targeting · C-7 collation/skeleton-alignment · LIST/REGNAL pacing) and reach the C-3/C-6 REVIEWERS ONLY as orientation ("a short/divergent reading may be a genuine recension feature — still prove it on the ink"); they are **NEVER** injected into the blind C-2/C-5 transcribers. Only the class-`screens` go to transcriber prompts.

- [ ] **C-2 Blind-transcribe GG** — dispatch an **isolated implementer subagent** (model: opus). It sees the GG image(s) for `(book,ch)` **ONLY** — never any CAM image, never the other witness, never another transcription. It produces `content/manuscript/kings/calibration/{ref}_witnessGG.json` to the SHIPPED schema (above): `witness:"GG"`, `book`, `chapter:ch`, `source_images`/`folio_sigla` from C-1, one contiguous `verses[]` from `v:1`, `geez` verbatim, `tokens` = the exact `_geez_to_tokens` normalization, `uncertain[]` with the `⟦illegible⟧`↔`marker:"illegible"` bijection, honest `damaged`/`uncertain` markers concentrated on real damage, `transcription_notes` (hand, damage, layout, ch→ch+1 boundary). The subagent prompt embeds the schema verbatim + the class-specific screens from C-1 + "fabricate nothing — illegible spans get `⟦illegible⟧` + a matching uncertain entry, never a guessed word." **The subagent MUST write via `scripts.core.manuscript_records.write_witness(witness="GG", book=..., chapter=..., source_images=..., folio_sigla=..., verses=[{v, column, line_start, geez, uncertain}], transcription_notes=..., output_path=...)`** — this helper derives canonical `tokens` from `geez` via `_geez_to_tokens`, auto-assigns `token_index` for `marker:"illegible"` entries, validates the record, and raises before writing if invalid. Raw `json.dump` is FORBIDDEN — it was the path that produced the 1Ki4 schema drift (custom uncertain markers `name_form`/`lectio`/etc. and `✣` in tokens) that needed a one-shot driver to collate. **BEFORE returning, the subagent runs `scripts.core.manuscript_self_check.screen_witness_for_class_failures(record, chapter_class)`** on its own written JSON and fixes any pattern-flagged token (re-verifying against parchment) — saves an adversarial review round on the obvious classes. The helper is parchment-blind and complements (does NOT replace) C-3 vision review.

- [ ] **C-3 Adversarial GG review** — dispatch an **independent reviewer subagent**. **Reviewer pre-flight: read `content/manuscript/_reviewer_context/GG_topology.md` IN FULL before opening the chapter** — it carries the cross-chapter scribal-hand references (known-clean `✣` anchors, stroke patterns for `ለ`/`ስ`/`ይ`/`ደ`/`ያ`/`ደ`, numeral-vs-letter, AMBIGUOUS-PARCHMENT classes). This saves 1 round per chapter that would otherwise be spent re-deriving the topology. It re-opens the same GG image(s) + the produced JSON and (a) runs the HARD validator, (b) spot-checks readings vs the image using the topology references, (c) checks honesty (flagged spans = real damage; no fabricated text). Fix-loop (same implementer fixes → re-review) until ✅. **At every round close BEFORE dispatching round N+1, controller calls `scripts.core.manuscript_rounds.escalate_if_unbounded(chapter_class, current_round=N, hard_defects=N_open, new_ambiguous=N_new_ambig)`** — if `escalate=True`, STOP the fix-loop and surface `reason`+`recommended_action` to the user; do NOT dispatch round N+1. **On APPROVED CLEAN, the reviewer APPENDS any newly-confirmed scribal-hand fact to `GG_topology.md`** (never overwriting; struck-through-if-refuted). **Validator command:** `cd "…\YHWH v2.4"; $env:PYTHONUTF8="1"; & "…\python.exe" -c "import json; from scripts.core.manuscript_records import validate_witness; d=json.load(open('content/manuscript/kings/calibration/{ref}_witnessGG.json',encoding='utf-8')); ok,e=validate_witness(d); print('OK' if ok else e); assert ok, e"` → must print `OK`.

- [ ] **C-4 Acquire CAM hi-res** (controller). From the CAM low-res band + the GG narrative just transcribed, identify the CAM Add. 1570 folio(s) for `(book,ch)` **by VISION** (ToC mislabels Reigns). Pull from CUDL IIIF per memory `cudl-iiif-access`: fetch the manifest, find the view, region-tile the ~80MP master in ≤1900px tiles, stitch with Pillow, QC the stitch (legible at native zoom; full chapter present). Save `GAPS/2_Kings/Cambridge-Add-1570-hires/MS-ADD-01570_f{NNN}_{ref}_hires.jpg`.

- [ ] **C-5 Blind-transcribe CAM hi-res** — fresh **isolated implementer subagent** (opus), the CAM hi-res image(s) for `(book,ch)` **ONLY** (no GG, no GG JSON, no skeleton). Produces `content/manuscript/kings/calibration/{ref}_witnessCAM_hires.json`, `witness:"CAM"`, same schema/contract as C-2 — **MUST use `scripts.core.manuscript_records.write_witness(witness="CAM", ..., output_path=...)`** (canonical writer; raw `json.dump` FORBIDDEN; see C-2 rationale). Class-specific screens from C-1 apply identically, PLUS the CAM-specific failure modes documented in `content/manuscript/_reviewer_context/CAM_topology.md` §2 — homoeoteleuton scripture-drop (worst CAM-specific class), column/folio-boundary scripture omission (CAM-1Ki1 lost TWO column-turn omissions in R1), dittography fabrication, divine-name harmonization, pseudo-archaism (the CARDINAL RULE cuts both ways on CAM — neither smoothed-toward-printed nor invented-archaisms; only the inked glyphs). The C-5 prompt MUST include the CAM topology section verbatim. CAM hand is denser + carries marginalia — ignore side-margin notes; marginalia out of scope per spec §2. **Before returning, the subagent runs `screen_witness_for_class_failures`** as in C-2 + a CAM-specific homoeoteleuton check: at every span where CAM is materially shorter than GG (if a prior GG witness is available — only at REGNAL/LIST comparison points) suspect a homoeoteleuton skip; verify on parchment before accepting.

- [ ] **C-6 Adversarial CAM review** — independent reviewer subagent. **Reviewer pre-flight: read `content/manuscript/_reviewer_context/CAM_topology.md` IN FULL + `GG_topology.md` §2 (every GG fidel-family class also fires on CAM)** before opening the chapter. CAM-specific failure classes (homoeoteleuton scripture-drop, column-boundary omission, dittography fabrication, divine-name harmonization, pseudo-archaism) are documented in §2; same-direction stroke calibration in §1 + §3. **The empirical pattern is that CAM is HEAVIER than GG in this scribal family** (denser hand, more red-rubric register, more line-end glyph-drop ambiguity, more boundary-omission risk); plan METHOD NOTE 3's `expected_rounds_max` already accommodates this (LIST class allows 7, REGNAL_FRAME 8) but the reviewer should NOT be alarmed if CAM takes more rounds than GG on the same chapter — that is the documented pattern, not a defect. Validator command identical with `…{ref}_witnessCAM_hires.json`. Fix-loop until the validator prints `OK` and honesty/readings are confirmed. **At every round close, controller calls `escalate_if_unbounded(...)` as in C-3.** **On APPROVED CLEAN, the reviewer APPENDS any newly-confirmed CAM scribal-hand fact to `CAM_topology.md`** (append-only; struck-through-if-refuted).

- [ ] **C-7 Collate via the shipped Phase-2 tool.** Controller runs the engine for this chapter:
  `cd "…\YHWH v2.4"; $env:PYTHONUTF8="1"; & "…\python.exe" -c "import json; from scripts.core import manuscript_collation as mc, manuscript_reconcile as mr; from scripts.core.manuscript_records import validate_witness; gg=json.load(open('content/manuscript/kings/calibration/{ref}_witnessGG.json',encoding='utf-8')); cam=json.load(open('content/manuscript/kings/calibration/{ref}_witnessCAM_hires.json',encoding='utf-8')); [exec('ok,e=validate_witness(w); assert ok,e') for w in (gg,cam)]; k=mc.load_kjv_skeleton('{book}',{ch}); col=mc.collate(gg,cam,k,book='{book}',chapter={ch}); rec,app=mr.reconcile(col); json.dump(col,open('content/manuscript/kings/collation/{ref}_collation.json','w',encoding='utf-8'),ensure_ascii=False,indent=2); print('semantic',col['metrics']['semantic_pass_pct'],'bothW',col['metrics'].get('ww_agreement_pct'),'base',col.get('base_witness'))"`
  (The engine emits base=CAM per the ratified D3 rule + the honest two-clause `_pick_base`; token-conservation + lacuna-honesty are HARD-gated inside the engine.)

- [ ] **C-8 Adversarial collation review** — independent reviewer subagent: independently recompute every metric from the collation `alignment[]`; verify lacuna reconcile == evidence `⟦illegible⟧` count; verify token-conservation; verify base + semantic. Fix-loop (re-collate after any evidence fix) until ✅.

- [ ] **C-9 Flip the manifest + append ledger + commit.** Controller sets `content/manuscript/kings/manifest.yaml` `{book}:{ch}:` → fill `GG.folios`/`GG.source_images` (from C-1), `CAM.folios`/`CAM.views` (from C-4), `status: calibrated`. **THEN append ONE row to `dev/MARATHON_LEDGER.md`** with the chapter's `{ref, class, c9_date, days, gg_rounds, cam_rounds, r1_defects, commit, notes}` — captures cadence telemetry per audit U-belt. Then:
  `./save.cmd "tau.6.x.4.c {ref}: blind dual-witness GG+CAM transcription + collation (semantic NN/NN, bothW NN%, base=CAM); manifest calibrated"`
  Evidence JSONs are now immutable.

- [ ] **C-10 (1 Kings 1 ONLY — the safety stop).** After `1ki1` C-9, evaluate the bi-directional rule (plan header). **Matches the ratified pattern** (semantic ≥ 95%, both-confident materially < 90% on clean text, base=CAM, no contradiction) → record one line in `dev/CALIBRATION_2026-05-17-kings-1ki1.md` and **continue the queue continuously** (no user check-in — the model is already ratified). **Contradicts** → STOP, write the finding to that file, surface to the user, do not proceed. For ch ≠ `1ki1`, skip C-10.

Repeat C-1…C-9 for the next queued chapter. The `run_manuscript_collation_at_scale.py --track kings` dry report is the cross-session progress ledger (`pending_needs_transcription` shrinks as chapters flip to calibrated).

## Stage-1 close: book-wide QA

- [ ] **S1-QA** After all 47 chapters are `calibrated`: run `& "…\python.exe" scripts/run_manuscript_collation_at_scale.py --track kings --write` (collates every chapter, writes `content/manuscript/kings/collation/*_collation.json` + `content/apparatus/{1ki,2ki}.json`). Then run `scripts/manuscript_qa.py` (parameterized for the kings track if needed — mirror its Samuel call) and confirm the QA verdict holds the engine's own metrics to the §4 bar with distinct-recension sub-bars as WARNs (memory `no-reassert-ratified-bar`: never re-assert a ratified one-time bar as a per-build fail). Write `dev/CALIBRATION_2026-05-17-kings-bookwide.md` (per-chapter table). Commit. `lint_rules` 11·0·0.

---

# STAGE 2 — Phase-3 render & integrate (post-marathon)

Reuses the τ.7.x machinery + design-spec §6 contract VERBATIM (the same Phase-3 deferred for Samuel — design spec §6 is the authoritative contract). Runs **after** Stage 1 produces the reconciled text + apparatus.

### Task 2.1: `KINGS_VERSE_COUNTS` floor

**Files:** Modify the verse-count-floor module (same module that defines the other τ.7.x book floors — locate via `grep -rn "VERSE_COUNTS" scripts/`; mirror the `ESTHER_VERSE_COUNTS`/`MQ?_VERSE_COUNTS` shape). Test: `tests/test_parallel_bible_tau6x2c_kings.py` (create).

- [ ] Add `KINGS_VERSE_COUNTS = {"1ki": {1:53, …, 22:53}, "2ki": {1:18, …, 25:30}}` — the canonical KJV/Masoretic ceiling, with a **documented Ethiopic "Books of Reigns" recension caveat** comment (design spec §6 line 207–212; exact per-chapter counts read from `content/notes/1ki.py`/`2ki.py` skeleton — `len(skeleton[ch])` per chapter, NOT hand-typed). Pin test: floor totals + `renumber_against_floor` underflow/no-overflow pattern. Commit.

### Task 2.2: Render `geez-tewahedo/1ki.py` + `2ki.py`

**Files:** Create `content/translations/geez-tewahedo/1ki.py`, `2ki.py` (via `write_book_module`, **including the τ.7.x.t `repr()` serialization fix** — manuscript text carries stray control-char artifacts). Modify `content/translations/geez-tewahedo/_meta.yaml` + `_source.yaml`.

- [ ] Build each module from the reconciled text (the engine's reconciled output per chapter — base=CAM running text). `SOURCE_QUALITY = "manuscript-collation-tier2"`; `SOURCE_PROVENANCE` records GG-00106 + Cambridge Add. 1570 (CC BY-NC, "Cambridge University Library") + crop provenance. `renumber_against_floor` against `KINGS_VERSE_COUNTS`. Update `_meta.yaml` book/verse stats + `ingest_record_tau6x2c`; `_source.yaml::ocr_strategy.tau6x4c_ingest` block. Pin tests mirror the τ.7.x convention (book loads, verse-count floor, renumber shape, `_meta`/`_source` back-link). Commit.

### Task 2.3: Apparatus store + `manuscript-collation-tier2` provenance tier

**Files:** `content/apparatus/1ki.json` + `2ki.json` (already written by S1-QA `--write`); register the `manuscript-collation-tier2` provenance tier in the reader-facing provenance surface (same path `ocr-tier3` flows — design spec §6 line 224–228); test: apparatus well-formedness + lacuna-honesty pin (no fabricated text where both witnesses fail) + provenance-tier-surfaced pin.

- [ ] Add the well-formedness + lacuna-honesty + tier-surface pins (design spec §8). Confirm every verse with a recorded disagreement/lacuna has a structured apparatus entry. Commit.

### Task 2.4: Release gate

- [ ] `lint_rules` **11·0·0**, `ruff format --check` clean, full focused regression green (same discipline as every τ.7.x ship). Update `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` (→ idle, arc closed) + `dev/CHANGELOG.md` (τ.6.x.4.c entry with cumulative corpus math + retrospective if §12 triggers fired). `superpowers:finishing-a-development-branch`. Local commit only — no push, no zip.

---

## Self-Review

**1. Spec coverage** (`2026-05-16-samuel-kings-dual-manuscript-collation-design.md`): §2 D1=B (reconstructed text + per-verse apparatus) → Stage 1 collation + Stage 2.3. §2 D2=B (semantic-skeleton + go/no-go) → C-7 engine semantic-pass + the 1ki1 safety stop (Kings inherits the ratified GO; bi-directional contradiction stop preserved). §2 D3=A (base + apparatus, eclectic recorded) → engine `_pick_base`/`reconcile`. §3 "Kings reuses Phases 2–3 verbatim" → Stage 0 reuse + Stage 1 (shipped tool) + Stage 2 (design-spec §6). §5 five units → all reused (engine/records/reconcile shipped; manifest+driver track-parameterized Stage 0). §6 render contract → Stage 2.1–2.4. §7 honesty contract (both-witness lacuna = marked gap, never fabricated; immutable evidence; tier surfaced) → SHIPPED-schema bijection + C-2/C-5 prompt + Stage 2.3. §8 testing → Stage 0 tests + S1-QA + Stage 2 pins + lint 11·0·0. §9 attribution → C-4 + Stage 2.2 `_source.yaml`. §3 phase tag `τ.6.x.4.c` → used throughout. No gaps.

**2. Placeholder scan:** No TBD/TODO. The 47× per-chapter procedure is a parameterized template with exact subagent roles + exact verification commands (the proven Samuel-widened structure; identical modulo book/chapter/images — not a placeholder). Stage 2 is fully specified by design-spec §6 + the τ.7.x convention (the same contract Samuel Phase-3 carries); exact per-chapter verse counts are read from the skeleton, not hand-typed (so the one unavoidable unknown is resolved deterministically at execution, not guessed).

**3. Type consistency:** The witness schema is the single SHIPPED `validate_witness` contract (top keys / per-verse keys / `_geez_to_tokens` / `⟦illegible⟧` bijection) referenced identically in C-2/C-3/C-5/C-6. `ref = f"{book}{ch}"` is defined once and used in every file path + the driver `_ref_for`. `track ∈ {samuel,kings}` is the one new parameter, samuel-default, threaded consistently through `load_manifest`/`run`/`main`. The collation API (`mc.load_kjv_skeleton`, `mc.collate(...,book=,chapter=)`, `mr.reconcile`, `validate_witness`) matches the shipped driver's usage exactly.

---

## Out of scope

- Kings GG/CAM **marginalia** transcription (design spec §2 D1-C — rejected for now).
- The French Patrologia Orientalis books (Chronicles/Ezra/Neh/Esther/Job) — separate easier printed-OCR track.
- Geʽez catchup loop (τ.6.x.2.o Sirach) + Amharic NT cadence — independently PAUSED, untouched by this arc.
- No push (remote deleted 2026-05-12); no zip ("continue"/"push" ≠ save — memories `reference_save`, `feedback_continue_not_save`).
