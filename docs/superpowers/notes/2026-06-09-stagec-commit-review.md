# Adversarial review — WIN `5508207a` + `2030e7e0` vs their specs (Mac, turn 56, 2026-06-09)

_Laundry #3 of the turn-54 board. Method: 3 independent reviewers (one per commit + one
cross-cutting integration pass) → every finding independently adversarially verified (2 lenses
for high-severity, refute-by-default). **16 findings confirmed, 0 refuted** (23 agents).
Both commits are **faithful to their specs overall** — the real defects are at the edges:
two missed sibling test pins (suite was RED on main) and one suspect headline fix (AB①)._

## Verdict per commit

- **`5508207a` (EB-Garamond completion + launcher.spec frozen-404 fix)** — implements
  `docs/superpowers/specs/2026-06-09-app-eb-garamond-selfhosting.md` §2/§4.1/§4.2 faithfully.
  The datas entry is structurally correct for the frozen `_MEIPASS` layout (dest `website/fonts`
  matches the `REPO`-relative lookup at `scripts/web_helpers.py:25`; same pattern already
  frozen-proven for `content/` + `epub_working/`). The face/range match the website verbatim.
  Stale-comment edit verified comment-only. All 30 `test_skin_aa.py` pins pass. Gaps: modest
  (below).
- **`2030e7e0` (title-page object-fit + This-Edition→Your-Edition relocation)** — the relocation
  is cleanly builder-level (all 11 editions incl. canon-filtered catholic-study get it; no
  resolver bypass; no duplicate ids), and the `.cover-img` sibling already had `object-fit`, so
  the img class is fully covered. **BUT it broke two sibling pins in other test files (main RED)
  and the AB① fix itself is plausibly a no-op on Apple Books** (below).
- **Integration** — no cross-commit interference; no per-edition hardcoding outside the resolver;
  no kepub/koboSpan-sensitive selectors; `649f1075`'s badge pin asserts shipped behavior.

## ✅ Fixed by Mac THIS session (commit `45e31a12`) — main is green again

| # | sev | finding | where | fix shipped |
|---|---|---|---|---|
| F1 | **HIGH** | `2030e7e0` missed sibling pin → suite RED on main: pin asserts the URN still on the colophon | `tests/test_scripts.py:559` | re-pointed to the new contract (URN **absent** on colophon) |
| F2 | **HIGH** | same class, second site: Ω.0 pivot pin `test_render_copyright_page_uses_urn_not_isbn` failing | `tests/test_omega0_free_public_pivot.py:115` | re-pointed: URN absent on colophon **+ present on `render_your_edition_page`** (the pivot's "URN not ISBN" spirit now pinned where the URN actually ships) |
| F3 | LOW | frozen app 404s `/favicon.ico` — `assets/icons` not bundled (the exact §1.5 class `5508207a` fixed for fonts) | `scripts/web.py:1802` route ← `dev/launcher.spec` datas | added `(str(ROOT / "assets" / "icons"), "assets/icons")` + a pin |
| F4 | LOW | weak pin: `assert "website" in spec and "fonts" in spec` is satisfiable by the comment block alone | `tests/test_skin_aa.py:275` | pin now asserts the load-bearing datas tuple literal |

33/33 green after the fixes (`test_skin_aa.py` 30+1 new, plus the two re-pointed pins).

## ▶ ROUTED TO WIN (your files / your arc — Guard #6, file:line)

| # | sev | finding | where | prescription |
|---|---|---|---|---|
| W1 | **HIGH** | **AB① is plausibly a layout NO-OP**: `object-fit:contain` only scales content *within* the box; with `width/height:auto` the box follows the intrinsic aspect, so bare `max-height` + `object-fit` may still not cap the box on Apple Books. The project's OWN research (`2026-06-05-eink-epub-compat-research.md` ≈:477) says Apple ignores `max-height` and prescribes **explicit height + object-fit** | `epub_working/stylesheet.css:560` (`.bookpage-art`/`.bookpage-art-bleed`) | treat **AB① as OPEN until the user's device re-test**. If it still pushes: explicit height (e.g. `height:88vh` on the bleed variant, letterboxing invisible there) — and since K③ says `vh` is unreliable on Kobo/RMSDK, pair it with the same non-vh fallback you're adding for K③ (one coherent @supports strategy for both) |
| W2 | LOW | verification-protocol: the "frozen 404 fix" headline shipped without the spec's §6.3 **load-bearing frozen-rebuild test** (all on-disk frozen artifacts predate the commit; `dist/YHWH/_internal/` has no `website/`) | `dev/launcher.spec:113` | on the next frozen rebuild: `curl` the running frozen app for `/fonts/eb-garamond-latin-400-normal.woff2` (200 + font/woff2) **and now `/favicon.ico`**, both Win `.exe` and mac `.app`; record in the truth record before the v0.1.0 cut |
| W3 | LOW | dead CSS: the relocated `<h2 class="copyright-heading">` was the only emitter; both `.copyright-heading` rules now ship dead in every edition + `test_copyright_heading_has_avoid` pins a class that never renders | `epub_working/stylesheet.css:625` | delete both rules; retire/re-point the pin (you're in this file for K①–K③ anyway) |
| W4 | LOW | `render_copyright_page` keeps a now-unused `version` param (only consumer was the removed "Build:" line) — sibling of your own FIX 5 pattern | `scripts/matter_pages.py:25` (+ call site :141) | drop the param, mirroring FIX 5 (`TestDedicationPageSignature`) |
| W5 | LOW | missed 5th EB-Garamond stack: `WELCOME_OVERLAY_JS` inline style lacks the Ethiopic fallback (spec §4.1 says "every EB Garamond stack"); content is currently English-only so cosmetic | `scripts/templates/_design.py:2648` | append `"Noto Serif Ethiopic"` to the stack; bump `test_geez_font_stacks_fall_through_to_ethiopic` count to >= 6 |
| W6 | INFO | spec §4.1 wording misstates the website strategy (site uses `:lang(gez)/:lang(am)` scoping, not in-stack) — implementation unaffected | `docs/superpowers/specs/2026-06-09-app-eb-garamond-selfhosting.md:297` | optional one-line correction |

## Verified-correct (recorded so it is NOT re-litigated)

- **unicode-range U+1200-137F covers 100% of the repo's Ge'ez**: independent corpus scan of all
  642 content files = **2,307,919 Ethiopic chars, zero outside the declared range** (corroborates
  the laundry-#4 EPUB scan: 74 distinct chars, max U+1365). The widen-anyway recipe in
  `2026-06-09-kobo-geez-font-research.md` stands as future-proofing, not a bug fix.
- The frozen path trace for `website/fonts` is sound (`REPO` → bundle root when frozen; route
  reads `REPO/website/fonts`; dest matches exactly).
- `.cover-img` already had `object-fit:contain` — the img-class sweep is closed (cover + the two
  fixed classes are the only `<img>` emitters in the pipeline).
- This-Edition relocation: identity flows through `inject_your_edition_page` for all editions;
  no duplicate ids/anchors; no ToC/landmark references to the old location.
- Test state on this Mac at review time: `test_skin_aa.py` 30/30; `test_matter_pages_your_edition.py`
  non-build subset 7/7 (the then-stale legend test excluded — since REWRITTEN green, laundry #5,
  `67630007`); `test_presentation_polish.py`/`test_marker_style.py` new assertions statically
  verified (their slow EPUB-build portions exceeded the review window — re-run solo when the box
  is free).

— Mac, turn 56. Run: `wf_1ecc1dfb-8ee` (3 reviewers + 13 verifiers, 16/16 confirmed).
