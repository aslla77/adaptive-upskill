# 13 — Prefetching the next lesson

Authoring a lesson takes long enough that the learner sits watching a spinner between
modules. That gap is the worst moment to introduce a wait: they have just finished
something and their attention is available.

So the next lesson is written **while they are working on the current one**.

```
deliver lesson 1  ->  dispatch background author for lesson 2
learner works on 1
learner finishes 1  ->  take lesson 2 (already there)  ->  dispatch author for lesson 3
```

## The loop

**Right after you hand the learner a lesson**, before they start answering:

```bash
python3 $SCRIPTS/upskill.py prefetch status --subject <s>
```

It prints the current module, what to build ahead, and whether anything is needed. If it
says `SHOULD BUILD`, claim the slot and dispatch a background subagent:

```bash
python3 $SCRIPTS/upskill.py prefetch claim --subject <s> --concept <next-concept>
```

The subagent authors the lesson exactly as `08-lesson-authoring.md` describes, writes it
(`render_lesson.py` for `html`, a markdown file for `chat`), and finishes with:

```bash
python3 $SCRIPTS/upskill.py prefetch ready --subject <s> --concept <c> \
  --lesson-id <id> --path <file>
```

**When the learner finishes the current module** — after `update`, after `plan`:

```bash
python3 $SCRIPTS/upskill.py prefetch take --subject <s>
```

- `HIT` — the file is ready. Deliver it immediately, then start the next prefetch.
- `MISS` — build it now, in the foreground, and tell the learner nothing about it.

Order matters: `update` → `plan` → `take`. Taking before the plan is regenerated will
report `not_yet`, because the module they just finished is still first.

## What the background author must not do

It writes **one lesson file** and calls `prefetch ready`. Nothing else.

It must never run `score`, `update`, `ingest`, or `plan`. Those rewrite `progress.json`
while the foreground session is also using it, and the learner's evidence is the one file
in this system that cannot be regenerated.

Give it everything it needs in the prompt — concept, `can_do`, `why`, module kind, exit
criterion, archetype, presentation, current mastery — so it never needs to read state.

## Depth is one. Not two, not three.

Only the next module is prefetched. A failed checkpoint re-orders the plan, so anything
built beyond the next module usually gets thrown away, and a discarded lesson costs the
full price of writing it. One deep covers the common case at the lowest waste.

## Misses, and which ones cost anything

| Reason | Meaning | Kept? |
|---|---|---|
| `empty` | nothing prefetched yet | — |
| `building` | still being written; wait or build in the foreground | yes |
| `not_yet` | the lesson is further down the plan, not next | **yes** |
| `stale_plan` | same concept, different treatment now (foundation vs remediation) | no |
| `wrong_concept` | the concept left the plan — mastered, skipped or newly locked | no |

`not_yet` and `building` never discard. Only a lesson that can no longer be taught as
written is thrown away.

## Watching whether it is worth it

`prefetch status` reports running counts:

```
stats: {"hits": 4, "misses": 1, "discarded": 1}
```

A discard is a lesson written and never used — real tokens for nothing. If discards
approach hits, prefetching is losing money on this subject: checkpoints are re-ordering
the plan too often. Say so and stop prefetching for that learner rather than quietly
burning tokens.

## When not to prefetch

- **During the diagnostic.** The plan does not exist yet; there is nothing to build.
- **When the plan has one module left.** `build ahead` returns nothing.
- **When the learner is about to stop.** A lesson prefetched at the end of a session is
  thrown away if the plan moves before they return.
- **When the current module is a `diagnose` kind.** Its outcome decides what comes next,
  so anything built ahead is a coin flip.
