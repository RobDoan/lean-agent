from pathlib import Path

import pytest


@pytest.fixture
def tmp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect HOME so paths.* land in a temp dir."""
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path
