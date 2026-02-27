"""Shared pytest fixtures for the huggingface-hub-search test suite."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import sync_playwright

if TYPE_CHECKING:
    from collections.abc import Generator

    from playwright.sync_api import Browser, Locator, Page

from _demo import demo as _demo

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_search_block(page: Page, label_text: str) -> Locator:
    """Return the Gradio block container that has the given label text."""
    return page.locator(".block").filter(
        has=page.locator("[data-testid='block-label']", has_text=label_text),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def browser() -> Generator[Browser]:
    """Launch a single Chromium instance shared across all test modules."""
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture(scope="module")
def demo_url() -> Generator[str]:
    """Launch the shared demo once per test module and yield its URL.

    Using module scope avoids repeated launch/close cycles and prevents
    port-binding races when running tests in parallel with pytest-xdist.
    """
    _, url, _ = _demo.launch(prevent_thread_lock=True)
    yield url
    _demo.close()


@pytest.fixture
def page(browser: Browser, demo_url: str) -> Generator[Page]:
    """Create a fresh browser page pointing at the demo for each test."""
    pg = browser.new_page()
    pg.set_default_timeout(10000)
    pg.goto(demo_url)
    yield pg
    pg.close()
