import gradio as gr
from chat_logic import chat_logic

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
        message.submit(chat_logic, [message, chatbot], [message, chatbot])

    demo.launch()

if __name__ == "__main__":
    launch_app()
