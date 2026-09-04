from typing import Any


class ContextBuilder:
    """
    Convert retrieved repository chunks into
    structured context for the LLM.
    """

    def __init__(
        self,
        max_context_chars: int = 12000,
    ):
        self.max_context_chars = max_context_chars

    def build(
        self,
        results: list[dict[str, Any]],
    ) -> str:

        if not results:
            return "No relevant repository context was found."

        sections = []
        current_size = 0

        for result in results:

            file_path = result.get(
                "file_path",
                "unknown",
            )

            score = result.get(
                "score",
                0.0,
            )

            content = result.get(
                "content",
                "",
            ).strip()

            if not content:
                continue

            section = (
                f"SOURCE: {file_path}\n"
                f"RELEVANCE: {score:.4f}\n"
                f"{'-' * 60}\n"
                f"{content}\n"
            )

            if (
                current_size + len(section)
                > self.max_context_chars
            ):
                break

            sections.append(section)
            current_size += len(section)

        if not sections:
            return "No usable repository context was found."

        return "\n".join(sections)

    def get_sources(
        self,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        sources = []

        for result in results:

            sources.append(
                {
                    "file_path": result.get(
                        "file_path",
                        "unknown",
                    ),
                    "score": float(
                        result.get("score", 0.0)
                    ),
                }
            )

        return sources