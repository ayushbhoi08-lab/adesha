# Lesson Zero — First Words

> **For:** a student who knows a little Sanskrit and has never programmed before.  
> **Goal:** write five tiny commands, understand why each one is Sanskrit, and walk away with your own sealed program.

In Ādeśa, every command is a Sanskrit word you can actually say out loud. You do not need to memorize rules first — you will learn one command at a time, run it, and see what happens.

---

## Step 1 — `vada`: make the computer speak

**What it does:** `vada` tells the computer to print something on the screen.

Type this in the playground and press **Run**:

```adesha
vada namaste
```

**Output:**

```text
namaste
```

The computer said back exactly what you told it to say.

> **Grammar note:** `vada` (वद) is the **loṭ lakāra** — the imperative mood. It is a real command: "Speak!"

**Try it:** change `namaste` to your own name or a Sanskrit word you like, then run again.

---

## Step 2 — `sthApaya`: remember something in a box

**What it does:** `sthApaya` gives a name to a value so you can use it later. Think of it as writing a word on a box and putting something inside.

```adesha
sthApaya nama rAma
vada namaste nama
```

**Output:**

```text
namaste rAma
```

First we put `rAma` into the box called `nama`. Then `vada namaste nama` printed `namaste` followed by whatever was in the box.

> **Grammar note:** `sthApaya` (स्थापय) is the causative imperative of the root √sthā, "to stand." It means "make it stand" — in other words, **establish!** That is why it is the command for making a variable.

**Try it:** change `rAma` to your name. The second line does not need to change at all.

---

## Step 3 — `punaH`: do it again

**What it does:** `punaH` repeats a command without you having to type it many times.

In Ādeśa you can count with **Sanskrit number-words** or with ordinary digits. Both work. Here is the Sanskrit way:

```adesha
punaH tri
    vada jaya
iti
```

**Output:**

```text
jaya
jaya
jaya
```

`tri` means "three," so the line inside (`vada jaya`) ran three times.

> **Grammar note:** `punaH` (पुनः) means **"again."** It is not a verb; it is an adverb that tells the command to come back and repeat.

**Try it:** replace `tri` with `paJca` (five) or with the digit `5`. Both will print `jaya` five times.

---

## Step 4 — `yadi`: choose a path

**What it does:** `yadi` lets the computer pick one of two things to do, depending on whether something is true.

```adesha
sthApaya x eka
yadi x == 1
    vada sAdhu
iti
```

**Output:**

```text
sAdhu
```

We put `eka` (one) into the box `x`. Then we asked: "Is `x` equal to 1?" Because the answer is **satya** (true), the computer printed `sAdhu` (well done).

If you change `eka` to `dvi` (two), nothing will print, because `x == 1` would be **asatya** (false).

> **Grammar note:** `yadi` (यदि) means **"if."** The same word is used in classical Sanskrit to open a conditional sentence.

**Try it:** change `eka` to `dvi` and run. Then change it back.

---

## Step 5 — `mudrA`: seal your first program

**What it does:** `mudrA` makes a fingerprint — a short code that proves your program has not been changed.

Here is a complete first program. Save it as `lesson0.adesha`:

```adesha
# mama prathamaH AdezaH
sthApaya nama rAma
vada namaste nama
mudrA nama
```

**Output:**

```text
namaste rAma
mudrA nama: 0000000000000000003de0b1961
```

The last line printed a fingerprint of the name `rAma`.

Now let us seal the *whole program*. In a terminal, run:

```bash
adesha seal lesson0.adesha
```

Your file now ends with a seal line like this:

```adesha
# mudrA: 5b7b4e4e4688f34e2e6031bf7c9
```

You can check it with:

```bash
adesha parIkSA lesson0.adesha
```

**Output:**

```text
siddha
```

`siddha` means "intact." If anyone changes even one letter in your file and you check it again, it will say `bhraSTa` (tampered). You now have a sealed artifact you made yourself.

> **Grammar note:** `mudrA` (मुद्रा) means **"seal"** — like the wax seal on a royal letter. Kings pressed their ring into wax so everyone knew the letter was untouched. Your `mudrA` does the same thing with math.

---

## What you learned

| Step | Command | Concept | Sanskrit grammar |
|---|---|---|---|
| 1 | `vada` (वद) | output | loṭ lakāra imperative: "Speak!" |
| 2 | `sthApaya` (स्थापय) | variables | causative imperative of √sthā: "Establish!" |
| 3 | `punaH` (पुनः) | loops | adverb meaning "again" |
| 4 | `yadi` (यदि) | conditionals | classical Sanskrit word for "if" |
| 5 | `mudrA` (मुद्रा) | integrity / seal | noun meaning "seal" |

You also met the A2 language features that make Ādeśa gentle for beginners:

- **Sanskrit number-words** like `eka`, `dvi`, `tri` work alongside digits.
- **`satya` / `asatya`** are the words for true and false.

Save your sealed `lesson0.adesha` somewhere safe. In the next lesson we will build on it.
