from backend.services.rag_service import RAGService


def search_repository(state, rag_service: RAGService):
    """
    Retrieve relevant chunks from the currently prepared repository.
    """

    question = state.get("question", "").strip()
    top_k = state.get("top_k", 5)

    if not question:
        return {
            "search_results": [],
            "retrieved_chunks": 0,
            "error": "Question cannot be empty.",
        }

    try:
        results = rag_service.repository_manager.search(
            question,
            top_k=top_k,
        )

        return {
            "search_results": results,
            "retrieved_chunks": len(results),
            "error": "",
        }

    except Exception as exc:
        return {
            "search_results": [],
            "retrieved_chunks": 0,
            "error": f"Repository search failed: {exc}",
        }


def build_context(state, rag_service: RAGService):
    """
    Build context from retrieved repository chunks.
    """

    results = state.get("search_results", [])

    if not results:
        return {
            "context": "",
            "sources": [],
            "error": "",
        }

    try:
        context = rag_service.context_builder.build(results)
        sources = rag_service.context_builder.get_sources(results)

        return {
            "context": context,
            "sources": sources,
            "error": "",
        }

    except Exception as exc:
        return {
            "context": "",
            "sources": [],
            "error": f"Context building failed: {exc}",
        }


def generate_answer(state, rag_service: RAGService):
    """
    Generate the final grounded answer.
    """

    question = state.get("question", "").strip()
    context = state.get("context", "")

    if not question:
        return {
            "answer": "",
            "error": "Question cannot be empty.",
        }

    if not context:
        return {
            "answer": (
                "I could not find relevant information "
                "in the repository for this question."
            ),
            "error": "",
        }

    try:
        answer = rag_service.llm_service.generate_answer(
            question,
            context,
        )

        return {
            "answer": answer,
            "error": "",
        }

    except Exception as exc:
        return {
            "answer": "",
            "error": f"Answer generation failed: {exc}",
        }