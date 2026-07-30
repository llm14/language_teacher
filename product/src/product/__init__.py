"""Interactive CLI entry point for the Language Teacher app."""

import sys
from collections.abc import Callable

from langchain_core.messages import BaseMessage, HumanMessage

from product import tutor

EXIT_COMMANDS = {"exit", "quit"}


def run_session(
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
    respond: Callable[[list[BaseMessage]], BaseMessage] = tutor.respond,
) -> list[BaseMessage]:
    """Run the REPL loop until an exit command or EOF. Returns the in-memory conversation history."""
    history: list[BaseMessage] = []
    write("Language Teacher CLI. Type 'exit' or 'quit' to leave.")
    while True:
        try:
            user_input = read("> ")
        except EOFError:
            break
        if user_input.strip().lower() in EXIT_COMMANDS:
            break
        history.append(HumanMessage(content=user_input))
        reply = respond(history)
        history.append(reply)
        write(reply.content)
    return history


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    run_session()
