from langgraph.graph import StateGraph, START, END

from backend.graph.state import RepositoryState
from backend.graph.nodes import (
    search_repository,
    build_context,
    generate_answer,
)
from backend.services.rag_service import RAGService


def build_repository_graph(rag_service: RAGService):
    """
    Build the repository analysis LangGraph workflow.
    """

    graph = StateGraph(RepositoryState)

    graph.add_node(
        "search_repository",
        lambda state: search_repository(state, rag_service),
    )

    graph.add_node(
        "build_context",
        lambda state: build_context(state, rag_service),
    )

    graph.add_node(
        "generate_answer",
        lambda state: generate_answer(state, rag_service),
    )

    graph.add_edge(START, "search_repository")
    graph.add_edge("search_repository", "build_context")
    graph.add_edge("build_context", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()