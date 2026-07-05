# -*- coding: utf-8 -*-
"""tests/test_a1.py — Phase A1 language features:
blocks (iti), else (anyathA), while (yAvat), functions (vidhi), lists (samUha).
"""

import pytest

from adesha.interp import run_line, io_context, execute_statements, parse_statements
from adesha.errors import DosA


def run_source(text, env=None):
    """Run a multi-line Ādeśa source string; return (output_lines_list, env)."""
    if env is None:
        env = {}
    out = []
    lines = [(i + 1, l) for i, l in enumerate(text.splitlines())]
    with io_context(
        output_fn=lambda *a, **kw: out.append(" ".join(str(x) for x in a)),
    ):
        stmts, _, term = parse_statements(lines, 0)
        assert term == "eof", f"unexpected terminator {term!r}"
        execute_statements(stmts, env)
    return out, env


# ---------------------------------------------------------------------------
# yadi blocks
# ---------------------------------------------------------------------------

class TestYadiBlock:
    def test_block_true_branch(self):
        out, _ = run_source("""
sthApaya n 5
yadi n > 3
    vada yes
iti
""")
        assert out == ["yes"]

    def test_block_false_branch_skips(self):
        out, _ = run_source("""
sthApaya n 1
yadi n > 3
    vada yes
iti
vada done
""")
        assert out == ["done"]

    def test_inline_still_works(self):
        out, _ = run_source("yadi 1 : vada yes")
        assert out == ["yes"]


class TestAnyathA:
    def test_else_branch(self):
        out, _ = run_source("""
sthApaya n 2
yadi n > 5
    vada bahu
anyathA
    vada alpam
iti
""")
        assert out == ["alpam"]

    def test_then_branch_with_else(self):
        out, _ = run_source("""
sthApaya n 10
yadi n > 5
    vada bahu
anyathA
    vada alpam
iti
""")
        assert out == ["bahu"]

    def test_anyathA_outside_yadi_raises_dosa10(self):
        with pytest.raises(DosA) as exc:
            run_source("anyathA\nvada no")
        assert exc.value.code == 10


class TestNestedYadi:
    def test_nested_blocks(self):
        out, _ = run_source("""
sthApaya a 1
sthApaya b 2
yadi a == 1
    yadi b == 2
        vada both
    iti
iti
""")
        assert out == ["both"]


# ---------------------------------------------------------------------------
# punaH blocks
# ---------------------------------------------------------------------------

class TestPunaHBlock:
    def test_block_repeat(self):
        out, _ = run_source("""
punaH 3
    vada x
iti
""")
        assert out == ["x", "x", "x"]

    def test_inline_still_works(self):
        out, _ = run_source("punaH 2 vada y")
        assert out == ["y", "y"]

    def test_repeat_zero_times(self):
        out, _ = run_source("punaH 0\n    vada no\niti")
        assert out == []


# ---------------------------------------------------------------------------
# yAvat while loop
# ---------------------------------------------------------------------------

class TestYAvat:
    def test_while_counts_up(self):
        out, _ = run_source("""
sthApaya n 1
yAvat n <= 3
    vada n
    sthApaya n n + 1
iti
""")
        assert out == ["1", "2", "3"]

    def test_while_false_from_start(self):
        out, _ = run_source("""
sthApaya n 10
yAvat n < 5
    vada n
iti
vada done
""")
        assert out == ["done"]

    def test_devanagari_spelling(self):
        out, _ = run_source("""
sthApaya n 1
यावत् n <= 2
    vada n
    sthApaya n n + 1
iti
""")
        assert out == ["1", "2"]


# ---------------------------------------------------------------------------
# vidhi functions
# ---------------------------------------------------------------------------

class TestVidhi:
    def test_function_definition_and_call(self):
        out, _ = run_source("""
vidhi abhivAdana nAma
    vada namaste nAma
iti

abhivAdana "Rama"
""")
        assert out == ["namaste Rama"]

    def test_function_with_multiple_params(self):
        out, _ = run_source("""
vidhi phala x y
    gaNaya x + y
iti

phala 10 32
""")
        assert out == ["42"]

    def test_function_locals_do_not_leak(self):
        out, env = run_source("""
vidhi setx val
    sthApaya x val
iti

setx 99
vada x
""")
        # x is local to the function, so resolving it as a bare word prints "x"
        assert out == ["x"]

    def test_function_can_read_outer_variable(self):
        out, _ = run_source("""
sthApaya greeting hello
vidhi sayit
    vada greeting
iti

sayit
""")
        assert out == ["hello"]

    def test_wrong_argument_count_raises_dosa11(self):
        with pytest.raises(DosA) as exc:
            run_source("""
vidhi one a
    vada a
iti

one 1 2
""")
        assert exc.value.code == 11

    def test_devanagari_spelling(self):
        out, _ = run_source("""
विधि dviguNa x
    gaNaya x * 2
iti

dviguNa 11
""")
        assert out == ["22"]


# ---------------------------------------------------------------------------
# samUha lists
# ---------------------------------------------------------------------------

class TestSamUha:
    def test_create_and_print(self):
        out, env = run_source("samUha L 1 2 3\nvada L")
        assert out == ["[1, 2, 3]"]
        assert env["L"] == [1, 2, 3]

    def test_empty_list(self):
        out, env = run_source("samUha zUnyA\nvada zUnyA")
        assert out == ["[]"]
        assert env["zUnyA"] == []

    def test_yojaya_append(self):
        out, env = run_source("samUha L 1\nyojaya L 2\nyojaya L 3\nvada L")
        assert out == ["[1, 2, 3]"]

    def test_dIrghA_length_list(self):
        out, _ = run_source("samUha L a b c\ngaNaya dIrghA(L)")
        assert out == ["3"]

    def test_dIrghA_length_string(self):
        out, _ = run_source("sthApaya zloka namaste\ngaNaya dIrghA(zloka)")
        assert out == ["7"]

    def test_dIrghA_in_sthApaya(self):
        out, env = run_source("samUha L 1 2\nsthApaya n dIrghA(L)\nvada n")
        assert out == ["2"]

    def test_append_to_non_list_raises_dosa12(self):
        with pytest.raises(DosA) as exc:
            run_source("sthApaya x 5\nyojaya x 3")
        assert exc.value.code == 12

    def test_devanagari_spellings(self):
        out, _ = run_source("""
समूह L 1
योजय L 2
गणय दीर्घा(L)
""")
        assert out == ["2"]


# ---------------------------------------------------------------------------
# block structure errors
# ---------------------------------------------------------------------------

class TestBlockErrors:
    def test_missing_iti_raises_dosa9(self):
        with pytest.raises(DosA) as exc:
            run_source("""
yadi 1
    vada yes
vada done
""")
        assert exc.value.code == 9

    def test_unmatched_iti_raises_dosa8(self):
        with pytest.raises(DosA) as exc:
            run_source("iti")
        assert exc.value.code == 8

    def test_nested_missing_iti_raises_dosa9(self):
        with pytest.raises(DosA) as exc:
            run_source("""
yadi 1
    yadi 2
        vada yes
vada done
""")
        assert exc.value.code == 9


# ---------------------------------------------------------------------------
# mixed / edge cases
# ---------------------------------------------------------------------------

class TestMixed:
    def test_inline_and_block_together(self):
        out, _ = run_source("""
yadi 1 : vada inline
yadi 1
    vada block
iti
""")
        assert out == ["inline", "block"]

    def test_function_inside_while(self):
        out, _ = run_source("""
vidhi greet
    vada hi
iti

sthApaya n 1
yAvat n <= 2
    greet
    sthApaya n n + 1
iti
""")
        assert out == ["hi", "hi"]

    def test_comments_ignored_in_block_parser(self):
        out, _ = run_source("""
# outer comment
yadi 1
    # inner comment
    vada yes
iti
""")
        assert out == ["yes"]
