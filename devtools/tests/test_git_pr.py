from devtools.git_pr import commit_message, pr_body, pr_title
from devtools.user_stories import AcceptanceCriterion, Story


def _story() -> Story:
    return Story(
        id="US-04",
        title="Orchestrator routes to the correct sub-agent",
        body="As a learner...",
        criteria=[
            AcceptanceCriterion(text="a thing", done=True),
            AcceptanceCriterion(text="another thing", done=False),
        ],
    )


def test_commit_message_without_extra():
    message = commit_message(_story())
    assert message == (
        "US-04: Orchestrator routes to the correct sub-agent\n\n"
        "Implements US-04. See USER_STORIES.md for acceptance criteria.\n"
    )


def test_commit_message_with_extra():
    message = commit_message(
        _story(),
        extra_message="Tidy up devtools scaffolding",
        extra_paths=["README.md", "devtools/pyproject.toml"],
    )
    assert "Also includes:\nTidy up devtools scaffolding" in message
    assert "- README.md" in message
    assert "- devtools/pyproject.toml" in message


def test_pr_title():
    assert pr_title(_story()) == "US-04: Orchestrator routes to the correct sub-agent"


def test_pr_body_without_extra():
    body = pr_body(_story())
    assert "- [x] a thing" in body
    assert "- [ ] another thing" in body
    assert "Also includes" not in body


def test_pr_body_with_extra():
    body = pr_body(
        _story(), extra_message="Tidy up devtools scaffolding", extra_paths=["README.md"]
    )
    assert "### Also includes" in body
    assert "Tidy up devtools scaffolding" in body
    assert "- README.md" in body
