# Language Teacher

An interactive command-line Chinese (Mandarin) tutor for a Portuguese-speaking learner, built on
[LangGraph](https://langchain-ai.github.io/langgraph/) and a locally-running
[Ollama](https://ollama.com/) model. No cloud LLM is ever called: every agent talks to Ollama over
HTTP on `localhost`.

## Architecture

The app is a small "orchestrator + sub-agents" system, each piece implemented as its own
[LangGraph](https://langchain-ai.github.io/langgraph/) graph:

```
CLI (product/__init__.py)
   |
   |  keeps the full conversation history in memory
   v
Orchestrator (product/orchestrator.py)
   |
   |  routes the latest turn to exactly one sub-agent
   |
   +---> Tutor agent (product/tutor.py)   -- free-form conversation practice with inline
   |                                         grammar correction (US-02)
   |
   +---> Quiz agent (product/quiz.py)     -- drills the learner on vocabulary they name (US-03)
```

- **Tutor and quiz agents** (`product/tutor.py`, `product/quiz.py`) are each a single-node
  LangGraph graph (built by the shared helper in `product/agent_graph.py`): the node prepends the
  agent's system prompt to the running message history and calls the local Ollama model
  (`ChatOllama`, model `qwen2.5:7b`, base URL `http://localhost:11434`) to produce the next
  `AIMessage`.
- **Orchestrator** (`product/orchestrator.py`) is itself a LangGraph graph with a conditional entry
  point. For each new learner turn it decides whether to dispatch to the quiz agent or the tutor
  agent:
  - If a quiz drill is already in progress — the previous reply came from the quiz agent and that
    agent hasn't yet declared the drill complete — the turn keeps going to the quiz agent
    regardless of what the learner typed. The quiz agent signals completion via an internal marker
    it appends to its own reply; the orchestrator strips that marker before anything is shown to
    the learner and stores the result as metadata (`additional_kwargs`) on the message instead.
  - Otherwise, the latest learner message is matched against a small set of quiz-intent keywords
    (e.g. "quiz", "test me", "testa-me"). A match routes to the quiz agent; anything else routes to
    the tutor agent for free-form chat/correction.
- **CLI** (`product/__init__.py`) is a simple read-eval-print loop that keeps the conversation
  history in memory for the duration of the process, calls the orchestrator once per non-blank
  learner turn, and prints the reply. Blank/whitespace-only input is ignored (no agent call, no
  history entry — the prompt is simply shown again). If the Ollama backend can't be reached (or
  raises any other error) for a given turn, the CLI prints a single-line error for that turn only
  and keeps the session alive for the next input, instead of crashing.

## Requirements

- Python (see `.python-version` for the exact version used in this project).
- [Ollama](https://ollama.com/) running locally and reachable at `http://localhost:11434`, with the
  `qwen2.5:7b` model pulled:

  ```
  ollama pull qwen2.5:7b
  ollama serve
  ```

## Running the CLI

From the `product/` directory, using [uv](https://docs.astral.sh/uv/):

```
uv sync
uv run product
```

This starts an interactive prompt. Type a message to chat with the tutor, or ask to be quizzed
(e.g. "Quiz me on 你好 and 谢谢") to start a vocabulary drill. Type `exit` or `quit` (or send EOF,
e.g. Ctrl+D / Ctrl+Z) to leave.

## Running the tests

```
uv run pytest
```

Some tests only run when Ollama is actually reachable at `http://localhost:11434` (they are
skipped otherwise); the rest run fully offline against stubbed models.
