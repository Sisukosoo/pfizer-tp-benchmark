"""Check that public-release tracked files do not include private artifacts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BLOCKED_TRACKED_PREFIXES = (
    "data/raw/",
    "data/processed/",
    "output/figures/",
    "output/reports/",
)

ALLOWED_TRACKED_FILES = {
    "data/raw/.gitkeep",
    "data/processed/.gitkeep",
    "output/figures/.gitkeep",
    "output/reports/.gitkeep",
}


def tracked_files() -> list[str]:
    """Return files currently tracked by Git."""

    result = subprocess.run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines()]


def find_private_tracked_files(files: list[str]) -> list[str]:
    """Return tracked files that should remain private/local."""

    blocked = []
    for file_path in files:
        if file_path in ALLOWED_TRACKED_FILES:
            continue
        if any(file_path.startswith(prefix) for prefix in BLOCKED_TRACKED_PREFIXES):
            blocked.append(file_path)
    return blocked


def main() -> int:
    """Run the public-release audit."""

    blocked = find_private_tracked_files(tracked_files())
    if blocked:
        print("Public release audit failed. These private artifacts are tracked:")
        for file_path in blocked:
            print(f"- {file_path}")
        return 1

    print("Public release audit passed.")
    print(
        "No raw Orbis files, processed decision CSVs, or generated outputs are tracked."
    )
    print("Use APP_DATA_MODE=synthetic for public demos and screenshots.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
