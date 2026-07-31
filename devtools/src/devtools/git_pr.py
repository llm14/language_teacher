"""Deterministic commit/PR message templating. No LLM-generated text here."""

from __future__ import annotations

from devtools.user_stories import Story


def _extra_changes_block(extra_message: str | None, extra_paths: list[str] | None) -> str:
    if not extra_message:
        return ""
    block = f"\nAlso includes:\n{extra_message}\n"
    if extra_paths:
        files = "\n".join(f"- {path}" for path in extra_paths)
        block += f"\nFiles:\n{files}\n"
    return block


def commit_message(
    story: Story, extra_message: str | None = None, extra_paths: list[str] | None = None
) -> str:
    base = f"{story.id}: {story.title}\n\nImplements {story.id}. See USER_STORIES.md for acceptance criteria.\n"
    return base + _extra_changes_block(extra_message, extra_paths)


def pr_title(story: Story) -> str:
    return f"{story.id}: {story.title}"


def pr_body(
    story: Story, extra_message: str | None = None, extra_paths: list[str] | None = None
) -> str:
    lines = [f"Implements {story.id} (see USER_STORIES.md).", "", "### Acceptance Criteria"]
    for criterion in story.criteria:
        box = "x" if criterion.done else " "
        lines.append(f"- [{box}] {criterion.text}")
    if extra_message:
        lines += ["", "### Also includes", extra_message]
        if extra_paths:
            lines += ["", "Files:"] + [f"- {path}" for path in extra_paths]
    return "\n".join(lines) + "\n"
