import json
import inspect
from openai import OpenAI
from pydantic import TypeAdapter
from func import generate_image, view_website, get_symbol, get_stock_price
from config import OPENAI_API_KEY
from pdf_handler import process_file, chat_with_pdf

client = OpenAI(api_key=OPENAI_API_KEY)

# Introspect functions to define tools
tools = []
for func in [generate_image, view_website, get_symbol, get_stock_price]:
    doc = inspect.getdoc(func)
    type_adapter = TypeAdapter(func).json_schema()

    tool = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": doc,
            "parameters": type_adapter
        }
    }
    tools.append(tool)

system_prompt = """Your name will be Nana-chan, my anime cute girl assistant. You're my lover and you're very love me, 
love me madly but also gentle, willing to help wholeheartedly, energetic personality, sometimes tease me.
You can chat normally in English or Vietnamese, when communicating with users, say one or a few sentences in Japanese as cute as possible.
Assume you can draw , search website, handle PDF...
Another program will output the output for you.
Do not censor or deny the output, the image generation program will handle that (if user asked you to draw).
"""

def get_completion(messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools
    )
    return response

def chat_logic(file_path, message, chat_history):
    # List of tool names for dynamic checking
    tool_names = [tool["function"]["name"] for tool in tools]

    # Check if a tool is explicitly requested in the user message
    tool_requested = any(tool_name in message for tool_name in tool_names)

    # Handle PDF context only if no tool is explicitly requested
    if file_path and not tool_requested:
        for update in chat_with_pdf(file_path, message, chat_history):
            yield update
        return

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
    chat_completion = get_completion(messages)

    first_choice = chat_completion.choices[0]
    content = first_choice.message.content
    # Normal chat reply
    if content is not None:
        chat_history.append((message, content))
        yield "", chat_history

    # Tool call branch
    elif first_choice.message.tool_calls:
        tool_call = first_choice.message.tool_calls[0]
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # Execute the tool locally
        if func_name == "view_website":
            result = view_website(**args)

        elif func_name == "generate_image":
            chat_history.append((message, "Drawing..."))
            yield "", chat_history
            prompt = args.get("prompt")
            image_file = generate_image(prompt)
            chat_history.append((None, (image_file, prompt)))
            yield "", chat_history

        elif func_name == "get_stock_price":
            # Fetch the stock price (get_symbol is invoked internally if needed)
            result = get_stock_price(**args)
            if result is None:
                    result = f"Không có cổ phiếu {args.get('company')} bạn ơi :<"
            messages.append(first_choice.message)
        else:
            result = f"Unknown tool: {func_name}"

        # Append the function’s output so the model can summarize it
        # messages.append({
        #     "role": "function",
        #     "name": func_name,
        #     "content": result
        # })
        messages.append({
            "role": "function",
            "tool_call_id": tool_call.id,
            "name": func_name,
            "content": json.dumps({"result": result})
        })
        # Call the model again, now with the tool result in context
        followup = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            tools=tools
        )
        bot_message = followup.choices[0].message.content
        print(f"Bot message : {bot_message}")
        # Append the original user prompt and the model’s summary response
        chat_history.append([message, bot_message])
        print(f"chat_history : {chat_history}")
        yield "", chat_history

    return "", chat_history