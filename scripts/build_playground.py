#!/usr/bin/env python3
"""Build the static Ādeśa playground by copying source files and keyword registry."""

from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PLAYGROUND = ROOT / "playground"
PY_DIR = PLAYGROUND / "py"
SRC_FILES = [
    ROOT / "aos_asm.py",
]
SRC_DIRS = [
    ROOT / "adesha",
]


def is_devanagari(text: str) -> bool:
    return any("\u0900" <= ch <= "\u097f" for ch in text)


def is_hk_canonical(text: str) -> bool:
    """Heuristic: canonical HK keyword uses uppercase ASCII letters."""
    return any("A" <= ch <= "Z" for ch in text) and not is_devanagari(text)


def collect_keywords():
    from adesha.interp import COMMANDS, BLOCK_COMMANDS

    groups: dict[int, list[str]] = defaultdict(list)
    for registry in (COMMANDS, BLOCK_COMMANDS):
        for name, fn in registry.items():
            groups[id(fn)].append(name)

    keywords: dict[str, list[str]] = {}
    for names in groups.values():
        dev = next((n for n in names if is_devanagari(n)), None)
        hk = next((n for n in names if is_hk_canonical(n)), None)
        if hk is None:
            hk = next(
                (n for n in names if not is_devanagari(n)),
                names[0] if names else "",
            )
        aliases = sorted(set(names))
        keywords[hk] = aliases
        # Sanity check: every group should expose at least Devanagari + HK.
        if dev is None:
            print(f"  warning: {hk} has no Devanagari alias")

    return keywords


def copy_python_sources() -> None:
    if PY_DIR.exists():
        shutil.rmtree(PY_DIR)
    PY_DIR.mkdir(parents=True)

    for src_dir in SRC_DIRS:
        dest = PY_DIR / src_dir.name
        shutil.copytree(
            src_dir,
            dest,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
        )

    for src_file in SRC_FILES:
        shutil.copy2(src_file, PY_DIR / src_file.name)


def main() -> int:
    print("Copying Python sources into playground/py/ ...")
    copy_python_sources()

    print("Generating playground/keywords.json ...")
    keywords = collect_keywords()
    with open(PLAYGROUND / "keywords.json", "w", encoding="utf-8") as f:
        json.dump(keywords, f, ensure_ascii=False, indent=2)

    count = len(keywords)
    aliases = sum(len(v) for v in keywords.values())
    print(f"  {count} keyword groups, {aliases} total aliases")

    print("Build complete: playground/ is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
