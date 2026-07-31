from langchain_core.messages import AIMessage, HumanMessage

from product import orchestrator
from product.orchestrator import CHAT, QUIZ, build_orchestrator_graph, classify_intent


def test_classify_intent_routes_quiz_requests_to_quiz():
    quiz_messages = [
        "Quiz me on 你好 and 谢谢.",
        "Can you test me on some vocab?",
        "Testa-me em 你好.",
        "Teste-me sobre números.",
        "Drill me on colours please.",
        "Pergunta-me sobre frutas.",
    ]
    for text in quiz_messages:
        assert classify_intent(text) == QUIZ, text


def test_classify_intent_routes_free_form_chat_to_chat():
    chat_messages = [
        "How do I say 'good morning' in Chinese?",
        "我今天很高兴, is this sentence correct?",
        "What's the weather like today?",
        "Can you explain measure words to me?",
    ]
    for text in chat_messages:
        assert classify_intent(text) == CHAT, text


def test_route_uses_latest_human_message_not_earlier_ones():
    history = [
        HumanMessage(content="Quiz me on 你好."),
        AIMessage(content="Ok, vamos começar."),
        HumanMessage(content="Actually, let's just chat about food."),
    ]
    assert classify_intent(history[-1].content) == CHAT


def test_orchestrator_graph_routes_quiz_request_to_quiz_agent(monkeypatch):
    quiz_reply = AIMessage(content="quiz reply")
    tutor_reply = AIMessage(content="tutor reply")
    monkeypatch.setattr(orchestrator.quiz, "respond", lambda history: quiz_reply)
    monkeypatch.setattr(orchestrator.tutor, "respond", lambda history: tutor_reply)

    graph = build_orchestrator_graph()
    history = [HumanMessage(content="Quiz me on 你好 and 谢谢.")]
    result = graph.invoke({"messages": history})

    assert result["messages"][-1] == quiz_reply


def test_orchestrator_graph_routes_free_form_message_to_tutor_agent(monkeypatch):
    quiz_reply = AIMessage(content="quiz reply")
    tutor_reply = AIMessage(content="tutor reply")
    monkeypatch.setattr(orchestrator.quiz, "respond", lambda history: quiz_reply)
    monkeypatch.setattr(orchestrator.tutor, "respond", lambda history: tutor_reply)

    graph = build_orchestrator_graph()
    history = [HumanMessage(content="我今天很高兴, is this correct?")]
    result = graph.invoke({"messages": history})

    assert result["messages"][-1] == tutor_reply


def test_respond_dispatches_to_quiz_when_quiz_keyword_present(monkeypatch):
    monkeypatch.setattr(orchestrator, "_orchestrator_graph", None)
    quiz_reply = AIMessage(content="quiz reply")
    monkeypatch.setattr(orchestrator.quiz, "respond", lambda history: quiz_reply)
    monkeypatch.setattr(orchestrator.tutor, "respond", lambda history: AIMessage(content="should not be called"))

    reply = orchestrator.respond([HumanMessage(content="Testa-me em 你好.")])

    assert reply == quiz_reply


def test_respond_dispatches_to_tutor_for_free_form_chat(monkeypatch):
    monkeypatch.setattr(orchestrator, "_orchestrator_graph", None)
    tutor_reply = AIMessage(content="tutor reply")
    monkeypatch.setattr(orchestrator.tutor, "respond", lambda history: tutor_reply)
    monkeypatch.setattr(orchestrator.quiz, "respond", lambda history: AIMessage(content="should not be called"))

    reply = orchestrator.respond([HumanMessage(content="Explica-me a gramática do 了.")])

    assert reply == tutor_reply


def test_orchestrator_keeps_routing_to_quiz_until_drill_complete(monkeypatch):
    next_quiz_reply = AIMessage(content="next question")
    monkeypatch.setattr(orchestrator.quiz, "respond", lambda history: next_quiz_reply)
    monkeypatch.setattr(orchestrator.tutor, "respond", lambda history: AIMessage(content="should not be called"))

    graph = build_orchestrator_graph()
    history = [
        HumanMessage(content="Quiz me on 你好 and 谢谢."),
        AIMessage(content="first question", additional_kwargs={"agent": "quiz", "quiz_complete": False}),
        # No quiz keyword here, but the drill isn't over yet, so this must still go to the quiz agent.
        HumanMessage(content="ni hao"),
    ]
    result = graph.invoke({"messages": history})

    assert result["messages"][-1] == next_quiz_reply


def test_orchestrator_returns_to_chat_after_drill_declared_complete(monkeypatch):
    tutor_reply = AIMessage(content="tutor reply")
    monkeypatch.setattr(orchestrator.tutor, "respond", lambda history: tutor_reply)
    monkeypatch.setattr(orchestrator.quiz, "respond", lambda history: AIMessage(content="should not be called"))

    graph = build_orchestrator_graph()
    history = [
        HumanMessage(content="Quiz me on 你好."),
        AIMessage(content="Drill complete!", additional_kwargs={"agent": "quiz", "quiz_complete": True}),
        HumanMessage(content="What's the weather like today?"),
    ]
    result = graph.invoke({"messages": history})

    assert result["messages"][-1] == tutor_reply


def test_quiz_in_progress_ignores_plain_ai_replies_without_agent_tag():
    history = [
        HumanMessage(content="How do I say hello?"),
        AIMessage(content="You can say 你好."),
        HumanMessage(content="ok thanks"),
    ]
    assert orchestrator._quiz_in_progress(history) is False
