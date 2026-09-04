from pathlib import Path
from typing import Any

from backend.rag.embeddings import EmbeddingService
from backend.rag.vector_store import VectorStore


INDEX_ROOT = Path("data/indexes")


class RepositoryIndexer:
    """
    Create, persist, load, and search repository indexes.
    """

    def __init__(
        self,
        repository_key: str | None = None,
    ):
        self.embedding_service = EmbeddingService()
        self.vector_store: VectorStore | None = None
        self.repository_key = repository_key

    def index_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if not chunks:
            raise ValueError(
                "No chunks were provided for indexing."
            )

        texts = [
            chunk["content"]
            for chunk in chunks
            if chunk.get("content")
        ]

        if not texts:
            raise ValueError(
                "No valid chunk content found."
            )

        vectors = (
            self.embedding_service
            .embed_documents(texts)
        )

        self.vector_store = VectorStore(
            dimension=vectors.shape[1]
        )

        self.vector_store.add_documents(
            vectors,
            chunks,
        )

        return {
            "vector_store": self.vector_store,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "embedding_dimension": vectors.shape[1],
        }

    def save(self):
        """
        Persist the current repository index.
        """

        if self.vector_store is None:
            raise RuntimeError(
                "Nothing to save. Index the repository first."
            )

        if not self.repository_key:
            raise ValueError(
                "repository_key is required for persistence."
            )

        directory = (
            INDEX_ROOT / self.repository_key
        )

        self.vector_store.save(directory)

        return directory

    def load(self):
        """
        Load the repository index from disk.
        """

        if not self.repository_key:
            raise ValueError(
                "repository_key is required for loading."
            )

        directory = (
            INDEX_ROOT / self.repository_key
        )

        self.vector_store = VectorStore.load(
            directory
        )

        return self.vector_store

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:

        if self.vector_store is None:
            raise RuntimeError(
                "Repository has not been indexed yet."
            )

        if not query or not query.strip():
            raise ValueError(
                "Search query cannot be empty."
            )

        query_vector = (
            self.embedding_service
            .embed_query(query)
        )

        return self.vector_store.search(
            query_vector,
            top_k=top_k,
        )