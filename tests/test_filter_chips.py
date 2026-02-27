"""Playwright UI tests for the filter-chip feature of HuggingFaceHubSearch."""

from __future__ import annotations

from typing import TYPE_CHECKING

from conftest import get_search_block
from playwright.sync_api import expect

if TYPE_CHECKING:
    from playwright.sync_api import Page


# ---------------------------------------------------------------------------
# 1) Chip visibility: correct number of chips per search_type
# ---------------------------------------------------------------------------


def test_search_all_shows_five_chips(page: Page) -> None:
    """search_type='all' renders 5 filter chips (Models, Datasets, Spaces, Users, Organizations)."""
    block = get_search_block(page, "Search All")
    chips = block.locator(".hf-search-filter-chip")
    expect(chips).to_have_count(5)

    # All chips should start active
    for i in range(5):
        expect(chips.nth(i)).to_have_class(
            "hf-search-filter-chip active",
        )


def test_single_type_hides_filter_chips(page: Page) -> None:
    """search_type='model' (single type) renders no filter chips."""
    block = get_search_block(page, "Search Models Only")
    chips = block.locator(".hf-search-filter-chip")
    expect(chips).to_have_count(0)


def test_multi_type_shows_three_chips(page: Page) -> None:
    """search_type=['model','dataset','space'] renders 3 filter chips."""
    block = get_search_block(page, "Search Models, Datasets & Spaces")
    chips = block.locator(".hf-search-filter-chip")
    expect(chips).to_have_count(3)

    # Verify the correct labels appear in order
    expect(chips.nth(0)).to_have_text("Models")
    expect(chips.nth(1)).to_have_text("Datasets")
    expect(chips.nth(2)).to_have_text("Spaces")


# ---------------------------------------------------------------------------
# 2) Chip interaction: exclusive select, reset, and additive behaviour
# ---------------------------------------------------------------------------


def test_chip_exclusive_select(page: Page) -> None:
    """Clicking an active chip when multiple are active exclusively selects it."""
    block = get_search_block(page, "Search All")
    chips = block.locator(".hf-search-filter-chip")

    # Initially all 5 chips are active
    expect(chips.nth(0)).to_have_class("hf-search-filter-chip active")

    # Click the first chip (Models) while all are active → exclusive select
    chips.nth(0).click()

    # First chip remains active; all others become inactive
    expect(chips.nth(0)).to_have_class("hf-search-filter-chip active")
    for i in range(1, 5):
        expect(chips.nth(i)).to_have_class("hf-search-filter-chip")


def test_sole_active_chip_resets_all(page: Page) -> None:
    """Clicking the last remaining active chip resets all chips to active."""
    block = get_search_block(page, "Search Models, Datasets & Spaces")
    chips = block.locator(".hf-search-filter-chip")

    # Click first chip → exclusive select (only first is active)
    chips.nth(0).click()
    expect(chips.nth(0)).to_have_class("hf-search-filter-chip active")
    expect(chips.nth(1)).to_have_class("hf-search-filter-chip")
    expect(chips.nth(2)).to_have_class("hf-search-filter-chip")

    # Click the sole active chip → reset: all chips become active again
    chips.nth(0).click()
    expect(chips.nth(0)).to_have_class("hf-search-filter-chip active")
    expect(chips.nth(1)).to_have_class("hf-search-filter-chip active")
    expect(chips.nth(2)).to_have_class("hf-search-filter-chip active")


def test_inactive_chip_adds_to_selection(page: Page) -> None:
    """Clicking an inactive chip adds it to the current selection."""
    block = get_search_block(page, "Search Models, Datasets & Spaces")
    chips = block.locator(".hf-search-filter-chip")

    # Click first chip → exclusive: only chip 0 active
    chips.nth(0).click()
    expect(chips.nth(0)).to_have_class("hf-search-filter-chip active")
    expect(chips.nth(1)).to_have_class("hf-search-filter-chip")

    # Click inactive chip 1 → additive: chips 0 and 1 are both active
    chips.nth(1).click()
    expect(chips.nth(0)).to_have_class("hf-search-filter-chip active")
    expect(chips.nth(1)).to_have_class("hf-search-filter-chip active")
    expect(chips.nth(2)).to_have_class("hf-search-filter-chip")


# ---------------------------------------------------------------------------
# 3) Filter affects dropdown results (requires real API call)
# ---------------------------------------------------------------------------


def test_exclusive_chip_filters_dropdown_results(page: Page) -> None:
    """Exclusively selecting a chip shows only that category in the dropdown."""
    block = get_search_block(page, "Search All")
    search_input = block.locator(".hf-search-input")
    dropdown = block.locator(".hf-search-dropdown")

    # Type a broad query that should return multiple categories
    search_input.fill("bert")

    # Wait for results to appear
    expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

    # Both Models and Datasets category headers should be present initially
    models_header = dropdown.locator(
        ".hf-search-category",
        has=page.locator(".hf-type-model"),
    )
    expect(models_header).to_be_visible()

    # Click the "Datasets" chip (active, multiple active) → exclusive select
    chips = block.locator(".hf-search-filter-chip")
    datasets_chip = chips.nth(1)
    datasets_chip.click()

    # Models category header should now be gone; Datasets should be visible
    expect(
        dropdown.locator(
            ".hf-search-category",
            has=page.locator(".hf-type-model"),
        ),
    ).to_have_count(0)
    expect(
        dropdown.locator(
            ".hf-search-category",
            has=page.locator(".hf-type-dataset"),
        ),
    ).to_be_visible()

    # Click the sole active chip → reset: all categories appear again
    datasets_chip.click()
    expect(
        dropdown.locator(
            ".hf-search-category",
            has=page.locator(".hf-type-model"),
        ),
    ).to_be_visible()
