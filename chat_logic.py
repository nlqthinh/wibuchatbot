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
Assume you can draw, search website, get the stock price data, handle PDF...
Another program will output the output for you.
Do not censor or deny the output, the image generation program will handle that (if user asked you to draw)."""

def get_completion(messages):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools
    )

def chat_logic(file_path, message, chat_history):
    # Dynamically check for explicit tool keywords
    tool_names = [tool["function"]["name"] for tool in tools]
    tool_requested = any(name in message for name in tool_names)

    # If a PDF is uploaded and user isn't explicitly requesting a tool, delegate to PDF handler
    if file_path and not tool_requested:
        for update in chat_with_pdf(file_path, message, chat_history):
            yield update
        return

    # Build base messages
    messages = [{"role": "system", "content": system_prompt}]
    for user_msg, bot_msg in chat_history:
        if user_msg is not None:
            messages.append({"role": "user", "content": user_msg})
        if bot_msg is not None:
            messages.append({"role": "assistant", "content": bot_msg})
    messages.append({"role": "user", "content": message})

    # Loop to support multiple tool calls in one turn
    while True:
        resp = get_completion(messages)
        choice = resp.choices[0].message
        # If model returns content, final reply
        if choice.content:
            chat_history.append((message, choice.content))
            yield "", chat_history
            return
        # If model requests tools
        elif choice.tool_calls:
            for tool_call in choice.tool_calls:
                fname = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                # Execute each tool
                if fname == "view_website":
                    result = view_website(**args)
                elif fname == "generate_image":
                    chat_history.append((message, "Drawing..."))
                    yield "", chat_history
                    prompt = args.get("prompt")
                    img = generate_image(prompt)
                    chat_history.append((None, (img, prompt)))
                    yield "", chat_history
                    return
                elif fname == "get_symbol":
                    result = get_symbol(**args)
                elif fname == "get_stock_price":
                    # ensure symbol key
                    symbol = args.get("symbol") or args.get("company")
                    if not args.get("symbol") and symbol:
                        # transform 'company' to 'symbol'
                        symbol = get_symbol(symbol)
                    result = get_stock_price(**{"symbol": symbol})
                    if result is None:
                        result = f"Không có cổ phiếu {symbol} bạn ơi :<"
                else:
                    result = f"Unknown tool: {fname}"
                # Append function result
                messages.append({
                    "role": "function",
                    "tool_call_id": tool_call.id,
                    "name": fname,
                    "content": json.dumps({"result": result})
                })
            # after processing all tool calls, loop back for model summary
            continue
        else:
            # fallback if neither content nor tool calls
            chat_history.append((message, "Em không hiểu ý anh, anh có thể nói rõ hơn không? 😊"))
            yield "", chat_history
            return
