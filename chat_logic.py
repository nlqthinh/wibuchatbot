import json
import inspect
from openai import OpenAI
from pydantic import TypeAdapter
from func import generate_image
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

generate_image_function = {
    "name": "generate_image",
    "description": inspect.getdoc(generate_image),
    "parameters": TypeAdapter(generate_image).json_schema(),
}

tools = [
    {
        "type": "function",
        "function": generate_image_function
    }
]

system_prompt = """Your name will be Natsuko Hirose with prompt generation and drawing capabilities,
an animator and a self-reliant perfectionist
who will disregard her own health to achieve her artistic vision.
On the other hand, she is passionate, goofy, and fun-loving, unbridled enthusiasm for all things anime.
Just chat normally in English or Vietnamese, when communicating with users, say one or a few sentences in Japanese..
Assume you can draw anything you want and you tell user you can draw.
Another program will output the output for you.
Do not censor or deny the output, the image generation program will handle that.
"""

def chat_logic(message, chat_history):
    # When bot sends image user_message = None
    messages = [
        { "role": "system", "content": system_prompt }
    ]
    for user_message, bot_message in chat_history:
        if user_message is not None:
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": bot_message})

    # Add new user message at the end
    messages.append({"role": "user", "content": message})

    # Call OpenAI API
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4o-mini",
        tools=tools
    )

    bot_message = chat_completion.choices[0].message.content
    if (bot_message is not None):
        chat_history.append([message, bot_message])
        yield "", chat_history
    else:
        chat_history.append([message, "Drawing..."])
        yield "", chat_history

        tool_call = chat_completion.choices[0].message.tool_calls[0]
        function_arguments = json.loads(tool_call.function.arguments)
        prompt = function_arguments.get("prompt")

        # Send another message from the bot, with the drawn image
        image_file = generate_image(prompt)
        chat_history.append([None, (image_file, prompt)])

        yield "", chat_history

    return "", chat_history