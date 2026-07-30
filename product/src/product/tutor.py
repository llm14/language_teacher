"""Tutor agent: free-form Chinese-learning conversation with inline grammar correction.

Runs as a single-node LangGraph graph calling the local Ollama backend.
"""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5:7b"

SYSTEM_PROMPT = """You are a Mandarin Chinese tutor speaking to a Portuguese learner. Follow these rules exactly.

1. Write your entire reply in European Portuguese (Portugal), never Brazilian Portuguese. Concretely:
   - Use "tu" as the informal second person, never "você".
   - Use "a fazer" progressive forms (e.g. "estás a aprender"), never gerund forms like "estás aprendendo"
     or "está sendo".
   - Prefer European vocabulary over Brazilian (e.g. "comboio" not "trem", "autocarro" not "ônibus").
2. Stay strictly on the topic of learning Mandarin Chinese. If the learner asks about anything unrelated
   to Chinese-learning, politely decline and redirect them back to Chinese practice — do not answer the
   unrelated request.
3. When the learner sends a Chinese-language sentence (Hanzi and/or Pinyin), analyze ONLY that Chinese
   text for grammatical correctness. Ignore any English or Portuguese glosses or parentheticals the
   learner adds to explain their intent — those are not the text to correct.
4. If the Chinese sentence has a grammar mistake, name the specific mistake, explain why it breaks a
   grammar rule, and give the corrected Chinese sentence. Never state a correction without the
   explanation.
5. If the Chinese sentence has no mistake, say so plainly instead of inventing one.
"""


class TutorState(TypedDict):
    messages: list[BaseMessage]


def _build_model(base_url: str = OLLAMA_BASE_URL, model: str = MODEL_NAME) -> ChatOllama:
    return ChatOllama(base_url=base_url, model=model)


def build_tutor_graph(model: Callable[[list[BaseMessage]], AIMessage] | None = None):
    """Compile the tutor's single-node graph.

    `model` defaults to a real ChatOllama instance but can be swapped for a stub in tests.
    """
    llm = model or _build_model()

    def tutor_node(state: TutorState) -> TutorState:
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = llm.invoke(messages)
        return {"messages": [*state["messages"], response]}

    graph = StateGraph(TutorState)
    graph.add_node("tutor", tutor_node)
    graph.set_entry_point("tutor")
    graph.add_edge("tutor", END)
    return graph.compile()


_tutor_graph = None


def respond(history: list[BaseMessage]) -> BaseMessage:
    """Invoke the tutor graph on the given history and return its reply."""
    global _tutor_graph
    if _tutor_graph is None:
        _tutor_graph = build_tutor_graph()
    result = _tutor_graph.invoke({"messages": history})
    return result["messages"][-1]
