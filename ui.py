import gradio as gr


def build_ui(
    on_chat_submit, index_files, on_clear_qdrant, on_clear_minio, on_clear_all
):
    """Build and return the Gradio Blocks UI.

    Parameters
    ----------
    on_chat_submit: callable
        The function that handles chat submissions. Must have signature
        (message, chat_history, k, ai_enabled, temperature, system_prompt_input) -> generator/tuple
    index_files: callable
        The function that handles indexing uploaded files. Must accept (files) and return status text.
    on_clear_qdrant: callable
        Function to clear the Qdrant collection. Accepts (confirmed: bool) -> str
    on_clear_minio: callable
        Function to clear MinIO images. Accepts (confirmed: bool) -> str
    on_clear_all: callable
        Function to clear both storages. Accepts (confirmed: bool) -> str
    """
    with gr.Blocks(
        theme=gr.themes.Citrus(),
        fill_height=True,
        css="""
/* Examples container directly under chat, full width */
#examples {
  width: 100%;
  margin-top: 8px;
  padding: 8px;
  border: 1px solid var(--border-color-primary);
  border-radius: 12px;
}

/* Make inner layout responsive regardless of Gradio version markup */
#examples .grid,
#examples .examples,
#examples .gr-examples,
#examples > div {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px;
}

/* Pill styling for each example item */
#examples .example,
#examples button,
#examples .gr-button,
#examples .sample,
#examples .border {
  border-radius: 999px;
  border: 1px solid var(--border-color-primary);
  background: var(--background-fill-primary);
  padding: 8px 12px;
  transition: border-color .2s ease, background .2s ease, transform .05s ease;
  cursor: pointer;
}

#examples .example:hover,
#examples button:hover,
#examples .gr-button:hover {
  border-color: var(--color-accent);
  background: var(--background-fill-secondary);
}

#examples .example:active,
#examples button:active,
#examples .gr-button:active {
  transform: translateY(1px);
}
""",
    ) as demo:
        # Title bar
        gr.Markdown(
            (
                "# Vision RAG Template\n"
                "Proof of concept of efficient page-level retrieval with a 'Special' Generative touch."
            )
        )

        # Collapsible sidebar (upload + indexing)
        with gr.Sidebar(open=True, elem_id="app-sidebar", width=425):
            gr.Markdown("### 📂 Upload & Index")
            files = gr.File(
                label="PDF documents",
                file_types=[".pdf"],
                file_count="multiple",
                type="filepath",
            )
            convert_button = gr.Button("🔄 Index documents", variant="secondary")
            status = gr.Textbox(
                value="Files not yet uploaded",
                label="Status",
                interactive=False,
                lines=1,
            )
            gr.Markdown("---")
            gr.Markdown("### 🤖 AI Settings")
            ai_enabled = gr.Checkbox(value=True, label="Enable AI responses")
            temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                step=0.1,
                value=0.7,
                label="Temperature",
                interactive=True,
            )
            system_prompt_input = gr.Textbox(
                label="Custom system prompt",
                lines=4,
                placeholder="Optional. Overrides default system behavior.",
            )
            gr.Markdown("---")
            gr.Markdown("### 🔎 Retrieval Settings")
            k = gr.Dropdown(
                choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                value=5,
                label="Top-k results",
                interactive=True,
            )

            # Danger Zone
            gr.Markdown("---")
            gr.Markdown("### ⚠️ Danger Zone")
            danger_confirm = gr.Checkbox(
                value=False,
                label="I understand this action will delete all data.",
            )
            with gr.Row():
                clear_qdrant_btn = gr.Button(
                    "🗑️ Clear Qdrant Collection", variant="secondary"
                )
                clear_minio_btn = gr.Button("🗑️ Clear MinIO Images", variant="secondary")
            clear_all_btn = gr.Button(
                "🧨 Clear Both (Qdrant + MinIO)", variant="secondary"
            )
            danger_status = gr.Textbox(
                value="",
                label="Danger Zone Status",
                interactive=False,
                lines=2,
            )

        # Main content
        with gr.Column():
            chat = gr.Chatbot(
                label="Chat",
                show_label=False,
                type="messages",
                layout="bubble",
                height=425,
                min_height=300,
                resizable=False,
                autoscroll=False,
                render_markdown=True,
                sanitize_html=True,
                group_consecutive_messages=True,
                line_breaks=True,
                show_copy_button=True,
                show_copy_all_button=True,
                show_share_button=True,
                placeholder="What would you like to know today?",
            )

            msg = gr.Textbox(
                placeholder="Ask a question regarding your uploaded PDFs",
                lines=1,
                autofocus=True,
            )
            gr.Examples(
                examples=[
                    ["What is the booking reference for case 002?"],
                    ["What is the claimant’s desired outcome for case 006?"],
                    ["Has any payment been received for case 001?"],
                    ["What is the claimant’s desired outcome for case 0015?"],
                ],
                inputs=[msg],
                elem_id="examples",
                label="",
            )

            with gr.Row():
                send_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear", variant="secondary")

            with gr.Accordion("Retrieved Pages", open=True):
                output_gallery = gr.Gallery(
                    label="Retrieved Pages",
                    show_label=False,
                    columns=4,
                )

        # Wiring
        convert_button.click(index_files, inputs=[files], outputs=[status])

        # Danger Zone wiring
        clear_qdrant_btn.click(
            on_clear_qdrant, inputs=[danger_confirm], outputs=[danger_status]
        )
        clear_minio_btn.click(
            on_clear_minio, inputs=[danger_confirm], outputs=[danger_status]
        )
        clear_all_btn.click(
            on_clear_all, inputs=[danger_confirm], outputs=[danger_status]
        )

        # Chat submit (Enter in textbox)
        msg.submit(
            on_chat_submit,
            inputs=[
                msg,
                chat,
                k,
                ai_enabled,
                temperature,
                system_prompt_input,
            ],
            outputs=[msg, chat, output_gallery],
        )

        # Chat submit (Send button)
        send_btn.click(
            on_chat_submit,
            inputs=[
                msg,
                chat,
                k,
                ai_enabled,
                temperature,
                system_prompt_input,
            ],
            outputs=[msg, chat, output_gallery],
        )

        # Clear chat and gallery
        def _clear_chat():
            return [], []

        clear_btn.click(_clear_chat, outputs=[chat, output_gallery])

    return demo
