import os
from typing import Any


os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Generate semantic embeddings for repository chunks.

    The embedding model is loaded only when an embedding operation
    is actually requested.
    """

    _model: Any = None

    @classmethod
    def _get_model(cls):
        """
        Lazily load SentenceTransformer.

        Important:
        SentenceTransformer is imported inside this method so that
        PyTorch and the ML stack are NOT loaded during FastAPI startup.
        """

        if cls._model is None:
            
            from sentence_transformers import SentenceTransformer

           
            try:
                import torch

                torch.set_num_threads(1)

                if hasattr(torch, "set_num_interop_threads"):
                    torch.set_num_interop_threads(1)

            except Exception:
               
                pass

            cls._model = SentenceTransformer(
                MODEL_NAME,
                device="cpu",
            )

        return cls._model

    @classmethod
    def clear_model(cls):
        """
        Release the embedding model from memory.

        Normally the singleton should remain loaded because repeatedly
        loading the model is expensive. This method is available for
        controlled memory cleanup if required.
        """

        cls._model = None

        try:
            import torch

            if hasattr(torch, "cuda"):
                torch.cuda.empty_cache()

        except Exception:
            pass

    def embed_documents(self, texts: list[str]):
        """
        Generate embeddings for multiple documents.
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

        return model.encode(
            cleaned_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=16,
            show_progress_bar=False,
        )

    def embed_query(self, query: str):
        """
        Generate an embedding for a search query.
        """

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        model = self._get_model()

        return model.encode(
            [query.strip()],
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=1,
            show_progress_bar=False,
        )[0]