# 10 — UI contract

Read this only when producing the HTML dashboard. It is the last thing built, on purpose:
a good-looking dashboard over a weak learning engine is the failure mode this ordering
avoids.

## The dashboard is a renderer

It reads `progress.json` and `plan.json` and displays them. It **never** writes learner
state. Nothing that happens in the browser is evidence. If a number can only be obtained
by opening the page, the design is wrong.

## Hard requirements

- **One file.** Inline CSS and JS. No build step — it opens from `file://`.
- **No network.** Zero external requests: no CDN, no fonts, no images, no analytics.
  Verify with the browser's network tab; the count must be zero.
- **No secrets.** No API keys, no tokens, no provider identifiers. Grep before shipping.
- **Keyboard usable.** Every control reachable by Tab, activatable by Enter or Space,
  with a visible focus ring. Never remove the outline without replacing it.
- **Semantic markup.** Real `<button>`, `<table>`, headings in order. `<progress>` for
  bars.
- **Never `innerHTML` with file content.** Concept labels and goals are learner text.
  Use `textContent` and `createElement`.
- **Readable in both themes.** Define colors for light, override under
  `@media (prefers-color-scheme: dark)`, and set an explicit background on `body`.
- **Never color alone.** Status must be legible in the text, not only in a swatch.

## What it shows

1. **Goal and progress** — the stated outcome, modules done over total.
2. **Mastery table** — concept, mastery, evidence count, how much was direct vs implied,
   status. Show the counts; a bar alone hides that 0.91 came from one easy item.
3. **Next recommended module with its `why`** — the reason is not decoration. A plan
   the learner cannot audit is a grade, not feedback.
4. **Skipped, with reasons and evidence.**
5. **Locked by prerequisites**, and what unlocks each.
6. **Due reviews** for archetype C.

Mark `assumed-ok` visibly distinct from measured statuses. It is the one place the
dashboard could quietly overstate what is known.

## What it must not show

- A single overall percentage as the headline. It hides the distribution that the whole
  system exists to surface.
- Streaks, badges, or anything that rewards activity over evidence.
- A mastery number presented as a validated measurement.

## Generating

```bash
python3 $SCRIPTS/upskill.py status --subject <s> --json
```

Fill `assets/dashboard-shell.html` with that data. **Do not author fresh HTML per
subject** — the shell is fixed and the content is injected, so accessibility and layout
stay tested instead of being re-improvised each time.

Write to `.upskill/<subject>/dashboard.html` and tell the learner the path. Do not offer
it as a download link; opening the file is the way.
