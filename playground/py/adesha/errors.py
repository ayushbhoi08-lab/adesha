# -*- coding: utf-8 -*-
"""
doSa (दोष, "fault/error") system — A0.3.

All interpreter errors flow through here.  Every doSa has:
  - a three-digit numeric code
  - a Sanskrit line (Harvard-Kyoto)
  - an English line
  - optional position ([pankti L] where pankti = "line")

Format:
    doSa-001 [pankti 7]: ajYAta Adeza "vad" — unknown command "vad" (did you mean: vada?)

Public API:
    DosA                    the one exception that crosses run_line -> REPL/script
    raise_dosa(code, ...)   build and raise a DosA
    suggest(word, names)    nearest match within edit distance <= 2, or ""
"""

# ---------------------------------------------------------------------------
# doSa code table
# Values are (sanskrit_template, english_template).
# Templates are str.format_map()-style with named keys.
# ---------------------------------------------------------------------------
_TABLE = {
    1:  ("ajYAta Adeza {word!r}{hint}",
         "unknown command {word!r}{hint}"),
    2:  ("varNa-doSa: {msg}",
         "character/token error: {msg}"),
    3:  ("gaNanA-doSa (vyAkaraNa): {msg}",
         "expression parse error: {msg}"),
    4:  ("gaNanA-doSa (kAla): {msg}",
         "runtime error: {msg}"),
    5:  ("yadi: dvibindu AvazyakaH  (yadi n > 3 : vada bahu)",
         "yadi: ':' is required  (yadi n > 3 : vada bahu)"),
    6:  ("Adeza-tarka riktaH: {cmd!r} ko tarka cAhie",
         "command {cmd!r} needs an argument"),
    7:  ("punaH: saMkhyA AvazyakA — {word!r} milA",
         "punaH: count must be an integer, got {word!r}"),
    8:  ("iti asthAna {msg}",
         "unmatched iti — {msg}"),
    9:  ("iti hInaH {word!r} prabandhaH",
         "missing iti for {word!r} block"),
    10: ("anyathA asthAne — yadi bahire",
         "anyathA outside yadi block"),
    11: ("vidhi-doSa: {msg}",
         "function error: {msg}"),
    12: ("samUha-doSa: {msg}",
         "list error: {msg}"),
    13: ("anukrama-doSa: {msg}",
         "index error: {msg}"),
    99: ("AntarikA-doSa: {msg}",
         "internal error: {msg}"),
}


# ---------------------------------------------------------------------------
# Edit distance (Levenshtein) for did-you-mean
# ---------------------------------------------------------------------------
def _edit_distance(a, b):
    la, lb = len(a), len(b)
    # small optimisation: bail early if lengths differ by more than 2
    if abs(la - lb) > 2:
        return abs(la - lb)
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * lb
        for j, cb in enumerate(b, 1):
            curr[j] = min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            )
        prev = curr
    return prev[lb]


def suggest(word, candidates, max_dist=2):
    """Return ' (did you mean: X?)' if a candidate is within max_dist, else ''."""
    best, best_d = None, max_dist + 1
    for c in candidates:
        d = _edit_distance(word.lower(), c.lower())
        if d < best_d:
            best, best_d = c, d
    return f" (did you mean: {best}?)" if best is not None else ""


# ---------------------------------------------------------------------------
# DosA exception
# ---------------------------------------------------------------------------
class DosA(Exception):
    """The single exception that the REPL and script runner catch and display."""

    def __init__(self, code, line=None, **kw):
        self.code = code
        self.line = line
        self.kw = kw
        super().__init__(str(self))

    def __str__(self):
        sk_tmpl, en_tmpl = _TABLE.get(self.code, ("doSa", "error"))
        try:
            sk = sk_tmpl.format_map(self.kw)
            en = en_tmpl.format_map(self.kw)
        except (KeyError, ValueError) as exc:
            sk = en = f"(formatting error: {exc})"
        pos = f" [pankti {self.line}]" if self.line else ""
        return f"doSa-{self.code:03d}{pos}: {sk} — {en}"


def raise_dosa(code, line=None, **kw):
    """Build and immediately raise a DosA."""
    raise DosA(code, line=line, **kw)
