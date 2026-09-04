import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.graph.graph import build_repository_graph
from backend.rag.indexer import RepositoryIndexer
from backend.services.rag_service import RAGService
from backend.services.repository_manager import create_repository_key



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)



app = FastAPI(
    title="AI Repository Intelligence",
    description="AI-powered GitHub repository analysis and question answering",
    version="1.0.0",
)



rag_service = RAGService()

repository_graph = build_repository_graph(
    rag_service
)


MAX_BACKGROUND_WORKERS = 2

executor = ThreadPoolExecutor(
    max_workers=MAX_BACKGROUND_WORKERS
)

job_lock = Lock()

prepare_jobs: dict[str, dict[str, Any]] = {}



class PrepareRepositoryRequest(BaseModel):
    repository_url: str = Field(
        ...,
        min_length=1,
        description="GitHub repository URL",
        examples=[
            "https://github.com/psf/requests"
        ],
    )


class AskRequest(BaseModel):
    repository_url: str = Field(
        ...,
        min_length=1,
        description="GitHub repository URL",
        examples=[
            "https://github.com/psf/requests"
        ],
    )

    question: str = Field(
        ...,
        min_length=1,
        description="Question about the repository",
        examples=[
            "How does authentication work?"
        ],
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of relevant chunks to retrieve",
    )


def get_index_directory(
    repository_key: str,
) -> Path:
    """
    Return the directory where a repository index
    is stored.
    """

    return (
        Path("data")
        / "indexes"
        / repository_key
    )


def index_exists(
    repository_key: str,
) -> bool:
    """
    Check whether a complete saved FAISS index exists.
    """

    directory = get_index_directory(
        repository_key
    )

    documents_file = (
        directory / "documents.npy"
    )

    faiss_file = (
        directory / "index.faiss"
    )

    return (
        documents_file.exists()
        and faiss_file.exists()
    )



def set_job(
    repository_key: str,
    data: dict[str, Any],
) -> None:
    """
    Safely create/update a preparation job.
    """

    with job_lock:
        prepare_jobs[repository_key] = data


def get_job(
    repository_key: str,
) -> dict[str, Any] | None:
    """
    Safely retrieve a preparation job.
    """

    with job_lock:
        return prepare_jobs.get(
            repository_key
        )



def prepare_repository_background(
    repository_url: str,
    repository_key: str,
) -> None:
    """
    Prepare a repository in the background.

    This includes:
        GitHub file collection
        chunking
        embeddings
        FAISS indexing
        index persistence
    """

    logger.info(
        "BACKGROUND START: %s",
        repository_url,
    )

    try:

        set_job(
            repository_key,
            {
                "status": "processing",
                "repository_key": repository_key,
                "repository": repository_url,
                "stage": "starting",
            },
        )

        logger.info(
            "Calling repository preparation..."
        )

        result = (
            rag_service.prepare_repository(
                repository_url
            )
        )

        logger.info(
            "BACKGROUND COMPLETE: %s",
            repository_url,
        )

        completed_result = {
            "status": result.get(
                "status",
                "created",
            ),
            "repository_key": repository_key,
            "repository": result.get(
                "repository",
                repository_url,
            ),
            "default_branch": result.get(
                "default_branch"
            ),
            "total_files": result.get(
                "total_files"
            ),
            "total_skipped": result.get(
                "total_skipped"
            ),
            "total_chunks": result.get(
                "total_chunks"
            ),
            "embedding_dimension": result.get(
                "embedding_dimension"
            ),
            "stage": "completed",
        }

        set_job(
            repository_key,
            completed_result,
        )

    except Exception as exc:

        logger.exception(
            "BACKGROUND FAILED: %s",
            repository_url,
        )

        set_job(
            repository_key,
            {
                "status": "failed",
                "repository_key": repository_key,
                "repository": repository_url,
                "stage": "failed",
                "error": str(exc),
            },
        )



@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "AI Repository Intelligence",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/prepare")
def prepare_repository(
    request: PrepareRepositoryRequest,
) -> dict[str, Any]:

    repository_url = (
        request.repository_url.strip()
    )

    if not repository_url:
        raise HTTPException(
            status_code=400,
            detail="Repository URL cannot be empty.",
        )

    repository_key = (
        create_repository_key(
            repository_url
        )
    )

    
    existing_job = get_job(
        repository_key
    )

    if existing_job is not None:

        status = existing_job.get(
            "status"
        )

        # Already processing
        if status == "processing":
            return existing_job

        # Already ready
        if status in {
            "loaded",
            "created",
        }:
            return existing_job

        # Failed previously -> retry
        if status == "failed":

            processing_job = {
                "status": "processing",
                "repository_key": repository_key,
                "repository": repository_url,
                "stage": "retrying",
            }

            set_job(
                repository_key,
                processing_job,
            )

            executor.submit(
                prepare_repository_background,
                repository_url,
                repository_key,
            )

            return processing_job

  
    if index_exists(repository_key):

        try:

            logger.info(
                "Existing index found: %s",
                repository_key,
            )

            indexer = RepositoryIndexer(
                repository_key
            )

            indexer.load()

            # Attach loaded index to current RAG service.
            rag_service.repository_manager.indexer = (
                indexer
            )

            total_chunks = len(
                indexer.vector_store.documents
            )

            result = {
                "status": "loaded",
                "repository_key": repository_key,
                "repository": repository_url,
                "total_chunks": total_chunks,
            }

            set_job(
                repository_key,
                result,
            )

            return result

        except Exception as exc:

            logger.exception(
                "Existing index could not be loaded: %s",
                repository_key,
            )

            processing_job = {
                "status": "processing",
                "repository_key": repository_key,
                "repository": repository_url,
                "stage": "rebuilding_index",
                "message": (
                    "Existing index could not be loaded. "
                    "Rebuilding repository index."
                ),
            }

            set_job(
                repository_key,
                processing_job,
            )

            executor.submit(
                prepare_repository_background,
                repository_url,
                repository_key,
            )

            return processing_job

   
    processing_job = {
        "status": "processing",
        "repository_key": repository_key,
        "repository": repository_url,
        "stage": "queued",
    }

    set_job(
        repository_key,
        processing_job,
    )

    logger.info(
        "Submitting repository to background worker: %s",
        repository_url,
    )

    executor.submit(
        prepare_repository_background,
        repository_url,
        repository_key,
    )

    return processing_job



@app.get(
    "/prepare/status/{repository_key}"
)
def prepare_status(
    repository_key: str,
) -> dict[str, Any]:

    job = get_job(
        repository_key
    )

    if job is not None:
        return job

    
    if index_exists(repository_key):

        try:

            indexer = RepositoryIndexer(
                repository_key
            )

            indexer.load()

            total_chunks = len(
                indexer.vector_store.documents
            )

            return {
                "status": "loaded",
                "repository_key": repository_key,
                "total_chunks": total_chunks,
            }

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Repository index exists but "
                    f"could not be loaded: {exc}"
                ),
            )

    raise HTTPException(
        status_code=404,
        detail=(
            "Repository preparation job "
            "not found."
        ),
    )



@app.post("/ask")
def ask_repository(
    request: AskRequest,
) -> dict[str, Any]:

    repository_url = (
        request.repository_url.strip()
    )

    question = (
        request.question.strip()
    )

   
    if not repository_url:
        raise HTTPException(
            status_code=400,
            detail="Repository URL cannot be empty.",
        )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    repository_key = (
        create_repository_key(
            repository_url
        )
    )

  
    job = get_job(
        repository_key
    )

    if job is not None:

        status = job.get(
            "status"
        )

        if status == "processing":

            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "Repository is still being "
                        "prepared. Please wait until "
                        "preparation is complete."
                    ),
                    "repository_key": repository_key,
                    "status": "processing",
                    "stage": job.get(
                        "stage"
                    ),
                },
            )

        if status == "failed":

            raise HTTPException(
                status_code=500,
                detail={
                    "message": (
                        "Repository preparation failed."
                    ),
                    "repository_key": repository_key,
                    "error": job.get(
                        "error"
                    ),
                },
            )

    
    if (
        job is None
        and index_exists(repository_key)
    ):

        try:

            indexer = RepositoryIndexer(
                repository_key
            )

            indexer.load()

            rag_service.repository_manager.indexer = (
                indexer
            )

            job = {
                "status": "loaded",
                "repository_key": repository_key,
                "repository": repository_url,
                "total_chunks": len(
                    indexer.vector_store.documents
                ),
            }

            set_job(
                repository_key,
                job,
            )

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to load repository index: "
                    f"{exc}"
                ),
            )

   
    if job is None:

        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Repository has not been prepared. "
                    "Call /prepare first."
                ),
                "repository_key": repository_key,
            },
        )

    if job.get("status") not in {
        "loaded",
        "created",
    }:

        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Repository is not ready."
                ),
                "repository_key": repository_key,
                "status": job.get(
                    "status"
                ),
            },
        )

   
    state = {
        "repository_url": repository_url,
        "question": question,
        "top_k": request.top_k,
        "repository_key": repository_key,
    }

    try:

        result = (
            repository_graph.invoke(
                state
            )
        )

        search_results = result.get(
            "search_results",
            [],
        )

        return {
            "answer": result.get(
                "answer",
                "",
            ),
            "sources": result.get(
                "sources",
                [],
            ),
            "retrieved_chunks": result.get(
                "retrieved_chunks",
                len(search_results),
            ),
        }

    except Exception as exc:

        logger.exception(
            "Repository question failed."
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )