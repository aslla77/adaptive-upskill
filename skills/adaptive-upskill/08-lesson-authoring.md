# 08 — Lesson authoring

## The shape is fixed

```
explain → retrieval → application → checkpoint
```

Retrieval before application, both before the checkpoint. Testing during learning
improves later retention more than re-reading does (Roediger & Karpicke, 2006), so
re-explaining is the **failure path**, not the default one.

One module per session. Do not run down the plan.

## Sections

**Objectives** — two or three, each an observable behaviour. Lift them from the
concept's `can_do`.

**Why this matters** — two sentences tying it to *their* goal, from the concept's `why`.
Not a general argument for the topic.

**Prerequisite check** — one quick question on the parent concept. If the parent is
`assumed-ok`, this is the moment it gets measured directly. If they miss it, stop the
lesson and go up the graph; that is cheaper than teaching on sand.

**Mental model** — the smallest useful version. Concrete relationships, one example, one
non-example. No history, no terminology that is not needed in the next paragraph.

**Worked example** — show the reasoning, not only the result. For archetype A, code that
actually runs.

**Retrieval** — close the material. Reconstruct the key step from memory. This is not
optional and it is not the same as the application step.

**Application** — a genuinely different problem. Not the worked example with the numbers
changed. If a learner can pattern-match their way through it, it is not application.

**Checkpoint** — see below.

## Hint ladder

Offer hints one rung at a time, only when asked, and never volunteer the next rung:

1. Point at where to look — "which line runs first?"
2. Name the relevant idea without applying it
3. Show the structure with the key step blank
4. Full solution, then ask them to explain why it works

Jumping to rung 4 feels helpful and destroys the evidence.

## Checkpoint

Different problem from the worked example. Deterministic if the subject allows.
Archetype B needs one transfer item before `advanced` is possible; archetype C needs the
review schedule, not a single pass.

Record it:

```bash
python3 $SCRIPTS/upskill.py update --subject <s> --responses <r.json>
```

Then read the output back to the learner: which concepts moved, from what to what. If it
says to re-plan, re-plan and explain **what changed and why**.

## When the checkpoint fails

Do not repeat the explanation. It already did not work.

1. **Check the prerequisite first**, especially anything at `assumed-ok`.
2. Ask them to explain their reasoning before correcting. Missing prerequisite and
   misconception look identical from the outside and need opposite responses.
3. Switch representation: worked example → non-example, prose → diagram, abstract →
   concrete instance.
4. On a second failure, drop to the prerequisite concept properly. Stop trying to teach
   the current one.

## When it passes suspiciously easily

If they say they already knew the answer, or the answer arrives instantly with no
working, add one application item. Lucky success and repeated success have to be
distinguished before mastery is recorded, and one item is a cheap way to do it.

## Saving

`.upskill/<subject>/lessons/<concept>-<n>.md` with frontmatter:

```yaml
---
concept: py-collections
module_kind: foundation
plan_version: 3
created: 2026-08-15T09:20:00Z
---
```

Markdown is the source of truth. HTML is only ever a rendering of these files plus
`progress.json` — never a place where state lives.

## Length

Shorter than feels right. A lesson the learner reads and forgets is worth less than a
short one they answered questions inside of. If the explanation is longer than the
practice, rebalance it.
