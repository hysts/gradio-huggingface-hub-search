"""Comprehensive Playwright UI tests for HuggingFaceHubSearch component.

Covers: search & select, keyboard navigation, clear button, dropdown
visibility, click-outside-to-close, filter-chip persistence after selection,
chip state recovery after DOM morph, and result_limit enforcement.
"""

from __future__ import annotations

import gradio as gr
from playwright.sync_api import Locator, Page, expect, sync_playwright

from huggingface_hub_search import HuggingFaceHubSearch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_search_block(page: Page, label_text: str) -> Locator:
    """Return the Gradio block container that has the given label text."""
    return page.locator(".block").filter(
        has=page.locator("[data-testid='block-label']", has_text=label_text),
    )


# ---------------------------------------------------------------------------
# 1) Search & select from dropdown (click)
# ---------------------------------------------------------------------------


def test_select_result_from_dropdown(demo_url: str) -> None:
    """Clicking a dropdown item populates the input with the selected id."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

        # Grab the first item's id before clicking
        first_item = dropdown.locator(".hf-search-item").first
        expect(first_item).to_be_visible()
        item_id = first_item.get_attribute("data-id")
        first_item.click()

        # Dropdown closes and input has the selected id
        expect(dropdown).not_to_have_class("hf-search-dropdown hf-search-open")
        expect(search_input).to_have_value(item_id)

        browser.close()


# ---------------------------------------------------------------------------
# 2) Search & select via keyboard (ArrowDown + Enter)
# ---------------------------------------------------------------------------


def test_select_result_with_keyboard(demo_url: str) -> None:
    """ArrowDown + Enter selects the first dropdown result."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

        first_item = dropdown.locator(".hf-search-item").first
        item_id = first_item.get_attribute("data-id")

        search_input.press("ArrowDown")

        # First item should get the active highlight
        expect(first_item).to_have_class("hf-search-item hf-search-active")

        search_input.press("Enter")

        # Dropdown closes and input has the correct value
        expect(dropdown).not_to_have_class("hf-search-dropdown hf-search-open")
        expect(search_input).to_have_value(item_id)

        browser.close()


# ---------------------------------------------------------------------------
# 3) Enter with no dropdown submits raw text
# ---------------------------------------------------------------------------


def test_enter_submits_raw_text_when_dropdown_closed(demo_url: str) -> None:
    """Pressing Enter when the dropdown is closed submits the typed text."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search Models Only")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        # Type text then immediately press Enter before debounce triggers
        search_input.focus()
        search_input.type("my-custom-model", delay=10)

        # Close any dropdown that might have appeared
        search_input.press("Escape")
        expect(dropdown).not_to_have_class("hf-search-dropdown hf-search-open")

        search_input.press("Enter")

        # Input keeps the typed text
        expect(search_input).to_have_value("my-custom-model")

        browser.close()


# ---------------------------------------------------------------------------
# 4) Clear button
# ---------------------------------------------------------------------------


def test_clear_button_appears_on_input(demo_url: str) -> None:
    """The clear button (X) becomes visible when the input has text."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(5000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        clear_btn = block.locator(".hf-search-clear")

        # Initially hidden (input is empty)
        expect(clear_btn).to_be_hidden()

        # Type something — clear button appears
        search_input.fill("test")
        expect(clear_btn).to_be_visible()

        browser.close()


def test_clear_button_resets_input(demo_url: str) -> None:
    """Clicking the clear button empties the input and hides the button."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(5000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        clear_btn = block.locator(".hf-search-clear")

        search_input.fill("bert")
        expect(clear_btn).to_be_visible()

        clear_btn.click()

        expect(search_input).to_have_value("")
        expect(clear_btn).to_be_hidden()

        browser.close()


def test_clear_button_visible_after_select(demo_url: str) -> None:
    """After selecting a dropdown result, the clear button must be visible."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")
        clear_btn = block.locator(".hf-search-clear")

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")
        dropdown.locator(".hf-search-item").first.click()

        # Input has a value → clear button must be visible
        expect(clear_btn).to_be_visible()

        browser.close()


# ---------------------------------------------------------------------------
# 5) Dropdown visibility
# ---------------------------------------------------------------------------


def test_dropdown_opens_on_typing(demo_url: str) -> None:
    """Typing a query opens the dropdown when results arrive."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        # Initially closed
        expect(dropdown).not_to_have_class("hf-search-dropdown hf-search-open")

        search_input.fill("bert")

        # Dropdown opens after debounce + API response
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

        # Contains at least one result item
        expect(dropdown.locator(".hf-search-item").first).to_be_visible()

        browser.close()


def test_dropdown_closes_on_escape(demo_url: str) -> None:
    """Pressing Escape closes the dropdown."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

        search_input.press("Escape")
        expect(dropdown).not_to_have_class("hf-search-dropdown hf-search-open")

        browser.close()


def test_dropdown_closes_on_click_outside(demo_url: str) -> None:
    """Clicking outside the search component closes the dropdown."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

        # Click somewhere outside — use the page title/heading
        page.locator("text=Hugging Face Hub Search Demo").click()

        expect(dropdown).not_to_have_class("hf-search-dropdown hf-search-open")

        browser.close()


def test_dropdown_closes_on_clear(demo_url: str) -> None:
    """Clearing the input closes the dropdown."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")
        clear_btn = block.locator(".hf-search-clear")

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

        clear_btn.click()
        expect(dropdown).not_to_have_class("hf-search-dropdown hf-search-open")

        browser.close()


# ---------------------------------------------------------------------------
# 6) Keyboard navigation (arrow keys)
# ---------------------------------------------------------------------------


def test_arrow_keys_navigate_results(demo_url: str) -> None:
    """ArrowDown/ArrowUp move the active highlight through results."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

        items = dropdown.locator(".hf-search-item")
        # Need at least 2 results for navigation test
        expect(items.nth(1)).to_be_visible()

        # No item is initially active
        expect(items.nth(0)).not_to_have_class("hf-search-item hf-search-active")

        # ArrowDown → first item active
        search_input.press("ArrowDown")
        expect(items.nth(0)).to_have_class("hf-search-item hf-search-active")
        expect(items.nth(1)).not_to_have_class("hf-search-item hf-search-active")

        # ArrowDown → second item active
        search_input.press("ArrowDown")
        expect(items.nth(0)).not_to_have_class("hf-search-item hf-search-active")
        expect(items.nth(1)).to_have_class("hf-search-item hf-search-active")

        # ArrowUp → back to first
        search_input.press("ArrowUp")
        expect(items.nth(0)).to_have_class("hf-search-item hf-search-active")
        expect(items.nth(1)).not_to_have_class("hf-search-item hf-search-active")

        browser.close()


# ---------------------------------------------------------------------------
# 7) Filter chips survive selection (regression for reported bug)
# ---------------------------------------------------------------------------


def test_chips_visible_after_selecting_result(demo_url: str) -> None:
    """Filter chips must still be visible after selecting a dropdown result."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")
        chips = block.locator(".hf-search-filter-chip")

        expect(chips).to_have_count(5)

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")
        dropdown.locator(".hf-search-item").first.click()

        # Chips must still be present and visible
        expect(chips).to_have_count(5)
        for i in range(5):
            expect(chips.nth(i)).to_be_visible()

        browser.close()


def test_chips_visible_after_clearing_selection(demo_url: str) -> None:
    """Filter chips must remain after selecting then clearing."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")
        chips = block.locator(".hf-search-filter-chip")

        expect(chips).to_have_count(5)

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")
        dropdown.locator(".hf-search-item").first.click()

        # Clear
        block.locator(".hf-search-clear").click()
        expect(search_input).to_have_value("")

        # Chips must still be present
        expect(chips).to_have_count(5)
        for i in range(5):
            expect(chips.nth(i)).to_be_visible()

        browser.close()


def test_chips_visible_after_keyboard_select(demo_url: str) -> None:
    """Filter chips must remain after keyboard selection."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")
        chips = block.locator(".hf-search-filter-chip")

        expect(chips).to_have_count(5)

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")
        search_input.press("ArrowDown")
        search_input.press("Enter")

        expect(chips).to_have_count(5)
        for i in range(5):
            expect(chips.nth(i)).to_be_visible()

        browser.close()


# ---------------------------------------------------------------------------
# 8) Chip toggle still works after selection + morph
# ---------------------------------------------------------------------------


def test_chip_toggle_works_after_select(demo_url: str) -> None:
    """Filter chip click still works after selecting a result (DOM morph)."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")
        chips = block.locator(".hf-search-filter-chip")

        # Select a result (triggers DOM morph)
        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")
        dropdown.locator(".hf-search-item").first.click()

        # Chip clicks should still work after DOM morph.
        # Click first chip (active, multiple active) → exclusive select:
        # first chip stays active, all others become inactive.
        first_chip = chips.nth(0)
        expect(first_chip).to_have_class("hf-search-filter-chip active")

        first_chip.click()
        expect(first_chip).to_have_class("hf-search-filter-chip active")
        for i in range(1, 5):
            expect(chips.nth(i)).to_have_class("hf-search-filter-chip")

        # Click the sole active chip → reset: all chips become active again
        first_chip.click()
        expect(first_chip).to_have_class("hf-search-filter-chip active")
        expect(chips.nth(1)).to_have_class("hf-search-filter-chip active")

        browser.close()


# ---------------------------------------------------------------------------
# 9) Category headers in dropdown
# ---------------------------------------------------------------------------


def test_dropdown_shows_category_headers(demo_url: str) -> None:
    """Dropdown results include category headers with colored dots."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

        # At least one category header should be present
        headers = dropdown.locator(".hf-search-category")
        expect(headers.first).to_be_visible()

        # Category header should contain a colored dot
        expect(headers.first.locator(".hf-search-category-dot")).to_be_visible()

        browser.close()


# ---------------------------------------------------------------------------
# 10) Single-type search has no chips but still works
# ---------------------------------------------------------------------------


def test_single_type_search_works_without_chips(demo_url: str) -> None:
    """Single-type search (model) has no filter chips but search works."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search Models Only")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")
        chips = block.locator(".hf-search-filter-chip")

        # No chips
        expect(chips).to_have_count(0)

        # Search still works
        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")
        expect(dropdown.locator(".hf-search-item").first).to_be_visible()

        browser.close()


# ---------------------------------------------------------------------------
# 11) Multi-type search chips survive selection
# ---------------------------------------------------------------------------


def test_multi_type_chips_survive_selection(demo_url: str) -> None:
    """3-type search chips survive a select + clear cycle."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search Models, Datasets & Spaces")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")
        chips = block.locator(".hf-search-filter-chip")

        expect(chips).to_have_count(3)

        # Search + select
        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")
        dropdown.locator(".hf-search-item").first.click()

        # Chips still present
        expect(chips).to_have_count(3)
        expect(chips.nth(0)).to_have_text("Models")
        expect(chips.nth(1)).to_have_text("Datasets")
        expect(chips.nth(2)).to_have_text("Spaces")

        # Clear and chips still present
        block.locator(".hf-search-clear").click()
        expect(chips).to_have_count(3)

        browser.close()


# ---------------------------------------------------------------------------
# 12) Empty search results show "No results found" message
# ---------------------------------------------------------------------------


def test_dropdown_shows_no_results_message(demo_url: str) -> None:
    """An obscure query that yields no API results shows 'No results found' in the dropdown."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        # Use a nonsense query extremely unlikely to match any real HF entity
        search_input.fill("xyzzy_noresults_gradiotest_42zqx")

        # Dropdown opens even when empty (renderEmpty + openDropdown are both called)
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

        # Status message visible with correct text
        status = dropdown.locator(".hf-search-status")
        expect(status).to_be_visible()
        expect(status).to_have_text("No results found")

        # No result items rendered
        expect(dropdown.locator(".hf-search-item")).to_have_count(0)

        browser.close()


# ---------------------------------------------------------------------------
# 13) submit_on_select=False: dropdown click does not commit; Enter does
# ---------------------------------------------------------------------------


def test_submit_on_select_false_does_not_trigger_change() -> None:
    """With submit_on_select=False, clicking a dropdown result fills the input.

    The change handler must NOT fire on click; only an explicit Enter press
    commits the value and fires change.
    """

    def on_change(value: dict | None) -> str:
        if not value:
            return ""
        return value.get("id") or ""

    with gr.Blocks() as _demo:
        search = HuggingFaceHubSearch(
            label="Test Search",
            search_type="model",
            submit_on_select=False,
        )
        change_out = gr.Textbox(label="Change Event Result")
        search.change(fn=on_change, inputs=search, outputs=change_out)

    _, url, _ = _demo.launch(prevent_thread_lock=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_default_timeout(10000)
            page.goto(url)

            block = _get_search_block(page, "Test Search")
            search_input = block.locator(".hf-search-input")
            dropdown = block.locator(".hf-search-dropdown")
            change_result = page.get_by_label("Change Event Result")

            search_input.fill("bert")
            expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

            first_item = dropdown.locator(".hf-search-item").first
            item_id = first_item.get_attribute("data-id")
            first_item.click()

            # Dropdown closed and input filled — but change NOT fired yet
            expect(dropdown).not_to_have_class("hf-search-dropdown hf-search-open")
            expect(search_input).to_have_value(item_id)
            expect(change_result).to_have_value("")

            # Explicit Enter press → change fires
            search_input.press("Enter")
            expect(change_result).not_to_have_value("")

            browser.close()
    finally:
        _demo.close()


# ---------------------------------------------------------------------------
# 14) Focus on input reopens dropdown with cached results
# ---------------------------------------------------------------------------


def test_focus_reopens_dropdown_with_cached_results(demo_url: str) -> None:
    """Re-focusing the input after clicking outside reopens the dropdown with cached results."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(10000)
        page.goto(demo_url)

        block = _get_search_block(page, "Search All")
        search_input = block.locator(".hf-search-input")
        dropdown = block.locator(".hf-search-dropdown")

        # Search and wait for results
        search_input.fill("bert")
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")
        expect(dropdown.locator(".hf-search-item").first).to_be_visible()

        # Click outside to close the dropdown
        page.locator("text=Hugging Face Hub Search Demo").click()
        expect(dropdown).not_to_have_class("hf-search-dropdown hf-search-open")

        # Click (focus) the input again — cached results should reopen the dropdown
        search_input.click()
        expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")
        expect(dropdown.locator(".hf-search-item").first).to_be_visible()

        browser.close()


# ---------------------------------------------------------------------------
# 15) result_limit: dropdown item count is capped at the configured limit
# ---------------------------------------------------------------------------


def test_result_limit_caps_dropdown_items() -> None:
    """result_limit=2 must produce at most 2 items per category in the dropdown."""

    with gr.Blocks() as _demo:
        HuggingFaceHubSearch(
            label="Limited Search",
            search_type="model",
            result_limit=2,
        )

    _, url, _ = _demo.launch(prevent_thread_lock=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_default_timeout(10000)
            page.goto(url)

            block = _get_search_block(page, "Limited Search")
            search_input = block.locator(".hf-search-input")
            dropdown = block.locator(".hf-search-dropdown")

            search_input.fill("bert")
            expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

            items = dropdown.locator(".hf-search-item")
            # "bert" has many model results; with limit=2, only 2 should appear
            expect(items).to_have_count(2)

            browser.close()
    finally:
        _demo.close()


def test_result_limit_larger_than_default_shows_more_items() -> None:
    """result_limit=10 shows more items than the default of 5 for a broad query."""

    with gr.Blocks() as _demo:
        HuggingFaceHubSearch(
            label="Wide Search",
            search_type="model",
            result_limit=10,
        )

    _, url, _ = _demo.launch(prevent_thread_lock=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_default_timeout(10000)
            page.goto(url)

            block = _get_search_block(page, "Wide Search")
            search_input = block.locator(".hf-search-input")
            dropdown = block.locator(".hf-search-dropdown")

            search_input.fill("bert")
            expect(dropdown).to_have_class("hf-search-dropdown hf-search-open")

            items = dropdown.locator(".hf-search-item")
            # "bert" has many model results; 10-item limit should yield > 5
            expect(items).to_have_count(10)

            browser.close()
    finally:
        _demo.close()
