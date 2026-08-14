# 12 — HTML lessons

Read this when `presentation` is `html`. That is always true for language subjects and
optional for anything whose material needs tables, annotation, or typed answers.

## The rule that keeps this cheap

**You write a JSON payload. You never write HTML.**

`assets/lesson-shell.html` is fixed, written once, and reused for every lesson in every
subject. `render_lesson.py` drops your payload into it.

Measured on a real Japanese lesson: **2.0 KB of JSON in, 15.8 KB of HTML out**, with a
13.8 KB shell that costs nothing after the first time. Authoring the page by hand costs
roughly eight times as much per lesson and produces a different layout, different
keyboard behaviour, and different bugs every time.

```bash
python3 $SCRIPTS/render_lesson.py --subject <s> --lesson <lesson.json>
```

## Payload

```json
{
  "lesson_id": "ja-mail-openings-01",
  "title": "メール[めーる]の書[か]き出[だ]し",
  "subject_label": "Japanese",
  "concept_label": "Email openings",
  "objective": "Open and close a business email correctly",
  "blocks": [
    {"type": "prose", "text": "Two paragraphs, separated\n\nby a blank line."},
    {"type": "example",
     "target": "お世話[せわ]になっております。",
     "gloss": "Thank you for your continued support.",
     "note": "To a first contact, use 初[はじ]めて… instead."},
    {"type": "table", "title": "Core set",
     "columns": ["Expression", "When", "Literal"],
     "rows": [["お世話[せわ]になっております", "Existing contact", "you are taking care of us"]]}
  ],
  "items": [
    {"id": "q1", "type": "choice", "concept": "ja-mail-openings", "level": 1,
     "prompt": "Second email to a client. Which opener?",
     "choices": ["初[はじ]めてご連絡[れんらく]いたします。", "お世話[せわ]になっております。"],
     "answer": 1,
     "why": "初めて is for a first contact."},
    {"id": "q2", "type": "cloze", "concept": "ja-mail-openings", "level": 2,
     "prompt": "よろしくお____いいたします。 (kana only)",
     "answer": "ねが", "hint": "The verb is 願う."},
    {"id": "q3", "type": "free", "concept": "ja-request-polite", "level": 3,
     "prompt": "Write two lines: open the email, then ask for the invoice by Friday."}
  ]
}
```

### Ruby annotation

`漢字[かんじ]` renders as ruby text above the characters. It works in prose, examples,
table cells, prompts, choices, and hints. Annotate a reading the first time it appears in
a lesson, then stop — annotating everything defeats the purpose.

The parser splits on whitespace, so `漢字[かんじ]` works and `この 漢字 [かんじ]` does not.

### Item types

| `type` | Learner does | Graded |
|---|---|---|
| `choice` | picks one option | in the page |
| `cloze` | types a short answer | in the page |
| `free` | writes freely | **by you**, against a rubric you wrote first |

`answer` for `choice` is the index, or the exact choice string. For `cloze` it is the
expected text. Add `"strict": true` when case matters — comparison is otherwise
case-insensitive after NFC normalisation and whitespace collapsing.

Give `cloze` items a `placeholder` when the expected form is ambiguous ("kana only",
"one word"). Half the wrong answers in a language lesson are format mismatches, and those
teach nothing.

`why` is shown after a correct answer. Use it for the discrimination the item was
testing, not for praise.

## Answers are hashed, not stored

`render_lesson.py` replaces every `answer` with a hash before writing the page, so
viewing source does not spoil the lesson. The hash is FNV-1a, matched byte-for-byte
between the script and the page.

It is **not cryptographic** — the goal is to stop answers appearing accidentally in front
of a learner, not to resist someone determined to extract them. Say so if asked.

## Getting results back

The learner presses Grade and the page produces:

```
UPSKILL_RESULT ja-mail-openings-01 2/2

--- free responses (paste these too) ---
[q3] お世話になっております。金曜日までに請求書をお送りいただけますでしょうか。
```

```bash
python3 $SCRIPTS/upskill.py ingest --subject <s> --output "<the whole paste>" --checkpoint
```

`ingest` records the graded items. **The free responses are still yours to grade** —
apply the rubric you wrote when authoring the item, then record it separately with
`update`. Do not let a free response ride along on the automatic count.

Progress is kept in `localStorage`, so a half-finished page survives a closed tab. That
is convenience only; nothing in the browser is evidence until it is ingested.

## What the shell already handles

Do not rebuild any of this in your payload:

- light and dark, following the system setting
- a font stack covering CJK, Latin diacritics and IPA
- keyboard operation and visible focus
- horizontal scrolling for wide tables
- all learner text inserted as text nodes, never as HTML

## Limits worth stating

- The page cannot play audio, so listening is still unmeasured.
- A `cloze` item accepts exactly one spelling. Where several answers are legitimately
  correct, use `choice`, or make it `free` and grade it.
- Nothing here is a secure context; treat the file as readable by whoever has the disk.
