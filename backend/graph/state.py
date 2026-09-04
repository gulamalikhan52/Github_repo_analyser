from typing import TypedDict, List, Dict, Any


class RepositoryState(TypedDict, total=False):
    repository_url: str
    question: str

    top_k: int

    repository_key: str
    repository_name: str

    search_results: List[Dict[str, Any]]
    retrieved_chunks: int

    context: str
    sources: List[Dict[str, Any]]

    answer: str

    error: str