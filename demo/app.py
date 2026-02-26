import gradio as gr

from huggingface_hub_search import HuggingFaceHubSearch


def on_select(value: dict | None) -> tuple[str, str, str]:
    if not value:
        return "", "", ""
    return (
        value.get("id") or "",
        value.get("type") or "",
        value.get("url") or "",
    )


with gr.Blocks() as demo:
    gr.Markdown("## Hugging Face Hub Search Demo")

    with gr.Row():
        with gr.Column():
            search_all = HuggingFaceHubSearch(
                label="Search All",
                placeholder="Search models, datasets, spaces...",
                search_type="all",
            )
            output_id = gr.Textbox(label="Selected ID")
            output_type = gr.Textbox(label="Type")
            output_url = gr.Textbox(label="URL")

        with gr.Column():
            search_models = HuggingFaceHubSearch(
                label="Search Models Only",
                placeholder="Search models...",
                search_type="model",
            )
            output_models_id = gr.Textbox(label="Selected ID")
            output_models_type = gr.Textbox(label="Type")
            output_models_url = gr.Textbox(label="URL")

        with gr.Column():
            search_multi = HuggingFaceHubSearch(
                label="Search Models, Datasets & Spaces",
                placeholder="Search models, datasets, spaces...",
                search_type=["model", "dataset", "space"],
            )
            output_multi_id = gr.Textbox(label="Selected ID")
            output_multi_type = gr.Textbox(label="Type")
            output_multi_url = gr.Textbox(label="URL")

    search_all.change(
        fn=on_select,
        inputs=search_all,
        outputs=[output_id, output_type, output_url],
    )
    search_models.change(
        fn=on_select,
        inputs=search_models,
        outputs=[output_models_id, output_models_type, output_models_url],
    )
    search_multi.change(
        fn=on_select,
        inputs=search_multi,
        outputs=[output_multi_id, output_multi_type, output_multi_url],
    )

if __name__ == "__main__":
    demo.launch()
