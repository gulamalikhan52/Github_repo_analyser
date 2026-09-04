from pathlib import PurePosixPath


SUPPORTED_EXTENSIONS = {
    # Python
    ".py",
    ".pyi",

    # JavaScript / TypeScript
    ".js",
    ".jsx",
    ".ts",
    ".tsx",

    # Java / Kotlin
    ".java",
    ".kt",
    ".kts",

    # C / C++
    ".c",
    ".h",
    ".cpp",
    ".hpp",

    # Go / Rust
    ".go",
    ".rs",

    # PHP / Ruby / C#
    ".php",
    ".rb",
    ".cs",

    # Web
    ".html",
    ".css",
    ".scss",

    # Data / Configuration
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".ini",
    ".cfg",
    ".conf",

    # Documentation
    ".md",
    ".rst",
    ".txt",

    # Shell / SQL
    ".sh",
    ".bash",
    ".ps1",
    ".sql",
}


IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    "coverage",
    "target",
    ".idea",
    ".vscode",
}


IGNORED_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",

    # Dependency lock files can be very large and add little
    # value for semantic repository analysis.
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
}


SPECIAL_FILES = {
    "dockerfile",
    "makefile",
    "procfile",
    "readme",
    "license",
    "authors",
    "notice",
}


def is_relevant_file(path: str) -> bool:
    """Return True if a repository file should be analyzed."""

    if not path:
        return False

    file_path = PurePosixPath(path)

    # Ignore directories.
    if any(
        directory.lower() in IGNORED_DIRECTORIES
        for directory in file_path.parts[:-1]
    ):
        return False

    filename = file_path.name.lower()

    # Ignore sensitive files and unnecessary lock files.
    if filename in IGNORED_FILENAMES:
        return False

    # Include useful extensionless repository files.
    if filename in SPECIAL_FILES:
        return True

    # Include supported extensions.
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS