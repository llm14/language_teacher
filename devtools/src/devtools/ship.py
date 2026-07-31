"""Deterministic ship pipeline: test, lint, commit, push, open PR.

No LLM calls happen here. Requires the story's acceptance criteria to
already be fully checked off before it will commit anything. Commits every
changed file in the repo, not just product/ and USER_STORIES.md; anything
outside that scope must be described via --message since there's no story
to derive a commit message from.
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


def _changed_paths() -> list[str]:
    result = _run(["git", "status", "--porcelain"], REPO_ROOT)
    paths = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def _is_story_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized == "USER_STORIES.md" or normalized.startswith("product/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test, lint, commit and open a PR for a story.")
    parser.add_argument("story_id", help="Story ID, e.g. US-01")
    parser.add_argument(
        "--message",
        "-m",
        default=None,
        help="Description of changes outside product/ and USER_STORIES.md. "
        "Required whenever such changes are present.",
    )
    args = parser.parse_args()

    story = load_story(args.story_id)
    if not story.all_done:
        unchecked = [c.text for c in story.criteria if not c.done]
        print(f"{story.id} has unmet acceptance criteria, refusing to ship:")
        for text in unchecked:
            print(f"  - {text}")
        raise SystemExit(1)

    extra_paths = sorted(p for p in _changed_paths() if not _is_story_path(p))
    if extra_paths and not args.message:
        print("Changes outside product/ and USER_STORIES.md need --message to describe them:")
        for path in extra_paths:
            print(f"  - {path}")
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

    _run(["git", "add", "-A"], REPO_ROOT)
    message = commit_message(story, extra_message=args.message, extra_paths=extra_paths)
    commit = _run(["git", "commit", "-m", message], REPO_ROOT)
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
            pr_body(story, extra_message=args.message, extra_paths=extra_paths),
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
