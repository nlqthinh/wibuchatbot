import gradio as gr
from chat_logic import chat_logic

def launch_app():
    with gr.Blocks() as demo:
        gr.Markdown("# Chat with AI Animator Anime Girl")
        chatbot = gr.Chatbot(
            label="Hirose Natsuko",
            height=500,
            avatar_images=[
                "https://cdn.rafled.com/anime-icons/images/DHRMkoUcrVROuThTBLav6DN0wAllZfeT.jpg",
                "https://s4.anilist.co/file/anilistcdn/character/large/b330953-W8j8BM3nowjF.jpg"
            ]
        )
        message = gr.Textbox(label="Your prompt:")
        message.submit(chat_logic, [message, chatbot], [message, chatbot])

    demo.launch()

if __name__ == "__main__":
    launch_app()
