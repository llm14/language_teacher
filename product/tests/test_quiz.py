import socket

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from product import quiz
from product.agent_graph import OLLAMA_BASE_URL
from product.quiz import (
    AGENT_TAG,
    QUIZ_COMPLETE_MARKER,
    SYSTEM_PROMPT,
    build_quiz_graph,
)


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


def test_quiz_node_prepends_system_prompt_to_history():
    stub = _StubModel()
    graph = build_quiz_graph(model=stub)
    history = [HumanMessage(content="Testa-me em 你好 e 谢谢.")]

    graph.invoke({"messages": history})

    sent = stub.received[0]
    assert sent[0] == SystemMessage(content=SYSTEM_PROMPT)
    assert sent[1:] == history


def test_quiz_node_appends_reply_to_history():
    stub = _StubModel(reply="Como se diz 'obrigado' em chinês?")
    graph = build_quiz_graph(model=stub)
    history = [HumanMessage(content="Testa-me em 谢谢.")]

    result = graph.invoke({"messages": history})

    assert result["messages"] == [
        HumanMessage(content="Testa-me em 谢谢."),
        AIMessage(content="Como se diz 'obrigado' em chinês?"),
    ]


def test_system_prompt_requires_european_portuguese():
    assert "European Portuguese" in SYSTEM_PROMPT
    assert "Brazilian Portuguese" in SYSTEM_PROMPT
    assert '"você"' in SYSTEM_PROMPT
    assert '"tu"' in SYSTEM_PROMPT


def test_system_prompt_restricts_to_named_vocab():
    assert "specific Chinese word(s) or phrase(s) they want to be quizzed on" in SYSTEM_PROMPT
    assert "never introduce or quiz on any other vocabulary" in SYSTEM_PROMPT


def test_system_prompt_requires_judging_answers():
    assert "judge whether it is correct or incorrect" in SYSTEM_PROMPT


def test_system_prompt_requires_completion_marker():
    assert QUIZ_COMPLETE_MARKER in SYSTEM_PROMPT


def test_respond_strips_completion_marker_and_flags_metadata(monkeypatch):
    stub = _StubModel(reply=f"Terminámos! Acertaste em tudo.\n{QUIZ_COMPLETE_MARKER}")
    monkeypatch.setattr(quiz, "_quiz_graph", build_quiz_graph(model=stub))

    reply = quiz.respond([HumanMessage(content="Testa-me em 你好.")])

    assert QUIZ_COMPLETE_MARKER not in reply.content
    assert reply.content == "Terminámos! Acertaste em tudo."
    assert reply.additional_kwargs == {"agent": AGENT_TAG, "quiz_complete": True}


def test_respond_flags_incomplete_when_marker_absent(monkeypatch):
    stub = _StubModel(reply="Próxima pergunta: o que significa 你好?")
    monkeypatch.setattr(quiz, "_quiz_graph", build_quiz_graph(model=stub))

    reply = quiz.respond([HumanMessage(content="Testa-me em 你好.")])

    assert reply.content == "Próxima pergunta: o que significa 你好?"
    assert reply.additional_kwargs == {"agent": AGENT_TAG, "quiz_complete": False}


@pytest.mark.skipif(not _ollama_reachable(), reason=f"Ollama not reachable at {OLLAMA_BASE_URL}")
def test_live_quiz_asks_about_named_vocab_only():
    graph = build_quiz_graph()
    history = [HumanMessage(content="Quero que me testes ao vocabulário: 你好 (olá) e 谢谢 (obrigado).")]
    result = graph.invoke({"messages": history})

    reply = result["messages"][-1]
    assert isinstance(reply, AIMessage)
    assert reply.content.strip()
    assert "你好" in reply.content or "谢谢" in reply.content


@pytest.mark.skipif(not _ollama_reachable(), reason=f"Ollama not reachable at {OLLAMA_BASE_URL}")
def test_live_quiz_judges_a_correct_answer():
    history = [
        HumanMessage(content="Quero que me testes só à palavra 谢谢 (obrigado). Pergunta-me a tradução."),
    ]
    graph = build_quiz_graph()
    first = graph.invoke({"messages": history})
    history = first["messages"]
    history.append(HumanMessage(content="Obrigado"))

    result = graph.invoke({"messages": history})
    reply = result["messages"][-1]
    assert isinstance(reply, AIMessage)
    assert reply.content.strip()
