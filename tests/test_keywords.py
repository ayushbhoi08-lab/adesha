# -*- coding: utf-8 -*-
"""tests/test_keywords.py — one class per Ādeśa keyword.
All I/O is driven through adesha.interp.io_context.
tiSTha patches time.sleep so the suite never actually waits.
"""

import sys
import pytest
from unittest.mock import patch

from adesha.interp import run_line, io_context, main
from adesha.errors import DosA


# ---------------------------------------------------------------------------
# shared helper
# ---------------------------------------------------------------------------

def run_out(line, env=None, inputs=()):
    """Run one Ādeśa line; return (output_lines_list, env)."""
    if env is None:
        env = {}
    out = []
    inp = iter(inputs)
    with io_context(
        output_fn=lambda *a, **kw: out.append(" ".join(str(x) for x in a)),
        input_fn=lambda prompt="": next(inp),
    ):
        run_line(line, env)
    return out, env


# ---------------------------------------------------------------------------
# sthApaya
# ---------------------------------------------------------------------------

class TestSthApaya:
    def test_stores_int(self):
        _, env = run_out("sthApaya n 42")
        assert env["n"] == 42

    def test_stores_expression(self):
        _, env = run_out("sthApaya r 3 * 7")
        assert env["r"] == 21

    def test_uses_variable_in_expression(self):
        env = {"x": 5}
        run_out("sthApaya y x + 1", env)
        assert env["y"] == 6

    def test_fallback_stores_string(self):
        _, env = run_out("sthApaya s namaste")
        assert env["s"] == "namaste"

    def test_lowercase_alias(self):
        _, env = run_out("sthapaya k 9")
        assert env["k"] == 9

    def test_devanagari_alias(self):
        _, env = run_out("स्थापय m 3")
        assert env["m"] == 3


# ---------------------------------------------------------------------------
# vada
# ---------------------------------------------------------------------------

class TestVada:
    def test_prints_literal_word(self):
        out, _ = run_out("vada namaste")
        assert out == ["namaste"]

    def test_resolves_variable(self):
        env = {"x": 42}
        out, _ = run_out("vada x", env)
        assert out == ["42"]

    def test_mixed_literal_and_variable(self):
        env = {"n": 5}
        out, _ = run_out("vada n lokAH", env)
        assert out == ["5 lokAH"]

    def test_devanagari_alias(self):
        out, _ = run_out("वद hi")
        assert out == ["hi"]


# ---------------------------------------------------------------------------
# gaNaya
# ---------------------------------------------------------------------------

class TestGaNaya:
    def test_addition(self):
        out, _ = run_out("gaNaya 3 + 4")
        assert out == ["7"]

    def test_uses_variable(self):
        env = {"n": 10}
        out, _ = run_out("gaNaya n * 3", env)
        assert out == ["30"]

    def test_lowercase_alias(self):
        out, _ = run_out("ganaya 2 + 2")
        assert out == ["4"]

    def test_devanagari_alias(self):
        out, _ = run_out("गणय 6 * 6")
        assert out == ["36"]


# ---------------------------------------------------------------------------
# yadi
# ---------------------------------------------------------------------------

class TestYadi:
    def test_true_branch_executes(self):
        out, _ = run_out("yadi 1 : vada yes")
        assert out == ["yes"]

    def test_false_branch_is_silent(self):
        out, _ = run_out("yadi 0 : vada no")
        assert out == []

    def test_comparison_with_variable(self):
        env = {"n": 5}
        out, _ = run_out("yadi n > 3 : vada bahu", env)
        assert out == ["bahu"]

    def test_missing_colon_raises_dosa5(self):
        with pytest.raises(DosA) as exc:
            run_out("yadi 1 vada yes")
        assert exc.value.code == 5

    def test_devanagari_alias(self):
        out, _ = run_out("यदि 1 : vada ok")
        assert out == ["ok"]


# ---------------------------------------------------------------------------
# punaH
# ---------------------------------------------------------------------------

class TestPunaH:
    def test_repeats_n_times(self):
        out, _ = run_out("punaH 3 vada x")
        assert out == ["x", "x", "x"]

    def test_zero_repetitions(self):
        out, _ = run_out("punaH 0 vada no")
        assert out == []

    def test_count_from_variable(self):
        env = {"k": 2}
        out, _ = run_out("punaH k vada hi", env)
        assert out == ["hi", "hi"]

    def test_builds_counter(self):
        env = {"n": 0}
        run_out("punaH 5 sthApaya n n + 1", env)
        assert env["n"] == 5

    def test_lowercase_alias(self):
        out, _ = run_out("punah 2 vada a")
        assert out == ["a", "a"]

    def test_devanagari_alias(self):
        out, _ = run_out("पुनः 2 vada b")
        assert out == ["b", "b"]

    def test_non_integer_raises_dosa7(self):
        with pytest.raises(DosA) as exc:
            run_out("punaH abc vada x")
        assert exc.value.code == 7


# ---------------------------------------------------------------------------
# zRNu
# ---------------------------------------------------------------------------

class TestZRNu:
    def test_stores_input_as_string(self):
        _, env = run_out("zRNu x", inputs=["namaste"])
        assert env["x"] == "namaste"

    def test_numeric_input_stays_string(self):
        _, env = run_out("zRNu n", inputs=["108"])
        assert env["n"] == "108"
        assert isinstance(env["n"], str)

    def test_lowercase_alias(self):
        _, env = run_out("srnu y", inputs=["hello"])
        assert env["y"] == "hello"

    def test_devanagari_alias(self):
        _, env = run_out("शृणु z", inputs=["world"])
        assert env["z"] == "world"


# ---------------------------------------------------------------------------
# tiSTha — time.sleep is patched; no actual sleeping
# ---------------------------------------------------------------------------

class TestTiSTha:
    def test_sleeps_given_seconds(self):
        with patch("time.sleep") as mock_sleep:
            run_out("tiSTha 2")
        mock_sleep.assert_called_once_with(2.0)

    def test_sleeps_from_variable(self):
        with patch("time.sleep") as mock_sleep:
            env = {"t": 1}
            run_out("tiSTha t", env)
        mock_sleep.assert_called_once_with(1.0)

    def test_zero_sleep(self):
        with patch("time.sleep") as mock_sleep:
            run_out("tiSTha 0")
        mock_sleep.assert_called_once_with(0.0)

    def test_lowercase_alias(self):
        with patch("time.sleep") as mock_sleep:
            run_out("tishtha 1")
        mock_sleep.assert_called_once()

    def test_devanagari_alias(self):
        with patch("time.sleep") as mock_sleep:
            run_out("तिष्ठ 3")
        mock_sleep.assert_called_once_with(3.0)


# ---------------------------------------------------------------------------
# mudrA
# ---------------------------------------------------------------------------

class TestMudrA:
    def test_output_format(self):
        env = {"x": "hello"}
        out, _ = run_out("mudrA x", env)
        assert len(out) == 1
        prefix, hex_part = out[0].split(": ", 1)
        assert prefix == "mudrA x"
        assert len(hex_part) == 27
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_stability_same_input_same_output(self):
        env = {"v": "namaste"}
        out1, _ = run_out("mudrA v", env)
        out2, _ = run_out("mudrA v", env)
        assert out1 == out2

    def test_literal_word_fallback(self):
        out, _ = run_out("mudrA hello")
        assert out[0].startswith("mudrA hello: ")
        assert len(out[0].split(": ")[1]) == 27

    def test_lowercase_alias(self):
        env = {"v": "test"}
        out, _ = run_out("mudra v", env)
        assert "mudrA v:" in out[0]

    def test_devanagari_alias(self):
        env = {"v": "test"}
        out, _ = run_out("मुद्रा v", env)
        assert ": " in out[0]
        assert len(out[0].split(": ")[1]) == 27


# ---------------------------------------------------------------------------
# samApti
# ---------------------------------------------------------------------------

class TestSamApti:
    def test_raises_system_exit(self):
        with pytest.raises(SystemExit):
            run_out("samApti")

    def test_lowercase_alias(self):
        with pytest.raises(SystemExit):
            run_out("samapti")

    def test_devanagari_alias(self):
        with pytest.raises(SystemExit):
            run_out("समाप्ति")


# ---------------------------------------------------------------------------
# Script-mode halt: first doSa exits with code 1 and stops execution
# ---------------------------------------------------------------------------

class TestScriptHalt:
    def test_first_dosa_halts_exit_1(self, tmp_path):
        script = tmp_path / "bad.adesha"
        script.write_text(
            "vada before\nvad typo\nvada after\n", encoding="utf-8"
        )
        out = []
        old_argv = sys.argv[:]
        sys.argv = ["adesha.py", str(script)]
        try:
            with pytest.raises(SystemExit) as exc:
                with io_context(
                    output_fn=lambda *a, **kw: out.append(" ".join(str(x) for x in a))
                ):
                    main()
        finally:
            sys.argv = old_argv
        assert exc.value.code == 1
        assert out[0] == "before"
        assert "doSa-001" in out[1]
        assert not any("after" in line for line in out)
