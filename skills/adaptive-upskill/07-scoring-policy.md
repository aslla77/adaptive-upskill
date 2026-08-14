# 07 — Scoring policy

The boundary this file draws is the reason the project exists. Cross it and the system
becomes a chatbot with extra JSON.

## What you may do

- Decide **what happened**: the choice matched the key or it did not; 2 of 3 tests
  passed; the answer earned 3 of 4 rubric points.
- Report that to the script.

## What you may never do

- Produce a mastery value.
- Decide a concept is mastered, or weak, or ready.
- Decide the diagnostic has gone on long enough.
- Decide what to teach next.
- Recompute anything the script computes, even when a script fails. **If a script errors,
  report the error.** A fallback estimate is worse than no number, because it looks the
  same as a real one.

## Choosing the mode

Use `deterministic` whenever the answer can be checked without judgement:

- multiple choice against a key
- exact numeric answer, or numeric within a stated tolerance
- code that makes a test suite pass
- an exact string or structured value

Use `rubric` only when it genuinely cannot be:

- explanation in the learner's own words
- justifying a design or method choice
- free production in a natural language

If you are unsure, it is deterministic. Rewrite the item until it can be.

## Response format

Report one object per item. The script normalises to 0–1.

```json
{"responses": [
  {"item_id":"q1","concept":"py-syntax","level":1,"answer_mode":"deterministic","correct":true},
  {"item_id":"q5","concept":"py-files-io","level":2,"answer_mode":"deterministic",
   "passed":2,"total":3,"also":[{"concept":"py-errors","level":2}]},
  {"item_id":"q6","concept":"rag-chunking","level":3,"answer_mode":"rubric",
   "rubric_points":3,"max_points":4,"note":"missed the recall/precision tradeoff"}
]}
```

Report exactly one of `correct`, `passed`+`total`, or `rubric_points`+`max_points`.
Passing a raw `score` is possible but discouraged — it hides how the number was reached.

## Rubric grading

1. The rubric is written **when the item is written**, before any answer exists.
2. Grade against the criteria only. Not against the learner's history, not against how
   articulate they sound, not against how hard they seem to be trying.
3. Prefer the `rubric-grader` subagent: give it the rubric and the answer, nothing else.
   A grader that does not know the learner cannot drift toward them.
4. Put what was missing in `note`. It becomes the lesson's starting point.
5. Partial credit is normal. Do not round up out of kindness — a softened score buys a
   lesson they did not need and skips one they did.

## Partial scores are ambiguous, and that is useful

A single item scoring between 0.3 and 0.7 does not resolve a concept; the script will
ask one more. Do not "fix" this by rounding to 0 or 1.

## Confidence

Collected, never scored. Its only job is to surface the confident-and-wrong case, which
is worth naming to the learner because it is the hardest gap to notice alone.

## Talking about the numbers

When reporting mastery, say what it came from: how many items, at what level, how much
of it was implied rather than measured. `assumed-ok` means "we skipped asking because a
harder item implied it" — say that in words, not just as a label.

Never describe a threshold or a mastery value as a validated measurement. They are
configuration defaults chosen to order a plan.
