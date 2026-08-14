#!/usr/bin/env python3
"""Thin alias: `schedule_review.py ...` == `upskill.py review ...`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import upskill  # noqa: E402

if __name__ == "__main__":
    sys.exit(upskill.main(["review"] + sys.argv[1:]))
