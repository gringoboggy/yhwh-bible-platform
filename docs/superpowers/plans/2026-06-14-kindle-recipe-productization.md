# Productize the proven June-10 Send-to-Kindle recipe as `--target-reader kindle`

**Status:** ✅ IMPLEMENTED + VERIFIED (Mac, turn 85) — all 7 production changes + the
gate fix shipped (commits `d4cd5257`, `5ae67722`, +final); the `--target-reader kindle`
build reproduces the june10 PASS shape on every signal (stamp aside), epubcheck 0/0/0/0,
gate-5 green, 308 kindle/popup/format tests green; artifact staged for the user's STK
re-confirm (the only remaining gate — M4 lights on it). **Owner:** Mac lane. **Mandate:** SESSION_STATE
turn-84 / handoff #1 — *"make the `--target-reader kindle` build mode emit exactly the
proven june10 recipe so the website generates it in one build. TDD; keep non-kindle
byte-identical. Do NOT re-introduce the KP3-oracle extras."*

## Why (the empirical ground truth)

The ONLY confirmed Send-to-Kindle (STK) success is `june10recipe.epub` (user-confirmed
delivered). Measured against the FAILED `FIXED.epub` and a fresh standard `everywhere`
build, the proven-PASS shape is:

| signal | june10 **PASS** | FIXED **FAIL** | everywhere build |
|---|---|---|---|
| files / xhtml / spine | 377 / 300 / **299** | 267 / 190 / 189 | 377 / 300 / 299 |
| dc:language | **1 (en-US)** | 1 | 6 |
| CSS+inline display:none / visibility:hidden | **0** | 0 | 7 rules |
| `hidden=""` footnote attrs | **406 (kept)** | 133 (unhide ran) | 406 |
| vn-sep spans | **132,949 (kept)** | 0 (dropped) | 132,949 |
| kindle_safe CSS | **absent** | present | absent |
| popup languages | **all 4 (heb+grc+lat+ara + back-tr)** | — | all 4 |
| popup labels/headers | **full (uncompacted)** | — | full |

**Derived facts:**
1. june10 == the `everywhere` build + exactly two deltas: strip `display:none`/
   `visibility:hidden` (CSS+inline), and collapse `dc:language` → single `en-US`.
2. june10 kept 406 `hidden=""` asides and PASSED ⇒ **Amazon's E3013/E999 scanner counts
   CSS `display:none`, NOT the HTML `hidden` attribute.** (So `apply_kindle_unhide` is
   unnecessary; Kindle's native footnote popups use the `hidden` asides.)
3. `.vn-sep { display:none }` alone hides ~400K chars (≫ the 10K E3013 cap), so stripping
   it is necessary; june10 stripped the rule (bullets become visible) and passed. Dropping
   the *spans* (current `apply_kindle_strip_hidden`) is a FAIL-column behavior — keep them.
4. june10 carries the full 4-language uncompacted apparatus at 25.3 MB and delivered ⇒ the
   kindle byte/element-ceiling theory that drove the file-split, the popup-language cap, and
   the (B) compaction was **falsified** (it came from the Kindle-Previewer/KDP oracle, which
   the saga proved gives false-green; the only valid oracle is real STK).

Independent review (Grok, read-only) converged on DROP 1–4,6 / KEEP single-lang / keep the
display:none strip but preserve vn-sep. Its one dissent (omit the OPF target-stamp to match
june10 exactly) is noted; we keep the stamp (standard custom OPF meta, KFX-ignored; the
gate's self-identification mechanism) and FLAG it as the single known deviation for the
user's STK re-test.

## The change (all kindle-target-only; non-kindle stays byte-identical)

Peel the kindle path back to the proven june10 shape. Each falsified transform is a
kindle-only accretion from the saga; with kindle no longer using them they are dead, so
remove them (git history preserves them; this doc records why).

- [ ] **1. file-split** — `resolve_file_split_target`: kindle uses `FILE_SPLIT_TARGET_DEFAULT`
  (→ 299 spine, like everywhere). Remove `FILE_SPLIT_TARGET_KINDLE` + its falsified comment.
- [ ] **2. popup-language cap** — `resolve_popup_language_cap`: kindle default `None`
  (uncapped). Keep the explicit `max_popup_languages` feature (UI/API/clone untouched).
- [ ] **3. (B) compaction** — gate the label/header compaction in
  `_apply_popup_languages_and_translation` on *a cap being active* (not on `is_kindle_target`),
  so default (uncapped) kindle = full uncompacted apparatus = june10; capped editions still
  compact. (Compaction + cap = the opt-in "compact mode".)
- [ ] **4. strip-hidden** — `apply_kindle_strip_hidden`: remove the vn-sep-span dropping;
  keep the CSS+inline `display:none`/`visibility:hidden` strip. (Grok: keep these surgically
  separate or you recreate the FAIL's vn-sep=0.)
- [ ] **5. remove** `apply_kindle_safe_css` + `_KINDLE_SAFE_CSS`, `apply_kindle_toc_rows` +
  helpers, `apply_kindle_unhide` + helper, and all three call sites.
- [ ] **6. KEEP** the single-`en-US` dc:language gate + the OPF target stamp.
- [ ] **7. gate** — `dev/verify_kr2_build.py` `kindle_safe_checks`: keep dc:language==1 and
  the raw display:none scan; REMOVE the "kindle_safe CSS present" check and the
  "hidden='' attrs == 0" check (both would FAIL june10 — they encode the FIXED shape).

## Tests (TDD — flip to the proven shape, watch RED, implement GREEN)

- `tests/test_file_split.py` — kindle uses the default cap.
- `tests/test_popup_language_cap.py` — kindle default uncapped/uncompacted; cap+compaction
  via explicit `max_popup_languages`; keep pick defaults + UI/API/clone coverage.
- `tests/test_kindle_strip_hidden.py` — vn-sep KEPT.
- `tests/test_kindle_safe.py` — remove `TestKindleSafeCss`, `TestKindleTocRows`,
  `TestKindleUnhideAttrs`.
- `tests/test_kindle_safe_gate.py` — proven-shape gate.
- NEW integration pin: a `--target-reader kindle` build reproduces the june10 signature.

## Verification gates (before "done")

- [ ] Full kindle test surface green + relevant suite (`-m "not slow"`).
- [ ] `--target-reader kindle` build of catholic-study matches june10 signature
  (0 display:none; dc:language==1; no kindle_safe; hidden attrs + vn-sep preserved; spine ==
  everywhere; all 4 popup languages; full labels). epubcheck 0/0/0/0.
- [ ] **Non-kindle byte-identity:** rebuilt `everywhere` catholic-study == `build/repro-everywhere`
  (the pre-change baseline) — unzipped-tree diff empty.
- [ ] Stage the artifact to Desktop for the user's **real Send-to-Kindle** re-test (the only
  valid oracle). M4 lights only on user STK confirmation.

## Cross-lane (Guard #4/#6 — flag to WIN on handoff)

`build_edition.py` is co-edited by WIN (round-7 popup-split). My edits are in distinct kindle
functions, but I also touch **`dev/verify_kr2_build.py` `kindle_safe_checks`** (WIN owns gates
4g–4n — distinct function) and change the **kindle default** of the popup-cap/compaction
(user-directed K-KIN B+C — now opt-in, feature preserved). Flag both on the milestone push.
