"""Orchestrator: routes each learner message to the tutor or quiz sub-agent.

Routing is a keyword heuristic over the latest human message (no LLM classifier call for v1),
wired as a LangGraph graph with a conditional entry point into the tutor (US-02) and quiz (US-03)
sub-agents.
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from product import quiz, tutor

CHAT = "chat"
QUIZ = "quiz"

# Phrases that signal the learner wants a vocab drill rather than free-form chat. Checked as
# case-insensitive substrings of the latest human message.
QUIZ_KEYWORDS = (
    "quiz",
    "test me",
    "testa-me",
    "testa me",
    "teste-me",
    "teste me",
    "drill me",
    "pergunta-me sobre",
)


class OrchestratorState(TypedDict):
    messages: list[BaseMessage]


def _latest_human_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def classify_intent(text: str) -> str:
    """Keyword heuristic: return QUIZ if `text` looks like a quiz request, else CHAT."""
    lowered = text.lower()
    if any(keyword in lowered for keyword in QUIZ_KEYWORDS):
        return QUIZ
    return CHAT


def _quiz_in_progress(messages: list[BaseMessage]) -> bool:
    """True if the most recent agent turn was an unfinished quiz drill.

    Once the quiz agent replies, it tags its message via `additional_kwargs` (see
    `quiz.respond`). As long as that tag says the drill isn't complete yet, every following
    learner turn keeps routing to the quiz agent, even if it contains no quiz keyword.
    """
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return (
                message.additional_kwargs.get("agent") == quiz.AGENT_TAG
                and not message.additional_kwargs.get("quiz_complete")
            )
    return False


def _route(state: OrchestratorState) -> str:
    messages = state["messages"]
    if _quiz_in_progress(messages):
        return QUIZ
    return classify_intent(_latest_human_text(messages))


def _quiz_node(state: OrchestratorState) -> OrchestratorState:
    reply = quiz.respond(state["messages"])
    return {"messages": [*state["messages"], reply]}


def _chat_node(state: OrchestratorState) -> OrchestratorState:
    reply = tutor.respond(state["messages"])
    return {"messages": [*state["messages"], reply]}


def build_orchestrator_graph():
    """Compile the orchestrator graph: route on the latest human message, then dispatch."""
    graph = StateGraph(OrchestratorState)
    graph.add_node(QUIZ, _quiz_node)
    graph.add_node(CHAT, _chat_node)
    graph.add_conditional_edges(START, _route, {QUIZ: QUIZ, CHAT: CHAT})
    graph.add_edge(QUIZ, END)
    graph.add_edge(CHAT, END)
    return graph.compile()


_orchestrator_graph = None


def respond(history: list[BaseMessage]) -> BaseMessage:
    """Invoke the orchestrator graph on the given history and return its reply."""
    global _orchestrator_graph
    if _orchestrator_graph is None:
        _orchestrator_graph = build_orchestrator_graph()
    result = _orchestrator_graph.invoke({"messages": history})
    return result["messages"][-1]
