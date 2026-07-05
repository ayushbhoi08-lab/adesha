# Ādeśa Web Playground

A zero-install, browser-based playground for the Ādeśa language. It runs the Python interpreter inside your browser using [Pyodide](https://pyodide.org/).

## Quick start

Build the playground from the current `adesha/` sources:

```bash
python ../scripts/build_playground.py
```

Then serve the folder over HTTP (Pyodide cannot load local files from `file://`):

```bash
cd playground
python -m http.server 8123
```

Open <http://localhost:8123/> in a modern browser.

## Features

- **CodeMirror 6** editor with keyword highlighting for Ādeśa commands.
- **Run** button executes the script against the Pyodide interpreter.
- **HK ⇄ Devanagari** toggle converts keywords between Harvard-Kyoto and Devanagari spellings.
- **Share** button copies a link with the script encoded in the URL fragment.
- **Lesson Zero** panel with starter snippets.

## Files

| File | Purpose |
|---|---|
| `index.html` | Shell UI |
| `style.css` | Dark theme styling |
| `main.js` | Pyodide bootstrap, editor, run loop, toggle, sharing |
| `examples.json` | Lesson Zero starter snippets |
| `keywords.json` | Generated keyword registry (run build script) |
| `py/` | Copied Python source files for Pyodide |

## Honesty notes

- This is an **alpha** teaching tool, not a full LMS.
- Voice recognition (Track D) is not available in the browser.
- Chip-true `sAkSya` notarization requires the desktop `AOS_GOLDEN` environment and is not available in the browser; `mudrA` fingerprinting works.
