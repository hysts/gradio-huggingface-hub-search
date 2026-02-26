"""Shared pytest fixtures for the huggingface-hub-search test suite."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Make the demo app importable from every worker process.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "demo"))

from app import demo as _demo  # type: ignore[import-untyped]


@pytest.fixture(scope="module")
def demo_url() -> Generator[str]:
    """Launch the shared demo once per test module and yield its URL.

    Using module scope avoids repeated launch/close cycles and prevents
    port-binding races when running tests in parallel with pytest-xdist.
    """
    _, url, _ = _demo.launch(prevent_thread_lock=True)
    yield url
    _demo.close()
