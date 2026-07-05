# -*- coding: utf-8 -*-
"""Tests for adesha/lexer.py (A0.2)."""

import pytest

from adesha.lexer import LexError, Token, tokenize


def kinds(text):
    return [t.kind for t in tokenize(text)]


def values(text):
    return [t.value for t in tokenize(text)]


class TestNumbers:
    def test_int(self):
        (t,) = tokenize("108")
        assert t == Token("NUMBER", 108, 1, 1)
        assert isinstance(t.value, int)

    def test_float(self):
        (t,) = tokenize("3.14")
        assert t.kind == "NUMBER"
        assert t.value == pytest.approx(3.14)
        assert isinstance(t.value, float)

    def test_int_then_op_not_float(self):
        # "5." with no digit after the dot is not a float
        with pytest.raises(LexError):
            tokenize("5.")

    def test_adjacent_number_ident(self):
        assert kinds("2 n") == ["NUMBER", "IDENT"]


class TestStrings:
    def test_spaces_survive(self):
        (t,) = tokenize('"namaste loka"')
        assert t == Token("STRING", "namaste loka", 1, 1)

    def test_escaped_quote(self):
        (t,) = tokenize(r'"say \"om\""')
        assert t.value == 'say "om"'

    def test_escaped_backslash(self):
        (t,) = tokenize(r'"a\\b"')
        assert t.value == "a\\b"

    def test_escaped_newline(self):
        (t,) = tokenize(r'"line1\nline2"')
        assert t.value == "line1\nline2"

    def test_empty_string(self):
        (t,) = tokenize('""')
        assert t.value == ""

    def test_unterminated_eof(self):
        with pytest.raises(LexError) as e:
            tokenize('"never ends')
        assert e.value.line == 1
        assert e.value.col == 1

    def test_unterminated_at_newline(self):
        with pytest.raises(LexError):
            tokenize('"broken\nvada x')

    def test_unknown_escape(self):
        with pytest.raises(LexError):
            tokenize(r'"bad \q"')

    def test_devanagari_content(self):
        (t,) = tokenize('"नमस्ते लोक"')
        assert t.value == "नमस्ते लोक"


class TestIdents:
    def test_ascii(self):
        (t,) = tokenize("vada")
        assert t == Token("IDENT", "vada", 1, 1)

    def test_harvard_kyoto_capitals(self):
        assert values("sthApaya punaH zRNu gaNaya") == [
            "sthApaya", "punaH", "zRNu", "gaNaya"]

    def test_devanagari_with_virama_and_matras(self):
        # स्थापय contains virāma (Mn) and vowel signs — must stay one token
        (t,) = tokenize("स्थापय")
        assert t.kind == "IDENT"
        assert t.value == "स्थापय"

    def test_devanagari_keywords(self):
        assert values("वद गणय पुनः शृणु") == ["वद", "गणय", "पुनः", "शृणु"]

    def test_digits_after_first_char(self):
        (t,) = tokenize("n1")
        assert t == Token("IDENT", "n1", 1, 1)

    def test_underscore(self):
        assert values("_x a_b") == ["_x", "a_b"]

    def test_digit_does_not_start_ident(self):
        assert kinds("1x") == ["NUMBER", "IDENT"]


class TestOpsAndColon:
    def test_single_char_ops(self):
        assert values("+ - * / % < > ( )") == list("+-*/%<>()")
        assert all(k == "OP" for k in kinds("+ - * / % < > ( )"))

    def test_two_char_ops(self):
        assert values("// <= >= == !=") == ["//", "<=", ">=", "==", "!="]

    def test_floordiv_not_two_divs(self):
        assert values("a // b") == ["a", "//", "b"]

    def test_lone_bang_is_error(self):
        with pytest.raises(LexError):
            tokenize("!")

    def test_colon_kind(self):
        assert kinds("yadi n > 3 : vada") == [
            "IDENT", "IDENT", "OP", "NUMBER", "COLON", "IDENT"]

    def test_no_spaces_expression(self):
        assert values("(n+1)*2") == ["(", "n", "+", 1, ")", "*", 2]


class TestComments:
    def test_skipped_by_default(self):
        assert tokenize("# whole line") == []

    def test_trailing(self):
        assert values("vada om # says om") == ["vada", "om"]

    def test_kept_when_asked(self):
        toks = tokenize("vada # hi", keep_comments=True)
        assert toks[-1].kind == "COMMENT"
        assert toks[-1].value == "# hi"

    def test_hash_inside_string_is_not_comment(self):
        (t,) = tokenize('"#108"')
        assert t == Token("STRING", "#108", 1, 1)


class TestPositions:
    def test_columns_single_line(self):
        toks = tokenize('vada "om" 108')
        assert [(t.line, t.col) for t in toks] == [(1, 1), (1, 6), (1, 11)]

    def test_lines_multi(self):
        toks = tokenize("vada om\nsthApaya n 5\n\ngaNaya n")
        assert [(t.value, t.line) for t in toks] == [
            ("vada", 1), ("om", 1),
            ("sthApaya", 2), ("n", 2), (5, 2),
            ("gaNaya", 4), ("n", 4)]

    def test_starting_line_offset(self):
        (t,) = tokenize("vada", line=7)
        assert (t.line, t.col) == (7, 1)

    def test_error_position(self):
        with pytest.raises(LexError) as e:
            tokenize("vada om\n  @")
        assert (e.value.line, e.value.col) == (2, 3)


class TestAcceptance:
    def test_plan_acceptance_line(self):
        # A0.2 acceptance: vada "namaste loka" keeps the space
        toks = tokenize('vada "namaste loka"')
        assert toks == [
            Token("IDENT", "vada", 1, 1),
            Token("STRING", "namaste loka", 1, 6)]
