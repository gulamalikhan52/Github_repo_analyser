from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """Generate semantic embeddings for repository chunks."""

    _model = None

    @classmethod
    def _get_model(cls):
        """Load the embedding model only once."""
        if cls._model is None:
            cls._model = SentenceTransformer(MODEL_NAME)

        return cls._model

    def embed_documents(self, texts: list[str]):
        """Generate embeddings for multiple documents."""

        if not texts:
            return []

        model = self._get_model()

        return model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=True,
        )

    def embed_query(self, query: str):
        """Generate an embedding for a search query."""

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        model = self._get_model()

        return model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0] 