from typing import Any

from backend.rag.context_builder import ContextBuilder
from backend.services.llm_service import LLMService
from backend.services.repository_manager import RepositoryManager


class RAGService:
    """
    End-to-end repository question answering service.

    Flow:
        GitHub Repository
            ↓
        RepositoryManager
            ↓
        Semantic Retrieval
            ↓
        ContextBuilder
            ↓
        LLMService
            ↓
        Answer + Sources
    """

    def __init__(self):
        self.repository_manager = RepositoryManager()
        self.context_builder = ContextBuilder()
        self.llm_service = LLMService()

    def prepare_repository(
        self,
        repository_url: str,
    ) -> dict[str, Any]:
        """
        Fetch or load a repository index.
        """

        return self.repository_manager.prepare_repository(
            repository_url
        )

    def ask(
        self,
        question: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Ask a question about the currently prepared repository.
        """

        if not question or not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        # Retrieve relevant repository chunks.
        results = self.repository_manager.search(
            question,
            top_k=top_k,
        )

        # Build LLM context.
        context = self.context_builder.build(
            results
        )

        # Generate grounded answer.
        answer = self.llm_service.generate_answer(
            question,
            context,
        )

        # Extract source information.
        sources = self.context_builder.get_sources(
            results
        )

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(results),
        }