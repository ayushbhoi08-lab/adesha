# -*- coding: utf-8 -*-
"""
Expression parser (A0.1 + A2) — recursive descent over the A0.2 tokens.

Replaces the v0 restricted-builtins path with a real parser. Grammar:

    expr  := or
    or    := and ( "vA" and )*
    and   := not ( "ca" not )*
    not   := "na" not | cmp
    cmp   := sum ( ("<"|"<="|">"|">="|"=="|"!=") sum )?
    sum   := term ( ("+"|"-") term )*
    term  := unary ( ("*"|"/"|"//"|"%") unary )*
    unary := "-" unary | postfix
    postfix := atom ( "[" expr "]" )*
    atom  := NUMBER | NUMBER-WORD | BOOL | STRING | IDENT | IDENT "(" args ")" | "(" expr ")"
    args  := expr ( expr )*   # space-separated, zero or more

Logical operators are Sanskrit (LOCKED 2026-07-04): ca (and), vA (or),
na (not).  Boolean literals are Sanskrit (A2 LOCKED): satya/asatya.
Number-word literals are Sanskrit (A2 LOCKED): zUnya..nava, daza, zata,
aSTottarazata.  Each registered in the three spellings (Harvard-Kyoto
canonical | lowercase | Devanagari).

`ca`/`vA` short-circuit and return the deciding operand, Python-style;
`na` returns a bool.

Every failure — lexing, parsing, or computing — raises ExprError, which
carries line/col when known. Callers rely on that being catchable
(sthApaya falls back to storing raw text). Task 4 routes it into the
doSa table.
"""

import operator

from .lexer import LexError, tokenize


class ExprError(Exception):
    """Any expression problem. Task 4 routes this through the doSa table.

    kind: "lex" | "parse" | "runtime" — lets errors.py assign distinct doSa codes.
    code: optional explicit doSa code (e.g. 13 for index errors).
    """

    def __init__(self, message, line=None, col=None, kind="parse", code=None):
        super().__init__(message)
        self.line = line
        self.col = col
        self.kind = kind
        self.code = code


# Sanskrit logical operators — HK canonical | lowercase | Devanagari
_OR_WORDS = {"vA", "va", "वा"}
_AND_WORDS = {"ca", "च"}          # lowercase == canonical
_NOT_WORDS = {"na", "न"}          # lowercase == canonical
_RESERVED = _OR_WORDS | _AND_WORDS | _NOT_WORDS

# Sanskrit number-word literals (A2) — HK canonical | lowercase | Devanagari
_NUMBER_WORDS = {
    "zUnya": 0, "zunya": 0, "शून्य": 0,
    "eka": 1, "एक": 1,
    "dvi": 2, "द्वि": 2,
    "tri": 3, "त्रि": 3,
    "catur": 4, "चतुर्": 4,
    "paJca": 5, "panca": 5, "पञ्च": 5,
    "SaS": 6, "sash": 6, "षष्": 6,
    "sapta": 7, "सप्त": 7,
    "aSTa": 8, "asta": 8, "अष्ट": 8,
    "nava": 9, "नव": 9,
    "daza": 10, "दश": 10,
    "zata": 100, "शत": 100,
    "aSTottarazata": 108, "astottarazata": 108, "अष्टोत्तरशत": 108,
}

# Sanskrit boolean literals (A2) — HK canonical | lowercase | Devanagari
_BOOL_WORDS = {
    "satya": True, "सत्य": True,
    "asatya": False, "असत्य": False,
}

# Expression-level builtins — HK canonical | lowercase | Devanagari
_EXPR_BUILTINS = {"dIrghA", "dirghA", "दीर्घा"}

_CMP_OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt,
            ">=": operator.ge, "==": operator.eq, "!=": operator.ne}
_SUM_OPS = {"+": operator.add, "-": operator.sub}
_TERM_OPS = {"*": operator.mul, "/": operator.truediv,
             "//": operator.floordiv, "%": operator.mod}

# Hook for executing user-defined functions from expression calls.
# interp.py registers this so expr.py stays free of circular imports.
_FUNCTION_RUNNER = None


def set_function_runner(runner):
    """Register a callable(fn, args, env, line) -> value for user vidhi calls."""
    global _FUNCTION_RUNNER
    _FUNCTION_RUNNER = runner


# --- parser (tokens -> small tuple AST) --------------------------------------

class _Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def advance(self):
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def at_op(self, ops):
        t = self.peek()
        return t is not None and t.kind == "OP" and t.value in ops

    def at_word(self, words):
        t = self.peek()
        return t is not None and t.kind == "IDENT" and t.value in words

    def expr(self):
        return self.or_()

    def or_(self):
        node = self.and_()
        while self.at_word(_OR_WORDS):
            self.advance()
            node = ("or", node, self.and_())
        return node

    def and_(self):
        node = self.not_()
        while self.at_word(_AND_WORDS):
            self.advance()
            node = ("and", node, self.not_())
        return node

    def not_(self):
        if self.at_word(_NOT_WORDS):
            self.advance()
            return ("not", self.not_())
        return self.cmp()

    def cmp(self):
        node = self.sum()
        if self.at_op(_CMP_OPS):
            op = self.advance().value
            node = ("bin", op, node, self.sum())
        return node

    def sum(self):
        node = self.term()
        while self.at_op(_SUM_OPS):
            op = self.advance().value
            node = ("bin", op, node, self.term())
        return node

    def term(self):
        node = self.unary()
        while self.at_op(_TERM_OPS):
            op = self.advance().value
            node = ("bin", op, node, self.unary())
        return node

    def unary(self):
        if self.at_op(("-",)):
            self.advance()
            return ("neg", self.unary())
        return self.postfix()

    def postfix(self):
        node = self.atom()
        while self.at_op(("[",)):
            self.advance()                       # consume '['
            idx = self.expr()
            if not self.at_op(("]",)):
                bad = self.peek()
                raise ExprError("']' na labdham — missing ']'",
                                bad.line if bad else None,
                                bad.col if bad else None)
            self.advance()                       # consume ']'
            node = ("index", node, idx)
        return node

    def atom(self):
        t = self.peek()
        if t is None:
            raise ExprError("apUrNa gaNanA — expression ends too early")
        if t.kind == "NUMBER":
            self.advance()
            return ("const", t.value)
        if t.kind == "STRING":
            self.advance()
            return ("const", t.value)
        if t.kind == "IDENT":
            if t.value in _RESERVED:
                raise ExprError(f"asthAne '{t.value}' — operator out of place",
                                t.line, t.col)
            self.advance()
            # function call: any identifier may be followed by '('
            if self.at_op(("(",)):
                self.advance()                   # consume '('
                args = []
                if not self.at_op((")",)):
                    while True:
                        args.append(self.expr())
                        if self.at_op((")",)):
                            break
                if not self.at_op((")",)):
                    bad = self.peek()
                    raise ExprError("')' na labdham — missing ')'",
                                    bad.line if bad else t.line,
                                    bad.col if bad else t.col)
                self.advance()                   # consume ')'
                return ("call", t.value, args)
            # number-word or boolean literal
            if t.value in _NUMBER_WORDS:
                return ("const", _NUMBER_WORDS[t.value])
            if t.value in _BOOL_WORDS:
                return ("const", _BOOL_WORDS[t.value])
            return ("var", t.value)
        if t.kind == "OP" and t.value == "(":
            self.advance()
            node = self.expr()
            if not self.at_op((")",)):
                bad = self.peek()
                raise ExprError("')' na labdham — missing ')'",
                                bad.line if bad else t.line,
                                bad.col if bad else t.col)
            self.advance()
            return node
        raise ExprError(f"asambhava cinha {t.value!r} — unexpected token",
                        t.line, t.col)


def parse(text, line=1):
    """Parse expression text into an AST; raise ExprError on any problem."""
    try:
        tokens = tokenize(text, line=line)
    except LexError as e:
        raise ExprError(str(e), e.line, e.col, kind="lex") from e
    p = _Parser(tokens)
    if p.peek() is None:
        raise ExprError("riktA gaNanA — empty expression", line, 1)
    node = p.expr()
    left = p.peek()
    if left is not None:
        raise ExprError(
            f"adhika cinha {left.value!r} — extra token after expression",
            left.line, left.col)
    return node


# --- AST walker ---------------------------------------------------------------

def _builtin_len(args):
    if len(args) != 1:
        raise ExprError("dIrghA tarka ekaH — dIrghA needs one argument",
                        kind="runtime")
    value = args[0]
    if isinstance(value, (str, list)):
        return len(value)
    raise ExprError(f"dIrghA requires string or list, got {value!r}",
                    kind="runtime")


def _run_call(name, arg_values, env, line):
    """Execute a function call from inside an expression."""
    if name in _EXPR_BUILTINS:
        return _builtin_len(arg_values)
    if _FUNCTION_RUNNER is not None:
        return _FUNCTION_RUNNER(name, arg_values, env, line)
    raise ExprError(f"ajYAta vidhi '{name}' — unknown function",
                    line=line, kind="runtime")


def _run(node, env):
    kind = node[0]
    if kind == "const":
        return node[1]
    if kind == "var":
        name = node[1]
        if name in env:
            return env[name]
        raise ExprError(f"ajYAta nAma '{name}' — unknown name", kind="runtime")
    if kind == "call":
        name, arg_nodes = node[1], node[2]
        arg_values = [_run(a, env) for a in arg_nodes]
        return _run_call(name, arg_values, env, line=None)
    if kind == "index":
        container = _run(node[1], env)
        idx = _run(node[2], env)
        if isinstance(idx, bool) or not isinstance(idx, int):
            raise ExprError("anukramaH saMkhyA bhavituM arhati — index must be an integer",
                            kind="runtime", code=13)
        if idx <= 0:
            raise ExprError("anukramaH dhanAtmakaH bhavituM arhati — index must be positive",
                            kind="runtime", code=13)
        try:
            return container[idx - 1]
        except (IndexError, TypeError):
            raise ExprError("bahirgataH anukramaH — index out of range",
                            kind="runtime", code=13)
    if kind == "or":                      # short-circuit, returns the operand
        left = _run(node[1], env)
        return left if left else _run(node[2], env)
    if kind == "and":
        left = _run(node[1], env)
        return _run(node[2], env) if left else left
    if kind == "not":
        return not _run(node[1], env)
    if kind == "neg":
        value = _run(node[1], env)
        try:
            return -value
        except TypeError:
            raise ExprError(f"na RNIkartum zakyam — cannot negate {value!r}",
                            kind="runtime") from None
    # ("bin", op, left, right)
    op = node[1]
    left = _run(node[2], env)
    right = _run(node[3], env)
    fn = _CMP_OPS.get(op) or _SUM_OPS.get(op) or _TERM_OPS.get(op)
    try:
        return fn(left, right)
    except ZeroDivisionError:
        raise ExprError("zUnyena bhAgaH — division by zero", kind="runtime") from None
    except TypeError:
        raise ExprError(
            f"ayogya prakArau — '{op}' cannot join {left!r} and {right!r}",
            kind="runtime") from None


def compute(text, env, line=1):
    """Parse and compute an expression against env. All failures -> ExprError."""
    return _run(parse(text, line=line), env)
