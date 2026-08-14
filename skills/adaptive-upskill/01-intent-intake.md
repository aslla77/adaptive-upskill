# 01 — Intent intake

Do not open with "what subject?". Open with what they want to be able to do. The
subject, the archetype, and half the curriculum fall out of the answer.

## The three questions

Ask Q1 and Q2 together. Ask Q3 only after you know the archetype.

**Q1.** What do you want to be able to do? If there is something you are currently stuck on, describe that.

**Q2.** By when, and how many hours a week can you give it?

**Q3.** archetype-specific, exactly one question:

| Archetype | Q3 | What it decides |
|---|---|---|
| A tool-build | What exactly is that task? What goes in, what comes out? | Which libraries and language features drop out of scope entirely |
| B concept-model | How far are you comfortable with what sits underneath this - the maths, statistics, or base theory? | Where the prerequisite chain is cut |
| C language | Is the goal a test score or actually using it? Which matters most right now - reading, listening, writing, or speaking? | Test prep and use are different curricula; the four skills need weights |

Stop at three. This whole step should take under two minutes.

## Then decide where the work will run

Every subject gets an `execution_environment`. Derive it — do not ask unless it is
genuinely unclear. Full rules in `11-execution-environments.md`.

| The subject… | Environment |
|---|---|
| natural language | `none` (forced — `init` rejects anything else for archetype C) |
| maths, physics, theory answered on paper | `none` |
| a language or tool that runs on a laptop | `local` |
| data work — pandas, plotting, SQL over a file | `notebook` |
| **needs a GPU or a heavy install: PyTorch, TensorFlow, training, CUDA** | `colab` |

The question is not "is this code?" but **"can they actually run it where they are?"**
Someone learning PyTorch should be training on MNIST, not fighting a CUDA install.

**`none` is a real answer.** Japanese and pure maths need no tooling, and a setup step in
front of them wastes the first session. Those subjects run entirely in chat and use the
identical scoring path; they simply never generate a notebook.

### Only if you landed on `colab`

Mention delivery once, then move on — do not turn intake into a setup session:

> Practical work will come as Colab notebooks. I generate the file, you upload it to
> Colab and run it. Connecting Google Drive could remove the upload step, but that
> means granting account access, so let us skip it for now and revisit if uploading
> becomes annoying.

**Never start the Google Drive OAuth flow on your own**, and never mention it for any
other environment. A Japanese learner should not see a Google authorisation prompt.
Whether that MCP can create Drive files is unverified — say so if asked.

## Classifying the archetype

| Signal | Archetype |
|---|---|
| The output is something that runs — a script, a query, an app | **A** tool-build |
| The output is understanding that transfers — "why does this happen", "which method fits" | **B** concept-model |
| The output is producing or understanding a human language | **C** language-acquisition |

Edge cases:

- **"I want to learn C"** is archetype **A**. Programming languages are tools.
- **SQL** is A. **Database theory / normalization** is B. Ask which they mean.
- **"I want to learn machine learning"** - if they want to run training jobs, A; if they want to
  choose and defend methods, B. Usually B with an A tail.
- **Certification and factual recall subjects** (law, anatomy, exam prep) are not yet
  supported. Say so: the spaced-repetition machinery they need is only partly built.
  Offer archetype B treatment and be explicit that recall scheduling will be weak.

When the answer spans two archetypes, pick the one that matches the **stated goal**, not
the subject label, and say which you picked.

## Goal types

| Type | Completion looks like | Effect on the plan |
|---|---|---|
| Artifact | A specific thing works | Curriculum is pulled toward whatever that artifact touches |
| Capability | Can handle a class of tasks unaided | Broader coverage, more transfer items |
| Exam | A score by a date | Coverage follows the syllabus; deadline drives pacing |
| Understanding | Can explain and judge | Heavier on concepts and counterexamples, lighter on tooling |

An exam goal with no deadline is usually a capability goal. Ask.

## Confirm before moving on

Print this table and get a yes:

| Field | Value |
|---|---|
| Subject | … |
| Archetype | A/B/C - mastery here means "…" |
| Environment | none / local / notebook / colab - one line of reasoning |
| Goal type | artifact / capability / exam / understanding |
| Done when | (one observable sentence) |
| Background | (their words, marked as self-report) |
| Budget | N hours/week, deadline … |

Record background as context. It never becomes a mastery number.

If they refuse the diagnostic, allow it, but state the cost: every concept starts
`unknown`, nothing gets skipped, and the plan is a generic ordering rather than a
personal one.
