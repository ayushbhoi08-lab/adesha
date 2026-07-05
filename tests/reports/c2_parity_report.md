# C2 Co-sim Parity Report — lane_residue three-way agreement

- Date: 2026-07-04
- Verdict: **ALL PASS**
- Lane programs: **1000/1000** three-way identical (N=1000, seed=108)
- A-TS `.aos` programs: **12/12** chain-0 stamps echoed by RTL
- Simulator: Icarus Verilog version 12.0 (devel) (s20150603-1539-g2693dd32b)
- RTL: isolated copy of `core_top` + 9 submodules, copied read-only from the private chip repository (the RTL itself is not published; this report is the evidence record). S9 artifacts untouched.
- Packets driven: 6067; tick monitor errors: 0.

The three parties, per input text:

1. `aos_asm._lane_fold_builtin` — this repo's built-in mirror (software)
2. `golden_model.fold_text` — the §2-verified golden model (imported read-only from the private chip repository)
3. `core_top` RTL under Icarus Verilog — golden-path feet streamed as FOLD packets + terminal RESET; fingerprint = last committed maṇḍala (the A-TS testbench rule, adapted from `tb_cosim_ats.v`)

## Input classes

| Class | N | Three-way pass |
|---|---|---|
| hk_verse | 240 | 240/240 |
| hk_synth | 240 | 240/240 |
| lowercase | 140 | 140/140 |
| ignored_or_empty | 100 | 100/100 |
| long_gt108 | 160 | 160/160 |
| mixed_ascii | 120 | 120/120 |
| **total** | **1000** | **1000/1000** |

Class notes: `hk_verse` = Harvard-Kyoto verses (BG 2.47, gāyatrī, BG 18.66, BG 4.7, Īśa 1, …) plus seeded substrings/shuffles/joins; `hk_synth` = random HK syllable strings; `lowercase` = all-lowercase degenerates 1–300 chars; `ignored_or_empty` = empty string, digits/punctuation-only, raw Devanagari (every char ignored → single zero foot); `long_gt108` = 109–1500 chars; `mixed_ascii` = random printable ASCII incl. length 0.

## Mismatches

None. All 1,000 lane inputs agree bit-for-bit across all three implementations.

## A-TS `.aos` program signatures

The A-TS harness construction (byte events → tick + feet → one FOLD chain, chain 0, B=108, seed=1) applied to `.aos` source texts; builder = `cosim_ats.ats_program` (reused, not re-implemented), which itself asserts real-Notarizer and S7-loopback agreement before any RTL runs.

| pid | program | events | chain-0 stamp | RTL | match |
|---|---|---|---|---|---|
| 1000 | aos_demo | 1 | 0x1f54 | 0x1f54 | OK |
| 1001 | aos_rand_0 | 9 | 0x0e65 | 0x0e65 | OK |
| 1002 | aos_rand_1 | 10 | 0x0540 | 0x0540 | OK |
| 1003 | aos_rand_2 | 1 | 0x1fa6 | 0x1fa6 | OK |
| 1004 | aos_rand_3 | 1 | 0x28ec | 0x28ec | OK |
| 1005 | aos_rand_4 | 1 | 0x2585 | 0x2585 | OK |
| 1006 | aos_rand_5 | 1 | 0x006b | 0x006b | OK |
| 1007 | aos_rand_6 | 1 | 0x24c5 | 0x24c5 | OK |
| 1008 | aos_rand_7 | 1 | 0x15c1 | 0x15c1 | OK |
| 1009 | aos_rand_8 | 1 | 0x097d | 0x097d | OK |
| 1010 | aos_pair_base | 1 | 0x2e1f | 0x2e1f | OK |
| 1011 | aos_pair_swap | 1 | 0x21dc | 0x21dc | OK |

Order sensitivity on the RTL: fp(aos_pair_base) ≠ fp(aos_pair_swap) — PASS.

## Gate legs

- [PASS] three-way lane parity (builtin == golden == RTL), 1000/1000
- [PASS] A-TS .aos chain-0 stamps echoed by RTL, 12/12
- [PASS] order sensitivity on RTL (.aos pair): 0x2e1f != 0x21dc
- [PASS] tick monitor clean (tick_errors=0)
- [PASS] RTL program count == battery size (1012 vs 1012)

## Findings

1. **The “all-lowercase → constant 108” claim only holds up to 28 letters.** Of 140 lowercase inputs, 123 fold to values ≠ 108 — texts with more than 28 laghu bits slice into multiple zero feet, so h keeps folding (e.g. two zero feet → (1·108+0)·108+0 = 11664 mod 12289). All three implementations agree on every such input, so parity is intact; the earlier docstring/plan wording was an overclaim and has been corrected in `aos_asm.py`.
2. What this does **not** prove: the 27-hex software mudrā (mod M107) is not chip-runnable on one lane and was not tested here; chip-true integrity remains the C3 `sAkSya` / A-TS 8-chain construction. One lane residue is 14 bits and is not an integrity primitive.

## Reproduce

```
cd tests/cosim_c2
python c2_cosim.py
C:\iverilog\bin\iverilog -g2012 -o tb_cosim_c2.vvp rtl/*.v tb_cosim_c2.v
C:\iverilog\bin\vvp tb_cosim_c2.vvp
python check_c2.py
```
