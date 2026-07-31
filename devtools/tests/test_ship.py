from devtools.ship import _is_story_path


def test_is_story_path_matches_user_stories_file():
    assert _is_story_path("USER_STORIES.md")


def test_is_story_path_matches_product_dir():
    assert _is_story_path("product/src/product/quiz.py")


def test_is_story_path_normalizes_windows_separators():
    assert _is_story_path("product\\src\\product\\quiz.py")


def test_is_story_path_rejects_other_paths():
    assert not _is_story_path("README.md")
    assert not _is_story_path("devtools/pyproject.toml")
    assert not _is_story_path(".claude/workflows/implement-story.js")
