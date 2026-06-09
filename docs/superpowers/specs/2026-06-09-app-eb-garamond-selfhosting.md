# Spec — Self-host EB Garamond (+ Noto Serif Ethiopic) in the desktop app

**Date:** 2026-06-09
**Status:** ready for implementation (WIN lane)
**Scope:** make the desktop-app consoles render in the *exact same* self-hosted
serif the public website ships (`website/style.css`), instead of silently
falling back to Georgia.

---

## 0. Why (problem statement)

The η.1 "manuscript skin" already re-tones every Tailwind console to the site's
manuscript palette and *asks for* `"EB Garamond"` in three places, but the app
never actually serves that font. The skin's own comment is explicit:

> `scripts/templates/_design.py:177-180`
> "Font: the site self-hosts EB Garamond; the app isn't serving it yet, so the
> stack falls back to Georgia (a faithful serif) — a later refinement can
> self-host EB Garamond to match exactly."

So today the console requests EB Garamond at:
- `_design.py:207-208` — Tailwind `fontFamily.sans` + `.serif`
- `_design.py:224` — `--font-stack-body` (the ζ.1 theme token)
- `_design.py:227` — `body { font-family: "EB Garamond", ... }`

…and every one of them resolves to **Georgia** because there is no
`@font-face` rule and no same-origin font byte source. The website, by
contrast, self-hosts five woff2 files and *does* render EB Garamond. The
consoles therefore do **not** match the site's actual rendering. This spec
closes that gap.

This is **console chrome only**. The EPUB build path embeds fonts via a
completely separate mechanism (`scripts/apply_style.py:108-148`,
`scripts/style_config.py`) and is **out of scope** — do not touch it.

---

## 1. Ground facts (verified file:line)

### 1.1 The site's `@font-face` block (the verbatim source of truth)
`website/style.css:6-27` — five self-hosted rules, all `format("woff2")`,
all relative `url("fonts/<name>.woff2")`, `font-display: swap`:

| family | style | weight | file |
|---|---|---|---|
| EB Garamond | normal | 400 | `eb-garamond-latin-400-normal.woff2` |
| EB Garamond | italic | 400 | `eb-garamond-latin-400-italic.woff2` |
| EB Garamond | normal | 600 | `eb-garamond-latin-600-normal.woff2` |
| EB Garamond | normal | 700 | `eb-garamond-latin-700-normal.woff2` |
| Noto Serif Ethiopic | normal | 400 | `noto-serif-ethiopic-ethiopic-400-normal.woff2` (`unicode-range: U+1200-137F, U+1380-139F, U+2D80-2DDF, U+AB00-AB2F`) |

Files confirmed present on disk in `website/fonts/` (sizes: 400-italic 22172 B,
400-normal 21704 B, 600-normal 23112 B, 700-normal 23076 B, ethiopic
49732 B), alongside `OFL-EBGaramond.txt`, `OFL-NotoSerifEthiopic.txt`,
`README.md`. License: **SIL OFL 1.1** — no attribution-in-UI requirement, but
the OFL text files must ship with the fonts.

### 1.2 The app server + static-serving model
- App = `scripts.web.Handler` (a `BaseHTTPRequestHandler`), launched by
  `scripts/launcher.py` (native pywebview window when frozen, browser
  otherwise; same localhost server on all 3 OSes).
- `REPO = Path(__file__).resolve().parent.parent` — `scripts/web_helpers.py:25`
  (re-exported into `scripts.web` at `web.py:63`). **In a frozen PyInstaller
  build, `__file__` resolves inside the bundle, so `REPO` points at the bundle
  root, NOT the dev repo on disk.** This is why the existing static routes work
  frozen *only because their dirs are bundled* (see §2).
- Static assets are hand-rolled `if` branches at the **bottom** of `do_GET`,
  after the table-driven dispatch and the `/` → INDEX_HTML branch
  (`web.py:1457-1458`). There is **no** generic static-directory handler.
  - favicon: `web.py:1801-1817` — reads `REPO / "assets" / "icons" /
    "program_icon.ico"`, `Content-Type image/x-icon`, `Cache-Control
    public, max-age=86400`. **Hardcoded filename → no sandboxing.**
  - matrix JS: `web.py:1825-1840` — reads `REPO / "scripts" / "templates" /
    "matrix_app.js"`, `Content-Type application/javascript; charset=utf-8`,
    `Cache-Control private, max-age=300`. **Hardcoded filename → no sandboxing.**
  - covers: `web.py:1846-1865` — `path` after `/content/covers/` is
    **user-supplied**, so it sandboxes via `scripts.core.safe_path.resolve_under`
    (`web.py:1851-1858`) then `self._send_file`.
- Path-safety helper: `scripts.core.safe_path.resolve_under(safe_root,
  user_path)` (`scripts/core/safe_path.py:95-137`) — rejects empty / >1024 /
  absolute / `..` / hidden / control-char / UNC, then `resolve()` +
  `relative_to()` containment against `safe_root.resolve()`. Raises
  `SafePathError`. **Use it for any route whose filename comes from the URL.**

### 1.3 The CSP (no edit required)
- Base policy `web.py:1086-1096` (`_CSP_POLICY`) — used by `_send_json`
  (`web.py:1199`), `_send_file` (`web.py:1308`), and any `nonce=None` response.
  `font-src 'self' data:;` is **`web.py:1091`**.
- Strict per-request policy `web.py:1124-1134` (`_csp_with_nonce`) — used by
  HTML responses (`_send_html` → `_send_security_headers(nonce=nonce)`,
  `web.py:1243`). Identical to base except `script-src` gets the nonce and
  drops `'unsafe-inline'`. **`font-src 'self' data:;` is unchanged at
  `web.py:1129`.** `style-src` keeps `'unsafe-inline'` (`web.py:1127`).
- **Conclusion:** `font-src 'self'` already permits same-origin woff2. The
  font bytes are served by the same localhost origin as the console HTML, so
  `'self'` covers them. The `@font-face` lives in the skin's inline `<style>`,
  which passes via `style-src 'unsafe-inline'`. **No CSP header change is
  needed for any policy.** (Adding the fonts via `data:` URIs would also pass
  under `'data:'`, but bloats HTML — use the route, per §3.)

### 1.4 The skin injection (where the `@font-face` will land)
- `MANUSCRIPT_SKIN_CSS` = `_design.py:183-252`. One inline `<script>`
  (184-211, the Tailwind config remap) + one inline `<style>` (212-252).
- Injected by `apply_manuscript_skin()` `_design.py:255-263`; guard at
  `:261` (idempotency sentinel `"manuscript-skin"`, requires
  `"cdn.tailwindcss.com"` present + `"</head>"` present); single `.replace`
  at `:263` inserts the block just before `</head>`.
- Called from `_send_html` at `web.py:1235`, **before** nonce injection
  (`web.py:1237-1238`) — so the skin's `<script>` gets the per-request nonce.
- The skin reaches **all 20 consoles** + the note editor at `/` (every page
  loads `cdn.tailwindcss.com`); only `scripts/templates/__init__.py` lacks the
  CDN line. So adding `@font-face` to the skin font-loads the *entire* console
  surface in one edit.

### 1.5 The frozen-bundle gotcha (the load-bearing constraint)
`dev/launcher.spec:93-107` bundles exactly three data trees:
`content` → `content`, `scripts/templates` → `scripts/templates`,
`epub_working` → `epub_working`. **`website/` is NOT bundled** (confirmed:
`grep website dev/launcher.spec` → no match). Therefore in a frozen build
`REPO / "website" / "fonts"` **does not exist** and a route reading from there
would 404 in the shipped app while working fine in `pyinstaller`-less dev.
This is the exact class of bug the prior finding-7 / WinError-3 fixes hit:
**files must be in `launcher.spec` `datas` and resolved via the bundle-relative
`REPO`, not a loose disk path.** §2 fixes this.

---

## 2. Deliverable (a): bundle the woff2 into the app

The font byte source-of-truth is `website/fonts/` (the same files the site
ships — reuse them; do **not** duplicate into `assets/`). Two options; **pick
Option A** (keeps `website/fonts` as the single source for both site and app):

### Option A (RECOMMENDED) — bundle `website/fonts` directly
Add ONE entry to `a.datas` in `dev/launcher.spec` (the list at lines 93-107),
mapping the on-disk `website/fonts` to a bundle-relative `website/fonts`:

```python
# In a = Analysis(..., datas=[ ... ]) at dev/launcher.spec:93-107, add:
        # Self-hosted UI fonts (SIL OFL 1.1) so the frozen app's manuscript
        # skin renders EB Garamond + Noto Serif Ethiopic exactly like the
        # public website, instead of falling back to Georgia. Served by the
        # /fonts/<name>.woff2 route (scripts/web.py). Source = the SAME files
        # the website ships (website/fonts/), so site + app stay byte-identical.
        (str(ROOT / "website" / "fonts"), "website/fonts"),
```

This makes `REPO / "website" / "fonts" / "<name>.woff2"` resolve correctly in
**both** dev (loose disk) and frozen (`_MEIPASS`/bundle root) because
`REPO = __file__.parent.parent` lands on the bundle root when frozen and the
data tree is bundled at the matching relative path.

The `_DROP_PREFIXES` filter (`launcher.spec:128-133`) drops only
`content/candidates`, `content/translations/sources`, `epub_working/.backups`
— `website/fonts` is untouched. The OFL text files + README in `website/fonts`
ride along (≈150 KB total for the whole tree; the five woff2 are ≈140 KB) —
acceptable, and shipping the OFL texts with the fonts is license-correct.

> **Do NOT** point `@font-face` at `assets/icons` or copy fonts there — that
> splits the source of truth. `website/fonts/` already exists in-repo on all 3
> OSes and is the same path the site resolves.

### Option B (only if WIN prefers fonts under `scripts/templates/`)
`scripts/templates/` is *already* bundled (`launcher.spec:101`). You could
`git mv website/fonts → scripts/templates/fonts` and update `website/style.css`
`url(...)` paths — but that breaks the site's relative `fonts/` convention and
the `website/fonts/README.md` documentation. **Not recommended.** Use A.

**No code in `scripts/` resolves `website/fonts` today** (confirmed: `grep -rn
"/fonts/\|website.*fonts\|woff2" scripts/` finds only the unrelated EPUB
`apply_style.py`/`style_config.py` embed path). So §2 + §3 together are the
first consumer.

---

## 3. Deliverable (b): the `/fonts/<file>.woff2` static route

Add a new `if` branch in `do_GET`, alongside the other static routes (after the
`/static/matrix.js` branch ending `web.py:1840`, before `/content/covers/` at
`web.py:1846` — keep the static cluster together). Model it on the
**covers** route (not favicon/matrix.js) because the filename is **user-supplied
from the URL** and must be sandboxed.

```python
# Self-hosted UI-font route — serves website/fonts/*.woff2 so the η.1
# manuscript skin renders EB Garamond + Noto Serif Ethiopic same-origin
# (font-src 'self', web.py:1091/1129 — no CSP change). Read-only. The
# filename comes from the URL, so sandbox via resolve_under like /content/
# covers/ does (web.py:1851-1858); restrict to .woff2 as a belt-and-braces
# guard. Source dir is bundled by dev/launcher.spec (website/fonts), so
# REPO/'website'/'fonts' resolves in both dev and the frozen .app.
if path.startswith("/fonts/") and path.endswith(".woff2"):
    rel = path[len("/fonts/"):]
    from scripts.core.safe_path import SafePathError, resolve_under

    fonts_root = REPO / "website" / "fonts"
    try:
        file_path = resolve_under(fonts_root, rel)
    except SafePathError:
        return self._send_json({"error": "forbidden"}, status=403)
    if not file_path.is_file():
        return self._send_json({"error": "not found"}, status=404)
    try:
        data = file_path.read_bytes()
    except OSError:
        return self._send_json({"error": "not found"}, status=404)
    self.send_response(200)
    self.send_header("Content-Type", "font/woff2")
    self.send_header("Content-Length", str(len(data)))
    # Public cache OK — fonts are static + immutable + non-sensitive
    # (same posture as favicon, web.py:1813).
    self.send_header("Cache-Control", "public, max-age=86400")
    self._send_security_headers()
    self.end_headers()
    self.wfile.write(data)
    return
```

Route contract:
- **Content-Type:** `font/woff2` (the registered media type for woff2;
  RFC 8081). Do not use `application/font-woff2` (legacy/incorrect).
- **Caching:** `public, max-age=86400` — fonts are static + immutable +
  non-sensitive, matching the favicon posture (`web.py:1813`). (`_send_file`'s
  `private, max-age=60` is for editorial content; fonts are not editorial.)
- **Path-safety:** `resolve_under(REPO/'website'/'fonts', rel)` +
  `.endswith(".woff2")` guard. The covers route is the precedent
  (`web.py:1851-1858`); favicon/matrix.js skip sandboxing only because they
  hardcode their filename — this route does not, so sandboxing is mandatory.
- **Security headers:** `self._send_security_headers()` with `nonce=None` →
  base `_CSP_POLICY` (a font byte stream has no inline scripts; that's correct,
  same as `_send_file`/`_send_json`).
- **Methods:** GET only (this is `do_GET`); no `do_POST` branch.

> Optionally factor the 9-line read/headers/write tail into a tiny
> `_send_font(file_path)` helper next to `_send_file` (`web.py:~1300`) — not
> required; the inline form above mirrors the existing favicon/matrix.js style
> and is fine for one route.

---

## 4. Deliverable (c): the `@font-face` + `font-family` rules in the skin

Add the five `@font-face` rules to the skin's inline `<style>` block in
`scripts/templates/_design.py`. Insert them at the **top** of the `<style>`
(right after the opening `<style>` at `:212`, before the `:root` block at
`:214`), so the faces are declared before the rules that use them.

Match the site (`website/style.css:7-27`) **verbatim** except the `url(...)`
must point at the **app's absolute `/fonts/` route** (the site uses relative
`fonts/...` because it resolves relative to `/style.css`; the app injects the
skin into many different console URLs, so it must use an **absolute** path):

```css
  /* η.1: self-hosted UI fonts (SIL OFL 1.1) — match website/style.css:7-27
     exactly so the console renders EB Garamond, not the Georgia fallback.
     url() is absolute (/fonts/...) because the skin is injected into many
     console paths; served same-origin by the /fonts route (font-src 'self'). */
  @font-face {
    font-family: "EB Garamond"; font-style: normal; font-weight: 400; font-display: swap;
    src: url("/fonts/eb-garamond-latin-400-normal.woff2") format("woff2");
  }
  @font-face {
    font-family: "EB Garamond"; font-style: italic; font-weight: 400; font-display: swap;
    src: url("/fonts/eb-garamond-latin-400-italic.woff2") format("woff2");
  }
  @font-face {
    font-family: "EB Garamond"; font-style: normal; font-weight: 600; font-display: swap;
    src: url("/fonts/eb-garamond-latin-600-normal.woff2") format("woff2");
  }
  @font-face {
    font-family: "EB Garamond"; font-style: normal; font-weight: 700; font-display: swap;
    src: url("/fonts/eb-garamond-latin-700-normal.woff2") format("woff2");
  }
  @font-face {
    font-family: "Noto Serif Ethiopic"; font-style: normal; font-weight: 400; font-display: swap;
    src: url("/fonts/noto-serif-ethiopic-ethiopic-400-normal.woff2") format("woff2");
    unicode-range: U+1200-137F, U+1380-139F, U+2D80-2DDF, U+AB00-AB2F;
  }
```

> Note: `MANUSCRIPT_SKIN_CSS` is a Python triple-quoted string. The `@font-face`
> block has no backslashes, so nothing needs escaping (unlike the existing
> `.hover\\:bg-blue-700:hover` at `_design.py:237`, which doubles its backslash).

### 4.1 Add Noto Serif Ethiopic to the font stacks (NEW — needed for Ge'ez)
The current font stacks (`_design.py:207-208`, `:224`, `:227`) name only
EB Garamond + Georgia/Times fallbacks. EB Garamond has **no Ethiopic
glyphs**, so any Ge'ez/Amharic text in a console (Hebrew/Greek lexicon
neighbors, parallel-Bible previews, edition names) would render tofu or a
system fallback. Append `"Noto Serif Ethiopic"` to each stack so the
unicode-range face covers Ethiopic codepoints while EB Garamond covers Latin.
Update **all three** sites so they stay identical:

- `_design.py:207` (Tailwind `sans`):
  `['"EB Garamond"','"Noto Serif Ethiopic"','Georgia','"Times New Roman"','serif']`
- `_design.py:208` (Tailwind `serif`): same as above.
- `_design.py:224` (`--font-stack-body`):
  `"EB Garamond", "Noto Serif Ethiopic", Georgia, "Times New Roman", serif`
- `_design.py:227` (`body { font-family: ... }`): same as `:224`.

(The Ethiopic face's `unicode-range` means it only loads when Ethiopic
codepoints are actually present — zero cost on Latin-only consoles, per
`font-display: swap` + range scoping. This mirrors the site, which also lists
Noto Serif Ethiopic for the same reason.)

### 4.2 Update the stale comment
`_design.py:177-180` currently says EB Garamond "isn't serving it yet … falls
back to Georgia." After this change that is false. Replace with a note that the
app now self-hosts the fonts via the `/fonts/` route + `launcher.spec` bundle
(point to this spec).

---

## 5. Deliverable (d): the CSP implication (cite current policy)

**No CSP header edit is required.** The app's font policy already permits
same-origin woff2 in **both** policies:

- Base `_CSP_POLICY` — `font-src 'self' data:;` at **`web.py:1091`**.
- Strict per-request `_csp_with_nonce` — `font-src 'self' data:;` at
  **`web.py:1129`** (the nonce only touches `script-src`, `web.py:1126`).

Because the `/fonts/` route (§3) serves the woff2 from the **same localhost
origin** as the console HTML, `'self'` covers it. The `@font-face` declaration
itself is inline CSS inside the skin's `<style>`, permitted by `style-src
'unsafe-inline'` (`web.py:1127`, kept on purpose for Tailwind Play). The skin's
`<script>` continues to pass via the per-request nonce (`web.py:1235` runs
before `web.py:1238`).

**Do not** add a CDN host to `font-src` and **do not** point `@font-face` at an
external URL — that breaks the no-CDN/self-host doctrine and would require a
policy edit. Same-origin route only.

---

## 6. Verification (how WIN proves it works)

1. **Dev (unfrozen):** start the app, open any console (e.g. `/wizard`).
   - DevTools → Network: `GET /fonts/eb-garamond-latin-400-normal.woff2`
     returns `200`, `Content-Type: font/woff2`, `Cache-Control: public,
     max-age=86400`.
   - DevTools → Elements/Computed on `body`: `font-family` resolves to
     `"EB Garamond"` and the **rendered** font is EB Garamond (compare a cap
     `Q`/ampersand glyph against the live site `www.yhwhyaway.com`), not
     Georgia.
   - No CSP violation in the console for `font-src`.
   - Path-safety: `GET /fonts/../../etc/passwd` and `GET /fonts/..%2f..%2f` →
     `403`; `GET /fonts/nope.woff2` → `404`; `GET /fonts/foo.txt` → falls
     through (does not match the `.woff2` guard).
2. **Ethiopic:** a console surface containing Ge'ez (or inject a test string)
   renders via Noto Serif Ethiopic, not tofu.
3. **Frozen (the load-bearing test):** rebuild the bundle
   (`pyinstaller dev/launcher.spec`) and launch the **frozen** app. Confirm
   `GET /fonts/eb-garamond-latin-400-normal.woff2` still returns `200` from the
   bundle (this is the §1.5 gotcha — it passes only if `website/fonts` is in
   `datas`). Run on macOS (.app, the lane that hit finding-7) **and** Windows
   (.exe) since the bundle path resolution differs per OS.
4. **Regression:** the favicon, `/static/matrix.js`, and `/content/covers/`
   routes still work (you added a sibling branch, didn't reorder existing
   ones). Run the existing web/handler test suite.

---

## 7. Out of scope (do not touch in this change)

- The EPUB build's font embedding (`scripts/apply_style.py:108-148`,
  `scripts/style_config.py`) — entirely separate from console chrome.
- The note-editor (`index.py`) raw-HTML → bold/italic-toolbar rework and the
  "separate the maintainer editor from the default landing" north-star — those
  are a different surface/spec; this change only adds fonts (the editor *does*
  get the fonts for free since the skin reaches `/`, which is fine).
- The η.1 skin's other known retone hazards (info-pill recolor, untouched
  status colors, unconditional red card-top, dark-mode clash, CDN-config
  timing). Documented for awareness in the skin facts; **not** part of this
  font change.
- Any CSP header edit (see §5 — none needed).

---

## 8. WIN implementation handoff (file:line)

Three edits + one new route. All paths absolute from repo root.

1. **`dev/launcher.spec`** — add ONE `datas` entry inside `a = Analysis(...,
   datas=[ ... ])` at **`dev/launcher.spec:93-107`**:
   `(str(ROOT / "website" / "fonts"), "website/fonts")`. (§2 Option A.)
   The `_DROP_PREFIXES` filter at `launcher.spec:128-133` does not need
   changing (it doesn't match `website/fonts`).

2. **`scripts/web.py`** — add the `/fonts/<file>.woff2` GET branch in `do_GET`,
   **between** the `/static/matrix.js` branch (ends **`web.py:1840`**) and the
   `/content/covers/` branch (starts **`web.py:1846`**). Sandbox via
   `scripts.core.safe_path.resolve_under(REPO / "website" / "fonts", rel)`
   (precedent: covers route `web.py:1851-1858`), `Content-Type font/woff2`,
   `Cache-Control public, max-age=86400`, `self._send_security_headers()`
   (nonce=None). Full body in §3. `REPO` is in scope (re-exported at
   `web.py:63`).

3. **`scripts/templates/_design.py`** — inside `MANUSCRIPT_SKIN_CSS`:
   - Insert the five `@font-face` rules at the top of the `<style>` block,
     right after the opening `<style>` at **`_design.py:212`** (before the
     `:root` at `:214`). `url()` is absolute `/fonts/<name>.woff2`. Verbatim
     match to `website/style.css:7-27` except the url path. (§4.)
   - Append `"Noto Serif Ethiopic"` to the font stacks at **`_design.py:207`**,
     **`:208`**, **`:224`**, **`:227`** (all four, kept identical). (§4.1.)
   - Update the stale "isn't serving it yet … Georgia" comment at
     **`_design.py:177-180`**. (§4.2.)

4. **No CSP edit.** `font-src 'self' data:;` already present at
   **`web.py:1091`** (base) and **`web.py:1129`** (strict). (§5.)

5. **Before save:** `ruff format` the touched `.py` files (pre-commit
   `ruff format --check .` will block otherwise). The `.spec` is Python too.

6. **Verify per §6**, including the **frozen** rebuild on macOS + Windows
   (the §1.5 bundle-path gotcha only surfaces frozen).
