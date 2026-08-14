# 11 — Execution environments

Where the learner's practical work runs. Decided once during intake, stored on the
competency map as `execution_environment`, and never changed silently afterwards.

`none` is a real answer, not a fallback. Japanese and pure mathematics need no tooling,
and putting a setup step in front of them wastes the first session on nothing.

| Value | Practical task is | Evidence comes back as |
|---|---|---|
| `none` | a production or transfer task answered in chat | your rubric points, or an exact answer |
| `local` | files plus tests on their machine | the test runner's `passed`/`total` |
| `notebook` | a generated `.ipynb` they run anywhere | a pasted `UPSKILL_RESULT` line |
| `colab` | a generated `.ipynb` with GPU setup | a pasted `UPSKILL_RESULT` line |

Archetype C is always `none` — `init` rejects anything else.

## Choosing

Ask only when it is genuinely unclear. Most subjects answer themselves.

| The subject… | Environment |
|---|---|
| is a natural language | `none` |
| is maths, physics, or theory answered on paper | `none` |
| is a language or tool that runs on a laptop | `local` |
| is data work — pandas, plotting, SQL over a small file | `notebook` |
| **needs a GPU or heavy install — PyTorch, TensorFlow, training, CUDA** | `colab` |
| needs cloud infrastructure the learner does not have | `colab`, or `none` for the theory half |

The deciding question is not "is this code?" but **"can they actually run it where they
are?"** Someone learning PyTorch on a laptop should be training on MNIST, not fighting a
CUDA install. That is what `colab` is for.

When a subject splits — PyTorch theory versus PyTorch code — pick the environment the
**practical tasks** need and answer the conceptual items in chat regardless. One
environment per subject.

## `none`

Everything happens in the conversation. No files beyond the workspace state.

The opening set's fifth slot is a **production or transfer task** instead of a runnable
one:

- maths / physics: a problem whose answer is exact, plus "what changes if this condition
  moves?"
- language: write the actual thing the goal needs — three sentences of the email, the
  refusal, the request

Deterministic scoring is still the default. A numeric answer, an exact form, a cloze
blank, a multiple choice — all `correct: true/false`. Only free production needs a
rubric, and that gets written before the answer arrives (`07-scoring-policy.md`).

Nothing about mastery, planning, or the prerequisite gate changes. `none` subjects use
the identical scoring path; they simply never call `make_notebook.py`.

## `local`

Write the broken source and its tests to `.upskill/<subject>/items/<task-id>/`, tell the
learner the path, let them use their editor, then run the tests and report
`passed`/`total`.

## `notebook` and `colab`

Generate the task with `make_notebook.py` rather than writing `.ipynb` by hand — the
grading cell has to be exactly right, and hand-written ones drift.

```bash
python3 $SCRIPTS/make_notebook.py --subject <s> --spec <task.json>
```

Task spec:

```json
{
  "task_id": "pt-training-loop-l2-001",
  "concept": "pt-training-loop",
  "level": 2,
  "environment": "colab",
  "title": "Complete the MNIST training loop",
  "intro_md": "The model and data are ready. Fill in only the training loop.",
  "setup": ["!pip -q install torch torchvision"],
  "instructions": "Fill in the TODO inside train_one_epoch.",
  "starter_code": "def train_one_epoch(...):\n    # TODO\n",
  "checks": [
    {"name": "loss_decreases", "code": "assert final_loss < initial_loss"},
    {"name": "accuracy_90",    "code": "assert accuracy >= 0.90"}
  ],
  "also": [{"concept": "pt-autograd", "level": 2}]
}
```

It writes `<task_id>.ipynb` and a manifest holding the concept, level and check count.

### Writing checks

Each check is one `assert` against a variable the learner's code produces. Checks run
in isolation, so one failure never hides the others.

- Name each check after **what it proves**, not what it inspects. `accuracy_90`, not
  `check_3`.
- Two to five checks. One check makes the task pass/fail; more than five turns partial
  credit into noise.
- Test the behaviour, not the spelling. Assert on the trained model's accuracy, not on
  whether they named a variable `optimizer`.
- Never write a check whose failure the learner cannot act on.

### Getting the result back

The learner runs every cell and pastes the last line:

```
UPSKILL_RESULT pt-training-loop-l2-001 2/3
```

```bash
python3 $SCRIPTS/upskill.py ingest --subject <s> --output "<pasted text>"
```

`ingest` parses the line, reads the manifest for the concept and level, and records the
evidence. **Do not read the number and pass it along yourself** — the parse is a step
where judgement could leak in, so it belongs in the script. If the check count in the
paste disagrees with the manifest, `ingest` refuses: the grading cell was edited or an
old notebook was run.

Ask for the whole output, not just the summary line. The `FAIL <name>` lines say which
check broke, and that is what the next lesson starts from.

## Colab delivery

The notebook is a local file. Getting it into Colab, easiest first:

1. **Upload it.** colab.research.google.com -> Upload -> pick the file. Works today, needs
   nothing.
2. **Through Drive.** If the learner keeps a Drive folder synced or mounted, put it there
   and open it from Colab.
3. **Google Drive MCP.** Only worth connecting if uploading becomes a recurring
   annoyance. It requires an OAuth grant, so **offer it, never start it unprompted**, and
   only once `colab` has actually been chosen — a Japanese learner should never see a
   Google authorisation prompt.

Whether that MCP can create Drive files has **not been verified**. Treat option 3 as
unconfirmed until it is connected and tested; options 1 and 2 always work.

Getting results back is a paste in every case. Nothing depends on the delivery route.

## Changing environment later

Changing it does not invalidate existing evidence — concept IDs are unchanged and scores
stay comparable. Say what is changing and why, then edit the map and re-run `init
--force` after telling the learner what `--force` overwrites.
