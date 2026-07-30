"""Tutor agent: free-form Chinese-learning conversation with inline grammar correction.

Runs as a single-node LangGraph graph calling the local Ollama backend.
"""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage

from product.agent_graph import build_model, build_single_node_graph

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


def build_tutor_graph(model: Callable[[list[BaseMessage]], AIMessage] | None = None):
    """Compile the tutor's single-node graph.

    `model` defaults to a real ChatOllama instance but can be swapped for a stub in tests.
    """
    return build_single_node_graph(SYSTEM_PROMPT, "tutor", model or build_model(MODEL_NAME))


_tutor_graph = None


def respond(history: list[BaseMessage]) -> BaseMessage:
    """Invoke the tutor graph on the given history and return its reply."""
    global _tutor_graph
    if _tutor_graph is None:
        _tutor_graph = build_tutor_graph()
    result = _tutor_graph.invoke({"messages": history})
    return result["messages"][-1]
