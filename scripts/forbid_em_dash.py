#!/usr/bin/env python3
"""Fail if any em-dash (U+2014) or en-dash (U+2013) is found in the given files.

Used by the .pre-commit-config.yaml `no-em-or-en-dash` hook and by CI lint.
"""
from __future__ import annotations

import sys

EM_DASH = chr(0x2014)  # avoid literal characters; pre-commit hook would self-trip
EN_DASH = chr(0x2013)


def main(paths: list[str]) -> int:
    hits = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                for line_no, line in enumerate(fh, 1):
                    if EM_DASH in line or EN_DASH in line:
                        hits.append((path, line_no, line.rstrip("\n")))
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
    for path, line_no, line in hits:
        print(f"{path}:{line_no}: em/en dash found: {line!r}")
    if hits:
        print(
            f"\nFAIL: {len(hits)} line(s) contain em ({EM_DASH}) or en ({EN_DASH}) dashes. "
            "Use periods, commas, parentheses, or colons instead."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
