"""Deterministic core for the adaptive-upskill skill.

Python 3.8 compatible. Standard library only -- no pip installs.
The LLM never computes a score or decides when the diagnostic stops.
Everything in this module is pure arithmetic over evidence records.
"""
import json
import os
import sys
from datetime import datetime, timedelta

SCHEMA_VERSION = 1

LEVEL_WEIGHT = {1: 1.00, 2: 1.20, 3: 1.50, 4: 1.80}
SOURCE_WEIGHT = {"direct": 1.0, "checkpoint": 1.0, "review": 1.0, "implied": 0.5}

# Thresholds are product configuration, NOT psychometrically validated values.
BAND_FOUNDATION = 0.45
BAND_DEVELOPING = 0.70
BAND_PROFICIENT = 0.85
PREREQ_GATE = 0.70

# A score in this open interval is ambiguous: one piece of it is not enough.
AMBIGUOUS_LOW = 0.30
AMBIGUOUS_HIGH = 0.70

IMPLY_MIN_LEVEL = 2
IMPLY_MIN_SCORE = 0.85
IMPLIED_SCORE = 0.80

REVIEW_INTERVALS_DAYS = [1, 3, 7, 14, 30]

# Where the learner's practical work actually runs. Chosen once, during intake.
# `none` is a first-class answer, not a fallback: Japanese and pure maths need no
# tooling, and pretending otherwise adds a setup wall in front of the learning.
ENVIRONMENTS = {
    "none": {"runnable": False,
             "practical_task": "production or transfer task answered in chat"},
    "local": {"runnable": True,
              "practical_task": "files plus tests on the learner's machine"},
    "notebook": {"runnable": True,
                 "practical_task": ".ipynb the learner runs anywhere"},
    "colab": {"runnable": True,
              "practical_task": ".ipynb with GPU setup, run on Colab"},
}

# How lessons are shown. Orthogonal to where code runs: a language learner has no
# execution environment at all yet still needs a rendered page, because terminals
# get CJK widths wrong, cannot show furigana, and drop glyphs the font lacks.
PRESENTATIONS = ("chat", "html")

# Per-archetype policy. Archetypes are defined in the skill reference files:
#   A = tool/build, B = concept/model, C = language acquisition.
ARCHETYPES = {
    "A": {
        "label": "tool-build",
        "max_diagnostic_items": 8,
        "advanced_requires_level": 3,
        "review_required_for_mastery": False,
    },
    "B": {
        "label": "concept-model",
        "max_diagnostic_items": 8,
        "advanced_requires_level": 3,
        "review_required_for_mastery": False,
    },
    "C": {
        "label": "language-acquisition",
        "max_diagnostic_items": 10,
        "advanced_requires_level": 3,
        # Getting it right once is not evidence of language mastery.
        "review_required_for_mastery": True,
    },
}


class UpskillError(Exception):
    pass


def _require(cond, message):
    if not cond:
        raise UpskillError(message)


# --------------------------------------------------------------------------
# IO
# --------------------------------------------------------------------------

def read_json(path):
    if not os.path.exists(path):
        raise UpskillError("file not found: %s" % path)
    with open(path, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except ValueError as exc:
            raise UpskillError("invalid JSON in %s: %s" % (path, exc))


def write_json(path, data):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def now_iso():
    """Caller may override via UPSKILL_NOW so fixtures stay reproducible."""
    override = os.environ.get("UPSKILL_NOW")
    if override:
        return override
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def parse_iso(value):
    if not value:
        return None
    text = value[:-1] if value.endswith("Z") else value
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Validation (stdlib only -- jsonschema is not available on every machine)
# --------------------------------------------------------------------------

def validate_competency(doc):
    _require(isinstance(doc, dict), "competency must be an object")
    _require(doc.get("archetype") in ARCHETYPES,
             "archetype must be one of %s" % sorted(ARCHETYPES))
    env = doc.setdefault("execution_environment", "none")
    _require(env in ENVIRONMENTS,
             "execution_environment must be one of %s" % sorted(ENVIRONMENTS))
    if doc["archetype"] == "C":
        _require(env == "none",
                 "archetype C is language learning; execution_environment must be 'none'")
        # Non-Latin scripts and diacritics are not reliably legible in a terminal.
        doc.setdefault("presentation", "html")
    presentation = doc.setdefault("presentation", "chat")
    _require(presentation in PRESENTATIONS,
             "presentation must be one of %s" % list(PRESENTATIONS))
    _require(not (doc["archetype"] == "C" and presentation != "html"),
             "archetype C must use presentation 'html'; a terminal cannot render "
             "furigana, CJK column widths, or missing-glyph fallbacks reliably")
    concepts = doc.get("concepts")
    _require(isinstance(concepts, list) and concepts, "concepts must be a non-empty list")
    ids = set()
    for c in concepts:
        _require(isinstance(c, dict), "each concept must be an object")
        cid = c.get("id")
        _require(isinstance(cid, str) and cid, "concept.id is required")
        _require(cid not in ids, "duplicate concept id: %s" % cid)
        ids.add(cid)
        for field in ("importance", "goal_relevance"):
            val = c.get(field, 1.0)
            _require(isinstance(val, (int, float)) and 0.5 <= val <= 1.5,
                     "%s.%s must be between 0.5 and 1.5" % (cid, field))
    for c in concepts:
        for p in c.get("prerequisites", []):
            _require(p in ids, "%s lists unknown prerequisite %s" % (c["id"], p))
    _detect_cycles(concepts)
    return doc


def _detect_cycles(concepts):
    graph = dict((c["id"], list(c.get("prerequisites", []))) for c in concepts)
    state = {}

    def visit(node, trail):
        if state.get(node) == "done":
            return
        if state.get(node) == "open":
            raise UpskillError("prerequisite cycle: %s" % " -> ".join(trail + [node]))
        state[node] = "open"
        for parent in graph.get(node, []):
            visit(parent, trail + [node])
        state[node] = "done"

    for node in graph:
        visit(node, [])


def validate_evidence(doc):
    _require(isinstance(doc, dict), "evidence must be an object")
    records = doc.get("records")
    _require(isinstance(records, list), "evidence.records must be a list")
    for r in records:
        _require(isinstance(r, dict), "each evidence record must be an object")
        _require(isinstance(r.get("concept"), str), "evidence.concept is required")
        _require(r.get("level") in LEVEL_WEIGHT, "evidence.level must be 1..4")
        _require(r.get("source") in SOURCE_WEIGHT,
                 "evidence.source must be one of %s" % sorted(SOURCE_WEIGHT))
        score = r.get("score")
        _require(isinstance(score, (int, float)) and 0.0 <= score <= 1.0,
                 "evidence.score must be between 0 and 1")
    return doc


# --------------------------------------------------------------------------
# Surmise implication (Doignon & Falmagne 1985, borrowed direction only)
# --------------------------------------------------------------------------

def transitive_prerequisites(concepts, concept_id):
    graph = dict((c["id"], list(c.get("prerequisites", []))) for c in concepts)
    seen = set()
    stack = list(graph.get(concept_id, []))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(graph.get(node, []))
    return seen


def derive_implied(concepts, records):
    """Strong performance on a hard item implies its prerequisites.

    Kept deliberately weak: score 0.8 at half weight, at most one implied
    record per concept, and never enough on its own to call something mastered.

    Direct evidence always wins. A concept that has been measured directly is
    never given an implied record -- otherwise a downstream success would both
    soften a genuine failure and drag down a concept that already scored higher
    than the implied value.
    """
    measured = set(r["concept"] for r in records
                   if r.get("source") != "implied" and not r.get("disputed"))
    best = {}
    for r in records:
        if r.get("disputed"):
            continue
        if r.get("source") == "implied":
            continue
        if r["level"] < IMPLY_MIN_LEVEL or r["score"] < IMPLY_MIN_SCORE:
            continue
        weight = LEVEL_WEIGHT[r["level"]] * SOURCE_WEIGHT["implied"]
        for parent in transitive_prerequisites(concepts, r["concept"]):
            if parent in measured:
                continue
            current = best.get(parent)
            if current is None or weight > current["weight"]:
                best[parent] = {"weight": weight, "from": r.get("item_id", r["concept"])}
    implied = []
    for concept_id, info in sorted(best.items()):
        implied.append({
            "item_id": "implied:%s" % info["from"],
            "concept": concept_id,
            "level": 1,
            "answer_mode": "implied",
            "score": IMPLIED_SCORE,
            "source": "implied",
            "disputed": False,
            "implied_from": info["from"],
            "_weight": info["weight"],
        })
    return implied


# --------------------------------------------------------------------------
# Mastery
# --------------------------------------------------------------------------

def record_weight(record):
    if record.get("disputed"):
        return 0.0
    if "_weight" in record:
        return record["_weight"]
    return LEVEL_WEIGHT[record["level"]] * SOURCE_WEIGHT[record["source"]]


def compute_mastery(competency, evidence_records, archetype=None):
    concepts = competency["concepts"]
    archetype = archetype or competency.get("archetype", "A")
    policy = ARCHETYPES[archetype]

    direct = [r for r in evidence_records if not r.get("disputed")]
    all_records = direct + derive_implied(concepts, direct)

    by_concept = {}
    for c in concepts:
        by_concept[c["id"]] = []
    for r in all_records:
        by_concept.setdefault(r["concept"], []).append(r)

    result = {}
    for concept_id, records in by_concept.items():
        num = 0.0
        den = 0.0
        direct_count = 0
        max_direct_level = 0
        has_review = False
        last_at = None
        for r in records:
            w = record_weight(r)
            num += r["score"] * w
            den += w
            if r["source"] != "implied":
                direct_count += 1
                if r["level"] > max_direct_level:
                    max_direct_level = r["level"]
            if r["source"] == "review":
                has_review = True
            stamp = r.get("timestamp")
            if stamp and (last_at is None or stamp > last_at):
                last_at = stamp
        value = (num / den) if den else 0.0
        result[concept_id] = {
            "value": round(value, 4),
            "evidence_count": len(records),
            "direct_count": direct_count,
            "max_direct_level": max_direct_level,
            "status": _status_for(value, len(records), direct_count,
                                  max_direct_level, has_review, policy),
            "last_evidence_at": last_at,
        }
    return result


def _status_for(value, count, direct_count, max_direct_level, has_review, policy):
    if count == 0:
        return "unknown"
    if direct_count == 0:
        # Only surmise-implied evidence: assume it is fine, do not call it mastery.
        return "assumed-ok"
    if value < BAND_FOUNDATION:
        return "foundation"
    if value < BAND_DEVELOPING:
        return "developing"
    if value < BAND_PROFICIENT:
        return "proficient"
    # advanced needs hard direct evidence, and for language work, spaced evidence
    if max_direct_level < policy["advanced_requires_level"]:
        return "proficient"
    if policy["review_required_for_mastery"] and not has_review:
        return "proficient"
    return "advanced"


# --------------------------------------------------------------------------
# Priority + diagnostic control
# --------------------------------------------------------------------------

def direct_dependents(concepts, concept_id):
    return [c["id"] for c in concepts if concept_id in c.get("prerequisites", [])]


def priority(concept, mastery_value, concepts):
    gap = 1.0 - max(0.0, min(1.0, mastery_value))
    dependents = len(direct_dependents(concepts, concept["id"]))
    prereq_factor = 1.0 + min(dependents, 4) * 0.10
    return round(gap
                 * float(concept.get("goal_relevance", 1.0))
                 * float(concept.get("importance", 1.0))
                 * prereq_factor, 4)


def _is_resolved(entry, records_for_concept):
    """During the diagnostic we only need to know where to start.

    One clear piece of evidence is enough. A second item is required only when
    the single result is ambiguous. Declaring mastery is a separate, stricter
    bar handled by _status_for.
    """
    if entry["evidence_count"] == 0:
        return False
    direct = [r for r in records_for_concept if r.get("source") != "implied"]
    if not direct:
        return True  # covered by surmise; ask about it only if a lesson fails
    if len(direct) >= 2:
        return True
    only = direct[0]["score"]
    return not (AMBIGUOUS_LOW < only < AMBIGUOUS_HIGH)


def next_probe(competency, evidence_records, asked_count):
    """Return the next concept/level to probe, or a stop decision."""
    concepts = competency["concepts"]
    archetype = competency.get("archetype", "A")
    policy = ARCHETYPES[archetype]
    mastery = compute_mastery(competency, evidence_records, archetype)

    grouped = {}
    for r in evidence_records:
        if not r.get("disputed"):
            grouped.setdefault(r["concept"], []).append(r)

    unresolved = []
    for c in concepts:
        entry = mastery[c["id"]]
        if not _is_resolved(entry, grouped.get(c["id"], [])):
            unresolved.append((priority(c, entry["value"], concepts), c["id"], c))

    if not unresolved:
        return {"stop": True, "stop_reason": "all concepts resolved",
                "asked": asked_count, "next_probe": None}
    if asked_count >= policy["max_diagnostic_items"]:
        return {"stop": True,
                "stop_reason": "reached max_diagnostic_items (%d); %d concept(s) left unknown"
                               % (policy["max_diagnostic_items"], len(unresolved)),
                "asked": asked_count,
                "unresolved": [c[1] for c in unresolved],
                "next_probe": None}

    unresolved.sort(key=lambda t: (-t[0], t[1]))
    _, concept_id, concept = unresolved[0]
    return {"stop": False, "stop_reason": None, "asked": asked_count,
            "next_probe": {"concept": concept_id,
                           "level": _probe_level(grouped.get(concept_id, [])),
                           "why": "highest unresolved priority (%.3f)" % unresolved[0][0]}}


def _probe_level(records):
    direct = [r for r in records if r.get("source") != "implied"]
    if not direct:
        return 2  # start mid so one item can discriminate in either direction
    last = direct[-1]
    if last["score"] < 0.5:
        return max(1, last["level"] - 1)   # find the floor
    return min(4, last["level"] + 1)       # find the ceiling


# --------------------------------------------------------------------------
# Planning
# --------------------------------------------------------------------------

def _module_kind(entry):
    if entry["status"] == "unknown":
        return "diagnose"
    if entry["status"] == "assumed-ok":
        return "verify"
    value = entry["value"]
    if value < BAND_FOUNDATION:
        return "foundation"
    if value < BAND_DEVELOPING:
        return "targeted-practice"
    if value < BAND_PROFICIENT:
        return "application"
    return "extension"


def build_plan(competency, mastery, minutes_per_week=None):
    concepts = competency["concepts"]
    by_id = dict((c["id"], c) for c in concepts)

    locked = []
    for c in concepts:
        blockers = []
        for p in c.get("prerequisites", []):
            entry = mastery.get(p, {"value": 0.0, "status": "unknown"})
            if entry["status"] in ("unknown", "foundation") or entry["value"] < PREREQ_GATE:
                blockers.append(p)
        if blockers:
            locked.append({"concept": c["id"], "blocked_by": sorted(blockers)})
    locked_ids = set(l["concept"] for l in locked)

    candidates = []
    skipped = []
    for c in concepts:
        entry = mastery.get(c["id"], {"value": 0.0, "status": "unknown",
                                      "evidence_count": 0, "direct_count": 0})
        kind = _module_kind(entry)
        if kind == "extension" and float(c.get("goal_relevance", 1.0)) < 1.2:
            skipped.append({
                "concept": c["id"],
                "reason": "demonstrated mastery and not central to the stated goal",
                "evidence": "mastery %.2f from %d evidence item(s), status %s"
                            % (entry["value"], entry["evidence_count"], entry["status"]),
            })
            continue
        if c["id"] in locked_ids:
            continue  # its blockers are scheduled instead
        candidates.append((priority(c, entry["value"], concepts), c, entry, kind))

    candidates.sort(key=lambda t: (-t[0], t[1]["id"]))

    modules = []
    used_minutes = 0
    for score, concept, entry, kind in candidates:
        minutes = int(concept.get("estimated_minutes", 45))
        if kind in ("application", "extension", "verify"):
            minutes = max(15, minutes // 2)
        blocking = [d for d in direct_dependents(concepts, concept["id"])
                    if d in locked_ids]
        modules.append({
            "order": len(modules) + 1,
            "concept": concept["id"],
            "label": concept.get("label", concept["id"]),
            "kind": kind,
            "priority": score,
            "why": _why(concept, entry, kind, blocking),
            "exit_criterion": _exit_criterion(kind, concept),
            "estimated_minutes": minutes,
        })
        used_minutes += minutes

    plan = {
        "version": SCHEMA_VERSION,
        "subject": competency.get("subject"),
        "archetype": competency.get("archetype"),
        "generated_at": now_iso(),
        "modules": modules,
        "skipped": skipped,
        "locked": locked,
        "total_estimated_minutes": used_minutes,
    }
    if minutes_per_week:
        plan["estimated_weeks"] = round(used_minutes / float(minutes_per_week), 1)
    return plan


def _why(concept, entry, kind, blocking):
    bits = ["mastery %.2f (%s)" % (entry["value"], entry["status"])]
    if entry.get("evidence_count") is not None:
        bits.append("%d evidence item(s)" % entry["evidence_count"])
    if blocking:
        bits.append("unblocks %s" % ", ".join(sorted(blocking)))
    if float(concept.get("goal_relevance", 1.0)) >= 1.2:
        bits.append("directly serves the stated goal")
    if kind == "diagnose":
        bits.append("no evidence yet, so it is measured before it is taught")
    return "; ".join(bits)


def _exit_criterion(kind, concept):
    label = concept.get("label", concept["id"])
    return {
        "diagnose": "answer 1-2 items on %s so it stops being unknown" % label,
        "verify": "confirm %s directly instead of relying on an implied result" % label,
        "foundation": "explain %s and apply it to a fresh basic case" % label,
        "targeted-practice": "solve two %s problems without hints" % label,
        "application": "apply %s in a scenario that is not a copy of the example" % label,
        "extension": "combine %s with another concept and defend the choice" % label,
    }[kind]


# --------------------------------------------------------------------------
# Review scheduling (retrieval practice; required for archetype C)
# --------------------------------------------------------------------------

def due_reviews(mastery, evidence_records, as_of=None):
    as_of_dt = parse_iso(as_of or now_iso())
    boxes = {}
    for r in evidence_records:
        if r.get("source") == "review" and not r.get("disputed"):
            key = r["concept"]
            if r["score"] >= BAND_DEVELOPING:
                boxes[key] = min(len(REVIEW_INTERVALS_DAYS) - 1, boxes.get(key, 0) + 1)
            else:
                boxes[key] = 0

    due = []
    for concept_id, entry in sorted(mastery.items()):
        if entry["status"] in ("unknown", "foundation"):
            continue  # still being learned; not a review candidate
        last = parse_iso(entry.get("last_evidence_at"))
        if last is None or as_of_dt is None:
            continue
        box = boxes.get(concept_id, 0)
        interval = REVIEW_INTERVALS_DAYS[box]
        if as_of_dt - last >= timedelta(days=interval):
            due.append({
                "concept": concept_id,
                "box": box,
                "interval_days": interval,
                "days_since": (as_of_dt - last).days,
                "status": entry["status"],
            })
    due.sort(key=lambda d: (-d["days_since"], d["concept"]))
    return due


# --------------------------------------------------------------------------
# Workspace helpers
# --------------------------------------------------------------------------

def workspace(subject, root=None):
    base = root or os.environ.get("UPSKILL_ROOT") or os.path.join(os.getcwd(), ".upskill")
    return os.path.join(base, subject)


def paths(subject, root=None):
    ws = workspace(subject, root)
    return {
        "workspace": ws,
        "competency": os.path.join(ws, "competency.json"),
        "evidence": os.path.join(ws, "evidence.json"),
        "progress": os.path.join(ws, "progress.json"),
        "plan": os.path.join(ws, "plan.json"),
        "items": os.path.join(ws, "items"),
        "lessons": os.path.join(ws, "lessons"),
    }


def load_state(subject, root=None):
    p = paths(subject, root)
    competency = validate_competency(read_json(p["competency"]))
    evidence = validate_evidence(read_json(p["evidence"]))
    return competency, evidence, p


def refresh_progress(competency, evidence, existing=None):
    mastery = compute_mastery(competency, evidence["records"])
    progress = dict(existing or {})
    progress.update({
        "version": SCHEMA_VERSION,
        "subject": competency.get("subject"),
        "archetype": competency.get("archetype"),
        "goal": competency.get("goal"),
        "mastery": mastery,
        "evidence_total": len(evidence["records"]),
        "updated_at": now_iso(),
    })
    progress.setdefault("plan_version", 0)
    progress.setdefault("completed_lessons", [])
    return progress, mastery


def die(message):
    sys.stderr.write("upskill: %s\n" % message)
    sys.exit(2)
