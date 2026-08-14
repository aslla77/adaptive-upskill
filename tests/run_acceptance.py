#!/usr/bin/env python3
"""Acceptance checks for adaptive-upskill v0.1. Python 3.8, stdlib only.

Each fixture is a response oracle: given (concept, level) it says how the learner
would do. The runner then drives the real adaptive loop -- opening set, then one
probe at a time until the script says STOP -- so item counts are measured, not assumed.

Run:  python3 tests/run_acceptance.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "skills", "adaptive-upskill", "scripts")
SKILLS = os.path.join(ROOT, "skills")
MAP = os.path.join(HERE, "fixtures", "python-competency.json")

sys.path.insert(0, SCRIPTS)
import upskill_core as core  # noqa: E402

# Opening set: concept + level, mirroring 06-item-authoring.md
OPENING = [
    ("py-syntax", 1),
    ("py-collections", 2),
    ("py-functions", 2),
    ("py-errors", 3),
    ("py-files-io", 2),
]

# fixture -> concept -> highest level the learner reliably handles (0 = none)
FIXTURES = {
    "novice": {"py-syntax": 1, "py-collections": 0, "py-functions": 0,
               "py-errors": 0, "py-files-io": 0, "py-modules": 0},
    "intermediate": {"py-syntax": 3, "py-collections": 1, "py-functions": 3,
                     "py-errors": 3, "py-files-io": 2, "py-modules": 0},
    "advanced": {"py-syntax": 4, "py-collections": 4, "py-functions": 4,
                 "py-errors": 4, "py-files-io": 3, "py-modules": 3},
}

FAILURES = []
PASSES = []


def check(name, condition, detail=""):
    (PASSES if condition else FAILURES).append(name)
    print("  %s %s%s" % ("PASS" if condition else "FAIL", name,
                         ("  -- " + detail) if detail else ""))


def run(args, root, now):
    env = dict(os.environ, UPSKILL_ROOT=root, UPSKILL_NOW=now)
    proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, "upskill.py")] + args,
                          capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError("command failed: %s\n%s" % (" ".join(args), proc.stderr))
    return proc.stdout


def answer(oracle, concept, level):
    ceiling = oracle.get(concept, 0)
    if level <= ceiling:
        return {"correct": True}
    if level == ceiling + 1:
        return {"passed": 2, "total": 3}   # partial: right at the edge
    return {"correct": False}


def drive(fixture_name, root):
    """Run the full adaptive diagnostic for one fixture. Returns (asked, plan)."""
    oracle = FIXTURES[fixture_name]
    run(["init", "--file", MAP, "--force"], root, "2026-08-15T09:00:00Z")

    responses = []
    for i, (concept, level) in enumerate(OPENING):
        resp = {"item_id": "open-%d" % i, "concept": concept, "level": level,
                "answer_mode": "deterministic"}
        resp.update(answer(oracle, concept, level))
        responses.append(resp)

    asked = 0
    step = 0
    while True:
        payload = json.dumps({"responses": responses})
        path = os.path.join(root, "resp.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(payload)
        out = run(["score", "--subject", "python", "--responses", path, "--json"],
                  root, "2026-08-15T09:%02d:00Z" % (step + 1))
        result = json.loads(out)
        asked = result["asked"]
        decision = result["decision"]
        if decision["stop"]:
            break
        probe = decision["next_probe"]
        step += 1
        if step > 20:
            raise RuntimeError("probe loop did not terminate")
        resp = {"item_id": "probe-%d" % step, "concept": probe["concept"],
                "level": probe["level"], "answer_mode": "deterministic"}
        resp.update(answer(oracle, probe["concept"], probe["level"]))
        responses = [resp]

    plan = json.loads(run(["plan", "--subject", "python", "--json"], root,
                          "2026-08-15T10:00:00Z"))
    status = json.loads(run(["status", "--subject", "python", "--json"], root,
                            "2026-08-15T10:00:00Z"))
    return asked, plan, status, decision


def module_signature(plan):
    return [(m["concept"], m["kind"]) for m in plan["modules"]]


def main():
    print("adaptive-upskill acceptance checks\n")
    print("environment")
    check("A8  runs on Python 3.8+ with stdlib only",
          sys.version_info >= (3, 8), "running %d.%d" % sys.version_info[:2])

    workdir = tempfile.mkdtemp(prefix="upskill-acceptance-")
    results = {}
    try:
        print("\nfixtures")
        for name in ("novice", "intermediate", "advanced"):
            root = os.path.join(workdir, name)
            asked, plan, status, decision = drive(name, root)
            results[name] = {"asked": asked, "plan": plan, "status": status,
                             "root": root, "decision": decision}
            print("  %-13s asked=%d  modules=%d  skipped=%d  locked=%d" %
                  (name, asked, len(plan["modules"]), len(plan["skipped"]),
                   len(plan["locked"])))

        print("\nA1  three learners get materially different plans")
        sigs = dict((n, module_signature(results[n]["plan"])) for n in results)
        pairs = [("novice", "intermediate"), ("novice", "advanced"),
                 ("intermediate", "advanced")]
        for a, b in pairs:
            check("A1  %s != %s" % (a, b), sigs[a] != sigs[b],
                  "%d vs %d modules" % (len(sigs[a]), len(sigs[b])))

        print("\nA2  same evidence produces byte-identical mastery")
        root = results["intermediate"]["root"]
        first = run(["status", "--subject", "python", "--json"], root, "2026-08-15T11:00:00Z")
        second = run(["status", "--subject", "python", "--json"], root, "2026-08-15T12:00:00Z")
        m1 = json.dumps(json.loads(first)["mastery"], sort_keys=True)
        m2 = json.dumps(json.loads(second)["mastery"], sort_keys=True)
        check("A2  mastery is reproducible across runs", m1 == m2)

        replay_root = os.path.join(workdir, "replay")
        os.makedirs(replay_root)
        shutil.copytree(os.path.join(root, "python"), os.path.join(replay_root, "python"))
        os.remove(os.path.join(replay_root, "python", "progress.json"))
        rebuilt = run(["status", "--subject", "python", "--json"], replay_root,
                      "2026-08-15T13:00:00Z")
        m3 = json.dumps(json.loads(rebuilt)["mastery"], sort_keys=True)
        check("A2  mastery rebuilds from evidence.json alone", m1 == m3)

        print("\nA3  prerequisites override score")
        ok = True
        detail = ""
        for name, data in results.items():
            plan = data["plan"]
            mastery = data["status"]["mastery"]
            locked = set(l["concept"] for l in plan["locked"])
            scheduled = set(m["concept"] for m in plan["modules"])
            overlap = locked & scheduled
            if overlap:
                ok = False
                detail = "%s scheduled locked concept(s) %s" % (name, sorted(overlap))
            for entry in plan["locked"]:
                for blocker in entry["blocked_by"]:
                    b = mastery[blocker]
                    if b["status"] not in ("unknown", "foundation") and b["value"] >= 0.70:
                        ok = False
                        detail = "%s: %s listed as blocker but is %s %.2f" % (
                            name, blocker, b["status"], b["value"])
        check("A3  locked concepts never appear as modules", ok, detail)

        inter = results["intermediate"]
        check("A3  intermediate locks py-files-io behind py-collections",
              any(l["concept"] == "py-files-io" and "py-collections" in l["blocked_by"]
                  for l in inter["plan"]["locked"]),
              json.dumps(inter["plan"]["locked"], ensure_ascii=False))

        print("\nA4  thin evidence is never dressed up as mastery")
        ok = True
        detail = ""
        for name, data in results.items():
            for cid, e in data["status"]["mastery"].items():
                if e["evidence_count"] == 0 and e["status"] != "unknown":
                    ok, detail = False, "%s/%s has no evidence but status %s" % (
                        name, cid, e["status"])
                if e["direct_count"] == 0 and e["evidence_count"] > 0 \
                        and e["status"] != "assumed-ok":
                    ok, detail = False, "%s/%s is implied-only but status %s" % (
                        name, cid, e["status"])
                if e["status"] == "advanced" and e["max_direct_level"] < 3:
                    ok, detail = False, "%s/%s advanced without level-3 evidence" % (
                        name, cid)
        check("A4  unknown / assumed-ok / advanced rules hold", ok, detail)

        print("\nA5  the diagnostic adapts its length")
        counts = dict((n, results[n]["asked"]) for n in results)
        check("A5  every fixture stops within the 8-item budget",
              all(c <= 8 for c in counts.values()), json.dumps(counts))
        check("A5  a confident learner is asked fewer items than a mixed one",
              counts["advanced"] < counts["intermediate"],
              "advanced=%d intermediate=%d" % (counts["advanced"],
                                               counts["intermediate"]))
        check("A5  every fixture stops on its own, not by hitting the cap",
              all(results[n]["decision"]["stop_reason"] == "all concepts resolved"
                  for n in results),
              json.dumps(dict((n, results[n]["decision"]["stop_reason"])
                              for n in results), ensure_ascii=False))

        print("\nA10 skill packages satisfy the Agent Skills spec")
        for entry in sorted(os.listdir(SKILLS)):
            path = os.path.join(SKILLS, entry, "SKILL.md")
            if not os.path.exists(path):
                continue
            problems = validate_skill(entry, path)
            check("A10 %s" % entry, not problems, "; ".join(problems))

        print("\nA11 execution environments")
        check("A11 archetype C is forced to environment 'none'",
              _rejects_env("C", "colab"), "")
        check("A11 an unknown environment is rejected", _rejects_env("A", "cloud"), "")
        check("A11 a map with no environment defaults to 'none'",
              core.validate_competency({"archetype": "A", "concepts":
                                        [{"id": "x", "importance": 1.0,
                                          "goal_relevance": 1.0}]}
                                       )["execution_environment"] == "none")

        nb_root = os.path.join(workdir, "notebook")
        problems, summary = notebook_roundtrip(nb_root)
        check("A11 notebook task round-trips to evidence", not problems,
              "; ".join(problems) or summary)

        print("\nsecurity")
        leaked = grep_secrets()
        check("no provider keys or tokens in the skill package", not leaked,
              ", ".join(leaked))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("\n%d passed, %d failed" % (len(PASSES), len(FAILURES)))
    return 1 if FAILURES else 0


def _rejects_env(archetype, env):
    doc = {"archetype": archetype, "execution_environment": env,
           "concepts": [{"id": "x", "importance": 1.0, "goal_relevance": 1.0}]}
    try:
        core.validate_competency(doc)
        return False
    except core.UpskillError:
        return True


def notebook_roundtrip(root):
    """Generate a notebook task, fake the learner running it, ingest the result.

    The grading cell is executed for real so a broken generator cannot pass.
    """
    import contextlib
    import io

    problems = []
    env = dict(os.environ, UPSKILL_ROOT=root, UPSKILL_NOW="2026-08-15T10:00:00Z")
    cmap = os.path.join(root, "map.json")
    os.makedirs(root)
    with open(cmap, "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "subject": "pytorch", "archetype": "A",
                   "execution_environment": "colab",
                   "goal": {"outcome": "train MNIST", "minutes_per_week": 180},
                   "concepts": [
                       {"id": "pt-tensors", "label": "tensors", "importance": 1.2,
                        "goal_relevance": 1.2, "prerequisites": []},
                       {"id": "pt-loop", "label": "training loop", "importance": 1.3,
                        "goal_relevance": 1.5, "prerequisites": ["pt-tensors"]}]}, fh)
    spec = os.path.join(root, "spec.json")
    with open(spec, "w", encoding="utf-8") as fh:
        json.dump({"task_id": "pt-loop-l2-001", "concept": "pt-loop", "level": 2,
                   "environment": "colab", "title": "loop",
                   "starter_code": "# TODO\n",
                   "checks": [{"name": "loss_down", "code": "assert final < initial"},
                              {"name": "acc_90", "code": "assert acc >= 0.9"},
                              {"name": "no_nan", "code": "assert not nan_seen"}],
                   "also": [{"concept": "pt-tensors", "level": 2}]}, fh)

    subprocess.run([sys.executable, os.path.join(SCRIPTS, "upskill.py"),
                    "init", "--file", cmap], capture_output=True, text=True, env=env)
    gen = subprocess.run([sys.executable, os.path.join(SCRIPTS, "make_notebook.py"),
                          "--subject", "pytorch", "--spec", spec],
                         capture_output=True, text=True, env=env)
    if gen.returncode != 0:
        return ["make_notebook failed: %s" % gen.stderr.strip()], ""

    nb_path = os.path.join(root, "pytorch", "items", "pt-loop-l2-001.ipynb")
    if not os.path.exists(nb_path):
        return ["notebook not written"], ""
    with open(nb_path, encoding="utf-8") as fh:
        nb = json.load(fh)
    if nb.get("nbformat") != 4:
        problems.append("not a v4 notebook")

    grading = "".join(nb["cells"][-1]["source"])
    try:
        compile(grading, "grading", "exec")
    except SyntaxError as exc:
        return ["grading cell does not compile: %s" % exc], ""

    # Run it as a learner would, with two of the three checks satisfied.
    buf = io.StringIO()
    namespace = {"final": 1.0, "initial": 2.0, "acc": 0.95, "nan_seen": True}
    with contextlib.redirect_stdout(buf):
        exec(grading, namespace)
    output = buf.getvalue()
    if "UPSKILL_RESULT pt-loop-l2-001 2/3" not in output:
        problems.append("grading cell printed %r" % output.strip().split("\n")[-1])

    ing = subprocess.run([sys.executable, os.path.join(SCRIPTS, "upskill.py"),
                          "ingest", "--subject", "pytorch", "--output", output,
                          "--json"], capture_output=True, text=True, env=env)
    if ing.returncode != 0:
        return problems + ["ingest failed: %s" % ing.stderr.strip()], ""
    result = json.loads(ing.stdout)
    if (result["passed"], result["total"]) != (2, 3):
        problems.append("ingest read %d/%d" % (result["passed"], result["total"]))
    mastery = result["mastery"]
    if abs(mastery["pt-loop"]["value"] - 0.6667) > 0.001:
        problems.append("pt-loop mastery %.4f, expected 0.6667" % mastery["pt-loop"]["value"])
    if mastery["pt-tensors"]["evidence_count"] != 1:
        problems.append("'also' concept did not receive evidence")

    # A tampered grading cell must be refused rather than silently trusted.
    bad = subprocess.run([sys.executable, os.path.join(SCRIPTS, "upskill.py"),
                          "ingest", "--subject", "pytorch",
                          "--output", "UPSKILL_RESULT pt-loop-l2-001 9/9"],
                         capture_output=True, text=True, env=env)
    if bad.returncode == 0:
        problems.append("a result with the wrong check count was accepted")

    return problems, "2/3 -> mastery %.3f, also-concept recorded" % mastery["pt-loop"]["value"]


PORTABLE_FIELDS = {"name", "description", "license", "compatibility",
                   "metadata", "allowed-tools"}


def validate_skill(dirname, path):
    """Check the spec rules we can check without a network call."""
    problems = []
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---\n"):
        return ["missing YAML frontmatter"]
    end = text.find("\n---\n", 3)
    if end == -1:
        return ["unterminated frontmatter"]
    block = text[4:end]

    keys = []
    for line in block.split("\n"):
        if line and not line.startswith((" ", "\t", "#")) and ":" in line:
            keys.append(line.split(":", 1)[0].strip())
    extra = set(keys) - PORTABLE_FIELDS
    if extra:
        problems.append("non-portable frontmatter field(s): %s" % sorted(extra))
    for required in ("name", "description"):
        if required not in keys:
            problems.append("missing required field: %s" % required)

    name = None
    for line in block.split("\n"):
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
    if name != dirname:
        problems.append("name %r does not match directory %r" % (name, dirname))
    if name and (len(name) > 64 or not all(c.islower() or c.isdigit() or c == "-"
                                           for c in name)
                 or name.startswith("-") or name.endswith("-") or "--" in name):
        problems.append("name violates the spec's character rules")

    desc = block.split("description:", 1)[1] if "description:" in block else ""
    desc = desc.split("\nlicense:")[0].split("\nmetadata:")[0]
    desc = desc.split("\nallowed-tools:")[0].split("\ncompatibility:")[0]
    if len(desc.strip()) > 1024:
        problems.append("description is %d chars, spec caps it at 1024" % len(desc.strip()))

    body_lines = text[end:].count("\n")
    if body_lines > 500:
        problems.append("SKILL.md body is %d lines, spec recommends under 500" % body_lines)

    skill_dir = os.path.dirname(path)
    for line in text.split("\n"):
        if line.strip().startswith("| `") and ".md`" in line:
            ref = line.split("`")[1]
            if not os.path.exists(os.path.join(skill_dir, ref)):
                problems.append("referenced file missing: %s" % ref)
    return problems


def grep_secrets():
    patterns = ("sk-ant-", "sk-proj-", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "Bearer ")
    hits = []
    for base, _dirs, files in os.walk(SKILLS):
        for fname in files:
            path = os.path.join(base, fname)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except (UnicodeDecodeError, OSError):
                continue
            for pattern in patterns:
                if pattern in content:
                    hits.append("%s in %s" % (pattern, os.path.relpath(path, ROOT)))
    return hits


if __name__ == "__main__":
    sys.exit(main())
