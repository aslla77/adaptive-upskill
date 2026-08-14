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


# Kana -> Hepburn romaji. Deterministic, so the renderer can accept a romaji
# answer without the learner needing a Japanese IME installed.
_ROMAJI = {
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo", "しゃ": "sha", "しゅ": "shu",
    "しょ": "sho", "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho", "にゃ": "nya",
    "にゅ": "nyu", "にょ": "nyo", "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo", "りゃ": "rya", "りゅ": "ryu",
    "りょ": "ryo", "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo", "じゃ": "ja",
    "じゅ": "ju", "じょ": "jo", "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo",
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "o", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ー": "", "っ": "*",
}


def _katakana_to_hiragana(text):
    out = []
    for ch in text:
        code = ord(ch)
        out.append(chr(code - 0x60) if 0x30A1 <= code <= 0x30F6 else ch)
    return "".join(out)


def kana_to_romaji(text):
    """Best-effort Hepburn. Returns '' when the input is not purely kana."""
    src = _katakana_to_hiragana(text)
    out = []
    i = 0
    while i < len(src):
        pair = src[i:i + 2]
        if pair in _ROMAJI:
            out.append(_ROMAJI[pair])
            i += 2
            continue
        ch = src[i]
        if ch in _ROMAJI:
            out.append(_ROMAJI[ch])
        elif ch in " \u3000":
            out.append(" ")
        else:
            return ""   # kanji or latin present; do not guess
        i += 1
    romaji = "".join(out)
    while "*" in romaji:                      # small tsu doubles the next consonant
        index = romaji.index("*")
        following = romaji[index + 1:index + 2]
        romaji = romaji[:index] + (following or "") + romaji[index + 1:]
    return romaji


def romaji_key(value):
    """Collapse the ways people spell the same romaji: spaces, macrons, long vowels."""
    text = unicodedata.normalize("NFKD", str(value)).lower()
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("-", "").replace("\u30fc", "")
    text = re.sub(r"\s+", "", text)
    for double, single in (("aa", "a"), ("ii", "i"), ("uu", "u"),
                           ("ee", "e"), ("oo", "o"), ("ou", "o")):
        text = text.replace(double, single)
    return text


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
        if item["type"] == "cloze":
            _reject_sentence_cloze(item, answer)
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
            hashes, hint = _cloze_hashes(item, answer)
            item["answer_hash"] = hashes[0]      # kept for older shells
            item["answer_hashes"] = hashes
            if hint and not item.get("accept_hint"):
                item["accept_hint"] = hint
        gradable += 1

    lesson["gradable_items"] = gradable
    return lesson


# A learner without a Japanese IME cannot type kana at all. Rather than make them
# install one, the renderer also accepts the romaji reading -- derived from the kana
# answer, so the author writes the answer once.
def _cloze_hashes(item, answer):
    strict = item.get("strict", False)
    hashes = [fnv1a(normalize(answer, strict))]
    hint = None

    romaji = kana_to_romaji(answer)
    if romaji:
        romaji_hash = fnv1a("romaji:" + romaji_key(romaji))
        if romaji_hash not in hashes:
            hashes.append(romaji_hash)
        hint = "kana or romaji"

    for alternate in item.pop("accept", []) or []:
        for candidate in (fnv1a(normalize(alternate, strict)),
                          fnv1a("romaji:" + romaji_key(alternate))):
            if candidate not in hashes:
                hashes.append(candidate)
    return hashes, hint


def _reject_sentence_cloze(item, answer):
    """Whole-sentence production must not be graded by string comparison.

    A learner who writes カフェに instead of カフェで is making exactly the mistake
    worth teaching from, and an exact-match check can only answer "wrong". Anything
    sentence-sized becomes a free item so the agent grades it against a rubric and
    can say which part was off.
    """
    text = normalize(answer, strict=True)
    words = len([w for w in re.split(r"\s+", text) if w])
    if words > 3 or len(text) > 12:
        raise core.UpskillError(
            "item %s is a cloze whose answer is a whole phrase (%r). Exact matching "
            "can only say 'wrong', which teaches nothing. Use \"type\": \"free\" and "
            "grade it against a rubric instead." % (item["id"], answer))


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
