"""HOME_HTML — the friendly default landing for the shipped app (v0.1.0 app-UX arc).

Spec: docs/superpowers/specs/2026-06-09-idiot-proof-app-design.md §1.
Colors: docs/superpowers/notes/2026-06-09-home-html-aa-colors.md (per-element AA).

Design constraints (load-bearing, do not "modernize" away):

- **CDN-free + JS-free.** This is the ONE surface every reader is guaranteed to
  see, so it must never flash half-skinned or hit the Tailwind-CDN timing race —
  and with zero ``<script>`` it has no CSP/nonce dependency at all. The η.1 skin
  pass (``apply_manuscript_skin``) is a structural no-op here (it only fires on
  pages that load the CDN).
- **The <style> is built from ``MS_PALETTE``** (one source of truth; no palette
  drift between HOME and the skin).
- **Gold is a fill or a hairline, never a text color** (2.76:1 on vellum fails
  AA). The single gold element is the primary CTA button; everything interactive
  besides it is indigo. Hover gold goes LIGHTER (#C49A2E), never darker.
- **One primary action.** "Build my Bible" -> /wizard (user-ratified default);
  the other end-user doors are low-emphasis indigo links; the maintainer door is
  a single quiet footer link to /notes. Demotion by information-architecture,
  not auth — the solo user never loses access to anything.
"""

from scripts.templates._design import MS_PALETTE as _P

HOME_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>YHWH Ya' Way · a free Bible publishing studio</title>
<style>
  /* Self-hosted faces (same files the site + skin use, via the /fonts/ route) —
     HOME is CDN-free so it must declare its own @font-face or EB Garamond only
     renders where the OS has it installed. font-src 'self' already allows it. */
  @font-face {{ font-family: "EB Garamond"; font-style: normal; font-weight: 400; font-display: swap;
                src: url("/fonts/eb-garamond-latin-400-normal.woff2") format("woff2"); }}
  @font-face {{ font-family: "EB Garamond"; font-style: normal; font-weight: 700; font-display: swap;
                src: url("/fonts/eb-garamond-latin-700-normal.woff2") format("woff2"); }}
  @font-face {{ font-family: "Noto Serif Ethiopic"; font-style: normal; font-weight: 400; font-display: swap;
                src: url("/fonts/noto-serif-ethiopic-ethiopic-400-normal.woff2") format("woff2");
                unicode-range: U+1200-137F, U+1380-139F, U+2D80-2DDF, U+AB00-AB2F; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh; display: flex; flex-direction: column;
    background: {_P["vellum"]}; color: {_P["ink"]};
    font-family: "EB Garamond", "Noto Serif Ethiopic", Georgia, "Times New Roman", serif;
    text-align: center;
  }}
  main {{ flex: 1; display: flex; flex-direction: column; align-items: center;
         justify-content: center; padding: 2rem 1.25rem; gap: 0; }}
  .hero-art {{ max-width: min(34rem, 92vw); width: 100%; height: auto;
               border: 1px solid {_P["gold_line"]}; border-radius: 0.5rem; display: block; }}
  h1 {{ font-size: 2rem; margin: 1.4rem 0 0.3rem; font-weight: 700; letter-spacing: 0.02em; }}
  .welcome {{ color: {_P["sepia"]}; font-size: 1.12rem; margin: 0 0 1.8rem; max-width: 36rem; }}
  .cta {{
    display: inline-block; background: {_P["gold"]}; color: {_P["ink"]};
    font-size: 1.18rem; font-weight: 700; text-decoration: none;
    padding: 0.85rem 2.2rem; border-radius: 0.5rem;
    border-top: 3px solid {_P["gold_line"]};
  }}
  .cta:hover {{ background: {_P["gold_hover"]}; }}
  .doors {{ margin: 1.6rem 0 0; display: flex; flex-wrap: wrap; gap: 0.4rem 1.6rem;
            justify-content: center; }}
  .doors a {{ color: {_P["indigo"]}; font-size: 1.0rem; }}
  .fineprint {{ color: {_P["muted"]}; font-size: 0.86rem; margin-top: 1.7rem; }}
  hr {{ border: 0; border-top: 1px solid {_P["gold_line"]}; width: min(20rem, 70vw);
        margin: 1.8rem auto 0; opacity: 0.65; }}
  footer {{ padding: 0.9rem; }}
  footer a {{ color: {_P["indigo"]}; font-size: 0.86rem; }}
  a:focus-visible, .cta:focus-visible {{ outline: 2px solid {_P["indigo"]}; outline-offset: 2px; }}
</style>
</head>
<body>
<main>
  <img class="hero-art" src="/static/social-card.png"
       alt="YHWH Ya' Way — illuminated-manuscript banner art"/>
  <h1>YHWH Ya&#8217; Way</h1>
  <p class="welcome">Read the Scriptures and build your own study Bible &#8212;
  free, on your own computer.</p>
  <a class="cta" href="/wizard">Build my Bible &#8594;</a>
  <nav class="doors" aria-label="More">
    <a href="/build-my-bible">Browse books &amp; notes</a>
    <a href="/hebrew">Hebrew lexicon</a>
    <a href="/greek">Greek lexicon</a>
  </nav>
  <p class="fineprint">Free &#183; runs entirely on your computer &#183; no account needed</p>
  <hr/>
</main>
<footer>
  <a href="/notes">Maintainer tools</a>
</footer>
</body>
</html>"""
