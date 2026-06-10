# Build yhwh-kobo-font-pack.zip — the K-R2-3 sideloadable Kobo font pack.
# Recipe: docs/superpowers/notes/2026-06-09-kobo-font-pack.md (Mac prep, 2026-06-09).
# Ship gate: the user's staged-fonts eyeball (does the Kobo preview dialog follow
# a selected reading font?) — build any time; UPLOAD only after the gate passes
# (gh release upload + re-merge SHA256SUMS.txt + apply the Guide copy §3).
#
# Usage:  pwsh -File dev/build_font_pack.ps1   (from the repo root)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$fonts = Join-Path $repo "content/assets/fonts"
$out = Join-Path $repo "dist"
$stage = Join-Path ([IO.Path]::GetTempPath()) "yhwh-font-pack-stage"

if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force $stage | Out-Null
New-Item -ItemType Directory -Force $out | Out-Null

# The five ttf files — names are LOAD-BEARING (the website Guide quotes them).
$ttfs = @(
    "Cardo-Regular.ttf",
    "Cardo-Italic.ttf",
    "Cardo-Bold.ttf",
    "NotoSerifEthiopic-Regular.ttf",
    "NotoNaskhArabic-Regular.ttf"
)
foreach ($f in $ttfs) {
    $src = Join-Path $fonts $f
    if (-not (Test-Path $src)) { throw "missing font: $src" }
    Copy-Item $src $stage
}

# README.txt — the plain-text twin of the Guide steps (font-pack note §3).
@'
YHWH Ya' Way — Kobo font pack
=============================

Better Hebrew, Greek, Ge'ez and Arabic on your Kobo.

Kobo's quick note pop-ups use your reader's own font, which often
lacks these alphabets (you'll see hollow boxes). These free fonts
fix that:

  Cardo-Regular.ttf / Cardo-Italic.ttf / Cardo-Bold.ttf
      Hebrew, polytonic Greek and Latin
  NotoSerifEthiopic-Regular.ttf
      Ge'ez / Amharic fidel
  NotoNaskhArabic-Regular.ttf
      Arabic (the Van Dyck translation pop-ups)

Install
-------
1. Unzip this file.
2. Connect your Kobo with the USB cable. In the Kobo's drive, make
   a folder called  fonts  at the top level (next to the .kobo
   folder) if it isn't already there.
3. Copy the five .ttf files into that fonts folder and eject the
   Kobo.
4. On the Kobo, open the Bible, tap the centre of the page, open
   the Aa (text) settings, then Font face, and choose Cardo.

All five fonts are released under the SIL Open Font License 1.1
(see LICENSE-OFL.txt). They are free to use, copy and share.
'@ | Set-Content (Join-Path $stage "README.txt") -Encoding utf8

# LICENSE-OFL.txt — the authoritative OFL 1.1 text. Standalone font
# redistribution MUST carry the license (unlike in-EPUB embedding).
$ofl = Join-Path $fonts "OFL.txt"
if (-not (Test-Path $ofl)) { throw "missing $ofl - commit the OFL 1.1 text next to the fonts first" }
Copy-Item $ofl (Join-Path $stage "LICENSE-OFL.txt")

$zip = Join-Path $out "yhwh-kobo-font-pack.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip
Remove-Item -Recurse -Force $stage

$h = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
"built: $zip"
"sha256: $h"
"size: $((Get-Item $zip).Length) bytes"
