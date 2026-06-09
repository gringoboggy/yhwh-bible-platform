# Frozen desktop note-editor "failed to load" — ROOT CAUSE + FIX (cross-platform) + M1 dmg COMPLETE

**Lane:** 🖥️ Mac · **Turn 41 · 2026-06-08** · found in M1 device-QA of the rebuilt macOS `.app` (user eyeball on the live native window).
**Verdict:** ✅ **Real release defect — the frozen desktop note-editor was broken on ALL 3 OSes — now FIXED + verified on the rebuilt frozen `.app`.** M1 (native-window dmg) is also fully closed.

---

## The bug (user-observed, then proven)
On the freshly-rebuilt frozen macOS `.app`, the note-editor opened with a rose **"failed to load"** toast (bottom-right) and the left **book list stuck on "loading…"**. The user noted it also happened "when it was just a web loader" — i.e. shell-independent.

Proven empirically by curling the running frozen app's own server (port via `lsof -nP -iTCP -sTCP:LISTEN -a -p <pid>`):
- `GET /api/books` → **works** (real data; gen = 4903 notes).
- `GET /api/kinds` → **`{"error":"internal_error","message":"unhandled FileNotFoundError in do_GET"}`**.

`scripts/templates/index.py:127` inits via `Promise.all([api('/api/books'), api('/api/kinds')])` — so `/api/kinds` throwing rejects the whole load → the "failed to load" toast fires and the book list never renders.

## Root cause (a frozen-build packaging class, NOT a content/bootstrap issue)
`scripts/web_helpers.py` lazily loaded two sibling scripts via a **disk path**:
```python
spec = importlib.util.spec_from_file_location("_note_quality", REPO / "scripts" / "note_quality.py")
spec.loader.exec_module(mod)   # reads the .py FROM DISK
```
A PyInstaller-frozen build ships **no loose `scripts/*.py` on disk** (the source lives in the bundled PYZ archive — confirmed: `Contents/Resources/scripts/` contains only `templates/`). So `REPO/scripts/note_quality.py` does not exist → `FileNotFoundError` at request time. Dev passes because the file is on disk.

This funnels through `_nq()`/`_nn()`, so the **whole note editor was broken when frozen**:
- `/api/kinds` (kind taxonomy → book-list load) — `_nq()`
- `/api/template` (new-note scaffold) — `_nn()`
- `quality_for()` via `/api/notes` (viewing any book's notes) — `_nq()`

It is **OS-independent** (PyInstaller behaves the same on Windows `.exe` + Linux AppImage) and **shell-independent** (native window AND `--shell browser`).

## The fix — `scripts/web_helpers.py`
Import the siblings as normal **package modules** instead of from a disk path:
```python
def _load_note_quality_helpers():
    from scripts import note_quality
    return note_quality

def _load_new_note_helpers():
    from scripts import new_note
    return new_note
```
Resolves from the PYZ archive when frozen AND from disk in dev; PyInstaller's static analysis detects these function-body imports so the modules get bundled. Both scripts are import-safe (argparse lives inside `main()` under `if __name__ == "__main__"`). Fixes the whole class at once (one change → all three endpoints). Class-scan confirmed only these two request-time `spec_from_file_location` loaders exist in the web layer (`migrate.py:102` is a legitimate migration-file loader, not request-time).

## Regression guard — `tests/test_desktop_theta.py::TestFrozenSafeScriptLoaders`
Simulates the frozen condition by monkeypatching `web_helpers.REPO` to a nonexistent path (no loose `scripts/` tree): the old disk-path loader would `FileNotFoundError`, the package import is unaffected. Proven **non-vacuous** (the old pattern raises `FileNotFoundError` under that REPO). 3 tests: both loaders + an end-to-end `api_kinds()` assertion.

## Verified on the REBUILT frozen `.app`
`./dev/build_desktop.sh` (PyInstaller via `.venv`, exit 0) → launched `dist/YHWH.app --skip-bootstrap --port 0`:
- `/api/kinds` → ✅ **72 kinds** (was FileNotFoundError).
- `/api/books` → ✅ **87 books, 91,733 notes**.
- Screenshot of the working editor (book list fully populated, no "failed to load"): `assets/2026-06-08-M1-note-editor-WORKING-frozen.png`.

---

## Bonus fix — book list rendered the code twice ("gen gen")
User noticed the editor's book column repeated the tag. `books.yaml` carries the human name under **`title`** ("The First Book of Moses, Genesis"), has **no `name` field**, and `api_books()` did `b.get("name", b["code"])` → fell back to the code → `name == code`. The row template shows `code | name | count` → "gen gen 4903". Fixed `scripts/web_notes.py` → `b.get("name") or b.get("title") or b["code"]` (+ a `title=` hover tooltip in `index.py`). Now: `gen | The First Book of Moses, Genesis | 4903` (0/87 repeating). Display-only; the shipped EPUB/reader already used `title` correctly.

## M1 (native-window dmg) — CLOSED
- TEST dmg wrapped from the **fixed** `.app` → `dist/YHWH-0.0.3-nativewin-TEST.dmg` (313M, unsigned, do-not-upload; the M3 release dmg reuses this verified recipe). Named off `0.0.3` so `build_dmg.sh`'s `rm -f dist/YHWH-${VERSION}.dmg` can't clobber the notarized one.
- The notarized `dist/YHWH-0.0.3.dmg` was moved to safety across the `rm -rf dist/` rebuild and **restored — checksum `043e884e…` matches the original** (intact, 309M).
- Native Cocoa window proven END-TO-END from the mounted dmg: launched the `.app` off the read-only DMG → Quartz shows a window owned by **"YHWH Ya' Way"**, 1280×900, layer 0 (not a browser). Dock icon (`YHWH.icns`) confirmed up by the user.

## → Windows lane (handoff)
1. The fix is shared code (`web_helpers.py`) → reaches Windows on pull. **Please VERIFY on the Windows `.exe` AND Linux AppImage**: launch each, open the note editor, confirm the book list loads (no "failed to load"); and scan for any sibling request-time disk-path reads. (User-requested cross-platform check.)
2. Book-name + tooltip fix (`web_notes.py`/`index.py`) — FYI/review.
3. **Brainstorm desktop-app user-friendliness** (user-requested): the app opens to a dense note-editor IDE; the user finds it overwhelming as a first page. Relates to device-QA finding 6 (app top-nav). Consider a friendlier default landing + clarifying who the shipped app is for.
