import socket

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from product.tutor import MODEL_NAME, OLLAMA_BASE_URL, SYSTEM_PROMPT, build_tutor_graph


def _ollama_reachable() -> bool:
    host, port = OLLAMA_BASE_URL.split("://")[1].split(":")
    try:
        with socket.create_connection((host, int(port)), timeout=0.5):
            return True
    except OSError:
        return False


class _StubModel:
    def __init__(self, reply: str = "resposta de teste"):
        self.reply = reply
        self.received: list = []

    def invoke(self, messages):
        self.received.append(messages)
        return AIMessage(content=self.reply)


def test_tutor_node_prepends_system_prompt_to_history():
    stub = _StubModel()
    graph = build_tutor_graph(model=stub)
    history = [HumanMessage(content="Wo hen hao")]

    graph.invoke({"messages": history})

    sent = stub.received[0]
    assert sent[0] == SystemMessage(content=SYSTEM_PROMPT)
    assert sent[1:] == history


def test_tutor_node_appends_reply_to_history():
    stub = _StubModel(reply="Muito bem!")
    graph = build_tutor_graph(model=stub)
    history = [HumanMessage(content="Ni hao")]

    result = graph.invoke({"messages": history})

    assert result["messages"] == [HumanMessage(content="Ni hao"), AIMessage(content="Muito bem!")]


def test_system_prompt_requires_european_portuguese():
    assert "European Portuguese" in SYSTEM_PROMPT
    assert "Brazilian Portuguese" in SYSTEM_PROMPT
    assert '"você"' in SYSTEM_PROMPT
    assert '"tu"' in SYSTEM_PROMPT


def test_system_prompt_requires_staying_on_topic():
    assert "Chinese" in SYSTEM_PROMPT
    assert "redirect" in SYSTEM_PROMPT


def test_system_prompt_requires_analyzing_only_the_chinese_text():
    assert "Ignore any English or Portuguese glosses" in SYSTEM_PROMPT


def test_system_prompt_requires_explained_corrections():
    assert "grammar mistake" in SYSTEM_PROMPT
    assert "explain why" in SYSTEM_PROMPT


@pytest.mark.skipif(not _ollama_reachable(), reason=f"Ollama not reachable at {OLLAMA_BASE_URL}")
def test_live_tutor_replies_in_portuguese():
    graph = build_tutor_graph()
    result = graph.invoke({"messages": [HumanMessage(content="Ola! Como estas?")]})

    reply = result["messages"][-1]
    assert isinstance(reply, AIMessage)
    assert reply.content.strip()
    assert MODEL_NAME == "qwen2.5:7b"
