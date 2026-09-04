import io
import logging
import zipfile
from pathlib import PurePosixPath

import requests

from backend.services.github_service import (
    parse_repository_url,
    get_github_headers,
)
from backend.utils.file_filter import is_relevant_file


logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 500_000


def collect_repository_files(repository_url: str):
    """
    Download a GitHub repository as a ZIP archive and collect
    only relevant source/documentation files.

    This intentionally avoids GitHub REST repository/tree APIs
    because the ZIP download works independently of the API
    core-rate-limit bucket.
    """

    logger.info("Starting repository collection: %s", repository_url)

    # Parse owner/repository from URL
    owner, repo = parse_repository_url(repository_url)

    logger.info("Repository: %s/%s", owner, repo)

    headers = get_github_headers()

    # GitHub's default branch is not required for downloading
    # the repository. GitHub redirects the archive request to
    # the correct repository archive.
    archive_url = (
        f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
    )

    logger.info("Downloading repository ZIP archive...")

    response = requests.get(
        archive_url,
        headers=headers,
        timeout=(15, 300),
        allow_redirects=True,
    )

    # Some repositories use master instead of main.
    if response.status_code == 404:
        logger.info("main branch not found. Trying master branch...")

        archive_url = (
            f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"
        )

        response = requests.get(
            archive_url,
            headers=headers,
            timeout=(15, 300),
            allow_redirects=True,
        )

    response.raise_for_status()

    logger.info(
        "Repository archive downloaded: %.2f MB",
        len(response.content) / (1024 * 1024),
    )

    content_type = response.headers.get("Content-Type", "")

    if "zip" not in content_type.lower():
        raise RuntimeError(
            f"GitHub did not return a ZIP archive. "
            f"Content-Type: {content_type}"
        )

    try:
        archive = zipfile.ZipFile(io.BytesIO(response.content))
    except zipfile.BadZipFile as exc:
        raise RuntimeError(
            "GitHub returned an invalid repository archive."
        ) from exc

    collected_files = []
    skipped_files = []

    archive_members = archive.infolist()

    logger.info(
        "Archive contains %s entries.",
        len(archive_members),
    )

    for member in archive_members:

        if member.is_dir():
            continue

        archive_path = member.filename

        parts = PurePosixPath(archive_path).parts

        # ZIP structure:
        # repository-branch/
        # repository-branch/backend/main.py
        if len(parts) < 2:
            continue

        file_path = "/".join(parts[1:])

        if not file_path:
            continue

        # Filter irrelevant files/directories
        if not is_relevant_file(file_path):

            skipped_files.append(
                {
                    "path": file_path,
                    "reason": "unsupported_or_ignored_file",
                }
            )

            continue

        file_size = member.file_size

        # Avoid extremely large files
        if file_size > MAX_FILE_SIZE:

            skipped_files.append(
                {
                    "path": file_path,
                    "reason": "file_too_large",
                    "size": file_size,
                }
            )

            continue

        try:
            raw_content = archive.read(member)

            content = raw_content.decode("utf-8")

        except UnicodeDecodeError:

            skipped_files.append(
                {
                    "path": file_path,
                    "reason": "non_utf8_file",
                }
            )

            continue

        except Exception as exc:

            skipped_files.append(
                {
                    "path": file_path,
                    "reason": f"archive_read_error: {exc}",
                }
            )

            continue

        collected_files.append(
            {
                "path": file_path,
                "content": content,
                "size": file_size,
            }
        )

    archive.close()

    logger.info("Repository collection completed.")
    logger.info(
        "Collected files: %s",
        len(collected_files),
    )
    logger.info(
        "Skipped files: %s",
        len(skipped_files),
    )

    return {
        "repository": f"{owner}/{repo}",
        "default_branch": None,
        "files": collected_files,
        "skipped_files": skipped_files,
        "total_files": len(collected_files),
        "total_skipped": len(skipped_files),
    }