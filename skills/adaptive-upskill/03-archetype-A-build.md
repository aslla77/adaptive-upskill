# 03 — Archetype A: tool / build

Python, C, SQL, Flutter, Git, shell, an API, a framework.

**Mastery means: they can make the thing work, unaided.** Not that they can describe it.

## What the map looks like

The prerequisite graph is real and mostly linear at the bottom, branching at the top.
Order the bottom by what breaks first without it: syntax → data structures → structuring
code → error handling → I/O and environment.

Bias `goal_relevance` hard toward the artifact. If the goal is "merge CSVs into Excel",
file I/O and encoding sit at 1.5 and classes sit at 0.5 or are absent. Cutting is the
main way this archetype gets personalised.

## Evidence types, best first

| Type | Scoring | Use for |
|---|---|---|
| Make failing tests pass | deterministic — `passed`/`total` | The strongest evidence available. Prefer it |
| Predict the output of a snippet | deterministic — `correct` | Fast, discriminating, cheap to author |
| Find and fix the bug | deterministic if tests exist | Best single discriminator between "read tutorials" and "can build" |
| Choose between two implementations and justify | rubric | Only at level 3+ |

Aim for **at least 3 of 4 items scored deterministically**. This archetype has the least
excuse for rubric scoring.

## Item levels

- **L1** — read code and say what it does
- **L2** — write or repair a few lines against a stated behaviour
- **L3** — diagnose something that looks correct but is not; explain the root cause
- **L4** — design under a constraint (performance, failure handling) and defend the choice

## The practical task

Every archetype-A diagnostic includes exactly one runnable task. Write it to
`.upskill/<subject>/items/<id>/` with the broken source plus tests, tell the learner the
path, and let them use their editor.

Score with `passed`/`total`. Attach it to a second concept with `also` when the task
genuinely exercises one — a CSV-encoding fix is evidence for both file I/O and error
handling. Do not stretch this; two concepts per task is the limit.

Showing the tests before they solve is fine. Knowing the acceptance criteria is normal
engineering, not cheating.

## Lessons

Explain in code. A worked example that runs beats three paragraphs. Hint ladders go
from "which line would you check first" to "here is the failing call" to "here is the
fix, explain why it works".

The application step must be a **different** problem, not the worked example with the
numbers changed.

## Checkpoints

Prefer a small runnable task over questions. If it runs and the tests pass, that is
mastery evidence and it needs no rubric.

## Failure handling

When a checkpoint fails, the cause is usually one level down: a data-structure gap
masquerading as a file-handling problem. Check whether the prerequisite is `assumed-ok`
— if it was never measured directly, measure it before re-teaching.

## Common mapping mistakes

- Mapping the language's feature list instead of the goal's needs. Decorators and
  metaclasses do not belong in a CSV-automation map.
- Treating "install and run" as trivial. For a beginner, environment and packaging is a
  real concept and a common wall. Give it a node.
- One giant "basics" concept. It cannot be diagnosed or skipped; split it.
