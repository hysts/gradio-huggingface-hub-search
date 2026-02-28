from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gradio as gr

_STATIC_DIR = Path(__file__).parent / "static"

_VALID_SEARCH_TYPES = frozenset({"model", "dataset", "space", "user", "org"})

_RESULT_LIMIT_DEFAULT = 5
# The Hugging Face quicksearch API rejects requests with limit > 20 (HTTP 400).
_RESULT_LIMIT_MAX = 20

# Ordered category definitions matching the frontend CATEGORIES object.
_CATEGORY_ORDER = ("model", "dataset", "space", "user", "org")
_CATEGORY_LABELS: dict[str, str] = {
    "model": "Models",
    "dataset": "Datasets",
    "space": "Spaces",
    "user": "Users",
    "org": "Organizations",
}


def _build_filters_html(search_type_str: str) -> str:
    """Build the static HTML for filter chip buttons.

    Returns an empty string when only one type is active (no chips needed).
    """
    types = list(_CATEGORY_ORDER) if search_type_str == "all" else [t.strip() for t in search_type_str.split(",")]

    if len(types) <= 1:
        return ""

    chips: list[str] = []
    for t in _CATEGORY_ORDER:
        if t not in types:
            continue
        label = _CATEGORY_LABELS[t]
        chips.append(
            f'<button type="button" class="hf-search-filter-chip active" data-type="{t}">'
            f'<span class="hf-search-filter-dot hf-type-{t}"></span>'
            f"{label}</button>"
        )
    return "".join(chips)


def _normalize_search_type(search_type: str | list[str]) -> str:
    """Normalize search_type to a comma-separated string for the frontend."""
    if isinstance(search_type, str):
        if search_type == "all":
            return "all"
        types = [search_type]
    else:
        types = list(search_type)

    for t in types:
        if t not in _VALID_SEARCH_TYPES:
            msg = f"Invalid search_type '{t}'. Must be one of {sorted(_VALID_SEARCH_TYPES)} or 'all'."
            raise ValueError(msg)

    return ",".join(types)


class HuggingFaceHubSearch(gr.HTML):
    def __init__(
        self,
        value: str | None = None,
        *,
        label: str | None = None,
        placeholder: str = "Search Hugging Face Hub...",
        search_type: str | list[str] = "all",
        submit_on_select: bool = True,
        result_limit: int = _RESULT_LIMIT_DEFAULT,
        **kwargs: Any,  # noqa: ANN401 - must accept arbitrary kwargs for gr.HTML
    ) -> None:
        if (
            isinstance(result_limit, bool)
            or not isinstance(result_limit, int)
            or not (1 <= result_limit <= _RESULT_LIMIT_MAX)
        ):
            msg = f"result_limit must be an integer between 1 and {_RESULT_LIMIT_MAX}, got {result_limit!r}."
            raise ValueError(msg)

        search_type_str = _normalize_search_type(search_type)
        filters_html = _build_filters_html(search_type_str)

        html_template = (_STATIC_DIR / "template.html").read_text(encoding="utf-8")
        css_template = (_STATIC_DIR / "style.css").read_text(encoding="utf-8")
        js_on_load = (_STATIC_DIR / "script.js").read_text(encoding="utf-8")

        super().__init__(
            value=value,
            label=label,
            show_label=label is not None,
            container=label is not None,
            html_template=html_template,
            css_template=css_template,
            js_on_load=js_on_load,
            placeholder=placeholder,
            search_type=search_type_str,
            submit_on_select=submit_on_select,
            result_limit=result_limit,
            filters_html=filters_html,
            **kwargs,
        )

    def preprocess(self, value: str | None) -> dict[str, str | None] | None:
        if not value:
            return None
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        # Plain string (backward compat) — wrap as minimal dict
        return {"id": value, "type": None, "url": None}

    def postprocess(self, value: str | dict | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get("id")
        return str(value)

    def api_info(self) -> dict[str, Any]:
        return {
            "type": "object",
            "description": "Selected Hugging Face Hub entity with its id, type, and URL.",
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"},
                "url": {"type": "string"},
            },
        }
