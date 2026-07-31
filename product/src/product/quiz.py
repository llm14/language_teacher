"""Vocab quiz agent: drills the learner on specific Chinese words/phrases they name.

Runs as a single-node LangGraph graph calling the local Ollama backend.
"""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage

from product.agent_graph import build_model, build_single_node_graph

MODEL_NAME = "qwen2.5:7b"

# Machine-readable marker the quiz agent appends once the drill is over. Stripped from the text
# shown to the learner; used only so the orchestrator can keep routing to this agent turn after
# turn while a drill is in progress (see orchestrator._quiz_in_progress).
QUIZ_COMPLETE_MARKER = "<<QUIZ_COMPLETE>>"

# Tag stored on the returned AIMessage's `additional_kwargs["agent"]` to identify replies from
# this agent, independent of the marker above.
AGENT_TAG = "quiz"

SYSTEM_PROMPT = f"""You are a Mandarin Chinese vocabulary quiz master speaking to a Portuguese learner.
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
   complete instead of inventing further questions, then add the exact line "{QUIZ_COMPLETE_MARKER}"
   alone on the final line of your reply. Only include that line once the drill is truly complete;
   never include it while any named word/phrase still needs to be asked about.
"""


def build_quiz_graph(model: Callable[[list[BaseMessage]], AIMessage] | None = None):
    """Compile the quiz agent's single-node graph.

    `model` defaults to a real ChatOllama instance but can be swapped for a stub in tests.
    """
    return build_single_node_graph(SYSTEM_PROMPT, "quiz", model or build_model(MODEL_NAME))


_quiz_graph = None


def _split_completion_marker(content: str) -> tuple[str, bool]:
    """Strip `QUIZ_COMPLETE_MARKER` from `content`, returning the cleaned text and whether it was present."""
    complete = QUIZ_COMPLETE_MARKER in content
    cleaned = content.replace(QUIZ_COMPLETE_MARKER, "").rstrip()
    return cleaned, complete


def respond(history: list[BaseMessage]) -> BaseMessage:
    """Invoke the quiz graph on the given history and return its reply.

    The returned message's text never contains the internal completion marker; instead the reply
    is tagged with `additional_kwargs = {"agent": "quiz", "quiz_complete": bool}` so the
    orchestrator can keep routing subsequent turns to this agent until the drill is complete.
    """
    global _quiz_graph
    if _quiz_graph is None:
        _quiz_graph = build_quiz_graph()
    result = _quiz_graph.invoke({"messages": history})
    raw_reply = result["messages"][-1]
    cleaned_content, complete = _split_completion_marker(str(raw_reply.content))
    return AIMessage(
        content=cleaned_content,
        additional_kwargs={"agent": AGENT_TAG, "quiz_complete": complete},
    )
