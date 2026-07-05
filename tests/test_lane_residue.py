"""
Tests for aos_asm.lane_residue and the underlying built-in mirror.

Expected values are hardcoded from a run against golden_model.fold_text
(the verified golden model in the private chip repository).
The mirror must match those values bit-for-bit — that is the C2 parity claim.
"""

import pytest
import aos_asm

VERSE = (
    "karmaNy evAdhikAras te mA phaleSu kadAcana "
    "| mA karma-phala-hetur bhUr mA te saMgo 'stv akarmaNi"
)

# ---------------------------------------------------------------------------
# Hardcoded golden-model reference values (computed 2026-07-04, golden_model.py)
# ---------------------------------------------------------------------------
VECTORS = [
    # (label, text, expected_int, expected_hex)
    ("BG 2.47 verse",          VERSE,       11394, "2c82"),
    ("all-lowercase 'namaste'", "namaste",     108, "006c"),
    ("empty string",           "",             108, "006c"),
    ("uppercase 'AUM'",        "AUM",         1475, "05c3"),
    ("first word 'karmaNy'",   "karmaNy",     3863, "0f17"),
    ("digits only '108'",      "108",          108, "006c"),
    ("mixed 'adeShA'",         "adeShA",      6594, "19c2"),
]


class TestLaneResidueMirror:
    """_lane_fold_builtin must equal the golden model on every vector."""

    @pytest.mark.parametrize("label,text,expected,_hex", VECTORS)
    def test_mirror_matches_golden(self, label, text, expected, _hex):
        assert aos_asm._lane_fold_builtin(text) == expected, \
            f"{label}: mirror gave {aos_asm._lane_fold_builtin(text)}, want {expected}"

    @pytest.mark.parametrize("label,text,expected,_hex", VECTORS)
    def test_lane_residue_int(self, label, text, expected, _hex):
        assert aos_asm.lane_residue(text) == expected


class TestLaneResidueProperties:
    """Semantic properties of the lane residue."""

    def test_all_lowercase_is_constant_108(self):
        # no-uppercase text of <= 28 letters → all-zero bits → ONE zero foot
        # → h = 1*108+0 = 108. NOT true past 28 letters: multiple zero feet
        # keep folding (C2 finding — see tests/reports/c2_parity_report.md).
        for s in ("namaste", "a", "xyz", "108", "", "hello world 42"):
            assert aos_asm.lane_residue(s) == 108, f"expected 108 for {s!r}"

    def test_lowercase_past_28_letters_is_not_108(self):
        # 30 lowercase letters → 2 zero feet → (1*108+0)*108+0 = 11664 mod 12289
        assert aos_asm.lane_residue("a" * 30) == 11664

    def test_output_in_range(self):
        assert 0 <= aos_asm.lane_residue(VERSE) < 12289

    def test_stable(self):
        assert aos_asm.lane_residue(VERSE) == aos_asm.lane_residue(VERSE)

    def test_case_sensitive(self):
        # uppercase letters contribute 1-bits; swapping case changes the result
        assert aos_asm.lane_residue("AUM") != aos_asm.lane_residue("aum")

    def test_non_alpha_ignored(self):
        # digits, spaces, punctuation carry no bits
        assert aos_asm.lane_residue("karmaNy") == aos_asm.lane_residue("karma Ny 42!")

    def test_returns_int_not_str(self):
        result = aos_asm.lane_residue(VERSE)
        assert isinstance(result, int)

    def test_numeric_input_accepted(self):
        # lane_residue(5) → lane_residue("5") → all-zero bits → 108
        assert aos_asm.lane_residue(5) == 108


class TestFingerprintUnaffectedByGolden:
    """fingerprint() must return 27-hex mod M107 regardless of AOS_GOLDEN."""

    def test_fingerprint_length(self):
        assert len(aos_asm.fingerprint(VERSE)) == 27

    def test_fingerprint_known_verse(self):
        assert aos_asm.fingerprint(VERSE) == "1be04017e74cbcf0137ab188428"

    def test_fingerprint_known_integer(self):
        # fingerprint(5): _fold(5) = (1*108+5) % M107 = 113 → hex "071" padded to 27
        assert aos_asm.fingerprint(5) == "000000000000000000000000071"

    def test_fingerprint_differs_from_lane_residue(self):
        # the two primitives serve different purposes and must differ on real text
        fp = aos_asm.fingerprint(VERSE)
        lr = f"{aos_asm.lane_residue(VERSE):04x}"
        assert fp != lr
