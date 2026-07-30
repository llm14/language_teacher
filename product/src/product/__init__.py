"""Interactive CLI entry point for the Language Teacher app."""

from collections.abc import Callable

EXIT_COMMANDS = {"exit", "quit"}


def run_session(
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> list[str]:
    """Run the REPL loop until an exit command or EOF. Returns the in-memory conversation history."""
    history: list[str] = []
    write("Language Teacher CLI. Type 'exit' or 'quit' to leave.")
    while True:
        try:
            user_input = read("> ")
        except EOFError:
            break
        if user_input.strip().lower() in EXIT_COMMANDS:
            break
        history.append(user_input)
        write(f"(echo) {user_input}")
    return history


def main() -> None:
    run_session()
