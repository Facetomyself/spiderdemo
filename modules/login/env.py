"""Load spiderdemo credentials from the project-root .env file.

The file is gitignored. This module returns the values to the caller and does
not log them.
"""

from __future__ import annotations

from pathlib import Path

USERNAME_KEY = "SPIDERDEMO_USERNAME"
PASSWORD_KEY = "SPIDERDEMO_PASSWORD"


def project_root() -> Path:
    """Return the spiderdemo project root (parent of modules/)."""
    return Path(__file__).resolve().parents[2]


def env_path() -> Path:
    return project_root() / ".env"


def load_dotenv(path: Path | None = None) -> dict[str, str]:
    """Parse a simple KEY=VALUE file. Missing file yields an empty mapping."""
    target = env_path() if path is None else path
    if not target.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in target.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def credentials(path: Path | None = None) -> tuple[str, str]:
    """Return username and password. Both must be non-empty."""
    values = load_dotenv(path)
    username = values.get(USERNAME_KEY, "")
    password = values.get(PASSWORD_KEY, "")
    if not username or not password:
        raise ValueError(
            "SPIDERDEMO_USERNAME and SPIDERDEMO_PASSWORD are required in the project .env"
        )
    return username, password
