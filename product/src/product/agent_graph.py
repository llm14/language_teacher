"""Shared single-node LangGraph wiring for agents backed by the local Ollama model."""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

OLLAMA_BASE_URL = "http://localhost:11434"


class AgentState(TypedDict):
    messages: list[BaseMessage]


def build_model(model_name: str, base_url: str = OLLAMA_BASE_URL) -> ChatOllama:
    return ChatOllama(base_url=base_url, model=model_name)


def build_single_node_graph(
    system_prompt: str,
    node_name: str,
    model: Callable[[list[BaseMessage]], AIMessage],
):
    """Compile a graph with one node: prepend `system_prompt`, call `model`, append its reply."""

    def node(state: AgentState) -> AgentState:
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = model.invoke(messages)
        return {"messages": [*state["messages"], response]}

    graph = StateGraph(AgentState)
    graph.add_node(node_name, node)
    graph.set_entry_point(node_name)
    graph.add_edge(node_name, END)
    return graph.compile()
