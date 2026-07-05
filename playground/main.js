// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const PY_FILES = [
  'py/aos_asm.py',
  'py/adesha/__init__.py',
  'py/adesha/lexer.py',
  'py/adesha/expr.py',
  'py/adesha/interp.py',
  'py/adesha/errors.py',
];

const DEFAULT_SCRIPT = `sthApaya nama world
vada namaste nama`;

const STATUS = {
  el: document.getElementById('status-text'),
  dot: document.getElementById('status-dot'),
  set(text, cls) {
    this.el.textContent = text;
    this.dot.className = cls || 'busy';
  },
};

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------
function toast(message) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2000);
}

function appendOutput(html, cls) {
  const out = document.getElementById('output');
  const line = document.createElement('span');
  line.className = `line ${cls || 'out'}`;
  line.innerHTML = html;
  out.appendChild(line);
  out.scrollTop = out.scrollHeight;
}

function clearOutput() {
  document.getElementById('output').innerHTML = '';
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ---------------------------------------------------------------------------
// Keyword maps for toggle
// ---------------------------------------------------------------------------
let keywords = {};
let toDevanagari = {};
let toHarvardKyoto = {};
let scriptIsDevanagari = false;

function buildKeywordMaps(data) {
  keywords = data;
  toDevanagari = {};
  toHarvardKyoto = {};
  for (const [canonical, aliases] of Object.entries(data)) {
    const dev = aliases.find(a => /[\u0900-\u097f]/.test(a));
    if (!dev) continue;
    for (const alias of aliases) {
      if (alias !== dev) toDevanagari[alias] = dev;
    }
    toHarvardKyoto[dev] = canonical;
  }
}

function replaceKeywords(source, map) {
  const keySet = new Set(Object.keys(map));
  let out = '';
  let i = 0;
  while (i < source.length) {
    const ch = source[i];
    if (ch === '#') {
      const end = source.indexOf('\n', i);
      out += end === -1 ? source.slice(i) : source.slice(i, end);
      i = end === -1 ? source.length : end;
      continue;
    }
    if (ch === '"') {
      let j = i + 1;
      while (j < source.length && source[j] !== '"') j++;
      out += source.slice(i, j + 1);
      i = j + 1;
      continue;
    }
    if (/[a-zA-Z_\u0900-\u097f]/.test(ch)) {
      let j = i;
      while (j < source.length && /[a-zA-Z0-9_\u0900-\u097f]/.test(source[j])) j++;
      const word = source.slice(i, j);
      out += keySet.has(word) ? map[word] : word;
      i = j;
      continue;
    }
    out += ch;
    i++;
  }
  return out;
}

// ---------------------------------------------------------------------------
// URL sharing
// ---------------------------------------------------------------------------
function encodeSource(source) {
  return btoa(unescape(encodeURIComponent(source)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function decodeSource(hash) {
  try {
    const b64 = hash.slice(1).replace(/-/g, '+').replace(/_/g, '/');
    const padded = b64 + '='.repeat((4 - (b64.length % 4)) % 4);
    return decodeURIComponent(escape(atob(padded)));
  } catch {
    return null;
  }
}

function updateUrl(source) {
  const hash = '#' + encodeSource(source);
  if (window.location.hash !== hash) {
    history.replaceState(null, '', hash);
  }
}

function loadFromUrl() {
  if (window.location.hash) {
    const src = decodeSource(window.location.hash);
    if (src !== null) return src;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Editor (plain textarea)
// ---------------------------------------------------------------------------
let editor = null;

function setEditorValue(text) {
  editor.value = text;
  updateLineCol();
}

function getEditorValue() {
  return editor.value;
}

function updateLineCol() {
  const pos = editor.selectionStart;
  const text = editor.value.substring(0, pos);
  const lines = text.split('\n');
  const line = lines.length;
  const col = lines[lines.length - 1].length + 1;
  document.getElementById('line-col').textContent = `Ln ${line}, Col ${col}`;
}

// ---------------------------------------------------------------------------
// Pyodide + interpreter setup
// ---------------------------------------------------------------------------
let pyodide = null;

function setLoadingDetails(msg) {
  const el = document.getElementById('loading-details');
  el.textContent = msg;
  el.classList.add('show');
}

async function initPyodide() {
  if (typeof loadPyodide !== 'function') {
    throw new Error('Pyodide script did not load. Check your internet connection and whether cdn.jsdelivr.net is blocked.');
  }
  STATUS.set('loading Pyodide…', 'busy');
  pyodide = await loadPyodide();

  STATUS.set('copying source files…', 'busy');
  pyodide.FS.mkdir('/py');
  pyodide.FS.mkdir('/py/adesha');
  for (const path of PY_FILES) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`failed to fetch ${path}`);
    const content = await response.text();
    pyodide.FS.writeFile('/' + path, content);
  }

  STATUS.set('importing interpreter…', 'busy');
  await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, '/py')
from adesha.interp import parse_statements, execute_statements, io_context
from adesha.errors import DosA
from js import prompt as js_prompt

def run_adesha(source):
    output_lines = []
    def output_fn(*args):
        output_lines.append(" ".join(str(a) for a in args))
    def input_fn(prompt=""):
        try:
            return js_prompt(prompt) or ""
        except Exception:
            return ""
    lines = [(i + 1, line) for i, line in enumerate(source.splitlines())]
    stmts, idx, term = parse_statements(lines, 0)
    with io_context(input_fn=input_fn, output_fn=output_fn):
        execute_statements(stmts, {})
    return {"ok": True, "output": output_lines}

def run_adesha_safe(source):
    try:
        return run_adesha(source)
    except DosA as e:
        return {"ok": False, "error": str(e), "output": []}
    except Exception as e:
        return {"ok": False, "error": f"AntarikA-doSa: {e}", "output": []}
`);
}

async function runScript() {
  if (!pyodide) return;
  const source = getEditorValue();
  updateUrl(source);
  clearOutput();
  STATUS.set('running…', 'busy');
  document.getElementById('btn-run').disabled = true;

  try {
    const run = pyodide.globals.get('run_adesha_safe');
    const result = run(source);
    const output = result.get('output').toJs();
    const ok = result.get('ok');
    const error = result.get('error');

    for (const line of output) {
      appendOutput(escapeHtml(String(line)), 'out');
    }
    if (!ok) {
      appendOutput(escapeHtml(String(error)), 'err');
      STATUS.set('error', 'error');
    } else {
      STATUS.set('finished', 'ready');
    }
  } catch (e) {
    appendOutput(escapeHtml(String(e)), 'err');
    STATUS.set('error', 'error');
  } finally {
    document.getElementById('btn-run').disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Lesson panel
// ---------------------------------------------------------------------------
async function loadExamples() {
  const response = await fetch('examples.json');
  if (!response.ok) return;
  const data = await response.json();
  const list = document.getElementById('lesson-list');
  list.innerHTML = '';
  data.snippets.forEach((snippet) => {
    const li = document.createElement('li');
    li.textContent = snippet.name;
    li.addEventListener('click', () => {
      setEditorValue(snippet.source);
      document.getElementById('script-name').textContent = snippet.name;
      document.querySelectorAll('#lesson-list li').forEach(el => el.classList.remove('active'));
      li.classList.add('active');
      clearOutput();
      updateUrl(snippet.source);
    });
    list.appendChild(li);
  });
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const loadStart = Date.now();
  const timer = setInterval(() => {
    const elapsed = Math.round((Date.now() - loadStart) / 1000);
    document.getElementById('loading-sub').textContent =
      `Elapsed: ${elapsed}s · downloading Pyodide WASM (~30 MB)…`;
  }, 1000);

  editor = document.getElementById('editor');
  editor.addEventListener('input', updateLineCol);
  editor.addEventListener('click', updateLineCol);
  editor.addEventListener('keyup', updateLineCol);

  const kwResponse = await fetch('keywords.json');
  if (!kwResponse.ok) throw new Error('failed to fetch keywords.json');
  buildKeywordMaps(await kwResponse.json());

  const initialSource = loadFromUrl() || DEFAULT_SCRIPT;
  scriptIsDevanagari = Object.values(keywords).some(aliases =>
    aliases.some(a => /[\u0900-\u097f]/.test(a) && initialSource.includes(a))
  );
  setEditorValue(initialSource);

  document.getElementById('btn-run').addEventListener('click', runScript);
  document.getElementById('btn-clear').addEventListener('click', () => {
    clearOutput();
    setEditorValue(DEFAULT_SCRIPT);
    document.getElementById('script-name').textContent = 'untitled';
    updateUrl(DEFAULT_SCRIPT);
  });
  document.getElementById('btn-share').addEventListener('click', () => {
    const source = getEditorValue();
    updateUrl(source);
    navigator.clipboard.writeText(window.location.href).then(
      () => toast('Share link copied to clipboard'),
      () => toast('Could not copy link'),
    );
  });
  document.getElementById('btn-toggle').addEventListener('click', () => {
    const source = getEditorValue();
    const map = scriptIsDevanagari ? toHarvardKyoto : toDevanagari;
    const next = replaceKeywords(source, map);
    scriptIsDevanagari = !scriptIsDevanagari;
    setEditorValue(next);
    document.getElementById('btn-toggle').textContent = scriptIsDevanagari
      ? 'Harvard-Kyoto'
      : 'Devanagari';
    updateUrl(next);
  });

  document.getElementById('btn-toggle').textContent = scriptIsDevanagari
    ? 'Harvard-Kyoto'
    : 'Devanagari';

  await loadExamples();
  updateUrl(initialSource);

  try {
    await initPyodide();
    clearInterval(timer);
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('btn-run').disabled = false;
    document.getElementById('btn-toggle').disabled = false;
    document.getElementById('btn-share').disabled = false;
    document.getElementById('btn-clear').disabled = false;
    STATUS.set('ready', 'ready');
  } catch (e) {
    clearInterval(timer);
    document.getElementById('loading-text').textContent = 'Failed to load playground';
    document.getElementById('loading-sub').textContent = 'See details below.';
    setLoadingDetails(`${e.name || 'Error'}: ${e.message || e}\n\nIf Pyodide is blocked, try a different network or check the browser console (F12 → Console).`);
    STATUS.set('load failed', 'error');
    throw e;
  }
}

main().catch(console.error);
