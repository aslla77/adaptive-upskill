#!/usr/bin/env python3
"""Thin alias: `score_diagnostic.py ...` == `upskill.py score ...`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import upskill  # noqa: E402

if __name__ == "__main__":
    sys.exit(upskill.main(["score"] + sys.argv[1:]))
