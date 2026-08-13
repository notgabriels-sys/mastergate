from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def write_contract(tmp_path: Path):
    def write_contract_file(contents: str, name: str = "delivery.toml") -> Path:
        path = tmp_path / name
        path.write_text(contents, encoding="utf-8")
        return path

    return write_contract_file
