# adaptive-upskill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Standard-Agent_Skills-blueviolet.svg)](https://agentskills.io/)
[![Works with](https://img.shields.io/badge/Works_with-Claude_Code_|_Codex_|_Cursor_|_Gemini_CLI-blue.svg)](#install)

> **Measure what you can actually do before teaching you anything — and never let the model be the one holding the score.**

Ask an agent to teach you something and it starts at the beginning. It doesn't know what you already know, so it either asks and believes your answer, or it guesses. You spend an hour on material you didn't need, the gap you actually had goes untouched, and when the session ends the whole thing evaporates.

`adaptive-upskill` runs a short diagnostic first, estimates mastery per concept from what you demonstrably did, and builds a plan that says **what it skipped and why**. Progress lives in files, so the next session resumes instead of restarting.

## The line this skill draws

**The model teaches. Scripts keep the score.**

Ask a model "rate my Python 0 to 1" and you get 0.62 today and 0.74 tomorrow. So it never gets asked.

```
model  ->  writes questions, grades free text against a rubric it wrote first,
           explains, authors lessons

script ->  normalises scores, computes mastery, decides when the diagnostic stops,
           enforces prerequisites, orders the plan, writes state
```

Every number comes from `scripts/`, which is plain Python over an append-only evidence file. Same evidence in, same mastery out, forever — delete the derived state and it rebuilds identically.

## What it does

**Starts from intent, not from a subject.** Not "what do you want to learn" but "what do you want to be able to do". The subject, the archetype, and half the curriculum fall out of that answer.

**Adapts its own length.** It opens with five items, then asks for exactly one more wherever the evidence is ambiguous, and stops when it can place you. In the reference fixtures a confident learner is resolved in 6 items, a mixed one in 7. The stopping decision is computed, never a judgement call.

**Skips what you can already do, and shows its work.** Every module carries the reason it is there. Every skipped module carries the evidence behind skipping it. A plan you cannot audit is a grade, not feedback.

**Prerequisites beat scores.** Score 0.83 on file I/O but 0.0 on the data structures underneath it, and file I/O stays locked until the gap is closed.

**Distinguishes "unknown" from "weak".** A concept with no evidence is `unknown`, not zero. A concept implied by a harder success you got right is `assumed-ok` — a guess worth acting on, explicitly not a demonstrated skill.

## Three archetypes

Mastery does not mean the same thing in every subject, so the skill does not pretend it does.

| | **A — tool / build**<br>Python, C, SQL, Flutter | **B — concept / model**<br>maths, physics, ML, RAG | **C — language**<br>English, Japanese |
|---|---|---|---|
| Mastery means | you can make it work | it transfers to a new case | fast, accurate, and still there next week |
| Main evidence | tests passing, bug diagnosis | problems, counterexamples, "what if this changes" | production, transformation, recall speed |
| Structure | prerequisite DAG | prerequisite DAG, stricter | grid and spiral, not a chain |
| Getting it right once | usually counts | needs a transfer item | **does not count** |

Archetype C cannot reach `advanced` without spaced review evidence. That rule is in the scoring code, not in the prose, so it cannot be talked around.

## Where the work runs

Chosen during intake, because it decides how practical tasks are delivered.

| | Practical task | Result comes back as |
|---|---|---|
| `none` | answered in conversation | rubric points or an exact answer |
| `local` | files and tests on your machine | the test runner's pass count |
| `notebook` | a generated `.ipynb` | a pasted result line |
| `colab` | a generated `.ipynb` with GPU setup | a pasted result line |

`none` is a first-class answer. Japanese and pure maths need no tooling, and putting a setup step in front of them wastes the first session.

Someone learning PyTorch should be training on MNIST, not fighting a CUDA install — so those subjects get `colab`, and the notebook carries a fixed grading cell:

```
PASS loss_decreases
FAIL grads_zeroed  <- AssertionError:
PASS accuracy_90

UPSKILL_RESULT pt-training-loop-l2-001 2/3
```

You paste that back. A script parses it and looks the concept up in the task manifest. Even that last step is code, because reading a number off the screen and passing it along is a place judgement could leak in. Edit the grading cell and the check count stops matching, and the result is refused.

## Install

Follows the open [Agent Skills](https://agentskills.io/) standard, so it works in Claude Code, OpenAI Codex, Cursor, Gemini CLI, GitHub Copilot, and other compatible agents.

```bash
git clone https://github.com/aslla77/adaptive-upskill.git

# Claude Code, this project only
mkdir -p .claude/skills
for s in adaptive-upskill upskill-next upskill-status upskill-review; do
  ln -sfn "$(pwd)/adaptive-upskill/skills/$s" ".claude/skills/$s"
done

# or for every project
cp -R adaptive-upskill/skills/* ~/.claude/skills/
```

Other agents: copy `skills/*` into that agent's skills directory (`.codex/skills/`, `.cursor/skills/`, `.gemini/skills/`, …).

Requires **Python 3.8+** on PATH. No third-party packages, no network calls, no API keys.

### Permissions

Tool grants from skill frontmatter expire when you send your next message, and a learning session runs scripts across many turns. Add this once so you are not approving the same command repeatedly:

```json
{
  "permissions": {
    "allow": [
      "Bash(python3 *adaptive-upskill/scripts/*)",
      "Bash(ls *)",
      "Bash(open *)",
      "Bash(say *)"
    ]
  }
}
```

Match the scripts directory rather than individual filenames. Listing them by name means
the one script a subject actually needs — `make_notebook.py` for PyTorch, `render_lesson.py`
for Japanese — is the one that turns out to be missing.

## Use

| Say | What happens |
|---|---|
| "I want to learn PyTorch" | intent → concept map → diagnostic → plan → first lesson |
| `/upskill-next` | the next module, one at a time |
| `/upskill-status` | mastery per concept, next module and why, what is locked |
| `/upskill-review` | retrieval practice on whatever is due |

Learning state is written to `./.upskill/<subject>/` in the directory you started the agent in. Add `.upskill/` to `.gitignore`. Come back to the same directory to continue — if you don't, the skill says so rather than quietly starting over.

## Layout

```
skills/adaptive-upskill/
├── SKILL.md                       navigator; the rest loads on demand
├── 01-intent-intake.md            intent → subject, archetype, environment, goal
├── 02-competency-mapping.md       writing and presenting the concept map
├── 03-archetype-A-build.md        tool / build
├── 04-archetype-B-concept.md      concept / model
├── 05-archetype-C-language.md     language acquisition
├── 06-item-authoring.md           items, levels, and keeping answer keys hidden
├── 07-scoring-policy.md           the deterministic / rubric boundary
├── 08-lesson-authoring.md         explain → retrieval → application → checkpoint
├── 09-state-contract.md           file contract and recovery
├── 10-ui-contract.md              dashboard contract
├── 11-execution-environments.md   none / local / notebook / colab
├── 12-html-lessons.md             the lesson payload format
├── 13-prefetching.md              building the next lesson in the background
├── scripts/                       Python 3.8, standard library only
└── assets/
    ├── lesson-shell.html          fixed page; never regenerated per lesson
    └── schemas/
```

`SKILL.md` stays a navigator on purpose. Skill bodies are a recurring token cost and get truncated when a long session compacts, so the detail sits in files that load only when the step needs them.

## What it borrows, and what it doesn't claim

Testing during learning beats re-reading for retention (Roediger & Karpicke, 2006), which is why lessons are shaped explain → retrieval → application rather than explain → explain.

Mastery gates with corrective loops come from mastery learning (Bloom, 1968). The meta-analysis (Kulik, Kulik & Bangert-Drowns, 1990) reports effects around 0.4 SD on locally written criterion-referenced tests and around 0.1 SD on standardised ones. This skill writes its own items, so it sits on the optimistic side of that gap. Worth knowing before treating a number here as an achievement measure.

Assessment is formative in the Black & Wiliam (1998) sense — scores exist to change what happens next, which is why every plan states its reasoning.

The prerequisite graph borrows the **direction** of the surmise relation (Doignon & Falmagne, 1985): succeeding at something hard implies the things underneath it, so they need not all be asked. It is not an implementation of Knowledge Space Theory and is not described as one.

**Thresholds are configuration, not measurement.** `0.45 / 0.70 / 0.85`, the evidence minimums, the item budgets — all chosen to order a plan sensibly, none validated against response data. The skill is instructed never to present them as anything more.

## Limits

- **Certification and factual-recall subjects are not supported.** The recall scheduling they need is minimal here.
- **Speaking and listening cannot be measured.** For a speaking goal the skill says so instead of approximating it in text.
- **Rubric scoring stays a judgement.** Free-response items are graded by a model against a rubric written before the answer existed. Deterministic items are preferred everywhere they are possible.
- **The progress dashboard is not built yet.** Its contract exists; the renderer does
  not. Lesson pages are separate and do work.
- **Answer hashing is not cryptographic.** It stops accidental exposure, not a determined
  reader.
- **v0.1.** The learning loop and the reference fixtures are verified; long-run behaviour across many sessions is not.

## Verification

```bash
python3 tests/run_acceptance.py
```

21 checks: plans differ across novice / intermediate / advanced fixtures, mastery is reproducible and rebuildable from evidence alone, prerequisite gates hold, thin evidence is never presented as mastery, the diagnostic stops on its own inside its budget, the packages satisfy the Agent Skills spec, notebook tasks round-trip into evidence, and no credentials are present.

## License

MIT — see [LICENSE](LICENSE).
