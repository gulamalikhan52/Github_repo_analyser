from pathlib import Path
from typing import Any
import gc

from backend.rag.embeddings import EmbeddingService
from backend.rag.vector_store import VectorStore


INDEX_ROOT = Path("data/indexes")

EMBEDDING_BATCH_SIZE = 8


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

        valid_chunks = [
            chunk
            for chunk in chunks
            if isinstance(chunk, dict)
            and chunk.get("content")
        ]

        if not valid_chunks:
            raise ValueError(
                "No valid chunk content found."
            )

        total_chunks = len(valid_chunks)

        for start in range(
            0,
            total_chunks,
            EMBEDDING_BATCH_SIZE,
        ):
            end = min(
                start + EMBEDDING_BATCH_SIZE,
                total_chunks,
            )

            batch_chunks = valid_chunks[start:end]

            batch_texts = [
                chunk["content"]
                for chunk in batch_chunks
            ]

            vectors = self.embedding_service.embed_documents(
                batch_texts
            )

            if vectors is None or len(vectors) == 0:
                raise ValueError(
                    f"Embedding generation returned no vectors "
                    f"for chunks {start}:{end}."
                )

            if len(vectors) != len(batch_chunks):
                raise ValueError(
                    f"Embedding count mismatch: "
                    f"expected {len(batch_chunks)}, "
                    f"got {len(vectors)}."
                )

            if self.vector_store is None:
                self.vector_store = VectorStore(
                    dimension=vectors.shape[1]
                )

            self.vector_store.add_documents(
                vectors,
                batch_chunks,
            )

            del batch_texts
            del vectors
            del batch_chunks

            gc.collect()

        if self.vector_store is None:
            raise RuntimeError(
                "Failed to build the vector store."
            )

        return {
            "vector_store": self.vector_store,
            "total_chunks": total_chunks,
            "embedding_dimension": self.vector_store.index.d,
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

        directory = INDEX_ROOT / self.repository_key

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

        directory = INDEX_ROOT / self.repository_key

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

        query_vector = self.embedding_service.embed_query(
            query
        )

        return self.vector_store.search(
            query_vector,
            top_k=top_k,
        )