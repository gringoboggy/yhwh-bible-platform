# YHWH program icon pack

Pre-rendered icon assets for the program binary, web
favicon, and desktop entry points. Ingested 2026-05-11.

## Source

Original Midjourney generation, cleaned + refined:
- Garbled embossed text on top/bottom of gold frame erased
  and reconstructed
- Stray Midjourney "©" hallucination next to the H removed
  (cloned from the symmetric iridescent pattern opposite)
- Transparent background isolated from the octagon body for
  clean icon use

## Files

### Master sources

| File | Purpose |
|---|---|
| `program_icon_2048.png` | Full-res opaque master (black background) |
| `program_icon_2048_transparent.png` | Full-res transparent master |
| `program_icon.ico` | Windows multi-resolution icon (embeds 16/32/48/64/128/256) |

### Pre-rendered sizes (all transparent PNG)

`icon_16.png`, `icon_24.png`, `icon_32.png`, `icon_48.png`,
`icon_64.png`, `icon_96.png`, `icon_128.png`, `icon_192.png`,
`icon_256.png`, `icon_384.png`, `icon_512.png`, `icon_1024.png`.

## Usage targets

| Target | File | Reference |
|---|---|---|
| PyInstaller (Windows .exe) | `program_icon.ico` | `pyinstaller --icon=assets/icons/program_icon.ico` |
| macOS .icns | derive from `icon_1024.png` (or all sizes) | future θ.4 phase; needs `iconutil` (macOS) or `pyicns-utils` (cross-platform) |
| Linux desktop entry | `icon_512.png` or `icon_1024.png` | `.desktop` file's `Icon=...` field |
| Web favicon | `program_icon.ico` | `<link rel="icon" href="/favicon.ico">` |
| Web touch icon (iOS, Android) | `icon_192.png` (or 512) | `<link rel="apple-touch-icon">` |
| Web manifest icons (PWA) | `icon_192.png` + `icon_512.png` | `manifest.json` icons array |

## Web favicon wiring

The web favicon is served from `scripts/web.py`'s
`/favicon.ico` route. As of 2026-05-11 the route returns
the contents of `assets/icons/program_icon.ico` directly
(no separate copy needed under `scripts/templates/`).

## Build pipeline notes

- The pack is pre-rendered — `scripts/build_icons.py`
  (planned in PROPOSAL_AI_ARTWORK.md §6) is no longer
  needed. Defer / skip.
- If you ever want to regenerate sizes (e.g. updated master
  art), the standard Python pipeline is:
  ```python
  from PIL import Image
  src = Image.open('icon_2048_transparent.png')
  for size in (16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 1024):
      src.resize((size, size), Image.LANCZOS).save(f'icon_{size}.png')
  ```
- The `.ico` packing is done via Pillow's `save(format='ICO',
  sizes=[(16,16), (32,32), ...])`.

## Total footprint

~8 MB for the entire pack (15 files). Reasonable for a
project that ships a desktop binary + a web console.
