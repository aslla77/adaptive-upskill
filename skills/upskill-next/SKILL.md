---
name: upskill-next
description: >
  Teach the next lesson in an existing adaptive-upskill study plan: one module, explain then retrieval then application then checkpoint, and record the result. Use when the learner says continue, next lesson, keep going.
license: MIT
metadata:
  framework_version: "0.1.0"
  routes_to: "adaptive-upskill"
allowed-tools: Read Write Edit Glob Grep Bash
---

# upskill-next

This is a routing entry point. It holds no procedure of its own, so it cannot drift
from the main skill.

**Invoke the `adaptive-upskill` skill, then execute **Step 6 (Teach one lesson)** of its SKILL.md.**

Read `08-lesson-authoring.md` before writing the lesson. Teach exactly one module -
the first unlocked entry in `plan.json` - then stop and record the checkpoint.

If `.upskill/` holds no workspace, do not start a diagnostic from here — say what was
not found and offer `/adaptive-upskill <topic>` instead.
