#!/usr/bin/env python3
"""Build a runnable practical task as a Jupyter notebook. Python 3.8, stdlib only.

Why a notebook: some subjects cannot be practised on the learner's laptop. PyTorch
needs a GPU, and a beginner should be training on MNIST rather than fighting CUDA
installs. The notebook runs wherever it has to -- Colab, Kaggle, a local Jupyter --
and still produces a machine-readable result, so scoring stays deterministic no
matter where the code executed.

Input: a task spec JSON (see `11-execution-environments.md`).
Output: <items>/<task_id>.ipynb  and  <items>/<task_id>.json (manifest)

    python3 make_notebook.py --subject pytorch --spec task.json

The learner runs every cell and pastes back the single UPSKILL_RESULT line.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import upskill_core as core  # noqa: E402

RESULT_PREFIX = "UPSKILL_RESULT"

COLAB_GPU_NOTE = (
    "> **Turn on the GPU** - Runtime -> Change runtime type -> Hardware accelerator -> GPU.\n"
    "> If the cell below prints `cpu` instead of `cuda`, it is not on yet."
)

DEVICE_CELL = (
    "import torch\n"
    "device = 'cuda' if torch.cuda.is_available() else 'cpu'\n"
    "print('device:', device)\n"
)


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(source)}


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": _lines(source)}


def _lines(text):
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def grading_cell(task_id, checks):
    """A fixed, self-contained grader.

    Every check runs in isolation so one failure cannot hide the rest, and the
    summary line is the only thing the learner has to carry back.
    """
    lines = [
        "# =====================================================",
        "#  GRADING CELL - do not edit",
        "#  Run it, then copy the final UPSKILL_RESULT line back to the agent",
        "# =====================================================",
        "_checks = []",
        "",
    ]
    for check in checks:
        name = check["name"]
        body = check["code"].rstrip("\n")
        lines.append("try:")
        for line in body.split("\n"):
            lines.append("    " + line)
        lines.append("    _checks.append((%r, True, ''))" % name)
        lines.append("except Exception as _e:")
        lines.append("    _checks.append((%r, False, type(_e).__name__ + ': ' + str(_e)[:120]))"
                     % name)
        lines.append("")
    lines += [
        "_passed = sum(1 for _, ok, _ in _checks if ok)",
        "for _name, _ok, _why in _checks:",
        "    print(('PASS ' if _ok else 'FAIL ') + _name + (('  <- ' + _why) if _why else ''))",
        "print()",
        # Built by concatenation on purpose: %-formatting here has to survive one
        # round of %-formatting in the generator, and it did not.
        "print('%s %s ' + str(_passed) + '/' + str(len(_checks)))"
        % (RESULT_PREFIX, task_id),
    ]
    return code("\n".join(lines))


def build(spec):
    task_id = spec["task_id"]
    env = spec.get("environment", "notebook")
    cells = [md("# %s\n\n%s" % (spec.get("title", task_id),
                                spec.get("intro_md", "")))]

    if env == "colab":
        cells.append(md(COLAB_GPU_NOTE))
    for command in spec.get("setup", []):
        cells.append(code(command))
    if spec.get("needs_device", env == "colab"):
        cells.append(code(DEVICE_CELL))

    cells.append(md("## Your turn\n\n%s" % spec.get("instructions", "")))
    cells.append(code(spec.get("starter_code", "# TODO\n")))

    if spec.get("scratch_cells", 1):
        cells.append(md("### Scratch space"))
        for _ in range(int(spec.get("scratch_cells", 1))):
            cells.append(code(""))

    cells.append(md("## Grading\n\nRun the cell below and copy back the **final `%s` line**."
                    % RESULT_PREFIX))
    cells.append(grading_cell(task_id, spec["checks"]))

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python"},
            "upskill": {"task_id": task_id, "concept": spec["concept"],
                        "level": spec["level"], "environment": env},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def manifest(spec):
    return {
        "task_id": spec["task_id"],
        "concept": spec["concept"],
        "level": spec["level"],
        "answer_mode": "deterministic",
        "environment": spec.get("environment", "notebook"),
        "total_checks": len(spec["checks"]),
        "check_names": [c["name"] for c in spec["checks"]],
        "also": spec.get("also", []),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="make_notebook")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--spec", required=True, help="task spec JSON, or - for stdin")
    parser.add_argument("--root")
    args = parser.parse_args(argv)

    spec = json.load(sys.stdin) if args.spec == "-" else core.read_json(args.spec)
    for field in ("task_id", "concept", "level", "checks"):
        if field not in spec:
            core.die("task spec is missing required field: %s" % field)
    if not spec["checks"]:
        core.die("a task with no checks produces no evidence; add at least one")

    paths = core.paths(args.subject, args.root)
    nb_path = os.path.join(paths["items"], spec["task_id"] + ".ipynb")
    core.write_json(nb_path, build(spec))
    core.write_json(os.path.join(paths["items"], spec["task_id"] + ".json"), manifest(spec))

    print("notebook: %s" % nb_path)
    print("checks  : %d" % len(spec["checks"]))
    print("")
    print("Tell the learner to run every cell, then paste back the %s line." % RESULT_PREFIX)
    if spec.get("environment") == "colab":
        print("Colab: upload this file, or open it from Drive, and enable the GPU runtime.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
