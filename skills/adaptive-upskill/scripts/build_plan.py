#!/usr/bin/env python3
"""Thin alias: `build_plan.py ...` == `upskill.py plan ...`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import upskill  # noqa: E402

if __name__ == "__main__":
    sys.exit(upskill.main(["plan"] + sys.argv[1:]))
