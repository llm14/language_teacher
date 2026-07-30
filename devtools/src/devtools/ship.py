"""Deterministic ship pipeline: test, lint, commit, push, open PR.

No LLM calls happen here. Requires the story's acceptance criteria to
already be fully checked off by `implement` before it will commit anything.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from devtools.git_pr import commit_message, pr_body, pr_title
from devtools.user_stories import load_story

REPO_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_DIR = REPO_ROOT / "product"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def _current_branch() -> str:
    result = _run(["git", "branch", "--show-current"], REPO_ROOT)
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Test, lint, commit and open a PR for a story.")
    parser.add_argument("story_id", help="Story ID, e.g. US-01")
    args = parser.parse_args()

    story = load_story(args.story_id)
    if not story.all_done:
        unchecked = [c.text for c in story.criteria if not c.done]
        print(f"{story.id} has unmet acceptance criteria, refusing to ship:")
        for text in unchecked:
            print(f"  - {text}")
        raise SystemExit(1)

    for label, cmd in (
        ("pytest", ["uv", "run", "pytest"]),
        ("ruff", ["uv", "run", "ruff", "check", "."]),
    ):
        result = _run(cmd, PRODUCT_DIR)
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            print(f"{label} failed, refusing to ship.")
            raise SystemExit(1)

    branch = _current_branch()
    if branch in ("main", "master", ""):
        branch = f"impl/{story.id.lower()}"
        checkout = _run(["git", "checkout", "-b", branch], REPO_ROOT)
        if checkout.returncode != 0:
            print(checkout.stderr, file=sys.stderr)
            raise SystemExit(1)

    _run(["git", "add", "product", "USER_STORIES.md"], REPO_ROOT)
    commit = _run(["git", "commit", "-m", commit_message(story)], REPO_ROOT)
    print(commit.stdout)
    if commit.returncode != 0:
        print(commit.stderr, file=sys.stderr)
        raise SystemExit(1)

    push = _run(["git", "push", "-u", "origin", branch], REPO_ROOT)
    print(push.stdout)
    if push.returncode != 0:
        print(push.stderr, file=sys.stderr)
        raise SystemExit(1)

    pr = _run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            pr_title(story),
            "--body",
            pr_body(story),
            "--base",
            "main",
            "--head",
            branch,
        ],
        REPO_ROOT,
    )
    print(pr.stdout)
    if pr.returncode != 0:
        print(pr.stderr, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
