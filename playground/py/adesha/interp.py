#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ādeśa (आदेश, "command") — the HIGH-LEVEL layer of the Ādeśa stack.

A small interpreted language whose keywords are Sanskrit imperatives
(loṭ lakāra), written in the HARVARD-KYOTO convention — a pure-ASCII,
reversible romanization of Devanagari, so every keyword types on any
English keyboard (retroflex/long sounds use capitals: A N T S R H).

A2 feature set: variables, arithmetic + comparison expressions, conditionals
(yadi), repetition (punaH), input (zRNu), blocks (iti), else (anyathA),
while (yAvat), functions (vidhi/dehi), lists (samUha/yojaya/indexing),
Sanskrit number-words, Sanskrit booleans, and a --trace teaching mode.
It can drop DOWN to the chip layer with `mudrA` and `sAkSya`.

    python adesha.py               # interactive shell (REPL)
    python adesha.py file.adesha   # run a script

Each keyword is registered as:  Harvard-Kyoto (canonical) | lowercase | Devanagari.
"""

import argparse
import os
import re
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

# make Devanagari input/output safe on Windows consoles
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
except Exception:
    pass

# so `import aos_asm` (repo root, one level above this package) works
# no matter where we're run from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .errors import DosA, raise_dosa, suggest
from .expr import ExprError, compute, set_function_runner
from .lexer import LexError, tokenize

COMMANDS = {}
BLOCK_COMMANDS = {}

# Injectable I/O — default to builtins; swap via io_context in tests.
_io = {"print": print, "input": input}

# Trace mode: when True, every executed statement is printed with its line number.
_TRACE = False


@contextmanager
def io_context(input_fn=None, output_fn=None):
    """Temporarily replace _io sinks; restores originals on exit."""
    old = dict(_io)
    if input_fn is not None:
        _io["input"] = input_fn
    if output_fn is not None:
        _io["print"] = output_fn
    try:
        yield
    finally:
        _io.update(old)


def command(*names):
    """Register a function under one or more spellings (Harvard-Kyoto + aliases)."""
    def wrap(fn):
        for n in names:
            COMMANDS[n] = fn
        return fn
    return wrap


def block_command(*names):
    """Register a block-handler function under one or more spellings."""
    def wrap(fn):
        for n in names:
            BLOCK_COMMANDS[n] = fn
        return fn
    return wrap


def _format_value(value):
    """Format a Python value for user-facing output.

    Booleans become Sanskrit satya/asatya. Lists are formatted like Python
    lists but with boolean elements translated. Everything else uses str().
    """
    if isinstance(value, bool):
        return "satya" if value else "asatya"
    if isinstance(value, list):
        return "[" + ", ".join(_format_value(v) for v in value) + "]"
    return str(value)


def resolve(token, env):
    """A token as a formatted value. Tries to evaluate it as an expression first
    (so L[1], f(), and number-words work in vada). A single bare token that
    cannot be evaluated falls back to the literal source text; anything with
    operators/brackets is a real expression error and is re-raised."""
    try:
        return _format_value(compute(token, env))
    except ExprError:
        # literal bare word: single token that does not form a valid expression
        # (e.g. "na", "namaste", an unknown identifier).
        try:
            toks = tokenize(token)
        except LexError:
            toks = []
        if len(toks) == 1:
            return token
        raise


# ---------------------------------------------------------------------------
# Statement model
# ---------------------------------------------------------------------------

@dataclass
class Line:
    text: str
    lineno: int


@dataclass
class Block:
    keyword: str      # yadi, yAvat, punaH, vidhi
    args: list        # tokens after the keyword on the opening line
    body: list        # list of Statement
    else_body: list   # for yadi only
    lineno: int


@dataclass
class Function:
    name: str
    params: list
    body: list        # list of Statement


# ---------------------------------------------------------------------------
# Block parsing
# ---------------------------------------------------------------------------

_YADI = {"yadi", "यदि"}
_PUNAH = {"punaH", "punah", "पुनः"}
_YAVAT = {"yAvat", "यावत्"}
_VIDHI = {"vidhi", "विधि"}
_ITI = {"iti", "इति"}
_ANYATHA = {"anyathA", "anyatha", "अन्यथा"}
_BLOCK_OPENERS = _YADI | _PUNAH | _YAVAT | _VIDHI


def _strip_comment(text):
    """Remove a '#'-comment; used by the block parser only."""
    i = text.find("#")
    if i == -1:
        return text
    return text[:i]


def _is_inline_block(word, parts):
    """Decide whether a block opener is in inline (A0) form."""
    if word in _YADI:
        return ":" in parts
    if word in _PUNAH:
        return len(parts) > 2
    return False


def parse_statements(lines, start=0, parent_lineno=None):
    """Parse a sequence of (lineno, text) lines into Statements.

    Returns (statements, next_index, terminator) where terminator is one of
    "iti", "anyathA", or "eof".
    """
    stmts = []
    i = start
    while i < len(lines):
        lineno, raw = lines[i]
        text = _strip_comment(raw).strip()
        if not text:
            i += 1
            continue

        parts = text.split()
        word = parts[0]

        if word in _ITI:
            if parent_lineno is None:
                raise_dosa(8, line=lineno, msg="unmatched iti")
            return stmts, i + 1, "iti"

        if word in _ANYATHA:
            if parent_lineno is None:
                raise_dosa(10, line=lineno)
            return stmts, i + 1, "anyathA"

        if word in _BLOCK_OPENERS:
            if _is_inline_block(word, parts):
                stmts.append(Line(raw, lineno))
                i += 1
            else:
                args = parts[1:]
                body, next_i, term = parse_statements(lines, i + 1, lineno)
                else_body = []
                if term == "anyathA":
                    else_body, next_i, term = parse_statements(lines, next_i, lineno)
                if term != "iti":
                    raise_dosa(9, line=lineno, word=word)
                stmts.append(Block(word, args, body, else_body, lineno))
                i = next_i
        else:
            stmts.append(Line(raw, lineno))
            i += 1

    if parent_lineno is not None:
        opener = lines[parent_lineno - 1][1].strip().split()[0] if parent_lineno - 1 < len(lines) else "?"
        raise_dosa(9, line=parent_lineno, word=opener)
    return stmts, i, "eof"


# --- commands  (Harvard-Kyoto canonical | lowercase alias | Devanagari) -----

@command("sthApaya", "sthapaya", "स्थापय")      # "establish!" -> set a variable
def _set(args, env):
    name, raw = args[0], " ".join(args[1:])
    try:
        env[name] = compute(raw, env)    # numbers / expressions
    except ExprError:
        env[name] = raw                  # fall back to a plain string


@command("vada", "वद")                           # "speak!" -> print
def _print(args, env):
    _io["print"](" ".join(resolve(a, env) for a in args))


@command("gaNaya", "ganaya", "गणय")             # "compute!" -> compute + print
def _calc(args, env):
    _io["print"](_format_value(compute(" ".join(args), env)))


@command("yadi", "यदि")                          # inline if -> yadi <expr> : <command>
def _if_inline(args, env):
    if ":" not in args:
        raise_dosa(5)
    i = args.index(":")
    if compute(" ".join(args[:i]), env):
        run_line(" ".join(args[i + 1:]), env)


@block_command("yadi", "यदि")                    # block if
def _if_block(stmt, env):
    expr = " ".join(stmt.args)
    if compute(expr, env):
        execute_statements(stmt.body, env)
    else:
        execute_statements(stmt.else_body, env)


@command("punaH", "punah", "पुनः")              # inline repeat -> punaH N <command>
def _repeat_inline(args, env):
    raw = args[0]
    if raw.lstrip("-").isdigit():
        n = int(raw)
    else:
        try:
            n = int(compute(raw, env))
        except (ExprError, TypeError, ValueError):
            raise_dosa(7, word=raw)
    rest = " ".join(args[1:])
    for _ in range(n):
        run_line(rest, env)


@block_command("punaH", "punah", "पुनः")        # block repeat
def _repeat_block(stmt, env):
    raw = stmt.args[0] if stmt.args else ""
    if raw.lstrip("-").isdigit():
        n = int(raw)
    else:
        try:
            n = int(compute(raw, env))
        except (ExprError, TypeError, ValueError):
            raise_dosa(7, word=raw)
    for _ in range(n):
        execute_statements(stmt.body, env)


@block_command("yAvat", "यावत्")                 # "as long as" -> while loop
def _while(stmt, env):
    expr = " ".join(stmt.args)
    while compute(expr, env):
        execute_statements(stmt.body, env)


@command("zRNu", "srnu", "शृणु")                # "listen!" -> read input into a var
def _read(args, env):
    env[args[0]] = _io["input"]("… ")


@command("tiSTha", "tishtha", "तिष्ठ")          # "stand still!" -> wait N seconds
def _wait(args, env):
    time.sleep(float(resolve(args[0], env)) if args else 0)


@command("mudrA", "mudra", "मुद्रा")            # "seal!" -> software fingerprint
def _seal(args, env):
    import aos_asm
    token = args[0]
    value = env.get(token, token)                # variable value, or the word itself
    _io["print"](f"mudrA {token}: {aos_asm.fingerprint(value)}")


@command("sAkSya", "sakshya", "साक्ष्य")        # "witness!" -> A-TS notarize
def _witness(args, env):
    import aos_asm
    token = args[0]
    value = env.get(token, token)                # variable value, or the word itself
    try:
        chain_hex = aos_asm.sakshya_notarize(value)
    except RuntimeError as exc:
        raise_dosa(4, msg=str(exc))
    ts = datetime.now(timezone.utc).isoformat()
    _io["print"](f"sAkSya {token}: {ts} {chain_hex}")


@command("samUha", "samUha", "समूह")            # "collection!" -> create list
def _list_create(args, env):
    if not args:
        raise_dosa(6, cmd="samUha")
    name = args[0]
    values = []
    for token in args[1:]:
        try:
            values.append(compute(token, env))
        except ExprError:
            values.append(token)
    env[name] = values


@command("yojaya", "yojaya", "योजय")            # "join!" -> append to list
def _list_append(args, env):
    if len(args) < 2:
        raise_dosa(6, cmd="yojaya")
    name, token = args[0], args[1]
    lst = env.get(name)
    if not isinstance(lst, list):
        raise_dosa(12, msg=f"{name} is not a list")
    try:
        value = compute(token, env)
    except ExprError:
        value = token
    lst.append(value)


@command("iti", "इति")                           # block terminator (should be parsed away)
def _iti(args, env):
    raise_dosa(8, msg="unmatched iti")


@command("anyathA", "anyatha", "अन्यथा")        # else marker (should be parsed away)
def _anyatha(args, env):
    raise_dosa(10)


@block_command("vidhi", "विधि")                  # "rule/procedure!" -> define function
def _define_function(stmt, env):
    if not stmt.args:
        raise_dosa(6, line=stmt.lineno, cmd="vidhi")
    name = stmt.args[0]
    params = stmt.args[1:]
    env[name] = Function(name, params, stmt.body)


class DehiReturn(Exception):
    """Control-flow exception carrying a vidhi's return value."""

    def __init__(self, value):
        self.value = value


@command("dehi", "dehi", "देहि")                  # "give!" -> return from vidhi
def _return(args, env):
    value = compute(" ".join(args), env) if args else None
    raise DehiReturn(value)


@command("samApti", "samapti", "समाप्ति")       # "the end" -> quit
def _quit(args, env):
    raise SystemExit


# --- value helpers ----------------------------------------------------------

def _resolve_value(token, env):
    """A token as a computed value, or itself if not a valid expression."""
    try:
        return compute(token, env)
    except ExprError:
        return token


def _execute_function_body(fn, local_env, lineno=None):
    """Run a function body and return its `dehi` value, or None."""
    try:
        execute_statements(fn.body, local_env)
    except DehiReturn as ret:
        return ret.value
    return None


def _call_function(fn, args, env, lineno=None):
    """Statement-style call: args are raw string tokens."""
    if len(args) != len(fn.params):
        raise_dosa(11, line=lineno,
                   msg=f"{fn.name} expects {len(fn.params)} arguments, got {len(args)}")
    local_env = dict(env)
    for param, arg in zip(fn.params, args):
        local_env[param] = _resolve_value(arg, env)
    return _execute_function_body(fn, local_env, lineno)


def _call_function_values(fn, arg_values, env, lineno=None):
    """Expression-style call: args are already evaluated Python values."""
    if len(arg_values) != len(fn.params):
        raise ExprError(
            f"{fn.name} expects {len(fn.params)} arguments, got {len(arg_values)}",
            line=lineno, kind="runtime")
    local_env = dict(env)
    for param, value in zip(fn.params, arg_values):
        local_env[param] = value
    return _execute_function_body(fn, local_env, lineno)


def _expr_function_runner(name, arg_values, env, line):
    """Callback registered with expr.py so vidhi calls work inside expressions."""
    fn = env.get(name)
    if not isinstance(fn, Function):
        raise ExprError(f"ajYAta vidhi '{name}' — unknown function",
                        line=line, kind="runtime")
    return _call_function_values(fn, arg_values, env, lineno=line)


set_function_runner(_expr_function_runner)


# --- interpreter ------------------------------------------------------------

def run_line(line, env, lineno=None):
    line = line.strip()
    if not line or line.startswith("#"):
        return
    parts = line.split()
    word, args = parts[0], parts[1:]

    fn = COMMANDS.get(word)
    if fn is None:
        fn_obj = env.get(word)
        if isinstance(fn_obj, Function):
            _call_function(fn_obj, args, env, lineno)
            return
        hint = suggest(word, list(COMMANDS))
        raise_dosa(1, line=lineno, word=word, hint=hint)

    try:
        fn(args, env)
    except DosA:
        raise
    except SystemExit:
        raise
    except DehiReturn:
        raise
    except ExprError as e:
        code = e.code or {"lex": 2, "parse": 3, "runtime": 4}.get(e.kind, 3)
        raise_dosa(code, line=lineno or e.line, msg=str(e))
    except IndexError:
        raise_dosa(6, line=lineno, cmd=word)
    except Exception as e:
        raise_dosa(99, line=lineno, msg=repr(e))


def execute_statement(stmt, env):
    if _TRACE:
        if isinstance(stmt, Line):
            _io["print"](f"{stmt.lineno}: {stmt.text.strip()}")
        elif isinstance(stmt, Block):
            _io["print"](f"{stmt.lineno}: {stmt.keyword} {' '.join(stmt.args)}")

    if isinstance(stmt, Line):
        run_line(stmt.text, env, stmt.lineno)
    elif isinstance(stmt, Block):
        fn = BLOCK_COMMANDS.get(stmt.keyword)
        if fn is None:
            raise_dosa(1, line=stmt.lineno, word=stmt.keyword)
        try:
            fn(stmt, env)
        except DosA:
            raise
        except SystemExit:
            raise
        except DehiReturn:
            raise
        except ExprError as e:
            code = e.code or {"lex": 2, "parse": 3, "runtime": 4}.get(e.kind, 3)
            raise_dosa(code, line=stmt.lineno or e.line, msg=str(e))
        except IndexError:
            raise_dosa(6, line=stmt.lineno, cmd=stmt.keyword)
        except Exception as e:
            raise_dosa(99, line=stmt.lineno, msg=repr(e))


def execute_statements(stmts, env):
    for stmt in stmts:
        execute_statement(stmt, env)


def _print_dosa(err):
    """Print a DosA without a traceback."""
    _io["print"](str(err))


def _update_block_depth(line, depth):
    """Adjust block depth for one REPL line based on openers/closers."""
    stripped = _strip_comment(line).strip()
    if not stripped:
        return depth
    parts = stripped.split()
    word = parts[0]
    if word in _BLOCK_OPENERS and not _is_inline_block(word, parts):
        return depth + 1
    if word in _ITI:
        return max(0, depth - 1)
    return depth


def repl(input_fn=None, output_fn=None, trace=False):
    """Interactive shell. input_fn/output_fn are injectable for Pyodide."""
    global _TRACE
    _TRACE = trace
    _in = input_fn or input
    _out = output_fn or print
    old_print = _io["print"]
    _io["print"] = _out
    env = {}
    _out("Ādeśa shell (Harvard-Kyoto) — type 'samApti' to quit.")
    try:
        buffer = []
        depth = 0
        while True:
            try:
                prompt = "... " if depth > 0 else ">> "
                line = _in(prompt)
            except (EOFError, KeyboardInterrupt):
                _out("")
                break
            buffer.append(line)
            depth = _update_block_depth(line, depth)
            if depth == 0 and buffer:
                text = "\n".join(buffer)
                buffer = []
                try:
                    lines = [(i + 1, l) for i, l in enumerate(text.splitlines())]
                    stmts, _, term = parse_statements(lines, 0)
                    execute_statements(stmts, env)
                except DosA as e:
                    _print_dosa(e)
                except DehiReturn:
                    raise_dosa(11, msg="dehi outside vidhi")
                except SystemExit:
                    break
    finally:
        _io["print"] = old_print


_SEAL_RE = re.compile(r'^# mudrA: [0-9a-f]{27}$')
_SUBCOMMANDS = {"run", "repl", "seal", "parIkSA"}


def _normalize(text):
    """Return file content with trailing blank lines and any seal footer removed."""
    lines = text.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and _SEAL_RE.match(lines[-1].strip()):
        lines.pop()
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def run_script(filepath, trace=False):
    global _TRACE
    _TRACE = trace
    env = {}
    with open(filepath, encoding="utf-8") as f:
        lines = [(i + 1, line.rstrip("\n")) for i, line in enumerate(f)]
    try:
        stmts, _, term = parse_statements(lines, 0)
        if term != "eof":
            raise_dosa(8, line=lines[-1][0], msg="unmatched iti")
        execute_statements(stmts, env)
    except DosA as e:
        _print_dosa(e)
        sys.exit(1)
    except DehiReturn:
        raise_dosa(11, msg="dehi outside vidhi")
    except SystemExit:
        pass


def cmd_seal(filepath):
    import aos_asm
    with open(filepath, encoding="utf-8") as f:
        text = f.read()
    normalized = _normalize(text)
    fp = aos_asm.fingerprint(normalized)
    sealed = normalized + f"\n# mudrA: {fp}\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(sealed)
    print(f"# mudrA: {fp}")


def cmd_pariksa(filepath):
    import aos_asm
    with open(filepath, encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    seal_line = lines[-1].strip() if lines else ""
    if not _SEAL_RE.match(seal_line):
        print("bhraSTa — no seal footer found")
        sys.exit(1)
    stored_fp = seal_line.split(": ", 1)[1]
    normalized = _normalize(text)
    actual_fp = aos_asm.fingerprint(normalized)
    if actual_fp == stored_fp:
        print("siddha")
        sys.exit(0)
    else:
        print("bhraSTa")
        sys.exit(1)


def main():
    # Back-compat: bare invocation → REPL; first arg not a subcommand → run script.
    if len(sys.argv) == 1:
        repl()
        return
    if sys.argv[1] not in _SUBCOMMANDS:
        run_script(sys.argv[1])
        return

    parser = argparse.ArgumentParser(prog="adesha", description="Ādeśa interpreter")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run a script")
    p_run.add_argument("file")
    p_run.add_argument("--trace", action="store_true",
                       help="print each line as it is executed")

    p_repl = sub.add_parser("repl", help="interactive shell (default)")
    p_repl.add_argument("--trace", action="store_true",
                        help="print each line as it is executed")

    p_seal = sub.add_parser("seal", help="fingerprint-seal a script")
    p_seal.add_argument("file")

    p_pk = sub.add_parser("parIkSA", help="verify a sealed script (siddha/bhraSTa)")
    p_pk.add_argument("file")

    args = parser.parse_args()

    if args.cmd == "run":
        run_script(args.file, trace=args.trace)
    elif args.cmd == "repl":
        repl(trace=args.trace)
    elif args.cmd == "seal":
        cmd_seal(args.file)
    elif args.cmd == "parIkSA":
        cmd_pariksa(args.file)


if __name__ == "__main__":
    main()
