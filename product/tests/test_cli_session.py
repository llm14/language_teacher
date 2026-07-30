from product import EXIT_COMMANDS, run_session


def test_exit_command_ends_session_cleanly():
    inputs = iter(["hello", "exit"])
    history = run_session(read=lambda prompt: next(inputs), write=lambda _: None)
    assert history == ["hello"]


def test_quit_is_also_an_exit_command():
    inputs = iter(["quit"])
    history = run_session(read=lambda prompt: next(inputs), write=lambda _: None)
    assert history == []
    assert EXIT_COMMANDS == {"exit", "quit"}


def test_history_accumulates_for_duration_of_run():
    inputs = iter(["a", "b", "c", "exit"])
    history = run_session(read=lambda prompt: next(inputs), write=lambda _: None)
    assert history == ["a", "b", "c"]


def test_eof_ends_session_without_error():
    def read(prompt: str) -> str:
        raise EOFError

    history = run_session(read=read, write=lambda _: None)
    assert history == []
