"""Atomic write + delete for persona files. Single-purpose Model-layer module."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(target: Path, content: str) -> None:
    """Write `content` to `target` atomically.

    Uses temp-file + os.replace, which is atomic on POSIX. Survives a kill-9
    mid-write — the target file is either the old version or the new version,
    never partial. Cleans up the temp file on any exception.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(dir=target.parent, prefix=".tmp_", suffix=".md")
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, target)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def delete_persona_file(target: Path) -> None:
    """Delete the persona file. Raises FileNotFoundError if absent."""
    target.unlink(missing_ok=False)
