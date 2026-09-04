import os
from typing import Any

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 8


class EmbeddingService:
    """
    Lightweight embedding service using FastEmbed/ONNX Runtime.

    FastEmbed avoids PyTorch/SentenceTransformer runtime overhead,
    which is important for low-memory deployment environments.
    """

    _model: Any = None

    @classmethod
    def _get_model(cls):
        """
        Lazily load the FastEmbed model.
        """

        if cls._model is None:
            from fastembed import TextEmbedding

            cls._model = TextEmbedding(
                model_name=MODEL_NAME,
                threads=1,
            )

        return cls._model

    @classmethod
    def clear_model(cls):
        """
        Release the embedding model reference.
        """

        cls._model = None

    def embed_documents(self, texts: list[str]):
        """
        Generate normalized document embeddings.

        Returns:
            numpy.ndarray with shape:
            (number_of_documents, 384)
        """

        if not texts:
            return []

        cleaned_texts = [
            text.strip()
            for text in texts
            if isinstance(text, str) and text.strip()
        ]

        if not cleaned_texts:
            return []

        model = self._get_model()

        import numpy as np

        
        vectors = []

        for start in range(0, len(cleaned_texts), EMBEDDING_BATCH_SIZE):
            batch_texts = cleaned_texts[
                start:start + EMBEDDING_BATCH_SIZE
            ]

            batch_embeddings = model.embed(
                batch_texts,
                batch_size=EMBEDDING_BATCH_SIZE,
            )

            batch_vectors = np.asarray(
                list(batch_embeddings),
                dtype=np.float32,
            )

            if batch_vectors.size == 0:
                continue

            vectors.append(batch_vectors)

        if not vectors:
            return []

        vectors = np.vstack(vectors).astype(
            np.float32,
            copy=False,
        )

        # Normalize for cosine/dot-product similarity.
        norms = np.linalg.norm(
            vectors,
            axis=1,
            keepdims=True,
        )

        vectors /= np.maximum(norms, 1e-12)

        return vectors

    def embed_query(self, query: str):
        """
        Generate a normalized query embedding.
        """

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        model = self._get_model()

        import numpy as np

        embeddings = model.embed(
            [query.strip()],
            batch_size=1,
        )

        vector = next(iter(embeddings))

        vector = np.asarray(
            vector,
            dtype=np.float32,
        )

        norm = np.linalg.norm(vector)

        if norm > 0:
            vector /= norm

        return vector