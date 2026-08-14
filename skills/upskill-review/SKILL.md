---
name: upskill-review
description: >
  Run spaced retrieval practice on adaptive-upskill concepts that are due, then record the results as review evidence. Required for language subjects before any concept can be called mastered. Use when the learner says review, practice, drill.
license: MIT
metadata:
  framework_version: "0.1.0"
  routes_to: "adaptive-upskill"
allowed-tools: Read Write Edit Glob Grep Bash
---

# upskill-review

This is a routing entry point. It holds no procedure of its own, so it cannot drift
from the main skill.

**Invoke the `adaptive-upskill` skill, then execute **Step 8 (Review)** of its SKILL.md.**

Items must require retrieval, not recognition - ask the learner to produce the answer,
not pick it from a list. Record with `--review` so the Leitner box advances.

If `.upskill/` holds no workspace, do not start a diagnostic from here — say what was
not found and offer `/adaptive-upskill <topic>` instead.
