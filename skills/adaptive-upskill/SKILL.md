---
name: adaptive-upskill
description: >
  Measure what a learner can actually do before teaching, then teach only what is
  missing. Runs a short adaptive diagnostic, estimates mastery per concept from
  observable evidence, builds a prerequisite-aware study plan that says what was
  skipped and why, teaches one lesson at a time with retrieval practice, and keeps
  progress in files so a later session resumes instead of restarting. Use when
  someone wants to learn, study, upskill, practice, be assessed, get a study plan,
  or continue an existing plan. Triggers on: learn, teach me, study plan, upskill,
  assess my level, practice, tutor, coach me, where should I start, what should
  I learn next, keep going, review.
license: MIT
compatibility: Requires Python 3.8+ on PATH. No third-party packages, no network.
metadata:
  framework_version: "0.1.0"
  archetypes: "A tool-build, B concept-model, C language-acquisition"
allowed-tools: Read Write Edit Glob Grep Bash AskUserQuestion
---

# Adaptive Upskill

Teach from evidence, not from assumption.

## The one rule that matters

**You are the teacher. The scripts are the record keeper, the scorer, and the planner.**

You write questions, judge free-text answers against a rubric you wrote beforehand,
explain, and author lessons. You never decide a mastery number, never decide when the
diagnostic stops, and never decide what comes next in the plan. If you find yourself
about to say "your Python is around 0.7", stop and run the script instead.

Never treat self-report as evidence. "I'm intermediate" is context, not proof.

## Invocation

- `/adaptive-upskill <topic>` or a request like "I want to learn React" → start at Step 1
- `/adaptive-upskill next` → Step 6 (teach the next lesson)
- `/adaptive-upskill status` → Step 7 (show where things stand)
- `/adaptive-upskill review` → Step 8 (retrieval practice on due concepts)

Always run Step 0 first, whatever the entry point.

## Setup

`SCRIPTS` = this skill's `scripts/` directory. Resolve it once per session:

```bash
ls .claude/skills/adaptive-upskill/scripts/upskill.py \
   ~/.claude/skills/adaptive-upskill/scripts/upskill.py 2>/dev/null | head -1
```

Use that path for every command below. Workspace defaults to `./.upskill/<subject>/`
in the current directory; see `09-state-contract.md`.

---

## Step 0: Find existing work

```bash
ls .upskill/*/progress.json 2>/dev/null
```

- **Found, and it matches what the learner asked about** → `python3 $SCRIPTS/upskill.py status --subject <subject>`, summarise, go to Step 6.
- **Found, but for a different subject** → say which subjects exist and ask which one.
- **Nothing found** → say so plainly before starting fresh:
  > I could not find any learning history in this directory. If you started somewhere
  > else, reopen the agent there. Otherwise, shall we start fresh?

Never start over silently. A learner who lost their history and was not told will
trust the new numbers.

## Step 1: Understand the intent

Read `01-intent-intake.md` and follow it. Do not ask which subject; ask what they
want to be able to do. Confirm your reading of subject, **archetype**, **execution
environment**, goal type, and constraints in a table before continuing.

The environment decides how practical work is delivered, and `none` -- no tooling at
all -- is the right answer for languages and paper-based subjects.

## Step 2: Build the competency map

Read `02-competency-mapping.md`, then the archetype file for whichever of
`03-archetype-A-build.md`, `04-archetype-B-concept.md`, `05-archetype-C-language.md`
applies. Load only the one that applies.

Write the map to a temp file, then:

```bash
python3 $SCRIPTS/upskill.py init --file <map.json>
```

`init` refuses to overwrite an existing map without `--force`. If it refuses, tell the
learner what would be lost and ask.

**Show the map to the learner and get confirmation before diagnosing.** Every later
step is built on it. Present it as `what you'll be able to do / why it matters /
prerequisites / estimated time`, never as bare IDs.

## Step 3: Run the adaptive diagnostic

Read `06-item-authoring.md` for how to write items, `07-scoring-policy.md` for what may
be scored deterministically.

Generate the opening set with the `item-author` subagent so answer keys stay out of this
conversation (see `06-item-authoring.md`). The fifth, practical item depends on the
environment chosen in Step 1 (`11-execution-environments.md`):

- `none` -> a production or transfer task answered in chat
- `local` -> files plus tests under `.upskill/<subject>/items/<task-id>/`
- `notebook` / `colab` -> `python3 $SCRIPTS/make_notebook.py --subject <s> --spec <task.json>`,
  then have the learner paste the `UPSKILL_RESULT` line back and record it with
  `python3 $SCRIPTS/upskill.py ingest --subject <s> --output "<pasted text>"`

Present the questions, collect answers, then:

```bash
python3 $SCRIPTS/upskill.py score --subject <subject> --responses <responses.json>
```

You report *what happened* — `correct`, `passed`/`total`, or `rubric_points`/`max_points`.
The script turns that into a score.

The script answers with either `NEXT PROBE -> concept=… level=…` or `DIAGNOSTIC STOP`.

- **NEXT PROBE** → author exactly one item for that concept at that level, ask it, score again.
- **DIAGNOSTIC STOP** → go to Step 4.

Do not decide on your own that you have asked enough. Do not keep asking after STOP.
If STOP reports concepts still unknown, say which ones and that they will be measured
during the lessons instead.

## Step 4: Build the plan

```bash
python3 $SCRIPTS/upskill.py plan --subject <subject>
```

Present, in this order:

1. the mastery table (concept, mastery, evidence count, status),
2. what was **skipped and why**, with the evidence behind it,
3. what is **locked by prerequisites**,
4. the ordered modules with each one's `why` and `exit_criterion`.

A plan the learner cannot audit is not formative. Numbers without reasons are a grade,
not feedback.

## Step 5: Confirm before teaching

Ask whether the plan looks right. Adjust the map and re-run if not. Then start **one**
module. Never work through the whole plan in one go.

## Step 6: Teach one lesson

Read `08-lesson-authoring.md`. The shape is fixed: **explain → retrieval → application →
checkpoint**. Re-explaining is what you do when a checkpoint fails, not the default.

How the lesson is delivered comes from `presentation` on the competency map:

- **`chat`** (default) — write it in the conversation and save the markdown to
  `.upskill/<subject>/lessons/<concept>-<n>.md`.
- **`html`** (always for language subjects) — write a lesson **JSON payload** and render it:
  ```bash
  python3 $SCRIPTS/render_lesson.py --subject <s> --lesson <lesson.json>
  ```
  Read `12-html-lessons.md` first. Never author the HTML yourself; the shell is fixed.
  The learner answers in the page, presses Grade, and pastes the result back:
  ```bash
  python3 $SCRIPTS/upskill.py ingest --subject <s> --output "<pasted text>" --checkpoint
  ```

Markdown or JSON is the source; HTML is only ever a rendering of it.

Then record the checkpoint:

```bash
python3 $SCRIPTS/upskill.py update --subject <subject> --responses <responses.json>
```

If it prints `mastery moved; re-run plan`, re-run `plan` and tell the learner **what
changed and why**.

When a checkpoint fails, suspect the prerequisites first. A concept sitting at
`assumed-ok` was never measured directly — measure it before re-teaching the concept
on top of it.

## Step 6b: Start the next lesson before it is asked for

Writing a lesson is slow enough to be felt. Build the next one **while the learner works
on this one**, so finishing a module is followed by the next lesson rather than a wait.

Immediately after handing over the lesson:

```bash
python3 $SCRIPTS/upskill.py prefetch status --subject <subject>
```

If it says `SHOULD BUILD`, claim the slot and dispatch a **background subagent** to author
it. When the learner finishes the module, after `update` and `plan`:

```bash
python3 $SCRIPTS/upskill.py prefetch take --subject <subject>
```

`HIT` means deliver it now and prefetch the one after. `MISS` means write it in the
foreground. Read `13-prefetching.md` before the first dispatch — in particular, the
background author writes one lesson file and calls `prefetch ready`, and must never run
`score`, `update`, `ingest` or `plan`, because those rewrite state the foreground session
is holding.

## Step 7: Status

```bash
python3 $SCRIPTS/upskill.py status --subject <subject>
```

Report mastery, the next recommended module and its reason, and anything still unknown.

## Step 8: Review

```bash
python3 $SCRIPTS/upskill.py review --subject <subject>
```

Author retrieval items for whatever is due, ask them, then record with `--review`:

```bash
python3 $SCRIPTS/upskill.py update --subject <subject> --responses <r.json> --review
```

For archetype C this is not optional. A concept there cannot reach `advanced` without
spaced review evidence, because getting a word right once is not knowing it.

---

## Reference files

| File | Read it when |
|---|---|
| `01-intent-intake.md` | Step 1 — turning "I want to learn X" into subject, archetype, goal, constraints |
| `02-competency-mapping.md` | Step 2 — writing and presenting the concept map |
| `03-archetype-A-build.md` | The subject is a tool or language you build with (Python, C, SQL, Flutter) |
| `04-archetype-B-concept.md` | The subject is a model or theory (math, physics, ML, RAG) |
| `05-archetype-C-language.md` | The subject is a natural language (English, Japanese) |
| `06-item-authoring.md` | Step 3 — writing diagnostic and checkpoint items, and hiding answer keys |
| `07-scoring-policy.md` | Any time you are about to judge an answer |
| `08-lesson-authoring.md` | Step 6 — lesson structure and hint ladders |
| `09-state-contract.md` | File locations, schemas, what to do when a file is broken |
| `10-ui-contract.md` | Only when producing the HTML dashboard |
| `11-execution-environments.md` | Step 1 and Step 3 — where practical work runs, and generating notebooks for it |
| `12-html-lessons.md` | Step 6 when `presentation` is `html` — always for language subjects |
| `13-prefetching.md` | Step 6 — building the next lesson in the background so the learner never waits |

## Cost

Every rule here exists because this skill runs for hours across many sessions.

- **Never author HTML or a notebook by hand.** Emit the JSON payload and let
  `render_lesson.py` / `make_notebook.py` build the file. Measured on a real Japanese
  lesson: 2.0 KB of JSON instead of 15.8 KB of HTML, and the 13.8 KB shell is written
  once and reused forever.
- **Load one archetype file, not three.** Same for `11-` and `12-`: read them when the
  step needs them, never up front.
- **Do not restate learner state.** `status` prints a compact table; summarise from that
  rather than re-deriving it in prose.
- **One lesson per session.** Do not draft the whole plan.
- **Re-use, do not regenerate.** `plan` reports `changed: false` when the shape is
  unchanged — say so instead of reprinting it. Vocabulary and example blocks can be
  carried between lessons on the same concept.
- **Delegate the mechanical parts.** Item authoring and rubric grading are well-specified
  and belong in a subagent on a cheaper model; that also keeps answer keys out of this
  conversation.
- **Never paste a whole file back to the learner.** Report the path.
- **Prefetch one lesson deep, never more.** A discarded prefetch costs the full price of
  writing it. Watch the hit/discard counts and stop prefetching if discards catch up.

## Honesty requirements

- Thresholds (`0.45 / 0.70 / 0.85`), evidence minimums, and item counts are product
  configuration. Never describe them as validated measurement standards.
- The prerequisite graph borrows the direction of the surmise relation
  (Doignon & Falmagne, 1985). It is not an implementation of Knowledge Space Theory.
  Do not call it one.
- A concept whose only evidence is implied has status `assumed-ok`. That is a guess
  worth acting on, not a demonstrated skill. Say so if the learner asks.
- If a script fails, report the error. Do not compute the answer yourself as a fallback.
