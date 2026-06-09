# Idiot-proof shipped app — design spec (v0.1.0 app-UX arc)

**Status:** READY for WIN to implement (WIN owns shared-code impl). · **Mac lane, 2026-06-09.**
**North star (user):** *"think of the dumbest person — make it idiot-proof"*; *"the editor on the right is confusing, people won't know what that HTML stuff is"*; *"instead of html code can we just build a font button thing for bold and stuff."*
**Method:** synthesized from a 3-angle design panel (reader-first / builder-first / minimal-change), all file:line-grounded against the live tree; the strongest idea from each taken. The three angles **converged** on the core mechanics (high confidence); they diverged on HOME skinning, the primary CTA target, and nav demotion — resolved below.

---

## The central decision (all three angles agree)

The shipped `.app`/`.exe` opens to a **maintainer tool**. `scripts/web.py:1457-1458` serves `INDEX_HTML` (the dense 3-pane raw-HTML note editor, `scripts/templates/index.py:21`) for `/`. A reader who double-clicked "a free Bible" lands on a `bg-slate-900` console with `Books | Notes | body(HTML) textarea`. **That is the north-star complaint.**

**Fix (one route move):** `/` → a new friendly `HOME_HTML`; the note editor moves to **`/notes`** (keep `/index.html` → editor for bookmarks, or 301). The launcher needs **zero** changes — `launcher.py:117` `build_url()` opens `http://localhost:<port>/` and the native/browser shells open that root, so the new landing becomes the first paint on every OS automatically.

```python
# scripts/web.py:1457-1458  (BEFORE)
if path == "/" or path == "/index.html":
    return self._send_html(INDEX_HTML)
# AFTER
if path == "/" or path == "/home":
    return self._send_html(HOME_HTML)
if path == "/notes" or path == "/index.html":
    return self._send_html(INDEX_HTML)
```

The audience split (from the console inventory): **end-user** = `wizard`, `build_my_bible`, `export`, `hebrew`, `greek` (+ `compare` as a public demo); **maintainer** = the note editor + `matrix`, `audit`, `audit_log`, `customize`, `publisher`, `covers`, `preflight`, `ops`, `apihelp`, `distribution`, `build_tracker`, `diff`. The app stays single-user/local — **demote by information-architecture, NOT auth/build-flags** (the solo user must never lose access to their own corpus). Demotion is reversible and zero-risk.

---

## (1) The landing page — `HOME_HTML` (new `scripts/templates/home.py`)

A single calm screen, no scroll needed for the primary action, no console header, no 20-link nav. Top→bottom:

1. **Hero band** — warm vellum (`--ms-vellum #F4ECD8`); `website/social-card.png` as the hero image (served same-origin, see routes below); the title in EB Garamond; one welcome line.
2. **ONE primary action** — a single large gold button (see *Color rule* below). **Label/target = the open question below.**
3. **A low-emphasis secondary row** — 2-3 indigo text-links (NOT gold): the other end-user doors (build / read-or-preview / Hebrew-Greek lookup).
4. **One quiet maintainer door** — small indigo footer link **"Maintainer tools"** → `/notes`. Demotion by *omission* + de-emphasis, not a 20-item menu. The reader's eye never lands there; the maintainer knows exactly where it is.

### ★ Resolved divergence — HOME must NOT load the Tailwind CDN (adopt the reader-first angle)
The η.1 skin guard (`_design.py:261`) only fires on pages that load `cdn.tailwindcss.com`. **`HOME_HTML` should hand-write ~30 lines of plain CSS** (using the `--ms-*` palette hex) and **not** load Tailwind. Rationale:
- It's the ONE surface every reader is guaranteed to see, so it must never flash half-skinned or hit the skin's CDN-timing race.
- It is structurally immune to **every** η.1-skin hazard the adversarial review found (`2026-06-09-eta1-skin-adversarial-review.md`): the blanket red card-top, recolored info pills, untouched emerald/amber status, the dark-mode clash. None can touch a CDN-free page.
- **Tradeoff:** ~10 palette hex are duplicated. **Mitigation (do this):** export a small `MS_PALETTE` dict/constant from `_design.py` and build `HOME_HTML`'s `<style>` from it — one source of truth, no drift.

(The builder-first/min-change angles proposed loading the CDN so HOME inherits the skin "for free"; rejected because it imports exactly the skin defects the review is telling WIN to fix, on the highest-traffic page.)

### Color rule for HOME + the app (honors the user + WCAG AA — see the skin review)
- **Gold** (`#B8860B` bg + `#2B2118` ink, 4.84:1 ✅) for **primary buttons** — the user loved these; keep them. Hover → a **lighter** gold `#C49A2E` (6.01:1 ✅), NOT the current darker `#9A6E12` (3.46:1 ✗).
- **Indigo** (`#243B6B`, 9.3–10.8:1 on the beige grounds ✅) for **links, secondary actions, focus rings, interactive accents** — the user's stated preference, and the accessible answer everywhere gold-as-text fails (2.76:1).
- **Gold-line** (`#9A6E12` solid) for **hairlines / borders / top-accent rules** only (decorative, passes UI 3:1).
- **Red** (`#7A1F2B`) for **destructive** (delete) + the existing theme-accent (hebrew/greek). See the *open question* on whether the primary should instead be red for strict site-parity.

---

## (2) The rich-text note editor — Bold/Italic toolbar, NO raw HTML

Maintainer-facing (now at `/notes`), but the user explicitly asked for it. Replace the `body (HTML)` textarea (`index.py:283-285`) with a `contenteditable` + a small toolbar. No framework, CSP-clean, normalizes to `<strong>`/`<em>` — which the existing `.preview` CSS already styles (`index.py:31-33`), so the editable surface *is* the rendered view (the separate preview pane `index.py:292-305` is deleted).

**DOM** (in `renderEditor`, `index.py:264-299`): a toolbar (`B` / `I` / `link` / `clear`) over `<div id="f-body" contenteditable="true" class="… preview">`. Initialize with `$('#f-body').innerHTML = d.body || ''` (NOT `escapeText` — that's what shows raw HTML today).

**Toolbar wiring** (inside the existing nonce'd `<script>`, so no CSP change): `document.execCommand('bold'|'italic'|'createLink'|'removeFormat')`. It's the only no-framework, no-dependency rich-text path and is universally implemented across the three shipped engines (WKWebView on the macOS frozen app, WebView2/Chromium on Windows, WebKitGTK on Linux). Ctrl/Cmd-B/I work natively in a `contenteditable`. Deprecated but fine for a single-user offline tool — and `normalizeBody` (below) makes the engine's exact output irrelevant.

**★ Normalize-on-save (MANDATORY — and a real security fix).** `execCommand` emits engine-dependent markup: WebKit emits **`<span style="font-weight:bold">`**, Chromium emits `<b>`. So `saveNote` must NOT post `innerHTML` verbatim. Run it through an **allowlist serializer** before `payload.body` (`index.py:330`) that: keeps only `strong`/`em`/`a[href]`/`br`; maps `<b>→<strong>`, `<i>→<em>`, **and styled `<span>`s** (`font-weight:bold`/`≥600` → `strong`; `font-style:italic` → `em`); unwraps everything else (keep text); validates `href` against `^(https?:|mailto:|#|/)`; HTML-escapes text nodes. *Use the builder-first/min-change `normalizeBody` that handles the styled-`<span>` case — WebKit (the macOS shipped engine) emits spans, so span-handling is load-bearing, not optional.* This is **strictly safer than today**: the current textarea POSTs arbitrary unsanitized HTML to `/api/notes`, and that body flows into EPUB output. Keep server-side sanitization as defense-in-depth regardless.

**Escape hatch:** keep an "Advanced: HTML source" `<details>` (collapsed by default, like the existing attribution-JSON `<details>` at `index.py:288-291`) holding the raw textarea for the rare note needing markup the toolbar can't express. Default = buttons-only; power not lost.

**Verify** in BOTH the frozen macOS WKWebView window and the Windows engine — the `execCommand` serialization differs, which is the one real verification cost (the normalize step de-risks it).

---

## (3) Maintainer-tool demotion (the nav)

The shared header nav is generated once from `CONSOLES` (`_design.py:2347-2368`) → `HEADER_NAV_LINKS` → applied to every console by `apply_design_system`. Today it's a flat 20-link row led by `("/", "note editor")`.

- **Ship first (lowest-risk, min-change angle):** in `CONSOLES`, add `("/home","home")` first, **relabel+move** `("/", "note editor")` → `("/notes","notes (maintainer)")` to the END. One edit demotes the editor across all 20 consoles at once. Update the cross-link-linter exception (§6.2, it currently exempts `/` for the editor) to `/notes`.
- **Fast-follow (builder-first angle, cleaner):** re-tier `CONSOLES` into **Build** (wizard, build-my-bible, customize, export) / **Read** (compare, hebrew, greek) / **Advanced ▾** (the maintainer set incl. the note editor), rendered as labeled groups. The note editor must never appear in the top tier — it's the surface the user named.

HOME itself shows none of this — just its own quiet footer "Maintainer tools" link.

---

## Static routes needed (shared with the EB-Garamond spec)
- **`/static/social-card.png`** — hardcoded path (`REPO/"website"/"social-card.png"`), no sandbox needed; `Content-Type image/png`, `Cache-Control public, max-age=86400`. `img-src 'self'` already allows it (CSP `web.py:1091`) — no CSP edit.
- **`/fonts/<name>.woff2`** — see `2026-06-09-app-eb-garamond-selfhosting.md` (sandboxed via `resolve_under(REPO/"website"/"fonts")`; bundle `website/fonts` in `launcher.spec` datas so it resolves frozen; no CSP edit — `font-src 'self'` already allows it). Self-hosting EB Garamond is what makes HOME (and the app) match the site's serif; do it with this arc.

---

## What stays maintainer-only (unchanged, reachable, demoted)
Note editor (`/notes`), `matrix`, `audit`, `audit_log`, `customize`, `publisher`, `covers`, `preflight`, `ops`, `apihelp`, `distribution`, `build_tracker`, `diff`. No auth, no skin change here — they keep their routes + behavior; only the IA changes.

---

## WIN implementation handoff (file:line)
1. New `scripts/templates/home.py` (`HOME_HTML`) — CDN-free, plain CSS from a new `MS_PALETTE` constant in `_design.py`; social-card hero; ONE gold primary CTA; indigo secondary links; footer "Maintainer tools" → `/notes`.
2. `scripts/web.py:1457-1458` — `/`→`HOME_HTML`; `/notes`(+`/index.html`)→`INDEX_HTML`; import `HOME_HTML`.
3. `scripts/web.py` ~`:1825` — add `/static/social-card.png` (hardcoded) + `/fonts/<name>.woff2` (sandboxed, per the font spec) branches.
4. `scripts/templates/_design.py:2347-2368` (`CONSOLES`) — add `("/home","home")` first; relabel+move editor to `("/notes",…)` last; update §6.2 linter exception to `/notes`. Add `MS_PALETTE` export.
5. `scripts/templates/index.py:264-305, :330` — textarea→toolbar+`contenteditable`; init via `innerHTML`; drop the preview pane; add `normalizeBody()` (with styled-`<span>` handling) at the `payload.body` site; add the collapsed raw-HTML `<details>` escape hatch.
6. Color: gold primary (lighter `#C49A2E` hover), indigo links/accents — coordinate with the η.1-skin review fixes.

## Open questions for the user
1. **Primary CTA target + label.** The honest fork: **(a) "Build my Bible →" → `/wizard`** (the flagship, fully working — recommended default) vs **(b) "Read the Bible →"** — but there is **no dedicated reader-render route yet**; the interim "read" target would be `/build-my-bible` (drill book→chapter→verse) or `/export`. If reading is the headline, we should add a first-class reader view (new scope). *Recommendation: ship "Build my Bible →" as the primary now; add "Read / preview" as a prominent secondary; decide whether a dedicated reader landing is a v0.1.0 or later item.*
2. **Primary-action COLOR.** Recommended default = **keep gold** (you loved it; AA-pass; lighter `#C49A2E` hover) + **indigo** for links/accents (your preference). The η.1-skin review's H7 offers an alternative: recolor the primary to **red** for strict site-parity (the site's CTA is red). Keeping gold honors your stated love and the gold-illumination identity (and ink-on-gold is NOT the "gold as text" the site forbids). Confirm gold-primary, or switch to red?
3. **Nav:** ship the flat reorder first, or go straight to grouped Build/Read/Advanced?
