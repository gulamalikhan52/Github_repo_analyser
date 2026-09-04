import hashlib
import logging

from backend.rag.chunker import chunk_repository_files
from backend.rag.indexer import RepositoryIndexer
from backend.services.repository_service import collect_repository_files


logger = logging.getLogger(__name__)

INDEX_ROOT = "data/indexes"


def create_repository_key(repository_url: str) -> str:
    normalized_url = repository_url.strip().lower()

    return hashlib.sha256(
        normalized_url.encode("utf-8")
    ).hexdigest()[:16]


class RepositoryManager:

    def __init__(self):
        self.indexer = None

    def prepare_repository(
        self,
        repository_url: str
    ) -> dict:

        if not repository_url:
            raise ValueError(
                "Repository URL cannot be empty."
            )

        repository_key = create_repository_key(
            repository_url
        )

        logger.info(
            "Preparing repository: %s",
            repository_url
        )

      

        indexer = RepositoryIndexer(
            repository_key
        )

        try:

            logger.info(
                "[1/5] Checking existing index..."
            )

            indexer.load()

            self.indexer = indexer

            total_chunks = len(
                indexer.vector_store.documents
            )

            logger.info(
                "Existing index loaded: %s chunks",
                total_chunks
            )

            return {
                "status": "loaded",
                "repository_key": repository_key,
                "repository": repository_url,
                "total_chunks": total_chunks,
            }

        except FileNotFoundError:

            logger.info(
                "No existing index found. Creating new index."
            )


        logger.info(
            "[2/5] Collecting repository files..."
        )

        repository_data = collect_repository_files(
            repository_url
        )

        logger.info(
            "Files collected: %s | Files skipped: %s",
            repository_data["total_files"],
            repository_data["total_skipped"],
        )

     

        logger.info(
            "[3/5] Creating chunks..."
        )

        chunks = chunk_repository_files(
            repository_data["files"]
        )

        logger.info(
            "Chunks created: %s",
            len(chunks)
        )

        if not chunks:

            raise ValueError(
                "No analyzable content found "
                "in the repository."
            )

     

        logger.info(
            "[4/5] Generating embeddings and "
            "building FAISS index..."
        )

        result = indexer.index_chunks(
            chunks
        )

        logger.info(
            "Embeddings generated: %s chunks | dimension=%s",
            result["total_chunks"],
            result["embedding_dimension"],
        )

      

        logger.info(
            "[5/5] Saving FAISS index..."
        )

        indexer.save()

        self.indexer = indexer

        logger.info(
            "Repository preparation completed: %s",
            repository_url
        )

        return {
            "status": "created",
            "repository_key": repository_key,
            "repository": repository_data[
                "repository"
            ],
            "default_branch": repository_data[
                "default_branch"
            ],
            "total_files": repository_data[
                "total_files"
            ],
            "total_skipped": repository_data[
                "total_skipped"
            ],
            "total_chunks": result[
                "total_chunks"
            ],
            "embedding_dimension": result[
                "embedding_dimension"
            ],
        }

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> list[dict]:

        if self.indexer is None:

            raise RuntimeError(
                "No repository has been prepared."
            )

        return self.indexer.search(
            query,
            top_k=top_k
        ) 