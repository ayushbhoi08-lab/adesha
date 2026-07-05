#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A0S Temporal Assembly — the LOW-LEVEL layer of the Ādeśa stack.

Its instructions ARE the chip's residue operations. Right now they run on a
small software model of the chip (below). The op *shapes* mirror the A0S / FOLD
design — lane prime 12289, FOLD seeded h0=1 in base B=108, ~108-bit signature.
The exact locked semantics live in your §2 spec / golden_model.py; point
_fold() and LANE there to run against the real core.

    python aos_asm.py            # built-in demo
    python aos_asm.py file.aos   # run an assembly file
"""

import importlib.util
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LANE = 12289          # default RNS lane prime
BASE = 108            # FOLD base B
MOD  = 2**107 - 1     # M107, a Mersenne prime -> ~108-bit signature space
H0   = 1             # FOLD seed h0 = 1


def _digits(n, base):
    n = abs(int(n))
    if n == 0:
        yield 0
        return
    ds = []
    while n:
        ds.append(n % base)
        n //= base
    yield from reversed(ds)


def _to_int(value):
    """Numbers pass through; text becomes an integer via its UTF-8 bytes."""
    if isinstance(value, (int, float)):
        return int(value)
    return int.from_bytes(str(value).encode("utf-8"), "big")


def _fold(n):
    """FOLD: Horner evaluation in base B, seeded at h0=1, reduced mod M107."""
    h = H0
    for d in _digits(n, BASE):
        h = (h * BASE + d) % MOD
    return h


def fingerprint(value):
    """Bridge used by Ādeśa's `mudrā`: any value -> stable 27-hex signature.

    Always uses the software mudrā (Horner over base-108 integer digits, mod
    M107≈2^107). Env-independent — AOS_GOLDEN does NOT affect this function.
    This is the integrity primitive used by seal/parIkSA/mudrA.
    """
    return f"{_fold(_to_int(value)):027x}"


# ---- lane_residue: chip-true FOLD over laghu/guru bits (C1 role-split) ------
# AOS_GOLDEN env var: path to golden_model.py (in the private chip repository).
# lane_residue() delegates to golden_model.fold_text when set and importable;
# on load failure, prints a notice once and falls back to _lane_fold_builtin.
# fingerprint() is unaffected by AOS_GOLDEN.

_GOLDEN_FOLD_TEXT = None
_FOOT_WIDTH = 28    # DATA_BITS from §2 spec


def _try_load_golden():
    global _GOLDEN_FOLD_TEXT
    path = os.environ.get("AOS_GOLDEN", "").strip()
    if not path:
        return
    try:
        spec = importlib.util.spec_from_file_location("_aos_golden_model", path)
        gm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gm)
        _GOLDEN_FOLD_TEXT = gm.fold_text
    except Exception as exc:
        print(f"software model — §2-shaped, not §2-verified (AOS_GOLDEN load failed: {exc})")


_try_load_golden()


def _lane_bits(text):
    """a-z -> 0 (laghu), A-Z -> 1 (guru); all else ignored. Mirrors golden text_to_bits."""
    for ch in str(text):
        if "a" <= ch <= "z":
            yield 0
        elif "A" <= ch <= "Z":
            yield 1


def _pack_feet(bits_iter):
    """Pack bits MSB-first into _FOOT_WIDTH-wide feet; zero-pad the final foot.
    Returns at least [0] (empty input → single zero foot). Mirrors golden slice_bits_to_feet.
    """
    bits = list(bits_iter)
    if not bits:
        return [0]
    feet = []
    for i in range(0, len(bits), _FOOT_WIDTH):
        chunk = bits[i:i + _FOOT_WIDTH]
        v = 0
        for b in chunk:
            v = (v << 1) | b
        v <<= (_FOOT_WIDTH - len(chunk))
        feet.append(v)
    return feet


def _lane_fold_builtin(text):
    """Built-in mirror of golden_model.fold_text: §2 FOLD over laghu/guru bits, mod Q.
    Mirror of §2 fold_text — parity verified in C2.
    """
    h = H0
    for foot in _pack_feet(_lane_bits(text)):
        h = (h * BASE + foot) % LANE
    return h


def lane_residue(text):
    """Chip-true lane residue: §2 FOLD over laghu/guru bits of text, mod Q=12289.

    Returns an int in [0, Q-1] = [0, 12288]. NOT an integrity primitive (14 bits;
    all-lowercase text of <=28 letters returns 108 = 0x006c — longer lowercase
    text folds multiple zero feet and varies with length; C2 finding). Delegates
    to golden_model.fold_text when AOS_GOLDEN is set and importable; otherwise
    uses _lane_fold_builtin — mirror of §2 fold_text, C2-verified: three-way
    parity (builtin == golden == core_top RTL) on 1000/1000 randomized inputs
    (tests/reports/c2_parity_report.md).
    """
    if _GOLDEN_FOLD_TEXT is not None:
        return _GOLDEN_FOLD_TEXT(str(text))
    return _lane_fold_builtin(str(text))


# ---- sakshya_notarize: chip-true A-TS witness (C3 role-split) ----------------
# Loads ats_notarizer.Notarizer lazily from AOS_GOLDEN's directory (the same
# READ-ONLY isolation approach as C2: sys.dont_write_bytecode before any D:
# import, art_dir added to sys.path so ats_notarizer can find golden_model).
# The Notarizer class is cached once loaded; None is never cached so that a
# later call with AOS_GOLDEN set will still succeed.

_ATS_NOTARIZER_CLASS = None


def _ensure_ats_notarizer():
    global _ATS_NOTARIZER_CLASS
    if _ATS_NOTARIZER_CLASS is not None:
        return _ATS_NOTARIZER_CLASS
    path = os.environ.get("AOS_GOLDEN", "").strip()
    if not path:
        return None                         # AOS_GOLDEN absent — no caching
    art_dir = os.path.dirname(os.path.abspath(path))
    sys.dont_write_bytecode = True          # D: is READ-ONLY — no .pyc writes
    if art_dir not in sys.path:
        sys.path.insert(0, art_dir)
    try:
        import ats_notarizer as _ats        # noqa: PLC0415
        _ATS_NOTARIZER_CLASS = _ats.Notarizer
    except Exception:
        pass
    return _ATS_NOTARIZER_CLASS


def sakshya_notarize(text):
    """Chip-true A-TS witness: notarize text through the REAL 8-chain Notarizer
    (golden-model backend, n_chains=8, B=108/primitive-roots, no FPGA required).

    Creates a fresh Notarizer, notarizes str(text) as a single event (tick
    advances to 1, then content bytes are folded in), and returns the 28-hex
    chain digest — 8 chains × 14 bits ≈ 108.7-bit fingerprint.

    This IS a chip-true integrity value: the same computation the A-TS Notarizer
    runs on the real core_top RTL (C2-verified golden path). It is NOT the
    software mudrā (mod M107) — those are different algorithms with different
    roles (see Decision 4 in plans/TRACK_C_CHIP_DEVKIT.md).

    Requires AOS_GOLDEN env var pointing to golden_model.py in the chip
    Core_Artifacts directory. Raises RuntimeError if unavailable.
    """
    N = _ensure_ats_notarizer()
    if N is None:
        raise RuntimeError(
            "chip-true notarization requires AOS_GOLDEN=/path/to/golden_model.py")
    notar = N(n_chains=8)
    notar.notarize(str(text))
    return notar.root_hex()


# --- the assembly interpreter (the chip language itself) --------------------

def run(text):
    reg = {f"r{i}": 0 for i in range(8)}
    mod = LANE

    def val(tok):
        return reg[tok] if tok in reg else int(tok)

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        op, *args = line.replace(",", " ").split()

        if op == "lane":                            # set the RNS lane prime
            mod = int(args[0])
        elif op == "laghu":                         # load:  laghu rX, val
            reg[args[0]] = val(args[1]) % mod
        elif op in ("yoga", "योग"):                 # add:   yoga rX, rY, Z
            reg[args[0]] = (val(args[1]) + val(args[2])) % mod
        elif op in ("guNa", "guna", "गुण"):         # mul:   guNa rX, rY, Z
            reg[args[0]] = (val(args[1]) * val(args[2])) % mod
        elif op == "fold":                          # FOLD rX
            reg[args[0]] = _fold(reg[args[0]])
        elif op in ("mudrA", "mudra", "मुद्रा"):    # fingerprint rX
            print(f"mudrA {args[0]}: {reg[args[0]]:x}")
        elif op == "vada":                          # print rX
            print(f"{args[0]} = {reg[args[0]]}")
        else:
            print(f"ajñāta ādeśa (unknown op): {op}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            run(f.read())
    else:
        run(
            "lane 12289\n"
            "laghu r0, 42\n"
            "guNa  r0, r0, 7\n"
            "fold  r0\n"
            "vada  r0\n"
            "mudrA r0\n"
        )
