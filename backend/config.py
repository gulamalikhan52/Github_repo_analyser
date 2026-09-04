import os

from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def validate_environment():
    """Validate required environment variables."""

    missing_keys = []

    if not GROQ_API_KEY:
        missing_keys.append("GROQ_API_KEY")

    if not GITHUB_TOKEN:
        missing_keys.append("GITHUB_TOKEN")

    if missing_keys:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing_keys)}"
        )

    return True