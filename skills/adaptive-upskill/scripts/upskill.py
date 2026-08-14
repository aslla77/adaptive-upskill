#!/usr/bin/env python3
"""adaptive-upskill CLI. Python 3.8+, standard library only.

Subcommands:
  init      install a validated competency map and create the workspace
  score     turn raw responses into evidence, recompute mastery, decide next probe
  plan      build the prerequisite-aware study plan
  update    record a checkpoint or review result
  review    list concepts that are due for retrieval practice
  status    human-readable summary of where the learner stands
  ingest    read a pasted notebook UPSKILL_RESULT line and record it as evidence
  prefetch  build the next lesson ahead of time so the learner never waits
  dispute   mark an item as disputed so it carries zero weight

The model reports what happened (correct / tests passed / rubric points).
This script decides what it means. That split is the point of the project.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import upskill_core as core  # noqa: E402


def _normalize(resp):
    """Turn a reported response into a 0..1 score. No model judgement here."""
    mode = resp.get("answer_mode", "deterministic")
    if "score" in resp:
        score = float(resp["score"])
    elif mode == "rubric":
        max_points = float(resp.get("max_points", 0))
        if max_points <= 0:
            raise core.UpskillError("rubric response %s needs max_points > 0"
                                    % resp.get("item_id"))
        score = float(resp.get("rubric_points", 0)) / max_points
    elif "passed" in resp and "total" in resp:
        total = float(resp["total"])
        if total <= 0:
            raise core.UpskillError("response %s needs total > 0" % resp.get("item_id"))
        score = float(resp["passed"]) / total
    elif "correct" in resp:
        score = 1.0 if resp["correct"] else 0.0
    else:
        raise core.UpskillError(
            "response %s must carry one of: correct, passed/total, rubric_points, score"
            % resp.get("item_id"))
    return max(0.0, min(1.0, score))


def _to_records(responses, source):
    records = []
    for resp in responses:
        record = {
            "item_id": resp.get("item_id") or "item-%d" % (len(records) + 1),
            "concept": resp["concept"],
            "level": int(resp.get("level", 2)),
            "answer_mode": resp.get("answer_mode", "deterministic"),
            "score": round(_normalize(resp), 4),
            "source": resp.get("source", source),
            "disputed": False,
            "timestamp": resp.get("timestamp") or core.now_iso(),
        }
        if resp.get("note"):
            record["note"] = resp["note"]
        records.append(record)
        # A secondary concept lets one practical task feed two concepts.
        for extra in resp.get("also", []):
            records.append({
                "item_id": record["item_id"] + ":" + extra["concept"],
                "concept": extra["concept"],
                "level": int(extra.get("level", record["level"])),
                "answer_mode": record["answer_mode"],
                "score": record["score"],
                "source": record["source"],
                "disputed": False,
                "timestamp": record["timestamp"],
            })
    return records


def _read_responses(args):
    if args.responses == "-":
        payload = json.load(sys.stdin)
    else:
        payload = core.read_json(args.responses)
    if isinstance(payload, list):
        return payload
    return payload.get("responses", [])


def _save(paths, competency, evidence):
    core.write_json(paths["evidence"], evidence)
    existing = {}
    if os.path.exists(paths["progress"]):
        existing = core.read_json(paths["progress"])
    progress, mastery = core.refresh_progress(competency, evidence, existing)
    core.write_json(paths["progress"], progress)
    return progress, mastery


# --------------------------------------------------------------------------

def cmd_init(args):
    doc = core.validate_competency(core.read_json(args.file))
    subject = args.subject or doc.get("subject")
    if not subject:
        raise core.UpskillError("--subject is required when the map has no subject field")
    doc["subject"] = subject
    doc.setdefault("version", core.SCHEMA_VERSION)
    p = core.paths(subject, args.root)
    if os.path.exists(p["competency"]) and not args.force:
        raise core.UpskillError(
            "%s already exists. Re-running init would discard the existing map and "
            "its plan. Pass --force only after telling the learner what is lost."
            % p["competency"])
    core.write_json(p["competency"], doc)
    if not os.path.exists(p["evidence"]) or args.force:
        core.write_json(p["evidence"], {"version": core.SCHEMA_VERSION,
                                        "subject": subject, "records": []})
    for sub in ("items", "lessons"):
        if not os.path.isdir(p[sub]):
            os.makedirs(p[sub])
    evidence = core.read_json(p["evidence"])
    _save(p, doc, evidence)
    return {"workspace": p["workspace"], "subject": subject,
            "archetype": doc["archetype"], "concepts": len(doc["concepts"])}


def cmd_score(args):
    competency, evidence, p = core.load_state(args.subject, args.root)
    if args.responses:
        new = _to_records(_read_responses(args), "direct")
        evidence["records"].extend(new)
        core.validate_evidence(evidence)
    progress, mastery = _save(p, competency, evidence)
    asked = len(set(r["item_id"].split(":")[0] for r in evidence["records"]
                    if r["source"] in ("direct",)))
    decision = core.next_probe(competency, evidence["records"], asked)
    progress["diagnostic"] = {"asked": asked, "stopped": decision["stop"],
                              "stop_reason": decision.get("stop_reason")}
    core.write_json(p["progress"], progress)
    return {"mastery": mastery, "decision": decision, "asked": asked}


def cmd_plan(args):
    competency, evidence, p = core.load_state(args.subject, args.root)
    progress, mastery = _save(p, competency, evidence)
    minutes = (competency.get("goal") or {}).get("minutes_per_week")
    plan = core.build_plan(competency, mastery, minutes)
    previous = core.read_json(p["plan"]) if os.path.exists(p["plan"]) else None
    plan["plan_version"] = progress.get("plan_version", 0) + 1
    if previous and _same_shape(previous, plan):
        plan["plan_version"] = previous.get("plan_version", plan["plan_version"])
        plan["changed"] = False
    else:
        plan["changed"] = True
        progress["plan_version"] = plan["plan_version"]
        core.write_json(p["progress"], progress)
    core.write_json(p["plan"], plan)
    return plan


def _same_shape(a, b):
    key = lambda plan: [(m["concept"], m["kind"]) for m in plan.get("modules", [])]
    return key(a) == key(b)


def cmd_update(args):
    competency, evidence, p = core.load_state(args.subject, args.root)
    source = "review" if args.review else "checkpoint"
    new = _to_records(_read_responses(args), source)
    evidence["records"].extend(new)
    core.validate_evidence(evidence)
    before = core.compute_mastery(competency, evidence["records"][:-len(new)]) if new else {}
    progress, mastery = _save(p, competency, evidence)
    changes = []
    for concept_id, entry in sorted(mastery.items()):
        old = before.get(concept_id, {"value": 0.0, "status": "unknown"})
        if old["status"] != entry["status"] or abs(old["value"] - entry["value"]) >= 0.05:
            changes.append({"concept": concept_id,
                            "from": "%s %.2f" % (old["status"], old["value"]),
                            "to": "%s %.2f" % (entry["status"], entry["value"])})
    return {"recorded": len(new), "changes": changes, "mastery": mastery,
            "replan_recommended": bool(changes)}


def cmd_review(args):
    competency, evidence, p = core.load_state(args.subject, args.root)
    _, mastery = _save(p, competency, evidence)
    due = core.due_reviews(mastery, evidence["records"], args.as_of)
    return {"due": due, "archetype": competency.get("archetype"),
            "review_required_for_mastery":
                core.ARCHETYPES[competency.get("archetype", "A")]["review_required_for_mastery"]}


def cmd_status(args):
    competency, evidence, p = core.load_state(args.subject, args.root)
    progress, mastery = _save(p, competency, evidence)
    plan = core.read_json(p["plan"]) if os.path.exists(p["plan"]) else None
    return {"subject": competency.get("subject"),
            "archetype": competency.get("archetype"),
            "goal": competency.get("goal"),
            "mastery": mastery,
            "plan": plan,
            "diagnostic": progress.get("diagnostic"),
            "workspace": p["workspace"]}


def cmd_ingest(args):
    """Read a pasted notebook result and turn it into evidence.

    Parsing the line here rather than eyeballing it keeps the last step of a
    remote-executed task as deterministic as a local one.
    """
    import re

    competency, evidence, p = core.load_state(args.subject, args.root)
    if args.output == "-":
        text = sys.stdin.read()
    elif os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = args.output  # allow pasting the line directly as the argument

    matches = re.findall(r"UPSKILL_RESULT\s+(\S+)\s+(\d+)\s*/\s*(\d+)", text)
    if not matches:
        raise core.UpskillError(
            "no UPSKILL_RESULT line found. Ask the learner to run the grading cell "
            "and paste its last line, which looks like: UPSKILL_RESULT <task-id> 4/6")
    task_id, passed, total = matches[-1]
    passed, total = int(passed), int(total)
    if total <= 0:
        raise core.UpskillError("the pasted result reports %d checks" % total)
    if passed > total:
        raise core.UpskillError("pasted result claims %d of %d checks" % (passed, total))

    manifest_path = os.path.join(p["items"], task_id + ".json")
    if not os.path.exists(manifest_path):
        raise core.UpskillError(
            "no manifest for task %s in %s. The notebook must be generated with "
            "make_notebook.py so the concept and level are known." % (task_id, p["items"]))
    manifest = core.read_json(manifest_path)
    if manifest["total_checks"] != total:
        raise core.UpskillError(
            "task %s defines %d checks but the pasted result reports %d. The grading "
            "cell was edited or an older notebook was run."
            % (task_id, manifest["total_checks"], total))

    resp = {"item_id": task_id, "concept": manifest["concept"],
            "level": manifest["level"], "answer_mode": "deterministic",
            "passed": passed, "total": total, "also": manifest.get("also", [])}
    new = _to_records([resp], "checkpoint" if args.checkpoint else "direct")
    evidence["records"].extend(new)
    core.validate_evidence(evidence)
    progress, mastery = _save(p, competency, evidence)
    return {"task": task_id, "passed": passed, "total": total,
            "concept": manifest["concept"], "mastery": mastery,
            "recorded": len(new)}


def _load_prefetch(paths):
    if os.path.exists(paths["prefetch"]):
        return core.read_json(paths["prefetch"])
    return core.empty_prefetch()


def cmd_prefetch(args):
    competency, evidence, p = core.load_state(args.subject, args.root)
    plan = core.read_json(p["plan"]) if os.path.exists(p["plan"]) else None
    progress = core.read_json(p["progress"]) if os.path.exists(p["progress"]) else {}
    plan_version = (plan or {}).get("plan_version", progress.get("plan_version", 0))
    state = _load_prefetch(p)
    op = args.op

    if op == "status":
        current = core.next_module(plan)
        target = core.prefetch_target(plan, current["concept"] if current else None)
        entry = state.get("entry")
        return {"op": op, "current_module": current, "build_next": target,
                "entry": entry, "plan_version": plan_version,
                "stats": state["stats"],
                "should_build": bool(target) and not (
                    entry and entry.get("concept") == (target or {}).get("concept")
                    and entry.get("plan_version") == plan_version)}

    if op == "claim":
        if not args.concept:
            raise core.UpskillError("claim needs --concept")
        target = core.prefetch_target(plan, None)
        for module in ((plan or {}).get("modules") or []):
            if module["concept"] == args.concept:
                target = module
                break
        state["entry"] = {"concept": args.concept, "status": "building",
                          "kind": args.kind or (target or {}).get("kind"),
                          "plan_version": plan_version, "started_at": core.now_iso()}
        core.write_json(p["prefetch"], state)
        return {"op": op, "entry": state["entry"]}

    if op == "ready":
        for field, value in (("--concept", args.concept), ("--lesson-id", args.lesson_id)):
            if not value:
                raise core.UpskillError("ready needs %s" % field)
        if args.path and not os.path.exists(args.path):
            raise core.UpskillError("ready --path points at a file that does not exist: %s"
                                    % args.path)
        previous = state.get("entry") or {}
        state["entry"] = {"concept": args.concept, "status": "ready",
                          "lesson_id": args.lesson_id, "path": args.path,
                          "kind": args.kind or previous.get("kind"),
                          "plan_version": plan_version, "ready_at": core.now_iso()}
        core.write_json(p["prefetch"], state)
        return {"op": op, "entry": state["entry"]}

    if op == "take":
        entry, miss = core.prefetch_take(state, plan, plan_version)
        if entry:
            state["stats"]["hits"] += 1
            state["entry"] = None
            core.write_json(p["prefetch"], state)
            return {"op": op, "hit": True, "entry": entry, "stats": state["stats"]}
        state["stats"]["misses"] += 1
        if miss in core.PREFETCH_DISCARD_REASONS:
            state["stats"]["discarded"] += 1
            state["entry"] = None
        core.write_json(p["prefetch"], state)
        return {"op": op, "hit": False, "reason": miss,
                "explanation": core.PREFETCH_MISS_REASONS[miss],
                "build_now": core.next_module(plan), "stats": state["stats"]}

    if op == "discard":
        state["entry"] = None
        state["stats"]["discarded"] += 1
        core.write_json(p["prefetch"], state)
        return {"op": op, "stats": state["stats"]}

    raise core.UpskillError("unknown prefetch op: %s" % op)


def cmd_dispute(args):
    competency, evidence, p = core.load_state(args.subject, args.root)
    hits = 0
    for r in evidence["records"]:
        if r["item_id"] == args.item or r["item_id"].startswith(args.item + ":"):
            r["disputed"] = True
            r["dispute_reason"] = args.reason or "learner disputed the item"
            hits += 1
    if not hits:
        raise core.UpskillError("no evidence record with item_id %s" % args.item)
    _save(p, competency, evidence)
    return {"disputed": hits, "item": args.item}


# --------------------------------------------------------------------------

def render(result, command):
    lines = []
    if command == "prefetch":
        op = result["op"]
        if op == "status":
            cur = result["current_module"]
            nxt = result["build_next"]
            e = result["entry"]
            lines.append("current module : %s" % (cur["concept"] if cur else "(none)"))
            lines.append("build ahead    : %s" % (nxt["concept"] if nxt else "(nothing left)"))
            if e:
                lines.append("prefetched     : %s [%s]" % (e["concept"], e["status"]))
            else:
                lines.append("prefetched     : (none)")
            lines.append("plan_version   : %s" % result["plan_version"])
            lines.append("SHOULD BUILD" if result["should_build"] else "nothing to do")
            lines.append("stats: %s" % json.dumps(result["stats"]))
        elif op == "take":
            if result["hit"]:
                e = result["entry"]
                lines.append("HIT -- %s is ready: %s" % (e["concept"], e.get("path") or e["lesson_id"]))
            else:
                lines.append("MISS (%s) -- %s" % (result["reason"], result["explanation"]))
                b = result["build_now"]
                lines.append("build now: %s" % (b["concept"] if b else "(nothing)"))
            lines.append("stats: %s" % json.dumps(result["stats"]))
        else:
            lines.append(json.dumps(result.get("entry") or result.get("stats"),
                                    ensure_ascii=False))
    if command == "ingest":
        lines.append("%s: %d/%d checks passed -> %s" %
                     (result["task"], result["passed"], result["total"],
                      result["concept"]))
        lines.append("")
    if command in ("score", "status", "update", "review", "ingest"):
        mastery = result.get("mastery") or {}
        if mastery:
            lines.append("%-22s %8s %5s %6s  %s" %
                         ("concept", "mastery", "evid", "direct", "status"))
            for concept_id, e in sorted(mastery.items(),
                                        key=lambda kv: (-kv[1]["value"], kv[0])):
                lines.append("%-22s %8.3f %5d %6d  %s" %
                             (concept_id, e["value"], e["evidence_count"],
                              e["direct_count"], e["status"]))
    if command == "score":
        d = result["decision"]
        lines.append("")
        lines.append("asked: %d" % result["asked"])
        if d["stop"]:
            lines.append("DIAGNOSTIC STOP -- %s" % d["stop_reason"])
            if d.get("unresolved"):
                lines.append("still unknown: %s" % ", ".join(d["unresolved"]))
        else:
            probe = d["next_probe"]
            lines.append("NEXT PROBE -> concept=%s level=%d (%s)" %
                         (probe["concept"], probe["level"], probe["why"]))
    if command == "plan":
        lines.append("plan_version %s  (changed: %s)" %
                     (result.get("plan_version"), result.get("changed")))
        lines.append("")
        for m in result["modules"]:
            lines.append("%d. [%s] %s  (%d min, priority %.3f)" %
                         (m["order"], m["kind"], m["label"], m["estimated_minutes"],
                          m["priority"]))
            lines.append("     why : %s" % m["why"])
            lines.append("     exit: %s" % m["exit_criterion"])
        if result["skipped"]:
            lines.append("")
            lines.append("skipped:")
            for s in result["skipped"]:
                lines.append("  - %s -- %s (%s)" % (s["concept"], s["reason"], s["evidence"]))
        if result["locked"]:
            lines.append("")
            lines.append("locked by prerequisites:")
            for l in result["locked"]:
                lines.append("  - %s <- needs %s" % (l["concept"], ", ".join(l["blocked_by"])))
        lines.append("")
        lines.append("total %d min%s" % (result["total_estimated_minutes"],
                     (", ~%s weeks" % result["estimated_weeks"])
                     if result.get("estimated_weeks") else ""))
    if command == "update":
        lines.append("")
        lines.append("recorded %d evidence record(s)" % result["recorded"])
        for c in result["changes"]:
            lines.append("  %s: %s -> %s" % (c["concept"], c["from"], c["to"]))
        if result["replan_recommended"]:
            lines.append("mastery moved; re-run `plan`")
    if command == "review":
        lines.append("")
        if not result["due"]:
            lines.append("nothing due for review")
        for d in result["due"]:
            lines.append("  %s -- box %d, interval %dd, %dd since last evidence (%s)" %
                         (d["concept"], d["box"], d["interval_days"],
                          d["days_since"], d["status"]))
        if result["review_required_for_mastery"]:
            lines.append("archetype C: spaced review evidence is required before "
                         "any concept can reach 'advanced'")
    if command == "init":
        lines.append("workspace: %s" % result["workspace"])
        lines.append("subject %s, archetype %s, %d concepts" %
                     (result["subject"], result["archetype"], result["concepts"]))
    if command == "status":
        lines.append("")
        lines.append("workspace: %s" % result["workspace"])
        if result.get("diagnostic"):
            lines.append("diagnostic: %s" % json.dumps(result["diagnostic"],
                                                       ensure_ascii=False))
    if command == "dispute":
        lines.append("marked %d record(s) for %s as disputed (weight 0)" %
                     (result["disputed"], result["item"]))
    return "\n".join(lines)


def main(argv=None):
    # Shared flags are accepted both before and after the subcommand, because
    # getting that wrong should not cost a turn mid-lesson.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="workspace root (default ./.upskill or $UPSKILL_ROOT)")
    common.add_argument("--json", action="store_true", help="emit raw JSON")

    parser = argparse.ArgumentParser(prog="upskill", parents=[common],
                                     description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command")
    add = lambda name: sub.add_parser(name, parents=[common])

    p_init = add("init")
    p_init.add_argument("--subject")
    p_init.add_argument("--file", required=True, help="competency map JSON")
    p_init.add_argument("--force", action="store_true")

    p_score = add("score")
    p_score.add_argument("--subject", required=True)
    p_score.add_argument("--responses", help="JSON file or - for stdin")

    p_plan = add("plan")
    p_plan.add_argument("--subject", required=True)

    p_update = add("update")
    p_update.add_argument("--subject", required=True)
    p_update.add_argument("--responses", required=True)
    p_update.add_argument("--review", action="store_true",
                          help="record as spaced review rather than checkpoint")

    p_review = add("review")
    p_review.add_argument("--subject", required=True)
    p_review.add_argument("--as-of", dest="as_of")

    p_status = add("status")
    p_status.add_argument("--subject", required=True)

    p_ingest = add("ingest")
    p_ingest.add_argument("--subject", required=True)
    p_ingest.add_argument("--output", required=True,
                          help="file with the pasted notebook output, the pasted line itself, or -")
    p_ingest.add_argument("--checkpoint", action="store_true",
                          help="record as a lesson checkpoint rather than diagnostic evidence")

    p_prefetch = add("prefetch")
    p_prefetch.add_argument("op", choices=["status", "claim", "ready", "take", "discard"])
    p_prefetch.add_argument("--subject", required=True)
    p_prefetch.add_argument("--concept")
    p_prefetch.add_argument("--lesson-id", dest="lesson_id")
    p_prefetch.add_argument("--path")
    p_prefetch.add_argument("--kind")

    p_dispute = add("dispute")
    p_dispute.add_argument("--subject", required=True)
    p_dispute.add_argument("--item", required=True)
    p_dispute.add_argument("--reason")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    handlers = {"init": cmd_init, "score": cmd_score, "plan": cmd_plan,
                "update": cmd_update, "review": cmd_review, "status": cmd_status,
                "ingest": cmd_ingest, "prefetch": cmd_prefetch,
                "dispute": cmd_dispute}
    try:
        result = handlers[args.command](args)
    except core.UpskillError as exc:
        core.die(str(exc))
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render(result, args.command))
    return 0


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        core.die("Python 3.8+ required, found %d.%d" % sys.version_info[:2])
    sys.exit(main())
