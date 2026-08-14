# 05 — Archetype C: language acquisition

English, Japanese, Korean, any human language.

**Mastery means: fast and accurate production, still there next week.** Getting a word
right once is not knowing it.

This archetype breaks two assumptions the other two rely on, so read this before mapping.

## What is different

| | A / B | **C** |
|---|---|---|
| Answering correctly once | usually counts | **does not count** |
| Structure | prerequisite DAG | **grid × spiral** |
| Time since last evidence | mostly irrelevant | **part of the measurement** |

The scripts enforce the first row: with archetype `C`, no concept reaches `advanced`
without at least one `review` evidence record. Do not try to route around it.

## Mapping: grid, not chain

A strict prerequisite chain is the wrong shape. Grammar is learned in loops, not in
order. Build the map as a small grid instead:

- **Axis 1 — level band** the learner is working in (one band at a time)
- **Axis 2 — skill** the goal actually needs: reading, listening, writing, speaking

Then make each concept a *usable competence*, not a grammar label:

- Bad: `ja-te-form`
- Good: `ja-request-polite` - "can make a polite request and decline politely"

Use prerequisites sparingly, only where one competence is literally contained in
another. Weight by the goal instead: a learner who needs business email gets writing at
`goal_relevance` 1.5 and speaking at 0.5.

**Spiral, do not gate.** The same competence returns at a higher band later as a new
concept, rather than being marked done.

## Evidence types

| Type | Scoring | Notes |
|---|---|---|
| Cloze / transformation / correct-the-error | deterministic — `correct` | Use heavily; cheap and reproducible |
| Comprehension question over a short passage | deterministic | Good for reading and listening |
| Translate a specific sentence with a target structure | rubric | Constrain it so the rubric is checkable |
| Produce a short message for a real scenario | rubric | The goal-relevant evidence for a writing goal |

Speaking cannot be measured here. Say so rather than approximating it with written
answers.

## Item levels

- **L1** — recognise: choose the correct form
- **L2** — produce in a scaffolded slot: fill it in, transform it
- **L3** — produce freely for a scenario, with register and politeness correct
- **L4** — produce under a real constraint: length limit, awkward situation, register shift

## Review is the engine, not an extra

Run `upskill.py review --subject <s>` at the start of every session, before teaching
anything new. Items are due on the Leitner schedule (1, 3, 7, 14, 30 days), advancing on
success and resetting to box 0 on failure.

Record with `--review`:

```bash
python3 $SCRIPTS/upskill.py update --subject <s> --responses <r.json> --review
```

A review item must be **retrieval**, not recognition. Ask them to produce the form, not
to pick it from a list.

## Lessons

Keep exposure and production close together. Short input, immediate use, correction,
use again. Long grammar explanations are the failure mode of this archetype.

Correct in this order: meaning first, then form, then naturalness. Correcting naturalness
in a sentence that does not yet mean the right thing wastes both of you.

## Honesty

- Say plainly that this archetype's mastery numbers depend on review history, and that
  a long gap makes them stale rather than wrong.
- Do not report a level-band claim ("N3", "B1") as measured. These maps are not
  calibrated against any framework's descriptors. Say what the learner did, not what
  certificate it resembles.
- Speaking and listening evidence is weak-to-absent in this environment. State that
  limitation when presenting a plan for a speaking goal.
