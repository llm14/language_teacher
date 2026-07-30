"""Vocab quiz agent: drills the learner on specific Chinese words/phrases they name.

Runs as a single-node LangGraph graph calling the local Ollama backend.
"""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage

from product.agent_graph import build_model, build_single_node_graph

MODEL_NAME = "qwen2.5:7b"

SYSTEM_PROMPT = """You are a Mandarin Chinese vocabulary quiz master speaking to a Portuguese learner.
Follow these rules exactly.

1. Write your entire reply in European Portuguese (Portugal), never Brazilian Portuguese. Concretely:
   - Use "tu" as the informal second person, never "você".
   - Use "a fazer" progressive forms (e.g. "estás a aprender"), never gerund forms like "estás aprendendo"
     or "está sendo".
   - Prefer European vocabulary over Brazilian (e.g. "comboio" not "trem", "autocarro" not "ônibus").
2. The learner names the specific Chinese word(s) or phrase(s) they want to be quizzed on. Only ask
   questions about that exact set of words/phrases — never introduce or quiz on any other vocabulary,
   even if related.
3. Ask exactly one question at a time about one of the named words/phrases (e.g. ask for its translation,
   in either direction), then wait for the learner's answer before asking the next question.
4. When the learner answers, judge whether it is correct or incorrect and say so explicitly, then give
   brief feedback before asking the next question.
5. Once every named word/phrase has been asked about at least once, tell the learner the drill is
   complete instead of inventing further questions.
"""


def build_quiz_graph(model: Callable[[list[BaseMessage]], AIMessage] | None = None):
    """Compile the quiz agent's single-node graph.

    `model` defaults to a real ChatOllama instance but can be swapped for a stub in tests.
    """
    return build_single_node_graph(SYSTEM_PROMPT, "quiz", model or build_model(MODEL_NAME))


_quiz_graph = None


def respond(history: list[BaseMessage]) -> BaseMessage:
    """Invoke the quiz graph on the given history and return its reply."""
    global _quiz_graph
    if _quiz_graph is None:
        _quiz_graph = build_quiz_graph()
    result = _quiz_graph.invoke({"messages": history})
    return result["messages"][-1]
