# 02 — Competency mapping

The map is the foundation. Everything downstream — what gets asked, what gets locked,
what gets skipped — is computed from it. A wrong map produces confident nonsense, so it
is confirmed with the learner before a single question is asked.

## Size

**4 to 7 concepts.** Not more.

Fewer than 4 and the plan cannot distinguish anything. More than 7 and the diagnostic
cannot cover it in the item budget, so most concepts stay `unknown` and the plan is
guesswork wearing a table.

If the subject genuinely needs more, cut by goal: map only what the stated goal touches,
and tell the learner what you cut.

## Each concept needs

```json
{
  "id": "py-collections",
  "label": "Tabular data with lists and dicts",
  "can_do": "Read a CSV row into a list and total it by department name as the key",
  "why": "'totals by department' is exactly this operation",
  "importance": 1.3,
  "goal_relevance": 1.3,
  "prerequisites": ["py-syntax"],
  "estimated_minutes": 60
}
```

- `id` — stable, lowercase, hyphenated, prefixed by subject.
- `label` — what a learner would call it.
- `can_do` - **an observable behaviour**, not a topic. "Knows about lists" is wrong;
  "Reads a CSV row into a list and totals it" is right. If you cannot write a question
  that checks it, rewrite it.
- `why` — tied to *their* goal, in their words where possible. This text is what makes
  the plan auditable later.
- `importance` — how central to the subject. `0.5`–`1.5`.
- `goal_relevance` — how central to **this learner's** stated goal. `0.5`–`1.5`.
  This is the field that makes two learners of the same subject get different plans.
  Use the range. If everything is 1.0 you have not personalised anything.
- `prerequisites` — direct parents only; the scripts compute transitivity. No cycles.
- `estimated_minutes` — first-time learning cost, ignoring what they already know.

## Prerequisite edges

Add an edge only when the child is genuinely unlearnable without the parent. Every edge
you add can lock a module, and a wrongly locked module wastes hours.

Test each edge: *"Could someone do the child's `can_do` while failing the parent's?"*
If yes, there is no edge.

The graph must be acyclic — `init` rejects cycles.

## Presenting it

Never show raw IDs. For each concept:

```
2. Tabular data with lists and dicts
   You will be able to - read a CSV row into a list and total it by department
   Why it matters - "totals by department" is exactly this operation
   Requires: 1 - about 60 min
```

Then a plain-text dependency sketch, the total estimate, and the same estimate divided
by their weekly budget. Close with:

> Does this map look right? Anything missing, anything you already know, anything to drop?

Act on the answer. "I already know that" does **not** raise mastery - it lowers
`goal_relevance` or removes the concept. Self-report changes scope, never score.

## Writing it

Write the JSON to a temp file and run `init`. Include the top-level `subject`,
`subject_label`, `archetype`, and `goal` fields. `init` validates ranges, unknown
prerequisite IDs, duplicate IDs, and cycles, and refuses to overwrite an existing map
without `--force`.

## Revising later

The map is not frozen. Revise when a checkpoint keeps failing for a reason the map does
not explain, or when the goal changes. Revise it deliberately: say what changed and that
existing evidence stays attached to concept IDs, so **renaming an ID discards its
evidence**. Add a new concept instead of renaming one that carries history.
