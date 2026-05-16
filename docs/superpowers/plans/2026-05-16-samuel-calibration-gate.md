# Samuel Calibration Gate (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the 1 Samuel 1 calibration report — two independent witness transcriptions, the three honest metrics, a recommended base witness, and an explicit GO/NO-GO recommendation — so the user can gate the Samuel/Kings dual-manuscript collation project.

**Architecture:** A manual vision-transcription pilot. The model reads the cropped folio images of 1 Samuel 1 from both Samuel witnesses, transcribes each independently into a structured JSON evidence file, semantically cross-checks against the project's known/English Samuel, collates the two witnesses, computes three measurable metrics, recommends the base witness, and writes a calibration report for the user's structural eyeball + GO/NO-GO. **No reusable production code is built** — this is Approach A (de-risk before tooling), per spec §3/§4.

**Tech Stack:** Vision transcription (model reading JPGs via the Read tool); hand-authored JSON evidence files (the project's `content/**/*.json` data convention; `json`/`ast`-readable); a Markdown report (the project's `dev/` report convention); local git commit. No new dependencies. No Python modules, no tests, no Tesseract.

**Scope:** Phase 1 ONLY. Phases 2-3 (the collation tool + render) get a separate plan written **after** a GO, sized to the calibration findings — per spec §5 ("sized to what Phase 1 reveals"). Detailing them now would be placeholder guesswork and is deliberately excluded.

**Spec:** `docs/superpowers/specs/2026-05-16-samuel-kings-dual-manuscript-collation-design.md`

---

## File structure (Phase 1 produces only data + a report — no production code)

- Create: `content/manuscript/samuel/calibration/1sa1_witnessGG.json` — Witness GG (GG 00106) transcription evidence.
- Create: `content/manuscript/samuel/calibration/1sa1_witnessCAM.json` — Witness CAM (Cambridge Add.1570) transcription evidence.
- Create: `content/manuscript/samuel/calibration/1sa1_collation.json` — W↔W collation + per-verse semantic judgments + metric tallies.
- Create: `dev/CALIBRATION_2026-05-16-samuel-1sa1.md` — the human-facing calibration report (the GO/NO-GO deliverable; mirrors the project's `dev/AUDIT_*.md` convention).
- No `scripts/`, no `tests/` changes (Approach A: no tooling in Phase 1).

### Evidence JSON schema (defined once; used identically in Tasks 2 & 4)

```json
{
  "witness": "GG",
  "book": "1sa",
  "chapter": 1,
  "source_images": ["GAPS/Samuel/01_1-Samuel/1-Samuel_f003r.jpg"],
  "folio_sigla": ["f003r"],
  "verses": [
    {
      "v": 1,
      "geez": "<verbatim transcribed Ge'ez of verse 1>",
      "tokens": ["<word1>", "<word2>"],
      "uncertain": [
        {"token_index": 1, "marker": "damaged", "note": "ink loss on right edge"}
      ],
      "column": 1,
      "line_start": 3
    }
  ],
  "transcription_notes": "free text: hand, damage, layout, ch.1->ch.2 boundary"
}
```

`marker` ∈ `"damaged" | "illegible" | "uncertain"`. `witness` ∈ `"GG" | "CAM"`. `tokens` is the whitespace-split word list of `geez` (rubric/punctuation stripped); `uncertain[].token_index` is 0-based into `tokens`.

### Collation JSON schema (defined once; produced in Task 6, consumed in Task 8)

```json
{
  "book": "1sa",
  "chapter": 1,
  "base_witness_recommended": "GG",
  "base_rationale": "<why>",
  "verses": [
    {
      "v": 1,
      "gg_tokens": ["..."],
      "cam_tokens": ["..."],
      "alignment": [
        {"gg": "<tok>", "cam": "<tok>", "class": "agree"}
      ],
      "semantic_pass": true,
      "semantic_note": "<matches known 1 Sam 1:1: Elkanah of Ramathaim>"
    }
  ],
  "metrics": {
    "ww_agreement_pct": 0.0,
    "ww_agreement_basis": "<agree>/<aligned>",
    "semantic_pass_pct": 0.0,
    "semantic_pass_basis": "<pass>/<total verses>",
    "uncertainty_pct": 0.0,
    "uncertainty_basis": "<flagged>/<total base tokens>"
  }
}
```

`class` ∈ `"agree" | "disagree" | "lacuna-gg" | "lacuna-cam" | "lacuna-both"`.

---

### Task 1: Locate 1 Samuel 1 in Witness GG

**Files:** none created (observation task feeding Task 2).

- [ ] **Step 1: View the opening GG folios**

Read these images in order until 1 Samuel 1 is found and its end (start of ch.2) is seen:
`GAPS/Samuel/01_1-Samuel/1-Samuel_f003r.jpg`, then `_f003v.jpg`, `_f004r.jpg`, `_f004v.jpg`, `_f005r.jpg` (continue only if ch.1 has not ended).

- [ ] **Step 2: Identify the chapter-1 span**

1 Samuel 1 is the Hannah narrative — recognisable content: Elkanah of Ramathaim; two wives Hannah and Peninnah; the yearly pilgrimage to Shiloh; Eli the priest and his sons Hophni and Phinehas; Hannah's vow and prayer; Samuel's birth and naming; the weaning and dedication at Shiloh. Identify the folio siglum, column, and line where ch.1 begins, and where ch.1 ends / ch.2 (Hannah's song, "My heart exults") begins.

Expected: a concrete record like "1 Sam 1 spans f003r col.1 line 3 → f003v col.2 line ~18; ch.2 begins f003v col.2." Hold this for Task 2's `source_images`, `folio_sigla`, `column`, `line_start`, and `transcription_notes`.

---

### Task 2: Transcribe 1 Samuel 1 from Witness GG (independently)

**Files:**
- Create: `content/manuscript/samuel/calibration/1sa1_witnessGG.json`

- [ ] **Step 1: Vision-transcribe every verse of ch.1 from the GG image(s)**

Transcribe verbatim, verse by verse, from the image(s) identified in Task 1. Do **not** open or consult any Witness-CAM image (independence is the whole point of the metric). For any glyph/word that is damaged, faded, illegible, or you are unsure of, still produce your best reading **and** add an `uncertain[]` entry with the right `marker`. Strip red-rubric section markers and manuscript punctuation from `tokens` (keep them out of the word list) but you may keep them in `geez` if useful.

- [ ] **Step 2: Write the evidence file**

Create `content/manuscript/samuel/calibration/1sa1_witnessGG.json` using the Evidence JSON schema above. `witness` = `"GG"`, `book` = `"1sa"`, `chapter` = `1`. Fill `source_images`/`folio_sigla` from Task 1. One `verses[]` entry per verse, contiguous from `v: 1`.

- [ ] **Step 3: Verify it is well-formed**

Run: `cd "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4" && PYTHONUTF8=1 py -3 -c "import json; d=json.load(open('content/manuscript/samuel/calibration/1sa1_witnessGG.json',encoding='utf-8')); vs=[x['v'] for x in d['verses']]; assert d['witness']=='GG' and d['book']=='1sa' and d['chapter']==1; assert vs==list(range(1,vs[-1]+1)), vs; print('GG verses:',len(vs),'last v:',vs[-1])"`

Expected: PASS — prints e.g. `GG verses: 20 last v: 20` (count is whatever the manuscript actually has; the assertion only requires contiguous numbering from 1).

---

### Task 3: Locate 1 Samuel 1 in Witness CAM

**Files:** none created (observation task feeding Task 4).

- [ ] **Step 1: View the opening CAM crops**

Read in order until 1 Sam 1 is found and its end is seen:
`GAPS/Samuel/1-2_Samuel__Cambridge_Add1570/Samuel1.jpg`, then `Samuel2.jpg`, `Samuel3.jpg`, `Samuel4.jpg` (continue only if needed).

- [ ] **Step 2: Identify the chapter-1 span (same content markers as Task 1 Step 2)**

Record which `SamuelN.jpg` crop(s) contain 1 Sam ch.1, and the column/line where it begins and ends. Note: the CAM hand is denser and carries marginalia — ignore the side-margin notes for this pilot (marginalia is out of scope, spec §2). Hold this for Task 4.

Expected: a concrete record like "1 Sam 1 spans Samuel1.jpg col.1 → Samuel2.jpg col.1."

---

### Task 4: Transcribe 1 Samuel 1 from Witness CAM (independently)

**Files:**
- Create: `content/manuscript/samuel/calibration/1sa1_witnessCAM.json`

- [ ] **Step 1: Vision-transcribe every verse of ch.1 from the CAM image(s)**

Same procedure as Task 2 Step 1, on the CAM image(s) from Task 3. Do **not** re-open or consult the GG images or `1sa1_witnessGG.json` while doing this — transcribe CAM purely from its own pages so the two transcriptions are genuinely independent.

- [ ] **Step 2: Write the evidence file**

Create `content/manuscript/samuel/calibration/1sa1_witnessCAM.json` using the Evidence JSON schema. `witness` = `"CAM"`, `book` = `"1sa"`, `chapter` = `1`. Fill `source_images`/`folio_sigla` (the `SamuelN.jpg` names) from Task 3.

- [ ] **Step 3: Verify it is well-formed**

Run: `cd "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4" && PYTHONUTF8=1 py -3 -c "import json; d=json.load(open('content/manuscript/samuel/calibration/1sa1_witnessCAM.json',encoding='utf-8')); vs=[x['v'] for x in d['verses']]; assert d['witness']=='CAM' and d['book']=='1sa' and d['chapter']==1; assert vs==list(range(1,vs[-1]+1)), vs; print('CAM verses:',len(vs),'last v:',vs[-1])"`

Expected: PASS — prints `CAM verses: N last v: N` with contiguous numbering from 1.

---

### Task 5: Semantic-skeleton check

**Files:** none created yet (judgments are recorded in Task 6's collation file).

- [ ] **Step 1: Read the project's known Samuel reference**

Read `content/notes/1sa.py` (the project's existing 1 Samuel material) and recall the well-known 1 Samuel 1 narrative as the semantic skeleton.

- [ ] **Step 2: Judge each verse**

For every verse 1..N, decide `semantic_pass` = true/false: does the transcribed Ge'ez (use the more-complete witness as the primary read for this judgment) plausibly **mean** what 1 Samuel 1:v is known to say? Write a one-line `semantic_note` per verse stating the matched content (e.g. `"v.1 = Elkanah of Ramathaim-zophim; PASS"` or `"v.11 = Hannah's vow; transcription garbled mid-verse; FAIL"`). Hold these for Task 6.

Expected: every verse has a boolean + a one-line reason.

---

### Task 6: Collate the two witnesses and compute the metrics

**Files:**
- Create: `content/manuscript/samuel/calibration/1sa1_collation.json`

- [ ] **Step 1: Align the two token streams per verse**

For each verse, align `gg_tokens` (from `1sa1_witnessGG.json`) against `cam_tokens` (from `1sa1_witnessCAM.json`) word-by-word. Classify each aligned pair: `agree` (same word, allowing Ge'ez orthographic-variant tolerance — note any tolerance applied in `semantic_note`/a verse note), `disagree` (both present, different), `lacuna-gg` / `lacuna-cam` (present in one, absent/illegible in the other), `lacuna-both`.

- [ ] **Step 2: Compute the three metrics with these exact formulas**

- `ww_agreement_pct = 100 * agree_tokens / aligned_tokens` where `aligned_tokens` = count of pairs classed `agree` or `disagree` (lacunae excluded from the denominator; record lacuna counts separately in a verse/summary note).
- `semantic_pass_pct = 100 * verses_with_semantic_pass_true / total_verses`.
- `uncertainty_pct = 100 * total_uncertain_entries_in_base_witness / total_tokens_in_base_witness` (base witness = the one recommended in Task 7; if Task 7 not yet done, compute for both and keep the base one after Task 7).

Record each percentage **and** its raw fraction in `metrics.*_basis` so it is auditable.

- [ ] **Step 3: Write the collation file**

Create `content/manuscript/samuel/calibration/1sa1_collation.json` using the Collation JSON schema (leave `base_witness_recommended`/`base_rationale` to Task 7; fill everything else now).

- [ ] **Step 4: Verify well-formed + the percentages match their bases**

Run: `cd "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4" && PYTHONUTF8=1 py -3 -c "import json; d=json.load(open('content/manuscript/samuel/calibration/1sa1_collation.json',encoding='utf-8')); m=d['metrics']; n,de=m['ww_agreement_basis'].split('/'); import math; assert abs(m['ww_agreement_pct'] - 100*int(n)/int(de)) < 0.1, m; print('agreement',m['ww_agreement_pct'],'semantic',m['semantic_pass_pct'],'uncertainty',m['uncertainty_pct'])"`

Expected: PASS — prints the three metric values; the assertion confirms `ww_agreement_pct` equals its stated fraction.

---

### Task 7: Recommend the base witness

**Files:**
- Modify: `content/manuscript/samuel/calibration/1sa1_collation.json` (set `base_witness_recommended` + `base_rationale`)

- [ ] **Step 1: Decide**

Pick the base witness for Samuel using, in priority order: (1) chapter-1 completeness (fewest missing/illegible verses), (2) lower `uncertainty_pct`, (3) clearer hand / fewer damage spans, (4) which witness's readings the agreements more often confirm. Write a 2-3 sentence `base_rationale`.

- [ ] **Step 2: Record it**

Set `base_witness_recommended` (`"GG"` or `"CAM"`) and `base_rationale` in `1sa1_collation.json`. If the base changed which witness `uncertainty_pct` is computed against, recompute it (Task 6 Step 2 formula) and update `metrics`.

- [ ] **Step 3: Verify**

Run: `cd "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4" && PYTHONUTF8=1 py -3 -c "import json; d=json.load(open('content/manuscript/samuel/calibration/1sa1_collation.json',encoding='utf-8')); assert d['base_witness_recommended'] in ('GG','CAM') and len(d['base_rationale'])>20; print('base:',d['base_witness_recommended'])"`

Expected: PASS — prints `base: GG` or `base: CAM`.

---

### Task 8: Write the calibration report

**Files:**
- Create: `dev/CALIBRATION_2026-05-16-samuel-1sa1.md`

- [ ] **Step 1: Author the report with these exact sections**

1. **What was done** — chapter (1 Sam 1), both witnesses, the source images/sigla, the independence procedure.
2. **Metrics vs the GO bar** — a table: metric | value | raw fraction | proposed GO threshold (W↔W agreement ≥ 90% / semantic-pass ≥ 95% / uncertainty ≤ 10%) | pass?.
3. **Collation summary** — agreement/disagreement/lacuna counts; the notable disagreements and lacunae verse-by-verse (the apparatus preview).
4. **Recommended base witness** — `base_witness_recommended` + the rationale.
5. **Structural eyeball guide for the user** (no Ge'ez needed) — does verse count match 1 Sam 1; do the flagged-uncertain spots correspond to visible damage on the named images; does the per-verse semantic_note read as a coherent Samuel 1; do the two witnesses broadly track. List the exact image paths to open.
6. **GO / NO-GO recommendation** — explicit, with reasoning against the GO bar.
7. **If NO-GO** — which spec §4 offramp (higher-res crops / easier book first / source a published Ge'ez / explicit lower tier) and why.

Pull all numbers directly from `1sa1_collation.json` (do not restate them by hand — read the file).

- [ ] **Step 2: Verify all sections present + numbers consistent**

Run: `cd "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4" && PYTHONUTF8=1 py -3 -c "t=open('dev/CALIBRATION_2026-05-16-samuel-1sa1.md',encoding='utf-8').read(); [t.index(h) for h in ['What was done','Metrics','Collation summary','Recommended base','eyeball','GO','NO-GO']]; print('all 7 sections present; len',len(t))"`

Expected: PASS — `.index()` raises if any section heading is missing; prints the length.

---

### Task 9: Commit the calibration evidence + report (local only)

**Files:** the 3 JSON files + the report.

- [ ] **Step 1: Stage exactly the Phase-1 artifacts**

Run: `cd "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4" && git add content/manuscript/samuel/calibration/1sa1_witnessGG.json content/manuscript/samuel/calibration/1sa1_witnessCAM.json content/manuscript/samuel/calibration/1sa1_collation.json dev/CALIBRATION_2026-05-16-samuel-1sa1.md`

- [ ] **Step 2: Commit (no push, no zip — project memory)**

Run:
```bash
git commit -m "$(cat <<'EOF'
tau.6.x.4.a calibration gate: 1 Samuel 1 dual-witness pilot (GG + CAM) — evidence + report; NO production code (Approach A)

Phase-1 calibration pilot per docs/superpowers/specs/2026-05-16-
samuel-kings-dual-manuscript-collation-design.md. Two independent
vision transcriptions of 1 Sam 1, semantic-skeleton check, W-W
collation, the 3 honest metrics, recommended base witness, and a
GO/NO-GO report for user review. No tooling built (calibrate-first).
Local commit only, no push, no zip.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"`

- [ ] **Step 3: Verify the commit + pre-commit hook + clean tree**

Run: `cd "C:/Users/bogda/Documents/YHWH-v2.4-full/YHWH v2.4" && git log --oneline -1 && git status --short`

Expected: the commit is logged; pre-commit printed `[pre-commit] ok` (ruff-format unaffected — no `.py`; `lint_rules.py` unaffected — it globs `dev/SCOPE_*.md` + PLAN/SESSION_STATE, not `dev/CALIBRATION_*.md`); `git status --short` shows no remaining staged changes.

---

### Task 10: Present to the user for the GO/NO-GO gate

**Files:**
- Modify: `dev/CALIBRATION_2026-05-16-samuel-1sa1.md` (append a "Decision" line once the user answers)

- [ ] **Step 1: Surface the report + a visual sample**

Push a visual-companion screen with: one CAM and one GG page crop reference (the exact image paths), the metrics table, and the GO/NO-GO recommendation. In the terminal, give the report path (`dev/CALIBRATION_2026-05-16-samuel-1sa1.md`) and the structural-eyeball guide (report §5). Ask the user for: (a) the structural eyeball result, (b) GO or NO-GO, (c) confirmation of the recommended base witness.

- [ ] **Step 2: Record the decision**

Append a final `## Decision (user)` line to `dev/CALIBRATION_2026-05-16-samuel-1sa1.md` capturing GO/NO-GO + base confirmation + date, and commit it locally (same no-push/no-zip rule).

- [ ] **Step 3: Route to the next plan**

Expected outcomes:
- **GO** → the next step is a new plan `docs/superpowers/plans/<date>-samuel-collation-tool.md` for Phases 2-3, **sized to these calibration findings** (per spec §5). Do not start it without the user.
- **NO-GO** → execute the user-chosen spec §4 offramp; no Phase 2-3 plan is written.

---

## Self-Review

**1. Spec coverage:** Spec §4 (the entire calibration gate — chapter choice, independent transcription, semantic check, the 3 metrics + formulas, GO bar, base-witness selection, the user's structural-eyeball role, the Phase-1 deliverable, NO-GO offramps) is covered by Tasks 1-10. Spec §3 "Phase 1 builds no tooling" is honored (zero `scripts/`/`tests/` changes). Spec §5/§6 (Phase 2-3 tool + render) are deliberately and explicitly deferred to a post-GO plan because the spec itself mandates the tool be "sized to what Phase 1 reveals" — that is a correct scope boundary, not a coverage gap. Spec §7 honesty (uncertainty markers, immutable evidence files, no fabrication) is built into the evidence schema + Task 2/4 procedure. Spec §9 attribution is referenced via `source_images` provenance in every evidence file. No gaps.

**2. Placeholder scan:** No "TBD/TODO/implement later". The Phase 2-3 deferral is explicit and justified by the spec, not a placeholder. Every task has exact paths, a concrete deliverable, and an executable verification.

**3. Type consistency:** The Evidence JSON schema (`witness`, `book`, `chapter`, `source_images`, `folio_sigla`, `verses[].v/geez/tokens/uncertain[]/column/line_start`, `transcription_notes`) is defined once and used identically in Tasks 2 & 4. The Collation JSON schema (`base_witness_recommended`, `base_rationale`, `verses[].gg_tokens/cam_tokens/alignment[].class/semantic_pass/semantic_note`, `metrics.*_pct/*_basis`) is defined once and consumed consistently in Tasks 6, 7, 8. `class` and `marker` enums are fixed and reused. The metric formulas in Task 6 Step 2 are the single source of truth, referenced by Task 7 and Task 8. Consistent.

---

## Out of scope (next plan, only after a GO)

Phases 2-3 — the folio manifest, per-folio transcription records, the verse-alignment/collation engine, the reconciled-text + apparatus, the QA report, and the τ.7.x-conventions render into `geez-tewahedo/{1sa,2sa}.py` + the apparatus store + the `manuscript-collation-tier2` provenance tier — are specified in §5-§6 of the design spec but are **intentionally not planned here**. They are written as their own plan after the calibration GO, sized to the measured failure modes. Kings reuses that Phase 2-3 plan as a template afterward.
