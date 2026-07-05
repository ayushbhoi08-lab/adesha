# Ādeśa (आदेश)

**A Sanskrit programming language — from Pāṇini to silicon.**

Ādeśa ("command") is a small interpreted language whose keywords are real Sanskrit imperatives, written in the pure-ASCII [Harvard-Kyoto](https://en.wikipedia.org/wiki/Harvard-Kyoto) convention so they type on any keyboard. When you write `vada` you are writing वद — the loṭ lakāra imperative *"Speak!"* — and the machine obeys.

```text
$ python adesha.py
Ādeśa shell (Harvard-Kyoto) — type 'samApti' to quit.
>> vada namaste lokAH
namaste lokAH
>> punaH tri vada punarukti
punarukti
punarukti
punarukti
```

`punaH tri` — "again, three times." Numbers can be Sanskrit words (`eka`, `dvi`, `tri`, … `aSTottarazata` = 108) or digits; both work everywhere.

## Why Sanskrit?

Not decoration — lineage. Pāṇini's **Aṣṭādhyāyī** (~500 BCE) is a formal generative grammar of ~4,000 ordered rewrite rules with meta-rules and context-sensitive transformations — structurally the same device as the BNF notation that defines modern programming languages (computer scientists sometimes call it the *Pāṇini–Backus form*). **Piṅgala's** Chandaḥśāstra (~200 BCE) encoded poetic meter as sequences of light (laghu) and heavy (guru) syllables — a binary notation, two millennia early. Sanskrit is arguably the only human language that was *formally specified*, the way programming languages are. Ādeśa is built on that inheritance: Sanskrit **structure and vocabulary** — never a claim that the machine "understands" Sanskrit meaning.

## The language in one screen

```text
# lesson0_final.adesha — my first program
sthApaya nama rAma          # "establish!"  — set a variable
vada namaste nama           # "speak!"      — print (namaste rAma)

yadi nama == rAma           # "if"
    vada sAdhu              # blocks end with iti ("thus")
anyathA                     # "otherwise"
    vada anyat
iti

vidhi ghata n               # "procedure"  — define a function
    yadi n <= eka
        dehi 1              # "give!"      — return a value
    iti
    dehi n * ghata(n - 1)
iti
gaNaya ghata(paJca)         # "compute!"   — 120 (recursion works)

samUha s                    # "collection" — make a list
yojaya s Adi                # "join!"      — append
vada s[eka]                 # 1-based indexing: eka is the first element

mudrA nama                  # "seal!"      — 108-bit integrity fingerprint
```

Booleans are `satya`/`asatya`. Logic is `ca`/`vA`/`na` (and/or/not). Errors speak both languages with a numbered `doSa` code, a line number, and a did-you-mean:

```text
>> vad namaste
doSa-001: ajYAta Adeza 'vad' (did you mean: vada?) — unknown command 'vad' (did you mean: vada?)
```

Every keyword is registered in three spellings: Harvard-Kyoto canonical (`sthApaya`), lowercase (`sthapaya`), and Devanagari (`स्थापय`).

## Sealed scripts

`adesha seal file.adesha` stamps a script with its own fingerprint footer; `adesha parIkSA file.adesha` later answers **siddha** (intact, exit 0) or **bhraSTa** (tampered, exit 1). Like a wax seal on a letter — tamper-evident homework, lesson files, and documents.

## Two layers, honestly labeled

Ādeśa is a two-layer stack:

- **`adesha/`** — the high-level language (this repo, fully self-contained, Python stdlib only).
- **`aos_asm.py`** — a low-level layer whose FOLD/lane operations mirror a private RNS chip design (the A0S project). It runs here on a **software model**. The chip-true `lane_residue()` in this repo was verified against the chip's RTL by co-simulation: **1,000/1,000 randomized inputs agree bit-for-bit** across the built-in mirror, the verified golden model, and the Verilog core under Icarus Verilog — see [tests/reports/c2_parity_report.md](tests/reports/c2_parity_report.md). The chip design itself is not in this repo, and nothing here requires it.

Two different numbers, two different jobs: `mudrA` is a 108-bit *software* integrity fingerprint (mod M107); the *chip lane residue* (mod 12289) reflects Harvard-Kyoto prosodic weight and is deliberately **not** an integrity primitive.

## Try it

```bash
git clone https://github.com/ayushbhoi08-lab/adesha.git
cd adesha
python adesha.py                       # REPL
python adesha.py examples/zloka_mudra.adesha   # seal a Bhagavad Gītā verse
python adesha.py --trace run examples/function.adesha  # watch it execute
python -m pytest tests -q              # the test suite
```

The browser playground (Pyodide, zero install) lives in [playground/](playground/) — serve it with `python -m http.server` from that folder, or open it directly at **https://ayushbhoi08-lab.github.io/adesha/**.

New to programming? Start with [Lesson Zero](docs/lessons/lesson0.md) — five steps that teach one programming concept and one real Sanskrit grammar note at a time.

## Status

Active, early, and honest about it. The language core (tokenizer, expression parser, blocks, functions with recursion, lists, dual-language errors, seal/verify CLI) is complete and tested. On the roadmap: a sandhi-based macro layer (Pāṇini's own mechanism as a language feature), an aṣṭa-dik turtle for teaching, and offline Sanskrit voice commands. This project makes **no claims** of natural-language understanding, translation, or NLP.

## License

[Apache-2.0](LICENSE)
