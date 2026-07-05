# -*- coding: utf-8 -*-
"""tests/test_examples.py — golden-stdout tests for all six examples/.
Input-consuming scripts (anumana, pratidhvani) receive injected stdin
via io_context; no subprocess needed.
"""

from pathlib import Path
import pytest

from adesha.interp import run_line, io_context

EXAMPLES = Path(__file__).parent.parent / "examples"


def run_script(name, inputs=()):
    """Run an example script; return list of output lines (one per print call)."""
    out = []
    inp = iter(inputs)
    env = {}
    with io_context(
        output_fn=lambda *a, **kw: out.append(" ".join(str(x) for x in a)),
        input_fn=lambda prompt="": next(inp),
    ):
        with open(EXAMPLES / name, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                run_line(line, env, lineno=lineno)
    return out


# ---------------------------------------------------------------------------
# namaste.adesha
# ---------------------------------------------------------------------------

class TestNamaste:
    def test_golden_output(self):
        assert run_script("namaste.adesha") == [
            "namaste lokAH",
            "ayam AdezaH asti",
        ]


# ---------------------------------------------------------------------------
# ganana.adesha
# ---------------------------------------------------------------------------

class TestGanana:
    def test_golden_output(self):
        assert run_script("ganana.adesha") == ["gaNanA", "108"]

    def test_counter_reaches_108(self):
        out = run_script("ganana.adesha")
        assert out[1] == "108"


# ---------------------------------------------------------------------------
# anumana.adesha  (interactive: zRNu + yadi)
# ---------------------------------------------------------------------------

class TestAnumana:
    def test_correct_guess(self):
        out = run_script("anumana.adesha", inputs=["108"])
        assert out == [
            "kimapi saMkhyAM cintaya",
            "sAdhu",
        ]

    def test_wrong_guess(self):
        out = run_script("anumana.adesha", inputs=["42"])
        assert out == [
            "kimapi saMkhyAM cintaya",
            "doSaH punaH yatnaM kuru",
        ]


# ---------------------------------------------------------------------------
# sarani108.adesha
# ---------------------------------------------------------------------------

class TestSarani108:
    def test_golden_table(self):
        assert run_script("sarani108.adesha") == [
            "108", "216", "324", "432",
            "540", "648", "756", "864", "972",
        ]


# ---------------------------------------------------------------------------
# zloka_mudra.adesha
# ---------------------------------------------------------------------------

_BG247_HK = (
    "karmaNy evAdhikAras te mA phaleSu kadAcana | "
    "mA karma-phala-hetur bhUr mA te saMgo 'stv akarmaNi"
)
_BG247_FINGERPRINT = "1be04017e74cbcf0137ab188428"


class TestZlokaMudra:
    def test_verse_line(self):
        out = run_script("zloka_mudra.adesha")
        assert out[0] == _BG247_HK

    def test_fingerprint_golden(self):
        out = run_script("zloka_mudra.adesha")
        assert out[1] == f"mudrA zloka: {_BG247_FINGERPRINT}"

    def test_fingerprint_stable(self):
        out1 = run_script("zloka_mudra.adesha")
        out2 = run_script("zloka_mudra.adesha")
        assert out1[1] == out2[1]


# ---------------------------------------------------------------------------
# pratidhvani.adesha  (interactive: zRNu + vada)
# ---------------------------------------------------------------------------

class TestPratidhvani:
    def test_echoes_input(self):
        out = run_script("pratidhvani.adesha", inputs=["namaste"])
        assert out == [
            "kimapi vada",
            "pratidhvani namaste",
        ]

    def test_echoes_different_input(self):
        out = run_script("pratidhvani.adesha", inputs=["Adeza"])
        assert out[1] == "pratidhvani Adeza"
