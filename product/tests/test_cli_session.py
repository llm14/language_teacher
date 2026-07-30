from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

import product
from product import EXIT_COMMANDS, run_session


def _stub_respond(history):
    return AIMessage(content=f"echo: {history[-1].content}")


def test_exit_command_ends_session_cleanly():
    inputs = iter(["hello", "exit"])
    history = run_session(read=lambda prompt: next(inputs), write=lambda _: None, respond=_stub_respond)
    assert history == [HumanMessage(content="hello"), AIMessage(content="echo: hello")]


def test_quit_is_also_an_exit_command():
    inputs = iter(["quit"])
    history = run_session(read=lambda prompt: next(inputs), write=lambda _: None, respond=_stub_respond)
    assert history == []
    assert EXIT_COMMANDS == {"exit", "quit"}


def test_history_accumulates_for_duration_of_run():
    inputs = iter(["a", "b", "c", "exit"])
    history = run_session(read=lambda prompt: next(inputs), write=lambda _: None, respond=_stub_respond)
    assert [m.content for m in history] == [
        "a",
        "echo: a",
        "b",
        "echo: b",
        "c",
        "echo: c",
    ]


def test_eof_ends_session_without_error():
    def read(prompt: str) -> str:
        raise EOFError

    history = run_session(read=read, write=lambda _: None, respond=_stub_respond)
    assert history == []


def test_main_reconfigures_streams_to_utf8(monkeypatch):
    monkeypatch.setattr(product, "run_session", MagicMock())
    stdout = MagicMock()
    stdin = MagicMock()
    monkeypatch.setattr(product.sys, "stdout", stdout)
    monkeypatch.setattr(product.sys, "stdin", stdin)

    product.main()

    stdout.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
    stdin.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
