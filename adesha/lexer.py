# -*- coding: utf-8 -*-
"""
Tokenizer (A0.2) — the lexical layer of Ādeśa.

Token kinds:
    NUMBER   ints and floats (123, 4.5)
    STRING   "…" with escapes \\" \\\\ \\n — spaces survive inside
    IDENT    Unicode letters (incl. Devanagari with vowel signs/virāma),
             then letters/digits/combining marks/underscore
    OP       + - * / // % < <= > >= == != ( ) [ ]
    COLON    :
    COMMENT  # to end of line (skipped unless keep_comments=True)

Every token carries a 1-based line and column — this feeds the doSa
error system (A0.3).
"""

import unicodedata
from typing import NamedTuple


class Token(NamedTuple):
    kind: str      # NUMBER | STRING | IDENT | OP | COLON | COMMENT
    value: object  # int/float for NUMBER, decoded str for STRING, else source text
    line: int      # 1-based
    col: int       # 1-based


class LexError(Exception):
    """Bad input at a known position. Task 4 routes this through the doSa table."""

    def __init__(self, message, line, col):
        super().__init__(message)
        self.line = line
        self.col = col


# two-char operators must be matched before their one-char prefixes
_OPS2 = ("//", "<=", ">=", "==", "!=")
_OPS1 = ("+", "-", "*", "/", "%", "<", ">", "(", ")", "[", "]")

_STRING_ESCAPES = {'"': '"', "\\": "\\", "n": "\n"}


def _is_ident_start(ch):
    return ch == "_" or ch.isalpha()


def _is_ident_part(ch):
    # isalnum covers letters and digits; Mn/Mc admits Devanagari vowel
    # signs and virāma (e.g. the ् in स्थापय), which are not letters
    return ch == "_" or ch.isalnum() or unicodedata.category(ch) in ("Mn", "Mc")


def tokenize(text, line=1, keep_comments=False):
    """Tokenize source text (any number of lines) into a list of Tokens.

    `line` sets the starting line number, so a caller feeding single
    lines from a script can report true positions later.
    """
    tokens = []
    i, n, col = 0, len(text), 1

    while i < n:
        ch = text[i]

        if ch == "\n":
            line += 1
            col = 1
            i += 1
            continue

        if ch in " \t\r":
            i += 1
            col += 1
            continue

        if ch == "#":                                   # comment to EOL
            start_i, start_col = i, col
            while i < n and text[i] != "\n":
                i += 1
            if keep_comments:
                tokens.append(Token("COMMENT", text[start_i:i], line, start_col))
            col += i - start_i
            continue

        if ch == '"':                                   # string literal
            start_line, start_col = line, col
            i += 1
            col += 1
            out = []
            while True:
                if i >= n or text[i] == "\n":
                    raise LexError("unterminated string", start_line, start_col)
                c = text[i]
                if c == "\\":
                    if i + 1 >= n:
                        raise LexError("unterminated string", start_line, start_col)
                    esc = text[i + 1]
                    if esc not in _STRING_ESCAPES:
                        raise LexError(f"unknown escape \\{esc}", line, col)
                    out.append(_STRING_ESCAPES[esc])
                    i += 2
                    col += 2
                    continue
                if c == '"':
                    i += 1
                    col += 1
                    break
                out.append(c)
                i += 1
                col += 1
            tokens.append(Token("STRING", "".join(out), start_line, start_col))
            continue

        if ch.isdigit():                                # number: int or float
            start_i, start_col = i, col
            while i < n and text[i].isdigit():
                i += 1
            if i + 1 < n and text[i] == "." and text[i + 1].isdigit():
                i += 1
                while i < n and text[i].isdigit():
                    i += 1
                value = float(text[start_i:i])
            else:
                value = int(text[start_i:i])
            col += i - start_i
            tokens.append(Token("NUMBER", value, line, start_col))
            continue

        if _is_ident_start(ch):                         # identifier / keyword
            start_i, start_col = i, col
            i += 1
            while i < n and _is_ident_part(text[i]):
                i += 1
            col += i - start_i
            tokens.append(Token("IDENT", text[start_i:i], line, start_col))
            continue

        if ch == ":":
            tokens.append(Token("COLON", ":", line, col))
            i += 1
            col += 1
            continue

        two = text[i:i + 2]
        if two in _OPS2:
            tokens.append(Token("OP", two, line, col))
            i += 2
            col += 2
            continue
        if ch in _OPS1:
            tokens.append(Token("OP", ch, line, col))
            i += 1
            col += 1
            continue

        raise LexError(f"unexpected character {ch!r}", line, col)

    return tokens
