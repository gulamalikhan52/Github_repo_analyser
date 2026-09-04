from pathlib import Path
from typing import Any

import faiss
import numpy as np


class VectorStore:
    """
    FAISS-based vector store with disk persistence.
    """

    def __init__(self, dimension: int):
        if dimension <= 0:
            raise ValueError("Dimension must be greater than 0.")

        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.documents: list[dict[str, Any]] = []

    def add_documents(
        self,
        vectors: np.ndarray,
        documents: list[dict[str, Any]],
    ):
        """
        Add vectors and their metadata to the FAISS index.
        """

        if len(vectors) != len(documents):
            raise ValueError(
                "Number of vectors must match number of documents."
            )

        if len(vectors) == 0:
            return

        vectors = np.asarray(
            vectors,
            dtype="float32",
        )

        if vectors.ndim != 2:
            raise ValueError(
                "Vectors must be a 2-dimensional array."
            )

        if vectors.shape[1] != self.dimension:
            raise ValueError(
                f"Expected vectors with dimension "
                f"{self.dimension}, got {vectors.shape[1]}."
            )

        self.index.add(vectors)
        self.documents.extend(documents)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search for the most similar documents.
        """

        if not self.documents:
            return []

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        query_vector = np.asarray(
            query_vector,
            dtype="float32",
        )

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        if query_vector.shape[1] != self.dimension:
            raise ValueError(
                f"Expected query dimension "
                f"{self.dimension}, got {query_vector.shape[1]}."
            )

        k = min(top_k, len(self.documents))

        scores, indices = self.index.search(
            query_vector,
            k,
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):
            if index < 0:
                continue

            document = dict(
                self.documents[index]
            )

            document["score"] = float(score)

            results.append(document)

        return results

    def save(
        self,
        directory: str | Path,
    ):
        """
        Save FAISS index and document metadata to disk.
        """

        directory = Path(directory)
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        index_path = directory / "index.faiss"
        metadata_path = directory / "documents.npy"

        faiss.write_index(
            self.index,
            str(index_path),
        )

        np.save(
            metadata_path,
            np.array(
                self.documents,
                dtype=object,
            ),
            allow_pickle=True,
        )

    @classmethod
    def load(
        cls,
        directory: str | Path,
    ):
        """
        Load a previously saved vector store.
        """

        directory = Path(directory)

        index_path = directory / "index.faiss"
        metadata_path = directory / "documents.npy"

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}"
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Document metadata not found: {metadata_path}"
            )

        index = faiss.read_index(
            str(index_path)
        )

        documents = np.load(
            metadata_path,
            allow_pickle=True,
        ).tolist()

        store = cls(index.d)
        store.index = index
        store.documents = documents

        return store