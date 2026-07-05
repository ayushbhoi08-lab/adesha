# -*- coding: utf-8 -*-
"""Tests for adesha/expr.py (A0.1)."""

import pytest

from adesha.expr import ExprError, compute


def c(text, **env):
    return compute(text, env)


class TestArithmetic:
    def test_int_literal(self):
        assert c("108") == 108

    def test_float_literal(self):
        assert c("3.5") == 3.5

    def test_add_sub(self):
        assert c("2 + 3 - 1") == 4

    def test_precedence_mul_over_add(self):
        assert c("2 + 3 * 4") == 14

    def test_parens_override(self):
        assert c("(2 + 3) * 4") == 20

    def test_left_assoc_sub(self):
        assert c("10 - 2 - 3") == 5

    def test_true_division(self):
        assert c("7 / 2") == 3.5

    def test_floor_division(self):
        assert c("7 // 2") == 3

    def test_modulo(self):
        assert c("10 % 3") == 1

    def test_mixed_float_int(self):
        assert c("1.5 + 2") == 3.5

    def test_nested_parens(self):
        assert c("((1 + 2) * (3 + 4))") == 21

    def test_no_spaces(self):
        assert c("(n+1)*2", n=5) == 12


class TestUnary:
    def test_negative(self):
        assert c("-5") == -5

    def test_double_negative(self):
        assert c("--5") == 5

    def test_triple_chain(self):
        assert c("- - -2") == -2

    def test_neg_parens(self):
        assert c("-(2 + 3)") == -5

    def test_neg_binds_tighter_than_mul(self):
        assert c("-2 * 3") == -6

    def test_neg_string_is_dosa(self):
        with pytest.raises(ExprError):
            c('-"om"')


class TestComparisons:
    def test_lt(self):
        assert c("3 < 5") is True

    def test_le_ge(self):
        assert c("5 <= 5") is True
        assert c("4 >= 5") is False

    def test_eq_ne(self):
        assert c("5 == 5") is True
        assert c("3 != 4") is True

    def test_int_float_eq(self):
        assert c("5 == 5.0") is True

    def test_string_comparison(self):
        assert c('"ansh" < "om"') is True
        assert c('"om" == "om"') is True

    def test_cmp_of_sums(self):
        assert c("2 + 2 == 2 * 2") is True

    def test_mixed_type_cmp_is_dosa(self):
        with pytest.raises(ExprError):
            c('1 < "om"')


class TestLogical:
    def test_na_truthiness(self):
        assert c("na 0") is True
        assert c("na 1") is False
        assert c('na ""') is True

    def test_na_chain(self):
        assert c("na na 108") is True

    def test_ca_returns_operand(self):
        assert c("1 ca 2") == 2
        assert c("0 ca 2") == 0

    def test_va_returns_operand(self):
        assert c("2 vA 3") == 2
        assert c("0 vA 3") == 3

    def test_precedence_na_ca_va(self):
        # na > ca > vA:  1 vA (0 ca 0) = 1 ;  (na 0) ca 5 = 5
        assert c("1 vA 0 ca 0") == 1
        assert c("na 0 ca 5") == 5

    def test_short_circuit_va(self):
        assert c("1 vA 1 / 0") == 1        # right side never runs

    def test_short_circuit_ca(self):
        assert c("0 ca 1 / 0") == 0

    def test_lowercase_va_alias(self):
        assert c("0 va 3") == 3

    def test_devanagari_spellings(self):
        assert c("1 च 2") == 2
        assert c("0 वा 3") == 3
        assert c("न 0") is True

    def test_with_comparisons(self):
        assert c("n > 3 ca n < 10", n=5) is True
        assert c("n < 3 vA n > 4", n=5) is True

    def test_operator_word_alone_is_dosa(self):
        with pytest.raises(ExprError):
            c("ca")
        with pytest.raises(ExprError):
            c("1 ca")


class TestVariablesAndStrings:
    def test_variable(self):
        assert c("n * 2", n=5) == 10

    def test_unknown_name_is_dosa(self):
        with pytest.raises(ExprError):
            c("nirvana")

    def test_string_concat(self):
        assert c('"om" + "kAra"') == "omkAra"

    def test_string_repeat(self):
        assert c('"om " * 3') == "om om om "

    def test_string_with_spaces(self):
        assert c('"namaste loka"') == "namaste loka"

    def test_string_plus_int_is_dosa(self):
        with pytest.raises(ExprError):
            c('"om" + 1')


class TestDosa:
    def test_division_by_zero(self):
        with pytest.raises(ExprError):
            c("1 / 0")
        with pytest.raises(ExprError):
            c("1 // 0")
        with pytest.raises(ExprError):
            c("1 % 0")

    def test_empty_expression(self):
        with pytest.raises(ExprError):
            c("")

    def test_multiword_bare_text(self):
        # the sthApaya fallback depends on this raising cleanly
        with pytest.raises(ExprError):
            c("karmaNy evAdhikAras te")

    def test_missing_close_paren(self):
        with pytest.raises(ExprError):
            c("(1 + 2")

    def test_trailing_operator(self):
        with pytest.raises(ExprError):
            c("1 +")

    def test_dunder_import_is_just_unknown_name(self):
        with pytest.raises(ExprError):
            c("__import__")

    def test_call_syntax_is_dosa(self):
        with pytest.raises(ExprError):
            c('__import__("os")')

    def test_attribute_access_is_dosa(self):
        with pytest.raises(ExprError):
            c("env.keys")

    def test_subscript_is_dosa(self):
        with pytest.raises(ExprError):
            c("a[0]")

    def test_error_carries_position(self):
        with pytest.raises(ExprError) as e:
            c("1 + + 2")
        assert e.value.line == 1
        assert e.value.col == 5

    def test_all_dosa_are_exprerror_not_python(self):
        for bad in ("1/0", "x", "1 +", "(", "a.b", "a[1]", '"om" + 1', ""):
            with pytest.raises(ExprError):
                c(bad)
