# huggingface-hub-search

[![Demo](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Demo-blue)](https://huggingface.co/spaces/hysts-gradio-custom-html/huggingface-hub-search)

A Gradio custom component that provides a live search box for the Hugging Face Hub — models, datasets, spaces, users, and organizations.

Built on top of `gr.HTML` (Gradio 6's custom HTML component API), with no extra frontend build step required.

## Features

- **Live search** — results appear as you type, fetched directly from the Hugging Face Hub API
- **Flexible scope** — search all resource types or restrict to a subset
- **Filter chips** — when multiple types are enabled, toggle-able chips let users narrow results interactively
- **Rich return value** — returns `id`, `type`, and `url` of the selected item
- **Zero frontend toolchain** — pure HTML / CSS / JS served via `gr.HTML`

## Installation

```bash
pip install huggingface-hub-search
```

Requires Python 3.12+ and Gradio 6.6+.

## Quick start

```python
import gradio as gr
from huggingface_hub_search import HuggingFaceHubSearch

def on_select(value: dict | None) -> tuple[str, str, str]:
    if not value:
        return "", "", ""
    return value.get("id") or "", value.get("type") or "", value.get("url") or ""

with gr.Blocks() as demo:
    search = HuggingFaceHubSearch(
        label="Search Hugging Face Hub",
        placeholder="Search models, datasets, spaces...",
        search_type="all",
    )
    id_box   = gr.Textbox(label="ID")
    type_box = gr.Textbox(label="Type")
    url_box  = gr.Textbox(label="URL")

    search.change(fn=on_select, inputs=search, outputs=[id_box, type_box, url_box])

demo.launch()
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `label` | `str \| None` | `None` | Label displayed above the component |
| `placeholder` | `str` | `"Search Hugging Face Hub..."` | Input placeholder text |
| `search_type` | `str \| list[str]` | `"all"` | Resource types to search (see below) |
| `submit_on_select` | `bool` | `True` | Fire the `change` event immediately when an item is selected from the dropdown |
| `result_limit` | `int` | `5` | Maximum number of results shown per category (1–20). The Hugging Face quicksearch API rejects values above 20. |

### `search_type` values

| Value | Description |
|-------|-------------|
| `"all"` | Search all types (models, datasets, spaces, users, organizations) |
| `"model"` | Models only |
| `"dataset"` | Datasets only |
| `"space"` | Spaces only |
| `"user"` | Users only |
| `"org"` | Organizations only |
| `["model", "dataset", "space"]` | Any combination as a list |

When more than one type is active, filter chips appear below the input so users can narrow the search scope interactively.

## Return value

`HuggingFaceHubSearch` passes a `dict` to your event handler:

```python
{
    "id":   "bert-base-uncased",          # repo / user / org ID
    "type": "model",                       # one of the search types above
    "url":  "https://huggingface.co/...", # canonical URL on the Hub
}
```

Returns `None` when the field is cleared.

## Examples

### Restrict to models only

```python
search = HuggingFaceHubSearch(
    label="Search Models",
    placeholder="Search models...",
    search_type="model",
)
```

### Search models, datasets, and spaces

```python
search = HuggingFaceHubSearch(
    label="Search Hub",
    placeholder="Search...",
    search_type=["model", "dataset", "space"],
)
```

### Disable auto-submit on selection

```python
search = HuggingFaceHubSearch(
    search_type="all",
    submit_on_select=False,  # user must press Enter to confirm selection
)
```

### Show more results per category

```python
search = HuggingFaceHubSearch(
    search_type="model",
    result_limit=10,  # up to 10 results per category (max 20, API limit)
)
```

## Development

```bash
# Install dependencies (including dev extras)
uv sync --group dev

# Run unit tests
uv run pytest tests/test_component.py

# Run all tests (including Playwright UI tests)
uv run pytest

# Lint and format
uv run ruff format .
uv run ruff check . --fix
```

The demo app is in `demo/app.py`:

```bash
uv run python demo/app.py
```

## Related projects

Inspired by [`radames/gradio_huggingfacehub_search`](https://github.com/radames/gradio_huggingfacehub_search),
which implements the same concept as a Gradio custom component.
This library takes a different approach — `gr.HTML` with no frontend build step.

## License

MIT
