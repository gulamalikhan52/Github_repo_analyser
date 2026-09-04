from backend.rag.chunker import chunk_repository
from backend.rag.embeddings import EmbeddingService
from backend.rag.vector_store import VectorStore
from backend.services.llm_service import LLMService


class RepositoryRAG:
    """Build and query a repository-level vector index."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = None
        self.llm_service = LLMService() 

    def build_index(self, files: list[dict]):
        """
        Chunk repository files and build a FAISS index.
        """

        chunks = chunk_repository(files)

        if not chunks:
            raise ValueError(
                "No analyzable content was found in the repository."
            )

        texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = self.embedding_service.embed_documents(
            texts
        )

        self.vector_store = VectorStore(
            embeddings.shape[1]
        )

        self.vector_store.add_documents(
            embeddings,
            chunks,
        )

        return {
            "chunks": len(chunks),
            "dimension": embeddings.shape[1],
        }

    def search(self, query: str, top_k: int = 5):
        """
        Retrieve the most relevant repository chunks.
        """

        if self.vector_store is None:
            raise RuntimeError(
                "Vector index has not been built yet."
            )

        query_embedding = self.embedding_service.embed_query(
            query
        )

        return self.vector_store.search(
            query_embedding,
            top_k=top_k,
        )