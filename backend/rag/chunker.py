from typing import Any



DEFAULT_CHUNK_SIZE = 4000


DEFAULT_CHUNK_OVERLAP = 500


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Source text.
        chunk_size: Maximum approximate characters per chunk.
        chunk_overlap: Characters repeated between consecutive chunks.

    Returns:
        List of text chunks.
    """

    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    text = text.strip()

    # Small files do not need splitting.
    if len(text) <= chunk_size:
        return [text]

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks


def chunk_repository_files(
    files: list[dict[str, Any]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """
    Convert repository files into RAG-ready chunks.

    Each returned chunk keeps the original file metadata.

    Expected input:
        [
            {
                "path": "backend/auth.py",
                "content": "...",
                "size": 1234,
                "sha": "..."
            }
        ]

    Returns:
        [
            {
                "content": "...",
                "file_path": "backend/auth.py",
                "chunk_index": 0,
                "total_chunks": 3,
                "size": 4000,
                "sha": "..."
            }
        ]
    """

    all_chunks = []

    for file_data in files:
        file_path = file_data.get("path")
        content = file_data.get("content", "")
        sha = file_data.get("sha")

        if not file_path or not content:
            continue

        chunks = chunk_text(
            text=content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        total_chunks = len(chunks)

        for index, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "content": chunk,
                    "file_path": file_path,
                    "chunk_index": index,
                    "total_chunks": total_chunks,
                    "size": len(chunk),
                    "sha": sha,
                }
            )

    return all_chunks