"""Parsing and updating of USER_STORIES.md."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

USER_STORIES_PATH = Path(__file__).resolve().parents[3] / "USER_STORIES.md"

_STORY_HEADER_RE = re.compile(r"^## (US-\d+): (.+)$", re.MULTILINE)
_CRITERION_RE = re.compile(r"^- \[( |x)\] (.+)$", re.MULTILINE)


@dataclass
class AcceptanceCriterion:
    text: str
    done: bool


@dataclass
class Story:
    id: str
    title: str
    body: str
    criteria: list[AcceptanceCriterion] = field(default_factory=list)

    @property
    def all_done(self) -> bool:
        return all(c.done for c in self.criteria)


def _find_story_span(text: str, story_id: str) -> tuple[str, str, int, int]:
    """Return (title, body, body_start, body_end) for a story's markdown block."""
    matches = list(_STORY_HEADER_RE.finditer(text))
    for i, match in enumerate(matches):
        if match.group(1) == story_id:
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return match.group(2).strip(), text[start:end], start, end
    raise ValueError(f"{story_id} not found")


def load_story(story_id: str, path: Path = USER_STORIES_PATH) -> Story:
    text = path.read_text(encoding="utf-8")
    title, body, _, _ = _find_story_span(text, story_id)
    criteria = [
        AcceptanceCriterion(text=match.group(2).strip(), done=match.group(1) == "x")
        for match in _CRITERION_RE.finditer(body)
    ]
    return Story(id=story_id, title=title, body=body.strip("\n"), criteria=criteria)


def mark_criterion_done(
    story_id: str, criterion_text: str, path: Path = USER_STORIES_PATH
) -> bool:
    """Check off one acceptance-criteria box for a story. Returns False if not found or already done."""
    text = path.read_text(encoding="utf-8")
    _, body, start, end = _find_story_span(text, story_id)
    updated_body, count = re.subn(
        rf"^- \[ \] {re.escape(criterion_text)}$",
        f"- [x] {criterion_text}",
        body,
        count=1,
        flags=re.MULTILINE,
    )
    if count == 0:
        return False
    path.write_text(text[:start] + updated_body + text[end:], encoding="utf-8")
    return True
