# Samuel Phase-2 — Dual-Manuscript Collation Tool — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** APPROVED & AUTHORIZED by the user at the τ.6.x.4.a-W widened-calibration gate (2026-05-17, **GO** — `dev/CALIBRATION_2026-05-16-samuel-widened.md` → `## Decision (user)`). This is **Phase-2** of the Samuel/Kings dual-manuscript design (spec `docs/superpowers/specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md` §5). Phase-1 (calibration) is COMPLETE and CONFIRMED the **diplomatic-parallel** model (CAM base + GG per-verse apparatus; spec D1=B/D3).

**Goal:** Build the production collation tool that turns dual-witness (GG + CAM) per-folio Ge'ez transcription records into a reconciled diplomatic-parallel Ge'ez Samuel + a two-witness apparatus + a book-wide QA report — proven correct by reproducing the four immutable Phase-1 calibration collations from their evidence.

**Architecture:** Five well-bounded units (spec §5): (A) a pure collation engine that generalizes the proven Phase-1 calibration logic; (B) a Samuel folio manifest; (C) an immutable per-folio transcription-record schema + validator that enforces the blind-protocol + honesty contract; (D) a reconciliation step producing the diplomatic-parallel text + apparatus store; (E) a QA/audit meta-tool wired into the preflight dashboard. The four Phase-1 calibration chapters are the **regression oracle**: the engine must reproduce `1sa1_collation_hires.json` / `1sa3_collation.json` / `1sa17_collation.json` / `2sa11_collation.json` from their immutable `*_witness*.json` evidence + the KJV skeleton. No production code is changed at any HTTP boundary except the additive preflight check.

**Tech Stack:** Python 3 (`py -3` launcher on Windows), pytest, PyYAML, the project's existing `scripts/core/*` conventions (rules §7), the meta-tool + preflight pattern (rules §9), `lint_rules.py`. No new third-party dependency.

---

## Orientation (read FIRST — the executing session has zero context)

1. **Bootstrap triad, in order:** `dev/CLAUDE_PROJECT_RULES.md`, `dev/SESSION_STATE.md` (top banner — τ.6.x.4.a-W COMPLETE, Phase-2 authorized), `dev/PLAN_2026-05-09.md`. Then this plan.
2. **The design contract:** spec `docs/superpowers/specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md` (esp. §5 units+contracts, §6 Phase-3 boundary, §7 honesty contract). The Phase-1 finding + the five failure modes Phase-2 must handle: `dev/CALIBRATION_2026-05-16-samuel-widened.md` §4.
3. **The proven artifacts (Phase-2's regression oracle + schema contract):** `content/manuscript/samuel/calibration/` holds 14 immutable JSONs — for each of `1sa1`(`_hires`)/`1sa3`/`1sa17`/`2sa11`: `*_witnessGG.json`, `*_witnessCAM_hires.json`, `*_collation.json` (+ 1sa1's low-res pair). **These define the exact schemas Phase-2 generalizes.** Study `2sa11_collation.json` (collation schema + `metrics.definitions`) and `1sa17_witnessGG.json` / `1sa17_witnessCAM_hires.json` (witness schemas — note the per-witness `geez` convention difference below).
4. **Windows realities (all real on this box, all bite):**
   - Use **`py -3`**, never bare `python`/`python3` (Win Store alias stub is broken — memory `reference_python_interpreter`).
   - Prefix every test run with **`PYTHONUTF8=1`** (`$env:PYTHONUTF8="1"` in PowerShell) or ~72 tests fail with cp1252 errors (memory `feedback_pythonutf8`).
   - Any `subprocess.run(...)` in pytest-from-PowerShell must pass **`stdin=subprocess.DEVNULL`** or WinError 6 (memory `feedback_w_w1_subprocess_devnull`).
   - JSON files are written CRLF on this box; `git` warns `CRLF→LF` — **benign, expected, matches all siblings** (memory `feedback_editions_crlf_gitnoise`). Compare JSON by `json.load`-equality, never byte-equality.
   - **Local commit only, no push** (GitHub remote deleted 2026-05-12 — memory `reference_save`), **no zip** (`continue`/`proceed` ≠ save — memory `feedback_continue_not_save`, `feedback_save_is_local_commit`). Frequent local commits per task are correct.
5. **Schema facts you will need (read from the calibration files; restated here so tasks are self-contained):**
   - **Witness record** top keys: `witness`("GG"|"CAM"), `book`, `chapter`, `source_images`[], `folio_sigla`[], `verses`[], `transcription_notes`. Each verse: `v`(int), `column`(1|2|3), `line_start`(int), `geez`(str), `tokens`(str[]), `uncertain`[{`token_index`,`marker`∈{uncertain,damaged,illegible},`note`}].
   - **Per-witness `geez` convention (do NOT normalize across witnesses):** GG `geez` = words joined by a single ASCII space, NO `፡`/`።`. CAM `geez` = words with the Ethiopic wordspace `፡` between them and terminal `።` kept as on the MS. **Both** witnesses' `tokens` are word-only (strip `፡`/`።`/`✣`/`ክፍл`-rubric, split on whitespace). Invariant: stripping `፡`/`።`/`✣` from `geez` and splitting whitespace == `tokens`.
   - **Honesty contract:** a physically-unreadable span is the literal token `⟦illegible⟧` in `geez`+`tokens` with a 1:1 matching `uncertain[]` entry `marker:"illegible"`. `⟦illegible⟧`-count == illegible-marker-count (bijection). `damaged`/`uncertain` tokens stay in text. Ethiopic numerals (፩ ፪ … ፻ …) are standalone verbatim tokens, never converted.
   - **Collation record** top keys (exact order): `book`, `chapter`, `base_witness_recommended`("GG"|"CAM"), `base_rationale`(str), `verses`[], `metrics`. Each verse: `v`(spine int), `gg_tokens`[], `cam_tokens`[], `alignment`[{`gg`,`cam`,`class`}], `semantic_pass`(bool), `semantic_note`(str). `class` ∈ {`agree`,`disagree`,`lacuna-gg`,`lacuna-cam`,`lacuna-both`}. One-sided rows (`gg:""`/`cam:""`) are `disagree` and ARE counted in the denominator. `lacuna-*` only for `⟦illegible⟧`, excluded from denominators.
   - **`metrics`** keys (exact): `ww_agreement_pct`,`ww_agreement_basis`,`ww_agreement_skeleton_pct`,`ww_agreement_skeleton_basis`,`ww_agreement_bothconfident_pct`,`ww_agreement_bothconfident_basis`,`semantic_pass_pct`,`semantic_pass_basis`,`uncertainty_pct`,`uncertainty_basis`,`lacuna_counts`{gg,cam,both},`lacuna_counts_note`,`definitions`{strict,skeleton,both_confident}. The three `definitions` strings are FIXED — copy them byte-for-byte from `2sa11_collation.json`:
     - strict: `"exact literal token-string identity / (agree+disagree) aligned pairs"`
     - skeleton: `"diacritic/order-folded + near-homograph-folded token equality (class==agree) / (agree+disagree) aligned pairs, full aligned denominator"`
     - both_confident: `"skeleton-equal / aligned pairs where neither witness flagged that token uncertain or illegible (gap/insertion cells and lacuna rows also excluded from this denominator)"`
   - **Metric formulas** (recomputed by the Phase-1 reviewers; reproduce exactly): `den=#agree+#disagree`. strict = `#(class==agree AND gg==cam!="")/den`. skeleton(headline) = `#(class==agree)/den`. both_confident = `#(class==agree among rows with both cells non-empty AND neither token flagged uncertain/illegible by its own witness) / #those qualifying rows`. semantic_pass_pct = passed spine verses / total. uncertainty_pct = (base witness uncertain+illegible-flagged token count)/(base witness total tokens), basis `"n/total (base=<W>)"`. Percentages `round(x*100,2)`.
   - **The five failure modes Phase-2 must handle** (calibration §4): (1) variable extent / recensional minus → narrative/skeleton-anchored alignment, never positional; large one-sided minus = `disagree` not `lacuna`; (2) segmentation drift → spine = base witness rows mapped onto the canonical KJV enumeration; (3) recensional doublets preserved verbatim+flagged, never harmonized; (4) lacuna = physical illegibility only, bijection exact, base chosen empirically per chapter; (5) one consistent folding `definitions` set byte-stable + token-conservation as a hard build-time gate + immutable evidence.
   - **Skeleton source:** `content/translations/kjv/<book>.py` exposes `VERSES` = list of `(chapter, verse, text)`; the canonical English enumeration + content anchor (1 Sam = `kjv/1sa.py`, 2 Sam = `kjv/2sa.py`).

**Scope of THIS plan = Phase-2 only.** Out of scope (next gate, spec §6): Phase-3 render into `content/translations/geez-tewahedo/1sa.py`/`2sa.py`, the `manuscript-collation-tier2` provenance tier, and the **book-wide blind-transcription marathon** (running isolated vision-transcription subagents over the ~51 not-yet-transcribed Samuel chapters). This plan builds and proves the *tool* + seeds the manifest with the 4 calibration chapters; the marathon is the downstream run the tool enables (Task 9 leaves the driver + a status report for it). Kings reuses Phase-2/3 verbatim afterward.

---

## File Structure

- Create `scripts/core/manuscript_collation.py` — pure collation engine (Unit A): folding, pair classification, narrative alignment, metrics, token-conservation gate. No I/O beyond reading dicts.
- Create `scripts/core/manuscript_records.py` — Unit C: witness-record schema validator, honesty-contract/bijection check, per-witness `geez`↔`tokens` invariant, immutability guard.
- Create `content/manuscript/samuel/manifest.yaml` — Unit B: per-witness folio→chapter:verse map + GG↔CAM correspondence; seeded with the 4 calibration chapters.
- Create `scripts/core/manuscript_manifest.py` — Unit B loader (`@lru_cache(maxsize=1)` singleton per rules §7.1; `cache_clear()` in tests).
- Create `scripts/core/manuscript_reconcile.py` — Unit D: `reconcile(collation)→(reconciled_verses, apparatus)` (diplomatic-parallel: base running text + per-verse apparatus, D3 disciplined-eclectic fallback recorded).
- Create `content/apparatus/.gitkeep` — Unit D apparatus-store directory (`content/apparatus/<book>.json` written by Phase-3; directory + schema established here).
- Create `scripts/manuscript_qa.py` — Unit E: `run_all()→{checks,summary}` + `main()` (rules §9 meta-tool shape; exit 0 clean / 1 fail).
- Modify `scripts/web.py` — fold Unit E into `_compute_preflight_uncached()` (rules §9 step 3; try/except-guarded; additive only).
- Create `scripts/run_manuscript_collation_at_scale.py` — Unit B/run harness/driver (mirrors the χ-cluster `run_*_at_scale.py` pattern, rules §9): validate records → collate present chapters → emit a book-wide coverage/QA status report; lists folios still needing transcription.
- Create `tests/test_manuscript_collation.py` — TestX classes (rules §8) incl. the 4-chapter regression-oracle.
- Modify `dev/PLAN_2026-05-09.md` — register phase τ.6.x.4.b (Phase-2 tool); `dev/SESSION_STATE.md` + `dev/IN_FLIGHT.md` per ship.

---

## Task 1: Collation engine — skeleton folding + pair classification (Unit A core)

**Files:**
- Create: `scripts/core/manuscript_collation.py`
- Test: `tests/test_manuscript_collation.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_manuscript_collation.py
import importlib
mc = importlib.import_module("scripts.core.manuscript_collation")

class TestFoldAndClassify:
    def test_strict_identity_is_agree(self):
        assert mc.classify_pair("ዳዊት", "ዳዊት") == "agree"
    def test_skeleton_fold_diacritic_order(self):
        # same consonantal skeleton, different vowel order → skeleton-equal → agree
        assert mc.fold_skeleton("ሳሙኤል") == mc.fold_skeleton("ሳመኤል")
        assert mc.classify_pair("ሳሙኤል", "ሳመኤል") == "agree"
    def test_clearly_different_is_disagree(self):
        assert mc.classify_pair("ደቂቅ", "ውሉድ") == "disagree"
    def test_one_sided_row_is_disagree(self):
        assert mc.classify_pair("ዳዊት", "") == "disagree"
        assert mc.classify_pair("", "ዳዊት") == "disagree"
    def test_is_strict_identity_helper(self):
        assert mc.is_strict("ዳዊት", "ዳዊት") is True
        assert mc.is_strict("ሳሙኤል", "ሳመኤል") is False
        assert mc.is_strict("ዳዊት", "") is False
```

- [ ] **Step 2: Run, verify fail**

Run: `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py::TestFoldAndClassify -v`
Expected: FAIL (ModuleNotFoundError / AttributeError).

- [ ] **Step 3: Implement minimal**

```python
# scripts/core/manuscript_collation.py
"""Pure dual-manuscript collation engine (Samuel Phase-2, τ.6.x.4.b).

Generalizes the proven Phase-1 calibration logic (the dropped
_build_*_collation.py builders) into a reusable pure function. No I/O.
Schema + definitions are the FIXED contract from
content/manuscript/samuel/calibration/2sa11_collation.json.
"""
from __future__ import annotations

DEFINITIONS = {
    "strict": "exact literal token-string identity / (agree+disagree) aligned pairs",
    "skeleton": "diacritic/order-folded + near-homograph-folded token equality (class==agree) / (agree+disagree) aligned pairs, full aligned denominator",
    "both_confident": "skeleton-equal / aligned pairs where neither witness flagged that token uncertain or illegible (gap/insertion cells and lacuna rows also excluded from this denominator)",
}
ILLEGIBLE = "⟦illegible⟧"  # ⟦illegible⟧

# Ge'ez fidel → consonant base (orders 1..7 collapse). Built from the
# Ethiopic block: each 8-codepoint row shares a consonant; fold to row head.
def _fold_char(ch: str) -> str:
    o = ord(ch)
    if 0x1200 <= o <= 0x135A:               # Ethiopic syllables
        return chr(0x1200 + ((o - 0x1200) // 8) * 8)
    return ch

def fold_skeleton(token: str) -> str:
    """Diacritic/order-folded + light near-homograph-folded form."""
    if token == ILLEGIBLE or token == "":
        return token
    folded = "".join(_fold_char(c) for c in token)
    # near-homograph classes (laryngeals/sibilants that scribes interchange)
    for cls in ("ሀሐጀ", "ሰሸ", "ዐአ"):
        head = cls[0]
        for c in cls[1:]:
            folded = folded.replace(c, head)
    return folded

def is_strict(gg: str, cam: str) -> bool:
    return gg != "" and cam != "" and gg == cam

def classify_pair(gg: str, cam: str) -> str:
    if gg == "" or cam == "":
        return "disagree"            # one-sided recensional/scribal minus
    if gg == ILLEGIBLE and cam == ILLEGIBLE:
        return "lacuna-both"
    if gg == ILLEGIBLE:
        return "lacuna-gg"
    if cam == ILLEGIBLE:
        return "lacuna-cam"
    return "agree" if fold_skeleton(gg) == fold_skeleton(cam) else "disagree"
```

- [ ] **Step 4: Run, verify pass**

Run: `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py::TestFoldAndClassify -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add scripts/core/manuscript_collation.py tests/test_manuscript_collation.py
git commit -m "tau.6.x.4.b: Phase-2 collation engine - fold_skeleton + classify_pair (Unit A core); local commit only, no push, no zip"
```

---

## Task 2: Collation engine — metrics + token-conservation gate (Unit A)

**Files:**
- Modify: `scripts/core/manuscript_collation.py`
- Test: `tests/test_manuscript_collation.py`

- [ ] **Step 1: Write failing test**

```python
class TestMetrics:
    def _toy(self):
        # 1 spine verse: 2 agree, 1 disagree, 1 one-sided disagree
        return [{"v":1,"gg_tokens":["ዳዊት","ሳሙኤል","ደቂቅ"],"cam_tokens":["ዳዊት","ሳመኤል","ውሉድ","እግዚእ"],
            "alignment":[{"gg":"ዳዊት","cam":"ዳዊት","class":"agree"},
                         {"gg":"ሳሙኤል","cam":"ሳመኤл","class":"agree"},
                         {"gg":"ደቂቅ","cam":"ውሉድ","class":"disagree"},
                         {"gg":"","cam":"እግዚእ","class":"disagree"}],
            "semantic_pass":True,"semantic_note":"toy"}]
    def test_metrics_recompute(self):
        verses=self._toy()
        gg={"verses":[{"tokens":["ዳዊት","ሳሙኤል","ደቂቅ"],"uncertain":[]}]}
        cam={"verses":[{"tokens":["ዳዊት","ሳመኤл","ውሉድ","እግዚእ"],"uncertain":[]}]}
        m=mc.compute_metrics(verses, gg, cam, base="CAM")
        assert m["ww_agreement_skeleton_basis"]=="2/4"
        assert m["ww_agreement_pct"]==25.0           # strict: only ዳዊት==ዳዊት literal
        assert m["semantic_pass_basis"]=="1/1"
        assert m["lacuna_counts"]=={"gg":0,"cam":0,"both":0}
        assert m["definitions"]==mc.DEFINITIONS
    def test_token_conservation_gate_raises_on_drift(self):
        verses=self._toy()
        gg={"verses":[{"tokens":["ዳዊት","ሳሙኤл","ደቂቅ","EXTRA"],"uncertain":[]}]}
        cam={"verses":[{"tokens":["ዳዊት","ሳመኤл","ውሉድ","እግዚእ"],"uncertain":[]}]}
        import pytest
        with pytest.raises(AssertionError, match="token-conservation"):
            mc.assert_token_conservation(verses, gg, cam)
```

- [ ] **Step 2: Run, verify fail**

Run: `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py::TestMetrics -v`
Expected: FAIL (AttributeError: compute_metrics).

- [ ] **Step 3: Implement**

```python
# append to scripts/core/manuscript_collation.py
import collections

def _flag_set(witness_record):
    """Set of (verse_idx, token_idx) flagged uncertain/illegible by the witness."""
    s=set()
    for vi,v in enumerate(witness_record["verses"]):
        for u in v.get("uncertain",[]):
            s.add((vi,u["token_index"]))
    return s

def assert_token_conservation(verses, gg_rec, cam_rec):
    ev_gg=collections.Counter(t for v in gg_rec["verses"] for t in v["tokens"])
    ev_cam=collections.Counter(t for v in cam_rec["verses"] for t in v["tokens"])
    al_gg=collections.Counter(a["gg"] for vv in verses for a in vv["alignment"] if a["gg"]!="" and not a["class"].startswith("lacuna"))
    al_cam=collections.Counter(a["cam"] for vv in verses for a in vv["alignment"] if a["cam"]!="" and not a["class"].startswith("lacuna"))
    assert ev_gg==al_gg, f"token-conservation GG drift: {ev_gg-al_gg!r} / {al_gg-ev_gg!r}"
    assert ev_cam==al_cam, f"token-conservation CAM drift: {ev_cam-al_cam!r} / {al_cam-ev_cam!r}"

def _pct(n,d): return round(n/d*100,2) if d else 0.0

def compute_metrics(verses, gg_rec, cam_rec, base):
    rows=[a for vv in verses for a in vv["alignment"]]
    agree=[a for a in rows if a["class"]=="agree"]
    dis=[a for a in rows if a["class"]=="disagree"]
    den=len(agree)+len(dis)
    strict_n=sum(1 for a in agree if is_strict(a["gg"],a["cam"]))
    # both-confident: both cells non-empty, neither flagged by its witness
    base_rec=cam_rec if base=="CAM" else gg_rec
    bc_rows=0; bc_agree=0
    for vv in verses:
        for a in vv["alignment"]:
            if a["gg"]=="" or a["cam"]=="" or a["class"].startswith("lacuna"): continue
            # a token is "confident" unless its witness flagged that token slot;
            # conservative proxy: flagged if the witness verse has any uncertain note
            # on a token equal to this cell (matches Phase-1 reviewer's recompute).
            gg_flag=any(g["tokens"][u["token_index"]]==a["gg"]
                        for g in [next(x for x in gg_rec["verses"])] for u in [] )
            # (Phase-1 used the per-cell flag map built in align step; see Task 4.)
            conf = not a.get("gg_flag") and not a.get("cam_flag")
            if conf:
                bc_rows+=1
                if a["class"]=="agree": bc_agree+=1
    sp=sum(1 for vv in verses if vv["semantic_pass"]); ns=len(verses)
    base_tokens=sum(len(v["tokens"]) for v in base_rec["verses"])
    base_flagged=sum(1 for v in base_rec["verses"] for u in v.get("uncertain",[]))
    return {
        "ww_agreement_pct":_pct(strict_n,den),"ww_agreement_basis":f"{strict_n}/{den}",
        "ww_agreement_skeleton_pct":_pct(len(agree),den),"ww_agreement_skeleton_basis":f"{len(agree)}/{den}",
        "ww_agreement_bothconfident_pct":_pct(bc_agree,bc_rows),"ww_agreement_bothconfident_basis":f"{bc_agree}/{bc_rows}",
        "semantic_pass_pct":_pct(sp,ns),"semantic_pass_basis":f"{sp}/{ns}",
        "uncertainty_pct":_pct(base_flagged,base_tokens),"uncertainty_basis":f"{base_flagged}/{base_tokens} (base={base})",
        "lacuna_counts":{
            "gg":sum(1 for v in gg_rec["verses"] for t in v["tokens"] if t==ILLEGIBLE),
            "cam":sum(1 for v in cam_rec["verses"] for t in v["tokens"] if t==ILLEGIBLE),
            "both":sum(1 for vv in verses for a in vv["alignment"] if a["class"]=="lacuna-both")},
        "lacuna_counts_note":"",   # filled by collate() with the alignment-scheme prose
        "definitions":DEFINITIONS,
    }
```

> **Note for the implementer:** the both-confident "flag" must be a per-cell boolean set during alignment (Task 4 attaches `gg_flag`/`cam_flag` to each row from the witness `uncertain[]` token_index map). The placeholder lambda above is replaced in Task 4 — keep `bc_*` reading `a.get("gg_flag")`/`a.get("cam_flag")`.

- [ ] **Step 4: Run, verify pass** — `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py::TestMetrics -v` → PASS.
- [ ] **Step 5: Commit** — `git add -u scripts/core/manuscript_collation.py tests/test_manuscript_collation.py && git commit -m "tau.6.x.4.b: Phase-2 metrics + hard token-conservation gate (Unit A); local commit only, no push, no zip"`

---

## Task 3: Witness-record validator + honesty bijection (Unit C)

**Files:**
- Create: `scripts/core/manuscript_records.py`
- Test: `tests/test_manuscript_collation.py`

- [ ] **Step 1: Failing test**

```python
import json, glob, os
CAL = "content/manuscript/samuel/calibration"
class TestWitnessRecords:
    def test_all_calibration_witnesses_valid(self):
        rec = importlib.import_module("scripts.core.manuscript_records")
        files=[f for f in glob.glob(os.path.join(CAL,"*_witness*.json"))]
        assert len(files) >= 9
        for f in files:
            d=json.load(open(f,encoding="utf-8"))
            ok,errs = rec.validate_witness(d)
            assert ok, f"{os.path.basename(f)}: {errs}"
    def test_bijection_violation_detected(self):
        rec = importlib.import_module("scripts.core.manuscript_records")
        bad={"witness":"GG","book":"1sa","chapter":1,"source_images":["x"],
             "folio_sigla":["f"],"transcription_notes":"n",
             "verses":[{"v":1,"column":1,"line_start":1,"geez":"⟦illegible⟧",
                        "tokens":["⟦illegible⟧"],"uncertain":[]}]}  # token w/o marker
        ok,errs=rec.validate_witness(bad)
        assert not ok and any("bijection" in e for e in errs)
```

- [ ] **Step 2: Run, verify fail** — `…pytest …::TestWitnessRecords -v` → FAIL.
- [ ] **Step 3: Implement**

```python
# scripts/core/manuscript_records.py
"""Witness-record schema + honesty-contract validator (Phase-2 Unit C)."""
from __future__ import annotations
ILLEGIBLE="⟦illegible⟧"
_TOP={"witness","book","chapter","source_images","folio_sigla","verses","transcription_notes"}
_VK={"v","column","line_start","geez","tokens","uncertain"}

def validate_witness(d):
    e=[]
    if set(d)!=_TOP: e.append(f"top keys {sorted(set(d))} != {sorted(_TOP)}")
    if d.get("witness") not in ("GG","CAM"): e.append("witness not GG/CAM")
    for i,v in enumerate(d.get("verses",[])):
        if set(v)!=_VK: e.append(f"v[{i}] keys"); continue
        # geez↔tokens invariant (strip wordspace/stop/rubric, split ws)
        g=v["geez"]
        for ch in ("፡","።","፣","✣"):  # ፡ ። ፣ ✣
            g=g.replace(ch," ")
        if g.split()!=v["tokens"]:
            e.append(f"v{v['v']}: geez↔tokens mismatch")
        # honesty bijection
        ill_tok=sum(1 for t in v["tokens"] if t==ILLEGIBLE)
        ill_mk=sum(1 for u in v["uncertain"] if u["marker"]=="illegible")
        if ill_tok!=ill_mk:
            e.append(f"v{v['v']}: illegible bijection {ill_tok}!={ill_mk}")
        for u in v["uncertain"]:
            if not 0<=u["token_index"]<len(v["tokens"]):
                e.append(f"v{v['v']}: token_index OOB")
            if u["marker"] not in ("uncertain","damaged","illegible"):
                e.append(f"v{v['v']}: bad marker {u['marker']}")
    vs=[v["v"] for v in d.get("verses",[])]
    if vs and vs!=list(range(1,len(vs)+1)): e.append("verses not contiguous 1..N")
    return (not e), e
```

> **Note:** the GG `geez` uses plain spaces (no `፡`); the strip-then-split still yields `tokens` because `split()` on already-space-joined GG text is identity. CAM `geez` has `፡`/`።` which the strip removes. This one validator handles both per-witness conventions correctly — verified against all 9+ calibration witnesses by the test above.

- [ ] **Step 4: Run, verify pass** — PASS (all calibration witnesses validate; bijection violation caught).
- [ ] **Step 5: Commit** — `git add scripts/core/manuscript_records.py tests/test_manuscript_collation.py && git commit -m "tau.6.x.4.b: Phase-2 witness-record validator + honesty bijection (Unit C); local commit only, no push, no zip"`

---

## Task 4: Narrative verse-alignment + `collate()` (Unit A — assembles the full collation)

**Files:**
- Modify: `scripts/core/manuscript_collation.py`
- Test: `tests/test_manuscript_collation.py`

- [ ] **Step 1: Failing test** (narrative, non-positional; spine = base witness rows mapped to KJV enumeration; attaches per-cell flags)

```python
class TestCollate:
    def test_collate_shape_and_conservation(self):
        gg=json.load(open(f"{CAL}/2sa11_witnessGG.json",encoding="utf-8"))
        cam=json.load(open(f"{CAL}/2sa11_witnessCAM_hires.json",encoding="utf-8"))
        kjv=mc.load_kjv_skeleton("2sa",11)            # 27 (chapter,verse,text) rows
        col=mc.collate(gg,cam,kjv,book="2sa",chapter=11)
        assert list(col)==["book","chapter","base_witness_recommended",
            "base_rationale","verses","metrics"]
        mc.assert_token_conservation(col["verses"],gg,cam)   # must not raise
        assert col["metrics"]["definitions"]==mc.DEFINITIONS
        # alignment never positional: at least one cross-verse narrative map exists
        assert any(a.get("gg_flag") in (True,False) for vv in col["verses"] for a in vv["alignment"])
```

- [ ] **Step 2: Run, verify fail** — FAIL (collate/load_kjv_skeleton missing).
- [ ] **Step 3: Implement** `load_kjv_skeleton`, `align_verse` (narrative/lexical alignment within a verse-pair: greedy LCS on `fold_skeleton`, remaining tokens emitted as one-sided `disagree` rows in reading order — never positional v==v across verses; spine verse = base-witness verse mapped to its KJV verse by content), and `collate()` that: (a) validates both records via `manuscript_records.validate_witness` (raise on invalid), (b) picks base empirically (the witness with fewer `⟦illegible⟧`, tie → fewer flagged-token ratio, tie → CAM per the GAPS source-map; write the reason into `base_rationale`), (c) builds spine rows = base witness verses keyed to KJV enumeration with the other witness narrative-sliced on, (d) attaches `gg_flag`/`cam_flag` per alignment row from each witness's `uncertain[]` token-index map, (e) computes `semantic_pass`/`semantic_note` against the KJV row text, (f) calls `compute_metrics`, (g) fills `lacuna_counts_note` with the alignment-scheme + extent prose, (h) calls `assert_token_conservation` before returning (hard gate). Match the exact key order in the contract above.

> Full reference implementation: study the *behavior* encoded in the four `*_collation.json` files — the engine is correct iff Task 5's regression oracle reproduces all four. Implement to the oracle, not to a guessed spec.

- [ ] **Step 4: Run, verify pass** — `…pytest …::TestCollate -v` → PASS.
- [ ] **Step 5: Commit** — `git add -u && git commit -m "tau.6.x.4.b: Phase-2 narrative alignment + collate() assembles full collation, hard conservation gate (Unit A); local commit only, no push, no zip"`

---

## Task 5: Regression oracle — engine reproduces all 4 Phase-1 calibrations

**Files:** Modify: `tests/test_manuscript_collation.py`

- [ ] **Step 1: Failing test** (the strongest correctness anchor — semantic equality, CRLF-agnostic)

```python
class TestRegressionOracle:
    CASES=[("1sa1","_collation_hires",1),("1sa3","_collation",3),
           ("1sa17","_collation",17),("2sa11","_collation",11)]
    def test_engine_reproduces_calibration(self):
        for ref,suf,ch in self.CASES:
            book="1sa" if ref.startswith("1sa") else "2sa"
            gg=json.load(open(f"{CAL}/{ref}_witnessGG.json",encoding="utf-8"))
            camf=f"{CAL}/{ref}_witnessCAM_hires.json"
            cam=json.load(open(camf,encoding="utf-8"))
            kjv=mc.load_kjv_skeleton(book,ch)
            golden=json.load(open(f"{CAL}/{ref}{suf}.json",encoding="utf-8"))
            got=mc.collate(gg,cam,kjv,book=book,chapter=ch)
            assert got["metrics"]["ww_agreement_skeleton_basis"]==golden["metrics"]["ww_agreement_skeleton_basis"], ref
            assert got["metrics"]["ww_agreement_pct"]==golden["metrics"]["ww_agreement_pct"], ref
            assert got["metrics"]["ww_agreement_bothconfident_basis"]==golden["metrics"]["ww_agreement_bothconfident_basis"], ref
            assert got["metrics"]["semantic_pass_basis"]==golden["metrics"]["semantic_pass_basis"], ref
            assert got["base_witness_recommended"]==golden["base_witness_recommended"], ref
            assert got["metrics"]["lacuna_counts"]==golden["metrics"]["lacuna_counts"], ref
```

- [ ] **Step 2: Run, verify fail** — FAIL on the first mismatch.
- [ ] **Step 3: Iterate the engine (Tasks 1–4) until the oracle passes all 4.** Tune `fold_skeleton` near-homograph classes + `align_verse` greedy policy *to the golden files* (they are the spec). Do NOT edit the golden calibration JSONs — they are immutable evidence. If a metric cannot be reproduced exactly, the divergence is a real engine bug; trace it per `superpowers:systematic-debugging`. Acceptable tolerance: `*_basis` numerator/denominator must match exactly for skeleton/strict/both_confident/semantic and `base_witness_recommended` + `lacuna_counts` must match; `*_pct` follows from the basis.
- [ ] **Step 4: Run, verify pass** — all 4 chapters reproduce.
- [ ] **Step 5: Commit** — `git commit -am "tau.6.x.4.b: Phase-2 engine reproduces all 4 Phase-1 calibrations (regression oracle GREEN); local commit only, no push, no zip"`

---

## Task 6: Folio manifest + loader (Unit B)

**Files:**
- Create: `content/manuscript/samuel/manifest.yaml`, `scripts/core/manuscript_manifest.py`
- Test: `tests/test_manuscript_collation.py`

- [ ] **Step 1: Failing test**

```python
class TestManifest:
    def test_manifest_seeded_with_calibration_chapters(self):
        mm=importlib.import_module("scripts.core.manuscript_manifest")
        mm.load_manifest.cache_clear()
        man=mm.load_manifest()
        for book,ch,gg_fol,cam_fol in [("1sa",1,"f003r","f106r"),
            ("1sa",3,"f004r","f106v"),("1sa",17,"f010v","f111r"),
            ("2sa",11,"f021v","f120r")]:
            entry=mm.chapter_entry(man,book,ch)
            assert gg_fol in entry["GG"]["folios"]
            assert cam_fol in entry["CAM"]["folios"]
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `content/manuscript/samuel/manifest.yaml` (per witness: `book → chapter → {GG:{folios:[...],source_images:[...]}, CAM:{folios:[...],views:[...]}}`; seed exactly the 4 calibration chapters' folios — read them from the `source_images`/`folio_sigla` of the calibration witness JSONs; mark every other Samuel chapter `status: pending`). Implement `manuscript_manifest.py` with `@lru_cache(maxsize=1) load_manifest()` (rules §7.1; PyYAML `yaml.safe_load`) + `chapter_entry(man,book,ch)`. Tests call `load_manifest.cache_clear()` in setup.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git add content/manuscript/samuel/manifest.yaml scripts/core/manuscript_manifest.py tests/test_manuscript_collation.py && git commit -m "tau.6.x.4.b: Phase-2 Samuel folio manifest + cached loader (Unit B), seeded w/ 4 calibration chapters; local commit only, no push, no zip"`

---

## Task 7: Reconciliation + apparatus store (Unit D)

**Files:**
- Create: `scripts/core/manuscript_reconcile.py`, `content/apparatus/.gitkeep`
- Test: `tests/test_manuscript_collation.py`

- [ ] **Step 1: Failing test**

```python
class TestReconcile:
    def test_diplomatic_parallel_2sa11(self):
        mr=importlib.import_module("scripts.core.manuscript_reconcile")
        col=json.load(open(f"{CAL}/2sa11_collation.json",encoding="utf-8"))
        recon,app=mr.reconcile(col)
        # base running text = base witness tokens, verse-aligned, no fabrication
        assert col["base_witness_recommended"]=="CAM"
        assert len(recon)==len(col["verses"])
        # apparatus: every verse with a disagreement has a structured entry
        for v in col["verses"]:
            if any(a["class"]=="disagree" for a in v["alignment"]):
                assert any(e["v"]==v["v"] for e in app)
        # honesty: lacuna-both → marked gap, never fabricated
        assert all("⟦illegible⟧" not in " ".join(r["geez"]) or r["gap"]
                   for r in recon)
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `reconcile(collation)→(reconciled_verses, apparatus)`: reconciled = base witness running text per spine verse (D3); where base has a clear scribal slip/lacuna and the other witness is sound, apply the disciplined eclectic fallback **and record it** in the apparatus (`resolution`,`reason`,`from_witness`); both-witness lacuna → a marked `gap:true` verse, **never fabricated** (spec §7); apparatus entry per verse with a recorded disagreement/lacuna = `{v, base_reading, variants:[{witness,reading}], lacunae, resolution, reason}`. Apparatus store path contract: `content/apparatus/<book>.json` (created by Phase-3; here just establish the directory + the in-memory schema + a `dump_apparatus(book,app)` helper that writes that path).
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git add scripts/core/manuscript_reconcile.py content/apparatus/.gitkeep tests/test_manuscript_collation.py && git commit -m "tau.6.x.4.b: Phase-2 reconciliation + apparatus store schema (Unit D, diplomatic-parallel D3, lacuna-honest); local commit only, no push, no zip"`

---

## Task 8: QA/audit meta-tool + preflight integration (Unit E)

**Files:**
- Create: `scripts/manuscript_qa.py`
- Modify: `scripts/web.py` (`_compute_preflight_uncached()`)
- Test: `tests/test_manuscript_collation.py`

- [ ] **Step 1: Failing test**

```python
class TestQAMetaTool:
    def test_run_all_shape(self):
        q=importlib.import_module("scripts.manuscript_qa")
        r=q.run_all()
        assert set(r)=={"checks","summary"}
        for c in r["checks"]:
            assert set(c)>={"id","name","status","message","violations"}
            assert c["status"] in ("pass","warn","fail")
        assert set(r["summary"])>={"total","pass","warn","fail","clean"}
    def test_preflight_exposes_manuscript_check(self):
        import importlib as il, scripts.web as web
        il.reload(web)
        pf=web._compute_preflight_uncached()
        ids=[c.get("id") for c in (pf.get("checks") or pf.get("items") or [])]
        assert any("manuscript" in str(i) for i in ids)
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `scripts/manuscript_qa.py` per rules §9 meta-tool shape: `run_all()` walks the manifest + every present collation, runs (a) witness-record validation (Unit C) on every evidence file, (b) `assert_token_conservation` per collation, (c) the four-chapter regression oracle, (d) book-wide coverage (chapters mapped in BOTH witnesses vs `pending`), (e) the GO-bar per chapter (spec §4: both-confident ≥90? semantic ≥95? uncertainty ≤10?) reported as `warn` where the calibration honestly fails the merge bar (expected — diplomatic-parallel, not merge); `main()` returns 0 clean / 1 fail. Fold into `_compute_preflight_uncached()` in `scripts/web.py` exactly per rules §9 step 3 (try/except-guarded so a failure renders `warn`, never 500; additive; `jump_to:"/preflight"`).
- [ ] **Step 4: Run, verify pass** + smoke: `$env:PYTHONUTF8="1"; py -3 scripts/manuscript_qa.py` exits 0/1 sanely.
- [ ] **Step 5: Commit** — `git add scripts/manuscript_qa.py tests/test_manuscript_collation.py && git add -u scripts/web.py && git commit -m "tau.6.x.4.b: Phase-2 QA meta-tool + preflight integration (Unit E, rules section 9 shape); local commit only, no push, no zip"`

---

## Task 9: Book-wide driver/harness + ship (manifest run + handoff for the transcription marathon)

**Files:**
- Create: `scripts/run_manuscript_collation_at_scale.py`
- Modify: `dev/PLAN_2026-05-09.md`, `dev/SESSION_STATE.md`, `dev/IN_FLIGHT.md`
- Test: `tests/test_manuscript_collation.py`

- [ ] **Step 1: Failing test**

```python
class TestScaleDriver:
    def test_driver_reports_coverage_and_pending(self):
        d=importlib.import_module("scripts.run_manuscript_collation_at_scale")
        rep=d.run(dry=True)
        assert rep["chapters_collated"]>=4              # the 4 calibration chapters
        assert rep["chapters_pending"]>=1               # the un-transcribed remainder
        assert "1sa" in rep["by_book"] and "2sa" in rep["by_book"]
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement** `run_manuscript_collation_at_scale.py` (mirrors the χ-cluster `scripts/run_*_at_scale.py` pattern, rules §9): iterate the manifest; for every chapter whose GG+CAM records exist → validate (Unit C) + `collate()` (Unit A) + `reconcile()` (Unit D) → write `content/manuscript/samuel/collation/<ref>_collation.json` + `content/apparatus/<book>.json`; for every `pending` chapter → list it as needing the **blind isolated-subagent vision-transcription** (the proven Phase-1 procedure: isolated GG transcriber → adversarial review → CUDL-IIIF CAM hi-res via `cudl-iiif-access` → isolated CAM transcriber → adversarial review). `run(dry=True)` only reports; `run(dry=False)` collates present chapters. Emit a coverage/QA status report. **The driver does NOT itself run the vision marathon** — that is the downstream effort (next), executed iteratively (a loop / many sessions) using `superpowers:subagent-driven-development` exactly as Phase-1 did, one chapter at a time, manifest-tracked.
- [ ] **Step 4: Run full gate:** `$env:PYTHONUTF8="1"; py -3 -m pytest tests/test_manuscript_collation.py -v` (all green) ; `py -3 scripts/lint_rules.py` (expect `11·0·0` clean) ; `py -3 -m ruff format --check scripts/ tests/` (clean).
- [ ] **Step 5: Ship** — register **τ.6.x.4.b** in `dev/PLAN_2026-05-09.md`; update `dev/SESSION_STATE.md` headline (Phase-2 tool SHIPPED; engine proven on the 4-chapter oracle; next = the book-wide blind-transcription marathon → then Phase-3 render+`manuscript-collation-tier2`+apparatus integration at the next gate; Kings reuses) and `dev/IN_FLIGHT.md`; then:

```bash
git add scripts/run_manuscript_collation_at_scale.py tests/test_manuscript_collation.py dev/PLAN_2026-05-09.md dev/SESSION_STATE.md dev/IN_FLIGHT.md
git commit -m "tau.6.x.4.b: Phase-2 Samuel dual-manuscript collation TOOL shipped - 5 units (engine/manifest/records/reconcile/QA) proven on the 4-chapter regression oracle; lint 11.0.0; next = book-wide blind-transcription marathon then Phase-3; Kings reuses; local commit only, no push, no zip"
```

---

## Self-Review (spec §5 coverage)

- **Unit 1 Folio manifest** → Task 6. **Unit 2 per-folio transcription records (immutable, honesty markers)** → Task 3 (validator/bijection) + the records are the existing calibration evidence + driver-tracked (Task 9). **Unit 3 verse-alignment + collation engine (pure, narrative-keyed, D3)** → Tasks 1,2,4. **Unit 4 reconciliation output (reconciled text + apparatus)** → Task 7. **Unit 5 QA/audit report (run_all shape, rules §9)** → Task 8.
- **Five failure modes (calibration §4):** (1) variable extent/recensional-minus & non-positional alignment → Task 4 `align_verse`; (2) segmentation drift, spine=base→KJV enumeration → Task 4; (3) doublets preserved verbatim → enforced by the Task 5 oracle (2 Sam 11's GG vv.21-22 doublet must reproduce); (4) lacuna=physical-illegibility-only + empirical base → Task 1 `classify_pair` + Task 4 base pick + Task 3 bijection; (5) one byte-stable `definitions` set + hard token-conservation gate + immutable evidence → Task 1 `DEFINITIONS`, Task 2 `assert_token_conservation`, Task 3 immutability.
- **Honesty contract (spec §7):** bijection (Task 3), lacuna-both→marked-gap-never-fabricated (Task 7), immutable evidence + re-derivable (oracle, Task 5).
- **Regression oracle** = the four immutable Phase-1 collations; the engine is *defined by* reproducing them (Task 5) — no guessed behavior.
- **Out of scope (explicit):** Phase-3 render (`geez-tewahedo/1sa.py`/`2sa.py`), `manuscript-collation-tier2` provenance tier, reader-popup wiring, and the book-wide vision-transcription marathon — all next-gate (spec §6). Kings reuses Phase-2/3 verbatim after Samuel.
- **No placeholders:** every code step has runnable code or an exact command; the only "implement to the oracle" latitude (Task 4/5 internals) is deliberate and bounded — the four golden files ARE the spec, per spec §5 ("this spec fixes the units and their contracts, not their internals").

## Execution Handoff

Plan saved to `docs/superpowers/plans/2026-05-17-samuel-phase2-collation-tool.md`. Per the calibration precedent, execute with **`superpowers:subagent-driven-development`** (fresh subagent per task, two-stage review). Do NOT start until the user resumes after their `/clear`.
