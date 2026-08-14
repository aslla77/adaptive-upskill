# 04 — Archetype B: concept / model

Mathematics, physics, statistics, machine learning, RAG, algorithms, system design.

**Mastery means: it transfers.** They can apply it to a situation that was not in the
material, and they know when it stops applying.

Reciting a definition is worth almost nothing here. The whole archetype is built around
not being fooled by fluent recall.

## What the map looks like

The prerequisite graph is the strictest of the three archetypes and it is genuinely
hierarchical. Skipping a layer here does not slow someone down, it makes the next layer
memorisation instead of understanding.

Because of that, the prerequisite gate matters more. Do not soften it. If the parent is
weak, the child is locked, even when the learner insists they are fine.

Cut by depth, not by breadth: keep the whole chain from their current floor to the goal,
and drop the branches the goal does not need.

## Evidence types, best first

| Type | Scoring | Use for |
|---|---|---|
| Numeric or symbolic problem with one answer | deterministic — `correct` | The cheapest real evidence. Use wherever the subject allows |
| "Condition X changes — what happens and why?" | rubric | **The transfer item.** The core of this archetype |
| Find the counterexample / say where the assumption breaks | rubric | Separates understanding from pattern-matching |
| Spot the flaw in a plausible-looking derivation | rubric, sometimes deterministic | Excellent at level 3 |
| Choose between methods for a constrained scenario | rubric | Level 3–4 |

More rubric scoring here than in archetype A. That is unavoidable, so control it:
write the rubric **before** seeing the answer, and grade with the `rubric-grader`
subagent so the grader does not know the learner's history.

## Item levels

- **L1** — state the idea in their own words with one valid example and one non-example
- **L2** — apply it to a routine case; compare two related ideas on stated criteria
- **L3** — predict what breaks when a condition changes; produce a counterexample
- **L4** — combine several ideas to design a solution and defend it against an alternative

## The transfer requirement

A concept in archetype B cannot be called `advanced` on routine problems alone. Before
declaring mastery, ask at least one **L3 transfer item** — a situation the learner has
not seen. The scripts already require `max_direct_level >= 3` for `advanced`; this is
the pedagogical reason.

## Lessons

Lead with the smallest useful model, not the history and not the full formalism. Then:

- one worked example with the reasoning shown, not just the result
- one **non**-example, and why it fails
- retrieval: reconstruct the key step without looking
- application: a scenario that changes one condition

Diagrams earn their place when a relationship is structural or spatial. Skip them
otherwise.

## Checkpoints

Mix one routine item with one transfer item. Passing the routine one alone is
`proficient`, not `advanced`. Say that to the learner rather than quietly capping it.

## Failure handling

Two failure modes look identical and need opposite responses:

- **Missing prerequisite** — they cannot follow the derivation at all. Go down the graph.
- **Misconception** — they follow it confidently and get it wrong the same way twice.
  Re-explaining does nothing. Give them the counterexample that contradicts their model
  and let them find the contradiction themselves.

Distinguish them by asking the learner to explain their reasoning before you correct it.

## Honesty

Never present a rubric score as a measurement. It is your judgement against criteria you
wrote. When a learner asks how confident the number is, say that it comes from a small
number of items and is meant to order the plan, not to certify anything.
