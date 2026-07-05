#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thin back-compat shim — the real interpreter lives in the adesha/ package.

    python adesha.py               # interactive shell (REPL)
    python adesha.py file.adesha   # run a script

(The adesha/ package directory shadows this file for `import adesha`,
so this shim is reachable only as a script — exactly what we want.)
"""

from adesha.interp import main

if __name__ == "__main__":
    main()
