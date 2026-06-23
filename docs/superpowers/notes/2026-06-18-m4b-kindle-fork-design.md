# M4b Kindle fork — design spec

**Status:** ⚠ SUPERSEDED — shipped as **Option B** (a separate `kindle_study_glossary`
spine file, **not** the Option-A chapter-tail `kindle-chapter-study` sections this spec
describes). Live implementation: `apply_kindle_m4b` / `verify_kindle_m4b` in
`scripts/core/kindle_post.py`, gated by `tests/test_kindle_m4b.py`. Kept for design-history;
§6 below is updated to the shipped gates.
**Date:** 2026-06-18 · **Lane:** mac · **Input:** `notes/2026-06-18-platform-kindle.md` Option A

---

## 1. Problem

Send-to-Kindle delivery is **proven** (`kindle_post.make_kindle_safe`, STK 6/6 PASS 2026-06-14). Phone QA on the inline-marker everywhere build **failed** on study-badge taps: `noteref` targets in chapter-tail `notes-section` after `page-break-before` resolve to wrong locations (3:24, 8:10, 11:26 teleport class — `notes/2026-06-15-kindle-phone-qa-kindle_img.md`).

User goal: **Kobo-like reading** — translation popups stay inline; **study notes move off the scripture line** to visible end-of-chapter blocks (or suppressed markers + navigate).

The retired `--target-reader kindle` in-pipeline variant is **declined** (Previewer-oracle extras broke STK). M4b extends the **proven june10 post-process path**, not the old variant.

---

## 2. Non-negotiables

| Constraint | Source |
|---|---|
| Send-to-Kindle must still pass `verify_kindle_safe` | `scripts/core/kindle_post.py` |
| epubcheck 0/0/0/0 on shipped kindle column cells | v1.0.0 gate |
| No `display:none` / `visibility:hidden` left in package | kindle_post physical strip |
| Single `dc:language` (`en-US`) in final artifact | kindle_post |
| `vn-sep` spans **kept** (visible language separators) | turn-85 correction |
| 9 KJV editions byte-stable under `everywhere` profile | M4b is kindle-column post-process only |
| Phone STK spot-check on link targets, not just delivery | M4 gate |

---

## 3. Target UX (M4b)

### Scripture body

- **Translation:** keep `vn-link` badges at verse start → same-file `vnote-*` asides (popup or inline preview per KFX; phone QA verifies).
- **Study:** **remove** inline ◈ / numbered study badges from verse text — verse line shows scripture only.

### Study presentation

- **Per chapter:** append a **Study Notes** block at the **end of the chapter's last spine piece** (same file as the chapter content — avoids cross-piece KFX anchor breakage).
- Block contains the merged `vnotes-*` / category content that would have been inline popups, with stable `#vnotes-{book}-{ch}-{v}` (or per-category) anchors.
- Optional verse-level jump: suppressed badge replaced by nothing in body; user reaches notes via chapter-tail section or a minimal same-file link if phone QA proves it.

### Explicitly out of scope (v1)

- Full-book study glossary backmatter (Kobo K-R9 mirror) — Option B; higher KFX pagination risk.
- Re-enabling retired `apply_kindle_*` in-pipeline transforms.

---

## 4. Pipeline placement

```
everywhere build (ethiopian-tewahedo / catalog edition)
    → kindle_post.make_kindle_safe (existing: strip hides, dc:language, mimetype)
    → kindle_post.apply_kindle_m4b (NEW: marker suppress + chapter-tail study HTML)
    → verify_kindle_safe + verify_kindle_m4b (NEW)
    → epubcheck 0/0/0/0
    → STK phone QA
```

`build_format_matrix` kindle row: keep `post_process: kindle_safe`; chain M4b inside `make_kindle_safe` or as `post_process: kindle_m4b` second step (configurable; default **on** for catalog kindle column once device-proven).

---

## 5. HTML transforms (`apply_kindle_m4b`)

### 5.1 Suppress inline study markers

For each study badge (`a.epub:type="noteref"` targeting `vnotes-*` / study categories):

1. Remove the `<a …>` badge element from the verse paragraph.
2. Preserve the aside payload — relocate, do not delete content.

Translation `vn-link` → `vnote-*` markers: **unchanged**.

### 5.2 Chapter-tail study block

Per chapter (within each spine HTML file):

1. Collect study asides referenced by suppressed badges in that chapter.
2. Emit after the last verse block, before the next chapter heading:

```html
<section class="kindle-chapter-study" epub:type="footnotes">
  <h3>Study Notes — {book} {chapter}</h3>
  <!-- relocated vnotes-* asides, ids preserved -->
</section>
```

3. **No `hidden=""` reliance** — content must be visible after kindle_post strip pass.
4. **Same-file anchors only** for phone-tested `noteref` jumps.

### 5.3 Page-break interaction

Chapter `page-break-before` on the **next** chapter heading must not sit between a `vn-link` and its `vnote-*` aside. Study block stays in the **same piece** as the chapter verses (reuse `apply_file_split` piece boundaries — no new split at study block).

---

## 6. Verification gates

### Existing — keep

- `verify_kindle_safe`: zero hides, single `dc:language`, mimetype first/stored
- `dev/verify_kr2_build.py` gates 1–4 on pre-post everywhere base (kindle column uses unstamped base)

### Shipped — `verify_kindle_m4b(epub_path) -> list[str]` (returns failing gate ids; empty list = pass)

| Check | Fail condition (as shipped in `scripts/core/kindle_post.py`) |
|---|---|
| m4b-1 | A study badge still targets a **same-file** `#…` anchor (not the glossary spine) |
| m4b-2 | A `vnotes-` aside still sits in the scripture prose |
| m4b-3 | Study badges present but **no `kindle_study_glossary` spine file** exists |
| m4b-4 | A **bare scripture verse** href (`#…`) appears in the glossary |
| m4b-5 | A translation `vnote` is inlined in the scripture prose |
| m4b-6 | A retired `kindle-chapter-study` block survives in scripture |

TDD: `tests/test_kindle_m4b.py` (`TestApplyKindleM4bHtml` / `TestApplyKindleM4bEpub` / `TestVerifyKindleM4b` / `TestMakeKindleM4b` / `TestKindleM4bCss`) — minimal fixture HTML through `apply_kindle_m4b`; phone-QA matrix separate (structural only).

---

## 7. Device QA matrix (user STK)

Minimum phone taps after implementation (6-variant fan-out like turn 87):

| # | Edition variant | Tap | Pass criterion |
|---|---|---|---|
| 1 | ethiopian-tewahedo (largest) | Gen 1:1 `vn-link` | Readable translation text |
| 2 | ethiopian-tewahedo | Gen 1:3 (multi-study verse) | No inline ◈ clutter; chapter-tail study reachable |
| 3 | catholic-study | Random study-heavy chapter | No 3:24-style teleport |
| 4 | jewish-study (smallest) | Hebrew verse popup | Scripts render |
| 5 | Any | Chapter nav from ToC | Lands on chapter start |
| 6 | Any | Study Notes chapter block | Visible endnotes, not blank |

### Gate sweep (Mac turn 125, 2026-06-18 — structural only, no STK upload)

`M4B=1 bash dev/reader_sim/kindle/gate.sh` on `~/Desktop/YHWH-kindle-m4b-qa/` — all **PASS** (epubcheck 0/0/0/0 · verify_kindle_safe · verify_kindle_m4b):

| Edition | Gate |
|---|---|
| catholic-study | PASS |
| eastern-orthodox | PASS |
| ethiopian-tewahedo | PASS |
| evangelical-reformed | PASS |
| jewish-study | PASS |
| scholarly-academic | PASS |

**STK device QA (2026-06-18): FAIL** — both m4b ethiopian uploads; Mac + phone identical.
`vn-link` teleports to chapter-tail notes; no translation popups; notes lack coord/back-link.
See `docs/superpowers/notes/2026-06-18-kindle-stk-m4b-device-qa.md`. Catalog regen blocked until fix.

**Mac turn 127 re-gate (2026-06-18):** 6/6 m4b variants on `~/Desktop/YHWH-kindle-m4b-qa/` —
`verify_kindle_safe` + `verify_kindle_m4b` + epubcheck all PASS. STK live poll still
gate-only (no `com.amazon.Kindle` library container on Mac box).

---

## 8. Implementation plan

| Step | Owner | Depends on |
|---|---|---|
| 1. This spec | Mac | platform-kindle brief ✓ |
| 2. `apply_kindle_m4b` + `verify_kindle_m4b` + tests | Mac | Step 1 |
| 3. Wire into `build_kindle.py` / `build_format_matrix` kindle row | Mac | Step 2 green |
| 4. 6-variant STK pack to `~/Desktop/YHWH-kindle-m4b-qa/` | Mac | Step 3 |
| 5. User phone Send-to-Kindle | User | Step 4 |
| 6. Regen 45 catalog kindle cells + SHA256SUMS | WIN | Step 5 PASS |

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| KFX breaks same-file chapter-tail anchors | TDD + phone matrix before catalog regen |
| `verify_kindle_safe` regression | Run both verifiers in series; no new hides |
| Byte-stability on everywhere editions | M4b only touches kindle post-process output |
| Scope creep into glossary backmatter | Decline Option B until Option A fails phone QA |

---

## 10. References

- `notes/2026-06-18-platform-kindle.md` — research + Option A/B ranking
- `notes/2026-06-15-kindle-phone-qa-kindle_img.md` — teleport evidence
- `scripts/core/kindle_post.py` — proven strip recipe
- `dev/EREADERS.md` §Kindle — STK acceptance record