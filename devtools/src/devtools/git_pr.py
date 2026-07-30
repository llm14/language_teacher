"""Deterministic commit/PR message templating. No LLM-generated text here."""

from __future__ import annotations

from devtools.user_stories import Story


def commit_message(story: Story) -> str:
    return f"{story.id}: {story.title}\n\nImplements {story.id}. See USER_STORIES.md for acceptance criteria.\n"


def pr_title(story: Story) -> str:
    return f"{story.id}: {story.title}"


def pr_body(story: Story) -> str:
    lines = [f"Implements {story.id} (see USER_STORIES.md).", "", "### Acceptance Criteria"]
    for criterion in story.criteria:
        box = "x" if criterion.done else " "
        lines.append(f"- [{box}] {criterion.text}")
    return "\n".join(lines) + "\n"
