"""Story implementation pipeline.

Runs an orchestrator agent session that dispatches the `python-implementer`
and `code-reviewer` subagents (defined in .claude/agents/) in a bounded
retry loop, scoped to product/. No git/PR actions happen here — see ship.py.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

from devtools.user_stories import Story, load_story, mark_criterion_done

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"


def _load_agent_body(name: str) -> str:
    """Read a .claude/agents/<name>.md persona, stripped of its YAML frontmatter."""
    text = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    _, _, body = text.split("---", 2)
    return body.strip()


def _build_task_prompt(story: Story) -> str:
    criteria_lines = "\n".join(
        f"- [{'x' if c.done else ' '}] {c.text}" for c in story.criteria
    )
    return f"""Story {story.id}: {story.title}

{story.body}

Acceptance criteria:
{criteria_lines}
"""


def _extract_text(message: object) -> str:
    if isinstance(message, AssistantMessage):
        return "\n".join(
            block.text for block in message.content if isinstance(block, TextBlock)
        )
    return ""


async def _run(story_id: str) -> bool:
    story = load_story(story_id)
    options = ClaudeAgentOptions(
        cwd=str(REPO_ROOT),
        setting_sources=["project"],
        system_prompt=_load_agent_body("orchestrator"),
        allowed_tools=[
            "Agent",
            "Read(product/**)",
            "Write(product/**)",
            "Edit(product/**)",
            "Glob(product/**)",
            "Grep(product/**)",
        ],
        permission_mode="dontAsk",
    )

    transcript: list[str] = []
    async for message in query(prompt=_build_task_prompt(story), options=options):
        text = _extract_text(message)
        if text:
            transcript.append(text)
        if isinstance(message, ResultMessage) and message.is_error:
            print(f"Orchestrator error: {message.result}")
            return False

    full_text = "\n".join(transcript)
    print(full_text)

    if "OUTCOME: SUCCESS" not in full_text:
        return False

    for criterion in story.criteria:
        if not criterion.done:
            mark_criterion_done(story.id, criterion.text)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Implement a user story via the agent pipeline.")
    parser.add_argument("story_id", help="Story ID, e.g. US-01")
    args = parser.parse_args()

    success = asyncio.run(_run(args.story_id))
    if not success:
        raise SystemExit(f"{args.story_id} not fully satisfied. See transcript above.")
    print(f"{args.story_id}: all acceptance criteria marked done.")
