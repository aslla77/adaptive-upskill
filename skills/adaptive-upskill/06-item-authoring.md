# 06 — Item authoring

## Keep the answer key out of this conversation

If you write the answer key in the main conversation, the learner sees it right before
answering. Tool calls are visible; there is no hiding them.

**Author items with a subagent.** Dispatch a general-purpose subagent with instructions
to write the items file and return only a count:

> Write N diagnostic items for `<subject>` covering `<concepts>` at `<levels>`, using
> the item schema in this message. Save to `.upskill/<subject>/items/<set-id>.json`.
> Then output only: the item IDs, their concepts, their levels, and the question text —
> **never the answers, keys, tests, or rubrics.**

Then read only the question text back and present it. The keys stay on disk.

Fallbacks, in order, if subagents are unavailable:

1. Author the **whole set at once** before asking anything, so keys scroll away.
2. As a last resort, tell the learner the keys are about to appear and ask them not to
   read the tool output. Do not pretend this is airtight.

Runnable tests for archetype A are an exception — showing them is fine and useful.

## Item schema

```json
{
  "id": "py-collections-l2-001",
  "concept": "py-collections",
  "level": 2,
  "answer_mode": "deterministic",
  "prompt": "…what the learner sees…",
  "choices": ["…"],
  "answer": "b",
  "rationale": "why b is right and why each distractor is wrong",
  "max_points": null,
  "rubric": null,
  "also": [{"concept": "py-errors", "level": 2}]
}
```

- `answer_mode` — `deterministic` or `rubric`. See `07-scoring-policy.md`.
- `rationale` — **required.** If you cannot write why each distractor is wrong, the item
  is not ready. This is also what you show when a learner disputes the item.
- `rubric` — for `rubric` items only: criteria with points, summing to `max_points`.
  Write it **before** seeing any answer.
- `also` — a second concept the item legitimately exercises. At most one.

## Level definitions

| Level | The learner must |
|---|---|
| 1 | Recognise or recall in a form they have seen |
| 2 | Apply it to a routine case |
| 3 | Handle something that looks right but is not, or where a condition changed |
| 4 | Design under a constraint and defend it against an alternative |

Level drives weight (1.00 / 1.20 / 1.50 / 1.80) and gates `advanced`, which needs direct
level-3+ evidence. Do not inflate levels to move numbers.

## Writing good distractors

Every wrong choice must be **the answer to a specific misconception**, not filler. A
learner who picks it should have told you something. If you cannot name the
misconception a distractor catches, replace it.

Avoid: "all of the above", "none of the above", one choice noticeably longer than the
rest, and negation stacking.

## The opening set

Five scored items, covering the highest-`goal_relevance` concepts:

- 1 easy (L1), 2 middle (L2), 1 hard (L3) — calibration
- 1 practical task, whose form comes from `execution_environment`, not from the archetype
  (`11-execution-environments.md`): `none` -> production or transfer answered in chat;
  `local` -> files plus tests; `notebook`/`colab` -> a generated notebook whose
  `UPSKILL_RESULT` line is fed to `upskill.py ingest`

Attach a confidence prompt to each. **Confidence is context, never a score input.** Its
use is to spot the dangerous quadrant — confident and wrong — and mention it to the
learner.

Do not exceed the opening set on your own initiative. After it, the script tells you
what to ask next, one item at a time.

## Follow-up items

`score` returns `NEXT PROBE -> concept=X level=N`. Author exactly one item, for that
concept, at that level. Not two. Not a different concept you think is more interesting.

The level is chosen deliberately: after a failure it probes lower to find the floor,
after a success it probes higher to find the ceiling.

## Checkpoint and review items

- **Checkpoint** — must be a different problem from the lesson's worked example, not a
  reskin. Prefer deterministic.
- **Review** — must require retrieval. Producing the answer, not recognising it among
  choices.

## Disputes

When a learner argues an item is wrong, show the `rationale`. If they are right, or it
is genuinely ambiguous:

```bash
python3 $SCRIPTS/upskill.py dispute --subject <s> --item <item-id> --reason "…"
```

The record stays in the file with weight 0. Then author a replacement. Never quietly
delete evidence.
