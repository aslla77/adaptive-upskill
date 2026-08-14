---
name: upskill-status
description: >
  Show where an adaptive-upskill learner stands: mastery per concept with evidence counts, the next recommended module and why, what was skipped, and what is locked. Use when the learner asks about progress, status, how am I doing.
license: MIT
metadata:
  framework_version: "0.1.0"
  routes_to: "adaptive-upskill"
allowed-tools: Read Write Edit Glob Grep Bash
---

# upskill-status

This is a routing entry point. It holds no procedure of its own, so it cannot drift
from the main skill.

**Invoke the `adaptive-upskill` skill, then execute **Step 7 (Status)** of its SKILL.md.**

Report the evidence counts alongside the mastery values, and mark `assumed-ok`
concepts as inferred rather than measured. Do not teach anything from here.

If `.upskill/` holds no workspace, do not start a diagnostic from here — say what was
not found and offer `/adaptive-upskill <topic>` instead.
