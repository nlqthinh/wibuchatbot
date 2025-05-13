import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")


