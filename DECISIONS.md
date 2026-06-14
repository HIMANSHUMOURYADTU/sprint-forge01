# DECISIONS.md - decision & learnings log

A short running note of the real choices you made: what you tried, what failed and why, what
you changed. This is your engineering judgement on the record - it is what separates a builder
from a button-presser, and it is graded (from git history + this file + PROMPTS.md, NOT from
an auto audit log, which may be empty on cloud models).

Append a 1-2 line entry whenever you make a real decision or hit/fix a wall. Add a timestamp.

Format:
`[HH:MM] <decision or problem> -> <what you did and why>`

---

## Example (replace with your own)
- `[10:20]` Used `Unique Inlinks` for orphan detection, not `Inlinks` -> `Inlinks` counts
  duplicate links (nav appearing twice), so it never hits 0; `Unique Inlinks` is the real
  orphan signal.
- `[11:05]` Path-segment clustering merged unrelated root pages -> kept it as the starter but
  added TF keywords so the topic-agent can split/name them properly.
- `[12:40]` Dashboard not updating live -> server tool wasn't emitting the SSE event; added
  `_emit(...)` in each li_* tool.

---

## My log
- `[--:--]` ...
