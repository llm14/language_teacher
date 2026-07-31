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


def test_blank_input_is_a_no_op():
    inputs = iter(["   ", "\t", "", "hello", "exit"])
    calls: list = []

    def _respond(history):
        calls.append(list(history))
        return AIMessage(content=f"echo: {history[-1].content}")

    history = run_session(read=lambda prompt: next(inputs), write=lambda _: None, respond=_respond)

    # Only the non-blank "hello" turn should ever have reached the agent.
    assert len(calls) == 1
    assert calls[0] == [HumanMessage(content="hello")]
    assert history == [HumanMessage(content="hello"), AIMessage(content="echo: hello")]


def test_backend_error_reports_one_line_and_keeps_session_alive():
    inputs = iter(["hello", "world", "exit"])
    writes: list = []
    calls: list = []

    def _flaky_respond(history):
        calls.append(list(history))
        if len(calls) == 1:
            raise ConnectionError("Ollama unreachable at http://localhost:11434")
        return AIMessage(content=f"echo: {history[-1].content}")

    history = run_session(
        read=lambda prompt: next(inputs),
        write=lambda msg: writes.append(msg),
        respond=_flaky_respond,
    )

    # First turn: backend call raised, so no AI reply was appended, but the human turn stays.
    # Second turn: backend call succeeds normally, proving the session survived the error.
    assert history == [
        HumanMessage(content="hello"),
        HumanMessage(content="world"),
        AIMessage(content="echo: world"),
    ]
    error_lines = [msg for msg in writes if msg.startswith("Error:")]
    assert len(error_lines) == 1
    assert "\n" not in error_lines[0]


def test_main_reconfigures_streams_to_utf8(monkeypatch):
    monkeypatch.setattr(product, "run_session", MagicMock())
    stdout = MagicMock()
    stdin = MagicMock()
    monkeypatch.setattr(product.sys, "stdout", stdout)
    monkeypatch.setattr(product.sys, "stdin", stdin)

    product.main()

    stdout.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
    stdin.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
