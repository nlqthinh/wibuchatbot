import time
import torch
from diffusers import DiffusionPipeline, EulerDiscreteScheduler
import requests
from config import JINA_API_KEY
import urllib3
import yfinance as yf
import time
from pprint import pprint

# Setup pipeline
scheduler = EulerDiscreteScheduler.from_pretrained("John6666/baxl-v3-sdxl", subfolder="scheduler")
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32  # Adjust dtype based on device
pipeline = DiffusionPipeline.from_pretrained(
    "John6666/baxl-v3-sdxl",
    scheduler=scheduler,
    use_safetensors=True,
    torch_dtype=torch_dtype 
)

device = "cuda" if torch.cuda.is_available() else "cpu"
pipeline.to(device)

def generate_image(prompt: str) -> str:
    """
    Creates an image based on the specified prompt using DiffusionPipeline.
    :param prompt: The prompt used to generate the image (must be in English).
    :return: Path to the generated image file.
    """
    image = pipeline(
        prompt=prompt,
        negative_prompt="ugly, deformed, disfigured, poor details, bad anatomy, low quality, worst quality",
        num_inference_steps=10
    ).images[0]

    # Save image file
    file_name = f"image_{int(time.time())}.png"
    image.save(file_name)
    return file_name

def view_website(url: str) -> str:
    """Fetch and return content from the given URL using JinaAI."""
    urllib3.disable_warnings()
    jina_url = f'https://r.jina.ai/{url}'
    headers = {
        'Authorization': f'{JINA_API_KEY}'
    }

    response = requests.get(jina_url, headers=headers, verify=False)
    # if response.status_code == 200:
    return response.text
    # else:
    #     return f"Error: Unable to fetch content from {url} (Status code: {response.status_code})"


def get_symbol(company: str) -> str:
    """
    Retrieve the stock symbol for a specified company using the Yahoo Finance API.
    :param company: The name of the company for which to retrieve the stock symbol, e.g., 'Nvidia'.
    :output: The stock symbol for the specified company.
    """
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": company, "country": "United States"}
    user_agents = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
    res = requests.get(url, params=params, headers=user_agents)

    data = res.json()

    quotes = data.get("quotes", [])
    if not quotes:
        return None
    
    symbol = data['quotes'][0]['symbol']
    return symbol


def get_stock_price(symbol:str, max_retries=3, retry_delay=5):
    """
    Retrieve the most recent stock price data for a specified company.
    Includes retry mechanism to handle rate limiting.

    :param symbol: The stock symbol.
    :param max_retries: Maximum number of retries.
    :param retry_delay: Delay between retries in seconds.
    :output: A dictionary containing the most recent stock price data.
    """
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(symbol)
            # Add a delay to avoid rate limiting
            time.sleep(retry_delay)  # Wait before making the request
            hist = stock.history(period="1d", interval="1m")
            latest = hist.iloc[-1]
            return {
                "timestamp": str(latest.name),
                "open": latest["Open"],
                "high": latest["High"],
                "low": latest["Low"],
                "close": latest["Close"],
                "volume": latest["Volume"]
            }
        # except yf.utils.YFRateLimitError: # Remove or comment out this line, since yf.utils.YFRateLimitError might not be available
        except yf.exceptions.YFRateLimitError: # Use yf.exceptions.YFRateLimitError as it is available in current yfinance version
            print(f"Rate limited. Retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})...")
            time.sleep(retry_delay)

    # raise yf.utils.YFRateLimitError("Too many requests. Rate limit exceeded after multiple retries.") # Update the exception type or comment out
    raise yf.exceptions.YFRateLimitError("Too many requests. Rate limit exceeded after multiple retries.") # Update the exception type here as well
     