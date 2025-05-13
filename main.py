import gradio as gr
from chat_logic import chat_logic
from pdf_handler import process_file, chat_with_pdf

def launch_app():
    with gr.Blocks() as demo:
        gr.Markdown("# Chat with your AI anime assistant")
        chatbot = gr.Chatbot(
            label="Nana-chan",
            height=500,
            avatar_images=[
                "https://cdn.rafled.com/anime-icons/images/DHRMkoUcrVROuThTBLav6DN0wAllZfeT.jpg",
                "images/akn.jpg"
            ]
        )
        message = gr.Textbox(label="Your prompt:")
        file_input = gr.File(label="Upload PDF", file_types=[".pdf"])
        status_output = gr.Textbox(label="Status")
        pdf_preview = gr.HTML(label="PDF Preview")

        # message.submit(chat_logic, [message, chatbot], [message, chatbot])
        file_input.change(
                fn=process_file,
                inputs=[file_input],
                outputs=[status_output, pdf_preview]
            )
        message.submit(
                fn=chat_logic,
                inputs=[file_input, message, chatbot],
                outputs=[message, chatbot]
            )


    demo.launch()

if __name__ == "__main__":
    launch_app()
