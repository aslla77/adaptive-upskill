# 09 — State contract

Conversation history is not storage. Claude Code re-attaches only the first 5,000 tokens
of a skill after auto-compaction, inside a 25,000-token budget shared across skills, so a
long tutoring session **will** lose parts of this file and of what was said. The files
below are what survives.

## Layout

```
<CWD>/.upskill/<subject>/
├── competency.json     concept map + goal + archetype   (edit via init)
├── evidence.json       append-only records              (SOURCE OF TRUTH)
├── progress.json       derived mastery + profile        (regenerated)
├── plan.json           current plan                     (regenerated)
├── items/              authored items incl. answer keys
└── lessons/            lesson markdown
```

Root resolution order: `--root` → `$UPSKILL_ROOT` → `./.upskill`.

**Evidence is the only irreplaceable file.** `progress.json` and `plan.json` are
recomputed from it on every command. If they disagree with evidence, evidence wins.

## Why the workspace is not inside the skill

The skill directory is a read-only package, and in this project it is a symlink into a
git repo. Writing learner data there would commit it and force every subject to share
one state. See ADR-0001 in the project.

The cost: learning continues only from the directory it started in. That is why Step 0
must announce the workspace path and must never restart silently.

## Records

```json
{"item_id":"py-collections-l2-001","concept":"py-collections","level":2,
 "answer_mode":"deterministic","score":0.0,"source":"direct",
 "disputed":false,"timestamp":"2026-08-15T09:04:00Z"}
```

`source` is one of:

| source | weight | meaning |
|---|---|---|
| `direct` | 1.0 | asked during the diagnostic |
| `checkpoint` | 1.0 | earned at the end of a lesson |
| `review` | 1.0 | spaced retrieval; required for `advanced` in archetype C |
| `implied` | 0.5 | never written by you — derived at read time from surmise |

Implied records are computed on every read, never stored, and are **skipped for any
concept that has direct evidence**. Direct measurement always wins over inference.

## Status values

| status | meaning |
|---|---|
| `unknown` | no evidence at all |
| `assumed-ok` | only implied evidence — a guess worth acting on, not a skill shown |
| `foundation` | < 0.45 |
| `developing` | 0.45–0.69 |
| `proficient` | 0.70–0.84, or higher without direct level-3 evidence |
| `advanced` | ≥ 0.85 with direct level-3+ evidence (plus review evidence for archetype C) |

## Editing rules

- Never hand-edit `evidence.json` to change a score. Use `dispute` — the record stays
  with weight 0 and a reason, so the history remains readable.
- Never write `progress.json` or `plan.json` yourself. Run the command.
- Renaming a concept `id` orphans its evidence. Add a new concept instead.
- `init` refuses to overwrite an existing map. Before ever passing `--force`, tell the
  learner exactly what is lost and get a yes. The same applies to deleting a workspace:
  say what disappears, then wait.

## When a file is broken

Validation failure is not a reason to regenerate. **Do not overwrite the file.**

1. Report which file and which check failed.
2. Copy it aside: `cp evidence.json evidence.json.bak-<date>`.
3. Show the learner the offending part and ask.

A corrupted `progress.json` is harmless — delete it and run any command to rebuild.
A corrupted `evidence.json` is real loss; treat it that way.

## Portability

Everything here is plain JSON with no vendor fields. Another agent — or a future
version of this skill — can read `evidence.json` and reproduce every number, because the
scoring rules are in code, not in a conversation. That is the point of the split.

## Permissions

Each `allowed-tools` grant expires when the learner sends their next message, so a
multi-turn session re-prompts for Bash. Add an allow rule once, in the project's
`.claude/settings.json`:

```json
{"permissions": {"allow": ["Bash(python3 *upskill*.py *)"]}}
```
