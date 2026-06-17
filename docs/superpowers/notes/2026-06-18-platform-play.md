# Platform research — Google Play Books (Round 9)

**Status:** FINDINGS — Round 9 WIN lane `platform-play` dimension.
**Date:** 2026-06-18 · **Lane:** win · **Dim:** `platform-play`

---

## 1. Our target UX (non-negotiables)

From `dev/EREADERS.md` §Google Play Books and the M5 phone-QA protocol:

| Surface | Target behavior |
|---|---|
| **Delivery** | Personal library upload (Android/iOS/web) — **not** Play Partner Center |
| **Popup footnotes** | `vn-link` + study badges open **readable** text (not blank, not jump-to-piece-top) — **❓ unverified; user phone-QA is the gate** |
| **Embedded fonts** | Hebrew/Greek/Arabic/Geʽez render in body (not tofu) — **❓ unverified** |
| **Collapsible ToC** | `<details>` expected **closed and stuck** — honest fail, document limitation |
| **Chapter nav** | ToC / in-book chapter jump lands on correct chapter start |
| **Page breaks** | Title page → first chapter: no mid-sentence disaster on long boundaries — **❓ unverified** |
| **Profile** | Today: `everywhere` build; promote to `play` target only if QA demands divergence |
| **Catalog** | M5 column `live: false` until rounds 1–3 pass (`website/src/data/catalog.json`) |

**Staged QA artifact (v0.1.0):** `YHWH-ethiopian-tewahedo-v0.1.0-everywhere-navy.epub` — GitHub release URL in `EREADERS.md:156–157`.

---

## 2. Official format support

| Topic | Vendor says | Our build uses |
|---|---|---|
| EPUB version | EPUB 3.3 preferred; 2/3 accepted; EpubCheck recommended ([Partner EPUB files](https://support.google.com/books/partner/answer/3316879)) | EPUB 3.3; `epubcheck 0/0/0/0` on shipped artifacts |
| Popup footnotes (`noteref`/`aside`) | **Not documented** — EPUB3 features "may not be supported across all platforms" (same page) | Full EPUB3 popup model (`epub:type="noteref"` / `footnote` asides) — same as `everywhere` |
| Embedded fonts | ✅ Supported ([feature table](https://support.google.com/books/partner/answer/3316879#enhanced)) | Embedded OFL fonts in `stylesheet.css` + font files in EPUB |
| Page-break CSS | Not enumerated; reflowable EPUB | CSS `page-break-*` honored on desktop readers; **unknown on Play** |
| Collapsible ToC (`<details>`) | No native support documented; epubtest + our research: **cannot expand** on Android | `toc_expandable` gated **off** for `everywhere` (`TARGET_CAPS.everywhere.toc_expandable: false`) |
| RTL / multi-script | ✅ Global language support (vendor table) | Multi-value `dc:language` in OPF (6 values on non-kindle builds) + `dir`/`lang` spans |

### Upload constraints (personal library + partner reference)

| Constraint | Source | Our artifact |
|---|---|---|
| Formats | `.epub`, `.pdf` only (no `.doc`/`.html`) | `.epub` ✅ |
| Partner max file size | **< 2 GB** per file ([file guidelines](https://support.google.com/books/partner/answer/3424254)) | ~25–30 MiB (`everywhere` / `kindle_safe` scale) — well under limit |
| Validation | EpubCheck recommended; ADE smoke-test suggested | CI gate `epubcheck 0/0/0/0` |
| Upload path | Play Books app → Profile → Upload; or `play.google.com/books`; Open With → Play Books ([consumer help](https://support.google.com/googleplay/answer/11012086)) | Protocol in `EREADERS.md:159–162` |
| JavaScript | ✘ | None in our EPUB ✅ |
| MathML | ✘ | Not used ✅ |
| Multi-column | ✘ | Single-column layout ✅ |

**Community caveat:** Play Books uses a **custom non-WebKit** renderer on Android (epubtest.org AT context); behavior can differ from Thorium/Calibre/Apple Books even on identical EPUB bytes.

**Sources (cite URLs):**

- https://support.google.com/books/partner/answer/3316879 (EPUB 3 feature grid)
- https://support.google.com/books/partner/answer/3424254 (file size, formats)
- https://support.google.com/googleplay/answer/11012086 (personal upload steps)
- `docs/superpowers/notes/2026-06-10-target-caps-research.md` (Play `<details>` closed-and-stuck)
- `dev/EREADERS.md` §Google Play Books

---

## 3. How others achieved similar goals

| Technique | Who / where | Applies to us? |
|---|---|---|
| **Ship EPUB 3 + EpubCheck clean** | Google Partner docs; Vellum/Calibre communities | ✅ Already our floor gate |
| **Avoid `<details>` for chapter lists** | Our TARGET_CAPS research (Play = stuck closed) | ✅ `everywhere` uses flat chapter pills |
| **Avoid JavaScript / MathML** | Google unsupported-feature table | ✅ No JS in EPUB |
| **Test on real Play app** before claiming support | Indie author guides; our M5 protocol | ⚠ **Required** — no substitute for phone QA |
| **Fallback to visible endnotes** if popups fail | Kindle `kindle_post` pattern | ❓ Reserve for Play only if QA fails popups — do not preempt |
| **Dedicated font embedding** | Google ✅ embedded fonts | ✅ Already embedded; verify on device |
| **Keep `everywhere` artifact** until divergence proven | Our FORMAT_MATRIX design §2 row 5 | ✅ Current staging path |

---

## 4. Gap vs our pipeline

| Gap | `build_edition` / post-process / `TARGET_CAPS` | Severity |
|---|---|---|
| **Zero device proof** for popups, fonts, page-breaks | M5 `live: false`; `EREADERS.md:22` UNTESTED | **HIGH** — blocks catalog column |
| **No `play` `target_reader`** — uses `everywhere` alias | `FORMAT_MATRIX` play row `target_reader: everywhere` (`build_edition.py:2075–2083`) | **MED** — intentional until QA |
| **No Play post-process** (cf. `kindle_safe`, `kepubify`) | `build_format_matrix.py` — play cell = plain copy of `everywhere` base | **LOW** — correct default |
| **No Play-specific gates** in `verify_kr2_build.py` | Only kobo/kindle stamped checks | **MED** — nothing catches Play regressions pre-QA |
| **`TARGET_CAPS` has no `play` entry** | Wizard uses `everywhere` caps (`wizard.py:546–582`) | **LOW** — `<details>` already off |
| **Popup model = full merged study asides** | Apple/Kobo forks don't apply; Play gets 25+ MiB popup graph | **MED** — may stress mobile renderer if popups work at all |
| **Multi-value `dc:language`** (6 tags) | Non-kindle OPF (`build_edition.py:1737–1748`) | **LOW** — Google claims global language support; Kindle proved multi-lang breaks **Amazon**, not Google |
| **No Play row in format-matrix CI** | `phase: M5` not built in default matrix jobs | **LOW** — awaits M5 fan-out after QA |

### Build paths (authoritative)

```text
Catalog cell "play"
  └─ FORMAT_MATRIX id=play, target_reader=everywhere, packaging=epub, phase=M5
       └─ build_format_matrix.base_build_target() → "everywhere"
            └─ build_edition.py <edition> --target-reader everywhere --version <v>
                 └─ shutil.copyfile (signature) / swap_epub_cover (variant colours)
                      └─ _gate_asset: epubcheck + verify_kr2_build (non-kindle bars)
```

Contrast:

- **Kindle:** `everywhere` base + `kindle_post.make_kindle_safe` (`build_format_matrix.py:284–285`)
- **Kobo:** `eink` base + kepubify (`build_format_matrix.py:256–262`)
- **Play:** `everywhere` base, **no** post-process

---

## 5. Options ranked — `everywhere` vs dedicated `play` profile

### Option A (recommended) — **Keep `everywhere` build; gate on phone QA**

- **Change:** Run M5 protocol on staged navy `everywhere` EPUB; record pass/fail per tap item in `EREADERS.md`; fan `build_format_matrix --phase M5` only after rounds 1–3 green.
- **Files:** `dev/EREADERS.md` (verdict section) · `website/src/data/catalog.json` (`play.live`) · `scripts/build_format_matrix.py` (M5 phase already wired)
- **Device proof:** User phone — Gen 1:1 popup, script sample verse, chapter nav, `<details>` stuck check, title→chapter break
- **Risk:** Low — same bytes as shipped v0.1.0 `everywhere` artifact; no builder churn

### Option B — **Add `target_reader: play` with minimal caps**

- **Change:** Fifth profile if QA shows specific failures fixable at build time — e.g. flatten study popups to inline/endnotes (Kindle-like strip), or cap popup languages, or Play-specific CSS.tweaks. Add `TARGET_CAPS.play`, wizard row, optional `yhwh:target-reader` stamp.
- **Files:** `build_edition.py` (`TARGET_READERS`, `FORMAT_MATRIX`) · `wizard.py` `TARGET_CAPS` · `validate_schemas.py`
- **Device proof:** A/B upload: `everywhere` vs `play` artifact on same phone
- **Risk:** Medium — fork surface area; must not bleed into `tablet` per `notes/2026-06-15-apple-m2-layout-directive.md`

### Option C (decline / defer) — **Document Play as unsupported; skip M5 column**

- **Change:** Leave M5 dark; note "use Thorium/Calibre/`everywhere` download instead"; remove Play from website format picker.
- **Files:** `FORMAT_MATRIX` phase gate · website catalog
- **Device proof:** N/A
- **Risk:** Low product impact if user doesn't read on Play; **high** if Play is a primary phone reader — user offered QA, so defer only on explicit user direction

---

## 6. Popup / font support — research verdict

| Feature | Research confidence | Rationale |
|---|---|---|
| **Popup footnotes** | **❓ LOW until device test** | Google docs silent on EPUB3 aside popups; Play Android uses custom engine; our popups work on Apple/Thorium/Kobo-kepub but each reader differs |
| **Embedded fonts** | **⚠ MED-HIGH likely OK** | Vendor table ✅; our fonts are standard TTF/OFL embedded same as Apple path |
| **Multi-script body text** | **⚠ MED** | Global language ✅; verify Geʽez/Arabic on phone — Play may ignore some `lang` without font embed |
| **`<details>` ToC** | **❌ HIGH confidence FAIL** | Closed-and-stuck on Android (our TARGET_CAPS gate_reason cites this) |
| **CSS page-breaks** | **❓ LOW** | Not in Google table; long scripture may reflow acceptably anyway |

**If popups fail on Play:** Do **not** auto-apply Kindle `kindle_post` (strips hides, collapses languages) — that recipe is Amazon-specific. Instead: document limitation OR design Play-specific visible-note presentation under Option B.

---

## 7. Open questions for device QA (M5 protocol)

1. Tap `vn-link` / study badge on Gen 1:1 — popup vs jump vs blank?
2. Hebrew/Greek/Arabic sample verse — scripts render?
3. Native ToC chapter jump — correct landing?
4. Collapsible ToC (if present in artifact) — confirm closed/stuck?
5. Title page → Genesis 1 — acceptable break behavior?
6. Upload size / processing time for ~25 MiB EPUB on phone — any timeout?
7. After QA: does **any** failure require a `play` profile, or is documentation enough?

---

## 8. Recommended implementation plan

| Step | Owner | Blocks |
|---|---|---|
| 1. User uploads `YHWH-ethiopian-tewahedo-v0.1.0-everywhere-navy.epub` per `EREADERS.md` protocol | User | All M5 work |
| 2. Record pass/fail + screenshots in `EREADERS.md` §Play (date-stamped) | WIN | Truth record |
| 3. **If rounds 1–3 PASS:** `build_format_matrix --phase M5` × 9 editions → attach 45 assets → `catalog.json` `play.live: true` | WIN | Website M5 column |
| 4. **If popups/fonts FAIL:** triage → Option B spec (minimal `play` profile) OR Option C (document limitation) | WIN + user | Profile decision |
| 5. Update `notes/2026-06-18-platform-implementation-matrix.md` Play column from ❓ → ✅/❌/⚠ | WIN | Round-9 merge |
| 6. Keep `toc_expandable: false` on any Play profile — do not enable `<details>` | — | Avoid closed-and-stuck trap |