#!/usr/bin/env python3
"""Render a lesson JSON into the fixed HTML shell. Python 3.8, stdlib only.

Why this exists, in two parts.

Legibility: a terminal cannot show furigana, gets CJK column widths wrong, and
renders diacritics at the mercy of whatever font is installed. Language study is
unworkable there. HTML fixes all of it.

Cost: the model must never author the page. It writes a small JSON payload -- the
sentences, the glosses, the items -- and this script drops it into a shell that was
written once. A lesson costs roughly the JSON, not roughly a web page.

    python3 render_lesson.py --subject japanese --lesson lesson.json

Answers are stored as hashes, so opening the page source does not spoil them.
The hash is FNV-1a and matches the identical function in the shell.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import upskill_core as core  # noqa: E402

SHELL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "assets", "lesson-shell.html")
PLACEHOLDER = '<script id="lesson-data" type="application/json">{}</script>'


def fnv1a(text):
    """32-bit FNV-1a over UTF-16 code units.

    Must agree with the shell's hash() for every input. JavaScript's charCodeAt
    yields UTF-16 code units, so anything outside the BMP is two values there and
    one code point in Python -- iterating Python characters would disagree on
    exactly the emoji and rare kanji a language lesson is likely to contain.
    """
    h = 0x811c9dc5
    units = text.encode("utf-16-le")
    for i in range(0, len(units), 2):
        code = units[i] | (units[i + 1] << 8)
        h ^= code
        h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) & 0xFFFFFFFF
    return "%08x" % h


def normalize(value, strict=False):
    text = unicodedata.normalize("NFC", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text if strict else text.lower()


def prepare(lesson):
    """Replace plaintext answers with hashes and validate the payload."""
    for field in ("lesson_id", "title", "items"):
        if field not in lesson:
            raise core.UpskillError("lesson is missing required field: %s" % field)
    if not lesson["items"]:
        raise core.UpskillError("a lesson with no items produces no evidence")

    seen = set()
    gradable = 0
    for item in lesson["items"]:
        for field in ("id", "type", "prompt", "concept", "level"):
            if field not in item:
                raise core.UpskillError("item %s is missing %s"
                                        % (item.get("id", "?"), field))
        if item["id"] in seen:
            raise core.UpskillError("duplicate item id: %s" % item["id"])
        seen.add(item["id"])
        if item["type"] not in ("choice", "cloze", "free"):
            raise core.UpskillError("item %s has unknown type %s"
                                    % (item["id"], item["type"]))
        if item["type"] == "free":
            item.pop("answer", None)
            continue

        if "answer" not in item:
            raise core.UpskillError(
                "item %s needs an answer, or type 'free' if it cannot be checked"
                % item["id"])
        answer = item.pop("answer")
        if item["type"] == "choice":
            choices = item.get("choices") or []
            if isinstance(answer, int):
                index = answer
            else:
                if answer not in choices:
                    raise core.UpskillError(
                        "item %s: answer %r is not one of its choices"
                        % (item["id"], answer))
                index = choices.index(answer)
            if not 0 <= index < len(choices):
                raise core.UpskillError("item %s: answer index out of range" % item["id"])
            item["answer_hash"] = fnv1a(normalize(str(index), strict=True))
        else:
            item["answer_hash"] = fnv1a(normalize(answer, item.get("strict", False)))
        gradable += 1

    lesson["gradable_items"] = gradable
    return lesson


def manifest(lesson):
    return {
        "task_id": lesson["lesson_id"],
        "concept": lesson["items"][0]["concept"],
        "level": lesson["items"][0]["level"],
        "answer_mode": "deterministic",
        "environment": "html",
        "total_checks": lesson["gradable_items"],
        "check_names": [i["id"] for i in lesson["items"] if i.get("answer_hash")],
        "also": lesson.get("also", []),
        "free_items": [{"id": i["id"], "concept": i["concept"], "level": i["level"]}
                       for i in lesson["items"] if i["type"] == "free"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="render_lesson")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--lesson", required=True, help="lesson JSON, or - for stdin")
    parser.add_argument("--root")
    args = parser.parse_args(argv)

    lesson = json.load(sys.stdin) if args.lesson == "-" else core.read_json(args.lesson)
    try:
        lesson = prepare(lesson)
    except core.UpskillError as exc:
        core.die(str(exc))

    shell_path = os.path.normpath(SHELL)
    if not os.path.exists(shell_path):
        core.die("lesson shell not found at %s" % shell_path)
    with open(shell_path, "r", encoding="utf-8") as fh:
        shell = fh.read()
    if PLACEHOLDER not in shell:
        core.die("lesson shell no longer contains the data placeholder")

    payload = json.dumps(lesson, ensure_ascii=False, sort_keys=True)
    # </script> inside JSON would end the tag early; nothing else needs escaping.
    payload = payload.replace("</", "<\\/")
    html = shell.replace(PLACEHOLDER,
                         '<script id="lesson-data" type="application/json">%s</script>'
                         % payload)

    paths = core.paths(args.subject, args.root)
    if not os.path.isdir(paths["lessons"]):
        os.makedirs(paths["lessons"])
    out = os.path.join(paths["lessons"], lesson["lesson_id"] + ".html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    core.write_json(os.path.join(paths["items"], lesson["lesson_id"] + ".json"),
                    manifest(lesson))

    free = [i["id"] for i in lesson["items"] if i["type"] == "free"]
    print("lesson: %s" % out)
    print("items : %d gradable, %d free-response" % (lesson["gradable_items"], len(free)))
    print("")
    print("Open it in a browser:")
    print("  open %s" % out)
    print("")
    print("The learner answers there, presses Grade, and pastes the result back.")
    if free:
        print("Free responses (%s) come back as text for you to grade against your rubric."
              % ", ".join(free))
    return 0


if __name__ == "__main__":
    sys.exit(main())
