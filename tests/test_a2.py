# -*- coding: utf-8 -*-
"""tests/test_a2.py — Phase A2 language features:
dEhi return values, 1-based list indexing, satya/asatya booleans,
Sanskrit number-word literals, and --trace mode.
"""

import sys
import pytest

import adesha.interp as interp
from adesha.interp import (
    run_line, io_context, execute_statements, parse_statements, repl, main
)
from adesha.errors import DosA, raise_dosa


def run_source(text, env=None, trace=False):
    """Run a multi-line Ādeśa source string; return (output_lines_list, env)."""
    if env is None:
        env = {}
    out = []
    lines = [(i + 1, l) for i, l in enumerate(text.splitlines())]
    old_trace = interp._TRACE
    interp._TRACE = trace
    try:
        with io_context(
            output_fn=lambda *a, **kw: out.append(" ".join(str(x) for x in a)),
        ):
            stmts, _, term = parse_statements(lines, 0)
            assert term == "eof", f"unexpected terminator {term!r}"
            try:
                execute_statements(stmts, env)
            except interp.DehiReturn:
                raise_dosa(11, msg="dehi outside vidhi")
    finally:
        interp._TRACE = old_trace
    return out, env


# ---------------------------------------------------------------------------
# dehi — function return values
# ---------------------------------------------------------------------------

class TestDehi:
    def test_basic_return(self):
        out, _ = run_source("""
vidhi paJca
    dehi 5
iti

gaNaya paJca()
""")
        assert out == ["5"]

    def test_return_used_in_expression(self):
        out, _ = run_source("""
vidhi dviguNa x
    dehi x * 2
iti

sthApaya n dviguNa(21)
gaNaya n
""")
        assert out == ["42"]

    def test_return_used_in_sthApaya(self):
        out, _ = run_source("""
vidhi saMkhyA
    dehi eka
iti

sthApaya x saMkhyA()
vada x
""")
        assert out == ["1"]

    def test_function_without_dehi_returns_none(self):
        out, env = run_source("""
vidhi mouna
    vada hi
iti

sthApaya x mouna()
vada x
""")
        assert out == ["hi", "None"]

    def test_multiple_arguments_in_expression_call(self):
        out, _ = run_source("""
vidhi yoga a b
    dehi a + b
iti

gaNaya yoga(10 32)
""")
        assert out == ["42"]

    def test_nested_function_calls(self):
        out, _ = run_source("""
vidhi bAhya x
    dehi x + 1
iti

vidhi antara y
    dehi bAhya(y) * 2
iti

gaNaya antara(5)
""")
        assert out == ["12"]

    def test_dehi_outside_function_raises_dosa11(self):
        with pytest.raises(DosA) as exc:
            run_source("dehi 5")
        assert exc.value.code == 11

    def test_devanagari_dehi_spelling(self):
        out, _ = run_source("""
विधि dviguNa x
    देहि x * 2
iti

gaNaya dviguNa(7)
""")
        assert out == ["14"]

    def test_statement_call_still_works(self):
        out, _ = run_source("""
vidhi abhivAdana nAma
    vada namaste nAma
iti

abhivAdana "Rama"
""")
        assert out == ["namaste Rama"]


# ---------------------------------------------------------------------------
# List indexing — 1-based
# ---------------------------------------------------------------------------

class TestIndexing:
    def test_first_element_is_index_one(self):
        out, _ = run_source("samUha L a b c\nvada L[1]")
        assert out == ["a"]

    def test_second_element(self):
        out, _ = run_source("samUha L 10 20 30\ngaNaya L[2]")
        assert out == ["20"]

    def test_out_of_range_raises_dosa13(self):
        with pytest.raises(DosA) as exc:
            run_source("samUha L a b\nvada L[3]")
        assert exc.value.code == 13

    def test_index_zero_raises_dosa13(self):
        with pytest.raises(DosA) as exc:
            run_source("samUha L a b\nvada L[zUnya]")
        assert exc.value.code == 13

    def test_negative_index_raises_dosa13(self):
        with pytest.raises(DosA) as exc:
            run_source("samUha L a b\nvada L[-1]")
        assert exc.value.code == 13

    def test_string_indexing(self):
        out, _ = run_source('sthApaya zloka "namaste"\nvada zloka[1]')
        assert out == ["n"]

    def test_index_with_number_word(self):
        out, _ = run_source("samUha L a b c\nvada L[tri]")
        assert out == ["c"]

    def test_nested_list_indexing(self):
        out, _ = run_source("samUha M 2 3\nsamUha L 1 M 4\ngaNaya L[2][1]")
        assert out == ["2"]

    def test_index_in_expression(self):
        out, _ = run_source("samUha L 10 20 30\ngaNaya L[1] + L[dvi]")
        assert out == ["30"]


# ---------------------------------------------------------------------------
# satya / asatya booleans
# ---------------------------------------------------------------------------

class TestBooleans:
    def test_satya_literal(self):
        out, _ = run_source("sthApaya x satya\nvada x")
        assert out == ["satya"]

    def test_asatya_literal(self):
        out, _ = run_source("sthApaya x asatya\nvada x")
        assert out == ["asatya"]

    def test_comparison_prints_satya(self):
        out, _ = run_source("gaNaya 1 == 1")
        assert out == ["satya"]

    def test_comparison_prints_asatya(self):
        out, _ = run_source("gaNaya 1 == 2")
        assert out == ["asatya"]

    def test_boolean_in_conditional(self):
        out, _ = run_source("""
yadi satya
    vada yes
iti
""")
        assert out == ["yes"]

    def test_asatya_in_conditional(self):
        out, _ = run_source("""
yadi asatya
    vada yes
iti
vada no
""")
        assert out == ["no"]

    def test_devanagari_boolean_literals(self):
        out, _ = run_source("sthApaya x सत्य\nvada x\nsthApaya y असत्य\nvada y")
        assert out == ["satya", "asatya"]

    def test_list_with_booleans_displays_sanskrit(self):
        out, _ = run_source("samUha L satya asatya\nvada L")
        assert out == ["[satya, asatya]"]

    def test_logical_not_of_boolean(self):
        out, _ = run_source("gaNaya na satya")
        assert out == ["asatya"]


# ---------------------------------------------------------------------------
# Sanskrit number-word literals
# ---------------------------------------------------------------------------

class TestNumberWords:
    def test_all_basic_number_words(self):
        out, _ = run_source("""
gaNaya zUnya
gaNaya eka
gaNaya dvi
gaNaya tri
gaNaya catur
gaNaya paJca
gaNaya SaS
gaNaya sapta
gaNaya aSTa
gaNaya nava
""")
        assert out == [str(i) for i in range(10)]

    def test_daza_zata_aSTottarazata(self):
        out, _ = run_source("gaNaya daza\ngaNaya zata\ngaNaya aSTottarazata")
        assert out == ["10", "100", "108"]

    def test_number_word_equals_digit(self):
        out, _ = run_source("gaNaya tri == 3")
        assert out == ["satya"]

    def test_arithmetic_with_number_words(self):
        out, _ = run_source("gaNaya paJca + dvi")
        assert out == ["7"]

    def test_punaH_with_number_word(self):
        out, _ = run_source("punaH tri vada x")
        assert out == ["x", "x", "x"]

    def test_devanagari_number_words(self):
        out, _ = run_source("""
gaNaya शून्य
gaNaya पञ्च
gaNaya अष्टोत्तरशत
""")
        assert out == ["0", "5", "108"]

    def test_number_words_in_samUha(self):
        out, _ = run_source("samUha L eka dvi tri\ngaNaya L[1] + L[2] + L[3]")
        assert out == ["6"]

    def test_lowercase_aliases(self):
        out, _ = run_source("gaNaya tri + catur")
        assert out == ["7"]


# ---------------------------------------------------------------------------
# --trace mode
# ---------------------------------------------------------------------------

class TestTrace:
    def test_trace_prints_each_line(self):
        out, _ = run_source(
            "sthApaya n 5\nvada n",
            trace=True,
        )
        assert "1: sthApaya n 5" in out
        assert "2: vada n" in out
        assert "5" in out

    def test_trace_block_opener(self):
        out, _ = run_source(
            "sthApaya n 1\nyAvat n <= 2\n    vada n\n    sthApaya n n + 1\niti",
            trace=True,
        )
        # opener line appears
        assert any("yAvat n <= 2" in line for line in out)
        # body lines appear
        assert any("vada n" in line for line in out)
        assert any("sthApaya n n + 1" in line for line in out)

    def test_trace_off_by_default(self):
        out, _ = run_source("vada hi")
        assert out == ["hi"]

    def test_repl_trace(self):
        inputs = ["sthApaya n 3", "vada n", "samApti"]
        out = []
        repl(
            input_fn=lambda prompt="": inputs.pop(0),
            output_fn=lambda *a, **kw: out.append(" ".join(str(x) for x in a)),
            trace=True,
        )
        # trace line prefixes present (each REPL entry is line 1)
        assert sum(1 for line in out if line.startswith("1:")) >= 2
        assert "3" in out
