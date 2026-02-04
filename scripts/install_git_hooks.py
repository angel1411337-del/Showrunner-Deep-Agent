"""Install Showrunner git hooks for passive mode."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

PRE_COMMIT = """#!/usr/bin/env sh
set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
  exit 0
fi

if command -v uv >/dev/null 2>&1; then
  uv run python -m showrunner.hooks.git_hook_handler --hook pre-commit --repo-root "$REPO_ROOT" || true
elif command -v python >/dev/null 2>&1; then
  python -m showrunner.hooks.git_hook_handler --hook pre-commit --repo-root "$REPO_ROOT" || true
fi

exit 0
"""

POST_COMMIT = """#!/usr/bin/env sh
set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
  exit 0
fi

if command -v uv >/dev/null 2>&1; then
  uv run python -m showrunner.hooks.git_hook_handler --hook post-commit --repo-root "$REPO_ROOT" || true
elif command -v python >/dev/null 2>&1; then
  python -m showrunner.hooks.git_hook_handler --hook post-commit --repo-root "$REPO_ROOT" || true
fi

exit 0
"""


def _git_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip())


def _write_hook(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    try:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        # On Windows, chmod may be a no-op; hooks still run via git-bash.
        pass


def install_hooks(repo_root: Path | None = None) -> None:
    root = repo_root or _git_root()
    hooks_dir = root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    _write_hook(hooks_dir / "pre-commit", PRE_COMMIT)
    _write_hook(hooks_dir / "post-commit", POST_COMMIT)


def main() -> int:
    repo_root = Path(os.getcwd())
    install_hooks(repo_root)
    print("Showrunner hooks installed in .git/hooks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
