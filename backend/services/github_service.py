import base64
import re
import os
from dotenv import load_dotenv

import requests

from backend.config import GITHUB_TOKEN
load_dotenv()

GITHUB_API_URL = "https://api.github.com"


def get_github_headers():
    """Return headers required for GitHub API requests."""

    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def parse_repository_url(repository_url: str):
    """
    Extract owner and repository name from a GitHub URL.

    Example:
        https://github.com/owner/repository
        -> ("owner", "repository")
    """

    if not repository_url:
        raise ValueError("Repository URL cannot be empty.")

    repository_url = repository_url.strip()

    pattern = r"^https?://github\.com/([^/]+)/([^/#?]+?)/?$"

    match = re.match(pattern, repository_url)

    if not match:
        raise ValueError(
            "Invalid GitHub repository URL. "
            "Use format: https://github.com/owner/repository"
        )

    owner = match.group(1)
    repo = match.group(2)

    return owner, repo


def get_authenticated_user():
    """Verify GitHub authentication."""

    response = requests.get(
        f"{GITHUB_API_URL}/user",
        headers=get_github_headers(),
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_repository(repository_url: str):
    """
    Fetch repository metadata from any accessible GitHub repository.
    """

    owner, repo = parse_repository_url(repository_url)

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"

    response = requests.get(
        url,
        headers=get_github_headers(),
        timeout=10,
    )

    if response.status_code == 404:
        raise ValueError(
            "Repository not found or you do not have permission "
            "to access it."
        )

    response.raise_for_status()

    return response.json()


def get_repository_tree(repository_url: str):
    """
    Fetch the complete file tree of a GitHub repository.
    """

    owner, repo = parse_repository_url(repository_url)

    repository = get_repository(repository_url)

    default_branch = repository.get("default_branch")

    if not default_branch:
        raise ValueError(
            "Could not determine repository default branch."
        )

    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{owner}/{repo}/git/trees/{default_branch}"
    )

    response = requests.get(
        url,
        headers=get_github_headers(),
        params={"recursive": "1"},
        timeout=30,
    )

    if response.status_code == 404:
        raise ValueError(
            "Repository tree could not be found or is not accessible."
        )

    response.raise_for_status()

    data = response.json()

    return {
        "owner": owner,
        "repository": repo,
        "default_branch": default_branch,
        "tree": data.get("tree", []),
        "truncated": data.get("truncated", False),
    }


def get_file_content(
    repository_url: str,
    file_path: str,
    default_branch: str | None = None,
):
    """
    Fetch the content of a single file.

    If default_branch is provided, repository metadata
    does not need to be fetched again.
    """

    owner, repo = parse_repository_url(repository_url)

    # Only fetch repository metadata if branch is not supplied.
    if default_branch is None:
        repository = get_repository(repository_url)

        default_branch = repository.get("default_branch")

        if not default_branch:
            raise ValueError(
                "Could not determine repository default branch."
            )

    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{owner}/{repo}/contents/{file_path}"
    )

    response = requests.get(
        url,
        headers=get_github_headers(),
        params={"ref": default_branch},
        timeout=30,
    )

    if response.status_code == 404:
        raise ValueError(
            f"File not found or inaccessible: {file_path}"
        )

    response.raise_for_status()

    data = response.json()

    if data.get("type") != "file":
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    if data.get("encoding") != "base64":
        raise ValueError(
            f"Unsupported file encoding: {data.get('encoding')}"
        )

    content = base64.b64decode(
        data["content"]
    ).decode(
        "utf-8",
        errors="replace",
    )

    return {
        "path": file_path,
        "content": content,
        "size": data.get("size", 0),
        "sha": data.get("sha"),
    }
