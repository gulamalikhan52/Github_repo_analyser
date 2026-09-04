from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.rag.rag_service import RepositoryRAG


class RepositoryState(TypedDict, total=False):
    question: str
    rag: RepositoryRAG
    retrieved_chunks: list[dict]
    answer: str
    sources: list[dict]
    error: str


def retrieve_node(state: RepositoryState):
    """Retrieve relevant repository context."""

    rag = state["rag"]
    question = state["question"]

    results = rag.search(
        question,
        top_k=5,
    )

    return {
        "retrieved_chunks": results,
    }


def generate_answer_node(state: RepositoryState):
    """Generate a grounded answer from retrieved context."""

    rag = state["rag"]
    question = state["question"]
    results = state.get("retrieved_chunks", [])

    if not results:
        return {
            "answer": (
                "I could not find relevant information "
                "in the repository."
            ),
            "sources": [],
        }

    context_parts = []

    for result in results:
        context_parts.append(
            f"File: {result['file_path']}\n"
            f"Language: {result['language']}\n"
            f"Content:\n{result['content']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    answer = rag.llm_service.generate_answer(
        question=question,
        context=context,
    )

    sources = [
        {
            "file_path": result["file_path"],
            "score": result["score"],
        }
        for result in results
    ]

    return {
        "answer": answer,
        "sources": sources,
    }


def build_repository_graph():
    """Build the repository intelligence workflow."""

    graph = StateGraph(RepositoryState)

    graph.add_node(
        "retrieve",
        retrieve_node,
    )

    graph.add_node(
        "generate_answer",
        generate_answer_node,
    )

    graph.add_edge(
        START,
        "retrieve",
    )

    graph.add_edge(
        "retrieve",
        "generate_answer",
    )

    graph.add_edge(
        "generate_answer",
        END,
    )

    return graph.compile() 