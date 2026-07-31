---
name: ship
description: >
  Test, lint, commit, push, and open a PR for a user story via devtools' deterministic
  ship.py (uv run ship). Classifies working-tree changes into story-scoped (product/,
  USER_STORIES.md) vs everything else, previews the branch/commit message/PR body, and
  confirms with the user before pushing or opening the PR. Use when the user says
  "ship this", "commit and push", "open a PR", or invokes /ship.
---

# Ship a story

`devtools/src/devtools/ship.py` (invoked via `uv run ship <story-id>`) is the deterministic
source of truth for shipping: it runs pytest + ruff, commits every changed file, pushes,
and opens a PR. It refuses to run if the story's acceptance criteria in USER_STORIES.md
aren't fully checked off, and refuses to commit non-story changes (anything outside
`product/` and `USER_STORIES.md`) unless given `--message`. Never reimplement its logic —
this skill's job is to gather what it needs and get the user's confirmation before it pushes.

## Steps

1. **Identify the story.** If not given explicitly, look at `USER_STORIES.md` headers
   (`## US-NN: ...`) and the current branch name to find the best match; ask if ambiguous.
2. **Check acceptance criteria** for that story in USER_STORIES.md. If any are unchecked,
   stop and tell the user — `ship` will refuse anyway.
3. **Classify the working tree.** Run `git status --porcelain` from the repo root. A path
   is "story-scoped" iff it is exactly `USER_STORIES.md` or starts with `product/`;
   everything else is "extra".
4. **Get a message for extra changes.** If any extra paths exist, ask the user for a
   one-line description (unless they already gave one in their request) — this becomes
   `--message`.
5. **Preview before running anything.** Show the user: the current branch (and whether
   `ship` will create `impl/<story-id>` because the branch is main/master), the
   story-scoped paths, the extra paths, and the `--message` text. This is the confirmation
   point — push and PR creation are not easily reversible, so do not run step 6 without
   explicit go-ahead.
6. **Run it**: `uv --directory devtools run ship <story-id> --message "<text>"` (omit
   `--message` entirely if there were no extra paths). Stream its output to the user.
7. **Report the result** — the PR URL on success, or the exact refusal reason (unmet
   criteria / failing tests / failing lint / missing message) on failure. Don't retry
   automatically; let the user decide the next step.

## Notes

- This never bypasses `ship.py`'s checks — if it refuses, the skill refuses too.
- If the user's request already includes both the story id and a description of the extra
  changes, you can skip asking and go straight to the step 5 preview.
