#!/usr/bin/env python3
"""Thin alias: `update_mastery.py ...` == `upskill.py update ...`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import upskill  # noqa: E402

if __name__ == "__main__":
    sys.exit(upskill.main(["update"] + sys.argv[1:]))
